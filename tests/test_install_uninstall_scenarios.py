from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from ai_wiki_toolkit.cli import app

runner = CliRunner()


def test_install_command_matches_init_behavior(repo_env: dict[str, Path]) -> None:
    result = runner.invoke(app, ["install", "--handle", "alice"])

    assert result.exit_code == 0
    assert (repo_env["repo"] / "ai-wiki" / "people" / "alice" / "drafts").is_dir()
    assert (repo_env["repo"] / "AGENT.md").exists()
    assert (
        "Recommendation: configure git user.name and git user.email for stable handle resolution."
        in result.output
    )


def test_uninstall_default_removes_managed_layer_but_preserves_user_docs(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    repo = repo_env["repo"]
    home = repo_env["home_dir"]
    (repo / "ai-wiki" / "constraints.md").write_text("# User constraints\n", encoding="utf-8")
    (repo / "ai-wiki" / "review-patterns" / "boundary.md").write_text(
        "# Shared pattern\n", encoding="utf-8"
    )
    (repo / "ai-wiki" / "people" / "alice" / "drafts" / "draft.md").write_text(
        "# Draft\n", encoding="utf-8"
    )
    (repo / "opencode.json").write_text(
        json.dumps(
            {
                "otherTool": {"enabled": True},
                "aiwikiToolkit": {"schemaVersion": 1},
            }
        ),
        encoding="utf-8",
    )

    uninstall_result = runner.invoke(app, ["uninstall"])

    assert uninstall_result.exit_code == 0
    assert not (repo / "ai-wiki" / "_toolkit").exists()
    assert not (home / "system" / "_toolkit").exists()
    assert (repo / "ai-wiki" / "constraints.md").read_text(encoding="utf-8") == "# User constraints\n"
    assert (repo / "ai-wiki" / "review-patterns" / "boundary.md").exists()
    assert (repo / "ai-wiki" / "people" / "alice" / "drafts" / "draft.md").exists()
    assert not (repo / "AGENT.md").exists()

    opencode_written = json.loads((repo / "opencode.json").read_text(encoding="utf-8"))
    assert opencode_written == {"otherTool": {"enabled": True}}
    assert "Removed opencode key: yes" in uninstall_result.output


def test_uninstall_preserves_prompt_file_content_outside_managed_block(
    repo_env: dict[str, Path],
) -> None:
    prompt = repo_env["repo"] / "CLAUDE.md"
    prompt.write_text("Header\n", encoding="utf-8")
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    uninstall_result = runner.invoke(app, ["uninstall"])

    assert uninstall_result.exit_code == 0
    assert prompt.exists()
    assert prompt.read_text(encoding="utf-8") == "Header\n"


def test_reinstall_restores_managed_layer_without_overwriting_user_docs(
    repo_env: dict[str, Path],
) -> None:
    first = runner.invoke(app, ["install", "--handle", "alice"])
    assert first.exit_code == 0

    repo = repo_env["repo"]
    (repo / "ai-wiki" / "constraints.md").write_text("# User constraints\n", encoding="utf-8")

    uninstall_result = runner.invoke(app, ["uninstall"])
    assert uninstall_result.exit_code == 0
    assert not (repo / "ai-wiki" / "_toolkit").exists()

    reinstall_result = runner.invoke(app, ["install", "--handle", "alice"])

    assert reinstall_result.exit_code == 0
    assert (repo / "ai-wiki" / "_toolkit" / "system.md").exists()
    assert (repo / "AGENT.md").exists()
    assert (repo / "ai-wiki" / "constraints.md").read_text(encoding="utf-8") == "# User constraints\n"


def test_uninstall_with_purge_requires_yes(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    result = runner.invoke(app, ["uninstall", "--purge-user-docs"])

    assert result.exit_code == 1
    assert "--purge-user-docs is destructive" in result.output
    assert (repo_env["repo"] / "ai-wiki").exists()


def test_uninstall_with_purge_and_yes_removes_repo_docs_but_preserves_shared_home_docs(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0
    (repo_env["home_dir"] / "system" / "preferences.md").write_text(
        "# Shared preferences\n", encoding="utf-8"
    )

    result = runner.invoke(app, ["uninstall", "--purge-user-docs", "--yes"])

    assert result.exit_code == 0
    assert not (repo_env["repo"] / "ai-wiki").exists()
    assert (repo_env["home_dir"] / "system").exists()
    assert not (repo_env["home_dir"] / "system" / "_toolkit").exists()
    assert (repo_env["home_dir"] / "system" / "preferences.md").read_text(encoding="utf-8") == (
        "# Shared preferences\n"
    )
    assert not (repo_env["repo"] / "AGENT.md").exists()
    assert "Shared home wiki preserved: yes" in result.output
