"""WebSocket endpoint for real-time flow event streaming."""

from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.ws.manager import ws_manager

router = APIRouter()


@router.websocket("/ws/flow/{run_id}")
async def flow_websocket(ws: WebSocket, run_id: str) -> None:
    """Stream real-time flow events to the client."""
    await ws_manager.connect(run_id, ws)
    try:
        while True:
            # Listen for client commands (e.g., set_verbose)
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
                # Client commands are handled client-side; we just acknowledge
                await ws.send_text(json.dumps({"type": "ack", "command": msg.get("command")}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(run_id, ws)
