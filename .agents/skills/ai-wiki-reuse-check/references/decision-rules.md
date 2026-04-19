# Decision Rules

## Outcome Meanings

- `wiki_used`
  Use when one or more AI wiki document reuse events were recorded for the task.

- `no_wiki_use`
  Use when the task completed without recording any AI wiki document reuse events.

## Recording Rules

- Record one `aiwiki-toolkit record-reuse` event per consulted user-owned AI wiki document.
- Do not record managed `_toolkit/**` docs with `record-reuse`; cite those paths in progress updates or final notes instead.
- If an AI wiki doc changed the task plan or behavior, cite its path in a progress update or final note.
- Use `reuse_outcome=not_helpful` when a consulted user-owned doc did not help materially but still influenced the search path.
- Record the task-level `aiwiki-toolkit record-reuse-check` entry after all document-level reuse events for that task are appended.
