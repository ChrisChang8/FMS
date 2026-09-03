from fastapi.testclient import TestClient

from app.main import create_app


def test_dashboard_and_market_endpoints() -> None:
    with TestClient(create_app()) as client:
        assert "FMS Simulator" in client.get("/").text
        assert "About liquidity" in client.get("/").text
        assert "About bid" in client.get("/").text
        assert "About last price" in client.get("/").text
        assert "Volatility spike" in client.get("/").text
        assert "PRICE (USD)" in client.get("/static/app.js").text
        assert "SIMULATED TIME" in client.get("/static/app.js").text
        assert "aria-expanded" in client.get("/static/app.js").text
        assert client.get("/static/app.js").status_code == 200
        stocks = client.get("/stocks").json()
        assert len(stocks) == 10
        assert client.get("/simulation/status").json()["running"] is False
        assert client.post("/simulation/start").json()["running"] is True
        assert client.post("/simulation/pause").json()["running"] is False
        assert client.get("/ticks/AAPL").json() == []
        assert client.get("/candles/AAPL?interval=1s").json() == []
        assert client.get("/ticks/NOPE").status_code == 404
        assert client.get("/candles/AAPL?interval=5m").status_code == 422
        assert client.get("/ticks/AAPL?limit=0").status_code == 422


def test_factor_controls_and_generated_market_data() -> None:
    with TestClient(create_app()) as client:
        service = client.app.state.simulation
        response = client.patch("/simulation/stocks/AAPL/factors", json={
            "liquidity": 0.8, "volume_multiplier": 2, "volatility_multiplier": 1.5,
            "behavior_type": "uptrend", "behavior_strength": 0.7,
        })
        assert response.status_code == 200
        assert response.json()["liquidity"] == 0.8
        client.portal.call(service.step_once)
        assert client.get("/quotes/AAPL").status_code == 200
        assert len(client.get("/ticks/AAPL").json()) == 1
        assert len(client.get("/candles/AAPL?interval=1s").json()) == 1
        assert client.patch("/simulation/stocks/AAPL/factors", json={"liquidity": 9}).status_code == 422
        client.post("/simulation/reset")
        assert client.get("/ticks/AAPL").json() == []


def test_websocket_filters_and_envelope() -> None:
    with TestClient(create_app()) as client:
        service = client.app.state.simulation
        with client.websocket_connect("/ws/market?symbols=AAPL&channels=tick") as websocket:
            initial = websocket.receive_json()
            assert initial["type"] == "status"
            client.portal.call(service.step_once)
            event = websocket.receive_json()
            assert event["type"] == "tick"
            assert event["symbol"] == "AAPL"
            assert set(event) == {"type", "timestamp", "symbol", "data"}
