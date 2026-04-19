from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, task
from crewai.agents.agent_builder.base_agent import BaseAgent

@CrewBase
class TddImplementationCrew():
    """TDD Implementation Crew - takes an implementation plan and generates TDD tests for the implementation."""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"


    @agent
    def tdd_planner(self) -> Agent:
        return Agent(
            config=self.agents_config['tdd_planner'],
            verbose=True
        )

    @agent
    def repo_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['repo_analyst'],
            verbose=True
        )

    @agent
    def test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['test_engineer'],
            verbose=True
        )

    @agent
    def tdd_reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config['tdd_reviewer'],
            # reasoning=True,
            verbose=True
        )

    @task
    def test_scoping_task(self) -> Task:
        return Task(config=self.tasks_config['test_scoping_task'])

    @task
    def repo_mapping_task(self) -> Task:
        return Task(
            config=self.tasks_config['repo_mapping_task'],
            context=[self.test_scoping_task()],
        )

    @task
    def test_generation_task(self) -> Task:
        return Task(
            config=self.tasks_config['test_generation_task'],
            context=[self.test_scoping_task(), self.repo_mapping_task()],
        )

    @task
    def test_review_task(self) -> Task:
        return Task(
            config=self.tasks_config['test_review_task'],
            context=[
                self.test_scoping_task(),
                self.repo_mapping_task(),
                self.test_generation_task(),
            ],
        )

    def tdd_implementation_crew(self) -> Crew:
        """TDD Implementation Crew (scope -> repo mapping -> test generation -> test review)"""
        return Crew(
            agents=[
                self.tdd_planner(),
                self.repo_analyst(),
                self.test_engineer(),
                self.tdd_reviewer(),
            ],
            tasks=[
                self.test_scoping_task(),
                self.repo_mapping_task(),
                self.test_generation_task(),
                self.test_review_task(),
            ],
            process=Process.sequential,
            verbose=True,
        )

    # =========================================================================
    # TDD Revision Crew
    # =========================================================================

    @task
    def test_revision_task(self) -> Task:
        return Task(
            config=self.tasks_config['test_revision_task'],
            output_file='failing_tests_draft.py',
        )

    @task
    def revised_test_review_task(self) -> Task:
        return Task(
            config=self.tasks_config['revision_review_task'],
            context=[self.test_revision_task()],
        )

    def tdd_revision_crew(self) -> Crew:
        return Crew(
        agents=[
            self.test_engineer(),
            self.tdd_reviewer(),
        ],
        tasks=[
            self.test_revision_task(),
            self.revised_test_review_task(),
        ],
        process=Process.sequential,
        verbose=True,
    )