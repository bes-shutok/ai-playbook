#!/usr/bin/env python3
"""Selftest for sync_runtime_scripts.sh: hermetic scratch canonical repos and
pinned DEPLOYED_ROOT targets for every disposition (current, installed,
converted, left) and every escalation the sync refuses on. No run touches the
real home: every subprocess gets a pinned DEPLOYED_ROOT and a scratch
canonical repo holding a copy of the script."""

import os
import shutil
import subprocess
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "sync_runtime_scripts.sh"


def scrub_env():
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return env


def git(root, *args):
    proc = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True, text=True, check=False, env=scrub_env(),
    )
    assert proc.returncode == 0, (args, proc.stderr)
    return proc.stdout.strip()


def make_repo(path):
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.email", "fixture@example.invalid")
    git(path, "config", "user.name", "fixture")
    return path


class SyncRuntimeScriptsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        base = Path(self._tmp.name)
        self.repo = base / "canon"
        self.scripts = (self.repo / "scripts").resolve()  # resolved form: the
        # script writes readlink -f targets, on macOS /private/var/... not /var
        self.scripts.mkdir(parents=True, exist_ok=True)
        make_repo(self.repo)
        shutil.copy2(SCRIPT, self.scripts / "sync_runtime_scripts.sh")
        self.deployed = base / "deployed" / "scripts"
        self.deployed.mkdir(parents=True)
        self.today = datetime.now().strftime("%Y%m%d")

    def write_manifest(self, *lines):
        (self.scripts / "runtime-scripts.list").write_text("\n".join(lines) + "\n")

    def put_canonical(self, name, content, commit=False):
        (self.scripts / name).write_text(content)
        if commit:
            git(self.repo, "add", f"scripts/{name}")
            git(self.repo, "commit", "-q", "-m", f"fixture {name}")

    def put_deployed_regular(self, name, content):
        (self.deployed / name).write_text(content)

    def put_deployed_canonical_symlink(self, name):
        os.symlink(str(self.scripts / name), str(self.deployed / name))

    def run_sync(self, script_path=None, deployed_root=None):
        env = scrub_env()
        env["DEPLOYED_ROOT"] = str(self.deployed if deployed_root is None else deployed_root)
        return subprocess.run(
            ["bash", str(self.scripts / "sync_runtime_scripts.sh" if script_path is None else script_path)],
            capture_output=True, text=True, check=False, env=env,
        )

    def snapshot(self):
        state = {}
        for entry in sorted(os.listdir(self.deployed)):
            path = self.deployed / entry
            if os.path.islink(path):
                state[entry] = ("link", os.readlink(path))
            elif os.path.isdir(path):
                state[entry] = ("dir",)
            elif os.path.isfile(path):
                state[entry] = ("file", path.read_text())
            else:
                state[entry] = ("other",)
        return state

    def test_fresh_install(self):
        self.write_manifest("probe_a.py")
        self.put_canonical("probe_a.py", "canonical bytes\n", commit=True)
        proc = self.run_sync()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("sync: probe_a.py: installed", proc.stdout)
        self.assertEqual(os.readlink(self.deployed / "probe_a.py"), str(self.scripts / "probe_a.py"))

    def test_current_symlink_noop(self):
        self.write_manifest("probe_a.py")
        self.put_canonical("probe_a.py", "canonical bytes\n", commit=True)
        self.put_deployed_canonical_symlink("probe_a.py")
        proc = self.run_sync()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("sync: probe_a.py: current", proc.stdout)
        self.assertEqual(os.readlink(self.deployed / "probe_a.py"), str(self.scripts / "probe_a.py"))

    def test_digest_current_conversion(self):
        self.write_manifest("probe_a.py")
        self.put_canonical("probe_a.py", "same bytes\n", commit=True)
        self.put_deployed_regular("probe_a.py", "same bytes\n")
        proc = self.run_sync()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("sync: probe_a.py: converted (digest-current, git-clean", proc.stdout)
        self.assertEqual(os.readlink(self.deployed / "probe_a.py"), str(self.scripts / "probe_a.py"))
        bak = self.deployed / f"probe_a.py.bak-{self.today}"
        self.assertEqual(bak.read_text(), "same bytes\n")

    def test_digest_drifted_conversion_records_compare_outcome(self):
        self.write_manifest("probe_a.py")
        self.put_canonical("probe_a.py", "canonical bytes\n")  # untracked: git-dirty
        self.put_deployed_regular("probe_a.py", "drifted bytes\n")
        proc = self.run_sync()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("sync: probe_a.py: converted (digest-drifted, git-dirty", proc.stdout)
        self.assertEqual(os.readlink(self.deployed / "probe_a.py"), str(self.scripts / "probe_a.py"))
        bak = self.deployed / f"probe_a.py.bak-{self.today}"
        self.assertEqual(bak.read_text(), "drifted bytes\n")

    def test_bak_name_exists_refuses(self):
        self.write_manifest("probe_a.py")
        self.put_canonical("probe_a.py", "canonical bytes\n", commit=True)
        self.put_deployed_regular("probe_a.py", "deployed bytes\n")
        (self.deployed / f"probe_a.py.bak-{self.today}").write_text("prior residue\n")
        proc = self.run_sync()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("escalated", proc.stdout)
        self.assertIn("already exists", proc.stdout)
        self.assertEqual((self.deployed / "probe_a.py").read_text(), "deployed bytes\n")

    def test_no_counterpart_left_alone(self):
        self.write_manifest("orphan.py")
        self.put_deployed_regular("orphan.py", "deployed-only bytes\n")
        proc = self.run_sync()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("sync: orphan.py: left", proc.stdout)
        self.assertEqual((self.deployed / "orphan.py").read_text(), "deployed-only bytes\n")

    def test_foreign_symlink_escalates(self):
        foreign_target = Path(self._tmp.name) / "foreign.txt"
        foreign_target.write_text("foreign\n")
        self.write_manifest("probe_a.py")
        self.put_canonical("probe_a.py", "canonical bytes\n", commit=True)
        os.symlink(str(foreign_target), str(self.deployed / "probe_a.py"))
        proc = self.run_sync()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("sync: probe_a.py: escalated", proc.stdout)
        self.assertIn("outside the canonical scripts directory", proc.stdout)
        self.assertEqual(os.readlink(self.deployed / "probe_a.py"), str(foreign_target))

    def test_dangling_deployed_symlink_escalates(self):
        self.write_manifest("probe_a.py")
        os.symlink(str(self.scripts / "probe_a.py"), str(self.deployed / "probe_a.py"))
        proc = self.run_sync()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("sync: probe_a.py: escalated", proc.stdout)
        self.assertIn("dangling", proc.stdout)
        self.assertEqual(os.readlink(self.deployed / "probe_a.py"), str(self.scripts / "probe_a.py"))
        self.assertFalse((self.scripts / "probe_a.py").exists())

    def test_canonical_absent_manifest_entry_escalates(self):
        self.write_manifest("ghost.py")
        proc = self.run_sync()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("sync: ghost.py: escalated", proc.stdout)
        self.assertIn("absent both deployed and canonical", proc.stdout)
        self.assertFalse((self.deployed / "ghost.py").exists())

    def test_mixed_manifest_pins_exit_one_with_lines(self):
        self.write_manifest("cur.py", "conv.py", "ghost.py")
        self.put_canonical("cur.py", "cur bytes\n", commit=True)
        self.put_canonical("conv.py", "conv canonical\n", commit=True)
        self.put_deployed_canonical_symlink("cur.py")
        self.put_deployed_regular("conv.py", "conv deployed\n")
        proc = self.run_sync()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("sync: cur.py: current", proc.stdout)
        self.assertIn("sync: conv.py: converted", proc.stdout)
        self.assertIn("sync: ghost.py: escalated", proc.stdout)
        self.assertIn("escalated=1", proc.stdout)
        self.assertEqual(os.readlink(self.deployed / "cur.py"), str(self.scripts / "cur.py"))
        self.assertEqual(os.readlink(self.deployed / "conv.py"), str(self.scripts / "conv.py"))
        self.assertFalse((self.deployed / "ghost.py").exists())

    def test_other_entry_type_escalates(self):
        self.write_manifest("dir_entry.py")
        (self.deployed / "dir_entry.py").mkdir()
        self.put_canonical("dir_entry.py", "canonical bytes\n", commit=True)
        proc = self.run_sync()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("sync: dir_entry.py: escalated", proc.stdout)
        self.assertIn("unsupported deployed entry type", proc.stdout)
        self.assertTrue((self.deployed / "dir_entry.py").is_dir())

    def test_through_symlink_invocation_resolves_scratch_canonical(self):
        alias_dir = Path(self._tmp.name) / "alias"
        alias_dir.mkdir()
        alias = alias_dir / "sync_via_link.sh"
        os.symlink(str(self.scripts / "sync_runtime_scripts.sh"), str(alias))
        # probe name absent from the real canonical scripts dir on purpose: a
        # run that resolved the real repo would escalate absent-both instead.
        self.write_manifest("through_link_probe.py")
        self.put_canonical("through_link_probe.py", "scratch canonical bytes\n", commit=True)
        self.put_deployed_regular("through_link_probe.py", "drifted bytes\n")
        proc = self.run_sync(script_path=alias)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("sync: through_link_probe.py: converted", proc.stdout)
        self.assertEqual(
            os.readlink(self.deployed / "through_link_probe.py"),
            str(self.scripts / "through_link_probe.py"),
        )

    def test_manifest_file_missing_escalates(self):
        proc = self.run_sync()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("manifest file missing", proc.stdout)
        self.assertEqual(os.listdir(self.deployed), [])

    def test_manifest_file_empty_escalates(self):
        (self.scripts / "runtime-scripts.list").write_text("")
        proc = self.run_sync()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("zero inventory entries", proc.stdout)
        self.assertEqual(os.listdir(self.deployed), [])

    def test_manifest_file_all_comments_escalates(self):
        (self.scripts / "runtime-scripts.list").write_text(
            "# comment one\n\n# comment two\n")
        proc = self.run_sync()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("zero inventory entries", proc.stdout)
        self.assertEqual(os.listdir(self.deployed), [])

    @unittest.skipIf(os.geteuid() == 0, "root reads anything")
    def test_manifest_file_unreadable_escalates(self):
        manifest = self.scripts / "runtime-scripts.list"
        manifest.write_text("probe_a.py\n")
        os.chmod(manifest, 0o000)
        self.addCleanup(os.chmod, manifest, 0o644)
        proc = self.run_sync()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("not readable", proc.stdout)
        self.assertEqual(os.listdir(self.deployed), [])

    def test_bak_dangling_symlink_refused(self):
        dangling_target = self.deployed / "gone-target.txt"
        self.write_manifest("probe_a.py")
        self.put_canonical("probe_a.py", "canonical bytes\n", commit=True)
        self.put_deployed_regular("probe_a.py", "deployed bytes\n")
        os.symlink(str(dangling_target), str(self.deployed / f"probe_a.py.bak-{self.today}"))
        proc = self.run_sync()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("sync: probe_a.py: escalated", proc.stdout)
        self.assertIn("already exists", proc.stdout)
        self.assertEqual((self.deployed / "probe_a.py").read_text(), "deployed bytes\n")
        self.assertTrue(os.path.islink(self.deployed / f"probe_a.py.bak-{self.today}"))
        self.assertEqual(os.readlink(self.deployed / f"probe_a.py.bak-{self.today}"), str(dangling_target))

    def test_second_run_idempotent(self):
        self.write_manifest("probe_a.py", "probe_b.sh")
        self.put_canonical("probe_a.py", "a bytes\n", commit=True)
        self.put_canonical("probe_b.sh", "b bytes\n", commit=True)
        self.put_deployed_regular("probe_b.sh", "b drifted\n")
        first = self.run_sync()
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertIn("sync: probe_a.py: installed", first.stdout)
        self.assertIn("sync: probe_b.sh: converted", first.stdout)
        before = self.snapshot()
        second = self.run_sync()
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertIn("sync: probe_a.py: current", second.stdout)
        self.assertIn("sync: probe_b.sh: current", second.stdout)
        self.assertEqual(self.snapshot(), before)

    def test_deployed_root_missing_escalates(self):
        self.write_manifest("probe_a.py")
        self.put_canonical("probe_a.py", "canonical bytes\n", commit=True)
        proc = self.run_sync(deployed_root=Path(self._tmp.name) / "nope")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("deployed root is not a directory", proc.stdout)
        self.assertEqual(os.listdir(self.deployed), [])

    def test_deployed_root_inside_canonical_escalates(self):
        self.write_manifest("probe_a.py")
        self.put_canonical("probe_a.py", "canonical bytes\n", commit=True)
        proc = self.run_sync(deployed_root=self.scripts)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("deployed root resolves inside the canonical scripts directory", proc.stdout)
        self.assertEqual(os.listdir(self.deployed), [])


if __name__ == "__main__":
    unittest.main(verbosity=1)
