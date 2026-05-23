import pytest
from httpx import AsyncClient


async def _seed(client: AsyncClient, event_type: str, dashboard_id: str = "test", n: int = 1):
    for _ in range(n):
        await client.post("/events/track", json={
            "event_type": event_type,
            "dashboard_id": dashboard_id,
        })


# ---------------------------------------------------------------------------
# Funnel
# ---------------------------------------------------------------------------

async def test_funnel_empty_returns_zeros(client: AsyncClient):
    r = await client.get("/analytics/funnel?steps=page_view,signup&dashboard_id=test")
    assert r.status_code == 200
    steps = r.json()["steps"]
    assert len(steps) == 2
    assert steps[0]["count"] == 0
    assert steps[1]["count"] == 0


async def test_funnel_first_step_has_no_conversion_rate(client: AsyncClient):
    await _seed(client, "page_view", n=3)
    r = await client.get("/analytics/funnel?steps=page_view,signup&dashboard_id=test")
    steps = r.json()["steps"]
    assert steps[0]["conversion_rate"] is None


async def test_funnel_conversion_rate_calculated(client: AsyncClient):
    await _seed(client, "page_view", n=4)
    await _seed(client, "signup", n=2)
    r = await client.get("/analytics/funnel?steps=page_view,signup&dashboard_id=test")
    steps = r.json()["steps"]
    assert steps[0]["count"] == 4
    assert steps[1]["count"] == 2
    assert steps[1]["conversion_rate"] == 50.0


async def test_funnel_zero_previous_step_no_division(client: AsyncClient):
    await _seed(client, "signup", n=2)
    r = await client.get("/analytics/funnel?steps=page_view,signup&dashboard_id=test")
    steps = r.json()["steps"]
    assert steps[0]["count"] == 0
    # division by zero is avoided — conversion_rate is None when prev_count == 0
    assert steps[1]["conversion_rate"] is None


async def test_funnel_respects_dashboard_id(client: AsyncClient):
    await _seed(client, "page_view", dashboard_id="dash-A", n=5)
    await _seed(client, "page_view", dashboard_id="dash-B", n=2)
    r = await client.get("/analytics/funnel?steps=page_view&dashboard_id=dash-A")
    assert r.json()["steps"][0]["count"] == 5


async def test_funnel_metadata(client: AsyncClient):
    r = await client.get("/analytics/funnel?steps=page_view&dashboard_id=test&hours=12")
    body = r.json()
    assert body["dashboard_id"] == "test"
    assert body["period_hours"] == 12


# ---------------------------------------------------------------------------
# Insights
# ---------------------------------------------------------------------------

async def test_insights_empty(client: AsyncClient):
    r = await client.get("/analytics/insights?dashboard_id=test")
    assert r.status_code == 200
    assert r.json() == []


# ---------------------------------------------------------------------------
# Aggregates
# ---------------------------------------------------------------------------

async def test_aggregates_empty(client: AsyncClient):
    r = await client.get("/analytics/aggregates?dashboard_id=test")
    assert r.status_code == 200
    assert r.json() == []


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

async def test_health(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
