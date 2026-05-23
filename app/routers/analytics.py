from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Event, EventAggregate, Insight
from app.schemas import FunnelResponse, FunnelStep, InsightResponse, AggregateResponse

router = APIRouter(prefix="/analytics")


@router.get("/funnel", response_model=FunnelResponse)
async def get_funnel(
    steps: str = Query(..., description="Comma-separated event types in funnel order, e.g. page_view,signup,purchase"),
    dashboard_id: str = Query("default"),
    hours: int = Query(24, ge=1, le=720),
    db: AsyncSession = Depends(get_db),
) -> FunnelResponse:
    event_types = [s.strip() for s in steps.split(",") if s.strip()]
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)

    funnel_steps: list[FunnelStep] = []
    prev_count: int | None = None

    for et in event_types:
        result = await db.execute(
            select(func.count(Event.id))
            .where(Event.dashboard_id == dashboard_id)
            .where(Event.event_type == et)
            .where(Event.timestamp >= since)
        )
        count: int = result.scalar_one() or 0

        conversion_rate: float | None = None
        if prev_count is not None and prev_count > 0:
            conversion_rate = round(count / prev_count * 100, 2)

        funnel_steps.append(FunnelStep(event_type=et, count=count, conversion_rate=conversion_rate))
        prev_count = count

    return FunnelResponse(steps=funnel_steps, dashboard_id=dashboard_id, period_hours=hours)


@router.get("/insights", response_model=list[InsightResponse])
async def list_insights(
    dashboard_id: str = Query("default"),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[InsightResponse]:
    result = await db.execute(
        select(Insight)
        .where(Insight.dashboard_id == dashboard_id)
        .order_by(Insight.generated_at.desc())
        .limit(limit)
    )
    return result.scalars().all()  # type: ignore[return-value]


@router.get("/aggregates", response_model=list[AggregateResponse])
async def list_aggregates(
    dashboard_id: str = Query("default"),
    hours: int = Query(24, ge=1, le=720),
    db: AsyncSession = Depends(get_db),
) -> list[AggregateResponse]:
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)
    result = await db.execute(
        select(EventAggregate)
        .where(EventAggregate.dashboard_id == dashboard_id)
        .where(EventAggregate.hour >= since)
        .order_by(EventAggregate.hour.desc())
    )
    return result.scalars().all()  # type: ignore[return-value]
