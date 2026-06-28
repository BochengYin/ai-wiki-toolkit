# SWE-Chain 018 Dogfood No-Router Main-Thread Rules

## Trigger

Run, review, or modify the `swe-chain-018-flask-dogfood-no-router-writeback`
experiment or another follow-up described as dogfood AI Wiki without router.

## Public/Local Signal

The user clarified on 2026-06-16 that this experiment should use the original
dogfood AI Wiki setup, remove the router layer, and let the agent write back
inside the same Codex thread. The experiment was created locally at:

`artifacts://local-swe-chain/swe-chain-018-flask-dogfood-no-router-writeback`

The local manifest and report are under that experiment's `run_config/`.

On 2026-06-16 the user clarified the next formal cross-repo panel should be
named `AI Wiki Native Writeback` / `aiwiki-native-writeback`, and should compare
three groups per repo:

- `raw-codex`
- `codex-init-agents` using Codex `/init`, not `aiwiki-toolkit init`
- `aiwiki-native-writeback`

The first gate is a five-repo panel: Flask, pytest 7, urllib3, Jinja2, and attrs.
If that gate completes without major issues, continue the same three-group
protocol across the remaining available SWE-chain repos before freezing final
claims.

In the 019 follow-up panel, the remaining xarray chains produced two public/local
failure modes:

- `xarray_2022.11.0_to_2023.7.0 / aiwiki-native-writeback` generated 25 current
  rows and an eval, but stopped during `2023.5.0 -> 2023.6.0` after the build row
  failed and the fix agent exited with code 1.
- `xarray_2025.6.0_to_2026.2.0` ran all three groups, but each group failed in
  the first build-agent call before writing any current row; the eval files have
  `None` metrics because there were no current rows to score.

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
- For cross-repo product claims, use the `AI Wiki Native Writeback` name and the
  `aiwiki-native-writeback` slug. Keep old 018 artifact names intact for
  reproducibility.
- Compare three groups per repo: raw Codex, Codex `/init` generated
  instructions, and AI Wiki Native Writeback installed on top of the initialized
  instructions.
- Treat the five-repo panel as the first gate. If it passes without major
  issues, continue the same protocol for the remaining SWE-chain repos before
  freezing final cross-repo claims.
- When a remaining-repo chain stops because Codex exits before or during an
  agent build/fix phase, record it as a chain-level agent startup/fix failure.
  Do not report `None` metrics or missing rows as model performance; explicitly
  separate "no score because no current rows" from F1 comparisons.
- If a partial chain has an eval, report metrics only for the available current
  rows and state which version step failed or was skipped.

## Applies When

- Running the 018 Flask dogfood no-router treatment.
- Creating a follow-up AI Wiki Native Writeback / no-router treatment.
- Comparing 018 against 015 or other writeback experiments.
- Designing or running the cross-repo three-group SWE-chain panel.

## Do Not Use When

- Running `swe-chain-015-flask-agent-skill-writeback`; that experiment has its
  own runner-hook protocol.
- The user asks to evaluate router quality or explicitly asks to run
  `aiwiki-toolkit route`.
- The task is a normal ai-wiki-toolkit code change unrelated to SWE-chain
  experiment setup.

## Related Files

- `artifacts://local-swe-chain/swe-chain-018-flask-dogfood-no-router-writeback/run_config/experiment_manifest.json`
- `artifacts://local-swe-chain/swe-chain-018-flask-dogfood-no-router-writeback/run_config/formal_report.md`
- `artifacts://local-swe-chain/swe-chain-018-flask-dogfood-no-router-writeback/run_config/comparison_report.md`
- `artifacts://local-swe-chain/swe-chain-018-flask-dogfood-no-router-writeback/run_config/smoke_report.md`
- `artifacts://local-swe-chain/swe-chain-018-flask-dogfood-no-router-writeback/groups/dogfood-no-router-writeback/generate/task.py`
- `artifacts://local-swe-chain/swe-chain-018-flask-dogfood-no-router-writeback/groups/dogfood-no-router-writeback/prompts/developer_build.j2`
- `artifacts://local-swe-chain/swe-chain-018-flask-dogfood-no-router-writeback/groups/dogfood-no-router-writeback/prompts/developer_fix.j2`
- `evals/impact/public/flask_swe_chain_dogfood_no_router_report.md`
- `<repo>/src/ai_wiki_toolkit/cli.py`
- `<repo>/tests/test_install_uninstall_scenarios.py`
- `<repo>/README.md`
- `<repo>/docs/usage.md`
- `artifacts://swe-chain-019/stage_b_progress.md`

## Source Pointer

- Source: User clarification in Codex while setting up and running the 018
  experiment.
- Captured by: Codex.
- Captured at: 2026-06-16.
- Updated from local 019 Stage B xarray panel results on 2026-06-26.
