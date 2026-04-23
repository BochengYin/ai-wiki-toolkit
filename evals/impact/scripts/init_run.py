"""Initialize an external results directory for a manual impact-eval run."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path

from prepare_variants import EXPERIMENTS, WORKDIR_ROOT, timestamp_slug


RUNS_ROOT = Path.home() / "aiwiki-impact-runs"
DEFAULT_MEMORY_AXIS_VARIANTS = (
    "plain_repo_no_aiwiki",
    "aiwiki_no_relevant_memory",
    "aiwiki_raw_drafts",
    "aiwiki_consolidated",
    "aiwiki_raw_plus_consolidated",
)
DEFAULT_PROMPT_AXIS_VARIANTS = (
    "plain_repo_no_aiwiki",
    "aiwiki_raw_drafts",
    "aiwiki_consolidated",
)
PROMPT_LEVELS = ("short", "medium", "full")


def parse_csv(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(",") if part.strip())


def default_workspace_root(experiment: str) -> Path:
    return WORKDIR_ROOT / "ai-wiki-toolkit" / experiment


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
        help="Root directory for result runs. Defaults to ~/aiwiki-impact-runs/<repo>/<experiment>/",
    )
    parser.add_argument(
        "--variants",
        type=parse_csv,
        default=DEFAULT_MEMORY_AXIS_VARIANTS,
        help="Comma-separated variant list to include. Defaults to the five memory-axis variants.",
    )
    parser.add_argument(
        "--prompt-levels",
        type=parse_csv,
        default=("medium",),
        help="Comma-separated prompt levels. Defaults to medium only.",
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
    return RUNS_ROOT / "ai-wiki-toolkit" / experiment


def normalize_run_label(label: str | None) -> str:
    if label:
        return label.strip().replace(" ", "-")
    return f"run_{timestamp_slug()}"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def create_result_slots(
    run_dir: Path,
    *,
    experiment: str,
    workspace_root: Path,
    variants: tuple[str, ...],
    prompt_levels: tuple[str, ...],
) -> None:
    for variant in variants:
        variant_root = workspace_root / variant
        if not variant_root.exists():
            raise SystemExit(f"Workspace variant does not exist: {variant_root}")
        for prompt_level in prompt_levels:
            slot = run_dir / variant / prompt_level
            slot.mkdir(parents=True, exist_ok=True)
            instructions = (
                f"# Result Slot\n\n"
                f"- Experiment: `{experiment}`\n"
                f"- Variant: `{variant}`\n"
                f"- Prompt level: `{prompt_level}`\n"
                f"- Workspace: `{variant_root}`\n\n"
                f"If you want to preserve the agent's final response, save it as `final_message.md` in this "
                f"folder before capture. This is optional.\n\n"
                f"After the run, capture the workspace result with:\n\n"
                f"```bash\n"
                f"uv run python evals/impact/scripts/save_result.py \\\n"
                f"  --run-dir \"{run_dir}\" \\\n"
                f"  --variant \"{variant}\" \\\n"
                f"  --prompt-level \"{prompt_level}\" \\\n"
                f"  --workspace \"{variant_root}\"\n"
                f"```\n"
                f"\nAdd `--first-pass-success` or `--first-pass-failure` only if you want to judge "
                f"correctness now. If you omit both, the result stays pending for later analysis.\n"
            )
            write_text(slot / "README.md", instructions)


def write_metadata(
    run_dir: Path,
    *,
    experiment: str,
    workspace_root: Path,
    variants: tuple[str, ...],
    prompt_levels: tuple[str, ...],
    notes: str,
) -> None:
    metadata = {
        "experiment": experiment,
        "workspace_root": str(workspace_root),
        "variants": list(variants),
        "prompt_levels": list(prompt_levels),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "notes": notes,
    }
    write_text(run_dir / "metadata.json", json.dumps(metadata, indent=2) + "\n")


def main() -> None:
    args = parse_args()
    prompt_levels = validate_levels(args.prompt_levels)
    workspace_root = resolve_workspace_root(args.experiment, args.workspace_root)
    output_root = (args.output_root or default_output_root(args.experiment)).resolve()
    run_dir = output_root / normalize_run_label(args.run_label)
    if run_dir.exists():
        raise SystemExit(f"Run directory already exists: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=False)

    create_result_slots(
        run_dir,
        experiment=args.experiment,
        workspace_root=workspace_root,
        variants=args.variants,
        prompt_levels=prompt_levels,
    )
    write_metadata(
        run_dir,
        experiment=args.experiment,
        workspace_root=workspace_root,
        variants=args.variants,
        prompt_levels=prompt_levels,
        notes=args.notes,
    )

    print(run_dir)


if __name__ == "__main__":
    main()
