from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Event
from app.schemas import EventCreate, EventResponse
from app.services.connection_manager import manager

router = APIRouter()


@router.post("/events/track", response_model=EventResponse, status_code=201)
async def track_event(
    payload: EventCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> EventResponse:
    ip = payload.ip or (request.client.host if request.client else "unknown")
    user_agent = payload.user_agent or request.headers.get("user-agent", "unknown")

    event = Event(
        dashboard_id=payload.dashboard_id,
        event_type=payload.event_type,
        properties=payload.properties,
        user_agent=user_agent,
        ip=ip,
        timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    await manager.broadcast(
        payload.dashboard_id,
        {
            "type": "new_event",
            "data": {
                "id": event.id,
                "event_type": event.event_type,
                "properties": event.properties,
                "timestamp": event.timestamp.isoformat(),
                "dashboard_id": event.dashboard_id,
            },
        },
    )

    return event  # type: ignore[return-value]
