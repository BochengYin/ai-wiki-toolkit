"""Initialize an external results directory for a CLI-first impact-eval run."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path

from prepare_variants import (
    available_experiments,
    EXPERIMENTS,
    RUNS_DIRNAME,
    resolve_repo_root,
    WORKDIR_ROOT,
    WORKSPACES_DIRNAME,
    timestamp_slug,
)


DEFAULT_MEMORY_AXIS_VARIANTS = (
    "plain_repo_no_aiwiki",
    "aiwiki_no_relevant_memory",
    "aiwiki_raw_drafts",
    "aiwiki_consolidated",
    "aiwiki_raw_plus_consolidated",
)
DEFAULT_WORKFLOW_PRIMARY_VARIANTS = (
    "no_aiwiki_workflow",
    "aiwiki_ambient_memory_workflow",
)
DEFAULT_WORKFLOW_DIAGNOSTIC_VARIANTS = (
    "aiwiki_scaffold_no_target_memory",
    "aiwiki_linked_raw_only",
    "aiwiki_linked_consolidated_only",
)
DEFAULT_PROMPT_AXIS_VARIANTS = (
    "plain_repo_no_aiwiki",
    "aiwiki_raw_drafts",
    "aiwiki_consolidated",
)
DEFAULT_PROMPT_LEVELS = ("original",)
DEFAULT_MODEL_FAMILY = "gpt-5.5"
DEFAULT_REASONING_EFFORT = "xhigh"
DEFAULT_EXECUTION_SURFACE = "codex-cli"
PROMPT_LEVELS = ("original", "short", "medium", "full")


def parse_csv(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(",") if part.strip())


def default_workspace_root(experiment: str) -> Path:
    return WORKDIR_ROOT / experiment / WORKSPACES_DIRNAME


def latest_subdirectory(root: Path) -> Path | None:
    if not root.exists():
        return None
    candidates = sorted(path for path in root.iterdir() if path.is_dir())
    if not candidates:
        return None
    return candidates[-1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--experiment",
        choices=sorted(EXPERIMENTS),
        default="ownership_boundary",
        help="Experiment family to initialize.",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=None,
        help="Path to the prepared workspace set. Defaults to the latest generated set for the experiment.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help="Root directory for result runs. Defaults to /private/tmp/aiwiki_first_round/<experiment>/runs/",
    )
    parser.add_argument(
        "--variants",
        type=parse_csv,
        default=None,
        help=(
            "Comma-separated variant or neutral slot list to include. Defaults to assignment.json "
            "slots when present, otherwise the five legacy memory-axis variants."
        ),
    )
    parser.add_argument(
        "--prompt-levels",
        type=parse_csv,
        default=DEFAULT_PROMPT_LEVELS,
        help=(
            "Comma-separated prompt levels. Defaults to original only for "
            "workflow-primary v2. short/medium/full remain for legacy round1 runs."
        ),
    )
    parser.add_argument(
        "--run-label",
        help="Optional human-readable run label. Defaults to a timestamp.",
    )
    parser.add_argument(
        "--notes",
        default="",
        help="Optional run-level notes to store in metadata.json.",
    )
    parser.add_argument(
        "--model-family",
        default=DEFAULT_MODEL_FAMILY,
        help="Expected model family for the run.",
    )
    parser.add_argument(
        "--reasoning-effort",
        default=DEFAULT_REASONING_EFFORT,
        help="Expected reasoning effort for the run.",
    )
    parser.add_argument(
        "--execution-surface",
        default=DEFAULT_EXECUTION_SURFACE,
        help="Execution surface for the run.",
    )
    return parser.parse_args()


def validate_levels(levels: tuple[str, ...]) -> tuple[str, ...]:
    invalid = [level for level in levels if level not in PROMPT_LEVELS]
    if invalid:
        raise SystemExit(f"Unsupported prompt levels: {', '.join(invalid)}")
    return levels


def resolve_workspace_root(experiment: str, requested: Path | None) -> Path:
    if requested is not None:
        if not requested.exists():
            raise SystemExit(f"Workspace root does not exist: {requested}")
        return requested.resolve()
    latest = latest_subdirectory(default_workspace_root(experiment))
    if latest is None:
        raise SystemExit(
            "Could not find a prepared workspace set. Run prepare_variants.py first or pass --workspace-root."
        )
    return latest.resolve()


def default_output_root(experiment: str) -> Path:
    return WORKDIR_ROOT / experiment / RUNS_DIRNAME


def normalize_run_label(label: str | None) -> str:
    if label:
        return label.strip().replace(" ", "-")
    return f"run_{timestamp_slug()}"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def prompt_hashes_for_run(experiment: str, prompt_levels: tuple[str, ...]) -> dict[str, str]:
    repo_root = resolve_repo_root(Path(__file__).resolve())
    spec = available_experiments(repo_root).get(experiment, EXPERIMENTS.get(experiment))
    if spec is None:
        return {}
    prompt_root = repo_root / "evals" / "impact" / "prompts" / spec.prompt_family
    hashes: dict[str, str] = {}
    for level in prompt_levels:
        prompt_path = prompt_root / f"{level}.md"
        if prompt_path.exists():
            hashes[level] = sha256_text(prompt_path.read_text(encoding="utf-8"))
    return hashes


def load_assignment(workspace_root: Path) -> dict | None:
    assignment_path = workspace_root / "assignment.json"
    if not assignment_path.exists():
        return None
    return json.loads(assignment_path.read_text(encoding="utf-8"))


def assignment_slots(assignment: dict | None) -> tuple[str, ...]:
    if assignment is None:
        return ()
    return tuple(slot["slot"] for slot in assignment.get("slots", []))


def assignment_variant_for_slot(assignment: dict | None, slot: str) -> str:
    if assignment is None:
        return slot
    for item in assignment.get("slots", []):
        if item.get("slot") == slot:
            return item.get("variant", slot)
    return slot


def workspace_for_slot(workspace_root: Path, assignment: dict | None, slot: str) -> Path:
    if assignment is None:
        return workspace_root / slot
    for item in assignment.get("slots", []):
        if item.get("slot") == slot and item.get("workspace"):
            return Path(item["workspace"])
    return workspace_root / "slots" / slot


def prompt_path_for_slot(experiment: str, prompt_level: str) -> Path:
    repo_root = resolve_repo_root(Path(__file__).resolve())
    spec = available_experiments(repo_root).get(experiment, EXPERIMENTS.get(experiment))
    prompt_family = spec.prompt_family if spec is not None else experiment
    return repo_root / "evals" / "impact" / "prompts" / prompt_family / f"{prompt_level}.md"


def render_cli_command(
    *,
    run_dir: Path,
    experiment: str,
    variant: str,
    slot: str,
    prompt_level: str,
    variant_root: Path,
    model_family: str,
    reasoning_effort: str,
) -> str:
    result_slot = run_dir / slot / prompt_level
    final_message = result_slot / "first_pass" / "final_message.md"
    prompt_path = prompt_path_for_slot(experiment, prompt_level)
    return (
        "```bash\n"
        "mkdir -p "
        f"\"{final_message.parent}\"\n"
        "codex exec \\\n"
        f"  --model \"{model_family}\" \\\n"
        f"  --config 'model_reasoning_effort=\"{reasoning_effort}\"' \\\n"
        "  --full-auto \\\n"
        f"  --cd \"{variant_root}\" \\\n"
        f"  --output-last-message \"{final_message}\" \\\n"
        f"  - < \"{prompt_path}\"\n"
        "uv run python evals/impact/scripts/save_result.py \\\n"
        f"  --run-dir \"{run_dir}\" \\\n"
        f"  --variant \"{variant}\" \\\n"
        f"  --slot \"{slot}\" \\\n"
        f"  --prompt-level \"{prompt_level}\" \\\n"
        f"  --workspace \"{variant_root}\" \\\n"
        f"  --final-message \"{final_message}\" \\\n"
        "  --phase first_pass\n"
        "```\n"
    )


def render_runner_command(run_dir: Path, prompt_level: str) -> str:
    return (
        "```bash\n"
        "uv run python evals/impact/scripts/run_cli_slots.py \\\n"
        f"  --run-dir \"{run_dir}\" \\\n"
        f"  --prompt-level \"{prompt_level}\"\n"
        "```\n"
    )


def create_result_slots(
    run_dir: Path,
    *,
    experiment: str,
    workspace_root: Path,
    variants: tuple[str, ...],
    prompt_levels: tuple[str, ...],
    assignment: dict | None = None,
    model_family: str = DEFAULT_MODEL_FAMILY,
    reasoning_effort: str = DEFAULT_REASONING_EFFORT,
) -> None:
    for slot in variants:
        variant = assignment_variant_for_slot(assignment, slot)
        variant_root = workspace_for_slot(workspace_root, assignment, slot)
        if not variant_root.exists():
            raise SystemExit(f"Workspace variant does not exist: {variant_root}")
        for prompt_level in prompt_levels:
            result_slot = run_dir / slot / prompt_level
            result_slot.mkdir(parents=True, exist_ok=True)
            instructions = (
                f"# Result Slot\n\n"
                f"- Experiment: `{experiment}`\n"
                f"- Slot: `{slot}`\n"
                f"- Variant: `{variant}`\n"
                f"- Prompt: `{prompt_level}`\n"
                f"- Workspace: `{variant_root}`\n\n"
                f"Preferred formal path: run the whole slot set once with the run-level sleep guard "
                f"from the run directory README. For this prompt level, the command is:\n\n"
                f"{render_runner_command(run_dir, prompt_level)}"
                f"Run the prompt with Codex CLI first, then capture the first-pass result:\n\n"
                f"{render_cli_command(run_dir=run_dir, experiment=experiment, variant=variant, slot=slot, prompt_level=prompt_level, variant_root=variant_root, model_family=model_family, reasoning_effort=reasoning_effort)}"
                f"\nThe standard run expects the exported session metadata to show "
                f"`source=exec`, `model={model_family}`, and `reasoning_effort={reasoning_effort}`.\n\n"
                f"Add `--first-pass-success` or `--first-pass-failure` only if you want to judge "
                f"correctness now. If you omit both, the result stays pending for later analysis.\n\n"
                f"If there is a later human nudge or repair, capture it separately with `--phase final`.\n"
                f"After all slots finish, export Codex sessions and run `validate_run.py`; the run is "
                f"not shareable for causal claims without a complete `codex_sessions/manifest.json`.\n"
            )
            write_text(result_slot / "README.md", instructions)


def write_run_readme(
    run_dir: Path,
    *,
    experiment: str,
    workspace_root: Path,
    prompt_levels: tuple[str, ...],
) -> None:
    prompt_level = prompt_levels[0] if prompt_levels else DEFAULT_PROMPT_LEVELS[0]
    readme = (
        "# Impact Eval Run\n\n"
        f"- Experiment: `{experiment}`\n"
        f"- Workspace root: `{workspace_root}`\n"
        f"- Prompt level: `{prompt_level}`\n\n"
        "Formal CLI-first runs should use one run-level sleep guard for the whole slot set. "
        "`run_cli_slots.py` starts `caffeinate -dimsu`, runs each neutral slot in sequence, "
        "captures first-pass artifacts immediately after each `codex exec`, and stops the "
        "sleep guard at the end.\n\n"
        f"{render_runner_command(run_dir, prompt_level)}"
        "After all slots finish, export sessions and validate the run:\n\n"
        "```bash\n"
        f"uv run python evals/impact/scripts/export_codex_sessions.py --workspace-root \"{workspace_root}\"\n"
        f"uv run python evals/impact/scripts/validate_run.py --run-dir \"{run_dir}\"\n"
        "```\n"
    )
    write_text(run_dir / "README.md", readme)


def write_metadata(
    run_dir: Path,
    *,
    experiment: str,
    workspace_root: Path,
    variants: tuple[str, ...],
    prompt_levels: tuple[str, ...],
    notes: str,
    assignment: dict | None = None,
    model_family: str = DEFAULT_MODEL_FAMILY,
    reasoning_effort: str = DEFAULT_REASONING_EFFORT,
    execution_surface: str = DEFAULT_EXECUTION_SURFACE,
) -> None:
    metadata = {
        "schema_version": 2,
        "experiment": experiment,
        "workspace_root": str(workspace_root),
        "variants": list(variants),
        "prompt_levels": list(prompt_levels),
        "prompt_hashes": prompt_hashes_for_run(experiment, prompt_levels),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "notes": notes,
        "assignment": assignment,
        "primary_comparison": (
            assignment.get("primary_comparison", [])
            if isinstance(assignment, dict)
            else []
        ),
        "diagnostic_variants": (
            assignment.get("diagnostic_variants", [])
            if isinstance(assignment, dict)
            else []
        ),
        "model_family": model_family,
        "reasoning_effort": reasoning_effort,
        "execution_surface": execution_surface,
    }
    write_text(run_dir / "metadata.json", json.dumps(metadata, indent=2) + "\n")


def main() -> None:
    args = parse_args()
    prompt_levels = validate_levels(args.prompt_levels)
    workspace_root = resolve_workspace_root(args.experiment, args.workspace_root)
    assignment = load_assignment(workspace_root)
    variants = args.variants
    if variants is None:
        variants = assignment_slots(assignment) or DEFAULT_MEMORY_AXIS_VARIANTS
    output_root = (args.output_root or default_output_root(args.experiment)).resolve()
    run_dir = output_root / normalize_run_label(args.run_label)
    if run_dir.exists():
        raise SystemExit(f"Run directory already exists: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=False)

    create_result_slots(
        run_dir,
        experiment=args.experiment,
        workspace_root=workspace_root,
        variants=variants,
        prompt_levels=prompt_levels,
        assignment=assignment,
        model_family=args.model_family,
        reasoning_effort=args.reasoning_effort,
    )
    write_run_readme(
        run_dir,
        experiment=args.experiment,
        workspace_root=workspace_root,
        prompt_levels=prompt_levels,
    )
    write_metadata(
        run_dir,
        experiment=args.experiment,
        workspace_root=workspace_root,
        variants=variants,
        prompt_levels=prompt_levels,
        notes=args.notes,
        assignment=assignment,
        model_family=args.model_family,
        reasoning_effort=args.reasoning_effort,
        execution_surface=args.execution_surface,
    )

    print(run_dir)


if __name__ == "__main__":
    main()
