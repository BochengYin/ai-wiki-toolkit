# Toolkit Managed Workflows

This file is managed by ai-wiki-toolkit. Future package versions may update it.

## AI Wiki Maintenance

1. Run one AI wiki reuse check at the end of every completed task, even when no AI wiki docs were used.
2. If any user-owned repo or system AI wiki docs were consulted, record one `aiwiki-toolkit record-reuse` event per consulted doc.
3. Do not log managed `_toolkit/**` docs with `record-reuse`; if they changed the plan or behavior, cite their paths in a progress update or the final note instead.
4. Record one `aiwiki-toolkit record-reuse-check` entry for the task using `wiki_used` or `no_wiki_use`.
5. The installer manages a `.gitignore` block that ignores `ai-wiki/metrics/reuse-events/`, `ai-wiki/metrics/task-checks/`, `ai-wiki/_toolkit/metrics/`, and `ai-wiki/_toolkit/catalog.json` so telemetry stays local by default.
6. If those telemetry paths were tracked before you upgraded, run `aiwiki-toolkit doctor` and follow the suggested `git rm --cached` fix once to untrack them.
7. Run one AI wiki update check at the end of every completed task, even when the result is `None`.
8. Always end with exactly one status line: `AI Wiki Update Candidate: None`, `Draft`, or `PromotionCandidate`.
9. If the result is `Draft` or `PromotionCandidate`, also print `AI Wiki Update Path: <path>`.
10. Do not write every task summary into the wiki; capture only durable memory.
11. Put shared team conventions in `ai-wiki/conventions/`.
12. Put reusable repo-specific review lessons in `ai-wiki/review-patterns/`.
13. Put reusable problem-solution memories in `ai-wiki/problems/`.
14. Put feature clarifications in `ai-wiki/features/`.
15. Put task-specific chronology and dead ends in `ai-wiki/trails/`.
16. Put raw personal draft notes in `ai-wiki/people/<handle>/drafts/`.
17. Promote only stable, reviewable rules into shared patterns or conventions.
