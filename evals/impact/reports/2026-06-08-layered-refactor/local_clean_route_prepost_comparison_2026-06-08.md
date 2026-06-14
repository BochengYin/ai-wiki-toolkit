# Clean Route Pre/Post Layer Comparison

Generated at: `2026-06-08T14:05:06+10:00`

## Method

This comparison reran the same local replay cohort with:

- route trace cohort: all replay-evaluable traces, `target_evaluable_traces=9999`
- replayed traces: `58`
- prompt recovery: `58 / 58`, unmatched `0`
- catalog cutoff: `trace-routed-at`
- repo data and labels: current checkout `ai-wiki/` via `--repo-root <local repo> --repo-wiki-dir <local repo>/ai-wiki`
- changed-path policy: replay-recovered explicit changed paths only

Router code versions:

- `914e845` - route precision tooling before the layer-evaluation commit
- `1aa3a26` - direct parent of `5c3c93d`
- `5c3c93d` - current layered route evaluation and feedback tooling

The old router was executed from temporary git worktrees; outputs were written under `evals/impact/reports/`.

## Aggregate Results

| router code | replayed | route_precision | noise | selected_docs | selected_useful | missed_useful | failed_route@selected | retrieval_precision | candidate20 coverage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `914e845` | 58 | 0.363 | 0.637 | 284 | 103 | 59 | n/a | n/a | n/a |
| `1aa3a26` parent | 58 | 0.363 | 0.637 | 284 | 103 | 59 | 16 / 0.276 | n/a | n/a |
| `5c3c93d` current | 58 | 0.361 | 0.639 | 296 | 107 | 58 | 13 / 0.224 | 0.358 | 0.707 |

Current vs direct parent (`5c3c93d - 1aa3a26`):

- route_precision: `-0.001`
- route_noise_rate: `+0.001`
- selected_docs: `+12`
- selected_useful: `+4`
- missed_useful: `-1`
- failed_route@selected: `-0.052`

`914e845` and `1aa3a26` produced the same aggregate replay metrics, so `1aa3a26` is a valid immediate pre-layer comparison point for this run.

## Paired Trace Changes

Paired by `trace_id`, not `task_id`, because one task id appears twice in the 58-trace cohort.

- paired traces: `58`
- traces with selected set/count/useful/missed change: `9`
- traces unchanged in selected set/count/useful/missed: `49`
- total selected docs delta: `+12`
- total selected useful delta: `+4`
- total missed useful delta: `-1`

| task_id | selected | selected_useful | missed_useful | added useful docs | task |
| --- | ---: | ---: | ---: | --- | --- |
| `draft-reuse-3-promote` | 0 -> 1 | 0 -> 0 | 4 -> 4 | none | 查找是否有 draft reuse 超过 3 次就应该 promote 的历史记录 |
| `clarify-whether-an-agent-can-know-current-session-id-and-duration-at-the-moment` | 0 -> 1 | 0 -> 0 | 0 -> 0 | none | Clarify whether an agent can know current session id and duration at the momen... |
| `ai-wiki-toolkit-trial-and-error-source-incident` | 0 -> 1 | 0 -> 1 | 2 -> 1 | `people/bochengyin/drafts/source-incident-timing-needs-provenance` | 用户询问 ai-wiki-toolkit 被用户下载后，是否可以自动沉淀 trial and error / source incident 经验 |
| `explain-why-historical-local-codex-sessions-are-not-enough-to-safely-infer-sourc` | 0 -> 6 | 0 -> 2 | 0 -> 0 | `people/bochengyin/drafts/codex-session-recovery-should-search-jsonl-and-state-db`, `people/bochengyin/drafts/efficiency-eval-should-include-source-incident-cost` | Explain why historical local Codex sessions are not enough to safely infer sou... |
| `push-current-changes-and-release-a-new-version` | 0 -> 1 | 0 -> 0 | 1 -> 1 | none | push current changes and release a new version |
| `promote-draft-ai-wiki-people-bochengyin-index-md` | 0 -> 1 | 0 -> 0 | 3 -> 3 | none | 检查是否已有自动 promote draft 到 ai-wiki/people/bochengyin/index.md 的机制 |
| `project-a-eval-report-diagnostics` | 6 -> 6 | 2 -> 2 | 4 -> 4 | none | 补做 Project A 的测试和诊断：运行完整本地测试、eval/report diagnostics，并给出具体优化建议 |
| `post-turn-hook-install-post-turn-capture-doctor-hook` | 6 -> 6 | 3 -> 3 | 0 -> 0 | none | 实现建议用户开启 post-turn hook：install 默认提示可开启 post-turn capture，doctor 检查/提示 hook 未启... |
| `push-current-changes-to-remote-merge-the-pr-then-release-npm-for-ai-wiki-toolkit` | 0 -> 1 | 0 -> 1 | 1 -> 1 | `conventions/distribution-target-matrix-must-match-published-assets` | push current changes to remote, merge the PR, then release npm for ai-wiki-too... |

## Interpretation

This clean comparison does not support the claim that the layer refactor caused the large gap versus the historical trace baseline.
Before the layer-evaluation commit, the same 58-prompt replay was already around route_precision `0.363` with `103` selected useful docs and `59` missed useful docs.
After the layer-evaluation commit, route_precision is `0.361`, selected useful increases by `+4`, missed useful improves by `-1`, and selected docs increase by `+12`.

The tradeoff is therefore small and mixed: current layering added more docs, found a few more useful docs, and slightly diluted precision. It did not explain the earlier replay-vs-historical-baseline drop from about `0.531` to about `0.36`; that drop predates this layer-evaluation commit.

The fields `retrieval_precision`, `candidate20 coverage`, eval-stage confusion, and selected+maybe failed-route rates are current-version diagnostics, not apples-to-apples fields emitted by the old router report. They are useful for debugging current Route Core, but they should not be treated as pre/post regression metrics for `1aa3a26`.

## Conclusion

The cleaner comparison says: the three-layer evaluation/feedback commit is not the main source of the route replay regression. The regression relative to historical selected docs was already present in the pre-layer router. The current commit adds diagnostic layers and slightly changes selection behavior; it creates a small precision/recall tradeoff, not a catastrophic route-quality regression.

Next local step, if needed: inspect why the pre-layer router already sits near `0.363` against a historical selected-doc baseline near `0.531`, using the changed traces plus the older regression diagnosis. A full bisect is not necessary for the layer commit question unless we want to find the earlier commit where replay first dropped below historical trace quality.
