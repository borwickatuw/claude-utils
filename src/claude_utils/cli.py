"""CLI entry point for claude-utils."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from claude_utils.clip import run_clip
from claude_utils.purge import run_purge


@click.group()
def main() -> None:
    """Utilities for managing Claude Code local data."""


@main.command()
@click.option(
    "--claude-dir",
    envvar="CLAUDE_DIR",
    default=str(Path.home() / ".claude"),
    show_default=True,
    help="Path to .claude directory.",
)
@click.option("-n", "--dry-run", is_flag=True, help="Show what would be deleted without deleting.")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation prompt.")
def purge(claude_dir: str, dry_run: bool, yes: bool) -> None:
    """Remove conversation history, debug logs, and other transient data."""
    sys.exit(run_purge(claude_dir=claude_dir, dry_run=dry_run, yes=yes))


@main.command()
@click.option("-t", "--text", is_flag=True, help="Rewrap prose: join soft-wrapped lines into paragraphs.")
def clip(text: bool) -> None:
    """Clean up text copied from Claude Code terminal output."""
    sys.exit(run_clip(text_mode=text))


if __name__ == "__main__":
    main()
