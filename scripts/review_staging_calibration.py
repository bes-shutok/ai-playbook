#!/usr/bin/env python3
"""Finding-record calibration vocabulary for the review-staging validator.

Owns the closed calibration enums (blast_radius, reachability, confidence)
and the three per-finding calibration checks, moved from
validate_current_payload in scripts/validate_review_staging.py (machinery
script refactor program, Task 4). The validator from-imports the constants
so they stay resolvable as validator module attributes
(scripts/test_review_record_selection.py reads vrs.VALID_* in its
vocabulary-equality arms). This module imports nothing from the validator,
so the import direction stays one-way; ``result`` is the validator's
ValidationResult duck-type (anything carrying ``add_error(str)``).
"""

from __future__ import annotations

VALID_BLAST_RADIUS = frozenset({"global", "multi-service", "single-service", "local"})
VALID_REACHABILITY = frozenset({"expected", "common", "plausible-edge", "theoretical"})
VALID_CONFIDENCE = frozenset({"verified", "strong-evidence", "hypothesis"})


def validate_finding_calibration(finding: dict, display: str, result) -> None:
    """The per-finding blast_radius / reachability / confidence enum checks,
    moved verbatim from validate_current_payload's findings loop; ``display``
    is the row's error label and ``result`` collects the targeted errors."""
    # r4 F1: membership against a frozenset crashes with an uncaught
    # TypeError when the operand is unhashable (e.g. a list), aborting
    # the run before any targeted error is recorded. Mirror the r3 F1
    # severity pattern: gate each enum check on isinstance(value, str)
    # so odd-typed values get the existing targeted invalid-* error.
    if (
        "blast_radius" in finding
        and (
            not isinstance(finding["blast_radius"], str)
            or finding["blast_radius"] not in VALID_BLAST_RADIUS
        )
    ):
        result.add_error(
            f"current finding {display} has invalid blast_radius "
            f"(expected one of {sorted(VALID_BLAST_RADIUS)})"
        )
    if (
        "reachability" in finding
        and (
            not isinstance(finding["reachability"], str)
            or finding["reachability"] not in VALID_REACHABILITY
        )
    ):
        result.add_error(
            f"current finding {display} has invalid reachability "
            f"(expected one of {sorted(VALID_REACHABILITY)})"
        )
    if (
        "confidence" in finding
        and (
            not isinstance(finding["confidence"], str)
            or finding["confidence"] not in VALID_CONFIDENCE
        )
    ):
        result.add_error(
            f"current finding {display} has invalid confidence "
            f"(expected one of {sorted(VALID_CONFIDENCE)}); "
            "map to the closed confidence enum (hypothesis, strong-evidence, verified); do not downgrade"
        )
