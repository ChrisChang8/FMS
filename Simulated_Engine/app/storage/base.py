"""Abstract persistence boundary used by simulation and transport code."""

from datetime import datetime
from typing import Protocol, Sequence

from app.models import Candle, MarketTick, Stock
from app.storage.models import PersistenceBatch, SessionStatus, SimulationSession


class SimulationStorage(Protocol):
    async def startup(self, stocks: Sequence[Stock]) -> None: ...
    async def shutdown(self) -> None: ...
    async def ready(self) -> bool: ...
    async def create_session(self, *, seed: int, drift: float, config: dict) -> SimulationSession: ...
    async def transition_session(
        self,
        session_id: int,
        status: SessionStatus,
        *,
        ended_at: datetime | None = None,
        failure_code: str | None = None,
        failure_detail: str | None = None,
    ) -> SimulationSession: ...
    async def persist_batch(self, batch: PersistenceBatch) -> None: ...
    async def list_sessions(self, *, before_id: int | None, limit: int) -> list[SimulationSession]: ...
    async def get_session(self, session_id: int) -> SimulationSession | None: ...
    async def read_ticks(
        self, session_id: int, *, symbol: str | None, after_sequence: int, limit: int
    ) -> list[MarketTick]: ...
    async def read_candles(
        self,
        session_id: int,
        *,
        symbol: str | None,
        interval: str | None,
        after_timestamp: datetime | None,
        limit: int,
    ) -> list[Candle]: ...
