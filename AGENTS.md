# Agent Notes

This repository contains the foundation for FMS, a local Python/FastAPI U.S. stock market data simulator. Future Codex agents should use this file as the starting point for orientation, then read the roadmap before making phase-specific changes.

## Repository Map

- `README.md` - Public-facing project overview, setup, run, and test instructions.
- `Docs/DATA_ROADMAP.md` - Phase-by-phase market data simulator roadmap and constraints.
- `AGENTS.md` - Agent-facing navigation and maintenance notes.
- `pyproject.toml` - Python project metadata, dependencies, and pytest configuration.
- `app/main.py` - FastAPI app factory and application instance.
- `app/api/` - API route modules. Phase 1 includes only the health endpoint.
- `app/core/` - Core application infrastructure such as typed settings and structured logging.
- `app/models/` - Placeholder package for future market data models. Do not add Phase 2 models before Phase 2 starts.
- `app/simulation/` - Placeholder package for future simulation engines.
- `app/services/` - Placeholder package for future service-layer code.
- `app/streaming/` - Placeholder package for future WebSocket and streaming code.
- `app/storage/` - Placeholder package for future storage and replay code.
- `tests/` - pytest suite. Phase 1 covers the health endpoint.

## How To Work Here

1. Start by reading `AGENTS.md`, then check `README.md` and anything added under `Docs/`.
2. Use `rg --files` to discover the current project structure before making assumptions.
3. Keep new documentation in `Docs/` unless a conventional root-level file is more appropriate.
4. When adding major source directories, tools, setup steps, or testing commands, update this file so future agents can find them quickly.
5. Preserve the repository's clean baseline: avoid unrelated generated files, broad refactors, or noisy metadata changes.

## Current Phase Status

Phase 1 is implemented:

- Python project configuration exists.
- FastAPI starts from `app.main:app`.
- `GET /health` returns the application health status.
- Typed settings use the `FMS_` environment variable prefix.
- Structured JSON-style logging is configured during app creation.
- pytest is configured and includes a health endpoint test.

Do not begin Phase 2 unless the user explicitly asks for Phase 2.

## Common Commands

Install development dependencies:

```powershell
python -m pip install -e ".[dev]"
```

Run the app:

```powershell
python -m uvicorn app.main:app --reload
```

Run tests:

```powershell
python -m pytest
```

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
