# AI Wiki Impact Eval Pilot

This note summarizes an artifact-backed pilot evaluation of whether `ai-wiki-toolkit` changes
coding-agent behavior on repeated historical repository problems. It is not a statistically powered
benchmark or an academic paper.

## Abstract

I ran a small artifact-backed pilot eval to test whether repo-local AI memory changes coding-agent
behavior on repeated historical problems. The tool under test, `ai-wiki-toolkit`, gives a repo an
`ai-wiki/` memory tree, managed prompt guidance, end-of-task memory-use footers, and write-back
checks. I used five real problems from developing the toolkit itself, recreated earlier repo states,
and ran six isolated Codex CLI sessions per family with the original prompt, `gpt-5.5`, and `xhigh`
reasoning. The primary comparison was no AI wiki workflow versus the realistic ambient AI wiki
workflow. In 4 of 5 families, the ambient workflow produced a better primary outcome; in 1 family
both conditions succeeded. This is not a statistically powered benchmark, but the artifacts provide
directional evidence that repo memory can help agents avoid repeated mistakes, especially around
ownership boundaries, release hazards, and workflow discipline.

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
- prompt: each family uses its own `original.md`
- session isolation: one independent persisted CLI session per slot
- workspace isolation: each slot runs in its own repo checkout
- scoring: manual `success`, `partial`, or `fail`, based on diffs, transcripts, tests, and rubric
- validation: session export and `validate_run.py` must show no critical confounds

The formal runs use original historical prompts only. They do not test whether the same conclusions
hold under prompt paraphrases, more ambiguous prompts, or more leading prompts.

Primary comparison:

- `no_aiwiki_workflow`: no AI wiki scaffold, prompt routing, skills, or accumulated memory
- `aiwiki_ambient_memory_workflow`: realistic AI wiki workflow with normal repo memory and ambient
  noise

Diagnostic variants:

- `aiwiki_scaffold_no_target_memory`
- `aiwiki_linked_raw_only`
- `aiwiki_linked_consolidated_only`
- `aiwiki_scaffold_no_adjacent_memory`

The diagnostic variants are useful for mechanism analysis. They should not be promoted into the main
claim.

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

| family | original prompt | problem being tested | success means | failure or partial means |
| --- | --- | --- | --- | --- |
| `ownership_boundary` | "Add a helper for the contributor branch-and-PR workflow in this repository..." | Will the agent keep a contributor-only workflow out of package code? | The helper stays repo-local, for example under `scripts/`, with tests/docs and no package CLI or package-module implementation. | Core logic goes into `src/ai_wiki_toolkit/` or the package CLI, even if the helper works. |
| `release_distribution_integrity` | "Expand public release and npm distribution support in this repository..." | Will the agent keep a public release and npm target expansion aligned across workflow, packages, archives, docs, and tests? | Release matrix, npm target resolution, package metadata, Windows zip staging, musl/libc handling, docs, Homebrew, and tests stay aligned. | The agent updates many surfaces but misses a central release hazard, such as Alpine musl binutils or root setup. |
| `windows_arm_smoke_cli_output` | "The `Release Smoke Windows ARM` workflow is failing..." | Will the agent fix a narrow smoke-test assertion that compares the wrong version output? | Both release-archive and npm-installed smoke paths compare against full CLI output such as `ai-wiki-toolkit <version>`, with regression tests. | The agent fixes only one path or keeps comparing against the bare package version. |
| `release_runtime_compatibility` | "A Linux npm install smoke test exposed a runtime compatibility problem..." | Will the agent catch binary runtime incompatibility before publishing, instead of stopping at build or install success? | The release process uses an older compatible Linux build baseline and runs release/npm runtime smoke checks before publishing. | The agent adds smoke gates but still builds on a too-new baseline, or only checks install success. |
| `scaffold_prompt_workflow_compliance` | "Extend the AI wiki scaffold so the toolkit better supports team coding memory..." | Will the agent keep scaffold, skill names, prompt routing, docs, and tests aligned with established repo memory? | It adds `conventions/`, `problems/`, `features/`, correct skill names, managed schema guidance, prompt/system workflow updates, doctor checks, README, and tests. | It invents incompatible names, keeps old routing, creates prompt churn, or crosses managed/user-owned boundaries. |

Full prompts live under:

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

## What This Supports

Reasonable claim:

> In this pilot suite, AI wiki-style repo memory was useful in several repeated historical coding
> tasks. It helped agents avoid a repeated ownership-boundary mistake, avoid known release hazards,
> improve runtime-release verification, and preserve scaffold/prompt workflow discipline.

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
- that the result is robust to prompt variants or paraphrases
- that the diagnostic variants are the main causal result
- that GitHub Actions releases would necessarily pass when no actual release workflow was run

## Prompt Robustness Follow-Up

The current formal runs intentionally use each family's original historical prompt. That keeps the
replay close to the real task request, but it leaves prompt robustness untested.

A stronger follow-up would rerun the same five families with controlled prompt variants, for example:

- a paraphrased but semantically equivalent prompt
- a shorter and more ambiguous prompt
- a more explicit but non-answer-leaking prompt

Those replications would test whether the observed AI wiki advantage depends on the exact wording of
the original prompt or survives reasonable task-request variation.

## Appendix A: Verbatim Original Prompts

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

- `evals/impact/report.md`

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
