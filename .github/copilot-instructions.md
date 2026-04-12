# AI Dojo CrewAI Project — Coding Conventions

This is a CrewAI crew project (`ai_dojo`) that orchestrates multiple AI agents to research and report on topics. **For comprehensive CrewAI API reference, see [AGENTS.md](../AGENTS.md)**.

## Quick Start

### Environment & Dependencies

- **Python**: >=3.10, <3.14
- **Package manager**: `uv` (not pip)
- **Core dependency**: `crewai[tools]==1.14.1`
- **Configuration**: Add `OPENAI_API_KEY` to `.env`

### Essential Commands

```bash
crewai run              # Execute the crew with default inputs
crewai train -n 5      # Train crew for 5 iterations
crewai test            # Run crew quality tests
crewai log-tasks-outputs  # View latest execution results
```

**Scripts in pyproject.toml**:

- `ai_dojo` / `run_crew` → `main.py:run()` — Run crew with default topic ("AI LLMs")
- `train` → `main.py:train()` — Train crew on LLM topic
- `test` → `main.py:test()` — Run test harness
- `replay` → `main.py:replay()` — Replay from specific task ID

## Project Structure

```
src/ai_dojo/
  crew.py              # @CrewBase class orchestrating agents and tasks
  main.py              # Entry points for run, train, test, replay
  config/
    agents.yaml        # Agent definitions (role, goal, backstory)
    tasks.yaml         # Task definitions (description, expected_output)
  tools/
    custom_tool.py     # Custom tool template
```

### Current Agents

- **researcher**: Uncovers cutting-edge developments in {topic}
- **reporting_analyst**: Creates detailed reports from research findings

### Output

- Default output file: `report.md` (in project root)

## Code Patterns & Conventions

### Agent Definition (@agent decorator)

```python
@agent
def researcher(self) -> Agent:
    return Agent(
        config=self.agents_config['researcher'],  # type: ignore[index]
        tools=[],  # Add tool instances here if needed
        verbose=True
    )
```

- Always add `# type: ignore[index]` to config dict access
- Agent method name must exactly match the YAML key
- Use `verbose=True` for development

### Task Definition (@task decorator)

```python
@task
def research_task(self) -> Task:
    return Task(
        config=self.tasks_config['research_task'],  # type: ignore[index]
        output_file='path/to/output.md'     # Optional: save output
    )
```

- Access config via `self.tasks_config[key_matching_yaml]`
- Always include `# type: ignore[index]`
- Last task in sequence can specify `output_file`

### Crew Assembly (@crew decorator)

```python
@crew
def crew(self) -> Crew:
    return Crew(
        agents=self.agents,
        tasks=self.tasks,
        process=Process.sequential,  # or Process.hierarchical
        verbose=True
    )
```

- Always use `Process.sequential` unless hierarchical delegation is needed
- `self.agents` and `self.tasks` are auto-populated by @agent/@task decorators

### YAML Agent Configuration

```yaml
researcher:
  role: >
    {topic} Senior Data Researcher    # Use {variable} for interpolation
  goal: >
    Uncover cutting-edge developments in {topic}
  backstory: >
    You're a seasoned researcher...
    Multiple lines supported
```

- Use `{topic}` and `{current_year}` variables (passed via `inputs` dict in `main.py`)
- Keep text indented and wrapped with `>`
- Long backstories improve agent behavior

### YAML Task Configuration

```yaml
research_task:
  description: >
    Conduct thorough research...
    Include context about {topic} and {current_year}
  expected_output: >
    A bullet-point list of 10 insights
  agent: researcher # Must match @agent method name
```

- `expected_output` is critical for task completion criteria
- Variables like `{topic}` are auto-interpolated from inputs
- Task name must match @task method name

### Running Crew in main.py

```python
def run():
    inputs = {
        'topic': 'AI LLMs',
        'current_year': str(datetime.now().year)
    }
    AiDojo().crew().kickoff(inputs=inputs)
```

- Provide all `{variables}` mentioned in agents.yaml and tasks.yaml
- Use `datetime.now().year` for current year variable
- Wrap in try/except to catch execution errors

## Common Development Tasks

### Adding a New Agent

1. Create `@agent` method in `crew.py` with `verbose=True`
2. Add corresponding definition in `config/agents.yaml` with role/goal/backstory
3. (Optional) Add tools to the agent if needed from `crewai_tools` or custom tools

### Adding a New Task

1. Create `@task` method in `crew.py`
2. Add definition in `config/tasks.yaml` with description/expected_output/agent
3. Chain task dependencies via `context=[previous_task()]` if needed
4. Add required input variables to `inputs` dict in `main.py`

### Adding a Custom Tool

1. Extend `BaseTool` in `tools/custom_tool.py` (or create new file in `tools/`)
2. Define `name`, `description`, `args_schema` (Pydantic model)
3. Implement `_run()` method
4. Add tool instance to agent: `tools=[MyCustomTool()]`
5. See [AGENTS.md](../AGENTS.md#custom-tools) for full template

### Testing Changes

```bash
crewai test                    # Default: 2 iterations, gpt-4o-mini
crewai test -n 5 -m gpt-4o   # Custom iterations and model
crewai train -n 3 -f training.json  # Train and save metrics
```

## Debugging & Troubleshooting

### Check Installed Version & Latest Release

```bash
python -c "import crewai; print(crewai.__version__)"
curl -s https://pypi.org/pypi/crewai/json | jq '.releases | keys | sort | .[-1]'
```

### View Latest Task Outputs

```bash
crewai log-tasks-outputs
```

### Replay Specific Task

```bash
crewai replay -t <task_id>    # Get task_id from log-tasks-outputs
```

### Common Errors

| Error                           | Cause                              | Fix                                                      |
| ------------------------------- | ---------------------------------- | -------------------------------------------------------- |
| `KeyError` on agent/task config | Method name doesn't match YAML key | Ensure `@agent researcher` matches `researcher:` in YAML |
| `{topic} not interpolated`      | Variable not in inputs dict        | Add `'topic': 'value'` to inputs in main.py              |
| `Tool not found for agent`      | Tool not added to agent instance   | Add `tools=[MyTool()]` to Agent() constructor            |
| `Task context reference fails`  | Task not yet decorated             | Use `context=[self.previous_task()]` only after @task    |

## File Locations & Conventions

| What           | Where                            | Notes                                            |
| -------------- | -------------------------------- | ------------------------------------------------ |
| Crew class     | `src/ai_dojo/crew.py`            | Edit agents/tasks here; use @CrewBase on class   |
| Agent defs     | `src/ai_dojo/config/agents.yaml` | Inline variables with `{variable_name}`          |
| Task defs      | `src/ai_dojo/config/tasks.yaml`  | Keep description/expected_output clear           |
| Custom tools   | `src/ai_dojo/tools/`             | All BaseTool subclasses go here                  |
| Entry points   | `src/ai_dojo/main.py`            | Modify run() inputs or add new functions         |
| Final output   | `report.md`                      | Generated by reporting_task (in root)            |
| Crew reference | `AGENTS.md`                      | Comprehensive CrewAI API docs (do NOT duplicate) |

## Key References

- **[AGENTS.md](../AGENTS.md)** — Complete CrewAI API reference, tool library, architecture patterns, memory/knowledge systems
- **[CrewAI Docs](https://docs.crewai.com)** — Official documentation
- **[crewai[tools] Changelog](https://github.com/crewAIInc/crewAI/releases)** — Latest changes and features (check this before major modifications)

## Anti-Patterns to Avoid

❌ **Don't** hardcode `OPENAI_API_KEY` in code — use `.env`  
❌ **Don't** use `Process.hierarchical` without `manager_llm` or `manager_agent`  
❌ **Don't** skip `# type: ignore[index]` on config dict access  
❌ **Don't** put complicated business logic in `crew.py` — keep it minimal  
❌ **Don't** forget to add new `{variables}` to the inputs dict in `main.py`  
❌ **Don't** leave commented-out code in agent/task methods  
❌ **Don't** use `pip install` — always use `uv add` for dependencies

## Version-Specific Guidance

This project uses **crewai[tools]==1.14.1**. Before modifying crew code:

1. Check if a newer version is available: `pip index versions crewai`
2. Review [changelog](https://docs.crewai.com/en/changelog) for breaking changes
3. Update AGENTS.md in this project if API changes are made

---

**Last updated**: April 2026  
**Project type**: CrewAI crew (sequential process)  
**Maintainers**: See git history for contributors
