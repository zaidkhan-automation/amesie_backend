# agents/langgraph/nodes/memory_loader.py

from agents.langgraph.state import AgentState
from agents.memory import search_long_term_memory

def memory_loader(state: AgentState) -> AgentState:
    try:
        seller_id = int(state["user_id"])
        memory = search_long_term_memory(seller_id=seller_id)
    except Exception:
        memory = []

    return {
        **state,
        "memory_context": memory or [],
    }
