# Coding Agent Eval Harness

This document packages the existing `ai-wiki-toolkit` impact-eval work as a coding-agent eval
harness. It is a Project A research artifact: task corpus, strategy matrix, metrics, reports,
failure taxonomy, current evidence, and the path from the current dogfood suite to a larger
20-50-task benchmark.

The harness evaluates coding-agent behavior on real historical repository failures. The current
question is:

> When a fresh coding-agent session receives the same task, does the repo-native AI wiki workflow
> help it avoid repeated mistakes, improve first-pass quality, or reduce unnecessary churn?

This is an agent-engineering eval. It is not a model leaderboard and not a statistically powered
claim about general coding ability.

## Current Status

The current suite has seven completed, six-slot, CLI-first benchmark families:

| metric | value |
| --- | --- |
| formal families | 7 |
| first-pass slots per family | 6 |
| captured first-pass attempts | 42 |
| primary strategies per family | 2 |
| diagnostic strategies per family | 4 |
| execution surface | Codex CLI |
| default model condition | `gpt-5.5`, `xhigh` reasoning |
| validation gate | exported session manifest plus `validate_run.py` |
| scoring labels | `success`, `partial`, `fail` |

The source material lives under:

- `evals/impact/families/`
- `evals/impact/prompts/`
- `evals/impact/notes/`
- `evals/impact/reports/current.md`
- `evals/impact/public/ai_wiki_impact_eval_pilot.md`
- `evals/impact/public/agent_failure_postmortem_pack.md`

## Task Corpus

Each family is based on a real historical problem from developing `ai-wiki-toolkit`. The family spec
defines the baseline commit, prompt family, memory fixtures, and exclusion rules used to construct
controlled workspace variants.

| family | task type | historical failure | expected behavior | primary result |
| --- | --- | --- | --- | --- |
| `ownership_boundary` | implementation surface | Contributor-only workflow implemented as package code | Keep helper repo-local under `scripts/` and docs; avoid package CLI/module changes | no AI wiki `fail`, ambient AI wiki `success` |
| `release_distribution_integrity` | release coordination | Public target matrix drift across workflows, npm, archives, docs, and smoke checks | Keep every public target aligned across release assets, npm metadata, Homebrew, docs, and verification | no AI wiki `partial`, ambient AI wiki `success` |
| `windows_arm_smoke_cli_output` | narrow CI fix | Smoke checks compared bare version instead of full CLI output | Compare against `ai-wiki-toolkit <version>` in both release-archive and npm-installed paths | both primary slots `success` |
| `release_runtime_compatibility` | release runtime | Linux binary published/installed successfully but failed on older runtime | Build on compatible baseline and run pre-publish runtime smoke checks | no AI wiki `partial`, ambient AI wiki `success` |
| `scaffold_prompt_workflow_compliance` | scaffold and prompt workflow | Scaffold/prompt changes drifted on names, skills, docs, or managed prompt boundaries | Preserve canonical areas, skill names, managed routing, docs, doctor checks, and tests | no AI wiki `partial`, ambient AI wiki `success` |
| `postinstall_archive_staging` | package wrapper bug | Postinstall extraction deleted its own downloaded archive | Stage archive outside the target directory and keep fix focused | both primary slots `success`; memory reduced churn |
| `aiwiki_evidence_integrity` | telemetry and auditability | Document reuse, task coverage, managed-doc exclusion, and write-back checks could blur together | Preserve per-handle evidence shards, `record-reuse-check`, managed-doc exclusion, and explicit write-back outcomes | no AI wiki `partial`, ambient AI wiki `success` |

## Strategy Matrix

Each family uses neutral slots. Semantic variant names stay outside workspace paths to reduce
treatment leakage.

| slot | strategy | role | purpose |
| --- | --- | --- | --- |
| `s01` | `no_aiwiki_workflow` | primary control | Fresh agent receives repo plus task, without AI wiki scaffold, memory, or skills |
| `s02` | `aiwiki_scaffold_no_target_memory` | diagnostic | AI wiki scaffold and non-target memory are present, but direct target memory is removed |
| `s03` | `aiwiki_linked_raw_only` | diagnostic | Raw source drafts for the target problem are present |
| `s04` | `aiwiki_linked_consolidated_only` | diagnostic | Consolidated or promoted memory for the target problem is present |
| `s05` | `aiwiki_ambient_memory_workflow` | primary treatment | Realistic AI wiki workflow with target, adjacent, and ambient repo memory available |
| `s06` | `aiwiki_scaffold_no_adjacent_memory` | diagnostic | AI wiki scaffold remains, but target and adjacent task-specific memory are removed |

The primary claim always comes from `s01` versus `s05`. Diagnostic slots explain mechanism and
noise; they are not promoted into the main causal conclusion.

## Run Protocol

The current formal protocol is Manual v2, CLI-first:

1. Choose a real historical problem and a baseline commit before the historical fix landed.
2. Define one `original.md` prompt that recreates the historical task without leaking the answer.
3. Prepare six neutral workspaces with controlled memory fixtures.
4. Run one fresh persisted Codex CLI session per slot.
5. Capture first-pass artifacts immediately.
6. Export visible sessions and a session manifest.
7. Validate confounds before scoring.
8. Score each slot as `success`, `partial`, or `fail` from diff, tests, artifacts, and transcript.
9. Generate product reports and cross-run summaries.

Useful commands:

```bash
aiwiki-toolkit eval impact families
aiwiki-toolkit eval impact family show ownership_boundary
aiwiki-toolkit eval impact plan --family ownership_boundary
aiwiki-toolkit eval impact prepare --family ownership_boundary
aiwiki-toolkit eval impact run --run-dir /path/to/run --all-slots
aiwiki-toolkit eval impact validate --run-dir /path/to/run
aiwiki-toolkit eval impact score --run-dir /path/to/run --slot s01 --prompt-level original --label fail
aiwiki-toolkit eval impact manifest --run-dir /path/to/run
aiwiki-toolkit eval impact report --run-dir /path/to/run
aiwiki-toolkit eval impact schedule report
aiwiki-toolkit eval impact route-noise report --since 30d
aiwiki-toolkit eval impact route-noise cohort --post-change-since 2026-06-04T08:20:53+10:00
aiwiki-toolkit eval impact route-noise replay --before 2026-06-04T08:20:53+10:00 --catalog-cutoff trace-routed-at --rerank-top 20
aiwiki-toolkit eval impact neutral report --period-id project-a-rerun-2026-06-03
```

## Metrics

The harness tracks three layers of evidence.

### Outcome Metrics

- first-attempt success rate
- average score, where `success=1.0`, `partial=0.5`, and `fail=0.0`
- primary outcome: positive, neutral, regression, or incomplete
- shareable-for-causal-claims flag from confound validation

### Workflow Metrics

- attempts
- human nudges
- first-pass versus final repair phase
- captured artifact coverage
- session export coverage
- critical confounds and warnings

### Change-Quality Metrics

- changed files
- untracked files
- project changed files
- managed AI wiki telemetry changes
- user-owned AI wiki file churn
- unnecessary implementation footprint

These metrics matter because a coding agent can pass the visible task while still creating future
maintenance cost.

## Failure Taxonomy

The current taxonomy comes from the postmortem pack:

| category | examples |
| --- | --- |
| eval harness leakage | baseline already contains the answer; prompt names intended surface |
| implementation-surface error | repo-local workflow becomes package code |
| memory specificity failure | consolidated guidance lacks concrete placement force |
| context-pruning failure | strict scaffold context removes adjacent memory needed for surface choice |
| release coordination miss | public target matrix updated but platform-specific setup missed |
| runtime compatibility miss | smoke gates added but build baseline remains incompatible |
| workflow/naming drift | scaffold areas, skill names, or managed routing diverge |
| evidence-integrity failure | task coverage and document reuse logs blur together |
| telemetry noise | not-helpful or flat shared logs weaken downstream diagnosis |
| change-quality churn | task succeeds but produces unnecessary user-owned docs or extra code footprint |

See `evals/impact/public/agent_failure_postmortem_pack.md` for the detailed case write-ups.

## Reporting Surfaces

The harness already exposes several report surfaces:

| surface | command or path | use |
| --- | --- | --- |
| family registry | `aiwiki-toolkit eval impact families` | Inspect runnable families and missing assets |
| family detail | `aiwiki-toolkit eval impact family show <family>` | Inspect prompt levels, memory fixtures, and next commands |
| run manifest | `aiwiki-toolkit eval impact manifest --run-dir <run>` | Audit baseline, prompt hashes, model, effort, slots, artifacts, and session export |
| product report | `aiwiki-toolkit eval impact report --run-dir <run>` | Compare primary variants and variant metrics |
| cross-run summary | `aiwiki-toolkit eval impact summarize --run-dir <run> ...` | Compare multiple runs |
| schedule report | `aiwiki-toolkit eval impact schedule report` | Review families, candidate queue, and recent runs |
| route-noise report | `aiwiki-toolkit eval impact route-noise report` | Aggregate route precision, selected-but-unused docs, missed useful docs, and noisy traces |
| route cohort report | `aiwiki-toolkit eval impact route-noise cohort --post-change-since <iso>` | Compare a fixed-size post-change evaluable cohort against a pre-change route baseline |
| historical route replay | `aiwiki-toolkit eval impact route-noise replay --before <iso> --catalog-cutoff trace-routed-at --rerank-top 20` | Recover historical route prompts from local Codex sessions, replay them through the current router, filter docs created after each original trace, rerank top index cards, and compare projected precision/noise against historical reuse events |
| neutral-family report | `aiwiki-toolkit eval impact neutral report --period-id <period>` | Expand neutral scheduled runs into primary slot scores, rubric judgments, change counts, and duration evidence |
| repo evaluation | `aiwiki-toolkit evaluate repo --since 30d` | Connect workflow coverage, route quality, memory quality, and eval readiness |
| public scorecard | `evals/impact/public/ai_wiki_impact_eval_pilot.md` | Explain external evidence and caveats |
| postmortem pack | `evals/impact/public/agent_failure_postmortem_pack.md` | Explain failure modes and robustness improvements |

This is already enough to support a VS Code agent-native advisor flow: run the deterministic reports,
then ask the IDE agent to read the generated Markdown/JSON and propose next eval or memory work.

## Current Evidence Boundaries

Reasonable to claim:

- The suite is an artifact-backed replay harness over real historical coding-agent failures.
- It compares no-AI-wiki and ambient-AI-wiki workflows under matched prompt/model/effort conditions.
- It has exposed concrete agent failure modes and eval-harness failure modes.
- It has produced directional positive signals on ownership boundaries, release coordination,
  release runtime compatibility, scaffold workflow discipline, and evidence integrity.
- Historical route replay can project whether a current router would have selected better memory for
  old tasks when prompt recovery has sufficient local Codex session provenance.

Not reasonable to claim yet:

- a statistically powered success-rate estimate
- a seed-controlled model comparison
- proof that AI wiki is necessary for every successful task
- broad external generalization beyond this repo
- a completed 20-50-task multi-repo benchmark
- that route replay is equivalent to a post-change production cohort; replay is retrospective and
  should stay labeled separately from new-task dogfood evidence

## Path To 20-50 Tasks

The next expansion should be incremental and evidence-gated:

1. Convert the current seven families into fully rubric-backed families by adding rubric JSON files.
2. Add prompt-variant replication for the strongest families:
   - original
   - concise
   - ambiguous
   - explicit but non-answer-leaking
3. Add 3-5 new real families from future source incidents using:
   - `aiwiki-toolkit eval impact family candidates`
   - `aiwiki-toolkit eval impact family draft`
   - `aiwiki-toolkit eval impact family promote`
4. Add one synthetic-but-realistic toy repo for repeatable permission, export, notification,
   reviewer-preference, and conflict-detection tasks.
5. Keep public claims separated by corpus:
   - dogfood historical repo failures
   - synthetic team-coding benchmark
   - external/open-source repo tasks, if later added

The target credible research milestone is:

- 20-50 tasks
- at least two primary strategies
- one fixed runner protocol
- written rubrics
- exported first-pass artifacts
- HTML or Markdown scorecard
- failure taxonomy
- postmortem updates after regressions

## Portfolio Summary

Project A is not starting from zero. In this repo, the core harness already exists:

- task families with historical baselines
- controlled memory variants
- CLI-first runner
- artifact capture
- session export
- confound validation
- manual and rubric-capable scoring
- product reports
- schedule reports
- candidate discovery from source incidents
- postmortem taxonomy

The remaining work is scale and polish: more tasks, rubric coverage, prompt robustness, cleaner
dashboarding, and at least one non-self-referential corpus.
