---
title: "Work ledger needs per-engineer identity and owner scoping"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "feature_clarification"
status: "draft"
created_at: "2026-04-27T19:12:16+1000"
updated_at: "2026-04-27T20:19:57+1000"
promotion_candidate: false
promotion_basis: "None yet. This is a product clarification for the next work-ledger iteration."
---
# Review Draft

## Context

The work ledger MVP records append-only work events and route can surface matching work context. For team use, this is under-scoped: one engineer's task should not automatically appear as actionable context for another engineer's agent session.

## Product Clarification

The work ledger needs two separate concepts:

1. session actor: the engineer currently using the agent in this repo clone
2. work owner or assignee: the engineer responsible for a task or epic

`author_handle` is not enough because the person who records an event may not be the person who should do the work.

## Desired Direction

Installation should create a local, gitignored identity file derived from git config when possible. Route and work commands should resolve the current actor from explicit CLI input, environment, local identity, then git config.

Work items should include ownership fields such as owner or assignee handles, requester, visibility, and routing scope. By default, route should surface a work item as actionable only when it is owned by the current actor, assigned to the current actor, unassigned and explicitly requested for triage, or directly mentioned by the user.

Team-visible work can still exist, but route should mark other people's work as informational or excluded rather than letting another engineer's agent start acting on it.

## Safety Requirement

Local identity data should stay out of shared git history. Shared work events should use stable handles, not private email addresses, unless the user explicitly opts into richer profile data.

## Path Refinement

The user prefers keeping local identity under the AI wiki tree instead of a separate repo-root `.aiwiki/` folder. A reasonable shape is a gitignored local runtime path under `ai-wiki/_toolkit/`, such as `ai-wiki/_toolkit/local/identity.json`.

This needs a clear boundary:

- `_toolkit/local/` is local runtime state, not package-managed source guidance.
- The package may create it if missing, but must not overwrite it on install.
- `.gitignore` should ignore only the local runtime path, not all of `ai-wiki/_toolkit/`, because tracked schema and managed docs still live there.
- Work events should default `author_handle`, `reporter_handle`, and `assignee_handles` from the resolved local identity.

## Implemented Follow-Up

PR #53 implemented the repo-local identity direction:

- installer creates `.env.aiwiki` with an aiwiki-toolkit managed block
- `.gitignore` ignores `.env.aiwiki`
- handle resolution uses explicit CLI input, environment, `.env.aiwiki`, git config, then fallback
- route packets include the resolved actor handle
- work capture defaults author, reporter, and assignee to the current actor
- work capture/status support explicit reporter and assignee overrides

## Task Placement Decision

Do not make `ai-wiki/people/<handle>/` the canonical task store. Keep canonical work state under `ai-wiki/work/events/` and link tasks to people with structured handles such as `reporter_handle`, `assignee_handles`, and future owner fields.

Reasons:

- reassignment should be an append-only status or ownership event, not a file move between people folders
- shared or paired work can have multiple assignees and does not fit one person's folder
- reporter, author, assignee, and owner are distinct concepts
- `people/<handle>/` should stay focused on person-local drafts, preferences, and working memory
- generated per-person task views can live under `_toolkit/work/` without making personal folders merge-heavy

The user-facing `ai-wiki/work/index.md` should explain how work links to people. The product surface should later add per-person generated views such as "my work", "reported by me", and "team backlog" derived from the central ledger and current `.env.aiwiki` actor.

## Implemented Owner-Scoped Views

PR #54 implemented the first owner-scoped work surface:

- `aiwiki-toolkit work mine` shows open tasks assigned to the current local actor
- `aiwiki-toolkit work list --assignee <handle>` and `--reporter <handle>` expose explicit team filters
- `ai-wiki/_toolkit/work/by-assignee/<handle>.md` and `by-reporter/<handle>.md` are generated from the central ledger
- route packets include `work_context.actor_handle` and per-item `actor_relation`
- route treats current-actor assignee work as actionable by default
- work assigned to another handle is excluded unless the user's task directly matches that work

The next design gap is ownership-change history: `status_changed` events can currently replace assignees, but there is not yet a dedicated `assignees_changed` or `ownership_changed` event type.
