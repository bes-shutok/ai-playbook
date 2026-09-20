#!/usr/bin/env python3
"""Tests for the certified-plan digest guard (docs_branch_plan_guard.py)."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent / "docs_branch_plan_guard.py"

FEATURE = "sync-guard-demo"
PLAN_NAME = f"2026-09-19-{FEATURE}.md"
PLANS_REL = Path("docs/plans")

CERTIFIED_TEXT = "# Plan: sync guard demo\n\nThe certified shape of the plan bytes.\n"
OLDER_TEXT = "# Plan: sync guard demo\n\nThe stale earlier shape of the plan bytes.\n"
THIRD_TEXT = "# Plan: sync guard demo\n\nA divergent edit shape of the plan bytes.\n"


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _run(*args: str) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _load_guard_module():
    # Mirrors test_check_lesson_scope.py: load the script module by path with
    # importlib.util. Loading at collection time also pins that the script
    # parses; while the script file is missing this raises and pytest reports
    # the collection error that is the plan's expected RED state.
    spec = importlib.util.spec_from_file_location("docs_branch_plan_guard_under_test", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# Collection-time parse pin: the script module must load by path for the
# suite to collect at all; while the script file is missing this raises and
# pytest reports the collection error that is the plan's expected RED state.
GUARD_MODULE = _load_guard_module()


class CertifiedPlanGuardTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.incoming = self.dir / "incoming"
        self.branch = self.dir / "branch"
        self.reviews = self.dir / "reviews"
        self.reviews.mkdir(parents=True)
        self.cert_digest = _digest(CERTIFIED_TEXT)
        self.older_digest = _digest(OLDER_TEXT)

    # ------------------------------------------------------------------
    # Fixtures
    # ------------------------------------------------------------------

    def _write_plan(self, root: Path, text: str, sub: str = "") -> Path:
        plan_dir = root / PLANS_REL
        if sub:
            plan_dir = plan_dir / sub
        plan_dir.mkdir(parents=True, exist_ok=True)
        plan = plan_dir / PLAN_NAME
        plan.write_text(text, encoding="utf-8")
        return plan

    def _write_sidecar(
        self,
        name: str,
        *,
        slug: str,
        round_: object,
        digest: str,
        date: str = "2026-09-19",
    ) -> Path:
        sidecar = self.reviews / name
        sidecar.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "date": date,
                    "artifact_slug": slug,
                    "round": round_,
                    "source_kind": "plan",
                    "source_digest": digest,
                }
            ),
            encoding="utf-8",
        )
        return sidecar

    def _run_guard(self) -> tuple[int, str, str]:
        return _run(
            "guard",
            "--incoming-root", str(self.incoming),
            "--branch-root", str(self.branch),
            "--plans-dir", str(PLANS_REL),
            "--reviews-dir", str(self.reviews),
        )

    def _run_check_restored(self, *files: str) -> tuple[int, str, str]:
        return _run(
            "check-restored",
            "--reviews-dir", str(self.reviews),
            "--plans-dir", str(PLANS_REL),
            *files,
        )

    # ------------------------------------------------------------------
    # guard: refusal and pass-through arms
    # ------------------------------------------------------------------

    def test_guard_refuses_certified_downgrade(self) -> None:
        self._write_plan(self.branch, CERTIFIED_TEXT)
        self._write_plan(self.incoming, OLDER_TEXT)
        sidecar = self._write_sidecar(
            f"2026-09-19-plan-review-{FEATURE}-r1.stats.json",
            slug=FEATURE,
            round_="r1",
            digest=self.cert_digest,
        )
        code, out, _err = self._run_guard()
        self.assertEqual(code, 1)
        self.assertIn("REFUSE:", out)
        self.assertIn(str(self.branch / PLANS_REL / PLAN_NAME), out)
        self.assertIn(self.cert_digest, out)
        self.assertIn(sidecar.name, out)

    def test_guard_allows_certified_upgrade(self) -> None:
        self._write_plan(self.branch, OLDER_TEXT)
        self._write_plan(self.incoming, CERTIFIED_TEXT)
        self._write_sidecar(
            f"2026-09-19-plan-review-{FEATURE}-r1.stats.json",
            slug=FEATURE,
            round_="r1",
            digest=self.cert_digest,
        )
        code, out, _err = self._run_guard()
        self.assertEqual(code, 0)
        self.assertIn("UPGRADE:", out)
        self.assertIn(PLAN_NAME, out)

    def test_guard_warns_when_neither_side_matches(self) -> None:
        self._write_plan(self.branch, OLDER_TEXT)
        self._write_plan(self.incoming, THIRD_TEXT)
        self._write_sidecar(
            f"2026-09-19-plan-review-{FEATURE}-r1.stats.json",
            slug=FEATURE,
            round_="r1",
            digest=self.cert_digest,
        )
        code, out, _err = self._run_guard()
        self.assertEqual(code, 0)
        self.assertIn("WARN:", out)
        self.assertIn(PLAN_NAME, out)
        self.assertIn(self.cert_digest, out)

    def test_guard_silent_without_sidecar(self) -> None:
        self._write_plan(self.branch, CERTIFIED_TEXT)
        self._write_plan(self.incoming, OLDER_TEXT)
        # No sidecar written under the reviews dir.
        code, out, _err = self._run_guard()
        self.assertEqual(code, 0)
        self.assertNotIn("REFUSE:", out)

    def test_guard_ignores_completed_subdir(self) -> None:
        # Only a completed/ copy exists on each side; even with a sidecar
        # that would certify a refusal, the subdir plan is never considered.
        self._write_plan(self.branch, CERTIFIED_TEXT, sub="completed")
        self._write_plan(self.incoming, OLDER_TEXT, sub="completed")
        self._write_sidecar(
            f"2026-09-19-plan-review-{FEATURE}-r1.stats.json",
            slug=FEATURE,
            round_="r1",
            digest=self.cert_digest,
        )
        code, out, _err = self._run_guard()
        self.assertEqual(code, 0)
        self.assertNotIn("REFUSE:", out)

    def test_guard_prefix_digest_sidecar(self) -> None:
        self._write_plan(self.branch, CERTIFIED_TEXT)
        self._write_plan(self.incoming, OLDER_TEXT)
        self._write_sidecar(
            f"2026-09-19-plan-review-{FEATURE}-r1.stats.json",
            slug=FEATURE,
            round_="r1",
            digest=self.cert_digest[:16],
        )
        code, out, _err = self._run_guard()
        self.assertEqual(code, 1)
        self.assertIn("REFUSE:", out)

    # ------------------------------------------------------------------
    # guard: latest-round selection arms
    # ------------------------------------------------------------------

    def test_guard_latest_round_wins(self) -> None:
        self._write_plan(self.branch, CERTIFIED_TEXT)  # matches the r3 digest
        self._write_plan(self.incoming, OLDER_TEXT)  # matches the r1 digest
        self._write_sidecar(
            f"2026-09-19-plan-review-{FEATURE}-r1.stats.json",
            slug=FEATURE,
            round_="r1",
            digest=self.older_digest,
            date="2026-09-18",
        )
        self._write_sidecar(
            f"2026-09-19-plan-review-{FEATURE}-r3.stats.json",
            slug=FEATURE,
            round_="r3",
            digest=self.cert_digest,
            date="2026-09-19",
        )
        # With r3 certified, the incoming r1-shaped bytes are a downgrade.
        # A mutant that picks r1 would see an upgrade and exit 0.
        code, out, _err = self._run_guard()
        self.assertEqual(code, 1)
        self.assertIn("REFUSE:", out)

    def test_guard_feature_slug_lookup(self) -> None:
        # The plan file carries the date prefix; the sidecar's artifact_slug
        # is the feature slug with the prefix stripped. A lookup keyed on
        # the full stem would find no sidecar and stay silent.
        self._write_plan(self.branch, CERTIFIED_TEXT)
        self._write_plan(self.incoming, OLDER_TEXT)
        self._write_sidecar(
            f"2026-09-19-plan-review-{FEATURE}-r1.stats.json",
            slug=FEATURE,
            round_="r1",
            digest=self.cert_digest,
        )
        code, out, _err = self._run_guard()
        self.assertEqual(code, 1)
        self.assertIn("REFUSE:", out)

    def test_guard_mixed_round_forms(self) -> None:
        # Sidecar A stores round "r9" (string form) certifying the stale
        # bytes; sidecar B stores round 10 (integer form) certifying the
        # current bytes. Raw string comparison would misorder ("r10" < "r9")
        # and raw mixed-type comparison would raise; only normalized
        # integers pick B as latest, which makes the stale incoming bytes a
        # refused downgrade.
        self._write_plan(self.branch, CERTIFIED_TEXT)  # digest matches sidecar B
        self._write_plan(self.incoming, OLDER_TEXT)  # digest matches sidecar A
        self._write_sidecar(
            f"2026-09-19-plan-review-{FEATURE}-r9.stats.json",
            slug=FEATURE,
            round_="r9",
            digest=self.older_digest,
            date="2026-09-18",
        )
        self._write_sidecar(
            f"2026-09-19-plan-review-{FEATURE}-r10.stats.json",
            slug=FEATURE,
            round_=10,
            digest=self.cert_digest,
            date="2026-09-19",
        )
        code, out, _err = self._run_guard()
        self.assertEqual(code, 1)
        self.assertIn("REFUSE:", out)

    # ------------------------------------------------------------------
    # check-restored: warn-only witness arms
    # ------------------------------------------------------------------

    def test_check_restored_warns_on_mismatch(self) -> None:
        restored = self._write_plan(self.branch, OLDER_TEXT)
        self._write_sidecar(
            f"2026-09-19-plan-review-{FEATURE}-r1.stats.json",
            slug=FEATURE,
            round_="r1",
            digest=self.cert_digest,
        )
        code, out, _err = self._run_check_restored(str(restored))
        self.assertEqual(code, 0)
        self.assertIn("WARN:", out)
        self.assertIn(str(restored), out)

    def test_check_restored_silent_on_match_or_missing_sidecar(self) -> None:
        restored = self._write_plan(self.branch, CERTIFIED_TEXT)
        sidecar = self._write_sidecar(
            f"2026-09-19-plan-review-{FEATURE}-r1.stats.json",
            slug=FEATURE,
            round_="r1",
            digest=self.cert_digest,
        )
        # Case 1: bytes match the certification digest, no warning.
        code, out, _err = self._run_check_restored(str(restored))
        self.assertEqual(code, 0)
        self.assertNotIn("WARN:", out)
        # Case 2: the sidecar is gone, the witness stays silent.
        sidecar.unlink()
        code, out, _err = self._run_check_restored(str(restored))
        self.assertEqual(code, 0)
        self.assertNotIn("WARN:", out)


if __name__ == "__main__":
    unittest.main()
