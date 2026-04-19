from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest


def load_pr_flow_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "pr_flow.py"
    spec = importlib.util.spec_from_file_location("repo_pr_flow", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("repo_pr_flow", module)
    spec.loader.exec_module(module)
    return module


def test_create_pull_request_pushes_new_branch_and_opens_pr(
    repo_env: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load_pr_flow_module()
    seen_commands: list[list[str]] = []

    def fake_run(command: list[str], *, cwd: Path, capture_output: bool, text: bool, check: bool):
        assert capture_output is True
        assert text is True
        assert check is False
        seen_commands.append(command)
        responses = {
            ("gh", "auth", "status"): subprocess.CompletedProcess(command, 0, "", ""),
            ("git", "status", "--short"): subprocess.CompletedProcess(command, 0, "", ""),
            ("git", "branch", "--show-current"): subprocess.CompletedProcess(
                command, 0, "feature/example\n", ""
            ),
            ("git", "rev-parse", "--abbrev-ref", "feature/example@{upstream}"): subprocess.CompletedProcess(
                command, 1, "", ""
            ),
            ("git", "push", "-u", "origin", "feature/example"): subprocess.CompletedProcess(
                command, 0, "", ""
            ),
            ("gh", "pr", "create", "--base", "main", "--head", "feature/example", "--fill"): subprocess.CompletedProcess(
                command, 0, "https://github.com/example/repo/pull/7\n", ""
            ),
        }
        key = tuple(command)
        if key not in responses:
            raise AssertionError(f"Unexpected command: {command}")
        return responses[key]

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    result = module.create_pull_request(repo_env["repo"])

    assert result.branch == "feature/example"
    assert result.pull_request_url == "https://github.com/example/repo/pull/7"
    assert seen_commands == [
        ["gh", "auth", "status"],
        ["git", "status", "--short"],
        ["git", "branch", "--show-current"],
        ["git", "rev-parse", "--abbrev-ref", "feature/example@{upstream}"],
        ["git", "push", "-u", "origin", "feature/example"],
        ["gh", "pr", "create", "--base", "main", "--head", "feature/example", "--fill"],
    ]


def test_create_pull_request_uses_plain_push_when_branch_has_upstream(
    repo_env: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load_pr_flow_module()

    def fake_run(command: list[str], *, cwd: Path, capture_output: bool, text: bool, check: bool):
        responses = {
            ("gh", "auth", "status"): subprocess.CompletedProcess(command, 0, "", ""),
            ("git", "status", "--short"): subprocess.CompletedProcess(command, 0, "", ""),
            ("git", "branch", "--show-current"): subprocess.CompletedProcess(command, 0, "fix/docs\n", ""),
            ("git", "rev-parse", "--abbrev-ref", "fix/docs@{upstream}"): subprocess.CompletedProcess(
                command, 0, "origin/fix/docs\n", ""
            ),
            ("git", "push"): subprocess.CompletedProcess(command, 0, "", ""),
            ("gh", "pr", "create", "--base", "main", "--head", "fix/docs", "--fill", "--draft"): subprocess.CompletedProcess(
                command, 0, "https://github.com/example/repo/pull/9\n", ""
            ),
        }
        key = tuple(command)
        if key not in responses:
            raise AssertionError(f"Unexpected command: {command}")
        return responses[key]

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    result = module.create_pull_request(repo_env["repo"], draft=True)

    assert result.branch == "fix/docs"
    assert result.pull_request_url.endswith("/pull/9")


def test_finish_pull_request_rebases_deletes_branch_and_syncs_main(
    repo_env: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load_pr_flow_module()
    seen_commands: list[list[str]] = []

    def fake_run(command: list[str], *, cwd: Path, capture_output: bool, text: bool, check: bool):
        seen_commands.append(command)
        responses = {
            ("gh", "auth", "status"): subprocess.CompletedProcess(command, 0, "", ""),
            ("git", "status", "--short"): subprocess.CompletedProcess(command, 0, "", ""),
            ("git", "branch", "--show-current"): subprocess.CompletedProcess(
                command, 0, "feature/pr-flow\n", ""
            ),
            ("gh", "pr", "merge", "feature/pr-flow", "--rebase", "--delete-branch", "--auto"): subprocess.CompletedProcess(
                command, 0, "", ""
            ),
            ("git", "fetch", "origin", "--prune"): subprocess.CompletedProcess(command, 0, "", ""),
            ("git", "switch", "main"): subprocess.CompletedProcess(command, 0, "", ""),
            ("git", "pull", "--ff-only", "origin", "main"): subprocess.CompletedProcess(
                command, 0, "", ""
            ),
        }
        key = tuple(command)
        if key not in responses:
            raise AssertionError(f"Unexpected command: {command}")
        return responses[key]

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    result = module.finish_pull_request(repo_env["repo"], auto=True)

    assert result == module.PullRequestFinishResult(branch="feature/pr-flow", base_branch="main")
    assert seen_commands == [
        ["gh", "auth", "status"],
        ["git", "status", "--short"],
        ["git", "branch", "--show-current"],
        ["gh", "pr", "merge", "feature/pr-flow", "--rebase", "--delete-branch", "--auto"],
        ["git", "fetch", "origin", "--prune"],
        ["git", "switch", "main"],
        ["git", "pull", "--ff-only", "origin", "main"],
    ]


def test_require_clean_worktree_rejects_dirty_repo(
    repo_env: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load_pr_flow_module()

    def fake_run(command: list[str], *, cwd: Path, capture_output: bool, text: bool, check: bool):
        if command == ["git", "status", "--short"]:
            return subprocess.CompletedProcess(command, 0, " M README.md\n", "")
        raise AssertionError(f"Unexpected command: {command}")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    with pytest.raises(module.PullRequestFlowError, match="Working tree is not clean"):
        module.require_clean_worktree(repo_env["repo"])
