# Reuse Schema v1

This document describes the first machine-readable schema for measuring whether AI wiki knowledge was reused during real work.

## Goals

- keep user-owned Markdown knowledge stable
- add machine-readable evidence without rewriting user docs
- distinguish preloaded knowledge reuse from lookup-based reuse
- support lightweight efficiency estimates without pretending token measurements are exact

## Source Of Truth

User-owned reuse observations live in `ai-wiki/metrics/reuse-events.jsonl`.

Package-managed aggregate files are regenerated under `ai-wiki/_toolkit/metrics/`.

The toolkit can append explicit observations via `aiwiki-toolkit record-reuse`.

## Event Fields

Each JSONL event may include:

- `schema_version`
- `event_id`
- `observed_at`
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

## Aggregate Outputs

The toolkit currently derives:

- `_toolkit/catalog.json`
- `_toolkit/metrics/document-stats.json`
- `_toolkit/metrics/task-stats.json`
