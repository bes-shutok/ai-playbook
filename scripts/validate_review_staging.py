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
# Canonical Pattern ID contract for version-1 sidecars: `lens#kebab-slug`.
# Owners are the declared shared review lenses (the per-worker required lens
# set) plus `consistency` (assigned ownership for plan/RFC contradictions)
# and the explicit `unknown` owner. The historical `prose-clarity` owner
# stays readable for legacy records only and is rejected from version-1
# sidecars.
SHARED_PATTERN_OWNERS = frozenset(
    {lens for lenses in REQUIRED_PANEL_LENSES.values() for lens in lenses}
    | {"consistency", "unknown"}
)
CANONICAL_PATTERN_RE = re.compile(
    r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*#[a-z0-9]+(?:-[a-z0-9]+)*$"
)
# Version-1 top-level sidecar contract. Required fields must all be present;
# optional fields are permitted in their documented type (``depth`` string,
# ``domains`` list, ``extensions`` object). Any other top-level field is
# rejected; future extensions belong inside the object-valued ``extensions``.
V1_REQUIRED_TOP_LEVEL_FIELDS = (
    "schema_version",
    "review_type",
    "date",
    "artifact_slug",
    "round",
    "panel_mode",
    "selection_reason",
    "source_kind",
    "source_digest",
    "escalation_reason",
    "counts",
    "panel",
    "deduplication_groups",
    "discarded",
    "severity_calibration",
    "triage_outcomes",
    "findings",
    "overflow",
    "soften_watchlist",
)
V1_OPTIONAL_TOP_LEVEL_FIELDS = ("depth", "domains", "extensions")
# r6 F8: version-1 ``date`` is a shape-checked string (calendar validity is
# out of scope; the documented contract is the format). ``\Z`` (not ``$``)
# so a trailing newline cannot slip through, ASCII-only ``[0-9]`` so
# Unicode decimal digits cannot pass (r1 F1).
V1_DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
SUPPORTED_SIDECAR_SCHEMA_VERSIONS = (1,)
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


FENCE_LINE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
HEADING_LINE_RE = re.compile(r"^#{1,6}\s")


def classify_fence_lines(
    lines: list[str],
    *,
    is_reset_heading=None,
) -> tuple[list[tuple[str, object]], int | None]:
    """Fence-aware line classifier shared by every Markdown scanner here.

    The single owner of the fence state machine (r1 F3): a fence opens on a
    line matching ``FENCE_LINE_RE`` — openers keep prefix-match semantics
    (either delimiter character, run of 3+, info strings allowed). A fence
    closes ONLY on a bare, equal-or-longer run of the same delimiter
    character as the opener (leading/trailing whitespace on the close line
    is allowed; any other suffix — info string or mixed characters — keeps
    the line fenced content, and a run of the other delimiter character
    never closes however long it is). This same-char + equal-or-longer +
    bare close rule supersedes the consolidation plan's length-only pin
    (r5 F5's "the delimiter character is not compared" is retired). Emits
    one event per input line, drawn from the specified vocabulary:

    - ``("fence_opener", None)``: this line opens a fence;
    - ``("fence_close", None)``: this line closes the currently open fence;
    - ``("in_fence_content", None)``: this line is content inside an open
      fence (never a heading, boundary, or metadata candidate);
    - ``("heading", raw_text)``: a heading line the consumer maps to its own
      semantics (severity-group ``### <Severity>`` vs finding header
      ``#### F<N>.`` vs other ``####``); the classifier does NOT classify
      heading sub-kinds (r2 F4);
    - ``("ordinary", raw_text)``: any other line outside a fence.

    Reset policy: with no ``is_reset_heading`` predicate (the default,
    content-preserving), a heading inside an open fence is
    ``in_fence_content`` (r5 F8 fenced-example purity). Passing a
    callable selects heading-reset mode (the r4 F3 containment mode for
    fences that never close, keyword-only so a half-configured mode is
    structurally unrepresentable rather than conventionally): a heading
    inside an open fence resets the fence state iff
    ``is_reset_heading(raw_text)`` is truthy (each consumer pins its own
    reset heading set); otherwise it stays fenced content.

    Returns ``(events, unclosed_opener_index)`` where
    ``unclosed_opener_index`` is the line index of the fence opener that never
    closed, or None when every fence closed (consumers use it to apply the
    partial fallback: keep pre-opener first-pass results, re-classify only
    from the opener onward).
    """
    events: list[tuple[str, object]] = []
    in_fence = False
    fence_len = 0
    fence_char = ""
    opener_index: int | None = None
    for i, line in enumerate(lines):
        fence_match = FENCE_LINE_RE.match(line)
        if fence_match:
            if in_fence:
                stripped = line.strip()
                if (
                    stripped == fence_char * len(stripped)
                    and len(stripped) >= fence_len
                ):
                    in_fence = False
                    fence_len = 0
                    fence_char = ""
                    opener_index = None
                    events.append(("fence_close", None))
                else:
                    events.append(("in_fence_content", None))
            else:
                in_fence = True
                fence_len = len(fence_match.group(1))
                fence_char = fence_match.group(1)[0]
                opener_index = i
                events.append(("fence_opener", None))
            continue
        if HEADING_LINE_RE.match(line):
            if in_fence and (is_reset_heading is None or not is_reset_heading(line)):
                events.append(("in_fence_content", None))
                continue
            if in_fence:
                in_fence = False
                fence_len = 0
                fence_char = ""
                opener_index = None
            events.append(("heading", line))
            continue
        if in_fence:
            events.append(("in_fence_content", None))
            continue
        events.append(("ordinary", line))
    return events, (opener_index if in_fence else None)


def classify_with_fallback(
    lines: list[str],
    is_reset_heading,
) -> tuple[
    list[tuple[str, object]], int | None, list[tuple[str, object]] | None
]:
    """Two-pass classification with the r6 F3 partial fallback.

    Contract (r6 F3 partial fallback): the first pass is the default
    content-preserving ``classify_fence_lines`` run over ALL lines. When every
    fence closed, ``reset_events`` is ``None`` and ``unclosed_opener`` is
    ``None``. When a fence never closed, the first pass is trustworthy only up
    to its opener: the suffix ``lines[unclosed_opener:]`` is re-classified with
    ``is_reset_heading`` (heading-reset mode) and returned as
    ``reset_events``; consumers keep the pre-opener first-pass results and
    interpret the suffix from the re-classified events (index-based consumers
    remap suffix indices with ``unclosed_opener + i``; order-based consumers
    apply the events directly). The helper owns only this two-pass
    orchestration — it REUSES ``classify_fence_lines`` and never re-implements
    fence tracking.

    ``is_reset_heading`` is a required positional argument, unlike the
    classifier's keyword-only optional predicate. The classifier runs both
    modes, so its predicate must be optional to express content-preserving
    mode. This helper only ever runs the reset mode (it invokes it solely on
    the unclosed suffix), and reset mode must never run without its explicit
    predicate — an optional predicate here would recreate the half-configured
    mode the classifier's keyword-only design makes structurally
    unrepresentable (the Task 3 collapse). Both consumers always have a
    predicate of their own.
    """
    events, unclosed_opener = classify_fence_lines(lines)
    if unclosed_opener is None:
        return events, None, None
    reset_events, _ = classify_fence_lines(
        lines[unclosed_opener:],
        is_reset_heading=is_reset_heading,
    )
    return events, unclosed_opener, reset_events


def split_finding_blocks(content: str) -> list[str]:
    findings_match = re.search(r"^## Findings\s*$", content, re.MULTILINE)
    if not findings_match:
        return []
    findings_section = content[findings_match.end() :]
    findings_section = re.split(r"\n## ", findings_section, maxsplit=1)[0]
    # Legacy findings use "### 1." or "### F1". Current grouped findings use
    # severity headings plus "#### F1." entries.
    # r5 F8: the current-format split is fence-aware. A ``#### F<N>.`` line
    # inside a properly fenced code example is quoted content, not a finding
    # header; splitting on it produced a phantom finding block that then
    # failed the Comment/Analysis gate with errors naming the phantom instead
    # of the real defect. Fence tracking is owned by the shared
    # ``classify_fence_lines`` classifier (single fence state machine).
    lines = findings_section.splitlines(keepends=True)
    header_re = re.compile(r"^####\s+F\d+\.")

    def is_finding_header(line: str) -> bool:
        return header_re.match(line) is not None

    def boundary_indices(events: list[tuple[str, object]]) -> list[int]:
        return [
            i
            for i, (kind, value) in enumerate(events)
            if kind == "heading" and is_finding_header(value)
        ]

    events, unclosed_opener, reset_events = classify_with_fallback(
        lines, is_finding_header
    )
    boundaries = boundary_indices(events)
    if reset_events is not None:
        # Partial fallback (r6 F3): a fence never closed, so the
        # content-preserving first pass is trustworthy only up to the opener.
        # Keep those boundaries and re-classify from the opener onward with
        # heading resets restricted to finding-header lines (the splitter's
        # reset heading set), so the unclosed fence cannot swallow later
        # findings (r4 F3) and pre-opener fenced examples stay content.
        boundaries = [i for i in boundaries if i < unclosed_opener]
        boundaries += [
            unclosed_opener + i for i in boundary_indices(reset_events)
        ]
    if boundaries:
        parts: list[str] = []
        starts = boundaries + [len(lines)]
        for bi in range(len(boundaries)):
            chunk = "".join(lines[starts[bi]:starts[bi + 1]]).strip()
            if chunk:
                parts.append(chunk)
        return parts
    parts_legacy = re.split(r"\n(?=### )", findings_section)
    blocks: list[str] = []
    for part in parts_legacy:
        stripped = part.strip()
        if not stripped.startswith("### "):
            continue
        header = stripped.splitlines()[0][4:].strip()
        if FINDING_HEADER_RE.match(header + " "):
            blocks.append(stripped)
    return blocks


def parse_markdown_findings(content: str) -> list[dict]:
    """Parse current-format Markdown findings into ``{id, severity, blocking,
    triage, pattern}`` dicts, one per ``#### F<N>.`` block.

    Severity is read from the enclosing ``### <Severity>`` group heading;
    blocking from either the canonical ``- **Blocking**: true | false`` bullet
    documented in ``review-staging/SKILL.md`` (the primary, human-facing
    template every producer skill emits) or the legacy bare ``- **blocking**``
    / ``- **non-blocking**`` bullet (older staging docs); triage from a
    ``**Triage**: <value>`` bullet; pattern from a ``**Pattern**: <id>`` bullet
    when present (used by the version-1 Markdown/sidecar pattern conservation
    cross-check). Metadata bullets are read ONLY between the finding header
    and the first level-four sub-heading of any name (Comment and Analysis
    are the common ones), and fenced code blocks are skipped, so quoted or
    example bullets in body prose cannot overwrite the parsed fields. Used by
    the Markdown/sidecar conservation cross-check.
    """
    findings_match = re.search(r"^## Findings\s*$", content, re.MULTILINE)
    if not findings_match:
        return []
    findings_section = content[findings_match.end() :]
    findings_section = re.split(r"\n## ", findings_section, maxsplit=1)[0]
    parsed: list[dict] = []
    current_severity: str | None = None
    current: dict | None = None
    # r3 F2: metadata bullets are read ONLY between the finding header and the
    # first level-four sub-heading of any name (Comment and Analysis are the
    # common ones), and fenced code blocks are skipped.
    # Previously every line after the header was scanned last-match-wins, so
    # an illustrative bullet quoted in a Comment/Analysis body (or inside a
    # fenced example) silently overwrote the finding's real parsed pattern,
    # blocking, or triage.
    #
    # r4 F3: the fence tracker is close-rule aware (a fence closes only on a
    # bare, equal-or-longer run of the same delimiter character as its
    # opener — see the ``classify_fence_lines`` docstring for the full rule)
    # and an UNCLOSED fence cannot
    # swallow the rest of the Findings section: when the section ends with a
    # fence still open, the region from the unclosed opener onward is
    # re-classified with severity-group and finding-header lines resetting
    # the fence state, while the pre-opener first-pass classification is
    # preserved (partial fallback, r6 F3), so the unclosed fence cannot hide
    # later blocking findings from readiness. r5 F8: heading-like lines
    # inside a properly CLOSED fence are content, so a fenced example quoting
    # the staging format cannot inject a phantom finding.
    severity_re = re.compile(r"^###\s+(Critical|High|Medium|Low)\b")
    finding_header_re = re.compile(r"^####\s+F(\d+)\.")

    def is_reset_heading(line: str) -> bool:
        # The parser's reset heading set: severity-group headings and finding
        # headers, NOT generic ``####`` sub-headings (r3 F2).
        return bool(severity_re.match(line) or finding_header_re.match(line))

    def apply_events(
        events: list[tuple[str, object]],
        scanned: list[dict],
        cur: dict | None,
        cur_severity: str | None,
        metadata_open: bool,
    ) -> tuple[dict | None, str | None, bool]:
        """Interpret classifier events; the parser keeps only this mapping.

        ``heading(raw_text)`` maps to the parser's own semantics
        (severity-group label, finding header, other ``####`` closing the
        metadata region); ``ordinary(raw_text)`` lines are metadata
        candidates inside the open finding's metadata region. Fence events
        and ``in_fence_content`` carry no finding/metadata meaning here.
        """
        for kind, value in events:
            if kind == "heading":
                line = value
                sev_match = severity_re.match(line)
                if sev_match:
                    cur_severity = sev_match.group(1)
                    continue
                block_match = finding_header_re.match(line)
                if block_match:
                    if cur is not None:
                        scanned.append(cur)
                    cur = {
                        "id": int(block_match.group(1)),
                        "severity": cur_severity,
                        "blocking": None,
                        "triage": None,
                    }
                    metadata_open = True
                    continue
                if re.match(r"^####\s+", line):
                    # Comment/Analysis sub-heading: the finding's metadata
                    # region ends here; body prose is never parsed as
                    # metadata.
                    metadata_open = False
                continue
            if kind != "ordinary":
                continue
            line = value
            if cur is None:
                continue
            if not metadata_open:
                continue
            labeled_blocking = re.search(
                r"-\s*\*\*[Bb]locking\*\*\s*:\s*(true|false)\b", line
            )
            if labeled_blocking:
                cur["blocking"] = labeled_blocking.group(1) == "true"
            elif re.search(r"-\s*\*\*blocking\*\*(?!\s*:)", line):
                cur["blocking"] = True
            elif re.search(r"-\s*\*\*non-blocking\*\*(?!\s*:)", line):
                cur["blocking"] = False
            triage = re.search(r"\*\*Triage\*\*:\s*(\S+)", line)
            if triage:
                cur["triage"] = triage.group(1).rstrip(".")
            pattern = re.search(r"-\s*\*\*[Pp]attern\*\*\s*:\s*(\S+)", line)
            if pattern:
                cur["pattern"] = pattern.group(1).rstrip(".")
        return cur, cur_severity, metadata_open

    lines = findings_section.splitlines()
    events, unclosed_opener, reset_events = classify_with_fallback(
        lines, is_reset_heading
    )
    scanned: list[dict] = []
    if reset_events is None:
        cur, _, _ = apply_events(
            events, scanned, None, current_severity, False
        )
    else:
        # Partial fallback (r6 F3): the content-preserving first pass is
        # trustworthy only up to the opener, so apply ONLY the pre-opener
        # prefix of its events (never the full list). Re-derive the state at
        # the opener from that prefix, flush the finding open at the opener
        # with its PRE-opener bullets (no double-append), and re-scan from
        # the opener with heading resets seeded with that state (severity
        # label, metadata-region flag) so same-group later findings parse
        # with their true severity (r4 F3 containment; post-opener bullets
        # are inside the unclosed fence and are not recovered, same as the
        # old full-discard behavior).
        cur, cur_severity, metadata_open = apply_events(
            events[:unclosed_opener], scanned, None, current_severity, False
        )
        if cur is not None:
            scanned.append(cur)
        cur, _, _ = apply_events(
            reset_events, scanned, None, cur_severity, metadata_open
        )
    if cur is not None:
        scanned.append(cur)
    return scanned


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


def _payload_has_worker_rows(payload: dict) -> bool:
    panel = payload.get("panel")
    if not isinstance(panel, list):
        return False
    return any(isinstance(row, dict) and "worker" in row for row in panel)


def classify_sidecar_schema(payload: object) -> str:
    """Classify a stats sidecar payload into one schema contract label.

    This is the ONE exported source of truth for schema classification; the
    summarizer routes its aggregation adapters from this label.

    Returns:

    - ``"current-v1"``: an explicit ``schema_version: 1`` record (the current
      versioned contract).
    - ``"legacy-worker-shaped"``: a versionless compatibility record whose
      panel rows still carry per-worker ``worker`` identity (pre-version
      worker-shaped history; aggregation keeps its worker/lens metrics).
    - ``"legacy-panel-mode"``: a versionless record that already carried the
      pre-version current shape (``panel_mode`` or
      ``counts.workers_launched``). Still legacy: no explicit version means
      the version-1 contract never applies.
    - ``"legacy"``: any other versionless historical record.
    - ``"unsupported"``: an explicit but unsupported schema version (the
      validator rejects these outright).

    A missing ``schema_version`` is never an error: versionless sidecars are
    legacy compatibility inputs by contract. An explicit ``null`` (or any
    non-int) ``schema_version`` IS an error: it is an explicit version value
    and classifies ``unsupported``.
    """
    if not isinstance(payload, dict):
        return "legacy"
    # Presence check first: an explicit ``"schema_version": null`` is an
    # explicit-but-unsupported version value, not a versionless legacy record
    # (``payload.get`` would conflate the two).
    if "schema_version" in payload:
        version = payload["schema_version"]
        if isinstance(version, bool) or not isinstance(version, int):
            return "unsupported"
        return "current-v1" if version in SUPPORTED_SIDECAR_SCHEMA_VERSIONS else "unsupported"
    counts = payload.get("counts")
    if "panel_mode" in payload or (
        isinstance(counts, dict) and "workers_launched" in counts
    ):
        return "legacy-panel-mode"
    if _payload_has_worker_rows(payload):
        return "legacy-worker-shaped"
    return "legacy"


# Schema labels whose payload carries the "current shape" (the pre-version
# current markers or an explicit version-1 record) and therefore routes
# through ``validate_current_payload``. Exported as ``is_current_shape`` so
# the summarizer's adapter selector and the drift canary share ONE
# definition of current-versus-legacy shape; the validator itself routes on
# ``CURRENT_SHAPE_LABELS`` applied to its single per-run classification
# (r6 F13). The set itself is also exported (``CURRENT_SHAPE_LABELS``) so
# the summarizer derives its adapter-routing label set from this single
# definition instead of hand-copying it.
CURRENT_SHAPE_LABELS = frozenset(
    {"current-v1", "legacy-panel-mode", "legacy-worker-shaped"}
)


def is_current_shape(payload: object) -> bool:
    """True iff the classifier labels ``payload`` as carrying the current
    per-worker panel shape (version-1, legacy-panel-mode, or the versionless
    worker-shaped compatibility records). One exported predicate; no call site
    re-derives the tests."""
    return classify_sidecar_schema(payload) in CURRENT_SHAPE_LABELS


def validate_canonical_pattern(pattern: object, where: str, result: ValidationResult) -> None:
    """Require a canonical ``lens#kebab-slug`` Pattern ID for ``where``.

    The owner must be a declared shared lens owner (plus ``consistency`` and
    ``unknown``); the historical ``prose-clarity`` owner is rejected here and
    stays readable only in legacy data. Colon body tags such as ``shrink:``
    are presentation text, never Pattern IDs.
    """
    if not isinstance(pattern, str) or not CANONICAL_PATTERN_RE.match(pattern):
        result.add_error(
            f"{where}: {pattern!r} is not a canonical Pattern ID "
            f"(expected lens#kebab-slug)"
        )
        return
    owner = pattern.split("#", 1)[0]
    if owner not in SHARED_PATTERN_OWNERS:
        result.add_error(
            f"{where}: pattern owner {owner!r} is not a declared shared lens "
            f"owner (allowed: {sorted(SHARED_PATTERN_OWNERS)}); legacy-only "
            f"owners such as 'prose-clarity' are invalid in version-1 sidecars"
        )


def _require_array(
    payload: dict,
    field_name: str,
    result: ValidationResult,
    schema_label: str,
) -> list:
    """Shared mistyped-container guard for array-typed sidecar fields (r4 F10
    collapses the seven near-identical guard sites into one helper per kind).

    Returns the field value when it is a usable list, else an empty list
    substitute (callers never iterate the substitute). Absent and explicit
    JSON ``null`` are both treated as absent (r4 F14): empty substitute, no
    error. A present-but-mistyped value gets ONE targeted error keyed on the
    schema label: the version-1 field-gate message for ``current-v1`` records,
    the current-shape message for versionless current shapes, and no error
    for pure legacy records (compatibility input).
    """
    value = payload.get(field_name)
    if isinstance(value, list):
        return value
    if value is not None:
        if schema_label == "current-v1":
            result.add_error(
                f"version-1 sidecar field {field_name!r} must be an array"
            )
        elif schema_label in CURRENT_SHAPE_LABELS:
            result.add_error(
                f"current sidecar {field_name!r} must be an array when present"
            )
    return []


def _require_object(
    payload: dict,
    field_name: str,
    result: ValidationResult,
    schema_label: str,
) -> dict:
    """Object-typed twin of ``_require_array`` (same contract, dict kind)."""
    value = payload.get(field_name)
    if isinstance(value, dict):
        return value
    if value is not None:
        if schema_label == "current-v1":
            result.add_error(
                f"version-1 sidecar field {field_name!r} must be an object"
            )
        elif schema_label in CURRENT_SHAPE_LABELS:
            result.add_error(
                f"current sidecar {field_name!r} must be an object when present"
            )
    return {}


def validate_version1_payload(
    payload: dict, content: str, result: ValidationResult
) -> None:
    """Enforce the version-1 top-level contract and canonical Pattern IDs.

    Applies ONLY to records classified ``current-v1``: versionless sidecars
    keep their legacy compatibility treatment. Covers the complete top-level
    allowlist (unknown fields rejected; ``extensions`` must be an object when
    present), canonical patterns for findings, overflow items, and discarded
    rows that carry a pattern, and Markdown/sidecar pattern conservation.
    """
    for field_name in V1_REQUIRED_TOP_LEVEL_FIELDS:
        if field_name not in payload:
            result.add_error(
                f"version-1 sidecar missing required top-level field "
                f"{field_name!r}"
            )
        elif payload[field_name] is None and field_name not in (
            "selection_reason",
            "escalation_reason",
        ):
            # r5 F1: an explicit JSON null for a version-1 required field is
            # NOT absent (except the two documented null-when-not-applicable
            # enum fields). The shared ``_require_array`` /
            # ``_require_object`` helpers treat null as absent (the r4 F14
            # null-as-absent compatibility pinned for VERSIONLESS current
            # shapes), so without this gate a null required container
            # bypassed both the required-field gate and the
            # mistyped-container gate, silently skipping the pattern and
            # conservation checks for that field. The null-as-absent
            # compatibility applies only to versionless records, never to
            # version-1 required container fields. An explicit null
            # ``schema_version`` is separately rejected as unsupported by
            # ``classify_sidecar_schema``.
            result.add_error(
                f"version-1 sidecar required top-level field {field_name!r} "
                "must not be JSON null; null-as-absent compatibility applies "
                "only to versionless records"
            )
    # r6 F8: scalar and optional-field type gates, placed beside (not woven
    # into) the r5 F1 null gate above. Required scalar fields skip ``None`` so
    # the r5 F1 gate stays the single reporter for explicit-null required
    # fields; optional fields fire on any PRESENT value including explicit
    # null (null is not the absent form for optional version-1 fields).
    # v1-gate-trio: the tuple widens with the enum-reason pair
    # (``selection_reason`` / ``escalation_reason``). For that pair the None
    # skip is correctness, not just delegation: null is the documented
    # not-applicable form (r5 F1 carve-out), so only present non-strings are
    # reported here. ``source_kind`` stays out of the tuple: its membership
    # gate in ``validate_current_payload`` already rejects hashable mistyped
    # values and a second gate would double-report them.
    for field_name in (
        "review_type",
        "artifact_slug",
        "date",
        "selection_reason",
        "escalation_reason",
    ):
        value = payload.get(field_name)
        if value is None:
            continue  # null: reported by the r5 F1 gate for the three required scalars; legal not-applicable form for the enum-reason pair (see block comment above)
        if not isinstance(value, str):
            result.add_error(
                f"version-1 sidecar field {field_name!r} must be a string"
            )
            continue
        if field_name == "date" and not V1_DATE_RE.match(value):
            result.add_error(
                "version-1 sidecar field 'date' must be a string in YYYY-MM-DD "
                "format"
            )
    # v1-gate-trio: ``round`` is dual-typed by contract (string or integer;
    # review-staging SKILL.md contract table). bool is excluded explicitly
    # because True is an int subclass in Python; the None skip keeps the r5 F1
    # gate the single reporter for an explicit-null required round.
    round_value = payload.get("round")
    if round_value is not None and (
        isinstance(round_value, bool) or not isinstance(round_value, (str, int))
    ):
        result.add_error(
            "version-1 sidecar field 'round' must be a string or integer"
        )
    for field_name, field_type, type_name in (
        ("depth", str, "a string"),
        ("domains", list, "a list"),
    ):
        if field_name in payload and not isinstance(
            payload[field_name], field_type
        ):
            result.add_error(
                f"version-1 sidecar field {field_name!r} must be {type_name}"
            )
    allowed = set(V1_REQUIRED_TOP_LEVEL_FIELDS) | set(V1_OPTIONAL_TOP_LEVEL_FIELDS)
    for key in payload:
        if key not in allowed:
            result.add_error(
                f"version-1 sidecar rejects unknown top-level field {key!r}; "
                f"future extensions belong in the object-valued 'extensions'"
            )
    if "extensions" in payload and not isinstance(payload["extensions"], dict):
        result.add_error(
            "version-1 sidecar 'extensions' must be an object when present"
        )
    # Array/object-typed required fields: the targeted mistyped-container
    # errors are emitted by the shared ``_require_array`` / ``_require_object``
    # guards inside ``validate_current_payload`` (r4 F10 collapse), which runs
    # for every current shape including version-1 records. A mistyped
    # container (dict, string, int) gets a targeted hard error there instead
    # of a silent skip or an AttributeError/TypeError traceback; missing
    # required fields are reported by the required-field loop above.

    v1_findings = payload.get("findings")
    if not isinstance(v1_findings, list):
        v1_findings = []  # type gate already reported; never iterate
    for finding in v1_findings:
        if not isinstance(finding, dict):
            continue
        fid = finding.get("id")
        if "pattern" not in finding:
            result.add_error(
                f"version-1 finding {fid} missing canonical pattern"
            )
        else:
            validate_canonical_pattern(
                finding["pattern"], f"version-1 finding {fid}", result
            )
    v1_overflow = payload.get("overflow")
    if not isinstance(v1_overflow, list):
        v1_overflow = []
    for item in v1_overflow:
        if isinstance(item, dict) and "pattern" in item:
            validate_canonical_pattern(
                item["pattern"], "version-1 overflow item", result
            )
    v1_discarded = payload.get("discarded")
    if not isinstance(v1_discarded, list):
        v1_discarded = []
    for row in v1_discarded:
        if isinstance(row, dict) and "pattern" in row:
            validate_canonical_pattern(
                row["pattern"], "version-1 discarded finding", result
            )

    # Markdown/sidecar pattern conservation: a version-1 finding cannot omit
    # its Pattern in the human record or present a different canonical pattern
    # than its sidecar entry.
    md_by_id = {
        f["id"]: f
        for f in parse_markdown_findings(content)
        if isinstance(f.get("id"), int)
    }
    for finding in v1_findings:
        if not isinstance(finding, dict):
            continue
        fid = finding.get("id")
        if not isinstance(fid, int) or fid not in md_by_id:
            continue  # id reconciliation is the generic conservation check
        md_pattern = md_by_id[fid].get("pattern")
        if not md_pattern:
            result.add_error(
                f"finding conservation: finding {fid} Markdown record is "
                f"missing its Pattern"
            )
        elif md_pattern != finding.get("pattern"):
            result.add_error(
                f"finding conservation: finding {fid} pattern disagrees "
                f"(Markdown {md_pattern!r}, sidecar {finding.get('pattern')!r})"
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
    schema_class = classify_sidecar_schema(payload)
    if schema_class == "unsupported":
        result.add_error(
            f"unsupported stats sidecar schema_version "
            f"{payload.get('schema_version')!r}; supported versions: "
            f"{list(SUPPORTED_SIDECAR_SCHEMA_VERSIONS)}"
        )
    elif schema_class == "current-v1":
        validate_version1_payload(payload, content, result)
    is_current = schema_class in CURRENT_SHAPE_LABELS
    if is_current:
        validate_current_payload(
            payload,
            content,
            result,
            expected_digest=expected_digest,
            source_kind=source_kind,
            schema_label=schema_class,
        )
    discarded = _require_array(
        payload, "discarded", result, schema_class
    )
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
    schema_label: str | None = None,
) -> None:
    panel_mode = payload.get("panel_mode")
    # The schema label is computed ONCE per validation run, in
    # ``validate_stats_sidecar``, and threaded in via ``schema_label``; the
    # internal classification below (r4 F10) exists only for direct callers
    # that do not supply a label. The label is fed to the shared
    # _require_array / _require_object guards: the targeted mistyped-container
    # error is keyed on the label, so version-1 records, versionless current
    # shapes, and pure legacy records all get their documented disposition
    # from one place. Versionless current shapes never reach the version-1
    # field gates, but they ARE actively validated here: a present-but-mistyped
    # container gets a targeted error instead of a silent empty substitution,
    # which would skip the counts/consistency gates below (r3 F3 false
    # accept). Pure legacy shapes are skipped (compatibility input).
    if schema_label is None:
        schema_label = classify_sidecar_schema(payload)
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

    panel = _require_array(payload, "panel", result, schema_label)
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

    counts = _require_object(payload, "counts", result, schema_label)
    if "workers_launched" in counts and counts["workers_launched"] != len(launched):
        result.add_error("counts.workers_launched does not match panel launches")

    findings = _require_array(payload, "findings", result, schema_label)
    # r6 F5: every finding row carries an integer id. Absence silently
    # sorts as 0 in the order check and homogeneous string ids compare
    # fine as strings, while mixed-type ids crash the order-check sort
    # with a TypeError traceback. Gate the id here (bool is rejected
    # alongside non-int: bool is an int subclass) and keep gating the
    # remaining fields so one run reports all finding-level defects.
    # r6 F5 / r1 F4 / r3 F2: ``id_ok`` is the single id predicate, gating
    # the targeted id errors, the append decision, and the display label
    # below. Rows reaching the append must pass the id gate AND carry a
    # string severity (r3 F1: unhashable severities must stay out of the
    # order-check sort); the append lives in the severity branch below.
    valid_rows: list = []
    # v1-gate-trio: ids already seen among valid-id rows. The duplicate gate
    # is additive error reporting only: the duplicate row keeps its
    # ``valid_rows`` membership (equal ids at one severity are sort-safe for
    # the frozen order-check sort key), so no membership logic changes.
    seen_ids: set = set()
    for i, finding in enumerate(findings):
        if not isinstance(finding, dict):
            result.add_error("current finding must be an object")
            continue
        fid = finding.get("id")
        id_ok = (
            "id" in finding
            and isinstance(fid, int)
            and not isinstance(fid, bool)
        )
        if not id_ok:
            if "id" not in finding:
                result.add_error(f"current finding at index {i} missing id")
            else:
                result.add_error(
                    f"current finding {fid!r} id must be an integer"
                )
        elif isinstance(finding.get("severity"), str):
            # r3 F1: an unhashable severity (e.g. a list) would crash the
            # frozen order-check sort key with a TypeError; keeping such
            # rows out of ``valid_rows`` leaves the targeted
            # invalid-severity error below as the single reporter.
            valid_rows.append(finding)
        # r2 F2/F3: one display label per row keeps the sibling errors
        # below attributable when the id gate failed (an id-less row would
        # otherwise render every sibling error as `current finding None
        # ...`). r3 F4: only valid integer ids are rendered via repr into
        # the label; any malformed id (string, bool, missing) falls back
        # to the `at index {i!r}` label, so a malformed id value can
        # never forge or garble collected error output.
        if id_ok:
            display = repr(fid)
            # v1-gate-trio: duplicate ids are rejected here, after the
            # display-label computation so {display} is defined. Only
            # valid-id rows participate (a malformed id keeps its own
            # targeted error). Both statements depend on exactly id_ok,
            # which nothing between them invalidates.
            if fid in seen_ids:
                result.add_error(
                    f"current finding {display} duplicate id"
                )
            else:
                seen_ids.add(fid)
        else:
            display = f"at index {i!r}"
        # v1-gate-trio: an omitted severity key gets its own message so an
        # author can distinguish it from a typo'd value; the invalid-severity
        # gate below becomes the present-but-wrong-value reporter only.
        if "severity" not in finding:
            result.add_error(f"current finding {display} missing severity")
        elif finding.get("severity") not in SEVERITY_ORDER:
            result.add_error(
                f"current finding {display} has invalid severity "
                f"(expected one of {list(SEVERITY_ORDER)})"
            )
        # blocking must be a real Python bool, not a string/int coercion.
        if "blocking" in finding and not isinstance(finding["blocking"], bool):
            result.add_error(
                f"current finding {display} blocking must be a boolean, "
                f"got {type(finding['blocking']).__name__}"
            )
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
                f"(expected one of {sorted(VALID_CONFIDENCE)})"
            )
        for field_name in REQUIRED_CURRENT_FINDING_FIELDS:
            if field_name not in finding:
                result.add_error(
                    f"current finding {display} missing {field_name}"
                )
    # r6 F5: only rows appended inside the findings loop — dict rows that
    # passed the id gate and carry a string severity (r3 F1) — are passed
    # to the order check, so mixed-type ids and unhashable severities can
    # never reach the sort (the errored rows already carry their targeted
    # errors above). validate_finding_order deliberately retains its own
    # defensive dict-rows filter for direct callers.
    validate_finding_order(valid_rows, result)
    validate_finding_budget(findings, result)

    overflow = _require_array(payload, "overflow", result, schema_label)
    for item in overflow:
        if not isinstance(item, dict):
            result.add_error("overflow item must be an object")
            continue
        if item.get("severity") == "Critical" or item.get("blocking") is True:
            result.add_error("Critical or blocking finding cannot be in overflow")

    # r4 F1: the versionless current-shape type gates now also cover
    # severity_calibration (and the remaining version-1 array fields), so a
    # truthy mistyped value (e.g. the integer 5) can never reach the
    # summarizer's len-derived counts and crash the strict audit. Absent and
    # JSON null stay absent (r4 F14).
    _require_array(payload, "severity_calibration", result, schema_label)
    _require_array(payload, "deduplication_groups", result, schema_label)
    _require_array(payload, "soften_watchlist", result, schema_label)

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

    # r6 F2: a non-dict entry already produced the targeted
    # finding-must-be-an-object error upstream; it must not also crash this
    # sort. Compare only dict rows.
    dict_rows = [row for row in findings if isinstance(row, dict)]
    if dict_rows != sorted(dict_rows, key=key):
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
        # r6 F1: a sidecar blocking true must never pair with a Markdown
        # record whose Blocking value is unparseable (omitted bullet, or the
        # bullet fenced inside the metadata region). Without this arm the
        # readiness predicate and the hard gate both fail open on exactly the
        # findings they exist to hold.
        elif sc.get("blocking") is True and md.get("blocking") is None:
            result.add_error(
                f"finding conservation: finding {sid} sidecar blocking is true "
                f"but the Markdown record has no parseable Blocking value"
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

    # r6 F5 finding-id gates. RED fixtures: each check must fail until the
    # findings-loop gate exists (missing id / integer id). Recipe: render the
    # markdown from the unmutated two-finding list first, then mutate the
    # sidecar payload, so failures stay attributable to the gate under test
    # instead of garbled-header conservation noise.
    # _payload_with_findings does not deep-copy the finding dicts, so each
    # fixture builds its own fresh two-finding list to stay isolated.
    # r1 F6: the shared recipe lives in one local runner; each fixture is a
    # slug/title/mutation/assertion tuple. A TypeError escaping the
    # validation run is caught (result None) so the RED phase records FAIL
    # instead of aborting the whole selftest suite.
    def _run_id_fixture(
        slug: str, title: str, mutate, errors_ok, label: str
    ) -> None:
        two = [_current_finding(id=1), _current_finding(id=2)]
        md = _current_findings_markdown(two, title=title)
        fixture_payload = _payload_with_findings(two)
        mutate(fixture_payload)
        fixture_path = _write_staging(
            root,
            f"2026-07-17-branch-review-id-{slug}-r1.md",
            md,
            fixture_payload,
        )
        try:
            fixture_result = validate_staging_file(fixture_path, hard=True)
        except TypeError:
            fixture_result = None
        check(
            label,
            fixture_result is not None and errors_ok(fixture_result.errors),
        )

    def _mutate_missing_id(p: dict) -> None:
        del p["findings"][1]["id"]

    _run_id_fixture(
        "missing",
        "id-missing",
        _mutate_missing_id,
        lambda errors: any("missing id" in e for e in errors),
        "finding id missing rejected",
    )

    # r4 F4: pin the display-label index fallback. The same id-less row also
    # carries a sibling defect (invalid severity); its sibling error must be
    # attributed via the `at index` label, not a repr'd id.
    def _mutate_missing_id_and_bad_severity(p: dict) -> None:
        del p["findings"][1]["id"]
        p["findings"][1]["severity"] = "Blocker"

    _run_id_fixture(
        "missing-sibling",
        "id-missing-sibling",
        _mutate_missing_id_and_bad_severity,
        lambda errors: any("missing id" in e for e in errors)
        and any(
            "at index" in e and "invalid severity" in e for e in errors
        ),
        "missing id row keeps sibling errors attributed via index label",
    )

    # Homogeneous string ids keep every sort key tuple same-kind, so neither
    # the gate phase nor the order check may crash the sort (silent-pass shape).
    def _mutate_str_ids(p: dict) -> None:
        p["findings"][0]["id"] = "F1"
        p["findings"][1]["id"] = "F2"

    _run_id_fixture(
        "string",
        "id-string",
        _mutate_str_ids,
        lambda errors: sum("must be an integer" in e for e in errors) >= 2,
        "finding id string rejected",
    )

    # bool is an int subclass in Python; it must not pass the integer gate.
    # Sibling id pinned at 2 keeps sort keys deterministic by construction.
    def _mutate_bool_id(p: dict) -> None:
        p["findings"][0]["id"] = True

    _run_id_fixture(
        "bool",
        "id-bool",
        _mutate_bool_id,
        lambda errors: sum("must be an integer" in e for e in errors) == 1
        and any("True" in e for e in errors),
        "finding id bool rejected",
    )

    # Mixed-type ids crash sorted() today; the runner's TypeError catch
    # records the crash so the check can assert it never happens.
    def _mutate_mixed_id(p: dict) -> None:
        p["findings"][0]["id"] = "F1"

    _run_id_fixture(
        "mixed",
        "id-mixed",
        _mutate_mixed_id,
        lambda errors: any("must be an integer" in e for e in errors),
        "finding id mixed types never crash the sort",
    )

    # r3 F1 RED fixture: a list severity is unhashable, so the frozen
    # order-check sort key would crash with a TypeError; the targeted
    # invalid-severity error must be the single reporter and the run must
    # not crash (the runner's TypeError catch above records a FAIL).
    def _mutate_list_severity(p: dict) -> None:
        p["findings"][0]["severity"] = ["High"]

    _run_id_fixture(
        "severity-list",
        "id-severity-list",
        _mutate_list_severity,
        lambda errors: any("invalid severity" in e for e in errors),
        "finding severity unhashable never crashes the sort",
    )

    # r4 F1 RED fixture: a list blast_radius is unhashable, so the
    # frozenset membership check would crash with a TypeError before any
    # targeted error is recorded; the targeted invalid-blast_radius error
    # must be the single reporter and the run must not crash (the runner's
    # TypeError catch above records a FAIL).
    def _mutate_list_blast_radius(p: dict) -> None:
        p["findings"][0]["blast_radius"] = ["global"]

    _run_id_fixture(
        "blast-radius-list",
        "id-blast-radius-list",
        _mutate_list_blast_radius,
        lambda errors: any("invalid blast_radius" in e for e in errors),
        "finding blast_radius unhashable never crashes the membership check",
    )

    # v1-gate-trio fixture: duplicate ids. Two rows sharing an id used to
    # validate clean — conservation reconciled both rows against their
    # Markdown blocks and the sort key (severity_rank, id) tolerates equal
    # ids — so triage references like "F1" became ambiguous. The findings-
    # loop duplicate gate must report the repeat row exactly once.
    def _mutate_duplicate_id(p: dict) -> None:
        p["findings"][1]["id"] = 1

    _run_id_fixture(
        "duplicate-id",
        "id-duplicate",
        _mutate_duplicate_id,
        lambda errors: sum("duplicate id" in e for e in errors) == 1,
        "duplicate finding ids rejected (exactly one report)",
    )

    # v1-gate-trio follow-up: pin the duplicate gate's additive-only
    # contract. The sidecar AND the markdown agree on ids [1, 1], so the
    # duplicate error must be the single report and the duplicate rows must
    # stay in conservation reconciliation and the order check (a refactor
    # evicting them from valid_rows must turn this RED).
    two_dup = [_current_finding(id=1), _current_finding(id=1)]
    md_dup = _current_findings_markdown(two_dup, title="id-duplicate-agreeing")
    dup_agreeing_path = _write_staging(
        root,
        "2026-07-17-branch-review-id-duplicate-agreeing-r1.md",
        md_dup,
        _payload_with_findings(two_dup),
    )
    try:
        dup_agreeing_result = validate_staging_file(dup_agreeing_path, hard=True)
    except TypeError:
        dup_agreeing_result = None
    check(
        "duplicate ids keep rows in conservation and order checks (single additive report)",
        dup_agreeing_result is not None
        and sum("duplicate id" in e for e in dup_agreeing_result.errors) == 1
        and not any(
            "conservation" in e or "order" in e
            for e in dup_agreeing_result.errors
        ),
    )

    # v1-gate-trio RED fixture: a row with no severity key is today
    # misreported as "has invalid severity (expected one of ...)", hiding
    # the omitted-key vs typo'd-value distinction. The dedicated message
    # must appear and the invalid-severity misreport must disappear for the
    # severity-less row (both directions pinned in one assertion).
    def _mutate_missing_severity(p: dict) -> None:
        del p["findings"][1]["severity"]

    _run_id_fixture(
        "missing-severity",
        "id-missing-severity",
        _mutate_missing_severity,
        lambda errors: any("missing severity" in e for e in errors)
        and not any("invalid severity" in e for e in errors),
        "missing severity gets a dedicated message (no invalid-severity misreport)",
    )

    # v1-gate-trio follow-up: a present explicit-null severity must hit the
    # invalid-severity arm; null is not the absent form here (unlike the
    # version-1 enum-reason carve-out). Guards a refactor that treats null
    # as omitted, which would silently accept severity-less rows.
    def _mutate_null_severity(p: dict) -> None:
        p["findings"][1]["severity"] = None

    _run_id_fixture(
        "severity-null",
        "id-severity-null",
        _mutate_null_severity,
        lambda errors: any("invalid severity" in e for e in errors)
        and not any("missing severity" in e for e in errors),
        "explicit-null severity reported as invalid, not missing",
    )

    # F13 RED probe: one validation run must classify the sidecar payload
    # exactly once. Rebind the module-global classify_sidecar_schema with a
    # counting wrapper that delegates to the original; the ONE production
    # classification on the validate_staging_file path is the call in
    # validate_stats_sidecar (is_current_shape is exported for the
    # summarizer and is no longer called on this path;
    # validate_current_payload receives the threaded schema_label and
    # classifies only when schema_label is None, which never happens in the
    # run below), and it resolves the global at call time, so the wrapper
    # intercepts it. Restore the original in finally so the rebinding never
    # leaks into other checks.
    probe_path = _write_staging(
        root,
        "2026-07-17-branch-review-classify-probe-r1.md",
        _current_clear_markdown("classify-probe"),
        _current_clear_payload(),
    )
    original_classify = classify_sidecar_schema
    classify_calls = [0]

    def _counting_classify(payload: object) -> str:
        classify_calls[0] += 1
        return original_classify(payload)

    globals()["classify_sidecar_schema"] = _counting_classify
    try:
        validate_staging_file(probe_path, hard=True)
    finally:
        globals()["classify_sidecar_schema"] = original_classify
    check(
        "sidecar payload classified exactly once per run",
        classify_calls[0] == 1,
    )

    # r2 F5: the plan-mandated schema_label=None backward-compat surface
    # (internal classification for direct callers) needs a driving fixture:
    # a direct call WITHOUT schema_label on a current-shape payload with a
    # mistyped container must produce the classified-label error, not the
    # pure-legacy silent skip. That message is only emitted when the
    # internal classification landed on a current-shape label.
    labelless_payload = json.loads(json.dumps(_current_clear_payload()))
    labelless_payload["panel"] = 5
    labelless_result = ValidationResult(path=Path("labelless"))
    validate_current_payload(
        labelless_payload,
        _current_clear_markdown("labelless"),
        labelless_result,
    )
    check(
        "direct call without schema_label classifies internally "
        "(mistyped container gets the current-shape error)",
        any(
            "current sidecar 'panel' must be an array when present" in e
            for e in labelless_result.errors
        ),
    )


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
        any("must be a boolean" in e for e in str_bool_res.errors),
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
        any("must be a boolean" in e and "got int" in e for e in int_bool_res.errors),
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
            "finding budget exceeded" in e
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
            "finding budget exceeded" in e
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

    # Negative: triage disagreement (Markdown dropped vs sidecar pending).
    # Fixtures are built as data (via the markdown builder) so a triage word
    # appearing in prose can never satisfy the assertion by accident.
    tri_md = _current_findings_markdown(
        [_current_finding(id=1, severity="Medium", blocking=False)]
    ).replace("- **Triage**: pending", "- **Triage**: dropped", 1)
    tri_payload = _payload_with_findings(
        [_current_finding(id=1, severity="Medium", blocking=False)]
    )
    tri_payload["findings"][0]["triage"] = "pending"
    tri_path = _write_staging(
        root, "2026-07-17-branch-review-cons-tri-r1.md", tri_md, tri_payload
    )
    check(
        "triage disagreement between Markdown and sidecar fails conservation",
        any(
            "triage disagrees" in e
            for e in validate_staging_file(tri_path, hard=True).errors
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

    # r5 F9: an empty --source-plan value must fail LOUDLY (argparse error,
    # exit 2), never silently skip the stale-digest gate. Pre-fix the
    # truthiness routing treated "" as not-supplied and exited 0.
    try:
        main(["--hard", str(staging), "--source-plan", ""])
        empty_rc: object = None
    except SystemExit as exc:
        empty_rc = exc.code
    check(
        "--source-plan empty value exits loudly (does not silently skip the digest gate, r5 F9)",
        empty_rc == 2,
    )


def _selftest_source_rfc_cli(root: Path, check) -> None:
    """The --source-rfc CLI flag must recompute the RFC digest and reach the
    stale-digest comparison, with the sidecar's source_kind type-checked as
    'rfc'. Mirrors _selftest_source_plan_cli. Each case must be DISCRIMINATING:
    it must fail if the wiring were severed (expected_digest dropped), not pass
    via the presence-only path."""
    import io

    rfc_path = root / "rfc.md"
    rfc_bytes = b"# RFC\n## Goals\n1. do foo\n"
    rfc_path.write_bytes(rfc_bytes)
    rfc_digest = compute_source_digest("rfc", rfc_bytes)

    other_path = root / "other-rfc.md"
    other_path.write_bytes(b"# Not the rfc\n")

    payload = json.loads(json.dumps(_current_clear_payload()))
    payload["source_digest"] = rfc_digest
    payload["source_kind"] = "rfc"
    staging = _write_staging(
        root, "2026-07-17-rfc-review-cli-r1.md",
        _current_clear_markdown("cli"), payload,
    )

    # Case A: point --source-rfc at the CORRECT rfc -> exit 0.
    rc_fresh = main(["--hard", str(staging), "--source-rfc", str(rfc_path)])
    check("--source-rfc fresh (correct rfc) exits 0", rc_fresh == 0)

    # Case A': point --source-rfc at a DIFFERENT file -> exit 1.
    rc_wrong_file = main(["--hard", str(staging), "--source-rfc", str(other_path)])
    check(
        "--source-rfc against a different file exits 1 (wiring is live)",
        rc_wrong_file == 1,
    )

    # Case B: fold the RFC (digest changes) -> exit 1 with stale error AND the
    # F7 path hint naming the hashed file via --source-rfc.
    rfc_path.write_bytes(rfc_bytes + b"\nfolded F1\n")
    buf = io.StringIO()
    real_stderr = sys.stderr
    sys.stderr = buf
    try:
        rc_stale = main(["--hard", str(staging), "--source-rfc", str(rfc_path)])
    finally:
        sys.stderr = real_stderr
    stale_text = buf.getvalue()
    check(
        "--source-rfc stale (post-fold) digest exits 1 with stale error",
        rc_stale == 1 and "stale" in stale_text and "source_digest" in stale_text,
    )
    check(
        "stale-digest error names --source-rfc and the hashed source-path (F7)",
        "--source-rfc" in stale_text and str(rfc_path) in stale_text,
    )

    # Case C: missing source-rfc file -> exit 1.
    rc_missing = main(
        ["--hard", str(staging), "--source-rfc", str(root / "nope.md")]
    )
    check("--source-rfc missing file exits 1", rc_missing == 1)

    # Case D: source_kind mismatch — sidecar says 'plan' but flag is --source-rfc
    # -> exit 1 with a mismatch error. Pins that the flag type-checks the
    # sidecar's declared kind rather than asserting it in prose.
    payload_plan = json.loads(json.dumps(_current_clear_payload()))
    payload_plan["source_digest"] = rfc_digest
    payload_plan["source_kind"] = "plan"
    staging_plan = _write_staging(
        root, "2026-07-17-rfc-review-cli-r1-plan.md",
        _current_clear_markdown("cli"), payload_plan,
    )
    rc_kind_mismatch = main(
        ["--hard", str(staging_plan), "--source-rfc", str(rfc_path)]
    )
    buf2 = io.StringIO()
    real_stderr2 = sys.stderr
    sys.stderr = buf2
    try:
        main(["--hard", str(staging_plan), "--source-rfc", str(rfc_path)])
    finally:
        sys.stderr = real_stderr2
    check(
        "--source-rfc rejects a sidecar declaring source_kind=plan",
        rc_kind_mismatch == 1 and "source_kind mismatch" in buf2.getvalue(),
    )


def _selftest_source_doc_cli(root: Path, check) -> None:
    """The --source-doc CLI flag (r4 F4) must recompute the document digest
    and reach the stale-digest comparison, with the sidecar's source_kind
    type-checked as 'document'. Mirrors _selftest_source_plan_cli. Each case
    must be DISCRIMINATING: pre-fix (no --source-doc flag) this whole test
    could not pass because argparse rejected the unknown flag."""
    import io

    doc_path = root / "doc.md"
    doc_bytes = b"# Doc\n## Steps\n1. do foo\n"
    doc_path.write_bytes(doc_bytes)
    doc_digest = compute_source_digest("document", doc_bytes)

    other_path = root / "other-doc.md"
    other_path.write_bytes(b"# Not the doc\n")

    payload = json.loads(json.dumps(_current_clear_payload()))
    payload["source_digest"] = doc_digest
    payload["source_kind"] = "document"
    staging = _write_staging(
        root, "2026-07-17-confluence-review-cli-r1.md",
        _current_clear_markdown("cli"), payload,
    )

    # Case A: point --source-doc at the CORRECT document -> exit 0.
    rc_fresh = main(["--hard", str(staging), "--source-doc", str(doc_path)])
    check("--source-doc fresh (correct document) exits 0", rc_fresh == 0)

    # Case A': point --source-doc at a DIFFERENT file -> exit 1 (wiring live).
    rc_wrong_file = main(["--hard", str(staging), "--source-doc", str(other_path)])
    check(
        "--source-doc against a different file exits 1 (wiring is live)",
        rc_wrong_file == 1,
    )

    # Case B: stale post-edit document -> exit 1 with stale error and hint.
    doc_path.write_bytes(doc_bytes + b"\nupdated section\n")
    buf = io.StringIO()
    real_stderr = sys.stderr
    sys.stderr = buf
    try:
        rc_stale = main(["--hard", str(staging), "--source-doc", str(doc_path)])
    finally:
        sys.stderr = real_stderr
    stale_text = buf.getvalue()
    check(
        "--source-doc stale digest exits 1 with stale error",
        rc_stale == 1 and "stale" in stale_text and "source_digest" in stale_text,
    )
    check(
        "stale-digest error names --source-doc and the hashed source-path",
        "--source-doc" in stale_text and str(doc_path) in stale_text,
    )

    # Case C: missing --source-doc file -> exit 1.
    rc_missing = main(
        ["--hard", str(staging), "--source-doc", str(root / "nope.md")]
    )
    check("--source-doc missing file exits 1", rc_missing == 1)

    # Case D: source_kind mismatch — sidecar says 'plan' but flag is
    # --source-doc -> exit 1 with a mismatch error (the flag type-checks the
    # sidecar's declared kind; the pre-fix workaround of passing a
    # document-kind digest via --source-plan hard-failed the same way).
    payload_plan = json.loads(json.dumps(_current_clear_payload()))
    payload_plan["source_digest"] = doc_digest
    payload_plan["source_kind"] = "plan"
    staging_plan = _write_staging(
        root, "2026-07-17-confluence-review-cli-r1-plan.md",
        _current_clear_markdown("cli"), payload_plan,
    )
    buf2 = io.StringIO()
    real_stderr2 = sys.stderr
    sys.stderr = buf2
    try:
        rc_kind_mismatch = main(
            ["--hard", str(staging_plan), "--source-doc", str(doc_path)]
        )
    finally:
        sys.stderr = real_stderr2
    check(
        "--source-doc rejects a sidecar declaring source_kind=plan",
        rc_kind_mismatch == 1 and "source_kind mismatch" in buf2.getvalue(),
    )

    # Case E: the three source flags are mutually exclusive.
    buf3 = io.StringIO()
    real_stderr3 = sys.stderr
    sys.stderr = buf3
    try:
        main(
            [
                "--hard", str(staging),
                "--source-doc", str(doc_path),
                "--source-plan", str(doc_path),
            ]
        )
        rc_both = 2  # argparse SystemExit(2) is raised before main returns
    except SystemExit as exc:
        rc_both = int(exc.code)
    finally:
        sys.stderr = real_stderr3
    check(
        "--source-doc and --source-plan are mutually exclusive",
        rc_both == 2 and "mutually exclusive" in buf3.getvalue(),
    )


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


# Version-1 sidecar contract (review-artifact-contracts plan). The selftests
# below reuse the production constants (V1_REQUIRED_TOP_LEVEL_FIELDS /
# V1_OPTIONAL_TOP_LEVEL_FIELDS) directly: no test-local copies, so the
# enforced contract and its test coverage cannot drift apart.
# ``schema_version`` is deliberately NOT in the selftest missing-field loop:
# a payload without ``schema_version`` is by definition legacy (legacy
# classification check), not a version-1 schema error.


def _version1_payload(*, pattern: str = "testing#weak-assertion") -> dict:
    """Build a complete version-1 sidecar payload with one canonical finding.

    Carries every required top-level field plus each optional field in its
    permitted type (``depth`` string, ``domains`` list, ``extensions`` object).
    """
    payload = _payload_with_findings([_current_finding(pattern=pattern)])
    payload.update(
        {
            "schema_version": 1,
            "review_type": "code",
            "date": "2026-08-28",
            "artifact_slug": "sample-branch",
            "round": 1,
            "selection_reason": None,
            "source_kind": "code",
            "source_digest": "0" * 64,
            "escalation_reason": None,
            "deduplication_groups": [],
            "discarded": [],
            "severity_calibration": [],
            "triage_outcomes": {},
            "soften_watchlist": [],
            "depth": "standard",
            "domains": ["docs"],
            "extensions": {"example": True},
        }
    )
    return payload


def _version1_markdown(*, pattern: str = "testing#weak-assertion") -> str:
    """Current-format findings Markdown whose finding carries a matching
    ``- **Pattern``: <canonical pattern>`` bullet for the conservation check."""
    md = _current_findings_markdown([_current_finding()], title="versioned")
    return md.replace(
        "- **Blocking**: false",
        f"- **Blocking**: false\n- **Pattern**: {pattern}",
        1,
    )


def _selftest_versioned_schema_and_patterns(root: Path, check) -> None:
    """Family: versioned (``schema_version: 1``) sidecar contract and canonical
    ``lens#kebab-slug`` pattern IDs (review-artifact-contracts plan).

    RED-first family: the negative checks fail until the versioned schema and
    pattern contract is implemented (Task 2 of the plan)."""
    import json as _json

    def stage(name: str, payload: dict, md: str) -> Path:
        return _write_staging(
            root, f"2026-07-17-branch-review-v1-{name}-r1.md", md, payload
        )

    base_md = _version1_markdown()
    base_payload = _version1_payload()

    # Positive: a complete version-1 sidecar with a canonical
    # testing#weak-assertion finding (and valid extensions object) passes hard.
    ok_path = stage("ok", base_payload, base_md)
    check(
        "v1 contract: complete version-1 sidecar with canonical pattern passes hard",
        validate_staging_file(ok_path, hard=True).ok,
    )

    # Negative: invalid sidecar patterns must fail hard with a targeted error.
    pattern_cases = {
        "missing pattern": None,
        "malformed pattern": "testingweakassertion",
        "slash-delimited pattern": "testing/weak-assertion",
        "unknown owner": "mystery#weak-assertion",
        "legacy prose-clarity owner": "prose-clarity#run-on",
    }
    for name, bad_pattern in pattern_cases.items():
        payload = _version1_payload()
        if bad_pattern is None:
            del payload["findings"][0]["pattern"]
        else:
            payload["findings"][0]["pattern"] = bad_pattern
        result = validate_staging_file(
            stage(f"pat-{name.replace(' ', '-')}", payload, base_md), hard=True
        )
        check(
            f"v1 contract: version-1 {name} fails hard with a pattern error",
            not result.ok and any("pattern" in e.lower() for e in result.errors),
        )

    # r3 F4: the five cases above are also satisfied by the Markdown/sidecar
    # conservation error alone (each mutates only the sidecar pattern), so
    # they do not discriminate the canonical pattern gate itself. These
    # agreeing-bad-pattern cases carry the SAME noncanonical pattern in both
    # the Markdown record and the sidecar, so conservation stays quiet and
    # only validate_canonical_pattern can fail the check — each asserting the
    # gate's specific message.
    agreeing_cases = (
        (
            "legacy prose-clarity owner",
            "prose-clarity#run-on",
            "is not a declared shared lens",
        ),
        (
            "slash-delimited pattern",
            "testing/weak-assertion",
            "is not a canonical Pattern ID",
        ),
    )
    for name, bad_pattern, gate_message in agreeing_cases:
        payload = _version1_payload(pattern=bad_pattern)
        md = _version1_markdown(pattern=bad_pattern)
        result = validate_staging_file(
            stage(f"agree-{name.replace(' ', '-')}", payload, md), hard=True
        )
        check(
            f"v1 contract: agreeing {name} in Markdown and sidecar fails on the canonical gate",
            not result.ok and any(gate_message in e for e in result.errors),
        )

    # r4 F7: the canonical-pattern gates for overflow items and discarded rows
    # had zero negative coverage (the loops above mutated findings only), so
    # deleting either container gate kept the suite green. Inject each bad
    # pattern value into both containers and assert the targeted hard failure.
    for container_name, gate_label in (
        ("overflow", "version-1 overflow item"),
        ("discarded", "version-1 discarded finding"),
    ):
        for name, bad_pattern in pattern_cases.items():
            if bad_pattern is None:
                # "missing pattern" applies to findings only: overflow and
                # discarded rows may legitimately omit a pattern.
                continue
            payload = _version1_payload()
            if container_name == "overflow":
                payload["overflow"] = [
                    {"severity": "Low", "blocking": False, "pattern": bad_pattern}
                ]
            else:
                payload["discarded"] = [
                    {"pattern": bad_pattern, "reason": "duplicate"}
                ]
            result = validate_staging_file(
                stage(
                    f"pat-{container_name}-{name.replace(' ', '-')}",
                    payload,
                    base_md,
                ),
                hard=True,
            )
            check(
                f"v1 contract: {name} in a {container_name} row fails hard "
                "with the container pattern gate",
                not result.ok and any(gate_label in e for e in result.errors),
            )
    # Positive twin: canonical patterns on BOTH containers validate hard.
    canonical_containers = _version1_payload()
    canonical_containers["overflow"] = [
        {"severity": "Low", "blocking": False, "pattern": "testing#spill-case"}
    ]
    canonical_containers["discarded"] = [
        {
            "worker": "testing",
            "worker_severity": "Low",
            "pattern": "testing#duplicate-case",
            "theme": "Same root cause as F1",
            "reason": "duplicate",
        }
    ]
    check(
        "v1 contract: canonical patterns on overflow and discarded rows pass hard",
        validate_staging_file(
            stage("pat-containers-ok", canonical_containers, base_md), hard=True
        ).ok,
    )

    # Markdown/sidecar pattern conservation: the Markdown finding must carry
    # the same canonical pattern as the sidecar.
    no_pattern_md = _current_findings_markdown([_current_finding()], title="versioned")
    result = validate_staging_file(
        stage("md-nopattern", base_payload, no_pattern_md), hard=True
    )
    check(
        "v1 contract: Markdown finding missing a Pattern fails hard",
        not result.ok and any("pattern" in e.lower() for e in result.errors),
    )
    diff_md = _version1_markdown(pattern="quality#other-case")
    result = validate_staging_file(
        stage("md-diffpattern", base_payload, diff_md), hard=True
    )
    check(
        "v1 contract: Markdown Pattern differing from sidecar Pattern fails hard",
        not result.ok and any("pattern" in e.lower() for e in result.errors),
    )

    # Extensions: object-valued passes (covered by the ok case); non-object
    # fails; an arbitrary undocumented top-level field fails.
    ext_payload = _version1_payload()
    ext_payload["extensions"] = "not-an-object"
    result = validate_staging_file(stage("ext-bad", ext_payload, base_md), hard=True)
    check(
        "v1 contract: non-object extensions fails hard",
        not result.ok and any("extensions" in e.lower() for e in result.errors),
    )
    extra_payload = _version1_payload()
    extra_payload["custom_future_field"] = True
    result = validate_staging_file(stage("extra-field", extra_payload, base_md), hard=True)
    check(
        "v1 contract: arbitrary undocumented top-level field fails hard",
        not result.ok
        and any("custom_future_field" in e or "top-level" in e.lower() for e in result.errors),
    )

    # Non-list container fields (F2/F6): a targeted hard error naming the
    # field, not a silent version-1 pass or an AttributeError/TypeError
    # traceback. All seven array-gated fields are covered so removing one from
    # the gate tuple cannot pass silently.
    for field_name, bad_value in (
        ("findings", {"a": 1}),
        ("discarded", 5),
        ("panel", {"worker": 1}),
        ("overflow", "not-a-list"),
        ("deduplication_groups", 7),
        ("severity_calibration", "oops"),
        ("soften_watchlist", {"x": 1}),
    ):
        bad_container = _json.loads(_json.dumps(base_payload))
        bad_container[field_name] = bad_value
        result = validate_staging_file(
            stage(f"bad-container-{field_name}", bad_container, base_md), hard=True
        )
        check(
            f"v1 contract: non-array {field_name!r} fails hard with a type error",
            not result.ok
            and any(
                f"{field_name!r} must be an array" in e for e in result.errors
            ),
        )

    # Non-dict counts (F1): targeted type error, never a TypeError traceback
    # in the counts comparison.
    bad_counts = _json.loads(_json.dumps(base_payload))
    bad_counts["counts"] = 5
    result = validate_staging_file(
        stage("bad-container-counts", bad_counts, base_md), hard=True
    )
    check(
        "v1 contract: non-object 'counts' fails hard with a type error",
        not result.ok
        and any("'counts' must be an object" in e for e in result.errors),
    )

    # Versionless current-shaped payloads: a present-but-non-list findings
    # container must fail hard (not silently pass with findings=[]), keeping
    # the pre-branch hard failure and the conservation check meaningful.
    legacy_bad_findings = _json.loads(_json.dumps(base_payload))
    del legacy_bad_findings["schema_version"]
    legacy_bad_findings["findings"] = {"1": dict(legacy_bad_findings["findings"][0])}
    result = validate_staging_file(
        stage("bad-findings-versionless", legacy_bad_findings, base_md), hard=True
    )
    check(
        "v1 contract: non-array findings on a versionless current-shaped sidecar fails hard",
        not result.ok
        and any("'findings' must be an array" in e for e in result.errors),
    )

    # r3 F3: the versionless current-shape guard covers the OTHER containers
    # too (counts / panel / overflow / discarded): a present-but-mistyped
    # container must fail hard with a targeted error instead of being silently
    # substituted with an empty value, which would skip the counts and
    # consistency gates (false accept).
    for field_name, bad_value, message in (
        ("counts", 5, "'counts' must be an object"),
        ("panel", {"worker": 1}, "'panel' must be an array"),
        ("overflow", "not-a-list", "'overflow' must be an array"),
        ("discarded", 7, "'discarded' must be an array"),
    ):
        legacy_bad = _json.loads(_json.dumps(base_payload))
        del legacy_bad["schema_version"]
        legacy_bad[field_name] = bad_value
        result = validate_staging_file(
            stage(
                f"bad-{field_name.replace('_', '-')}-versionless",
                legacy_bad,
                base_md,
            ),
            hard=True,
        )
        check(
            f"v1 contract: mistyped {field_name!r} on a versionless "
            "current-shaped sidecar fails hard",
            not result.ok and any(message in e for e in result.errors),
        )

    # r4 F1: severity_calibration joins the versionless current-shape type
    # gates. A truthy mistyped value (e.g. the integer 5) previously passed
    # the validator and then crashed the summarizer's len-derived calibration
    # count (TypeError: object of type 'int' has no len()).
    legacy_bad_calib = _json.loads(_json.dumps(base_payload))
    del legacy_bad_calib["schema_version"]
    legacy_bad_calib["severity_calibration"] = 5
    result = validate_staging_file(
        stage("bad-severity-calibration-versionless", legacy_bad_calib, base_md),
        hard=True,
    )
    check(
        "v1 contract: mistyped severity_calibration on a versionless "
        "current-shaped sidecar fails hard",
        not result.ok
        and any("'severity_calibration' must be an array" in e for e in result.errors),
    )

    # r4 F14: explicit JSON null containers on versionless current shapes are
    # treated as ABSENT (pinning the compatibility choice): a legacy record
    # that encodes an omitted container as null still validates instead of
    # hitting the mistyped-container gate. Only non-null mistyped values
    # (string, int, object-for-array) are rejected.
    null_containers = _json.loads(_json.dumps(base_payload))
    del null_containers["schema_version"]
    for field_name in (
        "counts",
        "overflow",
        "discarded",
        "severity_calibration",
        "deduplication_groups",
        "soften_watchlist",
    ):
        null_containers[field_name] = None
    check(
        "v1 contract: explicit JSON null containers on a versionless "
        "current-shaped sidecar validate as absent",
        validate_staging_file(
            stage("null-containers-versionless", null_containers, base_md), hard=True
        ).ok,
    )

    # r5 F1 / r1 F3: the null-as-absent compatibility does NOT extend to
    # version-1 records. An explicit JSON null for a version-1 REQUIRED field
    # (container or scalar) must fail hard with the targeted null error
    # (pre-fix it bypassed both the required-field gate and the shared
    # null-as-absent helpers, so `"findings": null` validated clean and
    # skipped the pattern and conservation checks). The scalar fields are
    # covered too, pinning the r6 F8 delegation: if someone later adds a
    # scalar to the null-allowed exception list, these fixtures turn RED.
    for field_name in (
        "findings",
        "counts",
        "date",
        "review_type",
        "artifact_slug",
        "round",
    ):
        null_required = _json.loads(_json.dumps(base_payload))
        null_required[field_name] = None
        null_result = validate_staging_file(
            stage(
                f"null-required-{field_name.replace('_', '-')}-v1",
                null_required,
                base_md,
            ),
            hard=True,
        )
        check(
            f"v1 contract: explicit JSON null required field {field_name!r} "
            "fails hard (r5 F1; null-as-absent is versionless-only)",
            not null_result.ok
            and any(
                "must not be JSON null" in e and f"{field_name!r}" in e
                for e in null_result.errors
            )
            # r4 F5: the r5 F1 null gate must stay the single reporter for
            # explicit-null required fields; the F8 type gates must not
            # double-report (the None skip delegation stays pinned).
            and not any(
                f"{field_name!r} must be a string" in e
                for e in null_result.errors
            ),
        )

    # r6 F8 (RED): scalar and optional-field type gates for version-1
    # records. The negative fixtures below FAIL (error-absent) until the
    # Task 4 production gates exist; the two over-gating guards (absent
    # optional fields stay valid, round dual typing) must keep passing both
    # before and after those gates land.

    def _v1_copy() -> dict:
        return _json.loads(_json.dumps(base_payload))

    # Scalar required-field type gates.
    for field_name, bad_value, message in (
        ("date", 20260829, "must be a string"),
        ("date", "2026-8-9", "YYYY-MM-DD"),
        # r1 F1 RED fixture: `$` also matches before a trailing newline, so
        # this one string passed the old anchored regex (the only listed
        # case it accepted). The trailing-garbage case also pins the end
        # anchor (distinct value so the filename tag cannot collide).
        ("date", "2026-08-29\n", "YYYY-MM-DD"),
        ("date", "2099-12-31X", "YYYY-MM-DD"),
        # r3 F5 fixture: leading garbage pins the start anchor (the rows
        # above pin the end anchor); the derived filename tag "X2026082"
        # stays distinct from every sibling fixture.
        ("date", "X2026-08-29", "YYYY-MM-DD"),
        # r2 F4 RED fixture: fullwidth digits pin the ASCII-only [0-9]
        # class; the old `\d` class accepted Unicode decimal digits. The
        # derived filename tag stays distinct from every sibling fixture.
        ("date", "２０２６-08-29", "YYYY-MM-DD"),
        ("review_type", 7, "must be a string"),
        ("artifact_slug", [], "must be a string"),
        # v1-gate-trio fixtures: the enum-reason pair is covered by the F8
        # scalar type-gate family (the loop tuple widened); these mistyped
        # shapes must fail hard.
        ("selection_reason", 5, "must be a string"),
        ("selection_reason", [], "must be a string"),
        ("escalation_reason", 7, "must be a string"),
        # Optional version-1 fields: a PRESENT but mistyped value must fail;
        # explicit null is not the absent form for optional version-1 fields
        # (r5 F1 pinned required fields only — this is the optional gap).
        ("depth", [], "must be a string"),
        ("depth", None, "must be a string"),
        ("domains", "api", "must be a list"),
        ("domains", None, "must be a list"),
    ):
        mistyped = _v1_copy()
        mistyped[field_name] = bad_value
        if bad_value is None:
            value_tag = "null"
        elif isinstance(bad_value, str):
            value_tag = bad_value.replace("-", "")[:8] or "string"
        else:
            value_tag = type(bad_value).__name__
        result = validate_staging_file(
            stage(f"type-{field_name}-{value_tag}-v1", mistyped, base_md),
            hard=True,
        )
        check(
            f"v1 contract: mistyped {field_name!r} "
            f"({'JSON null' if bad_value is None else repr(bad_value)}) "
            "fails hard with a targeted type error",
            not result.ok
            and any(f"{field_name!r}" in e and message in e for e in result.errors),
        )

    # v1-gate-trio: `round` is documented dual-typed (string or integer;
    # SKILL.md contract table). Bool and float shapes must fail hard; bool
    # needs the explicit exclusion because True is an int subclass in Python.
    for bad_round in (True, 3.5):
        round_bad = _v1_copy()
        round_bad["round"] = bad_round
        round_result = validate_staging_file(
            stage(f"round-{type(bad_round).__name__}-v1", round_bad, base_md),
            hard=True,
        )
        check(
            f"v1 contract: round = {bad_round!r} fails hard "
            "(must be a string or integer)",
            not round_result.ok
            and any(
                "'round'" in e and "must be a string or integer" in e
                for e in round_result.errors
            ),
        )

    # Over-gating guard: absent optional fields stay valid.
    for field_name in ("depth", "domains"):
        absent = _v1_copy()
        del absent[field_name]
        check(
            f"v1 contract: absent optional {field_name!r} stays valid (over-gating guard)",
            validate_staging_file(
                stage(f"absent-{field_name}-v1", absent, base_md), hard=True
            ).ok,
        )

    # Over-gating guard: round keeps its dual int/string typing.
    for round_value in (3, "r3"):
        dual = _v1_copy()
        dual["round"] = round_value
        check(
            f"v1 contract: round = {round_value!r} stays valid (dual-typing guard)",
            validate_staging_file(
                stage(f"round-{type(round_value).__name__}-v1", dual, base_md),
                hard=True,
            ).ok,
        )

    # v1-gate-trio keep-valid guards beside the over-gating guards above:
    # the r5 F1 carve-out keeps null selection_reason/escalation_reason legal
    # even after the F8 loop widens to the pair (the None skip makes the null
    # gate the single reporter), and non-null enum strings pin the widened
    # type gate against over-gating legal values. These pass before and
    # after any gate changes; they pin legal forms, not gates.
    for field_name, keep_value, value_form in (
        ("selection_reason", None, "null"),
        ("escalation_reason", None, "null"),
        ("selection_reason", "focused-panel", "string"),
        ("escalation_reason", "user-escalated", "string"),
    ):
        keep_valid = _v1_copy()
        keep_valid[field_name] = keep_value
        check(
            f"v1 contract: {field_name} = {keep_value!r} stays valid "
            "(enum-reason keep-valid guard)",
            validate_staging_file(
                stage(
                    f"keep-valid-{field_name}-{value_form}-v1",
                    keep_valid,
                    base_md,
                ),
                hard=True,
            ).ok,
        )

    # r3 F2: example bullets in Comment/Analysis bodies (prose or fenced)
    # must NOT overwrite the finding's real parsed metadata. Pre-fix the
    # parser scanned the whole finding block last-match-wins, so an
    # illustrative Pattern bullet in the Comment body replaced the real one
    # and produced a false pattern-disagreement hard error.
    quoted_md = _version1_markdown()
    quoted_md = quoted_md.replace(
        "#### Comment",
        (
            "#### Comment\n"
            "An illustrative fenced example (must be ignored by the parser):\n"
            "```markdown\n"
            "- **Pattern**: quality#illustrative-example\n"
            "- **Blocking**: true\n"
            "```\n"
            "Prose quote of a triage bullet also lives here: its Triage bullet "
            "staged pending, and this sentence must not affect parsing.\n"
            "- **Triage**: dropped\n"
        ),
        1,
    )
    check(
        "v1 contract: quoted-bullet fixture injected after Comment heading",
        "quality#illustrative-example" in quoted_md
        and "- **Triage**: dropped" in quoted_md,
    )
    result = validate_staging_file(
        stage("quoted-bullets", base_payload, quoted_md), hard=True
    )
    check(
        "v1 contract: fenced and post-Comment example bullets do not overwrite parsed metadata",
        result.ok,
    )
    # r4 F8: assert the parser OUTPUT directly, not just overall validation
    # success: a legal triage value quoted post-Comment would keep validation
    # green even if the parser wrongly resumed metadata parsing after the
    # sub-heading. The readiness predicate consumes exactly these parsed
    # fields, so pin them: triage keeps the metadata-region value (pending,
    # not the post-Comment quoted "dropped"), blocking stays false, pattern
    # keeps the metadata-region value.
    parsed_quoted = parse_markdown_findings(quoted_md)
    check(
        "v1 contract: post-Comment prose bullet leaves parsed triage at its "
        "metadata-region value and blocking false (parser output, not just "
        "result.ok)",
        len(parsed_quoted) == 1
        and parsed_quoted[0].get("triage") == "pending"
        and parsed_quoted[0].get("blocking") is False
        and parsed_quoted[0].get("pattern") == "testing#weak-assertion",
    )
    # r4 F3: an unclosed fence opener inside one finding's Comment body must
    # not swallow the remaining findings (pre-fix the naive parity toggle
    # stayed on for the rest of the section, hiding a later blocking pending
    # finding from readiness). The High-severity finding comes first in the
    # Markdown, so its unclosed fence precedes the Medium finding's header.
    fence_f1 = _current_finding(id=1)
    fence_f2 = _current_finding(id=2, severity="High", blocking=True)
    unclosed_md = _current_findings_markdown([fence_f1, fence_f2]).replace(
        "#### Comment",
        "#### Comment\nAn unclosed fence example follows:\n```python\nx = 1\n",
        1,
    )
    assert unclosed_md.count("```") % 2 == 1, (
        "unclosed opener not injected; fixture defanged"
    )
    parsed_unclosed = parse_markdown_findings(unclosed_md)
    check(
        "fence fix: unclosed fence before a later finding still parses both findings",
        sorted(f["id"] for f in parsed_unclosed) == [1, 2],
    )
    check(
        "fence fix: unclosed fence cannot hide a blocking pending finding from readiness",
        is_review_ready(unclosed_md) is False,
    )
    unclosed_payload = _payload_with_findings([fence_f2, fence_f1])
    check(
        "fence fix: staging doc with an unclosed fence validates (conservation sees both findings)",
        validate_staging_file(
            stage("unclosed-fence", unclosed_payload, unclosed_md), hard=True
        ).ok,
    )
    # r5 F5: the fence-length comparison pinned directly. A four-backtick
    # opener containing an embedded three-backtick line plus a trailing
    # illustrative bullet stays open until the four-backtick close: the
    # shorter delimiter must NOT close the fence, and the in-fence bullet
    # must not overwrite the parsed metadata fields. Reverting the
    # length-aware close (length-blind parity) fails this check.
    fence_len_md = _version1_markdown().replace(
        "#### Comment",
        (
            "#### Comment\n"
            "A longer fence with an embedded shorter delimiter:\n"
            "````markdown\n"
            "```\n"
            "- **Pattern**: quality#fenced-overwrite\n"
            "- **Blocking**: true\n"
            "- **Triage**: dropped\n"
            "````\n"
        ),
        1,
    )
    parsed_len = parse_markdown_findings(fence_len_md)
    check(
        "fence fix: shorter embedded delimiter does not close a longer fence "
        "(parsed fields keep metadata-region values, r5 F5)",
        len(parsed_len) == 1
        and parsed_len[0].get("pattern") == "testing#weak-assertion"
        and parsed_len[0].get("blocking") is False
        and parsed_len[0].get("triage") == "pending",
    )
    check(
        "fence fix: longer-fence fixture validates hard",
        validate_staging_file(
            stage("fence-length", base_payload, fence_len_md), hard=True
        ).ok,
    )
    # r5 F8: a properly fenced example quoting the staging format (a
    # severity heading and a finding header inside the fence) must not inject
    # a phantom finding into the parse, split a phantom finding block, or
    # shift the enclosing severity. Pre-fix the structural-heading reset ran
    # before the fence check, so the fenced header-like lines created a
    # phantom finding whose block then failed the Comment/Analysis gate.
    fenced_heading_md = _version1_markdown().replace(
        "#### Comment",
        (
            "#### Comment\n"
            "The staging format quoted verbatim as an example:\n"
            "````markdown\n"
            "### Low\n"
            "\n"
            "#### F9. Example finding quoted inside a fenced example\n"
            "- **Pattern**: quality#fenced-example\n"
            "- **Blocking**: true\n"
            "````\n"
        ),
        1,
    )
    parsed_fh = parse_markdown_findings(fenced_heading_md)
    check(
        "fence fix: heading-like lines inside a closed fence inject no phantom finding (r5 F8)",
        [f.get("id") for f in parsed_fh] == [1]
        and parsed_fh[0].get("pattern") == "testing#weak-assertion",
    )
    check(
        "fence fix: fenced severity-like line does not shift the enclosing severity (r5 F8)",
        parsed_fh[0].get("severity") == "Medium",
    )
    check(
        "fence fix: fenced heading-like lines do not split a phantom finding block (r5 F8)",
        len(split_finding_blocks(fenced_heading_md)) == 1,
    )
    check(
        "fence fix: fenced-example staging doc validates hard (r5 F8)",
        validate_staging_file(
            stage("fenced-heading-example", base_payload, fenced_heading_md), hard=True
        ).ok,
    )
    # tilde-closed-example: a properly CLOSED tilde fence (~~~) quoting the
    # staging format (a finding header with a fake pattern inside the fence)
    # is treated as fenced content, not structure: no phantom finding is
    # injected and only the real finding counts. Tilde support exists today
    # but was pinned by no fixture (rg -c '~~~' was 0 before this task).
    tilde_closed_md = _current_findings_markdown([_current_finding(id=1)]).replace(
        "#### Comment",
        (
            "#### Comment\n"
            "The staging format quoted verbatim inside a tilde fence:\n"
            "~~~markdown\n"
            "#### F99. fake#y\n"
            "- **Pattern**: quality#tilde-example\n"
            "- **Blocking**: true\n"
            "~~~\n"
        ),
        1,
    )
    assert tilde_closed_md.count("~~~") == 2, (
        "tilde example not injected; fixture defanged"
    )
    parsed_tilde_closed = parse_markdown_findings(tilde_closed_md)
    check(
        "fence fix: closed tilde fence example injects no phantom finding "
        "(# tilde-closed-example)",
        [f.get("id") for f in parsed_tilde_closed] == [1],
    )
    check(
        "fence fix: staging doc with a closed tilde-fenced example validates hard "
        "(# tilde-closed-example)",
        validate_staging_file(
            stage("tilde-closed-example", _payload_with_findings([_current_finding(id=1)]), tilde_closed_md),
            hard=True,
        ).ok,
    )
    # tilde-unclosed-containment: an unclosed tilde fence opener inside one
    # finding's Comment must not swallow the remaining findings (tilde analog
    # of the r4 F3 containment arm above). The High-severity finding comes
    # first in the Markdown, so its unclosed tilde fence precedes the Medium
    # finding's header.
    tilde_f1 = _current_finding(id=1)
    tilde_f2 = _current_finding(id=2, severity="High", blocking=True)
    tilde_unclosed_md = _current_findings_markdown([tilde_f1, tilde_f2]).replace(
        "#### Comment",
        "#### Comment\nAn unclosed tilde fence example follows:\n~~~python\nx = 1\n",
        1,
    )
    assert tilde_unclosed_md.count("~~~") % 2 == 1, (
        "unclosed tilde opener not injected; fixture defanged"
    )
    _, tilde_unclosed_opener = classify_fence_lines(tilde_unclosed_md.splitlines())
    assert tilde_unclosed_opener is not None, (
        "tilde opener not tracked as a fence; fixture defanged"
    )
    parsed_tilde_unclosed = parse_markdown_findings(tilde_unclosed_md)
    check(
        "fence fix: unclosed tilde fence before a later finding still parses both "
        "findings (# tilde-unclosed-containment)",
        sorted(f["id"] for f in parsed_tilde_unclosed) == [1, 2],
    )
    check(
        "fence fix: unclosed tilde fence cannot hide a blocking pending finding from "
        "readiness (# tilde-unclosed-containment)",
        is_review_ready(tilde_unclosed_md) is False,
    )
    check(
        "fence fix: staging doc with an unclosed tilde fence validates (conservation "
        "sees both findings) (# tilde-unclosed-containment)",
        validate_staging_file(
            stage("tilde-unclosed-containment", _payload_with_findings([tilde_f2, tilde_f1]), tilde_unclosed_md),
            hard=True,
        ).ok,
    )
    # reset-axis-contract: the reset axis is selected solely by the
    # keyword-only predicate — no half-configured mode exists, and a
    # positional second argument is rejected at call time.
    rac1_events, rac1_unclosed = classify_fence_lines(["~~~", "### High", "x"])
    check(
        "fence fix: no predicate keeps fenced headings as content and the "
        "opener unclosed (# reset-axis-contract)",
        rac1_events
        == [("fence_opener", None), ("in_fence_content", None), ("in_fence_content", None)]
        and rac1_unclosed == 0,
    )
    rac2_events, rac2_unclosed = classify_fence_lines(
        ["~~~", "#### F2.", "y"],
        is_reset_heading=lambda line: re.match(r"^####\s+F\d+\.", line) is not None,
    )
    check(
        "fence fix: a predicate alone activates heading reset (# reset-axis-contract)",
        rac2_events == [("fence_opener", None), ("heading", "#### F2."), ("ordinary", "y")]
        and rac2_unclosed is None,
    )
    try:
        classify_fence_lines(["~~~"], lambda line: True)
        rac_positional_rejected = False
    except TypeError:
        rac_positional_rejected = True
    check(
        "fence fix: positional second argument is rejected (# reset-axis-contract)",
        rac_positional_rejected,
    )
    # close-rule-in-reset-mode: the char+bare close rule also holds inside
    # the heading-reset pass (the same classifier serves both modes), and the
    # heading reset clears the fence state so a later fence line can reopen.
    # Characterization: GREEN today; pins that a future split of the reset
    # pass onto a different close path (or loss of the reset state clear)
    # fails an assertion instead of silently changing phantom promotion.
    crrm_events, crrm_unclosed = classify_fence_lines(
        ["```", "~~~", "#### F2.", "```", "x"],
        is_reset_heading=lambda line: re.match(r"^####\s+F\d+\.", line) is not None,
    )
    check(
        "fence fix: same-char bare close rule holds in heading-reset mode and a "
        "reset heading lets a later fence line reopen "
        "(# close-rule-in-reset-mode)",
        [e[0] for e in crrm_events]
        == [
            "fence_opener",
            "in_fence_content",
            "heading",
            "fence_opener",
            "in_fence_content",
        ]
        and crrm_unclosed == 3,
    )

    # cross-char-close: a fence must close only on a run of the SAME
    # delimiter character as the opener. RED under today's char-blind
    # length-only close rule; GREEN after the char-match + bare close rule
    # lands. Behavioral fixtures compare event KINDS plus unclosed_opener
    # only (payload-agnostic); full-tuple comparison is reserved for the
    # reset-axis-contract checks after the payload drop.
    cc1_events, cc1_unclosed = classify_fence_lines(
        ["```", "x = 1", "~~~", "- **Blocking**: true", "```"]
    )
    cc2_events, cc2_unclosed = classify_fence_lines(
        ["~~~", "```", "text", "~~~"]
    )
    cc3_events, cc3_unclosed = classify_fence_lines(
        ["```", "```~~~", "```"]
    )
    check(
        "fence fix: a bare run of the wrong delimiter character never closes "
        "a fence, whatever its length (cc1) (# cross-char-close)",
        [e[0] for e in cc1_events]
        == [
            "fence_opener",
            "in_fence_content",
            "in_fence_content",
            "in_fence_content",
            "fence_close",
        ]
        and cc1_unclosed is None,
    )
    check(
        "fence fix: a backtick run never closes a tilde fence (cc2) "
        "(# cross-char-close)",
        [e[0] for e in cc2_events]
        == ["fence_opener", "in_fence_content", "in_fence_content", "fence_close"]
        and cc2_unclosed is None,
    )
    check(
        "fence fix: a mixed-character line never closes a fence (cc3) "
        "(# cross-char-close)",
        [e[0] for e in cc3_events]
        == ["fence_opener", "in_fence_content", "fence_close"]
        and cc3_unclosed is None,
    )
    # bare-close-info-string: a fence closes only on a BARE delimiter run;
    # info strings and other non-bare suffixes keep the line fenced content.
    # RED today on all three arms.
    bc1_events, bc1_unclosed = classify_fence_lines(
        ["```", "intro", "```python", "- **Blocking**: true", "```"]
    )
    bc2_events, bc2_unclosed = classify_fence_lines(["```", "~~~x", "```"])
    bc3_events, bc3_unclosed = classify_fence_lines(["~~~", "~~~x", "~~~"])
    check(
        "fence fix: an info-string delimiter line stays fence content until "
        "the final bare close (bc1) (# bare-close-info-string)",
        [e[0] for e in bc1_events]
        == [
            "fence_opener",
            "in_fence_content",
            "in_fence_content",
            "in_fence_content",
            "fence_close",
        ]
        and bc1_unclosed is None,
    )
    check(
        "fence fix: a wrong-character run with an info-string suffix never "
        "closes a backtick fence (bc2) (# bare-close-info-string)",
        [e[0] for e in bc2_events]
        == ["fence_opener", "in_fence_content", "fence_close"]
        and bc2_unclosed is None,
    )
    check(
        "fence fix: a non-bare run never closes a tilde fence (bc3) "
        "(# bare-close-info-string)",
        [e[0] for e in bc3_events]
        == ["fence_opener", "in_fence_content", "fence_close"]
        and bc3_unclosed is None,
    )
    # bare-close-keep-valid: the close rules that stay legal before and
    # after the tightening. GREEN today; one check per arm (shared slug, the
    # cluster's multi-check-per-slug idiom) so a failing arm is named by its
    # own FAIL line.
    kv1_events, kv1_unclosed = classify_fence_lines(
        ["~~~~", "x", "```", "y", "~~~~~~"]
    )
    check(
        "fence fix: a bare equal-or-longer run of the same character closes "
        "(# bare-close-keep-valid)",
        [e[0] for e in kv1_events]
        == [
            "fence_opener",
            "in_fence_content",
            "in_fence_content",
            "in_fence_content",
            "fence_close",
        ]
        and kv1_unclosed is None,
    )
    kv2_events, kv2_unclosed = classify_fence_lines(["~~~~", "~~~"])
    check(
        "fence fix: a shorter bare same-character run stays fence content "
        "(length rule kept) (# bare-close-keep-valid)",
        [e[0] for e in kv2_events] == ["fence_opener", "in_fence_content"]
        and kv2_unclosed == 0,
    )
    kv3_events, kv3_unclosed = classify_fence_lines(["~~~", "~~~ "])
    check(
        "fence fix: trailing whitespace on a bare close line still closes "
        "(# bare-close-keep-valid)",
        [e[0] for e in kv3_events] == ["fence_opener", "fence_close"]
        and kv3_unclosed is None,
    )
    kv4_events, kv4_unclosed = classify_fence_lines(["~~~", "x", "  ~~~"])
    check(
        "fence fix: leading whitespace on a bare close line still closes "
        "(# bare-close-keep-valid)",
        [e[0] for e in kv4_events]
        == ["fence_opener", "in_fence_content", "fence_close"]
        and kv4_unclosed is None,
    )
    kv5_events, kv5_unclosed = classify_fence_lines(["```python"])
    check(
        "fence fix: a top-level info-string delimiter line still opens a "
        "fence (# bare-close-keep-valid)",
        [e[0] for e in kv5_events] == ["fence_opener"]
        and kv5_unclosed == 0,
    )
    # silent-misparse-metadata-region: a fenced example in the metadata
    # region whose in-example Blocking bullet sits after a bare ~~~ line.
    # Today the bare ~~~ closes the backtick fence (cross-char, length-only)
    # and the true bullet overwrites F1's real blocking=false, silently
    # flipping readiness. After the fix the whole example stays fenced
    # content. RED today.
    sm_f1 = _current_finding(id=1, severity="High", blocking=False)
    silent_md = _current_findings_markdown([sm_f1]).replace(
        "#### Comment",
        (
            "```\n"
            "text\n"
            "~~~\n"
            "- **Blocking**: true\n"
            "```\n"
            "#### Comment"
        ),
        1,
    )
    assert "~~~" in silent_md and "- **Blocking**: true" in silent_md, (
        "fenced example not injected; fixture defanged"
    )
    parsed_silent = parse_markdown_findings(silent_md)
    check(
        "fence fix: in-example bullet after a bare cross-character closer "
        "cannot overwrite the real blocking value or flip readiness "
        "(# silent-misparse-metadata-region)",
        len(parsed_silent) == 1
        and parsed_silent[0].get("blocking") is False
        and is_review_ready(silent_md) is True,
    )
    # Unclosed arm of the same residual: the same injected example WITHOUT
    # its terminating bare ``` line. The fallback must NOT recover the
    # in-example Blocking bullet (documented fail-open direction), so the
    # doc keeps F1's real pre-opener blocking=false (the post-opener true
    # bullet stays unrecovered) and reads as ready. Pins the residual
    # so a future fallback change that recovers fenced bullets fails here
    # instead of silently flipping readiness.
    silent_unclosed_md = silent_md.replace(
        "- **Blocking**: true\n```\n",
        "- **Blocking**: true\n",
        1,
    )
    assert "```" in silent_unclosed_md, "fixture defanged: no fence left"
    _, silent_unclosed_opener = classify_fence_lines(
        silent_unclosed_md.splitlines()
    )
    assert silent_unclosed_opener is not None, (
        "fixture defanged: the injected example still closes its fence"
    )
    parsed_silent_unclosed = parse_markdown_findings(silent_unclosed_md)
    check(
        "fence fix: an unclosed example fence leaves the in-example bullet "
        "unrecovered (fail-open residual pinned): blocking stays false and "
        "readiness stays true (# silent-misparse-metadata-region)",
        len(parsed_silent_unclosed) == 1
        and parsed_silent_unclosed[0].get("blocking") is False
        and is_review_ready(silent_unclosed_md) is True,
    )
    # phantom-f99-info-string: a properly closed fenced example in the
    # Comment body quoting an inner ```python line and a quoted #### F99.
    # header with field bullets. Today the inner ```python line closes the
    # outer fence, the quoted header becomes a live finding (ids [1, 99],
    # 2 blocks). After the fix the snippet stays fenced content. Presence
    # asserts only: fence-marker parity can never hold for this shape (the
    # fixture contributes exactly three fence-pattern lines). RED today.
    ph_f1 = _current_finding(id=1, severity="High", blocking=True)
    phantom_md = _current_findings_markdown([ph_f1]).replace(
        "#### Comment",
        (
            "#### Comment\n"
            "The staging format quoted verbatim inside a code fence:\n"
            "```\n"
            "```python\n"
            "#### F99. fake#y\n"
            "- **Pattern**: quality#phantom-example\n"
            "- **Blocking**: true\n"
            "```\n"
        ),
        1,
    )
    assert "```python" in phantom_md and "#### F99." in phantom_md, (
        "fenced example not injected; fixture defanged"
    )
    check(
        "fence fix: an inner info-string line in a properly closed example "
        "stays fence content; no phantom F99 finding or block "
        "(# phantom-f99-info-string)",
        [f.get("id") for f in parse_markdown_findings(phantom_md)] == [1]
        and len(split_finding_blocks(phantom_md)) == 1,
    )

    # fallback-preserves-fenced-example (r6 F3): a properly fenced
    # staging-format example (#### F99. inside the fence) in one finding's
    # Comment, FOLLOWED by a stray unclosed fence opener inside a LATER real
    # finding's Comment body (opener placement pinned: in-Comment, not top
    # level, r4 F3) and a subsequent real finding. The content-preserving
    # first pass classifies all of this correctly, but the fence never closes,
    # so the pre-fix full-discard fallback re-scanned the WHOLE section with
    # heading resets and the example's #### F99. line became a phantom finding
    # (a conservation error about content the first pass correctly ignored).
    # The partial fallback keeps the pre-opener first-pass results so F99
    # never surfaces.
    fb_f1 = _current_finding(id=1, severity="High", blocking=True)
    fb_f2 = _current_finding(id=2)
    fb_f3 = _current_finding(id=3, severity="Low")
    fallback_md = _current_findings_markdown([fb_f1, fb_f2, fb_f3])
    fallback_md = fallback_md.replace(
        "#### Comment",
        (
            "#### Comment\n"
            "The staging format quoted verbatim as an example:\n"
            "```markdown\n"
            "#### F99. fake#y\n"
            "- **Pattern**: quality#fenced-example\n"
            "- **Blocking**: true\n"
            "```\n"
        ),
        1,
    ).replace(
        "#### Comment\nConcrete claim for finding 2:",
        (
            "#### Comment\n"
            "An unclosed fence opener follows:\n"
            "```python\n"
            "x = 1\n"
            "Concrete claim for finding 2:"
        ),
        1,
    )
    assert fallback_md.count("```") % 2 == 1, (
        "unclosed opener not injected; fixture defanged"
    )
    assert "#### F99." in fallback_md, (
        "fenced example not injected; fixture defanged"
    )
    parsed_fallback = parse_markdown_findings(fallback_md)
    check(
        "fence fix: fallback keeps the fenced example as content; no phantom "
        "F99 finding, exactly the real findings parse "
        "(# fallback-preserves-fenced-example)",
        [f.get("id") for f in parsed_fallback] == [1, 2, 3],
    )
    fallback_blocks = split_finding_blocks(fallback_md)
    check(
        "fence fix: fallback block split returns exactly the real finding "
        "blocks, none starting at the F99 example header "
        "(# fallback-preserves-fenced-example)",
        len(fallback_blocks) == 3
        and not any(block.startswith("#### F99.") for block in fallback_blocks),
    )
    check(
        "fence fix: staging doc with a fenced example plus a later unclosed "
        "fence validates hard with no phantom-finding conservation error "
        "(# fallback-preserves-fenced-example)",
        validate_staging_file(
            stage(
                "fallback-preserves-fenced-example",
                _payload_with_findings([fb_f1, fb_f2, fb_f3]),
                fallback_md,
            ),
            hard=True,
        ).ok,
    )

    # phantom-unclosed-fallback (GREEN today, must stay green): an UNCLOSED
    # outer fence in a finding's Comment body quoting the staging format (a
    # ``### Low`` severity-group heading, a ``#### F7.`` finding header, and
    # field bullets). Under the r4 F3 / r6 F3 partial fallback the unclosed
    # suffix is re-classified with the parser's reset predicate, so the quoted
    # ``### Low`` and ``#### F7.`` lines reset the fence and F7 is PROMOTED to
    # a parsed finding carrying the quoted Low severity label — the documented
    # fallback promotion residual. Pin it: ids == [1, 7] with F7's severity
    # exactly "Low" (not the enclosing group's, not None).
    pu_f1 = _current_finding(id=1)
    phantom_unclosed_md = _current_findings_markdown([pu_f1]).replace(
        "#### Comment",
        (
            "#### Comment\n"
            "The staging format quoted verbatim as an example:\n"
            "```markdown\n"
            "### Low\n"
            "\n"
            "#### F7. Example finding quoted inside an unclosed fence\n"
            "- **Pattern**: quality#phantom-unclosed\n"
            "- **Blocking**: true\n"
        ),
        1,
    )
    _, phantom_unclosed_opener = classify_fence_lines(
        phantom_unclosed_md.splitlines()
    )
    assert phantom_unclosed_opener is not None, (
        "unclosed outer fence not injected; fixture defanged"
    )
    assert "#### F7." in phantom_unclosed_md and "### Low" in phantom_unclosed_md, (
        "quoted staging-format example not injected; fixture defanged"
    )
    parsed_phantom_unclosed = parse_markdown_findings(phantom_unclosed_md)
    check(
        "fence fix: unclosed fence quoting a staging example promotes the "
        "quoted F7 to a parsed finding with the quoted Low severity (r4 F3 / "
        "r6 F3 fallback promotion residual, ids [1, 7]) "
        "(# phantom-unclosed-fallback)",
        [f.get("id") for f in parsed_phantom_unclosed] == [1, 7]
        and next(
            (
                f.get("severity")
                for f in parsed_phantom_unclosed
                if f.get("id") == 7
            ),
            None,
        )
        == "Low",
    )

    # fallback-same-severity-group (r6 F3): the fenced example, the stray
    # unclosed fence opener (in a real finding's Comment, AFTER that finding's
    # Blocking bullet), and a later real finding, all inside the SAME severity
    # group (### Medium). A stray-fence-only same-group layout is GREEN today
    # (the heading-reset re-scan re-reads the ### Medium label before the
    # later finding), so the fenced example is load-bearing: under the
    # full-discard fallback its #### F99. line leaks in as a phantom
    # finding/block. The partial fallback must seed the reset region with the
    # first pass's state at the opener, so the straddling finding keeps its
    # pre-opener Blocking bullet (flushed once, not lost) and the later
    # finding parses with its true severity (not severity: None). The
    # example keeps only the header line so the straddling-block assertion
    # cannot be satisfied by the phantom block's content. The block checks
    # pin "no block STARTS at the F99 header": substring containment is
    # unsatisfiable because the fenced example text legitimately remains
    # inside the enclosing finding's block (r5 F8 keeps fenced examples in
    # the block they quote).
    sg_f1 = _current_finding(id=1)
    sg_f2 = _current_finding(id=2, blocking=True)
    sg_f3 = _current_finding(id=3)
    same_group_md = _current_findings_markdown([sg_f1, sg_f2, sg_f3])
    same_group_md = same_group_md.replace(
        "#### Comment",
        (
            "#### Comment\n"
            "The staging format quoted verbatim as an example:\n"
            "```markdown\n"
            "#### F99. fake#y\n"
            "```\n"
        ),
        1,
    ).replace(
        "#### Comment\nConcrete claim for finding 2:",
        (
            "#### Comment\n"
            "An unclosed fence opener follows (after this finding's Blocking "
            "bullet above):\n```python\nx = 1\nConcrete claim for finding 2:"
        ),
        1,
    )
    # Post-opener poison (r2 F4): this assert pins that post-opener lines
    # classify as in_fence_content (skipped) until the next reset heading, so
    # the poison bullet never lands in parsed metadata. The seeded
    # metadata-region flag is carried into the reset scan only for invariant
    # fidelity; no reachable path reads it for this assertion, because an
    # ordinary line in the reset region is read only after a finding header
    # (which re-derives the flag as True), a generic #### sub-heading (which
    # sets it False), or a fence-close (cur stays None, so lines skip). The
    # live seed is cur_severity, pinned by the separate severity-label assert
    # below.
    same_group_md = same_group_md.replace(
        "Concrete claim for finding 2:",
        "- **Pattern**: wrong#post-opener\nConcrete claim for finding 2:",
        1,
    )
    assert same_group_md.count("```") % 2 == 1, (
        "unclosed opener not injected; fixture defanged"
    )
    assert "#### F99." in same_group_md, (
        "fenced example not injected; fixture defanged"
    )
    parsed_same_group = parse_markdown_findings(same_group_md)
    check(
        "fence fix: same-group fallback parse yields exactly the real "
        "findings, no phantom F99 (# fallback-same-severity-group)",
        [f.get("id") for f in parsed_same_group] == [1, 2, 3],
    )
    sg_by_id = {f.get("id"): f for f in parsed_same_group}
    check(
        "fence fix: straddling finding keeps its pre-opener Blocking bullet "
        "(flushed once, not lost, not double-appended) and the later "
        "same-group finding parses with its true severity label, not None "
        "(# fallback-same-severity-group)",
        sg_by_id.get(2, {}).get("blocking") is True
        and sum(1 for f in parsed_same_group if f.get("id") == 2) == 1
        and sg_by_id.get(3, {}).get("severity") == "Medium",
    )
    check(
        "fence fix: post-opener poisoned Pattern bullet is not recovered into "
        "the straddling finding (# fallback-same-severity-group)",
        sg_by_id.get(2, {}).get("pattern") != "wrong#post-opener",
    )
    sg_blocks = split_finding_blocks(same_group_md)
    check(
        "fence fix: same-group block split keeps the straddling finding's "
        "pre-opener metadata bullet and the later finding as its own block, "
        "with no phantom F99 block (# fallback-same-severity-group)",
        len(sg_blocks) == 3
        and not any(block.startswith("#### F99.") for block in sg_blocks)
        and f"- **Blocking**: {'true' if sg_f2['blocking'] else 'false'}"
        in sg_blocks[1],
    )
    check(
        "fence fix: same-group staging doc validates hard with no "
        "conservation error (# fallback-same-severity-group)",
        validate_staging_file(
            stage(
                "fallback-same-severity-group",
                _payload_with_findings([sg_f1, sg_f2, sg_f3]),
                same_group_md,
            ),
            hard=True,
        ).ok,
    )

    # Negative twin: the same dashed illustrative bullets placed BETWEEN the
    # finding header and the first Comment sub-heading are real metadata
    # region and DO overwrite (pinning the parser's scoping boundary).
    metadata_region_md = _version1_markdown().replace(
        "- **Blocking**: false\n- **Pattern**: testing#weak-assertion",
        (
            "- **Blocking**: false\n"
            "- **Pattern**: testing#weak-assertion\n"
            "- **Pattern**: quality#illustrative-example\n"
            "- **Triage**: dropped"
        ),
        1,
    )
    check(
        "v1 contract: metadata-region fixture injected",
        "quality#illustrative-example" in metadata_region_md,
    )
    result = validate_staging_file(
        stage("metadata-region-overwrite", base_payload, metadata_region_md), hard=True
    )
    check(
        "v1 contract: a dashed bullet inside the metadata region still overwrites parsed fields",
        not result.ok,
    )

    # Simplification: canonical simplification#shrink passes while the
    # colon-delimited body tag stays presentation prose (never the Pattern ID).
    sim_md = _version1_markdown(pattern="simplification#shrink").replace(
        "#### Comment",
        "shrink: presentation body tag stays prose.\n#### Comment",
        1,
    )
    sim_payload = _version1_payload(pattern="simplification#shrink")
    result = validate_staging_file(stage("simplification", sim_payload, sim_md), hard=True)
    check(
        "v1 contract: canonical simplification#shrink passes; colon body tag stays prose",
        result.ok,
    )
    colon_payload = _version1_payload(pattern="shrink:")
    result = validate_staging_file(
        stage("simplification-colon", colon_payload, sim_md), hard=True
    )
    check(
        "v1 contract: colon-delimited shrink: tag is not a valid sidecar Pattern ID",
        not result.ok and any("pattern" in e.lower() for e in result.errors),
    )

    # Schema classification: versionless payloads are legacy and must not be
    # held to the version-1 contract.
    check(
        "v1 contract: schema classifier classify_sidecar_schema is exported",
        callable(classify_sidecar_schema),
    )
    legacy_payload = _json.loads(_json.dumps(base_payload))
    del legacy_payload["schema_version"]
    check(
        "v1 contract: versionless payload (schema_version absent) still passes hard",
        validate_staging_file(stage("unversioned", legacy_payload, base_md), hard=True).ok,
    )
    legacy_minimal = _json.loads(_json.dumps(legacy_payload))
    for field_name in V1_OPTIONAL_TOP_LEVEL_FIELDS + (
        "triage_outcomes",
        "soften_watchlist",
        "artifact_slug",
    ):
        legacy_minimal.pop(field_name, None)
    check(
        "v1 contract: versionless payload is not required to carry version-1 fields",
        validate_staging_file(stage("unversioned-minimal", legacy_minimal, base_md), hard=True).ok,
    )
    check(
        "v1 contract: classifier labels version-1 payload current",
        "current" in str(classify_sidecar_schema(base_payload)),
    )
    check(
        "v1 contract: classifier labels versionless payload legacy",
        "legacy" in str(classify_sidecar_schema(legacy_payload)),
    )

    # Explicit unsupported versions (F1/F7): an explicit ``null`` (presence,
    # not value) and an explicit future version (2) are both ``unsupported``,
    # never legacy compatibility input, and fail hard with a targeted error.
    for name, bad_version in (("null", None), ("two", 2)):
        unsupported = _json.loads(_json.dumps(base_payload))
        unsupported["schema_version"] = bad_version
        result = validate_staging_file(
            stage(f"unsupported-{name}", unsupported, base_md), hard=True
        )
        check(
            f"v1 contract: explicit schema_version {bad_version!r} classifies "
            "unsupported and fails hard",
            not result.ok
            and classify_sidecar_schema(unsupported) == "unsupported"
            and any("unsupported" in e for e in result.errors),
        )

    # Required-field enforcement: every documented required field present
    # passes (the ok case); any missing required field fails hard with a
    # targeted error naming the field. schema_version is excluded (its absence
    # means legacy, not a version-1 error; see the legacy checks above).
    for field_name in V1_REQUIRED_TOP_LEVEL_FIELDS:
        if field_name == "schema_version":
            continue
        variant = _json.loads(_json.dumps(base_payload))
        del variant[field_name]
        result = validate_staging_file(
            stage(f"missing-{field_name}", variant, base_md), hard=True
        )
        check(
            f"v1 contract: missing required field {field_name} fails hard",
            not result.ok and any(field_name in e for e in result.errors),
        )

    # r6 F1: sidecar blocking true paired with an unparseable Markdown
    # Blocking value (bullet omitted, or fenced inside the metadata region)
    # must fail hard — pre-fix both the hard gate and is_review_ready failed
    # open on exactly the unresolved blocking finding they exist to hold.
    blocking_payload = _json.loads(_json.dumps(base_payload))
    blocking_payload["findings"][0]["blocking"] = True
    blocking_payload["findings"][0]["triage"] = "pending"
    for name, mutated_md in (
        (
            "omitted",
            _version1_markdown().replace("- **Blocking**: false\n", "", 1),
        ),
        (
            "fenced",
            _version1_markdown().replace(
                "- **Blocking**: false",
                "```\n- **Blocking**: false\n```",
                1,
            ),
        ),
    ):
        result = validate_staging_file(
            stage(f"r6-f1-blocking-{name}", blocking_payload, mutated_md),
            hard=True,
        )
        check(
            f"v1 contract: sidecar blocking true with {name} Markdown Blocking "
            "bullet fails hard (r6 F1)",
            not result.ok
            and any(
                "no parseable Blocking value" in e for e in result.errors
            ),
        )
    # Positive twin: the same doc with the Blocking bullet present and
    # matching (blocking true on both sides) still passes hard.
    matching_md = _version1_markdown().replace(
        "- **Blocking**: false", "- **Blocking**: true", 1
    )
    check(
        "v1 contract: sidecar blocking true with a matching Markdown Blocking "
        "bullet passes hard (r6 F1 positive twin)",
        validate_staging_file(
            stage("r6-f1-blocking-matching", blocking_payload, matching_md),
            hard=True,
        ).ok,
    )

    # r6 F2: a non-dict findings entry must produce the targeted
    # finding-must-be-an-object error with no AttributeError traceback from
    # the order check's sort (assert via the returned result, which a crash
    # would prevent).
    nondict_payload = _json.loads(_json.dumps(base_payload))
    nondict_payload["findings"].append("not-an-object")
    result = validate_staging_file(
        stage("r6-f2-nondict-finding", nondict_payload, base_md), hard=True
    )
    check(
        "v1 contract: string findings entry yields the targeted object error, "
        "not an order-check crash (r6 F2)",
        not result.ok
        and any(e == "current finding must be an object" for e in result.errors),
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
            ("source_rfc_cli", _selftest_source_rfc_cli),
            ("source_doc_cli", _selftest_source_doc_cli),
            ("discarded_header_skip", _selftest_discarded_header_skip),
            ("versioned_schema_and_patterns", _selftest_versioned_schema_and_patterns),
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
    parser.add_argument(
        "--source-rfc",
        metavar="PATH",
        help=(
            "Reviewed RFC file. Recompute its SHA-256 digest and compare to "
            "sidecar.source_digest; fail hard on mismatch (stale review after "
            "a fold). RFC reviews only (source_kind=rfc). The digest recipe is "
            "byte-identical to --source-plan; this flag exists so the sidecar's "
            "source_kind is type-checked rather than asserted in prose."
        ),
    )
    parser.add_argument(
        "--source-doc",
        metavar="PATH",
        help=(
            "Reviewed generic document file (source_kind=document; e.g. "
            "Confluence/document reviews). Recompute its SHA-256 digest and "
            "compare to sidecar.source_digest; fail hard on mismatch (stale "
            "review after a fold). The digest recipe is byte-identical to "
            "--source-plan; this flag exists so the sidecar's source_kind is "
            "type-checked rather than asserted in prose."
        ),
    )
    args = parser.parse_args(argv)

    # r5 F9: an empty-string source-flag value must fail LOUDLY. The routing
    # below uses truthiness, so an empty expansion (e.g. a shell wrapper
    # invoking the flag with an unset variable) was silently treated as "flag
    # not supplied", disabling the stale-digest freshness gate with exit 0.
    for flag_name, flag_value in (
        ("--source-plan", args.source_plan),
        ("--source-rfc", args.source_rfc),
        ("--source-doc", args.source_doc),
    ):
        if flag_value is not None and not flag_value.strip():
            parser.error(
                f"{flag_name} value must not be empty; an empty value would "
                "silently skip the stale-digest gate (unset shell variable?)"
            )

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
    source_flag_name: str | None = None  # for the stale-digest error hint
    supplied_source_flags = [
        flag
        for flag in (args.source_plan, args.source_rfc, args.source_doc)
        if flag
    ]
    if len(supplied_source_flags) > 1:
        parser.error(
            "--source-plan, --source-rfc, and --source-doc are mutually "
            "exclusive"
        )
    if args.source_plan:
        source_kind = "plan"
        source_path = Path(args.source_plan).expanduser().resolve()
        source_flag_name = "--source-plan"
    elif args.source_rfc:
        # --source-rfc: RFC reviews. The digest recipe is byte-identical to
        # --source-plan (plain SHA-256 of the file bytes); a separate flag keeps
        # the sidecar's source_kind type-checked against the flag used.
        source_kind = "rfc"
        source_path = Path(args.source_rfc).expanduser().resolve()
        source_flag_name = "--source-rfc"
    elif args.source_doc:
        # --source-doc (r4 F4): generic document reviews. Same recipe and
        # rationale as --source-rfc; without this flag a document-kind sidecar
        # could never receive a digest freshness check via the CLI.
        source_kind = "document"
        source_path = Path(args.source_doc).expanduser().resolve()
        source_flag_name = "--source-doc"

    if source_kind is not None:
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
        expected_digest = compute_source_digest(source_kind, source_bytes)
        # Stash the path so the stale-digest error can name it (F7: an agent
        # that points the source flag at the wrong file gets an actionable hint
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
            # agent that pointed the source flag at the wrong file (e.g. the
            # staging doc instead of the plan/rfc) gets an actionable hint (F7).
            if (
                source_flag_name
                and _SOURCE_PATH_FOR_ERROR
                and "source_digest is stale" in error
            ):
                error = (
                    f"{error}; or {source_flag_name} points at the wrong file "
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
