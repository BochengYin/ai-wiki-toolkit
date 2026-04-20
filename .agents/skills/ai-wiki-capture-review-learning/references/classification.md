# PR Review Learning Classification

## One-Off Fix

Applies only to the current diff.

Example:
"Rename this variable to match the API response."

## Person Preference

Reflects a reviewer's preference but is not yet a team-wide rule.

Example:
"Carol prefers precise Python type hints and dislikes casual `object`."

## Team Convention Candidate

A reusable rule that may apply broadly.

Example:
"Prefer `str | None` over `object` when the possible return values are known."

## Review Pattern Candidate

A repeated review issue.

Example:
"Do not update generated prompt blocks manually."

## Decision Candidate

A durable tradeoff or product or architecture choice.

Example:
"We will make imports partial-success instead of all-or-nothing."

## Problem-Solution Memory

A reusable debugging or implementation lesson.

Example:
"Async notification tests are flaky unless using the fake queue."

## Not Reusable

Too local, obvious, or unlikely to help future tasks.
