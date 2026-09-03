from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.simulation import (
    DEFAULT_SIMULATED_STOCKS,
    MARKET_TIMEZONE,
    PriceSimulationConfig,
    PriceSimulationEngine,
)


START_TIME = datetime(2026, 8, 31, 8, 30, tzinfo=MARKET_TIMEZONE)


def test_same_seed_and_configuration_generate_same_prices() -> None:
    stock = DEFAULT_SIMULATED_STOCKS[0]
    config = PriceSimulationConfig(seed=42, drift=0.06)

    first_engine = PriceSimulationEngine(config)
    second_engine = PriceSimulationEngine(config)

    first_prices = first_engine.simulate(
        [stock],
        start_time=START_TIME,
        steps=5,
        step_size=timedelta(seconds=1),
    )
    second_prices = second_engine.simulate(
        [stock],
        start_time=START_TIME,
        steps=5,
        step_size=timedelta(seconds=1),
    )

    assert first_prices == second_prices


def test_different_seeds_can_generate_different_prices() -> None:
    stock = DEFAULT_SIMULATED_STOCKS[0]

    first_engine = PriceSimulationEngine(PriceSimulationConfig(seed=1))
    second_engine = PriceSimulationEngine(PriceSimulationConfig(seed=2))

    first_prices = first_engine.simulate(
        [stock],
        start_time=START_TIME,
        steps=5,
        step_size=timedelta(seconds=1),
    )
    second_prices = second_engine.simulate(
        [stock],
        start_time=START_TIME,
        steps=5,
        step_size=timedelta(seconds=1),
    )

    assert [point.price for point in first_prices] != [point.price for point in second_prices]


def test_prices_remain_positive_even_with_large_negative_noise() -> None:
    volatile_stock = DEFAULT_SIMULATED_STOCKS[6].model_copy(
        update={
            "starting_price": Decimal("0.01"),
            "base_volatility": Decimal("10"),
        }
    )
    engine = PriceSimulationEngine(PriceSimulationConfig(seed=15, minimum_price=Decimal("0.000001")))

    prices = engine.simulate(
        [volatile_stock],
        start_time=START_TIME,
        steps=100,
        step_size=timedelta(seconds=60),
    )

    assert all(point.price > Decimal("0") for point in prices)


def test_engine_supports_default_universe_of_ten_stocks() -> None:
    engine = PriceSimulationEngine(PriceSimulationConfig(seed=7))

    prices = engine.simulate(
        DEFAULT_SIMULATED_STOCKS,
        start_time=START_TIME,
        steps=2,
        step_size=timedelta(seconds=1),
    )

    assert len(DEFAULT_SIMULATED_STOCKS) == 10
    assert len(prices) == 20
    assert {point.symbol for point in prices} == {stock.symbol for stock in DEFAULT_SIMULATED_STOCKS}
    assert all(point.sequence_number in {1, 2} for point in prices)


def test_reset_replays_the_same_seeded_path() -> None:
    stock = DEFAULT_SIMULATED_STOCKS[1]
    engine = PriceSimulationEngine(PriceSimulationConfig(seed=99))

    first_prices = engine.simulate(
        [stock],
        start_time=START_TIME,
        steps=3,
        step_size=timedelta(seconds=1),
    )
    engine.reset()
    second_prices = engine.simulate(
        [stock],
        start_time=START_TIME,
        steps=3,
        step_size=timedelta(seconds=1),
    )

    assert first_prices == second_prices


def test_step_requires_positive_elapsed_time() -> None:
    engine = PriceSimulationEngine()

    with pytest.raises(ValueError, match="elapsed must be greater than zero"):
        engine.step(
            DEFAULT_SIMULATED_STOCKS[0],
            timestamp=START_TIME,
            elapsed=timedelta(seconds=0),
        )


def test_config_requires_minimum_price_that_preserves_money_precision() -> None:
    with pytest.raises(ValueError, match="minimum_price must be at least 0.000001"):
        PriceSimulationConfig(minimum_price=Decimal("0.0000001"))
