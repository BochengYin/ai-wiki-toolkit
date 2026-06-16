# SWE-Chain 017 Toolkit Hook vs 015 Agent-Skill Rules

## Trigger

Compare the currently running or recently run
`swe-chain-017-flask-aiwiki-toolkit-hook-writeback` experiment against
`swe-chain-015-flask-agent-skill-writeback`, especially when both are described as
"after-conversation writeback" or "agent-skill writeback".

## Public/Local Signal

Local experiment configuration shows both workflows are runner-triggered after normal
Codex completion and before revealed feedback, but they exercise different writeback
implementations and memory directories.

## Failed Attempt

Treating 017 and 015 agent-skill writeback as the same experiment is misleading because
both use a runner-managed end-of-turn trigger. The shared trigger hides the main
difference: 015 is a bespoke fork-plus-skill prototype, while 017 is a package-managed
`aiwiki-toolkit writeback setup` hook/runtime test.

## Fix Or Rule

- 015 agent-skill writeback uses the experiment harness protocol: runner normal-end hook,
  real `codex fork`, trial-error writeback skill, candidate files under
  `/app/ai-wiki/memory_quarantine/<attempt_id>/`, deterministic audit, then published
  memory under `/app/ai-wiki/memory/`.
- 017 toolkit hook writeback uses the packaged toolkit protocol: `aiwiki-toolkit
  writeback setup` installs `.codex/hooks/aiwiki_enqueue_writeback.py` plus
  `.agent/_toolkit/writeback/runtime`; accepted notes publish under
  `.agent/memories/notes/` with `.agent/memories/index.md`.
- Both are runner-managed after-conversation workflows, not main-thread writeback.
  Compare 018 separately: 018 removes the router and has the main thread write memory
  directly in the dogfood checkout.
- Do not treat an in-progress 017 isolated app state as a completed full-chain metric
  until a formal `chain.json`/`eval.json` for the intended chain is present.
- If the product question is whether dogfood needs the router layer, 018 is the
  stronger direct comparison. Stop or deprioritize 017 unless the question is
  specifically packaged hook/runtime behavior.

## Applies When

- Explaining, comparing, or rerunning 017 vs 015 agent-skill writeback.
- Deciding whether a result tested the aiwiki-toolkit packaged hook/runtime or only the
  earlier experiment harness writeback prototype.

## Do Not Use When

- Comparing 015 harness trial-error against 015 agent-skill writeback; that is a separate
  within-015 comparison.
- Running the no-router dogfood main-thread setup from 018, except to note that 018 is not
  hook-based.

## Related Files

- `/Users/by/AI Project/AI wiki Toolkit test repos/swe-chain-015-flask-agent-skill-writeback/run_config/experiment_manifest.json`
- `/Users/by/AI Project/AI wiki Toolkit test repos/swe-chain-017-flask-aiwiki-toolkit-hook-writeback/run_config/flask-toolkit-writeback-AGENTS.md`
- `/Users/by/AI Project/AI wiki Toolkit test repos/swe-chain-017-flask-aiwiki-toolkit-hook-writeback/groups/aiwiki-toolkit-hook-writeback/generate/task.py`
- `/Users/by/AI Project/ai-wiki-toolkit/evals/impact/public/flask_swe_chain_dogfood_no_router_report.md`

## Source Pointer

- Source: Local experiment manifests, AGENTS prompt, and runner code while clarifying 017
  vs 015 agent-skill writeback.
- Captured by: Codex.
- Captured at: 2026-06-16.
