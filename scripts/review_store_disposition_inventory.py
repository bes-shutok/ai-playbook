#!/usr/bin/env python3
"""Review-store disposition inventory (plan 2026-10-02-review-store-disposition-reconciliation.md, Task 1).

Enumerates the canonical records of the review record store
(``docs/reviews/``, a gitignored store of ``.md`` + ``.stats.json`` pairs)
and writes a markdown ledger skeleton naming every un-dispositioned
finding and unresolved blocking series.

Canonical-record selection spells the same exclusions the
``scripts/review_record_selection.py`` selection contract enforces
(importing that module would drag in its slug-argument surface, so the
exclusions are re-spelled here and pinned by the selftest): the
``.backup-<timestamp>`` copies are never enumerated, ``.md.stats.json``
doubles are not canonical, and an orphan half (a sidecar without its
``.md`` twin) is not a review record.

Blocking-signal normalization keys on the absence of each aggregate,
never on the ``counts`` key, because the store spans at least three
schema eras:

1. ``counts.blocking_open`` (current era);
2. top-level ``blocking_open_count`` (legacy era);
3. ``blocking_totals.blocking`` (legacy era);
4. the count of findings whose own ``blocking`` flag is true, when
   ``findings`` is a list of dicts (oldest era).

Records with a findings list where none of these resolve are inventoried
as ``schema: unknown-blocking`` and are NEVER silently treated as zero.
Records whose valid JSON carries a non-list ``findings`` value defeat
even these arms: they are skipped and counted in the skipped-shape
count, never silently dropped.

Triage normalization maps the store's real vocabulary onto
{terminal, un-dispositioned, unmapped}: the canonical terminal values
(``fixed``, ``folded``, and the equivalents in TERMINAL_TRIAGE below)
are excluded from the ledger; the known non-terminal values
(``open``, ``fix``, ``pending``) and an absent triage key are included
as un-dispositioned; everything else is unmapped and is BOTH included
as un-dispositioned AND surfaced in the unmapped-triage section, so the
mapping's blind spots stay visible instead of silent.

Exit codes: 0 when the inventory is written (any result, including
empty); 2 on tool failure (store directory missing or unreadable, or
malformed JSON). There is no exit-1 semantic: the guard family reserves
1 for a gate's semantic negative, and an inventory writer has none.

Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

BACKUP_INFIX = ".backup-"

DEFAULT_REVIEWS_DIR = Path("docs/reviews")

# Canonical terminal triage values (the mapping table the plan delegates to
# the script). The origin's defect statement bounds the terminal set: triage
# in {recorded, deferred, dropped, pending} is exactly the un-dispositioned
# vocabulary, so only the fixed/folded family (and prose sentences that
# themselves record a resolution) is terminal. Prefix forms cover the
# store's prose-compound resolutions ("resolved-by-descope: ...",
# "folded pre-descope: ...", "died with the Task 4 descope").
TERMINAL_TRIAGE_EXACT = {
    "fixed",
    "folded",
    "done",
}
TERMINAL_TRIAGE_PREFIXES = (
    "fixed ",
    "resolved",
    "folded ",
    "died with",
)
KNOWN_UNDISPOSITIONED_TRIAGE = {
    "open",
    "fix",
    "pending",
    "drop",
    "dropped",
    "deferred",
    "deferred-backlog",
    "backlogged",
    "backlog",
    "recorded",
}

ROUND_SUFFIX = re.compile(r"^(?P<base>.*)-r(?P<round>\d+)$")

SUMMARY_LINE = (
    "inventory: {findings} findings, {series} series, "
    "{records} records scanned, {skipped} skipped-shape, {unknown} unknown-blocking"
)


@dataclass
class CanonicalRecord:
    filename: str
    base: str
    slug: str
    round: int | None
    findings: list
    blocking_signal: int | None  # None = unknown-blocking


@dataclass
class Inventory:
    records_scanned: int = 0
    skipped_shape: int = 0
    unknown_blocking: int = 0
    finding_rows: list = field(default_factory=list)
    series_rows: list = field(default_factory=list)
    unmapped: list = field(default_factory=list)


def _triage_class(triage_value) -> tuple[str, str]:
    """Return (normalized-triage, unmapped-detail) for a triage value."""
    if triage_value is None:
        # an explicit JSON null is unmapped, not absent: include it AND
        # surface it in the unmapped-triage section
        return ("null", "null")
    if not isinstance(triage_value, str):
        return (str(triage_value), "")
    lowered = triage_value.strip().lower()
    if lowered in TERMINAL_TRIAGE_EXACT:
        return ("terminal", "")
    if any(lowered.startswith(prefix) for prefix in TERMINAL_TRIAGE_PREFIXES):
        return ("terminal", "")
    if lowered in KNOWN_UNDISPOSITIONED_TRIAGE:
        return (lowered, "")
    return (triage_value.strip(), triage_value.strip())


def _blocking_signal(record: dict, findings: list) -> int | None:
    counts = record.get("counts")
    if isinstance(counts, dict) and "blocking_open" in counts:
        return counts["blocking_open"]
    if "blocking_open_count" in record:
        return record["blocking_open_count"]
    totals = record.get("blocking_totals")
    if isinstance(totals, dict) and "blocking" in totals:
        return totals["blocking"]
    if isinstance(findings, list) and all(isinstance(f, dict) for f in findings):
        return sum(1 for f in findings if f.get("blocking") is True)
    return None


def _parse_name(filename: str) -> tuple[str, str, int | None] | None:
    """Return (base, slug, round) for a canonical sidecar filename, else None."""
    if not filename.endswith(".stats.json"):
        return None
    base = filename[: -len(".stats.json")]
    if BACKUP_INFIX in base:
        return None
    if base.endswith(".md"):
        return None  # .md.stats.json double
    match = ROUND_SUFFIX.match(base)
    if match:
        return (base, match.group("base"), int(match.group("round")))
    return (base, base, None)


def enumerate_canonical(reviews_dir: Path) -> list[Path]:
    """Canonical sidecars: backups, .md.stats.json doubles, and orphan halves
    (a sidecar without its .md twin) are excluded, per the selection
    contract the module docstring spells."""
    canonical = []
    for sidecar in sorted(reviews_dir.glob("*.stats.json")):
        parsed = _parse_name(sidecar.name)
        if parsed is None:
            continue
        if not (reviews_dir / (parsed[0] + ".md")).is_file():
            continue  # orphan half
        canonical.append(sidecar)
    return canonical


def load_record(path: Path) -> dict:
    return json.loads(path.read_text())


def run_inventory(reviews_dir: Path) -> tuple[Inventory, list[str]]:
    """Return (inventory, warnings); raise ToolFailure on unreadable input."""
    if not reviews_dir.is_dir():
        raise ToolFailure(f"review store directory missing or unreadable: {reviews_dir}")
    inv = Inventory()
    warnings: list[str] = []
    by_slug: dict[str, list[CanonicalRecord]] = {}
    for sidecar in enumerate_canonical(reviews_dir):
        inv.records_scanned += 1
        try:
            record = load_record(sidecar)
        except json.JSONDecodeError as exc:
            raise ToolFailure(f"malformed JSON in {sidecar.name}: {exc}") from exc
        if not isinstance(record, dict):
            inv.skipped_shape += 1
            continue
        parsed = _parse_name(sidecar.name)
        assert parsed is not None
        base, slug, round_number = parsed
        findings = record.get("findings")
        if findings is None or not isinstance(findings, list):
            # a non-list (int, dict) or absent findings value defeats even the
            # per-finding arm: skipped and counted, never silently dropped
            inv.skipped_shape += 1
            continue
        if findings and not all(isinstance(f, dict) for f in findings):
            # a findings list the per-finding arm cannot read: the blocking
            # signal is unknown; the record is inventoried in the findings
            # table as unknown-blocking and is never silently treated as zero
            inv.unknown_blocking += 1
            inv.finding_rows.append((slug, round_number, "-", "", "", "unknown-blocking", ""))
            continue
        signal = _blocking_signal(record, findings)
        if signal is None:
            inv.unknown_blocking += 1
        rec = CanonicalRecord(base, base, slug, round_number, findings, signal)
        by_slug.setdefault(slug, []).append(rec)
    for slug, records in sorted(by_slug.items()):
        records.sort(key=lambda r: (r.round is None, r.round or 0))
        latest = records[-1]
        if latest.blocking_signal is not None and latest.blocking_signal > 0:
            inv.series_rows.append(
                (slug, latest.round, latest.blocking_signal, latest.base)
            )
        for fd in latest.findings:
            raw_triage = fd.get("triage", "__absent__")
            if raw_triage == "__absent__":
                normalized, unmapped_detail = ("absent", "")
            else:
                normalized, unmapped_detail = _triage_class(raw_triage)
            if normalized == "terminal":
                continue
            consequence = str(fd.get("consequence", ""))
            if len(consequence) > 140:
                consequence = consequence[:140]
            row = (
                slug,
                latest.round,
                fd.get("id"),
                fd.get("severity", ""),
                fd.get("pattern", ""),
                normalized,
                consequence,
            )
            inv.finding_rows.append(row)
            if unmapped_detail:
                inv.unmapped.append((slug, latest.round, unmapped_detail))
    return inv, warnings


class ToolFailure(Exception):
    pass


def render(inv: Inventory) -> str:
    lines: list[str] = []
    lines.append("# Review-store disposition ledger")
    lines.append("")
    lines.append(
        "Standing bookkeeping duty: every future un-dispositioned finding receives a "
        "terminal line or a backlog row at the owning plan's completion pass. Ledger "
        "lines survive `scripts/review_retention.py` pruning because each line names "
        "the store filename it dispositions."
    )
    lines.append("")
    lines.append("## store-derived")
    lines.append("")
    lines.append("### Un-dispositioned findings (latest round per series)")
    lines.append("")
    if inv.finding_rows:
        lines.append("| slug | round | id | severity | pattern | triage | consequence |")
        lines.append("|---|---|---|---|---|---|---|")
        for slug, rnd, fid, severity, pattern, triage, consequence in inv.finding_rows:
            rnd_text = "r%d" % rnd if rnd is not None else "-"
            cons = consequence.replace("|", "\\|").replace("\n", " ")
            pat = str(pattern).replace("|", "\\|")
            lines.append(
                f"| {slug} | {rnd_text} | {fid} | {severity} | {pat} | {triage} | {cons} |"
            )
    else:
        lines.append("(none)")
    lines.append("")
    lines.append("### Unresolved blocking series (latest round blocking signal > 0)")
    lines.append("")
    if inv.series_rows:
        lines.append("| slug | round | blocking signal | record |")
        lines.append("|---|---|---|---|")
        for slug, rnd, signal, base in inv.series_rows:
            rnd_text = "r%d" % rnd if rnd is not None else "-"
            lines.append(f"| {slug} | {rnd_text} | {signal} | {base} |")
    else:
        lines.append("(none)")
    lines.append("")
    lines.append("### Unmapped triage values")
    lines.append("")
    if inv.unmapped:
        lines.append("| slug | round | triage value |")
        lines.append("|---|---|---|")
        for slug, rnd, detail in inv.unmapped:
            rnd_text = "r%d" % rnd if rnd is not None else "-"
            detail = detail.replace("|", "\\|").replace("\n", " ")
            lines.append(f"| {slug} | {rnd_text} | {detail} |")
    else:
        lines.append("(none)")
    lines.append("")
    lines.append(
        f"schema: unknown-blocking records: {inv.unknown_blocking}; "
        f"skipped-shape records: {inv.skipped_shape}"
    )
    lines.append("")
    lines.append("## receipt-derived")
    lines.append("")
    lines.append("(populated from state-file receipts by the reconciliation pass)")
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="review_store_disposition_inventory")
    sub = parser.add_subparsers(dest="command", required=True)
    run_p = sub.add_parser("inventory", help="write the ledger skeleton")
    run_p.add_argument("--repo", required=True, help="repository root")
    run_p.add_argument("--reviews-dir", default=str(DEFAULT_REVIEWS_DIR))
    run_p.add_argument("--out", required=True, help="output markdown path")
    return parser


def main(argv: list[str] | None = None) -> tuple[int, str]:
    args = build_parser().parse_args(argv)
    if args.command != "inventory":  # pragma: no cover - argparse enforced
        return 2, "unknown command\n"
    reviews_dir = Path(args.repo) / args.reviews_dir
    try:
        inv, _warnings = run_inventory(reviews_dir)
    except ToolFailure as exc:
        return 2, f"inventory: tool failure: {exc}\n"
    text = render(inv)
    out_path = Path(args.out)
    if out_path.parent and not out_path.parent.is_dir():
        out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text)
    summary = SUMMARY_LINE.format(
        findings=len(inv.finding_rows),
        series=len(inv.series_rows),
        records=inv.records_scanned,
        skipped=inv.skipped_shape,
        unknown=inv.unknown_blocking,
    )
    return 0, summary + "\n"


if __name__ == "__main__":
    rc, message = main()
    sys.stdout.write(message)
    sys.exit(rc)
