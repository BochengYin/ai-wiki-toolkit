# Route Precision Research Handoff

Date: 2026-06-05

This handoff summarizes the current `ai-wiki-toolkit` route precision work so a follow-up research
thread can focus on method design without re-deriving the experiment history.

## Current Question

The working question is not whether more memory should be added. The current bottleneck is whether
route can select the right existing memory with lower noise.

The specific failure pattern is:

- useful eval/memory docs exist
- many docs share broad vocabulary such as `eval`, `route`, `memory`, `workflow`, `report`,
  `metric`, or `source incident`
- route selects several adjacent docs where only one stage-specific doc is useful
- selected-but-unused docs dominate precision loss

## Baseline

The strict historical replay cohort contains 57 evaluable route traces.

Baseline replay result:

| traces | precision | noise | selected | selected useful | missed useful |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 57 | 0.350 | 0.650 | 320 | 112 | 52 |

The detailed false-positive analysis found:

- 320 selected docs
- 112 useful selections
- 208 false positives
- 43 unique false-positive docs
- top 10 false-positive docs account for 117 of 208 false positives

## Experiment Design

The `applies_when` experiment used a blinded metadata treatment.

Controls:

- same 57 historical route traces
- `catalog_cutoff=trace-routed-at`
- `max_docs=6`
- deterministic top-20 index-card reranker
- treatment target docs selected by control selected-count frequency only
- target selection did not use useful, false-positive, or missed-useful labels

Label generation:

- top 20 selected docs were targeted
- 15 of 20 had recoverable source/write-back sessions
- 14 labels passed audit
- label writer saw source-session context only, not route outcomes or the 57 replay prompts

Important limitation:

- core docs such as `constraints`, `decisions`, and `workflows` had no write-back session, so they
  were not part of the blinded `applies_when` treatment

## Round 1: Flat Hint Scorer

Initial treatment treated `applies_when` as ordinary positive hint text.

| condition | precision | noise | selected useful | missed useful | paired |
| --- | ---: | ---: | ---: | ---: | --- |
| control | 0.350 | 0.650 | 112 | 52 | - |
| treatment | 0.338 | 0.662 | 108 | 53 | 3 wins / 7 losses / 47 ties |

Interpretation:

Flat metadata made routing worse. Negative boundary text such as `not for report summaries` or
`not for ordinary route invocation` was still tokenized as positive matching surface.

## Round 2: Structured Applies-When Scorer

The scorer was changed to split `applies_when` into:

- positive clause: used as route hint text
- negative clause: excluded from positive scoring and used for a penalty when matched

Result:

| condition | precision | noise | selected useful | missed useful | paired |
| --- | ---: | ---: | ---: | ---: | --- |
| control | 0.350 | 0.650 | 112 | 52 | - |
| treatment | 0.350 | 0.650 | 112 | 51 | 3 wins / 3 losses / 51 ties |

Interpretation:

Structured negative-boundary handling fixed the regression but did not create a precision lift.
This showed that label-side metadata is necessary but insufficient.

## Round 3: Route-Side Action/Stage Alignment

The route side was then tightened. Route now extracts task intent signals such as:

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

Broad topic words such as `eval`, `route`, `memory`, or `workflow` are intentionally not counted as
action/stage alignment.

For docs with `applies_when`, the scorer compares the task action/stage terms against the positive
clause. If the doc has action/stage terms but none align with the task, it receives a small mismatch
penalty.

Result:

| condition | precision | noise | selected useful | missed useful | paired |
| --- | ---: | ---: | ---: | ---: | --- |
| control | 0.350 | 0.650 | 112 | 52 | - |
| treatment | 0.353 | 0.647 | 113 | 52 | 4 wins / 3 losses / 50 ties |

Interpretation:

The lift is small. It is not enough to claim route precision is fixed. It does support the narrower
hypothesis that both sides must be structured:

- memory labels need `do what when trigger; excluding nearby wrong cases`
- route needs to interpret the current prompt as action/stage, not just topic tokens

## Implemented Code Surfaces

Current route-side surfaces:

- `route.intent_signals` in route packets
- `applies_when_signal.task_alignment_tokens`
- `applies_when_signal.positive_alignment_tokens`
- `applies_when_signal.positive_alignment_matches`
- per-doc `applies_when_adjustment`
- route traces now record `intent_signals`
- route traces now record per-doc `route_applies_when_signals`
- historical replay items now include `intent_signals`

Relevant files:

- `src/ai_wiki_toolkit/route.py`
- `src/ai_wiki_toolkit/route_traces.py`
- `src/ai_wiki_toolkit/impact_analysis.py`
- `tests/test_route.py`
- `tests/test_route_traces.py`
- `evals/impact/public/blinded_applies_when_route_replay.md`

## What Not To Assume

Do not assume the next method should be core-doc gating.

The idea "move `constraints`, `decisions`, and `workflows` to `maybe_load` unless a task has an
explicit implementation/release/scaffold/ownership/constraint action" was proposed as one possible
route-side experiment, but it should not be treated as the selected next direction.

The user explicitly pushed back on that idea. It should remain an open method question, not an
accepted recommendation.

## Open Method Questions

The next research window should compare methods before coding another route change.

Questions to evaluate:

1. Should route use bucketed selection instead of flat top-k?
2. Should broad docs require action/stage match only when competing with a more specific doc?
3. Should negative `applies_when` matches suppress a doc entirely rather than apply a small penalty?
4. Should core docs receive explicit scope metadata instead of route-level gating?
5. Should route distinguish discussion, planning, implementation, replay, and reporting modes before
   selecting docs?
6. Should route optimize precision at fixed recall, or optimize a product metric such as useful docs
   per packet?
7. Should false positives be analyzed by prompt family before changing global scorer behavior?

## Recommended Starting Point For New Window

Start by reading:

1. `evals/impact/public/blinded_applies_when_route_replay.md`
2. `evals/impact/reports/route_false_positive_research_2026-06-04.md`
3. `evals/impact/experiments/applies_when_blind_2026_06/reports/control_vs_treatment.json`
4. `ai-wiki/people/bochengyin/drafts/route-false-positives-need-stage-labels-and-abstention.md`

Then inspect the seven paired traces where treatment changed precision in
`control_vs_treatment.json`. The method should be chosen from those concrete wins/losses, not from a
general preference for lower `max_docs`, core-doc gating, or more labels.
