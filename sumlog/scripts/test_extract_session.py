from pathlib import Path

from extract_session import (
    extract_prompts,
    build_metadata,
    render_metadata_yaml,
    assemble_document,
    resolve_output_path,
    tilde,
    extract_agents,
    build_agents_markdown,
    extract_tasks,
    build_tasks_markdown,
)


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


def test_build_metadata_counts_tools_and_dedupes_files():
    records = [
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Read", "input": {"file_path": "/a/b.py"}},
            {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}}]}},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Read", "input": {"file_path": "/a/b.py"}},
            {"type": "tool_use", "name": "Write", "input": {"file_path": "/a/c.py"}}]}},
        {"type": "user", "message": {"content": "not counted"}},
    ]
    meta = build_metadata(records)
    assert meta["tools_used"] == {"Read": 2, "Bash": 1, "Write": 1}
    assert meta["files_touched"] == ["/a/b.py", "/a/c.py"]  # deduped, order preserved


def test_build_metadata_handles_file_tool_without_path():
    # A file-tool (Edit) with missing file_path should be counted but not crash or add to files
    records = [
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Edit", "input": {}}]}},
    ]
    meta = build_metadata(records)
    assert meta["tools_used"] == {"Edit": 1}
    assert meta["files_touched"] == []


def test_build_metadata_collects_notebookedit_path():
    # NotebookEdit is a file-tool; file paths should be collected
    records = [
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "NotebookEdit", "input": {"file_path": "/nb/x.ipynb"}}]}},
    ]
    meta = build_metadata(records)
    assert meta["tools_used"] == {"NotebookEdit": 1}
    assert meta["files_touched"] == ["/nb/x.ipynb"]


def test_render_metadata_yaml_orders_and_nests():
    meta = {
        "session_id": "abc",
        "date": "2026-06-06",
        "cwd": "/x",
        "git_branch": "master",
        "prompt_count": 2,
        "tools_used": {"Read": 2, "Bash": 1},
        "files_touched": ["/x/a.py", "/x/b.py"],
    }
    assert render_metadata_yaml(meta) == (
        "session_id: abc\n"
        "date: 2026-06-06\n"
        "cwd: /x\n"
        "git_branch: master\n"
        "prompt_count: 2\n"
        "tools_used:\n"
        "  Read: 2\n"
        "  Bash: 1\n"
        "files_touched:\n"
        "  - /x/a.py\n"
        "  - /x/b.py"
    )


def test_render_metadata_yaml_empty_collections():
    meta = {
        "session_id": "abc",
        "date": "2026-06-06",
        "cwd": "/x",
        "git_branch": None,
        "prompt_count": 0,
        "tools_used": {},
        "files_touched": [],
    }
    out = render_metadata_yaml(meta)
    assert "git_branch: null\n" in out
    assert "tools_used: {}\n" in out
    assert out.endswith("files_touched: []")


def test_assemble_document_structure_and_verbatim_prompts():
    meta = {
        "session_id": "abc",
        "date": "2026-06-06",
        "cwd": "/x",
        "git_branch": "master",
        "prompt_count": 1,
        "tools_used": {"Read": 1},
        "files_touched": [],
    }
    prompts_md = "## Prompts (chronological)\n\n### Prompt 1\n\nhello world\n"
    doc = assemble_document("my-slug", "A short summary.", prompts_md, meta, "goal: ship it\n")
    assert doc.startswith("# Session Log — 2026-06-06 — my-slug\n")
    assert "## Summary\n\nA short summary.\n" in doc
    # prompts spliced byte-exact (no reformatting/truncation)
    assert prompts_md.rstrip("\n") in doc
    assert "## Handoff State\n\n```yaml\n" in doc
    assert "session_id: abc\n" in doc
    assert "goal: ship it" in doc
    assert doc.endswith("```\n")


def test_tilde_shorthands_home_paths():
    home = str(Path.home())
    assert tilde(home + "/files/x.py") == "~/files/x.py"
    assert tilde(home) == "~"
    # paths outside $HOME are left absolute (cannot be shorthanded)
    assert tilde("/tmp/x") == "/tmp/x"
    assert tilde("/var/data") == "/var/data"
    # a sibling dir that merely shares the home prefix string must not be rewritten
    assert tilde(home + "-backup/x") == home + "-backup/x"


def test_build_metadata_tildes_home_paths():
    home = str(Path.home())
    records = [
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Read", "input": {"file_path": home + "/proj/x.py"}},
            {"type": "tool_use", "name": "Write", "input": {"file_path": "/tmp/out.md"}}]}},
    ]
    meta = build_metadata(records)
    assert meta["files_touched"] == ["~/proj/x.py", "/tmp/out.md"]


def test_extract_agents_joins_dispatch_and_result():
    records = [
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "tu1", "name": "Agent",
             "input": {"description": "Do X", "subagent_type": "general-purpose",
                       "model": "haiku", "prompt": "..."}},
            {"type": "tool_use", "id": "b1", "name": "Bash", "input": {"command": "ls"}}]}},
        # the structured result rides on a user record whose tool_result links via tool_use_id
        {"type": "user", "toolUseResult": {
            "status": "completed", "agentId": "aid1", "agentType": "general-purpose",
            "totalTokens": 14647, "totalToolUseCount": 4, "totalDurationMs": 10806},
         "message": {"content": [{"type": "tool_result", "tool_use_id": "tu1", "content": "done"}]}},
    ]
    agents = extract_agents(records)
    assert len(agents) == 1  # the Bash tool_use is not an agent
    a = agents[0]
    assert a["label"] == "Do X"
    assert a["agent_type"] == "general-purpose"
    assert a["model"] == "haiku"
    assert a["status"] == "completed"
    assert a["tokens"] == 14647
    assert a["tool_uses"] == 4
    assert a["duration_ms"] == 10806


def test_extract_agents_dispatch_without_result():
    records = [
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "tu9", "name": "Agent",
             "input": {"description": "Pending", "subagent_type": "general-purpose"}}]}},
    ]
    agents = extract_agents(records)
    assert len(agents) == 1
    assert agents[0]["status"] == "(no result)"
    assert agents[0]["model"] == "inherit"  # no model in input -> inherited
    assert agents[0]["tokens"] == 0


def test_build_agents_markdown_empty_is_blank():
    assert build_agents_markdown([]) == ""


def test_build_agents_markdown_table_and_totals():
    agents = [
        {"label": "Do X", "agent_type": "general-purpose", "model": "haiku",
         "status": "completed", "tokens": 14647, "tool_uses": 4, "duration_ms": 10806},
        {"label": "Do Y", "agent_type": "general-purpose", "model": "sonnet",
         "status": "completed", "tokens": 2000, "tool_uses": 1, "duration_ms": 500},
    ]
    md = build_agents_markdown(agents)
    assert md.startswith("## Agents Dispatched\n")
    assert "| 1 | Do X | general-purpose | haiku | completed | 14,647 | 4 | 10.8s |" in md
    assert "| 2 | Do Y | general-purpose | sonnet | completed | 2,000 | 1 | 0.5s |" in md
    assert "2 agents" in md
    assert "16,647" in md  # total subagent tokens


def test_build_agents_markdown_escapes_pipe_in_label():
    agents = [{"label": "a | b", "agent_type": "x", "model": "haiku",
               "status": "completed", "tokens": 1, "tool_uses": 0, "duration_ms": 0}]
    md = build_agents_markdown(agents)
    assert "a \\| b" in md  # pipe escaped so it doesn't break the table


def _create(call_id, task_id, subject, description=""):
    return [
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": call_id, "name": "TaskCreate",
             "input": {"subject": subject, "description": description}}]}},
        {"type": "user", "toolUseResult": {"task": {"id": task_id, "subject": subject}},
         "message": {"content": [{"type": "tool_result", "tool_use_id": call_id, "content": "created"}]}},
    ]


def _update(call_id, task_id, to, success=True, frm="pending"):
    res = ({"success": True, "taskId": task_id, "statusChange": {"from": frm, "to": to}}
           if success else {"success": False, "taskId": task_id, "error": "Task not found"})
    return [
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": call_id, "name": "TaskUpdate",
             "input": {"taskId": task_id, "status": to}}]}},
        {"type": "user", "toolUseResult": res,
         "message": {"content": [{"type": "tool_result", "tool_use_id": call_id, "content": "ok"}]}},
    ]


def test_extract_tasks_replays_create_and_update():
    records = (
        _create("c1", "1", "Build it", "desc")
        + _update("u1", "1", "in_progress", frm="pending")
        + _update("u2", "1", "completed", frm="in_progress")
    )
    assert extract_tasks(records) == [{"id": "1", "subject": "Build it", "status": "completed"}]


def test_extract_tasks_preserves_creation_order():
    records = _create("c1", "1", "First") + _create("c2", "2", "Second")
    assert [t["id"] for t in extract_tasks(records)] == ["1", "2"]


def test_extract_tasks_ignores_failed_update():
    records = _create("c1", "1", "X") + _update("u1", "1", "completed", success=False)
    # a failed TaskUpdate ("Task not found") must not change status
    assert extract_tasks(records) == [{"id": "1", "subject": "X", "status": "pending"}]


def test_extract_tasks_todowrite_fallback():
    records = [
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "t1", "name": "TodoWrite", "input": {"todos": [
                {"content": "A", "status": "completed", "activeForm": "Aing"},
                {"content": "B", "status": "in_progress", "activeForm": "Bing"}]}}]}},
    ]
    assert extract_tasks(records) == [
        {"id": "1", "subject": "A", "status": "completed"},
        {"id": "2", "subject": "B", "status": "in_progress"},
    ]


def test_build_tasks_markdown_empty_is_blank():
    assert build_tasks_markdown([]) == ""


def test_build_tasks_markdown_table_and_totals():
    tasks = [
        {"id": "1", "subject": "Build it", "status": "completed"},
        {"id": "2", "subject": "Test it", "status": "in_progress"},
    ]
    md = build_tasks_markdown(tasks)
    assert md.startswith("## Task List\n")
    assert "| 1 | Build it | completed |" in md
    assert "| 2 | Test it | in_progress |" in md
    assert "2 tasks, 1 completed" in md


def test_resolve_output_path_collision_suffix(tmp_path):
    p1 = resolve_output_path("topic", "2026-06-06", tmp_path)
    assert p1.name == "2026-06-06-topic.md"
    p1.write_text("x")
    p2 = resolve_output_path("topic", "2026-06-06", tmp_path)
    assert p2.name == "2026-06-06-topic-2.md"
    p2.write_text("x")
    p3 = resolve_output_path("topic", "2026-06-06", tmp_path)
    assert p3.name == "2026-06-06-topic-3.md"
