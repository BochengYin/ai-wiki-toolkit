"""Helpers for npm meta-package and platform package distribution."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import tarfile

from ai_wiki_toolkit.release_artifacts import release_archive_path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PLATFORM_TARGETS_PATH = REPOSITORY_ROOT / "npm" / "platform-targets.json"

REPOSITORY_URL = "https://github.com/BochengYin/ai-wiki-toolkit"
REPOSITORY_BUGS_URL = f"{REPOSITORY_URL}/issues"
ROOT_PACKAGE_NAME = "ai-wiki-toolkit"


@dataclass(frozen=True)
class PlatformPackage:
    node_target: str
    package_name: str
    release_target: str
    os: tuple[str, ...]
    cpu: tuple[str, ...]
    binary_name: str


def load_platform_packages(config_path: Path = PLATFORM_TARGETS_PATH) -> tuple[PlatformPackage, ...]:
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    packages = [
        PlatformPackage(
            node_target=node_target,
            package_name=config["package_name"],
            release_target=config["release_target"],
            os=tuple(config["os"]),
            cpu=tuple(config["cpu"]),
            binary_name=config["binary_name"],
        )
        for node_target, config in raw.items()
    ]
    return tuple(sorted(packages, key=lambda package: package.package_name))


def expected_optional_dependencies(version: str) -> dict[str, str]:
    return {
        package.package_name: version for package in load_platform_packages()
    }


def render_platform_package_json(package: PlatformPackage, version: str) -> str:
    payload = {
        "name": package.package_name,
        "version": version,
        "description": f"Platform binary package for {ROOT_PACKAGE_NAME} ({package.node_target}).",
        "license": "MIT",
        "homepage": f"{REPOSITORY_URL}#readme",
        "bugs": {"url": REPOSITORY_BUGS_URL},
        "repository": {
            "type": "git",
            "url": f"git+{REPOSITORY_URL}.git",
        },
        "files": [
            f"bin/{package.binary_name}",
            "LICENSE",
            "README.md",
        ],
        "os": list(package.os),
        "cpu": list(package.cpu),
        "bin": {
            package.binary_name: f"bin/{package.binary_name}",
        },
    }
    return json.dumps(payload, indent=2) + "\n"


def render_platform_package_readme(package: PlatformPackage, version: str) -> str:
    root_readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8").strip()
    return "\n".join(
        [
            f"# {package.package_name}",
            "",
            f"This package contains the `{package.binary_name}` executable for `{package.node_target}`.",
            f"It is published as the platform-specific binary package for `{ROOT_PACKAGE_NAME}` `{version}`.",
            f"Most users should install `{ROOT_PACKAGE_NAME}` instead of using this package directly.",
            "",
            "---",
            "",
            "Below is the current root project README:",
            "",
            root_readme,
            "",
        ]
    )


def extract_release_binary(asset_path: Path, destination: Path) -> None:
    with tarfile.open(asset_path, "r:gz") as archive:
        members = [member for member in archive.getmembers() if member.isfile()]
        if len(members) != 1:
            raise ValueError(f"expected exactly one file in {asset_path}, found {len(members)}")

        member = members[0]
        extracted = archive.extractfile(member)
        if extracted is None:
            raise ValueError(f"could not extract {member.name} from {asset_path}")

        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as output:
            shutil.copyfileobj(extracted, output)

    destination.chmod(0o755)


def stage_platform_package(
    package: PlatformPackage,
    version: str,
    asset_dir: Path,
    output_root: Path,
    repository_root: Path = REPOSITORY_ROOT,
) -> Path:
    package_dir = output_root / package.package_name
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True)

    asset_path = release_archive_path(asset_dir, version, package.release_target)
    extract_release_binary(asset_path, package_dir / "bin" / package.binary_name)

    shutil.copy2(repository_root / "LICENSE", package_dir / "LICENSE")
    (package_dir / "README.md").write_text(
        render_platform_package_readme(package, version),
        encoding="utf-8",
    )
    (package_dir / "package.json").write_text(
        render_platform_package_json(package, version),
        encoding="utf-8",
    )
    return package_dir


def stage_platform_packages(
    version: str,
    asset_dir: Path,
    output_root: Path,
    repository_root: Path = REPOSITORY_ROOT,
) -> list[Path]:
    output_root.mkdir(parents=True, exist_ok=True)
    staged = []
    for package in load_platform_packages():
        staged.append(
            stage_platform_package(
                package=package,
                version=version,
                asset_dir=asset_dir,
                output_root=output_root,
                repository_root=repository_root,
            )
        )
    return staged
