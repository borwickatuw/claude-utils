"""Tests for ANSI escape stripping utility."""

import io
import sys

from claude_utils.no_ansi import ANSI_ESCAPE, run_no_ansi


def _run(input_text: str) -> str:
    """Run run_no_ansi with given stdin and capture stdout."""
    old_stdin, old_stdout = sys.stdin, sys.stdout
    sys.stdin = io.StringIO(input_text)
    sys.stdout = captured = io.StringIO()
    try:
        code = run_no_ansi()
    finally:
        sys.stdin, sys.stdout = old_stdin, old_stdout
    assert code == 0
    return captured.getvalue()


class TestNoAnsi:
    """Tests for run_no_ansi."""

    def test_strips_color_codes(self):
        result = _run("\x1b[31mred text\x1b[0m\n")
        assert result == "red text\n"

    def test_strips_bold(self):
        result = _run("\x1b[1mbold\x1b[0m\n")
        assert result == "bold\n"

    def test_strips_multiple_codes(self):
        result = _run("\x1b[1;32mgreen bold\x1b[0m normal\n")
        assert result == "green bold normal\n"

    def test_passthrough_clean_text(self):
        result = _run("no escapes here\n")
        assert result == "no escapes here\n"

    def test_empty_input(self):
        result = _run("")
        assert result == ""

    def test_multiple_lines(self):
        result = _run("\x1b[31mline1\x1b[0m\n\x1b[32mline2\x1b[0m\n")
        assert result == "line1\nline2\n"

    def test_regex_matches_common_sequences(self):
        cases = [
            "\x1b[0m",  # reset
            "\x1b[31m",  # red
            "\x1b[1;32m",  # bold green
            "\x1b[38;5;82m",  # 256-color
            "\x1b[K",  # erase to end of line
        ]
        for seq in cases:
            assert ANSI_ESCAPE.sub("", seq) == "", f"Failed to match {repr(seq)}"
