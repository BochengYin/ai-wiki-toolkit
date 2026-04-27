from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from ai_wiki_toolkit.cli import app

runner = CliRunner()


def _snapshot_workspace_text_files(repo_env: dict[str, Path]) -> dict[str, str]:
    snapshots: dict[str, str] = {}
    for prefix, root in (("repo", repo_env["repo"]), ("home", repo_env["home_dir"])):
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            snapshots[f"{prefix}/{path.relative_to(root).as_posix()}"] = path.read_text(
                encoding="utf-8"
            )
    return snapshots


def test_install_command_matches_init_behavior(repo_env: dict[str, Path]) -> None:
    result = runner.invoke(app, ["install", "--handle", "alice"])

    assert result.exit_code == 0
    assert (repo_env["repo"] / "ai-wiki" / "people" / "alice" / "drafts").is_dir()
    assert (repo_env["repo"] / ".env.aiwiki").exists()
    assert (repo_env["repo"] / "AGENT.md").exists()
    assert (repo_env["repo"] / "ai-wiki" / "_toolkit" / "index.md").exists()
    assert (repo_env["repo"] / "ai-wiki" / "_toolkit" / "workflows.md").exists()
    assert (repo_env["repo"] / "ai-wiki" / "conventions" / "index.md").exists()
    assert (repo_env["repo"] / "ai-wiki" / "problems" / "index.md").exists()
    assert (repo_env["repo"] / "ai-wiki" / "features" / "index.md").exists()
    assert (
        repo_env["repo"]
        / ".agents"
        / "skills"
        / "ai-wiki-consolidate-drafts"
        / "SKILL.md"
    ).exists()
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
        repo_env["repo"]
        / ".agents"
        / "skills"
        / "ai-wiki-clarify-before-code"
        / "SKILL.md"
    ).exists()
    assert (
        repo_env["repo"]
        / ".agents"
        / "skills"
        / "ai-wiki-capture-review-learning"
        / "SKILL.md"
    ).exists()
    assert (
        "Recommendation: configure git user.name and git user.email for stable handle resolution."
        in result.output
    )


def test_install_tolerates_duplicate_options_in_git_config(
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

    result = runner.invoke(app, ["install"])

    assert result.exit_code == 0
    assert (repo_env["repo"] / "ai-wiki" / "people" / "review-bot" / "drafts").is_dir()


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
        "# Ignore AI wiki local state so normal agent use does not dirty git status.\n"
        ".env.aiwiki\n"
        "ai-wiki/metrics/reuse-events/\n"
        "ai-wiki/metrics/task-checks/\n"
        "ai-wiki/_toolkit/metrics/\n"
        "ai-wiki/_toolkit/work/\n"
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
        "# Ignore AI wiki local state so normal agent use does not dirty git status.\n"
        ".env.aiwiki\n"
        "ai-wiki/metrics/reuse-events/\n"
        "ai-wiki/metrics/task-checks/\n"
        "ai-wiki/_toolkit/metrics/\n"
        "ai-wiki/_toolkit/work/\n"
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
    assert not (repo / ".env.aiwiki").exists()
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


def test_install_refreshes_existing_repo_skill_files(
    repo_env: dict[str, Path],
) -> None:
    skill_file = (
        repo_env["repo"]
        / ".agents"
        / "skills"
        / "ai-wiki-consolidate-drafts"
        / "references"
        / "output-contract.md"
    )
    skill_file.parent.mkdir(parents=True, exist_ok=True)
    skill_file.write_text("# Custom consolidate output contract\n", encoding="utf-8")

    result = runner.invoke(app, ["install", "--handle", "alice"])

    assert result.exit_code == 0
    assert "# AI Wiki Draft Consolidation" in skill_file.read_text(encoding="utf-8")
    assert "Updated skill files: 1" in result.output
    assert f"Updated skill file: {skill_file}" in result.output


def test_install_refreshes_existing_ai_wiki_footer_skill_contracts(
    repo_env: dict[str, Path],
) -> None:
    output_contract = (
        repo_env["repo"]
        / ".agents"
        / "skills"
        / "ai-wiki-reuse-check"
        / "references"
        / "output-contract.md"
    )
    output_contract.parent.mkdir(parents=True, exist_ok=True)
    output_contract.write_text(
        "\n".join(
            (
                "# Output Contract",
                "",
                "AI Wiki Reuse Evidence: wiki_used",
                "AI Wiki Eligibility: eligible",
                "AI Wiki Material Effects: changed_plan",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["install", "--handle", "alice"])

    assert result.exit_code == 0
    refreshed = output_contract.read_text(encoding="utf-8")
    assert "AI Wiki Reuse: user-owned memory used" in refreshed
    assert "AI Wiki Task Relevance: relevant | optional | not_relevant" in refreshed
    assert "AI Wiki Impact: <short user-facing impacts or none>" in refreshed
    assert "AI Wiki Eligibility" not in refreshed
    assert "AI Wiki Material Effects" not in refreshed
    assert "Updated skill files: 1" in result.output


def test_repeated_install_is_product_idempotent_for_same_handle(
    repo_env: dict[str, Path],
) -> None:
    first = runner.invoke(app, ["install", "--handle", "alice"])
    assert first.exit_code == 0

    first_snapshot = _snapshot_workspace_text_files(repo_env)

    second = runner.invoke(app, ["install", "--handle", "alice"])

    assert second.exit_code == 0
    assert _snapshot_workspace_text_files(repo_env) == first_snapshot
    assert "Created directories: 0" in second.output
    assert "Created files: 0" in second.output
    assert "Updated ignore files: 0" in second.output
    assert "Updated managed files: 0" in second.output
    assert "Updated skill files: 0" in second.output
    assert "Updated prompt files: 0" in second.output


def test_install_with_second_handle_adds_person_tree_without_churning_shared_files(
    repo_env: dict[str, Path],
) -> None:
    first = runner.invoke(app, ["install", "--handle", "alice"])
    assert first.exit_code == 0

    repo = repo_env["repo"]
    alice_draft = repo / "ai-wiki" / "people" / "alice" / "drafts" / "alice-note.md"
    alice_draft.write_text("# Alice note\n", encoding="utf-8")
    agent_before = (repo / "AGENT.md").read_text(encoding="utf-8")
    index_before = (repo / "ai-wiki" / "index.md").read_text(encoding="utf-8")
    workflows_before = (repo / "ai-wiki" / "workflows.md").read_text(encoding="utf-8")

    second = runner.invoke(app, ["install", "--handle", "bob"])

    assert second.exit_code == 0
    assert "Resolved handle: bob" in second.output
    assert (repo / "ai-wiki" / "people" / "alice" / "index.md").exists()
    assert (repo / "ai-wiki" / "people" / "alice" / "drafts").is_dir()
    assert (repo / "ai-wiki" / "people" / "bob" / "index.md").exists()
    assert (repo / "ai-wiki" / "people" / "bob" / "drafts").is_dir()
    assert alice_draft.read_text(encoding="utf-8") == "# Alice note\n"
    assert (repo / "AGENT.md").read_text(encoding="utf-8") == agent_before
    assert (repo / "ai-wiki" / "index.md").read_text(encoding="utf-8") == index_before
    assert (repo / "ai-wiki" / "workflows.md").read_text(encoding="utf-8") == workflows_before


def test_install_reuses_existing_person_tree_when_two_inputs_resolve_to_same_handle(
    repo_env: dict[str, Path],
) -> None:
    first = runner.invoke(app, ["install", "--handle", "Alice Reviewer"])
    assert first.exit_code == 0

    repo = repo_env["repo"]
    person_dir = repo / "ai-wiki" / "people" / "alice-reviewer"
    person_index_before = (person_dir / "index.md").read_text(encoding="utf-8")
    draft = person_dir / "drafts" / "carry-forward.md"
    draft.write_text("# Keep me\n", encoding="utf-8")

    second = runner.invoke(app, ["install", "--handle", "alice-reviewer"])

    assert second.exit_code == 0
    assert "Resolved handle: alice-reviewer" in second.output
    assert draft.read_text(encoding="utf-8") == "# Keep me\n"
    assert (person_dir / "index.md").read_text(encoding="utf-8") == person_index_before
    assert sorted(path.name for path in (repo / "ai-wiki" / "people").iterdir()) == [
        "alice-reviewer"
    ]


def test_refresh_metrics_regenerates_managed_catalog_and_stats(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    repo = repo_env["repo"]
    stale_catalog = repo / "ai-wiki" / "_toolkit" / "catalog.json"
    stale_task_stats = repo / "ai-wiki" / "_toolkit" / "metrics" / "task-stats.json"
    stale_work_state = repo / "ai-wiki" / "_toolkit" / "work" / "state.json"
    stale_catalog.write_text("{}", encoding="utf-8")
    stale_task_stats.write_text("{}", encoding="utf-8")
    stale_work_state.write_text("{}", encoding="utf-8")

    result = runner.invoke(app, ["refresh-metrics"])

    assert result.exit_code == 0
    assert stale_catalog.read_text(encoding="utf-8") != "{}"
    assert stale_task_stats.read_text(encoding="utf-8") != "{}"
    assert stale_work_state.read_text(encoding="utf-8") != "{}"
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
