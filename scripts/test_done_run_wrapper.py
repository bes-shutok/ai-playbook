"""Hermetic wrapper suite for scripts/done_run.sh (setup + commit + finalize).

Every test pins the lock homes, sweep context, and helper resolution into a
fixture tmp tree so no test reads or writes the host lock home, runtime home,
personal facts, or host-resolved gate validators. The commit-subcommand tests
pin every ``resolve_script`` override in ``done_sweep_gates_lib.py`` (except
``DONE_LOCK_SCRIPT``, pinned separately to the repo-local copy) at the repo
copy, plus the sync's ``DOCS_SYNC_NOW`` / ``DOCS_SYNC_TRACE_FILE`` and a
fixture public-hygiene patterns file, so the in-script landing sweep and
docs-branch sync run hermetically against the fixture repo.
"""
from __future__ import annotations

import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNNER = REPO_ROOT / "scripts" / "done_run.sh"
LOCK_SCRIPT = REPO_ROOT / "scripts" / "done-lock.sh"
CLOSEOUT_MIGRATE = REPO_ROOT / "scripts" / "worktree_closeout_migrate.py"
# The test venv resolves at runtime: the documented invocation prepends it to
# PATH, and under that interpreter's pytest its own bin directory is the venv.
VENV_BIN = os.environ.get("AI_PLAYBOOK_TEST_VENV") or str(Path(sys.executable).parent)

# Every resolve_script env override in done_sweep_gates_lib.py except
# DONE_LOCK_SCRIPT (pinned separately to the repo-local copy).
SWEEP_VALIDATOR_OVERRIDES = {
    "PLAN_READINESS_VALIDATOR": "plan_readiness.py",
    "CONFLUENCE_MIRROR_HYGIENE_SCRIPT": "confluence-mirror-hygiene.sh",
    "DOC_REGISTRY_VALIDATOR_SCRIPT": "doc_registry_validator.py",
    "REVIEW_STAGING_VALIDATOR": "validate_review_staging.py",
    "PUBLIC_HYGIENE_SCAN_SCRIPT": "scan-public-hygiene.sh",
    "INSTRUCTION_SIZE_CHECK_SCRIPT": "check-instruction-size.sh",
    "DESCRIPTION_LENGTH_CHECK_SCRIPT": "check_skill_description_length.py",
    "REVERSE_SQUASH_GUARD_SCRIPT": "reverse_squash_guard.py",
    "CHECK_PLAN_ORIGINS_CLOSED_SCRIPT": "check_plan_origins_closed.py",
    "CHECK_NO_EM_DASH_SCRIPT": "check-no-em-dash.sh",
}

CORPUS_REL = "docs/maintenance/development_lessons.md"


class FixtureMixin:
    """Shared hermetic fixture: repo, env pins, runner invocation helpers."""

    # Host Git selectors cleared before every fixture Git call (fixture
    # setup, helper calls, runner subprocesses): a session-bound selector
    # must never redirect a fixture call away from the temporary repo. The
    # object/alternate/ceiling/namespace/shallow routing variables are
    # cleared for the same reason (plan
    # docs/history/plans/2026-10-25-primary-log-branch-drift-at-commit.md
    # Task 1): a host object store, alternate, ceiling, namespace, or
    # shallow marker must never reroute a fixture Git call or a runner
    # subprocess.
    HOST_GIT_SELECTORS = (
        "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
        "GIT_CONFIG_PARAMETERS", "GIT_EXTERNAL_DIFF", "GIT_CONFIG_COUNT",
        "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CEILING_DIRECTORIES", "GIT_NAMESPACE", "GIT_SHALLOW_FILE",
    )

    def setUp(self) -> None:
        self.tmp = Path(__import__("tempfile").mkdtemp(prefix="done-run-fixture-"))
        self._clear_ambient_git_environment()
        self.fixture = self.tmp / "repo"
        self.fixture.mkdir()
        env = dict(os.environ)
        for var in (
            "DONE_LOCK_DIR", "DONE_LOCK_TOKEN", "DONE_LOCK_HOLDER_PID",
            "DONE_LOCK_POLL_SECS", "DONE_LOCK_STALE_SECS",
            "DONE_LOCK_INCOMPLETE_SECS", "DONE_LOCK_DEAD_HOLDER_GRACE_SECS",
            "DONE_LOCK_AGENT_MAX_WAIT_SECS", "DONE_LOCK_HOLD_PIN",
            "MERGE_LOCK_DIR", "MERGE_LOCK_TOKEN", "MERGE_LOCK_HOLDER_PID",
            "MERGE_LOCK_POLL_SECS", "MERGE_LOCK_STALE_SECS",
            "MERGE_LOCK_INCOMPLETE_SECS", "MERGE_LOCK_DEAD_HOLDER_GRACE_SECS",
            "DOCS_SYNC_NOW", "DOCS_SYNC_TRACE_FILE", "DOCS_SYNC_MERGE_MAX_WAIT",
            "PLAN_READINESS_VALIDATOR", "BACKLOG_LOCATION_GATE",
            "CHECK_NO_EM_DASH_SCRIPT", "CONFLUENCE_MIRROR_HYGIENE_SCRIPT",
            "DOC_REGISTRY_VALIDATOR_SCRIPT", "REVIEW_STAGING_VALIDATOR",
            "PUBLIC_HYGIENE_SCAN_SCRIPT", "PUBLIC_HYGIENE_PATTERNS_FILE",
            "PUBLIC_HYGIENE_REPO_ROOT",
            "INSTRUCTION_SIZE_CHECK_SCRIPT",
            "DESCRIPTION_LENGTH_CHECK_SCRIPT", "REVERSE_SQUASH_GUARD_SCRIPT",
            "CHECK_PLAN_ORIGINS_CLOSED_SCRIPT",
            "DONE_RUN_TRACE_FILE", "DONE_RUN_LINTER",
            "DONE_RUN_ID", "DONE_RUN_MANIFEST", "DONE_RUN_MARKER",
            "DONE_SWEEP_DECLARED_STAGE_PATHS",
            "GATE_LIVENESS_LEDGER_PATH",
            # cmd_setup's writer-claim arrays: inherited values must never
            # satisfy the runner's own mixed-input probe or inject operands
            # into the writer call (env scrub parity with the runner's
            # function-local declarations).
            "WM_ARGS", "ADOPT_ARGS",
        ):
            env.pop(var, None)
        self.base_env = env

    def _clear_ambient_git_environment(self) -> None:
        """Scrub host Git selectors from the process environment and scope
        Git config to a fixture file (system config disabled, global config
        pointed at an empty fixture file), restoring everything at cleanup;
        helper Git calls and every runner subprocess inherit the cleared
        environment."""
        names = list(self.HOST_GIT_SELECTORS) + [
            f"GIT_CONFIG_KEY_{i}" for i in range(10)
        ] + [f"GIT_CONFIG_VALUE_{i}" for i in range(10)] + [
            "GIT_CONFIG_NOSYSTEM", "GIT_CONFIG_GLOBAL",
        ]
        prior_values = {name: os.environ.get(name) for name in names}
        self.addCleanup(self._restore_ambient_git_environment, prior_values)
        for name in names:
            os.environ.pop(name, None)
        os.environ["GIT_CONFIG_NOSYSTEM"] = "1"
        gitconfig = self.tmp / "gitconfig"
        gitconfig.write_text("")
        os.environ["GIT_CONFIG_GLOBAL"] = str(gitconfig)

    @staticmethod
    def _restore_ambient_git_environment(
        prior_values: dict[str, str | None],
    ) -> None:
        for name, value in prior_values.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    def tearDown(self) -> None:
        subprocess.run(["chmod", "-R", "u+w", str(self.tmp)], check=False)
        subprocess.run(["rm", "-rf", str(self.tmp)], check=False)

    def init_fixture_repo(self, branch: str | None = None) -> Path:
        subprocess.run(["git", "init", "-q", str(self.fixture)], check=True)
        git = self.git
        git("config", "user.email", "t@example.test")
        git("config", "user.name", "t")
        (self.fixture / "seed.txt").write_text("seed\n")
        (self.fixture / ".gitignore").write_text("docs/tmp/\n__pycache__/\n")
        (self.fixture / ".ai-playbook").mkdir()
        tmp_dir = self.fixture / "docs" / "tmp"
        tmp_dir.mkdir(parents=True)
        (self.fixture / ".ai-playbook" / "facts.md").write_text(
            '```toml\n'
            'plans_dir = "docs/history/plans/"\n'
            'backlog_dir = "docs/history/backlog/"\n'
            'reviews_dir = ".ai-playbook/reviews/"\n'
            'tmp_dir = "docs/tmp/"\n'
            'metrics_dir = "docs/tmp/metrics/"\n'
            'review_certs_dir = ".ai-playbook/review-certs/"\n'
            "```\n"
        )
        git("add", ".")
        git("commit", "-qm", "seed")
        if branch:
            git("checkout", "-qb", branch)
        return self.fixture

    def git(self, *args: str, repo: Path | None = None, check: bool = True):
        proc = subprocess.run(
            ["git", "-C", str(repo or self.fixture), *args],
            capture_output=True, text=True, timeout=60,
        )
        if check and proc.returncode != 0:
            raise AssertionError(f"git {args} failed: {proc.stderr}")
        return proc

    def runner_env(self) -> dict:
        env = dict(self.base_env)
        env["PATH"] = VENV_BIN + os.pathsep + env.get("PATH", "")
        env["HOME"] = str(self.tmp / "home")
        env["XDG_CONFIG_HOME"] = str(self.tmp / "home")
        Path(env["HOME"]).mkdir(exist_ok=True)
        env["DONE_LOCK_ROOT"] = str(self.tmp / "locks" / "done")
        env["MERGE_LOCK_ROOT"] = str(self.tmp / "locks" / "merge")
        env["MERGE_LOCK_POLL_SECS"] = "1"
        env["DONE_LOCK_POLL_SECS"] = "1"
        env["DONE_LOCK_AGENT_MAX_WAIT_SECS"] = "1"
        env["DONE_LOCK_DEAD_HOLDER_GRACE_SECS"] = "0"
        env["DONE_LOCK_SCRIPT"] = str(LOCK_SCRIPT)
        env["DONE_SWEEP_REPO_ROOT"] = str(self.fixture)
        env["DONE_SWEEP_RUNTIME_HOME"] = str(self.tmp / "runtime-home")
        env["DONE_SWEEP_USER_FACTS"] = str(self.tmp / "user-facts.md")
        return env

    def run_setup(
        self, *args: str, cwd: Path | None = None,
        env: dict | None = None, env_extra: dict | None = None,
    ) -> subprocess.CompletedProcess:
        resolved = env if env is not None else self.runner_env()
        if env_extra:
            resolved = dict(resolved)
            resolved.update(env_extra)
        return subprocess.run(
            ["bash", str(RUNNER), "setup", *args],
            cwd=str(cwd or self.fixture),
            env=resolved,

            capture_output=True,
            text=True,
            timeout=300,
        )

    def done_session(self) -> Path:
        return self.fixture / "docs" / "tmp" / "done-session"

    # ---- run-manifest fixture helpers ----------------------------------- #
    # The one shared implementation of the three run-manifest fixture
    # helpers, consumed by the setup-state, adoption, and
    # authorized-restoration test classes (no class keeps its own copy).

    def rewrite_manifest(self, manifest: Path | dict, **changes: object) -> None:
        """Rewrite one run manifest record in place with the given field
        changes; accepts the manifest path or the setup exports dict carrying
        DONE_RUN_MANIFEST (both prior class-local copies serialized
        identically, so one shared implementation serves both callers)."""
        if isinstance(manifest, dict):
            manifest = Path(manifest["DONE_RUN_MANIFEST"])
        record = json.loads(manifest.read_text())
        record.update(changes)
        manifest.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")

    def craft_manifest_file(
        self, template: Path, run_id: str, **changes: object
    ) -> Path:
        record = json.loads(template.read_text())
        record["run_id"] = run_id
        record.update(changes)
        path = self.done_session() / f"run-manifest-{run_id}.json"
        path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        return path

    def session_names(self) -> list[str]:
        return sorted(p.name for p in self.done_session().iterdir())

    # ---- commit-subcommand helpers -------------------------------------- #

    def commit_env(self) -> dict:
        """Runner env plus the sweep validator pins, the sync pins, a fixture
        hygiene patterns file, and the run-trace file, so the commit
        subcommand's landing sweep and docs-branch sync run hermetically."""
        env = self.runner_env()
        for var, name in SWEEP_VALIDATOR_OVERRIDES.items():
            env[var] = str(REPO_ROOT / "scripts" / name)
        env["PUBLIC_HYGIENE_PATTERNS_FILE"] = str(self.tmp / "patterns.txt")
        (self.tmp / "patterns.txt").write_text("# fixture deny patterns\n")
        env["DOCS_SYNC_NOW"] = "2026-10-11T12:00:00Z"
        env["DOCS_SYNC_TRACE_FILE"] = str(self.tmp / "sync-trace.txt")
        env["DONE_RUN_TRACE_FILE"] = str(self.tmp / "run-trace.txt")
        return env

    def run_commit(self, *args: str, env: dict | None = None,
                   cwd: Path | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(RUNNER), "commit", *args],
            cwd=str(cwd or self.fixture),
            env=env or self.commit_env(),
            capture_output=True,
            text=True,
            timeout=300,
        )

    def eval_exports(self, output: str) -> dict:
        """Parse the runner's `export K=V` stdout lines into a dict."""
        exports: dict[str, str] = {}
        for line in output.splitlines():
            if line.startswith("export "):
                key, _, raw = line[len("export "):].partition("=")
                exports[key] = shlex.split(raw)[0]
        return exports

    def setup_session(self, *setup_args: str) -> tuple[subprocess.CompletedProcess, dict]:
        proc = self.run_setup(*setup_args)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc, self.eval_exports(proc.stdout)

    def commit_session(
        self, setup_proc: subprocess.CompletedProcess | None, exports: dict,
        *commit_args: str,
    ) -> subprocess.CompletedProcess:
        env = self.commit_env()
        env.update(exports)
        return self.run_commit(*commit_args, env=env)

    def trace_stages(self, env: dict) -> list[str]:
        path = Path(env["DONE_RUN_TRACE_FILE"])
        if not path.exists():
            return []
        return [
            line[len("stage "):] for line in path.read_text().splitlines()
            if line.startswith("stage ")
        ]

    def write_user_facts(self, *rows: tuple[str, str]) -> None:
        facts = self.tmp / "user-facts.md"
        lines = ["# fixture user facts\n"]
        if rows:
            lines.append("\n| key | value |\n|---|---|\n")
            for key, value in rows:
                lines.append(f"| `{key}` | `{value}` |\n")
        facts.write_text("".join(lines))

    def commit_count(self) -> int:
        return int(self.git("rev-list", "--count", "HEAD").stdout.strip())


class DoneRunSetupTest(FixtureMixin, unittest.TestCase):
    def test_happy_path_writes_marker_manifest_and_exports(self) -> None:
        self.init_fixture_repo()
        proc = self.run_setup("--label", "fixture-run")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        session = self.done_session()
        markers = sorted(session.glob("run-start-*"))
        self.assertEqual(len(markers), 1)
        fields = markers[0].read_text().split()
        self.assertEqual(len(fields), 3)
        manifests = list(session.glob("run-manifest-*.json"))
        self.assertEqual(len(manifests), 1)
        record = json.loads(manifests[0].read_text())
        self.assertFalse(record.get("complete", True))
        self.assertIn(f"export DONE_RUN_ID={record['run_id']}", proc.stdout)
        self.assertIn("export DONE_LOCK_DIR=", proc.stdout)
        self.assertIn("export DONE_LOCK_TOKEN=", proc.stdout)
        self.assertIn(f"export DONE_RUN_MANIFEST={manifests[0].resolve()}", proc.stdout)
        self.assertIn(f"export DONE_RUN_MARKER={markers[0].resolve()}", proc.stdout)

    def test_held_lock_refuses_with_lock_evidence_and_writes_nothing(self) -> None:
        self.init_fixture_repo()
        holder = subprocess.run(
            ["bash", str(LOCK_SCRIPT), "wait-acquire", "--label", "holder",
             "--max-wait", "10"],
            cwd=str(self.fixture), env=self.runner_env(),
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(holder.returncode, 0, holder.stderr)
        proc = self.run_setup("--label", "contender")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("OUTCOME: fail", proc.stderr)
        self.assertIn("done-lock:", proc.stderr)
        self.assertFalse(self.done_session().exists())

    def test_resume_classification_is_read_only(self) -> None:
        self.init_fixture_repo()
        first = self.run_setup("--label", "first")
        self.assertEqual(first.returncode, 0, first.stderr)
        session = self.done_session()
        before = sorted(p.name for p in session.iterdir())
        second = self.run_setup("--label", "second")
        self.assertEqual(second.returncode, 2)
        combined = second.stdout + second.stderr
        for remedy in ("recover-manifest", "adopt", "finalize-manifest"):
            self.assertIn(remedy, combined)
        self.assertIn("no new boundary written", combined)
        after = sorted(p.name for p in session.iterdir())
        self.assertEqual(before, after)

    def test_from_manifest_reenters_existing_boundary(self) -> None:
        self.init_fixture_repo()
        first = self.run_setup("--label", "first")
        self.assertEqual(first.returncode, 0, first.stderr)
        run_id = next(
            line.split("=", 1)[1].strip()
            for line in first.stdout.splitlines()
            if line.startswith("export DONE_RUN_ID=")
        )
        second = self.run_setup("--from-manifest", run_id)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn(f"export DONE_RUN_ID={run_id}", second.stdout)
        manifests = list(self.done_session().glob("run-manifest-*.json"))
        self.assertEqual(len(manifests), 1)

    def test_setup_provisioned_worktree_transferred_reviews_arrival(self) -> None:
        """Wrapper witness for the foreign-by-arrival default (plan
        docs/history/plans/2026-11-01-done-setup-staging-doc-foreign-arrival-default.md
        Task 1): setup over a provisioned linked worktree whose transferred
        reviews home carries pre-marker staging docs, with NO foreign list,
        succeeds and classifies the pre-marker docs foreign-by-arrival into
        the manifest's foreign-review list. A mid-session untracked scratch
        file keeps the residue sweep's dirty-worktree skip arm engaged so the
        provisioned worktree survives the setup's own fail-open sweep."""
        self.init_fixture_repo()
        gitignore = self.fixture / ".gitignore"
        gitignore.write_text(gitignore.read_text() + ".ai-playbook/reviews/\n")
        self.git("add", ".gitignore")
        self.git("commit", "-qm", "ignore the reviews home")
        review_rel = ".ai-playbook/reviews/2026-11-01-transferred-review-r1.md"
        (self.fixture / review_rel).parent.mkdir(parents=True, exist_ok=True)
        (self.fixture / review_rel).write_text("staged review record\n")
        (self.fixture / ".ai-playbook/reviews/"
         "2026-11-01-transferred-review-r1.stats.json").write_text("{}\n")
        wt = self.tmp / "repo-wt-provisioned"
        self.git("worktree", "add", "-q", "-b", "wt-provisioned", str(wt))
        # The provisioning transfer: the checked-out facts copy is already in
        # the worktree; the transfer copies the whole gitignored reviews home.
        shutil.copytree(
            self.fixture / ".ai-playbook" / "reviews",
            wt / ".ai-playbook" / "reviews",
        )
        doc_mtime = time.time() - 3600.0
        os.utime(wt / review_rel, (doc_mtime, doc_mtime))
        (wt / "scratch-untracked.md").write_text("untracked\n")
        env = self.runner_env()
        env["DONE_SWEEP_REPO_ROOT"] = str(wt)

        proc = self.run_setup("--label", "fixture-run", cwd=wt, env=env)

        self.assertEqual(proc.returncode, 0, proc.stderr)
        # the writer echo relays on stderr (the acquisition stdout carries
        # only export lines); the report shape is pinned beyond the loose
        # substring: the count and the bounded sample listing (the existing
        # report-emission limit)
        self.assertIn("foreign-by-arrival", proc.stderr)
        self.assertIn(
            "write-manifest: foreign-by-arrival: 1 gitignored staging "
            "candidate(s)",
            proc.stderr,
        )
        self.assertIn(review_rel, proc.stderr)
        self.assertNotIn("foreign-by-arrival", proc.stdout)
        exports = self.eval_exports(proc.stdout)
        marker_epoch = int(Path(exports["DONE_RUN_MARKER"]).read_text().split()[0])
        self.assertGreater(marker_epoch, doc_mtime)
        record = json.loads(Path(exports["DONE_RUN_MANIFEST"]).read_text())
        self.assertEqual(record["foreign_review_paths"], [review_rel])
        self.assertEqual(record["owned_review_paths"], [])
        self.assertFalse(record.get("complete", True))


class DoneRunSetupResidueSweepTest(FixtureMixin, unittest.TestCase):
    """Task 2 witnesses (plan
    2026-10-29-gate-removal-task2-review-residues): the fail-open residue
    sweep's retained-branch evidence survives the setup summary filter for
    every skip class, a no-branch-identity candidate invents no branch
    data, and a missing or failing sweep helper leaves the setup boundary
    and its own classification unchanged."""

    def add_adhoc_worktree(self, slug: str, branch: str) -> Path:
        path = self.tmp / f"repo-wt-{slug}"
        self.git("worktree", "add", "-q", "-b", branch, str(path))
        return path

    def git_at(self, date: str, *args: str, repo: Path | None = None):
        """A fixture git call with both commit dates pinned, so the
        sweep's introduction-versus-branch comparison is deterministic."""
        proc = subprocess.run(
            ["git", "-C", str(repo or self.fixture), *args],
            capture_output=True, text=True, timeout=60,
            env={
                **os.environ,
                "GIT_AUTHOR_DATE": date,
                "GIT_COMMITTER_DATE": date,
            },
        )
        if proc.returncode != 0:
            raise AssertionError(f"git {args} failed: {proc.stderr}")
        return proc

    def branch_oid(self, branch: str) -> str:
        return self.git("rev-parse", branch).stdout.strip()

    def land_twin(self, basename: str, date: str) -> None:
        """The twin's introduction commit: the plans-root vintage and the
        completed twin land in one dated commit, so the sweep's arm-6
        touched set carries the plans-root path a candidate branch
        re-commits."""
        plans = self.fixture / "docs/history/plans"
        (plans / "completed").mkdir(parents=True, exist_ok=True)
        (plans / basename).write_text("# Plan\n\n")
        (plans / "completed" / basename).write_text("# Plan\n\n")
        self.git_at(date, "add", "docs/history/plans")
        self.git_at(date, "commit", "-qm", f"plan: land {basename} with its twin")

    def commit_plan_in_worktree(self, path: Path, basename: str, date: str) -> None:
        plan = path / "docs/history/plans" / basename
        plan.parent.mkdir(parents=True, exist_ok=True)
        plan.write_text("# Plan worktree copy\n\n")
        self.git_at(date, "add", "docs/history/plans", repo=path)
        self.git_at(date, "commit", "-qm", f"plan: candidate {basename}", repo=path)

    def assert_summary_relays_skip(self, proc, branch: str, reason: str) -> None:
        """The summary line cmd_setup prints relays the branch-report skip
        evidence verbatim on stderr (the acquisition stdout carries only
        export lines), and the sweep's final OUTCOME rides the same relayed
        block as its last line (the sweep prints it last and the filter
        preserves order)."""
        self.assertIn(
            f"done_run setup: residue sweep (fail-open): branch-report: "
            f"branch {branch}: skipped at {self.branch_oid(branch)}; "
            f"reason: {reason}\nOUTCOME: pass\n",
            proc.stderr,
        )
        self.assertNotIn("residue sweep", proc.stdout)

    def test_residue_sweep_relays_dirty_branch_backed_skip_evidence(self) -> None:
        self.init_fixture_repo()
        path = self.add_adhoc_worktree("dirty", "wt-dirty")
        (path / "scratch-untracked.md").write_text("untracked\n")
        proc, exports = self.setup_session("--label", "fixture-run")
        self.assert_summary_relays_skip(proc, "wt-dirty", "dirty worktree")
        # fail-open continuation: the boundary was still written
        self.assertTrue(exports.get("DONE_RUN_ID"))
        # the skipped candidate's registration and tree survive the run
        self.assertTrue(path.is_dir())

    def test_residue_sweep_relays_post_landing_branch_backed_skip_evidence(self) -> None:
        self.init_fixture_repo()
        basename = "2026-01-01-alpha.md"
        self.land_twin(basename, "2026-01-01T00:00:00Z")
        path = self.add_adhoc_worktree("post", "wt-post")
        self.commit_plan_in_worktree(path, basename, "2026-01-02T00:00:00Z")
        proc, exports = self.setup_session("--label", "fixture-run")
        self.assert_summary_relays_skip(
            proc, "wt-post", "post-landing commits on branch"
        )
        self.assertTrue(exports.get("DONE_RUN_ID"))
        self.assertTrue(path.is_dir())

    def test_residue_sweep_relays_live_session_branch_backed_skip_evidence(self) -> None:
        self.init_fixture_repo()
        basename = "2026-01-01-alpha.md"
        # the twin's introduction postdates the branch's plan commit, so
        # the post-landing arm passes and the live-session witness decides
        self.land_twin(basename, "2026-01-02T00:00:00Z")
        path = self.add_adhoc_worktree("live", "wt-live")
        self.commit_plan_in_worktree(path, basename, "2026-01-01T00:00:00Z")
        stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        claims = self.fixture / "docs/tmp/execution-claims"
        claims.mkdir(parents=True, exist_ok=True)
        (claims / basename).write_text(
            "session: sess-setup-sweep\n"
            f"plan: docs/history/plans/{basename}\n"
            f"created: {stamp}\n"
            f"updated: {stamp}\n"
        )
        proc, exports = self.setup_session("--label", "fixture-run")
        self.assert_summary_relays_skip(
            proc, "wt-live",
            f"live-session evidence: execution-claims claim {basename}",
        )
        self.assertTrue(exports.get("DONE_RUN_ID"))
        self.assertTrue(path.is_dir())

    def test_residue_sweep_relays_missing_completed_twin_skip_evidence(self) -> None:
        self.init_fixture_repo()
        path = self.add_adhoc_worktree("twinless", "wt-twinless")
        self.commit_plan_in_worktree(
            path, "2026-01-01-beta.md", "2026-01-01T00:00:00Z"
        )
        proc, exports = self.setup_session("--label", "fixture-run")
        self.assert_summary_relays_skip(
            proc, "wt-twinless", "no completed twin in the primary HEAD tree"
        )
        self.assertTrue(exports.get("DONE_RUN_ID"))
        self.assertTrue(path.is_dir())

    def test_residue_sweep_keeps_no_branch_identity_skip_anonymous(self) -> None:
        self.init_fixture_repo()
        path = self.tmp / "repo-wt-loose"
        self.git("worktree", "add", "-q", "--detach", str(path))
        shutil.rmtree(path)
        proc, exports = self.setup_session("--label", "fixture-run")
        # the summary relays the sweep's pass on stderr but invents no
        # branch data for the branchless stale detached registration
        self.assertIn(
            "done_run setup: residue sweep (fail-open): OUTCOME: pass",
            proc.stderr,
        )
        self.assertNotIn("branch-report:", proc.stdout)
        self.assertNotIn("skipped at", proc.stdout)
        self.assertTrue(exports.get("DONE_RUN_ID"))

    def runner_dir_with_helpers(
        self, name: str, doctored: dict[str, str]
    ) -> tuple[Path, Path]:
        """A private runner copy whose resolve_helper sees this directory
        first: every repo helper is symlinked in except the doctored
        names, which are written with the given bodies; the returned home
        is empty so the deployed-home fallback arm resolves nothing."""
        runner_dir = self.tmp / name
        runner_dir.mkdir()
        shutil.copy2(RUNNER, runner_dir / "done_run.sh")
        for helper in REPO_ROOT.joinpath("scripts").iterdir():
            if (helper.suffix in (".py", ".sh", ".json")
                    and helper.name not in ("done_run.sh", *doctored)
                    and not helper.name.startswith("test_")):
                os.symlink(helper, runner_dir / helper.name)
        for helper_name, body in doctored.items():
            # an empty body omits the helper entirely, so neither
            # resolve_helper arm can resolve it
            if body:
                (runner_dir / helper_name).write_text(body)
        home = self.tmp / f"{name}-home"
        (home / ".ai-playbook").mkdir(parents=True)
        return runner_dir, home

    def run_via_runner_dir(self, runner_dir: Path, home: Path) -> subprocess.CompletedProcess:
        env = self.runner_env()
        env["HOME"] = str(home)
        return subprocess.run(
            ["bash", str(runner_dir / "done_run.sh"), "setup", "--label", "fixture-run"],
            cwd=str(self.fixture),
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
        )

    def test_missing_sweep_helper_keeps_setup_boundary(self) -> None:
        self.init_fixture_repo()
        runner_dir, home = self.runner_dir_with_helpers(
            "runner-no-sweep",
            {"worktree_closeout_migrate.py": ""},
        )
        proc = self.run_via_runner_dir(runner_dir, home)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        # the sweep step is skipped whole and setup still writes its
        # boundary: the existing classification is unchanged
        self.assertNotIn("residue sweep", proc.stdout)
        exports = self.eval_exports(proc.stdout)
        self.assertTrue(exports.get("DONE_RUN_ID"))

    def test_failing_sweep_keeps_setup_boundary_and_relays_outcome(self) -> None:
        self.init_fixture_repo()
        runner_dir, home = self.runner_dir_with_helpers(
            "runner-bad-sweep",
            {
                "worktree_closeout_migrate.py": (
                    "import sys\n"
                    "print('sweep stub: simulated command failure')\n"
                    "print('OUTCOME: tool_error')\n"
                    "sys.exit(9)\n"
                )
            },
        )
        proc = self.run_via_runner_dir(runner_dir, home)
        # fail-open: the sweep's failure OUTCOME is relayed verbatim on
        # stderr and the setup classification is unchanged (rc 0 boundary
        # written)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(
            "done_run setup: residue sweep (fail-open): OUTCOME: tool_error",
            proc.stderr,
        )
        self.assertNotIn("residue sweep", proc.stdout)
        exports = self.eval_exports(proc.stdout)
        self.assertTrue(exports.get("DONE_RUN_ID"))


class DoneRunSetupAcquisitionStdoutTest(FixtureMixin, unittest.TestCase):
    """Task 1 witnesses (plan docs/history/plans/
    2026-11-03-done-run-setup-stdout-export-emission-split.md): the setup
    acquisition stdout is eval-safe by construction -
    every stdout line on the success, re-entry, and refusal paths is an
    `export`-prefixed assignment the payload contract owns, every status,
    advisory, and diagnostic line (plain echo or printf relay) rides
    stderr beside an unchanged byte-identical payload, and a whole-stdout
    `eval` parses and sets the exports even when a status line carries
    shell metacharacters."""

    def assert_stdout_export_lines_only(self, proc) -> None:
        nonexport = [
            line for line in proc.stdout.splitlines()
            if line and not line.startswith("export ")
        ]
        self.assertEqual(nonexport, [], proc.stdout)

    def eval_whole_stdout(self, proc) -> dict:
        """A whole-stdout `eval` in a fresh bash: a status line beside the
        export block aborts the parse mid-file (the 2026-10-26/27 and
        2026-11-03 witnesses), so the eval must exit 0 with every payload
        export set in the eval's own env."""
        check = subprocess.run(
            ["bash", "-c",
             'eval "$1" && printf \'%s\\n\' '
             '"${DONE_LOCK_DIR-unset}" "${DONE_LOCK_TOKEN-unset}" '
             '"${DONE_RUN_MARKER-unset}" "${DONE_RUN_MANIFEST-unset}" '
             '"${DONE_RUN_ID-unset}"',
             "done-run-eval", proc.stdout],
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(check.returncode, 0, check.stderr)
        keys = ["DONE_LOCK_DIR", "DONE_LOCK_TOKEN", "DONE_RUN_MARKER",
                "DONE_RUN_MANIFEST", "DONE_RUN_ID"]
        values = check.stdout.splitlines()
        self.assertEqual(len(values), len(keys), check.stdout)
        for key, value in zip(keys, values):
            self.assertNotEqual(value, "unset", key)
        return dict(zip(keys, values))

    def assert_payload_shape(self, proc) -> list[str]:
        """The export payload keeps its exact byte shape: the lock acquire
        echo's two relayed assignment lines followed by the five setup
        assignment lines in the contract's order, `printf '%q'`-quoted
        values (bare for fixture-safe paths), the run id bare — the exact
        stdout bytes the pre-split emission built."""
        session = self.done_session()
        marker = next(session.glob("run-start-*")).resolve()
        manifest = next(session.glob("run-manifest-*.json")).resolve()
        run_id = json.loads(manifest.read_text())["run_id"]
        exports = self.eval_exports(proc.stdout)
        payload = [
            line for line in proc.stdout.splitlines()
            if line.startswith("export ")
        ]
        self.assertEqual(payload, [
            f"export DONE_LOCK_DIR={shlex.quote(exports['DONE_LOCK_DIR'])}",
            f"export DONE_LOCK_TOKEN={shlex.quote(exports['DONE_LOCK_TOKEN'])}",
            f"export DONE_LOCK_DIR={shlex.quote(exports['DONE_LOCK_DIR'])}",
            f"export DONE_LOCK_TOKEN={shlex.quote(exports['DONE_LOCK_TOKEN'])}",
            f"export DONE_RUN_MARKER={shlex.quote(str(marker))}",
            f"export DONE_RUN_MANIFEST={shlex.quote(str(manifest))}",
            f"export DONE_RUN_ID={run_id}",
        ])
        return payload

    def test_success_stdout_is_export_lines_only_and_eval_safe(self) -> None:
        self.init_fixture_repo()
        proc = self.run_setup("--label", "fixture-run")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assert_stdout_export_lines_only(proc)
        evaled = self.eval_whole_stdout(proc)
        exports = self.eval_exports(proc.stdout)
        self.assertEqual(evaled, exports)
        self.assertEqual(evaled["DONE_RUN_ID"], exports["DONE_RUN_ID"])

    def test_export_payload_lines_keep_byte_shape(self) -> None:
        """The byte-identical payload contract: the export lines carry the
        exact bytes the pre-split emission built (`printf '%q'` quoting in
        the contract's order), so a caller that evaluates only the export
        lines sees no change."""
        self.init_fixture_repo()
        proc = self.run_setup("--label", "fixture-run")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assert_payload_shape(proc)

    def test_reentry_status_lines_ride_stderr_exports_stdout(self) -> None:
        self.init_fixture_repo()
        first = self.run_setup("--label", "first")
        self.assertEqual(first.returncode, 0, first.stderr)
        run_id = self.eval_exports(first.stdout)["DONE_RUN_ID"]
        second = self.run_setup("--from-manifest", run_id)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn(
            f"done_run setup: re-entering boundary run_id={run_id} "
            "(explicit --from-manifest)",
            second.stderr,
        )
        self.assertNotIn("re-entering boundary", second.stdout)
        self.assert_stdout_export_lines_only(second)
        self.assertEqual(
            self.eval_exports(second.stdout)["DONE_RUN_ID"], run_id
        )

    def test_partial_marker_stop_diagnostics_ride_stderr(self) -> None:
        self.init_fixture_repo()
        repo_top = self.git("rev-parse", "--show-toplevel").stdout.strip()
        digest = hashlib.sha256(repo_top.rstrip("/").encode()).hexdigest()
        session = self.done_session()
        session.mkdir(parents=True)
        (session / "run-start-20261103T000000Z").write_text(
            f"{int(time.time())} {digest} {os.getpid()}\n"
        )
        second = self.run_setup("--label", "second")
        self.assertEqual(second.returncode, 2)
        self.assertIn(
            "done_run setup: found a content-confirmed marker with no "
            "manifest (partial marker write)",
            second.stderr,
        )
        self.assertIn(
            "done_run setup: remedy: re-run setup to write the manifest "
            "bound to that marker, or remove the marker to discard the "
            "attempt",
            second.stderr,
        )
        self.assertNotIn("partial marker write", second.stdout)
        self.assert_stdout_export_lines_only(second)

    def test_refusal_stdout_eval_safe_release_relay_on_stderr(self) -> None:
        """The orphan classification stop refuses through setup_die, whose
        terminal release relay is a printf of the captured release output:
        pre-change that block (its `OUTCOME:` line included) lands on stdout
        beside the lock payload relay; post-change stdout stays
        export-lines-only and the relayed block rides stderr. The release's
        own `OUTCOME:` contract channel is untouched - only the wrapper's
        relay destination moves."""
        self.init_fixture_repo()
        first = self.run_setup("--label", "first")
        self.assertEqual(first.returncode, 0, first.stderr)
        second = self.run_setup("--label", "second")
        self.assertEqual(second.returncode, 2)
        self.assertIn(
            "done_run setup: no new boundary written", second.stderr
        )
        self.assertIn("OUTCOME:", second.stderr)
        self.assertNotIn("OUTCOME:", second.stdout)
        self.assert_stdout_export_lines_only(second)

    def test_metacharacter_status_line_cannot_break_the_eval(self) -> None:
        """The 2026-11-03 witness: a status line carrying shell
        metacharacters (the residue sweep's branch-report relays a branch
        name with braces) aborted a whole-stdout eval after the hold was
        taken. Post-change the line rides stderr and the eval parses."""
        self.init_fixture_repo()
        path = self.tmp / "repo-wt-brace"
        self.git("worktree", "add", "-q", "-b", "wt-{brace}-plan", str(path))
        (path / "scratch-untracked.md").write_text("untracked\n")
        proc = self.run_setup("--label", "fixture-run")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("wt-{brace}-plan", proc.stderr)
        self.assertIn("skipped at", proc.stderr)
        self.assertNotIn("wt-{brace}-plan", proc.stdout)
        self.assertNotIn("skipped at", proc.stdout)
        self.assert_stdout_export_lines_only(proc)
        self.assert_payload_shape(proc)
        self.eval_whole_stdout(proc)


class DoneRunSetupManifestStateTest(FixtureMixin, unittest.TestCase):
    """Task 1 witnesses (plan
    docs/history/plans/2026-10-12-done-interrupted-manifest-state-
    classification.md): setup classifies the newest manifest through the
    canonical terminal states consumed from done_sweep_gates_lib's
    classify_run_boundary (read at run identity), the orphan and marker
    refusals stay byte-identical, and a corrupt newest record fails closed
    naming the record."""

    def seed_run(self, label: str) -> dict:
        self.init_fixture_repo()
        proc = self.run_setup("--label", label)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return self.eval_exports(proc.stdout)

    def terminal_notes(self, output: str) -> list[str]:
        return [
            line for line in output.splitlines() if "closed boundary" in line
        ]

    def test_finalized_newest_manifest_continues_to_fresh_boundary(self) -> None:
        exports = self.seed_run("first")
        manifest = Path(exports["DONE_RUN_MANIFEST"])
        run_id = exports["DONE_RUN_ID"]
        self.rewrite_manifest(manifest, complete=True)
        before = manifest.read_bytes()
        second = self.run_setup("--label", "second")
        self.assertEqual(second.returncode, 0, second.stderr)
        notes = self.terminal_notes(second.stderr)
        self.assertEqual(len(notes), 1, second.stderr)
        self.assertIn("finalized", notes[0])
        self.assertIn(run_id, notes[0])
        # the prior manifest stays byte-identical and a fresh boundary lands
        self.assertEqual(manifest.read_bytes(), before)
        session = self.done_session()
        self.assertEqual(len(list(session.glob("run-start-*"))), 2)
        manifests = sorted(session.glob("run-manifest-*.json"))
        self.assertEqual(len(manifests), 2)
        fresh = json.loads(manifests[-1].read_text())
        self.assertNotEqual(fresh["run_id"], run_id)
        self.assertFalse(fresh["complete"])
        self.assertIn(f"export DONE_RUN_ID={fresh['run_id']}", second.stdout)

    def test_adopted_newest_manifest_continues_with_state_named(self) -> None:
        exports = self.seed_run("first")
        template = Path(exports["DONE_RUN_MANIFEST"])
        marker_field = json.loads(template.read_text())["marker"]
        # the newest record's run id is named by another manifest's
        # adopted_from link (the directory's adopted set closes the boundary)
        newest_id = "20991231T235959Z-adoptee00000"
        older_id = "20260101T000000Z-adopter00000"
        self.craft_manifest_file(template, newest_id, marker=marker_field)
        adopter = self.craft_manifest_file(
            template, older_id, marker=marker_field, adopted_from=newest_id
        )
        template.unlink()  # the crafted adoptee is the newest manifest file
        before_newest = (
            self.done_session() / f"run-manifest-{newest_id}.json"
        ).read_bytes()
        second = self.run_setup("--label", "second")
        self.assertEqual(second.returncode, 0, second.stderr)
        notes = self.terminal_notes(second.stderr)
        self.assertEqual(len(notes), 1, second.stderr)
        self.assertIn("adopted", notes[0])
        self.assertIn(newest_id, notes[0])
        self.assertEqual(
            (self.done_session() / f"run-manifest-{newest_id}.json").read_bytes(),
            before_newest,
        )
        self.assertTrue(adopter.is_file())
        self.assertEqual(len(list(self.done_session().glob("run-start-*"))), 2)

    def test_dispositioned_dead_root_newest_manifest_continues(self) -> None:
        exports = self.seed_run("first")
        manifest = Path(exports["DONE_RUN_MANIFEST"])
        run_id = exports["DONE_RUN_ID"]
        self.rewrite_manifest(
            manifest,
            repo_root="0" * 64,  # the digest arm mismatch: a dead root
            dispositioned={
                "reason": "work-verified-landed",
                "date": "2026-10-13",
                "note": "dead-root close",
            },
        )
        before = manifest.read_bytes()
        second = self.run_setup("--label", "second")
        self.assertEqual(second.returncode, 0, second.stderr)
        notes = self.terminal_notes(second.stderr)
        self.assertEqual(len(notes), 1, second.stderr)
        self.assertIn("dispositioned", notes[0])
        self.assertIn(run_id, notes[0])
        self.assertEqual(manifest.read_bytes(), before)
        self.assertEqual(len(list(self.done_session().glob("run-start-*"))), 2)

    def test_shadow_closed_copy_continues_with_shadow_closed_named(self) -> None:
        exports = self.seed_run("first")
        manifest = Path(exports["DONE_RUN_MANIFEST"])
        run_id = exports["DONE_RUN_ID"]
        self.rewrite_manifest(manifest, complete=True)  # the canonical twin closes
        payload = json.loads(manifest.read_text())
        payload["complete"] = False
        shadow = self.done_session() / f"run-manifest-{run_id}.worktree.json"
        shadow.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        self.assertGreater(shadow.name, manifest.name)  # the copy sorts newest
        before_canon = manifest.read_bytes()
        before_shadow = shadow.read_bytes()
        second = self.run_setup("--label", "second")
        self.assertEqual(second.returncode, 0, second.stderr)
        notes = self.terminal_notes(second.stderr)
        self.assertEqual(len(notes), 1, second.stderr)
        self.assertIn("shadow-closed", notes[0])
        self.assertIn(run_id, notes[0])
        # both prior records stay byte-identical and a fresh boundary lands
        self.assertEqual(manifest.read_bytes(), before_canon)
        self.assertEqual(shadow.read_bytes(), before_shadow)
        self.assertEqual(len(list(self.done_session().glob("run-start-*"))), 2)

    def test_current_boundary_orphan_refusal_lines_byte_identical(self) -> None:
        exports = self.seed_run("first")
        run_id = exports["DONE_RUN_ID"]
        session = self.done_session()
        before = sorted(p.name for p in session.iterdir())
        second = self.run_setup("--label", "second")
        self.assertEqual(second.returncode, 2)
        self.assertIn(
            "done_run setup: found an unadopted current-boundary manifest "
            f"run_id={run_id} bound to the newest content-confirmed marker",
            second.stderr,
        )
        self.assertIn(
            "done_run setup: remedies: python3 scripts/done_sweep_gates_lib.py "
            f"recover-manifest --run-id {run_id} | re-enter exactly with "
            f"--from-manifest {run_id} | adopt via setup --adopt {run_id} | "
            "python3 scripts/done_sweep_gates_lib.py "
            f"finalize-manifest --run-id {run_id}",
            second.stderr,
        )
        self.assertIn(
            "done_run setup: no new boundary written (read-only "
            "classification; pass --from-manifest to re-enter explicitly)",
            second.stderr,
        )
        self.assertEqual(sorted(p.name for p in session.iterdir()), before)

    def test_stale_marker_orphan_refusal_lines_byte_identical(self) -> None:
        exports = self.seed_run("first")
        run_id = exports["DONE_RUN_ID"]
        marker = Path(exports["DONE_RUN_MARKER"])
        marker.write_text("garbage marker content\n")  # no longer confirmed
        second = self.run_setup("--label", "second")
        self.assertEqual(second.returncode, 2)
        self.assertIn(
            "done_run setup: found a stale-marker or markerless interrupted "
            f"manifest run_id={run_id}",
            second.stderr,
        )
        self.assertIn(
            "done_run setup: remedies: python3 scripts/done_sweep_gates_lib.py "
            f"recover-manifest --run-id {run_id} | adopt via setup --adopt "
            f"{run_id} | re-enter exactly with --from-manifest {run_id} | "
            "python3 scripts/done_sweep_gates_lib.py "
            f"finalize-manifest --run-id {run_id} | python3 "
            "scripts/done_sweep_gates_lib.py disposition-manifest --run-id "
            f"{run_id} (dead root only)",
            second.stderr,
        )
        self.assertIn(
            "done_run setup: no new boundary written (read-only "
            "classification; pass --from-manifest to re-enter explicitly)",
            second.stderr,
        )

    def test_corrupt_newest_manifest_fails_closed_naming_the_record(self) -> None:
        exports = self.seed_run("first")
        manifest = Path(exports["DONE_RUN_MANIFEST"])
        manifest.write_text("{ not json\n")
        session = self.done_session()
        before = sorted(p.name for p in session.iterdir())
        second = self.run_setup("--label", "second")
        self.assertEqual(second.returncode, 2)
        self.assertIn("unparseable", second.stderr)
        self.assertIn(manifest.name, second.stderr)
        # fail-closed: no fresh boundary, the corrupt record untouched
        self.assertEqual(sorted(p.name for p in session.iterdir()), before)

    def test_marker_only_refusal_unchanged(self) -> None:
        exports = self.seed_run("first")
        Path(exports["DONE_RUN_MANIFEST"]).unlink()
        second = self.run_setup("--label", "second")
        self.assertEqual(second.returncode, 2)
        self.assertIn(
            "done_run setup: found a content-confirmed marker with no "
            "manifest (partial marker write)",
            second.stderr,
        )
        self.assertIn(
            "done_run setup: remedy: re-run setup to write the manifest "
            "bound to that marker, or remove the marker to discard the attempt",
            second.stderr,
        )
        self.assertIn("done_run setup: no new boundary written", second.stderr)

    def test_from_manifest_reentry_unchanged_for_terminal_record(self) -> None:
        exports = self.seed_run("first")
        run_id = exports["DONE_RUN_ID"]
        manifest = Path(exports["DONE_RUN_MANIFEST"])
        self.rewrite_manifest(manifest, complete=True)
        second = self.run_setup("--from-manifest", run_id)
        self.assertEqual(second.returncode, 0, second.stderr)
        reexports = self.eval_exports(second.stdout)
        self.assertEqual(reexports["DONE_RUN_ID"], run_id)
        self.assertEqual(
            Path(reexports["DONE_RUN_MANIFEST"]).resolve(), manifest.resolve()
        )
        self.assertEqual(
            Path(reexports["DONE_RUN_MARKER"]).resolve(),
            Path(exports["DONE_RUN_MARKER"]).resolve(),
        )
        session = self.done_session()
        self.assertEqual(len(list(session.glob("run-manifest-*.json"))), 1)
        self.assertEqual(len(list(session.glob("run-start-*"))), 1)


class DoneRunSetupTerminalReleaseTest(FixtureMixin, unittest.TestCase):
    """Task 1 witnesses (plan docs/history/plans/2026-10-24-done-run-lock-
    span-and-append-ordering.md): every terminal classification and
    fail-closed exit after setup acquires the done lock releases only the
    generation that invocation acquired before exiting with the original
    refusal outcome and remedy text, while the explicit --from-manifest
    re-entry keeps its acquired lock."""

    def lock_status(self) -> str:
        proc = subprocess.run(
            ["bash", str(LOCK_SCRIPT), "status"],
            cwd=str(self.fixture), env=self.runner_env(),
            capture_output=True, text=True, timeout=120,
        )
        return proc.stdout + proc.stderr

    def seed_run(self, label: str) -> dict:
        self.init_fixture_repo()
        proc = self.run_setup("--label", label)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return self.eval_exports(proc.stdout)

    def classifier_failure_env(self) -> dict:
        """A PATH shim whose python3 fails only the boundary-classifier
        invocation, so the second setup reaches the classifier's
        tool-failure exit with the acquired lock held."""
        bin_dir = self.tmp / "shim-bin"
        bin_dir.mkdir()
        shim = bin_dir / "python3"
        shim.write_text(
            "#!/bin/sh\n"
            'for arg in "$@"; do\n'
            '  case "$arg" in\n'
            "    classify-run-boundary)\n"
            '      echo "shim: the boundary classifier failed" >&2\n'
            "      exit 9 ;;\n"
            "  esac\n"
            "done\n"
            f'exec "{sys.executable}" "$@"\n',
            encoding="utf-8",
        )
        shim.chmod(0o755)
        env = self.runner_env()
        env["PATH"] = str(bin_dir) + os.pathsep + env["PATH"]
        return env

    def test_orphan_classification_stop_releases_and_reentry_holds(self) -> None:
        exports = self.seed_run("first")
        run_id = exports["DONE_RUN_ID"]
        session = self.done_session()
        before = sorted(p.name for p in session.iterdir())
        second = self.run_setup("--label", "second")
        self.assertEqual(second.returncode, 2)
        # the original refusal outcome and remedy text, unchanged
        self.assertIn(
            "done_run setup: remedies: python3 scripts/done_sweep_gates_lib.py "
            f"recover-manifest --run-id {run_id} | re-enter exactly with "
            f"--from-manifest {run_id} | adopt via setup --adopt {run_id}",
            second.stderr,
        )
        self.assertIn(
            "done_run setup: no new boundary written (read-only "
            "classification; pass --from-manifest to re-enter explicitly)",
            second.stderr,
        )
        # this invocation's acquired generation released: the lock is free
        # and the read-only stop wrote nothing
        self.assertIn(": free", self.lock_status())
        self.assertNotIn("did not release", second.stdout + second.stderr)
        self.assertEqual(sorted(p.name for p in session.iterdir()), before)
        # the explicit re-entry still acquires and keeps the lock
        third = self.run_setup("--from-manifest", run_id)
        self.assertEqual(third.returncode, 0, third.stderr)
        reexports = self.eval_exports(third.stdout)
        self.assertEqual(reexports["DONE_RUN_ID"], run_id)
        self.assertIn(": held", self.lock_status())
        meta = Path(reexports["DONE_LOCK_DIR"]) / "meta.env"
        token_line = next(
            line for line in meta.read_text().splitlines()
            if line.startswith("lock_token=")
        )
        self.assertEqual(token_line, f"lock_token={reexports['DONE_LOCK_TOKEN']}")

    def test_classifier_tool_failure_releases_the_acquired_lock(self) -> None:
        self.seed_run("first")
        session = self.done_session()
        before = sorted(p.name for p in session.iterdir())
        second = self.run_setup(
            "--label", "second", env=self.classifier_failure_env(),
        )
        self.assertEqual(second.returncode, 3)
        self.assertIn("shim: the boundary classifier failed", second.stderr)
        self.assertIn(
            "done_run setup: the manifest-state classifier failed; "
            "no new boundary written (fail-closed)",
            second.stderr,
        )
        self.assertIn(": free", self.lock_status())
        self.assertNotIn("did not release", second.stdout + second.stderr)
        self.assertEqual(sorted(p.name for p in session.iterdir()), before)

    def test_unreadable_manifest_fail_closed_releases_the_acquired_lock(self) -> None:
        exports = self.seed_run("first")
        manifest = Path(exports["DONE_RUN_MANIFEST"])
        manifest.write_text("{ not json\n")
        session = self.done_session()
        before = sorted(p.name for p in session.iterdir())
        second = self.run_setup("--label", "second")
        self.assertEqual(second.returncode, 2)
        self.assertIn("unparseable", second.stderr)
        self.assertIn(manifest.name, second.stderr)
        self.assertIn(": free", self.lock_status())
        self.assertNotIn("did not release", second.stdout + second.stderr)
        self.assertEqual(sorted(p.name for p in session.iterdir()), before)
class DoneRunSetupAdoptionTest(FixtureMixin, unittest.TestCase):
    """Task 1 regressions (plan 2026-10-25-done-run-resume-ownership-gap):
    setup --adopt routes the classified orphan boundary through the writer's
    existing adoption (prior start commit and ownership claims carried into
    the new linked manifest), exact re-entry stays exact, and every
    incompatible transition input refuses with no durable marker or manifest
    change."""

    OWNED_REVIEW = ".ai-playbook/reviews/2026-10-25-adopt-own-review-r1.md"
    FOREIGN_REVIEW = ".ai-playbook/reviews/2026-10-25-adopt-peer-review-r1.md"

    def seed_interrupted_run(self) -> dict:
        """A fixture run owning one review and marking one peer review
        foreign, left interrupted (complete=false): the adoption target."""
        self.init_fixture_repo()
        (self.fixture / self.OWNED_REVIEW).parent.mkdir(parents=True)
        (self.fixture / self.OWNED_REVIEW).write_text("owned staging review\n")
        (self.fixture / self.FOREIGN_REVIEW).write_text("peer staging review\n")
        (self.fixture / "seed.txt").write_text("seed\nwork\n")
        _, exports = self.setup_session(
            "--owned-path", "seed.txt",
            "--owned-review", self.OWNED_REVIEW,
            "--foreign-review", self.FOREIGN_REVIEW,
        )
        return exports

    def create_post_setup_review(self) -> str:
        """A review created after the interrupted setup: the adoption's new
        claim, the one the pre-change wrapper silently dropped."""
        rel = ".ai-playbook/reviews/2026-10-25-adopt-late-review-r2.md"
        (self.fixture / rel).write_text(
            "review created after the interrupted setup\n"
        )
        return rel

    def test_adopt_routes_classified_orphan_through_writer(self) -> None:
        exports = self.seed_interrupted_run()
        prior_path = Path(exports["DONE_RUN_MANIFEST"])
        prior_bytes = prior_path.read_bytes()
        prior = json.loads(prior_bytes)
        # Move HEAD past the interrupted boundary's start commit so the
        # preserved-start assertion has a discriminating witness (seed HEAD
        # must not equal adopt HEAD).
        (self.fixture / "seed.txt").write_text("seed\nwork\nmore\n")
        self.git("add", "seed.txt")
        self.git("commit", "-qm", "post-boundary work")
        new_head = self.git("rev-parse", "HEAD").stdout.strip()
        new_rel = self.create_post_setup_review()
        proc = self.run_setup(
            "--adopt", exports["DONE_RUN_ID"], "--owned-review", new_rel,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(
            f"adopting the classified interrupted boundary "
            f"run_id={exports['DONE_RUN_ID']}",
            proc.stderr,
        )
        reexports = self.eval_exports(proc.stdout)
        adopted = json.loads(Path(reexports["DONE_RUN_MANIFEST"]).read_text())
        self.assertNotEqual(adopted["run_id"], prior["run_id"])
        self.assertEqual(adopted["adopted_from"], prior["run_id"])
        # the prior boundary is preserved: start commit, owned plan, owned
        # start-dirt paths, and foreign classifications; the new claim adds on
        self.assertEqual(adopted["start_commit"], prior["start_commit"])
        self.assertNotEqual(adopted["start_commit"], new_head)
        self.assertEqual(adopted["owned_paths"], prior["owned_paths"])
        self.assertEqual(adopted["owned_plan_paths"], prior["owned_plan_paths"])
        self.assertEqual(
            adopted["owned_review_paths"],
            [new_rel] + prior["owned_review_paths"],
        )
        self.assertEqual(
            adopted["foreign_review_paths"], prior["foreign_review_paths"]
        )
        # the prior record is byte-identical and the new manifest binds a
        # fresh marker (non-positional: name inequality against the prior
        # marker, not list position)
        self.assertEqual(prior_path.read_bytes(), prior_bytes)
        session = self.done_session()
        self.assertEqual(len(list(session.glob("run-manifest-*.json"))), 2)
        self.assertNotEqual(adopted["marker"], prior["marker"])
        self.assertTrue((session / adopted["marker"]).is_file())
        self.assertIn(f"export DONE_RUN_ID={adopted['run_id']}", proc.stdout)

    def test_adopt_routes_stale_marker_orphan_through_writer(self) -> None:
        exports = self.seed_interrupted_run()
        prior = json.loads(Path(exports["DONE_RUN_MANIFEST"]).read_text())
        Path(exports["DONE_RUN_MARKER"]).write_text("garbage marker content\n")
        new_rel = self.create_post_setup_review()
        proc = self.run_setup(
            "--adopt", exports["DONE_RUN_ID"], "--owned-review", new_rel,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        adopted = json.loads(
            Path(self.eval_exports(proc.stdout)["DONE_RUN_MANIFEST"]).read_text()
        )
        self.assertEqual(adopted["adopted_from"], prior["run_id"])
        self.assertEqual(adopted["start_commit"], prior["start_commit"])
        self.assertEqual(
            adopted["owned_review_paths"],
            [new_rel] + prior["owned_review_paths"],
        )

    def test_adopt_mismatched_id_refuses_before_any_write(self) -> None:
        exports = self.seed_interrupted_run()
        prior_path = Path(exports["DONE_RUN_MANIFEST"])
        prior_bytes = prior_path.read_bytes()
        before = self.session_names()
        proc = self.run_setup("--adopt", "20991231T235959Z-notaboundary")
        self.assertEqual(proc.returncode, 1)
        self.assertIn(
            "--adopt 20991231T235959Z-notaboundary names no classified "
            "interrupted boundary",
            proc.stderr,
        )
        self.assertIn(f"(classified run_id: {exports['DONE_RUN_ID']})", proc.stderr)
        self.assertEqual(prior_path.read_bytes(), prior_bytes)
        self.assertEqual(self.session_names(), before)

    def test_adopt_terminal_boundary_refuses_without_durable_change(self) -> None:
        exports = self.seed_interrupted_run()
        manifest = Path(exports["DONE_RUN_MANIFEST"])
        record = json.loads(manifest.read_text())
        record["complete"] = True
        manifest.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        before = manifest.read_bytes()
        before_names = self.session_names()
        proc = self.run_setup("--adopt", exports["DONE_RUN_ID"])
        self.assertEqual(proc.returncode, 1)
        self.assertIn(
            f"--adopt {exports['DONE_RUN_ID']} names the classified boundary "
            f"run_id={exports['DONE_RUN_ID']}, which is finalized",
            proc.stderr,
        )
        self.assertEqual(manifest.read_bytes(), before)
        self.assertEqual(self.session_names(), before_names)

    def test_adopt_already_adopted_boundary_refuses_without_durable_change(self) -> None:
        self.seed_interrupted_run()
        session = self.done_session()
        prior_path = sorted(session.glob("run-manifest-*.json"))[0]
        template = json.loads(prior_path.read_text())
        newest_id = "20991231T235959Z-adoptee00000"
        template["run_id"] = newest_id
        newest = session / f"run-manifest-{newest_id}.json"
        newest.write_text(json.dumps(template, indent=2, sort_keys=True) + "\n")
        adopter_id = "20260101T000000Z-adopter00000"
        template["run_id"] = adopter_id
        template["adopted_from"] = newest_id
        adopter = session / f"run-manifest-{adopter_id}.json"
        adopter.write_text(json.dumps(template, indent=2, sort_keys=True) + "\n")
        prior_path.unlink()  # the crafted adoptee is the newest manifest file
        before_names = self.session_names()
        before_newest = newest.read_bytes()
        before_adopter = adopter.read_bytes()
        proc = self.run_setup("--adopt", newest_id)
        self.assertEqual(proc.returncode, 1)
        self.assertIn(
            f"--adopt {newest_id} names the classified boundary "
            f"run_id={newest_id}, which is adopted",
            proc.stderr,
        )
        self.assertEqual(newest.read_bytes(), before_newest)
        self.assertEqual(adopter.read_bytes(), before_adopter)
        self.assertEqual(self.session_names(), before_names)

    def test_adopt_already_adopted_target_refuses_at_forward_arm(self) -> None:
        """Given a terminal newest boundary and --adopt naming an older run
        whose own boundary is already adopted (a same-session adopter links
        it), the forward arm refuses separately before any fresh marker: no
        new marker or manifest, no forwarding note, no writer run, and every
        prior record stays byte-identical."""
        exports = self.seed_interrupted_run()
        session = self.done_session()
        seeded = Path(exports["DONE_RUN_MANIFEST"])
        marker_field = json.loads(seeded.read_text())["marker"]
        newest_id = "20991231T235959Z-newest00001"
        self.craft_manifest_file(
            seeded, newest_id, marker=marker_field, complete=True
        )
        target_id = "20260101T000000Z-target00001"
        self.craft_manifest_file(seeded, target_id, marker=marker_field)
        adopter_id = "20260101T000001Z-adopter0001"
        self.craft_manifest_file(
            seeded, adopter_id, marker=marker_field, adopted_from=target_id
        )
        seeded.unlink()  # the crafted finalized record is the newest manifest
        target = session / f"run-manifest-{target_id}.json"
        newest = session / f"run-manifest-{newest_id}.json"
        adopter = session / f"run-manifest-{adopter_id}.json"
        before = {path: path.read_bytes() for path in (newest, target, adopter)}
        before_names = self.session_names()
        proc = self.run_setup("--adopt", target_id)
        self.assertEqual(proc.returncode, 1)
        self.assertIn(
            f"--adopt {target_id} names run_id={target_id}, whose own "
            "boundary is already adopted",
            proc.stderr,
        )
        self.assertIn("no new boundary written", proc.stderr)
        # refused at the forward arm: the fresh boundary never starts, so no
        # forwarding note prints and the writer never runs
        self.assertNotIn(
            "is not the classified boundary and is forwarded", proc.stdout
        )
        self.assertNotIn("the writer refused", proc.stderr)
        for path, payload in before.items():
            self.assertEqual(path.read_bytes(), payload)
        self.assertEqual(self.session_names(), before_names)

    def test_adopt_dispositioned_target_refuses_at_forward_arm(self) -> None:
        """Given a terminal newest boundary and --adopt naming an older run
        carrying a dispositioned record, the forward arm refuses separately
        (distinct from the already-adopted refusal) before any fresh marker;
        no new marker or manifest and the dispositioned record stays
        byte-identical."""
        exports = self.seed_interrupted_run()
        session = self.done_session()
        seeded = Path(exports["DONE_RUN_MANIFEST"])
        marker_field = json.loads(seeded.read_text())["marker"]
        newest_id = "20991231T235959Z-newest00002"
        self.craft_manifest_file(
            seeded, newest_id, marker=marker_field, complete=True
        )
        target_id = "20260101T000000Z-dispos00001"
        self.craft_manifest_file(
            seeded,
            target_id,
            marker=marker_field,
            dispositioned={
                "reason": "work-verified-landed",
                "date": "2026-10-30",
                "note": "fixture disposition close",
            },
        )
        seeded.unlink()  # the crafted finalized record is the newest manifest
        target = session / f"run-manifest-{target_id}.json"
        newest = session / f"run-manifest-{newest_id}.json"
        before = {path: path.read_bytes() for path in (newest, target)}
        before_names = self.session_names()
        proc = self.run_setup("--adopt", target_id)
        self.assertEqual(proc.returncode, 1)
        self.assertIn(
            f"--adopt {target_id} names run_id={target_id}, whose own "
            "boundary is dispositioned",
            proc.stderr,
        )
        self.assertIn("no new boundary written", proc.stderr)
        self.assertNotIn(
            "is not the classified boundary and is forwarded", proc.stdout
        )
        self.assertNotIn("the writer refused", proc.stderr)
        for path, payload in before.items():
            self.assertEqual(path.read_bytes(), payload)
        self.assertEqual(self.session_names(), before_names)

    def test_adopt_orphan_target_behind_terminal_newest_continues_adoption(
        self,
    ) -> None:
        """The forward arm preserves the writer's boundary contract: behind a
        terminal newest boundary, --adopt naming an older still-orphan run
        keeps forwarding, and the adoption continues with the target's
        existing ownership and start-commit composition carried verbatim
        into the new linked manifest."""
        exports = self.seed_interrupted_run()
        session = self.done_session()
        seeded = Path(exports["DONE_RUN_MANIFEST"])
        marker_field = json.loads(seeded.read_text())["marker"]
        newest_id = "20991231T235959Z-newest00003"
        self.craft_manifest_file(
            seeded, newest_id, marker=marker_field, complete=True
        )
        target_id = "20260101T000000Z-orphan00001"
        self.craft_manifest_file(seeded, target_id, marker=marker_field)
        seeded.unlink()  # the crafted finalized record is the newest manifest
        target_path = session / f"run-manifest-{target_id}.json"
        target = json.loads(target_path.read_text())
        target_bytes = target_path.read_bytes()
        newest_path = session / f"run-manifest-{newest_id}.json"
        newest_bytes = newest_path.read_bytes()
        new_rel = self.create_post_setup_review()
        proc = self.run_setup(
            "--adopt", target_id, "--owned-review", new_rel,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        # the forward arm routed the orphan target to the writer, which
        # adopted it: the terminal newest record is named and untouched
        # (the routing note rides stderr beside the other status lines)
        self.assertIn(
            "is not the classified boundary and is forwarded", proc.stderr
        )
        self.assertNotIn("is not the classified boundary and is forwarded", proc.stdout)
        self.assertEqual(newest_path.read_bytes(), newest_bytes)
        self.assertEqual(target_path.read_bytes(), target_bytes)
        reexports = self.eval_exports(proc.stdout)
        adopted = json.loads(Path(reexports["DONE_RUN_MANIFEST"]).read_text())
        self.assertEqual(adopted["adopted_from"], target_id)
        self.assertEqual(adopted["start_commit"], target["start_commit"])
        self.assertEqual(adopted["owned_paths"], target["owned_paths"])
        self.assertEqual(
            adopted["owned_plan_paths"], target["owned_plan_paths"]
        )
        self.assertEqual(
            adopted["owned_review_paths"],
            [new_rel] + target["owned_review_paths"],
        )
        self.assertEqual(
            adopted["foreign_review_paths"], target["foreign_review_paths"]
        )
        self.assertIn(f"export DONE_RUN_ID={adopted['run_id']}", proc.stdout)

    def test_adopt_corrupt_boundary_fails_closed(self) -> None:
        exports = self.seed_interrupted_run()
        manifest = Path(exports["DONE_RUN_MANIFEST"])
        manifest.write_text("{ not json\n")
        before_names = self.session_names()
        proc = self.run_setup("--adopt", exports["DONE_RUN_ID"])
        self.assertEqual(proc.returncode, 2)
        self.assertIn("unparseable", proc.stderr)
        self.assertIn("fail-closed", proc.stderr)
        self.assertEqual(self.session_names(), before_names)

    def test_writer_rejected_adopt_target_leaves_no_marker_or_manifest(self) -> None:
        # No partial boundary: the fresh boundary path forwards --adopt to the
        # writer, whose own validation refuses the unknown target; the wrapper
        # then removes the marker it just wrote and no manifest lands.
        self.init_fixture_repo()
        (self.fixture / "seed.txt").write_text("seed\nwork\n")
        proc = self.run_setup(
            "--adopt", "20991231T235959Z-ghost000000", "--owned-path", "seed.txt",
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("cannot adopt 20991231T235959Z-ghost000000", proc.stderr)
        self.assertIn("the writer refused", proc.stderr)
        session = self.done_session()
        self.assertEqual(list(session.glob("run-start-*")), [])
        self.assertEqual(list(session.glob("run-manifest-*.json")), [])

    def test_from_manifest_with_ownership_options_refuses_naming_adopt(self) -> None:
        exports = self.seed_interrupted_run()
        prior_path = Path(exports["DONE_RUN_MANIFEST"])
        prior_bytes = prior_path.read_bytes()
        before_names = self.session_names()
        new_rel = self.create_post_setup_review()
        proc = self.run_setup(
            "--from-manifest", exports["DONE_RUN_ID"], "--owned-review", new_rel,
        )
        self.assertEqual(proc.returncode, 3)
        self.assertIn("exact re-entry", proc.stderr)
        self.assertIn("--owned-review", proc.stderr)
        self.assertIn(f"setup --adopt {exports['DONE_RUN_ID']}", proc.stderr)
        self.assertEqual(prior_path.read_bytes(), prior_bytes)
        self.assertEqual(self.session_names(), before_names)

    def test_from_manifest_with_adopt_refuses_as_conflicting_modes(self) -> None:
        exports = self.seed_interrupted_run()
        prior_path = Path(exports["DONE_RUN_MANIFEST"])
        prior_bytes = prior_path.read_bytes()
        before_names = self.session_names()
        proc = self.run_setup(
            "--from-manifest", exports["DONE_RUN_ID"],
            "--adopt", exports["DONE_RUN_ID"],
        )
        self.assertEqual(proc.returncode, 3)
        self.assertIn("conflicting modes", proc.stderr)
        self.assertIn(f"setup --adopt {exports['DONE_RUN_ID']}", proc.stderr)
        self.assertEqual(prior_path.read_bytes(), prior_bytes)
        self.assertEqual(self.session_names(), before_names)

    def test_from_manifest_exact_reentry_changes_no_claims(self) -> None:
        exports = self.seed_interrupted_run()
        self.create_post_setup_review()  # on disk; re-entry must ignore it
        manifest = Path(exports["DONE_RUN_MANIFEST"])
        before = manifest.read_bytes()
        second = self.run_setup("--from-manifest", exports["DONE_RUN_ID"])
        self.assertEqual(second.returncode, 0, second.stderr)
        reexports = self.eval_exports(second.stdout)
        self.assertEqual(reexports["DONE_RUN_ID"], exports["DONE_RUN_ID"])
        self.assertEqual(
            Path(reexports["DONE_RUN_MANIFEST"]).resolve(), manifest.resolve()
        )
        self.assertEqual(manifest.read_bytes(), before)
        self.assertEqual(
            len(list(self.done_session().glob("run-manifest-*.json"))), 1
        )

    def test_terminal_newest_mismatched_adopt_forwards_to_writer(self) -> None:
        """Given a terminal newest classified boundary and --adopt naming a
        different id, expects an explicit routing note (the classified verdict
        plus the writer-validation forwarding, no silent fall-through), the
        writer's own cannot-adopt refusal surfaced, and zero surviving
        markers and manifests beyond the prior boundary after the rollback."""
        exports = self.seed_interrupted_run()
        manifest = Path(exports["DONE_RUN_MANIFEST"])
        record = json.loads(manifest.read_text())
        record["complete"] = True
        manifest.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        session = self.done_session()
        before_manifests = sorted(session.glob("run-manifest-*.json"))
        self.assertEqual(len(before_manifests), 1)
        proc = self.run_setup(
            "--adopt", "20991231T235959Z-bogus000000",
            "--owned-path", "seed.txt",
        )
        self.assertEqual(proc.returncode, 1)
        combined = proc.stdout + proc.stderr
        # the routing note names the classified verdict and the forwarding
        self.assertIn("is finalized (closed boundary)", combined)
        self.assertIn(
            "--adopt 20991231T235959Z-bogus000000 is not the classified "
            "boundary and is forwarded to the writer's own adoption "
            "validations",
            combined,
        )
        # the writer's own refusal surfaces through the wrapper's fail-partial
        self.assertIn("cannot adopt 20991231T235959Z-bogus000000", proc.stderr)
        self.assertIn("the writer refused", proc.stderr)
        # rollback: only the prior boundary survives, no new marker or manifest
        self.assertEqual(
            sorted(session.glob("run-manifest-*.json")), before_manifests
        )
        self.assertEqual(
            [p.name for p in session.glob("run-start-*")],
            [Path(exports["DONE_RUN_MARKER"]).name],
        )

    def test_from_manifest_reentry_ignores_inherited_wm_args(self) -> None:
        """Given WM_ARGS inherited from the environment, exact re-entry still
        succeeds: the runner's mixed-input probe reads its own function-local
        array, never the caller's environment."""
        exports = self.seed_interrupted_run()
        manifest = Path(exports["DONE_RUN_MANIFEST"])
        before = manifest.read_bytes()
        proc = self.run_setup(
            "--from-manifest", exports["DONE_RUN_ID"],
            env_extra={"WM_ARGS": "( --owned-review /tmp/injected.md )"},
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        reexports = self.eval_exports(proc.stdout)
        self.assertEqual(reexports["DONE_RUN_ID"], exports["DONE_RUN_ID"])
        self.assertEqual(manifest.read_bytes(), before)
        self.assertEqual(
            len(list(self.done_session().glob("run-manifest-*.json"))), 1
        )

    def test_empty_adopt_operand_refuses_at_parse_time(self) -> None:
        """`setup --adopt ""` refuses at the parse loop (exit 3, the
        unknown-argument refusal class, the empty operand named) instead of
        silently degrading to a fresh boundary; nothing durable changes."""
        exports = self.seed_interrupted_run()
        prior_path = Path(exports["DONE_RUN_MANIFEST"])
        prior_bytes = prior_path.read_bytes()
        before_names = self.session_names()
        proc = self.run_setup("--adopt", "")
        self.assertEqual(proc.returncode, 3)
        self.assertIn("--adopt requires a run-id operand", proc.stderr)
        self.assertIn("empty operand", proc.stderr)
        self.assertEqual(prior_path.read_bytes(), prior_bytes)
        self.assertEqual(self.session_names(), before_names)

    def test_empty_from_manifest_operand_refuses_at_parse_time(self) -> None:
        """`setup --from-manifest ""` refuses at the parse loop (exit 3, the
        same empty-operand class as --adopt) instead of silently degrading to
        a fresh boundary; nothing durable changes."""
        exports = self.seed_interrupted_run()
        prior_path = Path(exports["DONE_RUN_MANIFEST"])
        prior_bytes = prior_path.read_bytes()
        before_names = self.session_names()
        proc = self.run_setup("--from-manifest", "")
        self.assertEqual(proc.returncode, 3)
        self.assertIn(
            "--from-manifest requires a run-id operand", proc.stderr
        )
        self.assertIn("empty operand", proc.stderr)
        self.assertEqual(prior_path.read_bytes(), prior_bytes)
        self.assertEqual(self.session_names(), before_names)

    def test_adopt_ignores_inherited_adopt_args(self) -> None:
        """Given ADOPT_ARGS inherited from the environment, the classified
        orphan still adopts cleanly: the runner forwards only its own parsed
        --adopt target, never the caller's environment (the ADOPT_ARGS twin
        of the WM_ARGS inheritance witness)."""
        exports = self.seed_interrupted_run()
        proc = self.run_setup(
            "--adopt", exports["DONE_RUN_ID"],
            env_extra={
                "ADOPT_ARGS": "( --adopt 20991231T235959Z-ghost000000 )",
            },
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        reexports = self.eval_exports(proc.stdout)
        adopted = json.loads(Path(reexports["DONE_RUN_MANIFEST"]).read_text())
        self.assertEqual(adopted["adopted_from"], exports["DONE_RUN_ID"])


class DoneRunCommitTest(FixtureMixin, unittest.TestCase):
    """Task 3 repository tests: the commit subcommand's collapsed Step 3."""

    def learn_receipt_setup(self) -> tuple[dict, str, Path]:
        """A fixture session with a simulated learn commit plus its receipts
        file (one same-repo sha; the cross-repo arm lives in the skip test)."""
        self.init_fixture_repo(branch="feature/PROJ-1234-done-run")
        (self.fixture / "docs" / "history" / "backlog").mkdir(parents=True)
        (self.fixture / "docs" / "history" / "backlog" / "2026-10-11-item.md").write_text(
            "# item\n"
        )
        self.git("add", "docs/history/backlog/2026-10-11-item.md")
        self.git("commit", "-qm", "learn: place backlog item")
        learn_sha = self.git("rev-parse", "HEAD").stdout.strip()
        receipts = self.tmp / "learn-receipts.txt"
        receipts.write_text(f"committed: {learn_sha} place backlog item\n")
        # session work: a tracked edit plus the project lessons corpus
        (self.fixture / "seed.txt").write_text("seed\nwork\n")
        (self.fixture / "docs" / "maintenance").mkdir(parents=True, exist_ok=True)
        (self.fixture / CORPUS_REL).write_text("# lessons\n\nplaced rule one\n")
        return {}, learn_sha, receipts

    def test_single_commit_witness_with_receipts_and_trace_order(self) -> None:
        _, learn_sha, receipts = self.learn_receipt_setup()
        setup_proc, exports = self.setup_session(
            "--owned-path", "seed.txt", "--owned-path", CORPUS_REL,
        )
        count_before = self.commit_count()
        proc = self.commit_session(
            setup_proc, exports,
            "--stage", "seed.txt", "--stage", CORPUS_REL,
            "--subject", "close out the session work and lessons",
            "--learn-receipts-from", str(receipts),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        # exactly one landing commit beyond the learn commit
        self.assertEqual(self.commit_count(), count_before + 1)
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        shown = self.git("show", "--name-only", "--format=", landing).stdout
        self.assertIn("seed.txt", shown)
        self.assertIn(CORPUS_REL, shown)
        message = self.git("log", "-1", "--format=%B", landing).stdout
        self.assertIn("[PROJ-1234]", message.splitlines()[0])
        self.assertNotIn("Co-Authored-By", message)
        # the owned-commits ledger carries the receipt line and the fused
        # landing sha, in order
        ledger = self.done_session() / (
            f"owned-commits-{exports['DONE_RUN_ID']}.txt"
        )
        self.assertEqual(
            ledger.read_text().splitlines(), [learn_sha, landing],
        )
        # exactly one landing sweep, one sync, one landing commit; the sweep
        # precedes the sync and the sync precedes the landing commit
        stages = self.trace_stages(self.commit_env() | exports)
        self.assertEqual(stages.count("landing-sweep"), 1)
        self.assertEqual(stages.count("docs-sync"), 1)
        self.assertEqual(stages.count("landing-commit"), 1)
        self.assertLess(stages.index("landing-sweep"), stages.index("docs-sync"))
        self.assertLess(stages.index("docs-sync"), stages.index("landing-commit"))
        # the sync's own runner-owned lock span ran (merge-acquire traced)
        sync_trace = Path(self.commit_env()["DOCS_SYNC_TRACE_FILE"])
        self.assertIn("merge-acquire", sync_trace.read_text())
        # the corpus audit answered with the out-of-scope note
        self.assertIn("company master out of scope", proc.stdout)
        # base-branch immutability is a warning line, never a refusal
        self.assertIn("base-branch immutability", proc.stdout + proc.stderr)

    def test_receipt_skip_arm_skips_unresolvable_sha(self) -> None:
        _, learn_sha, _ = self.learn_receipt_setup()
        receipts = self.tmp / "learn-receipts.txt"
        receipts.write_text(
            f"committed: {learn_sha} place backlog item\n"
            "committed: 0123456789abcdef0123456789abcdef01234567 cross-repo sha\n"
        )
        setup_proc, exports = self.setup_session(
            "--owned-path", "seed.txt", "--owned-path", CORPUS_REL,
        )
        proc = self.commit_session(
            setup_proc, exports,
            "--stage", "seed.txt", "--stage", CORPUS_REL,
            "--subject", "close out the session work and lessons",
            "--learn-receipts-from", str(receipts),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("0123456789abcdef0123456789abcdef01234567", proc.stdout)
        self.assertIn("not resolvable", proc.stdout)
        ledger = self.done_session() / (
            f"owned-commits-{exports['DONE_RUN_ID']}.txt"
        )
        lines = ledger.read_text().splitlines()
        self.assertIn(learn_sha, lines)
        self.assertNotIn("0123456789abcdef0123456789abcdef01234567", lines)

    def test_sync_wiring_pass_and_lock_span(self) -> None:
        self.init_fixture_repo()
        (self.fixture / "seed.txt").write_text("seed\nwork\n")
        setup_proc, exports = self.setup_session("--owned-path", "seed.txt")
        proc = self.commit_session(
            setup_proc, exports,
            "--stage", "seed.txt", "--subject", "land the session work",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        combined = proc.stdout + proc.stderr
        self.assertIn("docs-branch: sync complete", combined)
        self.assertIn("merge-lock: held", combined)
        stages = self.trace_stages(self.commit_env() | exports)
        self.assertLess(stages.index("landing-sweep"), stages.index("docs-sync"))
        self.assertLess(stages.index("docs-sync"), stages.index("landing-commit"))
        sync_trace = Path(self.commit_env()["DOCS_SYNC_TRACE_FILE"]).read_text()
        self.assertIn("merge-acquire", sync_trace)

    def test_per_task_boundary_skips_docs_sync_keeps_migration(self) -> None:
        """[class: REPOSITORY_TEST] Given a per-task commit in an ad-hoc
        worktree whose run owns exactly one plan, the docs-branch sync is
        skipped, the review-artifact migration still runs against the plan's
        canonical Phase 0 baseline (a post-baseline review record transfers
        to the primary checkout, and no run-ID baseline is captured at commit
        time), and one trace line names the skipped leg; the landing commit
        still lands. The fixture also pins the producer/consumer path
        agreement end to end: the plan file is date-prefixed and the
        baseline sits at the date-stripped canonical slug dir, the path the
        plans Phase 0.1 producer is instructed to write and the
        ``plan_session_slug()`` consumer resolves (the execute-plan Step 0.4
        canonical session-slug rule), so a producer that keeps the
        date-prefixed stem fails this lookup."""
        self.init_fixture_repo()
        plans = self.fixture / "docs" / "history" / "plans"
        plans.mkdir(parents=True)
        plan_rel = "docs/history/plans/2026-10-18-per-task-example.md"
        (self.fixture / plan_rel).write_text("# plan\n")
        self.git("add", plan_rel)
        self.git("commit", "-qm", "plans: fixture owned plan")
        (self.fixture / "seed.txt").write_text("seed\nwork\n")
        primary_head = self.git("rev-parse", "HEAD").stdout.strip()
        worktree = self.tmp / "per-task-wt"
        self.git("worktree", "add", "-b", "per-task-wt-branch", str(worktree))
        try:
            # the run's declared work lives in the worktree
            (worktree / "seed.txt").write_text("seed\nwork\nper-task edit\n")
            # the run's Step 0 setup precedes every run artifact: a review
            # record already on disk is neither owned nor foreign and the
            # write-manifest claim gate refuses it
            wt_env = self.runner_env()
            wt_env["DONE_SWEEP_REPO_ROOT"] = str(worktree)
            setup = subprocess.run(
                ["bash", str(RUNNER), "setup", "--owned-path", "seed.txt",
                 "--owned-plan", plan_rel],
                cwd=str(worktree), env=wt_env,
                capture_output=True, text=True, timeout=300,
            )
            self.assertEqual(setup.returncode, 0, setup.stderr)
            # Phase 0: the run captures its closeout baseline before any
            # transferable run artifact exists.
            slug_dir = worktree / "docs" / "tmp" / "execute-plan" / "per-task-example"
            slug_dir.mkdir(parents=True)
            capture = subprocess.run(
                [sys.executable, str(CLOSEOUT_MIGRATE), "capture",
                 "--out", str(slug_dir / "closeout-baseline.json")],
                cwd=str(worktree), capture_output=True, text=True, timeout=120,
            )
            self.assertEqual(capture.returncode, 0, capture.stderr)
            # the run then creates a review artifact the baseline predates
            reviews = worktree / ".ai-playbook" / "reviews"
            reviews.mkdir(parents=True, exist_ok=True)
            record = reviews / "2026-10-18-per-task-example-code-review-r1.md"
            record.write_text("# review record\n", encoding="utf-8")
            # the done-lock session fence is done-lock's status witness, not
            # fixture state under test: remove it so the commit's foreign-dirt
            # gate sees only the declared work
            fence = worktree / ".ai-playbook" / "done-lock.session"
            if fence.exists():
                fence.unlink()
            env = self.commit_env()
            env["DONE_SWEEP_REPO_ROOT"] = str(worktree)
            env.update(self.eval_exports(setup.stdout))
            run_id = self.eval_exports(setup.stdout)["DONE_RUN_ID"]
            proc = subprocess.run(
                ["bash", str(RUNNER), "commit", "--stage", "seed.txt",
                 "--subject", "per-task landing",
                 "--boundary-class", "per-task"],
                cwd=str(worktree), env=env,
                capture_output=True, text=True, timeout=300,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            combined = proc.stdout + proc.stderr
            # the sync skipped: no sync completion line, no sync lock span
            self.assertNotIn("docs-branch: sync complete", combined)
            sync_trace = Path(env["DOCS_SYNC_TRACE_FILE"])
            if sync_trace.exists():
                self.assertNotIn("merge-acquire", sync_trace.read_text())
            # the skip is visible: one trace line naming the skipped leg
            self.assertIn("per-task boundary: skipping the docs-branch sync", combined)
            # the migration kept its position on the reused pre-work baseline:
            # the post-baseline review record transferred to the primary
            transferred = self.fixture / ".ai-playbook" / "reviews" / record.name
            self.assertTrue(transferred.is_file(), combined)
            self.assertEqual(transferred.read_text(encoding="utf-8"), "# review record\n")
            # the commit never captured a late run-ID baseline
            wt_session = worktree / "docs" / "tmp" / "done-session"
            self.assertFalse(
                (wt_session / f"worktree-migrate-baseline-{run_id}.json").exists(),
                "commit captured a late baseline",
            )
            # the migration manifest records the transfer verified, at the
            # primary checkout's canonical plan-slug destination
            self.assertEqual(
                list(wt_session.glob("worktree-migrate-manifest-*.json")), [],
                "one-owned-plan migration wrote the run-id manifest worktree-side",
            )
            primary_manifest = (
                self.fixture / "docs" / "tmp" / "execute-plan"
                / "per-task-example" / "closeout-migration.json"
            )
            self.assertTrue(primary_manifest.is_file(), combined)
            data = json.loads(primary_manifest.read_text(encoding="utf-8"))
            self.assertTrue(data.get("branch"), "migration manifest lost the branch record")
            migrated = {entry["source"] for entry in data["migrated"]}
            self.assertIn(f".ai-playbook/reviews/{record.name}", migrated)
            for entry in data["migrated"]:
                self.assertTrue(entry["verified"])
            # the landing commit landed on the worktree branch
            self.assertNotEqual(
                self.git("rev-parse", "HEAD", repo=worktree).stdout.strip(),
                primary_head,
            )
        finally:
            self.git("worktree", "remove", "--force", str(worktree), check=False)
            self.git("branch", "-D", "per-task-wt-branch", check=False)

    def test_unset_boundary_class_keeps_sync(self) -> None:
        """[class: REPOSITORY_TEST] Safety witness: given an unset class, the
        runner's composed stages match today's behavior exactly (the default
        final-closeout keeps the docs-branch sync and its lock span)."""
        self.init_fixture_repo()
        (self.fixture / "seed.txt").write_text("seed\nwork\n")
        setup_proc, exports = self.setup_session("--owned-path", "seed.txt")
        proc = self.commit_session(
            setup_proc, exports,
            "--stage", "seed.txt", "--subject", "final closeout landing",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        combined = proc.stdout + proc.stderr
        self.assertIn("docs-branch: sync complete", combined)
        stages = self.trace_stages(self.commit_env() | exports)
        self.assertEqual(stages.count("docs-sync"), 1)
        self.assertNotIn("skipping the docs-branch sync", combined)

    def test_guard_refuses_staged_foreign_path(self) -> None:
        self.init_fixture_repo()
        (self.fixture / "seed.txt").write_text("foreign baseline dirt\n")
        (self.fixture / "new.txt").write_text("session work\n")
        setup_proc, exports = self.setup_session("--owned-path", "new.txt")
        count_before = self.commit_count()
        proc = self.commit_session(
            setup_proc, exports,
            "--stage", "new.txt", "--stage", "seed.txt",
            "--subject", "try to land foreign dirt",
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("foreign-staging gate failed", proc.stdout + proc.stderr)
        self.assertEqual(self.commit_count(), count_before)

    def test_guard_refuses_reverse_squash_signature(self) -> None:
        self.init_fixture_repo()
        reviews = self.fixture / ".ai-playbook" / "reviews"
        reviews.mkdir(parents=True)
        receipt = reviews / "2026-01-01-foo-plan-review-bar-exec-r1.md"
        receipt.write_text("# exec receipt r1\n")
        self.git("add", str(receipt.relative_to(self.fixture)))
        setup_proc, exports = self.setup_session(
            "--owned-path", str(receipt.relative_to(self.fixture)),
        )
        count_before = self.commit_count()
        proc = self.commit_session(
            setup_proc, exports,
            "--stage", str(receipt.relative_to(self.fixture)),
            "--subject", "land a reviews-home egress",
        )
        self.assertNotEqual(proc.returncode, 0)
        combined = proc.stdout + proc.stderr
        self.assertIn("reverse-squash", combined.lower())
        self.assertIn("egress", combined.lower())
        self.assertEqual(self.commit_count(), count_before)
        stages = self.trace_stages(self.commit_env() | exports)
        self.assertEqual(stages[-1], "reverse-squash-check-staged")

    def test_guard_refuses_dirt_regression(self) -> None:
        self.init_fixture_repo()
        (self.fixture / "work.txt").write_text("a\nb\n")
        self.git("add", "work.txt")
        self.git("commit", "-qm", "base work content")
        seed_sha = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("update-ref", "refs/remotes/origin/main", seed_sha)
        self.git("symbolic-ref", "refs/remotes/origin/HEAD",
                 "refs/remotes/origin/main")
        (self.fixture / "work.txt").write_text("a\nb\nHEADGAINED\n")
        self.git("add", "work.txt")
        self.git("commit", "-qm", "gain head content")
        # every worktree line exists at the merge base while a HEAD-gained
        # line is removed, and the blob matches no ancestor vintage
        (self.fixture / "work.txt").write_text("b\nb\n")
        setup_proc, exports = self.setup_session("--owned-path", "work.txt")
        count_before = self.commit_count()
        proc = self.commit_session(
            setup_proc, exports,
            "--stage", "work.txt", "--subject", "land a dirt regression",
        )
        self.assertNotEqual(proc.returncode, 0)
        combined = proc.stdout + proc.stderr
        self.assertIn("dirt REGRESSION", combined)
        self.assertEqual(self.commit_count(), count_before)
        stages = self.trace_stages(self.commit_env() | exports)
        self.assertEqual(stages[-1], "dirt-regression-guard")

    def test_guard_refuses_cached_diff_leaked_revert(self) -> None:
        self.init_fixture_repo()
        (self.fixture / "work.txt").write_text("a\nold\n")
        self.git("add", "work.txt")
        self.git("commit", "-qm", "base work content")
        (self.fixture / "work.txt").write_text("a\nnew\n")
        self.git("add", "work.txt")
        self.git("commit", "-qm", "gain head content")
        # the index+worktree state equals the ancestor vintage: a leaked revert
        (self.fixture / "work.txt").write_text("a\nold\n")
        self.git("add", "work.txt")
        setup_proc, exports = self.setup_session("--owned-path", "work.txt")
        count_before = self.commit_count()
        proc = self.commit_session(
            setup_proc, exports,
            "--stage", "work.txt", "--subject", "land a leaked revert",
        )
        self.assertNotEqual(proc.returncode, 0)
        combined = proc.stdout + proc.stderr
        self.assertIn("leaked revert", combined)
        self.assertEqual(self.commit_count(), count_before)
        stages = self.trace_stages(self.commit_env() | exports)
        self.assertEqual(stages[-1], "cached-diff-guard")

    def test_guard_refuses_staged_path_outside_owned_set(self) -> None:
        self.init_fixture_repo()
        (self.fixture / "stranger.txt").write_text("pre-staged stranger\n")
        self.git("add", "stranger.txt")
        (self.fixture / "new.txt").write_text("session work\n")
        setup_proc, exports = self.setup_session("--owned-path", "new.txt")
        count_before = self.commit_count()
        proc = self.commit_session(
            setup_proc, exports,
            "--stage", "new.txt", "--subject", "sweep a stranger into the landing",
        )
        self.assertNotEqual(proc.returncode, 0)
        combined = proc.stdout + proc.stderr
        self.assertIn("stranger.txt", combined)
        self.assertIn("OUTCOME: fail", combined)
        self.assertEqual(self.commit_count(), count_before)
        stages = self.trace_stages(self.commit_env() | exports)
        self.assertEqual(stages[-1], "staged-scope-guard")

    def test_formatting_candidates_listed_without_revert(self) -> None:
        self.init_fixture_repo()
        (self.fixture / "fmt.txt").write_text("a\n")
        self.git("add", "fmt.txt")
        self.git("commit", "-qm", "add fmt")
        (self.fixture / "fmt.txt").write_text("a  \n")
        (self.fixture / "new.txt").write_text("session work\n")
        setup_proc, exports = self.setup_session(
            "--owned-path", "new.txt", "--owned-path", "fmt.txt",
        )
        proc = self.commit_session(
            setup_proc, exports,
            "--stage", "new.txt", "--stage", "fmt.txt",
            "--subject", "land work beside formatting noise",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("formatting-only", proc.stdout)
        self.assertIn("fmt.txt", proc.stdout)
        # no revert without the confirmation flag: the whitespace-only diff is
        # still in the worktree relative to HEAD
        self.assertIn("a  \n", self.git("show", "HEAD:fmt.txt").stdout)

    def test_formatting_revert_with_confirmation_flag(self) -> None:
        self.init_fixture_repo()
        (self.fixture / "fmt.txt").write_text("a\n")
        self.git("add", "fmt.txt")
        self.git("commit", "-qm", "add fmt")
        (self.fixture / "fmt.txt").write_text("a  \n")
        (self.fixture / "new.txt").write_text("session work\n")
        setup_proc, exports = self.setup_session(
            "--owned-path", "new.txt", "--owned-path", "fmt.txt",
        )
        proc = self.commit_session(
            setup_proc, exports,
            "--stage", "new.txt", "--stage", "fmt.txt",
            "--revert-formatting", "fmt.txt",
            "--subject", "land work after reverting formatting noise",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("fmt.txt", proc.stdout)
        shown = self.git("show", "--name-only", "--format=", "HEAD").stdout
        self.assertNotIn("fmt.txt", shown)
        self.assertIn("new.txt", shown)

    def test_side_repo_walk_reports_dirty_and_commits_confirmed_repo(self) -> None:
        self.init_fixture_repo()
        side = self.tmp / "side-skills"
        side.mkdir()
        subprocess.run(["git", "init", "-q", str(side)], check=True)
        self.git("config", "user.email", "t@example.test", repo=side)
        self.git("config", "user.name", "t", repo=side)
        (side / "README.md").write_text("side repo\n")
        self.git("add", ".", repo=side)
        self.git("commit", "-qm", "seed side", repo=side)
        (side / "new-skill.md").write_text("# new skill\n")
        self.write_user_facts(("skills_repo_path", str(side)))
        (self.fixture / "new.txt").write_text("session work\n")
        setup_proc, exports = self.setup_session("--owned-path", "new.txt")
        proc = self.commit_session(
            setup_proc, exports,
            "--stage", "new.txt", "--subject", "land main work",
            "--side-commit", str(side),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        # the walk reported the side repo's dirty path
        self.assertIn("new-skill.md", proc.stdout)
        # exactly one confirmed commit action in the side repo
        side_count = int(
            self.git("rev-list", "--count", "HEAD", repo=side).stdout.strip()
        )
        self.assertEqual(side_count, 2)
        shown = self.git("show", "--name-only", "--format=", "HEAD", repo=side).stdout
        self.assertIn("new-skill.md", shown)
        # the sensitive-data scan re-ran over the staged side-repo set
        self.assertIn("OUTCOME: pass", proc.stdout)


class DoneRunDescriptionLengthCatchTest(FixtureMixin, unittest.TestCase):
    """Plan 2026-10-24-description-length-gate-catch-promotion, Task 1: the
    commit subcommand's pre-refusal catch recording: a structured sweep
    result of gate=description-length rc=1 appends its deduplicated catch
    row to the repo ledger before the commit refuses; rc=2/rc=3 refuse
    without a catch; an append failure refuses naming the unrecorded catch;
    the fixed retry declares the ledger JSON and lands the catch."""

    OVER_SKILL = "agents/skills/over/SKILL.md"
    LEDGER_REL = "scripts/gate_liveness_ledger.json"

    def seed_ledger(self, payload: str | None = None) -> None:
        scripts = self.fixture / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        if payload is None:
            payload = json.dumps(
                {
                    "schema": 1,
                    "window": {"started": "2026-10-05"},
                    "guards": {},
                }
            )
        (scripts / "gate_liveness_ledger.json").write_text(payload)

    def write_over_skill(self, length: int = 1025) -> None:
        path = self.fixture / self.OVER_SKILL
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "---\nname: over\ndescription: " + "x" * length + "\n---\n\nbody\n"
        )

    def ledger_rows(self) -> list[dict]:
        data = json.loads((self.fixture / self.LEDGER_REL).read_text())
        return data["guards"].get("description-length", {}).get("rows", [])

    def refusing_session(self) -> tuple[dict, str]:
        """A fixture session whose declared over-cap skill refuses the
        landing sweep at description-length rc=1 (the modeled catch class);
        returns (exports, run_id)."""
        self.init_fixture_repo(branch="feature/PROJ-1234-done-run")
        self.write_over_skill()
        self.seed_ledger()
        setup_proc, exports = self.setup_session(
            "--owned-path", self.OVER_SKILL, "--owned-path", self.LEDGER_REL,
        )
        return exports, exports["DONE_RUN_ID"]

    def test_over_cap_refusal_records_catch_before_refusing(self) -> None:
        exports, run_id = self.refusing_session()
        count_before = self.commit_count()
        proc = self.commit_session(
            None, exports,
            "--stage", self.OVER_SKILL,
            "--subject", "land the over-cap skill",
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(
            self.commit_count(), count_before, "nothing may land past the gate"
        )
        combined = proc.stdout + proc.stderr
        self.assertIn("the landing sweep refused the staged set (rc=1)", combined)
        # The refusal names the ledger path as the next retry's required
        # declaration and identifies the recorded catch.
        self.assertIn("scripts/gate_liveness_ledger.json", combined)
        self.assertIn("recorded in scripts/gate_liveness_ledger.json", combined)
        rows = self.ledger_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["kind"], "catch")
        self.assertIn(f"run_id={run_id}", rows[0]["note"])

    def test_repeat_refusal_does_not_duplicate_the_catch(self) -> None:
        exports, run_id = self.refusing_session()
        first = self.commit_session(
            None, exports,
            "--stage", self.OVER_SKILL,
            "--subject", "land the over-cap skill",
        )
        self.assertNotEqual(first.returncode, 0)
        self.assertEqual(len(self.ledger_rows()), 1)
        second = self.commit_session(
            None, exports,
            "--stage", self.OVER_SKILL,
            "--subject", "land the over-cap skill",
        )
        self.assertNotEqual(second.returncode, 0)
        rows = self.ledger_rows()
        self.assertEqual(
            len(rows), 1, "the sequential retry must not duplicate the catch"
        )
        self.assertIn(f"run_id={run_id}", rows[0]["note"])
        self.assertIn(
            "no row appended: catch already recorded", second.stdout + second.stderr
        )

    def test_fixed_retry_declares_ledger_and_lands_the_catch(self) -> None:
        exports, run_id = self.refusing_session()
        refused = self.commit_session(
            None, exports,
            "--stage", self.OVER_SKILL,
            "--subject", "land the over-cap skill",
        )
        self.assertNotEqual(refused.returncode, 0)
        # Fix the description and declare the ledger JSON beside it: the
        # successful retry lands the recorded catch with the fix.
        (self.fixture / self.OVER_SKILL).write_text(
            "---\nname: over\ndescription: short and fixed\n---\n\nbody\n"
        )
        count_before = self.commit_count()
        proc = self.commit_session(
            None, exports,
            "--stage", self.OVER_SKILL,
            "--stage", self.LEDGER_REL,
            "--subject", "fix the over-cap skill description and land its catch",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.commit_count(), count_before + 1)
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        shown = self.git("show", "--name-only", "--format=", landing).stdout
        self.assertIn(self.OVER_SKILL, shown)
        self.assertIn(self.LEDGER_REL, shown)
        landed_ledger = self.git(
            "show", f"{landing}:{self.LEDGER_REL}"
        ).stdout
        self.assertIn(f"run_id={run_id}", landed_ledger)
        rows = self.ledger_rows()
        self.assertEqual(
            len(rows), 1, "exactly one catch row for the refused run"
        )
        self.assertEqual(rows[0]["kind"], "catch")

    def test_classified_tool_error_refusal_records_no_catch(self) -> None:
        exports, _run_id = self.refusing_session()
        for exit_code in (2, 3, 7):
            stub = self.tmp / f"checker-exit{exit_code}.py"
            stub.write_text(
                "#!/usr/bin/env python3\n"
                "import sys\n"
                "print('stub checker diagnostic')\n"
                f"sys.exit({exit_code})\n"
            )
            env = self.commit_env()
            env.update(exports)
            env["DESCRIPTION_LENGTH_CHECK_SCRIPT"] = str(stub)
            proc = self.run_commit(
                "--stage", self.OVER_SKILL,
                "--subject", "land the over-cap skill",
                env=env,
            )
            self.assertNotEqual(proc.returncode, 0, exit_code)
            combined = proc.stdout + proc.stderr
            self.assertIn(
                "the landing sweep refused the staged set (rc=3)", combined,
                f"checker exit {exit_code} must classify as tool error rc=3",
            )
            self.assertNotIn(
                "recorded in scripts/gate_liveness_ledger.json", combined,
                "a tool-error refusal records no catch",
            )
            self.assertEqual(
                self.ledger_rows(), [],
                f"checker exit {exit_code} must not append a catch row",
            )

    def test_missing_ledger_helper_refuses_naming_the_unrecorded_catch(self) -> None:
        exports, _run_id = self.refusing_session()
        count_before = self.commit_count()
        # A private runner copy whose resolve_helper sees a directory with
        # every helper symlinked in EXCEPT gate_liveness_ledger.py, so the
        # catch append has no checker to call and the append cannot happen.
        runner_dir = self.tmp / "runner-no-ledger"
        runner_dir.mkdir()
        shutil.copy2(RUNNER, runner_dir / "done_run.sh")
        for helper in REPO_ROOT.joinpath("scripts").iterdir():
            if (helper.suffix in (".py", ".sh", ".json")
                    and helper.name not in (
                        "done_run.sh", "gate_liveness_ledger.py",
                        "gate_liveness_ledger.json",
                    )
                    and not helper.name.startswith("test_")):
                os.symlink(helper, runner_dir / helper.name)
        env = self.commit_env()
        env.update(exports)
        # resolve_helper falls back to $HOME/.ai-playbook/scripts, where the
        # deployed gate_liveness_ledger.py lives; an empty temp home makes
        # the helper unresolvable from both arms.
        empty_home = self.tmp / "empty-home"
        (empty_home / ".ai-playbook").mkdir(parents=True)
        env["HOME"] = str(empty_home)
        proc = subprocess.run(
            ["bash", str(runner_dir / "done_run.sh"), "commit",
             "--stage", self.OVER_SKILL,
             "--subject", "land the over-cap skill"],
            cwd=str(self.fixture), env=env, capture_output=True, text=True,
            timeout=300,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(
            self.commit_count(), count_before,
            "an unrecordable catch leaves the landing refused",
        )
        combined = proc.stdout + proc.stderr
        self.assertIn("no gate_liveness_ledger.py resolved", combined)
        self.assertIn("could not be recorded", combined)

    def test_ledger_append_failure_refuses_naming_the_unrecorded_catch(self) -> None:
        exports, _run_id = self.refusing_session()
        count_before = self.commit_count()
        self.seed_ledger(payload="{not json")  # corrupt ledger: the append fails
        proc = self.commit_session(
            None, exports,
            "--stage", self.OVER_SKILL,
            "--subject", "land the over-cap skill",
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(
            self.commit_count(), count_before,
            "an unrecordable catch leaves the landing refused",
        )
        combined = proc.stdout + proc.stderr
        self.assertIn("could not be recorded", combined)
        self.assertIn("scripts/gate_liveness_ledger.json", combined)


class DoneRunGuardFiringCommitTest(FixtureMixin, unittest.TestCase):
    """Task 2 witnesses (plan docs/history/plans/2026-10-24-done-run-lock-
    span-and-append-ordering.md): the commit subcommand's repeated
    --guard-firing writes accepted rows BEFORE the declared-path staging and
    the landing sweep, stages the ledger path so the bytes ride the landing
    commit exactly once, and keeps every advisory outcome nonblocking,
    including a pre-write hygiene hit that leaves the canonical bytes
    unchanged."""

    LEDGER_REL = "scripts/gate_liveness_ledger.json"

    def seed_repo(self) -> None:
        self.init_fixture_repo(branch="feature/PROJ-1234-done-run")
        ledger = self.fixture / "scripts" / "gate_liveness_ledger.json"
        ledger.parent.mkdir(parents=True, exist_ok=True)
        ledger.write_text(json.dumps(
            {"schema": 1, "window": {"started": "2026-10-05"}, "guards": {}}
        ))
        self.git("add", self.LEDGER_REL)
        self.git("commit", "-qm", "seed the guard-liveness ledger")

    def committed_ledger_text(self) -> str:
        return self.git("show", f"HEAD:{self.LEDGER_REL}").stdout

    def matching_rows(self, text: str, evidence: str) -> list[dict]:
        doc = json.loads(text)
        return [
            row
            for guard in doc["guards"].values()
            for row in guard["rows"]
            if row.get("evidence") == evidence
        ]

    def test_landing_row_written_before_staging_and_lands_once(self) -> None:
        self.seed_repo()
        (self.fixture / "work.txt").write_text("session work\n")
        setup_proc, exports = self.setup_session("--owned-path", "work.txt")
        run_id = exports["DONE_RUN_ID"]
        count_before = self.commit_count()
        proc = self.commit_session(
            setup_proc, exports,
            "--stage", "work.txt",
            "--guard-firing", f"description-length:catch:fixture-evidence:run_id={run_id}",
            "--subject", "land work and the guard firing",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.commit_count(), count_before + 1)
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        shown = self.git("show", "--name-only", "--format=", landing).stdout
        self.assertIn("work.txt", shown)
        self.assertIn(self.LEDGER_REL, shown)
        rows = self.matching_rows(self.committed_ledger_text(), "fixture-evidence")
        self.assertEqual(len(rows), 1, "exactly one committed matching row")
        self.assertEqual(rows[0]["kind"], "catch")
        self.assertIn(f"run_id={run_id}", rows[0]["note"])
        # the row write preceded the declared-path staging and the sweep
        stages = self.trace_stages(self.commit_env() | exports)
        self.assertIn("guard-firing-appends", stages)
        self.assertLess(
            stages.index("guard-firing-appends"), stages.index("staging")
        )
        self.assertLess(
            stages.index("guard-firing-appends"), stages.index("landing-sweep")
        )

    def test_commit_hygiene_hit_skips_row_and_lands_anyway(self) -> None:
        self.seed_repo()
        (self.fixture / "work.txt").write_text("session work\n")
        setup_proc, exports = self.setup_session("--owned-path", "work.txt")
        env = self.commit_env()
        env.update(exports)
        # An active fixture deny pattern matching the row's evidence text: the
        # writer's pre-write screen skips the advisory row, the ledger bytes
        # stay unchanged, and the landing continues without them.
        patterns = Path(env["PUBLIC_HYGIENE_PATTERNS_FILE"])
        patterns.write_text("# fixture deny patterns\n\\bFORBIDDEN-EVIDENCE-TOKEN\\b\n")
        count_before = self.commit_count()
        proc = self.run_commit(
            "--stage", "work.txt",
            "--guard-firing",
            "description-length:incident:flagged FORBIDDEN-EVIDENCE-TOKEN evidence",
            "--subject", "land work with a screened-out firing",
            env=env,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.commit_count(), count_before + 1)
        combined = proc.stdout + proc.stderr
        self.assertIn("public-hygiene", combined)
        self.assertIn("advisory row is skipped", combined)
        self.assertEqual(
            (self.fixture / self.LEDGER_REL).read_text(),
            self.committed_ledger_text(),
            "a hygiene hit leaves the canonical ledger bytes unchanged",
        )
        self.assertEqual(self.matching_rows(self.committed_ledger_text(), "flagged FORBIDDEN-EVIDENCE-TOKEN evidence"), [])
        shown = self.git("show", "--name-only", "--format=", "HEAD").stdout
        self.assertIn("work.txt", shown)
        self.assertNotIn(self.LEDGER_REL, shown)


class DoneRunDeclaredStageChannelTest(FixtureMixin, unittest.TestCase):
    """Task 1 witnesses (plan
    docs/history/plans/2026-10-14-done-ownership-post-setup-learn-edits.md):
    the commit's declared set lands through its one landing sweep, and the
    carried set is proven from the refusal side by a companion run missing
    one declared member. The companion refuses at the step-6 staged-scope
    guard and pins its trace stage (plan review r3 residual: the guard, not
    the channel, owns this discrimination; Task 5's empty-declared arms own
    the channel-source cases)."""

    def test_declared_pair_passes_sweep_and_missing_member_companion_refuses_at_scope_guard(self) -> None:
        self.init_fixture_repo(branch="feature/PROJ-1234-done-run")
        (self.fixture / "a.txt").write_text("a\n")
        (self.fixture / "b.txt").write_text("b\n")
        self.git("add", "a.txt", "b.txt")
        self.git("commit", "-qm", "add the owned work files")
        setup_proc, exports = self.setup_session(
            "--owned-path", "a.txt", "--owned-path", "b.txt",
        )
        count_before = self.commit_count()
        # the learn step's product: tracked-file edits authored after the
        # setup manifest was written, both declared at commit
        (self.fixture / "a.txt").write_text("a\nlearn edit\n")
        (self.fixture / "b.txt").write_text("b\nlearn edit\n")
        first = self.commit_session(
            setup_proc, exports,
            "--stage", "a.txt", "--stage", "b.txt",
            "--subject", "land both declared learn edits",
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(self.commit_count(), count_before + 1)
        shown = self.git("show", "--name-only", "--format=", "HEAD").stdout
        self.assertIn("a.txt", shown)
        self.assertIn("b.txt", shown)
        stages = self.trace_stages(self.commit_env() | exports)
        self.assertIn("landing-sweep", stages)
        # the companion run: b.txt is staged out-of-band but missing from
        # the declared set, so the step-6 staged-scope guard refuses naming
        # the missing declared member
        (self.fixture / "a.txt").write_text("a\nlearn edit\ncompanion edit\n")
        (self.fixture / "b.txt").write_text("b\nlearn edit\ncompanion edit\n")
        self.git("add", "b.txt")
        second = self.commit_session(
            setup_proc, exports,
            "--stage", "a.txt",
            "--subject", "companion run missing one declared member",
        )
        self.assertNotEqual(second.returncode, 0)
        combined = second.stdout + second.stderr
        self.assertIn("b.txt", combined)
        self.assertIn("staged-scope guard refused the declared set", combined)
        self.assertEqual(self.commit_count(), count_before + 1)
        stages = self.trace_stages(self.commit_env() | exports)
        self.assertEqual(stages[-1], "staged-scope-guard")

    def test_gitignored_declared_path_reported_and_never_staged(self) -> None:
        self.init_fixture_repo(branch="feature/PROJ-1234-done-run")
        (self.fixture / ".gitignore").write_text(
            "docs/tmp/\n__pycache__/\nignored-dir/\n"
        )
        self.git("add", ".gitignore")
        self.git("commit", "-qm", "ignore the scratch home")
        ignored = self.fixture / "ignored-dir"
        ignored.mkdir()
        (ignored / "scratch.txt").write_text("scratch bytes\n")
        (self.fixture / "seed.txt").write_text("seed\nwork\n")
        setup_proc, exports = self.setup_session("--owned-path", "seed.txt")
        count_before = self.commit_count()
        proc = self.commit_session(
            setup_proc, exports,
            "--stage", "seed.txt", "--stage", "ignored-dir/scratch.txt",
            "--subject", "land work beside a gitignored declaration",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        combined = proc.stdout + proc.stderr
        self.assertIn("gitignored path not staged", combined)
        self.assertIn("ignored-dir/scratch.txt", combined)
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        shown = self.git("show", "--name-only", "--format=", landing).stdout
        self.assertIn("seed.txt", shown)
        self.assertNotIn("ignored-dir/scratch.txt", shown)
        # the declared gitignored path never entered the index and stays on
        # disk, so it never reaches the sweep's staged set
        self.assertEqual(
            self.git("ls-files", "--", "ignored-dir/scratch.txt").stdout, ""
        )
        self.assertTrue((ignored / "scratch.txt").is_file())


# Plan: docs/history/plans/2026-10-14-done-ownership-post-setup-learn-edits.md,
# Task 3: the manifest-resolved refusal's declared-stage remedy sentence,
# byte-identical to the lib suite's POST_LANDING_DECLARED_STAGE_REMEDY_SENTENCE
# literal (scripts/test_done_sweep_gates_lib.py).
DECLARED_STAGE_REMEDY_SENTENCE = (
    "; a live edit authored after setup (the documented learn step's "
    "product) is landed by re-running the commit with the path declared "
    "via --stage"
)
# The no-manifest refusal arm's byte-identical render for the
# closeout.md residue shape, byte-identical to the lib suite's
# POST_LANDING_NO_MANIFEST_REFUSAL_PIN (the gate message; the wrapper
# asserts the sweep summary line that carries it verbatim).
NO_MANIFEST_REFUSAL_PIN = (
    "post-landing-staging gate failed: primary checkout residue after "
    "landing (staged path(s): closeout.md); "
    "sanctioned cleanup: the land_squash.sh probe-then-reland path (run "
    "scripts/land_squash.sh probe, resolve or compose, then "
    "scripts/land_squash.sh land under the Primary land lock ownership "
    "(the primary done lock acquired before the merge lock, both held "
    "through the landing, released merge then done)); operator escape "
    "for dead residue only (done-lock.sh merge-status free AND the path "
    "is not peer-live dirt): git restore --staged --worktree -- <path> "
    "per residue path; record-only allowlist path(s) are never escapable"
)
RECORD_ONLY_CORPUS_REL = "projects/.ai-playbook/development_lessons.md"


class DoneRunUntrackDeclarationTest(FixtureMixin, unittest.TestCase):
    """Task 1 witnesses (plan
    docs/history/plans/2026-10-27-done-run-untrack-ignored-path.md): the
    explicit repeatable --untrack declaration for pre-staged index-only
    deletions of ignored paths. A valid declaration lands only the index
    deletion and keeps the local ignored copy and rule with the exact
    committed tree; each invalid path condition (absent from HEAD, still
    indexed, missing worktree copy, not ignored) refuses at the read-only
    preflight with HEAD, the index, and the working tree unchanged; an
    unchanged ignored tracked file stays outside the changed-blob refusal;
    a force-added ignored blob declared through --stage refuses at the
    preflight changed-blob scan; and two separate late-race cases exercise
    the two captured-tree invariants (a re-added untrack target; a
    force-added ignored non-target --stage path injected after preflight
    but during stage-operand processing and before tree capture) with no commit
    or ref update and the injected caller index state preserved."""

    TARGET_REL = "local-home/local.properties"

    def untrack_fixture(self, *force_tracked_ignored: str) -> None:
        """The untrack boundary: an ignored worktree file force-tracked at
        HEAD beside its ignore rule, origin/HEAD pinned at the seed so the
        branch-added deletion takes the dirt gate's input-set skip."""
        self.init_fixture_repo(branch="feature/PROJ-1-done-run")
        (self.fixture / ".gitignore").write_text(
            "docs/tmp/\n__pycache__/\nlocal-home/\n*.conf\n"
        )
        (self.fixture / "local-home").mkdir()
        (self.fixture / self.TARGET_REL).write_text("key=local\n")
        if force_tracked_ignored:
            for rel in force_tracked_ignored:
                (self.fixture / rel).write_text("tracked-ignored bytes\n")
            self.git("add", "-f", *force_tracked_ignored)
        self.git("add", "-f", self.TARGET_REL)
        self.git("add", ".gitignore")
        self.git("commit", "-qm", "track the local-only file beside its ignore rule")
        seed_sha = self.git("rev-parse", "HEAD~1").stdout.strip()
        self.git("update-ref", "refs/remotes/origin/main", seed_sha)
        self.git("symbolic-ref", "refs/remotes/origin/HEAD",
                 "refs/remotes/origin/main")

    def stage_target_deletion(self) -> None:
        """The caller's recovery action: the index-only deletion with the
        local copy retained (git rm --cached)."""
        self.git("rm", "--cached", "--quiet", self.TARGET_REL)

    def snapshot_state(self, worktree_rels: list[str]) -> tuple[str, str, dict[str, bytes]]:
        """HEAD oid, full index entries, and the named working-tree bytes."""
        head = self.git("rev-parse", "HEAD").stdout.strip()
        index = self.git("ls-files", "-s").stdout
        work = {
            rel: (self.fixture / rel).read_bytes() for rel in worktree_rels
        }
        return head, index, work

    def assert_state_unchanged(
        self, snap: tuple[str, str, dict[str, bytes]]
    ) -> None:
        head, index, work = snap
        self.assertEqual(self.git("rev-parse", "HEAD").stdout.strip(), head)
        self.assertEqual(self.git("ls-files", "-s").stdout, index)
        for rel, data in work.items():
            self.assertEqual((self.fixture / rel).read_bytes(), data)

    def git_injector_shim(
        self, trigger_args: list[str], inject_shell: str
    ) -> Path:
        """A PATH-shim git that performs one injected shell snippet the
        first time it sees the trigger argument vector, then forwards every
        call (including the triggering one) to the real git unchanged."""
        real_git = shutil.which("git")
        shim_dir = self.tmp / "git-shim"
        shim_dir.mkdir()
        marker = shim_dir / "injection-fired"
        script = shim_dir / "git"
        script.write_text(
            "#!/bin/bash\n"
            "REAL_GIT=%s\n"
            "if [ \"$*\" = %s ] && [ ! -e %s ]; then\n"
            "  : > %s\n"
            "  {\n%s\n} >/dev/null 2>&1\n"
            "fi\n"
            "exec \"$REAL_GIT\" \"$@\"\n"
            % (
                shlex.quote(real_git or "git"),
                shlex.quote(" ".join(trigger_args)),
                shlex.quote(str(marker)),
                shlex.quote(str(marker)),
                inject_shell,
            )
        )
        script.chmod(0o755)
        return shim_dir

    def run_with_shim(self, shim_dir: Path, exports: dict,
                      *args: str) -> subprocess.CompletedProcess:
        env = self.commit_env() | exports
        env["PATH"] = str(shim_dir) + os.pathsep + env["PATH"]
        return self.run_commit(*args, env=env)

    def test_valid_untrack_lands_index_deletion_and_keeps_local_copy_and_rule(self) -> None:
        self.untrack_fixture()
        self.stage_target_deletion()
        setup_proc, exports = self.setup_session("--owned-path", self.TARGET_REL)
        count_before = self.commit_count()
        proc = self.commit_session(
            setup_proc, exports,
            "--untrack", self.TARGET_REL,
            "--subject", "untrack the ignored local-only file",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        combined = proc.stdout + proc.stderr
        self.assertIn(
            "untrack preflight: accepted index-only deletion: "
            + self.TARGET_REL,
            combined,
        )
        self.assertEqual(self.commit_count(), count_before + 1)
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        # the exact committed tree: only the target's deletion against the
        # parent tree, no other entry changed
        self.assertEqual(
            self.git("diff", "--name-only", f"{landing}^", landing).stdout,
            self.TARGET_REL + "\n",
        )
        shown = self.git("show", "--name-status", "--format=", landing).stdout
        self.assertIn("D\t" + self.TARGET_REL, shown)
        # the retained local ignored copy and the intact ignore rule
        local_copy = self.fixture / self.TARGET_REL
        self.assertTrue(local_copy.is_file())
        self.assertEqual(local_copy.read_text(), "key=local\n")
        self.assertEqual(
            self.git("check-ignore", "-q", "--", self.TARGET_REL,
                     check=False).returncode,
            0,
        )
        gitignore = (self.fixture / ".gitignore").read_text()
        self.assertIn("local-home/", gitignore)
        stages = self.trace_stages(self.commit_env() | exports)
        self.assertEqual(stages[0], "untrack-preflight")
        self.assertIn("untrack-captured-tree-invariants", stages)

    def test_untrack_path_absent_from_head_refuses_with_state_preserved(self) -> None:
        self.untrack_fixture()
        self.stage_target_deletion()
        setup_proc, exports = self.setup_session("--owned-path", self.TARGET_REL)
        count_before = self.commit_count()
        snap = self.snapshot_state([self.TARGET_REL, "seed.txt"])
        proc = self.commit_session(
            setup_proc, exports,
            "--untrack", "ghost.txt",
            "--subject", "untrack a path HEAD never tracked",
        )
        self.assertEqual(proc.returncode, 3)
        self.assertIn(
            "--untrack path is not tracked by HEAD: ghost.txt", proc.stderr)
        self.assert_state_unchanged(snap)
        self.assertEqual(self.commit_count(), count_before)
        stages = self.trace_stages(self.commit_env() | exports)
        self.assertEqual(stages[-1], "untrack-preflight")

    def test_untrack_path_still_indexed_refuses_with_state_preserved(self) -> None:
        self.untrack_fixture()
        # no git rm --cached: the target is still an index entry
        setup_proc, exports = self.setup_session("--owned-path", self.TARGET_REL)
        count_before = self.commit_count()
        snap = self.snapshot_state([self.TARGET_REL, "seed.txt"])
        proc = self.commit_session(
            setup_proc, exports,
            "--untrack", self.TARGET_REL,
            "--subject", "untrack while the index entry remains",
        )
        self.assertEqual(proc.returncode, 3)
        self.assertIn(
            "--untrack path is still in the index: " + self.TARGET_REL,
            proc.stderr,
        )
        self.assert_state_unchanged(snap)
        self.assertEqual(self.commit_count(), count_before)
        stages = self.trace_stages(self.commit_env() | exports)
        self.assertEqual(stages[-1], "untrack-preflight")

    def test_untrack_path_missing_worktree_copy_refuses_with_state_preserved(self) -> None:
        self.untrack_fixture()
        self.stage_target_deletion()
        (self.fixture / self.TARGET_REL).unlink()
        setup_proc, exports = self.setup_session("--owned-path", self.TARGET_REL)
        count_before = self.commit_count()
        snap = self.snapshot_state(["seed.txt"])
        proc = self.commit_session(
            setup_proc, exports,
            "--untrack", self.TARGET_REL,
            "--subject", "untrack after the local copy vanished",
        )
        self.assertEqual(proc.returncode, 3)
        self.assertIn(
            "--untrack path is absent from the working tree: "
            + self.TARGET_REL,
            proc.stderr,
        )
        self.assert_state_unchanged(snap)
        self.assertFalse((self.fixture / self.TARGET_REL).exists())
        self.assertEqual(self.commit_count(), count_before)
        stages = self.trace_stages(self.commit_env() | exports)
        self.assertEqual(stages[-1], "untrack-preflight")

    def test_untrack_path_not_ignored_refuses_with_state_preserved(self) -> None:
        self.untrack_fixture()
        (self.fixture / "plain.txt").write_text("plain tracked bytes\n")
        self.git("add", "plain.txt")
        self.git("commit", "-qm", "add a plain tracked file")
        self.git("rm", "--cached", "--quiet", "plain.txt")
        setup_proc, exports = self.setup_session("--owned-path", "plain.txt")
        count_before = self.commit_count()
        snap = self.snapshot_state(["plain.txt", "seed.txt"])
        proc = self.commit_session(
            setup_proc, exports,
            "--untrack", "plain.txt",
            "--subject", "untrack a path no ignore rule matches",
        )
        self.assertEqual(proc.returncode, 3)
        self.assertIn(
            "--untrack path does not match an ignore rule: plain.txt",
            proc.stderr,
        )
        self.assert_state_unchanged(snap)
        self.assertEqual(self.commit_count(), count_before)
        stages = self.trace_stages(self.commit_env() | exports)
        self.assertEqual(stages[-1], "untrack-preflight")

    def test_unchanged_ignored_tracked_file_is_allowed(self) -> None:
        self.untrack_fixture("local-home/keystore.bin")
        self.stage_target_deletion()
        # keystore.bin stays a tracked index entry with unchanged content:
        # outside the staged delta, so the changed-blob scan never sees it
        setup_proc, exports = self.setup_session(
            "--owned-path", self.TARGET_REL,
            "--owned-path", "local-home/keystore.bin",
        )
        count_before = self.commit_count()
        proc = self.commit_session(
            setup_proc, exports,
            "--untrack", self.TARGET_REL,
            "--subject", "untrack one ignored file beside an unchanged one",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        combined = proc.stdout + proc.stderr
        self.assertNotIn("carries an ignored blob", combined)
        self.assertEqual(self.commit_count(), count_before + 1)
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        shown = self.git("show", "--name-status", "--format=", landing).stdout
        self.assertIn("D\t" + self.TARGET_REL, shown)
        self.assertNotIn("keystore.bin", shown)
        self.assertIn(
            "keystore.bin",
            self.git("ls-tree", "--name-only", landing, "local-home/").stdout,
        )
        self.assertTrue((self.fixture / "local-home" / "keystore.bin").is_file())

    def test_force_added_ignored_blob_via_stage_refuses_preflight(self) -> None:
        self.untrack_fixture()
        self.stage_target_deletion()
        # a never-tracked ignored path force-added to the index by the
        # caller before the invocation, then declared through --stage
        (self.fixture / "local-home" / "other.conf").write_text("forced bytes\n")
        self.git("add", "-f", "local-home/other.conf")
        setup_proc, exports = self.setup_session("--owned-path", self.TARGET_REL)
        count_before = self.commit_count()
        snap = self.snapshot_state(
            [self.TARGET_REL, "local-home/other.conf", "seed.txt"]
        )
        proc = self.commit_session(
            setup_proc, exports,
            "--untrack", self.TARGET_REL, "--stage", "local-home/other.conf",
            "--subject", "smuggle a forced ignored blob through --stage",
        )
        self.assertEqual(proc.returncode, 1)
        combined = proc.stdout + proc.stderr
        self.assertIn("carries an ignored blob", combined)
        self.assertIn("local-home/other.conf", combined)
        # the injected caller index state (other.conf still staged) and the
        # rest of HEAD, index, and worktree are unchanged
        self.assert_state_unchanged(snap)
        self.assertEqual(self.commit_count(), count_before)
        stages = self.trace_stages(self.commit_env() | exports)
        self.assertEqual(stages[-1], "untrack-preflight")

    def test_late_readded_target_refuses_at_captured_tree(self) -> None:
        self.untrack_fixture()
        self.stage_target_deletion()
        # a real declared edit authored after setup keeps the landing
        # non-empty, so the run reaches the captured-tree invariants
        # instead of the clean-index skip
        setup_proc, exports = self.setup_session("--owned-path", self.TARGET_REL)
        (self.fixture / "seed.txt").write_text("seed\nrace edit\n")
        count_before = self.commit_count()
        head_before = self.git("rev-parse", "HEAD").stdout.strip()
        # the injection rides the first plain check-ignore of the --stage
        # loop: strictly after the read-only preflight, before stage-operand
        # processing re-adds the target into the index
        shim_dir = self.git_injector_shim(
            ["check-ignore", "-q", "seed.txt"],
            f'"$REAL_GIT" -C {shlex.quote(str(self.fixture))} '
            f"add -f -- {shlex.quote(self.TARGET_REL)}",
        )
        proc = self.run_with_shim(
            shim_dir, exports,
            "--untrack", self.TARGET_REL, "--stage", "seed.txt",
            "--subject", "re-added target races past the preflight",
        )
        self.assertEqual(proc.returncode, 1)
        combined = proc.stdout + proc.stderr
        self.assertIn("re-entered the captured tree after the preflight", combined)
        self.assertIn(self.TARGET_REL, combined)
        # no commit and no ref update
        self.assertEqual(self.commit_count(), count_before)
        self.assertEqual(self.git("rev-parse", "HEAD").stdout.strip(), head_before)
        # the injected caller index state and ordinary explicit staging are
        # preserved, never undone
        self.assertIn(self.TARGET_REL, self.git("ls-files", "-s").stdout)
        self.assertIn(
            "seed.txt",
            self.git("diff", "--cached", "--name-only", "HEAD").stdout,
        )
        self.assertEqual(
            (self.fixture / self.TARGET_REL).read_text(), "key=local\n"
        )

    def test_late_force_added_ignored_stage_path_refuses_at_captured_tree(self) -> None:
        self.untrack_fixture()
        # the ignored non-target is a flat-pattern (*.conf) tracked file at
        # HEAD whose content is unchanged, so the preflight changed-blob
        # scan sees nothing and the runner's own git add of the tracked
        # path is not refused
        (self.fixture / "late.conf").write_text("tracked conf bytes\n")
        self.git("add", "-f", "late.conf")
        self.git("commit", "-qm", "force-track the ignored conf file")
        self.stage_target_deletion()
        setup_proc, exports = self.setup_session(
            "--owned-path", self.TARGET_REL, "--owned-path", "late.conf",
        )
        (self.fixture / "seed.txt").write_text("seed\nrace edit\n")
        count_before = self.commit_count()
        head_before = self.git("rev-parse", "HEAD").stdout.strip()
        # the injection fires during stage-operand processing: the force-add
        # of the ignored non-target's modified blob lands while the --stage
        # loop is between its first declared path and late.conf, so ordinary
        # matching declares late.conf and the captured-tree changed-blob
        # check, not the target check or the foreign-path fence, refuses
        shim_dir = self.git_injector_shim(
            ["check-ignore", "-q", "seed.txt"],
            f"printf 'forced conf bytes\\n' > "
            f"{shlex.quote(str(self.fixture / 'late.conf'))} && "
            f'"$REAL_GIT" -C {shlex.quote(str(self.fixture))} '
            "add -f -- late.conf",
        )
        proc = self.run_with_shim(
            shim_dir, exports,
            "--untrack", self.TARGET_REL,
            "--stage", "seed.txt", "--stage", "late.conf",
            "--subject", "force-added ignored blob races past the preflight",
        )
        self.assertEqual(proc.returncode, 1)
        combined = proc.stdout + proc.stderr
        self.assertIn(
            "captured tree carries an ignored blob among entries changed "
            "from HEAD: late.conf",
            combined,
        )
        # neither the target check nor the foreign-path fence refused
        self.assertNotIn("re-entered the captured tree", combined)
        self.assertNotIn("foreign path entered the staged index", combined)
        self.assertNotIn("git add refused the declared pathspec", combined)
        # no commit and no ref update
        self.assertEqual(self.commit_count(), count_before)
        self.assertEqual(self.git("rev-parse", "HEAD").stdout.strip(), head_before)
        # the injected caller index state and ordinary explicit staging are
        # preserved, never undone; the target stays index-absent
        self.assertIn("late.conf", self.git("ls-files", "-s").stdout)
        self.assertIn(
            "seed.txt",
            self.git("diff", "--cached", "--name-only", "HEAD").stdout,
        )
        self.assertNotIn(self.TARGET_REL, self.git("ls-files", "-s").stdout)
        self.assertEqual(
            (self.fixture / "late.conf").read_text(), "forced conf bytes\n"
        )

    # ---- coverage residuals (backlog 2026-10-31
    # untrack-wrapper-test-coverage-residuals, landed with the trio): the
    # repeatable-operand shape, the parser usage guards, and the
    # --guard-firing ordering pin.

    def test_repeatable_distinct_untrack_operands_both_land(self) -> None:
        """[class: REPOSITORY_TEST] Two distinct --untrack operands in one
        invocation both pass the preflight and both land their index-only
        deletions: a mutation accepting only the first operand fails here."""
        second = "other.conf"
        self.untrack_fixture(second)
        self.stage_target_deletion()
        self.git("rm", "--cached", "--quiet", second)
        setup_proc, exports = self.setup_session(
            "--owned-path", self.TARGET_REL, "--owned-path", second,
        )
        count_before = self.commit_count()
        proc = self.commit_session(
            setup_proc, exports,
            "--untrack", self.TARGET_REL, "--untrack", second,
            "--subject", "untrack two ignored tracked files",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        combined = proc.stdout + proc.stderr
        for rel in (self.TARGET_REL, second):
            self.assertIn(f"accepted index-only deletion: {rel}", combined)
            self.assertNotIn(rel, self.git("ls-files", "-s").stdout)
            self.assertTrue((self.fixture / rel).exists(), rel)
        self.assertEqual(self.commit_count(), count_before + 1)

    def test_untrack_parser_usage_guards_exit_3(self) -> None:
        """[class: REPOSITORY_TEST] The --untrack parser usage guards refuse
        with exit 3 and no state change: a missing value, a `--`-prefixed
        value, and a duplicate same-path operand."""
        self.untrack_fixture()
        snap = self.snapshot_state([self.TARGET_REL])
        count_before = self.commit_count()
        env = self.commit_env()
        missing = self.run_commit("--untrack", "--subject", "s", env=env)
        self.assertEqual(missing.returncode, 3, missing.stderr)
        self.assertIn("--untrack needs <repo-relative-path>", missing.stderr)
        dash = self.run_commit(
            "--untrack", "--dash.conf", "--subject", "s", env=env
        )
        self.assertEqual(dash.returncode, 3, dash.stderr)
        self.assertIn("--untrack needs <repo-relative-path>", dash.stderr)
        duplicate = self.run_commit(
            "--untrack", self.TARGET_REL, "--untrack", self.TARGET_REL,
            env=env,
        )
        self.assertEqual(duplicate.returncode, 3, duplicate.stderr)
        self.assertIn("more than once for path", duplicate.stderr)
        self.assert_state_unchanged(snap)
        self.assertEqual(self.commit_count(), count_before)

    def test_untrack_with_guard_firing_preflight_precedes_ledger_append(self) -> None:
        """[class: REPOSITORY_TEST] The --untrack + --guard-firing
        combination keeps the ordering: an invalid untrack operand refuses
        at the read-only preflight before any ledger append runs, so the
        advisory row is not written for a landing that never stages."""
        self.untrack_fixture()
        snap = self.snapshot_state([self.TARGET_REL])
        count_before = self.commit_count()
        ledger = self.fixture / "scripts" / "gate_liveness_ledger.json"
        if ledger.exists():
            ledger_before = ledger.read_bytes()
        else:
            ledger_before = None
        setup_proc, exports = self.setup_session("--owned-path", self.TARGET_REL)
        proc = self.commit_session(
            setup_proc, exports,
            "--untrack", "never-tracked.conf",
            "--guard-firing", "pin-guard:unit:evidence-untrack-ordering:ordering pin",
            "--subject", "must refuse before the ledger append",
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("not tracked by HEAD: never-tracked.conf", proc.stderr)
        self.assert_state_unchanged(snap)
        self.assertEqual(self.commit_count(), count_before)
        if ledger_before is None:
            self.assertFalse(ledger.exists(), "no ledger appended on preflight refusal")
        else:
            self.assertEqual(ledger.read_bytes(), ledger_before)


class DoneRunDeclaredStageRecoveryReplayTest(FixtureMixin, unittest.TestCase):
    """Task 5 witnesses (plan
    docs/history/plans/2026-10-14-done-ownership-post-setup-learn-edits.md):
    the end-to-end recovery replay through the real cmd_commit drive. The
    positive arm replays the origin incident's shape (primary-resident
    closeout, the declared post-setup learn edit lands on the first
    boundary, the record-only corpus append left unstaged); the negative
    arms pin the out-of-band-staged remedy refusal, the empty declared
    set's non-inheritance of a previous attempt's channel, the
    byte-identical no-manifest refusal that names neither remedy, and the
    absolute declared member's passage through the channel normalization.
    No lib-suite case moves here: every arm needs the cmd_commit drive
    (the --stage flow, the step-6 guard interaction, the channel
    composition), which the gate-level suite cannot express."""

    def replay_fixture(self) -> tuple[subprocess.CompletedProcess, dict]:
        """The origin incident's boundary: closeout.md and the record-only
        corpus are tracked and committed before setup, the manifest claims
        only seed.txt, and nothing is dirty at Step 0."""
        self.init_fixture_repo(branch="feature/PROJ-1234-done-run")
        corpus_dir = self.fixture / "projects" / ".ai-playbook"
        corpus_dir.mkdir(parents=True)
        (corpus_dir / "development_lessons.md").write_text("# lessons\n")
        (self.fixture / "closeout.md").write_text("committed run file\n")
        self.git("add", RECORD_ONLY_CORPUS_REL, "closeout.md")
        self.git("commit", "-qm", "add the run file and the record-only corpus")
        return self.setup_session("--owned-path", "seed.txt")

    def learn_edit(self, body: str) -> None:
        (self.fixture / "closeout.md").write_text(f"committed run file\n{body}\n")

    def test_declared_post_setup_edit_passes_first_boundary_record_only_append_unstaged(self) -> None:
        setup_proc, exports = self.replay_fixture()
        count_before = self.commit_count()
        # the learn step's products, all authored after the manifest was
        # written: the session work, the declared post-setup edit of the
        # unclaimed tracked file, and the record-only corpus append that
        # stays unstaged (permitted-dirty under the allowlist)
        (self.fixture / "seed.txt").write_text("seed\nwork\n")
        self.learn_edit("learn edit")
        (self.fixture / RECORD_ONLY_CORPUS_REL).write_text(
            "# lessons\nwitness append\n"
        )
        proc = self.commit_session(
            setup_proc, exports,
            "--stage", "seed.txt", "--stage", "closeout.md",
            "--subject", "land the session work and the post-setup learn edit",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertEqual(self.commit_count(), count_before + 1)
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        shown = self.git("show", "--name-only", "--format=", landing).stdout
        self.assertIn("seed.txt", shown)
        self.assertIn("closeout.md", shown)
        self.assertNotIn("development_lessons.md", shown)
        # the record-only append stayed unstaged and never entered the index
        self.assertIn(
            RECORD_ONLY_CORPUS_REL,
            self.git("diff", "--name-only", "HEAD").stdout,
        )
        self.assertEqual(
            self.git("diff", "--cached", "--name-only").stdout, ""
        )
        combined = proc.stdout + proc.stderr
        self.assertIn(
            "record-only allowlist path(s) permitted: "
            + RECORD_ONLY_CORPUS_REL,
            combined,
        )
        self.assertIn(
            "staged path(s) owned by the session manifest or the "
            "invocation's declared-stage channel: closeout.md, seed.txt",
            combined,
        )

    def test_out_of_band_staged_learn_edit_refuses_naming_declared_stage_remedy(self) -> None:
        setup_proc, exports = self.replay_fixture()
        count_before = self.commit_count()
        # the learn-edited path staged out-of-band and the commit invoked
        # with NO --stage at all: the empty declared set skips the step-6
        # staged-scope guard, so the run reaches the sweep, which refuses
        # naming the declared-stage re-run as the remedy
        self.learn_edit("learn edit")
        self.git("add", "closeout.md")
        proc = self.commit_session(
            setup_proc, exports,
            "--subject", "out-of-band staged learn edit, empty declared set",
        )
        self.assertEqual(proc.returncode, 1)
        combined = proc.stdout + proc.stderr
        self.assertIn("closeout.md", combined)
        self.assertIn(DECLARED_STAGE_REMEDY_SENTENCE, combined)
        self.assertIn("nothing committed", combined)
        self.assertEqual(self.commit_count(), count_before)
        stages = self.trace_stages(self.commit_env() | exports)
        self.assertEqual(stages[-1], "landing-sweep")

    def test_second_empty_declared_invocation_does_not_inherit_first_channel(self) -> None:
        setup_proc, exports = self.replay_fixture()
        count_before = self.commit_count()
        # the first attempt declares the post-setup edit and lands it
        self.learn_edit("learn edit")
        first = self.commit_session(
            setup_proc, exports,
            "--stage", "closeout.md",
            "--subject", "first attempt declares the post-setup edit",
        )
        self.assertEqual(first.returncode, 0, first.stderr + first.stdout)
        self.assertEqual(self.commit_count(), count_before + 1)
        # the second attempt in the same boundary: a further learn edit
        # staged out-of-band, NO --stage, and the first attempt's channel
        # fed as an ambient export; the empty declared set's active unset
        # must strip it, so the sweep refuses naming the residue path
        self.learn_edit("learn edit\nsecond edit")
        self.git("add", "closeout.md")
        env = self.commit_env()
        env.update(exports)
        env["DONE_SWEEP_DECLARED_STAGE_PATHS"] = "closeout.md\n"
        second = self.run_commit(
            "--subject", "second attempt with an empty declared set", env=env,
        )
        self.assertEqual(second.returncode, 1)
        combined = second.stdout + second.stderr
        self.assertIn("closeout.md", combined)
        self.assertIn(DECLARED_STAGE_REMEDY_SENTENCE, combined)
        self.assertNotIn("declared-stage channel path(s) owned", combined)
        self.assertEqual(self.commit_count(), count_before + 1)
        stages = self.trace_stages(env)
        self.assertEqual(stages[-1], "landing-sweep")

    def test_declared_stage_without_manifest_keeps_byte_identical_no_manifest_text(self) -> None:
        # no setup at all: no session, no manifest; the commit declares the
        # post-setup edit, the sweep's channel is never read (no owned set),
        # and the refusal is the byte-identical no-manifest render carrying
        # neither remedy sentence
        self.init_fixture_repo(branch="feature/PROJ-1234-done-run")
        (self.fixture / "closeout.md").write_text("committed run file\n")
        self.git("add", "closeout.md")
        self.git("commit", "-qm", "add the run file")
        count_before = self.commit_count()
        self.learn_edit("learn edit")
        proc = self.run_commit(
            "--stage", "closeout.md",
            "--subject", "declare a post-setup edit with no prior setup",
        )
        self.assertEqual(proc.returncode, 1)
        combined = proc.stdout + proc.stderr
        self.assertIn("[post-landing-staging] rc=1 " + NO_MANIFEST_REFUSAL_PIN, combined)
        self.assertNotIn(
            "re-running the commit with the path declared via --stage", combined
        )
        self.assertNotIn(
            "closing this done boundary and opening a fresh adopting boundary",
            combined,
        )
        self.assertEqual(self.commit_count(), count_before)

    def test_absolute_declared_member_passes_through_channel_normalization(self) -> None:
        setup_proc, exports = self.replay_fixture()
        count_before = self.commit_count()
        self.learn_edit("learn edit")
        # the step-6 staged-scope guard compares raw strings against git's
        # repo-relative staged entries, so a sole absolute declaration
        # refuses there (pre-existing guard behavior, unchanged by this
        # plan); the wrapper-encodable arm declares the same path in both
        # forms and pins the absolute member's passage through the channel
        # normalization into the gate (one deduplicated relative name)
        absolute = str((self.fixture / "closeout.md").resolve())
        proc = self.commit_session(
            setup_proc, exports,
            "--stage", "closeout.md", "--stage", absolute,
            "--subject", "the absolute declared member normalizes into the sweep",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertEqual(self.commit_count(), count_before + 1)
        combined = proc.stdout + proc.stderr
        self.assertIn(
            "declared-stage channel path(s) owned (1): closeout.md", combined
        )
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        shown = self.git("show", "--name-only", "--format=", landing).stdout
        self.assertIn("closeout.md", shown)


class DoneRunEmptyDeclaredForeignIndexTest(FixtureMixin, unittest.TestCase):
    """Task 2 witnesses (plan
    docs/history/plans/2026-10-16-done-empty-declared-set-foreign-index-
    fence.md): the landing commit's empty-declared refusal arm over a
    non-empty staged index, fenced to the live ad-hoc worktree closeout
    shape whose Step 0 manifest resolves (the primary-resident
    empty-declared shapes keep their upstream landing-sweep refusals, so
    only a linked worktree reaches the landing-commit stage today), plus
    the clean-index skip and the owned-set commit the arm must not
    disturb. The declared-deletion control is the existing
    DoneRunDeclaredDeletionTest suite, whose sets are all non-empty."""

    def worktree_fixture(self) -> Path:
        """An ad-hoc worktree closeout cwd: the primary seeds the facts
        dir family (the worktree migration's capture reads all four keys
        fail-loud), then a linked worktree becomes the fixture root."""
        primary = self.init_fixture_repo()
        (primary / ".ai-playbook" / "facts.md").write_text(
            "```toml\n"
            'plans_dir = "docs/history/plans/"\n'
            'backlog_dir = "docs/history/backlog/"\n'
            'reviews_dir = ".ai-playbook/reviews/"\n'
            'tmp_dir = "docs/tmp/"\n'
            'metrics_dir = ".ai-playbook/metrics/"\n'
            'review_certs_dir = ".ai-playbook/review-certs/"\n'
            "```\n"
        )
        self.git("add", ".ai-playbook/facts.md")
        self.git("commit", "-qm", "complete the facts dir family")
        worktree = self.tmp / "worktree"
        self.git("worktree", "add", "-qb", "feature/PROJ-1234-done-run",
                 str(worktree))
        self.fixture = worktree
        return worktree

    def provision_skip_evidence(self, exports: dict) -> Path:
        """Zero-plan runs own no plan baseline and the commit-time late
        capture is removed: the run-ID-keyed sibling skip record is the
        evidence the closeout contract requires before the docs-sync stage.
        The fixture owns no transferable run artifact, so the recorded
        scoped-copy inventory the skip arm's session duty requires is empty;
        the populated-inventory witness lives in
        DoneRunCloseoutBaselineArmTest."""
        skip = self.fixture / "docs" / "tmp" / "done-session" / (
            f"worktree-migrate-baseline-{exports['DONE_RUN_ID']}-skip.json"
        )
        skip.parent.mkdir(parents=True, exist_ok=True)
        skip.write_text(
            json.dumps(
                {
                    "skip": True,
                    "reason": "zero owned plans; no plan baseline to reuse",
                    "fallback": "manual scoped copy",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return skip

    def test_empty_declared_set_over_staged_foreign_file_refuses_at_landing_commit(self) -> None:
        self.worktree_fixture()
        setup_proc, exports = self.setup_session("--owned-path", "seed.txt")
        self.provision_skip_evidence(exports)
        # the foreign entry is staged AFTER setup, owned by no declared set
        (self.fixture / "foreign.txt").write_text("foreign staged work\n")
        self.git("add", "foreign.txt")
        before_status = self.git("status", "--porcelain").stdout
        count_before = self.commit_count()
        proc = self.commit_session(
            setup_proc, exports,
            "--subject", "empty declared set over a staged foreign file",
        )
        self.assertEqual(proc.returncode, 1)
        combined = proc.stdout + proc.stderr
        self.assertIn("empty declared set over a non-empty staged index", combined)
        self.assertIn("foreign.txt", combined)
        self.assertIn("nothing committed", combined)
        self.assertEqual(self.commit_count(), count_before)
        # the refusal wrote no bytes: the porcelain state is byte-identical
        self.assertEqual(self.git("status", "--porcelain").stdout, before_status)
        # the trace ends at the landing-commit stage, past the sweep gates
        stages = self.trace_stages(self.commit_env() | exports)
        self.assertEqual(stages[-1], "landing-commit")

    def test_clean_index_empty_declared_set_keeps_existing_skip_line(self) -> None:
        self.worktree_fixture()
        setup_proc, exports = self.setup_session("--owned-path", "seed.txt")
        self.provision_skip_evidence(exports)
        count_before = self.commit_count()
        proc = self.commit_session(
            setup_proc, exports,
            "--subject", "empty declared set over a clean index",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        combined = proc.stdout + proc.stderr
        self.assertIn("no staged changes; landing commit skipped", combined)
        self.assertNotIn("empty declared set over a non-empty staged index", combined)
        self.assertEqual(self.commit_count(), count_before)
        stages = self.trace_stages(self.commit_env() | exports)
        # the skip decided inside the landing-commit stage, which then ran on
        self.assertEqual(stages.count("landing-commit"), 1)

    def test_owned_declared_set_lands_exactly_its_paths_in_the_worktree(self) -> None:
        self.worktree_fixture()
        setup_proc, exports = self.setup_session("--owned-path", "seed.txt")
        self.provision_skip_evidence(exports)
        (self.fixture / "seed.txt").write_text("seed\nwork\n")
        count_before = self.commit_count()
        proc = self.commit_session(
            setup_proc, exports,
            "--stage", "seed.txt",
            "--subject", "land the declared seed edit",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.commit_count(), count_before + 1)
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        shown = self.git("show", "--name-only", "--format=", landing).stdout.split()
        self.assertEqual(shown, ["seed.txt"])
        stages = self.trace_stages(self.commit_env() | exports)
        self.assertEqual(stages.count("landing-commit"), 1)


class DoneRunAuthorizedRestorationTest(FixtureMixin, unittest.TestCase):
    """Task 1 witnesses (plan
    docs/history/plans/2026-10-19-done-cached-diff-authorized-reversal.md):
    the commit subcommand's invocation-scoped --authorize-ancestor-restoration
    binding and its guarded landing protocol: run-tuple resolution through
    the existing loader/classifier, the cached-diff lift for exactly one
    bound path, the recorded staged tree, the Git-order pre-update commit
    hooks, the index-tree and HEAD-identity refusals, the pre-transaction
    run-tuple/lock revalidation, one compare-and-swap ref transaction, the
    fused owned-commits ledger, and post-commit on the new HEAD."""

    VINTAGE = "a\nold\n"
    GAINED = "a\nnew\n"

    def restoration_fixture(self) -> tuple[dict, str, str]:
        """work.txt history: the ancestor vintage committed, a HEAD-gained
        vintage on top, and the staged index+worktree restored to the
        ancestor bytes; returns (setup exports, ancestor blob, prior HEAD)."""
        self.init_fixture_repo(branch="feature/PROJ-1234-done-run")
        (self.fixture / "work.txt").write_text(self.VINTAGE)
        self.git("add", "work.txt")
        self.git("commit", "-qm", "base work content")
        (self.fixture / "work.txt").write_text(self.GAINED)
        self.git("add", "work.txt")
        self.git("commit", "-qm", "gain head content")
        (self.fixture / "work.txt").write_text(self.VINTAGE)
        self.git("add", "work.txt")
        ancestor_blob = self.git("rev-parse", "HEAD~1:work.txt").stdout.strip()
        prior_head = self.git("rev-parse", "HEAD").stdout.strip()
        setup_proc, exports = self.setup_session("--owned-path", "work.txt")
        return exports, ancestor_blob, prior_head

    def install_hook(self, name: str, body: str) -> Path:
        hooks = self.fixture / ".git" / "hooks"
        hooks.mkdir(exist_ok=True)
        hook = hooks / name
        hook.write_text("#!/bin/sh\n" + body)
        hook.chmod(0o755)
        return hook

    def probe_path(self, name: str) -> Path:
        return self.tmp / f"probe-{name}.txt"

    def probe_snippet(self, hook: str, extra: str = "") -> str:
        """Shell snippet appending one probe record (cwd, arg count, GIT_DIR)
        for `hook`, plus any hook-specific extra lines."""
        probe = str(self.probe_path(hook))
        return (
            f"printf '%s\\n' '{hook}' >> '{probe}'\n"
            f"printf 'cwd=%s\\n' \"$(pwd)\" >> '{probe}'\n"
            f"printf 'args=%s\\n' \"$#\" >> '{probe}'\n"
            f"printf 'git_dir=%s\\n' \"${{GIT_DIR:-unset}}\" >> '{probe}'\n"
            f"{extra}"
        )

    def authorized_env(self, exports: dict, **overrides: str) -> dict:
        env = self.commit_env()
        env.update(exports)
        env.update(overrides)
        return env

    def assert_landed(
        self, proc: subprocess.CompletedProcess, exports: dict,
        prior_head: str, ancestor_blob: str,
    ) -> str:
        """The authorized landing witnesses shared by the positive arms."""
        self.assertEqual(proc.returncode, 0, proc.stderr)
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        parents = self.git("rev-list", "--parents", "-1", "HEAD").stdout.split()
        self.assertEqual(parents, [landing, prior_head])
        self.assertEqual(
            self.git("rev-parse", "HEAD:work.txt").stdout.strip(), ancestor_blob,
        )
        ledger = self.done_session() / (
            f"owned-commits-{exports['DONE_RUN_ID']}.txt"
        )
        self.assertEqual(ledger.read_text().splitlines(), [landing])
        return landing

    def assert_refused(self, proc: subprocess.CompletedProcess, exports: dict,
                       prior_head: str, *fragments: str) -> None:
        combined = proc.stdout + proc.stderr
        self.assertNotEqual(proc.returncode, 0, combined)
        for fragment in fragments:
            self.assertIn(fragment, combined)
        self.assertEqual(self.git("rev-parse", "HEAD").stdout.strip(), prior_head)
        ledger = self.done_session() / (
            f"owned-commits-{exports['DONE_RUN_ID']}.txt"
        )
        self.assertFalse(ledger.exists())

    def test_matching_authorized_restoration_lands_exact_staged_tree(self) -> None:
        exports, ancestor_blob, prior_head = self.restoration_fixture()
        count_before = self.commit_count()
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--subject", "restore the ancestor bytes deliberately",
            env=self.authorized_env(exports),
        )
        self.assert_landed(proc, exports, prior_head, ancestor_blob)
        self.assertEqual(self.commit_count(), count_before + 1)
        combined = proc.stdout + proc.stderr
        self.assertIn(
            "authorized restoration: path work.txt bound to expected blob",
            combined,
        )
        self.assertIn(
            "cached-diff guard: authorized ancestor restoration accepted "
            "for this invocation: work.txt",
            combined,
        )
        message = self.git("log", "-1", "--format=%B").stdout
        self.assertEqual(message.splitlines()[0], "[PROJ-1234] restore the ancestor bytes deliberately")
        # the guarded staged tree landed exactly its declared set
        shown = self.git("show", "--name-only", "--format=", "HEAD").stdout.split()
        self.assertEqual(shown, ["work.txt"])
        stages = self.trace_stages(self.commit_env() | exports)
        self.assertEqual(stages[0], "authorize-run-tuple")
        self.assertIn("landing-commit", stages)

    def test_wrong_expected_blob_refuses(self) -> None:
        exports, _, prior_head = self.restoration_fixture()
        head_blob = self.git("rev-parse", "HEAD:work.txt").stdout.strip()
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", head_blob,
            "--subject", "authorize the wrong blob",
            env=self.authorized_env(exports),
        )
        self.assert_refused(proc, exports, prior_head,
                            "does not equal the expected blob")

    def test_unbound_path_refuses(self) -> None:
        exports, ancestor_blob, prior_head = self.restoration_fixture()
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "elsewhere.txt", ancestor_blob,
            "--subject", "authorize a path outside the declared set",
            env=self.authorized_env(exports),
        )
        self.assert_refused(proc, exports, prior_head,
                            "not in the declared --stage set: elsewhere.txt")

    def test_missing_staged_file_refuses(self) -> None:
        """An authorized path whose declared shape is the already-staged
        deletion has no staged index entry and refuses (missing staged
        file), never impersonating the declared-deletion passage."""
        self.init_fixture_repo(branch="feature/PROJ-1234-done-run")
        (self.fixture / "gone.txt").write_text("tracked work\n")
        self.git("add", "gone.txt")
        self.git("commit", "-qm", "add gone")
        (self.fixture / "work.txt").write_text("plain work\n")
        self.git("add", "work.txt")
        self.git("commit", "-qm", "add work")
        (self.fixture / "gone.txt").unlink()
        self.git("rm", "--cached", "--quiet", "gone.txt")
        prior_head = self.git("rev-parse", "HEAD").stdout.strip()
        setup_proc, exports = self.setup_session(
            "--owned-path", "work.txt", "--owned-path", "gone.txt",
        )
        proc = self.run_commit(
            "--stage", "work.txt", "--stage", "gone.txt",
            "--authorize-ancestor-restoration", "gone.txt",
            "0123456789abcdef0123456789abcdef01234567",
            "--subject", "authorize a deletion as a restoration",
            env=self.authorized_env(exports),
        )
        self.assert_refused(proc, exports, prior_head,
                            "no staged index entry: gone.txt")

    def test_revert_formatting_on_authorized_path_refuses(self) -> None:
        """An authorized path also named in --revert-formatting (a
        whitespace-only ancestor/HEAD difference makes it both guard-flagged
        and a formatting candidate) refuses at the tree capture instead of
        landing HEAD's blob while recording an authorized landing; a second
        staged entry keeps the landing live so the refusal arm is reached."""
        self.init_fixture_repo(branch="feature/PROJ-1234-done-run")
        (self.fixture / "work.txt").write_text("a\nold\n")
        (self.fixture / "other.txt").write_text("other\n")
        self.git("add", "work.txt", "other.txt")
        self.git("commit", "-qm", "base work content")
        (self.fixture / "work.txt").write_text("a\nold \n")
        (self.fixture / "other.txt").write_text("other edit\n")
        self.git("add", "work.txt", "other.txt")
        self.git("commit", "-qm", "gain trailing space and edit")
        (self.fixture / "work.txt").write_text("a\nold\n")
        (self.fixture / "other.txt").write_text("other further\n")
        self.git("add", "work.txt", "other.txt")
        ancestor_blob = self.git("rev-parse", "HEAD~1:work.txt").stdout.strip()
        prior_head = self.git("rev-parse", "HEAD").stdout.strip()
        setup_proc, exports = self.setup_session(
            "--owned-path", "work.txt", "--owned-path", "other.txt",
        )
        proc = self.run_commit(
            "--stage", "work.txt", "--stage", "other.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--revert-formatting", "work.txt",
            "--subject", "authorize and revert-format the same path",
            env=self.authorized_env(exports),
        )
        self.assert_refused(
            proc, exports, prior_head,
            "left the declared set before the tree capture",
        )

    def test_authorized_empty_staged_set_at_landing_refuses(self) -> None:
        """A sole authorized path reverted by --revert-formatting empties the
        staged set; the landing refuses instead of the pre-existing
        no-staged-changes skip arm exiting 0 with the authorization inert."""
        self.init_fixture_repo(branch="feature/PROJ-1234-done-run")
        (self.fixture / "work.txt").write_text("a\nold\n")
        self.git("add", "work.txt")
        self.git("commit", "-qm", "base work content")
        (self.fixture / "work.txt").write_text("a\nold \n")
        self.git("add", "work.txt")
        self.git("commit", "-qm", "gain trailing space")
        (self.fixture / "work.txt").write_text("a\nold\n")
        self.git("add", "work.txt")
        ancestor_blob = self.git("rev-parse", "HEAD~1:work.txt").stdout.strip()
        prior_head = self.git("rev-parse", "HEAD").stdout.strip()
        setup_proc, exports = self.setup_session("--owned-path", "work.txt")
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--revert-formatting", "work.txt",
            "--subject", "authorize and revert-format the sole path",
            env=self.authorized_env(exports),
        )
        self.assert_refused(
            proc, exports, prior_head,
            "the staged set is empty at the landing",
        )

    def test_detached_head_attach_during_hooks_refuses(self) -> None:
        """A detached checkout that a pre-update commit hook re-attaches
        refuses (the detached landing arm's negative control)."""
        exports, ancestor_blob, prior_head = self.restoration_fixture()
        self.git("checkout", "--detach")
        self.install_hook(
            "prepare-commit-msg",
            "git symbolic-ref HEAD refs/heads/feature/PROJ-1234-done-run\n",
        )
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--boundary-class", "per-task",
            "--subject", "detached landing with attach hook",
            env=self.authorized_env(exports),
        )
        self.assert_refused(
            proc, exports, prior_head,
            "HEAD left detached during the pre-update commit hooks",
        )
        # the hook's re-attach side effect stands; the landing still refused
        attached = self.git("symbolic-ref", "-q", "HEAD").stdout.strip()
        self.assertEqual(attached, "refs/heads/feature/PROJ-1234-done-run")
        self.assertEqual(
            self.git("rev-parse", "HEAD").stdout.strip(), prior_head,
        )

    def test_stale_marker_refuses(self) -> None:
        exports, ancestor_blob, prior_head = self.restoration_fixture()
        Path(exports["DONE_RUN_MARKER"]).write_text("garbage marker content\n")
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--subject", "authorize over a stale marker",
            env=self.authorized_env(exports),
        )
        self.assert_refused(proc, exports, prior_head,
                            "no root-confirmed run-start marker")

    def test_mismatched_marker_export_refuses(self) -> None:
        exports, ancestor_blob, prior_head = self.restoration_fixture()
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--subject", "authorize with a foreign marker export",
            env=self.authorized_env(
                exports, DONE_RUN_MARKER=str(self.tmp / "elsewhere"),
            ),
        )
        self.assert_refused(proc, exports, prior_head,
                            "selected DONE_RUN_MARKER export is not the "
                            "newest root-confirmed marker")

    def test_mismatched_run_id_export_refuses(self) -> None:
        exports, ancestor_blob, prior_head = self.restoration_fixture()
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--subject", "authorize with a foreign run id export",
            env=self.authorized_env(exports, DONE_RUN_ID="20991231T235959Z-foreign00"),
        )
        self.assert_refused(proc, exports, prior_head,
                            "does not match the run manifest run_id=")

    def test_mismatched_manifest_export_refuses(self) -> None:
        exports, ancestor_blob, prior_head = self.restoration_fixture()
        # the export names a CANONICAL record bound to a foreign marker: a
        # conflicting signal, not a stale hint (a shadow-named or missing
        # export is only a hint and never selects; the selection itself
        # binds to the active confirmed marker)
        template = Path(exports["DONE_RUN_MANIFEST"])
        record = json.loads(template.read_text())
        record["marker"] = "run-start-00000000-dead"
        crafted = self.done_session() / "run-manifest-20991231T000000Z-foreign1.json"
        crafted.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--subject", "authorize with a foreign manifest export",
            env=self.authorized_env(exports, DONE_RUN_MANIFEST=str(crafted)),
        )
        self.assert_refused(proc, exports, prior_head,
                            "conflicts with the active confirmed marker")

    def test_root_mismatch_refuses(self) -> None:
        exports, ancestor_blob, prior_head = self.restoration_fixture()
        self.rewrite_manifest(exports, repo_root="0" * 64)
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--subject", "authorize over a foreign root manifest",
            env=self.authorized_env(exports),
        )
        self.assert_refused(proc, exports, prior_head,
                            "records a different repo root")

    def test_terminal_run_refuses(self) -> None:
        exports, ancestor_blob, prior_head = self.restoration_fixture()
        self.rewrite_manifest(exports, complete=True)
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--subject", "authorize over a finalized run",
            env=self.authorized_env(exports),
        )
        self.assert_refused(proc, exports, prior_head,
                            "the run boundary is finalized")

    def test_unowned_lock_refuses(self) -> None:
        exports, ancestor_blob, prior_head = self.restoration_fixture()
        env = self.authorized_env(exports)
        env.pop("DONE_LOCK_TOKEN")
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--subject", "authorize without the lock exports",
            env=env,
        )
        self.assert_refused(proc, exports, prior_head,
                            "no live done-lock ownership")

    def test_unrelated_reversal_still_refuses(self) -> None:
        self.init_fixture_repo(branch="feature/PROJ-1234-done-run")
        for name, vintage, gained in (
            ("work.txt", self.VINTAGE, self.GAINED),
            ("other.txt", "o\nold\n", "o\nnew\n"),
        ):
            (self.fixture / name).write_text(vintage)
            self.git("add", name)
            self.git("commit", "-qm", f"base {name}")
            (self.fixture / name).write_text(gained)
            self.git("add", name)
            self.git("commit", "-qm", f"gain {name}")
            (self.fixture / name).write_text(vintage)
            self.git("add", name)
        ancestor_blob = self.git("rev-parse", "HEAD~1:work.txt").stdout.strip()
        prior_head = self.git("rev-parse", "HEAD").stdout.strip()
        setup_proc, exports = self.setup_session(
            "--owned-path", "work.txt", "--owned-path", "other.txt",
        )
        count_before = self.commit_count()
        proc = self.run_commit(
            "--stage", "work.txt", "--stage", "other.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--subject", "authorize one restoration beside an unrelated one",
            env=self.authorized_env(exports),
        )
        combined = proc.stdout + proc.stderr
        self.assertNotEqual(proc.returncode, 0, combined)
        self.assertIn("leaked revert", combined)
        self.assertIn("other.txt", combined)
        self.assertEqual(self.git("rev-parse", "HEAD").stdout.strip(), prior_head)
        self.assertEqual(self.commit_count(), count_before)
        stages = self.trace_stages(self.commit_env() | exports)
        self.assertEqual(stages[-1], "cached-diff-guard")

    def test_hook_index_tree_change_refuses(self) -> None:
        exports, ancestor_blob, prior_head = self.restoration_fixture()
        count_before = self.commit_count()
        self.install_hook(
            "pre-commit",
            "printf 'a\\nhooked\\n' > work.txt\n"
            "git add work.txt\n",
        )
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--subject", "a hook mutates the staged tree",
            env=self.authorized_env(exports),
        )
        self.assert_refused(proc, exports, prior_head,
                            "changed the staged index tree")
        self.assertEqual(self.commit_count(), count_before)

    def test_hook_scope_change_refuses(self) -> None:
        exports, ancestor_blob, prior_head = self.restoration_fixture()
        count_before = self.commit_count()
        self.install_hook(
            "pre-commit",
            "printf 'stranger bytes\\n' > stranger.txt\n"
            "git add stranger.txt\n",
        )
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--subject", "a hook stages a foreign scope change",
            env=self.authorized_env(exports),
        )
        self.assert_refused(proc, exports, prior_head,
                            "changed the staged index tree")
        self.assertEqual(self.commit_count(), count_before)

    def test_worktree_bytes_never_substitute_staged_bytes(self) -> None:
        exports, ancestor_blob, prior_head = self.restoration_fixture()
        # a pre-update commit hook drifts the worktree bytes only; the index
        # keeps the staged restoration, and the landing must carry exactly
        # the staged blob (commit-tree never rereads worktree bytes)
        self.install_hook(
            "pre-commit",
            "printf 'a\\nhooked worktree drift\\n' > work.txt\n",
        )
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--subject", "land the staged bytes, not the worktree",
            env=self.authorized_env(exports),
        )
        self.assert_landed(proc, exports, prior_head, ancestor_blob)
        self.assertIn(self.VINTAGE, self.git("show", "HEAD:work.txt").stdout)
        self.assertIn(
            "hooked worktree drift",
            (self.fixture / "work.txt").read_text(),
        )

    def test_same_oid_head_switch_during_hooks_refuses(self) -> None:
        exports, ancestor_blob, prior_head = self.restoration_fixture()
        self.install_hook("pre-commit", "git checkout -qb same-snap-branch\n")
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--subject", "a hook switches HEAD at the same OID",
            env=self.authorized_env(exports),
        )
        self.assert_refused(proc, exports, prior_head,
                            "symbolic target changed")
        # the hook's side effect stands (outside the wrapper guarantee) and
        # nothing landed on top of it
        self.assertEqual(
            self.git("rev-parse", "HEAD").stdout.strip(), prior_head,
        )
        self.assertEqual(
            self.git("symbolic-ref", "--short", "-q", "HEAD").stdout.strip(),
            "same-snap-branch",
        )

    def test_branch_tip_move_during_hooks_refuses(self) -> None:
        exports, ancestor_blob, prior_head = self.restoration_fixture()
        count_before = self.commit_count()
        self.install_hook(
            "pre-commit",
            "new=$(git commit-tree 'HEAD^{tree}' -p HEAD -m 'hook moved the tip')\n"
            'git update-ref "refs/heads/$(git symbolic-ref --short HEAD)" "$new"\n',
        )
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--subject", "a hook moves the branch tip",
            env=self.authorized_env(exports),
        )
        combined = proc.stdout + proc.stderr
        self.assertNotEqual(proc.returncode, 0, combined)
        self.assertIn("OID moved", combined)
        ledger = self.done_session() / (
            f"owned-commits-{exports['DONE_RUN_ID']}.txt"
        )
        self.assertFalse(ledger.exists())
        # the hook's move stands and the wrapper landed nothing on top of it:
        # the tip is exactly the hook's sole-parent-at-prior-HEAD commit
        self.assertEqual(self.commit_count(), count_before + 1)
        tip = self.git("rev-list", "--parents", "-1", "HEAD").stdout.split()
        self.assertEqual(tip[1:], [prior_head])
        self.assertEqual(
            self.git("log", "-1", "--format=%s").stdout.strip(),
            "hook moved the tip",
        )

    def test_lock_replacement_during_hooks_refuses(self) -> None:
        exports, ancestor_blob, prior_head = self.restoration_fixture()
        self.install_hook(
            "pre-commit",
            'sed \'s/^lock_token=.*/lock_token=tampered/\' '
            '"$DONE_LOCK_DIR/meta.env" > "$DONE_LOCK_DIR/meta.env.t"\n'
            'mv "$DONE_LOCK_DIR/meta.env.t" "$DONE_LOCK_DIR/meta.env"\n',
        )
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--subject", "a hook replaces the lock token",
            env=self.authorized_env(exports),
        )
        self.assert_refused(proc, exports, prior_head,
                            "no live done-lock ownership")

    def test_manifest_finalized_during_hooks_refuses(self) -> None:
        exports, ancestor_blob, prior_head = self.restoration_fixture()
        self.install_hook(
            "pre-commit",
            "python3 -c 'import json,sys; p=sys.argv[1];"
            " d=json.load(open(p)); d[\"complete\"]=True;"
            " json.dump(d, open(p, \"w\"), indent=2, sort_keys=True)'"
            ' "$DONE_RUN_MANIFEST"\n',
        )
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--subject", "a hook finalizes the run manifest",
            env=self.authorized_env(exports),
        )
        self.assert_refused(proc, exports, prior_head,
                            "the run boundary is finalized")

    def test_hook_arguments_environment_and_message_handling(self) -> None:
        exports, ancestor_blob, prior_head = self.restoration_fixture()
        msg_file_record = str(self.probe_path("prepare-commit-msg-msgfile"))
        self.install_hook(
            "pre-commit",
            self.probe_snippet("pre-commit"),
        )
        self.install_hook(
            "prepare-commit-msg",
            self.probe_snippet(
                "prepare-commit-msg",
                extra=(
                    'printf \'msgfile=%s\\n\' "$1" >> "'
                    + str(self.probe_path("prepare-commit-msg"))
                    + '"\n'
                    'printf \'source=%s\\n\' "$2" >> "'
                    + str(self.probe_path("prepare-commit-msg"))
                    + '"\n'
                    'cp "$1" "' + str(msg_file_record) + '"\n'
                ),
            ),
        )
        self.install_hook(
            "commit-msg",
            self.probe_snippet(
                "commit-msg",
                extra=(
                    'printf \'msgfile=%s\\n\' "$1" >> "'
                    + str(self.probe_path("commit-msg"))
                    + '"\n'
                    'printf "commit-msg added a line\\n" >> "$1"\n'
                ),
            ),
        )
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--subject", "probe the pre-update commit hooks",
            env=self.authorized_env(exports),
        )
        self.assert_landed(proc, exports, prior_head, ancestor_blob)
        pre = self.probe_path("pre-commit").read_text().splitlines()
        self.assertIn("args=0", pre)
        self.assertEqual(
            [ln for ln in pre if ln.startswith("cwd=")],
            [f"cwd={self.fixture.resolve()}"],
        )
        self.assertTrue(
            [ln for ln in pre if ln.startswith("git_dir=")
             and not ln.endswith("=unset")],
            pre,
        )
        prepare = self.probe_path("prepare-commit-msg").read_text().splitlines()
        self.assertIn("args=2", prepare)
        self.assertIn("source=message", prepare)
        self.assertTrue(
            any(ln.startswith("msgfile=") for ln in prepare), prepare,
        )
        # the prepare-commit-msg file carried the composed message
        self.assertIn(
            "[PROJ-1234] probe the pre-update commit hooks",
            Path(msg_file_record).read_text(),
        )
        commit_msg = self.probe_path("commit-msg").read_text().splitlines()
        self.assertIn("args=1", commit_msg)
        self.assertTrue(
            any(ln.startswith("msgfile=") for ln in commit_msg), commit_msg,
        )
        # the landed message is the post-commit-msg file bytes: the hook's
        # added line rode through
        message = self.git("log", "-1", "--format=%B").stdout
        self.assertIn(
            "[PROJ-1234] probe the pre-update commit hooks", message,
        )
        self.assertIn("commit-msg added a line", message)

    def test_post_commit_no_args_sees_new_head(self) -> None:
        exports, ancestor_blob, prior_head = self.restoration_fixture()
        self.install_hook(
            "post-commit",
            self.probe_snippet(
                "post-commit",
                extra=(
                    "printf 'head=%s\\n' \"$(git rev-parse HEAD)\" >> \""
                    + str(self.probe_path("post-commit"))
                    + "\"\n"
                ),
            ),
        )
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--subject", "probe post-commit on the new HEAD",
            env=self.authorized_env(exports),
        )
        landing = self.assert_landed(proc, exports, prior_head, ancestor_blob)
        probe = self.probe_path("post-commit").read_text().splitlines()
        self.assertIn("args=0", probe)
        self.assertIn(f"head={landing}", probe)

    def test_hook_failure_refuses_and_skips_post_commit(self) -> None:
        exports, ancestor_blob, prior_head = self.restoration_fixture()
        count_before = self.commit_count()
        self.install_hook("pre-commit", "exit 1\n")
        self.install_hook(
            "post-commit", "touch " + str(self.probe_path("post-commit")) + "\n",
        )
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--subject", "pre-commit refuses outright",
            env=self.authorized_env(exports),
        )
        self.assert_refused(proc, exports, prior_head,
                            "pre-commit hook refused")
        self.assertEqual(self.commit_count(), count_before)
        # refusals skip post-commit
        self.assertFalse(self.probe_path("post-commit").exists())

    def test_marker_removal_during_hooks_refuses(self) -> None:
        exports, ancestor_blob, prior_head = self.restoration_fixture()
        self.install_hook("pre-commit", "rm -f \"$DONE_RUN_MARKER\"\n")
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--subject", "a hook removes the run marker",
            env=self.authorized_env(exports),
        )
        self.assert_refused(proc, exports, prior_head,
                            "no root-confirmed run-start marker")

    def test_post_commit_failure_leaves_commit_landed(self) -> None:
        exports, ancestor_blob, prior_head = self.restoration_fixture()
        count_before = self.commit_count()
        self.install_hook("post-commit", "exit 1\n")
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--subject", "post-commit fails after the landing",
            env=self.authorized_env(exports),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(
            "post-commit hook failed; the landed commit stands",
            proc.stderr,
        )
        self.assertEqual(self.commit_count(), count_before + 1)
        ledger = self.done_session() / (
            f"owned-commits-{exports['DONE_RUN_ID']}.txt"
        )
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        self.assertEqual(ledger.read_text().splitlines(), [landing])

    def test_reference_transaction_phases_fired(self) -> None:
        exports, ancestor_blob, prior_head = self.restoration_fixture()
        probe = self.probe_path("ref-transaction")
        self.install_hook(
            "reference-transaction",
            (
                f"printf 'phase=%s\\n' \"$1\" >> '{probe}'\n"
                f"cat >> '{probe}'\n"
            ),
        )
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--subject", "probe the ref transaction phases",
            env=self.authorized_env(exports),
        )
        landing = self.assert_landed(proc, exports, prior_head, ancestor_blob)
        text = probe.read_text()
        self.assertIn("phase=prepared", text)
        self.assertIn("phase=committed", text)
        self.assertIn(
            f"{prior_head} {landing} refs/heads/feature/PROJ-1234-done-run",
            text,
        )

    def test_reference_transaction_veto_blocks_landing(self) -> None:
        exports, ancestor_blob, prior_head = self.restoration_fixture()
        count_before = self.commit_count()
        self.install_hook(
            "reference-transaction",
            '[ "$1" = prepared ] || exit 0\n'
            'while read -r _old _new ref; do\n'
            '  case "$ref" in\n'
            '    refs/heads/feature/PROJ-1234-done-run) exit 1;;\n'
            '  esac\n'
            'done\n'
            'exit 0\n',
        )
        self.install_hook("post-commit", "touch " + str(self.probe_path("post-commit")) + "\n")
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--subject", "the ref hook vetoes the landing",
            env=self.authorized_env(exports),
        )
        self.assert_refused(proc, exports, prior_head,
                            "ref transaction refused")
        self.assertEqual(self.commit_count(), count_before)
        # refusals skip post-commit: the vetoed landing ran none
        self.assertFalse(self.probe_path("post-commit").exists())

    def test_detached_head_lands_direct_cas_without_branch(self) -> None:
        exports, ancestor_blob, prior_head = self.restoration_fixture()
        self.git("checkout", "--detach")
        branches_before = sorted(
            self.git(
                "for-each-ref", "refs/heads", "--format=%(refname)",
            ).stdout.splitlines()
        )
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--boundary-class", "per-task",
            "--subject", "detached authorized landing",
            env=self.authorized_env(exports),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        # direct HEAD compare-and-swapped: still detached, no branch created
        detached = self.git("symbolic-ref", "-q", "HEAD", check=False)
        self.assertNotEqual(detached.returncode, 0)
        self.assertEqual(landing, self.git("rev-parse", "HEAD").stdout.strip())
        parents = self.git("rev-list", "--parents", "-1", "HEAD").stdout.split()
        self.assertEqual(parents, [landing, prior_head])
        self.assertEqual(
            self.git("rev-parse", "HEAD:work.txt").stdout.strip(), ancestor_blob,
        )
        self.assertEqual(
            sorted(
                self.git(
                    "for-each-ref", "refs/heads", "--format=%(refname)",
                ).stdout.splitlines()
            ),
            branches_before,
        )
        ledger = self.done_session() / (
            f"owned-commits-{exports['DONE_RUN_ID']}.txt"
        )
        self.assertEqual(ledger.read_text().splitlines(), [landing])

    def test_landing_preserves_message_identity_and_ledger_once(self) -> None:
        exports, ancestor_blob, prior_head = self.restoration_fixture()
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--subject", "identity and message preservation",
            env=self.authorized_env(
                exports,
                GIT_AUTHOR_NAME="Auth Or", GIT_AUTHOR_EMAIL="auth@example.test",
                GIT_COMMITTER_NAME="Comm Itter",
                GIT_COMMITTER_EMAIL="comm@example.test",
            ),
        )
        landing = self.assert_landed(proc, exports, prior_head, ancestor_blob)
        self.assertEqual(
            self.git("log", "-1", "--format=%an <%ae>|%cn <%ce>").stdout.strip(),
            "Auth Or <auth@example.test>|Comm Itter <comm@example.test>",
        )
        self.assertEqual(
            self.git("log", "-1", "--format=%B").stdout.splitlines()[0],
            "[PROJ-1234] identity and message preservation",
        )
        # no signing injected when the signing config is unset
        self.assertNotIn("gpgsig", self.git("cat-file", "commit", landing).stdout)

    def test_signing_config_preserved(self) -> None:
        exports, ancestor_blob, prior_head = self.restoration_fixture()
        key = self.tmp / "signkey"
        subprocess.run(
            ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C",
             "fixture-signing", "-f", str(key)],
            check=True, capture_output=True, timeout=60,
        )
        self.git("config", "gpg.format", "ssh")
        self.git("config", "user.signingkey", str(key) + ".pub")
        self.git("config", "commit.gpgsign", "true")
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--subject", "signed authorized landing",
            env=self.authorized_env(exports),
        )
        landing = self.assert_landed(proc, exports, prior_head, ancestor_blob)
        self.assertIn(
            "gpgsig", self.git("cat-file", "commit", landing).stdout,
        )

    def test_declared_deletion_stays_scoped_beside_authorization(self) -> None:
        self.init_fixture_repo(branch="feature/PROJ-1234-done-run")
        (self.fixture / "gone.txt").write_text("tracked work\n")
        self.git("add", "gone.txt")
        self.git("commit", "-qm", "add gone")
        (self.fixture / "work.txt").write_text(self.VINTAGE)
        self.git("add", "work.txt")
        self.git("commit", "-qm", "base work content")
        (self.fixture / "work.txt").write_text(self.GAINED)
        self.git("add", "work.txt")
        self.git("commit", "-qm", "gain head content")
        (self.fixture / "work.txt").write_text(self.VINTAGE)
        self.git("add", "work.txt")
        (self.fixture / "gone.txt").unlink()
        self.git("rm", "--cached", "--quiet", "gone.txt")
        ancestor_blob = self.git("rev-parse", "HEAD~1:work.txt").stdout.strip()
        prior_head = self.git("rev-parse", "HEAD").stdout.strip()
        setup_proc, exports = self.setup_session(
            "--owned-path", "work.txt", "--owned-path", "gone.txt",
        )
        proc = self.run_commit(
            "--stage", "work.txt", "--stage", "gone.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--subject", "restoration beside the declared deletion",
            env=self.authorized_env(exports),
        )
        self.assert_landed(proc, exports, prior_head, ancestor_blob)
        shown = self.git("show", "--name-status", "--format=", "HEAD").stdout
        self.assertIn("D\tgone.txt", shown)
        self.assertIn("M\twork.txt", shown)

    def test_option_misuse_refuses(self) -> None:
        self.init_fixture_repo()
        missing_value = self.run_commit(
            "--stage", "seed.txt",
            "--authorize-ancestor-restoration", "work.txt",
            "--subject", "missing the blob value",
        )
        self.assertEqual(missing_value.returncode, 3)
        self.assertIn(
            "needs <repo-relative-path> <expected-blob-id>",
            missing_value.stderr,
        )
        duplicate = self.run_commit(
            "--stage", "seed.txt",
            "--authorize-ancestor-restoration", "a.txt",
            "0123456789abcdef0123456789abcdef01234567",
            "--authorize-ancestor-restoration", "b.txt",
            "0123456789abcdef0123456789abcdef01234567",
            "--subject", "two authorizations",
        )
        self.assertEqual(duplicate.returncode, 3)
        self.assertIn("given more than once", duplicate.stderr)


class DoneRunFinalizeTest(FixtureMixin, unittest.TestCase):
    """Task 4 repository tests: the finalize subcommand's release ceremony."""

    def run_finalize(
        self, *args: str, env: dict | None = None, cwd: Path | None = None,
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(RUNNER), "finalize", *args],
            cwd=str(cwd or self.fixture),
            env=env or self.runner_env(),
            capture_output=True,
            text=True,
            timeout=300,
        )

    def lib_invocation(self, *args: str) -> subprocess.CompletedProcess:
        env = self.runner_env()
        return subprocess.run(
            ["python3", str(REPO_ROOT / "scripts" / "done_sweep_gates_lib.py"), *args],
            cwd=str(self.fixture), env=env,
            capture_output=True, text=True, timeout=120,
        )

    def lock_invocation(self, *args: str, extra_env: dict | None = None) -> subprocess.CompletedProcess:
        env = self.runner_env()
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            ["bash", str(LOCK_SCRIPT), *args],
            cwd=str(self.fixture), env=env,
            capture_output=True, text=True, timeout=120,
        )

    def lock_status(self, merge: bool = False) -> str:
        proc = self.lock_invocation("merge-status" if merge else "status")
        return proc.stdout + proc.stderr

    def make_checkpoint(self, run_id: str) -> Path:
        proc = self.lib_invocation(
            "checkpoint-manifest", "--run-id", run_id,
            "--mode", "create", "--session", "fixture-session", "--gates", "landing",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return self.done_session() / f"run-checkpoint-{run_id}.json"

    def manifest_record(self, exports: dict) -> dict:
        return json.loads(Path(exports["DONE_RUN_MANIFEST"]).read_text())

    def test_finalize_releases_both_locks_finalizes_manifest_removes_checkpoint(self) -> None:
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "finalize-fixture")
        run_id = exports["DONE_RUN_ID"]
        checkpoint = self.make_checkpoint(run_id)
        self.assertTrue(checkpoint.exists())
        # A surviving merge-lock hold (the stranded-span case finalize recovers).
        merge = self.lock_invocation("merge-acquire", "--label", "fixture-merge-span")
        self.assertEqual(merge.returncode, 0, merge.stderr)
        merge_exports = self.eval_exports(merge.stdout)
        self.assertIn("MERGE_LOCK_DIR", merge_exports)
        self.assertIn(": held", self.lock_status())
        self.assertIn(": held", self.lock_status(merge=True))
        env = self.runner_env()
        env.update(exports)
        env.update(merge_exports)
        proc = self.run_finalize(env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        # Both locks released and verified free.
        self.assertIn(": free", self.lock_status())
        self.assertIn(": free", self.lock_status(merge=True))
        self.assertIn("done lock status: free", proc.stdout)
        # The manifest finalized and the checkpoint removed.
        record = self.manifest_record(exports)
        self.assertTrue(record.get("complete", False))
        self.assertFalse(checkpoint.exists())
        self.assertIn("removed: checkpoint-manifest", proc.stdout)

    # ---- held-lock guidance (plan
    # docs/history/plans/2026-10-31-done-finalize-manifest-leg-post-removal-ordering.md
    # Task 2): when the done
    # lock survives the release attempts, the FAILED line is chosen from the
    # manifest state and the finalize's own refusal cause. The hold is kept
    # standing by controlled inputs, never by wall-clock delay or fixture
    # timestamp aging: a deliberately wrong done-lock token refuses every
    # env-token release, and the lock's staleness and dead-holder clocks are
    # pinned far beyond the test's lifetime so the held verdict cannot flip.

    def held_lock_clock_env(self) -> dict:
        return {
            "DONE_LOCK_STALE_SECS": "999999",
            "DONE_LOCK_DEAD_HOLDER_GRACE_SECS": "999999",
        }

    def held_lock_finalize_env(self, exports: dict) -> dict:
        """Finalize env under which the setup hold survives the release
        attempts: the correct lock dir beside a deliberately wrong token
        (the controlled lock-state input that refuses every env-token
        release) plus the pinned staleness clocks."""
        env = self.runner_env()
        env.update(exports)
        env["DONE_LOCK_TOKEN"] = "0" * 64  # never the setup hold's token
        env.update(self.held_lock_clock_env())
        return env

    def assert_held_done_lock(self, proc: subprocess.CompletedProcess) -> None:
        """The run reported the held done-lock state and the hold still
        stands after it."""
        self.assertIn("done lock status is not free after the release", proc.stderr)
        self.assertIn(": held", proc.stdout)  # the status evidence the run printed
        held = self.lock_invocation(
            "status", extra_env=self.held_lock_clock_env(),
        )
        self.assertIn(": held", held.stdout + held.stderr)

    def test_finalize_identity_refusal_with_held_lock_reports_without_full_retry(self) -> None:
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "refusal-fixture")
        manifest = Path(exports["DONE_RUN_MANIFEST"])
        # The post-removal refusal shape: a schema-valid manifest whose
        # recorded root is a foreign 64-hex fingerprint, so finalize-manifest
        # aborts named and leaves the bytes unchanged.
        self.rewrite_manifest(
            manifest, repo_root=hashlib.sha256(b"/elsewhere/repo").hexdigest(),
        )
        refused_bytes = manifest.read_bytes()
        proc = self.run_finalize(env=self.held_lock_finalize_env(exports))
        # The non-zero identity-refusal result is preserved and the manifest
        # stays byte-identical.
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("run-manifest identity mismatch", proc.stdout)
        self.assertIn("manifest left unchanged", proc.stdout)
        self.assertEqual(manifest.read_bytes(), refused_bytes)
        # The held done-lock state is reported with no full finalize retry
        # and no release-only advice after the identity refusal.
        self.assert_held_done_lock(proc)
        self.assertIn(
            "the finalize above refused this manifest's identity", proc.stderr,
        )
        self.assertNotIn("full finalize re-run", proc.stderr)
        self.assertNotIn("release-only retry", proc.stderr)

    def test_finalize_other_incomplete_cause_with_held_lock_keeps_full_retry(self) -> None:
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "incomplete-fixture")
        manifest = Path(exports["DONE_RUN_MANIFEST"])
        # Another incomplete-manifest cause, no identity refusal: the
        # session dir is read-only, so the finalize's own rewrite fails
        # named and the record stays incomplete.
        self.done_session().chmod(0o555)
        proc = self.run_finalize(env=self.held_lock_finalize_env(exports))
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("cannot rewrite the run manifest", proc.stdout)
        self.assertNotIn("run-manifest identity mismatch", proc.stdout)
        # The contrasting held-lock guidance keeps the full-retry advice.
        self.assert_held_done_lock(proc)
        self.assertIn("the run manifest is NOT complete", proc.stderr)
        self.assertIn("needs its full finalize re-run", proc.stderr)

    def test_finalize_identity_refusal_unreadable_manifest_routes_refusal_disposition(self) -> None:
        """[class: REPOSITORY_TEST] Residual wrapper#identity-arm-invalid-json-miss
        (the 2026-10-31 closeout-gates trio, landed 52750a1fe): an
        unparseable manifest makes the completion probe print `unknown`, and
        the held-lock guidance must still route to the refusal-specific
        disposition when the finalize above refused the manifest's identity,
        never to the generic unreadable arm."""
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "unreadable-fixture")
        manifest = Path(exports["DONE_RUN_MANIFEST"])
        manifest.write_text("{not json")
        # The re-run shape: --run-id keeps the run bound while the manifest
        # bytes are unparseable (the completion probe then prints `unknown`).
        proc = self.run_finalize(
            "--run-id", exports["DONE_RUN_ID"],
            env=self.held_lock_finalize_env(exports),
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("run-manifest identity mismatch", proc.stdout)
        self.assert_held_done_lock(proc)
        self.assertIn(
            "refused this manifest's identity (the manifest itself was "
            "unreadable)", proc.stderr,
        )
        self.assertNotIn("re-derive it from the manifest", proc.stderr)

    def test_finalize_marking_withheld_with_held_lock_never_claims_identity_refusal(self) -> None:
        """[class: REPOSITORY_TEST] Residual wrapper-hold-guard-untested
        (the 2026-10-31 closeout-gates trio, landed 52750a1fe): with the
        marking withheld by the deferred-squash guard, the held-lock guidance
        keeps the full-retry advice and the identity-refusal disposition never
        prints (the `marking_withheld -eq 0` guard pins the deferred-squash
        path to its own resume advice)."""
        self.init_fixture_repo()
        self.facts_with_base_branch()
        setup_proc, exports = self.setup_session("--label", "withheld-held-fixture")
        run_id = exports["DONE_RUN_ID"]
        self.git("checkout", "-qb", "run/withheld-held")
        (self.fixture / "work.txt").write_text("work\n")
        self.git("add", "work.txt")
        self.git("commit", "-qm", "run work")
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        self.write_ledger(run_id, landing)
        self.make_checkpoint(run_id)
        proc = self.run_finalize(env=self.held_lock_finalize_env(exports))
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("LANDING DEFERRED", proc.stderr)
        self.assert_held_done_lock(proc)
        self.assertIn("needs its full finalize re-run", proc.stderr)
        self.assertNotIn("refused this manifest's identity", proc.stderr)

    def test_finalize_completed_manifest_with_held_lock_keeps_release_only_retry(self) -> None:
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "completed-fixture")
        manifest = Path(exports["DONE_RUN_MANIFEST"])
        # A completed manifest: the finalize step has nothing left to mark,
        # so the only safe retry is release-only.
        self.rewrite_manifest(manifest, complete=True)
        proc = self.run_finalize(env=self.held_lock_finalize_env(exports))
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("already complete; nothing to do", proc.stdout)
        self.assertNotIn("run-manifest identity mismatch", proc.stdout)
        # The contrasting held-lock guidance keeps the release-only advice.
        self.assert_held_done_lock(proc)
        self.assertIn("the run manifest is complete", proc.stderr)
        self.assertIn("release-only retry", proc.stderr)
        self.assertNotIn("full finalize re-run", proc.stderr)

    # ---- deferred-squash honesty (backlog
    # 2026-10-26-finalize-deferred-squash-silent-success): a ledger landing
    # commit not on the base branch prints the loud deferral, names a branch
    # commit, and withholds the complete marking; a landed commit keeps the
    # current success shape.

    def facts_with_base_branch(self) -> str:
        base_branch = self.git("symbolic-ref", "--short", "HEAD").stdout.strip()
        facts = self.fixture / ".ai-playbook" / "facts.md"
        facts.write_text(facts.read_text() + f'base_branch = "{base_branch}"\n')
        return base_branch

    def write_ledger(self, run_id: str, landing: str) -> Path:
        ledger = self.done_session() / f"owned-commits-{run_id}.txt"
        ledger.parent.mkdir(parents=True, exist_ok=True)
        ledger.write_text(landing + "\n")
        return ledger

    def test_finalize_deferred_squash_loud_line_withholds_marking(self) -> None:
        self.init_fixture_repo()
        self.facts_with_base_branch()
        setup_proc, exports = self.setup_session("--label", "deferred-fixture")
        run_id = exports["DONE_RUN_ID"]
        # A run-branch landing commit the squash never carried to the base.
        self.git("checkout", "-qb", "run/deferred")
        (self.fixture / "work.txt").write_text("work\n")
        self.git("add", "work.txt")
        self.git("commit", "-qm", "run work")
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        self.write_ledger(run_id, landing)
        checkpoint = self.make_checkpoint(run_id)
        merge = self.lock_invocation("merge-acquire", "--label", "peer-landing-span")
        self.assertEqual(merge.returncode, 0, merge.stderr)
        env = self.runner_env()
        env.update(exports)
        env.update(self.eval_exports(merge.stdout))
        proc = self.run_finalize(env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("LANDING DEFERRED", proc.stderr)
        self.assertIn("peer-landing-span", proc.stderr)
        self.assertIn(
            f"re-run the bound finalize (finalize --run-id {run_id}) or "
            "the landing helper's land-worktree mode after the lock frees",
            proc.stderr,
        )
        self.assertIn(f"the branch tip is {landing}", proc.stderr)
        self.assertIn("complete marking withheld", proc.stdout)
        # The summary names a branch commit, never landing_commit=.
        self.assertIn(f"branch_commit={landing}", proc.stdout)
        self.assertIn("squash pending", proc.stdout)
        self.assertNotIn("landing_commit=", proc.stdout)
        # The manifest stays incomplete and the checkpoint stays for resume.
        record = self.manifest_record(exports)
        self.assertFalse(record.get("complete", False))
        self.assertTrue(checkpoint.exists())
        # The release ceremony still ran to its status-free verification.
        self.assertIn(": free", self.lock_status())
        self.assertIn(": free", self.lock_status(merge=True))
        self.assertIn("done lock status: free", proc.stdout)

    def test_finalize_rerun_after_squash_lands_consumes_withheld_state(self) -> None:
        self.init_fixture_repo()
        base_branch = self.facts_with_base_branch()
        setup_proc, exports = self.setup_session("--label", "resume-fixture")
        run_id = exports["DONE_RUN_ID"]
        self.git("checkout", "-qb", "run/resume")
        (self.fixture / "work.txt").write_text("work\n")
        self.git("add", "work.txt")
        self.git("commit", "-qm", "run work")
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        self.write_ledger(run_id, landing)
        checkpoint = self.make_checkpoint(run_id)
        # First finalize: the squash has not run, so the marking is withheld
        # and the checkpoint is kept.
        merge = self.lock_invocation("merge-acquire", "--label", "peer-landing-span")
        self.assertEqual(merge.returncode, 0, merge.stderr)
        env = self.runner_env()
        env.update(exports)
        env.update(self.eval_exports(merge.stdout))
        first = self.run_finalize(env=env)
        self.assertEqual(first.returncode, 0, first.stderr + first.stdout)
        self.assertIn("LANDING DEFERRED", first.stderr)
        record = self.manifest_record(exports)
        self.assertFalse(record.get("complete", False))
        self.assertTrue(checkpoint.exists())
        # The squash lands (tree-equal base commit) and the run resumes: a
        # fresh done-lock hold stands in for the resume session's setup, and
        # the re-run finalize consumes the withheld state.
        tree = self.git("rev-parse", f"{landing}^{{tree}}").stdout.strip()
        base_tip = self.git("rev-parse", base_branch).stdout.strip()
        squash = self.git("commit-tree", tree, "-p", base_tip, "-m", "squash").stdout.strip()
        self.git("update-ref", f"refs/heads/{base_branch}", squash, base_tip)
        acq = self.lock_invocation("acquire", "--label", "resume-session")
        self.assertEqual(acq.returncode, 0, acq.stderr)
        resume_env = self.runner_env()
        resume_env.update(self.eval_exports(acq.stdout))
        # The resume re-run re-derives its binding: the agreeing DONE_RUN_ID
        # export (plan docs/history/plans/2026-11-02-done-finalize-resume-
        # marking-honesty.md Task 2) — the fresh hold's lock exports alone
        # are never binding evidence.
        resume_env["DONE_RUN_ID"] = run_id
        second = self.run_finalize(env=resume_env)
        self.assertEqual(second.returncode, 0, second.stderr + second.stdout)
        self.assertNotIn("LANDING DEFERRED", second.stderr)
        self.assertIn(f"landing_commit={landing}", second.stdout)
        record = self.manifest_record(exports)
        self.assertTrue(record.get("complete", False))
        self.assertFalse(checkpoint.exists())
        self.assertIn(": free", self.lock_status())

    def test_finalize_landed_landing_keeps_current_success_shape(self) -> None:
        self.init_fixture_repo()
        self.facts_with_base_branch()
        setup_proc, exports = self.setup_session("--label", "landed-fixture")
        run_id = exports["DONE_RUN_ID"]
        # The primary-placement shape: the landing commit sits on the base.
        (self.fixture / "work.txt").write_text("work\n")
        self.git("add", "work.txt")
        self.git("commit", "-qm", "direct base work")
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        self.write_ledger(run_id, landing)
        checkpoint = self.make_checkpoint(run_id)
        env = self.runner_env()
        env.update(exports)
        proc = self.run_finalize(env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertNotIn("LANDING DEFERRED", proc.stderr)
        self.assertIn(f"landing_commit={landing}", proc.stdout)
        record = self.manifest_record(exports)
        self.assertTrue(record.get("complete", False))
        self.assertFalse(checkpoint.exists())

    def test_finalize_squash_proof_tree_match_keeps_success_shape(self) -> None:
        self.init_fixture_repo()
        base_branch = self.facts_with_base_branch()
        setup_proc, exports = self.setup_session("--label", "squashed-fixture")
        run_id = exports["DONE_RUN_ID"]
        self.git("checkout", "-qb", "run/squashed")
        (self.fixture / "work.txt").write_text("work\n")
        self.git("add", "work.txt")
        self.git("commit", "-qm", "run work")
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        self.write_ledger(run_id, landing)
        checkpoint = self.make_checkpoint(run_id)
        # The squash landing the ancestry check cannot see: a base-branch
        # commit carrying the run branch tip's tree (the squash proof arm).
        tree = self.git("rev-parse", f"{landing}^{{tree}}").stdout.strip()
        base_tip = self.git("rev-parse", base_branch).stdout.strip()
        squash = self.git("commit-tree", tree, "-p", base_tip, "-m", "squash").stdout.strip()
        self.git("update-ref", f"refs/heads/{base_branch}", squash, base_tip)
        env = self.runner_env()
        env.update(exports)
        proc = self.run_finalize(env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertNotIn("LANDING DEFERRED", proc.stderr)
        self.assertIn(f"landing_commit={landing}", proc.stdout)
        record = self.manifest_record(exports)
        self.assertTrue(record.get("complete", False))
        self.assertFalse(checkpoint.exists())

    def test_finalize_rebased_squash_proof_patch_id_match_keeps_success_shape(self) -> None:
        self.init_fixture_repo()
        base_branch = self.facts_with_base_branch()
        setup_proc, exports = self.setup_session("--label", "rebased-fixture")
        run_id = exports["DONE_RUN_ID"]
        # The facts append is a tracked-file edit; commit it so the later
        # rebase runs against a clean tree.
        self.git("add", ".ai-playbook/facts.md")
        self.git("commit", "-qm", "record the base branch fact")
        self.git("checkout", "-qb", "run/rebased")
        (self.fixture / "work.txt").write_text("work\n")
        self.git("add", "work.txt")
        self.git("commit", "-qm", "run work")
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        self.write_ledger(run_id, landing)
        checkpoint = self.make_checkpoint(run_id)
        # The witnessed rebased-landing shape: the base advances, the run
        # branch rebases onto it before the squash, and the ledger keeps the
        # pre-rebase sha. Ancestry and the tree-identity fast path both miss;
        # the first-parent delta patch-id of the landing commit matches the
        # branch delta, so the squash still proves landed.
        self.git("checkout", base_branch)
        (self.fixture / "other.txt").write_text("other\n")
        self.git("add", "other.txt")
        self.git("commit", "-qm", "base advance")
        self.git("checkout", "run/rebased")
        self.git("rebase", base_branch)
        rebased_tree = self.git("rev-parse", "HEAD^{tree}").stdout.strip()
        base_tip = self.git("rev-parse", base_branch).stdout.strip()
        squash = self.git("commit-tree", rebased_tree, "-p", base_tip, "-m", "squash").stdout.strip()
        self.git("update-ref", f"refs/heads/{base_branch}", squash, base_tip)
        env = self.runner_env()
        env.update(exports)
        proc = self.run_finalize(env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertNotIn("LANDING DEFERRED", proc.stderr)
        self.assertIn(f"landing_commit={landing}", proc.stdout)
        record = self.manifest_record(exports)
        self.assertTrue(record.get("complete", False))
        self.assertFalse(checkpoint.exists())

    def test_finalize_unresolvable_base_skips_honesty_check_with_complete_marking(self) -> None:
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "failopen-fixture")
        run_id = exports["DONE_RUN_ID"]
        # A ledger landing commit with a base that cannot resolve: the
        # fixture facts carry no base_branch key and no origin/HEAD exists,
        # so the honesty check fails open to the success shape.
        self.git("checkout", "-qb", "run/failopen")
        (self.fixture / "work.txt").write_text("work\n")
        self.git("add", "work.txt")
        self.git("commit", "-qm", "run work")
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        self.write_ledger(run_id, landing)
        checkpoint = self.make_checkpoint(run_id)
        env = self.runner_env()
        env.update(exports)
        proc = self.run_finalize(env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("the deferred-squash honesty check is skipped", proc.stderr)
        self.assertIn(f"landing_commit={landing}", proc.stdout)
        record = self.manifest_record(exports)
        self.assertTrue(record.get("complete", False))
        self.assertFalse(checkpoint.exists())

    def test_finalize_origin_head_fallback_defers_naming_short_branch(self) -> None:
        self.init_fixture_repo()
        base_branch = self.git("symbolic-ref", "--short", "HEAD").stdout.strip()
        setup_proc, exports = self.setup_session("--label", "origin-head-fixture")
        run_id = exports["DONE_RUN_ID"]
        self.git("checkout", "-qb", "run/origin-head")
        (self.fixture / "work.txt").write_text("work\n")
        self.git("add", "work.txt")
        self.git("commit", "-qm", "run work")
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        self.write_ledger(run_id, landing)
        checkpoint = self.make_checkpoint(run_id)
        # The facts key is absent but origin/HEAD carries the base: the
        # deferred shape still resolves and names the short-name branch.
        base_tip = self.git("rev-parse", base_branch).stdout.strip()
        self.git("update-ref", f"refs/remotes/origin/{base_branch}", base_tip)
        self.git("symbolic-ref", "refs/remotes/origin/HEAD",
                 f"refs/remotes/origin/{base_branch}")
        env = self.runner_env()
        env.update(exports)
        proc = self.run_finalize(env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("LANDING DEFERRED", proc.stderr)
        self.assertIn(f"the squash to {base_branch} has not landed", proc.stderr)
        self.assertIn(f"branch_commit={landing}", proc.stdout)
        self.assertNotIn("landing_commit=", proc.stdout)
        record = self.manifest_record(exports)
        self.assertFalse(record.get("complete", False))
        self.assertTrue(checkpoint.exists())

    def test_finalize_guard_child_defers_after_marking_names_branch_commit(self) -> None:
        self.init_fixture_repo()
        self.facts_with_base_branch()
        setup_proc, exports = self.setup_session("--label", "child-corner-fixture")
        run_id = exports["DONE_RUN_ID"]
        self.git("checkout", "-qb", "run/childcorner")
        (self.fixture / "work.txt").write_text("work\n")
        self.git("add", "work.txt")
        self.git("commit", "-qm", "run work")
        # No owned-commits ledger yet, so the marking decision runs complete;
        # the guard-firing child commit appends the ledger's first line after
        # it and the summary recompute defers with the branch_commit naming.
        self.seed_tracked_guard_ledger()
        firing = f"description-length:catch:fixture-evidence:run_id={run_id}"
        env = self.commit_env()
        env.update(exports)
        proc = self.run_finalize("--guard-firing", firing, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("the complete marking above predates this ledger line", proc.stderr)
        # The second LANDING DEFERRED string's bound-form tail (Task 2's
        # documentation witness; the 2026-11-05 task-2 review's N3).
        self.assertIn(
            "re-run the bound finalize (finalize --run-id " + run_id
            + ") or the landing helper's land-worktree mode after the "
            "squash lands",
            proc.stderr,
        )
        self.assertIn("branch_commit=", proc.stdout)
        self.assertIn("squash pending", proc.stdout)
        self.assertNotIn("landing_commit=", proc.stdout)
        record = self.manifest_record(exports)
        self.assertTrue(record.get("complete", False))
        self.assertIn(": free", self.lock_status())

    def test_finalize_squash_proof_window_bound_pins_500_commit_scan(self) -> None:
        self.init_fixture_repo()
        base_branch = self.facts_with_base_branch()
        setup_proc, exports = self.setup_session("--label", "window-fixture")
        run_id = exports["DONE_RUN_ID"]
        self.git("checkout", "-qb", "run/window")
        (self.fixture / "work.txt").write_text("work\n")
        self.git("add", "work.txt")
        self.git("commit", "-qm", "run work")
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        self.write_ledger(run_id, landing)
        checkpoint = self.make_checkpoint(run_id)
        # The squash lands as a tree-equal base commit, then the base
        # advances 501 distinct-tree commits so the squash falls outside the
        # 500-commit window both proof scans bound: the deferral stands and
        # the window is pinned, not undocumented.
        tree = self.git("rev-parse", f"{landing}^{{tree}}").stdout.strip()
        base_tip = self.git("rev-parse", base_branch).stdout.strip()
        squash = self.git("commit-tree", tree, "-p", base_tip, "-m", "squash").stdout.strip()
        self.git("update-ref", f"refs/heads/{base_branch}", squash, base_tip)
        self.git("checkout", base_branch)
        marker = self.fixture / "advance.txt"
        for i in range(501):
            marker.write_text(f"advance {i}\n")
            self.git("add", "advance.txt")
            self.git("commit", "-qm", f"advance {i}")
        env = self.runner_env()
        env.update(exports)
        proc = self.run_finalize(env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("LANDING DEFERRED", proc.stderr)
        self.assertIn(f"branch_commit={landing}", proc.stdout)
        record = self.manifest_record(exports)
        self.assertFalse(record.get("complete", False))
        self.assertTrue(checkpoint.exists())

    def test_finalize_from_holder_accepts_a_verifiably_alive_recorded_holder(self) -> None:
        # The recorded holder is this pytest process: the finalize child shell
        # descends from it, so the lock script's from-holder ancestry gate
        # passes exactly per the sibling plan's recorded guards (pinned hold,
        # same host, holder alive with exact identity, not pid 1, ancestry).
        self.init_fixture_repo()
        env = self.runner_env()
        env["DONE_LOCK_HOLD_PIN"] = "1"
        env["DONE_LOCK_HOLDER_PID"] = str(os.getpid())
        env["MERGE_LOCK_HOLD_PIN"] = "1"
        env["MERGE_LOCK_HOLDER_PID"] = str(os.getpid())
        setup_proc = subprocess.run(
            ["bash", str(RUNNER), "setup", "--label", "from-holder-fixture"],
            cwd=str(self.fixture), env=env,
            capture_output=True, text=True, timeout=300,
        )
        self.assertEqual(setup_proc.returncode, 0, setup_proc.stderr)
        exports = self.eval_exports(setup_proc.stdout)
        run_id = exports["DONE_RUN_ID"]
        self.make_checkpoint(run_id)
        # A surviving merge-lock hold, pinned the same way; the finalize env
        # carries no lock exports at all (the exports-lost case).
        merge = self.lock_invocation(
            "merge-acquire", "--label", "fixture-merge-span",
            extra_env={"MERGE_LOCK_HOLD_PIN": "1", "MERGE_LOCK_HOLDER_PID": str(os.getpid())},
        )
        self.assertEqual(merge.returncode, 0, merge.stderr)
        lost_env = self.runner_env()
        for var in ("DONE_LOCK_DIR", "DONE_LOCK_TOKEN", "MERGE_LOCK_DIR", "MERGE_LOCK_TOKEN"):
            lost_env.pop(var, None)
        # The env-lost re-run keeps its run binding through the agreeing
        # DONE_RUN_ID export (plan docs/history/plans/2026-11-02-done-
        # finalize-resume-marking-honesty.md Task 2); the lock exports are
        # absent either way and never bind.
        lost_env["DONE_RUN_ID"] = run_id
        proc = self.run_finalize("--from-holder", env=lost_env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("from-holder", proc.stdout + proc.stderr)
        self.assertIn(": free", self.lock_status())
        self.assertIn(": free", self.lock_status(merge=True))
        record = self.manifest_record(exports)
        self.assertTrue(record.get("complete", False))
        # The unbound-resolution refusal composition (Task 2): the same
        # env-lost re-run without any binding evidence refuses fail-loud,
        # leaves the completed record untouched, and still runs the releases
        # over the already-free locks.
        unbound = self.run_finalize(env=self.runner_env())
        self.assertNotEqual(unbound.returncode, 0)
        self.assertIn("unbound-resolution refusal", unbound.stderr)
        self.assertEqual(
            self.finalization_lines(unbound),
            ["done_run finalize: finalization: run_id=unbound marking=refused"],
        )
        self.assertIn(": free", self.lock_status())
        self.assertIn(": free", self.lock_status(merge=True))
        self.assertIn("done lock status: free", unbound.stdout)
        self.assertTrue(self.manifest_record(exports).get("complete", False))

    def test_finalize_reports_missing_review_records_report_only(self) -> None:
        self.init_fixture_repo()
        plans_completed = self.fixture / "docs" / "history" / "plans" / "completed"
        plans_completed.mkdir(parents=True)
        (plans_completed / "2026-10-11-cited-plan.md").write_text(
            "# Plan\n\nreview record: 2026-10-11-cited-plan-review-fixture-exec-r1.md\n",
            encoding="utf-8",
        )
        setup_proc, exports = self.setup_session("--label", "scan-fixture")
        env = self.runner_env()
        env.update(exports)
        proc = self.run_finalize(env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("missing-review-record: 2026-10-11-cited-plan-review-fixture-exec-r1.md", proc.stdout)
        self.assertIn("never fabricate, never block, never delete", proc.stdout)
        # The landing-cost telemetry stays advisory-absent when nothing landed.
        self.assertNotIn("landing-cost telemetry appended", proc.stdout)

    # ---- reviews-corpus rooting (plan
    #      docs/history/plans/2026-10-29-done-finalize-missing-record-scan-
    #      primary-corpus-root.md): a relative reviews_dir resolves from the
    #      primary checkout, an absolute reviews_dir keeps its configured
    #      path, and plans_completed_dir stays rooted at the running
    #      checkout; the scan summary names the corpus root it used and the
    #      scan stays report-only. --------------------------------------- #

    def add_scan_worktree(self, branch: str) -> Path:
        """A linked worktree becomes the fixture root (the scan's running
        checkout); the caller seeds the primary before calling this when the
        worktree must inherit the seed."""
        worktree = self.tmp / "worktree"
        self.git("worktree", "add", "-qb", branch, str(worktree))
        self.fixture = worktree
        return worktree

    def git_reported_primary(self) -> Path:
        """The primary checkout exactly as the scan derives it: the first
        worktree line of git worktree list --porcelain (git itself prints the
        realpath; Path() here performs no symlink resolution)."""
        return Path(
            self.git("worktree", "list", "--porcelain").stdout.splitlines()[0]
            [len("worktree "):]
        )

    def finalize_from_fixture(
        self, label: str, *setup_args: str,
    ) -> subprocess.CompletedProcess:
        setup_proc, exports = self.setup_session("--label", label, *setup_args)
        env = self.runner_env()
        env.update(exports)
        return self.run_finalize(env=env)

    def test_finalize_scan_in_worktree_resolves_reviews_corpus_at_primary(self) -> None:
        # The cited record exists only in the primary corpus; the worktree's
        # transfer-in copy is partial (development lesson 74), so a
        # running-checkout resolution would over-report it missing.
        primary = self.init_fixture_repo()
        plans_completed = primary / "docs" / "history" / "plans" / "completed"
        plans_completed.mkdir(parents=True)
        (plans_completed / "2026-10-11-cited-plan.md").write_text(
            "# Plan\n\nreview record: 2026-10-11-primary-home-plan-review-fixture-exec-r1.md\n",
            encoding="utf-8",
        )
        reviews = primary / ".ai-playbook" / "reviews"
        reviews.mkdir()
        (reviews / "2026-10-11-primary-home-plan-review-fixture-exec-r1.md").write_text(
            "# review record\n", encoding="utf-8",
        )
        self.git("add", "docs/history/plans/completed")
        self.git("commit", "-qm", "cite the primary-only review record")
        self.add_scan_worktree("feature/scan-primary-corpus")
        primary = self.git_reported_primary()
        wt_reviews = self.fixture / ".ai-playbook" / "reviews"
        wt_reviews.mkdir(parents=True)
        (wt_reviews / "2026-10-11-worktree-side-code-review-fixture-r2.md").write_text(
            "# worktree-side record\n", encoding="utf-8",
        )
        # The run owns no staging doc, so the partial copy's worktree-side
        # record bulk-answers foreign at Step 0 and the scan stays the
        # behavior under test.
        proc = self.finalize_from_fixture("scan-worktree", "--claim-none")
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertNotIn(
            "missing-review-record: 2026-10-11-primary-home-plan-review-fixture-exec-r1.md",
            proc.stdout,
        )
        self.assertIn(
            f"missing-review-record scan: 0 missing record(s)"
            f" corpus_root={primary}/.ai-playbook/reviews/",
            proc.stdout,
        )

    def test_finalize_scan_keeps_absolute_reviews_dir_at_its_configured_root(self) -> None:
        primary = self.init_fixture_repo()
        alternate = self.tmp / "alternate-reviews"
        alternate.mkdir()
        record = "2026-10-11-alt-home-plan-review-fixture-exec-r1.md"
        (alternate / record).write_text("# alternate-corpus record\n", encoding="utf-8")
        (primary / ".ai-playbook" / "facts.md").write_text(
            "```toml\n"
            'plans_dir = "docs/history/plans/"\n'
            'backlog_dir = "docs/history/backlog/"\n'
            f'reviews_dir = "{alternate}"\n'
            'tmp_dir = "docs/tmp/"\n'
            'metrics_dir = "docs/tmp/metrics/"\n'
            'review_certs_dir = ".ai-playbook/review-certs/"\n'
            "```\n",
            encoding="utf-8",
        )
        plans_completed = primary / "docs" / "history" / "plans" / "completed"
        plans_completed.mkdir(parents=True)
        (plans_completed / "2026-10-11-alt-cited-plan.md").write_text(
            f"# Plan\n\nreview record: {record}\n", encoding="utf-8",
        )
        proc = self.finalize_from_fixture("scan-absolute")
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertNotIn(f"missing-review-record: {record}", proc.stdout)
        self.assertIn(
            f"missing-review-record scan: 0 missing record(s) corpus_root={alternate}",
            proc.stdout,
        )

    def test_finalize_scan_scans_completed_plans_at_the_running_checkout(self) -> None:
        # The citing plan exists only under the running checkout (the linked
        # worktree), so the scanned citation proves plans_completed_dir stayed
        # rooted there; the missing record stays a report-only warning.
        primary = self.init_fixture_repo()
        worktree = self.add_scan_worktree("feature/scan-running-checkout")
        primary = self.git_reported_primary()
        # Pin the facts-backed arm: the shared template leaves
        # plans_completed_dir unset, but the real repo sets it, so production
        # resolves this value through facts_rooted; exercise that path.
        # The scan reads facts from the RUNNING checkout (repo_top), which
        # for this fixture is the linked worktree, not the primary.
        facts = worktree / ".ai-playbook" / "facts.md"
        facts.write_text(
            facts.read_text(encoding="utf-8").replace(
                'tmp_dir = "docs/tmp/"',
                'plans_completed_dir = "docs/history/plans/completed/"\n'
                'tmp_dir = "docs/tmp/"',
            ),
            encoding="utf-8",
        )
        plans_completed = worktree / "docs" / "history" / "plans" / "completed"
        plans_completed.mkdir(parents=True)
        (plans_completed / "2026-10-11-worktree-only-plan.md").write_text(
            "# Plan\n\nreview record: 2026-10-11-never-copied-plan-review-fixture-exec-r1.md\n",
            encoding="utf-8",
        )
        proc = self.finalize_from_fixture("scan-running")
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn(
            "missing-review-record: 2026-10-11-never-copied-plan-review-fixture-exec-r1.md",
            proc.stdout,
        )
        self.assertIn("never fabricate, never block, never delete", proc.stdout)
        self.assertIn(
            f"missing-review-record scan: 1 missing record(s)"
            f" corpus_root={primary}/.ai-playbook/reviews/",
            proc.stdout,
        )

    # ---- guard-firing placement (plan docs/history/plans/2026-10-24-done-
    #      run-lock-span-and-append-ordering): landing-carried rows are never
    #      appended twice; with no prior landing the rows land through the
    #      checked commit subcommand as a child while the parent holds the
    #      done lock; both child failure arms restore or preserve as the plan
    #      fixes, and the release and status checks always run. ------------- #

    def seed_tracked_guard_ledger(self, payload: str | None = None) -> Path:
        ledger = self.fixture / "scripts" / "gate_liveness_ledger.json"
        ledger.parent.mkdir(parents=True, exist_ok=True)
        if payload is None:
            payload = json.dumps(
                {"schema": 1, "window": {"started": "2026-10-05"}, "guards": {}}
            )
        ledger.write_text(payload)
        self.git("add", "scripts/gate_liveness_ledger.json")
        self.git("commit", "-qm", "seed the guard-liveness ledger")
        return ledger

    def committed_ledger_text(self) -> str:
        return self.git("show", "HEAD:scripts/gate_liveness_ledger.json").stdout

    def matching_ledger_rows(self, evidence: str, committed: bool = False) -> list[dict]:
        text = self.committed_ledger_text() if committed else (
            self.fixture / "scripts" / "gate_liveness_ledger.json"
        ).read_text()
        doc = json.loads(text)
        return [
            row
            for guard in doc["guards"].values()
            for row in guard["rows"]
            if row.get("evidence") == evidence
        ]

    def committed_row_release_stub(self) -> Path:
        """A stub done-lock whose release-repo refuses unless HEAD's committed
        ledger already carries the fixture row: a passing finalize proves the
        fallback child commit landed before the release ran, while the parent
        still held the done lock. After the check the release is forwarded to
        the real lock script (the same env-token arm), so the fixture's hold
        is genuinely released. The sync's runner-owned merge span is satisfied
        with inert exports, since the fallback child's docs-branch sync
        resolves this same script for its merge acquire and release."""
        stub = self.tmp / "committed-row-lock.sh"
        merge_dir = self.tmp / "stub-merge-lock"
        stub.write_text(
            "#!/usr/bin/env bash\n"
            'LEDGER_REL="scripts/gate_liveness_ledger.json"\n'
            f'MERGE_DIR="{merge_dir}"\n'
            f'REAL_LOCK="{LOCK_SCRIPT}"\n'
            'case "$1" in\n'
            "  release-repo)\n"
            '    if ! git show "HEAD:$LEDGER_REL" 2>/dev/null | grep -q "run_id="; then\n'
            '      echo "stub: no committed guard-liveness row at release time" >&2\n'
            '      echo "OUTCOME: fail"\n'
            "      exit 2\n"
            "    fi\n"
            '    bash "$REAL_LOCK" release-repo\n'
            '    echo "stub: released after the ledger row was committed"\n'
            '    echo "OUTCOME: pass" ;;\n'
            "  merge-wait-acquire)\n"
            '    echo "export MERGE_LOCK_DIR=$MERGE_DIR"\n'
            '    echo "export MERGE_LOCK_TOKEN=stub-merge-token"\n'
            '    echo "OUTCOME: pass" ;;\n'
            "  merge-release)\n"
            '    echo "OUTCOME: pass" ;;\n'
            '  merge-status) echo "stub merge-lock: free" ;;\n'
            '  status) echo "stub done-lock: free" ;;\n'
            '  *) echo "OUTCOME: pass" ;;\n'
            "esac\n",
            encoding="utf-8",
        )
        stub.chmod(0o755)
        return stub

    def test_landing_carried_rows_never_appended_twice(self) -> None:
        self.init_fixture_repo(branch="feature/PROJ-1234-done-run")
        self.seed_tracked_guard_ledger()
        (self.fixture / "work.txt").write_text("session work\n")
        setup_proc, exports = self.setup_session("--owned-path", "work.txt")
        run_id = exports["DONE_RUN_ID"]
        firing = f"description-length:catch:fixture-evidence:run_id={run_id}"
        proc = self.commit_session(
            setup_proc, exports,
            "--stage", "work.txt", "--guard-firing", firing,
            "--subject", "land work and the guard firing",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(len(self.matching_ledger_rows("fixture-evidence")), 1)
        env = self.commit_env()
        env.update(exports)
        finalize_proc = self.run_finalize("--guard-firing", firing, env=env)
        self.assertEqual(
            finalize_proc.returncode, 0, finalize_proc.stderr + finalize_proc.stdout
        )
        self.assertIn(
            "never appended twice after a successful landing", finalize_proc.stdout
        )
        self.assertEqual(len(self.matching_ledger_rows("fixture-evidence")), 1)
        self.assertEqual(
            self.git(
                "status", "--porcelain", "--", "scripts/gate_liveness_ledger.json"
            ).stdout,
            "",
        )
        self.assertIn(": free", self.lock_status())

    def test_carried_arm_verifies_evidence_in_landing_bytes(self) -> None:
        # r1 residual item 2: the carried claim is verified against the
        # landing commit's ledger bytes before printing. A metacharacter
        # evidence pins the fixed-string match; an absent evidence pins the
        # not-verified variant.
        self.init_fixture_repo(branch="feature/PROJ-1234-done-run")
        self.seed_tracked_guard_ledger()
        (self.fixture / "work.txt").write_text("session work\n")
        setup_proc, exports = self.setup_session("--owned-path", "work.txt")
        run_id = exports["DONE_RUN_ID"]
        metachar_firing = f"description-length:catch:ev-with[0]brackets:run_id={run_id}"
        absent_firing = f"description-length:catch:absent-evidence:run_id={run_id}"
        proc = self.commit_session(
            setup_proc, exports,
            "--stage", "work.txt", "--guard-firing", metachar_firing,
            "--subject", "land work and the metachar guard firing",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(len(self.matching_ledger_rows("ev-with[0]brackets")), 1)
        env = self.commit_env()
        env.update(exports)
        verified = self.run_finalize("--guard-firing", metachar_firing, env=env)
        self.assertEqual(verified.returncode, 0, verified.stderr + verified.stdout)
        self.assertIn(
            "guard-liveness rows verified in this run's landing commit",
            verified.stdout,
        )
        self.assertNotIn("not verified as carried", verified.stdout + verified.stderr)
        unverified = self.run_finalize("--guard-firing", absent_firing, env=env)
        self.assertEqual(unverified.returncode, 0, unverified.stderr + unverified.stdout)
        self.assertIn("not verified as carried", unverified.stderr)
        self.assertIn(": free", self.lock_status())

    def test_fallback_child_lands_row_under_parent_lock(self) -> None:
        self.init_fixture_repo(branch="feature/PROJ-1234-done-run")
        self.seed_tracked_guard_ledger()
        setup_proc, exports = self.setup_session("--label", "fallback-child-fixture")
        run_id = exports["DONE_RUN_ID"]
        firing = f"description-length:catch:fixture-evidence:run_id={run_id}"
        count_before = self.commit_count()
        env = self.commit_env()
        env.update(exports)
        env["DONE_LOCK_SCRIPT"] = str(self.committed_row_release_stub())
        proc = self.run_finalize("--guard-firing", firing, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        # The release only succeeded because the child's landing had already
        # committed the row: the child ran while the parent held the lock.
        self.assertIn("released after the ledger row was committed", proc.stdout)
        self.assertIn("done lock status: free", proc.stdout)
        self.assertEqual(self.commit_count(), count_before + 1)
        rows = self.matching_ledger_rows("fixture-evidence", committed=True)
        self.assertEqual(len(rows), 1, "exactly one committed matching row")
        self.assertEqual(rows[0]["kind"], "catch")
        self.assertIn(f"run_id={run_id}", rows[0]["note"])
        # no post-landing tracked dirt: the worktree ledger matches the commit
        self.assertEqual(
            self.git(
                "status", "--porcelain", "--", "scripts/gate_liveness_ledger.json"
            ).stdout,
            "",
        )
        self.assertIn(": free", self.lock_status())

    def test_precommit_child_failure_restores_prior_bytes_and_index(self) -> None:
        self.init_fixture_repo(branch="feature/PROJ-1234-done-run")
        self.seed_tracked_guard_ledger()
        hook = self.fixture / ".git" / "hooks" / "pre-commit"
        hook.parent.mkdir(parents=True, exist_ok=True)
        hook.write_text("#!/bin/sh\nexit 1\n")
        hook.chmod(0o755)
        setup_proc, exports = self.setup_session("--label", "child-precommit-fail")
        run_id = exports["DONE_RUN_ID"]
        firing = f"description-length:catch:fixture-evidence:run_id={run_id}"
        count_before = self.commit_count()
        seed_bytes = (self.fixture / "scripts" / "gate_liveness_ledger.json").read_text()
        env = self.commit_env()
        env.update(exports)
        proc = self.run_finalize("--guard-firing", firing, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        combined = proc.stdout + proc.stderr
        self.assertIn("child commit failed", combined)
        self.assertIn("prior ledger bytes and index were restored", combined)
        self.assertEqual(
            self.commit_count(), count_before,
            "nothing may land past the failing pre-commit hook",
        )
        self.assertEqual(self.matching_ledger_rows("fixture-evidence", committed=True), [])
        self.assertEqual(
            (self.fixture / "scripts" / "gate_liveness_ledger.json").read_text(),
            seed_bytes,
            "the prior ledger bytes were restored",
        )
        self.assertEqual(self.git("diff", "--cached", "--name-only").stdout, "")
        self.assertIn(": free", self.lock_status())
        self.assertIn("done lock status: free", proc.stdout)

    def test_unborn_head_child_failure_routes_to_restore_arm(self) -> None:
        # done-run-lock-span r1 residual: an empty child_pre_head (unborn
        # HEAD) routed a pre-landing child failure into the after-landing
        # preserve arm under a misleading message; the guard routes empty
        # pre+post to the restore arm. Setup requires a resolvable HEAD, so
        # the fixture deletes the branch ref after setup to reach the shape.
        self.init_fixture_repo(branch="feature/PROJ-1234-done-run")
        self.seed_tracked_guard_ledger()
        setup_proc, exports = self.setup_session("--label", "child-unborn-head")
        self.git("update-ref", "-d", "refs/heads/feature/PROJ-1234-done-run")
        # No hook injection: on unborn HEAD the child dies at the captured
        # landing's HEAD resolution before any hook would run; the failure is
        # the unborn shape itself.
        firing = f"description-length:catch:fixture-evidence:run_id={exports['DONE_RUN_ID']}"
        seed_bytes = (
            self.fixture / "scripts" / "gate_liveness_ledger.json"
        ).read_text(encoding="utf-8")
        env = self.commit_env()
        env.update(exports)
        proc = self.run_finalize("--guard-firing", firing, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        combined = proc.stdout + proc.stderr
        self.assertIn("child commit failed", combined)
        self.assertIn("prior ledger bytes and index were restored", combined)
        self.assertNotIn("after landing", combined)
        self.assertNotEqual(
            self.git("rev-parse", "--verify", "--quiet", "HEAD", check=False).returncode, 0,
            "nothing may land on the unborn branch",
        )
        self.assertEqual(
            (self.fixture / "scripts" / "gate_liveness_ledger.json").read_text(encoding="utf-8"),
            seed_bytes,
            "the prior ledger bytes were restored",
        )
        self.assertNotIn(
            "scripts/gate_liveness_ledger.json",
            self.git("diff", "--cached", "--name-only").stdout,
            "the child's staged ledger entry was reset",
        )
        self.assertIn(": free", self.lock_status())

    def test_postcommit_child_failure_preserves_committed_row(self) -> None:
        self.init_fixture_repo(branch="feature/PROJ-1234-done-run")
        self.seed_tracked_guard_ledger()
        setup_proc, exports = self.setup_session("--label", "child-postcommit-fail")
        run_id = exports["DONE_RUN_ID"]
        # The owned-commits ledger path is a directory: the child's fused
        # owned-commits append fails right after its ref update lands.
        (self.done_session() / f"owned-commits-{run_id}.txt").mkdir()
        firing = f"description-length:catch:fixture-evidence:run_id={run_id}"
        count_before = self.commit_count()
        env = self.commit_env()
        env.update(exports)
        proc = self.run_finalize("--guard-firing", firing, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        combined = proc.stdout + proc.stderr
        self.assertIn("after landing", combined)
        self.assertIn("preserved (no rollback)", combined)
        self.assertIn("the owned-commits ledger append failed", combined)
        self.assertEqual(
            self.commit_count(), count_before + 1,
            "the child's landing stands",
        )
        rows = self.matching_ledger_rows("fixture-evidence", committed=True)
        self.assertEqual(len(rows), 1, "the committed row is preserved")
        self.assertIn(f"run_id={run_id}", rows[0]["note"])
        self.assertEqual(
            self.git(
                "status", "--porcelain", "--", "scripts/gate_liveness_ledger.json"
            ).stdout,
            "",
        )
        self.assertIn(": free", self.lock_status())
        self.assertIn("done lock status: free", proc.stdout)

    def test_child_append_failure_warns_and_lock_releases(self) -> None:
        # A corrupt committed ledger: every record call fails (tool error),
        # the child's arm warns and stages nothing, the landing skips, and
        # the release and status checks still run.
        self.init_fixture_repo(branch="feature/PROJ-1234-done-run")
        self.seed_tracked_guard_ledger(payload="{not json")
        setup_proc, exports = self.setup_session("--label", "append-fail-fixture")
        env = self.commit_env()
        env.update(exports)
        proc = self.run_finalize(
            "--guard-firing",
            "description-length:catch:fixture-evidence:run_id=run-x",
            env=env,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn(
            "guard-firing append failed for description-length",
            proc.stdout + proc.stderr,
        )
        self.assertIn("no staged changes; landing commit skipped", proc.stdout)
        # The real lock released anyway: the append failure is warning-only.
        self.assertIn(": free", self.lock_status())
        self.assertIn("done lock status: free", proc.stdout)

    # ---- finalization-state line (plan
    #      docs/history/plans/2026-11-02-done-finalize-resume-marking-honesty.md
    #      Task 1): every exit that reaches the exit assembly prints exactly
    #      one `finalization: run_id=<id or none> marking=<...>` line whose
    #      value matches the classification the FAILED routing consumes; the
    #      resume duty rides the existing LANDING DEFERRED / do-not-rerun
    #      advice beside it, and the failed arm names the re-run form. ---- #

    def finalization_lines(self, proc: subprocess.CompletedProcess) -> list[str]:
        return [
            line for line in (proc.stdout + proc.stderr).splitlines()
            if line.startswith("done_run finalize: finalization: run_id=")
        ]

    def test_finalize_state_line_reports_applied_on_bound_success(self) -> None:
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "state-applied")
        run_id = exports["DONE_RUN_ID"]
        env = self.runner_env()
        env.update(exports)
        proc = self.run_finalize(env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("marked complete in", proc.stdout)
        self.assertEqual(
            self.finalization_lines(proc),
            [f"done_run finalize: finalization: run_id={run_id} marking=applied"],
        )

    def test_finalize_state_line_reports_already_complete_on_release_only_retry(self) -> None:
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "state-already")
        run_id = exports["DONE_RUN_ID"]
        # A completed manifest: this invocation applies nothing, so the line
        # names the already-complete outcome (a release-only retry).
        self.rewrite_manifest(Path(exports["DONE_RUN_MANIFEST"]), complete=True)
        env = self.runner_env()
        env.update(exports)
        proc = self.run_finalize(env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("already complete; nothing to do", proc.stdout)
        self.assertEqual(
            self.finalization_lines(proc),
            [
                f"done_run finalize: finalization: run_id={run_id} "
                "marking=already-complete"
            ],
        )

    def test_finalize_state_line_reports_withheld_besides_deferred_lines(self) -> None:
        self.init_fixture_repo()
        self.facts_with_base_branch()
        setup_proc, exports = self.setup_session("--label", "state-withheld")
        run_id = exports["DONE_RUN_ID"]
        # A run-branch landing commit the squash never carried to the base.
        self.git("checkout", "-qb", "run/state-withheld")
        (self.fixture / "work.txt").write_text("work\n")
        self.git("add", "work.txt")
        self.git("commit", "-qm", "run work")
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        self.write_ledger(run_id, landing)
        self.make_checkpoint(run_id)
        env = self.runner_env()
        env.update(exports)
        proc = self.run_finalize(env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        # The line composes beside the existing loud deferral, never replaces
        # it; the deferral's re-run form names the bound form (Task 2).
        self.assertIn("LANDING DEFERRED", proc.stderr)
        self.assertIn(
            f"re-run the bound finalize (finalize --run-id {run_id}) or "
            "the landing helper's land-worktree mode",
            proc.stderr,
        )
        self.assertIn("complete marking withheld", proc.stdout)
        self.assertEqual(
            self.finalization_lines(proc),
            [f"done_run finalize: finalization: run_id={run_id} marking=withheld"],
        )
        self.assertFalse(self.manifest_record(exports).get("complete", False))

    def test_finalize_state_line_reports_refused_beside_do_not_rerun_advice(self) -> None:
        # Release failure after a refused marking: the line's value matches
        # the classification the FAILED advice carries, and the existing
        # do-not-rerun advice stays the refused arm's duty.
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "state-refused")
        manifest = Path(exports["DONE_RUN_MANIFEST"])
        self.rewrite_manifest(
            manifest, repo_root=hashlib.sha256(b"/elsewhere/repo").hexdigest(),
        )
        proc = self.run_finalize(env=self.held_lock_finalize_env(exports))
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("run-manifest identity mismatch", proc.stdout)
        self.assert_held_done_lock(proc)
        self.assertIn(
            "the finalize above refused this manifest's identity", proc.stderr,
        )
        self.assertIn("do not re-run finalize from the primary checkout", proc.stderr)
        self.assertEqual(
            self.finalization_lines(proc),
            [
                "done_run finalize: finalization: run_id="
                f"{exports['DONE_RUN_ID']} marking=refused"
            ],
        )

    def test_finalize_identity_refusal_free_lock_reports_exact_refused_line(self) -> None:
        # The identity-refusal classification is lock-state-independent: with
        # the setup hold already released (a free status), the state line
        # still reads exactly `run_id=<id> marking=refused` — the refused
        # value is keyed on the finalize's own refusal, never on lock state,
        # and a re-keying of the refused value on the release outcome fails
        # the exact-line equality. (A pure reordering of the emission is not
        # caught here; the line's position is unwitnessed — r2 finding 3.)
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "identity-free")
        manifest = Path(exports["DONE_RUN_MANIFEST"])
        self.rewrite_manifest(
            manifest, repo_root=hashlib.sha256(b"/elsewhere/repo").hexdigest(),
        )
        self.release_setup_hold(exports)
        # The agreeing DONE_RUN_ID export binds the run (the unbound refusal
        # otherwise owns this env-lost shape before the finalize-manifest
        # identity check ever runs); the released hold keeps the status free.
        env = self.runner_env()
        env.update(exports)
        proc = self.run_finalize(env=env)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("run-manifest identity mismatch", proc.stdout)
        self.assertEqual(
            self.finalization_lines(proc),
            [
                "done_run finalize: finalization: run_id="
                f"{exports['DONE_RUN_ID']} marking=refused"
            ],
        )
        # The release ran to free: the classification never waited on it.
        self.assertIn("done lock status: free", proc.stdout)
        self.assertIn(": free", self.lock_status())
        self.assertIn(": free", self.lock_status(merge=True))

    def test_finalize_state_line_reports_failed_and_names_rerun_duty(self) -> None:
        # A non-identity finalize-manifest failure (the read-only-session
        # fixture shape): marking=failed plus the concrete re-run duty.
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "state-failed")
        run_id = exports["DONE_RUN_ID"]
        self.done_session().chmod(0o555)
        env = self.runner_env()
        env.update(exports)
        proc = self.run_finalize(env=env)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("cannot rewrite the run manifest", proc.stdout)
        self.assertNotIn("run-manifest identity mismatch", proc.stdout)
        self.assertEqual(
            self.finalization_lines(proc),
            [f"done_run finalize: finalization: run_id={run_id} marking=failed"],
        )
        self.assertIn(
            "re-run finalize to retry the run manifest marking", proc.stderr,
        )

    def test_finalize_state_line_not_bound_lib_note_names_run_id_arg(self) -> None:
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "state-libnote")
        # The lib's no-run-manifest note: the --run-id arg names a record the
        # session directory does not hold, so nothing was bound and the line
        # names the argument with marking=not-bound, exit 0 preserved.
        env = self.runner_env()
        env.update(exports)
        proc = self.run_finalize("--run-id", "ghost-run-id", env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("no run manifest found for run_id ghost-run-id", proc.stdout)
        self.assertEqual(
            self.finalization_lines(proc),
            ["done_run finalize: finalization: run_id=ghost-run-id marking=not-bound"],
        )

    def test_finalize_state_line_not_bound_resolves_nothing_exit_zero(self) -> None:
        # The resolves-nothing resolution (an empty done-session directory):
        # run_id=none, marking=not-bound, exit 0 preserved.
        self.init_fixture_repo()
        proc = self.run_finalize()
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("no run manifest from setup", proc.stdout)
        self.assertEqual(
            self.finalization_lines(proc),
            ["done_run finalize: finalization: run_id=none marking=not-bound"],
        )
        self.assertIn("done lock status: free", proc.stdout)

    def test_finalize_state_line_release_failure_preserves_applied_marking(self) -> None:
        # Release failure over an applied marking: the marking value stands
        # beside the release-failure FAILED advice with the non-zero exit
        # preserved.
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "state-rlfail-applied")
        run_id = exports["DONE_RUN_ID"]
        proc = self.run_finalize(env=self.held_lock_finalize_env(exports))
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("done-lock release refused", proc.stderr)
        self.assertIn("release-only retry", proc.stderr)
        self.assertTrue(self.manifest_record(exports).get("complete", False))
        self.assertEqual(
            self.finalization_lines(proc),
            [f"done_run finalize: finalization: run_id={run_id} marking=applied"],
        )

    def test_finalize_state_line_release_failure_preserves_already_complete(self) -> None:
        # Release failure over an already-complete marking: the marking value
        # stands beside the release-failure FAILED advice with the non-zero
        # exit preserved.
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "state-rlfail-already")
        run_id = exports["DONE_RUN_ID"]
        self.rewrite_manifest(Path(exports["DONE_RUN_MANIFEST"]), complete=True)
        proc = self.run_finalize(env=self.held_lock_finalize_env(exports))
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("already complete; nothing to do", proc.stdout)
        self.assertIn("release-only retry", proc.stderr)
        self.assertEqual(
            self.finalization_lines(proc),
            [
                f"done_run finalize: finalization: run_id={run_id} "
                "marking=already-complete"
            ],
        )

    def test_finalize_state_line_sanitizes_hostile_run_id_arg(self) -> None:
        # A hostile --run-id drives the emission through the sanitizer
        # (newline/CR/tab flattened first, class substitution, the 64-byte
        # cap): the state line stays exactly one line, so a raw-echo
        # regression (an embedded newline forging a second finalization line,
        # a metacharacter smuggled into the output) fails the list equality.
        # The expected form is derived from the real tr/sed/cut pipeline, not
        # restated from the sanitizer's comment.
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "state-hostile")
        hostile = (
            "a\nb\tc\rd e|f;g`h$i'j\"k(l)m&n*o+p,q.r-s" + "Z" * 70
        )
        expected = (
            "a-b-c-d?e?f?g?h?i?j?k?l?m?n?o?p?q.r-s" + "Z" * 27
        )
        env = self.runner_env()
        env.update(exports)
        proc = self.run_finalize("--run-id", hostile, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("no run manifest found for run_id", proc.stdout)
        self.assertEqual(
            self.finalization_lines(proc),
            [
                "done_run finalize: finalization: "
                f"run_id={expected} marking=not-bound"
            ],
        )

    def test_finalize_landing_deferred_advice_sanitizes_hostile_run_id(self) -> None:
        # The second emission surface: the LANDING DEFERRED re-run advice
        # interpolates the bound run id through the same sanitizer
        # (finalize_bound_advice_id), so a hostile --run-id cannot forge a
        # second advice line or smuggle metacharacters into the re-run form.
        self.init_fixture_repo()
        self.facts_with_base_branch()
        setup_proc, exports = self.setup_session("--label", "deferred-hostile")
        # No newline/CR/tab: the hostile bytes must survive as a single-line
        # ledger filename for the withholding arm to key on.
        hostile = "a b|c;d$e%f^g&h*i(j)k" + "Z" * 70
        expected = "a?b?c?d?e?f?g?h?i?j?k" + "Z" * 43
        self.git("checkout", "-qb", "run/deferred-hostile")
        (self.fixture / "work.txt").write_text("work\n")
        self.git("add", "work.txt")
        self.git("commit", "-qm", "run work")
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        self.write_ledger(hostile, landing)
        env = self.runner_env()
        env.update(exports)
        proc = self.run_finalize("--run-id", hostile, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("LANDING DEFERRED", proc.stderr)
        self.assertIn(
            f"re-run the bound finalize (finalize --run-id {expected}) or "
            "the landing helper's land-worktree mode",
            proc.stderr,
        )
        self.assertEqual(
            self.finalization_lines(proc),
            [
                "done_run finalize: finalization: "
                f"run_id={expected} marking=withheld"
            ],
        )

    # ---- unbound-resolution refusal (plan
    #      docs/history/plans/2026-11-02-done-finalize-resume-marking-honesty.md
    #      Task 2): a resolution that selects a manifest without binding
    #      evidence (an explicit --run-id, an explicit --manifest the
    #      resolver bound, or a non-empty DONE_RUN_ID agreeing with the
    #      selected manifest's run_id) refuses fail-loud before any
    #      checkpoint or finalize-manifest mutation on both non-explicit
    #      arms, names the re-derive-and-retry remedy without ever echoing
    #      the resolved id, skips the guard-firing and report steps with
    #      named warnings, and still runs the releases; lock exports are
    #      never binding evidence. ---- #

    PEER_ID = "20991231T235959Z-peer00000001"
    # A peer id sorting BELOW a real run id (UTC stamp + hex suffix), so the
    # newest-glob fallback selects the own record over this peer's.
    LOW_PEER_ID = "19991231T235959Z-peer00000001"

    def craft_confirmed_marker(self, name: str) -> Path:
        """A root-confirmed run-start marker at an arbitrary name: the
        content carries this fixture repo's root digest, so marker_confirms
        accepts it and the newest-name selection picks it."""
        top = self.git("rev-parse", "--show-toplevel").stdout.strip().rstrip("/")
        digest = hashlib.sha256(top.encode()).hexdigest()
        marker = self.done_session() / name
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(f"{int(time.time())} {digest} 424242\n")
        return marker

    def release_setup_hold(self, exports: dict) -> None:
        """Release the setup hold so an env-lost finalize's from-holder
        release arm sees no hold and the release steps report free."""
        released = self.lock_invocation("release-repo", extra_env=exports)
        self.assertEqual(released.returncode, 0, released.stderr)

    def assert_unbound_refusal_shape(
        self, proc: subprocess.CompletedProcess,
    ) -> None:
        """The shared refusal witnesses: non-zero exit, the named refusal
        with the re-derive-and-retry remedy (placeholder plus re-derive
        sources), and the finalization-state line carrying
        `run_id=unbound marking=refused`."""
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("unbound-resolution refusal", proc.stderr)
        self.assertIn("done_run finalize --run-id <run_id>", proc.stderr)
        self.assertIn("setup echo", proc.stderr)
        self.assertIn("interrupted-manifest census", proc.stderr)
        self.assertEqual(
            self.finalization_lines(proc),
            ["done_run finalize: finalization: run_id=unbound marking=refused"],
        )

    def test_finalize_unbound_marker_arm_refuses_and_never_echoes(self) -> None:
        # The newest-confirmed-marker arm: a same-repo peer run whose
        # confirmed marker is the newest. The env-lost finalize (no exports,
        # no explicit args) must refuse instead of marking the peer record,
        # and the marker-resolved peer run id appears nowhere in the output.
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "unbound-marker")
        own_manifest = Path(exports["DONE_RUN_MANIFEST"])
        self.release_setup_hold(exports)
        peer_marker = self.craft_confirmed_marker("run-start-20991231T235959Z")
        peer_manifest = self.craft_manifest_file(
            own_manifest, self.PEER_ID, marker=peer_marker.name,
        )
        firing = "description-length:catch:fixture-evidence:run_id=unbound-probe"
        proc = self.run_finalize("--guard-firing", firing, env=self.runner_env())
        self.assert_unbound_refusal_shape(proc)
        # Never-echo: the marker-resolved peer id appears nowhere.
        self.assertNotIn(self.PEER_ID, proc.stdout + proc.stderr)
        # The steps under the refusal flag skip with their named warnings
        # (the guard-firing append, the landing summary plus missing-review
        # scan, and the landing-cost telemetry append).
        self.assertIn("guard-liveness rows not appended", proc.stderr)
        self.assertIn(
            "re-append them with --guard-firing on a bound re-run", proc.stderr,
        )
        self.assertIn(
            "the landing summary and the missing-review-record scan are "
            "skipped", proc.stderr,
        )
        self.assertIn("re-report them on a bound finalize re-run", proc.stderr)
        self.assertIn("landing-cost telemetry", proc.stderr)
        self.assertNotIn("missing-review-record scan:", proc.stdout)
        self.assertNotIn("landing summary:", proc.stdout)
        # No checkpoint or finalize-manifest mutation on either record.
        self.assertFalse(
            json.loads(peer_manifest.read_text()).get("complete", False)
        )
        self.assertFalse(
            json.loads(own_manifest.read_text()).get("complete", False)
        )
        self.assertFalse(
            (self.done_session() / f"run-checkpoint-{self.PEER_ID}.json").exists()
        )
        self.assertFalse(
            (
                self.done_session()
                / f"run-checkpoint-{exports['DONE_RUN_ID']}.json"
            ).exists()
        )
        # The releases still ran: the ceremony reached its status-free
        # verification with both locks free.
        self.assertIn("done lock status: free", proc.stdout)
        self.assertIn(": free", self.lock_status())
        self.assertIn(": free", self.lock_status(merge=True))

    def test_finalize_unbound_fallback_arm_refuses_and_never_echoes(self) -> None:
        # The newest-glob fallback arm: a peer record claiming the SAME
        # active marker makes the selector refuse the ambiguity, and the
        # fallback binds the newest canonical record. The env-lost finalize
        # must refuse, and the fallback-resolved peer id appears nowhere.
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "unbound-fallback")
        own_manifest = Path(exports["DONE_RUN_MANIFEST"])
        self.release_setup_hold(exports)
        active_marker = json.loads(own_manifest.read_text())["marker"]
        peer_manifest = self.craft_manifest_file(
            own_manifest, self.PEER_ID, marker=active_marker,
        )
        proc = self.run_finalize(env=self.runner_env())
        self.assert_unbound_refusal_shape(proc)
        self.assertNotIn(self.PEER_ID, proc.stdout + proc.stderr)
        self.assertFalse(
            json.loads(peer_manifest.read_text()).get("complete", False)
        )
        self.assertFalse(
            json.loads(own_manifest.read_text()).get("complete", False)
        )
        self.assertFalse(
            (self.done_session() / f"run-checkpoint-{self.PEER_ID}.json").exists()
        )
        self.assertIn("done lock status: free", proc.stdout)
        self.assertIn(": free", self.lock_status(merge=True))

    def test_finalize_unbound_refusal_with_held_lock_names_refusal_advice(self) -> None:
        # Refusal plus failed release over a fallback-bound peer manifest
        # that reads complete: the step-6 routing must take the
        # refusal-specific advice (re-derive binding, then the bound form;
        # the releases already ran), never the release-only-safe advice the
        # complete peer manifest would otherwise earn.
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "unbound-held")
        own_manifest = Path(exports["DONE_RUN_MANIFEST"])
        active_marker = json.loads(own_manifest.read_text())["marker"]
        peer_manifest = self.craft_manifest_file(
            own_manifest, self.PEER_ID, marker=active_marker, complete=True,
        )
        # The held-lock shape without any run binding evidence: the real
        # lock dir beside a deliberately wrong token (lock exports are never
        # binding evidence) plus the pinned staleness clocks.
        env = self.runner_env()
        env["DONE_LOCK_DIR"] = exports["DONE_LOCK_DIR"]
        env["DONE_LOCK_TOKEN"] = "0" * 64
        env.update(self.held_lock_clock_env())
        proc = self.run_finalize(env=env)
        self.assert_unbound_refusal_shape(proc)
        self.assert_held_done_lock(proc)
        # The release invocation actually ran under the refusal flag: the
        # release-refusal line prints only from the release's own non-zero
        # rc, so a skip-the-release-under-the-flag regression fails here
        # (status-derived hold evidence alone would stay green).
        self.assertIn("done-lock release refused", proc.stderr)
        self.assertIn("re-derive the binding", proc.stderr)
        self.assertIn("already ran", proc.stderr)
        self.assertNotIn("release-only retry", proc.stderr)
        self.assertNotIn(
            "do not re-run finalize from the primary checkout", proc.stderr,
        )
        self.assertNotIn(self.PEER_ID, proc.stdout + proc.stderr)
        # The refusal touched neither record.
        self.assertTrue(
            json.loads(peer_manifest.read_text()).get("complete", False)
        )
        self.assertFalse(
            json.loads(own_manifest.read_text()).get("complete", False)
        )

    def test_finalize_manifest_only_binds_and_marks_the_named_manifest(self) -> None:
        # A --manifest-only invocation with no other binding evidence marks
        # the NAMED manifest: the explicit --manifest is wired through the
        # resolver (canonical-name validation applies), so the newest-marker
        # peer record is never bound or marked.
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "manifest-bound")
        own_id = exports["DONE_RUN_ID"]
        own_manifest = Path(exports["DONE_RUN_MANIFEST"])
        self.release_setup_hold(exports)
        peer_marker = self.craft_confirmed_marker("run-start-20991231T235959Z")
        peer_manifest = self.craft_manifest_file(
            own_manifest, self.PEER_ID, marker=peer_marker.name,
        )
        proc = self.run_finalize(
            "--manifest", str(own_manifest), env=self.runner_env(),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("marked complete in", proc.stdout)
        self.assertTrue(
            json.loads(own_manifest.read_text()).get("complete", False)
        )
        self.assertFalse(
            json.loads(peer_manifest.read_text()).get("complete", False)
        )
        self.assertEqual(
            self.finalization_lines(proc),
            [f"done_run finalize: finalization: run_id={own_id} marking=applied"],
        )
        self.assertNotIn(self.PEER_ID, proc.stdout + proc.stderr)

    def test_finalize_manifest_resolver_rejected_falls_back_refuses(self) -> None:
        # The equality arm's identity half: a --manifest the resolver REFUSES
        # (named-but-absent) must never bind through the newest-glob fallback
        # the failed resolution hands control to. The fallback selects the
        # newest canonical record (a same-repo peer's); only equality with
        # the resolver's verbatim explicit-arm echo binds it — a mere
        # --manifest presence must not (the presence-only mutant marks the
        # peer record and exits 0, so this case is RED on that mutant and
        # GREEN on the real equality).
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "resolver-rejected")
        own_manifest = Path(exports["DONE_RUN_MANIFEST"])
        own_bytes = own_manifest.read_bytes()
        self.release_setup_hold(exports)
        peer_marker = self.craft_confirmed_marker("run-start-20991231T235959Z")
        peer_manifest = self.craft_manifest_file(
            own_manifest, self.PEER_ID, marker=peer_marker.name,
        )
        peer_bytes = peer_manifest.read_bytes()
        absent = (
            Path(exports["DONE_RUN_MANIFEST"]).parent
            / "run-manifest-20991231T235959Z-absent.json"
        )
        proc = self.run_finalize(
            "--manifest", str(absent), env=self.runner_env(),
        )
        self.assert_unbound_refusal_shape(proc)
        self.assertNotIn(self.PEER_ID, proc.stdout + proc.stderr)
        self.assertEqual(peer_manifest.read_bytes(), peer_bytes)
        self.assertEqual(own_manifest.read_bytes(), own_bytes)
        self.assertFalse(
            (self.done_session() / f"run-checkpoint-{self.PEER_ID}.json").exists()
        )
        self.assertIn("done lock status: free", proc.stdout)
        self.assertIn(": free", self.lock_status())
        self.assertIn(": free", self.lock_status(merge=True))

    def test_finalize_manifest_shadow_name_falls_back_unbound(self) -> None:
        # The canonical-shape fence: a shadow-named copy sorts newest, the
        # resolver's explicit arm refuses the name, and the newest-glob
        # fallback selects that very file — the equality arm binds only a
        # name passing the explicit arm's canonical-shape check
        # (run-manifest-<dot-free id>.json), so the explicit arm's refusal is
        # never overridable through the fallback and the peer record the
        # shadow copies is never checkpointed or marked.
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "shadow-name")
        own_manifest = Path(exports["DONE_RUN_MANIFEST"])
        own_bytes = own_manifest.read_bytes()
        self.release_setup_hold(exports)
        peer_marker = self.craft_confirmed_marker("run-start-20991231T235959Z")
        peer_manifest = self.craft_manifest_file(
            own_manifest, self.PEER_ID, marker=peer_marker.name,
        )
        peer_bytes = peer_manifest.read_bytes()
        # The shadow path carries the runner's own session-dir spelling, so
        # the equality arm (not a path-spelling divergence) is the thing
        # under test: git's toplevel and the test's tempfile root can spell
        # the same directory differently (/var vs /private/var), and the
        # witness must not pass on that accident.
        shadow = (
            Path(exports["DONE_RUN_MANIFEST"]).parent
            / "run-manifest-zz.shadow-copy.json"
        )
        shadow.write_text(peer_manifest.read_text())
        proc = self.run_finalize(
            "--manifest", str(shadow), env=self.runner_env(),
        )
        self.assert_unbound_refusal_shape(proc)
        self.assertNotIn(self.PEER_ID, proc.stdout + proc.stderr)
        self.assertEqual(peer_manifest.read_bytes(), peer_bytes)
        self.assertEqual(own_manifest.read_bytes(), own_bytes)
        self.assertFalse(
            (self.done_session() / f"run-checkpoint-{self.PEER_ID}.json").exists()
        )
        self.assertIn("done lock status: free", proc.stdout)
        self.assertIn(": free", self.lock_status())
        self.assertIn(": free", self.lock_status(merge=True))

    def test_finalize_agreement_clause_keys_line_and_marking_on_selection(self) -> None:
        # Deterministic pin of the agreement-clause bound path: the state
        # line and the marked manifest key on selected_run_id, the
        # resolution the binding evidence validated. This case cannot
        # witness the divergence re-key itself (the two resolutions cannot
        # diverge hermetically; deleting the re-key branch leaves the whole
        # suite green — r2 finding), so the re-key is wrapper-unwitnessed by
        # construction; its discrimination evidence is the r1 risk probe's
        # hook-based reproduction (peer marker flip between the two
        # resolves), recorded in the r1 staging doc's F5 body. The explicit
        # --run-id sole-evidence shape is exempt by design.
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "agreement-rekey")
        own_manifest = Path(exports["DONE_RUN_MANIFEST"])
        checkpoint = self.make_checkpoint(exports["DONE_RUN_ID"])
        self.release_setup_hold(exports)
        env = self.runner_env()
        env["DONE_RUN_ID"] = exports["DONE_RUN_ID"]
        proc = self.run_finalize(env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        selected_run_id = json.loads(own_manifest.read_text())["run_id"]
        self.assertEqual(selected_run_id, exports["DONE_RUN_ID"])
        self.assertEqual(
            self.finalization_lines(proc),
            [
                "done_run finalize: finalization: "
                f"run_id={selected_run_id} marking=applied"
            ],
        )
        # The marking landed in exactly run-manifest-<selected_run_id>.json.
        self.assertTrue(
            json.loads(own_manifest.read_text()).get("complete", False)
        )
        self.assertFalse(checkpoint.exists())

    def test_finalize_bound_fallback_marks_the_record_done_run_id_agrees_with(self) -> None:
        # The bound side of the fallback arm (Task 2's binding-evidence
        # predicate; the 2026-11-05 task-2 review's C1 composition): a peer
        # record claiming the same active marker makes the selector refuse
        # the ambiguity and the newest-glob fallback selects this run's OWN
        # record (the low-sorted peer id sorts below it), whose run_id the
        # non-empty DONE_RUN_ID export agrees with. The invocation is bound:
        # it marks the record it bound and reports the real run id with
        # marking=applied, never the false `run_id=none marking=not-bound`
        # exit 0 over a resolution that selected a record.
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "bound-fallback")
        own_id = exports["DONE_RUN_ID"]
        own_manifest = Path(exports["DONE_RUN_MANIFEST"])
        checkpoint = self.make_checkpoint(own_id)
        self.release_setup_hold(exports)
        active_marker = json.loads(own_manifest.read_text())["marker"]
        peer_manifest = self.craft_manifest_file(
            own_manifest, self.LOW_PEER_ID, marker=active_marker,
        )
        env = self.runner_env()
        env["DONE_RUN_ID"] = own_id
        proc = self.run_finalize(env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertNotIn("no run manifest from setup", proc.stdout)
        self.assertNotIn("marking=not-bound", proc.stdout + proc.stderr)
        self.assertIn("marked complete in", proc.stdout)
        self.assertTrue(
            json.loads(own_manifest.read_text()).get("complete", False)
        )
        self.assertFalse(
            json.loads(peer_manifest.read_text()).get("complete", False)
        )
        self.assertFalse(checkpoint.exists())
        self.assertEqual(
            self.finalization_lines(proc),
            [f"done_run finalize: finalization: run_id={own_id} marking=applied"],
        )
        self.assertIn("done lock status: free", proc.stdout)
        self.assertIn(": free", self.lock_status())
        self.assertIn(": free", self.lock_status(merge=True))

    def test_finalize_unbound_marker_arm_refuses_disagreeing_done_run_id(self) -> None:
        # The agreement clause of the binding-evidence predicate (Task 2;
        # the 2026-11-05 task-2 review's T1 discrimination witness for the
        # equality-dropped mutant): the env carries a non-empty DONE_RUN_ID
        # that DISAGREES with the marker-arm-selected peer record's run_id,
        # so nothing binds and the invocation refuses with the shared shape;
        # the selected peer id is never echoed and neither record is
        # mutated.
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "disagreeing-id")
        own_manifest = Path(exports["DONE_RUN_MANIFEST"])
        self.release_setup_hold(exports)
        peer_marker = self.craft_confirmed_marker("run-start-20991231T235959Z")
        peer_manifest = self.craft_manifest_file(
            own_manifest, self.PEER_ID, marker=peer_marker.name,
        )
        env = self.runner_env()
        env["DONE_RUN_ID"] = exports["DONE_RUN_ID"]
        proc = self.run_finalize(env=env)
        self.assert_unbound_refusal_shape(proc)
        self.assertNotIn(self.PEER_ID, proc.stdout + proc.stderr)
        self.assertFalse(
            json.loads(peer_manifest.read_text()).get("complete", False)
        )
        self.assertFalse(
            json.loads(own_manifest.read_text()).get("complete", False)
        )
        self.assertFalse(
            (self.done_session() / f"run-checkpoint-{self.PEER_ID}.json").exists()
        )
        self.assertIn("done lock status: free", proc.stdout)
        self.assertIn(": free", self.lock_status())
        self.assertIn(": free", self.lock_status(merge=True))

    def test_finalize_unbound_refusal_done_run_manifest_never_binds(self) -> None:
        # DONE_RUN_MANIFEST never binds (Task 2's hint-only doctrine; the
        # 2026-11-05 task-2 review's T1 discrimination witness for the
        # DONE_RUN_MANIFEST-binds mutant): the env carries only the
        # DONE_RUN_MANIFEST export (no DONE_RUN_ID) while a peer's confirmed
        # marker is newest, so nothing ties the selected peer record to this
        # run and the invocation refuses with the shared shape.
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "manifest-hint-only")
        own_manifest = Path(exports["DONE_RUN_MANIFEST"])
        self.release_setup_hold(exports)
        peer_marker = self.craft_confirmed_marker("run-start-20991231T235959Z")
        peer_manifest = self.craft_manifest_file(
            own_manifest, self.PEER_ID, marker=peer_marker.name,
        )
        env = self.runner_env()
        env["DONE_RUN_MANIFEST"] = str(own_manifest)
        proc = self.run_finalize(env=env)
        self.assert_unbound_refusal_shape(proc)
        self.assertNotIn(self.PEER_ID, proc.stdout + proc.stderr)
        self.assertFalse(
            json.loads(peer_manifest.read_text()).get("complete", False)
        )
        self.assertFalse(
            json.loads(own_manifest.read_text()).get("complete", False)
        )
        self.assertFalse(
            (self.done_session() / f"run-checkpoint-{self.PEER_ID}.json").exists()
        )
        self.assertIn("done lock status: free", proc.stdout)
        self.assertIn(": free", self.lock_status())
        self.assertIn(": free", self.lock_status(merge=True))

    def test_finalize_step6_advice_reads_the_marking_target_manifest(self) -> None:
        # The step-6 completion read target (Task 2; the 2026-11-05 task-2
        # review's T2 discrimination witness for the read-target-reverted
        # mutant): the held-lock shape with explicit --run-id of the own run
        # while a peer's confirmed marker is newest and the two records
        # DIVERGE (own complete, peer incomplete). The status-not-free advice
        # must derive from the OWN manifest's state (the marking target,
        # run-manifest-<RUN_ID>.json): the release-only-safe advice, never
        # the peer-derived full-retry advice.
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "divergent-target")
        own_id = exports["DONE_RUN_ID"]
        own_manifest = Path(exports["DONE_RUN_MANIFEST"])
        # The peer record is crafted from the still-incomplete own record,
        # then the own record diverges to complete: own is the marking
        # target, the resolver-selected peer stays incomplete.
        peer_marker = self.craft_confirmed_marker("run-start-20991231T235959Z")
        peer_manifest = self.craft_manifest_file(
            own_manifest, self.PEER_ID, marker=peer_marker.name,
        )
        self.rewrite_manifest(own_manifest, complete=True)
        env = self.runner_env()
        env["DONE_LOCK_DIR"] = exports["DONE_LOCK_DIR"]
        env["DONE_LOCK_TOKEN"] = "0" * 64
        env.update(self.held_lock_clock_env())
        proc = self.run_finalize("--run-id", own_id, env=env)
        self.assertNotEqual(proc.returncode, 0)
        self.assert_held_done_lock(proc)
        self.assertIn("the run manifest is complete", proc.stderr)
        self.assertIn("release-only retry", proc.stderr)
        self.assertNotIn("NOT complete", proc.stderr)
        self.assertNotIn("full finalize re-run", proc.stderr)
        self.assertEqual(
            self.finalization_lines(proc),
            [
                f"done_run finalize: finalization: run_id={own_id} "
                "marking=already-complete"
            ],
        )
        # The peer record the resolver selected stays untouched.
        self.assertFalse(
            json.loads(peer_manifest.read_text()).get("complete", False)
        )

    # ---- Task 3 refusal witnesses (plan
    #      docs/history/plans/2026-11-02-done-finalize-resume-marking-honesty.md
    #      Task 3): born-GREEN caller-side witnesses over Task 2's
    #      implementation: the bare env-lost invocation refuses through the
    #      marker arm (the wrong-run hazard contained beyond the fallback),
    #      the agreeing DONE_RUN_ID export keeps the legitimate fresh-shell
    #      retry marking, and the explicit --run-id alone marks the own
    #      record while a peer's confirmed marker is newest. ---- #

    def test_finalize_env_lost_no_args_refuses_newest_peer_marker_arm(self) -> None:
        # Safety witness: a shared done-session directory holding a same-repo
        # peer run whose confirmed marker IS the newest confirmed marker. The
        # env-lost finalize (no exports, no explicit args at all) refuses
        # through the marker arm instead of marking the peer record — the
        # wrong-run hazard is contained on the marker arm, not only the
        # newest-glob fallback — and the peer manifest bytes stay untouched.
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "safety-marker")
        own_manifest = Path(exports["DONE_RUN_MANIFEST"])
        self.release_setup_hold(exports)
        peer_marker = self.craft_confirmed_marker("run-start-20991231T235959Z")
        peer_manifest = self.craft_manifest_file(
            own_manifest, self.PEER_ID, marker=peer_marker.name,
        )
        peer_bytes = peer_manifest.read_bytes()
        proc = self.run_finalize(env=self.runner_env())
        self.assert_unbound_refusal_shape(proc)
        # Never-echo: the marker-resolved peer id appears nowhere.
        self.assertNotIn(self.PEER_ID, proc.stdout + proc.stderr)
        # Neither record was marked: the peer manifest is byte-identical.
        self.assertEqual(peer_manifest.read_bytes(), peer_bytes)
        self.assertFalse(
            json.loads(own_manifest.read_text()).get("complete", False)
        )
        self.assertFalse(
            (self.done_session() / f"run-checkpoint-{self.PEER_ID}.json").exists()
        )
        # The releases still ran: both locks verify free.
        self.assertIn("done lock status: free", proc.stdout)
        self.assertIn(": free", self.lock_status())
        self.assertIn(": free", self.lock_status(merge=True))

    def test_finalize_agreeing_done_run_id_export_keeps_marker_arm_marking_applied(self) -> None:
        # Keep-working witness: a fresh shell (a fresh done-lock hold's
        # exports standing in for the resume session, the rerun-after-squash
        # env shape) whose DONE_RUN_ID export agrees with the marker-arm-
        # selected manifest's run_id stays bound: the marking proceeds
        # unchanged with marking=applied and the checkpoint is consumed.
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "keep-working")
        own_id = exports["DONE_RUN_ID"]
        own_manifest = Path(exports["DONE_RUN_MANIFEST"])
        checkpoint = self.make_checkpoint(own_id)
        self.release_setup_hold(exports)
        acq = self.lock_invocation("acquire", "--label", "resume-session")
        self.assertEqual(acq.returncode, 0, acq.stderr)
        env = self.runner_env()
        env.update(self.eval_exports(acq.stdout))
        env["DONE_RUN_ID"] = own_id
        proc = self.run_finalize(env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("marked complete in", proc.stdout)
        self.assertTrue(
            json.loads(own_manifest.read_text()).get("complete", False)
        )
        self.assertFalse(checkpoint.exists())
        self.assertEqual(
            self.finalization_lines(proc),
            [f"done_run finalize: finalization: run_id={own_id} marking=applied"],
        )
        self.assertIn("done lock status: free", proc.stdout)
        self.assertIn(": free", self.lock_status())
        self.assertIn(": free", self.lock_status(merge=True))

    def test_finalize_explicit_run_id_sole_evidence_marks_own_leaves_peer_bytes(self) -> None:
        # Sole-evidence witness: an env-lost fresh shell (no exports) whose
        # only binding evidence is the explicit --run-id of the own run,
        # while a peer's confirmed marker is newest. The marking keys on
        # --run-id: the own manifest is marked complete, the peer record the
        # resolver selected stays byte-identical, and the line reports the
        # own id with marking=applied.
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "sole-evidence")
        own_id = exports["DONE_RUN_ID"]
        own_manifest = Path(exports["DONE_RUN_MANIFEST"])
        self.release_setup_hold(exports)
        peer_marker = self.craft_confirmed_marker("run-start-20991231T235959Z")
        peer_manifest = self.craft_manifest_file(
            own_manifest, self.PEER_ID, marker=peer_marker.name,
        )
        peer_bytes = peer_manifest.read_bytes()
        proc = self.run_finalize("--run-id", own_id, env=self.runner_env())
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("marked complete in", proc.stdout)
        self.assertTrue(
            json.loads(own_manifest.read_text()).get("complete", False)
        )
        self.assertEqual(peer_manifest.read_bytes(), peer_bytes)
        self.assertEqual(
            self.finalization_lines(proc),
            [f"done_run finalize: finalization: run_id={own_id} marking=applied"],
        )
        self.assertIn("done lock status: free", proc.stdout)
        self.assertIn(": free", self.lock_status())
        self.assertIn(": free", self.lock_status(merge=True))

    # ---- shadow propagation (plan
    #      docs/history/plans/2026-11-05-done-finalized-manifest-shadow.md
    #      Task 2): the finalize leg propagates the finalized manifest bytes
    #      into the primary checkout's surviving shadow record for the same
    #      run-id. Every case below runs the real finalize subcommand,
    #      worktree-dispatched through run_finalize's cwd parameter over the
    #      existing hermetic fixture; the finalize's own exit semantics and
    #      FAILED-line arms stay unchanged in every arm. ---- #

    def primary_session(self) -> Path:
        return self.fixture / "docs" / "tmp" / "done-session"

    def wt_done_session(self, worktree: Path) -> Path:
        return worktree / "docs" / "tmp" / "done-session"

    def worktree_finalize_session(
        self, *setup_args: str
    ) -> tuple[Path, dict, dict]:
        """An ad-hoc worktree beside the fixture primary with a setup
        boundary run inside it; returns (worktree, exports, finalize env)
        with the env keyed to the worktree the way a dispatched closeout
        invokes the finalize subcommand inside it."""
        worktree = self.tmp / "shadow-propagation-wt"
        self.git("worktree", "add", "-b", "shadow-propagation-wt-branch", str(worktree))
        (worktree / "seed.txt").write_text("seed\nwork\n", encoding="utf-8")
        env = self.runner_env()
        env["DONE_SWEEP_REPO_ROOT"] = str(worktree)
        setup = subprocess.run(
            ["bash", str(RUNNER), "setup", *setup_args],
            cwd=str(worktree), env=env, capture_output=True, text=True,
            timeout=300,
        )
        self.assertEqual(setup.returncode, 0, setup.stderr)
        exports = self.eval_exports(setup.stdout)
        env = self.runner_env()
        env["DONE_SWEEP_REPO_ROOT"] = str(worktree)
        env.update(exports)
        return worktree, exports, env

    def seed_primary_shadow(self, worktree: Path, run_id: str) -> Path:
        """The closeout migration's manifest transfer shape: the worktree
        run's pre-finalize manifest bytes copied verbatim into the primary
        done-session directory under the same canonical filename."""
        source = self.wt_done_session(worktree) / f"run-manifest-{run_id}.json"
        self.primary_session().mkdir(parents=True, exist_ok=True)
        shadow = self.primary_session() / source.name
        shadow.write_bytes(source.read_bytes())
        return shadow

    def seed_transfer_witness(self, slug: str, run_id: str) -> Path:
        """The closeout migration's transfer record: one verified migrated
        row whose source names the run's done-session manifest, at the
        canonical Phase 5 record home under the primary's facts tmp root."""
        record_dir = self.fixture / "docs" / "tmp" / "execute-plan" / slug
        record_dir.mkdir(parents=True, exist_ok=True)
        record = record_dir / "closeout-migration.json"
        record.write_text(
            json.dumps(
                {
                    "branch": [],
                    "migrated": [
                        {
                            "source": (
                                f"docs/tmp/done-session/run-manifest-{run_id}.json"
                            ),
                            "destination": str(
                                self.primary_session()
                                / f"run-manifest-{run_id}.json"
                            ),
                            "verified": True,
                        }
                    ],
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return record

    def worktree_root_digest(self, worktree: Path) -> str:
        """The done Step 0 identity digest of the worktree root (the same
        derivation the manifest's recorded repo_root carries)."""
        return hashlib.sha256(
            str(worktree.resolve()).rstrip("/").encode("utf-8")
        ).hexdigest()

    def git_shim_env(self, base_env: dict) -> dict:
        """A PATH whose ``git`` refuses exactly ``worktree list`` and
        delegates everything else to the real binary: the controlled input
        that makes the finalize leg's primary resolution fail without
        breaking any other git consumer of the finalize or the locks."""
        real_git = shutil.which("git")
        if not real_git:
            raise AssertionError("no real git binary on PATH")
        shim_dir = self.tmp / "git-shims"
        shim_dir.mkdir()
        shim = shim_dir / "git"
        shim.write_text(
            "#!/bin/bash\n"
            "prev=''\n"
            "for arg in \"$@\"; do\n"
            "  if [ \"$prev\" = \"worktree\" ] && [ \"$arg\" = \"list\" ]; then\n"
            "    echo 'git shim: worktree list refused (fixture)' >&2\n"
            "    exit 1\n"
            "  fi\n"
            "  prev=\"$arg\"\n"
            "done\n"
            f"exec {shlex.quote(real_git)} \"$@\"\n",
            encoding="utf-8",
        )
        shim.chmod(0o755)
        env = dict(base_env)
        env["PATH"] = str(shim_dir) + os.pathsep + env["PATH"]
        return env

    def test_finalize_propagates_finalized_bytes_to_primary_shadow(self) -> None:
        self.init_fixture_repo()
        worktree, exports, env = self.worktree_finalize_session(
            "--label", "shadow-propagate"
        )
        run_id = exports["DONE_RUN_ID"]
        shadow = self.seed_primary_shadow(worktree, run_id)
        # The migrated shadow carries the strict pre-finalize shape the
        # already-terminal guard keys on (the manifest schema always records
        # the flag; pre-finalize it is false with no disposition record).
        seeded = json.loads(shadow.read_text())
        self.assertIs(False, seeded["complete"])
        self.assertIsNone(seeded["dispositioned"])
        proc = self.run_finalize(env=env, cwd=worktree)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        # The source copy is finalized and the primary shadow carries the
        # finalized bytes (same run-id, same canonical filename).
        record = self.manifest_record(exports)
        self.assertTrue(record.get("complete", False))
        payload = json.loads(shadow.read_text())
        self.assertTrue(payload["complete"])
        self.assertEqual(payload["run_id"], run_id)
        self.assertEqual(
            payload["repo_root"], self.worktree_root_digest(worktree)
        )
        # The success report rides the leg's failure channel, not stdout.
        self.assertIn("shadow propagation:", proc.stderr)
        self.assertIn(
            "wrote the finalized bytes over the primary shadow", proc.stderr
        )
        self.assertNotIn(
            "wrote the finalized bytes over the primary shadow", proc.stdout
        )
        self.assertEqual(
            self.finalization_lines(proc),
            [f"done_run finalize: finalization: run_id={run_id} marking=applied"],
        )

    def test_finalize_shadow_absent_transfer_witness_writes_surviving_record(self) -> None:
        self.init_fixture_repo()
        plan_rel = "docs/history/plans/2026-11-06-shadow-propagation-witness.md"
        plans = self.fixture / "docs" / "history" / "plans"
        plans.mkdir(parents=True, exist_ok=True)
        (self.fixture / plan_rel).write_text("# plan\n", encoding="utf-8")
        self.git("add", plan_rel)
        self.git("commit", "-qm", "plans: fixture owned plan")
        worktree, exports, env = self.worktree_finalize_session(
            "--owned-path", "seed.txt", "--owned-plan", plan_rel,
        )
        run_id = exports["DONE_RUN_ID"]
        # The shadow is absent; the migration record witnesses the transfer.
        self.seed_transfer_witness("shadow-propagation-witness", run_id)
        proc = self.run_finalize(env=env, cwd=worktree)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        shadow = self.primary_session() / f"run-manifest-{run_id}.json"
        self.assertTrue(shadow.is_file(), proc.stderr)
        payload = json.loads(shadow.read_text())
        self.assertTrue(payload["complete"])
        self.assertEqual(payload["owned_plan_paths"], [plan_rel])
        self.assertIn("witnesses the transfer", proc.stderr)
        self.assertEqual(
            self.finalization_lines(proc),
            [f"done_run finalize: finalization: run_id={run_id} marking=applied"],
        )

    def test_finalize_shadow_absent_without_witness_skips_with_report(self) -> None:
        self.init_fixture_repo()
        worktree, exports, env = self.worktree_finalize_session(
            "--label", "shadow-nowitness"
        )
        run_id = exports["DONE_RUN_ID"]
        proc = self.run_finalize(env=env, cwd=worktree)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        shadow = self.primary_session() / f"run-manifest-{run_id}.json"
        self.assertFalse(shadow.exists())
        self.assertFalse(
            (self.primary_session() / f"run-manifest-{run_id}.json.tmp").exists()
        )
        self.assertIn(
            "no primary shadow and no closeout-migration transfer witness",
            proc.stderr,
        )
        self.assertEqual(
            self.finalization_lines(proc),
            [f"done_run finalize: finalization: run_id={run_id} marking=applied"],
        )

    def test_finalize_shadow_identity_mismatch_aborts_both_files_untouched(self) -> None:
        self.init_fixture_repo()
        worktree, exports, env = self.worktree_finalize_session(
            "--label", "shadow-mismatch"
        )
        run_id = exports["DONE_RUN_ID"]
        shadow = self.seed_primary_shadow(worktree, run_id)
        tampered = json.loads(shadow.read_text())
        tampered["owned_plan_paths"] = ["docs/history/plans/2026-11-06-other.md"]
        shadow.write_text(json.dumps(tampered, indent=2, sort_keys=True) + "\n")
        shadow_before = shadow.read_bytes()
        proc = self.run_finalize(env=env, cwd=worktree)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        # The finalize itself applied; the propagation aborted named.
        self.assertEqual(
            self.finalization_lines(proc),
            [f"done_run finalize: finalization: run_id={run_id} marking=applied"],
        )
        self.assertIn("identity mismatch between the primary shadow", proc.stderr)
        self.assertIn("both files untouched", proc.stderr)
        # The shadow keeps its tampered bytes; the source copy carries exactly
        # the finalized bytes the operation itself wrote before the arm ran
        # (the marking applied; the propagation's abort touches neither file).
        self.assertEqual(shadow.read_bytes(), shadow_before)
        finalized = json.loads(
            (
                self.wt_done_session(worktree) / f"run-manifest-{run_id}.json"
            ).read_text()
        )
        self.assertIs(True, finalized["complete"])

    def test_finalize_withheld_marks_nothing_and_propagates_nothing(self) -> None:
        self.init_fixture_repo()
        worktree, exports, env = self.worktree_finalize_session(
            "--label", "shadow-withheld"
        )
        run_id = exports["DONE_RUN_ID"]
        # The deferred-squash shape at the worktree: a run-branch landing
        # commit the squash never carried to the base branch. The base branch
        # is the primary checkout's own branch (the worktree branched from
        # its HEAD), derived - never hardcoded - because the hermetic env
        # drops init.defaultBranch and the fixture's default branch name is
        # whatever this git's compiled default is.
        base_branch = self.git("symbolic-ref", "--short", "HEAD").stdout.strip()
        wt_facts = worktree / ".ai-playbook" / "facts.md"
        wt_facts.write_text(
            wt_facts.read_text() + f'base_branch = "{base_branch}"\n'
        )
        self.git("checkout", "-qb", "run/shadow-withheld", repo=worktree)
        (worktree / "work.txt").write_text("work\n", encoding="utf-8")
        self.git("add", "work.txt", repo=worktree)
        self.git("commit", "-qm", "run work", repo=worktree)
        landing = self.git("rev-parse", "HEAD", repo=worktree).stdout.strip()
        ledger = self.wt_done_session(worktree) / f"owned-commits-{run_id}.txt"
        self.wt_done_session(worktree).mkdir(parents=True, exist_ok=True)
        ledger.write_text(landing + "\n", encoding="utf-8")
        shadow = self.seed_primary_shadow(worktree, run_id)
        shadow_before = shadow.read_bytes()
        proc = self.run_finalize(env=env, cwd=worktree)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("LANDING DEFERRED", proc.stderr)
        self.assertIn("complete marking withheld", proc.stdout)
        self.assertEqual(
            self.finalization_lines(proc),
            [f"done_run finalize: finalization: run_id={run_id} marking=withheld"],
        )
        # The withheld marking propagates nothing: no propagation line ran
        # and the shadow keeps its pre-finalize bytes.
        self.assertNotIn("shadow propagation", proc.stdout + proc.stderr)
        self.assertEqual(shadow.read_bytes(), shadow_before)
        self.assertFalse(self.manifest_record(exports).get("complete", False))

    def test_finalize_primary_dispatch_is_silent_noop_no_rewrite_no_report(self) -> None:
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "shadow-primary-dispatch")
        run_id = exports["DONE_RUN_ID"]
        manifest = Path(exports["DONE_RUN_MANIFEST"])
        env = self.runner_env()
        env.update(exports)
        # The primary-dispatched finalize: the resolved primary shadow path
        # is the file the finalize itself owns - silent no-op, no report.
        proc = self.run_finalize(env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertNotIn("shadow propagation", proc.stdout + proc.stderr)
        self.assertEqual(
            self.finalization_lines(proc),
            [f"done_run finalize: finalization: run_id={run_id} marking=applied"],
        )
        # The already-complete re-run: the arm no-ops silently again, and
        # nothing rewrote the manifest bytes.
        before_stat = manifest.stat().st_mtime_ns
        before_bytes = manifest.read_bytes()
        proc2 = self.run_finalize(env=env)
        self.assertEqual(proc2.returncode, 0, proc2.stderr + proc2.stdout)
        self.assertIn("already complete; nothing to do", proc2.stdout)
        self.assertNotIn("shadow propagation", proc2.stdout + proc2.stderr)
        self.assertEqual(
            self.finalization_lines(proc2),
            [
                f"done_run finalize: finalization: run_id={run_id} "
                "marking=already-complete"
            ],
        )
        self.assertEqual(manifest.stat().st_mtime_ns, before_stat)
        self.assertEqual(manifest.read_bytes(), before_bytes)

    def test_finalize_propagation_leaves_primary_boundary_finalized_setup_continues(self) -> None:
        self.init_fixture_repo()
        worktree, exports, env = self.worktree_finalize_session(
            "--label", "shadow-boundary"
        )
        run_id = exports["DONE_RUN_ID"]
        shadow = self.seed_primary_shadow(worktree, run_id)
        proc = self.run_finalize(env=env, cwd=worktree)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        # The canonical boundary classifier reads the propagated shadow as
        # terminal.
        classify = subprocess.run(
            [
                "python3",
                str(REPO_ROOT / "scripts" / "done_sweep_gates_lib.py"),
                "classify-run-boundary",
                "--session-dir", str(self.primary_session()),
                "--manifest", str(shadow),
            ],
            capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(classify.returncode, 0, classify.stderr)
        self.assertIn("verdict: finalized", classify.stdout)
        self.assertIn(f"run_id: {run_id}", classify.stdout)
        # Setup at the primary continues with a fresh boundary: the terminal
        # shadow is no false-interruption evidence.
        setup_proc = self.run_setup("--label", "fresh-after-propagation")
        self.assertEqual(setup_proc.returncode, 0, setup_proc.stderr)
        fresh_exports = self.eval_exports(setup_proc.stdout)
        self.assertTrue(fresh_exports.get("DONE_RUN_ID"))
        self.assertNotEqual(fresh_exports["DONE_RUN_ID"], run_id)

    def test_finalize_terminal_complete_shadow_skipped_never_overwritten(self) -> None:
        self.init_fixture_repo()
        worktree, exports, env = self.worktree_finalize_session(
            "--label", "shadow-complete"
        )
        run_id = exports["DONE_RUN_ID"]
        shadow = self.seed_primary_shadow(worktree, run_id)
        payload = json.loads(shadow.read_text())
        payload["complete"] = True
        shadow.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        shadow_before = shadow.read_bytes()
        proc = self.run_finalize(env=env, cwd=worktree)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn(
            "already carries terminal state (complete=true)", proc.stderr
        )
        self.assertEqual(shadow.read_bytes(), shadow_before)
        self.assertEqual(
            self.finalization_lines(proc),
            [f"done_run finalize: finalization: run_id={run_id} marking=applied"],
        )

    def test_finalize_dispositioned_shadow_skipped_never_overwritten(self) -> None:
        self.init_fixture_repo()
        worktree, exports, env = self.worktree_finalize_session(
            "--label", "shadow-dispositioned"
        )
        run_id = exports["DONE_RUN_ID"]
        shadow = self.seed_primary_shadow(worktree, run_id)
        payload = json.loads(shadow.read_text())
        payload["dispositioned"] = {
            "reason": "work-verified-landed",
            "date": "2026-11-06",
            "note": "closed elsewhere",
        }
        shadow.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        shadow_before = shadow.read_bytes()
        proc = self.run_finalize(env=env, cwd=worktree)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn(
            "already carries terminal state (a dispositioned record)",
            proc.stderr,
        )
        self.assertEqual(shadow.read_bytes(), shadow_before)
        self.assertEqual(
            self.finalization_lines(proc),
            [f"done_run finalize: finalization: run_id={run_id} marking=applied"],
        )

    def test_finalize_unresolvable_primary_reports_miss_outcome_arms_unchanged(self) -> None:
        self.init_fixture_repo()
        worktree, exports, env = self.worktree_finalize_session(
            "--label", "shadow-unresolvable"
        )
        run_id = exports["DONE_RUN_ID"]
        shadow = self.seed_primary_shadow(worktree, run_id)
        shadow_before = shadow.read_bytes()
        proc = self.run_finalize(env=self.git_shim_env(env), cwd=worktree)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        # The miss is reported on the failure channel and the finalize's own
        # outcome and FAILED arms are unchanged (applied, no finalize FAILED
        # line, no identity-mismatch routing).
        self.assertIn("shadow propagation:", proc.stderr)
        self.assertIn("primary checkout unresolved", proc.stderr)
        self.assertEqual(
            self.finalization_lines(proc),
            [f"done_run finalize: finalization: run_id={run_id} marking=applied"],
        )
        combined = proc.stdout + proc.stderr
        self.assertNotIn("the run manifest finalize did not complete", combined)
        self.assertNotIn("run-manifest identity mismatch", combined)
        # Nothing was written behind the unresolvable resolution.
        self.assertEqual(shadow.read_bytes(), shadow_before)

    def test_finalize_shadow_write_refused_reports_no_partial_write(self) -> None:
        self.init_fixture_repo()
        worktree, exports, env = self.worktree_finalize_session(
            "--label", "shadow-write-refused"
        )
        run_id = exports["DONE_RUN_ID"]
        shadow = self.seed_primary_shadow(worktree, run_id)
        shadow_before = shadow.read_bytes()
        self.primary_session().chmod(0o555)
        proc = self.run_finalize(env=env, cwd=worktree)
        self.primary_session().chmod(0o755)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("cannot write", proc.stderr)
        self.assertIn("no partial write", proc.stderr)
        self.assertEqual(shadow.read_bytes(), shadow_before)
        self.assertFalse(
            (self.primary_session() / f"run-manifest-{run_id}.json.tmp").exists()
        )
        self.assertEqual(
            self.finalization_lines(proc),
            [f"done_run finalize: finalization: run_id={run_id} marking=applied"],
        )

    def test_finalize_propagation_lines_never_trip_identity_mismatch_routing(self) -> None:
        # The write-refused propagation miss rides the output beside the
        # applied marking: no line carries the finalize's own identity-refusal
        # wording, the refused routing's advice never prints, and the state
        # line stays exactly `marking=applied`.
        self.init_fixture_repo()
        worktree, exports, env = self.worktree_finalize_session(
            "--label", "shadow-routing"
        )
        run_id = exports["DONE_RUN_ID"]
        self.seed_primary_shadow(worktree, run_id)
        self.primary_session().chmod(0o555)
        proc = self.run_finalize(env=env, cwd=worktree)
        self.primary_session().chmod(0o755)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        combined = proc.stdout + proc.stderr
        self.assertIn("shadow propagation:", proc.stderr)
        self.assertNotIn("run-manifest identity mismatch", combined)
        self.assertNotIn(
            "do not re-run finalize from the primary checkout", combined
        )
        self.assertEqual(
            self.finalization_lines(proc),
            [f"done_run finalize: finalization: run_id={run_id} marking=applied"],
        )

    def test_finalize_rerun_after_skipped_propagation_still_propagates(self) -> None:
        self.init_fixture_repo()
        worktree, exports, env = self.worktree_finalize_session(
            "--label", "shadow-rerun"
        )
        run_id = exports["DONE_RUN_ID"]
        shadow = self.seed_primary_shadow(worktree, run_id)
        shadow_before = shadow.read_bytes()
        # First finalize: the marking applies but the shadow write is
        # refused (the primary done-session directory is read-only).
        self.primary_session().chmod(0o555)
        proc = self.run_finalize(env=env, cwd=worktree)
        self.primary_session().chmod(0o755)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("no partial write", proc.stderr)
        self.assertEqual(shadow.read_bytes(), shadow_before)
        # The re-run: the already-complete early return still runs the
        # propagation arm and lands the same finalized bytes.
        rerun_env = self.runner_env()
        rerun_env["DONE_SWEEP_REPO_ROOT"] = str(worktree)
        proc2 = self.run_finalize("--run-id", run_id, env=rerun_env, cwd=worktree)
        self.assertEqual(proc2.returncode, 0, proc2.stderr + proc2.stdout)
        self.assertIn("already complete; nothing to do", proc2.stdout)
        self.assertIn(
            "wrote the finalized bytes over the primary shadow", proc2.stderr
        )
        payload = json.loads(shadow.read_text())
        self.assertTrue(payload["complete"])
        self.assertEqual(payload["run_id"], run_id)


class DoneRunDeclaredDeletionTest(FixtureMixin, unittest.TestCase):
    """The declared tracked-deletion arms: the staging partition, the
    guard call-site adjudications, and the end-to-end witnesses."""

    def stage_deletion_already_staged(self, rel: str) -> None:
        """Remove a tracked file and stage the deletion (worktree-absent,
        index-absent, HEAD-tracked: the witnessed refusal shape)."""
        (self.fixture / rel).unlink()
        self.git("rm", "--cached", "--quiet", rel)

    def test_already_staged_branch_added_deletion_lands_end_to_end(self) -> None:
        self.init_fixture_repo(branch="feature/PROJ-1-done-run")
        home = self.fixture / "audit-home"
        home.mkdir()
        (home / "audit.md").write_text("# audit bytes survive here\n")
        (self.fixture / ".gitignore").write_text(
            "docs/tmp/\n__pycache__/\naudit-home/\n"
        )
        (self.fixture / "records").mkdir()
        (self.fixture / "records" / "audit.md").write_text("# audit\n")
        self.git("add", "records/audit.md", ".gitignore")
        self.git("commit", "-qm", "add audit record")
        seed_sha = self.git("rev-parse", "HEAD~1").stdout.strip()
        self.git("update-ref", "refs/remotes/origin/main", seed_sha)
        self.git("symbolic-ref", "refs/remotes/origin/HEAD",
                 "refs/remotes/origin/main")
        self.stage_deletion_already_staged("records/audit.md")
        setup_proc, exports = self.setup_session(
            "--owned-path", "records/audit.md",
        )
        count_before = self.commit_count()
        proc = self.commit_session(
            setup_proc, exports,
            "--stage", "records/audit.md",
            "--subject", "move the audit record to its ignored home",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        combined = proc.stdout + proc.stderr
        self.assertIn("already-staged deletion, no staging operation needed",
                      combined)
        self.assertIn("declared deletion is the set's own removal", combined)
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        self.assertEqual(self.commit_count(), count_before + 1)
        shown = self.git("show", "--name-status", "--format=", landing).stdout
        self.assertIn("D\trecords/audit.md", shown)
        self.assertTrue((home / "audit.md").is_file())
        # the dirt gate ran its input-set skip, so the branch-added
        # deletion never reached the gate
        self.assertNotIn("dirt regression gate", combined)

    def test_index_tracked_worktree_absent_path_stages_through(self) -> None:
        self.init_fixture_repo(branch="feature/PROJ-1-done-run")
        (self.fixture / "gone.txt").write_text("tracked work\n")
        self.git("add", "gone.txt")
        self.git("commit", "-qm", "add gone")
        (self.fixture / "gone.txt").unlink()
        setup_proc, exports = self.setup_session("--owned-path", "gone.txt")
        proc = self.commit_session(
            setup_proc, exports,
            "--stage", "gone.txt", "--subject", "drop the tracked file",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        shown = self.git("show", "--name-status", "--format=", landing).stdout
        self.assertIn("D\tgone.txt", shown)

    def test_absent_untracked_declaration_refuses_named(self) -> None:
        self.init_fixture_repo(branch="feature/PROJ-1-done-run")
        setup_proc, exports = self.setup_session("--owned-path", "ghost.txt")
        count_before = self.commit_count()
        proc = self.commit_session(
            setup_proc, exports,
            "--stage", "ghost.txt", "--subject", "typo declaration",
        )
        self.assertEqual(proc.returncode, 3)
        self.assertIn("declared path is absent and not tracked: ghost.txt",
                      proc.stderr)
        self.assertEqual(self.commit_count(), count_before)

    def test_deliverables_skip_worktree_absent_declared_path(self) -> None:
        self.init_fixture_repo(branch="feature/PROJ-1-done-run")
        plan_rel = "docs/history/plans/2026-01-01-old-plan.md"
        (self.fixture / plan_rel).parent.mkdir(parents=True, exist_ok=True)
        (self.fixture / plan_rel).write_text("# old plan\n")
        self.git("add", plan_rel)
        self.git("commit", "-qm", "add old plan")
        (self.fixture / "kept.txt").write_text("kept\nwork\n")
        kept_rel = "docs/history/plans/2026-01-02-kept-plan.md"
        (self.fixture / kept_rel).write_text("# kept plan\nwork\n")
        self.stage_deletion_already_staged(plan_rel)
        setup_proc, exports = self.setup_session(
            "--owned-path", plan_rel, "--owned-path", kept_rel,
        )
        proc = self.commit_session(
            setup_proc, exports,
            "--stage", plan_rel, "--stage", kept_rel,
            "--subject", "retire the plan, keep the edit",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        combined = proc.stdout + proc.stderr
        # the deleted plan's path entered no deliverables surface: no
        # deliverables or stale-line machinery line may name it (the sweep
        # gates attribute the staged deletion elsewhere, which stays legal)
        offenders = [
            ln for ln in combined.splitlines()
            if plan_rel in ln
            and ("deliverable" in ln.lower() or "stale" in ln.lower())
        ]
        self.assertEqual(offenders, [])
        # the kept plan's deliverables line did reach the sweep (the
        # readiness gate names it), proving the append still runs for
        # existing paths
        self.assertIn(kept_rel, combined)

    def test_base_present_deletion_passes_stage5(self) -> None:
        self.init_fixture_repo(branch="feature/PROJ-1-done-run")
        (self.fixture / "old.txt").write_text("old\n")
        self.git("add", "old.txt")
        self.git("commit", "-qm", "add old")
        seed_sha = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("update-ref", "refs/remotes/origin/main", seed_sha)
        self.git("symbolic-ref", "refs/remotes/origin/HEAD",
                 "refs/remotes/origin/main")
        (self.fixture / "new.txt").write_text("new work\n")
        self.git("add", "new.txt")
        self.git("commit", "-qm", "add new work")
        self.stage_deletion_already_staged("old.txt")
        setup_proc, exports = self.setup_session(
            "--owned-path", "old.txt", "--owned-path", "new.txt",
        )
        proc = self.commit_session(
            setup_proc, exports,
            "--stage", "old.txt", "--stage", "new.txt",
            "--subject", "drop the base-present file",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("declared deletion is the set's own removal",
                      proc.stdout + proc.stderr)
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        shown = self.git("show", "--name-status", "--format=", landing).stdout
        self.assertIn("D\told.txt", shown)

    def test_mixed_set_lands_edit_beside_already_staged_deletion(self) -> None:
        self.init_fixture_repo(branch="feature/PROJ-1-done-run")
        (self.fixture / "artifact.txt").write_text("artifact\n")
        self.git("add", "artifact.txt")
        self.git("commit", "-qm", "add artifact")
        (self.fixture / "seed.txt").write_text("seed\nwork\n")
        self.stage_deletion_already_staged("artifact.txt")
        setup_proc, exports = self.setup_session(
            "--owned-path", "seed.txt", "--owned-path", "artifact.txt",
        )
        proc = self.commit_session(
            setup_proc, exports,
            "--stage", "seed.txt", "--stage", "artifact.txt",
            "--subject", "edit the seed, drop the artifact",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        shown = self.git("show", "--name-status", "--format=", landing).stdout
        self.assertIn("M\tseed.txt", shown)
        self.assertIn("D\tartifact.txt", shown)

    def test_unrelated_staged_deletion_refuses_at_scope_guard(self) -> None:
        self.init_fixture_repo(branch="feature/PROJ-1-done-run")
        (self.fixture / "stranger.txt").write_text("stranger\n")
        self.git("add", "stranger.txt")
        self.git("commit", "-qm", "add stranger")
        (self.fixture / "new.txt").write_text("session work\n")
        self.stage_deletion_already_staged("stranger.txt")
        setup_proc, exports = self.setup_session("--owned-path", "new.txt")
        count_before = self.commit_count()
        proc = self.commit_session(
            setup_proc, exports,
            "--stage", "new.txt", "--subject", "sweep a stranger deletion in",
        )
        self.assertNotEqual(proc.returncode, 0)
        combined = proc.stdout + proc.stderr
        self.assertIn("stranger.txt", combined)
        self.assertIn("OUTCOME: fail", combined)
        self.assertEqual(self.commit_count(), count_before)
        stages = self.trace_stages(self.commit_env() | exports)
        self.assertEqual(stages[-1], "staged-scope-guard")


class DoneRunDirtCorrectionSetTest(FixtureMixin, unittest.TestCase):
    """Task 1 witnesses (plan
    docs/history/plans/2026-10-22-done-dirt-regression-valid-correction-path.md):
    the invocation-scoped --authorize-dirt-correction finite path/blob
    mapping bound to the live run tuple: exact staged-blob and captured-tree
    binding, per-path regression lifting at the shared captured-tree
    boundary, and every named refusal with HEAD and the ledger unchanged."""

    WORK_BASE = "m1\nm2\n"
    WORK_GAINED = "m1\nm2\nWORKGAINED\n"
    WORK_DIRT = "m2\nm2\n"
    OTHER_BASE = "p1\np2\n"
    OTHER_GAINED = "p1\np2\nOTHERGAINED\n"
    OTHER_DIRT = "p2\np2\n"

    def correction_fixture(self) -> tuple[dict, str, dict]:
        """A two-file regressive staging wired to an origin/HEAD merge
        base; returns (setup exports, prior HEAD, {path: staged blob})."""
        self.init_fixture_repo(branch="feature/PROJ-1234-done-run")
        (self.fixture / "work.txt").write_text(self.WORK_BASE)
        (self.fixture / "other.txt").write_text(self.OTHER_BASE)
        self.git("add", "work.txt", "other.txt")
        self.git("commit", "-qm", "base the corrected files")
        base_sha = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("update-ref", "refs/remotes/origin/main", base_sha)
        self.git("symbolic-ref", "refs/remotes/origin/HEAD",
                 "refs/remotes/origin/main")
        (self.fixture / "work.txt").write_text(self.WORK_GAINED)
        (self.fixture / "other.txt").write_text(self.OTHER_GAINED)
        self.git("add", "work.txt", "other.txt")
        self.git("commit", "-qm", "gain content in both files")
        prior_head = self.git("rev-parse", "HEAD").stdout.strip()
        blobs = {}
        for rel, content in (
            ("work.txt", self.WORK_DIRT),
            ("other.txt", self.OTHER_DIRT),
        ):
            (self.fixture / rel).write_text(content)
            self.git("add", rel)
            blobs[rel] = self.git("ls-files", "-s", rel).stdout.split()[1]
        setup_proc, exports = self.setup_session(
            "--owned-path", "work.txt", "--owned-path", "other.txt",
        )
        return exports, prior_head, blobs

    def assert_refused(self, proc: subprocess.CompletedProcess, exports: dict,
                       prior_head: str, *fragments: str) -> None:
        combined = proc.stdout + proc.stderr
        self.assertNotEqual(proc.returncode, 0, combined)
        for fragment in fragments:
            self.assertIn(fragment, combined)
        self.assertEqual(self.git("rev-parse", "HEAD").stdout.strip(), prior_head)
        ledger = self.done_session() / (
            f"owned-commits-{exports['DONE_RUN_ID']}.txt"
        )
        self.assertFalse(ledger.exists())

    def test_matching_multi_file_correction_set_lands_every_declared_path(self) -> None:
        exports, prior_head, blobs = self.correction_fixture()
        count_before = self.commit_count()
        proc = self.commit_session(
            None, exports,
            "--stage", "work.txt", "--stage", "other.txt",
            "--authorize-dirt-correction", "work.txt", blobs["work.txt"],
            "--authorize-dirt-correction", "other.txt", blobs["other.txt"],
            "--subject", "land the directed contract correction",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        parents = self.git("rev-list", "--parents", "-1", "HEAD").stdout.split()
        self.assertEqual(parents, [landing, prior_head])
        self.assertEqual(
            self.git("rev-parse", "HEAD:work.txt").stdout.strip(),
            blobs["work.txt"],
        )
        self.assertEqual(
            self.git("rev-parse", "HEAD:other.txt").stdout.strip(),
            blobs["other.txt"],
        )
        ledger = self.done_session() / (
            f"owned-commits-{exports['DONE_RUN_ID']}.txt"
        )
        self.assertEqual(ledger.read_text().splitlines(), [landing])
        self.assertEqual(self.commit_count(), count_before + 1)
        combined = proc.stdout + proc.stderr
        # the gate reported exactly the correction set's regressed paths and
        # each was lifted once for this invocation
        self.assertIn("dirt REGRESSION: work.txt", combined)
        self.assertIn("dirt REGRESSION: other.txt", combined)
        self.assertEqual(
            combined.count(
                "authorized dirt correction accepted for this invocation"
            ),
            2,
        )
        stages = self.trace_stages(self.commit_env() | exports)
        # exactly one dirt-gate invocation, at the captured-tree boundary
        self.assertEqual(stages.count("dirt-regression-guard"), 1)
        self.assertLess(
            stages.index("landing-sweep"), stages.index("dirt-regression-guard")
        )

    def test_witnessed_merge_lock_restoration_without_authorization_refuses(self) -> None:
        exports, prior_head, _ = self.correction_fixture()
        count_before = self.commit_count()
        proc = self.commit_session(
            None, exports,
            "--stage", "work.txt", "--stage", "other.txt",
            "--subject", "land an unauthorized merge-lock restoration",
        )
        self.assert_refused(proc, exports, prior_head, "dirt REGRESSION")
        self.assertEqual(self.commit_count(), count_before)
        stages = self.trace_stages(self.commit_env() | exports)
        self.assertEqual(stages[-1], "dirt-regression-guard")

    def test_partial_correction_set_leaves_unmatched_regression_refused(self) -> None:
        exports, prior_head, blobs = self.correction_fixture()
        proc = self.commit_session(
            None, exports,
            "--stage", "work.txt", "--stage", "other.txt",
            "--authorize-dirt-correction", "work.txt", blobs["work.txt"],
            "--subject", "authorize one correction beside an unmatched one",
        )
        self.assert_refused(
            proc, exports, prior_head,
            "unmatched regression in the captured tree: other.txt",
        )
        combined = proc.stdout + proc.stderr
        # the matching path was lifted; only the unmatched one refused
        self.assertIn(
            "authorized dirt correction accepted for this invocation: work.txt",
            combined,
        )

    def test_mismatched_staged_blob_refuses(self) -> None:
        exports, prior_head, _ = self.correction_fixture()
        head_blob = self.git("rev-parse", "HEAD:work.txt").stdout.strip()
        proc = self.commit_session(
            None, exports,
            "--stage", "work.txt", "--stage", "other.txt",
            "--authorize-dirt-correction", "work.txt", head_blob,
            "--subject", "authorize the wrong blob",
        )
        self.assert_refused(proc, exports, prior_head,
                            "does not equal the expected blob")

    def test_undeclared_correction_path_refuses(self) -> None:
        exports, prior_head, blobs = self.correction_fixture()
        proc = self.commit_session(
            None, exports,
            "--stage", "work.txt", "--stage", "other.txt",
            "--authorize-dirt-correction", "elsewhere.txt", blobs["work.txt"],
            "--subject", "authorize a path outside the declared set",
        )
        self.assert_refused(proc, exports, prior_head,
                            "not in the declared --stage set: elsewhere.txt")

    def test_stale_run_tuple_refuses(self) -> None:
        exports, prior_head, blobs = self.correction_fixture()
        manifest = Path(exports["DONE_RUN_MANIFEST"])
        record = json.loads(manifest.read_text())
        record["complete"] = True
        manifest.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        proc = self.commit_session(
            None, exports,
            "--stage", "work.txt", "--stage", "other.txt",
            "--authorize-dirt-correction", "work.txt", blobs["work.txt"],
            "--subject", "authorize over a finalized run",
        )
        self.assert_refused(proc, exports, prior_head,
                            "the run boundary is finalized")

    def test_duplicate_correction_path_is_a_usage_error(self) -> None:
        self.init_fixture_repo()
        proc = self.run_commit(
            "--stage", "seed.txt",
            "--authorize-dirt-correction", "a.txt",
            "0123456789abcdef0123456789abcdef01234567",
            "--authorize-dirt-correction", "a.txt",
            "0123456789abcdef0123456789abcdef01234568",
            "--subject", "two entries for one path",
        )
        self.assertEqual(proc.returncode, 3)
        self.assertIn(
            "given more than once for path: a.txt", proc.stderr
        )

    def test_malformed_blob_is_a_usage_error(self) -> None:
        self.init_fixture_repo()
        proc = self.run_commit(
            "--stage", "seed.txt",
            "--authorize-dirt-correction", "a.txt", "nothex",
            "--subject", "a malformed expected blob",
        )
        self.assertEqual(proc.returncode, 3)
        self.assertIn("malformed expected blob id: nothex", proc.stderr)

    def test_missing_blob_value_is_a_usage_error(self) -> None:
        self.init_fixture_repo()
        proc = self.run_commit(
            "--stage", "seed.txt",
            "--authorize-dirt-correction", "a.txt",
            "--subject", "missing the blob value",
        )
        self.assertEqual(proc.returncode, 3)
        self.assertIn(
            "needs <repo-relative-path> <expected-blob-id>", proc.stderr
        )

    def binding_mutation_fixture(self) -> tuple[dict, str, str]:
        """work.txt: HEAD gained 'a\\nold \\n' over base 'a\\nold\\n'; the
        staged state restores the vintage bytes, which is both a cached-diff
        ancestor match and a formatting-only candidate against HEAD.
        new.txt carries a plain edit so the landing stays reachable after
        the formatting revert. Returns (exports, prior HEAD, vintage blob)."""
        self.init_fixture_repo(branch="feature/PROJ-1234-done-run")
        (self.fixture / "work.txt").write_text("a\nold\n")
        self.git("add", "work.txt")
        self.git("commit", "-qm", "base work content")
        base_sha = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("update-ref", "refs/remotes/origin/main", base_sha)
        self.git("symbolic-ref", "refs/remotes/origin/HEAD",
                 "refs/remotes/origin/main")
        (self.fixture / "work.txt").write_text("a\nold \n")
        (self.fixture / "new.txt").write_text("new work\n")
        self.git("add", "work.txt", "new.txt")
        self.git("commit", "-qm", "gain trailing space and add new work")
        (self.fixture / "new.txt").write_text("new work edited\n")
        self.git("add", "new.txt")
        (self.fixture / "work.txt").write_text("a\nold\n")
        self.git("add", "work.txt")
        vintage_blob = self.git("rev-parse", "HEAD~1:work.txt").stdout.strip()
        prior_head = self.git("rev-parse", "HEAD").stdout.strip()
        setup_proc, exports = self.setup_session(
            "--owned-path", "work.txt", "--owned-path", "new.txt",
        )
        return exports, prior_head, vintage_blob

    def test_authorized_path_mutation_after_binding_refuses_on_captured_tree(self) -> None:
        """The --revert-formatting arm mutates the authorized path after the
        staging binding but before the tree capture: exactly one gate call
        runs on the captured tree and the run refuses with HEAD and the
        ledger unchanged."""
        exports, prior_head, vintage_blob = self.binding_mutation_fixture()
        count_before = self.commit_count()
        env = self.commit_env()
        env.update(exports)
        proc = self.run_commit(
            "--stage", "work.txt", "--stage", "new.txt",
            "--authorize-ancestor-restoration", "work.txt", vintage_blob,
            "--authorize-dirt-correction", "work.txt", vintage_blob,
            "--revert-formatting", "work.txt",
            "--subject", "revert the authorized path after binding",
            env=env,
        )
        self.assert_refused(
            proc, exports, prior_head,
            "captured tree's blob for work.txt",
            "does not equal the expected blob",
        )
        self.assertEqual(self.commit_count(), count_before)
        stages = self.trace_stages(env)
        self.assertEqual(stages.count("dirt-regression-guard"), 1)

    def authorized_blob_fixture(
        self, head_bytes: bytes, staged_bytes: bytes,
    ) -> tuple[dict, str, str]:
        """work.txt: base 's1\\ns2\\n', HEAD content exactly head_bytes, and
        the staged content exactly staged_bytes; returns (exports, prior
        HEAD, the staged blob id)."""
        self.init_fixture_repo(branch="feature/PROJ-1234-done-run")
        (self.fixture / "work.txt").write_text("s1\ns2\n")
        self.git("add", "work.txt")
        self.git("commit", "-qm", "base work content")
        base_sha = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("update-ref", "refs/remotes/origin/main", base_sha)
        self.git("symbolic-ref", "refs/remotes/origin/HEAD",
                 "refs/remotes/origin/main")
        (self.fixture / "work.txt").write_bytes(head_bytes)
        self.git("add", "work.txt")
        self.git("commit", "-qm", "gain head content")
        prior_head = self.git("rev-parse", "HEAD").stdout.strip()
        (self.fixture / "work.txt").write_bytes(staged_bytes)
        self.git("add", "work.txt")
        blob = self.git("ls-files", "-s", "work.txt").stdout.split()[1]
        setup_proc, exports = self.setup_session("--owned-path", "work.txt")
        return exports, prior_head, blob

    def test_indeterminate_authorized_classification_refuses(self) -> None:
        """An authorized correction whose captured-tree classification is
        indeterminate refuses without a landing commit: no authorization
        suppresses a non-regression classifier outcome."""
        exports, prior_head, blob = self.authorized_blob_fixture(
            b"s1\ns2\nGAINED\n", b"\x00\x01binary\n"
        )
        proc = self.commit_session(
            None, exports,
            "--stage", "work.txt",
            "--authorize-dirt-correction", "work.txt", blob,
            "--subject", "authorize a binary restoration",
        )
        self.assert_refused(
            proc, exports, prior_head,
            "dirt regression guard refused the captured tree (rc=2)",
        )
        combined = proc.stdout + proc.stderr
        self.assertIn("dirt INDETERMINATE: work.txt", combined)

    def test_tool_error_authorized_classification_refuses(self) -> None:
        """The gate's strict-UTF-8 boundary is a tool error (rc=3) even
        under an authorization: the authorized path's staged bytes equal
        HEAD's undecodable blob (no diff for the sweep to trip over), a
        second declared path keeps the landing live, and the gate still
        fails closed reading the captured tree's content."""
        latin1 = "s1\ns2\nlatin1-caf\xe9\n".encode("latin-1")
        exports, prior_head, blob = self.authorized_blob_fixture(
            latin1, latin1
        )
        (self.fixture / "new.txt").write_text("new work edited\n")
        self.git("add", "new.txt")
        proc = self.commit_session(
            None, exports,
            "--stage", "work.txt", "--stage", "new.txt",
            "--authorize-dirt-correction", "work.txt", blob,
            "--subject", "authorize an undecodable restoration",
        )
        self.assert_refused(
            proc, exports, prior_head,
            "dirt regression guard refused the captured tree (rc=3)",
        )


class DoneRunDirtCachedDiffAuthorizationSeparationTest(FixtureMixin, unittest.TestCase):
    """Neither authorization satisfies the other guard (plan Standing
    constraints): a dirt-only authorization for a cached-diff regression and
    a cached-diff-only authorization for a dirt regression each refuse with
    no commit; only both together land the exact staged restoration."""

    VINTAGE = "a\nold\n"
    GAINED = "a\nnew\n"

    def dual_guard_fixture(self) -> tuple[dict, str, str]:
        self.init_fixture_repo(branch="feature/PROJ-1234-done-run")
        (self.fixture / "work.txt").write_text(self.VINTAGE)
        self.git("add", "work.txt")
        self.git("commit", "-qm", "base work content")
        base_sha = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("update-ref", "refs/remotes/origin/main", base_sha)
        self.git("symbolic-ref", "refs/remotes/origin/HEAD",
                 "refs/remotes/origin/main")
        (self.fixture / "work.txt").write_text(self.GAINED)
        self.git("add", "work.txt")
        self.git("commit", "-qm", "gain head content")
        (self.fixture / "work.txt").write_text(self.VINTAGE)
        self.git("add", "work.txt")
        vintage_blob = self.git("rev-parse", "HEAD~1:work.txt").stdout.strip()
        prior_head = self.git("rev-parse", "HEAD").stdout.strip()
        setup_proc, exports = self.setup_session("--owned-path", "work.txt")
        return exports, prior_head, vintage_blob

    def test_dirt_only_authorization_leaves_cached_diff_refusal(self) -> None:
        exports, prior_head, vintage_blob = self.dual_guard_fixture()
        proc = self.commit_session(
            None, exports,
            "--stage", "work.txt",
            "--authorize-dirt-correction", "work.txt", vintage_blob,
            "--subject", "dirt authorization cannot lift the cached-diff guard",
        )
        self.assertNotEqual(proc.returncode, 0)
        combined = proc.stdout + proc.stderr
        self.assertIn("leaked revert", combined)
        self.assertEqual(
            self.git("rev-parse", "HEAD").stdout.strip(), prior_head
        )
        stages = self.trace_stages(self.commit_env() | exports)
        self.assertEqual(stages[-1], "cached-diff-guard")

    def test_cached_diff_only_authorization_leaves_dirt_refusal(self) -> None:
        exports, prior_head, vintage_blob = self.dual_guard_fixture()
        proc = self.commit_session(
            None, exports,
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", vintage_blob,
            "--subject", "cached-diff authorization cannot lift the dirt gate",
        )
        self.assertNotEqual(proc.returncode, 0)
        combined = proc.stdout + proc.stderr
        self.assertIn("dirt REGRESSION: work.txt", combined)
        self.assertIn(
            "unmatched regression in the captured tree: work.txt", combined
        )
        self.assertEqual(
            self.git("rev-parse", "HEAD").stdout.strip(), prior_head
        )
        ledger = self.done_session() / (
            f"owned-commits-{exports['DONE_RUN_ID']}.txt"
        )
        self.assertFalse(ledger.exists())
        stages = self.trace_stages(self.commit_env() | exports)
        self.assertEqual(stages[-1], "dirt-regression-guard")

    def test_both_authorizations_land_the_exact_restoration(self) -> None:
        exports, prior_head, vintage_blob = self.dual_guard_fixture()
        count_before = self.commit_count()
        proc = self.commit_session(
            None, exports,
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", vintage_blob,
            "--authorize-dirt-correction", "work.txt", vintage_blob,
            "--subject", "land the doubly directed restoration",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        parents = self.git("rev-list", "--parents", "-1", "HEAD").stdout.split()
        self.assertEqual(parents, [landing, prior_head])
        self.assertEqual(
            self.git("rev-parse", "HEAD:work.txt").stdout.strip(),
            vintage_blob,
        )
        ledger = self.done_session() / (
            f"owned-commits-{exports['DONE_RUN_ID']}.txt"
        )
        self.assertEqual(ledger.read_text().splitlines(), [landing])
        self.assertEqual(self.commit_count(), count_before + 1)


class DoneRunCapturedTreeLandingTest(FixtureMixin, unittest.TestCase):
    """The shared captured-tree landing for primary-repository commits:
    hook refusals leave the ref and ledger unchanged, mutations staged
    after the final tree check stay excluded from the landed commit, and a
    checkout race after the final check advances only the captured branch
    while the output and ledger name it and post-commit sees the moved
    HEAD."""

    def install_hook(self, name: str, body: str) -> Path:
        hooks = self.fixture / ".git" / "hooks"
        hooks.mkdir(exist_ok=True)
        hook = hooks / name
        hook.write_text("#!/bin/sh\n" + body)
        hook.chmod(0o755)
        return hook

    def plain_edit_fixture(self) -> tuple[dict, str]:
        self.init_fixture_repo(branch="feature/PROJ-1234-done-run")
        (self.fixture / "seed.txt").write_text("seed\nwork\n")
        prior_head = self.git("rev-parse", "HEAD").stdout.strip()
        setup_proc, exports = self.setup_session("--owned-path", "seed.txt")
        return exports, prior_head

    def test_ordinary_hook_scope_change_refuses(self) -> None:
        exports, prior_head = self.plain_edit_fixture()
        count_before = self.commit_count()
        self.install_hook(
            "pre-commit",
            "printf 'stranger bytes\\n' > stranger.txt\n"
            "git add stranger.txt\n",
        )
        proc = self.commit_session(
            None, exports,
            "--stage", "seed.txt",
            "--subject", "a hook stages a foreign scope change",
        )
        self.assertNotEqual(proc.returncode, 0)
        combined = proc.stdout + proc.stderr
        self.assertIn("changed the staged index tree", combined)
        self.assertEqual(self.commit_count(), count_before)
        ledger = self.done_session() / (
            f"owned-commits-{exports['DONE_RUN_ID']}.txt"
        )
        self.assertFalse(ledger.exists())

    def test_post_final_check_index_mutation_stays_staged_and_excluded(self) -> None:
        exports, _ = self.plain_edit_fixture()
        self.install_hook(
            "reference-transaction",
            "[ \"$1\" = prepared ] || exit 0\n"
            "found=''\n"
            "while read -r _old _new ref; do\n"
            "  case \"$ref\" in\n"
            "    refs/heads/feature/PROJ-1234-done-run) found=1;;\n"
            "  esac\n"
            "done\n"
            "[ -n \"$found\" ] || exit 0\n"
            "printf 'stranger race\\n' > stranger.txt\n"
            "git add stranger.txt\n",
        )
        proc = self.commit_session(
            None, exports,
            "--stage", "seed.txt",
            "--subject", "a hook mutates the index after the final tree check",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        landing = self.git("rev-parse", "HEAD").stdout.strip()
        shown = self.git("show", "--name-only", "--format=", landing).stdout
        self.assertIn("seed.txt", shown)
        self.assertNotIn("stranger.txt", shown)
        # the later mutation remains staged and excluded from the landing
        staged = self.git("diff", "--cached", "--name-only").stdout
        self.assertIn("stranger.txt", staged)

    def test_checkout_race_after_final_check_advances_only_captured_branch(self) -> None:
        exports, prior_head = self.plain_edit_fixture()
        race_branch = "feature/PROJ-1234-race-b"
        self.git("branch", race_branch, prior_head)
        probe = self.tmp / "probe-post-commit.txt"
        self.install_hook(
            "reference-transaction",
            "[ \"$1\" = prepared ] || exit 0\n"
            "found=''\n"
            "while read -r _old _new ref; do\n"
            "  case \"$ref\" in\n"
            "    refs/heads/feature/PROJ-1234-done-run) found=1;;\n"
            "  esac\n"
            "done\n"
            "[ -n \"$found\" ] || exit 0\n"
            "# race the wrapper's final check: retarget HEAD inside the\n"
            "# transaction window (direct symref write; symbolic-ref would\n"
            "# need the HEAD lock the transaction itself holds)\n"
            "printf 'ref: refs/heads/" + race_branch + "\\n' > "
            "\"$(git rev-parse --absolute-git-dir)/HEAD\"\n",
        )
        self.install_hook(
            "post-commit",
            "printf 'head=%s\\n' \"$(git rev-parse HEAD)\" >> '" + str(probe) + "'\n",
        )
        proc = self.commit_session(
            None, exports,
            "--stage", "seed.txt",
            "--subject", "land through a checkout race after the final check",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        # HEAD was retargeted by the race: read the landing from the
        # captured branch, not from HEAD.
        landing = self.git(
            "rev-parse", "refs/heads/feature/PROJ-1234-done-run"
        ).stdout.strip()
        # only the captured branch advanced
        parents = self.git("rev-list", "--parents", "-1",
                           "refs/heads/feature/PROJ-1234-done-run").stdout.split()
        self.assertEqual(parents, [landing, prior_head])
        # the race destination and HEAD are unchanged
        self.assertEqual(
            self.git("rev-parse", f"refs/heads/{race_branch}").stdout.strip(),
            prior_head,
        )
        self.assertEqual(
            self.git("symbolic-ref", "--short", "-q", "HEAD").stdout.strip(),
            race_branch,
        )
        self.assertEqual(
            self.git("rev-parse", "HEAD").stdout.strip(), prior_head
        )
        # the output and ledger name the captured destination's landing
        combined = proc.stdout + proc.stderr
        self.assertIn(
            "captured branch refs/heads/feature/PROJ-1234-done-run", combined
        )
        self.assertIn(f"landed {landing}", combined)
        ledger = self.done_session() / (
            f"owned-commits-{exports['DONE_RUN_ID']}.txt"
        )
        self.assertEqual(ledger.read_text().splitlines(), [landing])
        # post-commit ran after the swap and observed the moved HEAD
        self.assertIn(f"head={prior_head}", probe.read_text())


class DoneRunGitEnvironmentIsolationTest(FixtureMixin, unittest.TestCase):
    """Fixture Git isolation witnesses (plan Task 1): a host Git selector in
    the wrapper-test environment is cleared and the fixture-scoped config
    keeps host/global config overrides out of the fixture's Git calls."""

    POISONED_SELECTORS = (
        "GIT_DIR", "GIT_INDEX_FILE", "GIT_CONFIG_COUNT",
        "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0",
        "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CEILING_DIRECTORIES", "GIT_NAMESPACE", "GIT_SHALLOW_FILE",
    )

    def setUp(self) -> None:
        # Simulate a host session's Git selectors arriving in the ambient
        # environment before the fixture harness runs; the harness must
        # clear them so every Git call operates on the fixture only. The
        # real ambient values are captured BEFORE the poison and restored
        # by a cleanup registered first (runs last, after the mixin's own
        # restore, which otherwise re-applies the poison as its "prior").
        real = {name: os.environ.get(name) for name in self.POISONED_SELECTORS}
        self._real_ambient = real
        self.addCleanup(self._restore_real_ambient, real)
        os.environ["GIT_DIR"] = "/nonexistent-host-git-dir"
        os.environ["GIT_INDEX_FILE"] = "/nonexistent-host-git-index"
        os.environ["GIT_CONFIG_COUNT"] = "1"
        os.environ["GIT_CONFIG_KEY_0"] = "user.name"
        os.environ["GIT_CONFIG_VALUE_0"] = "Host Override"
        os.environ["GIT_OBJECT_DIRECTORY"] = "/nonexistent-host-objects"
        os.environ["GIT_ALTERNATE_OBJECT_DIRECTORIES"] = (
            "/nonexistent-host-alternates"
        )
        os.environ["GIT_CEILING_DIRECTORIES"] = "/nonexistent-host-ceiling"
        os.environ["GIT_NAMESPACE"] = "host-namespace"
        os.environ["GIT_SHALLOW_FILE"] = "/nonexistent-host-shallow"
        super().setUp()

    def tearDown(self) -> None:
        # The restore fix is asserted, not trusted: run the registered
        # cleanups now (the mixin's re-apply of the poison, then the
        # real-ambient restore) and verify every poisoned selector ends up
        # byte-equal to the captured real mapping before the fixture tmp
        # tree is removed.
        self.doCleanups()
        for name, value in self._real_ambient.items():
            self.assertEqual(os.environ.get(name), value, name)
        super().tearDown()

    @staticmethod
    def _restore_real_ambient(real: dict) -> None:
        for name, value in real.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    def test_host_selectors_cleared_and_config_isolated_to_fixture(self) -> None:
        for var in self.POISONED_SELECTORS:
            self.assertNotIn(var, os.environ)
        self.assertEqual(os.environ.get("GIT_CONFIG_NOSYSTEM"), "1")
        self.init_fixture_repo(branch="feature/PROJ-1234-done-run")
        (self.fixture / "seed.txt").write_text("seed\nwork\n")
        count_before = self.commit_count()
        setup_proc, exports = self.setup_session("--owned-path", "seed.txt")
        proc = self.commit_session(
            setup_proc, exports,
            "--stage", "seed.txt",
            "--subject", "land under cleared host selectors",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertEqual(self.commit_count(), count_before + 1)
        # the landed identity is the fixture's, never the host override
        self.assertEqual(
            self.git("log", "-1", "--format=%an").stdout.strip(), "t"
        )


class DoneRunCapturedTreeLandingFenceTest(FixtureMixin, unittest.TestCase):
    """Captured-tree landing hardening witnesses: a drifted dirt-gate rc=1
    answer (no machine-readable regression paths, or no contractual OUTCOME
    line) refuses instead of failing open, and a foreign path staged into
    the index inside the capture window (between the staged-scope guard and
    the tree capture) refuses before the ref update. Both arms run a private
    runner copy whose helper resolution sees a doctored module, so the drift
    is injected at the exact boundary the landing owns."""

    TEMP_RUNNER_HELPERS = (
        "revert_set_classifier.py", "staged_scope_guard.py",
        "done_sweep_gates.sh", "done_sweep_gates_lib.py",
        "dirt_regression_gate.py", "reverse_squash_guard.py",
        "docs_branch_sync.sh",
    )

    DOCTOR_GATE_NO_PATH_LINES = (
        "import sys\n"
        "print('dirt REGRESSION: work.txt (restores base-era text over lines "
        "HEAD gained since deadbeef)')\n"
        "print('OUTCOME: fail')\n"
        "sys.exit(1)\n"
    )
    DOCTOR_GATE_NO_OUTCOME = (
        "import sys\n"
        "print('dirt REGRESSION: work.txt (restores base-era text over lines "
        "HEAD gained since deadbeef)')\n"
        "sys.exit(1)\n"
    )
    DOCTOR_RS_GUARD_STAGES_FOREIGN = (
        "import subprocess\n"
        "with open('stranger-window.txt', 'w') as handle:\n"
        "    handle.write('staged in the capture window\\n')\n"
        "subprocess.run(['git', 'add', 'stranger-window.txt'], check=True)\n"
        "print('OUTCOME: pass')\n"
    )

    def temp_runner_dir(self, doctor: dict[str, str]) -> Path:
        """A private runner copy whose resolve_helper sees this directory
        first: real helpers are symlinked in, and each doctored name is
        replaced by the given body."""
        runner_dir = self.tmp / "runner"
        runner_dir.mkdir()
        shutil.copy2(RUNNER, runner_dir / "done_run.sh")
        for name in self.TEMP_RUNNER_HELPERS:
            os.symlink(REPO_ROOT / "scripts" / name, runner_dir / name)
        for name, body in doctor.items():
            target = runner_dir / name
            if target.is_symlink() or target.exists():
                target.unlink()
            target.write_text(body)
        return runner_dir

    def run_temp_commit(
        self, runner_dir: Path, exports: dict, *args: str,
    ) -> subprocess.CompletedProcess:
        env = self.commit_env()
        env.update(exports)
        return subprocess.run(
            ["bash", str(runner_dir / "done_run.sh"), "commit", *args],
            cwd=str(self.fixture),
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
        )

    def gated_fixture(self) -> tuple[dict, str]:
        """A declared HEAD-tracked staged edit wired to an origin/HEAD merge
        base, so the landing's capture window and dirt-gate stage are both
        reached; returns (setup exports, prior HEAD)."""
        self.init_fixture_repo(branch="feature/PROJ-1234-done-run")
        (self.fixture / "work.txt").write_text("a\nb\n")
        self.git("add", "work.txt")
        self.git("commit", "-qm", "base work content")
        base_sha = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("update-ref", "refs/remotes/origin/main", base_sha)
        self.git("symbolic-ref", "refs/remotes/origin/HEAD",
                 "refs/remotes/origin/main")
        (self.fixture / "work.txt").write_text("a\nb\ngained\n")
        self.git("add", "work.txt")
        self.git("commit", "-qm", "gain head content")
        prior_head = self.git("rev-parse", "HEAD").stdout.strip()
        (self.fixture / "work.txt").write_text("a\nb\ngained edited\n")
        self.git("add", "work.txt")
        setup_proc, exports = self.setup_session("--owned-path", "work.txt")
        return exports, prior_head

    def assert_refused_no_landing(
        self, proc: subprocess.CompletedProcess, exports: dict,
        prior_head: str, *fragments: str,
    ) -> None:
        combined = proc.stdout + proc.stderr
        self.assertNotEqual(proc.returncode, 0, combined)
        for fragment in fragments:
            self.assertIn(fragment, combined)
        self.assertEqual(self.git("rev-parse", "HEAD").stdout.strip(), prior_head)
        ledger = self.done_session() / (
            f"owned-commits-{exports['DONE_RUN_ID']}.txt"
        )
        self.assertFalse(ledger.exists())

    def test_rc1_without_parsable_regression_paths_refuses(self) -> None:
        exports, prior_head = self.gated_fixture()
        runner_dir = self.temp_runner_dir({
            "dirt_regression_gate.py": self.DOCTOR_GATE_NO_PATH_LINES,
        })
        proc = self.run_temp_commit(
            runner_dir, exports,
            "--stage", "work.txt", "--boundary-class", "per-task",
            "--subject", "land under a drifted gate answer",
        )
        self.assert_refused_no_landing(
            proc, exports, prior_head,
            "rc=1 named no parsable regression path (helper drift)",
        )

    def test_rc1_without_outcome_line_refuses(self) -> None:
        exports, prior_head = self.gated_fixture()
        runner_dir = self.temp_runner_dir({
            "dirt_regression_gate.py": self.DOCTOR_GATE_NO_OUTCOME,
        })
        proc = self.run_temp_commit(
            runner_dir, exports,
            "--stage", "work.txt", "--boundary-class", "per-task",
            "--subject", "land under an outcome-less gate answer",
        )
        self.assert_refused_no_landing(
            proc, exports, prior_head,
            "no contractual 'OUTCOME: fail' line (helper drift)",
        )

    def test_foreign_staging_in_capture_window_refuses(self) -> None:
        exports, prior_head = self.gated_fixture()
        runner_dir = self.temp_runner_dir({
            "reverse_squash_guard.py": self.DOCTOR_RS_GUARD_STAGES_FOREIGN,
        })
        proc = self.run_temp_commit(
            runner_dir, exports,
            "--stage", "work.txt", "--boundary-class", "per-task",
            "--subject", "land under a capture-window staging race",
        )
        self.assert_refused_no_landing(
            proc, exports, prior_head,
            "a foreign path entered the staged index before the tree "
            "capture: stranger-window.txt",
        )
        # the injected entry remains staged, excluded from any landing
        staged = self.git("diff", "--cached", "--name-only").stdout
        self.assertIn("stranger-window.txt", staged)


class DoneRunCloseoutBaselineArmTest(FixtureMixin, unittest.TestCase):
    """Task 1 (plan 2026-10-18-worktree-closeout-single-start-baseline):
    the commit subcommand's ad-hoc-worktree migration reuses the run's one
    pre-work Phase 0 baseline (exactly one owned plan) or a valid skip
    record (zero or multiple owned plans, the manual scoped copy completed
    before commit), and never captures a late baseline.

    ``manual_scoped_copy`` below is the executable fixture mirror of the
    documented manual scoped-copy procedure the skip arm relies on: it
    enumerates every run-scoped inventory source class, verifies each copy
    by independent digest re-read, records the complete artifact list, and
    reports the transfer incomplete when a source is missing or any digest
    differs."""

    PLAN_REL = "docs/history/plans/2026-10-18-closeout-arm-example.md"
    PLAN_SLUG = "closeout-arm-example"
    PLAN2_REL = "docs/history/plans/2026-10-18-closeout-arm-second.md"
    PLAN2_SLUG = "closeout-arm-second"

    # ---- fixture helpers ------------------------------------------------- #

    def seed_tracked_plan(self, plan_rel: str) -> None:
        plans = self.fixture / "docs" / "history" / "plans"
        plans.mkdir(parents=True, exist_ok=True)
        (self.fixture / plan_rel).write_text("# plan\n", encoding="utf-8")
        self.git("add", plan_rel)
        self.git("commit", "-qm", "plans: fixture owned plan")

    def worktree_session(self, *setup_args: str) -> tuple[Path, dict, dict]:
        """An ad-hoc worktree beside the fixture primary with a setup
        boundary run inside it; returns (worktree, exports, commit env). The
        returned env is the hermetic commit env keyed to the worktree (the
        sweep validators and sync pins ride the same overrides the in-place
        commit tests pin)."""
        worktree = self.tmp / "ad-hoc-wt"
        self.git("worktree", "add", "-b", "closeout-arm-wt-branch", str(worktree))
        (worktree / "seed.txt").write_text("seed\nwork\n", encoding="utf-8")
        env = self.runner_env()
        env["DONE_SWEEP_REPO_ROOT"] = str(worktree)
        setup = subprocess.run(
            ["bash", str(RUNNER), "setup", *setup_args],
            cwd=str(worktree), env=env, capture_output=True, text=True,
            timeout=300,
        )
        self.assertEqual(setup.returncode, 0, setup.stderr)
        # the done-lock session fence is done-lock's status witness, not
        # fixture state under test: remove it so the commit's foreign-dirt
        # gate sees only the declared work
        fence = worktree / ".ai-playbook" / "done-lock.session"
        if fence.exists():
            fence.unlink()
        exports = self.eval_exports(setup.stdout)
        env = self.commit_env()
        env["DONE_SWEEP_REPO_ROOT"] = str(worktree)
        env.update(exports)
        return worktree, exports, env

    def capture_phase0_baseline(self, worktree: Path, slug: str) -> Path:
        slug_dir = worktree / "docs" / "tmp" / "execute-plan" / slug
        slug_dir.mkdir(parents=True, exist_ok=True)
        baseline = slug_dir / "closeout-baseline.json"
        capture = subprocess.run(
            [sys.executable, str(CLOSEOUT_MIGRATE), "capture", "--out", str(baseline)],
            cwd=str(worktree), capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(capture.returncode, 0, capture.stderr)
        return baseline

    def write_run_review_record(self, worktree: Path, name: str) -> Path:
        reviews = worktree / ".ai-playbook" / "reviews"
        reviews.mkdir(parents=True, exist_ok=True)
        record = reviews / name
        record.write_text("# review record\n", encoding="utf-8")
        return record

    def write_run_id_skip_record(self, worktree: Path, run_id: str) -> Path:
        skip = (
            worktree / "docs" / "tmp" / "done-session"
            / f"worktree-migrate-baseline-{run_id}-skip.json"
        )
        skip.parent.mkdir(parents=True, exist_ok=True)
        skip.write_text(
            json.dumps(
                {
                    "skip": True,
                    "reason": "no unique plan baseline; scoped copy recorded",
                    "fallback": "manual scoped copy",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return skip

    def manual_scoped_copy(
        self,
        worktree: Path,
        primary: Path,
        run_id: str,
        owned_plans: list[str],
        owned_reviews: list[str],
        plan_slugs: list[str],
        corrupt_destinations: set[str] | None = None,
    ) -> dict:
        """The documented manual scoped-copy procedure, as an executable
        fixture mirror. Source-class enumeration follows the plan's
        run-scoped inventory; the ignored-path listing only discovers
        candidates under the configured migration roots (never a blanket
        copy instruction); the skip record and every other control input
        are excluded; every copied artifact is verified by source and
        destination digest re-read; a missing source or digest mismatch
        leaves the transfer incomplete with the source worktree untouched."""
        corrupt_destinations = corrupt_destinations or set()
        tmp_root = worktree / "docs" / "tmp"
        reviews = worktree / ".ai-playbook" / "reviews"
        certs = worktree / ".ai-playbook" / "review-certs"
        metrics = tmp_root / "metrics"
        done_session = tmp_root / "done-session"
        entries: list[dict] = []
        excluded: list[str] = []

        def consider(rel: str, source: Path, klass: str) -> None:
            if not source.is_file():
                entries.append({"source": rel, "class": klass, "missing": True})
                return
            data = source.read_bytes()
            destination = primary / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            destination_digest = hashlib.sha256(
                destination.read_bytes()
            ).hexdigest()
            if rel in corrupt_destinations:
                # test injection: damage the copy before verification so the
                # digest mismatch arm is observable end to end
                destination.write_bytes(b"corrupted after copy\n")
                destination_digest = hashlib.sha256(
                    destination.read_bytes()
                ).hexdigest()
            entries.append(
                {
                    "source": rel,
                    "destination": destination.as_posix(),
                    "class": klass,
                    "source_digest": hashlib.sha256(data).hexdigest(),
                    "destination_digest": destination_digest,
                    "verified": (
                        hashlib.sha256(data).hexdigest() == destination_digest
                    ),
                }
            )

        selected: set[str] = set()
        # Class 1: each owned plan's execute-plan session directory.
        for slug in plan_slugs:
            session_dir = tmp_root / "execute-plan" / slug
            if session_dir.is_dir():
                for path in sorted(session_dir.rglob("*")):
                    if not path.is_file():
                        continue
                    rel = path.relative_to(worktree).as_posix()
                    if path.name == "closeout-baseline-skip.json":
                        excluded.append(rel)
                        continue
                    selected.add(rel)
                    consider(rel, path, "execute-plan-session")
        # Class 2: the plan's authoring telemetry file.
        for slug in plan_slugs:
            telemetry = tmp_root / "authoring" / slug / "context.jsonl"
            if telemetry.is_file():
                rel = telemetry.relative_to(worktree).as_posix()
                selected.add(rel)
                consider(rel, telemetry, "authoring-telemetry")
        # Class 3: the plan's metrics archive or its telemetry-absence
        # record (both as applicable).
        for slug in plan_slugs:
            for name, klass in (
                (f"{slug}-telemetry.json", "metrics-archive"),
                (f"{slug}-telemetry-absent.txt", "telemetry-absence-record"),
            ):
                candidate = metrics / name
                if candidate.is_file():
                    rel = candidate.relative_to(worktree).as_posix()
                    selected.add(rel)
                    consider(rel, candidate, klass)
        # Class 4: the plan-owned review-certification seal.
        for slug in plan_slugs:
            seal = certs / f"{slug}-seal.md"
            if seal.is_file():
                rel = seal.relative_to(worktree).as_posix()
                selected.add(rel)
                consider(rel, seal, "review-cert-seal")
        # Class 5: explicitly owned review Markdown plus its required
        # sidecar; a listed review absent from the worktree is a missing
        # source, never silently skipped.
        for review in owned_reviews:
            source = worktree / review
            selected.add(review)
            consider(review, source, "owned-review")
            sidecar = source.with_name(source.stem + ".stats.json")
            if sidecar.is_file():
                rel = sidecar.relative_to(worktree).as_posix()
                selected.add(rel)
                consider(rel, sidecar, "owned-review-sidecar")
        # Class 6: complete review pairs whose extensions.plan_identity
        # matches an owned plan path.
        if reviews.is_dir():
            for sidecar in sorted(reviews.glob("*.stats.json")):
                try:
                    payload = json.loads(sidecar.read_text(encoding="utf-8"))
                except ValueError:
                    continue
                identity = (payload.get("extensions") or {}).get(
                    "plan_identity"
                )
                if identity not in owned_plans:
                    continue
                # the sidecar's record: <stem>.stats.json pairs <stem>.md
                member = sidecar.parent / (
                    sidecar.name[: -len(".stats.json")] + ".md"
                )
                if not member.is_file():
                    continue
                for path in (sidecar, member):
                    rel = path.relative_to(worktree).as_posix()
                    if rel not in selected:
                        selected.add(rel)
                        consider(rel, path, "identity-matched-review-pair")
        # Class 7: done-session files whose names contain the exact RUN_ID;
        # the skip record and the scoped-copy record itself stay control
        # inputs, never transfer candidates.
        if done_session.is_dir() and run_id:
            for path in sorted(done_session.iterdir()):
                if not path.is_file() or run_id not in path.name:
                    continue
                rel = path.relative_to(worktree).as_posix()
                if path.name.endswith("-skip.json") or path.name.startswith(
                    "worktree-scoped-copy-record-"
                ):
                    excluded.append(rel)
                    continue
                selected.add(rel)
                consider(rel, path, "done-session")

        # Control inputs: the plan-deliverables record contributes only
        # entries exactly matching the current owned plan paths (and plan
        # files are never transfer candidates), so a stale prior-run entry
        # selects nothing; the record itself stays a control input and is
        # never a transfer candidate either way.
        deliverables = done_session / "plan-deliverables.txt"
        if deliverables.is_file():
            excluded.append(deliverables.relative_to(worktree).as_posix())
            for row in deliverables.read_text(encoding="utf-8").splitlines():
                row = row.strip()
                if row and row not in owned_plans:
                    excluded.append(row)

        # Discovery, never instruction: the ignored-path listing names
        # run-written candidates under the configured migration roots; a
        # discovered path no class selected and no rule excluded is recorded
        # as an unrelated artifact, never copied.
        discovery = subprocess.run(
            ["git", "-C", str(worktree), "status", "--ignored",
             "--porcelain", "-uall", "--", ".ai-playbook/reviews", "docs/tmp",
             ".ai-playbook/review-certs", ".ai-playbook/metrics"],
            capture_output=True, text=True, check=False,
        ).stdout
        for line in discovery.splitlines():
            raw = line[3:].strip()
            if not raw or " -> " in raw or raw.endswith("/"):
                continue
            path = worktree / raw
            if not path.is_file():
                continue
            rel = path.relative_to(worktree).as_posix()
            if rel not in selected and rel not in excluded:
                excluded.append(rel)

        complete = bool(entries) and all(
            entry.get("verified") and not entry.get("missing")
            for entry in entries
        )
        record_lines = ["# Manual scoped-copy record", ""]
        for entry in entries:
            if entry.get("missing"):
                record_lines.append(
                    f"- MISSING source {entry['source']} ({entry['class']})"
                )
                continue
            record_lines.append(
                f"- {entry['class']}: {entry['source']} -> "
                f"{entry['destination']} source {entry['source_digest']} "
                f"destination {entry['destination_digest']} "
                f"verified {str(entry['verified']).lower()}"
            )
        record_lines.append(f"complete: {str(complete).lower()}")
        record_text = "\n".join(record_lines) + "\n"
        if plan_slugs:
            record_path = (
                tmp_root / "execute-plan" / plan_slugs[0] / "manifest.md"
            )
            record_path.parent.mkdir(parents=True, exist_ok=True)
            with record_path.open("a", encoding="utf-8") as handle:
                handle.write(record_text)
        else:
            record_path = (
                done_session / f"worktree-scoped-copy-record-{run_id}.md"
            )
            record_path.parent.mkdir(parents=True, exist_ok=True)
            record_path.write_text(record_text, encoding="utf-8")
        return {
            "complete": complete,
            "entries": entries,
            "excluded": excluded,
            "record": record_path,
        }

    def run_worktree_commit(
        self, worktree: Path, env: dict, *args: str
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(RUNNER), "commit", *args],
            cwd=str(worktree), env=env, capture_output=True, text=True,
            timeout=300,
        )

    def wt_session(self, worktree: Path) -> Path:
        return worktree / "docs" / "tmp" / "done-session"

    def assert_no_late_baseline_and_no_migration(
        self, worktree: Path, run_id: str
    ) -> None:
        self.assertFalse(
            (self.wt_session(worktree) / f"worktree-migrate-baseline-{run_id}.json").exists(),
            "commit captured a late run-ID baseline",
        )
        self.assertEqual(
            list(self.wt_session(worktree).glob("worktree-migrate-manifest-*.json")),
            [],
            "baseline-based migrate ran on the skip arm",
        )

    # ---- baseline reuse arm (exactly one owned plan) --------------------- #

    def test_single_plan_phase0_baseline_reuse_transfers_new_artifact(self) -> None:
        """[class: REPOSITORY_TEST] A single-plan run's commit reuses the
        plan's canonical Phase 0 baseline: a review record created after the
        baseline and before commit transfers to the primary checkout with a
        verified manifest entry, no run-ID baseline is captured at commit
        time, and the docs sync follows the migration."""
        self.init_fixture_repo()
        self.seed_tracked_plan(self.PLAN_REL)
        worktree, exports, env = self.worktree_session(
            "--owned-path", "seed.txt", "--owned-plan", self.PLAN_REL,
        )
        run_id = exports["DONE_RUN_ID"]
        self.capture_phase0_baseline(worktree, self.PLAN_SLUG)
        record = self.write_run_review_record(
            worktree, "2026-10-18-closeout-arm-example-code-review-r1.md"
        )
        proc = self.run_worktree_commit(
            worktree, env, "--stage", "seed.txt", "--subject", "land the run work",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        combined = proc.stdout + proc.stderr
        transferred = self.fixture / ".ai-playbook" / "reviews" / record.name
        self.assertTrue(transferred.is_file(), combined)
        self.assertEqual(transferred.read_text(encoding="utf-8"), "# review record\n")
        self.assertFalse(
            (self.wt_session(worktree) / f"worktree-migrate-baseline-{run_id}.json").exists(),
            "commit captured a late baseline",
        )
        manifests = list(self.wt_session(worktree).glob("worktree-migrate-manifest-*.json"))
        self.assertEqual(
            manifests, [],
            "one-owned-plan migration wrote the run-id manifest worktree-side",
        )
        primary_manifest = (
            self.fixture / "docs" / "tmp" / "execute-plan"
            / self.PLAN_SLUG / "closeout-migration.json"
        )
        self.assertTrue(primary_manifest.is_file(), combined)
        data = json.loads(primary_manifest.read_text(encoding="utf-8"))
        self.assertTrue(data.get("branch"), "migration manifest lost the branch record")
        self.assertTrue(data["branch"][-1].get("branch"))
        migrated = {entry["source"] for entry in data["migrated"]}
        self.assertIn(f".ai-playbook/reviews/{record.name}", migrated)
        for entry in data["migrated"]:
            self.assertTrue(entry["verified"])
        self.assertIn("docs-branch: sync complete", combined)

    def test_dated_plan_directory_charter_baseline_reuse_transfers(self) -> None:
        """[class: REPOSITORY_TEST] An owned plan that is a dated plan
        directory's PLAN.md charter resolves the date-stripped directory
        session slug: the commit reuses the Phase 0 baseline seeded under
        docs/tmp/execute-plan/<date-stripped-dir-slug>/closeout-baseline.json
        and a post-baseline review record transfers to the primary checkout,
        pinning the wrapper's slug re-derivation against the canonical
        session-directory rule and the charter arm together."""
        plan_rel = "docs/history/plans/2026-10-18-closeout-charter/PLAN.md"
        self.init_fixture_repo()
        charter_dir = self.fixture / "docs" / "history" / "plans" / "2026-10-18-closeout-charter"
        charter_dir.mkdir(parents=True)
        (charter_dir / "PLAN.md").write_text("# plan\n", encoding="utf-8")
        self.git("add", "docs/history/plans/2026-10-18-closeout-charter/PLAN.md")
        self.git("commit", "-qm", "plans: fixture dated charter plan")
        worktree, exports, env = self.worktree_session(
            "--owned-path", "seed.txt", "--owned-plan", plan_rel,
        )
        run_id = exports["DONE_RUN_ID"]
        self.capture_phase0_baseline(worktree, "closeout-charter")
        record = self.write_run_review_record(
            worktree, "2026-10-18-closeout-charter-code-review-r1.md"
        )
        proc = self.run_worktree_commit(
            worktree, env, "--stage", "seed.txt", "--subject", "land the charter run work",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        combined = proc.stdout + proc.stderr
        transferred = self.fixture / ".ai-playbook" / "reviews" / record.name
        self.assertTrue(transferred.is_file(), combined)
        manifests = list(self.wt_session(worktree).glob("worktree-migrate-manifest-*.json"))
        self.assertEqual(
            manifests, [],
            "one-owned-plan migration wrote the run-id manifest worktree-side",
        )
        primary_manifest = (
            self.fixture / "docs" / "tmp" / "execute-plan"
            / "closeout-charter" / "closeout-migration.json"
        )
        self.assertTrue(primary_manifest.is_file(), combined)
        data = json.loads(primary_manifest.read_text(encoding="utf-8"))
        migrated = {entry["source"] for entry in data["migrated"]}
        self.assertIn(f".ai-playbook/reviews/{record.name}", migrated)
        for entry in data["migrated"]:
            self.assertTrue(entry["verified"])
        self.assertIn("docs-branch: sync complete", combined)
        self.assertFalse(
            (self.wt_session(worktree) / f"worktree-migrate-baseline-{run_id}.json").exists(),
            "commit captured a late baseline",
        )

    def test_baseline_wins_over_valid_skip_sibling(self) -> None:
        """[class: REPOSITORY_TEST] When both evidences exist (the canonical
        Phase 0 baseline and a valid plan-session skip sibling), the baseline
        wins: the migration runs on the baseline, a post-baseline artifact
        transfers, and no skip-bypass line is printed - precedence pinned,
        never silent."""
        self.init_fixture_repo()
        self.seed_tracked_plan(self.PLAN_REL)
        worktree, exports, env = self.worktree_session(
            "--owned-path", "seed.txt", "--owned-plan", self.PLAN_REL,
        )
        run_id = exports["DONE_RUN_ID"]
        self.capture_phase0_baseline(worktree, self.PLAN_SLUG)
        slug_dir = worktree / "docs" / "tmp" / "execute-plan" / self.PLAN_SLUG
        (slug_dir / "closeout-baseline-skip.json").write_text(
            json.dumps(
                {
                    "skip": True,
                    "reason": "stale sibling from a repaired capture",
                    "fallback": "scoped-copy enumeration at closeout",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        record = self.write_run_review_record(
            worktree, "2026-10-18-closeout-arm-example-code-review-r1.md"
        )
        proc = self.run_worktree_commit(
            worktree, env, "--stage", "seed.txt", "--subject", "land the run work",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        combined = proc.stdout + proc.stderr
        self.assertNotIn("valid closeout skip record governs", combined)
        transferred = self.fixture / ".ai-playbook" / "reviews" / record.name
        self.assertTrue(transferred.is_file(), combined)
        primary_manifest = (
            self.fixture / "docs" / "tmp" / "execute-plan"
            / self.PLAN_SLUG / "closeout-migration.json"
        )
        self.assertTrue(primary_manifest.is_file(), combined)
        data = json.loads(primary_manifest.read_text(encoding="utf-8"))
        migrated = {entry["source"] for entry in data["migrated"]}
        self.assertIn(f".ai-playbook/reviews/{record.name}", migrated)
        self.assertIn("docs-branch: sync complete", combined)

    def test_absolute_tmp_dir_manifest_lands_at_absolute_tmp(self) -> None:
        """[class: REPOSITORY_TEST] An absolute facts tmp_dir pins the
        one-owned-plan migration manifest (and the baseline reuse) to the
        absolute tmp root as-is: the manifest lands at
        <abs-tmp>/execute-plan/<slug>/closeout-migration.json and never
        under the primary checkout prefix."""
        self.init_fixture_repo()
        self.seed_tracked_plan(self.PLAN_REL)
        # the absolute tmp rides the worktree's resolved spelling so the
        # capture's relative_to sees one path identity (macOS /var symlink)
        abs_tmp = (self.tmp / "ad-hoc-wt").resolve() / "abs-tmp"
        (self.fixture / ".ai-playbook" / "facts.md").write_text(
            "```toml\n"
            'plans_dir = "docs/history/plans/"\n'
            'backlog_dir = "docs/history/backlog/"\n'
            f'tmp_dir = "{abs_tmp}"\n'
            'reviews_dir = ".ai-playbook/reviews/"\n'
            'metrics_dir = ".ai-playbook/metrics/"\n'
            'review_certs_dir = ".ai-playbook/review-certs/"\n'
            "```\n",
            encoding="utf-8",
        )
        self.git("add", ".ai-playbook/facts.md")
        self.git("commit", "-qm", "fixture: absolute tmp_dir facts")
        worktree, exports, env = self.worktree_session(
            "--owned-path", "seed.txt", "--owned-plan", self.PLAN_REL,
        )
        slug_dir = abs_tmp / "execute-plan" / self.PLAN_SLUG
        slug_dir.mkdir(parents=True, exist_ok=True)
        capture = subprocess.run(
            [sys.executable, str(CLOSEOUT_MIGRATE), "capture", "--out",
             str(slug_dir / "closeout-baseline.json")],
            cwd=str(worktree), capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(capture.returncode, 0, capture.stderr)
        record = self.write_run_review_record(
            worktree, "2026-10-18-closeout-arm-example-code-review-r1.md"
        )
        proc = self.run_worktree_commit(
            worktree, env, "--stage", "seed.txt", "--subject", "land the run work",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        combined = proc.stdout + proc.stderr
        manifest = abs_tmp / "execute-plan" / self.PLAN_SLUG / "closeout-migration.json"
        self.assertTrue(manifest.is_file(), combined)
        self.assertFalse(
            (self.fixture / "docs" / "tmp" / "execute-plan"
             / self.PLAN_SLUG / "closeout-migration.json").exists(),
            "absolute tmp_dir manifest leaked under the primary prefix",
        )

    def test_single_plan_missing_baseline_and_no_skip_refuses(self) -> None:
        """[class: REPOSITORY_TEST] A single-plan run with neither a Phase 0
        baseline nor a valid skip sibling keeps the existing migration
        refusal: the helper's implicit-empty-baseline refusal is named and
        nothing transfers."""
        self.init_fixture_repo()
        self.seed_tracked_plan(self.PLAN_REL)
        worktree, exports, env = self.worktree_session(
            "--owned-path", "seed.txt", "--owned-plan", self.PLAN_REL,
        )
        self.write_run_review_record(
            worktree, "2026-10-18-closeout-arm-example-code-review-r1.md"
        )
        proc = self.run_worktree_commit(
            worktree, env, "--stage", "seed.txt", "--subject", "land the run work",
        )
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        combined = proc.stdout + proc.stderr
        self.assertIn("baseline file not found", combined)
        self.assertIn("the worktree migration refused", combined)
        self.assertFalse(
            (self.fixture / ".ai-playbook" / "reviews").is_dir()
            and any((self.fixture / ".ai-playbook" / "reviews").iterdir()),
            "an unverified transfer landed at the primary checkout",
        )

    def test_single_plan_capture_failure_skip_sibling_bypasses_migrate(self) -> None:
        """[class: REPOSITORY_TEST] A single-plan run whose Phase 0 capture
        failed carries the sanctioned skip sibling; after the fixture's
        manual scoped copy and its recorded artifact list exist, the wrapper
        bypasses baseline-based migrate, reaches the docs sync, and never
        takes a late baseline. The fixture plan is undated (stem equals the
        canonical session slug), so the session directory stays active under
        the landing sweep's pending-plan check."""
        plan_rel = "docs/history/plans/closeout-arm-example.md"
        self.init_fixture_repo()
        self.seed_tracked_plan(plan_rel)
        worktree, exports, env = self.worktree_session(
            "--owned-path", "seed.txt", "--owned-plan", plan_rel,
        )
        run_id = exports["DONE_RUN_ID"]
        slug_dir = worktree / "docs" / "tmp" / "execute-plan" / self.PLAN_SLUG
        slug_dir.mkdir(parents=True, exist_ok=True)
        (slug_dir / "closeout-baseline-skip.json").write_text(
            json.dumps(
                {
                    "skip": True,
                    "reason": "capture failed",
                    "fallback": "scoped-copy enumeration at closeout",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        record = self.write_run_review_record(
            worktree, "2026-10-18-closeout-arm-example-code-review-r1.md"
        )
        copy = self.manual_scoped_copy(
            worktree, self.fixture, run_id, [plan_rel],
            [".ai-playbook/reviews/2026-10-18-closeout-arm-example-code-review-r1.md"],
            [self.PLAN_SLUG],
        )
        self.assertTrue(copy["complete"], copy)
        proc = self.run_worktree_commit(
            worktree, env, "--stage", "seed.txt", "--subject", "land the run work",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        combined = proc.stdout + proc.stderr
        self.assertIn("valid closeout skip record governs", combined)
        self.assertIn("docs-branch: sync complete", combined)
        self.assert_no_late_baseline_and_no_migration(worktree, run_id)
        # the manual scoped copy, not a migration, carried the artifact
        transferred = self.fixture / ".ai-playbook" / "reviews" / record.name
        self.assertTrue(transferred.is_file())

    # ---- skip-record arm (zero or multiple owned plans) ------------------ #

    def test_zero_plan_valid_skip_record_bypasses_migrate_and_reaches_docs_sync(self) -> None:
        """[class: REPOSITORY_TEST] A zero-plan run with a valid run-ID-keyed
        skip record: the wrapper bypasses baseline migration after the
        fixture's manual copy record exists, reaches the docs sync, and never
        takes a late baseline."""
        self.init_fixture_repo()
        worktree, exports, env = self.worktree_session("--owned-path", "seed.txt")
        run_id = exports["DONE_RUN_ID"]
        record = self.write_run_review_record(
            worktree, "2026-10-18-closeout-arm-example-code-review-r1.md"
        )
        copy = self.manual_scoped_copy(
            worktree, self.fixture, run_id, [],
            [".ai-playbook/reviews/2026-10-18-closeout-arm-example-code-review-r1.md"],
            [],
        )
        self.assertTrue(copy["complete"], copy)
        self.write_run_id_skip_record(worktree, run_id)
        proc = self.run_worktree_commit(
            worktree, env, "--stage", "seed.txt", "--subject", "land the run work",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        combined = proc.stdout + proc.stderr
        self.assertIn("valid closeout skip record governs", combined)
        self.assertIn("docs-branch: sync complete", combined)
        self.assert_no_late_baseline_and_no_migration(worktree, run_id)
        self.assertTrue(
            (self.fixture / ".ai-playbook" / "reviews" / record.name).is_file()
        )

    def test_multi_plan_valid_skip_record_bypasses_migrate(self) -> None:
        """[class: REPOSITORY_TEST] A multiple-plan run with a valid
        run-ID-keyed skip record bypasses baseline migration (no plan
        baseline is chosen arbitrarily, no migrate manifest is written) and
        reaches the docs sync."""
        self.init_fixture_repo()
        self.seed_tracked_plan(self.PLAN_REL)
        self.seed_tracked_plan(self.PLAN2_REL)
        worktree, exports, env = self.worktree_session(
            "--owned-path", "seed.txt",
            "--owned-plan", self.PLAN_REL, "--owned-plan", self.PLAN2_REL,
        )
        run_id = exports["DONE_RUN_ID"]
        self.write_run_review_record(
            worktree, "2026-10-18-closeout-arm-example-code-review-r1.md"
        )
        copy = self.manual_scoped_copy(
            worktree, self.fixture, run_id, [],
            [".ai-playbook/reviews/2026-10-18-closeout-arm-example-code-review-r1.md"],
            [],
        )
        self.assertTrue(copy["complete"], copy)
        self.write_run_id_skip_record(worktree, run_id)
        proc = self.run_worktree_commit(
            worktree, env, "--stage", "seed.txt", "--subject", "land the run work",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        combined = proc.stdout + proc.stderr
        self.assertIn("valid closeout skip record governs", combined)
        self.assertIn("docs-branch: sync complete", combined)
        self.assert_no_late_baseline_and_no_migration(worktree, run_id)

    def test_zero_plan_missing_skip_evidence_refuses(self) -> None:
        """[class: REPOSITORY_TEST] A zero-plan run whose setup-written skip
        record is deleted before commit keeps the existing migration refusal:
        setup is the record's producer, and its absence at commit time is the
        genuine refusal witness; nothing transfers and no late baseline is
        captured."""
        self.init_fixture_repo()
        worktree, exports, env = self.worktree_session("--owned-path", "seed.txt")
        run_id = exports["DONE_RUN_ID"]
        # the producer, not hand-provisioning, owns the record's presence;
        # deleting it restores the refusal witness this test pins
        skip = (
            self.wt_session(worktree)
            / f"worktree-migrate-baseline-{run_id}-skip.json"
        )
        self.assertTrue(skip.is_file(), "setup wrote no zero-plan skip record")
        skip.unlink()
        self.write_run_review_record(
            worktree, "2026-10-18-closeout-arm-example-code-review-r1.md"
        )
        proc = self.run_worktree_commit(
            worktree, env, "--stage", "seed.txt", "--subject", "land the run work",
        )
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        combined = proc.stdout + proc.stderr
        self.assertIn("the worktree migration refused", combined)
        self.assertFalse(
            (self.fixture / ".ai-playbook" / "reviews" / "2026-10-18-closeout-arm-example-code-review-r1.md").exists(),
            "an unverified transfer landed at the primary checkout",
        )
        self.assertFalse(
            (self.wt_session(worktree) / f"worktree-migrate-baseline-{run_id}.json").exists(),
            "commit captured a late baseline",
        )

    def test_setup_writes_zero_plan_skip_record_and_commit_bypasses(self) -> None:
        """[class: REPOSITORY_TEST] Setup is the zero-plan skip record's
        producer: a zero-plan run's setup writes a valid run-ID-keyed skip
        record at its own session resolution (the directory the commit leg
        reads), and the commit bypasses baseline migration on that record
        with no hand-provisioning, reaching the docs sync after the manual
        scoped copy."""
        self.init_fixture_repo()
        worktree, exports, env = self.worktree_session("--owned-path", "seed.txt")
        run_id = exports["DONE_RUN_ID"]
        skip = (
            self.wt_session(worktree)
            / f"worktree-migrate-baseline-{run_id}-skip.json"
        )
        self.assertTrue(skip.is_file(), "setup wrote no zero-plan skip record")
        payload = json.loads(skip.read_text(encoding="utf-8"))
        self.assertIs(payload.get("skip"), True)
        self.assertEqual(payload.get("fallback"), "manual scoped copy")
        record = self.write_run_review_record(
            worktree, "2026-10-18-closeout-arm-example-code-review-r1.md"
        )
        copy = self.manual_scoped_copy(
            worktree, self.fixture, run_id, [],
            [".ai-playbook/reviews/2026-10-18-closeout-arm-example-code-review-r1.md"],
            [],
        )
        self.assertTrue(copy["complete"], copy)
        proc = self.run_worktree_commit(
            worktree, env, "--stage", "seed.txt", "--subject", "land the run work",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        combined = proc.stdout + proc.stderr
        self.assertIn("valid closeout skip record governs", combined)
        self.assertIn("docs-branch: sync complete", combined)
        self.assert_no_late_baseline_and_no_migration(worktree, run_id)
        self.assertTrue(
            (self.fixture / ".ai-playbook" / "reviews" / record.name).is_file()
        )

    def test_multi_plan_missing_skip_evidence_refuses_despite_plan_baselines(self) -> None:
        """[class: REPOSITORY_TEST] A multiple-plan run refuses even when both
        plans carry canonical baselines and the setup-written skip record was
        deleted: no plan baseline is ever chosen arbitrarily, the run-ID skip
        record is the only skip evidence, and its absence at commit time is
        the genuine refusal witness."""
        self.init_fixture_repo()
        self.seed_tracked_plan(self.PLAN_REL)
        self.seed_tracked_plan(self.PLAN2_REL)
        worktree, exports, env = self.worktree_session(
            "--owned-path", "seed.txt",
            "--owned-plan", self.PLAN_REL, "--owned-plan", self.PLAN2_REL,
        )
        run_id = exports["DONE_RUN_ID"]
        skip = (
            self.wt_session(worktree)
            / f"worktree-migrate-baseline-{run_id}-skip.json"
        )
        self.assertTrue(skip.is_file(), "setup wrote no multi-plan skip record")
        skip.unlink()
        self.capture_phase0_baseline(worktree, self.PLAN_SLUG)
        self.capture_phase0_baseline(worktree, self.PLAN2_SLUG)
        record = self.write_run_review_record(
            worktree, "2026-10-18-closeout-arm-example-code-review-r1.md"
        )
        proc = self.run_worktree_commit(
            worktree, env, "--stage", "seed.txt", "--subject", "land the run work",
        )
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        combined = proc.stdout + proc.stderr
        self.assertIn("the worktree migration refused", combined)
        self.assertFalse(
            (self.fixture / ".ai-playbook" / "reviews" / record.name).exists(),
            "a plan baseline was chosen arbitrarily and used for migration",
        )
        self.assertFalse(
            (self.wt_session(worktree) / f"worktree-migrate-baseline-{run_id}.json").exists(),
            "commit captured a late baseline",
        )

    def test_invalid_skip_record_is_not_valid_skip_evidence(self) -> None:
        """[class: REPOSITORY_TEST] A skip record that is not a JSON object
        with skip true is not valid skip evidence: the existing refusal
        stands for both a wrong-payload and a malformed record."""
        for payload in ('{"skip": false, "reason": "not a skip"}', "not json at all"):
            with self.subTest(payload=payload):
                shutil.rmtree(self.fixture, ignore_errors=True)
                shutil.rmtree(self.tmp / "ad-hoc-wt", ignore_errors=True)
                self.init_fixture_repo()
                worktree, exports, env = self.worktree_session(
                    "--owned-path", "seed.txt",
                )
                run_id = exports["DONE_RUN_ID"]
                skip = self.write_run_id_skip_record(worktree, run_id)
                skip.write_text(payload, encoding="utf-8")
                proc = self.run_worktree_commit(
                    worktree, env, "--stage", "seed.txt",
                    "--subject", "land the run work",
                )
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                self.assertIn(
                    "the worktree migration refused", proc.stdout + proc.stderr
                )

    # ---- manual scoped-copy inventory clauses ----------------------------- #

    def test_manual_scoped_copy_transfers_every_named_source_class(self) -> None:
        """[class: REPOSITORY_TEST] The manual scoped-copy inventory
        enumerates every run-scoped source class (the execute-plan session
        directory, the authoring telemetry file, the metrics archive and its
        telemetry-absence record, the review-certification seal, the owned
        review Markdown and its sidecar, an identity-matched complete review
        pair, and exact-RUN_ID done-session files), copies each to the
        primary checkout, and records every source and destination with
        matching independently re-read digests."""
        self.init_fixture_repo()
        self.seed_tracked_plan(self.PLAN_REL)
        worktree, exports, env = self.worktree_session(
            "--owned-path", "seed.txt", "--owned-plan", self.PLAN_REL,
        )
        run_id = exports["DONE_RUN_ID"]
        slug_dir = worktree / "docs" / "tmp" / "execute-plan" / self.PLAN_SLUG
        slug_dir.mkdir(parents=True, exist_ok=True)
        (slug_dir / "task-1.log.md").write_text("# task log\n", encoding="utf-8")
        authoring = worktree / "docs" / "tmp" / "authoring" / self.PLAN_SLUG
        authoring.mkdir(parents=True, exist_ok=True)
        (authoring / "context.jsonl").write_text('{"event": "open"}\n', encoding="utf-8")
        metrics = worktree / "docs" / "tmp" / "metrics"
        metrics.mkdir(parents=True, exist_ok=True)
        (metrics / f"{self.PLAN_SLUG}-telemetry.json").write_text("{}\n", encoding="utf-8")
        (metrics / f"{self.PLAN_SLUG}-telemetry-absent.txt").write_text(
            "no telemetry this run\n", encoding="utf-8"
        )
        certs = worktree / ".ai-playbook" / "review-certs"
        certs.mkdir(parents=True, exist_ok=True)
        (certs / f"{self.PLAN_SLUG}-seal.md").write_text("seal\n", encoding="utf-8")
        reviews = worktree / ".ai-playbook" / "reviews"
        reviews.mkdir(parents=True, exist_ok=True)
        owned_review = reviews / "2026-10-18-closeout-arm-example-review.md"
        owned_review.write_text("owned review\n", encoding="utf-8")
        owned_stats = reviews / "2026-10-18-closeout-arm-example-review.stats.json"
        owned_stats.write_text(
            json.dumps({"extensions": {"plan_identity": self.PLAN_REL}}) + "\n",
            encoding="utf-8",
        )
        pair_record = reviews / "2026-10-18-closeout-arm-example-pair-r1.md"
        pair_record.write_text("pair review\n", encoding="utf-8")
        (reviews / "2026-10-18-closeout-arm-example-pair-r1.stats.json").write_text(
            json.dumps({"extensions": {"plan_identity": self.PLAN_REL}}) + "\n",
            encoding="utf-8",
        )
        (self.wt_session(worktree) / f"owned-commits-{run_id}.txt").write_text(
            "", encoding="utf-8"
        )
        copy = self.manual_scoped_copy(
            worktree, self.fixture, run_id,
            [self.PLAN_REL],
            [".ai-playbook/reviews/2026-10-18-closeout-arm-example-review.md"],
            [self.PLAN_SLUG],
        )
        self.assertTrue(copy["complete"], copy)
        by_source = {entry["source"]: entry for entry in copy["entries"]}
        expected = {
            f"docs/tmp/execute-plan/{self.PLAN_SLUG}/task-1.log.md",
            f"docs/tmp/authoring/{self.PLAN_SLUG}/context.jsonl",
            f"docs/tmp/metrics/{self.PLAN_SLUG}-telemetry.json",
            f"docs/tmp/metrics/{self.PLAN_SLUG}-telemetry-absent.txt",
            f".ai-playbook/review-certs/{self.PLAN_SLUG}-seal.md",
            ".ai-playbook/reviews/2026-10-18-closeout-arm-example-review.md",
            ".ai-playbook/reviews/2026-10-18-closeout-arm-example-review.stats.json",
            ".ai-playbook/reviews/2026-10-18-closeout-arm-example-pair-r1.md",
            ".ai-playbook/reviews/2026-10-18-closeout-arm-example-pair-r1.stats.json",
            f"docs/tmp/done-session/run-manifest-{run_id}.json",
            f"docs/tmp/done-session/owned-commits-{run_id}.txt",
        }
        self.assertEqual(set(by_source), expected)
        classes = {entry["class"] for entry in copy["entries"]}
        self.assertEqual(
            classes,
            {
                "execute-plan-session", "authoring-telemetry", "metrics-archive",
                "telemetry-absence-record", "review-cert-seal", "owned-review",
                "owned-review-sidecar", "identity-matched-review-pair",
                "done-session",
            },
        )
        for rel, entry in by_source.items():
            source = worktree / rel
            destination = Path(entry["destination"])
            self.assertTrue(destination.is_file(), rel)
            self.assertEqual(
                hashlib.sha256(source.read_bytes()).hexdigest(),
                hashlib.sha256(destination.read_bytes()).hexdigest(),
                rel,
            )
        # the record lists every copied source and destination and the
        # digests match an independent re-read
        record_text = Path(copy["record"]).read_text(encoding="utf-8")
        for rel, entry in by_source.items():
            self.assertIn(entry["source"], record_text)
            self.assertIn(entry["destination"], record_text)
            self.assertIn(entry["source_digest"], record_text)
            self.assertIn(entry["destination_digest"], record_text)
    def test_manual_scoped_copy_excludes_control_inputs_and_unrelated(self) -> None:
        """[class: REPOSITORY_TEST] The manual scoped-copy inventory never
        copies control inputs or unrelated artifacts: the skip record, the
        plan-deliverables record with its stale prior-run entry, foreign
        reviews, and discovered-but-class-less artifacts stay excluded, and
        tracked plan files are never transfer candidates."""
        self.init_fixture_repo()
        self.seed_tracked_plan(self.PLAN_REL)
        worktree, exports, env = self.worktree_session(
            "--owned-path", "seed.txt", "--owned-plan", self.PLAN_REL,
        )
        run_id = exports["DONE_RUN_ID"]
        self.write_run_id_skip_record(worktree, run_id)
        stale_plan = "docs/history/plans/2026-10-01-prior-run-example.md"
        deliverables = (
            worktree / "docs" / "tmp" / "done-session" / "plan-deliverables.txt"
        )
        deliverables.parent.mkdir(parents=True, exist_ok=True)
        deliverables.write_text(
            f"{self.PLAN_REL}\n{stale_plan}\n", encoding="utf-8"
        )
        prior_run = (
            worktree / "docs" / "tmp" / "execute-plan" / "prior-run" / "x.log"
        )
        prior_run.parent.mkdir(parents=True, exist_ok=True)
        prior_run.write_text("prior run log\n", encoding="utf-8")
        reviews = worktree / ".ai-playbook" / "reviews"
        reviews.mkdir(parents=True, exist_ok=True)
        foreign = reviews / "2026-10-18-foreign-session-review.md"
        foreign.write_text("foreign review\n", encoding="utf-8")
        (reviews / "2026-10-18-foreign-session-review.stats.json").write_text(
            json.dumps(
                {"extensions": {"plan_identity": "docs/history/plans/not-owned.md"}}
            )
            + "\n",
            encoding="utf-8",
        )
        (reviews / "unrelated-scratch.md").write_text("unrelated\n", encoding="utf-8")
        copy = self.manual_scoped_copy(
            worktree, self.fixture, run_id, [self.PLAN_REL], [], [self.PLAN_SLUG],
        )
        sources = {entry["source"] for entry in copy["entries"]}
        self.assertNotIn(
            f"docs/tmp/done-session/worktree-migrate-baseline-{run_id}-skip.json",
            sources,
        )
        self.assertNotIn(".ai-playbook/reviews/2026-10-18-foreign-session-review.md", sources)
        self.assertNotIn(
            ".ai-playbook/reviews/2026-10-18-foreign-session-review.stats.json", sources
        )
        self.assertNotIn(".ai-playbook/reviews/unrelated-scratch.md", sources)
        self.assertNotIn(self.PLAN_REL, sources)
        # the stale deliverables entry, the deliverables record itself, and
        # the prior-run session artifact appear only in the excluded set
        self.assertIn(stale_plan, copy["excluded"])
        self.assertIn("docs/tmp/done-session/plan-deliverables.txt", copy["excluded"])
        self.assertIn("docs/tmp/execute-plan/prior-run/x.log", copy["excluded"])
        # discovered-but-unselected artifacts are recorded excluded, never copied
        self.assertIn(".ai-playbook/reviews/unrelated-scratch.md", copy["excluded"])
        # the tracked plan file, the foreign review, the stale deliverables
        # entry, and the deliverables record never reached the primary
        record_text = Path(copy["record"]).read_text(encoding="utf-8")
        self.assertNotIn(self.PLAN_REL, record_text)
        self.assertNotIn(foreign.name, record_text)
        self.assertNotIn(stale_plan, record_text)
        self.assertNotIn("plan-deliverables.txt", record_text)
        self.assertFalse(
            (self.fixture / ".ai-playbook" / "reviews" / foreign.name).exists()
        )

    def test_manual_scoped_copy_incomplete_transfer_keeps_source_worktree(self) -> None:
        """[class: REPOSITORY_TEST] A missing listed source or a destination
        digest mismatch leaves the transfer incomplete (the record names it)
        and keeps every source artifact in the worktree available for
        recovery; the incomplete transfer never presents as complete."""
        self.init_fixture_repo()
        self.seed_tracked_plan(self.PLAN_REL)
        worktree, exports, env = self.worktree_session(
            "--owned-path", "seed.txt", "--owned-plan", self.PLAN_REL,
        )
        run_id = exports["DONE_RUN_ID"]
        review_rel = ".ai-playbook/reviews/2026-10-18-closeout-arm-example-review.md"
        record = self.write_run_review_record(
            worktree, "2026-10-18-closeout-arm-example-review.md"
        )
        # missing listed source: the owned-review manifest entry is absent
        missing_copy = self.manual_scoped_copy(
            worktree, self.fixture, run_id, [self.PLAN_REL],
            [".ai-playbook/reviews/absent-from-worktree.md"], [self.PLAN_SLUG],
        )
        self.assertFalse(missing_copy["complete"])
        self.assertTrue(
            any(entry.get("missing") for entry in missing_copy["entries"])
        )
        self.assertIn("complete: false", Path(missing_copy["record"]).read_text(encoding="utf-8"))
        # digest mismatch: the copy is damaged before verification
        mismatch_copy = self.manual_scoped_copy(
            worktree, self.fixture, run_id, [self.PLAN_REL], [review_rel],
            [self.PLAN_SLUG], corrupt_destinations={review_rel},
        )
        self.assertFalse(mismatch_copy["complete"])
        broken = next(
            entry for entry in mismatch_copy["entries"] if entry["source"] == review_rel
        )
        self.assertFalse(broken["verified"])
        self.assertNotEqual(
            broken["source_digest"], broken["destination_digest"]
        )
        # every source artifact stays in the worktree for recovery
        self.assertTrue(record.is_file())
        self.assertEqual(record.read_text(encoding="utf-8"), "# review record\n")
        self.assertTrue(worktree.is_dir())


class DoneRunRollingLogRefBoundCommitTest(FixtureMixin, unittest.TestCase):
    """Task 1 witnesses (plan
    docs/history/plans/2026-10-25-primary-log-branch-drift-at-commit.md):
    the expected symbolic-ref/starting-OID pair binds a primary rolling-log
    write to the caller-selected branch through staging and the captured-
    tree compare-and-swap; one cleanup owner mutates nothing on every
    refusal before the captured-ref swap and reports owned staged residue
    through blocked recovery; ordinary pair-less calls and worktree log
    commits keep their existing paths."""

    PLAN_LOG = "docs/history/backlog/PLAN-PROMPTS.md"
    EXEC_LOG = "docs/history/backlog/EXEC-PROMPTS.md"
    ENTRY = "\n- appended prompt entry\n"
    EM_DASH = "\u2014"

    # The private-runner-copy doctoring mechanism (same shape as
    # DoneRunCapturedTreeLandingFenceTest): each doctored helper replaces a
    # symlinked repo script the runner copy resolves first.
    TEMP_RUNNER_HELPERS = (
        "revert_set_classifier.py", "staged_scope_guard.py",
        "done_sweep_gates.sh", "done_sweep_gates_lib.py",
        "dirt_regression_gate.py", "reverse_squash_guard.py",
        "docs_branch_sync.sh",
    )
    DOCTOR_RS_GUARD_STAGES_FOREIGN = (
        "import subprocess\n"
        "with open('stranger-window.txt', 'w') as handle:\n"
        "    handle.write('staged in the capture window\\n')\n"
        "subprocess.run(['git', 'add', 'stranger-window.txt'], check=True)\n"
        "print('OUTCOME: pass')\n"
    )

    # ---- fixture helpers -------------------------------------------------- #

    def log_fixture(self) -> tuple[dict, str, str]:
        """Both rolling prompt logs tracked at HEAD, a held done boundary,
        and the caller selection (symbolic ref + starting OID) read under
        that hold; returns (setup exports, expected_ref, expected_oid)."""
        self.init_fixture_repo()
        log_dir = self.fixture / "docs" / "history" / "backlog"
        log_dir.mkdir(parents=True)
        (log_dir / "PLAN-PROMPTS.md").write_text("# PLAN prompts\n")
        (log_dir / "EXEC-PROMPTS.md").write_text("# EXEC prompts\n")
        self.git("add", self.PLAN_LOG, self.EXEC_LOG)
        self.git("commit", "-qm", "seed the rolling prompt logs")
        setup_proc, exports = self.setup_session("--owned-path", self.PLAN_LOG)
        branch = self.git("branch", "--show-current").stdout.strip()
        head = self.git("rev-parse", "HEAD").stdout.strip()
        return exports, "refs/heads/" + branch, head

    def rolling_env(self, exports: dict) -> dict:
        env = self.commit_env()
        env.update(exports)
        return env

    def head(self) -> str:
        return self.git("rev-parse", "HEAD").stdout.strip()

    def staged_paths(self) -> list[str]:
        out = self.git("diff", "--cached", "--name-only", "HEAD").stdout
        return [line for line in out.splitlines() if line.strip()]

    def worktree_dirty(self, rel: str) -> bool:
        status = self.git("status", "--porcelain", "--", rel).stdout
        # since the cleanup owner no longer unstages the owned delta, a
        # refused declared path carries its edit in BOTH the index and the
        # worktree; the surviving byte is any M in either status column
        return any(
            "M" in line[:2] for line in status.splitlines() if line.strip()
        )

    def assert_no_rolling_cleanup(
        self, proc: subprocess.CompletedProcess,
    ) -> None:
        self.assertNotIn(
            "rolling-log cleanup", proc.stdout + proc.stderr,
        )

    def assert_cleanup_verified(
        self, proc: subprocess.CompletedProcess,
    ) -> None:
        self.assertIn(
            "no owned staged residue; index and worktree bytes left untouched",
            proc.stdout + proc.stderr,
        )

    def assert_cleanup_blocks_on_residue(
        self, proc: subprocess.CompletedProcess,
    ) -> None:
        self.assertIn("BLOCKED RECOVERY", proc.stdout + proc.stderr)
        self.assertIn(
            "index and worktree bytes left untouched",
            proc.stdout + proc.stderr,
        )

    def install_hook(self, name: str, body: str) -> Path:
        hooks = self.fixture / ".git" / "hooks"
        hooks.mkdir(exist_ok=True)
        hook = hooks / name
        hook.write_text("#!/bin/sh\n" + body)
        hook.chmod(0o755)
        return hook

    def temp_runner_dir(self, doctor: dict[str, str]) -> Path:
        runner_dir = self.tmp / "runner"
        runner_dir.mkdir()
        shutil.copy2(RUNNER, runner_dir / "done_run.sh")
        for name in self.TEMP_RUNNER_HELPERS:
            os.symlink(REPO_ROOT / "scripts" / name, runner_dir / name)
        for name, body in doctor.items():
            target = runner_dir / name
            if target.is_symlink() or target.exists():
                target.unlink()
            target.write_text(body)
        return runner_dir

    def run_temp_commit(
        self, runner_dir: Path, exports: dict, *args: str,
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(runner_dir / "done_run.sh"), "commit", *args],
            cwd=str(self.fixture),
            env=self.rolling_env(exports),
            capture_output=True,
            text=True,
            timeout=300,
        )

    def ref_move_guard_body(self, ref: str, target: str) -> str:
        """A doctored reverse-squash guard that advances the branch ref
        mid-run (the ref-only land-worktree shape) and passes."""
        return (
            "import subprocess\n"
            "subprocess.run(['git', 'update-ref', "
            f"'{ref}', '{target}'], check=True)\n"
            "print('OUTCOME: pass')\n"
        )

    # ---- the pair lifecycle ----------------------------------------------- #

    def test_pair_lands_on_captured_primary_head_as_sole_parent(self) -> None:
        exports, ref, oid = self.log_fixture()
        (self.fixture / self.PLAN_LOG).write_text("# PLAN prompts\n" + self.ENTRY)
        proc = self.run_commit(
            "--stage", self.PLAN_LOG,
            "--subject", "log: append the prompt entry",
            "--expected-ref", ref, "--expected-oid", oid,
            env=self.rolling_env(exports),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        landing = self.head()
        # the commit builds from the captured primary HEAD as sole parent
        parents = self.git("rev-list", "--parents", "-1", "HEAD").stdout.split()
        self.assertEqual(parents, [landing, oid])
        self.assertEqual(
            self.git("symbolic-ref", "-q", "HEAD").stdout.strip(), ref,
        )
        # only the declared owned log path rides the commit
        shown = self.git("show", "--name-only", "--format=", landing).stdout
        self.assertEqual(
            [line for line in shown.splitlines() if line.strip()],
            [self.PLAN_LOG],
        )
        self.assertIn(
            self.ENTRY.strip(),
            self.git("show", f"HEAD:{self.PLAN_LOG}").stdout,
        )
        ledger = self.done_session() / (
            f"owned-commits-{exports['DONE_RUN_ID']}.txt"
        )
        self.assertEqual(ledger.read_text().splitlines()[-1], landing)
        # the pair precondition ran pre-stage and at the landing; the
        # cleanup owner stayed disarmed on success; no merge lock was taken
        stages = self.trace_stages(self.rolling_env(exports))
        self.assertIn("rolling-log-pre-stage-guard", stages)
        self.assertIn("rolling-log-ref-precondition", stages)
        self.assert_no_rolling_cleanup(proc)
        self.assertIn(
            "rolling-log boundary: skipping the docs-branch sync",
            proc.stdout + proc.stderr,
        )

    def test_partial_pair_refuses_before_staging_with_nothing_changed(self) -> None:
        exports, ref, oid = self.log_fixture()
        (self.fixture / self.PLAN_LOG).write_text("# PLAN prompts\n" + self.ENTRY)
        count_before = self.commit_count()
        for partial in (["--expected-ref", ref], ["--expected-oid", oid]):
            proc = self.run_commit(
                "--stage", self.PLAN_LOG, "--subject", "log: append",
                *partial, env=self.rolling_env(exports),
            )
            self.assertEqual(proc.returncode, 3, proc.stderr)
            self.assertIn("give both or neither", proc.stderr)
            self.assertEqual(self.head(), oid)
            self.assertEqual(self.staged_paths(), [])
            self.assertTrue(self.worktree_dirty(self.PLAN_LOG))
            self.assert_no_rolling_cleanup(proc)
        self.assertEqual(self.commit_count(), count_before)

    def test_pair_mismatch_refuses_before_staging_then_reselection_retries(self) -> None:
        exports, ref, stale_oid = self.log_fixture()
        # the shared checkout moves to a new tip after the caller's
        # selection (the wrong-branch incident shape)
        (self.fixture / "seed.txt").write_text("seed\nmoved\n")
        self.git("add", "seed.txt")
        self.git("commit", "-qm", "move the checkout tip")
        new_oid = self.head()
        (self.fixture / self.PLAN_LOG).write_text("# PLAN prompts\n" + self.ENTRY)
        proc = self.run_commit(
            "--stage", self.PLAN_LOG,
            "--subject", "log: append on a stale selection",
            "--expected-ref", ref, "--expected-oid", stale_oid,
            env=self.rolling_env(exports),
        )
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn("rolling-log ref precondition", proc.stderr)
        self.assertIn("recover", proc.stderr)
        # no ref movement, nothing staged, no cleanup ran
        self.assertEqual(self.head(), new_oid)
        self.assertEqual(self.staged_paths(), [])
        self.assertTrue(self.worktree_dirty(self.PLAN_LOG))
        self.assert_no_rolling_cleanup(proc)
        # pre-read recovery: the caller reselects the new tip under the
        # same hold and retries through the pair
        retry = self.run_commit(
            "--stage", self.PLAN_LOG,
            "--subject", "log: append after reselection",
            "--expected-ref", ref, "--expected-oid", new_oid,
            env=self.rolling_env(exports),
        )
        self.assertEqual(retry.returncode, 0, retry.stderr)
        parents = self.git("rev-list", "--parents", "-1", "HEAD").stdout.split()
        self.assertEqual(parents[1], new_oid)

    def test_ordinary_no_pair_call_keeps_existing_path(self) -> None:
        exports, ref, oid = self.log_fixture()
        (self.fixture / self.PLAN_LOG).write_text("# PLAN prompts\n" + self.ENTRY)
        proc = self.run_commit(
            "--stage", self.PLAN_LOG, "--subject", "log: ordinary append",
            env=self.rolling_env(exports),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        combined = proc.stdout + proc.stderr
        self.assertNotIn("rolling-log", combined)
        parents = self.git("rev-list", "--parents", "-1", "HEAD").stdout.split()
        self.assertEqual(parents[1], oid)
        # the ordinary refusal class is untouched: an unknown argument is a
        # usage refusal carrying no rolling-log mode text
        refused = self.run_commit(
            "--no-such-flag", env=self.rolling_env(exports),
        )
        self.assertEqual(refused.returncode, 3)
        self.assertIn("unknown argument", refused.stderr)
        self.assert_no_rolling_cleanup(refused)

    def test_worktree_log_commit_keeps_selected_branch_placement(self) -> None:
        exports, ref, oid = self.log_fixture()
        primary_head = self.head()
        wt = self.tmp / "log-wt"
        self.git("worktree", "add", "-b", "wt-log", str(wt))
        # the worktree log writer holds its own worktree-scoped boundary
        # (a zero-plan claim: the migration skip record covers the leg) and
        # commits its edit on its own selected branch, with no pair
        # the worktree writer's lib context roots at the worktree (its own
        # worktree-scoped done-session holds its marker); the fixture's
        # default pin targets the primary repo and would misbind the marker
        wt_env_extra = {"DONE_SWEEP_REPO_ROOT": str(wt)}
        wt_setup = self.run_setup("--claim-none", cwd=wt, env_extra=wt_env_extra)
        self.assertEqual(wt_setup.returncode, 0, wt_setup.stderr)
        wt_exports = self.eval_exports(wt_setup.stdout)
        (wt / self.PLAN_LOG).write_text("# PLAN prompts\n" + self.ENTRY)
        wt_commit_env = self.rolling_env(wt_exports)
        wt_commit_env.update(wt_env_extra)
        proc = self.run_commit(
            "--stage", self.PLAN_LOG, "--subject", "log: worktree append",
            "--boundary-class", "per-task",
            env=wt_commit_env, cwd=wt,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        # the primary ref and its checkout are untouched
        self.assertEqual(self.head(), primary_head)
        wt_tip = self.git("rev-parse", "refs/heads/wt-log").stdout.strip()
        parents = self.git("rev-list", "--parents", "-1", wt_tip).stdout.split()
        self.assertEqual(parents, [wt_tip, oid])
        self.assertIn(
            self.ENTRY.strip(),
            self.git("show", f"{wt_tip}:{self.PLAN_LOG}").stdout,
        )
        self.assertNotIn("rolling-log", proc.stdout + proc.stderr)

    # ---- foreign staged paths: early guard and capture-window fence ------- #

    def test_foreign_staged_path_refuses_before_git_add(self) -> None:
        exports, ref, oid = self.log_fixture()
        (self.fixture / "stranger.txt").write_text("foreign staged bytes\n")
        self.git("add", "stranger.txt")
        (self.fixture / self.PLAN_LOG).write_text("# PLAN prompts\n" + self.ENTRY)
        proc = self.run_commit(
            "--stage", self.PLAN_LOG,
            "--subject", "log: append beside a foreign staging",
            "--expected-ref", ref, "--expected-oid", oid,
            env=self.rolling_env(exports),
        )
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn(
            "a staged path outside the declared owned log set", proc.stderr,
        )
        self.assertIn("stranger.txt", proc.stderr)
        # refused before git add: only the foreign bytes are staged, the
        # writer's log edit never entered the index, no commit, no ref move
        self.assertEqual(self.staged_paths(), ["stranger.txt"])
        self.assertEqual(self.head(), oid)
        self.assertTrue(self.worktree_dirty(self.PLAN_LOG))
        self.assert_no_rolling_cleanup(proc)

    def test_foreign_path_in_capture_window_refuses_and_cleans_owned_delta(self) -> None:
        exports, ref, oid = self.log_fixture()
        (self.fixture / self.PLAN_LOG).write_text("# PLAN prompts\n" + self.ENTRY)
        # the foreign path enters the index after the early guard (the
        # runner's own pre-landing helper window) and before the tree
        # capture: the capture-window fence refuses, the cleanup owner
        # unstages only the writer-owned delta, the foreign bytes stay
        # staged, and no commit or ref movement happens
        runner_dir = self.temp_runner_dir({
            "reverse_squash_guard.py": self.DOCTOR_RS_GUARD_STAGES_FOREIGN,
        })
        proc = self.run_temp_commit(
            runner_dir, exports,
            "--stage", self.PLAN_LOG,
            "--subject", "log: append under a capture-window staging race",
            "--expected-ref", ref, "--expected-oid", oid,
        )
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn(
            "a foreign path entered the staged index before the tree "
            "capture: stranger-window.txt",
            proc.stdout + proc.stderr,
        )
        # the cleanup owner mutates nothing: the writer-owned delta stays
        # staged beside the foreign bytes and is reported for recovery
        self.assertEqual(
            self.staged_paths(),
            [self.PLAN_LOG, "stranger-window.txt"],
        )
        self.assertEqual(self.head(), oid)
        self.assertTrue(self.worktree_dirty(self.PLAN_LOG))
        self.assert_cleanup_blocks_on_residue(proc)

    # ---- done-lock consumers against an active primary log write ---------- #

    def test_done_consumer_refuses_before_mutation_while_log_write_holds(self) -> None:
        exports, ref, oid = self.log_fixture()
        (self.fixture / self.PLAN_LOG).write_text("# PLAN prompts\n" + self.ENTRY)
        # a named done-lock consumer (the closeout boundary setup) refuses
        # before writing any boundary state while the writer's hold stands
        # (the raised dead-holder grace keeps the writer's exported
        # generation unstealable for the probe)
        session = self.done_session()
        before = sorted(p.name for p in session.iterdir())
        contender = self.run_setup(
            "--label", "contender",
            env_extra={
                "DONE_LOCK_AGENT_MAX_WAIT_SECS": "2",
                "DONE_LOCK_DEAD_HOLDER_GRACE_SECS": "3600",
            },
        )
        self.assertNotEqual(contender.returncode, 0)
        self.assertIn("another done holds the lock", contender.stderr)
        self.assertEqual(sorted(p.name for p in session.iterdir()), before)
        # the log writer completes under its hold; refs and bytes unchanged
        # for anything the writer does not own
        proc = self.run_commit(
            "--stage", self.PLAN_LOG,
            "--subject", "log: append under the writer hold",
            "--expected-ref", ref, "--expected-oid", oid,
            env=self.rolling_env(exports),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        parents = self.git("rev-list", "--parents", "-1", "HEAD").stdout.split()
        self.assertEqual(parents, [self.head(), oid])

    def test_log_writer_waits_without_staging_while_consumer_holds(self) -> None:
        exports, ref, oid = self.log_fixture()
        (self.fixture / self.PLAN_LOG).write_text("# PLAN prompts\n" + self.ENTRY)
        # the writer's lock acquisition waits and fails fast while the
        # closeout boundary holds the done lock (the raised dead-holder
        # grace keeps the boundary's exported generation unstealable):
        # nothing is staged
        writer_env = self.runner_env()
        writer_env["DONE_LOCK_DEAD_HOLDER_GRACE_SECS"] = "3600"
        writer_acq = subprocess.run(
            ["bash", str(LOCK_SCRIPT), "wait-acquire", "--label", "log-writer",
             "--max-wait", "1"],
            cwd=str(self.fixture), env=writer_env,
            capture_output=True, text=True, timeout=60,
        )
        self.assertNotEqual(writer_acq.returncode, 0)
        self.assertEqual(self.staged_paths(), [])
        self.assertEqual(self.head(), oid)
        self.assertTrue(self.worktree_dirty(self.PLAN_LOG))
        # after checkout stability (the hold releases), the writer lands on
        # the same selected tip
        env = self.runner_env()
        env["DONE_LOCK_DIR"] = exports["DONE_LOCK_DIR"]
        env["DONE_LOCK_TOKEN"] = exports["DONE_LOCK_TOKEN"]
        release = subprocess.run(
            ["bash", str(LOCK_SCRIPT), "release-repo"],
            cwd=str(self.fixture), env=env,
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(release.returncode, 0, release.stderr)
        proc = self.run_commit(
            "--stage", self.PLAN_LOG,
            "--subject", "log: append after the hold clears",
            "--expected-ref", ref, "--expected-oid", oid,
            env=self.rolling_env(exports),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        parents = self.git("rev-list", "--parents", "-1", "HEAD").stdout.split()
        self.assertEqual(parents, [self.head(), oid])

    # ---- worktree merge-lock overlap --------------------------------------- #

    def test_primary_log_write_completes_while_worktree_merge_lock_held(self) -> None:
        exports, ref, oid = self.log_fixture()
        wt = self.tmp / "peer-wt"
        self.git("worktree", "add", "-b", "wt-peer", str(wt))
        # the worktree writer pauses after taking the merge lock, before
        # any ref update
        merge_acq = subprocess.run(
            ["bash", str(LOCK_SCRIPT), "merge-acquire",
             "--label", "wt-log-writer"],
            cwd=str(wt), env=self.runner_env(),
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(merge_acq.returncode, 0, merge_acq.stderr)
        merge_exports = self.eval_exports(merge_acq.stdout)
        # the primary log write completes while the merge lock stays held
        (self.fixture / self.PLAN_LOG).write_text("# PLAN prompts\n" + self.ENTRY)
        proc = self.run_commit(
            "--stage", self.PLAN_LOG,
            "--subject", "log: append while the merge lock is held",
            "--expected-ref", ref, "--expected-oid", oid,
            env=self.rolling_env(exports),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        primary_landing = self.head()
        parents = self.git("rev-list", "--parents", "-1", primary_landing).stdout
        self.assertEqual(len(parents.split()), 2)
        self.assertIn(
            "skipping the docs-branch sync", proc.stdout + proc.stderr,
        )
        # the paused worktree writer completes, advancing only its own
        # selected branch and leaving the primary checkout's bytes alone
        (wt / self.EXEC_LOG).write_text("# EXEC prompts\n" + self.ENTRY)
        subprocess.run(
            ["git", "-C", str(wt), "add", self.EXEC_LOG],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(wt), "commit", "-qm", "log: peer append"],
            check=True, capture_output=True,
        )
        wt_tip = self.git("rev-parse", "refs/heads/wt-peer").stdout.strip()
        self.assertEqual(self.head(), primary_landing)
        self.assertEqual(
            self.git("show", f"{primary_landing}:{self.EXEC_LOG}").stdout,
            "# EXEC prompts\n",
        )
        self.assertEqual(
            self.git("show", f"{wt_tip}:{self.EXEC_LOG}").stdout,
            "# EXEC prompts\n" + self.ENTRY,
        )
        env = self.runner_env()
        env.update(merge_exports)
        release = subprocess.run(
            ["bash", str(LOCK_SCRIPT), "merge-release-repo"],
            cwd=str(wt), env=env,
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(release.returncode, 0, release.stderr)

    # ---- ref move between selection and CAS (the land-worktree shape) ----- #

    def test_ref_move_between_selection_and_cas_refuses_and_reselects(self) -> None:
        exports, ref, oid = self.log_fixture()
        # the ref-only landing's own commit exists off to the side; the
        # branch sits back at the caller's selection tip
        # a content-free landing tip: any tree delta would read as a staged
        # phantom once the caller's selection rewinds the ref below it
        moved_tip = self.git(
            "commit-tree", f"{oid}^{{tree}}", "-p", oid,
            "-m", "ref-only landing tip",
        ).stdout.strip()
        self.git("update-ref", ref, moved_tip)
        self.git("update-ref", ref, oid)
        (self.fixture / self.PLAN_LOG).write_text("# PLAN prompts\n" + self.ENTRY)
        # the ref move lands mid-run (the runner's pre-landing helper
        # window), between the log writer's selection and its CAS
        runner_dir = self.temp_runner_dir({
            "reverse_squash_guard.py": self.ref_move_guard_body(ref, moved_tip),
        })
        proc = self.run_temp_commit(
            runner_dir, exports,
            "--stage", self.PLAN_LOG,
            "--subject", "log: append under a ref-only landing",
            "--expected-ref", ref, "--expected-oid", oid,
        )
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn(
            "does not match the expected starting OID", proc.stdout + proc.stderr,
        )
        # the landing the ref-only mode advanced stays standing; the writer
        # moved nothing itself
        self.assertEqual(self.head(), moved_tip)
        # the cleanup owner mutates nothing: the owned delta stays staged
        # and is reported through blocked recovery
        self.assertEqual(self.staged_paths(), [self.PLAN_LOG])
        self.assertTrue(self.worktree_dirty(self.PLAN_LOG))
        self.assert_cleanup_blocks_on_residue(proc)
        # the operator resolves the residue (the sanctioned remedy), then
        # the writer reselects the new tip and retries through the pair
        self.git("reset", "-q", "--", self.PLAN_LOG)
        retry = self.run_commit(
            "--stage", self.PLAN_LOG,
            "--subject", "log: append after reselecting the moved tip",
            "--expected-ref", ref, "--expected-oid", moved_tip,
            env=self.rolling_env(exports),
        )
        self.assertEqual(retry.returncode, 0, retry.stderr)
        parents = self.git("rev-list", "--parents", "-1", "HEAD").stdout.split()
        self.assertEqual(parents, [self.head(), moved_tip])

    # ---- representative pre-CAS refusals clean only the owned delta ------- #

    def test_pre_landing_gate_refusal_cleans_only_owned_delta(self) -> None:
        exports, ref, oid = self.log_fixture()
        (self.fixture / self.EXEC_LOG).write_text("# EXEC prompts\n- peer note\n")
        (self.fixture / self.PLAN_LOG).write_text(
            f"# PLAN prompts\n- entry with an em dash {self.EM_DASH} here\n"
        )
        proc = self.run_commit(
            "--stage", self.PLAN_LOG,
            "--subject", "log: append an em dash entry",
            "--expected-ref", ref, "--expected-oid", oid,
            env=self.rolling_env(exports),
        )
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn(
            "the landing sweep refused the staged set", proc.stderr,
        )
        self.assertEqual(self.head(), oid)
        # the cleanup owner mutates nothing: the owned delta stays staged
        # and is reported through blocked recovery
        self.assertEqual(self.staged_paths(), [self.PLAN_LOG])
        self.assert_cleanup_blocks_on_residue(proc)
        # the peer log's unstaged worktree bytes stay untouched
        self.assertTrue(self.worktree_dirty(self.EXEC_LOG))

    def test_post_hook_cas_refusal_cleans_only_owned_delta(self) -> None:
        exports, ref, oid = self.log_fixture()
        self.install_hook(
            "reference-transaction",
            '[ "$1" = prepared ] || exit 0\n'
            "while read -r _old _new r; do\n"
            f'  case "$r" in {ref}) exit 1;;\n'
            "  esac\n"
            "done\n"
            "exit 0\n",
        )
        (self.fixture / self.PLAN_LOG).write_text("# PLAN prompts\n" + self.ENTRY)
        proc = self.run_commit(
            "--stage", self.PLAN_LOG,
            "--subject", "log: append under a vetoed swap",
            "--expected-ref", ref, "--expected-oid", oid,
            env=self.rolling_env(exports),
        )
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn(
            "the ref transaction refused the captured branch ref "
            "compare-and-swap", proc.stderr,
        )
        self.assertEqual(self.head(), oid)
        # the cleanup owner mutates nothing: the owned delta stays staged
        # and is reported through blocked recovery
        self.assertEqual(self.staged_paths(), [self.PLAN_LOG])
        self.assertTrue(self.worktree_dirty(self.PLAN_LOG))
        self.assert_cleanup_blocks_on_residue(proc)

    # ---- a post-CAS failure never rolls the landed commit back ------------ #

    def test_ledger_append_failure_after_cas_keeps_commit_and_cleanup_disarmed(self) -> None:
        exports, ref, oid = self.log_fixture()
        # the fused ledger append cannot write: its path is a directory
        # (the run's own canonical ledger path; --run-id redirection would
        # now refuse pre-CAS under the explicit run-id binding check)
        blocked = self.done_session() / (
            f"owned-commits-{exports['DONE_RUN_ID']}.txt"
        )
        blocked.mkdir()
        (self.fixture / self.PLAN_LOG).write_text("# PLAN prompts\n" + self.ENTRY)
        proc = self.run_commit(
            "--stage", self.PLAN_LOG,
            "--subject", "log: append whose ledger append fails",
            "--expected-ref", ref, "--expected-oid", oid,
            env=self.rolling_env(exports),
        )
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn("the owned-commits ledger append failed", proc.stderr)
        self.assertIn("the landed commit stands", proc.stderr)
        # the captured ref advanced; the commit stands with sole parent
        landing = self.head()
        parents = self.git("rev-list", "--parents", "-1", "HEAD").stdout.split()
        self.assertEqual(parents, [landing, oid])
        # cleanup stayed disarmed (no cleanup message); the landed commit
        # consumed the staged delta, so the index matches the advanced HEAD
        self.assertEqual(self.staged_paths(), [])
        self.assert_no_rolling_cleanup(proc)

    # ---- pre-CAS refusal residue blocks later writers ---------------------- #

    def _unverifiable_cleanup_case(self, writer_log: str) -> None:
        exports, ref, oid = self.log_fixture()
        other_log = (
            self.EXEC_LOG if writer_log == self.PLAN_LOG else self.PLAN_LOG
        )
        # the writer's refusal driver: an em dash fails the landing sweep
        # before the CAS; the cleanup owner mutates nothing, so the owned
        # delta stays staged and is reported through blocked recovery
        (self.fixture / writer_log).write_text(
            f"# log\n- entry with an em dash {self.EM_DASH} here\n"
        )
        proc = self.run_commit(
            "--stage", writer_log,
            "--subject", "log: append whose refusal leaves residue",
            "--expected-ref", ref, "--expected-oid", oid,
            env=self.rolling_env(exports),
        )
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assert_cleanup_blocks_on_residue(proc)
        self.assertEqual(self.staged_paths(), [writer_log])
        residue_blob = self.git("ls-files", "-s", writer_log).stdout.split()[1]
        # a later writer of the same log refuses before git add, leaving
        # the residue bytes untouched
        (self.fixture / writer_log).write_text("# log\n- a later entry\n")
        later = self.run_commit(
            "--stage", writer_log, "--subject", "log: later same-log write",
            "--expected-ref", ref, "--expected-oid", oid,
            env=self.rolling_env(exports),
        )
        self.assertEqual(later.returncode, 1, later.stderr)
        self.assertIn(
            "a staged delta already exists on a rolling prompt log",
            later.stderr,
        )
        self.assertEqual(self.staged_paths(), [writer_log])
        self.assertEqual(
            self.git("ls-files", "-s", writer_log).stdout.split()[1],
            residue_blob,
        )
        self.assert_no_rolling_cleanup(later)
        # a later writer of the peer log refuses on the same residue
        (self.fixture / other_log).write_text("# peer log\n- peer entry\n")
        peer = self.run_commit(
            "--stage", other_log, "--subject", "log: later peer-log write",
            "--expected-ref", ref, "--expected-oid", oid,
            env=self.rolling_env(exports),
        )
        self.assertEqual(peer.returncode, 1, peer.stderr)
        self.assertIn(writer_log, peer.stderr)
        self.assertEqual(
            self.git("diff", "--cached", "--name-only", "HEAD", "--",
                     other_log).stdout,
            "",
        )
        self.assert_no_rolling_cleanup(peer)

    # ---- the refusal preserves declared bytes and index state (Task 2) ---- #

    def staging_race_helper(self, log_path: str) -> str:
        """A doctored helper that, in the runner's own pre-landing window,
        stages a second blob and then a mode-only update to the already
        staged declared path, plus an unrelated staged path (the origin
        edit-loss reproduction window; the pre-stage guard refuses any
        earlier unrelated staging, so it enters mid-run instead)."""
        return (
            "import subprocess\n"
            f"with open({log_path!r}, 'a') as handle:\n"
            "    handle.write('- second blob\\n')\n"
            "subprocess.run(['git', 'add', " + repr(log_path) + "], check=True)\n"
            "subprocess.run(['chmod', '+x', " + repr(log_path) + "], check=True)\n"
            "subprocess.run(['git', 'add', " + repr(log_path) + "], check=True)\n"
            "with open('unrelated.txt', 'w') as handle:\n"
            "    handle.write('unrelated staged\\n')\n"
            "subprocess.run(['git', 'add', 'unrelated.txt'], check=True)\n"
            "print('OUTCOME: pass')\n"
        )

    def test_pre_cas_refusal_preserves_staged_and_worktree_declared_bytes(self) -> None:
        exports, ref, oid = self.log_fixture()
        (self.fixture / self.PLAN_LOG).write_text("# PLAN prompts\n" + self.ENTRY)
        (self.fixture / "unrelated-wt.txt").write_text("untracked bytes\n")
        # the refusal driver: the doctored helper mutates the declared path
        # mid-run (second blob + mode-only update) and stages an unrelated
        # path, so the capture-window fence refuses pre-CAS
        runner_dir = self.temp_runner_dir({
            "reverse_squash_guard.py": self.staging_race_helper(self.PLAN_LOG),
        })
        proc = self.run_temp_commit(
            runner_dir, exports,
            "--stage", self.PLAN_LOG,
            "--subject", "log: append under a declared-path staging race",
            "--expected-ref", ref, "--expected-oid", oid,
        )
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn(
            "entered the staged index before the tree capture",
            proc.stdout + proc.stderr,
        )
        # the ref never advanced
        self.assertEqual(self.head(), oid)
        # the last staged blob (second content) and the mode change both
        # survive in the index and the worktree
        self.assertTrue(self.worktree_dirty(self.PLAN_LOG))
        staged_entry = self.git("ls-files", "-s", self.PLAN_LOG).stdout.strip()
        self.assertTrue(staged_entry.startswith("100755"), staged_entry)
        self.assertIn(
            "- second blob",
            self.git("show", f":{self.PLAN_LOG}").stdout,
        )
        self.assertIn(
            "- second blob",
            (self.fixture / self.PLAN_LOG).read_text(),
        )
        # unrelated staged and unstaged state is untouched
        self.assertEqual(
            self.staged_paths(),
            [self.PLAN_LOG, "unrelated.txt"],
        )
        self.assertTrue((self.fixture / "unrelated-wt.txt").exists())
        # blocked recovery names the owned residue
        self.assert_cleanup_blocks_on_residue(proc)

    def test_pre_cas_refusal_leaves_unrelated_staged_bytes_staged(self) -> None:
        exports, ref, oid = self.log_fixture()
        (self.fixture / self.PLAN_LOG).write_text("# PLAN prompts\n" + self.ENTRY)
        # the refusal driver: the capture-window fence (foreign paths
        # staged mid-run) refuses pre-CAS; the earlier unrelated staging
        # enters inside the same mid-run window
        helper = (
            "import subprocess\n"
            "with open('stranger-window.txt', 'w') as handle:\n"
            "    handle.write('staged in the capture window\\n')\n"
            "subprocess.run(['git', 'add', 'stranger-window.txt'], check=True)\n"
            "with open('unrelated.txt', 'w') as handle:\n"
            "    handle.write('unrelated staged\\n')\n"
            "subprocess.run(['git', 'add', 'unrelated.txt'], check=True)\n"
            "print('OUTCOME: pass')\n"
        )
        runner_dir = self.temp_runner_dir({
            "reverse_squash_guard.py": helper,
        })
        proc = self.run_temp_commit(
            runner_dir, exports,
            "--stage", self.PLAN_LOG,
            "--subject", "log: append beside unrelated staged bytes",
            "--expected-ref", ref, "--expected-oid", oid,
        )
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual(self.head(), oid)
        self.assertIn("unrelated.txt", self.staged_paths())
        self.assert_cleanup_blocks_on_residue(proc)

    def test_unverifiable_plan_log_cleanup_blocks_later_writers(self) -> None:
        self._unverifiable_cleanup_case(self.PLAN_LOG)

    def test_unverifiable_exec_log_cleanup_blocks_later_writers(self) -> None:
        self._unverifiable_cleanup_case(self.EXEC_LOG)


class DoneRunManifestSelectionTest(FixtureMixin, unittest.TestCase):
    """Manifest selection binds to the active confirmed marker: implicit
    selection matches the marker basename to exactly one canonical
    run-manifest-<run_id>.json payload whose run id agrees with its
    filename (a stale DONE_RUN_MANIFEST export is only a hint and never
    selects), an explicit --manifest is binding and missing, unreadable,
    marker-mismatched, run-id-mismatched, or noncanonical shadow paths
    refuse closed without fallthrough."""

    PLAN_LOG = "docs/history/backlog/PLAN-PROMPTS.md"
    EXEC_LOG = "docs/history/backlog/EXEC-PROMPTS.md"
    ENTRY = "\n- appended prompt entry\n"
    PEER_ID = "20991231T235959Z-peer00000001"

    def selection_fixture(self) -> tuple[dict, str, str, Path]:
        self.init_fixture_repo()
        log_dir = self.fixture / "docs" / "history" / "backlog"
        log_dir.mkdir(parents=True)
        (log_dir / "PLAN-PROMPTS.md").write_text("# PLAN prompts\n")
        (log_dir / "EXEC-PROMPTS.md").write_text("# EXEC prompts\n")
        self.git("add", self.PLAN_LOG, self.EXEC_LOG)
        self.git("commit", "-qm", "seed the rolling prompt logs")
        setup_proc, exports = self.setup_session("--owned-path", self.PLAN_LOG)
        branch = self.git("branch", "--show-current").stdout.strip()
        head = self.git("rev-parse", "HEAD").stdout.strip()
        manifest = Path(exports["DONE_RUN_MANIFEST"])
        return exports, "refs/heads/" + branch, head, manifest

    def craft_from(self, template: Path, run_id: str, **changes: object) -> Path:
        return self.craft_manifest_file(template, run_id, **changes)

    def head(self) -> str:
        return self.git("rev-parse", "HEAD").stdout.strip()

    def commit_with(self, exports: dict, *args: str) -> subprocess.CompletedProcess:
        env = self.commit_env()
        env.update(exports)
        return self.run_commit(
            "--stage", self.PLAN_LOG,
            "--subject", "log: manifest selection append",
            *args, env=env,
        )

    def test_implicit_selection_ignores_stale_export_peer_and_shadow(self) -> None:
        exports, ref, oid, manifest = self.selection_fixture()
        marker = json.loads(manifest.read_text())["marker"]
        # a finalized peer manifest under its own marker
        self.craft_from(
            manifest, self.PEER_ID, marker=f"{marker}-peer", complete=True,
        )
        # a divergent same-run shadow sharing the active marker
        shadow = self.done_session() / (
            f"run-manifest-{exports['DONE_RUN_ID']}.worktree.json"
        )
        shadow.write_text(manifest.read_text())
        # the setup export points at the shadow (stale hint)
        exports["DONE_RUN_MANIFEST"] = str(shadow)
        (self.fixture / self.PLAN_LOG).write_text(
            "# PLAN prompts\n" + self.ENTRY,
        )
        proc = self.commit_with(exports, "--expected-ref", ref,
                                "--expected-oid", oid)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(
            self.ENTRY.strip(),
            self.git("show", f"HEAD:{self.PLAN_LOG}").stdout,
        )
        ledger = self.done_session() / (
            f"owned-commits-{exports['DONE_RUN_ID']}.txt"
        )
        self.assertEqual(ledger.read_text().splitlines()[-1], self.head())

    def test_explicit_missing_manifest_refuses_without_fallthrough(self) -> None:
        exports, ref, oid, _ = self.selection_fixture()
        (self.fixture / self.PLAN_LOG).write_text(
            "# PLAN prompts\n" + self.ENTRY,
        )
        missing = str(self.tmp / "no-such-manifest.json")
        proc = self.commit_with(exports, "--manifest", missing,
                                "--expected-ref", ref, "--expected-oid", oid)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn("is missing or unreadable", proc.stderr)
        self.assertIn(missing, proc.stderr)
        self.assertEqual(self.head(), oid)
        self.assertEqual(self.staged_paths(), [self.PLAN_LOG])

    def staged_paths(self) -> list[str]:
        out = self.git("diff", "--cached", "--name-only", "HEAD").stdout
        return [line for line in out.splitlines() if line.strip()]

    def test_explicit_shadow_manifest_refuses_without_fallthrough(self) -> None:
        exports, ref, oid, manifest = self.selection_fixture()
        shadow = self.done_session() / (
            f"run-manifest-{exports['DONE_RUN_ID']}.worktree.json"
        )
        shadow.write_text(manifest.read_text())
        (self.fixture / self.PLAN_LOG).write_text(
            "# PLAN prompts\n" + self.ENTRY,
        )
        proc = self.commit_with(exports, "--manifest", str(shadow),
                                "--expected-ref", ref, "--expected-oid", oid)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn("noncanonical shadow name", proc.stderr)
        self.assertEqual(self.head(), oid)
        self.assertEqual(self.staged_paths(), [self.PLAN_LOG])

    def test_matching_shadow_explicit_with_broken_canonical_still_refuses(self) -> None:
        exports, ref, oid, manifest = self.selection_fixture()
        shadow = self.done_session() / (
            f"run-manifest-{exports['DONE_RUN_ID']}.worktree.json"
        )
        shadow.write_text(manifest.read_text())
        manifest.write_text("{ not json")  # the canonical record is broken
        (self.fixture / self.PLAN_LOG).write_text(
            "# PLAN prompts\n" + self.ENTRY,
        )
        proc = self.commit_with(exports, "--manifest", str(shadow),
                                "--expected-ref", ref, "--expected-oid", oid)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn("noncanonical shadow name", proc.stderr)
        self.assertEqual(self.head(), oid)

    def test_explicit_marker_mismatched_manifest_refuses(self) -> None:
        exports, ref, oid, manifest = self.selection_fixture()
        marker = json.loads(manifest.read_text())["marker"]
        foreign = self.craft_from(
            manifest, self.PEER_ID, marker=f"{marker}-foreign",
        )
        (self.fixture / self.PLAN_LOG).write_text(
            "# PLAN prompts\n" + self.ENTRY,
        )
        proc = self.commit_with(exports, "--manifest", str(foreign),
                                "--expected-ref", ref, "--expected-oid", oid)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn("records marker", proc.stderr)
        self.assertIn(
            json.loads(manifest.read_text())["marker"], proc.stderr,
        )
        self.assertEqual(self.head(), oid)

    def test_explicit_run_id_mismatch_refuses_distinctly(self) -> None:
        exports, ref, oid, _ = self.selection_fixture()
        (self.fixture / self.PLAN_LOG).write_text(
            "# PLAN prompts\n" + self.ENTRY,
        )
        proc = self.commit_with(exports, "--run-id", "20991231T000000Z-wrong00",
                                "--expected-ref", ref, "--expected-oid", oid)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn("--run-id 20991231T000000Z-wrong00 does not match",
                      proc.stderr)
        self.assertIn(exports["DONE_RUN_ID"], proc.stderr)
        self.assertEqual(self.head(), oid)

    def test_payload_run_id_disagreeing_with_filename_refuses_no_fallback(self) -> None:
        exports, ref, oid, manifest = self.selection_fixture()
        record = json.loads(manifest.read_text())
        record["run_id"] = "20991231T111111Z-mismatch0001"
        manifest.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        (self.fixture / self.PLAN_LOG).write_text(
            "# PLAN prompts\n" + self.ENTRY,
        )
        proc = self.commit_with(exports, "--expected-ref", ref,
                                "--expected-oid", oid)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn("no canonical manifest payload carries", proc.stderr)
        self.assertIn(record["marker"], proc.stderr)
        self.assertEqual(self.head(), oid)
        self.assertEqual(self.staged_paths(), [self.PLAN_LOG])

    def test_two_canonical_manifests_claiming_the_marker_refuse(self) -> None:
        exports, ref, oid, manifest = self.selection_fixture()
        marker = json.loads(manifest.read_text())["marker"]
        # a second canonical record claiming the SAME active marker
        self.craft_from(manifest, self.PEER_ID, marker=marker)
        (self.fixture / self.PLAN_LOG).write_text(
            "# PLAN prompts\n" + self.ENTRY,
        )
        proc = self.commit_with(exports, "--expected-ref", ref,
                                "--expected-oid", oid)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn("2 canonical manifests claim the active confirmed",
                      proc.stderr)
        self.assertEqual(self.head(), oid)

    def test_unparseable_canonical_candidate_refuses(self) -> None:
        exports, ref, oid, manifest = self.selection_fixture()
        manifest.write_text("{ not json")
        (self.fixture / self.PLAN_LOG).write_text(
            "# PLAN prompts\n" + self.ENTRY,
        )
        proc = self.commit_with(exports, "--expected-ref", ref,
                                "--expected-oid", oid)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn("is unparseable", proc.stderr)
        self.assertEqual(self.head(), oid)
        self.assertEqual(self.staged_paths(), [self.PLAN_LOG])

    def test_implicit_selection_skips_shadow_copies_silently(self) -> None:
        exports, ref, oid, manifest = self.selection_fixture()
        # an unparseable SHADOW copy is not a canonical candidate and never
        # refuses the implicit selection
        shadow = self.done_session() / (
            f"run-manifest-{exports['DONE_RUN_ID']}.worktree.json"
        )
        shadow.write_text("{ not json")
        (self.fixture / self.PLAN_LOG).write_text(
            "# PLAN prompts\n" + self.ENTRY,
        )
        proc = self.commit_with(exports, "--expected-ref", ref,
                                "--expected-oid", oid)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(
            self.ENTRY.strip(),
            self.git("show", f"HEAD:{self.PLAN_LOG}").stdout,
        )


if __name__ == "__main__":
    unittest.main()
