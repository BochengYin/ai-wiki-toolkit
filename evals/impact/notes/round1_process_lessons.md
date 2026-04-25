# Round 1 Process Lessons

This note documents what worked, what did not, and what we learned from the current manual
impact-eval round across:

- `ownership_boundary short`
- `ownership_boundary medium`
- `release_distribution_integrity short`

The goal of this note is not to restate every benchmark finding. It is to document the current
experiment process so the workflow is shareable and the next round starts from a clearer baseline.

## What Worked Well

### 1. Historical baselines made the tasks real again

The shift from "current working tree with obvious intended surfaces" to historical baselines was a
major improvement.

The strongest example is `ownership_boundary`, where the earlier benchmark leaked the answer
because the repo already contained the repo-local helper surface. The repaired baseline removed
that accidental guidance and made the surface-choice question real again.

### 2. External artifact capture prevented workspace contamination

Saving results outside the variant repos was the right call.

The current flow:

- prepares clean variant repos under `/private/tmp/aiwiki_first_round/.../workspaces/...`
- saves diffs and run metadata under `/private/tmp/aiwiki_first_round/.../runs/...`

That separation prevents one manual run from leaking back into later workspaces.

### 3. Session export made hidden experiment problems visible

Adding `export_codex_sessions.py` was one of the most useful improvements in this round.

Without visible session export, several important issues would have stayed hidden:

- full prompt surface differences beyond the task prompt
- variant-name leakage through paths and `cwd`
- AI wiki skill differences between variants
- later user follow-up overwriting what looked like a final-message artifact

This is a strong positive signal. The harness is now surfacing its own validity limits instead of
silently hiding them.

### 4. The benchmark families differentiated in informative ways

The three current comparisons did not all collapse into the same story:

- `ownership_boundary short` became the cleanest memory-sensitive benchmark
- `ownership_boundary medium` became a prompt-strength control
- `release_distribution_integrity short` became a coordination-completeness benchmark

That is useful. It means the benchmark family design is starting to produce distinct kinds of
evidence instead of one repetitive pass/fail template.

## What Did Not Go Well

### 1. Full prompt surface is still confounded

The task prompt itself is controlled well, but the full session prompt surface is not.

The visible transcripts show that sessions still include:

- variant names in path strings
- `AGENTS.md` instructions tied to the variant workspace
- `cwd`, date, and environment context
- AI wiki-only skills in AI wiki variants

This means `plain_repo_no_aiwiki` versus AI wiki variants is still not a pure memory comparison.
It is a bundled treatment that mixes:

- memory differences
- harness differences
- skill availability differences

### 2. Result capture is weaker than the analysis standard

The current report stack captures:

- diff
- status
- optional final message

But the real analysis standard we now need is:

- diff
- changed tests
- visible transcript
- visible session trace
- manual scoring against a written rubric

In other words, the harness currently captures enough to investigate, but not enough to rely on
summary artifacts alone.

### 3. `final_message.md` is not a stable first-pass artifact

This round exposed a concrete failure mode:

- if the operator continues the session after the first closeout, a later reply can become the
  saved `final_message.md`

That happened in the saved `release_distribution_integrity / aiwiki_no_relevant_memory` artifact.
The run was still analyzable because the visible transcript preserved the first substantive
closeout, but the saved final-message artifact itself was no longer a faithful first-pass summary.

### 4. Manual controls are real but under-recorded

This round depended on the operator manually holding constant:

- model family
- reasoning effort
- fresh-session discipline
- prompt consistency within a comparison set

That is acceptable for exploratory manual evals, but it is under-documented in the current
`result.json` schema. The runs are qualitatively comparable, not fully instrumented replays.

## Why These Problems Are Still Positive Signals

This round found real experiment issues, but they were the right kind of issues:

- visible
- diagnosable
- documentable
- actionable

That is much better than silent benchmark leakage.

In earlier `ownership_boundary` work, the benchmark failed because the repo baseline and prompt
already pointed at the intended answer. That was only obvious after careful review. In this round,
the new tooling and process made confounds easier to spot directly from artifacts.

So the positive signal is not "the harness is perfect."

The positive signal is:

- the harness is now exposing its own weaknesses early enough to repair them before broader sharing

## Main Lessons From The Benchmarks Themselves

### ownership_boundary short

This is currently the most informative benchmark for direct memory-sensitive implementation-surface
choice.

What it showed:

- the task-specific raw draft helped keep the helper in repo-local surfaces
- adjacent consolidated docs were not enough on their own
- raw-plus-consolidated is not automatically better, because memory has to be surfaced and used,
  not merely present in the repo

### ownership_boundary medium

This benchmark showed that one explicit boundary sentence can dominate the result.

What it showed:

- prompt specificity can wash out memory effects
- this family is useful as a control condition
- it should not be over-read as evidence that all memory states are equally good

### release_distribution_integrity short

This benchmark was useful, but it measured a different thing.

What it showed:

- the baseline repo and prompt were already strong enough for several variants to succeed
- AI wiki memory looked more helpful for coordinated completeness than for basic task direction
- this family is better for studying cross-surface synchronization than for studying bare success

## Shareable Round 1 Workflow

This is the historical round1 manual process. It has been superseded for formal v2 runs by the
Codex CLI-first workflow in `evals/impact/README.md`, but remains useful for interpreting old
artifacts.

1. Choose a real repeated repo problem and a historical baseline before the fix landed.
2. Define the five standard workspace variants with `prepare_variants.py`.
3. Create an external run dir with `init_run.py`.
4. Run each variant in a fresh Codex subscription session.
5. Capture the workspace diff immediately with `save_result.py`.
6. Export visible Codex sessions with `export_codex_sessions.py`.
7. Grade from:
   - task prompt
   - full visible prompt surface
   - diff
   - changed tests
   - visible transcript
8. Write a benchmark-specific findings note.
9. Update the top-level eval docs so the next session can continue from written state.

## Immediate Fixes Before Wider Sharing

If these evals are going to be shared externally, the next round should tighten five things first:

1. Stop leaking semantic variant names through workspace paths and visible `cwd`.
2. Separate memory effects from AI wiki harness/skill effects more cleanly.
3. Freeze a first-pass cutoff artifact before any later follow-up such as `code`.
4. Record model/effort/session metadata in result capture, not just in ad hoc notes.
5. Treat `report.md` as a summary only and require diff-plus-session review for claims about task
   success or memory effect.

Manual v2 addresses these by using neutral slot workspaces, workflow-primary primary/diagnostic
variants, `original` prompts, Codex CLI-first execution, exported session manifests, and
`validate_run.py` confound checks.

## Bottom Line

This round is good enough to document and discuss publicly as:

- a manual qualitative benchmark workflow
- an example of how to backsolve prompts from real repo history
- an example of how session traces can improve eval validity review

It is not yet good enough to present as:

- a clean causal estimate of AI wiki memory impact
- a fully instrumented benchmark harness
- a seed-controlled model-comparison framework
