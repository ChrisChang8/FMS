"""Coordinate low-latency simulation, streaming, and ordered persistence."""

import asyncio
from collections import defaultdict, deque
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from time import monotonic
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models import Candle, MarketState, MarketTick, MarketTrend, Quote, Stock
from app.simulation import (BehaviorType, CandleAggregator, DEFAULT_SIMULATED_STOCKS,
    MarketBehaviorConfig, SimulationClock, StockActivityConfig, TickSimulationConfig,
    TickSimulationEngine)
from app.storage import MemorySimulationStorage, PersistenceBatch, SimulationSession, SimulationStorage
from app.storage.models import PersistedBehavior

TICK_INTERVAL = timedelta(milliseconds=250)


class StockFactors(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    liquidity: float = Field(default=0.5, ge=0.0, le=1.0)
    volume_multiplier: float = Field(default=1.0, ge=0.1, le=3.0)
    volatility_multiplier: float = Field(default=1.0, ge=0.25, le=3.0)
    behavior_type: BehaviorType = BehaviorType.NORMAL
    behavior_strength: float = Field(default=0.5, ge=-1.0, le=1.0)


class StreamHub:
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
    def __init__(self, *, seed: int = 1, tick_history_size: int = 1000,
                 candle_history_size: int = 500, storage: SimulationStorage | None = None,
                 persistence_enabled: bool = False, queue_capacity: int = 128,
                 high_water_mark: int = 96, low_water_mark: int = 32,
                 retry_limit: int = 5, retry_base_seconds: float = .1,
                 shutdown_timeout: float = 10., history_page_limit: int = 500,
                 replay_min_speed: float = .1, replay_max_speed: float = 20.) -> None:
        if not 0 <= low_water_mark < high_water_mark <= queue_capacity:
            raise ValueError("persistence water marks must satisfy 0 <= low < high <= capacity")
        self.seed = seed
        self.stocks: tuple[Stock, ...] = tuple(DEFAULT_SIMULATED_STOCKS)
        self._stock_by_symbol = {s.symbol: s for s in self.stocks}
        self.clock, self.engine, self.aggregator = SimulationClock(), TickSimulationEngine(TickSimulationConfig(seed=seed)), CandleAggregator()
        self.hub = StreamHub()
        self.tick_history: dict[str, deque[MarketTick]] = defaultdict(lambda: deque(maxlen=tick_history_size))
        self.candle_history: dict[tuple[str, str], deque[Candle]] = defaultdict(lambda: deque(maxlen=candle_history_size))
        self.quotes: dict[str, Quote] = {}
        self.factors = {s.symbol: StockFactors() for s in self.stocks}
        self.storage = storage or MemorySimulationStorage()
        self.persistence_enabled, self.session = persistence_enabled, None
        self.running = self._desired_running = self._backpressured = False
        self._producer_task = self._writer_task = None
        self._queue: asyncio.Queue[PersistenceBatch] = asyncio.Queue(queue_capacity)
        self._high_water_mark, self._low_water_mark = high_water_mark, low_water_mark
        self._retry_limit, self._retry_base_seconds, self._shutdown_timeout = retry_limit, retry_base_seconds, shutdown_timeout
        self.history_page_limit = history_page_limit
        self.replay_min_speed, self.replay_max_speed = replay_min_speed, replay_max_speed
        self._last_committed_sequence, self._last_error = 0, None
        self._oldest_enqueued_monotonic: float | None = None
        self._pending_behaviors: list[PersistedBehavior] = []
        self._lock = asyncio.Lock()

    async def startup(self) -> None:
        await self.storage.startup(self.stocks)
        if self._producer_task is None:
            self._producer_task = asyncio.create_task(self._producer(), name="fms-market-producer")
        if self._writer_task is None:
            self._writer_task = asyncio.create_task(self._persistence_writer(), name="fms-persistence-writer")

    async def shutdown(self) -> None:
        self._desired_running = self.running = False
        drained = await self._drain()
        if self.session and self.session.status not in {"FAILED", "RESET", "COMPLETED"}:
            self.session = await self.storage.transition_session(self.session.id, "COMPLETED" if drained else "FAILED",
                ended_at=self.clock.current_time, failure_code=None if drained else "SHUTDOWN_DRAIN_TIMEOUT",
                failure_detail=None if drained else "Persistence queue did not drain before shutdown")
        for name in ("_producer_task", "_writer_task"):
            task = getattr(self, name)
            if task:
                task.cancel()
                with suppress(asyncio.CancelledError): await task
                setattr(self, name, None)
        await self.storage.shutdown()

    async def start(self) -> dict[str, Any]:
        await self.startup()
        if self.session is None:
            self.session = await self.storage.create_session(seed=self.seed, drift=.08,
                config={"simulated_start": self.clock.current_time.isoformat(), "tick_interval_ms": 250})
        if self.session.status in {"COMPLETED", "FAILED", "RESET"}:
            raise RuntimeError("reset the simulator before starting a terminal session")
        self.session = await self.storage.transition_session(self.session.id, "RUNNING")
        self._desired_running, self.running = True, not self._backpressured
        self._publish_status()
        return self.status()

    async def pause(self) -> dict[str, Any]:
        self._desired_running = self.running = False
        await self._drain()
        if self.session and self.session.status not in {"FAILED", "RESET", "COMPLETED"}:
            self.session = await self.storage.transition_session(self.session.id, "PAUSED")
        self._publish_status()
        return self.status()

    async def reset(self) -> dict[str, Any]:
        self._desired_running = self.running = False
        drained = await self._drain()
        if self.session and self.session.status not in {"FAILED", "RESET", "COMPLETED"}:
            self.session = await self.storage.transition_session(self.session.id, "RESET" if drained else "FAILED",
                ended_at=self.clock.current_time, failure_code=None if drained else "RESET_DRAIN_TIMEOUT",
                failure_detail=None if drained else "Persistence queue did not drain before reset")
        async with self._lock:
            self.clock.reset(); self.engine = TickSimulationEngine(TickSimulationConfig(seed=self.seed)); self.aggregator.reset()
            self.tick_history.clear(); self.candle_history.clear(); self.quotes.clear()
            self.factors = {s.symbol: StockFactors() for s in self.stocks}
            self.session, self._last_committed_sequence, self._last_error, self._backpressured = None, 0, None, False
        self._publish_status()
        return self.status()

    def status(self) -> dict[str, Any]:
        age = None if self._oldest_enqueued_monotonic is None else round((monotonic()-self._oldest_enqueued_monotonic)*1000, 1)
        state = "disabled" if not self.persistence_enabled else "error" if self._last_error else "backpressured" if self._backpressured else "ready"
        return {"running": self.running, "simulated_time": self.clock.current_time.isoformat(), "seed": self.seed,
            "tick_interval_ms": 250, "session_id": self.session.id if self.session else None,
            "session_status": self.session.status if self.session else None, "persistence_enabled": self.persistence_enabled,
            "persistence_state": state, "queue_depth": self._queue.qsize(), "oldest_pending_age_ms": age,
            "last_committed_sequence": self._last_committed_sequence, "last_persistence_error": self._last_error}

    def stock(self, symbol: str) -> Stock:
        normalized = symbol.strip().upper()
        if normalized not in self._stock_by_symbol: raise KeyError(normalized)
        return self._stock_by_symbol[normalized]

    def ticks(self, symbol: str, limit: int) -> list[MarketTick]:
        return list(self.tick_history[self.stock(symbol).symbol])[-limit:]

    def candles(self, symbol: str, interval: str, limit: int) -> list[Candle]:
        normalized = self.stock(symbol).symbol
        history = list(self.candle_history[(normalized, interval)])
        current = self.aggregator.snapshot(normalized, interval)
        if current: history.append(current)
        return history[-limit:]

    async def update_factors(self, symbol: str, factors: StockFactors) -> StockFactors:
        stock = self.stock(symbol)
        async with self._lock:
            self.factors[stock.symbol] = factors
            self.engine.configure_stock(stock.symbol, StockActivityConfig(liquidity=factors.liquidity, volume_multiplier=factors.volume_multiplier))
            kind = BehaviorType(factors.behavior_type)
            behavior = None if kind == BehaviorType.NORMAL else MarketBehaviorConfig(symbol=stock.symbol, behavior_type=kind,
                duration=timedelta(minutes=30), strength=factors.behavior_strength)
            self.engine.replace_behavior_from_config(behavior, symbol=stock.symbol, current_time=self.clock.current_time)
            self._pending_behaviors.append(PersistedBehavior(symbol=stock.symbol, behavior_type=kind.value,
                start_time=self.clock.current_time, duration_seconds=1800,
                strength=factors.behavior_strength))
        self._publish("status", {"factors": factors.model_dump(mode="json")}, stock.symbol)
        return factors

    async def step_once(self) -> list[MarketTick]:
        if self.session is None:
            await self.start(); self._desired_running = self.running = False
        async with self._lock:
            timestamp = self.clock.advance(TICK_INTERVAL)
            generated, quotes, candles = [], [], []
            for base in self.stocks:
                factors = self.factors[base.symbol]
                stock = base.model_copy(update={"base_volatility": base.base_volatility * Decimal(str(factors.volatility_multiplier))})
                tick = self.engine.step(stock, timestamp=timestamp, elapsed=TICK_INTERVAL)
                quote = Quote(symbol=tick.symbol, timestamp=tick.timestamp, bid=tick.bid, ask=tick.ask,
                    bid_size=tick.bid_size, ask_size=tick.ask_size)
                completed = self.aggregator.add_tick(tick)
                generated.append(tick); quotes.append(quote); candles.extend(completed)
                self.tick_history[tick.symbol].append(tick); self.quotes[tick.symbol] = quote
                self._publish("tick", tick.model_dump(mode="json"), tick.symbol, tick.timestamp.isoformat())
                self._publish("quote", quote.model_dump(mode="json"), tick.symbol, tick.timestamp.isoformat())
                for candle in completed:
                    self.candle_history[(candle.symbol, candle.interval)].append(candle)
                    self._publish("candle", candle.model_dump(mode="json"), candle.symbol, candle.timestamp.isoformat())
            states = [MarketState(symbol=s.symbol,
                trend=MarketTrend(self.factors[s.symbol].behavior_type) if self.factors[s.symbol].behavior_type in {t.value for t in MarketTrend} else MarketTrend.NORMAL,
                volatility=s.base_volatility * Decimal(str(self.factors[s.symbol].volatility_multiplier)),
                liquidity=self.factors[s.symbol].liquidity, momentum=0) for s in self.stocks]
            self._queue.put_nowait(PersistenceBatch(session_id=self.session.id, ticks=generated, quotes=quotes,
                candles=candles, market_states=states, behaviors=self._pending_behaviors,
                enqueued_at=datetime.now(UTC)))
            self._pending_behaviors = []
            if self._oldest_enqueued_monotonic is None: self._oldest_enqueued_monotonic = monotonic()
            if self._queue.qsize() >= self._high_water_mark:
                self._backpressured, self.running = True, False; self._publish_status()
            return generated

    async def _producer(self) -> None:
        while True:
            if self.running: await self.step_once()
            await asyncio.sleep(.25)

    async def _persistence_writer(self) -> None:
        while True:
            batch = await self._queue.get()
            try:
                for attempt in range(self._retry_limit + 1):
                    try:
                        await self.storage.persist_batch(batch); self._last_committed_sequence = batch.last_sequence; self._last_error = None; break
                    except Exception as exc:
                        self._last_error = f"{type(exc).__name__}: {exc}"
                        if attempt >= self._retry_limit:
                            self._desired_running = self.running = False
                            if self.session:
                                self.session = await self.storage.transition_session(self.session.id, "FAILED", ended_at=self.clock.current_time,
                                    failure_code="PERSISTENCE_WRITE_FAILED", failure_detail=str(exc)[:500])
                            self._publish_status(); break
                        await asyncio.sleep(self._retry_base_seconds * 2**attempt)
            finally:
                self._queue.task_done()
                self._oldest_enqueued_monotonic = monotonic() if self._queue.qsize() else None
                if self._backpressured and self._queue.qsize() <= self._low_water_mark and not self._last_error:
                    self._backpressured = False; self.running = self._desired_running; self._publish_status()

    async def _drain(self) -> bool:
        try:
            await asyncio.wait_for(self._queue.join(), self._shutdown_timeout); return self._last_error is None
        except TimeoutError: return False

    def _publish_status(self) -> None: self._publish("status", self.status())
    def _publish(self, event_type: str, data: dict[str, Any], symbol: str | None = None, timestamp: str | None = None) -> None:
        self.hub.publish({"type": event_type, "timestamp": timestamp or self.clock.current_time.isoformat(), "symbol": symbol, "data": data})
