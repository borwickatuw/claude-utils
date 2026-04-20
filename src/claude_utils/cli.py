"""CLI entry point for claude-utils."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from claude_utils.clip import run_clip
from claude_utils.defaults import run_defaults_list, run_defaults_set
from claude_utils.freq import run_freq
from claude_utils.no_ansi import run_no_ansi
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
@click.option(
    "-n", "--dry-run", is_flag=True, help="Show what would be deleted without deleting."
)
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation prompt.")
def purge(claude_dir: str, dry_run: bool, yes: bool) -> None:
    """Remove conversation history, debug logs, and other transient data."""
    sys.exit(run_purge(claude_dir=claude_dir, dry_run=dry_run, yes=yes))


@main.command()
@click.option(
    "-t",
    "--text",
    is_flag=True,
    help="Rewrap prose: join soft-wrapped lines into paragraphs.",
)
@click.option(
    "--with-credit", is_flag=True, help="Append '-- Claude Code' attribution."
)
def clip(text: bool, with_credit: bool) -> None:
    """Clean up text copied from Claude Code terminal output."""
    sys.exit(run_clip(text_mode=text, with_credit=with_credit))


@main.command()
@click.option(
    "-n",
    "--limit",
    type=int,
    default=None,
    help="Show only the top N entries.",
)
def freq(limit: int | None) -> None:
    """Frequency count of stdin lines."""
    sys.exit(run_freq(limit=limit))


@main.command("no-ansi")
def no_ansi() -> None:
    """Strip ANSI escape sequences from stdin."""
    sys.exit(run_no_ansi())


@main.command()
@click.argument("name", required=False)
@click.argument("state", required=False)
def defaults(name: str | None, state: str | None) -> None:
    """Manage Claude Code defaults in ~/.claude/settings.json."""
    if name is None:
        sys.exit(run_defaults_list())
    if state is None:
        raise click.UsageError("Usage: claude-utils defaults <name> <on|off|value>")
    sys.exit(run_defaults_set(name, state))


if __name__ == "__main__":
    main()
