import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.connection_manager import manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws/dashboard/{dashboard_id}")
async def dashboard_ws(websocket: WebSocket, dashboard_id: str) -> None:
    await manager.connect(websocket, dashboard_id)
    try:
        await websocket.send_json({
            "type": "connected",
            "dashboard_id": dashboard_id,
            "clients": manager.connection_count(dashboard_id),
        })
        while True:
            # Keep alive — client may send pings or commands
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, dashboard_id)
        logger.info("Client disconnected from dashboard %s", dashboard_id)
