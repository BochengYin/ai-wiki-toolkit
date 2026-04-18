from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ai_wiki_toolkit.frontmatter import parse_frontmatter
from ai_wiki_toolkit.review_workflow import (
    determine_promotion_basis,
    mark_draft_promotion_candidate,
    promote_review_draft,
    render_review_draft,
    render_review_pattern,
    should_mark_promotion_candidate,
)
from helpers import strip_margin


FIXED_NOW = datetime(2026, 4, 18, 0, 0, tzinfo=timezone.utc)


def test_render_review_draft_snapshot_and_frontmatter() -> None:
    rendered = render_review_draft(
        title="Missing boundary check",
        author_handle="alice",
        explicit_model="gpt-5.4",
        now=FIXED_NOW,
    )

    assert rendered == strip_margin(
        """
        ---
        title: "Missing boundary check"
        author_handle: "alice"
        model: "gpt-5.4"
        source_kind: "review"
        status: "draft"
        created_at: "2026-04-18T00:00:00Z"
        updated_at: "2026-04-18T00:00:00Z"
        promotion_candidate: false
        promotion_basis: "none"
        ---
        # Review Draft

        ## Context

        ## What Went Wrong

        ## Bad Example

        ## Fix

        ## Reuse Assessment

        ## Promotion Decision
        """
    )

    metadata, body = parse_frontmatter(rendered)
    assert metadata["author_handle"] == "alice"
    assert metadata["status"] == "draft"
    assert metadata["promotion_candidate"] is False
    assert body.startswith("# Review Draft")


def test_render_review_pattern_snapshot_and_frontmatter() -> None:
    rendered = render_review_pattern(
        title="Boundary checks before slicing",
        author_handle="alice",
        derived_from="ai-wiki/people/alice/drafts/missing-boundary-check.md",
        promotion_basis="repeat",
        explicit_model="gpt-5.4",
        now=FIXED_NOW,
    )

    assert rendered == strip_margin(
        """
        ---
        title: "Boundary checks before slicing"
        author_handle: "alice"
        model: "gpt-5.4"
        source_kind: "review"
        status: "active"
        created_at: "2026-04-18T00:00:00Z"
        updated_at: "2026-04-18T00:00:00Z"
        derived_from: "ai-wiki/people/alice/drafts/missing-boundary-check.md"
        promotion_basis: "repeat"
        ---
        # Shared Review Pattern

        ## Problem Pattern

        ## Why It Happens

        ## Bad Example

        ## Preferred Pattern

        ## Review Checklist
        """
    )

    metadata, body = parse_frontmatter(rendered)
    assert metadata["status"] == "active"
    assert metadata["derived_from"] == "ai-wiki/people/alice/drafts/missing-boundary-check.md"
    assert body.startswith("# Shared Review Pattern")


def test_determine_promotion_basis_for_repeat_signal() -> None:
    assert determine_promotion_basis(observation_count=2, reviewer_judgment=False) == "repeat"
    assert should_mark_promotion_candidate(observation_count=2, reviewer_judgment=False) is True


def test_determine_promotion_basis_for_reviewer_judgment() -> None:
    assert determine_promotion_basis(observation_count=1, reviewer_judgment=True) == "reviewer_judgment"
    assert should_mark_promotion_candidate(observation_count=1, reviewer_judgment=True) is True


def test_determine_promotion_basis_requires_signal() -> None:
    assert determine_promotion_basis(observation_count=1, reviewer_judgment=False) == "none"
    assert should_mark_promotion_candidate(observation_count=1, reviewer_judgment=False) is False


def test_mark_draft_promotion_candidate_updates_frontmatter_only(tmp_path: Path) -> None:
    draft_path = tmp_path / "draft.md"
    draft_path.write_text(
        render_review_draft(
            title="Missing boundary check",
            author_handle="alice",
            explicit_model="gpt-5.4",
            now=FIXED_NOW,
        ),
        encoding="utf-8",
    )

    changed = mark_draft_promotion_candidate(
        draft_path,
        observation_count=2,
        reviewer_judgment=False,
        now=datetime(2026, 4, 19, 0, 0, tzinfo=timezone.utc),
    )

    assert changed is True
    metadata, body = parse_frontmatter(draft_path.read_text(encoding="utf-8"))
    assert metadata["promotion_candidate"] is True
    assert metadata["promotion_basis"] == "repeat"
    assert metadata["updated_at"] == "2026-04-19T00:00:00Z"
    assert body.startswith("# Review Draft")


def test_promote_review_draft_requires_human_confirmation(tmp_path: Path) -> None:
    draft_path = tmp_path / "draft.md"
    draft_path.write_text(
        render_review_draft(
            title="Missing boundary check",
            author_handle="alice",
            explicit_model="gpt-5.4",
            now=FIXED_NOW,
            promotion_candidate=True,
            promotion_basis="repeat",
        ),
        encoding="utf-8",
    )

    result = promote_review_draft(
        draft_path,
        tmp_path / "review-patterns",
        human_confirmed=False,
        now=FIXED_NOW,
    )

    assert result is None
    assert not (tmp_path / "review-patterns").exists()


def test_promote_review_draft_creates_shared_pattern_after_human_confirmation(
    tmp_path: Path,
) -> None:
    draft_path = tmp_path / "draft.md"
    draft_path.write_text(
        render_review_draft(
            title="Missing boundary check",
            author_handle="alice",
            explicit_model="gpt-5.4",
            now=FIXED_NOW,
            promotion_candidate=True,
            promotion_basis="repeat+reviewer_judgment",
        ),
        encoding="utf-8",
    )

    pattern_path = promote_review_draft(
        draft_path,
        tmp_path / "review-patterns",
        human_confirmed=True,
        now=FIXED_NOW,
    )

    assert pattern_path == tmp_path / "review-patterns" / "missing-boundary-check.md"
    assert pattern_path.exists()
    metadata, _ = parse_frontmatter(pattern_path.read_text(encoding="utf-8"))
    assert metadata["status"] == "active"
    assert metadata["promotion_basis"] == "repeat+reviewer_judgment"
    assert metadata["derived_from"] == draft_path.as_posix()


def test_render_review_draft_uses_unknown_model_when_not_available() -> None:
    rendered = render_review_draft(
        title="Missing boundary check",
        author_handle="alice",
        env={},
        now=FIXED_NOW,
    )
    metadata, _ = parse_frontmatter(rendered)
    assert metadata["model"] == "unknown"
