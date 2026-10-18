#!/usr/bin/env python3
"""Interim single-file plan task span extractor.

Byte-level span extraction for single-file plans (backlog row
docs/history/backlog/2026-10-05-plan-worker-read-contract.md): a worker
prompt cites a task's exact bytes plus the plan's Terms section instead of
hand-pinned line ranges. The extractor is explicitly disposable: the
plan-directory shape supersedes it.

Span rules, over newline-delimited lines:
- The task N span starts at the first line matching ``### Task N:`` (the
  colon is part of the heading) and runs through the line before the next
  heading line starting with ``### `` or ``## ``, whichever comes first;
  the last section runs to end of file. The start offset is the byte
  offset of the heading line; the end offset is the byte offset of the
  terminator line or the file length, so the span is ``data[start:end]``
  and always carries the included lines' newlines.
- The Terms span starts at the line ``## Terms`` and runs through the line
  before the next ``## `` heading (or end of file).
- The Standing constraints span starts at the first line ``## Standing
  constraints`` and runs through the line before the next ``## `` heading
  (or end of file), the Terms span's rule with first match winning; the
  header line is emitted only when the section exists and the plan stays
  byte-compatible when it does not.

stdout grammar, full mode (the default)::

  plan: <path as given>
  task: <N>
  task-span: start=<int> end=<int> sha256=<hex>
  constraints-span: start=<int> end=<int> sha256=<hex>  [only when the
      section exists]
  terms-span: start=<int> end=<int> sha256=<hex>
  ---span-begin---
  <raw span bytes, verbatim>

``--spans-only`` prints just the header (offsets and digests, no marker
line and no bytes). The digests hash the exact span bytes (sha256 hex), so
a consumer can read a task's declared context surface, Terms plus the task
plus Standing constraints, as three whole verified slices.

Outcome contract (scripts/OUTCOME_CONTRACT.md): exit 0 pass; exit 3
tool_error (unreadable or non-UTF-8 operand, a plan-directory operand
(the plan-directory shape: the refusal points to whole-file
charter-plus-task reads, never span extraction across files), missing
``## Terms`` section, or task N not found) with a named reason line
before the final outcome line. Declared placement deviation: every final ``OUTCOME:`` line
is written to stderr because stdout carries the raw span bytes in full
mode (the same deviation done-lock.sh declares for its eval-consumed
acquire stdout). A run with no final OUTCOME line is tool error: stop and
re-derive from disk. ``--help`` is a metadata exit without an OUTCOME
line.
"""

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path

OUTCOME_LABELS = {0: "pass", 1: "fail", 2: "indeterminate", 3: "tool_error"}
SPAN_BEGIN_MARKER = "---span-begin---"

TASK_HEADING_RE = re.compile(r"^### Task (\d+):")
TERMS_HEADING_RE = re.compile(r"^## Terms\r?$")
CONSTRAINTS_HEADING_RE = re.compile(r"^## Standing constraints\r?$")


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
    sys.stderr.write("OUTCOME: %s\n" % OUTCOME_LABELS[code])


def tool_error(message):
    """An input that never resolved (operand, section, task) (exit 3)."""
    sys.stderr.write("plan-task-span: %s\n" % message)
    emit_outcome(3)
    return 3


def segments(data):
    """(byte offset, raw line bytes) for every newline-delimited segment;
    the offset is the segment's first byte and the split newline belongs to
    the segment that precedes it. UTF-8 multibyte sequences never contain
    the 0x0A byte, so byte splitting and per-line decoding agree."""
    found = []
    offset = 0
    for raw_line in data.split(b"\n"):
        found.append((offset, raw_line))
        offset += len(raw_line) + 1
    return found


def line_text(raw_line):
    """The decoded line without its carriage return (offsets stay raw)."""
    return raw_line.decode("utf-8").rstrip("\r")


def find_index(segs, predicate):
    """The first segment index whose decoded line satisfies the
    predicate, or None."""
    for index, (_, raw_line) in enumerate(segs):
        if predicate(line_text(raw_line)):
            return index
    return None


def span_bytes(data, segs, start_index, h3_terminates):
    """The exact span bytes for the section starting at start_index: from
    its offset through the line before the next terminator heading (``## ``
    always, ``### `` when h3_terminates), or through end of file."""
    start_offset = segs[start_index][0]

    def terminates(line):
        if line.startswith("## "):
            return True
        return h3_terminates and line.startswith("### ")

    for index in range(start_index + 1, len(segs)):
        if terminates(line_text(segs[index][1])):
            return data[start_offset:segs[index][0]]
    return data[start_offset:]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main(argv=None):
    parser = OutcomeArgumentParser(
        prog="plan_task_span.py",
        description="Print a single-file plan's task span bytes (Terms "
                    "always included in the header) with byte offsets and "
                    "sha256 digests.")
    parser.add_argument("--plan", required=True,
                        help="path to the plan file (working tree operand)")
    parser.add_argument("--task", required=True, type=int,
                        help="task number whose span to extract (the "
                             "``### Task N:`` heading)")
    parser.add_argument("--spans-only", action="store_true",
                        help="print just the header (offsets and digests, "
                             "no span bytes)")
    args = parser.parse_args(argv)
    if args.task < 1:
        return tool_error("task numbers start at 1; got %d" % args.task)
    if Path(args.plan).is_dir():
        # The plan-directory shape supersedes this extractor: the charter
        # and each task file are read whole beside each other, so span
        # extraction across files never happens. A directory operand
        # refuses loud with that pointer (no silent skip, no traceback).
        return tool_error(
            "the plan operand %s is a plan directory (the plan-directory "
            "shape): this extractor does not extract spans across files; "
            "read the charter and that task's own task file whole instead "
            "(the plan-directory shape supersedes this extractor)"
            % args.plan)
    try:
        data = Path(args.plan).read_bytes()
    except OSError as exc:
        return tool_error("the plan operand %s is unreadable: %s"
                          % (args.plan, exc))
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as exc:
        return tool_error("the plan operand %s is not decodable UTF-8 "
                          "text: %s" % (args.plan, exc))
    segs = segments(data)
    terms_index = find_index(segs, lambda line: TERMS_HEADING_RE.match(line))
    if terms_index is None:
        return tool_error("the plan %s has no `## Terms` section (no line "
                          "matching `## Terms`)" % args.plan)
    task_index = find_index(
        segs,
        lambda line: (TASK_HEADING_RE.match(line) is not None
                      and int(TASK_HEADING_RE.match(line).group(1))
                      == args.task))
    if task_index is None:
        return tool_error("task %d not found in the plan %s (no line "
                          "matching `### Task %d:`)"
                          % (args.task, args.plan, args.task))
    task_raw = span_bytes(data, segs, task_index, h3_terminates=True)
    terms_raw = span_bytes(data, segs, terms_index, h3_terminates=False)
    task_start = segs[task_index][0]
    terms_start = segs[terms_index][0]
    task_end = task_start + len(task_raw)
    terms_end = terms_start + len(terms_raw)
    # The Standing constraints span rides the Terms span's rule and is
    # tolerated absent: a plan without the section emits no line and the
    # outcome contract is unchanged.
    constraints_index = find_index(
        segs, lambda line: CONSTRAINTS_HEADING_RE.match(line))
    constraints_line = ""
    if constraints_index is not None:
        constraints_raw = span_bytes(data, segs, constraints_index,
                                     h3_terminates=False)
        constraints_start = segs[constraints_index][0]
        constraints_line = (
            "constraints-span: start=%d end=%d sha256=%s\n"
            % (constraints_start,
               constraints_start + len(constraints_raw),
               digest(constraints_raw)))
    header = (
        "plan: %s\n"
        "task: %d\n"
        "task-span: start=%d end=%d sha256=%s\n"
        "%s"
        "terms-span: start=%d end=%d sha256=%s\n"
        % (args.plan, args.task,
           task_start, task_end, digest(task_raw),
           constraints_line,
           terms_start, terms_end, digest(terms_raw)))
    try:
        sys.stdout.write(header)
        if not args.spans_only:
            sys.stdout.write(SPAN_BEGIN_MARKER + "\n")
            sys.stdout.flush()
            sys.stdout.buffer.write(task_raw)
            sys.stdout.buffer.flush()
    except BrokenPipeError:
        # The consumer closed stdout (a truncated capture): per the outcome
        # contract that is never a pass, so report tool error with the final
        # OUTCOME line on the still-open stderr instead of a bare traceback.
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return tool_error("the span consumer closed stdout before the "
                          "header and span bytes were fully read")
    emit_outcome(0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
