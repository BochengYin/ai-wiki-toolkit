from __future__ import annotations

import functools
import http.server
import json
import os
import platform
from pathlib import Path
import shutil
import socketserver
import subprocess
import threading

import pytest
from ai_wiki_toolkit import __version__

ROOT = Path(__file__).resolve().parents[1]


def test_package_json_version_matches_python_package() -> None:
    package_json = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))

    assert package_json["version"] == __version__


def test_package_json_exposes_cli_bin_and_postinstall() -> None:
    package_json = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))

    assert package_json["bin"]["aiwiki-toolkit"] == "npm/bin/aiwiki-toolkit.js"
    assert package_json["scripts"]["postinstall"] == "node npm/install.js"


def test_npm_wrapper_files_exist() -> None:
    assert (ROOT / "npm" / "install.js").exists()
    assert (ROOT / "npm" / "bin" / "aiwiki-toolkit.js").exists()
    assert (ROOT / "npm" / "shared.js").exists()


def _current_npm_target() -> str | None:
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "darwin" and machine in {"arm64", "aarch64"}:
        return "macos-arm64"
    if system == "darwin" and machine in {"x86_64", "amd64"}:
        return "macos-x64"
    if system == "linux" and machine in {"x86_64", "amd64"}:
        return "linux-x64"
    return None


class QuietHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


def test_npm_install_downloads_archive_outside_install_directory(tmp_path: Path) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not available")

    target = _current_npm_target()
    if target is None:
        pytest.skip("current platform is not supported by the npm wrapper")

    version = f"v{__version__}" if not __version__.startswith("v") else __version__
    asset_name = f"ai-wiki-toolkit-{version}-{target}.tar.gz"

    release_dir = tmp_path / "releases" / version
    release_dir.mkdir(parents=True)
    binary_contents = "#!/bin/sh\necho installed-from-test\n"
    (release_dir / asset_name).write_text(binary_contents, encoding="utf-8")

    package_dir = tmp_path / "package"
    package_dir.mkdir()
    shutil.copy2(ROOT / "package.json", package_dir / "package.json")
    shutil.copytree(ROOT / "npm", package_dir / "npm")

    tar_module = package_dir / "node_modules" / "tar"
    tar_module.mkdir(parents=True)
    (tar_module / "index.js").write_text(
        """
const fs = require("fs");
const path = require("path");

module.exports = {
  x: async ({ file, cwd }) => {
    const contents = fs.readFileSync(file, "utf8");
    fs.mkdirSync(cwd, { recursive: true });
    fs.writeFileSync(path.join(cwd, "aiwiki-toolkit"), contents);
  },
};
""".strip()
        + "\n",
        encoding="utf-8",
    )

    extract_zip_module = package_dir / "node_modules" / "extract-zip"
    extract_zip_module.mkdir(parents=True)
    (extract_zip_module / "index.js").write_text(
        """
module.exports = async () => {
  throw new Error("zip extraction should not run in this test");
};
""".strip()
        + "\n",
        encoding="utf-8",
    )

    handler = functools.partial(QuietHTTPRequestHandler, directory=str(tmp_path / "releases"))
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            env = os.environ.copy()
            env["AIWIKI_TOOLKIT_RELEASE_BASE_URL"] = (
                f"http://127.0.0.1:{server.server_address[1]}"
            )
            result = subprocess.run(
                [node, "npm/install.js"],
                cwd=package_dir,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
        finally:
            server.shutdown()
            thread.join()

    assert result.returncode == 0, result.stderr
    assert f"Installed ai-wiki-toolkit binary for {target}" in result.stdout
    assert (package_dir / "npm" / "vendor" / target / "aiwiki-toolkit").read_text(
        encoding="utf-8"
    ) == binary_contents
