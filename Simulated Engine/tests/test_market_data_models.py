from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models import Candle, MarketState, MarketTick, MarketTrend, Quote, Stock


TIMESTAMP = datetime(2026, 8, 29, 14, 31, 1, tzinfo=UTC)


def test_stock_normalizes_symbol_and_accepts_valid_reference_data() -> None:
    stock = Stock(
        symbol=" aapl ",
        company_name="Apple Inc.",
        starting_price=Decimal("224.15"),
        sector="Technology",
        average_volume=55_000_000,
        base_volatility=Decimal("0.018"),
    )

    assert stock.symbol == "AAPL"
    assert stock.starting_price == Decimal("224.15")


def test_stock_rejects_invalid_price_and_volume() -> None:
    with pytest.raises(ValidationError):
        Stock(
            symbol="AAPL",
            company_name="Apple Inc.",
            starting_price=Decimal("0"),
            sector="Technology",
            average_volume=0,
            base_volatility=Decimal("0.018"),
        )


def test_quote_requires_bid_lower_than_ask() -> None:
    with pytest.raises(ValidationError, match="bid must be lower than ask"):
        Quote(
            symbol="MSFT",
            timestamp=TIMESTAMP,
            bid=Decimal("430.10"),
            ask=Decimal("430.10"),
            bid_size=100,
            ask_size=200,
        )


def test_quote_exposes_spread() -> None:
    quote = Quote(
        symbol="MSFT",
        timestamp=TIMESTAMP,
        bid=Decimal("430.10"),
        ask=Decimal("430.14"),
        bid_size=100,
        ask_size=200,
    )

    assert quote.spread == Decimal("0.04")


def test_quote_requires_timezone_aware_timestamp() -> None:
    with pytest.raises(ValidationError, match="timestamp must include timezone information"):
        Quote(
            symbol="MSFT",
            timestamp=datetime(2026, 8, 29, 14, 31, 1),
            bid=Decimal("430.10"),
            ask=Decimal("430.14"),
            bid_size=100,
            ask_size=200,
        )


def test_market_tick_requires_price_inside_quote() -> None:
    with pytest.raises(ValidationError, match="price must be between bid and ask"):
        MarketTick(
            symbol="NVDA",
            timestamp=TIMESTAMP,
            price=Decimal("900.50"),
            bid=Decimal("900.10"),
            ask=Decimal("900.20"),
            bid_size=400,
            ask_size=500,
            trade_volume=100,
            sequence_number=1,
        )


def test_market_tick_accepts_internally_consistent_values() -> None:
    tick = MarketTick(
        symbol="NVDA",
        timestamp=TIMESTAMP,
        price=Decimal("900.15"),
        bid=Decimal("900.10"),
        ask=Decimal("900.20"),
        bid_size=400,
        ask_size=500,
        trade_volume=100,
        sequence_number=1,
    )

    assert tick.symbol == "NVDA"
    assert tick.sequence_number == 1


def test_candle_requires_high_and_low_to_bound_ohlc_prices() -> None:
    with pytest.raises(ValidationError, match="high must be the greatest OHLC price"):
        Candle(
            symbol="TSLA",
            interval="1m",
            timestamp=TIMESTAMP,
            open=Decimal("250.00"),
            high=Decimal("251.00"),
            low=Decimal("249.50"),
            close=Decimal("252.00"),
            volume=10_000,
            trade_count=40,
        )


def test_candle_accepts_valid_ohlcv_data() -> None:
    candle = Candle(
        symbol="TSLA",
        interval="1m",
        timestamp=TIMESTAMP,
        open=Decimal("250.00"),
        high=Decimal("252.00"),
        low=Decimal("249.50"),
        close=Decimal("251.25"),
        volume=10_000,
        trade_count=40,
    )

    assert candle.high == Decimal("252.00")
    assert candle.low == Decimal("249.50")


def test_market_state_bounds_liquidity_and_momentum() -> None:
    with pytest.raises(ValidationError):
        MarketState(
            symbol="AMZN",
            trend=MarketTrend.UPTREND,
            volatility=Decimal("0.02"),
            liquidity=1.5,
            momentum=0.2,
        )

    with pytest.raises(ValidationError):
        MarketState(
            symbol="AMZN",
            trend=MarketTrend.UPTREND,
            volatility=Decimal("0.02"),
            liquidity=0.8,
            momentum=-1.2,
        )


def test_market_state_accepts_valid_behavior_values() -> None:
    state = MarketState(
        symbol="AMZN",
        trend=MarketTrend.UPTREND,
        volatility=Decimal("0.02"),
        liquidity=0.8,
        momentum=0.2,
    )

    assert state.trend is MarketTrend.UPTREND
