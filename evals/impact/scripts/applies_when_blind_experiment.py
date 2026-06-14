"""Run the blinded applies_when route-quality experiment.

The experiment keeps the router, route traces, and route-quality labels fixed. The
only treatment variable is a metadata overlay that adds stage-aware routing hints
generated from original write-back sessions.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any

from ai_wiki_toolkit.frontmatter import parse_frontmatter, replace_frontmatter
from ai_wiki_toolkit.impact_analysis import generate_route_replay_report


DEFAULT_EXPERIMENT_DIR = Path("evals/impact/experiments/applies_when_blind_2026_06")
DEFAULT_REPLAY_REPORT = Path("evals/impact/reports/route-research-2026-06-04/historical_route_replay_2026-06-04.json")
DEFAULT_BEFORE = "2026-06-04T08:20:53+10:00"
DEFAULT_TARGET_COUNT = 20
DEFAULT_HANDLE = "bochengyin"
DEFAULT_MAX_DOCS = 6
DEFAULT_RERANK_TOP = 20
DEFAULT_BUDGET_WORDS = 3000
TRANSCRIPT_CHAR_LIMIT = 24000

LABEL_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["doc_id", "label_status", "applies_when", "routing_hint", "rationale"],
    "properties": {
        "doc_id": {"type": "string"},
        "label_status": {"type": "string", "enum": ["labeled", "insufficient_source"]},
        "applies_when": {"type": "string"},
        "routing_hint": {"type": "string"},
        "rationale": {"type": "string"},
    },
}

FORBIDDEN_LABEL_FRAGMENTS = (
    "false positive",
    "false-positive",
    "selected_not_helpful",
    "missed_useful",
    "route_false_positive_research_2026-06-04",
    "precision 0.350",
    "noise 0.650",
    "57-trace",
    "57 trace",
    "answer key",
)


def resolve_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists() and (candidate / "pyproject.toml").exists():
            return candidate
    raise RuntimeError("Could not find the ai-wiki-toolkit repository root.")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_ts(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip().replace("Z", "+00:00")
    if re.search(r"[+-]\d{4}$", raw):
        raw = f"{raw[:-5]}{raw[-5:-2]}:{raw[-2:]}"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def doc_relpath(doc_id: str) -> str:
    return f"ai-wiki/{doc_id}.md"


def selected_doc_counts(replay_report: dict[str, Any]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for item in replay_report.get("items", []):
        if not isinstance(item, dict):
            continue
        replay = item.get("replay")
        if not isinstance(replay, dict):
            continue
        selected = replay.get("selected_doc_ids")
        if isinstance(selected, list):
            counts.update(str(doc_id) for doc_id in selected if isinstance(doc_id, str))
    return counts


def load_source_incidents(repo_root: Path, handle: str) -> dict[str, list[dict[str, Any]]]:
    path = repo_root / "ai-wiki" / "metrics" / "source-incidents" / f"{handle}.jsonl"
    by_doc: dict[str, list[dict[str, Any]]] = {}
    if not path.exists():
        return by_doc
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        doc_id = row.get("doc_id")
        if isinstance(doc_id, str) and doc_id:
            by_doc.setdefault(doc_id, []).append(row)
    for rows in by_doc.values():
        rows.sort(key=lambda row: str(row.get("cutoff_timestamp") or row.get("recorded_at") or ""))
    return by_doc


def session_id_from_rollout(path: Path) -> str | None:
    match = re.search(r"rollout-[^-]+-[^-]+-[^-]+-([0-9a-f-]{36})\.jsonl$", path.name)
    if match:
        return match.group(1)
    match = re.search(r"([0-9a-f]{8}-[0-9a-f-]{27})", path.name)
    return match.group(1) if match else None


def text_from_assistant_record(record: dict[str, Any]) -> str:
    payload = record.get("payload")
    if not isinstance(payload, dict):
        return ""
    if record.get("type") == "event_msg" and payload.get("type") == "agent_message":
        message = payload.get("message")
        return message if isinstance(message, str) else ""
    if record.get("type") != "response_item" or payload.get("type") != "message":
        return ""
    if payload.get("role") != "assistant":
        return ""
    chunks: list[str] = []
    for item in payload.get("content", []):
        if isinstance(item, dict) and isinstance(item.get("text"), str):
            chunks.append(item["text"])
    return "\n".join(chunks)


def scan_rollouts_for_writebacks(
    *,
    doc_ids: list[str],
    sessions_root: Path,
) -> dict[str, list[dict[str, Any]]]:
    wanted = {
        doc_id: (
            f"AI Wiki Write-Back Path: {doc_relpath(doc_id)}",
            f"AI Wiki Update Path: {doc_relpath(doc_id)}",
        )
        for doc_id in doc_ids
    }
    matches: dict[str, list[dict[str, Any]]] = {doc_id: [] for doc_id in doc_ids}
    if not sessions_root.exists():
        return matches

    for rollout_path in sorted(sessions_root.rglob("rollout-*.jsonl")):
        try:
            lines = rollout_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line_number, line in enumerate(lines, start=1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = text_from_assistant_record(record)
            if not text:
                continue
            for doc_id, needles in wanted.items():
                if any(needle in text for needle in needles):
                    matches[doc_id].append(
                        {
                            "session_file": str(rollout_path),
                            "session_id": session_id_from_rollout(rollout_path),
                            "timestamp": record.get("timestamp"),
                            "line_number": line_number,
                            "match_kind": "assistant_footer",
                        }
                    )
    return matches


def previous_user_timestamp(session_path: Path, cutoff: datetime | None) -> str | None:
    if cutoff is None or not session_path.exists():
        return None
    selected: str | None = None
    try:
        lines = session_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = parse_ts(record.get("timestamp"))
        if ts is None or ts > cutoff:
            continue
        payload = record.get("payload")
        if (
            record.get("type") == "event_msg"
            and isinstance(payload, dict)
            and payload.get("type") == "user_message"
        ):
            selected = record.get("timestamp") if isinstance(record.get("timestamp"), str) else None
    return selected


def recover_sources(
    *,
    repo_root: Path,
    doc_ids: list[str],
    sessions_root: Path,
    handle: str,
) -> list[dict[str, Any]]:
    source_incidents = load_source_incidents(repo_root, handle)
    footer_matches = scan_rollouts_for_writebacks(doc_ids=doc_ids, sessions_root=sessions_root)
    rows: list[dict[str, Any]] = []
    for rank, doc_id in enumerate(doc_ids, start=1):
        incident_rows = source_incidents.get(doc_id, [])
        if incident_rows:
            source = incident_rows[0]
            session_relpath = source.get("session_relpath")
            session_file = (
                sessions_root / session_relpath
                if isinstance(session_relpath, str)
                else sessions_root / str(source.get("session_file") or "")
            )
            status = "source_incident_exact" if session_file.exists() else "source_incident_missing_session"
            rows.append(
                {
                    "rank": rank,
                    "doc_id": doc_id,
                    "writeback_path": source.get("writeback_path") or doc_relpath(doc_id),
                    "recovery_status": status,
                    "source_kind": "source_incident",
                    "session_file": str(session_file),
                    "session_id": source.get("session_id"),
                    "source_task_start_timestamp": source.get("source_task_start_timestamp"),
                    "first_writeback_at": source.get("cutoff_timestamp"),
                    "cutoff_timestamp": source.get("cutoff_timestamp"),
                }
            )
            continue

        matches = footer_matches.get(doc_id, [])
        if matches:
            match = sorted(matches, key=lambda item: str(item.get("timestamp") or ""))[0]
            session_file = Path(str(match["session_file"]))
            cutoff = parse_ts(match.get("timestamp"))
            rows.append(
                {
                    "rank": rank,
                    "doc_id": doc_id,
                    "writeback_path": doc_relpath(doc_id),
                    "recovery_status": "exact_footer_match",
                    "source_kind": "codex_footer_scan",
                    "session_file": str(session_file),
                    "session_id": match.get("session_id"),
                    "source_task_start_timestamp": previous_user_timestamp(session_file, cutoff),
                    "first_writeback_at": match.get("timestamp"),
                    "cutoff_timestamp": match.get("timestamp"),
                    "match_count": len(matches),
                }
            )
            continue

        rows.append(
            {
                "rank": rank,
                "doc_id": doc_id,
                "writeback_path": doc_relpath(doc_id),
                "recovery_status": "not_found",
                "source_kind": None,
                "session_file": None,
                "session_id": None,
                "source_task_start_timestamp": None,
                "first_writeback_at": None,
                "cutoff_timestamp": None,
            }
        )
    return rows


def trim_text(value: str, *, limit: int = 1800) -> str:
    if len(value) <= limit:
        return value
    head = max(0, limit // 2)
    tail = max(0, limit - head - 80)
    return f"{value[:head].rstrip()}\n\n[... trimmed {len(value) - head - tail} chars ...]\n\n{value[-tail:].lstrip()}"


def format_record(record: dict[str, Any]) -> str | None:
    payload = record.get("payload")
    if not isinstance(payload, dict):
        return None
    timestamp = str(record.get("timestamp") or "")
    if record.get("type") == "event_msg" and payload.get("type") == "user_message":
        message = payload.get("message")
        if isinstance(message, str) and message.strip():
            return f"### User Message ({timestamp})\n\n{trim_text(message, limit=2600)}"
    if record.get("type") == "event_msg" and payload.get("type") == "agent_message":
        message = payload.get("message")
        if isinstance(message, str) and message.strip():
            phase = payload.get("phase") if isinstance(payload.get("phase"), str) else "assistant"
            return f"### Assistant {phase} ({timestamp})\n\n{trim_text(message, limit=1800)}"
    if record.get("type") != "response_item":
        return None
    if payload.get("type") == "function_call":
        name = payload.get("name")
        raw_args = payload.get("arguments")
        args: dict[str, Any] = {}
        if isinstance(raw_args, str):
            try:
                args = json.loads(raw_args)
            except json.JSONDecodeError:
                args = {}
        elif isinstance(raw_args, dict):
            args = raw_args
        if name == "exec_command":
            cmd = args.get("cmd")
            workdir = args.get("workdir")
            if isinstance(cmd, str):
                body = f"cmd: {cmd}"
                if isinstance(workdir, str):
                    body += f"\nworkdir: {workdir}"
                return f"### Tool Call ({timestamp})\n\n```text\n{trim_text(body, limit=1800)}\n```"
        return f"### Tool Call ({timestamp})\n\n```text\n{name}\n```"
    if payload.get("type") == "function_call_output":
        output = payload.get("output")
        if isinstance(output, str) and output.strip():
            return f"### Tool Output ({timestamp})\n\n```text\n{trim_text(output, limit=2200)}\n```"
    return None


def transcript_excerpt(
    *,
    session_file: Path,
    start_timestamp: str | None,
    cutoff_timestamp: str | None,
) -> str:
    start = parse_ts(start_timestamp)
    cutoff = parse_ts(cutoff_timestamp)
    if not session_file.exists() or cutoff is None:
        return ""
    chunks: list[str] = []
    try:
        lines = session_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""
    recent_before_cutoff: list[dict[str, Any]] = []
    for line in lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = parse_ts(record.get("timestamp"))
        if ts is None or ts > cutoff:
            continue
        if start is not None and ts < start:
            continue
        if start is None:
            recent_before_cutoff.append(record)
            recent_before_cutoff = recent_before_cutoff[-120:]
            continue
        formatted = format_record(record)
        if formatted:
            chunks.append(formatted)
    if start is None:
        for record in recent_before_cutoff:
            formatted = format_record(record)
            if formatted:
                chunks.append(formatted)
    text = "\n\n".join(chunks)
    if len(text) <= TRANSCRIPT_CHAR_LIMIT:
        return text
    return (
        text[:8000].rstrip()
        + f"\n\n[... transcript trimmed {len(text) - TRANSCRIPT_CHAR_LIMIT} chars ...]\n\n"
        + text[-16000:].lstrip()
    )


def current_snapshot_if_safe(repo_root: Path, doc_id: str, cutoff_timestamp: str | None) -> tuple[str, str]:
    path = repo_root / doc_relpath(doc_id)
    if not path.exists():
        return "missing", ""
    text = path.read_text(encoding="utf-8")
    metadata, _body = parse_frontmatter(text)
    cutoff = parse_ts(cutoff_timestamp)
    updated = parse_ts(metadata.get("updated_at"))
    created = parse_ts(metadata.get("created_at"))
    if cutoff is None:
        return "current_file_no_source_cutoff", ""
    if updated is not None and updated <= cutoff + timedelta(minutes=5):
        return "current_file_safe_updated_before_cutoff", text
    if updated is None and created is not None and created <= cutoff + timedelta(minutes=5):
        return "current_file_safe_no_update_timestamp", text
    return "current_file_excluded_future_update_risk", ""


def render_label_packet(
    *,
    repo_root: Path,
    source: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    doc_id = str(source["doc_id"])
    snapshot_status, snapshot = current_snapshot_if_safe(
        repo_root,
        doc_id,
        source.get("cutoff_timestamp") if isinstance(source.get("cutoff_timestamp"), str) else None,
    )
    transcript = transcript_excerpt(
        session_file=Path(str(source.get("session_file") or "")),
        start_timestamp=source.get("source_task_start_timestamp")
        if isinstance(source.get("source_task_start_timestamp"), str)
        else None,
        cutoff_timestamp=source.get("cutoff_timestamp")
        if isinstance(source.get("cutoff_timestamp"), str)
        else None,
    )
    packet_meta = {
        "doc_id": doc_id,
        "writeback_path": source.get("writeback_path"),
        "recovery_status": source.get("recovery_status"),
        "source_kind": source.get("source_kind"),
        "source_session_id": source.get("session_id"),
        "first_writeback_at": source.get("first_writeback_at"),
        "snapshot_status": snapshot_status,
        "has_transcript_excerpt": bool(transcript.strip()),
    }
    lines = [
        "# Blind Applies-When Label Packet",
        "",
        "You are writing routing metadata for one AI Wiki memory.",
        "",
        "Allowed inputs in this packet:",
        "",
        "- the target memory path and metadata below",
        "- the source session excerpt up to the first write-back footer",
        "- the memory file snapshot only when the packet marks it as safe",
        "- the label grammar",
        "",
        "Forbidden inputs:",
        "",
        "- historical route prompts",
        "- selected/useful/false-positive/missed-useful outcomes",
        "- route precision or noise reports",
        "- any future notes or edits outside this packet",
        "",
        "Label grammar:",
        "",
        "```text",
        "<verb> <stage/object> when <trigger>; not for <nearby stages>",
        "```",
        "",
        "Return `insufficient_source` if this packet is not enough to write the label.",
        "",
        "## Target",
        "",
        "```json",
        json.dumps(packet_meta, indent=2, ensure_ascii=False),
        "```",
        "",
    ]
    if snapshot:
        lines.extend(
            [
                "## Safe Memory Snapshot",
                "",
                "```markdown",
                snapshot.strip(),
                "```",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## Memory Snapshot",
                "",
                f"Snapshot omitted: `{snapshot_status}`.",
                "",
            ]
        )
    lines.extend(
        [
            "## Source Session Excerpt",
            "",
            transcript.strip() or "No source transcript excerpt recovered.",
            "",
            "## Required JSON Output",
            "",
            "Return exactly:",
            "",
            "```json",
            json.dumps(
                {
                    "doc_id": doc_id,
                    "label_status": "labeled",
                    "applies_when": "",
                    "routing_hint": "",
                    "rationale": "",
                },
                indent=2,
            ),
            "```",
            "",
        ]
    )
    return "\n".join(lines), packet_meta


def prepare(args: argparse.Namespace) -> None:
    repo_root = resolve_repo_root(args.repo_root)
    output_dir = args.output_dir
    replay_report = load_json(repo_root / args.replay_report)
    output_dir.mkdir(parents=True, exist_ok=True)

    counts = selected_doc_counts(replay_report)
    target_docs = [doc_id for doc_id, _count in counts.most_common(args.target_count)]
    target_rows = [
        {
            "rank": index,
            "doc_id": doc_id,
            "selected_count": counts[doc_id],
            "path": doc_relpath(doc_id),
            "exists": (repo_root / doc_relpath(doc_id)).exists(),
        }
        for index, doc_id in enumerate(target_docs, start=1)
    ]
    sources = recover_sources(
        repo_root=repo_root,
        doc_ids=target_docs,
        sessions_root=args.sessions_root.expanduser(),
        handle=args.handle,
    )
    source_by_doc = {str(row["doc_id"]): row for row in sources}
    for row in target_rows:
        row["recovery_status"] = source_by_doc[row["doc_id"]]["recovery_status"]

    write_json(output_dir / "inputs" / "frozen_replay_report.json", replay_report)
    write_json(output_dir / "inputs" / "target_docs.json", target_rows)
    write_json(output_dir / "source_map" / "recovered_sessions.json", sources)
    write_json(output_dir / "label_packets" / "label.schema.json", LABEL_SCHEMA)

    packet_manifest: list[dict[str, Any]] = []
    for source in sources:
        if source.get("recovery_status") in {"not_found", "source_incident_missing_session"}:
            continue
        packet, packet_meta = render_label_packet(repo_root=repo_root, source=source)
        doc_id = str(source["doc_id"])
        packet_id = f"p{int(source['rank']):03d}-{doc_id.replace('/', '__')}"
        packet_path = output_dir / "label_packets" / packet_id / "input.md"
        packet_path.parent.mkdir(parents=True, exist_ok=True)
        packet_path.write_text(packet, encoding="utf-8")
        write_json(packet_path.parent / "packet_meta.json", packet_meta)
        packet_manifest.append(
            {
                "packet_id": packet_id,
                "doc_id": doc_id,
                "packet_path": str(packet_path),
                **packet_meta,
            }
        )
    write_json(output_dir / "label_packets" / "manifest.json", packet_manifest)

    manifest = {
        "schema_version": "applies-when-blind-experiment-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": "<local ai-wiki-toolkit checkout>",
        "experiment_dir": str(output_dir.relative_to(repo_root))
        if output_dir.is_relative_to(repo_root)
        else str(output_dir),
        "selection_rule": (
            "Top target_count docs by control replay selected_doc_ids frequency; "
            "selection ignores useful/false-positive outcomes."
        ),
        "target_count": args.target_count,
        "target_doc_count": len(target_docs),
        "packet_count": len(packet_manifest),
        "before": args.before,
        "catalog_cutoff": "trace-routed-at",
        "max_docs": args.max_docs,
        "rerank_top": args.rerank_top,
        "budget_words": args.budget_words,
    }
    write_json(output_dir / "manifest.json", manifest)
    print(f"Prepared experiment at {output_dir}")
    print(f"Target docs: {len(target_docs)}")
    print(f"Label packets: {len(packet_manifest)}")


def copy_packets_for_labeler(output_dir: Path, packet_root: Path) -> list[dict[str, Any]]:
    manifest = load_json(output_dir / "label_packets" / "manifest.json")
    packet_root.mkdir(parents=True, exist_ok=True)
    schema_text = (output_dir / "label_packets" / "label.schema.json").read_text(encoding="utf-8")
    copied: list[dict[str, Any]] = []
    for item in manifest:
        packet_id = str(item["packet_id"])
        source_dir = output_dir / "label_packets" / packet_id
        target_dir = packet_root / packet_id
        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(source_dir, target_dir)
        (target_dir / "label.schema.json").write_text(schema_text, encoding="utf-8")
        copied.append({**item, "labeler_dir": str(target_dir)})
    return copied


def run_labelers(args: argparse.Namespace) -> None:
    output_dir = args.output_dir
    packet_root = args.packet_root or Path(tempfile.gettempdir()) / "aiwiki_applies_when_blind_2026_06"
    copied = copy_packets_for_labeler(output_dir, packet_root)
    output_label_dir = output_dir / "labels" / "raw"
    output_label_dir.mkdir(parents=True, exist_ok=True)
    run_log: list[dict[str, Any]] = []
    for item in copied:
        packet_id = str(item["packet_id"])
        if args.limit is not None and len(run_log) >= args.limit:
            break
        labeler_dir = Path(str(item["labeler_dir"]))
        final_output = output_label_dir / f"{packet_id}.json"
        if final_output.exists() and not args.overwrite:
            run_log.append(
                {
                    "packet_id": packet_id,
                    "doc_id": item.get("doc_id"),
                    "returncode": 0,
                    "skipped": True,
                    "reason": "existing_label_output",
                    "output": str(final_output),
                }
            )
            continue
        prompt = (
            "Read only input.md in the current directory. Do not inspect parent directories, "
            "the original repository, route reports, or external files. Produce the required "
            "JSON object for the blind applies_when label packet. If the packet lacks enough "
            "source evidence, use label_status=insufficient_source."
        )
        cmd = [
            "codex",
            "exec",
            "--ephemeral",
            "--skip-git-repo-check",
            "--ignore-rules",
            "--sandbox",
            "read-only",
            "--cd",
            str(labeler_dir),
            "--output-schema",
            str(labeler_dir / "label.schema.json"),
            "--output-last-message",
            str(final_output),
            prompt,
        ]
        print(f"Running labeler for {packet_id}")
        result = subprocess.run(cmd, check=False, text=True, capture_output=True)
        run_log.append(
            {
                "packet_id": packet_id,
                "doc_id": item.get("doc_id"),
                "returncode": result.returncode,
                "stdout_tail": result.stdout[-4000:],
                "stderr_tail": result.stderr[-4000:],
                "output": str(final_output),
            }
        )
        if result.returncode != 0:
            print(f"Labeler failed for {packet_id}: {result.returncode}", file=sys.stderr)
            if not args.keep_going:
                break
    write_json(output_dir / "labels" / "labeler_run_log.json", run_log)
    print(f"Wrote labeler log: {output_dir / 'labels' / 'labeler_run_log.json'}")


def extract_json_object(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    if not stripped:
        return None
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, flags=re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(stripped[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None


def audit_label(label: dict[str, Any]) -> dict[str, Any]:
    text = " ".join(
        str(label.get(key) or "") for key in ("applies_when", "routing_hint", "rationale")
    ).lower()
    forbidden = [fragment for fragment in FORBIDDEN_LABEL_FRAGMENTS if fragment in text]
    applies_when = str(label.get("applies_when") or "").strip()
    return {
        "passed": not forbidden
        and label.get("label_status") == "labeled"
        and bool(applies_when)
        and len(applies_when) <= 260,
        "forbidden_fragments": forbidden,
        "applies_when_length": len(applies_when),
    }


def collect_labels(args: argparse.Namespace) -> None:
    output_dir = args.output_dir
    packet_manifest = load_json(output_dir / "label_packets" / "manifest.json")
    raw_dir = output_dir / "labels" / "raw"
    collected: list[dict[str, Any]] = []
    overlay: list[dict[str, Any]] = []
    for item in packet_manifest:
        packet_id = str(item["packet_id"])
        raw_path = raw_dir / f"{packet_id}.json"
        label = extract_json_object(raw_path.read_text(encoding="utf-8")) if raw_path.exists() else None
        if label is None:
            collected.append(
                {
                    "packet_id": packet_id,
                    "doc_id": item.get("doc_id"),
                    "label_status": "missing_output",
                    "audit": {"passed": False, "reason": "missing_or_unparseable_output"},
                }
            )
            continue
        audit = audit_label(label)
        row = {
            "packet_id": packet_id,
            "doc_id": item.get("doc_id"),
            "label": label,
            "audit": audit,
            "source_session_ref": "redacted" if item.get("source_session_id") else None,
            "snapshot_status": item.get("snapshot_status"),
        }
        collected.append(row)
        if audit["passed"]:
            overlay.append(
                {
                    "doc_id": item.get("doc_id"),
                    "applies_when": str(label.get("applies_when") or "").strip(),
                    "routing_hint": str(label.get("routing_hint") or "").strip(),
                    "source_session_ref": "redacted" if item.get("source_session_id") else None,
                    "packet_id": packet_id,
                    "snapshot_status": item.get("snapshot_status"),
                }
            )
    write_json(output_dir / "labels" / "collected_labels.json", collected)
    write_json(output_dir / "labels" / "treatment_overlay.json", overlay)
    print(f"Collected labels: {len(collected)}")
    print(f"Audit-passing overlay labels: {len(overlay)}")


def run_git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def create_temp_repo(source_wiki: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    shutil.copytree(source_wiki, target / "ai-wiki")
    (target / ".env.aiwiki").write_text("AIWIKI_TOOLKIT_ACTOR_HANDLE=bochengyin\n", encoding="utf-8")
    run_git(["init"], cwd=target)
    run_git(["config", "user.name", "AI Wiki Eval"], cwd=target)
    run_git(["config", "user.email", "eval@example.com"], cwd=target)
    run_git(["add", "."], cwd=target)
    run_git(["commit", "-m", "Prepare replay wiki"], cwd=target)


def apply_overlay(repo_root: Path, overlay: list[dict[str, Any]]) -> None:
    for item in overlay:
        doc_id = item.get("doc_id")
        if not isinstance(doc_id, str) or not doc_id:
            continue
        path = repo_root / doc_relpath(doc_id)
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        metadata, _body = parse_frontmatter(text)
        metadata = dict(metadata)
        applies_when = item.get("applies_when")
        routing_hint = item.get("routing_hint")
        if isinstance(applies_when, str) and applies_when.strip():
            metadata["applies_when"] = applies_when.strip()
        if isinstance(routing_hint, str) and routing_hint.strip():
            metadata["routing_hint"] = routing_hint.strip()
        path.write_text(replace_frontmatter(text, metadata), encoding="utf-8")


def compare_reports(control: dict[str, Any], treatment: dict[str, Any]) -> dict[str, Any]:
    control_summary = control.get("replay", {}).get("summary", {})
    treatment_summary = treatment.get("replay", {}).get("summary", {})
    paired: list[dict[str, Any]] = []
    treatment_by_trace = {
        item.get("trace_id"): item
        for item in treatment.get("items", [])
        if isinstance(item, dict) and isinstance(item.get("replay"), dict)
    }
    for control_item in control.get("items", []):
        if not isinstance(control_item, dict) or not isinstance(control_item.get("replay"), dict):
            continue
        trace_id = control_item.get("trace_id")
        treatment_item = treatment_by_trace.get(trace_id)
        if not isinstance(treatment_item, dict) or not isinstance(treatment_item.get("replay"), dict):
            continue
        c_replay = control_item["replay"]
        t_replay = treatment_item["replay"]
        c_precision = c_replay.get("route_precision")
        t_precision = t_replay.get("route_precision")
        paired.append(
            {
                "trace_id": trace_id,
                "task_id": control_item.get("task_id"),
                "control_precision": c_precision,
                "treatment_precision": t_precision,
                "precision_delta": (
                    t_precision - c_precision
                    if isinstance(c_precision, float) and isinstance(t_precision, float)
                    else None
                ),
                "control_selected": c_replay.get("selected_doc_ids"),
                "treatment_selected": t_replay.get("selected_doc_ids"),
                "control_missed_useful": c_replay.get("missed_useful_doc_ids"),
                "treatment_missed_useful": t_replay.get("missed_useful_doc_ids"),
            }
        )
    deltas = [row["precision_delta"] for row in paired if isinstance(row["precision_delta"], float)]
    return {
        "schema_version": "applies-when-control-treatment-comparison-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "control_summary": control_summary,
        "treatment_summary": treatment_summary,
        "summary_delta": {
            key: (
                treatment_summary.get(key) - control_summary.get(key)
                if isinstance(control_summary.get(key), (int, float))
                and isinstance(treatment_summary.get(key), (int, float))
                else None
            )
            for key in (
                "route_precision",
                "route_noise_rate",
                "selected_doc_count",
                "selected_useful_doc_count",
                "missed_useful_doc_count",
            )
        },
        "paired_trace_count": len(paired),
        "paired_wins": sum(1 for delta in deltas if delta > 0),
        "paired_losses": sum(1 for delta in deltas if delta < 0),
        "paired_ties": sum(1 for delta in deltas if delta == 0),
        "paired": paired,
    }


def render_comparison_markdown(comparison: dict[str, Any], overlay_count: int) -> str:
    control = comparison["control_summary"]
    treatment = comparison["treatment_summary"]
    delta = comparison["summary_delta"]
    return "\n".join(
        [
            "# Blinded Applies-When Route Replay",
            "",
            "This report compares the same 57 historical route traces with and without a",
            "blindly generated `applies_when` treatment overlay.",
            "",
            "## Setup",
            "",
            f"- Overlay labels applied: `{overlay_count}`",
            "- Target docs selected by control selected-count frequency, not false-positive outcomes.",
            "- Catalog cutoff: `trace-routed-at`",
            "- Claim type: retrospective route-quality replay, not production improvement.",
            "",
            "## Summary",
            "",
            "| condition | traces | precision | noise | selected | selected useful | missed useful |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            (
                f"| control | {control.get('trace_count')} | {control.get('route_precision'):.3f} | "
                f"{control.get('route_noise_rate'):.3f} | {control.get('selected_doc_count')} | "
                f"{control.get('selected_useful_doc_count')} | {control.get('missed_useful_doc_count')} |"
            ),
            (
                f"| treatment | {treatment.get('trace_count')} | {treatment.get('route_precision'):.3f} | "
                f"{treatment.get('route_noise_rate'):.3f} | {treatment.get('selected_doc_count')} | "
                f"{treatment.get('selected_useful_doc_count')} | {treatment.get('missed_useful_doc_count')} |"
            ),
            "",
            "## Delta",
            "",
            f"- Precision delta: `{delta.get('route_precision')}`",
            f"- Noise delta: `{delta.get('route_noise_rate')}`",
            f"- Selected useful delta: `{delta.get('selected_useful_doc_count')}`",
            f"- Missed useful delta: `{delta.get('missed_useful_doc_count')}`",
            f"- Paired wins/losses/ties: `{comparison.get('paired_wins')}` / `{comparison.get('paired_losses')}` / `{comparison.get('paired_ties')}`",
            "",
        ]
    )


def replay(args: argparse.Namespace) -> None:
    repo_root = resolve_repo_root(args.repo_root)
    output_dir = args.output_dir
    overlay_path = output_dir / "labels" / "treatment_overlay.json"
    overlay = load_json(overlay_path) if overlay_path.exists() else []
    worktree_root = output_dir / "worktrees"
    control_root = worktree_root / "control"
    treatment_root = worktree_root / "treatment"
    create_temp_repo(repo_root / "ai-wiki", control_root)
    create_temp_repo(repo_root / "ai-wiki", treatment_root)
    apply_overlay(treatment_root, overlay if isinstance(overlay, list) else [])
    run_git(["add", "."], cwd=treatment_root)
    run_git(["commit", "-m", "Apply treatment overlay"], cwd=treatment_root)

    control_report = generate_route_replay_report(
        repo_root=control_root,
        handle=args.handle,
        before=args.before,
        catalog_cutoff="trace-routed-at",
        target_evaluable_traces=args.target_evaluable_traces,
        max_docs=args.max_docs,
        rerank_top=args.rerank_top,
        budget_words=args.budget_words,
        max_items=10000,
    )
    treatment_report = generate_route_replay_report(
        repo_root=treatment_root,
        handle=args.handle,
        before=args.before,
        catalog_cutoff="trace-routed-at",
        target_evaluable_traces=args.target_evaluable_traces,
        max_docs=args.max_docs,
        rerank_top=args.rerank_top,
        budget_words=args.budget_words,
        max_items=10000,
    )
    comparison = compare_reports(control_report, treatment_report)
    reports_dir = output_dir / "reports"
    write_json(reports_dir / "control_replay.json", control_report)
    write_json(reports_dir / "treatment_replay.json", treatment_report)
    write_json(reports_dir / "control_vs_treatment.json", comparison)
    rendered = render_comparison_markdown(
        comparison,
        overlay_count=len(overlay) if isinstance(overlay, list) else 0,
    )
    (reports_dir / "control_vs_treatment.md").write_text(rendered, encoding="utf-8")
    print(rendered)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--repo-root", type=Path, default=None)
        subparser.add_argument("--output-dir", type=Path, default=DEFAULT_EXPERIMENT_DIR)
        subparser.add_argument("--handle", default=DEFAULT_HANDLE)
        subparser.add_argument("--before", default=DEFAULT_BEFORE)
        subparser.add_argument("--max-docs", type=int, default=DEFAULT_MAX_DOCS)
        subparser.add_argument("--rerank-top", type=int, default=DEFAULT_RERANK_TOP)
        subparser.add_argument("--budget-words", type=int, default=DEFAULT_BUDGET_WORDS)

    prepare_parser = subparsers.add_parser("prepare")
    add_common(prepare_parser)
    prepare_parser.add_argument("--replay-report", type=Path, default=DEFAULT_REPLAY_REPORT)
    prepare_parser.add_argument("--target-count", type=int, default=DEFAULT_TARGET_COUNT)
    prepare_parser.add_argument("--sessions-root", type=Path, default=Path.home() / ".codex" / "sessions")
    prepare_parser.set_defaults(func=prepare)

    label_parser = subparsers.add_parser("run-labelers")
    add_common(label_parser)
    label_parser.add_argument("--packet-root", type=Path, default=None)
    label_parser.add_argument("--limit", type=int, default=None)
    label_parser.add_argument("--keep-going", action="store_true")
    label_parser.add_argument("--overwrite", action="store_true")
    label_parser.set_defaults(func=run_labelers)

    collect_parser = subparsers.add_parser("collect-labels")
    add_common(collect_parser)
    collect_parser.set_defaults(func=collect_labels)

    replay_parser = subparsers.add_parser("replay")
    add_common(replay_parser)
    replay_parser.add_argument("--target-evaluable-traces", type=int, default=57)
    replay_parser.set_defaults(func=replay)

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir = args.output_dir.resolve()
    args.func(args)


if __name__ == "__main__":
    main()
