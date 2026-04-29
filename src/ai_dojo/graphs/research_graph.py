"""LangGraph migration of ai_dojo.crews.research.

CrewAI version:
    researcher -> research_task -> reporting_analyst -> reporting_task -> report.md

LangGraph version:
    research node -> reporting node -> write_report node

Run example:
    python -m ai_dojo.graphs.research_graph "AI LLMs"
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import TypedDict

from langchain.agents import create_agent
from langgraph.graph import END, START, StateGraph


class ResearchState(TypedDict, total=False):
    topic: str
    current_year: str
    research_bullets: str
    report: str
    report_path: str
    output_file: str


def _llm():
    return create_agent(
    model="ollama:gemma4",
    )

def research_node(state: ResearchState) -> ResearchState:
    """Replacement for CrewAI researcher + research_task."""
    topic = state["topic"]
    current_year = state.get("current_year", str(datetime.now().year))

    prompt = f"""
You are a {topic} Senior Data Researcher.

Goal: Uncover cutting-edge developments in {topic}.

Backstory: You're a seasoned researcher with a knack for uncovering the latest
developments in {topic}. You're known for finding relevant information and
presenting it clearly and concisely.

Task: Conduct thorough research about {topic}. Make sure you find interesting
and relevant information given the current year is {current_year}.

Expected output: A list with 10 bullet points of the most relevant information
about {topic}.
""".strip()

    messages = [{"role": "user", "content": prompt}]
    response = _llm().invoke({"messages": messages})
    last_message = response["messages"][-1]
    return {"research_bullets": last_message.content}


def reporting_node(state: ResearchState) -> ResearchState:
    """Replacement for CrewAI reporting_analyst + reporting_task."""
    topic = state["topic"]
    research_bullets = state["research_bullets"]

    prompt = f"""
You are a {topic} Reporting Analyst.

Goal: Create detailed reports based on {topic} data analysis and research findings.

Backstory: You're a meticulous analyst with a keen eye for detail. You're known
for turning complex data into clear and concise reports, making it easy for
others to understand and act on the information.

Context from researcher:
{research_bullets}

Task: Review the context you got and expand each topic into a full section for
a report. Make sure the report is detailed and contains any and all relevant
information.

Expected output: A fully fledged report with the main topics, each with a full
section of information. Format as markdown without code fences.
""".strip()

    messages = [{"role": "user", "content": prompt}]
    response = _llm().invoke({"messages": messages})
    last_message = response["messages"][-1]
    return {"report": last_message.content}



def write_report_node(state: ResearchState) -> ResearchState:
    """Explicit replacement for CrewAI Task(output_file='report.md')."""
    report_path = Path(state.get("report_path", "report.md"))
    report_path.write_text(state["report"], encoding="utf-8")
    return {"report_path": str(report_path)}


def build_research_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("research", research_node)
    graph.add_node("reporting", reporting_node)
    graph.add_node("write_report", write_report_node)

    graph.add_edge(START, "research")
    graph.add_edge("research", "reporting")
    graph.add_edge("reporting", "write_report")
    graph.add_edge("write_report", END)

    return graph.compile()


def run(topic: str = "AI LLMs", report_path: str = "report.md") -> ResearchState:
    app = build_research_graph()
    return app.invoke(
        {
            "topic": topic,
            "current_year": str(datetime.now().year),
            "report_path": report_path,
        }
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="python -m ai_dojo.graphs.research_graph"
    )
    parser.add_argument("--topic", default="AI LLMs")
    parser.add_argument("--output", default="report.md")
    args = parser.parse_args()

    final_state = run(topic=args.topic, report_path=args.output)
    print(f"Wrote {final_state['report_path']}")