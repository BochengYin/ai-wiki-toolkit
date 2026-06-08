"""Agent harness adapters built on route packet outputs.

This layer interprets route packets as non-binding harness hints. The route
core still owns context construction; harness code owns workflow execution,
tool-risk policy, phase state, and behavior-test evaluation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from ai_wiki_toolkit.route import DEFAULT_ROUTE_RERANK_TOP
from ai_wiki_toolkit.route_behavior import (
    ROUTE_BEHAVIOR_REPORT_SCHEMA_VERSION,
    ROUTE_BEHAVIOR_SUITE_SCHEMA_VERSION,
    RouteBehaviorReportResult,
    build_route_behavior_report,
    generate_route_behavior_report,
    render_route_behavior_report,
    render_route_behavior_report_json,
)

AGENT_HARNESS_BEHAVIOR_REPORT_SCHEMA_VERSION = ROUTE_BEHAVIOR_REPORT_SCHEMA_VERSION
AGENT_HARNESS_BEHAVIOR_SUITE_SCHEMA_VERSION = ROUTE_BEHAVIOR_SUITE_SCHEMA_VERSION

AgentHarnessBehaviorReportResult = RouteBehaviorReportResult


def adapter_hints_from_route_packet(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Return non-binding harness hints from a route packet.

    These hints deliberately do not change the route packet or Codex runtime
    permissions. A concrete agent surface may consume them, ignore them, or
    translate them into stronger runtime controls.
    """
    phase_plan = packet.get("phase_plan") if isinstance(packet.get("phase_plan"), dict) else {}
    behavior_contract = (
        packet.get("behavior_contract")
        if isinstance(packet.get("behavior_contract"), dict)
        else {}
    )
    current_phase = (
        phase_plan.get("current_phase")
        if isinstance(phase_plan.get("current_phase"), dict)
        else {}
    )
    route = packet.get("route") if isinstance(packet.get("route"), dict) else {}
    mode = route.get("mode") if isinstance(route.get("mode"), dict) else {}

    return {
        "schema_version": "agent-harness-adapter-hints-v1",
        "authority": "non_binding_hint",
        "status": "shadow",
        "source": "route_packet",
        "current_phase": current_phase or None,
        "route_mode": mode.get("name"),
        "workflow_contract_id": behavior_contract.get("workflow_contract_id"),
        "disallowed_actions": behavior_contract.get("disallowed_actions") or [],
        "required_steps": behavior_contract.get("workflow_steps_to_follow") or [],
        "note": (
            "AI Wiki Toolkit Core constructs context. Agent Harness may use these "
            "hints for workflow and tool policy, but route activation must not "
            "depend on runtime-control behavior."
        ),
    }


def build_agent_harness_behavior_report(
    suite: Mapping[str, Any],
    *,
    repo_root: Path,
    max_docs: int = 6,
    rerank_top: int = DEFAULT_ROUTE_RERANK_TOP,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Evaluate an agent harness behavior suite against route packet hints."""
    return build_route_behavior_report(
        suite,
        repo_root=repo_root,
        max_docs=max_docs,
        rerank_top=rerank_top,
        generated_at=generated_at,
    )


def render_agent_harness_behavior_report_json(payload: Mapping[str, Any]) -> str:
    """Render an agent harness behavior report as JSON."""
    return render_route_behavior_report_json(payload)


def render_agent_harness_behavior_report(payload: Mapping[str, Any]) -> str:
    """Render an agent harness behavior report as Markdown."""
    return render_route_behavior_report(payload).replace(
        "# Route Behavior Test Report",
        "# Agent Harness Behavior Test Report",
        1,
    )


def generate_agent_harness_behavior_report(
    *,
    suite_path: Path,
    repo_root: Path | None = None,
    handle: str | None = None,
    max_docs: int = 6,
    rerank_top: int = DEFAULT_ROUTE_RERANK_TOP,
    write: bool = False,
) -> AgentHarnessBehaviorReportResult:
    """Generate an agent harness behavior report.

    The underlying report schema remains route-behavior-report-v1 for backward
    compatibility with existing fixtures and CLI commands.
    """
    return generate_route_behavior_report(
        suite_path=suite_path,
        repo_root=repo_root,
        handle=handle,
        max_docs=max_docs,
        rerank_top=rerank_top,
        write=write,
    )
