# AI Wiki Hook Design Should Integrate, Not Copy

## Trigger

Read when designing, implementing, or evaluating hook-based AI Wiki workflow
support, especially Codex `SessionStart`, `UserPromptSubmit`, `PostToolUse`, or
`Stop` hooks.

## Public/Local Signal

The user clarified that `aiwiki-toolkit` should not copy the external
self-improving-agent design verbatim. Hook behavior should be adapted into the
AI Wiki workflow and product boundaries.

## Failed Attempt

Treating `pskoett/self-improving-agent` as a template to copy would push the
toolkit toward `.learnings/` and generic self-improvement prompts instead of the
repo's existing AI Wiki memory, reuse evidence, and write-back contracts.

## Fix Or Rule

Use external self-improvement hooks as inspiration only. For `aiwiki-toolkit`,
prefer moving the existing managed AI Wiki prompt guidance from `AGENTS.md` and
`CLAUDE.md` into lifecycle hooks where supported, starting with `SessionStart`
for session-level workflow context and keeping prompt files as fallback for
agents or environments without hooks.

## Applies When

- Adding hook installation or hook runtime support.
- Comparing hook-only versus prompt-file managed block experiments.
- Designing experiments for AI Wiki memory accumulation.

## Do Not Use When

- The task only concerns unrelated release, packaging, or diagnostics behavior.
- A user explicitly asks to copy or install the external self-improving-agent
  skill unchanged for a separate project.

## Related Files

- `src/ai_wiki_toolkit/content.py`
- `src/ai_wiki_toolkit/prompt.py`
- `src/ai_wiki_toolkit/scaffold.py`
- `tests/test_prompt_scenarios.py`
- `tests/test_install_uninstall_scenarios.py`

## Source Pointer

- Source: User clarification in Codex session on 2026-06-21.
- Captured by: Codex.
