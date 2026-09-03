# Phase 6 — Volume and Liquidity

Phase 6 adds deterministic market activity levels without beginning Phase 7 quote generation.

## What Was Created

- `StockActivityConfig` configures a stock's liquidity from `0.0` to `1.0` and an optional positive volume multiplier.
- `ActivitySimulationConfig` provides the random seed and default per-stock activity configuration.
- `MarketActivityEngine` generates interval share volume, supports symbol-specific overrides, tracks per-symbol sequences, and resets deterministically.
- `ActivityPoint` records the symbol, timestamp, interval trade volume, liquidity, price-volatility multiplier, and activity sequence number.
- Phase 6 tests cover deterministic replay, seed differences, liquidity behavior, volume overrides, validation, sequencing, and reset behavior.

## Activity Model

The engine starts with a stock's `average_volume`, which represents a normal full-session daily volume. It scales that value by the elapsed interval as a fraction of the 6.5-hour regular session. A per-stock volume multiplier and a monotonic liquidity factor then adjust the expected number of shares.

The final interval volume is sampled from a Poisson distribution. This distribution is useful for counts of events or shares occurring during a fixed interval: results vary naturally while remaining non-negative. Because the engine uses a configured NumPy seed, the same calls with the same configuration reproduce the same volumes.

Liquidity also produces a price-volatility multiplier from `1.5 - liquidity`. At liquidity `1.0`, the multiplier is `0.5`; at liquidity `0.0`, it is `1.5`. This gives later orchestration code a clean value for making liquid-stock pricing smoother and illiquid-stock pricing more irregular without coupling activity generation to the price engine.

## Configuration Example

```python
from datetime import timedelta

from app.simulation import MarketActivityEngine, StockActivityConfig

engine = MarketActivityEngine()
engine.configure_stock(
    "AAPL",
    StockActivityConfig(liquidity=0.9, volume_multiplier=1.1),
)

activity = engine.step(stock, timestamp=simulated_time, elapsed=timedelta(seconds=1))
```

## Assumptions and Decisions

- Liquidity uses a normalized `0.0` to `1.0` scale so configurations remain easy to compare.
- Zero-share intervals are valid, especially for low-volume or low-liquidity stocks over short time steps.
- The volume model is uniform across the regular session. Market-open and end-of-day volume curves remain Phase 15 work.
- Phase 6 exposes a price-volatility multiplier but does not create a combined tick pipeline; continuous ticks belong to Phase 8.
- Bid, ask, spread, and quote sizes are deliberately excluded because they belong to Phase 7.
- Existing stock `average_volume` values remain the per-stock baseline, while activity overrides keep Phase 6 controls separate from core reference data.

## Files Created or Changed

- `app/simulation/activity.py`
- `app/simulation/__init__.py`
- `tests/test_market_activity.py`
- `pyproject.toml`
- `README.md`
- `AGENTS.md`
- `Docs/Phases/phase-6-volume-and-liquidity.md`

`pytz` was added to development dependencies because the existing Phase 5 test suite imports it.

## Run and Test

Install dependencies and run the complete suite:

```powershell
python -m pip install -e ".[dev]"
python -m pytest
```

At Phase 6 completion, the full suite contains 75 passing tests.

## Phase Boundary

Phase 6 is complete. Phase 7 has not been started: there is no bid, ask, spread, or quote-generation engine.
