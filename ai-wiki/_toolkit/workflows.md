# Toolkit Managed Workflows

This file is managed by ai-wiki-toolkit. Future package versions may update it.

## AI Wiki Maintenance

1. Run one AI wiki reuse check at the end of every completed task, even when no AI wiki docs were used.
2. If any user-owned repo or system AI wiki docs were consulted, record one `aiwiki-toolkit record-reuse` event per consulted doc.
3. Do not log managed `_toolkit/**` docs with `record-reuse`; if they changed the plan or behavior, cite their paths in a progress update or the final note instead.
4. Record one `aiwiki-toolkit record-reuse-check` entry for the task using `wiki_used` or `no_wiki_use`.
5. Metrics logs should shard by handle under `ai-wiki/metrics/reuse-events/<handle>.jsonl` and `ai-wiki/metrics/task-checks/<handle>.jsonl` to reduce merge conflicts in team workflows.
6. If generated files under `ai-wiki/_toolkit/catalog.json` or `ai-wiki/_toolkit/metrics/*.json` drift or conflict after a merge, rerun `aiwiki-toolkit refresh-metrics` instead of hand-merging them.
7. Run one AI wiki update check at the end of every completed task, even when the result is `None`.
8. Always end with exactly one status line: `AI Wiki Update Candidate: None`, `Draft`, or `PromotionCandidate`.
9. If the result is `Draft` or `PromotionCandidate`, also print `AI Wiki Update Path: <path>`.
10. Put reusable repo-specific lessons in `ai-wiki/review-patterns/`.
11. Put task-specific chronology and dead ends in `ai-wiki/trails/`.
12. Put raw personal draft notes in `ai-wiki/people/<handle>/drafts/`.
13. Promote only stable, reviewable rules into shared patterns.
