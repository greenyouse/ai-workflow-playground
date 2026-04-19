import importlib


def test_import_crews():
    modules = [
        "ai_dojo.crews.research.research_crew",
        "ai_dojo.crews.idea_planning.idea_planning_crew",
        "ai_dojo.crews.implementation_planner.implementation_planner_crew",
    ]
    for m in modules:
        mod = importlib.import_module(m)
        assert mod is not None


def test_classes_and_methods():
    from ai_dojo.crews.research.research_crew import ResearchCrew
    from ai_dojo.crews.idea_planning.idea_planning_crew import IdeaPlanningCrew
    from ai_dojo.crews.implementation_planner.implementation_planner_crew import ImplementationPlannerCrew

    rc = ResearchCrew()
    assert hasattr(rc, "crew")

    ipc = IdeaPlanningCrew()
    assert hasattr(ipc, "planning_crew")

    ipc2 = ImplementationPlannerCrew()
    assert hasattr(ipc2, "implementation_planner_crew")
