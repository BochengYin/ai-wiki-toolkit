from __future__ import annotations

from datetime import datetime
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import subprocess
import sys


def _load_prepare_variants_module():
    script_path = (
        Path(__file__).resolve().parents[1]
        / "evals"
        / "impact"
        / "scripts"
        / "prepare_variants.py"
    )
    spec = spec_from_file_location("prepare_variants", script_path)
    assert spec is not None
    module = module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _git_status_clean(repo: Path) -> bool:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return not result.stdout.strip()


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _seed_ownership_memory_source(source: Path) -> None:
    source.mkdir()
    (source / ".git").mkdir()
    _write(
        source / "AGENTS.md",
        "Before\n\n<!-- aiwiki-toolkit:start -->\nmanaged\n<!-- aiwiki-toolkit:end -->\n\nAfter\n",
    )
    _write(source / ".agents" / "skills" / "ai-wiki-reuse-check" / "SKILL.md", "reuse\n")
    _write(source / "src" / "module.py", "print('ok')\n")
    _write(
        source / "ai-wiki" / "conventions" / "index.md",
        "# Conventions Index\n\n"
        "- [Package-managed vs user-owned AI wiki docs](package-managed-vs-user-owned-docs.md): keep evolving package-controlled guidance in `_toolkit/**` and keep repo-owned AI wiki docs stable unless a contributor intentionally edits them.\n",
    )
    _write(
        source / "ai-wiki" / "review-patterns" / "index.md",
        "# Review Patterns Index\n\n"
        "- [Shared prompt files must be user-agnostic](shared-prompt-files-must-be-user-agnostic.md): keep repo-shared prompt content stable across different local handles.\n",
    )
    _write(
        source / "ai-wiki" / "conventions" / "package-managed-vs-user-owned-docs.md",
        "rule\n",
    )
    _write(
        source / "ai-wiki" / "review-patterns" / "shared-prompt-files-must-be-user-agnostic.md",
        "pattern\n",
    )
    _write(
        source
        / "ai-wiki"
        / "people"
        / "bochengyin"
        / "drafts"
        / "user-owned-ai-wiki-index-should-not-be-an-upgrade-surface.md",
        "draft\n",
    )
    _write(
        source
        / "ai-wiki"
        / "people"
        / "bochengyin"
        / "drafts"
        / "repo-local-contributor-workflows-should-stay-out-of-the-package-layer.md",
        "draft\n",
    )
    _write(
        source
        / "ai-wiki"
        / "people"
        / "bochengyin"
        / "drafts"
        / "managed-toolkit-workflows-need-a-toc-and-scope-aware-conflict-checks.md",
        "draft\n",
    )
    _write(source / "ai-wiki" / "problems" / "unrelated.md", "ambient\n")


def test_prepare_variants_creates_expected_ownership_boundary_variants(tmp_path: Path) -> None:
    module = _load_prepare_variants_module()
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    (source / ".git").mkdir()
    _write(
        source / "AGENTS.md",
        "Before\n\n<!-- aiwiki-toolkit:start -->\nmanaged\n<!-- aiwiki-toolkit:end -->\n\nAfter\n",
    )
    _write(source / ".agents" / "skills" / "ai-wiki-reuse-check" / "SKILL.md", "reuse\n")
    _write(source / "src" / "module.py", "print('ok')\n")
    _write(
        source / "ai-wiki" / "conventions" / "index.md",
        "# Conventions Index\n\n"
        "- [Package-managed vs user-owned AI wiki docs](package-managed-vs-user-owned-docs.md): keep evolving package-controlled guidance in `_toolkit/**` and keep repo-owned AI wiki docs stable unless a contributor intentionally edits them.\n",
    )
    _write(
        source / "ai-wiki" / "review-patterns" / "index.md",
        "# Review Patterns Index\n\n"
        "- [Shared prompt files must be user-agnostic](shared-prompt-files-must-be-user-agnostic.md): keep repo-shared prompt content stable across different local handles.\n",
    )
    _write(
        source / "ai-wiki" / "conventions" / "package-managed-vs-user-owned-docs.md",
        "rule\n",
    )
    _write(
        source / "ai-wiki" / "review-patterns" / "shared-prompt-files-must-be-user-agnostic.md",
        "pattern\n",
    )
    _write(
        source
        / "ai-wiki"
        / "people"
        / "bochengyin"
        / "drafts"
        / "user-owned-ai-wiki-index-should-not-be-an-upgrade-surface.md",
        "draft\n",
    )
    _write(
        source
        / "ai-wiki"
        / "people"
        / "bochengyin"
        / "drafts"
        / "repo-local-contributor-workflows-should-stay-out-of-the-package-layer.md",
        "draft\n",
    )
    _write(
        source
        / "ai-wiki"
        / "people"
        / "bochengyin"
        / "drafts"
        / "managed-toolkit-workflows-need-a-toc-and-scope-aware-conflict-checks.md",
        "draft\n",
    )

    prepared = module.prepare_variants(
        source,
        output,
        module.OWNERSHIP_BOUNDARY,
        source_mode=module.SOURCE_MODE_WORKING_TREE,
        control_root=source,
        baseline_ref="HEAD",
    )
    assert len(prepared) == 5

    plain = output / "plain_repo_no_aiwiki"
    assert not (plain / "ai-wiki").exists()
    assert "managed" not in (plain / "AGENTS.md").read_text(encoding="utf-8")
    assert not (plain / ".agents").exists()
    assert _git_status_clean(plain)

    no_memory = output / "aiwiki_no_relevant_memory"
    assert not (
        no_memory / "ai-wiki" / "conventions" / "package-managed-vs-user-owned-docs.md"
    ).exists()
    assert not (
        no_memory
        / "ai-wiki"
        / "review-patterns"
        / "shared-prompt-files-must-be-user-agnostic.md"
    ).exists()
    assert not (
        no_memory
        / "ai-wiki"
        / "people"
        / "bochengyin"
        / "drafts"
        / "user-owned-ai-wiki-index-should-not-be-an-upgrade-surface.md"
    ).exists()
    assert _git_status_clean(no_memory)

    raw = output / "aiwiki_raw_drafts"
    assert not (
        raw / "ai-wiki" / "conventions" / "package-managed-vs-user-owned-docs.md"
    ).exists()
    assert (
        raw
        / "ai-wiki"
        / "people"
        / "bochengyin"
        / "drafts"
        / "repo-local-contributor-workflows-should-stay-out-of-the-package-layer.md"
    ).exists()

    consolidated = output / "aiwiki_consolidated"
    assert (
        consolidated / "ai-wiki" / "conventions" / "package-managed-vs-user-owned-docs.md"
    ).exists()
    assert not (
        consolidated
        / "ai-wiki"
        / "people"
        / "bochengyin"
        / "drafts"
        / "repo-local-contributor-workflows-should-stay-out-of-the-package-layer.md"
    ).exists()

    raw_plus = output / "aiwiki_raw_plus_consolidated"
    assert (
        raw_plus / "ai-wiki" / "conventions" / "package-managed-vs-user-owned-docs.md"
    ).exists()
    assert (
        raw_plus
        / "ai-wiki"
        / "people"
        / "bochengyin"
        / "drafts"
        / "repo-local-contributor-workflows-should-stay-out-of-the-package-layer.md"
    ).exists()


def test_load_experiment_spec_from_family_toml() -> None:
    module = _load_prepare_variants_module()
    spec_path = (
        Path(__file__).resolve().parents[1]
        / "evals"
        / "impact"
        / "families"
        / "ownership_boundary"
        / "spec.toml"
    )
    spec = module.load_experiment_spec(spec_path)

    assert spec.name == "ownership_boundary"
    assert spec.baseline_ref == "34cd5a3^"
    assert "repo-local-contributor-workflows" in "\n".join(spec.raw_docs)
    assert spec.consolidated_index_entries


def test_prepare_variants_can_write_workflow_primary_neutral_slots(tmp_path: Path) -> None:
    module = _load_prepare_variants_module()
    source = tmp_path / "source"
    output = tmp_path / "output"
    _seed_ownership_memory_source(source)

    prepared = module.prepare_variants(
        source,
        output,
        module.OWNERSHIP_BOUNDARY,
        source_mode=module.SOURCE_MODE_WORKING_TREE,
        control_root=source,
        baseline_ref="HEAD",
        workspace_layout=module.WORKSPACE_LAYOUT_NEUTRAL,
    )

    assert prepared == [
        output / "slots" / "s01",
        output / "slots" / "s02",
        output / "slots" / "s03",
        output / "slots" / "s04",
        output / "slots" / "s05",
    ]
    assert not (output / "no_aiwiki_workflow").exists()
    assert not (output / "slots" / "s01" / "EVAL_VARIANT.md").exists()
    assert _git_status_clean(output / "slots" / "s02")

    assignment = json.loads((output / "assignment.json").read_text(encoding="utf-8"))
    assert assignment["schema_version"] == 2
    assert assignment["workspace_layout"] == "neutral"
    assert assignment["primary_comparison"] == [
        "no_aiwiki_workflow",
        "aiwiki_ambient_memory_workflow",
    ]
    slots = {slot["slot"]: slot["variant"] for slot in assignment["slots"]}
    assert slots == {
        "s01": "no_aiwiki_workflow",
        "s02": "aiwiki_scaffold_no_target_memory",
        "s03": "aiwiki_linked_raw_only",
        "s04": "aiwiki_linked_consolidated_only",
        "s05": "aiwiki_ambient_memory_workflow",
    }

    no_aiwiki = output / "slots" / "s01"
    scaffold = output / "slots" / "s02"
    raw = output / "slots" / "s03"
    consolidated = output / "slots" / "s04"
    ambient = output / "slots" / "s05"

    assert not (no_aiwiki / "ai-wiki").exists()
    assert (scaffold / "ai-wiki" / "problems" / "unrelated.md").exists()
    assert not (
        scaffold
        / "ai-wiki"
        / "people"
        / "bochengyin"
        / "drafts"
        / "repo-local-contributor-workflows-should-stay-out-of-the-package-layer.md"
    ).exists()
    assert (
        raw
        / "ai-wiki"
        / "people"
        / "bochengyin"
        / "drafts"
        / "repo-local-contributor-workflows-should-stay-out-of-the-package-layer.md"
    ).exists()
    assert not (
        raw / "ai-wiki" / "conventions" / "package-managed-vs-user-owned-docs.md"
    ).exists()
    assert (
        consolidated / "ai-wiki" / "conventions" / "package-managed-vs-user-owned-docs.md"
    ).exists()
    assert (
        ambient / "ai-wiki" / "conventions" / "package-managed-vs-user-owned-docs.md"
    ).exists()
    assert (
        ambient
        / "ai-wiki"
        / "people"
        / "bochengyin"
        / "drafts"
        / "repo-local-contributor-workflows-should-stay-out-of-the-package-layer.md"
    ).exists()


def test_prepare_variants_creates_expected_release_distribution_variants(tmp_path: Path) -> None:
    module = _load_prepare_variants_module()
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    (source / ".git").mkdir()
    _write(
        source / "AGENTS.md",
        "Before\n\n<!-- aiwiki-toolkit:start -->\nmanaged\n<!-- aiwiki-toolkit:end -->\n\nAfter\n",
    )
    _write(source / ".agents" / "skills" / "ai-wiki-reuse-check" / "SKILL.md", "reuse\n")
    _write(source / "src" / "module.py", "print('ok')\n")
    _write(
        source / "ai-wiki" / "conventions" / "index.md",
        "# Conventions Index\n\n"
        "- [Distribution target matrix must match published assets](distribution-target-matrix-must-match-published-assets.md): keep every public release target aligned across release workflows, published assets, runtime target maps, package metadata, archive handling, docs, and smoke checks.\n",
    )
    _write(
        source / "ai-wiki" / "conventions" / "distribution-target-matrix-must-match-published-assets.md",
        "rule\n",
    )
    _write(
        source
        / "ai-wiki"
        / "people"
        / "bochengyin"
        / "drafts"
        / "distribution-target-matrix-must-match-published-assets.md",
        "draft\n",
    )

    prepared = module.prepare_variants(
        source,
        output,
        module.RELEASE_DISTRIBUTION_INTEGRITY,
        source_mode=module.SOURCE_MODE_WORKING_TREE,
        control_root=source,
        baseline_ref="HEAD",
    )
    assert len(prepared) == 5

    plain = output / "plain_repo_no_aiwiki"
    assert not (plain / "ai-wiki").exists()
    assert "managed" not in (plain / "AGENTS.md").read_text(encoding="utf-8")
    assert not (plain / ".agents").exists()
    assert _git_status_clean(plain)

    no_memory = output / "aiwiki_no_relevant_memory"
    assert not (
        no_memory
        / "ai-wiki"
        / "conventions"
        / "distribution-target-matrix-must-match-published-assets.md"
    ).exists()
    assert not (
        no_memory
        / "ai-wiki"
        / "people"
        / "bochengyin"
        / "drafts"
        / "distribution-target-matrix-must-match-published-assets.md"
    ).exists()
    assert "distribution-target-matrix-must-match-published-assets.md" not in (
        no_memory / "ai-wiki" / "conventions" / "index.md"
    ).read_text(encoding="utf-8")
    assert _git_status_clean(no_memory)

    raw = output / "aiwiki_raw_drafts"
    assert not (
        raw
        / "ai-wiki"
        / "conventions"
        / "distribution-target-matrix-must-match-published-assets.md"
    ).exists()
    assert (
        raw
        / "ai-wiki"
        / "people"
        / "bochengyin"
        / "drafts"
        / "distribution-target-matrix-must-match-published-assets.md"
    ).exists()

    consolidated = output / "aiwiki_consolidated"
    assert (
        consolidated
        / "ai-wiki"
        / "conventions"
        / "distribution-target-matrix-must-match-published-assets.md"
    ).exists()
    assert not (
        consolidated
        / "ai-wiki"
        / "people"
        / "bochengyin"
        / "drafts"
        / "distribution-target-matrix-must-match-published-assets.md"
    ).exists()
    assert "distribution-target-matrix-must-match-published-assets.md" in (
        consolidated / "ai-wiki" / "conventions" / "index.md"
    ).read_text(encoding="utf-8")

    raw_plus = output / "aiwiki_raw_plus_consolidated"
    assert (
        raw_plus
        / "ai-wiki"
        / "conventions"
        / "distribution-target-matrix-must-match-published-assets.md"
    ).exists()
    assert (
        raw_plus
        / "ai-wiki"
        / "people"
        / "bochengyin"
        / "drafts"
        / "distribution-target-matrix-must-match-published-assets.md"
    ).exists()


def test_prepare_variants_timestamp_slug_is_stable() -> None:
    module = _load_prepare_variants_module()
    assert (
        module.timestamp_slug(datetime(2026, 4, 22, 23, 45, 6))
        == "20260422-234506"
    )


def test_prepare_variants_default_output_root_uses_first_round_layout() -> None:
    module = _load_prepare_variants_module()
    module.timestamp_slug = lambda now=None: "20260424-200001"
    source_root = Path("/tmp/example-repo")
    assert module.default_output_root(source_root, "ownership_boundary") == Path(
        "/private/tmp/aiwiki_first_round/ownership_boundary/workspaces/20260424-200001"
    )


def test_prepare_variants_experiment_output_root_uses_workspace_layer() -> None:
    module = _load_prepare_variants_module()
    base_root = Path("/tmp/custom-round")
    assert module.experiment_output_root(
        base_root,
        "release_distribution_integrity",
        datetime(2026, 4, 24, 19, 20, 21),
    ) == Path(
        "/tmp/custom-round/release_distribution_integrity/workspaces/20260424-192021"
    )


def test_prepare_variants_committed_head_ignores_uncommitted_eval_changes(tmp_path: Path) -> None:
    module = _load_prepare_variants_module()
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    _git(source, "init", "-b", "main")
    _git(source, "config", "user.name", "Eval User")
    _git(source, "config", "user.email", "eval@example.com")

    _write(source / "AGENTS.md", "Repo instructions\n")
    _write(source / "pyproject.toml", "[project]\nname='fixture'\nversion='0.0.0'\n")
    _write(source / "src" / "module.py", "print('committed')\n")
    _write(
        source / "ai-wiki" / "conventions" / "index.md",
        "# Conventions Index\n\n"
        "- [Package-managed vs user-owned AI wiki docs](package-managed-vs-user-owned-docs.md): keep evolving package-controlled guidance in `_toolkit/**` and keep repo-owned AI wiki docs stable unless a contributor intentionally edits them.\n",
    )
    _write(
        source / "ai-wiki" / "review-patterns" / "index.md",
        "# Review Patterns Index\n\n"
        "- [Shared prompt files must be user-agnostic](shared-prompt-files-must-be-user-agnostic.md): keep repo-shared prompt content stable across different local handles.\n",
    )
    _write(
        source / "ai-wiki" / "conventions" / "package-managed-vs-user-owned-docs.md",
        "rule\n",
    )
    _write(
        source / "ai-wiki" / "review-patterns" / "shared-prompt-files-must-be-user-agnostic.md",
        "pattern\n",
    )
    _write(
        source
        / "ai-wiki"
        / "people"
        / "bochengyin"
        / "drafts"
        / "user-owned-ai-wiki-index-should-not-be-an-upgrade-surface.md",
        "draft\n",
    )
    _write(
        source
        / "ai-wiki"
        / "people"
        / "bochengyin"
        / "drafts"
        / "repo-local-contributor-workflows-should-stay-out-of-the-package-layer.md",
        "draft\n",
    )
    _write(
        source
        / "ai-wiki"
        / "people"
        / "bochengyin"
        / "drafts"
        / "managed-toolkit-workflows-need-a-toc-and-scope-aware-conflict-checks.md",
        "draft\n",
    )

    _git(source, "add", ".")
    _git(source, "commit", "-m", "Baseline")

    _write(source / "src" / "module.py", "print('dirty working tree')\n")
    _write(source / "evals" / "impact" / "README.md", "local eval controls\n")
    _write(source / "tests" / "test_impact_eval_setup.py", "local test\n")
    _write(
        source
        / "ai-wiki"
        / "people"
        / "bochengyin"
        / "drafts"
        / "impact-eval-prompts-should-backsolve-from-concrete-history.md",
        "meta draft\n",
    )

    module.prepare_variants(
        source,
        output,
        module.OWNERSHIP_BOUNDARY,
        source_mode=module.SOURCE_MODE_COMMITTED_HEAD,
        control_root=source,
        baseline_ref="HEAD",
    )

    raw_plus = output / "aiwiki_raw_plus_consolidated"
    assert (raw_plus / "src" / "module.py").read_text(encoding="utf-8") == "print('committed')\n"
    assert not (raw_plus / "evals" / "impact").exists()
    assert not (raw_plus / "tests" / "test_impact_eval_setup.py").exists()
    assert not (
        raw_plus
        / "ai-wiki"
        / "people"
        / "bochengyin"
        / "drafts"
        / "impact-eval-prompts-should-backsolve-from-concrete-history.md"
    ).exists()


def test_prepare_variants_can_use_historical_baseline_and_overlay_current_memory(tmp_path: Path) -> None:
    module = _load_prepare_variants_module()
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    _git(source, "init", "-b", "main")
    _git(source, "config", "user.name", "Eval User")
    _git(source, "config", "user.email", "eval@example.com")

    _write(source / "AGENTS.md", "Repo instructions\n")
    _write(source / "pyproject.toml", "[project]\nname='fixture'\nversion='0.0.0'\n")
    _write(
        source / "ai-wiki" / "conventions" / "index.md",
        "# Conventions Index\n\n",
    )
    _write(
        source / "ai-wiki" / "review-patterns" / "index.md",
        "# Review Patterns Index\n\n"
        "- [Shared prompt files must be user-agnostic](shared-prompt-files-must-be-user-agnostic.md): keep repo-shared prompt content stable across different local handles.\n",
    )
    _write(
        source / "ai-wiki" / "review-patterns" / "shared-prompt-files-must-be-user-agnostic.md",
        "pattern\n",
    )
    _write(source / "ai-wiki" / "workflows.md", "# Workflows\n\n")
    _write(source / "CONTRIBUTING.md", "# Contributing\n\n")
    _write(source / "CHANGELOG.md", "# Changelog\n\n")
    _write(source / "src" / "module.py", "print('baseline')\n")
    _git(source, "add", ".")
    _git(source, "commit", "-m", "Historical baseline")
    baseline_ref = _git(source, "rev-parse", "HEAD").strip()

    _write(source / "scripts" / "pr_flow.py", "print('helper')\n")
    _write(source / "tests" / "test_pr_flow_script.py", "def test_helper():\n    pass\n")
    _write(
        source / "ai-wiki" / "conventions" / "package-managed-vs-user-owned-docs.md",
        "rule\n",
    )
    _write(
        source
        / "ai-wiki"
        / "people"
        / "bochengyin"
        / "drafts"
        / "repo-local-contributor-workflows-should-stay-out-of-the-package-layer.md",
        "draft\n",
    )
    _write(
        source
        / "ai-wiki"
        / "people"
        / "bochengyin"
        / "drafts"
        / "user-owned-ai-wiki-index-should-not-be-an-upgrade-surface.md",
        "draft\n",
    )
    _write(
        source
        / "ai-wiki"
        / "people"
        / "bochengyin"
        / "drafts"
        / "managed-toolkit-workflows-need-a-toc-and-scope-aware-conflict-checks.md",
        "draft\n",
    )
    _git(source, "add", ".")
    _git(source, "commit", "-m", "Later helper and memory state")

    module.prepare_variants(
        source,
        output,
        module.OWNERSHIP_BOUNDARY,
        source_mode=module.SOURCE_MODE_COMMITTED_HEAD,
        control_root=source,
        baseline_ref=baseline_ref,
    )

    for variant in (
        "aiwiki_no_relevant_memory",
        "aiwiki_raw_drafts",
        "aiwiki_consolidated",
        "aiwiki_raw_plus_consolidated",
    ):
        assert not (output / variant / "scripts" / "pr_flow.py").exists()
        assert not (output / variant / "tests" / "test_pr_flow_script.py").exists()

    assert (
        output
        / "aiwiki_raw_drafts"
        / "ai-wiki"
        / "people"
        / "bochengyin"
        / "drafts"
        / "repo-local-contributor-workflows-should-stay-out-of-the-package-layer.md"
    ).exists()
    assert (
        output
        / "aiwiki_consolidated"
        / "ai-wiki"
        / "conventions"
        / "package-managed-vs-user-owned-docs.md"
    ).exists()
    assert not (
        output
        / "aiwiki_no_relevant_memory"
        / "ai-wiki"
        / "review-patterns"
        / "shared-prompt-files-must-be-user-agnostic.md"
    ).exists()
