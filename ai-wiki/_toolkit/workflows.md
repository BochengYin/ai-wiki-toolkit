# Toolkit Managed Workflows

This file is managed by ai-wiki-toolkit. Future package versions may update it.

## AI Wiki Maintenance

1. Start with the bounded memory read from `system.md`: read `ai-wiki/memory/index.md` if present, then open at most one strongly relevant linked memory file.
2. Do not run `aiwiki-toolkit route` as the normal task-start path. Use it only for explicit route diagnostics or when the bounded index is insufficient for a clearly memory-relevant task.
3. Produce one AI wiki reuse evidence footer at the end of every completed task.
4. First classify the task as `relevant`, `optional`, or `not_relevant` for AI wiki use.
5. Record one `aiwiki-toolkit record-reuse` event per consulted user-owned AI wiki doc.
6. Do not log managed `_toolkit/**` docs with `record-reuse`; if they changed the plan or behavior, cite their paths in a progress update or the final note instead.
7. Record one `aiwiki-toolkit record-reuse-check` entry for the task using `wiki_used` or `no_wiki_use`.
8. Treat the footer as the user-facing evidence surface; telemetry and generated aggregates are the local machine-readable record behind it.
9. The installer manages a `.gitignore` block that ignores `.env.aiwiki`, `ai-wiki/metrics/reuse-events/`, `ai-wiki/metrics/route-traces/`, `ai-wiki/metrics/source-incidents/`, `ai-wiki/metrics/taxonomy-evidence/`, `ai-wiki/metrics/task-checks/`, `ai-wiki/_toolkit/consolidation/`, `ai-wiki/_toolkit/diagnostics/`, `ai-wiki/_toolkit/metrics/`, `ai-wiki/_toolkit/reports/`, `ai-wiki/_toolkit/work/`, and `ai-wiki/_toolkit/catalog.json` so local identity, telemetry, and generated views stay local by default.
10. If those local-state paths were tracked before you upgraded, run `aiwiki-toolkit doctor` and follow the suggested `git rm --cached` fix once to untrack them.
11. Produce one AI wiki write-back outcome at the end of every completed task, even when the result is `None`.
12. If runtime skill exposure is missing, follow the Runtime Skill Fallback section in `system.md` and manually read the relevant repo-local skill files under `.agents/skills/`.
13. Before returning `None`, check for public/local trial-error, reusable clarification, missed relevant memory, and conflicts with existing memory.
14. Write back only after a concrete durable signal such as failed local/public checks, repeated trial-and-error, or a reusable clarification. Do not write every task summary into the wiki.
15. Put recorded memories under `ai-wiki/memory/` and keep `ai-wiki/memory/index.md` as the bounded read entrypoint.
16. Always end with exactly one status line: `AI Wiki Write-Back: none` or `AI Wiki Write-Back: memory recorded`.
17. If memory was recorded, also print `AI Wiki Write-Back Path: <path>`.
18. Put todo, active, processing, blocked, review, done, and archived work state in `ai-wiki/work/events/<handle>.jsonl` via `aiwiki-toolkit work`.
