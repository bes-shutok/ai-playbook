#!/usr/bin/env python3
"""Rejected plan and backlog archive lifecycle tests (plan Task 5, plus
the r1-F1 check-writes arm).

Covers the three ``RejectedArchiveLifecycleTest`` checkboxes of plan
``docs/plans/2026-09-23-ai-harness-friction-audit.md`` plus the
``check-writes`` test arm the r1 code review's F1 remediation adds:

- ``test_done_sweep_prunes_rejected_plan_deliverables``: a plan archived
  under the plans ``rejected/`` directory is excluded from the done
  sweep's readiness candidates and only its OWN ``plan-deliverables.txt``
  entries are pruned; a failing active plan's entry survives and a
  completed-dir entry keeps its existing archived pruning.
- ``test_rejected_plan_excluded_from_active_readiness``: a plan whose
  bytes sit under the plans ``rejected/`` directory is excluded from
  active-plan readiness even when its review sidecar is current and
  ready; the live copy at the top level still passes (control).
- ``test_rejected_archive_rows``: ownership-registry rows with
  ``state: rejected`` are accepted when they carry a real rejection
  date (``archived``) and a non-empty ``reason``; malformed metadata
  (missing date, non-date value, impossible calendar date, missing
  reason) is a HARD finding. An unknown state value stays HARD.
- ``test_check_writes_gates_rejected_archive_writes``: the registry
  write gate treats both rejected archives as frozen history — a body
  edit or deletion of a registered rejected row's src is a HARD
  unprotected write, the add/rename freeze move into either archive is
  the licensed lifecycle transition, and an unregistered archive path
  stays gated regardless of letter.

Hermeticity contract (mirrors test_done_sweep_gates_lib.py): every
fixture lives under mkdtemp with its own git repo and facts file; the
runtime home and user facts are redirected via ``DONE_SWEEP_RUNTIME_HOME``
and ``DONE_SWEEP_USER_FACTS`` so nothing touches the real ``~/.ai-playbook``;
no network.
"""

from __future__ import annotations

import io
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import doc_registry_validator as drv
import done_sweep_gates_lib as lib
import plan_readiness as pr

FACTS_BODY = (
    "```toml\n"
    'plans_dir = "docs/plans/"\n'
    'plans_completed_dir = "docs/plans/completed/"\n'
    'backlog_dir = "docs/history/backlog/"\n'
    'reviews_dir = "docs/reviews/"\n'
    'tmp_dir = "docs/tmp/"\n'
    "```\n"
)

REGISTRY_HEADER = (
    "| identity | sot | state | archived | reason | src | successor | aliases | audit |\n"
    "| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
)


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


class RejectedArchiveLifecycleTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        self.root.mkdir(parents=True)
        _git(self.root, "init", "-b", "main")
        _git(self.root, "config", "user.email", "fixture@example.invalid")
        _git(self.root, "config", "user.name", "fixture")
        (self.root / ".gitignore").write_text("__pycache__/\n/docs/\n", encoding="utf-8")
        (self.root / "README.md").write_text("fixture repo\n", encoding="utf-8")
        _git(self.root, "add", ".gitignore", "README.md")
        _git(self.root, "commit", "-m", "init", "-q")
        facts_dir = self.root / ".ai-playbook"
        facts_dir.mkdir(parents=True)
        (facts_dir / "facts.md").write_text(FACTS_BODY, encoding="utf-8")
        # Hermeticity: redirect the runtime home and user facts into the
        # fixture for the duration of each test.
        runtime_home = Path(self._tmp.name) / "runtime-home"
        runtime_home.mkdir()
        user_facts = Path(self._tmp.name) / "user-facts.md"
        user_facts.write_text("# fixture user facts\n", encoding="utf-8")
        self._saved_env = {
            key: os.environ.get(key)
            for key in ("DONE_SWEEP_RUNTIME_HOME", "DONE_SWEEP_USER_FACTS")
        }
        os.environ["DONE_SWEEP_RUNTIME_HOME"] = str(runtime_home)
        os.environ["DONE_SWEEP_USER_FACTS"] = str(user_facts)

    def tearDown(self) -> None:
        for key, value in self._saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    # ------------------------------------------------------------------
    # Fixture helpers
    # ------------------------------------------------------------------

    def _marker(self, epoch: float) -> Path:
        done_session = self.root / "docs" / "tmp" / "done-session"
        done_session.mkdir(parents=True, exist_ok=True)
        name = "run-start-" + datetime.fromtimestamp(
            epoch, tz=timezone.utc
        ).strftime("%Y%m%dT%H%M%SZ")
        marker = done_session / name
        marker.write_text(
            f"{int(epoch)} {self.root} {os.getpid()}\n", encoding="utf-8"
        )
        return marker

    def _write_deliverables(self, rel_paths: list[str]) -> Path:
        done_session = self.root / "docs" / "tmp" / "done-session"
        done_session.mkdir(parents=True, exist_ok=True)
        path = done_session / "plan-deliverables.txt"
        path.write_text("\n".join(rel_paths) + "\n", encoding="utf-8")
        return path

    def _read_deliverables(self) -> list[str]:
        path = self.root / "docs" / "tmp" / "done-session" / "plan-deliverables.txt"
        if not path.is_file():
            return []
        return [
            ln.strip()
            for ln in path.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.strip().startswith("#")
        ]

    def _write_stub_validator(self) -> Path:
        """Stub readiness validator: exit 0 only for plan paths with 'good'."""
        scripts = self.root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        stub = scripts / "plan_readiness.py"
        stub.write_text(
            "#!/usr/bin/env python3\n"
            "import sys\n"
            "plan = sys.argv[1] if len(sys.argv) > 1 else ''\n"
            "if 'good' in plan:\n"
            "    print('ready=yes')\n"
            "    sys.exit(0)\n"
            "print('readiness FAILED: stub rejection')\n"
            "sys.exit(1)\n",
            encoding="utf-8",
        )
        return stub

    def _write_registry(self, rows: str) -> Path:
        registry_dir = self.root / "docs" / "maintenance"
        registry_dir.mkdir(parents=True, exist_ok=True)
        registry = registry_dir / "document-registry.md"
        registry.write_text(REGISTRY_HEADER + rows, encoding="utf-8")
        return registry

    # ------------------------------------------------------------------
    # RejectedArchiveLifecycleTest#test_done_sweep_prunes_rejected_plan_deliverables
    # ------------------------------------------------------------------

    def test_done_sweep_prunes_rejected_plan_deliverables(self) -> None:
        """[class: REPOSITORY_TEST] A rejected plan's own deliverable
        entries are pruned and the plan never reaches the readiness gate;
        a failing active plan's entry survives and the completed-dir
        control keeps its existing archived pruning."""
        now = time.time()
        self._marker(now - 3600)  # previous run anchors the window
        self._marker(now)  # current run
        rejected_rel = "docs/plans/rejected/2026-09-20-rejected-plan.md"
        bad_rel = "docs/plans/2026-09-20-bad.md"
        completed_rel = "docs/plans/completed/2026-09-19-done-plan.md"
        for rel in (rejected_rel, bad_rel, completed_rel):
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("plan bytes\n", encoding="utf-8")
        self._write_deliverables([rejected_rel, bad_rel, completed_rel])
        self._write_stub_validator()

        ctx = lib.GateContext.discover(self.root)
        derivation = lib.derive_plan_readiness_candidates(ctx)
        candidate_rels = [str(p) for p in derivation.candidates]
        # The rejected and completed plans are excluded from gating; the
        # failing active plan stays the only candidate.
        self.assertEqual(candidate_rels, [bad_rel])
        archived_rels = {str(p) for p in derivation.archived}
        self.assertIn(rejected_rel, archived_rels)
        self.assertIn(completed_rel, archived_rels)

        result = lib.gate_plan_readiness(ctx)
        self.assertEqual(result.rc, 1, result.message)  # the bad plan failed
        self.assertIn("failed=1", result.message)
        remaining = self._read_deliverables()
        # ONLY the rejected plan's own entry was pruned (plus the completed
        # control's, per the unchanged completed behavior); the failing
        # active plan's entry survives for the next round.
        self.assertNotIn(rejected_rel, remaining)
        self.assertNotIn(completed_rel, remaining)
        self.assertEqual(remaining, [bad_rel])

    # ------------------------------------------------------------------
    # RejectedArchiveLifecycleTest#test_rejected_plan_excluded_from_active_readiness
    # ------------------------------------------------------------------

    def test_rejected_plan_excluded_from_active_readiness(self) -> None:
        """[class: REPOSITORY_TEST] A plan under the plans rejected/
        directory is excluded from active-plan readiness even with a
        current, ready review sidecar; the live top-level twin passes."""
        plans_dir = self.root / "docs" / "plans"
        reviews_dir = self.root / "docs" / "reviews"
        plans_dir.mkdir(parents=True, exist_ok=True)
        reviews_dir.mkdir(parents=True, exist_ok=True)
        live_plan, _review = pr._write_clean_state(plans_dir, reviews_dir)
        rejected_dir = plans_dir / "rejected"
        rejected_dir.mkdir(parents=True, exist_ok=True)
        rejected_plan = rejected_dir / live_plan.name
        rejected_plan.write_text(
            live_plan.read_text(encoding="utf-8"), encoding="utf-8"
        )

        ok, reason = pr.evaluate_readiness(rejected_plan, plans_dir, reviews_dir)
        self.assertFalse(ok, "a rejected-archive plan must not be active-ready")
        self.assertIsNotNone(reason)
        self.assertIn("rejected", reason.lower())

        # Control: the live copy at the top level still passes readiness.
        live_ok, live_reason = pr.evaluate_readiness(
            live_plan, plans_dir, reviews_dir
        )
        self.assertTrue(live_ok, live_reason)

    # ------------------------------------------------------------------
    # RejectedArchiveLifecycleTest#test_rejected_archive_rows
    # ------------------------------------------------------------------

    def test_rejected_archive_rows(self) -> None:
        """[class: REPOSITORY_TEST] Valid rejected archive rows for a plan
        and a backlog item are accepted; malformed metadata (missing or
        non-date rejection date, impossible calendar date, missing
        reason) is rejected; an unknown state value stays HARD."""
        cfg = drv.resolve_config(self.root)

        def validate(rows: str) -> tuple[int, str]:
            self._write_registry(rows)
            out = io.StringIO()
            code = drv.cmd_validate(self.root, cfg, out)
            return code, out.getvalue()

        # Valid plan and backlog rejected rows are accepted.
        valid_rows = (
            "| rejected-plan-a | no | rejected | 2026-09-23 | "
            "decided against: scope folded into the active audit plan | "
            "docs/plans/rejected/2026-09-20-plan-a.md |  |  |  |\n"
            "| rejected-backlog-b | no | rejected | 2026-09-22 | "
            "decided against: duplicates the completed work | "
            "docs/history/backlog/rejected/2026-09-19-b.md |  |  |  |\n"
            "| living-c | yes | living |  |  | docs/maintenance/living.md |  |  |  |\n"
        )
        code, out = validate(valid_rows)
        self.assertEqual(code, 0, out)
        self.assertIn("0 hard finding", out)

        # Malformed: missing rejection date.
        code, out = validate(
            "| rejected-plan-a | no | rejected |  | "
            "decided against: scope folded into the active audit plan | "
            "docs/plans/rejected/2026-09-20-plan-a.md |  |  |  |\n"
        )
        self.assertEqual(code, 1, out)
        self.assertIn("HARD", out)

        # Malformed: non-date rejection date.
        code, out = validate(
            "| rejected-plan-a | no | rejected | soon | "
            "decided against: scope folded into the active audit plan | "
            "docs/plans/rejected/2026-09-20-plan-a.md |  |  |  |\n"
        )
        self.assertEqual(code, 1, out)
        self.assertIn("HARD", out)

        # Malformed: impossible calendar date.
        code, out = validate(
            "| rejected-plan-a | no | rejected | 2026-13-45 | "
            "decided against: scope folded into the active audit plan | "
            "docs/plans/rejected/2026-09-20-plan-a.md |  |  |  |\n"
        )
        self.assertEqual(code, 1, out)
        self.assertIn("HARD", out)

        # Malformed: missing rejection reason.
        code, out = validate(
            "| rejected-backlog-b | no | rejected | 2026-09-22 |  | "
            "docs/history/backlog/rejected/2026-09-19-b.md |  |  |  |\n"
        )
        self.assertEqual(code, 1, out)
        self.assertIn("HARD", out)

        # Control: an unknown state value stays a HARD enum finding.
        code, out = validate(
            "| archived-c | no | archived | 2026-09-22 |  | "
            "docs/plans/completed/2026-09-19-c.md |  |  |  |\n"
        )
        self.assertEqual(code, 1, out)
        self.assertIn("invalid state value", out)

    # ------------------------------------------------------------------
    # RejectedArchiveLifecycleTest#test_check_writes_gates_rejected_archive_writes
    # ------------------------------------------------------------------

    def test_check_writes_gates_rejected_archive_writes(self) -> None:
        """[class: REPOSITORY_TEST] The registry write gate enforces the
        rejected-archive permanence contract both READMEs state: a body
        edit (M) or deletion (D) of a registered rejected row's src under
        either archive dir is a HARD unprotected write, while the
        add/rename freeze move into either archive (A/R) is the licensed
        lifecycle transition; an unregistered path under an archive dir
        stays gated even with a licensed letter."""
        cfg = drv.resolve_config(self.root)
        self._write_registry(
            "| rejected-plan-a | no | rejected | 2026-09-23 | "
            "decided against: scope folded into the active audit plan | "
            "docs/plans/rejected/2026-09-20-plan-a.md |  |  |  |\n"
            "| rejected-backlog-b | no | rejected | 2026-09-22 | "
            "decided against: duplicates the completed work | "
            "docs/history/backlog/rejected/2026-09-19-b.md |  |  |  |\n"
        )

        def check(entries: list[tuple[str, str]]) -> tuple[int, str]:
            out = io.StringIO()
            code = drv.cmd_check_writes(self.root, cfg, entries, out)
            return code, out.getvalue()

        # HARD: a body edit of a rejected plan record under the plans
        # archive (the exact accident class docs/plans/rejected/README.md
        # forbids: "Never delete the rejection record to make room").
        code, out = check(
            [("docs/plans/rejected/2026-09-20-plan-a.md", "M ")]
        )
        self.assertEqual(code, 1, out)
        self.assertIn(
            "HARD immutable path written without override:"
            " docs/plans/rejected/2026-09-20-plan-a.md",
            out,
        )
        self.assertIn("change type M;", out)

        # HARD: a deletion of a rejected backlog record under the
        # backlog archive.
        code, out = check(
            [("docs/history/backlog/rejected/2026-09-19-b.md", "D")]
        )
        self.assertEqual(code, 1, out)
        self.assertIn(
            "HARD immutable path written without override:"
            " docs/history/backlog/rejected/2026-09-19-b.md",
            out,
        )

        # Licensed: the freeze move INTO each archive passes for the
        # registered rejected srcs (clean porcelain add, name-status
        # rename).
        code, out = check(
            [("docs/plans/rejected/2026-09-20-plan-a.md", "A ")]
        )
        self.assertEqual(code, 0, out)
        self.assertIn("licensed lifecycle add", out)
        code, out = check(
            [("docs/history/backlog/rejected/2026-09-19-b.md", "R100")]
        )
        self.assertEqual(code, 0, out)
        self.assertIn("licensed lifecycle add", out)

        # HARD: an unregistered path under an archive dir stays gated
        # even with a licensed letter (no registered row, no exemption).
        code, out = check(
            [("docs/plans/rejected/2026-09-21-unregistered.md", "A ")]
        )
        self.assertEqual(code, 1, out)
        self.assertIn("HARD immutable path written without override", out)


if __name__ == "__main__":
    unittest.main()
