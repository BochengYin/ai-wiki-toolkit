"""Fail the release workflow when tag and package versions drift."""

from __future__ import annotations

import sys
from pathlib import Path

from ai_wiki_toolkit.release_version import find_version_mismatches, read_release_versions


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: check_release_version.py <tag>", file=sys.stderr)
        return 2

    tag = argv[1]
    expected = tag[1:] if tag.startswith("v") else tag
    versions = read_release_versions(Path.cwd())
    mismatches = find_version_mismatches(versions, expected)

    if mismatches:
        print("Release version mismatch detected:", file=sys.stderr)
        for mismatch in mismatches:
            print(f"- {mismatch}", file=sys.stderr)
        return 1

    print(f"Release version {expected} matches package metadata.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
