#!/usr/bin/env python3
"""Selftest for plan_delta_classifier.py.

Every dash, quote, ellipsis, and non-breaking-space fixture character is
built at run time from byte escapes; the em-dash and en-dash bytes never
appear literally in this file. CLI cases run against hermetic scratch git
repos under TemporaryDirectory (corrections_record's fixture builder); no
host state is touched.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import corrections_record as cr
import plan_delta_classifier as pdc

EM = b"\xe2\x80\x94"
EN = b"\xe2\x80\x93"
CURLY_DOUBLE_OPEN = b"\xe2\x80\x9c"
CURLY_DOUBLE_CLOSE = b"\xe2\x80\x9d"
CURLY_SINGLE_OPEN = b"\xe2\x80\x98"
CURLY_SINGLE_CLOSE = b"\xe2\x80\x99"
ELLIPSIS = b"\xe2\x80\xa6"
NBSP = b"\xc2\xa0"

CLASSIFIER = Path(__file__).resolve().parent / "plan_delta_classifier.py"
PLAN_REL = "docs/history/plans/acme-plan.md"


def assert_class(test, old, new, klass, *phrases):
    hunks = pdc.classify_lines(old, new)
    test.assertEqual(len(hunks), 1, hunks)
    hunk = hunks[0]
    test.assertEqual(hunk["class"], klass, hunk)
    if phrases:
        for phrase in phrases:
            test.assertIn(phrase, hunk["reason"])
    return hunk


class ClassifierTest(unittest.TestCase):
    def test_forward_checkbox_flip_is_exempt(self):
        assert_class(self, b"- [ ] x\n", b"- [x] x\n", pdc.CLASS_CHECKBOX)
        assert_class(self, b"1. [ ] x\n", b"1. [x] x\n", pdc.CLASS_CHECKBOX)

    def test_checkbox_near_misses_are_unclassified(self):
        assert_class(self, b"- [x] x\n", b"- [ ] x\n",
                     pdc.CLASS_UNCLASSIFIED, "forward")
        assert_class(self, b"- [X] x\n", b"- [x] x\n",
                     pdc.CLASS_UNCLASSIFIED, "forward")
        assert_class(self, b"- [ ] alpha\n", b"- [x] beta\n",
                     pdc.CLASS_UNCLASSIFIED, "byte-identical")

    def test_whitespace_is_exempt_and_near_miss_fails(self):
        # Re-indent within the same indent quantity class (one to three).
        assert_class(self, b"intro\n  alpha bravo\ntail\n",
                     b"intro\n   alpha bravo\ntail\n", pdc.CLASS_WHITESPACE)
        # Same class (four or more), prose-adjacent so never indented code.
        assert_class(self, b"intro\n    alpha bravo\ntail\n",
                     b"intro\n      alpha bravo\ntail\n",
                     pdc.CLASS_WHITESPACE)
        # Whitespace-run collapse.
        assert_class(self, b"alpha  bravo\n", b"alpha bravo\n",
                     pdc.CLASS_WHITESPACE)
        assert_class(self, b"para one\npara two\n",
                     b"para one\n\npara two\n", pdc.CLASS_WHITESPACE)
        assert_class(self, b"para one\n\npara two\n",
                     b"para one\npara two\n", pdc.CLASS_WHITESPACE)
        # Near-miss: the re-indent also changes one word.
        assert_class(self, b"  alpha bravo\n", b"   alpha delta\n",
                     pdc.CLASS_UNCLASSIFIED)

    def test_typography_members_are_exempt(self):
        assert_class(self, b"alpha %s omega\n" % EM, b"alpha, omega\n",
                     pdc.CLASS_TYPOGRAPHY)
        assert_class(self, b"alpha %s omega\n" % EN, b"alpha - omega\n",
                     pdc.CLASS_TYPOGRAPHY)
        assert_class(self, b"quote %salpha%s tail\n"
                     % (CURLY_DOUBLE_OPEN, CURLY_DOUBLE_CLOSE),
                     b'quote "alpha" tail\n', pdc.CLASS_TYPOGRAPHY)
        assert_class(self, b"quote %salpha%s tail\n"
                     % (CURLY_SINGLE_OPEN, CURLY_SINGLE_CLOSE),
                     b"quote 'alpha' tail\n", pdc.CLASS_TYPOGRAPHY)
        assert_class(self, b"wait %s tail\n" % ELLIPSIS, b"wait ... tail\n",
                     pdc.CLASS_TYPOGRAPHY)
        assert_class(self, b"alpha%sbeta\n" % NBSP, b"alpha beta\n",
                     pdc.CLASS_TYPOGRAPHY)

    def test_typography_exclusions_are_unclassified(self):
        # Numeric ranges: a dash adjacent to digits on both sides.
        assert_class(self, b"pages 3%s5\n" % EM, b"pages 3, 5\n",
                     pdc.CLASS_UNCLASSIFIED, "numeric range")
        assert_class(self, b"pages 3%s5\n" % EN, b"pages 3-5\n",
                     pdc.CLASS_UNCLASSIFIED, "numeric range")
        # Legacy em-dash shapes: hyphen, colon, semicolon.
        assert_class(self, b"alpha %s omega\n" % EM, b"alpha - omega\n",
                     pdc.CLASS_UNCLASSIFIED, "punctuation-equivalence")
        assert_class(self, b"alpha %s omega\n" % EM, b"alpha: omega\n",
                     pdc.CLASS_UNCLASSIFIED, "punctuation-equivalence")
        assert_class(self, b"alpha %s omega\n" % EM, b"alpha; omega\n",
                     pdc.CLASS_UNCLASSIFIED, "punctuation-equivalence")
        # A punctuation fix that also changes a word.
        assert_class(self, b"alpha %s omega\n" % EM, b"alpha, delta\n",
                     pdc.CLASS_UNCLASSIFIED, "punctuation-equivalence")
        # A heading-line dash substitution.
        assert_class(self, b"# Alpha %s Omega\n" % EM, b"# Alpha, Omega\n",
                     pdc.CLASS_UNCLASSIFIED, "heading")

    def test_whitespace_structure_near_misses_are_unclassified(self):
        # A list child's four-space indent collapsing to zero re-nests it.
        assert_class(self, b"- parent\n    child line\n",
                     b"- parent\nchild line\n",
                     pdc.CLASS_UNCLASSIFIED, "indent quantity class")
        # Blank-line removal adjacent to a four-space line flips its block
        # type (indented code becomes a lazy continuation).
        assert_class(self, b"para\n\n    code()\n", b"para\n    code()\n",
                     pdc.CLASS_UNCLASSIFIED, "block type")
        # A change to a line's trailing hard-break spacing.
        assert_class(self, b"alpha  \nbeta\n", b"alpha\nbeta\n",
                     pdc.CLASS_UNCLASSIFIED, "hard-break")
        # A blank-line change flipping a list between loose and tight form.
        assert_class(self, b"- a\n- b\n", b"- a\n\n- b\n",
                     pdc.CLASS_UNCLASSIFIED, "loose and tight")

    def test_blank_line_adjacent_to_setext_underline_is_unclassified(self):
        # Removing the blank between a paragraph and a setext "="
        # underline flips the paragraph to a heading in the resulting
        # text; the exempt verdict must not survive that flip.
        assert_class(self, b"Title\n\n=====\nbody\n", b"Title\n=====\nbody\n",
                     pdc.CLASS_UNCLASSIFIED, "excluded region")
        # Mirror polarity: adding the blank demotes the source heading to
        # plain paragraph text in the resulting text.
        assert_class(self, b"Title\n=====\nbody\n", b"Title\n\n=====\nbody\n",
                     pdc.CLASS_UNCLASSIFIED, "excluded region")
        # The ordinary blank-between-paragraphs shapes stay exempt.
        assert_class(self, b"para one\npara two\n",
                     b"para one\n\npara two\n", pdc.CLASS_WHITESPACE)
        assert_class(self, b"para one\n\npara two\n",
                     b"para one\npara two\n", pdc.CLASS_WHITESPACE)

    # ------------------------------------------------------------------
    # Gap-adjacency index-base fixtures (task contract recovery Task 1)
    # ------------------------------------------------------------------
    # Drift shape: an earlier pure change group shifts the new-side
    # offset relative to the old-side offset, so a later pure group's
    # gap-adjacency lookup must index its own side's lines and exclusion
    # set at its own side's gap offset. assert_class pins exactly one
    # hunk, so it is deliberately not applied to these two-hunk
    # fixtures; each fixture asserts its hunk count explicitly.

    DRIFT_INS_OLD = b"line one\nline two\nline three\ntail\n"
    DRIFT_INS_NEW = b"line one\nline two\n\nline three\ntail\n\n"
    DRIFT_DEL_OLD = b"alpha\nbravo\n\n\ncharlie\ndelta\n\n"
    DRIFT_DEL_NEW = b"alpha\nbravo\ncharlie\ndelta\n"
    DISTANCE_ZERO_INS_OLD = b"tail\n"
    DISTANCE_ZERO_INS_NEW = b"tail\n\n"
    DISTANCE_ZERO_DEL_OLD = b"tail\n\n"
    DISTANCE_ZERO_DEL_NEW = b"tail\n"
    MARKER_OLD = b"line one\nline two\nline three\n"
    MARKER_NEW = (b"line one\nline two\n\nline three\n"
                  b"marker alpha\nmarker bravo\n")
    ADJ_INS_OLD = b"alpha\nbravo\nTitle\n=====\nbody text\ntail text\n"
    ADJ_INS_NEW = (b"alpha\n\n\nbravo\nTitle\n\n=====\n"
                   b"body text\ntail text\n")
    ADJ_DEL_OLD = (b"alpha\n\n\nbravo\nTitle\n\n=====\n"
                   b"body text\ntail text\n")
    ADJ_DEL_NEW = b"alpha\nbravo\nTitle\n=====\nbody text\ntail text\n"

    def test_drifted_blank_insertion_after_earlier_insertion_classifies(self):
        # An earlier pure insertion drifts the offsets, so the appended
        # blank line's gap-adjacency lookup lands past the old lines'
        # end: pre-fix code raised IndexError here; post-fix the drifted
        # hunk classifies as a blank-line addition against its own side.
        hunks = pdc.classify_lines(self.DRIFT_INS_OLD, self.DRIFT_INS_NEW)
        self.assertEqual(len(hunks), 2, hunks)
        self.assertEqual(hunks[0]["class"], pdc.CLASS_WHITESPACE, hunks)
        self.assertEqual(hunks[0]["reason"], "blank line added")
        self.assertEqual(hunks[1]["class"], pdc.CLASS_WHITESPACE, hunks)
        self.assertEqual(hunks[1]["reason"], "blank line added")
        ok, message = pdc.exempt_verdict(hunks)
        self.assertTrue(ok, message)

    def test_drifted_blank_deletion_after_earlier_deletion_classifies(self):
        # Mirror: an earlier pure deletion drifts the offsets, so the
        # trailing blank line's gap-adjacency lookup lands past the new
        # lines' end: pre-fix code raised IndexError here; post-fix the
        # drifted hunk classifies as a blank-line removal.
        hunks = pdc.classify_lines(self.DRIFT_DEL_OLD, self.DRIFT_DEL_NEW)
        self.assertEqual(len(hunks), 2, hunks)
        self.assertEqual(hunks[0]["class"], pdc.CLASS_WHITESPACE, hunks)
        self.assertEqual(hunks[0]["reason"], "blank line removed")
        self.assertEqual(hunks[1]["class"], pdc.CLASS_WHITESPACE, hunks)
        self.assertEqual(hunks[1]["reason"], "blank line removed")
        ok, message = pdc.exempt_verdict(hunks)
        self.assertTrue(ok, message)

    def test_drifted_hunk_digest_is_offset_independent(self):
        # Hunk digests hash the change content only, so the drifted
        # hunk's digest equals the same edit's distance-zero digest no
        # matter where an earlier group moved the gap.
        drifted = pdc.classify_lines(self.DRIFT_INS_OLD, self.DRIFT_INS_NEW)
        distance_zero = pdc.classify_lines(self.DISTANCE_ZERO_INS_OLD,
                                           self.DISTANCE_ZERO_INS_NEW)
        self.assertEqual(len(distance_zero), 1, distance_zero)
        self.assertEqual(drifted[1]["digest"], distance_zero[0]["digest"])
        drifted = pdc.classify_lines(self.DRIFT_DEL_OLD, self.DRIFT_DEL_NEW)
        distance_zero = pdc.classify_lines(self.DISTANCE_ZERO_DEL_OLD,
                                           self.DISTANCE_ZERO_DEL_NEW)
        self.assertEqual(len(distance_zero), 1, distance_zero)
        self.assertEqual(drifted[1]["digest"], distance_zero[0]["digest"])

    def test_appended_non_blank_marker_lines_keep_named_refusal(self):
        # The non-blank early return precedes the gap-adjacency arm, so
        # appended marker lines take the named unclassified refusal with
        # the exact pre-fix string, byte-identical across the fix.
        hunks = pdc.classify_lines(self.MARKER_OLD, self.MARKER_NEW)
        self.assertEqual(len(hunks), 2, hunks)
        self.assertEqual(hunks[1]["class"], pdc.CLASS_UNCLASSIFIED, hunks)
        self.assertEqual(hunks[1]["reason"],
                         "a non-blank line was added; no exempt class "
                         "adds content")

    def test_drifted_insertion_adjacent_to_old_side_setext_refuses(self):
        # Excluded-status divergence: the old text's setext underline is
        # an excluded region and the new text's demoted copy is not. The
        # earlier two-blank insertion drifts the lookup two lines past
        # the gap, landing in range but off the excluded line pre-fix
        # (a whitespace pass, red here); post-fix the own-side lookup
        # reads the old-side exclusion at the corrected old-side line
        # numbers.
        hunks = pdc.classify_lines(self.ADJ_INS_OLD, self.ADJ_INS_NEW)
        self.assertEqual(len(hunks), 2, hunks)
        self.assertEqual(hunks[0]["class"], pdc.CLASS_WHITESPACE, hunks)
        self.assertEqual(hunks[1]["class"], pdc.CLASS_UNCLASSIFIED, hunks)
        self.assertEqual(
            hunks[1]["reason"],
            "a blank-line change adjacent to an excluded region of the "
            "source or resulting text is never exempt")

    def test_drifted_deletion_adjacent_to_new_side_setext_refuses(self):
        # Deletion mirror: deleting the blank promotes the new text's
        # setext underline into existence, so the exclusion lives on the
        # new side only. The earlier two-blank deletion drifts the
        # pre-fix lookup in range but off the excluded line (a
        # whitespace pass, red here); post-fix the own-side lookup reads
        # the new-side exclusion at the corrected new-side line numbers.
        hunks = pdc.classify_lines(self.ADJ_DEL_OLD, self.ADJ_DEL_NEW)
        self.assertEqual(len(hunks), 2, hunks)
        self.assertEqual(hunks[0]["class"], pdc.CLASS_WHITESPACE, hunks)
        self.assertEqual(hunks[1]["class"], pdc.CLASS_UNCLASSIFIED, hunks)
        self.assertEqual(
            hunks[1]["reason"],
            "a blank-line change adjacent to an excluded region of the "
            "source or resulting text is never exempt")

    def test_eof_newline_delta_is_never_exempt(self):
        # A checkbox flip riding a trailing-newline removal hides the
        # newline fact from the line model; the whole-delta grade must
        # refuse it as unclassified.
        hunks, ok, message = pdc.classify_delta(b"head\n- [ ] x\n",
                                                b"head\n- [x] x")
        self.assertEqual(len(hunks), 1, hunks)
        self.assertFalse(ok, message)
        self.assertTrue(message.startswith(cr.MARKER_PREFIX), message)
        self.assertIn("unclassified", message)
        # The flip with the trailing newline intact stays exempt.
        hunks, ok, message = pdc.classify_delta(b"head\n- [ ] x\n",
                                                b"head\n- [x] x\n")
        self.assertTrue(ok, message)
        self.assertEqual(hunks[0]["class"], pdc.CLASS_CHECKBOX, hunks)
        # The pure newline-only delta keeps the bytes-changed-no-hunks
        # refusal (the line evidence surface shows no hunks at all).
        self.assertEqual(pdc.classify_lines(b"tail text\n", b"tail text"),
                         [])
        hunks, ok, message = pdc.classify_delta(b"tail text\n", b"tail text")
        self.assertEqual(hunks, [])
        self.assertFalse(ok)
        self.assertIn("bytes changed", message)
        self.assertIn("no hunks", message)

    def test_link_destination_edit_is_unclassified(self):
        assert_class(self, b"[docs](http://x/a  b) tail\n",
                     b"[docs](http://x/a b) tail\n",
                     pdc.CLASS_UNCLASSIFIED, "excluded region")
        # An autolink target admits no spaces, so the autolink witness is
        # an em-dash change inside it (the character built at run time).
        assert_class(self, b"see <http://x/a%sb> end\n" % EM,
                     b"see <http://x/a, b> end\n",
                     pdc.CLASS_UNCLASSIFIED, "excluded region")

    def test_excluded_region_hunks_are_unclassified(self):
        assert_class(self, b"```python\nx = 1  + 2\n```\n",
                     b"```python\nx = 1 + 2\n```\n",
                     pdc.CLASS_UNCLASSIFIED, "excluded region")
        assert_class(self, b"~~~bash\ncd ~  here\n~~~\n",
                     b"~~~bash\ncd ~ here\n~~~\n",
                     pdc.CLASS_UNCLASSIFIED, "excluded region")
        assert_class(self, b"value `a  b` tail\n", b"value `a b` tail\n",
                     pdc.CLASS_UNCLASSIFIED, "excluded region")
        assert_class(self, b"- item\n\n      deep =  1\nprose\n",
                     b"- item\n\n      deep = 1\nprose\n",
                     pdc.CLASS_UNCLASSIFIED, "excluded region")
        assert_class(self, b"Title\n=====  \nbody\n",
                     b"Title\n=====\nbody\n",
                     pdc.CLASS_UNCLASSIFIED, "excluded region")
        assert_class(self, b"intro\n\n***  \nprose\n",
                     b"intro\n\n***\nprose\n",
                     pdc.CLASS_UNCLASSIFIED, "excluded region")
        assert_class(self, b"h1 | h2\n--- | ---  \nprose\n",
                     b"h1 | h2\n--- | ---\nprose\n",
                     pdc.CLASS_UNCLASSIFIED, "excluded region")
        # An unclosed fence extends to end of file.
        assert_class(self, b"text\n\n```text\nbody  x\nmore\n",
                     b"text\n\n```text\nbody x\nmore\n",
                     pdc.CLASS_UNCLASSIFIED, "excluded region")

    def test_crlf_excluded_regions_ride_line_numbers(self):
        # Whole-line excluded regions are recognized through
        # corrections_record's excluded_line_numbers, whose line numbers
        # agree with the classifier's own split("\n") line model under
        # CRLF, so a whitespace-only change inside a CRLF fence is
        # unclassified and a CRLF prose typography fix still classifies
        # typography.
        assert_class(self,
                     b"a\r\n" * 5 + b"```python\r\nx = 1  + 2\r\n```\r\n",
                     b"a\r\n" * 5 + b"```python\r\nx = 1 + 2\r\n```\r\n",
                     pdc.CLASS_UNCLASSIFIED, "excluded region")
        assert_class(self,
                     b"a\r\n" * 5 + b"alpha %s omega\r\n" % EM,
                     b"a\r\n" * 5 + b"alpha, omega\r\n",
                     pdc.CLASS_TYPOGRAPHY)

    def test_crlf_inline_span_drift_is_closed(self):
        # The char-span overlap check must not map corrections_record's
        # whole-text spans onto this classifier's coordinates: after N
        # CRLF lines those spans sit N chars left of their true
        # position, so a change inside a CRLF inline code span escapes
        # the guard (false pass) and a change just before the span is
        # swallowed by the drifted span (false block). The check now
        # uses per-line spans computed on the same lines it diffs.
        assert_class(self,
                     b"a\r\n" * 5 + b"see `a  b` end\r\n",
                     b"a\r\n" * 5 + b"see `a b` end\r\n",
                     pdc.CLASS_UNCLASSIFIED, "excluded region")
        assert_class(self,
                     b"a\r\n" * 5 + b"see  `a b` end\r\n",
                     b"a\r\n" * 5 + b"see `a b` end\r\n",
                     pdc.CLASS_WHITESPACE)

    def test_case_change_is_unclassified(self):
        assert_class(self, b"alpha Bravo\n", b"alpha bravo\n",
                     pdc.CLASS_UNCLASSIFIED, "case is never normalized")

    def test_exempt_verdict_whole_delta(self):
        fill_a = b"".join(b"f%d\n" % i for i in range(3, 11))
        fill_b = b"".join(b"g%d\n" % i for i in range(12, 20))
        old = b"- [ ] alpha\n\n" + fill_a + b"wait %s tail\n" % ELLIPSIS \
            + fill_b
        new = b"- [x] alpha\n\n" + fill_a + b"wait ... tail\n" + fill_b
        hunks = pdc.classify_lines(old, new)
        self.assertEqual([h["class"] for h in hunks],
                         [pdc.CLASS_CHECKBOX, pdc.CLASS_TYPOGRAPHY], hunks)
        ok, message = pdc.exempt_verdict(hunks)
        self.assertTrue(ok, message)
        self.assertTrue(message.startswith(cr.MARKER_PREFIX), message)
        # Adding one unclassified hunk flips the verdict to False.
        old_bad = old + b"Alpha tail\n"
        new_bad = new + b"alpha tail\n"
        hunks_bad = pdc.classify_lines(old_bad, new_bad)
        self.assertEqual(len(hunks_bad), 3, hunks_bad)
        ok, message = pdc.exempt_verdict(hunks_bad)
        self.assertFalse(ok)
        self.assertTrue(message.startswith(cr.MARKER_PREFIX), message)

    def test_zero_hunk_delta_with_byte_change_is_unclassified(self):
        self.assertEqual(pdc.classify_lines(b"tail text\n", b"tail text"),
                         [])
        hunks, ok, message = pdc.classify_delta(b"tail text\n",
                                                b"tail text")
        self.assertEqual(hunks, [])
        self.assertFalse(ok)
        self.assertTrue(message.startswith(cr.MARKER_PREFIX), message)
        self.assertIn("bytes changed", message)
        self.assertIn("no hunks", message)
        ok, message = pdc.exempt_verdict([])
        self.assertFalse(ok)

    # ------------------------------------------------------------------
    # CLI surface
    # ------------------------------------------------------------------

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(CLASSIFIER)] + list(args),
            capture_output=True, text=True, env=cr.hermetic_git_env())

    def last_outcome(self, proc):
        return proc.stdout.splitlines()[-1]

    def test_emit_row_and_exit_stimuli(self):
        old = b"# plan\n\nalpha %s bravo.\n" % EM
        fixed = b"# plan\n\nalpha, bravo.\n"
        repo = cr.build_scratch_repo(self)
        start = repo.commit_file(PLAN_REL, old, "seed plan")
        repo.write_file(PLAN_REL, fixed)
        # Exit 0 pass with an --emit-row row that validates.
        proc = self.run_cli("--plan", str(repo.root / PLAN_REL),
                            "--since", "HEAD", "--emit-row")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self.last_outcome(proc), "OUTCOME: pass")
        rows = [line for line in proc.stdout.splitlines()
                if line.startswith("corrections-row-json: ")]
        self.assertEqual(len(rows), 1, proc.stdout)
        row = json.loads(rows[0].split(": ", 1)[1])
        self.assertIsNone(cr.row_schema_reason(row, cr.FAMILY_PLAN))
        self.assertEqual(row["kind"], cr.KIND_SCRIPT_VERIFIED)
        self.assertEqual(row["evidence_commit"], start)
        self.assertEqual(row["before_digest"], cr.sha256_hex(old))
        self.assertEqual(row["after_digest"], cr.sha256_hex(fixed))
        self.assertEqual([set(h) for h in row["hunks"]],
                         [{"header", "digest"}] * len(row["hunks"]))
        # Exit 1 fail: an unclassified hunk.
        repo.write_file(PLAN_REL, b"# plan\n\nalpha charlie.\n")
        proc = self.run_cli("--plan", str(repo.root / PLAN_REL),
                            "--since", "HEAD")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertEqual(self.last_outcome(proc), "OUTCOME: fail")
        # The acked kind emits through the same schema builder and still
        # reports the unclassified delta as a fail.
        receipt_dir = tempfile.TemporaryDirectory(prefix="pdc-receipt-")
        self.addCleanup(receipt_dir.cleanup)
        receipt_path = Path(receipt_dir.name) / "receipt.json"
        receipt_path.write_text(json.dumps({
            "directive": "re-bind the unclassified delta",
            "authorization_witness": "state/turns/0001.record",
            "classifier_gap_row":
                "docs/history/backlog/2026-10-04-typography-bucket.md",
        }))
        proc = self.run_cli("--plan", str(repo.root / PLAN_REL),
                            "--since", "HEAD", "--emit-row",
                            "--kind", "operator-acked",
                            "--receipt", str(receipt_path))
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertEqual(self.last_outcome(proc), "OUTCOME: fail")
        rows = [line for line in proc.stdout.splitlines()
                if line.startswith("corrections-row-json: ")]
        self.assertEqual(len(rows), 1, proc.stdout)
        row = json.loads(rows[0].split(": ", 1)[1])
        self.assertIsNone(cr.row_schema_reason(row, cr.FAMILY_PLAN))
        self.assertEqual(row["kind"], cr.KIND_OPERATOR_ACKED)
        self.assertEqual(sorted(row["receipt"]),
                         ["authorization_witness", "classifier_gap_row",
                          "directive"])
        # Exit 3: an unreadable plan operand.
        proc = self.run_cli("--plan", str(repo.root / "absent.md"),
                            "--since", "HEAD")
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(self.last_outcome(proc), "OUTCOME: tool_error")
        # Exit 3: an unresolvable --since ref.
        proc = self.run_cli("--plan", str(repo.root / PLAN_REL),
                            "--since", "does-not-exist")
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(self.last_outcome(proc), "OUTCOME: tool_error")
        # Exit 2: git plumbing failure over resolved inputs. The ref
        # resolves but the plan path at it is a gitlink, so the blob read
        # fails after resolution.
        repo2 = cr.build_scratch_repo(self, name="gitlink-repo")
        repo2.write_file("README.md", b"seed\n")
        repo2.commit_all("seed readme")
        fake_blob = "abcdef0123456789abcdef0123456789abcdef01"
        repo2.git("update-index", "--add", "--cacheinfo",
                  "160000,%s,%s" % (fake_blob, PLAN_REL))
        repo2.git("commit", "-q", "-m", "gitlink plan path",
                  date=repo2.next_date())
        repo2.write_file(PLAN_REL, b"# plan\n\nworking tree bytes.\n")
        proc = self.run_cli("--plan", str(repo2.root / PLAN_REL),
                            "--since", "HEAD")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertEqual(self.last_outcome(proc), "OUTCOME: indeterminate")

    def test_since_surface_covers_working_tree(self):
        d1 = b"# t\n\n- [ ] item\n\none %s two\n" % EM
        d2 = b"# t\n\n- [ ] item\n\none, two\n"
        d3 = b"# t\n\n- [x] item\n\none, two\n"
        repo = cr.build_scratch_repo(self)
        start = repo.commit_file(PLAN_REL, d1, "seed plan")
        # The only delta is uncommitted, and its hunks classify: uncommitted
        # edits are never vacuously exempt.
        repo.write_file(PLAN_REL, d2)
        proc = self.run_cli("--plan", str(repo.root / PLAN_REL),
                            "--since", start)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self.last_outcome(proc), "OUTCOME: pass")
        self.assertIn(pdc.CLASS_TYPOGRAPHY, proc.stdout)
        self.assertNotIn("no delta", proc.stdout)
        # Committed history and the working tree classify together against
        # the start commit's blob in one surface.
        repo.commit_all("typography hop")
        repo.write_file(PLAN_REL, d3)
        proc = self.run_cli("--plan", str(repo.root / PLAN_REL),
                            "--since", start)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self.last_outcome(proc), "OUTCOME: pass")
        self.assertIn(pdc.CLASS_CHECKBOX, proc.stdout)
        self.assertIn(pdc.CLASS_TYPOGRAPHY, proc.stdout)


    def test_non_utf8_since_blob_is_tool_error(self):
        # A committed blob that is not decodable UTF-8 is an unreadable
        # operand: exit 3 with the final OUTCOME line, never a crash and
        # never a raw traceback without an outcome.
        seed = b"# plan\n\nalpha \x97 bravo.\n"
        repo = cr.build_scratch_repo(self)
        start = repo.commit_file(PLAN_REL, seed, "seed latin-1 plan")
        repo.write_file(PLAN_REL, b"# plan\n\nalpha, bravo.\n")
        proc = self.run_cli("--plan", str(repo.root / PLAN_REL),
                            "--since", start)
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(self.last_outcome(proc), "OUTCOME: tool_error")
        self.assertIn("not decodable UTF-8", proc.stderr)


class DirectoryPlanClassifierTest(unittest.TestCase):
    """Directory-plan operands at the CLI layer (plan-directory-shape
    Task 2): the `--plan` operand resolves through the shared shape helper
    and loops per file, decorating each hunk header with the file's
    relative path; the checkbox-flip proof applies per task file; a
    manifest-level add or remove of a task file is a structural delta,
    never exempt; the corrections chain records one row per changed
    file."""

    PLAN_DIR = "docs/history/plans/2026-10-08-dir-demo"

    CHARTER = (
        b"# Plan: dir demo\n"
        b"\n"
        b"## Validation Commands\n"
        b"\n"
        b"- none\n"
    )
    TASK_ONE = (
        b"### Task 1: alpha\n"
        b"\n"
        b"Files:\n"
        b"\n"
        b"- f\n"
        b"\n"
        b"Evidence:\n"
        b"\n"
        b"- [ ] box one\n"
    )
    TASK_TWO = (
        b"### Task 2: beta\n"
        b"\n"
        b"Files:\n"
        b"\n"
        b"- g\n"
        b"\n"
        b"Evidence:\n"
        b"\n"
        b"- [ ] box two\n"
    )

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(CLASSIFIER)] + list(args),
            capture_output=True, text=True, env=cr.hermetic_git_env())

    def last_outcome(self, proc):
        return proc.stdout.splitlines()[-1]

    def _seed_repo(self, name, task_blobs):
        """A scratch repo committing the directory plan: charter plus the
        given {relpath: bytes} task files."""
        repo = cr.build_scratch_repo(self, name=name)
        repo.write_file(self.PLAN_DIR + "/PLAN.md", self.CHARTER)
        for rel, blob in task_blobs.items():
            repo.write_file(self.PLAN_DIR + "/" + rel, blob)
        repo.commit_all("seed directory plan")
        return repo

    def test_classifier_per_file_headers(self):
        # A checkbox-flip-only delta on ONE task file returns the exempt
        # verdict with the task file named in the hunk header; the other
        # task file's bytes never appear as hunks.
        repo = self._seed_repo("dir-flip", {"tasks/01-alpha.md": self.TASK_ONE,
                                            "tasks/02-beta.md": self.TASK_TWO})
        flipped = self.TASK_ONE.replace(b"- [ ] box one\n", b"- [x] box one\n")
        repo.write_file(self.PLAN_DIR + "/tasks/01-alpha.md", flipped)
        proc = self.run_cli("--plan", str(repo.root / self.PLAN_DIR),
                            "--since", "HEAD")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self.last_outcome(proc), "OUTCOME: pass")
        hunk_lines = [line for line in proc.stdout.splitlines()
                      if line.startswith("hunk ")]
        self.assertEqual(len(hunk_lines), 1, proc.stdout)
        self.assertIn(pdc.CLASS_CHECKBOX, hunk_lines[0])
        self.assertTrue(hunk_lines[0].startswith(
            "hunk 1: tasks/01-alpha.md: @@"), hunk_lines[0])
        self.assertNotIn("tasks/02-beta.md:", proc.stdout)
        self.assertIn("file: PLAN.md", proc.stdout)
        self.assertIn("file: tasks/01-alpha.md", proc.stdout)
        self.assertIn("file: tasks/02-beta.md", proc.stdout)
        # The corrections chain records one row per changed file: exactly
        # the flipped task file here, its row hunks carrying the decorated
        # header.
        proc = self.run_cli("--plan", str(repo.root / self.PLAN_DIR),
                            "--since", "HEAD", "--emit-row")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        rows = [line for line in proc.stdout.splitlines()
                if line.startswith("corrections-row-json: ")]
        self.assertEqual(len(rows), 1, proc.stdout)
        row = json.loads(rows[0].split(": ", 1)[1])
        self.assertIsNone(cr.row_schema_reason(row, cr.FAMILY_PLAN))
        self.assertEqual(row["before_digest"], cr.sha256_hex(self.TASK_ONE))
        self.assertEqual(row["after_digest"], cr.sha256_hex(flipped))
        self.assertTrue(row["hunks"][0]["header"].startswith(
            "tasks/01-alpha.md: @@"), row["hunks"][0])
        # A flip on the second task file names THAT file's header instead.
        repo.write_file(self.PLAN_DIR + "/tasks/01-alpha.md", self.TASK_ONE)
        repo.write_file(self.PLAN_DIR + "/tasks/02-beta.md",
                        self.TASK_TWO.replace(b"- [ ] box two\n",
                                              b"- [x] box two\n"))
        proc = self.run_cli("--plan", str(repo.root / self.PLAN_DIR),
                            "--since", "HEAD")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        hunk_lines = [line for line in proc.stdout.splitlines()
                      if line.startswith("hunk ")]
        self.assertEqual(len(hunk_lines), 1, proc.stdout)
        self.assertTrue(hunk_lines[0].startswith(
            "hunk 1: tasks/02-beta.md: @@"), hunk_lines[0])

    def test_classifier_two_file_flip_emits_two_rows(self):
        # One run flipping BOTH task files against --since emits exactly two
        # corrections rows, one per changed file: each row validates against
        # the plan schema, carries its own before/after digests, and names
        # its own file in the decorated hunk header (the per-file row loop,
        # pinned with both legs flipped at once).
        repo = self._seed_repo("dir-flip-two",
                               {"tasks/01-alpha.md": self.TASK_ONE,
                                "tasks/02-beta.md": self.TASK_TWO})
        flipped_one = self.TASK_ONE.replace(b"- [ ] box one\n", b"- [x] box one\n")
        flipped_two = self.TASK_TWO.replace(b"- [ ] box two\n", b"- [x] box two\n")
        repo.write_file(self.PLAN_DIR + "/tasks/01-alpha.md", flipped_one)
        repo.write_file(self.PLAN_DIR + "/tasks/02-beta.md", flipped_two)
        proc = self.run_cli("--plan", str(repo.root / self.PLAN_DIR),
                            "--since", "HEAD", "--emit-row")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self.last_outcome(proc), "OUTCOME: pass")
        rows = [line for line in proc.stdout.splitlines()
                if line.startswith("corrections-row-json: ")]
        self.assertEqual(len(rows), 2, proc.stdout)
        expected = {
            "tasks/01-alpha.md": (self.TASK_ONE, flipped_one),
            "tasks/02-beta.md": (self.TASK_TWO, flipped_two),
        }
        seen = set()
        for row_line in rows:
            row = json.loads(row_line.split(": ", 1)[1])
            self.assertIsNone(cr.row_schema_reason(row, cr.FAMILY_PLAN))
            self.assertEqual(len(row["hunks"]), 1, row)
            rel = row["hunks"][0]["header"].split(":")[0]
            self.assertIn(rel, expected, row)
            old, new = expected[rel]
            self.assertEqual(row["before_digest"], cr.sha256_hex(old))
            self.assertEqual(row["after_digest"], cr.sha256_hex(new))
            seen.add(rel)
        self.assertEqual(seen, set(expected))

    def test_classifier_structural_add_and_remove(self):
        # Removing a task file is structural (the manifest's file set
        # shrank); the refusal names the removed file and is never exempt.
        repo = self._seed_repo("dir-remove",
                               {"tasks/01-alpha.md": self.TASK_ONE,
                                "tasks/02-beta.md": self.TASK_TWO})
        (repo.root / self.PLAN_DIR / "tasks" / "02-beta.md").unlink()
        proc = self.run_cli("--plan", str(repo.root / self.PLAN_DIR),
                            "--since", "HEAD")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(self.last_outcome(proc), "OUTCOME: fail")
        self.assertIn("structural", proc.stdout)
        self.assertIn("tasks/02-beta.md", proc.stdout)
        # Adding a task file is structural the same way.
        repo2 = self._seed_repo("dir-add", {"tasks/01-alpha.md": self.TASK_ONE})
        repo2.write_file(self.PLAN_DIR + "/tasks/02-beta.md", self.TASK_TWO)
        proc = self.run_cli("--plan", str(repo2.root / self.PLAN_DIR),
                            "--since", "HEAD")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(self.last_outcome(proc), "OUTCOME: fail")
        self.assertIn("structural", proc.stdout)
        self.assertIn("tasks/02-beta.md", proc.stdout)

    def test_classifier_directory_refusals_are_tool_errors(self):
        # A charterless directory is a named tool error, never a traceback.
        repo = cr.build_scratch_repo(self, name="dir-charterless")
        charterless = repo.root / "docs" / "history" / "plans" / "not-a-plan"
        charterless.mkdir(parents=True)
        proc = self.run_cli("--plan", str(charterless), "--since", "HEAD")
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(self.last_outcome(proc), "OUTCOME: tool_error")
        self.assertIn("not-a-plan", proc.stderr)


if __name__ == "__main__":
    unittest.main()
