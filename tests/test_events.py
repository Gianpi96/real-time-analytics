import pytest
from httpx import AsyncClient


async def test_track_event_returns_201(client: AsyncClient):
    response = await client.post("/events/track", json={
        "event_type": "page_view",
        "dashboard_id": "test",
        "properties": {"url": "/home"},
    })
    assert response.status_code == 201
    data = response.json()
    assert data["event_type"] == "page_view"
    assert data["dashboard_id"] == "test"
    assert data["id"] == 1


async def test_track_event_default_dashboard(client: AsyncClient):
    response = await client.post("/events/track", json={"event_type": "click"})
    assert response.status_code == 201
    assert response.json()["dashboard_id"] == "default"


async def test_track_event_properties_stored(client: AsyncClient):
    props = {"key": "value", "count": 42}
    response = await client.post("/events/track", json={
        "event_type": "custom",
        "properties": props,
    })
    assert response.status_code == 201
    assert response.json()["properties"] == props


async def test_track_event_missing_type_returns_422(client: AsyncClient):
    response = await client.post("/events/track", json={"dashboard_id": "test"})
    assert response.status_code == 422


async def test_track_event_auto_timestamp(client: AsyncClient):
    response = await client.post("/events/track", json={"event_type": "login"})
    assert response.status_code == 201
    assert response.json()["timestamp"] is not None


async def test_track_multiple_events_sequential_ids(client: AsyncClient):
    for i in range(3):
        r = await client.post("/events/track", json={"event_type": f"event_{i}"})
        assert r.json()["id"] == i + 1
