#!/usr/bin/env python3
"""Skill-text byte-budget gate (plan 2026-10-10-maintenance-skill-size-refactor.md, Task 2;
promoted to blocking 2026-11-10 by plan 2026-11-07-operative-file-read-budget-gate.md,
Task 1, through this docstring's own reserved criteria).

Fleet-wide byte budgets over every ``agents/skills/*/[A-Za-z]*.md`` skill
file. The gate measures growth the landing loop cannot otherwise see.

Posture (promoted 2026-11-10): the promotion criteria further down fired on
the first true catch - the fourteen-refusal single-read inventory recorded in
``docs/history/backlog/2026-11-07-operative-files-exceed-read-tool-single-read-cap.md`` -
so the gate is BLOCKING on the single-read ceiling class and advisory on the
per-file ratchet caps. Breach taxonomy:

- ceiling class (blocking): a skill file whose byte size exceeds the
  single-read ceiling (``SINGLE_READ_CEILING``; the caps table's metadata
  carries the calibration derivation - the binding witnessed pairing is
  111845 bytes refused at 27432 tokens, 4.08 bytes per token, so the ceiling
  sits inside the 25000-token budget by about 490 tokens at the worst
  pairing, and the calibration's safety rides the breach row naming any file
  the Read tool still refuses, not a wide numeric margin). The blocking
  breach report is the split set of record (load-on-dispatch, the learn
  router precedent).
- ratchet-cap breaches (advisory): a file over its own per-file cap prints
  exactly the advisory line the warning-only gate printed; the ratchet's
  growth-watch doctrine (lower on shrink, seed with margin, never raise) is
  unchanged, and these rows never move an exit code.
- rolling-log class (informational): the two rolling prompt logs
  (``docs/history/backlog/PLAN-PROMPTS.md`` and ``EXEC-PROMPTS.md``)
  measured against the Read tool's 262144-byte hard cap; informational rows
  never move an exit code, and the logs' size governance stays with their
  existing prune and freeze duties.

Admission test (machinery audit Part 5 item 2; the measured analysis
``docs/maintenance/maintenance-skill-refactor-analysis-2026-10-09.md``):
the maintenance corpus grew 18KB to 357KB in 24 days across 35 commits with
exactly ONE 64-byte shrink (the one-shrink ratchet), and every scheduler turn
and child dispatch loads the doctrine before working (~89K tokens per turn at
the measured corpus size). A breach line is the catch: any landing that grows
a file past its cap prints one.

Expected catch frequency: one ceiling-class exit 1 while any over-ceiling
skill file exists; one advisory breach line on any landing that grows a file
past its ratchet cap; the gate runs on every pins-suite invocation (the
suite surface, report-only) and standalone wherever blocking enforcement is
wanted.

False-positive cost: the ceiling class blocks only on measured bytes over
the calibrated single-read budget - a file the Read tool would refuse - and
clears by the owning plan's split; the advisory and informational classes
are fail-open by construction, bounded by the seeded margin (per-file cap =
current bytes plus the larger of 25% or 8192 bytes, the caps table being the
tuning surface).

Promotion record: warning-only from 2026-10-10; the reserved criteria below
said a later change promotes the gate to blocking ONLY after its first true
catch (a breach line that identified real growth worth stopping); that
catch is the fourteen-refusal inventory above, and the promotion landed
2026-11-10 in the same change that calibrated the caps table, the machinery
registry row ``script:skill_text_budget.py`` carrying the witness, the
promotion note, and the review date 2027-02-07.

Sunset (two-phase, so no weekly measurement is owed that no consumer owns):
until the growth-telemetry consumer lands (the doc-hygiene row owns that
rider wiring; it stays out of the landing plan's scope), the advisory
classes keep NO removal path - a dormant gate over a still-growing corpus is
never the removal case. When the consumer lands, its first SIX consecutive
weekly windows with zero reported breaches AND non-increasing fleet byte
totals arm the removal the pre-registered machinery-registry removals row
names (``done-skill:landing-cost-record-writer`` sibling posture; the
budget gate's own row carries disposition ``delete``).

Modes (two check surfaces, one ratchet; every operational run prints a final
OUTCOME line - a check/ratchet run or a usage or context failure without one
is a bug; ``--help`` prints help and exits without one):
- ``--check`` (standalone, the blocking surface): report per-file bytes
  versus the ceiling and the caps, caps gaps (a skill file with no caps
  entry is a reported gap line, never a silent skip), the maintenance
  per-section pilot entries (``pilot-pending`` for module files not yet
  created), and the rolling-log rows. Exit 1 with ``OUTCOME: fail`` when
  any ceiling-class file exists, 0 with ``OUTCOME: pass`` when the ceiling
  class is clean, 3 on usage or context errors (``OUTCOME: tool_error``).
- ``--check --suite`` (the pins suite's surface): prints both classes'
  rows plus the informational log rows but ALWAYS exits 0 (``OUTCOME:
  pass``); usage and context errors still exit 3 - the class the suite's
  wiring-failure detection depends on.
- ``--ratchet``: lower a cap when the file shrank below it and seed caps
  for newly created files (cap = current bytes plus the margin, clamped to
  the single-read ceiling so the table never re-grows past the calibrated
  budget); NEVER raise a cap. Writes the caps table back.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFAULT_CAPS_PATH = Path(__file__).resolve().parent / "skill_text_budget_caps.json"
DEFAULT_SKILLS_DIR = Path(__file__).resolve().parent.parent / "agents" / "skills"
MARGIN_FLOOR = 8192
MARGIN_RATIO = 0.25

# The single-read ceiling (plan 2026-11-07-operative-file-read-budget-gate.md
# Task 1): the blocking class. A skill file whose byte size exceeds this
# cannot load whole through the Read tool at the witnessed pairing; the caps
# table's metadata carries the calibration derivation.
SINGLE_READ_CEILING = 100000

# The rolling prompt logs' informational class: the Read tool's own hard
# per-file size cap, not a corpus choice.
TOOL_HARD_CAP = 262144
ROLLING_LOGS = ("PLAN-PROMPTS.md", "EXEC-PROMPTS.md")

# The maintenance per-section pilot: the analysis Part 4 table's per-module
# targets, carried as advisory pilot entries until the split's files exist
# (Task 3 lands them and ratchets their per-file caps; the pilot lines then
# compare the created files' bytes against the Part 4 targets).
PILOT_TARGETS = {
    "agents/skills/maintenance/SKILL.md": 40960,
    "agents/skills/maintenance/survey-arms.md": 46080,
    "agents/skills/maintenance/guards.md": 20480,
    "agents/skills/maintenance/decisions.md": 71680,
    "agents/skills/maintenance/quota-policy.md": 15360,
    "agents/skills/maintenance/scheduling.md": 10240,
    "agents/skills/maintenance/failure-cap.md": 20480,
    "agents/skills/maintenance/state-file.md": 46080,
    # zcode.md carries no Part 4 numeric target ("keep, budget it"): its
    # budget is the per-file cap the ratchet seeded, not a pilot entry
}


def margin_for(size: int) -> int:
    return max(int(size * MARGIN_RATIO), MARGIN_FLOOR)


def skill_files(skills_dir: Path) -> list[Path]:
    return sorted(
        p for p in skills_dir.glob("*/[A-Za-z]*.md") if p.is_file()
    )


def load_caps(path: Path) -> dict:
    if not path.is_file():
        return {"files": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("files", {}), dict):
        raise ValueError("malformed caps table (top-level shape)")
    return data


def lower_caps_to_ceiling(files_caps: dict[str, int]) -> dict[str, int]:
    """The 2026-11-10 calibration as a named operation (the caps table's
    metadata records the same derivation): every cap above the single-read
    ceiling drops to it; a cap at or below the ceiling stays. Lowering is
    the ratchet's sanctioned direction; the never-raise rule is untouched."""
    return {rel: min(cap, SINGLE_READ_CEILING) for rel, cap in files_caps.items()}


def rel_path(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def run_check(
    caps_path: Path,
    skills_dir: Path,
    repo_root: Path,
    backlog_dir: Path,
    suite: bool,
) -> int:
    caps = load_caps(caps_path)
    files_caps: dict[str, int] = caps.get("files", {})
    ceiling_lines = 0
    breach_lines = 0
    gap_lines = 0
    seen: set[str] = set()
    for path in skill_files(skills_dir):
        rel = rel_path(path, repo_root)
        seen.add(rel)
        size = path.stat().st_size
        if size > SINGLE_READ_CEILING:
            print(
                f"CEILING BREACH (blocking): {rel} {size} bytes > "
                f"single-read ceiling {SINGLE_READ_CEILING}"
            )
            ceiling_lines += 1
        cap = files_caps.get(rel)
        if cap is None:
            print(f"CAPS GAP (advisory): {rel} has no caps entry ({size} bytes)")
            gap_lines += 1
        elif size > cap:
            print(f"BREACH (advisory): {rel} {size} bytes > cap {cap}")
            breach_lines += 1
    for rel in sorted(set(files_caps) - seen):
        print(f"STALE CAP (advisory): {rel} caps entry names no on-disk skill file")
    pilot_pending = 0
    for rel, target in sorted(PILOT_TARGETS.items()):
        path = repo_root / rel
        if not path.is_file():
            print(f"PILOT PENDING (advisory): {rel} not yet created (Part 4 target {target} bytes)")
            pilot_pending += 1
        else:
            size = path.stat().st_size
            if size > target:
                print(f"PILOT OVER (advisory): {rel} {size} bytes > Part 4 target {target}")
    log_rows = 0
    for name in ROLLING_LOGS:
        path = backlog_dir / name
        rel = rel_path(path, repo_root)
        if not path.is_file():
            print(f"LOG (informational): {rel} not present (no measurement)")
        else:
            size = path.stat().st_size
            if size > TOOL_HARD_CAP:
                print(f"LOG OVER (informational): {rel} {size} bytes > tool hard cap {TOOL_HARD_CAP}")
            else:
                print(f"LOG (informational): {rel} {size} bytes <= tool hard cap {TOOL_HARD_CAP}")
        log_rows += 1
    posture = (
        "suite posture (report-only, never moves the exit)" if suite else "blocking posture"
    )
    print(
        f"skill-text budget: {ceiling_lines} ceiling breach(es) (blocking), "
        f"{breach_lines} ratchet breach line(s) (advisory), {gap_lines} caps gap(s), "
        f"{pilot_pending} pilot-pending module(s), {log_rows} rolling-log row(s) "
        f"(informational); {posture}"
    )
    if ceiling_lines and not suite:
        print("OUTCOME: fail")
        return 1
    print("OUTCOME: pass")
    return 0


def run_ratchet(caps_path: Path, skills_dir: Path, repo_root: Path) -> int:
    caps = load_caps(caps_path)
    files_caps: dict[str, int] = caps.setdefault("files", {})
    lowered = 0
    seeded = 0
    for path in skill_files(skills_dir):
        rel = rel_path(path, repo_root)
        size = path.stat().st_size
        # the calibrated single-read ceiling bounds every seed and lowering
        # (the caps table never re-grows past the budget the ceiling class
        # enforces); the never-raise rule is untouched
        candidate = min(size + margin_for(size), SINGLE_READ_CEILING)
        old = files_caps.get(rel)
        if old is None:
            files_caps[rel] = candidate
            seeded += 1
            print(f"SEEDED: {rel} cap {candidate} ({size} bytes + margin)")
        elif candidate < old:
            files_caps[rel] = candidate
            lowered += 1
            print(f"LOWERED: {rel} cap {old} -> {candidate} (file at {size} bytes)")
        # never raise: a grown file keeps its existing cap (the advisory
        # breach line in --check is the growth signal; the ratchet only
        # tightens)
    caps_path.write_text(json.dumps(caps, indent=2) + "\n", encoding="utf-8")
    print(f"ratchet: {lowered} cap(s) lowered, {seeded} seeded; no cap raised")
    print("OUTCOME: pass")
    return 0


class _OutcomeParser(argparse.ArgumentParser):
    # every run ends in a final OUTCOME line: argparse's own failures exit 3
    # with ``OUTCOME: tool_error`` instead of the bare exit 2 with no
    # OUTCOME line (a run without a final OUTCOME line is a bug)
    def error(self, message: str) -> None:
        print(f"usage error: {message}")
        print("OUTCOME: tool_error")
        sys.exit(3)


def main(argv: list[str] | None = None) -> int:
    parser = _OutcomeParser(
        description="Skill-text byte-budget gate (blocking single-read ceiling; advisory ratchet watch)"
    )
    parser.add_argument("--check", action="store_true", help="report per-file breaches (blocking ceiling class; advisory ratchet rows)")
    parser.add_argument("--suite", action="store_true", help="suite surface: print both classes' rows, always exit 0 (pairs with --check)")
    parser.add_argument("--ratchet", action="store_true", help="lower caps on shrink, seed new files, never raise")
    parser.add_argument("--caps", type=Path, default=DEFAULT_CAPS_PATH, help="caps table path")
    parser.add_argument("--skills-dir", type=Path, default=DEFAULT_SKILLS_DIR, help="skills root to walk")
    parser.add_argument(
        "--backlog-dir",
        type=Path,
        default=None,
        help="rolling prompt-log directory (default: <repo root>/docs/history/backlog)",
    )
    args = parser.parse_args(argv)
    if args.check == args.ratchet or (args.suite and not args.check):
        print("usage error: exactly one of --check or --ratchet is required; --suite pairs with --check only")
        print("OUTCOME: tool_error")
        return 3
    # the relative keys in the caps table resolve against the skills tree's
    # own repo root (the walked tree's parent-of-parent), not the script's
    # location: the hermetic fixtures run the gate over a temp tree
    repo_root = args.skills_dir.resolve().parent.parent
    backlog_dir = (
        args.backlog_dir
        if args.backlog_dir is not None
        else repo_root / "docs" / "history" / "backlog"
    )
    if not args.skills_dir.is_dir():
        print(f"skills dir not found: {args.skills_dir}")
        print("OUTCOME: tool_error")
        return 3
    try:
        if args.check:
            return run_check(args.caps, args.skills_dir, repo_root, backlog_dir, args.suite)
        return run_ratchet(args.caps, args.skills_dir, repo_root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"budget gate could not run reliably: {exc}")
        print("OUTCOME: tool_error")
        return 3


if __name__ == "__main__":
    sys.exit(main())
