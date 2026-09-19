#!/usr/bin/env python3
"""Hermetic tests for the live-signal harness detection seam.

Every test injects the environment and the ancestry probe: no real process
tree and no real home is consulted, so the suite passes on any host.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_detection


def foreign_env() -> dict:
    return {"CURSOR_INVOKED_AS": "agent"}


def codex_chain() -> list:
    return ["zsh", "codex exec plan X", "launchd"]


class HarnessDetectionTest(unittest.TestCase):
    def test_zcode_env_signal(self) -> None:
        self.assertEqual(
            harness_detection.detect_harness({"ZCODE_APP_VERSION": "3.12.3"}, ancestry=lambda: []),
            ("zcode", "env"),
        )

    def test_zcode_env_family_fallback(self) -> None:
        # The family, not one key, is the signal: ZCODE_BASE_URL alone detects.
        self.assertEqual(
            harness_detection.detect_harness({"ZCODE_BASE_URL": "https://api.z.ai"}, ancestry=lambda: []),
            ("zcode", "env"),
        )

    def test_codex_ancestry_signal(self) -> None:
        self.assertEqual(
            harness_detection.detect_harness({}, ancestry=codex_chain),
            ("codex", "ancestry"),
        )

    def test_codex_ancestry_matches_basename_only(self) -> None:
        # The word codex in a non-executable argument is not a codex ancestor:
        # matching is on the first token's basename.
        chain = ["zcode --resume codex-notes", "launchd"]
        self.assertEqual(
            harness_detection.detect_harness({}, ancestry=lambda: chain),
            (None, "none"),
        )

    def test_env_signal_precedence_over_ancestry(self) -> None:
        # Documented precedence: environment first.
        self.assertEqual(
            harness_detection.detect_harness({"ZCODE_APP_VERSION": "3.12.3"}, ancestry=codex_chain),
            ("zcode", "env"),
        )

    def test_codex_ancestry_when_env_foreign(self) -> None:
        self.assertEqual(
            harness_detection.detect_harness(foreign_env(), ancestry=codex_chain),
            ("codex", "ancestry"),
        )

    def test_unsupported_harness_env(self) -> None:
        harness, method = harness_detection.detect_harness(
            {"CURSOR_INVOKED_AS": "agent", "CLAUDECODE": "1"}, ancestry=lambda: []
        )
        self.assertIsNone(harness)
        self.assertEqual(method, "none")

    def test_no_signal_at_all(self) -> None:
        self.assertEqual(
            harness_detection.detect_harness({}, ancestry=lambda: []),
            (None, "none"),
        )

    def test_ancestry_depth_bound_inclusive(self) -> None:
        # The bound is at most six ancestors scanned (inclusive), documented
        # next to ANCESTRY_DEPTH_BOUND in harness_detection.py.
        six_deep = ["filler-1", "filler-2", "filler-3", "filler-4", "filler-5", "codex"]
        seven_deep = ["filler-1", "filler-2", "filler-3", "filler-4", "filler-5", "filler-6", "codex"]
        self.assertEqual(
            harness_detection.detect_harness({}, ancestry=lambda: six_deep),
            ("codex", "ancestry"),
        )
        self.assertEqual(
            harness_detection.detect_harness({}, ancestry=lambda: seven_deep),
            (None, "none"),
        )

    def test_cli_prints_json(self) -> None:
        # Injected environment AND injected ancestry (the seam resolves
        # _default_ancestry at call time, so patching it keeps the suite
        # hermetic even when the host's real ancestry carries a codex
        # basename): the module run as a script prints one JSON line whose
        # harness value is the literal string "none" (the token the skill
        # predicates match on, not JSON null) plus method and evidence keys,
        # and exits 0.
        injected = {"PATH": os.environ.get("PATH", ""), "HOME": "/nonexistent"}
        script_dir = str(Path(harness_detection.__file__).resolve().parent)
        runner = (
            "import sys; sys.path.insert(0, {0!r});"
            "import harness_detection as h;"
            "h._default_ancestry = lambda: [];"
            "sys.exit(h.main())"
        ).format(script_dir)
        result = subprocess.run(
            [sys.executable, "-c", runner],
            capture_output=True,
            text=True,
            env=injected,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["harness"], "none")
        self.assertEqual(payload["method"], "none")
        self.assertIn("no supported live signal", payload["evidence"])


class DefaultAncestryWalkTest(unittest.TestCase):
    """Exercise the REAL default walk code via a fixture ps on PATH."""

    def _run_with_fixture_ps(self, canned_line: str):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_dir = Path(tmpdir)
            ps = fixture_dir / "ps"
            ps.write_text("#!/bin/sh\nprintf '%s\\n' \"$PS_FIXTURE_LINE\"\n")
            ps.chmod(0o755)
            env = dict(os.environ)
            env["PATH"] = str(fixture_dir) + os.pathsep + env.get("PATH", "")
            env["PS_FIXTURE_LINE"] = canned_line
            with mock.patch.dict(os.environ, env, clear=True):
                return harness_detection._default_ancestry()

    def test_default_ancestry_walk_detects_codex(self) -> None:
        # The canned ps answers a parent chain containing a codex basename;
        # the DEFAULT walk (no injectable callable passed, both in the raw
        # walk and inside detect_harness) must find it through the real
        # ps-parsing code.
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_dir = Path(tmpdir)
            ps = fixture_dir / "ps"
            ps.write_text("#!/bin/sh\nprintf '%s\\n' \"$PS_FIXTURE_LINE\"\n")
            ps.chmod(0o755)
            env = dict(os.environ)
            env["PATH"] = str(fixture_dir) + os.pathsep + env.get("PATH", "")
            env["PS_FIXTURE_LINE"] = "  1 codex exec plan X"
            with mock.patch.dict(os.environ, env, clear=True):
                chain = harness_detection._default_ancestry()
                self.assertEqual(
                    harness_detection.detect_harness({}),
                    ("codex", "ancestry"),
                )
        self.assertTrue(any(c.split()[0].endswith("codex") for c in chain))

    def test_default_ancestry_walk_empty_chain(self) -> None:
        chain = self._run_with_fixture_ps("")
        harness, method = harness_detection.detect_harness({}, ancestry=lambda: chain)
        self.assertIsNone(harness)
        self.assertEqual(method, "none")
        self.assertEqual(chain, [])
        self.assertIn("no supported live signal", harness_detection._evidence("none"))


if __name__ == "__main__":
    unittest.main()
