"""PostgreSQL implementation of the simulation storage boundary."""

import json
from datetime import datetime
from typing import Any, Sequence

import asyncpg

from app.models import Candle, MarketTick, Stock
from app.storage.models import PersistenceBatch, SessionStatus, SimulationSession


class PostgresSimulationStorage:
    def __init__(self, url: str, *, min_size: int = 1, max_size: int = 5) -> None:
        self.url = url
        self.min_size = min_size
        self.max_size = max_size
        self.pool: asyncpg.Pool | None = None

    async def startup(self, stocks: Sequence[Stock]) -> None:
        self.pool = await asyncpg.create_pool(self.url, min_size=self.min_size, max_size=self.max_size)
        async with self.pool.acquire() as connection:
            await connection.executemany(
                """INSERT INTO stocks
                   (symbol, company_name, starting_price, sector, average_volume, base_volatility)
                   VALUES ($1, $2, $3, $4, $5, $6)
                   ON CONFLICT (symbol) DO UPDATE SET
                     company_name=EXCLUDED.company_name, starting_price=EXCLUDED.starting_price,
                     sector=EXCLUDED.sector, average_volume=EXCLUDED.average_volume,
                     base_volatility=EXCLUDED.base_volatility""",
                [(s.symbol, s.company_name, s.starting_price, s.sector, s.average_volume, s.base_volatility)
                 for s in stocks],
            )

    async def shutdown(self) -> None:
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def ready(self) -> bool:
        if not self.pool:
            return False
        try:
            return bool(await self.pool.fetchval("SELECT TRUE"))
        except asyncpg.PostgresError:
            return False

    async def create_session(self, *, seed: int, drift: float, config: dict) -> SimulationSession:
        row = await self._pool().fetchrow(
            """INSERT INTO simulation_sessions
               (seed, drift, config, config_version, status, started_at)
               VALUES ($1, $2, $3::jsonb, 1, 'CREATED', $4) RETURNING *""",
            seed, drift, json.dumps(config), datetime.fromisoformat(config["simulated_start"]),
        )
        return self._session(row)

    async def transition_session(
        self, session_id: int, status: SessionStatus, *, ended_at: datetime | None = None,
        failure_code: str | None = None, failure_detail: str | None = None,
    ) -> SimulationSession:
        row = await self._pool().fetchrow(
            """UPDATE simulation_sessions SET status=$2, ended_at=$3,
               failure_code=$4, failure_detail=$5 WHERE id=$1 RETURNING *""",
            session_id, status, ended_at, failure_code, failure_detail,
        )
        if row is None:
            raise KeyError(session_id)
        return self._session(row)

    async def persist_batch(self, batch: PersistenceBatch) -> None:
        async with self._pool().acquire() as connection:
            async with connection.transaction():
                await connection.executemany(
                    """INSERT INTO market_ticks
                       (session_id,symbol,"timestamp",price,bid,ask,bid_size,ask_size,trade_volume,sequence_number)
                       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
                       ON CONFLICT (session_id,sequence_number) DO NOTHING""",
                    [(batch.session_id, t.symbol, t.timestamp, t.price, t.bid, t.ask,
                      t.bid_size, t.ask_size, t.trade_volume, t.sequence_number) for t in batch.ticks],
                )
                await connection.executemany(
                    """INSERT INTO quotes
                       (session_id,symbol,"timestamp",bid,ask,bid_size,ask_size)
                       VALUES ($1,$2,$3,$4,$5,$6,$7)
                       ON CONFLICT (session_id,symbol,"timestamp") DO NOTHING""",
                    [(batch.session_id, q.symbol, q.timestamp, q.bid, q.ask, q.bid_size, q.ask_size)
                     for q in batch.quotes],
                )
                if batch.candles:
                    await connection.executemany(
                        """INSERT INTO candles
                           (session_id,symbol,"interval","timestamp",open,high,low,close,volume,trade_count)
                           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
                           ON CONFLICT (session_id,symbol,"interval","timestamp") DO NOTHING""",
                        [(batch.session_id, c.symbol, c.interval, c.timestamp, c.open, c.high,
                          c.low, c.close, c.volume, c.trade_count) for c in batch.candles],
                    )
                await connection.executemany(
                    """INSERT INTO market_states
                       (session_id,symbol,trend,volatility,liquidity,momentum,updated_at)
                       VALUES ($1,$2,$3,$4,$5,$6,$7)
                       ON CONFLICT (session_id,symbol) DO UPDATE SET
                         trend=EXCLUDED.trend, volatility=EXCLUDED.volatility,
                         liquidity=EXCLUDED.liquidity, momentum=EXCLUDED.momentum,
                         updated_at=EXCLUDED.updated_at""",
                    [(batch.session_id, s.symbol, s.trend.value, s.volatility, s.liquidity,
                      s.momentum, batch.ticks[-1].timestamp) for s in batch.market_states],
                )
                if batch.behaviors:
                    await connection.executemany(
                        """INSERT INTO market_behaviors
                           (session_id,symbol,behavior_type,start_time,duration_seconds,strength)
                           VALUES ($1,$2,$3,$4,$5,$6)""",
                        [(batch.session_id, b.symbol, b.behavior_type, b.start_time,
                          b.duration_seconds, b.strength) for b in batch.behaviors],
                    )

    async def list_sessions(self, *, before_id: int | None, limit: int) -> list[SimulationSession]:
        rows = await self._pool().fetch(
            """SELECT s.*,
               (SELECT count(*) FROM market_ticks t WHERE t.session_id=s.id) tick_count,
               (SELECT count(*) FROM candles c WHERE c.session_id=s.id) candle_count
               FROM simulation_sessions s WHERE ($1::bigint IS NULL OR s.id < $1)
               ORDER BY s.id DESC LIMIT $2""", before_id, limit,
        )
        return [self._session(row) for row in rows]

    async def get_session(self, session_id: int) -> SimulationSession | None:
        row = await self._pool().fetchrow(
            """SELECT s.*,
               (SELECT count(*) FROM market_ticks t WHERE t.session_id=s.id) tick_count,
               (SELECT count(*) FROM candles c WHERE c.session_id=s.id) candle_count
               FROM simulation_sessions s WHERE s.id=$1""", session_id,
        )
        return self._session(row) if row else None

    async def read_ticks(
        self, session_id: int, *, symbol: str | None, after_sequence: int, limit: int
    ) -> list[MarketTick]:
        rows = await self._pool().fetch(
            """SELECT symbol,"timestamp",price,bid,ask,bid_size,ask_size,trade_volume,sequence_number
               FROM market_ticks WHERE session_id=$1 AND sequence_number>$2
               AND ($3::varchar IS NULL OR symbol=$3)
               ORDER BY sequence_number LIMIT $4""", session_id, after_sequence, symbol, limit,
        )
        return [MarketTick.model_validate(dict(row)) for row in rows]

    async def read_candles(
        self, session_id: int, *, symbol: str | None, interval: str | None,
        after_timestamp: datetime | None, limit: int,
    ) -> list[Candle]:
        rows = await self._pool().fetch(
            """SELECT symbol,"interval","timestamp",open,high,low,close,volume,trade_count
               FROM candles WHERE session_id=$1
               AND ($2::varchar IS NULL OR symbol=$2) AND ($3::text IS NULL OR "interval"=$3)
               AND ($4::timestamptz IS NULL OR "timestamp">$4)
               ORDER BY "timestamp",symbol LIMIT $5""",
            session_id, symbol, interval, after_timestamp, limit,
        )
        return [Candle.model_validate(dict(row)) for row in rows]

    def _pool(self) -> asyncpg.Pool:
        if self.pool is None:
            raise RuntimeError("PostgreSQL storage is not started")
        return self.pool

    @staticmethod
    def _session(row: Any) -> SimulationSession:
        data = dict(row)
        if isinstance(data.get("config"), str):
            data["config"] = json.loads(data["config"])
        data.setdefault("tick_count", 0)
        data.setdefault("candle_count", 0)
        return SimulationSession.model_validate(data)
