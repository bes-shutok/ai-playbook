#!/usr/bin/env python3
"""Extraction tests for the docs-branch skill's Step 2 selector block.

The suite extracts the live selector lines from the skill bytes by pinned
anchors and executes them under the host bash, so the shipped text is tested
rather than a copy. Covers:

- the empty-array-safe export gate (length form; empty array emits no warning
  and exports nothing, non-empty exports the space-joined value),
- the primary-arm helper resolution precedence (override, project, deployed
  home, canonical skills root) and the set-but-missing override fall-through,
- the loud refusal when no helper resolves under a primary declaration.

Skill root: agents/skills/docs-branch/SKILL.md relative to this script's repo.
"""

import os
import re
import shutil
import subprocess
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_PATH = os.path.join(
    REPO_ROOT, "agents", "skills", "docs-branch", "SKILL.md"
)

UNSAFE_TEST_LITERAL = '[ "${EXTRA_SHADOW_DIRS[@]+x}" = "x" ]'
LENGTH_TEST_LITERAL = 'if [ "${#EXTRA_SHADOW_DIRS[@]}" -gt 0 ]; then'
REFUSAL_LITERAL = (
    "docs-branch: worktree_policy = primary but no plumbing helper found"
)
WARN_FALLBACK_LITERAL = (
    "WARN: no-worktree plumbing script not found; falling back to the worktree path"
)

HELPER_NAME = "docs_branch_sync_noworktree.sh"
STUB_BODY = (
    "#!/bin/bash\n"
    'echo "HELPER-RAN:$0"\n'
    'echo "EXTRA:${DOCS_SYNC_EXTRA_SHADOW_DIRS-UNSET}"\n'
    "exit 0\n"
)

START_ANCHOR = 'DOCS_SYNC_MODE="worktree"'
END_ANCHOR = "^esac$"


def _skill_bytes():
    with open(SKILL_PATH, encoding="utf-8") as fh:
        return fh.read()


def _extract_selector_block():
    """Extract the live selector lines from the skill bytes by pinned anchors."""
    text = _skill_bytes()
    start = text.index(START_ANCHOR)
    start = text.rindex("\n", 0, start) + 1
    end_match = re.search(END_ANCHOR, text[start:], flags=re.MULTILINE)
    if end_match is None:
        raise AssertionError("selector end anchor (esac) not found in skill bytes")
    return text[start : start + end_match.end()]


def _write_stub_helper(directory):
    scripts = os.path.join(directory, "scripts")
    os.makedirs(scripts, exist_ok=True)
    helper = os.path.join(scripts, HELPER_NAME)
    with open(helper, "w", encoding="utf-8") as fh:
        fh.write(STUB_BODY)
    return helper


def sh_quote(value):
    return "'" + value.replace("'", "'\\''") + "'"


def _run_selector(
    extra_shadow_dirs,
    worktree_policy="primary",
    project_helper=False,
    deployed_helper=False,
    skills_root=False,
    override_helper=False,
    override_value=None,
):
    """Run the extracted selector block under the host bash in a temp layout.

    Returns (returncode, stdout, stderr, paths) where paths names the helpers
    the layout created (project / deployed / skills-root / override) so
    assertions can pin which one the selector picked.
    """
    block = _extract_selector_block()
    tmp = tempfile.mkdtemp(prefix="docs-selector-test-")
    paths = {}
    try:
        home = os.path.join(tmp, "home")
        os.makedirs(os.path.join(home, ".ai-playbook"))
        project = os.path.join(tmp, "project")
        os.makedirs(os.path.join(project, ".ai-playbook"))
        ord_top = os.path.join(tmp, "ord-top")
        os.makedirs(ord_top)
        if project_helper:
            paths["project"] = _write_stub_helper(ord_top)
        if deployed_helper:
            paths["deployed"] = _write_stub_helper(
                os.path.join(home, ".ai-playbook")
            )
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": home,
        }
        if override_value is not None:
            env["DOCS_BRANCH_SYNC_NOWORKTREE_SCRIPT"] = override_value
        elif override_helper:
            paths["override"] = _write_stub_helper(
                os.path.join(tmp, "override")
            )
            env["DOCS_BRANCH_SYNC_NOWORKTREE_SCRIPT"] = paths["override"]
        if skills_root:
            paths["skills-root"] = _write_stub_helper(
                os.path.join(tmp, "skills-root")
            )
            env["DOCS_BRANCH_SKILLS_ROOT"] = tmp + "/skills-root"
        with open(
            os.path.join(project, ".ai-playbook", "facts.md"),
            "w",
            encoding="utf-8",
        ) as fh:
            fh.write("```toml\nworktree_policy = \"%s\"\n```\n" % worktree_policy)

        script_path = os.path.join(tmp, "run_selector.sh")
        with open(script_path, "w", encoding="utf-8") as fh:
            fh.write("#!/bin/bash\nset -u\n")
            fh.write("EXTRA_SHADOW_DIRS=(%s)\n" % " ".join(extra_shadow_dirs))
            fh.write("DOCS_EXPLICIT_DELETES=()\n")
            # a sentinel entry: under set -u on bash 3.2 an empty array makes
            # the selector's ${SHADOW_PATHS[*]} expansion read as unbound
            fh.write('SHADOW_PATHS=("docs/")\n')
            fh.write('PLAN_GUARD_SCRIPT=""\n')
            fh.write('DEDUPE_SCRIPT=""\n')
            fh.write("_ORD_TOP=%s\n" % sh_quote(ord_top))
            fh.write(block)
        proc = subprocess.run(
            ["bash", script_path],
            cwd=project,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return proc.returncode, proc.stdout, proc.stderr, paths
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _selected_helper(stdout):
    """Parse the selected helper path from the mode-start echo line."""
    match = re.search(r"helper: (.+)\)$", stdout, flags=re.MULTILINE)
    return match.group(1) if match else None


class ExportGateTest(unittest.TestCase):
    def test_unsafe_literal_absent_post_change(self):
        self.assertEqual(
            _skill_bytes().count(UNSAFE_TEST_LITERAL),
            0,
            "the bare-array POSIX test literal must be gone from the skill bytes",
        )

    def test_length_literal_appears_once_in_primary_arm(self):
        self.assertEqual(
            _skill_bytes().count(LENGTH_TEST_LITERAL),
            1,
            "the replacement length-test literal must appear exactly once",
        )

    def test_empty_array_no_warning_no_export(self):
        rc, out, err, _ = _run_selector([], project_helper=True)
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")
        self.assertIn("EXTRA:UNSET", out)

    def test_nonempty_array_exports_space_joined(self):
        rc, out, err, _ = _run_selector(
            ["docs/personal/", "resources/source/"], project_helper=True
        )
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")
        self.assertIn("EXTRA:docs/personal/ resources/source/", out)


class ResolutionPrecedenceTest(unittest.TestCase):
    def test_override_beats_project(self):
        rc, out, err, paths = _run_selector(
            [], project_helper=True, override_helper=True
        )
        self.assertEqual(rc, 0)
        self.assertEqual(_selected_helper(out), paths["override"])
        self.assertIn("HELPER-RAN:%s" % paths["override"], out)

    def test_project_beats_deployed_home(self):
        rc, out, err, paths = _run_selector(
            [], project_helper=True, deployed_helper=True
        )
        self.assertEqual(rc, 0)
        self.assertEqual(_selected_helper(out), paths["project"])
        self.assertIn("HELPER-RAN:%s" % paths["project"], out)

    def test_deployed_home_beats_skills_root(self):
        rc, out, err, paths = _run_selector(
            [], deployed_helper=True, skills_root=True
        )
        self.assertEqual(rc, 0)
        self.assertEqual(_selected_helper(out), paths["deployed"])
        self.assertIn("HELPER-RAN:%s" % paths["deployed"], out)

    def test_skills_root_probed_only_when_set_and_when_earlier_missed(self):
        rc, out, err, paths = _run_selector([], skills_root=True)
        self.assertEqual(rc, 0)
        self.assertEqual(_selected_helper(out), paths["skills-root"])
        self.assertIn("HELPER-RAN:%s" % paths["skills-root"], out)

    def test_set_but_missing_override_falls_to_deployed_home(self):
        # the project helper is present but must be skipped: the project slot
        # applies only when the override is unset, so a set-but-missing
        # override lands on the deployed home even over an existing project
        # helper (the discriminating fixture for that edge pin)
        rc, out, err, paths = _run_selector(
            [],
            project_helper=True,
            deployed_helper=True,
            override_value="/nonexistent/docs_branch_sync_noworktree.sh",
        )
        self.assertEqual(rc, 0)
        self.assertEqual(_selected_helper(out), paths["deployed"])

    def test_selected_helper_path_echoed_at_mode_start(self):
        rc, out, err, paths = _run_selector([], project_helper=True)
        self.assertEqual(rc, 0)
        self.assertIn("helper: %s" % paths["project"], out)


class RefusalTest(unittest.TestCase):
    def test_primary_no_helper_anywhere_refuses_loudly(self):
        rc, out, err, _ = _run_selector([])
        self.assertNotEqual(rc, 0)
        self.assertIn(REFUSAL_LITERAL, err)
        self.assertIn("DOCS_BRANCH_SYNC_NOWORKTREE_SCRIPT", err)
        self.assertNotIn(WARN_FALLBACK_LITERAL, err)
        self.assertNotIn("sync mode: no-worktree plumbing", out)

    def test_warn_fallback_literal_absent_from_skill_bytes(self):
        self.assertEqual(_skill_bytes().count(WARN_FALLBACK_LITERAL), 0)

    def test_refusal_literal_in_failure_semantics_span(self):
        text = _skill_bytes()
        start = text.index("Failure semantics (sync):")
        line_end = text.find("\n", start)
        span = text[start : line_end if line_end != -1 else len(text)]
        self.assertIn(REFUSAL_LITERAL, span)
        self.assertIn("primary-arm helper refusal", span)


class WorktreeArmUntouchedTest(unittest.TestCase):
    def test_unconfigured_policy_keeps_worktree_path(self):
        rc, out, err, _ = _run_selector(
            [], worktree_policy="worktrees", project_helper=True
        )
        self.assertEqual(rc, 0)
        self.assertIn("sync mode: worktree", out)
        self.assertNotIn("plumbing", out)

    def test_unknown_policy_keeps_named_report_and_worktree_path(self):
        rc, out, err, _ = _run_selector(
            [], worktree_policy="exotic", project_helper=True
        )
        self.assertEqual(rc, 0)
        self.assertIn("outside the spelled set", err)
        self.assertIn("sync mode: worktree", out)


if __name__ == "__main__":
    unittest.main()
