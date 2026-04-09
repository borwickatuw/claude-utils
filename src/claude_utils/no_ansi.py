"""Strip ANSI escape sequences from stdin."""

from __future__ import annotations

import re
import sys

ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]|\x1b\].*?\x07|\x1b\[.*?\x07")


def run_no_ansi() -> int:
    """Read stdin, strip ANSI escape codes, write to stdout. Returns exit code."""
    for line in sys.stdin:
        print(ANSI_ESCAPE.sub("", line), end="")
    return 0
