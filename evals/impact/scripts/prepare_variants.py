"""Prepare clean manual-run workspaces for AI wiki impact experiments."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import json
import io
from pathlib import Path
import shutil
import subprocess
import tarfile
import tomllib


START_MARKER = "<!-- aiwiki-toolkit:start -->"
END_MARKER = "<!-- aiwiki-toolkit:end -->"
DEFAULT_HANDLE = "eval-user"
DEFAULT_EMAIL = "eval-user@example.com"
ROUND_ROOT = Path("/private/tmp") / "aiwiki_first_round"
WORKSPACES_DIRNAME = "workspaces"
RUNS_DIRNAME = "runs"
WORKDIR_ROOT = ROUND_ROOT
SOURCE_MODE_COMMITTED_HEAD = "committed-head"
SOURCE_MODE_WORKING_TREE = "working-tree"
WORKSPACE_LAYOUT_LEGACY = "legacy"
WORKSPACE_LAYOUT_NEUTRAL = "neutral"
SLOTS_DIRNAME = "slots"
EXCLUDED_ROOT_NAMES = {
    ".git",
    ".venv",
    ".pytest_cache",
    "__pycache__",
    "build",
    "dist",
}
EXCLUDED_RELATIVE_PREFIXES = (
    "evals/impact/",
    "ai-wiki/metrics/reuse-events/",
    "ai-wiki/metrics/task-checks/",
    "ai-wiki/_toolkit/metrics/",
)
EXCLUDED_RELATIVE_PATHS = (
    "tests/test_impact_eval_setup.py",
    "tests/test_impact_eval_run_capture.py",
    "ai-wiki/people/bochengyin/drafts/impact-eval-prompts-should-backsolve-from-concrete-history.md",
)
AI_WIKI_SKILL_PREFIX = "ai-wiki-"
WORKFLOW_PRIMARY_VARIANTS = (
    "no_aiwiki_workflow",
    "aiwiki_ambient_memory_workflow",
)
WORKFLOW_DIAGNOSTIC_VARIANTS = (
    "aiwiki_scaffold_no_target_memory",
    "aiwiki_linked_raw_only",
    "aiwiki_linked_consolidated_only",
    "aiwiki_scaffold_no_adjacent_memory",
)
WORKFLOW_VARIANTS = (
    "no_aiwiki_workflow",
    "aiwiki_scaffold_no_target_memory",
    "aiwiki_linked_raw_only",
    "aiwiki_linked_consolidated_only",
    "aiwiki_ambient_memory_workflow",
    "aiwiki_scaffold_no_adjacent_memory",
)
LEGACY_VARIANTS = (
    "plain_repo_no_aiwiki",
    "aiwiki_no_relevant_memory",
    "aiwiki_raw_drafts",
    "aiwiki_consolidated",
    "aiwiki_raw_plus_consolidated",
)


@dataclass(frozen=True)
class ExperimentSpec:
    name: str
    prompt_family: str
    raw_docs: tuple[str, ...]
    raw_overlays: tuple[tuple[str, str], ...]
    consolidated_docs: tuple[str, ...]
    consolidated_overlays: tuple[tuple[str, str], ...]
    consolidated_index_entries: tuple[tuple[str, str], ...]
    baseline_ref: str = "HEAD"
    historical_issue: str = ""
    ambient_exclude_paths: tuple[str, ...] = ()
    strict_scaffold_exclude_paths: tuple[str, ...] = ()
    strict_scaffold_index_tokens: tuple[tuple[str, str], ...] = ()


OWNERSHIP_BOUNDARY = ExperimentSpec(
    name="ownership_boundary",
    prompt_family="ownership_boundary",
    baseline_ref="34cd5a3^",
    raw_docs=(
        "ai-wiki/people/bochengyin/drafts/user-owned-ai-wiki-index-should-not-be-an-upgrade-surface.md",
        "ai-wiki/people/bochengyin/drafts/repo-local-contributor-workflows-should-stay-out-of-the-package-layer.md",
        "ai-wiki/people/bochengyin/drafts/managed-toolkit-workflows-need-a-toc-and-scope-aware-conflict-checks.md",
    ),
    raw_overlays=(),
    consolidated_docs=(
        "ai-wiki/conventions/package-managed-vs-user-owned-docs.md",
        "ai-wiki/review-patterns/shared-prompt-files-must-be-user-agnostic.md",
    ),
    consolidated_overlays=(),
    consolidated_index_entries=(
        (
            "ai-wiki/conventions/index.md",
            "- [Package-managed vs user-owned AI wiki docs](package-managed-vs-user-owned-docs.md): keep evolving package-controlled guidance in `_toolkit/**` and keep repo-owned AI wiki docs stable unless a contributor intentionally edits them.",
        ),
        (
            "ai-wiki/review-patterns/index.md",
            "- [Shared prompt files must be user-agnostic](shared-prompt-files-must-be-user-agnostic.md): keep repo-shared prompt content stable across different local handles.",
        ),
    ),
    strict_scaffold_exclude_paths=(
        "ai-wiki/workflows.md",
        "ai-wiki/people/bochengyin/drafts/impact-eval-no-target-aiwiki-slots-must-exclude-task-specific-workflow-memory.md",
        "ai-wiki/people/bochengyin/drafts/adjacent-consolidated-guidance-can-underperform-task-specific-raw-drafts-in-impact-evals.md",
        "ai-wiki/people/bochengyin/drafts/workflow-primary-impact-evals-compare-working-modes.md",
    ),
)

RELEASE_DISTRIBUTION_INTEGRITY = ExperimentSpec(
    name="release_distribution_integrity",
    prompt_family="release_distribution_integrity",
    baseline_ref="06a47cd^",
    raw_docs=(
        "ai-wiki/people/bochengyin/drafts/distribution-target-matrix-must-match-published-assets.md",
    ),
    raw_overlays=(),
    consolidated_docs=(
        "ai-wiki/conventions/distribution-target-matrix-must-match-published-assets.md",
    ),
    consolidated_overlays=(),
    consolidated_index_entries=(
        (
            "ai-wiki/conventions/index.md",
            "- [Distribution target matrix must match published assets](distribution-target-matrix-must-match-published-assets.md): keep every public release target aligned across release workflows, published assets, runtime target maps, package metadata, archive handling, docs, and smoke checks.",
        ),
    ),
    strict_scaffold_exclude_paths=(
        "ai-wiki/problems/linux-musl-pyinstaller-needs-binutils-objdump.md",
        "ai-wiki/problems/windows-arm-smoke-version-checks-need-full-cli-output.md",
        "ai-wiki/people/bochengyin/drafts/introducing-new-npm-package-names-needs-a-bootstrap-publish-plan.md",
        "ai-wiki/people/bochengyin/drafts/linux-release-binaries-need-runtime-checks-against-an-older-glibc-baseline.md",
        "ai-wiki/trails/2026-04-18-release-workflow-and-prompt-block-edge-cases.md",
    ),
    strict_scaffold_index_tokens=(
        (
            "ai-wiki/problems/index.md",
            "linux-musl-pyinstaller-needs-binutils-objdump.md",
        ),
        (
            "ai-wiki/problems/index.md",
            "windows-arm-smoke-version-checks-need-full-cli-output.md",
        ),
        (
            "ai-wiki/trails/index.md",
            "2026-04-18-release-workflow-and-prompt-block-edge-cases.md",
        ),
    ),
)

EXPERIMENTS = {
    OWNERSHIP_BOUNDARY.name: OWNERSHIP_BOUNDARY,
    RELEASE_DISTRIBUTION_INTEGRITY.name: RELEASE_DISTRIBUTION_INTEGRITY,
}


def default_families_root(control_root: Path | None = None) -> Path:
    root = control_root or resolve_repo_root(Path(__file__).resolve())
    return root / "evals" / "impact" / "families"


def load_experiment_spec(spec_path: Path) -> ExperimentSpec:
    payload = tomllib.loads(spec_path.read_text(encoding="utf-8"))
    consolidated_index_entries = tuple(
        (entry["path"], entry["entry"])
        for entry in payload.get("consolidated_index_entries", [])
    )
    raw_overlays = tuple(
        (entry["source"], entry["destination"])
        for entry in payload.get("raw_overlays", [])
    )
    consolidated_overlays = tuple(
        (entry["source"], entry["destination"])
        for entry in payload.get("consolidated_overlays", [])
    )
    return ExperimentSpec(
        name=payload["name"],
        prompt_family=payload.get("prompt_family", payload["name"]),
        baseline_ref=payload.get("baseline_ref", "HEAD"),
        historical_issue=payload.get("historical_issue", ""),
        raw_docs=tuple(payload.get("raw_docs", [])),
        raw_overlays=raw_overlays,
        consolidated_docs=tuple(payload.get("consolidated_docs", [])),
        consolidated_overlays=consolidated_overlays,
        consolidated_index_entries=consolidated_index_entries,
        ambient_exclude_paths=tuple(payload.get("ambient_exclude_paths", [])),
        strict_scaffold_exclude_paths=tuple(
            payload.get("strict_scaffold_exclude_paths", [])
        ),
        strict_scaffold_index_tokens=tuple(
            (entry["path"], entry["token"])
            for entry in payload.get("strict_scaffold_index_tokens", [])
        ),
    )


def load_family_specs(families_root: Path) -> dict[str, ExperimentSpec]:
    if not families_root.exists():
        return {}
    specs: dict[str, ExperimentSpec] = {}
    for spec_path in sorted(families_root.glob("*/spec.toml")):
        spec = load_experiment_spec(spec_path)
        specs[spec.name] = spec
    return specs


def available_experiments(control_root: Path | None = None) -> dict[str, ExperimentSpec]:
    experiments = dict(EXPERIMENTS)
    experiments.update(load_family_specs(default_families_root(control_root)))
    return experiments


def resolve_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists() and (candidate / "pyproject.toml").exists():
            return candidate
    raise RuntimeError("Could not find the ai-wiki-toolkit repository root.")


def timestamp_slug(now: datetime | None = None) -> str:
    return (now or datetime.now()).strftime("%Y%m%d-%H%M%S")


def default_output_root(source_root: Path, experiment: str) -> Path:
    del source_root
    return WORKDIR_ROOT / experiment / WORKSPACES_DIRNAME / timestamp_slug()


def experiment_output_root(base_root: Path, experiment: str, now: datetime | None = None) -> Path:
    return base_root / experiment / WORKSPACES_DIRNAME / timestamp_slug(now)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    experiments = available_experiments()
    parser.add_argument(
        "--experiment",
        choices=sorted(experiments),
        default=OWNERSHIP_BOUNDARY.name,
        help="Experiment family to prepare.",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=None,
        help="Optional repo root override. Defaults to the current ai-wiki-toolkit repo.",
    )
    parser.add_argument(
        "--source-mode",
        choices=(SOURCE_MODE_COMMITTED_HEAD, SOURCE_MODE_WORKING_TREE),
        default=SOURCE_MODE_COMMITTED_HEAD,
        help=(
            "How to populate the experiment repos. "
            "Default copies the committed HEAD snapshot so local uncommitted changes "
            "do not leak into the variants."
        ),
    )
    parser.add_argument(
        "--baseline-ref",
        default=None,
        help=(
            "Optional git ref to use for the experiment baseline. "
            "Defaults to the experiment's configured baseline ref."
        ),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help="Directory where variant workspaces will be created.",
    )
    parser.add_argument(
        "--workspace-layout",
        choices=(WORKSPACE_LAYOUT_NEUTRAL, WORKSPACE_LAYOUT_LEGACY),
        default=WORKSPACE_LAYOUT_NEUTRAL,
        help=(
            "Use neutral slots for workflow-primary v2 runs, or legacy semantic "
            "variant directory names for round1 compatibility."
        ),
    )
    return parser.parse_args()


def is_excluded_relative(relative: Path) -> bool:
    relative_posix = relative.as_posix()
    if any(relative_posix.startswith(prefix) for prefix in EXCLUDED_RELATIVE_PREFIXES):
        return True
    if relative_posix in EXCLUDED_RELATIVE_PATHS:
        return True
    if any(part in EXCLUDED_ROOT_NAMES for part in relative.parts):
        return True
    return False


def should_copy(source_root: Path, path: Path) -> bool:
    relative = path.relative_to(source_root)
    return not is_excluded_relative(relative)


def copy_repo_tree_from_working_tree(source_root: Path, destination: Path) -> None:
    for path in source_root.rglob("*"):
        if not should_copy(source_root, path):
            continue
        target = destination / path.relative_to(source_root)
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def copy_repo_tree_from_git_ref(source_root: Path, destination: Path, ref: str) -> None:
    archive = subprocess.run(
        ["git", "archive", "--format=tar", ref],
        cwd=source_root,
        check=True,
        capture_output=True,
    ).stdout
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tar:
        tar.extractall(destination, filter="data")


def prune_excluded_paths(destination: Path) -> None:
    for root_name in EXCLUDED_ROOT_NAMES:
        remove_if_exists(destination, root_name)
    for prefix in EXCLUDED_RELATIVE_PREFIXES:
        remove_if_exists(destination, prefix.rstrip("/"))
    for relative_path in EXCLUDED_RELATIVE_PATHS:
        remove_if_exists(destination, relative_path)


def populate_repo_tree(source_root: Path, destination: Path, source_mode: str, baseline_ref: str) -> None:
    if source_mode == SOURCE_MODE_COMMITTED_HEAD:
        copy_repo_tree_from_git_ref(source_root, destination, baseline_ref)
    elif source_mode == SOURCE_MODE_WORKING_TREE:
        copy_repo_tree_from_working_tree(source_root, destination)
    else:
        raise RuntimeError(f"Unknown source mode: {source_mode}")
    prune_excluded_paths(destination)


def copy_overlay_file(control_root: Path, destination_root: Path, relative_path: str) -> None:
    source = control_root / relative_path
    if not source.exists():
        raise RuntimeError(f"Expected overlay file does not exist in control repo: {relative_path}")
    target = destination_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def copy_overlay_to_path(
    control_root: Path,
    destination_root: Path,
    source_path: str,
    destination_path: str,
) -> None:
    source = control_root / source_path
    if not source.exists():
        raise RuntimeError(f"Expected overlay file does not exist in control repo: {source_path}")
    target = destination_root / destination_path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def copy_current_tree(control_root: Path, destination_root: Path, relative_root: str) -> None:
    source = control_root / relative_root
    if not source.exists():
        return
    target_root = destination_root / relative_root
    if target_root.exists():
        shutil.rmtree(target_root)
    for path in source.rglob("*"):
        relative = path.relative_to(control_root)
        if is_excluded_relative(relative):
            continue
        target = destination_root / relative
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def copy_ai_wiki_skills(control_root: Path, destination_root: Path) -> None:
    source = control_root / ".agents" / "skills"
    if not source.exists():
        return
    target = destination_root / ".agents" / "skills"
    for child in source.iterdir():
        if not child.is_dir() or not child.name.startswith(AI_WIKI_SKILL_PREFIX):
            continue
        destination = target / child.name
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(child, destination)


def extract_managed_block(text: str) -> str | None:
    lines = text.splitlines()
    start_index = None
    end_index = None
    for index, line in enumerate(lines):
        if line.strip() == START_MARKER and start_index is None:
            start_index = index
            continue
        if line.strip() == END_MARKER and start_index is not None:
            end_index = index
            break
    if start_index is None or end_index is None or end_index < start_index:
        return None
    return "\n".join(lines[start_index : end_index + 1])


def replace_managed_block(text: str, managed_block: str) -> str:
    stripped = strip_managed_block(text).rstrip()
    if stripped:
        return stripped + "\n\n" + managed_block.rstrip() + "\n"
    return managed_block.rstrip() + "\n"


def copy_current_managed_prompt_block(control_root: Path, destination_root: Path) -> None:
    source = control_root / "AGENTS.md"
    target = destination_root / "AGENTS.md"
    if not source.exists() or not target.exists():
        return
    managed_block = extract_managed_block(source.read_text(encoding="utf-8"))
    if managed_block is None:
        return
    target.write_text(
        replace_managed_block(target.read_text(encoding="utf-8"), managed_block),
        encoding="utf-8",
    )


def ensure_index_entry(root: Path, relative_path: str, entry: str) -> None:
    target = root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        text = target.read_text(encoding="utf-8")
    else:
        header = Path(relative_path).stem.replace("-", " ").title()
        text = f"# {header}\n\n"
    if entry in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    target.write_text(text + entry + "\n", encoding="utf-8")


def inject_raw_memory(root: Path, control_root: Path, spec: ExperimentSpec) -> None:
    for path in spec.raw_docs:
        copy_overlay_file(control_root, root, path)
    for source_path, destination_path in spec.raw_overlays:
        copy_overlay_to_path(control_root, root, source_path, destination_path)


def inject_consolidated_memory(root: Path, control_root: Path, spec: ExperimentSpec) -> None:
    for path in spec.consolidated_docs:
        copy_overlay_file(control_root, root, path)
    for source_path, destination_path in spec.consolidated_overlays:
        copy_overlay_to_path(control_root, root, source_path, destination_path)
    for index_path, entry in spec.consolidated_index_entries:
        ensure_index_entry(root, index_path, entry)


def inject_ambient_memory(root: Path, control_root: Path, spec: ExperimentSpec) -> None:
    copy_current_tree(control_root, root, "ai-wiki")
    copy_ai_wiki_skills(control_root, root)
    copy_current_managed_prompt_block(control_root, root)
    inject_raw_memory(root, control_root, spec)
    inject_consolidated_memory(root, control_root, spec)
    for path in spec.ambient_exclude_paths:
        remove_if_exists(root, path)


def strip_managed_block(text: str) -> str:
    lines = text.splitlines()
    start_index = None
    end_index = None
    for index, line in enumerate(lines):
        if line.strip() == START_MARKER and start_index is None:
            start_index = index
            continue
        if line.strip() == END_MARKER and start_index is not None:
            end_index = index
            break
    if start_index is None or end_index is None or end_index < start_index:
        return text
    kept_lines = lines[:start_index] + lines[end_index + 1 :]
    stripped = "\n".join(kept_lines).strip()
    if not stripped:
        return ""
    return stripped + "\n"


def remove_if_exists(root: Path, relative_path: str) -> None:
    target = root / relative_path
    if not target.exists():
        return
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()


def remove_index_entry(root: Path, relative_path: str, entry: str) -> None:
    target = root / relative_path
    if not target.exists():
        return
    text = target.read_text(encoding="utf-8")
    if entry not in text:
        return
    target.write_text(text.replace(entry + "\n", ""), encoding="utf-8")


def sanitize_plain_repo(root: Path) -> None:
    agents_file = root / "AGENTS.md"
    if agents_file.exists():
        agents_file.write_text(
            strip_managed_block(agents_file.read_text(encoding="utf-8")),
            encoding="utf-8",
        )
    remove_if_exists(root, "ai-wiki")
    skills_dir = root / ".agents" / "skills"
    if skills_dir.exists():
        for child in list(skills_dir.iterdir()):
            if child.name.startswith(AI_WIKI_SKILL_PREFIX):
                shutil.rmtree(child)
        if not any(skills_dir.iterdir()):
            shutil.rmtree(skills_dir.parent)


def remove_relevant_memory(root: Path, spec: ExperimentSpec) -> None:
    overlay_destinations = tuple(
        destination
        for _, destination in (*spec.raw_overlays, *spec.consolidated_overlays)
    )
    for path in (
        *spec.raw_docs,
        *spec.consolidated_docs,
        *overlay_destinations,
        *spec.ambient_exclude_paths,
    ):
        remove_if_exists(root, path)
    for index_path, entry in spec.consolidated_index_entries:
        remove_index_entry(root, index_path, entry)


def remove_index_lines_containing(root: Path, relative_path: str, token: str) -> None:
    target = root / relative_path
    if not target.exists():
        return
    lines = target.read_text(encoding="utf-8").splitlines()
    kept = [line for line in lines if token not in line]
    if kept == lines:
        return
    target.write_text("\n".join(kept).rstrip() + "\n", encoding="utf-8")


def remove_strict_scaffold_memory(root: Path, spec: ExperimentSpec) -> None:
    for path in spec.strict_scaffold_exclude_paths:
        remove_if_exists(root, path)
    for index_path, token in spec.strict_scaffold_index_tokens:
        remove_index_lines_containing(root, index_path, token)


def remove_consolidated_memory(root: Path, spec: ExperimentSpec) -> None:
    for path in spec.consolidated_docs:
        remove_if_exists(root, path)
    for _, destination_path in spec.consolidated_overlays:
        remove_if_exists(root, destination_path)
    for index_path, entry in spec.consolidated_index_entries:
        remove_index_entry(root, index_path, entry)


def remove_raw_memory(root: Path, spec: ExperimentSpec) -> None:
    for path in spec.raw_docs:
        remove_if_exists(root, path)
    for _, destination_path in spec.raw_overlays:
        remove_if_exists(root, destination_path)


def write_variant_note(
    root: Path,
    *,
    control_root: Path,
    spec: ExperimentSpec,
    variant: str,
    baseline_ref: str,
) -> None:
    note = (
        f"# Eval Variant\n\n"
        f"- Experiment: `{spec.name}`\n"
        f"- Variant: `{variant}`\n"
        f"- Baseline ref: `{baseline_ref}`\n"
        f"- Prompt family: `{control_root / 'evals' / 'impact' / 'prompts' / spec.prompt_family}`\n"
        f"- Run each variant in a fresh Codex session.\n"
        f"- Do not compare variants in the same thread.\n"
    )
    (root / "EVAL_VARIANT.md").write_text(note, encoding="utf-8")


def run_command(cwd: Path, *command: str) -> None:
    subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)


def initialize_clean_git_repo(root: Path) -> None:
    run_command(root, "git", "init", "-b", "main")
    run_command(root, "git", "config", "user.name", DEFAULT_HANDLE)
    run_command(root, "git", "config", "user.email", DEFAULT_EMAIL)
    run_command(root, "git", "add", ".")
    run_command(root, "git", "commit", "-m", "Initialize eval workspace")


def prepare_variant(
    source_root: Path,
    output_root: Path,
    spec: ExperimentSpec,
    variant: str,
    *,
    source_mode: str,
    control_root: Path,
    baseline_ref: str,
    destination_name: str | None = None,
    write_note: bool = True,
) -> Path:
    destination = output_root / (destination_name or variant)
    populate_repo_tree(source_root, destination, source_mode, baseline_ref)

    if variant in {"plain_repo_no_aiwiki", "no_aiwiki_workflow"}:
        sanitize_plain_repo(destination)
    elif variant == "aiwiki_no_relevant_memory":
        remove_relevant_memory(destination, spec)
    elif variant == "aiwiki_raw_drafts":
        remove_relevant_memory(destination, spec)
        inject_raw_memory(destination, control_root, spec)
    elif variant == "aiwiki_consolidated":
        remove_relevant_memory(destination, spec)
        inject_consolidated_memory(destination, control_root, spec)
    elif variant == "aiwiki_raw_plus_consolidated":
        remove_relevant_memory(destination, spec)
        inject_raw_memory(destination, control_root, spec)
        inject_consolidated_memory(destination, control_root, spec)
    elif variant == "aiwiki_scaffold_no_target_memory":
        inject_ambient_memory(destination, control_root, spec)
        remove_relevant_memory(destination, spec)
    elif variant == "aiwiki_scaffold_no_adjacent_memory":
        inject_ambient_memory(destination, control_root, spec)
        remove_relevant_memory(destination, spec)
        remove_strict_scaffold_memory(destination, spec)
    elif variant == "aiwiki_linked_raw_only":
        inject_ambient_memory(destination, control_root, spec)
        remove_relevant_memory(destination, spec)
        inject_raw_memory(destination, control_root, spec)
    elif variant == "aiwiki_linked_consolidated_only":
        inject_ambient_memory(destination, control_root, spec)
        remove_relevant_memory(destination, spec)
        inject_consolidated_memory(destination, control_root, spec)
    elif variant == "aiwiki_ambient_memory_workflow":
        inject_ambient_memory(destination, control_root, spec)
    else:
        raise RuntimeError(f"Unknown variant: {variant}")

    if write_note:
        write_variant_note(
            destination,
            control_root=control_root,
            spec=spec,
            variant=variant,
            baseline_ref=baseline_ref,
        )
    initialize_clean_git_repo(destination)
    return destination


def slot_id(index: int) -> str:
    return f"s{index:02d}"


def write_assignment_manifest(
    output_root: Path,
    *,
    spec: ExperimentSpec,
    baseline_ref: str,
    workspace_layout: str,
    assignments: list[dict[str, str]],
) -> None:
    manifest = {
        "schema_version": 2,
        "experiment": spec.name,
        "baseline_ref": baseline_ref,
        "workspace_layout": workspace_layout,
        "primary_comparison": list(WORKFLOW_PRIMARY_VARIANTS),
        "diagnostic_variants": [
            assignment["variant"]
            for assignment in assignments
            if assignment["variant"] not in WORKFLOW_PRIMARY_VARIANTS
        ],
        "slots": assignments,
    }
    (output_root / "assignment.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )


def prepare_variants(
    source_root: Path,
    output_root: Path,
    spec: ExperimentSpec,
    *,
    source_mode: str = SOURCE_MODE_COMMITTED_HEAD,
    control_root: Path | None = None,
    baseline_ref: str | None = None,
    workspace_layout: str = WORKSPACE_LAYOUT_LEGACY,
    variants: tuple[str, ...] | None = None,
) -> list[Path]:
    output_root.mkdir(parents=True, exist_ok=True)
    control_root = (control_root or resolve_repo_root(Path(__file__).resolve())).resolve()
    baseline_ref = baseline_ref or spec.baseline_ref
    if workspace_layout == WORKSPACE_LAYOUT_NEUTRAL:
        selected_variants = variants or WORKFLOW_VARIANTS
        slots_root = output_root / SLOTS_DIRNAME
        prepared: list[Path] = []
        assignments: list[dict[str, str]] = []
        for index, variant in enumerate(selected_variants, start=1):
            slot = slot_id(index)
            workspace = prepare_variant(
                source_root,
                slots_root,
                spec,
                variant,
                source_mode=source_mode,
                control_root=control_root,
                baseline_ref=baseline_ref,
                destination_name=slot,
                write_note=False,
            )
            prepared.append(workspace)
            assignments.append(
                {
                    "slot": slot,
                    "variant": variant,
                    "workspace": str(workspace),
                }
            )
        write_assignment_manifest(
            output_root,
            spec=spec,
            baseline_ref=baseline_ref,
            workspace_layout=workspace_layout,
            assignments=assignments,
        )
        return prepared

    if workspace_layout != WORKSPACE_LAYOUT_LEGACY:
        raise RuntimeError(f"Unknown workspace layout: {workspace_layout}")

    selected_variants = variants or LEGACY_VARIANTS
    prepared = [
        prepare_variant(
            source_root,
            output_root,
            spec,
            variant,
            source_mode=source_mode,
            control_root=control_root,
            baseline_ref=baseline_ref,
        )
        for variant in selected_variants
    ]
    write_assignment_manifest(
        output_root,
        spec=spec,
        baseline_ref=baseline_ref,
        workspace_layout=workspace_layout,
        assignments=[
            {"slot": variant, "variant": variant, "workspace": str(output_root / variant)}
            for variant in selected_variants
        ],
    )
    return prepared


def main() -> None:
    args = parse_args()
    source_root = resolve_repo_root(args.source_root)
    control_root = resolve_repo_root(Path(__file__).resolve())
    spec = available_experiments(control_root)[args.experiment]
    output_root = args.output_root or default_output_root(source_root, spec.name)
    prepared = prepare_variants(
        source_root,
        output_root,
        spec,
        source_mode=args.source_mode,
        control_root=control_root,
        baseline_ref=args.baseline_ref,
        workspace_layout=args.workspace_layout,
    )
    print(f"Prepared {len(prepared)} workspaces under {output_root}")
    for path in prepared:
        print(path)


if __name__ == "__main__":
    main()
