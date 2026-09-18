import asyncio

from agents import Agent, Runner, SQLiteSession, function_tool, trace
from dotenv import load_dotenv
from openai.types.responses import ResponseTextDeltaEvent

load_dotenv(override=True)


async def tell_a_joke():
    # instructions is system prompt
    agent = Agent(
        name="Jokester", instructions="You are a joke teller", model="gpt-5.4-mini"
    )
    result = await Runner.run(agent, "Tell me a joke about Autonomous AI Agents")
    return result


async def tell_a_joke_trace():
    with trace("Telling a joke"):
        result = await tell_a_joke()
    print(result.final_output)
    print(result.to_input_list())


async def tell_a_joke_streamed():
    agent = Agent(
        name="Jokester", instructions="You are a joke teller", model="gpt-5.4-mini"
    )
    result = Runner.run_streamed(
        agent, input="Tell me a joke about Autonomous AI Agents."
    )
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(
            event.data, ResponseTextDeltaEvent
        ):
            print(event.data.delta, end="", flush=True)


@function_tool
def push_tool(message: str) -> str:
    """Send the given message to the user as push notification"""
    print(f"Push: {message}")
    return "Push sent success"


async def notify_user_traced(message):
    notifier = Agent(
        name="Notifier",
        model="gpt-5.4-mini",
        instructions="You notify the user upon request",
        tools=[push_tool],
    )
    with trace("Pizza has arrived"):
        result = await Runner.run(notifier, input=message)
    print(result.final_output)


async def non_memory_demo():
    agent = Agent(name="Assistant", model="gpt-5.4-mini")
    # Runner.run just process the current input, it doesn't maintain any state including chat history.
    response = await Runner.run(agent, input="Hi, My name is John")
    # Hi John! How can I help you today?
    print(response.final_output)
    response = await Runner.run(agent, input="What is my name?")
    # I don’t know your name unless you tell me.
    print(response.final_output)


async def short_term_memory_manual():
    agent = Agent(name="Assistant", model="gpt-5.4-mini")
    response = await Runner.run(agent, input="Hi, My name is John")
    # get the system and user and assistant message list of dictionary
    history = response.to_input_list()
    # Hi John! How can I help you today?
    print(response.final_output)

    # pass previous history
    response = await Runner.run(
        agent, input=history + [{"role": "user", "content": "What is my name?"}]
    )

    # Your name is John.
    print(response.final_output)


async def short_term_memory_sql_lite():
    # in memory session, pass db name as second arg for persistence to disk
    session = SQLiteSession("session-1")
    agent = Agent(name="Assistant", model="gpt-5.4-mini")
    response = await Runner.run(agent, input="Hi, My name is John", session=session)
    # Hi John — nice to meet you!
    print(response.final_output)
    response = await Runner.run(agent, input="What is my name?", session=session)
    # Your name is John.
    print(response.final_output)


async def main():
    # await tell_a_joke_trace()
    # await tell_a_joke_streamed()
    # print(push_tool)
    # print(push_tool.description)
    # await notify_user_traced(message='Notify the user pizza is available')
    # await non_memory_demo()
    # await short_term_memory_manual()
    await short_term_memory_sql_lite()


if __name__ == "__main__":
    asyncio.run(main())
