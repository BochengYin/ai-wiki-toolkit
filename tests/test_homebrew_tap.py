from __future__ import annotations

from pathlib import Path

from ai_wiki_toolkit.homebrew_tap import (
    default_tap_repository,
    release_commit_message,
    sync_formula_into_tap,
    tap_formula_path,
)


def test_default_tap_repository_uses_owner_namespace() -> None:
    assert default_tap_repository("BochengYin") == "BochengYin/homebrew-tap"


def test_tap_formula_path_uses_formula_subdirectory(tmp_path: Path) -> None:
    assert tap_formula_path(tmp_path) == tmp_path / "Formula" / "aiwiki-toolkit.rb"


def test_release_commit_message_is_stable() -> None:
    assert release_commit_message("v0.1.0") == "Update aiwiki-toolkit to v0.1.0"


def test_sync_formula_into_tap_writes_formula_and_reports_change(tmp_path: Path) -> None:
    result = sync_formula_into_tap("class AiwikiToolkit < Formula\nend\n", tmp_path)

    assert result.changed is True
    assert result.formula_path == tmp_path / "Formula" / "aiwiki-toolkit.rb"
    assert result.formula_path.read_text(encoding="utf-8") == "class AiwikiToolkit < Formula\nend\n"


def test_sync_formula_into_tap_is_noop_when_content_matches(tmp_path: Path) -> None:
    formula_path = tmp_path / "Formula" / "aiwiki-toolkit.rb"
    formula_path.parent.mkdir(parents=True)
    formula_path.write_text("same\n", encoding="utf-8")

    result = sync_formula_into_tap("same\n", tmp_path)

    assert result.changed is False
