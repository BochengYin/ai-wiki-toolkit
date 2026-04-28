---
title: "Consolidation queue conflict signals should avoid broad keyword matches"
author_handle: "bochengyin"
model: "unknown"
source_kind: "problem_solution"
status: "draft"
created_at: "2026-04-29T00:35:00+10:00"
updated_at: "2026-04-29T00:35:00+10:00"
promotion_candidate: false
promotion_basis: "none"
---
# Draft

## Context

While implementing `aiwiki-toolkit consolidate queue`, the first conflict heuristic treated any draft body containing `conflict` as a Conflict queue item.

## Problem

Broad keyword matching made the generated queue noisy. Drafts that mentioned avoiding merge conflicts or described conflict handling generically were incorrectly surfaced as `Conflict`.

## Fix

Use narrower conflict patterns such as `conflicts with`, `conflicting guidance`, `contradicts`, or `inconsistent with`, and continue to treat diagnostics conflict notes as stronger evidence.

## Reuse Assessment

Use this when adding AI wiki diagnostics or governance heuristics. Generated review queues should prefer precise weak signals over broad body keyword matches.
