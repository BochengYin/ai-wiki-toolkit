from __future__ import annotations

import json
from pathlib import Path

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
