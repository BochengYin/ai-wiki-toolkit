# Toolkit Managed System Rules

This file is managed by ai-wiki-toolkit. Future package versions may update it.

## Start Of Task

1. Do not run a router or load broad wiki areas by default.
2. If `ai-wiki/memory/index.md` exists, read that index first. Treat it as a routing index, not as task evidence.
3. Open at most one linked memory file before acting, and only when it directly matches the current source file, API, command, behavior, or repeated public/local failure.
4. If no memory index exists or no entry is strongly relevant, proceed without memory instead of searching `ai-wiki/**`.
5. Read `ai-wiki/constraints.md` only when the task involves code edits, release, security, compatibility, data handling, or user-owned AI wiki files.
6. Read another specific user-owned AI wiki doc only when the memory index, constraints file, user request, or current work explicitly points to it.
7. Use `ai-wiki/index.md` only as a map when you need to locate a specific user-owned doc; do not use it as permission to read every area.
8. `aiwiki-toolkit route` is optional diagnostic tooling. Use it only when the user asks for routing, you are debugging route quality, or the bounded memory index is insufficient for a clearly memory-relevant task.
9. If repo docs are not enough, read `<home>/ai-wiki/system/_toolkit/system.md` and then `<home>/ai-wiki/system/index.md` only when cross-project memory is directly relevant.
10. If `ai-wiki-clarify-before-code` is available, use it before implementation when ambiguity materially affects coding.
11. If `ai-wiki-capture-review-learning` is available, use it when reusable review feedback appears.
12. If `ai-wiki-reuse-check` and `ai-wiki-update-check` skills are available, use them to produce end-of-task AI wiki evidence and write-back outcomes.

## Bounded Memory Read

1. Prefer `ai-wiki/memory/index.md` over direct filesystem search.
2. Open at most one memory file during task start.
3. Open a memory file only for a strong match: same file, API, command, behavior, or repeated public/local failure surface.
4. Do not read memory solely because it was written in the previous task or previous chain step.
5. Do not read all memory files.
6. Never use hidden evaluator failures, hidden test names, private benchmark answers, or prior hidden-derived fixes as memory.

## Runtime Skill Fallback

1. Repo-local AI wiki skills live under `.agents/skills/<skill-name>/`.
2. Runtime skill discovery can differ from files on disk. If a needed AI wiki skill is not exposed by the active runtime, manually read `.agents/skills/<skill-name>/SKILL.md` and relevant files under `.agents/skills/<skill-name>/references/`.
3. For end-of-task reuse evidence, if `ai-wiki-reuse-check` is unavailable, read `.agents/skills/ai-wiki-reuse-check/SKILL.md` and `.agents/skills/ai-wiki-reuse-check/references/output-contract.md`.
4. For end-of-task write-back, if `ai-wiki-update-check` is unavailable, read `.agents/skills/ai-wiki-update-check/SKILL.md` and `.agents/skills/ai-wiki-update-check/references/output-contract.md`.
5. Do not skip the required AI wiki footer just because the runtime reports no available skills.

## AI Wiki Reuse Evidence

1. Produce one AI wiki reuse evidence footer at the end of every completed task.
2. First classify the task as `relevant`, `optional`, or `not_relevant` for AI wiki use.
3. Treat pure operational tasks such as pushing a PR, renaming a branch, or running an already-decided command as `not_relevant`; do not force unrelated wiki reads just to improve coverage metrics.
4. If any user-owned repo or system AI wiki docs were consulted, record one `aiwiki-toolkit record-reuse` event per consulted document.
5. If a managed `_toolkit/**` doc changed the plan or behavior, cite its path in a progress update or final note, but do not record it with `record-reuse`.
6. When a user-owned AI wiki doc materially changes the plan or behavior, cite its path in a progress update or final note.
7. Use `reuse_outcome=not_helpful` when a consulted user-owned AI wiki document did not help materially but still influenced the search path.
8. Record one `aiwiki-toolkit record-reuse-check` entry for the task with:
   - `wiki_used` when one or more AI wiki document events were recorded
   - `no_wiki_use` when no AI wiki document events were needed for the task

## AI Wiki Write-Back Outcome

1. Produce one AI wiki write-back outcome at the end of every completed task, even when you expect the result to be `None`.
2. Before returning `None`, check only for durable public/local write-back signals:
   - a failed local/public check that changed the fix
   - repeated public trial-and-error on the same source file, API, command, or behavior
   - a reusable tooling, packaging, or environment mismatch found through local/public evidence
   - a reusable clarification from the user that future tasks in this repo should apply
3. Do not write memory from hidden evaluator failures, hidden test names, private benchmark answers, or prior hidden-derived fixes.
4. Do not write back after a clean one-shot task unless it produced a reusable clarification or public/local trial-error lesson.
5. If memory is recorded, write or update a small file under `ai-wiki/memory/` and add or update one entry in `ai-wiki/memory/index.md` with the trigger, related files, and source pointer.
6. Choose exactly one outcome:
   - `None`: you checked and found no durable public/local lesson worth recording.
   - `MemoryRecorded`: you recorded a small public/local trial-error or clarification memory under `ai-wiki/memory/`.
7. Prefer small durable memory over long task transcripts or generic summaries.
8. If new memory conflicts with existing constraints or user-owned memory, flag the conflict instead of silently overwriting.
9. If a relevant existing AI wiki doc should have been used but was missed, mention the miss instead of silently returning `None`.
10. Always print exactly one final status line:
   - `AI Wiki Write-Back: none`
   - `AI Wiki Write-Back: memory recorded`
11. If the outcome is `MemoryRecorded`, also print:
   - `AI Wiki Write-Back Path: <path>`
