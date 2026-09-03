# Phase 9 — Candle Aggregation

Phase 9 adds deterministic OHLCV candle aggregation in `app/simulation/candles.py`.

## What Was Added

- `CandleAggregator` consumes only validated `MarketTick` records.
- One-second (`1s`) and one-minute (`1m`) buckets are aligned in `America/Chicago`.
- Open, high, low, close, share volume, and trade count are updated from ticks.
- Each symbol and interval has independent in-progress state.
- Entering a new bucket emits the completed prior candle.
- Snapshots return defensive copies and reset clears all state.

No empty candles are synthesized for intervals without trades. Candle history is kept by the Phase 10 service in memory and is not persisted.

## Verification

Run `python -m pytest`. Tests cover OHLCV calculations, exact boundaries, interval and symbol isolation, ordering validation, snapshots, and reset.
