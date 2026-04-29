# Planning With Context

This is the LangGraph planner with the `repo_context_collector` to scrape local files.

The results still aren't great but at least it's not hallucinating content as much.

Try running this with:
```bash
source .venv/bin/activate
graph idea-planning --code-path ./src --idea "$(cat example_runs/crewAI/critic_loop_implementation/implementation_draft.md)"
```

Check the [project_plan.md](./project_plan.md) output for an example of what was generated.
