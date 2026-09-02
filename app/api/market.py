"""REST endpoints for market data and simulation controls."""

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
