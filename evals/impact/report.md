# Impact Eval Report

This report summarizes the current evidence across `evals/impact/` notes. It is intentionally short:
the detailed run evidence lives in `evals/impact/notes/`.

## Current Status

The benchmark now has two useful families:

- `ownership_boundary`: tests whether AI wiki workflow helps keep contributor-only behavior out of
  package code.
- `release_distribution_integrity`: tests whether AI wiki workflow helps coordinate public release
  and npm distribution changes across coupled surfaces.

The latest report-worthy ownership-boundary evidence is the 2026-04-25 clean CLI-first original
prompt run documented in:

- `evals/impact/notes/manual_v2_cli_original_ownership_20260425_findings.md`

The latest report-worthy release-distribution evidence is the 2026-04-25 clean CLI-first original
prompt run documented in:

- `evals/impact/notes/manual_v2_cli_original_release_distribution_20260425_findings.md`

Both runs used five independent persisted Codex CLI sessions, `gpt-5.5`, `xhigh`, the original
prompt, and complete session exports validated by `validate_run.py` with no critical confounds.

The earlier 2026-04-25 10-repo transition run remains useful qualitative evidence, but it is no
longer the current formal ownership result because it mixed VS Code UI and Codex CLI fallback.

## Main Findings So Far

### Ownership Boundary

The clearest positive formal signal for AI wiki is the ownership-boundary primary comparison.

- No AI wiki (`s01`): fail. The agent repeated the package-surface mistake by adding
  `src/ai_wiki_toolkit/contributor_workflow.py` and package CLI wiring.
- Realistic AI wiki workflow (`s05`): success. The agent kept the helper repo-local under
  `scripts/`, added tests, and updated local workflow docs without adding package code.

This supports the claim that AI wiki workflow can help prevent repeated implementation-surface
mistakes.

Diagnostic variants are explanatory only:

- `aiwiki_linked_raw_only` succeeded and used the raw repo-local placement draft.
- `aiwiki_linked_consolidated_only` failed by putting the core helper in `src/ai_wiki_toolkit/`.
- `aiwiki_scaffold_no_target_memory` succeeded, but is contaminated as a no-target diagnostic because
  it still used workflow and impact-eval meta memory.

### Release Distribution Integrity

The clean formal release-distribution primary comparison now gives a narrower positive signal.

- No AI wiki (`s01`): partial. The agent produced a broad release/npm matrix expansion, but missed
  the known `linux-musl-x64` build hazard: Alpine PyInstaller builds need binutils/objdump setup run
  as root.
- Realistic AI wiki workflow (`s05`): success. The agent produced the same broad expansion and also
  applied the musl setup lesson, npm `libc` metadata, Windows zip staging, docs, Homebrew alignment,
  and tests.

This supports the claim that AI wiki can improve coordination quality for multi-surface release
work. It does not show that AI wiki is necessary for the agent to attempt the expansion; the
no-AI-wiki control already did substantial work.

Diagnostic variants are explanatory only. In the clean release run, `aiwiki_scaffold_no_target_memory`,
`aiwiki_linked_raw_only`, and `aiwiki_linked_consolidated_only` all scored success. They help explain
that adjacent release memory and targeted raw/consolidated notes can carry the missing musl/npm
details, but they are not the primary causal comparison.

## Current Claim Boundaries

Reasonable to claim:

- The clean CLI-first ownership-boundary run supports AI wiki workflow usefulness for the
  repeated-problem ownership-boundary task.
- The clean CLI-first release-distribution run supports a narrower AI wiki usefulness claim for
  completeness and known-hazard avoidance in multi-surface release work.
- Original prompts are better than medium-style prompts for testing memory reuse.
- Session exports are necessary for judging why the agent made a decision.

Not yet reasonable to claim:

- a clean quantitative causal estimate of AI wiki impact
- a seed-controlled benchmark result
- a final model comparison
- proof that AI wiki is necessary for release-distribution success
- a formal claim from the 2026-04-25 transition batch

## Next Formal Work

The next useful formal work is replication, not a new transition batch:

1. Repeat each family with additional independent five-slot batches.
2. Keep `original.md`, Codex CLI-first execution, and run-level `caffeinate`.
3. Preserve complete session exports and validator output before scoring.
4. Consider a stricter no-adjacent-memory release diagnostic if mechanism isolation matters.
5. Continue treating diagnostic variants as explanations, not primary conclusions.
