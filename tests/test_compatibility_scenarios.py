from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from ai_wiki_toolkit.cli import app
from helpers import write_git_config

runner = CliRunner()


def test_init_does_not_touch_legacy_ai_wiki_namespace(repo_env: dict[str, Path]) -> None:
    repo = repo_env["repo"]
    legacy_repo_dir = repo / ".ai-wiki"
    legacy_repo_dir.mkdir()
    legacy_repo_file = legacy_repo_dir / "index.md"
    legacy_repo_file.write_text("legacy repo wiki\n", encoding="utf-8")

    legacy_home_file = repo_env["home_dir"].parent / ".ai-wiki" / "system" / "index.md"
    legacy_home_file.parent.mkdir(parents=True)
    legacy_home_file.write_text("legacy system wiki\n", encoding="utf-8")

    result = runner.invoke(app, ["init", "--handle", "alice"])

    assert result.exit_code == 0
    assert legacy_repo_file.read_text(encoding="utf-8") == "legacy repo wiki\n"
    assert legacy_home_file.read_text(encoding="utf-8") == "legacy system wiki\n"


def test_upgrade_scenario_only_changes_managed_toolkit_and_prompt(
    repo_env: dict[str, Path],
) -> None:
    write_git_config(repo_env["repo"], email="engineer@example.com")
    first = runner.invoke(app, ["init"])
    assert first.exit_code == 0

    user_index = repo_env["repo"] / "ai-wiki" / "index.md"
    user_constraints = repo_env["repo"] / "ai-wiki" / "constraints.md"
    repo_toolkit = repo_env["repo"] / "ai-wiki" / "_toolkit" / "system.md"
    home_toolkit = repo_env["home_dir"] / "system" / "_toolkit" / "system.md"
    agent = repo_env["repo"] / "AGENT.md"

    user_index.write_text("# User-owned index\n", encoding="utf-8")
    user_constraints.write_text("# User-owned constraints\n", encoding="utf-8")
    repo_toolkit.write_text("# stale repo toolkit\n", encoding="utf-8")
    home_toolkit.write_text("# stale home toolkit\n", encoding="utf-8")
    agent.write_text("Header\n\n<!-- aiwiki-toolkit:start -->\nstale\n<!-- aiwiki-toolkit:end -->\n", encoding="utf-8")

    second = runner.invoke(app, ["init", "--handle", "lead"])

    assert second.exit_code == 0
    assert user_index.read_text(encoding="utf-8") == "# User-owned index\n"
    assert user_constraints.read_text(encoding="utf-8") == "# User-owned constraints\n"
    assert repo_toolkit.read_text(encoding="utf-8").startswith("# Toolkit Managed System Rules")
    assert home_toolkit.read_text(encoding="utf-8").startswith("# Toolkit Managed Cross-Project Rules")
    assert "ai-wiki/people/<handle>/index.md" in agent.read_text(encoding="utf-8")


def test_init_leaves_existing_home_user_docs_untouched(repo_env: dict[str, Path]) -> None:
    home_index = repo_env["home_dir"] / "system" / "index.md"
    home_index.parent.mkdir(parents=True, exist_ok=True)
    home_index.write_text("# My cross-project index\n", encoding="utf-8")

    result = runner.invoke(app, ["init", "--handle", "alice"])

    assert result.exit_code == 0
    assert home_index.read_text(encoding="utf-8") == "# My cross-project index\n"
