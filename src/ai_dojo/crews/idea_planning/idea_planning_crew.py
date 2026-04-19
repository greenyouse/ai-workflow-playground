from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent

@CrewBase
class IdeaPlanningCrew:
    """Idea Planning crew — Takes ideas and turns them into high level project plans."""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def planner(self) -> Agent:
        return Agent(
            config=self.agents_config['planner'], 
            verbose=True,
        )

    @agent
    def planning_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['planning_researcher'], 
            verbose=True,
        )

    @agent
    def reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config['reviewer'], 
            verbose=True,
        )

    @agent
    def synthesizer(self) -> Agent:
        return Agent(
            config=self.agents_config['synthesizer'], 
            verbose=True,
        )

    @task
    def scoping_task(self) -> Task:
        return Task(
            config=self.tasks_config['scoping_task'], 
        )

    @task
    def context_gathering_task(self) -> Task:
        return Task(
            config=self.tasks_config['context_gathering_task'], 
            context=[self.scoping_task()],
        )

    @task
    def quality_review_task(self) -> Task:
        return Task(
            config=self.tasks_config['quality_review_task'], 
            context=[self.scoping_task(), self.context_gathering_task()],
        )

    @task
    def finalization_task(self) -> Task:
        return Task(
            config=self.tasks_config['finalization_task'], 
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