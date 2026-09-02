"""WebSocket transport for live market events."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.simulation import SimulationService

router = APIRouter()
CHANNELS = {"tick", "quote", "candle", "status"}


@router.websocket("/ws/market")
async def market_stream(websocket: WebSocket) -> None:
    service: SimulationService = websocket.app.state.simulation
    requested_symbols = {item.upper() for item in _csv(websocket.query_params.get("symbols"))}
    requested_channels = {item.lower() for item in _csv(websocket.query_params.get("channels"))} or CHANNELS
    known_symbols = {stock.symbol for stock in service.stocks}
    if requested_symbols - known_symbols or requested_channels - CHANNELS:
        await websocket.close(code=1008, reason="Invalid symbols or channels filter")
        return
    await websocket.accept()
    queue = service.hub.subscribe()
    try:
        await websocket.send_json(
            {
                "type": "status",
                "timestamp": service.clock.current_time.isoformat(),
                "symbol": None,
                "data": service.status(),
            }
        )
        while True:
            event = await queue.get()
            if event["type"] not in requested_channels:
                continue
            if requested_symbols and event["symbol"] is not None and event["symbol"] not in requested_symbols:
                continue
            await websocket.send_json(event)
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        service.hub.unsubscribe(queue)


def _csv(value: str | None) -> set[str]:
    return {item.strip() for item in (value or "").split(",") if item.strip()}
