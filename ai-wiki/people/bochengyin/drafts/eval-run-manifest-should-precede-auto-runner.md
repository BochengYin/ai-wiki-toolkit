---
title: "Eval run manifest should precede auto runner"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "feature_clarification"
status: "draft"
created_at: "2026-05-21T09:51:00+10:00"
updated_at: "2026-05-23T22:27:10+10:00"
promotion_candidate: false
promotion_basis: "none"
---
# Draft

## Context

While productizing the impact-eval harness beyond `eval impact report`, the next step could have
been a full `eval impact run` command that prepares workspaces, invokes an agent, captures
transcripts, validates confounds, scores, and reports.

That would lock in agent-adapter semantics before the captured-run artifact contract is fully
auditable.

## Lesson

Add a captured-run manifest surface before auto-running benchmark families.

The manifest should make each run's identity and artifact inventory explicit:

- baseline ref
- prompt levels and prompt hashes
- model, reasoning effort, and execution surface
- slot-to-variant mapping
- session export presence
- confound status
- result, score, final-message, diff, status, head, command-result, and transcript paths

This keeps `eval impact report` focused on product metrics while giving future `eval impact run`
orchestrators a stable schema to produce and validate.

## 2026-05-21 Refinement

After adding the manifest surface, the next safe product slice was `eval impact plan`, not direct
agent execution.

The plan command should:

- read `evals/impact/families/<family>/spec.toml`
- hash the selected prompt files
- name the workflow-primary and diagnostic variants
- emit the intended prepare/init/run/export/validate/report commands
- mark `auto_invokes_agent=false`

This creates a dry-run contract for the future runner while keeping agent invocation, adapter
semantics, and scoring policy explicit instead of hidden inside the first orchestration command.

## 2026-05-21 Prepare Slice

After `eval impact plan`, the next safe product slice was `eval impact prepare`.

The prepare command should execute only the setup portion of the eval lifecycle:

- run the existing repo-local `prepare_variants.py` script
- run the existing repo-local `init_run.py` script
- create neutral slot workspaces
- create the run directory and metadata
- write initial `manifest.json` and `manifest.md`
- return the command outputs and next-step guidance

It should not run `codex exec`, score results, validate causal claims, or publish a benchmark
conclusion. This keeps the package API useful while continuing to treat agent invocation as a
separate adapter decision.

## 2026-05-22 Artifact Lifecycle Slice

After `eval impact prepare`, the next safe product slice was not a full auto-runner. It was to wrap
the existing repo-local artifact lifecycle as package commands:

- `eval impact capture` wraps `save_result.py`
- `eval impact validate` wraps `validate_run.py`
- `eval impact score` wraps `score_run.py`

Each command should update the run manifest after it writes artifacts. This gives installed users a
local, replayable path from prepared workspaces to captured results, confound validation, manual
scores, manifest, and report without hiding agent invocation policy inside the package API.

The smoke proof should use a real prepared run and real artifact commands, but it can simulate
workspace diffs and scores. A smoke without exported Codex sessions should still validate as
non-shareable for causal claims; that is evidence the confound gate is working, not a failure of the
artifact pipeline.

## 2026-05-22 Autonomous Runner Slice

After the artifact lifecycle commands were stable, `eval impact run` became safe to add as a
thin orchestrator over the existing repo-local scripts.

The runner should preserve three boundaries:

- support `--slot` first, then `--all-slots`, so single-slot adapter failures can be debugged before
  running a whole family
- keep transcript export and validation explicit in the result, with missing sessions producing
  confounds rather than causal claims
- require an explicit score policy for automated scoring

The first automated score policy can be `command-exit`, but it must be framed as execution-health
automation only. It should not be presented as semantic task correctness. Formal benchmark claims
still need manual, rubric, transcript-backed, or future judge-backed scoring.

The useful product artifact is a report bundle that contains the run result, manifest, and product
report together. This makes the autonomous runner auditable without hiding the runner command,
score policy, validation status, or primary comparison.

## 2026-05-23 Rubric Judge Slice

After the autonomous runner can execute slots and capture artifacts, the next safe scoring slice is
a local, auditable rubric judge rather than a cloud LLM judge.

The rubric judge should:

- read an explicit `impact-eval-rubric-v1` JSON file, defaulting by experiment only when omitted
- evaluate captured first-pass artifacts such as workspace diffs, final messages, result metadata,
  changed files, and untracked files
- write `rubric_judgment.json` before the normal `score.json` artifact
- record the rubric path and judgment artifact as score evidence
- keep command-exit scoring framed as execution health, not semantic correctness

This gives installed users an automated scoring loop for smoke and early benchmark development
without hiding the scoring basis. A future LLM judge can layer on top as a separate score policy,
but the artifact-backed deterministic rubric should remain the audit baseline.

## 2026-05-23 Family Discovery Slice

Before a family-level one-command benchmark runner, users need a discovery surface for available
benchmark families.

The product should not require users to already know names such as `ownership_boundary`. Add a
first-class family discovery step that can:

- list registered families from `evals/impact/families/*/spec.toml`
- show each family's historical issue, baseline ref, prompt family, and memory fixture counts
- identify whether matching prompt files and rubric files exist
- print the next runnable commands for `plan`, `prepare`, and eventually `benchmark`
- support JSON output so external automation can select a family programmatically

This should likely ship before or with a future `eval impact benchmark --family <name>` command.
Otherwise the benchmark runner is technically usable but not self-discoverable for installed users.

## 2026-05-23 Candidate Discovery Refinement

Family discovery should have two layers:

1. Formal family discovery lists runnable families already registered under
   `evals/impact/families/*/spec.toml`.
2. Candidate discovery scans AI wiki evidence for trial/error task shapes that might become future
   families.

Do not treat a broad product dimension such as "trial-and-error reduction" as a runnable family by
itself. A candidate family should show evidence of a concrete replayable mistake pattern:

- a prior agent failure, human correction, repeated retry, or missed-memory incident
- durable memory that should help a future agent avoid the same failure
- a baseline ref or historical state that can replay the task
- a prompt that does not leak the expected answer
- a rubric that can distinguish success, partial success, and failure from artifacts

The discovery output should therefore show readiness status such as `runnable`, `candidate`, or
`not_ready`, plus missing pieces. This makes the write-back loop explicit: task outcomes first
become AI wiki memory, repeated or high-value memory can become a candidate family, and only
runnable families should be passed to `prepare`, `run`, or a future one-command benchmark runner.

## 2026-05-23 Discovery Implementation Gaps

The project already has formal family specs and trial/error diagnostics, but they are not yet joined
into one discovery product surface.

Remaining implementation gaps:

- add `eval impact families` to list runnable specs from `evals/impact/families/*/spec.toml`
- add `eval impact family show <name>` or equivalent detail output
- include prompt presence, rubric presence, baseline ref, historical issue, memory fixture counts,
  and next commands in both text and JSON output
- expose existing `diagnose memory --focus trial-error` replay candidates through eval discovery
  instead of forcing users to know the diagnostics command
- define a candidate-readiness schema with missing pieces such as baseline, prompt, rubric, source
  incident, and replayable memory evidence
- add docs, CLI help, release smoke coverage, and tests before claiming installed users can discover
  benchmark families without reading the repo tree

## 2026-05-23 Discovery And Benchmark Implementation

The discovery slice has now shipped as package CLI surface:

- `eval impact families` lists registered runnable families
- `eval impact family show <name>` shows one family with prompts, rubric presence, fixtures, and
  next commands
- `eval impact family candidates` exposes trial/error replay candidates from diagnostics
- `eval impact family init --from-candidate ...` creates a draft family scaffold only when invoked
  explicitly
- `eval impact benchmark --family <name>` wraps prepare plus run for a family-level one-command
  benchmark

The implementation keeps candidate discovery report-oriented by default. It does not write
user-owned AI wiki docs or promote a broad product theme into a runnable family. Candidate readiness
distinguishes concrete replayable memory from broad high-reuse guidance and reports missing pieces
such as baseline, prompt, and rubric.

## 2026-05-23 Continuous Eval Loop Refinement

The deeper product goal is not static discovery of already-registered families. It is a continuous
loop:

1. normal agent work records trial/error evidence and AI wiki write-back
2. diagnostics cluster repeated or high-value failure patterns into candidate families
3. candidates accumulate source incidents, baseline refs, prompt drafts, and rubric drafts
4. mature candidates are explicitly promoted into runnable formal families
5. runnable families are benchmarked on a schedule
6. periodic reports compare current workflow performance against prior baselines

This requires a managed candidate queue and periodic report surface. Static `eval impact families`
and `family candidates` are only the discovery layer. They do not yet provide automatic family
crystallization, promotion gates, scheduled benchmark execution, trend reports, or regression alerts.

Keep automatic writes constrained: generated candidate queues and reports belong under
`ai-wiki/_toolkit/**`; formal family files under `evals/impact/**` should be created only by an
explicit apply/init/promote command or human-confirmed automation.

## 2026-05-23 Continuous Eval Loop Implementation

The continuous loop shipped as a staged product surface rather than a hidden auto-promotion path:

- `eval impact discover` refreshes a managed candidate queue under `ai-wiki/_toolkit/evals/`
  and preserves first-seen, last-seen, and seen-count state
- `eval impact family draft` writes managed candidate draft files without registering a formal
  family
- `eval impact family promote` is report-only by default and requires `--apply` before writing
  `evals/impact/**`
- `eval impact schedule report` writes periodic family/candidate/run reports under managed
  `_toolkit` paths
- `eval impact schedule run` benchmarks explicit families or `--all-runnable`, appends a run
  index, and refreshes the periodic report

This confirms the product boundary: discovery and reporting may be automatic and repeatable, but
new formal benchmark families still pass through a visible draft and promotion gate. That keeps the
system continuously iterable without letting noisy trial/error signals silently become benchmark
truth.

## 2026-05-24 Schedule Report Dogfood Fix

When dogfooding the continuous loop after reinstalling the local package, `eval impact discover`
was run with `--handle bochengyin --max-items 25`, but the follow-up `eval impact schedule report`
refreshed candidates with the default unfiltered 10-item view.

That made valid candidates from the just-run discovery appear as stale in the scheduled report.

Scheduled reports and scheduled runs should preserve the candidate discovery scope through explicit
filters such as `--handle`, `--since`, and `--candidate-max-items`. A periodic report should not
silently narrow the queue and convert legitimate candidates into stale entries just because the
report command used a smaller default refresh.

## Reuse Assessment

Use this when extending the eval product from report generation toward automated benchmark
execution. Do not start by auto-invoking agents until the run manifest and artifact lifecycle are
stable enough to audit.
