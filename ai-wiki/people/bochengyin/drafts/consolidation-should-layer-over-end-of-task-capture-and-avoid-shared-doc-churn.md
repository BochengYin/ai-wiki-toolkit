---
title: "Consolidation should layer over end-of-task capture and avoid shared doc churn"
author_handle: "bochengyin"
model: "unknown"
source_kind: "review"
status: "draft"
created_at: "2026-04-20T09:00:17+1000"
updated_at: "2026-05-20T11:20:55+1000"
promotion_candidate: true
promotion_basis: "Auto-marked from useful resolved reuse threshold; exact evidence is generated under ai-wiki/_toolkit/reports/promotion-candidates/latest.md."
promotion_report: "ai-wiki/_toolkit/reports/promotion-candidates/latest.md"
---
# Review Draft

## Context

We considered adding a Karpathy-style memory consolidation feature to `ai-wiki-toolkit` after comparing the current repo-native AI wiki flow with GBrain's documented "dream cycle" and compiled-truth pattern.

The repository already has a layered memory model:

- stable, shared guidance in `ai-wiki/constraints.md`, `ai-wiki/workflows.md`, `ai-wiki/decisions.md`, and `ai-wiki/review-patterns/`
- rawer, more task-local evidence in `ai-wiki/trails/`, `ai-wiki/people/<handle>/drafts/`, and `ai-wiki/metrics/`

What is missing is not the layer split itself, but a repeatable maintenance pass that turns repeated raw observations into better durable guidance.

## What Went Wrong

The tempting design is to run a heavy "consolidate memory" step at the end of every task and let it rewrite shared repo docs directly.

That clashes with the project's hard constraints:

- user-owned AI wiki docs are no-touch by default
- new AI wiki features must remain compatible with normal multi-user git collaboration
- the toolkit does not own a persistent runtime or a guaranteed stream of raw chat/session logs

Without those guardrails, a consolidation feature would create shared-doc churn, noisy merge conflicts, and overconfident rewrites based on weak evidence.

## Bad Example

- Treat consolidation as a replacement for the existing end-of-task update check.
- Rewrite `ai-wiki/workflows.md` or `ai-wiki/review-patterns/*.md` automatically after a single task.
- Assume the toolkit can always inspect full agent conversation history the way an always-on brain system can.
- Make consolidation depend on cron-only infrastructure even though many repo-agent workflows are session-based, not continuously running.

## Fix

Keep the current end-of-task update check as the capture layer and add consolidation as a second-layer maintenance workflow.

That second layer should:

- read repo-visible raw evidence such as drafts, trails, and metrics
- merge or refine handle-local drafts first
- mark promotion candidates only when the existing two-signal gate is satisfied
- avoid direct shared-doc writes by default
- support lazy or periodic triggering rather than forcing a heavy rewrite after every task

The most compatible trigger order is:

1. per-task capture at task end
2. lazy targeted consolidation when a related stable doc is read and looks stale
3. optional batch consolidation on a periodic schedule for users who run always-on agents

## Reuse Assessment

This looks reusable for repo-native agent memory systems that want compounding knowledge without turning collaborative markdown into a conflict magnet.

The durable rule is to separate capture from consolidation, and to treat promotion into shared guidance as a gated synthesis step rather than an automatic side effect of every task.

## Promotion Decision

Keep as a draft for now. Promote if the same capture-vs-consolidation boundary matters again in another repository or if a future consolidation command proves this trigger model in practice.

## 2026-05-20 External Confirmation

Karpathy's May 2026 move to Anthropic and Anthropic's April/May 2026 Managed Agents memory work add a strong external confirmation signal for the same boundary.

Publicly verifiable signals:

- Karpathy joined Anthropic's pre-training team and is reported to be starting work on using Claude to accelerate pre-training research.
- Karpathy's LLM Wiki gist frames persistent Markdown as a compounding artifact that should flag contradictions, stay current, and be linted over time.
- Anthropic's Managed Agents memory stores memories as files with auditability and API control.
- Anthropic's "dreaming" process reviews prior sessions and memory stores, extracts patterns, curates memory, and can keep memory high-signal between sessions.

Product implication for `ai-wiki-toolkit`:

- Treat "memory evolution" as the next layer above capture/reuse: freshness, contradiction detection, provenance, confidence, consolidation, and promotion workflow.
- Keep the repo-native trust model: source Markdown and local evidence remain reviewable, generated consolidation remains disposable, and shared user-owned docs are not rewritten without human confirmation.
- The near-term product surface should be a human-reviewable memory lifecycle queue, not an opaque always-on memory service.
