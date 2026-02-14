from agents.langgraph.state import AgentState

IMPORTANT_TRIGGERS = (
    "remember",
    "my name is",
    "i am",
    "i work",
    "i like",
    "i prefer",
    "always",
    "never",
    "important",
)

CONFIRM_WORDS = ("yes", "confirm", "okay", "sure")

def memory_classifier(state: AgentState) -> AgentState:
    messages = state.get("messages", [])
    if not messages:
        return {**state, "should_store_memory": False}

    last = messages[-1]["content"].lower()

    pending = state.get("memory_pending")

    # Step 1: detect memory intent
    if any(t in last for t in IMPORTANT_TRIGGERS):
        return {
            **state,
            "should_store_memory": False,
            "memory_pending": last,
        }

    # Step 2: explicit confirmation
    if pending and any(w == last.strip() for w in CONFIRM_WORDS):
        return {
            **state,
            "should_store_memory": True,
            "memory_pending": None,
        }

    return {
        **state,
        "should_store_memory": False,
        "memory_pending": pending,
    }
