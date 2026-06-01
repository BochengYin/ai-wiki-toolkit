---
title: "External AI wiki metrics need a proof stack, not a dashboard"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "design"
status: "draft"
created_at: "2026-05-28T20:34:28+1000"
updated_at: "2026-05-28T21:10:00+1000"
promotion_candidate: false
promotion_basis: "none"
---
# Review Draft

## Context

The user feels `ai-wiki-toolkit` is useful, but lacks metrics that can explain that usefulness to other people.

Existing toolkit evidence already includes task-level reuse checks, document-level reuse events, usefulness reports, memory diagnostics, promotion candidates, and artifact-backed impact evals. The product gap is not raw telemetry. The gap is an external proof stack that separates internal health signals from defensible outcome claims.

## Design Clarification

Do not lead with vanity analytics such as number of Markdown files, raw docs referenced, total reuse events, or claimed token savings. Those are adoption or instrumentation signals, not proof that the product is good.

Use a three-layer proof stack:

1. **Workflow coverage:** show that the memory workflow is actually being followed. Examples: task checks recorded, write-back checks completed, tasks with references, user-owned docs referenced, and coverage gaps.
2. **Memory and routing quality:** show whether the system is selecting useful context without creating noise. Examples: useful reuse ratio, `not_helpful` rate, stale/conflicting/noisy memory, route precision, route recall proxy, missed useful docs, and context cost.
3. **Outcome impact:** show whether fresh agents avoid repeated historical mistakes. Examples: first-pass success improvement in no-AI-wiki versus ambient-AI-wiki evals, wrong-path avoidance, reduced rework, change-profile quality, and artifact-derived saved active minutes.

The strongest external claim should be based on outcome impact, not routine telemetry. A good public headline is:

> In artifact-backed replays of real historical repo failures, ambient AI wiki memory helped fresh agents avoid repeated mistakes on the first pass.

Current dogfood numbers can support a case-study style claim, such as 4 of 5 historical families directionally favoring the ambient AI wiki workflow with one neutral family and zero families favoring the no-AI-wiki workflow. That should be labeled as a pilot, not a statistically powered benchmark.

## Product Shape

Split reporting surfaces by audience:

- **Public evidence page:** small case-study scorecard from impact eval artifacts, with primary comparisons, caveats, artifacts, and no overclaiming.
- **Local operator report:** workflow coverage, reuse checks, docs referenced, high-ROI docs, coverage gaps, and promotion candidates.
- **Memory quality review queue:** stale, noisy, conflicting, missed, and promotion-candidate memory that needs human judgment.
- **Route quality diagnostics:** route trace versus actual downstream reuse once route traces are recorded.

Do not make the weekly HTML report a full analytics dashboard by default. Keep it focused on self-involving human review items. Put raw counts and audit data in JSON or supporting Markdown reports.

## README Placement Refinement

The repository README is a good default entrypoint for the public evidence page because it is where new users evaluate whether the toolkit is worth trying.

Keep the README evidence section concise:

- one aggregate primary comparison
- one family table with no-AI-wiki versus ambient-AI-wiki outcomes
- links to artifact-backed notes or the full pilot write-up
- an explicit caveat that the result is a dogfooded pilot, not a statistically powered benchmark

Do not move the full eval write-up into the README. Keep detailed protocol, timing, caveats, and artifacts under `evals/impact/public/` or other eval-specific paths, then link from the README.

## README Rewrite Refinement

When the README is too long, split it by audience:

- README: product positioning, problem, user-visible benefits, proof, quickstart, workflow, safety model, core commands, and links.
- `docs/usage.md`: detailed command workflows for routing, reuse evidence, source incident timing, work ledger, diagnostics, reports, consolidation, promotion, impact evals, and uninstall.

This keeps the public entrypoint readable while preserving the operational reference material.

## Metric Ladder

Suggested top-line metrics:

- **Repeated mistake avoidance rate:** in historical replay families, how often ambient AI wiki avoids a known failure that the no-AI-wiki control repeats or only partially fixes.
- **First-pass outcome delta:** `success/partial/fail` difference between no-AI-wiki and ambient-AI-wiki primary slots.
- **High-value memory hit rate:** tasks where memory caused `changed_plan`, `blocked_wrong_path`, `avoided_retry`, `preserved_ownership_boundary`, or similar material effects.
- **Useful reuse ratio:** resolved reuse divided by resolved plus partial plus not_helpful reuse.
- **Coverage rate:** completed tasks with an explicit reuse check and write-back check.
- **Route quality:** useful selected docs divided by selected docs, useful selected docs divided by all useful docs found for the task, selected-but-unused docs, missed useful lookup docs, and context word/doc count.
- **Rework-adjusted saved active minutes:** source incident active-turn estimate minus ambient AI wiki replay duration, labeled as artifact-derived active-time context rather than exact human time saved.
- **Change-profile quality:** whether AI wiki reduces wrong-surface edits, unnecessary user-owned wiki churn, or extra implementation footprint when success rate is neutral.

## Implication

The near-term product work should not be "add more metrics" in the abstract. It should package existing evidence into a defensible proof stack:

1. improve or publish the impact-eval public scorecard
2. keep usefulness and diagnosis reports as local operator evidence
3. add route traces so route quality can be measured directly
4. present saved-time claims conservatively and only when backed by source incident and replay artifacts
