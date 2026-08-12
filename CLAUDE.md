# claude-utils

CLI utilities for managing Claude Code local data. Commands: `purge` (clean history/sessions/telemetry), `clip` (clean clipboard text), `defaults` (manage Claude Code settings in `~/.claude/settings.json`), `freq` (frequency counts), `no-ansi` (strip ANSI codes).

## Related Projects

- **claude-meta** - Cross-repo standards and audit tooling

## Security

Run `make security` before committing. This checks:
- Bandit Python security linter
- `uv audit` for dependency CVEs + adverse statuses

**No secrets gate, by decision.** This repo has no `.secrets.baseline` and no
`security-secrets` target. `SECURITY.md` Practice #8 scopes that gate to apps
with credentials, and this repo handles none: no `.env` or `.env.example`, and
no tracked file contains a credential-shaped string (verified 2026-08-12
across all 24 tracked files). The absence is deliberate, not an oversight —
revisit if this repo ever gains credentials or environment config.

## pysmelly

Read [docs/PYSMELLY.md](docs/PYSMELLY.md) before running pysmelly code smell analysis on this project.

## Cross-Repository Ideas

    claude-idea claude-utils "Description of the pattern or improvement"
