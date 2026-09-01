# Migrations

Plain, sequentially-numbered SQL files for the PostgreSQL schema used to persist
simulated market data and behaviors (Phase 12 of `Docs/DATA_ROADMAP.md`). No
migration framework is used, so no new Python dependency is required.

## Naming convention

`NNNN_short_description.sql`, applied in ascending numeric order. Each file is
up-only (no rollback script) and contains one logical schema change.

## Applying migrations

Requires a reachable PostgreSQL database and `psql` on `PATH`. Set
`DATABASE_URL` (or any `psql`-compatible connection string) first.

PowerShell:

```powershell
Get-ChildItem migrations\*.sql | Sort-Object Name | ForEach-Object {
    psql $env:DATABASE_URL -v ON_ERROR_STOP=1 -f $_.FullName
}
```

Bash:

```bash
for f in migrations/*.sql; do
    psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$f"
done
```

## Schema overview

Every table below lists its columns with a short explanation of what each one
represents. Table constraints (e.g. `bid < ask`, OHLC high/low bounds, ratio
ranges) mirror the validators in `app/models/market_data.py` and
`app/simulation/behaviors.py`.

### `simulation_sessions`

One row per simulation run. Everything else references `id` here for
grouping and replay.

| Column | Meaning |
| --- | --- |
| `id` | Primary key; the session identifier every other table references. |
| `seed` | Random number generator seed. Same seed + same config reproduces the exact same simulated prices. |
| `drift` | The global expected trend used to configure this run, e.g. `0.08` means prices lean upward ~8%/year on average before randomness is applied. Positive = upward lean, negative = downward lean, zero = no long-term trend. |
| `config` | Catch-all JSON bag for other run settings (e.g. clock speed) that don't need their own column. |
| `started_at` | When the simulation began, in simulated time. |
| `ended_at` | When the simulation finished; `NULL` while still running. |
| `created_at` | When this database row was inserted (wall-clock, for auditing). |

### `stocks`

Static reference/setup data for a simulated ticker (mirrors `Stock`). Doesn't
change during a run.

| Column | Meaning |
| --- | --- |
| `symbol` | Primary key; the uppercase ticker symbol (e.g. `AAPL`). |
| `company_name` | Display name for the simulated company. |
| `starting_price` | The price the stock begins a simulation at. |
| `sector` | Simulated industry grouping (e.g. `Technology`). |
| `average_volume` | Typical number of shares traded, used to scale realistic volume generation. |
| `base_volatility` | How bumpy this stock's price is ($\sigma$ in the price model) — higher values mean bigger random swings around the trend. |
| `created_at` | When this database row was inserted. |

### `market_states`

The *current* snapshot of how a stock is behaving right now, one row per
`(session_id, symbol)` — gets overwritten as the simulation progresses
(mirrors `MarketState`).

| Column | Meaning |
| --- | --- |
| `id` | Primary key. |
| `session_id` | Which simulation run this snapshot belongs to. |
| `symbol` | Which stock this snapshot describes. |
| `trend` | Current broad direction: `normal`, `uptrend`, `downtrend`, or `sideways`. |
| `volatility` | Current effective volatility for this stock (may differ from `stocks.base_volatility` if a behavior is adjusting it). |
| `liquidity` | Ratio from 0 to 1 describing how actively traded the stock currently is. Higher liquidity generally means smaller spreads and smoother pricing. |
| `momentum` | Ratio from -1 to 1 describing how strongly recent price movement is continuing in one direction. |
| `updated_at` | When this snapshot was last refreshed. |

### `market_behaviors`

Append-only history log of every behavior ever applied to a stock (mirrors
`MarketBehaviorConfig`/`BehaviorType`). Unlike `market_states`, rows here are
never overwritten, so past behaviors can be audited or replayed.

| Column | Meaning |
| --- | --- |
| `id` | Primary key. |
| `session_id` | Which simulation run this behavior was applied in. |
| `symbol` | Which stock the behavior was applied to. |
| `behavior_type` | One of the 10 supported behaviors (e.g. `uptrend`, `mean_reversion`, `volatility_spike`). |
| `start_time` | When the behavior began (simulated time). |
| `duration_seconds` | How long the behavior lasts. |
| `strength` | Ratio from -1 to 1 controlling how intensely the behavior modifies drift/volatility. |
| `created_at` | When this database row was inserted. |

### `quotes`

Bid/ask snapshots (mirrors `Quote`) — the current best price a buyer is
offering and a seller is asking.

| Column | Meaning |
| --- | --- |
| `id` | Primary key. |
| `session_id` | Which simulation run this quote belongs to. |
| `symbol` | Which stock this quote is for. |
| `timestamp` | When this quote was generated (simulated time). |
| `bid` | Highest price a buyer is currently willing to pay. |
| `ask` | Lowest price a seller is currently willing to accept. Always greater than `bid`. |
| `bid_size` | Number of shares available at the `bid` price. |
| `ask_size` | Number of shares available at the `ask` price. |

### `market_ticks`

The raw, continuous stream of simulated trades (mirrors `MarketTick`). This is
the highest-volume table.

| Column | Meaning |
| --- | --- |
| `id` | Primary key. |
| `session_id` | Which simulation run this tick belongs to. |
| `symbol` | Which stock traded. |
| `timestamp` | When the trade occurred (simulated time). |
| `price` | The actual trade price. Always between `bid` and `ask`. |
| `bid` / `ask` | The prevailing bid/ask at the moment of this trade. |
| `bid_size` / `ask_size` | Shares available at the bid/ask at the moment of this trade. |
| `trade_volume` | Number of shares traded in this single tick. |
| `sequence_number` | Increasing counter per `(session_id, symbol)` used to verify tick ordering. |

### `candles`

Ticks aggregated into OHLCV bars over a time bucket (mirrors `Candle`).
Computed *from* `market_ticks`, not generated independently.

| Column | Meaning |
| --- | --- |
| `id` | Primary key. |
| `session_id` | Which simulation run this candle belongs to. |
| `symbol` | Which stock this candle summarizes. |
| `interval` | Bucket size, e.g. `1s` or `1m`. |
| `timestamp` | Start time of the bucket (simulated time). |
| `open` | Price of the first trade in the bucket. |
| `high` | Highest trade price in the bucket. |
| `low` | Lowest trade price in the bucket. |
| `close` | Price of the last trade in the bucket. |
| `volume` | Total shares traded across all ticks in the bucket. |
| `trade_count` | Number of ticks aggregated into this candle. |
