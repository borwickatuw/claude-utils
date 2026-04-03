"""Clean clipboard text copied from Claude Code terminal output."""

from __future__ import annotations

import re
import sys
import textwrap

import pyperclip

# Zero-width and invisible Unicode characters
INVISIBLE_CHARS = frozenset(
    {
        "\u200b",  # zero-width space
        "\u200c",  # zero-width non-joiner
        "\u200d",  # zero-width joiner
        "\u2060",  # word joiner
        "\ufeff",  # zero-width no-break space (BOM)
        "\u00ad",  # soft hyphen
        "\u200e",  # left-to-right mark
        "\u200f",  # right-to-left mark
        "\u2061",  # function application
        "\u2062",  # invisible times
        "\u2063",  # invisible separator
        "\u2064",  # invisible plus
    }
)


def clean_clipboard_text(text: str) -> str:
    """Clean up text copied from Claude Code terminal output."""
    # Strip trailing whitespace per line (Claude Code pads lines to terminal width)
    lines = text.split("\n")
    stripped = "\n".join(line.rstrip() for line in lines)
    # Remove zero-width / invisible Unicode characters
    cleaned = "".join(ch for ch in stripped if ch not in INVISIBLE_CHARS)
    # Remove common leading indentation (Claude Code adds 2-space indent to code blocks)
    return textwrap.dedent(cleaned)


def rewrap_text(text: str) -> str:
    """Join soft-wrapped lines into paragraphs, preserving paragraph breaks."""
    # Strip the ⏺ marker Claude Code puts at the start of blocks
    text = re.sub(r"^⏺\s*", "", text)
    # Split into paragraphs on blank lines
    paragraphs = re.split(r"\n\n+", text)
    # Within each paragraph, collapse newlines into a single space
    joined = [
        re.sub(r"\s*\n\s*", " ", para.strip()) for para in paragraphs if para.strip()
    ]
    return "\n\n".join(joined)


def run_clip(text_mode: bool = False, with_credit: bool = False) -> int:
    """Read clipboard, clean it, write back. Returns exit code."""
    try:
        original = pyperclip.paste()
    except pyperclip.PyperclipException as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    cleaned = clean_clipboard_text(original)
    if text_mode:
        cleaned = rewrap_text(cleaned)
    if with_credit:
        cleaned += "\n-- Claude Code"

    if original == cleaned:
        print("clipboard already clean")
        return 0

    pyperclip.copy(cleaned)
    print("cleaned clipboard")
    return 0
