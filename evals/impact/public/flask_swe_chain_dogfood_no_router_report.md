# Dogfood Without Router on the Flask SWE-Chain

_A follow-up case study on simplifying AI Wiki memory to bounded reuse plus writeback_

## Abstract

This report follows two earlier Flask SWE-Chain reports:

- [`flask_swe_chain_memory_eval_report.md`](flask_swe_chain_memory_eval_report.md)
- [`flask_swe_chain_agent_skill_writeback_report.md`](flask_swe_chain_agent_skill_writeback_report.md)

The earlier Flask memory report showed that trial-error memory could be useful, but the old
dogfood setup performed poorly. At the time, the dogfood setup had multiple layers: label memory,
route memory to the agent, and write memory back after useful public/local experience. The follow-up
agent-skill report then showed that writeback could be implemented through a runner hook and a
conversation fork, but it did not prove that the router layer was necessary.

This run tested the simpler product question directly: what happens if dogfood keeps label/reuse and
writeback, but removes the router layer? The answer, in this Flask case study, was strong. Dogfood
without router completed the full Flask `2.0.0 -> 2.3.3` SWE-Chain and matched the strongest prior
Build+fix F1 result while using main-thread writeback instead of a forked writeback session.

That changes the product interpretation of the previous runs. The evidence no longer says "we need
a router and a separate writeback session." It says the router was the risky layer, and the useful
core is much smaller:

```text
bounded memory index/read rules
+ ordinary agent retrieval
+ public/local writeback
```

This is still a single-package case study, not a universal claim about all repositories. But for
the current ai-wiki-toolkit product direction, it is enough evidence to stop prioritizing the
then-in-progress 017 toolkit-hook writeback run and focus on the simpler no-router dogfood path.

## What Changed

The older dogfood setup had three conceptual layers:

| Layer | Purpose |
| --- | --- |
| Label | Attach reusable labels or summaries to memory notes. |
| Router | Select or route memories to the coding agent before it works. |
| Writeback | Record durable public/local trial-error memory for later steps. |

The new `018 dogfood no-router` run removed the router layer. The agent still had dogfood memory
available through the repo-local AI Wiki workflow, but it relied on the memory index and its own
retrieval judgment rather than a separate route step.

It also differed from the 015 writeback experiments in an important way: writeback happened in the
main coding thread. There was no runner-managed writeback fork and no separate child conversation
whose only job was to decide whether to publish a memory note.

## Protocol

The comparable runs used the same high-level SWE-Chain setup:

- Package chain: Flask `2.0.0 -> 2.3.3`
- Agent: Codex CLI
- Provider/model: OpenAI `gpt-5.5`
- Effort: high
- `max_iters=2`
- Fresh Codex coding session per SWE-Chain transition
- Revealed feedback used for allowed repair
- Final holdout used only for analysis

The key treatment difference was memory architecture:

| Group | Memory/writeback shape |
| --- | --- |
| `015 harness trial-error` | Harness-authored trial-error memory reference. |
| `015 agent-skill writeback` | Runner normal-end hook, `codex fork`, child writeback skill, quarantine, audit, publish/skip. |
| `018 dogfood no-router` | Dogfood AI Wiki setup, no router command, main-thread memory read/writeback. |

## Main Result

| Group | Survival | Build+fix Recall | Precision | F1 | TP/FN/FP | Final holdout F1 | Holdout pass | Note |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 015 harness trial-error | 17/17 | 100.0% | 98.2% | 99.1% | 108/0/2 | 93.2% | 2434/2447 | valid reference |
| 018 dogfood no-router | 17/17 | 99.1% | 99.1% | 99.1% | 107/1/1 | 94.1% | 2439/2447 | no router, main-thread writeback |
| 015 agent-skill writeback | 17/17 | 98.2% | 99.1% | 98.6% | 106/2/1 | 92.0% | 2433/2447 | valid workflow, causal conservative |

The practical readout is:

- 018 tied the best prior Build+fix F1: `99.1%`.
- 018 had the best final-holdout pass count among these three groups: `2439/2447`.
- 018 had the best final-holdout F1 among these three groups: `94.1%`.
- 018 did this without the router layer.
- 018 did this without the 015 forked writeback session.

The small differences should not be over-read statistically. But the absence of a drop is the
important signal: removing the router did not degrade the Flask run, and the simpler dogfood setup
performed at least as well as the more complicated writeback/fork designs in this case study.

## Why The Older Dogfood Result Looked Bad

The earlier dogfood result should not be interpreted as "dogfood memory does not work." It is better
explained as a router problem.

The router layer was meant to help by selecting relevant memory. In practice, a weak route can create
a worse starting frame than no route at all. It can make the agent spend attention on plausible but
low-value context, or approach the current upgrade through the wrong prior lesson.

That is the product lesson:

```text
bad routing can be worse than no routing
```

Routing may still become useful later, but it should not be in the default path until it has its own
precision evaluation. The default should be the simpler workflow that already performed well:
bounded memory index, agent-controlled reading, and writeback from public/local signals.

## What 015 And 017 Mean Now

The 015 agent-skill run and the partial 017 toolkit-hook run answer a different question from
018.

| Experiment | Question it answers |
| --- | --- |
| 015 agent-skill writeback | Can a runner hook fork the conversation and use an agent skill to write memory safely? |
| 017 toolkit hook writeback | Can the packaged `aiwiki-toolkit writeback setup` hook/runtime exercise that product plumbing? |
| 018 dogfood no-router | Does dogfood still work well if the router is removed and the main thread reads/writes memory? |

015 and 017 are both hook/fork-shaped writeback experiments. They are useful for validating
writeback infrastructure, but they are not necessary to explain the strong 018 product result.

The current product conclusion is not that forked writeback is bad. It is that forked writeback is
extra machinery. If main-thread dogfood writeback without router reaches the same performance band,
then the simpler path should be the next default candidate.

That is why stopping the 017 run is reasonable. It may still be useful later as a packaging or host
lifecycle test, but it is no longer the highest-value experiment for deciding whether dogfood needs
the router layer.

## Evidence For "No Router"

The 018 run recorded direct no-router evidence:

- the live log contained `1710` parsed command executions;
- there were `0` actual `aiwiki-toolkit route` command executions;
- the phrase `aiwiki-toolkit route` appeared only in instructions or status text, not as an executed
  command;
- reuse telemetry used `aiwiki-toolkit record-reuse` and `record-reuse-check`, which are accounting
  commands rather than router commands.

The 018 run also recorded direct main-thread writeback evidence:

- the treatment did not use the 015 runner hook;
- memory changes happened inside the same build/fix turns;
- the host app ended with 10 memory notes plus an index under `ai-wiki/memory/`;
- file-change events touched those memory notes and `index.md` during the chain.

## Product Direction

The best current default candidate is smaller than the old dogfood stack:

```text
AI Wiki enabled in the repo
-> agent reads bounded memory index when relevant
-> agent chooses what to inspect
-> agent performs the task
-> agent writes back only durable public/local lessons
```

The layers to keep:

1. repo-local, reviewable memory files;
2. a bounded memory index with strict read rules;
3. public/local-only writeback rules;
4. reuse telemetry for measurement;
5. a lightweight writeback check at task end.

The layers to defer:

1. router/read-selection as a default path;
2. forked writeback as required product behavior;
3. multi-layer label/router/writeback orchestration before the simpler path is exhausted.

## Limitations

This report should be read as an artifact-backed case study, not a broad benchmark result.

- It is one package chain: Flask `2.0.0 -> 2.3.3`.
- It is one model/agent setup: Codex CLI, OpenAI `gpt-5.5`, high effort.
- The groups were run in a complex local harness, so protocol verification matters.
- Final-holdout scores are useful analysis signals but not direct training signals.
- Router quality may depend on repository size, memory volume, and task ambiguity.

The conservative claim is still strong enough: for this Flask chain, no-router dogfood with
main-thread writeback was not worse than the more complex alternatives. That makes it the better
next product baseline.

## References

- [Evaluating Agent Memory on the Flask SWE-Chain](flask_swe_chain_memory_eval_report.md)
- [Agent-Skill Writeback on the Flask SWE-Chain](flask_swe_chain_agent_skill_writeback_report.md)
- [AI Wiki Impact Eval Pilot](ai_wiki_impact_eval_pilot.md)
- [SWE-Chain paper](https://arxiv.org/html/2605.14415v1)
- [SWE-Chain GitHub repository](https://github.com/CUHK-ARISE/SWE-Chain)
- [SWE-Chain Hugging Face dataset](https://huggingface.co/datasets/For-Anonymous-Submission-90/SWE-Chain)
