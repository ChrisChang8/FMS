# FMS Market Data Simulator

FMS is a local Python project for building a realistic, deterministic U.S. stock market data simulator. The project will eventually generate simulated prices, quotes, ticks, volume, volatility, candles, and real-time streams that another application can consume.

This repository has completed **Phase 5: Market Behavior Engine** from [Docs/DATA_ROADMAP.md](Docs/DATA_ROADMAP.md).

## Implemented Scope

Phase 1 created the application foundation:

- Python project configuration
- FastAPI application startup
- Typed configuration management
- Structured logging
- Basic health endpoint
- pytest test setup
- Placeholder package structure for future phases

Phase 2 adds the core market data models:

- `Stock` for simulated stock reference data
- `Quote` for bid and ask snapshots
- `MarketTick` for raw market updates
- `Candle` for OHLCV market data
- `MarketState` for behavior inputs such as trend, volatility, liquidity, and momentum

Phase 3 adds the simulation clock:

- Deterministic simulated market time
- Configurable start time and speed
- Pause, resume, reset, and manual time advancement
- Regular market session checks from 8:30 AM to 3:00 PM Central Time
- Consistent `America/Chicago` timezone handling

Phase 4 adds the price simulation engine:

- Seeded deterministic stock price generation
- A geometric Brownian motion price model using previous price, drift, volatility, random noise, and elapsed time
- Positive price protection with six-decimal money precision
- Per-symbol sequence numbers for generated price points
- A default local universe of 10 simulated U.S. stocks

Phase 5 adds the market behavior engine:

- 10 controllable market behaviors (normal, uptrend, downtrend, sideways, momentum, mean reversion, breakout, breakdown, consolidation, volatility spike)
- Modular behavior architecture that adjusts drift and volatility independently
- Configuration-based behavior creation and application
- Behavior lifecycle management (start, end, active tracking)
- Support for multiple simultaneous behaviors per stock
- Full integration with Phase 4 price engine

The project does **not** yet implement bid/ask quote generation, volume generation, tick generation, candle aggregation, streaming, storage, trading, portfolios, brokerage behavior, or real-money functionality.

## Project Structure

```text
app/
    api/          FastAPI route modules
    core/         Configuration and logging
    models/       Pydantic market data models
    services/     Future application services
    simulation/   Simulation clock and price engine
    storage/      Future storage and replay support
    streaming/    Future real-time streaming support

tests/            Automated tests
Docs/             Roadmap and project documentation
Docs/Phases/      Phase-specific implementation notes
notebooks/        Optional VS Code/Jupyter notebooks for visualizing simulator output
```

Detailed phase notes are available in:

- [Docs/Phases/phase-1-project-foundation.md](Docs/Phases/phase-1-project-foundation.md)
- [Docs/Phases/phase-2-market-data-models.md](Docs/Phases/phase-2-market-data-models.md)
- [Docs/Phases/phase-3-simulation-clock.md](Docs/Phases/phase-3-simulation-clock.md)
- [Docs/Phases/phase-4-price-simulation-engine.md](Docs/Phases/phase-4-price-simulation-engine.md)
- [Docs/Phases/phase-5-market-behavior-engine.md](Docs/Phases/phase-5-market-behavior-engine.md)

## Notebooks

The [notebooks](notebooks/) folder contains optional VS Code/Jupyter notebooks for visually inspecting simulator output. These notebooks are not part of the FastAPI application; they are local exploration tools for checking whether generated data looks reasonable.

Notebook-specific instructions live in [notebooks/NOTEBOOKS.md](notebooks/NOTEBOOKS.md).

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

If you are using the local virtual environment in this checkout:

```powershell
.\.venv\Scripts\python.exe -m pytest
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

A **stock model** describes one simulated company, such as its ticker symbol, starting price, sector, normal trading volume, and baseline volatility.

A **quote** is the current best simulated buying price and selling price. The bid is what a buyer is willing to pay, and the ask is what a seller is willing to accept. The bid must stay below the ask.

A **market tick** is one raw market update. It contains a trade price, bid, ask, sizes, volume, timestamp, and sequence number.

A **candle** summarizes trades over an interval. OHLCV means open, high, low, close, and volume.

A **market state** describes the simulated behavior being applied to a stock, such as whether it is trending up or down, how volatile it is, how liquid it is, and how much momentum it has.

A **health endpoint** is a simple API route that confirms the application can start and respond to requests.

**Typed configuration** means settings have expected names and value types, which helps catch mistakes early.

**Structured logging** writes logs in a consistent machine-readable shape, making later debugging and monitoring easier.

**Deterministic tests** are tests that should return the same result every time they run.

A **simulation clock** is a clock controlled by the simulator. It lets tests and future simulation engines move market time forward without relying on the exact time on your computer.

**Simulated time** is the time inside the market simulation. It can move faster than real time, pause, resume, or jump forward during tests.

**Simulation speed** controls how fast simulated time moves. A speed of `1.0` means one simulated second per real second. A speed of `2.0` means two simulated seconds per real second.

**America/Chicago** is the timezone used for simulated market timestamps.

The **regular trading session** is the part of the day treated as normal market hours. In Phase 3, that is `8:30 AM` through just before `3:00 PM` Central Time.

A **price simulation engine** is the part of the simulator that decides the next trade price for each stock.

**Drift** is the small long-term directional tendency in the price model.

**Volatility** means how jumpy the price is. Higher volatility generally creates larger simulated movements.

**Random market noise** is the unpredictable part of the model. It looks random, but a seed lets tests replay it exactly.

A **seed** is a starting value for the random number generator. Same seed plus same inputs means the same simulated price path.

**Geometric Brownian motion** is a simple stock-like movement model. It changes prices by proportional moves rather than by adding a fixed random amount.

A **price point** is one generated price at one simulated timestamp. It is not a full market tick yet because Phase 4 does not include bid, ask, spread, size, or volume.
