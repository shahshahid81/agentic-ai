import json
import os
from pprint import pprint

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader

load_dotenv(override=True)

OPENAI_CLIENT = OpenAI()

MODEL = "gpt-5.4-mini"


def get_file_path(filename):
    BASE_DIR = os.path.dirname(__file__)
    return os.path.join(BASE_DIR, filename)


def load_linkedin():
    path = get_file_path("twin/linkedin-ed-donner.pdf")

    reader = PdfReader(path)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text

    return text


def load_summary():
    path = get_file_path("twin/summary-ed-donner.txt")

    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def build_system_prompt():
    summary = load_summary()
    linkedin = load_linkedin()

    return f"""
    # Your role

    You are a digital twin running on a website, chatting with visitors.
    You represent the person whose website this is.

    You answer questions related to their:
    - career
    - background
    - skills
    - experience

    Here are the details of the person you represent:

    {summary}

    If asked, explain clearly that you are an AI digital twin of this person.

    # LinkedIn context

    {linkedin}

    # Rules

    - Be professional and engaging.
    - Act as if you are talking to a potential client or future employer.
    - Stay focused on the person's career, background, skills, and experience.
    - If asked about unrelated topics, steer the conversation back to professional topics.
    - Always stay in character as the digital twin.
    - Never make up information.
    - If you don't know something, say so.
    - If the information is not in the provided context, say that you don't know.
    """


SYSTEM_PROMPT = build_system_prompt()


def record_email(email):
    print(f"Recording email: {email}")

    path = get_file_path("emails.txt")

    with open(path, "a", encoding="utf-8") as file:
        file.write(f"{email}\n")

    return "Email received"


RECORD_EMAIL_TOOL = {
    "type": "function",
    "function": {
        "name": "record_email",
        "description": "Record the user's email address.",
        "parameters": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "The user's email address.",
                }
            },
            "required": ["email"],
            "additionalProperties": False,
        },
    },
}


TOOLS = [RECORD_EMAIL_TOOL]


def build_messages(message, history):
    return (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + history
        + [{"role": "user", "content": message}]
    )


def handle_tool_call(tool_call):
    name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)

    if name == "record_email":
        return record_email(arguments["email"])

    return "Unknown tool"


def chat(message, history):
    messages = build_messages(message, history)

    response = OPENAI_CLIENT.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
    )

    while response.choices[0].finish_reason == "tool_calls":
        assistant_message = response.choices[0].message

        messages.append(assistant_message)

        for tool_call in assistant_message.tool_calls:
            pprint(tool_call)

            result = handle_tool_call(tool_call)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )

        response = OPENAI_CLIENT.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
        )

    return response.choices[0].message.content


def create_demo():
    return gr.ChatInterface(
        fn=chat,
        title="Ed Donner's Digital Twin",
        description="Ask questions about Ed's career, background, skills and experience.",
    )


def main():
    demo = create_demo()
    demo.launch(inbrowser=True)


if __name__ == "__main__":
    main()
