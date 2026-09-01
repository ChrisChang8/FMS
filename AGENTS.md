# Agent Notes

This repository contains the foundation for FMS, a local Python/FastAPI U.S. stock market data simulator. Future Codex agents should use this file as the starting point for orientation, then read the roadmap before making phase-specific changes.

## Repository Map

- `README.md` - Public-facing project overview, setup, run, and test instructions.
- `Docs/DATA_ROADMAP.md` - Phase-by-phase market data simulator roadmap and constraints.
- `Docs/Phases/` - Phase-specific implementation notes. Each completed phase should have one file named like `phase-N-short-title.md`.
- `migrations/` - Plain numbered PostgreSQL migration SQL files for the mock market data and behavior schema. See `migrations/README.md` for the naming convention and how to apply them.
- `AGENTS.md` - Agent-facing navigation and maintenance notes.
- `pyproject.toml` - Python project metadata, dependencies, and pytest configuration.
- `app/main.py` - FastAPI app factory and application instance.
- `app/api/` - API route modules. Phase 1 includes only the health endpoint.
- `app/core/` - Core application infrastructure such as typed settings and structured logging.
- `app/models/` - Core Pydantic market data models for stocks, quotes, ticks, candles, and market state.
- `app/simulation/` - Simulation clock, price, behavior, activity, quote, and tick engines.
- `app/simulation/activity.py` - Deterministic per-stock volume and liquidity generation.
- `app/simulation/quotes.py` - Deterministic bid, ask, and spread generation.
- `app/simulation/ticks.py` - Deterministic composition of complete raw market ticks.
- `app/services/` - Placeholder package for future service-layer code.
- `app/streaming/` - Placeholder package for future WebSocket and streaming code.
- `app/storage/` - Placeholder package for future storage and replay code.
- `tests/` - pytest suite covering the health endpoint, market data models, and simulation clock.

## How To Work Here

1. Start by reading `AGENTS.md`, then check `README.md` and anything added under `Docs/`.
2. Use `rg --files` to discover the current project structure before making assumptions.
3. Keep new documentation in `Docs/` unless a conventional root-level file is more appropriate.
4. When adding major source directories, tools, setup steps, or testing commands, update this file so future agents can find them quickly.
5. Preserve the repository's clean baseline: avoid unrelated generated files, broad refactors, or noisy metadata changes.

## Current Phase Status

Phase 1 is implemented:

- Python project configuration exists.
- FastAPI starts from `app.main:app`.
- `GET /health` returns the application health status.
- Typed settings use the `FMS_` environment variable prefix.
- Structured JSON-style logging is configured during app creation.
- pytest is configured and includes a health endpoint test.
- Detailed Phase 1 notes live in `Docs/Phases/phase-1-project-foundation.md`.

Phase 2 is implemented:

- `app.models.Stock` defines simulated stock reference data.
- `app.models.Quote` defines bid/ask snapshots and validates `bid < ask`.
- `app.models.MarketTick` defines raw market updates and validates internal price consistency.
- `app.models.Candle` defines OHLCV candles and validates high/low boundaries.
- `app.models.MarketState` defines current behavior inputs such as trend, volatility, liquidity, and momentum.
- Model tests cover important validation rules.
- Detailed Phase 2 notes live in `Docs/Phases/phase-2-market-data-models.md`.

Phase 3 is implemented:

- `app.simulation.SimulationClock` tracks simulated market time.
- `SimulationClockConfig` defines start time and simulation speed.
- Clock timestamps are normalized to `America/Chicago`.
- Regular market hours are treated as 8:30 AM to 3:00 PM Central Time.
- Pause, resume, reset, speed changes, and manual advancement are supported.
- Simulation clock tests cover deterministic progression and session boundaries.
- Detailed Phase 3 notes live in `Docs/Phases/phase-3-simulation-clock.md`.

Phase 4 is implemented:

- `app.simulation.PriceSimulationEngine` generates seeded deterministic stock price movement.
- `PriceSimulationConfig` defines seed, drift, and minimum positive price.
- `PricePoint` represents one generated trade-price observation without quote or volume data.
- The engine uses a geometric Brownian motion model based on previous price, drift, volatility, random market noise, and elapsed time.
- Prices are kept positive and rounded to six decimal places.
- Per-symbol sequence numbers are tracked for generated price points.
- `DEFAULT_SIMULATED_STOCKS` provides a local 10-stock simulation universe.
- Price engine tests cover deterministic replay, different seed behavior, positive prices, reset behavior, and 10-stock support.
- Detailed Phase 4 notes live in `Docs/Phases/phase-4-price-simulation-engine.md`.

Phase 5 is implemented:

- `app.simulation.behaviors` provides 10 controllable market behaviors.
- `MarketBehavior` abstract base class and 10 concrete subclasses (Normal, Uptrend, Downtrend, Sideways, Momentum, Mean Reversion, Breakout, Breakdown, Consolidation, Volatility Spike).
- `BehaviorType` enum defines the 10 behavior types.
- `MarketBehaviorConfig` Pydantic model for configuration with duration and strength validation.
- `MarketBehaviorEngine` tracks and applies behaviors to multiple stocks simultaneously.
- `create_behavior()` factory function instantiates behaviors from configuration.
- Behaviors adjust drift and volatility independently without modifying the price engine.
- Full behavior test coverage (37 tests) integrated with existing 29 tests (66 total passing).
- Detailed Phase 5 notes live in `Docs/Phases/phase-5-market-behavior-engine.md`.

Phase 6 is implemented:

- `MarketActivityEngine` generates deterministic interval share volume.
- `StockActivityConfig` provides per-symbol liquidity and volume controls.
- Volume is based on each stock's average daily volume, elapsed time, liquidity, and a configurable multiplier.
- Higher liquidity produces more volume and a lower price-volatility multiplier for smoother pricing.
- Activity points have per-symbol sequence numbers and reset reproducibly from the configured seed.
- Phase 6 does not generate bid, ask, or spread data.
- Detailed Phase 6 notes live in `Docs/Phases/phase-6-volume-and-liquidity.md`.

Phase 7 is implemented:

- `QuoteSimulationEngine` generates deterministic top-of-book bid and ask prices around a reference price.
- `QuoteSimulationConfig` controls the seed, baseline spread, minimum tick, volatility sensitivity, and spread variation.
- Higher liquidity narrows spreads, while higher volatility widens them.
- Quote prices align to the configured tick size and always preserve a positive spread.
- `QuotePoint` intentionally excludes quote sizes, tick assembly, and order-book depth.
- Detailed Phase 7 notes live in `Docs/Phases/phase-7-bid-ask-and-spread.md`.

Phase 8 is implemented:

- `TickSimulationEngine` composes behavior, price, activity, quote, and quote-size generation into validated `MarketTick` records.
- Active behaviors adjust drift and volatility; liquidity then scales volatility before price and quote generation.
- The default 10-stock universe can be generated as one ordered stream.
- Timestamps remain nondecreasing and one global sequence number orders ticks across symbols.
- Trade prices remain within the generated bid and ask, and all sizes and trade volumes are positive.
- A master seed and full reset reproduce the complete tick stream.
- Detailed Phase 8 notes live in `Docs/Phases/phase-8-tick-generation.md`.

A PostgreSQL schema for simulation sessions, stocks, market states, behaviors, quotes, ticks, and candles has been added under `migrations/` ahead of Phase 12, at the user's explicit request. The application does not yet connect to this schema (no `app/storage` wiring); it is schema scaffolding only.

Do not begin Phase 9 unless the user explicitly asks for Phase 9.

## Common Commands

Install development dependencies:

```powershell
python -m pip install -e ".[dev]"
```

Run the app:

```powershell
python -m uvicorn app.main:app --reload
```

Run tests:

```powershell
python -m pytest
```

## Documentation Hygiene

As this repository grows, consider adding:

- `Docs/architecture.md` for system structure and major decisions.
- `Docs/setup.md` for local development instructions.
- `Docs/testing.md` for verification commands and expected test coverage.
- `Docs/decisions/` for notable design or implementation decisions.

## Development Rules for the Agent

Work on one phase at a time.

Do not implement future phases early.

When asked to start a phase:

1. Read Docs/DATA_ROADMAP.md first.
2. Review the existing repository before making changes.
3. Implement only the requested phase.
4. Keep the architecture compatible with future phases.
5. Prefer readable, typed, modular Python code.
6. Write deterministic tests wherever possible.
7. Keep mathematical logic separate from API and streaming logic.
8. Avoid unnecessary infrastructure and over-engineering.
9. Explain unfamiliar financial or mathematical concepts simply.
10. Stop after completing the requested phase.

At the end of each phase:

- Summarize what was created
- List files created or changed
- Explain how to run and test the phase
- Explain important technical concepts simply
- Document important assumptions or design decisions
- Create or update a phase-specific note in `Docs/Phases/` named like `phase-N-short-title.md`
- Link the phase-specific note from `README.md` and `AGENTS.md` when it is relevant to the current project status
- Do not automatically begin the next phase

## Core Principle

The goal is not to create random stock prices.

The goal is to create a small, realistic, deterministic market-data simulator whose output resembles a simplified live U.S. market-data feed and can later be consumed by other systems.
