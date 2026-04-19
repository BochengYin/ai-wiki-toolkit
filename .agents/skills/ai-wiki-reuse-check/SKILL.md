---
name: ai-wiki-reuse-check
description: Run the mandatory end-of-task AI wiki reuse check for ai-wiki-toolkit. Use it to record whether AI wiki docs were consulted during the task, append one reuse event per consulted doc, append one task-level reuse check, and report the outcome.
---

# AI Wiki Reuse Check

Use this skill at the end of every completed task in this repository.

This check is mandatory even when the correct outcome is `no_wiki_use`.

## Core Workflow

1. Review whether any repo-local or cross-project AI wiki docs were consulted during the task.
2. If one or more user-owned AI wiki docs were consulted, append one `aiwiki-toolkit record-reuse` event per consulted doc.
3. If a managed `_toolkit/**` doc changed the plan or behavior, cite its path in a progress update or final note, but do not log it with `record-reuse`.
4. When a user-owned AI wiki doc materially changes the plan or behavior, cite its path in a progress update or final note.
5. Use `reuse_outcome=not_helpful` for consulted user-owned docs that did not help materially but still affected the task flow.
6. Append one `aiwiki-toolkit record-reuse-check` entry for the task using:
   - `wiki_used` when one or more doc events were recorded
   - `no_wiki_use` when no AI wiki doc events were recorded
7. Emit the final result using [references/output-contract.md](references/output-contract.md).

## Constraints

- Do not skip the check just because the task was small or the result seems obvious.
- Record one task-level reuse check for every completed task.
- If multiple user-owned AI wiki docs were consulted, record them as separate `record-reuse` events.
- Do not record managed `_toolkit/**` docs with `record-reuse`.
- If an AI wiki doc changed the task plan or behavior, name the path explicitly in a user-facing update.
