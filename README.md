# claude-utils

Utilities for managing Claude Code local data.

## Commands

### `claude-utils purge`

Remove conversation history, debug logs, telemetry, and other transient data from `~/.claude/` while preserving configuration, memory, and project instructions.

```
claude-utils purge [--dry-run] [--yes] [--claude-dir PATH]
```

## Install

```
cd claude-utils
uv tool install --editable .
```
