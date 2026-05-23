from __future__ import annotations
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    event_type: str = Field(..., min_length=1, max_length=128)
    properties: dict[str, Any] = Field(default_factory=dict)
    user_agent: str | None = None
    ip: str | None = None
    dashboard_id: str = Field(default="default", max_length=128)


class EventResponse(BaseModel):
    id: int
    event_type: str
    properties: dict[str, Any]
    user_agent: str | None
    ip: str | None
    timestamp: datetime
    dashboard_id: str

    model_config = {"from_attributes": True}


class FunnelStep(BaseModel):
    event_type: str
    count: int
    conversion_rate: float | None = Field(None, description="% of previous step that reached this step")


class FunnelResponse(BaseModel):
    steps: list[FunnelStep]
    dashboard_id: str
    period_hours: int


class InsightResponse(BaseModel):
    id: int
    dashboard_id: str
    content: str
    generated_at: datetime
    period_start: datetime | None
    period_end: datetime | None

    model_config = {"from_attributes": True}


class AggregateResponse(BaseModel):
    hour: datetime
    event_type: str
    count: int
    dashboard_id: str

    model_config = {"from_attributes": True}
