---
title: "Impact eval no-target AI wiki slots must exclude task-specific workflow memory"
author_handle: "bochengyin"
model: "gpt-5.5"
source_kind: "eval-analysis"
status: "draft"
created_at: "2026-04-25T09:20:00+10:00"
updated_at: "2026-04-25T09:20:00+10:00"
promotion_candidate: false
promotion_basis: "none"
---
# Impact Eval No-Target AI Wiki Slots Must Exclude Task-Specific Workflow Memory

## Context

In the original-prompt `ownership_boundary` eval, every AI wiki-enabled slot avoided the package-surface failure and implemented a repo-local `scripts/pr_flow.py` helper.

The result looked like evidence that AI wiki use improved the outcome. It did improve the working mode relative to the clean no-AI-wiki baseline, but the `aiwiki_scaffold_no_target_memory` slot was not a clean no-target condition.

## What Happened

The scaffold AI wiki already contained `ai-wiki/workflows.md`, and that file referenced the repo-local helper path:

- `uv run python scripts/pr_flow.py create`
- `uv run python scripts/pr_flow.py finish`

The session transcript shows Codex using that file as the decisive implementation cue and saying that the repo already documented a missing `scripts/pr_flow.py` helper.

## Why It Matters

If a no-target AI wiki slot contains workflow docs that name the intended implementation surface, the eval can still compare working modes:

- with AI wiki and memory
- without AI wiki and without memory

But it cannot cleanly isolate raw/consolidated target-memory effects inside the AI wiki variants.

## Future Eval Rule

For a no-target AI wiki condition, remove or neutralize task-specific workflow docs, draft notes, index entries, and examples that reveal:

- the intended file path
- the intended layer or ownership boundary
- the historical failure mode
- the exact helper or command name

Keep only generic toolkit scaffolding and unrelated repo memory in that condition.

## Reuse Assessment

Use this when designing impact eval slots where one condition is meant to represent AI wiki scaffolding without relevant task memory.
