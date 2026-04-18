"""CLI for ai-wiki-toolkit."""

from __future__ import annotations

import typer

from ai_wiki_toolkit import __version__
from ai_wiki_toolkit.paths import RepoRootNotFoundError
from ai_wiki_toolkit.scaffold import (
    install_workspace,
    skill_manual_merge_url,
    uninstall_workspace,
)

app = typer.Typer(help="Initialize and maintain ai-wiki-toolkit scaffolds.")


def _version_callback(value: bool) -> None:
    if not value:
        return
    typer.echo(f"ai-wiki-toolkit {__version__}")
    raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    )
) -> None:
    """aiwiki-toolkit command group."""


def _echo_install_result(result) -> None:
    typer.echo(f"Repo wiki: {result.paths.repo_wiki_dir}")
    typer.echo(f"System wiki: {result.paths.system_dir}")
    typer.echo(f"Resolved handle: {result.resolved_handle}")
    typer.echo(f"Created directories: {len(result.created_dirs)}")
    typer.echo(f"Created files: {len(result.created_files)}")
    typer.echo(f"Updated managed files: {len(result.updated_managed_files)}")
    typer.echo(f"Updated prompt files: {len(result.updated_prompt_files)}")
    typer.echo(
        "Recommendation: configure git user.name and git user.email for stable handle resolution."
    )
    if result.skipped_skill_files:
        typer.echo(f"Skipped existing skill files: {len(result.skipped_skill_files)}")
        for path in result.skipped_skill_files:
            typer.echo(f"Skipped skill file: {path}")
        typer.echo(f"Manual merge guide: {skill_manual_merge_url()}")


@app.command("install")
def install(
    handle: str | None = typer.Option(
        None,
        "--handle",
        help="Override the user handle used for ai-wiki/people/<handle>/drafts/.",
    )
) -> None:
    """Install or refresh the repo and home AI wiki toolkit scaffolds."""
    try:
        result = install_workspace(handle=handle)
    except RepoRootNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    _echo_install_result(result)


@app.command("init")
def init_alias(
    handle: str | None = typer.Option(
        None,
        "--handle",
        help="Override the user handle used for ai-wiki/people/<handle>/drafts/.",
    )
) -> None:
    """Backward-compatible alias for install."""
    install(handle=handle)


@app.command("uninstall")
def uninstall(
    purge_user_docs: bool = typer.Option(
        False,
        "--purge-user-docs",
        help="Also remove repo-local user-owned ai-wiki documents. Shared home docs are preserved.",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        help="Confirm destructive removal when using --purge-user-docs.",
    ),
) -> None:
    """Remove managed ai-wiki-toolkit files and prompt wiring."""
    if purge_user_docs and not yes:
        typer.echo(
            "--purge-user-docs is destructive. Re-run with --purge-user-docs --yes.",
            err=True,
        )
        raise typer.Exit(code=1)

    try:
        result = uninstall_workspace(purge_user_docs=purge_user_docs)
    except RepoRootNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Repo wiki: {result.paths.repo_wiki_dir}")
    typer.echo(f"System wiki: {result.paths.system_dir}")
    typer.echo(f"Removed directories: {len(result.removed_dirs)}")
    typer.echo(f"Removed files: {len(result.removed_files)}")
    typer.echo(f"Updated prompt files: {len(result.updated_prompt_files)}")
    typer.echo(f"Deleted prompt files: {len(result.deleted_prompt_files)}")
    typer.echo(f"Removed opencode key: {'yes' if result.removed_opencode_key else 'no'}")
    if purge_user_docs:
        typer.echo("Shared home wiki preserved: yes")


if __name__ == "__main__":
    app()
