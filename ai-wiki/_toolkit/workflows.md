# Toolkit Managed Workflows

This file is managed by ai-wiki-toolkit. Future package versions may update it.

## AI Wiki Maintenance

1. Produce one AI wiki reuse evidence footer at the end of every completed task.
2. First classify the task as `eligible`, `optional`, or `not_applicable` for AI wiki use.
3. Record one `aiwiki-toolkit record-reuse` event per consulted user-owned AI wiki doc.
4. Do not log managed `_toolkit/**` docs with `record-reuse`; if they changed the plan or behavior, cite their paths in a progress update or the final note instead.
5. Record one `aiwiki-toolkit record-reuse-check` entry for the task using `wiki_used` or `no_wiki_use`.
6. Treat the footer as the user-facing evidence surface; telemetry and generated aggregates are the local machine-readable record behind it.
7. The installer manages a `.gitignore` block that ignores `ai-wiki/metrics/reuse-events/`, `ai-wiki/metrics/task-checks/`, `ai-wiki/_toolkit/metrics/`, and `ai-wiki/_toolkit/catalog.json` so telemetry stays local by default.
8. If those telemetry paths were tracked before you upgraded, run `aiwiki-toolkit doctor` and follow the suggested `git rm --cached` fix once to untrack them.
9. Produce one AI wiki update outcome at the end of every completed task, even when the result is `None`.
10. Before returning `None`, run memory candidate detection for problem-solution memory, feature clarification memory, convention candidates, missed relevant memory, and conflict or supersession.
11. Always end with exactly one status line: `AI Wiki Update Candidate: None`, `Draft`, or `PromotionCandidate`.
12. If the result is `Draft` or `PromotionCandidate`, also print `AI Wiki Update Path: <path>`.
13. Do not write every task summary into the wiki; capture only durable memory.
14. Put shared team conventions in `ai-wiki/conventions/`.
15. Put reusable repo-specific review lessons in `ai-wiki/review-patterns/`.
16. Put reusable problem-solution memories in `ai-wiki/problems/`.
17. Put feature clarifications in `ai-wiki/features/`.
18. Put task-specific chronology and dead ends in `ai-wiki/trails/`.
19. Put raw personal draft notes in `ai-wiki/people/<handle>/drafts/`.
20. Promote only stable, reviewable rules into shared patterns or conventions.
