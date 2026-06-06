from extract_session import extract_prompts


def test_extract_prompts_keeps_genuine_prompts():
    records = [
        # plain-string prompt -> kept verbatim
        {"type": "user", "message": {"content": "hello world"}},
        # text-block prompt with appended system-reminder -> reminder stripped, rest kept
        {"type": "user", "message": {"content": [
            {"type": "text",
             "text": "do the thing\n<system-reminder>injected</system-reminder>"}]}},
    ]
    assert extract_prompts(records) == ["hello world", "do the thing"]


def test_extract_prompts_excludes_non_prompts():
    records = [
        # skill-injected meta record -> excluded
        {"type": "user", "isMeta": True, "message": {"content": [
            {"type": "text", "text": "Base directory: /x"}]}},
        # tool_result (not a prompt) -> excluded
        {"type": "user", "message": {"content": [
            {"type": "tool_result", "content": "result blob"}]}},
        # reminder-only prompt -> empty after strip -> excluded
        {"type": "user", "message": {"content": [
            {"type": "text", "text": "<system-reminder>only</system-reminder>"}]}},
        # assistant turn -> excluded
        {"type": "assistant", "message": {"content": [
            {"type": "text", "text": "hi"}]}},
    ]
    assert extract_prompts(records) == []


def test_extract_prompts_joins_multiple_text_blocks():
    # A single user record with two text blocks -> joined with "\n"
    records = [
        {"type": "user", "message": {"content": [
            {"type": "text", "text": "first line"},
            {"type": "text", "text": "second line"},
        ]}},
    ]
    assert extract_prompts(records) == ["first line\nsecond line"]
