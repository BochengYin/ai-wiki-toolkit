---
title: "Recommendation lists should rank options by impact and name the best first"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "review"
status: "draft"
created_at: "2026-04-19T10:32:45+1000"
updated_at: "2026-04-19T10:32:45+1000"
promotion_candidate: false
promotion_basis: "none"
---
# Review Draft

## Context

We discussed ways to reduce npm installation time for a thin wrapper package around release binaries.

Multiple valid options existed, including better install logs, using system tools, local caching, shrinking the binary, and switching to platform-specific packages.

The response proposed several methods, but it did not immediately make the ranking explicit or clearly identify the highest-leverage option first.

## What Went Wrong

The advice enumerated possibilities before establishing decision priority.

That increased the user's evaluation burden and delayed the key conclusion: removing the second-stage `postinstall` download through platform-specific packages is materially more effective than polishing the current wrapper path.

## Bad Example

- Present five possible optimizations in roughly equal framing.
- Leave the strongest option implicit until later follow-up.
- Force the user to infer which recommendation is tactical and which is strategic.

## Fix

When proposing multiple improvements, rank them by expected impact and implementation cost, then state the recommended first move explicitly.

For performance-oriented advice, lead with the highest-leverage architectural change before mentioning lower-yield local optimizations.

## Reuse Assessment

This pattern is reusable for agent recommendations, technical tradeoff discussions, and performance triage.

Any answer that offers a menu of options without a visible ordering can feel less decisive than it should, even when the individual suggestions are correct.

## Promotion Decision

Keep as a draft for now. Promote if the same issue appears again in another recommendation-heavy task or review conversation.
