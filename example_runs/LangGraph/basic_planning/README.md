# Basic Planning

This is the first run through the LangGraph planner without any optimizations.

It's just pairs custom agents with custom tasks.

The context is supposed to be passed in but the LLM just hallucinates it because there's no
file system lookup. Basically the plan looks very "interesting" (hehe).

Try running this with:
```bash
source .venv/bin/activate
python -m ai_dojo.graphs.idea_planning_graph "./src/ai_dojo/utils/repo_context_collector.py" "The repo_context_collector currently used should classify more data for each file. Each file should record the: programming language, framework used, and the test framework used if that is applicable."
```

Check the [project_plan.md](./project_plan.md) output for an example of what was generated.
