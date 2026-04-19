"""Diagnosis helpers for AI wiki navigation and rule drift."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path
import re

from ai_wiki_toolkit.content import PROMPT_BLOCK_END, PROMPT_BLOCK_START, repo_starter_files
from ai_wiki_toolkit.frontmatter import parse_frontmatter
from ai_wiki_toolkit.paths import ToolkitPaths, build_paths, existing_prompt_targets, resolve_user_handle

_NORMALIZE_TOKEN_RE = re.compile(r"[^a-z0-9]+")
_LIST_MARKER_RE = re.compile(r"^(?:[-*+]\s+|\d+\.\s+)")
_H1_RE = re.compile(r"^#\s+(?P<title>.+?)\s*$")
_H2_RE = re.compile(r"^##\s+(?P<title>.+?)\s*$")


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


@dataclass(frozen=True)
class RuleDoc:
    display_path: str
    family: str
    scope: str
    title: str
    title_key: str
    body_key: str
    sections: dict[str, str]
    section_titles: dict[str, str]


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
        "_toolkit/index.md",
        "workflows.md",
        "decisions.md",
        "review-patterns/index.md",
        "trails/index.md",
        "people/<handle>/index.md",
        "metrics/",
    )


def _normalize_heading(value: str) -> str:
    lowered = value.strip().lower()
    lowered = re.sub(r"^\d+(?:\.\d+)*\s+", "", lowered)
    return _NORMALIZE_TOKEN_RE.sub(" ", lowered).strip()


def _normalize_body(value: str) -> str:
    normalized_lines: list[str] = []
    for raw_line in value.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r"^#+\s*", "", line)
        line = _LIST_MARKER_RE.sub("", line)
        line = re.sub(r"^\d+(?:\.\d+)*\s+", "", line)
        line = _NORMALIZE_TOKEN_RE.sub(" ", line.lower()).strip()
        if line:
            normalized_lines.append(line)
    return "\n".join(normalized_lines)


def _extract_title(body: str, fallback_path: Path) -> str:
    for line in body.splitlines():
        match = _H1_RE.match(line.strip())
        if match:
            return match.group("title").strip()
    return fallback_path.stem.replace("-", " ").replace("_", " ").strip() or fallback_path.stem


def _extract_h2_sections(body: str) -> tuple[dict[str, str], dict[str, str]]:
    sections: dict[str, str] = {}
    titles: dict[str, str] = {}
    current_key: str | None = None
    current_title: str | None = None
    buffer: list[str] = []

    def flush() -> None:
        if current_key is None or current_title is None:
            return
        sections[current_key] = _normalize_body("\n".join(buffer))
        titles[current_key] = current_title

    for line in body.splitlines():
        match = _H2_RE.match(line.strip())
        if match:
            flush()
            current_title = match.group("title").strip()
            current_key = _normalize_heading(current_title)
            buffer = []
            continue
        if current_key is not None:
            buffer.append(line)

    flush()
    return sections, titles


def _home_display_path(path: Path, home_dir: Path) -> str:
    return f"<home>/ai-wiki/{path.relative_to(home_dir).as_posix()}"


def _build_rule_doc(path: Path, *, display_path: str, family: str, scope: str) -> RuleDoc:
    text = path.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(text)
    title = metadata.get("title") if isinstance(metadata.get("title"), str) else None
    resolved_title = title.strip() if title and title.strip() else _extract_title(body, path)
    sections, section_titles = _extract_h2_sections(body)
    return RuleDoc(
        display_path=display_path,
        family=family,
        scope=scope,
        title=resolved_title,
        title_key=_normalize_heading(resolved_title),
        body_key=_normalize_body(body),
        sections=sections,
        section_titles=section_titles,
    )


def _collect_repo_rule_docs(paths: ToolkitPaths) -> list[RuleDoc]:
    documents: list[RuleDoc] = []

    for path in sorted(paths.repo_toolkit_dir.rglob("*.md")):
        relative = path.relative_to(paths.repo_toolkit_dir).as_posix()
        if relative == "index.md" or relative.startswith("schema/") or relative.startswith("metrics/"):
            continue
        family = "workflow" if relative == "workflows.md" else (
            "managed_system" if relative == "system.md" else f"managed_rule:{relative.removesuffix('.md')}"
        )
        documents.append(
            _build_rule_doc(
                path,
                display_path=f"ai-wiki/_toolkit/{relative}",
                family=family,
                scope="repo",
            )
        )

    for relative, family in (
        ("constraints.md", "constraints"),
        ("workflows.md", "workflow"),
        ("decisions.md", "decisions"),
    ):
        path = paths.repo_wiki_dir / relative
        if not path.exists():
            continue
        documents.append(
            _build_rule_doc(
                path,
                display_path=f"ai-wiki/{relative}",
                family=family,
                scope="repo",
            )
        )

    for path in sorted(paths.review_patterns_dir.glob("*.md")):
        if path.name == "index.md":
            continue
        documents.append(
            _build_rule_doc(
                path,
                display_path=f"ai-wiki/review-patterns/{path.name}",
                family="pattern",
                scope="repo",
            )
        )

    return documents


def _collect_home_rule_docs(paths: ToolkitPaths) -> list[RuleDoc]:
    documents: list[RuleDoc] = []

    home_managed_system = paths.home_toolkit_dir / "system.md"
    if home_managed_system.exists():
        documents.append(
            _build_rule_doc(
                home_managed_system,
                display_path=_home_display_path(home_managed_system, paths.home_dir),
                family="managed_system",
                scope="home",
            )
        )

    for relative, family in (
        ("preferences.md", "preferences"),
        ("agent-operating-contract.md", "agent_operating_contract"),
    ):
        path = paths.system_dir / relative
        if not path.exists():
            continue
        documents.append(
            _build_rule_doc(
                path,
                display_path=_home_display_path(path, paths.home_dir),
                family=family,
                scope="home",
            )
        )

    playbooks_dir = paths.system_dir / "playbooks"
    if playbooks_dir.exists():
        for path in sorted(playbooks_dir.glob("*.md")):
            documents.append(
                _build_rule_doc(
                    path,
                    display_path=_home_display_path(path, paths.home_dir),
                    family="pattern",
                    scope="home",
                )
            )

    return documents


def _docs_are_comparable(left: RuleDoc, right: RuleDoc) -> bool:
    if left.scope == right.scope and left.family == right.family == "workflow":
        return True
    if left.family != right.family:
        return False
    return bool(left.title_key) and left.title_key == right.title_key


def _ordered_pair(left: RuleDoc, right: RuleDoc) -> tuple[RuleDoc, RuleDoc]:
    def sort_key(doc: RuleDoc) -> tuple[int, str]:
        return (0 if doc.scope == "repo" else 1, doc.display_path)

    ordered = sorted((left, right), key=sort_key)
    return ordered[0], ordered[1]


def _shared_section_labels(left: RuleDoc, right: RuleDoc) -> tuple[list[str], list[str]]:
    duplicate_titles: list[str] = []
    conflicting_titles: list[str] = []
    for key in sorted(set(left.sections).intersection(right.sections)):
        title = left.section_titles.get(key) or right.section_titles.get(key) or key
        if left.sections[key] == right.sections[key]:
            duplicate_titles.append(title)
        else:
            conflicting_titles.append(title)
    return duplicate_titles, conflicting_titles


def _warn_or_info_for_rule_overlap(result: DoctorResult, left: RuleDoc, right: RuleDoc) -> None:
    primary, secondary = _ordered_pair(left, right)
    same_scope = primary.scope == secondary.scope
    duplicate_sections, conflicting_sections = _shared_section_labels(primary, secondary)

    if primary.body_key == secondary.body_key:
        if same_scope:
            _add_finding(
                result,
                severity="WARN",
                code="duplicate_rule_source",
                path=primary.display_path,
                message=(
                    f"`{primary.display_path}` duplicates `{secondary.display_path}`. "
                    "Keep one authoritative same-scope rule source."
                ),
                suggested_fix="Merge or remove one of the duplicate same-scope rule documents.",
            )
        return

    if conflicting_sections:
        section_list = ", ".join(conflicting_sections)
        if same_scope:
            _add_finding(
                result,
                severity="WARN",
                code="conflicting_rule_sections",
                path=primary.display_path,
                message=(
                    f"`{primary.display_path}` and `{secondary.display_path}` define overlapping rule sections "
                    f"with different content: {section_list}."
                ),
                suggested_fix="Repair the conflicting same-scope rule sections so the guidance is consistent.",
            )
            return

        _add_finding(
            result,
            severity="INFO",
            code="cross_scope_rule_conflict",
            path=primary.display_path,
            message=(
                f"`{primary.display_path}` overlaps with `{secondary.display_path}` but differs in sections: "
                f"{section_list}. Repo-local guidance takes precedence."
            ),
        )
        return

    if duplicate_sections:
        if same_scope:
            section_list = ", ".join(duplicate_sections)
            _add_finding(
                result,
                severity="WARN",
                code="duplicate_rule_sections",
                path=primary.display_path,
                message=(
                    f"`{primary.display_path}` and `{secondary.display_path}` repeat the same same-scope rule "
                    f"sections: {section_list}."
                ),
                suggested_fix="Consolidate the duplicated same-scope rule sections into one authoritative document.",
            )
        return

    if primary.family == "workflow" and primary.title_key != secondary.title_key:
        return

    if same_scope:
        _add_finding(
            result,
            severity="WARN",
            code="conflicting_rule_sources",
            path=primary.display_path,
            message=(
                f"`{primary.display_path}` and `{secondary.display_path}` appear to define the same same-scope "
                "rule but differ in content."
            ),
            suggested_fix="Consolidate the same-scope rule into one authoritative document or split the responsibilities clearly.",
        )
        return

    _add_finding(
        result,
        severity="INFO",
        code="cross_scope_rule_conflict",
        path=primary.display_path,
        message=(
            f"`{primary.display_path}` and `{secondary.display_path}` appear to define overlapping cross-scope "
            "rules with different content. Repo-local guidance takes precedence."
        ),
    )


def _check_rule_overlap(result: DoctorResult) -> None:
    documents = _collect_repo_rule_docs(result.paths) + _collect_home_rule_docs(result.paths)
    for left, right in combinations(documents, 2):
        if not _docs_are_comparable(left, right):
            continue
        _warn_or_info_for_rule_overlap(result, left, right)


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


def _check_repo_workflows(result: DoctorResult, starters: dict[str, str]) -> None:
    workflows_path = result.paths.repo_wiki_dir / "workflows.md"
    repo_relative_path = "ai-wiki/workflows.md"
    if not workflows_path.exists():
        _add_finding(
            result,
            severity="WARN",
            code="missing_repo_workflows",
            path=repo_relative_path,
            message="`ai-wiki/workflows.md` is missing.",
            suggested_fix="Create the repo workflows doc using the suggested starter content.",
        )
        _add_suggestion(
            result,
            path=repo_relative_path,
            reason="Repo workflows doc is missing.",
            content=starters["workflows.md"],
            replace_hint="Create this file with the starter content below, then customize it as needed.",
        )
        return

    text = workflows_path.read_text(encoding="utf-8")
    if "_toolkit/workflows.md" in text:
        _add_finding(
            result,
            severity="OK",
            code="repo_workflows_pointer_current",
            path=repo_relative_path,
            message="`ai-wiki/workflows.md` points to the managed baseline workflow doc.",
        )
        return

    _add_finding(
        result,
        severity="WARN",
        code="missing_repo_workflows_pointer",
        path=repo_relative_path,
        message="`ai-wiki/workflows.md` is missing the pointer to `_toolkit/workflows.md`.",
        suggested_fix="Add the managed workflow pointer or merge in the suggested starter content.",
    )
    _add_suggestion(
        result,
        path=repo_relative_path,
        reason="Repo workflows doc is missing the managed workflow pointer.",
        content=starters["workflows.md"],
        replace_hint=(
            "Keep any repo-specific workflow sections, but merge in the starter pointer to "
            "`_toolkit/workflows.md`."
        ),
    )


def _check_required_managed_doc(
    result: DoctorResult,
    *,
    relative_path: str,
    description: str,
) -> None:
    full_path = result.paths.repo_toolkit_dir / relative_path
    display_path = f"ai-wiki/_toolkit/{relative_path}"
    if full_path.exists():
        _add_finding(
            result,
            severity="OK",
            code="managed_doc_present",
            path=display_path,
            message=f"`{display_path}` exists.",
        )
        return

    _add_finding(
        result,
        severity="WARN",
        code="missing_managed_doc",
        path=display_path,
        message=f"`{display_path}` is missing.",
        suggested_fix=f"Run `aiwiki-toolkit install` to refresh the managed {description}.",
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
        for token in (
            "ai-wiki/_toolkit/index.md",
            "ai-wiki/index.md",
            "review-patterns/index.md",
            "people/<handle>/index.md",
        ):
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

    starters = repo_starter_files(resolved_handle)
    _check_required_managed_doc(result, relative_path="index.md", description="toolkit index")
    _check_required_managed_doc(result, relative_path="system.md", description="system rules")
    _check_required_managed_doc(result, relative_path="workflows.md", description="baseline workflows")
    _check_repo_index(result, starters)
    _check_repo_workflows(result, starters)
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
    _check_rule_overlap(result)

    return result
