# Release Distribution Integrity Round 1 Findings

This note summarizes the first recorded `release_distribution_integrity` runs and the current
defensible conclusions from them.

These findings are the repo-recorded result summary for this benchmark family.

## Runs

### Short

- report: `/private/tmp/aiwiki_first_round/release_distribution_integrity/runs/short-five-way/report.md`
- session manifest:
  - `/private/tmp/aiwiki_first_round/release_distribution_integrity/workspaces/20260424-182219/codex_sessions/manifest.json`

## Execution Conditions

The saved runs were executed manually under these intended conditions:

- execution surface: Codex subscription sessions, not direct API requests
- model: `gpt-5.4`
- reasoning effort: `xhigh` / extra high

Because these runs were executed through subscription sessions, not the API, temperature and seed
were not operator-exposed controls in this experiment.

The task prompt itself was clean:

- exported `prompt.md` files matched the guide prompt exactly
- all five variants within the run used the same exported prompt text

What was not controlled cleanly:

- full prompt surface beyond `prompt.md`
- variant names leaking through workspace paths
- `AGENTS.md` and skill differences between plain and AI wiki variants
- a frozen first-pass final-message capture

So these are usable qualitative case studies, not clean causal estimates of pure memory effect.

## Manual Scorecard For The 5 Recorded Variants

The following labels are a manual grading pass over the five recorded `short` runs using the rubric
in `evals/impact/release_distribution_integrity_runbook.md`.

| variant | manual grade | rationale |
| --- | --- | --- |
| `plain_repo_no_aiwiki` | `success` | coordinated the release workflow, npm metadata/runtime, docs, Homebrew alignment, and release-facing tests without AI wiki memory |
| `aiwiki_no_relevant_memory` | `partial` | broadly fixed the workflow and npm path, but left Homebrew alignment out and its saved `final_message.md` was not the first-pass closeout |
| `aiwiki_raw_drafts` | `partial` | coordinated the main release/npm/doc path well, but its release-facing verification remained thinner than the strongest runs |
| `aiwiki_consolidated` | `success` | updated the public workflow matrix, npm metadata/runtime, docs, Homebrew alignment, and runtime checks in one coordinated pass |
| `aiwiki_raw_plus_consolidated` | `success` | produced the most complete coordinated change, including runtime/artifact checks, Homebrew alignment, and a clear convention-driven implementation plan |

## Common Findings

All five variants broadly understood the task.

No recorded variant made the trivial failure of updating only one surface.

Across the five runs, the common coordinated surfaces were:

- `.github/workflows/release-binaries.yml`
- `.github/workflows/publish-npm.yml`
- `npm/platform-targets.json`
- `npm/shared.js`
- `package.json`
- `src/ai_wiki_toolkit/npm_distribution.py`
- `src/ai_wiki_toolkit/release_build.py`
- release/install docs

Most variants also chose to add `windows-x64` even though the prompt explicitly listed only
`windows-arm64`. The defensible interpretation is:

- the agents treated "end-to-end Windows support" as implying both mainstream Windows npm support
  and the new ARM64 target

That behavior is especially explicit in the `aiwiki_no_relevant_memory` session, where the agent
raised the ambiguity and then adopted a non-blocking assumption before coding.

## Strongest Results

The strongest coordinated outcomes were:

- `aiwiki_raw_plus_consolidated`
- `aiwiki_consolidated`
- `plain_repo_no_aiwiki`

Observed properties:

- broad multi-surface synchronization
- docs updated to match the widened public matrix
- Windows archive handling covered
- Linux libc-aware npm resolution covered
- Homebrew alignment included

This means the benchmark did not separate basic success from failure as sharply as
`ownership_boundary short` did.

The more informative distinction here was:

- completeness of coordination
- explicitness of the cross-surface reasoning
- quality of release-facing verification

## Partial Results

### aiwiki_no_relevant_memory

This run still produced a strong implementation, but it was weaker than the best coordinated runs
in two ways:

- it did not update the Homebrew alignment layer
- the saved `final_message.md` was overwritten by a later user `code` follow-up, so the transcript
  had to be used instead of the saved final-message artifact

Important nuance:

- this was not a failed run
- it was a successful implementation with a weaker artifact/coupling profile

### aiwiki_raw_drafts

This run covered the main workflow/npm/docs path well and did include Homebrew alignment, but its
verification surface was thinner than the strongest runs.

Compared with the strongest coordinated runs, it did not add the same breadth of release-facing
checks such as the stronger runtime/artifact coverage.

## What We Can Defend

1. We can defend that the task prompt itself was not the main validity problem.
   - the exported prompts matched the guide prompts exactly

2. We can defend that the run is still useful as a qualitative benchmark.
   - all five variants produced substantive coordinated diffs
   - the session traces explain why they chose those surfaces

3. We can defend that this family measures coordinated multi-surface completeness better than it
   measures basic "can the agent do the task at all?"
   - even the plain no-AI-wiki baseline was strong

4. We can defend that the promoted convention helped the agent articulate and execute a broader
   coordination plan.
   - this is clearest in the `aiwiki_consolidated` and `aiwiki_raw_plus_consolidated` runs

## What We Cannot Defend Yet

- We cannot claim that AI wiki memory was necessary for success on this task.
- We cannot claim a clean pure-memory comparison between plain and AI wiki variants.
- We cannot claim stable model-level effects from one run per condition.
- We cannot claim that changed-file counts or `final_message.md` alone are reliable evaluation
  signals.
- We cannot claim that `aiwiki_no_relevant_memory` is actually free of adjacent release memory.

## Main Validity Risks Exposed By This Family

### 1. Full prompt surface is not controlled

The task prompt was controlled, but the full session prompt surface was not.

Visible session traces still included:

- variant names in the workspace path
- `AGENTS.md` differences between plain and AI wiki repos
- AI wiki-specific skills such as `ai-wiki-clarify-before-code`

### 2. Artifact capture is weaker than the analysis standard now requires

The current harness captures:

- diff
- status
- optional final message

But this family showed that serious evaluation now also needs:

- visible session export
- transcript-based first-pass cutoff
- human review of changed tests, not just diffstat

### 3. `final_message.md` is not a reliable first-pass artifact yet

In the saved `aiwiki_no_relevant_memory` run, the captured `final_message.md` was a later reply to
`code`, not the original completion summary.

The first substantive closeout still exists in the visible transcript, so the run remains
interpretable. But this artifact path should not be trusted on its own.

## Recommended Reading With This Note

- `evals/impact/release_distribution_integrity_runbook.md`
- `evals/impact/notes/round1_process_lessons.md`
- `evals/impact/notes/ownership_boundary_round1_findings.md`
