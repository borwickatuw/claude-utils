"""Tests for clipboard cleaning utilities."""

from claude_utils.clip import INVISIBLE_CHARS, clean_clipboard_text, rewrap_text


class TestCleanClipboardText:
    """Tests for clean_clipboard_text."""

    def test_strips_trailing_whitespace(self):
        text = "hello   \nworld   \n"
        result = clean_clipboard_text(text)
        assert result == "hello\nworld\n"

    def test_removes_invisible_chars(self):
        text = "hello\u200bworld\u200d"
        result = clean_clipboard_text(text)
        assert result == "helloworld"

    def test_dedents_code_blocks(self):
        text = "  line1\n  line2\n  line3"
        result = clean_clipboard_text(text)
        assert result == "line1\nline2\nline3"

    def test_preserves_relative_indentation(self):
        text = "  def foo():\n      return 1"
        result = clean_clipboard_text(text)
        assert result == "def foo():\n    return 1"

    def test_empty_string(self):
        assert clean_clipboard_text("") == ""

    def test_already_clean(self):
        text = "hello world"
        assert clean_clipboard_text(text) == text

    def test_all_invisible_chars_removed(self):
        """Every char in INVISIBLE_CHARS should be stripped."""
        for char in INVISIBLE_CHARS:
            text = f"a{char}b"
            result = clean_clipboard_text(text)
            assert result == "ab", f"Failed to remove {repr(char)}"

    def test_mixed_invisible_and_whitespace(self):
        text = "hello\u200b   \nworld\u2060   "
        result = clean_clipboard_text(text)
        assert "hello" in result
        assert "world" in result
        assert "\u200b" not in result
        assert "\u2060" not in result


class TestRewrapText:
    """Tests for rewrap_text."""

    def test_joins_soft_wrapped_lines(self):
        text = "This is a\nlong sentence\nthat wraps."
        result = rewrap_text(text)
        assert result == "This is a long sentence that wraps."

    def test_preserves_paragraph_breaks(self):
        text = "Paragraph one.\n\nParagraph two."
        result = rewrap_text(text)
        assert result == "Paragraph one.\n\nParagraph two."

    def test_strips_marker(self):
        text = "⏺ Some content here"
        result = rewrap_text(text)
        assert result == "Some content here"

    def test_empty_string(self):
        assert rewrap_text("") == ""

    def test_multiple_blank_lines_treated_as_paragraph_break(self):
        text = "First.\n\n\n\nSecond."
        result = rewrap_text(text)
        assert result == "First.\n\nSecond."

    def test_collapses_internal_whitespace(self):
        text = "word1  \n  word2"
        result = rewrap_text(text)
        assert result == "word1 word2"
