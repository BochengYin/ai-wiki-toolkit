"""Validate CLI-first v2 impact-eval artifacts for shareable claims."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True, help="Run directory created by init_run.py.")
    parser.add_argument(
        "--session-export-root",
        type=Path,
        default=None,
        help="Codex session export root. Defaults to <workspace_root>/codex_sessions.",
    )
    return parser.parse_args()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def metadata_slots(metadata: dict) -> list[dict[str, str]]:
    assignment = metadata.get("assignment")
    if isinstance(assignment, dict) and assignment.get("slots"):
        return [
            {
                "slot": item["slot"],
                "variant": item.get("variant", item["slot"]),
            }
            for item in assignment["slots"]
        ]
    return [{"slot": variant, "variant": variant} for variant in metadata.get("variants", [])]


def default_session_export_root(metadata: dict) -> Path:
    workspace_root = metadata.get("workspace_root")
    if not workspace_root:
        raise SystemExit("metadata.json does not contain workspace_root")
    return Path(workspace_root) / "codex_sessions"


def session_metadata_paths(session_export_root: Path) -> list[Path]:
    if not session_export_root.exists():
        return []
    return sorted(session_export_root.glob("*/*/metadata.json"))


def prompt_paths(session_export_root: Path) -> list[Path]:
    if not session_export_root.exists():
        return []
    return sorted(session_export_root.glob("*/*/prompt.md"))


def transcript_paths(session_export_root: Path) -> list[Path]:
    if not session_export_root.exists():
        return []
    return sorted(session_export_root.glob("*/*/visible_transcript.md"))


def add_critical(confounds: list[dict], kind: str, detail: str, *, slot: str | None = None) -> None:
    item = {"kind": kind, "detail": detail}
    if slot is not None:
        item["slot"] = slot
    confounds.append(item)


def load_session_manifest(session_export_root: Path, critical_confounds: list[dict]) -> dict | None:
    manifest_path = session_export_root / "manifest.json"
    if not manifest_path.exists():
        add_critical(
            critical_confounds,
            "missing_session_manifest",
            f"No Codex session manifest found at {manifest_path}.",
        )
        return None
    try:
        return read_json(manifest_path)
    except json.JSONDecodeError as exc:
        add_critical(
            critical_confounds,
            "invalid_session_manifest",
            f"Could not parse Codex session manifest {manifest_path}: {exc}.",
        )
        return None


def validate_session_manifest(
    manifest: dict | None,
    slots: list[dict[str, str]],
    critical_confounds: list[dict],
    warnings: list[dict],
) -> None:
    if manifest is None:
        return
    slot_names = {item["slot"] for item in slots}
    manifest_variants = set(manifest.get("variants", []))
    for slot in sorted(slot_names - manifest_variants):
        add_critical(
            critical_confounds,
            "missing_slot_in_session_manifest",
            f"Session manifest does not list expected slot {slot}.",
            slot=slot,
        )
    for slot in manifest.get("missing_variants", []):
        add_critical(
            critical_confounds,
            "missing_session_export",
            f"Session manifest reports no exported Codex session for slot {slot}.",
            slot=slot,
        )
    exported_count = manifest.get("exported_session_count")
    if isinstance(exported_count, int) and exported_count < len(slots):
        add_critical(
            critical_confounds,
            "incomplete_session_manifest",
            f"Session manifest exported {exported_count} sessions for {len(slots)} expected slots.",
        )
    if not manifest.get("sessions"):
        warnings.append(
            {
                "kind": "empty_session_manifest",
                "detail": "Session manifest does not contain per-session metadata.",
            }
        )


def validate_session_execution_metadata(
    *,
    session_meta: dict,
    metadata: dict,
    critical_confounds: list[dict],
    slot: str,
) -> None:
    expected_surface = metadata.get("execution_surface")
    if expected_surface == "codex-cli" and session_meta.get("source") != "exec":
        add_critical(
            critical_confounds,
            "execution_surface_mismatch",
            (
                "Expected Codex CLI session source `exec`, "
                f"found `{session_meta.get('source')}`."
            ),
            slot=slot,
        )

    expected_model = metadata.get("model_family")
    if expected_model and session_meta.get("model") != expected_model:
        add_critical(
            critical_confounds,
            "model_mismatch",
            f"Expected model `{expected_model}`, found `{session_meta.get('model')}`.",
            slot=slot,
        )

    expected_effort = metadata.get("reasoning_effort")
    if expected_effort and session_meta.get("reasoning_effort") != expected_effort:
        add_critical(
            critical_confounds,
            "reasoning_effort_mismatch",
            (
                f"Expected reasoning effort `{expected_effort}`, "
                f"found `{session_meta.get('reasoning_effort')}`."
            ),
            slot=slot,
        )


def validate_run(run_dir: Path, session_export_root: Path | None = None) -> dict:
    run_dir = run_dir.resolve()
    metadata_path = run_dir / "metadata.json"
    if not metadata_path.exists():
        raise SystemExit(f"metadata.json not found under: {run_dir}")
    metadata = read_json(metadata_path)
    session_export_root = (session_export_root or default_session_export_root(metadata)).resolve()

    critical_confounds: list[dict] = []
    warnings: list[dict] = []
    slots = metadata_slots(metadata)
    semantic_variant_names = {item["variant"] for item in slots}
    manifest = load_session_manifest(session_export_root, critical_confounds)
    validate_session_manifest(manifest, slots, critical_confounds, warnings)

    for item in slots:
        slot = item["slot"]
        if not (session_export_root / slot).exists():
            add_critical(
                critical_confounds,
                "missing_session_export",
                f"No exported Codex session directory found for slot {slot}.",
                slot=slot,
            )

    seen_sessions: dict[str, str] = {}
    for meta_path in session_metadata_paths(session_export_root):
        session_meta = read_json(meta_path)
        session_id = session_meta.get("session_id")
        slot = session_meta.get("variant", meta_path.parent.parent.name)
        if session_id in seen_sessions:
            add_critical(
                critical_confounds,
                "session_reuse",
                f"Session {session_id} appears in both {seen_sessions[session_id]} and {slot}.",
                slot=slot,
            )
        elif session_id:
            seen_sessions[session_id] = slot

        validate_session_execution_metadata(
            session_meta=session_meta,
            metadata=metadata,
            critical_confounds=critical_confounds,
            slot=slot,
        )

        workspace_cwd = session_meta.get("workspace_cwd", "")
        for variant in semantic_variant_names:
            if variant and variant in workspace_cwd:
                add_critical(
                    critical_confounds,
                    "semantic_path_leak",
                    f"Workspace cwd exposes semantic variant name {variant}.",
                    slot=slot,
                )

    for transcript_path in transcript_paths(session_export_root):
        text = transcript_path.read_text(encoding="utf-8")
        slot = transcript_path.parent.parent.name
        for variant in semantic_variant_names:
            if variant and variant in text:
                add_critical(
                    critical_confounds,
                    "semantic_path_leak",
                    f"Visible transcript exposes semantic variant name {variant}.",
                    slot=slot,
                )

    expected_prompt_hashes = set(metadata.get("prompt_hashes", {}).values())
    if expected_prompt_hashes:
        for prompt_path in prompt_paths(session_export_root):
            actual = sha256_text(prompt_path.read_text(encoding="utf-8"))
            if actual not in expected_prompt_hashes:
                add_critical(
                    critical_confounds,
                    "prompt_mismatch",
                    f"Exported prompt hash does not match any expected prompt hash: {prompt_path}.",
                    slot=prompt_path.parent.parent.name,
                )
    else:
        warnings.append({"kind": "missing_expected_prompt_hashes", "detail": "No prompt_hashes in metadata."})

    result = {
        "schema_version": 2,
        "validated_at": datetime.now().isoformat(timespec="seconds"),
        "run_dir": str(run_dir),
        "session_export_root": str(session_export_root),
        "shareable_for_causal_claims": not critical_confounds,
        "critical_confounds": critical_confounds,
        "warnings": warnings,
    }
    write_json(run_dir / "confounds.json", result)
    return result


def main() -> None:
    args = parse_args()
    result = validate_run(args.run_dir, args.session_export_root)
    print(args.run_dir / "confounds.json")
    if result["critical_confounds"]:
        print(f"Critical confounds: {len(result['critical_confounds'])}")


if __name__ == "__main__":
    main()
