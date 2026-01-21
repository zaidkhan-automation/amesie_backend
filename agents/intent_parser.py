# agents/intent_parser.py
import re

INTENT_PATTERNS = {
    "list_products": re.compile(r"^(list|show)\s+my\s+products$"),
    "delete_product": re.compile(r"^delete\s+product\s+\d+$"),
    "update_stock": re.compile(r"^update\s+stock\s+\d+\s+\d+$"),
    "dashboard": re.compile(r".*\bdashboard\b.*"),
}

def parse_intent(message: str):
    msg = message.lower().strip()
    for intent, pattern in INTENT_PATTERNS.items():
        if pattern.match(msg):
            return intent
    return "chat_only"
