---
title: "Shared AI wiki prompt blocks need one-shot local gates"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "design"
status: "draft"
created_at: "2026-05-08T18:12:00+10:00"
updated_at: "2026-05-17T23:03:19+1000"
promotion_candidate: true
promotion_basis: "Auto-marked from useful resolved reuse threshold; exact evidence is generated under ai-wiki/_toolkit/reports/promotion-candidates/latest.md."
promotion_report: "ai-wiki/_toolkit/reports/promotion-candidates/latest.md"
---
# Review Draft

## Context

During a company pilot, `ai-wiki/` may be intentionally gitignored and present only in one developer's checkout, while a repo-shared `CLAUDE.md` still needs enough instruction for agents in that checkout to activate the AI wiki workflow.

The first attempted fix was to make the shared prompt louder with "MANDATORY" and "EVERY task" language. That improves adherence for the pilot user, but it creates a bad default for teammates who do not have a local AI wiki: their agents may repeatedly probe or invoke unavailable workflow commands.

## Design Rule

Repo-shared prompt blocks should not inline the heavy AI wiki workflow when the AI wiki is local opt-in. They should implement a mandatory, cheap, one-shot local capability gate:

1. Run exactly one local filesystem probe per agent session or repository checkout.
2. Treat `ai-wiki/_toolkit/system.md` as the activation file, even when `ai-wiki/` is gitignored.
3. If the activation file exists, read it and follow the full start-of-task and end-of-task workflow from there.
4. If the activation file is absent, cache AI wiki as disabled for the session and do not run `aiwiki-toolkit`, search `ai-wiki/**`, complain about missing setup, or re-probe on every task.
5. Re-check only when the working directory changes, the user says AI wiki was installed, or a command in the session created `ai-wiki/_toolkit/system.md`.

## Implication

The shared prompt should frame the check as a required branch, not as an optional "if you feel like it" instruction. Conditional language is still appropriate, but the condition must be explicit, bounded, and resource-safe.

The full workflow remains package-managed in `ai-wiki/_toolkit/system.md`. The shared prompt remains user-agnostic and lightweight, which preserves multi-user collaboration while allowing a local pilot to get reliable agent behavior.

## Implementation Evidence

Implemented in `ai-wiki-toolkit` 0.1.29 via PR #64. The managed prompt block now uses `## AI Wiki Local Workflow Gate`, requires one filesystem check for `ai-wiki/_toolkit/system.md`, activates the full workflow only when that file exists, and caches the disabled state when it does not.

## Wording Refinement

The local-gate prompt should be explicit that the availability check blocks the first response in a new session. The stronger wording can use bold Markdown and uppercase terms such as `CRITICAL`, `MUST`, and `BLOCKING REQUIREMENT`, but should avoid emoji so the managed block stays plain-text friendly across company prompt files.

When adding the managed block to a prompt file that does not already have one, prefer placing it after the top H1 and introductory paragraph so it appears before command and coding instructions. Existing managed blocks can still be replaced in place to avoid unexpectedly moving user-owned prompt content.

## Release Evidence

Released in `ai-wiki-toolkit` 0.1.30 via PR #65. This release added the no-emoji blocking wording, prompt-file insertion near the top of new prompt files, and matching doctor/tests coverage.
