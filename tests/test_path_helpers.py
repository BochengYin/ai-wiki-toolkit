from __future__ import annotations

from pathlib import Path

import pytest

from ai_wiki_toolkit.paths import (
    HANDLE_OVERRIDE_ENV,
    HOST_MODEL_ENV_VARS,
    MODEL_OVERRIDE_ENV,
    git_derived_handle,
    git_identity,
    resolve_model_name,
    resolve_user_handle,
    slugify,
)
from helpers import write_git_config


def test_slugify_normalizes_handles() -> None:
    assert slugify("Bocheng Yin") == "bocheng-yin"
    assert slugify("  CODE/Review  ") == "code-review"


def test_resolve_user_handle_prefers_explicit_override(repo_env: dict[str, Path]) -> None:
    handle = resolve_user_handle(repo_env["repo"], explicit_handle="Team Lead")
    assert handle == "team-lead"


def test_resolve_user_handle_prefers_env_override(
    repo_env: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(HANDLE_OVERRIDE_ENV, "Reviewer-A")
    handle = resolve_user_handle(repo_env["repo"])
    assert handle == "reviewer-a"


def test_resolve_user_handle_from_github_noreply_email(repo_env: dict[str, Path]) -> None:
    write_git_config(
        repo_env["repo"],
        email="162966873+BochengYin@users.noreply.github.com",
        name="Ignored Name",
    )
    handle = resolve_user_handle(repo_env["repo"])
    assert handle == "bochengyin"


def test_resolve_user_handle_from_email_local_part(repo_env: dict[str, Path]) -> None:
    write_git_config(
        repo_env["repo"], email="review.bot@example.com", name="Ignored Name"
    )
    handle = resolve_user_handle(repo_env["repo"])
    assert handle == "review-bot"


def test_resolve_user_handle_from_user_name_fallback(repo_env: dict[str, Path]) -> None:
    write_git_config(repo_env["repo"], name="Alice Reviewer")
    handle = resolve_user_handle(repo_env["repo"])
    assert handle == "alice-reviewer"


def test_git_identity_falls_back_when_config_parser_rejects_duplicate_option(
    repo_env: dict[str, Path],
) -> None:
    (repo_env["repo"] / ".git" / "config").write_text(
        "\n".join(
            (
                "[core]",
                "\trepositoryformatversion = 0",
                "\tbare = false",
                "\tlogallrefupdates = true",
                "[user]",
                "\temail = review.bot@example.com",
                "\tname = Review Bot",
                '[branch "feat/test"]',
                "\tgithub-pr-owner-number = 1",
                "\tgithub-pr-owner-number = 2",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    assert git_identity(repo_env["repo"]) == ("review.bot@example.com", "Review Bot")
    assert resolve_user_handle(repo_env["repo"]) == "review-bot"


def test_resolve_user_handle_falls_back_to_unknown(repo_env: dict[str, Path]) -> None:
    handle = resolve_user_handle(repo_env["repo"], git_email="", git_name="")
    assert handle == "unknown"


def test_git_derived_handle_prefers_email_before_name() -> None:
    assert (
        git_derived_handle(
            git_email="foo.bar@example.com",
            git_name="Someone Else",
        )
        == "foo-bar"
    )


def test_resolve_model_name_prefers_explicit_value() -> None:
    assert resolve_model_name(explicit_model="gpt-5.4") == "gpt-5.4"


def test_resolve_model_name_uses_toolkit_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(MODEL_OVERRIDE_ENV, "claude-sonnet")
    assert resolve_model_name() == "claude-sonnet"


@pytest.mark.parametrize("variable", HOST_MODEL_ENV_VARS[:3])
def test_resolve_model_name_uses_known_host_variables(
    variable: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    for candidate in HOST_MODEL_ENV_VARS:
        monkeypatch.delenv(candidate, raising=False)
    monkeypatch.setenv(variable, "host-model")
    assert resolve_model_name() == "host-model"


def test_resolve_model_name_falls_back_to_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(MODEL_OVERRIDE_ENV, raising=False)
    for variable in HOST_MODEL_ENV_VARS:
        monkeypatch.delenv(variable, raising=False)
    assert resolve_model_name() == "unknown"
