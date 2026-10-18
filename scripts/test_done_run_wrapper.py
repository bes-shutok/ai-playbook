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

import json
import os
import shlex
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNNER = REPO_ROOT / "scripts" / "done_run.sh"
LOCK_SCRIPT = REPO_ROOT / "scripts" / "done-lock.sh"
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

    def setUp(self) -> None:
        self.tmp = Path(__import__("tempfile").mkdtemp(prefix="done-run-fixture-"))
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
        ):
            env.pop(var, None)
        self.base_env = env

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
        self, setup_proc: subprocess.CompletedProcess, exports: dict, *commit_args: str,
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
        worktree, the docs-branch sync is skipped, the review-artifact
        migration still runs (its stdout line present), and one trace line
        names the skipped leg; the landing commit still lands."""
        self.init_fixture_repo()
        (self.fixture / "seed.txt").write_text("seed\nwork\n")
        primary_head = self.git("rev-parse", "HEAD").stdout.strip()
        worktree = self.tmp / "per-task-wt"
        self.git("worktree", "add", "-b", "per-task-wt-branch", str(worktree))
        try:
            (worktree / "seed.txt").write_text("seed\nwork\nper-task edit\n")
            wt_env = self.runner_env()
            wt_env["DONE_SWEEP_REPO_ROOT"] = str(worktree)
            setup = subprocess.run(
                ["bash", str(RUNNER), "setup", "--owned-path", "seed.txt"],
                cwd=str(worktree), env=wt_env,
                capture_output=True, text=True, timeout=300,
            )
            self.assertEqual(setup.returncode, 0, setup.stderr)
            # the done-lock session fence is done-lock's status witness, not
            # fixture state under test: remove it so the commit's foreign-dirt
            # gate sees only the declared work
            fence = worktree / ".ai-playbook" / "done-lock.session"
            if fence.exists():
                fence.unlink()
            env = self.commit_env()
            env["DONE_SWEEP_REPO_ROOT"] = str(worktree)
            env.update(self.eval_exports(setup.stdout))
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
            # the migration kept its position: its stdout line or manifest
            migration_ran = (
                "migrating review staging docs" in combined
                or any(
                    path.name.startswith("worktree-migrate-manifest")
                    for path in (worktree / "docs" / "tmp" / "done-session").glob(
                        "worktree-migrate-manifest-*.json"
                    )
                )
            )
            self.assertTrue(migration_ran, combined)
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

    def test_empty_declared_set_over_staged_foreign_file_refuses_at_landing_commit(self) -> None:
        self.worktree_fixture()
        setup_proc, exports = self.setup_session("--owned-path", "seed.txt")
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


if __name__ == "__main__":
    unittest.main()
