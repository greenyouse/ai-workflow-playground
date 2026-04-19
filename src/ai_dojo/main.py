#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from ai_dojo.crews.research.research_crew import ResearchCrew
from ai_dojo.crews.idea_planning.idea_planning_crew import IdeaPlanningCrew
from ai_dojo.flows.implementation_flow import ImplementationFlow
from ai_dojo.flows.tdd_flow import TDDFlow

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.

    Research mode (default):
        run_crew
        run_crew research          # explicit

    Planning mode:
        run_crew planning <idea>   # idea can be multi-word; no quotes needed

    Implementation planner mode:
        run_crew implementation <issue>   # issue can be multi-word; no quotes needed

    TDD Implementation mode:
        run_crew tdd <implementation_plan>
    """
    if len(sys.argv) > 1 and sys.argv[1] == 'implementation':
        if len(sys.argv) < 3:
            raise Exception(
                "Implementation mode requires an issue argument.\n"
                "Usage: run_crew implementation <issue>"
            )
        issue = ' '.join(sys.argv[2:])
        inputs = {
            'issue': issue,
            'idea': issue,
            'topic': issue,
            'current_year': str(datetime.now().year),
        }
        try:
            ImplementationFlow().kickoff(inputs=inputs)
        except Exception as e:
            raise Exception(f"An error occurred while running the implementation planner crew: {e}")
    elif len(sys.argv) > 1 and sys.argv[1] == 'planning':
        if len(sys.argv) < 4:
            raise Exception(
                "Planning mode requires an idea and code path argument.\n"
                "Usage: run_crew planning <code_path> <idea>"
            )
        idea = ' '.join(sys.argv[3:])
        code_path = sys.argv[2]
        inputs = {
            'idea': idea,
            "code_path": code_path
        }
        try:
            IdeaPlanningCrew().planning_crew().kickoff(inputs=inputs)
        except Exception as e:
            raise Exception(f"An error occurred while running the planning crew: {e}")
    elif len(sys.argv) > 1 and sys.argv[1] == 'tdd':
        print("args: ", sys.argv)
        if len(sys.argv) < 4:
            raise Exception(
                "TDD Implementation mode requires a code path and implementation plan.\n"
                "Usage: run_crew tdd <code_path> <implementation_plan>"
            )
        code_path = sys.argv[2]
        implementation_plan = ' '.join(sys.argv[3:])
        inputs = {
            'implementation_plan': implementation_plan,
            'code_path': code_path,
        }
        try:
            TDDFlow().kickoff(inputs=inputs)
        except Exception as e:
            raise Exception(f"An error occurred while running the TDD implementation flow: {e}")
    else:
        inputs = {
            'topic': 'AI LLMs',
            'current_year': str(datetime.now().year),
        }
        try:
            ResearchCrew().crew().kickoff(inputs=inputs)
        except Exception as e:
            raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs",
        'current_year': str(datetime.now().year)
    }
    try:
        ResearchCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        ResearchCrew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }

    try:
        ResearchCrew().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_planning():
    """
    Run the planning crew directly.

    Usage:
        run_planning <idea>    # idea can be multi-word; no quotes needed
    """
    if len(sys.argv) < 2:
        raise Exception(
            "run_planning requires an idea argument.\n"
            "Usage: run_planning <idea>"
        )
    idea = ' '.join(sys.argv[1:])
    inputs = {
        'idea': idea,
        'current_year': str(datetime.now().year),
    }
    try:
        IdeaPlanningCrew().planning_crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the planning crew: {e}")


def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        "topic": "",
        "current_year": ""
    }

    try:
        result = ResearchCrew().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")
