# Phase 5: Market Behavior Engine

## Overview

Phase 5 implements a controllable market behavior system that allows simulated stocks to exhibit different price movement patterns. This modular design enables independent behaviors to adjust drift and volatility, creating realistic market scenarios without modifying the core price simulation engine.

## What Was Implemented

### 1. Market Behavior Abstractions

**File:** `app/simulation/behaviors.py`

#### Core Classes:

- **`BehaviorType`**: An enum defining 10 behavior types:
  - `NORMAL` - No special behavior
  - `UPTREND` - Positive drift, increased volatility
  - `DOWNTREND` - Negative drift, increased volatility
  - `SIDEWAYS` - Reduced drift and volatility
  - `MOMENTUM` - Amplified drift in current direction, high volatility
  - `MEAN_REVERSION` - Dampened drift and volatility
  - `BREAKOUT` - Strong positive drift, very high volatility
  - `BREAKDOWN` - Strong negative drift, very high volatility
  - `CONSOLIDATION` - Minimal drift, minimal volatility
  - `VOLATILITY_SPIKE` - Normal drift, greatly increased volatility

- **`MarketBehavior`**: Abstract base class for all behaviors
  - Manages start time, duration, and strength
  - Provides `is_active()` to check if behavior is active at a given time
  - Provides `get_progress()` to track completion (0.0 to 1.0)
  - Abstract `apply()` method that subclasses override to modify drift/volatility

- **Concrete Behavior Classes**: 10 subclasses, each implementing `apply()` with different drift/volatility adjustments
  - `NormalBehavior`
  - `UptrendBehavior`
  - `DowntrendBehavior`
  - `SidewaysBehavior`
  - `MomentumBehavior`
  - `MeanReversionBehavior`
  - `BreakoutBehavior`
  - `BreakdownBehavior`
  - `ConsolidationBehavior`
  - `VolatilitySpikeBehavior`

#### Configuration:

- **`MarketBehaviorConfig`**: A Pydantic model for behavior configuration
  - `symbol`: Stock ticker symbol (uppercase pattern enforced)
  - `behavior_type`: Which behavior to apply
  - `duration`: How long the behavior lasts (validated to be positive)
  - `strength`: A ratio from -1.0 to 1.0 controlling intensity

### 2. Behavior Management Engine

- **`MarketBehaviorEngine`**: Tracks and applies behaviors to multiple stocks
  - `add_behavior()`: Add a behavior directly
  - `add_behavior_from_config()`: Create and add behavior from configuration
  - `remove_behavior()`: Remove a specific behavior
  - `cleanup_expired()`: Remove all expired behaviors
  - `get_active_behaviors()`: List behaviors active at current time
  - `get_adjustment()`: Calculate final adjusted drift/volatility for a stock
  - `reset()`: Clear all behaviors

### 3. Factory Function

- **`create_behavior()`**: Factory function to instantiate the correct behavior subclass from a `MarketBehaviorConfig`

## How Behaviors Work

Each behavior modifies two parameters:

1. **Drift**: The long-term directional tendency of prices
2. **Volatility**: The magnitude of price changes

For example:
- **Uptrend**: Increases drift by up to 20%, increases volatility by up to 15%
- **Consolidation**: Reduces drift by up to 95%, reduces volatility by up to 70%
- **Volatility Spike**: Keeps drift unchanged, increases volatility by up to 150%

The strength parameter (0.0 to 1.0, or -1.0 to 0.0) controls how aggressively each behavior affects prices.

## Integration with Phase 4

The behavior engine is **independent** of the `PriceSimulationEngine`. To use behaviors:

1. Create a `MarketBehaviorEngine`
2. Add behaviors using `add_behavior()` or `add_behavior_from_config()`
3. Before calling `PriceSimulationEngine.step()`, get adjusted parameters:
   ```python
   adjusted_drift, adjusted_volatility = behavior_engine.get_adjustment(
       symbol="AAPL",
       base_drift=0.08,
       base_volatility=stock.base_volatility,
       current_time=current_time
   )
   ```
4. Pass adjusted drift to `step()`: `engine.step(..., drift=adjusted_drift)`

This separation maintains modularity—the price engine doesn't need to know about behaviors.

## Determinism

All behaviors are deterministic:
- Same configuration + same stock + same time = same adjustment
- Behaviors respect the random seed from Phase 4
- The price engine's RNG remains unchanged

## Testing

**File:** `tests/test_market_behaviors.py`

Comprehensive test coverage (37 tests) includes:

- Individual behavior adjustments
- Behavior lifecycle (is_active, get_progress)
- Engine operations (add, remove, cleanup)
- Multiple behaviors on same stock
- Configuration validation
- Factory function
- Integration scenarios with multiple stocks

All 37 behavior tests + all 29 existing tests = **66 tests passing**.

## Key Design Decisions

1. **Separate from Price Engine**: Behaviors don't require changes to Phase 4. The price engine accepts an optional `drift` parameter, and behaviors calculate it externally.

2. **Modular Architecture**: New behaviors can be added by subclassing `MarketBehavior` without modifying the engine or existing behaviors.

3. **Configuration-Based**: `MarketBehaviorConfig` allows easy serialization and configuration from external sources (files, APIs, etc.).

4. **Progress Tracking**: `get_progress()` enables time-based visualization or analytics of behavior application.

5. **Multiple Behaviors**: Multiple behaviors can apply to the same stock simultaneously. They compose sequentially—each adjusts the result of the previous one.

6. **Automatic Expiration**: Behaviors automatically expire when their duration ends. `cleanup_expired()` removes them from memory.

## Mathematical Model

Each behavior applies a multiplier and/or adjustment to base values:

- Drift adjustments: `new_drift = base_drift + adjustment` or `new_drift = base_drift * multiplier`
- Volatility adjustments: `new_volatility = base_volatility * multiplier` (always multiplication)

Strength values between -1.0 and 1.0 scale these effects. The engine clamps out-of-range strengths automatically.

## Example Usage

```python
from datetime import datetime, timedelta
import pytz
from app.simulation import (
    MarketBehaviorConfig,
    MarketBehaviorEngine,
    BehaviorType,
)

chicago_tz = pytz.timezone("America/Chicago")
now = chicago_tz.localize(datetime(2026, 8, 29, 14, 30, 0))

# Create an engine
engine = MarketBehaviorEngine()

# Configure AAPL uptrend for 2 hours with 70% strength
uptrend_config = MarketBehaviorConfig(
    symbol="AAPL",
    behavior_type=BehaviorType.UPTREND,
    duration=timedelta(hours=2),
    strength=0.7,
)

# Apply the behavior
engine.add_behavior_from_config(uptrend_config, now)

# Later, get the adjustment
adjusted_drift, adjusted_volatility = engine.get_adjustment(
    symbol="AAPL",
    base_drift=0.08,
    base_volatility=0.22,
    current_time=now,
)

# Use adjusted values in price engine
price_point = price_engine.step(
    stock=aapl_stock,
    timestamp=now,
    elapsed=timedelta(seconds=1),
    drift=adjusted_drift,  # Pass the adjusted drift
)
```

## Files Created/Modified

### Created:
- `app/simulation/behaviors.py` - Market behavior engine implementation
- `tests/test_market_behaviors.py` - Comprehensive behavior tests

### Modified:
- `app/simulation/__init__.py` - Added behavior class exports

## Compatibility with Future Phases

Phase 5 maintains clean separation:
- Phase 6 (Volume and Liquidity) can independently adjust volume without affecting behaviors
- Phase 7 (Bid, Ask, Spread) can use behavior volatility to inform quote spread
- Phase 8+ (Streaming, storage) interact with behaviors only through the engine interface
- No existing Phase 1-4 code was modified

## Next Steps (Not Implemented)

Phase 6 will add:
- Volume generation
- Liquidity modeling
- Integration of liquidity with behavior effects

This can be done independently—behaviors are ready to be used immediately.

---

## Run Tests

```powershell
python -m pytest tests/test_market_behaviors.py -v
```

Or run all tests:

```powershell
python -m pytest
```

All 66 tests pass.
