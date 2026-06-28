# Leakage Boundaries

The benchmark should measure whether repo-level memory helps future coding
tasks without using hidden or future information.

Allowed inputs:

- The step specification shown to the agent.
- The editable source checkout for the current step.
- Public/local feedback generated before a fix turn, when the protocol exposes
  revealed feedback.
- Repo-local AI Wiki material configured for the current arm.

Disallowed inputs:

- Final holdout output as prompt input.
- Hidden evaluator names, raw hidden failure messages, or future-step answers as
  memory.
- Cross-group memory or logs.
- Imported narrative material as numeric source of truth unless audited.

Writeback mechanisms must quarantine or reject candidate memory that depends on
hidden, final, future-step, or cross-group evidence.
