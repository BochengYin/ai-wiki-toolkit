---
title: "AI wiki footer should use user-facing evidence language"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "product-feedback"
status: "draft"
created_at: "2026-04-25T20:25:00+1000"
updated_at: "2026-04-25T20:55:00+1000"
promotion_candidate: false
promotion_basis: "none"
---
# Review Draft

## Context

While discussing the AI wiki evidence workflow, the user pointed out that the current footer labels are not clear enough for normal product use.

Examples that felt too internal:

- `AI Wiki Eligibility: eligible`
- `AI Wiki Material Effects: avoided_retry`
- `AI Wiki Update Candidate: None`

## What Went Wrong

The footer currently exposes implementation and metrics language. It is useful for agents and evals, but it is not immediately obvious to a user what the lines mean.

In particular, `Update Candidate` sounds like a package update or generic status. The actual meaning is whether the completed task produced durable knowledge that should be written back into the AI wiki.

## Better Direction

Use user-facing labels that explain the workflow directly:

- `AI Wiki Task Relevance` instead of `AI Wiki Eligibility`
- `AI Wiki Impact` instead of `AI Wiki Material Effects`
- `AI Wiki Write-Back` instead of `AI Wiki Update Candidate`

The underlying skill or command may still be named `ai-wiki-update-check` for compatibility, but the visible footer should make the write-back purpose clear.

## Implementation Note

The footer language was updated to use:

- `AI Wiki Task Relevance`
- `AI Wiki Impact`
- `AI Wiki Write-Back`
- `AI Wiki Write-Back Path`

The existing skill name `ai-wiki-update-check` and telemetry commands remain compatible.

The installer now refreshes package-owned `.agents/skills/ai-wiki-*` files directly, so existing repos receive the revised footer contracts after upgrading the package and rerunning `aiwiki-toolkit install`.

## Reuse Assessment

This is reusable product feedback for the AI wiki evidence workflow. It should guide future revisions to the footer output contract, README examples, managed prompt text, and eval scoring language.

## Promotion Decision

Keep as a draft until the revised footer wording is validated in real tasks.
