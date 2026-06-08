# Agent Harness Behavior Test Report

- Generated at: `2026-06-08T16:21:04+10:00`
- Suite: `phase-plan-shadow-behavior-suite-2026-06-06`

## Summary

- Cases: `4`
- Passed cases: `4`
- Failed cases: `0`
- Failed checks: `0`
- Blocks activation: `False`
- Activation status: `eligible_for_shadow_validation`
- Activation reason: Behavior tests passed; activation still requires replay and product review.

## Cases

| case | status | blocks_activation | phase | workflow |
| --- | --- | --- | --- | --- |
| plan-no-edit | pass | False | plan | None |
| weekly-workflow-contract | pass | False | workflow | weekly-report-diagnostics |
| validation-runs-tests | pass | False | validate | None |
| git-phase-no-push-pr | pass | False | git | None |

## Failed Checks

_None._

## Failure Policy

- Behavior test failures block activation.
- Codex runtime-control failures return to runtime capability or adapter design.
- Doc-selection failures return to taxonomy, phase slot, or selector work.
- Harness failures must be fixed before more router tuning.
