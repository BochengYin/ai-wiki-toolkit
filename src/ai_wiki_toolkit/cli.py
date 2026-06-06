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
from ai_wiki_toolkit.impact_analysis import (
    generate_neutral_impact_eval_report,
    generate_route_cohort_report,
    generate_route_noise_report,
    generate_route_replay_report,
    render_neutral_impact_eval_report,
    render_neutral_impact_eval_report_json,
    render_route_cohort_report,
    render_route_cohort_report_json,
    render_route_noise_report,
    render_route_noise_report_json,
    render_route_replay_report,
    render_route_replay_report_json,
)
from ai_wiki_toolkit.impact_eval import (
    DEFAULT_PLAN_MODEL,
    DEFAULT_PLAN_PROMPT_LEVELS,
    DEFAULT_PLAN_REASONING_EFFORT,
    DEFAULT_RUN_SCORE_POLICY,
    DEFAULT_RUN_LABEL,
    DEFAULT_SOURCE_MODE,
    RUN_SCORE_POLICIES,
    SCORE_LABELS,
    backfill_historical_impact_eval_run_index,
    capture_impact_eval_result,
    draft_impact_eval_family_candidate,
    discover_impact_eval_families,
    discover_impact_eval_family_candidates,
    generate_impact_eval_manifest,
    generate_impact_eval_report,
    generate_impact_eval_schedule_report,
    generate_impact_eval_run_plan,
    generate_impact_eval_summary,
    init_impact_eval_family_from_candidate,
    load_impact_eval_run_dirs_from_file,
    prepare_impact_eval_run,
    render_impact_eval_benchmark_result,
    render_impact_eval_benchmark_result_json,
    render_impact_eval_candidate_draft_result,
    render_impact_eval_candidate_draft_result_json,
    render_impact_eval_candidate_promotion_result,
    render_impact_eval_candidate_promotion_result_json,
    render_impact_eval_candidate_queue,
    render_impact_eval_candidate_queue_json,
    render_impact_eval_capture_result,
    render_impact_eval_capture_result_json,
    render_impact_eval_families,
    render_impact_eval_families_json,
    render_impact_eval_family_candidates,
    render_impact_eval_family_candidates_json,
    render_impact_eval_family_detail,
    render_impact_eval_family_detail_json,
    render_impact_eval_family_init_result,
    render_impact_eval_family_init_result_json,
    render_impact_eval_history_backfill_result,
    render_impact_eval_history_backfill_result_json,
    render_impact_eval_manifest,
    render_impact_eval_manifest_json,
    render_impact_eval_prepare_result,
    render_impact_eval_prepare_result_json,
    render_impact_eval_report,
    render_impact_eval_report_json,
    render_impact_eval_run_plan,
    render_impact_eval_run_plan_json,
    render_impact_eval_run_result,
    render_impact_eval_run_result_json,
    render_impact_eval_schedule_report,
    render_impact_eval_schedule_report_json,
    render_impact_eval_schedule_run_result,
    render_impact_eval_schedule_run_result_json,
    render_impact_eval_score_result,
    render_impact_eval_score_result_json,
    render_impact_eval_summary,
    render_impact_eval_summary_json,
    render_impact_eval_validate_result,
    render_impact_eval_validate_result_json,
    run_impact_eval_benchmark,
    run_impact_eval_schedule,
    run_impact_eval,
    score_impact_eval_result,
    show_impact_eval_family,
    promote_impact_eval_family_candidate,
    refresh_impact_eval_candidate_queue,
    validate_impact_eval_run,
)
from ai_wiki_toolkit.paths import (
    RepoRootNotFoundError,
    build_paths,
    resolve_user_handle,
    resolve_user_handle_candidate,
    usable_user_handle,
)
from ai_wiki_toolkit.project_a import (
    generate_project_a_diagnostics,
    render_project_a_diagnostics,
    render_project_a_diagnostics_json,
)
from ai_wiki_toolkit.route import (
    DEFAULT_ROUTE_RERANK_TOP,
    DEFAULT_ROUTE_SAFETY_CAP_WORDS,
    generate_route_packet,
    render_route_packet_json,
    render_route_packet_text,
)
from ai_wiki_toolkit.repo_evaluation import (
    DEFAULT_REPO_EVALUATION_MAX_ITEMS,
    DEFAULT_REPO_EVALUATION_SINCE,
    generate_repo_evaluation,
)
from ai_wiki_toolkit.route_traces import record_route_trace
from ai_wiki_toolkit.source_incidents import (
    SOURCE_INCIDENT_TIMING_SOURCES,
    backfill_writeback_source_incidents,
    capture_post_turn_source_incidents,
    render_source_incident_backfill_json,
    render_source_incident_backfill_text,
)
from ai_wiki_toolkit.reuse_events import (
    EVIDENCE_MODES,
    NOT_HELPFUL_REASONS,
    RETRIEVAL_MODES,
    REUSE_CHECK_OUTCOMES,
    REUSE_OUTCOMES,
    SIGNAL_STATUSES,
    RepoWikiNotInitializedError,
    record_reuse_check,
    record_reuse_event,
)
from ai_wiki_toolkit.promotion import (
    DEFAULT_RESOLVED_TASK_THRESHOLD,
    generate_promotion_candidates,
)
from ai_wiki_toolkit.scaffold import (
    refresh_managed_metrics,
    install_workspace,
    uninstall_workspace,
)
from ai_wiki_toolkit.usefulness import generate_usefulness_report
from ai_wiki_toolkit.weekly_report import generate_weekly_report
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
evaluate_app = typer.Typer(help="Generate AI wiki repo evaluation reports.")
eval_app = typer.Typer(help="Report AI wiki impact eval results.")
impact_eval_app = typer.Typer(help="Inspect and summarize impact eval artifacts.")
impact_eval_family_app = typer.Typer(help="Discover and scaffold impact eval families.")
impact_eval_neutral_app = typer.Typer(help="Analyze neutral impact eval family runs.")
impact_eval_project_a_app = typer.Typer(help="Report Project A coding-agent eval harness health.")
impact_eval_route_noise_app = typer.Typer(help="Analyze route precision and noise for eval work.")
impact_eval_schedule_app = typer.Typer(help="Run and report scheduled impact eval loops.")
promote_app = typer.Typer(help="Mark handle-local promotion candidates from useful reuse evidence.")
report_app = typer.Typer(help="Generate AI wiki local reports.")
source_incident_app = typer.Typer(help="Backfill and inspect source incident timing evidence.")
app.add_typer(work_app, name="work")
app.add_typer(diagnose_app, name="diagnose")
app.add_typer(consolidate_app, name="consolidate")
app.add_typer(evaluate_app, name="evaluate")
app.add_typer(eval_app, name="eval")
app.add_typer(promote_app, name="promote")
app.add_typer(report_app, name="report")
app.add_typer(source_incident_app, name="source-incident")
eval_app.add_typer(impact_eval_app, name="impact")
impact_eval_app.add_typer(impact_eval_family_app, name="family")
impact_eval_app.add_typer(impact_eval_neutral_app, name="neutral")
impact_eval_app.add_typer(impact_eval_project_a_app, name="project-a")
impact_eval_app.add_typer(impact_eval_route_noise_app, name="route-noise")
impact_eval_app.add_typer(impact_eval_schedule_app, name="schedule")

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
    typer.echo(
        "Recommendation: if your agent runner supports post-turn hooks, configure it to run "
        "`aiwiki-toolkit source-incident capture-post-turn --apply`."
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
        help=(
            "Optional path signal. Repeat to add multiple paths. Explicit paths always influence "
            "routing; git status paths are displayed and only influence generic tasks."
        ),
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
    rerank_top: int = typer.Option(
        DEFAULT_ROUTE_RERANK_TOP,
        "--rerank-top",
        min=0,
        max=100,
        help="Number of top deterministic index cards to rerank after initial scoring. Use 0 to disable.",
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        help="Output format. Choices: text, json.",
    ),
    record_trace: bool = typer.Option(
        True,
        "--record-trace/--no-record-trace",
        help="Append a local route-trace telemetry event under ai-wiki/metrics/route-traces/.",
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
            rerank_top=rerank_top,
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

    text_packet = render_route_packet_text(result.packet)
    rendered_output = render_route_packet_json(result.packet) if normalized_format == "json" else text_packet
    if record_trace:
        record_route_trace(packet=result.packet, rendered_packet=text_packet)
    typer.echo(rendered_output, nl=False)


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
        help="Diagnostics focus. Choices: all, route, trial-error.",
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
        typer.echo("Invalid --focus. Expected one of: all, route, trial-error.", err=True)
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


@source_incident_app.command("backfill-writeback")
def source_incident_backfill_writeback(
    doc_ids: list[str] | None = typer.Option(
        None,
        "--doc-id",
        help="Optional target doc_id. Repeat to backfill only selected memories.",
    ),
    writeback_paths: list[str] | None = typer.Option(
        None,
        "--writeback-path",
        help="Optional AI wiki write-back path. Repeat to backfill only selected paths.",
    ),
    sessions_root: Path = typer.Option(
        Path.home() / ".codex" / "sessions",
        "--sessions-root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Codex sessions root to scan for first write-back footers.",
    ),
    apply: bool = typer.Option(
        False,
        "--apply/--dry-run",
        help="Append new source incident evidence. Default is a report-only dry run.",
    ),
    include_aborted: bool = typer.Option(
        True,
        "--include-aborted/--exclude-aborted",
        help="Include timed turn_aborted rows before the first write-back cutoff.",
    ),
    max_items: int | None = typer.Option(
        None,
        "--max-items",
        min=1,
        help="Maximum first-writeback candidates to report or write.",
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        help="Output format. Choices: text, json.",
    ),
    handle: str | None = typer.Option(
        None,
        "--handle",
        help="Optional override for the handle shard used under ai-wiki/metrics/.",
    ),
) -> None:
    """Backfill source incident timing from first AI Wiki write-back footers."""
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
        result = backfill_writeback_source_incidents(
            repo_wiki_dir=paths.repo_wiki_dir,
            sessions_root=sessions_root,
            author_handle=resolved_handle,
            repo_root=paths.repo_root,
            doc_ids=doc_ids or [],
            writeback_paths=writeback_paths or [],
            apply=apply,
            include_aborted=include_aborted,
            max_items=max_items,
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

    if normalized_format == "json":
        typer.echo(render_source_incident_backfill_json(result), nl=False)
    else:
        typer.echo(render_source_incident_backfill_text(result), nl=False)


@source_incident_app.command("capture-post-turn")
def source_incident_capture_post_turn(
    session_id: str | None = typer.Option(
        None,
        "--session-id",
        help="Optional Codex session id. Defaults to the latest write-back session for this repo.",
    ),
    doc_ids: list[str] | None = typer.Option(
        None,
        "--doc-id",
        help="Optional target doc_id. Repeat to capture only selected memories.",
    ),
    writeback_paths: list[str] | None = typer.Option(
        None,
        "--writeback-path",
        help="Optional AI wiki write-back path. Repeat to capture only selected paths.",
    ),
    sessions_root: Path = typer.Option(
        Path.home() / ".codex" / "sessions",
        "--sessions-root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Codex sessions root to scan for completed write-back turns.",
    ),
    apply: bool = typer.Option(
        False,
        "--apply/--dry-run",
        help="Append new source incident evidence. Default is a report-only dry run.",
    ),
    include_aborted: bool = typer.Option(
        True,
        "--include-aborted/--exclude-aborted",
        help="Include timed turn_aborted rows before the first write-back cutoff.",
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        help="Output format. Choices: text, json.",
    ),
    handle: str | None = typer.Option(
        None,
        "--handle",
        help="Optional override for the handle shard used under ai-wiki/metrics/.",
    ),
) -> None:
    """Capture source incident timing for the latest completed write-back turn."""
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
        result = capture_post_turn_source_incidents(
            repo_wiki_dir=paths.repo_wiki_dir,
            sessions_root=sessions_root,
            author_handle=resolved_handle,
            repo_root=paths.repo_root,
            session_id=session_id,
            doc_ids=doc_ids or [],
            writeback_paths=writeback_paths or [],
            apply=apply,
            include_aborted=include_aborted,
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

    if normalized_format == "json":
        typer.echo(render_source_incident_backfill_json(result), nl=False)
    else:
        typer.echo(render_source_incident_backfill_text(result), nl=False)


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


@evaluate_app.command("repo")
def evaluate_repo(
    repo_root: Path | None = typer.Option(
        None,
        "--repo-root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
        help="Repository root. Defaults to the current git repository.",
    ),
    wiki_dir: Path | None = typer.Option(
        None,
        "--wiki-dir",
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
        help="AI wiki directory. Defaults to <repo-root>/ai-wiki.",
    ),
    handle: str | None = typer.Option(
        None,
        "--handle",
        help="Optional author handle filter for local evidence logs.",
    ),
    since: str = typer.Option(
        DEFAULT_REPO_EVALUATION_SINCE,
        "--since",
        help="Optional ISO timestamp or duration such as 30d.",
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        help="Output format. Choices: text, json.",
    ),
    write: bool = typer.Option(
        True,
        "--write/--no-write",
        help="Write generated reports under ai-wiki/_toolkit/reports/repo-evaluation/.",
    ),
    max_items: int = typer.Option(
        DEFAULT_REPO_EVALUATION_MAX_ITEMS,
        "--max-items",
        min=1,
        help="Maximum items per repo evaluation section.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        help="Optional extra output path for the selected format.",
    ),
) -> None:
    """Generate a review-first repo evaluation and improvement advisor report."""
    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)
    if output is not None and not write:
        typer.echo("Use --output only when --write is enabled.", err=True)
        raise typer.Exit(code=1)

    try:
        paths = build_paths(repo_root)
        resolved_repo_root = paths.repo_root
        resolved_wiki_dir = wiki_dir.resolve() if wiki_dir is not None else paths.repo_wiki_dir
        if not resolved_wiki_dir.exists():
            raise RepoWikiNotInitializedError(
                "Repo AI wiki is not initialized. Run `aiwiki-toolkit install` first."
            )
        resolved_handle = resolve_user_handle(resolved_repo_root, explicit_handle=handle)
        result = generate_repo_evaluation(
            repo_root=resolved_repo_root,
            repo_wiki_dir=resolved_wiki_dir,
            handle=resolved_handle,
            since=since,
            max_items=max_items,
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
        typer.echo(f"Could not read AI wiki repo evaluation data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    rendered = result.json_text if normalized_format == "json" else result.markdown
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    typer.echo(rendered, nl=False)


@promote_app.command("candidates")
def promote_candidates(
    handle: str | None = typer.Option(
        None,
        "--handle",
        help="Draft owner handle whose people/<handle>/drafts/ evidence should be scanned.",
    ),
    since: str | None = typer.Option(
        None,
        "--since",
        help="Optional ISO timestamp or duration such as 14d for reuse evidence.",
    ),
    resolved_task_threshold: int = typer.Option(
        DEFAULT_RESOLVED_TASK_THRESHOLD,
        "--resolved-task-threshold",
        "--min-resolved-tasks",
        min=0,
        help="Require more than this many distinct resolved task IDs before auto-marking.",
    ),
    apply_changes: bool = typer.Option(
        False,
        "--apply/--no-apply",
        help="Mark qualifying drafts and refresh people/<handle>/index.md links.",
    ),
    update_index: bool = typer.Option(
        True,
        "--update-index/--no-update-index",
        help="When applying, refresh the stable Promotion Candidates section in people/<handle>/index.md.",
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        help="Output format. Choices: text, json.",
    ),
    write: bool = typer.Option(
        True,
        "--write/--no-write",
        help="Write generated reports under ai-wiki/_toolkit/reports/promotion-candidates/.",
    ),
) -> None:
    """Find useful reused drafts and optionally mark them as promotion candidates."""
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
        result = generate_promotion_candidates(
            paths.repo_wiki_dir,
            handle=resolved_handle,
            since=since,
            resolved_task_threshold=resolved_task_threshold,
            apply=apply_changes,
            update_index=update_index,
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
        typer.echo(f"Could not read AI wiki promotion data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if normalized_format == "json":
        typer.echo(result.json_text, nl=False)
    else:
        typer.echo(result.markdown, nl=False)


@report_app.command("usefulness")
def report_usefulness(
    handle: str | None = typer.Option(
        None,
        "--handle",
        help="Optional event author handle to filter local reuse evidence.",
    ),
    since: str | None = typer.Option(
        None,
        "--since",
        help="Optional ISO timestamp or duration such as 14d for reuse evidence.",
    ),
    until: str | None = typer.Option(
        None,
        "--until",
        help="Optional exclusive ISO timestamp upper bound for reuse evidence.",
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        help="Output format. Choices: text, json.",
    ),
    write: bool = typer.Option(
        True,
        "--write/--no-write",
        help="Write generated reports under ai-wiki/_toolkit/reports/usefulness/.",
    ),
) -> None:
    """Generate a local report of referenced files and estimated time impact."""
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
        result = generate_usefulness_report(
            paths.repo_wiki_dir,
            handle=handle,
            since=since,
            until=until,
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
        typer.echo(f"Could not read AI wiki report data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if normalized_format == "json":
        typer.echo(result.json_text, nl=False)
    else:
        typer.echo(result.markdown, nl=False)


@report_app.command("weekly")
def report_weekly(
    handle: str | None = typer.Option(
        None,
        "--handle",
        help="Optional actor handle. Defaults to the resolved local AI wiki handle.",
    ),
    if_due: bool = typer.Option(
        False,
        "--if-due",
        help="Skip generation when the current ISO week already has a report.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Generate even when --if-due would skip the current ISO week.",
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        help="Output format. Choices: text, json.",
    ),
    max_documents: int = typer.Option(
        30,
        "--max-documents",
        min=1,
        help="Maximum referenced documents to render in the HTML table.",
    ),
) -> None:
    """Generate a weekly local HTML report with last-run state."""
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
        result = generate_weekly_report(
            paths.repo_wiki_dir,
            handle=resolved_handle,
            if_due=if_due,
            force=force,
            max_documents=max_documents,
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
        typer.echo(f"Could not read AI wiki weekly report data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if normalized_format == "json":
        typer.echo(result.json_text, nl=False)
        return

    outputs = result.report["outputs"]
    if result.report["status"] == "skipped":
        typer.echo(f"Weekly report skipped: {result.report['reason']}")
    else:
        typer.echo("Weekly report generated.")
    typer.echo(f"HTML: {outputs.get('html') or outputs.get('latest_html')}")
    typer.echo(f"JSON: {outputs.get('json') or outputs.get('latest_json')}")
    typer.echo(f"State: {outputs['state']}")


@impact_eval_app.command("families")
def eval_impact_families(
    repo_root: Path | None = typer.Option(
        None,
        "--repo-root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Repository root containing evals/impact/. Defaults to the current repo.",
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
    """List registered impact eval families and their readiness."""
    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)

    try:
        result = discover_impact_eval_families(repo_root=repo_root)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except json.JSONDecodeError as exc:
        typer.echo(f"Could not read impact eval family data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    rendered = (
        render_impact_eval_families_json(result)
        if normalized_format == "json"
        else render_impact_eval_families(result)
    )
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        typer.echo(str(output))
    else:
        typer.echo(rendered, nl=False)


@impact_eval_app.command("discover")
def eval_impact_discover(
    repo_root: Path | None = typer.Option(
        None,
        "--repo-root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Repository root containing evals/impact/. Defaults to the current repo.",
    ),
    repo_wiki_dir: Path | None = typer.Option(
        None,
        "--repo-wiki-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="AI wiki directory to scan. Defaults to <repo-root>/ai-wiki.",
    ),
    handle: str | None = typer.Option(
        None,
        "--handle",
        help="Optional handle filter for local telemetry.",
    ),
    since: str | None = typer.Option(
        None,
        "--since",
        help="Optional ISO timestamp or duration such as 14d.",
    ),
    max_items: int = typer.Option(
        DEFAULT_DIAGNOSTICS_MAX_ITEMS,
        "--max-items",
        min=1,
        help="Maximum candidates to report.",
    ),
    include_not_ready: bool = typer.Option(
        True,
        "--include-not-ready/--ready-only",
        help="Include weaker observed signals in the managed queue.",
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
    """Refresh the managed impact eval candidate queue from trial/error evidence."""
    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)

    try:
        result = refresh_impact_eval_candidate_queue(
            repo_root=repo_root,
            repo_wiki_dir=repo_wiki_dir,
            handle=handle,
            since=since,
            max_items=max_items,
            include_not_ready=include_not_ready,
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except json.JSONDecodeError as exc:
        typer.echo(f"Could not read impact eval discovery data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    rendered = (
        render_impact_eval_candidate_queue_json(result)
        if normalized_format == "json"
        else render_impact_eval_candidate_queue(result)
    )
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        typer.echo(str(output))
    else:
        typer.echo(rendered, nl=False)


@impact_eval_family_app.command("show")
def eval_impact_family_show(
    family: str = typer.Argument(..., help="Impact eval family name."),
    repo_root: Path | None = typer.Option(
        None,
        "--repo-root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Repository root containing evals/impact/. Defaults to the current repo.",
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
    """Show one impact eval family's spec, prompts, rubric status, and next commands."""
    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)

    try:
        result = show_impact_eval_family(family=family, repo_root=repo_root)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except json.JSONDecodeError as exc:
        typer.echo(f"Could not read impact eval family data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    rendered = (
        render_impact_eval_family_detail_json(result)
        if normalized_format == "json"
        else render_impact_eval_family_detail(result)
    )
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        typer.echo(str(output))
    else:
        typer.echo(rendered, nl=False)


@impact_eval_family_app.command("candidates")
def eval_impact_family_candidates(
    repo_root: Path | None = typer.Option(
        None,
        "--repo-root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Repository root containing evals/impact/. Defaults to the current repo.",
    ),
    repo_wiki_dir: Path | None = typer.Option(
        None,
        "--repo-wiki-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="AI wiki directory to scan. Defaults to <repo-root>/ai-wiki.",
    ),
    handle: str | None = typer.Option(
        None,
        "--handle",
        help="Optional handle filter for local telemetry.",
    ),
    since: str | None = typer.Option(
        None,
        "--since",
        help="Optional ISO timestamp or duration such as 14d.",
    ),
    max_items: int = typer.Option(
        DEFAULT_DIAGNOSTICS_MAX_ITEMS,
        "--max-items",
        min=1,
        help="Maximum candidates to report.",
    ),
    include_not_ready: bool = typer.Option(
        False,
        "--include-not-ready",
        help="Include weaker missed/repeated issue signals that are not replay-ready.",
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
    """Discover trial/error memory signals that may become future eval families."""
    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)

    try:
        result = discover_impact_eval_family_candidates(
            repo_root=repo_root,
            repo_wiki_dir=repo_wiki_dir,
            handle=handle,
            since=since,
            max_items=max_items,
            include_not_ready=include_not_ready,
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except json.JSONDecodeError as exc:
        typer.echo(f"Could not read impact eval family candidate data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    rendered = (
        render_impact_eval_family_candidates_json(result)
        if normalized_format == "json"
        else render_impact_eval_family_candidates(result)
    )
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        typer.echo(str(output))
    else:
        typer.echo(rendered, nl=False)


@impact_eval_family_app.command("init")
def eval_impact_family_init(
    name: str = typer.Option(
        ...,
        "--name",
        help="New impact eval family name.",
    ),
    from_candidate: str = typer.Option(
        ...,
        "--from-candidate",
        help="Source candidate doc_id or task_id, such as problems/retry-loop.",
    ),
    baseline_ref: str = typer.Option(
        ...,
        "--baseline-ref",
        help="Historical baseline ref to replay from.",
    ),
    historical_issue: str | None = typer.Option(
        None,
        "--historical-issue",
        help="Optional historical issue summary for spec.toml.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing scaffold files.",
    ),
    repo_root: Path | None = typer.Option(
        None,
        "--repo-root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Repository root containing evals/impact/. Defaults to the current repo.",
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
    """Create a draft impact eval family scaffold from a trial/error candidate."""
    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)

    try:
        result = init_impact_eval_family_from_candidate(
            name=name,
            from_candidate=from_candidate,
            baseline_ref=baseline_ref,
            historical_issue=historical_issue,
            repo_root=repo_root,
            force=force,
        )
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    rendered = (
        render_impact_eval_family_init_result_json(result)
        if normalized_format == "json"
        else render_impact_eval_family_init_result(result)
    )
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        typer.echo(str(output))
    else:
        typer.echo(rendered, nl=False)


@impact_eval_family_app.command("draft")
def eval_impact_family_draft(
    candidate: str = typer.Option(
        ...,
        "--candidate",
        help="Candidate id, doc_id, task_id, or suggested family name from the managed queue.",
    ),
    family_name: str | None = typer.Option(
        None,
        "--family-name",
        help="Optional formal family name to use in the managed draft.",
    ),
    baseline_ref: str | None = typer.Option(
        None,
        "--baseline-ref",
        help="Optional baseline ref. Omit to leave the draft not ready for promotion.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing managed draft files.",
    ),
    repo_root: Path | None = typer.Option(
        None,
        "--repo-root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Repository root containing evals/impact/. Defaults to the current repo.",
    ),
    repo_wiki_dir: Path | None = typer.Option(
        None,
        "--repo-wiki-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="AI wiki directory. Defaults to <repo-root>/ai-wiki.",
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
    """Generate managed draft files for a candidate family without promoting them."""
    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)

    try:
        result = draft_impact_eval_family_candidate(
            candidate_id=candidate,
            family_name=family_name,
            baseline_ref=baseline_ref,
            repo_root=repo_root,
            repo_wiki_dir=repo_wiki_dir,
            force=force,
        )
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except json.JSONDecodeError as exc:
        typer.echo(f"Could not read impact eval family candidate data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    rendered = (
        render_impact_eval_candidate_draft_result_json(result)
        if normalized_format == "json"
        else render_impact_eval_candidate_draft_result(result)
    )
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        typer.echo(str(output))
    else:
        typer.echo(rendered, nl=False)


@impact_eval_family_app.command("promote")
def eval_impact_family_promote(
    candidate: str = typer.Option(
        ...,
        "--candidate",
        help="Candidate id, doc_id, task_id, or suggested family name from the managed queue.",
    ),
    family_name: str | None = typer.Option(
        None,
        "--family-name",
        help="Optional formal family name to write.",
    ),
    baseline_ref: str | None = typer.Option(
        None,
        "--baseline-ref",
        help="Optional baseline ref override.",
    ),
    apply: bool = typer.Option(
        False,
        "--apply",
        help="Actually write formal evals/impact family files. Default is report-only.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing formal family files when applying.",
    ),
    repo_root: Path | None = typer.Option(
        None,
        "--repo-root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Repository root containing evals/impact/. Defaults to the current repo.",
    ),
    repo_wiki_dir: Path | None = typer.Option(
        None,
        "--repo-wiki-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="AI wiki directory. Defaults to <repo-root>/ai-wiki.",
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
    """Check or apply promotion from a managed candidate draft to a formal family."""
    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)

    try:
        result = promote_impact_eval_family_candidate(
            candidate_id=candidate,
            family_name=family_name,
            baseline_ref=baseline_ref,
            repo_root=repo_root,
            repo_wiki_dir=repo_wiki_dir,
            apply=apply,
            force=force,
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except json.JSONDecodeError as exc:
        typer.echo(f"Could not read impact eval family candidate data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    rendered = (
        render_impact_eval_candidate_promotion_result_json(result)
        if normalized_format == "json"
        else render_impact_eval_candidate_promotion_result(result)
    )
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        typer.echo(str(output))
    else:
        typer.echo(rendered, nl=False)


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


@impact_eval_app.command("manifest")
def eval_impact_manifest(
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
    """Describe a captured impact eval run identity and artifact inventory."""
    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)

    try:
        manifest = generate_impact_eval_manifest(run_dir)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except json.JSONDecodeError as exc:
        typer.echo(f"Could not read impact eval data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    rendered = (
        render_impact_eval_manifest_json(manifest)
        if normalized_format == "json"
        else render_impact_eval_manifest(manifest)
    )
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        typer.echo(str(output))
    else:
        typer.echo(rendered, nl=False)


@impact_eval_app.command("plan")
def eval_impact_plan(
    family: str = typer.Option(
        ...,
        "--family",
        help="Impact eval family name under evals/impact/families/.",
    ),
    repo_root: Path | None = typer.Option(
        None,
        "--repo-root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Repository root containing evals/impact/. Defaults to the current repo.",
    ),
    prompt_levels: list[str] | None = typer.Option(
        None,
        "--prompt-level",
        help="Prompt level to include. Repeat for multiple levels. Defaults to original.",
    ),
    run_label: str = typer.Option(
        DEFAULT_RUN_LABEL,
        "--run-label",
        help="Run label to use in the planned run directory.",
    ),
    workspace_root: Path | None = typer.Option(
        None,
        "--workspace-root",
        help="Planned workspace root. Defaults to /private/tmp/aiwiki_first_round/<family>/workspaces/latest.",
    ),
    output_root: Path | None = typer.Option(
        None,
        "--output-root",
        help="Planned run output root. Defaults to /private/tmp/aiwiki_first_round/<family>/runs.",
    ),
    model_family: str = typer.Option(
        DEFAULT_PLAN_MODEL,
        "--model-family",
        help="Expected model family for the planned run.",
    ),
    reasoning_effort: str = typer.Option(
        DEFAULT_PLAN_REASONING_EFFORT,
        "--reasoning-effort",
        help="Expected reasoning effort for the planned run.",
    ),
    source_mode: str = typer.Option(
        DEFAULT_SOURCE_MODE,
        "--source-mode",
        help="Workspace source mode. Choices: committed-head, working-tree.",
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
    """Plan an impact eval run without preparing workspaces or invoking an agent."""
    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)

    try:
        plan = generate_impact_eval_run_plan(
            family=family,
            repo_root=repo_root,
            prompt_levels=tuple(prompt_levels or DEFAULT_PLAN_PROMPT_LEVELS),
            run_label=run_label,
            workspace_root=workspace_root,
            output_root=output_root,
            model_family=model_family,
            reasoning_effort=reasoning_effort,
            source_mode=source_mode,
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    rendered = (
        render_impact_eval_run_plan_json(plan)
        if normalized_format == "json"
        else render_impact_eval_run_plan(plan)
    )
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        typer.echo(str(output))
    else:
        typer.echo(rendered, nl=False)


@impact_eval_app.command("prepare")
def eval_impact_prepare(
    family: str = typer.Option(
        ...,
        "--family",
        help="Impact eval family name under evals/impact/families/.",
    ),
    repo_root: Path | None = typer.Option(
        None,
        "--repo-root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Repository root containing evals/impact/. Defaults to the current repo.",
    ),
    prompt_levels: list[str] | None = typer.Option(
        None,
        "--prompt-level",
        help="Prompt level to include. Repeat for multiple levels. Defaults to original.",
    ),
    run_label: str | None = typer.Option(
        None,
        "--run-label",
        help="Run label to use in the prepared run directory. Defaults to a timestamp.",
    ),
    workspace_root: Path | None = typer.Option(
        None,
        "--workspace-root",
        help="Workspace root to create. Defaults to /private/tmp/aiwiki_first_round/<family>/workspaces/<timestamp>.",
    ),
    output_root: Path | None = typer.Option(
        None,
        "--output-root",
        help="Run output root. Defaults to /private/tmp/aiwiki_first_round/<family>/runs.",
    ),
    model_family: str = typer.Option(
        DEFAULT_PLAN_MODEL,
        "--model-family",
        help="Expected model family for the prepared run.",
    ),
    reasoning_effort: str = typer.Option(
        DEFAULT_PLAN_REASONING_EFFORT,
        "--reasoning-effort",
        help="Expected reasoning effort for the prepared run.",
    ),
    source_mode: str = typer.Option(
        DEFAULT_SOURCE_MODE,
        "--source-mode",
        help="Workspace source mode. Choices: committed-head, working-tree.",
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
    """Prepare impact eval workspaces and a run skeleton without invoking an agent."""
    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)

    try:
        result = prepare_impact_eval_run(
            family=family,
            repo_root=repo_root,
            prompt_levels=tuple(prompt_levels or DEFAULT_PLAN_PROMPT_LEVELS),
            run_label=run_label,
            workspace_root=workspace_root,
            output_root=output_root,
            model_family=model_family,
            reasoning_effort=reasoning_effort,
            source_mode=source_mode,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except json.JSONDecodeError as exc:
        typer.echo(f"Could not read impact eval data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    rendered = (
        render_impact_eval_prepare_result_json(result)
        if normalized_format == "json"
        else render_impact_eval_prepare_result(result)
    )
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        typer.echo(str(output))
    else:
        typer.echo(rendered, nl=False)


@impact_eval_app.command("run")
def eval_impact_run(
    run_dir: Path = typer.Option(
        ...,
        "--run-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Prepared impact eval run directory containing metadata.json.",
    ),
    slots: list[str] | None = typer.Option(
        None,
        "--slot",
        help="Neutral slot to run, such as s01. Repeat for multiple slots.",
    ),
    all_slots: bool = typer.Option(
        False,
        "--all-slots",
        help="Run all slots listed in metadata.json.",
    ),
    prompt_level: str | None = typer.Option(
        None,
        "--prompt-level",
        help="Prompt level to run. Defaults to metadata prompt level or original.",
    ),
    codex_bin: str = typer.Option(
        "codex",
        "--codex-bin",
        help="Codex CLI executable to invoke.",
    ),
    sleep_guard: bool = typer.Option(
        True,
        "--sleep-guard/--no-sleep-guard",
        help="Use the run-level caffeinate guard where available.",
    ),
    export_sessions: bool = typer.Option(
        True,
        "--export-sessions/--skip-export-sessions",
        help="Export matching Codex visible sessions after running slots.",
    ),
    validate_run_flag: bool = typer.Option(
        True,
        "--validate/--no-validate",
        help="Validate exported session evidence and write confounds.json.",
    ),
    score_policy: str = typer.Option(
        DEFAULT_RUN_SCORE_POLICY,
        "--score-policy",
        help=f"Automatic scoring policy. Choices: {', '.join(RUN_SCORE_POLICIES)}.",
    ),
    rubric_path: Path | None = typer.Option(
        None,
        "--rubric",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Rubric JSON file for --score-policy rubric. Defaults to evals/impact/rubrics/<experiment>.json.",
    ),
    report: bool = typer.Option(
        True,
        "--report/--no-report",
        help="Generate report and manifest bundle artifacts after the run.",
    ),
    bundle_dir: Path | None = typer.Option(
        None,
        "--bundle-dir",
        help="Output directory for report bundle. Defaults to <run-dir>/report_bundle.",
    ),
    sessions_root: Path | None = typer.Option(
        None,
        "--sessions-root",
        help="Codex sessions root. Defaults to ~/.codex/sessions.",
    ),
    session_index: Path | None = typer.Option(
        None,
        "--session-index",
        help="Codex session index. Defaults to ~/.codex/session_index.jsonl.",
    ),
    match_workspace_root: Path | None = typer.Option(
        None,
        "--match-workspace-root",
        help="Optional workspace root to match against Codex session cwd values.",
    ),
    export_all_sessions: bool = typer.Option(
        False,
        "--export-all-sessions",
        help="Export every matching session instead of the latest session per slot.",
    ),
    repo_root: Path | None = typer.Option(
        None,
        "--repo-root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Repository root containing evals/impact/. Defaults to the current repo.",
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
    """Run impact eval slots with Codex CLI, capture artifacts, and produce a bundle."""
    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)

    try:
        result = run_impact_eval(
            run_dir=run_dir,
            slots=tuple(slots or ()),
            all_slots=all_slots,
            prompt_level=prompt_level,
            codex_bin=codex_bin,
            sleep_guard=sleep_guard,
            export_sessions=export_sessions,
            validate=validate_run_flag,
            score_policy=score_policy,
            rubric_path=rubric_path,
            report=report,
            bundle_dir=bundle_dir,
            sessions_root=sessions_root,
            session_index=session_index,
            match_workspace_root=match_workspace_root,
            export_all_sessions=export_all_sessions,
            repo_root=repo_root,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except json.JSONDecodeError as exc:
        typer.echo(f"Could not read impact eval data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    rendered = (
        render_impact_eval_run_result_json(result)
        if normalized_format == "json"
        else render_impact_eval_run_result(result)
    )
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        typer.echo(str(output))
    else:
        typer.echo(rendered, nl=False)


@impact_eval_app.command("benchmark")
def eval_impact_benchmark(
    family: str = typer.Option(
        ...,
        "--family",
        help="Impact eval family name under evals/impact/families/.",
    ),
    repo_root: Path | None = typer.Option(
        None,
        "--repo-root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Repository root containing evals/impact/. Defaults to the current repo.",
    ),
    prompt_levels: list[str] | None = typer.Option(
        None,
        "--prompt-level",
        help="Prompt level to include. Repeat for multiple levels. Defaults to original.",
    ),
    run_label: str | None = typer.Option(
        None,
        "--run-label",
        help="Run label to use in the prepared run directory. Defaults to a timestamp.",
    ),
    workspace_root: Path | None = typer.Option(
        None,
        "--workspace-root",
        help="Workspace root to create. Defaults to /private/tmp/aiwiki_first_round/<family>/workspaces/<timestamp>.",
    ),
    output_root: Path | None = typer.Option(
        None,
        "--output-root",
        help="Run output root. Defaults to /private/tmp/aiwiki_first_round/<family>/runs.",
    ),
    model_family: str = typer.Option(
        DEFAULT_PLAN_MODEL,
        "--model-family",
        help="Expected model family for the prepared run.",
    ),
    reasoning_effort: str = typer.Option(
        DEFAULT_PLAN_REASONING_EFFORT,
        "--reasoning-effort",
        help="Expected reasoning effort for the prepared run.",
    ),
    source_mode: str = typer.Option(
        DEFAULT_SOURCE_MODE,
        "--source-mode",
        help="Workspace source mode. Choices: committed-head, working-tree.",
    ),
    codex_bin: str = typer.Option(
        "codex",
        "--codex-bin",
        help="Codex CLI executable to invoke.",
    ),
    sleep_guard: bool = typer.Option(
        True,
        "--sleep-guard/--no-sleep-guard",
        help="Use the run-level caffeinate guard where available.",
    ),
    export_sessions: bool = typer.Option(
        True,
        "--export-sessions/--skip-export-sessions",
        help="Export matching Codex visible sessions after running slots.",
    ),
    validate_run_flag: bool = typer.Option(
        True,
        "--validate/--no-validate",
        help="Validate exported session evidence and write confounds.json.",
    ),
    score_policy: str = typer.Option(
        DEFAULT_RUN_SCORE_POLICY,
        "--score-policy",
        help=f"Automatic scoring policy. Choices: {', '.join(RUN_SCORE_POLICIES)}.",
    ),
    rubric_path: Path | None = typer.Option(
        None,
        "--rubric",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Rubric JSON file for --score-policy rubric. Defaults to evals/impact/rubrics/<experiment>.json.",
    ),
    report: bool = typer.Option(
        True,
        "--report/--no-report",
        help="Generate report and manifest bundle artifacts after the run.",
    ),
    bundle_dir: Path | None = typer.Option(
        None,
        "--bundle-dir",
        help="Output directory for report bundle. Defaults to <run-dir>/report_bundle.",
    ),
    sessions_root: Path | None = typer.Option(
        None,
        "--sessions-root",
        help="Codex sessions root. Defaults to ~/.codex/sessions.",
    ),
    session_index: Path | None = typer.Option(
        None,
        "--session-index",
        help="Codex session index. Defaults to ~/.codex/session_index.jsonl.",
    ),
    match_workspace_root: Path | None = typer.Option(
        None,
        "--match-workspace-root",
        help="Optional workspace root to match against Codex session cwd values.",
    ),
    export_all_sessions: bool = typer.Option(
        False,
        "--export-all-sessions",
        help="Export every matching session instead of the latest session per slot.",
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
    """Prepare and run a whole impact eval family in one command."""
    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)

    try:
        result = run_impact_eval_benchmark(
            family=family,
            repo_root=repo_root,
            prompt_levels=tuple(prompt_levels or DEFAULT_PLAN_PROMPT_LEVELS),
            run_label=run_label,
            workspace_root=workspace_root,
            output_root=output_root,
            model_family=model_family,
            reasoning_effort=reasoning_effort,
            source_mode=source_mode,
            codex_bin=codex_bin,
            sleep_guard=sleep_guard,
            export_sessions=export_sessions,
            validate=validate_run_flag,
            score_policy=score_policy,
            rubric_path=rubric_path,
            report=report,
            bundle_dir=bundle_dir,
            sessions_root=sessions_root,
            session_index=session_index,
            match_workspace_root=match_workspace_root,
            export_all_sessions=export_all_sessions,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except json.JSONDecodeError as exc:
        typer.echo(f"Could not read impact eval data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    rendered = (
        render_impact_eval_benchmark_result_json(result)
        if normalized_format == "json"
        else render_impact_eval_benchmark_result(result)
    )
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        typer.echo(str(output))
    else:
        typer.echo(rendered, nl=False)


@impact_eval_route_noise_app.command("report")
def eval_impact_route_noise_report(
    repo_root: Path | None = typer.Option(
        None,
        "--repo-root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Repository root. Defaults to the current repo.",
    ),
    repo_wiki_dir: Path | None = typer.Option(
        None,
        "--repo-wiki-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="AI wiki directory. Defaults to <repo-root>/ai-wiki.",
    ),
    handle: str | None = typer.Option(
        None,
        "--handle",
        help="Optional handle filter. Defaults to the resolved local handle.",
    ),
    since: str | None = typer.Option(
        DEFAULT_REPO_EVALUATION_SINCE,
        "--since",
        help="Optional ISO timestamp or duration such as 30d.",
    ),
    max_items: int = typer.Option(
        DEFAULT_DIAGNOSTICS_MAX_ITEMS,
        "--max-items",
        min=1,
        help="Maximum rows to include in each report section.",
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
    """Generate a route precision/noise report for impact-eval work."""
    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)

    try:
        result = generate_route_noise_report(
            repo_root=repo_root,
            repo_wiki_dir=repo_wiki_dir,
            handle=handle,
            since=since,
            max_items=max_items,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except json.JSONDecodeError as exc:
        typer.echo(f"Could not read route diagnostic data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    rendered = (
        render_route_noise_report_json(result)
        if normalized_format == "json"
        else render_route_noise_report(result)
    )
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        typer.echo(str(output))
    else:
        typer.echo(rendered, nl=False)


@impact_eval_route_noise_app.command("cohort")
def eval_impact_route_noise_cohort(
    post_change_since: str = typer.Option(
        ...,
        "--post-change-since",
        help="ISO timestamp marking the start of the post-change route cohort.",
    ),
    repo_root: Path | None = typer.Option(
        None,
        "--repo-root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Repository root. Defaults to the current repo.",
    ),
    repo_wiki_dir: Path | None = typer.Option(
        None,
        "--repo-wiki-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="AI wiki directory. Defaults to <repo-root>/ai-wiki.",
    ),
    handle: str | None = typer.Option(
        None,
        "--handle",
        help="Optional handle filter. Defaults to the resolved local handle.",
    ),
    target_evaluable_traces: int = typer.Option(
        57,
        "--target-evaluable-traces",
        min=1,
        help="Post-change evaluable route traces required before the cohort is complete.",
    ),
    baseline_evaluable_traces: int = typer.Option(
        57,
        "--baseline-evaluable-traces",
        min=1,
        help="Number of latest pre-change evaluable route traces to use as baseline.",
    ),
    only_evaluable: bool = typer.Option(
        True,
        "--only-evaluable/--include-unevaluated",
        help="Count only traces with document-level reuse events.",
    ),
    max_items: int = typer.Option(
        DEFAULT_DIAGNOSTICS_MAX_ITEMS,
        "--max-items",
        min=1,
        help="Maximum trace rows to include per cohort.",
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
    """Compare pre-change and post-change route precision cohorts."""
    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)

    try:
        result = generate_route_cohort_report(
            post_change_since=post_change_since,
            repo_root=repo_root,
            repo_wiki_dir=repo_wiki_dir,
            handle=handle,
            target_evaluable_traces=target_evaluable_traces,
            baseline_evaluable_traces=baseline_evaluable_traces,
            only_evaluable=only_evaluable,
            max_items=max_items,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except json.JSONDecodeError as exc:
        typer.echo(f"Could not read route cohort data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    rendered = (
        render_route_cohort_report_json(result)
        if normalized_format == "json"
        else render_route_cohort_report(result)
    )
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        typer.echo(str(output))
    else:
        typer.echo(rendered, nl=False)


@impact_eval_route_noise_app.command("replay")
def eval_impact_route_noise_replay(
    before: str | None = typer.Option(
        None,
        "--before",
        help="Only replay evaluable route traces before this ISO timestamp.",
    ),
    catalog_cutoff: str = typer.Option(
        "current",
        "--catalog-cutoff",
        help="Catalog cutoff policy for replay. Choices: current, trace-routed-at.",
    ),
    repo_root: Path | None = typer.Option(
        None,
        "--repo-root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Repository root. Defaults to the current repo.",
    ),
    repo_wiki_dir: Path | None = typer.Option(
        None,
        "--repo-wiki-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="AI wiki directory. Defaults to <repo-root>/ai-wiki.",
    ),
    handle: str | None = typer.Option(
        None,
        "--handle",
        help="Optional handle filter. Defaults to the resolved local handle.",
    ),
    target_evaluable_traces: int = typer.Option(
        57,
        "--target-evaluable-traces",
        min=1,
        help="Number of latest evaluable historical traces to replay.",
    ),
    codex_sessions_root: Path | None = typer.Option(
        None,
        "--codex-sessions-root",
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Codex sessions root. Defaults to ~/.codex/sessions.",
    ),
    codex_state_db: Path | None = typer.Option(
        None,
        "--codex-state-db",
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Codex state DB. Defaults to ~/.codex/state_5.sqlite.",
    ),
    max_docs: int = typer.Option(
        6,
        "--max-docs",
        min=1,
        max=20,
        help="Maximum number of route docs for each replay.",
    ),
    rerank_top: int = typer.Option(
        DEFAULT_ROUTE_RERANK_TOP,
        "--rerank-top",
        min=0,
        max=100,
        help="Number of top deterministic index cards to rerank for each replay route. Use 0 to disable.",
    ),
    budget_words: int = typer.Option(
        3000,
        "--budget-words",
        min=100,
        help="Safety cap for each replayed route packet.",
    ),
    max_items: int = typer.Option(
        DEFAULT_DIAGNOSTICS_MAX_ITEMS,
        "--max-items",
        min=1,
        help="Maximum replay rows to include in the report artifact.",
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
    """Replay historical route prompts through the current route scorer."""
    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)

    try:
        result = generate_route_replay_report(
            repo_root=repo_root,
            repo_wiki_dir=repo_wiki_dir,
            handle=handle,
            before=before,
            catalog_cutoff=catalog_cutoff,
            target_evaluable_traces=target_evaluable_traces,
            codex_sessions_root=codex_sessions_root,
            codex_state_db=codex_state_db,
            max_docs=max_docs,
            rerank_top=rerank_top,
            budget_words=budget_words,
            max_items=max_items,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except json.JSONDecodeError as exc:
        typer.echo(f"Could not read route replay data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    rendered = (
        render_route_replay_report_json(result)
        if normalized_format == "json"
        else render_route_replay_report(result)
    )
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        typer.echo(str(output))
    else:
        typer.echo(rendered, nl=False)


@impact_eval_neutral_app.command("report")
def eval_impact_neutral_report(
    period_id: str = typer.Option(
        ...,
        "--period-id",
        help="Scheduled run period id to analyze, such as project-a-rerun-2026-06-03.",
    ),
    families: list[str] | None = typer.Option(
        None,
        "--family",
        help="Optional family filter. Repeat for multiple families.",
    ),
    repo_root: Path | None = typer.Option(
        None,
        "--repo-root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Repository root containing evals/impact/. Defaults to the current repo.",
    ),
    repo_wiki_dir: Path | None = typer.Option(
        None,
        "--repo-wiki-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="AI wiki directory. Defaults to <repo-root>/ai-wiki.",
    ),
    neutral_only: bool = typer.Option(
        True,
        "--neutral-only/--include-all",
        help="Report only families whose primary outcome is neutral_signal.",
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
    """Generate a slot-level report for neutral impact-eval families."""
    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)

    try:
        result = generate_neutral_impact_eval_report(
            period_id=period_id,
            repo_root=repo_root,
            repo_wiki_dir=repo_wiki_dir,
            families=tuple(families or ()),
            neutral_only=neutral_only,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except json.JSONDecodeError as exc:
        typer.echo(f"Could not read neutral impact eval data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    rendered = (
        render_neutral_impact_eval_report_json(result)
        if normalized_format == "json"
        else render_neutral_impact_eval_report(result)
    )
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        typer.echo(str(output))
    else:
        typer.echo(rendered, nl=False)


@impact_eval_project_a_app.command("report")
def eval_impact_project_a_report(
    repo_root: Path | None = typer.Option(
        None,
        "--repo-root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Repository root containing evals/impact/. Defaults to the current repo.",
    ),
    repo_wiki_dir: Path | None = typer.Option(
        None,
        "--repo-wiki-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="AI wiki directory. Defaults to <repo-root>/ai-wiki.",
    ),
    handle: str | None = typer.Option(
        None,
        "--handle",
        help="Optional handle filter. Defaults to the resolved local handle.",
    ),
    since: str | None = typer.Option(
        DEFAULT_REPO_EVALUATION_SINCE,
        "--since",
        help="Optional ISO timestamp or duration such as 30d.",
    ),
    candidate_max_items: int = typer.Option(
        DEFAULT_DIAGNOSTICS_MAX_ITEMS,
        "--candidate-max-items",
        min=1,
        help="Maximum candidate/diagnostic items to include in underlying reports.",
    ),
    period_id: str | None = typer.Option(
        None,
        "--period-id",
        help="Optional schedule-report period id. Defaults to the current ISO week.",
    ),
    run_checks: bool = typer.Option(
        False,
        "--run-checks/--skip-checks",
        help="Run pytest, npm pack dry-run, and git diff whitespace checks before reporting.",
    ),
    write: bool = typer.Option(
        True,
        "--write/--no-write",
        help="Write evals/impact/reports/project_a_diagnostics_<date> artifacts.",
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
    """Generate one Project A diagnostic report across tests, evals, runs, and routing."""
    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)

    try:
        result = generate_project_a_diagnostics(
            repo_root=repo_root,
            repo_wiki_dir=repo_wiki_dir,
            handle=handle,
            since=since,
            candidate_max_items=candidate_max_items,
            period_id=period_id,
            run_checks=run_checks,
            write=write,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except json.JSONDecodeError as exc:
        typer.echo(f"Could not read Project A diagnostic data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    rendered = (
        render_project_a_diagnostics_json(result)
        if normalized_format == "json"
        else render_project_a_diagnostics(result)
    )
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        typer.echo(str(output))
    else:
        typer.echo(rendered, nl=False)


@impact_eval_schedule_app.command("report")
def eval_impact_schedule_report(
    repo_root: Path | None = typer.Option(
        None,
        "--repo-root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Repository root containing evals/impact/. Defaults to the current repo.",
    ),
    repo_wiki_dir: Path | None = typer.Option(
        None,
        "--repo-wiki-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="AI wiki directory. Defaults to <repo-root>/ai-wiki.",
    ),
    period_id: str | None = typer.Option(
        None,
        "--period-id",
        help="Report period id. Defaults to the current ISO week, such as 2026-W21.",
    ),
    refresh_candidates: bool = typer.Option(
        True,
        "--refresh-candidates/--no-refresh-candidates",
        help="Refresh the managed candidate queue before generating the report.",
    ),
    handle: str | None = typer.Option(
        None,
        "--handle",
        help="Optional handle filter for candidate queue refresh.",
    ),
    since: str | None = typer.Option(
        None,
        "--since",
        help="Optional ISO timestamp or duration such as 14d for candidate queue refresh.",
    ),
    candidate_max_items: int = typer.Option(
        DEFAULT_DIAGNOSTICS_MAX_ITEMS,
        "--candidate-max-items",
        min=1,
        help="Maximum candidates to refresh into the managed queue.",
    ),
    include_not_ready: bool = typer.Option(
        True,
        "--include-not-ready/--ready-only",
        help="Include weaker observed signals in the refreshed candidate queue.",
    ),
    max_recent_runs: int = typer.Option(
        20,
        "--max-recent-runs",
        min=1,
        help="Maximum indexed benchmark runs to include.",
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
    """Generate a periodic impact eval report from families, candidates, and run history."""
    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)

    try:
        result = generate_impact_eval_schedule_report(
            repo_root=repo_root,
            repo_wiki_dir=repo_wiki_dir,
            period_id=period_id,
            refresh_candidates=refresh_candidates,
            handle=handle,
            since=since,
            candidate_max_items=candidate_max_items,
            include_not_ready=include_not_ready,
            max_recent_runs=max_recent_runs,
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except json.JSONDecodeError as exc:
        typer.echo(f"Could not read impact eval schedule data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    rendered = (
        render_impact_eval_schedule_report_json(result)
        if normalized_format == "json"
        else render_impact_eval_schedule_report(result)
    )
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        typer.echo(str(output))
    else:
        typer.echo(rendered, nl=False)


@impact_eval_schedule_app.command("backfill-history")
def eval_impact_schedule_backfill_history(
    repo_root: Path | None = typer.Option(
        None,
        "--repo-root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Repository root containing evals/impact/. Defaults to the current repo.",
    ),
    repo_wiki_dir: Path | None = typer.Option(
        None,
        "--repo-wiki-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="AI wiki directory. Defaults to <repo-root>/ai-wiki.",
    ),
    notes: list[Path] | None = typer.Option(
        None,
        "--note",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Historical findings note to register. Repeat to override default note discovery.",
    ),
    replace_existing: bool = typer.Option(
        True,
        "--replace-existing/--append",
        help="Replace prior historical backfill entries before writing the run index.",
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
    """Register historical manual findings notes in the scheduled run index."""
    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)

    try:
        result = backfill_historical_impact_eval_run_index(
            repo_root=repo_root,
            repo_wiki_dir=repo_wiki_dir,
            note_paths=tuple(notes or ()),
            replace_existing=replace_existing,
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except json.JSONDecodeError as exc:
        typer.echo(f"Could not read impact eval history data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    rendered = (
        render_impact_eval_history_backfill_result_json(result)
        if normalized_format == "json"
        else render_impact_eval_history_backfill_result(result)
    )
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        typer.echo(str(output))
    else:
        typer.echo(rendered, nl=False)


@impact_eval_schedule_app.command("run")
def eval_impact_schedule_run(
    families: list[str] | None = typer.Option(
        None,
        "--family",
        help="Runnable family to benchmark. Repeat for multiple families.",
    ),
    all_runnable: bool = typer.Option(
        False,
        "--all-runnable",
        help="Benchmark every currently runnable family.",
    ),
    repo_root: Path | None = typer.Option(
        None,
        "--repo-root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Repository root containing evals/impact/. Defaults to the current repo.",
    ),
    repo_wiki_dir: Path | None = typer.Option(
        None,
        "--repo-wiki-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="AI wiki directory. Defaults to <repo-root>/ai-wiki.",
    ),
    period_id: str | None = typer.Option(
        None,
        "--period-id",
        help="Schedule period id. Defaults to the current ISO week, such as 2026-W21.",
    ),
    if_due: bool = typer.Option(
        False,
        "--if-due",
        help="Skip running if this period already has a completed schedule run.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Run even when --if-due would otherwise skip this period.",
    ),
    handle: str | None = typer.Option(
        None,
        "--handle",
        help="Optional handle filter for the post-run candidate queue refresh.",
    ),
    since: str | None = typer.Option(
        None,
        "--since",
        help="Optional ISO timestamp or duration such as 14d for candidate queue refresh.",
    ),
    candidate_max_items: int = typer.Option(
        DEFAULT_DIAGNOSTICS_MAX_ITEMS,
        "--candidate-max-items",
        min=1,
        help="Maximum candidates to refresh into the managed queue after the run.",
    ),
    include_not_ready: bool = typer.Option(
        True,
        "--include-not-ready/--ready-only",
        help="Include weaker observed signals in the refreshed candidate queue.",
    ),
    prompt_levels: list[str] | None = typer.Option(
        None,
        "--prompt-level",
        help="Prompt level to include. Repeat for multiple levels. Defaults to original.",
    ),
    model_family: str = typer.Option(
        DEFAULT_PLAN_MODEL,
        "--model-family",
        help="Expected model family for each prepared run.",
    ),
    reasoning_effort: str = typer.Option(
        DEFAULT_PLAN_REASONING_EFFORT,
        "--reasoning-effort",
        help="Expected reasoning effort for each prepared run.",
    ),
    source_mode: str = typer.Option(
        DEFAULT_SOURCE_MODE,
        "--source-mode",
        help="Workspace source mode. Choices: committed-head, working-tree.",
    ),
    codex_bin: str = typer.Option(
        "codex",
        "--codex-bin",
        help="Codex CLI executable to invoke.",
    ),
    sleep_guard: bool = typer.Option(
        True,
        "--sleep-guard/--no-sleep-guard",
        help="Use the run-level caffeinate guard where available.",
    ),
    export_sessions: bool = typer.Option(
        True,
        "--export-sessions/--skip-export-sessions",
        help="Export matching Codex visible sessions after running slots.",
    ),
    validate_run_flag: bool = typer.Option(
        True,
        "--validate/--no-validate",
        help="Validate exported session evidence and write confounds.json.",
    ),
    score_policy: str = typer.Option(
        DEFAULT_RUN_SCORE_POLICY,
        "--score-policy",
        help=f"Automatic scoring policy. Choices: {', '.join(RUN_SCORE_POLICIES)}.",
    ),
    rubric_path: Path | None = typer.Option(
        None,
        "--rubric",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Rubric JSON file for --score-policy rubric. Defaults by family when omitted.",
    ),
    sessions_root: Path | None = typer.Option(
        None,
        "--sessions-root",
        help="Codex sessions root. Defaults to ~/.codex/sessions.",
    ),
    session_index: Path | None = typer.Option(
        None,
        "--session-index",
        help="Codex session index. Defaults to ~/.codex/session_index.jsonl.",
    ),
    match_workspace_root: Path | None = typer.Option(
        None,
        "--match-workspace-root",
        help="Optional workspace root to match against Codex session cwd values.",
    ),
    export_all_sessions: bool = typer.Option(
        False,
        "--export-all-sessions",
        help="Export every matching session instead of the latest session per slot.",
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
    """Run scheduled family benchmarks and update the trend/report store."""
    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)

    try:
        result = run_impact_eval_schedule(
            repo_root=repo_root,
            repo_wiki_dir=repo_wiki_dir,
            families=tuple(families or ()),
            all_runnable=all_runnable,
            period_id=period_id,
            if_due=if_due,
            force=force,
            handle=handle,
            since=since,
            candidate_max_items=candidate_max_items,
            include_not_ready=include_not_ready,
            prompt_levels=tuple(prompt_levels or DEFAULT_PLAN_PROMPT_LEVELS),
            model_family=model_family,
            reasoning_effort=reasoning_effort,
            source_mode=source_mode,
            codex_bin=codex_bin,
            sleep_guard=sleep_guard,
            export_sessions=export_sessions,
            validate=validate_run_flag,
            score_policy=score_policy,
            rubric_path=rubric_path,
            sessions_root=sessions_root,
            session_index=session_index,
            match_workspace_root=match_workspace_root,
            export_all_sessions=export_all_sessions,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except json.JSONDecodeError as exc:
        typer.echo(f"Could not read impact eval schedule data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    rendered = (
        render_impact_eval_schedule_run_result_json(result)
        if normalized_format == "json"
        else render_impact_eval_schedule_run_result(result)
    )
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        typer.echo(str(output))
    else:
        typer.echo(rendered, nl=False)


@impact_eval_app.command("capture")
def eval_impact_capture(
    run_dir: Path = typer.Option(
        ...,
        "--run-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Impact eval run directory containing metadata.json.",
    ),
    slot: str = typer.Option(
        ...,
        "--slot",
        help="Neutral slot such as s01.",
    ),
    prompt_level: str = typer.Option(
        "original",
        "--prompt-level",
        help="Prompt level such as original.",
    ),
    workspace: Path | None = typer.Option(
        None,
        "--workspace",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Workspace to capture. Defaults to the slot workspace from metadata.json.",
    ),
    variant: str | None = typer.Option(
        None,
        "--variant",
        help="Semantic variant name. Defaults to the slot variant from metadata.json.",
    ),
    phase: str = typer.Option(
        "first_pass",
        "--phase",
        help="Capture phase. Choices: first_pass, final.",
    ),
    final_message: Path | None = typer.Option(
        None,
        "--final-message",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Optional saved final message markdown file to copy into the capture.",
    ),
    attempt: int = typer.Option(
        1,
        "--attempt",
        min=1,
        help="Attempt number for this saved result.",
    ),
    human_nudges: int = typer.Option(
        0,
        "--human-nudges",
        min=0,
        help="How many human nudges were needed.",
    ),
    first_pass_success: bool | None = typer.Option(
        None,
        "--first-pass-success/--first-pass-failure",
        help="Mark whether the first attempt succeeded.",
    ),
    notes: str = typer.Option(
        "",
        "--notes",
        help="Optional free-form notes for this result.",
    ),
    repo_root: Path | None = typer.Option(
        None,
        "--repo-root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Repository root containing evals/impact/. Defaults to the current repo.",
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
    """Capture first-pass or repaired impact eval artifacts from a local workspace."""
    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)

    try:
        result = capture_impact_eval_result(
            run_dir=run_dir,
            slot=slot,
            prompt_level=prompt_level,
            workspace=workspace,
            variant=variant,
            phase=phase,
            final_message=final_message,
            attempt=attempt,
            human_nudges=human_nudges,
            first_pass_success=first_pass_success,
            notes=notes,
            repo_root=repo_root,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except json.JSONDecodeError as exc:
        typer.echo(f"Could not read impact eval data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    rendered = (
        render_impact_eval_capture_result_json(result)
        if normalized_format == "json"
        else render_impact_eval_capture_result(result)
    )
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        typer.echo(str(output))
    else:
        typer.echo(rendered, nl=False)


@impact_eval_app.command("validate")
def eval_impact_validate(
    run_dir: Path = typer.Option(
        ...,
        "--run-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Impact eval run directory containing metadata.json.",
    ),
    session_export_root: Path | None = typer.Option(
        None,
        "--session-export-root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Codex session export root. Defaults to <workspace_root>/codex_sessions.",
    ),
    repo_root: Path | None = typer.Option(
        None,
        "--repo-root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Repository root containing evals/impact/. Defaults to the current repo.",
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
    """Validate session exports and confounds for a captured impact eval run."""
    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)

    try:
        result = validate_impact_eval_run(
            run_dir=run_dir,
            session_export_root=session_export_root,
            repo_root=repo_root,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except json.JSONDecodeError as exc:
        typer.echo(f"Could not read impact eval data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    rendered = (
        render_impact_eval_validate_result_json(result)
        if normalized_format == "json"
        else render_impact_eval_validate_result(result)
    )
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        typer.echo(str(output))
    else:
        typer.echo(rendered, nl=False)


@impact_eval_app.command("score")
def eval_impact_score(
    run_dir: Path = typer.Option(
        ...,
        "--run-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Impact eval run directory containing metadata.json.",
    ),
    slot: str = typer.Option(
        ...,
        "--slot",
        help="Neutral slot such as s01.",
    ),
    prompt_level: str = typer.Option(
        "original",
        "--prompt-level",
        help="Prompt level such as original.",
    ),
    label: str = typer.Option(
        ...,
        "--label",
        help=f"Manual score label. Choices: {', '.join(SCORE_LABELS)}.",
    ),
    rubric_refs: list[str] | None = typer.Option(
        None,
        "--rubric-ref",
        help="Repeatable rubric reference used for manual scoring.",
    ),
    evidence: list[str] | None = typer.Option(
        None,
        "--evidence",
        help="Repeatable evidence artifact path used for scoring.",
    ),
    notes: str = typer.Option(
        "",
        "--notes",
        help="Manual scoring notes.",
    ),
    repo_root: Path | None = typer.Option(
        None,
        "--repo-root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Repository root containing evals/impact/. Defaults to the current repo.",
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
    """Write a manual score artifact and refresh the run manifest."""
    normalized_format = output_format.strip().lower()
    if normalized_format not in {"text", "json"}:
        typer.echo("Invalid --format. Expected one of: text, json.", err=True)
        raise typer.Exit(code=1)

    try:
        result = score_impact_eval_result(
            run_dir=run_dir,
            slot=slot,
            prompt_level=prompt_level,
            label=label,
            rubric_refs=tuple(rubric_refs or ()),
            evidence=tuple(evidence or ()),
            notes=notes,
            repo_root=repo_root,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except json.JSONDecodeError as exc:
        typer.echo(f"Could not read impact eval data: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    rendered = (
        render_impact_eval_score_result_json(result)
        if normalized_format == "json"
        else render_impact_eval_score_result(result)
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
    source_incident_seconds: int | None = typer.Option(
        None,
        "--source-incident-seconds",
        min=0,
        help="Optional active seconds spent in the original source incident.",
    ),
    source_incident_timing_source: str = typer.Option(
        "manual",
        "--source-incident-source",
        help=(
            "Source of --source-incident-seconds. "
            f"Choices: {', '.join(SOURCE_INCIDENT_TIMING_SOURCES)}."
        ),
    ),
    source_incident_note: str | None = typer.Option(
        None,
        "--source-incident-note",
        help="Optional note describing what the source incident timing includes.",
    ),
    source_incident_from_codex_session: bool = typer.Option(
        False,
        "--source-incident-from-codex-session/--no-source-incident-from-codex-session",
        help=(
            "Derive source incident active seconds from --source-session-id in "
            "~/.codex/sessions."
        ),
    ),
    codex_sessions_root: Path | None = typer.Option(
        None,
        "--codex-sessions-root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Optional Codex sessions root for --source-incident-from-codex-session.",
    ),
    observed_at: str | None = typer.Option(
        None,
        "--observed-at",
        help="Optional explicit timestamp. Defaults to the current local time in ISO-8601 format.",
    ),
    session_id: str | None = typer.Option(
        None,
        "--session-id",
        help="Optional run/session identifier for this reuse observation.",
    ),
    source_session_id: str | None = typer.Option(
        None,
        "--source-session-id",
        help="Optional session identifier for the run that created the reused memory.",
    ),
    source_task_id: str | None = typer.Option(
        None,
        "--source-task-id",
        help="Optional task identifier for the run that created the reused memory.",
    ),
    consulted_order: int | None = typer.Option(
        None,
        "--consulted-order",
        min=1,
        help="Optional 1-based order in which this document was consulted during the task.",
    ),
    signal_status: str | None = typer.Option(
        None,
        "--signal-status",
        help=f"Whether a diagnostic signal is candidate or confirmed. Choices: {', '.join(SIGNAL_STATUSES)}.",
    ),
    not_helpful_reason: str | None = typer.Option(
        None,
        "--not-helpful-reason",
        help=f"Structured reason for a not_helpful signal. Choices: {', '.join(NOT_HELPFUL_REASONS)}.",
    ),
    resolved_by_doc_id: str | None = typer.Option(
        None,
        "--resolved-by-doc-id",
        help="Optional doc_id that later resolved the task when this document only partially helped.",
    ),
    superseded_by_doc_id: str | None = typer.Option(
        None,
        "--superseded-by-doc-id",
        help="Optional doc_id that made this document stale, noisy, or less useful.",
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
            source_incident_seconds=source_incident_seconds,
            source_incident_timing_source=source_incident_timing_source,
            source_incident_note=source_incident_note,
            source_incident_from_session=source_incident_from_codex_session,
            codex_sessions_root=codex_sessions_root,
            observed_at=observed_at,
            session_id=session_id,
            source_session_id=source_session_id,
            source_task_id=source_task_id,
            consulted_order=consulted_order,
            signal_status=signal_status,
            not_helpful_reason=not_helpful_reason,
            resolved_by_doc_id=resolved_by_doc_id,
            superseded_by_doc_id=superseded_by_doc_id,
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
