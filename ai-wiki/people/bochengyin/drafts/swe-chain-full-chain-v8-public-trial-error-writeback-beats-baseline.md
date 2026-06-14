---
title: "SWE-Chain full-chain v8 public trial-error writeback beats baseline"
author_handle: "bochengyin"
model: "gpt-5.5"
source_kind: "evaluation_result"
status: "draft"
created_at: "2026-06-11T17:27:38+1000"
updated_at: "2026-06-11T17:27:38+1000"
promotion_candidate: false
promotion_basis: "single full-chain Flask result; needs repeat on another chain or rerun before shared promotion"
---
# Draft

## Context

In the Flask SWE-Chain full-chain eval, the accepted treatment compared against the `/init` baseline
using the same agent, model, chain, and `max_iters=2` setup.

The valid treatment setup was:

- run with `/init`-style `AGENTS.md` for both baseline and treatment
- no task-time network install of `aiwiki-toolkit`
- no router layer in the task prompt
- public-only trial-error writeback enabled
- write memory only after meaningful public trial/error signals
- read `ai-wiki/memory/index.md` each step, but open at most one linked memory file only when it
  matches the same source file, API, command, behavior, or repeated public failure
- keep AI Wiki scaffold at `/app`, outside `/app/code`, so Flask diffs are not contaminated
- do not write hidden evaluator failures, hidden test names, or prior invalid hidden-derived fixes
  into future memory

## Result

On Flask `2.0.0 -> 2.3.3`, v8 beat baseline:

- build F1: `0.4609 -> 0.7752`
- build+fix F1: `0.5024 -> 0.7879`
- final TP: `53 -> 104`
- final FN: `99 -> 48`
- final hidden passed: `7666 -> 7766`
- final hidden failed: `489 -> 385`

The chain survived all 17 transitions. `chain.json` did not contain `ai-wiki`, `AGENTS.md`,
`AGENT.md`, or `_toolkit`, which kept scaffold out of the evaluated Flask diff.

## Lesson

The useful component setup was not broad memory injection. It was a constrained memory loop:
`/init` gives stable project workflow context, public trial-error writeback records only observed
local/public failure surfaces, and bounded reads keep the next step from overfitting to stale or
unrelated prior work.

The failed earlier shapes are part of the lesson:

- hidden-derived memory is invalid because it leaks evaluator information
- noisy writeback can drag later steps down
- reading many memory files behaves like prompt overhead rather than useful memory

## Reuse Assessment

Use this when designing the next SWE-Chain A/B run or when changing `ai-wiki-toolkit` writeback
components. The next confirmation should repeat this component setup on another chain or rerun Flask
before promoting it into shared AI Wiki conventions.
