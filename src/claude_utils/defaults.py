"""Manage Claude Code defaults in ~/.claude/settings.json."""

from __future__ import annotations

import json
from pathlib import Path

SETTINGS_PATH = Path.home() / ".claude" / "settings.json"

# Registry of managed defaults.
# Each entry maps a friendly name to its location in settings.json.
MANAGED_DEFAULTS: dict[str, dict] = {
    "no-1m-context": {
        "path": ["env", "CLAUDE_CODE_DISABLE_1M_CONTEXT"],
        "on_value": "1",
        "description": "Disable 1M context window",
    },
    "clear-on-plan": {
        "path": ["showClearContextOnPlanAccept"],
        "on_value": True,
        "description": "Show clear-context option when accepting a plan",
    },
}


def _read_settings() -> dict:
    """Read settings.json, returning {} if missing or empty."""
    if not SETTINGS_PATH.exists():
        return {}
    text = SETTINGS_PATH.read_text()
    if not text.strip():
        return {}
    return json.loads(text)


def _write_settings(settings: dict) -> None:
    """Write settings.json with consistent formatting."""
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2) + "\n")


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
    # Walk down to the parent
    current = data
    parents: list[tuple[dict, str]] = []
    for p in parent_path:
        if not isinstance(current, dict) or p not in current:
            return
        parents.append((current, p))
        current = current[p]
    if isinstance(current, dict):
        current.pop(key, None)
    # Clean up empty parent dicts
    for parent, p in reversed(parents):
        if not parent[p]:
            del parent[p]


def run_defaults_list() -> int:
    """Show current state of all managed defaults. Returns exit code."""
    settings = _read_settings()
    for name, spec in MANAGED_DEFAULTS.items():
        found, value = _get_nested(settings, spec["path"])
        if found and value == spec["on_value"]:
            state = "on"
        else:
            state = "off"
        print(f"  {name:20s} {state:4s}  {spec['description']}")
    return 0


def run_defaults_set(name: str, state: str) -> int:
    """Set a managed default to on or off. Returns exit code."""
    if name not in MANAGED_DEFAULTS:
        known = ", ".join(MANAGED_DEFAULTS)
        print(f"Error: unknown default {name!r} (known: {known})", file=__import__("sys").stderr)
        return 1
    spec = MANAGED_DEFAULTS[name]
    settings = _read_settings()
    if state == "on":
        _set_nested(settings, spec["path"], spec["on_value"])
        print(f"{name}: on  ({spec['description']})")
    else:
        _remove_nested(settings, spec["path"])
        print(f"{name}: off  ({spec['description']})")
    _write_settings(settings)
    return 0
