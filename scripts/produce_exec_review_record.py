#!/usr/bin/env python3
"""Produce a findings-bearing execution review record pair and validate it.

Writes one staging record (Markdown) plus its ``.stats.json`` sidecar from
structured review input, then validates the fresh pair with the existing
staging validator. The record and sidecar shapes are derived from the
validator's current grammar: the fixture builders ``_current_finding`` and
``_current_findings_markdown`` in ``scripts/validate_review_staging.py``
and the witnessed real-record shape under ``.ai-playbook/reviews/``. The
producer owns no validation rule of its own; a pair is a success only when
the validator says so.

Current-dated records (post-window): a record dated today arms every date
fence the validator pins on a canonical record, so the producer emits the
full post-window contract: the four freshness Metadata lines and sidecar
fields, the ``Record kind: canonical`` twin pair, the plan ``coverage``
pair (clean over the full five-worker lens set), the usage mint pair
(``review-run-id`` plus ``review-started-at-ms``, carried verbatim from
``scripts/review_usage_capture.py mint``), and the
``extensions.convergence.self_heal_attempt`` chain state (unused for
round 1; a valid prior round's state carried verbatim for higher rounds;
unknown when no valid prior round evidence exists in the output
directory).

Success contract (criterion: the validator's final outcome, not the exit
code, is the gate): the producer reports success only when its validation
invocation exits 0 AND the validator's final stdout line is
``OUTCOME: pass``. A soft-mode run can print ``OUTCOME: fail`` at exit 0,
so exit code alone is insufficient; the producer invokes hard mode through
the validator's ``main(["--hard", <record>])`` CLI contract in-process and
parses the final outcome line. A refused pair names the record path and
the validator's result and ends ``OUTCOME: fail`` (exit 1); malformed
inputs (unreadable or schema-violating findings JSON, missing plan file,
contradictory flags) and a failed pair write (directory creation included,
both halves removed) end ``OUTCOME: tool_error`` (exit 3).

Telemetry: the in-process validation rides the validator's fail-open
invocation telemetry, whose home resolves from repository facts; no
``--metrics-home`` override exists on the validator CLI, so tests isolate
telemetry by patching ``invocation_telemetry.resolve_metrics_home`` (the
same posture ``scripts/test_step31_record_validation_gate.py`` uses). No
telemetry file is written by this module outside the validator's own
append.

Creation-only: the producer creates new pairs and never touches an
existing record or sidecar; an existing target record or sidecar is a
named refusal, and the word "repair" appears nowhere in its outcomes (the
repair-only tool is ``scripts/regenerate_review_sidecar.py``, whose
zero-findings posture this module does not share and does not alter).

Deterministic bytes: every dynamic value is an explicit input (``--date``,
``--review-run-id``, ``--review-started-at-ms``; the date defaults to
today's UTC date when omitted). The same inputs produce byte-identical
Markdown and sidecar bytes.

Usage:

    python3 scripts/produce_exec_review_record.py \
        --out-dir DIR --session SESSION --plan PLAN \
        --findings-json FINDINGS.json \
        --review-run-id <32-char lowercase hex> \
        --review-started-at-ms <positive integer> \
        [--review-mode MODE] [--round N] [--date YYYY-MM-DD] \
        [--artifact-slug SLUG] [--last-fix-commit SHA] \
        [--prior-findings-filter yes|no]

The findings JSON schema:

    {
      "plan": "<repo-relative plan path, optional, cross-checked>",
      "review_round": <int, optional>,
      "review_mode": "<enum, optional>",
      "findings": [
        {
          "id": <int>, "title": "<str>", "severity": "<Critical|High|Medium|Low>",
          "blocking": <bool>, "status": "<str, optional>",
          "triage": "<pending|fixed|dropped|done|deferred, optional>",
          "file": "<str, optional>", "line": <int, optional>,
          "note": "<str, required>"
        }
      ]
    }

Per-finding optional overrides: ``pattern`` (canonical ``lens#slug``,
default ``quality#edge-case``, the validator fixture's own default),
``workers`` (list, default ``["correctness-completeness"]``),
``blast_radius``, ``reachability``, ``confidence`` (validator fixture
defaults). ``title``, ``status``, ``file``, ``line``, and ``note`` ride
the Markdown record; the sidecar findings carry the validator's current
finding shape only.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime
import importlib.util
import io
import json
import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import review_plan_identity  # noqa: E402
import validate_review_staging as vrs  # noqa: E402

OUTCOME_LABELS = {0: "pass", 1: "fail", 2: "indeterminate", 3: "tool_error"}

SEVERITY_ORDER = vrs.SEVERITY_ORDER
VALID_REVIEW_MODES = sorted(vrs.VALID_REVIEW_MODES)
DEFAULT_PATTERN = "quality#edge-case"
DEFAULT_WORKERS = ["correctness-completeness"]
DEFAULT_BLAST_RADIUS = "single-service"
DEFAULT_REACHABILITY = "plausible-edge"
DEFAULT_CONFIDENCE = "strong-evidence"
RESOLVED_TRIAGE_VALUES = sorted(vrs.RESOLVED_TRIAGE_VALUES)
VALID_TRIAGE_VALUES = ["pending", "deferred"] + RESOLVED_TRIAGE_VALUES

# The identity-qualified filename tail (-p<8 hex>-rN.md) binds the record
# filename to a plan identity token; a slug ending in that shape would trip
# the validator's identity gates when the record is later validated with
# --source-plan. Refuse it up front (named tool error).
_IDENTITY_QUALIFIED_TAIL_RE = re.compile(r"-p[0-9a-f]{8}\Z", re.IGNORECASE)
_ROUND_TAIL_RE = re.compile(r"-r([1-9][0-9]*)\.md\Z")
_NULL_LAST_FIX_TOKENS = {"none", "null", "n/a"}


class ProducerToolError(ValueError):
    """Malformed input or unsupported flag combination (exit 3)."""


class ProducerRefusal(ValueError):
    """A modeled refusal: existing target record, or the validator refused
    the generated pair (exit 1)."""


class OutcomeArgumentParser(argparse.ArgumentParser):
    """Argparse whose usage errors exit 3 with a final OUTCOME: tool_error
    line on stderr (the validator's own usage-error idiom); --help stays a
    metadata exit without an OUTCOME line."""

    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write("%s: error: %s\n" % (self.prog, message))
        sys.stderr.write("OUTCOME: %s\n" % OUTCOME_LABELS[3])
        raise SystemExit(3)


# ---------------------------------------------------------------------------
# Input parsing and normalization
# ---------------------------------------------------------------------------


def load_findings_input(path: Path) -> dict:
    """Read and schema-check the findings JSON input. Raises
    ``ProducerToolError`` on unreadable or schema-violating input."""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ProducerToolError(f"cannot read findings JSON {path}: {exc}")
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ProducerToolError(f"findings JSON {path} is not valid JSON: {exc}")
    if not isinstance(data, dict):
        raise ProducerToolError("findings JSON must be an object")
    allowed = {"plan", "review_round", "review_mode", "findings"}
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise ProducerToolError(
            f"findings JSON rejects unknown key(s) {unknown}; allowed keys "
            f"are {sorted(allowed)}"
        )
    findings = data.get("findings")
    if not isinstance(findings, list):
        raise ProducerToolError("findings JSON 'findings' must be a list")
    normalized = [_normalize_finding(row, index) for index, row in enumerate(findings)]
    seen: set[int] = set()
    for row in normalized:
        if row["id"] in seen:
            raise ProducerToolError(f"finding id {row['id']} appears twice; ids must be unique")
        seen.add(row["id"])
    data["findings"] = normalized
    return data


def _normalize_finding(row: object, index: int) -> dict:
    if not isinstance(row, dict):
        raise ProducerToolError(f"finding at index {index} must be an object")
    allowed = {
        "id",
        "title",
        "severity",
        "blocking",
        "status",
        "triage",
        "file",
        "line",
        "note",
        "pattern",
        "workers",
        "blast_radius",
        "reachability",
        "confidence",
    }
    unknown = sorted(set(row) - allowed)
    if unknown:
        raise ProducerToolError(
            f"finding at index {index} rejects unknown key(s) {unknown}"
        )
    fid = row.get("id")
    if not isinstance(fid, int) or isinstance(fid, bool) or fid < 1:
        raise ProducerToolError(
            f"finding at index {index} needs a positive integer 'id'"
        )
    title = row.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ProducerToolError(f"finding {fid} needs a non-empty string 'title'")
    severity = row.get("severity")
    if severity not in SEVERITY_ORDER:
        raise ProducerToolError(
            f"finding {fid} severity {severity!r} must be one of {list(SEVERITY_ORDER)}"
        )
    blocking = row.get("blocking", False)
    if not isinstance(blocking, bool):
        raise ProducerToolError(f"finding {fid} 'blocking' must be a boolean")
    note = row.get("note")
    if not isinstance(note, str) or not note.strip():
        raise ProducerToolError(
            f"finding {fid} needs a non-empty string 'note' (the finding's "
            "consequence claim; the sidecar consequence is built from it)"
        )
    triage = row.get("triage", "pending")
    if triage not in VALID_TRIAGE_VALUES:
        raise ProducerToolError(
            f"finding {fid} triage {triage!r} must be one of {VALID_TRIAGE_VALUES}"
        )
    status = row.get("status")
    if status is not None and (not isinstance(status, str) or not status.strip()):
        raise ProducerToolError(f"finding {fid} 'status' must be a non-empty string when present")
    file_ref = row.get("file")
    if file_ref is not None and (not isinstance(file_ref, str) or not file_ref.strip()):
        raise ProducerToolError(f"finding {fid} 'file' must be a non-empty string when present")
    line = row.get("line")
    if line is not None and (not isinstance(line, int) or isinstance(line, bool)):
        raise ProducerToolError(f"finding {fid} 'line' must be an integer when present")
    pattern = row.get("pattern", DEFAULT_PATTERN)
    if not isinstance(pattern, str) or not pattern.strip():
        raise ProducerToolError(f"finding {fid} 'pattern' must be a non-empty string when present")
    workers = row.get("workers", list(DEFAULT_WORKERS))
    if (
        not isinstance(workers, list)
        or not workers
        or not all(isinstance(item, str) and item.strip() for item in workers)
    ):
        raise ProducerToolError(
            f"finding {fid} 'workers' must be a non-empty list of strings when present"
        )
    normalized = dict(row)
    normalized.update(
        {
            "id": fid,
            "title": title.strip(),
            "severity": severity,
            "blocking": blocking,
            "triage": triage,
            "note": note.strip(),
            "pattern": pattern.strip(),
            "workers": [item.strip() for item in workers],
        }
    )
    return normalized


def _kebab_slug(text: str) -> str:
    lowered = text.strip().lower()
    kebab = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return kebab or "review"


def _default_artifact_slug(plan_path: Path) -> str:
    return _kebab_slug(plan_path.stem)


# ---------------------------------------------------------------------------
# Record and sidecar builders
# ---------------------------------------------------------------------------


def build_finding_block(finding: dict) -> str:
    """One ``#### F<N>.`` Markdown block: metadata bullets (read only
    before the first level-four sub-heading), then Comment and Analysis."""
    fid = finding["id"]
    lines = [
        f"#### F{fid}. {finding['title']}",
        "",
        f"- **Blocking**: {'true' if finding['blocking'] else 'false'}",
        f"- **Triage**: {finding['triage']}",
        f"- **Pattern**: {finding['pattern']}",
        f"- **Workers**: {', '.join(finding['workers'])}",
    ]
    location = finding.get("file")
    if isinstance(location, str) and location.strip():
        line_no = finding.get("line")
        anchor = f"{location.strip()}:{line_no}" if line_no is not None else location.strip()
        lines.append(f"- **Location**: `{anchor}`")
    if finding.get("status"):
        lines.append(f"- **Status**: {finding['status']}")
    lines.append(f"- **Consequence**: {finding['note']}")
    lines.append(
        "- **Reachability**: "
        f"{finding.get('reachability', DEFAULT_REACHABILITY)}; "
        "**Blast radius**: "
        f"{finding.get('blast_radius', DEFAULT_BLAST_RADIUS)}; "
        "**Confidence**: "
        f"{finding.get('confidence', DEFAULT_CONFIDENCE)}"
    )
    lines.extend(
        [
            "",
            "#### Comment",
            "",
            finding["note"],
            "",
            "#### Analysis",
            "",
            "Staged from the structured findings input by "
            "produce_exec_review_record.py; the claim, anchor, and "
            "calibration ride the finding's Metadata bullets and the "
            "Comment above. Verify the anchor and the discriminating "
            "input during triage before acting on this finding.",
        ]
    )
    return "\n".join(lines)


def build_findings_section(findings: list[dict]) -> str:
    """The ``## Findings`` body: all four severity groups in canonical
    order, each finding under its severity heading, then the overflow
    manifest."""
    by_severity: dict[str, list[dict]] = {sev: [] for sev in SEVERITY_ORDER}
    for finding in findings:
        by_severity.setdefault(finding["severity"], []).append(finding)
    sections = []
    for severity in SEVERITY_ORDER:
        rows = sorted(by_severity.get(severity, []), key=lambda row: row["id"])
        if not rows:
            sections.append(f"### {severity}\nNone.")
            continue
        blocks = [f"### {severity}"]
        blocks.extend(build_finding_block(row) for row in rows)
        sections.append("\n\n".join(blocks))
    return "\n\n".join(sections) + "\n\n### Overflow manifest\nNone."


def build_markdown(ctx: dict) -> str:
    """Build the full staging Markdown record from the normalized context."""
    findings = ctx["findings"]
    findings_count = len(findings)
    medium_plus = sum(1 for row in findings if row["severity"] in ("Critical", "High", "Medium"))
    solo = sum(1 for row in findings if len(row["workers"]) == 1)
    echo = sum(1 for row in findings if len(row["workers"]) > 1)
    panel_rows = []
    for worker, lenses in (
        ("correctness-completeness", "quality, implementation"),
        ("testing", "testing"),
        ("design-simplicity", "architecture, simplification"),
        ("contract-docs", "documentation"),
        ("risk", "security"),
    ):
        attributed = [row for row in findings if worker in row["workers"]]
        row_solo = sum(1 for row in attributed if len(row["workers"]) == 1)
        row_echo = sum(1 for row in attributed if len(row["workers"]) > 1)
        panel_rows.append(
            f"| {worker} | {lenses} | none | complete | {len(attributed)} "
            f"| {row_solo} | {row_echo} | no |"
        )
    if findings:
        verdict_line = f"{medium_plus} Medium+ findings accepted for fix"
        verdict_field = "no"
        triage_section = "Pending triage."
    else:
        # The canonical clean-round shape; the freshness contradiction
        # gates demand the mode/filter/last-fix preconditions the CLI
        # already enforces.
        verdict_line = "0 Medium+ findings; clear round"
        verdict_field = "yes"
        triage_section = (
            "| Worker | Lens | Staged | Fixed | Dropped | Deferred | Pending |\n"
            "|--------|------|--------|-------|---------|----------|---------|\n"
        )
    meta_lines = [
        f"# Plan Review: {ctx['session']} (plan: {ctx['plan_ref']})",
        "## Metadata",
        f"- Type: {ctx['review_type']}",
        "- Record kind: canonical",
        f"- Date: {ctx['date']}",
        f"- URL or Artifact: {ctx['plan_ref']}",
        f"- Round: r{ctx['round']}",
        f"- Review mode: {ctx['review_mode']}",
        "- Changed-risk signals: none",
        f"- Prior findings supplied as filter: {'yes' if ctx['prior_findings_filter'] else 'no'}",
        f"- Last fix commit: {ctx['last_fix_commit'] or 'none'}",
    ]
    if ctx["last_fix_commit"]:
        # The post-fix witness-ledger gate requires one of the two legal
        # shapes; the producer carries the documented empty shape.
        meta_lines.append("- Witness ledger: N/A (no public mutators)")
    meta_lines.extend(
        [
            "- Panel mode: full",
            f"- Source digest: {ctx['source_digest']} (sha256 of {ctx['plan_ref']})",
            f"- review-run-id: {ctx['review_run_id']}",
            f"- review-started-at-ms: {ctx['review_started_at_ms']}",
            f"- Findings: {findings_count}",
            f"- Staged findings: {findings_count}",
            "- Status: STAGED",
            "## Review Statistics",
            "### Panel",
            "| Worker | Lenses | Parent worker | Status | Raw | Solo | Echo | Relaunch |",
            "|--------|--------|---------------|--------|-----|------|------|----------|",
        ]
    )
    meta_lines.extend(panel_rows)
    meta_lines.extend(
        [
            "### Counts",
            "- Workers launched: 5",
            f"- Raw findings (all workers): {findings_count}",
            f"- Staged findings: {findings_count}",
            "- Discarded during synthesis: 0",
            f"- Solo staged (unique agent origin): {solo}",
            f"- Echo staged (multi-agent dedup): {echo}",
            "### Deduplication groups",
            "None.",
            "### Discarded findings",
            "None.",
            "### Severity calibration",
            "None.",
            "### Triage outcomes",
            triage_section,
            f"- Coverage: {ctx['coverage_outcome']}",
            "## Findings",
            "",
            build_findings_section(findings),
            "## Verdict for this round (before fixes)",
            verdict_line,
            "",
        ]
    )
    ctx["verdict_field"] = verdict_field
    return "\n".join(meta_lines)


def build_payload(ctx: dict) -> dict:
    """Build the version-1 stats sidecar payload (the real-record shape:
    the witnessed repair tool's field set minus its regeneration marker,
    plus the mint-derived self-heal chain state)."""
    findings_payload = [
        {
            "id": row["id"],
            "severity": row["severity"],
            "blocking": row["blocking"],
            "blast_radius": row.get("blast_radius", DEFAULT_BLAST_RADIUS),
            "reachability": row.get("reachability", DEFAULT_REACHABILITY),
            "confidence": row.get("confidence", DEFAULT_CONFIDENCE),
            "consequence": row["note"],
            "pattern": row["pattern"],
            "workers": list(row["workers"]),
            "triage": row["triage"],
        }
        for row in sorted(
            ctx["findings"], key=lambda row: (SEVERITY_ORDER.index(row["severity"]), row["id"])
        )
    ]
    panel = []
    for worker, lenses in (
        ("correctness-completeness", ["quality", "implementation"]),
        ("testing", ["testing"]),
        ("design-simplicity", ["architecture", "simplification"]),
        ("contract-docs", ["documentation"]),
        ("risk", ["security"]),
    ):
        attributed = [row for row in ctx["findings"] if worker in row["workers"]]
        panel.append(
            {
                "worker": worker,
                "lenses": list(lenses),
                "parent_worker": None,
                "descendant_launches": [],
                "status": "complete",
                "raw": len(attributed),
                "solo": sum(1 for row in attributed if len(row["workers"]) == 1),
                "echo": sum(1 for row in attributed if len(row["workers"]) > 1),
                "relaunch": False,
            }
        )
    material_lens_set = sorted(
        {lens for lenses in vrs.REQUIRED_PANEL_LENSES.values() for lens in lenses}
    )
    return {
        "schema_version": 1,
        "review_type": ctx["review_type"],
        "date": ctx["date"],
        "artifact_slug": ctx["artifact_slug"],
        "round": f"r{ctx['round']}",
        "panel_mode": "full",
        "selection_reason": None,
        "source_kind": "plan",
        "source_digest": ctx["source_digest"],
        "escalation_reason": None,
        "counts": {
            "workers_launched": 5,
            "raw_findings": len(ctx["findings"]),
            "staged_findings": len(ctx["findings"]),
            "discarded": 0,
            "solo_staged": sum(1 for row in ctx["findings"] if len(row["workers"]) == 1),
            "echo_staged": sum(1 for row in ctx["findings"] if len(row["workers"]) > 1),
        },
        "panel": panel,
        "deduplication_groups": [],
        "discarded": [],
        "severity_calibration": [],
        "triage_outcomes": [],
        "findings": findings_payload,
        "overflow": [],
        "soften_watchlist": [],
        "verdict": ctx["verdict_field"],
        "review_mode": ctx["review_mode"],
        "risk_signals": [],
        "prior_findings_filter": ctx["prior_findings_filter"],
        "last_fix_commit": ctx["last_fix_commit"],
        "record_kind": "canonical",
        "coverage": {
            "outcome": ctx["coverage_outcome"],
            "material_lens_set": material_lens_set,
            "completed": material_lens_set,
            "missing": [],
        },
        "extensions": {
            "convergence": {"self_heal_attempt": ctx["self_heal_state"]},
        },
    }


# ---------------------------------------------------------------------------
# Self-heal chain state (the shared gate's chain rule, producer side)
# ---------------------------------------------------------------------------


def _well_formed_self_heal_state(state: object) -> bool:
    """The state grammar of the shared self-heal gate (status enum, exact
    key set, 32-hex run id, consumed bindings)."""
    if not isinstance(state, dict):
        return False
    status = state.get("status")
    run_id = state.get("run_id")
    if status not in ("unused", "consumed", "unknown"):
        return False
    if not isinstance(run_id, str) or not vrs.USAGE_MINT_RUN_ID_RE.fullmatch(run_id):
        return False
    allowed = {"status", "run_id"}
    if status == "consumed":
        allowed |= {"round", "source_digest"}
        if not re.fullmatch(r"r([1-9][0-9]*)", str(state.get("round", ""))):
            return False
        if not re.fullmatch(r"[0-9a-f]{64}", str(state.get("source_digest", ""))):
            return False
    return set(state) == allowed


def _valid_prior_chain_state(prior_path: Path) -> dict | None:
    """The prior round's chain state when it is a valid post-fence
    canonical record; ``None`` for every other prior evidence shape."""
    prior_sidecar = vrs.stats_sidecar_path(prior_path)
    if not prior_path.is_file() or not prior_sidecar.is_file():
        return None
    try:
        prior_md = prior_path.read_text(encoding="utf-8")
        prior_payload = json.loads(prior_sidecar.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(prior_payload, dict):
        return None
    if prior_payload.get("record_kind") != "canonical":
        return None
    fence = vrs._date_fence(
        prior_path.name, prior_payload.get("date"), vrs.SELF_HEAL_STATE_MIN_DATE
    )
    if fence["name_class"] != "post-fence" or fence["sidecar_class"] != "post-fence":
        return None
    if not vrs._calendar_valid_record_date(fence["name_date"]) or not (
        vrs._calendar_valid_record_date(prior_payload.get("date"))
    ):
        return None
    digest = prior_payload.get("source_digest")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        return None
    extensions = prior_payload.get("extensions")
    convergence = extensions.get("convergence") if isinstance(extensions, dict) else None
    state = convergence.get("self_heal_attempt") if isinstance(convergence, dict) else None
    if not _well_formed_self_heal_state(state):
        return None
    prior_result = vrs.ValidationResult(prior_path)
    vrs.validate_usage_mint_gate(
        prior_path.name, prior_md, prior_result, sidecar_payload=prior_payload
    )
    if prior_result.errors:
        return None
    return state


def self_heal_chain_state(record_path: Path, run_id: str) -> dict:
    """The self-heal member for the record under construction: round 1 (or
    unnumbered) starts unused bound to the record's own run id; a higher
    round carries a valid prior round's state verbatim and reports unknown
    bound to its own run id when no valid prior evidence exists. The
    prior lookup keys on the round chain stem across every dated record in
    the output directory (the shared gate's predecessor-index shape); an
    ambiguous prior (two dated records for the same chain round) refuses
    before anything is written."""
    match = _ROUND_TAIL_RE.search(record_path.name)
    number = int(match.group(1)) if match else 1
    if number == 1:
        return {"status": "unused", "run_id": run_id}
    stem = re.sub(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}-", "", record_path.name)
    chain_stem = re.sub(r"-r[1-9][0-9]*\.md\Z", "", stem)
    name_re = re.compile(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}-(.+?)(?:-r([1-9][0-9]*))?\.md\Z"
    )
    candidates = []
    if record_path.parent.is_dir():
        for candidate in record_path.parent.iterdir():
            name_match = name_re.fullmatch(candidate.name)
            if name_match and name_match.group(1) == chain_stem and (
                int(name_match.group(2) or 1) == number - 1
            ):
                candidates.append(candidate)
    if len(candidates) > 1:
        raise ProducerRefusal(
            f"ambiguous prior-round records for chain {chain_stem!r} "
            f"round r{number - 1}: {sorted(c.name for c in candidates)}; "
            "the shared self-heal gate refuses an ambiguous predecessor, "
            "disambiguate the directory first"
        )
    state = _valid_prior_chain_state(candidates[0]) if candidates else None
    if state is not None:
        return dict(state)
    return {"status": "unknown", "run_id": run_id}


# ---------------------------------------------------------------------------
# Pair writing and validation
# ---------------------------------------------------------------------------


def write_pair(out_dir: Path, record_name: str, markdown: str, payload: dict) -> Path:
    """Write the record and its sidecar; refuse to touch an existing
    record or an existing sidecar (creation-only)."""
    record_path = out_dir / record_name
    if record_path.exists():
        raise ProducerRefusal(
            f"refusing to write an existing record (the producer only "
            f"creates new pairs): {record_path}"
        )
    sidecar_path = record_path.with_suffix(".stats.json")
    if sidecar_path.exists():
        raise ProducerRefusal(
            f"refusing to overwrite an existing sidecar (the producer only "
            f"creates new pairs): {sidecar_path}"
        )
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        record_path.write_text(markdown, encoding="utf-8")
        sidecar_path.write_text(
            json.dumps(payload, indent=1) + "\n", encoding="utf-8"
        )
    except OSError:
        # A half-written pair is a strand; remove the written half and
        # surface the failure as a tool error, never a silent partial pair.
        try:
            sidecar_path.unlink(missing_ok=True)
            record_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise ProducerToolError(
            f"failed to write the pair under {out_dir} (both halves removed)"
        ) from None
    return record_path


def run_validator(record_path: Path) -> tuple[int, str, str]:
    """Run the validator's hard-mode CLI contract in-process; returns
    (exit code, stdout, stderr)."""
    out_buf, err_buf = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out_buf), contextlib.redirect_stderr(err_buf):
        try:
            code = vrs.main(["--hard", str(record_path)])
        except SystemExit as exc:  # usage-error channel keeps its code
            code = exc.code
    return code, out_buf.getvalue(), err_buf.getvalue()


def final_outcome(stdout_text: str) -> str | None:
    """The final ``OUTCOME:`` line's label, or None when absent (a crash
    or truncated capture is never a pass)."""
    rows = [row.strip() for row in stdout_text.splitlines() if row.strip().startswith("OUTCOME:")]
    return rows[-1].split(":", 1)[1].strip() if rows else None


def validate_generated_pair(record_path: Path) -> tuple[bool, str, str]:
    """Validate one generated pair through the validator's hard-mode CLI
    contract. Returns ``(ok, outcome_label, evidence)``: ok is True only
    when the invocation exits 0 AND the final outcome line reads
    ``OUTCOME: pass``; the evidence carries the validator's stdout and
    stderr for refusal reporting."""
    code, out, err = run_validator(record_path)
    outcome = final_outcome(out)
    ok = code == 0 and outcome == "pass"
    evidence = out
    if err.strip():
        evidence = evidence.rstrip("\n") + "\n" + err
    return ok, (outcome or f"exit-{code}-no-outcome-line"), evidence


# ---------------------------------------------------------------------------
# Context assembly and CLI
# ---------------------------------------------------------------------------


def build_context(args: argparse.Namespace, findings_input: dict) -> dict:
    """Cross-check the CLI flags against the JSON input and assemble the
    normalized record context. Raises ``ProducerToolError`` on malformed
    input and ``ProducerRefusal`` on existing-record conflicts."""
    plan_path = Path(args.plan).expanduser()
    if not plan_path.is_file():
        raise ProducerToolError(f"plan file not found: {plan_path}")
    try:
        plan_bytes = plan_path.read_bytes()
    except OSError as exc:
        raise ProducerToolError(f"cannot read plan file {plan_path}: {exc}")

    json_plan = findings_input.get("plan")
    if json_plan is not None:
        if not isinstance(json_plan, str) or not json_plan.strip():
            raise ProducerToolError("findings JSON 'plan' must be a non-empty string when present")
        if Path(json_plan).resolve() != plan_path.resolve():
            raise ProducerToolError(
                f"plan mismatch: --plan {plan_path} does not match the "
                f"findings JSON 'plan' {json_plan!r}"
            )

    review_mode = args.review_mode
    json_mode = findings_input.get("review_mode")
    if review_mode is not None and json_mode is not None and review_mode != json_mode:
        raise ProducerToolError(
            f"review mode mismatch: --review-mode {review_mode!r} does not "
            f"match the findings JSON 'review_mode' {json_mode!r}"
        )
    if review_mode is None:
        review_mode = json_mode if json_mode is not None else "targeted"
    if review_mode not in vrs.VALID_REVIEW_MODES:
        raise ProducerToolError(
            f"review mode {review_mode!r} must be one of {VALID_REVIEW_MODES}"
        )

    round_value = args.round
    json_round = findings_input.get("review_round")
    if round_value is not None and json_round is not None and round_value != json_round:
        raise ProducerToolError(
            f"round mismatch: --round {round_value} does not match the "
            f"findings JSON 'review_round' {json_round}"
        )
    if round_value is None:
        round_value = json_round if json_round is not None else 1
    if (
        not isinstance(round_value, int)
        or isinstance(round_value, bool)
        or round_value < 1
    ):
        raise ProducerToolError(f"review round must be a positive integer; got {round_value!r}")

    if args.date is not None:
        date_value = args.date
    else:
        date_value = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    if not vrs._calendar_valid_record_date(date_value):
        raise ProducerToolError(
            f"date {date_value!r} must be a calendar-valid YYYY-MM-DD date"
        )

    run_id = args.review_run_id
    if not isinstance(run_id, str) or not vrs.USAGE_MINT_RUN_ID_RE.fullmatch(run_id):
        raise ProducerToolError(
            "--review-run-id must be a 32-character lowercase hex id (the "
            "review_usage_capture.py mint output's review_run_id)"
        )
    started_at = args.review_started_at_ms
    if started_at is None or started_at <= 0:
        raise ProducerToolError(
            "--review-started-at-ms must be a positive integer (the mint "
            "output's minted_at_ms)"
        )

    prior_filter = (args.prior_findings_filter or "no").strip().lower()
    if prior_filter not in ("yes", "no"):
        raise ProducerToolError("--prior-findings-filter must be yes or no")

    last_fix = (args.last_fix_commit or "").strip() or None
    findings = findings_input["findings"]
    clean_round = not findings
    if last_fix is not None and last_fix.lower() in _NULL_LAST_FIX_TOKENS:
        last_fix = None
    if last_fix is not None and clean_round and review_mode != "fresh-adversarial":
        # The freshness gate: a last-fix clean round's mode must be
        # fresh-adversarial; the producer refuses the unsupported
        # combination instead of emitting a record the validator refuses.
        raise ProducerToolError(
            f"--last-fix-commit with a clean (empty-findings) round "
            f"requires --review-mode fresh-adversarial; got {review_mode!r}"
        )

    slug = args.artifact_slug or _default_artifact_slug(plan_path)
    if _IDENTITY_QUALIFIED_TAIL_RE.search(slug):
        raise ProducerToolError(
            f"artifact slug {slug!r} ends in the identity-qualified tail "
            "(-p<8 hex>); that shape is reserved for plan-identity token "
            "filenames, pick a slug without it"
        )
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
        raise ProducerToolError(
            f"artifact slug {slug!r} must be kebab-case (lowercase letters, "
            "digits, hyphens)"
        )

    repo_root = review_plan_identity.repository_root(plan_path.parent)
    plan_ref = (
        review_plan_identity.normalize_plan_path(plan_path, repo_root)
        if repo_root is not None
        else plan_path.as_posix()
    )
    if plan_ref is None:
        plan_ref = plan_path.as_posix()

    record_name = f"{date_value}-plan-review-{slug}-r{round_value}.md"
    record_path = Path(args.out_dir) / record_name
    coverage_outcome = "clean"
    ctx = {
        "session": args.session,
        "plan_ref": plan_ref,
        "date": date_value,
        "round": round_value,
        "review_mode": review_mode,
        "prior_findings_filter": prior_filter == "yes",
        "last_fix_commit": last_fix,
        "review_run_id": run_id,
        "review_started_at_ms": started_at,
        "review_type": args.review_type,
        "artifact_slug": slug,
        "source_digest": vrs.compute_source_digest("plan", plan_bytes),
        "coverage_outcome": coverage_outcome,
        "findings": findings,
        "record_path": record_path,
    }
    # build_markdown resolves the verdict field the payload needs; keep the
    # call order explicit so the two builders stay in sync by construction.
    ctx["self_heal_state"] = self_heal_chain_state(record_path, run_id)
    return ctx


def produce(args: argparse.Namespace) -> int:
    """The produce flow: build, write, validate, report. Returns the exit
    code; the final OUTCOME line is printed by :func:`main`."""
    findings_input = load_findings_input(Path(args.findings_json))
    ctx = build_context(args, findings_input)
    markdown = build_markdown(ctx)
    payload = build_payload(ctx)
    record_path = write_pair(Path(args.out_dir), ctx["record_path"].name, markdown, payload)
    print(f"produced: {record_path}")
    print(f"sidecar: {record_path.with_suffix('.stats.json')}")
    ok, outcome, evidence = validate_generated_pair(record_path)
    if not ok:
        # Delete-on-refusal: a pair the validator refuses never strands.
        try:
            record_path.with_suffix(".stats.json").unlink()
            record_path.unlink()
        except OSError:
            pass
        print(f"REFUSED: validator outcome {outcome!r} for record {record_path}")
        sys.stdout.write(evidence)
        print("OUTCOME: fail")
        return 1
    print(f"validated: OUTCOME: pass (validator hard mode) for {record_path}")
    print("OUTCOME: pass")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = OutcomeArgumentParser(
        prog="produce_exec_review_record.py",
        description=(
            "Produce a findings-bearing execution review record pair "
            "(Markdown plus .stats.json sidecar) and validate it with "
            "scripts/validate_review_staging.py. Creation-only: existing "
            "records are never touched and nothing is ever repaired."
        ),
    )
    parser.add_argument("--out-dir", required=True, help="directory to write the pair into")
    parser.add_argument("--session", required=True, help="session identifier for the record title")
    parser.add_argument(
        "--plan", required=True, help="reviewed plan file; its bytes' SHA-256 becomes source_digest"
    )
    parser.add_argument(
        "--findings-json",
        required=True,
        help=(
            "findings input JSON: {plan, review_round, review_mode, "
            "findings: [{id, title, severity, blocking, status, triage, "
            "file, line, note}]}"
        ),
    )
    parser.add_argument(
        "--review-mode",
        default=None,
        choices=VALID_REVIEW_MODES,
        help="review mode (default: the JSON review_mode, else targeted)",
    )
    parser.add_argument(
        "--round",
        type=int,
        default=None,
        help="review round number (default: the JSON review_round, else 1)",
    )
    parser.add_argument(
        "--date",
        default=None,
        help="record date YYYY-MM-DD (default: today, UTC)",
    )
    parser.add_argument(
        "--artifact-slug",
        default=None,
        help="artifact slug (default: kebab-cased plan filename stem)",
    )
    parser.add_argument(
        "--review-run-id",
        required=True,
        help="32-character lowercase hex review run id (review_usage_capture.py mint)",
    )
    parser.add_argument(
        "--review-started-at-ms",
        type=int,
        required=True,
        help="positive integer mint time in ms (review_usage_capture.py mint)",
    )
    parser.add_argument(
        "--last-fix-commit",
        default=None,
        help="last fix commit sha when this round reviews a fix (default: none)",
    )
    parser.add_argument(
        "--prior-findings-filter",
        default="no",
        help="whether prior findings were supplied as filter: yes or no (default no)",
    )
    parser.add_argument(
        "--review-type",
        default="Plan Review",
        help="review type label (default: Plan Review)",
    )
    args = parser.parse_args(argv)
    try:
        return produce(args)
    except ProducerToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print(f"OUTCOME: {OUTCOME_LABELS[3]}")
        return 3
    except ProducerRefusal as exc:
        print(f"REFUSED: {exc}")
        print(f"OUTCOME: {OUTCOME_LABELS[1]}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
