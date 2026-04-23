"""Capture manual impact-eval artifacts outside the experiment workspaces."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys


PROMPT_LEVELS = ("short", "medium", "full")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True, help="Run directory created by init_run.py.")
    parser.add_argument("--variant", required=True, help="Variant name such as aiwiki_consolidated.")
    parser.add_argument("--prompt-level", required=True, help="Prompt level such as medium.")
    parser.add_argument("--workspace", type=Path, required=True, help="Workspace path for this variant.")
    parser.add_argument(
        "--final-message",
        type=Path,
        help="Optional path to a saved final message markdown file to copy into the slot.",
    )
    parser.add_argument("--attempt", type=int, default=1, help="Attempt number for this saved result.")
    parser.add_argument("--human-nudges", type=int, default=0, help="How many human nudges were needed.")
    first_pass_group = parser.add_mutually_exclusive_group()
    first_pass_group.add_argument(
        "--first-pass-success",
        dest="first_pass_success",
        action="store_true",
        default=None,
        help="Mark the run as a first-pass success.",
    )
    first_pass_group.add_argument(
        "--first-pass-failure",
        dest="first_pass_success",
        action="store_false",
        help="Mark the run as not succeeding on the first attempt.",
    )
    parser.add_argument("--notes", default="", help="Optional free-form notes for this result.")
    return parser.parse_args()


def run_git(workspace: Path, *command: str) -> str:
    result = subprocess.run(
        ["git", *command],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def run_command(workspace: Path, *command: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=workspace,
        check=check,
        capture_output=True,
        text=True,
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def copy_final_message(source: Path, destination: Path) -> None:
    if not source.exists():
        print(f"Warning: final message file does not exist, skipping copy: {source}", file=sys.stderr)
        return
    if source.resolve() == destination.resolve():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def list_untracked_files(workspace: Path) -> list[str]:
    return [
        line.strip()
        for line in run_git(workspace, "ls-files", "--others", "--exclude-standard").splitlines()
        if line.strip()
    ]


def build_untracked_patch(workspace: Path, relative_path: str) -> str:
    result = run_command(
        workspace,
        "git",
        "diff",
        "--binary",
        "--no-index",
        "--",
        "/dev/null",
        relative_path,
        check=False,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"Failed to diff {relative_path}")
    return result.stdout


def build_untracked_stat(workspace: Path, relative_path: str) -> str:
    result = run_command(
        workspace,
        "git",
        "diff",
        "--stat",
        "--no-index",
        "--",
        "/dev/null",
        relative_path,
        check=False,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"Failed to stat {relative_path}")
    return result.stdout


def main() -> None:
    args = parse_args()
    if args.prompt_level not in PROMPT_LEVELS:
        raise SystemExit(f"Unsupported prompt level: {args.prompt_level}")
    if args.attempt < 1:
        raise SystemExit("--attempt must be >= 1")
    if args.human_nudges < 0:
        raise SystemExit("--human-nudges must be >= 0")
    if not args.run_dir.exists():
        raise SystemExit(f"Run directory does not exist: {args.run_dir}")
    if not args.workspace.exists():
        raise SystemExit(f"Workspace does not exist: {args.workspace}")

    slot = args.run_dir / args.variant / args.prompt_level
    slot.mkdir(parents=True, exist_ok=True)

    if args.final_message is not None:
        copy_final_message(args.final_message, slot / "final_message.md")

    untracked_files = list_untracked_files(args.workspace)
    tracked_patch = run_git(args.workspace, "diff", "--binary")
    tracked_stat = run_git(args.workspace, "diff", "--stat")
    untracked_patch = "".join(build_untracked_patch(args.workspace, path) for path in untracked_files)
    untracked_stat = "".join(build_untracked_stat(args.workspace, path) for path in untracked_files)

    write_text(slot / "workspace_status.txt", run_git(args.workspace, "status", "--short"))
    write_text(slot / "workspace_diff.patch", tracked_patch + untracked_patch)
    write_text(slot / "workspace_diff_stat.txt", tracked_stat + untracked_stat)
    write_text(slot / "workspace_head.txt", run_git(args.workspace, "rev-parse", "HEAD"))

    tracked_changed_files = [
        line.strip()
        for line in run_git(args.workspace, "diff", "--name-only").splitlines()
        if line.strip()
    ]
    changed_files = tracked_changed_files + [path for path in untracked_files if path not in tracked_changed_files]
    result = {
        "variant": args.variant,
        "prompt_level": args.prompt_level,
        "workspace": str(args.workspace.resolve()),
        "captured_at": datetime.now().isoformat(timespec="seconds"),
        "attempt": args.attempt,
        "human_nudges": args.human_nudges,
        "first_pass_success": args.first_pass_success,
        "changed_files": changed_files,
        "untracked_files": untracked_files,
        "notes": args.notes,
    }
    write_text(slot / "result.json", json.dumps(result, indent=2) + "\n")

    print(slot)


if __name__ == "__main__":
    main()
