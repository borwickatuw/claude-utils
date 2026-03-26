"""CLI entry point for claude-utils."""

from __future__ import annotations

import argparse
import sys
from typing import NoReturn

from claude_utils.purge import run_purge


def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="claude-utils",
        description="Utilities for managing Claude Code local data.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    purge_parser = subparsers.add_parser(
        "purge",
        help="Remove conversation history, debug logs, and other transient data",
    )
    purge_parser.add_argument(
        "--claude-dir",
        default=None,
        help="Path to .claude directory (default: ~/.claude)",
    )
    purge_parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without deleting anything",
    )
    purge_parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )

    return parser


def main(argv: list[str] | None = None) -> NoReturn:
    parser = _create_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "purge":
        sys.exit(run_purge(
            claude_dir=args.claude_dir,
            dry_run=args.dry_run,
            yes=args.yes,
        ))

    sys.exit(1)


if __name__ == "__main__":
    main()
