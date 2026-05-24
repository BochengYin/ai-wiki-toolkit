from __future__ import annotations

import json
from pathlib import Path
import subprocess

from typer.testing import CliRunner

import ai_wiki_toolkit.impact_eval as impact_eval
from ai_wiki_toolkit.cli import app
from ai_wiki_toolkit.impact_eval import (
    capture_impact_eval_result,
    draft_impact_eval_family_candidate,
    discover_impact_eval_families,
    discover_impact_eval_family_candidates,
    generate_impact_eval_manifest,
    generate_impact_eval_report,
    generate_impact_eval_run_plan,
    generate_impact_eval_schedule_report,
    generate_impact_eval_summary,
    impact_eval_report_to_dict,
    impact_eval_summary_to_dict,
    init_impact_eval_family_from_candidate,
    prepare_impact_eval_run,
    promote_impact_eval_family_candidate,
    render_impact_eval_benchmark_result,
    render_impact_eval_candidate_draft_result,
    render_impact_eval_candidate_promotion_result,
    render_impact_eval_candidate_queue,
    render_impact_eval_capture_result,
    render_impact_eval_families,
    render_impact_eval_family_candidates,
    render_impact_eval_family_detail,
    render_impact_eval_family_init_result,
    render_impact_eval_manifest,
    render_impact_eval_prepare_result,
    render_impact_eval_report,
    render_impact_eval_run_plan,
    render_impact_eval_run_result,
    render_impact_eval_schedule_report,
    render_impact_eval_schedule_run_result,
    render_impact_eval_score_result,
    render_impact_eval_summary,
    render_impact_eval_validate_result,
    refresh_impact_eval_candidate_queue,
    run_impact_eval_benchmark,
    run_impact_eval,
    run_impact_eval_schedule,
    score_impact_eval_result,
    show_impact_eval_family,
    validate_impact_eval_run,
)


runner = CliRunner()


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_script_command_uses_python_from_path_when_running_as_packaged_binary(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        impact_eval.sys,
        "executable",
        "/opt/homebrew/bin/aiwiki-toolkit",
    )
    monkeypatch.setattr(
        impact_eval.shutil,
        "which",
        lambda name: "/usr/bin/python3" if name == "python3" else None,
    )

    command = impact_eval._script_command(tmp_path, "prepare_variants.py")

    assert command[:2] == [
        "/usr/bin/python3",
        str(tmp_path / "evals" / "impact" / "scripts" / "prepare_variants.py"),
    ]


def _write_result(
    run_dir: Path,
    *,
    slot: str,
    variant: str,
    score: str,
    first_pass_success: bool,
    phase: str = "first_pass",
    changed_files: list[str] | None = None,
    untracked_files: list[str] | None = None,
) -> None:
    result_dir = run_dir / slot / "original" / phase
    _write_json(
        result_dir / "result.json",
        {
            "slot": slot,
            "variant": variant,
            "prompt_level": "original",
            "phase": phase,
            "attempt": 1,
            "human_nudges": 0,
            "first_pass_success": first_pass_success,
            "changed_files": changed_files or ["scripts/example.py"],
            "untracked_files": untracked_files or [],
            "notes": "",
        },
    )
    (result_dir / "final_message.md").write_text("done\n", encoding="utf-8")
    _write_json(
        run_dir / slot / "original" / "score.json",
        {
            "schema_version": 2,
            "slot": slot,
            "prompt_level": "original",
            "label": score,
            "rubric_refs": [],
            "evidence": [f"{slot}/original/{phase}/workspace_diff.patch"],
            "notes": "",
        },
    )


def _make_run_dir(
    tmp_path: Path,
    *,
    name: str = "run_001",
    experiment: str = "scaffold_prompt_workflow_compliance",
) -> Path:
    run_dir = tmp_path / "runs" / name
    _write_json(
        run_dir / "metadata.json",
        {
            "schema_version": 2,
            "experiment": experiment,
            "workspace_root": "/tmp/workspaces",
            "variants": ["s01", "s02", "s03"],
            "prompt_levels": ["original"],
            "prompt_hashes": {"original": "abc123"},
            "created_at": "2026-04-29T10:00:00",
            "primary_comparison": [
                "no_aiwiki_workflow",
                "aiwiki_ambient_memory_workflow",
            ],
            "diagnostic_variants": ["aiwiki_linked_raw_only"],
            "model_family": "gpt-5.5",
            "reasoning_effort": "xhigh",
            "execution_surface": "codex-cli",
            "assignment": {
                "baseline_ref": "HEAD^",
                "workspace_layout": "neutral",
                "slots": [
                    {
                        "slot": "s01",
                        "variant": "no_aiwiki_workflow",
                        "workspace": "/tmp/workspaces/slots/s01",
                    },
                    {
                        "slot": "s02",
                        "variant": "aiwiki_ambient_memory_workflow",
                        "workspace": "/tmp/workspaces/slots/s02",
                    },
                    {
                        "slot": "s03",
                        "variant": "aiwiki_linked_raw_only",
                        "workspace": "/tmp/workspaces/slots/s03",
                    },
                ]
            },
        },
    )
    _write_json(
        run_dir / "confounds.json",
        {
            "shareable_for_causal_claims": True,
            "critical_confounds": [],
        },
    )
    _write_result(
        run_dir,
        slot="s01",
        variant="no_aiwiki_workflow",
        score="fail",
        first_pass_success=False,
    )
    _write_result(
        run_dir,
        slot="s02",
        variant="aiwiki_ambient_memory_workflow",
        score="success",
        first_pass_success=True,
    )
    _write_result(
        run_dir,
        slot="s03",
        variant="aiwiki_linked_raw_only",
        score="success",
        first_pass_success=True,
    )
    _write_result(
        run_dir,
        slot="s02",
        variant="aiwiki_ambient_memory_workflow",
        score="success",
        first_pass_success=True,
        phase="final",
    )
    return run_dir


def _make_empty_run_dir(tmp_path: Path, *, name: str = "run_empty") -> Path:
    run_dir = tmp_path / "runs" / name
    _write_json(
        run_dir / "metadata.json",
        {
            "schema_version": 2,
            "experiment": "ownership_boundary",
            "workspace_root": str(tmp_path / "workspaces"),
            "variants": ["s01", "s02", "s03"],
            "prompt_levels": ["original"],
            "prompt_hashes": {"original": "abc123"},
            "created_at": "2026-05-22T10:00:00",
            "primary_comparison": [
                "no_aiwiki_workflow",
                "aiwiki_ambient_memory_workflow",
            ],
            "diagnostic_variants": ["aiwiki_linked_raw_only"],
            "model_family": "gpt-5.5",
            "reasoning_effort": "xhigh",
            "execution_surface": "codex-cli",
            "assignment": {
                "baseline_ref": "HEAD^",
                "workspace_layout": "neutral",
                "slots": [
                    {
                        "slot": "s01",
                        "variant": "no_aiwiki_workflow",
                        "workspace": str(tmp_path / "workspaces" / "slots" / "s01"),
                    },
                    {
                        "slot": "s02",
                        "variant": "aiwiki_ambient_memory_workflow",
                        "workspace": str(tmp_path / "workspaces" / "slots" / "s02"),
                    },
                    {
                        "slot": "s03",
                        "variant": "aiwiki_linked_raw_only",
                        "workspace": str(tmp_path / "workspaces" / "slots" / "s03"),
                    },
                ],
            },
        },
    )
    return run_dir


def _install_fake_autorun_scripts(monkeypatch, *, fail_s01: bool = False) -> list[list[str]]:
    calls: list[list[str]] = []

    def fake_run(command: list[str], **kwargs):
        calls.append(command)
        script_name = Path(command[1]).name if len(command) > 1 else ""
        if script_name == "init_run.py":
            _write_prepared_metadata(command)
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="ok\n",
                stderr="",
            )
        if script_name == "prepare_variants.py":
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="ok\n",
                stderr="",
            )
        if script_name == "run_cli_slots.py":
            run_dir = Path(command[command.index("--run-dir") + 1])
            prompt_level = command[command.index("--prompt-level") + 1]
            metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
            if "--slots" in command:
                slots = [
                    item.strip()
                    for item in command[command.index("--slots") + 1].split(",")
                    if item.strip()
                ]
            else:
                slots = list(metadata["variants"])
            variant_map = {
                item["slot"]: item["variant"]
                for item in metadata["assignment"]["slots"]
            }
            results = []
            for slot in slots:
                result_dir = run_dir / slot / prompt_level / "first_pass"
                result_dir.mkdir(parents=True, exist_ok=True)
                _write_text(result_dir / "final_message.md", f"{slot} complete\n")
                _write_text(result_dir / "workspace_diff.patch", f"diff --git a/{slot} b/{slot}\n")
                _write_json(
                    result_dir / "result.json",
                    {
                        "schema_version": 2,
                        "slot": slot,
                        "variant": variant_map[slot],
                        "prompt_level": prompt_level,
                        "phase": "first_pass",
                        "attempt": 1,
                        "human_nudges": 0,
                        "first_pass_success": None,
                        "changed_files": [f"{slot}.txt"],
                        "untracked_files": [],
                    },
                )
                codex_returncode = 1 if fail_s01 and slot == "s01" else 0
                command_result = {
                    "slot": slot,
                    "variant": variant_map[slot],
                    "prompt_level": prompt_level,
                    "workspace": f"/tmp/workspaces/slots/{slot}",
                    "final_message": str(result_dir / "final_message.md"),
                    "codex_returncode": codex_returncode,
                    "save_result_returncode": 0,
                    "started_at": "2026-05-22T10:00:00",
                    "finished_at": "2026-05-22T10:00:01",
                }
                _write_json(result_dir / "command_result.json", command_result)
                results.append(command_result)
            _write_json(run_dir / "slot_command_results.json", {"results": results})
            return subprocess.CompletedProcess(
                args=command,
                returncode=1 if any(item["codex_returncode"] for item in results) else 0,
                stdout="",
                stderr="",
            )
        if script_name == "score_run.py":
            score_path = (
                Path(command[command.index("--run-dir") + 1])
                / command[command.index("--slot") + 1]
                / command[command.index("--prompt-level") + 1]
                / "score.json"
            )
            rubric_refs = []
            if "--rubric-refs" in command:
                rubric_refs = [
                    item.strip()
                    for item in command[command.index("--rubric-refs") + 1].split(",")
                    if item.strip()
                ]
            evidence = []
            if "--evidence" in command:
                evidence = [
                    item.strip()
                    for item in command[command.index("--evidence") + 1].split(",")
                    if item.strip()
                ]
            _write_json(
                score_path,
                {
                    "schema_version": 2,
                    "slot": command[command.index("--slot") + 1],
                    "prompt_level": command[command.index("--prompt-level") + 1],
                    "label": command[command.index("--label") + 1],
                    "rubric_refs": rubric_refs,
                    "evidence": evidence,
                },
            )
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout=str(score_path) + "\n",
                stderr="",
            )
        if script_name == "export_codex_sessions.py":
            workspace_root = Path(command[command.index("--workspace-root") + 1])
            output_root = workspace_root / "codex_sessions"
            output_root.mkdir(parents=True, exist_ok=True)
            _write_json(
                output_root / "manifest.json",
                {
                    "workspace_root": str(workspace_root),
                    "variants": ["s01", "s02", "s03"],
                    "exported_session_count": 3,
                    "missing_variants": [],
                    "sessions": [],
                },
            )
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout=str(output_root) + "\nExported sessions: 3\n",
                stderr="",
            )
        if script_name == "validate_run.py":
            confounds_path = Path(command[command.index("--run-dir") + 1]) / "confounds.json"
            _write_json(
                confounds_path,
                {
                    "schema_version": 2,
                    "shareable_for_causal_claims": True,
                    "critical_confounds": [],
                    "warnings": [],
                },
            )
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout=str(confounds_path) + "\n",
                stderr="",
            )
        return subprocess.CompletedProcess(args=command, returncode=0, stdout="", stderr="")

    monkeypatch.setattr("ai_wiki_toolkit.impact_eval.subprocess.run", fake_run)
    return calls


def test_impact_eval_report_computes_first_attempt_primary_signal(tmp_path: Path) -> None:
    run_dir = _make_run_dir(tmp_path)

    report = generate_impact_eval_report(run_dir)

    assert report.primary_comparison.outcome == "positive_signal"
    assert report.primary_comparison.first_attempt_success_delta == 1.0
    assert report.primary_comparison.avg_score_delta == 1.0
    ambient = {
        summary.variant: summary for summary in report.variant_summaries
    }["aiwiki_ambient_memory_workflow"]
    assert ambient.first_attempt_results == 1
    assert ambient.recorded_results == 2
    assert ambient.avg_changed_files == 1.0
    assert ambient.avg_untracked_files == 0.0
    assert ambient.avg_project_changed_files == 1.0
    assert ambient.avg_managed_wiki_changed_files == 0.0
    assert ambient.avg_user_wiki_changed_files == 0.0


def test_impact_eval_report_render_names_first_attempt_policy(tmp_path: Path) -> None:
    run_dir = _make_run_dir(tmp_path)
    report_text = render_impact_eval_report(generate_impact_eval_report(run_dir))

    assert "AI wiki first-attempt signal: `positive_signal`" in report_text
    assert "grade `first_pass` captures; `final` repair captures are diagnostic only" in report_text
    assert "| first_attempt_success_rate | 0/1 (0%) | 1/1 (100%) | +100% |" in report_text
    assert "| avg_project_changed_files | 1.00 | 1.00 | +0.00 |" in report_text
    assert "avg_project_changed_files" in report_text
    assert "avg_user_wiki_changed_files" in report_text
    assert "aiwiki_linked_raw_only" in report_text


def test_impact_eval_report_splits_project_managed_and_user_wiki_churn(
    tmp_path: Path,
) -> None:
    run_dir = _make_run_dir(tmp_path)
    _write_result(
        run_dir,
        slot="s02",
        variant="aiwiki_ambient_memory_workflow",
        score="success",
        first_pass_success=True,
        changed_files=[
            "src/ai_wiki_toolkit/example.py",
            "ai-wiki/_toolkit/metrics/task-stats.json",
            "ai-wiki/metrics/reuse-events/alice.jsonl",
            "ai-wiki/people/alice/drafts/retry-loop.md",
        ],
        untracked_files=[
            "ai-wiki/metrics/reuse-events/alice.jsonl",
            "ai-wiki/people/alice/drafts/retry-loop.md",
        ],
    )

    report = generate_impact_eval_report(run_dir)
    ambient = {
        summary.variant: summary for summary in report.variant_summaries
    }["aiwiki_ambient_memory_workflow"]

    assert ambient.avg_changed_files == 4.0
    assert ambient.avg_untracked_files == 2.0
    assert ambient.avg_project_changed_files == 1.0
    assert ambient.avg_managed_wiki_changed_files == 2.0
    assert ambient.avg_user_wiki_changed_files == 1.0
    assert ambient.avg_user_wiki_untracked_files == 1.0

    payload = impact_eval_report_to_dict(report)
    ambient_metrics = {
        item["variant"]: item for item in payload["variant_metrics"]
    }["aiwiki_ambient_memory_workflow"]
    assert ambient_metrics["avg_project_changed_files"] == 1.0
    assert ambient_metrics["avg_managed_wiki_changed_files"] == 2.0
    assert ambient_metrics["avg_user_wiki_changed_files"] == 1.0


def test_eval_impact_report_cli_outputs_json_and_writes_text(tmp_path: Path) -> None:
    run_dir = _make_run_dir(tmp_path)

    json_result = runner.invoke(
        app,
        ["eval", "impact", "report", "--run-dir", str(run_dir), "--format", "json"],
    )

    assert json_result.exit_code == 0
    payload = json.loads(json_result.output)
    assert payload["schema_version"] == "impact-eval-product-v1"
    assert payload["primary_comparison"]["outcome"] == "positive_signal"
    assert payload["shareable_for_causal_claims"] is True
    ambient_metrics = {
        item["variant"]: item for item in payload["variant_metrics"]
    }["aiwiki_ambient_memory_workflow"]
    assert ambient_metrics["avg_changed_files"] == 1.0

    output_path = tmp_path / "report.md"
    text_result = runner.invoke(
        app,
        [
            "eval",
            "impact",
            "report",
            "--run-dir",
            str(run_dir),
            "--output",
            str(output_path),
        ],
    )

    assert text_result.exit_code == 0
    assert text_result.output.strip() == str(output_path)
    assert output_path.read_text(encoding="utf-8").startswith(
        "# AI Wiki Impact Eval Product Report"
    )


def test_impact_eval_manifest_describes_run_identity_and_artifacts(
    tmp_path: Path,
) -> None:
    run_dir = _make_run_dir(tmp_path)

    manifest = generate_impact_eval_manifest(run_dir)

    assert manifest["schema_version"] == "impact-eval-run-manifest-v1"
    assert manifest["experiment"] == "scaffold_prompt_workflow_compliance"
    assert manifest["baseline_ref"] == "HEAD^"
    assert manifest["workspace_layout"] == "neutral"
    assert manifest["model"] == "gpt-5.5"
    assert manifest["reasoning_effort"] == "xhigh"
    assert manifest["agent_command"]["command_family"] == "codex exec"
    assert manifest["prompts"] == [{"level": "original", "sha256": "abc123"}]
    assert manifest["confounds"]["shareable_for_causal_claims"] is True
    assert manifest["artifact_summary"]["records"] == 4
    s01 = {slot["slot"]: slot for slot in manifest["slots"]}["s01"]
    assert s01["variant"] == "no_aiwiki_workflow"
    assert s01["workspace"] == "/tmp/workspaces/slots/s01"
    capture = s01["prompt_levels"][0]["captures"][0]
    assert capture["artifacts"]["result"] == "s01/original/first_pass/result.json"
    assert capture["artifacts"]["score"] == "s01/original/score.json"
    assert capture["artifacts"]["final_message"] == (
        "s01/original/first_pass/final_message.md"
    )

    rendered = render_impact_eval_manifest(manifest)
    assert "AI Wiki Impact Eval Run Manifest" in rendered
    assert "HEAD^" in rendered
    assert "codex exec" in rendered
    assert "s01/original/first_pass/result.json" in rendered


def test_eval_impact_manifest_cli_outputs_json_and_writes_text(tmp_path: Path) -> None:
    run_dir = _make_run_dir(tmp_path)

    json_result = runner.invoke(
        app,
        ["eval", "impact", "manifest", "--run-dir", str(run_dir), "--format", "json"],
    )

    assert json_result.exit_code == 0
    payload = json.loads(json_result.output)
    assert payload["schema_version"] == "impact-eval-run-manifest-v1"
    assert payload["baseline_ref"] == "HEAD^"
    assert payload["slots"][1]["variant"] == "aiwiki_ambient_memory_workflow"

    output_path = tmp_path / "manifest.md"
    text_result = runner.invoke(
        app,
        [
            "eval",
            "impact",
            "manifest",
            "--run-dir",
            str(run_dir),
            "--output",
            str(output_path),
        ],
    )

    assert text_result.exit_code == 0
    assert text_result.output.strip() == str(output_path)
    assert output_path.read_text(encoding="utf-8").startswith(
        "# AI Wiki Impact Eval Run Manifest"
    )


def _make_plan_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    _write_text(
        repo_root / "evals" / "impact" / "families" / "ownership_boundary" / "spec.toml",
        "\n".join(
            [
                'name = "ownership_boundary"',
                'prompt_family = "ownership_boundary"',
                'baseline_ref = "34cd5a3^"',
                'historical_issue = "Contributor helpers can drift into package code."',
                "",
                'raw_docs = ["ai-wiki/people/eval/drafts/raw.md"]',
                'consolidated_docs = ["ai-wiki/conventions/package-managed.md"]',
                "",
            ]
        ),
    )
    _write_text(
        repo_root / "evals" / "impact" / "prompts" / "ownership_boundary" / "original.md",
        "Add the contributor workflow helper.\n",
    )
    return repo_root


def _write_retry_loop_evidence(repo_root: Path, *, handle: str = "alice") -> Path:
    repo_wiki = repo_root / "ai-wiki"
    _write_text(
        repo_wiki / "problems" / "retry-loop.md",
        "---\ntitle: Retry Loop\nstatus: draft\n---\n# Retry Loop\n",
    )
    _write_jsonl(
        repo_wiki / "metrics" / "reuse-events" / f"{handle}.jsonl",
        [
            {
                "author_handle": handle,
                "doc_id": "problems/retry-loop",
                "doc_kind": "problems",
                "event_id": "evt_1",
                "evidence_mode": "explicit",
                "observed_at": "2026-05-20T10:00:00+00:00",
                "retrieval_mode": "lookup",
                "reuse_outcome": "resolved",
                "reuse_effects": ["avoided_retry"],
                "schema_version": "reuse-v1",
                "source_task_id": "source-task",
                "task_id": "task-retry",
            }
        ],
    )
    return repo_wiki


def test_discover_impact_eval_families_lists_runnable_specs(tmp_path: Path) -> None:
    repo_root = _make_plan_repo(tmp_path)
    _write_json(
        repo_root / "evals" / "impact" / "rubrics" / "ownership_boundary.json",
        {
            "schema_version": "impact-eval-rubric-v1",
            "success": [{"artifact": "workspace_diff", "contains": "diff --git"}],
        },
    )

    result = discover_impact_eval_families(repo_root=repo_root)

    assert result["schema_version"] == "impact-eval-family-discovery-v1"
    assert result["family_count"] == 1
    family = result["families"][0]
    assert family["name"] == "ownership_boundary"
    assert family["status"] == "runnable"
    assert family["prompt_present"] is True
    assert family["rubric_present"] is True
    assert family["memory_fixtures"]["raw_docs"] == 1
    assert family["next_commands"]["prepare"][-1] == "ownership_boundary"
    assert "ownership_boundary" in render_impact_eval_families(result)


def test_eval_impact_families_cli_outputs_json(tmp_path: Path) -> None:
    repo_root = _make_plan_repo(tmp_path)

    result = runner.invoke(
        app,
        [
            "eval",
            "impact",
            "families",
            "--repo-root",
            str(repo_root),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == "impact-eval-family-discovery-v1"
    assert payload["families"][0]["name"] == "ownership_boundary"


def test_show_impact_eval_family_reports_prompts_and_docs(tmp_path: Path) -> None:
    repo_root = _make_plan_repo(tmp_path)

    result = show_impact_eval_family(family="ownership_boundary", repo_root=repo_root)

    assert result["schema_version"] == "impact-eval-family-detail-v1"
    assert result["family"]["baseline_ref"] == "34cd5a3^"
    assert result["raw_docs"] == ["ai-wiki/people/eval/drafts/raw.md"]
    assert result["prompts"][0]["level"] == "original"
    assert result["prompts"][0]["sha256"]
    assert "AI Wiki Impact Eval Family" in render_impact_eval_family_detail(result)


def test_eval_impact_family_show_cli_outputs_json(tmp_path: Path) -> None:
    repo_root = _make_plan_repo(tmp_path)

    result = runner.invoke(
        app,
        [
            "eval",
            "impact",
            "family",
            "show",
            "ownership_boundary",
            "--repo-root",
            str(repo_root),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == "impact-eval-family-detail-v1"
    assert payload["family"]["name"] == "ownership_boundary"


def test_discover_impact_eval_family_candidates_uses_trial_error_evidence(
    tmp_path: Path,
) -> None:
    repo_root = _make_plan_repo(tmp_path)
    repo_wiki = repo_root / "ai-wiki"
    _write_text(
        repo_wiki / "problems" / "retry-loop.md",
        "---\ntitle: Retry Loop\nstatus: draft\n---\n# Retry Loop\n",
    )
    _write_jsonl(
        repo_wiki / "metrics" / "reuse-events" / "alice.jsonl",
        [
            {
                "author_handle": "alice",
                "doc_id": "problems/retry-loop",
                "doc_kind": "problems",
                "event_id": "evt_1",
                "evidence_mode": "explicit",
                "observed_at": "2026-05-20T10:00:00+00:00",
                "retrieval_mode": "lookup",
                "reuse_outcome": "resolved",
                "reuse_effects": ["avoided_retry"],
                "schema_version": "reuse-v1",
                "source_task_id": "source-task",
                "task_id": "task-retry",
            }
        ],
    )

    result = discover_impact_eval_family_candidates(
        repo_root=repo_root,
        repo_wiki_dir=repo_wiki,
        handle="alice",
    )

    assert result["schema_version"] == "impact-eval-family-candidates-v1"
    assert result["summary"]["candidate_count"] == 1
    candidate = result["candidates"][0]
    assert candidate["doc_id"] == "problems/retry-loop"
    assert candidate["status"] == "candidate"
    assert candidate["readiness"]["missing"] == ["baseline_ref", "prompt", "rubric"]
    assert candidate["evidence"]["trial_error_effects"] == {"avoided_retry": 1}
    assert "retry_loop" in candidate["candidate_id"]
    assert "AI Wiki Impact Eval Family Candidates" in render_impact_eval_family_candidates(result)


def test_eval_impact_family_candidates_cli_outputs_json(tmp_path: Path) -> None:
    repo_root = _make_plan_repo(tmp_path)
    repo_wiki = repo_root / "ai-wiki"
    _write_jsonl(
        repo_wiki / "metrics" / "reuse-events" / "alice.jsonl",
        [
            {
                "author_handle": "alice",
                "doc_id": "problems/retry-loop",
                "doc_kind": "problems",
                "event_id": "evt_1",
                "evidence_mode": "explicit",
                "observed_at": "2026-05-20T10:00:00+00:00",
                "retrieval_mode": "lookup",
                "reuse_outcome": "resolved",
                "reuse_effects": ["blocked_wrong_path"],
                "schema_version": "reuse-v1",
                "source_task_id": "source-task",
                "task_id": "task-retry",
            }
        ],
    )

    result = runner.invoke(
        app,
        [
            "eval",
            "impact",
            "family",
            "candidates",
            "--repo-root",
            str(repo_root),
            "--repo-wiki-dir",
            str(repo_wiki),
            "--handle",
            "alice",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == "impact-eval-family-candidates-v1"
    assert payload["candidates"][0]["doc_id"] == "problems/retry-loop"


def test_refresh_impact_eval_candidate_queue_accumulates_evidence(
    tmp_path: Path,
) -> None:
    repo_root = _make_plan_repo(tmp_path)
    repo_wiki = _write_retry_loop_evidence(repo_root)

    first = refresh_impact_eval_candidate_queue(
        repo_root=repo_root,
        repo_wiki_dir=repo_wiki,
        handle="alice",
    )
    second = refresh_impact_eval_candidate_queue(
        repo_root=repo_root,
        repo_wiki_dir=repo_wiki,
        handle="alice",
    )

    assert first["schema_version"] == "impact-eval-candidate-queue-v1"
    assert first["summary"]["active_count"] == 1
    candidate = second["candidates"][0]
    assert candidate["candidate_id"] == "problems_retry_loop"
    assert candidate["status"] == "candidate"
    assert candidate["seen_count"] == 2
    assert candidate["next_commands"]["draft"][:5] == [
        "aiwiki-toolkit",
        "eval",
        "impact",
        "family",
        "draft",
    ]
    assert Path(second["outputs"]["latest_json"]).exists()
    assert Path(second["outputs"]["latest_markdown"]).exists()
    assert "AI Wiki Impact Eval Candidate Queue" in render_impact_eval_candidate_queue(second)


def test_eval_impact_discover_cli_outputs_managed_queue_json(tmp_path: Path) -> None:
    repo_root = _make_plan_repo(tmp_path)
    repo_wiki = _write_retry_loop_evidence(repo_root)

    result = runner.invoke(
        app,
        [
            "eval",
            "impact",
            "discover",
            "--repo-root",
            str(repo_root),
            "--repo-wiki-dir",
            str(repo_wiki),
            "--handle",
            "alice",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == "impact-eval-candidate-queue-v1"
    assert payload["candidates"][0]["candidate_id"] == "problems_retry_loop"


def test_draft_and_promote_impact_eval_family_candidate(tmp_path: Path) -> None:
    repo_root = _make_plan_repo(tmp_path)
    repo_wiki = _write_retry_loop_evidence(repo_root)
    refresh_impact_eval_candidate_queue(
        repo_root=repo_root,
        repo_wiki_dir=repo_wiki,
        handle="alice",
    )

    draft = draft_impact_eval_family_candidate(
        candidate_id="problems_retry_loop",
        baseline_ref="abc123^",
        repo_root=repo_root,
        repo_wiki_dir=repo_wiki,
    )
    assert draft["schema_version"] == "impact-eval-candidate-draft-v1"
    assert draft["status"] == "ready"
    assert Path(draft["paths"]["spec"]).exists()
    assert Path(draft["paths"]["prompt"]).exists()
    assert Path(draft["paths"]["rubric"]).exists()
    assert "AI Wiki Impact Eval Candidate Draft" in render_impact_eval_candidate_draft_result(
        draft
    )

    check = promote_impact_eval_family_candidate(
        candidate_id="problems_retry_loop",
        repo_root=repo_root,
        repo_wiki_dir=repo_wiki,
    )
    assert check["promotable"] is True
    assert check["apply"] is False
    formal_spec = (
        repo_root
        / "evals"
        / "impact"
        / "families"
        / "problems_retry_loop"
        / "spec.toml"
    )
    assert not formal_spec.exists()

    applied = promote_impact_eval_family_candidate(
        candidate_id="problems_retry_loop",
        repo_root=repo_root,
        repo_wiki_dir=repo_wiki,
        apply=True,
    )
    assert applied["promoted"] is True
    assert formal_spec.exists()
    assert (
        repo_root
        / "evals"
        / "impact"
        / "prompts"
        / "problems_retry_loop"
        / "original.md"
    ).exists()
    assert (
        repo_root / "evals" / "impact" / "rubrics" / "problems_retry_loop.json"
    ).exists()
    assert "AI Wiki Impact Eval Candidate Promotion" in (
        render_impact_eval_candidate_promotion_result(applied)
    )


def test_eval_impact_family_draft_and_promote_cli_outputs_json(tmp_path: Path) -> None:
    repo_root = _make_plan_repo(tmp_path)
    repo_wiki = _write_retry_loop_evidence(repo_root)
    refresh_impact_eval_candidate_queue(
        repo_root=repo_root,
        repo_wiki_dir=repo_wiki,
        handle="alice",
    )

    draft_result = runner.invoke(
        app,
        [
            "eval",
            "impact",
            "family",
            "draft",
            "--candidate",
            "problems_retry_loop",
            "--baseline-ref",
            "abc123^",
            "--repo-root",
            str(repo_root),
            "--repo-wiki-dir",
            str(repo_wiki),
            "--format",
            "json",
        ],
    )
    assert draft_result.exit_code == 0
    draft_payload = json.loads(draft_result.output)
    assert draft_payload["schema_version"] == "impact-eval-candidate-draft-v1"

    promote_result = runner.invoke(
        app,
        [
            "eval",
            "impact",
            "family",
            "promote",
            "--candidate",
            "problems_retry_loop",
            "--repo-root",
            str(repo_root),
            "--repo-wiki-dir",
            str(repo_wiki),
            "--format",
            "json",
        ],
    )
    assert promote_result.exit_code == 0
    promote_payload = json.loads(promote_result.output)
    assert promote_payload["schema_version"] == "impact-eval-candidate-promotion-v1"
    assert promote_payload["promotable"] is True


def test_init_impact_eval_family_from_candidate_writes_scaffold(tmp_path: Path) -> None:
    repo_root = _make_plan_repo(tmp_path)

    result = init_impact_eval_family_from_candidate(
        name="retry-loop",
        from_candidate="problems/retry-loop",
        baseline_ref="abc123^",
        historical_issue="Agents can repeat a known retry-loop failure.",
        repo_root=repo_root,
    )

    assert result["schema_version"] == "impact-eval-family-init-v1"
    assert result["family"] == "retry_loop"
    assert (
        repo_root / "evals" / "impact" / "families" / "retry_loop" / "spec.toml"
    ).exists()
    assert (
        repo_root / "evals" / "impact" / "prompts" / "retry_loop" / "original.md"
    ).exists()
    assert (repo_root / "evals" / "impact" / "rubrics" / "retry_loop.json").exists()
    assert "AI Wiki Impact Eval Family Init" in render_impact_eval_family_init_result(result)


def test_eval_impact_family_init_cli_outputs_json(tmp_path: Path) -> None:
    repo_root = _make_plan_repo(tmp_path)

    result = runner.invoke(
        app,
        [
            "eval",
            "impact",
            "family",
            "init",
            "--name",
            "retry-loop",
            "--from-candidate",
            "problems/retry-loop",
            "--baseline-ref",
            "abc123^",
            "--repo-root",
            str(repo_root),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == "impact-eval-family-init-v1"
    assert payload["family"] == "retry_loop"


def test_impact_eval_run_plan_describes_next_orchestrator_step(tmp_path: Path) -> None:
    repo_root = _make_plan_repo(tmp_path)

    plan = generate_impact_eval_run_plan(
        family="ownership_boundary",
        repo_root=repo_root,
        workspace_root=tmp_path / "workspaces",
        output_root=tmp_path / "runs",
        run_label="run_test",
    )

    assert plan["schema_version"] == "impact-eval-run-plan-v1"
    assert plan["family_spec"]["baseline_ref"] == "34cd5a3^"
    assert plan["execution"]["auto_invokes_agent"] is False
    assert plan["workspace"]["run_dir"] == str(tmp_path / "runs" / "run_test")
    assert plan["comparison"]["primary"] == [
        "no_aiwiki_workflow",
        "aiwiki_ambient_memory_workflow",
    ]
    assert plan["prompts"][0]["level"] == "original"
    assert plan["prompts"][0]["sha256"]
    assert plan["commands"]["prepare_variants"][:4] == [
        "uv",
        "run",
        "python",
        "evals/impact/scripts/prepare_variants.py",
    ]
    assert "--baseline-ref" in plan["commands"]["prepare_variants"]
    assert plan["commands"]["run_slots"][0][-1] == "original"

    rendered = render_impact_eval_run_plan(plan)
    assert "AI Wiki Impact Eval Run Plan" in rendered
    assert "Auto-invokes agent: `no`" in rendered
    assert "prepare_variants.py" in rendered
    assert "eval impact score" in rendered


def test_eval_impact_plan_cli_outputs_json_and_writes_text(tmp_path: Path) -> None:
    repo_root = _make_plan_repo(tmp_path)

    json_result = runner.invoke(
        app,
        [
            "eval",
            "impact",
            "plan",
            "--family",
            "ownership_boundary",
            "--repo-root",
            str(repo_root),
            "--workspace-root",
            str(tmp_path / "workspaces"),
            "--output-root",
            str(tmp_path / "runs"),
            "--run-label",
            "run_test",
            "--format",
            "json",
        ],
    )

    assert json_result.exit_code == 0
    payload = json.loads(json_result.output)
    assert payload["schema_version"] == "impact-eval-run-plan-v1"
    assert payload["commands"]["manual_capture_template"][:4] == [
        "aiwiki-toolkit",
        "eval",
        "impact",
        "capture",
    ]
    assert payload["commands"]["manual_score_template"][:4] == [
        "aiwiki-toolkit",
        "eval",
        "impact",
        "score",
    ]
    assert payload["commands"]["post_run"][-1][:4] == [
        "aiwiki-toolkit",
        "eval",
        "impact",
        "report",
    ]

    output_path = tmp_path / "plan.md"
    text_result = runner.invoke(
        app,
        [
            "eval",
            "impact",
            "plan",
            "--family",
            "ownership_boundary",
            "--repo-root",
            str(repo_root),
            "--output",
            str(output_path),
        ],
    )

    assert text_result.exit_code == 0
    assert text_result.output.strip() == str(output_path)
    assert output_path.read_text(encoding="utf-8").startswith(
        "# AI Wiki Impact Eval Run Plan"
    )


def _write_prepared_metadata(command: list[str]) -> None:
    output_root = Path(command[command.index("--output-root") + 1])
    run_label = command[command.index("--run-label") + 1]
    workspace_root = Path(command[command.index("--workspace-root") + 1])
    run_dir = output_root / run_label
    _write_json(
        run_dir / "metadata.json",
        {
            "schema_version": 2,
            "experiment": command[command.index("--experiment") + 1],
            "workspace_root": str(workspace_root),
            "variants": ["s01", "s02"],
            "prompt_levels": ["original"],
            "prompt_hashes": {"original": "prepared-hash"},
            "created_at": "2026-05-21T10:00:00",
            "primary_comparison": [
                "no_aiwiki_workflow",
                "aiwiki_ambient_memory_workflow",
            ],
            "diagnostic_variants": [],
            "model_family": command[command.index("--model-family") + 1],
            "reasoning_effort": command[command.index("--reasoning-effort") + 1],
            "execution_surface": command[command.index("--execution-surface") + 1],
            "assignment": {
                "baseline_ref": "34cd5a3^",
                "workspace_layout": "neutral",
                "slots": [
                    {
                        "slot": "s01",
                        "variant": "no_aiwiki_workflow",
                        "workspace": str(workspace_root / "slots" / "s01"),
                    },
                    {
                        "slot": "s02",
                        "variant": "aiwiki_ambient_memory_workflow",
                        "workspace": str(workspace_root / "slots" / "s02"),
                    },
                ],
            },
        },
    )


def test_prepare_impact_eval_run_executes_prepare_and_init_then_writes_manifest(
    monkeypatch,
    tmp_path: Path,
) -> None:
    repo_root = _make_plan_repo(tmp_path)
    calls: list[list[str]] = []

    def fake_run(command: list[str], **kwargs):
        calls.append(command)
        if command[1].endswith("init_run.py"):
            _write_prepared_metadata(command)
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="ok\n",
            stderr="",
        )

    monkeypatch.setattr("ai_wiki_toolkit.impact_eval.subprocess.run", fake_run)

    result = prepare_impact_eval_run(
        family="ownership_boundary",
        repo_root=repo_root,
        workspace_root=tmp_path / "workspaces",
        output_root=tmp_path / "runs",
        run_label="run_test",
    )

    assert result["schema_version"] == "impact-eval-prepare-result-v1"
    assert result["run_dir"] == str(tmp_path / "runs" / "run_test")
    assert result["commands"][0]["name"] == "prepare_variants"
    assert result["commands"][1]["name"] == "init_run"
    assert calls[0][1].endswith("prepare_variants.py")
    assert calls[1][1].endswith("init_run.py")
    assert (tmp_path / "runs" / "run_test" / "manifest.json").exists()
    assert (tmp_path / "runs" / "run_test" / "manifest.md").exists()

    rendered = render_impact_eval_prepare_result(result)
    assert "AI Wiki Impact Eval Prepare Result" in rendered
    assert "run_test" in rendered
    assert "prepare_variants.py" in rendered


def test_eval_impact_prepare_cli_outputs_json(monkeypatch, tmp_path: Path) -> None:
    fake_result = {
        "schema_version": "impact-eval-prepare-result-v1",
        "family": "ownership_boundary",
        "workspace_root": str(tmp_path / "workspaces"),
        "run_dir": str(tmp_path / "runs" / "run_test"),
        "manifest": {
            "json": str(tmp_path / "runs" / "run_test" / "manifest.json"),
            "markdown": str(tmp_path / "runs" / "run_test" / "manifest.md"),
            "schema_version": "impact-eval-run-manifest-v1",
        },
        "commands": [],
        "plan": {},
        "next_steps": [],
    }

    monkeypatch.setattr("ai_wiki_toolkit.cli.prepare_impact_eval_run", lambda **_: fake_result)

    result = runner.invoke(
        app,
        [
            "eval",
            "impact",
            "prepare",
            "--family",
            "ownership_boundary",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == "impact-eval-prepare-result-v1"
    assert payload["manifest"]["schema_version"] == "impact-eval-run-manifest-v1"


def test_run_impact_eval_single_slot_runs_scores_validates_and_bundles(
    monkeypatch,
    tmp_path: Path,
) -> None:
    repo_root = _make_plan_repo(tmp_path)
    run_dir = _make_empty_run_dir(tmp_path)
    calls = _install_fake_autorun_scripts(monkeypatch)

    result = run_impact_eval(
        run_dir=run_dir,
        slots=("s01",),
        prompt_level="original",
        codex_bin="fake-codex",
        sleep_guard=False,
        export_sessions=False,
        validate=True,
        score_policy="command-exit",
        repo_root=repo_root,
    )

    assert result["schema_version"] == "impact-eval-run-result-v1"
    assert result["slots"] == ["s01"]
    assert result["runner_success"] is True
    assert result["score_results"][0]["label"] == "success"
    assert result["validation"]["shareable_for_causal_claims"] is True
    assert result["report"]["primary_comparison"]["outcome"] == "incomplete"
    assert (run_dir / "report_bundle" / "impact-report.json").exists()
    assert calls[0][1].endswith("run_cli_slots.py")
    assert calls[0][calls[0].index("--slots") + 1] == "s01"
    assert "--no-sleep-guard" in calls[0]

    rendered = render_impact_eval_run_result(result)
    assert "AI Wiki Impact Eval Run Result" in rendered
    assert "Score policy: `command-exit`" in rendered


def test_run_impact_eval_all_slots_exports_sessions_and_reports_primary_signal(
    monkeypatch,
    tmp_path: Path,
) -> None:
    repo_root = _make_plan_repo(tmp_path)
    run_dir = _make_empty_run_dir(tmp_path)
    sessions_root = tmp_path / "sessions"
    sessions_root.mkdir()
    calls = _install_fake_autorun_scripts(monkeypatch, fail_s01=True)

    result = run_impact_eval(
        run_dir=run_dir,
        all_slots=True,
        prompt_level="original",
        codex_bin="fake-codex",
        sleep_guard=False,
        export_sessions=True,
        validate=True,
        score_policy="command-exit",
        sessions_root=sessions_root,
        repo_root=repo_root,
    )

    assert result["slots"] == ["s01", "s02", "s03"]
    assert result["runner_success"] is False
    assert result["report"]["primary_comparison"]["outcome"] == "positive_signal"
    labels = {item["slot"]: item["label"] for item in result["score_results"]}
    assert labels == {"s01": "fail", "s02": "success", "s03": "success"}
    assert result["commands"]["export_sessions"]["returncode"] == 0
    assert result["bundle"]["primary_comparison"]["outcome"] == "positive_signal"
    run_command = calls[0]
    assert run_command[1].endswith("run_cli_slots.py")
    assert run_command[run_command.index("--slots") + 1] == "s01,s02,s03"
    assert any(call[1].endswith("export_codex_sessions.py") for call in calls)


def test_run_impact_eval_rubric_score_policy_writes_judgment_artifact(
    monkeypatch,
    tmp_path: Path,
) -> None:
    repo_root = _make_plan_repo(tmp_path)
    run_dir = _make_empty_run_dir(tmp_path)
    _install_fake_autorun_scripts(monkeypatch)
    rubric_path = tmp_path / "rubric.json"
    _write_json(
        rubric_path,
        {
            "schema_version": "impact-eval-rubric-v1",
            "name": "test-rubric",
            "success": [
                {
                    "id": "captures-diff",
                    "artifact": "workspace_diff",
                    "contains": "diff --git",
                    "description": "The run captured a workspace diff.",
                }
            ],
            "partial": [],
            "fail": [
                {
                    "id": "package-churn",
                    "artifact": "changed_files",
                    "changed_file_prefix": "src/ai_wiki_toolkit/",
                    "description": "Package surface churn is forbidden for this test rubric.",
                }
            ],
        },
    )

    result = run_impact_eval(
        run_dir=run_dir,
        slots=("s01",),
        prompt_level="original",
        codex_bin="fake-codex",
        sleep_guard=False,
        export_sessions=False,
        validate=True,
        score_policy="rubric",
        rubric_path=rubric_path,
        repo_root=repo_root,
    )

    assert result["score_policy"] == "rubric"
    assert result["score_results"][0]["label"] == "success"
    judgment = result["score_results"][0]["rubric_judgment"]
    assert judgment["schema_version"] == "impact-eval-rubric-judgment-v1"
    assert judgment["criteria"]["success"][0]["matched"] is True
    assert (run_dir / "s01" / "original" / "rubric_judgment.json").exists()
    score = json.loads((run_dir / "s01" / "original" / "score.json").read_text())
    assert score["rubric_refs"] == [str(rubric_path)]
    assert "rubric_judgment.json" in score["evidence"][0]


def test_run_impact_eval_benchmark_prepares_runs_and_bundles(
    monkeypatch,
    tmp_path: Path,
) -> None:
    repo_root = _make_plan_repo(tmp_path)
    calls = _install_fake_autorun_scripts(monkeypatch)

    result = run_impact_eval_benchmark(
        family="ownership_boundary",
        repo_root=repo_root,
        workspace_root=tmp_path / "workspaces",
        output_root=tmp_path / "runs",
        run_label="run_test",
        codex_bin="fake-codex",
        sleep_guard=False,
        export_sessions=False,
        validate=True,
        score_policy="command-exit",
    )

    assert result["schema_version"] == "impact-eval-benchmark-result-v1"
    assert result["run_dir"] == str(tmp_path / "runs" / "run_test")
    assert result["runner_success"] is True
    assert result["run"]["slots"] == ["s01", "s02"]
    assert result["run"]["score_results"][0]["label"] == "success"
    assert (tmp_path / "runs" / "run_test" / "report_bundle" / "run-result.json").exists()
    assert calls[0][1].endswith("prepare_variants.py")
    assert calls[1][1].endswith("init_run.py")
    assert calls[2][1].endswith("run_cli_slots.py")
    assert "AI Wiki Impact Eval Benchmark Result" in render_impact_eval_benchmark_result(result)


def test_eval_impact_benchmark_cli_outputs_json(monkeypatch, tmp_path: Path) -> None:
    fake_result = {
        "schema_version": "impact-eval-benchmark-result-v1",
        "family": "ownership_boundary",
        "run_dir": str(tmp_path / "runs" / "run_test"),
        "workspace_root": str(tmp_path / "workspaces"),
        "score_policy": "none",
        "runner_success": True,
        "prepare": {},
        "run": {},
        "report": {"primary_comparison": {"outcome": "neutral_signal"}},
        "bundle": {},
        "next_steps": [],
    }
    monkeypatch.setattr("ai_wiki_toolkit.cli.run_impact_eval_benchmark", lambda **_: fake_result)

    result = runner.invoke(
        app,
        [
            "eval",
            "impact",
            "benchmark",
            "--family",
            "ownership_boundary",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == "impact-eval-benchmark-result-v1"
    assert payload["runner_success"] is True


def test_generate_impact_eval_schedule_report_writes_latest(tmp_path: Path) -> None:
    repo_root = _make_plan_repo(tmp_path)
    repo_wiki = _write_retry_loop_evidence(repo_root)

    result = generate_impact_eval_schedule_report(
        repo_root=repo_root,
        repo_wiki_dir=repo_wiki,
        period_id="2026-W21",
        handle="alice",
        candidate_max_items=25,
    )

    assert result["schema_version"] == "impact-eval-schedule-report-v1"
    assert result["period_id"] == "2026-W21"
    assert result["summary"]["formal_family_count"] == 1
    assert result["summary"]["candidate_status_counts"]["candidate"] == 1
    assert result["candidate_filters"]["handle"] == "alice"
    assert result["candidate_filters"]["max_items"] == 25
    assert Path(result["outputs"]["json"]).exists()
    assert Path(result["outputs"]["markdown"]).exists()
    assert Path(result["outputs"]["latest_json"]).exists()
    assert Path(result["outputs"]["latest_markdown"]).exists()
    assert "AI Wiki Impact Eval Schedule Report" in render_impact_eval_schedule_report(
        result
    )


def test_run_impact_eval_schedule_records_index_and_report(
    monkeypatch,
    tmp_path: Path,
) -> None:
    repo_root = _make_plan_repo(tmp_path)
    repo_wiki = _write_retry_loop_evidence(repo_root)
    calls: list[dict] = []

    def fake_benchmark(**kwargs):
        calls.append(kwargs)
        family = kwargs["family"]
        return {
            "schema_version": "impact-eval-benchmark-result-v1",
            "family": family,
            "run_dir": str(tmp_path / "runs" / family),
            "workspace_root": str(tmp_path / "workspaces" / family),
            "score_policy": kwargs["score_policy"],
            "runner_success": True,
            "prepare": {},
            "run": {},
            "report": {
                "primary_comparison": {
                    "outcome": "positive_signal",
                    "first_attempt_success_delta": 1.0,
                    "avg_score_delta": 1.0,
                },
                "records": [{"slot": "s01"}],
            },
            "bundle": {"dir": str(tmp_path / "bundle" / family)},
        }

    monkeypatch.setattr(
        "ai_wiki_toolkit.impact_eval.run_impact_eval_benchmark",
        fake_benchmark,
    )

    result = run_impact_eval_schedule(
        repo_root=repo_root,
        repo_wiki_dir=repo_wiki,
        families=("ownership_boundary",),
        period_id="2026-W21",
        handle="alice",
        candidate_max_items=25,
        score_policy="command-exit",
        export_sessions=False,
        validate=False,
    )

    assert result["schema_version"] == "impact-eval-schedule-run-v1"
    assert result["status"] == "ran"
    assert calls[0]["family"] == "ownership_boundary"
    assert calls[0]["prompt_levels"] == ("original",)
    assert result["run_index"]["run_count"] == 1
    assert result["report"]["summary"]["indexed_run_count"] == 1
    assert result["report"]["candidate_filters"]["handle"] == "alice"
    assert result["report"]["candidate_filters"]["max_items"] == 25
    assert Path(result["run_index"]["path"]).exists()
    assert "AI Wiki Impact Eval Schedule Run" in render_impact_eval_schedule_run_result(
        result
    )

    skipped = run_impact_eval_schedule(
        repo_root=repo_root,
        repo_wiki_dir=repo_wiki,
        families=("ownership_boundary",),
        period_id="2026-W21",
        if_due=True,
        handle="alice",
        candidate_max_items=25,
        score_policy="command-exit",
    )
    assert skipped["status"] == "skipped"
    assert len(calls) == 1


def test_eval_impact_schedule_report_cli_outputs_json(tmp_path: Path) -> None:
    repo_root = _make_plan_repo(tmp_path)
    repo_wiki = _write_retry_loop_evidence(repo_root)

    result = runner.invoke(
        app,
        [
            "eval",
            "impact",
            "schedule",
            "report",
            "--repo-root",
            str(repo_root),
            "--repo-wiki-dir",
            str(repo_wiki),
            "--period-id",
            "2026-W21",
            "--handle",
            "alice",
            "--candidate-max-items",
            "25",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == "impact-eval-schedule-report-v1"
    assert payload["period_id"] == "2026-W21"
    assert payload["candidate_filters"]["handle"] == "alice"
    assert payload["candidate_filters"]["max_items"] == 25


def test_eval_impact_schedule_run_cli_outputs_json(monkeypatch, tmp_path: Path) -> None:
    repo_root = _make_plan_repo(tmp_path)
    repo_wiki = _write_retry_loop_evidence(repo_root)
    fake_result = {
        "schema_version": "impact-eval-schedule-run-v1",
        "status": "ran",
        "period_id": "2026-W21",
        "families": ["ownership_boundary"],
        "runs": [],
        "run_index": {"path": str(tmp_path / "index.json"), "run_count": 1},
        "report": {"summary": {}},
    }
    captured_kwargs: dict = {}

    def fake_schedule(**kwargs):
        captured_kwargs.update(kwargs)
        return fake_result

    monkeypatch.setattr("ai_wiki_toolkit.cli.run_impact_eval_schedule", fake_schedule)

    result = runner.invoke(
        app,
        [
            "eval",
            "impact",
            "schedule",
            "run",
            "--family",
            "ownership_boundary",
            "--repo-root",
            str(repo_root),
            "--repo-wiki-dir",
            str(repo_wiki),
            "--period-id",
            "2026-W21",
            "--handle",
            "alice",
            "--candidate-max-items",
            "25",
            "--score-policy",
            "command-exit",
            "--skip-export-sessions",
            "--no-validate",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == "impact-eval-schedule-run-v1"
    assert payload["status"] == "ran"
    assert captured_kwargs["handle"] == "alice"
    assert captured_kwargs["candidate_max_items"] == 25


def test_eval_impact_run_cli_outputs_json(monkeypatch, tmp_path: Path) -> None:
    run_dir = _make_empty_run_dir(tmp_path)
    fake_result = {
        "schema_version": "impact-eval-run-result-v1",
        "run_dir": str(run_dir),
        "slots": ["s01"],
        "prompt_level": "original",
        "codex_bin": "codex",
        "sleep_guard": False,
        "score_policy": "none",
        "runner_success": True,
        "runner_returncode": 0,
        "manifest": {},
        "commands": {"run": {}, "export_sessions": None, "validate": None, "score": []},
        "score_results": [],
        "validation": None,
        "report": None,
    }

    monkeypatch.setattr("ai_wiki_toolkit.cli.run_impact_eval", lambda **_: fake_result)

    result = runner.invoke(
        app,
        [
            "eval",
            "impact",
            "run",
            "--run-dir",
            str(run_dir),
            "--slot",
            "s01",
            "--skip-export-sessions",
            "--no-validate",
            "--no-report",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == "impact-eval-run-result-v1"


def test_capture_impact_eval_result_infers_slot_metadata_and_refreshes_manifest(
    monkeypatch,
    tmp_path: Path,
) -> None:
    repo_root = _make_plan_repo(tmp_path)
    run_dir = _make_run_dir(tmp_path)
    calls: list[list[str]] = []

    def fake_run(command: list[str], **kwargs):
        calls.append(command)
        result_dir = (
            Path(command[command.index("--run-dir") + 1])
            / command[command.index("--slot") + 1]
            / command[command.index("--prompt-level") + 1]
            / command[command.index("--phase") + 1]
        )
        _write_json(
            result_dir / "result.json",
            {
                "schema_version": 2,
                "slot": command[command.index("--slot") + 1],
                "variant": command[command.index("--variant") + 1],
                "prompt_level": command[command.index("--prompt-level") + 1],
                "phase": command[command.index("--phase") + 1],
                "attempt": 1,
                "human_nudges": 0,
                "first_pass_success": True,
                "changed_files": ["src/ai_wiki_toolkit/example.py"],
                "untracked_files": [],
            },
        )
        _write_text(result_dir / "workspace_diff.patch", "diff --git a/example b/example\n")
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=str(result_dir) + "\n",
            stderr="",
        )

    monkeypatch.setattr("ai_wiki_toolkit.impact_eval.subprocess.run", fake_run)

    result = capture_impact_eval_result(
        run_dir=run_dir,
        slot="s01",
        prompt_level="original",
        repo_root=repo_root,
        first_pass_success=True,
    )

    assert result["schema_version"] == "impact-eval-capture-result-v1"
    assert result["variant"] == "no_aiwiki_workflow"
    assert result["workspace"].replace("\\", "/").endswith("/tmp/workspaces/slots/s01")
    assert result["artifacts"]["result"].replace("\\", "/").endswith(
        "s01/original/first_pass/result.json"
    )
    assert result["manifest"]["schema_version"] == "impact-eval-run-manifest-v1"
    assert (run_dir / "manifest.json").exists()
    assert calls[0][1].endswith("save_result.py")
    assert calls[0][calls[0].index("--variant") + 1] == "no_aiwiki_workflow"

    rendered = render_impact_eval_capture_result(result)
    assert "AI Wiki Impact Eval Capture Result" in rendered
    assert "no_aiwiki_workflow" in rendered


def test_validate_impact_eval_run_executes_script_and_refreshes_manifest(
    monkeypatch,
    tmp_path: Path,
) -> None:
    repo_root = _make_plan_repo(tmp_path)
    run_dir = _make_run_dir(tmp_path)

    def fake_run(command: list[str], **kwargs):
        confounds_path = Path(command[command.index("--run-dir") + 1]) / "confounds.json"
        _write_json(
            confounds_path,
            {
                "schema_version": 2,
                "shareable_for_causal_claims": False,
                "critical_confounds": [{"kind": "missing_session_manifest"}],
                "warnings": [],
            },
        )
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=str(confounds_path) + "\nCritical confounds: 1\n",
            stderr="",
        )

    monkeypatch.setattr("ai_wiki_toolkit.impact_eval.subprocess.run", fake_run)

    result = validate_impact_eval_run(run_dir=run_dir, repo_root=repo_root)

    assert result["schema_version"] == "impact-eval-validate-result-v1"
    assert result["shareable_for_causal_claims"] is False
    assert result["critical_confounds"] == 1
    assert (run_dir / "manifest.md").exists()

    rendered = render_impact_eval_validate_result(result)
    assert "AI Wiki Impact Eval Validate Result" in rendered
    assert "Critical confounds: `1`" in rendered


def test_score_impact_eval_result_executes_script_and_refreshes_manifest(
    monkeypatch,
    tmp_path: Path,
) -> None:
    repo_root = _make_plan_repo(tmp_path)
    run_dir = _make_run_dir(tmp_path)

    def fake_run(command: list[str], **kwargs):
        score_path = (
            Path(command[command.index("--run-dir") + 1])
            / command[command.index("--slot") + 1]
            / command[command.index("--prompt-level") + 1]
            / "score.json"
        )
        _write_json(
            score_path,
            {
                "schema_version": 2,
                "slot": command[command.index("--slot") + 1],
                "prompt_level": command[command.index("--prompt-level") + 1],
                "label": command[command.index("--label") + 1],
                "rubric_refs": [],
                "evidence": [],
            },
        )
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=str(score_path) + "\n",
            stderr="",
        )

    monkeypatch.setattr("ai_wiki_toolkit.impact_eval.subprocess.run", fake_run)

    result = score_impact_eval_result(
        run_dir=run_dir,
        slot="s01",
        prompt_level="original",
        label="partial",
        evidence=("s01/original/first_pass/workspace_diff.patch",),
        repo_root=repo_root,
    )

    assert result["schema_version"] == "impact-eval-score-result-v1"
    assert result["label"] == "partial"
    assert Path(result["score_path"]).parts[-3:] == ("s01", "original", "score.json")
    assert result["manifest"]["schema_version"] == "impact-eval-run-manifest-v1"

    rendered = render_impact_eval_score_result(result)
    assert "AI Wiki Impact Eval Score Result" in rendered
    assert "partial" in rendered


def test_eval_impact_capture_validate_and_score_cli_output_json(
    monkeypatch,
    tmp_path: Path,
) -> None:
    run_dir = _make_run_dir(tmp_path)

    monkeypatch.setattr(
        "ai_wiki_toolkit.cli.capture_impact_eval_result",
        lambda **_: {
            "schema_version": "impact-eval-capture-result-v1",
            "run_dir": str(run_dir),
            "slot": "s01",
            "variant": "no_aiwiki_workflow",
            "manifest": {},
            "command": {},
        },
    )
    capture = runner.invoke(
        app,
        [
            "eval",
            "impact",
            "capture",
            "--run-dir",
            str(run_dir),
            "--slot",
            "s01",
            "--first-pass-success",
            "--format",
            "json",
        ],
    )
    assert capture.exit_code == 0
    assert json.loads(capture.output)["schema_version"] == "impact-eval-capture-result-v1"

    monkeypatch.setattr(
        "ai_wiki_toolkit.cli.validate_impact_eval_run",
        lambda **_: {
            "schema_version": "impact-eval-validate-result-v1",
            "run_dir": str(run_dir),
            "critical_confounds": 0,
            "warnings": 0,
            "manifest": {},
            "command": {},
        },
    )
    validate = runner.invoke(
        app,
        [
            "eval",
            "impact",
            "validate",
            "--run-dir",
            str(run_dir),
            "--format",
            "json",
        ],
    )
    assert validate.exit_code == 0
    assert json.loads(validate.output)["schema_version"] == "impact-eval-validate-result-v1"

    monkeypatch.setattr(
        "ai_wiki_toolkit.cli.score_impact_eval_result",
        lambda **_: {
            "schema_version": "impact-eval-score-result-v1",
            "run_dir": str(run_dir),
            "slot": "s01",
            "prompt_level": "original",
            "label": "success",
            "manifest": {},
            "command": {},
        },
    )
    score = runner.invoke(
        app,
        [
            "eval",
            "impact",
            "score",
            "--run-dir",
            str(run_dir),
            "--slot",
            "s01",
            "--label",
            "success",
            "--format",
            "json",
        ],
    )
    assert score.exit_code == 0
    assert json.loads(score.output)["schema_version"] == "impact-eval-score-result-v1"


def test_impact_eval_summary_classifies_success_and_diagnostic_quality_signals(
    tmp_path: Path,
) -> None:
    positive_run = _make_run_dir(
        tmp_path,
        name="positive",
        experiment="scaffold_prompt_workflow_compliance",
    )
    neutral_run = _make_run_dir(
        tmp_path,
        name="neutral",
        experiment="postinstall_archive_staging",
    )
    _write_result(
        neutral_run,
        slot="s01",
        variant="no_aiwiki_workflow",
        score="success",
        first_pass_success=True,
        changed_files=["npm/install.js", "tests/test_npm_wrapper.py"],
    )
    _write_result(
        neutral_run,
        slot="s02",
        variant="aiwiki_ambient_memory_workflow",
        score="success",
        first_pass_success=True,
        changed_files=[
            "npm/install.js",
            "tests/test_npm_wrapper.py",
            "ai-wiki/_toolkit/metrics/task-stats.json",
            "ai-wiki/metrics/reuse-events/alice.jsonl",
        ],
        untracked_files=["ai-wiki/metrics/reuse-events/alice.jsonl"],
    )
    _write_result(
        neutral_run,
        slot="s03",
        variant="aiwiki_linked_raw_only",
        score="success",
        first_pass_success=True,
        changed_files=[
            "npm/install.js",
            "tests/test_npm_wrapper.py",
            "ai-wiki/people/alice/drafts/postinstall.md",
        ],
        untracked_files=["ai-wiki/people/alice/drafts/postinstall.md"],
    )

    summary = generate_impact_eval_summary((positive_run, neutral_run))
    payload = impact_eval_summary_to_dict(summary)

    assert payload["total_runs"] == 2
    assert payload["shareable_runs"] == 2
    by_experiment = {item["experiment"]: item for item in payload["runs"]}
    assert (
        by_experiment["scaffold_prompt_workflow_compliance"]["product_signal"]
        == "success_uplift"
    )
    assert (
        by_experiment["postinstall_archive_staging"]["product_signal"]
        == "diagnostic_quality_signal"
    )
    assert (
        by_experiment["postinstall_archive_staging"][
            "avg_project_changed_files_delta"
        ]
        == 0.0
    )
    assert (
        by_experiment["postinstall_archive_staging"][
            "avg_managed_wiki_changed_files_delta"
        ]
        == 2.0
    )
    assert (
        by_experiment["postinstall_archive_staging"][
            "diagnostic_avg_user_wiki_changed_files"
        ]
        == 1.0
    )

    rendered = render_impact_eval_summary(summary)
    assert "AI Wiki Impact Eval Cross-Run Summary" in rendered
    assert "success_uplift" in rendered
    assert "diagnostic_quality_signal" in rendered


def test_eval_impact_summarize_cli_accepts_runs_file_and_outputs_json(
    tmp_path: Path,
) -> None:
    positive_run = _make_run_dir(tmp_path, name="positive")
    neutral_run = _make_run_dir(
        tmp_path,
        name="neutral",
        experiment="postinstall_archive_staging",
    )
    _write_result(
        neutral_run,
        slot="s01",
        variant="no_aiwiki_workflow",
        score="success",
        first_pass_success=True,
    )
    _write_result(
        neutral_run,
        slot="s02",
        variant="aiwiki_ambient_memory_workflow",
        score="success",
        first_pass_success=True,
    )
    runs_file = tmp_path / "runs.json"
    _write_json(
        runs_file,
        {
            "runs": [
                {"run_dir": str(positive_run)},
                {"run_dir": str(neutral_run)},
            ]
        },
    )

    result = runner.invoke(
        app,
        [
            "eval",
            "impact",
            "summarize",
            "--runs-file",
            str(runs_file),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == "impact-eval-cross-run-summary-v1"
    assert payload["total_runs"] == 2
    assert payload["product_signal_counts"]["success_uplift"] == 1
