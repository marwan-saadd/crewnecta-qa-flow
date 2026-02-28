"""QA Analysis Crew — compliance auditor + quality evaluator for one transcript."""

from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent

from crewnecta_qa_flow.tools import compliance_pattern_matcher, scorecard_calculator
from crewnecta_qa_flow.state.models import QAEvaluationOutput


@CrewBase
class QAAnalysisCrew:
    """QA analysis crew — two agents analyze one transcript sequentially."""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def compliance_auditor(self) -> Agent:
        return Agent(
            config=self.agents_config["compliance_auditor"],
            tools=[compliance_pattern_matcher],
        )

    @agent
    def quality_evaluator(self) -> Agent:
        return Agent(
            config=self.agents_config["quality_evaluator"],
            tools=[scorecard_calculator],
        )

    @task
    def compliance_audit_task(self) -> Task:
        return Task(
            config=self.tasks_config["compliance_audit_task"],
            agent=self.compliance_auditor(),
        )

    @task
    def quality_evaluation_task(self) -> Task:
        return Task(
            config=self.tasks_config["quality_evaluation_task"],
            agent=self.quality_evaluator(),
            context=[self.compliance_audit_task()],
            output_pydantic=QAEvaluationOutput,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
