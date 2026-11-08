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
        (self.repo / "scripts" / "test_registered_tool.py").write_text(
            "# exercises registered_tool\n")
        (self.repo / "scripts" / "test_shared_suite.py").write_text(
            "# exercises unregistered_tool and machinery_inventory\n")
        (self.repo / "scripts" / "keep_tool.sh").write_text(
            "#!/bin/sh\necho keep_tool\n")
        (self.repo / "scripts" / "test_keep_tool.sh").write_text(
            "# exercises keep_tool\n")
        # Dual-stem pair: one registry row will own BOTH script paths and
        # its committed witness test must name both stems (all-of pin).
        (self.repo / "scripts" / "alpha_tool.py").write_text("# alpha\n")
        (self.repo / "scripts" / "beta_tool.py").write_text("# beta\n")
        (self.repo / "scripts" / "test_dual_suite.py").write_text(
            "# exercises alpha_tool and beta_tool\n")
        (self.repo / "agents" / "hooks" / "my-hook" / "hook.sh").write_text("#!/bin/sh\n")
        (self.repo / "agents" / "skills" / "SKILL.md").write_text(SKILL_FIXTURE)
        subprocess.run(["git", "init", "-q"], cwd=self.repo)
        subprocess.run(["git", "add", "-A"], cwd=self.repo)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                        "commit", "-qm", "fixture"], cwd=self.repo)
        self.copy_script()
        self.commit_all("track the copied inventory script")
        # Scaffold, then disposition into a clean keep set.
        out = run(["--scaffold", "--repo-root", str(self.repo),
                   "--skill-path", "agents/skills/SKILL.md"], cwd=self.repo)
        self.assertEqual(out.returncode, 0, out.stderr)
        reg = json.loads((self.repo / "scripts" / "machinery_registry.json").read_text())
        ids = {e["id"] for e in reg["entries"]}
        self.assertIn("script:registered_tool.py", ids)
        self.assertIn("script:unregistered_tool.py", ids)
        self.assertIn("script:alpha_tool.py", ids)
        self.assertIn("script:beta_tool.py", ids)
        self.assertIn("hook:my-hook", ids)
        self.assertIn("state-field:alpha_field", ids)
        self.assertIn("state-field:beta_field", ids)
        self.assertNotIn("state-field:ok", ids)
        # A pathless script row resolving no source (the registry's
        # undercount-audit shape): it takes the tracked-test-source check only.
        reg["entries"].append({
            "id": "script:undercount-audit-helper",
            "kind": "script",
            "paths": [],
            "tests": [],
            "note": "warning-only helper; the shared checker keeps its own row",
            "witness": {"class": "red-test", "ref": "scripts/test_shared_suite.py"},
            "disposition": "keep",
        })
        # Merge the scaffold's two per-file rows into ONE row owning both
        # script paths: its witness must then name BOTH resolved stems,
        # pinning the all-of stem semantics (an any-of weakening, which
        # fails only when no resolved stem is present, would pass a
        # witness naming only one).
        reg["entries"] = [e for e in reg["entries"]
                          if e["id"] != "script:beta_tool.py"]
        for entry in reg["entries"]:
            if entry["id"] == "script:alpha_tool.py":
                entry["paths"] = ["scripts/alpha_tool.py",
                                  "scripts/beta_tool.py"]
        # Disposition: keep everything with a resolving witness. Script rows
        # witness test sources whose committed content names their stems
        # (witness-ref-validation plan, Task 1).
        witness_by_id = {
            "script:registered_tool.py": "scripts/test_registered_tool.py",
            "script:unregistered_tool.py": "scripts/test_shared_suite.py",
            "script:machinery_inventory.py": "scripts/test_shared_suite.py",
            "script:keep_tool.sh": "scripts/test_keep_tool.sh",
            "script:alpha_tool.py": "scripts/test_dual_suite.py",
            "script:undercount-audit-helper": "scripts/test_shared_suite.py",
        }
        for entry in reg["entries"]:
            entry["disposition"] = "keep"
            if entry["kind"] == "state-field":
                entry["witness"] = {"class": "user-decision",
                                    "ref": "agents/skills/SKILL.md"}
            else:
                entry["witness"] = {"class": "red-test",
                                    "ref": witness_by_id.get(
                                        entry["id"],
                                        "scripts/test_registered_tool.py")}
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

    def entry(self, reg, rid):
        """Row lookup by registry id: scaffold sort order is not a fixture
        contract, so each mutation names the row it means."""
        return next(e for e in reg["entries"] if e["id"] == rid)

    def test_clean_registry_checks_green(self):
        out = run(["--check", "--repo-root", str(self.repo),
                          "--skill-path", "agents/skills/SKILL.md"], cwd=self.repo)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)

    def test_scaffold_generates_rows_for_all_sources(self):
        reg = json.loads((self.repo / "scripts" / "machinery_registry.json").read_text())
        kinds = {e["kind"] for e in reg["entries"]}
        self.assertLessEqual({"script", "hook", "state-field"}, kinds)

    def test_unregistered_script_fails(self):
        def mutate(reg):
            reg["entries"] = [e for e in reg["entries"]
                              if e["id"] != "script:machinery_inventory.py"]
        self.write_registry(mutate)
        out = run(["--check", "--repo-root", str(self.repo),
                          "--skill-path", "agents/skills/SKILL.md"], cwd=self.repo)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("unregistered script file", out.stdout)

    def test_keep_with_missing_ref_fails(self):
        def mutate(reg):
            self.entry(reg, "script:machinery_inventory.py")["witness"]["ref"] = \
                "scripts/no_such_test.py"
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
            self.entry(reg, "script:machinery_inventory.py")["witness"] = {
                "class": "incident", "ref": "scripts/untracked_note.md"}
        self.write_registry(mutate)
        out = run(["--check", "--repo-root", str(self.repo),
                          "--skill-path", "agents/skills/SKILL.md"], cwd=self.repo)
        self.assertNotEqual(out.returncode, 0)

    def test_keep_with_class_none_fails(self):
        def mutate(reg):
            self.entry(reg, "script:machinery_inventory.py")["witness"] = {
                "class": "none", "ref": None}
        self.write_registry(mutate)
        out = run(["--check", "--repo-root", str(self.repo),
                          "--skill-path", "agents/skills/SKILL.md"], cwd=self.repo)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("witness class none", out.stdout)

    def test_delete_without_note_fails(self):
        def mutate(reg):
            entry = self.entry(reg, "script:machinery_inventory.py")
            entry["disposition"] = "delete"
            entry["paths"] = []  # not tracked as existing any more
        self.write_registry(mutate)
        out = run(["--check", "--repo-root", str(self.repo),
                          "--skill-path", "agents/skills/SKILL.md"], cwd=self.repo)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("delete row without a note", out.stdout)

    def test_duplicate_id_fails(self):
        def mutate(reg):
            twin = dict(self.entry(reg, "script:machinery_inventory.py"))
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
            self.entry(reg, "script:machinery_inventory.py")["paths"] = [
                "scripts/vanished_tool.py"]
        self.write_registry(mutate)
        out = run(["--check", "--repo-root", str(self.repo),
                          "--skill-path", "agents/skills/SKILL.md"], cwd=self.repo)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("keep path does not exist", out.stdout)

    def test_overlapping_paths_fail(self):
        def mutate(reg):
            self.entry(reg, "script:registered_tool.py")["paths"] = list(
                self.entry(reg, "script:machinery_inventory.py")["paths"])
        self.write_registry(mutate)
        out = run(["--check", "--repo-root", str(self.repo),
                          "--skill-path", "agents/skills/SKILL.md"], cwd=self.repo)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("already owned by", out.stdout)

    def test_pending_row_fails_plain_check_and_passes_allow_pending(self):
        def mutate(reg):
            self.entry(
                reg, "script:machinery_inventory.py")["disposition"] = "pending"
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

    # --- red-test witness validation (plan 2026-10-30-machinery-witness-ref-
    # validation, Task 1): a red-test witness ref must be a tracked test
    # source, and a script row's witness test must name every resolved script
    # stem, read from the committed HEAD copy of the test source. ---

    def commit_all(self, message):
        subprocess.run(["git", "add", "-A"], cwd=self.repo, check=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                        "commit", "-qm", message], cwd=self.repo, check=True)

    def run_check(self):
        return run(["--check", "--repo-root", str(self.repo),
                    "--skill-path", "agents/skills/SKILL.md"], cwd=self.repo)

    def test_red_test_witness_must_be_test_source_path(self):
        # A tracked Markdown file whose basename begins test_ is not a
        # Python/shell test source: the witness fails naming its row id.
        (self.repo / "docs").mkdir()
        (self.repo / "docs" / "test_readme_notes.md").write_text("# notes\n")
        self.commit_all("track a markdown notes file")
        def mutate(reg):
            self.entry(reg, "script:registered_tool.py")["witness"] = {
                "class": "red-test", "ref": "docs/test_readme_notes.md"}
        self.write_registry(mutate)
        out = self.run_check()
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("script:registered_tool.py", out.stdout)
        self.assertIn("not a tracked test-source path", out.stdout)

    def test_non_script_row_red_test_witness_must_be_test_source_path(self):
        # The tracked-test-source fence applies to every row kind, not only
        # script rows: a hook row's red-test witness pointing at a tracked
        # non-test path (the fixture README.md) fails naming its row id.
        (self.repo / "README.md").write_text("# fixture readme\n")
        self.commit_all("track the fixture README")
        def mutate(reg):
            self.entry(reg, "hook:my-hook")["witness"] = {
                "class": "red-test", "ref": "README.md"}
        self.write_registry(mutate)
        out = self.run_check()
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("hook:my-hook", out.stdout)
        self.assertIn("not a tracked test-source path", out.stdout)

    def test_red_test_witness_omitting_path_stem_fails(self):
        # A path-bearing script row whose committed witness test omits the
        # path-derived stem fails naming its row id.
        (self.repo / "scripts" / "test_registered_tool.py").write_text(
            "# exercises nothing\n")
        self.commit_all("drop the stem from the witness test")
        out = self.run_check()
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("script:registered_tool.py", out.stdout)
        self.assertIn("omits resolved script stem(s)", out.stdout)
        self.assertIn("registered_tool", out.stdout)

    def test_red_test_witness_omitting_id_derived_stem_fails(self):
        # A pathless script row with a filename-shaped id: the id supplies
        # the stem, and a witness test omitting it fails.
        def mutate(reg):
            row = self.entry(reg, "script:registered_tool.py")
            row["id"] = "script:probe_tool.py"
            row["paths"] = []
        self.write_registry(mutate)
        out = self.run_check()
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("script:probe_tool.py", out.stdout)
        self.assertIn("omits resolved script stem(s)", out.stdout)
        self.assertIn("probe_tool", out.stdout)

    def test_red_test_witness_omitting_note_derived_stem_fails(self):
        # A pathless row whose non-filename id carries a note naming a
        # concrete script path: the note supplies the stem, and a witness
        # test omitting it fails.
        def mutate(reg):
            row = self.entry(reg, "script:registered_tool.py")
            row["id"] = "script:helper-arm"
            row["paths"] = []
            row["note"] = "warning-only arm living in scripts/probe_tool.py"
        self.write_registry(mutate)
        out = self.run_check()
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("script:helper-arm", out.stdout)
        self.assertIn("omits resolved script stem(s)", out.stdout)
        self.assertIn("probe_tool", out.stdout)

    def test_red_test_witness_omitting_one_of_two_stems_fails(self):
        # All-of pin: the dual-path row script:alpha_tool.py resolves TWO
        # stems (alpha_tool, beta_tool); a committed witness test naming
        # only ONE of them must fail naming the row id. An any-of
        # weakening (fail only when NO resolved stem is present) passes
        # this row and is caught here.
        (self.repo / "scripts" / "test_dual_suite.py").write_text(
            "# exercises alpha_tool only\n")
        self.commit_all("drop beta_tool from the dual-stem witness test")
        out = self.run_check()
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("script:alpha_tool.py", out.stdout)
        self.assertIn("omits resolved script stem(s)", out.stdout)
        self.assertIn("beta_tool", out.stdout)

    def test_red_test_witness_naming_all_resolved_stems_passes(self):
        # Positive all-of control: the dual-path row's witness test names
        # BOTH resolved stems, so the check stays green.
        out = self.run_check()
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)

    def test_pathless_row_without_resolvable_source_gets_path_check_only(self):
        # The undercount-audit shape (no paths, no filename-shaped id, no
        # scripts/<file> path in the note): a valid test-source ref passes
        # and no inferred stem is checked (the witness content names none).
        out = self.run_check()
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertNotIn("undercount-audit-helper", out.stdout)

    def test_shell_test_source_witness_passes(self):
        # A .sh test source is a valid red-test witness: the clean fixture
        # witnesses script:keep_tool.sh with scripts/test_keep_tool.sh.
        reg = json.loads(
            (self.repo / "scripts" / "machinery_registry.json").read_text())
        row = next(e for e in reg["entries"] if e["id"] == "script:keep_tool.sh")
        self.assertEqual(row["witness"],
                         {"class": "red-test", "ref": "scripts/test_keep_tool.sh"})
        out = self.run_check()
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)

    def test_witness_content_read_from_committed_head(self):
        # Unstaged, then staged, edits to a witness test must not alter the
        # result: the check reads the committed HEAD copy of the test source
        # (the committed stem-less flip is covered by the path-stem mutation).
        (self.repo / "scripts" / "test_registered_tool.py").write_text(
            "# exercises nothing\n")
        out = self.run_check()
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        subprocess.run(["git", "add", "-A"], cwd=self.repo)
        out = self.run_check()
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)


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


class RegistryContentWitness(unittest.TestCase):
    """Content witness for the archive-rider report arm's admission row
    (plan 2026-11-07-archive-rider-sweep-ordering, Task 3): the real
    registry's row carries the named admission fields in its note, so the
    battery distinguishes the prescribed row from a structural-only row.
    Expected GREEN at landing; reds when the row is dropped or thinned."""

    ROW_ID = "duty:archive-ceremony-post-landing-report"
    # The citation rule's covering-plan form: the living covering plan at
    # this landing, its docs/history/plans/completed/ twin after the note's
    # documented re-point (no docs/history/backlog/completed/ twin exists
    # for the origin row, so the covering-plan form applies).
    ALLOWED_WITNESS_REFS = {
        "docs/history/plans/2026-11-07-archive-rider-sweep-ordering.md",
        "docs/history/plans/completed/2026-11-07-archive-rider-sweep-ordering.md",
    }

    def setUp(self):
        root = Path(__file__).parent.parent
        if not (root / ".git").exists():
            self.skipTest("not run from a repository checkout")
        self.registry = json.loads(
            (root / "scripts" / "machinery_registry.json").read_text(
                encoding="utf-8"))

    def admission_row(self):
        rows = [e for e in self.registry.get("entries", [])
                if e.get("id") == self.ROW_ID]
        self.assertEqual(
            len(rows), 1,
            "the archive-rider report arm's admission row is missing")
        return rows[0]

    def test_row_structure_matches_the_prescribed_shape(self):
        row = self.admission_row()
        self.assertEqual(row["disposition"], "keep")
        self.assertEqual(row["kind"], "protocol")
        # claim-if-concurrent: both arm files are owned by existing rows
        # (script:done_sweep_gates_lib.py, protocol:primary-log-ref-precondition).
        self.assertEqual(row["paths"], [])
        self.assertEqual(row["witness"]["class"], "incident")
        self.assertIn(row["witness"]["ref"], self.ALLOWED_WITNESS_REFS)

    def test_note_carries_the_named_admission_fields(self):
        note = self.admission_row().get("note") or ""
        needles = (
            # warning-only posture
            "warning-only",
            # concrete incident link: the two catches on 2026-11-07, the
            # origin row, and the covering-plan citation form with re-point
            "concrete incident",
            "2026-11-07",
            "docs/history/backlog/2026-11-07-archive-ceremony-exec-review-record-gap.md",
            "fef5ebd2a",
            "8cdc8ef65",
            "docs/history/plans/completed/2026-11-07-archive-rider-sweep-ordering.md",
            # expected catch frequency
            "expected catch frequency",
            # false-positive cost
            "false-positive cost",
            # promotion criteria with demotion pairing and operator approval
            "promotion criteria",
            "demotion",
            "operator approval",
            # false-catch ledger duty
            "false-catch ledger",
            # review date
            "review date: 2026-12-07",
            # the arm's paths
            "scripts/done_sweep_gates_lib.py",
            "scripts/done_run.sh",
            "archive_ceremony_post_landing_report",
        )
        for needle in needles:
            self.assertIn(needle, note, "missing admission field: " + needle)


def load_tests(loader, tests, pattern):
    """Pattern-aware selection pin (plan 2026-10-02-machinery-realtree-arm-run-mode,
    Task 1): under unittest DISCOVERY (pattern set) all three arms load,
    preserving discovery's today-semantics; under the documented default
    invocation (pattern unset) only the fixture arm runs, pinning it to
    exactly today's 24 tests (the real-tree and content-witness arms are the
    discovery and pytest extras)."""
    fixture = loader.loadTestsFromTestCase(MachineryInventoryTest)
    realtree = loader.loadTestsFromTestCase(RealTreeCheck)
    content = loader.loadTestsFromTestCase(RegistryContentWitness)
    if pattern:
        return unittest.TestSuite([fixture, realtree, content])
    return fixture


if __name__ == "__main__":
    if "--real-tree" in sys.argv:
        sys.argv.remove("--real-tree")
        unittest.main(argv=[sys.argv[0], "RealTreeCheck"])
    else:
        unittest.main()
