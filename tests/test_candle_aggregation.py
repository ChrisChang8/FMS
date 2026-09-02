from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.models import MarketTick
from app.simulation import CandleAggregator, MARKET_TIMEZONE

START = datetime(2026, 8, 31, 8, 30, tzinfo=MARKET_TIMEZONE)


def tick(offset: float, price: str, volume: int = 10, symbol: str = "AAPL") -> MarketTick:
    value = Decimal(price)
    return MarketTick(symbol=symbol, timestamp=START + timedelta(seconds=offset), price=value,
                      bid=value - Decimal("0.01"), ask=value + Decimal("0.01"), bid_size=10,
                      ask_size=10, trade_volume=volume, sequence_number=max(1, int(offset * 10) + 1))


def test_ohlcv_and_boundary_completion() -> None:
    aggregator = CandleAggregator(("1s",))
    assert aggregator.add_tick(tick(0.1, "10", 3)) == []
    aggregator.add_tick(tick(0.4, "12", 4))
    aggregator.add_tick(tick(0.9, "9", 5))
    completed = aggregator.add_tick(tick(1.0, "11", 6))
    candle = completed[0]
    assert (candle.open, candle.high, candle.low, candle.close) == tuple(map(Decimal, ["10", "12", "9", "9"]))
    assert candle.volume == 12
    assert candle.trade_count == 3
    assert candle.timestamp == START


def test_intervals_and_symbols_are_independent() -> None:
    aggregator = CandleAggregator()
    aggregator.add_tick(tick(0, "10", symbol="AAPL"))
    aggregator.add_tick(tick(0, "20", symbol="MSFT"))
    assert aggregator.snapshot("AAPL", "1s").close == Decimal("10")
    assert aggregator.snapshot("MSFT", "1m").close == Decimal("20")


def test_snapshot_is_a_copy_and_reset_clears_state() -> None:
    aggregator = CandleAggregator(("1s",))
    aggregator.add_tick(tick(0, "10"))
    first = aggregator.snapshot("AAPL", "1s")
    aggregator.add_tick(tick(0.5, "11"))
    assert first.close == Decimal("10")
    aggregator.reset()
    assert aggregator.snapshot("AAPL", "1s") is None


def test_out_of_order_ticks_and_bad_interval_are_rejected() -> None:
    aggregator = CandleAggregator(("1s",))
    aggregator.add_tick(tick(1, "10"))
    with pytest.raises(ValueError, match="backwards"):
        aggregator.add_tick(tick(0, "10"))
    with pytest.raises(ValueError, match="unsupported"):
        aggregator.snapshot("AAPL", "5m")
