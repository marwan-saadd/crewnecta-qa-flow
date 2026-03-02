"""FastAPI application — entry point for the backend server."""

from __future__ import annotations

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import CORS_ORIGINS

# Load .env before anything else
load_dotenv()

# Import event bridge so it registers listeners on import
import backend.bridge.event_bridge  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="CrewNecta QA Flow API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
from backend.routes.flow import router as flow_router
from backend.routes.transcripts import router as transcripts_router
from backend.ws.handler import router as ws_router

app.include_router(flow_router)
app.include_router(transcripts_router)
app.include_router(ws_router)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}
