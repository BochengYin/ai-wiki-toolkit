"""Feedback-loop APIs for route evidence and taxonomy candidates.

The feedback layer collects post-hoc evidence, induces inactive taxonomy
candidates, and evaluates route-core activation gates. It does not mutate
active taxonomy unless a separate activation workflow is added and passes.
"""

from __future__ import annotations

from ai_wiki_toolkit.route_activation import evaluate_route_activation_policy
from ai_wiki_toolkit.taxonomy_candidates import (
    DEFAULT_TAXONOMY_CANDIDATE_MIN_EVIDENCE,
    TAXONOMY_CANDIDATE_SCHEMA_VERSION,
    TaxonomyCandidateInductionResult,
    build_taxonomy_candidate_report,
    generate_taxonomy_candidate_report,
    render_taxonomy_candidate_report_json,
    render_taxonomy_candidate_report_markdown,
)
from ai_wiki_toolkit.taxonomy_evidence import (
    TAXONOMY_EVIDENCE_CONFIDENCES,
    TAXONOMY_EVIDENCE_SCHEMA_VERSION,
    TAXONOMY_EVIDENCE_SIGNAL_TYPES,
    RecordTaxonomyEvidenceResult,
    record_taxonomy_evidence,
)

__all__ = [
    "DEFAULT_TAXONOMY_CANDIDATE_MIN_EVIDENCE",
    "TAXONOMY_CANDIDATE_SCHEMA_VERSION",
    "TAXONOMY_EVIDENCE_CONFIDENCES",
    "TAXONOMY_EVIDENCE_SCHEMA_VERSION",
    "TAXONOMY_EVIDENCE_SIGNAL_TYPES",
    "RecordTaxonomyEvidenceResult",
    "TaxonomyCandidateInductionResult",
    "build_taxonomy_candidate_report",
    "evaluate_route_activation_policy",
    "generate_taxonomy_candidate_report",
    "record_taxonomy_evidence",
    "render_taxonomy_candidate_report_json",
    "render_taxonomy_candidate_report_markdown",
]
