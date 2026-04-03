"""Tests for CLI entry point."""

from click.testing import CliRunner

from claude_utils.cli import main


class TestCLI:
    """Tests for Click CLI commands."""

    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "purge" in result.output
        assert "clip" in result.output

    def test_purge_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["purge", "--help"])
        assert result.exit_code == 0
        assert "--claude-dir" in result.output
        assert "--dry-run" in result.output
        assert "--yes" in result.output

    def test_clip_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["clip", "--help"])
        assert result.exit_code == 0
        assert "--text" in result.output
        assert "--with-credit" in result.output

    def test_purge_nonexistent_dir(self):
        runner = CliRunner()
        result = runner.invoke(main, ["purge", "--claude-dir", "/nonexistent/path"])
        assert result.exit_code != 0

    def test_purge_dry_run(self, tmp_path):
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        sessions = claude_dir / "sessions"
        sessions.mkdir()
        (sessions / "data.json").write_text("{}")
        runner = CliRunner()
        result = runner.invoke(
            main, ["purge", "--claude-dir", str(claude_dir), "--dry-run"]
        )
        assert result.exit_code == 0
        assert "dry run" in result.output.lower()

    def test_purge_nothing(self, tmp_path):
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        runner = CliRunner()
        result = runner.invoke(main, ["purge", "--claude-dir", str(claude_dir)])
        assert result.exit_code == 0
        assert "nothing" in result.output.lower()
