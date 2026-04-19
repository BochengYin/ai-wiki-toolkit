"""Diagnosis helpers for AI wiki index upgrades."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ai_wiki_toolkit.content import PROMPT_BLOCK_END, PROMPT_BLOCK_START, repo_starter_files
from ai_wiki_toolkit.paths import ToolkitPaths, build_paths, existing_prompt_targets, resolve_user_handle


@dataclass(frozen=True)
class DoctorFinding:
    severity: str
    code: str
    path: str
    message: str
    suggested_fix: str | None = None


@dataclass(frozen=True)
class IndexUpgradeSuggestion:
    path: str
    reason: str
    content: str
    replace_hint: str


@dataclass
class DoctorResult:
    paths: ToolkitPaths
    resolved_handle: str
    findings: list[DoctorFinding] = field(default_factory=list)
    suggestions: list[IndexUpgradeSuggestion] = field(default_factory=list)


def _add_finding(
    result: DoctorResult,
    *,
    severity: str,
    code: str,
    path: str,
    message: str,
    suggested_fix: str | None = None,
) -> None:
    result.findings.append(
        DoctorFinding(
            severity=severity,
            code=code,
            path=path,
            message=message,
            suggested_fix=suggested_fix,
        )
    )


def _add_suggestion(
    result: DoctorResult,
    *,
    path: str,
    reason: str,
    content: str,
    replace_hint: str,
) -> None:
    result.suggestions.append(
        IndexUpgradeSuggestion(
            path=path,
            reason=reason,
            content=content,
            replace_hint=replace_hint,
        )
    )


def _top_level_index_missing_tokens() -> tuple[str, ...]:
    return (
        "review-patterns/index.md",
        "trails/index.md",
        "people/<handle>/index.md",
        "metrics/",
    )


def _check_repo_index(result: DoctorResult, starters: dict[str, str]) -> None:
    index_path = result.paths.repo_wiki_dir / "index.md"
    if not index_path.exists():
        _add_finding(
            result,
            severity="WARN",
            code="missing_repo_index",
            path="ai-wiki/index.md",
            message="`ai-wiki/index.md` is missing.",
            suggested_fix="Create the repo index or copy the suggested starter content.",
        )
        _add_suggestion(
            result,
            path="ai-wiki/index.md",
            reason="Top-level AI wiki index is missing.",
            content=starters["index.md"],
            replace_hint="Copy this starter content into the missing file.",
        )
        return

    text = index_path.read_text(encoding="utf-8")
    missing_tokens = [token for token in _top_level_index_missing_tokens() if token not in text]
    if not missing_tokens:
        _add_finding(
            result,
            severity="OK",
            code="repo_index_current",
            path="ai-wiki/index.md",
            message="`ai-wiki/index.md` already uses the current index-based navigation shape.",
        )
        return

    missing_refs = ", ".join(missing_tokens)
    _add_finding(
        result,
        severity="WARN",
        code="legacy_repo_index_navigation",
        path="ai-wiki/index.md",
        message=f"`ai-wiki/index.md` is missing current navigation references: {missing_refs}.",
        suggested_fix="Update the navigation section or use the suggested starter content as a merge target.",
    )
    _add_suggestion(
        result,
        path="ai-wiki/index.md",
        reason=f"Current index is missing recommended navigation references: {missing_refs}.",
        content=starters["index.md"],
        replace_hint=(
            "If the file already contains repo-specific notes, keep those notes and merge in the updated "
            "navigation structure instead of blindly replacing the whole file."
        ),
    )


def _check_child_index(
    result: DoctorResult,
    *,
    relative_path: str,
    starter_content: str,
    description: str,
) -> None:
    full_path = result.paths.repo_wiki_dir / relative_path
    repo_relative_path = f"ai-wiki/{relative_path}"
    if full_path.exists():
        _add_finding(
            result,
            severity="OK",
            code="child_index_present",
            path=repo_relative_path,
            message=f"`{repo_relative_path}` exists.",
        )
        return

    _add_finding(
        result,
        severity="WARN",
        code="missing_child_index",
        path=repo_relative_path,
        message=f"`{repo_relative_path}` is missing.",
        suggested_fix=f"Create the {description} index using the suggested starter content.",
    )
    _add_suggestion(
        result,
        path=repo_relative_path,
        reason=f"Missing {description} index.",
        content=starter_content,
        replace_hint="Create this file with the starter content below, then customize it as needed.",
    )


def _check_prompt_targets(result: DoctorResult) -> None:
    prompt_targets = existing_prompt_targets(result.paths.repo_root)
    if not prompt_targets:
        _add_finding(
            result,
            severity="INFO",
            code="no_prompt_targets",
            path="repo-root",
            message="No supported prompt file exists yet (`AGENT.md`, `AGENTS.md`, or `CLAUDE.md`).",
            suggested_fix="Run `aiwiki-toolkit install` if you want the managed prompt block created.",
        )
        return

    for prompt_path in prompt_targets:
        text = prompt_path.read_text(encoding="utf-8")
        if PROMPT_BLOCK_START not in text or PROMPT_BLOCK_END not in text:
            _add_finding(
                result,
                severity="INFO",
                code="prompt_without_managed_block",
                path=prompt_path.name,
                message=f"`{prompt_path.name}` exists but does not contain an `aiwiki-toolkit` managed block.",
                suggested_fix="Run `aiwiki-toolkit install` to add or refresh the managed prompt block.",
            )
            continue

        missing_tokens = []
        for token in ("review-patterns/index.md", "people/<handle>/index.md"):
            if token not in text:
                missing_tokens.append(token)

        if missing_tokens:
            _add_finding(
                result,
                severity="WARN",
                code="legacy_prompt_index_navigation",
                path=prompt_path.name,
                message=(
                    f"`{prompt_path.name}` has a managed block but is missing index-based references: "
                    f"{', '.join(missing_tokens)}."
                ),
                suggested_fix="Run `aiwiki-toolkit install` to refresh the managed prompt block.",
            )
            continue

        _add_finding(
            result,
            severity="OK",
            code="prompt_index_navigation_current",
            path=prompt_path.name,
            message=f"`{prompt_path.name}` already references the current index-based prompt navigation.",
        )


def run_doctor(start: Path | None = None, handle: str | None = None) -> DoctorResult:
    paths = build_paths(start)
    resolved_handle = resolve_user_handle(paths.repo_root, explicit_handle=handle)
    result = DoctorResult(paths=paths, resolved_handle=resolved_handle)

    if not paths.repo_wiki_dir.exists():
        _add_finding(
            result,
            severity="ERROR",
            code="missing_repo_wiki",
            path="ai-wiki/",
            message="`ai-wiki/` is missing.",
            suggested_fix="Run `aiwiki-toolkit install` first.",
        )
        return result

    _add_finding(
        result,
        severity="OK",
        code="repo_wiki_present",
        path="ai-wiki/",
        message="`ai-wiki/` exists.",
    )

    managed_system = paths.repo_toolkit_dir / "system.md"
    if managed_system.exists():
        _add_finding(
            result,
            severity="OK",
            code="managed_system_present",
            path="ai-wiki/_toolkit/system.md",
            message="`ai-wiki/_toolkit/system.md` exists.",
        )
    else:
        _add_finding(
            result,
            severity="WARN",
            code="missing_managed_system",
            path="ai-wiki/_toolkit/system.md",
            message="`ai-wiki/_toolkit/system.md` is missing.",
            suggested_fix="Run `aiwiki-toolkit install` to refresh managed files.",
        )

    starters = repo_starter_files(resolved_handle)
    _check_repo_index(result, starters)
    _check_child_index(
        result,
        relative_path="review-patterns/index.md",
        starter_content=starters["review-patterns/index.md"],
        description="review patterns",
    )
    _check_child_index(
        result,
        relative_path="trails/index.md",
        starter_content=starters["trails/index.md"],
        description="trails",
    )
    _check_child_index(
        result,
        relative_path=f"people/{resolved_handle}/index.md",
        starter_content=starters[f"people/{resolved_handle}/index.md"],
        description=f"personal index for handle `{resolved_handle}`",
    )
    _check_child_index(
        result,
        relative_path="metrics/index.md",
        starter_content=starters["metrics/index.md"],
        description="metrics",
    )
    _check_prompt_targets(result)

    return result
