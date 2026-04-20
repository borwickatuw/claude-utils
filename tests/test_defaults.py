"""Tests for defaults command."""

import json

import pytest
from click.testing import CliRunner

from claude_utils import defaults
from claude_utils.cli import main


@pytest.fixture()
def settings_file(tmp_path, monkeypatch):
    """Redirect SETTINGS_PATH to a temp file."""
    path = tmp_path / "settings.json"
    monkeypatch.setattr(defaults, "SETTINGS_PATH", path)
    return path


class TestDefaultsList:
    """Tests for `defaults` (list) command."""

    def test_shows_all_defaults(self, settings_file):
        runner = CliRunner()
        result = runner.invoke(main, ["defaults"])
        assert result.exit_code == 0
        for name in defaults.MANAGED_DEFAULTS:
            assert name in result.output

    def test_shows_off_when_no_file(self, settings_file):
        runner = CliRunner()
        result = runner.invoke(main, ["defaults"])
        assert result.exit_code == 0
        assert "no-1m-context" in result.output
        assert "off" in result.output

    def test_shows_on_when_set(self, settings_file):
        settings_file.write_text(json.dumps({"env": {"CLAUDE_CODE_DISABLE_1M_CONTEXT": "1"}}))
        runner = CliRunner()
        result = runner.invoke(main, ["defaults"])
        assert result.exit_code == 0
        assert "on" in result.output


class TestDefaultsSet:
    """Tests for `defaults set` command."""

    def test_set_on(self, settings_file):
        runner = CliRunner()
        result = runner.invoke(main, ["defaults", "no-1m-context", "on"])
        assert result.exit_code == 0
        data = json.loads(settings_file.read_text())
        assert data["env"]["CLAUDE_CODE_DISABLE_1M_CONTEXT"] == "1"

    def test_set_off_removes_key(self, settings_file):
        settings_file.write_text(json.dumps({"env": {"CLAUDE_CODE_DISABLE_1M_CONTEXT": "1"}}))
        runner = CliRunner()
        result = runner.invoke(main, ["defaults", "no-1m-context", "off"])
        assert result.exit_code == 0
        data = json.loads(settings_file.read_text())
        assert "env" not in data

    def test_set_preserves_other_keys(self, settings_file):
        settings_file.write_text(json.dumps({"effortLevel": "high"}))
        runner = CliRunner()
        result = runner.invoke(main, ["defaults", "clear-on-plan", "on"])
        assert result.exit_code == 0
        data = json.loads(settings_file.read_text())
        assert data["effortLevel"] == "high"
        assert data["showClearContextOnPlanAccept"] is True

    def test_set_off_preserves_other_env(self, settings_file):
        settings_file.write_text(
            json.dumps({"env": {"CLAUDE_CODE_DISABLE_1M_CONTEXT": "1", "OTHER": "val"}})
        )
        runner = CliRunner()
        result = runner.invoke(main, ["defaults", "no-1m-context", "off"])
        assert result.exit_code == 0
        data = json.loads(settings_file.read_text())
        assert data["env"] == {"OTHER": "val"}

    def test_unknown_name(self, settings_file):
        runner = CliRunner()
        result = runner.invoke(main, ["defaults", "bogus", "on"])
        assert result.exit_code == 1
        assert "unknown" in result.output.lower() or "unknown" in (result.stderr or "").lower()

    def test_invalid_state(self, settings_file):
        runner = CliRunner()
        result = runner.invoke(main, ["defaults", "no-1m-context", "maybe"])
        assert result.exit_code != 0

    def test_creates_file_if_missing(self, settings_file):
        assert not settings_file.exists()
        runner = CliRunner()
        result = runner.invoke(main, ["defaults", "clear-on-plan", "on"])
        assert result.exit_code == 0
        assert settings_file.exists()
        data = json.loads(settings_file.read_text())
        assert data["showClearContextOnPlanAccept"] is True

    def test_clear_on_plan_off(self, settings_file):
        settings_file.write_text(json.dumps({"showClearContextOnPlanAccept": True}))
        runner = CliRunner()
        result = runner.invoke(main, ["defaults", "clear-on-plan", "off"])
        assert result.exit_code == 0
        data = json.loads(settings_file.read_text())
        assert "showClearContextOnPlanAccept" not in data
