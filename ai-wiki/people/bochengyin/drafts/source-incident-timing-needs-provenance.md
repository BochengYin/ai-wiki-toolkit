---
title: "Source incident timing needs provenance"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "feature_clarification"
status: "draft"
created_at: "2026-05-24T00:00:00+1000"
updated_at: "2026-05-24T21:05:00+1000"
promotion_candidate: false
promotion_basis: "single implementation signal"
---
# Draft

## Context

While adding source incident trial/error timing to impact-eval discovery, the local telemetry could
identify replay candidates and trial/error effects, but the existing historical events mostly lacked
`source_session_id` or structured `source_incident` timing payloads.

## Lesson

Do not infer original trial/error active time from a replay candidate unless the event has explicit
source incident provenance.

Reliable evidence should be recorded as one of:

- `source_incident.active_seconds` from a manual or external estimate
- `source_incident` derived from a known Codex `source_session_id`
- a later explicit backfill event that states what the timing includes

When provenance is missing, reports should say `not_recorded` instead of estimating from task slugs,
observation spans, or later reuse timings.

Historical Codex backfill should write a new append-only ledger instead of mutating old
`reuse-events` rows. The first source incident backfill ledger is:

```text
ai-wiki/metrics/source-incidents/<handle>.jsonl
```

For write-back-footer backfill, the default timing policy should be
`first_writeback_user_task_inclusive`: find the first `AI Wiki Write-Back Path:` footer for a memory
in a session whose `cwd` matches the repo, then count active `task_complete.duration_ms` plus timed
`turn_aborted.duration_ms` rows from the current user task start through that first write-back turn.

Do not sum the whole Codex JSONL before the footer. Codex threads can be reused across many unrelated
tasks and even multiple days; summing all earlier `task_complete` rows can overstate a small source
incident by hours.

Prompt-level write-back skills should not claim current-turn source incident duration, because the
current `task_complete.duration_ms` row is written after the final assistant message lands. Use a
post-turn runner or wrapper to capture it after the session artifact is flushed:

```bash
aiwiki-toolkit source-incident capture-post-turn --apply
```

That command should inspect the latest completed write-back turn for the current repo, write the
same append-only `source-incidents/<handle>.jsonl` ledger, and report `skipped_existing` when the
same `(doc_id, session_id, policy)` evidence was already captured.

## Reuse Assessment

Use this when extending eval discovery, diagnostics, or usefulness reports that compare source
incident cost against later AI-wiki-assisted replays.
