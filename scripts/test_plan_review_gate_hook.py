"""Regression tests for agents/hooks/plan-review-gate/check-plan-review-gate.sh.

Each case runs the versioned script in a throwaway git repo, with HOME and
GIT_CONFIG_GLOBAL pointed at a temp dir, explicit fixture mtimes, and the
candidate listing in both orders (a stub `find` first on PATH).
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "agents/hooks/plan-review-gate/check-plan-review-gate.sh"
READY = "Verdict: ready=yes\n"
NOGO = "Verdict: No-Go\n"
DATE = "2026-11-20"
BASE_NS = 1_700_000_000 * 10**9
STEP_NS = 10 * 10**9


def plan_review(slug, n, token=""):
    return f"{DATE}-plan-review-{slug}{token}-r{n}.md"


class HookCase(unittest.TestCase):
    def run_hook(self, plan_name, reviews, order, extra_files=()):
        """reviews: list of (name, content, mtime_offset_steps). Returns (code, stderr)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            home = tmp / "home"
            home.mkdir()
            repo = tmp / "repo"
            repo.mkdir()
            env = {
                "HOME": str(home),
                "GIT_CONFIG_GLOBAL": str(home / "gitconfig"),
                "PATH": os.environ["PATH"],
            }
            git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], env=env, check=True, capture_output=True)
            git("init", "-q")
            git("config", "user.email", "t@example.com")
            git("config", "user.name", "t")
            plan = repo / "docs/plans" / plan_name
            plan.parent.mkdir(parents=True)
            plan.write_text("# plan\n")
            git("add", "docs/plans/" + plan_name)
            rdir = repo / ".ai-playbook/reviews"
            rdir.mkdir(parents=True)
            for name, content, off in list(reviews) + list(extra_files):
                f = rdir / name
                f.write_text(content)
                ns = BASE_NS + off * STEP_NS
                os.utime(f, ns=(ns, ns))
            stub = tmp / "stub"
            stub.mkdir()
            real_find = shutil.which("find")
            flag = "-r" if order == "reverse" else ""
            (stub / "find").write_text(f'#!/bin/sh\n{real_find} "$@" | sort {flag}\n')
            (stub / "find").chmod(0o755)
            env["PATH"] = f"{stub}:{env['PATH']}"
            payload = json.dumps({"tool_input": {"command": "git commit -m x"}})
            p = subprocess.run(
                ["bash", str(HOOK)], input=payload, text=True, capture_output=True, env=env, cwd=repo
            )
            return p.returncode, p.stderr

    def both(self, plan_name, reviews, expect_block, needle=None):
        for order in ("forward", "reverse"):
            code, err = self.run_hook(plan_name, reviews, order)
            with self.subTest(order=order):
                self.assertEqual(code, 2 if expect_block else 0, err)
                if needle:
                    self.assertIn(needle, err)


class RoundSelection(HookCase):
    def test_tie_higher_round_ready_allows(self):
        self.both("x.md", [(plan_review("x", 13), NOGO, 0), (plan_review("x", 14), READY, 0)], False)

    def test_tie_higher_round_nogo_blocks(self):
        self.both("x.md", [(plan_review("x", 13), READY, 0), (plan_review("x", 14), NOGO, 0)], True)

    def test_older_mtime_higher_round_nogo_blocks(self):
        self.both("x.md", [(plan_review("x", 13), READY, 1), (plan_review("x", 14), NOGO, 0)], True)

    def test_numeric_not_lexical(self):
        self.both("x.md", [(plan_review("x", 9), NOGO, 2), (plan_review("x", 10), READY, 0)], False)
        self.both("x.md", [(plan_review("x", 10), NOGO, 0), (plan_review("x", 9), READY, 2)], True)

    def test_same_number_tie_break_by_basename(self):
        a, b = plan_review("x", 5, "-p0000000a"), plan_review("x", 5, "-p0000000b")
        self.both("x.md", [(a, READY, 0), (b, NOGO, 0)], True, needle=b)
        self.both("x.md", [(a, NOGO, 0), (b, READY, 0)], False)

    def test_non_plan_review_rounds_never_decide(self):
        extras = [
            (f"{DATE}-code-review-x-r6.md", NOGO, 2),
            (f"{DATE}-exec-review-x-r7.md", NOGO, 3),
        ]
        for order in ("forward", "reverse"):
            code, err = self.run_hook("x.md", [(plan_review("x", 3), READY, 0)], order, extras)
            self.assertEqual(code, 0, err)
        for order in ("forward", "reverse"):
            code, err = self.run_hook(
                "x.md", [(plan_review("x", 2), NOGO, 0)], order, [(f"{DATE}-exec-review-x-r3.md", READY, 2)]
            )
            self.assertEqual(code, 2, err)

    def test_slug_boundaries(self):
        longer = [(plan_review("foo", 1), READY, 0), (plan_review("foo-bar", 9), NOGO, 2)]
        self.both("foo.md", longer, False)
        mid = [(plan_review("foo", 1), READY, 0), (f"{DATE}-code-review-plan-review-foo-r4.md", NOGO, 2)]
        self.both("foo.md", mid, False)

    def test_date_and_story_key_prefix_kept_in_review_name(self):
        self.both(f"{DATE}-p65-x.md", [(f"{DATE}-plan-review-{DATE}-p65-x-r2.md", NOGO, 0)], True)
        self.both("RCD-9-x.md", [(f"{DATE}-plan-review-rcd-9-x-r1.md", NOGO, 0)], True)

    def test_variants_ignored(self):
        rows = [
            (plan_review("x", 3), READY, 0),
            (plan_review("x", 2) + ".backup-20261120", NOGO, 2),
            (plan_review("x", 3) + ".wt-1", NOGO, 2),
        ]
        rows[1] = (f"{DATE}-plan-review-x-r2.md.backup-20261120.md", NOGO, 2)
        rows[2] = (f"{DATE}-plan-review-x-r3.wt-1.md", NOGO, 2)
        self.both("x.md", rows, False)


class NoArtifactAndPreservation(HookCase):
    def test_only_code_review_gives_warning_and_allow(self):
        self.both("x.md", [(f"{DATE}-code-review-x-r1.md", NOGO, 0)], False, needle="no review artifact")

    def test_only_non_canonical_variants_gives_warning(self):
        self.both("x.md", [(f"{DATE}-plan-review-x-r2.md.backup-1.md", NOGO, 0)], False, needle="no review artifact")

    def test_no_staged_plan_allows(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {"HOME": tmp, "GIT_CONFIG_GLOBAL": tmp + "/gc", "PATH": os.environ["PATH"]}
            subprocess.run(["git", "-C", tmp, "init", "-q"], env=env, check=True)
            payload = json.dumps({"tool_input": {"command": "git commit -m x"}})
            p = subprocess.run(["bash", str(HOOK)], input=payload, text=True, capture_output=True, env=env, cwd=tmp)
            self.assertEqual(p.returncode, 0, p.stderr)

    def test_other_repo_target_not_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            env = {"HOME": str(tmp), "GIT_CONFIG_GLOBAL": str(tmp / "gc"), "PATH": os.environ["PATH"]}
            for r in ("a", "b"):
                (tmp / r).mkdir()
                subprocess.run(["git", "-C", str(tmp / r), "init", "-q"], env=env, check=True)
            (tmp / "a/docs/plans").mkdir(parents=True)
            (tmp / "a/docs/plans/x.md").write_text("p\n")
            (tmp / "a/.ai-playbook/reviews").mkdir(parents=True)
            (tmp / "a/.ai-playbook/reviews" / plan_review("x", 1)).write_text(NOGO)
            subprocess.run(["git", "-C", str(tmp / "a"), "add", "."], env=env, check=True)
            payload = json.dumps({"tool_input": {"command": f"git -C {tmp / 'b'} commit -m x"}})
            p = subprocess.run(["bash", str(HOOK)], input=payload, text=True, capture_output=True, env=env, cwd=tmp / "a")
            self.assertEqual(p.returncode, 0, p.stderr)


if __name__ == "__main__":
    unittest.main()
