from __future__ import annotations

import json
from pathlib import Path
import re
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def _release_workflow_targets() -> set[str]:
    workflow = (ROOT / ".github" / "workflows" / "release-binaries.yml").read_text(
        encoding="utf-8"
    )
    return set(re.findall(r"^\s+target: ([a-z0-9-]+)\s*$", workflow, re.MULTILINE))


def _npm_wrapper_targets() -> set[str]:
    shared = (ROOT / "npm" / "shared.js").read_text(encoding="utf-8")
    return set(re.findall(r'target: "([a-z0-9-]+)"', shared))


def test_npm_wrapper_targets_are_subset_of_release_workflow_targets() -> None:
    npm_targets = _npm_wrapper_targets()
    release_targets = _release_workflow_targets()

    assert npm_targets <= release_targets


def test_public_package_metadata_includes_license_and_repository_links() -> None:
    package_json = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert (ROOT / "LICENSE").exists()
    assert package_json["license"] == "MIT"
    assert package_json["homepage"] == "https://github.com/BochengYin/ai-wiki-toolkit#readme"
    assert package_json["bugs"]["url"] == "https://github.com/BochengYin/ai-wiki-toolkit/issues"
    assert package_json["os"] == ["darwin", "linux"]

    assert pyproject["project"]["license"] == "MIT"
    assert pyproject["project"]["urls"] == {
        "Homepage": "https://github.com/BochengYin/ai-wiki-toolkit",
        "Repository": "https://github.com/BochengYin/ai-wiki-toolkit.git",
        "Issues": "https://github.com/BochengYin/ai-wiki-toolkit/issues",
    }


def test_release_workflow_passes_license_into_generated_homebrew_formula() -> None:
    workflow = (ROOT / ".github" / "workflows" / "release-binaries.yml").read_text(
        encoding="utf-8"
    )

    assert "--license MIT" in workflow
