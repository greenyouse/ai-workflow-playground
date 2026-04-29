# Basic TDD

This is the LangGraph TDD workflow. 

This takes an implementation plan and generates some failing tests, TDD style.

Try running this with:
```bash
source .venv/bin/activate
graph tdd --code-path "./src/ai_dojo/utils/repo_context_collector.py" --plan example_runs/LangGraph/implementation_with_context/implementation_draft.md
```

Check the [failing_tests_draft.py](./failing_tests_draft.py) output for an example of what was generated.
