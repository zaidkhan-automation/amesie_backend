import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.database import SessionLocal
from memory.context_loader import load_conversation_context
from core.logger import get_logger
from ws.session_store import ACTIVE_WS_SESSIONS
from agents.langgraph.graph import agent_app

router = APIRouter()
log = get_logger("WS")


@router.websocket("/ws/seller/agent")
async def seller_agent_ws(ws: WebSocket):

    conversation_id = ws.query_params.get("conversation_id")

    if not conversation_id:
        await ws.close(code=1008)
        return

    seller_id = ACTIVE_WS_SESSIONS.get(conversation_id)

    if not seller_id:
        await ws.close(code=1008)
        return

    await ws.accept()

    await ws.send_text(json.dumps({
        "event": "ready",
        "conversation_id": conversation_id
    }))

    messages = []

    try:
        while True:

            user_msg = await ws.receive_text()
            user_msg = user_msg.strip()

            if not user_msg:
                continue

            if user_msg.startswith("{") or user_msg.startswith("["):
                await ws.send_text(json.dumps({
                    "event": "response",
                    "status": "start"
                }))
                await ws.send_text(json.dumps({
                    "event": "response",
                    "status": "stream",
                    "data": {"text": "I can’t process raw JSON input."}
                }))
                await ws.send_text(json.dumps({
                    "event": "response",
                    "status": "end"
                }))
                continue

            messages.append({"role": "user", "content": user_msg})

            # Load memory
            db = SessionLocal()
            _, memory = load_conversation_context(db, conversation_id)
            db.close()

            state = {
                "chat_id": conversation_id,
                "user_id": seller_id,
                "messages": messages,
                "tool_call": None,
                "tool_result": None,
                "memory_context": memory or [],
            }

            # -----------------------------
            # RUN LANGGRAPH ONCE
            # -----------------------------
            final_state = agent_app.invoke(state)

            # -----------------------------
            # THINKING PHASE
            # -----------------------------
            await ws.send_text(json.dumps({
                "event": "thinking",
                "status": "start"
            }))

            thinking_text = final_state.get("thinking")

            if thinking_text:
                await ws.send_text(json.dumps({
                    "event": "thinking",
                    "status": "stream",
                    "data": {"text": thinking_text}
                }))

            await ws.send_text(json.dumps({
                "event": "thinking",
                "status": "end"
            }))

            # -----------------------------
            # ACTION PHASE (IF TOOL)
            # -----------------------------
            if final_state.get("tool_result") is not None:
                await ws.send_text(json.dumps({
                    "event": "action",
                    "status": "stream",
                    "data": {
                        "step": 1,
                        "text": "Executing tool"
                    }
                }))

            # -----------------------------
            # RESPONSE PHASE
            # -----------------------------
            await ws.send_text(json.dumps({
                "event": "response",
                "status": "start"
            }))

            final_messages = final_state.get("messages", [])

            if final_messages:
                last_msg = final_messages[-1]
                if last_msg.get("role") == "assistant":
                    text = last_msg.get("content", "")

                    # simulate streaming token by token
                    for token in text.split():
                        await ws.send_text(json.dumps({
                            "event": "response",
                            "status": "stream",
                            "data": {"text": token + " "}
                        }))

            await ws.send_text(json.dumps({
                "event": "response",
                "status": "end"
            }))

            # Keep last 30 messages only
            messages = final_messages[-30:]

    except WebSocketDisconnect:
        log.info("WS_DISCONNECT seller_id=%s", seller_id)

    except Exception as e:
        log.exception("WS_FATAL seller_id=%s error=%s", seller_id, str(e))

    finally:
        # DO NOT close session per message
        ACTIVE_WS_SESSIONS.pop(conversation_id, None)
        try:
            await ws.close()
        except Exception:
            pass
