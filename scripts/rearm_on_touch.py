#!/usr/bin/env python3
"""Rearm-on-touch mechanical check: the scripted form of the maintenance
skill's Step 0 rearm-on-touch duty.

Plan: docs/history/plans/2026-09-20-harness-triage-paperkeeping-dismantling-wall-clock.md,
section "Task 3: Rearm-on-touch mechanical check". This script mirrors (never
replaces) the duty prose in agents/skills/maintenance/SKILL.md Step 0 and the
re-arm hygiene shape in agents/skills/maintenance/zcode.md ("Recurring
automation recipe"): it reads the scheduler state file state-first, classifies
the loop state, applies the three listing-gated bookkeeping edits, and emits a
verdict or an explicit skipped-reason line.

Boundary: this script classifies, books, and decides. It NEVER calls
automation primitives (create, update, delete, or list): the calling session
performs any listing or re-arm the verdict calls for, optionally feeding a
fetched listing back through --listing-json as decision input.

Decision flow (state-first, per the maintenance Step 0 bullet and the State
file semantics):
1. no state file            -> skipped verdict `no-scheduler-state-file`,
                               rc 0, inert (the loop does not run here);
2. unparseable state JSON   -> class `malformed`, rc 2, loud error;
3. state file whose own last write (mtime) is older than one cadence period
   -> class `stale-state-listing-required` without a listing (the staleness
   escape: only the listing decides); with a listing provided, the listing
   decides and the verdict carries a staleness note;
4. state-first classification:
   - recorded parent id + null parent_absent_since  -> `parent-ok`;
   - recorded absence + live pending child          -> `surrendered-live-child`
     (expected surrender: the child re-arms the parent as its first action);
   - recorded absence >= one cadence period, no live child
     -> `darkness-rearm-required` (rearm_required true);
   - recorded absence < one cadence period, no live child
     -> `listing-required` reason `fresh-absence`;
   - null/missing parent id, no live child
     -> `listing-required` reason `null-parent-id`;
5. with --listing-json: the listing decides, and the three listing-gated
   bookkeeping edits apply: the parent_automation_id adopt under the Step 0
   adoption guards, the parent_absent_since set-or-clear keeping the earliest
   value, and the rearm_note clear on an armed-again listing. The edit is a
   targeted field edit through a temp file plus atomic replace that touches
   only the named fields and preserves all other bytes.

Recognition rule (mirrored literals): an ENABLED automation whose title equals
the recipe title, whose prompt begins with the scheduler prompt template's
opening line, and whose prompt contains the resolved repository root.

Output: one JSON verdict line plus a one-line human summary on stdout.
Exit codes: 0 for every normal verdict (including skipped and
listing-required classes); 2 for malformed-or-failed (unparseable state or
listing JSON, a refused structural edit, a twice-drifted write, or any
unexpected internal error). Cadence period: 2 hours. Live-child horizon:
6 hours.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Cadence period and live-child horizon (maintenance SKILL.md State file
# semantics: darkness at one cadence period; a pending child explains an
# absence only while it is live, fewer than six hours past).
CADENCE = timedelta(hours=2)
LIVE_CHILD_HORIZON = timedelta(hours=6)

# Recognition literals, mirrored from the pinned source of record:
# agents/skills/maintenance/zcode.md ("Recurring automation recipe"). This
# script mirrors, never edits, them; scripts/check_maintenance_pins.sh
# freezes the originals.
RECOGNITION_TITLE = "Maintenance scheduler turn (every 2 hours)"
RECOGNITION_PROMPT_OPENING = "You are the maintenance scheduler for the repository at"

STATE_REL_PATH = ".ai-playbook/scheduler-state.json"

CLASS_PARENT_OK = "parent-ok"
CLASS_SURRENDERED = "surrendered-live-child"
CLASS_DARKNESS = "darkness-rearm-required"
CLASS_LISTING_REQUIRED = "listing-required"
CLASS_STALE = "stale-state-listing-required"
CLASS_NO_STATE_FILE = "no-scheduler-state-file"
CLASS_MALFORMED = "malformed"

# The three fields this script may touch (and nothing else).
BOOKKEEPING_FIELDS = ("parent_automation_id", "parent_absent_since", "rearm_note")


class RearmError(Exception):
    """Loud failure: malformed input or a refused bookkeeping edit (rc 2)."""


# --------------------------------------------------------------------------- #
# Time and state helpers.
# --------------------------------------------------------------------------- #
def parse_iso(value):
    """Parse an ISO-8601 timestamp string; naive values read as UTC."""
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def iso_z(moment):
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def live_pending_child(state, now):
    """True when a pending children[] entry is live: its fire_at (or
    created_at for idle-time entries) is fewer than LIVE_CHILD_HORIZON past,
    with no failed outcome. A ghost record past the horizon, or one with a
    failed outcome, explains nothing and never suppresses darkness."""
    children = state.get("children")
    if not isinstance(children, list):
        return False
    for entry in children:
        if not isinstance(entry, dict):
            continue
        if entry.get("outcome") == "failed":
            continue
        reference = parse_iso(entry.get("fire_at")) or parse_iso(entry.get("created_at"))
        if reference is None:
            continue
        if (now - reference) < LIVE_CHILD_HORIZON:
            return True
    return False


# --------------------------------------------------------------------------- #
# Recognition rule (mirrored literals).
# --------------------------------------------------------------------------- #
def is_recognition_match(entry, repo_root):
    """ENABLED + recipe title + prompt opening + resolved repo root contained.
    A prompt that is missing or not a string can never match (the prompt
    conjuncts are part of the rule)."""
    if not isinstance(entry, dict):
        return False
    if entry.get("enabled") is not True:
        return False
    if str(entry.get("title") or "").strip() != RECOGNITION_TITLE:
        return False
    prompt = entry.get("prompt")
    if not isinstance(prompt, str) or not prompt:
        return False
    if not prompt.startswith(RECOGNITION_PROMPT_OPENING):
        return False
    return repo_root in prompt


def entry_id(entry):
    value = entry.get("automationId")
    return value if isinstance(value, str) and value else None


# --------------------------------------------------------------------------- #
# Listing input.
# --------------------------------------------------------------------------- #
def load_listing(listing_arg):
    """Read --listing-json (<path> or '-' for stdin). Returns (entries, used)."""
    if listing_arg is None:
        return None, False
    if listing_arg == "-":
        raw = sys.stdin.read()
    else:
        try:
            with open(listing_arg, "r", encoding="utf-8") as handle:
                raw = handle.read()
        except OSError as exc:
            raise RearmError("listing input unreadable: %s" % exc)
    try:
        doc = json.loads(raw)
    except ValueError as exc:
        raise RearmError("listing input is not parseable JSON: %s" % exc)
    return extract_entries(doc), True


def extract_entries(doc):
    """Accept a bare array or an object carrying the array under a known key."""
    if isinstance(doc, list):
        return doc
    if isinstance(doc, dict):
        for key in ("automations", "items", "results", "data", "tasks"):
            value = doc.get(key)
            if isinstance(value, list):
                return value
    raise RearmError(
        "listing input is neither an array nor an object with a known array field"
    )


# --------------------------------------------------------------------------- #
# Targeted bookkeeping edit: only the named fields, byte-preserving elsewhere,
# through a temp file plus atomic replace, with the one-retry drift guard.
# --------------------------------------------------------------------------- #
def field_pattern(field):
    return re.compile(r'("%s"\s*:\s*)(null|"(?:[^"\\]|\\.)*")' % re.escape(field))


def apply_bookkeeping(state_path, updates):
    """Apply the named-field edits atomically. Returns the applied-edits dict
    ({} when nothing changed). Raises RearmError on structural surprises."""
    if not updates:
        return {}
    for _attempt in range(2):
        raw = state_path.read_text(encoding="utf-8")
        try:
            before = json.loads(raw)
        except ValueError as exc:
            raise RearmError("state file turned unparseable mid-run: %s" % exc)
        if not isinstance(before, dict):
            raise RearmError("state file is not a JSON object")
        text = raw
        applied = {}
        for field, value in updates.items():
            new_json = json.dumps(value)
            match = field_pattern(field).search(text)
            if not match:
                raise RearmError(
                    "state file has no %s field; refusing a structural insert" % field
                )
            if match.group(2) == new_json:
                continue
            text = field_pattern(field).sub(
                lambda m: m.group(1) + new_json, text, count=1
            )
            applied[field] = {"from": before.get(field), "to": value}
        if not applied:
            return {}
        tmp_path = state_path.with_name("%s.rearm-tmp-%d" % (state_path.name, os.getpid()))
        try:
            tmp_path.write_text(text, encoding="utf-8")
            if state_path.read_text(encoding="utf-8") == raw:
                os.replace(tmp_path, state_path)
                return applied
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
    raise RearmError("state file drifted twice during bookkeeping; no write performed")


# --------------------------------------------------------------------------- #
# Verdict plumbing.
# --------------------------------------------------------------------------- #
def build_verdict(cls, reason=None, skipped=False, listing_used=False,
                  rearm_required=False, matches=None, bookkeeping=None, notes=None):
    return {
        "check": "rearm-on-touch",
        "class": cls,
        "reason": reason,
        "skipped": skipped,
        "listing_used": listing_used,
        "rearm_required": rearm_required,
        "recognition_matches": matches,
        "bookkeeping": bookkeeping if bookkeeping else None,
        "notes": notes or [],
    }


def human_summary(verdict):
    if verdict["class"] == CLASS_MALFORMED:
        return "rearm-on-touch: FAILED: %s" % (verdict["reason"] or "unspecified")
    bits = ["rearm-on-touch:", verdict["class"]]
    if verdict["reason"]:
        bits.append("reason=%s" % verdict["reason"])
    bits.append("rearm_required=%s" % ("true" if verdict["rearm_required"] else "false"))
    bits.append("listing=%s" % ("used" if verdict["listing_used"] else "none"))
    bits.append("edits=%d" % (len(verdict["bookkeeping"]) if verdict["bookkeeping"] else 0))
    for note in verdict["notes"]:
        bits.append("note: %s" % note)
    return " ".join(bits)


def emit(verdict, stream=None):
    stream = stream or sys.stdout
    print(json.dumps(verdict), file=stream)
    print(human_summary(verdict), file=stream)


# --------------------------------------------------------------------------- #
# Main decision flow.
# --------------------------------------------------------------------------- #
def resolve_repo_root(explicit):
    if explicit:
        return os.path.abspath(explicit)
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True, timeout=30,
        )
        root = out.stdout.strip()
        if root:
            return root
    except Exception:
        pass
    return os.getcwd()


def classify_state_first(state, now):
    """The no-listing state-first decision (rc 0 verdicts only)."""
    recorded = state.get("parent_automation_id")
    absent_since = parse_iso(state.get("parent_absent_since"))
    if not recorded:
        return build_verdict(CLASS_LISTING_REQUIRED, reason="null-parent-id")
    if absent_since is None:
        return build_verdict(CLASS_PARENT_OK)
    if live_pending_child(state, now):
        return build_verdict(CLASS_SURRENDERED)
    if (now - absent_since) > CADENCE:
        return build_verdict(CLASS_DARKNESS, rearm_required=True)
    return build_verdict(CLASS_LISTING_REQUIRED, reason="fresh-absence")


def classify_with_listing(state, state_path, entries, repo_root, now, stale, notes):
    """The listing-informed decision plus the three listing-gated bookkeeping
    edits (adoption guards, set-or-clear keeping the earliest value,
    armed-again clears)."""
    recorded = state.get("parent_automation_id")
    absent_since_raw = state.get("parent_absent_since")
    absent_since = parse_iso(absent_since_raw)
    matches = [e for e in entries if is_recognition_match(e, repo_root)]
    live = live_pending_child(state, now)

    updates = {}
    if stale:
        notes.append("state file stale past one cadence; the listing decided")
    differing = [m for m in matches if entry_id(m) != recorded]
    recorded_live = recorded is not None and any(
        entry_id(e) == recorded and e.get("enabled") is True for e in entries
    )
    if len(differing) == 1 and not recorded_live:
        updates["parent_automation_id"] = entry_id(differing[0])
    elif len(differing) > 1:
        notes.append("multiple differing-id matches; adoption deferred to the "
                     "duplicate-parent tripwire")
    if matches:
        # Armed again: an ENABLED recognition match clears the absence clock
        # and the rearm_note.
        if absent_since_raw is not None:
            updates["parent_absent_since"] = None
        if state.get("rearm_note") is not None:
            updates["rearm_note"] = None
    elif absent_since is None:
        # First observation of the absence, at this observation's timestamp.
        updates["parent_absent_since"] = iso_z(now)
    # else: the absence persists, so the field keeps its earliest value and is
    # never refreshed; rearm_note is left to its own writers.

    applied = apply_bookkeeping(state_path, updates)

    # Final classification uses the post-bookkeeping absence value.
    if matches:
        cls, reason, rearm_required = CLASS_PARENT_OK, None, False
    elif live:
        cls, reason, rearm_required = CLASS_SURRENDERED, None, False
    elif not recorded:
        cls, reason, rearm_required = CLASS_LISTING_REQUIRED, "null-parent-id", False
    else:
        effective_absent = updates.get("parent_absent_since", absent_since_raw)
        effective_dt = parse_iso(effective_absent)
        if effective_dt is not None and (now - effective_dt) > CADENCE:
            cls, reason, rearm_required = CLASS_DARKNESS, None, True
        else:
            cls, reason, rearm_required = CLASS_LISTING_REQUIRED, "fresh-absence", False

    return build_verdict(
        cls, reason=reason, listing_used=True, rearm_required=rearm_required,
        matches=len(matches), bookkeeping=applied, notes=notes,
    )


def run_check(args, repo_root, state_path, now):
    if not state_path.exists():
        emit(build_verdict(CLASS_NO_STATE_FILE, reason=CLASS_NO_STATE_FILE, skipped=True))
        return 0
    raw = state_path.read_text(encoding="utf-8")
    try:
        state = json.loads(raw)
    except ValueError as exc:
        raise RearmError("scheduler state file is not parseable JSON: %s" % exc)
    if not isinstance(state, dict):
        raise RearmError("scheduler state file is not a JSON object")

    entries, listing_used = load_listing(args.listing_json)

    if listing_used:
        mtime = state_path.stat().st_mtime
        stale = (now - datetime.fromtimestamp(mtime, tz=timezone.utc)) > CADENCE
        emit(classify_with_listing(state, state_path, entries, repo_root, now, stale, []))
        return 0

    mtime = state_path.stat().st_mtime
    if (now - datetime.fromtimestamp(mtime, tz=timezone.utc)) > CADENCE:
        emit(build_verdict(CLASS_STALE))
        return 0
    emit(classify_state_first(state, now))
    return 0


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Rearm-on-touch mechanical check (maintenance Step 0). "
                    "Classifies the scheduler state file state-first, applies "
                    "listing-gated bookkeeping, and prints a JSON verdict plus "
                    "a one-line human summary. Never calls automation "
                    "primitives."
    )
    parser.add_argument("--repo-root", default=None,
                        help="repository root (default: git toplevel of cwd)")
    parser.add_argument("--state-path", default=None,
                        help="scheduler state file (default: <repo-root>/"
                             + STATE_REL_PATH + ")")
    parser.add_argument("--listing-json", default=None,
                        help="path to a fetched automation listing JSON, or - "
                             "for stdin; decision input only")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    now = datetime.now(timezone.utc)
    try:
        repo_root = resolve_repo_root(args.repo_root)
        state_path = (Path(args.state_path) if args.state_path
                      else Path(repo_root) / STATE_REL_PATH)
        return run_check(args, repo_root, state_path, now)
    except RearmError as exc:
        emit(build_verdict(CLASS_MALFORMED, reason=str(exc)))
        print("rearm-on-touch: FAILED: %s" % exc, file=sys.stderr)
        return 2
    except Exception as exc:  # unexpected: loud fail, never a silent pass
        message = "unexpected %s: %s" % (type(exc).__name__, exc)
        emit(build_verdict(CLASS_MALFORMED, reason=message))
        print("rearm-on-touch: FAILED: %s" % message, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
