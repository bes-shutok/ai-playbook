#!/usr/bin/env python3
"""Selftest for code_delta_classifier.py.

Fixtures are hermetic: literal byte fixtures drive the per-language
comment-only proofs, and the CLI plus the certified-range round trip run
against scratch git repos built by corrections_record's fixture builder
(hermetic env, pinned dates, TemporaryDirectory teardown). No host state
is touched and no absolute personal path is embedded.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import corrections_record as cr
import code_delta_classifier as cdc

CLASSIFIER = Path(__file__).resolve().parent / "code_delta_classifier.py"
SRC = "src/app.py"
BASH_SRC = "run.sh"
SLUG = "acme-src"

# The certified branch: a base commit and two content commits, then the
# committed comment-only fix, then a further code change.
V0 = b"def f():\n    return 1\n"
V1 = b"def f():\n    return 2\n"
V2 = b"def g():\n    return 3\n"
V3 = b"def g():\n    # reviewed\n    return 3\n"
V4 = b"def g():\n    # reviewed\n    return 4\n"


def assert_message(test, message, *phrases):
    test.assertIsInstance(message, str)
    test.assertTrue(message.startswith(cr.MARKER_PREFIX), message)
    for banned in cr.BANNED_LITERALS:
        test.assertNotIn(banned, message)
    for phrase in phrases:
        test.assertIn(phrase, message)


def one_hunk(test, old, new, path, klass, *phrases):
    hunks = cdc.classify_lines(old, new, path)
    test.assertEqual(len(hunks), 1, hunks)
    hunk = hunks[0]
    test.assertEqual(hunk["class"], klass, hunk)
    for phrase in phrases:
        test.assertIn(phrase, hunk["reason"])
    return hunk


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(CLASSIFIER)] + list(args),
        capture_output=True, text=True, env=cr.hermetic_git_env())


def last_outcome(proc):
    return proc.stdout.splitlines()[-1]


class CodeClassifierTest(unittest.TestCase):
    def test_python_full_line_and_trailing_comments_are_exempt(self):
        # Full-line comments only: a rewritten comment and an added one.
        old = b"def f():\n    return 1\n# top note\n"
        new = b"def f():\n    return 1\n# rewritten note\n# added note\n"
        hunks = cdc.classify_lines(old, new, SRC)
        self.assertTrue(hunks, hunks)
        for hunk in hunks:
            self.assertEqual(hunk["class"], cdc.CLASS_COMMENT_ONLY, hunks)
        ok, message = cdc.exempt_verdict(hunks)
        self.assertTrue(ok, message)
        assert_message(self, message, "comment-only")
        # A pure comment-line addition.
        one_hunk(self, b"a = 1\n", b"a = 1\n# added note\n", SRC,
                 cdc.CLASS_COMMENT_ONLY, "full-line comment was added")
        # The trailing comment of an otherwise byte-identical code line.
        one_hunk(self, b"x = 1  # a\n", b"x = 1  # b\n", SRC,
                 cdc.CLASS_COMMENT_ONLY, "byte-identical")
        # A string on the line does not swallow the comment span: the
        # hash inside the string literal is not a comment.
        one_hunk(self, b'msg = "a#b"  # note\n',
                 b'msg = "a#b"  # changed note\n', SRC,
                 cdc.CLASS_COMMENT_ONLY, "byte-identical")

    def test_python_trailing_near_miss_is_unclassified(self):
        # The code content changed beside the trailing comment.
        hunk = one_hunk(self, b"x = 1  # a\n", b"x = 2  # b\n", SRC,
                        cdc.CLASS_UNCLASSIFIED, "code content")
        ok, message = cdc.exempt_verdict([hunk])
        self.assertFalse(ok)
        assert_message(self, message, "not exempt")

    def test_python_docstring_and_cookie_are_unclassified(self):
        # Module docstring edit.
        one_hunk(self, b'"""Old module doc."""\n\nx = 1\n',
                 b'"""New module doc."""\n\nx = 1\n', SRC,
                 cdc.CLASS_UNCLASSIFIED, "runtime", "doctest")
        # Function docstring edit.
        one_hunk(self, b'def f():\n    """Old."""\n    return 1\n',
                 b'def f():\n    """New."""\n    return 1\n', SRC,
                 cdc.CLASS_UNCLASSIFIED, "runtime", "doctest")
        # A docstring interior line is string-literal content.
        one_hunk(self, b'"""Multi.\n\nline two.\n"""\nx = 1\n',
                 b'"""Multi.\n\nline THREE.\n"""\nx = 1\n', SRC,
                 cdc.CLASS_UNCLASSIFIED, "runtime", "doctest")
        # Encoding declaration on lines 1-2: edited.
        one_hunk(self, b"# -*- coding: ascii -*-\nx = 1\n",
                 b"# -*- coding: utf-8 -*-\nx = 1\n", SRC,
                 cdc.CLASS_UNCLASSIFIED, "runtime", "decode")
        # Added.
        one_hunk(self, b"x = 1\n", b"# coding: latin-1\nx = 1\n", SRC,
                 cdc.CLASS_UNCLASSIFIED, "runtime", "decode")
        # Removed.
        one_hunk(self, b"# coding: latin-1\nx = 1\n", b"x = 1\n", SRC,
                 cdc.CLASS_UNCLASSIFIED, "runtime", "decode")
        # Another PEP 263 spelling (the vim form).
        one_hunk(self, b"# vim: set fileencoding=latin-1 :\nx = 1\n",
                 b"# vim: set fileencoding=utf-8 :\nx = 1\n", SRC,
                 cdc.CLASS_UNCLASSIFIED, "runtime", "decode")

    def test_directive_comment_is_unclassified(self):
        cases = [
            (b"x = 1\n", b"x = 1  # noqa\n", SRC, "noqa"),
            (b"stream = open(p)\n",
             b"stream = open(p)  # type: ignore\n", SRC, "type: ignore"),
            (b"# lint clean\n", b"# eslint-disable no-undef\n", SRC,
             "eslint-disable"),
            (b"echo hi\n",
             b"echo hi  # shellcheck disable=SC2086\n", BASH_SRC,
             "shellcheck disable"),
            (b"x = (1, 2)\n", b"x = (1, 2)  # fmt: skip\n", SRC, "fmt:"),
            (b"import os\n", b"import os  # isort: skip\n", SRC, "isort:"),
            (b"x = 1\n", b"x = 1  # ruff: noqa\n", SRC, "ruff: noqa"),
            (b"# broad\n",
             b"# pylint: disable=broad-exception-raised\n", SRC,
             "pylint: disable"),
            (b"# ok\n", b"# flake8: noqa\n", SRC, "flake8: noqa"),
            # Changing a member stays refused.
            (b"x = 1  # noqa\n", b"x = 1  # noqa: E501\n", SRC, "noqa"),
        ]
        for old, new, path, member in cases:
            one_hunk(self, old, new, path, cdc.CLASS_UNCLASSIFIED,
                     "directive", member)

    def test_bash_full_line_comment_is_exempt_and_heredoc_is_not(self):
        # Full-line comments outside quote context.
        old = b"#!/bin/bash\n# setup\nvalue=1\n"
        new = b"#!/bin/bash\n# updated setup\nvalue=1\n"
        one_hunk(self, old, new, BASH_SRC, cdc.CLASS_COMMENT_ONLY,
                 "byte-identical")
        # The trailing comment of an otherwise byte-identical code line.
        one_hunk(self, b"#!/bin/bash\necho hi  # note\n",
                 b"#!/bin/bash\necho hi  # changed note\n", BASH_SRC,
                 cdc.CLASS_COMMENT_ONLY, "byte-identical")
        # The same shape inside a heredoc body: data, never comments.
        one_hunk(self,
                 b"#!/bin/bash\ncat <<EOF\n# data one\nEOF\necho done\n",
                 b"#!/bin/bash\ncat <<EOF\n# data two\nEOF\necho done\n",
                 BASH_SRC, cdc.CLASS_UNCLASSIFIED, "heredoc")
        # A trailing partial-line comment change: the hash is mid-word,
        # so the word itself is code content.
        one_hunk(self, b"echo a#old\n", b"echo a#new\n", BASH_SRC,
                 cdc.CLASS_UNCLASSIFIED, "code content")
        # A hash inside double quotes is code, not a comment.
        one_hunk(self, b'echo "# one"\n', b'echo "# two"\n', BASH_SRC,
                 cdc.CLASS_UNCLASSIFIED, "code content")
        # A shebang change is runtime load-bearing.
        one_hunk(self, b"#!/bin/sh\necho hi\n",
                 b"#!/bin/bash\necho hi\n", BASH_SRC,
                 cdc.CLASS_UNCLASSIFIED, "shebang")

    def test_bash_heredoc_opener_whitespace_and_quote_spellings_refuse(self):
        # The heredoc body is data under every opener spelling bash
        # accepts; a semantic change inside the body is unclassified.
        openers = (b"cat <<EOF\n", b"cat <<-EOF\n", b"cat <<'EOF'\n",
                   b"cat << EOF\n", b"cat <<- EOF\n", b'cat << "EOF"\n')
        for opener in openers:
            one_hunk(self,
                     b"#!/bin/bash\n" + opener
                     + b"# data one\nEOF\necho done\n",
                     b"#!/bin/bash\n" + opener
                     + b"# data two\nEOF\necho done\n",
                     BASH_SRC, cdc.CLASS_UNCLASSIFIED, "heredoc")

    def test_quoted_diff_path_tokens_decode(self):
        # A C-quoted diff path token decodes back to its UTF-8 text.
        self.assertEqual(
            cdc._diff_section_path('"a/src/\\346\\227\\245\\346\\234\\254.py"'),
            "src/" + "\u65e5\u672c" + ".py")
        # A token with an unknown escape, or with bytes that do not
        # decode as UTF-8, yields no path.
        self.assertIsNone(cdc._diff_section_path('"a/src/\\q.py"'))
        self.assertIsNone(cdc._diff_section_path('"a/src/\\377.py"'))

    def test_unsupported_language_fails_closed(self):
        one_hunk(self, b"x = 1\n", b"x = 2\n", "src/app.rb",
                 cdc.CLASS_UNCLASSIFIED, "no classifier support",
                 "fails closed")
        one_hunk(self, b"# title\n", b"# other title\n", "README.md",
                 cdc.CLASS_UNCLASSIFIED, "no classifier support",
                 "fails closed")
        hunks, ok, message = cdc.classify_delta(
            b"x = 1\n", b"x = 2\n", "src/app.rb")
        self.assertFalse(ok)
        assert_message(self, message, "fails closed")

    def test_generated_file_is_unclassified(self):
        one_hunk(self,
                 b"# Generated by frobnicator. DO NOT EDIT.\n# note\nx = 1\n",
                 b"# Generated by frobnicator. DO NOT EDIT.\n"
                 b"# changed note\nx = 1\n",
                 SRC, cdc.CLASS_UNCLASSIFIED, "generated")

    # ------------------------------------------------------------------
    # CLI exit stimuli
    # ------------------------------------------------------------------

    def test_exit_stimuli(self):
        repo = cr.build_scratch_repo(self)
        base = repo.commit_file(
            BASH_SRC, b"#!/bin/bash\necho hi  # note\n", "seed script")
        good = repo.commit_file(
            BASH_SRC, b"#!/bin/bash\necho hi  # changed note\n",
            "comment-only fix")
        # Exit 0 pass with an --emit-row row that validates under the
        # code family schema.
        proc = run_cli("--fix-commits", base, good, "--base", base,
                       "--repo", str(repo.root), "--emit-row")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(last_outcome(proc), "OUTCOME: pass")
        rows = [line for line in proc.stdout.splitlines()
                if line.startswith("corrections-row-json: ")]
        self.assertEqual(len(rows), 1, proc.stdout)
        row = json.loads(rows[0].split(": ", 1)[1])
        self.assertIsNone(cr.row_schema_reason(row, cr.FAMILY_CODE))
        self.assertEqual(row["kind"], cr.KIND_SCRIPT_VERIFIED)
        self.assertEqual(row["before_base"], base)
        self.assertEqual(row["before_head"], base)
        self.assertEqual(row["after_base"], base)
        self.assertEqual(row["after_head"], good)
        # Exit 1 fail: an unclassified fix.
        bad = repo.commit_file(
            BASH_SRC, b"#!/bin/bash\necho there\n", "code change")
        proc = run_cli("--fix-commits", good, bad, "--base", base,
                       "--repo", str(repo.root))
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertEqual(last_outcome(proc), "OUTCOME: fail")
        self.assertNotIn("corrections-row-json", proc.stdout)
        # Exit 3 tool error: an unresolvable ref (base and a head).
        proc = run_cli("--fix-commits", good, bad, "--base", "no-such-ref",
                       "--repo", str(repo.root))
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(last_outcome(proc), "OUTCOME: tool_error")
        proc = run_cli("--fix-commits", "no-such-ref", bad, "--base", base,
                       "--repo", str(repo.root))
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(last_outcome(proc), "OUTCOME: tool_error")
        # Exit 3 tool error: the --repo operand is not a repository.
        proc = run_cli("--fix-commits", good, bad, "--base", base,
                       "--repo", str(repo.root / "absent-dir"))
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(last_outcome(proc), "OUTCOME: tool_error")
        # Exit 3 tool error: an unreadable operand (a blob that is not
        # decodable UTF-8 text).
        latin = repo.commit_file(SRC, b"x = 1\nnote = '\x97'\n",
                                 "latin-1 bytes")
        proc = run_cli("--fix-commits", bad, latin, "--base", base,
                       "--repo", str(repo.root))
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(last_outcome(proc), "OUTCOME: tool_error")
        self.assertIn("not decodable", proc.stderr)
        # Exit 2 indeterminate: git plumbing fails over resolved refs.
        # The fix resolves, the diff computes, and the blob read behind it
        # fails (a gitlink path).
        repo2 = cr.build_scratch_repo(self, name="gitlink-repo")
        g0 = repo2.commit_file("README.md", b"seed\n", "seed")
        fake_blob = "abcdef0123456789abcdef0123456789abcdef01"
        repo2.git("update-index", "--add", "--cacheinfo",
                  "160000,%s,src/gone.py" % fake_blob)
        repo2.git("commit", "-q", "-m", "gitlink path",
                  date=repo2.next_date())
        g1 = repo2.head()
        proc = run_cli("--fix-commits", g0, g1, "--base", g0,
                       "--repo", str(repo2.root))
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertEqual(last_outcome(proc), "OUTCOME: indeterminate")


class RangeRoundTripTest(unittest.TestCase):
    def certified_fixture(self):
        """The production shape: a base commit and two content commits
        certified as the review's range with both refs in the committed
        seal entry, the round-close commit and the seal entry commit
        landing between the certified head and the fix."""
        repo = cr.build_scratch_repo(self)
        b0 = repo.commit_file(SRC, V0, "base")
        c1 = repo.commit_file(SRC, V1, "feature one")
        c2 = repo.commit_file(SRC, V2, "feature two")
        certified = cr.diff_bytes(repo.root, b0, c2)
        close = repo.commit_allow_empty("round 1 close")
        entry = repo.append_seal_entry(
            SLUG, 1, SRC, c2, cr.sha256_hex(certified), close,
            reviewed=(b0, c2, cr.sha256_hex(certified)))
        return repo, {"b0": b0, "c1": c1, "c2": c2, "close": close,
                      "entry": entry, "certified": certified,
                      "certified_digest": cr.sha256_hex(certified)}

    def test_rebind_via_certified_refs(self):
        repo, fx = self.certified_fixture()
        # With the fix left uncommitted there is no hop: the heads resolve
        # the identical state, the correction is unclassifiable, and the
        # default re-review applies.
        repo.write_file(SRC, V3)
        self.assertEqual(repo.head(), fx["entry"])
        proc = run_cli("--fix-commits", fx["entry"], fx["entry"],
                       "--base", fx["b0"], "--repo", str(repo.root))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(last_outcome(proc), "OUTCOME: fail")
        self.assertIn("unclassifiable", proc.stdout)
        self.assertIn("re-review", proc.stdout)
        self.assertNotIn("corrections-row-json", proc.stdout)
        # The committed fix extends the branch by one commit; the hop diff
        # carries the seal file beside the comment-only fix.
        c3 = repo.commit_file(SRC, V3, "comment-only fix")
        fix_diff = cr.diff_bytes(repo.root, fx["c2"], c3)
        names = [new if new is not None else old
                 for old, new in cdc.parse_diff_paths(fix_diff)]
        self.assertIn(cr.seal_relpath(SRC, SLUG), names)
        self.assertIn(SRC, names)
        # The hop classifies comment-only: the seal path is excluded and
        # the source fix is provably comment-only.
        self.assertEqual(
            cdc.hop_unclassified(repo.root, fx["c2"], c3, fix_diff), [])
        # The CLI emits the row through corrections_record's schema
        # builder, with the before refs equal to the certified range and
        # the after side chained from it.
        proc = run_cli("--fix-commits", fx["c2"], c3, "--base", fx["b0"],
                       "--repo", str(repo.root), "--emit-row")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(last_outcome(proc), "OUTCOME: pass")
        self.assertIn("excluded (seal path): %s"
                      % cr.seal_relpath(SRC, SLUG), proc.stdout)
        rows = [line for line in proc.stdout.splitlines()
                if line.startswith("corrections-row-json: ")]
        self.assertEqual(len(rows), 1, proc.stdout)
        row = json.loads(rows[0].split(": ", 1)[1])
        self.assertIsNone(cr.row_schema_reason(row, cr.FAMILY_CODE))
        self.assertEqual(row["before_base"], fx["b0"])
        self.assertEqual(row["before_head"], fx["c2"])
        self.assertEqual(row["after_base"], fx["c2"])
        self.assertEqual(row["after_head"], c3)
        self.assertEqual(row["before_digest"], fx["certified_digest"])
        self.assertEqual(row["after_digest"], cr.sha256_hex(fix_diff))
        # The verifier regenerates both diffs, hash-confirms them, and
        # classifies the hop comment-only.
        ok, msg = cdc.verify_code_corrections(
            repo.root, SRC, 1, fx["certified_digest"], [row],
            certified_range={"base": fx["b0"], "head": fx["c2"]},
            slug=SLUG)
        self.assertTrue(ok, msg)
        assert_message(self, msg, "chain verified")
        # Refusal: the before refs differ from the certified range.
        drifted = dict(row)
        drifted["before_base"] = fx["c1"]
        ok, msg = cdc.verify_code_corrections(
            repo.root, SRC, 1, fx["certified_digest"], [drifted],
            certified_range={"base": fx["b0"], "head": fx["c2"]},
            slug=SLUG)
        self.assertFalse(ok)
        assert_message(self, msg, "before refs", "certified range")
        # Refusal: the after base is not the before head.
        chained = dict(row)
        chained["after_base"] = fx["b0"]
        ok, msg = cdc.verify_code_corrections(
            repo.root, SRC, 1, fx["certified_digest"], [chained],
            certified_range={"base": fx["b0"], "head": fx["c2"]},
            slug=SLUG)
        self.assertFalse(ok)
        assert_message(self, msg, "after base is not the before head")
        # Refusal: the after head is not the current branch head.
        repo.commit_file(SRC, V4, "next change")
        ok, msg = cdc.verify_code_corrections(
            repo.root, SRC, 1, fx["certified_digest"], [row],
            certified_range={"base": fx["b0"], "head": fx["c2"]},
            slug=SLUG)
        self.assertFalse(ok)
        assert_message(self, msg, "after head", "branch head")

    def test_non_ascii_quoted_path_hops(self):
        # A non-ASCII path diffuses as a C-quoted token under
        # core.quotePath; the decoded path must resolve to blobs on both
        # sides so the hop cannot vacuously pass.
        repo = cr.build_scratch_repo(self)
        name = "src/" + "\u65e5\u672c" + ".py"
        base = repo.commit_file(name, b"x = 1\n", "seed non-ascii path")
        mid = repo.commit_file(name, b"x = 2\n", "code change")
        diff = cr.diff_bytes(repo.root, base, mid)
        self.assertEqual(cdc.parse_diff_paths(diff), [(name, name)])
        verdicts = cdc.hop_unclassified(repo.root, base, mid, diff)
        self.assertTrue(verdicts, verdicts)
        self.assertIn(name, verdicts[0])
        # A comment-only change under the quoted path still passes.
        top = repo.commit_file(name, b"x = 2\n# reviewed\n",
                               "comment-only fix")
        diff = cr.diff_bytes(repo.root, mid, top)
        self.assertEqual(
            cdc.hop_unclassified(repo.root, mid, top, diff), [])

    def test_unresolvable_quoted_path_refuses_the_hop(self):
        # A diff naming a quoted path that resolves to no blob on a side
        # it names refuses fail-closed; it never reads as empty bytes.
        repo = cr.build_scratch_repo(self)
        base = repo.commit_file(SRC, b"x = 1\n", "seed")
        diff = (
            'diff --git "a/src/\\346\\227\\245.py" '
            '"b/src/\\346\\227\\245.py"\n'
            "index 0000000..1111111 100644\n"
            '--- "a/src/\\346\\227\\245.py"\n'
            '+++ "b/src/\\346\\227\\245.py"\n'
            "@@ -1 +1 @@\n"
            "-x = 1\n"
            "+x = 2\n").encode("ascii")
        verdicts = cdc.hop_unclassified(repo.root, base, base, diff)
        self.assertTrue(verdicts, verdicts)
        self.assertIn("no blob resolves", verdicts[0])

    def test_binary_sections_refuse_the_hop(self):
        # A binary diff section carries no ---/+++ headers; it refuses
        # the hop instead of dropping the file from classification.
        repo = cr.build_scratch_repo(self)
        repo.commit_file("blob.bin", b"\x00\x01\x02", "seed binary")
        base = repo.commit_file(SRC, b"x = 1\n", "seed source")
        # A binary-only hop refuses.
        head = repo.commit_file("blob.bin", b"\x00\x01\x03", "binary change")
        diff = cr.diff_bytes(repo.root, base, head)
        self.assertEqual(cdc.parse_diff_paths(diff), [(None, None)])
        verdicts = cdc.hop_unclassified(repo.root, base, head, diff)
        self.assertTrue(verdicts, verdicts)
        self.assertIn("binary", verdicts[0])
        # A mixed hop (a binary change beside a comment-only change)
        # refuses too.
        head = repo.commit_file(SRC, b"x = 1\n# reviewed\n", "comment fix")
        diff = cr.diff_bytes(repo.root, base, head)
        verdicts = cdc.hop_unclassified(repo.root, base, head, diff)
        self.assertTrue(verdicts, verdicts)
        # A pure comment-only hop over the same tree still passes.
        nxt = repo.commit_file(SRC, b"x = 1\n# rewritten\n", "comment fix 2")
        diff = cr.diff_bytes(repo.root, head, nxt)
        self.assertEqual(
            cdc.hop_unclassified(repo.root, head, nxt, diff), [])

    def test_mode_and_rename_sections_refuse_the_hop(self):
        # Mode and rename markers are runtime or path visible, never
        # comment content (r1 fold): a chmod or a rename riding beside a
        # comment-only fix refuses the hop unclassified instead of
        # dropping its section from the verdict.
        repo = cr.build_scratch_repo(self)
        repo.commit_file("run.sh", b"#!/bin/bash\necho hi\n", "seed script")
        base = repo.commit_file(SRC, V0, "seed source")
        # A chmod riding with a comment-only fix refuses.
        (repo.root / "run.sh").chmod(0o755)
        head = repo.commit_file(SRC, b"def f():\n    # reviewed\n    return 1\n",
                                "comment fix with chmod")
        diff = cr.diff_bytes(repo.root, base, head)
        self.assertTrue(
            any(s["rename_or_mode"] and not s["content"]
                for s in cdc.diff_sections(diff)),
            diff.decode("utf-8", "replace"))
        verdicts = cdc.hop_unclassified(repo.root, base, head, diff)
        self.assertTrue(verdicts, verdicts)
        self.assertIn("rename or mode", verdicts[0])
        # A pure rename riding with a comment-only fix refuses too.
        repo2 = cr.build_scratch_repo(self)
        repo2.commit_file("old_name.py", V1, "seed module")
        base2 = repo2.commit_file(SRC, V0, "seed source")
        repo2.git("mv", "old_name.py", "new_name.py")
        head2 = repo2.commit_file(SRC, b"def f():\n    # reviewed\n    return 1\n",
                                  "comment fix with rename")
        diff2 = cr.diff_bytes(repo2.root, base2, head2)
        self.assertTrue(
            any(s["rename_or_mode"] and not s["content"]
                for s in cdc.diff_sections(diff2)),
            diff2.decode("utf-8", "replace"))
        verdicts2 = cdc.hop_unclassified(repo2.root, base2, head2, diff2)
        self.assertTrue(verdicts2, verdicts2)
        self.assertIn("rename or mode", verdicts2[0])
        # A comment-only fix alone still passes over the same tree.
        nxt = repo.commit_file(SRC, b"def f():\n    # rewritten\n    return 1\n",
                               "comment fix alone")
        alone_diff = cr.diff_bytes(repo.root, head, nxt)
        self.assertEqual(
            cdc.hop_unclassified(repo.root, head, nxt, alone_diff), [])
        # The CLI refuses the chmod-riding fix: exit 1, no row.
        proc = run_cli("--fix-commits", base, head, "--base", base,
                       "--repo", str(repo.root), "--emit-row")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("rename or mode", proc.stdout)
        self.assertIn("no row", proc.stdout)


    def test_acked_emit_carries_the_receipt(self):
        # The operator-acked emit mirrors the plan classifier's: an
        # unclassified fix still reports the fail outcome but emits the
        # row carrying the receipt, so code rows can carry receipts; the
        # ack-witness operand echoes beside the row and resolves at the
        # validator against the caller's context.
        repo = cr.build_scratch_repo(self)
        base = repo.commit_file(SRC, V0, "base")
        bad = repo.commit_file(SRC, V1, "code change")
        receipt_dir = tempfile.TemporaryDirectory(prefix="cdc-receipt-")
        self.addCleanup(receipt_dir.cleanup)
        receipt_path = Path(receipt_dir.name) / "receipt.json"
        receipt_path.write_text(json.dumps({
            "directive": "re-bind the unclassified delta",
            "authorization_witness": "state/turns/0001.record",
            "classifier_gap_row":
                "docs/history/backlog/2026-10-04-typography-bucket.md",
        }))
        proc = run_cli("--fix-commits", base, bad, "--base", base,
                       "--repo", str(repo.root), "--emit-row",
                       "--kind", "operator-acked",
                       "--receipt", str(receipt_path),
                       "--ack-witness", "state/turns/0001.record")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(last_outcome(proc), "OUTCOME: fail")
        rows = [line for line in proc.stdout.splitlines()
                if line.startswith("corrections-row-json: ")]
        self.assertEqual(len(rows), 1, proc.stdout)
        self.assertIn("ack-witness: state/turns/0001.record", proc.stdout)
        row = json.loads(rows[0].split(": ", 1)[1])
        self.assertIsNone(cr.row_schema_reason(row, cr.FAMILY_CODE))
        self.assertEqual(row["kind"], cr.KIND_OPERATOR_ACKED)
        self.assertEqual(sorted(row["receipt"]),
                         ["authorization_witness", "classifier_gap_row",
                          "directive"])
        # The usage guards mirror the plan classifier's: the acked kind
        # requires the receipt, and neither operand rides script-verified
        # or a witness without the acked kind.
        proc = run_cli("--fix-commits", base, bad, "--base", base,
                       "--repo", str(repo.root), "--kind", "operator-acked")
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        proc = run_cli("--fix-commits", base, bad, "--base", base,
                       "--repo", str(repo.root), "--receipt",
                       str(receipt_path))
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        proc = run_cli("--fix-commits", base, bad, "--base", base,
                       "--repo", str(repo.root),
                       "--ack-witness", "state/turns/0001.record")
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)

    def test_acked_receipt_wrong_typed_field_maps_to_tool_error(self):
        # A receipt that is valid JSON but carries a wrong-typed required
        # field fails the schema at emit-time row validation (r2 fold):
        # the failure maps to exit 3 with the final OUTCOME line, never
        # an uncaught traceback past the outcome contract.
        repo = cr.build_scratch_repo(self)
        base = repo.commit_file(SRC, V0, "base")
        bad = repo.commit_file(SRC, V1, "code change")
        receipt_dir = tempfile.TemporaryDirectory(prefix="cdc-receipt-")
        self.addCleanup(receipt_dir.cleanup)
        receipt_path = Path(receipt_dir.name) / "receipt.json"
        receipt_path.write_text(json.dumps({
            "directive": 123,
            "authorization_witness": "state/turns/0001.record",
            "classifier_gap_row":
                "docs/history/backlog/2026-10-04-typography-bucket.md",
        }))
        proc = run_cli("--fix-commits", base, bad, "--base", base,
                       "--repo", str(repo.root), "--emit-row",
                       "--kind", "operator-acked",
                       "--receipt", str(receipt_path),
                       "--ack-witness", "state/turns/0001.record")
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(last_outcome(proc), "OUTCOME: tool_error")
        self.assertIn("receipt", proc.stderr)
        self.assertNotIn("corrections-row-json", proc.stdout)

    def test_no_classifiable_hunks_reason_names_the_condition(self):
        # The no-classifiable-hunks refusal names the actual condition
        # (seal exclusion, unparseable or binary sections); it never
        # claims every path lies under the seal path.
        repo = cr.build_scratch_repo(self)
        b0 = repo.commit_file(SRC, V0, "base")
        entry = repo.append_seal_entry(SLUG, 1, SRC, b0, "digest", b0)
        diff = cr.diff_bytes(repo.root, b0, entry)
        verdicts = cdc.hop_unclassified(repo.root, b0, entry, diff)
        self.assertEqual(len(verdicts), 1, verdicts)
        self.assertIn("no classifiable hunks", verdicts[0])
        self.assertNotIn("every changed path lies under", verdicts[0])
        proc = run_cli("--fix-commits", b0, entry, "--base", b0,
                       "--repo", str(repo.root))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("no classifiable hunks", proc.stdout)
        self.assertNotIn("every changed path lies under", proc.stdout)


if __name__ == "__main__":
    unittest.main()
