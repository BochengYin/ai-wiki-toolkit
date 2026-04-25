"""Run Manual v2 Codex CLI slots under one run-level sleep guard."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys
from collections.abc import Sequence

from init_run import (
    assignment_variant_for_slot,
    prompt_path_for_slot,
    workspace_for_slot,
)


DEFAULT_PROMPT_LEVEL = "original"
SLEEP_GUARD_ARGS = ("-dimsu",)


@dataclass(frozen=True)
class SlotCommandResult:
    slot: str
    variant: str
    prompt_level: str
    workspace: str
    final_message: str
    codex_returncode: int
    save_result_returncode: int
    started_at: str
    finished_at: str


def parse_csv(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(",") if part.strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True, help="Run directory from init_run.py.")
    parser.add_argument(
        "--prompt-level",
        default=None,
        help="Prompt level to run. Defaults to metadata prompt level or original.",
    )
    parser.add_argument(
        "--slots",
        type=parse_csv,
        default=None,
        help="Optional comma-separated neutral slots. Defaults to metadata variants.",
    )
    parser.add_argument(
        "--codex-bin",
        default="codex",
        help="Codex CLI executable. Defaults to codex.",
    )
    parser.add_argument(
        "--no-sleep-guard",
        action="store_true",
        help="Disable the run-level caffeinate guard. Intended only for tests or non-mac hosts.",
    )
    return parser.parse_args()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def sleep_guard_command(caffeinate_bin: str) -> list[str]:
    return [caffeinate_bin, *SLEEP_GUARD_ARGS]


def start_sleep_guard(*, enabled: bool, run_dir: Path) -> subprocess.Popen[str] | None:
    if not enabled:
        write_json(
            run_dir / "sleep_guard.json",
            {
                "schema_version": 1,
                "enabled": False,
                "started_at": None,
                "stopped_at": None,
                "command": None,
                "pid": None,
            },
        )
        return None

    caffeinate_bin = shutil.which("caffeinate")
    if caffeinate_bin is None:
        raise SystemExit(
            "caffeinate was not found. Install/use macOS caffeinate, or pass --no-sleep-guard "
            "for a non-formal run."
        )

    command = sleep_guard_command(caffeinate_bin)
    process = subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    write_json(
        run_dir / "sleep_guard.json",
        {
            "schema_version": 1,
            "enabled": True,
            "started_at": timestamp(),
            "stopped_at": None,
            "command": command,
            "pid": process.pid,
            "returncode": None,
        },
    )
    return process


def stop_sleep_guard(process: subprocess.Popen[str] | None, *, run_dir: Path) -> None:
    guard_path = run_dir / "sleep_guard.json"
    guard = read_json(guard_path) if guard_path.exists() else {"schema_version": 1}
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
    guard["stopped_at"] = timestamp()
    if process is not None:
        guard["returncode"] = process.returncode
    write_json(guard_path, guard)


def metadata_slots(metadata: dict) -> tuple[str, ...]:
    variants = metadata.get("variants", [])
    return tuple(str(variant) for variant in variants)


def metadata_prompt_level(metadata: dict) -> str:
    prompt_levels = metadata.get("prompt_levels", [])
    if prompt_levels:
        return str(prompt_levels[0])
    return DEFAULT_PROMPT_LEVEL


def build_codex_command(
    *,
    codex_bin: str,
    model_family: str,
    reasoning_effort: str,
    workspace: Path,
    final_message: Path,
) -> list[str]:
    return [
        codex_bin,
        "exec",
        "--model",
        model_family,
        "--config",
        f'model_reasoning_effort="{reasoning_effort}"',
        "--full-auto",
        "--cd",
        str(workspace),
        "--output-last-message",
        str(final_message),
        "-",
    ]


def build_save_result_command(
    *,
    run_dir: Path,
    variant: str,
    slot: str,
    prompt_level: str,
    workspace: Path,
    final_message: Path,
    notes: str,
) -> list[str]:
    save_result = Path(__file__).resolve().parent / "save_result.py"
    command = [
        sys.executable,
        str(save_result),
        "--run-dir",
        str(run_dir),
        "--variant",
        variant,
        "--slot",
        slot,
        "--prompt-level",
        prompt_level,
        "--workspace",
        str(workspace),
        "--final-message",
        str(final_message),
        "--phase",
        "first_pass",
    ]
    if notes:
        command.extend(["--notes", notes])
    return command


def run_slot(
    *,
    metadata: dict,
    run_dir: Path,
    slot: str,
    prompt_level: str,
    codex_bin: str,
) -> SlotCommandResult:
    assignment = metadata.get("assignment")
    workspace_root = Path(str(metadata["workspace_root"]))
    experiment = str(metadata["experiment"])
    model_family = str(metadata.get("model_family", "gpt-5.5"))
    reasoning_effort = str(metadata.get("reasoning_effort", "xhigh"))
    variant = assignment_variant_for_slot(assignment, slot)
    workspace = workspace_for_slot(workspace_root, assignment, slot)
    final_message = run_dir / slot / prompt_level / "first_pass" / "final_message.md"
    final_message.parent.mkdir(parents=True, exist_ok=True)
    prompt_path = prompt_path_for_slot(experiment, prompt_level)
    prompt_text = prompt_path.read_text(encoding="utf-8")

    started_at = timestamp()
    codex_command = build_codex_command(
        codex_bin=codex_bin,
        model_family=model_family,
        reasoning_effort=reasoning_effort,
        workspace=workspace,
        final_message=final_message,
    )
    codex_result = subprocess.run(codex_command, input=prompt_text, text=True, check=False)
    notes = (
        f"Captured by run_cli_slots.py; Codex CLI return code: {codex_result.returncode}. "
        "Run-level sleep guard metadata is in sleep_guard.json."
    )
    save_result = subprocess.run(
        build_save_result_command(
            run_dir=run_dir,
            variant=variant,
            slot=slot,
            prompt_level=prompt_level,
            workspace=workspace,
            final_message=final_message,
            notes=notes,
        ),
        check=False,
    )
    finished_at = timestamp()
    result = SlotCommandResult(
        slot=slot,
        variant=variant,
        prompt_level=prompt_level,
        workspace=str(workspace),
        final_message=str(final_message),
        codex_returncode=codex_result.returncode,
        save_result_returncode=save_result.returncode,
        started_at=started_at,
        finished_at=finished_at,
    )
    write_json(final_message.parent / "command_result.json", asdict(result))
    return result


def run_slots(
    *,
    run_dir: Path,
    slots: Sequence[str],
    prompt_level: str,
    codex_bin: str,
    sleep_guard: bool,
) -> list[SlotCommandResult]:
    metadata = read_json(run_dir / "metadata.json")
    guard = start_sleep_guard(enabled=sleep_guard, run_dir=run_dir)
    results: list[SlotCommandResult] = []
    try:
        for slot in slots:
            results.append(
                run_slot(
                    metadata=metadata,
                    run_dir=run_dir,
                    slot=slot,
                    prompt_level=prompt_level,
                    codex_bin=codex_bin,
                )
            )
    finally:
        stop_sleep_guard(guard, run_dir=run_dir)
    return results


def main() -> None:
    args = parse_args()
    run_dir = args.run_dir.resolve()
    metadata = read_json(run_dir / "metadata.json")
    slots = args.slots or metadata_slots(metadata)
    if not slots:
        raise SystemExit("No slots to run. Pass --slots or check metadata.json variants.")
    prompt_level = args.prompt_level or metadata_prompt_level(metadata)
    results = run_slots(
        run_dir=run_dir,
        slots=slots,
        prompt_level=prompt_level,
        codex_bin=args.codex_bin,
        sleep_guard=not args.no_sleep_guard,
    )
    failures = [
        result
        for result in results
        if result.codex_returncode != 0 or result.save_result_returncode != 0
    ]
    write_json(
        run_dir / "slot_command_results.json",
        {"results": [asdict(item) for item in results]},
    )
    if failures:
        raise SystemExit(
            "One or more slots had non-zero command exits: "
            + ", ".join(
                f"{item.slot}=codex:{item.codex_returncode}/save:{item.save_result_returncode}"
                for item in failures
            )
        )


if __name__ == "__main__":
    main()
