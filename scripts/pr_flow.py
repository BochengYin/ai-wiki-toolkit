"""Repo-local helper for creating and finishing GitHub pull requests with gh."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys


class PullRequestFlowError(RuntimeError):
    """Raised when the local PR flow cannot continue safely."""


@dataclass(frozen=True)
class PullRequestCreateResult:
    branch: str
    pull_request_url: str


@dataclass(frozen=True)
class PullRequestFinishResult:
    branch: str
    base_branch: str


def resolve_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    raise PullRequestFlowError("Could not find a git repository root from the current directory.")


def _run_command(
    repo_root: Path,
    command: list[str],
    *,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip() or "command failed"
        joined = " ".join(command)
        raise PullRequestFlowError(f"`{joined}` failed: {details}")
    return result


def require_clean_worktree(repo_root: Path) -> None:
    result = _run_command(repo_root, ["git", "status", "--short"], check=True)
    if result.stdout.strip():
        raise PullRequestFlowError(
            "Working tree is not clean. Commit or stash changes before running the PR flow."
        )


def require_gh_auth(repo_root: Path) -> None:
    _run_command(repo_root, ["gh", "auth", "status"], check=True)


def current_branch(repo_root: Path) -> str:
    result = _run_command(repo_root, ["git", "branch", "--show-current"], check=True)
    branch = result.stdout.strip()
    if not branch:
        raise PullRequestFlowError("Could not determine the current git branch.")
    return branch


def branch_has_upstream(repo_root: Path, branch: str) -> bool:
    result = _run_command(
        repo_root,
        ["git", "rev-parse", "--abbrev-ref", f"{branch}@{{upstream}}"],
        check=False,
    )
    return result.returncode == 0


def create_pull_request(
    repo_root: Path,
    *,
    base_branch: str = "main",
    draft: bool = False,
    title: str | None = None,
    body: str | None = None,
) -> PullRequestCreateResult:
    require_gh_auth(repo_root)
    require_clean_worktree(repo_root)

    branch = current_branch(repo_root)
    if branch == base_branch:
        raise PullRequestFlowError(
            f"Current branch is `{base_branch}`. Create or switch to a topic branch first."
        )

    if branch_has_upstream(repo_root, branch):
        _run_command(repo_root, ["git", "push"], check=True)
    else:
        _run_command(repo_root, ["git", "push", "-u", "origin", branch], check=True)

    command = ["gh", "pr", "create", "--base", base_branch, "--head", branch]
    if title and body:
        command.extend(["--title", title, "--body", body])
    elif title:
        command.extend(["--title", title, "--fill"])
    elif body:
        command.extend(["--body", body, "--fill"])
    else:
        command.append("--fill")
    if draft:
        command.append("--draft")

    result = _run_command(repo_root, command, check=True)
    pull_request_url = result.stdout.strip().splitlines()[-1].strip()
    if not pull_request_url:
        raise PullRequestFlowError("`gh pr create` succeeded but did not print a pull request URL.")
    return PullRequestCreateResult(branch=branch, pull_request_url=pull_request_url)


def finish_pull_request(
    repo_root: Path,
    *,
    base_branch: str = "main",
    auto: bool = False,
) -> PullRequestFinishResult:
    require_gh_auth(repo_root)
    require_clean_worktree(repo_root)

    branch = current_branch(repo_root)
    if branch == base_branch:
        raise PullRequestFlowError(
            f"Current branch is already `{base_branch}`. Switch to the PR branch you want to merge."
        )

    merge_command = ["gh", "pr", "merge", branch, "--rebase", "--delete-branch"]
    if auto:
        merge_command.append("--auto")
    _run_command(repo_root, merge_command, check=True)

    _run_command(repo_root, ["git", "fetch", "origin", "--prune"], check=True)
    _run_command(repo_root, ["git", "switch", base_branch], check=True)
    _run_command(repo_root, ["git", "pull", "--ff-only", "origin", base_branch], check=True)
    return PullRequestFinishResult(branch=branch, base_branch=base_branch)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser(
        "create",
        help="Push the current branch and open a GitHub pull request with gh.",
    )
    create_parser.add_argument("--base", default="main", help="Base branch for the pull request.")
    create_parser.add_argument("--draft", action="store_true", help="Create the PR as a draft.")
    create_parser.add_argument("--title", help="Optional PR title. Defaults to gh --fill behavior.")
    create_parser.add_argument("--body", help="Optional PR body. Defaults to gh --fill behavior.")

    finish_parser = subparsers.add_parser(
        "finish",
        help="Rebase-merge the current branch PR, delete the branch, and sync local main.",
    )
    finish_parser.add_argument("--base", default="main", help="Base branch to return to after merge.")
    finish_parser.add_argument(
        "--auto",
        action="store_true",
        help="Enable gh auto-merge if required checks are still running.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        repo_root = resolve_repo_root()
        if args.command == "create":
            result = create_pull_request(
                repo_root,
                base_branch=args.base,
                draft=args.draft,
                title=args.title,
                body=args.body,
            )
            print(f"Created pull request for `{result.branch}`.")
            print(result.pull_request_url)
            return 0

        result = finish_pull_request(
            repo_root,
            base_branch=args.base,
            auto=args.auto,
        )
        print(f"Merged `{result.branch}` and synced `{result.base_branch}`.")
        return 0
    except PullRequestFlowError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
