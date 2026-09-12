#!/usr/bin/env python3
"""Tests for the lesson scope duplicate validator (check_lesson_scope.py)."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent / "check_lesson_scope.py"

RULE_A = (
    "When a configuration rollout expands the pull request scope beyond its "
    "original title, update the title before merging so reviewers can rely on "
    "the title as the scope of record for later audits and incident tracing."
)

RULE_B = (
    "Before renaming a shared database column, grep every repository that "
    "consumes the schema and file the migration plan with each consuming team, "
    "because silent consumers break at runtime long after the rename lands."
)

SHORT_POINTER = "See the company guidelines master for the rollout title scope rule."

# Exactly 25 words (MIN_RULE_WORDS); see test_exact_min_word_boundary_flagged.
EXACT_MIN_BODY = (
    "A boundary rule body repeated verbatim in both files with exactly "
    "the minimum number of normalized words required for the duplicate "
    "floor to apply here"
)


def _run(*args: str) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _load_validator_module():
    # Direct import for unit-level assertions: register in sys.modules
    # before exec_module so the frozen dataclass resolves its module.
    spec = importlib.util.spec_from_file_location("check_lesson_scope_under_test", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CheckLessonScopeTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.corpus = self.dir / "development_lessons.md"
        self.master = self.dir / "company-guidelines.md"

    def _write(self, path: Path, text: str) -> Path:
        path.write_text(text, encoding="utf-8")
        return path

    def _corpus_with(self, heading: str, body: str) -> str:
        return f"# Project lessons\n\n## {heading}\n\n{body}\n"

    def _master_with(self, heading: str, body: str) -> str:
        return f"# Company guidelines\n\n## {heading}\n\n{body}\n"

    def test_verbatim_duplicate_flagged(self) -> None:
        self._write(self.corpus, self._corpus_with("12. Keep rollout PR titles in sync", RULE_A))
        # Leading paragraph puts the master heading on line 5 while the
        # corpus heading sits on line 3, so the line-number fields below
        # cannot pass by coincidence.
        self._write(
            self.master,
            f"# Company guidelines\n\nThis master governs shared engineering rules.\n\n"
            f"## 51. Keep rollout PR titles in sync\n\n{RULE_A}\n",
        )
        code, out, _err = _run(str(self.corpus), str(self.master))
        self.assertEqual(code, 1)
        self.assertIn("DUPLICATE:", out)
        self.assertIn("development_lessons.md:3", out)
        self.assertIn("company-guidelines.md:5", out)
        self.assertIn("Keep rollout PR titles in sync", out)

    def test_near_verbatim_duplicate_flagged(self) -> None:
        noisy_body = "  When   a CONFIGURATION rollout\nexpands the pull request scope beyond its original title, update the title before merging so reviewers can rely on the title as the scope of record for later audits and incident tracing.  "
        self._write(self.corpus, self._corpus_with("7. Keep Rollout PR Titles In Sync", noisy_body))
        self._write(self.master, self._master_with("51. Keep rollout PR titles in sync", RULE_A))
        code, out, _err = _run(str(self.corpus), str(self.master))
        self.assertEqual(code, 1)
        self.assertIn("DUPLICATE:", out)
        self.assertIn("development_lessons.md", out)
        self.assertIn("company-guidelines.md", out)

    def test_near_verbatim_with_real_edits_flagged(self) -> None:
        reworded = (
            "When a config rollout grows the pull request scope past its "
            "original title, update the title before merging so reviewers can "
            "treat the title as the scope of record for later audits and "
            "incident tracing."
        )
        self._write(self.corpus, self._corpus_with("12. Keep rollout PR titles in sync", reworded))
        self._write(self.master, self._master_with("51. Keep rollout PR titles in sync", RULE_A))
        code, out, _err = _run(str(self.corpus), str(self.master))
        self.assertEqual(code, 1)
        self.assertIn("DUPLICATE:", out)

    def test_divergent_rule_bodies_clean(self) -> None:
        divergent = (
            "Before approving a rollout, verify that the feature flag "
            "default matches the intended launch state, because a wrong "
            "default silently ships the change to every environment and "
            "defeats the staged ramp plan."
        )
        self._write(self.corpus, self._corpus_with("12. Verify flag defaults before approval", divergent))
        self._write(self.master, self._master_with("51. Keep rollout PR titles in sync", RULE_A))
        code, out, _err = _run(str(self.corpus), str(self.master))
        self.assertEqual(code, 0)
        self.assertNotIn("DUPLICATE:", out)

    def test_h4_subheading_does_not_split_block(self) -> None:
        body = f"{RULE_A}\n\n#### Evidence\n\nThe audit trail confirmed the title update."
        self._write(self.corpus, self._corpus_with("12. Keep rollout PR titles in sync", body))
        self._write(self.master, self._master_with("51. Keep rollout PR titles in sync", body))
        code, out, _err = _run(str(self.corpus), str(self.master))
        self.assertEqual(code, 1)
        self.assertIn("DUPLICATE:", out)

    def test_headingless_file_is_one_block(self) -> None:
        self._write(self.corpus, f"{RULE_A}\n")
        self._write(self.master, self._master_with("51. Keep rollout PR titles in sync", RULE_A))
        code, out, _err = _run(str(self.corpus), str(self.master))
        self.assertEqual(code, 1)
        self.assertIn("DUPLICATE:", out)

    def test_multilevel_enum_heading_pairs_with_unnumbered(self) -> None:
        # This test covers the numbered-vs-unnumbered pair-detection
        # path only: the corpus enum heading still pairs with the
        # unnumbered master heading. It cannot discriminate _ENUM_RE,
        # because the DUPLICATE line prints the raw headings verbatim;
        # the enum strip itself is enforced at code level.
        self._write(self.corpus, self._corpus_with("12.3. Keep rollout PR titles in sync", RULE_A))
        self._write(self.master, self._master_with("Keep rollout PR titles in sync", RULE_A))
        code, out, _err = _run(str(self.corpus), str(self.master))
        self.assertEqual(code, 1)
        self.assertIn("DUPLICATE:", out)
        self.assertIn("development_lessons.md:3 12.3. Keep rollout PR titles in sync", out)
        self.assertIn("company-guidelines.md:3 Keep rollout PR titles in sync", out)

    def test_multiple_duplicates_each_reported(self) -> None:
        corpus_text = (
            f"# Project lessons\n\n## 12. Keep rollout PR titles in sync\n\n{RULE_A}\n\n"
            f"## 13. Grep consumers before column renames\n\n{RULE_B}\n"
        )
        master_text = (
            f"# Company guidelines\n\n## 51. Grep consumers before column renames\n\n{RULE_B}\n\n"
            f"## 52. Keep rollout PR titles in sync\n\n{RULE_A}\n"
        )
        self._write(self.corpus, corpus_text)
        self._write(self.master, master_text)
        code, out, _err = _run(str(self.corpus), str(self.master))
        self.assertEqual(code, 1)
        dup_lines = [line for line in out.splitlines() if line.startswith("DUPLICATE:")]
        self.assertEqual(len(dup_lines), 2)
        self.assertIn("Keep rollout PR titles in sync", out)
        self.assertIn("Grep consumers before column renames", out)

    def test_project_only_rule_clean(self) -> None:
        self._write(self.corpus, self._corpus_with("12. Keep rollout PR titles in sync", RULE_A))
        self._write(self.master, self._master_with("51. Grep consumers before column renames", RULE_B))
        code, out, _err = _run(str(self.corpus), str(self.master))
        self.assertEqual(code, 0)
        self.assertNotIn("DUPLICATE:", out)

    def test_witness_pointer_clean(self) -> None:
        self._write(self.corpus, self._corpus_with("12. Rollout title witness", SHORT_POINTER))
        self._write(self.master, self._master_with("51. Keep rollout PR titles in sync", RULE_A))
        code, out, _err = _run(str(self.corpus), str(self.master))
        self.assertEqual(code, 0)
        self.assertNotIn("DUPLICATE:", out)

    def test_temporary_note_no_false_positive(self) -> None:
        note = "Session note: the rollout title scope discussion is parked until the audit meeting next week."
        self._write(self.corpus, self._corpus_with("Parking lot", note))
        self._write(self.master, self._master_with("51. Keep rollout PR titles in sync", RULE_A))
        code, out, _err = _run(str(self.corpus), str(self.master))
        self.assertEqual(code, 0)
        self.assertNotIn("DUPLICATE:", out)

    def test_ecosystem_tier_out_of_comparison(self) -> None:
        # Ecosystem-tier files (language guidelines) stay out of the
        # comparison unless passed explicitly. Invocation 1: corpus and
        # master hold distinct rules, so the run is clean even though a
        # third ecosystem file repeats the corpus rule verbatim.
        # Invocation 2: the same ecosystem file passed as the master
        # argument IS compared and flags the duplicate, proving the
        # comparison set is exactly the two CLI arguments.
        language_file = self.dir / "python_guidelines.md"
        self._write(language_file, f"# Python guidelines\n\n## 9. Keep rollout PR titles in sync\n\n{RULE_A}\n")
        self._write(self.corpus, self._corpus_with("12. Keep rollout PR titles in sync", RULE_A))
        self._write(self.master, self._master_with("51. Grep consumers before column renames", RULE_B))
        code, out, _err = _run(str(self.corpus), str(self.master))
        self.assertEqual(code, 0)
        self.assertNotIn("DUPLICATE:", out)
        code, out, _err = _run(str(self.corpus), str(language_file))
        self.assertEqual(code, 1)
        self.assertIn("DUPLICATE:", out)

    def test_missing_company_master_clean(self) -> None:
        self._write(self.corpus, self._corpus_with("12. Keep rollout PR titles in sync", RULE_A))
        code, _out, err = _run(str(self.corpus), str(self.master))
        self.assertEqual(code, 0)
        self.assertIn("WARNING:", err)

    def test_missing_corpus_clean(self) -> None:
        self._write(self.master, self._master_with("51. Keep rollout PR titles in sync", RULE_A))
        code, _out, err = _run(str(self.corpus), str(self.master))
        self.assertEqual(code, 0)
        self.assertIn("WARNING:", err)

    def test_empty_path_argument_exit_two(self) -> None:
        self._write(self.master, self._master_with("51. Keep rollout PR titles in sync", RULE_A))
        code, _out, err = _run("", str(self.master))
        self.assertEqual(code, 2)
        self.assertIn("usage", err)
        code, _out, err = _run("   ", str(self.master))
        self.assertEqual(code, 2)
        self.assertIn("usage", err)

    def test_non_utf8_corpus_exit_two(self) -> None:
        self.corpus.write_bytes(b"# Project lessons\n\n## 12. Bad encoding\n\n\xff\n")
        self._write(self.master, self._master_with("51. Keep rollout PR titles in sync", RULE_A))
        code, out, err = _run(str(self.corpus), str(self.master))
        self.assertEqual(code, 2)
        self.assertIn("ERROR:", err)
        self.assertNotIn("DUPLICATE:", out)

    def test_usage_error_exit_two(self) -> None:
        code, _out, err = _run()
        self.assertEqual(code, 2)
        self.assertIn("usage", err)
        code, _out, err = _run(str(self.corpus))
        self.assertEqual(code, 2)
        self.assertIn("usage", err)

    def test_extra_argument_exit_two(self) -> None:
        extra = self.dir / "extra.md"
        code, _out, err = _run(str(self.corpus), str(self.master), str(extra))
        self.assertEqual(code, 2)
        self.assertIn("usage", err)

    def test_unreadable_corpus_exit_two(self) -> None:
        if os.geteuid() == 0:
            self.skipTest("running as root; permission bits do not block reads")
        self._write(self.corpus, self._corpus_with("12. Keep rollout PR titles in sync", RULE_A))
        self._write(self.master, self._master_with("51. Keep rollout PR titles in sync", RULE_A))
        os.chmod(self.corpus, 0o000)
        self.addCleanup(os.chmod, self.corpus, 0o644)
        code, _out, err = _run(str(self.corpus), str(self.master))
        self.assertEqual(code, 2)
        self.assertIn("ERROR:", err)

    def test_unreadable_company_master_exit_two(self) -> None:
        if os.geteuid() == 0:
            self.skipTest("running as root; permission bits do not block reads")
        self._write(self.corpus, self._corpus_with("12. Keep rollout PR titles in sync", RULE_A))
        self._write(self.master, self._master_with("51. Keep rollout PR titles in sync", RULE_A))
        os.chmod(self.master, 0o000)
        self.addCleanup(os.chmod, self.master, 0o644)
        code, _out, err = _run(str(self.corpus), str(self.master))
        self.assertEqual(code, 2)
        self.assertIn("ERROR:", err)

    def test_exact_min_word_boundary_flagged(self) -> None:
        # Loud pin on the word counts so fixture drift is visible: the
        # duplicated body is exactly 25 normalized words (MIN_RULE_WORDS)
        # and must be flagged; the truncated variant is exactly 24 words
        # and must stay clean.
        words = EXACT_MIN_BODY.split()
        self.assertEqual(len(words), 25, "fixture drift: EXACT_MIN_BODY must be exactly 25 words")
        self._write(self.corpus, f"{EXACT_MIN_BODY}\n")
        self._write(self.master, f"{EXACT_MIN_BODY}\n")
        code, out, _err = _run(str(self.corpus), str(self.master))
        self.assertEqual(code, 1)
        self.assertIn("DUPLICATE:", out)
        truncated = " ".join(words[:24])
        self.assertEqual(len(truncated.split()), 24, "fixture drift: truncated variant must be exactly 24 words")
        self._write(self.corpus, f"{truncated}\n")
        self._write(self.master, f"{truncated}\n")
        code, out, _err = _run(str(self.corpus), str(self.master))
        self.assertEqual(code, 0)
        self.assertNotIn("DUPLICATE:", out)

    def test_shared_preamble_not_compared(self) -> None:
        # Content before the first heading is a preamble, not a block.
        # Folding-mutant rationale: the two headed bodies are IDENTICAL
        # short witnesses (under the 25-word floor), so a parse_blocks
        # change that folds the identical >=25-word preamble into the
        # first compared block pairs the preamble at ratio 1.0 and fails
        # this test; the correct parser compares only the short witness
        # pair, which stays under the floor, so the run is clean.
        self.assertGreaterEqual(len(EXACT_MIN_BODY.split()), 25)
        self._write(
            self.corpus,
            f"{EXACT_MIN_BODY}\n\n## 12. Rollout title witness\n\n{SHORT_POINTER}\n",
        )
        self._write(
            self.master,
            f"{EXACT_MIN_BODY}\n\n## 51. Rollout title witness\n\n{SHORT_POINTER}\n",
        )
        code, out, _err = _run(str(self.corpus), str(self.master))
        self.assertEqual(code, 0)
        self.assertNotIn("DUPLICATE:", out)

    def test_short_identical_body_stays_clean(self) -> None:
        self._write(self.corpus, self._corpus_with("12. Rollout witness", SHORT_POINTER))
        self._write(self.master, self._master_with("51. Rollout witness", SHORT_POINTER))
        code, out, _err = _run(str(self.corpus), str(self.master))
        self.assertEqual(code, 0)
        self.assertNotIn("DUPLICATE:", out)

    def test_fenced_hash_line_does_not_split(self) -> None:
        # A `#`-prefixed line inside a fenced code block is body text,
        # not a heading: the verbatim duplicated rule stays one block per
        # file and must still be flagged.
        body = (
            f"{RULE_A}\n\n"
            "```bash\n# not a heading: setup comment inside the fence\n"
            "echo check titles\n```\n"
        )
        self._write(self.corpus, self._corpus_with("12. Keep rollout PR titles in sync", body))
        self._write(self.master, self._master_with("51. Keep rollout PR titles in sync", body))
        code, out, _err = _run(str(self.corpus), str(self.master))
        self.assertEqual(code, 1)
        self.assertIn("DUPLICATE:", out)

    def test_distinct_fenced_content_stays_clean(self) -> None:
        # Identical prose but materially different fenced content (with
        # heading-like lines inside the fences) is one block per file;
        # the full-block ratio lands well under DUPLICATE_RATIO, so the
        # pair stays clean. A fence-blind parser would split at the
        # in-fence `##` lines and compare the identical prose fragments.
        corpus_body = (
            f"{RULE_A}\n\nRunbook excerpt:\n\n"
            "```text\n## Before merge: confirm title scope\n"
            "## After merge: log the title as scope of record\n```\n"
        )
        master_body = (
            f"{RULE_A}\n\nRunbook excerpt:\n\n"
            "~~~text\n## Grep the rollout diff for scope growth\n"
            "## Ask the author to retitle the request\n~~~\n"
        )
        self._write(self.corpus, self._corpus_with("12. Keep rollout PR titles in sync", corpus_body))
        self._write(self.master, self._master_with("51. Keep rollout PR titles in sync", master_body))
        code, out, _err = _run(str(self.corpus), str(self.master))
        self.assertEqual(code, 0)
        self.assertNotIn("DUPLICATE:", out)

    def test_reworded_beyond_ratio_threshold_clean(self) -> None:
        # Pins the upper side of DUPLICATE_RATIO: a topically related
        # but materially rewritten body must stay clean. Measured
        # SequenceMatcher(autojunk=False) ratio against RULE_A (block
        # text including normalized heading): 0.864, between 0.80 and
        # 0.87 and under the 0.90 threshold.
        reworded = (
            "When a configuration rollout widens the pull request scope beyond its "
            "original title, update the title before merge so reviewers can treat "
            "the title as the record of scope for audits and tracing of incidents."
        )
        self._write(self.corpus, self._corpus_with("12. Keep rollout PR titles in sync", reworded))
        self._write(self.master, self._master_with("51. Keep rollout PR titles in sync", RULE_A))
        code, out, _err = _run(str(self.corpus), str(self.master))
        self.assertEqual(code, 0)
        self.assertNotIn("DUPLICATE:", out)

    def test_heading_normalization_contract(self) -> None:
        module = _load_validator_module()
        self.assertEqual(module._normalize("## 12.3. Keep Rollout PR Titles"), "keep rollout pr titles")
        self.assertEqual(module._normalize("### 7. Rule"), "rule")
        self.assertEqual(module._normalize("##  Sloppy   heading  text "), "sloppy heading text")

    def test_stray_standalone_fence_not_clean(self) -> None:
        # A stray standalone fence line opens a fence that never closes;
        # the verbatim duplicated rule after it must not read as a clean
        # pass. With the unclosed-fence loud failure the run exits 2.
        corpus_text = (
            "# Project lessons\n\n## 12. Setup notes\n\n```\n\n"
            f"## 13. Keep rollout PR titles in sync\n\n{RULE_A}\n"
        )
        self._write(self.corpus, corpus_text)
        self._write(self.master, self._master_with("51. Keep rollout PR titles in sync", RULE_A))
        code, out, err = _run(str(self.corpus), str(self.master))
        self.assertEqual(code, 2)
        self.assertNotIn("DUPLICATE:", out)
        self.assertIn("ERROR: unclosed code fence", err)

    def test_inner_fence_inside_longer_wrapper_does_not_close(self) -> None:
        # An inner ``` line inside a ```` wrapper does not close the outer
        # fence (CommonMark: same character, run at least as long as the
        # opener, trailing whitespace only). The rule spanning the wrapper
        # stays one block per file and still matches.
        body = (
            f"{RULE_A}\n\n"
            "````text\n```bash\n# not a heading: inner fence\n```\n````\n"
        )
        self._write(self.corpus, self._corpus_with("12. Keep rollout PR titles in sync", body))
        self._write(self.master, self._master_with("51. Keep rollout PR titles in sync", body))
        code, out, _err = _run(str(self.corpus), str(self.master))
        self.assertEqual(code, 1)
        self.assertIn("DUPLICATE:", out)

    def test_unclosed_fence_exit_two(self) -> None:
        # A fence still open at EOF is a loud tool failure: exit 2 with
        # the ERROR line naming the file and the opening line on stderr.
        self._write(self.corpus, "# Project lessons\n\n## 12. Setup\n\n```bash\necho check titles\n")
        self._write(self.master, self._master_with("51. Keep rollout PR titles in sync", RULE_A))
        code, out, err = _run(str(self.corpus), str(self.master))
        self.assertEqual(code, 2)
        self.assertNotIn("DUPLICATE:", out)
        self.assertIn("ERROR: unclosed code fence", err)
        self.assertIn(str(self.corpus), err)
        self.assertIn("line 5", err)

    def test_zero_block_corpus_warns(self) -> None:
        # An existing corpus file that parses to zero blocks warns on
        # stderr (done WARNING semantics stop the commit); exit stays 0
        # so direct personal-repo runs keep the cold-start contract.
        self._write(self.corpus, "")
        self._write(self.master, self._master_with("51. Keep rollout PR titles in sync", RULE_A))
        code, _out, err = _run(str(self.corpus), str(self.master))
        self.assertEqual(code, 0)
        self.assertIn("WARNING:", err)
        self.assertIn(str(self.corpus), err)

    def test_h3_heading_splits_blocks(self) -> None:
        module = _load_validator_module()
        text = "# Top\nintro\n\n### Sub\nbody\n"
        blocks = module.parse_blocks(text)
        self.assertEqual([block.line for block in blocks], [1, 4])


if __name__ == "__main__":
    unittest.main()
