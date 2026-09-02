# Market Data Simulator Roadmap

## Project Goal

Build a technically strong local U.S. stock market data simulator.

This project is only responsible for generating realistic simulated market data.

Do not build:

- Frontend interfaces, except the explicitly requested local Phase 11 simulator-control dashboard
- Paper trading
- Order placement
- Portfolios
- User accounts
- Authentication
- Brokerage functionality
- Real-money trading

The simulator should eventually behave like a simplified live market-data feed that another application could consume.

Initial scope:

- Simulate approximately 10 U.S. stocks
- Generate realistic real-time market updates
- Support deterministic simulations using seeds
- Generate price, bid, ask, spread, volume, volatility, and timestamps
- Generate raw tick data
- Aggregate ticks into OHLCV candles
- Support controllable market behaviors
- Expose generated data through APIs and real-time streaming

## Technology

Primary stack:

- Python
- FastAPI
- NumPy
- Pydantic
- asyncio
- Polars or Pandas when appropriate
- WebSockets
- pytest

Potential later technologies:

- PostgreSQL for historical storage
- Redis only if performance testing proves it is useful

Do not introduce unnecessary infrastructure.

---

## Phase 1 — Project Foundation

Create the basic project structure.

Tasks:

- Create the Python project structure
- Configure dependencies
- Add FastAPI
- Add configuration management
- Add structured logging
- Add pytest
- Add a basic health endpoint
- Add README documentation

Suggested structure:

```text
app/
    api/
    core/
    models/
    simulation/
    services/
    streaming/
    storage/

tests/
```

Do not implement market simulation yet.

Success criteria:

- Application starts successfully
- Health endpoint works
- Tests run successfully
- Project structure is easy to understand

---

## Phase 2 — Market Data Models

Define the core objects used throughout the simulator.

Create models such as:

### Stock

Represents one simulated stock.

Possible fields:

- symbol
- company_name
- starting_price
- sector
- average_volume
- base_volatility

### MarketTick

Represents one raw market update.

Possible fields:

- symbol
- timestamp
- price
- bid
- ask
- bid_size
- ask_size
- trade_volume
- sequence_number

### Quote

Represents the current bid and ask information.

### Candle

Represents OHLCV market data.

Possible fields:

- symbol
- interval
- timestamp
- open
- high
- low
- close
- volume
- trade_count

### MarketState

Represents the current behavior of the simulated stock.

Possible fields:

- trend
- volatility
- liquidity
- momentum

Success criteria:

- Models are strongly typed
- Validation works correctly
- Unit tests cover important model rules

---

## Phase 3 — Simulation Clock

Create a clock for the simulated market.

The simulator should not depend directly on the computer clock.

Support:

* Current simulated time
* Start time
* Pause
* Resume
* Reset
* Simulation speed
* Deterministic progression

Use U.S. Central Time (`America/Chicago`) for all simulated market timestamps.

Initially support regular U.S. stock market hours converted to Chicago time:

* 8:30 AM to 3:00 PM Central Time

The simulator should treat these hours as the active regular trading session.

Success criteria:

* Tests can advance time predictably
* Pause and resume behave correctly
* Reset returns the simulation to the configured start time
* Same configuration produces the same timeline
* All timestamps use the `America/Chicago` timezone consistently

---

## Phase 4 — Price Simulation Engine

Generate realistic-looking stock price movement.

Do not use simple movement such as:

```python
price += random_number
```

Use a mathematical model that considers:

- Previous price
- Drift
- Volatility
- Random market noise
- Time progression

A basic geometric Brownian motion model is acceptable for the first version.

Use a configurable random seed.

Requirements:

- Same seed + same configuration = same simulation
- Different seeds can generate different simulations
- Prices must never become invalid or negative

Start with one stock and then expand to all 10.

---

## Phase 5 — Market Behavior Engine

Add controllable market behaviors.

Support behaviors such as:

- Normal
- Uptrend
- Downtrend
- Sideways
- Momentum
- Mean reversion
- Breakout
- Breakdown
- Consolidation
- Volatility spike

Use a modular design so behaviors can be added without rewriting the simulation engine.

Example concept:

```text
MarketBehavior
    UptrendBehavior
    DowntrendBehavior
    MeanReversionBehavior
    BreakoutBehavior
```

Possible configuration:

```text
symbol = AAPL
behavior = UPTREND
duration = 30 minutes
strength = 0.7
```

The simulation must remain deterministic.

---

## Phase 6 — Volume and Liquidity

Generate realistic market activity levels.

### Volume

Represents how many shares are being simulated as traded.

### Liquidity

Represents how active the simulated stock is.

Higher liquidity should generally result in:

- Higher volume
- Smaller spreads
- Smoother pricing

Lower liquidity should generally result in:

- Lower volume
- Larger spreads
- More irregular movement

Make these values configurable per stock.

---

## Phase 7 — Bid, Ask, and Spread

Generate realistic quote data.

### Bid

Highest simulated price a buyer is willing to pay.

### Ask

Lowest simulated price a seller is willing to accept.

### Spread

```text
ask - bid
```

Rules:

- Bid must always be lower than ask
- Spread must never be negative
- High liquidity should generally create smaller spreads
- High volatility may create larger spreads

Do not build a full order book in this phase.

---

## Phase 8 — Tick Generation

Create the continuous raw market-data stream.

Example tick:

```json
{
  "symbol": "AAPL",
  "price": 224.15,
  "bid": 224.14,
  "ask": 224.16,
  "bid_size": 500,
  "ask_size": 300,
  "trade_volume": 100,
  "timestamp": "2026-08-29T14:31:01.250Z",
  "sequence_number": 1001
}
```

Requirements:

- Support all 10 stocks
- Timestamps remain ordered
- Sequence numbers increase correctly
- Values remain internally consistent
- Same seed reproduces the same tick stream

---

## Phase 9 — Candle Aggregation

Convert raw ticks into OHLCV candles.

Start with:

- 1-second candles
- 1-minute candles

Design the system so additional intervals can be added later.

Each candle contains:

- Open
- High
- Low
- Close
- Volume
- Trade count

Candles must be calculated from generated tick data.

Do not generate candles independently.

Success criteria:

- Open is the first trade price
- High is the highest trade price
- Low is the lowest trade price
- Close is the final trade price
- Volume is aggregated correctly

---

## Phase 10 — Market Data API

Expose generated market data using FastAPI.

Possible endpoints:

```text
GET /stocks
GET /quotes/{symbol}
GET /ticks/{symbol}
GET /candles/{symbol}

GET /simulation/status
POST /simulation/start
POST /simulation/pause
POST /simulation/reset
```

Do not add trading endpoints.

Keep API logic separate from simulation logic.

---

## Phase 11 — Real-Time Streaming

Expose generated market data through WebSockets.

Example:

```text
ws://localhost:8000/ws/market
```

Stream information such as:

- Ticks
- Quotes
- Market timestamps

The streaming layer should be separate from the simulation engine.

The simulator should not care what future application consumes its output.

---

## Phase 12 — Historical Storage and Replay

Add persistence only after the simulator works correctly.

Consider PostgreSQL for storing:

- Simulation sessions
- Seed
- Configuration
- Ticks
- Candles
- Start time
- End time

Allow previous simulations to be replayed.

Before storing every tick, evaluate the performance and storage tradeoffs.

---

## Phase 13 — Testing and Validation

Create tests for market-data correctness.

Validate:

- Prices remain valid
- Bid is always below ask
- Spread is never negative
- Timestamps remain ordered
- Sequence numbers remain ordered
- Candle OHLC values are correct
- Volume aggregation is correct
- Same seed produces the same output
- Different seeds produce different output
- Market behaviors produce expected characteristics

---

## Phase 14 — Performance Testing

Measure simulator performance.

Track:

- Updates per second
- CPU usage
- Memory usage
- Tick-generation latency
- WebSocket throughput
- Dropped events

Test all 10 simulated stocks simultaneously.

Do not optimize before measuring.

Do not introduce Redis unless measurements show a clear reason.

---

## Phase 15 — Advanced Market Realism

Only begin after the core simulator works.

Possible improvements:

- Realistic market-open volatility
- Intraday volume patterns
- End-of-day behavior
- Correlated stocks
- Sector relationships
- Market-wide movement
- SPY influence
- Pre-market
- After-hours
- U.S. market holidays
- Trading halts
- Level 2 market depth
- More advanced mathematical price models

These are future improvements, not V1 requirements.

---

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
- Do not automatically begin the next phase

## Core Principle

The goal is not to create random stock prices.

The goal is to create a small, realistic, deterministic market-data simulator whose output resembles a simplified live U.S. market-data feed and can later be consumed by other systems.
