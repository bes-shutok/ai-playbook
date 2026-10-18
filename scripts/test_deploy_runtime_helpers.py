"""Contract tests for scripts/deploy_runtime_helpers.sh (the runtime-helper
deployment carrier).

The carrier deploys every name the canonical repo's scripts/runtime-scripts.list
admits from the resolved canonical repo into the runtime home (default
~/.ai-playbook/scripts), converting lagging regular-file copies into symlinks
with a .bak-<UTC date> sibling. Every fixture drives the real carrier through
subprocess with a temp --home, so the tests never touch the real runtime home.
"""

import hashlib
import os
import shutil
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
CARRIER = SCRIPTS_DIR / "deploy_runtime_helpers.sh"


def run_carrier(*args, cwd=None):
    """Invoke the carrier script in a subprocess and return the result."""
    return subprocess.run(
        ["bash", str(CARRIER), *[str(a) for a in args]],
        cwd=str(cwd) if cwd is not None else None,
        capture_output=True,
        text=True,
    )


def assert_pass(proc):
    assert proc.returncode == 0, "rc=%s stdout=%s stderr=%s" % (
        proc.returncode,
        proc.stdout,
        proc.stderr,
    )
    assert proc.stdout.strip().endswith("OUTCOME: pass"), proc.stdout


def assert_refused(proc):
    assert proc.returncode == 3, "rc=%s stdout=%s stderr=%s" % (
        proc.returncode,
        proc.stdout,
        proc.stderr,
    )
    assert proc.stdout.strip().endswith("OUTCOME: tool_error"), proc.stdout


class DeployRuntimeHelpersTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="deploy-runtime-helpers-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    # -- fixture helpers ---------------------------------------------------

    def make_canonical(self, names):
        """A temp canonical repo: scripts/<name> current bytes + the manifest."""
        canonical = self.tmp / "canonical"
        (canonical / "scripts").mkdir(parents=True)
        for name in names:
            (canonical / "scripts" / name).write_text("current bytes for %s\n" % name)
        self.write_manifest(canonical, names)
        return canonical

    def write_manifest(self, canonical, lines):
        path = canonical / "scripts" / "runtime-scripts.list"
        path.write_text("".join("%s\n" % line for line in lines))

    def facts_stub(self, value):
        """A user-facts document whose skills_repo_path table row names value."""
        path = self.tmp / "facts-stub.md"
        path.write_text(
            "# facts stub\n\n| Key | Value | Purpose |\n"
            "|-----|-------|---------|\n"
            "| `skills_repo_path` | `%s` | facts stub row |\n" % value
        )
        return path

    def canonical_snapshot(self, canonical):
        """Path set plus byte digests for every entry under the canonical repo."""
        state = {}
        for path in sorted(canonical.rglob("*")):
            rel = str(path.relative_to(canonical))
            if path.is_symlink():
                state[rel] = "symlink:%s" % os.readlink(path)
            elif path.is_dir():
                state[rel] = "dir"
            else:
                state[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
        return state

    # -- fixtures ----------------------------------------------------------

    def test_deploy_syncs_manifest_names_with_bak_aside_and_symlink(self):
        canonical = self.make_canonical(["alpha.py", "beta.py"])
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        (runtime / "alpha.py").write_text("stale bytes\n")
        proc = run_carrier(
            "--repo", canonical, "--home", runtime, cwd=self.tmp
        )
        assert_pass(proc)
        link = runtime / "alpha.py"
        self.assertTrue(link.is_symlink(), proc.stdout)
        self.assertEqual(
            os.path.realpath(link),
            os.path.realpath(canonical / "scripts" / "alpha.py"),
        )
        baks = list(runtime.glob("alpha.py.bak-*"))
        self.assertEqual(len(baks), 1, proc.stdout)
        self.assertEqual(baks[0].read_text(), "stale bytes\n")
        self.assertTrue((runtime / "beta.py").is_symlink(), proc.stdout)
        self.assertEqual(
            os.path.realpath(runtime / "beta.py"),
            os.path.realpath(canonical / "scripts" / "beta.py"),
        )

    def test_deploy_links_missing_name_and_leaves_correct_symlink_current(self):
        canonical = self.make_canonical(["gamma.py", "delta.py"])
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        (runtime / "delta.py").symlink_to(canonical / "scripts" / "delta.py")
        before = os.readlink(runtime / "delta.py")
        proc = run_carrier("--repo", canonical, "--home", runtime, cwd=self.tmp)
        assert_pass(proc)
        self.assertTrue((runtime / "gamma.py").is_symlink(), proc.stdout)
        self.assertEqual(
            os.path.realpath(runtime / "gamma.py"),
            os.path.realpath(canonical / "scripts" / "gamma.py"),
        )
        self.assertEqual(os.readlink(runtime / "delta.py"), before)
        self.assertIn("current: delta.py", proc.stdout)
        self.assertEqual(list(runtime.glob("delta.py.bak-*")), [])

    def test_check_reports_stale_missing_current_and_exits_zero(self):
        canonical = self.make_canonical(["stale_one.py", "gone.py", "fresh.py"])
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        (runtime / "stale_one.py").write_text("old bytes\n")
        (runtime / "fresh.py").symlink_to(canonical / "scripts" / "fresh.py")
        proc = run_carrier(
            "--check", "--repo", canonical, "--home", runtime, cwd=self.tmp
        )
        assert_pass(proc)
        lines = proc.stdout.splitlines()
        stale = [line for line in lines if line.startswith("stale:")]
        missing = [line for line in lines if line.startswith("missing:")]
        self.assertEqual(len(stale), 1, proc.stdout)
        self.assertEqual(len(missing), 1, proc.stdout)
        self.assertIn("stale_one.py", stale[0])
        self.assertIn("deploy_runtime_helpers.sh", stale[0])
        self.assertIn("gone.py", missing[0])
        self.assertIn("deploy_runtime_helpers.sh", missing[0])
        self.assertFalse(any("fresh.py" in line for line in lines), proc.stdout)

    def test_consumer_environment_resolves_canonical_from_facts(self):
        canonical = self.make_canonical(["helper.py"])
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        (runtime / "helper.py").write_text("stale\n")
        workdir = self.tmp / "consumer-project"
        workdir.mkdir()
        facts = self.facts_stub(canonical)
        proc = run_carrier(
            "--check", "--facts", facts, "--home", runtime, cwd=workdir
        )
        assert_pass(proc)
        self.assertTrue(
            any(
                line.startswith("stale:") and "helper.py" in line
                for line in proc.stdout.splitlines()
            ),
            proc.stdout,
        )
        proc = run_carrier("--facts", facts, "--home", runtime, cwd=workdir)
        assert_pass(proc)
        self.assertEqual(
            os.path.realpath(runtime / "helper.py"),
            os.path.realpath(canonical / "scripts" / "helper.py"),
        )

    def test_skills_repo_invocation_resolves_canonical_to_invocation_repo(self):
        checkout = self.tmp / "skills-checkout"
        (checkout / "scripts").mkdir(parents=True)
        (checkout / "scripts" / "local_helper.py").write_text("checkout bytes\n")
        (checkout / "scripts" / "second.py").write_text("second bytes\n")
        self.write_manifest(checkout, ["local_helper.py", "second.py"])
        subprocess.run(
            ["git", "init", "-q", str(checkout)], check=True, capture_output=True
        )
        elsewhere = self.tmp / "elsewhere"
        (elsewhere / "scripts").mkdir(parents=True)
        (elsewhere / "scripts" / "decoy.py").write_text("decoy bytes\n")
        self.write_manifest(elsewhere, ["decoy.py"])
        facts = self.facts_stub(elsewhere)
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        (runtime / "local_helper.py").write_text("stale\n")
        workdir = checkout / "scripts"
        proc = run_carrier(
            "--check", "--facts", facts, "--home", runtime, cwd=workdir
        )
        assert_pass(proc)
        self.assertTrue(
            any(
                line.startswith("stale:") and "local_helper.py" in line
                for line in proc.stdout.splitlines()
            ),
            proc.stdout,
        )
        proc = run_carrier("--facts", facts, "--home", runtime, cwd=workdir)
        assert_pass(proc)
        self.assertEqual(
            os.path.realpath(runtime / "local_helper.py"),
            os.path.realpath(checkout / "scripts" / "local_helper.py"),
        )
        self.assertEqual(
            os.path.realpath(runtime / "second.py"),
            os.path.realpath(checkout / "scripts" / "second.py"),
        )
        self.assertFalse((runtime / "decoy.py").exists())
        self.assertFalse((runtime / "decoy.py").is_symlink())

    def test_unresolvable_canonical_refuses_deploy_and_reports_check(self):
        workdir = self.tmp / "consumer-project"
        workdir.mkdir()
        bare_facts = self.tmp / "bare-facts.md"
        bare_facts.write_text("| `other_key` | `x` | unrelated row |\n")
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        # Arm 1: no --repo, a facts document without the key, a non-skills cwd.
        proc = run_carrier(
            "--facts", bare_facts, "--home", runtime, cwd=workdir
        )
        assert_refused(proc)
        self.assertIn("no canonical repo resolved", proc.stdout)
        proc = run_carrier(
            "--check", "--facts", bare_facts, "--home", runtime, cwd=workdir
        )
        assert_pass(proc)
        self.assertIn("advisory", proc.stdout)
        self.assertIn("skipped", proc.stdout)
        # Arm 2: a canonical repo that resolves but carries no manifest.
        empty = self.tmp / "empty-repo"
        empty.mkdir()
        proc = run_carrier("--repo", empty, "--home", runtime, cwd=workdir)
        assert_refused(proc)
        self.assertIn("runtime-scripts.list", proc.stdout)
        proc = run_carrier(
            "--check", "--repo", empty, "--home", runtime, cwd=workdir
        )
        assert_pass(proc)
        self.assertIn("advisory", proc.stdout)
        self.assertIn("skipped", proc.stdout)

    def test_prefixed_manifest_entry_maps_to_basename_and_stale_variants_flip(self):
        canonical = self.tmp / "canonical"
        (canonical / "scripts").mkdir(parents=True)
        for name in ("prefixed.py", "aimer.py", "collider.py"):
            (canonical / "scripts" / name).write_text("current bytes for %s\n" % name)
        self.write_manifest(
            canonical,
            ["# comment lines are skipped", "", "scripts/prefixed.py", "aimer.py", "collider.py"],
        )
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        decoy = runtime / "decoy_target.txt"
        decoy.write_text("decoy bytes\n")
        (runtime / "aimer.py").symlink_to(decoy)
        (runtime / "collider.py").write_text("old live bytes\n")
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        colliding = runtime / ("collider.py.bak-%s" % today)
        colliding.write_text("old sibling bytes\n")
        proc = run_carrier("--repo", canonical, "--home", runtime, cwd=self.tmp)
        assert_pass(proc)
        # The scripts/ prefix maps to the runtime-home basename.
        self.assertTrue((runtime / "prefixed.py").is_symlink(), proc.stdout)
        self.assertEqual(
            os.path.realpath(runtime / "prefixed.py"),
            os.path.realpath(canonical / "scripts" / "prefixed.py"),
        )
        # The aimed-elsewhere symlink is moved aside, not dereferenced.
        self.assertEqual(
            os.path.realpath(runtime / "aimer.py"),
            os.path.realpath(canonical / "scripts" / "aimer.py"),
        )
        aimer_baks = list(runtime.glob("aimer.py.bak-*"))
        self.assertEqual(len(aimer_baks), 1, proc.stdout)
        self.assertTrue(aimer_baks[0].is_symlink())
        self.assertEqual(os.path.realpath(aimer_baks[0]), os.path.realpath(decoy))
        # The colliding .bak-<date> sibling is replaced by the newer one.
        self.assertEqual(colliding.read_text(), "old live bytes\n")
        self.assertEqual(len(list(runtime.glob("collider.py.bak-*"))), 1)
        self.assertTrue((runtime / "collider.py").is_symlink())
        self.assertEqual(
            os.path.realpath(runtime / "collider.py"),
            os.path.realpath(canonical / "scripts" / "collider.py"),
        )

    def test_never_writes_into_the_canonical_repo(self):
        canonical = self.make_canonical(["one.py", "two.py", "three.py"])
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        (runtime / "one.py").write_text("stale\n")
        (runtime / "three.py").symlink_to(canonical / "scripts" / "three.py")
        before = self.canonical_snapshot(canonical)
        for mode_args in ([], ["--check"]):
            proc = run_carrier(
                *mode_args, "--repo", canonical, "--home", runtime, cwd=self.tmp
            )
            assert_pass(proc)
            self.assertEqual(self.canonical_snapshot(canonical), before)

    def test_missing_canonical_name_is_skipped_not_fabricated(self):
        canonical = self.make_canonical(["real.py"])
        self.write_manifest(canonical, ["real.py", "ghost.py"])
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        proc = run_carrier(
            "--check", "--repo", canonical, "--home", runtime, cwd=self.tmp
        )
        assert_pass(proc)
        self.assertTrue(
            any(
                line.startswith("skip:") and "ghost.py" in line
                for line in proc.stdout.splitlines()
            ),
            proc.stdout,
        )
        proc = run_carrier("--repo", canonical, "--home", runtime, cwd=self.tmp)
        assert_pass(proc)
        self.assertTrue(
            any(
                line.startswith("skip:") and "ghost.py" in line
                for line in proc.stdout.splitlines()
            ),
            proc.stdout,
        )
        self.assertFalse((runtime / "ghost.py").exists())
        self.assertFalse((runtime / "ghost.py").is_symlink())
        self.assertEqual(list(runtime.glob("ghost.py.bak-*")), [])
        self.assertTrue((runtime / "real.py").is_symlink())


if __name__ == "__main__":
    unittest.main()
