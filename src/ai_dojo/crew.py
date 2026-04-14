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
            config=self.agents_config['researcher'], 
            verbose=True,
        )

    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['reporting_analyst'], 
            verbose=True,
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'], 
        )

    @task
    def reporting_task(self) -> Task:
        return Task(
            config=self.tasks_config['reporting_task'], 
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

    # =========================================================================
    # IMPLEMENTATION PLANNER WORKFLOW
    # =========================================================================

    @agent
    def implementer(self) -> Agent:
        return Agent(
            config=self.agents_config['implementer'], 
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
            context=[
                self.issue_analysis_task(),
                self.context_retrieval_task(),
                self.implementation_drafting_task(),
            ],
        )

    @task
    def final_draft_synthesis_task(self) -> Task:
        return Task(
            config=self.tasks_config['final_draft_synthesis_task'], 
            context=[
                self.issue_analysis_task(),
                self.context_retrieval_task(),
                self.implementation_drafting_task(),
                self.draft_review_task(),
            ],
        )

    @task
    def revise_issue_task(self) -> Task:
        return Task(
            config=self.tasks_config['revise_issue_task'],
            context=[
                self.issue_analysis_task(),
                self.context_retrieval_task(),
                self.implementation_drafting_task(),
                self.draft_review_task(),
                self.final_draft_synthesis_task(),
            ],
            output_file='implementation_draft.md',
        )

    def implementation_planner_crew(self) -> Crew:
        """Implementation planner workflow crew (analyze → retrieve → draft → review → synthesize → revise)."""
        return Crew(
            agents=[
                self.planner(),
                self.researcher(),
                self.implementer(),
                self.reviewer(),
                self.synthesizer(),
            ],
            tasks=[
                self.issue_analysis_task(),
                self.context_retrieval_task(),
                self.implementation_drafting_task(),
                self.draft_review_task(),
                self.final_draft_synthesis_task(),
                self.revise_issue_task(),
            ],
            process=Process.sequential,
            verbose=True,
        )
