import os
from mistralai import Mistral

AGENT_ID = "ag_01b5fa17e4a743fa6ee6559b78ad319"

client = Mistral(
    api_key=os.environ.get("MISTRAL_API_KEY")
)

def run_seller_agent(message: str):
    response = client.beta.conversations.start(
        agent_id=AGENT_ID,
        inputs=message,
    )
    return response
