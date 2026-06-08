from __future__ import annotations

import json
from pathlib import Path
import subprocess

from typer.testing import CliRunner

from ai_wiki_toolkit.cli import app
from ai_wiki_toolkit.route import (
    _applies_when_adjustment,
    generate_route_packet,
    _route_intent_signals,
    _split_applies_when,
    _task_tokens,
)
from helpers import strip_margin

runner = CliRunner()


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_route_generates_context_packet_with_cited_sources(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    convention_path = (
        repo_env["repo"]
        / "ai-wiki"
        / "conventions"
        / "package-managed-vs-user-owned-docs.md"
    )
    convention_path.write_text(
        strip_margin(
            """
            ---
            title: "Package-managed vs user-owned docs"
            ---
            # Package-Managed Vs User-Owned Docs

            ## Rule

            Put evolving package-controlled guidance in `ai-wiki/_toolkit/**`.
            Keep user-owned docs stable unless a contributor intentionally edits them.
            Do not rewrite user-owned AI wiki docs during install.
            """
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "Update scaffold prompt routing without overwriting user-owned AI wiki docs.",
            "--changed-path",
            "src/ai_wiki_toolkit/content.py",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    assert packet["schema_version"] == "route-v1"
    assert packet["actor"]["handle"] == "alice"
    assert packet["route"]["task_type"] == "scaffold_prompt_workflow"
    assert "user_owned_docs" in packet["route"]["guardrail_tags"]
    assert "managed_prompt_block" in packet["route"]["guardrail_tags"]

    must_load_ids = {doc["doc_id"] for doc in packet["must_load"]}
    assert "constraints" in must_load_ids
    assert "conventions/package-managed-vs-user-owned-docs" in must_load_ids
    cards = {card["doc_id"]: card for card in packet["index_cards"]}
    assert cards["constraints"]["selection_reason_type"] == "safety_guardrail"

    rules = packet["must_follow"]
    assert rules
    assert all(rule["source"].startswith("ai-wiki/") for rule in rules)
    assert any(
        rule["rule"] == "Do not rewrite user-owned AI wiki docs during install."
        and rule["source"] == "ai-wiki/conventions/package-managed-vs-user-owned-docs.md"
        for rule in rules
    )
    success_items = packet["success_criteria"]["items"]
    assert packet["success_criteria"]["source"] == "generated_from_task_signals"
    assert any(
        item["criterion"] == (
            "Managed prompt, scaffold, or toolkit changes stay inside package-owned surfaces."
        )
        for item in success_items
    )
    assert any(
        "conventions/package-managed-vs-user-owned-docs" in item["verification"]
        for item in success_items
    )
    assert any(
        item["criterion"] == (
            "User-owned AI wiki content is not rewritten as a package side effect."
        )
        for item in success_items
    )


def test_route_packet_includes_index_cards_for_runtime_references(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    convention_path = (
        repo_env["repo"]
        / "ai-wiki"
        / "conventions"
        / "package-managed-vs-user-owned-docs.md"
    )
    convention_path.write_text(
        strip_margin(
            """
            ---
            title: "Package-managed vs user-owned docs"
            short_description: "Keep package-generated guidance separate from repo-owned notes."
            applies_when: "Task touches scaffold, install, prompt, or routing behavior."
            ---
            # Package-Managed Vs User-Owned Docs

            Do not rewrite user-owned AI wiki docs during install.
            """
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "Update scaffold routing without changing user-owned docs.",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    assert packet["context_budget"]["policy"] == "safety_cap_not_fill_target"
    assert packet["routing_strategy"]["mode"] == "index_cards_with_runtime_references"

    cards = {card["doc_id"]: card for card in packet["index_cards"]}
    card = cards["conventions/package-managed-vs-user-owned-docs"]
    assert card["short_description"] == (
        "Keep package-generated guidance separate from repo-owned notes."
    )
    assert card["routing_hint"] == "Task touches scaffold, install, prompt, or routing behavior."
    assert card["reference_path"] == "ai-wiki/conventions/package-managed-vs-user-owned-docs.md"
    assert card["load_mode"] == "required_context"


def test_route_applies_when_negative_boundary_does_not_boost_excluded_stage(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    broad_eval_path = (
        repo_env["repo"]
        / "ai-wiki"
        / "people"
        / "alice"
        / "drafts"
        / "route-usefulness-eval.md"
    )
    broad_eval_path.write_text(
        strip_margin(
            """
            ---
            title: "Route usefulness eval"
            short_description: "Evaluate route selected memories against actual reuse."
            applies_when: "Evaluate route usefulness when comparing route-selected memories against actual reuse, misses, and noisy selections; not for ordinary route invocation or general wiki reuse dashboards."
            ---
            # Route Usefulness Eval

            Compare selected memories with downstream reuse events.
            """
        ),
        encoding="utf-8",
    )
    specific_path = (
        repo_env["repo"]
        / "ai-wiki"
        / "conventions"
        / "route-invocation-dashboards.md"
    )
    specific_path.write_text(
        strip_margin(
            """
            ---
            title: "Route invocation dashboards"
            short_description: "Use for ordinary route invocation and general wiki reuse dashboards."
            ---
            # Route Invocation Dashboards

            Prefer this doc when reviewing ordinary route invocation and wiki reuse dashboards.
            """
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "Review ordinary route invocation and general wiki reuse dashboards.",
            "--max-docs",
            "1",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    assert packet["index_cards"][0]["doc_id"] == "conventions/route-invocation-dashboards"

    applies_when = _split_applies_when(
        "Evaluate route usefulness when comparing route-selected memories against actual reuse, "
        "misses, and noisy selections; not for ordinary route invocation or general wiki reuse "
        "dashboards."
    )
    adjustment, reasons, signal = _applies_when_adjustment(
        applies_when=applies_when,
        task_tokens=_task_tokens("Review ordinary route invocation and general wiki reuse dashboards."),
    )
    assert adjustment < 0
    assert signal["negative_matches"]
    assert any("negative boundary penalty" in reason for reason in reasons)


def test_route_applies_when_requires_action_stage_alignment(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    broad_capture_path = (
        repo_env["repo"]
        / "ai-wiki"
        / "people"
        / "alice"
        / "drafts"
        / "aaa-impact-eval-capture.md"
    )
    broad_capture_path.write_text(
        strip_margin(
            """
            ---
            title: "Impact eval capture"
            short_description: "Use for impact eval artifact capture and result files."
            applies_when: "Fix impact-eval artifact capture when saved run results must include untracked files."
            ---
            # Impact Eval Capture

            Impact eval artifact capture result files.
            """
        ),
        encoding="utf-8",
    )
    prompt_design_path = (
        repo_env["repo"]
        / "ai-wiki"
        / "people"
        / "alice"
        / "drafts"
        / "zzz-impact-eval-prompt-design.md"
    )
    prompt_design_path.write_text(
        strip_margin(
            """
            ---
            title: "Impact eval prompt design"
            short_description: "Use for impact eval prompt design."
            applies_when: "Design impact-eval task prompts when comparing memory variants."
            ---
            # Impact Eval Prompt Design

            Impact eval prompt design.
            """
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "Design impact-eval task prompts for memory variant comparison.",
            "--max-docs",
            "1",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    assert packet["index_cards"][0]["doc_id"] == (
        "people/alice/drafts/zzz-impact-eval-prompt-design"
    )
    assert packet["route"]["eval_stage"]["active"] is True
    assert packet["route"]["eval_stage"]["primary"] == "prompt_design"
    intent_signals = packet["route"]["intent_signals"]
    assert "design" in intent_signals["alignment_tokens"]
    assert "prompts" in intent_signals["alignment_tokens"]

    applies_when = _split_applies_when(
        "Fix impact-eval artifact capture when saved run results must include untracked files."
    )
    raw_tokens = _task_tokens(
        "Design impact-eval task prompts for memory variant comparison.",
        filter_stopwords=False,
    )
    task_tokens = _task_tokens("Design impact-eval task prompts for memory variant comparison.")
    adjustment, reasons, signal = _applies_when_adjustment(
        applies_when=applies_when,
        task_tokens=task_tokens,
        route_intent=_route_intent_signals(
            "Design impact-eval task prompts for memory variant comparison.",
            raw_task_tokens=raw_tokens,
            task_tokens=task_tokens,
        ),
    )
    assert adjustment < 0
    assert signal["positive_alignment_tokens"]
    assert not signal["positive_alignment_matches"]
    assert any("action/stage mismatch" in reason for reason in reasons)


def test_route_stage_compatible_selector_filters_adjacent_eval_stage_docs(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0
    repo_wiki = repo_env["repo"] / "ai-wiki"
    capture_doc = repo_wiki / "people" / "alice" / "drafts" / "impact-eval-result-capture.md"
    capture_doc.parent.mkdir(parents=True, exist_ok=True)
    capture_doc.write_text(
        strip_margin(
            """
            ---
            title: "Impact eval result capture"
            short_description: "Use for impact eval artifact capture and untracked result files."
            ---
            # Impact Eval Result Capture

            Impact eval artifact capture preserves result files, untracked files, and workspace diff evidence.
            """
        ),
        encoding="utf-8",
    )
    prompt_doc = repo_wiki / "people" / "alice" / "drafts" / "impact-eval-prompts.md"
    prompt_doc.write_text(
        strip_margin(
            """
            ---
            title: "Impact eval prompts"
            short_description: "Use for impact eval prompt design and task family prompts."
            ---
            # Impact Eval Prompts

            Impact eval prompt design covers task family prompt variants and rubric framing.
            """
        ),
        encoding="utf-8",
    )

    result = generate_route_packet(
        task="Fix impact eval result capture so untracked artifact files are saved.",
        max_docs=2,
        stage_compatible_doc_slots=True,
        start=repo_env["repo"],
    )

    packet = result.packet
    assert packet["route"]["eval_stage"]["primary"] == "artifact_capture"
    selected_ids = {
        card["doc_id"]
        for card in packet["index_cards"]
        if card.get("selection_reason_type")
    }
    assert "people/alice/drafts/impact-eval-result-capture" in selected_ids
    assert "people/alice/drafts/impact-eval-prompts" not in selected_ids
    assert packet["routing_strategy"]["selector"]["stage_compatible_doc_slots_required"] is True


def test_route_eval_stage_soft_scoring_demotes_adjacent_stage_to_maybe_load(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0
    repo_wiki = repo_env["repo"] / "ai-wiki"
    manifest_doc = repo_wiki / "people" / "alice" / "drafts" / "zzz-eval-run-manifest.md"
    manifest_doc.parent.mkdir(parents=True, exist_ok=True)
    manifest_doc.write_text(
        strip_margin(
            """
            ---
            title: "Eval run manifest"
            short_description: "Use for eval run manifest and runner workspace setup."
            ---
            # Eval Run Manifest

            Eval run manifest runner workspace setup defines slot mappings and run artifacts.
            """
        ),
        encoding="utf-8",
    )
    prompt_doc = repo_wiki / "people" / "alice" / "drafts" / "aaa-impact-eval-prompts.md"
    prompt_doc.write_text(
        strip_margin(
            """
            ---
            title: "Impact eval prompts"
            short_description: "Use for impact eval prompt design and task family prompts."
            ---
            # Impact Eval Prompts

            Impact eval prompt design covers task family prompt variants and rubric framing.
            """
        ),
        encoding="utf-8",
    )

    result = generate_route_packet(
        task="Design the eval run manifest for runner workspaces.",
        max_docs=1,
        eval_stage_scoring_mode="soft",
        start=repo_env["repo"],
    )

    packet = result.packet
    assert packet["route"]["eval_stage"]["primary"] == "manifest_or_runner"
    selected_cards = [
        card for card in packet["index_cards"] if card.get("selection_reason_type")
    ]
    assert selected_cards[0]["doc_id"] == "people/alice/drafts/zzz-eval-run-manifest"
    assert selected_cards[0]["eval_stage_signal"]["relation"] == "primary_stage_match"
    maybe_ids = {doc["doc_id"] for doc in packet["maybe_load"]}
    assert "people/alice/drafts/aaa-impact-eval-prompts" in maybe_ids
    maybe_prompt = next(
        doc
        for doc in packet["maybe_load"]
        if doc["doc_id"] == "people/alice/drafts/aaa-impact-eval-prompts"
    )
    assert maybe_prompt["eval_stage_signal"]["relation"] == "adjacent_eval_stage"


def test_route_classifies_simple_pr_tasks_as_low_effort(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "Push PR.",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    assert packet["route"]["effort"] == "low"
    assert packet["context_budget"]["effective_max_docs"] <= 3
    assert packet["success_criteria"]["items"][0]["criterion"] == (
        "The requested operation completes without pulling in unrelated work."
    )


def test_route_prioritizes_eval_workflow_over_generic_agent_terms(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            (
                "Project A coding-agent impact eval: add rubrics, register run index, "
                "and rerun Codex benchmark diagnostics."
            ),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    assert packet["route"]["task_type"] == "eval_workflow"
    assert any(
        item["criterion"] == "Eval output is reproducible and exposes the primary product signal."
        for item in packet["success_criteria"]["items"]
    )


def test_route_expands_chinese_task_terms_for_eval_routing(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0
    repo_wiki = repo_env["repo"] / "ai-wiki"
    doc_path = repo_wiki / "people" / "alice" / "drafts" / "route-eval-replay-rubric.md"
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(
        strip_margin(
            """
            ---
            title: "Route eval replay rubric"
            short_description: "Use for route evaluation replay rubric diagnostics."
            ---
            # Route Eval Replay Rubric

            Route evaluation replay reports need benchmark scoring and rubric diagnostics.
            """
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "为 aiwiki-toolkit 设计路由评估回放和评分诊断命令，先要计划不要代码",
            "--max-docs",
            "6",
            "--no-record-trace",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    assert packet["route"]["task_type"] == "eval_workflow"
    assert "task_evaluation" in packet["route"]["domain_tags"]
    language_signals = packet["route"]["language_signals"]
    assert language_signals["contains_cjk"] is True
    assert "replay" in language_signals["expanded_tokens"]
    assert any(
        "回放" in signal["matched_terms"]
        for signal in language_signals["chinese_synonyms"]
    )
    assert any(
        card["doc_id"] == "people/alice/drafts/route-eval-replay-rubric"
        for card in packet["index_cards"]
    )
    assert packet["route"]["mode"]["name"] == "plan"
    assert "edit_files" in packet["route"]["mode"]["disallowed_actions"]
    assert packet["behavior_contract"]["recognized_mode"] == "plan"


def test_route_does_not_treat_mentioned_code_bug_fix_label_as_intent(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "我觉得你要搞清楚为什么他当时是按照 code/bug_fix 走 然后才能正确的修复这个问题",
            "--no-record-trace",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    assert packet["route"]["task_type"] == "memory_governance"
    assert packet["route"]["mode"]["name"] == "plan"
    assert packet["behavior_contract"]["recognized_mode"] == "plan"
    assert "edit_files" in packet["behavior_contract"]["disallowed_actions"]
    mentioned = packet["route"]["mentioned_labels"]
    assert mentioned["labels"] == ["bug_fix", "code"]
    assert {"bug", "fix", "code"} <= set(mentioned["ignored_intent_tokens"])
    audit = packet["route"]["route_self_audit"]
    assert audit["status"] == "ok"
    assert any(
        observation["type"] == "mentioned_label_excluded_from_intent"
        for observation in audit["observations"]
    )
    assert not any(
        item["criterion"] == "The reported bug is reproduced or its failure mode is explicitly identified."
        for item in packet["success_criteria"]["items"]
    )


def test_route_plan_mode_arbitrates_bug_fix_task_type_for_planning_only_prompt(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "不要直接实现，先研究 router 为什么把 planning-only prompt 误判成 code/bug_fix，然后给出修复计划",
            "--no-record-trace",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    assert packet["route"]["mode"]["name"] == "plan"
    assert packet["route"]["task_type"] == "memory_governance"
    assert packet["behavior_contract"]["recognized_mode"] == "plan"
    assert "edit_files" in packet["behavior_contract"]["disallowed_actions"]
    audit = packet["route"]["route_self_audit"]
    assert audit["status"] == "ok"
    assert "mode_task_type_conflict" not in audit["flags"]


def test_route_does_not_trigger_fixed_workflow_from_broad_chinese_verify_synonym(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            (
                "先做 Codex runtime capability test，验证 route packet 能不能真的让 Codex "
                "进入 plan/code/validate/git/push 这些行为边界。这个比继续调 scorer 更优先。"
            ),
            "--no-record-trace",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    assert packet["route"]["task_type"] == "memory_governance"
    assert packet["route"]["workflow_contract"] is None
    assert packet["route"]["mode"]["name"] != "fixed_workflow"
    assert packet["behavior_contract"]["workflow_contract_id"] is None
    audit = packet["route"]["route_self_audit"]
    assert audit["status"] == "ok"
    assert "weak_workflow_trigger" not in audit["flags"]


def test_route_self_audit_flags_synthetic_mode_task_type_conflict() -> None:
    from ai_wiki_toolkit.route import _build_route_self_audit

    audit = _build_route_self_audit(
        task_type="bug_fix",
        route_mode={"name": "plan"},
        workflow_contract=None,
        mentioned_labels={"labels": [], "ignored_intent_tokens": [], "evidence": []},
        intent_signals={"mode": "analysis", "alignment_tokens": ["fix", "planning"]},
        task_tokens={"fix", "planning"},
        selected=[],
    )

    assert audit["status"] == "suspicious"
    assert "mode_task_type_conflict" in audit["flags"]
    assert audit["recommended_action"] == "record_taxonomy_evidence"
    assert audit["taxonomy_evidence_candidate"]["signal_type"] == "unknown_task_language"


def test_route_uses_fixed_workflow_contract_before_adjacent_design_docs(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0
    noisy_doc = (
        repo_env["repo"]
        / "ai-wiki"
        / "people"
        / "alice"
        / "drafts"
        / "weekly-report-eval-design.md"
    )
    noisy_doc.write_text(
        strip_margin(
            """
            ---
            title: "Weekly report eval design"
            short_description: "Use for weekly report eval product design and metrics."
            ---
            # Weekly Report Eval Design

            Weekly report eval product design metrics are adjacent to report diagnostics.
            """
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "Generate the weekly report with coverage promotion noisy diagnosis telemetry provenance.",
            "--max-docs",
            "3",
            "--no-record-trace",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    assert packet["route"]["mode"]["name"] == "fixed_workflow"
    assert packet["route"]["workflow_contract"]["id"] == "weekly-report-diagnostics"
    assert packet["behavior_contract"]["workflow_contract_id"] == "weekly-report-diagnostics"
    assert "load local metrics" in packet["behavior_contract"]["workflow_steps_to_follow"]
    assert packet["routing_strategy"]["selector"]["fixed_workflow_without_support"] is True
    selected_ids = {card["doc_id"] for card in packet["index_cards"]}
    assert "people/alice/drafts/weekly-report-eval-design" not in selected_ids


def test_route_fixed_workflow_can_select_primary_bucket_supporting_docs(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0
    release_doc = (
        repo_env["repo"]
        / "ai-wiki"
        / "people"
        / "alice"
        / "drafts"
        / "release-assets.md"
    )
    release_doc.write_text(
        strip_margin(
            """
            ---
            title: "Release assets"
            short_description: "Use for npm release package assets and distribution checks."
            ---
            # Release Assets

            Verify npm release assets, package distribution, and published version checks.
            """
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "push current changes and release a new version",
            "--max-docs",
            "3",
            "--no-record-trace",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    assert packet["route"]["mode"]["name"] == "fixed_workflow"
    assert packet["route"]["workflow_contract"]["id"] == "release-flow"
    selector = packet["routing_strategy"]["selector"]
    assert selector["fixed_workflow_without_support"] is True
    assert selector["workflow_contract_selection_mode"] == (
        "contract_with_supporting_doc_retrieval"
    )
    selected_ids = {card["doc_id"] for card in packet["index_cards"]}
    assert "people/alice/drafts/release-assets" in selected_ids
    assert "workflows" not in selected_ids


def test_route_bucket_selector_covers_release_and_eval_mixed_intent(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0
    repo_wiki = repo_env["repo"] / "ai-wiki"
    release_doc = repo_wiki / "problems" / "zzz-npm-release-package.md"
    release_doc.parent.mkdir(parents=True, exist_ok=True)
    release_doc.write_text(
        strip_margin(
            """
            ---
            title: "NPM release package"
            short_description: "Use for npm release package publish verification."
            ---
            # NPM Release Package

            Release distribution package publish verification keeps npm assets aligned.
            """
        ),
        encoding="utf-8",
    )
    eval_doc = repo_wiki / "people" / "alice" / "drafts" / "aaa-eval-report-quality.md"
    eval_doc.parent.mkdir(parents=True, exist_ok=True)
    eval_doc.write_text(
        strip_margin(
            """
            ---
            title: "Eval report quality"
            short_description: "Use for impact eval report quality metrics."
            ---
            # Eval Report Quality

            Impact eval report quality metrics cover neutral score and change profile.
            """
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "Implement npm release package verification, then add impact eval report quality metrics.",
            "--max-docs",
            "2",
            "--no-record-trace",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    bucket_ids = {bucket["id"] for bucket in packet["route"]["intent_buckets"]}
    assert "release_distribution" in bucket_ids
    assert "report_quality" in bucket_ids
    selected = {card["doc_id"]: card for card in packet["index_cards"]}
    assert "problems/zzz-npm-release-package" in selected
    assert "people/alice/drafts/aaa-eval-report-quality" in selected
    assert selected["problems/zzz-npm-release-package"]["selected_bucket_id"] == (
        "release_distribution"
    )
    assert selected["people/alice/drafts/aaa-eval-report-quality"]["selected_bucket_id"] == (
        "report_quality"
    )


def test_route_phase_plan_shadow_outputs_plan_read_only_for_no_code_prompt(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "只要计划，不要实现：解释 route phase_plan 应该怎么设计。",
            "--no-record-trace",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    phase_plan = packet["phase_plan"]
    current_phase = phase_plan["current_phase"]
    assert phase_plan["status"] == "shadow"
    assert phase_plan["replaces_intent_buckets"] is False
    assert current_phase["id"] == "plan"
    assert current_phase["agent_surface_mode"] == "plan"
    assert "edit_files" in current_phase["permissions"]["disallowed_actions"]
    assert current_phase["next_phase_inputs"]["reroute_policy"] == (
        "regenerate_after_current_phase"
    )
    assert "current_phase_result" in current_phase["next_phase_inputs"]["required_inputs"]


def test_route_phase_plan_orders_compound_prompt_without_replacing_buckets(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0
    repo_wiki = repo_env["repo"] / "ai-wiki"
    release_doc = repo_wiki / "problems" / "npm-release-package.md"
    release_doc.parent.mkdir(parents=True, exist_ok=True)
    release_doc.write_text(
        strip_margin(
            """
            ---
            title: "NPM release package"
            short_description: "Use for npm release package publish verification."
            ---
            # NPM Release Package

            Release distribution package publish verification keeps npm assets aligned.
            """
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "Plan the npm release package change, then implement it, run tests, commit locally, but do not push.",
            "--max-docs",
            "3",
            "--no-record-trace",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    phase_plan = packet["phase_plan"]
    phase_ids = [phase["id"] for phase in phase_plan["phases"]]
    assert phase_plan["status"] == "shadow"
    assert phase_plan["replaces_intent_buckets"] is False
    assert phase_ids == ["plan", "code", "validate", "git"]
    assert "push" not in phase_ids
    assert packet["route"]["intent_buckets"]
    assert packet["routing_strategy"]["phase_plan"]["mode"] == "shadow"
    assert packet["behavior_contract"]["current_phase_id"] == "plan"


def test_route_phase_plan_wraps_fixed_workflow_contract_current_phase(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "Generate the weekly report with coverage promotion noisy diagnosis telemetry provenance.",
            "--max-docs",
            "3",
            "--no-record-trace",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    current_phase = packet["phase_plan"]["current_phase"]
    assert current_phase["id"] == "workflow"
    assert current_phase["agent_surface_mode"] == "code"
    assert current_phase["workflow_contract_id"] == "weekly-report-diagnostics"
    assert "workflow_contract" in current_phase["intent_bucket_ids"]
    assert "follow_workflow_contract" in current_phase["permissions"]["allowed_actions"]


def test_route_keeps_broad_chinese_assessment_out_of_eval_workflow(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "评估一下这个设计想法是否合理，先不要写代码",
            "--no-record-trace",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    assert packet["route"]["task_type"] != "eval_workflow"
    assert "task_evaluation" not in packet["route"]["domain_tags"]
    language_signals = packet["route"]["language_signals"]
    assert language_signals["contains_cjk"] is True
    assert "eval" not in language_signals["expanded_tokens"]


def test_route_expands_chinese_route_precision_terms_for_memory_routing(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "优化记忆路由的噪音、漏选和召回 precision，先看 scorer",
            "--no-record-trace",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    assert packet["route"]["task_type"] == "memory_governance"
    assert "memory_governance" in packet["route"]["domain_tags"]
    language_signals = packet["route"]["language_signals"]
    assert {"noise", "precision", "recall", "route"} <= set(
        language_signals["expanded_tokens"]
    )


def test_route_does_not_treat_local_changes_as_ownership_boundary_signal(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "用户确认当前 AI Wiki 行为符合预期，要求把当前本地 changes 都 push 到云端 repo",
            "--max-docs",
            "3",
            "--no-record-trace",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    assert packet["route"]["task_type"] == "general"
    assert "user_owned_docs" not in packet["route"]["guardrail_tags"]
    selected_doc_ids = {card["doc_id"] for card in packet["index_cards"][:3]}
    assert "workflows" in selected_doc_ids


def test_route_multi_signal_scorer_protects_release_docs_in_eval_tasks(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0
    repo_wiki = repo_env["repo"] / "ai-wiki"
    release_doc = repo_wiki / "problems" / "npm-release-workflow-package.md"
    release_doc.parent.mkdir(parents=True, exist_ok=True)
    release_doc.write_text(
        strip_margin(
            """
            ---
            title: "NPM release workflow package"
            short_description: "Use when release package publish workflow behavior changes."
            ---
            # NPM Release Workflow Package

            Release distribution work must keep npm package publish and workflow behavior aligned.
            """
        ),
        encoding="utf-8",
    )
    eval_doc = repo_wiki / "people" / "alice" / "drafts" / "impact-eval-replay.md"
    eval_doc.parent.mkdir(parents=True, exist_ok=True)
    eval_doc.write_text(
        strip_margin(
            """
            ---
            title: "Impact eval replay"
            short_description: "Use for impact eval replay report and rubric work."
            ---
            # Impact Eval Replay

            Impact eval replay report tasks need rubric scoring diagnostics.
            """
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "Run impact eval replay rubric diagnostics, then fix npm release package publish workflow.",
            "--max-docs",
            "10",
            "--no-record-trace",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    assert packet["route"]["task_type"] == "eval_workflow"
    assert "release_distribution" in packet["route"]["domain_tags"]
    cards = {card["doc_id"]: card for card in packet["index_cards"]}
    assert "problems/npm-release-workflow-package" in cards
    release_card = cards["problems/npm-release-workflow-package"]
    assert "route tag signal release_distribution protected doc" in release_card["reason"]
    assert release_card["multi_signal_adjustment"] > 0
    assert any(
        item["route_tag"] == "release_distribution"
        and item["adjustment"] > 0
        for item in release_card["multi_signal"]["items"]
    )


def test_route_reranks_top_index_cards_by_card_specificity(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0
    repo_wiki = repo_env["repo"] / "ai-wiki"
    noisy_doc = repo_wiki / "people" / "alice" / "drafts" / "aaa-body-only-note.md"
    focused_doc = repo_wiki / "people" / "alice" / "drafts" / "zzz-card-selection.md"
    noisy_doc.parent.mkdir(parents=True, exist_ok=True)
    noisy_doc.write_text(
        strip_margin(
            """
            ---
            title: "Internal Note"
            short_description: "General implementation note."
            ---
            # Internal Note

            Route reranker precision index card selection should improve routing.
            """
        ),
        encoding="utf-8",
    )
    focused_doc.write_text(
        strip_margin(
            """
            ---
            title: "Card Selection"
            short_description: "Choose focused cards for route precision."
            ---
            # Card Selection

            Focused card selection.
            """
        ),
        encoding="utf-8",
    )

    disabled_result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "Improve route reranker precision index card selection.",
            "--max-docs",
            "3",
            "--rerank-top",
            "0",
            "--no-record-trace",
            "--format",
            "json",
        ],
    )
    enabled_result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "Improve route reranker precision index card selection.",
            "--max-docs",
            "3",
            "--rerank-top",
            "10",
            "--no-record-trace",
            "--format",
            "json",
        ],
    )

    assert disabled_result.exit_code == 0
    assert enabled_result.exit_code == 0
    disabled_packet = json.loads(disabled_result.output)
    enabled_packet = json.loads(enabled_result.output)
    assert disabled_packet["routing_strategy"]["reranker"]["enabled"] is False
    assert enabled_packet["routing_strategy"]["reranker"]["enabled"] is True
    assert enabled_packet["index_cards"][0]["doc_id"] == (
        "people/alice/drafts/zzz-card-selection"
    )
    cards = {card["doc_id"]: card for card in enabled_packet["index_cards"]}
    assert cards["people/alice/drafts/zzz-card-selection"]["rerank_adjustment"] > 0
    assert cards["people/alice/drafts/aaa-body-only-note"]["rerank_adjustment"] < 0
    assert "card reranker" in cards["people/alice/drafts/zzz-card-selection"]["reason"]


def test_route_does_not_let_auto_git_status_paths_pollute_specific_tasks(
    repo_env: dict[str, Path],
) -> None:
    subprocess.run(["git", "init"], cwd=repo_env["repo"], check=True, capture_output=True)
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0
    workflow_path = repo_env["repo"] / ".github" / "workflows" / "release.yml"
    workflow_path.parent.mkdir(parents=True, exist_ok=True)
    workflow_path.write_text("name: release\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "-N", ".github/workflows/release.yml"],
        cwd=repo_env["repo"],
        check=True,
        capture_output=True,
    )

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "Improve route precision for memory retrieval.",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    assert ".github/workflows/release.yml" in packet["route"]["changed_paths"]
    assert packet["route"]["changed_path_signal_source"] == "git_status"
    assert packet["route"]["changed_path_signal_used"] is False
    assert packet["route"]["task_type"] == "memory_governance"
    assert "release_distribution" not in packet["route"]["domain_tags"]
    assert "ci_workflow" not in packet["route"]["domain_tags"]


def test_route_uses_explicit_changed_paths_as_task_signals(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "Review the change.",
            "--changed-path",
            ".github/workflows/release.yml",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    assert packet["route"]["changed_path_signal_source"] == "explicit"
    assert packet["route"]["changed_path_signal_used"] is True
    assert packet["route"]["task_type"] == "release_distribution"
    assert "release_distribution" in packet["route"]["domain_tags"]


def test_route_penalizes_historically_not_helpful_selected_docs(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0
    repo_wiki = repo_env["repo"] / "ai-wiki"

    noisy_doc = repo_wiki / "people" / "alice" / "drafts" / "aaa-route-precision-noisy.md"
    useful_doc = repo_wiki / "people" / "alice" / "drafts" / "zzz-route-precision-useful.md"
    noisy_doc.parent.mkdir(parents=True, exist_ok=True)
    shared_doc_text = strip_margin(
        """
        ---
        title: "Route precision eval workflow report"
        short_description: "Improve route precision for eval workflow report tasks."
        ---
        # Route Precision Eval Workflow Report

        Route precision eval workflow report tasks need focused routing evidence.
        """
    )
    noisy_doc.write_text(shared_doc_text, encoding="utf-8")
    useful_doc.write_text(shared_doc_text, encoding="utf-8")

    noisy_doc_id = "people/alice/drafts/aaa-route-precision-noisy"
    useful_doc_id = "people/alice/drafts/zzz-route-precision-useful"
    task_ids = [f"old-route-noise-{index}" for index in range(3)]
    _write_jsonl(
        repo_wiki / "metrics" / "route-traces" / "alice.jsonl",
        [
            {
                "schema_version": "route-trace-v1",
                "trace_id": f"rt_test_{index}",
                "routed_at": f"2026-06-03T10:0{index}:00+00:00",
                "author_handle": "alice",
                "task_id": task_id,
                "task_type": "eval_workflow",
                "effort": "deep",
                "domain_tags": ["task_evaluation"],
                "selected_doc_ids": [noisy_doc_id],
                "must_load_doc_ids": [],
                "index_card_doc_ids": [noisy_doc_id],
                "maybe_load_doc_ids": [],
                "skipped_doc_ids": [],
                "packet_words": 120,
                "selected_doc_count": 1,
                "index_card_count": 1,
                "maybe_load_count": 0,
                "must_load_count": 0,
            }
            for index, task_id in enumerate(task_ids)
        ],
    )
    _write_jsonl(
        repo_wiki / "metrics" / "reuse-events" / "alice.jsonl",
        [
            {
                "schema_version": "reuse-v1",
                "event_id": f"evt_test_{index}",
                "observed_at": f"2026-06-03T10:1{index}:00+00:00",
                "author_handle": "alice",
                "task_id": task_id,
                "doc_id": noisy_doc_id,
                "doc_kind": "draft",
                "retrieval_mode": "preloaded",
                "evidence_mode": "explicit",
                "reuse_outcome": "not_helpful",
            }
            for index, task_id in enumerate(task_ids)
        ],
    )

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "Improve route precision eval workflow report.",
            "--max-docs",
            "2",
            "--no-record-trace",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    cards = {card["doc_id"]: card for card in packet["index_cards"]}
    assert packet["index_cards"][0]["doc_id"] == useful_doc_id
    assert cards[useful_doc_id]["route_quality_adjustment"] == 0
    assert cards[noisy_doc_id]["route_quality_adjustment"] == -6
    assert "route not-helpful penalty: -6 from 3" in cards[noisy_doc_id]["reason"]


def test_route_unused_penalty_is_support_aware(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0
    repo_wiki = repo_env["repo"] / "ai-wiki"

    supported_doc_id = "people/alice/drafts/aaa-supported-good"
    noisy_doc_id = "people/alice/drafts/zzz-supported-noisy"
    shared_doc_text = strip_margin(
        """
        ---
        title: "Tuning Evidence"
        short_description: "Useful selection evidence."
        ---
        # Tuning Evidence

        Route quality precision tuning should use support-aware usefulness evidence.
        """
    )
    for doc_id in (supported_doc_id, noisy_doc_id):
        doc_path = repo_wiki / f"{doc_id}.md"
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_text(shared_doc_text, encoding="utf-8")

    trace_rows: list[dict[str, object]] = []
    reuse_rows: list[dict[str, object]] = []
    for index in range(20):
        for doc_id, prefix in ((supported_doc_id, "supported"), (noisy_doc_id, "noisy")):
            task_id = f"{prefix}-support-aware-{index}"
            trace_rows.append(
                {
                    "schema_version": "route-trace-v1",
                    "trace_id": f"rt_{task_id}",
                    "routed_at": f"2026-06-03T11:{index:02d}:00+00:00",
                    "author_handle": "alice",
                    "task_id": task_id,
                    "task_type": "eval_workflow",
                    "effort": "deep",
                    "domain_tags": ["task_evaluation"],
                    "selected_doc_ids": [doc_id],
                    "must_load_doc_ids": [],
                    "index_card_doc_ids": [doc_id],
                    "maybe_load_doc_ids": [],
                    "skipped_doc_ids": [],
                    "packet_words": 120,
                    "selected_doc_count": 1,
                    "index_card_count": 1,
                    "maybe_load_count": 0,
                    "must_load_count": 0,
                }
            )
            useful_cutoff = 10 if doc_id == supported_doc_id else 1
            if index < useful_cutoff:
                reuse_rows.append(
                    {
                        "schema_version": "reuse-v1",
                        "event_id": f"evt_{task_id}",
                        "observed_at": f"2026-06-03T11:{index:02d}:30+00:00",
                        "author_handle": "alice",
                        "task_id": task_id,
                        "doc_id": doc_id,
                        "doc_kind": "draft",
                        "retrieval_mode": "preloaded",
                        "evidence_mode": "explicit",
                        "reuse_outcome": "resolved",
                    }
                )
    _write_jsonl(repo_wiki / "metrics" / "route-traces" / "alice.jsonl", trace_rows)
    _write_jsonl(repo_wiki / "metrics" / "reuse-events" / "alice.jsonl", reuse_rows)

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "Improve route quality precision tuning.",
            "--max-docs",
            "10",
            "--no-record-trace",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    cards = {card["doc_id"]: card for card in packet["index_cards"]}
    assert cards[supported_doc_id]["route_quality_adjustment"] == -2
    supported_signal = cards[supported_doc_id]["route_quality_signal"]
    assert supported_signal["selected_count"] == 20
    assert supported_signal["selected_useful_count"] == 10
    assert supported_signal["selected_precision"] == 0.5
    assert supported_signal["unused_penalty"] == 2
    assert supported_signal["unused_penalty_capped_by_support"] is True
    assert "unused-selection penalty capped by support: 10/20" in cards[supported_doc_id]["reason"]
    assert cards[noisy_doc_id]["route_quality_adjustment"] < 0
    noisy_signal = cards[noisy_doc_id]["route_quality_signal"]
    assert noisy_signal["selected_precision"] == 0.05
    assert noisy_signal["unused_penalty"] > supported_signal["unused_penalty"]
    assert "support 1/20 useful selections" in cards[noisy_doc_id]["reason"]


def test_route_text_packet_is_agent_readable(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "Diagnose a failing release smoke workflow.",
            "--changed-path",
            ".github/workflows/release.yml",
            "--max-docs",
            "3",
        ],
    )

    assert result.exit_code == 0
    assert "# AI Wiki Context Packet" in result.output
    assert "Task Type: `release_distribution`" in result.output
    assert "## Index Cards" in result.output
    assert "## Success Criteria" in result.output
    assert "Release and distribution behavior stays aligned across published targets." in result.output
    assert "Context Safety Cap:" in result.output
    assert "Actor: `alice`" in result.output
    assert "## Must Load" in result.output
    assert "## Trust Model" in result.output


def test_route_packet_includes_matching_work_context(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0
    capture_result = runner.invoke(
        app,
        [
            "work",
            "capture",
            "--work-id",
            "framework-ledger",
            "--title",
            "Build routeable work ledger",
            "--status",
            "processing",
            "--link",
            "ai-wiki/people/alice/drafts/framework-roadmap.md",
            "--occurred-at",
            "2026-04-27T10:00:00+10:00",
            "--handle",
            "alice",
        ],
    )
    assert capture_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "Continue the framework ledger work.",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    assert packet["work_context"]["source"] == "ai-wiki/_toolkit/work/state.json"
    assert packet["work_context"]["items"][0]["work_id"] == "framework-ledger"
    assert packet["work_context"]["items"][0]["status"] == "processing"
    assert packet["work_context"]["items"][0]["assignee_handles"] == ["alice"]
    assert packet["work_context"]["items"][0]["actor_relation"] == "assignee"
    assert packet["work_context"]["items"][0]["links"] == [
        "ai-wiki/people/alice/drafts/framework-roadmap.md"
    ]

    text_result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "Continue the framework ledger work.",
        ],
    )
    assert text_result.exit_code == 0
    assert "## Work Context" in text_result.output
    assert "`framework-ledger`" in text_result.output
    assert "relation `assignee`" in text_result.output


def test_route_packet_auto_includes_current_actor_work(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "bob"])
    assert install_result.exit_code == 0
    capture_result = runner.invoke(
        app,
        [
            "work",
            "capture",
            "--work-id",
            "bob-active-task",
            "--title",
            "Build Bob's assigned implementation",
            "--status",
            "active",
            "--assignee",
            "bob",
            "--handle",
            "bob",
        ],
    )
    assert capture_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "What should I work on next?",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    assert packet["actor"]["handle"] == "bob"
    assert packet["work_context"]["actor_handle"] == "bob"
    assert packet["work_context"]["items"][0]["work_id"] == "bob-active-task"
    assert packet["work_context"]["items"][0]["actor_relation"] == "assignee"


def test_route_packet_does_not_auto_include_other_assignees_work(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "bob"])
    assert install_result.exit_code == 0
    capture_result = runner.invoke(
        app,
        [
            "work",
            "capture",
            "--work-id",
            "alice-active-task",
            "--title",
            "Build Alice's assigned implementation",
            "--status",
            "active",
            "--assignee",
            "alice",
            "--handle",
            "alice",
        ],
    )
    assert capture_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "What should I work on next?",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    assert packet["actor"]["handle"] == "bob"
    assert packet["work_context"]["items"] == []


def test_route_packet_can_show_directly_requested_other_assignees_work(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "bob"])
    assert install_result.exit_code == 0
    capture_result = runner.invoke(
        app,
        [
            "work",
            "capture",
            "--work-id",
            "alice-active-task",
            "--title",
            "Build Alice's assigned implementation",
            "--status",
            "active",
            "--assignee",
            "alice",
            "--handle",
            "alice",
        ],
    )
    assert capture_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "Inspect alice-active-task before planning team handoff.",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    assert packet["actor"]["handle"] == "bob"
    assert packet["work_context"]["items"][0]["work_id"] == "alice-active-task"
    assert packet["work_context"]["items"][0]["actor_relation"] == "none"
    assert "assigned to another handle" in packet["work_context"]["items"][0]["reason"]


def test_route_requires_initialized_repo_wiki(repo_env: dict[str, Path]) -> None:
    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "Update prompt routing.",
        ],
    )

    assert result.exit_code == 1
    assert "Run `aiwiki-toolkit install` first." in result.output


def test_route_rejects_task_and_task_file_together(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0
    task_file = repo_env["repo"] / "task.md"
    task_file.write_text("Update prompt routing.\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "Update prompt routing.",
            "--task-file",
            str(task_file),
        ],
    )

    assert result.exit_code == 1
    assert "Use either --task or --task-file" in result.output
