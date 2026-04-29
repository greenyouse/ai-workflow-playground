# Planning With Context

This is the LangGraph implementation workflow with the `repo_context_collector` to scrape local files.

Try running this with:
```bash
source .venv/bin/activate
python -m ai_dojo.graphs.implementation_graph "./src/ai_dojo/utils/repo_context_collector.py" "The repo_context_collector currently used should classify more data for each file. Each file should record the: programming language, framework used, and the test framework used if that is applicable."
```

Check the [implementation_draft.md](./implementation_draft.md) output for an example of what was generated.
