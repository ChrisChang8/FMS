"""Tests for deterministic volume and liquidity generation."""

from datetime import datetime, timedelta

import pytest

from app.simulation import ActivitySimulationConfig, DEFAULT_SIMULATED_STOCKS, MarketActivityEngine, StockActivityConfig
from app.simulation.clock import MARKET_TIMEZONE


TIMESTAMP = datetime(2026, 8, 31, 9, 0, tzinfo=MARKET_TIMEZONE)
STOCK = DEFAULT_SIMULATED_STOCKS[0]


def test_same_seed_and_configuration_reproduce_activity() -> None:
    first = MarketActivityEngine(ActivitySimulationConfig(seed=42))
    second = MarketActivityEngine(ActivitySimulationConfig(seed=42))
    first_points = [first.step(STOCK, timestamp=TIMESTAMP, elapsed=timedelta(seconds=1)) for _ in range(20)]
    second_points = [second.step(STOCK, timestamp=TIMESTAMP, elapsed=timedelta(seconds=1)) for _ in range(20)]
    assert first_points == second_points


def test_different_seeds_generate_different_volume() -> None:
    first = MarketActivityEngine(ActivitySimulationConfig(seed=1))
    second = MarketActivityEngine(ActivitySimulationConfig(seed=2))
    first_volumes = [first.step(STOCK, timestamp=TIMESTAMP, elapsed=timedelta(seconds=1)).trade_volume for _ in range(10)]
    second_volumes = [second.step(STOCK, timestamp=TIMESTAMP, elapsed=timedelta(seconds=1)).trade_volume for _ in range(10)]
    assert first_volumes != second_volumes


def test_higher_liquidity_generates_more_volume_and_smoother_price_factor() -> None:
    low = MarketActivityEngine(ActivitySimulationConfig(seed=7))
    high = MarketActivityEngine(ActivitySimulationConfig(seed=7))
    low.configure_stock(STOCK.symbol, StockActivityConfig(liquidity=0.1))
    high.configure_stock(STOCK.symbol, StockActivityConfig(liquidity=0.9))
    low_points = [low.step(STOCK, timestamp=TIMESTAMP, elapsed=timedelta(minutes=1)) for _ in range(100)]
    high_points = [high.step(STOCK, timestamp=TIMESTAMP, elapsed=timedelta(minutes=1)) for _ in range(100)]
    assert sum(point.trade_volume for point in high_points) > sum(point.trade_volume for point in low_points)
    assert high_points[0].price_volatility_multiplier < low_points[0].price_volatility_multiplier


def test_volume_multiplier_controls_activity() -> None:
    baseline = MarketActivityEngine(ActivitySimulationConfig(seed=9))
    boosted = MarketActivityEngine(ActivitySimulationConfig(seed=9))
    boosted.configure_stock(STOCK.symbol, StockActivityConfig(volume_multiplier=2.0))
    baseline_total = sum(baseline.step(STOCK, timestamp=TIMESTAMP, elapsed=timedelta(minutes=1)).trade_volume for _ in range(50))
    boosted_total = sum(boosted.step(STOCK, timestamp=TIMESTAMP, elapsed=timedelta(minutes=1)).trade_volume for _ in range(50))
    assert boosted_total > baseline_total


def test_sequences_increment_per_symbol_and_reset_replays() -> None:
    engine = MarketActivityEngine(ActivitySimulationConfig(seed=11))
    first = engine.step(STOCK, timestamp=TIMESTAMP, elapsed=timedelta(seconds=1))
    second = engine.step(STOCK, timestamp=TIMESTAMP, elapsed=timedelta(seconds=1))
    engine.reset()
    replay = engine.step(STOCK, timestamp=TIMESTAMP, elapsed=timedelta(seconds=1))
    assert (first.sequence_number, second.sequence_number) == (1, 2)
    assert replay == first


@pytest.mark.parametrize("kwargs", [{"liquidity": -0.01}, {"liquidity": 1.01}, {"volume_multiplier": 0.0}])
def test_invalid_stock_activity_configuration_is_rejected(kwargs: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        StockActivityConfig(**kwargs)


def test_step_rejects_non_positive_elapsed_time() -> None:
    with pytest.raises(ValueError, match="elapsed"):
        MarketActivityEngine().step(STOCK, timestamp=TIMESTAMP, elapsed=timedelta(0))
