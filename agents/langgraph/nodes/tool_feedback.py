# agents/langgraph/nodes/tool_feedback.py

from agents.langgraph.state import AgentState

def tool_feedback(state: AgentState) -> AgentState:
    result = state.get("tool_result")
    if not result:
        return state

    # 🔒 FINAL assistant reply (END OF FLOW)
    messages = state["messages"] + [
        {
            "role": "assistant",
            "content": (
                f"✅ Product created successfully.\n"
                f"ID: {result['product']['id']}\n"
                f"Name: {result['product']['name']}\n"
                f"Price: {result['product']['price']}\n"
                f"Stock: {result['product']['stock_quantity']}"
            )
        }
    ]

    return {
        **state,
        "messages": messages,
        "tool_call": None,
        "tool_result": None,
    }
