#!/usr/bin/env python3
"""Backlog duplicate sweep for the docs-branch sync (warn-and-continue).

For every top-level ``<name>.md`` in the backlog directory whose archived
twin exists under ``completed/``, ``deferred/``, or ``rejected/``, compare
the two files after dropping lines matching ``^Status:``. The stale
top-level copy is deleted only when the normalized bodies are equal AND
the top-level ``Status:`` value equals the archived twin's Status; the
removal is reported on stdout. Bodies equal but Status values differing
(for example an archived item that was legitimately re-opened): both
copies are kept and an informational surface-and-keep line goes to
stdout. Any deeper mismatch: both copies are kept and a warning naming
the file goes to stderr. Items with no archived twin are never touched.
The command always exits 0 and is idempotent: once swept, a second run
finds nothing and changes nothing. The sweep never widens beyond these
archived twins. ``rejected/`` twins follow the same rules: a top-level
copy matching its rejected twin in body and Status is a stale leftover of
the rejection move; differing or mismatched content is retained and
surfaced, never deleted.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

STATUS_LINE_RE = re.compile(r"^Status:")
ARCHIVE_DIRS = ("completed", "deferred", "rejected")


def normalized_lines(text: str) -> list[str]:
    """The file's lines with ``^Status:`` lines dropped."""
    return [line for line in text.splitlines() if not STATUS_LINE_RE.match(line)]


def status_value(text: str) -> str | None:
    """The value of the file's first ``^Status:`` line, or None when absent."""
    for line in text.splitlines():
        if STATUS_LINE_RE.match(line):
            return line.split(":", 1)[1].strip()
    return None


def _display(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def sweep(worktree_root: Path, backlog_dir: Path) -> int:
    backlog = backlog_dir if backlog_dir.is_absolute() else worktree_root / backlog_dir
    if not backlog.is_dir():
        print(f"WARN: backlog directory not found, sweep skipped: {backlog}", file=sys.stderr)
        return 0
    for item in sorted(backlog.glob("*.md")):
        if not item.is_file():
            continue
        matched_twin: tuple[str, Path] | None = None
        status_only_twins: list[tuple[str, Path]] = []
        mismatched_twins: list[tuple[str, Path]] = []
        for archive_dir in ARCHIVE_DIRS:
            twin = backlog / archive_dir / item.name
            if not twin.is_file():
                continue
            try:
                item_text = item.read_text(encoding="utf-8")
                twin_text = twin.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                print(
                    f"WARN: backlog duplicate kept (unreadable: {exc}): {item.name}",
                    file=sys.stderr,
                )
                continue
            if normalized_lines(item_text) != normalized_lines(twin_text):
                mismatched_twins.append((archive_dir, twin))
            elif status_value(item_text) == status_value(twin_text):
                matched_twin = (archive_dir, twin)
                break
            else:
                status_only_twins.append((archive_dir, twin))
        if matched_twin is not None:
            archive_dir, twin = matched_twin
            item.unlink()
            print(
                f"REMOVED: {_display(item, worktree_root)} "
                f"(matches {archive_dir}/{item.name} in body and Status)"
            )
        else:
            if status_only_twins:
                twins = ", ".join(
                    f"{archive_dir}/{item.name}" for archive_dir, _ in status_only_twins
                )
                print(
                    f"KEPT: {_display(item, worktree_root)} "
                    f"(Status-only difference vs {twins}; both copies kept)"
                )
            if mismatched_twins:
                twins = ", ".join(f"{archive_dir}/{item.name}" for archive_dir, _ in mismatched_twins)
                print(
                    f"WARN: backlog duplicate kept (body mismatch beyond Status lines): "
                    f"{item.name} vs {twins}",
                    file=sys.stderr,
                )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sweep stale top-level backlog copies that match an archived twin."
    )
    parser.add_argument("--worktree-root", required=True, help="Root of the docs worktree.")
    parser.add_argument(
        "--backlog-dir",
        required=True,
        help="Backlog directory, absolute or relative to the worktree root.",
    )
    args = parser.parse_args(argv)
    return sweep(Path(args.worktree_root), Path(args.backlog_dir))


if __name__ == "__main__":
    sys.exit(main())
