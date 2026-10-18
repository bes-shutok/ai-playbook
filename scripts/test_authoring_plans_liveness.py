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
    """Declaration group: fixed-string spans against the four skill files."""

    @staticmethod
    def read(path: Path) -> str:
        return path.read_text(encoding="utf-8")

    @staticmethod
    def assert_span(testcase: unittest.TestCase, span: str, text: str, where: str) -> None:
        # assertTrue with a short label: the four skill files are large, and
        # assertIn's failure message would echo the whole file into the log.
        testcase.assertTrue(span in text, f"missing span in {where}: {span}")

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
        plans = self.read(PLANS_SKILL)
        self.assert_span(self, "Authoring claim: <claim path> (session <session id>)", plans, "plans/SKILL.md")
        self.assert_span(self, "dropped at the certification commit", plans, "plans/SKILL.md")
        # the spans re-keyed to their post-split modules (the
        # maintenance-skill-size-refactor split; the router no longer carries
        # the Step 1/Step 2 operative text)
        guards = self.read(MAINTENANCE_GUARDS)
        self.assert_span(self, "(mid-round fold landings included, each through the same lock)", guards, "maintenance/guards.md")
        survey = self.read(MAINTENANCE_SURVEY_ARMS)
        self.assert_span(self, "Plans-root liveness probe", survey, "maintenance/survey-arms.md")

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
