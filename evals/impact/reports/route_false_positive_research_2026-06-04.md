# Route False-Positive Research Report

- Generated from: `evals/impact/reports/historical_route_replay_2026-06-04.json`
- Cohort: strict temporal replay of the latest 57 pre-change evaluable route traces before `2026-06-04T08:20:53+10:00`
- Router: current scorer with conservative Chinese/mixed-language signals, support-aware route quality, multi-signal protection, deterministic top-card reranker, and `--catalog-cutoff trace-routed-at`

## Executive Finding

The low precision is not caused by one bad document. The replay selected `320` docs; `112` were useful and `208` were false positives (`207` unused plus `1` not-helpful). Route precision is `0.350` and noise is `0.650`.

The false positives are concentrated but not singular: `43` unique docs account for the `208` false-positive selections. The top 5 docs account for `67` false positives (`32.2%`), and the top 10 account for `117` (`56.2%`).

The main root cause is a label-and-logic interaction: many high-value drafts have broad titles/descriptions like `impact eval`, `report`, `workflow`, `metric`, `source incident`, and `memory diagnostics`. The router correctly recognizes them as adjacent, but the card labels do not encode which stage they apply to. A flat top-k scorer then selects several adjacent eval/memory drafts where only one stage-specific memory was useful.

## Measurement Caveats

- `selected_but_unused` means no downstream `record-reuse` event was logged for that doc in the same task. It can include docs that were skimmed but not recorded.
- Historical traces before this work did not always contain original task text; this replay recovered prompts from local Codex sessions. Recovery is good enough for diagnosis, but still not the same as live production routing.
- Some tasks are discussion/application/strategy prompts where AI Wiki may correctly have little to offer. A router that always fills 3-6 docs will look noisy on those tasks.

## Aggregate Slices

| replay task type | traces | selected | useful selected | precision | noise | missed useful |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| bug_fix | 4 | 24 | 10 | 0.417 | 0.583 | 4 |
| eval_workflow | 26 | 153 | 63 | 0.412 | 0.588 | 23 |
| general | 5 | 18 | 7 | 0.389 | 0.611 | 2 |
| memory_governance | 7 | 42 | 9 | 0.214 | 0.786 | 8 |
| release_distribution | 4 | 24 | 10 | 0.417 | 0.583 | 1 |
| scaffold_prompt_workflow | 11 | 59 | 13 | 0.220 | 0.780 | 14 |

| doc kind | selected | useful selected | false positives | precision |
| --- | ---: | ---: | ---: | ---: |
| draft | 243 | 87 | 156 | 0.358 |
| constraints | 24 | 13 | 11 | 0.542 |
| workflows | 17 | 3 | 14 | 0.176 |
| convention | 17 | 5 | 12 | 0.294 |
| decisions | 15 | 3 | 12 | 0.200 |
| problem | 1 | 0 | 1 | 0.000 |
| repo_index | 1 | 0 | 1 | 0.000 |
| convention_index | 1 | 0 | 1 | 0.000 |
| metrics_index | 1 | 1 | 0 | 1.000 |

Key interpretation: drafts dominate because most useful working memory is in drafts, but draft labels are also where most false positives come from. Core docs (`constraints`, `decisions`, `workflows`) are sometimes necessary but often selected as a safety blanket.

## Ablation Evidence

| variant | selected | useful selected | precision | noise | missed useful | interpretation |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| current max_docs=6 | 320 | 112 | 0.350 | 0.650 | 52 | Baseline for this report. |
| max_docs=3 | 171 | 74 | 0.433 | 0.567 | 74 | Fewer docs increases precision but drops recall sharply. |
| max_docs=4 | 222 | 87 | 0.392 | 0.608 | 67 | Better precision, still worse recall. |
| max_docs=5 | 272 | 100 | 0.368 | 0.632 | 60 | Middle tradeoff. |
| max_docs=8 | 415 | 123 | 0.296 | 0.704 | 47 | More docs improves recall slightly but produces heavy noise. |
| no multi-signal boost | 317 | 110 | 0.347 | 0.653 | 54 | Multi-signal is not the main noise source; removing it slightly hurts. |
| no route-quality adjustment | 324 | 116 | 0.358 | 0.642 | 55 | Route-quality currently trades precision for recall; it boosts some docs that later become false positives. |
| no multi-signal and no route-quality | 317 | 112 | 0.353 | 0.647 | 56 | Net effect is small; stage labels/top-k policy matter more. |

## False-Positive Hotspots

| doc | kind | selected | useful | false positives | missed | current label signal | recommended fix |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `people/bochengyin/drafts/impact-eval-prompts-should-backsolve-from-concrete-history` | draft | 22 | 6 | 16 | 1 | We started designing manual impact-eval prompts for `ai-wiki-toolkit` and initially framed the benchmark aroun | Add `applies_when`: manual prompt design from concrete historical tasks; down-rank for runner/report/capture implementation tasks. |
| `workflows` | workflows | 17 | 3 | 14 | 1 | These are repeatable repo-specific workflows worth following when changing scaffold behavior or cutting releas | Route as required only for explicit workflow/release/scaffold operations; otherwise maybe-load. This is route logic, not label-only. |
| `people/bochengyin/drafts/impact-eval-result-capture-must-include-untracked-files` | draft | 14 | 1 | 13 | 0 | While reviewing saved artifacts for the `ownership_boundary` impact experiment, we noticed that `save_result.p | Scope to result capture/save_result/untracked artifact bugs; avoid general eval planning. |
| `decisions` | decisions | 15 | 3 | 12 | 0 | Capture durable architectural and process decisions here. | Route only when prompt asks about architecture/process decisions or ownership constraints; otherwise maybe-load. |
| `people/bochengyin/drafts/trial-error-reduction-should-extend-memory-diagnostics` | draft | 20 | 8 | 12 | 0 | While discussing `eval-as-product-mvp`, we clarified that `trial_and_error_reduction` is not primarily a new b | Scope to trial/error metric extraction and memory diagnostics, not every eval workflow. |
| `constraints` | constraints | 24 | 13 | 11 | 5 | These are repo-specific constraints that should be treated as hard boundaries. | Keep protected but require explicit risk or implementation surface; do not use as default discussion context. |
| `people/bochengyin/drafts/source-incident-timing-needs-provenance` | draft | 13 | 2 | 11 | 1 | While adding source incident trial/error timing to impact-eval discovery, the local telemetry could identify r | Scope to source_session/source_incident/timing provenance; down-rank for generic eval/report work. |
| `people/bochengyin/drafts/neutral-impact-eval-runs-need-change-profile-quality-metrics` | draft | 11 | 1 | 10 | 0 | The `postinstall_archive_staging` impact eval produced a neutral first-attempt result: all six slots fixed the | Scope to neutral/quality-profile eval analysis; do not match generic quality/report terms alone. |
| `people/bochengyin/drafts/efficiency-eval-should-include-source-incident-cost` | draft | 15 | 6 | 9 | 1 | When evaluating AI wiki efficiency, formal replay comparisons between `no_aiwiki_workflow` and `aiwiki_ambient | Scope to source incident cost and efficiency claims; separate from general eval productization. |
| `people/bochengyin/drafts/workflow-primary-impact-evals-compare-working-modes` | draft | 16 | 7 | 9 | 3 | While redesigning the `ai-wiki-toolkit` impact eval flow, we clarified that the main product question is not w | Scope to comparing working modes, not every workflow/eval implementation. |
| `people/bochengyin/drafts/manual-impact-evals-need-visible-session-export-and-first-pass-cutoff` | draft | 12 | 4 | 8 | 2 | While documenting the first manual impact-eval round for `ownership_boundary` and `release_distribution_integr | Add or tighten `applies_when`/`routing_hint`; require stronger card-level match before top-k selection. |
| `conventions/package-managed-vs-user-owned-docs` | convention | 9 | 2 | 7 | 2 | Repo-wide package design for AI wiki ownership boundaries. | Good authoritative label, but user_owned_docs risk is too broad; route logic should require ownership action words. |
| `people/bochengyin/drafts/eval-product-run-requests-need-family-scope-check` | draft | 18 | 11 | 7 | 2 | After running `eval-as-product-mvp` locally, the report used the existing five captured impact-eval families.  | Add or tighten `applies_when`/`routing_hint`; require stronger card-level match before top-k selection. |
| `people/bochengyin/drafts/eval-product-mvp-starts-with-first-attempt-artifact-report` | draft | 9 | 4 | 5 | 6 | While turning `eval-as-product-mvp` into code, the product question was whether AI wiki should evaluate by exp | Add or tighten `applies_when`/`routing_hint`; require stronger card-level match before top-k selection. |
| `people/bochengyin/drafts/consolidation-should-layer-over-end-of-task-capture-and-avoid-shared-doc-churn` | draft | 7 | 2 | 5 | 2 | We considered adding a Karpathy-style memory consolidation feature to `ai-wiki-toolkit` after comparing the cu | Add or tighten `applies_when`/`routing_hint`; require stronger card-level match before top-k selection. |
| `conventions/distribution-target-matrix-must-match-published-assets` | convention | 8 | 3 | 5 | 1 | Release and package distribution for `ai-wiki-toolkit`. | Add or tighten `applies_when`/`routing_hint`; require stronger card-level match before top-k selection. |
| `people/bochengyin/drafts/eval-run-manifest-should-precede-auto-runner` | draft | 24 | 19 | 5 | 0 | While productizing the impact-eval harness beyond `eval impact report`, the next step could have been a full ` | High-support doc; keep but make stage-aware so it does not crowd out capture/discovery/source-incident docs. |
| `people/bochengyin/drafts/memory-compilation-mvp-needs-eval-gated-benefit` | draft | 4 | 0 | 4 | 1 | While discussing `memory-compilation-mvp`, the user challenged the assumption that compiling stable Markdown i | Add or tighten `applies_when`/`routing_hint`; require stronger card-level match before top-k selection. |
| `people/bochengyin/drafts/local-dogfooding-should-check-source-cli-vs-installed-entrypoint` | draft | 5 | 1 | 4 | 1 | While evaluating whether `ai-wiki-toolkit` is useful, the PATH executable came from a local installed entrypoint rather than the source checkout | Add or tighten `applies_when`/`routing_hint`; require stronger card-level match before top-k selection. |
| `people/bochengyin/drafts/feedback-diagnosis-mvp-should-start-as-explicit-generated-report` | draft | 3 | 0 | 3 | 0 | The `feedback-diagnosis-report` roadmap item asks the toolkit to diagnose missed, stale, noisy, conflicting, a | Add or tighten `applies_when`/`routing_hint`; require stronger card-level match before top-k selection. |

## Root-Cause Hypotheses

### H1: Stage granularity is missing from eval-memory labels

Evidence: the top false-positive docs are mostly eval/productization drafts. They are real, useful memories, but they cover different stages: prompt design, manifest, runner, capture, scoring, discovery, source-incident timing, and report interpretation. The route card layer mostly exposes broad nouns, so every eval task sees several adjacent memories as plausible.

Fix direction: add structured `applies_when` or `routing_hint` values to high-traffic eval docs. The labels should name the workflow stage and negative boundary, for example: `Use for manual prompt design from concrete historical tasks; not for runner implementation, result capture, or discovery reports.`

### H2: Core docs need an abstention/maybe-load policy

Evidence: `workflows`, `decisions`, and `constraints` generated many false positives. `constraints` still has decent precision because it is genuinely protective, but `workflows` and `decisions` are too often selected for discussion-only or strategy prompts.

Fix direction: core docs should be selected only when the prompt has an implementation/release/scaffold/ownership action. Otherwise they should appear in `maybe_load` or be represented as a one-line reminder, not counted as selected context.

### H3: CJK and discussion prompts need abstention, not just synonyms

Evidence: CJK traces have precision `0.267` versus `0.407` for non-CJK. The worst examples are short or discussion-like prompts: `好 那你说说...`, `评估...先不要代码`, application form advice, or product strategy. More synonyms can create false positives; the `本地` ownership false positive already proved this.

Fix direction: add a low-confidence route mode for short CJK/discussion prompts. It should select fewer docs and prefer asking the agent to inspect prior conversation/session context rather than filling top-k from broad toolkit labels.

### H4: Support-aware route quality should distinguish support type

Evidence: disabling route-quality adjustment improves precision from `0.350` to `0.358` but increases missed useful from `52` to `55`. The adjustment helps recall, but the missed-useful bonus can reinforce broadly useful docs in the wrong subtask.

Fix direction: route quality support should be conditioned on task subtype or matched stage. A doc useful for `eval manifest` should not get the same boost for `eval source incident timing` just because both contain `eval`.

### H5: Flat top-k is the wrong final selector for multi-intent tasks

Evidence: release/eval mixed tasks often need one release constraint, one workflow/PR doc, and one eval/report doc. Flat scoring can choose six adjacent eval drafts or six release/package docs instead of covering subgoals.

Fix direction: after scoring, apply diversity quotas by intent bucket: core constraint, primary task stage, secondary risk tag, and historical support. This is safer than simply lowering `max_docs`.

## Recommended Next Experiments

1. Label first: add `applies_when`/`routing_hint` to the top 10 false-positive docs, especially eval-stage docs. Rerun strict 57-trace replay.
2. Logic second: implement an abstention policy for discussion-only/short CJK prompts and core docs. Measure precision, missed useful, and selected count together.
3. Selector third: replace flat top-k with bucketed selection for eval workflow stages and mixed release/eval tasks.
4. Route-quality fourth: make support-aware adjustment conditional on stage match rather than raw doc-level history.
5. Measurement: require live post-change cohorts to record consulted docs; otherwise selected-but-unused may remain a noisy proxy.

## Appendix A: All 57 Trace Diagnoses

### 01. `promote-draft-ai-wiki-people-bochengyin-index-md`

- Prompt: 检查是否已有自动 promote draft 到 ai-wiki/people/bochengyin/index.md 的机制
- Replay: task_type `memory_governance`, risk tags `ci_workflow, memory_governance, user_owned_docs`, precision `0.167`, noise `0.833`
- Useful selected: `people/bochengyin/drafts/user-owned-ai-wiki-index-should-not-be-an-upgrade-surface`
- False positives: `people/bochengyin/drafts/context-routing-budget-should-be-sparse-and-index-backed`; `people/bochengyin/drafts/eval-product-mvp-starts-with-first-attempt-artifact-report`; `people/bochengyin/drafts/feedback-diagnosis-mvp-should-start-as-explicit-generated-report`; `people/bochengyin/drafts/impact-eval-result-capture-must-include-untracked-files`; `people/bochengyin/drafts/karpathy-skills-suggest-success-criteria-and-cross-agent-packaging`
- Missed useful: `people/bochengyin/drafts/consolidation-should-layer-over-end-of-task-capture-and-avoid-shared-doc-churn`; `people/bochengyin/index`
- Hypothesis: Memory/eval/provenance vocabulary overlaps; broad diagnostic drafts compete without stage-specific labels.

### 02. `draft-reuse-3-promote`

- Prompt: 查找是否有 draft reuse 超过 3 次就应该 promote 的历史记录
- Replay: task_type `memory_governance`, risk tags `memory_governance`, precision `0.000`, noise `1.000`
- Useful selected: -
- False positives: `people/bochengyin/drafts/ai-wiki-reuse-metrics-should-exclude-managed-docs-and-shard-by-handle`; `people/bochengyin/drafts/codex-session-recovery-should-search-jsonl-and-state-db`; `people/bochengyin/drafts/consolidation-should-layer-over-end-of-task-capture-and-avoid-shared-doc-churn`; `people/bochengyin/drafts/impact-eval-result-capture-must-include-untracked-files`; `people/bochengyin/drafts/karpathy-skills-suggest-success-criteria-and-cross-agent-packaging`; `people/bochengyin/drafts/linux-release-binaries-need-runtime-checks-against-an-older-glibc-baseline`
- Missed useful: `conventions/index`; `people/bochengyin/drafts/agent-framework-layers-should-guide-ai-wiki-toolkit-roadmap`; `people/bochengyin/drafts/consolidation-review-queue-should-use-diagnostics-as-prioritization-layer`; `work/events/bochengyin`
- Hypothesis: Missed-useful docs point to weak target labels or missing session/work-context signals.

### 03. `code`

- Prompt: 好 那你说说我们现在还有什么是需要 code 进去的。
- Replay: task_type `general`, risk tags `none`, precision `0.000`, noise `1.000`
- Useful selected: -
- False positives: `constraints`; `decisions`; `workflows`
- Missed useful: `people/bochengyin/drafts/ai-wiki-reuse-metrics-should-exclude-managed-docs-and-shard-by-handle`; `people/bochengyin/drafts/ai-wiki-usefulness-metrics-need-task-level-checks-plus-doc-events`
- Hypothesis: Core-doc fallback on underspecified or discussion-only prompt; route should abstain or return fewer selected docs.

### 04. `weekly-report-saved-time-coverage-promotion-noisy-diagnosis-telemetry-provenance`

- Prompt: 把 weekly report 从 saved-time 改成 coverage/promotion/noisy diagnosis，并加入 telemetry provenance 和 candidate not_helpful 支持
- Replay: task_type `memory_governance`, risk tags `memory_governance`, precision `0.000`, noise `1.000`
- Useful selected: -
- False positives: `people/bochengyin/drafts/context-routing-budget-should-be-sparse-and-index-backed`; `people/bochengyin/drafts/efficiency-eval-should-include-source-incident-cost`; `people/bochengyin/drafts/end-of-task-ai-wiki-update-check-must-always-run`; `people/bochengyin/drafts/eval-product-mvp-starts-with-first-attempt-artifact-report`; `people/bochengyin/drafts/feedback-diagnosis-mvp-should-start-as-explicit-generated-report`; `people/bochengyin/drafts/npm-postinstall-must-not-delete-its-own-download-archive`
- Missed useful: `people/bochengyin/drafts/ai-wiki-reuse-metrics-should-exclude-managed-docs-and-shard-by-handle`; `people/bochengyin/drafts/ai-wiki-usefulness-metrics-need-task-level-checks-plus-doc-events`
- Hypothesis: Memory/eval/provenance vocabulary overlaps; broad diagnostic drafts compete without stage-specific labels.

### 05. `karpathy-ai-wiki-toolkit`

- Prompt: 联网搜索 Karpathy 最近在研究什么，并基于结果思考 ai-wiki-toolkit 可以怎么进步
- Replay: task_type `scaffold_prompt_workflow`, risk tags `user_owned_docs`, precision `0.333`, noise `0.667`
- Useful selected: `people/bochengyin/drafts/consolidation-should-layer-over-end-of-task-capture-and-avoid-shared-doc-churn`; `people/bochengyin/drafts/karpathy-skills-suggest-success-criteria-and-cross-agent-packaging`
- False positives: `constraints`; `decisions`; `workflows`; `conventions/distribution-target-matrix-must-match-published-assets`
- Missed useful: -
- Hypothesis: Toolkit/user-owned risk tags over-protect core docs; label/logic should distinguish product strategy from scaffold edits.

### 06. `karpathy-html-markdown-ai-wiki-agent-memory-ai-wiki-toolkit-html`

- Prompt: 讨论 Karpathy 认为 HTML 比 Markdown 更适合作为 AI wiki/agent memory 载体，并判断 ai-wiki-toolkit 是否应该转向 HTML
- Replay: task_type `scaffold_prompt_workflow`, risk tags `managed_prompt_block, memory_governance, user_owned_docs`, precision `0.333`, noise `0.667`
- Useful selected: `people/bochengyin/drafts/consolidation-should-layer-over-end-of-task-capture-and-avoid-shared-doc-churn`; `people/bochengyin/drafts/karpathy-skills-suggest-success-criteria-and-cross-agent-packaging`
- False positives: `constraints`; `decisions`; `people/bochengyin/drafts/memory-compilation-mvp-needs-eval-gated-benefit`; `people/bochengyin/drafts/workflow-primary-impact-evals-compare-working-modes`
- Missed useful: -
- Hypothesis: Toolkit/user-owned risk tags over-protect core docs; label/logic should distinguish product strategy from scaffold edits.

### 07. `weekly-html-report-self-involving`

- Prompt: 修改 weekly HTML report，只显示需要用户 self-involving 的可行动数据，去掉省多少时间等效率估算展示
- Replay: task_type `general`, risk tags `none`, precision `0.000`, noise `1.000`
- Useful selected: -
- False positives: `constraints`; `decisions`; `workflows`
- Missed useful: -
- Hypothesis: Core-doc fallback on underspecified or discussion-only prompt; route should abstain or return fewer selected docs.

### 08. `ai-wiki-toolkit-ai-wiki-toolkit-handle-git-conflict`

- Prompt: 团队接入 ai-wiki-toolkit 时，评估 ai-wiki/_toolkit 生成物是否应该按 handle 分区以避免 git conflict，并提出/实现必要改动
- Replay: task_type `scaffold_prompt_workflow`, risk tags `user_owned_docs`, precision `0.000`, noise `1.000`
- Useful selected: -
- False positives: `constraints`; `conventions/distribution-target-matrix-must-match-published-assets`; `decisions`; `people/bochengyin/drafts/consolidation-should-layer-over-end-of-task-capture-and-avoid-shared-doc-churn`; `people/bochengyin/drafts/managed-toolkit-workflows-need-a-toc-and-scope-aware-conflict-checks`; `workflows`
- Missed useful: -
- Hypothesis: Toolkit/user-owned risk tags over-protect core docs; label/logic should distinguish product strategy from scaffold edits.

### 09. `push-current-changes-and-release-a-new-version`

- Prompt: push current changes and release a new version
- Replay: task_type `release_distribution`, risk tags `release_distribution`, precision `0.167`, noise `0.833`
- Useful selected: `people/bochengyin/drafts/linux-release-binaries-need-runtime-checks-against-an-older-glibc-baseline`
- False positives: `constraints`; `conventions/distribution-target-matrix-must-match-published-assets`; `conventions/package-managed-vs-user-owned-docs`; `problems/linux-musl-pyinstaller-needs-binutils-objdump`; `workflows`
- Missed useful: -
- Hypothesis: Release task is multi-intent; release conventions, package docs, and PR-flow docs need subgoal quotas instead of one flat top-k.

### 10. `evaluate-another-agent-s-assessment-that-ai-wiki-toolkit-has-first-version-workf`

- Prompt: Evaluate another agent's assessment that ai-wiki-toolkit has first-version workflow eval infrastructure and should next productize/researchize it into a continuous benchmark/eval engine, including whether GPU investment is needed.
- Replay: task_type `eval_workflow`, risk tags `ci_workflow, managed_prompt_block, release_distribution, task_evaluation, user_owned_docs`, precision `0.667`, noise `0.333`
- Useful selected: `people/bochengyin/drafts/eval-product-mvp-starts-with-first-attempt-artifact-report`; `people/bochengyin/drafts/impact-eval-prompts-should-backsolve-from-concrete-history`; `people/bochengyin/drafts/route-usefulness-eval-needs-route-traces-and-actual-use-comparison`; `people/bochengyin/drafts/workflow-primary-impact-evals-compare-working-modes`
- False positives: `people/bochengyin/drafts/computer-use-vscode-codex-multiline-prompts-need-clipboard-paste`; `people/bochengyin/drafts/trial-error-reduction-should-extend-memory-diagnostics`
- Missed useful: -
- Hypothesis: Likely measurement/context limitation or broad lexical overlap; inspect prompt context before changing scorer.

### 11. `implement-the-next-eval-productization-slice-after-eval-impact-report-add-lightw`

- Prompt: Implement the next eval productization slice after eval impact report: add lightweight impact eval manifest/schema support rather than full auto-running agent benchmark.
- Replay: task_type `eval_workflow`, risk tags `managed_prompt_block, task_evaluation`, precision `0.333`, noise `0.667`
- Useful selected: `people/bochengyin/drafts/eval-product-mvp-starts-with-first-attempt-artifact-report`; `people/bochengyin/drafts/eval-product-run-requests-need-family-scope-check`
- False positives: `people/bochengyin/drafts/computer-use-vscode-codex-multiline-prompts-need-clipboard-paste`; `people/bochengyin/drafts/impact-eval-prompts-should-backsolve-from-concrete-history`; `people/bochengyin/drafts/manual-impact-evals-need-visible-session-export-and-first-pass-cutoff`; `people/bochengyin/drafts/workflow-primary-impact-evals-compare-working-modes`
- Missed useful: -
- Hypothesis: Eval-stage granularity missing: broad eval drafts match every eval task, but only one workflow stage is actually useful.

### 12. `continue-eval-productization-after-adding-eval-impact-manifest-implement-the-nex`

- Prompt: Continue eval productization after adding eval impact manifest: implement the next safe orchestrator/run-plan slice for impact evals without auto-invoking agents yet.
- Replay: task_type `eval_workflow`, risk tags `managed_prompt_block, task_evaluation`, precision `0.500`, noise `0.500`
- Useful selected: `people/bochengyin/drafts/eval-run-manifest-should-precede-auto-runner`; `people/bochengyin/drafts/manual-impact-evals-need-visible-session-export-and-first-pass-cutoff`; `people/bochengyin/drafts/workflow-primary-impact-evals-compare-working-modes`
- False positives: `people/bochengyin/drafts/adjacent-consolidated-guidance-can-underperform-task-specific-raw-drafts-in-impact-evals`; `people/bochengyin/drafts/impact-eval-prompts-should-backsolve-from-concrete-history`; `people/bochengyin/drafts/neutral-impact-eval-runs-need-change-profile-quality-metrics`
- Missed useful: -
- Hypothesis: Eval-stage granularity missing: broad eval drafts match every eval task, but only one workflow stage is actually useful.

### 13. `decide-the-next-implementation-step-after-adding-eval-impact-manifest-and-eval-i`

- Prompt: Decide the next implementation step after adding eval impact manifest and eval impact plan for ai-wiki-toolkit eval productization.
- Replay: task_type `eval_workflow`, risk tags `task_evaluation, user_owned_docs`, precision `0.167`, noise `0.833`
- Useful selected: `people/bochengyin/drafts/eval-run-manifest-should-precede-auto-runner`
- False positives: `people/bochengyin/drafts/adjacent-consolidated-guidance-can-underperform-task-specific-raw-drafts-in-impact-evals`; `people/bochengyin/drafts/impact-eval-prompts-should-backsolve-from-concrete-history`; `people/bochengyin/drafts/impact-eval-result-capture-must-include-untracked-files`; `people/bochengyin/drafts/neutral-impact-eval-runs-need-change-profile-quality-metrics`; `people/bochengyin/drafts/workflow-primary-impact-evals-compare-working-modes`
- Missed useful: -
- Hypothesis: Eval-stage granularity missing: broad eval drafts match every eval task, but only one workflow stage is actually useful.

### 14. `implement-eval-impact-prepare-command-after-eval-impact-plan-create-workspaces-a`

- Prompt: Implement eval impact prepare command after eval impact plan: create workspaces and run skeleton from existing impact eval family scripts, without invoking agents.
- Replay: task_type `eval_workflow`, risk tags `managed_prompt_block, task_evaluation`, precision `0.167`, noise `0.833`
- Useful selected: `people/bochengyin/drafts/eval-run-manifest-should-precede-auto-runner`
- False positives: `people/bochengyin/drafts/eval-product-run-requests-need-family-scope-check`; `people/bochengyin/drafts/impact-eval-no-target-aiwiki-slots-must-exclude-task-specific-workflow-memory`; `people/bochengyin/drafts/impact-eval-prompts-should-backsolve-from-concrete-history`; `people/bochengyin/drafts/manual-impact-evals-need-visible-session-export-and-first-pass-cutoff`; `people/bochengyin/drafts/workflow-primary-impact-evals-compare-working-modes`
- Missed useful: -
- Hypothesis: Eval-stage granularity missing: broad eval drafts match every eval task, but only one workflow stage is actually useful.

### 15. `decide-next-step-after-implementing-eval-impact-plan-prepare-manifest-report-sum`

- Prompt: Decide next step after implementing eval impact plan, prepare, manifest, report, summarize for ai-wiki-toolkit eval productization.
- Replay: task_type `eval_workflow`, risk tags `task_evaluation, user_owned_docs`, precision `0.167`, noise `0.833`
- Useful selected: `people/bochengyin/drafts/eval-run-manifest-should-precede-auto-runner`
- False positives: `people/bochengyin/drafts/impact-eval-prompts-should-backsolve-from-concrete-history`; `people/bochengyin/drafts/impact-eval-result-capture-must-include-untracked-files`; `people/bochengyin/drafts/manual-impact-evals-need-visible-session-export-and-first-pass-cutoff`; `people/bochengyin/drafts/neutral-impact-eval-runs-need-change-profile-quality-metrics`; `people/bochengyin/drafts/workflow-primary-impact-evals-compare-working-modes`
- Missed useful: -
- Hypothesis: Eval-stage granularity missing: broad eval drafts match every eval task, but only one workflow stage is actually useful.

### 16. `complete-eval-impact-automation-lifecycle-by-adding-capture-validate-and-score-c`

- Prompt: Complete eval impact automation lifecycle by adding capture, validate, and score commands, then run an end-to-end smoke test proving the artifact pipeline works.
- Replay: task_type `eval_workflow`, risk tags `ci_workflow, task_evaluation`, precision `0.667`, noise `0.333`
- Useful selected: `people/bochengyin/drafts/eval-product-mvp-starts-with-first-attempt-artifact-report`; `people/bochengyin/drafts/eval-product-run-requests-need-family-scope-check`; `people/bochengyin/drafts/eval-run-manifest-should-precede-auto-runner`; `people/bochengyin/drafts/manual-impact-evals-need-visible-session-export-and-first-pass-cutoff`
- False positives: `people/bochengyin/drafts/consolidation-should-layer-over-end-of-task-capture-and-avoid-shared-doc-churn`; `people/bochengyin/drafts/impact-eval-result-capture-must-include-untracked-files`
- Missed useful: `constraints`; `conventions/package-managed-vs-user-owned-docs`; `people/bochengyin/drafts/workflow-primary-impact-evals-compare-working-modes`
- Hypothesis: Missed-useful docs point to weak target labels or missing session/work-context signals.

### 17. `implement-the-three-step-autonomous-impact-eval-runner-v0-single-slot-run-v1-all`

- Prompt: Implement the three-step autonomous impact eval runner: v0 single-slot run, v1 all-slots run, and v2 transcript export validate score policy baseline comparison report bundle, with tests and real smoke verification.
- Replay: task_type `eval_workflow`, risk tags `ci_workflow, task_evaluation`, precision `0.667`, noise `0.333`
- Useful selected: `people/bochengyin/drafts/eval-run-manifest-should-precede-auto-runner`; `people/bochengyin/drafts/impact-eval-prompts-should-backsolve-from-concrete-history`; `people/bochengyin/drafts/manual-impact-evals-need-visible-session-export-and-first-pass-cutoff`; `people/bochengyin/drafts/workflow-primary-impact-evals-compare-working-modes`
- False positives: `people/bochengyin/drafts/impact-eval-no-target-aiwiki-slots-must-exclude-task-specific-workflow-memory`; `people/bochengyin/drafts/neutral-impact-eval-runs-need-change-profile-quality-metrics`
- Missed useful: `constraints`; `conventions/package-managed-vs-user-owned-docs`; `people/bochengyin/drafts/eval-product-mvp-starts-with-first-attempt-artifact-report`; `people/bochengyin/drafts/eval-product-run-requests-need-family-scope-check`
- Hypothesis: Missed-useful docs point to weak target labels or missing session/work-context signals.

### 18. `add-a-rubric-judge-scoring-policy-to-the-autonomous-impact-eval-runner-so-eval-i`

- Prompt: Add a rubric judge scoring policy to the autonomous impact eval runner so eval impact run can score captured first-pass artifacts from rubric definitions, with tests and smoke verification.
- Replay: task_type `eval_workflow`, risk tags `ci_workflow, task_evaluation`, precision `0.667`, noise `0.333`
- Useful selected: `people/bochengyin/drafts/eval-run-manifest-should-precede-auto-runner`; `people/bochengyin/drafts/impact-eval-result-capture-must-include-untracked-files`; `people/bochengyin/drafts/manual-impact-evals-need-visible-session-export-and-first-pass-cutoff`; `people/bochengyin/drafts/workflow-primary-impact-evals-compare-working-modes`
- False positives: `people/bochengyin/drafts/eval-product-run-requests-need-family-scope-check`; `people/bochengyin/drafts/impact-eval-prompts-should-backsolve-from-concrete-history`
- Missed useful: `constraints`; `people/bochengyin/drafts/eval-product-mvp-starts-with-first-attempt-artifact-report`
- Hypothesis: Missed-useful docs point to weak target labels or missing session/work-context signals.

### 19. `answer-whether-the-current-ai-wiki-toolkit-can-be-downloaded-installed-and-used`

- Prompt: Answer whether the current ai-wiki toolkit can be downloaded, installed, and used by users to run local impact evaluation.
- Replay: task_type `eval_workflow`, risk tags `task_evaluation, user_owned_docs`, precision `0.333`, noise `0.667`
- Useful selected: `people/bochengyin/drafts/eval-run-manifest-should-precede-auto-runner`; `people/bochengyin/drafts/local-dogfooding-should-check-source-cli-vs-installed-entrypoint`
- False positives: `people/bochengyin/drafts/eval-product-run-requests-need-family-scope-check`; `people/bochengyin/drafts/manual-impact-evals-need-visible-session-export-and-first-pass-cutoff`; `people/bochengyin/drafts/neutral-impact-eval-runs-need-change-profile-quality-metrics`; `people/bochengyin/drafts/workflow-primary-impact-evals-compare-working-modes`
- Missed useful: `people/bochengyin/drafts/eval-product-mvp-starts-with-first-attempt-artifact-report`
- Hypothesis: Eval-stage granularity missing: broad eval drafts match every eval task, but only one workflow stage is actually useful.

### 20. `clarify-whether-users-must-run-plan-prepare-run-report-separately-or-whether-the`

- Prompt: Clarify whether users must run plan prepare run report separately or whether the current eval impact runner can one-click run a whole benchmark family.
- Replay: task_type `eval_workflow`, risk tags `task_evaluation`, precision `0.167`, noise `0.833`
- Useful selected: `people/bochengyin/drafts/eval-run-manifest-should-precede-auto-runner`
- False positives: `people/bochengyin/drafts/eval-product-run-requests-need-family-scope-check`; `people/bochengyin/drafts/impact-eval-prompts-should-backsolve-from-concrete-history`; `people/bochengyin/drafts/impact-eval-result-capture-must-include-untracked-files`; `people/bochengyin/drafts/trial-error-reduction-should-extend-memory-diagnostics`; `people/bochengyin/drafts/workflow-primary-impact-evals-compare-working-modes`
- Missed useful: `people/bochengyin/drafts/eval-product-mvp-starts-with-first-attempt-artifact-report`
- Hypothesis: Eval-stage granularity missing: broad eval drafts match every eval task, but only one workflow stage is actually useful.

### 21. `explain-with-examples-which-parts-of-eval-impact-workflow-are-currently-automate`

- Prompt: Explain with examples which parts of eval impact workflow are currently automated and which still require separate commands.
- Replay: task_type `eval_workflow`, risk tags `ci_workflow, task_evaluation`, precision `0.333`, noise `0.667`
- Useful selected: `people/bochengyin/drafts/eval-run-manifest-should-precede-auto-runner`; `people/bochengyin/drafts/workflow-primary-impact-evals-compare-working-modes`
- False positives: `people/bochengyin/drafts/computer-use-vscode-codex-multiline-prompts-need-clipboard-paste`; `people/bochengyin/drafts/impact-eval-prompts-should-backsolve-from-concrete-history`; `people/bochengyin/drafts/impact-eval-result-capture-must-include-untracked-files`; `people/bochengyin/drafts/neutral-impact-eval-runs-need-change-profile-quality-metrics`
- Missed useful: -
- Hypothesis: Eval-stage granularity missing: broad eval drafts match every eval task, but only one workflow stage is actually useful.

### 22. `clarify-whether-eval-impact-users-need-a-family-discovery-command-before-they-ca`

- Prompt: Clarify whether eval impact users need a family discovery command before they can run ownership_boundary or other benchmark families.
- Replay: task_type `eval_workflow`, risk tags `task_evaluation`, precision `0.333`, noise `0.667`
- Useful selected: `people/bochengyin/drafts/eval-product-run-requests-need-family-scope-check`; `people/bochengyin/drafts/eval-run-manifest-should-precede-auto-runner`
- False positives: `people/bochengyin/drafts/adjacent-consolidated-guidance-can-underperform-task-specific-raw-drafts-in-impact-evals`; `people/bochengyin/drafts/impact-eval-prompts-should-backsolve-from-concrete-history`; `people/bochengyin/drafts/impact-eval-result-capture-must-include-untracked-files`; `people/bochengyin/drafts/manual-impact-evals-need-visible-session-export-and-first-pass-cutoff`
- Missed useful: -
- Hypothesis: Eval-stage granularity missing: broad eval drafts match every eval task, but only one workflow stage is actually useful.

### 23. `design-the-eval-impact-family-discovery-step-including-how-it-should-identify-tr`

- Prompt: Design the eval impact family discovery step, including how it should identify trial-and-error memory candidates before running evaluation.
- Replay: task_type `eval_workflow`, risk tags `memory_governance, task_evaluation`, precision `0.667`, noise `0.333`
- Useful selected: `people/bochengyin/drafts/eval-product-run-requests-need-family-scope-check`; `people/bochengyin/drafts/eval-run-manifest-should-precede-auto-runner`; `people/bochengyin/drafts/trial-error-reduction-should-extend-memory-diagnostics`; `people/bochengyin/drafts/workflow-primary-impact-evals-compare-working-modes`
- False positives: `people/bochengyin/drafts/efficiency-eval-should-include-source-incident-cost`; `people/bochengyin/drafts/impact-eval-prompts-should-backsolve-from-concrete-history`
- Missed useful: -
- Hypothesis: Broad eval/research draft labels dominate through shared terms such as eval, report, replay, metric, and workflow.

### 24. `identify-what-the-current-project-still-needs-to-implement-eval-impact-family-di`

- Prompt: Identify what the current project still needs to implement eval impact family discovery and trial-error candidate discovery.
- Replay: task_type `eval_workflow`, risk tags `task_evaluation`, precision `0.667`, noise `0.333`
- Useful selected: `people/bochengyin/drafts/eval-product-run-requests-need-family-scope-check`; `people/bochengyin/drafts/eval-run-manifest-should-precede-auto-runner`; `people/bochengyin/drafts/trial-error-reduction-should-extend-memory-diagnostics`; `people/bochengyin/drafts/workflow-primary-impact-evals-compare-working-modes`
- False positives: `people/bochengyin/drafts/impact-eval-prompts-should-backsolve-from-concrete-history`; `people/bochengyin/drafts/route-usefulness-eval-needs-route-traces-and-actual-use-comparison`
- Missed useful: `constraints`
- Hypothesis: Missed-useful docs point to weak target labels or missing session/work-context signals.

### 25. `implement-eval-impact-family-discovery-trial-error-candidate-discovery-family-le`

- Prompt: Implement eval impact family discovery, trial-error candidate discovery, family-level benchmark runner, and candidate family init with docs and tests.
- Replay: task_type `eval_workflow`, risk tags `task_evaluation`, precision `0.667`, noise `0.333`
- Useful selected: `people/bochengyin/drafts/eval-product-run-requests-need-family-scope-check`; `people/bochengyin/drafts/eval-run-manifest-should-precede-auto-runner`; `people/bochengyin/drafts/impact-eval-prompts-should-backsolve-from-concrete-history`; `people/bochengyin/drafts/trial-error-reduction-should-extend-memory-diagnostics`
- False positives: `people/bochengyin/drafts/impact-eval-result-capture-must-include-untracked-files`; `people/bochengyin/drafts/workflow-primary-impact-evals-compare-working-modes`
- Missed useful: -
- Hypothesis: Broad eval/research draft labels dominate through shared terms such as eval, report, replay, metric, and workflow.

### 26. `clarify-roadmap-for-continuous-automatic-discovery-of-new-impact-eval-families-a`

- Prompt: Clarify roadmap for continuous automatic discovery of new impact eval families, automatic family crystallization, and scheduled periodic benchmark reports.
- Replay: task_type `eval_workflow`, risk tags `task_evaluation`, precision `0.500`, noise `0.500`
- Useful selected: `people/bochengyin/drafts/eval-product-run-requests-need-family-scope-check`; `people/bochengyin/drafts/eval-run-manifest-should-precede-auto-runner`; `people/bochengyin/drafts/impact-eval-prompts-should-backsolve-from-concrete-history`
- False positives: `people/bochengyin/drafts/impact-eval-result-capture-must-include-untracked-files`; `people/bochengyin/drafts/trial-error-reduction-should-extend-memory-diagnostics`; `people/bochengyin/drafts/workflow-primary-impact-evals-compare-working-modes`
- Missed useful: -
- Hypothesis: Eval-stage granularity missing: broad eval drafts match every eval task, but only one workflow stage is actually useful.

### 27. `build-a-continuous-impact-eval-loop-automatically-discover-new-eval-families-fro`

- Prompt: Build a continuous impact eval loop: automatically discover new eval families from trial/error evidence, persist candidate queue and drafts, gate promotion, and run scheduled benchmark reports.
- Replay: task_type `eval_workflow`, risk tags `memory_governance, task_evaluation`, precision `0.667`, noise `0.333`
- Useful selected: `people/bochengyin/drafts/eval-product-run-requests-need-family-scope-check`; `people/bochengyin/drafts/eval-run-manifest-should-precede-auto-runner`; `people/bochengyin/drafts/impact-eval-prompts-should-backsolve-from-concrete-history`; `people/bochengyin/drafts/trial-error-reduction-should-extend-memory-diagnostics`
- False positives: `people/bochengyin/drafts/impact-eval-result-capture-must-include-untracked-files`; `people/bochengyin/drafts/neutral-impact-eval-runs-need-change-profile-quality-metrics`
- Missed useful: `people/bochengyin/drafts/manual-impact-evals-need-visible-session-export-and-first-pass-cutoff`; `people/bochengyin/drafts/workflow-primary-impact-evals-compare-working-modes`
- Hypothesis: Missed-useful docs point to weak target labels or missing session/work-context signals.

### 28. `push-the-continuous-impact-eval-loop-changes-reinstall-the-local-aiwiki-toolkit`

- Prompt: Push the continuous impact eval loop changes, reinstall the local aiwiki-toolkit package from this repo, then run the new discovery/schedule feature end to end to find trial and error candidates.
- Replay: task_type `eval_workflow`, risk tags `release_distribution, task_evaluation, user_owned_docs`, precision `0.333`, noise `0.667`
- Useful selected: `people/bochengyin/drafts/eval-run-manifest-should-precede-auto-runner`
- False positives: `people/bochengyin/drafts/source-incident-timing-needs-provenance`; `people/bochengyin/drafts/trial-error-reduction-should-extend-memory-diagnostics`
- Missed useful: `constraints`; `conventions/distribution-target-matrix-must-match-published-assets`; `problems/windows-arm-smoke-version-checks-need-full-cli-output`
- Hypothesis: Missed-useful docs point to weak target labels or missing session/work-context signals.

### 29. `merge-pr-73-release-ai-wiki-toolkit-to-npm-update-the-local-installed-package-th`

- Prompt: Merge PR 73, release ai-wiki-toolkit to npm, update the local installed package, then run a formal end-to-end automated trial/error report using the new impact eval workflow.
- Replay: task_type `eval_workflow`, risk tags `ci_workflow, release_distribution, task_evaluation, user_owned_docs`, precision `0.000`, noise `1.000`
- Useful selected: -
- False positives: `people/bochengyin/drafts/eval-product-run-requests-need-family-scope-check`; `people/bochengyin/drafts/eval-run-manifest-should-precede-auto-runner`; `people/bochengyin/drafts/impact-eval-prompts-should-backsolve-from-concrete-history`; `people/bochengyin/drafts/manual-impact-evals-need-visible-session-export-and-first-pass-cutoff`; `people/bochengyin/drafts/neutral-impact-eval-runs-need-change-profile-quality-metrics`; `people/bochengyin/drafts/trial-error-reduction-should-extend-memory-diagnostics`
- Missed useful: `workflows`
- Hypothesis: Eval-stage granularity missing: broad eval drafts match every eval task, but only one workflow stage is actually useful.

### 30. `explain-the-discovered-continuous-impact-eval-candidates-their-underlying-proble`

- Prompt: Explain the discovered continuous impact eval candidates: their underlying problem, trial/error history, and available time-cost evidence.
- Replay: task_type `eval_workflow`, risk tags `task_evaluation`, precision `0.667`, noise `0.333`
- Useful selected: `people/bochengyin/drafts/efficiency-eval-should-include-source-incident-cost`; `people/bochengyin/drafts/eval-product-run-requests-need-family-scope-check`; `people/bochengyin/drafts/eval-run-manifest-should-precede-auto-runner`; `people/bochengyin/drafts/impact-eval-prompts-should-backsolve-from-concrete-history`
- False positives: `people/bochengyin/drafts/source-incident-timing-needs-provenance`; `people/bochengyin/drafts/trial-error-reduction-should-extend-memory-diagnostics`
- Missed useful: `people/bochengyin/drafts/consolidation-should-layer-over-end-of-task-capture-and-avoid-shared-doc-churn`; `people/bochengyin/drafts/local-dogfooding-should-check-source-cli-vs-installed-entrypoint`; `people/bochengyin/drafts/memory-compilation-mvp-needs-eval-gated-benefit`
- Hypothesis: Missed-useful docs point to weak target labels or missing session/work-context signals.

### 31. `implement-source-incident-trial-error-timing-extraction-for-impact-eval-candidat`

- Prompt: Implement source incident trial/error timing extraction for impact eval candidates, so discovery reports estimate how long the original problem took to diagnose and solve when timing evidence exists.
- Replay: task_type `eval_workflow`, risk tags `task_evaluation`, precision `0.500`, noise `0.500`
- Useful selected: `people/bochengyin/drafts/efficiency-eval-should-include-source-incident-cost`; `people/bochengyin/drafts/eval-product-run-requests-need-family-scope-check`; `people/bochengyin/drafts/trial-error-reduction-should-extend-memory-diagnostics`
- False positives: `people/bochengyin/drafts/eval-run-manifest-should-precede-auto-runner`; `people/bochengyin/drafts/memory-compilation-mvp-needs-eval-gated-benefit`; `people/bochengyin/drafts/source-incident-timing-needs-provenance`
- Missed useful: `people/bochengyin/drafts/codex-session-recovery-should-search-jsonl-and-state-db`
- Hypothesis: Eval-stage granularity missing: broad eval drafts match every eval task, but only one workflow stage is actually useful.

### 32. `implement-source-incident-trial-error-timing-extraction-for-impact-eval-candidat`

- Prompt: Implement source incident trial/error timing extraction for impact eval candidates, so discovery reports estimate how long the original problem took to diagnose and solve when timing evidence exists.
- Replay: task_type `eval_workflow`, risk tags `task_evaluation`, precision `0.500`, noise `0.500`
- Useful selected: `people/bochengyin/drafts/efficiency-eval-should-include-source-incident-cost`; `people/bochengyin/drafts/eval-product-run-requests-need-family-scope-check`; `people/bochengyin/drafts/trial-error-reduction-should-extend-memory-diagnostics`
- False positives: `people/bochengyin/drafts/eval-run-manifest-should-precede-auto-runner`; `people/bochengyin/drafts/memory-compilation-mvp-needs-eval-gated-benefit`; `people/bochengyin/drafts/source-incident-timing-needs-provenance`
- Missed useful: `people/bochengyin/drafts/codex-session-recovery-should-search-jsonl-and-state-db`
- Hypothesis: Eval-stage granularity missing: broad eval drafts match every eval task, but only one workflow stage is actually useful.

### 33. `merge-the-source-incident-timing-feature-into-the-repo-release-the-npm-package-u`

- Prompt: Merge the source incident timing feature into the repo, release the npm package, update the local installed package, then run a local report that explains what trial and error means and what source incident timing is recorded.
- Replay: task_type `release_distribution`, risk tags `release_distribution`, precision `0.333`, noise `0.667`
- Useful selected: `constraints`; `conventions/distribution-target-matrix-must-match-published-assets`
- False positives: `conventions/package-managed-vs-user-owned-docs`; `people/bochengyin/drafts/efficiency-eval-should-include-source-incident-cost`; `people/bochengyin/drafts/repo-local-contributor-workflows-should-stay-out-of-the-package-layer`; `people/bochengyin/drafts/source-incident-timing-needs-provenance`
- Missed useful: -
- Hypothesis: Release task is multi-intent; release conventions, package docs, and PR-flow docs need subgoal quotas instead of one flat top-k.

### 34. `explain-why-historical-local-codex-sessions-are-not-enough-to-safely-infer-sourc`

- Prompt: Explain why historical local Codex sessions are not enough to safely infer source incident trial/error timing when reuse telemetry lacks source incident provenance.
- Replay: task_type `bug_fix`, risk tags `managed_prompt_block, memory_governance`, precision `0.333`, noise `0.667`
- Useful selected: `people/bochengyin/drafts/codex-session-recovery-should-search-jsonl-and-state-db`; `people/bochengyin/drafts/efficiency-eval-should-include-source-incident-cost`
- False positives: `people/bochengyin/drafts/eval-product-run-requests-need-family-scope-check`; `people/bochengyin/drafts/manual-impact-evals-need-visible-session-export-and-first-pass-cutoff`; `people/bochengyin/drafts/source-incident-timing-needs-provenance`; `people/bochengyin/drafts/trial-error-reduction-should-extend-memory-diagnostics`
- Missed useful: -
- Hypothesis: Broad eval/research draft labels dominate through shared terms such as eval, report, replay, metric, and workflow.

### 35. `clarify-why-source-session-ids-were-not-saved-when-writing-ai-wiki-memory-and-in`

- Prompt: Clarify why source session ids were not saved when writing AI wiki memory, and inspect whether existing write-back records can link memories to local sessions without guessing.
- Replay: task_type `memory_governance`, risk tags `memory_governance`, precision `0.333`, noise `0.667`
- Useful selected: `people/bochengyin/drafts/codex-session-recovery-should-search-jsonl-and-state-db`; `people/bochengyin/drafts/efficiency-eval-should-include-source-incident-cost`
- False positives: `people/bochengyin/drafts/manual-impact-evals-need-visible-session-export-and-first-pass-cutoff`; `people/bochengyin/drafts/route-usefulness-eval-needs-route-traces-and-actual-use-comparison`; `people/bochengyin/drafts/source-incident-timing-needs-provenance`; `people/bochengyin/drafts/trial-error-reduction-should-extend-memory-diagnostics`
- Missed useful: -
- Hypothesis: Memory/eval/provenance vocabulary overlaps; broad diagnostic drafts compete without stage-specific labels.

### 36. `implement-write-back-provenance-backfill-for-source-incident-timing-find-first-a`

- Prompt: Implement write-back provenance backfill for source incident timing: find first AI Wiki Write-Back Path in local Codex sessions, count only task turns before the memory write, and write a new backfill evidence ledger.
- Replay: task_type `memory_governance`, risk tags `managed_prompt_block, memory_governance, workflow_state`, precision `0.667`, noise `0.333`
- Useful selected: `people/bochengyin/drafts/codex-session-recovery-should-search-jsonl-and-state-db`; `people/bochengyin/drafts/efficiency-eval-should-include-source-incident-cost`; `people/bochengyin/drafts/route-usefulness-eval-needs-route-traces-and-actual-use-comparison`; `people/bochengyin/drafts/trial-error-reduction-should-extend-memory-diagnostics`
- False positives: `people/bochengyin/drafts/local-dogfooding-should-check-source-cli-vs-installed-entrypoint`; `people/bochengyin/drafts/source-incident-timing-needs-provenance`
- Missed useful: -
- Hypothesis: Likely measurement/context limitation or broad lexical overlap; inspect prompt context before changing scorer.

### 37. `clarify-whether-an-agent-can-know-current-session-id-and-duration-at-the-moment`

- Prompt: Clarify whether an agent can know current session id and duration at the moment it writes AI Wiki memory, and whether write-back skill should auto-record source incident timing.
- Replay: task_type `memory_governance`, risk tags `managed_prompt_block, memory_governance`, precision `0.000`, noise `1.000`
- Useful selected: -
- False positives: `people/bochengyin/drafts/efficiency-eval-should-include-source-incident-cost`; `people/bochengyin/drafts/eval-run-manifest-should-precede-auto-runner`; `people/bochengyin/drafts/feedback-diagnosis-mvp-should-start-as-explicit-generated-report`; `people/bochengyin/drafts/local-dogfooding-should-check-source-cli-vs-installed-entrypoint`; `people/bochengyin/drafts/opencode-runtime-skill-exposure-needs-prompt-visible-fallback`; `people/bochengyin/drafts/source-incident-timing-needs-provenance`
- Missed useful: -
- Hypothesis: Memory/eval/provenance vocabulary overlaps; broad diagnostic drafts compete without stage-specific labels.

### 38. `implement-post-turn-source-incident-capture-for-ai-wiki-write-back-after-a-codex`

- Prompt: Implement post-turn source incident capture for AI Wiki write-back: after a Codex turn ends, scan current repo session write-back footers and append structured source incident ledger evidence without mutating old reuse events.
- Replay: task_type `memory_governance`, risk tags `managed_prompt_block, memory_governance, workflow_state`, precision `0.333`, noise `0.667`
- Useful selected: `constraints`; `people/bochengyin/drafts/source-incident-timing-needs-provenance`
- False positives: `people/bochengyin/drafts/consolidation-should-layer-over-end-of-task-capture-and-avoid-shared-doc-churn`; `people/bochengyin/drafts/efficiency-eval-should-include-source-incident-cost`; `people/bochengyin/drafts/managed-toolkit-workflows-need-a-toc-and-scope-aware-conflict-checks`; `people/bochengyin/drafts/repo-local-contributor-workflows-should-stay-out-of-the-package-layer`
- Missed useful: -
- Hypothesis: Likely measurement/context limitation or broad lexical overlap; inspect prompt context before changing scorer.

### 39. `session-ai-wiki-load-load-index-constraints-decisions-workflows`

- Prompt: 用户询问新 session 启动时 AI Wiki 实际 load 了多少内容，以及是否应该只 load index，另加 constraints、decisions、workflows
- Replay: task_type `general`, risk tags `none`, precision `0.667`, noise `0.333`
- Useful selected: `constraints`; `decisions`; `people/bochengyin/drafts/context-routing-budget-should-be-sparse-and-index-backed`; `workflows`
- False positives: `index`; `people/bochengyin/drafts/codex-session-recovery-should-search-jsonl-and-state-db`
- Missed useful: -
- Hypothesis: Likely measurement/context limitation or broad lexical overlap; inspect prompt context before changing scorer.

### 40. `ai-wiki-changes-push-repo`

- Prompt: 用户确认当前 AI Wiki 行为符合预期，要求把当前本地 changes 都 push 到云端 repo
- Replay: task_type `general`, risk tags `none`, precision `0.667`, noise `0.333`
- Useful selected: `constraints`; `workflows`
- False positives: `conventions/package-managed-vs-user-owned-docs`
- Missed useful: -
- Hypothesis: Likely measurement/context limitation or broad lexical overlap; inspect prompt context before changing scorer.

### 41. `ai-wiki-toolkit-trial-and-error-source-incident`

- Prompt: 用户询问 ai-wiki-toolkit 被用户下载后，是否可以自动沉淀 trial and error / source incident 经验
- Replay: task_type `bug_fix`, risk tags `user_owned_docs`, precision `0.500`, noise `0.500`
- Useful selected: `constraints`; `people/bochengyin/drafts/source-incident-timing-needs-provenance`; `people/bochengyin/drafts/trial-error-reduction-should-extend-memory-diagnostics`
- False positives: `people/bochengyin/drafts/efficiency-eval-should-include-source-incident-cost`; `people/bochengyin/drafts/eval-product-run-requests-need-family-scope-check`; `people/bochengyin/drafts/local-dogfooding-should-check-source-cli-vs-installed-entrypoint`
- Missed useful: -
- Hypothesis: Broad eval/research draft labels dominate through shared terms such as eval, report, replay, metric, and workflow.

### 42. `ai-wiki-toolkit-package-post-turn-hook`

- Prompt: 用户询问是否应该在用户下载 ai-wiki-toolkit package 时自动安装 post-turn hook
- Replay: task_type `release_distribution`, risk tags `release_distribution, user_owned_docs`, precision `0.833`, noise `0.167`
- Useful selected: `constraints`; `conventions/distribution-target-matrix-must-match-published-assets`; `conventions/package-managed-vs-user-owned-docs`; `decisions`; `workflows`
- False positives: `people/bochengyin/drafts/introducing-new-npm-package-names-needs-a-bootstrap-publish-plan`
- Missed useful: -
- Hypothesis: Likely measurement/context limitation or broad lexical overlap; inspect prompt context before changing scorer.

### 43. `post-turn-hook-install-post-turn-capture-doctor-hook`

- Prompt: 实现建议用户开启 post-turn hook：install 默认提示可开启 post-turn capture，doctor 检查/提示 hook 未启用，但不要默认启用
- Replay: task_type `bug_fix`, risk tags `ci_workflow, user_owned_docs`, precision `0.500`, noise `0.500`
- Useful selected: `constraints`; `decisions`; `people/bochengyin/drafts/post-turn-hooks-should-be-opt-in`
- False positives: `people/bochengyin/drafts/eval-product-mvp-starts-with-first-attempt-artifact-report`; `people/bochengyin/drafts/impact-eval-result-capture-must-include-untracked-files`; `workflows`
- Missed useful: -
- Hypothesis: Broad eval/research draft labels dominate through shared terms such as eval, report, replay, metric, and workflow.

### 44. `push-current-changes-to-remote-merge-the-pr-then-release-npm-for-ai-wiki-toolkit`

- Prompt: push current changes to remote, merge the PR, then release npm for ai-wiki-toolkit
- Replay: task_type `release_distribution`, risk tags `release_distribution, user_owned_docs`, precision `0.333`, noise `0.667`
- Useful selected: `constraints`; `conventions/distribution-target-matrix-must-match-published-assets`
- False positives: `people/bochengyin/drafts/distribution-target-matrix-must-match-published-assets`; `people/bochengyin/drafts/linux-release-binaries-need-runtime-checks-against-an-older-glibc-baseline`; `people/bochengyin/drafts/npm-postinstall-must-not-delete-its-own-download-archive`; `people/bochengyin/drafts/pr-flow-finish-needs-rebase-sync-after-local-main-ahead`
- Missed useful: `people/bochengyin/drafts/release-assets-should-not-be-blocked-by-homebrew-tap-sync`
- Hypothesis: Release task is multi-intent; release conventions, package docs, and PR-flow docs need subgoal quotas instead of one flat top-k.

### 45. `ai-wiki-toolkit-index-indexing`

- Prompt: 那我们的 ai wiki toolkit 里面的 index 是不是就是 indexing 呢？
- Replay: task_type `scaffold_prompt_workflow`, risk tags `user_owned_docs`, precision `0.167`, noise `0.833`
- Useful selected: `people/bochengyin/drafts/context-routing-budget-should-be-sparse-and-index-backed`
- False positives: `constraints`; `conventions/index`; `conventions/package-managed-vs-user-owned-docs`; `decisions`; `people/bochengyin/drafts/user-owned-ai-wiki-index-should-not-be-an-upgrade-surface`
- Missed useful: `index`
- Hypothesis: Toolkit/user-owned risk tags over-protect core docs; label/logic should distinguish product strategy from scaffold edits.

### 46. `ai-wiki-toolkit-vector-indexing`

- Prompt: 懂了 其实我们现在这 ai wiki toolkit 也没有必要做 vector indexing
- Replay: task_type `scaffold_prompt_workflow`, risk tags `user_owned_docs`, precision `0.000`, noise `1.000`
- Useful selected: -
- False positives: `constraints`; `conventions/package-managed-vs-user-owned-docs`; `decisions`; `people/bochengyin/drafts/vector-indexing-not-needed-for-current-ai-wiki-routing`; `workflows`
- Missed useful: `people/bochengyin/drafts/context-routing-budget-should-be-sparse-and-index-backed`
- Hypothesis: Toolkit/user-owned risk tags over-protect core docs; label/logic should distinguish product strategy from scaffold edits.

### 47. `ai-wiki-toolkit-metrics-think-hard`

- Prompt: 我觉得现在我的这个 ai wiki toolkit 是蛮好的，但是我感觉我缺少 metrics 来告诉别人我的这个有多好。你需要 think hard
- Replay: task_type `scaffold_prompt_workflow`, risk tags `user_owned_docs`, precision `0.500`, noise `0.500`
- Useful selected: `metrics/index`; `people/bochengyin/drafts/ai-wiki-usefulness-metrics-need-task-level-checks-plus-doc-events`; `people/bochengyin/drafts/neutral-impact-eval-runs-need-change-profile-quality-metrics`
- False positives: `constraints`; `decisions`; `workflows`
- Missed useful: `people/bochengyin/drafts/context-routing-budget-should-be-sparse-and-index-backed`; `people/bochengyin/drafts/efficiency-eval-should-include-source-incident-cost`; `people/bochengyin/drafts/eval-product-mvp-starts-with-first-attempt-artifact-report`; `people/bochengyin/drafts/impact-eval-prompts-should-backsolve-from-concrete-history`; `people/bochengyin/drafts/route-usefulness-eval-needs-route-traces-and-actual-use-comparison`; `people/bochengyin/drafts/vector-indexing-not-needed-for-current-ai-wiki-routing`; `people/bochengyin/drafts/workflow-primary-impact-evals-compare-working-modes`
- Hypothesis: Toolkit/user-owned risk tags over-protect core docs; label/logic should distinguish product strategy from scaffold edits.

### 48. `redacted-external-form-task`

- Prompt: Redacted external form-writing prompt
- Replay: task_type `scaffold_prompt_workflow`, risk tags `managed_prompt_block`, precision `0.000`, noise `1.000`
- Useful selected: -
- False positives: `constraints`; `people/bochengyin/drafts/source-incident-timing-needs-provenance`; `workflows`
- Missed useful: -
- Hypothesis: Core-doc fallback on underspecified or discussion-only prompt; route should abstain or return fewer selected docs.

### 49. `codex-security-application-field-why-does-ai-wiki-toolkit-need-codex-security`

- Prompt: Codex Security application field: why does ai-wiki-toolkit need Codex Security
- Replay: task_type `scaffold_prompt_workflow`, risk tags `managed_prompt_block, user_owned_docs`, precision `0.167`, noise `0.833`
- Useful selected: `constraints`
- False positives: `conventions/distribution-target-matrix-must-match-published-assets`; `decisions`; `people/bochengyin/drafts/consolidation-should-layer-over-end-of-task-capture-and-avoid-shared-doc-churn`; `people/bochengyin/drafts/impact-eval-prompts-should-backsolve-from-concrete-history`; `workflows`
- Missed useful: -
- Hypothesis: Toolkit/user-owned risk tags over-protect core docs; label/logic should distinguish product strategy from scaffold edits.

### 50. `aiwikitoolkit-code`

- Prompt: 你觉得关于 aiwikitoolkit 的建议如何？先别 code 告诉我你是怎么想的
- Replay: task_type `general`, risk tags `none`, precision `0.333`, noise `0.667`
- Useful selected: `constraints`
- False positives: `decisions`; `workflows`
- Missed useful: -
- Hypothesis: Core docs are useful sometimes but selected too often as a safety blanket.

### 51. `route-policy-optimization-auto-research-metrics`

- Prompt: 设计 Route Policy Optimization Auto Research 的评估，避免过拟合，选择 metrics，并寻找相关开源论文和基准
- Replay: task_type `eval_workflow`, risk tags `memory_governance, task_evaluation`, precision `0.167`, noise `0.833`
- Useful selected: `people/bochengyin/drafts/route-usefulness-eval-needs-route-traces-and-actual-use-comparison`
- False positives: `people/bochengyin/drafts/efficiency-eval-should-include-source-incident-cost`; `people/bochengyin/drafts/eval-run-manifest-should-precede-auto-runner`; `people/bochengyin/drafts/impact-eval-prompts-should-backsolve-from-concrete-history`; `people/bochengyin/drafts/neutral-impact-eval-runs-need-change-profile-quality-metrics`; `people/bochengyin/drafts/trial-error-reduction-should-extend-memory-diagnostics`
- Missed useful: -
- Hypothesis: Eval-stage granularity missing: broad eval drafts match every eval task, but only one workflow stage is actually useful.

### 52. `ai-wiki-toolkit-development`

- Prompt: 评估用户提供的 AI wiki toolkit 策略，结合当前 development，严谨说明已经做到什么、还可以继续做什么，不写代码
- Replay: task_type `scaffold_prompt_workflow`, risk tags `user_owned_docs`, precision `0.200`, noise `0.800`
- Useful selected: `constraints`
- False positives: `conventions/distribution-target-matrix-must-match-published-assets`; `conventions/package-managed-vs-user-owned-docs`; `decisions`; `workflows`
- Missed useful: `work/index`
- Hypothesis: Toolkit/user-owned risk tags over-protect core docs; label/logic should distinguish product strategy from scaffold edits.

### 53. `workflow-vs-skills-aiwiki-toolkit-evaluation-review-repo`

- Prompt: 评估用户对 workflow vs skills 区别的疑问，以及当前 aiwiki-toolkit 是否支持用户使用一段时间后自跑 evaluation、得到改进建议、review 后自行改进 repo
- Replay: task_type `scaffold_prompt_workflow`, risk tags `ci_workflow, task_evaluation, user_owned_docs`, precision `0.333`, noise `0.667`
- Useful selected: `constraints`; `conventions/package-managed-vs-user-owned-docs`
- False positives: `people/bochengyin/drafts/karpathy-skills-suggest-success-criteria-and-cross-agent-packaging`; `people/bochengyin/drafts/local-dogfooding-should-check-source-cli-vs-installed-entrypoint`; `people/bochengyin/drafts/toolkit-installed-repo-local-skills-should-skip-existing-files`; `workflows`
- Missed useful: -
- Hypothesis: Toolkit/user-owned risk tags over-protect core docs; label/logic should distinguish product strategy from scaffold edits.

### 54. `aiwiki-toolkit-evaluate-repo`

- Prompt: 为 aiwiki-toolkit 设计 evaluate repo 自评估与改进建议命令的详细实施步骤，用户先要计划不要代码
- Replay: task_type `eval_workflow`, risk tags `task_evaluation, user_owned_docs`, precision `0.167`, noise `0.833`
- Useful selected: `people/bochengyin/drafts/route-usefulness-eval-needs-route-traces-and-actual-use-comparison`
- False positives: `people/bochengyin/drafts/efficiency-eval-should-include-source-incident-cost`; `people/bochengyin/drafts/eval-product-mvp-starts-with-first-attempt-artifact-report`; `people/bochengyin/drafts/impact-eval-prompts-should-backsolve-from-concrete-history`; `people/bochengyin/drafts/impact-eval-result-capture-must-include-untracked-files`; `people/bochengyin/drafts/trial-error-reduction-should-extend-memory-diagnostics`
- Missed useful: -
- Hypothesis: Eval-stage granularity missing: broad eval drafts match every eval task, but only one workflow stage is actually useful.

### 55. `implementation-prompt-aiwiki-toolkit-evaluate-repo`

- Prompt: 为新窗口生成可复制粘贴的详细 implementation prompt：实现 aiwiki-toolkit evaluate repo 自评估与改进建议命令
- Replay: task_type `eval_workflow`, risk tags `managed_prompt_block, task_evaluation, user_owned_docs`, precision `0.000`, noise `1.000`
- Useful selected: -
- False positives: `people/bochengyin/drafts/efficiency-eval-should-include-source-incident-cost`; `people/bochengyin/drafts/eval-product-mvp-starts-with-first-attempt-artifact-report`; `people/bochengyin/drafts/impact-eval-no-target-aiwiki-slots-must-exclude-task-specific-workflow-memory`; `people/bochengyin/drafts/impact-eval-prompts-should-backsolve-from-concrete-history`; `people/bochengyin/drafts/source-incident-timing-needs-provenance`; `people/bochengyin/drafts/trial-error-reduction-should-extend-memory-diagnostics`
- Missed useful: -
- Hypothesis: Eval-stage granularity missing: broad eval drafts match every eval task, but only one workflow stage is actually useful.

### 56. `ai-wiki-toolkit-agent-codebase`

- Prompt: 评价别人关于增强 AI wiki toolkit 以找到 agent 工作的建议，并结合当前 codebase 给出判断
- Replay: task_type `scaffold_prompt_workflow`, risk tags `managed_prompt_block, user_owned_docs`, precision `0.250`, noise `0.750`
- Useful selected: `constraints`
- False positives: `conventions/package-managed-vs-user-owned-docs`; `decisions`; `workflows`
- Missed useful: `people/bochengyin/drafts/agent-framework-layers-should-guide-ai-wiki-toolkit-roadmap`; `people/bochengyin/drafts/eval-product-mvp-starts-with-first-attempt-artifact-report`; `people/bochengyin/drafts/external-ai-wiki-metrics-need-a-proof-stack-not-a-dashboard`; `people/bochengyin/drafts/route-usefulness-eval-needs-route-traces-and-actual-use-comparison`
- Hypothesis: Toolkit/user-owned risk tags over-protect core docs; label/logic should distinguish product strategy from scaffold edits.

### 57. `project-a-eval-report-diagnostics`

- Prompt: 补做 Project A 的测试和诊断：运行完整本地测试、eval/report diagnostics，并给出具体优化建议
- Replay: task_type `bug_fix`, risk tags `ci_workflow, task_evaluation`, precision `0.333`, noise `0.667`
- Useful selected: `people/bochengyin/drafts/eval-product-mvp-starts-with-first-attempt-artifact-report`; `people/bochengyin/drafts/eval-run-manifest-should-precede-auto-runner`
- False positives: `constraints`; `people/bochengyin/drafts/memory-compilation-mvp-needs-eval-gated-benefit`; `people/bochengyin/drafts/neutral-impact-eval-runs-need-change-profile-quality-metrics`; `people/bochengyin/drafts/trial-error-reduction-should-extend-memory-diagnostics`
- Missed useful: `people/bochengyin/drafts/eval-product-run-requests-need-family-scope-check`; `people/bochengyin/drafts/manual-impact-evals-need-visible-session-export-and-first-pass-cutoff`; `people/bochengyin/drafts/shared-ai-wiki-prompt-blocks-need-one-shot-local-gates`; `people/bochengyin/drafts/source-incident-timing-needs-provenance`
- Hypothesis: Missed-useful docs point to weak target labels or missing session/work-context signals.
