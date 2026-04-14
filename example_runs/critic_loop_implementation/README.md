
# Basic Planning

This is the same implementation workflow but with a critc loop added.

If the critic doesn't approve of the output, the output can be revised up to 2 times.

Try running this with:
```bash
source .venv/bin/activate
run_crew impelentation {issue}
```

Example project idea prompt I used:

```text
Your current crewAI workflow uses agent/task prompts, but task outputs are still fairly loose. Add a small structured output format for planner and researcher results so downstream tasks receive more consistent inputs.
```

Check out the [results here](./implementation_draft.md).
