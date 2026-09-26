import asyncio
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from sidekick_tools import search, send_email, wikipedia_lookup

load_dotenv(override=True)


def get_file_path(filename: str) -> str:
    """Return a path relative to this Python file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, filename)


def draw_graph(agent, filename: str):
    """Save a visual representation of a LangGraph graph."""
    with open(get_file_path(filename), "wb") as file:
        file.write(agent.get_graph().draw_mermaid_png())


simple_worker = create_agent(
    model="openai:gpt-5.4-mini",
    tools=[search, send_email, wikipedia_lookup],
    system_prompt="You are Sidekick, a helpful personal assistant. Use your tools to complete the task.",
    checkpointer=InMemorySaver(),
)
draw_graph(simple_worker, "simple_worker.png")


async def ask(worker, message):
    config = {"configurable": {"thread_id": "simple-sidekick"}}
    result = await worker.ainvoke(
        {"messages": [{"role": "user", "content": message}]}, config=config
    )
    return result["messages"][-1].content


async def simple_worker_demo():
    reply = await ask(
        simple_worker,
        "Search for who won the Nobel Prize in Physics in 2023 and send an email with a short summary.",
    )
    print(reply)


@tool
def book_meeting(person: str, day: str) -> str:
    """Book a meeting with a person on a given day."""
    return f"Meeting booked with {person} on {day}."


async def human_in_the_loop_demo():
    approval_agent = create_agent(
        model="openai:gpt-5.4-mini",
        tools=[book_meeting],
        system_prompt="You are a scheduling assistant. Use the book_meeting tool.",
        middleware=[HumanInTheLoopMiddleware(interrupt_on={"book_meeting": True})],
        checkpointer=InMemorySaver(),
    )

    config = {"configurable": {"thread_id": "approval-demo"}}
    result = await approval_agent.ainvoke(
        {
            "messages": [
                {"role": "user", "content": "Book a meeting with Sam on Friday."}
            ]
        },
        config,
    )

    interrupt = result["__interrupt__"][0]
    print("The agent paused and is asking for approval:")
    print(interrupt.value["action_requests"][0]["description"])

    resumed = await approval_agent.ainvoke(
        Command(resume={"decisions": [{"type": "approve"}]}), config
    )
    print(resumed["messages"][-1].content)

    config = {"configurable": {"thread_id": "rejection-demo"}}
    result = await approval_agent.ainvoke(
        {
            "messages": [
                {"role": "user", "content": "Book a meeting with Sam on Friday."}
            ]
        },
        config,
    )

    interrupt = result["__interrupt__"][0]
    print("The agent paused and is asking for approval:")
    print(interrupt.value["action_requests"][0]["description"])

    resumed = await approval_agent.ainvoke(
        Command(
            resume={
                "decisions": [
                    {"type": "reject", "message": "Rejected - no meetings on Fridays"}
                ]
            }
        ),
        config,
    )
    print(resumed["messages"][-1].content)


async def main():
    # await simple_worker_demo()
    await human_in_the_loop_demo()


if __name__ == "__main__":
    asyncio.run(main())
