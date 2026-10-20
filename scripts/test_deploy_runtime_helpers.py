"""Contract tests for scripts/deploy_runtime_helpers.sh (the runtime-helper
deployment carrier) and scripts/verify_runtime_deployment.py (the post-walk
deployment verifier).

The carrier deploys every name the canonical repo's scripts/runtime-scripts.list
admits from the resolved canonical repo into the runtime home (default
~/.ai-playbook/scripts), converting lagging regular-file copies into symlinks
with a .bak-<UTC date> sibling. After the walk the carrier runs the verifier
beside its own realpath: a closure diff plus a no-PYTHONPATH import probe over
materialized deployed bytes. Every fixture drives the real carrier through
subprocess with a temp --home, so the tests never touch the real runtime home.
"""

import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
CARRIER = SCRIPTS_DIR / "deploy_runtime_helpers.sh"
VERIFIER = SCRIPTS_DIR / "verify_runtime_deployment.py"

# Fixture stub bytes: valid Python importing one stdlib module, so the
# verifier's probe exercises its stdlib carve-out and fixture entries probe
# clean unless a fixture wires a real violation.
STUB_TEMPLATE = (
    "import textwrap\n"
    "LABEL = %(label)r\n"
    "def label(width=72):\n"
    "    return textwrap.fill(LABEL, width)\n"
)


def stub_bytes(name):
    return STUB_TEMPLATE % {"label": name}


def run_carrier(*args, cwd=None):
    """Invoke the carrier script in a subprocess and return the result."""
    return subprocess.run(
        ["bash", str(CARRIER), *[str(a) for a in args]],
        cwd=str(cwd) if cwd is not None else None,
        capture_output=True,
        text=True,
    )


def run_verifier(*args, cwd=None):
    """Invoke the deployment verifier in a subprocess and return the result."""
    return subprocess.run(
        [sys.executable, str(VERIFIER), *[str(a) for a in args]],
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


def assert_outcome(proc, outcome, code):
    """Exactly one final OUTCOME line matching the outcome and the exit code."""
    assert proc.returncode == code, "rc=%s stdout=%s stderr=%s" % (
        proc.returncode,
        proc.stdout,
        proc.stderr,
    )
    lines = proc.stdout.strip().splitlines()
    outcome_lines = [line for line in lines if line.startswith("OUTCOME:")]
    assert outcome_lines == ["OUTCOME: %s" % outcome], proc.stdout


def violation_names(proc, klass):
    """The named subjects of the verifier's verify-<klass> evidence lines."""
    prefix = "verify-%s:" % klass
    return sorted(
        line[len(prefix):].split(":")[0].strip()
        for line in proc.stdout.splitlines()
        if line.startswith(prefix)
    )


class DeployRuntimeHelpersTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="deploy-runtime-helpers-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    # -- fixture helpers ---------------------------------------------------

    def make_canonical(self, names):
        """A temp canonical repo: scripts/<name> importable stubs + the manifest."""
        canonical = self.tmp / "canonical"
        (canonical / "scripts").mkdir(parents=True)
        for name in names:
            (canonical / "scripts" / name).write_text(stub_bytes(name))
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
        # fresh.py is current and probed clean, so no line names it
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
        (checkout / "scripts" / "local_helper.py").write_text(stub_bytes("local_helper.py"))
        (checkout / "scripts" / "second.py").write_text(stub_bytes("second.py"))
        self.write_manifest(checkout, ["local_helper.py", "second.py"])
        subprocess.run(
            ["git", "init", "-q", str(checkout)], check=True, capture_output=True
        )
        elsewhere = self.tmp / "elsewhere"
        (elsewhere / "scripts").mkdir(parents=True)
        (elsewhere / "scripts" / "decoy.py").write_text(stub_bytes("decoy.py"))
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
            "--check", "--repo", empty, "--home", runtime, cwd=self.tmp
        )
        assert_pass(proc)
        self.assertIn("advisory", proc.stdout)
        self.assertIn("skipped", proc.stdout)

    def test_prefixed_manifest_entry_maps_to_basename_and_stale_variants_flip(self):
        canonical = self.tmp / "canonical"
        (canonical / "scripts").mkdir(parents=True)
        for name in ("prefixed.py", "aimer.py", "collider.py"):
            (canonical / "scripts" / name).write_text(stub_bytes(name))
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
        # Deploy mode: the walk still prints the existing skip line and creates
        # nothing, and the post-walk verifier converts the hole into a refusal
        # naming the entry's unrunnable import probe (remedy restore-or-drop).
        proc = run_carrier("--repo", canonical, "--home", runtime, cwd=self.tmp)
        assert_outcome(proc, "fail", 1)
        self.assertTrue(
            any(
                line.startswith("skip:") and "ghost.py" in line
                for line in proc.stdout.splitlines()
            ),
            proc.stdout,
        )
        self.assertIn("verify-canonical-missing: ghost.py", proc.stdout)
        self.assertIn("restore the canonical file or drop the manifest line", proc.stdout)
        self.assertFalse((runtime / "ghost.py").exists())
        self.assertFalse((runtime / "ghost.py").is_symlink())
        self.assertEqual(list(runtime.glob("ghost.py.bak-*")), [])
        # The refusal is post-walk: the admitted real entry was linked first.
        self.assertTrue((runtime / "real.py").is_symlink())

    # -- deployment verification: the eight pinned checks -------------------

    def test_closure_gap_refusal_names_member_and_is_post_walk(self):
        canonical = self.make_canonical(["b_sibling.py"])
        (canonical / "scripts" / "a_entry.py").write_text("import b_sibling\n")
        self.write_manifest(canonical, ["a_entry.py"])
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        proc = run_carrier("--repo", canonical, "--home", runtime, cwd=self.tmp)
        assert_outcome(proc, "fail", 1)
        self.assertIn("verify-closure-gap: b_sibling.py", proc.stdout)
        self.assertIn("runtime-scripts.list", proc.stdout)
        # Post-walk: the admitted entrypoint was linked before the refusal.
        self.assertTrue((runtime / "a_entry.py").is_symlink(), proc.stdout)
        self.assertEqual(
            os.path.realpath(runtime / "a_entry.py"),
            os.path.realpath(canonical / "scripts" / "a_entry.py"),
        )

    def test_depth2_fixture_names_exactly_the_closure_members(self):
        canonical = self.make_canonical(["depth_c.py", "bystander.py"])
        (canonical / "scripts" / "depth_a.py").write_text("import depth_b\n")
        (canonical / "scripts" / "depth_b.py").write_text("import depth_c\n")
        self.write_manifest(canonical, ["depth_a.py"])
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        proc = run_carrier("--repo", canonical, "--home", runtime, cwd=self.tmp)
        assert_outcome(proc, "fail", 1)
        self.assertEqual(
            violation_names(proc, "closure-gap"), ["depth_b.py", "depth_c.py"],
            proc.stdout,
        )
        self.assertEqual(
            violation_names(proc, "probe-fail"), ["depth_a.py"], proc.stdout
        )
        self.assertNotIn("bystander", proc.stdout)
        proc = run_carrier(
            "--check", "--repo", canonical, "--home", runtime, cwd=self.tmp
        )
        assert_outcome(proc, "pass", 0)
        self.assertEqual(
            violation_names(proc, "closure-gap"), ["depth_b.py", "depth_c.py"],
            proc.stdout,
        )
        self.assertEqual(
            violation_names(proc, "probe-fail"), ["depth_a.py"], proc.stdout
        )
        self.assertNotIn("bystander", proc.stdout)

    def test_function_level_import_is_scanned(self):
        canonical = self.make_canonical(["hidden_sibling.py"])
        (canonical / "scripts" / "func_body.py").write_text(
            "import textwrap\n"
            "def loader():\n"
            "    import hidden_sibling\n"
            "    return textwrap.fill(hidden_sibling.LABEL)\n"
        )
        self.write_manifest(canonical, ["func_body.py"])
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        proc = run_carrier("--repo", canonical, "--home", runtime, cwd=self.tmp)
        assert_outcome(proc, "fail", 1)
        self.assertEqual(
            violation_names(proc, "closure-gap"), ["hidden_sibling.py"], proc.stdout
        )
        # The entrypoint itself imports clean; only the closure gap refuses.
        self.assertEqual(violation_names(proc, "probe-fail"), [], proc.stdout)

    def test_local_sibling_shadowing_a_stdlib_name_is_a_closure_gap(self):
        """Existence alone gates the closure scan: an unadmitted local sibling
        named like a stdlib module is a closure gap, and it is the sole
        violation because the probe child's stdlib carve-out resolves the
        import to the real stdlib module, so the entry probes clean."""
        canonical = self.make_canonical(["shadower.py"])
        (canonical / "scripts" / "shadower.py").write_text("import dataclasses\n")
        (canonical / "scripts" / "dataclasses.py").write_text(
            stub_bytes("dataclasses.py")
        )
        self.write_manifest(canonical, ["shadower.py"])
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        (runtime / "shadower.py").symlink_to(canonical / "scripts" / "shadower.py")
        proc = run_verifier(
            "--repo", canonical, "--home", runtime, "--mode", "deploy"
        )
        assert_outcome(proc, "fail", 1)
        self.assertIn("verify-closure-gap: dataclasses.py", proc.stdout)
        self.assertEqual(
            violation_names(proc, "closure-gap"), ["dataclasses.py"], proc.stdout
        )
        self.assertEqual(violation_names(proc, "probe-fail"), [], proc.stdout)

    def test_check_mode_advises_one_converging_remedy_per_violation(self):
        canonical = self.make_canonical(["b_side.py", "loner.py"])
        (canonical / "scripts" / "a_lead.py").write_text("import b_side\n")
        self.write_manifest(canonical, ["a_lead.py", "loner.py", "ghost.py"])
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        (runtime / "a_lead.py").symlink_to(canonical / "scripts" / "a_lead.py")
        proc = run_carrier(
            "--check", "--repo", canonical, "--home", runtime, cwd=self.tmp
        )
        assert_outcome(proc, "pass", 0)
        # One advisory per violation: closure gap, canonical-missing,
        # home-absent, import failure, each naming its converging remedy.
        self.assertEqual(
            violation_names(proc, "closure-gap"), ["b_side.py"], proc.stdout
        )
        self.assertIn(
            "verify-closure-gap: b_side.py: a local sibling the admitted entries import is not admitted (remedy: admit it in scripts/runtime-scripts.list and redeploy)",
            proc.stdout,
        )
        self.assertEqual(
            violation_names(proc, "canonical-missing"), ["ghost.py"], proc.stdout
        )
        self.assertIn(
            "restore the canonical file or drop the manifest line", proc.stdout
        )
        self.assertEqual(
            violation_names(proc, "home-absent"), ["loner.py"], proc.stdout
        )
        self.assertIn("deploy_runtime_helpers.sh", proc.stdout)
        self.assertEqual(
            violation_names(proc, "probe-fail"), ["a_lead.py"], proc.stdout
        )
        self.assertIn("park for the operator", proc.stdout)
        self.assertNotIn("b_side.py", "".join(violation_names(proc, "probe-fail")))

    def test_unparseable_entrypoint_is_named(self):
        canonical = self.make_canonical([])
        (canonical / "scripts" / "broken_ep.py").write_text("def :(\n")
        self.write_manifest(canonical, ["broken_ep.py"])
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        proc = run_carrier("--repo", canonical, "--home", runtime, cwd=self.tmp)
        assert_outcome(proc, "fail", 1)
        self.assertIn("verify-unparseable: scripts/broken_ep.py", proc.stdout)
        self.assertIn(
            "verify-probe-fail: broken_ep.py", proc.stdout
        )
        proc = run_carrier(
            "--check", "--repo", canonical, "--home", runtime, cwd=self.tmp
        )
        assert_outcome(proc, "pass", 0)
        self.assertIn("verify-unparseable: scripts/broken_ep.py", proc.stdout)
        self.assertIn(
            "verify-probe-fail: broken_ep.py", proc.stdout
        )

    def test_unadmitted_broken_sibling_remedy_is_restore_only(self):
        """An unadmitted sibling has no manifest line to drop: its unparseable
        verdict carries the restore-only remedy, in check mode too."""
        canonical = self.make_canonical([])
        (canonical / "scripts" / "needs_broken.py").write_text("import broken_sib\n")
        (canonical / "scripts" / "broken_sib.py").write_text("def :(\n")
        self.write_manifest(canonical, ["needs_broken.py"])
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        proc = run_verifier(
            "--repo", canonical, "--home", runtime, "--mode", "check"
        )
        assert_outcome(proc, "pass", 0)
        self.assertIn(
            "verify-unparseable: scripts/broken_sib.py: canonical bytes do not"
            " parse (remedy: restore the canonical file)",
            proc.stdout,
        )
        self.assertNotIn("drop its manifest line", proc.stdout)

    def test_unreadable_entrypoint_is_named(self):
        if os.geteuid() == 0:
            self.skipTest(
                "read-bypassing privileges: an unreadable file is readable, the variant cannot fire"
            )
        canonical = self.make_canonical(["locked_ep.py"])
        (canonical / "scripts" / "locked_ep.py").chmod(0)
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        proc = run_carrier("--repo", canonical, "--home", runtime, cwd=self.tmp)
        assert_outcome(proc, "fail", 1)
        self.assertIn("verify-unreadable: scripts/locked_ep.py", proc.stdout)
        # The probe-root copy reads the verified canonical realpath, so a
        # copyfile OSError is the unreadable class with the restore-or-drop
        # remedy, not a probe failure.
        self.assertIn("verify-unreadable: locked_ep.py", proc.stdout)
        proc = run_carrier(
            "--check", "--repo", canonical, "--home", runtime, cwd=self.tmp
        )
        assert_outcome(proc, "pass", 0)
        self.assertIn("verify-unreadable: scripts/locked_ep.py", proc.stdout)

    def test_out_of_root_import_fails_the_probe(self):
        outside = self.tmp / "outside"
        outside.mkdir()
        (outside / "outside_helper.py").write_text("VALUE = 1\n")
        canonical = self.make_canonical([])
        (canonical / "scripts" / "evictor.py").write_text(
            "import sys\n"
            "sys.path.insert(0, r'%s')\n"
            "import outside_helper\n" % outside
        )
        self.write_manifest(canonical, ["evictor.py"])
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        proc = run_carrier("--repo", canonical, "--home", runtime, cwd=self.tmp)
        assert_outcome(proc, "fail", 1)
        # The provenance assertion fires: the entry and the offending module
        # path are named, and the out-of-root helper is not a local closure gap.
        self.assertIn("verify-probe-fail: evictor.py", proc.stdout)
        self.assertIn("outside_helper", proc.stdout)
        self.assertEqual(violation_names(proc, "closure-gap"), [], proc.stdout)

    def test_one_refusal_names_gap_and_import_failure_together(self):
        canonical = self.make_canonical(["gap_sib.py"])
        (canonical / "scripts" / "worker.py").write_text("import gap_sib\n")
        self.write_manifest(canonical, ["worker.py", "ghost_ep.py"])
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        proc = run_carrier("--repo", canonical, "--home", runtime, cwd=self.tmp)
        assert_outcome(proc, "fail", 1)
        self.assertIn("verify-closure-gap: gap_sib.py", proc.stdout)
        self.assertIn("verify-canonical-missing: ghost_ep.py", proc.stdout)

    # -- probe provenance: canonical-first classification --------------------

    def test_stale_regular_file_copy_is_named_not_canonical_and_never_executed(self):
        """Provenance witness: a home regular-file copy of an admitted name is
        never copied into the probe root nor executed, even though its bytes
        would run and fail; the verifier names not-canonical instead (verifier
        deploy mode refuses, check mode advises, exit 0)."""
        canonical = self.make_canonical(["stale_guard.py"])
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        marker = self.tmp / "probe-marker.txt"
        (runtime / "stale_guard.py").write_text(
            "import sys\n"
            "open(%r, 'w').write('executed')\n"
            "sys.exit(3)\n" % str(marker)
        )
        proc = run_verifier(
            "--repo", canonical, "--home", runtime, "--mode", "deploy"
        )
        assert_outcome(proc, "fail", 1)
        self.assertIn("verify-not-canonical: stale_guard.py", proc.stdout)
        self.assertIn(
            "run the deploy run from the primary checkout or remove the foreign file",
            proc.stdout,
        )
        self.assertIn("0 entrypoints probed", proc.stdout)
        self.assertFalse(marker.exists(), "the stale bytes were executed")
        proc = run_verifier(
            "--repo", canonical, "--home", runtime, "--mode", "check"
        )
        assert_outcome(proc, "pass", 0)
        self.assertIn("verify-not-canonical: stale_guard.py", proc.stdout)
        self.assertIn(
            "run the deploy run from the primary checkout or remove the foreign file",
            proc.stdout,
        )
        self.assertFalse(marker.exists(), "the stale bytes were executed")

    def test_symlink_aimed_outside_canonical_is_not_canonical_and_decoy_never_runs(self):
        """Containment witness: a home entry that is a symlink aimed at a
        regular file outside the canonical repo is named not-canonical, the
        verifier probes nothing, and the decoy bytes are never executed."""
        canonical = self.make_canonical(["linkout.py"])
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        decoy = self.tmp / "outside-decoy.py"
        marker = self.tmp / "decoy-marker.txt"
        decoy.write_text(
            "import sys\n"
            "open(%r, 'w').write('executed')\n"
            "sys.exit(3)\n" % str(marker)
        )
        (runtime / "linkout.py").symlink_to(decoy)
        proc = run_verifier(
            "--repo", canonical, "--home", runtime, "--mode", "deploy"
        )
        assert_outcome(proc, "fail", 1)
        self.assertIn("verify-not-canonical: linkout.py", proc.stdout)
        self.assertIn("0 entrypoints probed", proc.stdout)
        self.assertFalse(marker.exists(), "the decoy bytes were executed")

    def test_canonical_deleted_home_stale_copy_refuses_canonical_missing(self):
        """Canonical-first classification: with the canonical admitted file
        deleted and a stale copy left in the home, the deploy run refuses
        naming canonical-missing and never executes the home bytes."""
        canonical = self.make_canonical(["gone_canon.py"])
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        (runtime / "gone_canon.py").write_text("stale bytes\n")
        (canonical / "scripts" / "gone_canon.py").unlink()
        proc = run_carrier("--repo", canonical, "--home", runtime, cwd=self.tmp)
        assert_outcome(proc, "fail", 1)
        self.assertIn("skip: gone_canon.py", proc.stdout)
        self.assertIn("verify-canonical-missing: gone_canon.py", proc.stdout)
        # Canonical-first precedence: no not-canonical line, and the stale
        # home bytes were never copied or probed.
        self.assertNotIn("verify-not-canonical", proc.stdout)
        self.assertNotIn("verify-probe-fail", proc.stdout)
        self.assertIn("0 entrypoints probed", proc.stdout)
        self.assertEqual((runtime / "gone_canon.py").read_text(), "stale bytes\n")

    def test_deployer_without_adjacent_verifier_refuses_deploy_and_advises_check(self):
        """A deployer copy with no verifier beside its own realpath never
        skip-and-passes: deploy mode refuses, check mode prints one
        skipped-verification advisory and keeps its report-only contract."""
        lone_dir = self.tmp / "lone-deployer"
        lone_dir.mkdir()
        lone = lone_dir / "deploy_runtime_helpers.sh"
        shutil.copyfile(CARRIER, lone)
        canonical = self.make_canonical(["solo.py"])
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        proc = run_carrier("--repo", canonical, "--home", runtime, cwd=self.tmp)
        # Sanity: beside the real carrier the verifier resolves and passes.
        assert_pass(proc)
        proc = subprocess.run(
            ["bash", str(lone), "--repo", str(canonical), "--home", str(runtime)],
            cwd=str(self.tmp),
            capture_output=True,
            text=True,
        )
        assert_outcome(proc, "fail", 1)
        self.assertIn("no verify_runtime_deployment.py beside the deployer", proc.stdout)
        proc = subprocess.run(
            [
                "bash", str(lone),
                "--check", "--repo", str(canonical), "--home", str(runtime),
            ],
            cwd=str(self.tmp),
            capture_output=True,
            text=True,
        )
        assert_outcome(proc, "pass", 0)
        self.assertIn("advisory: deployment verification skipped", proc.stdout)

    # -- witnesses -----------------------------------------------------------

    def test_real_repo_deploys_and_verifies_clean(self):
        """Behavior witness: this worktree's canonical repo deploys into a temp
        home and every admitted .py entry imports clean under the verifier;
        .sh admissions are deployed but never probed."""
        repo_root = SCRIPTS_DIR.parent
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        proc = run_carrier("--repo", repo_root, "--home", runtime, cwd=self.tmp)
        assert_pass(proc)
        self.assertTrue((runtime / "done_sweep_gates.sh").is_symlink(), proc.stdout)
        proc = run_verifier(
            "--repo", repo_root, "--home", runtime, "--mode", "deploy"
        )
        assert_outcome(proc, "pass", 0)
        self.assertNotIn("verify-closure-gap", proc.stdout)
        self.assertNotIn("verify-probe-fail", proc.stdout)
        self.assertNotIn("verify-home-absent", proc.stdout)
        summary = next(
            line
            for line in proc.stdout.splitlines()
            if line.startswith("verification:")
        )
        match = re.match(
            r"verification: (\d+) manifest entries,"
            r" (\d+) entrypoints probed with .* \(python ([0-9.]+)\),"
            r" (\d+) violation",
            summary,
        )
        self.assertIsNotNone(match, summary)
        entries, probed, version, violations = match.groups()
        self.assertGreaterEqual(int(probed), 40, summary)
        self.assertLess(int(probed), int(entries), summary)
        self.assertEqual(violations, "0", summary)
        self.assertTrue(version, summary)

    def test_full_closure_repo_deploys_and_home_imports_clean(self):
        """Integration witness: a temp canonical repo whose manifest admits
        the full transitive closure deploys every admitted name, ends
        OUTCOME: pass, and the temp home alone imports each admitted .py
        entry (per-entry import against the home, no source-tree path
        channels); a .sh admission deploys but stays outside the probe, and
        an unadmitted unimported bystander is never deployed."""
        canonical = self.tmp / "canonical"
        (canonical / "scripts").mkdir(parents=True)
        (canonical / "scripts" / "leaf.py").write_text(stub_bytes("leaf.py"))
        (canonical / "scripts" / "mid.py").write_text(
            "import textwrap\n"
            "def render():\n"
            "    import leaf\n"
            "    return textwrap.fill(leaf.LABEL)\n"
        )
        (canonical / "scripts" / "top.py").write_text("import mid\n")
        (canonical / "scripts" / "solo.py").write_text(stub_bytes("solo.py"))
        (canonical / "scripts" / "run.sh").write_text(
            "#!/usr/bin/env bash\nexit 0\n"
        )
        (canonical / "scripts" / "bystander.py").write_text(
            stub_bytes("bystander.py")
        )
        admitted = ["top.py", "mid.py", "leaf.py", "solo.py", "run.sh"]
        # A duplicated admission line must not double-probe: leaf.py rides
        # twice in the manifest, and the summary regex below still pins exactly
        # 5 manifest entries and 4 probed entrypoints.
        self.write_manifest(canonical, admitted + ["leaf.py"])
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        proc = run_carrier("--repo", canonical, "--home", runtime, cwd=self.tmp)
        assert_pass(proc)
        for name in admitted:
            link = runtime / name
            self.assertTrue(link.is_symlink(), proc.stdout)
            self.assertEqual(
                os.path.realpath(link),
                os.path.realpath(canonical / "scripts" / name),
            )
        self.assertFalse((runtime / "bystander.py").exists())
        self.assertNotIn("verify-", proc.stdout)
        summary = next(
            line
            for line in proc.stdout.splitlines()
            if line.startswith("verification:")
        )
        match = re.match(
            r"verification: 5 manifest entries,"
            r" 4 entrypoints probed with .* \(python ([0-9.]+)\),"
            r" 0 violation",
            summary,
        )
        self.assertIsNotNone(match, proc.stdout)
        # Per-entry import verification against the temp home alone.
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        for name in ("top.py", "mid.py", "leaf.py", "solo.py"):
            proc = subprocess.run(
                [
                    sys.executable, "-I", "-S", "-B", "-c",
                    "import importlib, sys; sys.path.insert(0, sys.argv[1]);"
                    " importlib.import_module(sys.argv[2])",
                    str(runtime), name[:-3],
                ],
                cwd=str(self.tmp),
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                proc.returncode,
                0,
                "%s: %s%s" % (name, proc.stdout, proc.stderr),
            )

    def test_self_heal_does_not_rescue_a_hole_home(self):
        """Safety witness: a home where only plan_readiness.py is linked and
        runtime_capabilities.py is missing fails the probe despite the
        module's own sys.path self-heal (the idiom at scripts/plan_readiness.py
        line 56), and the closure scan names the omission."""
        canonical = self.make_canonical(["runtime_capabilities.py"])
        (canonical / "scripts" / "plan_readiness.py").write_text(
            "import sys\n"
            "from pathlib import Path\n"
            "sys.path.insert(0, str(Path(__file__).resolve().parent))\n"
            "import runtime_capabilities\n"
        )
        self.write_manifest(canonical, ["plan_readiness.py"])
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        proc = run_carrier("--repo", canonical, "--home", runtime, cwd=self.tmp)
        # The setup deploy itself refuses (the manifest deliberately omits the
        # sibling), but the walk has already linked plan_readiness.py: the home
        # under verification carries exactly that one entry.
        assert_outcome(proc, "fail", 1)
        self.assertTrue((runtime / "plan_readiness.py").is_symlink(), proc.stdout)
        self.assertFalse((runtime / "runtime_capabilities.py").exists())
        # Standalone deploy mode: one refusal names the gap and the probe failure.
        proc = run_verifier(
            "--repo", canonical, "--home", runtime, "--mode", "deploy"
        )
        assert_outcome(proc, "fail", 1)
        self.assertIn(
            "verify-closure-gap: runtime_capabilities.py", proc.stdout
        )
        self.assertIn("verify-probe-fail: plan_readiness.py", proc.stdout)
        # Check mode: the same findings as advisories, exit 0.
        proc = run_carrier(
            "--check", "--repo", canonical, "--home", runtime, cwd=self.tmp
        )
        assert_outcome(proc, "pass", 0)
        self.assertIn(
            "verify-closure-gap: runtime_capabilities.py", proc.stdout
        )
        self.assertIn("verify-probe-fail: plan_readiness.py", proc.stdout)

    def test_invocation_from_inside_canonical_scripts_cannot_false_green(self):
        """Safety witness: the probe child's cwd is the probe root, so invoking
        the deployer from inside the canonical scripts directory cannot make an
        unadmitted sibling importable; the deploy refusal stands."""
        canonical = self.tmp / "canonical"
        (canonical / "scripts").mkdir(parents=True)
        (canonical / "scripts" / "selflinked.py").write_text("import unattendant\n")
        (canonical / "scripts" / "unattendant.py").write_text(
            stub_bytes("unattendant.py")
        )
        self.write_manifest(canonical, ["selflinked.py"])
        subprocess.run(
            ["git", "init", "-q", str(canonical)], check=True, capture_output=True
        )
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        proc = run_carrier("--home", runtime, cwd=canonical / "scripts")
        assert_outcome(proc, "fail", 1)
        self.assertIn("verify-closure-gap: unattendant.py", proc.stdout)
        self.assertIn("verify-probe-fail: selflinked.py", proc.stdout)
        self.assertNotIn("OUTCOME: pass", proc.stdout)

    def test_parent_parent_scripts_loader_probes_clean(self):
        """Safety witness: an admitted entry loading a sibling through a
        Path(__file__).resolve().parent.parent / 'scripts' loader imports
        cleanly, because probe-root/scripts makes parent.parent/scripts resolve
        to the probe root itself."""
        canonical = self.make_canonical(["loaded_sibling.py"])
        (canonical / "scripts" / "pparent_loader.py").write_text(
            "import sys\n"
            "from pathlib import Path\n"
            "sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))\n"
            "import loaded_sibling\n"
        )
        self.write_manifest(canonical, ["pparent_loader.py", "loaded_sibling.py"])
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        proc = run_carrier("--repo", canonical, "--home", runtime, cwd=self.tmp)
        assert_pass(proc)
        proc = run_verifier(
            "--repo", canonical, "--home", runtime, "--mode", "deploy"
        )
        assert_outcome(proc, "pass", 0)
        self.assertEqual(violation_names(proc, "probe-fail"), [], proc.stdout)
        self.assertEqual(violation_names(proc, "closure-gap"), [], proc.stdout)


if __name__ == "__main__":
    unittest.main()
