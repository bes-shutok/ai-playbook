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
never echoing the slug), the excluded-region scanner, and the fixture
builder itself.
"""

import fcntl
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import corrections_record as cr

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
        # A seal entry whose round-close commit is not an ancestor of HEAD.
        repo2, c2 = plan_fixture(self)
        orphan = orphan_commit(repo2)
        repo2.write_seal_entry(PLAN_SLUG, 1, PLAN_REL, c2["start"],
                               hx(D1), orphan, message="seal: orphan close")
        ok, msg = vplan(repo2, [plan_row(hx(D1), hx(D2), c2["hop1"])],
                        hx(D1), D2)
        self.assertFalse(ok)
        assert_refusal(self, msg, "anchor", "round-close commit")
        # A moved anchor: the round-start blob does not re-hash to the
        # entry's claimed round-start digest.
        repo3, c3 = plan_fixture(self)
        repo3.write_seal_entry(PLAN_SLUG, 1, PLAN_REL, c3["start"],
                               hx(D2), c3["close"], message="seal: moved")
        ok, msg = vplan(repo3, [plan_row(hx(D2), hx(D3), c3["hop1"])],
                        hx(D2), D2)
        self.assertFalse(ok)
        assert_refusal(self, msg, "anchor", "re-hash")


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
        ok, msg = self.resolve()
        self.assertTrue(ok, msg)
        ok, msg = vplan(self.repo, [self.row], hx(D1), D2,
                        witness_path=self.witness_path)
        self.assertTrue(ok, msg)
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
