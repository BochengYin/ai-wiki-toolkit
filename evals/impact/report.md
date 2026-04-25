# Impact Eval Report

This report summarizes the current evidence across `evals/impact/` notes. Detailed run evidence
lives in `evals/impact/notes/`.

## Current Status

The benchmark now has five completed six-slot CLI-first families:

- `ownership_boundary`: tests whether AI wiki workflow helps keep contributor-only behavior out of
  package code.
- `release_distribution_integrity`: tests whether AI wiki workflow helps coordinate public release
  and npm distribution changes across coupled surfaces.
- `windows_arm_smoke_cli_output`: tests whether agents fix a narrow Windows ARM version-output
  smoke failure.
- `release_runtime_compatibility`: tests whether agents add older-baseline Linux runtime gates before
  release and npm publishing.
- `scaffold_prompt_workflow_compliance`: tests whether agents keep scaffold, prompt guidance, docs,
  and tests aligned with repo memory and ownership boundaries.

Latest report-worthy notes:

- `evals/impact/notes/manual_v2_cli_original_ownership_20260425_findings.md`
- `evals/impact/notes/manual_v2_cli_original_release_distribution_20260425_findings.md`
- `evals/impact/notes/manual_v2_cli_original_windows_arm_20260425_findings.md`
- `evals/impact/notes/manual_v2_cli_original_release_runtime_20260425_findings.md`
- `evals/impact/notes/manual_v2_cli_original_scaffold_prompt_workflow_20260425_findings.md`

All five current formal families used independent persisted Codex CLI sessions, `gpt-5.5`, `xhigh`,
the `original.md` prompt, complete session exports, and `validate_run.py` outputs with no critical
confounds.

The earlier 2026-04-25 10-repo transition run remains useful qualitative evidence, but it is no
longer the current formal result because it mixed VS Code UI and Codex CLI fallback.

## Main Findings So Far

### Ownership Boundary

The clearest positive formal signal for AI wiki is still the ownership-boundary primary comparison.

- No AI wiki (`s01`): fail. The agent repeated the package-surface mistake by adding
  `src/ai_wiki_toolkit/contributor_workflow.py` and package CLI wiring.
- Realistic AI wiki workflow (`s05`): success. The agent kept the helper repo-local under
  `scripts/`, added tests, and updated local workflow docs without adding package code.

This supports the claim that AI wiki workflow can help prevent repeated implementation-surface
mistakes.

### Release Distribution Integrity

The release-distribution primary comparison gives a narrower positive signal.

- No AI wiki (`s01`): partial. The agent produced a broad release/npm matrix expansion, but missed
  the known `linux-musl-x64` build hazard: Alpine PyInstaller builds need binutils/objdump setup run
  as root.
- Realistic AI wiki workflow (`s05`): success. The agent produced the same broad expansion and also
  applied the musl setup lesson, npm `libc` metadata, Windows zip staging, docs, Homebrew alignment,
  and tests.

This supports the claim that AI wiki can improve coordination quality for multi-surface release
work. It does not show that AI wiki is necessary for the agent to attempt the expansion.

### Windows ARM Smoke Output

The Windows ARM smoke family is neutral for AI wiki usefulness.

- No AI wiki (`s01`): success.
- Realistic AI wiki workflow (`s05`): success.
- All diagnostic variants: success.

Every slot fixed both release-archive and npm-installed smoke checks to compare against
`ai-wiki-toolkit <version>` instead of the bare package version and updated tests. This family is
useful as a deterministic CLI-first harness benchmark, but not as evidence that AI wiki memory is
needed.

### Release Runtime Compatibility

The release-runtime family gives a narrow positive primary comparison.

- No AI wiki (`s01`): partial. It added release and npm runtime smoke checks in `node:24-bookworm`,
  but left `linux-x64` building on `ubuntu-24.04`, so the release process catches the failure without
  producing an older-glibc-compatible baseline.
- Realistic AI wiki workflow (`s05`): success. It moved Linux builds to `ubuntu-22.04`, added
  release runtime smoke, added staged npm runtime smoke, and updated docs/tests.

Diagnostics also succeeded, including the strict no-adjacent slot. The best claim is therefore that
AI wiki improved the primary treatment's fix quality, not that target memory was necessary.

### Scaffold Prompt Workflow Compliance

The scaffold/prompt family gives a workflow-discipline positive primary comparison.

- No AI wiki (`s01`): partial. It implemented many surfaces, but drifted on names and routing:
  `problem-solutions/`, `ai-wiki-clarify-coding-task`, `ai-wiki-pr-review-learning`, and older
  `_toolkit/index.md` prompt routing.
- Realistic AI wiki workflow (`s05`): success. It stayed aligned with `conventions/`, `problems/`,
  `features/`, `ai-wiki-clarify-before-code`, `ai-wiki-capture-review-learning`, managed schema
  guidance, prompt/system workflow updates, doctor checks, README, and tests.

Diagnostics also succeeded, so the family is best interpreted as evidence that AI wiki can improve
workflow consistency and naming/routing discipline, not that target memory is necessary.

## Current Claim Boundaries

Reasonable to claim:

- The clean CLI-first ownership-boundary run supports AI wiki workflow usefulness for a
  repeated-problem ownership-boundary task.
- The release-distribution and release-runtime runs support narrower usefulness claims for
  completeness, known-hazard avoidance, and release-process quality.
- The scaffold/prompt run supports a workflow-discipline claim: AI wiki context helped the agent keep
  names, routing, docs, and tests aligned.
- The Windows ARM smoke run is a good deterministic harness check, but neutral on AI wiki usefulness.
- Original prompts and complete session exports are now the right baseline for interpreting these
  workflow-primary runs.

Not yet reasonable to claim:

- a clean quantitative causal estimate of AI wiki impact
- a seed-controlled benchmark result
- a final model comparison
- proof that AI wiki is necessary for release-distribution, release-runtime, scaffold, or Windows ARM
  success; several diagnostic variants solved those tasks
- a formal claim from the 2026-04-25 transition batch

## Next Formal Work

Remaining untested or immature families:

1. `postinstall_archive_staging`
2. `aiwiki_evidence_integrity`
3. `capture_vs_consolidation`, after more concrete signals exist

The next replication work should keep the now-default protocol:

1. Run six neutral slots per family.
2. Keep `original.md`, Codex CLI-first execution, and run-level `caffeinate`.
3. Preserve complete session exports and validator output before scoring.
4. Treat `no_aiwiki_workflow` versus `aiwiki_ambient_memory_workflow` as the primary comparison.
5. Treat diagnostic variants as explanations, not primary conclusions.
