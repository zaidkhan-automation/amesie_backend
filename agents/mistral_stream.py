# agents/mistral_stream.py

import os
from mistralai import Mistral
from sqlalchemy.orm import Session
from typing import Dict, Any, Generator

from core.database import SessionLocal
from db.conversations import insert_thread
from ingestion.summarize import maybe_summarize_conversation
from memory.context_loader import load_conversation_context
from memory.context_builder import build_context_prompt
from agents.system_prompt import SYSTEM_PROMPT
from vectorstore.qdrant_reader import retrieve_reinforced_facts

# FACT EXTRACTION (STEP 2)
from llm.fact_extractor import extract_user_facts
from services.user_facts_writer import insert_user_fact

MODEL_NAME = "mistral-large-latest"

SUMMARY_TRIGGER_TOKENS = 3000
MAX_CONTEXT_TOKENS = 1500

client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])


def approx_token_count(text: str) -> int:
    return max(1, len(text) // 4)


def stream_chat(
    *,
    chat_id: str,
    user_message: str,
    temperature: float = 0.3,
) -> Generator[str, None, None]:
    """
    STREAM-ONLY CHAT.
    ❌ Does NOT execute tools
    ❌ Does NOT loop
    ✅ Safe with LangGraph
    """

    db: Session = SessionLocal()

    try:
        # ─── 1️⃣ Load past conversation ───────────
        threads, latest_summary = load_conversation_context(db, chat_id)

        recent_threads = [
            {
                "user": t["user_raw_text"],
                "assistant": t["assistant_raw_text"],
            }
            for t in threads
        ]

        # ─── 2️⃣ Semantic recall ─────────────────
        semantic_hits = retrieve_reinforced_facts(
            user_id=chat_id,
            query=user_message,
            limit=5,
        )

        semantic_block = ""
        if semantic_hits:
            semantic_block = "SEMANTIC MEMORY:\n"
            for h in semantic_hits:
                semantic_block += f"- {h['text']}\n"

        # ─── 3️⃣ Context assembly ────────────────
        context_prompt = build_context_prompt(
            chat_id=chat_id,
            recent_threads=recent_threads,
            latest_summary=latest_summary,
            tokenizer=lambda t: t.split(),
            max_tokens=MAX_CONTEXT_TOKENS,
        )

        final_prompt = f"""{SYSTEM_PROMPT}

{semantic_block}

{context_prompt}

User: {user_message}
Assistant:
"""

        # ─── 4️⃣ Stream response (NO TOOLS) ──────
        stream = client.chat.stream(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": final_prompt}],
            temperature=temperature,
        )

        assistant_text = ""

        for event in stream:
            delta = event.data.choices[0].delta
            chunk = delta.content

            # 🚨 HARD GUARD: If model tries tool calling here
            if hasattr(delta, "tool_calls") and delta.tool_calls:
                yield "\n[Action required. Switching execution path.]\n"
                return

            if chunk:
                assistant_text += chunk
                yield chunk

        # ─── 5️⃣ Persist conversation ────────────
        insert_thread(
            db=db,
            chat_id=chat_id,
            user_text=user_message,
            assistant_text=assistant_text,
        )

        # ─── 6️⃣ Background fact extraction ──────
        try:
            facts = extract_user_facts(
                latest_message=user_message,
                previous_messages=[t["user"] for t in recent_threads[-2:]],
            )

            for fact in facts:
                insert_user_fact(
                    db=db,
                    user_id=str(chat_id),
                    fact_key=fact["fact_key"],
                    fact_value=fact["fact_value"],
                    confidence=fact.get("confidence", 0.3),
                )
        except Exception:
            pass  # NEVER break chat

        # ─── 7️⃣ Summarization trigger ───────────
        total_tokens = approx_token_count(
            semantic_block + context_prompt + user_message + assistant_text
        )

        if total_tokens >= SUMMARY_TRIGGER_TOKENS:
            maybe_summarize_conversation(db, chat_id)

        db.commit()

    finally:
        db.close()
