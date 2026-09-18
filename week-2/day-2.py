import asyncio
import os
import smtplib
from email.message import EmailMessage

from agents import Agent, ModelSettings, Runner, function_tool, trace
from agents.extensions.visualization import draw_graph
from dotenv import load_dotenv
from openai.types.responses import ResponseTextDeltaEvent

load_dotenv(override=True)


MODEL_NAME = "gpt-5.4-mini"

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER")


def get_file_path(filename):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, filename)


def draw_agent_graph(agent: Agent):
    # Convert the agent name into a simple filename.
    #
    # For example:
    # "Sales Manager With Handoff"
    #
    # becomes:
    # "sales_manager_with_handoff"
    filename = agent.name.lower().replace(" ", "_")
    graph_base_path = get_file_path(filename)

    draw_graph(
        agent,
        filename=graph_base_path,
    )
    graph_path = get_file_path(f"{filename}.png")
    print(f"Graph saved to: {graph_path}")
    return graph_path


def send_email(subject, text_body, html_body):
    msg = EmailMessage()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_ADDRESS
    msg["Subject"] = subject

    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(EMAIL_SMTP_SERVER, 587) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)


base_intro = """
You are a sales agent working for ComplyAI,
a company that provides a SaaS tool for ensuring SO2 compliance
and preparing for audits, powered by AI.
You write cold sales emails.
"""


professional_agent = Agent(
    name="Professional Sales Agent",
    instructions=(
        base_intro
        + "Your email style is professional, serious, "
        "with gravitas and credibility."
    ),
    model=MODEL_NAME,
)


humorous_agent = Agent(
    name="Humorous Sales Agent",
    instructions=(
        base_intro
        + "Your email style is witty, engaging and humorous."
    ),
    model=MODEL_NAME,
)


executive_agent = Agent(
    name="Executive Sales Agent",
    instructions=(
        base_intro
        + "Your email style is concise, to the point, "
        "in the style of a busy senior executive."
    ),
    model=MODEL_NAME,
)


sales_picker_agent = Agent(
    name="Sales Picker",
    instructions="""
You pick the best cold sales email from the given options.
Imagine you are a customer and pick the one you are most likely to respond to.
Do not give an explanation; reply with the selected email only.
""",
    model=MODEL_NAME,
)


async def stream_professional_email():
    agent = professional_agent

    result = Runner.run_streamed(
        agent,
        input="Write a cold sales email",
    )

    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(
            event.data, ResponseTextDeltaEvent
        ):
            print(event.data.delta, end="", flush=True)


async def parallel_cold_emails():
    message = "Write a cold sales email"

    with trace("Parallel Cold Emails"):
        results = await asyncio.gather(
            Runner.run(professional_agent, input=message),
            Runner.run(humorous_agent, input=message),
            Runner.run(executive_agent, input=message),
        )

    outputs = [result.final_output for result in results]

    for output in outputs:
        print(output)
        print("\n\n")


async def sales_selection_workflow():
    message = "Write a cold sales email"

    with trace("Sales Selection Workflow"):
        results = await asyncio.gather(
            Runner.run(professional_agent, input=message),
            Runner.run(humorous_agent, input=message),
            Runner.run(executive_agent, input=message),
        )

        outputs = [result.final_output for result in results]

        emails = (
            "Cold sales emails:\n\n"
            + "\n\nEmail:\n\n".join(outputs)
        )

        best = await Runner.run(
            sales_picker_agent,
            input=emails,
        )

    print(f"Best Sales Email:\n{best.final_output}")


# function description comments and type hints added to generate tool json schema
@function_tool
def send_email_tool(
    subject: str,
    text_body: str,
    html_body: str,
) -> str:
    """
    Send out an email with the given subject and body to all sales prospects.

    Args:
        subject: The subject of the email.
        text_body: The body of the email as plain text.
        html_body: The HTML body of the email.
    """

    send_email(
        subject,
        text_body,
        html_body,
    )

    return "Email sent successfully"


sales_sender_agent = Agent(
    name="Sales Sender",
    instructions="""
You pick the best cold sales email from the given options.
Imagine you are a customer and pick the one you are most likely to respond to.
Then use your tool to send the email.
""",
    model=MODEL_NAME,
    tools=[send_email_tool],
    model_settings=ModelSettings(tool_choice="required"),
)


async def send_sales_email():
    message = "Write a cold sales email"

    with trace("Sales Selection Workflow with Email"):
        results = await asyncio.gather(
            Runner.run(professional_agent, input=message),
            Runner.run(humorous_agent, input=message),
            Runner.run(executive_agent, input=message),
        )

        outputs = [result.final_output for result in results]

        emails = (
            "Cold sales emails:\n\n"
            + "\n\nEmail:\n\n".join(outputs)
        )

        best = await Runner.run(
            sales_sender_agent,
            input=emails,
        )

    print(f"Best Sales Email:\n{best.final_output}")


def get_agent_as_tools():
    # Convert each specialized sales agent into a tool.
    #
    # This means the Sales Manager can call these agents like normal
    # tools instead of directly handing control over to them.
    description = (
        "Use this tool to write a sales email. "
        "In the input, just instruct to write a sales email."
    )

    professional_agent_tool = professional_agent.as_tool(
        tool_name="professional_agent_tool",
        tool_description=description,
    )

    humorous_agent_tool = humorous_agent.as_tool(
        tool_name="humorous_agent_tool",
        tool_description=description,
    )

    executive_agent_tool = executive_agent.as_tool(
        tool_name="executive_agent_tool",
        tool_description=description,
    )

    return [
        professional_agent_tool,
        humorous_agent_tool,
        executive_agent_tool,
        send_email_tool,
    ]


async def send_sales_email_llm():
    # Convert the three sales agents and the email function into tools.
    #
    # The important difference from the previous examples is that
    # the LLM itself is now responsible for deciding which tools
    # to call and in what order.
    tools = get_agent_as_tools()

    sales_manager_prompt = """
    You are a Sales Manager at ComplyAI.
    Your goal is to find the single best cold sales email
    using the available sales email writer tools.
    """

    task = """
    Follow these steps:

    1. Generate Drafts:
    Use each of the three sales email writer tools to generate
    a different email draft.

    Just instruct each tool to write a sales email.
    No further details are needed.

    Do not proceed until all three drafts are ready,
    one from each tool.

    2. Evaluate and Select:
    Review the three drafts and choose the single best email
    based on which one is most effective.

    3. Send Email:
    Use your email tool to send the best email.
    Send only one email.
    """

    sales_manager = Agent(
        name="Sales Manager",
        instructions=sales_manager_prompt,
        tools=tools,
        model=MODEL_NAME,
    )
    draw_agent_graph(sales_manager)

    with trace("Sales Manager"):
        result = await Runner.run(
            sales_manager,
            task,
        )

    print(result.final_output)


async def send_sales_email_handoff():
    # Convert the three sales-writing agents into tools.
    #
    # We use these tools only for generating the initial drafts.
    tools = get_agent_as_tools()

    sales_manager_prompt = """
    You are a Sales Manager at ComplyAI.
    You get your sales team to draft emails, then hand off
    the drafts to the Sales Sender to choose and send the best one.
    """

    task = """
    Follow these steps:

    1. Generate Drafts:
    Use each of the three sales email writer tools to generate
    a different email draft.

    Just instruct each tool to write a sales email.
    No further details are needed.

    Do not proceed until all three drafts are ready,
    one from each tool.

    2. Handoff:
    Hand off to the Sales Sender to choose and send
    the single best email.
    """

    sales_manager = Agent(
        name="Sales Manager With Handoff",
        instructions=sales_manager_prompt,
        tools=tools[:3],
        handoffs=[sales_sender_agent],
        model=MODEL_NAME,
    )

    draw_agent_graph(sales_manager)

    with trace("Sales Manager"):
        result = await Runner.run(
            sales_manager,
            task,
        )

    print(result.final_output)


async def main():
    # Agent orchestration done by code.
    #
    # In these examples, Python code explicitly controls which agents
    # are called and when they are called.
    #
    # await stream_professional_email()
    # await parallel_cold_emails()
    # await sales_selection_workflow()
    # await send_sales_email()

    # Agent orchestration done by the LLM using agent-as-tool.
    #
    # Each specialized sales agent is exposed as a generic tool.
    # The Sales Manager is then responsible for deciding which tools
    # to call and using their outputs to complete the task.
    #
    # await send_sales_email_llm()

    # Agent orchestration done by the LLM using handoffs.
    #
    # A handoff transfers control from one agent to another.
    # The receiving agent gets the conversation history and continues
    # the task using its own instructions and tools.
    await send_sales_email_handoff()


if __name__ == "__main__":
    # View traces at:
    # https://platform.openai.com/logs?api=traces
    asyncio.run(main())
