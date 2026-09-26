# run this from week-4 folder as uv run day-4.py for proper sandbox file path

# - LangChain Core provides the low-level building blocks such as models, messages, prompts, tools, and runnables.
# - LangChain provides higher-level abstractions for common LLM applications and standard tool-calling agents.
# - LangChain's `create_agent()` uses a predefined agent execution pattern (model → tools → model); it does not automatically design arbitrary application-specific graph edges.
# - LangGraph provides explicit stateful workflow orchestration, where we define nodes, edges, routing, loops, persistence, and human-in-the-loop behavior.
# - Deep Agents builds on the LangChain/LangGraph ecosystem and adds higher-level machinery for complex, long-running tasks, such as planning, subagents, filesystem/context management, and task delegation.
# - The abstraction progression is: native APIs → our own agent loop → LangGraph for explicit orchestration → LangChain for standard agent abstractions → Deep Agents for complex autonomous task execution.

import os

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from dotenv import load_dotenv
from langchain_community.tools import GoogleSerperRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from slide_kit import build_slide

load_dotenv(override=True)


def get_file_path(filename: str) -> str:
    """Return a path relative to this Python file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, filename)


def draw_graph(agent, filename: str):
    """Save a visual representation of a LangGraph graph."""
    with open(get_file_path(filename), "wb") as file:
        file.write(agent.get_graph().draw_mermaid_png())


search = GoogleSerperRun(api_wrapper=GoogleSerperAPIWrapper())

sandbox = os.path.abspath("sandbox")
os.makedirs(sandbox, exist_ok=True)
model = ChatOpenAI(model="gpt-5.4-mini")


def researcher_demo():
    researcher = create_deep_agent(
        model=model,
        tools=[search],
        system_prompt=(
            "You are a research analyst. Plan your work with your todo tool, "
            "research with the search tool, and write your findings as a tidy markdown briefing to a file."
        ),
        backend=FilesystemBackend(root_dir=sandbox, virtual_mode=True),
    )

    draw_graph(researcher, "researcher.png")

    brief = """
    Our company is planning to move its sales fleet to electric vehicles.
    Research the public EV charging landscape in the US: find out roughly how many public charging points there are,
    and pick out two major charging networks a fleet could rely on.
    Write a one page markdown briefing, with a heading and a short section for each, to the file charging.md.
    """
    result = researcher.invoke({"messages": [{"role": "user", "content": brief}]})
    print(result["messages"][-1].content)

    tools_used = [
        tc["name"]
        for m in result["messages"]
        for tc in (getattr(m, "tool_calls", []) or [])
    ]
    print("Tools the agent called, in order:")
    print(tools_used)


def lead_demo():
    research_ev_instructions = """
    You research one electric vehicle using the search tool and return three concise facts
    that a fleet buyer would care about, such as price, range and charging.
    """

    overall_instructions = """
    You write comparison briefings for a company choosing electric vehicles for its sales fleet.
    For each vehicle, delegate the research to your vehicle-researcher sub-agent,
    then write a markdown comparison to a file, ending with a clear recommendation.
    """

    research_subagent = {
        "name": "vehicle-researcher",
        "description": "Researches a single electric vehicle and returns a short list of facts about it.",
        "system_prompt": research_ev_instructions,
    }

    lead = create_deep_agent(
        model=model,
        tools=[search],
        system_prompt=overall_instructions,
        subagents=[research_subagent],
        backend=FilesystemBackend(root_dir=sandbox, virtual_mode=True),
    )
    draw_graph(lead, "lead.png")

    mission = """
    Compare the Tesla Model Y and the Ford Mustang Mach-E as candidates for our 100-car sales fleet.
    Research each vehicle, then write a short markdown comparison with a recommendation to fleet.md.
    """

    result = lead.invoke({"messages": [{"role": "user", "content": mission}]})
    tools_used = [
        tc["name"]
        for m in result["messages"]
        for tc in (getattr(m, "tool_calls", []) or [])
    ]
    print("Tools the lead agent called:", tools_used)


@tool
def create_slide(title: str, key_points: list[str], recommendation: str) -> str:
    """Create a one-slide PowerPoint in the Voltway Research house style, saved as fleet.pptx."""
    build_slide(title, key_points, recommendation, os.path.join(sandbox, "fleet.pptx"))
    return "Saved the slide to /fleet.pptx"


def presenter_demo():
    slide_maker = {
        "name": "slide-maker",
        "description": "Turns a finished recommendation into a one-slide PowerPoint deck.",
        "system_prompt": "You turn research recommendations into slides, following your fleet-slide skill.",
        "tools": [create_slide],
        "skills": ["/skills/"],
    }

    presenter = create_deep_agent(
        model=model,
        subagents=[slide_maker],
        system_prompt="You prepare research for presentation by delegating to your slide-maker sub-agent.",
        backend=FilesystemBackend(root_dir=sandbox, virtual_mode=True),
    )

    result = presenter.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Read fleet.md and have a one-slide deck made of its recommendation.",
                }
            ]
        }
    )
    print(result["messages"][-1].content)


def main():
    researcher_demo()

    lead_demo()

    presenter_demo()


if __name__ == "__main__":
    main()
