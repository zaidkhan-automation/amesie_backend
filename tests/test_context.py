from memory.context_builder import build_context_prompt

def test_context_builder():
    threads = [
        ("hello", "hi there"),
        ("create product", "what is the name?"),
    ]

    class FakeSummary:
        user_summary = "User wants to create a product"
        assistant_summary = "Assistant asked for details"

    context = build_context_prompt(
        chat_id="test_chat",
        recent_threads=threads,
        latest_summary=FakeSummary(),
        tokenizer=lambda x: x.split(),  # fake tokenizer
    )

    print(context)

test_context_builder()
