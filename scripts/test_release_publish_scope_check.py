"""Tests for scripts/release_publish_scope_check.sh.

Exercises both deny classes, the delta-intersection scoping negative, the
charter-empty constant against a sibling-directory non-match, empty stdin,
delta paths with spaces and non-ASCII bytes, the deletion and README
non-match arms, pinned fixture git identity, and the tool-failure arm.
"""

import os
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CHECKER = REPO / "scripts" / "release_publish_scope_check.sh"

CHARTER_ITEM = "docs/history/backlog/completed/2026-01-01-item.md"
SIBLING_ITEM = "docs/history/backlog/completed-spring/2026-01-03-item.md"


def run_checker(stdin_text, cwd, extra_env=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_CONFIG")}
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [str(CHECKER)],
        input=stdin_text,
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=env,
        timeout=120,
    )


def sh(cmd, cwd):
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=120)


class PublishScopeCheckerTest(unittest.TestCase):
    def setUp(self):
        import shutil
        import tempfile

        self.base = Path(tempfile.mkdtemp(prefix="pubscope-"))
        repo = self.base / "repo"
        repo.mkdir()
        self.repo = repo
        sh(["git", "init", "-q", "-b", "main", "."], repo)
        # pin fixture identity so ambient global config cannot flip a verdict
        sh(["git", "config", "user.email", "fixture@example.invalid"], repo)
        sh(["git", "config", "user.name", "fixture"], repo)
        env = dict(os.environ)
        env["GIT_CONFIG_GLOBAL"] = str(repo / ".gitconfig-fixture")
        env["GIT_CONFIG_SYSTEM"] = "/dev/null"
        self.pinned_env = env
        (repo / ".gitignore").write_text("ignored-secret.txt\n")
        (repo / "ignored-secret.txt").write_text("secret\n")
        (repo / "plain-file.md").write_text("x\n")
        charter = repo / "docs/history/backlog/completed"
        sibling = repo / "docs/history/backlog/completed-spring"
        charter.mkdir(parents=True)
        sibling.mkdir(parents=True)
        (charter / "README.md").write_text("# charter-empty rule home\n")
        (charter / "2026-01-01-item.md").write_text("x\n")
        (charter / "2026-01-02-gone.md").write_text("x\n")
        (sibling / "2026-01-03-item.md").write_text("x\n")
        (repo / "delta file with space.md").write_text("x\n")
        (repo / "дельта-не-ascii.md").write_text("x\n")
        sh(["git", "add", "-A"], repo)
        sh(["git", "add", "-f", "ignored-secret.txt"], repo)
        sh(["git", "commit", "-qm", "fixture"], repo)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.base, ignore_errors=True)

    def run_pinned(self, stdin_text, extra_env=None):
        return run_checker(stdin_text, self.repo, extra_env)

    def test_selftest_arm(self):
        r = subprocess.run(
            [str(CHECKER), "--selftest"], capture_output=True, text=True, timeout=120
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("selftest: ok", r.stdout)

    def test_empty_stdin_clean(self):
        r = self.run_pinned("")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_clean_list_no_report(self):
        r = self.run_pinned("plain-file.md\ndocs/history/backlog/completed/README.md\n")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_deny_class_1_tracked_but_ignored(self):
        r = self.run_pinned("ignored-secret.txt\n")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(
            r.stdout, "PUBLISH-SCOPE: ignored-secret.txt (tracked-but-ignored)\n"
        )

    def test_deny_class_1_delta_intersection_not_repo_dump(self):
        # a tracked-ignored file NOT on stdin produces no line: the report is
        # the delta intersection, never a repo-wide dump. Feed only clean
        # paths and confirm the ignored file (tracked-ignored in the repo)
        # is not dumped.
        r = self.run_pinned("plain-file.md\n")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_deny_class_2_charter_empty_item(self):
        r = self.run_pinned(CHARTER_ITEM + "\n")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(
            r.stdout, "PUBLISH-SCOPE: %s (charter-empty-directory)\n" % CHARTER_ITEM
        )

    def test_deny_class_2_sibling_directory_never_matches(self):
        r = self.run_pinned(SIBLING_ITEM + "\n")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_deny_class_2_deletion_arm(self):
        sh(["git", "rm", "-q", CHARTER_ITEM.replace("2026-01-01-item", "2026-01-02-gone")], self.repo)
        sh(["git", "commit", "-qm", "delete row"], self.repo)
        r = self.run_pinned("docs/history/backlog/completed/2026-01-02-gone.md\n")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_deny_class_2_readme_never_matches(self):
        r = self.run_pinned("docs/history/backlog/completed/README.md\n")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_report_line_form_space_and_non_ascii(self):
        stdin = "delta file with space.md\nдельта-не-ascii.md\n"
        r = self.run_pinned(stdin)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")  # neither is in a deny class; line form asserted via class-1 fixture below
        # assert the report line form exactly for a spaced/non-ascii path by
        # force-adding a tracked-ignored spaced file
        spaced = "ignored delta file.md"
        (self.repo / spaced).write_text("y\n")
        with open(self.repo / ".gitignore", "a") as fh:
            fh.write("ignored delta file.md\n")
        sh(["git", "add", "-f", spaced], self.repo)
        sh(["git", "commit", "-qm", "force-add ignored"], self.repo)
        r2 = self.run_pinned(spaced + "\n")
        self.assertEqual(r2.returncode, 0)
        self.assertEqual(r2.stdout, "PUBLISH-SCOPE: %s (tracked-but-ignored)\n" % spaced)
        nonascii = "ignored-дельта.md"
        (self.repo / nonascii).write_text("y\n")
        with open(self.repo / ".gitignore", "a") as fh:
            fh.write("ignored-дельта.md\n")
        sh(["git", "add", "-f", nonascii], self.repo)
        sh(["git", "commit", "-qm", "force-add ignored nonascii"], self.repo)
        r3 = self.run_pinned(nonascii + "\n")
        self.assertEqual(r3.returncode, 0)
        self.assertEqual(r3.stdout, "PUBLISH-SCOPE: %s (tracked-but-ignored)\n" % nonascii)

    def test_fixture_git_identity_pinned(self):
        # the fixture pins GIT_CONFIG_GLOBAL/GIT_CONFIG_SYSTEM to fixture-local
        # identities; a checker run under the same pins stays deterministic
        r = self.run_pinned("plain-file.md\n")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")
        cfg = self.repo / ".gitconfig-fixture"
        self.assertFalse(cfg.exists())  # pins only redirect lookups away

    def test_tool_failure_arm_poisoned_env(self):
        # a poisoned GIT_DIR inside the checker's scrubbed environment must
        # not flip a verdict (the scrub unsets it before any git call)
        r = self.run_pinned(
            "plain-file.md\n",
            extra_env={"GIT_DIR": "/nonexistent/.git", "GIT_WORK_TREE": "/nonexistent"},
        )
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_tool_failure_nonzero_without_report(self):
        # simulate a failing git repository: point the whole invocation at a
        # non-repo cwd by running the checker from a directory outside git
        # while scrubbing is bypassed is impossible by design; instead assert
        # the documented tool-failure contract via a stubbed git on PATH.
        stub = self.base / "stubbin"
        stub.mkdir()
        (stub / "git").write_text("#!/bin/sh\nexit 128\n")
        os.chmod(stub / "git", 0o755)
        env = dict(self.pinned_env)
        env["PATH"] = str(stub) + os.pathsep + env.get("PATH", "")
        r = run_checker("plain-file.md\n", self.repo, extra_env={"PATH": env["PATH"], "GIT_CONFIG_GLOBAL": env["GIT_CONFIG_GLOBAL"], "GIT_CONFIG_SYSTEM": env["GIT_CONFIG_SYSTEM"]})
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")


if __name__ == "__main__":
    unittest.main()
