# Impact Eval Report

This report summarizes the current evidence across `evals/impact/` notes. It is intentionally short:
the detailed run evidence lives in `evals/impact/notes/`.

## Current Status

The benchmark now has two useful families:

- `ownership_boundary`: tests whether AI wiki workflow helps keep contributor-only behavior out of
  package code.
- `release_distribution_integrity`: tests whether AI wiki workflow helps coordinate public release
  and npm distribution changes across coupled surfaces.

The latest evidence is the 2026-04-25 10-repo original-prompt transition run documented in:

- `evals/impact/notes/manual_v2_original_10_repo_findings.md`

That run is useful qualitative evidence, but it is not the final formal run because execution mixed
VS Code UI and Codex CLI fallback, and old session exports did not record observed source/model/effort
fields.

## Main Findings So Far

### Ownership Boundary

The clearest positive signal for AI wiki is the ownership-boundary primary comparison.

- No AI wiki: the agent repeated the package-surface mistake by adding code under
  `src/ai_wiki_toolkit/`.
- Realistic AI wiki workflow: the agent kept the helper repo-local under `scripts/`, added tests,
  and updated `ai-wiki/workflows.md`.

This supports the claim that AI wiki workflow can help prevent repeated implementation-surface
mistakes.

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

- AI wiki workflow looks useful for the ownership-boundary repeated-problem task.
- Release-distribution memory appears more helpful for completeness and verification than for
  deciding whether to attempt the work.
- Original prompts are better than medium-style prompts for testing memory reuse.
- Session exports are necessary for judging why the agent made a decision.

Not yet reasonable to claim:

- a clean quantitative causal estimate of AI wiki impact
- a seed-controlled benchmark result
- a final model comparison
- a formal result from the 2026-04-25 transition batch

## Next Formal Run

The next report-worthy run should use the stricter protocol now documented in `evals/impact/README.md`:

1. Generate neutral five-slot workspaces.
2. Run only `original.md`.
3. Use Codex CLI-first execution for every slot.
4. Capture first-pass artifacts immediately.
5. Export a complete session manifest.
6. Run `validate_run.py`.
7. Score each slot with `score_run.py`.
8. Generate and update this report from the scored results.
