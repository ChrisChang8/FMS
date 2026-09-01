# Phase 8 — Tick Generation

Phase 8 creates the continuous raw market-data stream by composing the price, activity, and quote engines implemented in Phases 4, 6, and 7.

## What Was Added

- `TickSimulationConfig` configures the master seed and average top-of-book size.
- `TickSimulationConfig` also exposes the baseline drift used before behavior adjustments.
- `TickSimulationEngine` generates validated `MarketTick` objects.
- One call to `step()` combines:
  - a liquidity and volume observation;
  - active behavior adjustments to drift and volatility;
  - a liquidity-adjusted simulated trade price;
  - a bid and ask around that price;
  - seeded, liquidity-aware bid and ask sizes;
  - a global tick sequence number.
- `simulate()` produces one tick per stock per time step and supports the default 10-stock universe.
- `reset()` resets every component engine, random stream, sequence number, and timestamp so a stream can be replayed exactly.
- Behaviors can be attached directly or created from `MarketBehaviorConfig` through the tick engine.

## Stream Guarantees

- The same seed, stock configuration, stock order, and timing inputs reproduce the same complete tick stream.
- The same behavior configuration and start times must also be supplied when replaying a behavior-driven stream.
- Sequence numbers are global to the stream and increase by one for every tick.
- Stocks generated during the same step share a timestamp; timestamps are therefore nondecreasing rather than required to be unique.
- A direct `step()` call rejects a timestamp earlier than the last emitted tick.
- Every tick satisfies `bid < ask` and `bid <= price <= ask` through the existing `MarketTick` validation.
- Sub-cent reference prices remain internally consistent even when the configured quote tick size is one cent.
- Bid size, ask size, and trade volume are always positive.
- All timestamps are normalized to `America/Chicago`.

## Important Decisions

### Global sequence numbers

The component engines track some values per symbol, but the finished raw feed uses a single global sequence. This makes ordering unambiguous when updates from all 10 stocks are interleaved.

### Trade volume

The activity engine models interval volume and can legitimately sample zero shares for a very short interval. A `MarketTick` represents an actual trade event, so Phase 8 promotes a zero sample to one share. This preserves the existing positive-volume model contract.

### Liquidity and quote sizes

Higher liquidity raises the expected bid and ask size. Sizes are sampled independently from a seeded Poisson distribution and are clamped to at least one share.

### Price and liquidity integration

The activity engine's volatility multiplier is applied to the stock's base volatility before generating the next price. High-liquidity stocks therefore tend to move more smoothly, while low-liquidity stocks tend to move more irregularly, as established in Phase 6.

### Behavior integration

For each tick, the behavior engine first adjusts baseline drift and stock volatility. The activity engine's liquidity multiplier is then applied to that behavior-adjusted volatility. The price engine receives the adjusted drift and final volatility, and the quote engine receives the same final volatility. This makes behaviors visible in both trade prices and spreads while keeping the dependency flow deterministic and one-directional.

```text
behavior + base drift/volatility
              |
              v
activity/liquidity adjustment
              |
              v
         price engine
              |
              v
         quote engine
              |
              v
          market tick
```

Calling `reset()` clears active behaviors along with the generated stream state. A caller replaying a behavior-driven scenario should reset the engine and then add the same behavior configuration at the same simulated start time.

### Scope boundary

Phase 8 only creates raw ticks. It does not aggregate candles, expose APIs, stream over WebSockets, or write ticks to storage. Those remain later roadmap phases.

## Files Created or Changed

- `app/simulation/ticks.py`
- `app/simulation/__init__.py`
- `tests/test_tick_engine.py`
- `README.md`
- `AGENTS.md`
- `Docs/Phases/phase-8-tick-generation.md`

## Test Coverage

The Phase 8 tests verify:

- deterministic replay with the same seed;
- different output from different seeds;
- generation for all 10 default stocks;
- nondecreasing timestamps;
- globally increasing sequence numbers;
- internally consistent prices and quotes;
- internally consistent sub-cent ticks;
- positive trade and quote sizes;
- deterministic reset behavior;
- liquidity-aware quote sizes;
- behavior-adjusted prices and quote spreads;
- behavior expiration;
- rejection of timestamp regressions and invalid configuration.

Run the complete suite with:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

At Phase 8 completion, the suite contains 102 passing tests.
