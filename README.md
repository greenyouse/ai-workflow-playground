# AiDojo Crew

Hey this is just a personal project for playing around with workflow systems. It uses [crewAI](https://crewai.com) right now but the framework isn't important.

It'll have a a few general software helper workflows that help augment software engineers doing work.
It's mostly for me to practicing building AI workflow systems though.

Workflows so far:
- default crewAI research workflow (boilerplate, will delete)
- planning for project planning

## Disclaimer
I set this to run against a local [Gemma4](https://deepmind.google/models/gemma/) model via [Ollama](https://ollama.com/).

Make sure to work through that setup first before running the repo.

It's just the gemma4:e4b model with 128K context so it run on most computers.

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
run_crew research
run_crew planning {idea}
```

These commands will trigger the differ ai-dojo Crew workflows. They run agnts and assign them tasks to work on.

See the [examples](./example_runs/README.md) to see examples of the workflow performance.

### Project structure
- Modify `src/ai_dojo/config/agents.yaml` to define your agents
- Modify `src/ai_dojo/config/tasks.yaml` to define your tasks
- Modify `src/ai_dojo/crew.py` to add your own logic, tools and specific args
- Modify `src/ai_dojo/main.py` to add custom inputs for your agents and tasks

## Roadmap
The general idea is to start with basic workflows, then augment them with progressively more powerful features:
- RAG
- Tools
- Validation
- Lightweight Planning
- Tracing
- Evals
- Persistance
- Templates + Approvals
- Repo memories + Adaptive retrieval
- Multi-agent workflows
- Creating a workflow platform
  - APIs
  - Async processing
  - UI
