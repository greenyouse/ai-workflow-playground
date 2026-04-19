from pathlib import Path

import yaml

from ai_dojo.crews.idea_planning.idea_planning_crew import IdeaPlanningCrew
from ai_dojo.crews.implementation_planner.implementation_planner_crew import ImplementationPlannerCrew
from ai_dojo.crews.research.research_crew import ResearchCrew
from ai_dojo.crews.tdd_implementation.tdd_implementation_crew import TddImplementationCrew
from crewai import Agent, Crew, Process, Task


CREWS_ROOT = Path(__file__).resolve().parents[1] / "src" / "ai_dojo" / "crews"


def _load_yaml(relative_path: str) -> dict:
    with (CREWS_ROOT / relative_path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _patch_configs(monkeypatch, crew_class, agents_relative_path: str, tasks_relative_path: str):
    agents_config = _load_yaml(agents_relative_path)
    tasks_config = _load_yaml(tasks_relative_path)
    monkeypatch.setattr(crew_class, "agents_config", agents_config, raising=False)
    monkeypatch.setattr(crew_class, "tasks_config", tasks_config, raising=False)
    return agents_config, tasks_config


def _assert_crew_contract(crew, expected_agent_count: int, expected_task_count: int):
    assert isinstance(crew, Crew)
    assert crew.process == Process.sequential
    assert len(crew.agents) == expected_agent_count
    assert len(crew.tasks) == expected_task_count


def _assert_agent(agent):
    assert isinstance(agent, Agent)
    assert agent.verbose is True


def _assert_task(task, expected_context_length: int = 0, expected_output_file: str | None = None):
    assert isinstance(task, Task)
    assert len(task.context) == expected_context_length
    assert task.output_file == expected_output_file


def test_research_crew_contract(monkeypatch):
    agents_config, tasks_config = _patch_configs(
        monkeypatch,
        ResearchCrew,
        "research/config/agents.yaml",
        "research/config/tasks.yaml",
    )

    assert set(agents_config) == {"researcher", "reporting_analyst"}
    assert set(tasks_config) == {"research_task", "reporting_task"}

    crew = ResearchCrew().crew()

    _assert_crew_contract(crew, expected_agent_count=2, expected_task_count=2)
    _assert_agent(ResearchCrew().researcher())
    _assert_agent(ResearchCrew().reporting_analyst())
    _assert_task(ResearchCrew().research_task())
    _assert_task(ResearchCrew().reporting_task(), expected_output_file="report.md")


def test_idea_planning_crew_contract(monkeypatch):
    agents_config, tasks_config = _patch_configs(
        monkeypatch,
        IdeaPlanningCrew,
        "idea_planning/config/agents.yaml",
        "idea_planning/config/tasks.yaml",
    )

    assert set(agents_config) == {"planner", "planning_researcher", "reviewer", "synthesizer"}
    assert set(tasks_config) == {"scoping_task", "context_gathering_task", "quality_review_task", "finalization_task"}

    crew = IdeaPlanningCrew().planning_crew()

    _assert_crew_contract(crew, expected_agent_count=4, expected_task_count=4)
    _assert_agent(IdeaPlanningCrew().planner())
    _assert_agent(IdeaPlanningCrew().planning_researcher())
    _assert_agent(IdeaPlanningCrew().reviewer())
    _assert_agent(IdeaPlanningCrew().synthesizer())

    _assert_task(IdeaPlanningCrew().scoping_task())
    _assert_task(IdeaPlanningCrew().context_gathering_task(), expected_context_length=1)
    _assert_task(IdeaPlanningCrew().quality_review_task(), expected_context_length=2)
    _assert_task(IdeaPlanningCrew().finalization_task(), expected_context_length=3)


def test_implementation_planner_crew_contract(monkeypatch):
    agents_config, tasks_config = _patch_configs(
        monkeypatch,
        ImplementationPlannerCrew,
        "implementation_planner/config/agents.yaml",
        "implementation_planner/config/tasks.yaml",
    )

    assert set(agents_config) == {"researcher", "planner", "reviewer", "synthesizer", "implementer"}
    assert set(tasks_config) == {
        "issue_analysis_task",
        "context_retrieval_task",
        "implementation_drafting_task",
        "draft_review_task",
        "final_draft_synthesis_task",
        "revise_issue_task",
    }

    crew = ImplementationPlannerCrew().implementation_planner_crew()

    _assert_crew_contract(crew, expected_agent_count=5, expected_task_count=6)
    _assert_agent(ImplementationPlannerCrew().planner())
    _assert_agent(ImplementationPlannerCrew().researcher())
    _assert_agent(ImplementationPlannerCrew().implementer())
    _assert_agent(ImplementationPlannerCrew().reviewer())
    _assert_agent(ImplementationPlannerCrew().synthesizer())

    _assert_task(ImplementationPlannerCrew().issue_analysis_task())
    _assert_task(ImplementationPlannerCrew().context_retrieval_task(), expected_context_length=1)
    _assert_task(ImplementationPlannerCrew().implementation_drafting_task(), expected_context_length=2)
    _assert_task(ImplementationPlannerCrew().draft_review_task(), expected_context_length=3)
    _assert_task(ImplementationPlannerCrew().final_draft_synthesis_task(), expected_context_length=4)
    _assert_task(
        ImplementationPlannerCrew().revise_issue_task(),
        expected_context_length=5,
        expected_output_file="implementation_draft.md",
    )


def test_tdd_implementation_crew_contract(monkeypatch):
    agents_config, tasks_config = _patch_configs(
        monkeypatch,
        TddImplementationCrew,
        "tdd_implementation/config/agents.yaml",
        "tdd_implementation/config/tasks.yaml",
    )

    assert set(agents_config) == {"tdd_planner", "repo_analyst", "test_engineer", "tdd_reviewer"}
    assert set(tasks_config) == {
        "test_scoping_task",
        "repo_mapping_task",
        "test_generation_task",
        "test_review_task",
        "test_revision_task",
        "revision_review_task",
    }

    crew = TddImplementationCrew().tdd_implementation_crew()

    _assert_crew_contract(crew, expected_agent_count=4, expected_task_count=4)
    _assert_agent(TddImplementationCrew().tdd_planner())
    _assert_agent(TddImplementationCrew().repo_analyst())
    _assert_agent(TddImplementationCrew().test_engineer())
    _assert_agent(TddImplementationCrew().tdd_reviewer())

    _assert_task(TddImplementationCrew().test_scoping_task())
    _assert_task(TddImplementationCrew().repo_mapping_task(), expected_context_length=1)
    _assert_task(TddImplementationCrew().test_generation_task(), expected_context_length=2)
    _assert_task(TddImplementationCrew().test_review_task(), expected_context_length=3)
    _assert_task(
        TddImplementationCrew().test_revision_task(),
        expected_context_length=0,
        expected_output_file="failing_tests_draft.py",
    )
    _assert_task(TddImplementationCrew().revised_test_review_task(), expected_context_length=1)
