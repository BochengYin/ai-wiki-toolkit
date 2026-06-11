# Reuse Schema v1

This document describes the first machine-readable schema for measuring whether AI wiki knowledge was reused during real work.

## Goals

- keep user-owned Markdown knowledge stable
- add machine-readable evidence without rewriting user docs
- distinguish preloaded knowledge reuse from lookup-based reuse
- support lightweight efficiency estimates without pretending token measurements are exact

## Source Of Truth

User-owned reuse observations live in `ai-wiki/metrics/reuse-events/<handle>.jsonl`.

User-owned route selection traces live in `ai-wiki/metrics/route-traces/<handle>.jsonl`.

User-owned source incident timing evidence lives in `ai-wiki/metrics/source-incidents/<handle>.jsonl`.

User-owned taxonomy post-hoc evidence lives in `ai-wiki/metrics/taxonomy-evidence/<handle>.jsonl`.

User-owned reuse checks live in `ai-wiki/metrics/task-checks/<handle>.jsonl`.

Package-managed aggregate files are regenerated under `ai-wiki/_toolkit/metrics/`.
Handle-scoped generated metrics are regenerated under `ai-wiki/_toolkit/metrics/by-handle/<handle>/`.

The installer ignores the telemetry shards and generated aggregate views in `.gitignore` by default
so routine reuse logging does not dirty git status.

The toolkit can append explicit document observations via `aiwiki-toolkit record-reuse`.

The toolkit can append source incident timing evidence via `aiwiki-toolkit source-incident backfill-writeback` or `aiwiki-toolkit source-incident capture-post-turn`.

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
- `session_id`
- `source_session_id`
- `source_task_id`
- `consulted_order`
- `signal_status`
- `not_helpful_reason`
- `resolved_by_doc_id`
- `superseded_by_doc_id`

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

## Route Trace Fields

Each route trace entry may include:

- `schema_version`
- `trace_id`
- `routed_at`
- `author_handle`
- `task_id`
- `task_type`
- `effort`
- `domain_tags`
- `guardrail_tags`
- `changed_paths`
- `selected_doc_ids`
- `must_load_doc_ids`
- `index_card_doc_ids`
- `maybe_load_doc_ids`
- `skipped_doc_ids`
- `packet_words`
- `selected_doc_count`
- `index_card_count`
- `maybe_load_count`
- `must_load_count`
- `route_scores`
- `context_budget`

## Route Diagnostic Metrics

`aiwiki-toolkit diagnose memory --focus route` joins route traces with downstream
`record-reuse` events by `task_id`.

It reports:

- `selected_doc_ids`: docs selected by route
- `useful_selected_doc_ids`: selected docs with resolved or partial downstream reuse
- `selected_but_unused_doc_ids`: selected docs with no downstream reuse event
- `selected_not_helpful_doc_ids`: selected docs with only not_helpful downstream reuse
- `later_lookup_doc_ids`: lookup docs that were not selected by route
- `missed_useful_doc_ids`: useful lookup docs that were not selected by route
- route precision, route recall proxy, route noise rate, packet words, selected doc count,
  and later lookup count

Route recall is a proxy because useful-but-unlooked-up docs are unknowable from local
telemetry alone.

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

## Diagnostic Provenance

Reuse events may carry optional provenance for post-task diagnosis:

- `session_id`: the current agent session or run id
- `source_session_id`: the session that originally generated the memory
- `source_task_id`: the task that originally generated the memory
- `consulted_order`: 1-based order in which the document was read
- `signal_status`: `candidate` for inferred hints or `confirmed` for human/explicit judgments
- `not_helpful_reason`: one of `stale`, `too_generic`, `wrong_scope`, `missing_detail`, `hard_to_find`, `contradicted`, `superseded`, `superseded_by_later_doc`, or `other`
- `resolved_by_doc_id`: a later document that resolved the task
- `superseded_by_doc_id`: a later document that made this one stale, noisy, or less useful

Candidate signals are review hints, not promotion blockers by themselves unless the team treats
them as confirmed evidence.

## Managed Docs

Managed control-plane docs under `_toolkit/**` must not be recorded with `aiwiki-toolkit record-reuse`.

If they materially influence task behavior, cite their path in user-facing progress notes instead.

## Aggregate Outputs

The toolkit currently derives:

- `_toolkit/catalog.json`
- `_toolkit/metrics/document-stats.json`
- `_toolkit/metrics/task-stats.json`
- `_toolkit/metrics/by-handle/<handle>/document-stats.json`
- `_toolkit/metrics/by-handle/<handle>/task-stats.json`

Those generated views are intended as local snapshots. Regenerate them with
`aiwiki-toolkit refresh-metrics` whenever you need a fresh local view.
