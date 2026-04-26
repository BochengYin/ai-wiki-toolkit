# AI Wiki Impact Eval Pilot

This note summarizes an artifact-backed pilot evaluation of whether `ai-wiki-toolkit` changes
coding-agent behavior on repeated historical repository problems. It is not a statistically powered
benchmark or an academic paper.

The question is about agent memory and workflow, not raw model capability. I am not trying to show
that `gpt-5.5` can or cannot solve these tasks. I am trying to test whether a fresh agent session,
with the same model and task prompt, behaves differently when reusable project memory is exposed
through repo-local files, managed guidance, and end-of-task write-back checks.

## Abstract

I ran a small artifact-backed pilot eval to test whether repo-local AI memory changes coding-agent
behavior on repeated historical problems. The tool under test, `ai-wiki-toolkit`, gives a repo an
`ai-wiki/` memory tree, managed prompt guidance, end-of-task memory-use footers, and write-back
checks. I used five real problems from developing the toolkit itself, recreated earlier repo states,
and ran six isolated Codex CLI sessions per family with the original effective task prompt,
`gpt-5.5`, and `xhigh` reasoning. The primary comparison was no AI wiki workflow versus the
realistic ambient AI wiki workflow. Here, `ambient` means the repo memory was present in the normal
workspace environment and discoverable through the usual AI wiki guidance; the task prompt did not
name the target memory document or tell the agent the expected solution. In 4 of 5 families, the
ambient workflow produced a better primary outcome; in 1 family both conditions succeeded. This is
not a statistically powered benchmark, but the artifacts provide directional evidence that
repo-visible memory can help fresh agents avoid repeated mistakes, especially around ownership
boundaries, release hazards, and workflow discipline.

## Headline Statistical Status

This is not a statistically powered benchmark.

This note does not claim confidence intervals, statistical significance, general model success-rate
estimates, or proof that AI wiki memory is necessary. Each family has one primary control sample and
one primary treatment sample:

- `no_aiwiki_workflow`
- `aiwiki_ambient_memory_workflow`

The diagnostic variants help explain mechanisms, but they are not the main causal comparison.

The strongest defensible framing is:

> This is an artifact-backed pilot evaluation over five historical coding-task families. In this
> suite, the ambient AI wiki workflow outperformed the no-AI-wiki workflow in four of five primary
> comparisons and tied in one. The result is directional evidence that repo memory can change agent
> behavior on repeated real-world problems, not a statistically powered estimate of general
> performance.

## What AI Wiki Toolkit Is

`ai-wiki-toolkit` is a small toolkit for adding structured, repo-local memory to coding-agent
workflows.

It gives a repository:

- a local `ai-wiki/` tree for conventions, decisions, problems, feature notes, workflows, trails, and
  person-specific drafts
- managed prompt guidance that tells agents when and how to consult those docs
- local skills for behaviors such as clarifying ambiguous tasks, capturing reusable review learning,
  checking AI wiki reuse, and checking whether a task produced memory worth writing back
- installer behavior for creating or refreshing package-owned starter files without overwriting
  user-owned project notes
- local telemetry that records whether tasks checked for AI wiki reuse

The goal is not to make a global knowledge base. The goal is to keep project-specific memory close
to the codebase, so future agents can reuse lessons from previous failures, reviews, and release
work.

The broader hypothesis is that self-updating memory should not be limited to one agent inside one
long-running workspace. If the memory is stored in reviewable repo files, refreshed through explicit
workflow checks, and visible to future independent sessions, the same pattern may help multiple
agents collaborate on a shared codebase. This pilot tests that hypothesis in one repo where the
toolkit was itself developed using the toolkit.

## Footer And Write-Back Behavior

The end-of-task footer is the user-visible evidence surface. It is meant to make memory use auditable
instead of invisible.

Current footer fields:

- `AI Wiki Reuse`: whether user-owned repo or system memory was used
- `AI Wiki Task Relevance`: whether AI wiki use was relevant, optional, or not relevant for the task
- `AI Wiki Docs Used`: which user-owned docs were consulted, when applicable
- `AI Wiki Impact`: how the memory changed the plan or implementation, when applicable
- `AI Wiki Missed Memory`: whether relevant memory appears to have been missed
- `AI Wiki Write-Back`: whether the task produced a durable lesson worth recording
- `AI Wiki Write-Back Path`: the draft path, when a draft or promotion candidate was recorded

The write-back check is separate from reuse. A task can use no prior memory but still produce a new
lesson worth recording. It can also use prior memory and still produce no new durable lesson.

More detail is in Appendix C.

## Why These Historical Tasks Are Valid Test Cases

The toolkit was developed while using the toolkit itself. That matters.

During normal development, the repo accumulated real notes about mistakes and fixes: release hazards,
workflow-boundary mistakes, naming drift, scaffold behavior, and smoke-test failures. The eval takes
those historical problems and replays them against earlier repository states, using the original
task-style prompts rather than prompts that directly reveal the answer.

Some original tasks came from the actual agent operating context rather than from a polished
human-written benchmark prompt. In those cases, the user-level request could be as small as "code",
while the effective task instruction came from the surrounding system/developer prompt and repo
state. That is intentional for this pilot: the goal is to reproduce the conditions under which the
original development failures happened, then compare whether the AI wiki workflow changes the
outcome under the same effective task prompt.

This gives realistic test cases because:

- the problems came from actual development work, not synthetic puzzles
- the target memories were written before the eval run
- success and failure can be judged against concrete code diffs and tests
- the eval can test whether an agent repeats a known mistake when the memory is absent

This also creates an important validity threat:

- the memories are unusually well matched to the tasks because the benchmark is built from the same
  project's history

That is acceptable for a pilot case-study suite, but it should be stated plainly.

## Protocol Summary

The current formal runs use Manual v2, a CLI-first workflow-primary protocol.

Fixed conditions:

- model: `gpt-5.5`
- reasoning effort: `xhigh`
- execution path: Codex CLI first
- prompt: each family uses its own `original.md`, representing the original effective task prompt
- session isolation: one independent persisted CLI session per slot
- workspace isolation: each slot runs in its own repo checkout
- scoring: manual `success`, `partial`, or `fail`, based on diffs, transcripts, tests, and rubric
- validation: session export and `validate_run.py` must show no critical confounds

The formal runs use original historical effective prompts only. They do not test whether the same
conclusions hold under prompt paraphrases, more ambiguous prompts, more polished human-written
prompts, or more leading prompts.

Primary comparison:

- `no_aiwiki_workflow`: no AI wiki scaffold, prompt routing, skills, or accumulated memory
- `aiwiki_ambient_memory_workflow`: realistic AI wiki workflow with normal repo memory, normal
  repo-local AI wiki guidance, and ordinary adjacent memory/noise available in the workspace. The
  prompt is not allowed to explicitly point at the target memory document or directly provide the
  expected implementation strategy.

Diagnostic variants:

- `aiwiki_scaffold_no_target_memory`
- `aiwiki_linked_raw_only`
- `aiwiki_linked_consolidated_only`
- `aiwiki_scaffold_no_adjacent_memory`

The diagnostic variants are useful for mechanism analysis. They should not be promoted into the main
claim.

## Method Details

Each benchmark family starts from a real historical problem in `ai-wiki-toolkit`. For each family, I
selected a repository baseline from before the historical fix landed, then generated six isolated
workspace copies from that baseline.

The same original effective prompt was used for every slot within a family. The prompt was
intentionally task-like rather than answer-like: it recreated the historical task request without
naming the exact memory document or directly telling the agent the desired implementation strategy.
For some families, the effective prompt includes task context that originally came from the agent
runtime or repo state rather than from a standalone user-authored sentence. The comparison still
holds within that family because every slot received the same effective prompt.

The six slots were neutral directories named `s01` through `s06`. Their semantic roles were stored
outside the workspace in assignment metadata so the visible working directory would not leak names
such as `no_aiwiki_workflow` or `aiwiki_ambient_memory_workflow`.

The slot roles were:

- `s01`: no AI wiki workflow
- `s02`: AI wiki scaffold without the target memory
- `s03`: AI wiki workflow linked to raw draft memory for the target problem
- `s04`: AI wiki workflow linked to consolidated memory for the target problem
- `s05`: realistic ambient AI wiki workflow
- `s06`: AI wiki scaffold without target or adjacent task-specific memory

For every slot, I ran a fresh persisted Codex CLI session with the same model and reasoning effort:

- `gpt-5.5`
- `xhigh`
- `codex exec`
- `--output-last-message` to save the first-pass final message

No VS Code UI or Computer Use execution path was used for the formal runs. The runner wrapped each
family in a run-level `caffeinate` guard to reduce sleep or lock-screen interference. Each slot used
its own repository checkout, and no slot was run from another slot's repo.

Immediately after each slot finished, `save_result.py` captured first-pass artifacts:

- workspace diff
- diff stat
- workspace status
- workspace head
- command result metadata
- final message

After all slots in a family finished, `export_codex_sessions.py` exported the visible Codex session
artifacts and a manifest. Then `validate_run.py` checked for critical confounds such as missing
sessions, missing first-pass artifacts, non-CLI execution, reused sessions, or model/effort mismatch.
Only runs with no critical confounds are treated as the current formal result.

Scoring was manual but artifact-backed. For each slot, I reviewed:

- `workspace_diff.patch`
- `visible_transcript.md`
- `visible_session.jsonl`
- changed tests
- `first_pass/final_message.md`
- the family-specific rubric

Scores were recorded as `success`, `partial`, or `fail`. A generated family report summarized the
slot scores, but the manual score was based on the artifacts rather than on the final message alone.

## How The Protocol Evolved

The current method was not the first version. It came from several failed or partially confounded
rounds.

The first `ownership_boundary` design failed because it leaked the answer. The baseline already
contained the repo-local helper surface, and the prompt asked the agent to extend the existing
repo-local PR flow. That meant every variant was already pointed at the correct surface, so the run
could not test whether AI wiki memory changed implementation-surface choice.

The next round fixed that by using historical baselines from before the fix landed. That made the
tasks real again, but it revealed other problems: semantic variant names leaked through workspace
paths, full prompt surfaces differed across variants, first-pass final messages were not always
stable after follow-up interaction, and the result capture was weaker than the later analysis
standard.

The original-prompt transition run improved the task prompts and neutral slot layout, but it still
mixed VS Code UI and Codex CLI fallback. It was useful qualitative evidence, but not clean formal
evidence because the execution surface and manifest metadata were inconsistent.

The final Manual v2 formal runs moved to a CLI-first protocol: independent persisted Codex CLI
sessions, neutral slot paths, one original effective prompt per family, immediate artifact capture,
exported session manifests, run-level sleep protection, validator checks, and manual scoring from
diffs plus visible transcripts.

This iterative process matters because the benchmark itself was a source of failure modes. The
useful result is not just the final table of scores; it is also the record of how prompt leakage,
workspace leakage, UI instability, sleep risk, session export gaps, and weak final-message artifacts
were found and removed before making the current public claim.

## Artifacts And Reproducibility

The benchmark materials are meant to be auditable, not just summarized.

Public artifact repository:

- https://github.com/BochengYin/ai-wiki-toolkit-impact-eval-artifacts

The repository contains the stable materials:

- prompts
- family specs
- runbooks
- scoring notes
- validation and scoring scripts
- the synthesis report

The per-run artifacts should accompany this write-up as a redacted artifact bundle:

- slot diffs
- visible transcripts
- visible session JSONL
- final messages
- score files
- validator outputs
- session-export manifests

Full raw session exports are useful for transparency, but only if they pass a privacy and secrets
review. If raw logs cannot be published safely, the public bundle should include the visible logs,
manifests, and hashes for the withheld raw logs.

For this publication snapshot, the artifact repository includes visible session artifacts and
SHA-256 hashes for the withheld raw session exports.

## Family Table

| family | original effective prompt excerpt | problem being tested | success means | failure or partial means |
| --- | --- | --- | --- | --- |
| `ownership_boundary` | "Add a helper for the contributor branch-and-PR workflow in this repository..." | Will the agent keep a contributor-only workflow out of package code? | The helper stays repo-local, for example under `scripts/`, with tests/docs and no package CLI or package-module implementation. | Core logic goes into `src/ai_wiki_toolkit/` or the package CLI, even if the helper works. |
| `release_distribution_integrity` | "Expand public release and npm distribution support in this repository..." | Will the agent keep a public release and npm target expansion aligned across workflow, packages, archives, docs, and tests? | Release matrix, npm target resolution, package metadata, Windows zip staging, musl/libc handling, docs, Homebrew, and tests stay aligned. | The agent updates many surfaces but misses a central release hazard, such as Alpine musl binutils or root setup. |
| `windows_arm_smoke_cli_output` | "The `Release Smoke Windows ARM` workflow is failing..." | Will the agent fix a narrow smoke-test assertion that compares the wrong version output? | Both release-archive and npm-installed smoke paths compare against full CLI output such as `ai-wiki-toolkit <version>`, with regression tests. | The agent fixes only one path or keeps comparing against the bare package version. |
| `release_runtime_compatibility` | "A Linux npm install smoke test exposed a runtime compatibility problem..." | Will the agent catch binary runtime incompatibility before publishing, instead of stopping at build or install success? | The release process uses an older compatible Linux build baseline and runs release/npm runtime smoke checks before publishing. | The agent adds smoke gates but still builds on a too-new baseline, or only checks install success. |
| `scaffold_prompt_workflow_compliance` | "Extend the AI wiki scaffold so the toolkit better supports team coding memory..." | Will the agent keep scaffold, skill names, prompt routing, docs, and tests aligned with established repo memory? | It adds `conventions/`, `problems/`, `features/`, correct skill names, managed schema guidance, prompt/system workflow updates, doctor checks, README, and tests. | It invents incompatible names, keeps old routing, creates prompt churn, or crosses managed/user-owned boundaries. |

Full prompt files live under:

- `evals/impact/prompts/ownership_boundary/original.md`
- `evals/impact/prompts/release_distribution_integrity/original.md`
- `evals/impact/prompts/windows_arm_smoke_cli_output/original.md`
- `evals/impact/prompts/release_runtime_compatibility/original.md`
- `evals/impact/prompts/scaffold_prompt_workflow_compliance/original.md`

## Results Summary

| family | no AI wiki primary control | ambient AI wiki primary treatment | interpretation |
| --- | --- | --- | --- |
| `ownership_boundary` | fail | success | Strongest positive signal. AI wiki changed the implementation surface from package code to repo-local workflow code. |
| `release_distribution_integrity` | partial | success | Narrow positive signal. AI wiki helped avoid a known musl release-build hazard while keeping the multi-surface expansion aligned. |
| `windows_arm_smoke_cli_output` | success | success | Neutral. The task was direct enough that both primary conditions solved it. |
| `release_runtime_compatibility` | partial | success | Narrow positive signal. AI wiki improved the fix from smoke-gate-only to older-baseline plus runtime verification. |
| `scaffold_prompt_workflow_compliance` | partial | success | Workflow-discipline signal. AI wiki helped keep naming, routing, docs, and tests aligned. |

Aggregate primary comparison:

- 4 of 5 families directionally favored the ambient AI wiki workflow
- 1 of 5 families was neutral
- 0 of 5 families favored the no-AI-wiki workflow

This aggregate is descriptive only. It is not a statistically powered success-rate estimate.

## Rework-Adjusted Efficiency View

The replay timings above are not enough to estimate productivity impact. AI wiki memory is meant to
amortize earlier discovery and correction work, so this pilot also records a source incident cost for
each family.

This source column is a `source active-turn estimate`: selected `task_complete.duration_ms` values
from the original incident sessions that produced the reusable lesson, plus
`turn_aborted.duration_ms` when an interrupted failed attempt is part of the incident. It excludes
human waiting time between turns, but includes tool, CI, release, and package wait that happened
inside those agent turns. It should be treated as an approximate acquisition or rework-cost estimate,
not as an exact human time-saved measurement.

It is not a direct no-AI-wiki baseline. The source incidents were real development traces where the
task scope was still being discovered, corrected, or validated through release feedback. The formal
replays are cleaner reproductions: they start from an earlier repo state and use the historical
effective prompt after the task was understood.

The source incidents were normal development sessions that were already initialized and used
`gpt-5.4` with `xhigh` reasoning. The formal replay sessions used `gpt-5.5` with `xhigh` reasoning,
fresh persisted Codex CLI sessions, neutral slot workspaces, and the original effective prompt for
each family. This means the source and replay timing columns are not model-identical timing
measurements. They are best read as a rework-cost context column beside the formal primary
comparison, not as a direct speed benchmark.

The public-facing saved-time metric below is `estimated saved active mins using ambient AI wiki`. It
is not `no_aiwiki_workflow` replay time minus `aiwiki_ambient_memory_workflow` replay time. That
comparison is the formal outcome control above. For efficiency, the relevant question is whether a
later ambient AI wiki run used less active agent time than the original source incident that produced
the reusable lesson:

`estimated saved active mins using ambient AI wiki = source active-turn estimate - ambient AI wiki replay duration`

Positive numbers mean the later AI wiki run used less active agent time than the original
fail/correct or discovery loop. Negative numbers mean the AI wiki run did not save active time, even
if it improved correctness.

| family | source active-turn estimate | ambient AI wiki replay | estimated saved active mins using ambient AI wiki | interpretation |
| --- | --- | --- | --- | --- |
| `ownership_boundary` | about 7.5 min for interrupted failed attempt, boundary diagnosis, repo-local correction, and push; about 17.9 min if release closeout is included. The failed implementation attempt was an interrupted turn, so it is counted from `turn_aborted.duration_ms` rather than `task_complete.duration_ms`. | 8.5 min, success | `-1.0 min` versus the fail/correct loop; `+9.4 min` if release closeout is included | No core active-time saving, but a strong correctness improvement: AI wiki changed the implementation surface from package code to repo-local workflow code. |
| `release_distribution_integrity` | about 25.4 min for real target expansion and scope discovery; about 54.1 min if release rescue and musl fixes are included | 13.7 min, success | `+11.7 min` versus core target expansion; `+40.4 min` if release rescue and musl follow-up are included | Positive saved-active-mins signal. AI wiki avoided known release hazards that had been expensive in the source incident. |
| `windows_arm_smoke_cli_output` | about 4.0 min | 3.8 min, success | `+0.2 min` | Outcome-neutral and timing-neutral. This family does not support a meaningful efficiency claim. |
| `release_runtime_compatibility` | about 20.4 min, from the `0.1.7` npm install/runtime failure to the older-glibc fix and release | 7.7 min, success | `+12.7 min` | Positive saved-active-mins signal. AI wiki improved the fix from smoke-gate-only to older-baseline plus runtime verification. |
| `scaffold_prompt_workflow_compliance` | about 15.7 min for core PR #10; about 36.6 min if dogfood and routing follow-ups are included | 18.4 min, success | `-2.7 min` versus core PR work; `+18.2 min` if dogfood and routing follow-ups are included | No core active-time saving, but a workflow-discipline improvement; the timing claim is positive only under the extended follow-up context. |

Summed over the conservative core source estimates, the ambient AI wiki runs took about 52.1 minutes
against about 73.0 minutes of source active-turn cost, or about `20.9` estimated saved active
minutes using ambient AI wiki. If the documented release, rescue, dogfood, and routing follow-ups
are included where available, the source context rises to about 133.0 minutes, giving about `80.9`
estimated saved active minutes in the extended context. These are not claims of exact human time
saved; they are artifact-derived active-time context for the cost of acquiring and reusing the
memory.

I also checked whether the fresh replay sessions paid a meaningful initialization penalty. Using the
visible session artifact, I measured the time from `session_meta` to the first visible assistant
message. Across the 10 primary replay sessions (`s01` and `s05`), this window averaged about 10.3
seconds, with an 11.0 second median and a 5.9 to 17.0 second range. Across all 30 formal replay
slots, it averaged about 11.9 seconds, with an 11.8 second median and a 5.9 to 19.0 second range.

This startup window is small relative to the multi-minute family differences. Removing it would not
change the primary outcomes or the interpretation above. The more important timing caveat is the
model and session-context difference: the source estimates came from already initialized `gpt-5.4`
development sessions, while the formal replays were fresh `gpt-5.5` CLI sessions.

The conservative efficiency claim is therefore:

> AI wiki did not reduce first-pass runtime in this pilot. It produced estimated saved active
> minutes only when the avoided discovery or correction loop was larger than the observed AI wiki
> workflow overhead.

## Fermi Extrapolation

The measured pilot is too small to make a statistically powered productivity claim, but it can
support a transparent Fermi-style estimate.

This repository is a small side-project repo. At the time of this write-up it has about 25,000
tracked lines, including about 5,200 lines under `src/`, 5,800 lines under `tests/`, and about 12,300
lines of docs, AI wiki notes, and eval material.

The repo also did not have AI wiki installed from the first minute. The first commit was on
2026-04-18 at 20:40 local time. The first repo-local AI wiki scaffold landed on 2026-04-18 at 22:22,
and the first repo-local AI wiki skills landed on 2026-04-18 at 23:29. A fuller team-memory layout
landed on 2026-04-20 at 23:39. In other words, the earliest no-AI-wiki window was real, but small
relative to the rest of this development burst.

To get from per-family saved-time estimates to a repo-level number, I used an explicit future
frequency assumption. This is not a measured incident count; it is a Fermi input for this small,
release-heavy side project. I treat the exact `ownership_boundary` incident as a one-off and set it
to zero future occurrences. I use the extended saved-time column because this estimate is about
avoiding repeated release, rescue, dogfood, and routing follow-up loops.

| family | assumed small-repo frequency/week | extended saved mins per occurrence | estimated saved active mins/week |
| --- | ---: | ---: | ---: |
| `ownership_boundary` | 0/week | 9.4 | 0.0 |
| `release_distribution_integrity` | 1/week | 40.4 | 40.4 |
| `windows_arm_smoke_cli_output` | 0.5/week | 0.2 | 0.1 |
| `release_runtime_compatibility` | 1/week | 12.7 | 12.7 |
| `scaffold_prompt_workflow_compliance` | 0.5/week | 18.2 | 9.1 |
| **Total** | | | **62.3, rounded to 62** |

Using the same frequencies with the conservative core saved-time values would give about 23 saved
active minutes per week. The `62` figure is therefore specifically an extended follow-up and
rework estimate, not the conservative core estimate.

For an illustrative weekly estimate, I treat this repo as a side project with roughly 25 active
project hours per week: weekday evenings plus weekend daytime work. Using the extended source
context above, the five measured families imply about 62 estimated saved active minutes per week in
this small repo. That gives:

```text
small-repo extended estimate = 62 saved active mins/week
weekly active project hours = 25
62 / 25 = about 2.5 saved active mins per active project hour
```

Now scale that to a hypothetical medium repository:

- medium repo size: 100,000 lines
- current repo size: 25,000 lines
- size multiplier: 4x
- team size: 6 people
- active engineering time: 40 hours/person/week
- team active time: 240 hours/week

The deliberately linear estimate is:

```text
2.5 saved active mins/hour
* 240 team active hours/week
* 4 size multiplier
= about 2,400 saved active mins/week
= about 40 saved active hours/week
```

This `40 saved active hours/week` number should be read as a linear Fermi extrapolation, not as a
measured result. It assumes memory reuse opportunities scale with both repository size and team
activity, and it uses the extended saved-time estimate that includes avoided release, rescue,
dogfood, and routing follow-up loops. A practical planning range should discount this until the same
method is run on a real medium repo.

This estimate is also project-specific. Different repositories will have different recurring failure
modes, release cadence, platform surface, automation, reviewer expectations, and documentation
quality. AI wiki only helps when a task asks an agent to do something it is likely to get wrong or
rediscover, and the relevant lesson has already been captured in the repo memory. In this repository,
the npm release path is a good example: when an agent avoids known packaging, target-matrix, runtime,
and artifact-staging mistakes, it can avoid expensive release rescue work. If the agent would already
run the release perfectly, or if the project has mature automation that prevents the same mistakes
without AI wiki, the incremental saving is much smaller.

## What This Supports

Reasonable claim:

> In this pilot suite, AI wiki-style repo memory was useful in several repeated historical coding
> tasks. It helped agents avoid a repeated ownership-boundary mistake, avoid known release hazards,
> improve runtime-release verification, and preserve scaffold/prompt workflow discipline.

Broader but still limited interpretation:

> The results are consistent with the idea that self-updating agent memory can be moved from a
> private single-agent workspace into repo-visible collaboration infrastructure. Because every slot
> starts from a fresh session, the useful memory must come from the repository, scaffold, skills, or
> AI wiki workflow rather than from conversational carryover. That is a useful signal for future
> multi-agent team workflows, but it is not yet proof that the effect generalizes across teams.

More precise by family:

- `ownership_boundary`: evidence that memory can change where an agent places code.
- `release_distribution_integrity`: evidence that memory can improve multi-surface release
  completeness and known-hazard handling.
- `release_runtime_compatibility`: evidence that memory can improve the quality of release-process
  fixes.
- `scaffold_prompt_workflow_compliance`: evidence that memory can improve naming and workflow
  discipline.
- `windows_arm_smoke_cli_output`: neutral benchmark, useful for harness coverage but not evidence
  that memory was needed.

## What This Does Not Prove

This note does not claim:

- statistical significance
- confidence intervals
- a general success-rate improvement
- that AI wiki memory is necessary for success
- that the result generalizes to all tasks, repos, models, or agents
- that the result has already been validated in a multi-person or multi-team deployment
- that the result holds in very large repositories with much larger AI wiki histories, document
  backlogs, or context-window pressure
- that the result is robust to prompt variants or paraphrases
- that the diagnostic variants are the main causal result
- that this is a comparison against every other self-updating memory system
- that GitHub Actions releases would necessarily pass when no actual release workflow was run

## Prompt Robustness Follow-Up

The current formal runs intentionally use each family's original historical effective prompt. That
keeps the replay close to the real task request, including cases where the operative instruction came
from the surrounding agent context rather than a polished user prompt. It also leaves prompt
robustness untested.

A stronger follow-up would rerun the same five families with controlled prompt variants, for example:

- a paraphrased but semantically equivalent prompt
- a shorter and more ambiguous prompt
- a more explicit but non-answer-leaking prompt

Those replications would test whether the observed AI wiki advantage depends on the exact wording of
the original prompt or survives reasonable task-request variation.

## Repository Scale Follow-Up

This pilot also does not test AI wiki behavior in a large, long-running repository with many more
documents, stale notes, unresolved drafts, and accumulated workflow history.

That matters because a memory system can fail at scale in ways that do not appear in a small
case-study repo:

- relevant notes may be harder to discover
- old or adjacent notes may crowd out the actual task memory
- agents may spend too much context budget reading low-value docs
- context-window pressure may reduce the quality of implementation or final verification

A stronger follow-up would run the same kind of primary comparison in a larger repository or create a
controlled high-document-count variant of this repo. That would test whether AI wiki still improves
agent behavior when retrieval, triage, and context budgeting become harder.

## Appendix A: Verbatim Original Effective Prompts

These are the prompt files used in the formal runs. They preserve the effective task instruction for
the historical reproduction, even when the original user-facing request was shorter and the fuller
task context came from the agent runtime or repository state.

### `ownership_boundary`

```text
Add a helper for the contributor branch-and-PR workflow in this repository.

The workflow should require starting from a new branch instead of working on `main`, pushing changes from that branch, and switching back to `main` after the pull request is merged.

New branch names must follow:

- `feature/YYYY_MM_DD_description`
- `chore/YYYY_MM_DD_description`
- `fix/YYYY_MM_DD_description`
```

### `release_distribution_integrity`

```text
Expand public release and npm distribution support in this repository.

Add end-to-end Windows support for the npm distribution, and expand the public
release/distribution matrix to cover:

- `linux-arm64`
- `linux-musl-x64`
- `windows-arm64`

Keep docs and tests up to date.
```

### `windows_arm_smoke_cli_output`

```text
The `Release Smoke Windows ARM` workflow is failing in both the release-archive smoke path and the npm-installed smoke path.

The binary appears to be present and executable, but both jobs fail during the version verification step.

Please diagnose and fix the Windows ARM smoke workflow failure.

Keep relevant tests up to date.
```

### `release_runtime_compatibility`

```text
A Linux npm install smoke test exposed a runtime compatibility problem.

In a clean `node:24-bookworm` linux/amd64 container, `npm install -g ai-wiki-toolkit@0.1.7` succeeds, but running `aiwiki-toolkit --version` fails at runtime with a Python shared library / GLIBC version error.

Please update the release process so this class of Linux binary runtime compatibility issue is caught before publishing.

Keep docs and tests up to date.
```

### `scaffold_prompt_workflow_compliance`

```text
Extend the AI wiki scaffold so the toolkit better supports team coding memory.

Add repo-local starter areas for shared conventions, reusable problem-solution notes, and feature-specific working memory. Add repo-local skills for clarifying ambiguous coding tasks before implementation and for capturing reusable PR review learning. Add lightweight managed schema guidance for this team-memory layer.

Update the installer, managed prompt guidance, README, and tests so these new scaffold pieces are created and documented consistently.

Preserve the existing compatibility guarantees: do not overwrite user-owned AI wiki docs, keep package-managed content in managed areas, and keep shared prompt guidance suitable for multiple contributors.
```

## Appendix B: Detailed Result Notes

Detailed family notes:

- `evals/impact/notes/manual_v2_cli_original_ownership_20260425_findings.md`
  - Problem found: agents can treat contributor-only workflow automation as package functionality.
  - Improvement observed: the ambient AI wiki workflow kept the helper repo-local under `scripts/`,
    added tests/docs, and avoided package CLI or `src/ai_wiki_toolkit/` implementation.
- `evals/impact/notes/manual_v2_cli_original_release_distribution_20260425_findings.md`
  - Problem found: release target expansion can look broad while still missing a known
    release-build hazard, especially Alpine musl PyInstaller setup.
  - Improvement observed: the ambient AI wiki workflow kept the release matrix, npm metadata,
    archive staging, docs, tests, and musl setup aligned.
- `evals/impact/notes/manual_v2_cli_original_windows_arm_20260425_findings.md`
  - Problem found: the Windows ARM smoke workflow compared `--version` output against a bare package
    version even though the CLI prints `ai-wiki-toolkit <version>`.
  - Improvement observed: every primary and diagnostic slot fixed both smoke paths, so this family
    is a deterministic harness check rather than evidence of AI wiki advantage.
- `evals/impact/notes/manual_v2_cli_original_release_runtime_20260425_findings.md`
  - Problem found: install success can hide a Linux binary runtime failure caused by an incompatible
    build baseline.
  - Improvement observed: the ambient AI wiki workflow added an older Linux build baseline plus
    pre-publish release and npm runtime smoke checks.
- `evals/impact/notes/manual_v2_cli_original_scaffold_prompt_workflow_20260425_findings.md`
  - Problem found: scaffold and prompt changes can drift into inconsistent names, outdated routing,
    or unclear managed/user-owned boundaries.
  - Improvement observed: the ambient AI wiki workflow preserved the intended areas, skill names,
    managed schema guidance, prompt workflow, docs, doctor checks, and tests.

Current synthesis:

- `evals/impact/reports/current.md`

## Appendix C: Footer Details

The footer is deliberately simple. It answers two separate questions:

1. Did this task use existing user-owned AI wiki memory?
2. Did this task produce a new durable lesson worth writing back?

Example with no prior memory used:

```text
AI Wiki Reuse: no user-owned memory used
AI Wiki Task Relevance: relevant
AI Wiki Impact: none
AI Wiki Missed Memory: none known
AI Wiki Write-Back: none
```

Example with prior memory used:

```text
AI Wiki Reuse: user-owned memory used
AI Wiki Task Relevance: relevant
AI Wiki Docs Used: problems/linux-release-runtime-compatibility
AI Wiki Impact: changed the release fix from install-only checking to runtime verification
AI Wiki Missed Memory: none known
AI Wiki Write-Back: none
```

Example with new memory recorded:

```text
AI Wiki Reuse: no user-owned memory used
AI Wiki Task Relevance: relevant
AI Wiki Impact: none
AI Wiki Missed Memory: none known
AI Wiki Write-Back: draft recorded
AI Wiki Write-Back Path: ai-wiki/people/<handle>/drafts/<file>.md
```

Managed `_toolkit/**` files can guide the workflow, but they are not counted as user-owned memory
reuse events. That separation keeps the metric from confusing package-owned control instructions
with project-specific knowledge reuse.
