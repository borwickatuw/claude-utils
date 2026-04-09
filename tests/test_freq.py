"""Tests for frequency counting utility."""

import io

from claude_utils.freq import run_freq


def _run(input_text: str, limit: int | None = None) -> str:
    """Run run_freq with given stdin and capture stdout."""
    import sys

    old_stdin, old_stdout = sys.stdin, sys.stdout
    sys.stdin = io.StringIO(input_text)
    sys.stdout = captured = io.StringIO()
    try:
        code = run_freq(limit=limit)
    finally:
        sys.stdin, sys.stdout = old_stdin, old_stdout
    assert code == 0
    return captured.getvalue()


class TestFreq:
    """Tests for run_freq."""

    def test_basic_counting(self):
        result = _run("apple\nbanana\napple\napple\nbanana\n")
        lines = result.strip().split("\n")
        assert lines[0].strip() == "3 apple"
        assert lines[1].strip() == "2 banana"

    def test_limit(self):
        result = _run("a\nb\na\nb\nc\n", limit=1)
        lines = result.strip().split("\n")
        assert len(lines) == 1

    def test_empty_input(self):
        result = _run("")
        assert result == ""

    def test_single_line(self):
        result = _run("hello\n")
        assert result.strip() == "1 hello"

    def test_preserves_whitespace_in_values(self):
        result = _run("  indented\n  indented\nnormal\n")
        lines = result.strip().split("\n")
        assert lines[0].strip() == "2   indented"

    def test_alignment(self):
        # With counts of different widths, should right-align
        text = "a\n" * 100 + "b\n"
        result = _run(text)
        lines = result.strip().split("\n")
        assert lines[0] == "100 a"
        assert lines[1] == "  1 b"
