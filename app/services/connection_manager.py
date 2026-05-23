import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections grouped by dashboard_id."""

    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, dashboard_id: str) -> None:
        await websocket.accept()
        self._connections.setdefault(dashboard_id, []).append(websocket)
        logger.info("WS connected: dashboard=%s total=%d", dashboard_id, len(self._connections[dashboard_id]))

    def disconnect(self, websocket: WebSocket, dashboard_id: str) -> None:
        bucket = self._connections.get(dashboard_id, [])
        if websocket in bucket:
            bucket.remove(websocket)
        logger.info("WS disconnected: dashboard=%s total=%d", dashboard_id, len(bucket))

    async def broadcast(self, dashboard_id: str, message: dict) -> None:
        bucket = self._connections.get(dashboard_id, [])
        stale: list[WebSocket] = []
        for ws in bucket:
            try:
                await ws.send_json(message)
            except Exception:
                stale.append(ws)
        for ws in stale:
            bucket.remove(ws)

    def connection_count(self, dashboard_id: str) -> int:
        return len(self._connections.get(dashboard_id, []))


# Singleton shared across the FastAPI process
manager = ConnectionManager()
