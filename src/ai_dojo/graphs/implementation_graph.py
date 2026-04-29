"""LangGraph migration of ai_dojo.flows.implementation_flow.

CrewAI flow shape:
    prepare_context_and_run
        -> planning_crew
        -> review_crew
        -> approved? finalization_crew : revision_crew
        -> loop review until approved or max_revisions

LangGraph shape:
    collect_context
        -> planning
        -> review
        -> conditional: finalize or revise
        -> revise loops back to review
"""

from __future__ import annotations

import argparse
import re
import sys
from typing import TypedDict

from langchain.agents import create_agent
from langgraph.graph import END, START, StateGraph

from ai_dojo.utils.repo_context_collector import RepoContextCollector


class ImplementationState(TypedDict, total=False):
    issue: str
    code_path: str

    repo_context_content: str
    is_context_truncated: bool
    collected_files: str

    issue_analysis: str
    draft_plan: str
    review_feedback: str
    revised_plan: str

    revision_count: int
    max_revisions: int
    approved: bool

    final_result: str
    implementation_draft_path: str
    last_error: str


def _llm():
    return create_agent(model="ollama:gemma4")


def _is_approved(text: str) -> bool:
    raw = text.lower()
    match = re.search(r"approved\s*:\s*(true|false)", raw)
    if match:
        return match.group(1) == "true"
    return "approved" in raw and "not approved" not in raw


def collect_context_node(state: ImplementationState) -> ImplementationState:
    """Replacement for prepare_context_and_run."""
    issue = state.get("issue", "")
    code_path = state.get("code_path", "")

    if not issue:
        raise ValueError("State 'issue' must be provided.")
    if not code_path:
        raise ValueError("State 'code_path' must be provided.")

    collector = RepoContextCollector()

    try:
        repo_ctx = collector.collect(code_path, issue)
    except Exception as exc:
        return {
            "last_error": f"Failed to collect repo context: {exc}",
            "final_result": "Error: Could not read repository context.",
        }

    return {
        "repo_context_content": repo_ctx.content,
        "is_context_truncated": repo_ctx.is_truncated,
        "collected_files": repo_ctx.file_list,
        "revision_count": state.get("revision_count", 0),
        "max_revisions": state.get("max_revisions", 3),
        "approved": False,
    }

def route_after_collect_context(state: ImplementationState) -> str:
    if state.get("last_error"):
        return "write_error"
    return "issue_analysis"

def issue_analysis_node(state: ImplementationState) -> ImplementationState:
    """Replacement for planner + issue_analysis_task."""
    issue = state["issue"]

    prompt = f"""
You are a Project Strategy Lead.

Goal:
Analyze the issue and produce a bounded, realistic implementation plan.

Backstory:
You are an expert at project scoping and task decomposition. You turn vague
ideas into manageable plans, identify missing information, and avoid
overbuilding.

Task:
Analyze the following issue:

{issue}

Classify it as a bug, feature request, or refactor. Identify the likely
technical requirements, possible system impacts, unknowns, and the types of
code or documentation context needed before implementation.

Expected output:
A structured issue analysis containing:
- issue type
- problem summary
- likely requirements
- impacted areas
- possible side effects
- open questions
- prioritized retrieval strategy for relevant code and documentation context
""".strip()

    messages = [{"role": "user", "content": prompt}]
    response = _llm().invoke({"messages": messages})
    last_message = response["messages"][-1]
    return {"issue_analysis": last_message.content}


def implementation_drafting_node(state: ImplementationState) -> ImplementationState:
    """Replacement for implementer + implementation_drafting_task."""
    issue = state["issue"]
    issue_analysis = state["issue_analysis"]
    repo_context = state["repo_context_content"]
    collected_files = state["collected_files"]

    prompt = f"""
You are an Implementation Engineer.

Goal:
Transform validated technical plans into concrete implementation artifacts for
the issue, including proposed code changes, tests, and supporting technical
notes when appropriate.

Backstory:
You are a detail-oriented software engineer specializing in execution. You turn
scoped plans and technical context into practical implementation drafts. You
favor clear, testable changes, call out assumptions when context is incomplete,
and avoid inventing unsupported details.

Issue:
{issue}

Issue analysis:
{issue_analysis}

Repository context:
{repo_context}

Local files referenced:
{collected_files}

Task:
Using the issue analysis and structured technical context, propose a practical
solution. Draft the implementation approach, including proposed code changes,
relevant tests, and migration or rollout notes only if necessary.

Expected output:
A draft implementation package containing:
- solution summary
- proposed code changes or pseudocode
- test plan and sample test cases
- assumptions
- affected components
- required migration or rollout notes, if any

Important:
Ground all findings in the repository context. Do not invent missing code.
""".strip()

    messages = [{"role": "user", "content": prompt}]
    response = _llm().invoke({"messages": messages})
    last_message = response["messages"][-1]
    return {
        "draft_plan": last_message.content,
    }


def review_node(state: ImplementationState) -> ImplementationState:
    """Replacement for reviewer + draft_review_task."""
    issue = state["issue"]
    implementation_plan = state.get("revised_plan") or state["draft_plan"]
    repo_context = state["repo_context_content"]
    collected_files = state["collected_files"]

    prompt = f"""
You are a Technical Quality Critic.

Goal:
Evaluate the current plan for logic flaws, hidden risks, missing criteria, and
unsupported assumptions.

Backstory:
You are a rigorous reviewer who stress-tests plans before implementation. You
look for ambiguity, unrealistic scope, missing edge cases, and weak reasoning,
and you suggest concrete corrections.

Task:
Critically evaluate the following implementation draft for:

{issue}

Check for logic errors, missing edge cases, security concerns, architectural
misalignment, unsupported assumptions, and inadequate test coverage. Confirm
that the proposed implementation actually addresses the original issue without
unnecessary scope expansion.

Draft implementation:
{implementation_plan}

Collected files:
{collected_files}

Repository context:
{repo_context}

Expected output:
Start with exactly one of these lines:

approved: true

or

approved: false

Then include concise review feedback explaining the decision.
""".strip()

    messages = [{"role": "user", "content": prompt}]
    response = _llm().invoke({"messages": messages})
    last_message = response["messages"][-1]
    return {
        "review_feedback": last_message.content,
        "approved": _is_approved(last_message.content),
    }


def route_after_review(state: ImplementationState) -> str:
    """Conditional replacement for CrewAI route_after_review."""
    if state.get("approved", False):
        return "finalize"

    revision_count = state.get("revision_count", 0)
    max_revisions = state.get("max_revisions", 3)

    if revision_count >= max_revisions:
        return "finalize"

    return "revise"


def revision_node(state: ImplementationState) -> ImplementationState:
    """Replacement for implementer + revise_issue_task."""
    issue = state["issue"]
    implementation_plan = state.get("revised_plan") or state["draft_plan"]
    review_feedback = state["review_feedback"]
    repo_context = state["repo_context_content"]
    collected_files = state["collected_files"]

    revision_count = state.get("revision_count", 0) + 1

    prompt = f"""
You are an Implementation Engineer.

Goal:
Revise the implementation draft using reviewer feedback.

Issue:
{issue}

Draft implementation:
{implementation_plan}

Review feedback:
{review_feedback}

Repository context:
{repo_context}

Repository context file collection:
{collected_files}

Revision round:
{revision_count}

Task:
Update the proposed solution, tests, and technical notes to address the most
important critiques where possible. Preserve unresolved risks, assumptions, or
open questions if they cannot be fully resolved from the available context.

Expected output:
A revised implementation draft containing:
- updated solution summary
- revised code changes or pseudocode
- updated test plan
- addressed review items
- unresolved concerns requiring human judgment

Important:
Ground all findings in the repository context. Do not invent missing context.
""".strip()

    messages = [{"role": "user", "content": prompt}]
    response = _llm().invoke({"messages": messages})
    last_message = response["messages"][-1]
    return {
        "revision_count": revision_count,
        "revised_plan": last_message.content,
    }


def finalization_node(state: ImplementationState) -> ImplementationState:
    """Replacement for synthesizer + final_draft_synthesis_task."""
    issue = state["issue"]
    implementation_plan = state.get("revised_plan") or state["draft_plan"]
    review_feedback = state.get("review_feedback", "")
    approved = state.get("approved", False)
    revision_count = state.get("revision_count", 0)
    max_revisions = state.get("max_revisions", 3)

    prompt = f"""
You are a Documentation Specialist.

Goal:
Convert validated planning materials into clear, structured Markdown
documentation for human use.

Backstory:
You turn research, planning, and review outputs into polished documentation.
You preserve important caveats, make uncertainty visible, and organize the
result into an actionable implementation brief.

Issue:
{issue}

Implementation draft:
{implementation_plan}

Review feedback:
{review_feedback}

Approval status:
approved: {str(approved).lower()}

Revision count:
{revision_count}

Max revisions:
{max_revisions}

Task:
Consolidate the issue analysis, technical context, implementation draft, and
review feedback into a final Markdown implementation brief. Present it in a
form a human developer can act on immediately, while preserving important
caveats, assumptions, and unresolved questions.

Expected output:
A clean Markdown implementation brief containing:
- Issue Summary
- Proposed Solution
- Affected Areas
- Implementation Notes
- Test Plan
- Key Risks
- Required Revisions
- Open Questions

Important:
If the plan was finalized only because max revisions was reached, make that
clear in the risks or open questions section. Format as Markdown without code
fences.
""".strip()

    messages = [{"role": "user", "content": prompt}]
    response = _llm().invoke({"messages": messages})
    last_message = response["messages"][-1]
    return {"final_result": last_message.content}


def write_implementation_draft_node(
    state: ImplementationState,
) -> ImplementationState:
    """Replacement for output_file='implementation_draft.md'."""
    path = state.get("implementation_draft_path", "implementation_draft.md")
    content = state.get("final_result", "Error: No final result was produced.")

    with open(path, "w", encoding="utf-8") as file:
        file.write(content)

    return {"implementation_draft_path": path}


def build_implementation_graph():
    graph = StateGraph(ImplementationState)

    graph.add_node("collect_context", collect_context_node)
    graph.add_node("issue_analysis", issue_analysis_node)
    graph.add_node("implementation_drafting", implementation_drafting_node)
    graph.add_node("review", review_node)
    graph.add_node("revise", revision_node)
    graph.add_node("finalize", finalization_node)
    graph.add_node("write_implementation_draft", write_implementation_draft_node)

    graph.add_edge(START, "collect_context")
    graph.add_edge("collect_context", "issue_analysis")

    graph.add_conditional_edges(
        "collect_context",
        route_after_collect_context,
        {
         "issue_analysis": "issue_analysis",
        "write_error": "write_implementation_draft",
        },
    )

    graph.add_edge("issue_analysis", "implementation_drafting")
    graph.add_edge("implementation_drafting", "review")

    graph.add_conditional_edges(
        "review",
        route_after_review,
        {
            "revise": "revise",
            "finalize": "finalize",
        },
    )

    graph.add_edge("revise", "review")
    graph.add_edge("finalize", "write_implementation_draft")
    graph.add_edge("write_implementation_draft", END)

    return graph.compile()


def run(
    issue: str,
    code_path: str,
    max_revisions: int = 3,
    implementation_draft_path: str = "implementation_draft.md",
) -> ImplementationState:
    app = build_implementation_graph()
    return app.invoke(
        {
            "issue": issue,
            "code_path": code_path,
            "max_revisions": max_revisions,
            "implementation_draft_path": implementation_draft_path,
        }
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="python -m ai_dojo.graphs.implementation_graph"
    )
    parser.add_argument("--code-path")
    parser.add_argument("--issue")
    parser.add_argument("--max-revisions", type=int, max=3)
    parser.add_argument("--output", default="implementation_draft.md")
    args = parser.parse_args()

    final_state = run(
        issue=args.issue,
        code_path=args.code_path,
        max_revisions=args.max_revisions,
        output=args.output,
    )

    print(f"Wrote {final_state['implementation_draft_path']}")