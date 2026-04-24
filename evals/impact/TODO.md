# Impact Eval TODO

This file tracks benchmark families that still need to be designed or run.

Use this as the first entrypoint when opening a new session to continue impact-eval work.

## Reusable Benchmark Recipe

Unless a family clearly needs a different harness, reuse the `ownership_boundary` workflow:

1. choose a real historical problem, not a synthetic toy task
2. pick a baseline commit from before the fix landed
3. define the five standard variants:
   - `plain_repo_no_aiwiki`
   - `aiwiki_no_relevant_memory`
   - `aiwiki_raw_drafts`
   - `aiwiki_consolidated`
   - `aiwiki_raw_plus_consolidated`
4. define `short` and `medium` prompts
5. run each variant in a fresh Codex subscription session
6. save artifacts with:
   - `prepare_variants.py`
   - `init_run.py`
   - `save_result.py`
   - `report_runs.py`
7. grade the results with the manual rubric:
   - `success`
   - `partial`
   - `fail`

Reference implementation:

- `evals/impact/ownership_boundary_runbook.md`
- `evals/impact/notes/ownership_boundary_round1_findings.md`

## Status Legend

- `done`: benchmark family has already been run and documented
- `next`: high-priority next family to design
- `planned`: likely future family, but task/prompt design still needs work
- `needs-more-signals`: promising family, but current raw/consolidated evidence is still too thin

## Family Backlog

| family | status | type | core question | likely source memory |
| --- | --- | --- | --- | --- |
| `ownership_boundary` | `done` | repeated-problem / surface-choice | does AI wiki memory keep a contributor-only helper out of package code? | `repo-local-contributor-workflows-should-stay-out-of-the-package-layer`, adjacent ownership/prompt docs |
| `release_distribution_integrity` | `done` | repeated-problem / coordinated multi-surface change | when a public distribution target changes, does memory help the agent keep workflows, asset names, npm metadata, archive handling, docs, and smoke checks aligned? | `ai-wiki/conventions/distribution-target-matrix-must-match-published-assets.md`, source draft, related release-fix drafts |
| `windows_arm_smoke_cli_output` | `planned` | narrow repeated-problem benchmark | does memory help the agent fix the exact Windows ARM smoke assertion by comparing against full CLI output instead of the bare version? | `ai-wiki/problems/windows-arm-smoke-version-checks-need-full-cli-output.md` |
| `release_runtime_compatibility` | `planned` | repeated-problem / release-runtime verification | does memory help the agent choose an older glibc baseline and add runtime verification instead of stopping at build or install success? | `linux-release-binaries-need-runtime-checks-against-an-older-glibc-baseline.md` |
| `postinstall_archive_staging` | `planned` | repeated-problem / packaging | does memory help the agent avoid self-deleting npm postinstall staging paths? | `npm-postinstall-must-not-delete-its-own-download-archive.md` |
| `scaffold_prompt_workflow_compliance` | `planned` | workflow-compliance | when changing scaffold or prompt behavior, does memory help the agent update tests, rerun install, and avoid prompt churn? | `ai-wiki/workflows.md`, `shared-prompt-files-must-be-user-agnostic.md`, prompt-churn drafts |
| `aiwiki_evidence_integrity` | `planned` | telemetry / end-of-task workflow | does memory help the agent preserve the distinction between document-level reuse events and task-level checks, and always run update checks? | `ai-wiki-usefulness-metrics-need-task-level-checks-plus-doc-events.md`, `end-of-task-ai-wiki-update-check-must-always-run.md`, `ai-wiki-reuse-metrics-should-exclude-managed-docs-and-shard-by-handle.md` |
| `capture_vs_consolidation` | `needs-more-signals` | consolidation-design benchmark | when consolidation exists, does it improve reuse without creating shared-doc churn or overwriting end-of-task capture? | `consolidation-should-layer-over-end-of-task-capture-and-avoid-shared-doc-churn.md` |

## Notes Per Family

### ownership_boundary

Already run.

Artifacts:

- `evals/impact/ownership_boundary_runbook.md`
- `evals/impact/notes/ownership_boundary_round1_findings.md`

### release_distribution_integrity

Already run and documented.

Artifacts:

- `evals/impact/release_distribution_integrity_runbook.md`
- `evals/impact/notes/release_distribution_integrity_round1_findings.md`
- `evals/impact/notes/round1_process_lessons.md`

Current defended takeaway:

- this family is useful for coordinated multi-surface completeness
- it is less discriminating than `ownership_boundary short` for basic success/failure
- full prompt surface still needs tighter control before stronger causal claims

Why this family was still a strong candidate:

- a promoted shared convention
- a detailed source draft
- repeated multi-surface failures across workflows, npm, docs, and smoke verification

### windows_arm_smoke_cli_output

This is narrower and cleaner than the full distribution-integrity family.

Good choice if the next benchmark should be small and deterministic.

Likely success criterion:

- fix the smoke check in the right workflow/test surface
- compare against `ai-wiki-toolkit <version>` instead of bare `<version>`

### release_runtime_compatibility

This family is attractive because it reflects a real runtime-success versus build-success gap.

The benchmark would likely test whether the agent:

- adds runtime verification
- chooses an older Linux/glibc baseline
- avoids stopping after publish/install-only green signals

### postinstall_archive_staging

This is another good narrow repeated-problem family.

The benchmark would likely test whether the agent:

- keeps transient downloads outside disposable target directories
- fixes the staging layout rather than misdiagnosing the remote asset

### scaffold_prompt_workflow_compliance

This is the best workflow-compliance family candidate.

It would test whether the agent follows:

- test updates
- `uv run pytest`
- local `aiwiki-toolkit install` verification
- prompt-block boundary checks
- no user-specific churn

### aiwiki_evidence_integrity

This family is less about code placement and more about end-of-task workflow correctness.

It would likely test whether the agent:

- records task-level checks
- separates document events from denominator coverage
- avoids counting managed `_toolkit/**` docs as reuse evidence
- always emits an update outcome

This family may need a slightly different scoring rubric from `ownership_boundary`.

### capture_vs_consolidation

This is not the best next family yet.

It is still more of a design hypothesis than a benchmark with a clean direct task.

Promote it later if more concrete consolidation tasks appear.

## Suggested Next Session Starts

If you want the closest follow-on to the current release family:

1. `windows_arm_smoke_cli_output`

If you want the next broader release/verification benchmark:

1. `release_runtime_compatibility`

If you want the next workflow-style benchmark:

1. `scaffold_prompt_workflow_compliance`
