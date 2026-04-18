from __future__ import annotations

from pathlib import Path

from ai_wiki_toolkit.release_version import find_version_mismatches, read_release_versions


def test_read_release_versions_reads_current_project_metadata() -> None:
    versions = read_release_versions(Path.cwd())

    assert versions.package_json == "0.1.6"
    assert versions.pyproject == "0.1.6"
    assert versions.python_package == "0.1.6"


def test_find_version_mismatches_reports_expected_release_mismatch() -> None:
    versions = read_release_versions(Path.cwd())

    mismatches = find_version_mismatches(versions, "0.1.7")

    assert mismatches == [
        "package.json version 0.1.6 != expected release version 0.1.7",
        "pyproject.toml version 0.1.6 != expected release version 0.1.7",
        "src/ai_wiki_toolkit/__init__.py version 0.1.6 != expected release version 0.1.7",
    ]
