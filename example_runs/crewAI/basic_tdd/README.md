# Basic TDD

This creates an initial TDD file with failing tests based on the existing codebase and an implementation plan.

This takes a path for the relevant code to use for generating the tests as the first arg. That recursively pulls all the files at the path into context to guide the test implementation. Based on that, the code will copy your programming language, test framework, and coding style.

The output is basically garbage right now because the plan it gets is bad. I'll reuse the repo context collector to improve the implementation plan and then update the example here. It should help a lot.

Try running this with:
```bash
source .venv/bin/activate
run_crew tdd {relevant_code} {implementation_plan}
```

Example command I used:

```text
run_crew tdd ./src/ai_dojo "$(cat example_runs/crewAI/critic_loop_implementation/implementation_draft.md)"
```

Check out the [results here](./failing_tests_draft.py).
