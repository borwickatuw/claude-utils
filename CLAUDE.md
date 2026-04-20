# claude-utils

CLI utilities for managing Claude Code local data. Commands: `purge` (clean history/sessions/telemetry), `clip` (clean clipboard text), `defaults` (manage Claude Code settings in `~/.claude/settings.json`), `freq` (frequency counts), `no-ansi` (strip ANSI codes).

## Related Projects

- **claude-meta** - Cross-repo standards and audit tooling

## Security

Run `make security` before committing. This checks:
- Bandit Python security linter
- pip-audit for dependency vulnerabilities

## pysmelly

Read [docs/PYSMELLY.md](docs/PYSMELLY.md) before running pysmelly code smell analysis on this project.

## Cross-Repository Ideas

    claude-idea claude-utils "Description of the pattern or improvement"
