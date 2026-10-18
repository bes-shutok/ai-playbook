#!/usr/bin/env python3
"""Unit tests for the plan-shape resolver and the Task 1 validator surface.

Covers ``scripts/plan_shape.py`` (the one grammar derivation for plan
operands: single-file passthrough, directory charter-plus-tasks resolution,
the named refusal arms, the directory ordinal grammar, and the canonical
manifest-digest serialization) and the review-staging validator's
``--source-plan`` directory acceptance (manifest digest beside the unchanged
missing-operand tool error), per the plan-directory-shape plan's Task 1.

Run from the repository root:

    "$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_plan_shape.py -q
"""

import contextlib
import hashlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

import plan_shape
import validate_review_staging as vrs

REPO_ROOT = Path(__file__).resolve().parent.parent


def _write_bytes(path: Path, data: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _make_directory_plan(
    root: Path,
    slug: str = "2026-10-08-dirplan",
    charter_text: str = "# Plan: fixture\n\n## Why\n\nFixture charter.\n",
    task_texts: dict[str, str] | None = None,
) -> Path:
    """Well-formed directory plan fixture: charter plus two ordinal tasks."""
    plan_dir = root / slug
    _write_text(plan_dir / "PLAN.md", charter_text)
    if task_texts is None:
        task_texts = {
            "01-first.md": "### Task 1: first\n\n- [ ] do first. [class: IMPLEMENTATION_REQUIRED]\n",
            "02-second.md": "### Task 2: second\n\n- [ ] do second. [class: REPOSITORY_TEST]\n",
        }
    for name, text in task_texts.items():
        _write_text(plan_dir / "tasks" / name, text)
    return plan_dir


class ResolveDirectoryOperandTest(unittest.TestCase):
    """test_resolve_directory_operand: the well-formed directory shape."""

    def test_returns_charter_sorted_tasks_and_slug(self):
        with tempfile.TemporaryDirectory() as td:
            plan_dir = _make_directory_plan(Path(td)).resolve()
            shape = plan_shape.resolve_plan_operand(plan_dir)
            self.assertEqual(shape.kind, "directory")
            self.assertEqual(shape.charter_text, (plan_dir / "PLAN.md").read_text(encoding="utf-8"))
            relpaths = [rel for rel, _path, _text in shape.task_files]
            self.assertEqual(relpaths, ["tasks/01-first.md", "tasks/02-second.md"])
            for rel, path, text in shape.task_files:
                self.assertEqual(path, plan_dir / rel)
                self.assertEqual(text, path.read_text(encoding="utf-8"))
            self.assertEqual(shape.slug, plan_dir.name)

    def test_charter_file_operand_shape_fields(self):
        with tempfile.TemporaryDirectory() as td:
            plan_file = _write_text(
                Path(td) / "2026-10-08-solo.md", "# Plan: solo\n"
            )
            shape = plan_shape.resolve_plan_operand(plan_file)
            self.assertEqual(shape.kind, "file")
            self.assertEqual(shape.charter_text, "# Plan: solo\n")
            self.assertEqual(shape.task_files, ())
            self.assertEqual(shape.slug, "2026-10-08-solo")


class ResolveRefusalArmsTest(unittest.TestCase):
    """test_resolve_refusal_arms: every refusal names defect and operand path."""

    def _assert_refusal(self, operand: Path, *needles: str):
        with self.assertRaises(plan_shape.PlanShapeRefusal) as caught:
            plan_shape.resolve_plan_operand(operand)
        message = str(caught.exception)
        for needle in needles:
            self.assertIn(needle, message)
        self.assertIn(str(operand), message)

    def test_charterless_directory_refuses(self):
        with tempfile.TemporaryDirectory() as td:
            bare = Path(td) / "2026-10-08-bare"
            bare.mkdir()
            # The readiness gate's pinned legacy family for a charterless
            # directory stays "not a file" (the in-file selftest's
            # plan_path_is_directory arm matches that substring).
            self._assert_refusal(bare, "not a file", "PLAN.md")

    def test_empty_tasks_directory_refuses(self):
        with tempfile.TemporaryDirectory() as td:
            plan_dir = Path(td) / "2026-10-08-empty-tasks"
            _write_text(plan_dir / "PLAN.md", "# charter\n")
            (plan_dir / "tasks").mkdir()
            self._assert_refusal(plan_dir, "empty", "tasks")

    def test_nonexistent_path_refuses(self):
        with tempfile.TemporaryDirectory() as td:
            ghost = Path(td) / "2026-10-08-ghost.md"
            self._assert_refusal(ghost, "does not exist")

    def test_unreadable_charter_refuses(self):
        with tempfile.TemporaryDirectory() as td:
            plan_dir = Path(td) / "2026-10-08-locked"
            _write_text(plan_dir / "PLAN.md", "# charter\n")
            _write_text(plan_dir / "tasks" / "01-a.md", "### Task 1: a\n")
            charter = plan_dir / "PLAN.md"
            os.chmod(charter, 0o000)
            try:
                self._assert_refusal(plan_dir, "cannot read")
            finally:
                os.chmod(charter, 0o644)

    def test_missing_tasks_directory_refuses(self):
        with tempfile.TemporaryDirectory() as td:
            plan_dir = Path(td) / "2026-10-08-no-tasks-dir"
            _write_text(plan_dir / "PLAN.md", "# charter\n")
            self._assert_refusal(plan_dir, "tasks")

    def test_non_markdown_file_under_tasks_refuses(self):
        with tempfile.TemporaryDirectory() as td:
            plan_dir = Path(td) / "2026-10-08-stray"
            _write_text(plan_dir / "PLAN.md", "# charter\n")
            _write_text(plan_dir / "tasks" / "01-a.md", "### Task 1: a\n")
            _write_text(plan_dir / "tasks" / "notes.txt", "stray\n")
            self._assert_refusal(plan_dir, "tasks/notes.txt")


class ResolveOrdinalGrammarTest(unittest.TestCase):
    """test_resolve_ordinal_collision: the directory ordinal grammar."""

    def test_duplicate_ordinal_refuses_naming_both_files(self):
        with tempfile.TemporaryDirectory() as td:
            plan_dir = _make_directory_plan(
                Path(td),
                task_texts={
                    "01-first.md": "### Task 1: first\n",
                    "02-also-first.md": "### Task 1: dup\n",
                },
            )
            with self.assertRaises(plan_shape.PlanShapeRefusal) as caught:
                plan_shape.resolve_plan_operand(plan_dir)
            message = str(caught.exception)
            self.assertIn("tasks/01-first.md", message)
            self.assertIn("tasks/02-also-first.md", message)
            self.assertIn("Task 1", message)

    def test_missing_ordinal_refuses_naming_the_gap(self):
        with tempfile.TemporaryDirectory() as td:
            plan_dir = _make_directory_plan(
                Path(td),
                task_texts={
                    "01-first.md": "### Task 1: first\n",
                    "03-third.md": "### Task 3: third\n",
                },
            )
            with self.assertRaises(plan_shape.PlanShapeRefusal) as caught:
                plan_shape.resolve_plan_operand(plan_dir)
            self.assertIn("2", str(caught.exception))

    def test_task_file_without_heading_refuses_naming_the_file(self):
        with tempfile.TemporaryDirectory() as td:
            plan_dir = _make_directory_plan(
                Path(td),
                task_texts={
                    "01-first.md": "### Task 1: first\n",
                    "02-headless.md": "no task heading here\n",
                },
            )
            with self.assertRaises(plan_shape.PlanShapeRefusal) as caught:
                plan_shape.resolve_plan_operand(plan_dir)
            self.assertIn("tasks/02-headless.md", str(caught.exception))

    def test_task_zero_only_directory_refuses_naming_ordinal_1(self):
        # The task sequence must start at 1: a directory whose only task
        # file declares '### Task 0:' never reaches the range scan, so the
        # refusal names the absent first ordinal explicitly.
        with tempfile.TemporaryDirectory() as td:
            plan_dir = _make_directory_plan(
                Path(td),
                task_texts={"00-zero.md": "### Task 0: zero\n"},
            ).resolve()
            with self.assertRaises(plan_shape.PlanShapeRefusal) as caught:
                plan_shape.resolve_plan_operand(plan_dir)
            message = str(caught.exception)
            self.assertIn("missing task ordinal(s) 1", message)
            self.assertIn("present ordinals: 0", message)
            self.assertIn(str(plan_dir), message)


class ManifestDigestOrderingAndBoundaryTest(unittest.TestCase):
    """test_manifest_digest_ordering_and_boundary: canonical serialization pins."""

    def test_payload_serialization_is_sorted_relpath_nul_sha_lines(self):
        with tempfile.TemporaryDirectory() as td:
            plan_dir = _make_directory_plan(Path(td))
            shape = plan_shape.resolve_plan_operand(plan_dir)
            charter = (plan_dir / "PLAN.md").read_bytes()
            first = (plan_dir / "tasks" / "01-first.md").read_bytes()
            second = (plan_dir / "tasks" / "02-second.md").read_bytes()
            expected = b"".join(
                rel.encode("utf-8")
                + b"\x00"
                + hashlib.sha256(data).hexdigest().encode("ascii")
                + b"\n"
                for rel, data in (
                    ("PLAN.md", charter),
                    ("tasks/01-first.md", first),
                    ("tasks/02-second.md", second),
                )
            )
            self.assertEqual(shape.digest_payload, expected)
            self.assertEqual(
                vrs.compute_source_digest("plan", shape.digest_payload),
                hashlib.sha256(expected).hexdigest(),
            )

    def test_enumeration_order_never_changes_payload(self):
        charter = b"# Plan: reorder\n\n## Why\n\nCharter.\n"
        first = b"### Task 1: first\n"
        second = b"### Task 2: second\n"
        entries = [
            ("PLAN.md", charter),
            ("tasks/01-first.md", first),
            ("tasks/02-second.md", second),
        ]
        # The same (relpath, bytes) entry set enumerated in two orders:
        # the canonical sort makes the payload order-independent (the
        # plan's edge case: stable under file reordering). A RENAME is
        # not a reorder: relpaths are load-bearing lines, so a renamed
        # task file is a payload change by construction.
        rotated = [entries[2], entries[0], entries[1]]
        reversed_entries = list(reversed(entries))
        self.assertEqual(
            plan_shape.manifest_digest_payload(entries),
            plan_shape.manifest_digest_payload(rotated),
        )
        self.assertEqual(
            plan_shape.manifest_digest_payload(entries),
            plan_shape.manifest_digest_payload(reversed_entries),
        )

    def test_resolver_returns_task_files_sorted(self):
        with tempfile.TemporaryDirectory() as td:
            # Created 02 before 01; the resolver sorts lexicographically.
            plan_dir = _make_directory_plan(
                Path(td),
                task_texts={
                    "02-second.md": "### Task 2: second\n",
                    "01-first.md": "### Task 1: first\n",
                },
            )
            shape = plan_shape.resolve_plan_operand(plan_dir)
            self.assertEqual(
                [rel for rel, _path, _text in shape.task_files],
                ["tasks/01-first.md", "tasks/02-second.md"],
            )

    def test_any_file_byte_change_changes_payload(self):
        with tempfile.TemporaryDirectory() as td:
            base = _make_directory_plan(Path(td))
            baseline = plan_shape.resolve_plan_operand(base).digest_payload
            _write_text(
                base / "tasks" / "02-second.md",
                "### Task 2: second\n\none byte more.\n",
            )
            self.assertNotEqual(
                plan_shape.resolve_plan_operand(base).digest_payload, baseline
            )

    def test_file_boundary_is_visible_in_payload(self):
        with tempfile.TemporaryDirectory() as td:
            charter = "# Plan: boundary\n"
            split = _make_directory_plan(
                Path(td),
                slug="2026-10-08-split",
                charter_text=charter,
                task_texts={
                    "01-a.md": "### Task 1: A\n",
                    "02-b.md": "### Task 2: B\n",
                },
            )
            merged = _make_directory_plan(
                Path(td),
                slug="2026-10-08-merged",
                charter_text=charter,
                task_texts={
                    "01-a.md": "### Task 1: A\n\n### Task 2: B\n",
                },
            )
            self.assertNotEqual(
                plan_shape.resolve_plan_operand(split).digest_payload,
                plan_shape.resolve_plan_operand(merged).digest_payload,
            )


class FileOperandPassthroughTest(unittest.TestCase):
    """test_file_operand_passthrough: file operands match today's values."""

    def test_passthrough_matches_raw_bytes(self):
        landed = REPO_ROOT / (
            "docs/history/plans/completed/"
            "2026-10-05-plan-sizing-execution-budget.md"
        )
        raw = landed.read_bytes()
        shape = plan_shape.resolve_plan_operand(landed)
        self.assertEqual(shape.kind, "file")
        self.assertEqual(shape.digest_payload, raw)
        self.assertEqual(
            shape.charter_text, raw.decode("utf-8")
        )
        self.assertEqual(shape.task_files, ())
        self.assertEqual(shape.slug, landed.stem)
        self.assertEqual(
            vrs.compute_source_digest("plan", shape.digest_payload),
            vrs.compute_source_digest("plan", raw),
        )


class ValidatorSourcePlanDirectoryTest(unittest.TestCase):
    """test_validator_source_plan_directory: --source-plan accepts directories."""

    def _run_validator(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = vrs.main(argv)
        return rc, out.getvalue(), err.getvalue()

    def _staging_doc(self, root: Path, source_digest: str) -> Path:
        payload = vrs._post_window_fixture_payload("plan")
        payload["source_digest"] = source_digest
        return vrs._write_staging(
            root,
            "2026-09-22-plan-review-dirplan-r1.md",
            vrs._post_window_fixture_markdown("plan"),
            payload,
        )

    def test_directory_operand_verifies_against_manifest_digest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            plan_dir = _make_directory_plan(root / "plans").resolve()
            shape = plan_shape.resolve_plan_operand(plan_dir)
            manifest_digest = vrs.compute_source_digest(
                "plan", shape.digest_payload
            )
            staging = self._staging_doc(root, manifest_digest)
            rc, out, err = self._run_validator(
                ["--hard", str(staging), "--source-plan", str(plan_dir)]
            )
            self.assertEqual(rc, 0, f"out={out!r} err={err!r}")
            self.assertTrue(out.rstrip().endswith("OUTCOME: pass"))

    def test_directory_operand_detects_stale_manifest_digest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            plan_dir = _make_directory_plan(root / "plans").resolve()
            staging = self._staging_doc(root, "abc123")
            rc, out, err = self._run_validator(
                ["--hard", str(staging), "--source-plan", str(plan_dir)]
            )
            self.assertEqual(rc, 1, f"out={out!r} err={err!r}")

    def test_missing_operand_still_fails_as_tool_error(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            staging = self._staging_doc(
                root, vrs._post_window_fixture_payload("plan")["source_digest"]
            )
            ghost = root / "no-such-plan.md"
            rc, out, err = self._run_validator(
                ["--hard", str(staging), "--source-plan", str(ghost)]
            )
            self.assertEqual(rc, 3)
            self.assertIn(f"source file not found: {ghost.resolve()}", err)
            # The non-json tool-error surface: ERROR on stderr, the
            # OUTCOME line on stdout (mirroring the existing arm at the
            # source routing region).
            self.assertIn("OUTCOME: tool_error", out)


if __name__ == "__main__":
    unittest.main()
