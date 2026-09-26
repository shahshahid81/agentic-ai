import asyncio
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field

load_dotenv(override=True)


def get_file_path(filename: str) -> str:
    """Return a path relative to this Python file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, filename)


def draw_graph(agent, filename: str):
    """Save a visual representation of a LangGraph graph."""
    with open(get_file_path(filename), "wb") as file:
        file.write(agent.get_graph().draw_mermaid_png())


@tool
def get_weather(city: str) -> str:
    """Return today's weather for a city."""
    pretend = {"London": "rainy, 14 degrees", "Rome": "sunny, 27 degrees"}
    return pretend.get(city, "clear, 20 degrees")


@tool
def get_population(city: str) -> str:
    """Return the population of a city."""
    pretend = {"London": "8.9 million", "Rome": "2.8 million"}
    return pretend.get(city, "unknown")


async def simple_agent_demo():
    # internally creates a lang graph with state, node and edges.
    agent = create_agent(
        model="openai:gpt-5.4-mini",
        system_prompt="You are a helpful assistant who answers concisely.",
    )

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "What is the Model Context Protocol, in two sentences?",
                }
            ]
        }
    )
    print(result["messages"][-1].content)

    # async version of agent
    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "What is the Model Context Protocol, in two sentences?",
                }
            ]
        }
    )
    print(result["messages"][-1].content)


async def travel_agent_tools_demo():
    # internally creates a lang graph with state, node including tools and edges.
    agent = create_agent(
        model="openai:gpt-5.4-mini",
        system_prompt="You are a travel assistant. Use your tools to answer questions about cities.",
        tools=[get_weather, get_population],
    )

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "What is the weather and population of Rome?",
                }
            ]
        }
    )
    print(result["messages"][-1].content)

    draw_graph(agent, "travel_agent_tools_demo.png")


async def travel_agent_memory_demo():
    memory_agent = create_agent(
        model="openai:gpt-5.4-mini",
        system_prompt="You are a travel assistant. Use your tools to answer questions about cities.",
        tools=[get_weather],
        checkpointer=MemorySaver(),
    )

    config = {"configurable": {"thread_id": "trip-planning"}}
    memory_agent.invoke(
        {"messages": [{"role": "user", "content": "I am planning a trip to London."}]},
        config=config,
    )
    result = memory_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "What is the weather like where I am going on my trip?",
                }
            ]
        },
        config=config,
    )
    print(result["messages"][-1].content)

    draw_graph(memory_agent, "travel_agent_memory_demo.png")


class CityReport(BaseModel):
    city: str = Field(description="The city name")
    weather: str = Field(description="A short weather description")
    population: str = Field(description="The population")


async def travel_agent_structured_output_demo():
    report_agent = create_agent(
        model="openai:gpt-5.4-mini",
        tools=[get_weather],
        response_format=CityReport,
    )

    result = report_agent.invoke(
        {"messages": [{"role": "user", "content": "Give me a report on London."}]}
    )
    report = result["structured_response"]
    print(report)
    print("Just the weather:", report.weather)

    draw_graph(report_agent, "travel_agent_structured_output_demo.png")


@wrap_tool_call
def log_tool_calls(request, handler):
    call = request.tool_call
    print(f"  [middleware] calling {call['name']} with {call['args']}")
    return handler(request)


async def travel_agent_middleware_demo():
    # middleware tool called before model call, each tool call and before answering
    watched_agent = create_agent(
        model="openai:gpt-5.4-mini",
        tools=[get_weather, get_population],
        system_prompt="You are a travel assistant. Use your tools.",
        middleware=[log_tool_calls],
    )

    result = watched_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Weather and population of London and Rome?",
                }
            ]
        }
    )
    print("\nFinal answer:", result["messages"][-1].content)

    draw_graph(watched_agent, "travel_agent_middleware_demo.png")

async def browser_agent_mcp_demo():
    # executed below command to generate playwright_check.png image.
    # npx -y playwright@latest screenshot --channel=chrome https://news.ycombinator.com playwright_check.png

    client = MultiServerMCPClient({
        "playwright": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@playwright/mcp@latest","--isolated"]
        }
    })

    browser_tools = await client.get_tools()
    print(f"Loaded {len(browser_tools)} browser tools:")
    for t in browser_tools:
        print('-', t.name)

    browser_agent = create_agent(
        model='openai:gpt-5.4-mini',
        tools=browser_tools,
        system_prompt="You are a web research assistant. Use the browser tools to complete the task, then report clearly.",
    )

    result = await browser_agent.ainvoke({"messages": [{"role": "user",
    "content": "Go to https://news.ycombinator.com and tell me the titles of the top three stories on the front page."}]})
    print(result["messages"][-1].content)

async def main():
    # await simple_agent_demo()

    # await travel_agent_tools_demo()

    # await travel_agent_memory_demo()

    # await travel_agent_structured_output_demo()

    # await travel_agent_middleware_demo()

    await browser_agent_mcp_demo()


if __name__ == "__main__":
    asyncio.run(main())
