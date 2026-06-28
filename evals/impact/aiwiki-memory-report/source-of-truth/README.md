# Report-Level Source Of Truth

These files are the tables to cite first while reporting the AI Wiki memory
report. They are lighter than the raw SWE-Chain artifacts but stricter than the
ignored local drafting materials.

## Tables

- `buildfix-absolute-metrics.md` - absolute build+fix target-fix,
  missed-target, and introduced-unrelated-regression counts plus precision,
  recall, and F1 for every valid eval cell discovered in the audited result
  roots. Use this when the report needs raw counts or F1 rather than delta.
- `cross-model-net-improvement.md` - main cross-repo, cross-group net
  improvement table. This is based on audited merged-rate source material and
  keeps the codex-raw baseline convention.
- `020-flask-hook-ablation.md` - 020 lifecycle-hook ablation table for the
  single Flask chain. Keep this separate from cross-repo stop-only results.
- `coverage-status.md` - validity map for discovered eval cells, including
  empty `0/0/0` shells and any partial runs. Check this before citing a new
  cell.

## Local Material Not Promoted

Ignored local working material may contain detailed per-step tables, narrative
notes, or mixed analysis/status prose. Use it only as local working context
until a specific table is audited and promoted into `source-of-truth/`.

## Contract

- Raw `eval.json` remains the measurement source of truth.
- These Markdown tables are the report source of truth after the 2026-06-27
  audit and the 2026-06-28 resume/exact-fill refresh.
- Preserve partial-run labels and footnotes when copying into the report if a
  future run is still partial.
- Do not mix 020 Flask hook-ablation cells with 020 cross-repo stop-only cells.

## Reader-Facing Terminology

The raw SWE-Chain evaluator uses `TP`, `FN`, `FP`, and `TN`, but the report
should use software-testing terms in prose and public tables. AI Wiki memory in
this report is not ML model training; the measurements are test-behavior
outcomes from real repository-upgrade tasks.

| Raw label | Report term |
|---|---|
| `TP` | `fixed target behavior` |
| `FN` | `missed target behavior` |
| `FP` | `introduced unrelated regression` |
| `TN` | `preserved unrelated behavior` |

Prefer `target fix rate` and `unrelated-behavior preservation rate` in
reader-facing prose. Use `introduced unrelated regression rate` only when a
cost-oriented metric is needed, and avoid the ambiguous shorthand
`regression rate`.
