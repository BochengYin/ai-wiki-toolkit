# Codex Data Audit - 2026-06-27

Audit target:
`<local-writing-worktree>/outputs/`

Raw experiment roots checked:

- `artifacts://swe-chain-019/`
- `artifacts://swe-chain-019-claudecode/`
- `artifacts://swe-chain-020/`
- `artifacts://swe-chain-021/`

## What Checked Out

- `aiwiki_perstep_fp_fn.md`: all 68 valid TP/FP/FN cells matched current raw
  `eval.json`.
- `aiwiki_rate_metrics.md`: recall and regression-rate rows matched recomputed
  `TP/(TP+FN)` and `FP/(FP+TN)`.
- `aiwiki_rate_metrics_merged.md`: net-improvement cells matched recomputation
  against codex raw.
- 020 Flask hook sweep archive table matched the corresponding
  `results_archive/flask_2.0.0_to_2.3.3/*/eval.json` files.

## Required Corrections And Caveats

1. `conan_2.12.0_to_2.20.1 / exact` is a valid partial eval with 14 of 16
   steps. Its F1 `0.4948` is a 14-step partial-chain metric. On overlapping
   steps, raw is F1 `0.4880` and exact is F1 `0.4948`.

2. `xarray_2022.11.0_to_2023.7.0 / native` is a valid partial eval with 9 of
   10 steps. Its `TP=720 / FN=667 / FP=10204` values are correct for those
   scored steps, but must be labeled partial.

3. `aiwiki_perstep_delta_vs_raw*.md` total deltas use overlapping steps when a
   comparison arm is partial. Do not read those deltas as full-chain overall
   differences unless every arm has full step coverage.

4. 020 Flask has two valid stop-hook values:
   - Best stop-only archive `stop-only-strict-20260623T0730`: build+fix
     F1 `0.9953`, precision `1.0`, FP `0`.
   - Current `results/flask/.../eval.json`, pointing to
     `stop-post-strict-20260623T0935`: build+fix F1 `0.9862`, precision
     `0.9817`, FP `2`.

   The stop-only-all run summary skipped Flask and points to the best
   `stop-only-strict-20260623T0730` archive. Report tables must choose and
   state one Flask stop-only source consistently.

5. Some status prose in the local research packet is stale relative to
   current eval files:
   - 021 `conan_2.12.0_to_2.20.1 / exact` now has a partial valid eval.
   - 020 `xarray_2025.6.0_to_2026.2.0 / stop` has a harness-fix valid eval:
     `TP=299 / FN=593 / FP=1173`, F1 `0.2529`.
   - 019-claudecode now has valid `jinja2 / native`, `attrs / raw`, and
     `attrs / init` evals. `attrs / native` was still absent in the checked
     state.

6. FP mechanism wording should be narrower than the early summary:
   - Conan `untargz -> _untargz` is present in `agent_step_diff` and caused a
     real live-patch regression, but it also appears in `gold_diff`.
   - Xarray's `UndefinedVariableError` pandas shim is present in
     `agent_step_diff` and caused an import-collapse regression, but a similar
     shim also appears in `gold_diff`.

   Safe wording: "the live patch produced a true FP regression under the
   SWE-Chain metric." Stronger wording such as "memory made the agent over-edit"
   needs additional evidence, especially when `gold_diff` contains the same
   change.

## Report Data Contract

- Use raw `eval.json` as numeric source of truth.
- Track step coverage for every result cell.
- Exclude 0/0/0 shells from scored tables.
- Label partial evals in every table and chart.
- Separate "mechanism evidence" from "configuration causality"; single-run
  cross-arm rankings are directional only.
- Keep raw JSON/JSONL artifacts out of git unless a tiny, purpose-built excerpt
  is needed for a published appendix.
