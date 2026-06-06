---
title: "Route precision next method should use stage-slot selection"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "analysis"
status: "draft"
created_at: "2026-06-05T10:28:49+1000"
updated_at: "2026-06-06T14:18:00+1000"
promotion_candidate: false
promotion_basis: "Single follow-up analysis of the 57-trace blinded applies_when replay changed-precision pairs."
---

# Route Precision Next Method Should Use Stage-Slot Selection

## Context

After the blinded `applies_when` treatment and route-side action/stage alignment pass, the strict
57-trace route replay moved only slightly: precision changed from `0.350` to `0.353`, with `4` paired
wins, `3` paired losses, and `50` ties.

The next method question should not default to core-doc gating. The handoff asked for a concrete
read of the seven changed paired traces before choosing the next route precision method.

## Observation

The seven changed traces mostly show same-topic, different-stage competition inside eval/product
memory:

- Assessment/productization prompts can need product-MVP, prompt-design, route-usefulness, or
  workflow-comparison memory, but coarse `benchmark` / `evaluate` tokens also pull in adjacent
  family-scope or efficiency docs.
- Runner/scoring prompts can need manifest, first-pass artifact report, capture, manual cutoff, or
  comparison-mode docs, but current labels sometimes treat `run`, `report`, or broad `eval` as enough
  evidence for the wrong stage.
- Metrics and diagnostics prompts need a narrower distinction between public proof metrics,
  route-usefulness metrics, source-incident timing, neutral report quality, and consolidation design.
- Release-plus-eval tasks are mixed-intent; they need at least one release/distribution doc and one
  eval/trial doc, not six adjacent eval docs.

The wins happened when treatment swapped in a doc that covered the active stage or mixed subgoal,
such as distribution target guidance for a release task, route-usefulness memory for an evaluate-repo
prompt, or source-incident timing memory for Project A diagnostics.

The losses happened when coarse action tokens created false same-stage matches: `benchmark`,
`evaluate`, `run`, `report`, or `metrics` could admit family-scope, efficiency, consolidation, or
report-quality docs even when the task needed a different eval stage.

## Method Direction

The next route precision experiment should use mode-first routing, workflow-contract routing, and a
stage-slot selector. It should not be a global core-doc gate.

Core docs are a special case. `constraints`, `decisions`, and `workflows` can look like false
positives in selected-vs-reused telemetry, but some of that is intentional safety coverage. The next
method should distinguish "selected because this task is governed by a mandatory safety/workflow
contract" from "selected as generic discussion context." Do not optimize by blindly removing core
docs from packets.

Mode is a parent decision, not just another scoring feature. A prompt should first be interpreted
under a mode such as `plan`, `code`, `question_only`, `fixed_workflow`, `review`, or `report`. Only
then should docs compete inside the mode. "Think hard", "plan first", "do not code", "evaluate",
"decide", and "research" should make the task a planning or question mode unless the user also asks
for implementation.

Some workflow-like task families should stop competing as ordinary memory at all. Weekly reports,
promotion/reuse metrics, task checks, diagnostics provenance, release flow, and similar recurring
processes need explicit workflow contracts that the agent can follow and that evals can verify. For
those tasks, route should select the workflow contract first, then only add supporting docs when the
current task asks for a design change, debugging, or exception handling.

Candidate method:

1. Classify the task into a route mode before scoring docs. Modes can be `plan`, `code`,
   `question_only`, `fixed_workflow`, `review`, and `report`. Mode controls which workflow contracts
   and doc slots are eligible.
2. Detect fixed workflows before ordinary memory retrieval. If a prompt maps to a known workflow,
   select the workflow contract as the primary artifact and treat adjacent memory as supporting
   evidence only.
3. Split mixed-intent tasks into buckets before top-k selection, such as `release_distribution` plus
   `eval_report`. Each active bucket gets coverage before same-family extras are added.
4. Classify the task into one or more route slots, such as `assessment`, `prompt_design`,
   `manifest_or_runner`, `artifact_capture`, `rubric_scoring`, `report_quality`,
   `route_usefulness`, `source_incident_timing`, `public_metrics`, `release_distribution`, and
   `memory_consolidation`.
5. Classify candidate docs into the same slots from `applies_when`, `routing_hint`, title, kind, and
   historical support.
6. Apply incompatibility before final top-k selection: a doc in an adjacent eval slot should not
   displace a doc in the primary slot unless it has stronger task evidence or fills an explicit
   secondary slot.
7. Keep one or two docs per active slot before adding support/history candidates. This preserves
   mixed-intent coverage without filling the packet with same-family eval drafts.
8. Treat `not_for` as slot-level exclusion only when the excluded stage is strongly matched. Avoid
   penalizing a doc just because generic words such as `eval`, `run`, or `report` appear in both
   positive and negative clauses.
9. Add a workflow-contract layer for fixed processes. The test should verify agent behavior, not
   only selected-doc precision: did the agent enter the expected workflow, follow the required
   steps, and avoid reading adjacent design notes as substitutes for the workflow?
10. For plan / think-hard / no-code prompts, route in planning or question mode first. This is a
   prompt-mode decision, not a normal doc competition against implementation-stage memory.

## Experiment Shape

Evaluate this before coding a product change:

- replay the same 57-trace cohort with `catalog_cutoff=trace-routed-at`, `max_docs=6`, and the same
  treatment overlay
- report aggregate precision/noise, selected useful, missed useful, and selected count
- separately report the seven changed-precision traces and whether each loss was fixed without
  reversing any win
- add a per-slot diagnostic: primary slot selected, adjacent slot selected, mixed-intent slot filled,
  and selected-but-unused same-slot duplicates
- add a workflow-following diagnostic for fixed processes: expected workflow selected, required
  workflow steps followed, adjacent docs avoided unless justified, and no-code/planning constraints
  respected
- add behavior tests that run an agent-like harness over small tasks and judge whether the route
  packet caused the expected mode and workflow behavior, not just whether a selected document was
  later cited

This keeps the next method grounded in the observed paired traces instead of a general preference for
fewer docs, more labels, or core-doc gating.

## 2026-06-05 Implementation Result

The first implementation added mode-first routing, workflow contracts, intent buckets, doc slots,
selection reason types, behavior contracts, and trace/replay diagnostics for those fields.

Important refinement from the first replay attempt: fixed workflows should not keep selecting core
docs as ordinary selected context. If a task maps to a fixed workflow and does not ask to modify,
debug, or implement that workflow, route should output the workflow contract and abstain from
supporting docs. If the prompt asks to change the workflow, it should route in `code` mode and allow
supporting docs.

Verification after that refinement:

- targeted route and route-trace tests: `27 passed`
- full test suite: `312 passed, 1 skipped`
- strict 57-trace replay with `catalog_cutoff=trace-routed-at` and `rerank_top=20`:
  - replay precision `0.371`
  - replay noise `0.629`
  - selected docs `278`
  - selected useful docs `103`
  - missed useful docs `55`

This is a precision improvement over the earlier `0.350` / `0.353` route precision results, but it
is more conservative: selected useful docs dropped. Treat the next round as a precision/recall tradeoff
analysis, not as a final route fix.

## Future Redesign TODOs

These follow from the next design discussion and should be tested before another route-side rewrite:

1. Test whether the token/signal layer and baseline classification layer are actually useful as
   separate stages. Compare the current split pipeline against a merged signal-to-classification
   pipeline instead of assuming the split is necessary.
2. Design automatic taxonomy induction with a two-gate activation path. Gate 1 should identify a
   repeated unknown-task or unknown-doc cluster from traces, misses, false positives, and task
   language. Gate 2 should validate the generated category in shadow mode through replay or behavior
   tests before it becomes active. Do not require a human to manually create every new taxonomy item.
3. Separate taxonomy from `when / do / excluding` labels. Taxonomy decides what category exists;
   `when / do / excluding` describes when a known category or document should apply. Test whether the
   same label schema can help propose categories, but do not treat applicability labels as a complete
   replacement for taxonomy.
4. Verify whether explicit route-packet prompts can make the runtime agent switch behavior between
   planning and coding surfaces. Internal phases such as architecture, coding, validation, and PR
   work may need to map onto the actual runtime modes that Codex exposes.
5. Verify whether route-mode permissions can be enforced by prompt alone: read-only, edit-files,
   run-tests, git-write, push, and PR creation should be tested as behavioral constraints, not just
   packet metadata.
6. Replace unordered `intent_buckets` with a composable `phase_plan`. The plan should support
   optional phases, loops, skipped phases, and repo policy differences such as solo-development tasks
   that do not require PR creation.
7. Avoid hard-coding an Apex-like order. Use common phases such as init-branch, explore/analyze,
   plan, propose alternatives, execute, validate/review, fix, add tests, verify, and PR as a library
   of phase candidates that route can compose for the current prompt.
8. Add a CLI/debug surface that shows the runtime catalog/index cards built for the current task so
   the user can inspect doc kind, doc slots, routing hints, and applies_when before final selection.
9. Clarify the interaction between `doc_kind` and `doc_slots`. `doc_kind` carries ownership/trust
   and can affect permission or mandatory-read behavior; `doc_slots` should represent the task phase
   or context role the doc can support.
10. Run a scorer-versus-reranker ablation. Test whether the deterministic top-card reranker provides
   independent value or whether its specificity logic should be folded into the primary scorer.
11. Upgrade packet output to be phase-aware. Each phase should include `current_phase`, runtime mode,
   permissions, selected docs, exit criteria, and trace fields. Later phases should be regenerated
   after earlier phases produce new decisions or artifacts, rather than treated as a fixed full-plan
   prediction.
