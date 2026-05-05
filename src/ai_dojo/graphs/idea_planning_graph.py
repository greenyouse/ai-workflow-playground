"""
Takes an idea and translates it into an implementation plan.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from pydantic import BaseModel, field_validator

from langchain.agents import create_agent
from langgraph.graph import END, START, StateGraph
from ai_dojo.utils.repo_context_collector import RepoContextCollector


class IdeaPlanningState(BaseModel):
    idea: str
    code_path: str = ""
    scoping_brief: str = ""
    research_summary: str = ""
    review_report: str = ""
    project_plan: str = ""
    project_plan_path: str = "project_plan.md"
    repo_context: str = ""
    is_context_truncated: bool = False
    collected_files: str = ""


def _llm():
    return create_agent(model="ollama:gemma4")


def scoping_node(state: IdeaPlanningState) -> IdeaPlanningState:
    """Replacement for planner + scoping_task."""
    idea = state.idea

    prompt = f"""
You are a Project Strategy Lead.

Goal:
Analyze the idea and produce a bounded, realistic implementation plan.

Backstory:
You are an expert at project scoping and task decomposition. You turn vague
ideas into manageable plans, identify missing information, and avoid
overbuilding.

Task:
Analyze the initial idea: {idea}.

Define the likely problem statement, propose a bounded MVP scope, identify
assumptions and unknowns, and list the technical areas that require further
research before planning.

Expected output:
A structured scoping brief containing:
- problem statement
- proposed MVP scope
- non-goals
- assumptions
- open questions
- prioritized research areas
""".strip()

    messages = [{"role": "user", "content": prompt}]
    response = _llm().invoke({"messages": messages})
    last_message = response["messages"][-1]
    return {"scoping_brief": last_message.content}


def context_gathering_node(state: IdeaPlanningState) -> IdeaPlanningState:
    """Replacement for planning_researcher + context_gathering_task."""
    idea = state.idea
    code_path = state.code_path

    if not code_path:
        return {
            "repo_context": "No repository context provided.",
            "collected_files": "",
            "is_context_truncated": False,
        }

    repo_ctx = RepoContextCollector().collect(code_path, issue=idea)
    return {
        "repo_context": repo_ctx.content,
        "collected_files": repo_ctx.file_list,
        "is_context_truncated": repo_ctx.is_truncated,
    }

def quality_review_node(state: IdeaPlanningState) -> IdeaPlanningState:
    """Replacement for reviewer + quality_review_task."""
    scoping_brief = state.scoping_brief
    collected_files = state.collected_files
    repo_context = state.repo_context

    prompt = f"""
You are a Technical Quality Critic.

Goal:
Evaluate the current plan for logic flaws, hidden risks, missing criteria,
and unsupported assumptions.

Backstory:
You are a rigorous reviewer who stress-tests plans before implementation.
You look for ambiguity, unrealistic scope, missing edge cases, and weak
reasoning, and you suggest concrete corrections.

Scoping brief:
{scoping_brief}

Collected files:
{collected_files}

Repository context:
{repo_context}

Task:
Review the scoping brief and research summary together. Identify logic flaws,
unsupported assumptions, scope risks, missing decision criteria, unresolved
unknowns, and any weak or missing evidence. Suggest concrete corrections where
needed.

Expected output:
A review report containing:
- critiques
- major risks
- unsupported assumptions
- missing information
- recommended corrections to improve the final plan
""".strip()

    messages = [{"role": "user", "content": prompt}]
    response = _llm().invoke({"messages": messages})
    last_message = response["messages"][-1]
    return {"review_report": last_message.content}


def finalization_node(state: IdeaPlanningState) -> IdeaPlanningState:
    """Replacement for synthesizer + finalization_task."""
    idea = state.idea
    scoping_brief = state.scoping_brief
    review_report = state.review_report

    prompt = f"""
You are a Documentation Specialist.

Goal:
Convert validated planning materials into clear, structured Markdown
documentation for human use.

Backstory:
You turn research, planning, and review outputs into polished documentation.
You preserve important caveats, make uncertainty visible, and organize the
result into an actionable project plan and task list.

Idea:
{idea}

Scoping brief:
{scoping_brief}

Review report:
{review_report}

Task:
Synthesize the scoping brief, research summary, and review report into a final
Markdown project plan.

Include these sections:
- Problem Statement
- MVP Scope
- Milestones
- First 3 Tasks
- Key Risks
- Open Questions

Important:
Preserve important caveats and do not introduce unsupported claims.

Expected output:
A clean Markdown project plan ready for project implementation, with major
uncertainties and risks clearly documented. Format as Markdown without code
fences.
""".strip()

    messages = [{"role": "user", "content": prompt}]
    response = _llm().invoke({"messages": messages})
    last_message = response["messages"][-1]
    return {"project_plan": last_message.content}


def write_project_plan_node(state: IdeaPlanningState) -> IdeaPlanningState:
    """Explicit replacement for CrewAI Task(output_file='project_plan.md')."""
    project_plan_path = Path(state.project_plan_path)
    project_plan_path.write_text(state.project_plan, encoding="utf-8")
    return {"project_plan_path": str(project_plan_path)}


def build_idea_planning_graph():
    graph = StateGraph(IdeaPlanningState)

    graph.add_node("scoping", scoping_node)
    graph.add_node("context_gathering", context_gathering_node)
    graph.add_node("quality_review", quality_review_node)
    graph.add_node("finalization", finalization_node)
    graph.add_node("write_project_plan", write_project_plan_node)

    graph.add_edge(START, "scoping")
    graph.add_edge("scoping", "context_gathering")
    graph.add_edge("context_gathering", "quality_review")
    graph.add_edge("quality_review", "finalization")
    graph.add_edge("finalization", "write_project_plan")
    graph.add_edge("write_project_plan", END)

    return graph.compile()


def run(
    idea: str,
    code_path: str = "",
    project_plan_path: str = "project_plan.md",
) -> IdeaPlanningState:
    app = build_idea_planning_graph()
    return app.invoke(
        {
            "idea": idea,
            "code_path": code_path,
            "project_plan_path": project_plan_path,
        }
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="python -m ai_dojo.graphs.idea_planning_graph"
    )
    parser.add_argument("--code-path")
    parser.add_argument("--idea")
    parser.add_argument("--output", default="project_plan.md")
    args = parser.parse_args()

    final_state = run(
        idea=args.idea,
        code_path=args.code_path,
        project_plan_path=args.output,
    )

    print(f"Wrote {final_state.project_plan_path}")