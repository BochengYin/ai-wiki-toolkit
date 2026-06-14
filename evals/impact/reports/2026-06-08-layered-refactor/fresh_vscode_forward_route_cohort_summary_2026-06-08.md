# Fresh VS Code Forward Route Cohort Summary

Generated at: `2026-06-08T16:25:00+10:00`

## Executive Summary

This run executed a one-shot fresh VS Code checkout forward route cohort in:

```text
<fresh VS Code checkout path redacted>
```

This is not a Windows OS run. It is a fresh VS Code window/worktree run on the same macOS host.

The cohort recorded real route traces and downstream reuse evidence:

- route traces: `12`
- task checks: `12`
- reuse events: `22`
- route precision: `0.305`
- route recall proxy: `0.818`
- selected docs: `59`
- useful selected docs: `18`
- missed useful docs: `4`
- failed route at selected: `1 / 12 = 0.083`
- failed route at selected+maybe: `1 / 12 = 0.083`

The run says the current router is good at avoiding complete misses in this curated fresh VS Code
cohort, but still noisy: `41 / 59` selected docs had no downstream useful reuse evidence.

## Setup And Verification

Fresh checkout:

- HEAD: `5c3c93d`
- baseline test command: `uv run pytest`
- baseline result before cohort: `346 passed, 1 skipped`

For the actual cohort, route traces were recorded before writing generated report files into the
checkout so dirty eval report paths did not influence route selection.

## Route Metrics

Source reports:

- `evals/impact/reports/2026-06-08-layered-refactor/fresh_vscode_route_noise_report_2026-06-08.md`
- `evals/impact/reports/2026-06-08-layered-refactor/fresh_vscode_route_noise_report_2026-06-08.json`
- `evals/impact/reports/2026-06-08-layered-refactor/fresh_vscode_route_diagnostics_2026-06-08.json`

Summary:

| metric | value |
| --- | ---: |
| route_trace_count | 12 |
| selected_doc_count | 59 |
| useful_selected_doc_count | 18 |
| selected_but_unused_doc_count | 41 |
| useful_doc_count | 22 |
| missed_useful_doc_count | 4 |
| traces_with_missed_useful_docs | 3 |
| route_precision | 0.305 |
| route_recall_proxy | 0.818 |
| route_noise_rate | 0.695 |
| avg_selected_docs | 4.917 |
| avg_packet_words | 1120.417 |

Complete miss analysis:

| metric | value |
| --- | ---: |
| failed_route_at_selected | 1 / 12 = 0.083 |
| failed_route_at_selected+maybe | 1 / 12 = 0.083 |

The failed route was `fvscode-07-postinstall-archive-staging`: route selected
`people/bochengyin/drafts/introducing-new-npm-package-names-needs-a-bootstrap-publish-plan`, while
the useful docs were:

- `people/bochengyin/drafts/npm-postinstall-must-not-delete-its-own-download-archive`
- `people/bochengyin/drafts/workflow-packaging-queue-should-use-evidence-gated-smallest-asset-selection`

## Task-Level Findings

| task | task_type | precision | recall_proxy | missed useful |
| --- | --- | ---: | ---: | ---: |
| `fvscode-07-postinstall-archive-staging` | release_distribution | 0.000 | 0.000 | 2 |
| `fvscode-12-local-forward-summary` | memory_governance | 0.167 | 0.500 | 1 |
| `fvscode-02-route-trace-reuse-pipeline` | memory_governance | 1.000 | 0.500 | 1 |
| `fvscode-01-fresh-checkout-baseline` | eval_workflow | 0.167 | 1.000 | 0 |
| `fvscode-06-source-vs-installed-entrypoint` | general | 0.167 | 1.000 | 0 |
| `fvscode-03-forward-metrics-separation` | eval_workflow | 0.333 | 1.000 | 0 |
| `fvscode-04-scaffold-prompt-workflow-compliance` | scaffold_prompt_workflow | 0.333 | 1.000 | 0 |
| `fvscode-05-ownership-boundary-user-docs` | scaffold_prompt_workflow | 0.333 | 1.000 | 0 |
| `fvscode-08-source-session-provenance` | memory_governance | 0.333 | 1.000 | 0 |
| `fvscode-09-behavior-suite-separate-layer` | memory_governance | 0.333 | 1.000 | 0 |
| `fvscode-10-taxonomy-candidates-no-activation` | workflow_state | 0.333 | 1.000 | 0 |
| `fvscode-11-cjk-task-only-interpretation` | memory_governance | 0.500 | 1.000 | 0 |

## Behavior Suite

Source reports:

- `evals/impact/reports/2026-06-08-layered-refactor/fresh_vscode_behavior_suite_2026-06-08.md`
- `evals/impact/reports/2026-06-08-layered-refactor/fresh_vscode_behavior_suite_2026-06-08.json`

Result:

- case_count: `4`
- check_count: `11`
- failed_case_count: `0`
- failed_check_count: `0`
- blocks_activation: `false`

This is a separate Agent Harness behavior result. It is not part of route retrieval precision.

## Taxonomy Candidates

Source reports:

- `evals/impact/reports/2026-06-08-layered-refactor/fresh_vscode_taxonomy_candidates_2026-06-08.md`
- `evals/impact/reports/2026-06-08-layered-refactor/fresh_vscode_taxonomy_candidates_2026-06-08.json`

Result:

- evidence_events_scanned: `0`
- clusters_considered: `0`
- candidate_count: `0`
- active_taxonomy_changed: `false`

No taxonomy was activated.

## Command Results

All required commands either succeeded or were corrected:

- Fresh checkout baseline `uv run pytest`: `346 passed, 1 skipped`
- Task-local `uv run pytest -q`: passed
- Temporary scaffold install: passed
- Temporary ownership-boundary install and `refresh-metrics`: passed
- Source CLI / module CLI / installed entrypoint version checks: all reported `ai-wiki-toolkit 0.1.39`
- Behavior suite: passed
- Taxonomy candidates: passed with no activation
- Initial `npm pack --dry-run --ignore-scripts` for task 07 failed because it was run in `npm/`, but
  this repo's `package.json` is at the repo root. Corrected command from repo root succeeded.
- Corrected `uv run pytest tests/test_npm_wrapper.py -q`: passed, `5 passed, 1 skipped`

The correction artifact is:

```text
evals/impact/local_experiment/fresh_vscode_postinstall_correction_2026-06-08.json
```

## Comparison To Task-Only Replay

The closest previous task-only replay comparator is the all-58 local replay:

| metric | all-58 task-only replay | fresh VS Code forward |
| --- | ---: | ---: |
| traces | 58 | 12 |
| route_precision | 0.361 | 0.305 |
| selected docs | 296 | 59 |
| useful selected docs | 107 | 18 |
| missed useful docs | 58 | 4 |
| failed_route_at_selected | 13 / 58 = 0.224 | 1 / 12 = 0.083 |

Interpretation:

- Precision is lower in this fresh VS Code run (`0.305` vs `0.361`), mostly because the router still
  selected broad adjacent memory that was not used.
- Complete misses are better in this cohort (`0.083` vs `0.224`), but this is only 12 curated tasks,
  so it should not be overclaimed.
- Missed useful docs are lower in absolute and per-task terms, but forward recall is affected by what
  the agent actually looked up and recorded.

## What This Proves

This run proves that a fresh VS Code checkout can produce route traces, reuse events, task checks,
behavior reports, taxonomy reports, and a local route-noise report end to end.

It also shows that current route behavior can avoid total misses on most fresh tasks in this curated
cohort.

## What This Does Not Prove

This does not prove Windows OS compatibility.

This does not prove the router is better than historical baseline routing. Historical selected-doc
baseline and fresh forward telemetry are different cohorts with different labels and task mix.

This does not prove activation readiness. Precision is still low, and task 07 exposed a concrete
missed-useful failure in npm/postinstall routing.

## Recommendation

Recommendation: `needs_more_evidence`.

Do not activate taxonomy. Do not claim route precision is fixed. The next practical fix should inspect
the task 07 failure and the repeated noisy hotspots before running a larger fresh cohort.
