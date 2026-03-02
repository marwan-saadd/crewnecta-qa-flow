"""CrewAI event bus → WebSocket relay.

Registers handlers on crewai_event_bus to capture events and broadcast
them to WebSocket clients for real-time progress tracking.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from crewai.events import (
    BaseEventListener,
    crewai_event_bus,
    FlowStartedEvent,
    FlowFinishedEvent,
    MethodExecutionStartedEvent,
    MethodExecutionFinishedEvent,
    MethodExecutionFailedEvent,
    CrewKickoffStartedEvent,
    CrewKickoffCompletedEvent,
    AgentExecutionStartedEvent,
    AgentExecutionCompletedEvent,
    TaskStartedEvent,
    TaskCompletedEvent,
    ToolUsageStartedEvent,
    ToolUsageFinishedEvent,
    ToolUsageErrorEvent,
    LLMCallStartedEvent,
    LLMCallCompletedEvent,
)

from backend.ws.manager import ws_manager


# Module-level state for the bridge
_run_id: str | None = None
_loop: asyncio.AbstractEventLoop | None = None


def bind(run_id: str, loop: asyncio.AbstractEventLoop) -> None:
    """Bind the bridge to a specific run_id and event loop."""
    global _run_id, _loop
    _run_id = run_id
    _loop = loop


def unbind() -> None:
    global _run_id, _loop
    _run_id = None
    _loop = None


def _emit(msg_type: str, data: dict[str, Any], verbose_only: bool = False) -> None:
    if not _run_id or not _loop:
        return
    message = {
        "run_id": _run_id,
        "type": msg_type,
        "verbose_only": verbose_only,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }
    asyncio.run_coroutine_threadsafe(
        ws_manager.broadcast(_run_id, message),
        _loop,
    )


def emit_step_notification(step_name: str, status: str, summary: str | None = None) -> None:
    """Called from flow steps via _notify_step to emit custom step events."""
    _emit(f"step_{status}", {
        "method_name": step_name,
        "summary": summary,
    })


def emit_state_snapshot(state_dict: dict[str, Any]) -> None:
    """Emit a full state snapshot after a step completes."""
    _emit("state_snapshot", state_dict)


class EventBridge(BaseEventListener):
    """Captures CrewAI events and broadcasts them over WebSocket."""

    def setup_listeners(self, crewai_event_bus) -> None:
        # --- Flow lifecycle ---
        @crewai_event_bus.on(FlowStartedEvent)
        def on_flow_started(source, event):
            _emit("flow_started", {"flow_name": event.flow_name})

        @crewai_event_bus.on(FlowFinishedEvent)
        def on_flow_finished(source, event):
            _emit("flow_finished", {
                "flow_name": event.flow_name,
            })

        # --- Method / step execution ---
        @crewai_event_bus.on(MethodExecutionStartedEvent)
        def on_method_started(source, event):
            _emit("step_started", {"method_name": event.method_name})

        @crewai_event_bus.on(MethodExecutionFinishedEvent)
        def on_method_finished(source, event):
            _emit("step_finished", {"method_name": event.method_name})

        @crewai_event_bus.on(MethodExecutionFailedEvent)
        def on_method_failed(source, event):
            _emit("step_failed", {
                "method_name": event.method_name,
                "error": str(event.error) if hasattr(event, "error") else None,
            })

        # --- Crew ---
        @crewai_event_bus.on(CrewKickoffStartedEvent)
        def on_crew_started(source, event):
            _emit("crew_started", {
                "crew_name": str(getattr(event, "crew_name", None)),
            })

        @crewai_event_bus.on(CrewKickoffCompletedEvent)
        def on_crew_completed(source, event):
            _emit("crew_completed", {
                "crew_name": str(getattr(event, "crew_name", None)),
            })

        # --- Agent ---
        @crewai_event_bus.on(AgentExecutionStartedEvent)
        def on_agent_started(source, event):
            role = None
            if hasattr(event, "agent") and hasattr(event.agent, "role"):
                role = str(event.agent.role)
            elif hasattr(event, "agent_role"):
                role = str(event.agent_role)
            _emit("agent_started", {"agent_name": role})

        @crewai_event_bus.on(AgentExecutionCompletedEvent)
        def on_agent_completed(source, event):
            role = None
            if hasattr(event, "agent") and hasattr(event.agent, "role"):
                role = str(event.agent.role)
            elif hasattr(event, "agent_role"):
                role = str(event.agent_role)
            _emit("agent_completed", {"agent_name": role})

        # --- Task ---
        @crewai_event_bus.on(TaskStartedEvent)
        def on_task_started(source, event):
            desc = None
            if hasattr(event, "task") and hasattr(event.task, "description"):
                desc = str(event.task.description)[:100]
            elif hasattr(event, "task_name"):
                desc = str(event.task_name)
            _emit("task_started", {"task_description": desc})

        @crewai_event_bus.on(TaskCompletedEvent)
        def on_task_completed(source, event):
            desc = None
            if hasattr(event, "task") and hasattr(event.task, "description"):
                desc = str(event.task.description)[:100]
            elif hasattr(event, "task_name"):
                desc = str(event.task_name)
            _emit("task_completed", {"task_description": desc})

        # --- Tool ---
        @crewai_event_bus.on(ToolUsageStartedEvent)
        def on_tool_started(source, event):
            _emit("tool_started", {
                "tool_name": str(getattr(event, "tool_name", None)),
            })

        @crewai_event_bus.on(ToolUsageFinishedEvent)
        def on_tool_finished(source, event):
            _emit("tool_finished", {
                "tool_name": str(getattr(event, "tool_name", None)),
            })

        @crewai_event_bus.on(ToolUsageErrorEvent)
        def on_tool_error(source, event):
            _emit("tool_error", {
                "tool_name": str(getattr(event, "tool_name", None)),
                "error": str(getattr(event, "error", None)),
            })

        # --- LLM (verbose only) ---
        @crewai_event_bus.on(LLMCallStartedEvent)
        def on_llm_started(source, event):
            _emit("llm_call_started", {}, verbose_only=True)

        @crewai_event_bus.on(LLMCallCompletedEvent)
        def on_llm_completed(source, event):
            response_text = None
            if hasattr(event, "response") and event.response:
                response_text = str(event.response)[:500]
            _emit("llm_call_completed", {"response_preview": response_text}, verbose_only=True)


# Instantiate once — auto-registers with event bus
event_bridge = EventBridge()
