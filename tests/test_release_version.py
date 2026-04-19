from __future__ import annotations

from pathlib import Path

from ai_wiki_toolkit import __version__
from ai_wiki_toolkit.release_version import find_version_mismatches, read_release_versions


def test_read_release_versions_reads_current_project_metadata() -> None:
    versions = read_release_versions(Path.cwd())

    assert versions.package_json == __version__
    assert versions.pyproject == __version__
    assert versions.python_package == __version__


def test_find_version_mismatches_reports_expected_release_mismatch() -> None:
    versions = read_release_versions(Path.cwd())

    expected_version = "9.9.9"
    mismatches = find_version_mismatches(versions, expected_version)

    assert mismatches == [
        f"package.json version {__version__} != expected release version {expected_version}",
        f"pyproject.toml version {__version__} != expected release version {expected_version}",
        f"src/ai_wiki_toolkit/__init__.py version {__version__} != expected release version {expected_version}",
    ]
