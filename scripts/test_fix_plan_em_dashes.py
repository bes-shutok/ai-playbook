#!/usr/bin/env python3
"""Selftest for fix_plan_em_dashes.py.

Every em-dash fixture character is built at run time from byte escapes;
the em-dash and en-dash bytes never appear literally in this file. CLI
cases run against TemporaryDirectory operands; no host state is touched
and no absolute personal path is embedded.

Setext underlines, thematic breaks, and table delimiter rows cannot
carry an em dash and still scan as those regions (their defining
character sets exclude U+2014), so their arms assert byte-preservation
of the region lines beside prose substitutions in the same construct;
the backtick fence, tilde fence, inline code span, indented code block,
and link destination arms place the character inside the region itself.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fix_plan_em_dashes  # noqa: F401  the module must exist to import

FIXER = Path(__file__).resolve().parent / "fix_plan_em_dashes.py"

EM = b"\xe2\x80\x94"


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(FIXER)] + list(args),
        capture_output=True, text=True)


class FixerTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="fix-plan-em-dashes-")
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)

    def write(self, name, content):
        path = self.tmp / name
        path.write_bytes(content)
        return path

    def test_substitutes_comma_outside_excluded_regions(self):
        doc = (
            b"alpha %s omega\n"                             # prose
            b"alpha  %s  omega\n"                           # spaces fold
            b"```bash\n"
            b"code %s here\n"                               # backtick fence
            b"```\n"
            b"~~~\n"
            b"code %s here\n"                               # tilde fence
            b"~~~\n"
            b"run `x %s y` now\n"                           # inline span
            b"\n"
            b"    code %s here\n"                           # indented code
            b"title %s line\n"                              # setext title
            b"------\n"                                     # setext underline
            b"\n"
            b"***\n"                                        # thematic break
            b"| A | B |\n"
            b"| --- | --- |\n"                              # delimiter row
            b"| a %s b |\n"                                 # content cell
            b"see [docs](http://example.com/a%sb) now\n"    # link dest
            b"pages 3%s7 cited\n"                           # numeric range
            b"range 3 %s 5 stays\n"                         # numeric range
            b"tier 3 %s gold\n"                             # one digit only
        ) % ((EM,) * 12)
        expected = (
            b"alpha, omega\n"
            b"alpha, omega\n"
            b"```bash\n"
            b"code %s here\n"
            b"```\n"
            b"~~~\n"
            b"code %s here\n"
            b"~~~\n"
            b"run `x %s y` now\n"
            b"\n"
            b"    code %s here\n"
            b"title, line\n"
            b"------\n"
            b"\n"
            b"***\n"
            b"| A | B |\n"
            b"| --- | --- |\n"
            b"| a, b |\n"
            b"see [docs](http://example.com/a%sb) now\n"
            b"pages 3%s7 cited\n"
            b"range 3 %s 5 stays\n"
            b"tier 3, gold\n"
        ) % ((EM,) * 7)
        path = self.write("plan.md", doc)
        proc = run_cli(str(path))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(path.read_bytes(), expected)
        self.assertEqual(proc.stdout.splitlines()[-1], "OUTCOME: pass")

    def test_idempotent_and_counts(self):
        doc = (
            b"one %s two\n"            # line 1: 1 substitution
            b"```\n"
            b"code %s here\n"          # excluded region
            b"```\n"
            b"three  %s  four\n"       # line 5: 1 substitution
            b"five %s six %s seven\n"  # line 6: 2 substitutions
        ) % ((EM,) * 5)
        expected = (
            b"one, two\n"
            b"```\n"
            b"code %s here\n"
            b"```\n"
            b"three, four\n"
            b"five, six, seven\n"
        ) % (EM,)
        path = self.write("plan.md", doc)
        first = run_cli(str(path))
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(path.read_bytes(), expected)
        # Count gates: the exact per-line and total numbers, not presence.
        for counted in ("line 1: 1 substitution",
                        "line 5: 1 substitution",
                        "line 6: 2 substitutions",
                        "total: 4 substitutions"):
            self.assertIn(counted, first.stdout)
        second = run_cli(str(path))
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(path.read_bytes(), expected)
        self.assertIn("total: 0 substitutions", second.stdout)
        for out_line in second.stdout.splitlines():
            self.assertFalse(out_line.startswith("line "), out_line)

    def test_unbalanced_fence_refuses(self):
        inside = b"prose line\n```\ncode %s more\ntail\n" % EM
        path = self.write("inside.md", inside)
        proc = run_cli(str(path))
        self.assertEqual(proc.returncode, 3)
        self.assertIn("unbalanced fence", proc.stderr)
        self.assertEqual(proc.stdout.splitlines()[-1], "OUTCOME: tool_error")
        self.assertEqual(path.read_bytes(), inside)
        # A dash before the fence refuses too: no byte is rewritten, so a
        # scanner disagreement never becomes a silent substitution.
        before = b"alpha %s omega\n```\nbody\n" % EM
        path = self.write("before.md", before)
        proc = run_cli(str(path))
        self.assertEqual(proc.returncode, 3)
        self.assertIn("unbalanced fence", proc.stderr)
        self.assertEqual(path.read_bytes(), before)

    def test_crlf_fence_body_is_byte_identical(self):
        # The drift repro: corrections_record's whole-text char spans sit
        # N chars left of their true position after N CRLF lines when
        # mapped onto this fixer's own coordinates, so a match near a
        # span's end escaped the overlap guard and the fence body was
        # rewritten. The exclusion decision now rides drift-free
        # outputs, so the bytes stay identical.
        doc = b"l\r\n" * 5 + b"```\r\ncode <" + EM + b">\r\n```\r\n"
        path = self.write("crlf-fence.md", doc)
        proc = run_cli(str(path))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(path.read_bytes(), doc)
        self.assertIn("total: 0 substitutions", proc.stdout)
        self.assertEqual(proc.stdout.splitlines()[-1], "OUTCOME: pass")

    def test_crlf_prose_substitutes_and_is_idempotent(self):
        # A legitimate prose em dash in a CRLF file still substitutes,
        # the CRLF line endings survive byte-for-byte, and a second run
        # is a zero-substitution no-op.
        doc = (
            b"one %s two\r\n"            # line 1: prose, 1 substitution
            b"```\r\n"
            b"code %s here\r\n"          # line 3: excluded region
            b"```\r\n"
            b"three  %s  four\r\n"       # line 5: spaces fold, 1
        ) % ((EM,) * 3)
        expected = (
            b"one, two\r\n"
            b"```\r\n"
            b"code %s here\r\n"
            b"```\r\n"
            b"three, four\r\n"
        ) % EM
        path = self.write("crlf-prose.md", doc)
        first = run_cli(str(path))
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(path.read_bytes(), expected)
        for counted in ("line 1: 1 substitution",
                        "line 5: 1 substitution",
                        "total: 2 substitutions"):
            self.assertIn(counted, first.stdout)
        second = run_cli(str(path))
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(path.read_bytes(), expected)
        self.assertIn("total: 0 substitutions", second.stdout)

    def test_crlf_unbalanced_fence_refuses(self):
        # The modeled refusal keeps working when the fence lines end
        # CRLF: no byte is rewritten, exit 3, OUTCOME: tool_error.
        doc = b"prose line\r\n```\r\ncode %s more\r\ntail\r\n" % EM
        path = self.write("crlf-open.md", doc)
        proc = run_cli(str(path))
        self.assertEqual(proc.returncode, 3)
        self.assertIn("unbalanced fence", proc.stderr)
        self.assertEqual(proc.stdout.splitlines()[-1], "OUTCOME: tool_error")
        self.assertEqual(path.read_bytes(), doc)

    def test_tool_error(self):
        missing = self.tmp / "absent.md"
        proc = run_cli(str(missing))
        self.assertEqual(proc.returncode, 3)
        self.assertEqual(proc.stdout.splitlines()[-1], "OUTCOME: tool_error")
        self.assertIn("absent.md", proc.stderr)
        # A file whose only em dash sits inside a link destination is left
        # byte-identical with a zero-substitution count.
        original = b"see [docs](http://example.com/a%sb) now\n" % EM
        path = self.write("link-only.md", original)
        proc = run_cli(str(path))
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(path.read_bytes(), original)
        self.assertIn("total: 0 substitutions", proc.stdout)
        self.assertEqual(proc.stdout.splitlines()[-1], "OUTCOME: pass")


if __name__ == "__main__":
    unittest.main()
