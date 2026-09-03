# Phase 12 — Live Persistence, Historical Charts, and Replay

Phase 12 is implemented. This document records the delivered architecture and its operational defaults.

## Summary

Use a hybrid pipeline optimized for chart latency:

1. Generate deterministic market data live.
2. Update in-memory state and publish immediately through the existing WebSocket.
3. Enqueue the same ordered batch for asynchronous PostgreSQL persistence.
4. Pause simulation when the bounded persistence queue reaches its safety threshold.
5. Use stored candles for historical charts and stored ticks for timed replay.

WebSockets remain a client transport, not an internal persistence mechanism. Pre-generated data is reserved for replay, testing, demos, and analysis.

## Implementation Changes

### Persistence pipeline

- Add an async PostgreSQL driver, connection-pool settings, and a storage interface with a PostgreSQL implementation.
- Represent each 250 ms step as one ordered persistence batch containing its 10 ticks, derived quotes, completed candles, and relevant state/behavior changes.
- Publish generated events to the live in-memory/WebSocket path without waiting for PostgreSQL.
- Have one background writer persist batches transactionally and in global sequence order using bulk operations.
- Use a bounded queue with configurable capacity and high-water mark. Pause simulated time when the threshold is reached; resume automatically after the writer recovers and the queue drains below a low-water mark.
- Never silently discard persistence batches. Mark a session incomplete or failed if shutdown or an unrecoverable database error prevents the queue from draining.
- On graceful pause, reset, completion, or shutdown, drain queued writes before applying the terminal session status.

### Schema and lifecycle alignment

- Add incremental migrations matching the updated consolidated schema; do not use the destructive platform bootstrap as the application migration path.
- Bring `simulation_sessions` lifecycle fields, configuration version, failure metadata, global tick uniqueness, quote idempotency, and replay indexes into the numbered migrations.
- Treat `(session_id, sequence_number)` as the authoritative tick order and `(session_id, symbol, timestamp)` as quote identity.
- Keep completed candles unique by session, symbol, interval, and timestamp.
- Upsert `market_states` as current session snapshots; preserve historical behavior changes in `market_behaviors`.
- Create a session on the first start after reset, retain it across pause/resume, and finalize it only after queued records are durable.
- A stored session is replay-complete only when its terminal status is `COMPLETED` or `RESET` and all queued writes were drained.

### Historical and replay interfaces

- Add:
  - `GET /simulation/sessions`
  - `GET /simulation/sessions/{session_id}`
  - `GET /simulation/sessions/{session_id}/ticks`
  - `GET /simulation/sessions/{session_id}/candles`
  - `WS /ws/replay/{session_id}`
- Use bounded cursor pagination; ticks paginate by global sequence and candles by timestamp.
- Replay persisted ticks in sequence order, preserving simulated timestamps while scaling wall-clock delays by playback speed.
- Support replay controls for pause, resume, speed change, and stop without affecting the live simulator.
- Label active, failed, or incompletely drained sessions as partial history rather than complete replay sources.

### Dashboard

- Add Live, Historical, and Replay modes to the existing dashboard.
- Live mode continues consuming `/ws/market`.
- Historical mode selects a stored session, symbol, and interval and renders persisted candles directly.
- Replay mode consumes `/ws/replay/{session_id}` and progressively updates the chart.
- Display session lifecycle, simulated date range, seed, persistence health, queue depth, writer lag, and partial/complete status.
- Default historical charts to candles because they are substantially cheaper to query and render than raw ticks.

## Public Types and Configuration

- Add a storage abstraction for session lifecycle, atomic batch persistence, paginated tick/candle reads, and readiness checks.
- Add internal `PersistenceBatch`, persistence-health, and replay-control models.
- Extend simulation status with `session_id`, `persistence_state`, `queue_depth`, `oldest_pending_age_ms`, `last_committed_sequence`, and `last_persistence_error`.
- Add environment settings for PostgreSQL URL, pool sizing, queue capacity, high/low water marks, write batch size, retry limits/backoff, shutdown drain timeout, history page limits, and replay speed bounds.
- Keep the existing live WebSocket envelope compatible; add typed replay lifecycle and error envelopes.

## Test Plan

- Verify live WebSocket publication does not wait for an intentionally delayed database write.
- Verify generated batches persist atomically and retain exact global sequence order.
- Verify transient database failures trigger retries and eventually recover without duplicates.
- Verify queue high-water pressure pauses simulated time and low-water recovery resumes it.
- Verify reset, completion, and graceful shutdown drain persistence before finalizing the session.
- Verify unrecoverable or timed-out writes produce an incomplete/failed session rather than a falsely complete replay.
- Verify session, tick, and candle pagination has stable ordering, validated limits, and correct symbol/interval filtering.
- Verify replay timing, filtering, pause/resume, speed changes, completion, and independent client controls.
- Verify historical charts load persisted candles and replay charts reproduce the stored path.
- Add a PostgreSQL-backed integration test suite plus existing unit/API/WebSocket regression tests.
- Benchmark generation-to-WebSocket latency, writer throughput, queue depth, and historical candle-query latency at the current 10-symbol/40-tick-per-second workload and under a defined burst load.

## Assumptions and Defaults

- Live chart latency is prioritized over commit-before-publish durability.
- Brief database delays are absorbed asynchronously; sustained pressure pauses generation before queued audit data is lost.
- A process crash can leave already-streamed events absent from storage; such a session must be identified as incomplete and cannot be advertised as a complete replay.
- PostgreSQL is the durable operational source of truth; process memory remains the lowest-latency live view.
- Stored candles power past graphs; stored ticks power detailed replay and audit.
- Redis, Kafka, Snowflake, multi-worker coordination, trading execution, and schema partitioning remain outside this phase until measurements justify them.
