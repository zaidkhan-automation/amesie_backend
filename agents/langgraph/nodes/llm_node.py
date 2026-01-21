from agents.langgraph.state import AgentState
from agents.mistral_client import call_mistral_with_tools
from agents.langgraph.tool_schemas import SELLER_TOOLS

SYSTEM_INSTRUCTION = """
You are a seller assistant.

If the user wants to create a product AND the required fields
(name and price) are present, you MUST call the tool
`seller_create_product` immediately.

Do NOT ask follow-up questions if required fields exist.
Only ask questions if required fields are missing.
"""

def llm_node(state: AgentState) -> AgentState:
    messages = []

    # System rules
    messages.append({
        "role": "system",
        "content": SYSTEM_INSTRUCTION
    })

    # Optional memory
    if state.get("memory_context"):
        messages.append({
            "role": "system",
            "content": f"Relevant memory:\n{state['memory_context']}"
        })

    # Conversation history
    messages.extend(state["messages"])

    response = call_mistral_with_tools(
        messages=messages,
        tools=SELLER_TOOLS
    )

    # TOOL CALL
    if response.get("tool_call"):
        return {
            **state,
            "tool_call": response["tool_call"]
        }

    # NORMAL ASSISTANT RESPONSE
    return {
        **state,
        "messages": state["messages"] + [{
            "role": "assistant",
            "content": response["content"]
        }]
    }
