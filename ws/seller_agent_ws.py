# ws/seller_agent_ws.py

import uuid
import json
import os
import traceback
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import jwt, JWTError

from core.database import SessionLocal
from memory.context_loader import load_conversation_context

from services.fact_reinforce import reinforce_fact, contradict_fact
from services.fact_detect import detect_fact_confirmation

from agents.langgraph.graph import agent_app

router = APIRouter()

SECRET_KEY = os.environ["JWT_SECRET"]
ALGORITHM = "HS256"


@router.websocket("/ws/seller/agent")
async def seller_agent_ws(ws: WebSocket):
    await ws.accept()

    chat_id = None
    seller_id = None
    messages: list[dict] = []

    try:
        # ─── AUTH HANDSHAKE (LOOP UNTIL VALID) ───────────
        while True:
            raw = await ws.receive_text()

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_text(json.dumps({
                    "type": "auth_required",
                    "message": "Send JSON first: { token, chat_id }"
                }))
                continue

            token = data.get("token")
            chat_id = data.get("chat_id")

            if not token:
                await ws.send_text(json.dumps({
                    "type": "error",
                    "message": "Missing JWT token"
                }))
                continue

            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            except JWTError:
                await ws.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid or expired token"
                }))
                continue

            seller_id = payload.get("seller_id")
            if not seller_id:
                await ws.send_text(json.dumps({
                    "type": "error",
                    "message": "seller_id missing in token"
                }))
                continue

            if not chat_id:
                chat_id = f"chat_{uuid.uuid4()}"
                await ws.send_text(json.dumps({
                    "type": "chat_init",
                    "chat_id": chat_id
                }))
            else:
                await ws.send_text(json.dumps({
                    "type": "chat_resume",
                    "chat_id": chat_id
                }))

            await ws.send_text(json.dumps({
                "type": "ready",
                "message": "Seller agent ready"
            }))
            break

        # ─── MAIN CHAT LOOP (SAME AS PYTHON TESTS) ───────
        while True:
            msg = (await ws.receive_text()).strip()
            if not msg:
                continue

            # ─── FACT MEMORY (NON BLOCKING) ────────────
            try:
                signal = detect_fact_confirmation(
                    user_message=msg,
                    chat_id=chat_id,
                )
                if signal:
                    if signal["type"] == "reinforce":
                        reinforce_fact(
                            user_id=chat_id,
                            fact_key=signal["fact_key"],
                            fact_value=signal["fact_value"],
                        )
                    elif signal["type"] == "contradict":
                        contradict_fact(
                            user_id=chat_id,
                            fact_key=signal["fact_key"],
                            fact_value=signal["fact_value"],
                        )
            except Exception:
                pass

            # ─── LOAD MEMORY CONTEXT ───────────────────
            db = SessionLocal()
            _, summary = load_conversation_context(db, chat_id)
            db.close()

            messages.append({
                "role": "user",
                "content": msg
            })

            state = {
                "chat_id": chat_id,
                "user_id": seller_id,
                "messages": messages,
                "tool_call": None,
                "tool_result": None,
                "memory_context": summary or [],
            }

            # 🔥 EXACT SAME PATH AS WORKING PY TESTS
            result = agent_app.invoke(state)

            if not result or "messages" not in result:
                await ws.send_text(json.dumps({
                    "type": "assistant",
                    "content": "Something went wrong."
                }))
                continue

            messages = result["messages"]
            last = messages[-1]

            await ws.send_text(json.dumps({
                "type": "assistant",
                "content": last.get("content", "")
            }))

    except WebSocketDisconnect:
        return

    except Exception as e:
        traceback.print_exc()
        try:
            await ws.send_text(json.dumps({
                "type": "error",
                "message": str(e)
            }))
        except Exception:
            pass
