# Work Ledger Schema v1

The work ledger records todos, active or processing work, blocked items, review items, completed work, and epics as append-only events.

## Source Of Truth

Local actor identity lives in the gitignored `.env.aiwiki` file at the repository root.

User-owned work events live in `ai-wiki/work/events/<handle>.jsonl`.

Package-managed generated views live under `ai-wiki/_toolkit/work/`:

- `state.json`
- `report.md`
- `by-assignee/<handle>.md`
- `by-reporter/<handle>.md`

Generated views are local snapshots. Regenerate them with `aiwiki-toolkit work report` or `aiwiki-toolkit refresh-metrics`.

Keep canonical work state in `ai-wiki/work/events/<handle>.jsonl`, not in `ai-wiki/people/<handle>/`.
The people namespace is for personal drafts and preferences. Work links to people through event fields.

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
8. Route packets may use work assigned to the current actor as actionable context by default.
9. Route packets may show work assigned to other handles only when the current task directly matches that work.
10. Work events are not knowledge-reuse evidence by themselves.
