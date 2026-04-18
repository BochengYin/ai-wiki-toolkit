from __future__ import annotations

import json
from pathlib import Path

from ai_wiki_toolkit.opencode import remove_opencode_config, upsert_opencode_config


def test_upsert_opencode_creates_file_with_namespaced_key(tmp_path: Path) -> None:
    path = tmp_path / "opencode.json"

    result = upsert_opencode_config(path)

    assert path.exists()
    assert result["aiwikiToolkit"]["schemaVersion"] == 1
    assert result["aiwikiToolkit"]["managedBy"] == "ai-wiki-toolkit"


def test_upsert_opencode_updates_namespaced_key_only(tmp_path: Path) -> None:
    path = tmp_path / "opencode.json"
    path.write_text(
        json.dumps(
            {
                "otherTool": {"enabled": True},
                "aiwikiToolkit": {"schemaVersion": 0, "keepMe": "yes"},
            }
        ),
        encoding="utf-8",
    )

    updated = upsert_opencode_config(path, {"schemaVersion": 2, "newField": "value"})

    assert updated["otherTool"] == {"enabled": True}
    assert updated["aiwikiToolkit"] == {
        "schemaVersion": 2,
        "managedBy": "ai-wiki-toolkit",
        "keepMe": "yes",
        "newField": "value",
    }

    written = json.loads(path.read_text(encoding="utf-8"))
    assert written["otherTool"] == {"enabled": True}


def test_upsert_opencode_currently_reformats_json_text(tmp_path: Path) -> None:
    path = tmp_path / "opencode.json"
    original = '{"otherTool":{"enabled":true},"aiwikiToolkit":{"schemaVersion":0}}\n'
    path.write_text(original, encoding="utf-8")

    upsert_opencode_config(path, {"schemaVersion": 2})

    updated_text = path.read_text(encoding="utf-8")
    assert updated_text != original
    assert updated_text.startswith("{\n  \"otherTool\"")


def test_remove_opencode_removes_namespaced_key_and_preserves_other_fields(
    tmp_path: Path,
) -> None:
    path = tmp_path / "opencode.json"
    path.write_text(
        json.dumps(
            {
                "otherTool": {"enabled": True},
                "aiwikiToolkit": {"schemaVersion": 1},
            }
        ),
        encoding="utf-8",
    )

    result = remove_opencode_config(path)

    assert result == {"otherTool": {"enabled": True}}
    assert json.loads(path.read_text(encoding="utf-8")) == {"otherTool": {"enabled": True}}


def test_remove_opencode_deletes_file_when_only_toolkit_key_exists(tmp_path: Path) -> None:
    path = tmp_path / "opencode.json"
    path.write_text(json.dumps({"aiwikiToolkit": {"schemaVersion": 1}}), encoding="utf-8")

    result = remove_opencode_config(path)

    assert result == {}
    assert not path.exists()
