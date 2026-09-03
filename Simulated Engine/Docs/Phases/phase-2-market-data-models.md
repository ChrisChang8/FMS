# Phase 2 - Market Data Models

Phase 2 defines the core data objects used by the market data simulator. These models do not generate prices, advance time, stream data, or expose new API endpoints. They only describe the shape of valid market data and reject values that would make later simulation phases unreliable.

## What Phase 2 Created

Phase 2 added `app/models/market_data.py`, which contains the following Pydantic models:

- `Stock`
- `Quote`
- `MarketTick`
- `Candle`
- `MarketState`
- `MarketTrend`

The models are exported from `app/models/__init__.py`, so other code can import them from `app.models`.

Example:

```python
from app.models import Stock, Quote, MarketTick, Candle, MarketState
```

## Files Created or Changed

Created:

- `app/models/market_data.py`
- `tests/test_market_data_models.py`
- `Docs/Phases/phase-2-market-data-models.md`

Changed:

- `app/models/__init__.py`
- `pyproject.toml`
- `README.md`
- `AGENTS.md`

## Model Details

### Stock

`Stock` represents one simulated stock.

Fields:

- `symbol`
- `company_name`
- `starting_price`
- `sector`
- `average_volume`
- `base_volatility`

Important validation:

- Ticker symbols are normalized to uppercase.
- Ticker symbols must look like valid U.S. stock symbols.
- Starting price must be greater than zero.
- Average volume must be a positive integer.
- Base volatility cannot be negative.

### Quote

`Quote` represents current bid and ask information.

Fields:

- `symbol`
- `timestamp`
- `bid`
- `ask`
- `bid_size`
- `ask_size`

Important validation:

- `bid` must be lower than `ask`.
- Bid and ask prices must be greater than zero.
- Bid and ask sizes must be positive integers.
- Timestamp must include timezone information.

The model also exposes a `spread` property:

```python
spread = ask - bid
```

### MarketTick

`MarketTick` represents one raw market update.

Fields:

- `symbol`
- `timestamp`
- `price`
- `bid`
- `ask`
- `bid_size`
- `ask_size`
- `trade_volume`
- `sequence_number`

Important validation:

- `bid` must be lower than `ask`.
- `price` must be between `bid` and `ask`.
- Trade volume must be positive.
- Sequence number must be positive.
- Timestamp must include timezone information.

### Candle

`Candle` represents OHLCV market data.

Fields:

- `symbol`
- `interval`
- `timestamp`
- `open`
- `high`
- `low`
- `close`
- `volume`
- `trade_count`

Important validation:

- Interval must look like a simple duration, such as `1s`, `1m`, `5m`, `1h`, or `1d`.
- `high` must be the greatest of open, high, low, and close.
- `low` must be the smallest of open, high, low, and close.
- Volume and trade count must be positive.
- Timestamp must include timezone information.

### MarketState

`MarketState` represents current behavior inputs for a simulated stock.

Fields:

- `symbol`
- `trend`
- `volatility`
- `liquidity`
- `momentum`

Important validation:

- `trend` must be one of the values defined by `MarketTrend`.
- `volatility` cannot be negative.
- `liquidity` must be between `0.0` and `1.0`.
- `momentum` must be between `-1.0` and `1.0`.

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

The development dependencies include test tooling such as `pytest`.

## How To Run All Tests

From the `Simulated Engine` directory, with the virtual environment activated:

```powershell
python -m pytest
```

Or run pytest directly through the local virtual environment:

```powershell
..\.venv\Scripts\python.exe -m pytest
```

Expected result:

```text
12 passed
```

The exact runtime may vary. A pytest cache warning does not necessarily mean the test suite failed; the important result is that all tests pass.

## How To Run Only Phase 2 Tests

Run just the market data model tests:

```powershell
..\.venv\Scripts\python.exe -m pytest tests\test_market_data_models.py
```

Run one specific test by name:

```powershell
..\.venv\Scripts\python.exe -m pytest tests\test_market_data_models.py -k quote
```

The `-k quote` option tells pytest to run only tests with `quote` in the test name.

## How To Run The Application

Phase 2 does not add any new API endpoints. The existing health endpoint from Phase 1 should still work.

Start the app:

```powershell
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
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

## Beginner-Friendly Concepts

A **model** is a structured description of data. Instead of passing around loose dictionaries, the simulator uses models so each object has clear fields and rules.

A **ticker symbol** is the short stock identifier, such as `AAPL`, `MSFT`, or `NVDA`.

A **bid** is the simulated price a buyer is willing to pay.

An **ask** is the simulated price a seller is willing to accept.

A **spread** is the difference between ask and bid. For example, if the bid is `100.00` and the ask is `100.05`, the spread is `0.05`.

A **tick** is one raw market update. Later phases will generate streams of ticks, but Phase 2 only defines what a valid tick looks like.

A **candle** summarizes activity over a time interval. `OHLCV` means open, high, low, close, and volume.

**Liquidity** means how easy it is to trade a stock in the simulation. Higher liquidity usually means tighter spreads and smoother activity in future phases.

**Volatility** means how much the price tends to move. Higher volatility usually means bigger price changes in future phases.

**Momentum** means directional pressure. Positive momentum suggests upward pressure; negative momentum suggests downward pressure.

## Design Decisions

- Models are pure data and validation objects.
- No simulation clock was added in Phase 2.
- No price generation was added in Phase 2.
- No WebSocket or streaming behavior was added in Phase 2.
- `Decimal` is used for prices to avoid floating-point rounding surprises in money-like values.
- Timestamps must include timezone information so future phases do not have to guess which timezone a tick or candle belongs to.
- Validation rules are intentionally simple and deterministic so tests return the same results every time.

## Phase Boundary

Phase 2 is complete when the models exist, validation works, and tests cover important model rules.

Do not begin Phase 3 until explicitly requested.
