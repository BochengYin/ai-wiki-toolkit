# Agent-Skill Writeback on the Flask SWE-Chain

_A product-shape case study for runner hooks, conversation fork, and quarantined memory writeback_

## Abstract

This report follows the earlier Flask SWE-Chain memory evaluation:
[`flask_swe_chain_memory_eval_report.md`](flask_swe_chain_memory_eval_report.md).

The earlier report found that `init + trial-error memory` was the best next default candidate among
the evaluated memory horizons. It also left open an important product question: should production
writeback be authored by the harness, by the coding agent, by a separate agent skill, by a human, or
by some hybrid?

This follow-up experiment tested that product question directly. It ran a full Flask SWE-Chain
`2.0.0 -> 2.3.3` same-run comparison with two groups:

- `init-harness-trial-error`: deterministic harness-authored trial-error memory.
- `init-agent-skill-writeback`: runner-triggered conversation fork, repo-local writeback skill,
  quarantined candidate memory, immediate deterministic audit, then publish or skip.

The main result is not a benchmark-performance win. The benchmark numbers were essentially tied.
The main result is a product-shape win: the agent-skill writeback protocol completed the full chain,
respected quarantine and audit boundaries, forked the real Codex conversation on every treatment
attempt, and wrote less memory than the deterministic harness while preserving high final test
performance.

That points to the next product direction: AI Wiki writeback should be a runner/lifecycle feature
with agent-authored memory candidates, skill instructions, quarantine, immediate audit, and explicit
publish/reject behavior. "Ask the coding agent to remember to call a hook" is too weak to be the
primary trigger.

## What Changed Since The Earlier Flask Report

The earlier Flask memory report evaluated memory horizons:

| Layer | Question |
| --- | --- |
| `/init` | Does repo orientation help? |
| Trial-error memory | Does recent debugging experience help future fresh agents? |
| Recurring learning | Do repeated signals across steps help? |
| Router/read-selection | Can an attention-control layer choose useful memory? |

This experiment evaluated writeback product shape instead:

| Layer | Question |
| --- | --- |
| Runner normal-end hook | Can writeback be triggered reliably after a coding attempt? |
| Programmatic conversation fork | Can writeback run in a separate child conversation with parent context? |
| Repo-local writeback skill | Can an agent decide whether to write or skip memory? |
| Quarantine + audit | Can memory be reviewed before it becomes visible to future agents? |
| Host/container sync | Can published memory actually persist into later SWE-Chain steps? |

The distinction matters. The earlier experiment gave evidence that trial-error memory is useful.
This experiment tested whether the writeback path can look like a product rather than an experiment
harness shortcut.

## Protocol

The final formal run used:

- Package chain: Flask `2.0.0 -> 2.3.3`
- Agent: Codex CLI
- Provider/model: OpenAI `gpt-5.5`
- Effort: high
- `max_iters=2`
- One fresh Codex session per SWE-Chain step
- Up to two conversations per step:
  - `build`: first attempt
  - `fix_1`: retry attempt after revealed feedback, when needed
- Same SWE-Chain source, oracle, revealed/final split, container images, and scoring commands
- Runner-managed after-conversation hook after a normal Codex turn completion
- Quarantined memory candidate directory for every writeback attempt
- Immediate deterministic safety audit before any note reached `/app/ai-wiki/memory/`

The final trigger condition was:

```text
codex exec exits 0
and Codex JSONL contains turn.completed
then runner invokes after_conversation.py
then revealed feedback may run
```

Timeouts, crashes, nonzero exits, and missing `turn.completed` do not trigger writeback. Those runs
are incomplete and must be repaired or quarantined.

## Why Runner Hook Won

The original PRD started with a natural product intuition: tell the coding agent to invoke an
after-conversation hook when it finishes. That was not reliable enough in formal SWE-Chain runs.
The coding agent could keep polishing, stall before the hook, or timeout before reaching the
self-call.

Local Codex lifecycle hook probes also did not produce a usable Stop or PreToolUse signal in this
environment. The reliable trigger was a wrapper-level normal-end hook controlled by the runner.

That changes the product design:

| Candidate trigger | Result |
| --- | --- |
| Coding agent self-calls hook | Useful convention, not reliable as the primary trigger |
| Codex Stop hook in this environment | Did not produce a usable signal in local probes |
| Runner normal-end hook | Completed both formal groups |

The product implication is direct: writeback should live in lifecycle infrastructure. The agent can
know about the convention, but the system should own the trigger.

## Formal Result

| Group | Successful steps | Attempts | Fix attempts | Formal hooks | Published notes | Skips | Avg revealed pass rate | Avg final pass rate | Total elapsed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `init-harness-trial-error` | 17/17 | 31 | 14 | 31 | 31 | 0 | 0.9970 | 0.9947 | 6720.5s |
| `init-agent-skill-writeback` | 17/17 | 31 | 14 | 31 | 20 | 11 | 0.9981 | 0.9943 | 6514.5s |

The benchmark-performance result is effectively a tie:

- both groups survived the full chain;
- treatment was slightly higher on revealed pass rate;
- harness was slightly higher on final holdout pass rate;
- treatment was slightly faster;
- none of these differences should be read as a strong performance claim from a single run.

The product-shape result is clearer:

- treatment forked the current coding conversation on all 31 formal attempts;
- the forked child invoked the repo-local `ai-wiki-trial-error-writeback` skill;
- writeback candidates were quarantined before publication;
- deterministic audit approved 20 treatment notes and skipped 11;
- the final leakage audit found no final-holdout, future-step, hook-output, writeback-context, or
  quarantine-path leakage in published treatment memory or treatment coding logs.

## What "Skip" Means

In this experiment, a skip is a writeback decision, not a test outcome.

The treatment writeback agent skipped 11 of 31 formal attempts. A skip means the child writeback
conversation concluded that no new durable memory should be published for that attempt. Common safe
reasons include:

- the attempt was a normal implementation pass;
- the observed verification gap was already covered by existing memory;
- the lesson was too step-specific;
- the candidate would be noisy or low confidence;
- no failed local/public check changed the implementation direction.

The deterministic harness published 31 notes because it is a high-recall reference mechanism. It is
supposed to convert nearly every eligible public/local signal into a memory note. The agent-skill
treatment was more selective. That is a product advantage if the skipped notes were genuinely low
value, because production memory should minimize confident noise.

## Why There Is No Precision, Recall, Or F1 Here

The earlier Flask memory report includes SWE-Chain precision, recall, and F1 because that run
generated benchmark classification metrics for resolved upgrade behavior and regressions.

This follow-up report intentionally focuses on writeback workflow correctness. It reports test pass
rates and writeback decisions, but it does not claim memory precision, memory recall, or memory F1.

Those would require a separate labeling step:

| Metric | Required label |
| --- | --- |
| Memory precision | Of published notes, how many were correct, reusable, non-duplicative, and safe? |
| Memory recall | Of all attempts where a reusable lesson existed, how many did the writeback flow capture? |
| Memory F1 | Combined precision and recall over that labeled writeback opportunity set |

The available `approved` and `skipped` labels are safety/protocol outcomes. They are not enough to
measure memory quality. A skipped note can be correct behavior. An approved note can be safe but
still not useful. A future evaluation should add a post-hoc memory-quality rubric.

## Safety And Validity

The final formal run is valid for workflow correctness. There are two caveats.

First, treatment `fix_1` attempts are conditionally valid for memory-effect interpretation because
current-step revealed failure data intentionally entered the retry prompt. That is normal for the
benchmark's repair loop, but it means causal memory-performance claims should be conservative.

Second, several earlier attempts were invalid or superseded and were quarantined before the final
rerun. The repair log matters because it shaped the final protocol:

- agent-self-hook attempts timed out or stalled before reaching the hook;
- one rerun exposed prior failed artifacts to the agent and was invalidated;
- stderr handling and JSON stream parsing had to be hardened;
- hook-published memory initially lived only in the host mirror and did not carry into later Docker
  step state;
- the runner was fixed to sync approved memory back into `/app` and verify index visibility before
  the next step.

The important lesson is that memory experiments need their own verification loop. It is easy to
think memory was published or read when it only existed in a side tree.

## Product Direction

This is the first run where the writeback path starts to look like the product I would want:

```text
coding attempt completes normally
-> runner/lifecycle hook fires
-> system forks the completed conversation
-> child writeback agent invokes a repo-local skill
-> child decides write / skip / blocked
-> candidate goes to quarantine
-> deterministic audit publishes or rejects
-> approved memory becomes visible to later agents through the repo memory index
```

The strongest product conclusions are:

1. Writeback trigger should be owned by lifecycle infrastructure, not by agent obedience.
2. The coding agent and writeback agent should be separate roles.
3. Memory candidates should be quarantined by default.
4. Publication should require an immediate audit step.
5. Skipping should be first-class, not treated as failure.
6. Memory quality needs its own precision/recall evaluation before broad default rollout.
7. Host/container or worktree sync must be treated as a product invariant, not an implementation
   detail.

This points toward a smaller, sharper product than the earlier dogfood routing stack: start with
bounded memory read plus lifecycle writeback. Defer router/read-selection until it has its own
precision eval.

## Open Questions / Next Product Work

The next ai-wiki-toolkit product design needs to answer:

- What is the default lifecycle trigger in Codex CLI, Codex app, and other agent hosts?
- What exact context does the writeback fork receive?
- Is writeback synchronous at task end, asynchronous after task end, or both?
- What does quarantine look like in a normal repo?
- Who can approve memory: deterministic audit, agent audit, human, or policy stack?
- What is the UI for "skipped" and "rejected" writeback?
- How do we measure memory precision, recall, and F1 without creating a heavy review burden?
- How do we prevent memory from turning into a noisy project diary?
- How do we support hosts where true conversation fork is unavailable?

## References

- [Evaluating Agent Memory on the Flask SWE-Chain](flask_swe_chain_memory_eval_report.md)
- [AI Wiki Impact Eval Pilot](ai_wiki_impact_eval_pilot.md)
- [SWE-Chain paper](https://arxiv.org/html/2605.14415v1)
- [SWE-Chain GitHub repository](https://github.com/CUHK-ARISE/SWE-Chain)
- [SWE-Chain Hugging Face dataset](https://huggingface.co/datasets/For-Anonymous-Submission-90/SWE-Chain)
