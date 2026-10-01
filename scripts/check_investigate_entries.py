#!/usr/bin/env python3
"""Investigate rolling-log entry validator (investigate Stage 3/4 self-check).

Checks the structural minimum of every entry in the tracked rolling prompt
log of ready-to-dispatch plan-creation prompts (default
``docs/history/backlog/PLAN-PROMPTS.md``):

- the entry carries a ``Rejected alternatives:`` field with at least one
  list item (a missing field or an empty list is a violation), and
- every disposition line (a list item under ``Rejected alternatives:``
  until the next field heading like ``Prompt:`` or the next entry) carries
  at least one evidence-basis marker:

  - a repo-relative path starting ``docs/``, ``agents/``, or
    ``scripts/`` that names a file: the matched span must end ``.md`` or
    resolve to an existing file (cwd-relative), and the disposition line
    must end at the citation - its last non-space character is the
    citation parenthetical's closing ``)`` or the path's final character
    (a bare directory span such as ``docs/history/backlog/`` and free
    text trailing the citation both fail);
  - a word-bounded run of 7-40 hexadecimal characters (a commit sha); the
    run must contain at least one digit, so all-letter hex words such as
    "defaced" never masquerade as a sha;
  - the tokens ``witnessed`` or ``adjudication``, or the span
    ``plan docs/history/``;
  - a double-quoted span containing the word ``operator`` (a quoted
    operator correction).

Parsing bounds: ``## `` sections are entries only OUTSIDE fenced code
blocks (the log's fenced entry-template block is not an entry) and after
the preamble (text before the first entry heading is the preamble and is
never parsed as an entry). Disposition collection stops at the first line
that is not a ``- `` list item: a blank line, a field heading, or the next
``## `` heading ends the list.

The marker list is the mechanical floor - a deliberate superset of the
conceptual evidence kinds (disk witness, landed mechanism, commit,
witnessed incident, quoted operator correction); review supplies the
judgment above it. It is owned here, never restated in the skill text.

Exit codes: 0 clean; 1 violations (each named on stderr with the entry
slug and the failing line text, with a summary on stdout); 2 tool failure
(unreadable log), the outside-the-repository-root invocation refusal, or
CLI usage error.

single-line disposition constraint: each ``- `` line is
checked separately and must END at its citation, so a multi-line
disposition style whose citation lands mid-block is rejected (latent
today, pinned as documented). The ``CITATION_TAIL_CHARS`` strip can
remove a legitimate trailing character from an exotic filename; that is
an accepted trade.

Shaped after ``scripts/doc_registry_validator.py`` (argparse CLI,
fail-loud exits, stdlib only). Repo-relative paths only; no PII.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_LOG = "docs/history/backlog/PLAN-PROMPTS.md"

ENTRY_HEADING_PREFIX = "## "
REJECTED_FIELD_PREFIX = "Rejected alternatives:"
DISPOSITION_PREFIX = "- "
FENCE_PREFIX = "```"

# Evidence-basis markers (the mechanical floor; see the module docstring).
PATH_MARKER_RE = re.compile(r"\b(?:docs|agents|scripts)/\S+")
HEX_RUN_RE = re.compile(r"(?<!\w)[0-9a-fA-F]{7,40}(?!\w)")
WITNESS_TOKEN_RE = re.compile(r"\b(?:witnessed|adjudication)\b")
PLAN_HISTORY_TOKEN = "plan docs/history/"
OPERATOR_QUOTE_RE = re.compile(r'"[^"]*\boperator\b[^"]*', re.IGNORECASE)

# Closing punctuation the greedy ``\S+`` path capture swallows when the
# cited path sits inside a citation parenthetical or ends a sentence;
# stripped before the suffix and on-disk checks. A trailing ``/`` is never
# stripped, so a bare directory span such as ``docs/history/backlog/``
# keeps failing.
# tail-strip trade: the strip can drop a legitimate trailing char
# from an exotic filename; an accepted trade.
CITATION_TAIL_CHARS = ')]}"\'`.,;:!?'


def parse_entries(text: str) -> list[dict]:
    """Parse the log into entries outside fences, after the preamble.

    Returns one dict per ``## `` entry: ``slug``, ``rejected_lineno``
    (None when the field is absent) and ``dispositions`` as
    ``(lineno, line)`` pairs collected from the list items under
    ``Rejected alternatives:`` until the first non-list line. Fenced
    blocks (the entry template) are skipped entirely, and text before
    the first entry heading is preamble.
    """
    entries: list[dict] = []
    current: dict | None = None
    in_fence = False
    collecting = False
    for lineno, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if stripped.startswith(FENCE_PREFIX):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if raw.startswith(ENTRY_HEADING_PREFIX):
            current = {
                "slug": raw[len(ENTRY_HEADING_PREFIX):].strip(),
                "rejected_lineno": None,
                "dispositions": [],
            }
            entries.append(current)
            collecting = False
            continue
        if current is None:
            continue  # preamble before the first entry heading
        if collecting:
            if raw.startswith(DISPOSITION_PREFIX):
                current["dispositions"].append((lineno, stripped))
                continue
            # A blank line, a field heading, or the next entry ends the
            # list; the terminating line falls through to the checks
            # below (it can itself start a new field).
            collecting = False
        if stripped.startswith(REJECTED_FIELD_PREFIX):
            current["rejected_lineno"] = lineno
            collecting = True
    return entries


def _span_names_file_evidence(span: str) -> bool:
    """True when the matched path span ends in ``.md`` or names an
    existing file (cwd-relative, the validator's path convention;
    ``os.path.isfile``, never ``exists()``, so a bare directory does not
    count)."""
    span = span.rstrip(CITATION_TAIL_CHARS)
    if span.endswith(".md"):
        return True
    return os.path.isfile(span)


def _has_path_marker(line: str) -> bool:
    """True when a matched path span is file evidence cited at line end.

    The disposition line must end at the citation: its last non-space
    character is the citation parenthetical's closing ``)`` or the
    matched path's final character, so free text trailing the citation
    fails the marker.
    """
    tail = line.rstrip()
    for match in PATH_MARKER_RE.finditer(line):
        if not _span_names_file_evidence(match.group(0)):
            continue
        span = match.group(0).rstrip(CITATION_TAIL_CHARS)
        if tail.endswith(")") or tail.endswith(span):
            return True
    return False


def has_evidence_basis(line: str) -> bool:
    """True when the disposition line carries at least one marker."""
    if _has_path_marker(line):
        return True
    for match in HEX_RUN_RE.finditer(line):
        if any(ch.isdigit() for ch in match.group(0)):
            return True
    if WITNESS_TOKEN_RE.search(line):
        return True
    if PLAN_HISTORY_TOKEN in line:
        return True
    if OPERATOR_QUOTE_RE.search(line):
        return True
    return False


def check_entries(entries: list[dict]) -> list[str]:
    """Return one human-readable violation per structural-minimum miss.

    Each violation names the entry slug and the failing line text so a
    drifted entry is actionable without re-deriving anything.
    """
    violations: list[str] = []
    for entry in entries:
        slug = entry["slug"]
        if entry["rejected_lineno"] is None:
            violations.append(
                "entry '%s': no 'Rejected alternatives:' field" % slug)
            continue
        if not entry["dispositions"]:
            violations.append(
                "entry '%s': empty 'Rejected alternatives:' list (line %d)"
                % (slug, entry["rejected_lineno"]))
            continue
        for lineno, line in entry["dispositions"]:
            if not has_evidence_basis(line):
                violations.append(
                    "entry '%s': disposition line %d lacks an evidence-basis"
                    " marker (a docs/ agents/ scripts/ path ending in .md or"
                    " naming an existing file, cited at the line's end - the"
                    " line ends at the path or its citation parenthetical; a"
                    " 7-40 hex commit; the 'witnessed'/'adjudication' tokens;"
                    " the span 'plan docs/history/'; or a quoted operator"
                    " correction): %s" % (slug, lineno, line))
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="check_investigate_entries.py",
        description="Check investigate rolling-log entries' structural"
                    " minimum: non-empty rejected alternatives and"
                    " evidence-cited dispositions.",
    )
    parser.add_argument(
        "--log", default=DEFAULT_LOG, metavar="PATH",
        help="rolling prompt log to check (default: %(default)s)")
    args = parser.parse_args(argv)

    top = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True)
    toplevel = top.stdout.strip() if top.returncode == 0 else ""
    cwd = os.path.realpath(os.getcwd())
    top_resolved = os.path.realpath(toplevel) if toplevel else None
    if not toplevel or top_resolved != cwd:
        print("entry validator: invoked outside the repository root;"
              " run from the repository root", file=sys.stderr)
        return 2

    log_path = Path(args.log)
    try:
        text = log_path.read_text(encoding="utf-8")
    except OSError as exc:
        print("error: cannot read log %s: %s" % (log_path, exc),
              file=sys.stderr)
        return 2

    entries = parse_entries(text)
    violations = check_entries(entries)
    for violation in violations:
        print(violation, file=sys.stderr)
    disposition_count = sum(len(entry["dispositions"]) for entry in entries)
    print("check_investigate_entries: %d entry(ies), %d disposition line(s),"
          " %d violation(s) in %s"
          % (len(entries), disposition_count, len(violations), log_path))
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
