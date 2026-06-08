from __future__ import annotations

from ai_wiki_toolkit.feedback import (
    TAXONOMY_EVIDENCE_SIGNAL_TYPES,
    evaluate_route_activation_policy,
)


def test_feedback_layer_exposes_route_core_activation_policy() -> None:
    replay_report = {
        "prompt_recovery": {"replayed_trace_count": 57},
        "baseline": {
            "summary": {
                "selected_useful_doc_count": 10,
                "missed_useful_doc_count": 3,
            }
        },
        "replay": {
            "summary": {
                "selected_useful_doc_count": 11,
                "missed_useful_doc_count": 2,
            }
        },
        "comparison": {
            "route_precision_delta": 0.01,
            "route_noise_delta": -0.01,
        },
        "items": [],
    }

    policy = evaluate_route_activation_policy(replay_report=replay_report)

    assert policy["status"] == "activate_recommended"
    assert {item["category"] for item in policy["criteria"]} == {"route_core"}
    assert "user_correction" in TAXONOMY_EVIDENCE_SIGNAL_TYPES
