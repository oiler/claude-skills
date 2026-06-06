from extract_session import extract_prompts


def test_extract_prompts_filters_and_strips():
    records = [
        # 1. plain-string prompt -> kept verbatim
        {"type": "user", "message": {"content": "hello world"}},
        # 2. text-block prompt with appended system-reminder -> reminder stripped
        {"type": "user", "message": {"content": [
            {"type": "text",
             "text": "do the thing\n<system-reminder>injected</system-reminder>"}]}},
        # 3. skill-injected meta record -> excluded
        {"type": "user", "isMeta": True, "message": {"content": [
            {"type": "text", "text": "Base directory: /x"}]}},
        # 4. tool_result (not a prompt) -> excluded
        {"type": "user", "message": {"content": [
            {"type": "tool_result", "content": "result blob"}]}},
        # 5. reminder-only prompt -> empty after strip -> skipped
        {"type": "user", "message": {"content": [
            {"type": "text", "text": "<system-reminder>only</system-reminder>"}]}},
        # 6. assistant turn -> excluded
        {"type": "assistant", "message": {"content": [
            {"type": "text", "text": "hi"}]}},
    ]
    assert extract_prompts(records) == ["hello world", "do the thing"]
