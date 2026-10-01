#!/usr/bin/env python3
"""Prompt-log origin checker: flags PLAN-PROMPTS.md entries whose every
origin is served.

The tracked rolling prompt log docs/history/backlog/PLAN-PROMPTS.md holds
one ``## <slug>`` section per ready-to-dispatch authoring entry, each
listing its backlog origins. The log's own prune rule removes an entry
when its plan file lands, but nothing mechanical verifies the landed
log, so an all-served entry can sit dispatchable for hours past its
plan's full lifecycle (the witnessed 2026-09-30 drift). This checker
reads the log (sections after the entry-template fence only; the fenced
template placeholders are never parsed as an entry), collects each
entry's ``Origins:`` lines, and classifies every origin:

- SERVED when the origin file's first ``Status:`` line (bullet or bare,
  at any header depth, first such line only) reads ``done`` or
  ``covered``, or when the origin file is absent from the backlog top
  level because it sits in a backlog archive state directory
  (``completed/``, ``rejected/``, ``deferred/``, resolved by basename
  and reported with the resolved path relative to the backlog
  directory).
- LIVE otherwise: a present file with no or a novel status, or an
  absent file that resolves nowhere. A missing or unparseable status is
  not by itself a finding; only done/covered prefixes and absent files
  are findings, so the checker stays fail-open for novel statuses and
  fail-closed only for the witnessed drift classes.

An entry is STALE only when EVERY origin is served (a mixed entry still
carries unlanded work and stays). Exit 1 for a stale entry, 0
otherwise. Frozen entries are checked like any other: a frozen entry
whose origins are all served is exactly the witnessed wedge, and the
freeze rule itself already orders its prune.

The default log path resolves against this script's own repo root,
never the caller's cwd (the pins sweep promises run-from-anywhere and
never cds). Stdlib only; no network.
"""

from __future__ import annotations

import argparse
import io
import re
import sys
import tempfile
from pathlib import Path
from typing import TextIO

SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parent.parent
DEFAULT_LOG_REL = "docs/history/backlog/PLAN-PROMPTS.md"
ARCHIVE_DIR_NAMES = ("completed", "rejected", "deferred")

# One entry per ``## <slug>`` section, per the log's entry template.
ENTRY_HEADING_RE = re.compile(r"^##[ \t]+(.+?)[ \t]*$")
ORIGINS_HEADER_RE = re.compile(r"^[ \t]*Origins[ \t]*:[ \t]*$")
ORIGIN_ITEM_RE = re.compile(r"^[ \t]*-[ \t]+(\S+\.md)[ \t]*$")
# Any line opening with a fence toggles fenced state; the entry template
# lives inside one, and its placeholder ``## <short-slug>`` heading and
# ``Origins:`` lines must never parse as an entry.
FENCE_LINE_RE = re.compile(r"^[ \t]*```")

# The corpus status shapes ``Status: open`` and ``- **Status:** covered
# (...): optional bullet, optional bold around the label and the value.
STATUS_LINE_RE = re.compile(
    r"^[ \t]*(?:[-*+][ \t]*)?(?:\*\*)?[ \t]*status(?:\*\*)?[ \t]*:"
    r"[ \t]*(?:\*\*)?[ \t]*(.+?)[ \t]*$",
    re.IGNORECASE,
)
# served status VALUES; a hyphenated continuation such as ``done-phony``
# is not a done declaration (mirrors the backlog corpus gate).
SERVED_STATUS_RE = re.compile(r"^(?:done|covered)(?![A-Za-z0-9_-])", re.IGNORECASE)


def parse_entries(text: str) -> list[tuple[str, list[str]]]:
    """(slug, origin paths) per ``## `` section after the template fence,
    in file order. Content inside a fenced block is skipped entirely."""
    entries: list[tuple[str, list[str]]] = []
    slug: str | None = None
    origins: list[str] = []
    in_origins = False
    in_fence = False
    for line in text.splitlines():
        if FENCE_LINE_RE.match(line):
            in_fence = not in_fence
            in_origins = False
            continue
        if in_fence:
            continue
        heading = ENTRY_HEADING_RE.match(line)
        if heading:
            if slug is not None:
                entries.append((slug, origins))
            slug = heading.group(1).strip()
            origins = []
            in_origins = False
            continue
        if slug is None:
            continue
        if in_origins:
            item = ORIGIN_ITEM_RE.match(line)
            if item:
                origins.append(item.group(1))
                continue
            in_origins = False
        if ORIGINS_HEADER_RE.match(line):
            in_origins = True
    if slug is not None:
        entries.append((slug, origins))
    return entries


def first_status(origin_path: Path) -> str | None:
    """The file's first ``Status:`` line value (bullet or bare, at any
    header depth), or None when the file has none or is unreadable."""
    try:
        text = origin_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for line in text.splitlines():
        match = STATUS_LINE_RE.match(line)
        if match:
            return match.group(1)
    return None


def resolve_archive_path(basename: str, backlog_dir: Path) -> Path | None:
    """The origin's file inside a backlog archive state directory,
    resolved by basename (sorted first match), or None."""
    for state in ARCHIVE_DIR_NAMES:
        state_dir = backlog_dir / state
        if not state_dir.is_dir():
            continue
        for found in sorted(state_dir.rglob(basename)):
            if found.is_file():
                return found
    return None


def classify_origin(origin: str, backlog_dir: Path) -> tuple[bool, str]:
    """(served, report detail) for one logged origin path. The detail is
    the raw status text for a served-by-status origin, the resolved
    archive path relative to the backlog directory for a served-by-
    archive origin, and empty for a live origin."""
    basename = Path(origin.replace("\\", "/")).name
    top = backlog_dir / basename
    if top.is_file():
        status = first_status(top)
        if status is not None and SERVED_STATUS_RE.match(status):
            return True, status
        return False, ""
    archived = resolve_archive_path(basename, backlog_dir)
    if archived is not None:
        return True, archived.relative_to(backlog_dir).as_posix()
    return False, ""


def check_log(log_path: Path, out: TextIO) -> int:
    """Check every entry of the log, print one line per origin plus a
    verdict line per stale entry, and return 1 only for a stale entry
    (an entry whose every origin is served)."""
    text = log_path.read_text(encoding="utf-8", errors="replace")
    backlog_dir = log_path.resolve().parent
    stale: list[str] = []
    for slug, origins in parse_entries(text):
        if not origins:
            # Fail-open: a malformed entry without an Origins block is
            # not a witnessed drift class.
            continue
        all_served = True
        for origin in origins:
            served, detail = classify_origin(origin, backlog_dir)
            name = Path(origin.replace("\\", "/")).name
            if served:
                out.write(f"SERVED: {slug} -> {name} [{detail}]\n")
            else:
                all_served = False
                out.write(f"LIVE: {slug} -> {name}\n")
        if all_served:
            stale.append(slug)
    for slug in stale:
        out.write(
            f"STALE: {slug}: every origin served;"
            " prune per the log's prune rule\n"
        )
    return 1 if stale else 0


def selftest() -> int:
    """Exercise both verdicts against a fixture log: an all-served
    entry must be STALE (exit 1), and a mixed entry must stay."""
    done = "2026-10-01-selftest-done-origin.md"
    archived = "2026-10-01-selftest-archived-origin.md"
    live = "2026-10-01-selftest-live-origin.md"
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / done).write_text(
            "# fixture origin\n\nStatus: done (fixture witness)\n",
            encoding="utf-8",
        )
        archive = root / "completed"
        archive.mkdir()
        (archive / archived).write_text(
            "# fixture origin moved to the archive\n", encoding="utf-8"
        )
        (root / live).write_text(
            "# fixture origin\n\n- **Status:** open\n", encoding="utf-8"
        )
        template = (
            "Entry template (one section per entry):\n\n"
            "```\n## <short-slug>\n\nOrigins:\n"
            "- docs/history/backlog/<origin>.md\n```\n"
        )
        stale_entry = (
            "## selftest-stale\n\nAdded: fixture\n\nOrigins:\n"
            f"- docs/history/backlog/{done}\n"
            f"- docs/history/backlog/{archived}\n\n"
            "Urgency: fixture\n\nPrompt: fixture\n\n"
            "Rejected alternatives:\n- none\n\n"
        )
        mixed_entry = (
            "## selftest-mixed\n\nAdded: fixture\n\nOrigins:\n"
            f"- docs/history/backlog/{archived}\n"
            f"- docs/history/backlog/{live}\n\n"
            "Urgency: fixture\n\nPrompt: fixture\n\n"
            "Rejected alternatives:\n- none\n"
        )
        log = root / "PLAN-PROMPTS.md"
        log.write_text(template + stale_entry + mixed_entry, encoding="utf-8")
        buffer = io.StringIO()
        code = check_log(log, buffer)
        report = buffer.getvalue()
    problems = []
    if code != 1:
        problems.append(f"fixture exited {code}, expected 1 (the stale entry)")
    if f"SERVED: selftest-stale -> {done} [done (fixture witness)]" not in report:
        problems.append("served-by-status line missing")
    if f"SERVED: selftest-stale -> {archived} [completed/{archived}]" not in report:
        problems.append("served-by-archive line with the resolved path missing")
    if "STALE: selftest-stale" not in report:
        problems.append("STALE verdict line missing")
    if "STALE: selftest-mixed" in report:
        problems.append("mixed entry was flagged stale")
    if f"LIVE: selftest-mixed -> {live}" not in report:
        problems.append("live origin line missing")
    if "<short-slug>" in report:
        problems.append("entry-template fence leaked into the report")
    if problems:
        for problem in problems:
            print(f"selftest FAIL: {problem}", file=sys.stderr)
        return 1
    print("selftest ok: all-served entry STALE (exit 1), mixed entry stays")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Flag PLAN-PROMPTS.md entries whose every origin is served "
            "(a done/covered status, or the file resolved into a backlog "
            "archive state directory); exit 1 for a stale entry, 0 otherwise"
        )
    )
    parser.add_argument(
        "log",
        nargs="?",
        default=None,
        help=(
            "prompt log path (default: "
            f"{DEFAULT_LOG_REL}, resolved against this script's repo root)"
        ),
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="exercise both verdicts against a fixture instead of checking a log",
    )
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    if args.log:
        log_path = Path(args.log).expanduser()
    else:
        log_path = REPO_ROOT / DEFAULT_LOG_REL
    if not log_path.is_file():
        parser.error(f"prompt log not found: {log_path}")
    return check_log(log_path, sys.stdout)


if __name__ == "__main__":
    raise SystemExit(main())
