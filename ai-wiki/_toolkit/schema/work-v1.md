# Work Ledger Schema v1

The work ledger records todos, active or processing work, blocked items, review items, completed work, and epics as append-only events.

## Source Of Truth

Local actor identity lives in the gitignored `.env.aiwiki` file at the repository root.

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
- `reporter_handle`
- `assignee_handles`
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
3. Resolve the current actor from explicit CLI input, environment, `.env.aiwiki`, git config, then fallback.
4. Default `author_handle`, `reporter_handle`, and `assignee_handles` to the current actor when capturing new work.
5. Prefer append-only events over rewriting shared work files.
6. Treat `_toolkit/work/*` as generated views, not canonical memory.
7. Do not automatically archive or drop a large epic without human confirmation.
8. Route packets may use active, processing, or matching work items as routing hints, but work events are not knowledge-reuse evidence by themselves.
