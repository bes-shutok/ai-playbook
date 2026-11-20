#!/usr/bin/env python3
"""Hermetic fixture suite for scripts/reconcile_execute_plan_handoff.py.

Every fixture builds its own throwaway primary checkout (a scratch ``git
init`` repository is its own primary checkout, the same fabrication the
execution-claim suite uses) with a two-task plan, a staged plan-review pair,
an execution claim, and a done-pending ``runtime_state.json``. The admission
matrix drives the helper through the CLI as a subprocess; the between-reads
drift and atomic-write seams run in-process against the module so the
interrupted-write guarantees are observable. No live ``docs/tmp/`` state;
every refusal path asserts unchanged manifest bytes and an unchanged
accepted worker terminal receipt.
"""

from __future__ import annotations

import contextlib
import errno
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import reconcile_execute_plan_handoff as recon  # noqa: E402
import fix_plan_em_dashes as plan_fixer  # noqa: E402

RECONCILE_SCRIPT = os.path.join(SCRIPTS_DIR, "reconcile_execute_plan_handoff.py")


def clean_python_environment() -> dict[str, str]:
    env = os.environ.copy()
    for name in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONUSERBASE"):
        env.pop(name, None)
    # Git's repository-selection variables override ``git -C <fixture>`` and
    # can redirect CLI integration tests into the caller's real checkout.
    for name in tuple(env):
        if name.startswith("GIT_"):
            env.pop(name, None)
    return env

SESSION = "fixture-session-0f3e"
RUN_SESSION_ID = "run-fixture-0f3e"
PLAN_REL = "docs/history/plans/2026-10-01-recon-fixture-story.md"
PLAN_SLUG = "recon-fixture-story"
ARTIFACT_SLUG = "recon-fixture-story"
STATE_REL = "docs/tmp/execute-plan/2026-10-01-recon-fixture-story/runtime_state.json"
REVIEW_BASE = ".ai-playbook/reviews/2026-10-01-plan-review-recon-fixture-story"

PLAN_TEXT_LAUNCH = """# Plan: Reconciliation fixture story

## Terms

- Fixture term: the launched scope digest normalizes the checkbox markers only.

## Tasks

### Task 1: First fixture task

Files:
- scripts/example_one.py

- [ ] First clause for task one.
- [ ] Second clause for task one.

### Task 2: Second fixture task

Files:
- scripts/example_two.py

- [ ] First clause for task two.
"""

WORKER_RECEIPT_ONE = {
    "status": "success",
    "evidence": ["scripts/example_one.py"],
    "selected_tests": ["scripts/test_example_one.py::test_first_clause"],
    "validation": [{"command": "pytest scripts/test_example_one.py -q", "exit": 0}],
}
WORKER_RECEIPT_TWO = {
    "status": "success",
    "evidence": ["scripts/example_two.py"],
    "selected_tests": ["scripts/test_example_two.py::test_second_clause"],
}

# The fixture's initial on-disk plan: task one's completion was marked after
# launch (the Step 1.3 shape), so the reviewed bytes bind the reconcilable
# projection while the launch scopes stay the unchecked-byte scopes (marker
# normalization keeps the scope digest stable across the marking).
PLAN_TEXT_MARKED = (
    PLAN_TEXT_LAUNCH
    .replace("- [ ] First clause for task one.", "- [x] First clause for task one.")
    .replace("- [ ] Second clause for task one.", "- [x] Second clause for task one.")
)

DONE_STATUSES = ("complete", "checkpointed", "deferred")


def canonical_digest(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def task_section(plan_text: str, task_number: int) -> str:
    return recon._extract_task_section(plan_text, task_number)


class RunFixture:
    """One throwaway primary checkout holding a done-pending task-one run.

    The fixture starts at the launch state: the staged review pair, the
    claim, and the runtime state all bind the launch plan bytes; helpers
    rewrite individual surfaces for each regression.
    """

    def __init__(self) -> None:
        self._tmp = tempfile.mkdtemp(prefix="recon-handoff-fixture-")
        # Canonicalize: the repo-root fences and identity comparisons resolve
        # the root, and the macOS temp parent is a symlink.
        self.root = Path(self._tmp).resolve()
        self._null_config = self.root / ".gitconfig-null"
        self._null_config.write_text("", encoding="utf-8")
        self._git("init", "-q")
        self._git("config", "user.email", "fixture@example.invalid")
        self._git("config", "user.name", "Fixture")
        self._git("commit", "--allow-empty", "-q", "-m", "init")
        self.launch_scope_one = recon.task_scope_digest(task_section(PLAN_TEXT_LAUNCH, 1))
        self.launch_scope_two = recon.task_scope_digest(task_section(PLAN_TEXT_LAUNCH, 2))
        self.plan_path = self.root / PLAN_REL
        self.plan_path.parent.mkdir(parents=True)
        self.plan_path.write_text(PLAN_TEXT_MARKED, encoding="utf-8")
        self.state_path = self.root / STATE_REL
        self.state_path.parent.mkdir(parents=True)
        self.claim_path = self.root / "docs" / "tmp" / "execution-claims" / f"{ARTIFACT_SLUG}.md"
        self.claim_path.parent.mkdir(parents=True)
        self.write_claim()
        self.write_review(1, self.plan_digest())
        self.write_state()
        # One initial commit only: the run's own work stays uncommitted, so
        # the done commit gate stays observable as a commit-count delta.

    # -- lifecycle ---------------------------------------------------------- #

    def cleanup(self) -> None:
        shutil.rmtree(self._tmp, True)

    def _git(self, *args: str) -> None:
        subprocess.run(
            ["git", "-C", str(self.root), *args],
            check=True,
            capture_output=True,
            timeout=60,
            env=self.subprocess_env(),
        )

    def subprocess_env(self) -> dict:

        env = clean_python_environment()
        fixture_home = Path(self._tmp) / "home"
        fixture_home.mkdir(exist_ok=True)
        env["HOME"] = str(fixture_home)
        env["LC_ALL"] = "C"
        env["LANG"] = "C"
        env["TZ"] = "UTC"
        env["GIT_CONFIG_GLOBAL"] = str(self._null_config)
        env["GIT_CONFIG_SYSTEM"] = str(self._null_config)
        return env


    # -- surface writers ------------------------------------------------------ #

    def write_claim(self, session: str = SESSION, plan_line: str = PLAN_REL) -> None:
        self.claim_path.write_text(
            f"session: {session}\nplan: {plan_line}\ncreated: fixture\nupdated: fixture\n",
            encoding="utf-8",
        )

    def remove_claim(self) -> None:
        self.claim_path.unlink()

    def write_review(self, round_no: int, digest: str, verdict: str = "yes") -> None:
        record = self.root / f"{REVIEW_BASE}-r{round_no}.md"
        record.parent.mkdir(parents=True, exist_ok=True)
        sidecar = self.root / f"{REVIEW_BASE}-r{round_no}.stats.json"
        record.write_text(
            f"# Plan Review: recon fixture round r{round_no}\n\n"
            "## Summary\n\n"
            f"Verdict: ready={verdict}.\n",
            encoding="utf-8",
        )
        payload = {
            "schema_version": 1,
            "review_type": "Plan Review",
            "date": "2026-10-01",
            "artifact_slug": ARTIFACT_SLUG,
            "round": f"r{round_no}",
            "source_kind": "plan",
            "source_digest": digest,
            "verdict": verdict,
            "extensions": {"plan_identity": PLAN_REL},
        }
        sidecar.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def latest_sidecar(self) -> dict:
        rounds = sorted(self.root.glob(f"{REVIEW_BASE}-r*.stats.json"))
        path = rounds[-1]
        return json.loads(path.read_text(encoding="utf-8"))

    def base_state(self) -> dict:
        return {
            "plan_slug": PLAN_SLUG,
            "plan_digest": self.plan_digest(),
            "generation": 7,
            "run_session_id": RUN_SESSION_ID,
            "workflow_state": "running",
            "tasks": {
                "1": {
                    "status": "done-pending",
                    "checkbox": False,
                    "terminal_receipt": dict(WORKER_RECEIPT_ONE),
                },
                "2": {"status": "pending", "checkbox": False},
            },
        }

    def write_state(self, state: dict | None = None) -> None:
        payload = state if state is not None else self.base_state()
        self.state_path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    def mutate_state(self, mutator) -> None:
        state = self.read_state()
        mutator(state)
        self.write_state(state)

    # -- readers ----------------------------------------------------------------- #

    def plan_digest(self) -> str:
        return hashlib.sha256(self.plan_path.read_bytes()).hexdigest()

    def read_state(self) -> dict:
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def state_bytes(self) -> bytes:
        return self.state_path.read_bytes()

    def worker_receipt_digest(self, key: str = "1") -> str:
        record = self.read_state()["tasks"][key]
        return canonical_digest(record.get("terminal_receipt"))

    def capture(self) -> dict:
        """The preservation witness: manifest bytes plus the accepted worker
        terminal receipt digest."""
        return {"bytes": self.state_bytes(), "worker": self.worker_receipt_digest("1")}

    def commit_count(self) -> int:
        result = subprocess.run(
            ["git", "-C", str(self.root), "rev-list", "--count", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
            env=self.subprocess_env(),
        )
        return int(result.stdout.strip())

    # -- invocations ---------------------------------------------------------------- #

    def make_reconciler(self, **overrides) -> recon.HandoffReconciler:
        parameters = {
            "state_path": self.state_path,
            "plan_path": self.plan_path,
            "task_number": 1,
            "session": SESSION,
            "repo_root": self.root,
        }
        parameters.update(overrides)
        return recon.HandoffReconciler(**parameters)

    def run_cli(
        self,
        *,
        command: str = "reconcile",
        task: int = 1,
        session: str = SESSION,
        state: Path | None = None,
        plan: Path | None = None,
        timeout: float = 120,
    ) -> subprocess.CompletedProcess:
        state_path = Path(state or self.state_path)
        before_state = state_path.read_bytes()
        process = subprocess.run(
            [
                os.path.abspath(sys.executable),
                RECONCILE_SCRIPT,
                command,
                "--state",
                str(state or self.state_path),
                "--plan",
                str(plan or self.plan_path),
                "--task",
                str(task),
                "--session",
                session,
                "--repo-root",
                str(self.root),
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=self.subprocess_env(),
        )
        process.fixture_state_snapshot = (state_path, before_state)
        return process

    @staticmethod
    def parse_result(process: subprocess.CompletedProcess) -> dict:
        return json.loads(process.stdout.splitlines()[0])

    @staticmethod
    def final_outcome(process: subprocess.CompletedProcess) -> str:
        return process.stdout.strip().splitlines()[-1]


def reconcile_in_process(fixture: RunFixture, **overrides) -> tuple[dict, str]:
    return fixture.make_reconciler(**overrides).reconcile()


class ReconciliationFixtureTest(unittest.TestCase):
    """Shared fixture lifecycle and assertion helpers."""

    def setUp(self) -> None:
        self.fx = RunFixture()
        self.addCleanup(self.fx.cleanup)

    def fresh_fixture(self) -> RunFixture:
        fixture = RunFixture()
        self.addCleanup(fixture.cleanup)
        return fixture

    def assert_refusal(self, process: subprocess.CompletedProcess, reason_code: str) -> dict:
        self.assertEqual(process.returncode, 1, process.stdout)
        self.assertEqual(self.fx.final_outcome(process), "OUTCOME: fail")
        result = self.fx.parse_result(process)
        self.assertEqual(result["status"], "refused")
        self.assertEqual(result["reason_code"], reason_code)
        state_path, before_state = process.fixture_state_snapshot
        self.assertEqual(state_path.read_bytes(), before_state)
        return result

    def assert_capture_unchanged(self, before: dict, fixture: RunFixture | None = None) -> None:
        target = fixture or self.fx
        self.assertEqual(target.state_bytes(), before["bytes"])
        self.assertEqual(target.worker_receipt_digest("1"), before["worker"])


class ReconciledReceiptTest(ReconciliationFixtureTest):
    """Requirements 1, 2, and 9: the readable per-task receipt, the single
    atomic replacement, and the preservation of every other record."""

    def test_reconcile_success_stores_readable_per_task_receipt(self) -> None:
        before = self.fx.capture()
        pre_run_plan_digest = self.fx.read_state()["plan_digest"]
        process = self.fx.run_cli()
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        self.assertEqual(self.fx.final_outcome(process), "OUTCOME: pass")
        result = self.fx.parse_result(process)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["reason_code"], "reconciled")
        self.assertEqual(result["generation"], 8)
        state = self.fx.read_state()
        self.assertEqual(state["generation"], 8)
        record = state["tasks"]["1"]
        # The reconciled projection.
        self.assertEqual(record["status"], "complete")
        self.assertIs(record["checkbox"], True)
        # The stored receipt is a plain JSON object on the task record, and
        # every binding is readable and exact.
        receipt = record["handoff_reconciliation"]
        self.assertEqual(receipt["receipt_version"], 1)
        self.assertEqual(receipt["run_session_id"], RUN_SESSION_ID)
        self.assertEqual(receipt["plan_slug"], PLAN_SLUG)
        self.assertEqual(receipt["plan_path"], PLAN_REL)
        self.assertEqual(receipt["plan_digest"], self.fx.plan_digest())
        self.assertEqual(receipt["task_id"], "1")
        self.assertEqual(receipt["plan_task"], 1)
        self.assertEqual(receipt["expected_generation"], 7)
        self.assertEqual(receipt["task_scope_digest"], self.fx.launch_scope_one)
        self.assertEqual(receipt["worker_receipt_digest"], canonical_digest(WORKER_RECEIPT_ONE))
        self.assertEqual(receipt["checkbox_projection"], {"checked": 2, "total": 2})
        self.assertEqual(receipt["reconciled_status"], "complete")
        self.assertEqual(
            receipt["review"],
            {
                "record": f"{REVIEW_BASE}-r1.md",
                "sidecar": f"{REVIEW_BASE}-r1.stats.json",
                "round": "r1",
                "source_digest": self.fx.plan_digest(),
                "verdict": "yes",
            },
        )
        # The accepted worker terminal receipt is preserved verbatim.
        self.assertEqual(record["terminal_receipt"], WORKER_RECEIPT_ONE)
        self.assertEqual(self.fx.worker_receipt_digest("1"), before["worker"])
        # Every other task record and the run-level fields survive the same
        # replacement untouched.
        self.assertEqual(state["tasks"]["2"], {"status": "pending", "checkbox": False})
        self.assertEqual(state["workflow_state"], "running")
        self.assertEqual(state["run_session_id"], RUN_SESSION_ID)
        # The launched run digest stays the run's own record; the receipt
        # carries the current digest instead.
        self.assertEqual(state["plan_digest"], pre_run_plan_digest)
        # The reconciliation itself commits nothing: the done commit gate
        # stays required.
        self.assertEqual(self.fx.commit_count(), 1)
        # The result's next action names the ordinary gates.
        self.assertIn("preflight", result["next_action"])
        self.assertIn("done commit gate", result["next_action"])

    def test_different_runtime_slug_refuses_without_mutation(self) -> None:
        self.fx.mutate_state(lambda state: state.__setitem__("plan_slug", "some-other-plan"))
        before = self.fx.capture()
        result = self.assert_refusal(self.fx.run_cli(), "plan-identity-mismatch")
        self.assertIn("some-other-plan", result["evidence"][0])
        self.assert_capture_unchanged(before)


class ClaimAdmissionMatrixTest(ReconciliationFixtureTest):
    """Requirement 5: claim and task-state admission, each independently,
    each a named refusal with unchanged manifest and terminal-receipt bytes.
    The helper enforces the claim itself, so it cannot be reached before
    claim acquisition even when only the parent would otherwise enforce it."""

    def test_missing_claim_refuses_without_mutation(self) -> None:
        before = self.fx.capture()
        self.fx.remove_claim()
        result = self.assert_refusal(self.fx.run_cli(), "claim-missing")
        self.assertIn("claim", result["evidence"][0])
        self.assert_capture_unchanged(before)

    def test_foreign_claim_session_refuses_without_mutation(self) -> None:
        before = self.fx.capture()
        self.fx.write_claim(session="other-session")
        self.assert_refusal(self.fx.run_cli(), "claim-foreign")
        self.assert_capture_unchanged(before)

    def test_foreign_claim_plan_refuses_without_mutation(self) -> None:
        before = self.fx.capture()
        self.fx.write_claim(plan_line="docs/history/plans/some-other-plan.md")
        self.assert_refusal(self.fx.run_cli(), "claim-foreign")
        self.assert_capture_unchanged(before)

    def test_task_state_other_than_done_pending_refuses_without_mutation(self) -> None:
        for status in ("pending", "claimed", "complete", "checkpointed", "deferred"):
            with self.subTest(status=status):
                fx = self.fresh_fixture()
                fx.mutate_state(lambda state, s=status: state["tasks"]["1"].__setitem__("status", s))
                before = {"bytes": fx.state_bytes(), "worker": fx.worker_receipt_digest("1")}
                process = fx.run_cli()
                self.assertEqual(process.returncode, 1, process.stdout)
                self.assertEqual(fx.final_outcome(process), "OUTCOME: fail")
                result = fx.parse_result(process)
                self.assertEqual(result["status"], "refused")
                self.assertEqual(result["reason_code"], "task-state-not-done-pending")
                self.assertIn(repr(status), result["evidence"][0])
                self.assertEqual(fx.state_bytes(), before["bytes"])
                self.assertEqual(fx.worker_receipt_digest("1"), before["worker"])


class EvidenceRefusalMatrixTest(ReconciliationFixtureTest):
    """The remaining refusal classes, each named, each without mutation."""

    def test_terminal_receipt_missing_refuses(self) -> None:
        self.fx.mutate_state(lambda state: state["tasks"]["1"].pop("terminal_receipt"))
        before = self.fx.capture()
        self.assert_refusal(self.fx.run_cli(), "terminal-receipt-missing")
        self.assert_capture_unchanged(before)

    def test_stale_review_digest_refuses(self) -> None:
        # The plan was corrected after the review: the staged sidecar still
        # binds the launch digest, so the review evidence is stale.
        before = self.fx.capture()
        corrected = self.fx.plan_path.read_text(encoding="utf-8").replace(
            "- [ ] First clause for task two.", "- [ ] First clause for task two, corrected."
        )
        self.fx.plan_path.write_text(corrected, encoding="utf-8")
        self.assert_refusal(self.fx.run_cli(), "plan-digest-stale")
        self.assert_capture_unchanged(before)

    def test_review_verdict_no_refuses(self) -> None:
        before = self.fx.capture()
        self.fx.write_review(1, self.fx.plan_digest(), verdict="no")
        self.assert_refusal(self.fx.run_cli(), "review-verdict-no")
        self.assert_capture_unchanged(before)

    def test_missing_review_artifact_refuses(self) -> None:
        before = self.fx.capture()
        (self.fx.root / f"{REVIEW_BASE}-r1.md").unlink()
        self.assert_refusal(self.fx.run_cli(), "review-evidence-unusable")
        self.assert_capture_unchanged(before)

    def test_malformed_sidecar_refuses(self) -> None:
        before = self.fx.capture()
        (self.fx.root / f"{REVIEW_BASE}-r1.stats.json").write_text("{not json", encoding="utf-8")
        self.assert_refusal(self.fx.run_cli(), "review-evidence-unusable")
        self.assert_capture_unchanged(before)

    def test_missing_plan_task_heading_refuses(self) -> None:
        before = self.fx.capture()
        result = self.assert_refusal(self.fx.run_cli(task=9), "task-not-found")
        self.assertIn("### Task 9:", result["evidence"][0])
        self.assert_capture_unchanged(before)

    def test_projection_incomplete_refuses(self) -> None:
        # A checkbox projection change the reviewed bytes do not cover: the
        # reviewed task carries an unchecked clause. The launched scope
        # digest is bound, so marker normalization passes and the incomplete
        # projection is what refuses.
        self.fx.mutate_state(
            lambda state: state["tasks"]["1"].__setitem__("task_scope_digest", self.fx.launch_scope_one)
        )
        half_marked = self.fx.plan_path.read_text(encoding="utf-8").replace(
            "- [x] First clause for task one.", "- [ ] First clause for task one."
        )
        self.fx.plan_path.write_text(half_marked, encoding="utf-8")
        self.fx.write_review(2, self.fx.plan_digest())
        before = self.fx.capture()
        result = self.assert_refusal(self.fx.run_cli(), "projection-incomplete")
        self.assertIn("1/2", result["evidence"][0])
        self.assert_capture_unchanged(before)


class TaskScopeRegressionTest(ReconciliationFixtureTest):
    """Requirement 7: changed task text beyond checkbox markers after
    launch, same run, plan, and task identifiers, refuses named."""

    def test_changed_task_scope_after_launch_refuses(self) -> None:
        # The launch record binds the launch scope; the task text then gains
        # a clause (beyond checkbox markers) and a fresh review covers the
        # changed bytes, so the refusal is scope drift and nothing else.
        self.fx.mutate_state(
            lambda state: state["tasks"]["1"].__setitem__("task_scope_digest", self.fx.launch_scope_one)
        )
        widened = self.fx.plan_path.read_text(encoding="utf-8").replace(
            "- [x] Second clause for task one.",
            "- [x] Second clause for task one.\n- [x] Third clause added after launch.",
        )
        self.fx.plan_path.write_text(widened, encoding="utf-8")
        protected = subprocess.run(
            [sys.executable, plan_fixer.__file__, "--preserve-tasks", str(self.fx.plan_path)],
            capture_output=True, text=True, timeout=30, env=self.fx.subprocess_env(),
        )
        self.assertEqual(protected.returncode, 0, protected.stderr)
        self.fx.write_review(2, self.fx.plan_digest())
        before = self.fx.capture()
        result = self.assert_refusal(self.fx.run_cli(), "task-scope-changed")
        self.assertIn(self.fx.launch_scope_one, result["evidence"][0])
        self.assertIn("recover-scope-drift", result["evidence"][1])
        self.assertIn("prelaunch", result["evidence"][1])
        self.assertIn("reviewed task-scope change referral", result["evidence"][1])
        # Same run, plan, and task identifiers throughout.
        state = self.fx.read_state()
        self.assertEqual(state["run_session_id"], RUN_SESSION_ID)
        self.assertEqual(state["plan_slug"], PLAN_SLUG)
        self.assertEqual(state["tasks"]["1"]["task_scope_digest"], self.fx.launch_scope_one)
        self.assert_capture_unchanged(before)

    def test_checkbox_marking_alone_does_not_change_scope(self) -> None:
        # The marker normalization: completion marking after launch must not
        # read as scope drift.
        self.fx.mutate_state(
            lambda state: state["tasks"]["1"].__setitem__("task_scope_digest", self.fx.launch_scope_one)
        )
        marked = (
            self.fx.plan_path.read_text(encoding="utf-8")
            .replace("- [ ] First clause for task one.", "- [x] First clause for task one.")
            .replace("- [ ] Second clause for task one.", "- [x] Second clause for task one.")
        )
        self.fx.plan_path.write_text(marked, encoding="utf-8")
        self.fx.write_review(2, self.fx.plan_digest())
        process = self.fx.run_cli()
        self.assertEqual(process.returncode, 0, process.stderr)
        result = self.fx.parse_result(process)
        self.assertEqual(result["reason_code"], "reconciled")
        receipt = self.fx.read_state()["tasks"]["1"]["handoff_reconciliation"]
        self.assertEqual(receipt["task_scope_digest"], self.fx.launch_scope_one)


class LegacyScopeRegressionTest(ReconciliationFixtureTest):
    """Requirement 8: a legacy done-pending record without the per-task
    task_scope_digest recovers the launch scope only from exact plan bytes
    whose digest equals the run's saved launch plan_digest."""

    def test_legacy_launch_scope_recovers_from_exact_launch_bytes(self) -> None:
        # The run's saved launch digest names the current bytes, so those
        # bytes are the exact launch bytes and the scope is recoverable.
        before = self.fx.capture()
        self.assertIsNone(self.fx.read_state()["tasks"]["1"].get("task_scope_digest"))
        process = self.fx.run_cli()
        self.assertEqual(process.returncode, 0, process.stderr)
        result = self.fx.parse_result(process)
        self.assertEqual(result["reason_code"], "reconciled")
        state = self.fx.read_state()
        self.assertEqual(state["tasks"]["1"]["task_scope_digest"], self.fx.launch_scope_one)
        self.assertEqual(
            state["tasks"]["1"]["handoff_reconciliation"]["task_scope_digest"],
            self.fx.launch_scope_one,
        )
        # The worker receipt survived the legacy reconciliation too.
        self.assertEqual(self.fx.worker_receipt_digest("1"), before["worker"])

    def test_legacy_launch_scope_unverified_when_bytes_changed(self) -> None:
        before = self.fx.capture()
        corrected = self.fx.plan_path.read_text(encoding="utf-8").replace(
            "- [ ] First clause for task two.", "- [ ] First clause for task two, corrected."
        )
        self.fx.plan_path.write_text(corrected, encoding="utf-8")
        self.fx.write_review(2, self.fx.plan_digest())
        result = self.assert_refusal(self.fx.run_cli(), "launch-scope-unverified")
        self.assertIn("launch plan_digest", result["evidence"][0])
        self.assert_capture_unchanged(before)

    def test_legacy_launch_scope_unverified_when_launch_digest_missing(self) -> None:
        self.fx.mutate_state(lambda state: state.pop("plan_digest"))
        before = self.fx.capture()
        self.assert_refusal(self.fx.run_cli(), "launch-scope-unverified")
        self.assert_capture_unchanged(before)


class AlreadyReconciledRetryTest(ReconciliationFixtureTest):
    """Requirement 6: the exact-match retry is a success without another
    write or generation increment; anything else refuses."""

    def test_same_receipt_retry_after_interrupted_response(self) -> None:
        process = self.fx.run_cli()
        self.assertEqual(process.returncode, 0, process.stderr)
        after_first = self.fx.state_bytes()
        generation_after_first = self.fx.read_state()["generation"]
        # The parent never read the first response (interrupted); the retry
        # must report success without another write or generation increment.
        retry = self.fx.run_cli()
        self.assertEqual(retry.returncode, 0, retry.stderr)
        self.assertEqual(self.fx.final_outcome(retry), "OUTCOME: pass")
        result = self.fx.parse_result(retry)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["reason_code"], "already-reconciled")
        self.assertEqual(result["generation"], generation_after_first)
        self.assertEqual(self.fx.state_bytes(), after_first)
        self.assertEqual(self.fx.read_state()["generation"], generation_after_first)

    def test_mismatched_evidence_retry_refuses(self) -> None:
        self.fx.run_cli()
        after_first = self.fx.state_bytes()
        # The plan moved on after the reconciliation (an unrelated task's
        # clause was corrected) and a fresh review covers the new bytes; the
        # stored receipt no longer matches the requested receipt.
        corrected = self.fx.plan_path.read_text(encoding="utf-8").replace(
            "- [ ] First clause for task two.", "- [ ] First clause for task two, corrected."
        )
        self.fx.plan_path.write_text(corrected, encoding="utf-8")
        self.fx.write_review(2, self.fx.plan_digest())
        process = self.fx.run_cli()
        self.assertEqual(process.returncode, 1, process.stdout)
        result = self.fx.parse_result(process)
        self.assertEqual(result["status"], "refused")
        self.assertEqual(result["reason_code"], "reconciliation-mismatch")
        self.assertIn("plan_digest", result["evidence"][0])
        self.assertEqual(self.fx.state_bytes(), after_first)

    def test_projection_clobbered_after_reconciliation_refuses(self) -> None:
        # Test-fabricated state surgery (manual manifest edits are
        # prohibited in production): the receipt matches but the record no
        # longer matches the reconciled projection, so the retry refuses.
        self.fx.run_cli()
        self.fx.mutate_state(
            lambda state: state["tasks"]["1"].__setitem__("status", "done-pending")
        )
        after_clobber = self.fx.state_bytes()
        process = self.fx.run_cli()
        self.assertEqual(process.returncode, 1, process.stdout)
        result = self.fx.parse_result(process)
        self.assertEqual(result["status"], "refused")
        self.assertEqual(result["reason_code"], "reconciliation-mismatch")
        self.assertIn("reconciled projection", result["evidence"][0])
        self.assertEqual(self.fx.state_bytes(), after_clobber)


class PreReplacementDriftTest(ReconciliationFixtureTest):
    """Requirement 4 and 9: the helper re-reads run identity, task identity,
    task-scope digest, and expected generation immediately before the atomic
    replacement and refuses any drift, named, without mutation."""

    def test_drift_mapping_contains_only_reachable_receipt_fields(self) -> None:
        self.assertEqual(
            recon.DRIFT_REASON_BY_FIELD,
            {
                "expected_generation": "stale-generation",
                "run_session_id": "run-identity-drift",
                "plan_slug": "plan-identity-drift",
                "plan_path": "plan-identity-drift",
                "plan_digest": "plan-bytes-changed",
                "task_scope_digest": "task-scope-changed",
                "worker_receipt_digest": "worker-receipt-changed",
                "review": "review-evidence-drift",
                "checkbox_projection": "plan-bytes-changed",
            },
        )

    def drift_seam(self, target_path: Path, mutate_after_first_read) -> tuple[dict, str]:
        original = recon._read_bytes
        seen: dict[str, int] = {}

        def seam(path: Path) -> bytes:
            payload = original(path)
            key = str(path)
            if path == target_path:
                count = seen.get(key, 0) + 1
                seen[key] = count
                if count == 1:
                    # The first read returned the pre-drift bytes; a
                    # concurrent parent-style write lands before the
                    # pre-replacement re-read.
                    mutate_after_first_read()
            return payload

        with mock.patch.object(recon, "_read_bytes", side_effect=seam):
            return reconcile_in_process(self.fx)

    def assert_drift_refusal(
        self, result: dict, outcome: str, reason_code: str, before_bytes: bytes, injected_mutator
    ) -> None:
        """The refusal names its class, the helper added nothing, and the
        only bytes on disk are the injected parent-style write itself."""
        self.assertEqual(outcome, "fail")
        self.assertEqual(result["status"], "refused")
        self.assertEqual(result["reason_code"], reason_code)
        state = json.loads(before_bytes)
        injected_mutator(state)
        self.assertEqual(
            self.fx.state_bytes().decode("utf-8"),
            json.dumps(state, sort_keys=True, indent=2) + "\n",
        )
        record = self.fx.read_state()["tasks"]["1"]
        self.assertNotIn("handoff_reconciliation", record)
        self.assertNotIn("task_scope_digest", record)
        self.assertEqual(record, state["tasks"]["1"])

    def test_stale_generation_drift_refuses(self) -> None:
        before_bytes = self.fx.state_bytes()

        def inject(state) -> None:
            state["generation"] = 8

        result, outcome = self.drift_seam(
            self.fx.state_path,
            lambda: self.fx.mutate_state(inject),
        )
        self.assert_drift_refusal(result, outcome, "stale-generation", before_bytes, inject)
        self.assertEqual(self.fx.read_state()["generation"], 8)  # only the injected write

    def test_run_identity_drift_refuses(self) -> None:
        before_bytes = self.fx.state_bytes()

        def inject(state) -> None:
            state["run_session_id"] = "run-fixture-other"

        result, outcome = self.drift_seam(
            self.fx.state_path,
            lambda: self.fx.mutate_state(inject),
        )
        self.assert_drift_refusal(result, outcome, "run-identity-drift", before_bytes, inject)

    def test_worker_receipt_drift_refuses(self) -> None:
        before_bytes = self.fx.state_bytes()

        def inject(state) -> None:
            state["tasks"]["1"]["terminal_receipt"]["validation"].append(
                {"command": "pytest scripts/test_unexpected.py -q", "exit": 1}
            )

        def apply() -> None:
            self.fx.mutate_state(inject)

        result, outcome = self.drift_seam(self.fx.state_path, apply)
        self.assert_drift_refusal(result, outcome, "worker-receipt-changed", before_bytes, inject)

    def test_task_state_drift_refuses(self) -> None:
        before_bytes = self.fx.state_bytes()

        def inject(state) -> None:
            state["tasks"]["1"]["status"] = "complete"

        result, outcome = self.drift_seam(
            self.fx.state_path,
            lambda: self.fx.mutate_state(inject),
        )
        # The re-derived receipt refuses the no-longer-done-pending record.
        self.assert_drift_refusal(result, outcome, "task-state-not-done-pending", before_bytes, inject)

    def test_plan_bytes_drift_refuses(self) -> None:
        before = self.fx.capture()

        def mutate() -> None:
            text = self.fx.plan_path.read_text(encoding="utf-8") + "\nDrift note.\n"
            self.fx.plan_path.write_text(text, encoding="utf-8")

        result, outcome = self.drift_seam(self.fx.plan_path, mutate)
        # The drifted bytes are no longer covered by the staged review; the
        # manifest and terminal receipt are untouched.
        self.assertEqual(outcome, "fail")
        self.assertEqual(result["reason_code"], "plan-digest-stale")
        self.assert_capture_unchanged(before)


class AtomicWriteRegressionTest(ReconciliationFixtureTest):
    """Requirement 9: atomic-write failures and interrupted temp writes leave
    the previous complete manifest; a success leaves the complete new one."""

    def temp_litter(self) -> list[Path]:
        return sorted(self.fx.state_path.parent.glob(".reconcile-handoff-*.tmp"))

    def test_replace_failure_preserves_old_manifest_bytes(self) -> None:
        before = self.fx.capture()
        with mock.patch.object(recon, "_replace", side_effect=OSError("injected replace failure")):
            result, outcome = reconcile_in_process(self.fx)
        self.assertEqual(outcome, "tool_error")
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["reason_code"], "atomic-write-failed")
        self.assertEqual(self.fx.state_bytes(), before["bytes"])
        self.assertEqual(self.fx.worker_receipt_digest("1"), before["worker"])
        self.assertEqual(self.temp_litter(), [])

    def test_interrupted_temp_write_preserves_old_manifest_bytes(self) -> None:
        before = self.fx.capture()

        def partial_write(reconciler, fd, payload):
            # Write half the payload, then die: the interrupted-write shape.
            os.write(fd, payload[: len(payload) // 2])
            raise OSError("injected interruption mid-write")

        with mock.patch.object(
            recon.HandoffReconciler, "_write_temp_payload", partial_write
        ):
            result, outcome = reconcile_in_process(self.fx)
        self.assertEqual(outcome, "tool_error")
        self.assertEqual(result["reason_code"], "atomic-write-failed")
        self.assertEqual(self.fx.state_bytes(), before["bytes"])
        self.assertEqual(self.fx.read_state()["tasks"]["1"]["status"], "done-pending")
        self.assertEqual(self.temp_litter(), [])

    def test_success_replacement_is_the_complete_new_state(self) -> None:
        result, outcome = reconcile_in_process(self.fx)
        self.assertEqual(outcome, "pass")
        state = self.fx.read_state()
        self.assertEqual(state["tasks"]["1"]["status"], "complete")
        self.assertEqual(state["tasks"]["1"]["checkbox"], True)
        self.assertIn("handoff_reconciliation", state["tasks"]["1"])
        self.assertIn("task_scope_digest", state["tasks"]["1"])
        self.assertEqual(state["generation"], 8)
        # The written bytes parse as the complete state (no torn write).
        reparsed = json.loads(self.fx.state_bytes().decode("utf-8"))
        self.assertEqual(reparsed, state)


class ScopeDriftRecoveryAdmissionTest(ReconciliationFixtureTest):
    """Recovery-specific ordered gates and outcome contract."""

    def prepare_recovery(self) -> None:
        changed = self.fx.plan_path.read_text(encoding="utf-8").replace(
            "### Task 2: Second fixture task",
            "- [ ] Added reviewed clause after launch.\n\n### Task 2: Second fixture task",
        )
        self.fx.plan_path.write_text(changed, encoding="utf-8")
        self.fx.write_review(2, self.fx.plan_digest())
        path = self.fx.root / "scripts" / "example_one.py"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"launch baseline")
        baseline = hashlib.sha256(path.read_bytes()).hexdigest()
        post = hashlib.sha256(b"accepted worker effect").hexdigest()
        def seed(state):
            record = state["tasks"]["1"]
            record["task_scope_digest"] = self.fx.launch_scope_one
            record["effect_baseline"] = {"scripts/example_one.py": baseline}
            record["terminal_receipt"]["effect_evidence"] = {"scripts/example_one.py": post}
        self.fx.mutate_state(seed)

    def run_recovery(self):
        return self.fx.run_cli(command="recover-scope-drift")

    def test_scope_unchanged_refuses_and_names_reconcile(self):
        self.prepare_recovery()
        self.fx.mutate_state(lambda s: s["tasks"]["1"].__setitem__("task_scope_digest", recon.task_scope_digest(task_section(self.fx.plan_path.read_text(), 1))))
        before = self.fx.state_bytes()
        process = self.run_recovery()
        self.assertEqual(process.returncode, 1)
        result = self.fx.parse_result(process)
        self.assertEqual(result["reason_code"], "scope-unchanged")
        self.assertIn("reconcile", " ".join(result["evidence"]))
        self.assertEqual(self.fx.state_bytes(), before)

    def test_fully_checked_and_checklistless_projection_refuse(self):
        self.prepare_recovery()
        text = self.fx.plan_path.read_text().replace("- [ ] Added reviewed clause after launch.", "- [x] Added reviewed clause after launch.")
        self.fx.plan_path.write_text(text); self.fx.write_review(3, self.fx.plan_digest())
        before = self.fx.state_bytes(); result = self.assert_refusal(self.run_recovery(), "projection-complete")
        self.assertEqual(self.fx.state_bytes(), before)
        text = self.fx.plan_path.read_text()
        section = recon._extract_task_section(text, 1)
        for line in section.splitlines():
            if line.startswith("- [x] "):
                text = text.replace(line, line.replace("- [x] ", "* "), 1)
        self.fx.plan_path.write_text(text); self.fx.write_review(4, self.fx.plan_digest())
        self.assert_refusal(self.run_recovery(), "projection-complete")

    def test_missing_evidence_baseline_escape_and_symlink_gates(self):
        self.prepare_recovery()
        self.fx.mutate_state(lambda s: s["tasks"]["1"]["terminal_receipt"].__setitem__("effect_evidence", {}))
        self.assert_refusal(self.run_recovery(), "effect-evidence-unavailable")
        self.fx.mutate_state(lambda s: s["tasks"]["1"]["terminal_receipt"].__setitem__("effect_evidence", {"scripts/example_one.py": "a" * 64}))
        self.fx.mutate_state(lambda s: s["tasks"]["1"].pop("effect_baseline"))
        self.assert_refusal(self.run_recovery(), "effect-baseline-unrecorded")
        self.fx.mutate_state(lambda s: (s["tasks"]["1"].__setitem__("effect_baseline", {"../escape": "absent"}), s["tasks"]["1"]["terminal_receipt"].__setitem__("effect_evidence", {"../escape": "a" * 64})))
        self.assert_refusal(self.run_recovery(), "effect-path-escapes-root")
        outside = self.fx.root.parent / (self.fx.root.name + "-outside")
        outside.write_bytes(b"outside")
        link = self.fx.root / "scripts" / "linked.py"
        link.symlink_to(outside)
        self.fx.mutate_state(lambda s: (s["tasks"]["1"].__setitem__("effect_baseline", {"scripts/linked.py": "absent"}), s["tasks"]["1"]["terminal_receipt"].__setitem__("effect_evidence", {"scripts/linked.py": "a" * 64})))
        self.assert_refusal(self.run_recovery(), "effect-path-escapes-root")
        outside.unlink()

    def test_escaping_symlink_refuses_before_effect_file_probe(self):
        self.prepare_recovery()
        outside = self.fx.root.parent / (self.fx.root.name + "-outside")
        outside.write_bytes(b"outside")
        self.addCleanup(lambda: outside.unlink(missing_ok=True))
        (self.fx.root / "scripts" / "linked.py").symlink_to(outside)
        self.fx.mutate_state(lambda s: (s["tasks"]["1"].__setitem__("effect_baseline", {"scripts/linked.py": "absent"}), s["tasks"]["1"]["terminal_receipt"].__setitem__("effect_evidence", {"scripts/linked.py": "a" * 64})))
        with mock.patch.object(recon, "_read_bytes", wraps=recon._read_bytes) as reader:
            result, outcome = self.fx.make_reconciler().recover_scope_drift()
        self.assertEqual(outcome, "fail")
        self.assertEqual(result["reason_code"], "effect-path-escapes-root")
        self.assertFalse(any(Path(call.args[0]).resolve() == outside.resolve() for call in reader.call_args_list))

    def test_gate_precedence_and_legacy_scope_refusal(self):
        self.prepare_recovery()
        def make_scope_unchanged(state):
            state["tasks"]["1"]["task_scope_digest"] = recon.task_scope_digest(
                task_section(self.fx.plan_path.read_text(), 1)
            )
            state["tasks"]["1"]["terminal_receipt"].pop("effect_evidence", None)
            state["tasks"]["1"].pop("effect_baseline", None)
        self.fx.mutate_state(make_scope_unchanged)
        self.assert_refusal(self.run_recovery(), "scope-unchanged")
        self.fx.mutate_state(lambda s: s["tasks"]["1"].pop("task_scope_digest"))
        self.assert_refusal(self.run_recovery(), "launch-scope-unrecorded")
        self.fx.mutate_state(lambda s: s["tasks"]["1"].__setitem__("task_scope_digest", self.fx.launch_scope_one))
        # Full projection outranks absent evidence.
        all_checked = self.fx.plan_path.read_text().replace("- [ ] Added reviewed clause after launch.", "- [x] Added reviewed clause after launch.")
        self.fx.plan_path.write_text(all_checked); self.fx.write_review(3, self.fx.plan_digest())
        self.fx.mutate_state(lambda s: (s["tasks"]["1"]["terminal_receipt"].pop("effect_evidence", None), s["tasks"]["1"].pop("effect_baseline", None)))
        self.assert_refusal(self.run_recovery(), "projection-complete")

    def test_empty_changed_path_set_and_inherited_admission_gates(self):
        self.prepare_recovery()
        self.fx.mutate_state(lambda s: s["tasks"]["1"]["terminal_receipt"].__setitem__("effect_evidence", {"": "a" * 64}))
        self.assert_refusal(self.run_recovery(), "effect-evidence-unavailable")
        self.fx.mutate_state(lambda s: s["tasks"]["1"]["terminal_receipt"].pop("effect_evidence"))
        self.fx.remove_claim()
        self.assert_refusal(self.run_recovery(), "claim-missing")
        self.fx.write_claim(session="other")
        self.assert_refusal(self.run_recovery(), "claim-foreign")
        self.fx.write_claim()
        self.fx.mutate_state(lambda s: s["tasks"]["1"].pop("terminal_receipt"))
        self.assert_refusal(self.run_recovery(), "terminal-receipt-missing")

    def test_unreadable_directory_returns_tool_error_unchanged(self):
        self.prepare_recovery()
        directory = self.fx.root / "scripts" / "directory.py"
        directory.mkdir()
        self.fx.mutate_state(lambda s: (s["tasks"]["1"].__setitem__("effect_baseline", {"scripts/directory.py": "absent"}), s["tasks"]["1"]["terminal_receipt"].__setitem__("effect_evidence", {"scripts/directory.py": "a" * 64})))
        before = self.fx.state_bytes()
        process = self.run_recovery()
        self.assertEqual(process.returncode, 3)
        self.assertEqual(self.fx.final_outcome(process), "OUTCOME: tool_error")
        self.assertEqual(self.fx.parse_result(process)["reason_code"], "effect-path-unreadable")
        self.assertEqual(self.fx.state_bytes(), before)

    def test_dangling_in_root_symlink_refuses_without_recovery_state_write(self):
        self.prepare_recovery()
        link = self.fx.root / "scripts" / "dangling.py"
        link.symlink_to(self.fx.root / "scripts" / "not-created.py")
        self.fx.mutate_state(lambda s: (
            s["tasks"]["1"]["effect_baseline"].update({"scripts/dangling.py": "absent"}),
            s["tasks"]["1"]["terminal_receipt"]["effect_evidence"].update({"scripts/dangling.py": "a" * 64}),
        ))
        before = self.fx.state_bytes()
        result = self.assert_refusal(self.run_recovery(), "effect-path-escapes-root")
        self.assertEqual(self.fx.state_bytes(), before)
        self.assertIn("symlink", " ".join(result["evidence"]))

    def test_fifo_recovery_refuses_promptly_and_preserves_state(self):
        self.prepare_recovery()
        fifo = self.fx.root / "scripts" / "waiting.fifo"
        os.mkfifo(fifo)
        self.fx.mutate_state(lambda s: (
            s["tasks"]["1"]["effect_baseline"].update({"scripts/waiting.fifo": "absent"}),
            s["tasks"]["1"]["terminal_receipt"]["effect_evidence"].update({"scripts/waiting.fifo": "a" * 64}),
        ))
        before = self.fx.state_bytes()
        process = self.fx.run_cli(command="recover-scope-drift", timeout=2.0)
        self.assertEqual(process.returncode, 3, process.stderr)
        self.assertEqual(self.fx.final_outcome(process), "OUTCOME: tool_error")
        self.assertEqual(self.fx.parse_result(process)["reason_code"], "effect-path-unreadable")
        self.assertEqual(self.fx.state_bytes(), before)

    def test_valid_absent_effect_requeues_and_replace_failure_is_atomic(self):
        self.prepare_recovery()
        before = self.fx.state_bytes()
        with mock.patch.object(recon, "_replace", side_effect=OSError("injected")):
            result, outcome = self.fx.make_reconciler().recover_scope_drift()
        self.assertEqual(outcome, "tool_error")
        self.assertEqual(result["reason_code"], "atomic-write-failed")
        self.assertEqual(self.fx.state_bytes(), before)
        process = self.run_recovery()
        self.assertEqual(process.returncode, 0, process.stderr + process.stdout)
        self.assertEqual(self.fx.final_outcome(process), "OUTCOME: pass")
        state = self.fx.read_state(); record = state["tasks"]["1"]
        self.assertEqual(record["status"], "pending")
        self.assertFalse(record["checkbox"])
        self.assertIn("scope_recovery", record)
        self.assertEqual(state["generation"], 8)

    def test_recovery_partition_decides_named_corner_cells(self):
        digest = "a" * 64
        self.assertEqual(recon._classify_effect("absent", digest, "absent"), "absent")
        self.assertEqual(recon._classify_effect(digest, "absent", "absent"), "present")
        self.assertEqual(recon._classify_effect("absent", "absent", "absent"), "neutral")
        self.assertEqual(recon._classify_effect(digest, digest, digest), "neutral")
        self.assertEqual(recon._classify_effect(digest, "b" * 64, "c" * 64), "evolved")

    def test_multi_path_aggregation_refuses_mixed_present_and_accepts_absent_neutral(self):
        self.prepare_recovery()
        path = self.fx.root / "scripts" / "example_one.py"
        path.write_bytes(b"accepted worker effect")
        absent_post = "absent"
        self.fx.mutate_state(lambda state: (
            state["tasks"]["1"]["effect_baseline"].update({"scripts/never_created.py": "absent"}),
            state["tasks"]["1"]["terminal_receipt"]["effect_evidence"].update({"scripts/never_created.py": absent_post}),
        ))
        before = self.fx.state_bytes()
        process = self.run_recovery()
        self.assertEqual(process.returncode, 1)
        self.assertEqual(self.fx.parse_result(process)["reason_code"], "effect-present")
        self.assertEqual(self.fx.state_bytes(), before)

        path.write_bytes(b"launch baseline")
        process = self.run_recovery()
        self.assertEqual(process.returncode, 0, process.stderr + process.stdout)
        self.assertEqual(self.fx.parse_result(process)["reason_code"], "scope-drift-recovered")
        state = self.fx.read_state()
        self.assertEqual(state["tasks"]["1"]["scope_recovery"]["effect_verdicts"], {
            "scripts/example_one.py": "absent",
            "scripts/never_created.py": "neutral",
        })

    def test_evolved_effect_has_its_named_refusal_class(self):
        self.prepare_recovery()
        path = self.fx.root / "scripts" / "example_one.py"
        path.write_bytes(b"later unrelated bytes")
        before = self.fx.state_bytes()
        process = self.run_recovery()
        self.assertEqual(process.returncode, 1)
        self.assertEqual(self.fx.parse_result(process)["reason_code"], "effect-evolved")
        self.assertEqual(self.fx.state_bytes(), before)

    def test_success_preserves_original_receipts_unrelated_records_and_plan_digest(self):
        self.prepare_recovery()
        self.fx.mutate_state(lambda state: state["tasks"].update({"2": {"status": "pending", "checkbox": False, "sentinel": [1, 2, 3]}}))
        before = self.fx.read_state()
        old_receipt = before["tasks"]["1"]["terminal_receipt"]
        old_baseline = before["tasks"]["1"]["effect_baseline"]
        unrelated = before["tasks"]["2"]
        plan_digest = before["plan_digest"]
        process = self.run_recovery()
        self.assertEqual(process.returncode, 0, process.stderr + process.stdout)
        after = self.fx.read_state()
        record = after["tasks"]["1"]
        self.assertEqual(record["status"], "pending")
        self.assertFalse(record["checkbox"])
        self.assertEqual(record["task_scope_digest"], record["scope_recovery"]["task_scope_digest"])
        self.assertEqual(after["generation"], before["generation"] + 1)
        self.assertEqual(record["terminal_receipt"], old_receipt)
        self.assertEqual(record["effect_baseline"], old_baseline)
        self.assertEqual(after["tasks"]["2"], unrelated)
        self.assertEqual(after["plan_digest"], plan_digest)
        self.assertEqual(set(record["scope_recovery"]), {
            "run_session_id", "plan_slug", "plan_path", "plan_digest", "task_id", "plan_task",
            "expected_generation", "prior_task_scope_digest", "task_scope_digest",
            "worker_receipt_digest", "review", "checkbox_projection", "effect_verdicts",
        })

    def test_recovered_task_reinvocation_refuses_for_ordinary_loop_reselection(self):
        self.prepare_recovery()
        first = self.run_recovery()
        self.assertEqual(first.returncode, 0, first.stderr + first.stdout)
        state_after = self.fx.state_bytes()
        second = self.run_recovery()
        self.assertEqual(second.returncode, 1)
        self.assertEqual(self.fx.parse_result(second)["reason_code"], "task-state-not-done-pending")
        self.assertEqual(self.fx.state_bytes(), state_after)

    def test_recovery_reread_field_groups_refuse_without_helper_mutation(self):
        for group, (fields, refusal_code) in recon.SCOPE_RECOVERY_GROUPS.items():
            with self.subTest(group=group):
                self.prepare_recovery()
                original = recon.HandoffReconciler._scope_drift_admission
                calls = 0

                def admission(instance, plan_raw, state):
                    nonlocal calls
                    result = original(instance, plan_raw, state)
                    calls += 1
                    if calls == 2:
                        receipt, evidence = result
                        if group == "effect_verdicts":
                            evidence["current"]["scripts/example_one.py"] = "f" * 64
                        else:
                            field = fields[0]
                            receipt[field] = f"changed-{field}"
                    return result

                before = self.fx.state_bytes()
                with mock.patch.object(recon.HandoffReconciler, "_scope_drift_admission", autospec=True, side_effect=admission):
                    result, outcome = self.fx.make_reconciler().recover_scope_drift()
                self.assertEqual(outcome, "fail")
                self.assertEqual(result["reason_code"], refusal_code)
                self.assertEqual(self.fx.state_bytes(), before)

    def test_recovery_field_group_registry_covers_the_terms_nine_groups(self):
        self.assertEqual(len(recon.SCOPE_RECOVERY_GROUPS), 9)
        flattened = [field for fields, _ in recon.SCOPE_RECOVERY_GROUPS.values() for field in fields]
        self.assertEqual(set(flattened), {
            "run_session_id", "plan_slug", "plan_path", "plan_digest", "task_id", "plan_task",
            "expected_generation", "prior_task_scope_digest", "task_scope_digest",
            "worker_receipt_digest", "effect_verdicts", "review", "checkbox_projection",
        })

    def test_cli_recovery_reenters_status_keyed_preflight_and_task_selection(self):
        self.prepare_recovery()
        process = self.run_recovery()
        self.assertEqual(process.returncode, 0, process.stderr + process.stdout)
        record = self.fx.read_state()["tasks"]["1"]
        self.assertEqual(record["status"], "pending")
        self.assertIn("terminal_receipt", record)  # historical evidence is preserved
        self.assertIsNone(emulated_preflight(self.fx))
        self.assertEqual(canonical_next_task(self.fx), "1")


class TwoTaskSequenceTest(ReconciliationFixtureTest):
    """Requirement 10: two distinct tasks reconciled in sequence; the second
    transition preserves the first task's scope digest and receipt."""

    def test_second_reconciliation_preserves_first_task_record(self) -> None:
        # Both tasks sit done-pending with launched scope digests; the
        # reviewed bytes mark every clause complete.
        def seed_both_tasks(state) -> None:
            state["tasks"]["1"]["task_scope_digest"] = self.fx.launch_scope_one
            state["tasks"]["2"] = {
                "status": "done-pending",
                "checkbox": False,
                "terminal_receipt": dict(WORKER_RECEIPT_TWO),
                "task_scope_digest": self.fx.launch_scope_two,
            }

        self.fx.mutate_state(seed_both_tasks)
        fully_marked = (
            self.fx.plan_path.read_text(encoding="utf-8")
            .replace("- [ ] First clause for task one.", "- [x] First clause for task one.")
            .replace("- [ ] Second clause for task one.", "- [x] Second clause for task one.")
            .replace("- [ ] First clause for task two.", "- [x] First clause for task two.")
        )
        self.fx.plan_path.write_text(fully_marked, encoding="utf-8")
        self.fx.write_review(2, self.fx.plan_digest())
        first = self.fx.run_cli(task=1)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(self.fx.parse_result(first)["reason_code"], "reconciled")
        state_after_first = self.fx.read_state()
        task_one_record = state_after_first["tasks"]["1"]
        self.assertEqual(task_one_record["status"], "complete")
        self.assertEqual(task_one_record["task_scope_digest"], self.fx.launch_scope_one)
        # The second transition: the state now sits at generation 8.
        second = self.fx.run_cli(task=2)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(self.fx.parse_result(second)["reason_code"], "reconciled")
        state_after_second = self.fx.read_state()
        self.assertEqual(state_after_second["generation"], 9)
        # The first task's scope digest and receipt are preserved verbatim.
        self.assertEqual(state_after_second["tasks"]["1"], task_one_record)
        # The second task carries its own scope digest and receipt.
        task_two = state_after_second["tasks"]["2"]
        self.assertEqual(task_two["status"], "complete")
        self.assertEqual(task_two["task_scope_digest"], self.fx.launch_scope_two)
        self.assertEqual(
            task_two["handoff_reconciliation"]["worker_receipt_digest"],
            canonical_digest(WORKER_RECEIPT_TWO),
        )
        self.assertEqual(
            task_two["handoff_reconciliation"]["task_scope_digest"], self.fx.launch_scope_two
        )


def emulated_preflight(fixture: RunFixture) -> str | None:
    """The documented Phase 1 preflight predicates over disk truth: the
    latest review pair binds the current plan bytes with a yes verdict, and
    every accepted terminal handoff is projected onto the reviewed checklist
    (the witnessed incident's refusal set)."""
    plan_text = fixture.plan_path.read_text(encoding="utf-8")
    digest = fixture.plan_digest()
    sidecar = fixture.latest_sidecar()
    if sidecar.get("source_digest") != digest or sidecar.get("verdict") != "yes":
        return "review-not-current"
    state = fixture.read_state()
    for key, record in state["tasks"].items():
        section = task_section(plan_text, int(key))
        projection = recon.checkbox_projection(section)
        # Parent preflight classifies done-pending from the status key. A
        # recovered record deliberately retains its historical terminal
        # receipt while returning to pending, so receipt presence alone is
        # not an unresolved handoff.
        if record.get("status") == recon.DONE_PENDING_STATUS:
            return f"unresolved-done-handoff:{key}"
        if record.get("terminal_receipt"):
            expected_checkbox = projection["total"] > 0 and projection["checked"] == projection["total"]
            if bool(record.get("checkbox")) != expected_checkbox:
                return f"checkbox-ownership-mismatch:{key}"
    return None


def canonical_next_task(fixture: RunFixture) -> str | None:
    """The canonical continuation: while an accepted terminal handoff sits
    unresolved (the witnessed incident) preflight emits no continuation;
    otherwise the first incomplete task in plan order is next."""
    if emulated_preflight(fixture) is not None:
        return None
    plan_text = fixture.plan_path.read_text(encoding="utf-8")
    state = fixture.read_state()
    for key in sorted(state["tasks"], key=int):
        record = state["tasks"][key]
        if record.get("status") not in DONE_STATUSES:
            section = task_section(plan_text, int(key))
            projection = recon.checkbox_projection(section)
            if projection["checked"] < projection["total"]:
                return key
    return None


class EndToEndFixtureTest(ReconciliationFixtureTest):
    """Requirement 11: a corrected and freshly reviewed done-pending task
    reconciles, passes preflight, receives the canonical next continuation,
    and still requires the ordinary done commit gate."""

    def test_corrected_reviewed_done_pending_task_reconciles_end_to_end(self) -> None:
        commits_before = self.fx.commit_count()
        # The witnessed shape: after the accepted task-one handoff the plan
        # was corrected (task one's completion was marked in Step 1.3 and
        # task two's clause was reworded during review), so the launch digest
        # and the old checkbox projection went stale together.
        self.fx.mutate_state(
            lambda state: state["tasks"]["1"].__setitem__("task_scope_digest", self.fx.launch_scope_one)
        )
        corrected = (
            self.fx.plan_path.read_text(encoding="utf-8")
            .replace("- [ ] First clause for task one.", "- [x] First clause for task one.")
            .replace("- [ ] Second clause for task one.", "- [x] Second clause for task one.")
            .replace("- [ ] First clause for task two.", "- [ ] First clause for task two, reworded.")
        )
        self.fx.plan_path.write_text(corrected, encoding="utf-8")
        self.fx.write_review(2, self.fx.plan_digest())
        # Before reconciliation the ordinary preflight refuses the run: the
        # accepted handoff sits unresolved against the stale projection, and
        # no canonical continuation is emitted.
        self.assertEqual(emulated_preflight(self.fx), "unresolved-done-handoff:1")
        self.assertIsNone(canonical_next_task(self.fx))
        # The receipt-backed reconciliation.
        process = self.fx.run_cli()
        self.assertEqual(process.returncode, 0, process.stderr)
        result = self.fx.parse_result(process)
        self.assertEqual(result["reason_code"], "reconciled")
        # The reviewed bytes mark task one fully checked; the normalized
        # scope still matches the launched scope.
        receipt = self.fx.read_state()["tasks"]["1"]["handoff_reconciliation"]
        self.assertEqual(receipt["task_scope_digest"], self.fx.launch_scope_one)
        self.assertEqual(receipt["plan_digest"], self.fx.plan_digest())
        # Ordinary preflight now passes and the canonical continuation is
        # the next incomplete task.
        self.assertIsNone(emulated_preflight(self.fx))
        self.assertEqual(canonical_next_task(self.fx), "2")
        # The reconciliation committed nothing and left the run running, so
        # the ordinary done commit gate is still required.
        self.assertEqual(self.fx.commit_count(), commits_before)
        self.assertEqual(self.fx.read_state()["workflow_state"], "running")
        self.assertIn("done commit gate", result["next_action"])



class EffectEvidenceCaptureCliTest(unittest.TestCase):
    CLI_TEST_ENV = {"PYTHONIOENCODING": "utf-8"}

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="effect-capture-")
        self.root = Path(self.temp.name)
        (self.root / "repo" / "dir").mkdir(parents=True)
        self.repo = self.root / "repo"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_capture(self, *paths: str, timeout: float = 5.0):
        return subprocess.run(
            [sys.executable, RECONCILE_SCRIPT, "capture-effect-evidence", "--repo-root", str(self.repo), *paths],
            capture_output=True, text=True, timeout=timeout, env=self.CLI_TEST_ENV.copy(),
        )

    def test_capture_cli_hashes_raw_bytes_and_marks_only_missing_paths_absent(self):
        payload = b"\x00raw\xff\nbytes"
        (self.repo / "dir" / "raw.bin").write_bytes(payload)
        result = self.run_capture("dir/raw.bin", "dir/missing.bin")
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[-1], "OUTCOME: pass")
        self.assertEqual(json.loads(lines[0]), {
            "status": "success",
            "effect_evidence": {
                "dir/raw.bin": hashlib.sha256(payload).hexdigest(),
                "dir/missing.bin": "absent",
            },
        })

    def test_capture_refuses_symlinks_directories_and_never_prints_partial_map(self):
        (self.repo / "dir" / "good.bin").write_bytes(b"good")
        outside = self.root / "outside.bin"
        outside.write_bytes(b"outside")
        (self.repo / "dir" / "link.bin").symlink_to(outside)
        result = self.run_capture("dir/good.bin", "dir/link.bin")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("OUTCOME: fail", result.stderr)
        (self.repo / "linked-dir").symlink_to(outside.parent, target_is_directory=True)
        result = self.run_capture("dir/good.bin", "linked-dir/outside.bin")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("OUTCOME: fail", result.stderr)
        result = self.run_capture("dir")
        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stdout, "")
        self.assertIn("OUTCOME: tool_error", result.stderr)

    def test_capture_rejects_embedded_nul_without_partial_map(self):
        (self.repo / "dir" / "good.bin").write_bytes(b"good")
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.dict(os.environ, self.CLI_TEST_ENV, clear=True):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = recon.main([
                    "capture-effect-evidence", "--repo-root", str(self.repo),
                    "dir/good.bin", "dir/bad\x00path.bin",
                ])
        self.assertEqual(result, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(json.loads(stderr.getvalue().splitlines()[0])["reason_code"], "effect-path-escapes-root")
        self.assertIn("OUTCOME: fail", stderr.getvalue())

    def test_directory_descriptor_metadata_error_is_tool_error_and_closes_fd(self):
        root_fd = os.open(self.repo, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        opened_fds = []
        open_directory = recon._open_directory_at

        def remember_open(parent_fd, component):
            fd = open_directory(parent_fd, component)
            opened_fds.append(fd)
            return fd

        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.dict(os.environ, self.CLI_TEST_ENV, clear=True):
            with mock.patch.object(recon, "_open_repository_root", return_value=root_fd):
                with mock.patch.object(recon, "_open_directory_at", side_effect=remember_open):
                    with mock.patch.object(recon.os, "fstat", side_effect=OSError(errno.EIO, "injected metadata failure")):
                        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                            result = recon.main([
                                "capture-effect-evidence", "--repo-root", str(self.repo), "dir/good.bin",
                            ])
        self.assertEqual(result, 3)
        self.assertEqual(stdout.getvalue(), "")
        payload = json.loads(stderr.getvalue().splitlines()[0])
        self.assertEqual(payload["reason_code"], "effect-path-unreadable")
        self.assertIn("OUTCOME: tool_error", stderr.getvalue())
        self.assertEqual(len(opened_fds), 1)
        with self.assertRaises(OSError):
            os.fstat(opened_fds[0])
        with self.assertRaises(OSError):
            os.fstat(root_fd)

    def test_capture_close_failures_are_modeled_and_cleanup_continues(self):
        (self.repo / "dir" / "good.bin").write_bytes(b"good")
        real_close = os.close
        real_dup = os.dup
        real_open_file = recon._open_regular_file_at
        real_open_directory = recon._open_directory_at
        cases = ("file", "current", "intermediate", "root")
        for target in cases:
            with self.subTest(target=target):
                root_fd = os.open(self.repo, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
                target_fd = {"root": root_fd}
                attempted = []

                def remember_dup(fd):
                    result = real_dup(fd)
                    target_fd["current"] = result
                    return result

                def remember_file(parent_fd, leaf):
                    result = real_open_file(parent_fd, leaf)
                    target_fd["file"] = result
                    return result

                def remember_directory(parent_fd, component):
                    result = real_open_directory(parent_fd, component)
                    target_fd["intermediate"] = result
                    return result

                def injected_close(fd):
                    attempted.append(fd)
                    real_close(fd)
                    if fd == target_fd.get(target):
                        raise OSError(errno.EIO, "injected close failure")

                stdout = io.StringIO()
                stderr = io.StringIO()
                with mock.patch.dict(os.environ, self.CLI_TEST_ENV, clear=True):
                    with mock.patch.object(recon, "_open_repository_root", return_value=root_fd):
                        with mock.patch.object(recon.os, "dup", side_effect=remember_dup):
                            with mock.patch.object(recon, "_open_regular_file_at", side_effect=remember_file):
                                with mock.patch.object(recon, "_open_directory_at", side_effect=remember_directory):
                                    with mock.patch.object(recon.os, "close", side_effect=injected_close):
                                        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                                            result = recon.main([
                                                "capture-effect-evidence", "--repo-root", str(self.repo), "dir/good.bin",
                                            ])
                self.assertEqual(result, 3)
                self.assertEqual(stdout.getvalue(), "")
                payload = json.loads(stderr.getvalue().splitlines()[0])
                self.assertEqual(payload["reason_code"], "effect-path-unreadable")
                self.assertIn("OUTCOME: tool_error", stderr.getvalue())
                self.assertTrue(set(target_fd.values()).issubset(attempted), (target, target_fd, attempted))

    def test_repository_root_close_failure_is_modeled_without_retrying_close(self):
        real_close = os.close
        real_open_directory = recon._open_directory_at
        closed = []
        opened = []
        events = []

        def remember_open(parent_fd, component):
            fd = real_open_directory(parent_fd, component)
            opened.append(fd)
            events.append(("open", fd))
            return fd

        def close_and_fail_once(fd):
            closed.append(fd)
            events.append(("close", fd))
            real_close(fd)
            if len(closed) == 1:
                raise OSError(errno.EIO, "injected root-walk close failure")

        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.dict(os.environ, self.CLI_TEST_ENV, clear=True):
            with mock.patch.object(recon, "_open_directory_at", side_effect=remember_open):
                with mock.patch.object(recon.os, "close", side_effect=close_and_fail_once):
                    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                        result = recon.main([
                            "capture-effect-evidence", "--repo-root", str(self.repo), "dir/good.bin",
                        ])
        self.assertEqual(result, 3)
        self.assertEqual(stdout.getvalue(), "")
        payload = json.loads(stderr.getvalue().splitlines()[0])
        self.assertEqual(payload["reason_code"], "repository-root-unreadable")
        self.assertGreater(len(closed), 0)
        self.assertTrue(opened)
        for fd in set(opened):
            with self.subTest(fd=fd), self.assertRaises(OSError):
                os.fstat(fd)
        self.assertEqual(events[1][0], "close")
        self.assertEqual(events[2][0], "open")
        self.assertIn("OUTCOME: tool_error", stderr.getvalue())

    def test_capture_close_failure_preserves_primary_refusal(self):
        (self.repo / "dir" / "link.bin").symlink_to(self.repo / "dir" / "good.bin")
        root_fd = os.open(self.repo, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        real_close = os.close

        def close_and_fail(fd):
            real_close(fd)
            raise OSError(errno.EIO, "injected close failure")

        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.dict(os.environ, self.CLI_TEST_ENV, clear=True):
            with mock.patch.object(recon, "_open_repository_root", return_value=root_fd):
                with mock.patch.object(recon.os, "close", side_effect=close_and_fail):
                    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                        result = recon.main([
                            "capture-effect-evidence", "--repo-root", str(self.repo), "dir/link.bin",
                        ])
        self.assertEqual(result, 1)
        self.assertEqual(stdout.getvalue(), "")
        payload = json.loads(stderr.getvalue().splitlines()[0])
        self.assertEqual(payload["reason_code"], "effect-path-escapes-root")
        self.assertIn("OUTCOME: fail", stderr.getvalue())

    def test_effect_descriptor_duplication_error_is_tool_error(self):
        root_fd = os.open(self.repo, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.dict(os.environ, self.CLI_TEST_ENV, clear=True):
            with mock.patch.object(recon, "_open_repository_root", return_value=root_fd):
                with mock.patch.object(recon.os, "dup", side_effect=OSError(errno.EMFILE, "too many open files")):
                    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                        result = recon.main([
                            "capture-effect-evidence", "--repo-root", str(self.repo), "dir/good.bin",
                        ])
        self.assertEqual(result, 3)
        self.assertEqual(stdout.getvalue(), "")
        payload = json.loads(stderr.getvalue().splitlines()[0])
        self.assertEqual(payload["reason_code"], "effect-path-unreadable")
        self.assertIn("OUTCOME: tool_error", stderr.getvalue())
        with self.assertRaises(OSError):
            os.fstat(root_fd)

    def test_fifo_without_writer_refuses_promptly_with_no_map(self):
        fifo = self.repo / "dir" / "waiting.fifo"
        os.mkfifo(fifo)
        result = self.run_capture("dir/waiting.fifo", timeout=2.0)
        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stdout, "")
        self.assertIn("OUTCOME: tool_error", result.stderr)

    def test_capture_refuses_unreadable_file(self):
        (self.repo / "dir" / "private.bin").write_bytes(b"private")
        with mock.patch.object(recon, "_open_regular_file_at", side_effect=PermissionError("denied")):
            with self.assertRaises(recon._ToolError):
                recon.capture_effect_evidence(self.repo, ["dir/private.bin"])

    def test_capture_cli_reports_unreadable_file_as_tool_error(self):
        (self.repo / "dir" / "private.bin").write_bytes(b"private")
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.dict(os.environ, self.CLI_TEST_ENV, clear=True):
            with mock.patch.object(recon, "_open_regular_file_at", side_effect=PermissionError("denied")):
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    rc = recon.main(["capture-effect-evidence", "--repo-root", str(self.repo), "dir/private.bin"])
        self.assertEqual(rc, 3)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("OUTCOME: tool_error", stderr.getvalue())

    def test_parent_directory_symlink_swap_stays_on_held_directory_descriptor(self):
        original_dir = self.repo / "dir"
        original_file = original_dir / "target.bin"
        original_file.write_bytes(b"inside")
        outside = self.root / "outside"
        outside.mkdir()
        outside_file = outside / "target.bin"
        outside_file.write_bytes(b"outside")
        moved_dir = self.repo / "dir-held"
        real_open = recon._open_directory_at
        swapped = False

        def open_then_swap(parent_fd, component):
            nonlocal swapped
            fd = real_open(parent_fd, component)
            if component == "dir" and not swapped:
                original_dir.rename(moved_dir)
                original_dir.symlink_to(outside, target_is_directory=True)
                swapped = True
            return fd

        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.dict(os.environ, self.CLI_TEST_ENV, clear=True), mock.patch.object(recon, "_open_directory_at", side_effect=open_then_swap):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                rc = recon.main(["capture-effect-evidence", "--repo-root", str(self.repo), "dir/target.bin"])
        self.assertTrue(swapped)
        self.assertEqual(rc, 0, stderr.getvalue())
        output = stdout.getvalue().splitlines()
        self.assertEqual(output[-1], "OUTCOME: pass")
        evidence = json.loads(output[0])["effect_evidence"]
        self.assertEqual(evidence["dir/target.bin"], hashlib.sha256(b"inside").hexdigest())
        self.assertNotIn(hashlib.sha256(b"outside").hexdigest(), output[0])

    def test_repository_root_swap_to_symlink_refuses_without_outside_read_or_output(self):
        (self.repo / "dir" / "target.bin").write_bytes(b"inside")
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "dir").mkdir()
        (outside / "dir" / "target.bin").write_bytes(b"outside")
        moved_repo = self.root / "repo-held"
        real_stat = recon._stat_at
        swapped = False

        def stat_then_swap(parent_fd, name):
            nonlocal swapped
            result = real_stat(parent_fd, name)
            if name == self.repo.name and not swapped:
                self.repo.rename(moved_repo)
                self.repo.symlink_to(outside, target_is_directory=True)
                swapped = True
            return result

        stdout = io.StringIO()
        stderr = io.StringIO()
        started = time.monotonic()
        with mock.patch.dict(os.environ, self.CLI_TEST_ENV, clear=True), mock.patch.object(recon, "_stat_at", side_effect=stat_then_swap):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                rc = recon.main(["capture-effect-evidence", "--repo-root", str(self.repo), "dir/target.bin"])
        elapsed = time.monotonic() - started
        self.assertTrue(swapped)
        self.assertLess(elapsed, 2.0)
        self.assertEqual(rc, 3, stderr.getvalue())
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("OUTCOME: tool_error", stderr.getvalue())
        self.assertNotIn(hashlib.sha256(b"outside").hexdigest(), stderr.getvalue())

    def test_parent_producer_contracts_use_capture_command_and_defer_state_writes(self):
        repo_root = Path(__file__).resolve().parents[1]
        loop = (repo_root / "agents/skills/execute-plan/implementation-loop.md").read_text()
        contract = (repo_root / "agents/skills/execute-plan/runtime-contract.md").read_text()
        loop_producer = loop.split("**Pre-prompt scope and effect record:**", 1)[1].split("**Inline fallback:**", 1)[0]
        contract_producer = contract.split("For scope-drift recovery, the parent records", 1)[1].split("The scope-drift recovery admission order", 1)[0]
        self.assertIn("capture-effect-evidence", loop_producer)
        self.assertIn("effect_baseline", loop_producer)
        self.assertIn("Write runtime state only after the command returns a complete successful map", loop_producer)
        self.assertIn("capture-effect-evidence", contract_producer)
        self.assertIn("at acceptance it invokes the same command", contract_producer)
        self.assertIn("post-only `effect_evidence`", contract_producer)
        self.assertIn("refuses before producer state writes", contract_producer)
        self.assertIn("records no baseline half", contract_producer)


class ProtectedPlanWriteRegressionTest(ReconciliationFixtureTest):
    """The plan write path keeps launched task scope stable, and the
    workflow contracts describe the same prelaunch/postlaunch split."""

    def test_preserve_cleanup_then_checkbox_write_keeps_task_scope(self) -> None:
        # Rebuild the fixture's launch bytes with legacy punctuation both
        # inside and outside the task. The plan digest and scope witnesses
        # are then captured from those exact bytes.
        launch = self.fx.plan_path.read_text(encoding="utf-8")
        launch = launch.replace("Fixture term: the launched scope digest normalizes the checkbox markers only.",
                                "Fixture term: the launched scope " + chr(0x2014) + " digest normalizes checkbox markers.")
        launch = launch.replace("First clause for task one.", "First clause " + chr(0x2014) + " for task one.")
        launch = launch.replace("- [x] First clause " + chr(0x2014) + " for task one.",
                                "- [ ] First clause " + chr(0x2014) + " for task one.")
        launch = launch.replace("- [x] Second clause for task one.", "- [ ] Second clause for task one.")
        self.fx.plan_path.write_text(launch, encoding="utf-8")
        launch_scope = recon.task_scope_digest(task_section(launch, 1))
        self.fx.mutate_state(lambda state: (
            state.__setitem__("plan_digest", self.fx.plan_digest()),
            state["tasks"]["1"].__setitem__("task_scope_digest", launch_scope),
        ))

        original_task = task_section(launch, 1)
        completed = subprocess.run(
            [sys.executable, plan_fixer.__file__, "--preserve-tasks", str(self.fx.plan_path)],
            capture_output=True, text=True, timeout=30, env=self.fx.subprocess_env(),
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        after_cleanup = self.fx.plan_path.read_text(encoding="utf-8")
        self.assertEqual(task_section(after_cleanup, 1), original_task)
        self.assertIn("Fixture term: the launched scope, digest", after_cleanup)

        # The ordinary checkbox-only task boundary preserves the same scope.
        marked = (after_cleanup
                  .replace("- [ ] First clause " + chr(0x2014) + " for task one.",
                           "- [x] First clause " + chr(0x2014) + " for task one.")
                  .replace("- [ ] Second clause for task one.", "- [x] Second clause for task one."))
        self.fx.plan_path.write_text(marked, encoding="utf-8")
        self.fx.write_review(2, self.fx.plan_digest())
        process = self.fx.run_cli()
        self.assertEqual(process.returncode, 0, process.stderr)
        receipt = self.fx.read_state()["tasks"]["1"]["handoff_reconciliation"]
        self.assertEqual(receipt["task_scope_digest"], launch_scope)

    def test_preacceptance_recovery_requires_liveness_before_writes(self) -> None:
        runtime = (Path(SCRIPTS_DIR).parent
                   / "agents/skills/execute-plan/runtime-contract.md")
        contract = runtime.read_text(encoding="utf-8")
        liveness = contract.index("Before any plan, task-path, or runtime-state write")
        source_validation = contract.index("Before any write, use the reconciliation helper")
        restore = contract.index("restore the verified launch bytes")
        dispatch = contract.index("Before recovery dispatch")
        self.assertLess(liveness, source_validation)
        self.assertLess(source_validation, restore)
        self.assertLess(liveness, dispatch)
        normalized = " ".join(contract.split())
        self.assertIn("Do not restore the plan while liveness is unknown", normalized)
        self.assertIn("immediately before every plan write and recovery dispatch", normalized)

    def test_protected_write_contract_is_declared_at_each_owner(self) -> None:
        plans = Path(SCRIPTS_DIR).parent / "agents/skills/plans/SKILL.md"
        execution = Path(SCRIPTS_DIR).parent / "agents/skills/execute-plan/implementation-loop.md"
        runtime = Path(SCRIPTS_DIR).parent / "agents/skills/execute-plan/runtime-contract.md"
        agent_logs = Path(SCRIPTS_DIR).parent / "agents/skills/execute-plan/agent-logs.md"
        invocation = Path(SCRIPTS_DIR).parent / "agents/skills/execute-plan/invocation-and-orchestration.md"
        documents = {
            "plans skill": plans.read_text(encoding="utf-8"),
            "execute-plan implementation loop": execution.read_text(encoding="utf-8"),
            "execute-plan runtime contract": runtime.read_text(encoding="utf-8"),
            "execute-plan agent logs": agent_logs.read_text(encoding="utf-8"),
            "execute-plan invocation contract": invocation.read_text(encoding="utf-8"),
        }
        required = {
            "plans skill": (
                "--preserve-tasks", "before the first task launch",
                "in full mode before recording",
                "before recording `runtime_state.plan_digest` or task-scope digests",
                "sole postlaunch exception", "before each write", "plan-deliverables.txt",
            ),
            "execute-plan implementation loop": ("--preserve-tasks", "task_scope_digest"),
            "execute-plan runtime contract": (
                "equals the saved launch digest", "tasks[task_id].task_scope_digest",
                "plan-source-missing", "plan-source-digest-mismatch",
                "plan-task-scope-mismatch", "leaving the plan, task record, and runtime evidence unchanged",
                "run_base", "session_start_commit", "primary checkout",
                "arbitrary refs, branches, or snapshots", "checkbox projections",
                "whose runtime records have an accepted terminal receipt and `checkbox: true`",
                "current bytes equal that projection", "continue without restoration",
                "reconstructed expected projection", "before each plan write",
                "after every successful plan mutation",
                "original-worker-liveness-unknown", "do not fabricate a terminal receipt",
                "before any plan, task-path, or runtime-state write",
                "do not restore the plan while liveness is unknown",
                "immediately before every plan write and recovery dispatch",
                "distinct recovery worker", "existing diff",
            ),
            "execute-plan agent logs": ("task-<N>-recovery.log.md", "does not write a receipt"),
            "execute-plan invocation contract": (
                "do not synthesize a receipt", "do not relaunch the original worker",
            ),
        }
        for owner, fragments in required.items():
            normalized = " ".join(documents[owner].split()).lower()
            for fragment in fragments:
                with self.subTest(owner=owner, fragment=fragment):
                    self.assertTrue(
                        fragment.lower() in normalized,
                        f"{owner} omits required contract text: {fragment}",
                    )


class GitEnvironmentIsolationTest(ReconciliationFixtureTest):
    """CLI fixtures never inherit repository redirection from the caller."""

    def test_reconcile_cli_ignores_inherited_git_dir(self):
        decoy = self.fx.root / "decoy.git"
        subprocess.run(
            ["git", "init", "--bare", str(decoy)],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
            env=self.fx.subprocess_env(),
        )
        with mock.patch.dict(os.environ, {"GIT_DIR": str(decoy)}):
            process = self.fx.run_cli()
        self.assertEqual(process.returncode, 0, process.stderr + process.stdout)
        self.assertEqual(self.fx.final_outcome(process), "OUTCOME: pass")



if __name__ == "__main__":
    unittest.main()
