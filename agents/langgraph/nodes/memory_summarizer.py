from agents.langgraph.state import AgentState
from agents.mistral_client import call_mistral_with_tools

SUMMARY_PROMPT = """
Summarize the conversation into ONE short factual sentence.

Rules:
- Only durable facts (name, identity, preferences, decisions)
- Ignore greetings, jokes, calculations, tools
- One sentence only
- Plain text
"""

def memory_summarizer(state: AgentState) -> AgentState:
    # hard stop if classifier said no
    if not state.get("should_store_memory"):
        return {
            **state,
            "memory_summary": None,
        }

    messages = state.get("messages", [])
    if not messages:
        return {
            **state,
            "memory_summary": None,
        }

    convo = "\n".join(
        f"{m['role']}: {m['content']}"
        for m in messages[-6:]
        if m.get("role") in ("user", "assistant")
        and isinstance(m.get("content"), str)
    )

    if not convo.strip():
        return {
            **state,
            "memory_summary": None,
        }

    try:
        response = call_mistral_with_tools(
            messages=[
                {"role": "system", "content": SUMMARY_PROMPT},
                {"role": "user", "content": convo},
            ],
            tools=[],
            timeout=6,
        )
        summary = response.get("content", "").strip()
        if not summary:
            summary = None

    except Exception:
        summary = None

    return {
        **state,
        "memory_summary": summary,
    }
