---
name: ai-wiki-consolidate-drafts
description: Use when handle-local AI wiki drafts have grown into a noisy backlog and related notes should be clustered, refined, or promoted without directly rewriting shared docs by default.
---

# AI Wiki Consolidate Drafts

Use this skill when `ai-wiki/people/*/drafts/` has accumulated related notes and the next step is to consolidate them into clearer draft clusters, promotion candidates, or explicit conflicts and supersessions.

## Workflow

1. Read the relevant draft set, usually under one handle in `ai-wiki/people/*/drafts/`.
2. Read nearby context that may confirm or narrow the consolidation target:
   - `ai-wiki/conventions/index.md`
   - `ai-wiki/decisions.md`
   - `ai-wiki/review-patterns/index.md`
   - `ai-wiki/problems/index.md`
   - `ai-wiki/features/index.md`
   - relevant files under `ai-wiki/trails/` when chronology matters
   - `ai-wiki/metrics/` and `_toolkit/metrics/*.json` only as weak signals
3. Cluster drafts by durable topic, repeated failure mode, or repeated rule, not by filename alone.
4. For each cluster, choose one next action using [references/candidate-types.md](references/candidate-types.md).
5. Use [references/promotion-targets.md](references/promotion-targets.md) to propose the best destination when a cluster is mature enough for shared or repo-level memory.
6. Use [references/conflict-and-supersession.md](references/conflict-and-supersession.md) to flag conflicts, refinements, or supersession instead of silently merging away differences.
7. Default to refining handle-local drafts first. Do not directly rewrite `ai-wiki/conventions/*.md`, `ai-wiki/review-patterns/*.md`, `ai-wiki/problems/*.md`, or `ai-wiki/features/*.md` unless the user explicitly asks for promotion or doc creation.
8. Emit the result using [references/output-contract.md](references/output-contract.md).

## Rules

- Cluster first, judge second.
- Do not promote every repeated draft.
- Metrics may support prioritization, but they are weak signals and must not be the sole basis for promotion.
- Make the suggested target path explicit whenever the action is `Refine draft` or `Promotion candidate`.
- If a cluster is still unstable, keep it local and explain what evidence is still missing.
- Shared conventions and review patterns still require human confirmation before writing shared docs.
