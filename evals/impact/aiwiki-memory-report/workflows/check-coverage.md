# Check Coverage

Coverage checks prevent incomplete cells from becoming headline results.

Rules:

- Count migration coverage by unique `(prev_version, next_version)` pairs.
- Do not count `eval.json.chain[]` phase rows as migration steps.
- Flag any cited cell that is missing from `coverage-status.md`.
- Flag any partial cell cited without an explicit caveat.
- Flag any empty `0/0/0` shell outside the coverage/quarantine table.
- Keep empty shells out of result tables unless the table explicitly documents
  them as excluded or quarantined artifacts.

Current status after the 2026-06-28 refresh:

- No known partial cells.
- Empty `0/0/0` shells remain listed in `coverage-status.md`.
