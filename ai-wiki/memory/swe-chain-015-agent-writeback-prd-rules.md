# SWE-Chain 015 Agent Writeback PRD Rules

## Trigger

The user clarified the requirements while drafting the PRD for
`swe-chain-015-flask-agent-skill-writeback`.

## Public/Local Signal

The PRD was written at
`/Users/by/AI Project/AI wiki Toolkit test repos/swe-chain-015-flask-agent-skill-writeback/prd.md`.

During formal execution, local runner probes and failed/superseded runs showed that the
original agent-self-triggered hook convention was not reliable enough for formal data.
The completed run used a runner-managed normal-end hook instead.

## Failed Attempt

The original PRD expectation said every formal attempt should end by having the coding
agent trigger the after-conversation hook. In practice, formal attempts could timeout or
stall before reaching that self-call. Local Codex lifecycle hook probes also did not
produce a usable Stop/PreToolUse hook signal in this environment.

## Fix Or Rule

For future work on `swe-chain-015-flask-agent-skill-writeback`, read the experiment PRD before
running or modifying the experiment.

Key confirmed rules:

- The formal `/goal` applies only to formal experiment execution, not PRD writing.
- Workflow correctness is the primary success criterion; performance metrics are analysis outputs.
- A real programmatic conversation fork is required. A separate new session plus context file is not acceptable.
- If programmatic fork preflight fails, stop and write blocked outputs rather than running a simulation.
- Treat "agent calls the hook itself" as an auxiliary convention only. The formal
  trigger is the runner normal-end hook: Codex exit code `0` plus `turn.completed`,
  then run the after-conversation hook before revealed feedback.
- Timeout, nonzero exit, crash, or missing `turn.completed` means no writeback hook;
  quarantine the incomplete run and rerun after repair if the failure is repairable.
- Treatment writeback must call the trial-error writeback skill every time, even when it skips.
- Memory candidates must go to `/app/ai-wiki/memory_quarantine/<attempt_id>/` and be immediately audited before publication.
- When Codex runs on a host mirror while Docker owns `/app`, approved hook-published
  memory must sync back into the container and be verified in `/app/ai-wiki/memory/index.md`
  before the next step.
- Repairable setup/runtime failures should be diagnosed, fixed, and rerun without a fixed retry cap.
- Protocol blockers must stop the run and be reported instead of being repaired around.

## Applies When

- Running, reviewing, or modifying `swe-chain-015-flask-agent-skill-writeback`.
- Creating follow-up scripts or prompts for that experiment.

## Do Not Use When

- Running a different SWE-Chain experiment with its own PRD or user instructions.
- The current user explicitly changes the experiment protocol.

## Related Files

- `/Users/by/AI Project/AI wiki Toolkit test repos/swe-chain-015-flask-agent-skill-writeback/prd.md`
- `/Users/by/AI Project/ai-wiki-toolkit/evals/impact/public/flask_swe_chain_memory_eval_report.md`

## Source Pointer

- Source: User clarification interview in Codex while drafting the PRD.
- Captured by: Codex.
- Captured at: 2026-06-14.
