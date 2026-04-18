"""Path resolution helpers for ai-wiki-toolkit."""

from __future__ import annotations

import configparser
from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess
from typing import Mapping

REPO_DIRNAME = "ai-wiki"
HOME_DIRNAME = "ai-wiki"
HOME_OVERRIDE_ENV = "AIWIKI_TOOLKIT_HOME_DIR"
HANDLE_OVERRIDE_ENV = "AIWIKI_TOOLKIT_HANDLE"
MODEL_OVERRIDE_ENV = "AIWIKI_TOOLKIT_MODEL"
HOST_MODEL_ENV_VARS = (
    "OPENAI_MODEL",
    "ANTHROPIC_MODEL",
    "CLAUDE_CODE_MODEL",
    "CODEX_MODEL",
    "OPENCODE_MODEL",
    "AI_MODEL",
)
PROMPT_FILENAMES = ("AGENTS.md", "AGENT.md", "CLAUDE.md")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
_GITHUB_NOREPLY_RE = re.compile(
    r"^(?:\d+\+)?(?P<username>[^@+]+)@users\.noreply\.github\.com$", re.IGNORECASE
)


class RepoRootNotFoundError(RuntimeError):
    """Raised when a git repository root cannot be found."""


@dataclass(frozen=True)
class ToolkitPaths:
    repo_root: Path
    repo_wiki_dir: Path
    review_patterns_dir: Path
    people_dir: Path
    home_dir: Path
    system_dir: Path
    repo_toolkit_dir: Path
    home_toolkit_dir: Path


def resolve_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    raise RepoRootNotFoundError(
        "Could not find a git repository root from the current directory."
    )


def resolve_home_dir() -> Path:
    override = os.getenv(HOME_OVERRIDE_ENV)
    if override:
        return Path(override).expanduser().resolve()
    return (Path.home() / HOME_DIRNAME).resolve()


def build_paths(start: Path | None = None) -> ToolkitPaths:
    repo_root = resolve_repo_root(start)
    home_dir = resolve_home_dir()
    repo_wiki_dir = repo_root / REPO_DIRNAME
    system_dir = home_dir / "system"
    return ToolkitPaths(
        repo_root=repo_root,
        repo_wiki_dir=repo_wiki_dir,
        review_patterns_dir=repo_wiki_dir / "review-patterns",
        people_dir=repo_wiki_dir / "people",
        home_dir=home_dir,
        system_dir=system_dir,
        repo_toolkit_dir=repo_wiki_dir / "_toolkit",
        home_toolkit_dir=system_dir / "_toolkit",
    )


def existing_prompt_targets(repo_root: Path) -> list[Path]:
    return [repo_root / name for name in PROMPT_FILENAMES if (repo_root / name).exists()]


def slugify(value: str) -> str:
    lowered = value.strip().lower()
    slug = _NON_ALNUM_RE.sub("-", lowered).strip("-")
    return slug or "unknown"


def _git_config_path(repo_root: Path) -> Path | None:
    git_dir = repo_root / ".git"
    if git_dir.is_dir():
        return git_dir / "config"
    return None


def _read_git_config_file_value(repo_root: Path, key: str) -> str | None:
    config_path = _git_config_path(repo_root)
    if not config_path or not config_path.exists():
        return None

    section, _, option = key.partition(".")
    if not section or not option:
        return None

    parser = configparser.ConfigParser()
    parser.read(config_path, encoding="utf-8")
    if parser.has_option(section, option):
        return parser.get(section, option)
    return None


def _read_git_config_subprocess_value(repo_root: Path, key: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "config", "--get", key],
            cwd=repo_root,
            capture_output=True,
            check=False,
            text=True,
        )
    except OSError:
        return None

    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def read_git_config_value(repo_root: Path, key: str) -> str | None:
    return _read_git_config_file_value(repo_root, key) or _read_git_config_subprocess_value(
        repo_root, key
    )


def git_identity(repo_root: Path) -> tuple[str | None, str | None]:
    local_email = _read_git_config_file_value(repo_root, "user.email")
    local_name = _read_git_config_file_value(repo_root, "user.name")
    if local_email is not None or local_name is not None:
        return local_email, local_name

    return (
        _read_git_config_subprocess_value(repo_root, "user.email"),
        _read_git_config_subprocess_value(repo_root, "user.name"),
    )


def git_derived_handle(
    git_email: str | None = None, git_name: str | None = None
) -> str | None:
    if git_email:
        match = _GITHUB_NOREPLY_RE.match(git_email.strip())
        if match:
            return slugify(match.group("username"))
        local_part = git_email.partition("@")[0].strip()
        if local_part:
            return slugify(local_part)
    if git_name:
        return slugify(git_name)
    return None


def resolve_user_handle(
    repo_root: Path,
    explicit_handle: str | None = None,
    env: Mapping[str, str] | None = None,
    git_email: str | None = None,
    git_name: str | None = None,
) -> str:
    env = env or os.environ
    if explicit_handle:
        return slugify(explicit_handle)

    env_handle = env.get(HANDLE_OVERRIDE_ENV)
    if env_handle:
        return slugify(env_handle)

    if git_email is None or git_name is None:
        resolved_email, resolved_name = git_identity(repo_root)
        if git_email is None:
            git_email = resolved_email
        if git_name is None:
            git_name = resolved_name

    derived = git_derived_handle(
        git_email=git_email,
        git_name=git_name,
    )
    return derived or "unknown"


def resolve_model_name(
    explicit_model: str | None = None, env: Mapping[str, str] | None = None
) -> str:
    env = env or os.environ
    if explicit_model:
        return explicit_model

    toolkit_model = env.get(MODEL_OVERRIDE_ENV)
    if toolkit_model:
        return toolkit_model

    for variable in HOST_MODEL_ENV_VARS:
        value = env.get(variable)
        if value:
            return value
    return "unknown"
