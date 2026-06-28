# Metrics

Raw SWE-Chain `eval.json` uses confusion-matrix labels. The report uses
software-testing terminology so readers do not confuse repo memory with ML
training.

| Raw label | Report term |
|---|---|
| `TP` | fixed target behavior |
| `FN` | missed target behavior |
| `FP` | introduced unrelated regression |
| `TN` | preserved unrelated behavior |

Primary reader-facing metrics:

- `target fix rate = fixed target behavior / (fixed target behavior + missed target behavior)`
- `unrelated-behavior preservation rate = preserved unrelated behavior / (preserved unrelated behavior + introduced unrelated regression)`
- `introduced unrelated regression rate = introduced unrelated regression / (introduced unrelated regression + preserved unrelated behavior)`
- `net = delta_target_fix_rate - delta_introduced_unrelated_regression_rate`

Step coverage must be counted by unique `(prev_version, next_version)` pairs,
not by phase rows in `eval.json.chain[]`.
