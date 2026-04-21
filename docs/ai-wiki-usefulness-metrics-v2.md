# AI Wiki Usefulness Metrics v2

This document records the next metrics direction for `ai-wiki-toolkit`.

The goal is not to reward agents for touching wiki files. The goal is to measure whether the agent:

- used AI wiki memory when it should have
- stayed out of the way when AI wiki was not needed
- changed behavior materially when useful memory existed
- exposed missed relevant memory when a useful doc existed but was not picked

Do not treat this as a request to build a benchmark runner yet.

## First Classify Task Eligibility

Before interpreting any coverage or reuse metric, classify the task:

- `not_applicable`
  Pure operational work such as pushing a PR, renaming a branch, running `git status`, or rerunning an already-decided command.

- `optional`
  Low-risk work where repo memory may help, but the task can often complete correctly without it.

- `eligible`
  Coding, debugging, release, review, clarification, or conflict-heavy work where existing team memory could materially change the plan.

Simple operational tasks should not be forced to read AI wiki just to improve coverage scores.

## Layer 1: Workflow Coverage

These metrics answer whether the agent routed tasks correctly.

- `task_check_coverage`
  Tasks with an explicit AI wiki footer or task-level evidence record divided by total tasks.

- `wiki_touch_rate`
  Eligible tasks that consulted at least one user-owned AI wiki doc divided by eligible tasks.

Raw `wiki_touch_rate` across all tasks is misleading because it punishes `not_applicable` operational work.

## Layer 2: Material Reuse

These metrics answer whether AI wiki changed agent behavior, not just whether a doc was listed.

- `material_reuse_given_wiki_use`
  Tasks with material reuse divided by eligible tasks that used at least one user-owned AI wiki doc.

- `material_reuse_per_eligible_task`
  Tasks with material reuse divided by eligible tasks.

- `material_reuse_rate`
  Use this only when the denominator is stated explicitly. Do not report it without saying whether the denominator is `eligible_tasks` or `wiki_used_eligible_tasks`.

- `avoided_retry_count`
  Count tasks where AI wiki prevented a repeated failed attempt.

- `blocked_wrong_path_count`
  Count tasks where AI wiki prevented an incorrect implementation or release path.

- `plan_changed_by_wiki_count`
  Count tasks where AI wiki materially changed the plan.

Material reuse should require at least one concrete effect such as:

- `changed_plan`
- `avoided_retry`
- `blocked_wrong_path`
- `resolved_conflict`
- `reused_convention`
- `captured_durable_memory`

Listing used docs is not enough to prove usefulness.

## Layer 3: Miss Metrics

These metrics answer the most valuable negative question:

Why did the agent fail to pick relevant memory that already existed?

- `missed_relevant_memory_count`
  Count known incidents where a relevant user-owned AI wiki doc existed but the agent failed to use it in time.

- `missed_relevant_memory_rate`
  Only use this when the denominator is `reviewed_eligible_tasks`, not all tasks.

- `repeated_issue_after_memory_exists_count`
  Count tasks that repeated a known issue even though the relevant memory already existed.

In practice, start with incidents before chasing a strict rate, because many misses are never discovered.

## Incident Shape

Start with manual or draft-backed incidents before adding a dedicated CLI.

Suggested fields:

- `task_id`
- `task_kind`
- `missed_doc`
- `expected_use`
- `discovered_by`
- `impact`
- `fix`

Recommended `discovered_by` values:

- `user`
- `pr_review`
- `test_failure`
- `agent_self_review`

Recommended `impact` values:

- `extra_iteration`
- `wrong_plan`
- `repeated_error`
- `missed_update`

## Evidence Rules

- User-owned AI wiki docs are the knowledge-reuse evidence surface.
- Managed `_toolkit/**` docs are workflow controls, not knowledge-reuse evidence.
- The end-of-task AI wiki footer is the user-facing evidence surface.
- Local telemetry under `ai-wiki/metrics/` is the machine-readable record behind that footer.

## Practical Reading

If `material_reuse_given_wiki_use` is high but `wiki_touch_rate` is low, the wiki is useful when reached, but routing is missing relevant docs too often.

If `wiki_touch_rate` is high but material reuse is low, the agent is reading too much wiki without changing behavior.

If missed-memory incidents stay common, prioritize retrieval and routing before adding more notes.
