# Mock market data seed

Generates a deterministic, self-contained set of mock market data for the FMS
simulator and writes it out as a portable `.sql` file. This is **market data
only** — no users, accounts, orders, fills, or instruments are seeded.

## What it produces

Running [`../notebooks/seed_data_generation.ipynb`](../notebooks/seed_data_generation.ipynb)
reuses the existing simulation engines (`TickSimulationEngine`,
`CandleAggregator`, `MarketBehaviorEngine`) with a fixed seed to generate:

- 1 `simulation_sessions` row (seed `42`, drift `0.08`, status `COMPLETED`)
- 5 `stocks` rows across varied sectors
- 5 `market_states` rows (one snapshot per stock)
- 2 `market_behaviors` rows (an uptrend and a volatility spike, actually
  applied during generation so downstream data reflects them)
- ~1500 `quotes` rows and ~1500 `market_ticks` rows (5 stocks x 300 one-second
  steps), derived so bid/ask/price and sequencing constraints hold
- `candles` rows for the `1s` and `1m` intervals

The notebook writes the result to
[`../migrations/seed_mock_market_data.sql`](../migrations/seed_mock_market_data.sql)
as plain `INSERT` statements wrapped in a transaction, matching the tables
defined in `migrations/0001`-`0009` and mirrored in
`Platform/Trading Platform Schema.sql`.

## Applying the seed file

Run the numbered schema migrations first, then apply the seed file the same
way (see `migrations/README.md`):

```powershell
psql $env:DATABASE_URL -v ON_ERROR_STOP=1 -f "migrations/seed_mock_market_data.sql"
```

## Regenerating

Re-run all cells in `notebooks/seed_data_generation.ipynb` top to bottom. The
generation is fully deterministic (fixed seed and start time), so re-running
without code changes produces byte-identical output.
