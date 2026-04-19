"""Stage npm platform packages from release assets."""

from __future__ import annotations

import argparse
from pathlib import Path

from ai_wiki_toolkit.npm_distribution import stage_platform_packages


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stage npm platform packages from GitHub Release assets."
    )
    parser.add_argument(
        "--version",
        required=True,
        help="Package version without the leading v, for example 0.1.6.",
    )
    parser.add_argument(
        "--asset-dir",
        type=Path,
        required=True,
        help="Directory containing downloaded release archives.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory where staged npm platform package folders will be created.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    staged = stage_platform_packages(
        version=args.version,
        asset_dir=args.asset_dir,
        output_root=args.output_dir,
    )
    for path in staged:
        print(path)


if __name__ == "__main__":
    main()
