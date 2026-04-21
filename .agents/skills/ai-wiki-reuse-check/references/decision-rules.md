# Decision Rules

## Task Eligibility

Classify the task before judging whether `no_wiki_use` is acceptable.

- `not_applicable`
  Pure operational work such as pushing a PR, renaming a branch, or running an already-decided command.

- `optional`
  Low-risk work where repo memory may help, but the task can often complete correctly without it.

- `eligible`
  Coding, debugging, release, review, clarification, or conflict-heavy work where existing team memory could materially change the plan.

## Outcome Meanings

- `wiki_used`
  Use when one or more AI wiki document reuse events were recorded for the task.

- `no_wiki_use`
  Use when the task completed without recording any AI wiki document reuse events.

## Recording Rules

- Record one `aiwiki-toolkit record-reuse` event per consulted user-owned AI wiki document.
- Do not record managed `_toolkit/**` docs with `record-reuse`; cite those paths in progress updates or final notes instead.
- `no_wiki_use` is correct for `not_applicable` tasks; do not force unrelated wiki reads just to improve coverage metrics.
- If an AI wiki doc changed the task plan or behavior, cite its path in a progress update or final note.
- Use `reuse_outcome=not_helpful` when a consulted user-owned doc did not help materially but still influenced the search path.
- Record the task-level `aiwiki-toolkit record-reuse-check` entry after all document-level reuse events for that task are appended.

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
