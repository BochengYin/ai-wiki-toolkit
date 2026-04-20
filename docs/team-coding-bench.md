# TeamCodingBench Roadmap

This document records a future evaluation plan for measuring whether `ai-wiki-toolkit` improves coding-agent behavior in small team workflows.

Do not implement this benchmark yet.

## Goal

Compare the same coding tasks with and without `ai-wiki-toolkit`.

Baseline:

- agent gets repo plus raw task prompt

Treatment:

- agent gets repo plus `ai-wiki-toolkit` shared memory and skills

## What To Measure

- `clarification_hit_rate`
- `false_confirmed_rate`
- `preference_reuse_rate`
- `repeated_review_issue_rate`
- `conflict_detection_rate`
- `requirement_coverage`
- `tests_pass_rate`
- `wiki_update_quality`
- `memory_regression_accuracy`

## Toy Project Ideas

A small FastAPI or Python service with:

- tickets
- permissions
- notifications
- CSV export and import
- tests
- type hints
- reviewer preferences
- feature clarifications

## Example Tasks

### Ambiguous requirement

Prompt:
"Users should be able to export tickets, but only the right people should see private comments."

Expected:

- agent asks or flags permission ambiguity
- agent reads the existing decision about private comments
- agent does not expose private comments to everyone

### PR review preference capture

Prompt:
"Reviewer Carol says: Please don't use object here. We know this returns str or None."

Expected:

- agent classifies it as a Python typing preference
- agent proposes a person preference and a convention candidate
- future tasks avoid casual `object` type hints

### Problem-solution reuse

Prompt:
"Implement notification when ticket is assigned."

Existing memory:
"Async notification tests are flaky unless using fake queue."

Expected:

- agent uses the fake queue in tests
- no sleep-based flaky tests

### Conflict detection

Existing decision:
"Only admins can bulk export tickets."

New prompt:
"PO says all team members should export tickets."

Expected:

- agent flags the conflict instead of silently overwriting

## Future Inspiration

The benchmark should follow the spirit of synthetic-but-realistic, repeatable evaluation:
fixed corpus, fixed tasks, gold expectations, baseline versus treatment comparison.
