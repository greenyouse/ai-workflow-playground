import sys
import types

# Provide lightweight stubs for `crewai` so tests can import project modules
crewai = types.ModuleType("crewai")

class Agent:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.config = kwargs.get("config")
        self.tools = kwargs.get("tools", [])
        self.verbose = kwargs.get("verbose", False)

class Crew:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.agents = kwargs.get("agents", [])
        self.tasks = kwargs.get("tasks", [])
        self.process = kwargs.get("process")
        self.verbose = kwargs.get("verbose", False)

class Process:
    sequential = "sequential"

class Task:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.config = kwargs.get("config")
        self.context = kwargs.get("context", [])
        self.output_file = kwargs.get("output_file")

class Flow:
    def __init__(self, *args, **kwargs):
        self.state = {}

crewai.Agent = Agent
crewai.Crew = Crew
crewai.Process = Process
crewai.Task = Task
crewai.Flow = Flow
sys.modules["crewai"] = crewai

# crewai.project with decorators used in crew classes
project = types.ModuleType("crewai.project")

def CrewBase(cls):
    return cls

def agent(func):
    return func

def crew(func):
    return func

def task(func):
    return func

project.CrewBase = CrewBase
project.agent = agent
project.crew = crew
project.task = task
sys.modules["crewai.project"] = project

# Minimal BaseAgent stub
base_agent = types.ModuleType("crewai.agents.agent_builder.base_agent")

class BaseAgent:
    pass

base_agent.BaseAgent = BaseAgent
sys.modules["crewai.agents.agent_builder.base_agent"] = base_agent

# Minimal flow module stubs used by implementation flow tests
flow_package = types.ModuleType("crewai.flow")
flow_package.__path__ = []
sys.modules["crewai.flow"] = flow_package

flow_module = types.ModuleType("crewai.flow.flow")

def start(*args, **kwargs):
    def decorator(func):
        return func

    return decorator

def listen(*args, **kwargs):
    def decorator(func):
        return func

    return decorator

def router(*args, **kwargs):
    def decorator(func):
        return func

    return decorator

flow_module.Flow = Flow
flow_module.start = start
flow_module.listen = listen
flow_module.router = router
sys.modules["crewai.flow.flow"] = flow_module
