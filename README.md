# AiDojo Crew

Hey this is just a personal project for playing around with workflow systems. It uses [crewAI](https://crewai.com) and [LangGraph](https://www.langchain.com/langgraph) right now but the framework isn't important.

It'll have a a few general software helper workflows that help augment software engineers doing work.
It's mostly for me to practice building AI workflow systems though.

LanGraph is what I'm going to use going forward. There are some graphs (workflows) that you can try now. Go through the install docs, then run `graph` to see what's available.

## Disclaimer
I set this to run against a local [Gemma4](https://deepmind.google/models/gemma/) model via [Ollama](https://ollama.com/).

Make sure to work through that setup first before running the repo.

It's just the gemma4:e4b model with 128K context so it should run on most computers.

## Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

(Optional) Lock the dependencies and install them by using the CLI command:
```bash
crewai install
```
## Running the Project

Here's how to run the two workflows so far:

```bash
source .venv/bin/activate
graph # displays a help menu with all the workflows available
# a couple example workflows
graph research
graph idea-planning --code-path {path} --idea {idea}
```

These commands will trigger the differ ai-dojo Crew workflows. They run agents and assign them tasks to work on.

See [these examples](./example_runs/README.md) for the workflows in action.

## Roadmap
The general idea is to start with basic workflows, then augment them with progressively more powerful features:
- RAG
- Tools
- Validation
- Lightweight Planning
- Tracing
- Evals
- Persistence
- Templates + Approvals
- Repo memories + Adaptive retrieval
- Multi-agent workflows
- Creating a workflow platform
  - APIs
  - Async processing
  - UI
