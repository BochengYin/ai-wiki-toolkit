# Work Ledger Schema v1

The work ledger records todos, active or processing work, blocked items, review items, completed work, and epics as append-only events.

## Source Of Truth

User-owned work events live in `ai-wiki/work/events/<handle>.jsonl`.

Package-managed generated views live under `ai-wiki/_toolkit/work/`:

- `state.json`
- `report.md`

Generated views are local snapshots. Regenerate them with `aiwiki-toolkit work report` or `aiwiki-toolkit refresh-metrics`.

## Event Fields

Each JSONL event may include:

- `schema_version`: currently `work-v1`
- `event_id`
- `event_type`: `captured` or `status_changed`
- `occurred_at`
- `author_handle`
- `item_type`: `task` or `epic`
- `work_id`
- `title`
- `status`
- `epic_id`
- `source`
- `links`
- `agent_name`
- `model`
- `notes`

## Statuses

Use:

- `inbox`
- `proposed`
- `todo`
- `planned`
- `active`
- `processing`
- `blocked`
- `review`
- `done`
- `archived`
- `dropped`

## Lifecycle Rules

1. Capture conversation todos with `aiwiki-toolkit work capture`.
2. Move work through lifecycle states with `aiwiki-toolkit work status`.
3. Prefer append-only events over rewriting shared work files.
4. Treat `_toolkit/work/*` as generated views, not canonical memory.
5. Do not automatically archive or drop a large epic without human confirmation.
6. Route packets may use active, processing, or matching work items as routing hints, but work events are not knowledge-reuse evidence by themselves.
