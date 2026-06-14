# AI Wiki Toolkit Layered Refactor Local Report

Generated at: `2026-06-08T17:45:00+10:00`

Baseline commit: `5c3c93d`
Branch: `codex/route-precision-tooling-reports`

Artifact bundle:

- `evals/impact/reports/2026-06-08-layered-refactor/`

## Executive Summary

This report summarizes the local evidence for the recent route-layer refactor. It uses local data
only, does not activate taxonomy, and does not claim production improvement from old selected-doc
metrics.

The main local signal is:

- Task-only replay precision has moved from the earlier `0.350` strict replay to `0.361` on the
  all-58 replay-evaluable cohort.
- The clean paired pre/post comparison shows the layer refactor did not materially improve
  precision by itself: `0.363 -> 0.361`.
- The same clean comparison shows recall-like behavior improved slightly: selected useful docs
  increased `103 -> 107`, missed useful docs decreased `59 -> 58`, and failed route@selected
  decreased `16/58 -> 13/58`.
- Agent Harness behavior checks passed and do not block shadow validation.
- Taxonomy candidate induction did not activate taxonomy.

Interpretation: keep the layered refactor, but describe the win as better coverage and fewer complete
misses, not as a clean precision win. The next evidence step should be future forward testing in new
real work, not more retrospective tuning alone.

Activation recommendation: `needs_more_evidence`.

Future testing loop recommendation: yes. Run a small forward loop specifically to measure whether
new tasks keep the lower complete-miss rate without letting selected context become too noisy.

## Data Cohort

Local replay cohort:

| metric | value |
| --- | ---: |
| raw route traces | 123 valid JSONL events |
| target_evaluable_traces | 9999 |
| target_trace_count | 58 |
| recovered_trace_count | 58 |
| replayed_trace_count | 58 |
| unmatched_trace_count | 0 |
| prompt recovery confidence | 57 high, 1 low |
| catalog cutoff | trace-routed-at |

Fresh VS Code cohort:

| metric | value |
| --- | ---: |
| route traces | 12 |
| task checks | 12 |
| reuse events | 22 |
| baseline test result | 346 passed, 1 skipped |

The fresh VS Code cohort is not a Windows OS run. It is a brand-new VS Code checkout on the same
macOS host.

## Route Core Results

Task-only replay series:

| run | traces | route_precision | retrieval_precision | selected_useful | missed_useful |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-06-04 strict replay | 57 | 0.350 | n/a | 112 | n/a |
| 2026-06-06 phase-plan replay | 57 | 0.352 | n/a | 102 | 58 |
| 2026-06-07 old strict 57 | 57 | 0.355 | 0.351 | 103 | 58 |
| 2026-06-07 latest 57 | 57 | 0.353 | 0.348 | 104 | 57 |
| 2026-06-08 all evaluable | 58 | 0.361 | 0.358 | 107 | 58 |

Current all-58 route metrics:

| metric | value |
| --- | ---: |
| selected docs | 296 |
| selected useful docs | 107 |
| missed_useful_doc_count | 58 |
| failed_route@selected | 13 / 58 = 0.224 |
| failed_route@selected+maybe | 13 / 58 = 0.224 |
| failed_route@candidate20 | 4 / 58 = 0.069 |
| useful_coverage@selected | 0.467 |
| useful_coverage@selected+maybe | 0.472 |
| useful_coverage@candidate20 | 0.707 |

The candidate pool is doing better than final selected context: `candidate20` coverage is `0.707`,
while selected coverage is `0.467`. The local bottleneck is selection and stage ranking, not only
candidate generation.

## Clean Pre/Post Layer Comparison

The clean paired comparison compares the current layered router against the direct pre-layer parent
on the same 58 prompts and same temporal catalog cutoff.

| version | route_precision | selected_docs | selected_useful | missed_useful | failed_route@selected |
| --- | ---: | ---: | ---: | ---: | ---: |
| pre-layer parent `1aa3a26` | 0.363 | 284 | 103 | 59 | 16 / 58 |
| current layered `5c3c93d` | 0.361 | 296 | 107 | 58 | 13 / 58 |

This is the key precision/recall tradeoff. Precision is essentially flat and slightly lower, but the
router selected more useful docs and reduced complete misses. In retrieval terms, the refactor looks
like a small recall/coverage improvement, not a precision improvement.

## Route Ablation Findings

The all-58 ablation run compared current against `no_reranker`,
`no_route_quality_history`, `no_eval_bucket_selector`, and eval-stage variants.

| variant | route_precision | retrieval_precision | missed_useful | failed_route@selected+maybe | candidate20 coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| current | 0.361 | 0.358 | 58 | 0.224 | 0.707 |
| eval_stage_shadow | 0.361 | 0.358 | 58 | 0.224 | 0.707 |
| eval_stage_soft_scoring | 0.368 | 0.362 | 59 | 0.207 | 0.725 |
| stage_compatible_doc_slots | 0.358 | 0.352 | 60 | 0.190 | 0.707 |
| no_eval_bucket_selector | 0.353 | 0.337 | 56 | 0.172 | 0.707 |
| no_reranker | 0.350 | 0.336 | 61 | 0.224 | 0.707 |
| no_route_quality_history | 0.360 | 0.353 | 59 | 0.155 | 0.734 |

Findings:

- `no_reranker` is the clearest precision and missed-useful regression. That supports keeping the
  reranker.
- `no_eval_bucket_selector` reduces missed useful docs but loses precision sharply. It is not a
  clean win.
- `no_route_quality_history` improves failed-route rate but loses retrieval precision and adds one
  missed useful doc. It is a diagnostic signal, not an activation candidate.
- `eval_stage_soft_scoring` slightly improves precision and candidate coverage, but adds one missed
  useful doc. It is the most plausible next shadow candidate, not something to activate directly.

The ablation results support keeping the layered architecture, but they do not identify a
non-regressing selector change ready to ship.

## Agent Harness Results

Agent Harness is evaluated separately from retrieval precision.

| metric | value |
| --- | ---: |
| suite | phase-plan-shadow-behavior-suite-2026-06-06 |
| case_count | 4 |
| check_count | 11 |
| failed_case_count | 0 |
| failed_check_count | 0 |
| behavior_pass_rate | 1.000 |
| blocks activation | false |

Failure source classification: none.

This proves the local phase/workflow behavior checks passed. It does not prove route retrieval
precision improved.

## Feedback Loop Local Findings

Taxonomy candidate induction:

| metric | value |
| --- | ---: |
| evidence_events_scanned | 3 |
| cluster_count | 2 |
| candidate_count | 1 |
| Gate 1 status | passed |
| Gate 2 status | not_run |
| active_taxonomy_changed | false |

The local candidate is inactive. Gate 2 was not supplied or run, so this supports shadow validation
planning only. It does not support taxonomy activation.

Fresh VS Code taxonomy induction scanned `0` evidence events and produced `0` candidates. It also
kept `active_taxonomy_changed=false`.

## Fresh VS Code Forward Signal

The fresh VS Code run produced real route traces and downstream reuse evidence:

| metric | value |
| --- | ---: |
| route traces | 12 |
| route_precision | 0.305 |
| route_recall_proxy | 0.818 |
| selected docs | 59 |
| useful selected docs | 18 |
| missed useful docs | 4 |
| failed_route@selected | 1 / 12 = 0.083 |

This is a useful smoke signal because complete misses are low in a fresh checkout. It is not a
replacement for the replay cohort because it is only 12 curated tasks and a different task mix.

## What Can Be Concluded From Local Data

- The current layered router can replay all 58 locally replay-evaluable traces with recovered
  prompts and a temporal catalog cutoff.
- The recent route work improved the task-only replay series modestly, from around `0.35` precision
  to `0.361`.
- The direct layer refactor effect is mostly recall-like: more useful selected docs and fewer
  complete route misses, with slightly lower precision.
- The reranker appears worth keeping because removing it worsens precision and missed useful docs.
- Behavior harness checks pass and should remain a separate activation gate from retrieval metrics.
- Taxonomy induction is non-destructive locally; no taxonomy was activated.

## What Cannot Be Concluded Without Future Forward Testing

- This does not prove production precision is fixed.
- This does not prove the fresh VS Code cohort will generalize beyond 12 curated tasks.
- This does not prove Windows OS behavior.
- This does not justify taxonomy activation because Gate 2 is not run.
- This does not justify treating behavior pass rate as route retrieval precision.
- This does not identify a selector ablation that is ready to activate without further validation.

## Activation Recommendation

Recommendation: `needs_more_evidence`.

Keep the layered refactor and continue future testing. The next loop should track forward tasks with:

- route precision
- recall proxy
- missed useful docs
- failed_route@selected
- selected-but-unused hotspots
- behavior-suite pass/fail as a separate layer

The target is not simply higher top-k recall. The target is high-recall candidate discovery plus
sparse, high-signal selected context that does not increase wrong-stage noise.
