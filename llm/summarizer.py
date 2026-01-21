# llm/summarizer.py

from mistralai import Mistral
import os

client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

MAX_TOKENS_FOR_FULL_EMBED = 300  # ~1200 chars

def should_summarize(text: str) -> bool:
    return len(text.split()) > MAX_TOKENS_FOR_FULL_EMBED


def summarize(text: str) -> str:
    res = client.chat.complete(
        model="mistral-small-latest",
        messages=[
            {
                "role": "user",
                "content": (
                    "Summarize the following text in 1–2 sentences. "
                    "Preserve meaning, remove noise:\n\n" + text
                ),
            }
        ],
        temperature=0.2,
    )
    return res.choices[0].message.content.strip()
