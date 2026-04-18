"""Review draft and shared pattern helpers."""

from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from ai_wiki_toolkit.frontmatter import parse_frontmatter, render_frontmatter, replace_frontmatter
from ai_wiki_toolkit.paths import resolve_model_name, slugify


def utc_now_string(now: datetime | None = None) -> str:
    current = now or datetime.now(timezone.utc)
    return current.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def determine_promotion_basis(
    observation_count: int = 1, reviewer_judgment: bool = False
) -> str:
    has_repeat_signal = observation_count >= 2
    if has_repeat_signal and reviewer_judgment:
        return "repeat+reviewer_judgment"
    if has_repeat_signal:
        return "repeat"
    if reviewer_judgment:
        return "reviewer_judgment"
    return "none"


def should_mark_promotion_candidate(
    observation_count: int = 1, reviewer_judgment: bool = False
) -> bool:
    return determine_promotion_basis(observation_count, reviewer_judgment) != "none"


def draft_frontmatter(
    title: str,
    author_handle: str,
    model: str,
    created_at: str,
    updated_at: str,
    promotion_candidate: bool = False,
    promotion_basis: str = "none",
) -> OrderedDict[str, object]:
    metadata: OrderedDict[str, object] = OrderedDict()
    metadata["title"] = title
    metadata["author_handle"] = author_handle
    metadata["model"] = model
    metadata["source_kind"] = "review"
    metadata["status"] = "draft"
    metadata["created_at"] = created_at
    metadata["updated_at"] = updated_at
    metadata["promotion_candidate"] = promotion_candidate
    metadata["promotion_basis"] = promotion_basis
    return metadata


def pattern_frontmatter(
    title: str,
    author_handle: str,
    model: str,
    created_at: str,
    updated_at: str,
    derived_from: str,
    promotion_basis: str,
) -> OrderedDict[str, object]:
    metadata: OrderedDict[str, object] = OrderedDict()
    metadata["title"] = title
    metadata["author_handle"] = author_handle
    metadata["model"] = model
    metadata["source_kind"] = "review"
    metadata["status"] = "active"
    metadata["created_at"] = created_at
    metadata["updated_at"] = updated_at
    metadata["derived_from"] = derived_from
    metadata["promotion_basis"] = promotion_basis
    return metadata


def render_review_draft(
    title: str,
    author_handle: str,
    explicit_model: str | None = None,
    env: Mapping[str, str] | None = None,
    now: datetime | None = None,
    promotion_candidate: bool = False,
    promotion_basis: str = "none",
) -> str:
    timestamp = utc_now_string(now)
    metadata = draft_frontmatter(
        title=title,
        author_handle=author_handle,
        model=resolve_model_name(explicit_model=explicit_model, env=env),
        created_at=timestamp,
        updated_at=timestamp,
        promotion_candidate=promotion_candidate,
        promotion_basis=promotion_basis,
    )
    body = """# Review Draft

## Context

## What Went Wrong

## Bad Example

## Fix

## Reuse Assessment

## Promotion Decision
"""
    return f"{render_frontmatter(metadata)}\n{body}"


def render_review_pattern(
    title: str,
    author_handle: str,
    derived_from: str,
    promotion_basis: str,
    explicit_model: str | None = None,
    env: Mapping[str, str] | None = None,
    now: datetime | None = None,
) -> str:
    timestamp = utc_now_string(now)
    metadata = pattern_frontmatter(
        title=title,
        author_handle=author_handle,
        model=resolve_model_name(explicit_model=explicit_model, env=env),
        created_at=timestamp,
        updated_at=timestamp,
        derived_from=derived_from,
        promotion_basis=promotion_basis,
    )
    body = """# Shared Review Pattern

## Problem Pattern

## Why It Happens

## Bad Example

## Preferred Pattern

## Review Checklist
"""
    return f"{render_frontmatter(metadata)}\n{body}"


def mark_draft_promotion_candidate(
    draft_path: Path,
    observation_count: int = 1,
    reviewer_judgment: bool = False,
    now: datetime | None = None,
) -> bool:
    current = draft_path.read_text(encoding="utf-8")
    metadata, _ = parse_frontmatter(current)
    basis = determine_promotion_basis(observation_count, reviewer_judgment)
    metadata["promotion_candidate"] = basis != "none"
    metadata["promotion_basis"] = basis
    metadata["updated_at"] = utc_now_string(now)
    updated = replace_frontmatter(current, metadata)
    if updated == current:
        return False
    draft_path.write_text(updated, encoding="utf-8")
    return True


def promote_review_draft(
    draft_path: Path,
    patterns_dir: Path,
    human_confirmed: bool = False,
    now: datetime | None = None,
) -> Path | None:
    current = draft_path.read_text(encoding="utf-8")
    metadata, _ = parse_frontmatter(current)
    if not human_confirmed or not metadata.get("promotion_candidate"):
        return None

    title = str(metadata.get("title", draft_path.stem))
    author_handle = str(metadata.get("author_handle", "unknown"))
    model = str(metadata.get("model", "unknown"))
    promotion_basis = str(metadata.get("promotion_basis", "none"))
    derived_from = draft_path.as_posix()
    rendered = render_review_pattern(
        title=title,
        author_handle=author_handle,
        derived_from=derived_from,
        promotion_basis=promotion_basis,
        explicit_model=model,
        now=now,
    )

    patterns_dir.mkdir(parents=True, exist_ok=True)
    pattern_path = patterns_dir / f"{slugify(title)}.md"
    pattern_path.write_text(rendered, encoding="utf-8")
    return pattern_path
