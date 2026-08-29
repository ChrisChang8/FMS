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

## Development Rules for the Agent

Work on one phase at a time.

Do not implement future phases early.

When asked to start a phase:

1. Read Docs/DATA_ROADMAP.md first.
2. Review the existing repository before making changes.
3. Implement only the requested phase.
4. Keep the architecture compatible with future phases.
5. Prefer readable, typed, modular Python code.
6. Write deterministic tests wherever possible.
7. Keep mathematical logic separate from API and streaming logic.
8. Avoid unnecessary infrastructure and over-engineering.
9. Explain unfamiliar financial or mathematical concepts simply.
10. Stop after completing the requested phase.

At the end of each phase:

- Summarize what was created
- List files created or changed
- Explain how to run and test the phase
- Explain important technical concepts simply
- Document important assumptions or design decisions
- Do not automatically begin the next phase

## Core Principle

The goal is not to create random stock prices.

The goal is to create a small, realistic, deterministic market-data simulator whose output resembles a simplified live U.S. market-data feed and can later be consumed by other systems.
