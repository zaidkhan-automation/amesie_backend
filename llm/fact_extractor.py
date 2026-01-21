# llm/fact_extractor.py

import os
import json
from mistralai import Mistral

MODEL_NAME = "mistral-small-latest"

client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])


SYSTEM_PROMPT = """
You are a background fact-extraction module.

Your job is to extract ONLY explicit user facts stated by the user.
Do NOT guess, infer, assume, or paraphrase.

A valid user fact MUST:
- Be explicitly stated by the user
- Be about the user themselves
- Not be a question, joke, example, or hypothetical

IMPORTANT:
Statements like:
- "my name is X"
- "I am called X"
- "I live in X"
ARE considered explicit user facts.

If no clear fact is present, return an empty list.

Return JSON ONLY.
"""

def extract_user_facts(
    *,
    latest_message: str,
    previous_messages: list[str] | None = None,
) -> list[dict]:
    """
    Returns a list of extracted facts.
    If none found, returns [].
    """

    context = ""
    if previous_messages:
        context = "\n".join(previous_messages[-2:])

    user_prompt = f"""
LATEST USER MESSAGE:
{latest_message}

PREVIOUS USER CONTEXT (optional):
{context}

OUTPUT FORMAT:
{{
  "facts": [
    {{
      "fact_key": "name",
      "fact_value": "Ahmed",
      "confidence": 0.55
    }}
  ]
}}
"""

    response = client.chat.complete(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,  # IMPORTANT: deterministic
    )

    raw = response.choices[0].message.content.strip()

    try:
        parsed = json.loads(raw)
    except Exception:
        return []

    facts = parsed.get("facts", [])

    # HARD GUARD: ensure exactness
    clean_facts = []
    for f in facts:
        if (
            isinstance(f, dict)
            and isinstance(f.get("fact_key"), str)
            and isinstance(f.get("fact_value"), str)
        ):
            clean_facts.append(
                {
                    "fact_key": f["fact_key"].strip().lower(),
                    "fact_value": f["fact_value"].strip(),
                    "confidence": float(f.get("confidence", 0.3)),
                }
            )

    return clean_facts
