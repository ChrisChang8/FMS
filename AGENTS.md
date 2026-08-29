# Agent Notes

This repository is intentionally minimal right now. Future Codex agents should use this file as the starting point for orientation, then update it as the project structure becomes more concrete.

## Repository Map

- `README.md` - Public-facing project overview. It is currently empty.
- `Docs/` - Intended home for repository documentation, design notes, requirements, and implementation references. It is currently empty.
- `AGENTS.md` - Agent-facing navigation and maintenance notes.

## How To Work Here

1. Start by reading `AGENTS.md`, then check `README.md` and anything added under `Docs/`.
2. Use `rg --files` to discover the current project structure before making assumptions.
3. Keep new documentation in `Docs/` unless a conventional root-level file is more appropriate.
4. When adding major source directories, tools, setup steps, or testing commands, update this file so future agents can find them quickly.
5. Preserve the repository's clean baseline: avoid unrelated generated files, broad refactors, or noisy metadata changes.

## Documentation Hygiene

As this repository grows, consider adding:

- `Docs/architecture.md` for system structure and major decisions.
- `Docs/setup.md` for local development instructions.
- `Docs/testing.md` for verification commands and expected test coverage.
- `Docs/decisions/` for notable design or implementation decisions.

