from __future__ import annotations

from pathlib import Path

import pytest

from ai_wiki_toolkit.release_build import (
    DEFAULT_DOCKER_PLATFORM,
    DEFAULT_LINUX_BUILD_IMAGE,
    DEFAULT_LINUX_CONTAINER_BUILD,
    LinuxContainerBuildConfig,
    build_linux_release_archive_in_container,
    docker_build_args,
    linux_build_inner_command,
)


def test_default_linux_container_build_targets_bookworm() -> None:
    assert DEFAULT_LINUX_CONTAINER_BUILD == LinuxContainerBuildConfig(
        image=DEFAULT_LINUX_BUILD_IMAGE,
        docker_platform=DEFAULT_DOCKER_PLATFORM,
    )


def test_linux_build_inner_command_runs_tests_and_packages_archive() -> None:
    command = linux_build_inner_command("v0.1.7", DEFAULT_LINUX_CONTAINER_BUILD)

    assert "python -m venv build/linux-release-venv" in command
    assert "build/linux-release-venv/bin/python -m pytest" in command
    assert "--distpath build/linux-release-dist" in command
    assert "--version v0.1.7" in command
    assert "--target linux-x64" in command
    assert "--output-dir release-assets" in command


def test_docker_build_args_mount_repo_and_use_bookworm_image() -> None:
    repo_root = Path("/tmp/repo root")

    command = docker_build_args(repo_root, "0.1.7")

    assert command[:5] == [
        "docker",
        "run",
        "--rm",
        "--platform",
        DEFAULT_DOCKER_PLATFORM,
    ]
    assert f"{repo_root.resolve()}:/workspace" in command
    assert "PIP_DISABLE_PIP_VERSION_CHECK=1" in command
    assert DEFAULT_LINUX_BUILD_IMAGE in command
    image_index = command.index(DEFAULT_LINUX_BUILD_IMAGE)
    assert command[image_index + 1 : image_index + 3] == [
        DEFAULT_LINUX_CONTAINER_BUILD.shell,
        "-lc",
    ]
    assert "build/linux-release-venv/bin/python -m pytest" in command[image_index + 3]


def test_linux_build_inner_command_supports_custom_target_and_setup_commands() -> None:
    config = LinuxContainerBuildConfig(
        image="python:3.11-alpine",
        docker_platform="linux/amd64",
        shell="sh",
        target="linux-musl-x64",
        setup_commands=("echo preparing-musl",),
    )

    command = linux_build_inner_command("v0.1.7", config)

    assert "echo preparing-musl" in command
    assert "--target linux-musl-x64" in command


def test_build_linux_release_archive_in_container_runs_docker(monkeypatch: pytest.MonkeyPatch) -> None:
    seen_commands: list[list[str]] = []

    def fake_run(command: list[str], *, check: bool) -> None:
        assert check is True
        seen_commands.append(command)

    monkeypatch.setattr("ai_wiki_toolkit.release_build.subprocess.run", fake_run)

    build_linux_release_archive_in_container(Path("/tmp/repo"), "v0.1.7")

    assert len(seen_commands) == 1
    assert seen_commands[0][0:2] == ["docker", "run"]


def test_docker_build_args_omits_user_flag_without_posix_uid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delattr("os.getuid", raising=False)
    monkeypatch.delattr("os.getgid", raising=False)

    command = docker_build_args(Path("/tmp/repo"), "0.1.7")

    assert "--user" not in command
