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
