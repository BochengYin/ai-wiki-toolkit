# Historical Route Replay Report

- Generated at: `2026-06-08T14:00:31+10:00`
- Before: `None`
- Catalog cutoff: `trace-routed-at`
- Handle: `bochengyin`

## Prompt Recovery

- Target traces: `58`
- Recovered traces: `58`
- Replayed traces: `58`
- Unmatched traces: `0`
- Confidence counts: `{'high': 57, 'low': 1}`
- Route command candidates scanned: `807`

## Comparison

| cohort | traces | precision | noise | retrieval_precision | selected | selected_useful | retrieval_selected | retrieval_useful | core_docs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 58 | 0.531 | 0.469 | 0.495 | 339 | 180 | 297 | 147 | 42 |
| replay | 58 | 0.361 | 0.639 | 0.358 | 296 | 107 | 265 | 95 | 31 |

- Precision delta: `-0.169`
- Noise delta: `0.169`

## Layered Metrics

- Baseline reason types: `{'safety_guardrail': 42, 'topical_memory': 297}`
- Replay reason types: `{'background_reference': 37, 'bucket_primary': 88, 'mandatory_contract': 3, 'safety_guardrail': 28, 'topical_memory': 140}`
- Replay mandatory contract docs: `3`
- Replay safety guardrail docs: `28`
- Replay core docs selected-but-unused: `19`
- Replay retrieval selected-but-unused: `169`

## RAG-Style Retrieval Metrics

| cohort | failed@selected | failed@selected+maybe | failed@candidate20 | coverage@selected | coverage@selected+maybe | coverage@candidate20 | maybe_recovery | avg_words | avg_docs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 0.052 | 0.017 | - | 0.786 | 0.808 | - | 0.667 | 1000.569 | 8.431 |
| replay | 0.224 | 0.224 | 0.069 | 0.467 | 0.472 | 0.707 | 0.000 | 1128.431 | 7.655 |

## Per-Trace Regression Summary

- Compared items: `58`
- Precision regressions: `35`
- Precision improvements: `8`
- Precision ties: `15`
- Precision uncomputed: `0`
- Noise regressions: `35`
- Noise improvements: `8`
- Noise ties: `15`
- Noise uncomputed: `0`

## Temporal Catalog

- Filtered future docs: `652`
- Selected future docs: `0`
- Selected unknown-created-at docs: `72`
- Catalog docs without created_at: `17`

## Eval Stage Confusion

- Stage-active traces: `27`
- Selected eval docs: `138`
- Compatible eval docs: `98`
- Incompatible eval docs: `40`
- Compatibility rate: `0.710`

| task_stage | doc_stage | selected_docs |
| --- | --- | --- |
| manifest_or_runner | prompt_design | 12 |
| manifest_or_runner | artifact_capture | 4 |
| source_incident_timing | manifest_or_runner | 4 |
| prompt_design | source_incident_timing | 3 |
| prompt_design | manifest_or_runner | 2 |
| route_usefulness | artifact_capture | 2 |
| route_usefulness | prompt_design | 2 |
| source_incident_timing | prompt_design | 2 |
| manifest_or_runner | public_metrics | 1 |
| manifest_or_runner | route_usefulness | 1 |

## Replay Rows

| task_id | confidence | old_precision | replay_precision | delta | prompt |
| --- | --- | --- | --- | --- | --- |
| promote-draft-ai-wiki-people-bochengyin-index-md | high | 0.167 | 0.000 | -0.167 | 检查是否已有自动 promote draft 到 ai-wiki/people/bochengyin/index.md 的机制 |
| draft-reuse-3-promote | high | 0.000 | 0.000 | 0.000 | 查找是否有 draft reuse 超过 3 次就应该 promote 的历史记录 |
| code | high | 0.333 | 0.000 | -0.333 | 好 那你说说我们现在还有什么是需要 code 进去的。 |
| weekly-report-saved-time-coverage-promotion-noisy-diagnosis-telemetry-provenance | high | 0.500 | 0.000 | -0.500 | 把 weekly report 从 saved-time 改成 coverage/promotion/noisy diagnosis，并加入 telemetry proven... |
| karpathy-ai-wiki-toolkit | high | 0.167 | 0.333 | 0.167 | 联网搜索 Karpathy 最近在研究什么，并基于结果思考 ai-wiki-toolkit 可以怎么进步 |
| karpathy-html-markdown-ai-wiki-agent-memory-ai-wiki-toolkit-html | high | 0.167 | 0.333 | 0.167 | 讨论 Karpathy 认为 HTML 比 Markdown 更适合作为 AI wiki/agent memory 载体，并判断 ai-wiki-toolkit 是否应该转向... |
| weekly-html-report-self-involving | high | 0.333 | 0.000 | -0.333 | 修改 weekly HTML report，只显示需要用户 self-involving 的可行动数据，去掉省多少时间等效率估算展示 |
| ai-wiki-toolkit-ai-wiki-toolkit-handle-git-conflict | high | 0.333 | 0.000 | -0.333 | 团队接入 ai-wiki-toolkit 时，评估 ai-wiki/_toolkit 生成物是否应该按 handle 分区以避免 git conflict，并提出/实现必要改动 |
| push-current-changes-and-release-a-new-version | high | 0.333 | 0.000 | -0.333 | push current changes and release a new version |
| evaluate-another-agent-s-assessment-that-ai-wiki-toolkit-has-first-version-workf | high | 0.667 | 0.500 | -0.167 | Evaluate another agent's assessment that ai-wiki-toolkit has first-version workflow eva... |
| implement-the-next-eval-productization-slice-after-eval-impact-report-add-lightw | high | 0.333 | 0.333 | 0.000 | Implement the next eval productization slice after eval impact report: add lightweight... |
| continue-eval-productization-after-adding-eval-impact-manifest-implement-the-nex | high | 0.500 | 0.500 | 0.000 | Continue eval productization after adding eval impact manifest: implement the next safe... |
| decide-the-next-implementation-step-after-adding-eval-impact-manifest-and-eval-i | high | 0.500 | 0.333 | -0.167 | Decide the next implementation step after adding eval impact manifest and eval impact p... |
| implement-eval-impact-prepare-command-after-eval-impact-plan-create-workspaces-a | high | 0.500 | 0.167 | -0.333 | Implement eval impact prepare command after eval impact plan: create workspaces and run... |
| decide-next-step-after-implementing-eval-impact-plan-prepare-manifest-report-sum | high | 0.500 | 0.167 | -0.333 | Decide next step after implementing eval impact plan, prepare, manifest, report, summar... |
| complete-eval-impact-automation-lifecycle-by-adding-capture-validate-and-score-c | high | 0.833 | 0.667 | -0.167 | Complete eval impact automation lifecycle by adding capture, validate, and score comman... |
| implement-the-three-step-autonomous-impact-eval-runner-v0-single-slot-run-v1-all | high | 1.000 | 0.500 | -0.500 | Implement the three-step autonomous impact eval runner: v0 single-slot run, v1 all-slot... |
| add-a-rubric-judge-scoring-policy-to-the-autonomous-impact-eval-runner-so-eval-i | high | 0.833 | 0.667 | -0.167 | Add a rubric judge scoring policy to the autonomous impact eval runner so eval impact r... |
| answer-whether-the-current-ai-wiki-toolkit-can-be-downloaded-installed-and-used | high | 0.500 | 0.333 | -0.167 | Answer whether the current ai-wiki toolkit can be downloaded, installed, and used by us... |
| clarify-whether-users-must-run-plan-prepare-run-report-separately-or-whether-the | high | 0.333 | 0.333 | 0.000 | Clarify whether users must run plan prepare run report separately or whether the curren... |
| explain-with-examples-which-parts-of-eval-impact-workflow-are-currently-automate | high | 0.333 | 0.333 | 0.000 | Explain with examples which parts of eval impact workflow are currently automated and w... |
| clarify-whether-eval-impact-users-need-a-family-discovery-command-before-they-ca | high | 0.333 | 0.333 | 0.000 | Clarify whether eval impact users need a family discovery command before they can run o... |
| design-the-eval-impact-family-discovery-step-including-how-it-should-identify-tr | high | 0.667 | 0.500 | -0.167 | Design the eval impact family discovery step, including how it should identify trial-an... |
| identify-what-the-current-project-still-needs-to-implement-eval-impact-family-di | high | 0.667 | 0.667 | 0.000 | Identify what the current project still needs to implement eval impact family discovery... |
| implement-eval-impact-family-discovery-trial-error-candidate-discovery-family-le | high | 0.667 | 0.667 | 0.000 | Implement eval impact family discovery, trial-error candidate discovery, family-level b... |
| clarify-roadmap-for-continuous-automatic-discovery-of-new-impact-eval-families-a | high | 0.500 | 0.500 | 0.000 | Clarify roadmap for continuous automatic discovery of new impact eval families, automat... |
| build-a-continuous-impact-eval-loop-automatically-discover-new-eval-families-fro | high | 1.000 | 0.833 | -0.167 | Build a continuous impact eval loop: automatically discover new eval families from tria... |
| push-the-continuous-impact-eval-loop-changes-reinstall-the-local-aiwiki-toolkit | high | 1.000 | 0.333 | -0.667 | Push the continuous impact eval loop changes, reinstall the local aiwiki-toolkit packag... |
| merge-pr-73-release-ai-wiki-toolkit-to-npm-update-the-local-installed-package-th | high | 0.500 | 0.000 | -0.500 | Merge PR 73, release ai-wiki-toolkit to npm, update the local installed package, then r... |
| explain-the-discovered-continuous-impact-eval-candidates-their-underlying-proble | high | 0.500 | 0.667 | 0.167 | Explain the discovered continuous impact eval candidates: their underlying problem, tri... |
| implement-source-incident-trial-error-timing-extraction-for-impact-eval-candidat | high | 0.667 | 0.500 | -0.167 | Implement source incident trial/error timing extraction for impact eval candidates, so... |
| implement-source-incident-trial-error-timing-extraction-for-impact-eval-candidat | high | 1.000 | 0.500 | -0.500 | Implement source incident trial/error timing extraction for impact eval candidates, so... |
| merge-the-source-incident-timing-feature-into-the-repo-release-the-npm-package-u | low | 0.667 | 0.333 | -0.333 | merge the source incident timing feature into the repo release the npm package update |
| explain-why-historical-local-codex-sessions-are-not-enough-to-safely-infer-sourc | high | 0.333 | 0.333 | 0.000 | Explain why historical local Codex sessions are not enough to safely infer source incid... |
| clarify-why-source-session-ids-were-not-saved-when-writing-ai-wiki-memory-and-in | high | 0.167 | 0.333 | 0.167 | Clarify why source session ids were not saved when writing AI wiki memory, and inspect... |
| implement-write-back-provenance-backfill-for-source-incident-timing-find-first-a | high | 1.000 | 0.667 | -0.333 | Implement write-back provenance backfill for source incident timing: find first AI Wiki... |
| clarify-whether-an-agent-can-know-current-session-id-and-duration-at-the-moment | high | 0.167 | 0.000 | -0.167 | Clarify whether an agent can know current session id and duration at the moment it writ... |
| implement-post-turn-source-incident-capture-for-ai-wiki-write-back-after-a-codex | high | 0.500 | 0.333 | -0.167 | Implement post-turn source incident capture for AI Wiki write-back: after a Codex turn... |
| session-ai-wiki-load-load-index-constraints-decisions-workflows | high | 0.500 | 0.667 | 0.167 | 用户询问新 session 启动时 AI Wiki 实际 load 了多少内容，以及是否应该只 load index，另加 constraints、decisions、wor... |
| ai-wiki-changes-push-repo | high | 0.667 | 0.667 | 0.000 | 用户确认当前 AI Wiki 行为符合预期，要求把当前本地 changes 都 push 到云端 repo |
| ai-wiki-toolkit-trial-and-error-source-incident | high | 0.667 | 1.000 | 0.333 | 用户询问 ai-wiki-toolkit 被用户下载后，是否可以自动沉淀 trial and error / source incident 经验 |
| ai-wiki-toolkit-package-post-turn-hook | high | 0.833 | 0.833 | 0.000 | 用户询问是否应该在用户下载 ai-wiki-toolkit package 时自动安装 post-turn hook |
| post-turn-hook-install-post-turn-capture-doctor-hook | high | 0.833 | 0.500 | -0.333 | 实现建议用户开启 post-turn hook：install 默认提示可开启 post-turn capture，doctor 检查/提示 hook 未启用，但不要默认启用 |
| push-current-changes-to-remote-merge-the-pr-then-release-npm-for-ai-wiki-toolkit | high | 0.333 | 1.000 | 0.667 | push current changes to remote, merge the PR, then release npm for ai-wiki-toolkit |
| ai-wiki-toolkit-index-indexing | high | 0.000 | 0.000 | 0.000 | 那我们的 ai wiki toolkit 里面的 index 是不是就是 indexing 呢？ |
| ai-wiki-toolkit-vector-indexing | high | 0.000 | 0.000 | 0.000 | 懂了 其实我们现在这 ai wiki toolkit 也没有必要做 vector indexing |
| ai-wiki-toolkit-metrics-think-hard | high | 0.333 | 0.500 | 0.167 | 我觉得现在我的这个 ai wiki toolkit 是蛮好的，但是我感觉我缺少 metrics 来告诉别人我的这个有多好。你需要 think hard |
| openai-codex-for-open-source | high | 0.667 | 0.000 | -0.667 | OpenAI Codex for Open Source 申请表字段填写建议 |
| codex-security-application-field-why-does-ai-wiki-toolkit-need-codex-security | high | 0.167 | 0.167 | 0.000 | Codex Security application field: why does ai-wiki-toolkit need Codex Security |
| aiwikitoolkit-code | high | 0.833 | 0.333 | -0.500 | 你觉得关于 aiwikitoolkit 的建议如何？先别 code 告诉我你是怎么想的 |
| route-policy-optimization-auto-research-metrics | high | 0.833 | 0.167 | -0.667 | 设计 Route Policy Optimization Auto Research 的评估，避免过拟合，选择 metrics，并寻找相关开源论文和基准 |
| ai-wiki-toolkit-development | high | 0.833 | 0.200 | -0.633 | 评估用户提供的 AI wiki toolkit 策略，结合当前 development，严谨说明已经做到什么、还可以继续做什么，不写代码 |
| workflow-vs-skills-aiwiki-toolkit-evaluation-review-repo | high | 0.833 | 0.333 | -0.500 | 评估用户对 workflow vs skills 区别的疑问，以及当前 aiwiki-toolkit 是否支持用户使用一段时间后自跑 evaluation、得到改进建议、re... |
| aiwiki-toolkit-evaluate-repo | high | 0.833 | 0.167 | -0.667 | 为 aiwiki-toolkit 设计 evaluate repo 自评估与改进建议命令的详细实施步骤，用户先要计划不要代码 |
| implementation-prompt-aiwiki-toolkit-evaluate-repo | high | 0.833 | 0.000 | -0.833 | 为新窗口生成可复制粘贴的详细 implementation prompt：实现 aiwiki-toolkit evaluate repo 自评估与改进建议命令 |
| ai-wiki-toolkit-agent-codebase | high | 0.333 | 0.250 | -0.083 | 评价别人关于增强 AI wiki toolkit 以找到 agent 工作的建议，并结合当前 codebase 给出判断 |
| project-a-eval-report-diagnostics | high | 1.000 | 0.333 | -0.667 | 补做 Project A 的测试和诊断：运行完整本地测试、eval/report diagnostics，并给出具体优化建议 |
| evals-impact-reports-route-precision-handoff-2026-06-05-md-core-doc-gating-57-tr | high | 0.333 | 0.167 | -0.167 | 请先读 evals/impact/reports/route-method-2026-06-05/route_precision_handoff_2026-06-05.md。不要直接实现 core-doc gating。先... |

## Warnings

- Historical replay is approximate when prompt recovery confidence is not exact_session or trace_task.
- Use the route-noise cohort report for forward-looking post-change production evidence.
