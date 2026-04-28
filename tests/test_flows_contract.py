from pathlib import Path

from ai_dojo.flows.implementation_flow import ImplementationFlow
from ai_dojo.flows.tdd_flow import TDDFlow
from ai_dojo.models import ReviewVerdict


def test_implementation_flow_build_inputs_use_collected_context():
    flow = ImplementationFlow()
    flow.state.issue = "Add a review gate for implementation plans"
    flow.state.code_path = "src/ai_dojo"
    flow.state.repo_context_content = "repo context payload"
    flow.state.collected_files = "/tmp/project/src/ai_dojo/main.py"
    flow.state.draft_plan = "draft implementation plan"
    flow.state.review_feedback = "approved: false"

    assert flow._build_planning_inputs() == {
        "idea": "Add a review gate for implementation plans",
        "issue": "Add a review gate for implementation plans",
        "code_path": "src/ai_dojo",
        "repo_context": "repo context payload",
        "collected_files": "/tmp/project/src/ai_dojo/main.py",
        "revision_round": "0",
    }

    assert flow._build_review_inputs("draft implementation plan") == {
        "idea": "Add a review gate for implementation plans",
        "issue": "Add a review gate for implementation plans",
        "code_path": "src/ai_dojo",
        "repo_context": "repo context payload",
        "collected_files": "/tmp/project/src/ai_dojo/main.py",
        "implementation_plan": "draft implementation plan",
    }

    assert flow._build_revision_inputs() == {
        "idea": "Add a review gate for implementation plans",
        "issue": "Add a review gate for implementation plans",
        "code_path": "src/ai_dojo",
        "repo_context": "repo context payload",
        "collected_files": "/tmp/project/src/ai_dojo/main.py",
        "implementation_plan": "draft implementation plan",
        "review_feedback": "approved: false",
        "revision_round": "0",
    }


def test_implementation_flow_defaults_to_revision_limit_and_state_model():
    flow = ImplementationFlow()

    assert flow.max_revisions == 1
    assert flow.state.issue == ""
    assert flow.state.code_path == ""
    assert flow.state.final_result == ""


def test_implementation_flow_formats_structured_review_verdict():
    flow = ImplementationFlow()
    verdict = ReviewVerdict(
        approved=False,
        summary="Needs another pass",
        major_issues=["Missing tests", "Unclear routing"],
        required_revisions=["Add focused tests", "Route on structured verdict"],
    )

    assert flow._format_review_feedback(verdict) == (
        "approved: false\n"
        "summary: Needs another pass\n"
        "major_issues:\n"
        "- Missing tests\n"
        "- Unclear routing\n"
        "required_revisions:\n"
        "- Add focused tests\n"
        "- Route on structured verdict"
    )


def test_implementation_flow_extracts_structured_review_verdict():
    flow = ImplementationFlow()
    result = type(
        "Result",
        (),
        {"pydantic": ReviewVerdict(approved=True, summary="Looks good")},
    )()

    verdict = flow._extract_review_verdict(result)

    assert verdict.approved is True
    assert verdict.summary == "Looks good"


def test_tdd_flow_build_inputs_include_retrieval_payloads():
    flow = TDDFlow()
    flow.state["implementation_plan"] = "Add deterministic retrieval for TDD"
    flow.state["code_path"] = "src/ai_dojo"
    flow.state["repo_context"] = "Resolved code path: /tmp/project/src/ai_dojo"
    flow.state["collected_files"] = "/tmp/project/src/ai_dojo/main.py"
    flow.state["revisions"] = 1
    flow.state["result"] = type(
        "Result",
        (),
        {
            "raw": "status: needs revision",
            "tasks_output": [
                type("TaskOutput", (), {"raw": "scope report"})(),
                type("TaskOutput", (), {"raw": "repo mapping"})(),
                type("TaskOutput", (), {"raw": "generated tests"})(),
                type("TaskOutput", (), {"raw": "review feedback"})(),
            ],
        },
    )()

    assert flow._build_initial_inputs() == {
        "implementation_plan": "Add deterministic retrieval for TDD",
        "code_path": "src/ai_dojo",
        "repo_context": "Resolved code path: /tmp/project/src/ai_dojo",
        "collected_files": "/tmp/project/src/ai_dojo/main.py",
    }

    assert flow._build_revision_inputs() == {
        "implementation_plan": "Add deterministic retrieval for TDD",
        "code_path": "src/ai_dojo",
        "repo_context": "Resolved code path: /tmp/project/src/ai_dojo",
        "collected_files": "/tmp/project/src/ai_dojo/main.py",
        "previous_result": "status: needs revision",
        "previous_test_suite": "generated tests",
        "review_feedback": "review feedback",
        "revision_round": "1",
    }


def test_tdd_flow_revision_inputs_fall_back_to_result_raw_when_task_outputs_missing():
    flow = TDDFlow()
    flow.state["implementation_plan"] = "Add deterministic retrieval for TDD"
    flow.state["code_path"] = "src/ai_dojo"
    flow.state["repo_context"] = "Resolved code path: /tmp/project/src/ai_dojo"
    flow.state["collected_files"] = "/tmp/project/src/ai_dojo/main.py"
    flow.state["revisions"] = 1
    flow.state["result"] = type("Result", (), {"raw": "status: needs revision"})()

    assert flow._build_revision_inputs()["previous_test_suite"] == "status: needs revision"
    assert flow._build_revision_inputs()["review_feedback"] == "status: needs revision"


def test_tdd_flow_collects_directory_context(tmp_path: Path):
    source_dir = tmp_path / "src" / "ai_dojo"
    source_dir.mkdir(parents=True)
    first_file = source_dir / "main.py"
    second_file = source_dir / "flows.py"
    cache_dir = source_dir / "__pycache__"
    cache_dir.mkdir()
    cached_file = cache_dir / "ignored.py"
    first_file.write_text("print('hello')\n", encoding="utf-8")
    second_file.write_text("FLOW = True\n", encoding="utf-8")
    cached_file.write_text("SHOULD_NOT_APPEAR = True\n", encoding="utf-8")

    flow = TDDFlow()
    flow.state["code_path"] = str(source_dir)
    flow.state["resolved_code_path"] = source_dir.resolve()

    collected_files, repo_context = flow._collect_repo_context()

    assert str(first_file.resolve()) in collected_files
    assert str(second_file.resolve()) in collected_files
    assert str(cached_file.resolve()) not in collected_files
    assert f"Resolved code path: {source_dir.resolve()}" in repo_context
    assert f"--- FILE: {first_file.resolve()} ---" in repo_context
    assert "print('hello')" in repo_context
    assert "SHOULD_NOT_APPEAR" not in repo_context


def test_tdd_flow_collects_single_file_context(tmp_path: Path):
    source_file = tmp_path / "service.py"
    source_file.write_text("VALUE = 42\n", encoding="utf-8")

    flow = TDDFlow()
    flow.state["code_path"] = str(source_file)
    flow.state["resolved_code_path"] = source_file.resolve()

    collected_files, repo_context = flow._collect_repo_context()

    assert collected_files == str(source_file.resolve())
    assert "Path type: file" in repo_context
    assert "VALUE = 42" in repo_context


def test_tdd_flow_resolve_code_path_requires_existing_file_or_directory(tmp_path: Path):
    flow = TDDFlow()
    flow.state["code_path"] = str(tmp_path / "missing.py")

    try:
        flow._resolve_code_path()
    except FileNotFoundError as exc:
        assert "code_path does not exist" in str(exc)
    else:
        raise AssertionError("Expected FileNotFoundError for missing code_path")
