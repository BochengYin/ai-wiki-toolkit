# Impact Eval

This directory holds manual-only impact eval assets for comparing how `ai-wiki-toolkit`
changes agent behavior on repeated repo problems.

Primary repo-local documentation for the current benchmark lives in:

- `evals/impact/TODO.md`
- `evals/impact/ownership_boundary_runbook.md`
- `evals/impact/notes/ownership_boundary_v0_failure.md`
- `evals/impact/notes/ownership_boundary_round1_findings.md`

The first benchmark family is `ownership_boundary`. It measures whether different AI wiki
memory states change how reliably an agent:

- keeps a contributor helper out of distributed package surfaces
- adds a helper under repo surfaces such as `scripts/` instead of inventing a package feature
- updates the relevant local workflow guidance
- avoids turning contributor-only behavior into `src/ai_wiki_toolkit/` product code

The original version of this benchmark leaked too much of the intended answer. That failure is
documented in:

```text
evals/impact/notes/ownership_boundary_v0_failure.md
```

## Workspace Variants

Run the experiment across five variants:

- `plain_repo_no_aiwiki`
- `aiwiki_no_relevant_memory`
- `aiwiki_raw_drafts`
- `aiwiki_consolidated`
- `aiwiki_raw_plus_consolidated`

These five variants let you separate:

- harness effect
- raw draft effect
- consolidate effect
- consolidated guidance under raw-draft noise

## Prepare Workspaces

From the repo root:

```bash
uv run python evals/impact/scripts/prepare_variants.py --experiment ownership_boundary
```

By default this creates clean git repos outside the main repository under:

```text
~/aiwiki-impact-workdirs/ai-wiki-toolkit/ownership_boundary/<timestamp>/
```

Important: `prepare_variants.py` now copies a committed git snapshot by default, not the current
working tree. That means local uncommitted eval scaffolding, scratch notes, or unrelated code
changes do not leak into the experiment repos.

For `ownership_boundary`, the default baseline is the historical ref:

```text
34cd5a3^
```

This rewinds the generated repos to a state before the repo-local PR helper and its tests were
added, then overlays only the experiment's selected AI wiki memory.

If you explicitly want to build variants from the current dirty working tree, opt in:

```bash
uv run python evals/impact/scripts/prepare_variants.py \
  --experiment ownership_boundary \
  --source-mode working-tree
```

Each generated workspace includes an `EVAL_VARIANT.md` file with:

- the variant name
- the prompt family path
- the rule for running the variant in a fresh Codex session

## Prompt Packs

Use the prompt family under:

```text
evals/impact/prompts/ownership_boundary/
```

Start with:

```text
evals/impact/prompts/ownership_boundary/TASK.md
```

That file explains the concrete repo-realistic task being tested. The active prompt-specificity
variants are:

- `short.md`
- `medium.md`

Recommended sequence:

1. Fix the prompt level to `medium` and run all five memory variants.
2. Then compare prompt sensitivity on the most informative three variants:
   - `plain_repo_no_aiwiki`
   - `aiwiki_raw_drafts`
   - `aiwiki_consolidated`
3. Run `short` and `medium` on those three variants.

This keeps the first pass manageable while still measuring whether consolidated memory lets you
write shorter prompts without relying on an over-specified `full` prompt.

## Manual Run Protocol

For each variant:

1. Open that workspace in a fresh Codex session.
2. Paste one prompt from the prompt family.
3. Let the agent work normally.
4. Save:
   - final response
   - final diff or changed-file snapshot
   - whether the task succeeded on the first attempt
   - how many retries or human nudges were needed

Important constraints:

- Do not reuse the same Codex session across variants.
- Do not run one variant inside another variant's repository tree.
- Keep the model and approval mode the same across all variants in the same comparison set.

## Save Results Outside The Workspaces

Do not save experiment outputs inside the variant repos. That would leak prior runs back into
future experiments.

Initialize an external run directory:

```bash
uv run python evals/impact/scripts/init_run.py \
  --experiment ownership_boundary \
  --workspace-root /tmp/aiwiki-impact-ownership-boundary
```

This creates a result tree under:

```text
~/aiwiki-impact-runs/ai-wiki-toolkit/ownership_boundary/<run-label>/
```

Each slot contains a small README showing how to capture the workspace result. Saving a
`final_message.md` is optional.

After a manual run finishes, capture the result:

```bash
uv run python evals/impact/scripts/save_result.py \
  --run-dir ~/aiwiki-impact-runs/ai-wiki-toolkit/ownership_boundary/run_20260422-120000 \
  --variant aiwiki_consolidated \
  --prompt-level medium \
  --workspace /tmp/aiwiki-impact-ownership-boundary/aiwiki_consolidated
```

If you also want to preserve the final response text, save it as `final_message.md` in the slot
first, then pass `--final-message <that-path>`. If the file is missing, `save_result.py` now
skips it and still captures the diff artifacts.

If you want to judge correctness immediately, add one of:

- `--first-pass-success`
- `--first-pass-failure`

If you omit both, the result stays pending so you can analyze correctness later.

`save_result.py` writes:

- `workspace_diff.patch`
- `workspace_diff_stat.txt`
- `workspace_status.txt`
- `workspace_head.txt`
- `result.json`

all outside the experiment repo, so reruns do not contaminate future sessions.

## Current Scope

The current setup script prepares only the `ownership_boundary` benchmark family because it
already has both:

- raw draft evidence under `ai-wiki/people/bochengyin/drafts/`
- consolidated shared memory under `ai-wiki/conventions/` and `ai-wiki/review-patterns/`

Add new benchmark families only after deciding which raw draft cluster and which consolidated
target should be compared.
