"""Helpers for validating release version consistency."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import tomllib


@dataclass(frozen=True)
class ReleaseVersions:
    package_json: str
    pyproject: str
    python_package: str


def read_release_versions(root: Path) -> ReleaseVersions:
    """Read the package versions that must stay in sync for a release."""
    package_json_version = json.loads((root / "package.json").read_text())["version"]
    pyproject_version = tomllib.loads((root / "pyproject.toml").read_text())["project"][
        "version"
    ]

    namespace: dict[str, str] = {}
    exec((root / "src" / "ai_wiki_toolkit" / "__init__.py").read_text(), namespace)
    python_package_version = namespace["__version__"]

    return ReleaseVersions(
        package_json=package_json_version,
        pyproject=pyproject_version,
        python_package=python_package_version,
    )


def find_version_mismatches(
    versions: ReleaseVersions, expected_version: str | None = None
) -> list[str]:
    """Return human-readable mismatch messages for release version validation."""
    mismatches: list[str] = []

    if versions.package_json != versions.pyproject:
        mismatches.append(
            f"package.json version {versions.package_json} != pyproject.toml version {versions.pyproject}"
        )

    if versions.package_json != versions.python_package:
        mismatches.append(
            f"package.json version {versions.package_json} != src/ai_wiki_toolkit/__init__.py version {versions.python_package}"
        )

    if expected_version is not None:
        if versions.package_json != expected_version:
            mismatches.append(
                f"package.json version {versions.package_json} != expected release version {expected_version}"
            )
        if versions.pyproject != expected_version:
            mismatches.append(
                f"pyproject.toml version {versions.pyproject} != expected release version {expected_version}"
            )
        if versions.python_package != expected_version:
            mismatches.append(
                f"src/ai_wiki_toolkit/__init__.py version {versions.python_package} != expected release version {expected_version}"
            )

    return mismatches
