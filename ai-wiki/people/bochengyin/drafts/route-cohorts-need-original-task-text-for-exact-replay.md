---
title: "Route cohorts need original task text for exact replay"
author_handle: bochengyin
model: codex
source_kind: implementation_note
status: draft
created_at: 2026-06-04
updated_at: 2026-06-04
promotion_candidate: false
promotion_basis: "Single route-cohort implementation; keep local until repeated."
---

# Route Cohorts Need Original Task Text For Exact Replay

## Problem

Historical `route-trace-v1` rows recorded `task_id`, task type, changed paths, and selected docs, but not the original task prompt. That is enough for aggregate route-noise reporting, but not enough to replay the exact same task through a new scorer.

## Preferred Pattern

Route traces used for precision cohorts should include the original task text, changed-path signal policy, and route quality adjustments. This lets future cohorts compare route behavior without reconstructing prompts from lossy slugs.

For route precision claims, separate:

- historical baseline reports over old traces
- post-change evaluable cohorts with a fixed target count
- projection/replay experiments, which should be labeled as approximate if task text was reconstructed

## 2026-06-04 Replay Follow-Up

`aiwiki-toolkit eval impact route-noise replay` now recovers historical route prompts from local
Codex rollout JSONL and records prompt-recovery confidence in the report. Future route traces also
record best-effort session provenance (`source_session_id`, rollout path, cwd/title preview, and git
metadata) so exact backplay does not depend on slug-only matching.

Treat replay as a diagnostic/falsification tool, not proof of production improvement. The first
57-trace recovered replay found all 57 prompts with high confidence, but the current scorer's
retrospective precision was lower than the historical selected-doc baseline. That result is useful
because it shows the next optimization should inspect why useful historical docs are being missed
before claiming route precision improved.

The first regression diagnosis is recorded at:

```text
evals/impact/reports/route_replay_regression_diagnosis_2026-06-04.md
```

The main findings were: mixed Chinese/English prompts lose most task semantics in lexical routing;
current-catalog replay can select docs that did not exist at the original trace time; old dirty-path
signals explain only part of the historical baseline advantage; and mixed tasks need risk-tag or
multi-signal scoring so release/eval/memory docs are not pushed out by a single primary task type.

A conservative support-aware unused penalty has been added as a guardrail: documents with enough
selected-useful support have raw unused-count penalties capped, while explicit `not_helpful` remains
a strong negative signal. This prevents over-penalizing broadly useful docs but does not resolve the
main replay regression.

`route-noise replay` now supports `--catalog-cutoff trace-routed-at`. Use that mode when judging
historical traces so docs created after the original route are filtered out; keep docs without
`created_at` in the packet but report them as an uncertainty bucket.

The bilingual routing pass should stay conservative. Mapping every Chinese use of "评估" to
`eval_workflow` overclassified prompts that meant "assess this idea" rather than "run an eval
harness." Safer synonym triggers are more machine-eval-specific terms such as "自评估", "评分",
"基准", and "回放"; broader semantic understanding likely needs a reranker over deterministic index
cards rather than more keyword expansion.

The same conservatism applies to ownership-boundary synonyms. Do not map "本地" by itself to
ownership or user-owned-doc risk: in replay, a normal "本地 changes push 到 repo" task was pushed
toward broad index/user-owned docs and lost the historically useful workflows doc. Keep boundary
triggers to stronger phrases such as "公司代码", "隐私", "权限", "用户文档", or "不能覆盖".

The scorer also now has a capped multi-signal boost: release, CI, eval, and memory-governance risk
tags can protect matching docs even when the primary `task_type` points elsewhere. The boost should
require matching doc terms and stay capped, because broad unconditional risk boosts create route
noise quickly.

A deterministic top index-card reranker now runs after initial scoring. It should stay a second
stage over card metadata only: title, short description, routing hint, kind, historical score
signals, and route-quality adjustments. It should not load all full Markdown bodies as a second pass.
Use `--rerank-top 0` for ablations. In the first strict 57-trace replay, default `--rerank-top 20`
nudged precision from `0.349` to `0.350`; this is a small guardrail improvement, not proof that route
precision is fixed.
