"""Tests for continuous deterministic market tick generation."""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.simulation import (
    DEFAULT_SIMULATED_STOCKS,
    BehaviorType,
    MARKET_TIMEZONE,
    MarketBehaviorConfig,
    StockActivityConfig,
    TickSimulationConfig,
    TickSimulationEngine,
)


START_TIME = datetime(2026, 8, 31, 8, 30, tzinfo=MARKET_TIMEZONE)


def simulate(engine: TickSimulationEngine, *, steps: int = 3) -> list:
    return engine.simulate(
        DEFAULT_SIMULATED_STOCKS,
        start_time=START_TIME,
        steps=steps,
        step_size=timedelta(milliseconds=250),
    )


def test_same_seed_reproduces_the_complete_tick_stream() -> None:
    first = simulate(TickSimulationEngine(TickSimulationConfig(seed=42)))
    second = simulate(TickSimulationEngine(TickSimulationConfig(seed=42)))
    assert first == second


def test_different_seeds_change_the_tick_stream() -> None:
    first = simulate(TickSimulationEngine(TickSimulationConfig(seed=1)))
    second = simulate(TickSimulationEngine(TickSimulationConfig(seed=2)))
    assert first != second


def test_all_ten_stocks_have_ordered_timestamps_and_global_sequences() -> None:
    ticks = simulate(TickSimulationEngine(), steps=4)
    assert len(ticks) == 40
    assert {tick.symbol for tick in ticks} == {stock.symbol for stock in DEFAULT_SIMULATED_STOCKS}
    assert [tick.timestamp for tick in ticks] == sorted(tick.timestamp for tick in ticks)
    assert [tick.sequence_number for tick in ticks] == list(range(1, 41))


def test_tick_values_are_internally_consistent_and_positive() -> None:
    ticks = simulate(TickSimulationEngine(), steps=10)
    assert all(tick.bid < tick.ask for tick in ticks)
    assert all(tick.bid <= tick.price <= tick.ask for tick in ticks)
    assert all(tick.bid_size > 0 and tick.ask_size > 0 for tick in ticks)
    assert all(tick.trade_volume > 0 for tick in ticks)


def test_sub_cent_stock_still_produces_an_internally_consistent_tick() -> None:
    stock = DEFAULT_SIMULATED_STOCKS[0].model_copy(
        update={"starting_price": Decimal("0.000001"), "base_volatility": Decimal("0")}
    )
    tick = TickSimulationEngine().step(
        stock,
        timestamp=START_TIME,
        elapsed=timedelta(milliseconds=1),
    )
    assert tick.bid <= tick.price <= tick.ask


def test_reset_replays_the_same_stream() -> None:
    engine = TickSimulationEngine(TickSimulationConfig(seed=17))
    first = simulate(engine)
    engine.reset()
    assert simulate(engine) == first


def test_behavior_adjusts_the_price_generated_for_a_tick() -> None:
    stock = DEFAULT_SIMULATED_STOCKS[0].model_copy(update={"base_volatility": Decimal("0")})
    normal = TickSimulationEngine(TickSimulationConfig(seed=12))
    trending = TickSimulationEngine(TickSimulationConfig(seed=12))
    trending.add_behavior_from_config(
        MarketBehaviorConfig(
            symbol=stock.symbol,
            behavior_type=BehaviorType.UPTREND,
            duration=timedelta(hours=1),
            strength=1.0,
        ),
        current_time=START_TIME,
    )

    normal_tick = normal.step(stock, timestamp=START_TIME, elapsed=timedelta(minutes=10))
    trending_tick = trending.step(stock, timestamp=START_TIME, elapsed=timedelta(minutes=10))

    assert trending_tick.price > normal_tick.price


def test_behavior_volatility_flows_into_quote_generation() -> None:
    stock = DEFAULT_SIMULATED_STOCKS[2]
    normal = TickSimulationEngine(TickSimulationConfig(seed=21))
    volatile = TickSimulationEngine(TickSimulationConfig(seed=21))
    volatile.add_behavior_from_config(
        MarketBehaviorConfig(
            symbol=stock.symbol,
            behavior_type=BehaviorType.VOLATILITY_SPIKE,
            duration=timedelta(hours=1),
            strength=1.0,
        ),
        current_time=START_TIME,
    )

    normal_ticks = [
        normal.step(
            stock,
            timestamp=START_TIME + timedelta(seconds=step),
            elapsed=timedelta(seconds=1),
        )
        for step in range(20)
    ]
    volatile_ticks = [
        volatile.step(
            stock,
            timestamp=START_TIME + timedelta(seconds=step),
            elapsed=timedelta(seconds=1),
        )
        for step in range(20)
    ]

    assert sum(tick.ask - tick.bid for tick in volatile_ticks) > sum(
        tick.ask - tick.bid for tick in normal_ticks
    )


def test_expired_behavior_no_longer_changes_tick_price() -> None:
    stock = DEFAULT_SIMULATED_STOCKS[0].model_copy(update={"base_volatility": Decimal("0")})
    normal = TickSimulationEngine(TickSimulationConfig(seed=31))
    expired = TickSimulationEngine(TickSimulationConfig(seed=31))
    expired.add_behavior_from_config(
        MarketBehaviorConfig(
            symbol=stock.symbol,
            behavior_type=BehaviorType.UPTREND,
            duration=timedelta(seconds=1),
            strength=1.0,
        ),
        current_time=START_TIME,
    )
    timestamp = START_TIME + timedelta(seconds=2)

    normal_tick = normal.step(stock, timestamp=timestamp, elapsed=timedelta(seconds=1))
    expired_tick = expired.step(stock, timestamp=timestamp, elapsed=timedelta(seconds=1))

    assert expired_tick == normal_tick


def test_stock_liquidity_configuration_affects_quote_sizes() -> None:
    low = TickSimulationEngine(TickSimulationConfig(seed=9))
    high = TickSimulationEngine(TickSimulationConfig(seed=9))
    for stock in DEFAULT_SIMULATED_STOCKS:
        low.configure_stock(stock.symbol, StockActivityConfig(liquidity=0.1))
        high.configure_stock(stock.symbol, StockActivityConfig(liquidity=0.9))
    low_ticks = simulate(low, steps=20)
    high_ticks = simulate(high, steps=20)
    assert sum(tick.bid_size + tick.ask_size for tick in high_ticks) > sum(
        tick.bid_size + tick.ask_size for tick in low_ticks
    )


def test_step_rejects_a_timestamp_that_moves_backwards() -> None:
    engine = TickSimulationEngine()
    stock = DEFAULT_SIMULATED_STOCKS[0]
    engine.step(stock, timestamp=START_TIME, elapsed=timedelta(seconds=1))
    with pytest.raises(ValueError, match="timestamp must not move backwards"):
        engine.step(stock, timestamp=START_TIME - timedelta(seconds=1), elapsed=timedelta(seconds=1))


@pytest.mark.parametrize("kwargs", [{"seed": -1}, {"average_quote_size": 0}])
def test_invalid_configuration_is_rejected(kwargs: dict[str, int]) -> None:
    with pytest.raises(ValueError):
        TickSimulationConfig(**kwargs)
