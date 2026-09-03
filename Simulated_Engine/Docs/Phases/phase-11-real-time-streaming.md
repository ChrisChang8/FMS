# Phase 11 — Real-Time Streaming and Dashboard

Phase 11 exposes live simulation events at `WS /ws/market` and adds the local dashboard at `GET /`.

## WebSocket Protocol

Clients receive envelopes with `type`, `timestamp`, nullable `symbol`, and `data`. Channels are `tick`, `quote`, `candle`, and `status`. Optional comma-separated `symbols` and `channels` query parameters filter delivery. Each client has a bounded queue; when it fills, the oldest queued event is discarded so slow clients cannot block the producer.

Completed candles are streamed when the next interval begins. REST candle responses additionally include the current in-progress snapshot.

## Dashboard

The dependency-free HTML/CSS/JavaScript dashboard displays a selected stock's live chart, current price, quote, spread, recent ticks, simulation clock, and status. The chart labels simulated time and USD price axes and marks the latest tick price. Plain-language hover/focus help explains bid, ask, spread, and every market factor. The dashboard provides start, pause, and reset actions plus selected-stock sliders for liquidity, volume, volatility, behavior, and behavior strength. The UI loads initial data through REST and reconnects its WebSocket with exponential backoff.

Run `python -m uvicorn app.main:app --reload`, then open `http://127.0.0.1:8000/`.

This is a market-data simulation console only. It does not provide trading functionality and all data disappears when the process exits.
