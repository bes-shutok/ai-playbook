#!/usr/bin/env python3
"""Selftest for plan_task_span.py (interim plan task span extractor).

The fixture plan is built in memory from a line list and written to a
TemporaryDirectory; expected spans and digests are recomputed independently
from that line list (byte-level), never through the extractor's own
helpers. No host state is touched and no git repository is needed.
"""

import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

EXTRACTOR = Path(__file__).resolve().parent / "plan_task_span.py"
SPAN_BEGIN_MARKER = "---span-begin---"

LINES = [
    "# Sample plan",
    "",
    "Intro prose.",
    "",
    "## Terms",
    "- alpha: the first term",
    "- beta: the second term",
    "",
    "## Overview",
    "Overview prose.",
    "",
    "### Task 1: First task",
    "Step one.",
    "Step two.",
    "",
    "### Task 2: Second task",
    "Step three.",
    "",
    "### Task 3: Third task",
    "Final step.",
]
PLAN_BYTES = ("\n".join(LINES) + "\n").encode("utf-8")


def line_offset(prefix):
    """Byte offset of the first fixture line starting with prefix."""
    offset = 0
    for line in LINES:
        if line.startswith(prefix):
            return offset
        offset += len(line.encode("utf-8")) + 1
    raise AssertionError("no fixture line starts with %r" % prefix)


def expected_span(start_prefix, stop_prefixes):
    """The exact span bytes for the section starting at start_prefix,
    through the line before the next line starting with any stop prefix
    (or through end of file), recomputed from the line list."""
    start_line = None
    for index, line in enumerate(LINES):
        if line.startswith(start_prefix):
            start_line = index
            break
    if start_line is None:
        raise AssertionError("no fixture line starts with %r" % start_prefix)
    end_line = len(LINES)
    for index in range(start_line + 1, len(LINES)):
        if any(LINES[index].startswith(stop)
               for stop in stop_prefixes):
            end_line = index
            break
    return ("\n".join(LINES[start_line:end_line]) + "\n").encode("utf-8")


TASK_1 = expected_span("### Task 1:", ("### ", "## "))
TASK_2 = expected_span("### Task 2:", ("### ", "## "))
TASK_3 = expected_span("### Task 3:", ("### ", "## "))
TERMS = expected_span("## Terms", ("## ",))


def list_bytes(lines):
    """The exact file bytes for a line list (newline-joined, trailing
    newline), recomputed at byte level independent of the extractor."""
    return ("\n".join(lines) + "\n").encode("utf-8")


def list_offset(lines, prefix):
    """Byte offset of the first list line starting with prefix."""
    offset = 0
    for line in lines:
        if line.startswith(prefix):
            return offset
        offset += len(line.encode("utf-8")) + 1
    raise AssertionError("no line starts with %r" % prefix)


def list_span(lines, start_prefix, stop_prefixes):
    """The exact span bytes for the section starting at the first line
    starting with start_prefix, through the line before the next line
    starting with any stop prefix (or through end of file), recomputed
    from the given line list."""
    start_line = None
    for index, line in enumerate(lines):
        if line.startswith(start_prefix):
            start_line = index
            break
    if start_line is None:
        raise AssertionError("no line starts with %r" % start_prefix)
    end_line = len(lines)
    for index in range(start_line + 1, len(lines)):
        if any(lines[index].startswith(stop) for stop in stop_prefixes):
            end_line = index
            break
    return list_bytes(lines[start_line:end_line])


# The second fixture list: a plan declaring `## Standing constraints`.
# The first list's helpers (line_offset, expected_span, the TASK_N/TERMS
# constants) are hard-bound to the LINES/PLAN_BYTES module globals, so
# this list recomputes spans locally through the parameterized helpers
# above; the subprocess invocation helper (run_cli) reuses cleanly.
CONSTRAINTS_LINES = [
    "# Sample plan",
    "",
    "## Terms",
    "- alpha: the first term",
    "",
    "## Standing constraints",
    "- every task commits with a scoped pathspec",
    "",
    "## Gist & Examples",
    "TLDR: spans, verified.",
    "",
    "### Task 1: First task",
    "Step one.",
]
CONSTRAINTS_PLAN_BYTES = list_bytes(CONSTRAINTS_LINES)


class SpanExtractorTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="plan-task-span-")
        self.addCleanup(self._tmp.cleanup)
        self.plan = Path(self._tmp.name) / "plan.md"
        self.plan.write_bytes(PLAN_BYTES)
        self.constraints_plan = Path(self._tmp.name) / "constraints-plan.md"
        self.constraints_plan.write_bytes(CONSTRAINTS_PLAN_BYTES)

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(EXTRACTOR)] + list(args),
            capture_output=True)

    def last_err_line(self, proc):
        return proc.stderr.decode("utf-8").splitlines()[-1]

    def parse_header(self, stdout_bytes):
        """(header line dict keyed by the key before ': ', payload bytes)
        from a full-mode stdout capture."""
        marker = (SPAN_BEGIN_MARKER + "\n").encode("utf-8")
        self.assertIn(marker, stdout_bytes)
        header_part, _, payload = stdout_bytes.partition(marker)
        fields = {}
        for line in header_part.decode("utf-8").splitlines():
            key, _, value = line.partition(": ")
            fields[key] = value
        return fields, payload

    def check_task_span(self, task_number, expected_bytes):
        proc = self.run_cli("--plan", str(self.plan),
                            "--task", str(task_number))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.last_err_line(proc), "OUTCOME: pass")
        fields, payload = self.parse_header(proc.stdout)
        self.assertEqual(payload, expected_bytes)
        start = PLAN_BYTES.index(expected_bytes)
        end = start + len(expected_bytes)
        self.assertEqual(fields["plan"], str(self.plan))
        self.assertEqual(fields["task"], str(task_number))
        self.assertEqual(fields["task-span"],
                         "start=%d end=%d sha256=%s"
                         % (start, end,
                            hashlib.sha256(expected_bytes).hexdigest()))
        terms_start = PLAN_BYTES.index(TERMS)
        self.assertEqual(fields["terms-span"],
                         "start=%d end=%d sha256=%s"
                         % (terms_start, terms_start + len(TERMS),
                            hashlib.sha256(TERMS).hexdigest()))
        return fields

    def test_task_spans_are_exact_slices(self):
        self.check_task_span(1, TASK_1)
        self.check_task_span(2, TASK_2)
        self.check_task_span(3, TASK_3)
        # The spans are the exact section slices: each carries its heading
        # line and the blank line before the terminator heading.
        self.assertTrue(TASK_1.startswith(b"### Task 1: First task\n"))
        self.assertTrue(TASK_1.endswith(b"Step two.\n\n"))

    def test_third_task_ends_at_end_of_file(self):
        fields, payload = None, None
        proc = self.run_cli("--plan", str(self.plan), "--task", "3")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        fields, payload = self.parse_header(proc.stdout)
        self.assertEqual(payload, TASK_3)
        end = int(fields["task-span"].split(" ")[1].split("=")[1])
        self.assertEqual(end, len(PLAN_BYTES))
        self.assertEqual(payload, PLAN_BYTES[-len(TASK_3):])

    def test_terms_span_always_in_header(self):
        for task_number in (1, 2, 3):
            proc = self.run_cli("--plan", str(self.plan),
                                "--task", str(task_number),
                                "--spans-only")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("terms-span: ", proc.stdout.decode("utf-8"))

    def test_constraints_span_present(self):
        given = list_span(CONSTRAINTS_LINES, "## Standing constraints",
                          ("## ",))
        proc = self.run_cli("--plan", str(self.constraints_plan),
                            "--task", "1")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.last_err_line(proc), "OUTCOME: pass")
        stdout = proc.stdout.decode("utf-8")
        fields, payload = self.parse_header(proc.stdout)
        start = CONSTRAINTS_PLAN_BYTES.index(given)
        expects = ("start=%d end=%d sha256=%s"
                   % (start, start + len(given),
                      hashlib.sha256(given).hexdigest()))
        self.assertEqual(fields["constraints-span"], expects)
        # Shaped exactly like the terms line: offsets and digest only.
        self.assertRegex(fields["constraints-span"],
                         r"^start=\d+ end=\d+ sha256=[0-9a-f]{64}$")
        # Header placement: between the task-span and terms-span lines.
        header_lines = stdout[:stdout.index(SPAN_BEGIN_MARKER + "\n")]
        keys = [line.partition(": ")[0]
                for line in header_lines.splitlines()]
        self.assertEqual(keys, ["plan", "task", "task-span",
                                "constraints-span", "terms-span"])
        # No raw section bytes in either mode: the full-mode payload stays
        # the task span alone, and spans-only stays header-only.
        self.assertEqual(
            payload,
            list_span(CONSTRAINTS_LINES, "### Task 1:", ("### ", "## ")))
        self.assertNotIn(b"Standing constraints", proc.stdout)
        spans_only = self.run_cli("--plan", str(self.constraints_plan),
                                  "--task", "1", "--spans-only")
        self.assertEqual(spans_only.returncode, 0, spans_only.stderr)
        spans_only_text = spans_only.stdout.decode("utf-8")
        self.assertIn("constraints-span: %s" % expects, spans_only_text)
        self.assertNotIn(SPAN_BEGIN_MARKER, spans_only_text)
        self.assertNotIn("Standing constraints", spans_only_text)

    def test_constraints_span_absent_byte_compatible(self):
        proc = self.run_cli("--plan", str(self.plan), "--task", "1")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.last_err_line(proc), "OUTCOME: pass")
        stdout = proc.stdout.decode("utf-8")
        self.assertNotIn("constraints-span", stdout)
        header_lines = stdout[:stdout.index(SPAN_BEGIN_MARKER + "\n")]
        keys = [line.partition(": ")[0]
                for line in header_lines.splitlines()]
        # Byte-identical to the pre-plan grammar: exactly the four header
        # lines in the pre-plan order, nothing added anywhere.
        self.assertEqual(keys, ["plan", "task", "task-span", "terms-span"])
        spans_only = self.run_cli("--plan", str(self.plan), "--task", "1",
                                  "--spans-only")
        self.assertEqual(spans_only.returncode, 0, spans_only.stderr)
        keys = [line.partition(": ")[0]
                for line in spans_only.stdout.decode("utf-8").splitlines()]
        self.assertEqual(keys, ["plan", "task", "task-span", "terms-span"])

    def test_constraints_span_first_match_wins(self):
        insert_at = CONSTRAINTS_LINES.index("### Task 1: First task")
        duplicate = ["## Standing constraints",
                     "- a later duplicate section",
                     ""]
        two_sections = (CONSTRAINTS_LINES[:insert_at] + duplicate
                        + CONSTRAINTS_LINES[insert_at:])
        plan_bytes = list_bytes(two_sections)
        plan = self.plan.parent / "two-constraints-sections.md"
        plan.write_bytes(plan_bytes)
        given = list_span(two_sections, "## Standing constraints", ("## ",))
        proc = self.run_cli("--plan", str(plan), "--task", "1")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        fields, _ = self.parse_header(proc.stdout)
        start = plan_bytes.index(given)
        self.assertEqual(
            fields["constraints-span"],
            "start=%d end=%d sha256=%s"
            % (start, start + len(given),
               hashlib.sha256(given).hexdigest()))
        # The span covers the first section's bytes, not the duplicate's.
        self.assertEqual(
            given,
            b"## Standing constraints\n"
            b"- every task commits with a scoped pathspec\n\n")

    def test_constraints_span_runs_to_next_heading(self):
        given = list_span(CONSTRAINTS_LINES, "## Standing constraints",
                          ("## ",))
        proc = self.run_cli("--plan", str(self.constraints_plan),
                            "--task", "1")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        fields, _ = self.parse_header(proc.stdout)
        end = int(fields["constraints-span"].split(" ")[1].split("=")[1])
        self.assertEqual(end, list_offset(CONSTRAINTS_LINES,
                                          "## Gist & Examples"))
        # The span carries its heading and the blank line before the
        # terminator heading, and excludes the terminator's bytes.
        self.assertTrue(given.startswith(b"## Standing constraints\n"))
        self.assertTrue(given.endswith(b"scoped pathspec\n\n"))
        self.assertNotIn(b"Gist", given)

    def test_spans_only_prints_header_without_bytes(self):
        proc = self.run_cli("--plan", str(self.plan), "--task", "1",
                            "--spans-only")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.last_err_line(proc), "OUTCOME: pass")
        stdout = proc.stdout.decode("utf-8")
        self.assertNotIn(SPAN_BEGIN_MARKER, stdout)
        self.assertNotIn("### Task 1:", stdout)
        self.assertNotIn("Step one.", stdout)
        fields = {}
        for line in stdout.splitlines():
            key, _, value = line.partition(": ")
            fields[key] = value
        start = PLAN_BYTES.index(TASK_1)
        self.assertEqual(fields["task-span"],
                         "start=%d end=%d sha256=%s"
                         % (start, start + len(TASK_1),
                            hashlib.sha256(TASK_1).hexdigest()))

    def test_absent_task_is_tool_error(self):
        proc = self.run_cli("--plan", str(self.plan), "--task", "4")
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(self.last_err_line(proc), "OUTCOME: tool_error")
        self.assertIn("task 4 not found", proc.stderr.decode("utf-8"))

    def test_task_number_zero_is_tool_error(self):
        proc = self.run_cli("--plan", str(self.plan), "--task", "0")
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(self.last_err_line(proc), "OUTCOME: tool_error")
        self.assertIn("task numbers start at 1",
                      proc.stderr.decode("utf-8"))

    def test_missing_terms_is_tool_error(self):
        no_terms = Path(self._tmp.name) / "no-terms.md"
        no_terms.write_bytes(
            b"# Plan\n\n### Task 1: Only task\nbody\n")
        proc = self.run_cli("--plan", str(no_terms), "--task", "1")
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(self.last_err_line(proc), "OUTCOME: tool_error")
        self.assertIn("no `## Terms` section", proc.stderr.decode("utf-8"))

    def test_directory_operand_refuses_with_whole_file_pointer(self):
        """A directory operand refuses loud (exit 3 tool_error) with a
        pointer to whole-file charter-plus-task reads; no span bytes are
        extracted across files (the plan-directory-shape plan, Task 4)."""
        plan_dir = Path(self._tmp.name) / "2026-10-08-dir-plan"
        (plan_dir / "tasks").mkdir(parents=True)
        (plan_dir / "PLAN.md").write_bytes(
            b"# Plan\n\n## Terms\n- alpha: term\n\n### Task 1: Only task\nbody\n"
        )
        (plan_dir / "tasks" / "01-only.md").write_bytes(
            b"### Task 1: Only task\nbody\n"
        )
        proc = self.run_cli("--plan", str(plan_dir), "--task", "1")
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(self.last_err_line(proc), "OUTCOME: tool_error")
        err = proc.stderr.decode("utf-8")
        self.assertIn("plan-directory shape", err)
        self.assertIn("charter", err)
        # No span bytes: nothing is extracted across files.
        self.assertEqual(proc.stdout, b"")

    def test_unreadable_path_is_tool_error(self):
        absent = Path(self._tmp.name) / "absent.md"
        proc = self.run_cli("--plan", str(absent), "--task", "1")
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(self.last_err_line(proc), "OUTCOME: tool_error")
        self.assertIn(str(absent), proc.stderr.decode("utf-8"))

    def test_usage_error_exits_three_with_outcome(self):
        proc = self.run_cli("--plan", str(self.plan))
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(self.last_err_line(proc), "OUTCOME: tool_error")


if __name__ == "__main__":
    unittest.main()
