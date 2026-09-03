"""Storage-facing models for durable simulation history."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models import Candle, MarketState, MarketTick, Quote

SessionStatus = Literal["CREATED", "RUNNING", "PAUSED", "COMPLETED", "FAILED", "RESET"]


class SimulationSession(BaseModel):
    id: int
    seed: int
    drift: float
    config: dict[str, Any]
    config_version: int = 1
    status: SessionStatus
    started_at: datetime
    ended_at: datetime | None = None
    created_at: datetime
    failure_code: str | None = None
    failure_detail: str | None = None
    tick_count: int = 0
    candle_count: int = 0

    @property
    def replay_complete(self) -> bool:
        return self.status in {"COMPLETED", "RESET"}


class PersistenceBatch(BaseModel):
    session_id: int
    ticks: list[MarketTick]
    quotes: list[Quote]
    candles: list[Candle] = Field(default_factory=list)
    market_states: list[MarketState] = Field(default_factory=list)
    behaviors: list["PersistedBehavior"] = Field(default_factory=list)
    enqueued_at: datetime

    @property
    def first_sequence(self) -> int:
        return self.ticks[0].sequence_number

    @property
    def last_sequence(self) -> int:
        return self.ticks[-1].sequence_number


class PersistedBehavior(BaseModel):
    symbol: str
    behavior_type: str
    start_time: datetime
    duration_seconds: float
    strength: float
