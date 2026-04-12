from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent


@CrewBase
class AiDojo():
    """AiDojo crew — supports a research/report workflow and a planning workflow."""

    agents: list[BaseAgent]
    tasks: list[Task]

    # =========================================================================
    # RESEARCH WORKFLOW
    # =========================================================================

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],  # type: ignore[index]
            verbose=True,
        )

    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['reporting_analyst'],  # type: ignore[index]
            verbose=True,
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'],  # type: ignore[index]
        )

    @task
    def reporting_task(self) -> Task:
        return Task(
            config=self.tasks_config['reporting_task'],  # type: ignore[index]
            output_file='report.md',
        )

    @crew
    def crew(self) -> Crew:
        """Research and reporting crew (default)."""
        return Crew(
            agents=[self.researcher(), self.reporting_analyst()],
            tasks=[self.research_task(), self.reporting_task()],
            process=Process.sequential,
            verbose=True,
        )

    # =========================================================================
    # PLANNING WORKFLOW
    # =========================================================================

    @agent
    def planner(self) -> Agent:
        return Agent(
            config=self.agents_config['planner'],  # type: ignore[index]
            verbose=True,
        )

    @agent
    def planning_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['planning_researcher'],  # type: ignore[index]
            verbose=True,
        )

    @agent
    def reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config['reviewer'],  # type: ignore[index]
            verbose=True,
        )

    @agent
    def synthesizer(self) -> Agent:
        return Agent(
            config=self.agents_config['synthesizer'],  # type: ignore[index]
            verbose=True,
        )

    @task
    def scoping_task(self) -> Task:
        return Task(
            config=self.tasks_config['scoping_task'],  # type: ignore[index]
        )

    @task
    def context_gathering_task(self) -> Task:
        return Task(
            config=self.tasks_config['context_gathering_task'],  # type: ignore[index]
            context=[self.scoping_task()],
        )

    @task
    def quality_review_task(self) -> Task:
        return Task(
            config=self.tasks_config['quality_review_task'],  # type: ignore[index]
            context=[self.scoping_task(), self.context_gathering_task()],
        )

    @task
    def finalization_task(self) -> Task:
        return Task(
            config=self.tasks_config['finalization_task'],  # type: ignore[index]
            context=[
                self.scoping_task(),
                self.context_gathering_task(),
                self.quality_review_task(),
            ],
        )

    def planning_crew(self) -> Crew:
        """Planning workflow crew (scoping → research → review → finalize)."""
        return Crew(
            agents=[
                self.planner(),
                self.planning_researcher(),
                self.reviewer(),
                self.synthesizer(),
            ],
            tasks=[
                self.scoping_task(),
                self.context_gathering_task(),
                self.quality_review_task(),
                self.finalization_task(),
            ],
            process=Process.sequential,
            verbose=True,
        )
