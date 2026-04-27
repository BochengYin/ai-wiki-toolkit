# Work Ledger Index

Use this area for repo-native work state that agents should be able to reference across conversations.

The default machine-readable event log lives under `work/events/<handle>.jsonl`.

Keep canonical work items in this central ledger, not inside `people/<handle>/`.
Link work to people with `author_handle`, `reporter_handle`, and `assignee_handles`.

## Statuses

Work items may move through:

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

## Usage

- Resolve current local actor identity from `.env.aiwiki` when no explicit handle is supplied.
- Capture conversation todos with `aiwiki-toolkit work capture`.
- Update status with `aiwiki-toolkit work status`.
- Use `aiwiki-toolkit work mine` to inspect open work assigned to the current local actor.
- Use `aiwiki-toolkit work list --assignee <handle>` or `--reporter <handle>` for team views.
- Regenerate local managed views with `aiwiki-toolkit work report`.
- Treat generated files under `_toolkit/work/` as views, not canonical work memory.
- Route packets should treat work assigned to the current actor as actionable by default. Work assigned to other handles should appear only when directly matched by the user's request.
