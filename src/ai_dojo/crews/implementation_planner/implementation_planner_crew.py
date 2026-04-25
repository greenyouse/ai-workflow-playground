from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, task
from crewai.agents.agent_builder.base_agent import BaseAgent

@CrewBase
class ImplementationPlannerCrew:
    """Implementation planner crew — Turns an issue into a reviewable plan."""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],
            verbose=True,
        )

    @agent
    def planner(self) -> Agent:
        return Agent(
            config=self.agents_config['planner'],
            verbose=True,
        )

    @agent
    def synthesizer(self) -> Agent:
        return Agent(
            config=self.agents_config['synthesizer'],
            verbose=True,
        )

    @agent
    def implementer(self) -> Agent:
        return Agent(
            config=self.agents_config['implementer'],
            verbose=True,
        )

    @agent
    def reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config['reviewer'],
            verbose=True,
        )

    @task
    def issue_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['issue_analysis_task'],
        )

    @task
    def context_retrieval_task(self) -> Task:
        return Task(
            config=self.tasks_config['context_retrieval_task'],
            context=[self.issue_analysis_task()],
        )

    @task
    def implementation_drafting_task(self) -> Task:
        return Task(
            config=self.tasks_config['implementation_drafting_task'],
            context=[self.issue_analysis_task(), self.context_retrieval_task()],
        )

    @task
    def draft_review_task(self) -> Task:
        return Task(
            config=self.tasks_config['draft_review_task'],
        )

    @task
    def final_draft_synthesis_task(self) -> Task:
        return Task(
            config=self.tasks_config['final_draft_synthesis_task'],
            markdown=True,
        )

    @task
    def revise_issue_task(self) -> Task:
        return Task(
            config=self.tasks_config['revise_issue_task'],
        )

    def planning_crew(self) -> Crew:
        """Initial planning workflow: analyze -> retrieve -> draft."""
        return Crew(
            agents=[
                self.planner(),
                self.researcher(),
                self.implementer(),
            ],
            tasks=[
                self.issue_analysis_task(),
                self.context_retrieval_task(),
                self.implementation_drafting_task(),
            ],
            process=Process.sequential,
            verbose=True,
        )

    def review_crew(self) -> Crew:
        """Review workflow that approves or rejects the drafted plan."""
        return Crew(
            agents=[self.reviewer()],
            tasks=[self.draft_review_task()],
            process=Process.sequential,
            verbose=True,
        )

    def revision_crew(self) -> Crew:
        """Revision workflow that updates a disapproved plan."""
        return Crew(
            agents=[self.implementer()],
            tasks=[self.revise_issue_task()],
            process=Process.sequential,
            verbose=True,
        )

    def finalization_crew(self) -> Crew:
        """Finalizes the report so it can be output"""
        return Crew(
            agents=[self.synthesizer()],
            tasks=[self.final_draft_synthesis_task()],
            process=Process.sequential,
            verbose=True,
        )
