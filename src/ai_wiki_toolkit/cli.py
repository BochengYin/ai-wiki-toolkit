"""CLI for ai-wiki-toolkit."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

from ai_wiki_toolkit import __version__
from ai_wiki_toolkit.consolidation import (
    DEFAULT_CONSOLIDATION_MAX_ITEMS,
    generate_consolidation_queue,
)
from ai_wiki_toolkit.diagnostics import (
    DEFAULT_DIAGNOSTICS_MAX_ITEMS,
    DEFAULT_HIGH_ROI_MIN_EVENTS,
    DEFAULT_NOISY_MIN_EVENTS,
    DIAGNOSTIC_FOCUSES,
    generate_memory_diagnostics,
)
from ai_wiki_toolkit.doctor import run_doctor
from ai_wiki_toolkit.impact_eval import (
    generate_impact_eval_report,
    generate_impact_eval_summary,
    load_impact_eval_run_dirs_from_file,
    render_impact_eval_report,
    render_impact_eval_report_json,
    render_impact_eval_summary,
    render_impact_eval_summary_json,
)
from ai_wiki_toolkit.paths import (
    RepoRootNotFoundError,
    build_paths,
    resolve_user_handle,
    resolve_user_handle_candidate,
    usable_user_handle,
)
from ai_wiki_toolkit.route import (
    DEFAULT_ROUTE_SAFETY_CAP_WORDS,
    generate_route_packet,
    render_route_packet_json,
    render_route_packet_text,
)
from ai_wiki_toolkit.reuse_events import (
    EVIDENCE_MODES,
    RETRIEVAL_MODES,
    REUSE_CHECK_OUTCOMES,
    REUSE_OUTCOMES,
    RepoWikiNotInitializedError,
    record_reuse_check,
    record_reuse_event,
)
from ai_wiki_toolkit.scaffold import (
    refresh_managed_metrics,
    install_workspace,
    uninstall_workspace,
)
from ai_wiki_toolkit.work_ledger import (
    WORK_ITEM_TYPES,
    WORK_STATUSES,
    build_work_state,
    filter_work_items,
    record_work_event,
    refresh_work_report,
    render_work_items_report,
)

app = typer.Typer(help="Initialize and maintain ai-wiki-toolkit scaffolds.")
work_app = typer.Typer(help="Record and report AI wiki work ledger state.")
diagnose_app = typer.Typer(help="Generate AI wiki diagnostic reports.")
consolidate_app = typer.Typer(help="Generate AI wiki draft consolidation queues.")
eval_app = typer.Typer(help="Report AI wiki impact eval results.")
impact_eval_app = typer.Typer(help="Summarize first-attempt impact eval metrics.")
app.add_typer(work_app, name="work")
app.add_typer(diagnose_app, name="diagnose")
app.add_typer(consolidate_app, name="consolidate")
app.add_typer(eval_app, name="eval")
eval_app.add_typer(impact_eval_app, name="impact")

PROMPTED_IDENTITY_SOURCE = "prompted-handle"


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
    typer.echo(f"Updated ignore files: {len(result.updated_ignore_files)}")
    typer.echo(f"Updated managed files: {len(result.updated_managed_files)}")
    typer.echo(f"Updated skill files: {len(result.updated_skill_files)}")
    typer.echo(f"Updated prompt files: {len(result.updated_prompt_files)}")
    typer.echo(
        "Recommendation: configure git user.name and git user.email for stable handle resolution."
    )
    for path in result.updated_skill_files:
        typer.echo(f"Updated skill file: {path}")


def _can_prompt_for_team_id() -> bool:
    return sys.stdin.isatty()


def _prompt_for_team_id() -> str:
    typer.echo("Could not detect a git user.name or user.email.")
    typer.echo("")
    typer.echo("AI wiki needs a stable local ID for your team identity.")
    while True:
        value = typer.prompt(
            "What ID would you prefer to use in this team?",
            default="",
            show_default=False,
            prompt_suffix=" ",
        )
        handle = usable_user_handle(value)
        if handle:
            typer.echo("")
            typer.echo(f"Using AI wiki ID: {handle}")
            typer.echo("")
            typer.echo(
                "This ID will be stored in .env.aiwiki and used for "
                f"ai-wiki/people/{handle}/. AI wiki workflows can also use it as "
                "your branch-name component."
            )
            return handle
        typer.echo(
            "Please enter a team ID, for example: alice, alice-reviewer, or byin."
        )


def _resolve_install_handle(handle: str | None) -> tuple[str | None, str | None]:
    paths = build_paths()
    resolved = resolve_user_handle_candidate(paths.repo_root, explicit_handle=handle)
    if resolved:
        if resolved.source == "explicit-handle":
            return handle, None
        return None, None

    if not _can_prompt_for_team_id():
        typer.echo(
            "Could not detect an AI wiki ID and this shell is non-interactive.\n"
            "Run `aiwiki-toolkit install --handle your-name` or set "
            "`AIWIKI_TOOLKIT_HANDLE`.",
            err=True,
        )
        raise typer.Exit(code=1)

    prompted_handle = _prompt_for_team_id()
    return prompted_handle, PROMPTED_IDENTITY_SOURCE


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
        if any(f.path == ".gitignore" for f in actionable_findings):
            typer.echo(f"{step}. Run `aiwiki-toolkit install` to refresh the managed `.gitignore` block if needed.")
            step += 1
        tracked_telemetry = next(
            (f for f in actionable_findings if f.code == "tracked_telemetry_in_git_index"),
            None,
        )
        if tracked_telemetry and tracked_telemetry.suggested_fix:
            typer.echo(f"{step}. Untrack legacy local-state paths once:")
            typer.echo(f"   {tracked_telemetry.suggested_fix}")
            step += 1
        if any(f.path.startswith("ai-wiki/") and not f.path.startswith("ai-wiki/_toolkit/") for f in actionable_findings):
            if suggest_index_upgrade:
                typer.echo(
                    f"{step}. Review the suggested starter updates below and copy or merge them into the listed paths."
                )
            else:
                typer.echo(
                    f"{step}. Re-run with `aiwiki-toolkit doctor --suggest-index-upgrade` to print the latest starter content for the affected repo docs."
                )
            step += 1
        if any(f.path in {"AGENT.md", "AGENTS.md", "CLAUDE.md"} for f in actionable_findings):
            typer.echo(f"{step}. Re-run `aiwiki-toolkit install` if you need the managed prompt block refreshed.")

    if suggest_index_upgrade and result.suggestions:
        typer.echo("")
        typer.echo("Suggested starter updates:")
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


@app.command("route")
def route(
    task: str | None = typer.Option(
        None,
        "--task",
        help="Current task request. Agents should pass the user's task text here.",
    ),
    task_file: Path | None = typer.Option(
        None,
        "--task-file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Read the current task request from a file instead of --task.",
    ),
    task_id: str | None = typer.Option(
        None,
        "--task-id",
        help="Optional stable task id. Defaults to a slug derived from --task.",
    ),
    changed_paths: list[str] | None = typer.Option(
        None,
        "--changed-path",
        help="Optional path signal. Repeat to add multiple paths. Defaults to git status paths.",
    ),
    budget_words: int = typer.Option(
        DEFAULT_ROUTE_SAFETY_CAP_WORDS,
        "--budget-words",
        min=100,
        help="Safety cap for rendered packet words. Route may use less.",
    ),
    max_docs: int = typer.Option(
        6,
        "--max-docs",
        min=1,
        max=20,
        help="Maximum number of must-load documents to include.",
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        help="Output format. Choices: text, json.",
    ),
) -> None:
    """Generate a task-aware AI wiki context packet."""
    if task and task_file:
        typer.echo("Use either --task or --task-file, not both.", err=True)
        raise typer.Exit(code=1)

    task_text = task
    if task_file:
        task_text = task_file.read_text(encoding="utf-8")

    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)

    try:
        result = generate_route_packet(
            task=task_text,
            task_id=task_id,
            changed_paths=changed_paths or [],
            budget_words=budget_words,
            max_docs=max_docs,
        )
    except RepoRootNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except RepoWikiNotInitializedError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except json.JSONDecodeError as exc:
        typer.echo(f"Could not read AI wiki routing data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if normalized_format == "json":
        typer.echo(render_route_packet_json(result.packet), nl=False)
    else:
        typer.echo(render_route_packet_text(result.packet), nl=False)


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
        install_handle, identity_source = _resolve_install_handle(handle)
        result = install_workspace(
            handle=install_handle,
            identity_source=identity_source,
        )
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
    typer.echo(f"Updated ignore files: {len(result.updated_ignore_files)}")
    typer.echo(f"Deleted ignore files: {len(result.deleted_ignore_files)}")
    typer.echo(f"Updated prompt files: {len(result.updated_prompt_files)}")
    typer.echo(f"Deleted prompt files: {len(result.deleted_prompt_files)}")
    typer.echo(f"Removed opencode key: {'yes' if result.removed_opencode_key else 'no'}")
    if purge_user_docs:
        typer.echo("Shared home wiki preserved: yes")


@app.command("refresh-metrics")
def refresh_metrics() -> None:
    """Regenerate managed repo catalog, metrics, and work views from user-owned AI wiki state."""
    try:
        result = refresh_managed_metrics()
    except RepoRootNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except RepoWikiNotInitializedError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Repo wiki: {result.paths.repo_wiki_dir}")
    typer.echo(f"Refreshed files: {len(result.refreshed_files)}")
    for path in result.refreshed_files:
        typer.echo(f"Refreshed file: {path}")


@diagnose_app.command("memory")
def diagnose_memory(
    handle: str | None = typer.Option(
        None,
        "--handle",
        help="Optional author handle filter for local evidence logs.",
    ),
    since: str | None = typer.Option(
        None,
        "--since",
        help="Optional ISO timestamp or duration such as 14d.",
    ),
    focus: str = typer.Option(
        "all",
        "--focus",
        help="Diagnostics focus. Choices: all, trial-error.",
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        help="Output format. Choices: text, json.",
    ),
    write: bool = typer.Option(
        True,
        "--write/--no-write",
        help="Write generated reports under ai-wiki/_toolkit/diagnostics/.",
    ),
    max_items: int = typer.Option(
        DEFAULT_DIAGNOSTICS_MAX_ITEMS,
        "--max-items",
        min=1,
        help="Maximum items per diagnostics section.",
    ),
    high_roi_min_events: int = typer.Option(
        DEFAULT_HIGH_ROI_MIN_EVENTS,
        "--high-roi-min-events",
        min=1,
        help="Resolved reuse event threshold for high-ROI memory.",
    ),
    noisy_min_events: int = typer.Option(
        DEFAULT_NOISY_MIN_EVENTS,
        "--noisy-min-events",
        min=1,
        help="Total event threshold for noisy memory candidates.",
    ),
) -> None:
    """Diagnose AI wiki memory quality from local reuse and task-check evidence."""
    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)
    normalized_focus = focus.strip().lower()
    if normalized_focus not in DIAGNOSTIC_FOCUSES:
        typer.echo("Invalid --focus. Expected one of: all, trial-error.", err=True)
        raise typer.Exit(code=1)

    try:
        paths = build_paths()
        if not paths.repo_wiki_dir.exists():
            raise RepoWikiNotInitializedError(
                "Repo AI wiki is not initialized. Run `aiwiki-toolkit install` first."
            )
        result = generate_memory_diagnostics(
            paths.repo_wiki_dir,
            handle=handle,
            since=since,
            focus=normalized_focus,
            max_items=max_items,
            high_roi_min_events=high_roi_min_events,
            noisy_min_events=noisy_min_events,
            write=write,
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
    except json.JSONDecodeError as exc:
        typer.echo(f"Could not read AI wiki diagnostics data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if normalized_format == "json":
        typer.echo(result.json_text, nl=False)
    else:
        typer.echo(result.markdown, nl=False)


@consolidate_app.command("queue")
def consolidate_queue(
    handle: str | None = typer.Option(
        None,
        "--handle",
        help="Optional author handle whose people/<handle>/drafts/ queue should be reviewed.",
    ),
    since: str | None = typer.Option(
        None,
        "--since",
        help="Optional ISO timestamp or duration such as 14d for diagnostics evidence.",
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        help="Output format. Choices: text, json.",
    ),
    write: bool = typer.Option(
        True,
        "--write/--no-write",
        help="Write generated reports under ai-wiki/_toolkit/consolidation/.",
    ),
    max_items: int = typer.Option(
        DEFAULT_CONSOLIDATION_MAX_ITEMS,
        "--max-items",
        min=1,
        help="Maximum draft clusters in the queue.",
    ),
    high_roi_min_events: int = typer.Option(
        DEFAULT_HIGH_ROI_MIN_EVENTS,
        "--high-roi-min-events",
        min=1,
        help="Resolved reuse event threshold for high-ROI memory signals.",
    ),
    noisy_min_events: int = typer.Option(
        DEFAULT_NOISY_MIN_EVENTS,
        "--noisy-min-events",
        min=1,
        help="Total event threshold for noisy memory signals.",
    ),
) -> None:
    """Generate a human-reviewable draft consolidation and promotion queue."""
    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)

    try:
        paths = build_paths()
        if not paths.repo_wiki_dir.exists():
            raise RepoWikiNotInitializedError(
                "Repo AI wiki is not initialized. Run `aiwiki-toolkit install` first."
            )
        resolved_handle = resolve_user_handle(paths.repo_root, explicit_handle=handle)
        result = generate_consolidation_queue(
            paths.repo_wiki_dir,
            handle=resolved_handle,
            since=since,
            max_items=max_items,
            high_roi_min_events=high_roi_min_events,
            noisy_min_events=noisy_min_events,
            write=write,
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
    except json.JSONDecodeError as exc:
        typer.echo(f"Could not read AI wiki consolidation data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if normalized_format == "json":
        typer.echo(result.json_text, nl=False)
    else:
        typer.echo(result.markdown, nl=False)


@impact_eval_app.command("report")
def eval_impact_report(
    run_dir: Path = typer.Option(
        ...,
        "--run-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Impact eval run directory containing metadata.json and captured result artifacts.",
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        help="Output format. Choices: text, json.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        help="Optional output file. Defaults to stdout only.",
    ),
) -> None:
    """Summarize first-attempt impact eval metrics from a captured run."""
    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)

    try:
        report = generate_impact_eval_report(run_dir)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except json.JSONDecodeError as exc:
        typer.echo(f"Could not read impact eval data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    rendered = (
        render_impact_eval_report_json(report)
        if normalized_format == "json"
        else render_impact_eval_report(report)
    )
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        typer.echo(str(output))
    else:
        typer.echo(rendered, nl=False)


@impact_eval_app.command("summarize")
def eval_impact_summarize(
    run_dirs: list[Path] | None = typer.Option(
        None,
        "--run-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Impact eval run directory. Repeat to summarize multiple runs.",
    ),
    runs_file: Path | None = typer.Option(
        None,
        "--runs-file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="JSON file containing run directories as a list, `run_dirs`, or `runs[].run_dir`.",
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        help="Output format. Choices: text, json.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        help="Optional output file. Defaults to stdout only.",
    ),
) -> None:
    """Summarize product-level impact across multiple captured eval runs."""
    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)

    selected_run_dirs: list[Path] = list(run_dirs or [])
    try:
        if runs_file is not None:
            selected_run_dirs.extend(load_impact_eval_run_dirs_from_file(runs_file))
        if not selected_run_dirs:
            typer.echo("Provide at least one --run-dir or --runs-file.", err=True)
            raise typer.Exit(code=1)
        summary = generate_impact_eval_summary(tuple(selected_run_dirs))
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except json.JSONDecodeError as exc:
        typer.echo(f"Could not read impact eval data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    rendered = (
        render_impact_eval_summary_json(summary)
        if normalized_format == "json"
        else render_impact_eval_summary(summary)
    )
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        typer.echo(str(output))
    else:
        typer.echo(rendered, nl=False)


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
    handle: str | None = typer.Option(
        None,
        "--handle",
        help="Optional override for the handle shard used under ai-wiki/metrics/.",
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
            handle=handle,
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
    typer.echo(f"Author handle: {result.author_handle}")
    typer.echo(f"Event log: {result.event_log_path}")
    typer.echo(f"Document stats: {result.document_stats_path}")
    typer.echo(f"Task stats: {result.task_stats_path}")


@app.command("record-reuse-check")
def record_reuse_check_command(
    task_id: str = typer.Option(
        ...,
        "--task-id",
        help="Stable task identifier for the completed task that was checked for AI wiki reuse.",
    ),
    check_outcome: str = typer.Option(
        ...,
        "--check-outcome",
        help=f"Whether the task used AI wiki docs. Choices: {', '.join(REUSE_CHECK_OUTCOMES)}.",
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
        help="Optional free-form note describing the reuse check outcome.",
    ),
    checked_at: str | None = typer.Option(
        None,
        "--checked-at",
        help="Optional explicit timestamp. Defaults to the current local time in ISO-8601 format.",
    ),
    handle: str | None = typer.Option(
        None,
        "--handle",
        help="Optional override for the handle shard used under ai-wiki/metrics/.",
    ),
) -> None:
    """Append one task-level reuse check and refresh managed metric aggregates."""
    try:
        result = record_reuse_check(
            task_id=task_id,
            check_outcome=check_outcome,
            agent_name=agent_name,
            model=model,
            notes=notes,
            checked_at=checked_at,
            handle=handle,
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

    typer.echo(f"Recorded reuse check: {result.check_id}")
    typer.echo(f"Checked at: {result.checked_at}")
    typer.echo(f"Author handle: {result.author_handle}")
    typer.echo(f"Check log: {result.check_log_path}")
    typer.echo(f"Document stats: {result.document_stats_path}")
    typer.echo(f"Task stats: {result.task_stats_path}")


@work_app.command("capture")
def work_capture(
    work_id: str = typer.Option(
        ...,
        "--work-id",
        "--task-id",
        help="Stable work item id. --task-id is accepted as an alias for task items.",
    ),
    title: str = typer.Option(
        ...,
        "--title",
        help="Human-readable work item title.",
    ),
    item_type: str = typer.Option(
        "task",
        "--item-type",
        help=f"Work item type. Choices: {', '.join(WORK_ITEM_TYPES)}.",
    ),
    status: str | None = typer.Option(
        None,
        "--status",
        help=f"Initial status. Choices: {', '.join(WORK_STATUSES)}.",
    ),
    epic_id: str | None = typer.Option(
        None,
        "--epic-id",
        help="Optional parent epic id for task items.",
    ),
    source: str | None = typer.Option(
        "conversation",
        "--source",
        help="Where this work item came from, such as conversation, issue, pr, or roadmap.",
    ),
    links: list[str] | None = typer.Option(
        None,
        "--link",
        help="Repeatable related path or URL that route can later cite as work context.",
    ),
    reporter_handle: str | None = typer.Option(
        None,
        "--reporter",
        help="Optional reporter handle. Defaults to the current local AI wiki actor.",
    ),
    assignee_handles: list[str] | None = typer.Option(
        None,
        "--assignee",
        help="Repeatable assignee handle. Defaults to the current local AI wiki actor.",
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
        help="Optional free-form work note.",
    ),
    occurred_at: str | None = typer.Option(
        None,
        "--occurred-at",
        help="Optional explicit timestamp. Defaults to the current local time in ISO-8601 format.",
    ),
    handle: str | None = typer.Option(
        None,
        "--handle",
        help="Optional override for the handle shard used under ai-wiki/work/events/.",
    ),
) -> None:
    """Capture a task or epic in the append-only AI wiki work ledger."""
    try:
        result = record_work_event(
            event_type="captured",
            item_type=item_type,
            work_id=work_id,
            status=status,
            title=title,
            epic_id=epic_id,
            source=source,
            links=links or [],
            reporter_handle=reporter_handle,
            assignee_handles=assignee_handles or [],
            agent_name=agent_name,
            model=model,
            notes=notes,
            occurred_at=occurred_at,
            handle=handle,
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

    typer.echo(f"Recorded work event: {result.event_id}")
    typer.echo(f"Occurred at: {result.occurred_at}")
    typer.echo(f"Author handle: {result.author_handle}")
    typer.echo(f"Event log: {result.event_log_path}")
    typer.echo(f"Work state: {result.state_path}")
    typer.echo(f"Work report: {result.report_path}")


@work_app.command("status")
def work_status(
    work_id: str = typer.Option(
        ...,
        "--work-id",
        "--task-id",
        help="Stable work item id. --task-id is accepted as an alias for task items.",
    ),
    status: str = typer.Option(
        ...,
        "--status",
        help=f"New status. Choices: {', '.join(WORK_STATUSES)}.",
    ),
    item_type: str = typer.Option(
        "task",
        "--item-type",
        help=f"Work item type. Choices: {', '.join(WORK_ITEM_TYPES)}.",
    ),
    title: str | None = typer.Option(
        None,
        "--title",
        help="Optional title update to store with the status event.",
    ),
    epic_id: str | None = typer.Option(
        None,
        "--epic-id",
        help="Optional parent epic id for task items.",
    ),
    source: str | None = typer.Option(
        None,
        "--source",
        help="Optional source update for the status event.",
    ),
    links: list[str] | None = typer.Option(
        None,
        "--link",
        help="Repeatable related path or URL.",
    ),
    reporter_handle: str | None = typer.Option(
        None,
        "--reporter",
        help="Optional reporter handle update.",
    ),
    assignee_handles: list[str] | None = typer.Option(
        None,
        "--assignee",
        help="Repeatable assignee handle update.",
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
        help="Optional free-form work note.",
    ),
    occurred_at: str | None = typer.Option(
        None,
        "--occurred-at",
        help="Optional explicit timestamp. Defaults to the current local time in ISO-8601 format.",
    ),
    handle: str | None = typer.Option(
        None,
        "--handle",
        help="Optional override for the handle shard used under ai-wiki/work/events/.",
    ),
) -> None:
    """Append a status transition to the AI wiki work ledger."""
    try:
        result = record_work_event(
            event_type="status_changed",
            item_type=item_type,
            work_id=work_id,
            status=status,
            title=title,
            epic_id=epic_id,
            source=source,
            links=links or [],
            reporter_handle=reporter_handle,
            assignee_handles=assignee_handles or [],
            agent_name=agent_name,
            model=model,
            notes=notes,
            occurred_at=occurred_at,
            handle=handle,
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

    typer.echo(f"Recorded work event: {result.event_id}")
    typer.echo(f"Occurred at: {result.occurred_at}")
    typer.echo(f"Author handle: {result.author_handle}")
    typer.echo(f"Event log: {result.event_log_path}")
    typer.echo(f"Work state: {result.state_path}")
    typer.echo(f"Work report: {result.report_path}")


@work_app.command("report")
def work_report() -> None:
    """Regenerate AI wiki work ledger managed views."""
    try:
        result = refresh_work_report()
    except RepoRootNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except RepoWikiNotInitializedError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Work state: {result.state_path}")
    typer.echo(f"Work report: {result.report_path}")


@work_app.command("mine")
def work_mine(
    include_closed: bool = typer.Option(
        False,
        "--include-closed",
        help="Include done, archived, and dropped tasks.",
    ),
    statuses: list[str] | None = typer.Option(
        None,
        "--status",
        help=f"Repeatable status filter. Choices: {', '.join(WORK_STATUSES)}.",
    ),
    handle: str | None = typer.Option(
        None,
        "--handle",
        help="Optional actor handle override. Defaults to the current local AI wiki actor.",
    ),
) -> None:
    """Print open tasks assigned to the current local AI wiki actor."""
    try:
        paths = build_paths()
        if not paths.repo_wiki_dir.exists():
            raise RepoWikiNotInitializedError(
                "Repo AI wiki is not initialized. Run `aiwiki-toolkit install` first."
            )
        actor_handle = resolve_user_handle(paths.repo_root, explicit_handle=handle)
        state = build_work_state(paths.repo_wiki_dir)
        items = filter_work_items(
            state,
            assignee_handle=actor_handle,
            statuses=statuses or None,
            include_closed=include_closed,
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

    typer.echo(render_work_items_report(f"My Work: {actor_handle}", items), nl=False)


@work_app.command("list")
def work_list(
    assignee_handle: str | None = typer.Option(
        None,
        "--assignee",
        help="Filter tasks by assignee handle.",
    ),
    reporter_handle: str | None = typer.Option(
        None,
        "--reporter",
        help="Filter tasks by reporter handle.",
    ),
    include_closed: bool = typer.Option(
        False,
        "--include-closed",
        help="Include done, archived, and dropped tasks.",
    ),
    statuses: list[str] | None = typer.Option(
        None,
        "--status",
        help=f"Repeatable status filter. Choices: {', '.join(WORK_STATUSES)}.",
    ),
) -> None:
    """Print tasks from the central AI wiki work ledger."""
    try:
        paths = build_paths()
        if not paths.repo_wiki_dir.exists():
            raise RepoWikiNotInitializedError(
                "Repo AI wiki is not initialized. Run `aiwiki-toolkit install` first."
            )
        state = build_work_state(paths.repo_wiki_dir)
        items = filter_work_items(
            state,
            assignee_handle=assignee_handle,
            reporter_handle=reporter_handle,
            statuses=statuses or None,
            include_closed=include_closed,
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

    title_parts = ["Work"]
    if assignee_handle:
        title_parts.append(f"assignee={assignee_handle}")
    if reporter_handle:
        title_parts.append(f"reporter={reporter_handle}")
    typer.echo(render_work_items_report(" ".join(title_parts), items), nl=False)


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
    """Diagnose AI wiki navigation and rule drift and optionally print starter updates."""
    try:
        result = run_doctor(handle=handle)
    except RepoRootNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    _echo_doctor_result(result, suggest_index_upgrade=suggest_index_upgrade, strict=strict)


if __name__ == "__main__":
    app()
