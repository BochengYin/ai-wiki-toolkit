"""Export visible Codex session traces for one impact-eval workspace set."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil


DEFAULT_CODEX_HOME = Path.home() / ".codex"
DEFAULT_SESSIONS_ROOT = DEFAULT_CODEX_HOME / "sessions"
DEFAULT_SESSION_INDEX = DEFAULT_CODEX_HOME / "session_index.jsonl"
VISIBLE_RESPONSE_ITEM_TYPES = {"message", "function_call", "function_call_output"}


@dataclass(frozen=True)
class MatchedSession:
    session_id: str
    session_file: Path
    variant: str
    cwd: Path
    session_timestamp: str | None
    updated_at: str | None
    thread_name: str | None

    @property
    def sort_key(self) -> tuple[datetime, str]:
        return parse_timestamp(self.updated_at or self.session_timestamp), self.session_id


def parse_csv(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(",") if part.strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace-root",
        type=Path,
        required=True,
        help="Prepared impact-eval workspace root such as .../workspaces/<timestamp>/.",
    )
    parser.add_argument(
        "--match-workspace-root",
        type=Path,
        default=None,
        help="Optional workspace root to match against Codex session cwd values. Defaults to --workspace-root.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory. Defaults to <workspace-root>/codex_sessions/.",
    )
    parser.add_argument(
        "--sessions-root",
        type=Path,
        default=DEFAULT_SESSIONS_ROOT,
        help="Codex sessions root. Defaults to ~/.codex/sessions/.",
    )
    parser.add_argument(
        "--session-index",
        type=Path,
        default=DEFAULT_SESSION_INDEX,
        help="Codex session index. Defaults to ~/.codex/session_index.jsonl.",
    )
    parser.add_argument(
        "--variants",
        type=parse_csv,
        default=None,
        help="Optional comma-separated variant list. Defaults to all variant repos under the workspace root.",
    )
    parser.add_argument(
        "--all-sessions",
        action="store_true",
        help="Export every matching session instead of the latest session per variant.",
    )
    return parser.parse_args()


def parse_timestamp(value: str | None) -> datetime:
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    normalized = value.replace("Z", "+00:00") if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def discover_workspace_variants(workspace_root: Path) -> tuple[str, ...]:
    slots_root = workspace_root / "slots"
    if slots_root.exists():
        return tuple(
            sorted(
                path.name
                for path in slots_root.iterdir()
                if path.is_dir() and (path / ".git").exists()
            )
        )
    variants = sorted(
        path.name
        for path in workspace_root.iterdir()
        if path.is_dir() and (path / ".git").exists()
    )
    return tuple(variants)


def load_session_index(session_index_path: Path) -> dict[str, dict]:
    if not session_index_path.exists():
        return {}
    index: dict[str, dict] = {}
    for line in session_index_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        session_id = payload.get("id")
        if session_id:
            index[session_id] = payload
    return index


def load_session_meta(session_file: Path) -> dict:
    for line in session_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("type") == "session_meta":
            payload = record.get("payload", {})
            if not isinstance(payload, dict):
                break
            return payload
    raise ValueError(f"Could not find session_meta in {session_file}")


def load_turn_context(session_file: Path) -> dict:
    for line in session_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("type") == "turn_context":
            payload = record.get("payload", {})
            if isinstance(payload, dict):
                return payload
            return {}
    return {}


def reasoning_effort_from_turn_context(turn_context: dict) -> str | None:
    effort = turn_context.get("effort")
    if isinstance(effort, str):
        return effort
    collaboration_mode = turn_context.get("collaboration_mode", {})
    if not isinstance(collaboration_mode, dict):
        return None
    settings = collaboration_mode.get("settings", {})
    if not isinstance(settings, dict):
        return None
    effort = settings.get("reasoning_effort")
    return effort if isinstance(effort, str) else None


def variant_from_cwd(workspace_root: Path, variants: set[str], cwd: Path) -> str | None:
    try:
        relative = cwd.resolve().relative_to(workspace_root.resolve())
    except ValueError:
        return None
    if not relative.parts:
        return None
    if relative.parts[0] == "slots" and len(relative.parts) > 1:
        candidate = relative.parts[1]
        if candidate not in variants:
            return None
        return candidate
    candidate = relative.parts[0]
    if candidate not in variants:
        return None
    return candidate


def collect_matching_sessions(
    *,
    match_workspace_root: Path,
    sessions_root: Path,
    session_index: dict[str, dict],
    variants: tuple[str, ...],
) -> list[MatchedSession]:
    variants_set = set(variants)
    matches: list[MatchedSession] = []
    for session_file in sorted(sessions_root.rglob("*.jsonl")):
        try:
            session_meta = load_session_meta(session_file)
        except ValueError:
            continue
        session_id = session_meta.get("id")
        cwd_value = session_meta.get("cwd")
        if not session_id or not cwd_value:
            continue
        cwd = Path(cwd_value)
        variant = variant_from_cwd(match_workspace_root, variants_set, cwd)
        if variant is None:
            continue
        index_entry = session_index.get(session_id, {})
        matches.append(
            MatchedSession(
                session_id=session_id,
                session_file=session_file,
                variant=variant,
                cwd=cwd,
                session_timestamp=session_meta.get("timestamp"),
                updated_at=index_entry.get("updated_at"),
                thread_name=index_entry.get("thread_name"),
            )
        )
    return matches


def select_sessions(matches: list[MatchedSession], *, export_all_sessions: bool) -> list[MatchedSession]:
    if export_all_sessions:
        return sorted(matches, key=lambda match: (match.variant, *match.sort_key))

    selected: list[MatchedSession] = []
    by_variant: dict[str, list[MatchedSession]] = {}
    for match in matches:
        by_variant.setdefault(match.variant, []).append(match)
    for variant in sorted(by_variant):
        selected.append(max(by_variant[variant], key=lambda match: match.sort_key))
    return selected


def extract_message_text(payload: dict) -> str:
    parts = []
    for content_part in payload.get("content", []):
        if not isinstance(content_part, dict):
            continue
        text = content_part.get("text")
        if content_part.get("type") in {"input_text", "output_text"} and isinstance(text, str):
            parts.append(text)
    return "\n\n".join(parts).strip()


def is_instructions_message(text: str) -> bool:
    return text.startswith("# AGENTS.md instructions for ")


def load_visible_records(session_file: Path) -> list[dict]:
    visible: list[dict] = []
    for line in session_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        record_type = record.get("type")
        if record_type == "session_meta":
            visible.append(record)
            continue
        if record_type != "response_item":
            continue
        item_type = record.get("payload", {}).get("type")
        if item_type in VISIBLE_RESPONSE_ITEM_TYPES:
            visible.append(record)
    return visible


def load_session_without_reasoning(session_file: Path) -> list[dict]:
    filtered: list[dict] = []
    for line in session_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if (
            record.get("type") == "response_item"
            and record.get("payload", {}).get("type") == "reasoning"
        ):
            continue
        filtered.append(record)
    return filtered


def collect_visible_messages(visible_records: list[dict]) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for record in visible_records:
        if record.get("type") != "response_item":
            continue
        payload = record.get("payload", {})
        if payload.get("type") != "message":
            continue
        text = extract_message_text(payload)
        if not text:
            continue
        role = payload.get("role")
        if not isinstance(role, str):
            continue
        messages.append({"role": role, "text": text})
    return messages


def extract_task_prompt(messages: list[dict[str, str]]) -> str:
    for message in messages:
        if message["role"] != "user":
            continue
        text = message["text"].strip()
        if not text or is_instructions_message(text):
            continue
        return message["text"]
    return ""


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def write_jsonl(path: Path, records: list[dict]) -> None:
    lines = [json.dumps(record, ensure_ascii=False) for record in records]
    write_text(path, "\n".join(lines) + ("\n" if lines else ""))


def render_transcript(match: MatchedSession, messages: list[dict[str, str]], task_prompt: str) -> str:
    lines = [
        "# Visible Codex Transcript",
        "",
        f"- Variant: `{match.variant}`",
        f"- Session id: `{match.session_id}`",
        f"- Thread name: `{match.thread_name or 'unknown'}`",
        f"- Session file: `{match.session_file}`",
        f"- Workspace cwd: `{match.cwd}`",
        "- Hidden reasoning exported: `no`",
    ]
    if task_prompt:
        lines.extend(
            [
                "",
                "## Task Prompt",
                "",
                "```md",
                task_prompt.rstrip(),
                "```",
            ]
        )
    lines.extend(
        [
            "",
            "## Messages",
            "",
        ]
    )
    for message in messages:
        role = message["role"].title()
        lines.extend(
            [
                f"### {role}",
                "",
                message["text"].rstrip(),
                "",
            ]
        )
    lines.extend(
        [
            "## Notes",
            "",
            "This transcript keeps only visible user and assistant messages.",
            "Use `visible_session.jsonl` in the same directory for the full visible tool-call trace.",
        ]
    )
    return "\n".join(lines) + "\n"


def export_session(match: MatchedSession, output_root: Path) -> dict:
    session_meta = load_session_meta(match.session_file)
    turn_context = load_turn_context(match.session_file)
    session_without_reasoning = load_session_without_reasoning(match.session_file)
    visible_records = load_visible_records(match.session_file)
    messages = collect_visible_messages(visible_records)
    task_prompt = extract_task_prompt(messages)
    session_dir = output_root / match.variant / match.session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "session_id": match.session_id,
        "variant": match.variant,
        "thread_name": match.thread_name,
        "session_file": str(match.session_file),
        "workspace_cwd": str(match.cwd),
        "session_timestamp": match.session_timestamp,
        "updated_at": match.updated_at,
        "source": session_meta.get("source"),
        "originator": session_meta.get("originator"),
        "cli_version": session_meta.get("cli_version"),
        "model_provider": session_meta.get("model_provider"),
        "model": turn_context.get("model"),
        "reasoning_effort": reasoning_effort_from_turn_context(turn_context),
        "turn_context_cwd": turn_context.get("cwd"),
        "user_message_count": sum(1 for message in messages if message["role"] == "user"),
        "assistant_message_count": sum(1 for message in messages if message["role"] == "assistant"),
        "tool_call_count": sum(
            1
            for record in visible_records
            if record.get("type") == "response_item"
            and record.get("payload", {}).get("type") == "function_call"
        ),
        "tool_output_count": sum(
            1
            for record in visible_records
            if record.get("type") == "response_item"
            and record.get("payload", {}).get("type") == "function_call_output"
        ),
        "task_prompt_present": bool(task_prompt),
        "hidden_reasoning_exported": False,
    }
    write_json(session_dir / "metadata.json", metadata)
    write_text(session_dir / "prompt.md", task_prompt.rstrip() + ("\n" if task_prompt else ""))
    write_jsonl(session_dir / "session_without_reasoning.jsonl", session_without_reasoning)
    write_jsonl(session_dir / "visible_session.jsonl", visible_records)
    write_text(session_dir / "visible_transcript.md", render_transcript(match, messages, task_prompt))
    return metadata


def render_output_readme(manifest: dict) -> str:
    variants = ", ".join(manifest["variants"])
    missing = ", ".join(manifest["missing_variants"]) if manifest["missing_variants"] else "none"
    selection = "all matching sessions" if manifest["all_sessions"] else "latest session per variant"
    return (
        "# Codex Session Export\n\n"
        f"- Workspace root: `{manifest['workspace_root']}`\n"
        f"- Sessions root: `{manifest['sessions_root']}`\n"
        f"- Exported at: `{manifest['exported_at']}`\n"
        f"- Variants: `{variants}`\n"
        f"- Selection mode: `{selection}`\n"
        f"- Missing variants: `{missing}`\n"
        "- Hidden reasoning exported: `no`\n\n"
        "Per-session directories contain:\n\n"
        "- `metadata.json`\n"
        "- `prompt.md`\n"
        "- `session_without_reasoning.jsonl`\n"
        "- `visible_session.jsonl`\n"
        "- `visible_transcript.md`\n"
        "\n"
        "`metadata.json` includes the observed session source, model, and reasoning effort when "
        "those fields are available in the local Codex session trace.\n"
    )


def export_workspace_sessions(
    *,
    workspace_root: Path,
    output_root: Path,
    sessions_root: Path,
    session_index_path: Path,
    match_workspace_root: Path | None = None,
    variants: tuple[str, ...] | None = None,
    export_all_sessions: bool = False,
) -> dict:
    workspace_root = workspace_root.resolve()
    output_root = output_root.resolve()
    sessions_root = sessions_root.expanduser().resolve()
    session_index_path = session_index_path.expanduser().resolve()
    match_workspace_root = (match_workspace_root or workspace_root).resolve()

    variants = variants or discover_workspace_variants(workspace_root)
    session_index = load_session_index(session_index_path)
    matches = collect_matching_sessions(
        match_workspace_root=match_workspace_root,
        sessions_root=sessions_root,
        session_index=session_index,
        variants=variants,
    )
    selected = select_sessions(matches, export_all_sessions=export_all_sessions)

    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    exported_sessions = [export_session(match, output_root) for match in selected]
    exported_variants = {session["variant"] for session in exported_sessions}
    manifest = {
        "workspace_root": str(workspace_root),
        "match_workspace_root": str(match_workspace_root),
        "output_root": str(output_root),
        "sessions_root": str(sessions_root),
        "session_index": str(session_index_path),
        "variants": list(variants),
        "all_sessions": export_all_sessions,
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "exported_session_count": len(exported_sessions),
        "missing_variants": [variant for variant in variants if variant not in exported_variants],
        "sessions": exported_sessions,
    }
    write_json(output_root / "manifest.json", manifest)
    write_text(output_root / "README.md", render_output_readme(manifest))
    return manifest


def main() -> None:
    args = parse_args()
    workspace_root = args.workspace_root.resolve()
    if not workspace_root.exists():
        raise SystemExit(f"Workspace root does not exist: {workspace_root}")

    sessions_root = args.sessions_root.expanduser().resolve()
    if not sessions_root.exists():
        raise SystemExit(f"Codex sessions root does not exist: {sessions_root}")

    output_root = (args.output_dir or (workspace_root / "codex_sessions")).resolve()
    variants = args.variants
    if variants is None:
        variants = discover_workspace_variants(workspace_root)
    if not variants:
        raise SystemExit(f"No workspace variants found under: {workspace_root}")

    manifest = export_workspace_sessions(
        workspace_root=workspace_root,
        output_root=output_root,
        sessions_root=sessions_root,
        session_index_path=args.session_index,
        match_workspace_root=args.match_workspace_root,
        variants=variants,
        export_all_sessions=args.all_sessions,
    )
    print(output_root)
    print(f"Exported sessions: {manifest['exported_session_count']}")
    if manifest["missing_variants"]:
        print(f"Missing variants: {', '.join(manifest['missing_variants'])}")


if __name__ == "__main__":
    main()
