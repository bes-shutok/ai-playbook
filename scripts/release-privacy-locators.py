#!/usr/bin/env python3
"""Bounded locator front end for the release privacy gate.

Plan: docs/history/plans/2026-10-26-release-privacy-gate-diagnostics-and-replay.md
(Task 1). ``release-rewrite.sh`` runs its privacy scanner through this helper:
the helper spawns the scanner, streams its stdout in memory under a hard
65,536-byte parse bound, and emits only safe hit locators, so the scanner's
raw stdout (whose FAIL rows echo the matched content) never lands on disk or
in the release transcript.

Usage:

  python3 release-privacy-locators.py --scanner <scanner> -- <scanner argv...>

The scanner argv after ``--`` must carry ``--files`` as its final option,
followed by the scanned paths; those paths are the requested set a locator
row must name exactly.

Row acceptance: a row is accepted only when exactly one split of its
colon-separated prefix names an exact requested path followed by an
all-digit line number (the ``path:line:content`` form). Ripgrep's
``line:content`` form is considered only when exactly one path was scanned,
and assigns that sole path. Malformed rows, pathless rows in multi-path
scans, unrequested paths, and ambiguous prefixes yield no locator.

Stdout contract: one ``path:line`` locator per accepted FAIL row (deduplicated,
first-seen order, control bytes and undecodable bytes escaped, matched content
dropped), or the single sentinel line ``LOCATOR-BOUND-EXCEEDED`` when the
scanner output crossed the parse bound, in which case no locators are emitted.
The exit code is the scanner's exit code, unchanged; a helper-internal failure
(a missing scanner, a bad invocation) is a tool error and exits 3.
release-rewrite.sh matches the sentinel line and the 65536-byte bound verbatim
in its failure message; keep the two files in step.
"""

from __future__ import annotations

import os
import subprocess
import sys

PARSE_BOUND = 65536
BOUND_SENTINEL = "LOCATOR-BOUND-EXCEEDED"


def fatal(message: str) -> None:
    print("release-privacy-locators: FATAL: %s" % message, file=sys.stderr)
    sys.exit(3)


def _digits(token: bytes) -> bool:
    return bool(token) and all(0x30 <= b <= 0x39 for b in token)


def parse_row(row: bytes, requested: dict, sole_path):
    """Resolve one stdout row to a single (path, line) locator, or None.

    Every colon split is a candidate: ``path:line:content`` with an exact
    requested path and an all-digit line, plus the single-path
    ``line:content`` form. Exactly one distinct candidate is accepted; zero
    or several reject the row.
    """
    if not row:
        return None
    colon_at = [i for i, b in enumerate(row) if b == 0x3A]
    candidates = set()
    for pos, i in enumerate(colon_at[:-1]):
        path = row[:i]
        line = row[i + 1:colon_at[pos + 1]]
        if _digits(line) and path in requested:
            candidates.add((path, line))
    if sole_path is not None and colon_at and _digits(row[:colon_at[0]]):
        candidates.add((sole_path, row[:colon_at[0]]))
    if len(candidates) == 1:
        return candidates.pop()
    return None


def escape_path(path: str) -> str:
    """Escape every byte that could corrupt a terminal or a log line."""
    out = []
    for ch in path:
        code = ord(ch)
        if ch == "\\":
            out.append("\\\\")
        elif 0xDC80 <= code <= 0xDCFF:
            # surrogateescape remainder of an undecodable byte: show its hex.
            out.append("\\x%02x" % (code - 0xDC00))
        elif code < 0x20 or code == 0x7F:
            out.append("\\x%02x" % code)
        else:
            out.append(ch)
    return "".join(out)


def main() -> int:
    argv = sys.argv[1:]
    scanner = None
    scanner_argv = []
    i = 0
    while i < len(argv):
        if argv[i] == "--scanner":
            i += 1
            if i >= len(argv):
                fatal("--scanner requires a value")
            scanner = argv[i]
        elif argv[i] == "--":
            scanner_argv = argv[i + 1:]
            break
        else:
            fatal("unexpected argument: %s" % argv[i])
        i += 1
    if scanner is None:
        fatal("usage: release-privacy-locators.py --scanner <scanner> -- <scanner argv...>")
    if "--files" not in scanner_argv:
        fatal("the scanner argv must carry --files followed by the scanned paths")
    paths = scanner_argv[scanner_argv.index("--files") + 1:]
    if not paths:
        fatal("the scanner argv must name at least one path after --files")
    requested = {}
    for path in paths:
        requested[os.fsencode(path)] = path
    sole_path = os.fsencode(paths[0]) if len(paths) == 1 else None

    try:
        proc = subprocess.Popen(
            ["bash", scanner, *scanner_argv],
            stdout=subprocess.PIPE,
        )
    except OSError as exc:
        fatal("cannot spawn the scanner: %s" % exc)

    retained = bytearray()
    total = 0
    overflow = False
    while True:
        chunk = proc.stdout.read(PARSE_BOUND)
        if not chunk:
            break
        total += len(chunk)
        if overflow:
            continue  # drain: keep the child's pipe empty, retain nothing
        if total > PARSE_BOUND:
            overflow = True
            retained.clear()
            continue
        retained.extend(chunk)
    proc.stdout.close()
    scanner_rc = proc.wait()

    if overflow:
        print(BOUND_SENTINEL)
        return scanner_rc

    emitted = set()
    for row in bytes(retained).split(b"\n"):
        locator = parse_row(row, requested, sole_path)
        if locator is None or locator in emitted:
            continue
        emitted.add(locator)
        raw_path, line = locator
        print("%s:%s" % (escape_path(requested[raw_path]), line.decode("ascii")))
    return scanner_rc


if __name__ == "__main__":
    sys.exit(main())
