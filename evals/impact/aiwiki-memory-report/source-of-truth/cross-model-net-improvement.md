# Cross-Model Net Improvement Table

Primary report-level table for cross-repo comparisons.

Source material:
audited merged-rate source material, promoted from ignored local drafting
material into this table.

Audit status:
`../audits/codex-data-audit-20260627.md` confirmed this table's net-improvement
cells against raw `eval.json` on 2026-06-27. The table was refreshed after the
2026-06-28 resume and exact-fill completions.

Metric:
each non-reference cell is `net (delta_target_fix_rate /
delta_introduced_unrelated_regression_rate)` in percentage points, where
`net = delta_target_fix_rate - delta_introduced_unrelated_regression_rate`.
This is equivalent to `delta_target_fix_rate +
delta_unrelated_behavior_preservation_rate`.

Terminology:
the raw SWE-Chain evaluator uses `TP`/`FN`/`FP`/`TN`, but report prose should
use IT terms: fixed target behavior, missed target behavior, introduced
unrelated regression, and preserved unrelated behavior. AI Wiki memory in this
report is not ML model training, so the reader-facing report avoids
confusion-matrix labels.

Baseline:
all groups are compared to codex raw for the same repo. Claude Code rows are
therefore total deltas versus codex raw, not Claude-internal intervention
effects.

Scale columns:
`steps` counts unique migration pairs in the codex raw reference eval.
`raw ref scored tests` sums the reference build+fix `evaluated` counts across
those steps. This is a scored test-outcome count, not a de-duplicated count of
test files or test function names.

Coverage caveats:

- Empty 0/0/0 eval shells are excluded.
- There are no known partial cells in this table after the 2026-06-28 resume
  refresh.

| repo | steps | raw ref scored tests | difficulty | codex-raw ref (target fix / unrelated regression) | init | native | stop | exact | raw-cc | init-cc | native-cc |
|---|---:|---:|---:|---|---|---|---|---|---|---|---|
| xarray_2022.11.0_to_2023.7.0 | 10 | 102,608 | 0.866 | 96%/0% | -16.8 (-13.9/+2.9) | -55.2 (-43.9/+11.3) | -11.3 (-5.1/+6.2) | -7.3 (-5.9/+1.4) | - | - | - |
| conan_2.12.0_to_2.20.1 | 16 | 53,786 | 0.544 | 41%/0% | +1.5 (+1.5/+0.0) | -3.4 (+1.7/+5.0) | -21.9 (-21.8/+0.1) | +1.7 (+1.7/-0.0) | - | - | - |
| conan_2.23.0_to_2.28.1 | 11 | 41,852 | 0.484 | 40%/1% | -4.8 (-4.8/-0.0) | -11.2 (-9.5/+1.6) | -8.0 (-7.9/+0.0) | +0.8 (+0.8/+0.0) | - | - | - |
| pytest_8.0.0_to_8.3.5 | 12 | 30,400 | 0.456 | 74%/0% | +9.0 (+9.1/+0.0) | -1.9 (-2.1/-0.1) | -1.6 (-1.2/+0.3) | +6.2 (+6.2/-0.0) | - | - | - |
| poetry_1.5.0_to_1.8.5 | 10 | 10,710 | 0.404 | 60%/0% | +4.8 (+4.8/+0.0) | +3.1 (+3.1/+0.0) | -21.1 (-21.1/+0.0) | +2.1 (+2.1/-0.0) | - | - | - |
| urllib3_2.0.7_to_2.6.3 | 12 | 15,708 | 0.263 | 56%/10% | +26.2 (+17.3/-8.9) | +26.7 (+17.3/-9.4) | +27.5 (+17.9/-9.5) | +19.7 (+10.3/-9.5) | +52.0 (+42.3/-9.7) | +39.2 (+29.5/-9.7) | +36.2 (+26.9/-9.3) |
| pytest_7.0.0_to_7.4.4 | 16 | 36,860 | 0.246 | 58%/2% | +22.1 (+20.8/-1.3) | -7.2 (-3.1/+4.1) | +20.0 (+18.6/-1.4) | +19.8 (+18.6/-1.2) | +22.3 (+20.8/-1.5) | +24.0 (+22.6/-1.4) | +19.6 (+18.1/-1.5) |
| attrs_21.3.0_to_26.1.0 | 13 | 11,826 | 0.195 | 72%/0% | -3.4 (-2.7/+0.6) | -0.0 (+0.2/+0.2) | -1.0 (-0.8/+0.2) | -1.0 (-1.0/0.0) | +13.4 (+13.3/-0.0) | +0.8 (+0.8/-0.0) | +13.8 (+13.7/-0.0) |
| flask_2.0.0_to_2.3.3 | 17 | 5,708 | 0.150 | 100%/0% | -5.5 (-5.6/-0.0) | -4.6 (-4.6/+0.0) | -0.9 (-0.9/+0.0) | -35.9 (-26.9/+9.0) | +0.0 (0.0/-0.0) | +0.0 (0.0/-0.0) | -0.9 (-0.9/-0.0) |
| jinja2_2.8_to_2.10.3 | 12 | 3,878 | 0.135 | 91%/0% | -1.7 (-0.8/+0.9) | -14.2 (-13.0/+1.2) | +1.6 (+1.5/-0.0) | -3.9 (-3.8/+0.1) | -20.8 (-20.6/+0.2) | -12.9 (-13.0/-0.1) | -13.6 (-13.7/-0.1) |
| pyjwt_2.0.0_to_2.12.1 | 15 | 2,702 | 0.000 | 96%/0% | +0.8 (+0.8/0.0) | -5.6 (-5.6/0.0) | -8.9 (-8.9/0.0) | -3.2 (-3.2/0.0) | - | - | - |

Interpretation notes:

- This table is good for the report's main "no single winner" and
  "native/writeback is not consistently positive" claims.
- Do not use this table alone to claim a causal effect for 020 stop-only; 019
  native and 020 stop-only are not a clean A/B.
- Do not use the Claude Code columns to claim Claude-internal treatment effects;
  use family-specific tables for that.
