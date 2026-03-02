"""WebSocket connection manager — tracks connections per run_id."""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections grouped by run_id."""

    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, run_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections[run_id].append(ws)

    def disconnect(self, run_id: str, ws: WebSocket) -> None:
        conns = self._connections.get(run_id, [])
        if ws in conns:
            conns.remove(ws)
        if not conns:
            self._connections.pop(run_id, None)

    async def broadcast(self, run_id: str, message: dict[str, Any]) -> None:
        """Send a JSON message to all clients watching a given run_id."""
        dead: list[WebSocket] = []
        for ws in self._connections.get(run_id, []):
            try:
                await ws.send_text(json.dumps(message, default=str))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(run_id, ws)

    def has_clients(self, run_id: str) -> bool:
        return bool(self._connections.get(run_id))


ws_manager = ConnectionManager()
