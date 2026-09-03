import time

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.simulation import SimulationService
from app.storage import MemorySimulationStorage


class SlowMemoryStorage(MemorySimulationStorage):
    async def persist_batch(self, batch) -> None:
        import asyncio
        await asyncio.sleep(0.3)
        await super().persist_batch(batch)


def test_live_generation_does_not_wait_for_storage() -> None:
    storage = SlowMemoryStorage()
    service = SimulationService(storage=storage, persistence_enabled=True)

    async def exercise() -> None:
        await service.startup()
        started = time.monotonic()
        ticks = await service.step_once()
        elapsed = time.monotonic() - started
        assert len(ticks) == 10
        assert elapsed < 0.2
        assert service.status()["queue_depth"] >= 0
        await service.pause()
        session = await storage.get_session(service.session.id)
        assert session is not None
        assert session.tick_count == 10
        await service.shutdown()

    import asyncio
    asyncio.run(exercise())


def test_sessions_history_and_replay_interfaces() -> None:
    with TestClient(create_app()) as client:
        service = client.app.state.simulation
        for _ in range(5):
            client.portal.call(service.step_once)
        paused = client.post("/simulation/pause").json()
        session_id = paused["session_id"]

        sessions = client.get("/simulation/sessions").json()
        assert sessions[0]["id"] == session_id
        assert sessions[0]["tick_count"] == 50
        assert sessions[0]["replay_complete"] is False

        ticks = client.get(
            f"/simulation/sessions/{session_id}/ticks?symbol=AAPL&after_sequence=0&limit=2"
        ).json()
        assert len(ticks) == 2
        assert ticks[0]["symbol"] == "AAPL"
        assert ticks[0]["sequence_number"] < ticks[1]["sequence_number"]

        candles = client.get(
            f"/simulation/sessions/{session_id}/candles?symbol=AAPL&interval=1s"
        ).json()
        assert candles

        with client.websocket_connect(f"/ws/replay/{session_id}?symbols=AAPL&speed=20") as websocket:
            assert websocket.receive_json()["type"] == "replay_start"
            event = websocket.receive_json()
            assert event["type"] == "tick"
            assert event["symbol"] == "AAPL"


def test_history_validation_and_unknown_session() -> None:
    with TestClient(create_app()) as client:
        assert client.get("/simulation/sessions/999").status_code == 404
        assert client.get("/simulation/sessions/999/ticks").status_code == 404
        client.portal.call(client.app.state.simulation.step_once)
        client.post("/simulation/pause")
        session_id = client.get("/simulation/sessions").json()[0]["id"]
        assert client.get(f"/simulation/sessions/{session_id}/ticks?symbol=NOPE").status_code == 404
        assert client.get(f"/simulation/sessions/{session_id}/candles?interval=5m").status_code == 422
