#!/usr/bin/env python3
"""Selftest for corrections_record.py.

Every fixture is a hermetic scratch git repo under TemporaryDirectory; no
host state is touched. Pinned: the row schema for both kinds with the
vacuous-row and empty-array edges, the seal-recorded anchor leg, the
per-hop digest binding to bytes re-derived from git, linkage, terminal,
seal integrity (range match, hop dating, digest-field edit detection,
append-only), the subject-bound operator ack receipt with the injected
witness path, the advisory-lock append, the marker-prefix and
banned-literal constants, the seal slug shape gate (a slug outside the
safe kebab shape refuses as a schema error at the seal-path derivation,
never echoing the slug), the excluded-region scanner, the fixture
builder itself, the canonical correction-row digest, the optional
author_session_id schema (operator-acked plan-family rows only), and
the primary-state authorization route (the fixed scheduler-state
selector, the matched correction_authorizations entry, and the
kind-aware classification bypass for a fully verified operator-acked
plan hop).
"""

import fcntl
import inspect
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import corrections_record as cr
import session_channel as sc

# The four session-channel sources; every row-identity, writer, and
# mode-boundary fixture pins and clears these using the session-channel
# selftest save/restore pattern (sc._save_env / sc._restore_env).
SESSION_ENV_NAMES = (sc.CLAUDE_SESSION_ENV, sc.CURSOR_SESSION_ENV,
                     sc.CURSOR_CONVERSATION_ENV, sc.CODEX_SESSION_ENV)

PLAN_REL = "docs/history/plans/acme-plan.md"
PLAN_SLUG = "acme-plan"
D1 = b"# plan\n\nalpha bravo.\n"
D2 = b"# plan\n\nalpha, bravo.\n"
D3 = b"# plan\n\nalpha, bravo! charlie\n"
NOW = "2026-10-04T00:00:00Z"


def hx(data):
    return cr.sha256_hex(data)


def plan_row(before, after, evidence, kind=cr.KIND_SCRIPT_VERIFIED,
             recorded_by="session-a", receipt=None, hunk_digest=None):
    if hunk_digest is None:
        hunk_digest = hx(b"hunk-bytes")
    row = {
        "kind": kind,
        "before_digest": before,
        "after_digest": after,
        "evidence_commit": evidence,
        "hunks": [{"header": "@@ -2 +2 @@", "digest": hunk_digest}],
        "recorded_at": NOW,
        "recorded_by": recorded_by,
    }
    if receipt is not None:
        row["receipt"] = receipt
    return row


def code_row(before_base, before_head, after_base, after_head,
             before_digest, after_digest, kind=cr.KIND_SCRIPT_VERIFIED,
             receipt=None):
    row = {
        "kind": kind,
        "before_digest": before_digest,
        "after_digest": after_digest,
        "before_base": before_base,
        "before_head": before_head,
        "after_base": after_base,
        "after_head": after_head,
        "hunks": [{"header": "@@ -1 +1 @@", "digest": hx(b"hunk")}],
        "recorded_at": NOW,
        "recorded_by": "session-a",
    }
    if receipt is not None:
        row["receipt"] = receipt
    return row


def plan_fixture(test):
    """D1 committed at start, round-close commit, seal entry commit, then
    the D2 fix commit; dates pinned and increasing."""
    repo = cr.build_scratch_repo(test)
    start = repo.commit_file(PLAN_REL, D1, "seed plan")
    close = repo.commit_allow_empty("round 1 close")
    entry = repo.append_seal_entry(PLAN_SLUG, 1, PLAN_REL, start, hx(D1),
                                   close)
    hop1 = repo.commit_file(PLAN_REL, D2, "fix typography")
    return repo, {"start": start, "close": close, "entry": entry,
                  "hop1": hop1}


def orphan_commit(repo, message="orphan"):
    tree = repo.git("rev-parse", "HEAD^{tree}").stdout.strip()
    return repo.git("commit-tree", tree, "-m", message).stdout.strip()


def vplan(repo, rows, source_digest, current, **kw):
    return cr.verify_corrections(
        repo.root, PLAN_REL, cr.FAMILY_PLAN, 1, source_digest, rows,
        current_bytes=current, **kw)


def assert_refusal(test, msg, leg, *phrases):
    test.assertIsInstance(msg, str)
    test.assertTrue(msg.startswith(cr.MARKER_PREFIX), msg)
    test.assertIn(cr.LEG_REASONS[leg], msg)
    for phrase in phrases:
        test.assertIn(phrase, msg)
    for banned in cr.BANNED_LITERALS:
        test.assertNotIn(banned, msg)


class RecordSchemaTest(unittest.TestCase):
    def setUp(self):
        self.plan_row = plan_row("a" * 64, "b" * 64, "c" * 40)
        self.code_row = code_row("a" * 40, "b" * 40, "b" * 40, "d" * 40,
                                 "e" * 64, "f" * 64,
                                 kind=cr.KIND_OPERATOR_ACKED,
                                 receipt={"directive": "re-bind",
                                          "authorization_witness":
                                              "state/turns/0001.record",
                                          "classifier_gap_row":
                                              "docs/history/backlog/g.md"})

    def test_row_shapes_both_kinds(self):
        self.assertIsNone(cr.row_schema_reason(self.plan_row,
                                               cr.FAMILY_PLAN))
        self.assertIsNone(cr.row_schema_reason(self.code_row,
                                               cr.FAMILY_CODE))
        cr.validate_row(self.plan_row, cr.FAMILY_PLAN)
        cr.validate_row(self.code_row, cr.FAMILY_CODE)
        # The kind alone decides the receipt key: an acked plan row carries
        # it, a script-verified row must not.
        acked_plan = dict(self.plan_row)
        acked_plan["kind"] = cr.KIND_OPERATOR_ACKED
        acked_plan["receipt"] = dict(self.code_row["receipt"])
        self.assertIsNone(cr.row_schema_reason(acked_plan, cr.FAMILY_PLAN))
        with_receipt = dict(self.plan_row)
        with_receipt["receipt"] = {"directive": "x",
                                   "authorization_witness": "w",
                                   "classifier_gap_row": "g"}
        self.assertIn("unexpected key",
                      cr.row_schema_reason(with_receipt, cr.FAMILY_PLAN))

    def test_schema_refusals_name_the_rule(self):
        cases = []
        missing = dict(self.plan_row)
        del missing["evidence_commit"]
        cases.append((missing, "missing required key", cr.FAMILY_PLAN))
        extra = dict(self.plan_row)
        extra["surprise"] = 1
        cases.append((extra, "unexpected key", cr.FAMILY_PLAN))
        nonhex = dict(self.plan_row)
        nonhex["before_digest"] = "zz" * 32
        cases.append((nonhex, "hex64", cr.FAMILY_PLAN))
        unknown = dict(self.plan_row)
        unknown["kind"] = "self-approved"
        cases.append((unknown, "unknown kind", cr.FAMILY_PLAN))
        vacuous = dict(self.plan_row)
        vacuous["after_digest"] = vacuous["before_digest"]
        cases.append((vacuous, "vacuous", cr.FAMILY_PLAN))
        empty_hunks = dict(self.plan_row)
        empty_hunks["hunks"] = []
        cases.append((empty_hunks, "hunks is empty", cr.FAMILY_PLAN))
        bad_hunk = dict(self.plan_row)
        bad_hunk["hunks"] = [{"header": "@@", "digest": "nope"}]
        cases.append((bad_hunk, "hex64", cr.FAMILY_PLAN))
        not_object = "junk"
        cases.append((not_object, "schema refusal", cr.FAMILY_PLAN))
        short_receipt = dict(self.code_row)
        short_receipt["receipt"] = {"directive": "re-bind"}
        cases.append((short_receipt, "missing required key",
                      cr.FAMILY_CODE))
        for row, phrase, family in cases:
            reason = cr.row_schema_reason(row, family)
            self.assertIsNotNone(reason, row)
            self.assertTrue(reason.startswith(cr.MARKER_PREFIX), reason)
            self.assertIn(phrase, reason)
        self.assertIn("not an array", cr.corrections_array_reason("x"))
        self.assertIn("empty", cr.corrections_array_reason([]))
        self.assertIsNone(cr.corrections_array_reason(None))
        self.assertIn("unknown kind",
                      cr.corrections_array_reason([{"kind": "junk"}]))

    def test_record_operand_loading(self):
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "record.json"
            good.write_text(json.dumps({"corrections": [self.plan_row]}))
            self.assertEqual(len(cr.load_corrections(good)), 1)
            bare = Path(tmp) / "bare.json"
            bare.write_text(json.dumps([self.plan_row]))
            self.assertEqual(len(cr.load_corrections(bare)), 1)
            bad = Path(tmp) / "bad.json"
            bad.write_text("{not json")
            try:
                cr.load_corrections(bad)
                self.fail("expected CorrectionsSchemaError")
            except cr.CorrectionsSchemaError as exc:
                self.assertIn("decodable JSON", str(exc))


class AnchorLegTest(unittest.TestCase):
    def test_seal_recorded_anchor(self):
        repo, c = plan_fixture(self)
        row = plan_row(hx(D1), hx(D2), c["hop1"])
        ok, msg = vplan(repo, [row], hx(D1), D2)
        self.assertTrue(ok, msg)
        self.assertTrue(msg.startswith(cr.MARKER_PREFIX), msg)
        self.assertIn("chain verified", msg)
        # Preserved pre-landing shape: the anchors are plain ancestors, so
        # the landing resolution never ran and its success suffix must
        # stay absent from the verified message (r1 T6 negative pin).
        self.assertNotIn(
            "squash-orphaned seal anchors resolved through HEAD-ancestor",
            msg)
        # The declared digest may also equal the verified chain's terminal.
        ok, msg = vplan(repo, [row], hx(D2), D2)
        self.assertTrue(ok, msg)
        # The honest clean shape: declared digest equals both the current
        # bytes and the seal round-start digest, no record.
        ok, msg = vplan(repo, [], hx(D1), D1)
        self.assertTrue(ok, msg)
        # A bare rewrite: declared digest matches neither the seal entry
        # nor a verifying record.
        ok, msg = vplan(repo, [], hx(D2), D2)
        self.assertFalse(ok)
        assert_refusal(self, msg, "anchor", "bare rewrite")
        # An unresolvable seal: no entry for the sidecar's round.
        ok, msg = cr.verify_corrections(
            repo.root, PLAN_REL, cr.FAMILY_PLAN, 2, hx(D2), [row],
            current_bytes=D2)
        self.assertFalse(ok)
        assert_refusal(self, msg, "anchor", "no resolvable entry")
        # A seal entry whose round-close commit is not an ancestor of HEAD
        # and whose sealed round-start bytes no first-parent commit
        # carries: the no-byte-identity refusal (re-keyed from the
        # pre-resolver shape).
        repo2, c2 = plan_fixture(self)
        orphan = orphan_commit(repo2)
        repo2.write_seal_entry(PLAN_SLUG, 1, PLAN_REL, c2["start"],
                               hx(D3), orphan, message="seal: orphan close")
        ok, msg = vplan(repo2, [plan_row(hx(D1), hx(D2), c2["hop1"])],
                        hx(D1), D2)
        self.assertFalse(ok)
        assert_refusal(self, msg, "anchor", "round-close commit",
                       "no first-parent ancestor")
        # A moved anchor: the round-start blob does not re-hash to the
        # entry's claimed round-start digest.
        repo3, c3 = plan_fixture(self)
        repo3.write_seal_entry(PLAN_SLUG, 1, PLAN_REL, c3["start"],
                               hx(D2), c3["close"], message="seal: moved")
        ok, msg = vplan(repo3, [plan_row(hx(D2), hx(D3), c3["hop1"])],
                        hx(D2), D2)
        self.assertFalse(ok)
        assert_refusal(self, msg, "anchor", "re-hash")

    # ------------------------------------------------------------------
    # Legacy one-line seal rows (committed corpus shapes), family-aware
    # lookup, and the landed-anchor resolver (certification-seal-landing-
    # survival plan, Task 1).
    # ------------------------------------------------------------------

    LEGACY_SHAPES = (
        # Review-row shape: labeled pipe segments naming every anchor.
        "# Review certification seal: acme-plan\n"
        "\n"
        "r3 | artifact {artifact} (sidecar .stats.json, source_digest "
        "{digest}) | round-start commit {start} | round-start digest "
        "{digest} | round-close digest {digest} (clean round, no fold "
        "after) | round-close commit {close} (the authoring branch tip; "
        "the squash landing folds the branch) | verdict ready=yes, zero "
        "findings, the rule-4 blind correctness-completeness probe "
        "complete\n",
        # Plan-row shape: a bare artifact path segment and paired
        # round-start commit and digest tokens.
        "r3 | {artifact} | round-start {start} digest {digest} | "
        "round-close {close} (the squash landing carrying the certified "
        "bytes) | certifying chain r3 (fresh-adversarial focused panel, "
        "zero blocking)\n",
        # Dash-prefixed row: date, path, and dashed digest labels.
        "- r3 2026-10-14 {artifact} round-start {start} round-start-digest "
        "{digest} round-close {close} certified-digest {digest} zero "
        "unresolved blocking (series r1 full panel)\n",
    )

    def legacy_repo(self, shape, *, start=None, close=None, digest=None,
                    artifact=PLAN_REL, round_line="r3"):
        repo = cr.build_scratch_repo(self)
        start = start if start is not None else repo.commit_file(
            PLAN_REL, D1, "seed plan")
        close = close if close is not None else repo.commit_allow_empty(
            "round 3 close")
        digest = digest if digest is not None else hx(D1)
        rel = cr.seal_relpath(artifact, PLAN_SLUG)
        text = shape.format(artifact=artifact, digest=digest, start=start,
                            close=close)
        if round_line != "r3":
            text = text.replace("r3 ", "%s " % round_line, 1)
        repo.write_file(rel, text)
        return repo, rel, start, close

    def test_legacy_row_shapes_parse_to_the_entry_model(self):
        for shape in self.LEGACY_SHAPES:
            repo, rel, start, close = self.legacy_repo(shape)
            entry = cr.load_seal_entry(repo.root, rel, 3, cr.FAMILY_PLAN)
            self.assertIsNotNone(entry, shape)
            self.assertEqual(entry.round, 3)
            self.assertEqual(entry.fields["artifact"], PLAN_REL)
            self.assertEqual(entry.fields["round_start_commit"], start)
            self.assertEqual(entry.fields["round_start_digest"], hx(D1))
            self.assertEqual(entry.fields["round_close_commit"], close)
            # The legacy row end to end: the zero-hop clean shape verifies
            # over the unrewritten producer prose.
            ok, msg = cr.verify_corrections(
                repo.root, PLAN_REL, cr.FAMILY_PLAN, 3, hx(D1), [],
                current_bytes=D1)
            self.assertTrue(ok, msg)
            self.assertIn("chain verified", msg)
        # An abbreviated commit identifier in any shape stays
        # unresolvable, never silently widened.
        for shape, field in ((self.LEGACY_SHAPES[0], "start"),
                             (self.LEGACY_SHAPES[1], "start"),
                             (self.LEGACY_SHAPES[2], "close")):
            repo, rel, _s, _c = self.legacy_repo(
                shape, **{field: "4a6c8b2b"})
            self.assertIsNone(cr.load_seal_entry(
                repo.root, rel, 3, cr.FAMILY_PLAN), field)
        # A row-shaped line without the canonical fields stays prose and
        # the round stays unresolvable.
        repo, rel, _s, _c = self.legacy_repo(
            "r6 | %s | certifying digest %s (matches the plan bytes on "
            "disk at sealing) | certifying chain r6\n"
            % (PLAN_REL, hx(D1)))
        self.assertIsNone(cr.load_seal_entry(repo.root, rel, 6,
                                             cr.FAMILY_PLAN))
        repo2, rel2, _s2, _c2 = self.legacy_repo(
            "r3 | artifact %s | round-start commit only\n" % PLAN_REL)
        self.assertIsNone(cr.load_seal_entry(repo2.root, rel2, 3,
                                             cr.FAMILY_PLAN))
        # Duplicate same-family rows refuse: a legacy row beside a block
        # entry for the same round, and two identical legacy rows.
        repo3, rel3, start3, close3 = self.legacy_repo(self.LEGACY_SHAPES[0])
        with open(Path(repo3.root) / rel3, "a") as handle:
            handle.write("\n## round 3\nartifact: %s\nround_start_commit: "
                         "%s\nround_start_digest: %s\nround_close_commit: "
                         "%s\n" % (PLAN_REL, start3, hx(D1), close3))
        self.assertIsNone(cr.load_seal_entry(repo3.root, rel3, 3,
                                             cr.FAMILY_PLAN))
        repo4, rel4, _s4, _c4 = self.legacy_repo(self.LEGACY_SHAPES[1])
        text = (Path(repo4.root) / rel4).read_text()
        (Path(repo4.root) / rel4).write_text(text + text)
        self.assertIsNone(cr.load_seal_entry(repo4.root, rel4, 3,
                                             cr.FAMILY_PLAN))
        # Legacy rows never select as code-family entries: they carry no
        # family or staging_round fields.
        repo5, rel5, _s5, _c5 = self.legacy_repo(self.LEGACY_SHAPES[0])
        self.assertIsNone(cr.load_seal_entry(repo5.root, rel5, 3,
                                             cr.FAMILY_CODE))

    def test_load_seal_entry_distinguishes_plan_and_code_rounds(self):
        repo = cr.build_scratch_repo(self)
        start = repo.commit_file(PLAN_REL, D1, "seed plan")
        close = repo.commit_allow_empty("round 2 close")
        rel = cr.seal_relpath(PLAN_REL, PLAN_SLUG)
        code_digest = hx(b"code-bytes")
        repo.write_file(rel, "\n".join([
            "## round 2",
            "artifact: %s" % PLAN_REL,
            "round_start_commit: %s" % start,
            "round_start_digest: %s" % hx(D1),
            "round_close_commit: %s" % close,
            "",
            "## round 2",
            "artifact: src/app.py",
            "round_start_commit: %s" % start,
            "round_start_digest: %s" % code_digest,
            "round_close_commit: %s" % close,
            "reviewed_base: %s" % start,
            "reviewed_head: %s" % start,
            "range_digest: %s" % code_digest,
            "family: code",
            "staging_round: r2",
        ]) + "\n")
        repo.commit_all("colliding rounds")
        plan_entry = cr.load_seal_entry(repo.root, rel, 2, cr.FAMILY_PLAN)
        self.assertIsNotNone(plan_entry)
        self.assertEqual(plan_entry.fields["artifact"], PLAN_REL)
        self.assertNotIn("family", plan_entry.fields)
        code_entry = cr.load_seal_entry(repo.root, rel, 2, cr.FAMILY_CODE)
        self.assertIsNotNone(code_entry)
        self.assertEqual(code_entry.fields["family"], cr.FAMILY_CODE)
        self.assertEqual(code_entry.fields["staging_round"], "r2")
        # The block number alone never selects a code entry.
        self.assertIsNone(cr.load_seal_entry(repo.root, rel, 3,
                                             cr.FAMILY_CODE))
        # A duplicate code block for the same staging round refuses while
        # the plan lookup keeps resolving its own entry.
        text = (repo.root / rel).read_text()
        duplicate = text[text.index("## round 2", 1):]
        repo.write_file(rel, text + duplicate)
        self.assertIsNone(cr.load_seal_entry(repo.root, rel, 2,
                                             cr.FAMILY_CODE))
        self.assertIsNotNone(cr.load_seal_entry(repo.root, rel, 2,
                                                cr.FAMILY_PLAN))
        # A verifier case: an orphaned code-family anchor refuses even
        # though HEAD history carries a blob matching the recorded digest,
        # and the plan-blob resolver is never invoked for the code family.
        code_repo = cr.build_scratch_repo(self)
        body = b"def f():\n    return 1\n"
        b0 = code_repo.commit_file("src/app.py", body, "base code")
        code_close = code_repo.commit_allow_empty("round 1 close")
        code_repo.append_seal_entry("acme-src", 1, "src/app.py", b0,
                                    hx(body), code_close,
                                    reviewed=(b0, b0, hx(body)))
        code_orphan = orphan_commit(code_repo)
        code_repo.write_seal_entry("acme-src", 1, "src/app.py", b0,
                                   hx(body), code_orphan,
                                   reviewed=(b0, b0, hx(body)),
                                   message="seal: orphan code close")
        with mock.patch.object(cr, "resolve_landed_anchor") as scan:
            ok, msg = cr.verify_corrections(
                code_repo.root, "src/app.py", cr.FAMILY_CODE, 1, hx(body),
                [], slug="acme-src")
        self.assertFalse(ok)
        assert_refusal(self, msg, "anchor", "round-close commit",
                       "not an ancestor of HEAD")
        scan.assert_not_called()

    def test_resolution_scan_caps_history(self):
        self.assertEqual(cr.LANDED_ANCHOR_SCAN_LIMIT, 400)
        repo = cr.build_scratch_repo(self)
        start = repo.commit_file(PLAN_REL, D1, "seed plan")
        close = repo.commit_allow_empty("round 1 close")
        entry_commit = repo.append_seal_entry(PLAN_SLUG, 1, PLAN_REL, start,
                                              hx(D1), close)
        repo.commit_file(PLAN_REL, D2,
                         "move the bytes off the sealed digest")
        for index in range(401):
            repo.commit_allow_empty("filler %d" % index)
        # 401 first-parent candidates at or past the move commit: the scan
        # enumerates at most 400 commits and reports a plain no-match even
        # though the sealed bytes sit just beyond the cap.
        anchor, scan_error = cr.resolve_landed_anchor(
            repo.root, PLAN_REL, hx(D1), repo.head())
        self.assertIsNone(scan_error)
        self.assertIsNone(anchor)
        # The bound is the cap, not the bytes: a larger limit reaches the
        # newest sealed-bytes carrier.
        beyond, _beyond_error = cr.resolve_landed_anchor(
            repo.root, PLAN_REL, hx(D1), repo.head(),
            limit=cr.LANDED_ANCHOR_SCAN_LIMIT + 10)
        self.assertEqual(beyond, entry_commit)

    def test_resolution_scan_includes_candidate_400(self):
        repo = cr.build_scratch_repo(self)
        start = repo.commit_file(PLAN_REL, D1, "seed plan")
        repo.commit_file(PLAN_REL, D2, "move the bytes off the sealed "
                                        "digest")
        for index in range(398):
            repo.commit_allow_empty("filler %d" % index)
        # Candidate positions from HEAD: 398 fillers, the D2 move (399),
        # the sealed D1 seed at candidate 400 exactly.
        anchor, scan_error = cr.resolve_landed_anchor(
            repo.root, PLAN_REL, hx(D1), repo.head())
        self.assertIsNone(scan_error)
        self.assertEqual(anchor, start)

    def test_resolution_scan_plumbing_failure_refuses(self):
        # A failing first-parent enumeration is a distinct plumbing
        # refusal, never a no-match pass.
        repo, c = plan_fixture(self)
        orphan = orphan_commit(repo)
        repo.write_seal_entry(PLAN_SLUG, 1, PLAN_REL, orphan, hx(D1),
                              c["close"], message="seal: orphan start")
        real_git_text = cr.git_text

        def failing_rev_list(repo_arg, *args):
            if args and args[0] == "rev-list":
                return None
            return real_git_text(repo_arg, *args)

        with mock.patch.object(cr, "git_text",
                               side_effect=failing_rev_list):
            ok, msg = vplan(repo, [], hx(D1), D1)
        self.assertFalse(ok)
        assert_refusal(self, msg, "anchor",
                       "enumerating first-parent history")

    def test_candidate_read_failure_refuses_without_older_match(self):
        # A candidate whose ls-tree names the path but whose blob read
        # fails refuses the scan at that candidate; the matching HEAD
        # bytes are never accepted through a failed read.
        repo = cr.build_scratch_repo(self)
        repo.commit_file(PLAN_REL, D1, "seed plan")
        hop = repo.commit_file(PLAN_REL, D2, "move to D2")
        orphan = orphan_commit(repo)
        repo.write_seal_entry(PLAN_SLUG, 1, PLAN_REL, orphan, hx(D2), hop,
                              message="seal: orphan with hop digest")
        real_git_bytes = cr.git_bytes

        def failing_blob(repo_arg, *args):
            if args and args[0] == "cat-file":
                return None
            return real_git_bytes(repo_arg, *args)

        with mock.patch.object(cr, "git_bytes", side_effect=failing_blob):
            ok, msg = vplan(repo, [], hx(D2), D2)
        self.assertFalse(ok)
        assert_refusal(self, msg, "anchor", "reading the blob")

    def test_verification_context_uses_one_pinned_head(self):
        # Every HEAD-dependent leg receives the same resolved snapshot id:
        # the anchor ancestry checks, the plan-family evidence ancestry,
        # the resolver scan, and the code-family terminal comparison.
        repo, c = plan_fixture(self)
        orphan_a = orphan_commit(repo, message="orphan a")
        orphan_b = orphan_commit(repo, message="orphan b")
        repo.write_seal_entry(PLAN_SLUG, 1, PLAN_REL, orphan_a, hx(D1),
                              orphan_b, message="seal: pinned head")
        landing_tree = repo.git(
            "rev-parse", "%s^{tree}" % c["start"]).stdout.strip()
        hop_date = int(repo.git(
            "show", "-s", "--format=%ct", c["hop1"]).stdout.split()[0])
        # The landing predates the hop evidence it anchors (an honest
        # round's hop commits ride after its close), so the dating leg
        # sees the honest order over the resolved pair.
        landing = repo.git(
            "commit-tree", landing_tree, "-p", "HEAD", "-m",
            "landing carrying the sealed bytes",
            date=hop_date - 30).stdout.strip()
        seen = []
        real_is_ancestor = cr.is_ancestor
        real_scan = cr.resolve_landed_anchor

        def spy_ancestor(repo_arg, ancestor, descendant="HEAD"):
            seen.append(("ancestor", ancestor, descendant))
            return real_is_ancestor(repo_arg, ancestor, descendant)

        def spy_scan(repo_arg, artifact_path, digest, head_sha,
                     limit=cr.LANDED_ANCHOR_SCAN_LIMIT):
            seen.append(("scan", artifact_path, head_sha))
            return real_scan(repo_arg, artifact_path, digest, head_sha,
                             limit)

        with mock.patch.object(cr, "is_ancestor", side_effect=spy_ancestor), \
                mock.patch.object(cr, "resolve_landed_anchor",
                                  side_effect=spy_scan):
            ok, msg = vplan(repo, [plan_row(hx(D1), hx(D2), c["hop1"])],
                            hx(D1), D2, head=landing)
        self.assertTrue(ok, msg)
        self.assertIn("squash-orphaned seal anchors resolved through "
                      "HEAD-ancestor %s" % landing, msg)
        self.assertTrue(seen)
        for kind, _subject, descendant in seen:
            self.assertEqual(descendant, landing, kind)
        # Code family: the anchor ancestry legs pin to the supplied head,
        # the row-local after-base check keeps the row's own after head,
        # and the terminal comparison runs against the same pinned id.
        code_repo = cr.build_scratch_repo(self)
        b0 = code_repo.commit_file("src/app.py", "def f():\n    return 1\n",
                                   "base")
        b1 = code_repo.commit_file("src/app.py", "def f():\n    return 2\n",
                                   "one")
        close = code_repo.commit_allow_empty("round close")
        d0 = hx(code_repo.git("diff", "%s...%s" % (b0, b1)).stdout.encode())
        code_repo.append_seal_entry("acme-src", 1, "src/app.py", b1, d0,
                                    close, reviewed=(b0, b1, d0))
        m2 = code_repo.commit_file("src/app.py", "def f():\n    return 3\n",
                                   "two")
        b3 = code_repo.commit_file("src/app.py", "def g():\n    return 3\n",
                                   "three")
        d1 = hx(code_repo.git("diff", "%s...%s" % (b1, m2)).stdout.encode())
        d2 = hx(code_repo.git("diff", "%s...%s" % (m2, b3)).stdout.encode())
        code_seen = []

        def code_spy(repo_arg, ancestor, descendant="HEAD"):
            code_seen.append((ancestor, descendant))
            return real_is_ancestor(repo_arg, ancestor, descendant)

        rows = [code_row(b0, b1, b1, m2, d0, d1),
                code_row(m2, m2, m2, b3, d1, d2)]
        with mock.patch.object(cr, "is_ancestor", side_effect=code_spy):
            ok, msg = cr.verify_corrections(
                code_repo.root, "src/app.py", cr.FAMILY_CODE, 1, d0, rows,
                certified_range={"base": b0, "head": b1}, slug="acme-src",
                head=b3)
        self.assertTrue(ok, msg)
        self.assertIn((close, b3), code_seen)
        self.assertIn((b1, b3), code_seen)
        self.assertIn((b1, m2), code_seen)
        self.assertNotIn("HEAD", [d for _a, d in code_seen])
        # The terminal comparison consumes the pinned id: the same chain
        # under a different explicit head refuses as a terminal mismatch
        # even though that chain's own after head is the repository HEAD.
        ok, msg = cr.verify_corrections(
            code_repo.root, "src/app.py", cr.FAMILY_CODE, 1, d0, rows,
            certified_range={"base": b0, "head": b1}, slug="acme-src",
            head=close)
        self.assertFalse(ok)
        assert_refusal(self, msg, "terminal", "branch head")

    def test_present_non_commit_and_ambiguous_probe_refuse(self):
        # A present non-commit object (a tree id in an anchor field) is an
        # unclassifiable anchor: refusal without any scan.
        repo, c = plan_fixture(self)
        tree_id = repo.git(
            "rev-parse", "%s^{tree}" % c["start"]).stdout.strip()
        repo.write_seal_entry(PLAN_SLUG, 1, PLAN_REL, tree_id, hx(D1),
                              c["close"], message="seal: tree anchor")
        with mock.patch.object(cr, "resolve_landed_anchor") as scan:
            ok, msg = vplan(repo, [], hx(D1), D1)
        self.assertFalse(ok)
        assert_refusal(self, msg, "anchor", "Git cannot classify commit "
                       "object", tree_id)
        scan.assert_not_called()
        # An injected ambiguous commit-object probe failure is an error,
        # never a conclusive absence, and never reaches the scan.
        repo2, c2 = plan_fixture(self)
        orphan = orphan_commit(repo2)
        repo2.write_seal_entry(PLAN_SLUG, 1, PLAN_REL, c2["start"], hx(D1),
                               orphan, message="seal: orphan close")
        real_run_git = cr.run_git

        def ambiguous_probe(repo_arg, *args):
            if args[:2] == ("cat-file", "-e"):
                return subprocess.CompletedProcess(["git"], 128)
            return real_run_git(repo_arg, *args)

        with mock.patch.object(cr, "run_git", side_effect=ambiguous_probe):
            with mock.patch.object(cr, "resolve_landed_anchor") as scan:
                ok, msg = vplan(repo2, [], hx(D1), D1)
        self.assertFalse(ok)
        assert_refusal(self, msg, "anchor", "Git cannot classify commit "
                       "object")
        scan.assert_not_called()
        # A full-format absent commit id is conclusively missing, and only
        # that confirmed absence reaches the byte-identity scan.
        absent = "a" * 40
        self.assertEqual(cr.commit_object_status(repo2.root, absent),
                         "missing")
        repo3, c3 = plan_fixture(self)
        repo3.write_seal_entry(PLAN_SLUG, 1, PLAN_REL, c3["start"],
                               hx(D3), absent, message="seal: absent close")
        ok, msg = vplan(repo3, [], hx(D3), D3)
        self.assertFalse(ok)
        assert_refusal(self, msg, "anchor", "round-close commit",
                       "no first-parent ancestor")

    def test_squash_orphaned_anchors_resolve_by_byte_identity(self):
        repo, c = plan_fixture(self)
        orphan_a = orphan_commit(repo, message="orphan a")
        orphan_b = orphan_commit(repo, message="orphan b")
        self.assertNotEqual(orphan_a, orphan_b)
        repo.write_seal_entry(PLAN_SLUG, 1, PLAN_REL, orphan_a, hx(D1),
                              orphan_b, message="seal: squash orphaned")
        # The hop row verifies and names the resolved HEAD ancestor: the
        # most recent first-parent commit carrying D1 at the artifact path
        # before the D2 hop is the fixture's seal-entry commit.
        ok, msg = vplan(repo, [plan_row(hx(D1), hx(D2), c["hop1"])],
                        hx(D1), D2)
        self.assertTrue(ok, msg)
        self.assertIn("squash-orphaned seal anchors resolved through "
                      "HEAD-ancestor %s" % c["entry"], msg)
        # The zero-hop clean shape verifies over the same seal.
        ok, msg = vplan(repo, [], hx(D1), D1)
        self.assertTrue(ok, msg)
        self.assertIn("HEAD-ancestor %s" % c["entry"], msg)

    def test_single_orphaned_round_start_resolves_before_reachable_close(self):
        repo = cr.build_scratch_repo(self)
        repo.commit_file(PLAN_REL, D1, "seed plan")
        repo.commit_file(PLAN_REL, D2, "move off the sealed bytes")
        close = repo.commit_allow_empty("round close")
        repo.commit_file(PLAN_REL, D1, "the sealed bytes return")
        orphan = orphan_commit(repo, message="orphan start")
        repo.write_seal_entry(PLAN_SLUG, 1, PLAN_REL, orphan, hx(D1), close,
                              message="seal: orphan start")
        # The resolver lands on the first D1-carrying commit after the
        # reachable close, and the existing ordering check refuses the
        # resolved pair.
        ok, msg = vplan(repo, [], hx(D1), D1)
        self.assertFalse(ok)
        assert_refusal(self, msg, "seal", "round-start commit postdates",
                       "round-close")

    def test_code_family_after_base_ancestry_regression(self):
        # The code-family after_base to after_head ancestry relation stays
        # row-local: an intermediate after head that does not descend from
        # its after base refuses regardless of the pinned verification
        # head, and the honest chain still verifies.
        repo = cr.build_scratch_repo(self)
        b0 = repo.commit_file("src/app.py", "def f():\n    return 1\n",
                              "base")
        b1 = repo.commit_file("src/app.py", "def f():\n    return 2\n",
                              "one")
        close = repo.commit_allow_empty("round close")
        d0 = hx(repo.git("diff", "%s...%s" % (b0, b1)).stdout.encode())
        repo.append_seal_entry("acme-src", 1, "src/app.py", b1, d0, close,
                               reviewed=(b0, b1, d0))
        b2 = repo.commit_file("src/app.py", "def f():\n    return 3\n",
                              "two")
        d1 = hx(repo.git("diff", "%s...%s" % (b1, b2)).stdout.encode())
        broken = code_row(b0, b1, b2, b1, d0, d1)
        ok, msg = cr.verify_corrections(
            repo.root, "src/app.py", cr.FAMILY_CODE, 1, d0, [broken],
            certified_range={"base": b0, "head": b1}, slug="acme-src",
            head=b2)
        self.assertFalse(ok)
        assert_refusal(self, msg, "linkage",
                       "after head does not descend")
        good = code_row(b0, b1, b1, b2, d0, d1)
        ok, msg = cr.verify_corrections(
            repo.root, "src/app.py", cr.FAMILY_CODE, 1, d0, [good],
            certified_range={"base": b0, "head": b1}, slug="acme-src",
            head=b2)
        self.assertTrue(ok, msg)


class ChainLegsTest(unittest.TestCase):
    def test_hop_digests_bound_to_bytes(self):
        repo, c = plan_fixture(self)
        row = plan_row(hx(D1), hx(D2), c["hop1"])
        ok, msg = vplan(repo, [row], hx(D1), D2)
        self.assertTrue(ok, msg)
        # Near-miss: the evidence bytes are the typo-only D2 but the row
        # declares a semantic D3 digest; the binding must refuse.
        ok, msg = vplan(repo, [plan_row(hx(D1), hx(D3), c["hop1"])],
                        hx(D1), D2)
        self.assertFalse(ok)
        assert_refusal(self, msg, "binding", "after digest")
        # Hop 0 binds to the seal round-start blob, not to declared values.
        ok, msg = vplan(repo, [plan_row(hx(D3), hx(D2), c["hop1"])],
                        hx(D3), D2)
        self.assertFalse(ok)
        assert_refusal(self, msg, "binding", "before digest")
        # The evidence commit must commit the artifact path.
        other = repo.commit_file("notes.txt", b"unrelated\n", "other file")
        ok, msg = vplan(repo, [plan_row(hx(D1), hx(D2), other)], hx(D1), D2)
        self.assertFalse(ok)
        assert_refusal(self, msg, "binding", "artifact path")
        # The evidence commit must be an ancestor of HEAD.
        orphan = orphan_commit(repo)
        ok, msg = vplan(repo, [plan_row(hx(D1), hx(D2), orphan)], hx(D1), D2)
        self.assertFalse(ok)
        assert_refusal(self, msg, "binding", "ancestor")
        # The classifier hook: a non-exempt verdict refuses the
        # classification leg; an empty verdict passes.
        ok, msg = vplan(repo, [row], hx(D1), D2,
                        classify=lambda old, new: ["hunk 0 unclassified"])
        self.assertFalse(ok)
        assert_refusal(self, msg, "classify", "hunk 0")
        ok, msg = vplan(repo, [row], hx(D1), D2, classify=lambda old,
                        new: [])
        self.assertTrue(ok, msg)

    def test_linkage_terminal_and_multi_hop(self):
        repo, c = plan_fixture(self)
        hop2 = repo.commit_file(PLAN_REL, D3, "second correction")
        rows = [plan_row(hx(D1), hx(D2), c["hop1"]),
                plan_row(hx(D2), hx(D3), hop2)]
        ok, msg = vplan(repo, rows, hx(D1), D3)
        self.assertTrue(ok, msg)
        # Breaking the declared linkage refuses naming that leg.
        broken = [rows[0], plan_row(hx(D1), hx(D3), hop2)]
        ok, msg = vplan(repo, broken, hx(D1), D3)
        self.assertFalse(ok)
        assert_refusal(self, msg, "linkage")
        # Breaking the terminal equality refuses naming that leg.
        ok, msg = vplan(repo, rows, hx(D1), D2)
        self.assertFalse(ok)
        assert_refusal(self, msg, "terminal", "current bytes")
        # A declared record carrying zero hops is the vacuous zero-hop
        # refusal, never a pass.
        ok, msg = vplan(repo, [], hx(D1), D2, record_declared=True)
        self.assertFalse(ok)
        assert_refusal(self, msg, "vacuous", "zero hops")


class SealLegTest(unittest.TestCase):
    def code_fixture(self):
        repo = cr.build_scratch_repo(self)
        b0 = repo.commit_file("src/app.py", "def f():\n    return 1\n",
                              "base code")
        b1 = repo.commit_file("src/app.py", "def f():\n    return 2\n",
                              "change code")
        close = repo.commit_allow_empty("round close")
        diff0 = repo.git("diff", "%s...%s" % (b0, b1)).stdout
        entry = repo.append_seal_entry(
            "acme-src", 1, "src/app.py", b1, hx(diff0.encode()), close,
            reviewed=(b0, b1, hx(diff0.encode())))
        b2 = repo.commit_file("src/app.py",
                              "def f():\n    # note\n    return 2\n",
                              "comment fix")
        diff1 = repo.git("diff", "%s...%s" % (b1, b2)).stdout
        return repo, {"b0": b0, "b1": b1, "close": close, "entry": entry,
                      "b2": b2, "diff0": hx(diff0.encode()),
                      "diff1": hx(diff1.encode())}

    def test_seal_integrity(self):
        # Append-only per-round entries pass: the code chain re-binds
        # through the seal's certified range.
        repo, cf = self.code_fixture()
        row = code_row(cf["b0"], cf["b1"], cf["b1"], cf["b2"],
                       cf["diff0"], cf["diff1"])
        ok, msg = cr.verify_corrections(
            repo.root, "src/app.py", cr.FAMILY_CODE, 1, cf["diff0"], [row],
            certified_range={"base": cf["b0"], "head": cf["b1"]},
            slug="acme-src")
        self.assertTrue(ok, msg)
        # A sidecar range differing from the seal's certified range
        # refuses naming the seal leg.
        ok, msg = cr.verify_corrections(
            repo.root, "src/app.py", cr.FAMILY_CODE, 1, cf["diff0"], [row],
            certified_range={"base": cf["b0"], "head": cf["b0"]},
            slug="acme-src")
        self.assertFalse(ok)
        assert_refusal(self, msg, "seal", "certified range")
        # A hop commit dated before its seal entry's round-close commit
        # refuses, even though the history order is honest; the dating leg
        # precedes the digest binding, so the hop's content is arbitrary.
        repo2, c2 = plan_fixture(self)
        early_hop = repo2.commit_file(PLAN_REL, D1, "backdated fix",
                                      date=1)
        ok, msg = vplan(repo2, [plan_row(hx(D1), hx(D2), early_hop)],
                        hx(D1), D2)
        self.assertFalse(ok)
        assert_refusal(self, msg, "seal", "round-close commit")
        # A digest-field edit of the on-disk seal entry is still caught by
        # the anchor leg's re-hash against the current file (the
        # committed-history witness retired with the 2026-10-11 seal-home
        # re-point; non-digest field edits are out of scope under the
        # untracked posture).
        repo3, c3 = plan_fixture(self)
        seal_rel = cr.seal_relpath(PLAN_REL, PLAN_SLUG)
        text = (repo3.root / seal_rel).read_text()
        text = text.replace("round_start_digest: %s" % hx(D1),
                            "round_start_digest: %s" % hx(D3))
        repo3.write_file(seal_rel, text)
        repo3.commit_all("edit round 1 entry")
        ok, msg = vplan(repo3, [plan_row(hx(D1), hx(D2), c3["hop1"])],
                        hx(D1), D2)
        self.assertFalse(ok)
        assert_refusal(self, msg, "anchor", "round-start digest")
        # Append-only plan rounds pass: round 2 anchors at the hop commit
        # and verifies clean, while round 1 still verifies.
        repo4, c4 = plan_fixture(self)
        repo4.commit_allow_empty("round 2 close")
        repo4.append_seal_entry(PLAN_SLUG, 2, PLAN_REL, c4["hop1"], hx(D2),
                                repo4.head())
        ok, msg = vplan(repo4, [plan_row(hx(D1), hx(D2), c4["hop1"])],
                        hx(D1), D2)
        self.assertTrue(ok, msg)
        ok, msg = cr.verify_corrections(
            repo4.root, PLAN_REL, cr.FAMILY_PLAN, 2, hx(D2), [],
            current_bytes=D2)
        self.assertTrue(ok, msg)


class SealDatingLegTest(unittest.TestCase):
    """The consistent seal-move tamper (r1 fold): rewriting the latest
    round's seal entry to re-point round_start_commit at a later commit
    and re-declaring the moved round-start digest re-binds arbitrary
    semantic edits with zero corrections rows, because the anchor legs
    never ordered the entry's own commits. The seal-integrity dating leg
    refuses the move (an honest round's round-start commit never
    postdates its round-close commit), and honest rounds still verify."""

    def _consistent_move(self, repo, c, moved_bytes):
        """Rewrite the round-1 entry consistently: round_start_commit
        moved to a later commit carrying the moved bytes, the moved
        round-start digest recorded, the round-close commit untouched.
        When the tree already holds the moved bytes the attacker commit
        is an empty one: the plan blob at the commit is the moved bytes
        and only the commit date moves."""
        head_blob = cr.blob_bytes(repo.root, repo.head(), PLAN_REL)
        if head_blob == moved_bytes:
            moved_commit = repo.commit_allow_empty("attacker commit")
        else:
            moved_commit = repo.commit_file(PLAN_REL, moved_bytes,
                                            "attacker semantic edit")
        repo.write_seal_entry(PLAN_SLUG, 1, PLAN_REL, moved_commit,
                              hx(moved_bytes), c["close"],
                              message="seal: consistent move")
        return moved_commit

    def test_consistent_move_refuses_on_the_dating_leg(self):
        repo, c = plan_fixture(self)
        # The semantic shape: the attacker edits the plan body itself.
        self._consistent_move(repo, c, D3)
        ok, msg = vplan(repo, [], hx(D3), D3)
        self.assertFalse(ok)
        assert_refusal(self, msg, "seal", "round-start commit postdates")
        # The digest-only shape: a later empty attacker commit whose plan
        # blob still carries the hop's bytes (the task's D2 move witness).
        repo2, c2 = plan_fixture(self)
        self._consistent_move(repo2, c2, D2)
        ok, msg = vplan(repo2, [], hx(D2), D2)
        self.assertFalse(ok)
        assert_refusal(self, msg, "seal", "round-start commit postdates")

    def test_honest_round_start_equal_close_still_verifies(self):
        # The dating leg orders start <= close: an honest round whose
        # round-start commit is also its round-close commit keeps the
        # zero-hop clean shape.
        repo = cr.build_scratch_repo(self)
        start = repo.commit_file(PLAN_REL, D1, "seed plan")
        repo.append_seal_entry(PLAN_SLUG, 1, PLAN_REL, start, hx(D1),
                               start)
        ok, msg = vplan(repo, [], hx(D1), D1)
        self.assertTrue(ok, msg)


class SlugShapeTest(unittest.TestCase):
    """The seal slug shape gate (r1 fix fold): the artifact slug is
    interpolated into the seal relpath, so a slug outside the safe kebab
    shape refuses as a schema error before any path is derived, and the
    refusal never echoes the slug (echoing would leak a banned routing
    literal into a corrections reason quoting the seal path)."""

    UNSAFE = ("../evil", "a/b", "..", ".", "a.b", "a b", "-lead",
              "trail-", "UPPER", "under_score", "")

    def test_benign_slug_verifies_end_to_end(self):
        self.assertIsNone(cr.slug_shape_reason(PLAN_SLUG))
        self.assertEqual(
            cr.seal_relpath(PLAN_REL, PLAN_SLUG),
            ".ai-playbook/review-certs/%s.md" % PLAN_SLUG)
        repo, c = plan_fixture(self)
        ok, msg = cr.verify_corrections(
            repo.root, PLAN_REL, cr.FAMILY_PLAN, 1, hx(D1), [],
            current_bytes=D1, slug=PLAN_SLUG)
        self.assertTrue(ok, msg)
        # A missing slug keeps the artifact-stem fallback (no slug in play).
        self.assertEqual(
            cr.seal_relpath(PLAN_REL, None),
            ".ai-playbook/review-certs/%s.md" % Path(PLAN_REL).stem)

    def test_banned_literal_slug_refuses_without_echo(self):
        # Every current banned literal carries an underscore, so it fails
        # the kebab shape too; the reserved-substring clause precedes the
        # shape clause, so a slug carrying one is named as exactly that.
        for bad in ("source_digest-evil", "x-source_kind-y",
                    "source_digest", "prefix-source_kind-suffix"):
            reason = cr.slug_shape_reason(bad)
            self.assertIsNotNone(reason)
            self.assertTrue(reason.startswith(cr.MARKER_PREFIX), reason)
            self.assertIn("slug", reason)
            self.assertIn("kebab", reason)
            self.assertIn("reserved routing substring", reason)
            for banned in cr.BANNED_LITERALS:
                self.assertNotIn(banned, reason)
            self.assertNotIn(bad, reason)
        # A literal-free slug violating only the shape names the shape
        # clause.
        self.assertIn("fails the shape", cr.slug_shape_reason("../evil"))
        self.assertIn("fails the shape", cr.slug_shape_reason("dotted.name"))

    def test_path_unsafe_slugs_refuse(self):
        for bad in self.UNSAFE:
            reason = cr.slug_shape_reason(bad)
            self.assertIsNotNone(reason, repr(bad))
            self.assertTrue(reason.startswith(cr.MARKER_PREFIX), reason)
            self.assertIn("slug", reason)

    def test_seal_path_derivation_refuses_unsafe_slug(self):
        for bad in ("source_digest-evil", "../evil"):
            try:
                cr.seal_relpath(PLAN_REL, bad)
                self.fail("expected CorrectionsSchemaError for %r" % bad)
            except cr.CorrectionsSchemaError as exc:
                msg = str(exc)
                self.assertTrue(msg.startswith(cr.MARKER_PREFIX), msg)
                for banned in cr.BANNED_LITERALS:
                    self.assertNotIn(banned, msg)

    def test_verify_refuses_unsafe_slug_as_schema_leg(self):
        repo, c = plan_fixture(self)
        for bad in ("source_digest-evil", "../evil"):
            ok, msg = cr.verify_corrections(
                repo.root, PLAN_REL, cr.FAMILY_PLAN, 1, hx(D1), [],
                current_bytes=D1, slug=bad)
            self.assertFalse(ok)
            assert_refusal(self, msg, "schema", "slug")
            self.assertNotIn(bad, msg)
            self.assertNotIn("anchor leg", msg)


ACK_RECEIPT = {
    "directive": "re-bind the exempt delta without a fresh round",
    "authorization_witness": "PLACEHOLDER",
    "classifier_gap_row":
        "docs/history/backlog/2026-10-04-typography-bucket.md",
}


def witness_lines(before, after, writer="scheduler-turn-writer",
                  direction=ACK_RECEIPT["directive"]):
    return [
        "turn: authorize-rebind",
        "writer: %s" % writer,
        "operator_direction: %s" % direction,
        "artifact: %s" % PLAN_REL,
        "before_digest: %s" % before,
        "after_digest: %s" % after,
    ]


class AckReceiptTest(unittest.TestCase):
    def setUp(self):
        self.repo, self.c = plan_fixture(self)
        self.witness_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.witness_dir.cleanup)
        self.witness_path = str(Path(self.witness_dir.name) / "turn.record")
        Path(self.witness_path).write_text(
            "\n".join(witness_lines(hx(D1), hx(D2))) + "\n")
        self.gap_rel = ACK_RECEIPT["classifier_gap_row"]
        self.repo.write_file(
            self.gap_rel,
            "# classifier gap\n\nproposal: a typography bucket covering "
            "hunk digest %s\n" % hx(b"hunk-bytes"))
        self.repo.commit_all("file gap row")
        receipt = dict(ACK_RECEIPT)
        receipt["authorization_witness"] = self.witness_path
        self.row = plan_row(hx(D1), hx(D2), self.c["hop1"],
                            kind=cr.KIND_OPERATOR_ACKED, receipt=receipt)

    def resolve(self, row=None, witness=None):
        return cr.resolve_ack_receipt(
            row or self.row, witness or self.witness_path,
            self.repo.root, PLAN_REL)

    def test_subject_bound_resolution(self):
        # resolve_ack_receipt itself keeps resolving an injected turn
        # record (the code family still routes through it); at the
        # verify level the plan family no longer does (Task 2 retirement,
        # pinned by StateAuthorizationTest), so a plan acked row beside a
        # caller-selected witness path refuses.
        ok, msg = self.resolve()
        self.assertTrue(ok, msg)
        ok, msg = vplan(self.repo, [self.row], hx(D1), D2,
                        witness_path=self.witness_path)
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt", "caller-selected witness path")
        # An unresolvable witness: the injected path does not exist.
        ok, msg = self.resolve(witness=str(
            Path(self.witness_dir.name) / "absent.record"))
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt", "unresolvable witness")
        # The receipt must name the resolved witness record.
        other = dict(self.row)
        other["receipt"] = dict(ACK_RECEIPT)
        other["receipt"]["authorization_witness"] = \
            "state/turns/other.record"
        ok, msg = self.resolve(row=other)
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt", "unresolvable witness")
        # A subject mismatch: the witness stops echoing the after digest.
        Path(self.witness_path).write_text(
            "\n".join(witness_lines(hx(D1), "f" * 64)) + "\n")
        ok, msg = self.resolve()
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt", "subject mismatch")
        Path(self.witness_path).write_text(
            "\n".join(witness_lines(hx(D1), hx(D2))) + "\n")
        # A turn record written by the recording session refuses.
        Path(self.witness_path).write_text(
            "\n".join(witness_lines(hx(D1), hx(D2),
                                    writer="session-a")) + "\n")
        ok, msg = self.resolve()
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt", "recording session")
        # A commit-trailer-only witness is not a turn record.
        Path(self.witness_path).write_text(
            "Acked-by: operator\nSigned-off-by: operator\n")
        ok, msg = self.resolve()
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt", "commit-trailer-only")
        Path(self.witness_path).write_text(
            "\n".join(witness_lines(hx(D1), hx(D2))) + "\n")
        # A dangling gap-row path refuses.
        dangling = dict(self.row)
        dangling["receipt"] = dict(ACK_RECEIPT)
        dangling["receipt"]["authorization_witness"] = self.witness_path
        dangling["receipt"]["classifier_gap_row"] = \
            "docs/history/backlog/absent-gap.md"
        ok, msg = self.resolve(row=dangling)
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt", "dangling")
        # A gap row without the quoted hunk digest refuses.
        self.repo.write_file(self.gap_rel,
                             "# classifier gap\n\nproposal: typography\n")
        self.repo.commit_all("empty gap row")
        ok, msg = self.resolve()
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt", "does not quote")

    def test_append_advisory_lock(self):
        record = self.repo.root / "record.json"
        record.write_text("{}")
        lock_path = cr.corrections_lock_path(self.repo.root, PLAN_SLUG)
        # A concurrent holder of the advisory lock refuses the append,
        # naming the concurrent-round possibility beside an unwitnessed
        # mutation.
        with open(lock_path, "a+") as held:
            fcntl.flock(held, fcntl.LOCK_EX)
            ok, msg = cr.append_corrections(
                record, [self.row], self.repo.root, PLAN_SLUG)
            self.assertFalse(ok)
            assert_refusal(self, msg, "append", "concurrent certification",
                           "mutation")
            fcntl.flock(held, fcntl.LOCK_UN)
        # A record changed underneath the lock (digest expectation stale)
        # refuses with the same naming discipline.
        ok, msg = cr.append_corrections(
            record, [self.row], self.repo.root, PLAN_SLUG,
            expect_sha256=cr.sha256_hex(b"different"))
        self.assertFalse(ok)
        assert_refusal(self, msg, "append", "concurrent certification",
                       "mutation")
        ok, new_sha = cr.append_corrections(
            record, [self.row], self.repo.root, PLAN_SLUG,
            expect_sha256=cr.sha256_hex(record.read_bytes()))
        self.assertTrue(ok, new_sha)
        self.assertEqual(new_sha, cr.sha256_hex(record.read_bytes()))
        self.assertEqual(len(cr.load_corrections(record)), 1)
        self.assertTrue(lock_path.name.endswith("%s.lock" % PLAN_SLUG))


# The fixed selector every plan-family operator-ack receipt must name
# (plan Terms: Operator-ack receipt); pinned against the module constant
# in AuthorSessionSchemaTest.
ACK_SELECTOR = ".ai-playbook/scheduler-state.json#correction_authorizations"
ACK_GAP_REL = "docs/history/backlog/2026-10-18-unclassified-gap.md"
ACK_WRITER = "sess-writer"
ACK_AUTHOR = "sess-author"


def ack_state_row(before, after, evidence,
                  directive="re-bind the unclassified delta"):
    """An operator-acked plan-family row whose receipt names the fixed
    state selector and which carries the emitting session's identity."""
    receipt = {
        "directive": directive,
        "authorization_witness": ACK_SELECTOR,
        "classifier_gap_row": ACK_GAP_REL,
    }
    row = plan_row(before, after, evidence, kind=cr.KIND_OPERATOR_ACKED,
                   receipt=receipt)
    row["author_session_id"] = ACK_AUTHOR
    return row


def ack_entry(row, **overrides):
    """The correction_authorizations entry binding the row digest and the
    exact row subject (plan Assumptions: the entry's carried fields)."""
    entry = {
        "row_digest": cr.correction_row_digest(row),
        "writer_session_id": ACK_WRITER,
        "operator_direction": row["receipt"]["directive"],
        "recorded_at": NOW,
        "author_session_id": row.get("author_session_id", ACK_AUTHOR),
        "artifact_path": PLAN_REL,
        "before_digest": row["before_digest"],
        "after_digest": row["after_digest"],
        "evidence_commit": row["evidence_commit"],
        "hunk_digests": [h["digest"] for h in row["hunks"]],
    }
    entry.update(overrides)
    return entry


def refuse_all(old_bytes, new_bytes):
    return ["hunk 0 unclassified"]


class RowDigestTest(unittest.TestCase):
    """The correction row identity (plan Terms): the lowercase SHA-256 of
    the canonical JSON encoding (sorted keys, compact separators) of the
    full row, excluding only receipt.authorization_witness so the fixed
    selector does not create a cycle."""

    def row(self):
        base = plan_row("a" * 64, "b" * 64, "c" * 40,
                        kind=cr.KIND_OPERATOR_ACKED,
                        receipt={"directive": "d",
                                 "authorization_witness": "witness-a",
                                 "classifier_gap_row": "g"})
        base["author_session_id"] = "sess"
        return base

    def test_excludes_only_the_authorization_witness(self):
        row = self.row()
        other = json.loads(json.dumps(row))
        other["receipt"]["authorization_witness"] = "witness-b"
        self.assertEqual(cr.correction_row_digest(row),
                         cr.correction_row_digest(other))
        for field, value in (("recorded_by", "someone-else"),
                             ("after_digest", "f" * 64)):
            changed = json.loads(json.dumps(row))
            changed[field] = value
            self.assertNotEqual(cr.correction_row_digest(row),
                                cr.correction_row_digest(changed),
                                field)
        changed = json.loads(json.dumps(row))
        changed["receipt"]["directive"] = "other"
        self.assertNotEqual(cr.correction_row_digest(row),
                            cr.correction_row_digest(changed))

    def test_canonical_encoding_and_shape(self):
        row = self.row()
        digest = cr.correction_row_digest(row)
        self.assertRegex(digest, r"^[0-9a-f]{64}$")
        trimmed = json.loads(json.dumps(row))
        trimmed["receipt"].pop("authorization_witness")
        canonical = json.dumps(trimmed, sort_keys=True,
                               separators=(",", ":"))
        self.assertEqual(digest, cr.sha256_hex(canonical.encode("utf-8")))

    def test_non_ascii_values_use_the_default_escaping(self):
        # The canonical encoding pins the stdlib default (ensure_ascii):
        # non-ASCII values ride \\uXXXX escapes, never raw UTF-8 bytes.
        row = self.row()
        row["recorded_by"] = "s\u00e9ance-ops"
        trimmed = json.loads(json.dumps(row))
        trimmed["receipt"].pop("authorization_witness")
        ascii_form = json.dumps(trimmed, sort_keys=True,
                                separators=(",", ":"), ensure_ascii=True)
        raw_form = json.dumps(trimmed, sort_keys=True,
                              separators=(",", ":"), ensure_ascii=False)
        self.assertNotEqual(ascii_form, raw_form)
        self.assertEqual(cr.correction_row_digest(row),
                         cr.sha256_hex(ascii_form.encode("utf-8")))
        self.assertNotEqual(cr.correction_row_digest(row),
                            cr.sha256_hex(raw_form.encode("utf-8")))


class AuthorSessionSchemaTest(unittest.TestCase):
    """author_session_id rides only operator-acked plan-family rows,
    absent-tolerated so archived rows re-validate unchanged."""

    def base(self, kind=cr.KIND_OPERATOR_ACKED):
        receipt = None
        if kind == cr.KIND_OPERATOR_ACKED:
            receipt = {"directive": "d",
                       "authorization_witness": ACK_SELECTOR,
                       "classifier_gap_row": "g"}
        return plan_row("a" * 64, "b" * 64, "c" * 40, kind=kind,
                        receipt=receipt)

    def test_acked_plan_row_records_the_author_session(self):
        row = self.base()
        row["author_session_id"] = "sess-1"
        self.assertIsNone(cr.row_schema_reason(row, cr.FAMILY_PLAN))
        self.assertIsNone(cr.row_schema_reason(row))

    def test_absent_key_stays_absent_tolerated(self):
        self.assertIsNone(cr.row_schema_reason(self.base(), cr.FAMILY_PLAN))

    def test_script_verified_and_code_rows_never_carry_it(self):
        script_row = self.base(cr.KIND_SCRIPT_VERIFIED)
        script_row["author_session_id"] = "sess-1"
        self.assertIn("unexpected key",
                      cr.row_schema_reason(script_row, cr.FAMILY_PLAN))
        code = code_row("a" * 40, "b" * 40, "b" * 40, "d" * 40,
                        "e" * 64, "f" * 64, kind=cr.KIND_OPERATOR_ACKED,
                        receipt={"directive": "d",
                                 "authorization_witness": "w",
                                 "classifier_gap_row": "g"})
        code["author_session_id"] = "sess-1"
        self.assertIn("unexpected key",
                      cr.row_schema_reason(code, cr.FAMILY_CODE))

    def test_whitespace_author_session_is_malformed(self):
        for value in ("", "   "):
            row = self.base()
            row["author_session_id"] = value
            reason = cr.row_schema_reason(row, cr.FAMILY_PLAN)
            self.assertIsNotNone(reason)
            self.assertIn("author_session_id", reason)

    def test_fixed_selector_constant(self):
        self.assertEqual(
            cr.ACK_STATE_SELECTOR,
            ".ai-playbook/scheduler-state.json#correction_authorizations")
        self.assertEqual(cr.SCHEDULER_STATE_RELPATH,
                         ".ai-playbook/scheduler-state.json")
        self.assertEqual(cr.CORRECTION_AUTHORIZATIONS_KEY,
                         "correction_authorizations")


class StateAuthorizationTest(unittest.TestCase):
    """The plan-family state-file authorization route: the receipt names
    the fixed selector, the primary state file carries the matching
    correction_authorizations entry, and a fully verified authorization
    lets that hop bypass only the classification leg."""

    def setUp(self):
        self.repo = cr.build_scratch_repo(self)
        start = self.repo.commit_file(PLAN_REL, D1, "seed plan")
        close = self.repo.commit_allow_empty("round 1 close")
        self.repo.append_seal_entry(PLAN_SLUG, 1, PLAN_REL, start, hx(D1),
                                    close)
        self.hop = self.repo.commit_file(PLAN_REL, D3, "unclassified fix")
        self.row = ack_state_row(hx(D1), hx(D3), self.hop)
        self.primary_dir = tempfile.TemporaryDirectory(prefix="ack-primary-")
        self.addCleanup(self.primary_dir.cleanup)
        self.primary = Path(self.primary_dir.name)
        self.write_entries([ack_entry(self.row)])
        self.repo.write_file(
            ACK_GAP_REL,
            "# classifier gap\n\nhunk digest %s\n"
            % self.row["hunks"][0]["digest"])
        self.repo.commit_all("file the classifier gap row")

    def write_entries(self, entries, doc=None):
        state_dir = self.primary / ".ai-playbook"
        state_dir.mkdir(parents=True, exist_ok=True)
        payload = {"correction_authorizations": entries} \
            if doc is None else doc
        (state_dir / "scheduler-state.json").write_text(json.dumps(payload))

    def write_raw_state(self, text):
        state_dir = self.primary / ".ai-playbook"
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "scheduler-state.json").write_text(text)

    def verify(self, rows=None, classify=None, **kw):
        return cr.verify_corrections(
            self.repo.root, PLAN_REL, cr.FAMILY_PLAN, 1, hx(D1),
            [self.row] if rows is None else rows, current_bytes=D3,
            classify=classify, primary_checkout=str(self.primary), **kw)

    def test_valid_operator_acked_hop_bypasses_only_classification(self):
        # The hop's delta is unclassified; the verified state authorization
        # is the only reason the chain verifies.
        ok, msg = self.verify(classify=refuse_all)
        self.assertTrue(ok, msg)
        self.assertIn("chain verified", msg)

    def test_without_state_mode_the_classify_leg_still_refuses(self):
        ok, msg = cr.verify_corrections(
            self.repo.root, PLAN_REL, cr.FAMILY_PLAN, 1, hx(D1),
            [self.row], current_bytes=D3, classify=refuse_all)
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt", "no witness record path")

    def test_legacy_turn_record_route_is_retired_for_plan_rows(self):
        # End state (corrections-chain-operator-ack plan, Task 2): every
        # production consumer resolves the primary checkout and passes it
        # in, so a plan-family acked row without one refuses through the
        # named receipt legs: a caller-selected witness path never selects
        # authority, and its absence stays the missing-witness refusal.
        # The code family keeps the turn-record resolution (pinned by
        # test_code_family_receipt_and_classify_unchanged).
        witness_dir = tempfile.TemporaryDirectory(prefix="ack-witness-")
        self.addCleanup(witness_dir.cleanup)
        witness_path = str(Path(witness_dir.name) / "turn.record")
        Path(witness_path).write_text(
            "\n".join(witness_lines(hx(D1), hx(D3))) + "\n")
        legacy_row = plan_row(hx(D1), hx(D3), self.hop,
                              kind=cr.KIND_OPERATOR_ACKED,
                              receipt={
                                  "directive": ACK_RECEIPT["directive"],
                                  "authorization_witness": witness_path,
                                  "classifier_gap_row": ACK_GAP_REL})
        ok, msg = cr.verify_corrections(
            self.repo.root, PLAN_REL, cr.FAMILY_PLAN, 1, hx(D1),
            [legacy_row], current_bytes=D3, witness_path=witness_path,
            classify=refuse_all)
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt", "caller-selected witness path")
        ok, msg = cr.verify_corrections(
            self.repo.root, PLAN_REL, cr.FAMILY_PLAN, 1, hx(D1),
            [legacy_row], current_bytes=D3, classify=refuse_all)
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt", "no witness record path")

    def test_missing_witness_shapes_refuse(self):
        for entries, doc in (([], None), (None, {})):
            self.write_entries(entries or [], doc=doc)
            ok, msg = self.verify()
            self.assertFalse(ok)
            assert_refusal(self, msg, "receipt",
                           "no correction_authorizations entry")
        empty_dir = tempfile.TemporaryDirectory(prefix="ack-empty-primary-")
        self.addCleanup(empty_dir.cleanup)
        ok, msg = cr.verify_corrections(
            self.repo.root, PLAN_REL, cr.FAMILY_PLAN, 1, hx(D1),
            [self.row], current_bytes=D3,
            primary_checkout=empty_dir.name)
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt", "unresolvable witness",
                       "unreadable")
        self.write_raw_state("not json {")
        ok, msg = self.verify()
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt", "unresolvable witness",
                       "not decodable JSON")
        self.write_entries(None, doc={"correction_authorizations": "junk"})
        ok, msg = self.verify()
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt", "is not an array")

    def test_undecodable_state_bytes_refuse(self):
        # Invalid UTF-8 in the state file is a named refusal, never an
        # escaping decode crash.
        state_dir = self.primary / ".ai-playbook"
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "scheduler-state.json").write_bytes(b"\xff\xfe{}")
        ok, msg = self.verify()
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt", "unresolvable witness",
                       "unreadable")

    def test_changed_row_digest_refuses(self):
        self.write_entries([ack_entry(self.row, row_digest="a" * 64)])
        ok, msg = self.verify()
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt",
                       "no correction_authorizations entry")

    def test_malformed_row_digest_shape_refuses(self):
        # A shape-malformed row digest (not hex64) is malformed state, not
        # a silent non-match: the entry hits the named malformed refusal
        # instead of the missing-witness one (briefing item c).
        entry = ack_entry(self.row)
        entry["row_digest"] = "witness-shape-not-hex"
        self.write_entries([entry])
        ok, msg = self.verify()
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt",
                       "malformed correction_authorizations entry",
                       "row_digest is not a hex64 digest")

    def test_non_dict_array_member_refuses(self):
        # A non-dict array member is malformed state, never a silent
        # non-match: the pre-scan refuses through the named malformed leg
        # instead of letting the member fall through to the
        # missing-witness refusal.
        self.write_entries(["bare-string-member"])
        ok, msg = self.verify()
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt",
                       "malformed correction_authorizations entry",
                       "not a JSON object")
        # The shared selector keeps filtering dicts for matching; the
        # shape refusal for non-dict members belongs to the pre-scan.
        digest = cr.correction_row_digest(self.row)
        self.assertEqual(cr.entries_matching_row_digest(
            ["bare-string-member", ack_entry(self.row)], digest),
            [ack_entry(self.row)])

    def test_entry_reason_hex64_leg_refuses_directly(self):
        # Direct witness for the hex64 leg inside
        # authorization_entry_reason: a full-shape entry whose row_digest
        # is not a hex64 digest refuses through the named malformed leg.
        entry = ack_entry(self.row)
        entry["row_digest"] = "witness-shape-not-hex"
        reason = cr.authorization_entry_reason(self.row, entry, PLAN_REL)
        assert_refusal(self, reason, "receipt",
                       "malformed correction_authorizations entry",
                       "row_digest is not a hex64 digest")

    def test_duplicate_entry_refuses(self):
        self.write_entries([ack_entry(self.row), ack_entry(self.row)])
        ok, msg = self.verify()
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt", "non-unique")

    def test_malformed_entry_refuses(self):
        def drop_recorded_at(entry):
            del entry["recorded_at"]

        def add_surprise(entry):
            entry["surprise"] = 1

        def blank_writer(entry):
            entry["writer_session_id"] = "   "

        def empty_author(entry):
            entry["author_session_id"] = ""

        def empty_direction(entry):
            entry["operator_direction"] = ""

        def non_list_hunks(entry):
            entry["hunk_digests"] = "not-a-list"

        def empty_hunks(entry):
            entry["hunk_digests"] = []

        for mutate in (drop_recorded_at, add_surprise, blank_writer,
                       empty_author, empty_direction, non_list_hunks,
                       empty_hunks):
            entry = ack_entry(self.row)
            mutate(entry)
            self.write_entries([entry])
            ok, msg = self.verify()
            self.assertFalse(ok, mutate)
            assert_refusal(self, msg, "receipt",
                           "malformed correction_authorizations entry")

    def test_mismatched_copied_field_refuses(self):
        for overrides in ({"after_digest": "f" * 64},
                          {"before_digest": "e" * 64},
                          {"artifact_path": "docs/history/plans/other.md"},
                          {"evidence_commit": "a" * 40},
                          {"author_session_id": "sess-other"},
                          {"recorded_at": "1999-01-01T00:00:00Z"}):
            self.write_entries([ack_entry(self.row, **overrides)])
            ok, msg = self.verify()
            self.assertFalse(ok, overrides)
            assert_refusal(self, msg, "receipt", "subject mismatch")

    def test_swapped_hunk_order_refuses(self):
        two_hunk = ack_state_row(hx(D1), hx(D3), self.hop)
        two_hunk["hunks"] = [
            {"header": "@@ -2 +2 @@", "digest": hx(b"hunk-bytes")},
            {"header": "@@ -3 +3 @@", "digest": hx(b"second-hunk")},
        ]
        self.repo.write_file(
            ACK_GAP_REL,
            "# classifier gap\n\nhunk digests %s and %s\n"
            % (hx(b"hunk-bytes"), hx(b"second-hunk")))
        self.repo.commit_all("quote both hunk digests")
        self.write_entries([ack_entry(two_hunk)])
        ok, msg = self.verify(rows=[two_hunk])
        self.assertTrue(ok, msg)
        entry = ack_entry(two_hunk)
        entry["hunk_digests"] = list(reversed(entry["hunk_digests"]))
        self.write_entries([entry])
        ok, msg = self.verify(rows=[two_hunk])
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt", "subject mismatch")

    def test_same_session_writer_refuses(self):
        self.write_entries(
            [ack_entry(self.row, writer_session_id=ACK_AUTHOR)])
        ok, msg = self.verify()
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt",
                       "written by the recording session")
        self.write_entries(
            [ack_entry(self.row, writer_session_id="sess-x",
                       author_session_id="sess-x")])
        ok, msg = self.verify()
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt",
                       "written by the recording session")

    def test_writer_equal_to_row_author_refuses(self):
        # The second same-session disjunct in isolation: the entry's own
        # copied author differs from the row's, but the writer equals the
        # row's author session; the refusal echoes the compared row value.
        self.write_entries(
            [ack_entry(self.row, writer_session_id=ACK_AUTHOR,
                       author_session_id="sess-other")])
        ok, msg = self.verify()
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt",
                       "written by the recording session",
                       "the row's author_session_id", ACK_AUTHOR)

    def test_identity_less_row_refuses_on_the_state_route(self):
        # On the state route the row must carry its own nonempty
        # author_session_id; without it the writer-distinctness checks
        # would silently no-op, so the route refuses instead. Archived
        # legacy rows never reach this route, so absent tolerance for
        # them is unaffected.
        naked = json.loads(json.dumps(self.row))
        naked.pop("author_session_id")
        self.write_entries(
            [ack_entry(naked, writer_session_id="sess-fabricated",
                       author_session_id="sess-fabricated")])
        ok, msg = self.verify(rows=[naked])
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt", "author_session_id")

    def test_directive_mismatch_refuses(self):
        self.write_entries(
            [ack_entry(self.row, operator_direction="an unrelated ask")])
        ok, msg = self.verify()
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt", "subject mismatch",
                       "operator_direction")

    def test_caller_selected_witness_path_refuses(self):
        rogue = json.loads(json.dumps(self.row))
        rogue["receipt"]["authorization_witness"] = "/tmp/elsewhere.record"
        ok, msg = self.verify(rows=[rogue])
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt", "unresolvable witness",
                       "fixed selector")
        ok, msg = self.verify(witness_path="/tmp/elsewhere.record")
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt", "unresolvable witness",
                       "caller-selected witness path")

    def test_gap_record_legs_hold_in_state_mode(self):
        self.repo.write_file(ACK_GAP_REL, "# gap without any digest\n")
        self.repo.commit_all("blank the gap row")
        ok, msg = self.verify()
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt", "does not quote")
        rogue = json.loads(json.dumps(self.row))
        rogue["receipt"]["classifier_gap_row"] = \
            "docs/history/backlog/absent-gap.md"
        self.write_entries([ack_entry(rogue)])
        ok, msg = self.verify(rows=[rogue])
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt", "dangling")

    def test_broken_linkage_still_refuses_in_state_mode(self):
        hop2 = self.repo.commit_file(PLAN_REL, D2, "second fix")
        row2 = plan_row(hx(D1), hx(D2), hop2)
        ok, msg = self.verify(rows=[self.row, row2])
        self.assertFalse(ok)
        assert_refusal(self, msg, "linkage")

    def test_code_family_receipt_and_classify_unchanged(self):
        repo = cr.build_scratch_repo(self, name="code-ack-repo")
        b0 = repo.commit_file("src/app.py", "def f():\n    return 1\n",
                              "base code")
        b1 = repo.commit_file("src/app.py", "def f():\n    return 2\n",
                              "change code")
        close = repo.commit_allow_empty("round close")
        diff0 = repo.git("diff", "%s...%s" % (b0, b1)).stdout
        repo.append_seal_entry(
            "acme-src", 1, "src/app.py", b1, hx(diff0.encode()), close,
            reviewed=(b0, b1, hx(diff0.encode())))
        b2 = repo.commit_file("src/app.py",
                              "def f():\n    # note\n    return 2\n",
                              "comment fix")
        diff1 = repo.git("diff", "%s...%s" % (b1, b2)).stdout
        witness_dir = tempfile.TemporaryDirectory(prefix="code-ack-")
        self.addCleanup(witness_dir.cleanup)
        witness_path = str(Path(witness_dir.name) / "turn.record")
        Path(witness_path).write_text("\n".join([
            "turn: authorize-rebind",
            "writer: scheduler-turn-writer",
            "operator_direction: accept the comment-only re-bind",
            "artifact: src/app.py",
            "before_digest: %s" % hx(diff0.encode()),
            "after_digest: %s" % hx(diff1.encode()),
        ]) + "\n")
        gap_rel = "docs/history/backlog/code-ack-gap.md"
        repo.write_file(gap_rel, "# gap\n\nhunk %s\n" % hx(b"hunk"))
        repo.commit_all("file the code gap row")
        row = code_row(b0, b1, b1, b2, hx(diff0.encode()), hx(diff1.encode()),
                       kind=cr.KIND_OPERATOR_ACKED,
                       receipt={"directive": "accept the comment-only re-bind",
                                "authorization_witness": witness_path,
                                "classifier_gap_row": gap_rel})
        # The turn-record receipt still resolves for code-family rows even
        # with a primary checkout in play, and the classify leg still
        # applies to an acked code hop: no bypass for the code family.
        ok, msg = cr.verify_corrections(
            repo.root, "src/app.py", cr.FAMILY_CODE, 1, hx(diff0.encode()),
            [row], certified_range={"base": b0, "head": b1},
            slug="acme-src", witness_path=witness_path, classify=refuse_all,
            head=b2, primary_checkout=str(self.primary))
        self.assertFalse(ok)
        assert_refusal(self, msg, "classify", "hunk 0")
        ok, msg = cr.verify_corrections(
            repo.root, "src/app.py", cr.FAMILY_CODE, 1, hx(diff0.encode()),
            [row], certified_range={"base": b0, "head": b1},
            slug="acme-src", witness_path=witness_path,
            head=b2, primary_checkout=str(self.primary))
        self.assertTrue(ok, msg)


class CorrectionAuthorizationWriterTest(unittest.TestCase):
    """The production acknowledgment writer (plan Task 3): a later
    distinct interactive session records the durable
    correction_authorizations entry into the primary checkout's scheduler
    state file. Same-session and empty writer identities refuse, no
    caller-supplied writer identity, state path, or mode exists, appends
    are idempotent by row digest, conflicting duplicates refuse, the
    entry survives a full state rewrite, and a post-replace read-back
    confirms the appended digest or refuses with a named loss."""

    DIRECTIVE = "re-bind the unclassified delta"
    WRITER = "sess-operator-writer"

    def setUp(self):
        self.repo = cr.build_scratch_repo(self)
        start = self.repo.commit_file(PLAN_REL, D1, "seed plan")
        close = self.repo.commit_allow_empty("round 1 close")
        self.repo.append_seal_entry(PLAN_SLUG, 1, PLAN_REL, start, hx(D1),
                                    close)
        self.hop = self.repo.commit_file(PLAN_REL, D3, "unclassified fix")
        self.row = ack_state_row(hx(D1), hx(D3), self.hop)
        self.repo.write_file(
            ACK_GAP_REL,
            "# classifier gap\n\nhunk digest %s\n"
            % self.row["hunks"][0]["digest"])
        self.repo.commit_all("file the classifier gap row")
        self.write_entries([])
        # The save/restore pattern from the session-channel selftest:
        # every fixture pins and clears all four session sources.
        self.saved_env = sc._save_env(*SESSION_ENV_NAMES)

    def tearDown(self):
        sc._restore_env(self.saved_env)

    def pin_env(self, **values):
        """Clear all four session sources, then set the named ones."""
        for name in SESSION_ENV_NAMES:
            os.environ.pop(name, None)
        for name, value in values.items():
            os.environ[name] = value

    def state_path(self):
        return self.repo.root / ".ai-playbook" / "scheduler-state.json"

    def write_entries(self, entries, doc=None):
        state_dir = self.repo.root / ".ai-playbook"
        state_dir.mkdir(parents=True, exist_ok=True)
        payload = {"schema": 4, "correction_authorizations": entries} \
            if doc is None else doc
        (state_dir / "scheduler-state.json").write_text(json.dumps(payload))

    def read_doc(self):
        return json.loads(self.state_path().read_text())

    def record(self, row=None, direction=None, repo=None):
        return cr.record_correction_authorization(
            self.repo.root if repo is None else repo,
            self.row if row is None else row,
            self.DIRECTIVE if direction is None else direction,
            PLAN_REL)

    def test_valid_distinct_session_append_binds_digest_and_subject(self):
        # The writer session resolves through the Codex fallback; the row
        # keeps its own author identity (the two-session shape).
        self.pin_env(**{sc.CODEX_SESSION_ENV: self.WRITER})
        ok, msg = self.record()
        self.assertTrue(ok, msg)
        self.assertIn("authorization recorded", msg)
        digest = cr.correction_row_digest(self.row)
        self.assertIn(digest, msg)
        entries = self.read_doc()["correction_authorizations"]
        self.assertEqual(len(entries), 1)
        expected = {
            "row_digest": digest,
            "writer_session_id": self.WRITER,
            "operator_direction": self.DIRECTIVE,
            "author_session_id": ACK_AUTHOR,
            "artifact_path": PLAN_REL,
            "before_digest": self.row["before_digest"],
            "after_digest": self.row["after_digest"],
            "evidence_commit": self.hop,
            "hunk_digests": [h["digest"] for h in self.row["hunks"]],
        }
        self.assertEqual(set(entries[0]), set(cr.AUTHORIZATION_ENTRY_KEYS))
        self.assertEqual(entries[0]["row_digest"], expected["row_digest"])
        for key, value in expected.items():
            self.assertEqual(entries[0][key], value, key)
        self.assertRegex(entries[0]["recorded_at"],
                         r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
        # The produced entry is the shape the verifier accepts, and the
        # state route resolves it.
        self.assertIsNone(cr.authorization_entry_reason(
            self.row, entries[0], PLAN_REL))
        ok, msg = cr.resolve_state_authorization(
            self.row, str(self.repo.root), self.repo.root, PLAN_REL)
        self.assertTrue(ok, msg)
        # The targeted edit changed only the array member.
        doc = self.read_doc()
        self.assertEqual(doc["schema"], 4)

    def test_same_session_writer_refuses(self):
        for env in ({sc.CODEX_SESSION_ENV: ACK_AUTHOR},
                    {sc.CLAUDE_SESSION_ENV: ACK_AUTHOR,
                     sc.CODEX_SESSION_ENV: self.WRITER}):
            self.pin_env(**env)
            ok, msg = self.record()
            self.assertFalse(ok, env)
            assert_refusal(self, msg, "append",
                           "written by the recording session", ACK_AUTHOR)
        self.assertEqual(self.read_doc()["correction_authorizations"], [])

    def test_empty_writer_identity_refuses(self):
        for env in ({}, {sc.CODEX_SESSION_ENV: ""},
                    {sc.CODEX_SESSION_ENV: "   "}):
            self.pin_env(**env)
            ok, msg = self.record()
            self.assertFalse(ok, env)
            assert_refusal(self, msg, "append", "unbound writer session",
                           "empty")
        self.assertEqual(self.read_doc()["correction_authorizations"], [])

    def test_writer_identity_and_path_are_never_caller_supplied(self):
        # No writer-identity, state-path, witness-path, or mode parameter
        # exists to call: the writer derives its own session identity and
        # resolves its own write root.
        params = set(inspect.signature(
            cr.record_correction_authorization).parameters)
        for banned in ("writer_session_id", "writer_identity",
                       "state_path", "witness_path", "mode"):
            self.assertNotIn(banned, params)
        self.pin_env(**{sc.CODEX_SESSION_ENV: self.WRITER})
        with self.assertRaises(TypeError):
            cr.record_correction_authorization(
                self.repo.root, self.row, self.DIRECTIVE, PLAN_REL,
                writer_session_id="sess-forge")
        with self.assertRaises(TypeError):
            cr.record_correction_authorization(
                self.repo.root, self.row, self.DIRECTIVE, PLAN_REL,
                state_path="/tmp/elsewhere-state.json")
        with self.assertRaises(TypeError):
            cr.record_correction_authorization(
                self.repo.root, self.row, self.DIRECTIVE, PLAN_REL,
                mode="interactive")
        self.assertEqual(self.read_doc()["correction_authorizations"], [])

    def test_scheduled_shape_without_writer_invocation_keeps_fresh_review(self):
        # The scheduled-maintenance shape never invokes the writer: the
        # authorization stays absent and the verifier refuses through the
        # missing-witness leg (fresh review retained).
        ok, msg = cr.verify_corrections(
            self.repo.root, PLAN_REL, cr.FAMILY_PLAN, 1, hx(D1),
            [self.row], current_bytes=D3,
            primary_checkout=str(self.repo.root), classify=refuse_all)
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt",
                       "no correction_authorizations entry")
        self.assertEqual(self.read_doc()["correction_authorizations"], [])

    def test_direction_is_required_and_must_match_the_receipt(self):
        self.pin_env(**{sc.CODEX_SESSION_ENV: self.WRITER})
        ok, msg = self.record(direction="   ")
        self.assertFalse(ok)
        assert_refusal(self, msg, "append", "operator direction is empty")
        ok, msg = self.record(direction="an unrelated ask")
        self.assertFalse(ok)
        assert_refusal(self, msg, "append", "subject mismatch",
                       "receipt directive")
        self.assertEqual(self.read_doc()["correction_authorizations"], [])

    def test_row_must_be_an_acked_plan_row_with_an_author(self):
        self.pin_env(**{sc.CODEX_SESSION_ENV: self.WRITER})
        naked = json.loads(json.dumps(self.row))
        naked.pop("author_session_id")
        ok, msg = self.record(row=naked)
        self.assertFalse(ok)
        assert_refusal(self, msg, "append", "unbound author session",
                       "author_session_id")
        script_row = plan_row(hx(D1), hx(D3), self.hop)
        ok, msg = self.record(row=script_row)
        self.assertFalse(ok)
        assert_refusal(self, msg, "append", "operator-acked plan-family row")
        self.assertEqual(self.read_doc()["correction_authorizations"], [])

    def test_append_is_idempotent_and_conflicting_duplicates_refuse(self):
        self.pin_env(**{sc.CODEX_SESSION_ENV: self.WRITER})
        ok, msg = self.record()
        self.assertTrue(ok, msg)
        ok, msg = self.record()
        self.assertTrue(ok, msg)
        self.assertIn("already present", msg)
        self.assertEqual(len(self.read_doc()["correction_authorizations"]),
                         1)
        # A different later session acking the same row digest is a
        # conflicting duplicate, not an idempotent repeat.
        self.pin_env(**{sc.CODEX_SESSION_ENV: "sess-other-operator"})
        ok, msg = self.record()
        self.assertFalse(ok)
        assert_refusal(self, msg, "append", "conflicting",
                       cr.correction_row_digest(self.row))
        self.assertEqual(len(self.read_doc()["correction_authorizations"]),
                         1)

    def test_entry_survives_a_full_state_rewrite_and_still_verifies(self):
        self.pin_env(**{sc.CODEX_SESSION_ENV: self.WRITER})
        ok, msg = self.record()
        self.assertTrue(ok, msg)
        doc = self.read_doc()
        doc["last_run_at"] = "2026-10-20T00:00:00Z"
        doc["children"] = []
        self.state_path().write_text(
            json.dumps(doc, indent=2, sort_keys=True) + "\n")
        ok, msg = cr.resolve_state_authorization(
            self.row, str(self.repo.root), self.repo.root, PLAN_REL)
        self.assertTrue(ok, msg)
        ok, msg = cr.verify_corrections(
            self.repo.root, PLAN_REL, cr.FAMILY_PLAN, 1, hx(D1),
            [self.row], current_bytes=D3,
            primary_checkout=str(self.repo.root), classify=refuse_all)
        self.assertTrue(ok, msg)
        self.assertIn("chain verified", msg)

    def test_read_back_confirms_the_append_or_names_the_loss(self):
        self.pin_env(**{sc.CODEX_SESSION_ENV: self.WRITER})
        with mock.patch.object(cr.os, "replace", lambda src, dst: None):
            ok, msg = self.record()
        self.assertFalse(ok)
        assert_refusal(self, msg, "append", "ack append lost",
                       "fresh operator direction")
        self.assertEqual(self.read_doc()["correction_authorizations"], [])
        # The temp copy the failed replace left behind is cleaned up.
        leftovers = list((self.repo.root / ".ai-playbook").glob(
            "scheduler-state.json.ack-tmp-*"))
        self.assertEqual(leftovers, [])

    def test_write_root_is_the_primary_checkout_not_a_worktree_copy(self):
        secondary_dir = tempfile.TemporaryDirectory(prefix="ack-secondary-")
        self.addCleanup(secondary_dir.cleanup)
        secondary = Path(secondary_dir.name) / "wt"
        self.repo.git("worktree", "add", "-b", "ack-side", str(secondary))
        decoy_dir = secondary / ".ai-playbook"
        decoy_dir.mkdir(parents=True, exist_ok=True)
        (decoy_dir / "scheduler-state.json").write_text(json.dumps(
            {"schema": 4, "correction_authorizations": [
                ack_entry(self.row, writer_session_id="sess-decoy")]}))
        self.pin_env(**{sc.CODEX_SESSION_ENV: self.WRITER})
        ok, msg = self.record(repo=str(secondary))
        self.assertTrue(ok, msg)
        # The entry landed in the primary checkout's state file and the
        # worktree-local decoy was never touched.
        entries = self.read_doc()["correction_authorizations"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["writer_session_id"], self.WRITER)
        decoy = json.loads(
            (decoy_dir / "scheduler-state.json").read_text())
        self.assertEqual(decoy["correction_authorizations"],
                         [ack_entry(self.row, writer_session_id="sess-decoy")])

    def test_plumbing_failure_and_absent_state_refuse(self):
        self.pin_env(**{sc.CODEX_SESSION_ENV: self.WRITER})
        with mock.patch.object(cr, "git_text", return_value=None):
            ok, msg = self.record()
        self.assertFalse(ok)
        assert_refusal(self, msg, "append", "git plumbing failed",
                       "primary checkout")
        self.state_path().unlink()
        ok, msg = self.record()
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt", "unresolvable witness",
                       "absent or unreadable")

    def test_malformed_existing_row_digest_refuses_the_writer(self):
        self.pin_env(**{sc.CODEX_SESSION_ENV: self.WRITER})
        entry = ack_entry(self.row, writer_session_id="sess-historic")
        entry["row_digest"] = "past-entry-not-hex"
        self.write_entries([entry])
        ok, msg = self.record()
        self.assertFalse(ok)
        assert_refusal(self, msg, "receipt",
                       "malformed correction_authorizations entry",
                       "row_digest is not a hex64 digest")

    def test_drift_between_pre_read_and_replace_retries_once_and_merges(self):
        # A concurrent writer lands its own change after the writer's
        # pre-read and before the drift re-read (hooked through a
        # read_text side effect): the guard catches the drift, the single
        # retry re-evaluates the precondition on the concurrent bytes,
        # and the final state carries both the concurrent change and the
        # new entry.
        self.pin_env(**{sc.CODEX_SESSION_ENV: self.WRITER})
        state = self.state_path()
        real_read_text = Path.read_text
        reads = {"n": 0}

        def concurrent_replace(path, *args, **kwargs):
            text = real_read_text(path, *args, **kwargs)
            # git reports the physical checkout path (/private/var on
            # macOS), so compare resolved paths, never lexical ones.
            if path.resolve() == state.resolve():
                reads["n"] += 1
                if reads["n"] == 2:
                    # The writer's first drift re-read: the concurrent
                    # writer lands its change here, between the pre-read
                    # and the replace precondition.
                    doc = json.loads(text)
                    doc["last_run_at"] = "2026-10-20T09:30:00Z"
                    state.write_text(
                        json.dumps(doc, indent=2, sort_keys=True) + "\n")
                    text = real_read_text(path, *args, **kwargs)
            return text

        with mock.patch.object(Path, "read_text", concurrent_replace):
            ok, msg = self.record()
        self.assertTrue(ok, msg)
        doc = self.read_doc()
        self.assertEqual(doc["last_run_at"], "2026-10-20T09:30:00Z")
        entries = doc["correction_authorizations"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["row_digest"],
                         cr.correction_row_digest(self.row))
        self.assertEqual(entries[0]["writer_session_id"], self.WRITER)

    def test_drift_on_both_attempts_refuses_and_leaves_the_state(self):
        # Drift on both attempts exhausts the one-retry guard: the named
        # refusal fires, no entry is written, and the state file stays
        # exactly as the concurrent writer left it.
        self.pin_env(**{sc.CODEX_SESSION_ENV: self.WRITER})
        state = self.state_path()
        real_read_text = Path.read_text
        reads = {"n": 0}
        concurrent = {"n": 0}

        def concurrent_twice(path, *args, **kwargs):
            text = real_read_text(path, *args, **kwargs)
            # git reports the physical checkout path (/private/var on
            # macOS), so compare resolved paths, never lexical ones.
            if path.resolve() == state.resolve():
                reads["n"] += 1
                if reads["n"] in (2, 4):
                    concurrent["n"] += 1
                    doc = json.loads(text)
                    doc["last_run_at"] = "2026-10-20T09:3%d:00Z" \
                        % concurrent["n"]
                    state.write_text(
                        json.dumps(doc, indent=2, sort_keys=True) + "\n")
                    text = real_read_text(path, *args, **kwargs)
            return text

        with mock.patch.object(Path, "read_text", concurrent_twice):
            ok, msg = self.record()
        self.assertFalse(ok)
        assert_refusal(self, msg, "append", "drifted twice",
                       "no write was performed")
        self.assertEqual(reads["n"], 4)
        self.assertEqual(concurrent["n"], 2)
        doc = self.read_doc()
        self.assertEqual(doc["last_run_at"], "2026-10-20T09:32:00Z")
        self.assertEqual(doc["correction_authorizations"], [])


class MarkerConstantsTest(unittest.TestCase):
    def test_prefix_and_banned_literals(self):
        self.assertEqual(cr.MARKER_PREFIX, "corrections verification: ")
        self.assertIsInstance(cr.BANNED_LITERALS, tuple)
        self.assertTrue(len(cr.BANNED_LITERALS) >= 2)
        self.assertEqual(len(set(cr.LEG_REASONS.values())),
                         len(cr.LEG_REASONS))
        for leg, fragment in cr.LEG_REASONS.items():
            reason = cr.leg_reason(leg, "detail")
            self.assertTrue(reason.startswith(cr.MARKER_PREFIX), reason)
            self.assertTrue(reason.startswith(
                cr.MARKER_PREFIX + fragment), reason)
            for banned in cr.BANNED_LITERALS:
                self.assertNotIn(banned, reason)


class RegionScannerTest(unittest.TestCase):
    def test_excluded_regions(self):
        # Backtick fences with an info string; prose after the close is
        # classifiable.
        t = "```python\nx = 1\n```\nprose line\n"
        self.assertEqual(cr.excluded_line_numbers(t), {1, 2, 3})
        self.assertFalse(cr.line_fully_excluded(t, 4))
        # Tilde fences with an info string.
        t = "~~~bash\ncd ~\n~~~\nprose\n"
        self.assertEqual(cr.excluded_line_numbers(t), {1, 2, 3})
        # An unclosed fence extends to end of file.
        t = "text\n\n```text\nbody\nmore\n"
        self.assertEqual(cr.excluded_line_numbers(t), {3, 4, 5})
        # Inline code spans exclude exactly the span.
        t = "see `a b` end\n"
        tick = t.index("`")
        close = t.index("`", tick + 1)
        self.assertTrue(cr.span_excluded(t, tick, close + 1))
        self.assertFalse(cr.span_excluded(t, 0, 3))
        self.assertFalse(cr.span_excluded(t, t.index("end"),
                                          t.index("end") + 3))
        # Indented code blocks after a blank line.
        t = "para\n\n    code()\nafter\n"
        self.assertEqual(cr.excluded_line_numbers(t), {3})
        # A four-space continuation without a blank line stays prose.
        t = "para\n    continuation\n"
        self.assertEqual(cr.excluded_line_numbers(t), set())
        # Indented code inside list nesting (content column 2, so six
        # spaces).
        t = "- item\n\n      deep = 1\nprose\n"
        self.assertEqual(cr.excluded_line_numbers(t), {3})
        # Setext underline lines.
        t = "Title\n=====\nbody\n"
        self.assertEqual(cr.excluded_line_numbers(t), {2})
        t = "Title\n-----\nbody\n"
        self.assertEqual(cr.excluded_line_numbers(t), {2})
        # Thematic breaks.
        t = "intro\n\n***\nprose\n"
        self.assertEqual(cr.excluded_line_numbers(t), {3})
        t = "intro\n\n- - -\nprose\n"
        self.assertEqual(cr.excluded_line_numbers(t), {3})
        # Table delimiter rows, with and without outer pipes.
        t = "h1 | h2\n--- | ---\nprose\n"
        self.assertEqual(cr.excluded_line_numbers(t), {2})
        t = "| h1 | h2 |\n| --- | --- |\nprose\n"
        self.assertEqual(cr.excluded_line_numbers(t), {2})
        # Link destination spans: the ](...) target and <...> autolinks.
        t = "[docs](http://x/y) tail\n"
        self.assertTrue(cr.span_excluded(t, t.index("("),
                                         t.index(")") + 1))
        self.assertFalse(cr.span_excluded(t, 0, 1))
        t = "<http://x/y> ok\n"
        self.assertTrue(cr.span_excluded(t, 0, t.index(">") + 1))
        self.assertFalse(cr.span_excluded(t, t.index("ok"),
                                          t.index("ok") + 2))
        # Prose outside excluded regions is classifiable.
        t = "plain words here\n"
        self.assertEqual(cr.excluded_char_spans(t), [])
        self.assertEqual(cr.excluded_line_numbers(t), set())
        self.assertFalse(cr.line_fully_excluded(t, 1))


class FixtureBuilderTest(unittest.TestCase):
    def test_hermetic_scratch_repo(self):
        env = cr.hermetic_git_env()
        git_keys = {k for k in env if k.startswith("GIT_")}
        self.assertEqual(git_keys,
                         {"GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM"})
        self.assertEqual(env["GIT_CONFIG_GLOBAL"], "/dev/null")
        self.assertEqual(env["GIT_CONFIG_SYSTEM"], "/dev/null")
        repo = cr.build_scratch_repo(self)
        self.assertIsInstance(repo.temp_directory,
                              tempfile.TemporaryDirectory)
        self.assertTrue(str(repo.root).startswith(tempfile.gettempdir()))
        self.assertEqual(
            repo.git("config", "user.email").stdout.strip(),
            "fixture@example.invalid")
        self.assertEqual(
            repo.git("config", "user.name").stdout.strip(), "fixture")
        # Explicit author and committer dates are pinned per commit.
        sha = repo.commit_file("f.txt", b"one\n", "one", date=1700000000)
        show = repo.git("show", "-s", "--format=%at %ct",
                        sha).stdout.strip()
        self.assertEqual(show, "1700000000 1700000000")
        sha2 = repo.commit_file("f.txt", b"two\n", "two")
        show2 = repo.git("show", "-s", "--format=%at %ct",
                         sha2).stdout.strip()
        stamp = int(show2.split()[0])
        self.assertGreater(stamp, 1700000000)
        self.assertEqual(show2.split(), [str(stamp), str(stamp)])
        # Seed content is committed at HEAD.
        self.assertIn(b"two\n",
                      repo.git("show", "HEAD:f.txt").stdout.encode())
        # Seal entries are written and committed as part of seeding.
        start = repo.head()
        repo.append_seal_entry("builder-plan", 1, "f.txt", start,
                               hx(b"two\n"), start)
        seal_rel = cr.seal_relpath("f.txt", "builder-plan")
        committed = repo.git("show", "HEAD:%s" % seal_rel).stdout
        entries = cr.parse_seal(committed)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].round, 1)
        self.assertEqual(entries[0].fields["artifact"], "f.txt")
        self.assertEqual(entries[0].fields["round_start_commit"], start)
        self.assertEqual(entries[0].fields["round_start_digest"],
                         hx(b"two\n"))
        self.assertEqual(entries[0].fields["round_close_commit"], start)


if __name__ == "__main__":
    unittest.main()
