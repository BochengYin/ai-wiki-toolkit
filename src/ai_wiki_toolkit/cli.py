"""CLI for ai-wiki-toolkit."""

from __future__ import annotations

import typer

from ai_wiki_toolkit import __version__
from ai_wiki_toolkit.doctor import run_doctor
from ai_wiki_toolkit.paths import RepoRootNotFoundError
from ai_wiki_toolkit.reuse_events import (
    EVIDENCE_MODES,
    RETRIEVAL_MODES,
    REUSE_OUTCOMES,
    RepoWikiNotInitializedError,
    record_reuse_event,
)
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


def _echo_doctor_result(result, *, suggest_index_upgrade: bool, strict: bool) -> None:
    typer.echo(f"Repo: {result.paths.repo_root}")
    typer.echo(f"Handle: {result.resolved_handle}")
    typer.echo("")

    severity_rank = {"ERROR": 0, "WARN": 1, "INFO": 2, "OK": 3}
    findings = sorted(
        result.findings,
        key=lambda finding: (severity_rank.get(finding.severity, 99), finding.path, finding.code),
    )
    for finding in findings:
        typer.echo(f"{finding.severity:<5} {finding.path} {finding.message}")

    actionable_findings = [f for f in findings if f.severity in {"ERROR", "WARN"}]
    if actionable_findings:
        typer.echo("")
        typer.echo("Suggested next steps:")
        step = 1
        if any(f.path.startswith("ai-wiki/_toolkit/") for f in actionable_findings):
            typer.echo(f"{step}. Run `aiwiki-toolkit install` to refresh managed files if needed.")
            step += 1
        if any(f.path.startswith("ai-wiki/") and not f.path.startswith("ai-wiki/_toolkit/") for f in actionable_findings):
            if suggest_index_upgrade:
                typer.echo(
                    f"{step}. Review the suggested index updates below and copy or merge them into the listed paths."
                )
            else:
                typer.echo(
                    f"{step}. Re-run with `aiwiki-toolkit doctor --suggest-index-upgrade` to print the latest starter content for the affected index files."
                )
            step += 1
        if any(f.path in {"AGENT.md", "AGENTS.md", "CLAUDE.md"} for f in actionable_findings):
            typer.echo(f"{step}. Re-run `aiwiki-toolkit install` if you need the managed prompt block refreshed.")

    if suggest_index_upgrade and result.suggestions:
        typer.echo("")
        typer.echo("Suggested index updates:")
        typer.echo("")
        for suggestion in result.suggestions:
            typer.echo(f"Path: {suggestion.path}")
            typer.echo(f"Why: {suggestion.reason}")
            typer.echo(f"How: {suggestion.replace_hint}")
            typer.echo("Starter content:")
            typer.echo("```md")
            typer.echo(suggestion.content.rstrip("\n"))
            typer.echo("```")
            typer.echo("")

    if strict and actionable_findings:
        raise typer.Exit(code=1)


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


@app.command("record-reuse")
def record_reuse(
    doc_id: str = typer.Option(
        ...,
        "--doc-id",
        help="Document identifier, usually the ai-wiki path without the .md suffix.",
    ),
    task_id: str = typer.Option(
        ...,
        "--task-id",
        help="Stable task identifier for grouping reuse observations.",
    ),
    retrieval_mode: str = typer.Option(
        ...,
        "--retrieval-mode",
        help=f"How the document was reached. Choices: {', '.join(RETRIEVAL_MODES)}.",
    ),
    evidence_mode: str = typer.Option(
        ...,
        "--evidence-mode",
        help=f"How strongly the reuse was observed. Choices: {', '.join(EVIDENCE_MODES)}.",
    ),
    reuse_outcome: str = typer.Option(
        ...,
        "--reuse-outcome",
        help=f"How useful the reuse was. Choices: {', '.join(REUSE_OUTCOMES)}.",
    ),
    doc_kind: str | None = typer.Option(
        None,
        "--doc-kind",
        help="Optional override for the document kind. Defaults to an inferred value from --doc-id.",
    ),
    reuse_effects: list[str] | None = typer.Option(
        None,
        "--reuse-effect",
        help="Repeatable effect label such as avoided_search, avoided_retry, or faster_resolution.",
    ),
    agent_name: str | None = typer.Option(
        None,
        "--agent-name",
        help="Optional agent identifier such as codex or claude-code.",
    ),
    model: str | None = typer.Option(
        None,
        "--model",
        help="Optional model name. Defaults to AIWIKI_TOOLKIT_MODEL or detected host model env vars.",
    ),
    notes: str | None = typer.Option(
        None,
        "--notes",
        help="Optional free-form note describing the reuse observation.",
    ),
    saved_tokens: int | None = typer.Option(
        None,
        "--saved-tokens",
        min=0,
        help="Optional estimated token savings for this observation.",
    ),
    saved_seconds: int | None = typer.Option(
        None,
        "--saved-seconds",
        min=0,
        help="Optional estimated seconds saved for this observation.",
    ),
    observed_at: str | None = typer.Option(
        None,
        "--observed-at",
        help="Optional explicit timestamp. Defaults to the current local time in ISO-8601 format.",
    ),
) -> None:
    """Append one reuse observation and refresh managed metric aggregates."""
    try:
        result = record_reuse_event(
            doc_id=doc_id,
            task_id=task_id,
            retrieval_mode=retrieval_mode,
            evidence_mode=evidence_mode,
            reuse_outcome=reuse_outcome,
            doc_kind=doc_kind,
            reuse_effects=reuse_effects or [],
            agent_name=agent_name,
            model=model,
            notes=notes,
            saved_tokens=saved_tokens,
            saved_seconds=saved_seconds,
            observed_at=observed_at,
        )
    except RepoRootNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except RepoWikiNotInitializedError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Recorded reuse event: {result.event_id}")
    typer.echo(f"Observed at: {result.observed_at}")
    typer.echo(f"Event log: {result.event_log_path}")
    typer.echo(f"Document stats: {result.document_stats_path}")
    typer.echo(f"Task stats: {result.task_stats_path}")


@app.command("doctor")
def doctor(
    handle: str | None = typer.Option(
        None,
        "--handle",
        help="Override the user handle used for person index checks.",
    ),
    suggest_index_upgrade: bool = typer.Option(
        False,
        "--suggest-index-upgrade",
        help="Print the latest starter content for any missing or outdated repo index files.",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Exit with code 1 if warnings or errors are found.",
    ),
) -> None:
    """Diagnose AI wiki index drift and optionally print upgrade starters."""
    try:
        result = run_doctor(handle=handle)
    except RepoRootNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    _echo_doctor_result(result, suggest_index_upgrade=suggest_index_upgrade, strict=strict)


if __name__ == "__main__":
    app()
