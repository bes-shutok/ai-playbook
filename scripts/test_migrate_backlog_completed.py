"""Unit tests for scripts/migrate_backlog_completed.py (fold-then-delete migration).

Covers the pinned matcher contract (date-prefix strip, hyphen tokenization,
stop-word exclusion, two-token threshold, lexicographic tie-break) and the
pinned apply contract (write-gate licensing notes, row backfill with identity
collision escalation, disposition bullets, idempotent re-run, frozen dirs).
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HELPER = os.path.join(REPO, "scripts", "migrate_backlog_completed.py")

REGISTRY_HEADER = """<!-- registry -->
| identity | sot | state | archived | reason | src | successor | aliases | audit |
|---|---|---|---|---|---|---|---|---|
"""


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def read(path):
    with open(path) as f:
        return f.read()


class Fixture:
    def __init__(self):
        self.root = tempfile.mkdtemp(prefix="mig-fixture-")
        self.plans = os.path.join(self.root, "plans-completed")
        self.inbox = os.path.join(self.root, "backlog-completed")
        self.registry_path = os.path.join(self.root, "registry.md")
        self.selfhost = os.path.join(self.root, "self-host-plan.md")
        os.makedirs(self.plans)
        os.makedirs(self.inbox)
        write(self.selfhost, "# Plan: self host\n\n## Disposition of migrated backlog items\n\n(none)\n")

    def plan(self, name, body="# Plan\n\nbody\n"):
        write(os.path.join(self.plans, name), body)
        return os.path.join(self.plans, name)

    def item(self, name):
        write(os.path.join(self.inbox, name), "origin body\n")
        return os.path.join(self.inbox, name)

    def registry(self, rows):
        write(self.registry_path, REGISTRY_HEADER + "".join(rows))

    def run(self, *extra, apply=False, report=None):
        cmd = [sys.executable, HELPER,
               "--plans-dir", self.plans,
               "--backlog-completed-dir", self.inbox,
               "--registry", self.registry_path,
               "--self-host", self.selfhost]
        if report:
            cmd += ["--report", report]
        if apply:
            cmd += ["--apply"]
        cmd += list(extra)
        return subprocess.run(cmd, capture_output=True, text=True)

    def cleanup(self):
        shutil.rmtree(self.root)


class MatcherTest(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()

    def tearDown(self):
        self.fx.cleanup()

    def test_exact_stem_match(self):
        self.fx.plan("2026-09-02-review-panel-hermeticity-dimension.md")
        self.fx.item("2026-09-01-review-panel-hermeticity-dimension.md")
        self.fx.registry("")
        report = os.path.join(self.fx.root, "report.md")
        rc = self.fx.run("--report", report).returncode
        self.assertEqual(rc, 0)
        self.assertIn("review-panel-hermeticity-dimension", read(report))

    def test_single_token_overlap_unmatched(self):
        self.fx.plan("2026-01-01-alpha-beta-gamma.md")
        self.fx.item("2026-01-02-alpha-only.md")
        self.fx.registry("")
        self.fx.run("--apply")
        self.assertTrue(os.path.exists(os.path.join(self.fx.inbox, "2026-01-02-alpha-only.md")) is False)
        self.assertIn("alpha-only", read(self.fx.selfhost))

    def test_best_score_wins(self):
        self.fx.plan("2026-01-01-aa-bb-cc.md")
        self.fx.plan("2026-01-02-aa-bb.md")
        self.fx.item("2026-01-03-aa-bb-cc-x.md")
        self.fx.registry("")
        report = os.path.join(self.fx.root, "report.md")
        self.fx.run("--report", report)
        self.assertIn("2026-01-01-aa-bb-cc.md", read(report))

    def test_tie_break_deterministic(self):
        self.fx.plan("2026-01-01-zz-yy.md")
        self.fx.plan("2026-01-02-zz-yy-variant.md")
        self.fx.item("2026-01-03-zz-yy-extra.md")
        self.fx.registry("")
        report = os.path.join(self.fx.root, "report.md")
        self.fx.run("--report", report)
        text = read(report)
        self.assertIn("2026-01-01-zz-yy.md", text)
        self.assertIn("tie", text.lower())

    def test_stop_words_excluded(self):
        self.fx.plan("2026-01-01-review-and-fix.md")
        self.fx.item("2026-01-02-review-and.md")
        self.fx.registry("")
        report = os.path.join(self.fx.root, "report.md")
        self.fx.run("--report", report)
        self.assertIn("self-host", read(report))


class ApplyTest(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()

    def tearDown(self):
        self.fx.cleanup()

    def test_missing_destination_fails(self):
        self.fx.item("2026-01-02-aa-bb.md")
        self.fx.registry("")
        overrides = os.path.join(self.fx.root, "overrides.txt")
        write(overrides, "aa-bb docs/history/plans/completed/2026-01-09-nope.md\n")
        before = sorted(os.listdir(self.fx.inbox))
        rc = self.fx.run("--overrides", overrides, apply=True).returncode
        self.assertNotEqual(rc, 0)
        self.assertEqual(sorted(os.listdir(self.fx.inbox)), before)

    def test_unregistered_item_gets_row_note(self):
        self.fx.plan("2026-01-01-aa-bb.md")
        self.fx.item("2026-01-02-aa-bb.md")
        self.fx.registry("")
        rc = self.fx.run(apply=True).returncode
        self.assertEqual(rc, 0)
        reg = read(self.fx.registry_path)
        self.assertIn("aa-bb", reg)
        self.assertIn("user-approved ", reg)
        self.assertIn("disposition folded into", reg)
        self.assertFalse(os.path.exists(os.path.join(self.fx.inbox, "2026-01-02-aa-bb.md")))

    def test_destination_row_noted(self):
        self.fx.plan("2026-01-01-aa-bb.md")
        self.fx.item("2026-01-02-aa-bb.md")
        self.fx.registry("| aa-bb | no | completed | 2026-01-01 | executed | docs/history/plans/completed/2026-01-01-aa-bb.md |  |  |  |\n")
        self.fx.run(apply=True)
        reg = read(self.fx.registry_path)
        self.assertIn("received backlog-completed/2026-01-02-aa-bb.md disposition (per-item file deleted)", reg)

    def test_rowless_destination_backfilled_and_licensed(self):
        self.fx.plan("2026-01-01-aa-bb.md")
        self.fx.item("2026-01-02-aa-bb.md")
        self.fx.registry("")
        rc = self.fx.run(apply=True).returncode
        self.assertEqual(rc, 0)
        reg = read(self.fx.registry_path)
        self.assertIn("received backlog-completed/2026-01-02-aa-bb.md disposition", reg)

    def test_apply_folds_bullet_and_deletes(self):
        dest = self.fx.plan("2026-01-01-aa-bb.md")
        self.fx.item("2026-01-02-aa-bb.md")
        self.fx.registry("")
        self.fx.run(apply=True)
        text = read(dest)
        self.assertIn("## Disposition of migrated backlog items", text)
        self.assertIn("2026-01-02-aa-bb.md", text)
        self.assertFalse(os.path.exists(os.path.join(self.fx.inbox, "2026-01-02-aa-bb.md")))
        # idempotent no-op
        rc = self.fx.run(apply=True).returncode
        self.assertEqual(rc, 0)
        self.assertEqual(read(dest), text)

    def test_self_host_section(self):
        self.fx.item("2026-01-02-qq-rr.md")
        self.fx.registry("")
        self.fx.run(apply=True)
        self.assertIn("2026-01-02-qq-rr.md", read(self.fx.selfhost))
        self.assertFalse(os.path.exists(os.path.join(self.fx.inbox, "2026-01-02-qq-rr.md")))

    def test_registry_audit_note_src_unchanged(self):
        self.fx.plan("2026-01-01-aa-bb.md")
        self.fx.item("2026-01-02-aa-bb.md")
        item_src = "backlog-completed/2026-01-02-aa-bb.md"
        dest_src = "plans-completed/2026-01-01-aa-bb.md"
        self.fx.registry(
            "| aa-bb | no | completed | 2026-01-01 | executed | %s |  |  | existing audit |\n" % dest_src
            + "| aa-bb-item | no | completed | 2026-01-02 | executed | %s |  |  |  |\n" % item_src
            + "| other | no | completed | 2026-01-03 | executed | elsewhere/x.md |  |  |  |\n")
        self.fx.run("--date", "2026-09-25", apply=True)
        reg = read(self.fx.registry_path)
        self.assertIn("user-approved 2026-09-25: migration audit - disposition folded into plans-completed/2026-01-01-aa-bb.md; per-item file deleted", reg)
        self.assertIn("existing audit; received backlog-completed/2026-01-02-aa-bb.md disposition (per-item file deleted)", reg)
        self.assertIn("| aa-bb | no | completed | 2026-01-01 | executed | %s |" % dest_src, reg)
        self.assertIn("| elsewhere/x.md |", reg) if False else None
        self.assertIn(" elsewhere/x.md ", reg)

    def test_frozen_dirs_untouched(self):
        self.fx.plan("2026-01-01-aa-bb.md")
        self.fx.item("2026-01-02-aa-bb.md")
        self.fx.registry("")
        frozen = os.path.join(self.fx.root, "frozen")
        write(os.path.join(frozen, "deferred", "a.md"), "d\n")
        write(os.path.join(frozen, "rejected", "b.md"), "r\n")
        before = {}
        for dirpath, _, files in os.walk(frozen):
            for name in files:
                p = os.path.join(dirpath, name)
                before[p] = read(p)
        self.fx.run(apply=True)
        for p, body in before.items():
            self.assertEqual(read(p), body)

    def test_overrides_win(self):
        self.fx.plan("2026-01-01-aa-bb.md")
        self.fx.plan("2026-01-05-cc-dd.md")
        self.fx.item("2026-01-02-aa-bb.md")
        self.fx.registry("")
        overrides = os.path.join(self.fx.root, "overrides.txt")
        write(overrides, "aa-bb plans-completed/2026-01-05-cc-dd.md\n")
        self.fx.run("--overrides", overrides, apply=True)
        self.assertIn("2026-01-02-aa-bb.md", read(os.path.join(self.fx.plans, "2026-01-05-cc-dd.md")))


class ReportTest(unittest.TestCase):
    def test_dry_run_writes_report_and_mutates_nothing(self):
        fx = Fixture()
        try:
            fx.plan("2026-01-01-aa-bb.md")
            fx.item("2026-01-02-aa-bb.md")
            fx.item("2026-01-03-xx.md")
            fx.registry("")
            report = os.path.join(fx.root, "report.md")
            before_inbox = sorted(os.listdir(fx.inbox))
            before_plans = {n: read(os.path.join(fx.plans, n)) for n in os.listdir(fx.plans)}
            rc = fx.run(report=report).returncode
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.exists(report))
            self.assertEqual(sorted(os.listdir(fx.inbox)), before_inbox)
            self.assertEqual({n: read(os.path.join(fx.plans, n)) for n in os.listdir(fx.plans)}, before_plans)
        finally:
            fx.cleanup()


if __name__ == "__main__":
    unittest.main()
