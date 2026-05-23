from unittest.mock import patch, AsyncMock
from starlette.testclient import TestClient
from app.main import app

# init_db() tries to reach the Docker PostgreSQL host — not available in local tests.
# WebSocket tests don't use the DB, so we patch it for the entire TestClient lifespan.
_PATCH = lambda: patch("app.main.init_db", new_callable=AsyncMock)


def test_websocket_connect_sends_confirmation():
    with _PATCH():
        with TestClient(app) as tc:
            with tc.websocket_connect("/ws/dashboard/test-dash") as ws:
                data = ws.receive_json()
                assert data["type"] == "connected"
                assert data["dashboard_id"] == "test-dash"
                assert "clients" in data


def test_websocket_ping_pong():
    with _PATCH():
        with TestClient(app) as tc:
            with tc.websocket_connect("/ws/dashboard/test-dash") as ws:
                ws.receive_json()  # consume the connected message
                ws.send_text("ping")
                assert ws.receive_text() == "pong"


def test_websocket_multiple_clients_same_dashboard():
    with _PATCH():
        with TestClient(app) as tc:
            with tc.websocket_connect("/ws/dashboard/shared") as ws1:
                d1 = ws1.receive_json()
                assert d1["clients"] == 1
                with tc.websocket_connect("/ws/dashboard/shared") as ws2:
                    d2 = ws2.receive_json()
                    assert d2["clients"] == 2
