# agents/mistral_stream.py

import os
from mistralai import Mistral

client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])


def stream_chat(prompt: str, temperature: float = 0.3):
    """
    Proper token streaming for Mistral SDK (current version).
    Yields text chunks as they arrive.
    """

    stream = client.chat.stream(
        model="mistral-large-latest",
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )

    for event in stream:
        try:
            # Safely drill down into delta content
            chunk = event.data.choices[0].delta.content
            if chunk:
                yield chunk
        except Exception:
            # Ignore non-delta events (start/end/usage/etc)
            continue
