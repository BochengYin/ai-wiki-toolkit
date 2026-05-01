# AI Wiki Evidence Integrity Task

This prompt family tests one concrete AI wiki telemetry and end-of-task workflow failure without
directly naming the intended command or schema design.

## Task

Improve the AI wiki usefulness evidence workflow so it is auditable rather than anecdotal.

The repo can already append document-level reuse observations, but the metrics do not reliably show
whether a completed task actually performed the AI wiki reuse check. The evidence can also be
distorted by counting managed workflow/control docs as knowledge reuse, and the end-of-task update
decision can disappear when there is no durable memory to save.

The agent should update the toolkit and repo AI wiki workflow so completed tasks leave trustworthy
evidence, add focused regression tests, and update the relevant docs.

## Why this is a real task

This benchmark uses a real historical evidence gap in this repository. The first reuse-metrics
shape could record per-document observations, but it did not create a task-level denominator for
completed work. That made it impossible to distinguish "the AI wiki was checked and was not useful"
from "the workflow never ran."

The repo already has raw drafts about the same failure class:

- `ai-wiki/people/bochengyin/drafts/ai-wiki-usefulness-metrics-need-task-level-checks-plus-doc-events.md`
- `ai-wiki/people/bochengyin/drafts/ai-wiki-reuse-metrics-should-exclude-managed-docs-and-shard-by-handle.md`
- `ai-wiki/people/bochengyin/drafts/end-of-task-ai-wiki-update-check-must-always-run.md`

Without relevant memory, an agent could easily add only more document-level logging, count
`_toolkit/**` reads as successful knowledge reuse, write all append-only evidence into shared files,
or keep the final update decision optional.

## Expected Implementation Shape

A strong solution will usually:

- keep document-level reuse observations separate from task-level reuse checks
- make task-level checks recordable even when no user-owned AI wiki doc was useful
- avoid counting managed `_toolkit/**` docs as knowledge-reuse evidence
- shard user-owned evidence by handle to reduce append-only merge conflicts
- keep generated aggregate metrics under package-managed paths
- make the end-of-task update outcome explicit for every completed task
- add CLI, schema, scaffold, and docs/tests that cover the workflow

A weak solution often:

- treats absence of document reuse events as proof that the AI wiki was not useful
- logs managed workflow docs as successful reuse evidence
- keeps a single shared JSONL write target for all contributors
- adds metrics output without a task-level denominator
- updates only docs or prompts without regression tests
- emits update-check text only when a new durable memory draft exists

## What Varies Across Variants

- `no_aiwiki_workflow`: no AI wiki at all
- `aiwiki_ambient_memory_workflow`: realistic current AI wiki memory
- `aiwiki_scaffold_no_target_memory`: AI wiki exists, but not the target evidence-integrity memory
- `aiwiki_linked_raw_only`: the target raw drafts exist
- `aiwiki_linked_consolidated_only`: linked consolidated evidence and ownership docs exist
- `aiwiki_scaffold_no_adjacent_memory`: AI wiki scaffold exists, but target evidence memory and
  adjacent workflow skills/docs are removed

## Manual v2 Prompt

Manual v2 uses only:

- `original.md`: the historical evidence-integrity request without naming the exact command or
  file layout

## Human Evaluation Questions

- Did the agent add a task-level evidence record distinct from document-level reuse events?
- Did it preserve a denominator for completed tasks that checked the AI wiki but reused nothing?
- Did it keep managed `_toolkit/**` docs out of knowledge-reuse metrics?
- Did it avoid shared append-only evidence logs for multi-handle collaboration?
- Did it make the end-of-task update outcome mandatory and visible?
- Did it add focused tests and docs without unrelated wiki or release churn?
