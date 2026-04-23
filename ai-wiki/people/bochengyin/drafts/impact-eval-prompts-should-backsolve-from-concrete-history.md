---
title: "Impact eval prompts should backsolve from concrete history"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "review"
status: "draft"
created_at: "2026-04-22T20:40:00+1000"
updated_at: "2026-04-22T20:40:00+1000"
promotion_candidate: false
promotion_basis: "none"
---
# Review Draft

## Context

We started designing manual impact-eval prompts for `ai-wiki-toolkit` and initially framed the
benchmark around abstract ownership and prompt-boundary rules.

That produced prompts that were technically related to the repo, but they did not feel like real
historical work. The better benchmark shape emerged only after we traced the task back to a
concrete repeated issue: contributor-only PR flow behavior could easily have been implemented as a
distributed package feature under `src/ai_wiki_toolkit/` even though it really belonged in
repo-local surfaces such as `scripts/pr_flow.py` and `ai-wiki/workflows.md`.

## What Went Wrong

The first benchmark prompts started from the rule we wanted to test instead of the concrete task
that had actually gone wrong before.

That made the prompts sound like wiki-maintenance homework rather than realistic implementation
work. It also made it harder to tell whether the experiment was measuring:

- memory usefulness
- prompt specificity
- or simply how well the agent could restate an abstract policy

We also let the experiment baseline and prompt leak too much of the intended answer.

The first run still contained the already-built `scripts/pr_flow.py` helper and its dedicated test
file, and the prompt explicitly said "extend the existing repo-local PR flow". That meant the
benchmark could no longer tell whether AI wiki memory helped the agent choose the correct surface.
The repo and prompt had already chosen it.

## Bad Example

- Ask the agent to "refine ownership guidance" without naming the concrete repo task.
- Use a benchmark prompt that only restates an already abstract rule.
- Change both the task itself and the prompt detail level at the same time.
- Measure consolidate value using a task that never clearly existed as a real repeated mistake.
- Build all variants from a baseline that already contains the target implementation surface.
- Name the intended surface directly in the prompt when the benchmark is supposed to test surface choice.

## Fix

Backsolve each impact-eval task from a real repeated history item in the repo:

1. identify a concrete failure or near-miss from drafts, trails, review patterns, or problems
2. phrase the benchmark as the actual implementation or update task an agent would have faced
3. make sure the repo baseline does not already contain the target implementation surface when the
   benchmark is supposed to test surface selection
4. vary only:
   - memory state
   - prompt specificity
5. do not directly name the intended surface in the prompt unless the benchmark is explicitly
   about behavior inside that already-known surface
6. keep the prompt ladder narrow:
   - `short`: core task requirements only
   - `medium`: the same task requirements plus one scope or boundary sentence
   - retire `full` when it mostly feeds the intended answer instead of measuring what memory adds
7. when the benchmark is testing surface choice, it is often fine to say "helper", "script", or
   another behavior-shaped noun, but avoid naming the favored placement such as `repo-local` or a
   specific directory; the point is to test whether memory keeps the agent out of the wrong
   package surface without directly telling it where to land

For this repo, "add or extend a repo-local PR flow helper without turning it into a package
feature" is a stronger benchmark than "refine ownership guidance" because it is concrete, has a
real wrong path under `src/ai_wiki_toolkit/`, and still exercises the same memory boundary.

## Reuse Assessment

This should generalize to other manual benchmark design work for repo-native agent systems.

If the benchmark task is not obviously something that could have happened in the repo's actual
history, it is probably too abstract to measure whether drafts or consolidated memory reduce real
mistakes.

If every variant already contains the target code surface, or the prompt directly names that
surface, the benchmark will mostly measure cleanup style and extra churn rather than actual memory
help with implementation choice.

If the strongest benchmark signal is "can AI wiki memory reduce how much prompt text we need",
two prompt levels are often enough. A `full` prompt can quickly collapse into answer leakage and
stop measuring the effect of drafts or consolidated memory.

## Promotion Decision

Keep as a draft for now. Promote if the same "backsolve from concrete history" rule proves useful
in another benchmark family besides ownership and prompt-boundary tasks.
