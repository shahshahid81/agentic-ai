import asyncio
import os
import smtplib
from email.message import EmailMessage

from agents import (
    Agent,
    ModelSettings,
    Runner,
    Tool,
    WebSearchTool,
    function_tool,
    trace,
)
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv(override=True)


MODEL_NAME = "gpt-5.4-mini"
WEB_SEARCH_COUNT = 3

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER")


def get_file_path(filename: str) -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, filename)


SEARCH_AGENT_INSTRUCTIONS = """
You are a research assistant. 
Given a search term, you search the web for that term and produce a concise summary of the results.
The summary must be 2-3 paragraphs and less than 300 words.
Capture the main points and be succint. Reply only with the summary.
"""

task = "Most Popular AI Agent Frameworks in 2026"

settings = ModelSettings(tool_choice="required")
tools: list[Tool] = [WebSearchTool()]

search_agent = Agent(
    name="Search Agent",
    instructions=SEARCH_AGENT_INSTRUCTIONS,
    tools=tools,
    model=MODEL_NAME,
    model_settings=settings,
)


# Here, the order matters. If we have reason key before query, LLM will generate better query if they have reason.
class WebSearchItem(BaseModel):
    reason: str = Field(
        description="Your reasoning for why this search is important to the query."
    )
    query: str = Field(description="The search term to use for the web search")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(
        description="A list of web searches to perform to best answer the query"
    )


RESEARCH_AGENT_INSTRUCTIONS = f"""
You are a research assistant. Given a user query, come up with a set of web searches
to perform to best answer the query. Output {WEB_SEARCH_COUNT} terms to query for.
"""

planner_agent = Agent(
    name="Planner Agent",
    instructions=RESEARCH_AGENT_INSTRUCTIONS,
    model=MODEL_NAME,
    output_type=WebSearchPlan,
)


WRITER_AGENT_INSTRUCTIONS = """
You are a senior researcher tasked with writing a cohesive report for a research query.
You will be provided with the original query, and some research.
Generate a comprehensive report based on the research and the query.
The final output should be in markdown format, and it should be lengthy and detailed.
Aim for 5-10 pages of content, at least 1000 words.
"""


class ReportData(BaseModel):
    short_summary: str = Field(
        description="A short 2-3 sentence summary of the findings."
    )
    markdown_report: str = Field(description="The final report")
    follow_up_questions: list[str] = Field(
        description="Suggested topics to research further"
    )


writer_agent = Agent(
    name="Writer Agent",
    instructions=WRITER_AGENT_INSTRUCTIONS,
    model=MODEL_NAME,
    output_type=ReportData,
)


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


EMAIL_AGENT_INSTRUCTIONS = """
You are provided with a detailed report. Use your tool to send an email, converting the report into
a clean, well presented HTML email with appropriate subject line.
"""

email_agent = Agent(
    name="Email Agent",
    instructions=EMAIL_AGENT_INSTRUCTIONS,
    tools=[send_email_tool],
    model=MODEL_NAME,
)


async def search(item: WebSearchItem):
    input_message = f"Search Term: {item.query}\nReason for searching: {item.reason}"
    result = await Runner.run(
        search_agent,
        input_message,
    )
    return result.final_output


async def run_searches(query: str):
    print("Planning searches...")

    result = await Runner.run(
        planner_agent,
        f"Query: {query}",
    )

    searches = result.final_output.searches

    print(f"Will perform {len(searches)} searches")

    tasks = [search(item) for item in searches]

    results = await asyncio.gather(*tasks)

    print("Finished searching")

    return results


async def write_report(query: str, search_results: list[str]):
    print("Thinking about report...")

    input_message = (
        f"Original Query: {query}\nSummarized search results: {search_results}"
    )

    result = await Runner.run(
        writer_agent,
        input_message,
    )

    print("Finished writing report")

    return result.final_output


async def send_email_report(report: ReportData):
    print("Writing email...")

    result = await Runner.run(
        email_agent,
        report.markdown_report,
    )

    print("Email sent")

    return result.final_output


async def main():
    # result = await Runner.run(search_agent,task)

    # # ideally do not perform blocking io operation in async method, for demo, we are ignoring.
    # with open(get_file_path('search_result.md'), 'w', encoding='utf-8') as f:  # noqa: ASYNC230
    #     f.write(result.final_output)

    # print(WebSearchPlan.model_json_schema())

    # result = await Runner.run(planner_agent, task)
    # print(result.final_output)

    query = "Most popular AI Agent frameworks in 2026"

    with trace("Research Trace"):
        print("Starting research...")

        search_results = await run_searches(query)

        report = await write_report(
            query,
            search_results,
        )

        await send_email_report(report)

        print("Hooray!")


if __name__ == "__main__":
    asyncio.run(main())
