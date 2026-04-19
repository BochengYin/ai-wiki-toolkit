# Reuse Schema v1

This document describes the first machine-readable schema for measuring whether AI wiki knowledge was reused during real work.

## Goals

- keep user-owned Markdown knowledge stable
- add machine-readable evidence without rewriting user docs
- distinguish preloaded knowledge reuse from lookup-based reuse
- support lightweight efficiency estimates without pretending token measurements are exact

## Source Of Truth

User-owned reuse observations live in `ai-wiki/metrics/reuse-events/<handle>.jsonl`.

User-owned reuse checks live in `ai-wiki/metrics/task-checks/<handle>.jsonl`.

Package-managed aggregate files are regenerated under `ai-wiki/_toolkit/metrics/`.

The toolkit can append explicit document observations via `aiwiki-toolkit record-reuse`.

The toolkit can append task-level reuse checks via `aiwiki-toolkit record-reuse-check`.

Legacy flat files such as `ai-wiki/metrics/reuse-events.jsonl` and `ai-wiki/metrics/task-checks.jsonl`
are still read for compatibility, but new writes should use the per-handle shard paths.

## Reuse Event Fields

Each JSONL event may include:

- `schema_version`
- `event_id`
- `observed_at`
- `author_handle`
- `task_id`
- `doc_id`
- `doc_kind`
- `retrieval_mode`
- `evidence_mode`
- `reuse_outcome`
- `reuse_effects`
- `agent_name`
- `model`
- `notes`
- `estimated_savings`

## Task Check Fields

Each task check entry may include:

- `schema_version`
- `check_id`
- `checked_at`
- `author_handle`
- `task_id`
- `check_outcome`
- `agent_name`
- `model`
- `notes`

## Retrieval Mode

- `preloaded`: the document was already loaded in the normal read path
- `lookup`: the document was consulted after extra searching or backtracking

## Evidence Mode

- `explicit`: the run clearly stated that the document was used
- `inferred`: the reuse is inferred from behavior or chronology rather than an explicit statement

## Reuse Outcome

- `resolved`: the wiki materially helped resolve the task
- `partial`: the wiki helped, but did not fully resolve the task
- `not_helpful`: the wiki was consulted, but did not help materially

## Managed Docs

Managed control-plane docs under `_toolkit/**` must not be recorded with `aiwiki-toolkit record-reuse`.

If they materially influence task behavior, cite their path in user-facing progress notes instead.

## Aggregate Outputs

The toolkit currently derives:

- `_toolkit/catalog.json`
- `_toolkit/metrics/document-stats.json`
- `_toolkit/metrics/task-stats.json`

If those generated views drift or conflict across branches, regenerate them with
`aiwiki-toolkit refresh-metrics` instead of hand-merging the JSON.
