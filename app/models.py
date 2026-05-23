from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, UniqueConstraint
from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    dashboard_id = Column(String(128), nullable=False, index=True)
    event_type = Column(String(128), nullable=False, index=True)
    properties = Column(JSON, default=dict)
    user_agent = Column(String(512))
    ip = Column(String(64))
    timestamp = Column(DateTime, default=_utcnow, nullable=False, index=True)


class EventAggregate(Base):
    __tablename__ = "event_aggregates"
    __table_args__ = (
        UniqueConstraint("dashboard_id", "event_type", "hour", name="uq_aggregate"),
    )

    id = Column(Integer, primary_key=True, index=True)
    dashboard_id = Column(String(128), nullable=False, index=True)
    event_type = Column(String(128), nullable=False)
    hour = Column(DateTime, nullable=False, index=True)
    count = Column(Integer, default=0, nullable=False)


class Insight(Base):
    __tablename__ = "insights"

    id = Column(Integer, primary_key=True, index=True)
    dashboard_id = Column(String(128), nullable=False, index=True)
    content = Column(Text, nullable=False)
    generated_at = Column(DateTime, default=_utcnow, nullable=False)
    period_start = Column(DateTime)
    period_end = Column(DateTime)
