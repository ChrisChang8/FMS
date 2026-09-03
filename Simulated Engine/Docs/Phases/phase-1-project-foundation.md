# Phase 1 - Project Foundation

Phase 1 creates the basic Python/FastAPI foundation for the market data simulator. It does not generate market data, define stock/tick/candle models, advance simulated time, stream updates, store history, or implement trading features.

## What Phase 1 Created

Phase 1 added a small FastAPI application with:

- Project metadata and dependency configuration
- A clear application package structure
- Typed configuration management
- Structured JSON-style logging
- A basic health endpoint
- pytest configuration and a health endpoint test
- Public and agent-facing documentation

## Files Created or Changed

Created:

- `pyproject.toml`
- `.gitignore`
- `app/__init__.py`
- `app/main.py`
- `app/api/__init__.py`
- `app/api/health.py`
- `app/core/__init__.py`
- `app/core/config.py`
- `app/core/logging.py`
- `app/models/__init__.py`
- `app/services/__init__.py`
- `app/simulation/__init__.py`
- `app/storage/__init__.py`
- `app/streaming/__init__.py`
- `tests/test_health.py`
- `Docs/Phases/phase-1-project-foundation.md`

Changed:

- `README.md`
- `AGENTS.md`

## Application Structure

The project uses this package layout:

```text
app/
    api/          FastAPI route modules
    core/         Configuration and logging
    models/       Future market data models
    services/     Future application services
    simulation/   Future simulation engines
    storage/      Future storage and replay support
    streaming/    Future real-time streaming support

tests/            Automated tests
Docs/             Roadmap and project documentation
Docs/Phases/      Phase-specific implementation notes
```

The placeholder packages exist so future phases have an obvious home. They should stay lightweight until their roadmap phase begins.

## Configuration

Phase 1 settings live in `app/core/config.py`.

Settings are loaded with Pydantic settings and use the `FMS_` environment variable prefix.

Available settings:

- `FMS_APP_NAME`
- `FMS_ENVIRONMENT`
- `FMS_LOG_LEVEL`

Default values:

```text
app_name = FMS Market Data Simulator
environment = local
log_level = INFO
```

## Health Endpoint

Phase 1 exposes:

```text
GET /health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "FMS Market Data Simulator",
  "environment": "local"
}
```

The health endpoint only confirms the application foundation is working. It does not report simulation status because the simulator does not exist in Phase 1.

## How To Set Up The Project

From the `Simulated Engine` directory:

```powershell
cd "Simulated Engine"
```

Create a virtual environment if one does not already exist:

```powershell
python -m venv ../.venv
```

Activate it:

```powershell
..\.venv\Scripts\Activate.ps1
```

Install the project with development dependencies:

```powershell
python -m pip install -e ".[dev]"
```

## How To Run The Application

From the `Simulated Engine` directory, with dependencies installed:

```powershell
python -m uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/health
```

## How To Run Tests

Run all tests:

```powershell
python -m pytest
```

Run only the Phase 1 health test:

```powershell
python -m pytest tests\test_health.py
```

Expected Phase 1-only result:

```text
1 passed
```

Later phases add more tests, so the full test count will grow over time.

## Beginner-Friendly Concepts

A **FastAPI application** is a Python web app that can expose URLs other software can call.

An **endpoint** is one URL handled by the app. In Phase 1, `/health` is the only endpoint.

A **health endpoint** is a simple status check. It tells you the app can start and respond.

**Typed configuration** means settings have expected names and value types, which helps catch mistakes early.

**Structured logging** means logs follow a consistent shape. This makes them easier for people and tools to search later.

**pytest** is the test runner used to confirm the project behaves as expected.

An **editable install** means Python imports the project directly from this checkout, so local code changes are picked up without rebuilding a package.

## Design Decisions

- Phase 1 uses plain `pip` and editable installs instead of adding Poetry, Hatch, Docker, or other infrastructure.
- Logging uses the Python standard library to keep the foundation small.
- The app is created through `create_app()` so future phases can configure routes and dependencies cleanly.
- The health endpoint returns only application-level status.
- Placeholder packages are allowed, but they do not contain simulation logic yet.

## Phase Boundary

Phase 1 is complete when the app starts, `/health` works, tests run, and the structure is easy to understand.

Do not begin Phase 2 unless explicitly requested.
