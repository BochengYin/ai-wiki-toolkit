from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_release_smoke_workflow_targets_windows_11_arm() -> None:
    workflow = (ROOT / ".github" / "workflows" / "release-smoke-windows-arm.yml").read_text(
        encoding="utf-8"
    )

    assert "name: Release Smoke Windows ARM" in workflow
    assert "runs-on: windows-11-arm" in workflow
    assert "workflow_dispatch:" in workflow
    assert "Release Binaries" in workflow
    assert "Publish npm Package" in workflow


def test_release_smoke_workflow_checks_release_archive_and_npm_install() -> None:
    workflow = (ROOT / ".github" / "workflows" / "release-smoke-windows-arm.yml").read_text(
        encoding="utf-8"
    )

    assert 'gh release download "${{ steps.release.outputs.release_tag }}" --pattern "ai-wiki-toolkit-${{ steps.release.outputs.release_tag }}-windows-arm64.zip"' in workflow
    assert 'Expand-Archive -Path $archive -DestinationPath $destination' in workflow
    assert '$expected = "ai-wiki-toolkit ${{ steps.release.outputs.package_version }}"' in workflow
    assert '& "release-assets/windows-arm64/aiwiki-toolkit.exe" --version' in workflow
    assert "Expected binary version '$expected' but binary returned '$version'." in workflow
    assert 'npm install -g "ai-wiki-toolkit@$version"' in workflow
    assert '& aiwiki-toolkit --version' in workflow
    assert "Expected npm-installed version '$expected' but binary returned '$version'." in workflow
