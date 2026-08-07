"""Manage Claude Code defaults in ~/.claude/settings.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

SETTINGS_PATH = Path.home() / ".claude" / "settings.json"

# Registry of managed defaults.
#
# kind: "toggle" — accepts on/off
#   on_value  — value to write when "on"
#   off_value — value to write when "off" (omit to remove the key instead)
#
# kind: "int" — accepts a number or "off" (to remove)
#   min/max — optional bounds
#   env     — if True, store as string (for env vars)
MANAGED_DEFAULTS: dict[str, dict] = {
    "no-1m-context": {
        "path": ["env", "CLAUDE_CODE_DISABLE_1M_CONTEXT"],
        "kind": "toggle",
        "on_value": "1",
        "description": "Disable 1M context window",
    },
    "clear-on-plan": {
        "path": ["showClearContextOnPlanAccept"],
        "kind": "toggle",
        "on_value": True,
        "description": "Show clear-context option when accepting a plan",
    },
    "reduced-motion": {
        "path": ["prefersReducedMotion"],
        "kind": "toggle",
        "on_value": True,
        "description": "Reduce UI animations",
    },
    "spinner-tips": {
        "path": ["spinnerTipsEnabled"],
        "kind": "toggle",
        "on_value": True,
        "off_value": False,
        "description": "Show spinner tips",
    },
    "git-instructions": {
        "path": ["includeGitInstructions"],
        "kind": "toggle",
        "on_value": True,
        "off_value": False,
        "description": "Include built-in git instructions in prompt",
    },
    "respect-gitignore": {
        "path": ["respectGitignore"],
        "kind": "toggle",
        "on_value": True,
        "off_value": False,
        "description": "Respect .gitignore in @ file picker",
    },
    "no-survey": {
        "path": ["feedbackSurveyRate"],
        "kind": "toggle",
        "on_value": 0,
        "description": "Suppress feedback surveys",
    },
    "cleanup-days": {
        "path": ["cleanupPeriodDays"],
        "kind": "int",
        "min": 1,
        "description": "Session transcript retention (days, default: 30)",
    },
    "autocompact-pct": {
        "path": ["env", "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE"],
        "kind": "int",
        "min": 1,
        "max": 100,
        "env": True,
        "description": "Auto-compaction threshold (%, default: ~95)",
    },
}


def _read_settings() -> dict:
    """Read settings.json, returning {} if missing or empty."""
    if not SETTINGS_PATH.exists():
        return {}
    text = SETTINGS_PATH.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    return json.loads(text)


def _write_settings(settings: dict) -> None:
    """Write settings.json with consistent formatting."""
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _get_nested(data: dict, path: list[str]) -> tuple[bool, object]:
    """Get a value at a nested path. Returns (found, value)."""
    current = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return False, None
        current = current[key]
    return True, current


def _set_nested(data: dict, path: list[str], value: object) -> None:
    """Set a value at a nested path, creating intermediate dicts."""
    current = data
    for key in path[:-1]:
        current = current.setdefault(key, {})
    current[path[-1]] = value


def _remove_nested(data: dict, path: list[str]) -> None:
    """Remove a key at a nested path, cleaning up empty parent dicts."""
    if len(path) == 1:
        data.pop(path[0], None)
        return
    parent_path, key = path[:-1], path[-1]
    current = data
    parents: list[tuple[dict, str]] = []
    for p in parent_path:
        if not isinstance(current, dict) or p not in current:
            return
        parents.append((current, p))
        current = current[p]
    if isinstance(current, dict):
        current.pop(key, None)
    for parent, p in reversed(parents):
        if not parent[p]:
            del parent[p]


def _display_state(settings: dict, spec: dict) -> str:
    """Return the display state: on/off for toggles, value for ints, '-' if unset."""
    found, value = _get_nested(settings, spec["path"])
    if not found:
        return "-"
    if spec["kind"] == "toggle":
        if value == spec["on_value"]:
            return "on"
        return "off"
    return str(value)


def run_defaults_list() -> int:
    """Show current state of all managed defaults. Returns exit code."""
    settings = _read_settings()
    for name, spec in MANAGED_DEFAULTS.items():
        state = _display_state(settings, spec)
        print(f"  {name:20s} {state:5s}  {spec['description']}")
    return 0


def _validate_toggle(state: str, name: str) -> str | None:
    """Validate toggle state. Returns error message or None."""
    if state not in {"on", "off"}:
        return f"Error: {name!r} accepts 'on' or 'off', got {state!r}"
    return None


def _validate_int(state: str, name: str, spec: dict) -> str | None:
    """Validate int state. Returns error message or None."""
    if state == "off":
        return None
    try:
        val = int(state)
    except ValueError:
        return f"Error: {name!r} accepts a number or 'off', got {state!r}"
    lo = spec.get("min")
    hi = spec.get("max")
    if lo is not None and val < lo:
        return f"Error: {name!r} minimum is {lo}, got {val}"
    if hi is not None and val > hi:
        return f"Error: {name!r} maximum is {hi}, got {val}"
    return None


def run_defaults_set(name: str, state: str) -> int:
    """Set a managed default. Returns exit code."""
    if name not in MANAGED_DEFAULTS:
        known = ", ".join(MANAGED_DEFAULTS)
        print(f"Error: unknown default {name!r} (known: {known})", file=sys.stderr)
        return 1

    spec = MANAGED_DEFAULTS[name]

    if spec["kind"] == "toggle":
        err = _validate_toggle(state, name)
    else:
        err = _validate_int(state, name, spec)
    if err:
        print(err, file=sys.stderr)
        return 1

    settings = _read_settings()

    if state == "off":
        if "off_value" in spec:
            _set_nested(settings, spec["path"], spec["off_value"])
        else:
            _remove_nested(settings, spec["path"])
        print(f"{name}: off  ({spec['description']})")
    elif state == "on":
        _set_nested(settings, spec["path"], spec["on_value"])
        print(f"{name}: on  ({spec['description']})")
    else:
        # Int value
        val: int | str = int(state)
        if spec.get("env"):
            val = state
        _set_nested(settings, spec["path"], val)
        print(f"{name}: {state}  ({spec['description']})")

    _write_settings(settings)
    return 0
