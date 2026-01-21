# agents/langgraph/state.py
from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    chat_id: str
    user_id: str

    # Full conversation (OpenAI / Mistral compatible format)
    messages: List[Dict[str, Any]]

    # Tool routing
    tool_call: Optional[Dict[str, Any]]
    tool_result: Optional[Any]

    # Injected context (summary + memories)
    memory_context: List[Dict[str, Any]]
