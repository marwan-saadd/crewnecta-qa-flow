"""Coaching Crew — generates a personalized coaching plan for one agent."""

import os
from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent

from crewnecta_qa_flow.state.models import CoachingPlan


def _get_google_calendar_mcp() -> list:
    """Return Google Calendar MCP config if credentials are available."""
    creds = os.getenv("GOOGLE_CALENDAR_CREDENTIALS")
    if not creds:
        return []
    try:
        from crewai.mcp import MCPServerStdio
        return [
            MCPServerStdio(
                command="npx",
                args=["-y", "@cocal/google-calendar-mcp"],
                env={"GOOGLE_CALENDAR_CREDENTIALS": creds},
            )
        ]
    except Exception:
        return []


@CrewBase
class CoachingCrew:
    """Coaching crew — one agent creates one coaching plan."""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def coaching_architect(self) -> Agent:
        mcps = _get_google_calendar_mcp()
        return Agent(
            config=self.agents_config["coaching_architect"],
            **({"mcps": mcps} if mcps else {}),
        )

    @task
    def coaching_plan_task(self) -> Task:
        return Task(
            config=self.tasks_config["coaching_plan_task"],
            agent=self.coaching_architect(),
            output_pydantic=CoachingPlan,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
