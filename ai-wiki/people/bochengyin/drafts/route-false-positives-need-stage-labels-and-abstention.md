---
title: "Route false positives need stage labels and abstention"
author_handle: bochengyin
model: codex
source_kind: analysis
status: draft
created_at: 2026-06-04
updated_at: 2026-06-04
promotion_candidate: false
promotion_basis: "Single 57-trace false-positive research report; keep local until a follow-up scorer/label fix proves it."
---

# Route False Positives Need Stage Labels And Abstention

## Problem

The strict 57-trace historical route replay selected 320 docs, with 112 useful selections and 208
false positives. The detailed analysis is recorded at:

```text
evals/impact/reports/route-research-2026-06-04/route_false_positive_research_2026-06-04.md
```

The low precision is not caused by one bad document. The false positives concentrate in broad
eval/memory drafts and core docs. The top 10 false-positive docs account for 117 of 208 false
positive selections.

## Lesson

Route precision is currently limited by a label-and-logic interaction:

- Many high-value eval/productization drafts have broad labels such as eval, report, replay,
  workflow, metric, source incident, and memory diagnostics.
- The labels do not encode the workflow stage strongly enough: prompt design, manifest, runner,
  capture, scoring, discovery, source-incident timing, report interpretation, or release.
- Core docs such as constraints, decisions, and workflows are selected too often as a safety
  blanket for discussion-only or strategy prompts.
- Short CJK/discussion prompts often need abstention or prior-turn context, not more keyword
  expansion.

## Preferred Next Fixes

Start with labels before changing scorer weights:

1. Add or tighten `applies_when` / `routing_hint` on the top false-positive eval docs.
2. Include negative boundaries, such as "not for runner implementation" or "not for generic eval
   planning."
3. Add route logic that treats discussion-only and short CJK prompts as low-confidence routes that
   can return fewer selected docs.
4. Move core docs to `maybe_load` unless the prompt has an implementation, release, scaffold,
   ownership, or constraint-sensitive action.
5. Replace flat top-k with bucketed selection for multi-intent tasks after labels are improved.

## Label Shape

Use action-and-stage labels rather than broad topic labels.

`verb + noun` is a good minimum because it names the action and object, such as `score artifacts`,
`capture results`, or `discover families`.

`verb + adjective + noun` is useful only when the adjective narrows routing, such as `capture
first-pass artifacts` or `discover trial-error candidates`. Avoid adjectives that do not change
selection, such as generic `good`, `better`, `robust`, or `formal`.

The preferred shape for `applies_when` is:

```text
<verb> <stage/object> when <trigger>; not for <nearby stages>
```

Examples:

- `Design manual eval prompts from concrete historical tasks; not for runner implementation or
  artifact capture.`
- `Capture first-pass eval artifacts and untracked files; not for prompt design or family
  discovery.`
- `Score captured artifacts with rubric definitions; not for manifest planning or release tasks.`

## Blinded Label Reconstruction Experiment

When testing whether `applies_when` would have improved historical route precision, the treatment
labels must be reconstructed from each memory's original write-back/source session, not from the
57-trace false-positive report.

Allowed label-writer inputs:

- the target memory file as it existed at the time being labeled
- the source session that produced that memory
- text before or at the first write-back footer for that memory
- the label grammar: `do what when trigger; excluding nearby wrong cases`

Forbidden label-writer inputs:

- the 57 route replay prompts
- selected/useful/false-positive/missed-useful outcomes
- `route_false_positive_research_2026-06-04.md`
- notes created after the evaluated route trace cutoff
- future edits to the target memory

The replay evaluator can use the 57-trace ground truth, but the label writer cannot. Otherwise the
treatment labels are answer-key leakage rather than evidence that labels would have helped at
memory creation time.

## 2026-06-05 Blinded Applies-When Result

The first blinded `applies_when` treatment did not improve the strict 57-trace replay. With 14
audit-passing labels generated from source-session packets, control precision was `0.350` and
treatment precision was `0.338`; noise moved from `0.650` to `0.662`.

The main failure mode was that the current scorer treats `applies_when` as a flat `routing_hint`.
That means tokens in negative boundaries such as `not for report summaries` or `not for ordinary
route invocation` still become positive matching surface. Stage labels can therefore widen broad
eval/memory docs instead of narrowing them.

Next scorer work should parse `applies_when` into positive and negative clauses. Positive clauses
should require action/stage alignment before boosting broad drafts. Negative clauses should penalize
or suppress docs when the task matches an excluded nearby stage.

## 2026-06-05 Structured Applies-When Follow-Up

After changing the scorer to split `applies_when` into positive and negative clauses, the same
14-label blind treatment no longer hurt the 57-trace replay. Control stayed at precision `0.350` and
noise `0.650`; treatment was also precision `0.350` and noise `0.650`, with missed useful docs
moving from `52` to `51`.

This means structured `not_for` handling fixed the flat-hint regression, but did not produce a
precision lift. The next bottleneck is positive action/stage alignment: broad eval and memory drafts
should not be boosted by generic nouns unless the task also matches the intended workflow stage or
action.

## 2026-06-05 Route-Side Action/Stage Follow-Up

After adding route-side task intent signals, the same 14-label blind treatment produced a small
positive lift on the strict 57-trace replay: control stayed at precision `0.350` and noise `0.650`,
while treatment moved to precision `0.353` and noise `0.647`. Selected useful docs moved from `112`
to `113`; missed useful docs stayed at `52`; paired traces were `4` wins, `3` losses, and `50` ties.

The route-side change intentionally does not treat broad domain words such as `route`, `memory`,
`eval`, or `workflow` as action/stage alignment. It extracts more specific task intent terms such as
`design`, `implement`, `run`, `report`, `label`, `manifest`, `prompt`, `artifact`, `session`, or
`provenance`, then compares them to the positive clause of `applies_when`.

This supports the user's concern that both sides need tightening. Memory labels should define
`do what when trigger; excluding nearby wrong cases`, and route logic should interpret the current
prompt as an action/stage instead of a flat topic bag.

## 2026-06-05 Method Selection Refinement

After the route-side action/stage follow-up, the user pushed back on immediately doing core-doc
gating for `constraints`, `decisions`, and `workflows`. Treat core-doc gating as an open method
question, not the selected next step.

Before another route scorer change, write a handoff and inspect the concrete paired wins/losses from
the 57-trace replay. The next method should be chosen from observed failure cases, not from a generic
preference for fewer docs, more labels, or moving core docs to `maybe_load`.

The handoff report is:

```text
evals/impact/reports/route-method-2026-06-05/route_precision_handoff_2026-06-05.md
```
