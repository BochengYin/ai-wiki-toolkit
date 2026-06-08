# Trace-Signal Route Replay Comparison

Generated at: `2026-06-08T14:27:32+10:00`

## Method

This reruns the same `58` replay-evaluable traces with the current router and `catalog_cutoff=trace-routed-at`, but changes the replay input policy:

- Task-only replay: use recovered route command task text and only explicit `--changed-path` values from the original route command.
- Trace-signal replay: use the same recovered task text, but pass `changed_paths` recorded in each historical route trace as explicit changed-path signals.

Trace-signal coverage:

- traces with changed_paths: `50`
- traces without changed_paths: `8`
- total changed_paths passed: `641`
- max changed_paths on one trace: `46`

## Aggregate Results

| cohort | route_precision | retrieval_precision | selected_docs | selected_useful | missed_useful | failed_route@selected | failed_route@selected+maybe | candidate20 coverage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| trace-selected baseline | 0.531 | 0.495 | 339 | 180 | 44 | 0.052 | 0.017 | n/a |
| task-only replay | 0.361 | 0.358 | 296 | 107 | 58 | 0.224 | 0.224 | 0.707 |
| trace-signal replay | 0.384 | 0.381 | 307 | 118 | 55 | 0.293 | 0.276 | 0.799 |

Trace-signal delta vs task-only:

- route_precision: `+0.023`
- retrieval_precision: `+0.022`
- selected_docs: `+11`
- selected_useful: `+11`
- missed_useful: `-3`
- failed_route@selected: `+0.069`
- failed_route@selected+maybe: `+0.052`
- candidate20 useful coverage: `+0.092`

Approximate gap closure:

- route_precision gap closed vs trace-selected baseline: `0.135` of the task-only gap.
- selected_useful gap closed vs trace-selected baseline: `0.151` of the task-only selected-useful gap.

## Paired Trace Effects

- paired traces: `58`
- traces with any selected/useful/missed/precision change: `32`
- traces with selected useful wins: `17`
- traces with selected useful losses: `12`
- traces with missed useful improvement: `6`
- traces with missed useful worsening: `5`

Top useful wins:

| task_id | changed_paths | precision | selected_useful_delta | missed_useful_delta | task |
| --- | ---: | ---: | ---: | ---: | --- |
| `implementation-prompt-aiwiki-toolkit-evaluate-repo` | 9 | 0.000 -> 0.667 | +4 | +0 | 为新窗口生成可复制粘贴的详细 implementation prompt：实现 aiwiki-toolkit evaluate repo 自评估与改进建议命令 |
| `aiwikitoolkit-code` | 9 | 0.333 -> 0.667 | +3 | +0 | 你觉得关于 aiwikitoolkit 的建议如何？先别 code 告诉我你是怎么想的 |
| `implement-the-three-step-autonomous-impact-eval-runner-v0-single-slot-run-v1-all` | 9 | 0.500 -> 0.833 | +2 | -2 | Implement the three-step autonomous impact eval runner: v0 single-slot run, v1... |
| `project-a-eval-report-diagnostics` | 7 | 0.333 -> 0.667 | +2 | -2 | 补做 Project A 的测试和诊断：运行完整本地测试、eval/report diagnostics，并给出具体优化建议 |
| `route-policy-optimization-auto-research-metrics` | 9 | 0.167 -> 0.500 | +2 | +0 | 设计 Route Policy Optimization Auto Research 的评估，避免过拟合，选择 metrics，并寻找相关开源论文和基准 |
| `aiwiki-toolkit-evaluate-repo` | 9 | 0.167 -> 0.500 | +2 | +0 | 为 aiwiki-toolkit 设计 evaluate repo 自评估与改进建议命令的详细实施步骤，用户先要计划不要代码 |
| `ai-wiki-toolkit-development` | 9 | 0.200 -> 0.500 | +2 | +0 | 评估用户提供的 AI wiki toolkit 策略，结合当前 development，严谨说明已经做到什么、还可以继续做什么，不写代码 |
| `complete-eval-impact-automation-lifecycle-by-adding-capture-validate-and-score-c` | 9 | 0.667 -> 0.833 | +1 | -1 | Complete eval impact automation lifecycle by adding capture, validate, and sco... |

Top useful losses:

| task_id | changed_paths | precision | selected_useful_delta | missed_useful_delta | task |
| --- | ---: | ---: | ---: | ---: | --- |
| `session-ai-wiki-load-load-index-constraints-decisions-workflows` | 17 | 0.667 -> 0.333 | -2 | +1 | 用户询问新 session 启动时 AI Wiki 实际 load 了多少内容，以及是否应该只 load index，另加 constraints、deci... |
| `ai-wiki-changes-push-repo` | 17 | 0.667 -> 0.000 | -2 | +0 | 用户确认当前 AI Wiki 行为符合预期，要求把当前本地 changes 都 push 到云端 repo |
| `merge-the-source-incident-timing-feature-into-the-repo-release-the-npm-package-u` | 12 | 0.333 -> 0.000 | -2 | +0 | merge the source incident timing feature into the repo release the npm package... |
| `clarify-why-source-session-ids-were-not-saved-when-writing-ai-wiki-memory-and-in` | 3 | 0.333 -> 0.000 | -2 | +0 | Clarify why source session ids were not saved when writing AI wiki memory, and... |
| `push-the-continuous-impact-eval-loop-changes-reinstall-the-local-aiwiki-toolkit` | 11 | 0.333 -> 0.000 | -1 | +1 | Push the continuous impact eval loop changes, reinstall the local aiwiki-toolk... |
| `karpathy-ai-wiki-toolkit` | 36 | 0.333 -> 0.167 | -1 | +1 | 联网搜索 Karpathy 最近在研究什么，并基于结果思考 ai-wiki-toolkit 可以怎么进步 |
| `evals-impact-reports-route-precision-handoff-2026-06-05-md-core-doc-gating-57-tr` | 46 | 0.167 -> 0.000 | -1 | +1 | 请先读 evals/impact/reports/route-method-2026-06-05/route_precision_handoff_2026-06-05.md。不要直接实现 core-doc... |
| `clarify-whether-eval-impact-users-need-a-family-discovery-command-before-they-ca` | 10 | 0.333 -> 0.167 | -1 | +1 | Clarify whether eval impact users need a family discovery command before they ... |

## Interpretation

Historical changed-path signals explain part of the task-only replay gap, but not most of it. Passing trace `changed_paths` improves route precision from `0.361` to `0.384` and selected useful docs from `107` to `118`. That closes about `0.135` of the route-precision gap against the trace-selected baseline.

The signal is not cleanly positive. It improves recall-like metrics, but failed-route rates worsen: failed_route@selected moves from `0.224` to `0.293`. The historical dirty-path context is broad: `641` path signals across `58` traces, with common paths such as `README.md`, `src/ai_wiki_toolkit/cli.py`, and broad eval/report files. That can recover useful task area context, but it also pulls in adjacent docs.

Conclusion: trace changed paths are a real missing control variable, but they are not enough to make replay exact or to recover the historical selected-doc baseline. The remaining gap likely needs either true session-context replay, better prompt/context capture in future traces, or a router that is less dependent on implicit worktree/session state.
