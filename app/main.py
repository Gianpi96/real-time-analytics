import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import init_db
from app.routers import events, analytics, websocket

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Real-Time Analytics API",
    description="Event tracking, WebSocket dashboards, funnel analysis and Groq-powered AI insights.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(events.router, tags=["Events"])
app.include_router(analytics.router, tags=["Analytics"])
app.include_router(websocket.router, tags=["WebSocket"])


@app.get("/health", tags=["Health"])
async def health() -> dict:
    return {"status": "ok"}
