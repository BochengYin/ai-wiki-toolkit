from __future__ import annotations

from pathlib import Path

import pytest

from ai_wiki_toolkit.release_runtime import (
    DEFAULT_DOCKER_PLATFORM,
    DEFAULT_LINUX_RUNTIME_CHECKS,
    LinuxRuntimeCheck,
    docker_run_args,
    parse_linux_runtime_check,
    verify_linux_runtime_asset,
)


def test_default_linux_runtime_checks_cover_older_and_current_baselines() -> None:
    assert DEFAULT_LINUX_RUNTIME_CHECKS == (
        LinuxRuntimeCheck(name="older-glibc", image="node:24-bookworm"),
        LinuxRuntimeCheck(name="current-glibc", image="node:24-trixie"),
    )


def test_parse_linux_runtime_check_requires_name_and_image() -> None:
    assert parse_linux_runtime_check(" older = node:24-bookworm ") == LinuxRuntimeCheck(
        name="older",
        image="node:24-bookworm",
    )

    with pytest.raises(ValueError):
        parse_linux_runtime_check("node:24-bookworm")


def test_docker_run_args_mounts_release_assets_and_runs_version() -> None:
    asset_path = Path("/tmp/release-assets/ai-wiki-toolkit-v0.1.7-linux-x64.tar.gz")

    command = docker_run_args(asset_path, DEFAULT_LINUX_RUNTIME_CHECKS[0])

    assert command[:6] == [
        "docker",
        "run",
        "--rm",
        "--platform",
        DEFAULT_DOCKER_PLATFORM,
        "-v",
    ]
    assert command[6] == f"{asset_path.parent.resolve()}:/release-assets:ro"
    assert command[7:10] == ["node:24-bookworm", "bash", "-lc"]
    assert "/release-assets/ai-wiki-toolkit-v0.1.7-linux-x64.tar.gz" in command[10]
    assert "ldd --version" in command[10]
    assert "/work/aiwiki-toolkit --version" in command[10]


def test_verify_linux_runtime_asset_runs_all_checks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    asset_path = tmp_path / "ai-wiki-toolkit-v0.1.7-linux-x64.tar.gz"
    asset_path.write_text("placeholder", encoding="utf-8")
    seen_commands: list[list[str]] = []

    def fake_run(command: list[str], *, check: bool) -> None:
        assert check is True
        seen_commands.append(command)

    monkeypatch.setattr("ai_wiki_toolkit.release_runtime.subprocess.run", fake_run)

    verify_linux_runtime_asset(asset_path)

    assert len(seen_commands) == 2
    assert seen_commands[0][7] == "node:24-bookworm"
    assert seen_commands[1][7] == "node:24-trixie"


def test_verify_linux_runtime_asset_requires_existing_archive(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.tar.gz"

    with pytest.raises(FileNotFoundError):
        verify_linux_runtime_asset(missing_path)
