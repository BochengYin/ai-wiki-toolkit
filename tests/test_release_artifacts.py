from __future__ import annotations

from pathlib import Path

from ai_wiki_toolkit.release_artifacts import (
    archive_extension,
    binary_filename,
    normalized_version,
    release_archive_name,
    release_archive_path,
)


def test_normalized_version_adds_v_prefix() -> None:
    assert normalized_version("0.1.0") == "v0.1.0"


def test_normalized_version_preserves_existing_prefix() -> None:
    assert normalized_version("v0.1.0") == "v0.1.0"


def test_binary_filename_uses_exe_for_windows() -> None:
    assert binary_filename("windows-x64") == "aiwiki-toolkit.exe"


def test_binary_filename_uses_plain_name_for_unix() -> None:
    assert binary_filename("linux-x64") == "aiwiki-toolkit"
    assert binary_filename("macos-arm64") == "aiwiki-toolkit"


def test_archive_extension_matches_target_family() -> None:
    assert archive_extension("windows-x64") == "zip"
    assert archive_extension("linux-x64") == "tar.gz"


def test_release_archive_name_is_stable() -> None:
    assert (
        release_archive_name("0.1.0", "macos-arm64")
        == "ai-wiki-toolkit-v0.1.0-macos-arm64.tar.gz"
    )


def test_release_archive_path_joins_output_dir() -> None:
    output_dir = Path("release-assets")
    assert release_archive_path(output_dir, "v0.1.0", "windows-x64") == (
        output_dir / "ai-wiki-toolkit-v0.1.0-windows-x64.zip"
    )
