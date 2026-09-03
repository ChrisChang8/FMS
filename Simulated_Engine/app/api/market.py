"""REST endpoints for live and historical market data."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.services.simulation import SimulationService, StockFactors
from app.simulation import SUPPORTED_CANDLE_INTERVALS

router = APIRouter()


def get_service(request: Request) -> SimulationService:
    return request.app.state.simulation


def require_symbol(service: SimulationService, symbol: str) -> str:
    try:
        return service.stock(symbol).symbol
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown stock symbol: {symbol.upper()}") from exc


@router.get("/stocks")
def stocks(service: SimulationService = Depends(get_service)) -> list[dict]:
    return [
        {**stock.model_dump(mode="json"), "factors": service.factors[stock.symbol].model_dump(mode="json")}
        for stock in service.stocks
    ]


@router.get("/quotes/{symbol}")
def quote(symbol: str, service: SimulationService = Depends(get_service)) -> dict:
    normalized = require_symbol(service, symbol)
    current = service.quotes.get(normalized)
    if current is None:
        raise HTTPException(status_code=404, detail=f"No quote available for {normalized}")
    return current.model_dump(mode="json")


@router.get("/ticks/{symbol}")
def ticks(symbol: str, limit: int = Query(100, ge=1, le=1000), service: SimulationService = Depends(get_service)) -> list[dict]:
    normalized = require_symbol(service, symbol)
    return [tick.model_dump(mode="json") for tick in service.ticks(normalized, limit)]


@router.get("/candles/{symbol}")
def candles(
    symbol: str,
    interval: str = Query("1s"),
    limit: int = Query(100, ge=1, le=500),
    service: SimulationService = Depends(get_service),
) -> list[dict]:
    normalized = require_symbol(service, symbol)
    if interval not in SUPPORTED_CANDLE_INTERVALS:
        raise HTTPException(status_code=422, detail="interval must be one of: 1s, 1m")
    return [candle.model_dump(mode="json") for candle in service.candles(normalized, interval, limit)]


@router.get("/simulation/status")
def status(service: SimulationService = Depends(get_service)) -> dict:
    return service.status()


@router.post("/simulation/start")
async def start(service: SimulationService = Depends(get_service)) -> dict:
    return await service.start()


@router.post("/simulation/pause")
async def pause(service: SimulationService = Depends(get_service)) -> dict:
    return await service.pause()


@router.post("/simulation/reset")
async def reset(service: SimulationService = Depends(get_service)) -> dict:
    return await service.reset()


@router.patch("/simulation/stocks/{symbol}/factors")
async def factors(symbol: str, body: StockFactors, service: SimulationService = Depends(get_service)) -> dict:
    normalized = require_symbol(service, symbol)
    updated = await service.update_factors(normalized, body)
    return updated.model_dump(mode="json")


def _session_json(session) -> dict:
    return {**session.model_dump(mode="json"), "replay_complete": session.replay_complete}


@router.get("/simulation/sessions")
async def sessions(
    before_id: int | None = Query(None, ge=1),
    limit: int = Query(50, ge=1),
    service: SimulationService = Depends(get_service),
) -> list[dict]:
    if limit > service.history_page_limit:
        raise HTTPException(status_code=422, detail=f"limit must be <= {service.history_page_limit}")
    return [_session_json(item) for item in await service.storage.list_sessions(before_id=before_id, limit=limit)]


@router.get("/simulation/sessions/{session_id}")
async def session(session_id: int, service: SimulationService = Depends(get_service)) -> dict:
    found = await service.storage.get_session(session_id)
    if found is None:
        raise HTTPException(status_code=404, detail="Unknown simulation session")
    return _session_json(found)


@router.get("/simulation/sessions/{session_id}/ticks")
async def historical_ticks(
    session_id: int,
    symbol: str | None = Query(None),
    after_sequence: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    service: SimulationService = Depends(get_service),
) -> list[dict]:
    if await service.storage.get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="Unknown simulation session")
    if limit > service.history_page_limit:
        raise HTTPException(status_code=422, detail=f"limit must be <= {service.history_page_limit}")
    normalized = require_symbol(service, symbol) if symbol else None
    rows = await service.storage.read_ticks(
        session_id, symbol=normalized, after_sequence=after_sequence, limit=limit
    )
    return [item.model_dump(mode="json") for item in rows]


@router.get("/simulation/sessions/{session_id}/candles")
async def historical_candles(
    session_id: int,
    symbol: str | None = Query(None),
    interval: str | None = Query(None),
    after_timestamp: datetime | None = Query(None),
    limit: int = Query(100, ge=1),
    service: SimulationService = Depends(get_service),
) -> list[dict]:
    if await service.storage.get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="Unknown simulation session")
    if limit > service.history_page_limit:
        raise HTTPException(status_code=422, detail=f"limit must be <= {service.history_page_limit}")
    normalized = require_symbol(service, symbol) if symbol else None
    if interval is not None and interval not in SUPPORTED_CANDLE_INTERVALS:
        raise HTTPException(status_code=422, detail="interval must be one of: 1s, 1m")
    rows = await service.storage.read_candles(
        session_id, symbol=normalized, interval=interval,
        after_timestamp=after_timestamp, limit=limit,
    )
    return [item.model_dump(mode="json") for item in rows]
