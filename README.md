# Real-Time Analytics System

Event tracking with WebSocket push, hourly aggregation via Celery, and daily AI insights powered by Groq.

## Architecture

```
Client
  │
  ├─► POST /events/track ──────────────────► FastAPI (asyncpg + PostgreSQL)
  │                                                 │
  └─► WS /ws/dashboard/{id} ◄── broadcast ──────────┘
                                                    │
                                             Redis (broker)
                                                    │
                                            Celery Worker + Beat
                                                    │
                                    ┌───────────────┴────────────────┐
                              hourly aggregate                  daily Groq call
                           EventAggregate table              Insight table (llama-3.3-70b)
```

## Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI + Uvicorn |
| Database | PostgreSQL 16 + SQLAlchemy 2 (async) |
| Async driver | asyncpg |
| Sync driver (Celery) | psycopg2 |
| Task queue | Celery 5 + Redis 7 |
| AI insights | Groq `llama-3.3-70b-versatile` |
| Containerization | Docker Compose |

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/events/track` | Track an event; broadcasts to all WS clients of the same dashboard |
| `WS` | `/ws/dashboard/{dashboard_id}` | Real-time event stream for a dashboard |
| `GET` | `/analytics/funnel` | Conversion funnel across sequential event types |
| `GET` | `/analytics/insights` | AI-generated daily insights |
| `GET` | `/analytics/aggregates` | Hourly aggregated event counts |
| `GET` | `/health` | Health check |

## Celery Schedule

| Task | Trigger | Action |
|------|---------|--------|
| `aggregate_events` | Every hour at `:00` | Writes `EventAggregate` rows per hour / event type / dashboard |
| `generate_daily_insights` | Daily at 01:00 UTC | Sends event summary to Groq, stores `Insight` row |

## Database Models

```
Event
  id, dashboard_id, event_type, properties (JSON),
  user_agent, ip, timestamp

EventAggregate
  id, dashboard_id, event_type, hour, count
  UNIQUE (dashboard_id, event_type, hour)

Insight
  id, dashboard_id, content, generated_at,
  period_start, period_end
```

## Project Structure

```
real-time-analytics/
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── app/
    ├── main.py
    ├── config.py
    ├── database.py
    ├── models.py
    ├── schemas.py
    ├── routers/
    │   ├── events.py         # POST /events/track
    │   ├── analytics.py      # GET /analytics/*
    │   └── websocket.py      # WS /ws/dashboard/{id}
    ├── services/
    │   ├── connection_manager.py
    │   └── groq_service.py
    └── tasks/
        ├── celery_app.py
        └── scheduled_tasks.py
```

## Setup

```bash
# 1. Copy and fill environment variables
copy .env.example .env

# 2. Build and start all services
docker compose up --build
```

API available at `http://localhost:8000` — interactive docs at `http://localhost:8000/docs`.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Async PostgreSQL URL (asyncpg) |
| `SYNC_DATABASE_URL` | Sync PostgreSQL URL (psycopg2, used by Celery) |
| `REDIS_URL` | Redis broker URL |
| `GROQ_API_KEY` | API key from [console.groq.com](https://console.groq.com) |

## Git

```bash
git init
git add .
git commit -m "feat: initial real-time analytics system"
git remote add origin https://github.com/<user>/<repo>.git
git branch -M main
git push -u origin main
```
