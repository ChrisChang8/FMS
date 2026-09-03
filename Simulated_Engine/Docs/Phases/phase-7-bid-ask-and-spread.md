# Phase 7 — Bid, Ask, and Spread

Phase 7 adds deterministic top-of-book quote prices without beginning Phase 8 tick generation.

## What Was Created

- `QuoteSimulationConfig` configures the random seed, base spread in basis points, minimum tick size, volatility sensitivity, and bounded spread variation.
- `QuoteSimulationEngine` generates bid and ask prices around a supplied reference price using current liquidity and volatility.
- `QuotePoint` records the symbol, normalized Chicago timestamp, bid, and ask and exposes their difference as `spread`.
- Public exports make the Phase 7 types available from `app.simulation`.
- Tests cover replay, reset behavior, quote validity, liquidity and volatility effects, tick alignment, and invalid inputs.

## Spread Model

The engine begins with a spread proportional to the reference price:

```text
reference price × base spread basis points / 10,000
```

It multiplies that baseline by a liquidity factor from `1.5 - liquidity`, so higher liquidity produces a smaller spread. It also multiplies by `1 + volatility × sensitivity`, so more volatile conditions produce a larger spread. A small seeded variation prevents every quote under identical market conditions from having exactly the same width while preserving deterministic replay.

The configured minimum tick acts as the spread floor. The bid is rounded down and the ask is rounded up to valid tick increments, which ensures the bid remains below the ask. With the default configuration, the tick size is one cent.

## Configuration Example

```python
from decimal import Decimal

from app.simulation import QuoteSimulationConfig, QuoteSimulationEngine

engine = QuoteSimulationEngine(
    QuoteSimulationConfig(
        seed=42,
        base_spread_bps=Decimal("2"),
        minimum_tick=Decimal("0.01"),
    )
)

quote = engine.step(
    "AAPL",
    timestamp=simulated_time,
    reference_price=Decimal("224.15"),
    liquidity=0.9,
    volatility=Decimal("0.2"),
)
```

## Assumptions and Decisions

- The reference price is the midpoint anchor, not a generated trade. A later orchestration layer can supply a Phase 4 price.
- Liquidity remains on the Phase 6 normalized `0.0` to `1.0` scale.
- Volatility is a non-negative decimal input, allowing behavior-adjusted volatility to be supplied without coupling the quote engine to the behavior engine.
- Money calculations use `Decimal`; seeded NumPy randomness is converted through strings before entering the decimal calculation.
- Bid and ask are top-of-book prices only. Phase 7 does not model individual orders, market depth, or a full order book.
- Quote sizes are excluded. They become part of the complete raw market update when Phase 8 is explicitly implemented.
- Sequence numbers are also deferred to Phase 8 because Phase 7 produces quotes rather than the continuous tick stream.

## Files Created or Changed

- `app/simulation/quotes.py`
- `app/simulation/__init__.py`
- `tests/test_quote_engine.py`
- `README.md`
- `AGENTS.md`
- `Docs/Phases/phase-7-bid-ask-and-spread.md`

## Run and Test

Install dependencies and run the complete suite:

```powershell
python -m pip install -e ".[dev]"
python -m pytest
```

At Phase 7 completion, the full suite contains 89 passing tests.

## Phase Boundary

Phase 7 is complete. Phase 8 has not been started: there is no continuous tick generator, quote-size generator, combined market update, or stream sequencing.
