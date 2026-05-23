"""
Celery tasks:
  - aggregate_events   : runs hourly, writes EventAggregate rows
  - generate_daily_insights : runs daily, calls Groq and writes Insight rows
"""
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from app.tasks.celery_app import celery_app
from app.config import settings
from app.models import Event, EventAggregate, Insight
from app.services.groq_service import generate_insight_sync

logger = logging.getLogger(__name__)

# Synchronous engine — Celery workers are not async
_engine = create_engine(settings.sync_database_url, pool_pre_ping=True)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ---------------------------------------------------------------------------
# Hourly aggregation
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def aggregate_events(self, hour_offset: int = 1) -> str:
    """Aggregate events. hour_offset=1 means previous hour (production default)."""
    now = _utcnow()
    hour_start = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=hour_offset)
    hour_end = hour_start + timedelta(hours=1)

    try:
        with Session(_engine) as db:
            rows = db.execute(
                select(
                    Event.event_type,
                    Event.dashboard_id,
                    func.count(Event.id).label("cnt"),
                )
                .where(Event.timestamp >= hour_start)
                .where(Event.timestamp < hour_end)
                .group_by(Event.event_type, Event.dashboard_id)
            ).all()

            for row in rows:
                existing = db.execute(
                    select(EventAggregate).where(
                        EventAggregate.event_type == row.event_type,
                        EventAggregate.dashboard_id == row.dashboard_id,
                        EventAggregate.hour == hour_start,
                    )
                ).scalar_one_or_none()

                if existing:
                    existing.count = row.cnt
                else:
                    db.add(EventAggregate(
                        event_type=row.event_type,
                        dashboard_id=row.dashboard_id,
                        hour=hour_start,
                        count=row.cnt,
                    ))

            db.commit()
            msg = f"Aggregated {len(rows)} event-type rows for {hour_start.isoformat()}"
            logger.info(msg)
            return msg

    except Exception as exc:
        logger.exception("aggregate_events failed")
        raise self.retry(exc=exc)


# ---------------------------------------------------------------------------
# Daily insight generation via Groq
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def generate_daily_insights(self, day_offset: int = 1) -> str:
    """Generate insights. day_offset=1 means yesterday (production default)."""
    now = _utcnow()
    day_start = (now - timedelta(days=day_offset)).replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)

    try:
        with Session(_engine) as db:
            dashboard_ids = [
                row[0]
                for row in db.execute(
                    select(Event.dashboard_id)
                    .where(Event.timestamp >= day_start)
                    .where(Event.timestamp < day_end)
                    .distinct()
                ).all()
            ]

            generated = 0
            for dashboard_id in dashboard_ids:
                summary = _build_summary(db, dashboard_id, day_start, day_end)
                if not summary:
                    continue

                insight_text = generate_insight_sync(summary)

                db.add(Insight(
                    dashboard_id=dashboard_id,
                    content=insight_text,
                    generated_at=now,
                    period_start=day_start,
                    period_end=day_end,
                ))
                generated += 1

            db.commit()
            msg = f"Generated {generated} insights for {day_start.date()}"
            logger.info(msg)
            return msg

    except Exception as exc:
        logger.exception("generate_daily_insights failed")
        raise self.retry(exc=exc)


def _build_summary(db: Session, dashboard_id: str, day_start: datetime, day_end: datetime) -> str:
    """Build a human-readable text summary to send to Groq."""
    hourly = db.execute(
        select(EventAggregate.hour, EventAggregate.event_type, EventAggregate.count)
        .where(EventAggregate.dashboard_id == dashboard_id)
        .where(EventAggregate.hour >= day_start)
        .where(EventAggregate.hour < day_end)
        .order_by(EventAggregate.hour)
    ).all()

    lines = [
        f"Analytics Summary — Dashboard: {dashboard_id}",
        f"Date: {day_start.date()}",
        "",
    ]

    if hourly:
        lines.append("Hourly breakdown:")
        for row in hourly:
            lines.append(f"  {row.hour.strftime('%H:00')}  {row.event_type}: {row.count}")
    else:
        # Fall back to raw event totals
        totals = db.execute(
            select(Event.event_type, func.count(Event.id).label("cnt"))
            .where(Event.dashboard_id == dashboard_id)
            .where(Event.timestamp >= day_start)
            .where(Event.timestamp < day_end)
            .group_by(Event.event_type)
        ).all()
        if not totals:
            return ""
        lines.append("Event totals (no hourly aggregates yet):")
        for row in totals:
            lines.append(f"  {row.event_type}: {row.cnt}")

    return "\n".join(lines)
