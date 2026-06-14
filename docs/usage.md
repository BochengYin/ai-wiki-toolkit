# ai-wiki-toolkit Usage Guide

This page keeps the detailed command guide out of the README while preserving the practical workflows
needed for local use, diagnostics, reports, and impact evals.

## Install And Update

Install in a target git repository:

```bash
aiwiki-toolkit install
aiwiki-toolkit install --handle your-handle
```

`init` remains a backward-compatible alias:

```bash
aiwiki-toolkit init
```

After upgrading the package, refresh managed files and check for stale starter docs or prompt blocks:

```bash
aiwiki-toolkit install
aiwiki-toolkit doctor --strict
```

If `doctor` reports missing starter pointers, print suggested starter content:

```bash
aiwiki-toolkit doctor --suggest-index-upgrade
```

For npm installs, update through npm:

```bash
npm update -g ai-wiki-toolkit
npm install -g ai-wiki-toolkit@latest
```

## Default Agent Workflow

Agents should not dump the whole wiki or run the router as the default task-start path. The default
workflow installed by `aiwiki-toolkit install` is:

1. Use the managed `AGENTS.md` block to check whether `ai-wiki/_toolkit/system.md` exists.
2. If AI Wiki is enabled, read the managed system workflow.
3. Read `ai-wiki/memory/index.md` when it exists.
4. Open at most one linked memory file, and only when it strongly matches the same file, API,
   command, behavior, or repeated public/local failure.
5. Work normally, then write back only to `ai-wiki/memory/` after a durable public/local
   trial-error signal or reusable clarification.

## Optional Route Diagnostics

Use route when you are explicitly tuning, debugging, or inspecting memory selection:

```bash
aiwiki-toolkit route --task "current user request"
```

The command emits a transient context packet with task type, guardrail tags, success criteria, index
cards, `must_load` docs, `must_follow` rules, `maybe_load` docs, and explicit skip reasons.

After initial scoring, route reranks the top deterministic index cards by card-level specificity.
The reranker only sees card metadata such as title, short description, routing hint, kind, and
existing scores; it does not load every full Markdown document as a second pass. Use
`--rerank-top 0` to disable the reranker for scorer comparisons.

Route also exposes scorer diagnostics in JSON packets. `route.language_signals` shows conservative
English and Chinese task-term expansions, including mixed-language prompts. Each card includes
`multi_signal_adjustment` / `multi_signal` for capped route-tag protection and
`route_quality_signal` for support-aware history such as selected count, useful selections,
selected precision, missed-useful bonus, and unused/not-helpful penalties.

By default, route shows `git status` paths in the packet but only uses them as routing signals when
the task text is generic. Pass `--changed-path` when a path should explicitly influence task
classification, domain/guardrail tags, and document scoring.

Route trace telemetry records the task text, selected docs, language signals, route quality
adjustments/signals, multi-signal adjustments, changed-path signal policy, and best-effort local
Codex session provenance such as `CODEX_THREAD_ID`, rollout path, thread cwd/title, and git metadata
when `~/.codex/state_5.sqlite` is available. This supports later local replay without uploading
repository contents.

The packet is generated guidance, not canonical memory. Markdown files under `ai-wiki/` remain the
source of truth.

## Recording Reuse Evidence

Append one document-level reuse observation:

```bash
aiwiki-toolkit record-reuse \
  --doc-id review-patterns/shared-prompt-files-must-be-user-agnostic \
  --task-id release-followup \
  --retrieval-mode lookup \
  --evidence-mode explicit \
  --reuse-outcome resolved \
  --reuse-effect avoided_retry \
  --saved-tokens 1200 \
  --saved-seconds 45
```

Record that a completed task was checked for AI wiki reuse, even when no wiki docs were needed:

```bash
aiwiki-toolkit record-reuse-check \
  --task-id release-followup \
  --check-outcome wiki_used
```

Only user-owned AI wiki knowledge docs should be recorded with `record-reuse`. Managed control-plane
docs under `_toolkit/**` can be cited in user-facing notes when they affect behavior, but they should
not be logged as knowledge-reuse events.

## Source Incident Timing

When a reused memory came from a real earlier incident, record the original acquisition or
trial/error cost separately:

```bash
aiwiki-toolkit record-reuse \
  --doc-id problems/retry-loop \
  --task-id followup-using-memory \
  --retrieval-mode lookup \
  --evidence-mode explicit \
  --reuse-outcome resolved \
  --reuse-effect avoided_retry \
  --source-task-id original-retry-loop \
  --source-incident-seconds 780 \
  --source-incident-source manual \
  --source-incident-note "Failed attempt plus correction turn."
```

If the source incident was a local Codex session, `record-reuse` can derive an active-turn estimate:

```bash
aiwiki-toolkit record-reuse \
  --doc-id problems/retry-loop \
  --task-id followup-using-memory \
  --retrieval-mode lookup \
  --evidence-mode explicit \
  --reuse-outcome resolved \
  --source-session-id 019dcf06-example \
  --source-incident-from-codex-session
```

Treat source incident timing as source active-turn context for research, not exact human time saved.

## Work Ledger

Capture conversation todos or epics as routeable repo-local work state:

```bash
aiwiki-toolkit work capture \
  --work-id aiwiki-framework-roadmap \
  --title "Build the coding agent working framework" \
  --item-type epic \
  --status proposed \
  --source conversation

aiwiki-toolkit work capture \
  --work-id work-ledger \
  --title "Capture conversation todos as AI wiki work state" \
  --status todo \
  --epic-id aiwiki-framework-roadmap \
  --assignee your-handle \
  --link ai-wiki/people/your-handle/drafts/agent-framework-roadmap.md

aiwiki-toolkit work status \
  --work-id work-ledger \
  --status processing
```

Useful owner-scoped views:

```bash
aiwiki-toolkit work mine
aiwiki-toolkit work list --assignee your-handle
aiwiki-toolkit work list --reporter your-handle --include-closed
```

Work events are not knowledge-reuse evidence; they stay separate from `record-reuse`.

## Metrics, Diagnostics, And Reports

Regenerate local telemetry and work snapshots:

```bash
aiwiki-toolkit refresh-metrics
```

Inspect memory quality:

```bash
aiwiki-toolkit diagnose memory
aiwiki-toolkit diagnose memory --since 14d --handle your-handle
aiwiki-toolkit diagnose memory --focus route --handle your-handle
aiwiki-toolkit diagnose memory --focus trial-error
```

Route diagnostics join `route-traces/<handle>.jsonl` with downstream `record-reuse` events by
`task_id`. They report route-selected docs, selected-but-unused docs, later lookup docs, useful
selected docs, missed useful docs, route precision, route recall proxy, route noise, and context
cost.

Impact-eval route reports separate historical summaries, real post-change cohorts, and replay
projections:

```bash
aiwiki-toolkit eval impact route-noise report --since 30d
aiwiki-toolkit eval impact route-noise cohort --post-change-since 2026-06-04T08:20:53+10:00
aiwiki-toolkit eval impact route-noise replay --before 2026-06-04T08:20:53+10:00 --catalog-cutoff trace-routed-at --rerank-top 20
```

`route-noise replay` recovers historical route prompts from local Codex session JSONL when old route
traces do not yet contain task text. It compares the historical selected docs and current-router
selected docs against the same downstream reuse events, and labels the result as a retrospective
projection rather than post-change production evidence. Use `--rerank-top 0` to compare replay
without the index-card reranker.

Generate a repo-level evaluation and improvement advisor report:

```bash
aiwiki-toolkit evaluate repo --since 30d
aiwiki-toolkit evaluate repo --since 30d --format json --no-write
```

Run this after a repo has used the AI wiki workflow for a while and has at least some task checks,
reuse events, route traces, drafts, or impact-eval artifacts. By default it writes generated outputs
under:

```text
ai-wiki/_toolkit/reports/repo-evaluation/<handle>/latest.md
ai-wiki/_toolkit/reports/repo-evaluation/<handle>/latest.json
```

Use `--no-write` for stdout only. The command does not edit user-owned AI wiki docs, does not create
workflows, skills, subagents, or automations, and does not change route policy.

How to read the sections:

- `Executive Summary` gives the overall status, top review opportunities, and what not to change yet.
- `Workflow Coverage` checks task-level reuse checks, document reuse events, documents with reuse,
  coverage gaps, and weak end-of-task evidence.
- `Route Quality` summarizes route traces, selected docs, useful selected docs, missed useful docs,
  selected-but-unused docs, precision, recall proxy, noise, and context cost.
- `Memory Quality` surfaces high-ROI, noisy, stale, conflicting, and missed-memory candidates.
- `Draft And Consolidation Queue` summarizes the human-review queue and points back to
  `aiwiki-toolkit consolidate queue --since <since>`.
- `Impact Eval Readiness` separates local diagnostics from outcome-impact proof and points to the
  impact-eval candidate flow.
- `Asset Selection Opportunities` recommends the smallest reviewable asset form: note, workflow,
  skill, subagent, automation, extend existing, or skip.

Treat every recommendation as review-first. A workflow is a transparent process contract; a skill is
a runtime-packaged capability with triggers and instructions. They are different asset forms, not a
ranked maturity ladder. Route policy optimization is a later phase; this command only points out
review opportunities.

Generate usefulness reports:

```bash
aiwiki-toolkit report usefulness --handle your-handle
aiwiki-toolkit report usefulness --handle your-handle --format json
```

Generate a weekly local HTML review queue:

```bash
aiwiki-toolkit report weekly --handle your-handle
aiwiki-toolkit report weekly --handle your-handle --if-due
```

The weekly HTML page focuses on items that need human judgment: promotion candidates, personal drafts
that may need diagnosis, and not-helpful signals. Raw coverage and referenced-file data belongs in
JSON payloads and supporting reports. Saved-time estimates belong in impact-eval reports.

## Draft Consolidation And Promotion

Generate a human-reviewable consolidation queue:

```bash
aiwiki-toolkit consolidate queue
aiwiki-toolkit consolidate queue --since 14d --handle your-handle
```

Mark handle-local draft promotion candidates from confirmed-useful reuse evidence:

```bash
aiwiki-toolkit promote candidates --handle your-handle
aiwiki-toolkit promote candidates --handle your-handle --apply
```

The default promotion run is report-only. With `--apply`, a draft is marked only when it meets the
configured resolved-use evidence threshold and has no `not_helpful` reuse events.

## Impact Eval Workflow

Inspect registered families:

```bash
aiwiki-toolkit eval impact families
aiwiki-toolkit eval impact families --format json
aiwiki-toolkit eval impact family show ownership_boundary
```

Discover trial/error replay candidates from existing AI wiki evidence:

```bash
aiwiki-toolkit eval impact discover
aiwiki-toolkit eval impact family candidates
aiwiki-toolkit eval impact family draft --candidate problems_retry_loop --baseline-ref HEAD^
aiwiki-toolkit eval impact family promote --candidate problems_retry_loop
aiwiki-toolkit eval impact family promote --candidate problems_retry_loop --apply
```

Plan and prepare a run:

```bash
aiwiki-toolkit eval impact plan --family ownership_boundary
aiwiki-toolkit eval impact prepare --family ownership_boundary
```

Run and inspect a captured benchmark:

```bash
aiwiki-toolkit eval impact run --run-dir /path/to/eval-run --slot s01
aiwiki-toolkit eval impact run --run-dir /path/to/eval-run --all-slots --score-policy command-exit
aiwiki-toolkit eval impact benchmark --family ownership_boundary --score-policy command-exit
aiwiki-toolkit eval impact validate --run-dir /path/to/eval-run
aiwiki-toolkit eval impact score --run-dir /path/to/eval-run --slot s01 --prompt-level original --label success
aiwiki-toolkit eval impact manifest --run-dir /path/to/eval-run
aiwiki-toolkit eval impact report --run-dir /path/to/eval-run
aiwiki-toolkit eval impact summarize --run-dir /path/to/eval-run --run-dir /path/to/another-run
```

`eval impact report` reads existing artifacts such as `metadata.json`, `result.json`, `score.json`,
and `confounds.json`. It compares primary variants, normally `no_aiwiki_workflow` and
`aiwiki_ambient_memory_workflow`, using first-attempt captures for the product signal. Repaired
captures stay diagnostic.

Use `eval impact manifest` to audit run identity before interpreting scores. It reports baseline ref,
prompt hashes, model, reasoning effort, execution surface, slot-to-variant mapping, session export
presence, confounds, and captured artifact paths.

## Uninstall

Remove the managed layer while keeping user-owned wiki documents:

```bash
aiwiki-toolkit uninstall
```

This removes managed prompt blocks, managed `.gitignore` blocks, `ai-wiki/_toolkit/**`,
`~/ai-wiki/system/_toolkit/**`, and the `aiwikiToolkit` key from `opencode.json`.

To also remove repo-local user-owned docs, opt in explicitly:

```bash
aiwiki-toolkit uninstall --purge-user-docs --yes
```

Even with `--purge-user-docs --yes`, the shared home wiki under `~/ai-wiki/system/` is preserved.
