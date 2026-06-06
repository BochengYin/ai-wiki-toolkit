# Project A Coding-Agent Eval Harness Diagnostics

- Generated at: `2026-06-04T07:03:03+10:00`
- Repo root: `<local ai-wiki-toolkit checkout>`
- Handle: `bochengyin`
- Since: `30d`
- Local checks run: `yes`

## Local Checks

| command | returncode | ok |
| --- | --- | --- |
| uv run pytest | 0 | yes |
| npm pack --dry-run --ignore-scripts | 0 | yes |
| git diff --check | 0 | yes |

## Harness State

- Runnable families: `7`
- Rubrics present: `7`
- Rubrics missing: `none`
- Indexed runs: `17`
- Recent runs: `17`

| family | status | rubric | baseline |
| --- | --- | --- | --- |
| aiwiki_evidence_integrity | runnable | yes | 8228ba6^ |
| ownership_boundary | runnable | yes | 34cd5a3^ |
| postinstall_archive_staging | runnable | yes | 408ff40^ |
| release_distribution_integrity | runnable | yes | 06a47cd^ |
| release_runtime_compatibility | runnable | yes | f946ed6^ |
| scaffold_prompt_workflow_compliance | runnable | yes | b1366fe^ |
| windows_arm_smoke_cli_output | runnable | yes | e0d6fa9^ |

## Recent Runs

| period | family | score_policy | outcome | artifact_status |
| --- | --- | --- | --- | --- |
| smoke-20260523225229 | windows_arm_smoke_cli_output | command-exit | neutral_signal | True |
| dogfood-fixed-20260524124712 | windows_arm_smoke_cli_output | command-exit | neutral_signal | True |
| formal-20260524T034658Z | ownership_boundary | command-exit | neutral_signal | True |
| historical-2026-05-01 | aiwiki_evidence_integrity | manual-note-rubric | positive_signal | run_dir_missing |
| historical-2026-04-25 | ownership_boundary | manual-note-rubric | positive_signal | run_dir_missing |
| historical-2026-04-30 | postinstall_archive_staging | manual-note-rubric | neutral_signal | run_dir_missing |
| historical-2026-04-25 | release_distribution_integrity | manual-note-rubric | positive_signal | run_dir_missing |
| historical-2026-04-25 | release_runtime_compatibility | manual-note-rubric | positive_signal | run_dir_missing |
| historical-2026-04-25 | scaffold_prompt_workflow_compliance | manual-note-rubric | positive_signal | run_dir_missing |
| historical-2026-04-25 | windows_arm_smoke_cli_output | manual-note-rubric | neutral_signal | run_dir_missing |
| project-a-rerun-2026-06-03 | aiwiki_evidence_integrity | rubric | positive_signal | True |
| project-a-rerun-2026-06-03 | ownership_boundary | rubric | positive_signal | True |
| project-a-rerun-2026-06-03 | postinstall_archive_staging | rubric | neutral_signal | True |
| project-a-rerun-2026-06-03 | release_distribution_integrity | rubric | neutral_signal | True |
| project-a-rerun-2026-06-03 | release_runtime_compatibility | rubric | neutral_signal | True |
| project-a-rerun-2026-06-03 | scaffold_prompt_workflow_compliance | rubric | positive_signal | True |
| project-a-rerun-2026-06-03 | windows_arm_smoke_cli_output | rubric | neutral_signal | True |

## Repo Evaluation

- Overall status: `useful with route-quality review needed`
- Checked tasks: `132`
- Task checks: `133`
- Reuse events: `496`
- Coverage gaps: `0`
- Route traces: `101`
- Route precision: `0.300`
- Route recall proxy: `0.788`
- Route noise rate: `0.700`
- Selected-but-unused docs: `406`
- Missed useful docs: `43`

## Optimization Backlog

| priority | title | reason |
| --- | --- | --- |
| P1 | Reduce route noise before adding more memory | Route precision is 0.300 and noise rate is 0.700. |
| P2 | Analyze neutral benchmark families before adding memory | All runnable families have successful rubric runs; 4 latest outcomes are neutral: postinstall_archive_staging, release_distribution_integrity, release_runtime_compatibility, windows_arm_smoke_cli_output. |
| P2 | Add per-slot timeout and heartbeat artifacts | Recent rubric runs are indexed only after completion; long Codex slots need elapsed-time, timeout, and heartbeat evidence for production-style ops. |

## Claim Boundary

This report is a local diagnostic over repo artifacts and telemetry. It is not itself a fresh multi-slot Codex benchmark rerun unless `--run-checks` and a separate `schedule run` command were executed successfully.
