"""WebSocket transports for live market events and stored-session replay."""

import asyncio
from contextlib import suppress

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


@router.websocket("/ws/replay/{session_id}")
async def replay_stream(websocket: WebSocket, session_id: int) -> None:
    service: SimulationService = websocket.app.state.simulation
    session = await service.storage.get_session(session_id)
    symbols = {item.upper() for item in _csv(websocket.query_params.get("symbols"))}
    known_symbols = {stock.symbol for stock in service.stocks}
    try:
        speed = float(websocket.query_params.get("speed", "1"))
    except ValueError:
        speed = 0
    if session is None or symbols - known_symbols or not service.replay_min_speed <= speed <= service.replay_max_speed:
        await websocket.close(code=1008, reason="Invalid session, symbols, or speed")
        return
    await websocket.accept()
    state = {"paused": False, "stopped": False, "speed": speed}

    async def controls() -> None:
        while True:
            message = await websocket.receive_json()
            action = message.get("action")
            if action == "pause": state["paused"] = True
            elif action == "resume": state["paused"] = False
            elif action == "stop": state["stopped"] = True; return
            elif action == "set_speed" and isinstance(message.get("speed"), (int, float)) and service.replay_min_speed <= message["speed"] <= service.replay_max_speed:
                state["speed"] = float(message["speed"])
            else:
                await websocket.send_json({"type": "replay_error", "timestamp": service.clock.current_time.isoformat(),
                    "symbol": None, "data": {"detail": "Invalid replay control"}})

    control_task = asyncio.create_task(controls())
    cursor, previous = 0, None
    try:
        await websocket.send_json({"type": "replay_start", "timestamp": session.started_at.isoformat(),
            "symbol": None, "data": {"session_id": session_id, "complete": session.replay_complete}})
        while not state["stopped"]:
            while state["paused"] and not state["stopped"]:
                await asyncio.sleep(.05)
            rows = await service.storage.read_ticks(session_id, symbol=None, after_sequence=cursor, limit=500)
            if not rows: break
            cursor = rows[-1].sequence_number
            visible_rows = [row for row in rows if not symbols or row.symbol in symbols]
            for tick in visible_rows:
                if state["stopped"]: break
                while state["paused"] and not state["stopped"]: await asyncio.sleep(.05)
                if previous is not None:
                    await asyncio.sleep(min(max((tick.timestamp-previous).total_seconds()/state["speed"], 0), 2))
                await websocket.send_json({"type": "tick", "timestamp": tick.timestamp.isoformat(),
                    "symbol": tick.symbol, "data": tick.model_dump(mode="json")})
                previous = tick.timestamp
        await websocket.send_json({"type": "replay_complete", "timestamp": (previous or session.started_at).isoformat(),
            "symbol": None, "data": {"session_id": session_id, "last_sequence": cursor}})
    except (WebSocketDisconnect, RuntimeError, asyncio.CancelledError):
        pass
    finally:
        control_task.cancel()
        with suppress(asyncio.CancelledError, WebSocketDisconnect): await control_task
