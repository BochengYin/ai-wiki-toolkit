---
name: ai-wiki-reuse-check
description: Produce the mandatory end-of-task AI wiki reuse evidence for ai-wiki-toolkit. Use it to classify task eligibility, record consulted user-owned docs, append local telemetry, and emit the user-facing footer.
---

# AI Wiki Reuse Evidence

Use this skill at the end of every completed task in this repository.

This evidence footer is mandatory even when the correct outcome is `no_wiki_use`.

## Core Workflow

1. Classify the task as `eligible`, `optional`, or `not_applicable` for AI wiki use before judging whether the absence of wiki reads is a problem.
2. Use the final AI wiki footer as the user-facing evidence surface; local telemetry is the machine-readable record behind it.
3. Review whether any repo-local or cross-project AI wiki docs were consulted during the task.
4. Before or during the task, check whether relevant memory existed in:
   - `conventions/`
   - `decisions.md`
   - `review-patterns/`
   - `problems/`
   - `features/`
   - `trails/`
   - `people/<handle>/`
5. If one or more user-owned AI wiki docs were consulted, append one `aiwiki-toolkit record-reuse` event per consulted doc.
6. If a managed `_toolkit/**` doc changed the plan or behavior, cite its path in a progress update or final note, but do not log it with `record-reuse`.
7. When a user-owned AI wiki doc materially changes the plan or behavior, cite its path in a progress update or final note.
8. Use `reuse_outcome=not_helpful` for consulted user-owned docs that did not help materially but still affected the task flow.
9. Prefer specific doc ids such as `conventions/python-typing`, `problems/async-notification-tests-flaky`, or `features/bulk-invoice-upload`.
10. Append one `aiwiki-toolkit record-reuse-check` entry for the task using:
   - `wiki_used` when one or more doc events were recorded
   - `no_wiki_use` when no AI wiki doc events were recorded
11. Emit the final result using [references/output-contract.md](references/output-contract.md).

## Constraints

- Do not skip the footer just because the task was small or the result seems obvious.
- Record one task-level reuse check for every completed task.
- `no_wiki_use` is correct for `not_applicable` operational tasks.
- Do not force unrelated wiki reads just to improve coverage metrics.
- If multiple user-owned AI wiki docs were consulted, record them as separate `record-reuse` events.
- Do not record managed `_toolkit/**` docs with `record-reuse`.
- Listing used docs is evidence of touch, not proof of material reuse.
- If a relevant user-owned AI wiki doc should have been used but was not, note the miss in the footer even if telemetry still records `no_wiki_use`.
- If an AI wiki doc changed the task plan or behavior, name the path explicitly in a user-facing update.
