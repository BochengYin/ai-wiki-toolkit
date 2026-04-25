# Manual v2 Original-Prompt 10-Repo Findings

This note records the 2026-04-25 transition run across both current impact-eval families.

It is useful evidence, but not a clean formal result. The run happened during the shift from
VS Code/Computer Use execution to Codex CLI-first execution. The artifacts are complete enough to
analyze behavior, but the old session exports do not yet record source/model/effort fields in the
manifest, and the release family mixes one UI run with four CLI fallback runs.

## Scope

Prompt level:

- `original`

Model condition intended by the operator:

- `gpt-5.5`
- `xhigh`

Workspace root for both families:

- `/private/tmp/aiwiki_first_round/<family>/workspaces/20260425-005106`

Run dirs:

- `/private/tmp/aiwiki_first_round/ownership_boundary/runs/ui-original-five-slots-20260425-0139`
- `/private/tmp/aiwiki_first_round/release_distribution_integrity/runs/ui-original-five-slots-20260425-0218`

Session exports:

- `/private/tmp/aiwiki_first_round/ownership_boundary/workspaces/20260425-005106/codex_sessions_ui_original_ownership/manifest.json`
- `/private/tmp/aiwiki_first_round/release_distribution_integrity/workspaces/20260425-005106/codex_sessions_ui_original_release/manifest.json`

## Slot Map

| slot | variant | role |
| --- | --- | --- |
| `s01` / `s01_smoke_clean` | `no_aiwiki_workflow` | primary control |
| `s02` | `aiwiki_scaffold_no_target_memory` | diagnostic: harness and non-target memory only |
| `s03` | `aiwiki_linked_raw_only` | diagnostic: target raw drafts |
| `s04` | `aiwiki_linked_consolidated_only` | diagnostic: linked consolidated docs |
| `s05` | `aiwiki_ambient_memory_workflow` | primary treatment: realistic AI wiki workflow |

Ownership used `s01_smoke_clean` for the no-AI-wiki slot because the first `s01` workspace was
contaminated by an operator prompt-entry mistake before the valid smoke run.

## Execution Notes

Ownership:

- all five analyzed sessions came from VS Code Codex UI runs
- the session export has all five slots and no missing variants
- the old export lacks observed `source`, `model`, and `reasoning_effort` fields

Release distribution:

- `s01` came from VS Code Codex UI
- `s02` through `s05` used Codex CLI fallback after Computer Use / VS Code accessibility became
  unreliable
- the run metadata still says `vscode-codex-extension`, so execution-surface metadata is stale for
  `s02` through `s05`
- the session export has all five slots and no missing variants
- the old export lacks observed `source`, `model`, and `reasoning_effort` fields

Process consequence:

- This batch can support qualitative findings.
- It should not be treated as a clean formal causal run under the newer CLI-first validator.
- The later CLI-first protocol and manifest validation were added specifically to prevent this
  ambiguity from recurring.

## Ownership Boundary Findings

Primary comparison:

- `no_aiwiki_workflow` failed the ownership boundary. It added package-facing implementation under
  `src/ai_wiki_toolkit/contributor_workflow.py` and CLI wiring in `src/ai_wiki_toolkit/cli.py`,
  while also adding a repo-local script.
- `aiwiki_ambient_memory_workflow` succeeded more cleanly. It added `scripts/pr_flow.py`, focused
  tests under `tests/`, and `ai-wiki/workflows.md`, without adding package code.

Diagnostic comparison:

- `aiwiki_scaffold_no_target_memory` avoided the package-code failure and added a repo-local helper,
  but it updated broader public docs such as `CONTRIBUTING.md` and `CHANGELOG.md`.
- `aiwiki_linked_raw_only` used the repo-local workflow memory directly and added
  `scripts/pr_flow.py`, tests, `CONTRIBUTING.md`, and `ai-wiki/workflows.md`.
- `aiwiki_linked_consolidated_only` also stayed repo-local. The transcript shows it used both the
  workflow doc and consolidated ownership guidance to avoid `src/ai_wiki_toolkit/`.
- `aiwiki_ambient_memory_workflow` produced the narrowest ownership-boundary diff: script, tests,
  and workflow doc only.

Interpretation:

- The primary working-mode comparison is favorable to AI wiki: no-AI-wiki repeated the exact
  package-surface mistake, while realistic AI wiki did not.
- The diagnostic result is less clean as a target-memory isolation test, because the scaffold-only
  slot also avoided the main package-code failure. In this task, AI wiki harness and ambient routing
  may already be enough to push the agent toward repo-local work.
- The strongest observed benefit is not merely "the agent read a specific doc"; it is that the
  AI wiki workflow changed where the agent looked and which implementation surface it considered
  legitimate.

## Release Distribution Integrity Findings

Primary comparison:

- `no_aiwiki_workflow` already made a broad, plausible coordinated release update across workflows,
  npm metadata, archive handling, docs, and tests.
- `aiwiki_ambient_memory_workflow` also made a broad coordinated update and explicitly reused the
  distribution-matrix convention plus platform-specific problem notes.

Diagnostic comparison:

- All five release slots touched the major coupled surfaces:
  - release workflows
  - npm target maps and wrapper code
  - package metadata
  - Windows zip handling
  - release/build helpers
  - docs
  - release-facing tests
- AI wiki variants more explicitly surfaced known platform lessons such as musl/binutils setup,
  Windows ARM smoke behavior, npm `libc` metadata, and official runner labels.
- `s02` and `s03` created new local draft notes during the run. That is useful product behavior, but
  for eval analysis it is also extra working-tree noise that should be separated from first-pass
  task scoring.

Interpretation:

- This family is not a strong binary success/failure discriminator under the original prompt,
  because the no-AI-wiki baseline can already complete a broad implementation.
- It is still useful for comparing completeness and verification quality.
- The likely AI wiki value here is coordination discipline: remembering platform-specific release
  failure modes and making the agent check more coupled surfaces before closing.

## Cross-Run Findings

What looks positive:

- `ownership_boundary` gives a clear primary comparison: no-AI-wiki failed the boundary, realistic
  AI wiki succeeded.
- `release_distribution_integrity` shows that AI wiki can act as a coordination checklist for
  multi-surface release work.
- The original prompt is better than `medium` for workflow-primary claims because it does not tell
  the agent the answer directly.
- Neutral slot paths reduced treatment-name leakage compared with round1 semantic paths.

What remains weak:

- This transition run mixes UI and CLI execution.
- Old session exports are complete but do not include observed source/model/effort metadata.
- Ownership `s01` required a replacement clean smoke slot because of an operator mistake.
- Release `s02` through `s05` have stale run-level execution-surface metadata after CLI fallback.
- No release slot ran the actual Docker/PyInstaller release matrix locally.
- `final_message.md` is inconsistent: missing for ownership, present for release CLI fallback slots.
  The visible transcript remains the better evidence source.

## Process Improvements From This Batch

Already implemented after this run:

- Formal runs should be Codex CLI-first.
- `init_run.py` should default to `codex-cli`, `gpt-5.5`, and `xhigh`.
- `export_codex_sessions.py` should export observed source/model/effort when present.
- `validate_run.py` should require a complete `codex_sessions/manifest.json`.
- UI / Computer Use should be smoke-only and should not block eval execution.

Still recommended:

- Score this batch with `score_run.py` if it will be used in a human-facing report, while marking it
  as a transition run.
- Re-run the same two families with the new CLI-first protocol before making stronger formal claims.
- Keep family runbooks as reproduction specs; put concrete run findings in timestamped or
  batch-named notes.
- Build future reports from `notes/index.md` order instead of asking readers to infer chronology
  from file names.

## Bottom Line

This 10-repo batch is the first useful original-prompt v2 evidence:

- For ownership-boundary behavior, AI wiki workflow looks clearly useful in the primary comparison.
- For release-distribution work, AI wiki looks more like a completeness and verification aid than a
  simple success/failure switch.

Because the run was transitional and not fully CLI-first, it should be cited as qualitative evidence
and as the reason for the stricter formal protocol, not as the final causal report.
