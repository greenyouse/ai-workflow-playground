from pathlib import Path

from ai_dojo.utils.repo_context_collector import RepoContextCollector


def test_collect_is_deterministic_for_same_issue_and_path(tmp_path: Path):
    source_dir = tmp_path / "src" / "ai_dojo"
    flows_dir = source_dir / "flows"
    configs_dir = source_dir / "crews" / "implementation_planner" / "config"
    docs_dir = tmp_path / "docs"
    flows_dir.mkdir(parents=True)
    configs_dir.mkdir(parents=True)
    docs_dir.mkdir(parents=True)

    (flows_dir / "implementation_flow.py").write_text("FLOW = 'implementation'\n", encoding="utf-8")
    (configs_dir / "tasks.yaml").write_text("task: implementation_flow\n", encoding="utf-8")
    (docs_dir / "notes.md").write_text("general documentation\n", encoding="utf-8")

    collector = RepoContextCollector()

    first = collector.collect(str(source_dir), issue="update implementation flow config")
    second = collector.collect(str(source_dir), issue="update implementation flow config")

    assert first.file_list == second.file_list
    assert first.content == second.content
    assert [item.score for item in first.ranked_files] == [item.score for item in second.ranked_files]


def test_collect_prioritizes_issue_and_target_path_matches(tmp_path: Path):
    source_dir = tmp_path / "src" / "ai_dojo"
    flows_dir = source_dir / "flows"
    tests_dir = tmp_path / "tests"
    flows_dir.mkdir(parents=True)
    tests_dir.mkdir(parents=True)

    target_file = flows_dir / "implementation_flow.py"
    nearby_file = flows_dir / "other_flow.py"
    unrelated_file = tests_dir / "test_misc.py"
    target_file.write_text("FLOW = 'implementation'\n", encoding="utf-8")
    nearby_file.write_text("FLOW = 'other'\n", encoding="utf-8")
    unrelated_file.write_text("def test_misc():\n    assert True\n", encoding="utf-8")

    collector = RepoContextCollector()
    result = collector.collect(str(source_dir), issue="fix implementation flow routing")

    assert result.ranked_files[0].path == str(target_file.resolve())
    assert str(unrelated_file.resolve()) not in result.file_list.splitlines()[:2]
    assert any(reason.startswith("keyword:") for reason in result.ranked_files[0].match_reasons)


def test_collect_marks_truncation_and_preserves_ranked_order(tmp_path: Path):
    source_dir = tmp_path / "src"
    source_dir.mkdir(parents=True)
    first = source_dir / "flow_alpha.py"
    second = source_dir / "flow_beta.py"
    first.write_text("A = 'alpha'\n" * 5, encoding="utf-8")
    second.write_text("B = 'beta'\n" * 5, encoding="utf-8")

    collector = RepoContextCollector(max_repo_context_chars=140)
    result = collector.collect(str(source_dir), issue="flow alpha")

    assert result.is_truncated is True
    assert result.selected_file_count == 1
    assert result.file_list.splitlines() == [str(first.resolve())]
    assert "CONTEXT TRUNCATED" in result.content


def test_collect_uses_content_matches_to_outrank_shallower_file(tmp_path: Path):
    source_dir = tmp_path / "src" / "ai_dojo"
    source_dir.mkdir(parents=True)
    shallow_file = source_dir / "helper.py"
    deeper_dir = source_dir / "features" / "routing"
    deeper_dir.mkdir(parents=True)
    deeper_file = deeper_dir / "planner.py"

    shallow_file.write_text("def helper():\n    return 'noop'\n", encoding="utf-8")
    deeper_file.write_text(
        "def implementation_router():\n    return 'routing implementation plan'\n",
        encoding="utf-8",
    )

    collector = RepoContextCollector()
    result = collector.collect(str(source_dir), issue="implementation routing")

    assert result.ranked_files[0].path == str(deeper_file.resolve())
    assert any(reason.startswith("content_keyword:") for reason in result.ranked_files[0].match_reasons)


def test_collect_oversized_top_file_does_not_block_smaller_matches(tmp_path: Path):
    source_dir = tmp_path / "src"
    source_dir.mkdir(parents=True)
    large_file = source_dir / "alpha_flow.py"
    smaller_file = source_dir / "alpha_notes.py"

    large_file.write_text("def alpha_flow():\n    return 'alpha'\n" * 20, encoding="utf-8")
    smaller_file.write_text("def alpha_note():\n    return 'alpha'\n", encoding="utf-8")

    collector = RepoContextCollector(max_repo_context_chars=280)
    result = collector.collect(str(source_dir), issue="alpha flow")

    assert result.is_truncated is True
    assert str(large_file.resolve()) in result.file_list.splitlines()
    assert str(smaller_file.resolve()) in result.file_list.splitlines()
    assert result.selected_file_count == 2


def test_collect_repo_context_preserves_tuple_compatibility(tmp_path: Path):
    source_file = tmp_path / "service.py"
    source_file.write_text("VALUE = 42\n", encoding="utf-8")

    collector = RepoContextCollector()
    collected_files, repo_context = collector.collect_repo_context(str(source_file), issue="service value")

    assert collected_files == str(source_file.resolve())
    assert f"Resolved code path: {source_file.resolve()}" in repo_context
    assert "Path type: file" in repo_context
    assert f"--- FILE: {source_file.resolve()} ---" in repo_context
    assert "VALUE = 42" in repo_context