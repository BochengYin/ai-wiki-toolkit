# Work Ledger Index

Use this area for repo-native work state that agents should be able to reference across conversations.

The default machine-readable event log lives under `work/events/<handle>.jsonl`.

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

- Capture conversation todos with `aiwiki-toolkit work capture`.
- Update status with `aiwiki-toolkit work status`.
- Regenerate local managed views with `aiwiki-toolkit work report`.
- Treat generated files under `_toolkit/work/` as views, not canonical work memory.
