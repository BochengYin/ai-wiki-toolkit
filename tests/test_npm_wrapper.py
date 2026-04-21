from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import zipfile

import pytest
from ai_wiki_toolkit import __version__
from ai_wiki_toolkit.npm_distribution import (
    expected_optional_dependencies,
    load_platform_packages,
    render_platform_package_json,
    stage_platform_packages,
)
from ai_wiki_toolkit.release_artifacts import release_archive_name

ROOT = Path(__file__).resolve().parents[1]


def test_package_json_version_matches_python_package() -> None:
    package_json = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))

    assert package_json["version"] == __version__


def test_package_json_exposes_cli_bin_and_optional_platform_dependencies() -> None:
    package_json = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))

    assert package_json["bin"]["aiwiki-toolkit"] == "npm/bin/aiwiki-toolkit.js"
    assert package_json["optionalDependencies"] == expected_optional_dependencies(__version__)
    assert "scripts" not in package_json or "postinstall" not in package_json["scripts"]


def test_npm_wrapper_files_exist() -> None:
    assert (ROOT / "npm" / "bin" / "aiwiki-toolkit.js").exists()
    assert (ROOT / "npm" / "shared.js").exists()
    assert (ROOT / "npm" / "platform-targets.json").exists()


def _current_npm_target() -> str | None:
    node = shutil.which("node")
    if node is None:
        return None

    result = subprocess.run(
        [
            node,
            "-e",
            "const { currentTarget } = require('./npm/shared');"
            "const target = currentTarget();"
            "process.stdout.write(target ? target.node_target : '');",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def test_current_target_resolves_linux_libc_variants() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not available")

    script = """
const { currentTarget } = require('./npm/shared');
const values = [
  currentTarget('linux', 'x64', 'glibc')?.package_name || '',
  currentTarget('linux', 'x64', 'musl')?.package_name || '',
  currentTarget('linux', 'arm64', 'glibc')?.package_name || '',
  currentTarget('win32', 'arm64')?.package_name || '',
];
process.stdout.write(values.join('\\n'));
"""
    result = subprocess.run(
        [node, "-e", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "ai-wiki-toolkit-linux-x64",
        "ai-wiki-toolkit-linux-musl-x64",
        "ai-wiki-toolkit-linux-arm64",
        "ai-wiki-toolkit-win32-arm64",
    ]


def test_npm_bin_invokes_installed_platform_binary(tmp_path: Path) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not available")

    node_target = _current_npm_target()
    if node_target is None:
        pytest.skip("current platform is not supported by the npm meta package")

    package = next(
        package for package in load_platform_packages() if package.node_target == node_target
    )
    if package.binary_name.endswith(".exe"):
        pytest.skip("wrapper integration test uses a shell stub and is skipped on Windows targets")

    package_dir = tmp_path / "package"
    package_dir.mkdir()
    shutil.copytree(ROOT / "npm", package_dir / "npm")

    platform_package_dir = package_dir / "node_modules" / package.package_name
    (platform_package_dir / "bin").mkdir(parents=True)
    (platform_package_dir / "package.json").write_text(
        render_platform_package_json(package, __version__),
        encoding="utf-8",
    )
    binary_path = platform_package_dir / "bin" / package.binary_name
    binary_path.write_text("#!/bin/sh\necho installed-from-platform-package\n", encoding="utf-8")
    binary_path.chmod(0o755)

    result = subprocess.run(
        [node, "npm/bin/aiwiki-toolkit.js"],
        cwd=package_dir,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "installed-from-platform-package"


def test_stage_platform_packages_creates_publishable_directories(tmp_path: Path) -> None:
    asset_dir = tmp_path / "release-assets"
    asset_dir.mkdir()
    output_dir = tmp_path / "build" / "npm-platforms"

    for package in load_platform_packages():
        archive_path = asset_dir / release_archive_name(__version__, package.release_target)
        payload = tmp_path / f"{package.release_target}-{package.binary_name}"
        payload.write_text("binary payload\n", encoding="utf-8")
        if archive_path.suffix == ".zip":
            with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.write(payload, arcname=package.binary_name)
        else:
            with tarfile.open(archive_path, "w:gz") as archive:
                archive.add(payload, arcname=package.binary_name)

    staged = stage_platform_packages(
        version=__version__,
        asset_dir=asset_dir,
        output_root=output_dir,
        repository_root=ROOT,
    )

    assert len(staged) == len(load_platform_packages())
    root_readme = (ROOT / "README.md").read_text(encoding="utf-8").strip()
    for package_dir in staged:
        package_json = json.loads((package_dir / "package.json").read_text(encoding="utf-8"))
        assert package_json["version"] == __version__
        platform_readme = (package_dir / "README.md").read_text(encoding="utf-8")
        assert root_readme in platform_readme
        assert (package_dir / "LICENSE").exists()
        bin_mapping = package_json["bin"]
        assert len(bin_mapping) == 1
        expected_binary_name = Path(next(iter(bin_mapping.values()))).name
        assert (package_dir / "bin" / expected_binary_name).exists()
