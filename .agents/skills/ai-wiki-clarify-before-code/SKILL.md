---
name: ai-wiki-clarify-before-code
description: Use before implementation when a request is ambiguous enough that coding directly may create wrong behavior, wrong tests, wrong API shape, wrong data model, wrong permission behavior, or wrong long-term team memory.
---

# AI Wiki Clarify Before Code

Use this skill before implementation when a request is ambiguous enough that coding directly may create wrong behavior, wrong tests, wrong API shape, wrong data model, wrong permission behavior, or wrong long-term team memory.

Do not ask generic questions just to be safe. Ask only questions that materially affect implementation.

## Workflow

1. Read the task.
2. Read relevant AI wiki context:
   - `ai-wiki/conventions/index.md`
   - `ai-wiki/decisions.md`
   - `ai-wiki/review-patterns/index.md`
   - `ai-wiki/problems/index.md`
   - `ai-wiki/features/index.md` when feature context matters
3. Identify known constraints.
4. Identify blocking unknowns.
5. Identify non-blocking assumptions.
6. Decide whether the agent is ready to code.
7. Propose wiki updates only for durable learnings.

## Output Contract

Use the output format in [references/output-contract.md](references/output-contract.md).

## Rules

- Do not treat inferred assumptions as confirmed requirements.
- Do not block coding on unknowns that do not affect implementation.
- Prefer 3-5 high-impact questions over a long generic questionnaire.
- If new information conflicts with existing AI wiki memory, flag it in the workflow.
- If a clarification becomes durable, propose a feature note, decision, convention, or problem-solution memory.
