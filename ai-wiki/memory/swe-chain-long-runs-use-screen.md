# SWE-Chain Long Runs Need Detached Screen

## Trigger

Use this when launching a long-running SWE-chain experiment queue or multi-repo panel from a Codex tool call.

## Public/Local Signal

A queue launched with `nohup ... &` appeared running briefly, but after the tool call returned the host-side runner and `codex exec` process were gone. The Docker container remained up only as an idle `tail -f /dev/null` container, and the result directory had only startup warnings in `live_log.jsonl` with no `thread.started`, no `turn.started`, and no `chain.json`.

## Failed Attempt

Starting the experiment with plain background `nohup bash run_config/run_exact_match_queue.sh ... &` did not keep the host-side queue alive in this environment.

## Fix Or Rule

For long SWE-chain queues launched from Codex, start the queue in detached `/usr/bin/screen`:

```bash
/usr/bin/screen -dmS <session-name> /bin/zsh -lc "cd '<experiment-root>' && exec bash run_config/run_exact_match_queue.sh '<run-id>' > '<launch-log>' 2>&1"
```

Then verify all three before considering the run live:

- `screen -ls` shows the detached session.
- `ps` shows `run_exact_match_queue.sh`, `generate.chain`, and `codex exec`.
- `live_log.jsonl` contains `thread.started` and `turn.started`, not only startup warnings.

For dependent follow-up runs, prefer a small watcher script in the OS temp
directory over a deeply nested one-liner. Have the watcher poll actual host-side
processes with `pgrep -f` for the runner, `generate.chain`, `codex exec`, and
eval command. Do not rely only on `screen -ls` from inside another detached
screen; it can miss sibling sessions in this environment and trigger the
follow-up too early. Avoid multiline `python -c` inside nested screen commands;
use a temp script or heredoc so the coverage check fails cleanly.

When launching several screen sessions from Codex, remember that the active
shell may be `zsh`. Do not put bash-only array expansion such as
`${!chains[@]}` inside an inline command that the outer shell can see; either
write a small launcher script or start each `screen` command explicitly.

For sequential fill runs that archive old empty-shell artifacts one arm at a
time, make the monitor ignore pending arms until their archive marker exists or
they become the current arm. Otherwise stale pre-archive `chain.json` files from
old startup failures can make pending arms look like partial coverage, such as
`1/11`, before the new run has actually started that arm.

## Applies When

- The task is to start, resume, or monitor a multi-hour SWE-chain or AI Wiki Toolkit experiment from Codex.
- The queue depends on host-side Codex CLI processes, not only Docker containers.

## Do Not Use When

- Running a short foreground command.
- A user explicitly wants the command tied to the current terminal session.
- A different process supervisor, such as `tmux`, `launchctl`, or CI, is already managing the queue.

## Related Files

- `run_config/run_exact_match_queue.sh`
- `run_config/run_one.sh`
- `groups/*/agent/codex.py`

## Source Pointer

Observed while launching `swe-chain-021-aiwiki-exact-match-stop`: the `nohup` launch left an idle pytest7 Docker container and no JSON turn events; relaunching via detached `screen` kept the queue, `generate.chain`, and `codex exec` alive.
