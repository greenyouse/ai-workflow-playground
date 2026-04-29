from __future__ import annotations

import argparse
from pathlib import Path

from ai_dojo.graphs.research_graph import run as run_research
from ai_dojo.graphs.idea_planning_graph import run as run_idea_planning
from ai_dojo.graphs.implementation_graph import run as run_implementation
from ai_dojo.graphs.tdd_graph import run as run_tdd


def main() -> None:
    parser = argparse.ArgumentParser(prog="ai-dojo")
    subparsers = parser.add_subparsers(dest="graph", required=True)

    research = subparsers.add_parser("research")
    research.add_argument("--topic", default="AI LLMs")
    research.add_argument("--output", default="report.md")

    idea = subparsers.add_parser("idea-planning")
    idea.add_argument("--code-path", required=True)
    idea.add_argument("--idea", required=True)
    idea.add_argument("--output", default="project_plan.md")

    implementation = subparsers.add_parser("implementation")
    implementation.add_argument("--code-path", required=True)
    implementation.add_argument("--issue", required=True)
    implementation.add_argument("--max-revisions", type=int, default=3)
    implementation.add_argument("--output", default="implementation_draft.md")

    tdd = subparsers.add_parser("tdd")
    tdd.add_argument("--code-path", required=True)
    tdd.add_argument("--plan", required=True)
    tdd.add_argument("--max-revisions", type=int, default=1)
    tdd.add_argument("--output", default="failing_tests_draft.py")

    args = parser.parse_args()

    if args.graph == "research":
        result = run_research(topic=args.topic, report_path=args.output)

    elif args.graph == "idea-planning":
        result = run_idea_planning(
            idea=args.idea,
            code_path=args.code_path,
            project_plan_path=args.output,
        )

    elif args.graph == "implementation":
        result = run_implementation(
            issue=args.issue,
            code_path=args.code_path,
            max_revisions=args.max_revisions,
            implementation_draft_path=args.output,
        )

    elif args.graph == "tdd":
        plan = Path(args.plan).read_text(encoding="utf-8")
        result = run_tdd(
            implementation_plan=plan,
            code_path=args.code_path,
            max_revisions=args.max_revisions,
            failing_tests_path=args.output,
        )

    else:
        raise SystemExit(f"Unknown graph: {args.graph}")

    print("Done.")


if __name__ == "__main__":
    main()