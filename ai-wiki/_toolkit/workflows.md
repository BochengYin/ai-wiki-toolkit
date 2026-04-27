# Toolkit Managed Workflows

This file is managed by ai-wiki-toolkit. Future package versions may update it.

## AI Wiki Maintenance

1. Start each non-trivial task by running `aiwiki-toolkit route --task "<current user request>"` when available.
2. Use the route packet to decide which user-owned docs to consult first, but record reuse only for docs actually consulted or materially used.
3. Produce one AI wiki reuse evidence footer at the end of every completed task.
4. First classify the task as `relevant`, `optional`, or `not_relevant` for AI wiki use.
5. Record one `aiwiki-toolkit record-reuse` event per consulted user-owned AI wiki doc.
6. Do not log managed `_toolkit/**` docs with `record-reuse`; if they changed the plan or behavior, cite their paths in a progress update or the final note instead.
7. Record one `aiwiki-toolkit record-reuse-check` entry for the task using `wiki_used` or `no_wiki_use`.
8. Treat the footer as the user-facing evidence surface; telemetry and generated aggregates are the local machine-readable record behind it.
9. The installer manages a `.gitignore` block that ignores `ai-wiki/metrics/reuse-events/`, `ai-wiki/metrics/task-checks/`, `ai-wiki/_toolkit/metrics/`, and `ai-wiki/_toolkit/catalog.json` so telemetry stays local by default.
10. If those telemetry paths were tracked before you upgraded, run `aiwiki-toolkit doctor` and follow the suggested `git rm --cached` fix once to untrack them.
11. Produce one AI wiki write-back outcome at the end of every completed task, even when the result is `None`.
12. Before returning `None`, run memory candidate detection for problem-solution memory, feature clarification memory, convention candidates, missed relevant memory, and conflict or supersession.
13. Always end with exactly one status line: `AI Wiki Write-Back: none`, `draft recorded`, or `promotion candidate`.
14. If the result is `Draft` or `PromotionCandidate`, also print `AI Wiki Write-Back Path: <path>`.
15. Do not write every task summary into the wiki; capture only durable memory.
16. Put shared team conventions in `ai-wiki/conventions/`.
17. Put reusable repo-specific review lessons in `ai-wiki/review-patterns/`.
18. Put reusable problem-solution memories in `ai-wiki/problems/`.
19. Put feature clarifications in `ai-wiki/features/`.
20. Put task-specific chronology and dead ends in `ai-wiki/trails/`.
21. Put raw personal draft notes in `ai-wiki/people/<handle>/drafts/`.
22. Promote only stable, reviewable rules into shared patterns or conventions.
