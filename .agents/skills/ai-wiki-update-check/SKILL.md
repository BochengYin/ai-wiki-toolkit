---
name: ai-wiki-update-check
description: Produce the mandatory end-of-task AI wiki write-back outcome for ai-wiki-toolkit. Use it to record only public/local trial-error memory or reusable clarification memory, then emit the required final status line.
---

# AI Wiki Write-Back Check

Use this skill at the end of every completed task in this repository.

This outcome is mandatory even when the correct result is `None`.

## Core Workflow

1. Review the completed task, local/public checks, and user-visible outcome.
2. Before returning `None`, check only for durable public/local write-back signals:
   - a failed local/public check that changed the fix
   - repeated public trial-and-error on the same source file, API, command, or behavior
   - a reusable tooling, packaging, or environment mismatch found through local/public evidence
   - a reusable clarification from the user that future tasks in this repo should apply
3. Do not write memory from hidden evaluator failures, hidden test names, private benchmark answers, or prior hidden-derived fixes.
4. Do not write back after a clean one-shot task unless it produced a reusable clarification or public/local trial-error lesson.
5. Choose exactly one outcome: `None` or `MemoryRecorded`.
6. If the outcome is `MemoryRecorded`, create or update a small note under `ai-wiki/memory/` and update `ai-wiki/memory/index.md`.
7. Emit the final result using the exact output contract in [references/output-contract.md](references/output-contract.md).
8. Use [references/decision-rules.md](references/decision-rules.md) for the decision gate, memory shape, conflict handling, and index update rules.

## Constraints

- Do not skip the write-back outcome just because no durable lesson is expected.
- Do not write every task summary into the wiki.
- Do not write from hidden evaluator results or private benchmark answers.
- Do not treat "no wiki docs were opened" as proof that no public/local trial-error memory was produced.
- If new memory conflicts with existing memory, flag the conflict instead of silently overwriting.
- Prefer small durable memory over long transcripts.
- Keep project-specific memory in `ai-wiki/memory/`.
