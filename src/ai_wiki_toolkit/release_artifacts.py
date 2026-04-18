"""Helpers for naming and packaging release artifacts."""

from __future__ import annotations

from pathlib import Path

REPOSITORY_NAME = "ai-wiki-toolkit"
CLI_BINARY_NAME = "aiwiki-toolkit"

WINDOWS_TARGET_PREFIX = "windows-"


def normalized_version(version: str) -> str:
    value = version.strip()
    if not value:
        raise ValueError("version must not be empty")
    return value if value.startswith("v") else f"v{value}"


def binary_filename(target: str) -> str:
    if target.startswith(WINDOWS_TARGET_PREFIX):
        return f"{CLI_BINARY_NAME}.exe"
    return CLI_BINARY_NAME


def archive_extension(target: str) -> str:
    if target.startswith(WINDOWS_TARGET_PREFIX):
        return "zip"
    return "tar.gz"


def release_archive_name(version: str, target: str) -> str:
    return f"{REPOSITORY_NAME}-{normalized_version(version)}-{target}.{archive_extension(target)}"


def release_archive_path(output_dir: Path, version: str, target: str) -> Path:
    return output_dir / release_archive_name(version, target)
