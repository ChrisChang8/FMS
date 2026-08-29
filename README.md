# FMS Market Data Simulator

FMS is a local Python project for building a realistic, deterministic U.S. stock market data simulator. The project will eventually generate simulated prices, quotes, ticks, volume, volatility, candles, and real-time streams that another application can consume.

This repository is currently on **Phase 1: Project Foundation** from [Docs/DATA_ROADMAP.md](Docs/DATA_ROADMAP.md).

## Phase 1 Scope

Phase 1 creates only the application foundation:

- Python project configuration
- FastAPI application startup
- Typed configuration management
- Structured logging
- Basic health endpoint
- pytest test setup
- Placeholder package structure for future phases

Phase 1 does **not** implement stock models, market ticks, candles, simulation clocks, price movement, streaming, storage, trading, portfolios, brokerage behavior, or real-money functionality.

## Project Structure

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
```

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the project with development dependencies:

```powershell
python -m pip install -e ".[dev]"
```

## Run the Application

Start the FastAPI development server:

```powershell
python -m uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "FMS Market Data Simulator",
  "environment": "local"
}
```

## Run Tests

```powershell
python -m pytest
```

## Configuration

Settings are loaded through typed Pydantic settings with the `FMS_` environment variable prefix.

Available Phase 1 settings:

- `FMS_APP_NAME`
- `FMS_ENVIRONMENT`
- `FMS_LOG_LEVEL`

For example:

```powershell
$env:FMS_ENVIRONMENT = "development"
python -m uvicorn app.main:app --reload
```

## Important Concepts

A **health endpoint** is a simple API route that confirms the application can start and respond to requests.

**Typed configuration** means settings have expected names and value types, which helps catch mistakes early.

**Structured logging** writes logs in a consistent machine-readable shape, making later debugging and monitoring easier.

**Deterministic tests** are tests that should return the same result every time they run.
