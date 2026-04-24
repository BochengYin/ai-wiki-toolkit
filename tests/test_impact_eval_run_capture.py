from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import subprocess
import sys


def _load_script(script_name: str):
    script_path = (
        Path(__file__).resolve().parents[1]
        / "evals"
        / "impact"
        / "scripts"
        / script_name
    )
    script_dir = str(script_path.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = spec_from_file_location(script_name.replace(".py", ""), script_path)
    assert spec is not None
    module = module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _git(repo: Path, *command: str) -> str:
    result = subprocess.run(
        ["git", *command],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-b", "main"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Eval User"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "eval@example.com"],
        cwd=path,
        check=True,
        capture_output=True,
    )


def test_init_run_creates_external_result_slots(tmp_path: Path) -> None:
    module = _load_script("init_run.py")
    workspace_root = tmp_path / "workspaces"
    output_root = tmp_path / "runs"
    for variant in module.DEFAULT_MEMORY_AXIS_VARIANTS:
        (workspace_root / variant).mkdir(parents=True)

    run_dir = output_root / "ownership_boundary" / "run_manual_test"
    module.create_result_slots(
        run_dir,
        experiment="ownership_boundary",
        workspace_root=workspace_root,
        variants=module.DEFAULT_MEMORY_AXIS_VARIANTS,
        prompt_levels=("medium",),
    )
    module.write_metadata(
        run_dir,
        experiment="ownership_boundary",
        workspace_root=workspace_root,
        variants=module.DEFAULT_MEMORY_AXIS_VARIANTS,
        prompt_levels=("medium",),
        notes="test",
    )

    assert (run_dir / "metadata.json").exists()
    metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["experiment"] == "ownership_boundary"
    assert metadata["variants"] == list(module.DEFAULT_MEMORY_AXIS_VARIANTS)
    assert (run_dir / "plain_repo_no_aiwiki" / "medium" / "README.md").exists()


def test_init_run_default_paths_use_first_round_layout() -> None:
    module = _load_script("init_run.py")
    assert module.default_workspace_root("ownership_boundary") == Path(
        "/private/tmp/aiwiki_first_round/ownership_boundary/workspaces"
    )
    assert module.default_output_root("release_distribution_integrity") == Path(
        "/private/tmp/aiwiki_first_round/release_distribution_integrity/runs"
    )


def test_save_result_captures_diff_and_message(tmp_path: Path) -> None:
    module = _load_script("save_result.py")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _init_repo(workspace)
    (workspace / "tracked.txt").write_text("before\n", encoding="utf-8")
    _git(workspace, "add", ".")
    _git(workspace, "commit", "-m", "init")
    (workspace / "tracked.txt").write_text("after\n", encoding="utf-8")
    (workspace / "new_file.txt").write_text("new\n", encoding="utf-8")

    run_dir = tmp_path / "runs" / "run_001"
    slot = run_dir / "aiwiki_consolidated" / "medium"
    slot.mkdir(parents=True)
    final_message = tmp_path / "final_message.md"
    final_message.write_text("agent summary\n", encoding="utf-8")

    original_argv = sys.argv
    sys.argv = [
        "save_result.py",
        "--run-dir",
        str(run_dir),
        "--variant",
        "aiwiki_consolidated",
        "--prompt-level",
        "medium",
        "--workspace",
        str(workspace),
        "--final-message",
        str(final_message),
        "--attempt",
        "2",
        "--human-nudges",
        "1",
        "--first-pass-failure",
        "--notes",
        "manual capture",
    ]
    try:
        module.main()
    finally:
        sys.argv = original_argv

    assert (slot / "final_message.md").read_text(encoding="utf-8") == "agent summary\n"
    diff_text = (slot / "workspace_diff.patch").read_text(encoding="utf-8")
    assert "tracked.txt" in diff_text
    assert "new_file.txt" in diff_text
    assert "/dev/null" in diff_text
    result = json.loads((slot / "result.json").read_text(encoding="utf-8"))
    assert result["attempt"] == 2
    assert result["human_nudges"] == 1
    assert result["first_pass_success"] is False
    assert result["changed_files"] == ["tracked.txt", "new_file.txt"]
    assert result["untracked_files"] == ["new_file.txt"]


def test_save_result_accepts_final_message_already_in_slot(tmp_path: Path) -> None:
    module = _load_script("save_result.py")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _init_repo(workspace)
    (workspace / "tracked.txt").write_text("before\n", encoding="utf-8")
    _git(workspace, "add", ".")
    _git(workspace, "commit", "-m", "init")
    (workspace / "tracked.txt").write_text("after\n", encoding="utf-8")

    run_dir = tmp_path / "runs" / "run_001"
    slot = run_dir / "aiwiki_consolidated" / "medium"
    slot.mkdir(parents=True)
    final_message = slot / "final_message.md"
    final_message.write_text("already here\n", encoding="utf-8")

    original_argv = sys.argv
    sys.argv = [
        "save_result.py",
        "--run-dir",
        str(run_dir),
        "--variant",
        "aiwiki_consolidated",
        "--prompt-level",
        "medium",
        "--workspace",
        str(workspace),
        "--final-message",
        str(final_message),
    ]
    try:
        module.main()
    finally:
        sys.argv = original_argv

    assert (slot / "final_message.md").read_text(encoding="utf-8") == "already here\n"
    assert (slot / "workspace_diff.patch").exists()


def test_save_result_skips_missing_final_message(tmp_path: Path, capsys) -> None:
    module = _load_script("save_result.py")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _init_repo(workspace)
    (workspace / "tracked.txt").write_text("before\n", encoding="utf-8")
    _git(workspace, "add", ".")
    _git(workspace, "commit", "-m", "init")
    (workspace / "tracked.txt").write_text("after\n", encoding="utf-8")

    run_dir = tmp_path / "runs" / "run_001"
    slot = run_dir / "aiwiki_consolidated" / "medium"
    slot.mkdir(parents=True)
    missing_final_message = tmp_path / "does-not-exist.md"

    original_argv = sys.argv
    sys.argv = [
        "save_result.py",
        "--run-dir",
        str(run_dir),
        "--variant",
        "aiwiki_consolidated",
        "--prompt-level",
        "medium",
        "--workspace",
        str(workspace),
        "--final-message",
        str(missing_final_message),
    ]
    try:
        module.main()
    finally:
        sys.argv = original_argv

    captured = capsys.readouterr()
    assert "Warning: final message file does not exist" in captured.err
    assert not (slot / "final_message.md").exists()
    assert (slot / "workspace_diff.patch").exists()
    result = json.loads((slot / "result.json").read_text(encoding="utf-8"))
    assert result["first_pass_success"] is None


def test_report_runs_builds_markdown_summary(tmp_path: Path) -> None:
    module = _load_script("report_runs.py")
    run_dir = tmp_path / "runs" / "run_001"
    run_dir.mkdir(parents=True)
    (run_dir / "metadata.json").write_text(
        json.dumps(
            {
                "experiment": "ownership_boundary",
                "workspace_root": "/tmp/workspaces",
                "variants": ["plain_repo_no_aiwiki", "aiwiki_consolidated"],
                "prompt_levels": ["medium"],
                "created_at": "2026-04-22T21:00:00",
                "notes": "test report",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    slot_a = run_dir / "plain_repo_no_aiwiki" / "medium"
    slot_a.mkdir(parents=True)
    (slot_a / "final_message.md").write_text("message a\n", encoding="utf-8")
    (slot_a / "result.json").write_text(
        json.dumps(
            {
                "variant": "plain_repo_no_aiwiki",
                "prompt_level": "medium",
                "attempt": 2,
                "human_nudges": 1,
                "first_pass_success": False,
                "changed_files": ["scripts/pr_flow.py", "tests/test_pr_flow_script.py"],
                "untracked_files": ["tests/test_pr_flow_script.py"],
                "notes": "needed hint",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    slot_b = run_dir / "aiwiki_consolidated" / "medium"
    slot_b.mkdir(parents=True)
    (slot_b / "final_message.md").write_text("message b\n", encoding="utf-8")
    (slot_b / "result.json").write_text(
        json.dumps(
            {
                "variant": "aiwiki_consolidated",
                "prompt_level": "medium",
                "attempt": 1,
                "human_nudges": 0,
                "first_pass_success": True,
                "changed_files": ["scripts/pr_flow.py", "ai-wiki/workflows.md"],
                "untracked_files": [],
                "notes": "clean pass",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    slot_c = run_dir / "aiwiki_raw_drafts" / "medium"
    slot_c.mkdir(parents=True)
    (slot_c / "result.json").write_text(
        json.dumps(
            {
                "variant": "aiwiki_raw_drafts",
                "prompt_level": "medium",
                "attempt": 1,
                "human_nudges": 0,
                "first_pass_success": None,
                "changed_files": ["scripts/pr_flow.py"],
                "untracked_files": [],
                "notes": "pending review",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    report_text = module.render_report(run_dir, json.loads((run_dir / "metadata.json").read_text()), module.collect_results(run_dir))
    assert "# Impact Eval Report" in report_text
    assert "plain_repo_no_aiwiki" in report_text
    assert "aiwiki_consolidated" in report_text
    assert "aiwiki_raw_drafts" in report_text
    assert "first_pass_successes" in report_text
    assert "first_pass_pending" in report_text
    assert "pending" in report_text
    assert "clean pass" in report_text
    assert "changed_file_count" in report_text
    assert "tests/test_pr_flow_script.py" in report_text
    assert "untracked_files" in report_text


def test_export_codex_sessions_exports_latest_visible_session_per_variant(tmp_path: Path) -> None:
    module = _load_script("export_codex_sessions.py")
    workspace_root = tmp_path / "workspaces" / "20260424-182219"
    plain_repo = workspace_root / "plain_repo_no_aiwiki"
    consolidated_repo = workspace_root / "aiwiki_consolidated"
    plain_repo.mkdir(parents=True)
    consolidated_repo.mkdir(parents=True)

    codex_root = tmp_path / ".codex"
    sessions_root = codex_root / "sessions" / "2026" / "04" / "24"
    sessions_root.mkdir(parents=True)
    session_index_path = codex_root / "session_index.jsonl"

    def write_session(
        session_id: str,
        *,
        cwd: Path,
        prompt: str,
        assistant: str,
        session_timestamp: str,
        updated_at: str,
        thread_name: str,
    ) -> None:
        session_file = sessions_root / f"rollout-{session_id}.jsonl"
        records = [
            {
                "type": "session_meta",
                "payload": {
                    "id": session_id,
                    "timestamp": session_timestamp,
                    "cwd": str(cwd),
                    "source": "vscode",
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": f"# AGENTS.md instructions for {cwd}",
                        }
                    ],
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": prompt}],
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": assistant}],
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "reasoning",
                    "encrypted_content": "hidden",
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "name": "exec_command",
                    "arguments": "{\"cmd\":\"pwd\"}",
                    "call_id": f"call-{session_id}",
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call_output",
                    "call_id": f"call-{session_id}",
                    "output": "pwd output",
                },
            },
        ]
        session_file.write_text(
            "\n".join(json.dumps(record) for record in records) + "\n",
            encoding="utf-8",
        )
        with session_index_path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "id": session_id,
                        "thread_name": thread_name,
                        "updated_at": updated_at,
                    }
                )
                + "\n"
            )

    write_session(
        "plain-old",
        cwd=plain_repo,
        prompt="older prompt",
        assistant="older assistant",
        session_timestamp="2026-04-24T08:00:00Z",
        updated_at="2026-04-24T08:05:00Z",
        thread_name="Older plain thread",
    )
    write_session(
        "plain-new",
        cwd=plain_repo,
        prompt="Expand public release and npm distribution support.",
        assistant="Reading files now.",
        session_timestamp="2026-04-24T09:00:00Z",
        updated_at="2026-04-24T09:10:00Z",
        thread_name="Latest plain thread",
    )
    write_session(
        "consolidated",
        cwd=consolidated_repo,
        prompt="Keep docs and tests up to date.",
        assistant="Checking docs and tests.",
        session_timestamp="2026-04-24T10:00:00Z",
        updated_at="2026-04-24T10:15:00Z",
        thread_name="Consolidated thread",
    )

    output_root = workspace_root / "codex_sessions"
    manifest = module.export_workspace_sessions(
        workspace_root=workspace_root,
        output_root=output_root,
        sessions_root=codex_root / "sessions",
        session_index_path=session_index_path,
        variants=("plain_repo_no_aiwiki", "aiwiki_consolidated"),
    )

    assert manifest["exported_session_count"] == 2
    assert manifest["missing_variants"] == []
    assert not (output_root / "plain_repo_no_aiwiki" / "plain-old").exists()

    latest_plain = output_root / "plain_repo_no_aiwiki" / "plain-new"
    assert latest_plain.exists()
    assert (latest_plain / "prompt.md").read_text(encoding="utf-8") == (
        "Expand public release and npm distribution support.\n"
    )
    plain_metadata = json.loads((latest_plain / "metadata.json").read_text(encoding="utf-8"))
    assert plain_metadata["thread_name"] == "Latest plain thread"
    assert plain_metadata["hidden_reasoning_exported"] is False

    visible_session = (latest_plain / "visible_session.jsonl").read_text(encoding="utf-8")
    assert '"type": "reasoning"' not in visible_session
    assert "encrypted_content" not in visible_session
    assert '"type": "function_call"' in visible_session
    assert '"type": "function_call_output"' in visible_session

    session_without_reasoning = (latest_plain / "session_without_reasoning.jsonl").read_text(
        encoding="utf-8"
    )
    assert '"type": "reasoning"' not in session_without_reasoning
    assert "encrypted_content" not in session_without_reasoning
    assert '"type": "session_meta"' in session_without_reasoning
    assert '"type": "function_call"' in session_without_reasoning
    assert '"type": "function_call_output"' in session_without_reasoning

    transcript = (latest_plain / "visible_transcript.md").read_text(encoding="utf-8")
    assert "## Task Prompt" in transcript
    assert "Expand public release and npm distribution support." in transcript
    assert "Reading files now." in transcript
    assert "visible_session.jsonl" in transcript

    consolidated = output_root / "aiwiki_consolidated" / "consolidated"
    assert consolidated.exists()
    assert "Keep docs and tests up to date." in (consolidated / "prompt.md").read_text(encoding="utf-8")


def test_export_codex_sessions_can_match_legacy_workspace_root(tmp_path: Path) -> None:
    module = _load_script("export_codex_sessions.py")
    workspace_root = tmp_path / "first_round" / "ownership_boundary" / "20260423-170541"
    legacy_root = tmp_path / "legacy" / "ownership_boundary" / "20260423-170541"
    target_repo = workspace_root / "plain_repo_no_aiwiki"
    legacy_repo = legacy_root / "plain_repo_no_aiwiki"
    target_repo.mkdir(parents=True)
    legacy_repo.mkdir(parents=True)

    codex_root = tmp_path / ".codex"
    sessions_root = codex_root / "sessions" / "2026" / "04" / "23"
    sessions_root.mkdir(parents=True)
    session_index_path = codex_root / "session_index.jsonl"

    session_file = sessions_root / "rollout-legacy.jsonl"
    session_file.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "type": "session_meta",
                        "payload": {
                            "id": "legacy-session",
                            "timestamp": "2026-04-23T07:00:00Z",
                            "cwd": str(legacy_repo),
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "response_item",
                        "payload": {
                            "type": "message",
                            "role": "user",
                            "content": [{"type": "input_text", "text": "medium prompt"}],
                        },
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    session_index_path.write_text(
        json.dumps(
            {
                "id": "legacy-session",
                "thread_name": "Legacy thread",
                "updated_at": "2026-04-23T07:05:00Z",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    output_root = workspace_root / "codex_sessions"
    manifest = module.export_workspace_sessions(
        workspace_root=workspace_root,
        match_workspace_root=legacy_root,
        output_root=output_root,
        sessions_root=codex_root / "sessions",
        session_index_path=session_index_path,
        variants=("plain_repo_no_aiwiki",),
    )

    assert manifest["exported_session_count"] == 1
    assert manifest["match_workspace_root"] == str(legacy_root.resolve())
    exported = output_root / "plain_repo_no_aiwiki" / "legacy-session"
    assert exported.exists()
