# Implementation with local context

This is the same implementation workflow but with a repo_context_collector
to provide local files for context.

Try running this with:
```bash
source .venv/bin/activate
run_crew implementation {file_path} {issue}
```

Example project idea prompt I used:

```text
run_crew implementation "./src/ai_dojo/utils/repo_context_collector.py" "The repo_context_collector currently used should classify more data for each file. Each file should record the: programming language, framework used, and the test framework used if that is applicable."

```

Check out the [results here](./implementation_draft.md).
