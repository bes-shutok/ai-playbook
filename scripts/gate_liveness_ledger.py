#!/usr/bin/env python3
"""Guard liveness ledger: count what guards actually catch and actually cost.

The prove-first metric for the guard stack (origin
docs/history/backlog/2026-10-05-done-guard-stack-liveness-economics.md;
operator directive 2026-10-05, doctrine in
projects/.ai-playbook/agent_workflow_guidelines.md section 64): a guard
proposal records the observed case count and the actual time lost of its
harm class BEFORE the guard is designed or planned, and every live firing
of an existing guard is recorded here afterward, so retirement and
narrowing decisions read a measured catch-to-incident ratio instead of
anecdotes.

Subcommands:
  show    Print per-guard tallies and the stack ratio. Final OUTCOME: pass.
  record  Append one row (kind catch | incident | basis | override) and print
          the guard's updated tally. catch: the firing stopped real harm.
          incident: the firing blocked or misdirected valid work.
          basis: the prove-first cost basis of a guard PROPOSAL
          (--harm-cases and --time-lost-minutes required).
          override: an operator-directed interactive proceed past a tripped
          deferral-class gate (the user-directed-override rule), recorded so
          the false-refusal cost stays visible at the next census.

Outcome contract (scripts/OUTCOME_CONTRACT.md, register row added by the
2026-10-05 review fold): every run ends with a final OUTCOME: line on
stdout. Exit 0 pass; exit 3 tool_error (missing or corrupt ledger, usage
violation through the parser override, unexpected failure through the
catch-all, invalid row input). This is a recorder, not a gate: it has no
modeled fail or indeterminate class. --help stays a metadata exit.

Stdlib only; repo-relative paths only; no PII.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

SCHEMA_VERSION = 1
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
KINDS = ("catch", "incident", "basis", "override")


def default_ledger_path() -> Path:
    return Path(__file__).resolve().parent / "gate_liveness_ledger.json"


class ToolError(Exception):
    """Usage, environment, or corrupt-input failure: exit 3, tool_error."""


class ContractParser(argparse.ArgumentParser):
    """Argparse whose usage violations answer as tool error, not exit 2."""

    def error(self, message: str) -> None:  # type: ignore[override]
        print(f"gate_liveness_ledger: {message}", file=sys.stderr)
        print("OUTCOME: tool_error")
        raise SystemExit(3)


def load_ledger(path: Path) -> dict:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ToolError(f"ledger unreadable at {path}: {exc}")
    try:
        data = json.loads(raw)
    except ValueError as exc:
        raise ToolError(f"ledger is not valid JSON at {path}: {exc}")
    if not isinstance(data, dict) or data.get("schema") != SCHEMA_VERSION:
        raise ToolError(f"ledger schema mismatch at {path}: expected schema {SCHEMA_VERSION}")
    if not isinstance(data.get("guards"), dict):
        raise ToolError(f"ledger guards table missing at {path}")
    return data


def save_ledger(path: Path, data: dict) -> None:
    # Atomic write (red-on-main-baseline-repair-and-auto-demote plan, Task 3):
    # a concurrent reader (the pins suite's recorded-red consult) must never
    # observe a torn file, so the payload lands in a sibling temp file and is
    # os.replace'd into place; replace is atomic within one directory.
    tmp_path = path.with_name(path.name + ".tmp")
    try:
        tmp_path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")
        os.replace(tmp_path, path)
    except OSError as exc:
        try:
            tmp_path.unlink()
        except OSError:
            pass
        raise ToolError(f"ledger write failed at {path}: {exc}")


def guard_tally(guard: dict) -> dict:
    rows = [r for r in guard.get("rows", []) if isinstance(r, dict)]
    catches = sum(1 for r in rows if r.get("kind") == "catch")
    incidents = sum(1 for r in rows if r.get("kind") == "incident")
    overrides = sum(1 for r in rows if r.get("kind") == "override")
    time_known = [r["time_lost_minutes"] for r in rows if r.get("time_lost_minutes") is not None]
    bases = [r for r in rows if r.get("kind") == "basis"]
    return {
        "catches": catches,
        "incidents": incidents,
        "overrides": overrides,
        "time_lost_minutes": sum(time_known) if time_known else 0,
        "time_known_rows": len(time_known),
        "basis_rows": len(bases),
    }


def print_report(data: dict, only_guard: str | None) -> int:
    guards = data["guards"]
    names = [only_guard] if only_guard else sorted(guards)
    if only_guard and only_guard not in guards:
        raise ToolError(f"unknown guard: {only_guard}")
    total_catches = 0
    total_incidents = 0
    total_overrides = 0
    for name in names:
        t = guard_tally(guards[name])
        total_catches += t["catches"]
        total_incidents += t["incidents"]
        total_overrides += t["overrides"]
        time_part = f"time_lost_minutes={t['time_lost_minutes']} (known on {t['time_known_rows']} rows)"
        print(f"{name}: catches={t['catches']} incidents={t['incidents']} overrides={t['overrides']} {time_part}")
        if t["catches"] == 0 and t["incidents"] == 0 and t["overrides"] == 0 and t["basis_rows"] == 0:
            note = guards[name].get("notes", "")
            print(f"  note: {note}" if note else "  note: (none)")
        for row in guards[name].get("rows", []):
            if isinstance(row, dict) and row.get("kind") == "basis":
                print(
                    f"  basis: harm_cases={row.get('harm_cases')} "
                    f"time_lost_minutes={row.get('time_lost_minutes')} evidence={row.get('evidence')}"
                )
    print(
        f"TOTAL: catches={total_catches} incidents={total_incidents} "
        f"ratio={total_catches}:{total_incidents} overrides={total_overrides}"
    )
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    data = load_ledger(Path(args.ledger))
    code = print_report(data, args.guard)
    print("OUTCOME: pass")
    return code


def cmd_record(args: argparse.Namespace) -> int:
    if not DATE_RE.match(args.date or ""):
        raise ToolError(f"date must be YYYY-MM-DD: {args.date!r}")
    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError as exc:
        raise ToolError(f"date is not a real calendar date: {args.date} ({exc})")
    if not args.evidence:
        raise ToolError("evidence is required (a repo-relative path or a commit sha)")
    if args.kind == "basis" and (args.harm_cases is None or args.time_lost_minutes is None):
        raise ToolError("basis rows require --harm-cases and --time-lost-minutes")
    path = Path(args.ledger)
    data = load_ledger(path)
    guard = data["guards"].setdefault(args.guard, {"notes": "", "rows": []})
    if not isinstance(guard.get("rows"), list):
        raise ToolError(f"guard rows corrupted for {args.guard}")
    row = {
        "kind": args.kind,
        "date": args.date,
        "evidence": args.evidence,
        "time_lost_minutes": args.time_lost_minutes,
    }
    if args.kind == "basis":
        row["harm_cases"] = args.harm_cases
    if args.note:
        row["note"] = args.note
    guard["rows"].append(row)
    save_ledger(path, data)
    t = guard_tally(guard)
    print(
        f"{args.guard}: catches={t['catches']} incidents={t['incidents']} overrides={t['overrides']} "
        f"time_lost_minutes={t['time_lost_minutes']} (row appended: {args.kind} {args.date})"
    )
    print("OUTCOME: pass")
    return 0


def build_parser() -> ContractParser:
    parser = ContractParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ledger", default=str(default_ledger_path()), help="ledger JSON path")
    sub = parser.add_subparsers(dest="command", required=True)
    p_show = sub.add_parser("show", help="print tallies and the stack ratio")
    p_show.add_argument("--guard", default=None, help="restrict the report to one guard")
    p_show.set_defaults(func=cmd_show)
    p_rec = sub.add_parser("record", help="append one row")
    p_rec.add_argument("--guard", required=True)
    p_rec.add_argument("--kind", required=True, choices=KINDS)
    p_rec.add_argument("--date", required=True, help="row date, YYYY-MM-DD")
    p_rec.add_argument("--evidence", required=True, help="repo-relative path or commit sha witnessing the row")
    p_rec.add_argument("--time-lost-minutes", type=int, default=None)
    p_rec.add_argument("--harm-cases", type=int, default=None, help="basis rows only: observed case count")
    p_rec.add_argument("--note", default="")
    p_rec.set_defaults(func=cmd_record)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except ToolError as exc:
        print(f"gate_liveness_ledger: {exc}", file=sys.stderr)
        print("OUTCOME: tool_error")
        return 3
    except Exception as exc:  # the contract's no-line rule: a crash is a tool error, never a silent exit
        print(f"gate_liveness_ledger: unexpected failure: {exc!r}", file=sys.stderr)
        print("OUTCOME: tool_error")
        return 3


if __name__ == "__main__":
    sys.exit(main())
