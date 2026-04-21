"""Helpers for building Linux release artifacts inside a baseline container."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shlex
import subprocess

CLI_BINARY_NAME = "aiwiki-toolkit"
DEFAULT_DOCKER_PLATFORM = "linux/amd64"
DEFAULT_LINUX_BUILD_IMAGE = "python:3.11-bookworm"
DEFAULT_WORKSPACE_DIR = "/workspace"
DEFAULT_CONTAINER_HOME = "/tmp/aiwiki-release-home"


@dataclass(frozen=True)
class LinuxContainerBuildConfig:
    image: str = DEFAULT_LINUX_BUILD_IMAGE
    docker_platform: str = DEFAULT_DOCKER_PLATFORM
    shell: str = "bash"
    workspace_dir: str = DEFAULT_WORKSPACE_DIR
    container_home: str = DEFAULT_CONTAINER_HOME
    target: str = "linux-x64"
    output_dir: str = "release-assets"
    venv_dir: str = "build/linux-release-venv"
    dist_dir: str = "build/linux-release-dist"
    pyinstaller_work_dir: str = "build/linux-pyinstaller-work"
    pyinstaller_spec_dir: str = "build/linux-pyinstaller-spec"
    setup_commands: tuple[str, ...] = ()


DEFAULT_LINUX_CONTAINER_BUILD = LinuxContainerBuildConfig()


def linux_build_inner_command(version: str, config: LinuxContainerBuildConfig) -> str:
    venv_python = shlex.quote(f"{config.venv_dir}/bin/python")
    binary_path = shlex.quote(f"{config.dist_dir}/{CLI_BINARY_NAME}")
    output_dir = shlex.quote(config.output_dir)
    target = shlex.quote(config.target)
    normalized_version = shlex.quote(version)

    return "\n".join(
        [
            "set -eu",
            "mkdir -p \"$HOME\"",
            *config.setup_commands,
            f"rm -rf {shlex.quote(config.venv_dir)}",
            f"rm -rf {shlex.quote(config.dist_dir)}",
            f"rm -rf {shlex.quote(config.pyinstaller_work_dir)}",
            f"rm -rf {shlex.quote(config.pyinstaller_spec_dir)}",
            f"python -m venv {shlex.quote(config.venv_dir)}",
            f"{venv_python} -m pip install --upgrade pip",
            f"{venv_python} -m pip install '.[dev,release]'",
            f"{venv_python} -m pytest",
            (
                f"{venv_python} -m PyInstaller --clean --noconfirm --onefile "
                f"--name {CLI_BINARY_NAME} --paths src "
                f"--distpath {shlex.quote(config.dist_dir)} "
                f"--workpath {shlex.quote(config.pyinstaller_work_dir)} "
                f"--specpath {shlex.quote(config.pyinstaller_spec_dir)} "
                "src/ai_wiki_toolkit/cli.py"
            ),
            (
                f"{venv_python} scripts/build_release_archive.py "
                f"--binary {binary_path} "
                f"--version {normalized_version} "
                f"--target {target} "
                f"--output-dir {output_dir}"
            ),
        ]
    )


def docker_build_args(
    repo_root: Path,
    version: str,
    config: LinuxContainerBuildConfig = DEFAULT_LINUX_CONTAINER_BUILD,
) -> list[str]:
    return [
        "docker",
        "run",
        "--rm",
        "--platform",
        config.docker_platform,
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "-e",
        f"HOME={config.container_home}",
        "-e",
        "PIP_DISABLE_PIP_VERSION_CHECK=1",
        "-v",
        f"{repo_root.resolve()}:{config.workspace_dir}",
        "-w",
        config.workspace_dir,
        config.image,
        config.shell,
        "-lc",
        linux_build_inner_command(version, config),
    ]


def build_linux_release_archive_in_container(
    repo_root: Path,
    version: str,
    config: LinuxContainerBuildConfig = DEFAULT_LINUX_CONTAINER_BUILD,
) -> None:
    subprocess.run(docker_build_args(repo_root, version, config), check=True)
