# Fresh Windows Forward Route Trace Plan

Generated at: `2026-06-08T14:43:29+1000`

## Executive Summary

The next step should be a one-shot fresh Windows forward cohort, not another historical replay.
The goal is to measure whether a fresh Windows agent can produce route traces that later match actual
useful AI Wiki docs.

Local preparation is complete:

- Manifest: `evals/impact/local_experiment/fresh_windows_forward_route_cohort_2026-06-08.json`
- Target evaluable traces: `12`
- Dry-route preflight: `12 / 12` tasks routed successfully with `--no-record-trace`
- Taxonomy activation: explicitly out of scope
- Historical replay: explicitly out of scope for this cohort

This local machine cannot produce the real Windows traces. The Windows run is only complete after the
cohort tasks run in a fresh Windows checkout and each task has downstream reuse/check evidence.

## What This Measures

This cohort measures forward route quality:

- route-selected docs that were actually useful
- selected docs that were noisy or unused
- useful docs found later through lookup
- missed useful docs
- failed routes where selected docs contain none of the useful docs
- context cost from selected docs and packet words

It must not mix in historical replay precision. Historical replay remains diagnostic; this Windows
cohort is forward evidence.

## Manifest

The manifest defines 12 tasks:

```text
evals/impact/local_experiment/fresh_windows_forward_route_cohort_2026-06-08.json
```

Task categories:

- Windows install / CLI entrypoint smoke
- Windows ARM smoke output capture
- route trace + reuse telemetry pipeline
- forward route cohort reporting
- scaffold prompt workflow compliance
- ownership boundary preservation
- release/runtime compatibility
- npm postinstall archive staging
- source-session provenance
- Agent Harness behavior suite
- taxonomy candidate induction without activation
- CJK task-only interpretation

## Windows Execution Protocol

Run from a brand-new Windows checkout.

1. Prepare the repo:

```powershell
uv sync --extra dev
uv run pytest
```

2. Record the cohort start timestamp before the first cohort route:

```powershell
$CohortStart = (Get-Date).ToString("yyyy-MM-ddTHH:mm:sszzz")
$CohortStart
```

3. For each task in the manifest, run route first. Do not pass `--no-record-trace`.

```powershell
$TaskId = "fw-win-01-install-entrypoint-smoke"
$Task = @'
On a brand-new Windows checkout, verify ai-wiki-toolkit can be run from the source tree and from the installed entrypoint if installed. Compare `uv run aiwiki-toolkit --help` with `uv run python -m ai_wiki_toolkit.cli --help`, run `uv run aiwiki-toolkit doctor`, and report exact version/help mismatches. Do not modify source files.
'@

uv run aiwiki-toolkit route --task-id $TaskId --task $Task
```

4. Complete the task using the route packet.

5. Record downstream use evidence for user-owned AI Wiki docs that actually helped.

Use `preloaded` when the useful doc was selected by route:

```powershell
uv run aiwiki-toolkit record-reuse `
  --task-id $TaskId `
  --doc-id "<doc-id-from-route-packet>" `
  --retrieval-mode preloaded `
  --evidence-mode explicit `
  --reuse-outcome resolved `
  --reuse-effect changed_plan `
  --agent-name codex `
  --notes "Fresh Windows forward cohort: route-selected doc was useful."
```

Use `lookup` when the useful doc was found after route:

```powershell
uv run aiwiki-toolkit record-reuse `
  --task-id $TaskId `
  --doc-id "<doc-id-found-after-route>" `
  --retrieval-mode lookup `
  --evidence-mode explicit `
  --reuse-outcome resolved `
  --reuse-effect avoided_retry `
  --agent-name codex `
  --notes "Fresh Windows forward cohort: useful doc was missed by initial route."
```

Then record the task-level check:

```powershell
uv run aiwiki-toolkit record-reuse-check `
  --task-id $TaskId `
  --check-outcome wiki_used `
  --agent-name codex `
  --notes "Fresh Windows forward cohort task completed with reuse evidence."
```

If no AI Wiki doc was useful, still record the task-level check:

```powershell
uv run aiwiki-toolkit record-reuse-check `
  --task-id $TaskId `
  --check-outcome no_wiki_use `
  --agent-name codex `
  --notes "Fresh Windows forward cohort task completed; no AI Wiki doc was useful."
```

Do not manually record every unused selected doc. The report computes selected-but-unused by joining
route traces to reuse events.

## Reporting Commands

After all 12 tasks are complete, generate the forward cohort reports:

```powershell
uv run aiwiki-toolkit eval impact route-noise cohort `
  --post-change-since $CohortStart `
  --target-evaluable-traces 12 `
  --baseline-evaluable-traces 58 `
  --max-items 20 `
  --format text `
  --output evals/impact/reports/2026-06-08-layered-refactor/windows_forward_route_cohort_2026-06-08.md

uv run aiwiki-toolkit eval impact route-noise cohort `
  --post-change-since $CohortStart `
  --target-evaluable-traces 12 `
  --baseline-evaluable-traces 58 `
  --max-items 20 `
  --format json `
  --output evals/impact/reports/2026-06-08-layered-refactor/windows_forward_route_cohort_2026-06-08.json
```

Optionally inspect route diagnostics for the same period without writing generated diagnostics
outside the eval report directory:

```powershell
uv run aiwiki-toolkit diagnose memory --focus route --handle bochengyin --since $CohortStart --no-write
```

Do not run `route-noise replay` for the Windows claim. Replay answers a different question.

## Local Dry-Route Preflight

The local preflight used:

```text
uv run aiwiki-toolkit route --task-id <task_id> --task <prompt> --format json --no-record-trace
```

All 12 tasks routed successfully.

| task_id | task_type | mode | selected | maybe | top selected docs |
| --- | --- | --- | ---: | ---: | --- |
| `fw-win-01-install-entrypoint-smoke` | `scaffold_prompt_workflow` | `report` | 6 | 3 | `people/bochengyin/drafts/user-owned-ai-wiki-index-should-not-be-an-upgrade-surface`, `people/bochengyin/drafts/local-dogfooding-should-check-source-cli-vs-installed-entrypoint` |
| `fw-win-02-windows-arm-smoke-full-output` | `release_distribution` | `plan` | 6 | 3 | `problems/windows-arm-smoke-version-checks-need-full-cli-output`, `people/bochengyin/drafts/eval-run-manifest-should-precede-auto-runner` |
| `fw-win-03-route-trace-reuse-pipeline` | `memory_governance` | `fixed_workflow` | 1 | 0 | `people/bochengyin/drafts/route-cohorts-need-original-task-text-for-exact-replay` |
| `fw-win-04-forward-route-cohort-report` | `memory_governance` | `fixed_workflow` | 1 | 0 | `people/bochengyin/drafts/route-cohorts-need-original-task-text-for-exact-replay` |
| `fw-win-05-scaffold-prompt-workflow-compliance` | `scaffold_prompt_workflow` | `report` | 6 | 3 | `people/bochengyin/drafts/consolidation-should-layer-over-end-of-task-capture-and-avoid-shared-doc-churn`, `conventions/package-managed-vs-user-owned-docs` |
| `fw-win-06-ownership-boundary-user-docs` | `scaffold_prompt_workflow` | `report` | 6 | 3 | `metrics/index`, `conventions/package-managed-vs-user-owned-docs` |
| `fw-win-07-release-runtime-compatibility` | `release_distribution` | `fixed_workflow` | 1 | 0 | `people/bochengyin/drafts/linux-release-binaries-need-runtime-checks-against-an-older-glibc-baseline` |
| `fw-win-08-postinstall-archive-staging` | `release_distribution` | `fixed_workflow` | 1 | 0 | `people/bochengyin/drafts/workflow-packaging-queue-should-use-evidence-gated-smallest-asset-selection` |
| `fw-win-09-source-session-provenance` | `memory_governance` | `fixed_workflow` | 1 | 0 | `people/bochengyin/drafts/source-incident-timing-needs-provenance` |
| `fw-win-10-behavior-suite-separate-layer` | `memory_governance` | `report` | 6 | 3 | `people/bochengyin/drafts/route-precision-experiments-should-separate-forward-routing-from-historical-metrics`, `people/bochengyin/drafts/ai-wiki-usefulness-metrics-need-task-level-checks-plus-doc-events` |
| `fw-win-11-taxonomy-candidates-no-activation` | `workflow_state` | `report` | 3 | 3 | `people/bochengyin/drafts/eval-product-run-requests-need-family-scope-check`, `people/bochengyin/drafts/opencode-runtime-skill-exposure-needs-prompt-visible-fallback` |
| `fw-win-12-cjk-task-only-route-interpretation` | `memory_governance` | `plan` | 6 | 3 | `people/bochengyin/drafts/route-cohorts-need-original-task-text-for-exact-replay`, `people/bochengyin/drafts/route-precision-next-method-should-use-stage-slot-selection` |

## Acceptance Criteria

The Windows run is complete only if:

- all route commands exit successfully
- `uv run pytest` exits successfully or the failure is reported with full output
- route traces are recorded for all 12 task IDs
- task-level reuse checks are recorded for all 12 task IDs
- enough document-level reuse evidence exists for all 12 tasks to be route-noise evaluable
- cohort markdown and JSON reports are generated
- taxonomy candidate induction, if run, reports `active_taxonomy_changed=false`
- behavior-suite pass rate is reported separately from route precision

## Expected Interpretation

If current task-only replay is the best proxy for a fresh Windows agent, then this forward cohort
should be judged mainly by:

- whether route precision is closer to `0.361` than the historical selected-doc baseline
- whether failed-route@selected stays near or below `13 / 58 = 0.224`
- whether missed useful docs drop when the agent records real lookup docs carefully
- whether fixed workflow routing produces fewer noisy selected docs without hiding useful lookup docs

If the 12-task cohort has fewer than 12 evaluable traces, do not claim a precision result. Report it
as an instrumentation failure first.
