# Phase 4 - Price Simulation Engine

Phase 4 adds deterministic stock price generation. It creates realistic-looking trade-price movement without generating quotes, spreads, volumes, ticks, candles, APIs, WebSockets, storage, or Phase 5 market behavior classes.

## What Phase 4 Created

Phase 4 added `app/simulation/price_engine.py`, which contains:

- `PriceSimulationConfig`
- `PricePoint`
- `PriceSimulationEngine`
- `DEFAULT_SIMULATED_STOCKS`

The engine is exported from `app/simulation/__init__.py`, so other code can import it from `app.simulation`.

Example:

```python
from datetime import datetime, timedelta

from app.simulation import DEFAULT_SIMULATED_STOCKS, MARKET_TIMEZONE, PriceSimulationEngine

engine = PriceSimulationEngine()
prices = engine.simulate(
    DEFAULT_SIMULATED_STOCKS,
    start_time=datetime(2026, 8, 31, 8, 30, tzinfo=MARKET_TIMEZONE),
    steps=5,
    step_size=timedelta(seconds=1),
)
```

## Files Created or Changed

Created:

- `app/simulation/price_engine.py`
- `tests/test_price_engine.py`
- `Docs/Phases/phase-4-price-simulation-engine.md`

Changed:

- `app/simulation/__init__.py`
- `pyproject.toml`
- `README.md`
- `AGENTS.md`

## Engine Details

`PriceSimulationConfig` configures:

- `seed`
- `drift`
- `minimum_price`

Important validation:

- `minimum_price` must be greater than zero.

`PriceSimulationEngine` supports:

- Generating one price step for one stock
- Generating repeated price steps for one or more stocks
- Replaying the same path after `reset()`
- Tracking sequence numbers per symbol
- Keeping prices above zero

`DEFAULT_SIMULATED_STOCKS` provides the first 10-stock simulation universe:

- `AAPL`
- `MSFT`
- `NVDA`
- `AMZN`
- `GOOGL`
- `META`
- `TSLA`
- `JPM`
- `XOM`
- `UNH`

## Price Model

Phase 4 uses a basic geometric Brownian motion model. In simple terms, each new price is based on:

- The previous price
- A small long-term directional drift
- The stock's volatility
- Random market noise from a seeded random number generator
- The amount of simulated time that passed

This avoids simple movement like `price += random_number`. Prices move by percentage-like changes, which better resembles how stock prices behave.

## Determinism

The engine uses NumPy's seeded random number generator:

```python
PriceSimulationConfig(seed=42)
```

The same seed, stock inputs, start time, step count, and step size produce the same prices. Different seeds can produce different paths.

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

Phase 4 adds NumPy as a runtime dependency because the price engine uses NumPy's deterministic random number generator.

## How To Run All Tests

From the `Simulated Engine` directory, with the virtual environment activated:

```powershell
python -m pytest
```

Or run pytest directly through the local virtual environment:

```powershell
..\.venv\Scripts\python.exe -m pytest
```

## How To Run Only Phase 4 Tests

Run just the price engine tests:

```powershell
..\.venv\Scripts\python.exe -m pytest tests\test_price_engine.py
```

Run one specific test by name:

```powershell
..\.venv\Scripts\python.exe -m pytest tests\test_price_engine.py -k seed
```

The `-k seed` option tells pytest to run only tests with `seed` in the test name.

## How To Run The Application

Phase 4 does not add any new API endpoints. The existing health endpoint from Phase 1 should still work.

Start the app:

```powershell
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/health
```

## Beginner-Friendly Concepts

A **price simulation engine** is the part of the simulator that decides the next trade price for each stock.

**Drift** is the small long-term directional tendency in the price model. Positive drift means the model has a slight upward pull over time.

**Volatility** means how jumpy the price is. A higher volatility value generally creates larger up and down movements.

**Random market noise** is the unpredictable part of the model. It is random-looking, but because it comes from a seed, tests can replay it exactly.

A **seed** is a starting value for the random number generator. If you use the same seed and the same inputs, you get the same simulated price path.

**Geometric Brownian motion** is a common simple model for stock-like movement. It changes prices by proportional movements instead of adding the same fixed amount each time.

A **price point** is one generated price at one simulated timestamp. It is not a full market tick yet because Phase 4 does not include bid, ask, spread, size, or volume.

## Design Decisions

- The price engine lives in `app/simulation/` because it is simulation logic, not API or streaming logic.
- The engine generates price points only. Quote, spread, volume, tick, and candle generation remain future phases.
- Prices are stored as `Decimal` values rounded to six decimal places to match the existing money model precision.
- The model treats volatility and drift as annualized inputs and converts elapsed seconds into a fraction of a regular trading year.
- Sequence numbers are tracked per symbol so future tick generation can build on this behavior.
- A default 10-stock universe was added to satisfy Phase 4 scope while keeping reference data simple and local.

## Phase Boundary

Phase 4 is complete when seeded price generation is deterministic, different seeds can produce different paths, prices remain valid and positive, and the engine can generate price points for the default 10-stock universe.

Do not begin Phase 5 until explicitly requested.
