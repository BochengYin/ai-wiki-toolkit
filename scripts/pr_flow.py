"""Repo-local helper for creating PRs, finishing merges, and tagging releases."""

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
    merged: bool


@dataclass(frozen=True)
class ReleaseTagResult:
    tag: str
    base_branch: str
    commit: str
    pushed: bool


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


def normalize_release_tag(version_or_tag: str) -> str:
    value = version_or_tag.strip()
    if not value:
        raise PullRequestFlowError("Release version must not be empty.")
    return value if value.startswith("v") else f"v{value}"


def local_tag_exists(repo_root: Path, tag: str) -> bool:
    result = _run_command(
        repo_root,
        ["git", "rev-parse", "-q", "--verify", f"refs/tags/{tag}"],
        check=False,
    )
    return result.returncode == 0


def remote_tag_exists(repo_root: Path, tag: str) -> bool:
    result = _run_command(
        repo_root,
        ["git", "ls-remote", "--tags", "origin", f"refs/tags/{tag}"],
        check=True,
    )
    return bool(result.stdout.strip())


def branch_has_upstream(repo_root: Path, branch: str) -> bool:
    result = _run_command(
        repo_root,
        ["git", "rev-parse", "--abbrev-ref", f"{branch}@{{upstream}}"],
        check=False,
    )
    return result.returncode == 0


def pull_request_state(repo_root: Path, branch: str) -> str:
    result = _run_command(
        repo_root,
        ["gh", "pr", "view", branch, "--json", "state"],
        check=True,
    )
    for token in ('"state":"MERGED"', '"state":"OPEN"', '"state":"CLOSED"'):
        if token in result.stdout:
            return token.split('"')[3]
    raise PullRequestFlowError(f"Could not determine pull request state for `{branch}`.")


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

    state = pull_request_state(repo_root, branch)
    if state != "MERGED":
        merge_command = ["gh", "pr", "merge", branch, "--rebase", "--delete-branch"]
        if auto:
            merge_command.append("--auto")
        _run_command(repo_root, merge_command, check=True)
        state = pull_request_state(repo_root, branch)

    if state != "MERGED":
        return PullRequestFinishResult(branch=branch, base_branch=base_branch, merged=False)

    _run_command(repo_root, ["git", "fetch", "origin", "--prune"], check=True)
    _run_command(repo_root, ["git", "switch", base_branch], check=True)
    _run_command(repo_root, ["git", "pull", "--ff-only", "origin", base_branch], check=True)
    return PullRequestFinishResult(branch=branch, base_branch=base_branch, merged=True)


def tag_release(
    repo_root: Path,
    *,
    version_or_tag: str,
    base_branch: str = "main",
    push: bool = True,
) -> ReleaseTagResult:
    require_clean_worktree(repo_root)

    tag = normalize_release_tag(version_or_tag)

    _run_command(repo_root, ["git", "fetch", "origin", "--prune", "--tags"], check=True)
    _run_command(repo_root, ["git", "switch", base_branch], check=True)
    _run_command(repo_root, ["git", "pull", "--ff-only", "origin", base_branch], check=True)

    if remote_tag_exists(repo_root, tag):
        raise PullRequestFlowError(f"Release tag `{tag}` already exists on origin.")
    if local_tag_exists(repo_root, tag):
        raise PullRequestFlowError(f"Release tag `{tag}` already exists locally.")

    check_script = repo_root / "scripts" / "check_release_version.py"
    _run_command(repo_root, [sys.executable, str(check_script), tag], check=True)

    _run_command(repo_root, ["git", "tag", tag], check=True)
    if push:
        _run_command(repo_root, ["git", "push", "origin", tag], check=True)

    commit = _run_command(repo_root, ["git", "rev-parse", "HEAD"], check=True).stdout.strip()
    return ReleaseTagResult(
        tag=tag,
        base_branch=base_branch,
        commit=commit,
        pushed=push,
    )


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

    tag_parser = subparsers.add_parser(
        "tag-release",
        help="Sync the base branch, verify the version, and create a release tag.",
    )
    tag_parser.add_argument(
        "version",
        help="Semantic version or tag name, for example `0.1.12` or `v0.1.12`.",
    )
    tag_parser.add_argument("--base", default="main", help="Base branch to sync before tagging.")
    tag_parser.add_argument(
        "--local-only",
        action="store_true",
        help="Create the tag locally without pushing it to origin.",
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

        if args.command == "finish":
            result = finish_pull_request(
                repo_root,
                base_branch=args.base,
                auto=args.auto,
            )
            if result.merged:
                print(f"Merged `{result.branch}` and synced `{result.base_branch}`.")
            else:
                print(
                    f"Enabled auto-merge for `{result.branch}`. Wait for GitHub to merge it, "
                    f"then rerun `uv run python scripts/pr_flow.py finish` to sync `{result.base_branch}`."
                )
            return 0

        result = tag_release(
            repo_root,
            version_or_tag=args.version,
            base_branch=args.base,
            push=not args.local_only,
        )
        location = "and pushed it to origin" if result.pushed else "without pushing it"
        print(
            f"Created release tag `{result.tag}` at `{result.commit}` from `{result.base_branch}` "
            f"{location}."
        )
        return 0
    except PullRequestFlowError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
