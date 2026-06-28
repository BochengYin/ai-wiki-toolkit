# Step Lifecycle

One chain is an ordered sequence of version migrations. One step is a single
`prev_version -> next_version` migration.

Per-step lifecycle:

1. Copy the previous version source tree into the editable checkout.
2. Remove the target repo's own tests from the editable code area.
3. Install the arm-specific prompt, AI Wiki tree, hook runtime, or memory gate.
4. Write the version-specific upgrade spec into the checkout.
5. Split eligible tests into revealed feedback and final holdout subsets.
6. Run the agent build turn.
7. Run revealed feedback checks and write a bounded retry report if needed.
8. With `max_iters=2`, run at most one fix turn.
9. Run revealed checks again and select the final build+fix phase.
10. Run final holdout scoring when the protocol enables it.
11. Save the step to `chain.json`.
12. Release a successful patched checkout as the baseline for the next step.

The chain property matters: later steps inherit successful earlier patches, so
mistakes can cascade.
