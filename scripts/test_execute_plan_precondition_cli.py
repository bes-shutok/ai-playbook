"""CLI contract tests for retained execute-plan predecessor checks."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "scripts" / "execute_plan_runtime.py"

# Origin fixture text: an unrelated filler keyword line plus a contradictory
# legacy clause; the real contract wording is absent from it.
GUIDE_TEXT = (
    "legacy: removal of restrictions is forbidden here\n"
    "filler line mentioning remove\n"
)
REAL_CLAUSE = "staged-doc restrictions were lifted for the guide"
FORBIDDEN_CLAUSE = "removal of restrictions is forbidden here"


def run_precondition(predecessors: list[dict[str, Any]], repo_root: Path) -> dict[str, Any]:
    """Run the precondition CLI over one predecessor declaration list."""

    with tempfile.TemporaryDirectory() as tmp:
        declaration_path = Path(tmp) / "predecessors.json"
        declaration_path.write_text(
            json.dumps({"predecessors": predecessors}), encoding="utf-8"
        )
        completed = subprocess.run(
            [
                sys.executable,
                "-E",
                "-s",
                str(RUNTIME),
                "--operation",
                "precondition",
                "--predecessors-file",
                str(declaration_path),
                "--repo-root",
                str(repo_root),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    if completed.returncode != 0:
        raise AssertionError(
            f"precondition CLI exited {completed.returncode}: {completed.stderr}"
        )
    return json.loads(completed.stdout)


def make_repo_with_guide(text: str) -> tempfile.TemporaryDirectory:
    """Create a scratch repo root carrying docs/guide.md with the given text."""

    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    (root / "docs").mkdir()
    (root / "docs" / "guide.md").write_text(text, encoding="utf-8")
    return tmp


class PreconditionCliTests(unittest.TestCase):
    def test_malformed_or_unreadable_predecessors_return_structured_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            malformed = root / "predecessors-broken.json"
            malformed.write_text("{not json", encoding="utf-8")
            missing = root / "predecessors-absent.json"

            for target in (malformed, missing):
                with self.subTest(target=target.name):
                    completed = subprocess.run(
                        [
                            sys.executable,
                        "-E",
                        "-s",
                            str(RUNTIME),
                            "--operation",
                            "precondition",
                            "--predecessors-file",
                            str(target),
                            "--repo-root",
                            str(ROOT),
                        ],
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    result = json.loads(completed.stdout)
                    self.assertEqual(result["status"], "blocked")
                    self.assertEqual(result["reason_code"], "precondition-unverified")
                    self.assertEqual(result["action_scope"], "repository-read")
                    self.assertEqual(result["checkpoint_identity"], "precondition:verify")
                    self.assertEqual(result["next_action"], "preserve-and-reconcile")
                    self.assertTrue(result["resume_allowed"])
                    self.assertEqual(result["predecessors"], [])
                    self.assertIn(str(target), " ".join(result["evidence"]))


class ArtifactClauseContractTests(unittest.TestCase):
    """Required-clause contract for the artifact outcome's contains field."""

    def test_single_string_contains_keeps_today_reading(self):
        # Regression pin: expected green before and after the clause work.
        with make_repo_with_guide(GUIDE_TEXT) as tmp:
            root = Path(tmp)
            present = run_precondition(
                [{
                    "ref": "guide",
                    "outcomes": [{
                        "kind": "artifact",
                        "path": "docs/guide.md",
                        "contains": "remove",
                    }],
                }],
                root,
            )
            self.assertEqual(present["status"], "success")
            self.assertEqual(present["action_scope"], "repository-read")
            self.assertEqual(present["checkpoint_identity"], "precondition:verify")
            record = present["predecessors"][0]
            self.assertTrue(record["verified"])
            self.assertEqual(
                record["verified_by"], {"kind": "artifact", "target": "docs/guide.md"}
            )
            absent = run_precondition(
                [{
                    "ref": "guide",
                    "outcomes": [{
                        "kind": "artifact",
                        "path": "docs/guide.md",
                        "contains": "no such clause exists anywhere",
                    }],
                }],
                root,
            )
            self.assertEqual(absent["status"], "blocked")
            self.assertEqual(absent["reason_code"], "precondition-unverified")
            self.assertEqual(absent["next_action"], "preserve-and-reconcile")
            self.assertTrue(absent["resume_allowed"])
            record = absent["predecessors"][0]
            self.assertFalse(record["verified"])
            self.assertIsNone(record["verified_by"])

    def test_list_contains_verifies_only_when_every_clause_appears(self):
        with make_repo_with_guide(GUIDE_TEXT + REAL_CLAUSE + "\n") as tmp:
            root = Path(tmp)
            complete = run_precondition(
                [{
                    "ref": "guide",
                    "outcomes": [{
                        "kind": "artifact",
                        "path": "docs/guide.md",
                        "contains": [REAL_CLAUSE, "filler line mentioning remove"],
                    }],
                }],
                root,
            )
            self.assertEqual(complete["status"], "success")
            self.assertTrue(complete["predecessors"][0]["verified"])
            partial = run_precondition(
                [{
                    "ref": "guide",
                    "outcomes": [{
                        "kind": "artifact",
                        "path": "docs/guide.md",
                        "contains": [REAL_CLAUSE, "the absent second clause"],
                    }],
                }],
                root,
            )
            self.assertEqual(partial["status"], "blocked")
            self.assertEqual(partial["reason_code"], "precondition-unverified")
            record = partial["predecessors"][0]
            self.assertFalse(record["verified"])
            self.assertIsNone(record["verified_by"])
            joined = " ".join(partial["evidence"])
            self.assertIn("the absent second clause", joined)
            self.assertNotIn(REAL_CLAUSE, joined)

    def test_unrelated_keyword_hit_does_not_satisfy_required_clause(self):
        with make_repo_with_guide(GUIDE_TEXT) as tmp:
            root = Path(tmp)
            result = run_precondition(
                [{
                    "ref": "guide",
                    "outcomes": [{
                        "kind": "artifact",
                        "path": "docs/guide.md",
                        "contains": REAL_CLAUSE,
                    }],
                }],
                root,
            )
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason_code"], "precondition-unverified")
            joined = " ".join(result["evidence"])
            self.assertIn(REAL_CLAUSE, joined)

    def test_malformed_contains_declaration_blocks_with_field_named(self):
        cases = {
            "empty string": "",
            "empty list": [],
            "non-string member": [REAL_CLAUSE, 7],
            "empty-string clause": [REAL_CLAUSE, ""],
        }
        for label, contains in cases.items():
            with self.subTest(contains=label):
                with make_repo_with_guide(GUIDE_TEXT) as tmp:
                    root = Path(tmp)
                    result = run_precondition(
                        [{
                            "ref": "guide",
                            "outcomes": [{
                                "kind": "artifact",
                                "path": "docs/guide.md",
                                "contains": contains,
                            }],
                        }],
                        root,
                    )
                    self.assertEqual(result["status"], "blocked")
                    self.assertEqual(result["reason_code"], "precondition-unverified")
                    self.assertEqual(result["action_scope"], "repository-read")
                    self.assertEqual(result["next_action"], "preserve-and-reconcile")
                    self.assertTrue(result["resume_allowed"])
                    record = result["predecessors"][0]
                    self.assertFalse(record["verified"])
                    self.assertIsNone(record["verified_by"])
                    joined = " ".join(result["evidence"])
                    self.assertIn("malformed", joined.lower())
                    self.assertIn("contains", joined)


class ArtifactForbiddenClauseContractTests(unittest.TestCase):
    """Forbidden-clause contract for the artifact outcome's must_not_contain field."""

    def test_forbidden_clause_present_blocks_naming_it_with_record_false(self):
        # Every required clause is present and the contradictory legacy clause
        # sits in the same file; the forbidden arm must still block and name it.
        with make_repo_with_guide(GUIDE_TEXT + REAL_CLAUSE + "\n") as tmp:
            root = Path(tmp)
            result = run_precondition(
                [{
                    "ref": "guide",
                    "outcomes": [{
                        "kind": "artifact",
                        "path": "docs/guide.md",
                        "contains": [REAL_CLAUSE, "filler line mentioning remove"],
                        "must_not_contain": FORBIDDEN_CLAUSE,
                    }],
                }],
                root,
            )
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason_code"], "precondition-unverified")
            record = result["predecessors"][0]
            self.assertFalse(record["verified"])
            self.assertIsNone(record["verified_by"])
            joined = " ".join(result["evidence"])
            self.assertIn(FORBIDDEN_CLAUSE, joined)

    def test_list_must_not_contain_blocks_when_any_member_is_present(self):
        with make_repo_with_guide(GUIDE_TEXT + REAL_CLAUSE + "\n") as tmp:
            root = Path(tmp)
            absent_clause = "a clause that never appears in this file"
            result = run_precondition(
                [{
                    "ref": "guide",
                    "outcomes": [{
                        "kind": "artifact",
                        "path": "docs/guide.md",
                        "contains": REAL_CLAUSE,
                        "must_not_contain": [absent_clause, FORBIDDEN_CLAUSE],
                    }],
                }],
                root,
            )
            self.assertEqual(result["status"], "blocked")
            record = result["predecessors"][0]
            self.assertFalse(record["verified"])
            self.assertIsNone(record["verified_by"])
            joined = " ".join(result["evidence"])
            self.assertIn(FORBIDDEN_CLAUSE, joined)
            self.assertNotIn(absent_clause, joined)

    def test_forbidden_clause_absent_with_required_present_verifies(self):
        with make_repo_with_guide(GUIDE_TEXT + REAL_CLAUSE + "\n") as tmp:
            root = Path(tmp)
            result = run_precondition(
                [{
                    "ref": "guide",
                    "outcomes": [{
                        "kind": "artifact",
                        "path": "docs/guide.md",
                        "contains": [REAL_CLAUSE, "filler line mentioning remove"],
                        "must_not_contain": "a clause that never appears in this file",
                    }],
                }],
                root,
            )
            self.assertEqual(result["status"], "success")
            record = result["predecessors"][0]
            self.assertTrue(record["verified"])
            self.assertEqual(
                record["verified_by"], {"kind": "artifact", "target": "docs/guide.md"}
            )

    def test_clean_file_with_no_forbidden_hit_verifies(self):
        clean_text = "v2: staged-doc restrictions were lifted for the guide\n"
        with make_repo_with_guide(clean_text) as tmp:
            root = Path(tmp)
            result = run_precondition(
                [{
                    "ref": "guide",
                    "outcomes": [{
                        "kind": "artifact",
                        "path": "docs/guide.md",
                        "contains": REAL_CLAUSE,
                        "must_not_contain": FORBIDDEN_CLAUSE,
                    }],
                }],
                root,
            )
            self.assertEqual(result["status"], "success")
            record = result["predecessors"][0]
            self.assertTrue(record["verified"])
            self.assertEqual(
                record["verified_by"], {"kind": "artifact", "target": "docs/guide.md"}
            )

    def test_malformed_must_not_contain_declaration_blocks_with_field_named(self):
        cases = {
            "wrong type": 7,
            "empty string": "",
            "non-string member": [FORBIDDEN_CLAUSE, 7],
            "empty-string clause": [FORBIDDEN_CLAUSE, ""],
        }
        for label, must_not_contain in cases.items():
            with self.subTest(must_not_contain=label):
                with make_repo_with_guide(GUIDE_TEXT + REAL_CLAUSE + "\n") as tmp:
                    root = Path(tmp)
                    result = run_precondition(
                        [{
                            "ref": "guide",
                            "outcomes": [{
                                "kind": "artifact",
                                "path": "docs/guide.md",
                                "contains": REAL_CLAUSE,
                                "must_not_contain": must_not_contain,
                            }],
                        }],
                        root,
                    )
                    self.assertEqual(result["status"], "blocked")
                    self.assertEqual(result["reason_code"], "precondition-unverified")
                    record = result["predecessors"][0]
                    self.assertFalse(record["verified"])
                    self.assertIsNone(record["verified_by"])
                    joined = " ".join(result["evidence"])
                    self.assertIn("malformed", joined.lower())
                    self.assertIn("must_not_contain", joined)


if __name__ == "__main__":
    unittest.main()
