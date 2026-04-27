# Repository Guidelines

## Project Structure & Module Organization
Core Python code lives in `src/ai_wiki_toolkit/`. `cli.py` is the Typer entrypoint; the other modules hold scaffold, path, release, and Homebrew logic. Tests live in `tests/`, with fixtures in `tests/conftest.py` and helpers in `tests/helpers.py`. The Node wrapper is under `npm/`, release scripts are in `scripts/`, docs are in `docs/`, and CI lives in `.github/workflows/`.

## Build, Test, and Development Commands
Use `uv sync --extra dev` for a lockfile-based setup, or `python -m pip install -e ".[dev]"` to match the README and CI. Run tests with `uv run pytest` or `python -m pytest`. Install release extras with `python -m pip install ".[release]"`. Validate the npm wrapper with `npm pack --dry-run --ignore-scripts`. Follow `docs/releasing.md` for local PyInstaller dry runs.

## Coding Style & Naming Conventions
Target Python 3.11+ and follow the existing style: 4-space indentation, `from __future__ import annotations`, explicit type hints, and snake_case for modules, functions, and tests. Use PascalCase only for classes and exceptions. Keep CLI wiring thin in `cli.py`; move filesystem or content logic into dedicated modules. No formatter or linter is configured yet, so match the current import ordering and concise docstring style.

## Testing Guidelines
This repo uses `pytest` with files named `test_*.py` and scenario-style functions such as `test_init_empty_repo_creates_expected_tree`. Add or update tests for every behavior change, especially around scaffold compatibility, prompt-file updates, release artifacts, and wrapper behavior. Prefer `typer.testing.CliRunner` for CLI coverage and the existing filesystem fixtures for repo/home scenarios.

## Commit & Pull Request Guidelines
Recent commits use short, imperative, sentence-case subjects such as `Fix release publish job and normalize AI wiki wording`. Keep commits focused and separate behavioral changes from release or docs-only updates where possible. Pull requests should summarize user-facing impact, list local verification commands, and link any related issue or follow-up. Update docs when install or release behavior changes.

## Compatibility & Configuration Notes
`aiwiki-toolkit` is designed to run inside a git repository and derives default handles from `git user.name` or `git user.email`. Preserve the compatibility guarantees in `README.md`: do not overwrite user-owned `ai-wiki/**/*.md` content outside managed `_toolkit/` paths, and keep prompt-file edits inside the `<!-- aiwiki-toolkit:start -->` and `<!-- aiwiki-toolkit:end -->` markers.

<!-- aiwiki-toolkit:start -->
## AI Wiki Toolkit

Before starting work:

1. Run `aiwiki-toolkit route --task "<current user request>"` when available, and use the generated AI Wiki Context Packet as the first-pass routing layer.
2. Read `ai-wiki/_toolkit/system.md`.
3. Use `ai-wiki/index.md` as a repo-owned map when you need a quick overview of local AI wiki areas.
4. If repo docs are not enough, read `<home>/ai-wiki/system/_toolkit/system.md` and then `<home>/ai-wiki/system/index.md`.
5. Keep project-specific notes in `ai-wiki/`.
6. Keep cross-project reusable notes in `<home>/ai-wiki/system/`.
7. Only suggest promotion from a draft to a shared pattern or convention when the two-signal gate is satisfied.
8. Agents may suggest promotion candidates, but humans confirm shared patterns and team conventions.
9. If `ai-wiki-clarify-before-code` is available, use it before implementation when ambiguity materially affects coding.
10. If `ai-wiki-capture-review-learning` is available, use it when reusable review feedback appears.
11. If `ai-wiki-reuse-check` and `ai-wiki-update-check` skills are available, use them to produce the end-of-task AI wiki evidence footer and write-back outcome.

## End Of Task

1. Produce one AI wiki reuse footer for every completed task.
2. First classify the task as `relevant`, `optional`, or `not_relevant` for AI wiki use; pure operational tasks such as pushing a PR or running an already-decided command are `not_relevant`.
3. If any user-owned AI wiki docs were consulted, record one `aiwiki-toolkit record-reuse` event per consulted doc.
4. If a managed `_toolkit/**` doc materially changed the plan or behavior, cite its path in a progress update or final note, but do not log it with `record-reuse`.
5. If a user-owned AI wiki doc materially changed the plan or behavior, cite its path in a progress update or final note.
6. Record one `aiwiki-toolkit record-reuse-check` entry for the task using `wiki_used` or `no_wiki_use`.
7. Produce one AI wiki write-back outcome for every completed task, even if the result is `None`.
8. Before returning `None`, check for convention candidates, reusable PR review learning, feature clarification memory, durable decisions, problem-solution memory, missed relevant memory, conflict or supersession, or a person preference that should stay personal for now.
9. Choose exactly one result: `None`, `Draft`, or `PromotionCandidate`.
10. If the result is `Draft`, record the lesson under `ai-wiki/people/<handle>/drafts/` and print `AI Wiki Write-Back Path: <path>`.
11. If the result is `PromotionCandidate`, mark or update the draft as a promotion candidate, print `AI Wiki Write-Back Path: <path>`, and ask for human confirmation before creating `ai-wiki/review-patterns/*.md` or `ai-wiki/conventions/*.md`.
12. Always print exactly one final status line:
   - `AI Wiki Write-Back: none`
   - `AI Wiki Write-Back: draft recorded`
   - `AI Wiki Write-Back: promotion candidate`
<!-- aiwiki-toolkit:end -->
