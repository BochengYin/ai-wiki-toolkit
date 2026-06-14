# Route Precision Research Journey

Date: 2026-06-05

This report documents a route-precision research loop for `ai-wiki-toolkit`: how an initially
reasonable metadata idea failed, what the failure revealed about coding-agent context construction,
and why the next router design moved from flat label matching to mode-aware, workflow-aware
selection.

The audience is coding-agent builders who care about eval design, context selection, failure
analysis, and production-quality agent behavior. The focus is not a feature announcement. It is the
research path: measure, intervene, replay, inspect changed pairs, revise the system model, and add
behavioral tests.

## Executive Summary

The original problem was low route precision. In a strict 57-trace historical replay, route selected
`320` documents. Only `112` selected documents were later useful, producing precision `0.350` and
noise `0.650`. The false positives were not random: `208` false-positive selections came from only
`43` unique docs, and the top `10` false-positive docs accounted for `117` of them.

The first hypothesis was that labels were too broad. Many useful memories were named with terms
like `eval`, `route`, `workflow`, `report`, `metric`, or `source incident`, but those labels did not
say which stage of work they applied to. A prompt about prompt design, artifact capture, runner
manifest, report quality, or source-incident timing could route to the same adjacent family of docs.

I tested a blinded metadata treatment: add source-session-derived `applies_when` labels to frequent
route targets, then replay the same 57 traces. The first treatment made precision worse, from
`0.350` to `0.338`, because the router treated exclusion text as positive match text. A label that
said "not for report summaries" still contributed tokens like `report` and widened selection.

Splitting labels into positive and negative clauses stopped the regression but did not improve
precision. Adding route-side action/stage alignment produced only a small lift, from `0.350` to
`0.353`. The important finding was not that labels solved the problem. The important finding was
that labels without a stronger router model cannot reliably express "use this document for this
stage, but not for nearby stages."

The next method therefore moved to a router-side design:

- classify the prompt mode before selecting docs: `plan`, `code`, `question_only`, `fixed_workflow`,
  `review`, or `report`
- detect fixed workflow contracts before ordinary memory retrieval
- split mixed tasks into intent buckets, such as release/distribution plus eval/report
- classify docs into route slots, such as prompt design, artifact capture, manifest/runner, report
  quality, route usefulness, source-incident timing, public metrics, and release distribution
- record selection reason types, such as `mandatory_contract`, `safety_guardrail`,
  `workflow_contract`, `bucket_primary`, and `background_reference`
- evaluate behavior, not only selected-document precision

A first prototype of this direction replayed the same 57-trace cohort at precision `0.371`, noise
`0.629`, selected docs `278`, selected useful docs `103`, and missed useful docs `55`. That is a
precision improvement, but selected useful docs dropped. I treat it as a precision/recall tradeoff
that needs a next-round evaluation, not as a final fix.

## Research Question

The question was not "can the system load more memory?" It was:

> Can a coding-agent memory router select the right existing memory with lower noise, while
> preserving enough useful context for real tasks?

That framing matters because many selected-but-unused docs were adjacent and credible. They were not
bad memories. They were useful memories at the wrong stage.

## Step 1: Measure The Failure

The first replay established a concrete baseline:

| traces | selected | selected useful | false positives | missed useful | precision | noise |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 57 | 320 | 112 | 208 | 52 | 0.350 | 0.650 |

The concentration pattern made the problem actionable. A small number of broad docs dominated the
noise:

- `impact-eval-prompts...`: 16 false positives
- `impact-eval-result-capture...`: 13 false positives
- `trial-error...`: 12 false positives
- `source-incident...`: 11 false positives
- `workflows`, `decisions`, and `constraints` often appeared as core safety context

The key diagnosis was "eval-stage soup." Prompt design, artifact capture, runner manifests, report
quality, source incident timing, and route usefulness all use words like `eval`, `run`, `report`, and
`metrics`, but they are different work stages.

## Step 2: Try The Obvious Label Fix

The first proposed fix was to add stage-aware metadata to high-traffic docs. To avoid overfitting,
the treatment was blinded:

- trace cohort: the same 57 historical route traces
- catalog cutoff: `trace-routed-at`
- max selected docs: `6`
- reranker: deterministic top-20 index-card reranker
- treatment target docs: top docs by control selected-count frequency, not by false-positive labels
- label source: original source/write-back session context only
- excluded from the label writer: route prompts, precision outcomes, missed-useful docs, future
  research notes

The target set was the top `20` docs by control selected frequency. Those represented `270` of
`320` control selected-document exposures. Of those `20`, `15` had recoverable source sessions and
`14` labels passed audit.

This made the experiment a fair metadata intervention rather than a hand-tuned answer-key patch.

## Step 3: First Negative Result

The first treatment treated `applies_when` as ordinary positive hint text.

| condition | traces | precision | noise | selected | selected useful | missed useful |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| control | 57 | 0.350 | 0.650 | 320 | 112 | 52 |
| treatment | 57 | 0.338 | 0.662 | 320 | 108 | 53 |

Paired comparison:

- wins: `3`
- losses: `7`
- ties: `47`

The failure was instructive. A natural-language label has both positive and negative intent:

```text
Use for route usefulness evaluation; not for ordinary route invocation or general reuse dashboards.
```

A flat token scorer cannot understand that structure. It sees tokens like `route`, `reuse`, and
`dashboard` anywhere in the label and may boost the document for exactly the cases the label meant to
exclude.

So the first result was not "metadata is bad." It was "metadata needs semantics."

## Step 4: Split Positive And Negative Label Semantics

The next scorer parsed `applies_when` into two parts:

- positive clause: available for normal route matching
- negative clause: removed from positive matching and used as a penalty when the task strongly
  matches the excluded condition

Result:

| condition | traces | precision | noise | selected | selected useful | missed useful |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| control | 57 | 0.350 | 0.650 | 320 | 112 | 52 |
| treatment | 57 | 0.350 | 0.650 | 320 | 112 | 51 |

Paired comparison:

- wins: `3`
- losses: `3`
- ties: `51`

This fixed the regression but did not create a lift. Negative boundaries are necessary, but they are
only defensive. They prevent some wrong matches; they do not create a strong enough positive model of
which stage the prompt is actually in.

## Step 5: Add Route-Side Action/Stage Alignment

The next change was on the router side. Instead of only asking whether a task shares broad topic
words with a doc, the route packet extracted action/stage signals such as:

- `design`
- `implement`
- `run`
- `report`
- `label`
- `manifest`
- `prompt`
- `artifact`
- `session`
- `provenance`

Broad nouns such as `eval`, `route`, `memory`, and `workflow` were intentionally not treated as
stage alignment. They are useful topic words, but too broad to decide whether a doc belongs in the
packet.

Result:

| condition | traces | precision | noise | selected | selected useful | missed useful |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| control | 57 | 0.350 | 0.650 | 320 | 112 | 52 |
| treatment | 57 | 0.353 | 0.647 | 320 | 113 | 52 |

Paired comparison:

- wins: `4`
- losses: `3`
- ties: `50`

This was a small positive result, not a solved result. It showed that route-side structure matters,
but it also showed that action/stage terms alone were still too weak.

## Step 6: Inspect The Seven Changed-Precision Pairs

The 57-trace replay had `37` traces where the selected set changed. Only `7` changed precision. That
means "treatment changed" did not mean seven total selection changes; it meant seven paired traces
where the changed selection affected measured precision.

Those seven traces were the most useful research signal:

- `4` treatment wins
- `3` treatment losses
- `30` traces changed selected sets but preserved the same precision

The wins showed cases where treatment pulled in the right subgoal or stage:

- release-plus-eval work needed distribution guidance in addition to eval docs
- evaluate-repo work benefited from route-usefulness memory rather than trial/error or source timing
- diagnostics work benefited from source-incident timing/provenance memory
- rubric/scoring work benefited from the right eval product/report quality stage

The losses showed the remaining failure:

- assessment/productization prompts still pulled adjacent efficiency or family-scope docs
- runner prompts could swap prompt-design or workflow-comparison memory for capture/product-MVP
  memory at the wrong moment
- "think hard" metrics prompts were planning/decision tasks, not implementation-memory retrieval
  tasks

The changed-pair analysis changed the method. The issue was no longer just "make labels more
specific." The issue was that route needed a parent model of mode, workflow, and subgoal coverage.

## Step 7: Redesign The Router Model

The next design separated routing into layers.

### Mode First

The prompt mode is a parent decision, not just another scoring feature. A task like "think hard",
"plan first", "do not code", "decide", "evaluate", or "research" should not compete directly
against implementation-stage docs. It should first enter a mode such as:

- `plan`
- `code`
- `question_only`
- `fixed_workflow`
- `review`
- `report`

Only after mode classification should docs compete.

### Workflow Contracts

Some tasks have fixed workflows: weekly report metrics, promotion/reuse diagnostics, task-check
memory, diagnostics provenance, release flow, and similar repeated processes.

For those tasks, the router should select the workflow contract first. Adjacent design notes should
not substitute for the workflow. Supporting docs should be opened only when the task asks to change,
debug, or handle an exception in the workflow.

This also changes the eval. The test should ask:

- did the agent identify the correct workflow?
- did it follow the required steps?
- did it avoid using a nearby design note as a workflow replacement?
- did it open supporting docs only for exceptions, design changes, or debugging?

### Intent Buckets

Mixed-intent prompts should not be handled by flat top-k. A task like "merge PR, release npm, and
run trial/error report" has at least two subgoals:

- release/distribution
- eval/report

Flat top-k can fill the packet with six adjacent eval docs and miss the release/distribution slot.
The better selector first allocates coverage by intent bucket, then uses scoring inside each bucket.

### Selection Reason Types

Core docs need a different interpretation from ordinary memory docs. A core safety doc may look
unused in selected-vs-reused telemetry but still be intentionally present as a guardrail.

The router therefore needs reason types such as:

- `mandatory_contract`
- `safety_guardrail`
- `workflow_contract`
- `bucket_primary`
- `background_reference`

Then route precision can be analyzed differently by reason type. A safety guardrail should not be
judged exactly like a topical draft.

## Step 8: Prototype Result

The first prototype added:

- route modes
- fixed workflow contracts
- intent buckets
- doc slots
- selection reason types
- behavior contracts in route packets
- trace fields for mode, workflow contract, buckets, slots, and reason types
- tests for plan/no-code mode, fixed workflow behavior, and release-plus-eval bucket coverage

Focused route tests passed, and the full test suite passed in the implementation run. The strict
57-trace replay with the prototype returned:

| traces | precision | noise | selected | selected useful | missed useful |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 57 | 0.371 | 0.629 | 278 | 103 | 55 |

This is better precision but worse useful-selection recall. The interpretation is:

> The mode/workflow/bucket design reduced some noise by selecting fewer docs, but it may now be too
> conservative. The next experiment should optimize precision at an explicit recall floor or use a
> product metric closer to agent task success.

## What This Changed In The Evaluation Strategy

The original selected-doc precision metric was useful for finding the problem, but it is not enough
to define product quality.

The next evaluation should include behavior tests:

- mode accuracy: did the agent enter plan, code, report, review, question, or workflow mode?
- workflow follow rate: did it execute the expected fixed workflow steps?
- bucket coverage rate: did mixed-intent prompts cover each required subgoal?
- adjacent-doc overread rate: did it read same-topic wrong-stage docs?
- core-doc reason accuracy: were core docs selected as guardrails/contracts, not generic filler?
- supporting-doc discipline: did it open design notes only when the task required design/debugging?

This is closer to the product question for coding agents: did the context construction cause the
agent to behave correctly, not merely did a selected doc later get cited.

## Lessons

1. Broad labels create credible false positives.

   The worst docs were not low-quality docs. They were high-value docs with broad topic labels.
   Without stage information, useful memory becomes noisy memory.

2. Excluding conditions can hurt if the router has no negative semantics.

   Natural language like "not for report summaries" only works if the router treats it as an
   exclusion. A flat scorer can turn it into a positive match.

3. Label-side fixes need route-side structure.

   `applies_when` labels helped only after the router understood positive versus negative clauses
   and extracted action/stage intent from the prompt.

4. Mode is above document competition.

   Planning, implementation, reporting, review, and question-answering are different modes. They
   should not all compete in the same top-k document pool.

5. Fixed workflows should be tested behaviorally.

   For recurring workflows, the right outcome is not "the agent selected a related memory." The
   right outcome is "the agent followed the workflow and only opened supporting docs when justified."

6. Mixed-intent tasks need coverage before ranking.

   A single top-k list can miss a required subgoal. Intent buckets preserve coverage for tasks that
   combine release, eval, reporting, and implementation.

7. Precision gains must be read with recall.

   The prototype improved precision but lost selected useful docs. That is progress only if the
   product metric values lower noise more than the lost context, or if the next iteration recovers
   recall through bucket-specific coverage.

## Reproducibility Artifacts

Public-safe artifacts:

- `evals/impact/public/blinded_applies_when_route_replay.md`
- `evals/impact/reports/route-research-2026-06-04/route_false_positive_research_2026-06-04.md`
- `evals/impact/reports/route-method-2026-06-05/route_precision_handoff_2026-06-05.md`
- `evals/impact/experiments/applies_when_blind_2026_06/manifest.json`
- `evals/impact/experiments/applies_when_blind_2026_06/inputs/target_docs.json`
- `evals/impact/experiments/applies_when_blind_2026_06/labels/treatment_overlay.json`
- `evals/impact/experiments/applies_when_blind_2026_06/reports/control_vs_treatment.md`
- `evals/impact/experiments/applies_when_blind_2026_06/reports/control_vs_treatment.json`

Representative commands:

```bash
python -m ai_wiki_toolkit.cli eval impact route-noise replay \
  --before 2026-06-04T08:20:53+10:00 \
  --catalog-cutoff trace-routed-at \
  --rerank-top 20 \
  --format json

python -m pytest tests/test_route.py tests/test_route_traces.py
python -m pytest
```

Raw label packets, raw labeler outputs, recovered source maps, temporary worktrees, and local session
exports are intentionally not part of this public report until scrubbed.
