# Route Eval-Stage Ablation Report

- Generated at: `2026-06-07T16:03:28+10:00`
- Before: `2026-06-04T08:20:53+10:00`
- Catalog cutoff: `trace-routed-at`
- Target evaluable traces: `57`

## Variant Summary

| variant | retrieval_precision | retrieval_delta | failed@selected+maybe | failed_delta | maybe_recovery | coverage@selected+maybe | selected_useful | useful_delta | missed_useful | missed_delta | stage_incompatible | precision_regressions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current | 0.363 | 0.000 | 0.228 | 0.000 | 0.000 | 0.473 | 106 | 0 | 56 | 0 | 39 | 34 |
| eval_stage_shadow | 0.363 | 0.000 | 0.228 | 0.000 | 0.000 | 0.473 | 106 | 0 | 56 | 0 | 39 | 34 |
| eval_stage_soft_scoring | 0.363 | 0.000 | 0.211 | -0.018 | 0.000 | 0.496 | 107 | 1 | 58 | 2 | 19 | 34 |
| stage_compatible_doc_slots | 0.353 | -0.010 | 0.193 | -0.035 | 0.000 | 0.465 | 104 | -2 | 59 | 3 | 0 | 37 |
| no_eval_bucket_selector | 0.340 | -0.023 | 0.175 | -0.053 | 0.091 | 0.500 | 111 | 5 | 54 | -2 | 39 | 31 |
| no_reranker | 0.340 | -0.023 | 0.228 | 0.000 | 0.071 | 0.473 | 103 | -3 | 59 | 3 | 38 | 33 |
| no_route_quality_history | 0.357 | -0.006 | 0.158 | -0.070 | 0.100 | 0.487 | 107 | 1 | 57 | 1 | 31 | 35 |

## Top Eval-Stage Off-Diagonal Pairs

| variant | task_stage | doc_stage | selected_docs |
| --- | --- | --- | --- |
| current | manifest_or_runner | prompt_design | 12 |
| current | manifest_or_runner | artifact_capture | 4 |
| current | source_incident_timing | manifest_or_runner | 4 |
| current | prompt_design | source_incident_timing | 3 |
| current | prompt_design | manifest_or_runner | 2 |
| eval_stage_shadow | manifest_or_runner | prompt_design | 12 |
| eval_stage_shadow | manifest_or_runner | artifact_capture | 4 |
| eval_stage_shadow | source_incident_timing | manifest_or_runner | 4 |
| eval_stage_shadow | prompt_design | source_incident_timing | 3 |
| eval_stage_shadow | prompt_design | manifest_or_runner | 2 |
| eval_stage_soft_scoring | manifest_or_runner | prompt_design | 5 |
| eval_stage_soft_scoring | manifest_or_runner | artifact_capture | 2 |
| eval_stage_soft_scoring | route_usefulness | prompt_design | 2 |
| eval_stage_soft_scoring | source_incident_timing | manifest_or_runner | 2 |
| eval_stage_soft_scoring | source_incident_timing | prompt_design | 2 |
| no_eval_bucket_selector | manifest_or_runner | prompt_design | 12 |
| no_eval_bucket_selector | source_incident_timing | manifest_or_runner | 4 |
| no_eval_bucket_selector | manifest_or_runner | artifact_capture | 3 |
| no_eval_bucket_selector | prompt_design | source_incident_timing | 3 |
| no_eval_bucket_selector | manifest_or_runner | source_incident_timing | 2 |
| no_reranker | manifest_or_runner | prompt_design | 11 |
| no_reranker | manifest_or_runner | artifact_capture | 6 |
| no_reranker | source_incident_timing | manifest_or_runner | 4 |
| no_reranker | prompt_design | source_incident_timing | 3 |
| no_reranker | prompt_design | artifact_capture | 2 |
| no_route_quality_history | manifest_or_runner | prompt_design | 10 |
| no_route_quality_history | manifest_or_runner | artifact_capture | 3 |
| no_route_quality_history | prompt_design | source_incident_timing | 2 |
| no_route_quality_history | route_usefulness | prompt_design | 2 |
| no_route_quality_history | source_incident_timing | manifest_or_runner | 2 |

## Activation

- Status: `blocked`
- Reason: Ablation is diagnostic only; activation requires non-regressing replay plus behavior tests.
- Best retrieval variant: `no_route_quality_history`
- Recommended next step: Prioritize eval-stage selector if it improves retrieval precision without losing useful docs; otherwise inspect the largest off-diagonal stage pairs.

## Candidate Signal

- Variant: `no_route_quality_history`
- Retrieval precision delta vs current: `-0.006`
- Failed route@selected+maybe delta vs current: `-0.070`
- Maybe recovery rate delta vs current: `0.100`
- Selected useful delta vs current: `1`
- Missed useful delta vs current: `1`

## Warnings

- Ablation variants are retrospective projections over recovered route prompts.
- Do not activate a selector change from ablation alone; combine with behavior tests.
