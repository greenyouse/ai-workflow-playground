# Basic Planning

This is the first run through the LangGraph planner without any optimizations.

It's just pairs custom agents with custom tasks.

The context is supposed to be passed in but the LLM just hallucinates it because there's no
file system lookup. Basically the plan looks very "interesting" (hehe).

Try running this with:
```bash
source .venv/bin/activate
graph idea-planning --code-path ./src --idea "$(cat example_runs/crewAI/critic_loop_implementation/implementation_draft.md)"
```

Check the [project_plan.md](./project_plan.md) output for an example of what was generated.
