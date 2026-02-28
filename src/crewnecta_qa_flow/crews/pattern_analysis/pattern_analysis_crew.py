"""Pattern Analysis Crew — analyzes all evaluations for cross-agent patterns."""

from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent

from crewnecta_qa_flow.state.models import PatternInsightsOutput


@CrewBase
class PatternAnalysisCrew:
    """Pattern analysis crew — one agent reviews all evaluations."""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def pattern_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["pattern_analyst"],
        )

    @task
    def pattern_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["pattern_analysis_task"],
            agent=self.pattern_analyst(),
            output_pydantic=PatternInsightsOutput,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
