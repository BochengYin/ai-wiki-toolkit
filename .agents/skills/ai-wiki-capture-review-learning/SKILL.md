---
name: ai-wiki-capture-review-learning
description: Use when the user provides PR review feedback, code review comments, or reviewer preferences that may be reusable.
---

# AI Wiki Capture PR Review Learning

Use this skill when the user provides PR review feedback, code review comments, or reviewer preferences that may be reusable.

The goal is not to save every comment. The goal is to preserve feedback that can help future agents avoid repeated review issues.

## Workflow

1. Read the review comment.
2. Identify reviewer, reviewer role, and scope if available.
3. Classify the feedback.
4. Decide whether it is reusable.
5. Check existing AI wiki memory for related conventions, review patterns, decisions, problems, and person preferences.
6. Propose the smallest useful wiki update.
7. If the feedback conflicts with existing memory, flag the conflict instead of silently overwriting.
8. Prefer draft or person preference first unless promotion criteria are met.

## Important Rules

- A single review comment should not automatically become a team convention.
- If the reviewer is an owner or tech lead for that area, it may be a stronger convention candidate.
- If the same feedback appears repeatedly, suggest promotion.
- If it refines an existing convention, update the convention with history.
- If it only applies to the current code, mark it as one-off and do not store.
