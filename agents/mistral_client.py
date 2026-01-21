import os
import json
from mistralai import Mistral

client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
MODEL = "mistral-large-latest"


def call_mistral_with_tools(*, messages, tools=None):
    response = client.chat.complete(
        model=MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto" if tools else None,
        temperature=0.3,
    )

    msg = response.choices[0].message

    # TOOL CALL PATH
    if msg.tool_calls:
        tool = msg.tool_calls[0]
        args = tool.function.arguments

        # 🔥 normalize arguments
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

    # NORMAL RESPONSE
    return {
        "content": msg.content or ""
    }
