import os

from dotenv import load_dotenv
from langchain.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv(override=True)


MODEL_NAME = "gpt-5.4-mini"


llm = ChatOpenAI(model=MODEL_NAME)


def basic_llm_demo():
    message = "In one sentence, what does it mean for an AI Agent to be autonomous"
    reply = llm.invoke(message)

    # content='An AI agent is autonomous if it can perceive its environment, make decisions, and take actions toward its goals with minimal or no human intervention.' additional_kwargs={'refusal': None} response_metadata={'token_usage': {'completion_tokens': 31, 'prompt_tokens': 21, 'total_tokens': 52, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0, 'text_tokens': None}, 'prompt_tokens_details': {'audio_tokens': 0, 'cache_write_tokens': 0, 'cached_tokens': 0, 'image_tokens': 0, 'text_tokens': None}}, 'model_provider': 'openai', 'model_name': 'gpt-5.4-mini-2026-03-17', 'system_fingerprint': None, 'id': 'chatcmpl-ERV1BYZS2pE2CQAq5u1FuHDj5sKWt', 'service_tier': 'default', 'finish_reason': 'stop', 'logprobs': None} id='lc_run--01a0d198-05ca-71b2-93c0-f918af79b3d3-0' tool_calls=[] invalid_tool_calls=[] usage_metadata={'input_tokens': 21, 'output_tokens': 31, 'total_tokens': 52, 'input_token_details': {'audio_tokens': 0, 'cache_read': 0}, 'output_token_details': {'audio_tokens': 0, 'reasoning_tokens': 0}}

    print(reply)

    # An AI agent is autonomous if it can perceive its environment, make decisions, and take actions toward its goals with minimal or no human intervention.
    print(reply.content)
    print()


def streaming_demo():
    message = "In one sentence, what does it mean for an AI Agent to be autonomous"

    for chunk in llm.stream(message):
        # content='' additional_kwargs={} response_metadata={'model_provider': 'openai'} id='lc_run--01a0d19c-6d53-7fb2-bda6-a01cc9dd6e62' tool_calls=[] invalid_tool_calls=[] tool_call_chunks=[]
        # content='An' additional_kwargs={} response_metadata={'model_provider': 'openai'} id='lc_run--01a0d19c-6d53-7fb2-bda6-a01cc9dd6e62' tool_calls=[] invalid_tool_calls=[] tool_call_chunks=[]
        # content=' AI' additional_kwargs={} response_metadata={'model_provider': 'openai'} id='lc_run--01a0d19c-6d53-7fb2-bda6-a01cc9dd6e62' tool_calls=[] invalid_tool_calls=[] tool_call_chunks=[]
        # content=' agent' additional_kwargs={} response_metadata={'model_provider': 'openai'} id='lc_run--01a0d19c-6d53-7fb2-bda6-a01cc9dd6e62' tool_calls=[] invalid_tool_calls=[] tool_call_chunks=[]
        # content=' is' additional_kwargs={} response_metadata={'model_provider': 'openai'} id='lc_run--01a0d19c-6d53-7fb2-bda6-a01cc9dd6e62' tool_calls=[] invalid_tool_calls=[] tool_call_chunks=[]
        # content=' autonomous' additional_kwargs={} response_metadata={'model_provider': 'openai'} id='lc_run--01a0d19c-6d53-7fb2-bda6-a01cc9dd6e62' tool_calls=[] invalid_tool_calls=[] tool_call_chunks=[]
        # content=' if' additional_kwargs={} response_metadata={'model_provider': 'openai'} id='lc_run--01a0d19c-6d53-7fb2-bda6-a01cc9dd6e62' tool_calls=[] invalid_tool_calls=[] tool_call_chunks=[]
        # content=' it' additional_kwargs={} response_metadata={'model_provider': 'openai'} id='lc_run--01a0d19c-6d53-7fb2-bda6-a01cc9dd6e62' tool_calls=[] invalid_tool_calls=[] tool_call_chunks=[]
        # content=' can' additional_kwargs={} response_metadata={'model_provider': 'openai'} id='lc_run--01a0d19c-6d53-7fb2-bda6-a01cc9dd6e62' tool_calls=[] invalid_tool_calls=[] tool_call_chunks=[]
        # content=' independently' additional_kwargs={} response_metadata={'model_provider': 'openai'} id='lc_run--01a0d19c-6d53-7fb2-bda6-a01cc9dd6e62' tool_calls=[] invalid_tool_calls=[] tool_call_chunks=[]
        # content=',' additional_kwargs={} response_metadata={'model_provider': 'openai'} id='lc_run--01a0d19c-6d53-7fb2-bda6-a01cc9dd6e62' tool_calls=[] invalid_tool_calls=[] tool_call_chunks=[]
        # content=' decide' additional_kwargs={} response_metadata={'model_provider': 'openai'} id='lc_run--01a0d19c-6d53-7fb2-bda6-a01cc9dd6e62' tool_calls=[] invalid_tool_calls=[] tool_call_chunks=[]
        # content=',' additional_kwargs={} response_metadata={'model_provider': 'openai'} id='lc_run--01a0d19c-6d53-7fb2-bda6-a01cc9dd6e62' tool_calls=[] invalid_tool_calls=[] tool_call_chunks=[]
        # content=' and' additional_kwargs={} response_metadata={'model_provider': 'openai'} id='lc_run--01a0d19c-6d53-7fb2-bda6-a01cc9dd6e62' tool_calls=[] invalid_tool_calls=[] tool_call_chunks=[]
        # content=' act' additional_kwargs={} response_metadata={'model_provider': 'openai'} id='lc_run--01a0d19c-6d53-7fb2-bda6-a01cc9dd6e62' tool_calls=[] invalid_tool_calls=[] tool_call_chunks=[]
        # content=' toward' additional_kwargs={} response_metadata={'model_provider': 'openai'} id='lc_run--01a0d19c-6d53-7fb2-bda6-a01cc9dd6e62' tool_calls=[] invalid_tool_calls=[] tool_call_chunks=[]
        # content=' its' additional_kwargs={} response_metadata={'model_provider': 'openai'} id='lc_run--01a0d19c-6d53-7fb2-bda6-a01cc9dd6e62' tool_calls=[] invalid_tool_calls=[] tool_call_chunks=[]
        # content=' goals' additional_kwargs={} response_metadata={'model_provider': 'openai'} id='lc_run--01a0d19c-6d53-7fb2-bda6-a01cc9dd6e62' tool_calls=[] invalid_tool_calls=[] tool_call_chunks=[]
        # content=' with' additional_kwargs={} response_metadata={'model_provider': 'openai'} id='lc_run--01a0d19c-6d53-7fb2-bda6-a01cc9dd6e62' tool_calls=[] invalid_tool_calls=[] tool_call_chunks=[]
        # content=' minimal' additional_kwargs={} response_metadata={'model_provider': 'openai'} id='lc_run--01a0d19c-6d53-7fb2-bda6-a01cc9dd6e62' tool_calls=[] invalid_tool_calls=[] tool_call_chunks=[]
        # content=' human' additional_kwargs={} response_metadata={'model_provider': 'openai'} id='lc_run--01a0d19c-6d53-7fb2-bda6-a01cc9dd6e62' tool_calls=[] invalid_tool_calls=[] tool_call_chunks=[]
        # content=' intervention' additional_kwargs={} response_metadata={'model_provider': 'openai'} id='lc_run--01a0d19c-6d53-7fb2-bda6-a01cc9dd6e62' tool_calls=[] invalid_tool_calls=[] tool_call_chunks=[]
        # content='.' additional_kwargs={} response_metadata={'model_provider': 'openai'} id='lc_run--01a0d19c-6d53-7fb2-bda6-a01cc9dd6e62' tool_calls=[] invalid_tool_calls=[] tool_call_chunks=[]
        # content='' additional_kwargs={} response_metadata={'finish_reason': 'stop', 'model_name': 'gpt-5.4-mini-2026-03-17', 'service_tier': 'default', 'model_provider': 'openai'} id='lc_run--01a0d19c-6d53-7fb2-bda6-a01cc9dd6e62' tool_calls=[] invalid_tool_calls=[] tool_call_chunks=[]
        # content='' additional_kwargs={} response_metadata={} id='lc_run--01a0d19c-6d53-7fb2-bda6-a01cc9dd6e62' tool_calls=[] invalid_tool_calls=[] usage_metadata={'input_tokens': 21, 'output_tokens': 26, 'total_tokens': 47, 'input_token_details': {'audio_tokens': 0, 'cache_read': 0}, 'output_token_details': {'audio_tokens': 0, 'reasoning_tokens': 0}} tool_call_chunks=[]
        # content='' additional_kwargs={} response_metadata={} id='lc_run--01a0d19c-6d53-7fb2-bda6-a01cc9dd6e62' tool_calls=[] invalid_tool_calls=[] tool_call_chunks=[] chunk_position='last'

        # Above are all the chunks    
        # print(chunk)

        print(chunk.content, end="", flush=True)


def google_gemini_demo():
    google_gemini_llm = ChatOpenAI(
        model="gemini-3.5-flash-lite",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=os.getenv("GOOGLE_API_KEY"),
    )

    reply = google_gemini_llm.invoke("In one sentence, what is LangChain?")
    print(reply.content)


def message_formats_demo():
    messages = [
        SystemMessage('You are a terse assistant who answers in exactly five words.'),
        HumanMessage('What is the capital of France?')
    ]

    print(llm.invoke(messages).content)

    messages_as_dicts = [
        {'role': 'system', 'content': 'You are a terse assistant who answers in exactly five words.'},
        {'role': 'user', 'content': 'What is the capital of France?'},
    ]

    print(llm.invoke(messages_as_dicts).content)


@tool
def get_share_price(symbol: str) -> float:
    """Return the current share price for a given ticker symbol."""
    fake_prices = {"AAPL": 241.5, "GOOG": 168.2, "AMZN": 198.0}
    return fake_prices.get(symbol.upper(), 0.0)


def tool_demo():
    # below attributes are added due to tool decorator
    print("name:", get_share_price.name)
    print("description:", get_share_price.description)
    print("args:", get_share_price.args)
    print("called directly:", get_share_price.invoke({"symbol": "AAPL"}))

    llm_with_tools = llm.bind_tools([get_share_price])

    # Note that only one api call is done, which in response returns tool call in finish reason
    response = llm_with_tools.invoke("What is the share price of Amazon?")

    # content='' additional_kwargs={'refusal': None} response_metadata={'token_usage': {'completion_tokens': 19, 'prompt_tokens': 138, 'total_tokens': 157, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0, 'text_tokens': None}, 'prompt_tokens_details': {'audio_tokens': 0, 'cache_write_tokens': 0, 'cached_tokens': 0, 'image_tokens': 0, 'text_tokens': None}}, 'model_provider': 'openai', 'model_name': 'gpt-5.4-mini-2026-03-17', 'system_fingerprint': None, 'id': 'chatcmpl-ERVWdRZfvZslDlRL93bLUzpSV2w7v', 'service_tier': 'default', 'finish_reason': 'tool_calls', 'logprobs': None} id='lc_run--01a0d1b5-ca18-7111-ac2d-e1f3d6bbe8d4-0' tool_calls=[{'name': 'get_share_price', 'args': {'symbol': 'AMZN'}, 'id': 'call_UCKfdDdmbcREiRqmqu3pjRLH', 'type': 'tool_call'}] invalid_tool_calls=[] usage_metadata={'input_tokens': 138, 'output_tokens': 19, 'total_tokens': 157, 'input_token_details': {'audio_tokens': 0, 'cache_read': 0}, 'output_token_details': {'audio_tokens': 0, 'reasoning_tokens': 0}} 
    print(response)

    # content: ''
    print("content:", repr(response.content))

    # tool_calls: [{'name': 'get_share_price', 'args': {'symbol': 'AMZN'}, 'id': 'call_agqa33mUE8XRbtr8OrM5q04v', 'type': 'tool_call'}]
    print("tool_calls:", response.tool_calls)

    llm_with_tools = llm.bind_tools([get_share_price])

    conversation = [
        HumanMessage("What is the share price of Amazon?")
    ]

    ai_message = llm_with_tools.invoke(conversation)
    conversation.append(ai_message)

    for call in ai_message.tool_calls:
        if call["name"] == "get_share_price":
            result = get_share_price.invoke(call["args"])
            conversation.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=call["id"],
                )
            )

    final = llm_with_tools.invoke(conversation)
    # Amazon (AMZN) is **$198.00** per share.
    print(final.content)


class Company(BaseModel):
    name: str = Field(description="The company name")
    ticker: str = Field(description="The stock ticker symbol")
    founded_year: int = Field(description="The year the company was founded")


def structured_output_demo():
    structured_llm = llm.with_structured_output(Company)

    company = structured_llm.invoke("Tell me about Amazon the technology company")
    # name='Amazon' ticker='AMZN' founded_year=1994
    print(company)
    print("Just the ticker:", company.ticker)


def main():
    basic_llm_demo()
    streaming_demo()
    google_gemini_demo()
    message_formats_demo()
    tool_demo()
    structured_output_demo()


if __name__ == "__main__":
    main()

