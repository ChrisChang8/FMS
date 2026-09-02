"""Application service coordinating the in-memory market simulation."""

import asyncio
from collections import defaultdict, deque
from contextlib import suppress
from datetime import timedelta
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models import Candle, MarketTick, Quote, Stock
from app.simulation import (
    BehaviorType,
    CandleAggregator,
    DEFAULT_SIMULATED_STOCKS,
    MarketBehaviorConfig,
    SimulationClock,
    StockActivityConfig,
    TickSimulationConfig,
    TickSimulationEngine,
)

TICK_INTERVAL = timedelta(milliseconds=250)


class StockFactors(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    liquidity: float = Field(default=0.5, ge=0.0, le=1.0)
    volume_multiplier: float = Field(default=1.0, ge=0.1, le=3.0)
    volatility_multiplier: float = Field(default=1.0, ge=0.25, le=3.0)
    behavior_type: BehaviorType = BehaviorType.NORMAL
    behavior_strength: float = Field(default=0.5, ge=-1.0, le=1.0)


class StreamHub:
    """Non-blocking fan-out using one bounded queue per connection."""

    def __init__(self, queue_size: int = 256) -> None:
        self.queue_size = queue_size
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(self.queue_size)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        self._subscribers.discard(queue)

    def publish(self, event: dict[str, Any]) -> None:
        for queue in tuple(self._subscribers):
            if queue.full():
                with suppress(asyncio.QueueEmpty):
                    queue.get_nowait()
            with suppress(asyncio.QueueFull):
                queue.put_nowait(event)


class SimulationService:
    """Own simulation state and expose safe lifecycle/history operations."""

    def __init__(self, *, seed: int = 1, tick_history_size: int = 1000, candle_history_size: int = 500) -> None:
        self.seed = seed
        self.stocks: tuple[Stock, ...] = tuple(DEFAULT_SIMULATED_STOCKS)
        self._stock_by_symbol = {stock.symbol: stock for stock in self.stocks}
        self.clock = SimulationClock()
        self.engine = TickSimulationEngine(TickSimulationConfig(seed=seed))
        self.aggregator = CandleAggregator()
        self.hub = StreamHub()
        self.tick_history: dict[str, deque[MarketTick]] = defaultdict(lambda: deque(maxlen=tick_history_size))
        self.candle_history: dict[tuple[str, str], deque[Candle]] = defaultdict(
            lambda: deque(maxlen=candle_history_size)
        )
        self.quotes: dict[str, Quote] = {}
        self.factors = {stock.symbol: StockFactors() for stock in self.stocks}
        self.running = False
        self._task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()

    async def startup(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._producer(), name="fms-market-producer")

    async def shutdown(self) -> None:
        self.running = False
        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def start(self) -> dict[str, Any]:
        await self.startup()
        self.running = True
        self._publish_status()
        return self.status()

    async def pause(self) -> dict[str, Any]:
        self.running = False
        self._publish_status()
        return self.status()

    async def reset(self) -> dict[str, Any]:
        async with self._lock:
            self.running = False
            self.clock.reset()
            self.engine = TickSimulationEngine(TickSimulationConfig(seed=self.seed))
            self.aggregator.reset()
            self.tick_history.clear()
            self.candle_history.clear()
            self.quotes.clear()
            self.factors = {stock.symbol: StockFactors() for stock in self.stocks}
        self._publish_status()
        return self.status()

    def status(self) -> dict[str, Any]:
        return {
            "running": self.running,
            "simulated_time": self.clock.current_time.isoformat(),
            "seed": self.seed,
            "tick_interval_ms": int(TICK_INTERVAL.total_seconds() * 1000),
        }

    def stock(self, symbol: str) -> Stock:
        normalized = symbol.strip().upper()
        if normalized not in self._stock_by_symbol:
            raise KeyError(normalized)
        return self._stock_by_symbol[normalized]

    def ticks(self, symbol: str, limit: int) -> list[MarketTick]:
        self.stock(symbol)
        return list(self.tick_history[symbol.strip().upper()])[-limit:]

    def candles(self, symbol: str, interval: str, limit: int) -> list[Candle]:
        normalized = self.stock(symbol).symbol
        history = list(self.candle_history[(normalized, interval)])
        current = self.aggregator.snapshot(normalized, interval)
        if current is not None:
            history.append(current)
        return history[-limit:]

    async def update_factors(self, symbol: str, factors: StockFactors) -> StockFactors:
        stock = self.stock(symbol)
        async with self._lock:
            self.factors[stock.symbol] = factors
            self.engine.configure_stock(
                stock.symbol,
                StockActivityConfig(
                    liquidity=factors.liquidity,
                    volume_multiplier=factors.volume_multiplier,
                ),
            )
            behavior = None
            behavior_type = BehaviorType(factors.behavior_type)
            if behavior_type != BehaviorType.NORMAL:
                behavior = MarketBehaviorConfig(
                    symbol=stock.symbol,
                    behavior_type=behavior_type,
                    duration=timedelta(minutes=30),
                    strength=factors.behavior_strength,
                )
            self.engine.replace_behavior_from_config(
                behavior, symbol=stock.symbol, current_time=self.clock.current_time
            )
        self._publish("status", {"factors": factors.model_dump(mode="json")}, stock.symbol)
        return factors

    async def step_once(self) -> list[MarketTick]:
        """Generate a deterministic batch; public to support precise tests."""
        async with self._lock:
            timestamp = self.clock.advance(TICK_INTERVAL)
            generated: list[MarketTick] = []
            for base_stock in self.stocks:
                factors = self.factors[base_stock.symbol]
                stock = base_stock.model_copy(
                    update={"base_volatility": base_stock.base_volatility * Decimal(str(factors.volatility_multiplier))}
                )
                tick = self.engine.step(stock, timestamp=timestamp, elapsed=TICK_INTERVAL)
                generated.append(tick)
                self.tick_history[tick.symbol].append(tick)
                quote = Quote(
                    symbol=tick.symbol,
                    timestamp=tick.timestamp,
                    bid=tick.bid,
                    ask=tick.ask,
                    bid_size=tick.bid_size,
                    ask_size=tick.ask_size,
                )
                self.quotes[tick.symbol] = quote
                completed = self.aggregator.add_tick(tick)
                self._publish("tick", tick.model_dump(mode="json"), tick.symbol, tick.timestamp.isoformat())
                self._publish("quote", quote.model_dump(mode="json"), tick.symbol, tick.timestamp.isoformat())
                for candle in completed:
                    self.candle_history[(candle.symbol, candle.interval)].append(candle)
                    self._publish("candle", candle.model_dump(mode="json"), candle.symbol, candle.timestamp.isoformat())
            return generated

    async def _producer(self) -> None:
        while True:
            if self.running:
                await self.step_once()
            await asyncio.sleep(TICK_INTERVAL.total_seconds())

    def _publish_status(self) -> None:
        self._publish("status", self.status())

    def _publish(self, event_type: str, data: dict[str, Any], symbol: str | None = None, timestamp: str | None = None) -> None:
        self.hub.publish(
            {
                "type": event_type,
                "timestamp": timestamp or self.clock.current_time.isoformat(),
                "symbol": symbol,
                "data": data,
            }
        )
