"""Helpers for runtime verification of Linux release artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shlex
import subprocess

CLI_BINARY_NAME = "aiwiki-toolkit"
DEFAULT_DOCKER_PLATFORM = "linux/amd64"


@dataclass(frozen=True)
class LinuxRuntimeCheck:
    name: str
    image: str


DEFAULT_LINUX_RUNTIME_CHECKS = (
    LinuxRuntimeCheck(name="older-glibc", image="node:24-bookworm"),
    LinuxRuntimeCheck(name="current-glibc", image="node:24-trixie"),
)


def parse_linux_runtime_check(value: str) -> LinuxRuntimeCheck:
    name, separator, image = value.partition("=")
    normalized_name = name.strip()
    normalized_image = image.strip()
    if not separator or not normalized_name or not normalized_image:
        raise ValueError("runtime checks must look like <name>=<docker-image>")
    return LinuxRuntimeCheck(name=normalized_name, image=normalized_image)


def linux_runtime_inner_command(asset_name: str) -> str:
    archive_path = shlex.quote(f"/release-assets/{asset_name}")
    binary_path = shlex.quote(f"/work/{CLI_BINARY_NAME}")
    return "\n".join(
        [
            "set -eu",
            "mkdir -p /work",
            f"tar -xzf {archive_path} -C /work",
            "ldd --version | head -n1",
            f"{binary_path} --version",
        ]
    )


def docker_run_args(
    asset_path: Path,
    check: LinuxRuntimeCheck,
    *,
    docker_platform: str = DEFAULT_DOCKER_PLATFORM,
) -> list[str]:
    return [
        "docker",
        "run",
        "--rm",
        "--platform",
        docker_platform,
        "-v",
        f"{asset_path.parent.resolve()}:/release-assets:ro",
        check.image,
        "bash",
        "-lc",
        linux_runtime_inner_command(asset_path.name),
    ]


def verify_linux_runtime_asset(
    asset_path: Path,
    *,
    checks: tuple[LinuxRuntimeCheck, ...] = DEFAULT_LINUX_RUNTIME_CHECKS,
    docker_platform: str = DEFAULT_DOCKER_PLATFORM,
) -> None:
    if not asset_path.exists():
        raise FileNotFoundError(f"Linux release asset does not exist: {asset_path}")

    for check in checks:
        print(f"Checking {check.name} runtime with {check.image}", flush=True)
        subprocess.run(
            docker_run_args(asset_path, check, docker_platform=docker_platform),
            check=True,
        )
