# Route Schema v1

`aiwiki-toolkit route` generates a transient AI Wiki Context Packet for the current task.

The packet is a derived view, not canonical memory. Markdown files under `ai-wiki/`
remain the source of truth.

## Packet Fields

- `schema_version`: currently `route-v1`.
- `task_id`: stable task id, either supplied by the caller or derived from the task text.
- `task`: current user request text, when supplied by the agent.
- `route.task_type`: coarse task class such as `scaffold_prompt_workflow`, `release_distribution`, `memory_governance`, `workflow_state`, `eval_workflow`, or `general`.
- `route.risk_tags`: task risks such as `user_owned_docs`, `managed_prompt_block`, `release_distribution`, `ci_workflow`, `memory_governance`, `workflow_state`, or `task_evaluation`.
- `route.changed_paths`: path signals supplied by the caller or inferred from `git status --short`.
- `actor`: resolved local actor handle from CLI/environment, `.env.aiwiki`, git config, or fallback.
- `route.effort`: coarse effort level such as `low`, `normal`, or `deep`.
- `context_budget`: safety cap and document limits for the packet. The word value is not a fill target; route may use less.
- `routing_strategy`: how the packet expects agents to use direct context versus runtime references.
- `work_context`: actor-scoped matching work-ledger items from `ai-wiki/_toolkit/work/state.json`, when available.
  Work items include `actor_relation` so agents can distinguish assigned, reported, unassigned, and other matched work.
- `success_criteria`: generated task guidance with criteria and verification checks. These items are derived from task signals and are not canonical memory.
- `index_cards`: short name/description/reference cards for selected docs and runtime references.
- `must_load`: authoritative user-owned AI wiki docs the agent should consult directly when required.
- `maybe_load`: lower-confidence docs that may help if the task needs more context.
- `must_follow`: source-cited rules extracted from authoritative user-owned docs.
- `context_notes`: source-cited notes from exploratory docs such as drafts.
- `skip`: docs intentionally not loaded because the route found no strong signal.
- `trust_model`: reminders about provenance and source-of-truth boundaries.

## Trust Rules

1. Every `must_follow` rule must cite a user-owned source path.
2. Drafts and trails may provide `context_notes`, but they should not become authoritative rules unless promoted by the existing human-confirmed workflow.
3. Managed `_toolkit/**` docs can guide routing behavior, but they should not be recorded as user-owned reuse events.
4. If the packet looks wrong or incomplete, agents should fall back to the baseline read order in `ai-wiki/_toolkit/system.md`.
5. Record reuse only for user-owned docs actually consulted or materially used, not for every packet candidate.
6. Treat `work_context` items with `actor_relation=assignee` as actionable for the current actor. Treat other matched work as context unless the user explicitly asks to work on it.
7. Prefer index cards and runtime references over loading broad full documents. Simple operational tasks should follow the specific workflow they need instead of pulling in broad memory.
8. Treat `success_criteria` as generated planning help. Agents may refine it, but should not cite it as a source of truth.
