"""
Takes an implementation plan and turns that into failing tests
for TDD style development.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from pydantic import BaseModel

from langchain.agents import create_agent
from langgraph.graph import END, START, StateGraph

from ai_dojo.utils.repo_context_collector import RepoContextCollector


class TDDState(BaseModel):
    implementation_plan: str
    code_path: str = ""

    resolved_code_path: str
    repo_context: str
    collected_files: str
    max_file_chars: int = 20000
    max_repo_context_chars: int = 120000

    test_strategy: str
    repo_mapping: str
    test_suite: str
    review_feedback: str

    previous_test_suite: str
    revised_test_suite: str
    revision_review: str

    revisions: int = 0
    max_revisions: int = 1

    approved: bool = False
    final_test_suite: str
    final_review: str
    failing_tests_path: str = "failing_tests_draft.py"
    last_error: str


def _llm():
    return create_agent(model="ollama:gemma4")


def _is_approved(text: str) -> bool:
    raw = text.lower()

    if "status: approved" in raw:
        return True
    if "status: not approved" in raw:
        return False

    if re.search(r"\bapproved\s*:\s*true\b", raw):
        return True
    if re.search(r"\bapproved\s*:\s*false\b", raw):
        return False

    if "ready" in raw and "not ready" not in raw:
        return True

    return False


def collect_repo_context_node(state: TDDState) -> TDDState:
    """Replacement for TDDFlow.collect_repo_context."""
    code_path = state.code_path

    if not code_path:
        raise ValueError("State 'code_path' must be provided.")

    collector = RepoContextCollector(
        max_file_chars=state.max_file_chars,
        max_repo_context_chars=state.max_repo_context_chars
    )

    resolved_code_path = collector.resolve_code_path(code_path)
    collected_files, repo_context = collector.collect_repo_context(resolved_code_path)

    return {
        "resolved_code_path": str(resolved_code_path),
        "collected_files": collected_files,
        "repo_context": repo_context,
        "revisions": state.revisions,
        "max_revisions": state.max_revisions,
        "approved": False,
    }


def test_scoping_node(state: TDDState) -> TDDState:
    """Replacement for tdd_planner + test_scoping_task."""
    implementation_plan = state["implementation_plan"]

    prompt = f"""
You are a Test Strategy Lead.

Goal:
Translate the implementation plan into a bounded, practical TDD test strategy.

Backstory:
You are an expert in TDD and software quality. You identify the core behaviors,
edge cases, and integration points that should be tested first to define
success clearly without overbuilding the initial test suite.

Implementation plan:
{implementation_plan}

Task:
Review the implementation plan. Identify the critical behaviors, edge cases,
failure modes, and integration points that should be covered by the initial TDD
test suite. Prioritize the smallest set of tests that clearly defines expected
behavior.

Expected output:
A structured test strategy containing:
- behaviors to validate
- prioritized test cases
- suggested test level, such as unit or integration
- key edge cases
- assumptions
- open questions that could affect test design
""".strip()

    messages = [{"role": "user", "content": prompt}]
    response = _llm().invoke({"messages": messages})
    last_message = response["messages"][-1]
    return {"test_strategy": last_message.content}


def repo_mapping_node(state: TDDState) -> TDDState:
    """Replacement for repo_analyst + repo_mapping_task."""
    code_path = state["code_path"]
    collected_files = state["collected_files"]
    repo_context = state["repo_context"]
    test_strategy = state["test_strategy"]

    prompt = f"""
You are a Codebase Infrastructure Analyst.

Goal:
Analyze the repository structure and testing conventions to determine where and
how new tests should be added.

Backstory:
You specialize in codebase archaeology. You identify existing test suites,
naming conventions, frameworks, fixtures, helpers, and structural patterns so
new tests fit naturally into the repository and reuse existing testing
infrastructure where possible.

Code path:
{code_path}

Test strategy:
{test_strategy}

Collected files:
{collected_files}

Repository context:
{repo_context}

Task:
Analyze the repository evidence already collected from the code path. Use only
the provided file manifest and supplied file contents to identify where new
tests should live, which testing framework and conventions are used, and which
fixtures, helpers, mocks, or existing test patterns should be reused.

Expected output:
A structured repository test-context report containing:
- target test file location
- framework and style conventions
- relevant fixtures or helpers
- similar existing tests to follow
- repository-specific constraints
- files reviewed

Important:
Only reference files that appear in the provided collected files list. Do not
infer unseen files or repository structure beyond the supplied evidence.
""".strip()

    messages = [{"role": "user", "content": prompt}]
    response = _llm().invoke({"messages": messages})
    last_message = response["messages"][-1]
    return {"repo_mapping": last_message.content}


def test_generation_node(state: TDDState) -> TDDState:
    """Replacement for test_engineer + test_generation_task."""
    implementation_plan = state["implementation_plan"]
    test_strategy = state["test_strategy"]
    repo_mapping = state["repo_mapping"]
    collected_files = state["collected_files"]
    repo_context = state["repo_context"]

    prompt = f"""
You are a TDD Test Developer.

Goal:
Generate concrete, intentionally failing test code based on the testing
strategy and repository conventions.

Backstory:
You specialize in writing clean, idiomatic test code. You create tests that
define required behavior before implementation exists, reuse repository testing
patterns where possible, and make unavoidable assumptions explicit instead of
silently inventing details.

Implementation plan:
{implementation_plan}

Test strategy:
{test_strategy}

Repository test-context report:
{repo_mapping}

Collected files:
{collected_files}

Repository context:
{repo_context}

Task:
Using the test strategy and repository test-context report, generate the
initial failing test suite for the implementation plan. Follow repository
conventions for test structure, naming, fixtures, and style.

Expected output:
A draft failing test suite containing:
- target test file path
- concrete test code
- short code comments for assumptions
- a short code comment explaining why the tests should fail before
  implementation exists

Important:
Do not output Markdown, prose summaries, or code fences. Do not invent helpers,
fixtures, modules, or file locations that are absent from the repository
evidence.
""".strip()

    messages = [{"role": "user", "content": prompt}]
    response = _llm().invoke({"messages": messages})
    last_message = response["messages"][-1]
    return {
        "test_suite": last_message.content,
        "final_test_suite": last_message.content,
    }


def test_review_node(state: TDDState) -> TDDState:
    """Replacement for tdd_reviewer + test_review_task."""
    implementation_plan = state["implementation_plan"]
    test_strategy = state["test_strategy"]
    repo_mapping = state["repo_mapping"]
    test_suite = state["test_suite"]
    collected_files = state["collected_files"]

    prompt = f"""
You are a Test Quality Critic.

Goal:
Verify that the generated tests accurately capture the intended behavior,
follow repository conventions, and fail for the right reasons.

Backstory:
You are a skeptic who checks that tests are not passing by accident, overfitting
to implementation details, or using brittle logic. You ensure the test suite
reflects the implementation plan's requirements clearly and idiomatically.

Implementation plan:
{implementation_plan}

Test strategy:
{test_strategy}

Repository mapping:
{repo_mapping}

Collected files:
{collected_files}

Generated test suite:
{test_suite}

Task:
Critically review the generated tests. Ensure they are idiomatic, aligned with
the implementation plan, consistent with repository conventions, and unlikely
to pass prematurely or fail for irrelevant reasons. Check for brittle
assertions, missing coverage, over-coupling to imagined implementation details,
and references to files or helpers that do not appear in the supplied
repository evidence.

Expected output:
Start with exactly one of these lines:

status: approved

or

status: not approved

Then include:
- major critiques
- coverage gaps
- brittle or misleading test patterns
- convention mismatches
- required revisions, if any
""".strip()

    messages = [{"role": "user", "content": prompt}]
    response = _llm().invoke({"messages": messages})
    last_message = response["messages"][-1]

    return {
        "review_feedback": last_message.content,
        "approved": _is_approved(last_message.content),
        "final_review": last_message.content,
    }


def route_after_review(state: TDDState) -> str:
    """Replacement for TDDFlow.route_after_initial / route_after_revision."""
    if state.approved:
        return "done"

    if state.revisions < state.max_revisions:
        return "revise"

    return "done"


def test_revision_node(state: TDDState) -> TDDState:
    """Replacement for test_engineer + test_revision_task."""
    revisions = state.revisions + 1

    implementation_plan = state.implementation_plan
    previous_test_suite = state.revised_test_suite or state.test_suite
    review_feedback = state.revision_review or state.review_feedback
    collected_files = state.collected_files
    repo_context = state.repo_context

    prompt = f"""
You are a TDD Test Developer.

Goal:
Revise the generated test suite using reviewer feedback.

Implementation plan:
{implementation_plan}

Previous test suite:
{previous_test_suite}

Review feedback:
{review_feedback}

Collected files:
{collected_files}

Repository context:
{repo_context}

Revision round:
{revisions}

Task:
Revise the generated test suite using the explicit prior-round artifacts. Treat
the previous test suite as the last draft and the review feedback as the
feedback that must be addressed in this revision round. Update test structure,
assertions, fixtures, and assumptions to address the most important critiques
while preserving the intended TDD behavior.

Expected output:
A revised failing test suite containing:
- updated test code
- addressed review items as short code comments where useful
- short code comments on unresolved assumptions or issues needing human judgment

Important:
Do not output Markdown, prose summaries, or code fences. Continue to rely only
on the supplied repository evidence and do not introduce unseen files, helpers,
or fixtures.
""".strip()

    messages = [{"role": "user", "content": prompt}]
    response = _llm().invoke({"messages": messages})
    last_message = response["messages"][-1]

    return {
        "revisions": revisions,
        "previous_test_suite": previous_test_suite,
        "revised_test_suite": last_message.content,
        "final_test_suite": last_message.content,
    }


def revision_review_node(state: TDDState) -> TDDState:
    """Replacement for tdd_reviewer + revised_test_review_task."""
    implementation_plan = state["implementation_plan"]
    previous_test_suite = state["previous_test_suite"]
    revised_test_suite = state["revised_test_suite"]
    review_feedback = state["review_feedback"]

    prompt = f"""
You are a Test Quality Critic.

Goal:
Review the revised failing test suite produced by the previous task.

Implementation plan:
{implementation_plan}

Previous test suite:
{previous_test_suite}

Prior review feedback:
{review_feedback}

Revised test suite:
{revised_test_suite}

Task:
Compare the revised draft against the prior review feedback and confirm whether
the earlier critiques were actually addressed. Focus on whether the tests still
fail for the right reasons, remain aligned with the implementation plan, follow
repository conventions, and avoid brittle or fabricated details.

Expected output:
Start with exactly one of these lines:

status: approved

or

status: not approved

Then include:
- specific review items that were resolved
- remaining gaps or risks
- brittle or misleading patterns still present
- whether the revised suite is acceptable for human use or needs another pass

Important:
Do not introduce new requirements that were not part of the prior review.
""".strip()

    messages = [{"role": "user", "content": prompt}]
    response = _llm().invoke({"messages": messages})
    last_message = response["messages"][-1]

    return {
        "revision_review": last_message.content,
        "approved": _is_approved(last_message.content),
        "final_review": last_message.content,
    }


def write_failing_tests_node(state: TDDState) -> TDDState:
    """Writes the final generated/revised failing test draft."""
    path = Path(state.failing_tests_path)
    path.write_text(state.final_test_suite, encoding="utf-8")
    return {"failing_tests_path": str(path)}


def build_tdd_graph():
    graph = StateGraph(TDDState)

    graph.add_node("collect_repo_context", collect_repo_context_node)
    graph.add_node("test_scoping", test_scoping_node)
    graph.add_node("repo_mapping", repo_mapping_node)
    graph.add_node("test_generation", test_generation_node)
    graph.add_node("test_review", test_review_node)
    graph.add_node("test_revision", test_revision_node)
    graph.add_node("revision_review", revision_review_node)
    graph.add_node("write_failing_tests", write_failing_tests_node)

    graph.add_edge(START, "collect_repo_context")
    graph.add_edge("collect_repo_context", "test_scoping")
    graph.add_edge("test_scoping", "repo_mapping")
    graph.add_edge("repo_mapping", "test_generation")
    graph.add_edge("test_generation", "test_review")

    graph.add_conditional_edges(
        "test_review",
        route_after_review,
        {
            "revise": "test_revision",
            "done": "write_failing_tests",
        },
    )

    graph.add_edge("test_revision", "revision_review")

    graph.add_conditional_edges(
        "revision_review",
        route_after_review,
        {
            "revise": "test_revision",
            "done": "write_failing_tests",
        },
    )

    graph.add_edge("write_failing_tests", END)

    return graph.compile()


def run(
    implementation_plan: str,
    code_path: str,
    max_revisions: int = 1,
    failing_tests_path: str = "failing_tests_draft.py",
) -> TDDState:
    app = build_tdd_graph()
    return app.invoke(
        {
            "implementation_plan": implementation_plan,
            "code_path": code_path,
            "max_revisions": max_revisions,
            "failing_tests_path": failing_tests_path,
        }
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="python -m ai_dojo.graphs.tdd_graph"
    )
    parser.add_argument("--code-path")
    parser.add_argument("--issue")
    parser.add_argument("--max-revisions", type=int, default=3)
    parser.add_argument("--output", default="failing_tests_draft.py")
    args = parser.parse_args()

    final_state = run(
        implementation_plan=args.issue,
        code_path=args.code_path,
        max_revisions=args.max_revisions,
        failing_tests_path=args.output,
    )

    print(f"Wrote {final_state['failing_tests_path']}")
    print(f"Approved: {final_state.approved}")