---
title: "Efficiency eval should include source incident cost"
author_handle: "bochengyin"
model: "gpt-5.5"
source_kind: "task"
status: "draft"
created_at: "2026-04-26T11:29:00+1000"
updated_at: "2026-04-26T18:49:15+1000"
promotion_candidate: false
promotion_basis: "none"
---
# Draft

## Context

When evaluating AI wiki efficiency, formal replay comparisons between `no_aiwiki_workflow` and `aiwiki_ambient_memory_workflow` are not enough on their own.

The useful memory often came from an earlier real incident where an agent made mistakes, went through debugging or reviewer/user correction, and eventually produced the fix that became durable AI wiki knowledge.

## Rule

Efficiency reports should include a third dimension:

- source incident / knowledge acquisition cost
- formal no-AI-wiki replay cost and outcome
- formal ambient-AI-wiki replay cost and outcome

The source incident cost should be derived from the original session artifact when available. Prefer selected Codex `task_complete.duration_ms` values when the goal is active-turn cost, and include `turn_aborted.duration_ms` when an interrupted failed attempt is part of the actual incident. Label the result as a `source active-turn estimate`.

Do not present source active-turn cost as exact human time saved. It excludes waiting time between user turns, but includes tool, CI, release, and package wait that happened inside selected agent turns.

Do not present source active-turn cost as the no-AI-wiki baseline. It is a memory acquisition or correction-cost context column. Real source incidents can include scope discovery, human correction, release feedback, interrupted turns, and post-fix rescue work that are not identical to a clean formal replay.

When formal replays use fresh sessions, report the visible initialization window separately. A practical artifact-derived proxy is the time from `session_meta` to the first visible assistant message. This is not pure model startup because it can include initial task planning, but it helps show whether fresh-session overhead is large enough to affect the comparison.

## Why

This avoids claiming vague token savings. It frames AI wiki value as amortizing real discovery and rework cost across later independent sessions.

The conservative claim is not "AI wiki saved exactly N minutes." The better claim is:

- the original lesson had an observed acquisition cost
- the formal replay shows whether later agents avoided the same failure mode
- net efficiency depends on whether avoided follow-up/rework exceeds the AI wiki lookup and workflow overhead

When reporting a saved-time number, use the public label `estimated saved active mins using ambient
AI wiki`: `source incident active-turn estimate - ambient AI wiki replay duration`. Positive values
mean the AI wiki replay used less active agent time than the original incident. Negative values
should be reported plainly as no active-time saving, even when correctness improved.

Do not compute saved time as `no_aiwiki_workflow replay duration - aiwiki_ambient_memory_workflow
replay duration`. That comparison belongs to the formal outcome control. The efficiency comparison
is between the original source incident cost and the later ambient AI wiki replay.

If extrapolating from a small repo to a larger team repo, label the result as a Fermi extrapolation.
State the repo size, active-project-hour assumption, per-family future frequency assumptions, team
size, saved-minutes-per-active-hour calculation, and scaling multiplier. Keep the frequency table and
derived totals on one time base, such as weekly, rather than mixing monthly and weekly units in the
same explanation. Set one-off families to zero in recurring estimates rather than counting every
measured benchmark family as recurring. Say plainly that savings depend on project-specific recurring
failure modes, release cadence, automation, and whether the relevant lessons have already been
captured in repo memory. Do not present the extrapolated number as measured productivity until the
same method has been run on a real medium or large repo.

## Reporting Pattern

For each case study, report:

- source incident duration and failure mode
- whether the source number is full fail-plus-fix, correction-only, or includes release/rescue follow-up
- whether interrupted failed turns were counted separately from completed correction turns
- memory produced from that incident
- no-AI-wiki replay duration and score
- ambient-AI-wiki replay duration and score
- observed AI wiki overhead
- estimated saved active mins using ambient AI wiki
- avoided follow-up or rework class
- conservative break-even interpretation
- replay initialization-window check when comparing already-initialized source sessions against fresh replay sessions
- any Fermi extrapolation assumptions, including per-family frequency, if a team-level estimate is included
