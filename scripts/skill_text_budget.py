#!/usr/bin/env python3
"""Skill-text byte-budget gate (plan 2026-10-10-maintenance-skill-size-refactor.md, Task 2).

Fleet-wide, WARNING-ONLY byte budgets over every ``agents/skills/*/[A-Za-z]*.md``
skill file. The gate measures growth the landing loop cannot otherwise see and
reports breaches as advisory lines; a breach NEVER moves the exit code at this
landing.

Admission test (machinery audit Part 5 item 2; the measured analysis
``docs/maintenance/maintenance-skill-refactor-analysis-2026-10-09.md``):
the maintenance corpus grew 18KB to 357KB in 24 days across 35 commits with
exactly ONE 64-byte shrink (the one-shrink ratchet), and every scheduler turn
and child dispatch loads the doctrine before working (~89K tokens per turn at
the measured corpus size). A breach line is the catch: any landing that grows
a file past its cap prints one.

Expected catch frequency: one breach line on any landing that grows a file
past its cap; the gate runs on every pins-suite invocation (per-landing),
read monthly through the pins suite's own reports.

False-positive cost: zero blocking - the gate is fail-open by construction
(advisory lines, exit 0), and false positives are bounded by the seeded
margin (per-file cap = current bytes plus the larger of 25% or 8192 bytes,
the caps table being the tuning surface).

Promotion criteria: the gate stays warning-only within this plan; a later
change promotes it to blocking (exit 1, ``OUTCOME: fail``) ONLY after its
first true catch (a breach line that identified real growth worth stopping).

Sunset (two-phase, so no weekly measurement is owed that no consumer owns):
until the growth-telemetry consumer lands (the doc-hygiene row owns that
rider wiring; it stays out of the landing plan's scope), the gate runs
warning-only with NO removal path - a dormant gate over a still-growing
corpus is never the removal case. When the consumer lands, its first SIX
consecutive weekly windows with zero reported breaches AND non-increasing
fleet byte totals arm the removal the pre-registered machinery-registry
removals row names (``done-skill:landing-cost-record-writer`` sibling
posture; the budget gate's own row carries disposition ``delete``).

Modes:
- ``--check``: report per-file bytes versus cap (advisory breach lines),
  caps gaps (a skill file with no caps entry is a reported gap line, never
  a silent skip), and the maintenance per-section pilot entries
  (``pilot-pending`` for module files not yet created). Always ends
  ``OUTCOME: pass`` while warning-only.
- ``--ratchet``: lower a cap when the file shrank below it and seed caps for
  newly created files (cap = current bytes plus the margin); NEVER raise a
  cap. Writes the caps table back.
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


def run_check(caps_path: Path, skills_dir: Path, repo_root: Path) -> int:
    caps = load_caps(caps_path)
    files_caps: dict[str, int] = caps.get("files", {})
    breach_lines = 0
    gap_lines = 0
    seen: set[str] = set()
    for path in skill_files(skills_dir):
        rel = path.resolve().relative_to(repo_root).as_posix()
        seen.add(rel)
        size = path.stat().st_size
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
    print(
        f"skill-text budget: {breach_lines} breach line(s), {gap_lines} caps gap(s), "
        f"{pilot_pending} pilot-pending module(s); warning-only posture, breach lines never move the exit"
    )
    print("OUTCOME: pass")
    return 0


def run_ratchet(caps_path: Path, skills_dir: Path, repo_root: Path) -> int:
    caps = load_caps(caps_path)
    files_caps: dict[str, int] = caps.setdefault("files", {})
    lowered = 0
    seeded = 0
    for path in skill_files(skills_dir):
        rel = path.resolve().relative_to(repo_root).as_posix()
        size = path.stat().st_size
        candidate = size + margin_for(size)
        old = files_caps.get(rel)
        if old is None:
            files_caps[rel] = candidate
            seeded += 1
            print(f"SEEDED: {rel} cap {candidate} ({size} bytes + margin)")
        elif candidate < old:
            files_caps[rel] = candidate
            lowered += 1
            print(f"LOWERED: {rel} cap {old} -> {candidate} (file at {size} bytes)")
        # never raise: a grown file keeps its existing cap (the breach line in
        # --check is the growth signal; the ratchet only tightens)
    caps_path.write_text(json.dumps(caps, indent=2) + "\n", encoding="utf-8")
    print(f"ratchet: {lowered} cap(s) lowered, {seeded} seeded; no cap raised")
    print("OUTCOME: pass")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Skill-text byte-budget gate (warning-only)")
    parser.add_argument("--check", action="store_true", help="report per-file breaches as advisory lines")
    parser.add_argument("--ratchet", action="store_true", help="lower caps on shrink, seed new files, never raise")
    parser.add_argument("--caps", type=Path, default=DEFAULT_CAPS_PATH, help="caps table path")
    parser.add_argument("--skills-dir", type=Path, default=DEFAULT_SKILLS_DIR, help="skills root to walk")
    args = parser.parse_args(argv)
    if args.check == args.ratchet:
        print("usage error: exactly one of --check or --ratchet is required")
        print("OUTCOME: tool_error")
        return 3
    # the relative keys in the caps table resolve against the skills tree's
    # own repo root (the walked tree's parent-of-parent), not the script's
    # location: the hermetic fixtures run the gate over a temp tree
    repo_root = args.skills_dir.resolve().parent.parent
    if not args.skills_dir.is_dir():
        print(f"skills dir not found: {args.skills_dir}")
        print("OUTCOME: tool_error")
        return 3
    try:
        if args.check:
            return run_check(args.caps, args.skills_dir, repo_root)
        return run_ratchet(args.caps, args.skills_dir, repo_root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"budget gate could not run reliably: {exc}")
        print("OUTCOME: tool_error")
        return 3


if __name__ == "__main__":
    sys.exit(main())
