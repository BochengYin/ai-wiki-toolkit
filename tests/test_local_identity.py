from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from ai_wiki_toolkit.cli import app
from ai_wiki_toolkit.paths import read_repo_local_env, resolve_user_handle

runner = CliRunner()


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
