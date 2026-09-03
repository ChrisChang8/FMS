"""Tests for deterministic top-of-book quote generation."""

from datetime import datetime
from decimal import Decimal

import pytest

from app.simulation import QuoteSimulationConfig, QuoteSimulationEngine
from app.simulation.clock import MARKET_TIMEZONE


TIMESTAMP = datetime(2026, 8, 31, 9, 0, tzinfo=MARKET_TIMEZONE)


def generate_series(engine: QuoteSimulationEngine, *, liquidity: float, volatility: Decimal) -> list:
    return [
        engine.step(
            "aapl",
            timestamp=TIMESTAMP,
            reference_price=Decimal("224.15"),
            liquidity=liquidity,
            volatility=volatility,
        )
        for _ in range(20)
    ]


def test_same_seed_and_inputs_reproduce_quotes() -> None:
    assert generate_series(QuoteSimulationEngine(QuoteSimulationConfig(seed=42)), liquidity=0.5, volatility=Decimal("0.2")) == generate_series(
        QuoteSimulationEngine(QuoteSimulationConfig(seed=42)), liquidity=0.5, volatility=Decimal("0.2")
    )


def test_reset_replays_quote_sequence() -> None:
    engine = QuoteSimulationEngine(QuoteSimulationConfig(seed=7))
    first = generate_series(engine, liquidity=0.5, volatility=Decimal("0.2"))
    engine.reset()
    assert generate_series(engine, liquidity=0.5, volatility=Decimal("0.2")) == first


def test_bid_is_always_below_ask_and_spread_is_positive() -> None:
    quotes = generate_series(QuoteSimulationEngine(), liquidity=0.0, volatility=Decimal("1.5"))
    assert all(quote.bid < quote.ask and quote.spread > 0 for quote in quotes)
    assert all(quote.symbol == "AAPL" for quote in quotes)


def test_high_liquidity_generates_smaller_spreads() -> None:
    low = generate_series(QuoteSimulationEngine(QuoteSimulationConfig(seed=3)), liquidity=0.1, volatility=Decimal("0.3"))
    high = generate_series(QuoteSimulationEngine(QuoteSimulationConfig(seed=3)), liquidity=0.9, volatility=Decimal("0.3"))
    assert sum(quote.spread for quote in high) < sum(quote.spread for quote in low)


def test_high_volatility_generates_larger_spreads() -> None:
    calm = generate_series(QuoteSimulationEngine(QuoteSimulationConfig(seed=5)), liquidity=0.5, volatility=Decimal("0.1"))
    volatile = generate_series(QuoteSimulationEngine(QuoteSimulationConfig(seed=5)), liquidity=0.5, volatility=Decimal("0.8"))
    assert sum(quote.spread for quote in volatile) > sum(quote.spread for quote in calm)


def test_quotes_respect_configured_tick_size() -> None:
    quote = QuoteSimulationEngine(QuoteSimulationConfig(minimum_tick=Decimal("0.05"))).step(
        "AAPL", timestamp=TIMESTAMP, reference_price=Decimal("224.13"), liquidity=0.5, volatility=Decimal("0.2")
    )
    assert quote.bid % Decimal("0.05") == 0
    assert quote.ask % Decimal("0.05") == 0


@pytest.mark.parametrize(
    ("field", "value"),
    [("reference_price", Decimal("0")), ("liquidity", -0.1), ("liquidity", 1.1), ("volatility", Decimal("-0.1"))],
)
def test_invalid_market_inputs_are_rejected(field: str, value: object) -> None:
    inputs = {"reference_price": Decimal("100"), "liquidity": 0.5, "volatility": Decimal("0.2")}
    inputs[field] = value
    with pytest.raises(ValueError):
        QuoteSimulationEngine().step("AAPL", timestamp=TIMESTAMP, **inputs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"base_spread_bps": Decimal("0")},
        {"minimum_tick": Decimal("0")},
        {"volatility_sensitivity": Decimal("-1")},
        {"spread_noise": 1.1},
    ],
)
def test_invalid_configuration_is_rejected(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        QuoteSimulationConfig(**kwargs)
