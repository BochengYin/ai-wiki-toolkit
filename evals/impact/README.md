# Impact Eval

This directory holds manual-only impact eval assets for comparing how `ai-wiki-toolkit`
changes agent behavior on repeated repo problems.

Primary repo-local documentation for the current benchmark lives in:

- `evals/impact/public_writeup_draft.md`
- `evals/impact/notes/index.md`
- `evals/impact/report.md`
- `evals/impact/TODO.md`
- `evals/impact/ownership_boundary_runbook.md`
- `evals/impact/release_distribution_integrity_runbook.md`
- `evals/impact/notes/manual_v2_original_10_repo_findings.md`
- `evals/impact/notes/ownership_boundary_v0_failure.md`
- `evals/impact/notes/ownership_boundary_round1_findings.md`
- `evals/impact/notes/release_distribution_integrity_round1_findings.md`
- `evals/impact/notes/round1_process_lessons.md`

The current documented benchmark families are:

- `ownership_boundary`
- `release_distribution_integrity`
- `windows_arm_smoke_cli_output`
- `release_runtime_compatibility`
- `scaffold_prompt_workflow_compliance`

## Manual v2: Workflow-Primary Framing

The primary v2 question is:

> Does the AI wiki workflow help agents make fewer repeated mistakes when a repo problem that was
> previously discovered and recorded appears again?

This is a workflow comparison first, not a single-document causality claim.

Primary comparison:

- `no_aiwiki_workflow`
  No AI wiki scaffold, prompt routing, skills, or accumulated memory.
- `aiwiki_ambient_memory_workflow`
  The realistic AI wiki working mode: current repo AI wiki memory is present, including relevant
  memories, adjacent memories, and normal ambient noise.

Diagnostic variants:

- `aiwiki_scaffold_no_target_memory`
  Keeps the AI wiki harness and ambient non-target memory, but removes the benchmark-targeted memory.
- `aiwiki_linked_raw_only`
  Adds back the source raw drafts for the same problem family.
- `aiwiki_linked_consolidated_only`
  Adds back the linked consolidated docs for the same problem family.

Use the primary comparison to answer whether the working mode helps. Use the diagnostic variants to
explain why it helped, did not help, or introduced noise.

Manual v2 workspaces use neutral slot paths such as:

```text
.../workspaces/<timestamp>/
  assignment.json
  slots/
    s01/
    s02/
    s03/
    s04/
    s05/
    s06/
```

The semantic variant mapping lives only in external `assignment.json` and run metadata. Do not put
variant names inside workspace paths or files.

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

Read `evals/impact/notes/index.md` first when you need chronology. It separates:

- stable family runbooks
- concrete run findings
- the current report synthesis

The latest 10-repo original-prompt transition run is documented in:

```text
evals/impact/notes/manual_v2_original_10_repo_findings.md
```

The historical round1 process strengths, weaknesses, and shareable workflow are documented in:

```text
evals/impact/notes/round1_process_lessons.md
```

## Workspace Variants

Manual v2 prepares six standard workspaces by default, but their role is different from round1. The
primary workflow comparison is:

- `no_aiwiki_workflow`
- `aiwiki_ambient_memory_workflow`

The diagnostic variants are:

- `aiwiki_scaffold_no_target_memory`
- `aiwiki_linked_raw_only`
- `aiwiki_linked_consolidated_only`
- `aiwiki_scaffold_no_adjacent_memory`

The sixth slot is for mechanism analysis only. It keeps the AI wiki scaffold/workflow path but
removes the targeted memory plus adjacent task-specific memory. For `release_distribution_integrity`,
that includes nearby release/problem notes such as musl binutils, Windows ARM smoke, npm package
bootstrap, and release-trail notes. For `ownership_boundary`, that includes workflow docs and
impact-eval notes that name the repo-local contributor workflow path.

The round1 semantic variant names are still supported with `--workspace-layout legacy` for old
analysis:

- `plain_repo_no_aiwiki`
- `aiwiki_no_relevant_memory`
- `aiwiki_raw_drafts`
- `aiwiki_consolidated`
- `aiwiki_raw_plus_consolidated`

## Prepare Workspaces

From the repo root:

```bash
uv run python evals/impact/scripts/prepare_variants.py --experiment ownership_boundary
```

By default this now creates workflow-primary v2 neutral slots outside the main repository under:

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
added, then overlays either the realistic current AI wiki memory or the selected diagnostic memory
state.

If you explicitly want to build variants from the current dirty working tree, opt in:

```bash
uv run python evals/impact/scripts/prepare_variants.py \
  --experiment ownership_boundary \
  --source-mode working-tree
```

Legacy semantic-directory workspaces include an `EVAL_VARIANT.md` file with:

- the variant name
- the prompt family path
- the rule for running the variant in a fresh Codex session

That `EVAL_VARIANT.md` note is only used by the legacy semantic-directory layout. It is intentionally
omitted from v2 neutral slots to avoid leaking the treatment name into the visible prompt surface.

## Prompt Packs

Use the prompt family under:

```text
evals/impact/prompts/ownership_boundary/
```

Start with:

```text
evals/impact/prompts/ownership_boundary/TASK.md
```

That file explains the concrete repo-realistic task being tested. Manual v2 uses one active prompt:

- `original.md`

Recommended sequence:

1. Run `original.md` across all six neutral slots.
2. Read the primary workflow comparison first:
   - `no_aiwiki_workflow`
   - `aiwiki_ambient_memory_workflow`
3. Use the diagnostic slots to explain the result:
   - `aiwiki_scaffold_no_target_memory`
   - `aiwiki_linked_raw_only`
   - `aiwiki_linked_consolidated_only`
   - `aiwiki_scaffold_no_adjacent_memory`
4. Do not run `medium` for workflow-primary claims; it names the boundary too directly and turns
   the eval into prompt-following rather than memory reuse.

Legacy round1 prompt files such as `short.md`, `medium.md`, and `full.md` remain for interpreting
old runs only.

## Codex CLI-First Run Protocol

Formal v2 runs are Codex CLI-first. Computer Use or the VS Code Codex extension may still be used
for operator smoke checks, but UI automation is not the blocking execution path for shareable evals.

For each neutral slot:

1. Run the slot with `codex exec` from a fresh persisted CLI session.
2. Use the same prompt file, model, reasoning effort, and execution profile across slots.
3. Write the agent's last message with `--output-last-message`.
4. Immediately capture:
   - first-pass diff or changed-file snapshot immediately after the first substantive closeout
   - final response convenience text when available
   - later final-state diff only if a human nudge or repair happens
   - whether the first pass succeeded
   - how many retries or human nudges were needed
5. Export visible Codex sessions for the whole workspace set.
6. Validate the run before making workflow or causal claims.

The standard execution condition is:

- execution surface: `codex-cli`
- model family: `gpt-5.5`
- reasoning effort: `xhigh`

Preferred formal run command:

```bash
uv run python evals/impact/scripts/run_cli_slots.py \
  --run-dir /private/tmp/aiwiki_first_round/ownership_boundary/runs/run_20260425 \
  --prompt-level original
```

`run_cli_slots.py` starts one run-level macOS sleep guard with `caffeinate -dimsu`, runs each
neutral slot in sequence from a fresh `codex exec` session, captures first-pass artifacts
immediately after each slot with `save_result.py`, and stops the sleep guard at the end. This avoids
per-slot UI or operator-presence dependencies while keeping session persistence in the Codex CLI.

Example manual slot command:

```bash
mkdir -p /private/tmp/aiwiki_first_round/ownership_boundary/runs/run_20260425/s01/original/first_pass
codex exec \
  --model "gpt-5.5" \
  --config 'model_reasoning_effort="xhigh"' \
  --full-auto \
  --cd /private/tmp/aiwiki_first_round/ownership_boundary/workspaces/20260425-100000/slots/s01 \
  --output-last-message /private/tmp/aiwiki_first_round/ownership_boundary/runs/run_20260425/s01/original/first_pass/final_message.md \
  - < evals/impact/prompts/ownership_boundary/original.md
```

Important constraints:

- Do not reuse the same Codex session across slots.
- Do not run one slot inside another slot's repository tree.
- Keep the model, reasoning effort, and execution profile the same across all variants in the same
  comparison set.
- The exported `codex_sessions/manifest.json` must show one matching session per slot.
- For CLI-first runs, exported session metadata must show `source=exec`, the expected model, and the
  expected reasoning effort.

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

Each slot contains a small README showing how to run the CLI prompt and capture the workspace
result. For CLI-first runs, `codex exec --output-last-message` writes `final_message.md`
automatically before `save_result.py` copies it into the first-pass artifact directory.

After a manual run finishes, capture the result:

```bash
uv run python evals/impact/scripts/save_result.py \
  --run-dir /private/tmp/aiwiki_first_round/ownership_boundary/runs/run_20260422-120000 \
  --slot s02 \
  --variant aiwiki_ambient_memory_workflow \
  --prompt-level original \
  --workspace /private/tmp/aiwiki_first_round/ownership_boundary/workspaces/20260423-170541/slots/s02 \
  --phase first_pass
```

For UI-only legacy runs, you may still save response text manually as `final_message.md` and pass
`--final-message <that-path>`. If the file is missing, `save_result.py` skips it and still captures
the diff artifacts.

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

After exporting visible Codex sessions, validate the run before making shareable claims:

```bash
uv run python evals/impact/scripts/validate_run.py \
  --run-dir /private/tmp/aiwiki_first_round/ownership_boundary/runs/run_20260422-120000 \
  --session-export-root /private/tmp/aiwiki_first_round/ownership_boundary/workspaces/20260423-170541/codex_sessions
```

This writes `confounds.json`. If it contains critical confounds, `report.md` may still summarize
the run, but it must not be treated as a clean causal claim.

Write manual rubric labels separately from capture artifacts:

```bash
uv run python evals/impact/scripts/score_run.py \
  --run-dir /private/tmp/aiwiki_first_round/ownership_boundary/runs/run_20260422-120000 \
  --slot s02 \
  --prompt-level original \
  --label success \
  --evidence s02/original/first_pass/workspace_diff.patch,s02/original/first_pass/result.json
```

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
        assignment.json
        slots/
          s01/
          s02/
          s03/
          s04/
          s05/
          s06/
        codex_sessions/
    runs/
      <run-label>/
        <slot>/
          <prompt-level>/
            first_pass/
            final/
            score.json
```

Rules:

- `workspaces/<timestamp>/` is a prepared standard six-slot set for one experiment family.
- `assignment.json` is the only place semantic variant names should appear in the workspace set.
- `workspaces/<timestamp>/codex_sessions/` is required workspace-level metadata for shareable
  claims; it must contain a complete `manifest.json`.
- Reuse the same workspace set if you repeat `original` for another model or manual comparison set.
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
  --prompt-levels original \
  --run-label original-six-way
```

Then run each slot with the CLI command in the slot README and capture the result into the matching
run slot with `save_result.py`.

After the variant runs finish, export the visible Codex session traces for the workspace set:

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

The export is workspace-level metadata, not variant-repo content. A complete export is required
before `validate_run.py` can mark a run shareable for causal claims. Each exported session keeps:

- `metadata.json`
- `prompt.md`
- `session_without_reasoning.jsonl`
- `visible_session.jsonl`
- `visible_transcript.md`

Important boundary:

- `session_without_reasoning.jsonl` keeps the raw session stream except hidden reasoning records
- `visible_session.jsonl` and `visible_transcript.md` are the human-usable filtered views
- hidden internal reasoning records are intentionally omitted
- `manifest.json` records the exported sessions, missing slots, execution source, model, and
  reasoning effort fields needed for validation
