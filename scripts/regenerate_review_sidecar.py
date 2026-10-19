"""Regenerate a missing review stats sidecar from its own record's Markdown.

The repair tool for the witnessed defective-pair class (review-record
legacy identity plan, Task 3): a canonical review record whose Markdown
carries its full review metadata while its ``<record>.stats.json`` twin
is missing. The tool transcribes the sidecar from the record's own lines
under the rule-closed taxonomy (transcribed, derived, and defaulted
classes with no required version-1 field unassigned), marks it
``extensions.regenerated_from_markdown: true``, appends the missing
``Record kind: canonical`` Markdown twin when the record needs one (the
only Markdown write it ever performs), then validates the repaired pair
in place at its real destination with the expected digest armed from the
transcribed identity's plan bytes. Any validation refusal deletes the
just-written sidecar in the same invocation (delete-on-refusal), so no
non-validating sidecar strands and a corrected-Markdown retry stays
bounded: a rewrite is permitted only for a sidecar carrying this tool's
own regeneration marker, and a foreign sidecar is never overwritten.

Trust anchor: transcription shifts the repaired pair's trust anchor to
the Markdown record. The tool never invents evidence (no evidence-bearing
field is ever defaulted) and never guesses a plan identity from the
filename slug: a record whose Markdown resolves no identity is refused
and named in the census.

Refusals are recorded outcomes, not run failures: the tool always exits 0
after printing its repair census (the per-run inventory naming every
repaired pair and every refused record with its reason). ``--receipt
PATH`` writes the same census lines to a file on a real run; a dry run
(``--dry-run``) prints the would-repair and would-refuse sets and writes
nothing anywhere.

Usage:

    python3 scripts/regenerate_review_sidecar.py [--dry-run] [--receipt PATH] RECORD ...

Each RECORD argument is a review record path; a directory argument is
scanned for defective candidates (records whose sidecar is missing or
carries this tool's marker), iterated per series in ascending round order
so a higher round's verbatim chain carry always sees its lower neighbor's
final sidecar.

Single-owner reuse: the fence classification, Metadata section reader,
record-kind twin reader, panel lens table, and calendar-date checks are
imported from ``validate_review_staging`` (the shared gates this tool
must satisfy); the artifact slug comes from ``plan_readiness.artifact_slug``
(the one canonical slug derivation) so a repaired sidecar can never
disagree with the consulting readiness gate about the slug.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import review_plan_identity
import validate_review_staging as vrs

# The sidecar extensions member marking this tool's own output (the one
# additive extensions member this plan lands). Descriptive-only: no gate
# keys tolerance on it, and the bounded-retry rule reads it to permit a
# corrected-Markdown rewrite of the tool's own sidecar.
REGENERATED_MARKER_KEY = "regenerated_from_markdown"

# The rule-closed transcription taxonomy over the version-1 sidecar's
# top-level fields: every required field (the version-1 required set plus
# the extended freshness set plus the fenced coverage/record_kind members)
# is assigned to exactly one class, pairwise disjoint. ``verdict`` is
# optional in the version-1 contract but required by this tool (it is
# transcribed from the record's Summary verdict line). The optional
# ``depth`` and ``domains`` fields are transcribed when their Metadata
# lines are present and omitted otherwise; they stay outside the required
# partition.
TRANSCRIBED_FIELDS = frozenset(
    {
        "source_digest",
        "verdict",
        "counts",
        "panel",
        "findings",
        "round",
        "date",
        "review_type",
        "panel_mode",
        "selection_reason",
        "review_mode",
        "risk_signals",
        "prior_findings_filter",
        "last_fix_commit",
    }
)
DERIVED_FIELDS = frozenset(
    {
        "artifact_slug",
        "source_kind",
        "schema_version",
        "record_kind",
        "coverage",
    }
)
DEFAULTED_FIELDS = frozenset(
    {
        "escalation_reason",
        "soften_watchlist",
        "deduplication_groups",
        "discarded",
        "overflow",
        "severity_calibration",
        "triage_outcomes",
    }
)
OPTIONAL_TRANSCRIBED_FIELDS = frozenset({"depth", "domains"})

# The Metadata labels the transcribed class reads verbatim, mapped to the
# internal transcription keys. A record missing any of these lines is an
# incomplete record and is refused without writing.
_TRANSCRIBED_META_LABELS = (
    ("Source digest", "source_digest"),
    ("Round", "round"),
    ("Date", "date"),
    ("Type", "review_type"),
    ("Panel mode", "panel_mode"),
    ("Selection reason", "selection_reason"),
    ("Review mode", "review_mode"),
    ("Changed-risk signals", "risk_signals"),
    ("Prior findings supplied as filter", "prior_findings_filter"),
    ("Last fix commit", "last_fix_commit"),
    ("Coverage", "coverage_outcome"),
    ("Findings", "findings_declared"),
    ("review-run-id", "mint_run_id"),
    ("review-started-at-ms", "mint_started_at"),
)
_REQUIRED_META_LABELS = frozenset(label for label, _ in _TRANSCRIBED_META_LABELS)

# The Counts-section lines the counts transcription reads verbatim.
_COUNTS_META = (
    ("Workers launched", "workers_launched"),
    ("Raw findings (all workers)", "raw_findings"),
    ("Staged findings", "staged_findings"),
    ("Discarded during synthesis", "discarded"),
    ("Solo staged (unique agent origin)", "solo_staged"),
    ("Echo staged (multi-agent dedup)", "echo_staged"),
)

# The one staging-name grammar of the shared self-heal gate (the same
# fullmatch shape ``validate_review_staging`` uses for predecessor
# indexing), reused here for the chain-stem and prior-round lookups.
_STAGING_NAME_RE = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}-(.+?)(?:-r([1-9][0-9]*))?\.md\Z"
)
_ROUND_SUFFIX_RE = re.compile(r"-r([1-9][0-9]*)\.md\Z")

_NULL_VOCABULARY = {"none", "null", "n/a"}


class RepairRefusal(ValueError):
    """A named transcription refusal (fail-closed, no write follows)."""


def _int_cell(label: str, value: str) -> int:
    try:
        return int(value.strip())
    except ValueError:
        raise RepairRefusal(
            f"incomplete record: {label} must be an integer; got "
            f"{value!r}"
        )


def _split_list_value(value: str) -> list[str]:
    items = [item.strip() for item in value.split(",")]
    cleaned = [item for item in items if item]
    if len(cleaned) == 1 and cleaned[0].lower() in _NULL_VOCABULARY:
        return []
    return cleaned


def _metadata_values(meta: str) -> tuple[dict[str, str], set[str]]:
    """First-occurrence values per Metadata label plus the duplicated set."""
    values: dict[str, str] = {}
    duplicates: set[str] = set()
    for match in re.finditer(
        r"^-[ \t]*([^:\n]+?)[ \t]*:[ \t]*(.*?)[ \t]*$", meta, re.MULTILINE
    ):
        label, value = match.group(1), match.group(2)
        if label in values:
            duplicates.add(label)
        else:
            values[label] = value
    return values, duplicates


def _section_lines(content: str, heading: str) -> list[str]:
    """Lines between the ``## <heading>`` / ``### <heading>`` line and the
    next heading; empty when the section is absent."""
    lines = content.splitlines()
    start = None
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped in (f"## {heading}", f"### {heading}"):
            start = idx + 1
            break
    if start is None:
        return []
    out: list[str] = []
    for line in lines[start:]:
        if line.startswith("## ") or line.startswith("### "):
            break
        out.append(line)
    return out


def _panel_rows(content: str) -> list[dict[str, str]]:
    """Panel table rows keyed by header name (never by column position:
    the witnessed shape and the branch-review template order the columns
    differently)."""
    header = None
    rows: list[dict[str, str]] = []
    for line in _section_lines(content, "Panel"):
        if not line.strip().startswith("|"):
            if header is not None:
                break
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        if header is None:
            header = cells
            continue
        rows.append(dict(zip(header, cells)))
    return rows


def _transcribe_panel(content: str) -> list[dict]:
    """Transcribe the panel rows verbatim from the record's own table."""
    required_columns = (
        "Worker",
        "Lenses",
        "Status",
        "Raw",
        "Solo",
        "Echo",
        "Relaunch",
        "Parent worker",
    )
    panel: list[dict] = []
    for row in _panel_rows(content):
        missing = [column for column in required_columns if column not in row]
        if missing:
            raise RepairRefusal(
                "incomplete record: Panel table is missing column(s) "
                f"{missing}"
            )
        relaunch = row["Relaunch"].strip().lower()
        if relaunch not in ("yes", "no"):
            raise RepairRefusal(
                "incomplete record: Panel Relaunch cell must be yes or no; "
                f"got {row['Relaunch']!r}"
            )
        parent = row["Parent worker"].strip()
        lenses = [item for item in row["Lenses"].split(",") if item.strip()]
        if not lenses:
            # The single lens fallback the shared gates use: a row without
            # declared lenses inherits the worker's required lens set.
            lenses = sorted(
                vrs.REQUIRED_PANEL_LENSES.get(row["Worker"].strip(), [])
            )
        panel.append(
            {
                "worker": row["Worker"].strip(),
                "lenses": [lens.strip() for lens in lenses],
                "parent_worker": None if parent.lower() in _NULL_VOCABULARY else parent,
                "status": row["Status"].strip(),
                "raw": _int_cell("Panel Raw", row["Raw"]),
                "solo": _int_cell("Panel Solo", row["Solo"]),
                "echo": _int_cell("Panel Echo", row["Echo"]),
                "relaunch": relaunch == "yes",
                # The Markdown table carries no descendant-launch column;
                # the canonical empty form is the derived constant.
                "descendant_launches": [],
            }
        )
    if not panel:
        raise RepairRefusal(
            "incomplete record: the Panel table carries no worker rows"
        )
    return panel


def _well_formed_self_heal_state(state: object) -> bool:
    """The state grammar of the shared self-heal gate (status enum, exact
    key set, 32-hex run id, consumed bindings)."""
    if not isinstance(state, dict):
        return False
    status = state.get("status")
    run_id = state.get("run_id")
    if status not in ("unused", "consumed", "unknown"):
        return False
    if not isinstance(run_id, str) or not vrs.USAGE_MINT_RUN_ID_RE.fullmatch(
        run_id
    ):
        return False
    allowed = {"status", "run_id"}
    if status == "consumed":
        allowed |= {"round", "source_digest"}
        if not re.fullmatch(r"r([1-9][0-9]*)", str(state.get("round", ""))):
            return False
        if not re.fullmatch(
            r"[0-9a-f]{64}", str(state.get("source_digest", ""))
        ):
            return False
    return set(state) == allowed


def _valid_prior_chain_state(prior_path: Path) -> dict | None:
    """The prior round's chain state when it is a valid post-fence
    canonical record; ``None`` for every other prior evidence shape
    (missing, malformed, pre-fence, or non-canonical)."""
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
        prior_path.name,
        prior_payload.get("date"),
        vrs.SELF_HEAL_STATE_MIN_DATE,
    )
    if fence["name_class"] != "post-fence" or fence["sidecar_class"] != "post-fence":
        return None
    if not vrs._calendar_valid_record_date(
        fence["name_date"]
    ) or not vrs._calendar_valid_record_date(prior_payload.get("date")):
        return None
    digest = prior_payload.get("source_digest")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        return None
    extensions = prior_payload.get("extensions")
    convergence = (
        extensions.get("convergence") if isinstance(extensions, dict) else None
    )
    state = (
        convergence.get("self_heal_attempt")
        if isinstance(convergence, dict)
        else None
    )
    if not _well_formed_self_heal_state(state):
        return None
    prior_result = vrs.ValidationResult(prior_path)
    vrs.validate_usage_mint_gate(
        prior_path.name, prior_md, prior_result, sidecar_payload=prior_payload
    )
    if prior_result.errors:
        return None
    return state


def _self_heal_chain_state(record: Path, own_run_id: str) -> dict:
    """The self-heal member chain rule: a valid post-fence canonical prior
    round carries the prior chain state verbatim (same run id and status);
    a repaired round of 1 or unnumbered derives the unused status bound to
    the record's own run id; every other unavailable prior evidence shape
    derives the unknown status bound to the record's own run id."""
    match = _ROUND_SUFFIX_RE.search(record.name)
    number = int(match.group(1)) if match else 1
    if number == 1:
        return {"status": "unused", "run_id": own_run_id}
    stem_match = _STAGING_NAME_RE.fullmatch(record.name)
    chain_stem = stem_match.group(1) if stem_match else record.stem
    predecessors: dict[tuple[str, int], list[Path]] = {}
    for candidate in record.parent.iterdir():
        name_match = _STAGING_NAME_RE.fullmatch(candidate.name)
        if name_match:
            key = (name_match.group(1), int(name_match.group(2) or 1))
            predecessors.setdefault(key, []).append(candidate)
    candidates = sorted(predecessors.get((chain_stem, number - 1), []))
    if len(candidates) == 1:
        state = _valid_prior_chain_state(candidates[0])
        if state is not None:
            return dict(state)
    return {"status": "unknown", "run_id": own_run_id}


def transcribe_record(record: Path) -> dict:
    """Transcribe the record's own lines into the internal field set.

    Pure read: raises ``RepairRefusal`` and never writes. The returned
    dict carries every transcribed value plus the parsed counts, panel,
    verdict, optional depth/domains, the identity, and the needs-twin
    flag; the payload assembly happens in ``repair_record``.
    """
    try:
        content = record.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise RepairRefusal(f"cannot read record: {exc}")
    meta = vrs._metadata_section(content)
    if meta is None:
        raise RepairRefusal("record carries no Metadata section")
    values, duplicates = _metadata_values(meta)
    for label in sorted(duplicates & _REQUIRED_META_LABELS):
        raise RepairRefusal(f"duplicate Metadata label {label!r}")
    fields: dict = {}
    for label, key in _TRANSCRIBED_META_LABELS:
        if label not in values:
            raise RepairRefusal(
                f"incomplete record: missing Metadata line {label!r}"
            )
        fields[key] = values[label]

    present, md_kind, kind_lines = vrs._metadata_record_kind(content)
    if kind_lines > 1:
        raise RepairRefusal(
            "duplicate 'Record kind:' Metadata label; keep exactly one"
        )
    if present and md_kind != "canonical":
        raise RepairRefusal(
            f"record kind twin declares {md_kind!r}; the repair tool "
            "transcribes canonical records only"
        )
    fields["needs_twin"] = not present

    filter_value = fields["prior_findings_filter"].strip().lower()
    if filter_value not in ("yes", "no"):
        raise RepairRefusal(
            "incomplete record: 'Prior findings supplied as filter' must "
            f"be yes or no; got {fields['prior_findings_filter']!r}"
        )
    fields["prior_findings_filter"] = filter_value == "yes"

    last_fix = fields["last_fix_commit"].strip()
    fields["last_fix_commit"] = (
        None if last_fix.lower() in _NULL_VOCABULARY else last_fix
    )
    fields["risk_signals"] = _split_list_value(fields["risk_signals"])
    fields["identity"] = review_plan_identity.markdown_identity(content)
    if fields["identity"] is None:
        raise RepairRefusal(
            "record resolves no plan identity (no URL or Artifact line); "
            "refusing to guess one from the filename slug"
        )

    summary = summary_of(content)
    verdicts = verdict_tokens_of(summary)
    if not verdicts:
        raise RepairRefusal(
            "incomplete record: no ready=yes/no verdict line in the "
            "record's ## Summary"
        )
    fields["verdict"] = verdicts[-1]

    count_values: dict[str, int] = {}
    for line in _section_lines(content, "Counts"):
        count_match = re.match(
            r"^-[ \t]*(.+?)[ \t]*:[ \t]*([0-9]+)[ \t]*$", line
        )
        if count_match:
            count_values[count_match.group(1)] = int(count_match.group(2))
    counts: dict[str, int] = {}
    for label, key in _COUNTS_META:
        if label not in count_values:
            raise RepairRefusal(
                f"incomplete record: missing Counts line {label!r}"
            )
        counts[key] = count_values[label]
    fields["counts"] = counts

    declared = _int_cell("Metadata Findings", fields["findings_declared"])
    if declared != counts["staged_findings"]:
        raise RepairRefusal(
            "record declares inconsistent staged findings: the Metadata "
            f"Findings line says {declared} while the Counts section says "
            f"{counts['staged_findings']}"
        )
    if counts["staged_findings"] != 0:
        raise RepairRefusal(
            f"record declares {counts['staged_findings']} staged findings; "
            "the repair tool transcribes the zero-findings witnessed class "
            "only (no finding detail is ever invented)"
        )
    fields["findings"] = []

    fields["panel"] = _transcribe_panel(content)

    if "Depth" in values:
        fields["depth"] = values["Depth"]
    if "Domains" in values:
        fields["domains"] = _split_list_value(values["Domains"])
    return fields


def summary_of(content: str) -> str:
    """The record's ``## Summary`` section (empty when absent)."""
    return "\n".join(_section_lines(content, "Summary"))


def verdict_tokens_of(summary: str) -> list[str]:
    """The ready=yes/no tokens per the shared verdict token grammar
    (word-bounded ``ready=(yes|no)``, last occurrence wins)."""
    return [
        match.group(1).lower()
        for match in re.finditer(r"\bready\s*=\s*(yes|no)\b", summary, re.IGNORECASE)
    ]


def _sidecar_is_ours(sidecar: Path) -> bool:
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    extensions = payload.get("extensions") if isinstance(payload, dict) else None
    return (
        isinstance(extensions, dict)
        and extensions.get(REGENERATED_MARKER_KEY) is True
    )


def _assemble_payload(fields: dict, identity: str, slug: str, state: dict) -> dict:
    material = sorted(
        {lens for row in fields["panel"] for lens in row["lenses"]}
    )
    payload: dict = {
        "schema_version": 1,
        "review_type": fields["review_type"],
        "date": fields["date"],
        "artifact_slug": slug,
        "round": fields["round"],
        "panel_mode": fields["panel_mode"],
        "selection_reason": fields["selection_reason"],
        "source_kind": "plan",
        "source_digest": fields["source_digest"],
        "escalation_reason": None,
        "counts": fields["counts"],
        "panel": fields["panel"],
        "deduplication_groups": [],
        "discarded": [],
        "severity_calibration": [],
        "triage_outcomes": [],
        "findings": fields["findings"],
        "overflow": [],
        "soften_watchlist": [],
        "verdict": fields["verdict"],
        "review_mode": fields["review_mode"],
        "risk_signals": fields["risk_signals"],
        "prior_findings_filter": fields["prior_findings_filter"],
        "last_fix_commit": fields["last_fix_commit"],
        "record_kind": "canonical",
        "coverage": {
            "outcome": fields["coverage_outcome"],
            "material_lens_set": material,
            "completed": material,
            "missing": [],
        },
        "extensions": {
            "plan_identity": identity,
            "convergence": {"self_heal_attempt": state},
            REGENERATED_MARKER_KEY: True,
        },
    }
    if "depth" in fields:
        payload["depth"] = fields["depth"]
    if "domains" in fields:
        payload["domains"] = fields["domains"]
    return payload


def _outcome(dry_run: bool, reason: str) -> tuple[str, str]:
    return ("would-refuse" if dry_run else "refused", reason)


def repair_record(record: Path, *, dry_run: bool = False) -> tuple[str, str | None]:
    """One candidate record's repair arm.

    Returns ``(status, reason)`` with status ``repaired``, ``refused``,
    ``would-repair``, or ``would-refuse``; the reason is ``None`` only for
    the repaired/would-repair outcomes. A dry run writes nothing anywhere;
    a real run writes the twin line (when needed), the sidecar, and
    nothing else, and deletes the just-written sidecar on any in-place
    validation refusal (restoring the Markdown when the twin line was
    appended), so a refusal strands no partial state.
    """
    record = Path(record)
    sidecar = vrs.stats_sidecar_path(record)
    if sidecar.is_file() and not _sidecar_is_ours(sidecar):
        return _outcome(
            dry_run,
            "refusing to overwrite the existing stats sidecar (it carries "
            "no regeneration marker; a foreign sidecar is never "
            "overwritten)",
        )
    try:
        fields = transcribe_record(record)
    except RepairRefusal as exc:
        return _outcome(dry_run, str(exc))

    root = review_plan_identity.repository_root(record.parent)
    if root is None:
        return _outcome(
            dry_run, "cannot resolve the repository root for the record"
        )
    identity = fields["identity"]
    plan_path = root / identity
    if not plan_path.is_file():
        return _outcome(
            dry_run,
            f"plan identity path {identity!r} does not exist under the "
            "repository root (moved or completed plan); refusing",
        )
    try:
        plan_bytes = plan_path.read_bytes()
    except OSError as exc:
        return _outcome(
            dry_run,
            f"cannot read the plan bytes at the recorded identity path: "
            f"{exc}",
        )
    expected_digest = vrs.compute_source_digest("plan", plan_bytes)

    try:
        import plan_readiness

        slug = plan_readiness.artifact_slug(Path(identity))
    except ValueError as exc:
        return _outcome(dry_run, str(exc))

    if dry_run:
        if fields["source_digest"] != expected_digest:
            return (
                "would-refuse",
                "recorded source digest does not match the live plan bytes "
                "at the recorded identity path (stale digest)",
            )
        return ("would-repair", None)

    original_md: str | None = None
    if fields["needs_twin"] and (
        vrs._date_fence(
            record.name, None, vrs.RECORD_KIND_SIDECAR_MIN_DATE
        )["name_class"]
        == "post-fence"
    ):
        original_md = record.read_text(encoding="utf-8")
        record.write_text(
            original_md.replace(
                "## Metadata\n",
                "## Metadata\n- Record kind: canonical\n",
                1,
            ),
            encoding="utf-8",
        )

    state = _self_heal_chain_state(record, fields["mint_run_id"])
    payload = _assemble_payload(fields, identity, slug, state)
    refused_reason: str | None
    try:
        sidecar.write_text(
            json.dumps(payload, indent=1) + "\n", encoding="utf-8"
        )
        result = vrs.validate_staging_file(
            record,
            hard=True,
            expected_digest=expected_digest,
            source_kind="plan",
        )
        if result.errors:
            refused_reason = result.errors[0]
        else:
            return ("repaired", None)
    except OSError as exc:
        refused_reason = f"repair write failed: {exc}"
    # Delete-on-refusal: the in-place validation refused, so the
    # just-written sidecar is deleted in the same invocation and an
    # appended twin line is restored, leaving no non-validating strand.
    if original_md is not None:
        record.write_text(original_md, encoding="utf-8")
    try:
        sidecar.unlink()
    except OSError:
        pass
    return ("refused", refused_reason)


def _round_order_key(path: Path) -> tuple:
    """Per-series ascending round order (the campaign's iteration order:
    a higher round's verbatim chain carry must see its lower neighbor's
    final sidecar)."""
    stem_match = _STAGING_NAME_RE.fullmatch(path.name)
    round_match = _ROUND_SUFFIX_RE.search(path.name)
    round_no = int(round_match.group(1)) if round_match else 1
    if stem_match is None:
        return (path.name, round_no)
    return (stem_match.group(1), round_no, path.name)


def _collect_records(paths: list[str]) -> list[Path]:
    """Explicit files in argument order; directories scanned for defective
    candidates (sidecar missing or marker-bearing) in ascending round
    order."""
    records: list[Path] = []
    seen: set[Path] = set()
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            candidates = [
                candidate
                for candidate in sorted(path.glob("*.md"))
                if not vrs.stats_sidecar_path(candidate).is_file()
                or _sidecar_is_ours(vrs.stats_sidecar_path(candidate))
            ]
            candidates.sort(key=_round_order_key)
            for candidate in candidates:
                if candidate not in seen:
                    seen.add(candidate)
                    records.append(candidate)
        else:
            if path not in seen:
                seen.add(path)
                records.append(path)
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="regenerate_review_sidecar.py",
        description=(
            "Regenerate missing review stats sidecars from their own "
            "records' Markdown (the defective-pair repair tool). Refusals "
            "are recorded outcomes; the exit code is 0 whenever the run "
            "completed and printed its census."
        ),
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="review record paths (a directory is scanned for defective "
        "candidates)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the would-repair and would-refuse sets and write "
        "nothing",
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        default=None,
        help="write the repair census to this receipt file (real runs "
        "only; a dry run writes nothing)",
    )
    args = parser.parse_args(argv)

    records = _collect_records(args.paths)
    lines: list[str] = []
    repaired = 0
    refused = 0
    for record in records:
        status, reason = repair_record(record, dry_run=args.dry_run)
        if status in ("repaired", "would-repair"):
            lines.append(f"{status}: {record}")
            repaired += 1
        else:
            lines.append(f"{status}: {record} ({reason})")
            refused += 1
    mode = "dry run" if args.dry_run else "repair"
    header = (
        f"{mode} census: {len(records)} candidate record(s); "
        f"{'would-repair' if args.dry_run else 'repaired'}={repaired} "
        f"{'would-refuse' if args.dry_run else 'refused'}={refused}"
    )
    print(header)
    for line in lines:
        print(line)
    if args.receipt is not None:
        if args.dry_run:
            print("dry run: the receipt file was not written")
        else:
            args.receipt.write_text(
                "\n".join([header] + lines) + "\n", encoding="utf-8"
            )
            print(f"receipt: {args.receipt}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
