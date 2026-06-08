# Impact Eval Route Noise Report

- Generated at: `2026-06-08T16:21:09+10:00`
- Since: `2026-06-08T16:20:30+10:00`
- Handle: `bochengyin`

## Summary

- Route traces: `12`
- Selected docs: `59`
- Selected-but-unused docs: `41`
- Missed useful docs: `4`
- Route precision: `0.305`
- Route recall proxy: `0.818`
- Route noise rate: `0.695`

## Task Types

| task_type | traces | precision | noise | unused | missed |
| --- | --- | --- | --- | --- | --- |
| release_distribution | 1 | 0.000 | 1.000 | 1 | 2 |
| general | 1 | 0.167 | 0.833 | 5 | 0 |
| eval_workflow | 2 | 0.250 | 0.750 | 9 | 0 |
| scaffold_prompt_workflow | 2 | 0.333 | 0.667 | 8 | 0 |
| workflow_state | 1 | 0.333 | 0.667 | 2 | 0 |
| memory_governance | 5 | 0.360 | 0.640 | 16 | 2 |

## Top Noisy Traces

| task | task_type | precision | noise | unused | missed |
| --- | --- | --- | --- | --- | --- |
| fvscode-07-postinstall-archive-staging | release_distribution | 0.000 | 1.000 | 1 | 2 |
| fvscode-01-fresh-checkout-baseline | eval_workflow | 0.167 | 0.833 | 5 | 0 |
| fvscode-06-source-vs-installed-entrypoint | general | 0.167 | 0.833 | 5 | 0 |
| fvscode-12-local-forward-summary | memory_governance | 0.167 | 0.833 | 5 | 1 |
| fvscode-03-forward-metrics-separation | eval_workflow | 0.333 | 0.667 | 4 | 0 |
| fvscode-04-scaffold-prompt-workflow-compliance | scaffold_prompt_workflow | 0.333 | 0.667 | 4 | 0 |
| fvscode-05-ownership-boundary-user-docs | scaffold_prompt_workflow | 0.333 | 0.667 | 4 | 0 |
| fvscode-08-source-session-provenance | memory_governance | 0.333 | 0.667 | 4 | 0 |
| fvscode-09-behavior-suite-separate-layer | memory_governance | 0.333 | 0.667 | 4 | 0 |
| fvscode-10-taxonomy-candidates-no-activation | workflow_state | 0.333 | 0.667 | 2 | 0 |
| fvscode-11-cjk-task-only-interpretation | memory_governance | 0.500 | 0.500 | 3 | 0 |
| fvscode-02-route-trace-reuse-pipeline | memory_governance | 1.000 | 0.000 | 0 | 1 |

## Noisy Doc Hotspots

| doc | selected_unused | selected_not_helpful |
| --- | --- | --- |
| people/bochengyin/drafts/local-dogfooding-should-check-source-cli-vs-installed-entrypoint | 3 | 0 |
| people/bochengyin/drafts/route-precision-experiments-should-separate-forward-routing-from-historical-metrics | 3 | 0 |
| people/bochengyin/drafts/ai-wiki-reuse-metrics-should-exclude-managed-docs-and-shard-by-handle | 3 | 0 |
| people/bochengyin/drafts/route-usefulness-eval-needs-route-traces-and-actual-use-comparison | 3 | 0 |
| people/bochengyin/drafts/company-code-telemetry-must-be-local-metadata-first | 2 | 0 |
| people/bochengyin/drafts/route-false-positives-need-stage-labels-and-abstention | 2 | 0 |
| people/bochengyin/drafts/packaged-eval-runners-need-real-python-script-launchers | 2 | 0 |
| people/bochengyin/drafts/public-eval-artifacts-must-redact-local-provenance-before-push | 2 | 0 |
| people/bochengyin/drafts/eval-product-run-requests-need-family-scope-check | 2 | 0 |
| people/bochengyin/drafts/end-of-task-ai-wiki-update-check-must-always-run | 2 | 0 |
| people/bochengyin/drafts/introducing-new-npm-package-names-needs-a-bootstrap-publish-plan | 1 | 0 |
| people/bochengyin/drafts/route-cohorts-need-original-task-text-for-exact-replay | 1 | 0 |
| conventions/package-managed-vs-user-owned-docs | 1 | 0 |
| people/bochengyin/drafts/efficiency-eval-should-include-source-incident-cost | 1 | 0 |
| people/bochengyin/drafts/impact-eval-result-capture-must-include-untracked-files | 1 | 0 |
| people/bochengyin/drafts/source-incident-timing-needs-provenance | 1 | 0 |
| problems/windows-arm-smoke-version-checks-need-full-cli-output | 1 | 0 |
| people/bochengyin/drafts/route-precision-next-method-should-use-stage-slot-selection | 1 | 0 |
| conventions/distribution-target-matrix-must-match-published-assets | 1 | 0 |
| people/bochengyin/drafts/user-owned-ai-wiki-index-should-not-be-an-upgrade-surface | 1 | 0 |
| review-patterns/shared-prompt-files-must-be-user-agnostic | 1 | 0 |
| constraints | 1 | 0 |
| people/bochengyin/drafts/managed-toolkit-workflows-need-a-toc-and-scope-aware-conflict-checks | 1 | 0 |
| people/bochengyin/drafts/toolkit-installed-repo-local-skills-should-skip-existing-files | 1 | 0 |
| people/bochengyin/drafts/codex-session-recovery-should-search-jsonl-and-state-db | 1 | 0 |
| people/bochengyin/drafts/ai-wiki-usefulness-metrics-need-task-level-checks-plus-doc-events | 1 | 0 |
| people/bochengyin/drafts/release-assets-should-not-be-blocked-by-homebrew-tap-sync | 1 | 0 |

## Missed Doc Hotspots

| doc | missed_useful |
| --- | --- |
| people/bochengyin/drafts/npm-postinstall-must-not-delete-its-own-download-archive | 1 |
| people/bochengyin/drafts/workflow-packaging-queue-should-use-evidence-gated-smallest-asset-selection | 1 |
| people/bochengyin/drafts/external-ai-wiki-metrics-need-a-proof-stack-not-a-dashboard | 1 |
| people/bochengyin/drafts/route-usefulness-eval-needs-route-traces-and-actual-use-comparison | 1 |

## Recommendations

- Review task types with high selected-but-unused counts before adding more memory.
- Add or refine route hints for repeated missed useful docs.
- Demote or narrow docs repeatedly selected without downstream reuse.
- Treat recall as a proxy; useful docs that were never looked up remain unknown.
