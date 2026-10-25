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
    # must never redirect a fixture call away from the temporary repo.
    HOST_GIT_SELECTORS = (
        "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
        "GIT_CONFIG_PARAMETERS", "GIT_EXTERNAL_DIFF", "GIT_CONFIG_COUNT",
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
        env["DONE_LOCK_ROOT"] = str(self.tmp / "locks" / "done")
        env["MERGE_LOCK_ROOT"] = str(self.tmp / "locks" / "merge")
        env["MERGE_LOCK_POLL_SECS"] = "1"
        env["DONE_LOCK_SCRIPT"] = str(LOCK_SCRIPT)
        env["DONE_SWEEP_REPO_ROOT"] = str(self.fixture)
        env["DONE_SWEEP_RUNTIME_HOME"] = str(self.tmp / "runtime-home")
        env["DONE_SWEEP_USER_FACTS"] = str(self.tmp / "user-facts.md")
        return env

    def run_setup(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(RUNNER), "setup", *args],
            cwd=str(cwd or self.fixture),
            env=self.runner_env(),
            capture_output=True,
            text=True,
            timeout=300,
        )

    def done_session(self) -> Path:
        return self.fixture / "docs" / "tmp" / "done-session"

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

    def run_commit(self, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(RUNNER), "commit", *args],
            cwd=str(self.fixture),
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


class DoneRunSetupManifestStateTest(FixtureMixin, unittest.TestCase):
    """Task 1 witnesses (plan
    docs/history/plans/2026-10-12-done-interrupted-manifest-state-
    classification.md): setup classifies the newest manifest through the
    canonical terminal states consumed from done_sweep_gates_lib's
    classify_run_boundary (read at run identity), the orphan and marker
    refusals stay byte-identical, and a corrupt newest record fails closed
    naming the record."""

    def rewrite_manifest(self, manifest: Path, **changes: object) -> None:
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
        notes = self.terminal_notes(second.stdout)
        self.assertEqual(len(notes), 1, second.stdout)
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
        notes = self.terminal_notes(second.stdout)
        self.assertEqual(len(notes), 1, second.stdout)
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
        notes = self.terminal_notes(second.stdout)
        self.assertEqual(len(notes), 1, second.stdout)
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
        notes = self.terminal_notes(second.stdout)
        self.assertEqual(len(notes), 1, second.stdout)
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
            f"recover-manifest --run-id {run_id} | re-enter with --from-manifest "
            f"{run_id} (adopt) | python3 scripts/done_sweep_gates_lib.py "
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
            f"recover-manifest --run-id {run_id} | adopt via --from-manifest "
            f"{run_id} | python3 scripts/done_sweep_gates_lib.py "
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
        still lands."""
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
            # the migration manifest records the transfer verified
            manifests = list(wt_session.glob("worktree-migrate-manifest-*.json"))
            self.assertEqual(len(manifests), 1)
            data = json.loads(manifests[0].read_text(encoding="utf-8"))
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
    "scripts/land_squash.sh land under the merge lock); operator escape "
    "for dead residue only (done-lock.sh merge-status free AND the path "
    "is not peer-live dirt): git restore --staged --worktree -- <path> "
    "per residue path; record-only allowlist path(s) are never escapable"
)
RECORD_ONLY_CORPUS_REL = "projects/.ai-playbook/development_lessons.md"


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

    def rewrite_manifest(self, exports: dict, **changes: object) -> None:
        manifest = Path(exports["DONE_RUN_MANIFEST"])
        record = json.loads(manifest.read_text())
        record.update(changes)
        manifest.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")

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
        crafted = self.tmp / "crafted-manifest.json"
        record = json.loads(Path(exports["DONE_RUN_MANIFEST"]).read_text())
        record["marker"] = "run-start-00000000-dead"
        crafted.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        proc = self.run_commit(
            "--stage", "work.txt",
            "--authorize-ancestor-restoration", "work.txt", ancestor_blob,
            "--subject", "authorize with a foreign manifest export",
            env=self.authorized_env(exports, DONE_RUN_MANIFEST=str(crafted)),
        )
        self.assert_refused(proc, exports, prior_head,
                            "not bound to the newest root-confirmed marker")

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

    def run_finalize(self, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(RUNNER), "finalize", *args],
            cwd=str(self.fixture),
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
        proc = self.run_finalize("--from-holder", env=lost_env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("from-holder", proc.stdout + proc.stderr)
        self.assertIn(": free", self.lock_status())
        self.assertIn(": free", self.lock_status(merge=True))
        record = self.manifest_record(exports)
        self.assertTrue(record.get("complete", False))

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

    # ---- guard-liveness append placement (plan 2026-10-24-description-
    #      length-gate-catch-promotion): the append loop runs BEFORE the
    #      done-lock release; append failure stays a warning and the lock
    #      releases. ------------------------------------------------------- #

    def seed_guard_ledger(self) -> Path:
        ledger = self.fixture / "scripts" / "gate_liveness_ledger.json"
        ledger.parent.mkdir(parents=True, exist_ok=True)
        ledger.write_text(json.dumps(
            {"schema": 1, "window": {"started": "2026-10-05"}, "guards": {}}
        ))
        return ledger

    def ordering_lock_stub(self, ledger: Path) -> Path:
        """A stub done-lock whose release-repo refuses unless the fixture
        guard-liveness ledger already carries a run_id row: a passing
        finalize proves the append loop ran before the release."""
        stub = self.tmp / "ordering-lock.sh"
        stub.write_text(
            "#!/usr/bin/env bash\n"
            'LEDGER="%s"\n'
            'case "$1" in\n'
            "  release-repo)\n"
            '    if grep -q "run_id=" "$LEDGER" 2>/dev/null; then\n'
            '      echo "stub: released after the ledger row existed"\n'
            '      echo "OUTCOME: pass"\n'
            "    else\n"
            '      echo "stub: no guard-liveness row at release time" >&2\n'
            '      echo "OUTCOME: fail"\n'
            "      exit 2\n"
            "    fi ;;\n"
            '  merge-status) echo "stub merge-lock: free" ;;\n'
            '  status) echo "stub done-lock: free" ;;\n'
            '  *) echo "OUTCOME: pass" ;;\n'
            "esac\n" % ledger,
            encoding="utf-8",
        )
        return stub

    def test_guard_liveness_appends_run_before_done_lock_release(self) -> None:
        self.init_fixture_repo()
        ledger = self.seed_guard_ledger()
        setup_proc, exports = self.setup_session("--label", "append-order-fixture")
        run_id = exports["DONE_RUN_ID"]
        env = self.runner_env()
        env.update(exports)
        env["DONE_LOCK_SCRIPT"] = str(self.ordering_lock_stub(ledger))
        env["GATE_LIVENESS_LEDGER_PATH"] = str(ledger)
        proc = self.run_finalize(
            "--guard-firing",
            f"description-length:catch:fixture-evidence:run_id={run_id}",
            env=env,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        # The release only succeeded because the row already existed: the
        # append loop ran before the done-lock release.
        self.assertIn("released after the ledger row existed", proc.stdout)
        self.assertIn("done lock status: free", proc.stdout)
        data = json.loads(ledger.read_text())
        rows = data["guards"]["description-length"]["rows"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["kind"], "catch")
        self.assertIn(f"run_id={run_id}", rows[0]["note"])

    def test_guard_liveness_append_failure_warns_and_lock_releases(self) -> None:
        self.init_fixture_repo()
        setup_proc, exports = self.setup_session("--label", "append-fail-fixture")
        corrupt = self.tmp / "corrupt-ledger.json"
        corrupt.write_text("{not json")
        env = self.runner_env()
        env.update(exports)
        env["GATE_LIVENESS_LEDGER_PATH"] = str(corrupt)
        proc = self.run_finalize(
            "--guard-firing",
            "description-length:catch:fixture-evidence:run_id=run-x",
            env=env,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn(
            "guard-liveness append failed for description-length", proc.stderr
        )
        # The real lock released anyway: the append failure is warning-only.
        self.assertIn(": free", self.lock_status())
        self.assertIn("done lock status: free", proc.stdout)


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
        for var in (
            "GIT_DIR", "GIT_INDEX_FILE", "GIT_CONFIG_COUNT",
            "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0",
        ):
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
        self.assertEqual(len(manifests), 1)
        data = json.loads(manifests[0].read_text(encoding="utf-8"))
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
        self.assertEqual(len(manifests), 1)
        data = json.loads(manifests[0].read_text(encoding="utf-8"))
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
        manifests = list(self.wt_session(worktree).glob("worktree-migrate-manifest-*.json"))
        self.assertEqual(len(manifests), 1)
        data = json.loads(manifests[0].read_text(encoding="utf-8"))
        migrated = {entry["source"] for entry in data["migrated"]}
        self.assertIn(f".ai-playbook/reviews/{record.name}", migrated)
        self.assertIn("docs-branch: sync complete", combined)

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


if __name__ == "__main__":
    unittest.main()
