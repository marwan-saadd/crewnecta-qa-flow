"""Background thread flow execution manager.

Runs the CrewAI flow in a background thread and relays events/state
snapshots to WebSocket clients via the event bridge.
"""

from __future__ import annotations

import asyncio
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from crewnecta_qa_flow.flow.qa_auditor_flow import QAAuditorFlow
from crewnecta_qa_flow.state.models import InteractionTranscript, QAAuditorState

from backend.bridge import event_bridge
from backend.ws.manager import ws_manager


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class FlowRun:
    run_id: str
    status: RunStatus = RunStatus.PENDING
    started_at: datetime | None = None
    finished_at: datetime | None = None
    state: QAAuditorState | None = None
    flow: QAAuditorFlow | None = field(default=None, repr=False)
    error: str | None = None
    thread: threading.Thread | None = field(default=None, repr=False)

    def get_live_state(self) -> QAAuditorState | None:
        """Return the current state — live from the flow if running, or final."""
        if self.flow is not None:
            try:
                return self.flow.state
            except Exception:
                pass
        return self.state


class RunManager:
    """Manages flow runs — one at a time (CrewAI event bus is a singleton)."""

    def __init__(self) -> None:
        self._runs: dict[str, FlowRun] = {}
        self._lock = threading.Lock()
        self._active_run_id: str | None = None

    def get_run(self, run_id: str) -> FlowRun | None:
        return self._runs.get(run_id)

    def is_busy(self) -> bool:
        return self._active_run_id is not None

    def start_run(
        self,
        transcripts: list[dict[str, Any]],
        loop: asyncio.AbstractEventLoop,
        campaign_name: str = "Customer Support — Q1 2026 Audit",
        evaluation_period: str = "February 2026",
    ) -> str:
        """Start a new flow run in a background thread. Returns run_id."""
        with self._lock:
            if self._active_run_id:
                raise RuntimeError("A flow is already running")

            run_id = str(uuid.uuid4())
            run = FlowRun(run_id=run_id)
            self._runs[run_id] = run
            self._active_run_id = run_id

        # Bind the event bridge to this run
        event_bridge.bind(run_id, loop)

        thread = threading.Thread(
            target=self._execute_flow,
            args=(run_id, transcripts, campaign_name, evaluation_period, loop),
            daemon=True,
        )
        run.thread = thread
        thread.start()

        return run_id

    def _execute_flow(
        self,
        run_id: str,
        transcripts: list[dict[str, Any]],
        campaign_name: str,
        evaluation_period: str,
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        """Run the flow in a background thread."""
        run = self._runs[run_id]
        run.status = RunStatus.RUNNING
        run.started_at = datetime.now(timezone.utc)

        # Notify clients
        asyncio.run_coroutine_threadsafe(
            ws_manager.broadcast(run_id, {
                "run_id": run_id,
                "type": "run_status",
                "verbose_only": False,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {"status": "running"},
            }),
            loop,
        )

        try:
            # Build initial state
            parsed_transcripts = [InteractionTranscript(**t) for t in transcripts]
            state = QAAuditorState(
                raw_transcripts=parsed_transcripts,
                campaign_name=campaign_name,
                evaluation_period=evaluation_period,
                compliance_requirements=[
                    "PCI-DSS: No card numbers read back",
                    "Call recording disclosure required",
                    "Identity verification before account changes",
                    "Terms and conditions disclosure on sales calls",
                ],
            )

            flow = QAAuditorFlow()
            flow.initial_state = state
            # Store flow reference for live state access
            run.flow = flow

            flow.kickoff()

            run.state = flow.state
            run.status = RunStatus.COMPLETED
            run.finished_at = datetime.now(timezone.utc)

            # Send final state snapshot
            state_dict = flow.state.model_dump(mode="json")
            asyncio.run_coroutine_threadsafe(
                ws_manager.broadcast(run_id, {
                    "run_id": run_id,
                    "type": "state_snapshot",
                    "verbose_only": False,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "data": state_dict,
                }),
                loop,
            )

            # Send completion
            asyncio.run_coroutine_threadsafe(
                ws_manager.broadcast(run_id, {
                    "run_id": run_id,
                    "type": "run_status",
                    "verbose_only": False,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "data": {"status": "completed"},
                }),
                loop,
            )

        except Exception as e:
            run.status = RunStatus.FAILED
            run.error = str(e)
            run.finished_at = datetime.now(timezone.utc)

            asyncio.run_coroutine_threadsafe(
                ws_manager.broadcast(run_id, {
                    "run_id": run_id,
                    "type": "run_status",
                    "verbose_only": False,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "data": {"status": "failed", "error": str(e)},
                }),
                loop,
            )

        finally:
            event_bridge.unbind()
            run.flow = None  # Release flow reference
            with self._lock:
                self._active_run_id = None


run_manager = RunManager()
