# Agent Failure Postmortem Pack

This pack turns the `ai-wiki-toolkit` impact-eval findings into concise coding-agent failure
postmortems. It is intended for public technical discussion, not as a statistically powered
benchmark.

The cases come from real `ai-wiki-toolkit` development and eval work. They are artifact-backed by
the notes under `evals/impact/notes/` and the synthesis in `evals/impact/reports/synthesis/current.md`.

## How To Read This

Each case follows the same structure:

- Problem: what broke or what the eval exposed.
- Impact: why it mattered for the workflow.
- Investigation: which evidence was inspected.
- Root cause: the actual failure mechanism.
- Fix: what changed or what the desired agent behavior became.
- Verification: how the result was checked.
- Prevention: what reusable rule or eval surface came out of it.

The failure categories are intentionally specific. The goal is to show that agent work can be
debugged and improved systematically, not just that a model sometimes succeeds or fails.

## Source Notes

- `evals/impact/reports/synthesis/current.md`
- `evals/impact/notes/manual_v2_cli_original_ownership_20260425_findings.md`
- `evals/impact/notes/manual_v2_cli_original_release_distribution_20260425_findings.md`
- `evals/impact/notes/manual_v2_cli_original_release_runtime_20260425_findings.md`
- `evals/impact/notes/manual_v2_cli_original_scaffold_prompt_workflow_20260425_findings.md`
- `evals/impact/notes/manual_v2_cli_original_postinstall_archive_20260430_findings.md`
- `evals/impact/notes/manual_v2_cli_original_aiwiki_evidence_20260501_findings.md`
- `evals/impact/notes/ownership_boundary_v0_failure.md`
- `evals/impact/notes/round1_process_lessons.md`

## Taxonomy Summary

| id | category | short name | evidence source |
| --- | --- | --- | --- |
| `AF-01` | eval harness | Prompt and baseline leakage | `ownership_boundary_v0_failure.md` |
| `AF-02` | implementation surface | Contributor workflow became package code | `manual_v2_cli_original_ownership_20260425_findings.md` |
| `AF-03` | memory specificity | Consolidated guidance lacked placement force | `manual_v2_cli_original_ownership_20260425_findings.md` |
| `AF-04` | context removal | Scaffold without adjacent memory picked the wrong surface | `manual_v2_cli_original_ownership_20260425_findings.md` |
| `AF-05` | release coordination | Musl release target missed build setup | `manual_v2_cli_original_release_distribution_20260425_findings.md` |
| `AF-06` | release runtime | Smoke gates without compatible build baseline | `manual_v2_cli_original_release_runtime_20260425_findings.md` |
| `AF-07` | workflow discipline | Scaffold names and prompt routing drifted | `manual_v2_cli_original_scaffold_prompt_workflow_20260425_findings.md` |
| `AF-08` | evidence integrity | Task coverage used flat shared evidence files | `manual_v2_cli_original_aiwiki_evidence_20260501_findings.md` |
| `AF-09` | evidence integrity | No-adjacent evidence run blurred reuse signals | `manual_v2_cli_original_aiwiki_evidence_20260501_findings.md` |
| `AF-10` | change quality | Easy bug fix still created unnecessary wiki churn | `manual_v2_cli_original_postinstall_archive_20260430_findings.md` |

## AF-01: Prompt And Baseline Leakage

Problem:

The first `ownership_boundary` eval design could not answer whether AI wiki memory changed an
agent's implementation surface choice.

Impact:

The run produced diffs, but the result was not valid evidence. Every variant was already pointed at
the correct repo-local surface, so the comparison could not separate memory effects from leaked task
guidance.

Investigation:

The failing design was reviewed in `ownership_boundary_v0_failure.md`. The review checked the repo
baseline, task prompt, changed files, and which surfaces every variant modified.

Root cause:

The baseline already contained `scripts/pr_flow.py` and `tests/test_pr_flow_script.py`, and the
prompt asked the agent to extend an existing repo-local PR flow. The answer was leaked through both
the codebase and the prompt.

Fix:

The repaired design moved to a historical baseline from before the helper existed, removed wording
that named the target surface, and controlled memory injection by variant.

Verification:

The later formal run used neutral slots, independent Codex CLI sessions, exported session manifests,
and a clean validator result before scoring.

Prevention:

Before treating an agent eval as evidence, verify that the target surface is not already present in
every variant and that the prompt does not name the desired solution path unless that is the point of
the eval.

## AF-02: Contributor Workflow Became Package Code

Problem:

In the formal `ownership_boundary` run, the no-AI-wiki primary control implemented a
contributor-only workflow as package functionality.

Impact:

That would ship a repo-local contributor helper as distributed product code, expanding the public
API surface for behavior that belonged in local scripts and workflow docs.

Investigation:

The `s01` artifacts in `manual_v2_cli_original_ownership_20260425_findings.md` showed new package
code under `src/ai_wiki_toolkit/contributor_workflow.py` and package CLI wiring in
`src/ai_wiki_toolkit/cli.py`.

Root cause:

Without reachable project memory, the agent treated "make a contributor workflow helper" as a normal
package feature request instead of a repo-local workflow request.

Fix:

The successful ambient AI wiki variant kept the helper under `scripts/`, added tests, updated local
workflow guidance, and avoided package CLI or package-module changes.

Verification:

The formal run validated one independent session per slot, no critical confounds, first-pass
capture artifacts, changed-test evidence, and manual scoring.

Prevention:

For coding-agent tasks that touch contributor workflows, route agents to ownership-boundary memory
before editing. The expected behavior is to choose the narrowest repo-local surface first.

## AF-03: Consolidated Guidance Lacked Placement Force

Problem:

The `aiwiki_linked_consolidated_only` ownership diagnostic failed even though it had adjacent
ownership guidance.

Impact:

This exposed that not all memory formats are equally useful. A promoted or consolidated note can be
too abstract to steer a concrete implementation decision.

Investigation:

The `s04` artifacts showed a wrapper under `scripts/`, but the core implementation still went into
`src/ai_wiki_toolkit/pr_flow.py`.

Root cause:

The available consolidated guidance did not carry enough task-specific placement force. It helped
the agent notice a repo-local script path, but not enough to keep core logic out of package code.

Fix:

The raw placement draft and ambient memory performed better in this family. The mechanism lesson is
to preserve concrete source-incident details until a consolidated note proves it can steer the same
decision.

Verification:

The diagnostic was compared against raw-only success, ambient success, no-AI-wiki failure, and strict
no-adjacent failure inside the same formal run.

Prevention:

When consolidating memory, keep concrete "do not put this in `src/`" placement rules where the task
needs surface selection, not just general ownership language.

## AF-04: Scaffold Without Adjacent Memory Picked The Wrong Surface

Problem:

The strict `aiwiki_scaffold_no_adjacent_memory` ownership diagnostic also failed the ownership
rubric.

Impact:

This narrowed the mechanism claim. The AI wiki scaffold alone was not enough; reachable adjacent
workflow memory mattered.

Investigation:

The `s06` artifacts showed a repo-local script and tests, but also core implementation under
`src/ai_wiki_toolkit/contributor_workflow.py`.

Root cause:

The agent had general scaffold behavior but lacked the adjacent memory that made the package-vs-repo
ownership boundary concrete for this task.

Fix:

The ambient workflow kept adjacent workflow memory available and selected the repo-local surface.

Verification:

The `s06` run used the same prompt, model, reasoning effort, and Codex CLI-first path as the formal
slots, then was validated and scored as a supplemental diagnostic.

Prevention:

Context routing should not over-trim adjacent memory for surface-choice tasks. A small number of
concrete ownership notes can be more valuable than broad scaffold instructions.

## AF-05: Musl Release Target Missed Build Setup

Problem:

The release-distribution no-AI-wiki control broadly expanded the public target matrix but missed the
Alpine musl build setup.

Impact:

The PR would look comprehensive across workflows, npm metadata, docs, Homebrew, and tests, but the
`linux-musl-x64` release path could still fail during PyInstaller packaging.

Investigation:

The `s01` artifacts in `manual_v2_cli_original_release_distribution_20260425_findings.md` showed
`linux-musl-x64` using `python:3.11-alpine` without `binutils`/`objdump` setup or root setup.

Root cause:

The agent coordinated many visible release surfaces but missed a less obvious platform-specific
build prerequisite.

Fix:

The ambient AI wiki variant added target-specific container setup, installed `binutils` before the
PyInstaller build, ran setup as root, added runtime checks, and kept npm `libc` metadata aligned.

Verification:

The run used six Codex CLI-first slots, exported session manifests, clean validation, artifact-backed
manual scoring, and changed-test review.

Prevention:

Release target changes need matrix-level checklists that include workflow matrix, archive names, npm
metadata, install guards, docs, Homebrew, and release-facing smoke checks.

## AF-06: Smoke Gates Without Compatible Build Baseline

Problem:

The release-runtime no-AI-wiki control added useful runtime smoke checks but left the Linux build on
`ubuntu-24.04`.

Impact:

The release process would catch the runtime failure, but it would still produce a binary from a
newer glibc baseline and rely on the smoke test to fail instead of preventing the bad artifact.

Investigation:

The `s01` artifacts in `manual_v2_cli_original_release_runtime_20260425_findings.md` showed release
and npm runtime smoke checks in `node:24-bookworm`, while the `linux-x64` build baseline remained
newer.

Root cause:

The agent interpreted the incident as a missing verification gate, not as a build-baseline
compatibility problem.

Fix:

The ambient AI wiki variant lowered the Linux build baseline to `ubuntu-22.04` and added pre-publish
runtime checks for release and staged npm install paths.

Verification:

The family used independent CLI sessions, captured artifacts, clean validator output, and manual
scoring against the release-runtime rubric.

Prevention:

For release runtime bugs, require agents to ask two questions: "Will this catch the failure?" and
"Will this produce a compatible artifact before publishing?"

## AF-07: Scaffold Names And Prompt Routing Drifted

Problem:

The no-AI-wiki scaffold/prompt slot implemented many correct surfaces but invented incompatible
names and older routing.

Impact:

That kind of drift would make future agents read the wrong directories, call the wrong skills, or
miss the managed start-of-task workflow.

Investigation:

The `s01` artifacts in `manual_v2_cli_original_scaffold_prompt_workflow_20260425_findings.md`
showed `problem-solutions/`, `ai-wiki-clarify-coding-task`, `ai-wiki-pr-review-learning`, and older
`_toolkit/index.md` prompt routing.

Root cause:

The agent understood the broad product request but did not preserve the repo's established naming,
skill, and prompt-routing contracts.

Fix:

The ambient AI wiki variant stayed aligned with `conventions/`, `problems/`, `features/`,
`ai-wiki-clarify-before-code`, `ai-wiki-capture-review-learning`, managed schema guidance, prompt
workflow updates, doctor checks, README, and tests.

Verification:

The formal run had complete session exports, no critical confounds, first-pass captures, and manual
scores for all six variants.

Prevention:

For scaffold or prompt behavior changes, route to memory that names the canonical directories,
skills, managed block boundaries, and required doctor/tests before editing.

## AF-08: Task Coverage Used Flat Shared Evidence Files

Problem:

The no-AI-wiki evidence-integrity slot found the task-level denominator idea but implemented the
wrong evidence shape.

Impact:

Flat shared evidence files would create collaboration conflicts and weaken per-handle auditability.
The wrong command shape would also make future task-level checks harder to distinguish from
document-level reuse events.

Investigation:

The `s01` artifacts in `manual_v2_cli_original_aiwiki_evidence_20260501_findings.md` showed task
coverage, document stats, managed-doc exclusion, docs, and tests, but used flat shared evidence files
and a `record-check` command rather than per-handle `record-reuse-check`.

Root cause:

The agent captured the high-level metric but missed the collaboration and audit contract: evidence
should be sharded by handle and document reuse should remain separate from task-level checks.

Fix:

The ambient AI wiki variant added per-handle document/task-check shards, `record-reuse-check`,
`refresh-metrics`, managed-doc exclusion, explicit write-back workflow text, docs, scaffold updates,
and tests.

Verification:

The product report classified the primary comparison as positive, and manual scoring checked the
full evidence contract rather than only the existence of a metric.

Prevention:

When adding telemetry, treat storage shape as part of correctness. Metrics that are hard to audit or
easy to conflict on are partial fixes, even when the headline count exists.

## AF-09: No-Adjacent Evidence Run Blurred Reuse Signals

Problem:

The strict no-adjacent evidence-integrity diagnostic partially solved the feature but weakened the
evidence signal.

Impact:

It would make downstream diagnostics noisier by mixing real reuse evidence with several
`not_helpful` observations and by keeping flat shared logs.

Investigation:

The `s06` artifacts in `manual_v2_cli_original_aiwiki_evidence_20260501_findings.md` showed
task-level reuse/write-back checks, managed-doc exclusion, separate document-vs-coverage stats, docs,
and tests, but missed per-handle sharding and logged several not-helpful document events.

Root cause:

Without adjacent memory about the evidence model, the agent preserved some semantic distinctions but
did not preserve the full telemetry contract.

Fix:

The successful variants used raw, consolidated, scaffold, or ambient memory that carried the desired
per-handle and task-check shape.

Verification:

The diagnostic was compared against successful raw, consolidated, scaffold, and ambient variants in
the same formal family.

Prevention:

Route and diagnosis telemetry should be treated as a trust boundary. Agents need explicit guidance
on which events count as knowledge reuse and which events are only workflow controls or noise.

## AF-10: Easy Bug Fix Still Created Unnecessary Wiki Churn

Problem:

In the postinstall archive family, every slot fixed the core bug, but some variants wrote new
user-owned AI wiki drafts or broadened implementation surfaces unnecessarily.

Impact:

Pass/fail success hid a change-quality issue. A coding agent can solve the user-visible bug while
still creating avoidable documentation churn or extra implementation footprint.

Investigation:

The postinstall note showed that `aiwiki_scaffold_no_target_memory`,
`aiwiki_linked_consolidated_only`, and `aiwiki_scaffold_no_adjacent_memory` each wrote a new
user-owned draft. The consolidated-only slot also touched an extra project file, `npm/shared.js`.

Root cause:

The task prompt localized the bug strongly enough for every condition to pass, but not every memory
state prevented the agent from rewriting an already-known lesson or broadening the code path.

Fix:

The ambient and raw-memory variants used the target memory, staged the archive safely, and avoided
new user-owned wiki churn.

Verification:

The family was neutral on first-attempt success, so the product signal came from change-profile
metrics: project files, managed telemetry, and user-owned wiki churn.

Prevention:

Postmortems should record quality signals, not only pass/fail. Track user-owned wiki churn,
unnecessary project-file footprint, and whether exact memory prevents rediscovering the same lesson.

## Interview Narrative

This pack supports four defensible claims:

1. Coding-agent failures were classified by mechanism, not just by outcome.
2. Eval harness failures were treated as first-class incidents and repaired before stronger claims
   were made.
3. The same evidence loop turned incidents into memory, memory into eval families, and eval families
   into improved routing and reporting.
4. Several failures were not "model could not code" failures. They were boundary, context, workflow,
   release, or measurement failures, which are exactly the kinds of issues an agent engineering
   system needs to expose.
