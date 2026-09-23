#!/usr/bin/env python3
"""Parallel-work regression probes for shared-checkout reliability.

Plan: docs/plans/2026-09-23-ai-harness-friction-audit.md, Task 4. Every test
is a probe of one unrelated-peer false-block family against the real gate
code, with the intentional data-loss protections pinned in the same run:

- a task-owned ignored deliverable survives the done sweep while unrelated
  peer artifacts are not claimed by the session-scoped gates;
- a peer's unrelated staged whole-file deletion (an ordinary dirt shape the
  recipe's file enumeration picks up) is classified by the dirt regression
  gate instead of aborting the run as a git-environment error;
- the dirt gate's regression detection and its fail-closed posture for
  never-tracked paths survive the narrowing unchanged.

Hermeticity contract: every fixture lives under tempfile.TemporaryDirectory
with explicit teardown, git config is neutralized per fixture, no network,
and the done-gate runtime home and user facts are redirected into the
fixture the same way scripts/test_done_sweep_gates_lib.py does it.

The suite runs under both runners the plan's validation commands use:
``python3 -m unittest scripts.test_parallel_work_regressions`` and
``python3 -m pytest scripts/test_parallel_work_regressions.py``.
"""

from __future__ import annotations

import os
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

import done_sweep_gates_lib as lib

DIRT_GATE_PATH = SCRIPTS_DIR / "dirt_regression_gate.py"


def _git_env() -> dict[str, str]:
    env = dict(os.environ)
    env["GIT_CONFIG_GLOBAL"] = "/dev/null"
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    return env


def _marker_name(epoch: float) -> str:
    return "run-start-" + datetime.fromtimestamp(epoch, tz=timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )


class ParallelWorkRegressionTest(unittest.TestCase):
    """Probes over hermetic fixture repos; one false-block family per test."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        # Resolve: on macOS the temp root is a /var symlink of /private/var,
        # and GateContext.discover resolves the repo root, so every path
        # comparison below must use the resolved spelling.
        self.root = (Path(self._tmp.name) / "repo").resolve()
        self.root.mkdir()
        self._git("init", "-q", "-b", "main")
        self._git("config", "user.email", "fixture@example.invalid")
        self._git("config", "user.name", "fixture")
        # /docs/ ignored: the shared-checkout reality the done sweep gates
        # operate on (reviews, tmp, and run state live outside the index).
        (self.root / ".gitignore").write_text("__pycache__/\n/docs/\n", encoding="utf-8")
        (self.root / "README.md").write_text("fixture repo\n", encoding="utf-8")
        self._git("add", ".gitignore", "README.md")
        self._git("commit", "-q", "-m", "init")
        facts_dir = self.root / ".ai-playbook"
        facts_dir.mkdir()
        (facts_dir / "facts.md").write_text(
            "```toml\n"
            'plans_dir = "docs/plans/"\n'
            'plans_completed_dir = "docs/plans/completed/"\n'
            'backlog_dir = "docs/history/backlog/"\n'
            'reviews_dir = "docs/reviews/"\n'
            'tmp_dir = "docs/tmp/"\n'
            "```\n",
            encoding="utf-8",
        )
        # Redirect the runtime home and user facts into the fixture, and pin
        # the ambient resolver inputs, like the done-gate suite does.
        runtime_home = Path(self._tmp.name) / "runtime-home"
        runtime_home.mkdir()
        (runtime_home / "facts.md").write_text("# fixture user facts\n", encoding="utf-8")
        self._saved_env = {
            key: os.environ.get(key)
            for key in (
                "DONE_SWEEP_RUNTIME_HOME",
                "DONE_SWEEP_USER_FACTS",
                "REVIEW_STAGING_VALIDATOR",
                "DOC_REGISTRY_VALIDATOR_SCRIPT",
                "DONE_SWEEP_REPO_ROOT",
            )
        }
        os.environ["DONE_SWEEP_RUNTIME_HOME"] = str(runtime_home)
        os.environ["DONE_SWEEP_USER_FACTS"] = str(runtime_home / "facts.md")
        for key in (
            "REVIEW_STAGING_VALIDATOR",
            "DOC_REGISTRY_VALIDATOR_SCRIPT",
            "DONE_SWEEP_REPO_ROOT",
        ):
            os.environ.pop(key, None)
        self.addCleanup(self._restore_env)
        # Two content-confirmed markers anchor the session window: the
        # previous-run marker one hour ago, the current-run marker now.
        now = time.time()
        self._make_marker(now - 3600)
        self._make_marker(now)

    def _restore_env(self) -> None:
        for key, value in self._saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    # ------------------------------------------------------------------
    # Fixture helpers
    # ------------------------------------------------------------------

    def _git(self, *args: str) -> str:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(self.root),
            capture_output=True,
            text=True,
            env=_git_env(),
            check=False,
        )
        self.assertEqual(
            proc.returncode, 0, f"git {args} failed: {proc.stderr}"
        )
        return proc.stdout

    def _make_marker(self, epoch: float) -> Path:
        done_session = self.root / "docs" / "tmp" / "done-session"
        done_session.mkdir(parents=True, exist_ok=True)
        marker = done_session / _marker_name(epoch)
        marker.write_text(f"{int(epoch)} {self.root} {os.getpid()}\n", encoding="utf-8")
        return marker

    def _write(self, rel: str, text: str) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def _stub_staging_validator(self) -> Path:
        """Exit-0 validator stub recording every invoked staging path."""
        stub = self.root / "scripts" / "stub_review_staging_validator.py"
        stub.parent.mkdir(parents=True, exist_ok=True)
        stub.write_text(
            "#!/usr/bin/env python3\n"
            "import sys\n"
            "log = __file__ + '.invocations'\n"
            "with open(log, 'a', encoding='utf-8') as fh:\n"
            "    fh.write('\\n'.join(sys.argv[1:]) + '\\n')\n"
            "sys.exit(0)\n",
            encoding="utf-8",
        )
        os.environ["REVIEW_STAGING_VALIDATOR"] = str(stub)
        return stub

    def _run_dirt_gate(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(DIRT_GATE_PATH), *args],
            cwd=str(self.root),
            capture_output=True,
            text=True,
            env=_git_env(),
            check=False,
        )

    # ------------------------------------------------------------------
    # Task 4 required probe: task-owned ignored deliverable preserved
    # ------------------------------------------------------------------

    def test_task_owned_ignored_deliverable_is_preserved(self):
        """Given a task-owned ignored deliverable plus unrelated peer
        artifacts, the deliverable survives and the peer artifacts are not
        claimed: the review-staging gate validates only the task's own
        in-window staging doc, the docs-tmp sweep removes nothing, and every
        file stays byte-identical on disk."""
        # Task-owned ignored deliverables, written inside the session window.
        own_review = self._write(
            "docs/reviews/2026-09-23-branch-review-r1.md",
            "# Review\n\ntask-owned staging record\n",
        )
        own_log = self._write(
            "docs/tmp/implement-task4.log.md",
            "# implement task4 log\n\nprobes and outputs\n",
        )
        # Unrelated peer artifacts: an old staging-shaped doc outside the
        # window, and in-window scratch files that are not staging-shaped.
        peer_old_review = self._write(
            "docs/reviews/2026-09-20-branch-review-r1.md",
            "# Peer review\n\npeer-owned record from an earlier session\n",
        )
        old_t = time.time() - 86400
        os.utime(peer_old_review, (old_t, old_t))
        peer_scratch_review = self._write(
            "docs/reviews/peer-scratch-notes.md",
            "peer scratch next to the review records\n",
        )
        peer_scratch_tmp = self._write(
            "docs/tmp/peer-scratch.md",
            "peer scratch under docs/tmp\n",
        )
        before = {
            path: path.read_bytes()
            for path in (
                own_review,
                own_log,
                peer_old_review,
                peer_scratch_review,
                peer_scratch_tmp,
            )
        }
        stub = self._stub_staging_validator()
        ctx = lib.GateContext.discover(self.root)

        # The claim surface names exactly the task's own staging doc.
        candidates = lib.derive_review_staging_candidates(ctx)
        self.assertEqual([str(path) for path in candidates], [str(own_review)])

        # The gate claims and validates only that candidate; the peer's
        # out-of-window staging doc and non-staging scratch are never
        # validated as this run's own.
        result = lib.run_gate("review-staging", ctx)
        self.assertEqual(result.rc, 0, result.message)
        self.assertIn("1 session-touched", result.message)
        invocations = Path(str(stub) + ".invocations").read_text(encoding="utf-8")
        self.assertIn(str(own_review), invocations)
        self.assertNotIn(str(peer_old_review), invocations)
        self.assertNotIn(str(peer_scratch_review), invocations)

        # The sweep removes nothing: the task's log deliverable survives
        # (never synced; removal would be permanent) and the peer scratch is
        # kept as unclear-ownership work.
        sweep = lib.run_gate("docs-tmp-sweep", ctx)
        self.assertEqual(sweep.rc, 0, sweep.message)
        self.assertIn("removed=0", sweep.message)
        for path, payload in before.items():
            self.assertTrue(path.is_file(), f"missing after sweep: {path}")
            self.assertEqual(path.read_bytes(), payload, f"mutated: {path}")

    # ------------------------------------------------------------------
    # Reproduced false block: dirt gate staged-deletion edge (backlog
    # origin docs/history/backlog/2026-09-22-dirt-gate-staged-deletion-edge.md)
    # ------------------------------------------------------------------

    def _seed_dirt_fixture(self) -> str:
        """base commit (app.txt plus a base-era peer file), then a HEAD
        commit that gains lines in app.txt and adds a post-base peer file;
        returns the base sha."""
        self._write("app.txt", "alpha\nbeta\ngamma\n")
        self._write("peer-note.txt", "peer notes, present since base\n")
        self._git("add", "app.txt", "peer-note.txt")
        self._git("commit", "-q", "-m", "base")
        base_sha = self._git("rev-parse", "HEAD").strip()
        self._write("app.txt", "alpha\nbeta-head-v2\ngamma\ndelta-head\n")
        self._write("peer-later.txt", "peer content HEAD gained\n")
        self._git("add", "app.txt", "peer-later.txt")
        self._git("commit", "-q", "-m", "head gains lines")
        return base_sha

    def test_staged_deletion_of_unrelated_peer_file_does_not_block_gate(self):
        """Given the pre-commit recipe's file enumeration with a peer's
        unrelated staged whole-file deletion in it, the gate classifies the
        deletion instead of aborting with a git-environment error: the
        deletion of base-era content passes, our own forward dirt passes,
        and the run is not blocked by the peer artifact."""
        base_sha = self._seed_dirt_fixture()
        # The peer stages a whole-file deletion of their own unrelated file
        # (git rm: worktree gone, index gone, HEAD still tracks it).
        self._git("rm", "-q", "peer-note.txt")
        # Our own task dirt is a forward edit of our file.
        self._write("app.txt", "alpha\nbeta-head-v2\ngamma\ndelta-head\nepsilon-forward\n")
        enumerated = [
            line
            for line in self._git("diff", "HEAD", "--name-only").splitlines()
            if line.strip()
        ]
        self.assertEqual(sorted(enumerated), ["app.txt", "peer-note.txt"])
        proc = self._run_dirt_gate("--base", base_sha, *enumerated)
        self.assertEqual(
            proc.returncode, 0,
            f"stderr: {proc.stderr}; stdout: {proc.stdout}",
        )
        self.assertIn("PASS", proc.stdout)
        self.assertNotIn("does not exist or is not a tracked file", proc.stderr)
        # The direct single-path form classifies the same way.
        proc = self._run_dirt_gate("--base", base_sha, "peer-note.txt")
        self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
        self.assertIn("PASS", proc.stdout)

    def test_staged_whole_file_deletion_still_classifies(self):
        """The narrowing only removes the misclassification: a staged
        whole-file deletion that removes lines HEAD gained since the base is
        still named a dirt REGRESSION (whoever owns the file), and a
        never-tracked ghost path still fails closed with exit 2."""
        base_sha = self._seed_dirt_fixture()
        # A staged deletion of the task file itself is the regressive shape.
        self._git("rm", "-q", "app.txt")
        proc = self._run_dirt_gate("--base", base_sha, "app.txt")
        self.assertEqual(proc.returncode, 1, f"stderr: {proc.stderr}")
        self.assertIn("dirt REGRESSION", proc.stdout)
        self.assertIn("app.txt", proc.stdout)
        # A post-base peer file's content is HEAD-gained by definition, so
        # its staged deletion is named a regression too - classified, never
        # the rc 2 git-environment error this family used to produce.
        self._git("rm", "-q", "peer-later.txt")
        proc = self._run_dirt_gate("--base", base_sha, "peer-later.txt")
        self.assertEqual(proc.returncode, 1, f"stderr: {proc.stderr}")
        self.assertIn("dirt REGRESSION: peer-later.txt", proc.stdout)
        # Fail-closed preserved for a path that never existed in HEAD.
        proc = self._run_dirt_gate("--base", base_sha, "ghost.txt")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("does not exist or is not a tracked file", proc.stderr)


if __name__ == "__main__":
    unittest.main()
