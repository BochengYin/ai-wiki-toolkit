"""Sync a generated formula into a checked-out Homebrew tap repository."""

from __future__ import annotations

import argparse
from pathlib import Path

from ai_wiki_toolkit.homebrew_tap import release_commit_message, sync_formula_into_tap


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--formula", required=True, type=Path, help="Path to aiwiki-toolkit.rb.")
    parser.add_argument(
        "--tap-dir",
        required=True,
        type=Path,
        help="Path to the checked-out Homebrew tap repository root.",
    )
    parser.add_argument("--version", required=True, help="Release version for commit message output.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    formula_text = args.formula.read_text(encoding="utf-8")
    result = sync_formula_into_tap(formula_text=formula_text, tap_root=args.tap_dir)
    print(result.formula_path)
    print(f"changed={str(result.changed).lower()}")
    print(release_commit_message(args.version))


if __name__ == "__main__":
    main()
