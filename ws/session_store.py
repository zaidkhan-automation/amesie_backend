# ws/session_store.py

from typing import Dict

# ⚠️ Replace with Redis in production
ACTIVE_WS_SESSIONS: Dict[str, int] = {}
