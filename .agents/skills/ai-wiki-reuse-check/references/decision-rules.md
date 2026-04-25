# Decision Rules

## Task Relevance

Classify the task before judging whether `no_wiki_use` is acceptable.

- `not_relevant`
  Pure operational work such as pushing a PR, renaming a branch, or running an already-decided command.

- `optional`
  Low-risk work where repo memory may help, but the task can often complete correctly without it.

- `relevant`
  Coding, debugging, release, review, clarification, or conflict-heavy work where existing team memory could materially change the plan.

## Outcome Meanings

- `wiki_used`
  Use when one or more AI wiki document reuse events were recorded for the task.

- `no_wiki_use`
  Use when the task completed without recording any AI wiki document reuse events.

## Recording Rules

- Record one `aiwiki-toolkit record-reuse` event per consulted user-owned AI wiki document.
- Do not record managed `_toolkit/**` docs with `record-reuse`; cite those paths in progress updates or final notes instead.
- Use `reuse_outcome=not_helpful` when a consulted user-owned doc did not help materially but still influenced the search path.
- Record the task-level `aiwiki-toolkit record-reuse-check` entry after all document-level reuse events for that task are appended.
- Prefer specific doc ids such as `conventions/python-typing`, `problems/async-notification-tests-flaky`, `features/bulk-invoice-upload`, or `review-patterns/shared-prompt-files-must-be-user-agnostic`.
- `no_wiki_use` is correct for `not_relevant` tasks; do not force unrelated wiki reads just to improve coverage metrics.

## Material Reuse Hints

Listing used docs is not enough to prove usefulness. When relevant, note whether the wiki:

- changed the plan
- avoided a retry
- blocked a wrong path
- resolved a conflict
- reused an existing convention
- captured durable memory

## Missed Relevant Memory

If a relevant user-owned AI wiki doc should have been used but was only discovered after user correction, review, or later failure, note the miss in the footer even when telemetry still records `no_wiki_use`.
