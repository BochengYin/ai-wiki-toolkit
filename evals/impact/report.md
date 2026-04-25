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

That run used five independent persisted Codex CLI sessions, `gpt-5.5`, `xhigh`, the original prompt,
and a complete session export validated by `validate_run.py` with no critical confounds.

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

The release-distribution family is less useful as a binary pass/fail benchmark because the
no-AI-wiki run already produced a broad implementation.

It is still useful for judging coordination quality. AI wiki variants more explicitly reused known
release lessons around distribution-matrix alignment, musl setup, Windows ARM smoke behavior, and
npm platform metadata.

This supports a narrower claim: AI wiki can improve coordination and verification discipline for
multi-surface release work, but this family needs detailed scoring rather than simple success counts.

## Current Claim Boundaries

Reasonable to claim:

- The clean CLI-first ownership-boundary run supports AI wiki workflow usefulness for the
  repeated-problem ownership-boundary task.
- Release-distribution memory appears more helpful for completeness and verification than for
  deciding whether to attempt the work.
- Original prompts are better than medium-style prompts for testing memory reuse.
- Session exports are necessary for judging why the agent made a decision.

Not yet reasonable to claim:

- a clean quantitative causal estimate of AI wiki impact
- a seed-controlled benchmark result
- a final model comparison
- a formal release-distribution result from the 2026-04-25 transition batch

## Next Formal Run

The next report-worthy run should apply the same stricter protocol to
`release_distribution_integrity`:

1. Generate neutral five-slot workspaces.
2. Run only `original.md`.
3. Use Codex CLI-first execution for every slot.
4. Capture first-pass artifacts immediately.
5. Export a complete session manifest.
6. Run `validate_run.py`.
7. Score each slot with `score_run.py`.
8. Generate and update this report from the scored results.
