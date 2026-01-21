# memory/summarizer.py

def summarize_conversation(
    user_text: str,
    assistant_text: str,
    llm_client,
) -> dict:
    prompt = f"""
You are summarizing a conversation for long-term memory.

Rules:
- Be concise and factual
- Preserve user intent, constraints, and decisions
- Remove chit-chat and repetition
- Do NOT invent information
- Output plain text only

Conversation:
USER:
{user_text}

ASSISTANT:
{assistant_text}

Return:
User summary and assistant summary separately.
"""

    response = llm_client.generate(prompt)

    # Expected simple split (keep it boring and safe)
    return {
        "user": response["user_summary"],
        "assistant": response["assistant_summary"],
    }
