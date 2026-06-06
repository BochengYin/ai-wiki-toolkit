# Route Replay Regression Diagnosis

- Generated from: `evals/impact/reports/historical_route_replay_2026-06-04.json`
- Cohort: latest 57 pre-change evaluable route traces before `2026-06-04T08:20:53+10:00`
- Prompt recovery: 57/57 recovered, all high confidence

## Summary

The replay regression is not a session-recovery problem. Historical prompts were recovered
successfully. The issue is that the current lexical router, current catalog, and historical reuse
ground truth are not aligned enough for a direct "new scorer is better" claim.

Baseline historical precision was `0.535`; strict temporal replay precision with the current scorer
is `0.350`. Replay noise is `0.650`.

The current replay now uses `--catalog-cutoff trace-routed-at`, which filters known docs created
after each historical trace. That makes the metric stricter and more trustworthy than the earlier
current-catalog replay.

The current router also uses a deterministic top index-card reranker over the first 20 candidates.
This is a card-metadata pass, not a full-document LLM reranker: it adjusts the already-scored
candidate cards using title, short description, routing hint, kind, and existing scores.

## Quantified Findings

### Prompt Language

Chinese or mixed Chinese prompts regressed more sharply:

| prompt bucket | traces | baseline precision | replay precision |
| --- | ---: | ---: | ---: |
| CJK present | 25 | 0.507 | 0.265 |
| no CJK | 32 | 0.556 | 0.407 |

The router now has a conservative Chinese/English task synonym map for route, eval, release, CI, and
memory-governance terms. It intentionally does not treat every Chinese use of "评估" as
`eval_workflow`, because many historical prompts used that word to mean "assess this idea" rather
than "run an eval harness." Chinese and mixed prompts still lag because lexical routing cannot
recover conversational context such as "now code it" from the single route prompt alone.

Route JSON packets and route traces now expose `language_signals`, including matched Chinese terms
and expanded scorer tokens. This makes bilingual routing failures diagnosable without re-tokenizing
the original prompt from logs.

Earlier tokenization dropped most Chinese task semantics. For example, the prompt:

```text
为 aiwiki-toolkit 设计 evaluate repo 自评估与改进建议命令的详细实施步骤，用户先要计划不要代码
```

reduces mostly to:

```text
aiwiki-toolkit, evaluate, repo
```

That makes route choose broad repo/toolkit docs instead of the historically useful metrics and
evaluation docs.

### Temporal Catalog Leakage

Earlier replay used the current catalog, including docs created after some historical route traces.

- Strict temporal replay filtered known future docs: 479
- Selected future docs after filtering: 0
- Selected docs without `created_at`: 87
- Catalog docs without `created_at`: 17

Temporal cutoff fixes the eval fairness problem. It does not, by itself, close the gap to the
historical baseline because many remaining misses are semantic/contextual rather than future-doc
leakage.

### Dirty Path Signal

Old route traces were produced before implicit `git status` paths were removed from specific-task
scoring. Passing the old trace `changed_paths` back as explicit signals improved replay precision
from `0.354` to about `0.405`.

That means dirty-path removal explains part of the regression against historical traces. It does not
explain the full gap to the historical baseline of `0.535`.

### Route Quality Adjustment

The new route-quality adjustment is not the primary cause:

| variant | replay precision |
| --- | ---: |
| current scorer before temporal cutoff | 0.354 |
| no route-quality adjustment | 0.345 |
| missed-useful bonus only | 0.358 |
| lower penalty caps | 0.356 |
| support-aware unused penalty | 0.353 |
| strict temporal replay with bilingual + multi-signal scorer | 0.349 |
| strict temporal replay with deterministic top-card reranker | 0.350 |

However, raw penalty counts can still suppress specific high-value docs. Example: the Windows ARM
smoke note was historically useful 7 times in this cohort but can receive a large penalty from
not-helpful and selected-but-unused history.

A conservative support-aware unused penalty now caps raw unused-count penalties when a document has
enough selected-useful support. It is a guardrail against over-penalizing broadly useful docs, not a
fix for the main replay regression.

### Task Type And Mixed Tasks

Task-type changes are not the sole cause:

| bucket | traces | baseline precision | replay precision |
| --- | ---: | ---: | ---: |
| task type unchanged | 27 | 0.541 | 0.403 |
| task type changed | 30 | 0.529 | 0.296 |

Mixed tasks are still a real issue, but the scorer now uses risk-tag signals to protect release, CI,
eval, and memory-governance docs when the primary task type points elsewhere. The protection is
capped and requires matching doc terms, so it is a guardrail rather than an unconditional broad-doc
boost. A deterministic index-card reranker then adjusts the top candidate cards before final
selection.

Per-card packet fields now include `multi_signal_adjustment`, `multi_signal`, and
`route_quality_signal`, so future reports can attribute score movement to risk protection,
support-aware penalties, missed-useful bonuses, or rerank changes separately.

### Doc-Level Hotspots

Replay-selected docs with low historical precision:

| doc | replay useful / selected |
| --- | ---: |
| `people/bochengyin/drafts/source-incident-timing-needs-provenance` | 3 / 26 |
| `workflows` | 3 / 20 |
| `decisions` | 3 / 16 |
| `people/bochengyin/drafts/neutral-impact-eval-runs-need-change-profile-quality-metrics` | 1 / 8 |
| `people/bochengyin/drafts/linux-release-binaries-need-runtime-checks-against-an-older-glibc-baseline` | 1 / 7 |

Historically useful docs most often lost by replay:

| doc | useful hits lost |
| --- | ---: |
| `problems/windows-arm-smoke-version-checks-need-full-cli-output` | 7 |
| `people/bochengyin/drafts/external-ai-wiki-metrics-need-a-proof-stack-not-a-dashboard` | 7 |
| `constraints` | 6 |
| `people/bochengyin/drafts/manual-impact-evals-need-visible-session-export-and-first-pass-cutoff` | 6 |
| `people/bochengyin/drafts/workflow-primary-impact-evals-compare-working-modes` | 6 |
| `people/bochengyin/drafts/route-usefulness-eval-needs-route-traces-and-actual-use-comparison` | 6 |
| `people/bochengyin/drafts/workflow-packaging-queue-should-use-evidence-gated-smallest-asset-selection` | 6 |

## Likely Root Causes

1. The router is still mostly lexical. It does not understand Chinese task semantics or synonyms well
   enough, so mixed-language prompts collapse into a few generic English tokens.
2. Single `task_type` scoring is too brittle for mixed tasks. Risk tags identify release, eval, and
   memory-governance concerns, but they do not yet protect the corresponding high-value docs when
   the main task type points elsewhere.
3. Retrospective replay uses a current catalog against historical reuse ground truth. Docs created
   later, or docs that would have been useful but were not historically consulted, are counted as
   noise.
4. Some draft first paragraphs become broad `short_description` text, which gives high path/title
   scores to general eval-adjacent docs. Removing short descriptions alone did not fix the metric,
   but broad generated descriptions are still a noise source.
5. Route-quality penalties should not rely only on raw selected-unused or not-helpful counts. They
   need a precision/support view so frequently useful docs are not over-penalized for being broad.

## Recommended Next Experiments

1. Keep strict replay as the default analysis posture:
   use `--catalog-cutoff trace-routed-at`, and treat selected docs without `created_at` as an
   explicit uncertainty bucket.
2. Add richer replay diagnosis sections directly to the generated report: language bucket, task-type
   transition, doc-level lost useful docs, new noisy docs, and ablation summaries.
3. Treat Chinese/English synonym routing and deterministic card reranking as first-pass guards only.
   The next meaningful improvement is likely an LLM or embedding reranker over top deterministic
   index cards, especially for prompts that depend on prior conversation context.
4. Curate `applies_when` / `routing_hint` for high-impact docs and stop treating the first body
   paragraph as strong path/title evidence for drafts.
