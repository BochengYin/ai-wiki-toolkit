from __future__ import annotations

from ai_wiki_toolkit.agent_harness import (
    adapter_hints_from_route_packet,
    render_agent_harness_behavior_report,
)


def test_adapter_hints_from_route_packet_are_non_binding() -> None:
    packet = {
        "route": {"mode": {"name": "plan"}},
        "phase_plan": {
            "current_phase": {
                "id": "plan",
                "agent_surface_mode": "plan",
                "permissions": {"edit_files": False},
            }
        },
        "behavior_contract": {
            "workflow_contract_id": "weekly-report-diagnostics",
            "disallowed_actions": ["edit_files"],
            "workflow_steps_to_follow": ["load metrics", "render report"],
        },
    }

    hints = adapter_hints_from_route_packet(packet)

    assert hints["schema_version"] == "agent-harness-adapter-hints-v1"
    assert hints["authority"] == "non_binding_hint"
    assert hints["status"] == "shadow"
    assert hints["route_mode"] == "plan"
    assert hints["current_phase"]["id"] == "plan"
    assert hints["workflow_contract_id"] == "weekly-report-diagnostics"
    assert hints["disallowed_actions"] == ["edit_files"]
    assert hints["required_steps"] == ["load metrics", "render report"]


def test_agent_harness_report_renderer_uses_harness_title() -> None:
    rendered = render_agent_harness_behavior_report(
        {
            "generated_at": "2026-06-08T00:00:00+00:00",
            "suite": {"name": "fixture"},
            "summary": {
                "case_count": 0,
                "passed_case_count": 0,
                "failed_case_count": 0,
                "failed_check_count": 0,
                "blocks_activation": False,
            },
            "activation": {
                "status": "eligible_for_shadow_validation",
                "reason": "fixture",
            },
            "items": [],
            "failure_policy": [],
        }
    )

    assert "# Agent Harness Behavior Test Report" in rendered
