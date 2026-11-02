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

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import reconcile_execute_plan_handoff as recon  # noqa: E402

RECONCILE_SCRIPT = os.path.join(SCRIPTS_DIR, "reconcile_execute_plan_handoff.py")

SESSION = "fixture-session-0f3e"
RUN_SESSION_ID = "run-fixture-0f3e"
PLAN_REL = "docs/history/plans/2026-10-01-recon-fixture-story.md"
PLAN_SLUG = "2026-10-01-recon-fixture-story"
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
        env = os.environ.copy()
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
        task: int = 1,
        session: str = SESSION,
        state: Path | None = None,
        plan: Path | None = None,
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable,
                RECONCILE_SCRIPT,
                "reconcile",
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
            timeout=120,
            env=self.subprocess_env(),
        )

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
        self.assertEqual(process.returncode, 0, process.stderr)
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
        self.fx.write_review(2, self.fx.plan_digest())
        before = self.fx.capture()
        result = self.assert_refusal(self.fx.run_cli(), "task-scope-changed")
        self.assertIn(self.fx.launch_scope_one, result["evidence"][0])
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
        if record.get("terminal_receipt"):
            if record.get("status") not in DONE_STATUSES:
                return f"unresolved-done-handoff:{key}"
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


if __name__ == "__main__":
    unittest.main()
