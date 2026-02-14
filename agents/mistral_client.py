import os
import json
from mistralai import Mistral

client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
MODEL = "mistral-large-latest"


# ---------------------------------------------------
# 🔹 BLOCKING CALL (FOR LANGGRAPH TOOL EXECUTION)
# ---------------------------------------------------
def call_mistral_with_tools(*, messages, tools=None):

    response = client.chat.complete(
        model=MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto" if tools else None,
        temperature=0.3,
    )

    msg = response.choices[0].message

    if msg.tool_calls:
        tool = msg.tool_calls[0]
        args = tool.function.arguments

        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                args = {}

        return {
            "tool_call": {
                "name": tool.function.name,
                "arguments": args or {},
            }
        }

    return {
        "content": msg.content or ""
    }


# ---------------------------------------------------
# 🔹 TRUE STREAMING (DIRECT FROM MISTRAL)
# ---------------------------------------------------
def stream_mistral_response(messages, tools=None):

    stream = client.chat.stream(
        model=MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto" if tools else None,
        temperature=0.3,
    )

    for event in stream:

        if not event.data:
            continue

        delta = event.data.choices[0].delta

        # Stream normal tokens
        if delta.content:
            yield {
                "type": "content",
                "data": delta.content
            }

        # Stream tool calls
        if delta.tool_calls:
            tool = delta.tool_calls[0]
            args = tool.function.arguments

            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {}

            yield {
                "type": "tool_call",
                "data": {
                    "name": tool.function.name,
                    "arguments": args or {}
                }
            }
