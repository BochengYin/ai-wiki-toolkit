---
title: "Route precision next method should use stage-slot selection"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "analysis"
status: "draft"
created_at: "2026-06-05T10:28:49+1000"
updated_at: "2026-06-07T11:40:00+1000"
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

## 2026-06-06 Design Refinement

Two refinements should guide the next router design.

First, taxonomy should be induced from trace evidence, but new categories should not become active
from a single task. End-of-task checks can record unknown task language, false positives, missed
useful docs, and user corrections as taxonomy evidence. Repeated evidence can form a
`TaxonomyCandidate`, but that candidate should only become active after shadow replay or behavior
tests show an improvement without regressions.

`when / do / excluding` labels are applicability labels, not taxonomy itself. They can describe when
a category or document applies and can help propose a category, but the taxonomy layer still needs a
separate identity, kind, positive and negative examples, activation status, and validation history.

Second, compound prompts should use phase rerouting instead of a fixed full-plan prediction. Route
should generate the current phase with mode, permissions, docs, goal, and exit criteria. After the
phase completes, the runtime should reroute using the original task, phase outputs, changed paths,
unresolved criteria, and user feedback to generate the next phase. This supports optional phases,
skipped phases, and loops such as implement -> validate -> fix -> validate.

Codex runtime compatibility is an acceptance requirement, not an optional fallback. The design
should verify whether route packets can reliably control Codex planning, coding, validation, git, and
push/PR behavior. If prompt-visible phase contracts are not strong enough on Codex, the method should
use a stronger Codex-specific adapter or harness rather than treating the behavior as unsupported.

## 2026-06-06 Codex Runtime Capability Smoke Result

The first Codex runtime capability smoke test used isolated temporary git repositories and
`codex exec` with broad local permissions so behavior came from prompt-visible route packets rather
than filesystem sandbox enforcement.

The smoke covered six phase boundaries: read-only planning, code edit plus test, validation-only,
local commit without push, commit plus push to a local bare remote, and PR-summary without calling
`gh`. All six passed. The result supports trying prompt-visible phase contracts as the first
`phase_plan` implementation path.

Important caveats:

- This does not prove that Codex exposes a public runtime API for mode, goals, or permissions.
- The validation-only case generated `__pycache__/` while running pytest, so the permission schema
  should distinguish source edits, generated test artifacts, git index writes, commits, pushes, and
  PR/API calls.
- The router still misclassified planning requests as `code` / `bug_fix` during this work, so the
  next bottleneck is generating the right phase packet from natural prompts.

The report is `evals/impact/reports/codex_runtime_capability_2026-06-06.md`.

## 2026-06-06 Route Self-Audit Implementation Result

The next router pass fixed the planning-only `code` / `bug_fix` misclassification by separating
route labels mentioned in the prompt from actual user intent. Prompts that ask why a route was
classified as `code/bug_fix` now record `mentioned_labels` and exclude those label tokens from the
intent classifier instead of treating them as implementation requests.

The implementation also added task-type arbitration and a packet-level `route_self_audit`:

- `task_type_arbitration` explains when a route label mention and planning mode adjust a coarse
  task type such as `bug_fix` into `memory_governance`.
- `route_self_audit` reports suspicious packet contradictions such as label-as-intent, plan-vs-bug
  task type conflicts, or weak workflow triggers.
- Suspicious audits include a taxonomy-evidence candidate, but they do not activate taxonomy.
- Route traces now store `route_self_audit` so repeated mismatches can feed later
  TaxonomyCandidate induction.

The fixed regression cases are:

- "搞清楚为什么 ... code/bug_fix ..." now routes as `memory_governance` with `mode=plan`.
- "不要直接实现，先研究 ... code/bug_fix ..." now routes as `memory_governance` with
  `mode=plan`.
- The Codex runtime capability prompt no longer triggers the `diagnostics-provenance` fixed
  workflow from the broad Chinese `验证` synonym.
- The real weekly report workflow still triggers `weekly-report-diagnostics`.

Verification:

- targeted route and route-trace tests: `31 passed`

## 2026-06-06 TaxonomyCandidate Induction Implementation Result

The next step implemented Gate 1 candidate induction from taxonomy post-hoc evidence. The toolkit
now reads per-handle append-only evidence logs under `ai-wiki/metrics/taxonomy-evidence/<handle>.jsonl`
and generates inactive `TaxonomyCandidate` reports under
`ai-wiki/_toolkit/reports/taxonomy-candidates/<handle-or-all>/`.

The implementation deliberately does not write active taxonomy. Candidate reports include
`category_id`, `kind`, `status`, `when`, `do`, `excluding`, positive examples, negative examples,
source evidence ids, Gate 1 evidence summary, and Gate 2 validation status. Gate 1 requires repeated
coherent evidence. Single signals are rejected as insufficient evidence so one-off task language does
not pollute taxonomy.

Gate 2 is represented as an external shadow replay or behavior-test result. A candidate can move from
`proposed` to `shadow` only when the supplied validation shows improvement with zero regressions. If a
candidate improves a local case but causes any regression, it remains `proposed` and non-active.

New command:

- `aiwiki-toolkit taxonomy candidates --handle <handle> --format json --no-write`
- `aiwiki-toolkit taxonomy candidates --handle <handle> --shadow-validation-json validation.json --write`

Fixed regression coverage:

- repeated `route_phase_planning` evidence induces a proposed candidate.
- single evidence does not induce a candidate.
- Gate 2 pass marks a candidate as `shadow`, not active.
- Gate 2 regression keeps a candidate `proposed`.
- managed reports write under `_toolkit/reports` without creating `ai-wiki/taxonomy` or
  `_toolkit/taxonomy`.

Verification:

- taxonomy candidate tests: `5 passed`
- taxonomy evidence, init, and doctor tests: `24 passed`
- full test suite: `325 passed, 1 skipped`

## 2026-06-06 PhasePlan Shadow Output Implementation Result

The next step upgraded unordered `intent_buckets` into a phase-aware shadow output without replacing
the active bucket selector. Route packets now include top-level `phase_plan` with
`schema_version=route-phase-plan-v1`, `status=shadow`, `active=false`, and
`replaces_intent_buckets=false`.

Each current phase includes:

- `id`
- `agent_surface_mode` mapped to the Codex-visible `plan` or `code` surface
- `permissions` with allowed and disallowed actions
- `workflow_contract_id`
- `intent_bucket_ids`
- `docs`
- `goal`
- `acceptance_criteria`
- `exit_criteria`
- `next_phase_inputs`

The implementation keeps future phases as candidates only. It records that the next phase should be
regenerated after the current phase completes using the original task, current phase result, changed
paths, unresolved acceptance criteria, and user feedback.

Important behavior decisions:

- Plan-only / no-code prompts produce `current_phase=plan`, `agent_surface_mode=plan`, and
  `edit_files` disallowed.
- Compound prompts can produce ordered phase candidates such as `plan -> code -> validate -> git`.
  Negated phases such as "do not push" are omitted.
- Fixed workflow contracts produce a `workflow` phase only when the route mode is actually
  `fixed_workflow`. A release workflow contract should not override an explicit "plan, then
  implement, then test" sequence.
- The route mode classifier now treats `upgrade` as an implementation signal so prompts like
  "Upgrade unordered intent_buckets into phase-aware shadow output" route to `code` instead of
  planning-only mode.

The shadow output is rendered in the Markdown packet, included in JSON packets, persisted in route
traces, and copied into route replay diagnostics. It is intentionally not used to change selected
docs yet.

Fixed regression coverage:

- plan-only Chinese prompt routes to a read-only plan phase.
- compound prompt preserves explicit phase order and does not include negated push.
- fixed weekly report workflow wraps the workflow contract as the current phase.
- route traces persist `phase_plan`.

Verification:

- focused route and route-trace tests: `34 passed`
- init, doctor, install/uninstall tests: `38 passed`
- full test suite: `328 passed, 1 skipped`

## 2026-06-06 Behavior Test Harness Implementation Result

The next step implemented route behavior tests as a separate eval/report surface instead of treating
selected-doc precision as the only success signal.

New command:

- `aiwiki-toolkit eval impact route-noise behavior --suite <suite.json> --format json`

The behavior harness reads a suite of route tasks plus observed agent events, generates route packets
when needed, and evaluates checks such as:

- workflow contract recognition
- required workflow steps followed
- no-edit compliance
- validation phase ran tests without feature edits
- adjacent design notes were not selected or opened as workflow substitutes
- push/PR did not happen when disallowed

The report includes pass/fail status, failure reason, failure source, failure plan, and whether the
failure blocks activation. Any failed behavior check sets `blocks_activation=true`, and the report
states that behavior failures prevent marking a route change successful or active.

The first phase-plan shadow suite is:

```text
evals/impact/route_behavior/phase_plan_shadow_suite_2026-06-06.json
```

Generated reports:

```text
evals/impact/reports/route_behavior_tests_2026-06-06.md
evals/impact/reports/route_behavior_tests_2026-06-06.json
```

Result:

- cases: `4`
- passed cases: `4`
- failed cases: `0`
- failed checks: `0`
- blocks activation: `false`
- activation status: `eligible_for_shadow_validation`

The behavior report still does not activate anything. It explicitly says activation still requires
replay and product review. During report generation, the suite exposed one route-mode issue:
`只要计划，不要实现` produced `current_phase=plan` but `route_mode=code`. The fix added `只要计划` and
`不要实现` to route-mode plan phrases, so the plan-only case now reports both `route_mode=plan` and
`current_phase=plan`.

Verification:

- route behavior tests: `2 passed`
- focused route/behavior/replay/init regressions: `76 passed`
- full test suite: `330 passed, 1 skipped`

## 2026-06-06 Replay + Behavior Activation Decision

The next step added a combined activation decision report that consumes both historical route replay
and behavior-test reports. This makes activation a product decision gate instead of a manual reading
of selected-doc precision.

Activation is only allowed when all of these conditions pass:

1. Behavior tests have zero failed checks and do not set `blocks_activation=true`.
2. Behavior coverage includes the configured minimum case count.
3. Replay covers at least the configured historical trace count.
4. Replay precision does not regress.
5. Replay noise does not increase.
6. Selected useful docs do not decrease unless the threshold is explicitly relaxed.
7. Missed useful docs do not increase unless the threshold is explicitly relaxed.
8. Per-trace precision and noise regressions stay within configured tolerances.

Passing the report only recommends activation. It does not mutate active taxonomy, active route
logic, or shared user-owned docs.

New command:

```text
aiwiki-toolkit eval impact route-noise activation \
  --replay-report evals/impact/reports/route_replay_phase_plan_2026-06-06.json \
  --behavior-report evals/impact/reports/route_behavior_tests_2026-06-06.json \
  --handle bochengyin \
  --write
```

Generated reports:

```text
evals/impact/reports/route_replay_phase_plan_2026-06-06.md
evals/impact/reports/route_replay_phase_plan_2026-06-06.json
evals/impact/reports/route_activation_decision_2026-06-06.md
evals/impact/reports/route_activation_decision_2026-06-06.json
ai-wiki/_toolkit/reports/route-activation/bochengyin/latest.md
ai-wiki/_toolkit/reports/route-activation/bochengyin/latest.json
```

Result:

- behavior cases: `4`
- behavior failed checks: `0`
- replayed traces: `57`
- precision delta: `-0.186`
- noise delta: `0.186`
- selected useful delta: `-77`
- missed useful delta: `16`
- precision regression items: `5`
- noise regression items: `5`
- decision: `blocked`

The behavior gate passed, but replay blocked activation. The current phase-plan/route changes should
remain shadow research outputs until replay precision, noise, useful-doc recall, and per-trace
regressions are fixed. This is a useful result: it prevents a behavior-only win from being mistaken
for a route-quality activation.

## 2026-06-07 Layered Metrics And Workflow Support Split

The next implementation split fixed workflow contracts from supporting document retrieval. A fixed
workflow match now remains a behavior contract that the agent must follow, but it no longer forces
`selected_doc_count=0` for workflows whose primary bucket can provide supporting evidence.

Before this change, fixed workflow traces such as release, promotion, and diagnostics provenance
could return no selected docs because the selector treated the workflow contract as a substitute for
supporting docs. After this change, the contract stays separate and the selector can still pick
slot-matched supporting docs:

- `memory-promotion` can pick memory/reuse metrics support.
- `release-flow` can pick release distribution support.
- `diagnostics-provenance` can pick source incident timing support.
- generic workflow contracts still avoid adjacent design notes when no support request is present.

The replay report now also separates ordinary retrieval from mandatory/core context:

- `retrieval_precision` excludes `mandatory_contract` and `safety_guardrail` docs from the
  denominator.
- `mandatory_contract`, `safety_guardrail`, and `background_reference` are counted separately by
  `selection_reason_type`.
- core docs selected-but-unused are reported as context noise instead of being mixed silently into
  ordinary retrieval precision.
- per-trace regression counts are computed over the full replayed cohort, not only the truncated
  display rows.

Verification:

- focused route/replay/activation tests: `45 passed`
- full test suite: `337 passed, 1 skipped`

Layered replay outputs:

```text
evals/impact/reports/route_replay_layered_old_strict_57_2026-06-07.md
evals/impact/reports/route_replay_layered_latest_2026-06-07.md
evals/impact/reports/route_activation_decision_layered_old_strict_57_2026-06-07.md
evals/impact/reports/route_activation_decision_layered_2026-06-07.md
```

Result on the old strict 57 cohort:

- baseline precision: `0.535`
- baseline retrieval precision: `0.498`
- replay precision: `0.355`
- replay retrieval precision: `0.351`
- selected useful delta: `-75`
- missed useful delta: `15`
- precision regression items: `34`
- decision: `blocked`

Result on the latest 57 cohort:

- baseline precision: `0.538`
- baseline retrieval precision: `0.502`
- replay precision: `0.353`
- replay retrieval precision: `0.348`
- selected useful delta: `-75`
- missed useful delta: `15`
- precision regression items: `34`
- decision: `blocked`

This confirms the fixed-workflow zero-doc issue was real and is now narrower, but it was not the
main source of the route precision regression. The larger remaining problem is still eval-stage
soup: prompts and docs share broad `eval/report/run/metrics` terms while needing different workflow
stages. The next method should prioritize eval-stage classification and stage-compatible doc slots,
then run ablations for fixed-workflow support, core safety selection, eval bucket selection, rerank,
and route-quality history adjustment on both fixed cohorts.

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
   work must map onto the actual runtime modes that Codex exposes; Codex compatibility is a required
   acceptance test, not an optional fallback.
5. Verify whether route-mode permissions can be enforced by prompt alone: read-only, edit-files,
   run-tests, git-write, push, and PR creation should be tested as behavioral constraints, not just
   packet metadata. If prompt-only control fails on Codex, design a stronger Codex-specific adapter
   or harness.
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

## 2026-06-07 Eval-Stage Ablation Result

The eval-stage classifier and stage-compatible doc-slot selector were implemented as an ablation
surface. The classifier is shadow by default; only the `stage_compatible_doc_slots` variant enforces
stage compatibility during document selection.

Reports:

```text
evals/impact/reports/route_eval_stage_ablation_old_strict_57_2026-06-07.md
evals/impact/reports/route_eval_stage_ablation_latest_57_2026-06-07.md
```

Old strict 57:

- current retrieval precision: `0.363`
- current eval-stage compatibility: `0.707`
- current incompatible eval docs: `39`
- `stage_compatible_doc_slots` retrieval precision: `0.353`
- `stage_compatible_doc_slots` useful delta vs current: `-2`
- `stage_compatible_doc_slots` missed useful delta vs current: `3`
- `stage_compatible_doc_slots` incompatible eval docs: `0`

Latest 57:

- current retrieval precision: `0.360`
- current eval-stage compatibility: `0.710`
- current incompatible eval docs: `40`
- `stage_compatible_doc_slots` retrieval precision: `0.354`
- `stage_compatible_doc_slots` useful delta vs current: `-1`
- `stage_compatible_doc_slots` missed useful delta vs current: `2`
- `stage_compatible_doc_slots` incompatible eval docs: `0`

Conclusion: stage-compatible hard filtering proves the diagnosis but is not an activation-ready
selector. It eliminates eval-stage incompatible docs, but it also loses useful docs and increases
missed useful docs on both cohorts. The next method should not activate hard stage filtering. It
should use eval stage as a soft scoring feature, a bucket tie-breaker, or an abstention/maybe-load
boundary, then test whether that preserves useful docs while reducing off-stage prompt-design and
artifact-capture confusion.

The dominant off-diagonal pair remains `manifest_or_runner -> prompt_design`, with secondary
confusion around `manifest_or_runner -> artifact_capture` and
`source_incident_timing -> manifest_or_runner`. These pairs should drive the next targeted
classifier/scorer tests.

## 2026-06-07 Eval-Stage Soft Scoring Result

The follow-up implementation added `eval_stage_soft_scoring` as an ablation variant instead of
activating it as the default router. Soft scoring uses eval stage in three places:

- same-stage docs receive a small score boost
- adjacent eval-stage docs receive a small penalty instead of being filtered out
- intent buckets and equal-score docs use eval-stage compatibility as a tie-breaker
- adjacent-stage docs that still have meaningful signal can appear in `maybe_load`

This directly targets the main off-diagonal pair `manifest_or_runner -> prompt_design` without
deleting prompt-design docs from the packet.

Old strict 57:

- current retrieval precision: `0.363`
- soft retrieval precision: `0.363`
- soft selected useful delta vs current: `+1`
- soft missed useful delta vs current: `+2`
- incompatible eval docs: `39 -> 19`
- `manifest_or_runner -> prompt_design`: `12 -> 5`

Latest 57:

- current retrieval precision: `0.360`
- soft retrieval precision: `0.364`
- soft selected useful delta vs current: `+2`
- soft missed useful delta vs current: `+1`
- precision regression items: `34 -> 33`
- incompatible eval docs: `40 -> 19`
- `manifest_or_runner -> prompt_design`: `12 -> 5`

Conclusion: soft scoring is the best candidate so far, but still should not activate automatically.
It improves stage compatibility and preserves or increases selected useful docs, but it increases
missed useful docs on both cohorts. The next step should inspect the newly missed useful docs and
decide whether `maybe_load` should count as recoverable support or whether the stage penalty/secondary
stage logic needs tuning.
