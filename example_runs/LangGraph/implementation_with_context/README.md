# Planning With Context

This is the LangGraph implementation workflow with the `repo_context_collector` to scrape local files.

Try running this with:
```bash
source .venv/bin/activate
python -m ai_dojo.graphs.idea_planning_graph ./src "$(cat example_runs/crewAI/critic_loop_implementation/implementation_draft.md)"
```

Check the [implementation_draft.md](./implementation_draft.md) output for an example of what was generated.
