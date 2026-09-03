# Phase 10 — Market Data API

Phase 10 adds an application service and FastAPI routes around the simulation engines.

## Runtime

`SimulationService` owns the clock, tick engine, candle aggregator, latest quotes, factor settings, and bounded histories. It advances simulated time by an exact 250 milliseconds per batch and produces one tick for each of the ten stocks. Tick history is limited to 1,000 records per symbol; candle history is limited to 500 records per symbol and interval.

The service is process-local. Pause preserves state, while reset pauses and restores the original seed, time, factors, engines, and empty histories.

## Endpoints

- `GET /stocks`
- `GET /quotes/{symbol}`
- `GET /ticks/{symbol}?limit=100`
- `GET /candles/{symbol}?interval=1s&limit=100`
- `GET /simulation/status`
- `POST /simulation/start`, `/pause`, and `/reset`
- `PATCH /simulation/stocks/{symbol}/factors`

Factor controls are liquidity, volume multiplier, volatility multiplier, behavior type, and behavior strength. They apply to future ticks for the selected symbol. Non-normal behavior replaces the previous controlled behavior for that symbol and expires after 30 simulated minutes.

There are no order, portfolio, account, storage, or replay endpoints.
