"""Hermetic tests for check-no-em-dash.sh added-lines mode and usage text.

Each AddedLinesModeTest case builds its own throwaway git repository in a
temporary directory; no fixture lives outside tmp and nothing touches the
network. Git configuration is isolated from the host (system and global
config are pointed at the null device) so the results depend only on this
script's behavior.
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "check-no-em-dash.sh"

# Isolate git from host configuration; strip ambient repo pointers so the
# temporary directory is the only repository these tests can touch.
_HERMETIC_ENV = {
    key: value
    for key, value in os.environ.items()
    if key not in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE")
}
_HERMETIC_ENV.update(
    {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
    }
)

UNMATCHED_MESSAGE = "pathspec matches no tracked file"


class AddedLinesModeTest(unittest.TestCase):
    """added-lines mode behavior against a throwaway git repository."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="em-dash-added-lines-")
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name)
        self._git("init", "-q")
        self._git("config", "user.name", "em-dash-test")
        self._git("config", "user.email", "em-dash-test@example.invalid")
        (self.repo / "tracked.md").write_text("clean line\n", encoding="utf-8")
        self._git("add", "tracked.md")
        self._git("commit", "-q", "-m", "seed tracked file")

    def _git(self, *args):
        subprocess.run(
            ["git", *args],
            cwd=self.repo,
            env=_HERMETIC_ENV,
            check=True,
            capture_output=True,
            text=True,
        )

    def _run_added_lines(self, *args):
        return subprocess.run(
            ["bash", str(SCRIPT), "added-lines", *args],
            cwd=self.repo,
            env=_HERMETIC_ENV,
            capture_output=True,
            text=True,
        )

    def test_unmatched_pathspec_aborts_non_zero(self):
        result = self._run_added_lines("--base", "HEAD", "does-not-exist.md")
        self.assertNotEqual(
            result.returncode,
            0,
            "an unmatched pathspec must never read as clean (exit 0)",
        )
        self.assertIn(UNMATCHED_MESSAGE, result.stderr)
        self.assertIn("does-not-exist.md", result.stderr)

    def test_matched_path_with_no_diff_exits_zero(self):
        result = self._run_added_lines("--base", "HEAD", "tracked.md")
        self.assertEqual(
            result.returncode,
            0,
            "the guard must not false-abort a legitimate tracked pathspec",
        )
        self.assertEqual(result.stdout, "")

    def test_untracked_pathspec_aborts_non_zero(self):
        # Real file, never tracked: the mode cannot scan it, so aborting is
        # intended and must not later be relaxed back to warn-and-continue.
        (self.repo / "untracked.md").write_text("never added\n", encoding="utf-8")
        result = self._run_added_lines("--base", "HEAD", "untracked.md")
        self.assertEqual(result.returncode, 2)
        self.assertIn(UNMATCHED_MESSAGE, result.stderr)
        self.assertIn("untracked.md", result.stderr)

    def test_added_em_dash_line_reported(self):
        (self.repo / "tracked.md").write_text(
            "clean line\nhas an em dash — here\n",
            encoding="utf-8",
        )
        result = self._run_added_lines("--base", "HEAD", "tracked.md")
        self.assertEqual(result.returncode, 1)
        self.assertIn("tracked.md:2:", result.stdout)

    def test_long_form_base_and_separator_accepted(self):
        (self.repo / "tracked.md").write_text(
            "clean line\nhas an em dash — here\n",
            encoding="utf-8",
        )
        short_form = self._run_added_lines("--base", "HEAD", "tracked.md")
        long_form = self._run_added_lines("--base=HEAD", "tracked.md")
        separator = self._run_added_lines("--base", "HEAD", "--", "tracked.md")
        for name, result in (("long form", long_form), ("separator", separator)):
            self.assertEqual(
                result.returncode,
                short_form.returncode,
                f"{name} must match the short-form exit status",
            )
            self.assertEqual(
                result.stdout,
                short_form.stdout,
                f"{name} must match the short-form report",
            )


class UsageTextTest(unittest.TestCase):
    """The usage text documents the implemented argument forms."""

    def test_usage_documents_long_form_and_separator(self):
        result = subprocess.run(
            ["bash", str(SCRIPT), "--help"],
            cwd=tempfile.gettempdir(),
            env=_HERMETIC_ENV,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        usage = result.stdout
        self.assertIn("--base=REF", usage)
        self.assertIn(
            "added-lines [--base REF] [--base=REF] [--] [paths...]",
            usage,
            "the added-lines row must document the long form and the -- separator",
        )


if __name__ == "__main__":
    unittest.main()
