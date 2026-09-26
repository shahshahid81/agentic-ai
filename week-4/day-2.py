import os
import random
import smtplib
from email.message import EmailMessage
from typing import Annotated

from dotenv import load_dotenv
from langchain_community.tools import GoogleSerperRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict

load_dotenv(override=True)
MODEL_NAME = "gpt-5.4-mini"

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER")


class State(TypedDict):
    # State is shared between all nodes in the graph.
    #
    # add_messages is a reducer. Instead of replacing the existing messages,
    # new messages returned by a node are appended to the message history.
    messages: Annotated[list, add_messages]

    # Translator node writes the translated text into this state field.
    spanish: str


llm = ChatOpenAI(model=MODEL_NAME)


def get_file_path(filename: str) -> str:
    """Return a path relative to this Python file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, filename)


def draw_graph(agent, filename: str):
    """Save a visual representation of a LangGraph graph."""
    with open(get_file_path(filename), "wb") as file:
        file.write(agent.get_graph().draw_mermaid_png())


nouns = [
    "Cabbages",
    "Unicorns",
    "Toasters",
    "Penguins",
    "Bananas",
    "Eels",
    "Pickles",
]

adjectives = [
    "outrageous",
    "smelly",
    "pedantic",
    "existential",
    "sparkly",
    "haunted",
]


def silly_node(state: State) -> dict:
    """Generate a random silly sentence and add it to the message history."""
    sentence = f"{random.choice(nouns)} are {random.choice(adjectives)}"

    return {
        "messages": [
            {
                "role": "assistant",
                "content": sentence,
            }
        ]
    }


def create_silly_graph():
    """Create the simplest possible LangGraph: START -> silly -> END."""
    builder = StateGraph(State)

    builder.add_node("silly", silly_node)

    builder.add_edge(START, "silly")
    builder.add_edge("silly", END)

    return builder.compile()


def run_silly_graph():
    """Run the simple graph demo."""
    graph = create_silly_graph()

    draw_graph(graph, "graph.png")

    # invoke() starts at START and follows the edges until END.
    result = graph.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "say something",
                }
            ]
        }
    )

    print(result["messages"][-1].content)


search = GoogleSerperRun(api_wrapper=GoogleSerperAPIWrapper())


@tool
def send_email(
    subject: str,
    text_body: str,
) -> str:
    """
    Send out an email with the given subject and body to all sales prospects.

    Args:
        subject: The subject of the email.
        text_body: The body of the email as plain text.
    """

    msg = EmailMessage()

    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_ADDRESS
    msg["Subject"] = subject

    msg.set_content(text_body)

    with smtplib.SMTP(EMAIL_SMTP_SERVER, 587) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

    return "Email sent successfully"


tools = [
    search,
    send_email,
]

# bind_tools() does NOT execute the tools.
#
# It tells the LLM:
# "These tools are available. If appropriate, return a tool call."
#
# ToolNode is responsible for actually executing the requested tool later.
llm_with_tools = llm.bind_tools(tools)


def chatbot_node(state: State) -> dict:
    """
    Ask the LLM to respond to the current conversation.

    The LLM can either:
    1. Return a normal AI response.
    2. Return a tool call.

    The conditional edge after this node examines the result and decides
    whether to go to the tools node or continue toward translation.
    """

    return {"messages": [llm_with_tools.invoke(state["messages"])]}


def translator_node(state: State) -> dict:
    """
    Translate the latest message into Spanish.

    This node runs after the chatbot has finished its tool loop.
    """

    last_message = state["messages"][-1].content

    prompt = (
        "Translate this into Spanish, replying with the translation only:\n\n"
        f"{last_message}"
    )

    return {"spanish": llm.invoke(prompt).content}


def create_chatbot_graph(checkpointer=None):
    """
    Build and compile the chatbot graph.
    """

    builder = StateGraph(State)

    # Normal application node that calls the LLM.
    builder.add_node("chatbot", chatbot_node)

    # Special prebuilt node that executes the tools requested by the LLM.
    builder.add_node("tools", ToolNode(tools))

    # Node responsible for translating the final chatbot response.
    builder.add_node("translator", translator_node)

    builder.add_edge(START, "chatbot")

    # tools_condition returns one of two routing values:
    #
    # "tools" -> the chatbot requested a tool
    # END     -> the chatbot has finished
    #
    # We remap the END result to "translator" so that the final
    # chatbot response is translated before the graph actually ends.
    builder.add_conditional_edges(
        "chatbot",
        tools_condition,
        {
            "tools": "tools",
            END: "translator",
        },
    )

    # After a tool executes, return to the chatbot.
    #
    # This creates the tool-calling loop:
    #
    # chatbot -> tools -> chatbot -> tools -> ...
    #
    # The loop ends when the chatbot produces a response without
    # requesting another tool.
    builder.add_edge("tools", "chatbot")

    # The translator is the actual final node.
    # This is where the graph finally reaches the real END.
    builder.add_edge("translator", END)

    return builder.compile(checkpointer=checkpointer)


def run_memory_demo(config):
    """
    Demonstrate conversation memory using MemorySaver.

    MemorySaver keeps checkpoints in RAM, so the data disappears when
    the Python process terminates.
    """

    memory = MemorySaver()

    graph = create_chatbot_graph(checkpointer=memory)

    draw_graph(graph, "chatbot.png")

    graph.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Hi, my name is Ed.",
                }
            ]
        },
        config,
    )

    second = graph.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "What is my name?",
                }
            ]
        },
        config,
    )

    print(second["messages"][-1].content)
    print(second["spanish"])

    result = graph.invoke({"messages": [{"role": "user", "content": "Use your search tool to tell me the ingredients in banoffee pie and send me an email."}]}, config)
    print(result["messages"][-1].content)
    print(result["spanish"])

    return graph


def run_sqlite_memory_demo():
    """
    Demonstrate persistent graph memory using SQLite.

    Unlike MemorySaver, the checkpoint data is stored on disk and can
    survive the lifetime of the Python process.
    """

    with SqliteSaver.from_conn_string("memory.db") as sql_memory:
        durable_graph = create_chatbot_graph(checkpointer=sql_memory)

        sql_config = {"configurable": {"thread_id": "conversation-2"}}

        durable_graph.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": ("Remember that my favourite color is orange."),
                    }
                ]
            },
            sql_config,
        )

        reply = durable_graph.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "What is my favourite color?",
                    }
                ]
            },
            sql_config,
        )

        print(reply["messages"][-1].content)
        print(reply["spanish"])


def time_travel_demo(graph, config):
    snapshot = graph.get_state(config)
    messages = snapshot.values["messages"]

    print("Messages stored so far:", len(messages))

    for message in messages:
        print(message.content)

    history = list(graph.get_state_history(config))
    print("Number of saved checkpoints:", len(history))

    for h in reversed(history):
        m = h.metadata
        queued = ", ".join(t.name for t in h.tasks) or "(run complete)"
        print(
            f"step {m['step']:>2}  {m['source']:<5}  messages={len(h.values.get('messages', []))}  about to run: {queued}"
        )

    # pick a checkpoint from middle of the history list
    earlier = history[len(history) // 2]
    print("A checkpoint from earlier held", len(earlier.values["messages"]), "messages")

    replay_config = {
        "configurable": {
            "thread_id": "conversation-1",
            "checkpoint_id": earlier.config["configurable"]["checkpoint_id"],
        }
    }
    resumed = graph.invoke(None, replay_config)
    print(
        "Resumed from the past; the graph now holds",
        len(resumed["messages"]),
        "messages",
    )

    again = graph.invoke(
        {"messages": [{"role": "user", "content": "What do you know about me?"}]},
        replay_config,
    )
    print(again["messages"][-1].content)
    print(again["spanish"])


def main():
    run_silly_graph()

    # A thread_id identifies one conversation.
    #
    # Multiple graph.invoke() calls using the same thread_id share the
    # checkpointed state.
    config = {"configurable": {"thread_id": "conversation-1"}}

    graph = run_memory_demo(config)

    time_travel_demo(graph, config)

    run_sqlite_memory_demo()


if __name__ == "__main__":
    main()
