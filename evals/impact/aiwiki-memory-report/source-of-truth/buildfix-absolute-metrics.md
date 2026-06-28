# Build+Fix Absolute Metrics

This is the report-level absolute metric table for valid SWE-Chain eval cells audited on 2026-06-27 and refreshed after completed resume and exact-fill runs on 2026-06-28.
Use this when the report needs fixed-target, missed-target, introduced-unrelated-regression, precision, recall, F1, or partial-run status rather than delta-only comparisons.

## Contract

- Raw measurement source: `groups/<group>/results/<chain>/<model-dir>/eval.json`, field `overall.build+fix`.
- `Steps` counts unique migration pairs `(prev_version, next_version)`, not phase rows in `chain[]`.
- Empty `0/0/0` shells are excluded here and listed in `coverage-status.md`.
- `partial` means the eval has fewer scored migration steps than the best known valid coverage for that chain.
- The `stop` group here uses the current 020 `results/` pointer. For Flask hook variants, cite `020-flask-hook-ablation.md` instead.
- `xarray_2025.6.0_to_2026.2.0` currently has only a 020 stop/harness-fix eval, so it is absolute-only and has no cross-model delta row.
- Column mapping from raw SWE-Chain `eval.json`: `Fixed Target` is official
  `TP`, `Missed Target` is official `FN`, and `Introduced Unrelated Regression`
  is official `FP`. The report uses these IT terms because AI Wiki memory is
  not ML model training.

## Valid Eval Cells

| Chain | Difficulty | Group | Steps | Status | Fixed Target | Missed Target | Introduced Unrelated Regression | Precision | Recall | F1 |
|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|
| `xarray_2025.6.0_to_2026.2.0` | 0.989 | `stop` | 11 | complete | 299 | 593 | 1173 | 20.31% | 33.52% | 0.2529 |
| `xarray_2022.11.0_to_2023.7.0` | 0.866 | `raw` | 10 | complete | 1351 | 49 | 7 | 99.48% | 96.50% | 0.9797 |
| `xarray_2022.11.0_to_2023.7.0` | 0.866 | `init` | 10 | complete | 1156 | 244 | 2338 | 33.09% | 82.57% | 0.4725 |
| `xarray_2022.11.0_to_2023.7.0` | 0.866 | `native` | 10 | complete | 736 | 664 | 10205 | 6.73% | 52.57% | 0.1193 |
| `xarray_2022.11.0_to_2023.7.0` | 0.866 | `stop` | 10 | complete | 1280 | 120 | 5061 | 20.19% | 91.43% | 0.3308 |
| `xarray_2022.11.0_to_2023.7.0` | 0.866 | `exact` | 10 | complete | 1269 | 131 | 1267 | 50.04% | 90.64% | 0.6448 |
| `conan_2.12.0_to_2.20.1` | 0.544 | `raw` | 16 | complete | 248 | 354 | 229 | 51.99% | 41.20% | 0.4597 |
| `conan_2.12.0_to_2.20.1` | 0.544 | `init` | 16 | complete | 257 | 345 | 233 | 52.45% | 42.69% | 0.4707 |
| `conan_2.12.0_to_2.20.1` | 0.544 | `native` | 16 | complete | 258 | 344 | 2580 | 9.09% | 42.86% | 0.1500 |
| `conan_2.12.0_to_2.20.1` | 0.544 | `stop` | 16 | complete | 117 | 485 | 272 | 30.08% | 19.44% | 0.2362 |
| `conan_2.12.0_to_2.20.1` | 0.544 | `exact` | 16 | complete | 258 | 344 | 219 | 54.09% | 42.86% | 0.4782 |
| `conan_2.23.0_to_2.28.1` | 0.484 | `raw` | 11 | complete | 101 | 151 | 215 | 31.96% | 40.08% | 0.3556 |
| `conan_2.23.0_to_2.28.1` | 0.484 | `init` | 11 | complete | 89 | 163 | 211 | 29.67% | 35.32% | 0.3225 |
| `conan_2.23.0_to_2.28.1` | 0.484 | `native` | 11 | complete | 77 | 175 | 842 | 8.38% | 30.56% | 0.1315 |
| `conan_2.23.0_to_2.28.1` | 0.484 | `stop` | 11 | complete | 81 | 171 | 226 | 26.38% | 32.14% | 0.2898 |
| `conan_2.23.0_to_2.28.1` | 0.484 | `exact` | 11 | complete | 103 | 149 | 231 | 30.84% | 40.87% | 0.3515 |
| `pytest_8.0.0_to_8.3.5` | 0.456 | `raw` | 12 | complete | 179 | 64 | 118 | 60.27% | 73.66% | 0.6630 |
| `pytest_8.0.0_to_8.3.5` | 0.456 | `init` | 12 | complete | 201 | 42 | 121 | 62.42% | 82.72% | 0.7115 |
| `pytest_8.0.0_to_8.3.5` | 0.456 | `native` | 12 | complete | 174 | 69 | 80 | 68.50% | 71.60% | 0.7002 |
| `pytest_8.0.0_to_8.3.5` | 0.456 | `stop` | 12 | complete | 176 | 67 | 212 | 45.36% | 72.43% | 0.5578 |
| `pytest_8.0.0_to_8.3.5` | 0.456 | `exact` | 12 | complete | 194 | 49 | 115 | 62.78% | 79.84% | 0.7029 |
| `poetry_1.5.0_to_1.8.5` | 0.404 | `raw` | 10 | complete | 174 | 115 | 36 | 82.86% | 60.21% | 0.6974 |
| `poetry_1.5.0_to_1.8.5` | 0.404 | `init` | 10 | complete | 188 | 101 | 39 | 82.82% | 65.05% | 0.7287 |
| `poetry_1.5.0_to_1.8.5` | 0.404 | `native` | 10 | complete | 183 | 106 | 37 | 83.18% | 63.32% | 0.7190 |
| `poetry_1.5.0_to_1.8.5` | 0.404 | `stop` | 10 | complete | 113 | 176 | 35 | 76.35% | 39.10% | 0.5172 |
| `poetry_1.5.0_to_1.8.5` | 0.404 | `exact` | 10 | complete | 180 | 109 | 32 | 84.91% | 62.28% | 0.7186 |
| `urllib3_2.0.7_to_2.6.3` | 0.263 | `raw` | 12 | complete | 87 | 69 | 1323 | 6.17% | 55.77% | 0.1111 |
| `urllib3_2.0.7_to_2.6.3` | 0.263 | `init` | 12 | complete | 114 | 42 | 150 | 43.18% | 73.08% | 0.5429 |
| `urllib3_2.0.7_to_2.6.3` | 0.263 | `native` | 12 | complete | 114 | 42 | 80 | 58.76% | 73.08% | 0.6514 |
| `urllib3_2.0.7_to_2.6.3` | 0.263 | `stop` | 12 | complete | 115 | 41 | 62 | 64.97% | 73.72% | 0.6907 |
| `urllib3_2.0.7_to_2.6.3` | 0.263 | `exact` | 12 | complete | 103 | 53 | 71 | 59.20% | 66.03% | 0.6243 |
| `urllib3_2.0.7_to_2.6.3` | 0.263 | `raw-cc` | 12 | complete | 153 | 3 | 37 | 80.53% | 98.08% | 0.8844 |
| `urllib3_2.0.7_to_2.6.3` | 0.263 | `init-cc` | 12 | complete | 133 | 23 | 32 | 80.61% | 85.26% | 0.8287 |
| `urllib3_2.0.7_to_2.6.3` | 0.263 | `native-cc` | 12 | complete | 129 | 27 | 97 | 57.08% | 82.69% | 0.6754 |
| `pytest_7.0.0_to_7.4.4` | 0.246 | `raw` | 16 | complete | 131 | 95 | 473 | 21.69% | 57.96% | 0.3157 |
| `pytest_7.0.0_to_7.4.4` | 0.246 | `init` | 16 | complete | 178 | 48 | 108 | 62.24% | 78.76% | 0.6953 |
| `pytest_7.0.0_to_7.4.4` | 0.246 | `native` | 16 | complete | 124 | 102 | 1969 | 5.92% | 54.87% | 0.1069 |
| `pytest_7.0.0_to_7.4.4` | 0.246 | `stop` | 16 | complete | 173 | 53 | 68 | 71.78% | 76.55% | 0.7409 |
| `pytest_7.0.0_to_7.4.4` | 0.246 | `exact` | 16 | complete | 173 | 53 | 136 | 55.99% | 76.55% | 0.6468 |
| `pytest_7.0.0_to_7.4.4` | 0.246 | `raw-cc` | 16 | complete | 178 | 48 | 39 | 82.03% | 78.76% | 0.8036 |
| `pytest_7.0.0_to_7.4.4` | 0.246 | `init-cc` | 16 | complete | 182 | 44 | 64 | 73.98% | 80.53% | 0.7712 |
| `pytest_7.0.0_to_7.4.4` | 0.246 | `native-cc` | 16 | complete | 172 | 54 | 56 | 75.44% | 76.11% | 0.7577 |
| `attrs_21.3.0_to_26.1.0` | 0.195 | `raw` | 13 | complete | 369 | 141 | 3 | 99.19% | 72.35% | 0.8367 |
| `attrs_21.3.0_to_26.1.0` | 0.195 | `init` | 13 | complete | 355 | 155 | 74 | 82.75% | 69.61% | 0.7561 |
| `attrs_21.3.0_to_26.1.0` | 0.195 | `native` | 13 | complete | 370 | 140 | 25 | 93.67% | 72.55% | 0.8177 |
| `attrs_21.3.0_to_26.1.0` | 0.195 | `stop` | 13 | complete | 365 | 145 | 23 | 94.07% | 71.57% | 0.8129 |
| `attrs_21.3.0_to_26.1.0` | 0.195 | `exact` | 13 | complete | 364 | 146 | 3 | 99.18% | 71.37% | 0.8301 |
| `attrs_21.3.0_to_26.1.0` | 0.195 | `raw-cc` | 13 | complete | 437 | 73 | 0 | 100.00% | 85.69% | 0.9229 |
| `attrs_21.3.0_to_26.1.0` | 0.195 | `init-cc` | 13 | complete | 373 | 137 | 2 | 99.47% | 73.14% | 0.8430 |
| `attrs_21.3.0_to_26.1.0` | 0.195 | `native-cc` | 13 | complete | 439 | 71 | 0 | 100.00% | 86.08% | 0.9252 |
| `flask_2.0.0_to_2.3.3` | 0.150 | `raw` | 17 | complete | 108 | 0 | 1 | 99.08% | 100.00% | 0.9954 |
| `flask_2.0.0_to_2.3.3` | 0.150 | `init` | 17 | complete | 102 | 6 | 0 | 100.00% | 94.44% | 0.9714 |
| `flask_2.0.0_to_2.3.3` | 0.150 | `native` | 17 | complete | 103 | 5 | 1 | 99.04% | 95.37% | 0.9717 |
| `flask_2.0.0_to_2.3.3` | 0.150 | `stop` | 17 | complete | 107 | 1 | 2 | 98.17% | 99.07% | 0.9862 |
| `flask_2.0.0_to_2.3.3` | 0.150 | `exact` | 17 | complete | 79 | 29 | 439 | 15.25% | 73.15% | 0.2524 |
| `flask_2.0.0_to_2.3.3` | 0.150 | `raw-cc` | 17 | complete | 108 | 0 | 0 | 100.00% | 100.00% | 1.0000 |
| `flask_2.0.0_to_2.3.3` | 0.150 | `init-cc` | 17 | complete | 108 | 0 | 0 | 100.00% | 100.00% | 1.0000 |
| `flask_2.0.0_to_2.3.3` | 0.150 | `native-cc` | 17 | complete | 107 | 1 | 1 | 99.07% | 99.07% | 0.9907 |
| `jinja2_2.8_to_2.10.3` | 0.135 | `raw` | 12 | complete | 119 | 12 | 6 | 95.20% | 90.84% | 0.9297 |
| `jinja2_2.8_to_2.10.3` | 0.135 | `init` | 12 | complete | 118 | 13 | 39 | 75.16% | 90.08% | 0.8195 |
| `jinja2_2.8_to_2.10.3` | 0.135 | `native` | 12 | complete | 102 | 29 | 49 | 67.55% | 77.86% | 0.7234 |
| `jinja2_2.8_to_2.10.3` | 0.135 | `stop` | 12 | complete | 121 | 10 | 5 | 96.03% | 92.37% | 0.9416 |
| `jinja2_2.8_to_2.10.3` | 0.135 | `exact` | 12 | complete | 114 | 17 | 10 | 91.94% | 87.02% | 0.8941 |
| `jinja2_2.8_to_2.10.3` | 0.135 | `raw-cc` | 12 | complete | 92 | 39 | 13 | 87.62% | 70.23% | 0.7797 |
| `jinja2_2.8_to_2.10.3` | 0.135 | `init-cc` | 12 | complete | 102 | 29 | 3 | 97.14% | 77.86% | 0.8644 |
| `jinja2_2.8_to_2.10.3` | 0.135 | `native-cc` | 12 | complete | 101 | 30 | 1 | 99.02% | 77.10% | 0.8670 |
| `pyjwt_2.0.0_to_2.12.1` | 0.000 | `raw` | 15 | complete | 119 | 5 | 0 | 100.00% | 95.97% | 0.9794 |
| `pyjwt_2.0.0_to_2.12.1` | 0.000 | `init` | 15 | complete | 120 | 4 | 0 | 100.00% | 96.77% | 0.9836 |
| `pyjwt_2.0.0_to_2.12.1` | 0.000 | `native` | 15 | complete | 112 | 12 | 0 | 100.00% | 90.32% | 0.9491 |
| `pyjwt_2.0.0_to_2.12.1` | 0.000 | `stop` | 15 | complete | 108 | 16 | 0 | 100.00% | 87.10% | 0.9311 |
| `pyjwt_2.0.0_to_2.12.1` | 0.000 | `exact` | 15 | complete | 115 | 9 | 0 | 100.00% | 92.74% | 0.9623 |
| `flask_2.0.0_to_2.0.1` | - | `raw` | 1 | complete | 8 | 0 | 0 | 100.00% | 100.00% | 1.0000 |
| `flask_2.0.0_to_2.0.1` | - | `init` | 1 | complete | 8 | 0 | 0 | 100.00% | 100.00% | 1.0000 |
| `flask_2.0.0_to_2.0.1` | - | `native` | 1 | complete | 8 | 0 | 0 | 100.00% | 100.00% | 1.0000 |

## Raw Eval Paths

| Chain | Group | eval.json |
|---|---|---|
| `xarray_2025.6.0_to_2026.2.0` | `stop` | `artifacts://swe-chain-020/groups/aiwiki-lifecycle-hooks/results/xarray_2025.6.0_to_2026.2.0/codex-openai-gpt-5.5/eval.json` |
| `xarray_2022.11.0_to_2023.7.0` | `raw` | `artifacts://swe-chain-019/groups/raw-codex/results/xarray_2022.11.0_to_2023.7.0/codex-openai-gpt-5.5/eval.json` |
| `xarray_2022.11.0_to_2023.7.0` | `init` | `artifacts://swe-chain-019/groups/codex-init-agents/results/xarray_2022.11.0_to_2023.7.0/codex-openai-gpt-5.5/eval.json` |
| `xarray_2022.11.0_to_2023.7.0` | `native` | `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/xarray_2022.11.0_to_2023.7.0/codex-openai-gpt-5.5/eval.json` |
| `xarray_2022.11.0_to_2023.7.0` | `stop` | `artifacts://swe-chain-020/groups/aiwiki-lifecycle-hooks/results/xarray_2022.11.0_to_2023.7.0/codex-openai-gpt-5.5/eval.json` |
| `xarray_2022.11.0_to_2023.7.0` | `exact` | `artifacts://swe-chain-021/groups/aiwiki-exact-match-stop/results/xarray_2022.11.0_to_2023.7.0/codex-openai-gpt-5.5/eval.json` |
| `conan_2.12.0_to_2.20.1` | `raw` | `artifacts://swe-chain-019/groups/raw-codex/results/conan_2.12.0_to_2.20.1/codex-openai-gpt-5.5/eval.json` |
| `conan_2.12.0_to_2.20.1` | `init` | `artifacts://swe-chain-019/groups/codex-init-agents/results/conan_2.12.0_to_2.20.1/codex-openai-gpt-5.5/eval.json` |
| `conan_2.12.0_to_2.20.1` | `native` | `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/conan_2.12.0_to_2.20.1/codex-openai-gpt-5.5/eval.json` |
| `conan_2.12.0_to_2.20.1` | `stop` | `artifacts://swe-chain-020/groups/aiwiki-lifecycle-hooks/results/conan_2.12.0_to_2.20.1/codex-openai-gpt-5.5/eval.json` |
| `conan_2.12.0_to_2.20.1` | `exact` | `artifacts://swe-chain-021/groups/aiwiki-exact-match-stop/results/conan_2.12.0_to_2.20.1/codex-openai-gpt-5.5/eval.json` |
| `conan_2.23.0_to_2.28.1` | `raw` | `artifacts://swe-chain-019/groups/raw-codex/results/conan_2.23.0_to_2.28.1/codex-openai-gpt-5.5/eval.json` |
| `conan_2.23.0_to_2.28.1` | `init` | `artifacts://swe-chain-019/groups/codex-init-agents/results/conan_2.23.0_to_2.28.1/codex-openai-gpt-5.5/eval.json` |
| `conan_2.23.0_to_2.28.1` | `native` | `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/conan_2.23.0_to_2.28.1/codex-openai-gpt-5.5/eval.json` |
| `conan_2.23.0_to_2.28.1` | `stop` | `artifacts://swe-chain-020/groups/aiwiki-lifecycle-hooks/results/conan_2.23.0_to_2.28.1/codex-openai-gpt-5.5/eval.json` |
| `conan_2.23.0_to_2.28.1` | `exact` | `artifacts://swe-chain-021/groups/aiwiki-exact-match-stop/results/conan_2.23.0_to_2.28.1/codex-openai-gpt-5.5/eval.json` |
| `pytest_8.0.0_to_8.3.5` | `raw` | `artifacts://swe-chain-019/groups/raw-codex/results/pytest_8.0.0_to_8.3.5/codex-openai-gpt-5.5/eval.json` |
| `pytest_8.0.0_to_8.3.5` | `init` | `artifacts://swe-chain-019/groups/codex-init-agents/results/pytest_8.0.0_to_8.3.5/codex-openai-gpt-5.5/eval.json` |
| `pytest_8.0.0_to_8.3.5` | `native` | `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/pytest_8.0.0_to_8.3.5/codex-openai-gpt-5.5/eval.json` |
| `pytest_8.0.0_to_8.3.5` | `stop` | `artifacts://swe-chain-020/groups/aiwiki-lifecycle-hooks/results/pytest_8.0.0_to_8.3.5/codex-openai-gpt-5.5/eval.json` |
| `pytest_8.0.0_to_8.3.5` | `exact` | `artifacts://swe-chain-021/groups/aiwiki-exact-match-stop/results/pytest_8.0.0_to_8.3.5/codex-openai-gpt-5.5/eval.json` |
| `poetry_1.5.0_to_1.8.5` | `raw` | `artifacts://swe-chain-019/groups/raw-codex/results/poetry_1.5.0_to_1.8.5/codex-openai-gpt-5.5/eval.json` |
| `poetry_1.5.0_to_1.8.5` | `init` | `artifacts://swe-chain-019/groups/codex-init-agents/results/poetry_1.5.0_to_1.8.5/codex-openai-gpt-5.5/eval.json` |
| `poetry_1.5.0_to_1.8.5` | `native` | `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/poetry_1.5.0_to_1.8.5/codex-openai-gpt-5.5/eval.json` |
| `poetry_1.5.0_to_1.8.5` | `stop` | `artifacts://swe-chain-020/groups/aiwiki-lifecycle-hooks/results/poetry_1.5.0_to_1.8.5/codex-openai-gpt-5.5/eval.json` |
| `poetry_1.5.0_to_1.8.5` | `exact` | `artifacts://swe-chain-021/groups/aiwiki-exact-match-stop/results/poetry_1.5.0_to_1.8.5/codex-openai-gpt-5.5/eval.json` |
| `urllib3_2.0.7_to_2.6.3` | `raw` | `artifacts://swe-chain-019/groups/raw-codex/results/urllib3_2.0.7_to_2.6.3/codex-openai-gpt-5.5/eval.json` |
| `urllib3_2.0.7_to_2.6.3` | `init` | `artifacts://swe-chain-019/groups/codex-init-agents/results/urllib3_2.0.7_to_2.6.3/codex-openai-gpt-5.5/eval.json` |
| `urllib3_2.0.7_to_2.6.3` | `native` | `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/urllib3_2.0.7_to_2.6.3/codex-openai-gpt-5.5/eval.json` |
| `urllib3_2.0.7_to_2.6.3` | `stop` | `artifacts://swe-chain-020/groups/aiwiki-lifecycle-hooks/results/urllib3_2.0.7_to_2.6.3/codex-openai-gpt-5.5/eval.json` |
| `urllib3_2.0.7_to_2.6.3` | `exact` | `artifacts://swe-chain-021/groups/aiwiki-exact-match-stop/results/urllib3_2.0.7_to_2.6.3/codex-openai-gpt-5.5/eval.json` |
| `urllib3_2.0.7_to_2.6.3` | `raw-cc` | `artifacts://swe-chain-019-claudecode/groups/raw-claude/results/urllib3_2.0.7_to_2.6.3/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `urllib3_2.0.7_to_2.6.3` | `init-cc` | `artifacts://swe-chain-019-claudecode/groups/claude-init-agents/results/urllib3_2.0.7_to_2.6.3/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `urllib3_2.0.7_to_2.6.3` | `native-cc` | `artifacts://swe-chain-019-claudecode/groups/aiwiki-native-writeback/results/urllib3_2.0.7_to_2.6.3/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `pytest_7.0.0_to_7.4.4` | `raw` | `artifacts://swe-chain-019/groups/raw-codex/results/pytest_7.0.0_to_7.4.4/codex-openai-gpt-5.5/eval.json` |
| `pytest_7.0.0_to_7.4.4` | `init` | `artifacts://swe-chain-019/groups/codex-init-agents/results/pytest_7.0.0_to_7.4.4/codex-openai-gpt-5.5/eval.json` |
| `pytest_7.0.0_to_7.4.4` | `native` | `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/pytest_7.0.0_to_7.4.4/codex-openai-gpt-5.5/eval.json` |
| `pytest_7.0.0_to_7.4.4` | `stop` | `artifacts://swe-chain-020/groups/aiwiki-lifecycle-hooks/results/pytest_7.0.0_to_7.4.4/codex-openai-gpt-5.5/eval.json` |
| `pytest_7.0.0_to_7.4.4` | `exact` | `artifacts://swe-chain-021/groups/aiwiki-exact-match-stop/results/pytest_7.0.0_to_7.4.4/codex-openai-gpt-5.5/eval.json` |
| `pytest_7.0.0_to_7.4.4` | `raw-cc` | `artifacts://swe-chain-019-claudecode/groups/raw-claude/results/pytest_7.0.0_to_7.4.4/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `pytest_7.0.0_to_7.4.4` | `init-cc` | `artifacts://swe-chain-019-claudecode/groups/claude-init-agents/results/pytest_7.0.0_to_7.4.4/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `pytest_7.0.0_to_7.4.4` | `native-cc` | `artifacts://swe-chain-019-claudecode/groups/aiwiki-native-writeback/results/pytest_7.0.0_to_7.4.4/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `attrs_21.3.0_to_26.1.0` | `raw` | `artifacts://swe-chain-019/groups/raw-codex/results/attrs_21.3.0_to_26.1.0/codex-openai-gpt-5.5/eval.json` |
| `attrs_21.3.0_to_26.1.0` | `init` | `artifacts://swe-chain-019/groups/codex-init-agents/results/attrs_21.3.0_to_26.1.0/codex-openai-gpt-5.5/eval.json` |
| `attrs_21.3.0_to_26.1.0` | `native` | `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/attrs_21.3.0_to_26.1.0/codex-openai-gpt-5.5/eval.json` |
| `attrs_21.3.0_to_26.1.0` | `stop` | `artifacts://swe-chain-020/groups/aiwiki-lifecycle-hooks/results/attrs_21.3.0_to_26.1.0/codex-openai-gpt-5.5/eval.json` |
| `attrs_21.3.0_to_26.1.0` | `exact` | `artifacts://swe-chain-021/groups/aiwiki-exact-match-stop/results/attrs_21.3.0_to_26.1.0/codex-openai-gpt-5.5/eval.json` |
| `attrs_21.3.0_to_26.1.0` | `raw-cc` | `artifacts://swe-chain-019-claudecode/groups/raw-claude/results/attrs_21.3.0_to_26.1.0/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `attrs_21.3.0_to_26.1.0` | `init-cc` | `artifacts://swe-chain-019-claudecode/groups/claude-init-agents/results/attrs_21.3.0_to_26.1.0/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `attrs_21.3.0_to_26.1.0` | `native-cc` | `artifacts://swe-chain-019-claudecode/groups/aiwiki-native-writeback/results/attrs_21.3.0_to_26.1.0/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `flask_2.0.0_to_2.3.3` | `raw` | `artifacts://swe-chain-019/groups/raw-codex/results/flask_2.0.0_to_2.3.3/codex-openai-gpt-5.5/eval.json` |
| `flask_2.0.0_to_2.3.3` | `init` | `artifacts://swe-chain-019/groups/codex-init-agents/results/flask_2.0.0_to_2.3.3/codex-openai-gpt-5.5/eval.json` |
| `flask_2.0.0_to_2.3.3` | `native` | `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/flask_2.0.0_to_2.3.3/codex-openai-gpt-5.5/eval.json` |
| `flask_2.0.0_to_2.3.3` | `stop` | `artifacts://swe-chain-020/groups/aiwiki-lifecycle-hooks/results/flask_2.0.0_to_2.3.3/codex-openai-gpt-5.5/eval.json` |
| `flask_2.0.0_to_2.3.3` | `exact` | `artifacts://swe-chain-021/groups/aiwiki-exact-match-stop/results/flask_2.0.0_to_2.3.3/codex-openai-gpt-5.5/eval.json` |
| `flask_2.0.0_to_2.3.3` | `raw-cc` | `artifacts://swe-chain-019-claudecode/groups/raw-claude/results/flask_2.0.0_to_2.3.3/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `flask_2.0.0_to_2.3.3` | `init-cc` | `artifacts://swe-chain-019-claudecode/groups/claude-init-agents/results/flask_2.0.0_to_2.3.3/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `flask_2.0.0_to_2.3.3` | `native-cc` | `artifacts://swe-chain-019-claudecode/groups/aiwiki-native-writeback/results/flask_2.0.0_to_2.3.3/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `jinja2_2.8_to_2.10.3` | `raw` | `artifacts://swe-chain-019/groups/raw-codex/results/jinja2_2.8_to_2.10.3/codex-openai-gpt-5.5/eval.json` |
| `jinja2_2.8_to_2.10.3` | `init` | `artifacts://swe-chain-019/groups/codex-init-agents/results/jinja2_2.8_to_2.10.3/codex-openai-gpt-5.5/eval.json` |
| `jinja2_2.8_to_2.10.3` | `native` | `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/jinja2_2.8_to_2.10.3/codex-openai-gpt-5.5/eval.json` |
| `jinja2_2.8_to_2.10.3` | `stop` | `artifacts://swe-chain-020/groups/aiwiki-lifecycle-hooks/results/jinja2_2.8_to_2.10.3/codex-openai-gpt-5.5/eval.json` |
| `jinja2_2.8_to_2.10.3` | `exact` | `artifacts://swe-chain-021/groups/aiwiki-exact-match-stop/results/jinja2_2.8_to_2.10.3/codex-openai-gpt-5.5/eval.json` |
| `jinja2_2.8_to_2.10.3` | `raw-cc` | `artifacts://swe-chain-019-claudecode/groups/raw-claude/results/jinja2_2.8_to_2.10.3/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `jinja2_2.8_to_2.10.3` | `init-cc` | `artifacts://swe-chain-019-claudecode/groups/claude-init-agents/results/jinja2_2.8_to_2.10.3/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `jinja2_2.8_to_2.10.3` | `native-cc` | `artifacts://swe-chain-019-claudecode/groups/aiwiki-native-writeback/results/jinja2_2.8_to_2.10.3/claudecode-anthropic-claude-opus-4-8/eval.json` |
| `pyjwt_2.0.0_to_2.12.1` | `raw` | `artifacts://swe-chain-019/groups/raw-codex/results/pyjwt_2.0.0_to_2.12.1/codex-openai-gpt-5.5/eval.json` |
| `pyjwt_2.0.0_to_2.12.1` | `init` | `artifacts://swe-chain-019/groups/codex-init-agents/results/pyjwt_2.0.0_to_2.12.1/codex-openai-gpt-5.5/eval.json` |
| `pyjwt_2.0.0_to_2.12.1` | `native` | `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/pyjwt_2.0.0_to_2.12.1/codex-openai-gpt-5.5/eval.json` |
| `pyjwt_2.0.0_to_2.12.1` | `stop` | `artifacts://swe-chain-020/groups/aiwiki-lifecycle-hooks/results/pyjwt_2.0.0_to_2.12.1/codex-openai-gpt-5.5/eval.json` |
| `pyjwt_2.0.0_to_2.12.1` | `exact` | `artifacts://swe-chain-021/groups/aiwiki-exact-match-stop/results/pyjwt_2.0.0_to_2.12.1/codex-openai-gpt-5.5/eval.json` |
| `flask_2.0.0_to_2.0.1` | `raw` | `artifacts://swe-chain-019/groups/raw-codex/results/flask_2.0.0_to_2.0.1/codex-openai-gpt-5.5/eval.json` |
| `flask_2.0.0_to_2.0.1` | `init` | `artifacts://swe-chain-019/groups/codex-init-agents/results/flask_2.0.0_to_2.0.1/codex-openai-gpt-5.5/eval.json` |
| `flask_2.0.0_to_2.0.1` | `native` | `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/flask_2.0.0_to_2.0.1/codex-openai-gpt-5.5/eval.json` |
