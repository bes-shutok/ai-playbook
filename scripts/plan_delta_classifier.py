#!/usr/bin/env python3
"""Plan-bytes delta classifier for graded review certification.

The classifier buckets each hunk of a plan-bytes delta into the exempt
classes of the binding's Exempt class term or ``unclassified``:

- ``checkbox-flip``: only the forward ``- [ ]`` to ``- [x]`` flip on an
  otherwise byte-identical line; the reverse flip, ``- [X]``, and any
  other same-line byte change are unclassified.
- ``whitespace``: whitespace-run collapse and blank-line add or remove,
  constrained to structure-preserving shapes (the leading-indent quantity
  class of each affected line is unchanged, a tab counted as four columns
  and bucketed zero / one to three / four or more; no adjacency to a
  four-space-or-tab line whose block type would flip; no list loose/tight
  flip; no trailing hard-break spacing change; no adjacency to a line
  excluded in either the source or the resulting text, since a
  blank-line change can flip setext-underline status between the two
  texts).
- ``typography``: the punctuation-equivalence map with exactly one
  em-dash arm (comma, with surrounding spaces normalized to a comma plus
  one trailing space), en dash to hyphen with single-space
  normalization, curly quotes to straight, the ellipsis character to
  three periods, and non-breaking space to space; never adjacent to a
  digit on both sides, never on a heading line, and case is never
  normalized. Legacy hyphen, colon, and semicolon em-dash shapes are
  unclassified and take the operator ack path.

Every exempt class is recognized only on lines outside the excluded
regions scanned by corrections_record (fences, inline code spans,
indented code blocks, setext underlines, thematic breaks, table
delimiter rows, link destinations). Case is never normalized.

Library surface: ``classify_lines(old_bytes, new_bytes)`` returns the
hunk list (each hunk: ``header``, ``digest``, ``class``, ``reason``);
``exempt_verdict(hunks)`` grades a whole delta; ``classify_delta`` adds
the bytes-changed-no-hunks refusal so a digest-changing delta with no
line-level hunks is never vacuously exempt, and refuses any hunk-bearing
delta whose sides disagree on the trailing newline (the line model drops
that fact); ``build_row`` produces
corrections rows through corrections_record's schema builder; an
operator-acked row records the emitting session's nonempty
``author_session_id``, which the CLI derives from
scripts/session_channel.py, and a missing or empty identity refuses the
emission so the hop stays on the fresh-review path, while a
script-verified row never carries the key. Refusals
start with MARKER_PREFIX and contain no banned literal. Decoding is
UTF-8 strict. Consumers: the staging validator and the readiness gate
re-run the classifier over bytes re-derived from git.

Directory-plan CLI layer: the ``--plan`` operand resolves through
``plan_shape.resolve_plan_operand``; a directory plan classifies per
file (the charter plus every task file from the resolver's sorted list),
each hunk header decorated with the file's operand-relative path, and
the corrections chain records one row per changed file. A manifest-level
add or remove of a task file (the file set at the ``--since`` commit
disagrees with the resolver's file list) is a structural delta, never
exempt. The single-file operand path is unchanged.
"""

import argparse
import difflib
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import corrections_record as cr
import plan_shape

CLASS_CHECKBOX = "checkbox-flip"
CLASS_WHITESPACE = "whitespace"
CLASS_TYPOGRAPHY = "typography"
CLASS_UNCLASSIFIED = "unclassified"
EXEMPT_CLASSES = (CLASS_CHECKBOX, CLASS_WHITESPACE, CLASS_TYPOGRAPHY)

# Hunk digests hash the change content only (old side prefixed "-",
# new side prefixed "+"), never line numbers, so the same edit at
# different offsets carries the same digest for gap-row quoting.
_CHECKBOX_RE = re.compile(r"^ {0,3}(?:[-*+]|\d{1,9}[.)]) \[([ xX])\] ")
_HEADING_RE = re.compile(r"^ {0,3}#{1,6}(?:[ \t]|$)")
_LIST_MARKER_RE = re.compile(r"^ {0,3}(?:[-*+]|\d{1,9}[.)])(?:[ \t]|$)")
_TRAIL_WS_RE = re.compile(r"[ \t]*\Z")
_LEAD_WS_RE = re.compile(r"[ \t]*")
_WS_RUN_RE = re.compile(r"[ \t]+")
_EM_RE = re.compile(r"[ \t]*\u2014[ \t]*")
_EN_RE = re.compile(r"(?P<l>[ \t]*)\u2013(?P<r>[ \t]*)")
_DASH_RE = re.compile(r"[\u2013\u2014]")
# The punctuation-equivalence map: exactly one em-dash arm (comma);
# the legacy hyphen, colon, and semicolon shapes are absent by design.
_CURLY_MAP = (("\u2018", "'"), ("\u2019", "'"),
              ("\u201c", "\""), ("\u201d", "\""),
              ("\u2026", "..."), ("\u00a0", " "))
_MAP_MEMBERS = ("\u2014", "\u2013", "\u2018", "\u2019",
                "\u201c", "\u201d", "\u2026", "\u00a0")
# Hunks split on any equal run: each contiguous change is its own hunk,
# so unrelated exempt changes never merge into one mixed hunk.
def _change_groups(opcodes):
    groups = []
    current = None
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            if current is not None:
                groups.append(tuple(current))
                current = None
            continue
        if current is None:
            current = [i1, i2, j1, j2]
        else:
            current[1] = i2
            current[3] = j2
    if current is not None:
        groups.append(tuple(current))
    return groups


def _en_repl(match):
    return " - " if (match.group("l") or match.group("r")) else "-"


def _typography_candidate(line):
    line = _EM_RE.sub(", ", line)
    line = _EN_RE.sub(_en_repl, line)
    for source, target in _CURLY_MAP:
        line = line.replace(source, target)
    return line


def _dash_between_digits(line):
    for match in _DASH_RE.finditer(line):
        left = line[:match.start()].rstrip(" \t")
        right = line[match.end():].lstrip(" \t")
        if left and right and left[-1].isdigit() and right[0].isdigit():
            return True
    return False


def _leading_ws(line):
    match = _LEAD_WS_RE.match(line)
    column = 0
    for ch in match.group(0):
        column += 4 - (column % 4) if ch == "\t" else 1
    return len(match.group(0)), column


def _indent_bucket(column):
    if column == 0:
        return 0
    if column <= 3:
        return 1
    return 4


def _checkbox_pair_verdict(old_line, new_line):
    old_match = _CHECKBOX_RE.match(old_line)
    if old_match is None:
        return None
    reason = ("only the forward - [ ] to - [x] flip on an otherwise "
              "byte-identical line is exempt; the reverse flip, - [X], "
              "and any other same-line byte change are unclassified")
    if old_match.group(1) == " ":
        flip = old_line[:old_match.start(1)] + "x" + old_line[old_match.end(1):]
        if new_line == flip:
            return CLASS_CHECKBOX, "forward checkbox flip"
        new_match = _CHECKBOX_RE.match(new_line)
        if new_match is not None and new_match.group(1) == " ":
            return None
        return CLASS_UNCLASSIFIED, reason
    new_match = _CHECKBOX_RE.match(new_line)
    if new_match is None or new_match.group(1) != old_match.group(1):
        return CLASS_UNCLASSIFIED, reason
    return None


def _whitespace_pair_verdict(old_line, new_line):
    trail_old = _TRAIL_WS_RE.search(old_line).group(0)
    trail_new = _TRAIL_WS_RE.search(new_line).group(0)
    if trail_old != trail_new and ("  " in trail_old or "  " in trail_new):
        return CLASS_UNCLASSIFIED, (
            "a change to a line's trailing hard-break spacing (two or "
            "more trailing spaces) is not a whitespace change")
    old_body = old_line[:len(old_line) - len(trail_old)]
    new_body = new_line[:len(new_line) - len(trail_new)]
    old_lead, old_column = _leading_ws(old_body)
    new_lead, new_column = _leading_ws(new_body)
    if _indent_bucket(old_column) != _indent_bucket(new_column):
        return CLASS_UNCLASSIFIED, (
            "the leading-indent quantity class changed across the change "
            "(classes: zero, one to three, four or more; a tab counts as "
            "four columns)")
    old_core = _WS_RUN_RE.sub(" ", old_body[old_lead:])
    new_core = _WS_RUN_RE.sub(" ", new_body[new_lead:])
    if old_core == new_core:
        return CLASS_WHITESPACE, (
            "whitespace-run collapse or re-indent within the same indent "
            "quantity class")
    return None


def _typography_pair_verdict(old_line, new_line):
    if _HEADING_RE.match(old_line) or _HEADING_RE.match(new_line):
        return CLASS_UNCLASSIFIED, (
            "a typography hit on a heading line is left for the operator "
            "ack path, never auto-exempt")
    if not any(member in old_line for member in _MAP_MEMBERS):
        return CLASS_UNCLASSIFIED, (
            "the line changed beyond the punctuation-equivalence map; "
            "case is never normalized")
    if _typography_candidate(old_line) != new_line:
        return CLASS_UNCLASSIFIED, (
            "the line changed beyond the punctuation-equivalence map (the "
            "only em-dash arm is the comma form; legacy hyphen, colon, "
            "and semicolon shapes are unclassified); case is never "
            "normalized")
    if _dash_between_digits(old_line):
        return CLASS_UNCLASSIFIED, (
            "a dash adjacent to a digit on both sides is a numeric range, "
            "never typography")
    return CLASS_TYPOGRAPHY, "punctuation-equivalence substitution"


def _changed_char_range(old_line, new_line):
    limit = min(len(old_line), len(new_line))
    start = 0
    while start < limit and old_line[start] == new_line[start]:
        start += 1
    end = 0
    while end < limit - start and \
            old_line[len(old_line) - 1 - end] == new_line[len(new_line) - 1 - end]:
        end += 1
    return start, len(old_line) - end, start, len(new_line) - end


def _overlaps(spans, start, end):
    return any(span_start < end and start < span_end
               for span_start, span_end in spans)


def _inline_spans_by_line(lines):
    """Per-line inline excluded spans (inline code spans, link
    destinations, autolinks), computed by corrections_record's
    character-level scanner on the same split("\n") line strings this
    classifier diffs, keyed by 1-based line number with base 0. The
    scanner's whole-text char spans would drift left one char per
    preceding CRLF line when mapped onto these coordinates, so they are
    never consulted here; whole-line regions ride
    excluded_line_numbers, whose line numbers agree with this line
    model under CRLF."""
    by_line = {}
    for index, line in enumerate(lines):
        spans = cr._inline_excluded_spans(line, 0)
        if spans:
            by_line[index + 1] = spans
    return by_line


def _blank_change_reason(*neighbors):
    for line, line_number, excluded in neighbors:
        if line is None:
            continue
        _, column = _leading_ws(line)
        if column >= 4:
            return ("a blank-line change adjacent to a four-space-or-tab "
                    "line flips the line's block type")
        if _LIST_MARKER_RE.match(line):
            return ("a blank-line change adjacent to list items flips the "
                    "list between loose and tight form")
        if line_number in excluded:
            return ("a blank-line change adjacent to an excluded region "
                    "of the source or resulting text is never exempt")
    return None


def _classify_pair(context, old_index, new_index):
    old_line = context["old_lines"][old_index]
    new_line = context["new_lines"][new_index]
    if old_line == new_line:
        return None
    if (old_index + 1) in context["old_excluded"] or \
            (new_index + 1) in context["new_excluded"]:
        return CLASS_UNCLASSIFIED, (
            "the changed line lies inside an excluded region (fenced "
            "code, indented code, setext underline, thematic break, "
            "table delimiter row)")
    old_start, old_end, new_start, new_end = _changed_char_range(
        old_line, new_line)
    if _overlaps(context["old_inline"].get(old_index + 1, ()),
                 old_start, old_end) or \
            _overlaps(context["new_inline"].get(new_index + 1, ()),
                      new_start, new_end):
        return CLASS_UNCLASSIFIED, (
            "the changed bytes lie inside an excluded region (inline code "
            "span or link destination)")
    for verdict in (_checkbox_pair_verdict(old_line, new_line),
                    _whitespace_pair_verdict(old_line, new_line)):
        if verdict is not None:
            return verdict
    return _typography_pair_verdict(old_line, new_line)


def _removed_line_verdict(context, old_index, i1, i2, j1, j2):
    line = context["old_lines"][old_index]
    if line.strip():
        return CLASS_UNCLASSIFIED, (
            "a non-blank line was removed; no exempt class removes content")
    neighbors = []
    if old_index > 0:
        neighbors.append((context["old_lines"][old_index - 1], old_index,
                          context["old_excluded"]))
    if old_index + 1 < len(context["old_lines"]):
        neighbors.append((context["old_lines"][old_index + 1], old_index + 2,
                          context["old_excluded"]))
    if j1 == j2:
        # A pure deletion closes the gap in the resulting text, so the
        # boundary lines carry new line numbers there and their excluded
        # status can differ between the texts (a setext underline exists
        # only once the blank before it is gone; the thematic-break
        # sibling is guarded line-locally either way). The gap lives at
        # the new-side offset j1, so the new lines and the new exclusion
        # set are indexed there; indexing the old-side offset i1 reads
        # the wrong line or past the array once an earlier change group
        # has drifted the two sides.
        if j1 > 0:
            neighbors.append((context["new_lines"][j1 - 1], j1,
                              context["new_excluded"]))
        if j1 < len(context["new_lines"]):
            neighbors.append((context["new_lines"][j1], j1 + 1,
                              context["new_excluded"]))
    reason = _blank_change_reason(*neighbors)
    if reason is not None:
        return CLASS_UNCLASSIFIED, reason
    return CLASS_WHITESPACE, "blank line removed"


def _added_line_verdict(context, new_index, i1, i2, j1, j2):
    line = context["new_lines"][new_index]
    if line.strip():
        return CLASS_UNCLASSIFIED, (
            "a non-blank line was added; no exempt class adds content")
    neighbors = []
    if new_index > 0:
        neighbors.append((context["new_lines"][new_index - 1], new_index,
                          context["new_excluded"]))
    if new_index + 1 < len(context["new_lines"]):
        neighbors.append((context["new_lines"][new_index + 1], new_index + 2,
                          context["new_excluded"]))
    if i1 == i2:
        # A pure insertion opens the gap in the source text, so the
        # source-side boundary lines carry the pre-change adjacency and
        # their excluded status can differ between the texts (adding the
        # blank can demote a setext heading to plain text). The gap
        # lives at the old-side offset i1, so the old lines and the old
        # exclusion set are indexed there; indexing the new-side offset
        # j1 reads the wrong line or past the array once an earlier
        # change group has drifted the two sides.
        if i1 > 0:
            neighbors.append((context["old_lines"][i1 - 1], i1,
                              context["old_excluded"]))
        if i1 < len(context["old_lines"]):
            neighbors.append((context["old_lines"][i1], i1 + 1,
                              context["old_excluded"]))
    reason = _blank_change_reason(*neighbors)
    if reason is not None:
        return CLASS_UNCLASSIFIED, reason
    return CLASS_WHITESPACE, "blank line added"


def _classify_hunk(context, i1, i2, j1, j2):
    members = []
    shared = min(i2 - i1, j2 - j1)
    for offset in range(shared):
        verdict = _classify_pair(context, i1 + offset, j1 + offset)
        if verdict is not None:
            members.append(verdict)
    for old_index in range(i1 + shared, i2):
        members.append(_removed_line_verdict(context, old_index,
                                             i1, i2, j1, j2))
    for new_index in range(j1 + shared, j2):
        members.append(_added_line_verdict(context, new_index,
                                           i1, i2, j1, j2))
    if not members:
        return None
    classes = {klass for klass, _ in members}
    if classes == {CLASS_UNCLASSIFIED} or len(classes) > 1:
        refusal = next((reason for klass, reason in members
                        if klass == CLASS_UNCLASSIFIED), None)
        if refusal is None:
            refusal = ("a hunk mixing exempt classes carries no single "
                       "exempt class")
        return CLASS_UNCLASSIFIED, refusal
    return members[0]


def _split_lines(text):
    # The trailing "" split artifact is dropped, so a final newline is
    # invisible here; classify_delta compares the raw bytes' trailing
    # newline separately so that fact is never absorbed silently.
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def _hunk_header(old_lines, new_lines, i1, i2, j1, j2):
    old_count = i2 - i1
    new_count = j2 - j1
    old_start = i1 + 1 if old_count else i1
    new_start = j1 + 1 if new_count else j1
    return "@@ -%d,%d +%d,%d @@" % (old_start, old_count, new_start,
                                    new_count)


def _hunk_digest(old_lines, new_lines, i1, i2, j1, j2):
    payload = b"\n".join(
        [("-" + line).encode("utf-8") for line in old_lines[i1:i2]]
        + [("+" + line).encode("utf-8") for line in new_lines[j1:j2]])
    return cr.sha256_hex(payload)


def classify_lines(old_bytes, new_bytes):
    """The hunk list for the byte delta: each hunk carries ``header``,
    ``digest``, ``class`` (one of EXEMPT_CLASSES or ``unclassified``)
    and the ``reason`` naming the rule applied or violated. Identical
    bytes give no hunks."""
    if old_bytes == new_bytes:
        return []
    old_text = old_bytes.decode("utf-8")
    new_text = new_bytes.decode("utf-8")
    old_lines = _split_lines(old_text)
    new_lines = _split_lines(new_text)
    context = {
        "old_lines": old_lines,
        "new_lines": new_lines,
        "old_excluded": cr.excluded_line_numbers(old_text),
        "new_excluded": cr.excluded_line_numbers(new_text),
        "old_inline": _inline_spans_by_line(old_lines),
        "new_inline": _inline_spans_by_line(new_lines),
    }
    matcher = difflib.SequenceMatcher(a=old_lines, b=new_lines,
                                      autojunk=False)
    hunks = []
    for i1, i2, j1, j2 in _change_groups(matcher.get_opcodes()):
        verdict = _classify_hunk(context, i1, i2, j1, j2)
        if verdict is None:
            continue
        klass, reason = verdict
        hunks.append({
            "header": _hunk_header(old_lines, new_lines, i1, i2, j1, j2),
            "digest": _hunk_digest(old_lines, new_lines, i1, i2, j1, j2),
            "class": klass,
            "reason": reason,
        })
    return hunks


def bytes_changed_no_hunks_reason(old_bytes, new_bytes):
    """The named refusal for a digest-changing delta whose line evidence
    surface shows no hunks (for example a trailing-newline change):
    never an exemption, never a vacuous row."""
    return cr.leg_reason(
        "classify",
        "bytes changed with no hunks: the digests differ (%s.. -> %s..) "
        "while the line evidence surface shows no hunks; the delta is "
        "never vacuously exempt"
        % (cr.sha256_hex(old_bytes)[:12], cr.sha256_hex(new_bytes)[:12]))


def exempt_verdict(hunks):
    """(True, prefixed success message) when every hunk carries an exempt
    class and at least one hunk exists; otherwise (False, prefixed
    refusal naming the unclassified hunk(s) and their violated rules)."""
    if not hunks:
        return False, cr.leg_reason(
            "classify", "no hunks on the evidence surface to exempt")
    bad = [hunk for hunk in hunks
           if hunk["class"] == CLASS_UNCLASSIFIED]
    if bad:
        return False, cr.leg_reason(
            "classify",
            "hunk(s) not exempt: " + "; ".join(
                "%s %s" % (hunk["header"], hunk["reason"])
                for hunk in bad))
    return True, "%sdelta fully exempt: every hunk carries an exempt " \
                 "class (%s)" % (cr.MARKER_PREFIX,
                                 ", ".join(sorted({hunk["class"]
                                                   for hunk in hunks})))


def classify_delta(old_bytes, new_bytes):
    """(hunks, ok, message) for the whole delta: identical bytes pass
    with no hunks; a digest-changing delta with no hunks takes the
    bytes-changed-no-hunks refusal; a hunk-carrying delta whose two
    sides disagree on the trailing newline is unclassified (the line
    model drops that fact); otherwise exempt_verdict grades the hunk
    list."""
    hunks = classify_lines(old_bytes, new_bytes)
    if not hunks:
        if cr.sha256_hex(old_bytes) != cr.sha256_hex(new_bytes):
            return hunks, False, bytes_changed_no_hunks_reason(
                old_bytes, new_bytes)
        return hunks, True, cr.MARKER_PREFIX + "no delta: identical bytes"
    if old_bytes.endswith(b"\n") != new_bytes.endswith(b"\n"):
        return hunks, False, cr.leg_reason(
            "classify",
            "the delta changes the trailing newline while the line "
            "evidence surface shows hunk(s); the newline fact is "
            "invisible to the line model, so the delta is unclassified")
    ok, message = exempt_verdict(hunks)
    return hunks, ok, message


def build_row(kind, old_bytes, new_bytes, evidence_commit, hunks,
              receipt=None, recorded_at=None,
              recorded_by="plan_delta_classifier", author_session_id=None):
    """A corrections row built through corrections_record's schema builder
    (row_keys + validate_row), so every emitted row is born-conformant.
    Only an operator-acked row records the emitting session's identity:
    the caller passes the nonempty value the session-channel helper
    returned, and a missing (None) or empty identity refuses the
    emission so the hop stays on the fresh-review path - there is no
    key-free operator-acked default emission. A script-verified row
    never carries the key."""
    row = {
        "kind": kind,
        "before_digest": cr.sha256_hex(old_bytes),
        "after_digest": cr.sha256_hex(new_bytes),
        "evidence_commit": evidence_commit,
        "hunks": [{"header": hunk["header"], "digest": hunk["digest"]}
                  for hunk in hunks],
        "recorded_at": recorded_at,
        "recorded_by": recorded_by,
    }
    if row["recorded_at"] is None:
        row["recorded_at"] = _utc_now()
    if kind == cr.KIND_OPERATOR_ACKED:
        row["receipt"] = receipt
        if author_session_id is None:
            raise cr.CorrectionsSchemaError(cr.leg_reason(
                "schema",
                "operator-acked emission refused: no author session "
                "identity was provided; the hop remains on the "
                "fresh-review path"))
        if not isinstance(author_session_id, str) or \
                not author_session_id.strip():
            raise cr.CorrectionsSchemaError(cr.leg_reason(
                "schema",
                "operator-acked emission refused: the author session "
                "identity is empty; the hop remains on the "
                "fresh-review path"))
        row[cr.AUTHOR_SESSION_KEY] = author_session_id
    elif author_session_id is not None:
        raise cr.CorrectionsSchemaError(cr.leg_reason(
            "schema",
            "a script-verified row never carries author_session_id"))
    cr.validate_row(row, cr.FAMILY_PLAN)
    return row


def _utc_now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def run_directory_plan_mode(args):
    """The ``--plan`` directory layer over the resolver: one classified
    delta per file (charter plus sorted task files), hunk headers
    decorated with the file's operand-relative path, one corrections row
    per changed file, and the manifest-level structural refusal when the
    file set at --since disagrees with the resolver's file list. Exit
    vocabulary is the CLI's (0 pass, 1 fail, 2 indeterminate, 3 tool
    error); the single-file operand path never enters here."""
    try:
        shape = plan_shape.resolve_plan_operand(args.plan)
    except plan_shape.PlanShapeRefusal as exc:
        return tool_error(str(exc))
    plan_absolute = shape.root
    toplevel = cr.git_text(plan_absolute.parent, "rev-parse",
                           "--show-toplevel")
    if toplevel is None:
        return tool_error("the plan operand %s is not inside a git "
                          "repository" % args.plan)
    root = toplevel.strip()
    dir_rel = os.path.relpath(str(plan_absolute), root).replace(os.sep, "/")
    if dir_rel == os.pardir or dir_rel.startswith(os.pardir + os.sep):
        return tool_error("the plan operand %s lies outside the "
                          "repository at %s" % (args.plan, root))
    since = cr.resolve_commit(root, args.since)
    if since is None:
        return tool_error("the --since ref %r does not resolve to a "
                          "commit" % args.since)
    listing = cr.git_text(root, "ls-tree", "-r", "--name-only", since,
                          "--", dir_rel)
    if listing is None:
        return indeterminate(
            "git ls-tree failed over the resolved commit %s" % since)
    old_files = sorted(ln.strip() for ln in listing.splitlines()
                       if ln.strip())
    entries = [(plan_shape.CHARTER_FILENAME,
                plan_absolute / plan_shape.CHARTER_FILENAME)]
    entries += [(rel, path) for rel, path, _text in shape.task_files]
    new_files = ["%s/%s" % (dir_rel, rel) for rel, _path in entries]
    new_set = set(new_files)
    added = sorted(rel for rel in new_files if rel not in set(old_files))
    removed = sorted(path for path in old_files if path not in new_set)
    print("plan: %s" % dir_rel)
    print("shape: directory (charter + %d task file(s))"
          % len(shape.task_files))
    print("since: %s" % since)
    structural_message = None
    if added or removed:
        parts = []
        if added:
            parts.append("added: %s" % ", ".join(added))
        if removed:
            parts.append("removed: %s" % ", ".join(removed))
        structural_message = cr.leg_reason(
            "classify",
            "structural delta: the plan manifest's file set changed (%s); "
            "a manifest-level task-file add or remove is never exempt"
            % "; ".join(parts))
        # A structural delta never classifies per file: an added task file
        # carries no --since blob and a removed one no working-tree bytes,
        # so the manifest-level refusal is the whole verdict.
        for rel, _path in entries:
            print("file: %s" % rel)
        print("refusal: %s" % structural_message)
        emit_outcome(1)
        return 1
    all_hunks = []
    changed = []
    for rel, path in entries:
        file_rel = "%s/%s" % (dir_rel, rel)
        try:
            new_bytes = path.read_bytes()
        except OSError as exc:
            return tool_error("the plan operand %s is unreadable: %s"
                              % (file_rel, exc))
        try:
            new_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            return tool_error("the plan operand %s is not decodable UTF-8 "
                              "text: %s" % (file_rel, exc))
        old_bytes = cr.blob_bytes(root, since, file_rel)
        if old_bytes is None:
            return indeterminate(
                "the plan blob %s:%s is unreadable: git plumbing failed "
                "over resolved inputs" % (since, file_rel))
        try:
            old_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            return tool_error("the plan blob %s:%s is not decodable UTF-8 "
                              "text: %s" % (since, file_rel, exc))
        hunks, _ok, _message = classify_delta(old_bytes, new_bytes)
        print("file: %s" % rel)
        print("before digest: %s" % cr.sha256_hex(old_bytes))
        print("after digest: %s" % cr.sha256_hex(new_bytes))
        for index, hunk in enumerate(hunks, 1):
            hunk["header"] = "%s: %s" % (rel, hunk["header"])
            print("hunk %d: %s %s (%s)"
                  % (index, hunk["header"], hunk["class"], hunk["reason"]))
        if hunks:
            changed.append((rel, old_bytes, new_bytes, hunks))
            all_hunks.extend(hunks)
    if not all_hunks:
        print("verdict: %sno delta: identical bytes" % cr.MARKER_PREFIX)
        emit_outcome(0)
        return 0
    ok, message = exempt_verdict(all_hunks)
    if ok:
        print("verdict: %s" % message)
    else:
        print("refusal: %s" % message)
    if args.emit_row:
        if not changed:
            print("no row: a corrections row is never vacuous")
        elif not ok and args.kind != cr.KIND_OPERATOR_ACKED:
            print("no row: a script-verified row requires every hunk "
                  "exempt; the ack path is --kind operator-acked "
                  "--receipt")
        else:
            head = cr.resolve_commit(root, "HEAD")
            if head is None:
                return tool_error("HEAD does not resolve; no evidence "
                                  "commit for the row")
            try:
                receipt = load_receipt(args.receipt) \
                    if args.kind == cr.KIND_OPERATOR_ACKED else None
                # The emitting session's identity comes from the shared
                # session-channel helper (Task 3); an empty derivation
                # refuses the operator-acked emission below and the hop
                # remains on the fresh-review path.
                author = cr.session_identity() \
                    if args.kind == cr.KIND_OPERATOR_ACKED else None
                for _rel, old_bytes, new_bytes, hunks in changed:
                    row = build_row(args.kind, old_bytes, new_bytes, head,
                                    hunks, receipt=receipt,
                                    author_session_id=author)
                    print("corrections-row-json: %s"
                          % json.dumps(row, sort_keys=True))
            except (OSError, ValueError, UnicodeDecodeError) as exc:
                return tool_error("the receipt operand %s is unreadable "
                                  "or not decodable JSON: %s"
                                  % (args.receipt, exc))
            except cr.CorrectionsSchemaError as exc:
                return tool_error(str(exc))
    emit_outcome(0 if ok else 1)
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# CLI entry
# ---------------------------------------------------------------------------

# Outcome contract (scripts/OUTCOME_CONTRACT.md): the four outcomes and the
# argparse override. A usage violation exits 3 with a final `OUTCOME:
# tool_error` line on stderr before exit; `--help` stays a metadata exit
# without an `OUTCOME:` line; every classified run's final line is on stdout.
OUTCOME_LABELS = {0: "pass", 1: "fail", 2: "indeterminate", 3: "tool_error"}


class OutcomeArgumentParser(argparse.ArgumentParser):
    """Argument parser whose usage errors exit 3 (tool error) with a final
    `OUTCOME: tool_error` line on stderr before exit, overriding argparse's
    default exit 2; `--help` stays a metadata exit without an `OUTCOME:`
    line."""

    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write("%s: error: %s\n" % (self.prog, message))
        sys.stderr.write("OUTCOME: %s\n" % OUTCOME_LABELS[3])
        raise SystemExit(3)


def emit_outcome(code):
    print("OUTCOME: %s" % OUTCOME_LABELS[code])


def indeterminate(message):
    """A git plumbing failure over already-resolved inputs (exit 2, never
    a domain finding)."""
    sys.stderr.write("plan-delta-classifier: %s\n" % message)
    emit_outcome(2)
    return 2


def tool_error(message):
    """An input that never resolved (operand, ref, receipt) (exit 3)."""
    sys.stderr.write("plan-delta-classifier: %s\n" % message)
    emit_outcome(3)
    return 3


def load_receipt(path):
    """The receipt operand as a JSON object; schema errors surface through
    corrections_record's row validation at build time."""
    raw = Path(path).read_bytes()
    doc = json.loads(raw.decode("utf-8"))
    if not isinstance(doc, dict):
        raise cr.CorrectionsSchemaError(
            cr.leg_reason("schema", "receipt operand is not a JSON object"))
    return doc


def main(argv=None):
    parser = OutcomeArgumentParser(
        prog="plan_delta_classifier.py",
        description="Classify a plan file's delta since a start commit's "
                    "blob and emit corrections rows.")
    parser.add_argument("--plan", required=True,
                        help="path to the plan file (working tree operand)")
    parser.add_argument("--since", required=True,
                        help="start commit whose blob is the before side")
    parser.add_argument("--emit-row", action="store_true",
                        help="print the corrections row as one JSON line")
    parser.add_argument("--kind",
                        choices=(cr.KIND_SCRIPT_VERIFIED,
                                 cr.KIND_OPERATOR_ACKED),
                        default=cr.KIND_SCRIPT_VERIFIED)
    parser.add_argument("--receipt",
                        help="receipt JSON operand for the operator-acked "
                             "kind")
    args = parser.parse_args(argv)
    if args.kind == cr.KIND_OPERATOR_ACKED and not args.receipt:
        return tool_error("--kind operator-acked requires --receipt "
                          "<receipt-json>")
    if args.receipt and args.kind != cr.KIND_OPERATOR_ACKED:
        return tool_error("--receipt requires --kind operator-acked")
    if Path(args.plan).is_dir():
        return run_directory_plan_mode(args)
    try:
        new_bytes = Path(args.plan).read_bytes()
    except OSError as exc:
        return tool_error("the plan operand %s is unreadable: %s"
                          % (args.plan, exc))
    try:
        new_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        return tool_error("the plan operand %s is not decodable UTF-8 "
                          "text: %s" % (args.plan, exc))
    plan_absolute = Path(args.plan).resolve()
    toplevel = cr.git_text(plan_absolute.parent, "rev-parse",
                           "--show-toplevel")
    if toplevel is None:
        return tool_error("the plan operand %s is not inside a git "
                          "repository" % args.plan)
    root = toplevel.strip()
    rel = os.path.relpath(str(plan_absolute), root)
    if rel == os.pardir or rel.startswith(os.pardir + os.sep):
        return tool_error("the plan operand %s lies outside the "
                          "repository at %s" % (args.plan, root))
    since = cr.resolve_commit(root, args.since)
    if since is None:
        return tool_error("the --since ref %r does not resolve to a "
                          "commit" % args.since)
    old_bytes = cr.blob_bytes(root, since, rel)
    if old_bytes is None:
        listing = cr.git_text(root, "ls-tree", since, "--", rel)
        if listing is None:
            return indeterminate(
                "git ls-tree failed over the resolved commit %s" % since)
        if not listing.strip():
            return tool_error("the plan path %s is not tracked at the "
                              "--since commit %s" % (rel, since))
        return indeterminate(
            "the plan blob %s:%s is unreadable: git plumbing failed over "
            "resolved inputs" % (since, rel))
    try:
        old_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        return tool_error("the plan blob %s:%s is not decodable UTF-8 "
                          "text: %s" % (since, rel, exc))
    hunks, ok, message = classify_delta(old_bytes, new_bytes)
    print("plan: %s" % rel)
    print("since: %s" % since)
    print("before digest: %s" % cr.sha256_hex(old_bytes))
    print("after digest: %s" % cr.sha256_hex(new_bytes))
    for index, hunk in enumerate(hunks, 1):
        print("hunk %d: %s %s (%s)"
              % (index, hunk["header"], hunk["class"], hunk["reason"]))
    if ok:
        print("verdict: %s" % message)
    else:
        print("refusal: %s" % message)
    if args.emit_row:
        if not hunks:
            print("no row: a corrections row is never vacuous")
        elif not ok and args.kind != cr.KIND_OPERATOR_ACKED:
            print("no row: a script-verified row requires every hunk "
                  "exempt; the ack path is --kind operator-acked "
                  "--receipt")
        else:
            head = cr.resolve_commit(root, "HEAD")
            if head is None:
                return tool_error("HEAD does not resolve; no evidence "
                                  "commit for the row")
            try:
                receipt = load_receipt(args.receipt) \
                    if args.kind == cr.KIND_OPERATOR_ACKED else None
                # The emitting session's identity comes from the shared
                # session-channel helper (Task 3); an empty derivation
                # refuses the operator-acked emission below and the hop
                # remains on the fresh-review path.
                author = cr.session_identity() \
                    if args.kind == cr.KIND_OPERATOR_ACKED else None
                row = build_row(args.kind, old_bytes, new_bytes, head,
                                hunks, receipt=receipt,
                                author_session_id=author)
            except (OSError, ValueError, UnicodeDecodeError) as exc:
                return tool_error("the receipt operand %s is unreadable "
                                  "or not decodable JSON: %s"
                                  % (args.receipt, exc))
            except cr.CorrectionsSchemaError as exc:
                return tool_error(str(exc))
            print("corrections-row-json: %s"
                  % json.dumps(row, sort_keys=True))
    emit_outcome(0 if ok else 1)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
