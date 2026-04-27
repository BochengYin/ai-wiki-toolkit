"""Repo-local identity file helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ai_wiki_toolkit.managed_block import remove_managed_block_file, upsert_managed_block_file
from ai_wiki_toolkit.paths import (
    HANDLE_OVERRIDE_ENV,
    LOCAL_ACTOR_HANDLE_ENV,
    LOCAL_DISPLAY_NAME_ENV,
    LOCAL_IDENTITY_SOURCE_ENV,
    LOCAL_IDENTITY_VERSION_ENV,
    repo_local_env_path,
)

LOCAL_ENV_BLOCK_START = "# <!-- aiwiki-toolkit:start -->"
LOCAL_ENV_BLOCK_END = "# <!-- aiwiki-toolkit:end -->"
LOCAL_IDENTITY_VERSION = "1"


@dataclass(frozen=True)
class LocalIdentityResult:
    path: Path
    actor_handle: str
    updated: bool


def _dotenv_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', r"\"")
    return f'"{escaped}"'


def _identity_source(*, explicit_handle: str | None, env_handle: str | None) -> str:
    if explicit_handle:
        return "explicit-handle"
    if env_handle:
        return HANDLE_OVERRIDE_ENV
    return "git-config-or-existing-local"


def render_local_identity_body(
    *,
    actor_handle: str,
    display_name: str | None = None,
    identity_source: str = "git-config-or-existing-local",
) -> str:
    lines = [
        "# Local aiwiki-toolkit identity. This file is ignored by git.",
        f"{LOCAL_IDENTITY_VERSION_ENV}={LOCAL_IDENTITY_VERSION}",
        f"{LOCAL_ACTOR_HANDLE_ENV}={actor_handle}",
    ]
    if display_name:
        lines.append(f"{LOCAL_DISPLAY_NAME_ENV}={_dotenv_quote(display_name)}")
    lines.extend(
        [
            f"{LOCAL_IDENTITY_SOURCE_ENV}={identity_source}",
        ]
    )
    return "\n".join(lines)


def upsert_local_identity_file(
    *,
    repo_root: Path,
    actor_handle: str,
    explicit_handle: str | None = None,
    env_handle: str | None = None,
) -> LocalIdentityResult:
    body = render_local_identity_body(
        actor_handle=actor_handle,
        identity_source=_identity_source(
            explicit_handle=explicit_handle,
            env_handle=env_handle,
        ),
    )
    path = repo_local_env_path(repo_root)
    updated = upsert_managed_block_file(
        path,
        body=body,
        start_marker=LOCAL_ENV_BLOCK_START,
        end_marker=LOCAL_ENV_BLOCK_END,
    )
    return LocalIdentityResult(path=path, actor_handle=actor_handle, updated=updated)


def remove_local_identity_file(repo_root: Path) -> tuple[bool, bool]:
    return remove_managed_block_file(
        repo_local_env_path(repo_root),
        start_marker=LOCAL_ENV_BLOCK_START,
        end_marker=LOCAL_ENV_BLOCK_END,
    )
