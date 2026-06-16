# SWE-Chain 018 Dogfood No-Router Main-Thread Rules

## Trigger

Run, review, or modify the `swe-chain-018-flask-dogfood-no-router-writeback`
experiment or another follow-up described as dogfood AI Wiki without router.

## Public/Local Signal

The user clarified on 2026-06-16 that this experiment should use the original
dogfood AI Wiki setup, remove the router layer, and let the agent write back
inside the same Codex thread. The experiment was created locally at:

`/Users/by/AI Project/AI wiki Toolkit test repos/swe-chain-018-flask-dogfood-no-router-writeback`

The local manifest and report are under that experiment's `run_config/`.

## Failed Attempt

The closest prior experiment, `swe-chain-015-flask-agent-skill-writeback`, used a
runner-managed normal-end hook for writeback. Reusing that hook protocol for this
experiment would be wrong because the user explicitly wanted dogfood main-thread
writeback instead.

Another wrong setup is to keep calling `aiwiki-toolkit route`; this experiment is
specifically testing dogfood behavior without the router layer.

## Fix Or Rule

For `swe-chain-018-flask-dogfood-no-router-writeback`:

- Use dogfood AI Wiki install output: generated `AGENTS.md`, `ai-wiki/`, and
  `.agents/skills/`.
- Copy `.agents/skills/` into the isolated app so the main Codex thread can use
  the AI Wiki end-of-task skills.
- Do not run `aiwiki-toolkit route`.
- The main Codex build/fix thread performs the bounded memory index read,
  reuse footer, and write-back outcome.
- When writeback is warranted, the same thread writes or updates
  `ai-wiki/memory/*.md` and `ai-wiki/memory/index.md`.
- Do not use the 015 runner fork/hook writeback protocol except as a separate
  baseline or control.
- After the 018 full Flask run matched the strongest 015 Build+fix F1 band,
  deprioritize or stop 017 toolkit-hook runs when the question is whether
  dogfood needs the router layer. 017 is still useful later as a packaged
  hook/runtime or host-lifecycle validation, but it answers a different question.
- For the ai-wiki-toolkit product default, expose 018 through `aiwiki-toolkit
  install`: managed prompt/system docs plus repo-local reuse/write-back skills.
  Do not make users run a new router, lifecycle hook, or forked writeback command
  for the default path.
- Match the prior Flask SWE-chain setup with `codex`, `openai`, `gpt-5.5`,
  `high`, and `max_iters=2` unless the user changes the comparison.
- Smoke-test the setup before running the full Flask chain when changing the
  treatment protocol.
- For recall, precision, and F1 comparisons, run the group evaluator with
  `bash eval.sh <chain.json> 2 live` to create `eval.json`. Native metrics come
  from test-level TP/FN/FP classification in `eval.json`; holdout pass rate is a
  separate outcome and should not be reported as F1. Older 014 eval artifacts do
  not include `final_holdout` classification rows, so report those as `N/A`
  instead of inferring them from pass rates.

## Applies When

- Running the 018 Flask dogfood no-router treatment.
- Creating a follow-up dogfood no-router treatment.
- Comparing 018 against 015 or other writeback experiments.

## Do Not Use When

- Running `swe-chain-015-flask-agent-skill-writeback`; that experiment has its
  own runner-hook protocol.
- The user asks to evaluate router quality or explicitly asks to run
  `aiwiki-toolkit route`.
- The task is a normal ai-wiki-toolkit code change unrelated to SWE-chain
  experiment setup.

## Related Files

- `/Users/by/AI Project/AI wiki Toolkit test repos/swe-chain-018-flask-dogfood-no-router-writeback/run_config/experiment_manifest.json`
- `/Users/by/AI Project/AI wiki Toolkit test repos/swe-chain-018-flask-dogfood-no-router-writeback/run_config/formal_report.md`
- `/Users/by/AI Project/AI wiki Toolkit test repos/swe-chain-018-flask-dogfood-no-router-writeback/run_config/comparison_report.md`
- `/Users/by/AI Project/AI wiki Toolkit test repos/swe-chain-018-flask-dogfood-no-router-writeback/run_config/smoke_report.md`
- `/Users/by/AI Project/AI wiki Toolkit test repos/swe-chain-018-flask-dogfood-no-router-writeback/groups/dogfood-no-router-writeback/generate/task.py`
- `/Users/by/AI Project/AI wiki Toolkit test repos/swe-chain-018-flask-dogfood-no-router-writeback/groups/dogfood-no-router-writeback/prompts/developer_build.j2`
- `/Users/by/AI Project/AI wiki Toolkit test repos/swe-chain-018-flask-dogfood-no-router-writeback/groups/dogfood-no-router-writeback/prompts/developer_fix.j2`
- `/Users/by/AI Project/ai-wiki-toolkit/evals/impact/public/flask_swe_chain_dogfood_no_router_report.md`
- `/Users/by/AI Project/ai-wiki-toolkit/src/ai_wiki_toolkit/cli.py`
- `/Users/by/AI Project/ai-wiki-toolkit/tests/test_install_uninstall_scenarios.py`
- `/Users/by/AI Project/ai-wiki-toolkit/README.md`
- `/Users/by/AI Project/ai-wiki-toolkit/docs/usage.md`

## Source Pointer

- Source: User clarification in Codex while setting up and running the 018
  experiment.
- Captured by: Codex.
- Captured at: 2026-06-16.
