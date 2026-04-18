"""Render Homebrew formulae for ai-wiki-toolkit release assets."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

from ai_wiki_toolkit.release_artifacts import release_archive_name

DEFAULT_DESCRIPTION = "Local-first scaffold for repo-local and home-level AI wiki prompts"
FORMULA_CLASS_NAME = "AiwikiToolkit"
FORMULA_FILENAME = "aiwiki-toolkit.rb"
BREW_TARGETS = ("macos-arm64", "macos-x64", "linux-x64")


@dataclass(frozen=True)
class FormulaAsset:
    target: str
    sha256: str


def release_asset_url(repository: str, version: str, target: str) -> str:
    archive_name = release_archive_name(version, target)
    return f"https://github.com/{repository}/releases/download/{version}/{archive_name}"


def sha256_for_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def formula_assets_from_directory(asset_dir: Path, version: str) -> list[FormulaAsset]:
    assets: list[FormulaAsset] = []
    for target in BREW_TARGETS:
        archive_path = asset_dir / release_archive_name(version, target)
        if not archive_path.exists():
            raise FileNotFoundError(f"Missing release archive for {target}: {archive_path}")
        assets.append(FormulaAsset(target=target, sha256=sha256_for_file(archive_path)))
    return assets


def _asset_by_target(assets: list[FormulaAsset]) -> dict[str, FormulaAsset]:
    mapping = {asset.target: asset for asset in assets}
    missing = [target for target in BREW_TARGETS if target not in mapping]
    if missing:
        raise ValueError(f"missing Homebrew formula assets for targets: {', '.join(missing)}")
    return mapping


def render_homebrew_formula(
    *,
    repository: str,
    version: str,
    assets: list[FormulaAsset],
    homepage: str | None = None,
    description: str = DEFAULT_DESCRIPTION,
    license_name: str | None = None,
) -> str:
    normalized_homepage = homepage or f"https://github.com/{repository}"
    asset_map = _asset_by_target(assets)
    version_number = version.removeprefix("v")
    lines = [
        f"class {FORMULA_CLASS_NAME} < Formula",
        f'  desc "{description}"',
        f'  homepage "{normalized_homepage}"',
        f'  version "{version_number}"',
    ]
    if license_name:
        lines.append(f'  license "{license_name}"')
    lines.extend(
        [
            "",
            "  on_macos do",
            "    on_arm do",
            f'      url "{release_asset_url(repository, version, "macos-arm64")}"',
            f'      sha256 "{asset_map["macos-arm64"].sha256}"',
            "    end",
            "",
            "    on_intel do",
            f'      url "{release_asset_url(repository, version, "macos-x64")}"',
            f'      sha256 "{asset_map["macos-x64"].sha256}"',
            "    end",
            "  end",
            "",
            "  on_linux do",
            "    on_intel do",
            f'      url "{release_asset_url(repository, version, "linux-x64")}"',
            f'      sha256 "{asset_map["linux-x64"].sha256}"',
            "    end",
            "  end",
            "",
            "  def install",
            '    bin.install "aiwiki-toolkit"',
            "  end",
            "",
            "  test do",
            '    assert_match version.to_s, shell_output("#{bin}/aiwiki-toolkit --version")',
            "  end",
            "end",
        ]
    )
    return "\n".join(lines) + "\n"
