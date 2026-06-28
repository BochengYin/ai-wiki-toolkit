# Eval Coverage Status

This table records which copied/known experiment cells have valid build+fix metrics, which are partial, and which are empty shells.
It is meant to prevent accidental citation of incomplete `eval.json` files while drafting the report.
It was refreshed after the 2026-06-28 resume and exact-fill completions.

## Status Rules

- `valid`: `overall.build+fix` has at least one fixed target behavior, missed
  target behavior, or introduced unrelated regression.
- `empty`: `overall.build+fix` is `0/0/0`; do not cite as a result.
- `partial`: valid, but fewer scored migration steps than the best known valid coverage for that chain.
- `complete`: valid and full known coverage for that chain.
- `Steps` counts unique migration pairs `(prev_version, next_version)`, not phase rows in `chain[]`.
- The `fixed/missed/regressed` count column maps to the raw SWE-Chain
  `TP/FN/FP` fields but uses report terminology.

## All Discovered Cells

| Chain | Group | Steps | Status | Build+fix fixed/missed/regressed | F1 | eval.json |
|---|---|---:|---|---:|---:|---|
| `xarray_2025.6.0_to_2026.2.0` | `raw` | 0 | empty | 0/0/0 | - | `artifacts://swe-chain-019/groups/raw-codex/results/xarray_2025.6.0_to_2026.2.0/codex-openai-gpt-5.5/eval.json` |
| `xarray_2025.6.0_to_2026.2.0` | `init` | 0 | empty | 0/0/0 | - | `artifacts://swe-chain-019/groups/codex-init-agents/results/xarray_2025.6.0_to_2026.2.0/codex-openai-gpt-5.5/eval.json` |
| `xarray_2025.6.0_to_2026.2.0` | `native` | 0 | empty | 0/0/0 | - | `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/xarray_2025.6.0_to_2026.2.0/codex-openai-gpt-5.5/eval.json` |
| `xarray_2025.6.0_to_2026.2.0` | `stop` | 11 | complete | 299/593/1173 | 0.2529 | `artifacts://swe-chain-020/groups/aiwiki-lifecycle-hooks/results/xarray_2025.6.0_to_2026.2.0/codex-openai-gpt-5.5/eval.json` |
| `xarray_2025.6.0_to_2026.2.0` | `exact` | 0 | empty | 0/0/0 | - | `artifacts://swe-chain-021/groups/aiwiki-exact-match-stop/results/xarray_2025.6.0_to_2026.2.0/codex-openai-gpt-5.5/eval.json` |
| `xarray_2022.11.0_to_2023.7.0` | `raw` | 10 | complete | 1351/49/7 | 0.9797 | `artifacts://swe-chain-019/groups/raw-codex/results/xarray_2022.11.0_to_2023.7.0/codex-openai-gpt-5.5/eval.json` |
| `xarray_2022.11.0_to_2023.7.0` | `init` | 10 | complete | 1156/244/2338 | 0.4725 | `artifacts://swe-chain-019/groups/codex-init-agents/results/xarray_2022.11.0_to_2023.7.0/codex-openai-gpt-5.5/eval.json` |
| `xarray_2022.11.0_to_2023.7.0` | `native` | 10 | complete | 736/664/10205 | 0.1193 | `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/xarray_2022.11.0_to_2023.7.0/codex-openai-gpt-5.5/eval.json` |
| `xarray_2022.11.0_to_2023.7.0` | `stop` | 10 | complete | 1280/120/5061 | 0.3308 | `artifacts://swe-chain-020/groups/aiwiki-lifecycle-hooks/results/xarray_2022.11.0_to_2023.7.0/codex-openai-gpt-5.5/eval.json` |
| `xarray_2022.11.0_to_2023.7.0` | `exact` | 10 | complete | 1269/131/1267 | 0.6448 | `artifacts://swe-chain-021/groups/aiwiki-exact-match-stop/results/xarray_2022.11.0_to_2023.7.0/codex-openai-gpt-5.5/eval.json` |
| `conan_2.12.0_to_2.20.1` | `raw` | 16 | complete | 248/354/229 | 0.4597 | `artifacts://swe-chain-019/groups/raw-codex/results/conan_2.12.0_to_2.20.1/codex-openai-gpt-5.5/eval.json` |
| `conan_2.12.0_to_2.20.1` | `init` | 16 | complete | 257/345/233 | 0.4707 | `artifacts://swe-chain-019/groups/codex-init-agents/results/conan_2.12.0_to_2.20.1/codex-openai-gpt-5.5/eval.json` |
| `conan_2.12.0_to_2.20.1` | `native` | 16 | complete | 258/344/2580 | 0.1500 | `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/conan_2.12.0_to_2.20.1/codex-openai-gpt-5.5/eval.json` |
| `conan_2.12.0_to_2.20.1` | `stop` | 16 | complete | 117/485/272 | 0.2362 | `artifacts://swe-chain-020/groups/aiwiki-lifecycle-hooks/results/conan_2.12.0_to_2.20.1/codex-openai-gpt-5.5/eval.json` |
| `conan_2.12.0_to_2.20.1` | `exact` | 16 | complete | 258/344/219 | 0.4782 | `artifacts://swe-chain-021/groups/aiwiki-exact-match-stop/results/conan_2.12.0_to_2.20.1/codex-openai-gpt-5.5/eval.json` |
| `conan_2.23.0_to_2.28.1` | `raw` | 11 | complete | 101/151/215 | 0.3556 | `artifacts://swe-chain-019/groups/raw-codex/results/conan_2.23.0_to_2.28.1/codex-openai-gpt-5.5/eval.json` |
| `conan_2.23.0_to_2.28.1` | `init` | 11 | complete | 89/163/211 | 0.3225 | `artifacts://swe-chain-019/groups/codex-init-agents/results/conan_2.23.0_to_2.28.1/codex-openai-gpt-5.5/eval.json` |
| `conan_2.23.0_to_2.28.1` | `native` | 11 | complete | 77/175/842 | 0.1315 | `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/conan_2.23.0_to_2.28.1/codex-openai-gpt-5.5/eval.json` |
| `conan_2.23.0_to_2.28.1` | `stop` | 11 | complete | 81/171/226 | 0.2898 | `artifacts://swe-chain-020/groups/aiwiki-lifecycle-hooks/results/conan_2.23.0_to_2.28.1/codex-openai-gpt-5.5/eval.json` |
| `conan_2.23.0_to_2.28.1` | `exact` | 11 | complete | 103/149/231 | 0.3515 | `artifacts://swe-chain-021/groups/aiwiki-exact-match-stop/results/conan_2.23.0_to_2.28.1/codex-openai-gpt-5.5/eval.json` |
| `pytest_8.0.0_to_8.3.5` | `raw` | 12 | complete | 179/64/118 | 0.6630 | `artifacts://swe-chain-019/groups/raw-codex/results/pytest_8.0.0_to_8.3.5/codex-openai-gpt-5.5/eval.json` |
| `pytest_8.0.0_to_8.3.5` | `init` | 12 | complete | 201/42/121 | 0.7115 | `artifacts://swe-chain-019/groups/codex-init-agents/results/pytest_8.0.0_to_8.3.5/codex-openai-gpt-5.5/eval.json` |
| `pytest_8.0.0_to_8.3.5` | `native` | 12 | complete | 174/69/80 | 0.7002 | `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/pytest_8.0.0_to_8.3.5/codex-openai-gpt-5.5/eval.json` |
| `pytest_8.0.0_to_8.3.5` | `stop` | 12 | complete | 176/67/212 | 0.5578 | `artifacts://swe-chain-020/groups/aiwiki-lifecycle-hooks/results/pytest_8.0.0_to_8.3.5/codex-openai-gpt-5.5/eval.json` |
| `pytest_8.0.0_to_8.3.5` | `exact` | 12 | complete | 194/49/115 | 0.7029 | `artifacts://swe-chain-021/groups/aiwiki-exact-match-stop/results/pytest_8.0.0_to_8.3.5/codex-openai-gpt-5.5/eval.json` |
| `poetry_1.5.0_to_1.8.5` | `raw` | 10 | complete | 174/115/36 | 0.6974 | `artifacts://swe-chain-019/groups/raw-codex/results/poetry_1.5.0_to_1.8.5/codex-openai-gpt-5.5/eval.json` |
| `poetry_1.5.0_to_1.8.5` | `init` | 10 | complete | 188/101/39 | 0.7287 | `artifacts://swe-chain-019/groups/codex-init-agents/results/poetry_1.5.0_to_1.8.5/codex-openai-gpt-5.5/eval.json` |
| `poetry_1.5.0_to_1.8.5` | `native` | 10 | complete | 183/106/37 | 0.7190 | `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/poetry_1.5.0_to_1.8.5/codex-openai-gpt-5.5/eval.json` |
| `poetry_1.5.0_to_1.8.5` | `stop` | 10 | complete | 113/176/35 | 0.5172 | `artifacts://swe-chain-020/groups/aiwiki-lifecycle-hooks/results/poetry_1.5.0_to_1.8.5/codex-openai-gpt-5.5/eval.json` |
| `poetry_1.5.0_to_1.8.5` | `exact` | 10 | complete | 180/109/32 | 0.7186 | `artifacts://swe-chain-021/groups/aiwiki-exact-match-stop/results/poetry_1.5.0_to_1.8.5/codex-openai-gpt-5.5/eval.json` |
| `urllib3_2.0.7_to_2.6.3` | `raw` | 12 | complete | 87/69/1323 | 0.1111 | `artifacts://swe-chain-019/groups/raw-codex/results/urllib3_2.0.7_to_2.6.3/codex-openai-gpt-5.5/eval.json` |
| `urllib3_2.0.7_to_2.6.3` | `init` | 12 | complete | 114/42/150 | 0.5429 | `artifacts://swe-chain-019/groups/codex-init-agents/results/urllib3_2.0.7_to_2.6.3/codex-openai-gpt-5.5/eval.json` |
| `urllib3_2.0.7_to_2.6.3` | `native` | 12 | complete | 114/42/80 | 0.6514 | `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/urllib3_2.0.7_to_2.6.3/codex-openai-gpt-5.5/eval.json` |
| `urllib3_2.0.7_to_2.6.3` | `stop` | 12 | complete | 115/41/62 | 0.6907 | `artifacts://swe-chain-020/groups/aiwiki-lifecycle-hooks/results/urllib3_2.0.7_to_2.6.3/codex-openai-gpt-5.5/eval.json` |
| `urllib3_2.0.7_to_2.6.3` | `exact` | 12 | complete | 103/53/71 | 0.6243 | `artifacts://swe-chain-021/groups/aiwiki-exact-match-stop/results/urllib3_2.0.7_to_2.6.3/codex-openai-gpt-5.5/eval.json` |
| `urllib3_2.0.7_to_2.6.3` | `raw-cc` | 12 | complete | 153/3/37 | 0.8844 | `artifacts://swe-chain-019-claudecode/groups/raw-claude/results/urllib3_2.0.7_to_2.6.3/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `urllib3_2.0.7_to_2.6.3` | `init-cc` | 12 | complete | 133/23/32 | 0.8287 | `artifacts://swe-chain-019-claudecode/groups/claude-init-agents/results/urllib3_2.0.7_to_2.6.3/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `urllib3_2.0.7_to_2.6.3` | `native-cc` | 12 | complete | 129/27/97 | 0.6754 | `artifacts://swe-chain-019-claudecode/groups/aiwiki-native-writeback/results/urllib3_2.0.7_to_2.6.3/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `pytest_7.0.0_to_7.4.4` | `raw` | 16 | complete | 131/95/473 | 0.3157 | `artifacts://swe-chain-019/groups/raw-codex/results/pytest_7.0.0_to_7.4.4/codex-openai-gpt-5.5/eval.json` |
| `pytest_7.0.0_to_7.4.4` | `init` | 16 | complete | 178/48/108 | 0.6953 | `artifacts://swe-chain-019/groups/codex-init-agents/results/pytest_7.0.0_to_7.4.4/codex-openai-gpt-5.5/eval.json` |
| `pytest_7.0.0_to_7.4.4` | `native` | 16 | complete | 124/102/1969 | 0.1069 | `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/pytest_7.0.0_to_7.4.4/codex-openai-gpt-5.5/eval.json` |
| `pytest_7.0.0_to_7.4.4` | `stop` | 16 | complete | 173/53/68 | 0.7409 | `artifacts://swe-chain-020/groups/aiwiki-lifecycle-hooks/results/pytest_7.0.0_to_7.4.4/codex-openai-gpt-5.5/eval.json` |
| `pytest_7.0.0_to_7.4.4` | `exact` | 16 | complete | 173/53/136 | 0.6468 | `artifacts://swe-chain-021/groups/aiwiki-exact-match-stop/results/pytest_7.0.0_to_7.4.4/codex-openai-gpt-5.5/eval.json` |
| `pytest_7.0.0_to_7.4.4` | `raw-cc` | 16 | complete | 178/48/39 | 0.8036 | `artifacts://swe-chain-019-claudecode/groups/raw-claude/results/pytest_7.0.0_to_7.4.4/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `pytest_7.0.0_to_7.4.4` | `init-cc` | 16 | complete | 182/44/64 | 0.7712 | `artifacts://swe-chain-019-claudecode/groups/claude-init-agents/results/pytest_7.0.0_to_7.4.4/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `pytest_7.0.0_to_7.4.4` | `native-cc` | 16 | complete | 172/54/56 | 0.7577 | `artifacts://swe-chain-019-claudecode/groups/aiwiki-native-writeback/results/pytest_7.0.0_to_7.4.4/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `attrs_21.3.0_to_26.1.0` | `raw` | 13 | complete | 369/141/3 | 0.8367 | `artifacts://swe-chain-019/groups/raw-codex/results/attrs_21.3.0_to_26.1.0/codex-openai-gpt-5.5/eval.json` |
| `attrs_21.3.0_to_26.1.0` | `init` | 13 | complete | 355/155/74 | 0.7561 | `artifacts://swe-chain-019/groups/codex-init-agents/results/attrs_21.3.0_to_26.1.0/codex-openai-gpt-5.5/eval.json` |
| `attrs_21.3.0_to_26.1.0` | `native` | 13 | complete | 370/140/25 | 0.8177 | `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/attrs_21.3.0_to_26.1.0/codex-openai-gpt-5.5/eval.json` |
| `attrs_21.3.0_to_26.1.0` | `stop` | 13 | complete | 365/145/23 | 0.8129 | `artifacts://swe-chain-020/groups/aiwiki-lifecycle-hooks/results/attrs_21.3.0_to_26.1.0/codex-openai-gpt-5.5/eval.json` |
| `attrs_21.3.0_to_26.1.0` | `exact` | 13 | complete | 364/146/3 | 0.8301 | `artifacts://swe-chain-021/groups/aiwiki-exact-match-stop/results/attrs_21.3.0_to_26.1.0/codex-openai-gpt-5.5/eval.json` |
| `attrs_21.3.0_to_26.1.0` | `raw-cc` | 13 | complete | 437/73/0 | 0.9229 | `artifacts://swe-chain-019-claudecode/groups/raw-claude/results/attrs_21.3.0_to_26.1.0/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `attrs_21.3.0_to_26.1.0` | `init-cc` | 13 | complete | 373/137/2 | 0.8430 | `artifacts://swe-chain-019-claudecode/groups/claude-init-agents/results/attrs_21.3.0_to_26.1.0/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `attrs_21.3.0_to_26.1.0` | `native-cc` | 13 | complete | 439/71/0 | 0.9252 | `artifacts://swe-chain-019-claudecode/groups/aiwiki-native-writeback/results/attrs_21.3.0_to_26.1.0/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `flask_2.0.0_to_2.3.3` | `raw` | 17 | complete | 108/0/1 | 0.9954 | `artifacts://swe-chain-019/groups/raw-codex/results/flask_2.0.0_to_2.3.3/codex-openai-gpt-5.5/eval.json` |
| `flask_2.0.0_to_2.3.3` | `init` | 17 | complete | 102/6/0 | 0.9714 | `artifacts://swe-chain-019/groups/codex-init-agents/results/flask_2.0.0_to_2.3.3/codex-openai-gpt-5.5/eval.json` |
| `flask_2.0.0_to_2.3.3` | `native` | 17 | complete | 103/5/1 | 0.9717 | `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/flask_2.0.0_to_2.3.3/codex-openai-gpt-5.5/eval.json` |
| `flask_2.0.0_to_2.3.3` | `stop` | 17 | complete | 107/1/2 | 0.9862 | `artifacts://swe-chain-020/groups/aiwiki-lifecycle-hooks/results/flask_2.0.0_to_2.3.3/codex-openai-gpt-5.5/eval.json` |
| `flask_2.0.0_to_2.3.3` | `exact` | 17 | complete | 79/29/439 | 0.2524 | `artifacts://swe-chain-021/groups/aiwiki-exact-match-stop/results/flask_2.0.0_to_2.3.3/codex-openai-gpt-5.5/eval.json` |
| `flask_2.0.0_to_2.3.3` | `raw-cc` | 17 | complete | 108/0/0 | 1.0000 | `artifacts://swe-chain-019-claudecode/groups/raw-claude/results/flask_2.0.0_to_2.3.3/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `flask_2.0.0_to_2.3.3` | `init-cc` | 17 | complete | 108/0/0 | 1.0000 | `artifacts://swe-chain-019-claudecode/groups/claude-init-agents/results/flask_2.0.0_to_2.3.3/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `flask_2.0.0_to_2.3.3` | `native-cc` | 17 | complete | 107/1/1 | 0.9907 | `artifacts://swe-chain-019-claudecode/groups/aiwiki-native-writeback/results/flask_2.0.0_to_2.3.3/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `jinja2_2.8_to_2.10.3` | `raw` | 12 | complete | 119/12/6 | 0.9297 | `artifacts://swe-chain-019/groups/raw-codex/results/jinja2_2.8_to_2.10.3/codex-openai-gpt-5.5/eval.json` |
| `jinja2_2.8_to_2.10.3` | `init` | 12 | complete | 118/13/39 | 0.8195 | `artifacts://swe-chain-019/groups/codex-init-agents/results/jinja2_2.8_to_2.10.3/codex-openai-gpt-5.5/eval.json` |
| `jinja2_2.8_to_2.10.3` | `native` | 12 | complete | 102/29/49 | 0.7234 | `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/jinja2_2.8_to_2.10.3/codex-openai-gpt-5.5/eval.json` |
| `jinja2_2.8_to_2.10.3` | `stop` | 12 | complete | 121/10/5 | 0.9416 | `artifacts://swe-chain-020/groups/aiwiki-lifecycle-hooks/results/jinja2_2.8_to_2.10.3/codex-openai-gpt-5.5/eval.json` |
| `jinja2_2.8_to_2.10.3` | `exact` | 12 | complete | 114/17/10 | 0.8941 | `artifacts://swe-chain-021/groups/aiwiki-exact-match-stop/results/jinja2_2.8_to_2.10.3/codex-openai-gpt-5.5/eval.json` |
| `jinja2_2.8_to_2.10.3` | `raw-cc` | 12 | complete | 92/39/13 | 0.7797 | `artifacts://swe-chain-019-claudecode/groups/raw-claude/results/jinja2_2.8_to_2.10.3/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `jinja2_2.8_to_2.10.3` | `init-cc` | 12 | complete | 102/29/3 | 0.8644 | `artifacts://swe-chain-019-claudecode/groups/claude-init-agents/results/jinja2_2.8_to_2.10.3/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `jinja2_2.8_to_2.10.3` | `native-cc` | 12 | complete | 101/30/1 | 0.8670 | `artifacts://swe-chain-019-claudecode/groups/aiwiki-native-writeback/results/jinja2_2.8_to_2.10.3/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `pyjwt_2.0.0_to_2.12.1` | `raw` | 15 | complete | 119/5/0 | 0.9794 | `artifacts://swe-chain-019/groups/raw-codex/results/pyjwt_2.0.0_to_2.12.1/codex-openai-gpt-5.5/eval.json` |
| `pyjwt_2.0.0_to_2.12.1` | `init` | 15 | complete | 120/4/0 | 0.9836 | `artifacts://swe-chain-019/groups/codex-init-agents/results/pyjwt_2.0.0_to_2.12.1/codex-openai-gpt-5.5/eval.json` |
| `pyjwt_2.0.0_to_2.12.1` | `native` | 15 | complete | 112/12/0 | 0.9491 | `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/pyjwt_2.0.0_to_2.12.1/codex-openai-gpt-5.5/eval.json` |
| `pyjwt_2.0.0_to_2.12.1` | `stop` | 15 | complete | 108/16/0 | 0.9311 | `artifacts://swe-chain-020/groups/aiwiki-lifecycle-hooks/results/pyjwt_2.0.0_to_2.12.1/codex-openai-gpt-5.5/eval.json` |
| `pyjwt_2.0.0_to_2.12.1` | `exact` | 15 | complete | 115/9/0 | 0.9623 | `artifacts://swe-chain-021/groups/aiwiki-exact-match-stop/results/pyjwt_2.0.0_to_2.12.1/codex-openai-gpt-5.5/eval.json` |
| `flask_2.0.0_to_2.0.1` | `raw` | 1 | complete | 8/0/0 | 1.0000 | `artifacts://swe-chain-019/groups/raw-codex/results/flask_2.0.0_to_2.0.1/codex-openai-gpt-5.5/eval.json` |
| `flask_2.0.0_to_2.0.1` | `init` | 1 | complete | 8/0/0 | 1.0000 | `artifacts://swe-chain-019/groups/codex-init-agents/results/flask_2.0.0_to_2.0.1/codex-openai-gpt-5.5/eval.json` |
| `flask_2.0.0_to_2.0.1` | `native` | 1 | complete | 8/0/0 | 1.0000 | `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/flask_2.0.0_to_2.0.1/codex-openai-gpt-5.5/eval.json` |

## Known Partial Cells

None after the 2026-06-28 resume refresh.

## Empty Shells

| Chain | Group | eval.json |
|---|---|---|
| `xarray_2025.6.0_to_2026.2.0` | `raw` | `artifacts://swe-chain-019/groups/raw-codex/results/xarray_2025.6.0_to_2026.2.0/codex-openai-gpt-5.5/eval.json` |
| `xarray_2025.6.0_to_2026.2.0` | `init` | `artifacts://swe-chain-019/groups/codex-init-agents/results/xarray_2025.6.0_to_2026.2.0/codex-openai-gpt-5.5/eval.json` |
| `xarray_2025.6.0_to_2026.2.0` | `native` | `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/xarray_2025.6.0_to_2026.2.0/codex-openai-gpt-5.5/eval.json` |
| `xarray_2025.6.0_to_2026.2.0` | `exact` | `artifacts://swe-chain-021/groups/aiwiki-exact-match-stop/results/xarray_2025.6.0_to_2026.2.0/codex-openai-gpt-5.5/eval.json` |
