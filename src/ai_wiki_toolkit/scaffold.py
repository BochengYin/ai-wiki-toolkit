"""Scaffold creation for ai-wiki-toolkit."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import shutil

from ai_wiki_toolkit.content import (
    AI_WIKI_UPDATE_SKILL_DIR,
    TOOLKIT_GITHUB_URL,
    managed_home_toolkit_files,
    managed_repo_toolkit_files,
    repo_starter_files,
    repo_skill_starter_files,
    system_starter_files,
)
from ai_wiki_toolkit.opencode import remove_opencode_config
from ai_wiki_toolkit.paths import (
    ToolkitPaths,
    build_paths,
    existing_prompt_targets,
    resolve_user_handle,
)
from ai_wiki_toolkit.prompt import remove_managed_block_file, upsert_managed_block_file


@dataclass
class InitResult:
    paths: ToolkitPaths
    resolved_handle: str
    created_dirs: list[Path] = field(default_factory=list)
    created_files: list[Path] = field(default_factory=list)
    updated_prompt_files: list[Path] = field(default_factory=list)
    updated_managed_files: list[Path] = field(default_factory=list)
    skipped_skill_files: list[Path] = field(default_factory=list)


@dataclass
class UninstallResult:
    paths: ToolkitPaths
    removed_dirs: list[Path] = field(default_factory=list)
    removed_files: list[Path] = field(default_factory=list)
    updated_prompt_files: list[Path] = field(default_factory=list)
    deleted_prompt_files: list[Path] = field(default_factory=list)
    removed_opencode_key: bool = False


def _ensure_dir(path: Path, result: InitResult) -> None:
    if path.exists():
        return
    path.mkdir(parents=True, exist_ok=True)
    result.created_dirs.append(path)


def _write_if_missing(path: Path, content: str, result: InitResult) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    result.created_files.append(path)


def _write_skill_if_missing(path: Path, content: str, result: InitResult) -> None:
    if path.exists():
        result.skipped_skill_files.append(path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    result.created_files.append(path)


def _write_managed(path: Path, content: str, result: InitResult) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        result.created_files.append(path)
        return

    current = path.read_text(encoding="utf-8")
    if current == content:
        return

    path.write_text(content, encoding="utf-8")
    result.updated_managed_files.append(path)


def install_workspace(start: Path | None = None, handle: str | None = None) -> InitResult:
    paths = build_paths(start)
    resolved_handle = resolve_user_handle(paths.repo_root, explicit_handle=handle)
    result = InitResult(paths=paths, resolved_handle=resolved_handle)

    for directory in (
        paths.repo_wiki_dir,
        paths.repo_wiki_dir / "trails",
        paths.review_patterns_dir,
        paths.people_dir / resolved_handle / "drafts",
        paths.repo_toolkit_dir,
        paths.system_dir,
        paths.system_dir / "playbooks",
        paths.system_dir / "templates",
        paths.home_toolkit_dir,
    ):
        _ensure_dir(directory, result)

    for relative_path, content in repo_starter_files().items():
        _write_if_missing(paths.repo_wiki_dir / relative_path, content, result)

    for relative_path, content in system_starter_files().items():
        _write_if_missing(paths.system_dir / relative_path, content, result)

    for relative_path, content in managed_repo_toolkit_files().items():
        _write_managed(paths.repo_toolkit_dir / relative_path, content, result)

    for relative_path, content in managed_home_toolkit_files().items():
        _write_managed(paths.home_toolkit_dir / relative_path, content, result)

    for relative_path, content in repo_skill_starter_files().items():
        _write_skill_if_missing(paths.repo_root / relative_path, content, result)

    prompt_targets = existing_prompt_targets(paths.repo_root)
    if not prompt_targets:
        prompt_targets = [paths.repo_root / "AGENT.md"]

    for path in prompt_targets:
        if upsert_managed_block_file(path, resolved_handle):
            result.updated_prompt_files.append(path)

    return result


def init_workspace(start: Path | None = None, handle: str | None = None) -> InitResult:
    return install_workspace(start=start, handle=handle)


def _remove_tree_if_exists(path: Path, result: UninstallResult) -> None:
    if not path.exists():
        return
    shutil.rmtree(path)
    result.removed_dirs.append(path)


def _remove_file_if_exists(path: Path, result: UninstallResult) -> None:
    if not path.exists():
        return
    path.unlink()
    result.removed_files.append(path)


def uninstall_workspace(
    start: Path | None = None, *, purge_user_docs: bool = False
) -> UninstallResult:
    paths = build_paths(start)
    result = UninstallResult(paths=paths)

    prompt_targets = existing_prompt_targets(paths.repo_root)
    for path in prompt_targets:
        updated, deleted = remove_managed_block_file(path)
        if not updated:
            continue
        if deleted:
            result.deleted_prompt_files.append(path)
        else:
            result.updated_prompt_files.append(path)

    repo_opencode = paths.repo_root / "opencode.json"
    opencode_before_exists = repo_opencode.exists()
    opencode_before_text = (
        repo_opencode.read_text(encoding="utf-8") if opencode_before_exists else None
    )
    opencode_result = remove_opencode_config(repo_opencode)
    if opencode_before_exists:
        if not repo_opencode.exists() or repo_opencode.read_text(encoding="utf-8") != opencode_before_text:
            result.removed_opencode_key = True
            if opencode_result == {}:
                result.removed_files.append(repo_opencode)

    if purge_user_docs:
        _remove_tree_if_exists(paths.repo_wiki_dir, result)
        _remove_tree_if_exists(paths.home_toolkit_dir, result)
        return result

    _remove_tree_if_exists(paths.repo_toolkit_dir, result)
    _remove_tree_if_exists(paths.home_toolkit_dir, result)
    return result


def skill_manual_merge_url() -> str:
    return f"{TOOLKIT_GITHUB_URL}/tree/main/{AI_WIKI_UPDATE_SKILL_DIR}"
