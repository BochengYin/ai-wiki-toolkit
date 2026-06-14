# Blinded Applies-When Route Replay

This report compares the same 57 historical route traces with and without a
blindly generated `applies_when` treatment overlay.

## Setup

- Overlay labels applied: `14`
- Target docs selected by control selected-count frequency, not false-positive outcomes.
- Catalog cutoff: `trace-routed-at`
- Claim type: retrospective route-quality replay, not production improvement.

## Summary

| condition | traces | precision | noise | selected | selected useful | missed useful |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| control | 57 | 0.350 | 0.650 | 320 | 112 | 52 |
| treatment | 57 | 0.353 | 0.647 | 320 | 113 | 52 |

## Delta

- Precision delta: `0.0031250000000000444`
- Noise delta: `-0.0031250000000000444`
- Selected useful delta: `1`
- Missed useful delta: `0`
- Paired wins/losses/ties: `4` / `3` / `50`
