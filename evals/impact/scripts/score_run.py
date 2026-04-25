"""Write manual impact-eval score artifacts separate from capture artifacts."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path


SCORE_LABELS = ("success", "partial", "fail")


def parse_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True, help="Run directory created by init_run.py.")
    parser.add_argument("--slot", required=True, help="Neutral slot or legacy variant directory.")
    parser.add_argument("--prompt-level", required=True, help="Prompt level such as original.")
    parser.add_argument("--label", choices=SCORE_LABELS, required=True, help="Manual score label.")
    parser.add_argument("--rubric-refs", type=parse_csv, default=[], help="Comma-separated rubric references.")
    parser.add_argument("--evidence", type=parse_csv, default=[], help="Comma-separated evidence artifact paths.")
    parser.add_argument("--notes", default="", help="Manual scoring notes.")
    return parser.parse_args()


def write_score(
    run_dir: Path,
    *,
    slot: str,
    prompt_level: str,
    label: str,
    rubric_refs: list[str] | None = None,
    evidence: list[str] | None = None,
    notes: str = "",
) -> Path:
    if label not in SCORE_LABELS:
        raise ValueError(f"Unsupported score label: {label}")
    score_path = run_dir / slot / prompt_level / "score.json"
    payload = {
        "schema_version": 2,
        "slot": slot,
        "prompt_level": prompt_level,
        "label": label,
        "rubric_refs": rubric_refs or [],
        "evidence": evidence or [],
        "notes": notes,
        "scored_at": datetime.now().isoformat(timespec="seconds"),
    }
    score_path.parent.mkdir(parents=True, exist_ok=True)
    score_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return score_path


def main() -> None:
    args = parse_args()
    path = write_score(
        args.run_dir,
        slot=args.slot,
        prompt_level=args.prompt_level,
        label=args.label,
        rubric_refs=args.rubric_refs,
        evidence=args.evidence,
        notes=args.notes,
    )
    print(path)


if __name__ == "__main__":
    main()
