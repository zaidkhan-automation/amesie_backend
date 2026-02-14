from agents.langgraph.state import AgentState
from agents.memory import add_long_term_memory
from core.logger import get_logger

log = get_logger("MEMORY")

def memory_writer(state: AgentState) -> AgentState:
    summary = state.get("memory_summary")
    if not summary:
        return state

    try:
        seller_id = int(state["user_id"])
        add_long_term_memory(
            seller_id=seller_id,
            text=summary,
            metadata={"source": "conversation"},
        )
        log.info(
            "MEMORY_WRITE user_id=%s summary=%r",
            seller_id,
            summary,
        )
    except Exception as e:
        log.exception(
            "MEMORY_WRITE_FAIL user_id=%s error=%s",
            state.get("user_id"),
            str(e),
        )

    return state
