"""Risk Scoring Crew — scores a single transcript for review priority."""

import os
from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent

from crewnecta_qa_flow.tools import keyword_red_flag_scanner
from crewnecta_qa_flow.state.models import RiskScoreOutput


def _get_google_sheets_mcp() -> list:
    """Return Google Sheets MCP config if credentials are available."""
    creds = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    if not creds:
        return []
    try:
        from crewai.mcp import MCPServerStdio
        return [
            MCPServerStdio(
                command="npx",
                args=["-y", "@anthropic/mcp-google-sheets"],
                env={"GOOGLE_SHEETS_CREDENTIALS": creds},
            )
        ]
    except Exception:
        return []


@CrewBase
class RiskScoringCrew:
    """Risk scoring crew — one agent scores one transcript."""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def risk_scorer(self) -> Agent:
        mcps = _get_google_sheets_mcp()
        return Agent(
            config=self.agents_config["risk_scorer"],
            tools=[keyword_red_flag_scanner],
            **({"mcps": mcps} if mcps else {}),
        )

    @task
    def risk_scoring_task(self) -> Task:
        return Task(
            config=self.tasks_config["risk_scoring_task"],
            agent=self.risk_scorer(),
            output_pydantic=RiskScoreOutput,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
