import asyncio
import os
import smtplib
from email.message import EmailMessage

from agents import (
    Agent,
    GuardrailFunctionOutput,
    OpenAIChatCompletionsModel,
    Runner,
    function_tool,
    output_guardrail,
    trace,
)
from agents.extensions.visualization import draw_graph
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

load_dotenv(override=True)


MODEL_NAME = "gpt-5.4-mini"


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

GEMINI_CLIENT = AsyncOpenAI(
    base_url=GEMINI_BASE_URL,
    api_key=GOOGLE_API_KEY,
)

GEMINI_MODEL = OpenAIChatCompletionsModel(
    model="gemini-3.1-flash-lite",
    openai_client=GEMINI_CLIENT,
)


EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER")


def get_file_path(filename: str) -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, filename)


def draw_agent_graph(agent: Agent):
    # Convert the agent name into a simple filename.
    #
    # For example:
    # "Sales Manager"
    #
    # becomes:
    # "sales_manager"
    filename = agent.name.lower().replace(" ", "_")
    graph_base_path = get_file_path(filename)

    draw_graph(
        agent,
        filename=graph_base_path,
    )

    graph_path = get_file_path(f"{filename}.png")

    print(f"Graph saved to: {graph_path}")

    return graph_path


def send_email(
    subject: str,
    text_body: str,
    html_body: str,
):
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
    model=GEMINI_MODEL,
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
    # The important part is that the LLM itself is now responsible
    # for deciding which tools to call and in what order.

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

    with trace("Sales Manager across different models"):
        result = await Runner.run(
            sales_manager,
            task,
        )

    print(result.final_output)


class EmailReview(BaseModel):
    is_professional: bool = Field(
        description="Whether the email is professional and appropriate"
    )
    number_of_sentences: int = Field(
        description=(
            "The number of sentences in the body of the email, "
            "not including the greeting and signature"
        )
    )
    contains_placeholders: bool = Field(
        description="Whether the email contains placeholders for personalization"
    )


checker = Agent(
    name="Checker",
    instructions="You review potential sales emails",
    model=MODEL_NAME,
    output_type=EmailReview,
)


async def structured_output_demo():
    print(EmailReview.model_json_schema())

    email = """
    Hi [first_name],
    
    I'm hitting you up to see if you'd like to buy our product. It's really great. You'll miss out if you don't buy it.
    
    Laters.
    
    Ed
    """

    result = await Runner.run(
        checker,
        email,
    )

    print(result.final_output)


@output_guardrail
async def email_guardrail(ctx, agent, message):
    result = await Runner.run(
        checker,
        message,
        context=ctx.context,
    )

    review = result.final_output

    is_problem = (
        review.contains_placeholders
        or not review.is_professional
    )

    return GuardrailFunctionOutput(
        output_info={"review": review},
        tripwire_triggered=is_problem,
    )


async def guardrail_demo():
    # using guard rail inbuilt to openai agents package, this will work with open ai agents only.
    cowboy_instructions = "Speak like a cowboy"

    sales_agent_cowboy = Agent(
        name="cowboy_sales_agent",
        instructions=cowboy_instructions,
        model=MODEL_NAME,
        output_guardrails=[email_guardrail],
    )

    result = await Runner.run(
        sales_agent_cowboy,
        "Write a cold sales email",
    )

    print(result.final_output)

    # using simple agent and simple checker without inbuilt guard rails, will work with any model.
    simple_cowboy_agent = Agent(
        name="simple_cowboy_agent",
        instructions=cowboy_instructions,
        model=GEMINI_MODEL,
    )

    result = await Runner.run(
        simple_cowboy_agent,
        "Write a cold sales email",
    )

    email = result.final_output

    print(email)

    result = await Runner.run(
        checker,
        email,
    )

    review = result.final_output

    if not review.is_professional or review.contains_placeholders:
        print(
            "The email is not professional or has placeholders "
            "and will not be sent"
        )
    else:
        print("Email is good")


async def main():
    # await send_sales_email_llm()

    # await structured_output_demo()

    await guardrail_demo()


if __name__ == "__main__":
    # Refer to Day 2 for the earlier version of this code.
    # This version focuses only on the final Sales Manager workflow.
    asyncio.run(main())

