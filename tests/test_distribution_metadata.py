from __future__ import annotations

import json
from pathlib import Path
import re
import tomllib

from ai_wiki_toolkit import __version__
from ai_wiki_toolkit.npm_distribution import expected_optional_dependencies, load_platform_packages

ROOT = Path(__file__).resolve().parents[1]


def _release_workflow_targets() -> set[str]:
    workflow = (ROOT / ".github" / "workflows" / "release-binaries.yml").read_text(
        encoding="utf-8"
    )
    return set(re.findall(r"^\s+target: ([a-z0-9-]+)\s*$", workflow, re.MULTILINE))


def _npm_wrapper_targets() -> set[str]:
    return {package.release_target for package in load_platform_packages()}


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
    assert package_json["os"] == ["darwin", "linux", "win32"]
    assert package_json["optionalDependencies"] == expected_optional_dependencies(__version__)

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


def test_release_workflow_installs_binutils_for_linux_musl_builds() -> None:
    workflow = (ROOT / ".github" / "workflows" / "release-binaries.yml").read_text(
        encoding="utf-8"
    )

    assert "target: linux-musl-x64" in workflow
    assert "--run-as-root" in workflow
    assert '--setup-command "apk add --no-cache binutils git"' in workflow
    assert "${{ matrix.container_extra_args }}" in workflow


def test_publish_npm_workflow_downloads_release_archives_by_prefix() -> None:
    workflow = (ROOT / ".github" / "workflows" / "publish-npm.yml").read_text(
        encoding="utf-8"
    )

    assert '--pattern "ai-wiki-toolkit-${version}-*"' in workflow


def test_publish_npm_workflow_can_force_trusted_auth_for_recovery() -> None:
    workflow = (ROOT / ".github" / "workflows" / "publish-npm.yml").read_text(
        encoding="utf-8"
    )

    assert "npm_auth_mode:" in workflow
    assert "Unsupported npm_auth_mode" in workflow
    assert "npm_auth_mode=token requires NPM_PUBLISH_TOKEN." in workflow
    assert "unset NODE_AUTH_TOKEN" in workflow
    assert "sed -i '/_authToken/d;/always-auth/d'" in workflow
