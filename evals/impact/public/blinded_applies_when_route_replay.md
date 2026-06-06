# Blinded Applies-When Route Replay

This note summarizes a blinded route-quality replay experiment for `ai-wiki-toolkit`.

It is a follow-up to the earlier AI Wiki impact eval pilot, but it tests a different layer of the
system. The pilot asked whether ambient repo memory changed fresh coding-agent outcomes. This
experiment asks whether adding stage-aware routing metadata to existing memory improves the route
packet's precision on historical route traces.

## Question

Can blind, source-session-derived `applies_when` labels reduce route noise without using the route
answer key?

The expected product mechanism was:

- broad memory docs get stage-specific labels
- route packets select fewer adjacent but irrelevant docs
- precision improves without losing useful memory

## Protocol

The experiment used the existing strict 57-trace historical replay cohort.

Fixed conditions:

- trace cohort: 57 evaluable historical route traces
- catalog cutoff: `trace-routed-at`
- max selected docs: 6
- reranker: deterministic top-20 index-card reranker
- primary target selection: top docs by control replay selected-count frequency
- target selection did not use false-positive, useful, or missed-useful outcomes

The target set was the top 20 docs by control selected frequency. Those 20 docs represented 270 of
320 control selected-document exposures.

Source recovery:

- 15 of 20 target docs had recoverable source/write-back sessions and generated blind label packets
- 14 labels passed the mechanical audit and were applied as the treatment overlay
- 5 target docs had no original write-back session available: `constraints`, `workflows`,
  `decisions`, `conventions/package-managed-vs-user-owned-docs`, and
  `conventions/distribution-target-matrix-must-match-published-assets`

The blind label writer saw only a packet containing the target memory path, safe source-session
context up to the first write-back footer, and the label grammar. It did not see the 57 route prompts,
false-positive outcomes, missed-useful docs, precision reports, or future route research.

## Results

The first treatment did not improve route precision. It made precision slightly worse because the
router treated the entire `applies_when` label as plain positive hint text.

### Round 1: Flat Hint Scorer

| condition | traces | precision | noise | selected | selected useful | missed useful |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| control | 57 | 0.350 | 0.650 | 320 | 112 | 52 |
| treatment | 57 | 0.338 | 0.662 | 320 | 108 | 53 |

Paired trace comparison:

- wins: 3
- losses: 7
- ties: 47
- precision delta: -0.0125
- selected useful delta: -4
- missed useful delta: +1

### Round 2: Structured Applies-When Scorer

After the negative result, the scorer was changed to parse `applies_when` into a positive clause and
a negative boundary clause. The positive clause is available for normal hint matching. The negative
clause no longer boosts the document; if the task matches that boundary, the document receives a
penalty.

With the same 14-label treatment overlay:

| condition | traces | precision | noise | selected | selected useful | missed useful |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| control | 57 | 0.350 | 0.650 | 320 | 112 | 52 |
| treatment | 57 | 0.350 | 0.650 | 320 | 112 | 51 |

Paired trace comparison:

- wins: 3
- losses: 3
- ties: 51
- precision delta: 0.0000
- selected useful delta: 0
- missed useful delta: -1

### Round 3: Route-Side Action/Stage Alignment

The next scorer pass tightened the route side instead of only changing memory labels. The route
packet now extracts action/stage intent signals from the task, such as `design`, `implement`, `run`,
`report`, `label`, `manifest`, `prompt`, `artifact`, or `session`. For docs with `applies_when`, the
scorer compares those task intent terms against the positive clause. If a labeled doc has clear
action/stage terms but none align with the task, it receives a small mismatch penalty.

With the same 14-label treatment overlay:

| condition | traces | precision | noise | selected | selected useful | missed useful |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| control | 57 | 0.350 | 0.650 | 320 | 112 | 52 |
| treatment | 57 | 0.353 | 0.647 | 320 | 113 | 52 |

Paired trace comparison:

- wins: 4
- losses: 3
- ties: 50
- precision delta: +0.0031
- selected useful delta: +1
- missed useful delta: 0

## Interpretation

The negative first result was useful. It showed that simply adding text labels to memory is not
enough.

The flat-hint scorer treated `applies_when` as a plain `routing_hint`. That meant every token in the
label was available for positive matching. A label like:

```text
Evaluate route usefulness when comparing route-selected memories against actual reuse, misses, and
noisy selections; not for ordinary route invocation or general wiki reuse dashboards.
```

helps the right tasks in theory, but a flat scorer does not understand the negative boundary. Terms
in the exclusion clause, such as `route`, `reuse`, `dashboard`, or `ordinary`, can still widen
matching. In several Round 1 losses, newly labeled eval/product docs displaced more useful docs
rather than filtering noise.

The structured scorer fixed that failure mode: the treatment no longer hurt aggregate precision, and
missed useful docs dropped by one. But it still did not create a precision lift. The labels changed
some paired selections, but the wins and losses canceled out.

The route-side action/stage pass produced a small positive lift. This is not large enough to claim
that routing precision is fixed, but it supports the product hypothesis: stage-aware memory labels
need a route query model that distinguishes the task's action and workflow stage from broad topic
words like `eval`, `route`, `memory`, or `workflow`.

The result points to a sharper next hypothesis:

> Stage-aware metadata needs structured interpretation. `applies_when` should not be treated as one
> flat bag of positive tokens. Structured negative boundaries are only a guardrail. Positive stage
> alignment needs to be enforced on both sides: memory labels must be specific, and route prompts
> must be interpreted as actions/stages, not just topic bags.

## What Should Change Next

The next experiment should continue tightening both sides rather than keep rewriting labels alone:

- require action/stage alignment before boosting broad eval or memory drafts
- score label verbs and workflow stages separately from generic nouns
- treat `not_for` as a suppressor, not merely as a penalty, when the excluded stage is strongly
  matched
- avoid boosting labels from nouns alone; require action or stage alignment for broad eval/memory
  drafts
- give core docs a separate scope-label path, because they do not have source write-back sessions

The primary result here is not "labels alone improve precision." The defensible claim is:

> A blinded metadata-only treatment over 57 historical route traces first worsened precision under a
> flat hint scorer. A structured `applies_when` scorer removed that regression. Adding route-side
> action/stage alignment then produced a small precision lift, from `0.350` to `0.353`, without
> increasing missed useful docs. The next bottleneck is stronger positive alignment and selection
> policy, not more memory volume.

## Artifacts

Local reproducibility artifacts are under:

```text
evals/impact/experiments/applies_when_blind_2026_06/
```

Public-safe artifacts include:

- `manifest.json`
- `inputs/target_docs.json`
- `labels/treatment_overlay.json`
- `reports/control_vs_treatment.md`
- `reports/control_vs_treatment.json`

Raw label packets, raw labeler outputs, recovered source maps, and temporary worktrees are
local-only until scrubbed. They may contain local session excerpts and filesystem paths.
