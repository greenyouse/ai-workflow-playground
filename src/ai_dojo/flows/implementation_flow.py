from datetime import datetime
from crewai.flow.flow import Flow, listen, router, start
from ai_dojo.crews.implementation_planner.implementation_planner_crew import ImplementationPlannerCrew


class ImplementationFlow(Flow):
    max_revisions: int = 2

    @start()
    def run_implementation(self):
        self.state["revisions"] = 0
        inputs = self._build_inputs()
        result = ImplementationPlannerCrew().implementation_planner_crew().kickoff(inputs=inputs)
        self.state["result"] = result
        return result

    @router(run_implementation)
    def check_quality(self, _result):
        if self.state["revisions"] < self.max_revisions:
            return "needs_revision"
        return "done"

    @listen("needs_revision")
    def revise(self):
        self.state["revisions"] += 1
        inputs = self._build_inputs()
        inputs["revision_round"] = str(self.state["revisions"])
        inputs["previous_result"] = getattr(self.state["result"], "raw", str(self.state["result"]))

        result = ImplementationPlannerCrew().implementation_planner_crew().kickoff(inputs=inputs)
        self.state["result"] = result
        return result

    @listen("done")
    def finish(self, _result):
        return self.state["result"]

    def _build_inputs(self) -> dict[str, str]:
        issue = self.state.get("issue", "")
        current_year = self.state.get("current_year", str(datetime.now().year))
        return {
            "issue": issue,
            "idea": issue,
            "topic": issue,
            "current_year": current_year,
        }