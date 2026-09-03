"""Aggregate raw market ticks into deterministic OHLCV candles."""

from datetime import datetime

from app.models import Candle, MarketTick
from app.simulation.clock import MARKET_TIMEZONE


SUPPORTED_CANDLE_INTERVALS = {"1s": 1, "1m": 60}


class CandleAggregator:
    """Maintain an in-progress candle for every symbol and interval."""

    def __init__(self, intervals: tuple[str, ...] = ("1s", "1m")) -> None:
        unknown = set(intervals) - SUPPORTED_CANDLE_INTERVALS.keys()
        if unknown:
            raise ValueError(f"unsupported candle interval: {sorted(unknown)[0]}")
        self.intervals = intervals
        self._current: dict[tuple[str, str], Candle] = {}
        self._last_tick_time: dict[str, datetime] = {}

    def add_tick(self, tick: MarketTick) -> list[Candle]:
        """Apply one tick and return candles closed by this tick."""
        last = self._last_tick_time.get(tick.symbol)
        if last is not None and tick.timestamp < last:
            raise ValueError("tick timestamp must not move backwards")
        self._last_tick_time[tick.symbol] = tick.timestamp
        completed: list[Candle] = []
        for interval in self.intervals:
            key = (tick.symbol, interval)
            bucket = self._bucket_start(tick.timestamp, interval)
            candle = self._current.get(key)
            if candle is None or candle.timestamp != bucket:
                if candle is not None:
                    completed.append(candle.model_copy(deep=True))
                self._current[key] = self._from_tick(tick, interval, bucket)
            else:
                self._current[key] = candle.model_copy(
                    update={
                        "high": max(candle.high, tick.price),
                        "low": min(candle.low, tick.price),
                        "close": tick.price,
                        "volume": candle.volume + tick.trade_volume,
                        "trade_count": candle.trade_count + 1,
                    }
                )
        return completed

    def snapshot(self, symbol: str, interval: str) -> Candle | None:
        self._validate_interval(interval)
        candle = self._current.get((symbol.strip().upper(), interval))
        return candle.model_copy(deep=True) if candle else None

    def reset(self) -> None:
        self._current.clear()
        self._last_tick_time.clear()

    @staticmethod
    def _from_tick(tick: MarketTick, interval: str, timestamp: datetime) -> Candle:
        return Candle(
            symbol=tick.symbol,
            interval=interval,
            timestamp=timestamp,
            open=tick.price,
            high=tick.price,
            low=tick.price,
            close=tick.price,
            volume=tick.trade_volume,
            trade_count=1,
        )

    @staticmethod
    def _bucket_start(timestamp: datetime, interval: str) -> datetime:
        seconds = SUPPORTED_CANDLE_INTERVALS[interval]
        local = timestamp.astimezone(MARKET_TIMEZONE)
        epoch = int(local.timestamp())
        return datetime.fromtimestamp(epoch - (epoch % seconds), tz=MARKET_TIMEZONE)

    @staticmethod
    def _validate_interval(interval: str) -> None:
        if interval not in SUPPORTED_CANDLE_INTERVALS:
            raise ValueError(f"unsupported candle interval: {interval}")
