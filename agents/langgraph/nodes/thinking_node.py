from agents.langgraph.state import AgentState
from agents.mistral_client import call_mistral_with_tools

THINKING_PROMPT = """
You are an intent classifier.
Return JSON only.
intent values:
- create_product
- update_price
- update_stock
- delete_product
- list_products
- calculator
- chat
- meta
"""

META_KEYWORDS = (
    "system",
    "rules",
    "prompt",
    "ignore",
    "tools",
    "training",
)


def thinking_node(state: AgentState) -> AgentState:

    content = state["messages"][-1]["content"].lower()

    if any(k in content for k in META_KEYWORDS):
        return {
            **state,
            "thinking": '{"intent":"meta"}'
        }

    response = call_mistral_with_tools(
        messages=[
            {"role": "system", "content": THINKING_PROMPT},
            {"role": "user", "content": content}
        ],
        tools=[]
    )

    return {
        **state,
        "thinking": response.get("content", '{"intent":"chat"}')
    }
