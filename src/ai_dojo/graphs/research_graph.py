"""
Researches a topic with LLM knowledge (no external search) and
returns a report of what the LLM knows about the subject.

graph structure:
    research node -> reporting node -> write_report node

Run example:
    graph research "AI LLMs"
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, field_validator
from typing import TypedDict

from langchain.agents import create_agent
from langgraph.graph import END, START, StateGraph

class ResearchState(BaseModel):
    topic: str
    current_year: str = str(datetime.now().year)
    research_bullets: list[str] = []
    report: str = ""
    report_path: Path | str = "report.md"
    output_file: str | None = None

    @field_validator("research_bullets", mode="before")
    @classmethod
    def parse_bullets(cls, v: str) -> list[str]:
        # Splitting by newline and stripping common bullet characters
        bullets = [line.strip("-•* \t") for line in v.splitlines() if line.strip()]
        # High-level validation: Ensure we actually got content
        if not bullets:
            raise ValueError("Researcher returned an empty list of bullets")
        return bullets

    @field_validator("report")
    @classmethod
    def validate_report(cls, v: str) -> str:
        if len(v) < 100:
            raise ValueError("Generated report is too short to be valid.")
        return v

def _llm():
    return create_agent(
    model="ollama:gemma4",
    )

def research_node(state: ResearchState) -> dict:
    """Researches a topic and returns a bulleted list of information on the topic."""
    topic = state.topic
    current_year = state.current_year

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


def reporting_node(state: ResearchState) -> dict:
    topic = state.topic
    research_bullets = state.research_bullets

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

def write_report_node(state: ResearchState) -> dict:
    report_path = Path(state.report_path)
    report_path.write_text(state.report, encoding="utf-8")
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
    print(f"Wrote {final_state.report_path}")