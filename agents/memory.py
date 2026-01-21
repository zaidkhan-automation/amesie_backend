# agents/memory.py
from collections import defaultdict, deque
from typing import List, Dict

MAX_MESSAGES = 12

_memory: Dict[int, deque] = defaultdict(
    lambda: deque(maxlen=MAX_MESSAGES)
)

def add_message(session_id: int, role: str, content: str):
    if role not in ("user", "assistant"):
        return

    text = content.strip()

    # ❌ NEVER STORE TOOL / JSON / CONTROL OUTPUT
    if text.startswith("{") or text.startswith("["):
        return
    if "tool" in text.lower():
        return

    _memory[session_id].append({
        "role": role,
        "content": text,
    })

def get_messages(session_id: int) -> List[dict]:
    return list(_memory[session_id])

def clear_session(session_id: int):
    _memory.pop(session_id, None)
