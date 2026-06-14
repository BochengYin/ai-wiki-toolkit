# Evaluating Agent Memory on the Flask SWE-Chain

_A production-simulation case study for trial-error and recurring memory_

## Abstract

This report is a public research note, internal experiment log, and benchmark-methodology note. It
explains why I moved from an ai-wiki-toolkit project-history pilot eval to a Flask SWE-Chain
experiment, what failed along the way, and what the final production-simulation run suggests about
agent memory.

I care less here about whether `gpt-5.5` can solve individual Flask upgrade tasks in isolation. The
thing I wanted to understand is whether repo-local memory helps fresh agents move through a
multi-step chain, and which memory horizon actually helps.

The strongest result from the final Flask run is directional: `init + trial-error memory` was the
best next default candidate under this protocol. It achieved the highest final holdout F1
(`0.9647`) and zero final-holdout false positives. Recurring-only memory looked noisy and unstable,
and the older dogfood router-style workflow is not ready to be a default candidate without its own
precision evaluation.

Statistically, this is still a case study: one artifact-backed Flask SWE-Chain
production-simulation run, interpreted alongside earlier pilot and exploratory runs.

## What I Mean By Memory

In this report, memory means repo-local, reviewable context that survives across fresh agent
sessions. The boundary matters: I am talking about files a future agent can inspect and a human can
audit, rather than model hidden state, one long chat thread, or global personal memory.

For the Flask experiment, memory was implemented as Markdown files under `/app/ai-wiki/memory/`,
linked from `/app/ai-wiki/memory/index.md`, and read by fresh agents at later steps.

Each SWE-Chain step reset the Codex session. Ordinary conversational context did not carry across
steps. What carried across steps was only repo-local memory: the `/init`-style `AGENTS.md`
orientation and, for treatment groups, `/app/ai-wiki/memory/`.

That is the point of the setup. I wanted to test durable repo memory across independent fresh
agents, instead of accidentally measuring the continuity of one long conversation.

## Prior Evidence: The AI Wiki Impact Pilot

Before the SWE-Chain work, ai-wiki-toolkit already had a pilot impact eval:
[`ai_wiki_impact_eval_pilot.md`](ai_wiki_impact_eval_pilot.md).

That pilot replayed five historical problems from developing ai-wiki-toolkit itself. It compared a
no-AI-wiki workflow against an ambient AI Wiki workflow, using fresh Codex CLI sessions, the same
model, and artifact-backed manual scoring. In the primary comparison, ambient AI Wiki performed
better in four of five families and tied in one.

That made the memory effect plausible. At the same time, the pilot was still tied to
ai-wiki-toolkit's own project history. The memories were naturally well matched to the repo's past
failures. Useful evidence, but too close to home to answer the broader benchmark question.

So the next step was to move from "can memory ever help?" to "what kind of memory helps in a
stricter, external, multi-step benchmark?"

## Why Flask SWE-Chain

SWE-Chain was attractive first because it is a continuous task chain. A team does not usually work
on one isolated issue and then forget the repository. A team spends weeks or months in the same repo,
accumulating context, debugging experience, compatibility lessons, and workflow discipline.

Most coding-agent benchmarks are one-off: the agent either solves one task or it does not. That is
useful for measuring raw task performance, but it is a poor fit for evaluating evolving memory.
Memory should matter most when independent fresh agents work through related steps over time.

SWE-Chain gives that shape: a package is upgraded across a sequence of version transitions, with
each step building on the code produced by earlier steps. I used the Flask full chain
(`2.0.0 -> 2.3.3`) as the first case study. The scope here is just that Flask chain.

SWE-Chain also gives an external oracle and measurable outcomes: resolving or recall, precision,
F1, false positives/regressions, chain survival, and per-step behavior. That makes it a better place
to study whether a memory design generalizes beyond a project's own historical failures.

## Memory Horizons

The experiments separate two memory horizons.

**Short-horizon task memory** captures trial-error learning from a concrete task. An agent writes
code, runs checks, hits failures, repairs them, and records the durable lesson so future agents do
not repeat the same debugging loop.

**Long-horizon recurring memory** tries to accumulate repeated signals across multiple conversations
or steps. Examples include files that repeatedly change, APIs that repeatedly appear, environment
tooling mismatches, or repeated broad feedback surfaces.

These horizons solve different problems:

| Memory horizon | Problem it tries to solve | Source | Intended use |
| --- | --- | --- | --- |
| Trial-error memory | Learning from the current conversation should carry forward | Agent coding trajectory, local/public checks, repair attempts | Help later agents avoid the same debugging loop |
| Recurring learning | Repeated patterns across sessions should accumulate | Multiple conversations or steps | Promote repeated signals into more durable project memory |

The final run suggests trial-error memory is already useful under this protocol. Recurring learning
is still promising, but its candidate generation and read footprint need better filtering before it
should be treated as a default.

## Early Flask Experiments

The first Flask experiments were exploratory. They compared raw no-init behavior, init-only,
trial-error/v8-style memory, and older dogfood setups.

One early result was immediately important: `/init` is a big deal. It gives the agent a chance to
read the repo and write down a working understanding of it. That is different from AI Wiki memory,
but it still behaves like orientation memory.

In an early Flask full-chain run:

| Early setup | Build+fix F1 | Recall | Precision | Interpretation |
| --- | ---: | ---: | ---: | --- |
| raw baseline, no init | 0.7674 | 0.6513 | 0.9340 | Original no-orientation baseline |
| init-only | 0.7909 | 0.6842 | 0.9369 | `/init` itself improves repo understanding |

After this, "memory vs nothing" stopped being the useful comparison. The better baseline became an
initialized agent, and the real question became which memory horizon improves over that.

The early dogfood runs exposed a second issue. The old dogfood workflow had accumulated several
layers: memory labels, taxonomy or doc-slot selection, router/read-selection, and writeback/reuse
metrics. That made sense as a proof of concept, but in SWE-Chain it behaved like an unreliable
attention-control layer.

The worse part was the framing. Sometimes the agent still opened plenty of files, but the router
handed it a plausible-looking, weakly relevant first frame for the task. That changed how the agent
read the upgrade spec and where it spent attention.

**Bad routing can be worse than no routing because it adds confident noise.**

To me, the lesson is less "routing can never work" and more "routing has to earn trust on precision
before it comes back as a default memory layer."

## Correcting The Experiment Design

The later runs were as much about fixing the evaluation protocol as about comparing memory
treatments.

Several things had to be made explicit:

- AI Wiki scaffold had to live outside the evaluated Flask package.
- `/app/AGENTS.md` could be injected, but AI Wiki files must not enter `/app/code`.
- Groups had to be independent: no memory or logs copied between groups.
- The same SWE-Chain source, Flask chain, model, effort, max iterations, container base, and scoring
  command had to be used across groups.
- The run could not copy host Codex config into containers.
- Task containers could not install aiwiki-toolkit from the network.
- Hidden or final-holdout evaluator information could not be written into memory.
- Metrics had to account for retry attempts as well as final pass/fail.

This became a methodology problem in its own right: how do we reduce human-in-the-loop review when
agents are helping run the experiment itself?

The problem sat in my experiment workflow rather than SWE-Chain itself. I used agents to help design
harness changes, run groups, inspect logs, and summarize results. That creates a second layer of
evaluation risk: the agent being evaluated is one thing, and the agent helping run the evaluation is
another. It can misunderstand the protocol, miss an isolation rule, summarize the wrong run, or fail
to notice that a group never actually ran the intended setup.

The right direction is a verify-and-repair loop around the experiment runner itself: preflight checks
for config parity and scaffold placement, post-run checks for memory leakage and group isolation,
metric availability checks, and explicit report-generation validation. If a check fails, the agent
should repair and rerun. The hard part is that many checks were learned only after a bad or
ambiguous run exposed the failure mode.

**If there is a better way to design rigorous experiments while still letting agents run them fully
AFK, I would be happy to learn it.**

## Production-Simulation Protocol

The final run used a production-simulation protocol on the Flask full chain:

- Package chain: Flask `2.0.0 -> 2.3.3`
- Agent: Codex CLI
- Provider/model: OpenAI `gpt-5.5`
- Effort: high
- `max_iters=2`
- One fresh Codex session per SWE-Chain step
- Up to two conversations per step:
  - `build`: first attempt
  - `fix_1`: retry attempt if the revealed feedback suite failed
- Same SWE-Chain oracle and scoring framework across all groups
- Final holdout scoring used only for analysis, not for memory writeback
- ai-wiki-toolkit source checkout fixed at `175b9a46cd8228051a893dc982d8da480a407e74`
- The final four groups did not install or run `aiwiki-toolkit` inside task containers

The four final groups were:

| Group | Setup |
| --- | --- |
| `init-only` | `/init`-style `AGENTS.md`; no AI Wiki memory |
| `init-trial-error` | `AGENTS.md` plus memory index pointer; trial-error memory enabled |
| `init-recurring-learning` | `AGENTS.md` plus memory index pointer; recurring learning enabled |
| `init-trial-error-recurring-learning` | Both trial-error and recurring memory enabled |

The memory pointer appended to `AGENTS.md` was intentionally short:

```md
## AI Wiki Memory

If `/app/ai-wiki/memory/index.md` exists, read it before editing and follow its read rules.
Treat memory as reference material for the current task, not as a replacement for the spec or source.
Do not write hidden evaluator feedback into memory.
```

The memory index described the folder and linked entries. It did not route the agent or select a
top-k set of files.

## Revealed Feedback And Final Holdout

SWE-Chain provides the underlying task chain, oracle, and test corpus. For this production-simulation
experiment, the harness split that corpus into two deterministic subsets:

- a revealed feedback suite
- a final holdout suite

This is roughly the same instinct as separating validation and test sets in machine learning. The
model itself is not being trained here, so the analogy is limited, but the separation is useful:

| Suite | Rough ML analogy | Agent can see result? | Can affect retry? | Can affect memory? | Use |
| --- | --- | ---: | ---: | ---: | --- |
| revealed feedback | validation / CI feedback | Yes | Yes | Yes, in sanitized form | Guides `fix_1` and allowed memory signals |
| final holdout | unseen test set | No | No | No | Final generalization scoring |

The split used the current step's evaluable SWE-Chain tests:

1. Consider tests that passed in the source baseline.
2. Separate upgrade-related tests from non-upgrade tests. Upgrade-related tests are those where the
   cross baseline fails or errors.
3. Within each bucket, use a stable hash of package, transition, and test node id.
4. Put about 70% into the revealed feedback suite and the rest into final holdout.
5. Ensure both sides are non-empty when possible.

After attempt 1, the harness runs the revealed suite. If the revealed suite indicates a retry is
needed, the same step/session gets a `fix_1` attempt and can see revealed feedback.

After the agent stops, the harness runs the final holdout suite privately. At that point the agent is
done: no new attempt, no memory read, no retry. Final holdout is just scoring.

## Metrics

The report tracks both per-attempt and final metrics.

| Metric | Meaning |
| --- | --- |
| Build F1 | First attempt performance on the revealed suite |
| Build+fix F1 | Best performance after revealed-feedback retry, if any |
| Holdout F1 | Final code performance on the private holdout suite |
| Recall / resolved | How much intended upgrade behavior was recovered |
| Precision | How many produced changes avoided false positives/regressions |
| TP / FN / FP | Per-phase classification counts |
| Conversations | One Codex task attempt for one SWE-Chain step |
| Fix iterations | Number of `fix_1` attempts used |
| Turns / session ids | Execution telemetry when available |

This matters because a second attempt is normal in real work. An agent often writes a first version,
sees CI feedback, and repairs it. A useful metric should capture both first-pass quality and the
ability to repair while still measuring generalization on held-out tests.

## Final Four-Group Result

| Group | Survival | Conversations | Fix iters | Build+fix F1 | Holdout F1 | Holdout recall | Holdout precision | Holdout FP | Interpretation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `init-only` | 17/17 | 27 | 10 | 0.9907 | 0.9195 | 0.9091 | 0.9302 | 3 | Strong initialized baseline |
| `init-trial-error` | 17/17 | 26 | 9 | 0.9714 | 0.9647 | 0.9318 | 1.0000 | 0 | Best next default candidate |
| `init-recurring-learning` | 17/17 | 32 | 15 | 0.2524 | 0.9302 | 0.9091 | 0.9524 | 2 | Noisy / unstable |
| `init-trial-error-recurring-learning` | 17/17 | 30 | 13 | 0.9907 | 0.9302 | 0.9091 | 0.9524 | 2 | Stable, but did not beat trial-error |

The headline interpretation:

- `init-only` is a strong baseline.
- `init-trial-error` had the best final holdout F1 and zero final-holdout false positives.
- `init-recurring-learning` had acceptable holdout numbers but collapsed on revealed build+fix F1,
  with a large false-positive signal. It also produced the heaviest memory-read footprint.
- `init-trial-error-recurring-learning` stabilized the recurring layer, but did not beat
  trial-error-only on final holdout F1.

The best next default candidate is therefore `init + trial-error memory`.

I read this as suggestive evidence with a narrow scope. It is one full-chain Flask run. Before turning
it into a broader benchmark claim, I would want to repeat the same protocol on another SWE-Chain
package or rerun Flask with a fixed seed.

## Memory Activity And Safety

The final run also tracked memory activity.

| Group | Memory files | Trial-error notes | Recurring notes | Memory read commands | Broad-like memory commands |
| --- | ---: | ---: | ---: | ---: | ---: |
| `init-only` | 0 | 0 | 0 | 0 | 0 |
| `init-trial-error` | 11 | 10 | 0 | 48 | 0 |
| `init-recurring-learning` | 16 | 0 | 15 | 101 | 1 |
| `init-trial-error-recurring-learning` | 25 | 9 | 15 | 62 | 1 |

The safety audit found no direct final-holdout or hidden evaluator leakage in copied AI Wiki memory.
The only `hidden` matches were guard text such as "do not use hidden evaluator failures."

One nuance: in this benchmark run, memory notes were harness-generated from public/local trajectories
for experiment control. The task agent's real trial-error behavior produced the signal, but the
outer runner generated the Markdown notes from structured public/local data. I would avoid reading
that as a production product decision about writeback authoring. Whether production ai-wiki-toolkit
writeback should be agent-authored, tool-mediated, human-reviewed, or hybrid is still a separate
design question.

## Artifact Plan

The planned public artifact location is:

`BochengYin/ai-wiki-toolkit-impact-eval-artifacts/artifacts/2026-06-13-swe-chain-flask-production-sim-four-group/`

The initial public artifact release should include:

```text
artifacts/2026-06-13-swe-chain-flask-production-sim-four-group/
  README.md
  reports/
    final_report.md
    summary_metrics.csv
    overall_phase_metrics.csv
    per_attempt_metrics.csv
    per_step_summary.csv
    memory_activity.csv
    noise_audit.csv
    recurring_support_counts.csv
  run_config/
    run_production_sim_four_groups.sh
    flask-init-AGENTS.md
    memory-index-template.md
  checksums.sha256
```

This follows SWE-Chain's artifact spirit while publishing a sanitized subset first. Raw trajectories
and full logs are intentionally out of scope for the initial public artifact release.

## Boundaries

The boundaries are important.

I would keep the claim narrow: this run does not establish that AI Wiki improves all SWE-Chain
tasks.

Recurring learning also deserves a narrower reading. This implementation was too noisy in this Flask
run; that says more about this candidate generator than about the whole idea.

Same for router/read-selection. This run says the old dogfood routing layer was not precise enough
to be treated as a default memory mechanism. Routing still has room as a research direction.

Model comparison was outside scope. The model was fixed at `gpt-5.5`.

It also leaves production writeback design open.

Raw trajectories are outside the initial artifact release.

## Open Questions / Next Experiments

Can the `init + trial-error memory` result reproduce on another SWE-Chain package?

Should writeback be agent-authored, tool-mediated, human-reviewed, or hybrid?

Can recurring learning be made useful with better filtering?

Can router/read-selection be evaluated independently before reintroducing it?

Can experiment verification be automated enough to reduce HITL while keeping the benchmark
auditable?

## References

- [AI Wiki Impact Eval Pilot](ai_wiki_impact_eval_pilot.md)
- [SWE-Chain paper](https://arxiv.org/html/2605.14415v1)
- [SWE-Chain GitHub repository](https://github.com/CUHK-ARISE/SWE-Chain)
- [SWE-Chain Hugging Face dataset](https://huggingface.co/datasets/For-Anonymous-Submission-90/SWE-Chain)
- [ai-wiki-toolkit impact eval artifacts repository](https://github.com/BochengYin/ai-wiki-toolkit-impact-eval-artifacts)
