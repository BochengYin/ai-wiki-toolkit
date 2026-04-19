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
    assert (repo_env["repo"] / "ai-wiki" / "_toolkit" / "index.md").exists()
    assert (repo_env["repo"] / "ai-wiki" / "_toolkit" / "workflows.md").exists()
    assert (
        repo_env["repo"]
        / ".agents"
        / "skills"
        / "ai-wiki-reuse-check"
        / "SKILL.md"
    ).exists()
    assert (
        repo_env["repo"]
        / ".agents"
        / "skills"
        / "ai-wiki-update-check"
        / "SKILL.md"
    ).exists()
    assert (
        "Recommendation: configure git user.name and git user.email for stable handle resolution."
        in result.output
    )


def test_install_refreshes_managed_workflow_docs_without_overwriting_user_workflows(
    repo_env: dict[str, Path],
) -> None:
    first = runner.invoke(app, ["install", "--handle", "alice"])
    assert first.exit_code == 0

    repo = repo_env["repo"]
    managed_index = repo / "ai-wiki" / "_toolkit" / "index.md"
    managed_workflows = repo / "ai-wiki" / "_toolkit" / "workflows.md"
    user_workflows = repo / "ai-wiki" / "workflows.md"
    user_custom = "# Project Workflows\n\nMy repo-specific workflow.\n"

    managed_index.write_text("# stale managed index\n", encoding="utf-8")
    managed_workflows.write_text("# stale managed workflows\n", encoding="utf-8")
    user_workflows.write_text(user_custom, encoding="utf-8")

    second = runner.invoke(app, ["install", "--handle", "alice"])

    assert second.exit_code == 0
    assert managed_index.read_text(encoding="utf-8").startswith("# Toolkit Managed Index")
    assert managed_workflows.read_text(encoding="utf-8").startswith("# Toolkit Managed Workflows")
    assert user_workflows.read_text(encoding="utf-8") == user_custom


def test_install_upserts_gitignore_block_without_overwriting_user_entries(
    repo_env: dict[str, Path],
) -> None:
    repo = repo_env["repo"]
    gitignore = repo / ".gitignore"
    gitignore.write_text(".venv/\nnode_modules/\n", encoding="utf-8")

    result = runner.invoke(app, ["install", "--handle", "alice"])

    assert result.exit_code == 0
    assert gitignore.read_text(encoding="utf-8") == (
        ".venv/\n"
        "node_modules/\n"
        "\n"
        "# <!-- aiwiki-toolkit:start -->\n"
        "# Ignore AI wiki telemetry so normal agent use does not dirty git status.\n"
        "ai-wiki/metrics/reuse-events/\n"
        "ai-wiki/metrics/task-checks/\n"
        "ai-wiki/_toolkit/metrics/\n"
        "ai-wiki/_toolkit/catalog.json\n"
        "# <!-- aiwiki-toolkit:end -->\n"
    )
    assert "Updated ignore files: 1" in result.output


def test_install_refreshes_stale_gitignore_block_in_place(repo_env: dict[str, Path]) -> None:
    repo = repo_env["repo"]
    gitignore = repo / ".gitignore"
    gitignore.write_text(
        ".venv/\n\n"
        "# <!-- aiwiki-toolkit:start -->\n"
        "# stale ignore block\n"
        "# <!-- aiwiki-toolkit:end -->\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["install", "--handle", "alice"])

    assert result.exit_code == 0
    assert gitignore.read_text(encoding="utf-8") == (
        ".venv/\n"
        "\n"
        "# <!-- aiwiki-toolkit:start -->\n"
        "# Ignore AI wiki telemetry so normal agent use does not dirty git status.\n"
        "ai-wiki/metrics/reuse-events/\n"
        "ai-wiki/metrics/task-checks/\n"
        "ai-wiki/_toolkit/metrics/\n"
        "ai-wiki/_toolkit/catalog.json\n"
        "# <!-- aiwiki-toolkit:end -->\n"
    )
    assert "Updated ignore files: 1" in result.output


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
    assert (
        repo / ".agents" / "skills" / "ai-wiki-update-check" / "SKILL.md"
    ).exists()
    assert not (repo / ".gitignore").exists()
    assert (repo / "ai-wiki" / "constraints.md").read_text(encoding="utf-8") == "# User constraints\n"
    assert (repo / "ai-wiki" / "review-patterns" / "boundary.md").exists()
    assert (repo / "ai-wiki" / "people" / "alice" / "drafts" / "draft.md").exists()
    assert not (repo / "AGENT.md").exists()

    opencode_written = json.loads((repo / "opencode.json").read_text(encoding="utf-8"))
    assert opencode_written == {"otherTool": {"enabled": True}}
    assert "Removed opencode key: yes" in uninstall_result.output


def test_uninstall_removes_gitignore_block_but_preserves_user_entries(
    repo_env: dict[str, Path],
) -> None:
    repo = repo_env["repo"]
    gitignore = repo / ".gitignore"
    gitignore.write_text(".venv/\n", encoding="utf-8")
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    uninstall_result = runner.invoke(app, ["uninstall"])

    assert uninstall_result.exit_code == 0
    assert gitignore.exists()
    assert gitignore.read_text(encoding="utf-8") == ".venv/\n"
    assert "Updated ignore files: 1" in uninstall_result.output
    assert "Deleted ignore files: 0" in uninstall_result.output


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


def test_install_skips_existing_repo_skill_files_and_reports_manual_merge(
    repo_env: dict[str, Path],
) -> None:
    skill_file = (
        repo_env["repo"]
        / ".agents"
        / "skills"
        / "ai-wiki-update-check"
        / "references"
        / "decision-rules.md"
    )
    skill_file.parent.mkdir(parents=True, exist_ok=True)
    skill_file.write_text("# Custom decision rules\n", encoding="utf-8")

    result = runner.invoke(app, ["install", "--handle", "alice"])

    assert result.exit_code == 0
    assert skill_file.read_text(encoding="utf-8") == "# Custom decision rules\n"
    assert "Skipped existing skill files: 1" in result.output
    assert f"Skipped skill file: {skill_file}" in result.output
    assert (
        "Manual merge guide: https://github.com/BochengYin/ai-wiki-toolkit/tree/main/.agents/skills"
        in result.output
    )


def test_refresh_metrics_regenerates_managed_catalog_and_stats(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    repo = repo_env["repo"]
    stale_catalog = repo / "ai-wiki" / "_toolkit" / "catalog.json"
    stale_task_stats = repo / "ai-wiki" / "_toolkit" / "metrics" / "task-stats.json"
    stale_catalog.write_text("{}", encoding="utf-8")
    stale_task_stats.write_text("{}", encoding="utf-8")

    result = runner.invoke(app, ["refresh-metrics"])

    assert result.exit_code == 0
    assert stale_catalog.read_text(encoding="utf-8") != "{}"
    assert stale_task_stats.read_text(encoding="utf-8") != "{}"
    assert "Refreshed files:" in result.output


def test_refresh_metrics_requires_initialized_repo_wiki(repo_env: dict[str, Path]) -> None:
    result = runner.invoke(app, ["refresh-metrics"])

    assert result.exit_code == 1
    assert "Run `aiwiki-toolkit install` first." in result.output


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
