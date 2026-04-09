"""Frequency count: equivalent of sort | uniq -c | sort -rn."""

from __future__ import annotations

import sys
from collections import Counter


def run_freq(limit: int | None = None) -> int:
    """Read stdin lines, print frequency-sorted counts. Returns exit code."""
    counts = Counter(line.rstrip("\n") for line in sys.stdin)
    items = counts.most_common(limit)
    if not items:
        return 0
    width = len(str(items[0][1]))
    for value, count in items:
        print(f"{count:>{width}} {value}")
    return 0
