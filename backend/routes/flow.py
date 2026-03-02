"""Flow routes — start runs and query state."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.bridge.run_manager import run_manager

router = APIRouter(prefix="/api/flow", tags=["flow"])


class StartFlowRequest(BaseModel):
    use_demo: bool = False
    transcripts: list[dict[str, Any]] | None = None
    campaign_name: str = "Customer Support — Q1 2026 Audit"
    evaluation_period: str = "February 2026"


class StartFlowResponse(BaseModel):
    run_id: str


@router.post("/start", response_model=StartFlowResponse)
async def start_flow(req: StartFlowRequest) -> StartFlowResponse:
    """Start a new QA audit flow run."""
    if run_manager.is_busy():
        raise HTTPException(status_code=409, detail="A flow is already running")

    transcripts: list[dict[str, Any]]

    if req.use_demo:
        import json
        from backend.config import MOCK_TRANSCRIPTS_PATH

        if not MOCK_TRANSCRIPTS_PATH.exists():
            raise HTTPException(status_code=404, detail="Demo transcript file not found")
        with open(MOCK_TRANSCRIPTS_PATH) as f:
            data = json.load(f)
        transcripts = data.get("transcripts", data) if isinstance(data, dict) else data
    elif req.transcripts:
        transcripts = req.transcripts
    else:
        raise HTTPException(status_code=400, detail="Provide transcripts or set use_demo=true")

    loop = asyncio.get_running_loop()
    run_id = run_manager.start_run(
        transcripts=transcripts,
        loop=loop,
        campaign_name=req.campaign_name,
        evaluation_period=req.evaluation_period,
    )
    return StartFlowResponse(run_id=run_id)


@router.get("/{run_id}/state")
async def get_flow_state(run_id: str) -> dict:
    """Return the current state snapshot for a run."""
    run = run_manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    result: dict[str, Any] = {
        "run_id": run.run_id,
        "status": run.status.value,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "error": run.error,
    }

    live_state = run.get_live_state()
    if live_state:
        try:
            result["state"] = live_state.model_dump(mode="json")
        except Exception:
            result["state"] = None
    else:
        result["state"] = None

    return result
