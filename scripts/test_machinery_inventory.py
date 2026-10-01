#!/usr/bin/env python3
"""Hermetic suite for the machinery inventory: a scratch git tree carrying a
tracked-layout fixture, each check arm mutated one at a time."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parent / "machinery_inventory.py"

SKILL_FIXTURE = """# Skill

## State file

Path: `.ai-playbook/scheduler-state.json`.

`alpha_field` is the top-level alpha.
`beta_field` is the rolling beta.
`ok` is too short to count.

## Invariants

Keep going.
"""


def run(args, cwd):
    return subprocess.run([sys.executable, str(SCRIPT)] + args,
                          capture_output=True, text=True, cwd=cwd)


class MachineryInventoryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="machinery-inv-test-"))
        self.repo = self.tmp / "tree"
        (self.repo / "scripts").mkdir(parents=True)
        (self.repo / "agents" / "hooks" / "my-hook").mkdir(parents=True)
        (self.repo / "agents" / "skills").mkdir(parents=True)
        (self.repo / "scripts" / "registered_tool.py").write_text("# registered\n")
        (self.repo / "scripts" / "unregistered_tool.py").write_text("# regrowth\n")
        (self.repo / "scripts" / "test_registered_tool.py").write_text("# test\n")
        (self.repo / "agents" / "hooks" / "my-hook" / "hook.sh").write_text("#!/bin/sh\n")
        (self.repo / "agents" / "skills" / "SKILL.md").write_text(SKILL_FIXTURE)
        subprocess.run(["git", "init", "-q"], cwd=self.repo)
        subprocess.run(["git", "add", "-A"], cwd=self.repo)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                        "commit", "-qm", "fixture"], cwd=self.repo)
        self.copy_script()
        # Scaffold, then disposition into a clean keep set.
        out = run(["--scaffold", "--repo-root", str(self.repo),
                   "--skill-path", "agents/skills/SKILL.md"], cwd=self.repo)
        self.assertEqual(out.returncode, 0, out.stderr)
        reg = json.loads((self.repo / "scripts" / "machinery_registry.json").read_text())
        ids = {e["id"] for e in reg["entries"]}
        self.assertIn("script:registered_tool.py", ids)
        self.assertIn("script:unregistered_tool.py", ids)
        self.assertIn("hook:my-hook", ids)
        self.assertIn("state-field:alpha_field", ids)
        self.assertIn("state-field:beta_field", ids)
        self.assertNotIn("state-field:ok", ids)
        # Disposition: keep everything with a resolving witness.
        for entry in reg["entries"]:
            entry["disposition"] = "keep"
            if entry["kind"] == "state-field":
                entry["witness"] = {"class": "user-decision",
                                    "ref": "agents/skills/SKILL.md"}
            else:
                entry["witness"] = {"class": "red-test",
                                    "ref": "scripts/test_registered_tool.py"}
        (self.repo / "scripts" / "machinery_registry.json").write_text(json.dumps(reg))
        subprocess.run(["git", "add", "-A"], cwd=self.repo)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def copy_script(self):
        shutil.copy(SCRIPT, self.repo / "scripts" / "machinery_inventory.py")
        subprocess.run(["git", "add", "-A"], cwd=self.repo)

    def write_registry(self, mutate):
        reg = json.loads((self.repo / "scripts" / "machinery_registry.json").read_text())
        mutate(reg)
        (self.repo / "scripts" / "machinery_registry.json").write_text(json.dumps(reg))

    def test_clean_registry_checks_green(self):
        out = run(["--check", "--repo-root", str(self.repo),
                          "--skill-path", "agents/skills/SKILL.md"], cwd=self.repo)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)

    def test_scaffold_generates_rows_for_all_sources(self):
        reg = json.loads((self.repo / "scripts" / "machinery_registry.json").read_text())
        kinds = {e["kind"] for e in reg["entries"]}
        self.assertLessEqual({"script", "hook", "state-field"}, kinds)

    def test_unregistered_script_fails(self):
        self.write_registry(lambda r: r["entries"].pop(0))  # script:machinery_inventory.py
        out = run(["--check", "--repo-root", str(self.repo),
                          "--skill-path", "agents/skills/SKILL.md"], cwd=self.repo)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("unregistered script file", out.stdout)

    def test_keep_with_missing_ref_fails(self):
        def mutate(reg):
            reg["entries"][0]["witness"]["ref"] = "scripts/no_such_test.py"
        self.write_registry(mutate)
        out = run(["--check", "--repo-root", str(self.repo),
                          "--skill-path", "agents/skills/SKILL.md"], cwd=self.repo)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("does not resolve", out.stdout)

    def test_keep_with_untracked_ref_fails(self):
        # A ref that exists on disk but is untracked must fail (worktree
        # independence: only tracked paths count).
        (self.repo / "scripts" / "untracked_note.md").write_text("x\n")
        def mutate(reg):
            reg["entries"][0]["witness"] = {"class": "incident",
                                            "ref": "scripts/untracked_note.md"}
        self.write_registry(mutate)
        out = run(["--check", "--repo-root", str(self.repo),
                          "--skill-path", "agents/skills/SKILL.md"], cwd=self.repo)
        self.assertNotEqual(out.returncode, 0)

    def test_keep_with_class_none_fails(self):
        def mutate(reg):
            reg["entries"][0]["witness"] = {"class": "none", "ref": None}
        self.write_registry(mutate)
        out = run(["--check", "--repo-root", str(self.repo),
                          "--skill-path", "agents/skills/SKILL.md"], cwd=self.repo)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("witness class none", out.stdout)

    def test_delete_without_note_fails(self):
        def mutate(reg):
            entry = reg["entries"][0]
            entry["disposition"] = "delete"
            entry["paths"] = []  # not tracked as existing any more
        self.write_registry(mutate)
        out = run(["--check", "--repo-root", str(self.repo),
                          "--skill-path", "agents/skills/SKILL.md"], cwd=self.repo)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("delete row without a note", out.stdout)

    def test_duplicate_id_fails(self):
        def mutate(reg):
            twin = dict(reg["entries"][0])
            reg["entries"].append(twin)
        self.write_registry(mutate)
        out = run(["--check", "--repo-root", str(self.repo),
                          "--skill-path", "agents/skills/SKILL.md"], cwd=self.repo)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("duplicate id", out.stdout)

    def test_removals_row_with_existing_path_fails(self):
        def mutate(reg):
            reg["removals"].append({
                "id": "script:gone.py", "kind": "script",
                "paths": ["scripts/registered_tool.py"],
                "witness": {"class": "none", "ref": None}, "note": "spent",
            })
        self.write_registry(mutate)
        out = run(["--check", "--repo-root", str(self.repo),
                          "--skill-path", "agents/skills/SKILL.md"], cwd=self.repo)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("still exists", out.stdout)

    def test_missing_state_field_row_fails(self):
        def mutate(reg):
            reg["entries"] = [e for e in reg["entries"]
                              if e["id"] != "state-field:beta_field"]
        self.write_registry(mutate)
        out = run(["--check", "--repo-root", str(self.repo),
                          "--skill-path", "agents/skills/SKILL.md"], cwd=self.repo)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("unregistered state field", out.stdout)

    def test_keep_with_missing_path_fails(self):
        def mutate(reg):
            reg["entries"][0]["paths"] = ["scripts/vanished_tool.py"]
        self.write_registry(mutate)
        out = run(["--check", "--repo-root", str(self.repo),
                          "--skill-path", "agents/skills/SKILL.md"], cwd=self.repo)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("keep path does not exist", out.stdout)

    def test_overlapping_paths_fail(self):
        def mutate(reg):
            reg["entries"][1]["paths"] = list(reg["entries"][0]["paths"])
        self.write_registry(mutate)
        out = run(["--check", "--repo-root", str(self.repo),
                          "--skill-path", "agents/skills/SKILL.md"], cwd=self.repo)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("already owned by", out.stdout)

    def test_pending_row_fails_plain_check_and_passes_allow_pending(self):
        def mutate(reg):
            reg["entries"][0]["disposition"] = "pending"
        self.write_registry(mutate)
        out = run(["--check", "--repo-root", str(self.repo),
                          "--skill-path", "agents/skills/SKILL.md"], cwd=self.repo)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("still pending", out.stdout)
        out = run(["--check", "--allow-pending", "--repo-root", str(self.repo),
                          "--skill-path", "agents/skills/SKILL.md"], cwd=self.repo)
        self.assertEqual(out.returncode, 0, out.stdout)

    def test_temp_teardown(self):
        self.assertTrue(self.repo.exists())
        # tearDown removes the tree; explicit assertion documents the contract.
        shutil.rmtree(self.tmp, ignore_errors=True)
        self.assertFalse(self.repo.exists())


class RealTreeCheck(unittest.TestCase):
    """Enforcing arm of the standing regrowth guard: the real repository tree
    must pass the check mode. Invocation: `python3 scripts/test_machinery_inventory.py
    --real-tree` (runs ONLY this arm against the live tracked tree, from a repo
    checkout; outside one it skips with exit 0). The default run is fixture-only
    by deliberate contract (plan 2026-10-02-machinery-realtree-arm-run-mode,
    Task 1): default-run inclusion of this arm is deferred until the default
    consumers are ready for the arm's red-on-drift semantics."""
    def test_real_tree_checks_green(self):
        root = Path(__file__).parent.parent
        if not (root / ".git").exists():
            self.skipTest("not run from a repository checkout")
        out = subprocess.run([sys.executable, str(SCRIPT), "--check"],
                             capture_output=True, text=True, cwd=root)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)


def load_tests(loader, tests, pattern):
    """Pattern-aware selection pin (plan 2026-10-02-machinery-realtree-arm-run-mode,
    Task 1): under unittest DISCOVERY (pattern set) both arms load, preserving
    discovery's today-semantics; under the documented default invocation
    (pattern unset) only the fixture arm runs, pinning it to exactly today's
    14 tests."""
    fixture = loader.loadTestsFromTestCase(MachineryInventoryTest)
    realtree = loader.loadTestsFromTestCase(RealTreeCheck)
    if pattern:
        return unittest.TestSuite([fixture, realtree])
    return fixture


if __name__ == "__main__":
    if "--real-tree" in sys.argv:
        sys.argv.remove("--real-tree")
        unittest.main(argv=[sys.argv[0], "RealTreeCheck"])
    else:
        unittest.main()
