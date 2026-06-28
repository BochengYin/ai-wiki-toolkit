# 020 Flask Hook Ablation Table

Primary report-level table for the 020 lifecycle-hook ablation.

Scope:
single repo chain `flask_2.0.0_to_2.3.3`, codex / openai / gpt-5.5, build+fix
metric.

Raw source:
`artifacts://swe-chain-020/groups/aiwiki-lifecycle-hooks/results_archive/flask_2.0.0_to_2.3.3/<variant>/eval.json`

Audit status:
`../audits/codex-data-audit-20260627.md` confirmed these archive values against
raw `eval.json`.

Net metric:
`net (delta_target_fix_rate / delta_introduced_unrelated_regression_rate)` uses
the same convention as `cross-model-net-improvement.md`: percentage-point deltas
versus codex raw for the same Flask chain, with
`net = delta_target_fix_rate - delta_introduced_unrelated_regression_rate`.
Reference codex raw has target fix rate `100.0%`, introduced unrelated
regression rate `0.0184%`, and build+fix F1 `0.9954`. Because raw already has
perfect target fix rate, all scored ablation cells are net-negative versus raw;
use this table mainly to compare hook variants against each other.

Important separation:
this table is a single-repo hook ablation. Keep it separate from the 020
cross-repo stop-only table. The cross-repo stop-only run skipped Flask and
points to the best `stop-only-strict-20260623T0730` archive; current
`results/flask/.../eval.json` points to `stop-post-strict-20260623T0935`.

| order (worst to best) | variant | hooks configured | build F1 | build P | build introduced unrelated regression | build+fix F1 | build+fix P | build+fix R | introduced unrelated regression rate | net (Δfix/Δunrelated reg) | fixed target | missed target | introduced unrelated regression |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| 1 | `codex-openai-gpt-5.5-before-stop-only-20260622T083033` | PostToolUse, SessionStart, Stop, UserPromptSubmit | 0.8298 | 0.9750 | 2 | 0.3321 | 0.2111 | 0.7778 | 5.9730% | -28.2 (-22.2/+6.0) | 84 | 24 | 314 |
| 2 | `codex-openai-gpt-5.5-session-stop-20260622T2241` | SessionStart, Stop | 0.8377 | 0.9639 | 3 | 0.8898 | 0.8203 | 0.9722 | 0.4135% | -3.2 (-2.8/+0.4) | 105 | 3 | 23 |
| 3 | `codex-openai-gpt-5.5-stop-post-20260622T1330` | PostToolUse, Stop | 0.7075 | 0.7212 | 29 | 0.9474 | 0.9802 | 0.9167 | 0.0360% | -8.4 (-8.3/+0.0) | 99 | 9 | 2 |
| 4 | `codex-openai-gpt-5.5-stop-only-trusted-20260622T1329` | Stop | 0.7935 | 0.9605 | 3 | 0.9515 | 1.0000 | 0.9074 | 0.0000% | -9.2 (-9.3/-0.0) | 98 | 10 | 0 |
| 5 | `codex-openai-gpt-5.5-user-stop-20260622T2035` | Stop, UserPromptSubmit | 0.7717 | 0.9342 | 5 | 0.9524 | 0.9804 | 0.9259 | 0.0369% | -7.4 (-7.4/+0.0) | 100 | 8 | 2 |
| 6 | `codex-openai-gpt-5.5-stop-with-session-post-20260622T0117` | PostToolUse, SessionStart, Stop | 0.7685 | 0.8211 | 17 | 0.9861 | 0.9907 | 0.9815 | 0.0179% | -1.9 (-1.9/-0.0) | 106 | 2 | 1 |
| 7 | `codex-openai-gpt-5.5-stop-post-strict-20260623T0935` | PostToolUse, Stop | 0.8394 | 0.9529 | 4 | 0.9862 | 0.9817 | 0.9907 | 0.0358% | -0.9 (-0.9/+0.0) | 107 | 1 | 2 |
| 8 | `codex-openai-gpt-5.5-user-post-stop-strict4-20260623T0535` | PostToolUse, Stop, UserPromptSubmit | 0.7600 | 0.8261 | 16 | 0.9907 | 0.9907 | 0.9907 | 0.0179% | -0.9 (-0.9/-0.0) | 107 | 1 | 1 |
| 9 | `codex-openai-gpt-5.5-stop-only-strict-20260623T0730` | Stop | 0.8210 | 0.9512 | 4 | 0.9953 | 1.0000 | 0.9907 | 0.0000% | -0.9 (-0.9/-0.0) | 107 | 1 | 0 |

Aborted variants excluded from metrics:

| variant | reason |
|---|---|
| `codex-openai-gpt-5.5-aborted-stop-only-no-hook-trust-20260622T0136` | no `eval.json`; only `live_log.jsonl` |
| `codex-openai-gpt-5.5-aborted-stop-only-with-skills-20260622T0126` | no `eval.json`; only `live_log.jsonl` |

Report reading:

- The best scored Flask hook-ablation cell is pure `Stop`:
  `stop-only-strict-20260623T0730`, build+fix F1 `0.9953`, precision `1.0`,
  introduced unrelated regression count `0`, and net `-0.9 (-0.9/-0.0)` versus
  codex raw.
- The worst scored cell is the "everything on" hook stack:
  PostToolUse + SessionStart + Stop + UserPromptSubmit, build+fix F1 `0.3321`,
  precision `0.2111`, introduced unrelated regression count `314`,
  introduced unrelated regression rate `5.9730%`, and net `-28.2 (-22.2/+6.0)`.
- This supports "prompt-time/session-time intervention can hurt on Flask" within
  this single-repo ablation. It does not by itself prove cross-repo causality.
