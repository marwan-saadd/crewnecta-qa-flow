"""Transcript routes — demo data endpoint."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from backend.config import MOCK_TRANSCRIPTS_PATH

router = APIRouter(prefix="/api/transcripts", tags=["transcripts"])


@router.get("/demo")
async def get_demo_transcripts() -> dict:
    """Return demo transcripts from mock_transcripts.json."""
    if not MOCK_TRANSCRIPTS_PATH.exists():
        raise HTTPException(status_code=404, detail="Demo transcript file not found")

    with open(MOCK_TRANSCRIPTS_PATH) as f:
        data = json.load(f)

    transcripts = data.get("transcripts", data) if isinstance(data, dict) else data
    return {"transcripts": transcripts, "count": len(transcripts)}
