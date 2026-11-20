#!/usr/bin/env python3
"""Hermetic suite for the machinery inventory: a scratch git tree carrying a
tracked-layout fixture, each check arm mutated one at a time."""

import copy
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

    def test_load_tests_discovery_arm_includes_render_classes(self):
        # Suite selection (plan 2026-11-13-known-red-gates-consumed-baseline,
        # Task 1): the render-mode test classes join load_tests's discovery
        # arm, so the required inventory run collects them; Task 3 extends
        # the same join to the known-red consumption witness class.
        loader = unittest.defaultTestLoader
        suite = load_tests(loader, unittest.TestSuite(), "discovery-pattern")

        def leaf_ids(node):
            for item in node:
                if isinstance(item, unittest.TestSuite):
                    yield from leaf_ids(item)
                else:
                    yield item.id()

        ids = list(leaf_ids(suite))
        self.assertTrue(
            any("RenderBaselineTest.test_" in test_id for test_id in ids),
            ids)
        self.assertTrue(
            any("RegistryContentWitnessKnownRedBaseline.test_" in test_id
                for test_id in ids),
            ids)


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


class RegistryContentWitnessZeroTurnCensus(unittest.TestCase):
    """Content witness for the zero-turn census duty row pair (plan
    2026-11-13-errored-zero-turn-carrier-recovery, Task 3): the real
    registry's rows carry the named admission fields, so the battery
    distinguishes the prescribed row pair from a structural-only pair.
    Expected GREEN at landing; reds when either row is dropped or thinned."""

    ROW_ID = "duty:carrier-liveness-zero-turn"
    ALLOWED_WITNESS_REFS = {
        "docs/history/plans/2026-11-13-errored-zero-turn-carrier-recovery.md",
        "docs/history/plans/completed/2026-11-13-errored-zero-turn-carrier-recovery.md",
    }

    def setUp(self):
        root = Path(__file__).parent.parent
        if not (root / ".git").exists():
            self.skipTest("not run from a repository checkout")
        self.registry = json.loads(
            (root / "scripts" / "machinery_registry.json").read_text(
                encoding="utf-8"))

    def _row(self, section):
        rows = [e for e in self.registry.get(section, [])
                if e.get("id") == self.ROW_ID]
        self.assertEqual(len(rows), 1,
                         "the zero-turn census %s row is missing" % section)
        return rows[0]

    def test_zero_turn_row_structure_matches_the_prescribed_shape(self):
        entry = self._row("entries")
        self.assertEqual(entry["disposition"], "keep")
        self.assertEqual(entry["kind"], "protocol")
        self.assertEqual(entry["paths"], [])
        self.assertEqual(entry["tests"], ["scripts/test_execute_plan_resume_watcher.py"])
        self.assertEqual(entry["witness"]["class"], "incident")
        self.assertIn(entry["witness"]["ref"], self.ALLOWED_WITNESS_REFS)
        removals = self._row("removals")
        self.assertEqual(removals["disposition"], "delete")
        self.assertEqual(removals["paths"], [])
        self.assertIn(removals["witness"]["ref"], self.ALLOWED_WITNESS_REFS)

    def test_zero_turn_note_carries_the_named_admission_fields(self):
        note = self._row("entries").get("note") or ""
        needles = (
            # warning-only posture and wiring
            "warning-only",
            "carrier-liveness|zero-turn|automation=<id>|session=<id>",
            "newest-30",
            # concrete incident link and the covering-plan citation form
            "concrete incident",
            "2026-11-12/13",
            "docs/history/backlog/2026-11-13-errored-zero-turn-carrier-recovery.md",
            # expected catch frequency and false-positive cost
            "expected catch",
            "false-positive cost",
            # sunset and promotion criteria
            "sunset 2026-12-13",
            "third true catch",
            # the witness re-point duty to the completed twin
            "docs/history/plans/completed/2026-11-13-errored-zero-turn-carrier-recovery.md",
            # the arm's surfaces
            "scripts/execute_plan_runtime.py",
            "scripts/test_execute_plan_resume_watcher.py",
        )
        for needle in needles:
            self.assertIn(needle, note, "missing admission field: " + needle)
        removals_note = self._row("removals").get("note") or ""
        for needle in ("sunset 2026-12-13", "third true catch", "co-removal set"):
            self.assertIn(needle, removals_note, "missing removals field: " + needle)


class RegistryContentWitnessPostFireCensus(unittest.TestCase):
    """Content witness for the post-fire census duty row pair (plan
    2026-11-14-post-fire-verification-arm-zero-executions, Task 3): the real
    registry's rows carry the named admission fields, so the battery
    distinguishes the prescribed row pair from a structural-only pair.
    Expected GREEN at landing; reds when either row is dropped or thinned."""

    ROW_ID = "duty:post-fire-verification-census"
    # the citation rule's re-point form: the living covering plan at this
    # landing, its docs/history/plans/completed/ twin after the note's
    # re-point duty executes at the plan-family completion fold
    ALLOWED_WITNESS_REFS = {
        "docs/history/plans/2026-11-14-post-fire-verification-arm-zero-executions.md",
        "docs/history/plans/completed/2026-11-14-post-fire-verification-arm-zero-executions.md",
    }

    def setUp(self):
        root = Path(__file__).parent.parent
        if not (root / ".git").exists():
            self.skipTest("not run from a repository checkout")
        self.registry = json.loads(
            (root / "scripts" / "machinery_registry.json").read_text(
                encoding="utf-8"))

    def _row(self, section):
        rows = [e for e in self.registry.get(section, [])
                if e.get("id") == self.ROW_ID]
        self.assertEqual(len(rows), 1,
                         "the post-fire census %s row is missing" % section)
        return rows[0]

    def test_post_fire_row_structure_matches_the_prescribed_shape(self):
        entry = self._row("entries")
        self.assertEqual(entry["disposition"], "keep")
        self.assertEqual(entry["kind"], "protocol")
        self.assertEqual(entry["paths"], [])
        self.assertEqual(entry["tests"],
                         ["scripts/test_maintenance_fire_outcomes.py"])
        self.assertEqual(entry["witness"]["class"], "incident")
        self.assertIn(entry["witness"]["ref"], self.ALLOWED_WITNESS_REFS)
        removals = self._row("removals")
        self.assertEqual(removals["disposition"], "delete")
        self.assertEqual(removals["paths"], [])
        self.assertIn(removals["witness"]["ref"], self.ALLOWED_WITNESS_REFS)

    def test_post_fire_note_carries_the_named_admission_fields(self):
        note = self._row("entries").get("note") or ""
        needles = (
            # warning-only posture and wiring
            "warning-only",
            "census subcommand",
            "record-outcome and append-correction writes",
            "unwired",
            "report-only",
            "never blocking or arming",
            # concrete incident link and the origin-row citation form
            "concrete incident",
            "zero-execution window",
            "docs/history/backlog/2026-11-14-post-fire-verification-arm-zero-executions.md",
            # expected catch frequency and false-positive cost
            "expected catch",
            "every survey turn holding passed-fire one-shot members",
            "false-positive cost",
            "one unwired line misreporting a wiped corpus",
            "unknown degradation",
            # review date and the witness re-point duty to the completed twin
            "review date 2026-12-05",
            "docs/history/plans/completed/2026-11-14-post-fire-verification-arm-zero-executions.md",
            # the arm's surfaces
            "scripts/maintenance_fire_outcomes.py",
            "scripts/test_maintenance_fire_outcomes.py",
        )
        for needle in needles:
            self.assertIn(needle, note, "missing admission field: " + needle)
        removals_note = self._row("removals").get("note") or ""
        for needle in (
            "sunset = review date 2026-12-05",
            "co-removal set",
            "both registry rows",
            "exercised-catch record",
            "recorded correction decisions",
            "docs/history/plans/completed/2026-11-14-post-fire-verification-arm-zero-executions.md",
        ):
            self.assertIn(needle, removals_note, "missing removals field: " + needle)


# --- Known-red gate baseline rendering (plan
# 2026-11-13-known-red-gates-consumed-baseline, Task 1). Each test renders the
# baseline from a scratch git tree carrying copies of the three producer
# surfaces, the five core-file checkpoint targets the pins suite's pre-pin
# checkpoint probes, one commit on HEAD, a minimal tracked recorded-red
# register, and a caps table seeding one advisory budget breach. The scratch
# tree is its own repository, so the render's primary-checkout resolution
# (the first `git worktree list --porcelain` entry) anchors at the scratch
# root and every producer resolves repo-relative within that target
# checkout. ---

RENDER_PINS_REGISTER = {
    "schema": 1,
    "guards": {
        "check_maintenance_pins": {
            "rows": [
                {
                    "kind": "override",
                    "date": "2026-01-15",
                    "note": "pin: G1e guard present review-by: 2099-01-01 "
                            "fixture standing red",
                },
                {
                    "kind": "override",
                    "date": "2026-01-15",
                    "note": "pin: pricing rule pointer review-by: 2024-06-01 "
                            "fixture flip red",
                },
                {
                    "kind": "override",
                    "date": "2026-01-15",
                    "note": "pin: malformed sample pin name review-by: not-a-date",
                },
            ],
        },
    },
}

# the escalation assertions pin the recorded-red evaluation clock to a fixed
# date through the ambient PINS_RECORDED_RED_AS_OF seam: 2024-06-01 is after
# the pin (recorded) here, and before the system date in the unset arm
# (expired there), so both escalation shapes are deterministic
RENDER_AS_OF_PIN = "2024-05-05"

RENDER_RECORDED_LINE = ("PIN RECORDED RED (recorded 2026-01-15, "
                        "review-by 2099-01-01): G1e guard present")
RENDER_FLIP_LINE_RECORDED = ("PIN RECORDED RED (recorded 2026-01-15, "
                             "review-by 2024-06-01): pricing rule pointer")
RENDER_FLIP_LINE_EXPIRED = ("PIN RECORDED RED EXPIRED (recorded 2026-01-15, "
                            "review-by 2024-06-01): pricing rule pointer")
RENDER_MALFORMED_LINE = ("PIN RECORDED RED MALFORMED (treated as not recorded): "
                         "malformed sample pin name")
RENDER_BREACH_LINE = "BREACH (advisory): agents/skills/done/SKILL.md 100 bytes > cap 10"

RENDER_EXCLUDED_LINE_PREFIXES = (
    "PIN RECORDED REDS SUPPRESSED THIS RUN:",
    "prune-range pins: first missing clause:",
    "placement pins: first missing span:",
    "missing ",
    "CAPS GAP",
    "STALE CAP",
    "LOG ",
)


class RenderBaselineTest(unittest.TestCase):
    PRODUCER_SCRIPTS = ("machinery_inventory.py", "check_maintenance_pins.sh",
                        "skill_text_budget.py")

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="render-baseline-test-"))
        self.repo = Path(os.path.realpath(self.tmp)) / "primary"
        (self.repo / "scripts").mkdir(parents=True)
        for name in ("maintenance", "done", "execute-plan"):
            (self.repo / "agents" / "skills" / name).mkdir(parents=True)
        # the five core-file checkpoint targets ($S $Z $P $D $E) plus the
        # state-file surface the inventory witness consult reads
        self.write(
            self.repo / "agents" / "skills" / "maintenance" / "SKILL.md",
            "# maintenance router\n")
        self.write(
            self.repo / "agents" / "skills" / "maintenance" / "zcode.md",
            "# zcode overlay\n")
        self.write(
            self.repo / "agents" / "skills" / "maintenance" / "prompt-templates.md",
            "# prompt templates\n")
        self.write(
            self.repo / "agents" / "skills" / "done" / "SKILL.md", "b" * 100)
        self.write(
            self.repo / "agents" / "skills" / "execute-plan" / "SKILL.md",
            "# execute-plan router\n")
        self.write(
            self.repo / "agents" / "skills" / "maintenance" / "state-file.md",
            "# state file surface\n\n## State file\n\n"
            "`alpha_field` is the top-level alpha.\n")
        scripts_dir = Path(__file__).parent
        for name in self.PRODUCER_SCRIPTS:
            shutil.copy(scripts_dir / name, self.repo / "scripts" / name)
        # fixture caps table: done/SKILL.md carries a 10-byte cap its 100
        # bytes exceed, seeding the advisory budget BREACH line
        self.write(
            self.repo / "scripts" / "skill_text_budget_caps.json",
            json.dumps({"files": {"agents/skills/done/SKILL.md": 10}}))
        self.write(self.repo / "scripts" / "gate_liveness_ledger.json",
                   json.dumps(RENDER_PINS_REGISTER))
        self.write(self.repo / "scripts" / "machinery_registry.json",
                   json.dumps({"schema_version": 1, "entries": [],
                               "removals": []}))
        self.fixture_commit("fixture tree")
        self.base = self.render_payload()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, path, text):
        path.write_text(text, encoding="utf-8")

    def fixture_commit(self, message):
        # determinism pins: identity, commit dates, and init.defaultBranch
        env = dict(os.environ)
        env.update({"GIT_AUTHOR_DATE": "2026-01-01T00:00:00 +0000",
                    "GIT_COMMITTER_DATE": "2026-01-01T00:00:00 +0000"})
        subprocess.run(
            ["git", "-c", "init.defaultBranch=main", "init", "-q"],
            cwd=self.repo, check=True)
        subprocess.run(["git", "add", "-A"], cwd=self.repo, check=True)
        subprocess.run(
            ["git", "-c", "user.email=fixture@example.test",
             "-c", "user.name=fixture", "commit", "-qm", message],
            cwd=self.repo, check=True, env=env)

    def git_out(self, repo, *args):
        out = subprocess.run(["git", "-C", str(repo)] + list(args),
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        return out.stdout.strip()

    def render_env(self, **extra):
        # hermetic env pins: every ambient env input the pins producer reads
        # is pinned here; PINS_RECORDED_RED_REGISTER stays unset so the
        # suite's default resolution anchors at the target checkout's
        # tracked ledger (scripts/gate_liveness_ledger.json)
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(self.tmp),
            "TMPDIR": str(self.tmp),
            "PINS_DUPLICATE_ROOT": str(self.repo),
            "PINS_RECORDED_RED_AS_OF": RENDER_AS_OF_PIN,
        }
        env.update(extra)
        return env

    def run_render(self, out_arg="baseline.json", cwd=None, env=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--render-baseline", str(out_arg)],
            capture_output=True, text=True, cwd=str(cwd or self.repo),
            env=env if env is not None else self.render_env())

    def render_payload(self, out_arg="baseline.json", cwd=None, env=None):
        out = self.run_render(out_arg, cwd, env)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("OUTCOME: pass", out.stdout)
        return json.loads(
            (self.repo / out_arg).read_text(encoding="utf-8"))

    def captured(self, payload, producer):
        return [entry["line"]
                for entry in payload["producers"][producer]["captured_lines"]]

    def normalize(self, payload):
        # determinism modulo the documented variable fields: the generation
        # timestamp, the base-tip hash, and absolute paths in captured lines
        payload = copy.deepcopy(payload)
        payload["generated_at"] = "<generated-at>"
        if isinstance(payload.get("base_tip"), dict):
            payload["base_tip"]["commit"] = "<base-tip>"

        def walk(node):
            if isinstance(node, dict):
                return {key: walk(value) for key, value in node.items()}
            if isinstance(node, list):
                return [walk(item) for item in node]
            if isinstance(node, str):
                return node.replace(str(self.repo), "<checkout-root>")
            return node

        return walk(payload)

    def test_render_writes_baseline_with_capture_vocabulary_and_metadata(self):
        payload = self.base
        self.assertEqual(payload["schema"], "known-red-gates-baseline")
        self.assertEqual(payload["schema_version"], 1)
        self.assertRegex(payload["generated_at"],
                         r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
        self.assertEqual(payload["primary_checkout"], str(self.repo))
        self.assertEqual(payload["write_home"], str(self.repo / "baseline.json"))
        self.assertEqual(payload["base_tip"]["commit"],
                         self.git_out(self.repo, "rev-parse", "HEAD"))
        self.assertEqual(payload["base_tip"]["source"], "primary-branch")
        self.assertEqual(sorted(payload["producers"]),
                         ["machinery_inventory", "maintenance_pins",
                          "skill_text_budget"])
        for producer, section in payload["producers"].items():
            self.assertEqual(section["status"], "captured", producer)
            self.assertIsNone(section["unavailable_reason"])
            self.assertRegex(section["digest"], r"^[0-9a-f]{64}$")
        # live inventory emissions from the minimal fixture (regrowth FAILs)
        inventory = self.captured(payload, "machinery_inventory")
        self.assertTrue(any(line.startswith(
            "FAIL: regrowth: unregistered script file scripts/")
            for line in inventory), inventory)
        self.assertIn(
            "FAIL: regrowth: unregistered state field state-field:alpha_field",
            inventory)
        # recorded line samples (the register seam) beside live emissions
        pins = self.captured(payload, "maintenance_pins")
        self.assertIn(RENDER_RECORDED_LINE, pins)
        self.assertIn(RENDER_FLIP_LINE_RECORDED, pins)
        self.assertIn(RENDER_MALFORMED_LINE, pins)
        malformed = [entry for entry
                     in payload["producers"]["maintenance_pins"]["captured_lines"]
                     if entry["line"] == RENDER_MALFORMED_LINE]
        self.assertEqual(malformed[0]["stream"], "stderr")
        self.assertTrue(any(line.startswith("PIN FAIL: ") for line in pins),
                        pins)
        # the recorded names were suppressed (no plain PIN FAIL for them)
        self.assertNotIn("PIN FAIL: G1e guard present", pins)
        self.assertNotIn("PIN FAIL: pricing rule pointer", pins)
        budget = self.captured(payload, "skill_text_budget")
        self.assertIn(RENDER_BREACH_LINE, budget)
        self.assertTrue(
            any(line.startswith("PILOT PENDING (advisory): ") for line in budget),
            budget)
        # excluded vocabulary never classifies into any section
        for producer, section in payload["producers"].items():
            for entry in section["captured_lines"]:
                for prefix in RENDER_EXCLUDED_LINE_PREFIXES:
                    self.assertFalse(
                        entry["line"].startswith(prefix),
                        (producer, entry["line"]))

    def test_legacy_exit_shape_and_modeled_fail_are_capture_success(self):
        payload = self.base
        inventory = payload["producers"]["machinery_inventory"]
        # the inventory check runs red on the fixture (rc 1) with the legacy
        # exit shape: no OUTCOME: line anywhere; that shape is normal output,
        # never an unavailable trigger
        self.assertEqual(inventory["exit_code"], 1)
        self.assertEqual(inventory["status"], "captured")
        for entry in inventory["captured_lines"]:
            self.assertFalse(entry["line"].startswith("OUTCOME:"))
        # a modeled fail exit carrying its expected output is capture-success
        pins = payload["producers"]["maintenance_pins"]
        self.assertEqual(pins["exit_code"], 1)
        self.assertEqual(pins["status"], "captured")
        self.assertTrue(pins["expected_output"])
        self.assertEqual(payload["producers"]["skill_text_budget"]["exit_code"], 0)
        self.assertEqual(payload["producers"]["skill_text_budget"]["status"],
                         "captured")

    def test_render_deterministic_modulo_documented_variable_fields(self):
        first = self.normalize(self.base)
        second = self.normalize(self.render_payload())
        self.assertEqual(first, second)

    def test_digest_discrimination_one_mutation_per_producer(self):
        # one mutation per producer: editing one producer's controlling
        # tracked input moves that section's recorded digest while the other
        # two stay byte-equal
        previous = self.base
        mutations = (
            ("machinery_inventory", "scripts/machinery_registry.json"),
            ("maintenance_pins", "scripts/check_maintenance_pins.sh"),
            ("skill_text_budget", "agents/skills/done/SKILL.md"),
        )
        for producer, rel in mutations:
            path = self.repo / rel
            path.write_text(
                path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            payload = self.render_payload()
            self.assertNotEqual(
                payload["producers"][producer]["digest"],
                previous["producers"][producer]["digest"], rel)
            for other, section in payload["producers"].items():
                if other != producer:
                    self.assertEqual(
                        section["digest"],
                        previous["producers"][other]["digest"], (rel, other))
            previous = payload

    def test_unavailable_producer_recorded_others_still_rendered(self):
        # the unavailable-producer injection resolves producer paths
        # repo-relative within the target checkout (scripts/ under the
        # scratch primary), so deleting the copy there is the seam
        (self.repo / "scripts" / "skill_text_budget.py").unlink()
        out = self.run_render()
        self.assertEqual(out.returncode, 2, out.stdout + out.stderr)
        self.assertIn("OUTCOME: indeterminate", out.stdout)
        self.assertIn("render: producer unavailable: skill_text_budget:",
                      out.stdout)
        payload = json.loads((self.repo / "baseline.json").read_text(
            encoding="utf-8"))
        budget = payload["producers"]["skill_text_budget"]
        self.assertEqual(budget["status"], "unavailable")
        self.assertIn("not found", budget["unavailable_reason"])
        self.assertEqual(payload["producers"]["machinery_inventory"]["status"],
                         "captured")
        self.assertEqual(payload["producers"]["maintenance_pins"]["status"],
                         "captured")
        # the other sections still render: never a silent partial baseline
        self.assertTrue(self.captured(payload, "machinery_inventory"))
        self.assertTrue(self.captured(payload, "maintenance_pins"))

    def test_producer_timeout_records_unavailable(self):
        self.write(self.repo / "scripts" / "check_maintenance_pins.sh",
                   "#!/usr/bin/env bash\nsleep 60\n")
        out = self.run_render(
            env=self.render_env(MACHINERY_RENDER_TIMEOUT_SECS="2"))
        self.assertEqual(out.returncode, 2, out.stdout + out.stderr)
        payload = json.loads((self.repo / "baseline.json").read_text(
            encoding="utf-8"))
        pins = payload["producers"]["maintenance_pins"]
        self.assertEqual(pins["status"], "unavailable")
        self.assertIn("timed out", pins["unavailable_reason"])
        self.assertEqual(payload["producers"]["machinery_inventory"]["status"],
                         "captured")
        self.assertEqual(payload["producers"]["skill_text_budget"]["status"],
                         "captured")

    def test_producer_without_expected_output_records_unavailable(self):
        self.write(self.repo / "scripts" / "check_maintenance_pins.sh",
                   "#!/usr/bin/env bash\necho unexpected output\nexit 0\n")
        out = self.run_render()
        self.assertEqual(out.returncode, 2, out.stdout + out.stderr)
        self.assertIn("OUTCOME: indeterminate", out.stdout)
        payload = json.loads((self.repo / "baseline.json").read_text(
            encoding="utf-8"))
        pins = payload["producers"]["maintenance_pins"]
        self.assertEqual(pins["status"], "unavailable")
        self.assertIn("terminated without its expected output",
                      pins["unavailable_reason"])
        self.assertEqual(payload["producers"]["machinery_inventory"]["status"],
                         "captured")
        self.assertEqual(payload["producers"]["skill_text_budget"]["status"],
                         "captured")

    def test_unwritable_existing_baseline_refuses_and_writes_nothing(self):
        baseline = self.repo / "baseline.json"
        original = baseline.read_bytes()
        baseline.chmod(0o444)
        try:
            out = self.run_render()
        finally:
            baseline.chmod(0o644)
        self.assertEqual(out.returncode, 3, out.stdout + out.stderr)
        self.assertIn("OUTCOME: tool_error", out.stdout)
        self.assertIn("render: refusing to write baseline:", out.stdout)
        self.assertIn(str(baseline), out.stdout)
        self.assertEqual(baseline.read_bytes(), original)

    def test_unwritable_output_directory_refuses_and_writes_nothing(self):
        locked = self.tmp / "locked"
        locked.mkdir()
        locked.chmod(0o555)
        try:
            out = self.run_render(str(locked / "baseline.json"))
        finally:
            locked.chmod(0o700)
        self.assertEqual(out.returncode, 3, out.stdout + out.stderr)
        self.assertIn("OUTCOME: tool_error", out.stdout)
        self.assertIn("render: refusing to write baseline:", out.stdout)
        self.assertFalse((locked / "baseline.json").exists())

    def test_env_posture_ambient_only_pins_resolve_at_tracked_ledger(self):
        # no pins variable in the render's environment: the pins producer's
        # register default resolves the target checkout's tracked ledger
        # (the recorded line proves it), the as-of clock rides the system
        # date (the 2024-06-01 review-by reads expired), and the duplicate
        # root falls back to the same checkout root
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
               "HOME": str(self.tmp), "TMPDIR": str(self.tmp)}
        out = self.run_render(env=env)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        payload = json.loads(
            (self.repo / "baseline.json").read_text(encoding="utf-8"))
        pins = self.captured(payload, "maintenance_pins")
        self.assertIn(RENDER_RECORDED_LINE, pins)
        self.assertIn(RENDER_FLIP_LINE_EXPIRED, pins)
        # an expired recorded red fails as unrecorded: the plain PIN FAIL
        # line rides beside the escalation line
        self.assertIn("PIN FAIL: pricing rule pointer", pins)
        self.assertIn(RENDER_MALFORMED_LINE, pins)

    def test_fixture_seam_register_env_forwarded(self):
        # the other fixture-seam leg: the test supplies its own pins through
        # the ambient PINS_RECORDED_RED_REGISTER seam and the producer sees
        # that register, not the tracked ledger
        alt = self.tmp / "alt-register.json"
        self.write(alt, json.dumps({"schema": 1, "guards": {
            "check_maintenance_pins": {"rows": [{
                "kind": "override", "date": "2026-02-20",
                "note": "pin: state-file lane arm present "
                        "review-by: 2099-01-01 alt fixture red",
            }]}}}))
        payload = self.render_payload(
            env=self.render_env(PINS_RECORDED_RED_REGISTER=str(alt)))
        pins = self.captured(payload, "maintenance_pins")
        self.assertIn("PIN RECORDED RED (recorded 2026-02-20, "
                      "review-by 2099-01-01): state-file lane arm present",
                      pins)
        self.assertNotIn(RENDER_RECORDED_LINE, pins)

    def test_primary_checkout_resolution_from_linked_worktree(self):
        wt = self.tmp / "linked"
        self.git_out(self.repo, "worktree", "add", "--quiet", "-b",
                     "wtbranch", str(wt))
        diverged = wt / "agents" / "skills" / "done" / "SKILL.md"
        diverged.write_text("b" * 120, encoding="utf-8")
        env = dict(os.environ)
        env.update({"GIT_AUTHOR_DATE": "2026-02-02T00:00:00 +0000",
                    "GIT_COMMITTER_DATE": "2026-02-02T00:00:00 +0000"})
        subprocess.run(["git", "add", "-A"], cwd=wt, check=True)
        subprocess.run(
            ["git", "-c", "user.email=fixture@example.test",
             "-c", "user.name=fixture", "commit", "-qm",
             "diverge the pinned skill file"],
            cwd=wt, check=True, env=env)
        out = self.run_render("baseline-rel.json", cwd=wt)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("OUTCOME: pass", out.stdout)
        # a relative output path resolves against the primary checkout, not
        # the invocation cwd
        self.assertFalse((wt / "baseline-rel.json").exists())
        payload = json.loads(
            (self.repo / "baseline-rel.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["write_home"],
                         str(self.repo / "baseline-rel.json"))
        self.assertEqual(payload["primary_checkout"], str(self.repo))
        # base-tip provenance: the primary checkout's branch tip, not the
        # diverging worktree branch's tip
        self.assertEqual(payload["base_tip"]["commit"],
                         self.git_out(self.repo, "rev-parse", "main"))
        self.assertNotEqual(payload["base_tip"]["commit"],
                            self.git_out(self.repo, "rev-parse", "wtbranch"))
        # the producers ran against the primary tree: the advisory breach
        # line carries the primary byte count (100, not the worktree's 120)
        # and every producer section matches the primary-tree render
        self.assertIn(RENDER_BREACH_LINE, self.captured(payload,
                                                        "skill_text_budget"))
        self.assertNotIn(
            "BREACH (advisory): agents/skills/done/SKILL.md 120 bytes > cap 10",
            self.captured(payload, "skill_text_budget"))
        self.assertEqual(self.normalize(payload)["producers"],
                         self.normalize(self.base)["producers"])


# --- Known-red baseline consumption witness (plan
# 2026-11-13-known-red-gates-consumed-baseline, Task 3). Content needles over
# the real registry row and the four pinned triage surfaces (Task 2's Files):
# the preamble surface carries the Done-when worktree claims (explicit-rooted
# primary-checkout resolution, matching-baseline pre-existing classification,
# the absent/unreadable/unavailable/stale fail-open arms, the snapshot-
# subordination span, and the pins-escalation carve-out span); the sweep
# surface owns the operative classification clause with the full carve-out
# predicate; the exec surface carries the two pointer placements; the survey
# surface carries the regeneration duty. A row-only landing (the registry row
# present with any pinned surface stripped) reds the run, and each failure
# message names the stripped surface and the missing needle. ---

KNOWN_RED_PREAMBLE_SURFACE = "agents/skills/review-agents/SKILL.md"

KNOWN_RED_PREAMBLE_NEEDLES = (
    "**Known-red baseline preamble:**",
    "baseline-known-red-gates.json",
    # explicit-rooted primary-checkout resolution (the home authority)
    "explicit-rooted in the primary checkout's maintenance state home",
    "maintenance_state_dir",
    ".ai-playbook/maintenance/",
    "git worktree list --porcelain",
    # matching-baseline pre-existing classification
    "as pre-existing with its baseline pointer",
    # snapshot-subordination span
    "subordinated to the render-time snapshot: live producer output wins "
    "and the pins-escalation carve-out wins",
    # pins-escalation carve-out span
    "a failing-pin line the pins run itself escalates stays actionable "
    "regardless of baseline membership",
    # unknown reds actionable (the classification's negative arm)
    "(an unknown red) stays fully actionable",
    # fail-open arms: absent, unreadable, stale, unavailable
    "absent or unreadable the preamble is omitted whole",
    "stale (its recorded controlling-input digest no longer matches the "
    "producer's current tracked inputs)",
    "unavailable (the render recorded the producer as failed to run, "
    "timed out, or terminated without its expected output)",
    # citation by reference to the operative classification home
    "agents/skills/plans/plan-quality-gate.md",
    "the operative classification home",
    "cited by reference",
    # the placement marker owning-layer note
    "<!-- portability: abstract -->",
)

KNOWN_RED_SWEEP_SURFACE = "agents/skills/plans/plan-quality-gate.md"

KNOWN_RED_SWEEP_NEEDLES = (
    "Known-red baseline classification (pre-review text-policy sweep "
    "clause; the operative classification home)",
    "binds every producer-reading surface",
    "agents/skills/execute-plan/implementation-loop.md",
    "baseline-known-red-gates.json",
    "resolved explicit-rooted in the primary checkout's maintenance state "
    "home",
    "maintenance_state_dir",
    ".ai-playbook/maintenance/",
    "git worktree list --porcelain",
    # matching-baseline pre-existing classification
    "Each baseline-listed line classifies pre-existing with its baseline "
    "pointer",
    # the carve-out's escalation predicate (exit-effect keyed)
    "except a failing-pin line the pins run itself escalates (the "
    "pins-escalation carve-out, exit-effect keyed",
    "a plain `PIN FAIL` or lowercase `pin fail:` line",
    "keep their baseline classification",
    "scripts/gate_liveness_ledger.json` against the system date",
    "exact string equality",
    "`PIN RECORDED RED EXPIRED`",
    "`PIN RECORDED RED MALFORMED`",
    "a failing line matching no register entry",
    "a recorded-shaped line the re-read cannot confirm",
    "Every unmatched line stays actionable, and no exit code changes",
    # fail-open arms: absent, unreadable, unavailable, stale
    "when the file is absent or unreadable",
    "digest no longer matches the producer's current tracked inputs, "
    "re-derived from the primary checkout's working-tree bytes",
)

KNOWN_RED_EXEC_SURFACE = (
    "agents/skills/execute-plan/implementation-loop.md")

KNOWN_RED_EXEC_NEEDLES = (
    # Step 1.4 verification gate placement
    "classify per the known-red baseline classification clause in "
    "`agents/skills/plans/plan-quality-gate.md`'s pre-review text-policy "
    "sweep (the operative classification home, cited by reference; "
    "fail-open)",
    # Phase 2 fresh-run placement
    "classify per the same known-red baseline classification clause",
    "with no second pointer",
)

KNOWN_RED_SURVEY_SURFACE = "agents/skills/maintenance/survey-arms.md"

KNOWN_RED_SURVEY_NEEDLES = (
    "regenerates the known-red gate baseline",
    "--render-baseline <resolved-home>/baseline-known-red-gates.json",
    "explicit-rooted in the primary checkout's maintenance state home",
    "maintenance_state_dir",
    ".ai-playbook/maintenance/",
    "git worktree list --porcelain",
    "the render runs the three producers against the primary checkout's "
    "tree",
    "never a blocked turn",
)


class RegistryContentWitnessKnownRedBaseline(unittest.TestCase):
    """Content witness for the known-red gate baseline's protocol row (plan
    2026-11-13-known-red-gates-consumed-baseline, Task 3): the real
    registry's row carries the named machinery admission fields with its
    witness at the covering plan's living path and its pre-registered
    removals row, and each of the four pinned triage surfaces carries its
    landed consumption clause, so the battery distinguishes the prescribed
    row-plus-surface landing from a row-only landing (a row landing without
    the surface text reds the run) and from a thinned row. Expected GREEN
    at landing; reds when the row is dropped, its admission fields are
    thinned, or any of the four pinned skill surfaces is stripped."""

    ROW_ID = "protocol:known-red-gates-baseline"
    # the citation rule's re-point form: the living covering plan at this
    # landing, its docs/history/plans/completed/ twin after the note's
    # re-point duty executes at the plan-family completion fold (the
    # duty:carrier-liveness-zero-turn precedent).
    ALLOWED_WITNESS_REFS = {
        "docs/history/plans/2026-11-13-known-red-gates-consumed-baseline.md",
        "docs/history/plans/completed/"
        "2026-11-13-known-red-gates-consumed-baseline.md",
    }

    def setUp(self):
        root = Path(__file__).parent.parent
        if not (root / ".git").exists():
            self.skipTest("not run from a repository checkout")
        self.root = root
        self.registry = json.loads(
            (root / "scripts" / "machinery_registry.json").read_text(
                encoding="utf-8"))

    def admission_row(self):
        rows = [e for e in self.registry.get("entries", [])
                if e.get("id") == self.ROW_ID]
        self.assertEqual(
            len(rows), 1,
            "the known-red gate baseline's protocol row is missing")
        return rows[0]

    def removals_row(self):
        rows = [e for e in self.registry.get("removals", [])
                if e.get("id") == self.ROW_ID]
        self.assertEqual(
            len(rows), 1,
            "the known-red gate baseline's pre-registered removals row "
            "is missing")
        return rows[0]

    def assert_surface(self, rel, needles):
        text = (self.root / rel).read_text(encoding="utf-8")
        for needle in needles:
            self.assertIn(needle, text,
                          "%s stripped: missing needle: %r" % (rel, needle))

    def test_row_structure_matches_the_prescribed_shape(self):
        row = self.admission_row()
        self.assertEqual(row["disposition"], "keep")
        self.assertEqual(row["kind"], "protocol")
        # claim-if-concurrent: the four triage surfaces and the render mode
        # stay owned by their standing registry rows.
        self.assertEqual(row["paths"], [])
        self.assertEqual(row["witness"]["class"], "incident")
        self.assertIn(row["witness"]["ref"], self.ALLOWED_WITNESS_REFS)
        self.assertEqual(self.removals_row()["disposition"], "delete")
        self.assertEqual(self.removals_row()["paths"], [])

    def test_note_carries_the_named_admission_fields(self):
        note = self.admission_row().get("note") or ""
        needles = (
            # the landed artifact and its covering plan
            "baseline-known-red-gates.json",
            "docs/history/plans/"
            "2026-11-13-known-red-gates-consumed-baseline.md",
            # concrete incident link: the origin row and its instances
            "docs/history/backlog/"
            "2026-11-10-known-red-gates-retriage-tax.md",
            "five 2026-11-09/10 re-triage instances",
            # expected catch frequency
            "every multi-worker round while pins red",
            # false-positive cost, re-priced under the digest design
            "a re-render without review absorbs newly introduced reds as "
            "pre-existing until the next review",
            "re-priced under the digest design",
            "the origin's field prices stale-masking",
            # landing posture
            "fail-open",
            # review date
            "review date 2026-12-10",
            # the witness re-point duty to the completed twin
            "Witness re-point duty",
            "docs/history/plans/completed/"
            "2026-11-13-known-red-gates-consumed-baseline.md",
            "plan-family completion fold",
            "duty:carrier-liveness-zero-turn",
        )
        for needle in needles:
            self.assertIn(needle, note, "missing admission field: " + needle)

    def test_removals_row_pre_registers_the_sunset(self):
        note = self.removals_row().get("note") or ""
        for needle in (
            "2026-12-10",
            "co-removal set",
            "docs/history/plans/completed/"
            "2026-11-13-known-red-gates-consumed-baseline.md",
            "plan-family completion fold",
            "duty:carrier-liveness-zero-turn",
        ):
            self.assertIn(needle, note,
                          "removals row thinned: missing needle: %r" % needle)

    def test_preamble_surface_carries_the_landed_claims(self):
        self.assert_surface(KNOWN_RED_PREAMBLE_SURFACE,
                            KNOWN_RED_PREAMBLE_NEEDLES)

    def test_sweep_surface_carries_the_landed_claims(self):
        self.assert_surface(KNOWN_RED_SWEEP_SURFACE, KNOWN_RED_SWEEP_NEEDLES)

    def test_exec_surface_carries_the_pointer_binding(self):
        self.assert_surface(KNOWN_RED_EXEC_SURFACE, KNOWN_RED_EXEC_NEEDLES)

    def test_survey_surface_carries_the_regeneration_duty(self):
        self.assert_surface(KNOWN_RED_SURVEY_SURFACE,
                            KNOWN_RED_SURVEY_NEEDLES)


def load_tests(loader, tests, pattern):
    """Pattern-aware selection pin (plan 2026-10-02-machinery-realtree-arm-run-mode,
    Task 1): under unittest DISCOVERY (pattern set) all arms load, preserving
    discovery's today-semantics; under the documented default invocation
    (pattern unset) only the fixture arm runs, pinning it to exactly the
    pre-render 24 tests (the real-tree, content-witness, and render-baseline
    arms are the discovery and pytest extras; the render arm joined the
    discovery arm per plan 2026-11-13-known-red-gates-consumed-baseline,
    Task 1, and the known-red consumption witness class joined per the same
    plan's Task 3, and the post-fire census content witness class joined per
    plan 2026-11-14-post-fire-verification-arm-zero-executions Task 3, so the
    required inventory run collects them)."""
    fixture = loader.loadTestsFromTestCase(MachineryInventoryTest)
    realtree = loader.loadTestsFromTestCase(RealTreeCheck)
    content = loader.loadTestsFromTestCase(RegistryContentWitness)
    zero_turn = loader.loadTestsFromTestCase(RegistryContentWitnessZeroTurnCensus)
    post_fire = loader.loadTestsFromTestCase(RegistryContentWitnessPostFireCensus)
    render = loader.loadTestsFromTestCase(RenderBaselineTest)
    known_red = loader.loadTestsFromTestCase(
        RegistryContentWitnessKnownRedBaseline)
    if pattern:
        return unittest.TestSuite([fixture, realtree, content, zero_turn,
                                   post_fire, render, known_red])
    return fixture


if __name__ == "__main__":
    if "--real-tree" in sys.argv:
        sys.argv.remove("--real-tree")
        unittest.main(argv=[sys.argv[0], "RealTreeCheck"])
    else:
        unittest.main()
