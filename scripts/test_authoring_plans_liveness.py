#!/usr/bin/env python3
"""Selftest for the authoring round liveness contract (stdlib unittest).

Two test groups (the authoring-round-liveness-gap plan, Task 1):

- PlansLivenessProbeTest: behavioral fixtures over a temp git repository,
  exercising scripts/check_authoring_plans_liveness.py end to end. Every
  fixture builds inside its own mktemp -d directory with an explicit
  teardown, never inside the repository this file lives in.
- LivenessDeclarationTest: fixed-string span assertions against the four
  skill files that carry the authoring-round liveness duties. The probe
  script itself is exercised by the behavior group, not span-asserted.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE = REPO_ROOT / "scripts" / "check_authoring_plans_liveness.py"

PROMPT_TEMPLATES = REPO_ROOT / "agents" / "skills" / "maintenance" / "prompt-templates.md"
PLANS_SKILL = REPO_ROOT / "agents" / "skills" / "plans" / "SKILL.md"
MAINTENANCE_SKILL = REPO_ROOT / "agents" / "skills" / "maintenance" / "SKILL.md"
MAINTENANCE_GUARDS = REPO_ROOT / "agents/skills/maintenance/guards.md"
MAINTENANCE_SURVEY_ARMS = REPO_ROOT / "agents/skills/maintenance/survey-arms.md"
MAINTENANCE_TEMPLATE_AUTHORING = REPO_ROOT / "agents/skills/maintenance/template-authoring.md"
# Re-aimed 2026-10-11 (the done target-state flip; the dissolved sweep-gates
# modules' in-session duty texts live in the collapsed done SKILL.md).
DONE_SKILL = REPO_ROOT / "agents" / "skills" / "done" / "SKILL.md"

PLANS_DIR = "docs/history/plans"
CLAIMS_DIR = "docs/tmp/authoring-claims"

SLUG = "demo-plan"
PLAN_BASENAME = "2026-10-05-" + SLUG + ".md"


def iso_minutes_ago(minutes: int) -> str:
    """ISO timestamp with offset, the given number of minutes in the past."""
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()


def write_claim(repo: Path, name: str, updated: str, naming_line: str, session: str = "sess-fixture-1") -> None:
    """Write one authoring claim file in the duty's four-frontmatter-line shape.

    ``naming_line`` is a body line carrying the plan reference (the text the
    probe's slug-or-basename containment matching reads).
    """
    claims = repo / CLAIMS_DIR
    claims.mkdir(parents=True, exist_ok=True)
    body = (
        f"session: {session}\n"
        "item: docs/history/backlog/demo-item.md\n"
        f"created: {updated}\n"
        f"updated: {updated}\n"
        f"{naming_line}\n"
    )
    (claims / name).write_text(body, encoding="utf-8")


class PlansLivenessProbeTest(unittest.TestCase):
    """Behavioral group: each fixture lives in a temp dir, never in this repo."""

    def setUp(self) -> None:
        self.base = Path(tempfile.mkdtemp(prefix="liveness-fixture-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.base, ignore_errors=False)

    def make_repo(self, name: str) -> Path:
        repo = self.base / name
        repo.mkdir()
        subprocess.run(
            ["git", "init", "-q", str(repo)], capture_output=True, text=True, check=True
        )
        (repo / PLANS_DIR).mkdir(parents=True)
        return repo

    def add_plan(self, repo: Path, basename: str = PLAN_BASENAME) -> Path:
        plan = repo / PLANS_DIR / basename
        plan.write_text(f"# Plan: {basename}\n", encoding="utf-8")
        return plan

    def run_probe(self, repo: Path) -> subprocess.CompletedProcess:
        if not PROBE.exists():
            raise FileNotFoundError(f"probe script missing: {PROBE}")
        return subprocess.run(
            [sys.executable, str(PROBE), "--repo", str(repo)],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_fresh_claim_classifies_live(self) -> None:
        repo = self.make_repo("fresh")
        plan = self.add_plan(repo)
        write_claim(
            repo,
            "demo-item.md",
            iso_minutes_ago(5),
            f"plan: {PLANS_DIR}/{PLAN_BASENAME}",
        )
        proc = self.run_probe(repo)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        lines = proc.stdout.splitlines()
        live = [line for line in lines if line.startswith("live:")]
        self.assertTrue(live, proc.stdout)
        self.assertIn(f"{PLANS_DIR}/{PLAN_BASENAME}", live[0])
        self.assertIn("demo-item.md", live[0])
        self.assertEqual(lines[-1], "OUTCOME: pass", proc.stdout)

    def test_no_claim_classifies_stranded(self) -> None:
        repo = self.make_repo("noclaim")
        plan = self.add_plan(repo)
        proc = self.run_probe(repo)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        lines = proc.stdout.splitlines()
        stranded = [line for line in lines if line.startswith("stranded:")]
        self.assertTrue(stranded, proc.stdout)
        self.assertIn(f"{PLANS_DIR}/{PLAN_BASENAME}", stranded[0])
        self.assertEqual(lines[-1], "OUTCOME: fail", proc.stdout)

    def test_stale_claim_classifies_stranded(self) -> None:
        repo = self.make_repo("stale")
        plan = self.add_plan(repo)
        write_claim(
            repo,
            "demo-item.md",
            iso_minutes_ago(180),
            f"plan: {PLANS_DIR}/{PLAN_BASENAME}",
        )
        proc = self.run_probe(repo)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        lines = proc.stdout.splitlines()
        stranded = [line for line in lines if line.startswith("stranded:")]
        self.assertTrue(stranded, proc.stdout)
        self.assertIn(f"{PLANS_DIR}/{PLAN_BASENAME}", stranded[0])
        self.assertEqual(lines[-1], "OUTCOME: fail", proc.stdout)

    def test_liveness_directory_candidates(self) -> None:
        """Directory candidates (the plan-directory-shape plan, Task 4): an
        untracked plan directory classifies live with a fresh claim on the
        slug and stranded without, reported at its charter path; a
        charterless untracked directory reports stranded naming the
        charterless reason."""
        charter_rel = f"{PLANS_DIR}/2026-10-08-demo-dir/PLAN.md"

        def add_directory_plan(repo: Path, charter: bool) -> None:
            plan_dir = repo / PLANS_DIR / "2026-10-08-demo-dir"
            (plan_dir / "tasks").mkdir(parents=True)
            if charter:
                (plan_dir / "PLAN.md").write_text(
                    "# Plan: demo dir\n", encoding="utf-8"
                )
            (plan_dir / "tasks" / "01-first.md").write_text(
                "### Task 1: first\n", encoding="utf-8"
            )

        # live: a fresh claim names the directory slug (date prefix stripped).
        live_repo = self.make_repo("dir-live")
        add_directory_plan(live_repo, charter=True)
        write_claim(
            live_repo, "demo-dir.md", iso_minutes_ago(5), "target slug: demo-dir"
        )
        live_proc = self.run_probe(live_repo)
        self.assertEqual(live_proc.returncode, 0, live_proc.stdout + live_proc.stderr)
        live_lines = [
            line for line in live_proc.stdout.splitlines() if line.startswith("live:")
        ]
        self.assertTrue(live_lines, live_proc.stdout)
        self.assertIn(charter_rel, live_lines[0])
        self.assertIn("demo-dir.md", live_lines[0])
        self.assertEqual(live_proc.stdout.splitlines()[-1], "OUTCOME: pass")

        # stranded: the same untracked directory with no claim naming it.
        stranded_repo = self.make_repo("dir-stranded")
        add_directory_plan(stranded_repo, charter=True)
        stranded_proc = self.run_probe(stranded_repo)
        self.assertEqual(
            stranded_proc.returncode, 1, stranded_proc.stdout + stranded_proc.stderr
        )
        stranded_lines = [
            line
            for line in stranded_proc.stdout.splitlines()
            if line.startswith("stranded:")
        ]
        self.assertTrue(stranded_lines, stranded_proc.stdout)
        self.assertIn(charter_rel, stranded_lines[0])
        self.assertEqual(stranded_proc.stdout.splitlines()[-1], "OUTCOME: fail")

        # charterless: tasks files but no charter -> stranded naming the reason.
        bare_repo = self.make_repo("dir-charterless")
        add_directory_plan(bare_repo, charter=False)
        bare_proc = self.run_probe(bare_repo)
        self.assertEqual(bare_proc.returncode, 1, bare_proc.stdout + bare_proc.stderr)
        bare_lines = [
            line
            for line in bare_proc.stdout.splitlines()
            if line.startswith("stranded:")
        ]
        self.assertTrue(bare_lines, bare_proc.stdout)
        self.assertIn(f"{PLANS_DIR}/2026-10-08-demo-dir/", bare_lines[0])
        self.assertIn("charterless", bare_lines[0])
        self.assertEqual(bare_proc.stdout.splitlines()[-1], "OUTCOME: fail")

    def test_state_subdirectories_never_enumerated(self) -> None:
        repo = self.make_repo("statedirs")
        completed = repo / PLANS_DIR / "completed"
        completed.mkdir(parents=True)
        (completed / "2026-09-01-archived-plan.md").write_text(
            "# archived\n", encoding="utf-8"
        )
        proc = self.run_probe(repo)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertNotIn("live:", proc.stdout)
        self.assertNotIn("stranded:", proc.stdout)
        self.assertNotIn("2026-09-01-archived-plan.md", proc.stdout + proc.stderr)
        self.assertIn("candidates=0", proc.stdout)
        self.assertEqual(proc.stdout.splitlines()[-1], "OUTCOME: pass", proc.stdout)

    def test_witnessed_shapes_classify_live(self) -> None:
        # The two 2026-10-04 instances: in each, the claim is created minutes
        # before its plan file appears and its updated: stays fresh.
        repo_one = self.make_repo("witness-one")
        self.add_plan(repo_one, "2026-10-04-operator-flare-shape.md")
        write_claim(
            repo_one,
            "operator-flare-shape.md",
            iso_minutes_ago(3),
            "plan: 2026-10-04-operator-flare-shape.md",
        )
        proc_one = self.run_probe(repo_one)
        self.assertEqual(proc_one.returncode, 0, proc_one.stdout + proc_one.stderr)
        self.assertTrue(
            any(
                line.startswith("live:")
                and "2026-10-04-operator-flare-shape.md" in line
                for line in proc_one.stdout.splitlines()
            ),
            proc_one.stdout,
        )

        repo_two = self.make_repo("witness-two")
        self.add_plan(repo_two, "2026-10-04-primary-round-shape.md")
        # Slug-only naming arm: the claim text carries the stripped slug.
        write_claim(
            repo_two,
            "primary-round-shape.md",
            iso_minutes_ago(1),
            "target slug: primary-round-shape",
        )
        proc_two = self.run_probe(repo_two)
        self.assertEqual(proc_two.returncode, 0, proc_two.stdout + proc_two.stderr)
        self.assertTrue(
            any(
                line.startswith("live:")
                and "2026-10-04-primary-round-shape.md" in line
                for line in proc_two.stdout.splitlines()
            ),
            proc_two.stdout,
        )


class LivenessDeclarationTest(unittest.TestCase):
    """Declaration group: fixed-string spans against the four skill files.

    Pinned surface: the operative body paragraphs of the target files. The
    scheduled-payload mirror paragraph in template-authoring.md is out of the
    pinned contract; only the body AUTHORING CLAIM paragraph is asserted.
    """

    @staticmethod
    def read(path: Path) -> str:
        return path.read_text(encoding="utf-8")

    @staticmethod
    def assert_span(testcase: unittest.TestCase, span: str, text: str, where: str) -> None:
        # assertTrue with a short label: the four skill files are large, and
        # assertIn's failure message would echo the whole file into the log.
        testcase.assertTrue(span in text, f"missing span in {where}: {span}")

    @staticmethod
    def assert_absent(testcase: unittest.TestCase, span: str, text: str, where: str) -> None:
        testcase.assertTrue(span not in text, f"forbidden span in {where}: {span}")

    def test_heartbeat_milestones_declared(self) -> None:
        text = self.read(MAINTENANCE_TEMPLATE_AUTHORING)
        self.assert_span(self, "at every review-record write while a round is in flight", text, "template-authoring.md")
        self.assert_span(
            self,
            "at every mechanical gate pass (the pre-round gates, the certification commit, the readiness gate)",
            text,
            "template-authoring.md",
        )

    def test_marker_and_reconciliation_declared(self) -> None:
        # Re-aimed 2026-10-22 (the marker-lifetime reconciliation plan,
        # Task 1): the header marker is permanent provenance through
        # certification, landing, and archival; the contract rejects
        # certification-time removal wording and any claim that the probe
        # reads the plan header (it matches fresh claim-file text instead).
        plans = self.read(PLANS_SKILL)
        self.assert_span(self, "Authoring claim: <claim path> (session <session id>)", plans, "plans/SKILL.md")
        self.assert_span(self, "permanent provenance once written", plans, "plans/SKILL.md")
        self.assert_span(self, "remains unchanged through certification, landing, and archival", plans, "plans/SKILL.md")
        self.assert_span(self, "never reads the plan header", plans, "plans/SKILL.md")
        self.assert_span(self, "fresh claim-file text", plans, "plans/SKILL.md")
        for forbidden in (
            "dropped at the certification commit",
            "The line is dropped",
            "probe reads the marker",
            "probe reads the plan header",
        ):
            self.assert_absent(self, forbidden, plans, "plans/SKILL.md")
        # The canonical marker-lifetime rule lives in the template's AUTHORING
        # CLAIM procedure; this span pins that home so the plans skill's
        # pointer cannot silently dangle.
        template = self.read(MAINTENANCE_TEMPLATE_AUTHORING)
        self.assert_span(self, "remaining unchanged through certification, landing, and archival", template, "template-authoring.md")
        # the spans re-keyed to their post-split modules (the
        # maintenance-skill-size-refactor split; the router no longer carries
        # the Step 1/Step 2 operative text)
        guards = self.read(MAINTENANCE_GUARDS)
        self.assert_span(self, "(mid-round fold landings included, each through the same lock)", guards, "maintenance/guards.md")
        survey = self.read(MAINTENANCE_SURVEY_ARMS)
        self.assert_span(self, "Plans-root liveness probe", survey, "maintenance/survey-arms.md")

    def test_claim_deletion_boundaries_declared(self) -> None:
        # Added 2026-10-22 (the closeout-lifecycle plan, Task 2): the
        # template's AUTHORING CLAIM procedure owns the placement-specific
        # deletion boundaries, refusal retention with its duplicate-origin
        # carve-out, and the ownership-checked stand-down; the plans skill
        # invokes that procedure and scopes its completion evidence per
        # placement. Fixed-string text-contract pins, not runtime deletion
        # proof.
        template = self.read(MAINTENANCE_TEMPLATE_AUTHORING)
        # Separate worktree and primary success boundaries.
        self.assert_span(
            self,
            "under worktree placement the delete fires only after the closeout's verified done migration, the owned-files-clean preflight passing, a passing gate-removal result, and the authoring-branch removal",
            template,
            "template-authoring.md",
        )
        self.assert_span(
            self,
            "under primary-checkout placement the delete fires after the verified done commits and the plan and review artifact state at their primary homes",
            template,
            "template-authoring.md",
        )
        self.assert_span(
            self,
            "with no worktree-only landing, owned-files-clean, gate-removal, or branch-removal gate in that placement",
            template,
            "template-authoring.md",
        )
        # Ordinary refusal retention, the unverifiable-primary arm, and the
        # duplicate-origin carve-out that deletes the claim while the branch
        # and worktree stay standing.
        self.assert_span(
            self,
            "an ordinary worktree landing or artifact-migration refusal keeps the claim standing beside the worktree and branch",
            template,
            "template-authoring.md",
        )
        self.assert_span(
            self,
            "an unverifiable primary-placement closeout keeps the claim standing until its done commits and artifact state verify",
            template,
            "template-authoring.md",
        )
        self.assert_span(
            self,
            "the duplicate-origin coverage-gate refusal (the duplicate-origin coverage gate's exit 1 naming the covering plan): that specific refusal deletes this session's owned claim while the worktree and branch stay standing for recovery",
            template,
            "template-authoring.md",
        )
        # Owned stand-down: the current-session identity check, its required
        # read-before-delete order, and preservation of foreign, missing, or
        # unreadable identities observed at that read.
        self.assert_span(
            self,
            "before every updated: refresh and before each delete ordered below, re-read the claim file and mutate it only while its session: line still names this session's id",
            template,
            "template-authoring.md",
        )
        self.assert_span(
            self,
            "a session: line that is absent or unparseable at that read is treated as foreign, left in place and reported",
            template,
            "template-authoring.md",
        )
        self.assert_span(
            self,
            "a claim file missing or unreadable at a delete's final identity read is preserved and reported the same way",
            template,
            "template-authoring.md",
        )
        self.assert_span(
            self,
            "a foreign id means another session took the item mid-run: leave the file untouched and report it",
            template,
            "template-authoring.md",
        )
        # The non-atomicity statement: the check-then-unlink is best-effort
        # against stale takeover and gives no ownership guarantee after the
        # read.
        self.assert_span(
            self,
            "best-effort and not atomic with stale takeover",
            template,
            "template-authoring.md",
        )
        self.assert_span(
            self,
            "no ownership guarantee extends past it",
            template,
            "template-authoring.md",
        )
        # The plans skill: placement-scoped completion evidence, tracked
        # freeze retained for both placements, and the closeout sequence
        # invoking the template-owned procedure without restating claim
        # policy.
        plans = self.read(PLANS_SKILL)
        self.assert_span(
            self,
            "the boundary evidence for the session's placement",
            plans,
            "plans/SKILL.md",
        )
        self.assert_span(
            self,
            "Worktree placement: the owned-files-clean preflight, the gate-removal invocation ending `OUTCOME: pass`, the authoring branch removed with no live worktree or run naming it",
            plans,
            "plans/SKILL.md",
        )
        self.assert_span(
            self,
            "Primary-checkout placement: the verified `done` commits and the plan and review artifact state at their primary homes, with no owned-files-clean, gate-removal, or branch-removal evidence",
            plans,
            "plans/SKILL.md",
        )
        self.assert_span(
            self,
            "Both placements also verify the tracked freeze",
            plans,
            "plans/SKILL.md",
        )
        # Primary-placement freeze arm: a non-default-branch primary run reads
        # the freeze on its own branch per the Entry freeze placement clause.
        self.assert_span(
            self,
            "on a primary-placement run whose current branch is not the default branch, the freeze reads on that run's branch per the Entry freeze paragraph's placement clause",
            plans,
            "plans/SKILL.md",
        )
        self.assert_span(
            self,
            "run the AUTHORING CLAIM procedure's placement-matched deletion from `agents/skills/maintenance/template-authoring.md` as the closeout's claim step",
            plans,
            "plans/SKILL.md",
        )

    def test_done_gate_declared(self) -> None:
        text = self.read(DONE_SKILL)
        self.assert_span(
            self,
            "plans-root liveness (a session-level conditional gate the runner does not execute; apply it in-session per its bullet below before continuing)",
            text,
            "done/SKILL.md",
        )
        self.assert_span(self, "check_authoring_plans_liveness.py", text, "done/SKILL.md")

    def test_preserved_anchors_stay_pinned(self) -> None:
        self.assert_span(
            self,
            "immediately when a review round returns",
            self.read(MAINTENANCE_TEMPLATE_AUTHORING),
            "template-authoring.md",
        )
        self.assert_span(
            self,
            "plans-archive-twin",
            self.read(DONE_SKILL),
            "done/SKILL.md",
        )
        self.assert_span(
            self,
            "lands via its own merge-lock-serialized self-landing onto the default branch from its ad-hoc worktree",
            self.read(MAINTENANCE_GUARDS),
            "maintenance/guards.md",
        )


if __name__ == "__main__":
    unittest.main()
