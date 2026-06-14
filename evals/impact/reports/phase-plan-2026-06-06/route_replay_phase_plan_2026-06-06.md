# Historical Route Replay Report

- Generated at: `2026-06-06T23:10:51+10:00`
- Before: `None`
- Catalog cutoff: `trace-routed-at`
- Handle: `bochengyin`

## Prompt Recovery

- Target traces: `57`
- Recovered traces: `57`
- Replayed traces: `57`
- Unmatched traces: `0`
- Confidence counts: `{'high': 56, 'low': 1}`
- Route command candidates scanned: `763`

## Comparison

| cohort | traces | precision | noise | selected | selected_useful |
| --- | --- | --- | --- | --- | --- |
| baseline | 57 | 0.538 | 0.462 | 333 | 179 |
| replay | 57 | 0.352 | 0.648 | 290 | 102 |

- Precision delta: `-0.186`
- Noise delta: `0.186`

## Temporal Catalog

- Filtered future docs: `637`
- Selected future docs: `0`
- Selected unknown-created-at docs: `70`
- Catalog docs without created_at: `17`

## Replay Rows

| task_id | confidence | old_precision | replay_precision | delta | prompt |
| --- | --- | --- | --- | --- | --- |
| draft-reuse-3-promote | high | 0.000 | - | - | 查找是否有 draft reuse 超过 3 次就应该 promote 的历史记录 |
| code | high | 0.333 | 0.000 | -0.333 | 好 那你说说我们现在还有什么是需要 code 进去的。 |
| weekly-report-saved-time-coverage-promotion-noisy-diagnosis-telemetry-provenance | high | 0.500 | 0.000 | -0.500 | 把 weekly report 从 saved-time 改成 coverage/promotion/noisy diagnosis，并加入 telemetry proven... |
| karpathy-ai-wiki-toolkit | high | 0.167 | 0.333 | 0.167 | 联网搜索 Karpathy 最近在研究什么，并基于结果思考 ai-wiki-toolkit 可以怎么进步 |
| karpathy-html-markdown-ai-wiki-agent-memory-ai-wiki-toolkit-html | high | 0.167 | 0.333 | 0.167 | 讨论 Karpathy 认为 HTML 比 Markdown 更适合作为 AI wiki/agent memory 载体，并判断 ai-wiki-toolkit 是否应该转向... |
| weekly-html-report-self-involving | high | 0.333 | 0.000 | -0.333 | 修改 weekly HTML report，只显示需要用户 self-involving 的可行动数据，去掉省多少时间等效率估算展示 |
| ai-wiki-toolkit-ai-wiki-toolkit-handle-git-conflict | high | 0.333 | 0.000 | -0.333 | 团队接入 ai-wiki-toolkit 时，评估 ai-wiki/_toolkit 生成物是否应该按 handle 分区以避免 git conflict，并提出/实现必要改动 |
| push-current-changes-and-release-a-new-version | high | 0.333 | - | - | push current changes and release a new version |
| evaluate-another-agent-s-assessment-that-ai-wiki-toolkit-has-first-version-workf | high | 0.667 | 0.500 | -0.167 | Evaluate another agent's assessment that ai-wiki-toolkit has first-version workflow eva... |
| implement-the-next-eval-productization-slice-after-eval-impact-report-add-lightw | high | 0.333 | 0.333 | 0.000 | Implement the next eval productization slice after eval impact report: add lightweight... |

## Warnings

- Historical replay is approximate when prompt recovery confidence is not exact_session or trace_task.
- Use the route-noise cohort report for forward-looking post-change production evidence.
