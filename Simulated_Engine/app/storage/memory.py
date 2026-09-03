"""In-process storage adapter for tests and database-free local use."""

from datetime import UTC, datetime
from typing import Sequence

from app.models import Candle, MarketTick, Stock
from app.storage.models import PersistenceBatch, SessionStatus, SimulationSession


class MemorySimulationStorage:
    def __init__(self) -> None:
        self.sessions: dict[int, SimulationSession] = {}
        self.ticks: dict[int, list[MarketTick]] = {}
        self.candles: dict[int, list[Candle]] = {}
        self._next_id = 1

    async def startup(self, stocks: Sequence[Stock]) -> None:
        return None

    async def shutdown(self) -> None:
        return None

    async def ready(self) -> bool:
        return True

    async def create_session(self, *, seed: int, drift: float, config: dict) -> SimulationSession:
        now = datetime.now(UTC)
        session = SimulationSession(
            id=self._next_id, seed=seed, drift=drift, config=config, status="CREATED",
            started_at=datetime.fromisoformat(config["simulated_start"]), created_at=now,
        )
        self._next_id += 1
        self.sessions[session.id] = session
        self.ticks[session.id] = []
        self.candles[session.id] = []
        return session.model_copy(deep=True)

    async def transition_session(
        self, session_id: int, status: SessionStatus, *, ended_at: datetime | None = None,
        failure_code: str | None = None, failure_detail: str | None = None,
    ) -> SimulationSession:
        current = self.sessions[session_id]
        updated = current.model_copy(update={
            "status": status, "ended_at": ended_at,
            "failure_code": failure_code, "failure_detail": failure_detail,
        })
        self.sessions[session_id] = updated
        return updated.model_copy(deep=True)

    async def persist_batch(self, batch: PersistenceBatch) -> None:
        existing = {tick.sequence_number for tick in self.ticks[batch.session_id]}
        self.ticks[batch.session_id].extend(
            tick.model_copy(deep=True) for tick in batch.ticks if tick.sequence_number not in existing
        )
        candle_keys = {(c.symbol, c.interval, c.timestamp) for c in self.candles[batch.session_id]}
        self.candles[batch.session_id].extend(
            c.model_copy(deep=True) for c in batch.candles
            if (c.symbol, c.interval, c.timestamp) not in candle_keys
        )

    async def list_sessions(self, *, before_id: int | None, limit: int) -> list[SimulationSession]:
        ids = sorted((i for i in self.sessions if before_id is None or i < before_id), reverse=True)[:limit]
        return [await self.get_session(i) for i in ids]  # type: ignore[list-item]

    async def get_session(self, session_id: int) -> SimulationSession | None:
        session = self.sessions.get(session_id)
        if session is None:
            return None
        return session.model_copy(update={
            "tick_count": len(self.ticks[session_id]),
            "candle_count": len(self.candles[session_id]),
        }, deep=True)

    async def read_ticks(
        self, session_id: int, *, symbol: str | None, after_sequence: int, limit: int
    ) -> list[MarketTick]:
        rows = (t for t in self.ticks.get(session_id, []) if t.sequence_number > after_sequence)
        if symbol:
            rows = (t for t in rows if t.symbol == symbol)
        return [t.model_copy(deep=True) for t in sorted(rows, key=lambda value: value.sequence_number)[:limit]]

    async def read_candles(
        self, session_id: int, *, symbol: str | None, interval: str | None,
        after_timestamp: datetime | None, limit: int,
    ) -> list[Candle]:
        rows = self.candles.get(session_id, [])
        filtered = [c for c in rows if (not symbol or c.symbol == symbol)
                    and (not interval or c.interval == interval)
                    and (after_timestamp is None or c.timestamp > after_timestamp)]
        return [c.model_copy(deep=True) for c in sorted(filtered, key=lambda value: (value.timestamp, value.symbol))[:limit]]
