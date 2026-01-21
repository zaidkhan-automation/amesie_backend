# utils/token_counter.py

def count_tokens(text: str, tokenizer) -> int:
    if not text:
        return 0
    return len(tokenizer.encode(text))            
