# Formal E2E Trial/Error Automation Report

- Period: `formal-20260524T034658Z`
- CLI under test: npm-installed `/opt/homebrew/bin/aiwiki-toolkit`
- Version: `ai-wiki-toolkit 0.1.36`
- Release tag: `v0.1.36`
- Scope: orchestration E2E smoke for trial/error discovery, scheduled reporting, workspace preparation, slot execution, artifact capture, scoring, run indexing, and report generation.
- Agent command: `/usr/bin/true`
- Semantic quality claim: none. This run proves the released automation path executes end to end; it does not grade real agent reasoning quality.

## Release Verification

- PR #73 merged into `main`.
- `v0.1.33` and `v0.1.34` were not reused after failed release binary workflows.
- `v0.1.35` published successfully, then exposed a packaged-runtime eval runner bug during local E2E.
- `v0.1.36` fixed the packaged-runtime script launcher and published successfully.
- GitHub Release assets for `v0.1.36`: macOS arm64/x64, Linux arm64/x64/musl-x64, Windows arm64/x64, and `aiwiki-toolkit.rb`.
- npm latest: `ai-wiki-toolkit@0.1.36`.
- Windows ARM release smoke: success.

## Discovery

- Active candidates: `25`
- Candidate status counts: `candidate=12`, `observed=6`, `promoted=7`
- Runnable formal families: `7`

## Scheduled Run

- Family: `ownership_boundary`
- Slots executed: `s01` through `s06`
- Score policy: `command-exit`
- Runner success: `true`
- Run directory: `/private/tmp/aiwiki_first_round/ownership_boundary/runs/formal-20260524T034658Z-ownership_boundary`
- Run index: `ai-wiki/_toolkit/evals/runs/index.json`
- Schedule report: `ai-wiki/_toolkit/evals/reports/formal-20260524T034658Z/report.md`
- Product report: `/private/tmp/aiwiki_first_round/ownership_boundary/runs/formal-20260524T034658Z-ownership_boundary/report_bundle/impact-report.md`

## Outcome

- Schedule run status: `ran`
- Indexed runs after this run: `3`
- Primary comparison outcome: `neutral_signal`
- First-attempt success: `6/6`
- Artifact capture: `result.json`, `workspace_diff.patch`, `workspace_status.txt`, `workspace_head.txt`, `command_result.json`, `score.json`, manifest, bundle, and schedule report were generated.

## Interpretation

The released npm CLI can now run the full eval automation loop locally from a user checkout. The earlier packaged-runtime failure was real and is fixed in `0.1.36`: the standalone binary now invokes eval helper scripts through a real Python interpreter instead of treating script paths as Typer subcommands.

The next meaningful research run should replace `/usr/bin/true` with a real agent command and use rubric scoring or human review for semantic quality.
