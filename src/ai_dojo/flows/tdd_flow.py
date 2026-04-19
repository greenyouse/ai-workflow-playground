from pathlib import Path

from crewai.flow.flow import Flow, listen, router, start
from ai_dojo.crews.tdd_implementation.tdd_implementation_crew import TddImplementationCrew
from ai_dojo.utils.repo_context_collector import RepoContextCollector


class TDDFlow(Flow):
    max_revisions: int = 1
    max_file_chars: int = 20000
    max_repo_context_chars: int = 120000

    @start()
    def collect_repo_context(self):
        collector = self._repo_context_collector()
        self.state["resolved_code_path"] = self._resolve_code_path(collector)
        collected_files, repo_context = collector.collect_repo_context(
            self.state["resolved_code_path"]
        )
        self.state["collected_files"] = collected_files
        self.state["repo_context"] = repo_context
        return repo_context

    @listen(collect_repo_context)
    def run_initial(self, _repo_context):
        self.state["revisions"] = 0
        result = TddImplementationCrew().tdd_implementation_crew().kickoff(
            inputs=self._build_initial_inputs()
        )
        self.state["result"] = result
        return result

    @router(run_initial)
    def route_after_initial(self, result):
        if self._is_approved(result):
            return "done"
        if self.state["revisions"] < self.max_revisions:
            return "needs_revision"
        return "done"

    @listen("needs_revision")
    def revise(self):
        self.state["revisions"] += 1
        result = TddImplementationCrew().tdd_revision_crew().kickoff(
            inputs=self._build_revision_inputs()
        )
        self.state["result"] = result
        return result

    @router(revise)
    def route_after_revision(self, result):
        if self._is_approved(result):
            return "done"
        return "done"

    @listen("done")
    def finish(self):
        return self.state["result"]

    def _build_initial_inputs(self) -> dict[str, str]:
        return {
            "implementation_plan": self.state.get("implementation_plan", ""),
            "code_path": self.state.get("code_path", ""),
            "repo_context": self.state.get("repo_context", ""),
            "collected_files": self.state.get("collected_files", ""),
        }

    def _build_revision_inputs(self) -> dict[str, str]:
        previous_test_suite, review_feedback = self._extract_revision_artifacts(
            self.state["result"]
        )
        return {
            "implementation_plan": self.state.get("implementation_plan", ""),
            "code_path": self.state.get("code_path", ""),
            "repo_context": self.state.get("repo_context", ""),
            "collected_files": self.state.get("collected_files", ""),
            "previous_result": getattr(self.state["result"], "raw", str(self.state["result"])),
            "previous_test_suite": previous_test_suite,
            "review_feedback": review_feedback,
            "revision_round": str(self.state["revisions"]),
        }

    def _is_approved(self, result) -> bool:
        raw = getattr(result, "raw", str(result)).lower()
        return "status: approved" in raw

    def _resolve_code_path(self, collector: RepoContextCollector | None = None) -> Path:
        return (collector or self._repo_context_collector()).resolve_code_path(
            self.state.get("code_path", "")
        )

    def _extract_revision_artifacts(self, result) -> tuple[str, str]:
        task_outputs = getattr(result, "tasks_output", None)
        if task_outputs is None:
            task_outputs = getattr(result, "tasks_outputs", [])

        previous_test_suite = ""
        review_feedback = ""

        if len(task_outputs) > 2:
            previous_test_suite = self._stringify_output(task_outputs[2])
        if len(task_outputs) > 3:
            review_feedback = self._stringify_output(task_outputs[3])

        previous_result = getattr(result, "raw", str(result))
        if not previous_test_suite:
            previous_test_suite = previous_result
        if not review_feedback:
            review_feedback = previous_result

        return previous_test_suite, review_feedback

    def _stringify_output(self, output) -> str:
        return getattr(output, "raw", str(output))

    def _repo_context_collector(self) -> RepoContextCollector:
        return RepoContextCollector(
            max_file_chars=self.max_file_chars,
            max_repo_context_chars=self.max_repo_context_chars,
        )

    def _collect_repo_context(self) -> tuple[str, str]:
        return self._repo_context_collector().collect_repo_context(
            self.state["resolved_code_path"]
        )