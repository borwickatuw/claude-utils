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

    def test_shows_on_when_set(self, settings_file):
        settings_file.write_text(json.dumps({"env": {"CLAUDE_CODE_DISABLE_1M_CONTEXT": "1"}}))
        runner = CliRunner()
        result = runner.invoke(main, ["defaults"])
        assert result.exit_code == 0
        # no-1m-context should show "on"
        for line in result.output.splitlines():
            if "no-1m-context" in line:
                assert "on" in line

    def test_unset_toggle_shows_dash(self, settings_file):
        """Unset toggles show '-' rather than assuming a default."""
        runner = CliRunner()
        result = runner.invoke(main, ["defaults"])
        assert result.exit_code == 0
        for line in result.output.splitlines():
            if "spinner-tips" in line:
                assert " - " in line

    def test_default_on_toggle_shows_off_when_false(self, settings_file):
        settings_file.write_text(json.dumps({"spinnerTipsEnabled": False}))
        runner = CliRunner()
        result = runner.invoke(main, ["defaults"])
        assert result.exit_code == 0
        for line in result.output.splitlines():
            if "spinner-tips" in line:
                assert " off " in line

    def test_int_shows_dash_when_absent(self, settings_file):
        runner = CliRunner()
        result = runner.invoke(main, ["defaults"])
        assert result.exit_code == 0
        for line in result.output.splitlines():
            if "cleanup-days" in line:
                assert " - " in line

    def test_int_shows_value_when_set(self, settings_file):
        settings_file.write_text(json.dumps({"cleanupPeriodDays": 90}))
        runner = CliRunner()
        result = runner.invoke(main, ["defaults"])
        assert result.exit_code == 0
        for line in result.output.splitlines():
            if "cleanup-days" in line:
                assert "90" in line


class TestDefaultsSetToggle:
    """Tests for toggle settings."""

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


class TestDefaultsSetOffValue:
    """Tests for toggles with off_value (default-on settings)."""

    def test_spinner_tips_off_sets_false(self, settings_file):
        runner = CliRunner()
        result = runner.invoke(main, ["defaults", "spinner-tips", "off"])
        assert result.exit_code == 0
        data = json.loads(settings_file.read_text())
        assert data["spinnerTipsEnabled"] is False

    def test_spinner_tips_on_sets_true(self, settings_file):
        settings_file.write_text(json.dumps({"spinnerTipsEnabled": False}))
        runner = CliRunner()
        result = runner.invoke(main, ["defaults", "spinner-tips", "on"])
        assert result.exit_code == 0
        data = json.loads(settings_file.read_text())
        assert data["spinnerTipsEnabled"] is True

    def test_git_instructions_off(self, settings_file):
        runner = CliRunner()
        result = runner.invoke(main, ["defaults", "git-instructions", "off"])
        assert result.exit_code == 0
        data = json.loads(settings_file.read_text())
        assert data["includeGitInstructions"] is False

    def test_respect_gitignore_off(self, settings_file):
        runner = CliRunner()
        result = runner.invoke(main, ["defaults", "respect-gitignore", "off"])
        assert result.exit_code == 0
        data = json.loads(settings_file.read_text())
        assert data["respectGitignore"] is False

    def test_reduced_motion_on(self, settings_file):
        runner = CliRunner()
        result = runner.invoke(main, ["defaults", "reduced-motion", "on"])
        assert result.exit_code == 0
        data = json.loads(settings_file.read_text())
        assert data["prefersReducedMotion"] is True

    def test_no_survey_on(self, settings_file):
        runner = CliRunner()
        result = runner.invoke(main, ["defaults", "no-survey", "on"])
        assert result.exit_code == 0
        data = json.loads(settings_file.read_text())
        assert data["feedbackSurveyRate"] == 0


class TestDefaultsSetInt:
    """Tests for int-value settings."""

    def test_cleanup_days_set(self, settings_file):
        runner = CliRunner()
        result = runner.invoke(main, ["defaults", "cleanup-days", "90"])
        assert result.exit_code == 0
        data = json.loads(settings_file.read_text())
        assert data["cleanupPeriodDays"] == 90

    def test_cleanup_days_off_removes(self, settings_file):
        settings_file.write_text(json.dumps({"cleanupPeriodDays": 90}))
        runner = CliRunner()
        result = runner.invoke(main, ["defaults", "cleanup-days", "off"])
        assert result.exit_code == 0
        data = json.loads(settings_file.read_text())
        assert "cleanupPeriodDays" not in data

    def test_cleanup_days_rejects_zero(self, settings_file):
        runner = CliRunner()
        result = runner.invoke(main, ["defaults", "cleanup-days", "0"])
        assert result.exit_code == 1

    def test_cleanup_days_rejects_non_number(self, settings_file):
        runner = CliRunner()
        result = runner.invoke(main, ["defaults", "cleanup-days", "banana"])
        assert result.exit_code == 1

    def test_autocompact_pct_set(self, settings_file):
        runner = CliRunner()
        result = runner.invoke(main, ["defaults", "autocompact-pct", "50"])
        assert result.exit_code == 0
        data = json.loads(settings_file.read_text())
        # env vars stored as strings
        assert data["env"]["CLAUDE_AUTOCOMPACT_PCT_OVERRIDE"] == "50"

    def test_autocompact_pct_rejects_over_100(self, settings_file):
        runner = CliRunner()
        result = runner.invoke(main, ["defaults", "autocompact-pct", "150"])
        assert result.exit_code == 1

    def test_autocompact_pct_off_removes(self, settings_file):
        settings_file.write_text(
            json.dumps({"env": {"CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "50"}})
        )
        runner = CliRunner()
        result = runner.invoke(main, ["defaults", "autocompact-pct", "off"])
        assert result.exit_code == 0
        data = json.loads(settings_file.read_text())
        assert "env" not in data

    def test_toggle_rejects_number(self, settings_file):
        runner = CliRunner()
        result = runner.invoke(main, ["defaults", "no-1m-context", "42"])
        assert result.exit_code == 1
