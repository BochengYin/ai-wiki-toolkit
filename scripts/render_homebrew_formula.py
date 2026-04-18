"""Render a Homebrew formula from GitHub Release archives."""

from __future__ import annotations

import argparse
from pathlib import Path

from ai_wiki_toolkit.homebrew_formula import (
    FORMULA_FILENAME,
    formula_assets_from_directory,
    render_homebrew_formula,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, help="GitHub repository in owner/name form.")
    parser.add_argument("--version", required=True, help="Release tag, for example v0.1.0.")
    parser.add_argument(
        "--asset-dir",
        required=True,
        type=Path,
        help="Directory containing GitHub Release archives produced by the release workflow.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(FORMULA_FILENAME),
        help="Path where the generated formula should be written.",
    )
    parser.add_argument("--homepage", help="Optional homepage override.")
    parser.add_argument("--license", dest="license_name", help="Optional SPDX license identifier.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    assets = formula_assets_from_directory(args.asset_dir, args.version)
    formula = render_homebrew_formula(
        repository=args.repository,
        version=args.version,
        assets=assets,
        homepage=args.homepage,
        license_name=args.license_name,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(formula, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
