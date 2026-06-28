# Artifact Contract

Raw artifacts are large and usually remain outside this repository. Public docs
refer to them through logical artifact IDs.

| Artifact | Meaning | Public handling |
|---|---|---|
| `chain.json` | Ordered step state, phase summaries, diffs, holdout records, and resume state | Reference by logical ID; include small summaries only |
| `eval.json` | Scored build, build+fix, and final-holdout metrics from replay/live test results | Numeric measurement source of truth |
| `record.jsonl` | Turn-level trajectory events saved out of `chain.json` | Keep external or sampled |
| `live_log.jsonl` | Agent/runner live event log for debugging timeouts and failures | Keep external or sampled |
| `live_results.jsonl` | Live feedback or holdout test result rows when used for scoring | Keep external or sampled |
| `replay_curr_results.jsonl` | Replay test results for current patched codebases | External raw artifact |
| `replay_prev_results.jsonl` | Replay test results for previous baseline codebases | External raw artifact |

`source-of-truth/` tables are derived, audited report inputs. They should name
their raw logical artifact IDs or audit sources.
