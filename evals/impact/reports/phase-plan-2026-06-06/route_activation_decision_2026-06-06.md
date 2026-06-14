# Route Activation Decision Report

- Generated at: `2026-06-06T23:12:07+10:00`
- Decision: `blocked`
- Activation allowed: `False`
- Blocks activation: `True`
- Reason: At least one behavior or replay metric criterion failed.

## Inputs

- Replay report: `evals/impact/reports/phase-plan-2026-06-06/route_replay_phase_plan_2026-06-06.json`
- Behavior report: `evals/impact/reports/phase-plan-2026-06-06/route_behavior_tests_2026-06-06.json`

## Metrics

- Replayed traces: `57`
- Behavior cases: `4`
- Behavior failed checks: `0`
- Precision delta: `-0.186`
- Noise delta: `0.186`
- Selected useful delta: `-77`
- Missed useful delta: `16`
- Precision regression items: `5`
- Noise regression items: `5`

## Criteria

| criterion | category | status | observed | threshold |
| --- | --- | --- | --- | --- |
| behavior_does_not_block_activation | behavior | pass | {"blocks_activation": false, "failed_check_count": 0} | {'blocks_activation': False, 'failed_check_count': 0} |
| behavior_case_count | behavior | pass | 4 | >= 4 |
| replayed_trace_count | replay | pass | 57 | >= 57 |
| route_precision_delta | replay | fail | -0.186 | >= 0.0 |
| route_noise_delta | replay | fail | 0.186 | <= 0.0 |
| selected_useful_doc_delta | replay | fail | -77 | >= 0 |
| missed_useful_doc_delta | replay | fail | 16 | <= 0 |
| precision_regression_items | replay | fail | 5 | <= 0 |
| noise_regression_items | replay | fail | 5 | <= 0 |

## Activation Policy

- Behavior tests must have zero failed checks and must not block activation.
- Replay must cover at least the configured minimum trace count.
- Replay precision must not regress.
- Replay noise must not increase.
- Selected useful docs must not decrease unless the threshold is explicitly relaxed.
- Missed useful docs must not increase unless the threshold is explicitly relaxed.
- Per-trace precision and noise regressions must stay within configured tolerances.
- Passing this report recommends activation; it does not mutate active taxonomy or route state.
