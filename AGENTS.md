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

If this repository contains `ai-wiki/`, read `ai-wiki/_toolkit/system.md` before starting work and follow its end-of-task workflow. Use `ai-wiki/index.md` as the repo-owned map when you need navigation.
<!-- aiwiki-toolkit:end -->
