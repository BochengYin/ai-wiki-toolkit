# Impact Eval

This directory holds manual-only impact eval assets for comparing how `ai-wiki-toolkit`
changes agent behavior on repeated repo problems.

Primary repo-local documentation for the current benchmark lives in:

- `evals/impact/TODO.md`
- `evals/impact/ownership_boundary_runbook.md`
- `evals/impact/release_distribution_integrity_runbook.md`
- `evals/impact/notes/ownership_boundary_v0_failure.md`
- `evals/impact/notes/ownership_boundary_round1_findings.md`
- `evals/impact/notes/release_distribution_integrity_round1_findings.md`
- `evals/impact/notes/round1_process_lessons.md`

The current documented benchmark families are:

- `ownership_boundary`
- `release_distribution_integrity`

`ownership_boundary` measures whether different AI wiki memory states change how reliably an
agent:

- keeps a contributor helper out of distributed package surfaces
- adds a helper under repo surfaces such as `scripts/` instead of inventing a package feature
- updates the relevant local workflow guidance
- avoids turning contributor-only behavior into `src/ai_wiki_toolkit/` product code

`release_distribution_integrity` measures whether different memory states change how completely an
agent keeps a public release/distribution matrix aligned across:

- release workflows
- npm target resolution and package metadata
- archive handling
- docs
- release-facing checks

The original version of this benchmark leaked too much of the intended answer. That failure is
documented in:

```text
evals/impact/notes/ownership_boundary_v0_failure.md
```

The current round-level process strengths, weaknesses, and shareable workflow are documented in:

```text
evals/impact/notes/round1_process_lessons.md
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
/private/tmp/aiwiki_first_round/<experiment>/workspaces/<timestamp>/
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
  --workspace-root /private/tmp/aiwiki_first_round/ownership_boundary/workspaces/20260423-170541
```

This creates a result tree under:

```text
/private/tmp/aiwiki_first_round/<experiment>/runs/<run-label>/
```

Each slot contains a small README showing how to capture the workspace result. Saving a
`final_message.md` is optional.

After a manual run finishes, capture the result:

```bash
uv run python evals/impact/scripts/save_result.py \
  --run-dir /private/tmp/aiwiki_first_round/ownership_boundary/runs/run_20260422-120000 \
  --variant aiwiki_consolidated \
  --prompt-level medium \
  --workspace /private/tmp/aiwiki_first_round/ownership_boundary/workspaces/20260423-170541/aiwiki_consolidated
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

The current setup script prepares the benchmark families registered in
`evals/impact/scripts/prepare_variants.py`. Today that includes:

- `ownership_boundary`
- `release_distribution_integrity`

Add new benchmark families only after deciding which raw draft cluster and which consolidated
target should be compared.

## Current Filesystem Layout

Use one round root per experiment batch:

```text
/private/tmp/aiwiki_first_round/
  <experiment>/
    workspaces/
      <timestamp>/
        plain_repo_no_aiwiki/
        aiwiki_no_relevant_memory/
        aiwiki_raw_drafts/
        aiwiki_consolidated/
        aiwiki_raw_plus_consolidated/
        codex_sessions/
    runs/
      <run-label>/
        <variant>/
          <prompt-level>/
```

Rules:

- `workspaces/<timestamp>/` is a prepared five-repo set for one experiment family.
- `workspaces/<timestamp>/codex_sessions/` is optional workspace-level metadata for exported visible Codex traces.
- Reuse the same workspace set across `short` and `medium` runs.
- `runs/<run-label>/` stores captured results only; it must stay outside the variant repos.
- Treat prompt level as a run dimension, not a workspace dimension.
- Put obsolete or invalid workspace sets under `/private/tmp/aiwiki_first_round/archive/`.

## Standard Generation Flow

Prepare one workspace set:

```bash
uv run python evals/impact/scripts/prepare_variants.py \
  --experiment release_distribution_integrity
```

This prints the new workspace root, for example:

```text
/private/tmp/aiwiki_first_round/release_distribution_integrity/workspaces/20260424-182219
```

Create a run directory for one comparison pass:

```bash
uv run python evals/impact/scripts/init_run.py \
  --experiment release_distribution_integrity \
  --workspace-root /private/tmp/aiwiki_first_round/release_distribution_integrity/workspaces/20260424-182219 \
  --prompt-levels medium \
  --run-label medium-five-way
```

Then open each variant repo in a fresh session, run the chosen prompt, and capture the result into
the matching run slot with `save_result.py`.

If you also want to preserve the visible Codex chat-window trace for the workspace set, export it
after the variant runs finish:

```bash
uv run python evals/impact/scripts/export_codex_sessions.py \
  --workspace-root /private/tmp/aiwiki_first_round/release_distribution_integrity/workspaces/20260424-182219
```

If the historical Codex sessions were recorded under an older workspace root but you want to store
the export under a newer copied workspace tree, add:

```bash
  --match-workspace-root /private/tmp/old-experiment-root/<experiment>/workspaces/<timestamp>
```

This creates:

```text
/private/tmp/aiwiki_first_round/release_distribution_integrity/workspaces/20260424-182219/codex_sessions/
```

The export is workspace-level metadata, not variant-repo content. Each exported session keeps:

- `metadata.json`
- `prompt.md`
- `session_without_reasoning.jsonl`
- `visible_session.jsonl`
- `visible_transcript.md`

Important boundary:

- `session_without_reasoning.jsonl` keeps the raw session stream except hidden reasoning records
- `visible_session.jsonl` and `visible_transcript.md` are the human-usable filtered views
- hidden internal reasoning records are intentionally omitted
