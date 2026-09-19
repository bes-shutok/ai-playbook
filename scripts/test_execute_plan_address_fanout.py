#!/usr/bin/env python3
"""Hermetic harness for the execute-plan address fan-out parent entrypoint.

Every case runs the production ``run_address_fanout`` entrypoint over a
temporary Git repository with deterministic worker doubles and real
``git diff --binary`` patches. The entrypoint never edits the staging doc
and never commits; the parent merge is a single per-round commit.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import execute_plan_address_fanout as fanout  # noqa: E402
import execute_plan_runtime as runtime  # noqa: E402
import validate_review_staging as vrs  # noqa: E402


class AddressFanoutHarness(unittest.TestCase):
    SECRET = "fanout-harness-secret"

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base = Path(self.temp_dir.name)
        self.repo = self.base / "repo"
        self.repo.mkdir(parents=True)
        self.tmp = self.base / "tmp"
        self.workspace_root = self.tmp / "execute-plan" / "fixture-plan"
        # Hermetic git: neutralize host global/system config so hooks,
        # gpgsign, or aliases from the developer machine cannot leak into
        # the fixture repository; identity is set repo-locally below.
        self._git_env = dict(os.environ)
        self._git_env["GIT_CONFIG_GLOBAL"] = "/dev/null"
        self._git_env["GIT_CONFIG_SYSTEM"] = "/dev/null"
        self._git("init", "-q")
        self._git("config", "user.email", "fanout@example.invalid")
        self._git("config", "user.name", "Fanout Test")
        for name in ("a.txt", "b.txt", "c.txt"):
            (self.repo / name).write_text(f"original {name}\n", encoding="utf-8")
        (self.repo / "blob.bin").write_bytes(bytes(range(64)))
        self._git("add", ".")
        self._git("commit", "-qm", "fixture")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _git(self, *args, cwd=None, check=True):
        return subprocess.run(
            ["git", *args],
            cwd=cwd or self.repo,
            env=self._git_env,
            capture_output=True,
            text=True,
            check=check,
        )

    def _head(self) -> str:
        return self._git("rev-parse", "HEAD").stdout.strip()

    def _commit_count(self) -> int:
        return int(self._git("rev-list", "HEAD", "--count").stdout.strip())

    def _binary_patch(self, workspace: Path) -> bytes:
        """Real git (binary-capable) patch for the workspace's edits."""

        self._git("add", "-N", ".", cwd=workspace)
        completed = subprocess.run(
            ["git", "diff", "--binary"],
            cwd=workspace,
            env=self._git_env,
            capture_output=True,
            check=True,
        )
        return completed.stdout

    def success_behavior(self, edits, counts=None):
        """Deterministic worker double: apply edits in the injected workspace
        and return a real binary-capable patch plus its changed-path
        receipt, attempt echo, and token digest."""

        def launch(directive):
            workspace = Path(directive["workspace"])
            for name, content in edits.items():
                target = workspace / name
                if content is None:
                    target.unlink()
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if isinstance(content, bytes):
                        target.write_bytes(content)
                    else:
                        target.write_text(content, encoding="utf-8")
            patch = self._binary_patch(workspace)
            return {
                "status": "success",
                "patch": patch,
                "changed_paths": sorted(fanout.patch_changed_paths(patch)),
                "attempt": directive["attempt"],
                "token_digest": directive["token_digest"],
                "counts": counts
                or {"fixed": len(directive["findings"]), "dropped": 0, "deferred": 0, "pending": 0},
                "triage": {finding_id: {"status": "done"} for finding_id in directive["findings"]},
            }

        return launch

    def run_fanout(self, finding_files, behaviors, cancellation=None, round_id="r1", **overrides):
        launches = []

        def worker_port(directive):
            launches.append(directive)
            behavior = behaviors.get(directive["worker"])
            if behavior is None:
                raise AssertionError(f"unexpected worker launch: {directive['worker']}")
            return behavior(directive)

        result = fanout.run_address_fanout(
            round_id,
            finding_files,
            self.repo,
            self.workspace_root,
            self.SECRET,
            worker_port,
            cancellation or (lambda directive: True),
            **overrides,
        )
        return result, launches

    def test_address_fanout_transitive_grouping(self):
        finding_files = {
            1: ["src/a.py", "src/b.py"],
            2: ["src/b.py", "src/c.py"],
            3: ["src/c.py", "src/d.py"],
            4: ["docs/e.md"],
        }
        plan = fanout.plan_fanout(finding_files)
        self.assertEqual(plan["mode"], "fanout")
        # Findings 1-3 share files transitively (b.py, c.py) and land in one
        # worker; finding 4 is disjoint.
        self.assertEqual(sorted(plan["workers"][0]["findings"]), [1, 2, 3])
        self.assertEqual(sorted(plan["workers"][1]["findings"]), [4])
        first_files = set(plan["workers"][0]["files"])
        second_files = set(plan["workers"][1]["files"])
        self.assertTrue(first_files.isdisjoint(second_files))
        self.assertEqual(
            sorted(first_files | second_files),
            sorted({path for paths in finding_files.values() for path in paths}),
        )
        # Deterministic: identical input, identical grouping.
        self.assertEqual(plan, fanout.plan_fanout(finding_files))
        # Greedy packing caps at three workers.
        five = fanout.plan_fanout({finding_id: [f"f{finding_id}.txt"] for finding_id in range(1, 6)})
        self.assertEqual(five["mode"], "fanout")
        self.assertEqual(len(five["workers"]), 3)

    def test_address_fanout_scope_violation_is_quarantined(self):
        finding_files = {1: ["a.txt"], 2: ["c.txt"]}
        violating_behavior = self.success_behavior({"c.txt": "w2 fix\n", "intruder.txt": "out of scope\n"})

        result, launches = self.run_fanout(
            finding_files,
            {"w1": self.success_behavior({"a.txt": "w1 fix\n"}), "w2": violating_behavior},
        )
        self.assertEqual(result["mode"], "fanout")
        self.assertEqual(result["merge_receipt"]["applied"], ["w1"])
        record = result["record"]
        self.assertEqual(record["terminal"].get("w2"), fanout.REASON_SCOPE_VIOLATION)
        self.assertTrue(
            any(
                entry["worker"] == "w2" and entry["reason_code"] == fanout.REASON_SCOPE_VIOLATION
                for entry in record["quarantined"]
            )
        )
        # The quarantined patch can never mutate the parent worktree.
        self.assertFalse((self.repo / "intruder.txt").exists())
        self.assertEqual((self.repo / "a.txt").read_text(encoding="utf-8"), "w1 fix\n")
        self.assertEqual((self.repo / "c.txt").read_text(encoding="utf-8"), "original c.txt\n")
        merge = result["merge_receipt"]
        self.assertEqual(merge["blocked_subsets"], {"w2": fanout.REASON_SCOPE_VIOLATION})
        self.assertEqual(merge["counts"]["fixed"], 1)
        self.assertEqual(len(launches), 2)

    def test_address_fanout_subset_retry_requires_termination(self):
        finding_files = {1: ["a.txt"], 2: ["c.txt"]}

        def timed_out_once(directive):
            raise fanout.WorkerFailure(fanout.REASON_WORKER_TIMEOUT)

        # Arm 1: cancellation unverified -> terminal blocked subset, no retry.
        result, launches = self.run_fanout(
            finding_files,
            {"w1": timed_out_once, "w2": self.success_behavior({"c.txt": "w2 fix\n"})},
            cancellation=lambda directive: False,
            round_id="r1",
        )
        self.assertEqual([d["attempt"] for d in launches if d["worker"] == "w1"], ["a1"])
        self.assertEqual(result["merge_receipt"]["blocked_subsets"], {"w1": fanout.REASON_CANCELLATION_UNVERIFIED})
        self.assertEqual(result["record"]["terminal"]["w1"], fanout.REASON_CANCELLATION_UNVERIFIED)
        self.assertEqual(result["merge_receipt"]["applied"], ["w2"])
        # Each round starts from a clean committed worktree.
        self._git("reset", "--hard", "HEAD")

        # Arm 2: verified termination -> exactly one retry on the same subset.
        attempts_seen = []

        def failing_then_fixed(directive):
            attempts_seen.append(directive["attempt"])
            if directive["attempt"] == "a1":
                raise fanout.WorkerFailure(fanout.REASON_WORKER_TIMEOUT)
            return self.success_behavior({"a.txt": "w1 retry fix\n"})(directive)

        result, launches = self.run_fanout(
            finding_files,
            {"w1": failing_then_fixed, "w2": self.success_behavior({"c.txt": "w2 fix\n"})},
            round_id="r2",
        )
        self.assertEqual(attempts_seen, ["a1", "a2"])
        self.assertEqual([d["attempt"] for d in launches if d["worker"] == "w1"], ["a1", "a2"])
        self.assertEqual(result["merge_receipt"]["applied"], ["w1", "w2"])
        self.assertEqual((self.repo / "a.txt").read_text(encoding="utf-8"), "w1 retry fix\n")
        retry_directive = next(d for d in launches if d["worker"] == "w1" and d["attempt"] == "a2")
        self.assertEqual(sorted(retry_directive["findings"]), [1])
        self.assertEqual(sorted(retry_directive["files"]), ["a.txt"])
        self._git("reset", "--hard", "HEAD")

        # Arm 3: second failure -> terminal blocked subset, never a third attempt.
        def always_times_out(directive):
            raise fanout.WorkerFailure(fanout.REASON_WORKER_TIMEOUT)

        result, launches = self.run_fanout(
            finding_files,
            {"w1": always_times_out, "w2": self.success_behavior({"c.txt": "w2 fix\n"})},
            round_id="r3",
        )
        self.assertEqual(sorted({d["attempt"] for d in launches if d["worker"] == "w1"}), ["a1", "a2"])
        self.assertEqual(result["record"]["terminal"]["w1"], fanout.REASON_WORKER_ERROR)
        self.assertEqual(result["merge_receipt"]["applied"], ["w2"])

    def test_address_fanout_missing_file_data_falls_back(self):
        finding_files = {1: ["a.txt"], 2: []}
        result, launches = self.run_fanout(
            finding_files,
            {"w1": self.success_behavior({"a.txt": "never written\n"})},
        )
        self.assertEqual(result["mode"], "single")
        self.assertEqual(result["reason"], "missing-file-data")
        self.assertEqual(result["transitions"], [])
        self.assertIsNone(result["record"])
        self.assertIsNone(result["merge_receipt"])
        self.assertEqual(launches, [])
        self.assertEqual((self.repo / "a.txt").read_text(encoding="utf-8"), "original a.txt\n")
        # Ambiguous non-string file data is also missing file data.
        result, _ = self.run_fanout({1: ["a.txt"], 2: ["c.txt", 7]}, {})
        self.assertEqual(result["mode"], "single")
        self.assertEqual(result["reason"], "missing-file-data")

    def test_address_fanout_parent_merge_is_single_commit(self):
        finding_files = {1: ["a.txt"], 2: ["c.txt"]}
        head_before = self._head()
        count_before = self._commit_count()
        result, _ = self.run_fanout(
            finding_files,
            {
                "w1": self.success_behavior({"a.txt": "w1 fix\n"}),
                "w2": self.success_behavior({"c.txt": "w2 fix\n"}),
            },
        )
        self.assertEqual(result["mode"], "fanout")
        # The entrypoint never creates a commit.
        self.assertEqual(self._head(), head_before)
        self.assertEqual(self._commit_count(), count_before)
        # The parent merges worker results and lands the round's single
        # address commit as the usual per-round done.
        self._git("add", "-A")
        self._git("commit", "-qm", "address r1")
        self.assertEqual(self._commit_count(), count_before + 1)
        self.assertEqual((self.repo / "a.txt").read_text(encoding="utf-8"), "w1 fix\n")
        self.assertEqual((self.repo / "c.txt").read_text(encoding="utf-8"), "w2 fix\n")
        self.assertNotIn("commit", result)
        self.assertEqual(result["merge_receipt"]["applied"], ["w1", "w2"])

    def test_address_fanout_assignment_is_complete(self):
        finding_files = {
            1: ["x/1.py"],
            2: ["x/1.py", "x/2.py"],
            3: ["x/3.py"],
            4: ["x/4.py"],
            5: ["x/5.py"],
        }
        plan = fanout.plan_fanout(finding_files)
        self.assertEqual(plan["mode"], "fanout")
        workers = plan["workers"]
        self.assertLessEqual(len(workers), fanout.MAX_FANOUT_WORKERS)
        self.assertGreaterEqual(len(workers), 2)
        assigned: list[int] = []
        for worker in workers:
            assigned.extend(worker["findings"])
            expected_files = sorted({path for finding_id in worker["findings"] for path in finding_files[finding_id]})
            self.assertEqual(sorted(worker["files"]), expected_files)
        self.assertEqual(sorted(assigned), sorted(finding_files))
        self.assertEqual(len(assigned), len(set(assigned)), "every finding id occurs in exactly one worker")
        file_sets = [set(worker["files"]) for worker in workers]
        for index, files in enumerate(file_sets):
            for other in file_sets[index + 1 :]:
                self.assertTrue(files.isdisjoint(other))

    def test_address_fanout_entrypoint_launches_and_merges_with_worker_doubles(self):
        finding_files = {1: ["a.txt"], 2: ["b.txt", "blob.bin"], 3: ["c.txt"]}
        head_before = self._head()
        directives = []

        def recording(behavior):
            def launch(directive):
                directives.append(dict(directive))
                return behavior(directive)

            return launch

        result, _ = self.run_fanout(
            finding_files,
            {
                "w1": recording(self.success_behavior({"a.txt": "w1 fix\n"})),
                "w2": recording(
                    self.success_behavior({"b.txt": "w2 fix\n", "blob.bin": bytes(range(64, 128))})
                ),
                "w3": recording(self.success_behavior({"c.txt": "w3 fix\n"})),
            },
        )
        self.assertEqual(result["mode"], "fanout")
        self.assertEqual(len(directives), 3)
        round_directives = sorted(directives, key=lambda directive: directive["worker"])
        for directive in round_directives:
            self.assertEqual(directive["round"], "r1")
            self.assertEqual(directive["attempt"], "a1")
            self.assertEqual(directive["baseline"], head_before)
            self.assertEqual(len(directive["token"]), 64)
            self.assertEqual(directive["token_digest"], fanout.token_digest(directive["token"]))
            self.assertTrue(Path(directive["workspace"]).exists())
            self.assertTrue((Path(directive["workspace"]) / ".git").exists())
            self.assertTrue(Path(directive["workspace"]).resolve().is_relative_to(self.workspace_root.resolve()))
        self.assertEqual(round_directives[0]["log"], "review-r1-receiving-review-w1.log.md")
        self.assertTrue(round_directives[0]["workspace"].endswith("address-r1-w1-a1"))
        self.assertEqual(round_directives[0]["files"], ["a.txt"])
        self.assertEqual(round_directives[0]["findings"], [1])
        # All three accepted patches applied serially into the parent worktree.
        self.assertEqual(result["merge_receipt"]["applied"], ["w1", "w2", "w3"])
        self.assertEqual((self.repo / "a.txt").read_text(encoding="utf-8"), "w1 fix\n")
        self.assertEqual((self.repo / "b.txt").read_text(encoding="utf-8"), "w2 fix\n")
        self.assertEqual((self.repo / "c.txt").read_text(encoding="utf-8"), "w3 fix\n")
        self.assertEqual((self.repo / "blob.bin").read_bytes(), bytes(range(64, 128)))
        self.assertEqual(self._head(), head_before)
        record = result["record"]
        self.assertEqual(record["baseline"], head_before)
        self.assertEqual(sorted(record["workers"]), ["w1", "w2", "w3"])
        for name, worker_record in record["workers"].items():
            self.assertEqual(worker_record["status"], "accepted")
            self.assertIsNotNone(worker_record["accepted"])
            # The acceptance closes the active attempt as completed.
            self.assertEqual(worker_record["attempts"][0]["event"], "completed")
        self.assertEqual(result["merge_receipt"]["counts"], {"fixed": 3, "dropped": 0, "deferred": 0, "pending": 0})
        self.assertEqual(result["transitions"][0]["kind"], "start")
        self.assertEqual(record["grouping"][0]["worker"], "w1")
        self.assertEqual(sorted(record["grouping"][1]["findings"]), [2])
        self.assertEqual(sorted(record["grouping"][2]["files"]), ["c.txt"])

    def test_address_fanout_late_attempt_receipt_is_quarantined(self):
        finding_files = {1: ["a.txt"], 2: ["c.txt"]}
        state: dict[str, dict] = {}

        def late_first_attempt(directive):
            if directive["attempt"] == "a1":
                state["a1"] = dict(directive)
                raise fanout.WorkerFailure(fanout.REASON_WORKER_TIMEOUT)
            # The cancelled first attempt returns only after the retry (a2)
            # result: both receipts arrive in one collected batch, a1 last.
            a1_workspace = Path(state["a1"]["workspace"])
            (a1_workspace / "a.txt").write_text("stale a1 fix\n", encoding="utf-8")
            stale_patch = self._binary_patch(a1_workspace)
            late = {
                "status": "success",
                "patch": stale_patch,
                "changed_paths": sorted(fanout.patch_changed_paths(stale_patch)),
                "attempt": state["a1"]["attempt"],
                "token_digest": state["a1"]["token_digest"],
                "counts": {"fixed": 1, "dropped": 0, "deferred": 0, "pending": 0},
            }
            fresh = self.success_behavior({"a.txt": "a2 fix\n"})(directive)
            return [fresh, late]

        result, launches = self.run_fanout(
            finding_files,
            {"w1": late_first_attempt, "w2": self.success_behavior({"c.txt": "w2 fix\n"})},
        )
        self.assertEqual(result["mode"], "fanout")
        self.assertEqual(result["merge_receipt"]["applied"], ["w1", "w2"])
        record = result["record"]
        # The retry's accepted result stands; the late a1 receipt never
        # mutates machine state or the worktree. A CAS-refused quarantine
        # leaves no machine-state entry: the evidence is the refused
        # transition, the accepted receipt staying on a2, and the worktree
        # content coming from a2 only.
        self.assertEqual(record["workers"]["w1"]["accepted"]["attempt"], "a2")
        self.assertEqual((self.repo / "a.txt").read_text(encoding="utf-8"), "a2 fix\n")
        stale_transitions = [
            transition
            for transition in result["transitions"]
            if transition["kind"] == "quarantine"
            and transition["worker"] == "w1"
            and transition["attempt"] == "a1"
            and fanout.REASON_STALE_ATTEMPT in str(transition.get("detail", ""))
        ]
        self.assertEqual(len(stale_transitions), 1)
        self.assertEqual(
            [entry for entry in record["quarantined"] if entry["worker"] == "w1"],
            [],
            "a CAS-refused late receipt cannot mutate machine state",
        )
        attempts = {entry["id"]: entry for entry in record["workers"]["w1"]["attempts"]}
        self.assertEqual(attempts["a1"]["event"], "cancelled-verified")
        self.assertEqual(attempts["a2"]["event"], "completed")
        self.assertEqual(record["terminal"], {})
        self.assertEqual(sorted({d["attempt"] for d in launches if d["worker"] == "w1"}), ["a1", "a2"])
        self.assertEqual(result["merge_receipt"]["counts"]["fixed"], 2)


    def test_reason_code_enum_matches_validator_pins(self) -> None:
        # r1 F21: the producer constants in execute_plan_address_fanout are
        # the definition site of the closed enum; the validator pins the
        # same set by equality.
        self.assertEqual(fanout.REASON_CODES, vrs.ADDRESS_FANOUT_REASON_CODES)
        self.assertEqual(
            fanout._TERMINAL_REASONS,
            {fanout.REASON_CANCELLATION_UNVERIFIED, fanout.REASON_AMBIGUOUS_PATCH, fanout.REASON_SCOPE_VIOLATION},
        )

    def test_traditional_unified_diff_cannot_bypass_scope_witness(self) -> None:
        # r1 F6: a plain unified diff (no diff --git headers) parses to the
        # empty header set, but git's own numstat witness derives the real
        # changed path. The disagreement is an ambiguous patch: quarantined
        # terminally, the parent worktree byte-identical.
        finding_files = {1: ["a.txt"], 2: ["c.txt"]}
        traditional = (
            b"--- a/a.txt\n+++ b/a.txt\n@@ -1 +1 @@\n-original a.txt\n+w1 traditional fix\n"
        )

        def traditional_worker(directive):
            return {
                "status": "success",
                "patch": traditional,
                "changed_paths": ["a.txt"],
                "attempt": directive["attempt"],
                "token_digest": directive["token_digest"],
                "counts": {"fixed": 1, "dropped": 0, "deferred": 0, "pending": 0},
            }

        ok, derived = fanout.git_numstat_paths(self.repo, traditional)
        self.assertTrue(ok)
        self.assertEqual(derived, {"a.txt"})
        self.assertEqual(fanout.patch_changed_paths(traditional), set(), "the header parse alone is blind to this diff")

        result, _ = self.run_fanout(
            finding_files,
            {"w1": traditional_worker, "w2": self.success_behavior({"c.txt": "w2 fix\n"})},
        )
        record = result["record"]
        self.assertEqual(record["terminal"].get("w1"), fanout.REASON_AMBIGUOUS_PATCH)
        self.assertEqual(result["merge_receipt"]["applied"], ["w2"])
        self.assertEqual((self.repo / "a.txt").read_text(encoding="utf-8"), "original a.txt\n")

    def test_numstat_refusal_or_disagreement_is_an_ambiguous_patch(self) -> None:
        # r1 F6 arms: numstat failing and numstat disagreeing with the
        # header parse each reject, never an empty-path pass.
        git_patch = self._binary_patch(self._worktree_copy())
        receipt = sorted(fanout.patch_changed_paths(git_patch))
        submission = {
            "attempt": "a1",
            "token_digest": fanout.token_digest("t"),
            "patch": git_patch,
            "changed_paths": receipt,
        }
        failing = fanout.verify_patch_submission(
            submission, ["a.txt"], submission["token_digest"], "a1", numstat_port=lambda _patch: (False, set())
        )
        self.assertEqual(failing, [fanout.REASON_AMBIGUOUS_PATCH])
        disagreeing = fanout.verify_patch_submission(
            submission, ["a.txt"], submission["token_digest"], "a1", numstat_port=lambda _patch: (True, {"elsewhere.txt"})
        )
        self.assertEqual(disagreeing, [fanout.REASON_AMBIGUOUS_PATCH])
        agreeing = fanout.verify_patch_submission(
            submission, ["a.txt"], submission["token_digest"], "a1", numstat_port=lambda _patch: (True, set(receipt))
        )
        self.assertEqual(agreeing, [])

    def _worktree_copy(self) -> Path:
        worktree = self.tmp / "witness-copy"
        subprocess.run(
            ["git", "worktree", "add", "--detach", str(worktree), self._head()],
            cwd=self.repo, env=self._git_env, capture_output=True, check=True,
        )
        (worktree / "a.txt").write_text("witness fix\n", encoding="utf-8")
        self._git("add", "-N", ".", cwd=worktree)
        return worktree

    def test_commit_marker_smuggle_is_a_terminal_scope_violation(self) -> None:
        # r1 F7(c): a patch carrying a commit object (format-patch style
        # "From <sha>" marker) is a scope violation, never applied.
        finding_files = {1: ["a.txt"], 2: ["c.txt"]}
        worktree = self._worktree_copy()
        patch = self._binary_patch(worktree)

        def smuggler(directive):
            return {
                "status": "success",
                "patch": b"From 0123456789abcdef0123456789abcdef01234567 Mon Sep 17 00:00:00 2001\n" + patch,
                "changed_paths": sorted(fanout.patch_changed_paths(patch)),
                "attempt": directive["attempt"],
                "token_digest": directive["token_digest"],
                "counts": {"fixed": 1, "dropped": 0, "deferred": 0, "pending": 0},
            }

        result, _ = self.run_fanout(
            finding_files,
            {"w1": smuggler, "w2": self.success_behavior({"c.txt": "w2 fix\n"})},
        )
        self.assertEqual(result["record"]["terminal"], {"w1": fanout.REASON_SCOPE_VIOLATION})
        self.assertEqual(result["merge_receipt"]["applied"], ["w2"])
        self.assertEqual((self.repo / "a.txt").read_text(encoding="utf-8"), "original a.txt\n")

    def test_patch_checker_refusal_terminates_subset(self) -> None:
        # r1 F7(a): a refusing patch checker (patch does not apply cleanly
        # to the recorded baseline) is a terminal ambiguous_patch block.
        finding_files = {1: ["a.txt"], 2: ["c.txt"]}

        def refusing_checker(_repo_root, _patch):
            return False, "refused by the injected checker"

        result, _ = self.run_fanout(
            finding_files,
            {"w1": self.success_behavior({"a.txt": "w1 fix\n"}), "w2": self.success_behavior({"c.txt": "w2 fix\n"})},
            patch_checker=refusing_checker,
        )
        self.assertEqual(result["record"]["terminal"], {"w1": fanout.REASON_AMBIGUOUS_PATCH, "w2": fanout.REASON_AMBIGUOUS_PATCH})
        self.assertEqual(result["merge_receipt"]["applied"], [])
        self.assertEqual((self.repo / "a.txt").read_text(encoding="utf-8"), "original a.txt\n")

    def test_parent_merge_conflict_terminates_the_accepted_worker(self) -> None:
        # r1 F8: after an accept, the patch failing to apply is parent-owned
        # terminal bookkeeping: the accepted attempt is blocked with
        # parent_merge_conflict in the machine record, the worker is not in
        # the applied list, and the other worker's patch lands.
        finding_files = {1: ["a.txt"], 2: ["c.txt"]}

        def raising_port(_repo_root, _patch):
            raise RuntimeError("conflicting worktree state")

        def selective_port(repo_root, patch):
            # w1's patch (a.txt) fails; w2's (c.txt) applies.
            if b"a.txt" in patch.splitlines()[0]:
                raise RuntimeError("conflicting worktree state")
            return fanout.apply_patch(repo_root, patch)

        result, _ = self.run_fanout(
            finding_files,
            {"w1": self.success_behavior({"a.txt": "w1 fix\n"}), "w2": self.success_behavior({"c.txt": "w2 fix\n"})},
            patch_application_port=selective_port,
        )
        merge = result["merge_receipt"]
        self.assertEqual(merge["applied"], ["w2"])
        self.assertEqual(merge["blocked_subsets"], {"w1": fanout.REASON_PARENT_MERGE_CONFLICT})
        record = result["record"]
        self.assertEqual(record["terminal"]["w1"], fanout.REASON_PARENT_MERGE_CONFLICT)
        self.assertEqual(record["workers"]["w1"]["status"], "blocked")
        self.assertEqual((self.repo / "a.txt").read_text(encoding="utf-8"), "original a.txt\n")
        self.assertEqual((self.repo / "c.txt").read_text(encoding="utf-8"), "w2 fix\n")

    def test_drop_only_and_blocked_worker_reports(self) -> None:
        # r1 F9: an honest drop-only submission (empty patch, empty
        # changed-path receipt) is accepted with zero changed paths, and a
        # documented status: blocked report takes the worker-error retry
        # path with cancellation verification, never a terminal
        # ambiguous_patch quarantine.
        finding_files = {1: ["a.txt"], 2: ["c.txt"]}

        def blocked_then_success(directive):
            if directive["attempt"] == "a1":
                return {"status": "blocked", "attempt": "a1", "token_digest": directive["token_digest"]}
            return self.success_behavior({"a.txt": "w1 retry fix\n"})(directive)

        result, launches = self.run_fanout(
            finding_files,
            {"w1": blocked_then_success, "w2": self.success_behavior({"c.txt": "w2 fix\n"})},
        )
        self.assertEqual(result["merge_receipt"]["applied"], ["w1", "w2"])
        self.assertEqual(result["merge_receipt"]["blocked_subsets"], {})
        record = result["record"]
        self.assertEqual([entry["event"] for entry in record["workers"]["w1"]["attempts"]], ["cancelled-verified", "completed"])
        self.assertEqual(record["workers"]["w1"]["attempts"][0]["reason_code"], fanout.REASON_WORKER_ERROR)
        self.assertEqual(sorted({d["attempt"] for d in launches if d["worker"] == "w1"}), ["a1", "a2"])
        # Clean the worktree between arms: each round starts from the
        # recorded baseline.
        self._git("reset", "--hard", "HEAD")
        self._git("clean", "-qfd")

        # Drop-only: the empty patch with an empty receipt is accepted.
        def drop_only(directive):
            return {
                "status": "success",
                "patch": b"",
                "changed_paths": [],
                "attempt": directive["attempt"],
                "token_digest": directive["token_digest"],
                "counts": {"fixed": 0, "dropped": 1, "deferred": 0, "pending": 0},
            }

        result, _ = self.run_fanout(
            {1: ["a.txt"], 2: ["c.txt"]},
            {"w1": drop_only, "w2": self.success_behavior({"c.txt": "w2 drop-only\n"})},
            round_id="r-drop",
        )
        self.assertEqual(result["merge_receipt"]["applied"], ["w1", "w2"])
        # w2's accepted fix plus w1's accepted drop.
        self.assertEqual(result["merge_receipt"]["counts"], {"fixed": 1, "dropped": 1, "deferred": 0, "pending": 0})
        self.assertEqual(result["record"]["workers"]["w1"]["accepted"]["changed_paths"], [])
        self.assertEqual((self.repo / "a.txt").read_text(encoding="utf-8"), "original a.txt\n")

        # An empty patch whose receipt disagrees stays ambiguous.
        def empty_patch_bad_receipt(directive):
            return {
                "status": "success",
                "patch": b"",
                "changed_paths": ["a.txt"],
                "attempt": directive["attempt"],
                "token_digest": directive["token_digest"],
                "counts": {"fixed": 1, "dropped": 0, "deferred": 0, "pending": 0},
            }

        result, _ = self.run_fanout(
            {1: ["a.txt"], 2: ["c.txt"]},
            {"w1": empty_patch_bad_receipt, "w2": self.success_behavior({"c.txt": "w2 x\n"})},
            round_id="r-bad-empty",
        )
        self.assertEqual(result["record"]["terminal"].get("w1"), fanout.REASON_AMBIGUOUS_PATCH)

    def test_accept_count_conservation_fails_closed(self) -> None:
        # r1 O12: counts that do not sum to the worker's finding subset are
        # refused at accept with no mutation, and the run loop quarantines
        # the submission instead of applying the patch.
        finding_files = {1: ["a.txt"], 2: ["c.txt"]}

        def dishonest_counts(directive):
            base = self.success_behavior({"a.txt": "w1 fix\n"})(directive)
            base["counts"] = {"fixed": 5, "dropped": 0, "deferred": 0, "pending": 0}
            return base

        result, _ = self.run_fanout(
            finding_files,
            {"w1": dishonest_counts, "w2": self.success_behavior({"c.txt": "w2 fix\n"})},
        )
        self.assertEqual(result["record"]["terminal"], {"w1": fanout.REASON_AMBIGUOUS_PATCH})
        self.assertEqual(result["merge_receipt"]["applied"], ["w2"])
        self.assertNotEqual(result["record"]["workers"]["w1"].get("status"), "accepted")
        self.assertEqual((self.repo / "a.txt").read_text(encoding="utf-8"), "original a.txt\n")

    def test_canonicalize_tolerates_row_forms_and_bad_ids(self) -> None:
        # r1 O31: the list-of-rows input form is a first-class citizen.
        rows = [
            {"id": 1, "files": ["src/a.py", "src/b.py"]},
            {"id": 2, "files": ["src/c.py"]},
        ]
        canonical, problems = fanout.canonicalize_finding_files(rows)
        self.assertEqual(problems, [])
        self.assertEqual(canonical, {1: ("src/a.py", "src/b.py"), 2: ("src/c.py",)})
        plan = fanout.plan_fanout(rows)
        self.assertEqual(plan["mode"], "fanout")
        self.assertEqual(sorted(plan["workers"][0]["findings"]), [1])
        # A non-mapping row is a problem row with a None id.
        canonical, problems = fanout.canonicalize_finding_files([{"id": 1, "files": ["a.txt"]}, "garbage"])
        self.assertEqual(canonical, {1: ("a.txt",)})
        self.assertEqual(problems, [{"id": None, "reason": "missing-file-data"}])
        # r1 F33: a non-coercible finding id degrades to a problem row
        # instead of crashing the entry.
        canonical, problems = fanout.canonicalize_finding_files([{"id": "F1", "files": ["a.txt"]}, {"id": 2, "files": ["c.txt"]}])
        self.assertEqual(canonical, {2: ("c.txt",)})
        self.assertEqual(problems, [{"id": "F1", "reason": "missing-file-data"}])
        result = fanout.plan_fanout([{"id": "F1", "files": ["a.txt"]}, {"id": 2, "files": ["c.txt"]}])
        self.assertEqual(result["mode"], "single")
        self.assertEqual(result["reason"], "missing-file-data")
        self.assertEqual(result["findings"], ["F1"])
        # Mixed id types degrade without raising on the sort; only failed
        # ids land in the problems projection.
        result = fanout.plan_fanout({1: ["a.txt"], "F9": ["c.txt"]})
        self.assertEqual(result["mode"], "single")
        self.assertEqual(result["findings"], ["F9"])

    def test_parse_worker_submission_documented_prose_shape(self) -> None:
        # r1 F10: the documented Address Fan-out Worker return (workspace
        # patch path plus raw scope token echo) parses into the verifier's
        # submission shape, and the run loop accepts it end to end.
        token = fanout.issue_scope_token("r1", "w1", "a1", self.SECRET)
        digest = fanout.token_digest(token)
        worktree = self._worktree_copy()
        patch = self._binary_patch(worktree)
        workspace = self.tmp / "prose-ws"
        workspace.mkdir(parents=True, exist_ok=True)
        patch_name = "w1.patch"
        (workspace / patch_name).write_bytes(patch)
        return_text = (
            "### Status\nsuccess\n\n"
            "### Token and attempt echo\n"
            f"- Scope token: {token}\n"
            "- Attempt id: a1\n\n"
            "### Binary patch\n"
            f"- {patch_name}\n\n"
            "### Patch digest\n"
            f"- {hashlib.sha256(patch).hexdigest()}\n\n"
            "### Changed-path receipt\n- a.txt\n\n"
            "### Per-finding triage\n- 1: done; fixed\n\n"
            "### Files changed\n- a.txt\n\n"
            "### Tests run\n- none\n\n"
            "### Execution log\n- review-r1-receiving-review-w1.log.md\n"
        )
        submission = fanout.parse_worker_submission(return_text, workspace)
        self.assertEqual(submission["status"], "success")
        self.assertEqual(submission["attempt"], "a1")
        self.assertEqual(submission["token_digest"], digest)
        self.assertEqual(submission["patch"], patch)
        self.assertEqual(submission["patch_digest"], hashlib.sha256(patch).hexdigest())
        self.assertEqual(submission["changed_paths"], ["a.txt"])
        self.assertEqual(submission["counts"], {"fixed": 1, "dropped": 0, "deferred": 0, "pending": 0})
        self.assertEqual(
            fanout.verify_patch_submission(submission, ["a.txt"], digest, "a1", numstat_port=lambda _p: (True, {"a.txt"})),
            [],
        )

        # End to end: the worker double emits the documented prose and the
        # parent parses it before verification.
        def prose_worker(directive):
            ws = Path(directive["workspace"])
            (ws / "a.txt").write_text("w1 e2e prose fix\n", encoding="utf-8")
            self._git("add", "-N", ".", cwd=ws)
            worker_patch = subprocess.run(
                ["git", "diff", "--binary"], cwd=ws, env=self._git_env, capture_output=True, check=True
            ).stdout
            (ws / "w.patch").write_bytes(worker_patch)
            text = (
                "### Status\nsuccess\n\n"
                "### Token and attempt echo\n"
                f"- Scope token: {directive['token']}\n"
                f"- Attempt id: {directive['attempt']}\n\n"
                "### Binary patch\n- w.patch\n\n"
                "### Patch digest\n\n"
                "### Changed-path receipt\n- a.txt\n\n"
                "### Per-finding triage\n- 1: done; fixed\n\n"
                "### Files changed\n- a.txt\n\n"
                "### Tests run\n- none\n\n"
                "### Execution log\n- review-r1-receiving-review-w1.log.md\n"
            )
            return fanout.parse_worker_submission(text, ws)

        result, _ = self.run_fanout(
            {1: ["a.txt"], 2: ["c.txt"]},
            {"w1": prose_worker, "w2": self.success_behavior({"c.txt": "w2 fix\n"})},
            round_id="r-prose",
        )
        self.assertEqual(result["merge_receipt"]["applied"], ["w1", "w2"])
        self.assertEqual((self.repo / "a.txt").read_text(encoding="utf-8"), "w1 e2e prose fix\n")

        # A digest echo that disagrees with the patch bytes fails closed.
        bad = return_text.replace(hashlib.sha256(patch).hexdigest(), "0" * 64)
        with self.assertRaises(ValueError):
            fanout.parse_worker_submission(bad, workspace)
        # A blocked return parses without patch keys.
        blocked = fanout.parse_worker_submission(
            "### Status\nblocked\n\n### Token and attempt echo\n"
            f"- Scope token: {token}\n- Attempt id: a1\n",
            workspace,
        )
        self.assertEqual(blocked, {"status": "blocked", "attempt": "a1", "token": token, "token_digest": digest})
        with self.assertRaises(ValueError):
            fanout.parse_worker_submission("### Status\nconfused\n", workspace)

    def test_two_submission_worker_takes_only_the_accepted_patch(self):
        # r2 F1 (SE-1): a worker returning two valid submissions in one
        # attempt must not swap the applied bytes after the authority
        # refuses the second accept. Pre-fix the take gate read the worker
        # snapshot (still "accepted" from the first accept) instead of the
        # accept outcome itself, so patch 2 was applied to the parent
        # worktree while machine state recorded patch 1's digest.
        finding_files = {1: ["a.txt", "b.txt"], 2: ["a.txt", "b.txt"], 3: ["c.txt"]}
        digests = []

        def two_submission_worker(directive):
            workspace = Path(directive["workspace"])
            (workspace / "a.txt").write_text("w1 fix one\n", encoding="utf-8")
            patch_one = self._binary_patch(workspace)
            (workspace / "b.txt").write_text("w1 fix two\n", encoding="utf-8")
            patch_two = self._binary_patch(workspace)
            digests.append(hashlib.sha256(patch_one).hexdigest())

            def make(patch):
                return {
                    "status": "success",
                    "patch": patch,
                    "changed_paths": sorted(fanout.patch_changed_paths(patch)),
                    "attempt": directive["attempt"],
                    "token_digest": directive["token_digest"],
                    "counts": {"fixed": 2, "dropped": 0, "deferred": 0, "pending": 0},
                    "triage": {},
                }

            return [make(patch_one), make(patch_two)]

        result, _ = self.run_fanout(
            finding_files,
            {"w1": two_submission_worker, "w2": self.success_behavior({"c.txt": "w2 fix\n"})},
        )
        self.assertEqual(result["merge_receipt"]["applied"], ["w1", "w2"])
        # The applied bytes are the FIRST accepted patch: b.txt never lands
        # and the machine record carries patch one's digest.
        self.assertEqual((self.repo / "a.txt").read_text(encoding="utf-8"), "w1 fix one\n")
        self.assertEqual((self.repo / "b.txt").read_text(encoding="utf-8"), "original b.txt\n")
        accepted = result["record"]["workers"]["w1"]["accepted"]
        self.assertEqual(accepted["patch_digest"], digests[0])
        self.assertEqual(result["record"]["workers"]["w1"]["status"], "accepted")

    def test_rename_patches_pass_the_numstat_gate(self):
        # r2 F3: git apply --numstat prints only the post-image path of a
        # rename while the header parse names both sides, so the old
        # whole-set comparison refused every rename patch (terminal
        # ambiguous_patch burned the subset). Plain and quoted renames now
        # compare like with like (post-image), and an out-of-scope rename
        # SOURCE still refuses through the union scope check.
        def rename_patch(old, new):
            # A clean detached worktree (no intent-to-add noise from the
            # witness copy) so the staged rename is the only change: true
            # 100%-similarity rename headers, not a delete-plus-add pair.
            worktree = self.tmp / f"rename-ws-{new}"
            subprocess.run(
                ["git", "worktree", "add", "--detach", str(worktree), self._head()],
                cwd=self.repo, env=self._git_env, capture_output=True, check=True,
            )
            (worktree / old).rename(worktree / new)
            self._git("add", "-A", ".", cwd=worktree)
            return subprocess.run(
                ["git", "-c", "core.quotePath=false", "diff", "--binary", "--cached", "-M"],
                cwd=worktree, env=self._git_env, capture_output=True, check=True,
            ).stdout

        plain = rename_patch("c.txt", "renamed.txt")
        self.assertEqual(fanout.git_numstat_paths(self.repo, plain), (True, {"renamed.txt"}))
        plain_submission = {
            "attempt": "a1",
            "token_digest": fanout.token_digest("t"),
            "patch": plain,
            "changed_paths": sorted(fanout.patch_changed_paths(plain)),
        }
        self.assertEqual(plain_submission["changed_paths"], ["c.txt", "renamed.txt"])
        self.assertEqual(
            fanout.verify_patch_submission(plain_submission, ["c.txt", "renamed.txt"], plain_submission["token_digest"], "a1"),
            [],
            "a plain rename patch must pass the numstat agreement gate",
        )
        # The load-bearing arm: a rename whose SOURCE is out of scope keeps
        # the scope violation even though the post-image sets agree.
        outside = fanout.verify_patch_submission(
            plain_submission,
            ["renamed.txt"],
            plain_submission["token_digest"],
            "a1",
        )
        self.assertEqual(outside, [fanout.REASON_SCOPE_VIOLATION])
        # Quoted rename: a non-ASCII target forces git's quoted header
        # rendering; the decoded header sides agree with the raw numstat
        # output like with like.
        e_acute = "renam\N{LATIN SMALL LETTER E WITH ACUTE}d.txt"
        quoted = rename_patch("c.txt", e_acute)
        self.assertEqual(fanout.patch_changed_paths(quoted), {"c.txt", e_acute})
        numstat_ok, derived = fanout.git_numstat_paths(self.repo, quoted)
        self.assertTrue(numstat_ok)
        self.assertEqual(derived, {e_acute})
        quoted_submission = {
            "attempt": "a1",
            "token_digest": fanout.token_digest("t"),
            "patch": quoted,
            "changed_paths": sorted(fanout.patch_changed_paths(quoted)),
        }
        self.assertEqual(
            fanout.verify_patch_submission(
                quoted_submission,
                ["c.txt", e_acute],
                quoted_submission["token_digest"],
                "a1",
                numstat_port=lambda _patch: (True, derived),
            ),
            [],
            "a quoted rename patch must pass the numstat agreement gate",
        )

    def test_rename_round_passes_the_real_numstat_witness_and_disagreement_quarantines(self):
        # r3 F12: a fanout round whose worker double returns a real -M
        # rename patch is judged by the production parent's git-backed
        # numstat witness (never the tautological default that derives the
        # expected set from the header it verifies), and a tampered patch
        # whose header post-image disagrees with git's own parse
        # quarantines terminally.
        def rename_behavior(directive):
            workspace = Path(directive["workspace"])
            (workspace / "c.txt").rename(workspace / "renamed.txt")
            self._git("add", "-A", ".", cwd=workspace)
            patch = subprocess.run(
                ["git", "diff", "--binary", "--cached", "-M"],
                cwd=workspace, env=self._git_env, capture_output=True, check=True,
            ).stdout
            self.assertIn(b"diff --git a/c.txt b/renamed.txt", patch)
            return {
                "status": "success",
                "patch": patch,
                "changed_paths": sorted(fanout.patch_changed_paths(patch)),
                "attempt": directive["attempt"],
                "token_digest": directive["token_digest"],
                "counts": {"fixed": 1, "dropped": 0, "deferred": 0, "pending": 0},
            }

        result, _ = self.run_fanout(
            {1: ["c.txt", "renamed.txt"], 2: ["b.txt"]},
            {"w1": rename_behavior, "w2": self.success_behavior({"b.txt": "w2 fix\n"})},
        )
        self.assertEqual(result["mode"], "fanout")
        self.assertEqual(result["merge_receipt"]["applied"], ["w1", "w2"])
        self.assertFalse((self.repo / "c.txt").exists())
        self.assertEqual((self.repo / "renamed.txt").read_text(encoding="utf-8"), "original c.txt\n")

        # Disagreement arm: a header whose post-image diverges from git's
        # own numstat parse is an ambiguous patch and terminates the subset
        # without retrying.
        def tampered_behavior(directive):
            workspace = Path(directive["workspace"])
            (workspace / "a.txt").write_text("tampered header fix\n", encoding="utf-8")
            patch = self._binary_patch(workspace)
            tampered = patch.replace(b"diff --git a/a.txt b/a.txt", b"diff --git a/a.txt b/ghost.txt", 1)
            self.assertNotEqual(tampered, patch)
            return {
                "status": "success",
                "patch": tampered,
                "changed_paths": sorted(fanout.patch_changed_paths(tampered)),
                "attempt": directive["attempt"],
                "token_digest": directive["token_digest"],
                "counts": {"fixed": 1, "dropped": 0, "deferred": 0, "pending": 0},
            }

        result, _ = self.run_fanout(
            {1: ["a.txt"], 2: ["blob.bin"]},
            {"w1": tampered_behavior, "w2": self.success_behavior({"blob.bin": bytes(range(64, 128))})},
            round_id="r2",
        )
        self.assertEqual(result["mode"], "fanout")
        self.assertEqual(result["merge_receipt"]["applied"], ["w2"])
        self.assertEqual(result["record"]["terminal"].get("w1"), fanout.REASON_AMBIGUOUS_PATCH)
        self.assertFalse((self.repo / "ghost.txt").exists())
        self.assertEqual((self.repo / "a.txt").read_text(encoding="utf-8"), "original a.txt\n")

    def test_mixed_quoted_rename_header_parses_and_passes_the_real_gate(self):
        # r3 F18: a rename whose OLD path needs git's C-quoting but whose
        # NEW path is pure ASCII renders the mixed-quoted header
        # `diff --git "a/caf<e-acute>.md" b/new.md`, which matched neither
        # header regex pre-fix and false-quarantined an honest rename as
        # ambiguous_patch. Each side's quoting now decodes independently and
        # the patch passes the real git numstat witness end to end.
        accented = "caf\N{LATIN SMALL LETTER E WITH ACUTE}.md"
        worktree = self.base / "mixed-ws"
        self._git("worktree", "add", "--detach", str(worktree), self._head())
        (worktree / accented).write_text("renamed content\n", encoding="utf-8")
        self._git("add", accented, cwd=worktree)
        self._git("commit", "-qm", "add accented file", cwd=worktree)
        self._git("mv", accented, "new.md", cwd=worktree)
        patch = subprocess.run(
            ["git", "diff", "--binary", "--cached", "-M"],
            cwd=worktree, env=self._git_env, capture_output=True, check=True,
        ).stdout
        header = patch.splitlines()[0]
        self.assertTrue(header.startswith(b'diff --git "a/caf'), header)
        self.assertTrue(header.endswith(b"b/new.md"), header)
        self.assertEqual(fanout.patch_changed_paths(patch), {accented, "new.md"})
        numstat_ok, derived = fanout.git_numstat_paths(self.repo, patch)
        self.assertTrue(numstat_ok)
        self.assertEqual(derived, {"new.md"})
        submission = {
            "attempt": "a1",
            "token_digest": fanout.token_digest("t"),
            "patch": patch,
            "changed_paths": sorted(fanout.patch_changed_paths(patch)),
        }
        self.assertEqual(
            fanout.verify_patch_submission(
                submission,
                [accented, "new.md"],
                submission["token_digest"],
                "a1",
                numstat_port=lambda _patch: fanout.git_numstat_paths(self.repo, patch),
            ),
            [],
            "a mixed-quoted rename must pass the real numstat agreement gate",
        )

    def test_empty_patch_claiming_fixes_is_ambiguous(self):
        # r3 F17: a drop-only submission (empty patch, empty changed-path
        # receipt) whose counts claim fixes or deferrals is an ambiguous
        # patch - zero bytes changed can never be recorded as fixing or
        # deferring findings - while the honest all-zero drop stays accepted.
        base = {
            "attempt": "a1",
            "token_digest": fanout.token_digest("t"),
            "patch": b"",
            "changed_paths": [],
        }
        claiming = dict(base, counts={"fixed": 1, "dropped": 0, "deferred": 0, "pending": 0})
        self.assertEqual(
            fanout.verify_patch_submission(claiming, ["a.txt"], claiming["token_digest"], "a1"),
            [fanout.REASON_AMBIGUOUS_PATCH],
        )
        deferring = dict(base, counts={"fixed": 0, "dropped": 0, "deferred": 2, "pending": 0})
        self.assertEqual(
            fanout.verify_patch_submission(deferring, ["a.txt"], deferring["token_digest"], "a1"),
            [fanout.REASON_AMBIGUOUS_PATCH],
        )
        honest = dict(base, counts={"fixed": 0, "dropped": 1, "deferred": 0, "pending": 0})
        self.assertEqual(
            fanout.verify_patch_submission(honest, ["a.txt"], honest["token_digest"], "a1"),
            [],
        )

    def _triage_return(self, token, workspace, patch_name, triage_lines):
        patch = (workspace / patch_name).read_bytes() if patch_name else b""
        digest_line = f"- {hashlib.sha256(patch).hexdigest()}\n\n" if patch else "\n"
        return (
            "### Status\nsuccess\n\n"
            "### Token and attempt echo\n"
            f"- Scope token: {token}\n"
            "- Attempt id: a1\n\n"
            "### Binary patch\n"
            f"- {patch_name or 'none'}\n\n"
            "### Patch digest\n"
            f"{digest_line}"
            "### Changed-path receipt\n\n"
            "### Per-finding triage\n"
            + "".join(f"- {line}\n" for line in triage_lines)
        )

    def test_triage_verdict_parse_is_positional_and_strict(self):
        # r2 F8: the verdict is parsed positionally after the finding id, so
        # a colon-bearing reason can never redirect the parse (the old
        # last-colon take turned "1: done; see docs/x.md:12 for the covered
        # call site" into a zero-count that failed count conservation
        # terminally), and an unmatched verdict is an explicit per-line
        # error instead of a silent under-count.
        token = fanout.issue_scope_token("r1", "w1", "a1", self.SECRET)
        workspace = self.tmp / "verdict-ws"
        workspace.mkdir(parents=True, exist_ok=True)
        (workspace / "fix.patch").write_bytes(b"placeholder body\n")
        parsed = fanout.parse_worker_submission(
            self._triage_return(
                token,
                workspace,
                "fix.patch",
                ["1: done; see docs/x.md:12 for the covered call site", "2: dropped; duplicate of 1"],
            ),
            workspace,
        )
        self.assertEqual(parsed["counts"], {"fixed": 1, "dropped": 1, "deferred": 0, "pending": 0})
        with self.assertRaises(ValueError):
            fanout.parse_worker_submission(
                self._triage_return(token, workspace, "fix.patch", ["1: postponed; waiting on the review"]),
                workspace,
            )

    def test_drop_only_return_bridges_to_an_accepted_empty_submission(self):
        # r2 F9: the documented drop-only return (Binary patch: none plus an
        # empty Changed-path receipt) parses into the accepted empty
        # submission and flows through the parent as an accepted drop, not a
        # retried-and-terminally-blocked bridge failure. A drop-only return
        # that carries changed paths or a done/pending triage fails the
        # bridge explicitly.
        token = fanout.issue_scope_token("r1", "w1", "a1", self.SECRET)
        digest = fanout.token_digest(token)
        workspace = self.tmp / "drop-ws"
        workspace.mkdir(parents=True, exist_ok=True)
        text = self._triage_return(
            token,
            workspace,
            None,
            ["1: dropped; no longer reproduces", "2: dropped; duplicate of 1"],
        )
        submission = fanout.parse_worker_submission(text, workspace)
        self.assertEqual(submission["patch"], b"")
        self.assertEqual(submission["changed_paths"], [])
        self.assertEqual(submission["counts"]["dropped"], 2)
        self.assertEqual(fanout.verify_patch_submission(submission, ["a.txt", "b.txt"], digest, "a1"), [])
        with self.assertRaises(ValueError):
            fanout.parse_worker_submission(
                self._triage_return(token, workspace, None, ["1: done; no patch needed"]),
                workspace,
            )
        # r4 O22: the strictness arm for the other non-drop verdict: a
        # drop-only return carrying a pending triage fails the bridge
        # exactly like a done one, so an unfinished finding can never hide
        # inside a patch-less submission.
        with self.assertRaises(ValueError):
            fanout.parse_worker_submission(
                self._triage_return(token, workspace, None, ["1: pending; still blocked upstream"]),
                workspace,
            )
        # r5 F9: the parent witness's empty-patch claiming arm refuses a
        # pending-claiming count too (the bridge can never produce that
        # shape), so an empty patch can never be recorded as leaving
        # findings pending.
        pending_claim = {
            "status": "success",
            "attempt": "a1",
            "token_digest": digest,
            "patch": b"",
            "changed_paths": [],
            "counts": {"fixed": 0, "dropped": 0, "deferred": 0, "pending": 1},
        }
        self.assertEqual(
            fanout.verify_patch_submission(pending_claim, ["a.txt"], digest, "a1"),
            [fanout.REASON_AMBIGUOUS_PATCH],
        )
        drop_counts = dict(pending_claim, counts={"fixed": 0, "dropped": 1, "deferred": 0, "pending": 0})
        self.assertEqual(fanout.verify_patch_submission(drop_counts, ["a.txt"], digest, "a1"), [])

        def drop_worker(directive):
            return fanout.parse_worker_submission(
                self._triage_return(
                    directive["token"],
                    Path(directive["workspace"]),
                    None,
                    [f"{finding}: dropped; out of scope for a code fix" for finding in directive["findings"]],
                ),
                Path(directive["workspace"]),
            )

        result, _ = self.run_fanout(
            {1: ["a.txt", "b.txt"], 2: ["a.txt", "b.txt"], 3: ["c.txt"]},
            {"w1": drop_worker, "w2": self.success_behavior({"c.txt": "w2 fix\n"})},
        )
        self.assertEqual(result["merge_receipt"]["applied"], ["w1", "w2"])
        self.assertEqual(result["record"]["workers"]["w1"]["status"], "accepted")
        self.assertEqual(result["merge_receipt"]["counts"]["dropped"], 2)
        self.assertEqual(result["merge_receipt"]["counts"]["fixed"], 1)

    def test_fanout_cli_operations_are_invocable(self):
        # r2 F9: the pure parent operations are a documented shell surface
        # (plan, issue-token, verify-submission); the fan-out contract is
        # exercisable by the documented operator.
        completed = subprocess.run(
            [sys.executable, str(SCRIPTS / "execute_plan_address_fanout.py"),
             "--operation", "plan",
             "--input", json.dumps({"finding_files": {"1": ["a.txt"], "2": ["b.txt"]}})],
            capture_output=True, text=True, check=True,
        )
        plan = json.loads(completed.stdout)["plan"]
        self.assertEqual(plan["mode"], "fanout")
        self.assertEqual(len(plan["workers"]), 2)
        completed = subprocess.run(
            [sys.executable, str(SCRIPTS / "execute_plan_address_fanout.py"),
             "--operation", "issue-token",
             "--input", json.dumps({"round": "r9", "worker": "w1", "attempt": "a1", "secret": "s"})],
            capture_output=True, text=True, check=True,
        )
        issued = json.loads(completed.stdout)
        self.assertEqual(issued["token_digest"], fanout.token_digest(issued["token"]))
        patch = self._binary_patch(self._worktree_copy())
        submission_path = self.tmp / "cli-submission.json"
        submission_path.write_text(json.dumps({
            "attempt": "a1",
            "token_digest": issued["token_digest"],
            "patch": base64.b64encode(patch).decode("ascii"),
            "changed_paths": sorted(fanout.patch_changed_paths(patch)),
        }), encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(SCRIPTS / "execute_plan_address_fanout.py"),
             "--operation", "verify-submission",
             "--repo-root", str(self.repo),
             "--input", json.dumps({
                 "submission_path": str(submission_path),
                 "worker_files": sorted(fanout.patch_changed_paths(patch)),
                 "expected_token_digest": issued["token_digest"],
                 "expected_attempt": "a1",
             })],
            capture_output=True, text=True, check=True,
        )
        self.assertEqual(json.loads(completed.stdout), {"operation": "verify-submission", "violations": [], "accepted": True})

    def test_fanout_composes_with_runtime_driver_and_validates_sidecar(self) -> None:
        """r1 F2 + F4: the production composition. state_recorder is the
        runtime driver's record_address_fanout (the only producible
        production wiring); the run's generations and terminal map advance
        in machine state, the finalize renders the three-key sidecar, and
        the --hard validator accepts the projection round trip."""

        state_path = self.tmp / "runtime_state.json"
        runtime.create_manifest(state_path, "fixture-plan", [{"id": "task-1", "number": 1, "status": "pending"}])
        driver = runtime.RuntimeDriver(
            state_path,
            plan_slug="fixture-plan",
            repo_root=self.repo,
            commit_lookup=lambda _commit: True,
        )
        finding_files = {1: ["a.txt"], 2: ["c.txt"]}
        result, _ = self.run_fanout(
            finding_files,
            {
                "w1": self.success_behavior({"a.txt": "w1 composed fix\n"}),
                "w2": self.success_behavior({"c.txt": "w2 composed fix\n"}),
            },
            state_recorder=driver.record_address_fanout,
            round_id="r-compose",
        )
        self.assertEqual(result["mode"], "fanout")
        # F2: the seam keeps the live record current (generation 1, no
        # stale-generation refusals, accepted results in machine state).
        self.assertIsNotNone(result["record"])
        persisted = runtime.load_manifest(state_path)["address_fanout"]
        self.assertEqual(persisted["generation"], 1)
        self.assertEqual(persisted["workers"]["w1"]["status"], "accepted")
        self.assertEqual(persisted["workers"]["w2"]["status"], "accepted")
        self.assertEqual(persisted["terminal"], {})
        self.assertEqual(result["merge_receipt"]["blocked_subsets"], {})
        self.assertEqual(result["merge_receipt"]["counts"], {"fixed": 2, "dropped": 0, "deferred": 0, "pending": 0})

        # F4: finalize renders the sidecar projection from the machine
        # record; the projection carries exactly the three spec keys, and a
        # mid-flight attempt (no terminal event) projects no row.
        inflight = dict(persisted)
        inflight = fanout.copy.deepcopy(inflight)
        inflight["workers"]["w1"]["attempts"][0]["event"] = "launched"
        inflight["workers"]["w1"]["attempts"][0]["reason_code"] = None
        projection = fanout.render_sidecar_projection(inflight)
        self.assertEqual(projection["workers"][0]["attempts"], [])
        projection = fanout.render_sidecar_projection(persisted)
        self.assertEqual(set(projection), {"round", "finding_files", "workers"})
        self.assertEqual(projection["round"], "r-compose")
        for worker in projection["workers"]:
            for attempt in worker["attempts"]:
                self.assertIn(attempt["status"], vrs.ADDRESS_FANOUT_ATTEMPT_STATUSES)
                self.assertIn(attempt["reason_code"], vrs.ADDRESS_FANOUT_REASON_CODES)

        manifest_projection = self.tmp / "manifest-fanout.md"
        sidecar_path = self.tmp / "stats.json"
        sidecar_path.write_text(json.dumps({"schema_version": 1, "round": "r-compose"}), encoding="utf-8")
        finalized = driver.finalize_address_fanout("r-compose", 1, manifest_projection, sidecar_path)
        self.assertEqual(finalized["status"], "success", finalized)
        self.assertTrue(finalized["commit_authorized"])
        rendered = json.loads(sidecar_path.read_text(encoding="utf-8"))["extensions"]["address_fanout"]
        self.assertEqual(set(rendered), {"round", "finding_files", "workers"})

        # The render-finalize-validate round trip: the same --hard gate the
        # round commit must pass accepts the projection.
        payload = {
            "schema_version": 1,
            "round": "r-compose",
            "findings": [{"id": 1}, {"id": 2}],
            "extensions": {"address_fanout": rendered},
        }
        validation = vrs.ValidationResult(path=sidecar_path)
        vrs.validate_address_fanout_contract(payload, validation, schema_class="current-v1")
        self.assertEqual(validation.errors, [])


if __name__ == "__main__":
    unittest.main()
