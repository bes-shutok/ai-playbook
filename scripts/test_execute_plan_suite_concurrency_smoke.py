#!/usr/bin/env python3
"""Concurrency smoke for the execute-plan runtime test suite.

Repeatable probe for the 2026-09-18 observation that 4 of 8 concurrent
suite runs returned success-instead-of-blocked from the archive-gate
refusal subtests (open-claims and commit-pending), a mechanism never
reproduced serially in about 25 runs. The focused target is the refusal
subset class ``ArchiveGatePreArchiveTest`` of ``test_execute_plan_runtime``.

Isolation design: every instance is spawned with its ``TMPDIR`` environment
bound to its own distinct mktemp root inside the class-level harness root
(Python's ``tempfile`` reads ``TMPDIR``, not the working directory, so the
binding is what isolates tempfile use between instances). A
``runtime_state.json`` that escaped its instance root would therefore prove
cross-instance contamination; with the uuid-suffixed per-test fixture
placement landed on main, none is expected anywhere.

The parallel pair-run leg (two concurrent full-suite instances on the
shared ambient temp directory) is exercised separately by the plan's
Validation Commands block; this harness keeps the controlled-concurrency
window bounded and repeatable.

Run: ``( cd scripts && python3 -m unittest test_execute_plan_suite_concurrency_smoke )``
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent

# The focused archive-gate refusal subset (module and class names verified
# against scripts/test_execute_plan_runtime.py).
FOCUSED_TARGET = "test_execute_plan_runtime.ArchiveGatePreArchiveTest"

# Three rounds of a concurrent pair plus one burst round of eight instances,
# matching the 2026-09-18 observation window (8 concurrent suite runs).
PAIR_ROUNDS = 3
PAIR_INSTANCES = 2
BURST_INSTANCES = 8

# Per-instance subprocess timeout; the focused subset runs in seconds
# serially, so this only bounds a wedged instance.
INSTANCE_TIMEOUT_SECONDS = 600

# The leftovers assertion must observe the harness root BEFORE it is
# removed; unittest orders methods alphabetically, so the rounds test runs
# first and this method last.
FINAL_TEST_METHOD = "test_no_shared_fixture_leftovers_after_smoke"


class SuiteConcurrencySmokeTest(unittest.TestCase):
    """Every concurrent focused-subset instance exits clean and isolated.

    The harness temp root is class-level and created with ``mkdtemp``;
    per-instance roots live inside it and each instance's ``TMPDIR`` points
    at its own root. The root is removed in ``tearDown`` after the leftovers
    assertion has run, and a class cleanup removes it even when a failure
    aborts a test before ``tearDown`` gets there.
    """

    harness_root: Path = Path()
    instance_roots: list[Path] = []

    @classmethod
    def setUpClass(cls) -> None:
        cls.harness_root = Path(tempfile.mkdtemp(prefix="execute-plan-suite-smoke-"))
        cls.instance_roots = []
        # Failure safety net: removes the harness root even when a failure
        # aborts a test before tearDown runs (idempotent with tearDown).
        cls.addClassCleanup(shutil.rmtree, cls.harness_root, ignore_errors=True)

    def tearDown(self) -> None:
        # Remove the harness root only once the leftovers assertion has read
        # it; the class cleanup registered above still removes it after any
        # earlier abort.
        if self._testMethodName == FINAL_TEST_METHOD:
            shutil.rmtree(self.harness_root, ignore_errors=True)

    def _spawn_instance(self) -> subprocess.CompletedProcess:
        """Spawn one focused-subset instance bound to its own temp root."""
        instance_root = Path(
            tempfile.mkdtemp(prefix="instance-", dir=self.harness_root)
        )
        self.instance_roots.append(instance_root)
        env = dict(os.environ)
        env["TMPDIR"] = str(instance_root)
        return subprocess.run(
            [sys.executable, "-m", "unittest", FOCUSED_TARGET],
            cwd=str(SCRIPTS_DIR),
            env=env,
            capture_output=True,
            text=True,
            timeout=INSTANCE_TIMEOUT_SECONDS,
        )

    def _run_round(self, instance_count: int, round_label: str) -> None:
        """Run one round of ``instance_count`` concurrent instances."""
        with ThreadPoolExecutor(max_workers=instance_count) as pool:
            futures = [
                pool.submit(self._spawn_instance) for _ in range(instance_count)
            ]
            results = [future.result() for future in futures]
        problems = []
        for index, completed in enumerate(results, start=1):
            combined = (completed.stdout or "") + (completed.stderr or "")
            if completed.returncode != 0 or "FAILED" in combined or "ERROR" in combined:
                tail = "\n".join(combined.strip().splitlines()[-10:])
                problems.append(
                    f"{round_label} instance {index}/{instance_count}: "
                    f"exit={completed.returncode}\n{tail}"
                )
        self.assertEqual(
            problems,
            [],
            msg=f"concurrent focused-subset round not clean: {round_label}",
        )

    def test_focused_refusal_subset_survives_concurrent_pair_runs(self):
        """Three pair rounds plus one eight-instance burst, all clean."""
        for round_index in range(1, PAIR_ROUNDS + 1):
            self._run_round(
                PAIR_INSTANCES, f"pair-round-{round_index}"
            )
        self._run_round(BURST_INSTANCES, f"burst-{BURST_INSTANCES}-instances")

    def test_no_shared_fixture_leftovers_after_smoke(self):
        """Zero runtime_state.json files outside the per-instance roots.

        This discriminates cross-instance contamination only because each
        instance's ``TMPDIR`` is bound to its own root: a shared-temp
        ``runtime_state.json`` write would land outside every instance root.
        """
        expected_instances = PAIR_ROUNDS * PAIR_INSTANCES + BURST_INSTANCES
        self.assertEqual(
            len(self.instance_roots),
            expected_instances,
            msg="smoke rounds did not spawn the prescribed instance count",
        )
        leftovers = [
            path
            for path in sorted(self.harness_root.rglob("runtime_state.json"))
            if not any(path.is_relative_to(root) for root in self.instance_roots)
        ]
        self.assertEqual(
            leftovers,
            [],
            msg="runtime_state.json leftovers escaped the per-instance roots",
        )


if __name__ == "__main__":
    unittest.main()
