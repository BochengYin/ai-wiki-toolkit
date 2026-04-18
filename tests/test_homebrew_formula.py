from __future__ import annotations

from pathlib import Path

from ai_wiki_toolkit.homebrew_formula import (
    FormulaAsset,
    formula_assets_from_directory,
    release_asset_url,
    render_homebrew_formula,
    sha256_for_file,
)


def test_release_asset_url_uses_github_release_download_path() -> None:
    assert release_asset_url("example/ai-wiki-toolkit", "v0.1.0", "linux-x64") == (
        "https://github.com/example/ai-wiki-toolkit/releases/download/"
        "v0.1.0/ai-wiki-toolkit-v0.1.0-linux-x64.tar.gz"
    )


def test_sha256_for_file_returns_expected_digest(tmp_path: Path) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("aiwiki\n", encoding="utf-8")

    assert sha256_for_file(sample) == (
        "78be2802a078f6cb1653d5aee09b96b5bb36f704f0a8f7bf7a111b17f8329aa3"
    )


def test_formula_assets_from_directory_reads_expected_archives(tmp_path: Path) -> None:
    for filename in (
        "ai-wiki-toolkit-v0.1.0-macos-arm64.tar.gz",
        "ai-wiki-toolkit-v0.1.0-macos-x64.tar.gz",
        "ai-wiki-toolkit-v0.1.0-linux-x64.tar.gz",
    ):
        (tmp_path / filename).write_text(filename, encoding="utf-8")

    assets = formula_assets_from_directory(tmp_path, "v0.1.0")

    assert [asset.target for asset in assets] == ["macos-arm64", "macos-x64", "linux-x64"]


def test_render_homebrew_formula_includes_expected_urls_and_checksums() -> None:
    formula = render_homebrew_formula(
        repository="example/ai-wiki-toolkit",
        version="v0.1.0",
        license_name="MIT",
        assets=[
            FormulaAsset("macos-arm64", "a" * 64),
            FormulaAsset("macos-x64", "b" * 64),
            FormulaAsset("linux-x64", "c" * 64),
        ],
    )

    assert 'class AiwikiToolkit < Formula' in formula
    assert 'homepage "https://github.com/example/ai-wiki-toolkit"' in formula
    assert 'version "0.1.0"' in formula
    assert 'license "MIT"' in formula
    assert 'url "https://github.com/example/ai-wiki-toolkit/releases/download/v0.1.0/ai-wiki-toolkit-v0.1.0-macos-arm64.tar.gz"' in formula
    assert 'sha256 "' + ("a" * 64) + '"' in formula
    assert 'assert_match version.to_s, shell_output("#{bin}/aiwiki-toolkit --version")' in formula
