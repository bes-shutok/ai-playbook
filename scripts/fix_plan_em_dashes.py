#!/usr/bin/env python3
"""Em-dash write-time fence for plan bytes.

Substitutes every em dash (U+2014) outside the excluded regions scanned
by corrections_record (fenced code blocks, inline code spans, indented
code blocks, setext underlines, thematic breaks, table delimiter rows,
link destinations) with the comma form of the binding's typography map
(agent_workflow_guidelines.md section 39.1): the em dash and any
surrounding spaces become a comma plus one trailing space, with no
space before the comma and never a hyphen. A dash adjacent to a digit
on both sides, across the surrounding spaces, is a numeric range and
stays untouched, matching the classifier's unclassified rule.

A fenced region left unclosed is the modeled refusal: a scanner
disagreement about the excluded tail never becomes a silent
substitution, so the run exits 3 with no byte written.

The rewrite is in place, reporting per-line substitution counts. The
substituted bytes re-classify as the typography exempt class, so a
boundary scan over them re-binds without a fresh round. Outcome
contract (scripts/OUTCOME_CONTRACT.md): exit 0 pass, exit 3 tool
error, and a final `OUTCOME:` line on every run.
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import corrections_record as cr

# The only em-dash arm of the typography map: the surrounding spaces
# fold into a comma plus one trailing space. Never a hyphen: the legacy
# hyphen, colon, and semicolon shapes stay outside the map by design.
EM_RE = re.compile(r"[ \t]*\u2014[ \t]*")
REPLACEMENT = ", "

PROG = "fix_plan_em_dashes.py"
OUTCOME_LABELS = {0: "pass", 3: "tool_error"}

# A prose line appended past the operand's bytes: corrections_record's
# scanner excludes it exactly when a fence is still open at end of file
# (an unclosed fenced region extends to end of file), so the
# fence-balance verdict is the scanner's own judgment, never a
# re-implementation of its state machine.
FENCE_PROBE = "zz-fence-balance-probe-zz"


def unbalanced_fence(text):
    """True when the scanner's fence state is still open at end of
    file, detected through corrections_record's scanner itself."""
    if not text:
        return False
    probe = text if text.endswith("\n") else text + "\n"
    probe += FENCE_PROBE + "\n"
    return cr.line_fully_excluded(probe, len(probe.splitlines()))


def substitute(text):
    """(new_text, counts) with counts keyed by 1-based line number. The
    exclusion decision is derived from drift-free outputs only:
    corrections_record's excluded_line_numbers marks the whole-line
    regions (fenced or indented code, setext underline, thematic break,
    table delimiter row), and the inline regions (inline code spans,
    link destinations, autolinks) are bounded by per-line spans that
    corrections_record's character-level scanner computes on the very
    line strings this function iterates. Mapping the scanner's
    whole-text char spans onto these coordinates would drift left one
    char per preceding CRLF line and let a match near a span's end
    escape the guard, so no whole-text span is consulted. A match with
    a digit on both sides across the surrounding spaces is a numeric
    range and stays unchanged."""
    excluded = cr.excluded_line_numbers(text)
    lines = text.split("\n")
    counts = {}
    for index, line in enumerate(lines):
        if index + 1 in excluded:
            continue
        local_spans = cr._inline_excluded_spans(line, 0)
        pieces = []
        cursor = 0
        made = 0
        for match in EM_RE.finditer(line):
            if any(span_start < match.end() and match.start() < span_end
                   for span_start, span_end in local_spans):
                continue
            left = line[:match.start()].rstrip(" \t")
            right = line[match.end():].lstrip(" \t")
            if left and right and left[-1].isdigit() and right[0].isdigit():
                continue
            pieces.append(line[cursor:match.start()])
            pieces.append(REPLACEMENT)
            cursor = match.end()
            made += 1
        if made:
            pieces.append(line[cursor:])
            lines[index] = "".join(pieces)
            counts[index + 1] = made
    return "\n".join(lines), counts


# Outcome contract (scripts/OUTCOME_CONTRACT.md): a usage violation
# exits 3 with a final `OUTCOME: tool_error` line on stderr before
# exit; every classified run's final line is on stdout.
class OutcomeArgumentParser(argparse.ArgumentParser):
    """Argument parser whose usage errors exit 3 (tool error) with a
    final `OUTCOME: tool_error` line on stderr before exit."""

    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write("%s: error: %s\n" % (PROG, message))
        sys.stderr.write("OUTCOME: %s\n" % OUTCOME_LABELS[3])
        raise SystemExit(3)


def tool_error(message):
    """An input that never resolved (operand unreadable, not UTF-8, or
    not writable) or the modeled unbalanced-fence refusal (exit 3)."""
    sys.stderr.write("%s: %s\n" % (PROG, message))
    print("OUTCOME: %s" % OUTCOME_LABELS[3])
    return 3


def main(argv=None):
    parser = OutcomeArgumentParser(
        prog=PROG,
        description="Substitute em dashes outside excluded plan-bytes "
                    "regions with the comma form, in place.")
    parser.add_argument("plan",
                        help="path to the plan Markdown operand (rewritten "
                             "in place)")
    args = parser.parse_args(argv)
    path = Path(args.plan)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return tool_error("the operand %s is unreadable: %s"
                          % (args.plan, exc))
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return tool_error("the operand %s is not decodable UTF-8 text: %s"
                          % (args.plan, exc))
    if unbalanced_fence(text):
        return tool_error(
            "unbalanced fence: a fenced region is opened but never closed "
            "(an unclosed fenced region extends to end of file); refusing "
            "to rewrite rather than guess the excluded tail; close or "
            "remove the fence by hand")
    new_text, counts = substitute(text)
    if new_text != text:
        try:
            path.write_bytes(new_text.encode("utf-8"))
        except OSError as exc:
            return tool_error("the operand %s is not writable: %s"
                              % (args.plan, exc))
    print("operand: %s" % args.plan)
    total = 0
    for line_number in sorted(counts):
        made = counts[line_number]
        total += made
        print("line %d: %d substitution%s"
              % (line_number, made, "" if made == 1 else "s"))
    print("total: %d substitution%s" % (total, "" if total == 1 else "s"))
    print("OUTCOME: %s" % OUTCOME_LABELS[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
