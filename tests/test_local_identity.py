from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

import ai_wiki_toolkit.cli as cli
import ai_wiki_toolkit.paths as path_helpers
from ai_wiki_toolkit.cli import app
from ai_wiki_toolkit.paths import read_repo_local_env, resolve_user_handle

runner = CliRunner()


def _hide_git_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(path_helpers, "git_identity", lambda repo_root: (None, None))


def test_install_creates_gitignored_env_aiwiki_identity(repo_env: dict[str, Path]) -> None:
    result = runner.invoke(app, ["install", "--handle", "Alice Reviewer"])

    assert result.exit_code == 0
    local_env = repo_env["repo"] / ".env.aiwiki"
    assert local_env.read_text(encoding="utf-8") == (
        "# <!-- aiwiki-toolkit:start -->\n"
        "# Local aiwiki-toolkit identity. This file is ignored by git.\n"
        "AIWIKI_TOOLKIT_LOCAL_IDENTITY_VERSION=1\n"
        "AIWIKI_TOOLKIT_ACTOR_HANDLE=alice-reviewer\n"
        "AIWIKI_TOOLKIT_IDENTITY_SOURCE=explicit-handle\n"
        "# <!-- aiwiki-toolkit:end -->\n"
    )
    assert ".env.aiwiki\n" in (repo_env["repo"] / ".gitignore").read_text(encoding="utf-8")
    assert read_repo_local_env(repo_env["repo"])["AIWIKI_TOOLKIT_ACTOR_HANDLE"] == "alice-reviewer"


def test_install_prompts_for_team_id_when_identity_is_missing(
    repo_env: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli, "_can_prompt_for_team_id", lambda: True)
    _hide_git_identity(monkeypatch)

    result = runner.invoke(app, ["install"], input="Alice Reviewer\n")

    assert result.exit_code == 0
    assert "Could not detect a git user.name or user.email." in result.output
    assert "AI wiki needs a stable local ID for your team identity." in result.output
    assert "What ID would you prefer to use in this team?" in result.output
    assert "Using AI wiki ID: alice-reviewer" in result.output
    assert (
        "This ID will be stored in .env.aiwiki and used for "
        "ai-wiki/people/alice-reviewer/. AI wiki workflows can also use it as "
        "your branch-name component."
    ) in result.output
    assert (repo_env["repo"] / "ai-wiki" / "people" / "alice-reviewer" / "drafts").is_dir()
    local_env = read_repo_local_env(repo_env["repo"])
    assert local_env["AIWIKI_TOOLKIT_ACTOR_HANDLE"] == "alice-reviewer"
    assert local_env["AIWIKI_TOOLKIT_IDENTITY_SOURCE"] == "prompted-handle"


def test_init_prompts_for_team_id_when_identity_is_missing(
    repo_env: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli, "_can_prompt_for_team_id", lambda: True)
    _hide_git_identity(monkeypatch)

    result = runner.invoke(app, ["init"], input="Team User\n")

    assert result.exit_code == 0
    assert "Using AI wiki ID: team-user" in result.output
    assert (repo_env["repo"] / "ai-wiki" / "people" / "team-user" / "drafts").is_dir()


def test_install_reprompts_for_empty_or_invalid_team_id(
    repo_env: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli, "_can_prompt_for_team_id", lambda: True)
    _hide_git_identity(monkeypatch)

    result = runner.invoke(app, ["install"], input="\n???\nByin\n")

    assert result.exit_code == 0
    assert (
        result.output.count(
            "Please enter a team ID, for example: alice, alice-reviewer, or byin."
        )
        == 2
    )
    assert "Using AI wiki ID: byin" in result.output
    assert (repo_env["repo"] / "ai-wiki" / "people" / "byin" / "drafts").is_dir()


def test_install_fails_non_interactive_when_identity_is_missing(
    repo_env: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    _hide_git_identity(monkeypatch)

    result = runner.invoke(app, ["install"])

    assert result.exit_code == 1
    assert (
        "Could not detect an AI wiki ID and this shell is non-interactive.\n"
        "Run `aiwiki-toolkit install --handle your-name` or set "
        "`AIWIKI_TOOLKIT_HANDLE`."
    ) in result.output
    assert not (repo_env["repo"] / "ai-wiki" / "people" / "unknown").exists()


@pytest.mark.parametrize("unresolved_handle", ["unknown", "undefined", "undefine"])
def test_install_prompts_when_existing_env_aiwiki_identity_is_unresolved(
    repo_env: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
    unresolved_handle: str,
) -> None:
    (repo_env["repo"] / ".env.aiwiki").write_text(
        "\n".join(
            [
                "# <!-- aiwiki-toolkit:start -->",
                f"AIWIKI_TOOLKIT_ACTOR_HANDLE={unresolved_handle}",
                "# <!-- aiwiki-toolkit:end -->",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(cli, "_can_prompt_for_team_id", lambda: True)
    _hide_git_identity(monkeypatch)

    result = runner.invoke(app, ["install"], input="Team User\n")

    assert result.exit_code == 0
    assert "Using AI wiki ID: team-user" in result.output
    assert (repo_env["repo"] / "ai-wiki" / "people" / "team-user" / "drafts").is_dir()
    local_env = read_repo_local_env(repo_env["repo"])
    assert local_env["AIWIKI_TOOLKIT_ACTOR_HANDLE"] == "team-user"
    assert local_env["AIWIKI_TOOLKIT_IDENTITY_SOURCE"] == "prompted-handle"


def test_resolve_user_handle_uses_env_aiwiki_before_git_config(repo_env: dict[str, Path]) -> None:
    (repo_env["repo"] / ".git" / "config").write_text(
        "\n".join(
            [
                "[core]",
                "\trepositoryformatversion = 0",
                "[user]",
                "\temail = bob@example.com",
                "\tname = Bob Example",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (repo_env["repo"] / ".env.aiwiki").write_text(
        "\n".join(
            [
                "# <!-- aiwiki-toolkit:start -->",
                "AIWIKI_TOOLKIT_ACTOR_HANDLE=alice",
                "# <!-- aiwiki-toolkit:end -->",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert resolve_user_handle(repo_env["repo"]) == "alice"


def test_env_override_wins_over_env_aiwiki(repo_env: dict[str, Path], monkeypatch) -> None:
    (repo_env["repo"] / ".env.aiwiki").write_text("AIWIKI_TOOLKIT_ACTOR_HANDLE=alice\n", encoding="utf-8")
    monkeypatch.setenv("AIWIKI_TOOLKIT_HANDLE", "Carol")

    assert resolve_user_handle(repo_env["repo"]) == "carol"
