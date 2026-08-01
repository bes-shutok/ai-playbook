#!/usr/bin/env python3
"""Validate review staging markdown per review-staging skill.

Exit 0 when valid (soft mode may print warnings). Exit 1 when invalid in --hard mode.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import facts_paths
except ImportError:  # pragma: no cover
    facts_paths = None  # type: ignore

STAGING_NAME_RE = re.compile(
    r"^(?:\d{4}-\d{2}-\d{2}-)?"
    r"(?:"
    r"branch-review|.+?-branch-review|"
    r"plan-review|.+?-plan-review|"
    r"rfc-review|.+?-rfc-review|"
    r"confluence-review|.+?-confluence-review|"
    r"PR-\d+"
    r").+"
    r"(?:-r\d+|-(?:light|full|review-local))?\.md$",
    re.IGNORECASE,
)
ROUND_SUFFIX_RE = re.compile(r"-r(\d+)\.md$", re.IGNORECASE)
MEDIUM_PLUS_VERDICT_RE = re.compile(
    r"(\d+)\s+Medium\+?\s+findings(?:\s+accepted\s+for\s+fix)?",
    re.IGNORECASE,
)
CLEAR_ROUND_RE = re.compile(r"0\s+Medium\+?\s+findings;\s*clear\s+round", re.IGNORECASE)
FINDING_HEADER_RE = re.compile(r"^(?:F(\d+)|(\d+)\.)\s", re.MULTILINE)
STUB_BYTE_THRESHOLD = 2000
LEGACY_MIN_BLOCK_CHARS = 120
DEFAULT_PANEL_WORKERS = (
    "correctness-completeness",
    "testing",
    "design-simplicity",
    "contract-docs",
    "risk",
)
# Required lenses per base worker for full-panel completion coverage. Source:
# review-panel-selection.md "Recommended five-worker panel". For contract-docs
# the validator requires at least `documentation` (the `consistency` lens is
# conditional on plan/RFC review and is not part of the always-required set).
REQUIRED_PANEL_LENSES = {
    "correctness-completeness": frozenset({"quality", "implementation"}),
    "testing": frozenset({"testing"}),
    "design-simplicity": frozenset({"architecture", "simplification"}),
    "contract-docs": frozenset({"documentation"}),
    "risk": frozenset({"security"}),
}
# Worker statuses that count as a launch toward the six-worker ceiling but
# NEVER as completed coverage for full-panel completion.
INCOMPLETE_WORKER_STATUSES = frozenset({"failed", "timed-out"})
# Statuses that are neither skipped nor a recognized incomplete outcome; any
# status outside {complete, skipped} ∪ INCOMPLETE_WORKER_STATUSES is "unknown"
# and also fails coverage.
VALID_COMPLETED_STATUS = "complete"
VALID_SKIPPED_STATUS = "skipped"
# Triage values that resolve a finding (no longer count toward readiness).
RESOLVED_TRIAGE_VALUES = frozenset({"done", "dropped", "fixed"})
LEGACY_DEFAULT_PANEL_AGENTS = (
    "quality",
    "implementation",
    "testing",
    "simplification",
    "documentation",
    "architecture",
    "security",
)
SEVERITY_ORDER = ("Critical", "High", "Medium", "Low")
VALID_SOURCE_KINDS = frozenset({"plan", "rfc", "document", "code"})
VALID_BLAST_RADIUS = frozenset({"global", "multi-service", "single-service", "local"})
VALID_REACHABILITY = frozenset({"expected", "common", "plausible-edge", "theoretical"})
VALID_CONFIDENCE = frozenset({"verified", "strong-evidence", "hypothesis"})
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
# Finding budget per worker (severity-calibration.md "Finding budget"):
# all Critical + all blocking expand; up to BUDGET_NONBLOCKING_HIGH_MED
# additional non-blocking High/Medium; up to BUDGET_NONBLOCKING_LOW additional
# non-blocking Low. Remaining credible non-blocking candidates go to overflow.
BUDGET_NONBLOCKING_HIGH_MED = 5
BUDGET_NONBLOCKING_LOW = 2
REQUIRED_CURRENT_FINDING_FIELDS = (
    "blocking",
    "consequence",
    "reachability",
    "blast_radius",
    "confidence",
)
VALID_DISCARD_REASONS = frozenset({
    "duplicate",
    "already-mitigated",
    "false-positive",
    "out-of-scope",
    "prior-review",
    "insufficient-evidence",
    "severity-merged",
    "noise",
    "assumption-invalid",
    "downstream-pr",
    "agent-failed",
    "agent-skipped",
    "invalid-anchor",
    "excerpt-mismatch",
    "wrong-owner",
})


def finding_has_comment_and_analysis(block: str) -> tuple[bool, bool]:
    has_comment = "#### Comment" in block
    has_analysis = "#### Analysis" in block
    return has_comment, has_analysis


def is_legacy_finding_block(block: str) -> bool:
    """Pre-gold-format rounds: ### F<N> with Status/triage bullets, no Comment/Analysis."""
    if "#### Comment" in block or "#### Analysis" in block:
        return False
    if "**Status:**" not in block and "**Triage:**" not in block:
        return False
    return len(block.strip()) >= LEGACY_MIN_BLOCK_CHARS


@dataclass
class ValidationResult:
    path: Path
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    medium_plus_expected: int = 0
    finding_sections: int = 0

    def add_error(self, message: str) -> None:
        self.errors.append(message)
        self.ok = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "path": str(self.path),
            "errors": self.errors,
            "warnings": self.warnings,
            "medium_plus_expected": self.medium_plus_expected,
            "finding_sections": self.finding_sections,
        }


def resolve_reviews_dir(start_dir: Path) -> Path:
    if facts_paths is not None:
        resolved = facts_paths.resolve_toml_key(start_dir, "reviews_dir")
        if resolved is not None:
            return resolved
    return start_dir / "docs" / "history" / "reviews"


def compute_source_digest(source_kind: str, content_or_diff_bytes: bytes) -> str:
    """Return the authoritative source digest for a review.

    For ``plan``, ``rfc``, and ``document`` reviews the input is the exact
    reviewed document UTF-8 bytes. For ``code`` reviews the input is the exact
    stored diff bytes. In every case the recipe is ``SHA-256`` of those exact
    bytes, rendered as a lowercase 64-character hex string.
    """
    if source_kind not in VALID_SOURCE_KINDS:
        raise ValueError(f"unknown source_kind: {source_kind!r}")
    if not isinstance(content_or_diff_bytes, (bytes, bytearray)):
        raise TypeError("content_or_diff_bytes must be bytes, not str")
    return hashlib.sha256(content_or_diff_bytes).hexdigest()


def is_staging_review_path(path: Path) -> bool:
    name = path.name
    if not name.endswith(".md"):
        return False
    if STAGING_NAME_RE.match(name):
        return True
    if ROUND_SUFFIX_RE.search(name) and "review" in name.lower():
        return True
    return False


def extract_medium_plus_count(content: str) -> int:
    verdict_match = re.search(
        r"## Verdict for this round \(before fixes\)(.*?)(?:\n## |\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    search_blob = verdict_match.group(1) if verdict_match else content
    if CLEAR_ROUND_RE.search(search_blob):
        return 0
    match = MEDIUM_PLUS_VERDICT_RE.search(search_blob)
    if match:
        return int(match.group(1))
    counts_match = re.search(
        r"\|\s*Medium\+\s*staged\s*\|\s*(\d+)\s*\|",
        content,
        re.IGNORECASE,
    )
    if counts_match:
        return int(counts_match.group(1))
    medium_only = re.search(
        r"(\d+)\s+Medium\s+findings\s+accepted\s+for\s+fix",
        search_blob,
        re.IGNORECASE,
    )
    if medium_only:
        return int(medium_only.group(1))
    return 0


def extract_staged_count(content: str) -> int:
    staged_match = re.search(
        r"\|\s*Staged findings\s*\|\s*(\d+)\s*\|",
        content,
        re.IGNORECASE,
    )
    if staged_match:
        return int(staged_match.group(1))
    bullet_match = re.search(
        r"^-\s*Staged findings:\s*(\d+)\s*$",
        content,
        re.IGNORECASE | re.MULTILINE,
    )
    if bullet_match:
        return int(bullet_match.group(1))
    meta_match = re.search(
        r"^-\s*Findings:\s*(\d+)\s*$",
        content,
        re.IGNORECASE | re.MULTILINE,
    )
    if meta_match:
        return int(meta_match.group(1))
    return extract_medium_plus_count(content)


def split_finding_blocks(content: str) -> list[str]:
    findings_match = re.search(r"^## Findings\s*$", content, re.MULTILINE)
    if not findings_match:
        return []
    findings_section = content[findings_match.end() :]
    findings_section = re.split(r"\n## ", findings_section, maxsplit=1)[0]
    # Legacy findings use "### 1." or "### F1". Current grouped findings use
    # severity headings plus "#### F1." entries.
    current_parts = re.split(r"\n(?=#### F\d+\.)", findings_section)
    if len(current_parts) > 1:
        return [part.strip() for part in current_parts[1:] if part.strip()]
    parts = re.split(r"\n(?=### )", findings_section)
    blocks: list[str] = []
    for part in parts:
        stripped = part.strip()
        if not stripped.startswith("### "):
            continue
        header = stripped.splitlines()[0][4:].strip()
        if FINDING_HEADER_RE.match(header + " "):
            blocks.append(stripped)
    return blocks


def parse_markdown_findings(content: str) -> list[dict]:
    """Parse current-format Markdown findings into ``{id, severity, blocking,
    triage}`` dicts, one per ``#### F<N>.`` block.

    Severity is read from the enclosing ``### <Severity>`` group heading;
    blocking from either the canonical ``- **Blocking**: true | false`` bullet
    documented in ``review-staging/SKILL.md`` (the primary, human-facing
    template every producer skill emits) or the legacy bare ``- **blocking**``
    / ``- **non-blocking**`` bullet (older staging docs); triage from a
    ``**Triage**: <value>`` bullet. Used by the Markdown/sidecar conservation
    cross-check.
    """
    findings_match = re.search(r"^## Findings\s*$", content, re.MULTILINE)
    if not findings_match:
        return []
    findings_section = content[findings_match.end() :]
    findings_section = re.split(r"\n## ", findings_section, maxsplit=1)[0]
    parsed: list[dict] = []
    current_severity: str | None = None
    current: dict | None = None
    for line in findings_section.splitlines():
        sev_match = re.match(r"^###\s+(Critical|High|Medium|Low)\b", line)
        if sev_match:
            current_severity = sev_match.group(1)
            continue
        block_match = re.match(r"^####\s+F(\d+)\.", line)
        if block_match:
            if current is not None:
                parsed.append(current)
            current = {
                "id": int(block_match.group(1)),
                "severity": current_severity,
                "blocking": None,
                "triage": None,
            }
            continue
        if current is None:
            continue
        labeled_blocking = re.search(
            r"-\s*\*\*[Bb]locking\*\*\s*:\s*(true|false)\b", line
        )
        if labeled_blocking:
            current["blocking"] = labeled_blocking.group(1) == "true"
        elif re.search(r"-\s*\*\*blocking\*\*(?!\s*:)", line):
            current["blocking"] = True
        elif re.search(r"-\s*\*\*non-blocking\*\*(?!\s*:)", line):
            current["blocking"] = False
        triage = re.search(r"\*\*Triage\*\*:\s*(\S+)", line)
        if triage:
            current["triage"] = triage.group(1).rstrip(".")
    if current is not None:
        parsed.append(current)
    return parsed


def is_review_ready(content: str) -> bool:
    """Return True iff no blocking finding remains unresolved.

    Readiness keys only on ``blocking: true``; severity is irrelevant. A
    blocking Low blocks readiness exactly as much as a blocking Critical. A
    finding counts as resolved when its triage value is one of
    ``RESOLVED_TRIAGE_VALUES`` (``done``/``dropped``/``fixed``); ``pending``,
    ``deferred``, or a missing triage value counts as unresolved. An empty
    review (no findings) is ready.
    """
    for finding in parse_markdown_findings(content):
        if finding.get("blocking") is True:
            triage = finding.get("triage")
            if triage not in RESOLVED_TRIAGE_VALUES:
                return False
    return True


def stats_sidecar_path(staging_path: Path) -> Path:
    return staging_path.with_suffix(".stats.json")


def metadata_allows_stats_skip(content: str) -> bool:
    meta = re.search(r"^## Metadata\s*$", content, re.MULTILINE)
    if not meta:
        return False
    tail = content[meta.end() :]
    tail = re.split(r"\n## ", tail, maxsplit=1)[0]
    return bool(
        re.search(
            r"Stats sidecar:\s*skipped\b",
            tail,
            re.IGNORECASE,
        )
    )


def validate_discarded_findings(content: str, result: ValidationResult) -> None:
    section_match = re.search(
        r"^### Discarded findings\s*$",
        content,
        re.MULTILINE,
    )
    if not section_match:
        return
    tail = content[section_match.end() :]
    tail = re.split(r"\n### ", tail, maxsplit=1)[0]
    if re.search(r"^\s*None\.?\s*$", tail, re.MULTILINE):
        return
    for line in tail.splitlines():
        if not line.strip().startswith("|"):
            continue
        if re.match(r"^\|\s*(?:Agent|Worker)\s*\|", line):
            continue
        if re.match(r"^\|[-:| ]+\|$", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6:
            continue
        _agent, _sev, _pattern, _theme, reason, notes = cells[:6]
        if reason not in VALID_DISCARD_REASONS:
            result.add_warning(f"unknown discard reason code: {reason}")
        if reason == "wrong-owner" and not re.search(r"lead:\s*\w+", notes, re.IGNORECASE):
            result.add_error(
                "wrong-owner discard row missing Notes lead: <agent-id>"
            )


def validate_stats_sidecar(
    staging_path: Path,
    content: str,
    result: ValidationResult,
    *,
    expected_digest: str | None = None,
    source_kind: str | None = None,
) -> None:
    staged_count = extract_staged_count(content)
    # Hard gate: never waive the sidecar when the doc claims staged findings.
    # Also never waive when the caller explicitly asked for a digest check
    # (--source-plan): a waived sidecar would silently skip the stale-digest
    # comparison, which matters most on the clear round that gates execution.
    if (
        metadata_allows_stats_skip(content)
        and staged_count == 0
        and expected_digest is None
    ):
        return
    if metadata_allows_stats_skip(content) and staged_count > 0:
        result.add_error(
            "Stats sidecar: skipped is not allowed when Staged findings > 0"
        )
    sidecar = stats_sidecar_path(staging_path)
    if not sidecar.is_file():
        result.add_error(f"missing required stats sidecar: {sidecar.name}")
        return
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        result.add_error(f"invalid stats sidecar JSON: {exc}")
        return
    for key in ("panel", "counts"):
        if key not in payload:
            result.add_warning(f"stats sidecar missing '{key}'")
    is_current = (
        "panel_mode" in payload
        or "workers_launched" in (payload.get("counts") or {})
        or any(isinstance(row, dict) and "worker" in row for row in (payload.get("panel") or []))
    )
    if is_current:
        validate_current_payload(
            payload,
            content,
            result,
            expected_digest=expected_digest,
            source_kind=source_kind,
        )
    discarded = payload.get("discarded") or []
    for row in discarded:
        if not isinstance(row, dict):
            continue
        reason = row.get("reason")
        if reason == "wrong-owner" and not (
            row.get("lead_agent")
            or (row.get("lead_worker") and row.get("lead_lens"))
        ):
            result.add_error(
                "stats sidecar wrong-owner row missing lead ownership"
            )


def validate_full_panel_completion(
    launched: list[dict], result: ValidationResult
) -> None:
    """Enforce completed full-panel coverage for ``panel_mode == "full"``.

    Each of the five default base workers must appear exactly once among
    launched (non-skipped) rows with status ``complete`` and all of its
    required lenses. Duplicate workers fail. Failed, timed-out, and any other
    non-complete status counts as a launch (toward the six-worker ceiling) but
    never as completed coverage: a base worker whose only row is failed or
    timed-out fails full-panel completion.
    """
    seen: dict[str, list[dict]] = {}
    for row in launched:
        if not isinstance(row, dict):
            continue
        worker = row.get("worker")
        seen.setdefault(str(worker), []).append(row)
    # Duplicate workers (same name in more than one launched row).
    for worker, rows in seen.items():
        if len(rows) > 1:
            result.add_error(
                f"full panel: worker {worker!r} appears {len(rows)} times; "
                f"each base worker must appear exactly once"
            )
    present = set(seen.keys())
    for base in DEFAULT_PANEL_WORKERS:
        rows = seen.get(base, [])
        if not rows:
            result.add_error(
                f"full panel: missing required base worker {base!r}"
            )
            continue
        # Coverage: at least one row must be complete with required lenses.
        complete_rows = [
            r for r in rows
            if r.get("status") == VALID_COMPLETED_STATUS
        ]
        if not complete_rows:
            statuses = sorted({str(r.get("status")) for r in rows})
            result.add_error(
                f"full panel: worker {base!r} has no completed coverage "
                f"(statuses: {statuses}); failed/timed-out rows count as "
                f"launches but never as coverage"
            )
            continue
        # Required lenses: the (first) complete row must carry every required
        # lens for this worker.
        row = complete_rows[0]
        lenses = row.get("lenses")
        lens_set = set(lenses) if isinstance(lenses, list) else set()
        required = REQUIRED_PANEL_LENSES.get(base, frozenset())
        missing_lenses = required - lens_set
        if missing_lenses:
            result.add_error(
                f"full panel: worker {base!r} missing required lenses "
                f"{sorted(missing_lenses)} (have {sorted(lens_set)})"
            )


def validate_current_payload(
    payload: dict,
    content: str,
    result: ValidationResult,
    *,
    expected_digest: str | None = None,
    source_kind: str | None = None,
) -> None:
    panel_mode = payload.get("panel_mode")
    if panel_mode not in {"full", "focused"}:
        result.add_error("current sidecar panel_mode must be full or focused")
    if panel_mode == "focused" and not payload.get("selection_reason"):
        result.add_error("focused panel missing selection_reason")

    # Source-digest authority (F2). Backward compat: payloads with no
    # source_kind and no expected_digest supplied stay presence-only so legacy
    # artifacts with placeholder digests still validate. Opting in (either by
    # declaring source_kind on the payload OR by supplying expected_digest to
    # the validator) activates the 64-hex syntax check and the freshness
    # comparison.
    declared_kind = payload.get("source_kind")
    if declared_kind is not None and declared_kind not in VALID_SOURCE_KINDS:
        result.add_error(
            f"current sidecar source_kind must be one of "
            f"{sorted(VALID_SOURCE_KINDS)}; got {declared_kind!r}"
        )
    # Only compare when both the orchestrator-supplied source_kind and the
    # sidecar-declared source_kind are present; this keeps the opt-in backward
    # compat invariant explicit (legacy payloads with no source_kind stay
    # presence-only).
    if source_kind and declared_kind and source_kind != declared_kind:
        result.add_error(
            f"source_kind mismatch: validator got {source_kind!r} but sidecar "
            f"declares {declared_kind!r}"
        )
    digest = payload.get("source_digest")
    if not digest:
        result.add_error("current sidecar missing source_digest")
    else:
        authoritative = expected_digest is not None or declared_kind is not None
        if authoritative and not HEX64_RE.match(str(digest)):
            result.add_error(
                "current sidecar source_digest must be a lowercase 64-char hex "
                "SHA-256; got an invalid or placeholder digest"
            )
        if expected_digest is not None and str(digest) != expected_digest:
            result.add_error(
                f"current sidecar source_digest is stale (mismatch vs expected_digest); "
                f"reviewed artifact may have changed"
            )

    panel = payload.get("panel") or []
    launched = [
        row
        for row in panel
        if isinstance(row, dict) and row.get("status") != "skipped"
    ]
    if len(launched) > 6:
        result.add_error("panel exceeds six actual worker launches")
    if len(launched) == 6 and not payload.get("escalation_reason"):
        result.add_error("sixth worker missing escalation_reason")

    workers = {str(row.get("worker")) for row in launched}
    if panel_mode == "full":
        validate_full_panel_completion(launched, result)

    flattened_descendants: set[str] = set()
    for row in launched:
        worker = row.get("worker")
        lenses = row.get("lenses")
        descendants = row.get("descendant_launches")
        if not worker:
            result.add_error("panel row missing worker")
        if not isinstance(lenses, list) or not lenses:
            result.add_error(f"worker {worker!r} missing non-empty lenses")
        if not isinstance(descendants, list):
            result.add_error(f"worker {worker!r} missing descendant_launches")
            continue
        flattened_descendants.update(str(item) for item in descendants)
    for descendant in flattened_descendants:
        matching = [
            row
            for row in launched
            if str(row.get("worker")) == descendant and row.get("parent_worker")
        ]
        if not matching:
            result.add_error(
                f"descendant launch {descendant!r} is not flattened into panel"
            )

    counts = payload.get("counts") or {}
    if "workers_launched" in counts and counts["workers_launched"] != len(launched):
        result.add_error("counts.workers_launched does not match panel launches")

    findings = payload.get("findings") or []
    for finding in findings:
        if not isinstance(finding, dict):
            result.add_error("current finding must be an object")
            continue
        fid = finding.get("id")
        if finding.get("severity") not in SEVERITY_ORDER:
            result.add_error(
                f"current finding {fid} has invalid severity "
                f"(expected one of {list(SEVERITY_ORDER)})"
            )
        # blocking must be a real Python bool, not a string/int coercion.
        if "blocking" in finding and not isinstance(finding["blocking"], bool):
            result.add_error(
                f"current finding {fid} blocking must be a boolean, "
                f"got {type(finding['blocking']).__name__}"
            )
        if (
            "blast_radius" in finding
            and finding["blast_radius"] not in VALID_BLAST_RADIUS
        ):
            result.add_error(
                f"current finding {fid} has invalid blast_radius "
                f"(expected one of {sorted(VALID_BLAST_RADIUS)})"
            )
        if (
            "reachability" in finding
            and finding["reachability"] not in VALID_REACHABILITY
        ):
            result.add_error(
                f"current finding {fid} has invalid reachability "
                f"(expected one of {sorted(VALID_REACHABILITY)})"
            )
        if (
            "confidence" in finding
            and finding["confidence"] not in VALID_CONFIDENCE
        ):
            result.add_error(
                f"current finding {fid} has invalid confidence "
                f"(expected one of {sorted(VALID_CONFIDENCE)})"
            )
        for field_name in REQUIRED_CURRENT_FINDING_FIELDS:
            if field_name not in finding:
                result.add_error(
                    f"current finding {fid} missing {field_name}"
                )
    validate_finding_order(findings, result)
    validate_finding_budget(findings, result)

    for item in payload.get("overflow") or []:
        if not isinstance(item, dict):
            result.add_error("overflow item must be an object")
            continue
        if item.get("severity") == "Critical" or item.get("blocking") is True:
            result.add_error("Critical or blocking finding cannot be in overflow")

    validate_markdown_severity_groups(content, result)
    validate_finding_conservation(content, payload, result)


def validate_finding_order(findings: list, result: ValidationResult) -> None:
    """Require severity buckets Critical→Low, then ascending finding ID.

    Blocking / blast_radius / reachability / confidence are finding metadata only;
    they must not reshuffle presentation (stable through triage).
    """
    severity_rank = {value: index for index, value in enumerate(SEVERITY_ORDER)}

    def key(row: dict) -> tuple:
        return (
            severity_rank.get(row.get("severity"), 99),
            row.get("id", 0),
        )

    if findings != sorted(findings, key=key):
        result.add_error(
            "findings are not ordered by severity then ascending finding ID"
        )


def validate_finding_budget(findings: list, result: ValidationResult) -> None:
    """Enforce the per-worker finding budget from severity-calibration.md.

    Every worker fully expands all Critical findings and all blocking findings,
    plus up to ``BUDGET_NONBLOCKING_HIGH_MED`` additional non-blocking
    High/Medium findings and up to ``BUDGET_NONBLOCKING_LOW`` additional
    non-blocking Low findings; remaining credible non-blocking candidates go to
    overflow.

    Bucketing: a finding may carry a ``workers`` list; it counts against each
    named worker's budget. Findings without ``workers`` attribution fall into a
    single unnamed bucket (the historical global default), so legacy sidecars
    without per-finding attribution still get a sound overall cap.
    """
    buckets: dict[str, dict[str, int]] = {}
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        severity = finding.get("severity")
        blocking = finding.get("blocking")
        # Critical and blocking findings are always fully expanded; never cap.
        if severity == "Critical" or blocking is True:
            continue
        workers = finding.get("workers")
        if not isinstance(workers, list) or not workers:
            keys = [""]
        else:
            keys = [str(w) for w in workers]
        for key in keys:
            bucket = buckets.setdefault(key, {"high_med": 0, "low": 0})
            if severity in ("High", "Medium"):
                bucket["high_med"] += 1
            elif severity == "Low":
                bucket["low"] += 1
    for key, counts in buckets.items():
        label = repr(key) if key else "the unattributed pool"
        if counts["high_med"] > BUDGET_NONBLOCKING_HIGH_MED:
            result.add_error(
                f"finding budget exceeded: worker {label} has "
                f"{counts['high_med']} non-blocking High/Medium findings "
                f"(max {BUDGET_NONBLOCKING_HIGH_MED}); move extras to overflow"
            )
        if counts["low"] > BUDGET_NONBLOCKING_LOW:
            result.add_error(
                f"finding budget exceeded: worker {label} has "
                f"{counts['low']} non-blocking Low findings "
                f"(max {BUDGET_NONBLOCKING_LOW}); move extras to overflow"
            )


def validate_finding_conservation(
    content: str, payload: dict, result: ValidationResult
) -> None:
    """Reconcile Markdown findings with sidecar findings.

    For current-format payloads: the count of ``#### F<N>.`` Markdown blocks
    must equal ``len(payload["findings"])``; when the sidecar carries
    ``counts.staged_findings`` it must equal the same number; and per-finding
    id, severity, blocking, and triage must agree between Markdown and sidecar.
    Disagreement is a hard conservation error.
    """
    sidecar_findings = payload.get("findings") or []
    if not isinstance(sidecar_findings, list):
        return
    md_findings = parse_markdown_findings(content)
    # Only apply when at least one side signals current-format findings.
    if not md_findings and not sidecar_findings:
        return

    if len(md_findings) != len(sidecar_findings):
        result.add_error(
            f"finding conservation: Markdown lists {len(md_findings)} finding(s) "
            f"but sidecar lists {len(sidecar_findings)}"
        )

    counts = payload.get("counts") or {}
    if isinstance(counts, dict) and "staged_findings" in counts:
        if counts["staged_findings"] != len(sidecar_findings):
            result.add_error(
                f"finding conservation: counts.staged_findings="
                f"{counts['staged_findings']} but sidecar has "
                f"{len(sidecar_findings)} finding(s)"
            )

    md_by_id = {f["id"]: f for f in md_findings if isinstance(f.get("id"), int)}
    for sc in sidecar_findings:
        if not isinstance(sc, dict):
            continue
        sid = sc.get("id")
        if not isinstance(sid, int) or sid not in md_by_id:
            result.add_error(
                f"finding conservation: sidecar finding id {sid!r} has no "
                f"matching Markdown #### F block"
            )
            continue
        md = md_by_id[sid]
        if (
            md.get("severity") is not None
            and sc.get("severity") is not None
            and md["severity"] != sc.get("severity")
        ):
            result.add_error(
                f"finding conservation: finding {sid} severity disagrees "
                f"(Markdown {md['severity']!r}, sidecar {sc.get('severity')!r})"
            )
        if (
            md.get("blocking") is not None
            and sc.get("blocking") is not None
            and md["blocking"] != sc.get("blocking")
        ):
            result.add_error(
                f"finding conservation: finding {sid} blocking disagrees "
                f"(Markdown {md['blocking']!r}, sidecar {sc.get('blocking')!r})"
            )
        if (
            md.get("triage") is not None
            and sc.get("triage") is not None
            and md["triage"] != sc.get("triage")
        ):
            result.add_error(
                f"finding conservation: finding {sid} triage disagrees "
                f"(Markdown {md['triage']!r}, sidecar {sc.get('triage')!r})"
            )


def validate_markdown_severity_groups(
    content: str, result: ValidationResult
) -> None:
    positions = [content.find(f"### {severity}") for severity in SEVERITY_ORDER]
    if any(position < 0 for position in positions):
        result.add_error(
            "current staging doc must include Critical, High, Medium, Low groups"
        )
    elif positions != sorted(positions):
        result.add_error("severity groups are not ordered Critical, High, Medium, Low")


def detect_solo_collapse(staging_path: Path, content: str) -> bool:
    """Detect legacy Solo-collapse while current panels validate from sidecars.

    Returns True when the staging doc is a code review (not a plan/RFC/confluence
    review) AND the Panel table shows the default panel agents as folded into
    Solo / skipped while only an orchestrator-Solo row ran. See UL#190.
    """
    filename = staging_path.name.lower()
    # The filename prefix is the authoritative review-type discriminator:
    #   -code-review-r<N>  -> execute-plan Phase 3 code review (panel expected)
    #   -branch-review-    -> standalone doing-code-review branch review (panel expected)
    #   -plan-review-r<N>  -> pre-execution plan review (NON-panel; Solo OK)
    #   -rfc-review-       -> RFC review (NON-panel)
    #   -confluence-review -> Confluence review (NON-panel)
    # The Type line is NOT used as a discriminator: an execute-plan Phase 3 code
    # review is legitimately "Branch Review (Plan-based, ...)" but still runs
    # the full panel, so "Plan-based" must not exempt it.
    is_panel_review = "-code-review-r" in filename or "-branch-review-" in filename
    if not is_panel_review:
        return False
    if re.search(r"^\|\s*Worker\s*\|", content, re.MULTILINE):
        return False

    # Parse the Panel table rows. A row is "panel-ran" for an agent if the
    # agent name appears and its status is complete (regardless of Raw count;
    # an agent may legitimately return zero findings).
    panel_section = content.split("### Panel", 1)[1] if "### Panel" in content else ""
    # Stop at the next ### subsection.
    panel_section = re.split(r"\n### ", panel_section, maxsplit=1)[0]
    folded_or_skipped = 0
    present_complete = 0
    for agent in LEGACY_DEFAULT_PANEL_AGENTS:
        # Match a table row mentioning this agent. Status is the 2nd column.
        row_re = re.compile(
            rf"\|\s*[^|]*\b{re.escape(agent)}\b[^|]*\s*\|\s*([^||]+)\s*\|",
            re.IGNORECASE,
        )
        match = row_re.search(panel_section)
        if not match:
            continue
        status = match.group(1).strip().lower()
        if "folded into solo" in status or status.startswith("skipped"):
            folded_or_skipped += 1
        elif status.startswith("complete"):
            present_complete += 1
    # Solo-collapse: all legacy default agents are folded/skipped, or none
    # completed while a majority are folded/skipped (an orchestrator-Solo row
    # claimed completion in place of the panel).
    if folded_or_skipped >= len(LEGACY_DEFAULT_PANEL_AGENTS):
        return True
    if present_complete == 0 and folded_or_skipped >= 4:
        return True
    return False


def validate_staging_file(
    path: Path,
    *,
    hard: bool = False,
    expected_digest: str | None = None,
    source_kind: str | None = None,
) -> ValidationResult:
    result = ValidationResult(path=path)
    if not path.is_file():
        result.add_error("file does not exist")
        return result

    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        result.add_error(f"cannot read file: {exc}")
        return result

    size = path.stat().st_size

    for heading in ("## Metadata", "## Review Statistics"):
        if heading not in content:
            result.add_error(f"missing {heading}")

    if "### Panel" not in content:
        result.add_error("missing ### Panel under Review Statistics")

    # Legacy anti-Solo check. Current five-worker panels validate from sidecars.
    if "### Panel" in content and detect_solo_collapse(path, content):
        result.add_error(
            "Solo-collapse detected: the legacy default review-panel agents are "
            "'folded into Solo' or skipped, but only an orchestrator-Solo row "
            "ran. A code review must launch the full review-panel-selection.md "
            "panel (Hard Gate #1); 'Solo' is a dedup label, not a mode. See UL#190."
        )

    if "### Counts" not in content and "Agents launched" not in content:
        result.add_warning("missing ### Counts or Agents launched row")

    if "### Triage outcomes" not in content and "Pending triage" not in content:
        result.add_warning("missing ### Triage outcomes or Pending triage placeholder")

    medium_plus = extract_medium_plus_count(content)
    staged_count = extract_staged_count(content)
    result.medium_plus_expected = max(staged_count, medium_plus)
    finding_blocks = split_finding_blocks(content)
    result.finding_sections = len(finding_blocks)

    # Cross-check: Verdict claiming Medium+ cannot pair with Staged findings: 0.
    if staged_count == 0 and medium_plus > 0:
        result.add_error(
            f"verdict claims {medium_plus} Medium+ but Counts/Metadata staged findings is 0"
        )

    if staged_count > 0 or medium_plus > 0:
        effective_staged = max(staged_count, medium_plus)
        if not re.search(r"^## Findings\s*$", content, re.MULTILINE):
            result.add_error("verdict claims Medium+ but missing ## Findings section")
        for idx, block in enumerate(finding_blocks, start=1):
            has_comment, has_analysis = finding_has_comment_and_analysis(block)
            if has_comment or has_analysis:
                if not has_comment:
                    result.add_error(f"finding {idx} missing #### Comment")
                if not has_analysis:
                    result.add_error(f"finding {idx} missing #### Analysis")
            elif not is_legacy_finding_block(block):
                result.add_error(
                    f"finding {idx} missing #### Comment/Analysis (legacy blocks need "
                    f"Status/Triage and >= {LEGACY_MIN_BLOCK_CHARS} chars)"
                )
        if len(finding_blocks) < effective_staged:
            delta = effective_staged - len(finding_blocks)
            if len(finding_blocks) == 0:
                result.add_error(
                    f"staged count expects {effective_staged} findings but no finding sections"
                )
            else:
                result.add_error(
                    f"staged count expects {effective_staged} findings but only "
                    f"{len(finding_blocks)} finding sections (gap {delta})"
                )
        if size < STUB_BYTE_THRESHOLD and effective_staged > 0:
            result.add_error(
                f"stub suspected: {effective_staged} staged findings claimed but file is only "
                f"{size} bytes (threshold {STUB_BYTE_THRESHOLD})"
            )
    else:
        if "## Review Statistics" not in content:
            result.add_error("clear round still requires ## Review Statistics")

    validate_discarded_findings(content, result)
    validate_stats_sidecar(
        path,
        content,
        result,
        expected_digest=expected_digest,
        source_kind=source_kind,
    )

    if hard and not result.ok:
        return result
    if not hard and result.errors:
        result.add_warning("soft mode: errors reported but exit code remains 0")
    return result


def newest_staging_for_branch(repo_root: Path, branch: str) -> Path | None:
    reviews_dir = resolve_reviews_dir(repo_root)
    if not reviews_dir.is_dir():
        return None
    slug = branch.lower().replace("/", "-")
    candidates = [
        p
        for p in reviews_dir.glob("*.md")
        if slug in p.name.lower() and is_staging_review_path(p)
    ]
    if not candidates:
        candidates = [p for p in reviews_dir.glob("*.md") if is_staging_review_path(p)]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


_CHECK_FAILURES = [0]


def _make_check():
    def check(name: str, ok: bool) -> None:
        if ok:
            print(f"OK: {name}")
        else:
            print(f"FAIL: {name}", file=sys.stderr)
            _CHECK_FAILURES[0] += 1

    return check


def _write_staging(root: Path, name: str, md: str, sidecar: object | None = None) -> Path:
    """Write a staging markdown doc (and optional stats sidecar) under root."""
    path = root / name
    path.write_text(md)
    if sidecar is not None:
        path.with_suffix(".stats.json").write_text(
            sidecar if isinstance(sidecar, str) else json.dumps(sidecar)
        )
    return path


def _current_clear_payload() -> dict:
    """Canonical current-format five-worker clear-review sidecar payload."""
    return {
        "panel_mode": "full",
        "selection_reason": None,
        "source_digest": "abc123",
        "escalation_reason": None,
        "counts": {"workers_launched": 5, "staged_findings": 0},
        "panel": [
            {
                "worker": worker,
                "lenses": lenses,
                "parent_worker": None,
                "descendant_launches": [],
                "status": "complete",
                "raw": 0,
                "solo": 0,
                "echo": 0,
                "relaunch": False,
            }
            for worker, lenses in (
                ("correctness-completeness", ["quality", "implementation"]),
                ("testing", ["testing"]),
                ("design-simplicity", ["architecture", "simplification"]),
                ("contract-docs", ["documentation"]),
                ("risk", ["security"]),
            )
        ],
        "findings": [],
        "overflow": [],
    }


def _current_clear_markdown(title: str = "current") -> str:
    import textwrap

    return textwrap.dedent(
        f"""\
        # Branch Review: {title}
        ## Metadata
        - Panel mode: full
        - Source digest: abc123
        - Findings: 0
        - Status: STAGED
        ## Review Statistics
        ### Panel
        | Worker | Lenses | Parent worker | Status | Raw | Solo | Echo | Relaunch |
        |--------|--------|---------------|--------|-----|------|------|----------|
        | correctness-completeness | quality, implementation | none | complete | 0 | 0 | 0 | no |
        | testing | testing | none | complete | 0 | 0 | 0 | no |
        | design-simplicity | architecture, simplification | none | complete | 0 | 0 | 0 | no |
        | contract-docs | documentation | none | complete | 0 | 0 | 0 | no |
        | risk | security | none | complete | 0 | 0 | 0 | no |
        ### Counts
        - Workers launched: 5
        - Staged findings: 0
        ### Deduplication groups
        None.
        ### Discarded findings
        None.
        ### Severity calibration
        None.
        ### Triage outcomes
        Pending triage.
        ## Findings
        ### Critical
        None.
        ### High
        None.
        ### Medium
        None.
        ### Low
        None.
        ### Overflow manifest
        None.
        """
    )


def _current_finding(
    *,
    id: int = 1,
    severity: str = "Medium",
    blocking: bool = False,
    blast_radius: str = "single-service",
    reachability: str = "plausible-edge",
    confidence: str = "strong-evidence",
    consequence: str = "Concrete harmful outcome on edge path.",
    workers: tuple[str, ...] = ("correctness-completeness",),
    **extra,
) -> dict:
    """Build a single valid current-format finding dict."""
    finding = {
        "id": id,
        "severity": severity,
        "blocking": blocking,
        "blast_radius": blast_radius,
        "reachability": reachability,
        "confidence": confidence,
        "consequence": consequence,
        "pattern": "quality#edge-case",
        "workers": list(workers),
    }
    finding.update(extra)
    return finding


def _payload_with_findings(findings: list[dict]) -> dict:
    """Canonical clear payload with ``findings`` set and counts adjusted."""
    payload = _current_clear_payload()
    payload["findings"] = findings
    payload["counts"]["staged_findings"] = len(findings)
    return payload


def _current_findings_markdown(findings: list[dict], *, title: str = "conservation") -> str:
    """Build a current-format staging markdown whose Findings section lists the
    given findings under their severity groups.

    Each finding dict must carry ``id``, ``severity``, ``blocking`` (bool), and
    optionally ``triage`` (default ``pending``). The Markdown mirrors the
    sidecar so the conservation cross-check can reconcile the two.
    """
    by_severity: dict[str, list[dict]] = {sev: [] for sev in SEVERITY_ORDER}
    for finding in findings:
        by_severity.setdefault(finding.get("severity", "Low"), []).append(finding)
    sections = []
    for severity in SEVERITY_ORDER:
        rows = by_severity.get(severity, [])
        if not rows:
            sections.append(f"### {severity}\nNone.")
            continue
        lines = [f"### {severity}"]
        for finding in rows:
            fid = finding.get("id", 0)
            blocking = finding.get("blocking", False)
            triage = finding.get("triage", "pending")
            lines.extend(
                [
                    f"#### F{fid}. Sample finding {fid}",
                    f"- **Blocking**: {'true' if blocking else 'false'}",
                    f"- **Triage**: {triage}",
                    "#### Comment",
                    (
                        f"Concrete claim for finding {fid}: the reviewed change "
                        "introduces a reachable condition where the stated contract "
                        "and observed behavior diverge. Anchored to the exact lines "
                        "in the reviewed artifact. Why it matters: a follow-on "
                        "caller relies on the documented invariant, so the gap can "
                        "surface as wrong normal-path behavior when the caller "
                        "exercises the affected branch under typical load. Fix: "
                        "align the code with the contract, or update the contract "
                        "and every caller that depends on the prior shape. Record "
                        "the verification anchor and the discriminating input that "
                        "demonstrates the divergence."
                    ),
                    "#### Analysis",
                    (
                        "Verified against the reviewed artifact at the cited anchor. "
                        "Reachability confirmed on a normal path under stated inputs "
                        "and realistic load assumptions. No mitigating guard, feature "
                        "flag, or upstream validation was present. Severity reflects "
                        "tangible consequence, not effort, reviewer fatigue, or "
                        "comment length; the budget and ordering rules apply."
                    ),
                ]
            )
        sections.append("\n".join(lines))
    findings_block = "\n\n".join(sections)
    findings_count = len(findings)
    return "\n".join(
        [
            f"# Branch Review: {title}",
            "## Metadata",
            "- Panel mode: full",
            "- Source digest: abc123",
            f"- Findings: {findings_count}",
            f"- Staged findings: {findings_count}",
            "- Status: STAGED",
            "## Review Statistics",
            "### Panel",
            "| Worker | Lenses | Parent worker | Status | Raw | Solo | Echo | Relaunch |",
            "|--------|--------|---------------|--------|-----|------|------|----------|",
            "| correctness-completeness | quality, implementation | none | complete | 0 | 0 | 0 | no |",
            "| testing | testing | none | complete | 0 | 0 | 0 | no |",
            "| design-simplicity | architecture, simplification | none | complete | 0 | 0 | 0 | no |",
            "| contract-docs | documentation | none | complete | 0 | 0 | 0 | no |",
            "| risk | security | none | complete | 0 | 0 | 0 | no |",
            "### Counts",
            "- Workers launched: 5",
            f"- Staged findings: {findings_count}",
            "### Deduplication groups",
            "None.",
            "### Discarded findings",
            "None.",
            "### Severity calibration",
            "None.",
            "### Triage outcomes",
            "Pending triage.",
            "## Findings",
            "",
            findings_block,
            "",
            "### Overflow manifest",
            "None.",
            "## Verdict for this round (before fixes)",
            f"{findings_count} Medium+ findings accepted for fix",
            "",
        ]
    )


# ---------------------------------------------------------------------------
# Self-test families. Each takes the tmp root and the shared check() closure.
# ---------------------------------------------------------------------------


def _selftest_path_names(_root: Path, check) -> None:
    check(
        "PR staging name without 'review'",
        is_staging_review_path(Path("2026-07-17-PR-99-feature-r1.md")),
    )
    check(
        "confluence staging without round suffix",
        is_staging_review_path(Path("2026-07-17-confluence-review-foo.md")),
    )
    check(
        "branch-review round name",
        is_staging_review_path(Path("2026-07-17-branch-review-main-r2.md")),
    )


def _selftest_legacy_stubs(root: Path, check) -> None:
    import textwrap

    stub = _write_staging(
        root,
        "2026-07-17-branch-review-x-r1.md",
        textwrap.dedent(
            """\
            # Branch Review: x
            ## Metadata
            - Findings: 2
            - Status: STAGED
            ## Review Statistics
            ### Panel
            | Agent | Status | Raw | Solo | Echo | Relaunch |
            |-------|--------|-----|------|------|----------|
            | quality | complete | 0 | 0 | 0 | no |
            ### Counts
            - Agents launched: 1
            - Agents skipped: 0
            - Raw findings (all agents): 0
            - Staged findings: 2
            - Discarded during synthesis: 0
            - Solo staged (unique agent origin): 0
            - Echo staged (multi-agent dedup): 0
            ### Deduplication groups
            None (each staged finding had a single agent origin).
            ### Discarded findings
            None.
            ### Severity calibration
            None (agent severities matched staged severities).
            ### Triage outcomes
            Pending triage.
            ## Findings
            ### 1. Thin
            - **Severity**: Medium
            - **Triage**: pending
            ### 2. Also thin
            - **Severity**: Low
            - **Triage**: pending
            ## Verdict for this round (before fixes)
            **2 Medium+ findings accepted for fix**
            """
        ),
    )
    result = validate_staging_file(stub, hard=True)
    check("stub findings without Comment/Analysis fail hard", not result.ok)
    check(
        "stub fails specifically for missing Comment",
        any("Comment" in e for e in result.errors),
    )
    check(
        "stub fails for missing stats sidecar",
        any("stats sidecar" in e for e in result.errors),
    )
    check(
        "bullet staged count 2 from stub",
        extract_staged_count(stub.read_text()) == 2,
    )

    gap = _write_staging(
        root,
        "2026-07-17-branch-review-gap-r1.md",
        textwrap.dedent(
            """\
            # Branch Review: gap
            ## Metadata
            - Findings: 3
            - Stats sidecar: skipped
            - Status: STAGED
            ## Review Statistics
            ### Panel
            | Agent | Status | Raw | Solo | Echo | Relaunch |
            |-------|--------|-----|------|------|----------|
            | quality | complete | 1 | 1 | 0 | no |
            ### Counts
            - Staged findings: 3
            ### Deduplication groups
            None (each staged finding had a single agent origin).
            ### Discarded findings
            None.
            ### Severity calibration
            None (agent severities matched staged severities).
            ### Triage outcomes
            Pending triage.
            ## Findings
            ### 1. Only one
            - **Severity**: Medium
            - **Triage**: pending
            #### Comment
            Contract says X. Code does Y. Why it matters: Z. Fix: pad.
            #### Analysis
            Verified against HEAD.
            ## Verdict for this round (before fixes)
            **3 Medium+ findings accepted for fix**
            """
        )
        + ("x" * 2000),
    )
    gap_result = validate_staging_file(gap, hard=True)
    check(
        "count gap 1-4 fails hard",
        any("gap" in e for e in gap_result.errors),
    )
    check(
        "stats skip with staged findings fails hard",
        any("Stats sidecar: skipped" in e for e in gap_result.errors),
    )

    wrong = _write_staging(
        root,
        "2026-07-17-branch-review-wo-r1.md",
        textwrap.dedent(
            """\
            # Branch Review: wo
            ## Metadata
            - Findings: 0
            - Status: STAGED
            ## Review Statistics
            ### Panel
            | Agent | Status | Raw | Solo | Echo | Relaunch |
            |-------|--------|-----|------|------|----------|
            | quality | complete | 0 | 0 | 0 | no |
            ### Counts
            - Staged findings: 0
            ### Deduplication groups
            None (each staged finding had a single agent origin).
            ### Discarded findings
            | Agent | Agent severity | Pattern | Theme | Reason | Notes |
            |-------|----------------|---------|-------|--------|-------|
            | architecture | Medium | architecture#x | IP drift | wrong-owner | |
            ### Severity calibration
            None (agent severities matched staged severities).
            ### Triage outcomes
            Pending triage.
            ## Verdict for this round (before fixes)
            0 Medium+ findings; clear round
            """
        ),
        '{"panel":[],"counts":{}}',
    )
    wo_result = validate_staging_file(wrong, hard=True)
    check(
        "wrong-owner without lead fails hard",
        any("wrong-owner" in e and "lead" in e for e in wo_result.errors),
    )

    clear = _write_staging(
        root,
        "2026-07-17-branch-review-clear-r1.md",
        textwrap.dedent(
            """\
            # Branch Review: clear
            ## Metadata
            - Findings: 0
            - Status: STAGED
            ## Review Statistics
            ### Panel
            | Agent | Status | Raw | Solo | Echo | Relaunch |
            |-------|--------|-----|------|------|----------|
            | quality | complete | 0 | 0 | 0 | no |
            ### Counts
            - Agents launched: 1
            - Agents skipped: 0
            - Raw findings (all agents): 0
            - Staged findings: 0
            - Discarded during synthesis: 0
            - Solo staged (unique agent origin): 0
            - Echo staged (multi-agent dedup): 0
            ### Deduplication groups
            None (each staged finding had a single agent origin).
            ### Discarded findings
            None.
            ### Severity calibration
            None (agent severities matched staged severities).
            ### Triage outcomes
            | Agent | Staged | Fixed | Dropped | Deferred | Pending |
            |-------|--------|-------|---------|----------|---------|
            | quality | 0 | 0 | 0 | 0 | 0 |
            ## Verdict for this round (before fixes)
            0 Medium+ findings; clear round
            """
        ),
        '{"panel":[{"agent":"quality","status":"complete","raw":0,"solo":0,"echo":0}],'
        '"counts":{"staged_findings":0}}',
    )
    clear_result = validate_staging_file(clear, hard=True)
    check("clear round with sidecar passes hard", clear_result.ok)

    lie = _write_staging(
        root,
        "2026-07-17-branch-review-lie-r1.md",
        textwrap.dedent(
            """\
            # Branch Review: lie
            ## Metadata
            - Findings: 0
            - Stats sidecar: skipped
            - Status: STAGED
            ## Review Statistics
            ### Panel
            | Agent | Status | Raw | Solo | Echo | Relaunch |
            |-------|--------|-----|------|------|----------|
            | quality | complete | 0 | 0 | 0 | no |
            ### Counts
            - Staged findings: 0
            ### Deduplication groups
            None (each staged finding had a single agent origin).
            ### Discarded findings
            None.
            ### Severity calibration
            None (agent severities matched staged severities).
            ### Triage outcomes
            Pending triage.
            ## Verdict for this round (before fixes)
            **3 Medium+ findings accepted for fix**
            """
        ),
    )
    lie_result = validate_staging_file(lie, hard=True)
    check(
        "clear-round lie (staged 0 + verdict Medium+) fails hard",
        not lie_result.ok
        and any("verdict claims" in e for e in lie_result.errors),
    )

    phrase = _write_staging(
        root,
        "2026-07-17-branch-review-phrase-r1.md",
        textwrap.dedent(
            """\
            # Branch Review: phrase
            ## Metadata
            - Findings: 0
            - Status: STAGED
            ## Review Statistics
            ### Panel
            | Agent | Status | Raw | Solo | Echo | Relaunch |
            |-------|--------|-----|------|------|----------|
            | quality | complete | 0 | 0 | 0 | no |
            ### Counts
            - Staged findings: 0
            ### Deduplication groups
            None (each staged finding had a single agent origin).
            ### Discarded findings
            None.
            ### Severity calibration
            None (agent severities matched staged severities).
            ### Triage outcomes
            | Agent | Staged | Fixed | Dropped | Deferred | Pending |
            |-------|--------|-------|---------|----------|---------|
            | quality | 0 | 0 | 0 | 0 | 0 |
            ## Findings
            ### 1. Mentions skip phrase
            - **Severity**: Low
            - **Triage**: dropped
            #### Comment
            Discussed `Stats sidecar: skipped` as a waived option for clear rounds.
            #### Analysis
            Prose only; staged count remains 0.
            ## Verdict for this round (before fixes)
            0 Medium+ findings; clear round
            """
        ),
        '{"panel":[],"counts":{"staged_findings":0}}',
    )
    phrase_result = validate_staging_file(phrase, hard=True)
    check(
        "Stats sidecar phrase outside Metadata does not waive sidecar",
        phrase_result.ok,
    )


def _selftest_current_contract(root: Path, check) -> None:
    """Family: current-format contract (clear, descendants, overflow, focused,
    sixth-worker, blocking-independence, severity order)."""
    current = _write_staging(
        root,
        "2026-07-17-branch-review-current-r1.md",
        _current_clear_markdown("current"),
    )
    current_payload = _current_clear_payload()
    current_sidecar = current.with_suffix(".stats.json")
    current_sidecar.write_text(json.dumps(current_payload))
    check(
        "current five-worker clear review passes",
        validate_staging_file(current, hard=True).ok,
    )

    hidden_payload = json.loads(json.dumps(current_payload))
    hidden_payload["panel"][0]["descendant_launches"] = ["hidden-child"]
    current_sidecar.write_text(json.dumps(hidden_payload))
    hidden_result = validate_staging_file(current, hard=True)
    check(
        "concealed descendant launch fails",
        any("not flattened" in error for error in hidden_result.errors),
    )

    overflow_payload = json.loads(json.dumps(current_payload))
    overflow_payload["overflow"] = [
        {"severity": "Critical", "blocking": False, "pattern": "quality#x"}
    ]
    current_sidecar.write_text(json.dumps(overflow_payload))
    overflow_result = validate_staging_file(current, hard=True)
    check(
        "non-blocking Critical cannot enter overflow",
        any("cannot be in overflow" in error for error in overflow_result.errors),
    )

    # focused panel without selection_reason must fail hard. The base
    # payload already has selection_reason: None, so flipping panel_mode
    # alone exercises the focused-panel metadata gate.
    focused_payload = json.loads(json.dumps(current_payload))
    focused_payload["panel_mode"] = "focused"
    current_sidecar.write_text(json.dumps(focused_payload))
    focused_result = validate_staging_file(current, hard=True)
    check(
        "focused panel missing selection_reason fails",
        any("selection_reason" in error for error in focused_result.errors),
    )

    # six worker launches without escalation_reason must fail hard.
    sixth_payload = json.loads(json.dumps(current_payload))
    sixth_payload["panel"].append(
        {
            "worker": "escalation-risk",
            "lenses": ["concurrency"],
            "parent_worker": None,
            "descendant_launches": [],
            "status": "complete",
            "raw": 0,
            "solo": 0,
            "echo": 0,
            "relaunch": False,
        }
    )
    sixth_payload["counts"]["workers_launched"] = 6
    current_sidecar.write_text(json.dumps(sixth_payload))
    sixth_result = validate_staging_file(current, hard=True)
    check(
        "sixth worker missing escalation_reason fails",
        any("escalation_reason" in error for error in sixth_result.errors),
    )

    # blocking/severity independence: a blocking Low cannot defer to overflow
    # (it blocks readiness), while a non-blocking Medium can.
    blocking_low_payload = json.loads(json.dumps(current_payload))
    blocking_low_payload["overflow"] = [
        {
            "id": 1,
            "severity": "Low",
            "blocking": True,
            "pattern": "quality#low-blocking",
        }
    ]
    current_sidecar.write_text(json.dumps(blocking_low_payload))
    blocking_low_result = validate_staging_file(current, hard=True)
    check(
        "blocking Low cannot defer to overflow (blocks readiness)",
        any("cannot be in overflow" in error for error in blocking_low_result.errors),
    )

    nonblocking_medium_payload = json.loads(json.dumps(current_payload))
    nonblocking_medium_payload["overflow"] = [
        {
            "id": 2,
            "severity": "Medium",
            "blocking": False,
            "pattern": "quality#medium-nonblocking",
        }
    ]
    current_sidecar.write_text(json.dumps(nonblocking_medium_payload))
    nonblocking_medium_result = validate_staging_file(current, hard=True)
    check(
        "non-blocking Medium may defer to overflow (does not block readiness)",
        not any(
            "cannot be in overflow" in error
            for error in nonblocking_medium_result.errors
        ),
    )

    order_result = ValidationResult(path=Path("order"))
    validate_finding_order(
        [
            {
                "id": 1,
                "severity": "Low",
                "blocking": False,
                "blast_radius": "local",
                "reachability": "theoretical",
                "confidence": "hypothesis",
            },
            {
                "id": 2,
                "severity": "High",
                "blocking": True,
                "blast_radius": "global",
                "reachability": "expected",
                "confidence": "verified",
            },
        ],
        order_result,
    )
    check("severity order is enforced", not order_result.ok)


# ---------------------------------------------------------------------------
# New contract families (Task 3). RED -> GREEN for each.
# ---------------------------------------------------------------------------


def _selftest_source_digest(root: Path, check) -> None:
    """F2: source-digest authority. Digest is SHA-256 of exact reviewed bytes;
    orchestrator supplies expected_digest + source_kind; mismatch fails."""
    plan_bytes = "plan body\n".encode("utf-8")
    plan_digest = compute_source_digest("plan", plan_bytes)
    # SHA-256 of "plan body\n" (UTF-8), lowercase 64-hex.
    check(
        "compute_source_digest returns lowercase 64-hex sha256",
        plan_digest == hashlib.sha256(plan_bytes).hexdigest()
        and len(plan_digest) == 64
        and plan_digest == plan_digest.lower(),
    )
    # Recipe: same bytes -> same digest; code vs document both hash exact bytes.
    code_bytes = b"diff --git a/x b/x\n+added\n"
    check(
        "compute_source_digest code recipe hashes exact diff bytes",
        compute_source_digest("code", code_bytes)
        == hashlib.sha256(code_bytes).hexdigest(),
    )

    base_md = _current_clear_markdown("digest")
    base_payload = _current_clear_payload()

    # Case A: placeholder (non-64-hex) digest must fail hard (invalid syntax),
    # even without expected_digest, when source_kind is declared.
    bad_payload = json.loads(json.dumps(base_payload))
    bad_payload["source_digest"] = "abc123"
    bad_payload["source_kind"] = "plan"
    bad_path = _write_staging(
        root, "2026-07-17-branch-review-digest-syntax-r1.md", base_md, bad_payload
    )
    bad_result = validate_staging_file(bad_path, hard=True)
    check(
        "placeholder digest with source_kind fails (invalid syntax)",
        any("source_digest" in e for e in bad_result.errors),
    )

    # Case B: a valid 64-hex digest that does NOT match the expected digest
    # must fail hard (stale digest) when expected_digest is supplied.
    stale_payload = json.loads(json.dumps(base_payload))
    stale_payload["source_digest"] = "0" * 64
    stale_payload["source_kind"] = "plan"
    stale_path = _write_staging(
        root, "2026-07-17-branch-review-digest-stale-r1.md", base_md, stale_payload
    )
    stale_result = validate_staging_file(
        stale_path, hard=True, expected_digest=plan_digest, source_kind="plan"
    )
    check(
        "stale digest (mismatch vs expected_digest) fails",
        any(
            "source_digest" in e and ("stale" in e or "mismatch" in e or "expected" in e)
            for e in stale_result.errors
        ),
    )

    # Case C: the correct computed digest passes freshness comparison.
    fresh_payload = json.loads(json.dumps(base_payload))
    fresh_payload["source_digest"] = plan_digest
    fresh_payload["source_kind"] = "plan"
    fresh_path = _write_staging(
        root, "2026-07-17-branch-review-digest-fresh-r1.md", base_md, fresh_payload
    )
    fresh_result = validate_staging_file(
        fresh_path, hard=True, expected_digest=plan_digest, source_kind="plan"
    )
    check(
        "fresh digest (matches expected_digest) passes",
        fresh_result.ok,
    )

    # Case D: invalid source_kind enum must fail.
    kind_payload = json.loads(json.dumps(base_payload))
    kind_payload["source_digest"] = plan_digest
    kind_payload["source_kind"] = "wiki"
    kind_path = _write_staging(
        root, "2026-07-17-branch-review-digest-kind-r1.md", base_md, kind_payload
    )
    kind_result = validate_staging_file(kind_path, hard=True)
    check(
        "invalid source_kind enum fails",
        any("source_kind" in e for e in kind_result.errors),
    )

    # Case E (F2): when the orchestrator supplies a source_kind that differs
    # from the sidecar-declared source_kind, the validator must fail with a
    # mismatch error. This pins the opt-in backward-compat boundary: legacy
    # payloads (no source_kind) stay presence-only, but when both sides
    # declare a kind they must agree.
    mismatch_payload = json.loads(json.dumps(base_payload))
    mismatch_payload["source_digest"] = plan_digest
    mismatch_payload["source_kind"] = "plan"
    mismatch_path = _write_staging(
        root, "2026-07-17-branch-review-digest-kindmismatch-r1.md", base_md, mismatch_payload
    )
    mismatch_result = validate_staging_file(
        mismatch_path, hard=True, expected_digest=plan_digest, source_kind="code"
    )
    check(
        "source_kind mismatch (orchestrator vs sidecar) fails",
        any("source_kind mismatch" in e for e in mismatch_result.errors),
    )
    # And the matching positive: same kind on both sides does not error on mismatch.
    agree_result = validate_staging_file(
        mismatch_path, hard=True, expected_digest=plan_digest, source_kind="plan"
    )
    check(
        "source_kind agreement (orchestrator == sidecar) does not flag mismatch",
        not any("source_kind mismatch" in e for e in agree_result.errors),
    )


def _selftest_typed_current_schema(root: Path, check) -> None:
    """Enforce typed fields in sidecar findings: blocking is a real bool;
    severity, blast_radius, reachability, confidence are enum-checked.

    The Markdown mirrors the canonical well-typed finding so the conservation
    cross-check stays quiet; the typed-field mutations under test change only
    sidecar field values, so the typed-rule errors are the load-bearing ones."""
    md = _current_findings_markdown([_current_finding()], title="typed")

    # Baseline: a single well-typed non-blocking Medium finding passes.
    good = _payload_with_findings([_current_finding()])
    good_path = _write_staging(
        root, "2026-07-17-branch-review-typed-good-r1.md", md, good
    )
    check(
        "well-typed finding passes",
        validate_staging_file(good_path, hard=True).ok,
    )

    # String boolean for blocking must fail (not coerced to truthy/falsy).
    str_bool = json.loads(json.dumps(good))
    str_bool["findings"][0]["blocking"] = "false"
    str_bool_path = _write_staging(
        root, "2026-07-17-branch-review-typed-strbool-r1.md", md, str_bool
    )
    str_bool_res = validate_staging_file(str_bool_path, hard=True)
    check(
        "string 'false' blocking value fails (must be real bool)",
        any("blocking" in e for e in str_bool_res.errors),
    )

    # Integer blocking must fail.
    int_bool = json.loads(json.dumps(good))
    int_bool["findings"][0]["blocking"] = 1
    int_bool_path = _write_staging(
        root, "2026-07-17-branch-review-typed-intbool-r1.md", md, int_bool
    )
    int_bool_res = validate_staging_file(int_bool_path, hard=True)
    check(
        "int blocking value fails (must be real bool)",
        any("blocking" in e for e in int_bool_res.errors),
    )

    # Invalid blast_radius enum must fail.
    bad_blast = json.loads(json.dumps(good))
    bad_blast["findings"][0]["blast_radius"] = "whole-world"
    bad_blast_path = _write_staging(
        root, "2026-07-17-branch-review-typed-blast-r1.md", md, bad_blast
    )
    check(
        "invalid blast_radius enum fails",
        any(
            "blast_radius" in e
            for e in validate_staging_file(bad_blast_path, hard=True).errors
        ),
    )

    # Invalid reachability enum must fail.
    bad_reach = json.loads(json.dumps(good))
    bad_reach["findings"][0]["reachability"] = "maybe"
    bad_reach_path = _write_staging(
        root, "2026-07-17-branch-review-typed-reach-r1.md", md, bad_reach
    )
    check(
        "invalid reachability enum fails",
        any(
            "reachability" in e
            for e in validate_staging_file(bad_reach_path, hard=True).errors
        ),
    )

    # Invalid confidence enum must fail.
    bad_conf = json.loads(json.dumps(good))
    bad_conf["findings"][0]["confidence"] = "gut-feel"
    bad_conf_path = _write_staging(
        root, "2026-07-17-branch-review-typed-conf-r1.md", md, bad_conf
    )
    check(
        "invalid confidence enum fails",
        any(
            "confidence" in e
            for e in validate_staging_file(bad_conf_path, hard=True).errors
        ),
    )


def _selftest_finding_budget(root: Path, check) -> None:
    """Finding budget: per worker, all Critical + all blocking expand; up to 5
    additional non-blocking High/Medium; up to 2 additional non-blocking Low.
    Remaining go to overflow. Budget is enforced per-worker bucket when
    findings carry a ``workers`` list; otherwise a single global bucket.

    Each case writes a Markdown that mirrors its findings so the conservation
    cross-check does not add noise; the budget rule is the load-bearing gate."""

    def stage(name: str, findings: list[dict]) -> Path:
        return _write_staging(
            root,
            name,
            _current_findings_markdown(findings, title="budget"),
            _payload_with_findings(findings),
        )

    def hm(id_: int) -> dict:
        return _current_finding(id=id_, severity="Medium", blocking=False)

    def low(id_: int) -> dict:
        return _current_finding(
            id=id_, severity="Low", blocking=False, reachability="theoretical"
        )

    # Positive: exactly 5 non-blocking Medium + 2 non-blocking Low for one
    # worker is within budget.
    ok_path = stage(
        "2026-07-17-branch-review-budget-ok-r1.md",
        [hm(1), hm(2), hm(3), hm(4), hm(5), low(6), low(7)],
    )
    check(
        "5 non-blocking High/Medium + 2 non-blocking Low within budget passes",
        validate_staging_file(ok_path, hard=True).ok,
    )

    # Negative: a sixth non-blocking High/Medium for the SAME worker fails.
    over_hm_path = stage(
        "2026-07-17-branch-review-budget-overhm-r1.md",
        [hm(1), hm(2), hm(3), hm(4), hm(5), hm(6)],
    )
    check(
        "sixth non-blocking High/Medium for one worker exceeds budget",
        any(
            "budget" in e or "findings" in e
            for e in validate_staging_file(over_hm_path, hard=True).errors
        ),
    )

    # Negative: a third non-blocking Low for the SAME worker fails.
    over_low_path = stage(
        "2026-07-17-branch-review-budget-overlow-r1.md",
        [low(1), low(2), low(3)],
    )
    check(
        "third non-blocking Low for one worker exceeds budget",
        any(
            "budget" in e or "findings" in e
            for e in validate_staging_file(over_low_path, hard=True).errors
        ),
    )

    # Budget is per-worker: 6 non-blocking Medium split across two workers
    # (3 each) is within budget. This requires explicit `workers` attribution.
    split_path = stage(
        "2026-07-17-branch-review-budget-split-r1.md",
        [
            _current_finding(id=1, severity="Medium", workers=("correctness-completeness",)),
            _current_finding(id=2, severity="Medium", workers=("correctness-completeness",)),
            _current_finding(id=3, severity="Medium", workers=("correctness-completeness",)),
            _current_finding(id=4, severity="Medium", workers=("testing",)),
            _current_finding(id=5, severity="Medium", workers=("testing",)),
            _current_finding(id=6, severity="Medium", workers=("testing",)),
        ],
    )
    check(
        "6 Medium split 3/3 across two workers is within per-worker budget",
        validate_staging_file(split_path, hard=True).ok,
    )

    # Critical and blocking findings are never budget-capped.
    crit_path = stage(
        "2026-07-17-branch-review-budget-crit-r1.md",
        [_current_finding(id=i, severity="Critical", blocking=False) for i in range(1, 8)],
    )
    check(
        "seven non-blocking Critical findings do not exceed budget (always expand)",
        validate_staging_file(crit_path, hard=True).ok,
    )


def _selftest_finding_conservation(root: Path, check) -> None:
    """Markdown findings, sidecar findings, counts, IDs, severity, blocking,
    and triage must all agree."""
    base_finding = _current_finding(id=1, severity="Medium", blocking=False)
    base_finding["triage"] = "pending"

    # Positive: Markdown and sidecar agree (1 finding, id 1, Medium,
    # non-blocking, pending).
    ok_md = _current_findings_markdown([base_finding])
    ok_payload = _payload_with_findings([base_finding])
    ok_path = _write_staging(
        root, "2026-07-17-branch-review-cons-ok-r1.md", ok_md, ok_payload
    )
    check(
        "matching Markdown and sidecar findings pass conservation",
        validate_staging_file(ok_path, hard=True).ok,
    )

    # Negative: sidecar has the finding but Markdown drops it (count mismatch).
    drop_md = _current_findings_markdown([])
    drop_path = _write_staging(
        root, "2026-07-17-branch-review-cons-drop-r1.md", drop_md, ok_payload
    )
    check(
        "Markdown missing a sidecar finding fails conservation",
        any(
            "conservation" in e or "Markdown" in e or "findings" in e
            for e in validate_staging_file(drop_path, hard=True).errors
        ),
    )

    # Negative: counts.staged_findings disagrees with len(sidecar findings).
    bad_counts = json.loads(json.dumps(ok_payload))
    bad_counts["counts"]["staged_findings"] = 2
    bad_counts_path = _write_staging(
        root, "2026-07-17-branch-review-cons-counts-r1.md", ok_md, bad_counts
    )
    check(
        "counts.staged_findings != len(findings) fails conservation",
        any(
            "conservation" in e or "staged_findings" in e
            for e in validate_staging_file(bad_counts_path, hard=True).errors
        ),
    )

    # Negative: finding ID mismatch (Markdown F1 vs sidecar id 2).
    md_id = _current_findings_markdown(
        [_current_finding(id=2, severity="Medium", blocking=False)]
    )
    id_payload = _payload_with_findings(
        [_current_finding(id=2, severity="Medium", blocking=False)]
    )
    id_mismatch_payload = json.loads(json.dumps(id_payload))
    id_mismatch_payload["findings"][0]["id"] = 1
    id_path = _write_staging(
        root, "2026-07-17-branch-review-cons-id-r1.md", md_id, id_mismatch_payload
    )
    check(
        "Markdown/sidecar finding ID mismatch fails conservation",
        any(
            "conservation" in e or "id" in e.lower()
            for e in validate_staging_file(id_path, hard=True).errors
        ),
    )

    # Negative: severity disagreement (Markdown Medium vs sidecar High).
    sev_md = _current_findings_markdown(
        [_current_finding(id=1, severity="Medium", blocking=False)]
    )
    sev_payload = _payload_with_findings(
        [_current_finding(id=1, severity="High", blocking=False)]
    )
    sev_path = _write_staging(
        root, "2026-07-17-branch-review-cons-sev-r1.md", sev_md, sev_payload
    )
    check(
        "severity disagreement between Markdown and sidecar fails conservation",
        any(
            "conservation" in e or "severity" in e.lower()
            for e in validate_staging_file(sev_path, hard=True).errors
        ),
    )

    # Negative: blocking disagreement (Markdown blocking vs sidecar not).
    blk_md = _current_findings_markdown(
        [_current_finding(id=1, severity="Medium", blocking=True)]
    )
    blk_payload = _payload_with_findings(
        [_current_finding(id=1, severity="Medium", blocking=False)]
    )
    blk_path = _write_staging(
        root, "2026-07-17-branch-review-cons-blk-r1.md", blk_md, blk_payload
    )
    check(
        "blocking disagreement between Markdown and sidecar fails conservation",
        any(
            "conservation" in e or "blocking" in e.lower()
            for e in validate_staging_file(blk_path, hard=True).errors
        ),
    )


def _selftest_full_panel_completion(root: Path, check) -> None:
    """For panel_mode == full: each of the 5 default workers must appear exactly
    once with status == complete and its required lenses. Failed/timed-out/other
    statuses count as launches (toward the 6 ceiling) but never as completed
    coverage. Duplicate workers fail."""
    md = _current_clear_markdown("panel")

    def panel_payload(panel: list[dict]) -> dict:
        payload = _current_clear_payload()
        payload["panel"] = panel
        launched = [
            r for r in panel if isinstance(r, dict) and r.get("status") != "skipped"
        ]
        payload["counts"]["workers_launched"] = len(launched)
        return payload

    def worker_row(worker: str, *, lenses=None, status: str = "complete") -> dict:
        if lenses is None:
            lenses = sorted(REQUIRED_PANEL_LENSES[worker])
        return {
            "worker": worker,
            "lenses": list(lenses),
            "parent_worker": None,
            "descendant_launches": [],
            "status": status,
            "raw": 0,
            "solo": 0,
            "echo": 0,
            "relaunch": False,
        }

    def full_panel() -> list[dict]:
        return [worker_row(w) for w in DEFAULT_PANEL_WORKERS]

    # Positive: all five workers complete with required lenses passes.
    ok_path = _write_staging(
        root,
        "2026-07-17-branch-review-panel-ok-r1.md",
        md,
        panel_payload(full_panel()),
    )
    check(
        "full panel: all five complete with required lenses passes",
        validate_staging_file(ok_path, hard=True).ok,
    )

    # Negative: a worker with status failed counts as a launch but not as
    # completed coverage -> full-panel completion must fail.
    failed_panel = full_panel()
    failed_panel[1] = worker_row("testing", status="failed")
    failed_path = _write_staging(
        root,
        "2026-07-17-branch-review-panel-failed-r1.md",
        md,
        panel_payload(failed_panel),
    )
    check(
        "full panel: failed worker does not satisfy completed coverage",
        any(
            "completion" in e or "complete" in e or "coverage" in e
            for e in validate_staging_file(failed_path, hard=True).errors
        ),
    )

    # Negative: a worker with status timed-out does not satisfy coverage.
    timed_panel = full_panel()
    timed_panel[2] = worker_row("design-simplicity", status="timed-out")
    timed_path = _write_staging(
        root,
        "2026-07-17-branch-review-panel-timed-r1.md",
        md,
        panel_payload(timed_panel),
    )
    check(
        "full panel: timed-out worker does not satisfy completed coverage",
        any(
            "completion" in e or "complete" in e or "coverage" in e
            for e in validate_staging_file(timed_path, hard=True).errors
        ),
    )

    # Negative: an unknown status does not satisfy coverage.
    unknown_panel = full_panel()
    unknown_panel[0] = worker_row("correctness-completeness", status="running")
    unknown_path = _write_staging(
        root,
        "2026-07-17-branch-review-panel-unknown-r1.md",
        md,
        panel_payload(unknown_panel),
    )
    check(
        "full panel: unknown worker status does not satisfy completed coverage",
        any(
            "completion" in e or "complete" in e or "coverage" in e or "status" in e
            for e in validate_staging_file(unknown_path, hard=True).errors
        ),
    )

    # Negative: a duplicate worker (same name twice) fails.
    dup_panel = full_panel()
    dup_panel.append(worker_row("risk"))
    dup_payload = panel_payload(dup_panel)
    dup_payload["escalation_reason"] = "duplicate test escalation"
    dup_path = _write_staging(
        root,
        "2026-07-17-branch-review-panel-dup-r1.md",
        md,
        dup_payload,
    )
    check(
        "full panel: duplicate worker fails",
        any(
            "duplicate" in e.lower() or "exactly once" in e.lower()
            for e in validate_staging_file(dup_path, hard=True).errors
        ),
    )

    # Negative: a worker missing a required lens fails.
    wrong_lens_panel = full_panel()
    wrong_lens_panel[0] = worker_row(
        "correctness-completeness", lenses=["quality"]  # missing implementation
    )
    wrong_lens_path = _write_staging(
        root,
        "2026-07-17-branch-review-panel-lens-r1.md",
        md,
        panel_payload(wrong_lens_panel),
    )
    check(
        "full panel: worker missing a required lens fails",
        any(
            "lens" in e.lower() for e in validate_staging_file(wrong_lens_path, hard=True).errors
        ),
    )

    # Negative: a missing worker fails.
    missing_panel = full_panel()[:4]
    missing_path = _write_staging(
        root,
        "2026-07-17-branch-review-panel-missing-r1.md",
        md,
        panel_payload(missing_panel),
    )
    check(
        "full panel: missing worker fails",
        any(
            "missing" in e.lower() or "completion" in e.lower() or "coverage" in e.lower()
            for e in validate_staging_file(missing_path, hard=True).errors
        ),
    )


def _selftest_readiness_independence(root: Path, check) -> None:
    """Readiness blocks only on blocking findings, never on severity. A pending
    blocking Low blocks readiness; a pending non-blocking Medium does not.
    Resolving the blocking Low (dropping it) makes the review ready even though
    the non-blocking Medium remains pending."""
    blocking_low = _current_finding(
        id=1, severity="Low", blocking=True, reachability="theoretical"
    )
    blocking_low["triage"] = "pending"
    nonblocking_medium = _current_finding(id=2, severity="Medium", blocking=False)
    nonblocking_medium["triage"] = "pending"

    # Both pending: NOT ready (blocking Low blocks).
    both_md = _current_findings_markdown([blocking_low, nonblocking_medium])
    check(
        "pending blocking Low + pending non-blocking Medium => not ready",
        is_review_ready(both_md) is False,
    )

    # Only the non-blocking Medium pending (Low dropped): ready.
    dropped_low = _current_finding(
        id=1, severity="Low", blocking=True, reachability="theoretical"
    )
    dropped_low["triage"] = "dropped"
    ready_md = _current_findings_markdown([dropped_low, nonblocking_medium])
    check(
        "dropped blocking Low + pending non-blocking Medium => ready",
        is_review_ready(ready_md) is True,
    )

    # A pending non-blocking Medium alone does not block readiness.
    only_medium_md = _current_findings_markdown([nonblocking_medium])
    check(
        "pending non-blocking Medium alone => ready",
        is_review_ready(only_medium_md) is True,
    )

    # A pending blocking High blocks readiness.
    blocking_high = _current_finding(id=1, severity="High", blocking=True)
    blocking_high["triage"] = "pending"
    check(
        "pending blocking High => not ready",
        is_review_ready(_current_findings_markdown([blocking_high])) is False,
    )

    # A deferred blocking finding still blocks (deferred is not resolved).
    deferred_low = _current_finding(
        id=1, severity="Low", blocking=True, reachability="theoretical"
    )
    deferred_low["triage"] = "deferred"
    check(
        "deferred blocking Low still blocks readiness",
        is_review_ready(_current_findings_markdown([deferred_low])) is False,
    )

    # An empty review is ready.
    check(
        "empty review is ready",
        is_review_ready(_current_clear_markdown("ready-empty")) is True,
    )


def _selftest_producer_artifacts(root: Path, check) -> None:
    """Positive fixtures: each review producer (code/branch, plan, RFC,
    confluence/document) emits a current-format staging payload that passes
    hard validation without manual repair, and the orchestrator-supplied
    expected digest matches the sidecar (source-digest authority, fresh)."""
    base_payload = _current_clear_payload()

    def fresh_payload(source_kind: str, artifact_bytes: bytes) -> dict:
        payload = json.loads(json.dumps(base_payload))
        digest = compute_source_digest(source_kind, artifact_bytes)
        payload["source_digest"] = digest
        payload["source_kind"] = source_kind
        return payload

    # 1. Code / branch review: digest over the exact stored diff bytes.
    diff_bytes = (
        b"diff --git a/src/app.py b/src/app.py\n"
        b"index 1111111..2222222 100644\n"
        b"--- a/src/app.py\n"
        b"+++ b/src/app.py\n"
        b"@@ -10,3 +10,4 @@ def handle(req):\n"
        b"     return ok(req)\n"
        b"+    log(req.id)\n"
    )
    code_md = _current_clear_markdown("code-prod")
    code_payload = fresh_payload("code", diff_bytes)
    code_path = _write_staging(
        root, "2026-07-17-branch-review-code-prod-r1.md", code_md, code_payload
    )
    code_result = validate_staging_file(
        code_path,
        hard=True,
        expected_digest=code_payload["source_digest"],
        source_kind="code",
    )
    check(
        "producer: code/branch review current payload validates (fresh digest)",
        code_result.ok,
    )

    # 2. Plan review: digest over the exact reviewed plan UTF-8 bytes.
    plan_bytes = (
        "# Plan: sample feature\n\n"
        "An anonymized plan body covering tasks and evaluation criteria.\n"
    ).encode("utf-8")
    plan_md = _current_clear_markdown("plan-prod")
    plan_payload = fresh_payload("plan", plan_bytes)
    plan_path = _write_staging(
        root, "2026-07-17-plan-review-plan-prod-r1.md", plan_md, plan_payload
    )
    plan_result = validate_staging_file(
        plan_path,
        hard=True,
        expected_digest=plan_payload["source_digest"],
        source_kind="plan",
    )
    check(
        "producer: plan review current payload validates (fresh digest)",
        plan_result.ok,
    )

    # 3. RFC review: digest over the exact reviewed RFC UTF-8 bytes.
    rfc_bytes = (
        "# RFC: sample design\n\n"
        "An anonymized RFC body with context, options, and a decision.\n"
    ).encode("utf-8")
    rfc_md = _current_clear_markdown("rfc-prod")
    rfc_payload = fresh_payload("rfc", rfc_bytes)
    rfc_path = _write_staging(
        root, "2026-07-17-rfc-review-rfc-prod-r1.md", rfc_md, rfc_payload
    )
    rfc_result = validate_staging_file(
        rfc_path,
        hard=True,
        expected_digest=rfc_payload["source_digest"],
        source_kind="rfc",
    )
    check(
        "producer: RFC review current payload validates (fresh digest)",
        rfc_result.ok,
    )

    # 4. Confluence / document review: digest over the exact reviewed doc bytes.
    doc_bytes = (
        "# Sample runbook\n\n"
        "An anonymized Confluence/document body with steps and owners.\n"
    ).encode("utf-8")
    doc_md = _current_clear_markdown("doc-prod")
    doc_payload = fresh_payload("document", doc_bytes)
    doc_path = _write_staging(
        root, "2026-07-17-confluence-review-doc-prod-r1.md", doc_md, doc_payload
    )
    doc_result = validate_staging_file(
        doc_path,
        hard=True,
        expected_digest=doc_payload["source_digest"],
        source_kind="document",
    )
    check(
        "producer: confluence/document review current payload validates (fresh digest)",
        doc_result.ok,
    )

    # Cross-check: a different artifact's digest must NOT validate against any
    # of these producers (stale-digest authority is per-artifact).
    stale = compute_source_digest("plan", b"different bytes\n")
    stale_result = validate_staging_file(
        plan_path, hard=True, expected_digest=stale, source_kind="plan"
    )
    check(
        "producer: stale expected_digest against the plan artifact fails",
        any(
            "source_digest" in e
            for e in stale_result.errors
        ),
    )


def _selftest_source_plan_cli(root: Path, check) -> None:
    """The --source-plan CLI flag must recompute the plan digest and reach the
    stale-digest comparison. Pins the main() wiring that
    validate_staging_file(expected_digest=...) already covers at the function
    level in _selftest_source_digest. Each case must be DISCRIMINATING: it must
    fail if the wiring were severed (expected_digest dropped), not pass via the
    presence-only path."""
    import io

    plan_path = root / "plan.md"
    plan_bytes = b"# Plan\n## Tasks\n1. do foo\n"
    plan_path.write_bytes(plan_bytes)
    plan_digest = compute_source_digest("plan", plan_bytes)

    # A second, different file so we can prove the digest comparison actually
    # ran (a severed-wiring regression would pass regardless of which file we
    # point at; pointing at the wrong file and asserting exit 1 is the
    # discriminating positive-vs-negative contrast).
    other_path = root / "other.md"
    other_path.write_bytes(b"# Not the plan\n")

    payload = json.loads(json.dumps(_current_clear_payload()))
    payload["source_digest"] = plan_digest
    payload["source_kind"] = "plan"
    staging = _write_staging(
        root, "2026-07-17-plan-review-cli-r1.md",
        _current_clear_markdown("cli"), payload,
    )

    # Case A (discriminating): point --source-plan at the CORRECT plan -> exit 0.
    rc_fresh = main(["--hard", str(staging), "--source-plan", str(plan_path)])
    check("--source-plan fresh (correct plan) exits 0", rc_fresh == 0)

    # Case A' (the discriminating twin): point --source-plan at a DIFFERENT
    # existing file -> exit 1. This is what makes Case A meaningful: if the
    # wiring were severed (expected_digest dropped), both A and A' would exit 0.
    rc_wrong_file = main(["--hard", str(staging), "--source-plan", str(other_path)])
    check(
        "--source-plan against a different file exits 1 (wiring is live)",
        rc_wrong_file == 1,
    )

    # Case B: fold the plan (digest changes) -> exit 1 with stale error AND the
    # F7 path hint naming the hashed file.
    plan_path.write_bytes(plan_bytes + b"\nfolded F1\n")
    buf = io.StringIO()
    real_stderr = sys.stderr
    sys.stderr = buf
    try:
        rc_stale = main(["--hard", str(staging), "--source-plan", str(plan_path)])
    finally:
        sys.stderr = real_stderr
    stale_text = buf.getvalue()
    check(
        "--source-plan stale (post-fold) digest exits 1 with stale error",
        rc_stale == 1 and "stale" in stale_text and "source_digest" in stale_text,
    )
    check(
        "stale-digest error includes the hashed source-path hint (F7)",
        str(plan_path) in stale_text,
    )

    # Case C: missing source-plan file -> exit 1.
    rc_missing = main(
        ["--hard", str(staging), "--source-plan", str(root / "nope.md")]
    )
    check("--source-plan missing file exits 1", rc_missing == 1)


def _selftest_discarded_header_skip(root: Path, check) -> None:
    """The discarded-findings header skip must recognize the authoritative
    `| Worker | Worker severity | Pattern | Theme | Reason | Notes |` header
    (review-staging/SKILL.md:156, review-plan/SKILL.md:152), not only the legacy
    `| Agent |` header. Pre-fix, line 380 matched `^\\|\\s*Agent\\s*\\|` only, so a
    correctly-formatted `| Worker |` header row was parsed as a data row. Its
    cells become `(Worker, Worker severity, Pattern, Theme, Reason, Notes)`; the
    reason cell (index 4) is the literal `Reason`, which is not a valid discard
    code, so the validator emitted a spurious
    `unknown discard reason code: Reason` warning.

    Discrimination nuance (testing-F2 + the IMPORTANT nuance in the plan): a
    naive "warnings contains unknown discard reason code" assertion would PASS
    pre-fix AND post-fix because the negative-twin data row (with reason
    `not-a-real-reason`) always emits that warning regardless of the bug. So the
    RED-phase discriminating assertion targets the header-skip bug specifically:
    the spurious warning's reason token is the literal `Reason` (the column
    header). Pre-fix the header is parsed as data -> reason="Reason" -> the
    `unknown discard reason code: Reason` warning IS present -> assertion (a)
    FAILS, exposing the bug. Post-fix the header is skipped -> that warning is
    GONE -> assertion (a) PASSES. Assertion (b) pins the negative twin so the
    fix cannot over-skip genuine data rows.

    Assert on `result.warnings` (a list[str]), NOT `result.ok`: `add_warning`
    does not flip `ok` (lines 148-149), so an `result.ok` assertion would
    false-pass (testing-F2).
    """
    import json as _json

    # Reuse the canonical fixtures the way _selftest_source_plan_cli does
    # (lines 2419-2425). The fixture MUST be a full current-format staging doc,
    # NOT a stub; a stub fails validate_staging_file for unrelated structural
    # reasons (missing ## Metadata / ## Review Statistics / ### Panel).
    payload = _json.loads(_json.dumps(_current_clear_payload()))
    md = _current_clear_markdown("discarded-header")

    # Inject a populated Discarded section in place of the canonical `None.`
    # (replace ONLY the first `### Discarded findings\\nNone.` occurrence).
    # Header row + `|---|` separator + two data rows: one valid (`duplicate`),
    # one with a BAD reason (`not-a-real-reason`) as the negative twin.
    populated = (
        "| Worker | Worker severity | Pattern | Theme | Reason | Notes |\n"
        "|---|---|---|---|---|---|\n"
        "| correctness-completeness | High | quality#edge-case | dup | "
        "duplicate | same as F1 |\n"
        "| testing | Medium | testing#gap | bad | not-a-real-reason | none |"
    )
    fixture_md = md.replace(
        "### Discarded findings\nNone.",  # canonical _current_clear_markdown form (dedented)
        f"### Discarded findings\n{populated}",
        1,
    )
    # Defensive: confirm the injection actually landed (a silent no-op replace
    # would make this test exercise nothing).
    check(
        "discarded-header fixture injected (None. replaced)",
        "not-a-real-reason" in fixture_md and "| Worker | Worker severity |"
        in fixture_md,
    )

    staging = _write_staging(
        root, "2026-07-17-branch-review-discarded-header.md", fixture_md, payload,
    )
    result = validate_staging_file(staging, hard=False)

    # The fixture's BAD data row guarantees the Discarded section is parsed and
    # the reason-code check fires, so warnings must be non-empty.
    check(
        "discarded-header fixture yields non-empty warnings",
        len(result.warnings) > 0,
    )

    # Assertion (b) - the negative twin: the BAD-reason data row is STILL caught.
    # This holds both pre-fix and post-fix; it proves the fix did not over-skip
    # genuine data rows (testing-F1).
    check(
        "discarded-header: BAD data row (not-a-real-reason) still warned",
        any("unknown discard reason code: not-a-real-reason" in w for w in result.warnings),
    )

    # Assertion (a) - the discriminating RED assertion: NO warning should
    # mention the literal reason token `Reason` (the column header). Pre-fix the
    # `| Worker |` header is parsed as a data row -> reason cell (index 4) is the
    # literal `Reason` -> `unknown discard reason code: Reason` is emitted ->
    # this assertion FAILS (RED), exposing the bug. Post-fix the header is
    # skipped -> the `Reason`-token warning is GONE -> this assertion PASSES
    # (GREEN). Assert via `not any(...)` so the post-fix expectation is encoded
    # directly; the RED run demonstrates the failure, the GREEN run the pass.
    check(
        "discarded-header: Worker header row NOT parsed as data "
        "(no `unknown discard reason code: Reason`)",
        not any("unknown discard reason code: Reason" in w for w in result.warnings),
    )


def run_selftest() -> int:
    import tempfile

    _CHECK_FAILURES[0] = 0
    check = _make_check()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for _name, fn in (
            ("path_names", _selftest_path_names),
            ("legacy_stubs", _selftest_legacy_stubs),
            ("current_contract", _selftest_current_contract),
            ("source_digest", _selftest_source_digest),
            ("typed_current_schema", _selftest_typed_current_schema),
            ("finding_budget", _selftest_finding_budget),
            ("finding_conservation", _selftest_finding_conservation),
            ("full_panel_completion", _selftest_full_panel_completion),
            ("readiness_independence", _selftest_readiness_independence),
            ("producer_artifacts", _selftest_producer_artifacts),
            ("source_plan_cli", _selftest_source_plan_cli),
            ("discarded_header_skip", _selftest_discarded_header_skip),
        ):
            fn(root, check)

    if _CHECK_FAILURES[0]:
        print(
            f"validate_review_staging: --selftest FAILED ({_CHECK_FAILURES[0]})",
            file=sys.stderr,
        )
        return 1
    print("validate_review_staging: --selftest ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate review staging markdown")
    parser.add_argument("path", nargs="?", help="Staging markdown file")
    parser.add_argument(
        "--hard",
        action="store_true",
        help="Exit 1 when validation fails",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON result on stdout")
    parser.add_argument(
        "--newest-for-branch",
        metavar="BRANCH",
        help="Validate newest staging doc for branch slug in reviews_dir",
    )
    parser.add_argument(
        "--cwd",
        default=".",
        help="Repo cwd when using --newest-for-branch",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run fixture checks and exit",
    )
    parser.add_argument(
        "--source-plan",
        metavar="PATH",
        help=(
            "Reviewed plan file. Recompute its SHA-256 digest and compare to "
            "sidecar.source_digest; fail hard on mismatch (stale review after "
            "a fold). Plan reviews only (source_kind=plan)."
        ),
    )
    args = parser.parse_args(argv)

    if args.selftest:
        return run_selftest()

    target: Path | None = None
    if args.path:
        target = Path(args.path).expanduser().resolve()
    elif args.newest_for_branch:
        repo_root = Path(args.cwd).expanduser().resolve()
        target = newest_staging_for_branch(repo_root, args.newest_for_branch)
        if target is None:
            payload = {
                "ok": True,
                "skipped": True,
                "reason": "no staging doc found for branch",
            }
            if args.json:
                print(json.dumps(payload))
            return 0
    else:
        parser.error("path or --newest-for-branch is required")

    expected_digest: str | None = None
    source_kind: str | None = None
    if args.source_plan:
        # --source-plan is plan-only: hardcode source_kind and compute the
        # digest of the named plan file. RFC/document reviewers needing the
        # same gate should add their own flag then (recipe is byte-identical).
        source_kind = "plan"
        source_path = Path(args.source_plan).expanduser().resolve()
        if not source_path.is_file():
            payload = {"ok": False, "errors": [f"source file not found: {source_path}"]}
            if args.json:
                print(json.dumps(payload))
            else:
                print(f"ERROR: source file not found: {source_path}", file=sys.stderr)
            return 1
        try:
            source_bytes = source_path.read_bytes()
        except OSError as exc:
            print(f"ERROR: cannot read source file: {exc}", file=sys.stderr)
            return 1
        expected_digest = compute_source_digest("plan", source_bytes)
        # Stash the path so the stale-digest error can name it (F7: an agent
        # that points --source-plan at the wrong file gets an actionable hint
        # instead of an opaque "artifact may have changed").
        _SOURCE_PATH_FOR_ERROR = str(source_path)
    else:
        _SOURCE_PATH_FOR_ERROR = None

    result = validate_staging_file(
        target,
        hard=args.hard,
        expected_digest=expected_digest,
        source_kind=source_kind,
    )
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        for warning in result.warnings:
            print(f"WARN: {warning}", file=sys.stderr)
        for error in result.errors:
            # Augment stale-digest errors with the hashed source path so an
            # agent that pointed --source-plan at the wrong file (e.g. the
            # staging doc instead of the plan) gets an actionable hint (F7).
            if (
                _SOURCE_PATH_FOR_ERROR
                and "source_digest is stale" in error
            ):
                error = (
                    f"{error}; or --source-plan points at the wrong file "
                    f"(hashed: {_SOURCE_PATH_FOR_ERROR})"
                )
            print(f"ERROR: {error}", file=sys.stderr)
        if result.ok:
            print(f"OK: {target}")
        else:
            print(f"FAIL: {target}", file=sys.stderr)

    if args.hard and not result.ok:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
