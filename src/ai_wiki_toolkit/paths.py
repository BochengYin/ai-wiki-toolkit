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
LOCAL_ENV_FILENAME = ".env.aiwiki"
LOCAL_ACTOR_HANDLE_ENV = "AIWIKI_TOOLKIT_ACTOR_HANDLE"
LOCAL_DISPLAY_NAME_ENV = "AIWIKI_TOOLKIT_DISPLAY_NAME"
LOCAL_IDENTITY_SOURCE_ENV = "AIWIKI_TOOLKIT_IDENTITY_SOURCE"
LOCAL_IDENTITY_VERSION_ENV = "AIWIKI_TOOLKIT_LOCAL_IDENTITY_VERSION"
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
UNRESOLVED_HANDLE_VALUES = frozenset({"unknown", "undefined", "undefine"})
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


@dataclass(frozen=True)
class ResolvedUserHandle:
    handle: str
    source: str


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


def repo_local_env_path(repo_root: Path) -> Path:
    return repo_root / LOCAL_ENV_FILENAME


def slugify(value: str) -> str:
    lowered = value.strip().lower()
    slug = _NON_ALNUM_RE.sub("-", lowered).strip("-")
    return slug or "unknown"


def is_unresolved_handle(value: str | None) -> bool:
    if not value:
        return True
    return slugify(value) in UNRESOLVED_HANDLE_VALUES


def usable_user_handle(value: str | None) -> str | None:
    if is_unresolved_handle(value):
        return None
    return slugify(value or "")


def _parse_dotenv_value(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {'"', "'"}:
        inner = stripped[1:-1]
        if stripped[0] == '"':
            inner = inner.replace(r"\"", '"').replace(r"\\", "\\")
        return inner
    return stripped


def read_repo_local_env(repo_root: Path) -> dict[str, str]:
    path = repo_local_env_path(repo_root)
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        normalized_key = key.strip()
        if not normalized_key or not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", normalized_key):
            continue
        values[normalized_key] = _parse_dotenv_value(value)
    return values


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
    try:
        parser.read(config_path, encoding="utf-8")
    except configparser.Error:
        return None
    if parser.has_option(section, option):
        return parser.get(section, option)
    return None


def _read_git_config_local_subprocess_value(repo_root: Path, key: str) -> str | None:
    config_path = _git_config_path(repo_root)
    if not config_path or not config_path.exists():
        return None

    try:
        result = subprocess.run(
            ["git", "config", "--file", str(config_path), "--get", key],
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
    return (
        _read_git_config_file_value(repo_root, key)
        or _read_git_config_local_subprocess_value(repo_root, key)
        or _read_git_config_subprocess_value(repo_root, key)
    )


def git_identity(repo_root: Path) -> tuple[str | None, str | None]:
    local_email = _read_git_config_file_value(
        repo_root, "user.email"
    ) or _read_git_config_local_subprocess_value(repo_root, "user.email")
    local_name = _read_git_config_file_value(
        repo_root, "user.name"
    ) or _read_git_config_local_subprocess_value(repo_root, "user.name")
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
    resolved = resolve_user_handle_candidate(
        repo_root,
        explicit_handle=explicit_handle,
        env=env,
        git_email=git_email,
        git_name=git_name,
    )
    return resolved.handle if resolved else "unknown"


def resolve_user_handle_candidate(
    repo_root: Path,
    explicit_handle: str | None = None,
    env: Mapping[str, str] | None = None,
    git_email: str | None = None,
    git_name: str | None = None,
) -> ResolvedUserHandle | None:
    env = env or os.environ
    explicit = usable_user_handle(explicit_handle)
    if explicit:
        return ResolvedUserHandle(handle=explicit, source="explicit-handle")

    env_handle = usable_user_handle(env.get(HANDLE_OVERRIDE_ENV))
    if env_handle:
        return ResolvedUserHandle(handle=env_handle, source=HANDLE_OVERRIDE_ENV)

    local_handle = usable_user_handle(
        read_repo_local_env(repo_root).get(LOCAL_ACTOR_HANDLE_ENV)
    )
    if local_handle:
        return ResolvedUserHandle(handle=local_handle, source=LOCAL_ENV_FILENAME)

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
    git_handle = usable_user_handle(derived)
    if git_handle:
        return ResolvedUserHandle(handle=git_handle, source="git-config")
    return None


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
