#!/usr/bin/env python3
"""Backlog root closure rescan: the done-corpus sweep's verification carrier.

Answers one question mechanically: how many closure-declared backlog
roots are still fold-less outside the sweep record's skip set, and did
every recorded fold-and-delete actually fold? Reuses ``classify_origin``
and the fold-then-delete consult helpers from
``scripts/check_plan_origins_closed.py``. The GREEN end-state is a
printed 0 and exit 0; the pre-sweep corpus exits non-zero with a
non-zero printed count (the RED census witness).

Census arm: every date-stamped ``.md`` file at the backlog top level is
classified; a root classifying ``closed`` (status closed/done) or
``covered`` (status covered with a covering-plan witness) outside the
skip set is one fold-less root finding. Open roots are not
closure-declared and never count; the completed tree is not this
script's surface (the dated-file find line owns it).

Record arm: with ``--skip-from-record`` the script parses the sweep
record's adjudication table for the skip set and the fold anchors.
The record grammar is pinned: ONE pipe table under a fixed heading
(a ``Sweep record`` heading, e.g.
``## Sweep record (2026-10-01-done-origin-fold-delete-enforcement)``)
whose header row is exactly::

    path | outcome | covering plan

with the closed outcome vocabulary ``fold-and-delete | delete-no-fold |
skip``; skip rows live in the same table. Every row's path cell
contributes its filename stem to the reconciliation count: ``skip``
rows join the skip set, ``fold-and-delete`` rows must name a covering
plan in the covering-plan cell, and that plan must carry the
``## Disposition of migrated backlog items`` section boundary-anchoring
the item's basename (the existing consult helpers); each missing anchor
counts into the same total as a fold-less root. ``delete-no-fold`` rows
(recoverable-via-git-history deletions) require no anchor.

``--expect-removed <n>`` cross-checks the record's adjudicated rows plus
skip rows against n and fails on mismatch, so the record reconciles
file-for-file with the RED census; it requires ``--skip-from-record``.

Exit codes: 0 only when the total is 0 (a bare run with no skips and no
record is valid); 1 when any fold-less root or missing anchor is found;
2 on usage errors, an unreadable or grammatically malformed record, or
an ``--expect-removed`` mismatch (the reconciliation is a different
failure class from closure findings).

Read-only (no side effects); stdlib only. Paths resolve from arguments
and the repo facts file (``.ai-playbook/facts.md``, keys ``backlog_dir``
and ``backlog_completed_dir``) anchored at the repo root with
conventional repo-relative defaults; no machine-specific absolute path
is hardcoded.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_plan_origins_closed import (
    DEFAULT_BACKLOG_DIR,
    DEFAULT_COMPLETED_DIR,
    _disposition_consult,
    classify_origin,
    resolve_dir,
    resolve_repo_root,
)

# Root census scope: the backlog top level's dated item files (the
# corpus's item convention; non-dated files such as PLAN-PROMPTS.md are
# not backlog items and never classify).
DATE_STAMPED_ITEM_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-.*\.md$")

# Closure-declared classify_origin states whose roots owe the
# fold-and-delete disposal.
FOLD_LESS_STATES = ("closed", "covered")

# Sweep record grammar (pinned).
RECORD_HEADING_RE = re.compile(r"^\s*#{1,6}\s+sweep\s+record\b", re.IGNORECASE)
RECORD_HEADER_CELLS = ("path", "outcome", "covering plan")
OUTCOME_FOLD = "fold-and-delete"
OUTCOME_DELETE = "delete-no-fold"
OUTCOME_SKIP = "skip"
OUTCOME_VOCABULARY = (OUTCOME_FOLD, OUTCOME_DELETE, OUTCOME_SKIP)
_SEPARATOR_CELL_RE = re.compile(r":?-{1,}:?")
_MD_SUFFIX_RE = re.compile(r"\.md$", re.IGNORECASE)


class RecordError(Exception):
    """Unreadable or grammatically malformed sweep record (exit 2)."""


def normalize_slug(raw: str) -> str:
    """One slug form: the date-stamped filename stem.

    Accepts a bare stem (``2026-09-20-example-origin-item``) or an
    ``.md`` path (``docs/history/backlog/2026-09-20-example-origin-item.md``,
    backtick quoting tolerated); both normalize to the filename stem.
    """
    text = raw.strip().strip("`")
    return _MD_SUFFIX_RE.sub("", Path(text).name)


def _split_row(line: str) -> list[str]:
    stripped = line.strip()
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def parse_sweep_record(record_path: Path) -> tuple[set[str], list[dict]]:
    """Parse the pinned sweep-record grammar.

    Returns ``(skip stems, rows)``; each row dict carries ``path``
    (raw cell), ``stem``, ``outcome``, ``covering`` (raw cell), and
    ``lineno``. Raises ``RecordError`` on an unreadable file, a missing
    record heading, a first table whose header differs from the pinned
    one, a shifted row, an out-of-vocabulary outcome, an empty path
    cell, a duplicate path, or a fold-and-delete row naming no covering
    plan.
    """
    try:
        text = record_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise RecordError(f"cannot read sweep record {record_path}: {exc}")
    lines = text.splitlines()
    heading_index = next(
        (i for i, line in enumerate(lines) if RECORD_HEADING_RE.match(line)),
        None,
    )
    if heading_index is None:
        raise RecordError(
            f"no 'Sweep record' heading found in {record_path}"
        )
    header_index = None
    for i in range(heading_index + 1, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith("#"):
            break  # the section ended before any table opened
        if not stripped.startswith("|"):
            continue
        cells = [cell.lower() for cell in _split_row(lines[i])]
        if cells != list(RECORD_HEADER_CELLS):
            raise RecordError(
                f"the first table under the Sweep record heading at "
                f"{record_path}:{i + 1} has header cells {cells}; expected "
                f"{list(RECORD_HEADER_CELLS)}"
            )
        header_index = i
        break
    if header_index is None:
        raise RecordError(
            f"no '{' | '.join(RECORD_HEADER_CELLS)}' table under the "
            f"Sweep record heading in {record_path}"
        )
    skip_stems: set[str] = set()
    rows: list[dict] = []
    seen_stems: dict[str, int] = {}
    for i in range(header_index + 1, len(lines)):
        stripped = lines[i].strip()
        if not stripped.startswith("|"):
            break  # the record table ended
        cells = _split_row(lines[i])
        if cells and all(
            _SEPARATOR_CELL_RE.fullmatch(cell) for cell in cells
        ):
            continue  # separator row (any GFM alignment form)
        if len(cells) != len(RECORD_HEADER_CELLS):
            raise RecordError(
                f"sweep record row at {record_path}:{i + 1} has "
                f"{len(cells)} cell(s), expected "
                f"{len(RECORD_HEADER_CELLS)}; a shifted row would silently "
                f"misassign the reconciliation"
            )
        path_cell, outcome, covering = cells
        if outcome not in OUTCOME_VOCABULARY:
            raise RecordError(
                f"sweep record row at {record_path}:{i + 1} has outcome "
                f"'{outcome}'; expected one of "
                f"{' | '.join(OUTCOME_VOCABULARY)}"
            )
        if not path_cell:
            raise RecordError(
                f"sweep record row at {record_path}:{i + 1} has an empty "
                f"path cell"
            )
        stem = normalize_slug(path_cell)
        if stem in seen_stems:
            raise RecordError(
                f"sweep record names {path_cell} twice (rows "
                f"{seen_stems[stem]} and {i + 1}); the reconciliation must "
                f"stay file-for-file"
            )
        seen_stems[stem] = i + 1
        if outcome == OUTCOME_FOLD and not covering:
            raise RecordError(
                f"sweep record fold-and-delete row at {record_path}:{i + 1} "
                f"names no covering plan"
            )
        rows.append(
            {
                "path": path_cell,
                "stem": stem,
                "outcome": outcome,
                "covering": covering,
                "lineno": i + 1,
            }
        )
        if outcome == OUTCOME_SKIP:
            skip_stems.add(stem)
    return skip_stems, rows


def census_fold_less_roots(
    backlog_dir: Path, completed_dir: Path, skip_stems: set[str]
) -> tuple[list[tuple[str, str, str]], int]:
    """Classify every dated backlog root; return the fold-less findings
    outside the skip set as ``(name, state, detail)`` triples plus the
    count of roots the skip set spared."""
    findings: list[tuple[str, str, str]] = []
    spared = 0
    for path in sorted(backlog_dir.iterdir()):
        if not path.is_file() or not DATE_STAMPED_ITEM_RE.match(path.name):
            continue
        state, detail = classify_origin(path.name, backlog_dir, completed_dir)
        if state not in FOLD_LESS_STATES:
            continue
        if normalize_slug(path.name) in skip_stems:
            spared += 1
            continue
        findings.append((path.name, state, detail))
    return findings, spared


def check_fold_anchors(
    rows: list[dict], repo_root: Path
) -> list[str]:
    """Every fold-and-delete row whose covering plan lacks the
    ``## Disposition of migrated backlog items`` anchor boundary-anchoring
    the item's basename (the existing consult helpers), as finding lines."""
    problems: list[str] = []
    for row in rows:
        if row["outcome"] != OUTCOME_FOLD:
            continue
        item_name = Path(row["path"]).name
        covering = row["covering"]
        plan_path = Path(covering)
        if not plan_path.is_absolute():
            plan_path = repo_root / plan_path
        if not plan_path.is_file():
            problems.append(
                f"fold-and-delete anchor missing: {item_name} -> covering "
                f"plan not found: {covering}"
            )
            continue
        try:
            plan_text = plan_path.read_text(
                encoding="utf-8", errors="replace"
            )
        except OSError as exc:
            problems.append(
                f"fold-and-delete anchor missing: {item_name} -> covering "
                f"plan unreadable: {covering} ({exc})"
            )
            continue
        if not _disposition_consult(plan_text, item_name):
            problems.append(
                f"fold-and-delete anchor missing: {item_name} is not "
                f"boundary-anchored in {covering}'s "
                f"'## Disposition of migrated backlog items' section"
            )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Count fold-less closure-declared (done/covered) backlog roots "
            "outside the sweep record's skip set; exit 0 only at 0"
        )
    )
    parser.add_argument(
        "--skip-from-record",
        dest="skip_from_record",
        metavar="PATH",
        help=(
            "sweep record carrying the pinned adjudication table "
            "(its skip rows join the skip set; its fold-and-delete rows "
            "are anchor-checked)"
        ),
    )
    parser.add_argument(
        "--skip-slug",
        dest="skip_slugs",
        action="append",
        default=[],
        metavar="SLUG",
        help=(
            "skip one slug for this ad-hoc run (a date-stamped stem or "
            ".md path); repeatable"
        ),
    )
    parser.add_argument(
        "--expect-removed",
        dest="expect_removed",
        type=int,
        metavar="N",
        help=(
            "cross-check the record's adjudicated rows plus skip rows "
            "against N; fails on mismatch (requires --skip-from-record)"
        ),
    )
    parser.add_argument(
        "--repo-root",
        help=(
            "repository root anchoring facts and relative paths "
            "(default: git toplevel of the current directory)"
        ),
    )
    parser.add_argument(
        "--backlog-dir",
        help="backlog top-level directory (overrides the facts key backlog_dir)",
    )
    parser.add_argument(
        "--completed-dir",
        help=(
            "completed directory "
            "(overrides the facts key backlog_completed_dir)"
        ),
    )
    args = parser.parse_args(argv)

    if args.expect_removed is not None:
        if args.skip_from_record is None:
            parser.error("--expect-removed requires --skip-from-record")
        if args.expect_removed < 0:
            parser.error("--expect-removed must be >= 0")

    skip_stems = {normalize_slug(slug) for slug in args.skip_slugs}
    rows: list[dict] = []
    if args.skip_from_record is not None:
        record_path = Path(args.skip_from_record).expanduser()
        if not record_path.is_absolute():
            repo_root_hint = resolve_repo_root(args.repo_root)
            record_path = repo_root_hint / record_path
        if not record_path.is_file():
            print(
                f"error: sweep record not found: {record_path}",
                file=sys.stderr,
            )
            return 2
        try:
            record_skips, rows = parse_sweep_record(record_path)
        except RecordError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        skip_stems |= record_skips

    repo_root = resolve_repo_root(args.repo_root)
    backlog_dir = resolve_dir(
        args.backlog_dir, repo_root, "backlog_dir", DEFAULT_BACKLOG_DIR
    )
    completed_dir = resolve_dir(
        args.completed_dir,
        repo_root,
        "backlog_completed_dir",
        DEFAULT_COMPLETED_DIR,
    )
    if not backlog_dir.is_dir():
        print(f"error: backlog directory not found: {backlog_dir}", file=sys.stderr)
        return 2

    findings, spared = census_fold_less_roots(
        backlog_dir, completed_dir, skip_stems
    )
    anchor_problems = check_fold_anchors(rows, repo_root)

    total = len(findings) + len(anchor_problems)
    for name, state, detail in findings:
        print(f"fold-less root: {name} ({state}: {detail})")
    for line in anchor_problems:
        print(line)
    if args.skip_from_record is not None:
        outcomes = [row["outcome"] for row in rows]
        print(
            f"record: {len(rows)} row(s) "
            f"({outcomes.count(OUTCOME_SKIP)} skip, "
            f"{outcomes.count(OUTCOME_FOLD)} fold-and-delete, "
            f"{outcomes.count(OUTCOME_DELETE)} delete-no-fold); "
            f"{spared} root(s) spared by the skip set"
        )
    elif spared or skip_stems:
        print(f"{spared} root(s) spared by the ad-hoc skip set")

    exit_code = 1 if total else 0
    if args.expect_removed is not None:
        total_rows = len(rows)
        if total_rows != args.expect_removed:
            print(
                f"expect-removed mismatch: record rows (adjudicated "
                f"{total_rows - outcomes.count(OUTCOME_SKIP)} + skip "
                f"{outcomes.count(OUTCOME_SKIP)}) = {total_rows}, "
                f"expected {args.expect_removed}; the sweep record must "
                f"reconcile file-for-file with the census"
            )
            exit_code = 2
    print(
        f"check_backlog_root_closure: {total} fold-less closure-declared "
        f"root(s) outside the skip set; exit {exit_code}"
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
