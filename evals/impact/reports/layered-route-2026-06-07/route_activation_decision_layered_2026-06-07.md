# Route Activation Decision Report

- Generated at: `2026-06-07T11:35:41+10:00`
- Decision: `blocked`
- Activation allowed: `False`
- Blocks activation: `True`
- Reason: At least one behavior or replay metric criterion failed.

## Inputs

- Replay report: `evals/impact/reports/layered-route-2026-06-07/route_replay_layered_latest_2026-06-07.json`
- Behavior report: `evals/impact/reports/phase-plan-2026-06-06/route_behavior_tests_2026-06-06.json`

## Metrics

- Replayed traces: `57`
- Behavior cases: `4`
- Behavior failed checks: `0`
- Precision delta: `-0.185`
- Noise delta: `0.185`
- Baseline retrieval precision: `0.502`
- Replay retrieval precision: `0.348`
- Selected useful delta: `-75`
- Missed useful delta: `15`
- Precision regression items: `34`
- Noise regression items: `34`
- Baseline retrieval selected docs: `291`
- Replay retrieval selected docs: `264`
- Baseline core docs: `42`
- Replay core docs: `31`

## Criteria

| criterion | category | status | observed | threshold |
| --- | --- | --- | --- | --- |
| behavior_does_not_block_activation | behavior | pass | {"blocks_activation": false, "failed_check_count": 0} | {'blocks_activation': False, 'failed_check_count': 0} |
| behavior_case_count | behavior | pass | 4 | >= 4 |
| replayed_trace_count | replay | pass | 57 | >= 57 |
| route_precision_delta | replay | fail | -0.185 | >= 0.0 |
| route_noise_delta | replay | fail | 0.185 | <= 0.0 |
| selected_useful_doc_delta | replay | fail | -75 | >= 0 |
| missed_useful_doc_delta | replay | fail | 15 | <= 0 |
| precision_regression_items | replay | fail | 34 | <= 0 |
| noise_regression_items | replay | fail | 34 | <= 0 |

## Activation Policy

- Behavior tests must have zero failed checks and must not block activation.
- Replay must cover at least the configured minimum trace count.
- Replay precision must not regress.
- Replay noise must not increase.
- Selected useful docs must not decrease unless the threshold is explicitly relaxed.
- Missed useful docs must not increase unless the threshold is explicitly relaxed.
- Per-trace precision and noise regressions must stay within configured tolerances.
- Passing this report recommends activation; it does not mutate active taxonomy or route state.
