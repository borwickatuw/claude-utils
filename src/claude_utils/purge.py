"""Purge Claude Code transient data while preserving config and memory."""

from __future__ import annotations

import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

# UUID pattern for conversation transcript directories/files
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")

# Top-level directories whose contents are safe to purge entirely
PURGEABLE_DIRS = [
    "backups",
    "cache",
    "debug",
    "file-history",
    "paste-cache",
    "plans",
    "session-env",
    "sessions",
    "shell-snapshots",
    "statsig",
    "tasks",
    "telemetry",
    "todos",
]

# Top-level files safe to truncate/remove
PURGEABLE_FILES = [
    "history.jsonl",
    "mcp-needs-auth-cache.json",
    "stats-cache.json",
]

# Items to preserve inside each project directory
PROJECT_KEEP = {"memory", "CLAUDE.md"}


@dataclass
class PurgeResult:
    """Tracks what was (or would be) purged."""

    dirs_removed: list[str] = field(default_factory=list)
    files_removed: list[str] = field(default_factory=list)
    bytes_freed: int = 0


def _dir_size(path: Path) -> int:
    total = 0
    for entry in path.rglob("*"):
        if entry.is_file():
            total += entry.stat().st_size
    return total


def _file_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return 0


_GB = 1_073_741_824
_MB = 1_048_576
_KB = 1024


def _format_size(nbytes: int) -> str:
    if nbytes >= _GB:
        return f"{nbytes / _GB:.1f} GB"
    if nbytes >= _MB:
        return f"{nbytes / _MB:.1f} MB"
    if nbytes >= _KB:
        return f"{nbytes / _KB:.1f} KB"
    return f"{nbytes} B"


def _is_empty_dir(path: Path) -> bool:
    """Check if a directory is empty or contains only empty subdirectories."""
    for child in path.iterdir():
        if child.is_file():
            return False
        if child.is_dir() and not _is_empty_dir(child):
            return False
    return True


def _rmtree_empty(path: Path) -> None:
    """Remove a directory tree that contains only empty subdirectories."""
    for child in path.iterdir():
        if child.is_dir():
            _rmtree_empty(child)
    path.rmdir()


def _scan_project_transcripts(project_dir: Path) -> list[Path]:
    """Find conversation transcript dirs and files inside a project directory."""
    targets: list[Path] = []
    for child in sorted(project_dir.iterdir()):
        if child.name in PROJECT_KEEP:
            continue
        if UUID_RE.match(child.name) or child.name == "sessions-index.json":
            targets.append(child)
    return targets


def _would_be_empty_after_purge(project_dir: Path, purge_targets: set[Path]) -> bool:
    """Check if a project dir would be empty after removing the given targets."""
    for child in project_dir.iterdir():
        if child not in purge_targets:
            # Something would remain -- but is it an empty dir?
            if child.is_dir() and _is_empty_dir(child):
                continue
            return False
    return True


def _collect_targets(claude_dir: Path) -> tuple[list[Path], int, int]:
    """Collect all paths to purge and their total size.

    Returns (targets, total_bytes, empty_project_count).
    """
    targets: list[Path] = []
    total_bytes = 0

    # Top-level purgeable directories
    for dirname in PURGEABLE_DIRS:
        dirpath = claude_dir / dirname
        if dirpath.is_dir():
            size = _dir_size(dirpath)
            if size > 0:
                targets.append(dirpath)
                total_bytes += size

    # Top-level purgeable files
    for filename in PURGEABLE_FILES:
        filepath = claude_dir / filename
        size = _file_size(filepath)
        if size > 0:
            targets.append(filepath)
            total_bytes += size

    # Project conversation transcripts
    empty_projects = 0
    projects_dir = claude_dir / "projects"
    if projects_dir.is_dir():
        for project in sorted(projects_dir.iterdir()):
            if not project.is_dir():
                continue
            project_purge: list[Path] = []
            for target in _scan_project_transcripts(project):
                size = _dir_size(target) if target.is_dir() else _file_size(target)
                project_purge.append(target)
                total_bytes += size
            targets.extend(project_purge)
            if project_purge and _would_be_empty_after_purge(
                project, set(project_purge)
            ):
                empty_projects += 1

    return targets, total_bytes, empty_projects


def _print_plan(
    targets: list[Path], total_bytes: int, empty_projects: int, claude_dir: Path
) -> None:
    """Print a summary of what will be purged."""
    # Group by category for readable output
    top_dirs: list[Path] = []
    top_files: list[Path] = []
    project_targets: dict[str, list[Path]] = {}

    projects_prefix = claude_dir / "projects"

    for t in targets:
        try:
            t.relative_to(projects_prefix)
            project_name = t.parent.name
            project_targets.setdefault(project_name, []).append(t)
        except ValueError:
            if t.is_dir():
                top_dirs.append(t)
            else:
                top_files.append(t)

    if top_dirs:
        print("Directories to clear:")
        for d in top_dirs:
            print(f"  {d.name}/  ({_format_size(_dir_size(d))})")

    if top_files:
        print("Files to remove/truncate:")
        for f in top_files:
            print(f"  {f.name}  ({_format_size(_file_size(f))})")

    if project_targets:
        n_projects = len(project_targets)
        n_transcripts = sum(len(v) for v in project_targets.values())
        print(
            f"Conversation transcripts: {n_transcripts} items"
            f" across {n_projects} projects"
        )
        if empty_projects:
            print(f"Empty project directories to remove: {empty_projects}")

    print(f"\nTotal to free: {_format_size(total_bytes)}")


def _execute_purge(targets: list[Path], claude_dir: Path) -> PurgeResult:
    """Delete the collected targets."""
    result = PurgeResult()

    projects_prefix = claude_dir / "projects"

    for target in targets:
        if target.is_file():
            size = target.stat().st_size
            target.unlink()
            result.files_removed.append(str(target))
            result.bytes_freed += size
            continue

        if not target.is_dir():
            continue

        size = _dir_size(target)
        if target.is_relative_to(projects_prefix):
            # Project transcript dir: remove entirely
            shutil.rmtree(target)
        else:
            # Top-level dir: clear contents, keep dir
            for child in target.iterdir():
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
        result.dirs_removed.append(str(target))
        result.bytes_freed += size

    # Remove empty project directories
    projects_dir = claude_dir / "projects"
    if projects_dir.is_dir():
        for project in sorted(projects_dir.iterdir()):
            if not project.is_dir():
                continue
            if _is_empty_dir(project):
                _rmtree_empty(project)
                result.dirs_removed.append(str(project))

    return result


def run_purge(
    claude_dir: str,
    dry_run: bool = False,
    yes: bool = False,
) -> int:
    """Main purge entrypoint. Returns exit code."""
    path = Path(claude_dir)

    if not path.is_dir():
        print(f"Error: {path} does not exist or is not a directory", file=sys.stderr)
        return 1

    targets, total_bytes, empty_projects = _collect_targets(path)

    if not targets:
        print("Nothing to purge.")
        return 0

    _print_plan(targets, total_bytes, empty_projects, path)

    if dry_run:
        print("\n(dry run -- nothing was deleted)")
        return 0

    if not yes:
        try:
            response = input("\nProceed? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            return 1
        if response not in {"y", "yes"}:
            print("Aborted.")
            return 0

    result = _execute_purge(targets, path)
    print(f"\nPurged {_format_size(result.bytes_freed)}.")
    return 0
