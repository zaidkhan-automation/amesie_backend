from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    chat_id: str
    user_id: str

    messages: List[Dict[str, Any]]

    thinking: Optional[str]
    route: Optional[str]

    tool_call: Optional[Dict[str, Any]]
    tool_result: Optional[Any]

    memory_context: Optional[List[str]]

    should_store_memory: Optional[bool]
    memory_summary: Optional[str]
