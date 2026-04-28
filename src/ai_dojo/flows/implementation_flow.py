import re

from pydantic import BaseModel
from crewai.flow.flow import Flow, listen, router, start
from crewai import Crew
from ai_dojo.crews.implementation_planner.implementation_planner_crew import ImplementationPlannerCrew
from ai_dojo.utils.repo_context_collector import RepoContextCollector

class ImplementationState(BaseModel):
    """
    Structured state for the Implementation Flow.
    """
    issue: str = ""
    code_path: str = ""

    # Context data populated by RepoContextCollector
    repo_context_content: str = ""
    is_context_truncated: bool = False
    collected_files: str = ""

    # Planning artifacts
    draft_plan: str = ""
    review_feedback: str = ""
    revised_plan: str = ""

    # Execution tracking
    revision_count: int = 0
    max_revisions: int = 3
    approved: bool = False
    final_result: str = ""
    last_error: str = ""

class ImplementationFlow(Flow[ImplementationState]):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize utility once to avoid repeated file system scans
        self.context_collector = RepoContextCollector()
        # Cache the Crew instances to prevent re-creating Agents/Tools on every step
        self._planning_crew: Crew | None = None
        self._review_crew: Crew | None = None
        self._revision_crew: Crew | None = None
        self._finalization_crew: Crew | None = None

    def _get_planning_crew(self) -> Crew:
        if self._planning_crew is None:
            self._planning_crew = ImplementationPlannerCrew().planning_crew()
        return self._planning_crew

    def _get_review_crew(self) -> Crew:
        if self._review_crew is None:
            self._review_crew = ImplementationPlannerCrew().review_crew()
        return self._review_crew

    def _get_revision_crew(self) -> Crew:
        if self._revision_crew is None:
            self._revision_crew = ImplementationPlannerCrew().revision_crew()
        return self._revision_crew

    def _get_finalization_crew(self) -> Crew:
        if self._finalization_crew is None:
            self._finalization_crew = ImplementationPlannerCrew().finalization_crew()
        return self._finalization_crew

    @start()
    def prepare_context_and_run(self):
        """
        1. Validate inputs.
        2. Collect repo context from code_path.
        3. Build the initial planning inputs.
        """
        self._validate_initial_state()

        try:
            repo_ctx = self.context_collector.collect(self.state.code_path, self.state.issue)
            self.state.repo_context_content = repo_ctx.content
            self.state.is_context_truncated = repo_ctx.is_truncated
            self.state.collected_files = repo_ctx.file_list
        except Exception as e:
            self.state.last_error = f"Failed to collect repo context: {str(e)}"
            self.state.final_result = "Error: Could not read repository context."
            raise ValueError(e)

        return self._build_planning_inputs()

    def _result_to_text(self, result) -> str:
        return getattr(result, "raw", str(result))

    def _build_planning_inputs(self) -> dict[str, str]:
        return {
            "idea": self.state.issue,
            "issue": self.state.issue,
            "code_path": self.state.code_path,
            "repo_context": self.state.repo_context_content,
            "collected_files": self.state.collected_files,
            "revision_round": str(self.state.revision_count),
        }

    def _build_review_inputs(self, implementation_plan: str) -> dict[str, str]:
        return {
            "idea": self.state.issue,
            "issue": self.state.issue,
            "code_path": self.state.code_path,
            "repo_context": self.state.repo_context_content,
            "collected_files": self.state.collected_files,
            "implementation_plan": implementation_plan,
        }

    def _build_revision_inputs(self) -> dict[str, str]:
        return {
            "idea": self.state.issue,
            "issue": self.state.issue,
            "code_path": self.state.code_path,
            "repo_context": self.state.repo_context_content,
            "collected_files": self.state.collected_files,
            "implementation_plan": self.state.draft_plan,
            "review_feedback": self.state.review_feedback,
            "revision_round": str(self.state.revision_count),
        }

    @listen(prepare_context_and_run)
    def run_planning(self, planning_inputs: dict[str, str]) -> str:
        """
        Execute the initial planning crew and persist the draft plan.
        """
        try:
            result = self._get_planning_crew().kickoff(inputs=planning_inputs)
            draft_plan = self._result_to_text(result)
            self.state.draft_plan = draft_plan
            self.state.final_result = draft_plan
            return self.state.final_result
        except Exception as e:
            self.state.last_error = str(e)
            self.state.final_result = f"Error: {str(e)}"
            raise ValueError(e)

    @router(run_planning)
    def run_after_planning(self, _implementation_plan: str):
        return "review"

    @listen("review")
    def run_review(self, implementation_plan: str) -> str:
        """
        Review the draft plan and persist the review feedback.
        """
        try:
            review_result = self._get_review_crew().kickoff(
                inputs=self._build_review_inputs(implementation_plan)
            )
            report_text = self._result_to_text(review_result)
            self.state.review_feedback = report_text
            self.state.approved = self._is_approved(review_result)
            return self.state.approved
        except Exception as e:
            self.state.last_error = str(e)
            self.state.review_feedback = f"approved: false\nerror: {str(e)}"
            self.state.approved = False
            raise ValueError(e)

    @router(run_review)
    def route_after_review(self, is_approved: bool) -> str:
        """
        Route to approval or revision based on the review verdict.
        """
        if is_approved:
            return "approved"
        return "revise"

    @listen("approved")
    def finalize_approved(self, _review_result: str):
        """
        Return the original plan if it passed review.
        """
        try:
            final_report = self._get_finalization_crew().kickoff(
                inputs=self._build_revision_inputs()
            )
            report_text = self._result_to_text(final_report)
            self.state.final_result = report_text
            return self.state.final_result
        except Exception as e:
            self.state.last_error = str(e)
            self.state.final_result = f"Error: {str(e)}"
            raise ValueError(e)

    @listen("revise")
    def revise_plan(self, _review_result: str):
        """
        Revise the draft plan using the review feedback.
        """
        self.state.revision_count += 1
        try:
            revision_result = self._get_revision_crew().kickoff(
                inputs=self._build_revision_inputs()
            )
            revised_plan = self._result_to_text(revision_result)
            self.state.revised_plan = revised_plan
            self.state.final_result = revised_plan
            return revised_plan
        except Exception as e:
            self.state.last_error = str(e)
            self.state.final_result = f"Error: {str(e)}"
            raise ValueError(e)

    @router(revise_plan)
    def route_after_revised_plan(self, _revised_result: str):
        if self.state.revision_count < self.state.max_revisions:
            return "review"
        return "approved"

    # TODO: crewAI has a bug generating Pydantic model output on local LLMs
    def _is_approved(self, result) -> bool:
        raw = self._result_to_text(result).lower()
        match = re.search(r"approved\s*:\s*(true|false)", raw)
        if match:
            return match.group(1) == "true"
        return "approved" in raw and "not approved" not in raw

    def _validate_initial_state(self):
        if not self.state.issue:
            raise ValueError("State 'issue' must be provided.")
        if not self.state.code_path:
            raise ValueError("State 'code_path' must be provided.")

    def kickoff(self, issue: str, code_path: str, **kwargs):
        """
        Convenience method to start the flow with inputs.
        """
        self.state.issue = issue
        self.state.code_path = code_path
        # Override max_revisions if passed
        if 'max_revisions' in kwargs:
            self.state.max_revisions = kwargs['max_revisions']
        return super().kickoff()
