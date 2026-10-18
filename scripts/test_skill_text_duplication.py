#!/usr/bin/env python3
"""Tests for scripts/skill_text_duplication.py (plan 2026-10-10-anti-growth-rule-set, Task 2)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skill_text_duplication.py")


class SkillTextDuplicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="stdup-test-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        # a.md: 20 words, the 10-word shingle "a b c d e f g h i j" occurs twice
        # -> repeated_span_pct 100.0 (all 20 words covered)
        self.write("a.md", "a b c d e f g h i j " * 2 + "\n")
        # b.md: shares the same 10-gram with a.md once -> intersection 1
        self.write("b.md", "a b c d e f g h i j x y z\n")
        # c.md: duplicated sentence of >=60 normalized chars, twice
        sent = ("this long diagnostic sentence exists exactly twice here so the "
                "duplicated sentence detector must report it with count two.")
        self.write("c.md", sent + " One tail.\n\n" + sent + " Other tail.\n")
        # d.md: fewer than 10 words -> degenerate 0.0
        self.write("d.md", "tiny file\n")
        # e.md: empty file -> degenerate 0.0
        self.write("e.md", "")
        # excluded subtree
        os.makedirs(os.path.join(self.tmp, "docs", "history"))
        self.write(os.path.join("docs", "history", "archived.md"), "a b c d e f g h i j " * 2 + "\n")

    def write(self, rel, content):
        path = os.path.join(self.tmp, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(content)
        return path

    def run_script(self, *args):
        proc = subprocess.run(
            [sys.executable, SCRIPT] + list(args),
            capture_output=True, text=True, cwd=self.tmp,
        )
        return proc

    def test_repeated_span_math(self):
        out = self.run_script("--json", self.tmp)
        self.assertEqual(out.returncode, 0)
        self.assertIn("OUTCOME: pass", out.stderr)
        data = json.loads(out.stdout.split("OUTCOME: pass")[0])
        by_path = {f["path"]: f for f in data["files"]}
        a = by_path[os.path.join(self.tmp, "a.md")]
        self.assertEqual(a["words"], 20)
        self.assertEqual(a["repeated_span_pct"], 100.0)

    def test_duplicated_sentence_detection(self):
        out = self.run_script("--json", self.tmp)
        data = json.loads(out.stdout.split("OUTCOME: pass")[0])
        c = {f["path"]: f for f in data["files"]}[os.path.join(self.tmp, "c.md")]
        self.assertEqual(len(c["duplicated_sentences"]), 1)
        text, count = c["duplicated_sentences"][0]
        self.assertEqual(count, 2)
        self.assertGreaterEqual(len(text), 60)

    def test_cross_file_intersection(self):
        out = self.run_script("--json", self.tmp)
        data = json.loads(out.stdout.split("OUTCOME: pass")[0])
        pairs = {(p["path_a"], p["path_b"]): p["shared_shingles"] for p in data["pairs"]}
        key = (os.path.join(self.tmp, "a.md"), os.path.join(self.tmp, "b.md"))
        self.assertEqual(pairs[key], 1)

    def test_degenerate_files_report_zero(self):
        out = self.run_script("--json", self.tmp)
        data = json.loads(out.stdout.split("OUTCOME: pass")[0])
        by_path = {f["path"]: f for f in data["files"]}
        self.assertEqual(by_path[os.path.join(self.tmp, "d.md")]["repeated_span_pct"], 0.0)
        self.assertEqual(by_path[os.path.join(self.tmp, "e.md")]["repeated_span_pct"], 0.0)

    def test_history_subtree_excluded(self):
        out = self.run_script("--json", self.tmp)
        data = json.loads(out.stdout.split("OUTCOME: pass")[0])
        self.assertNotIn(os.path.join(self.tmp, "docs", "history", "archived.md"),
                         [f["path"] for f in data["files"]])

    def test_exit_contract_usage_error(self):
        proc = self.run_script("--bogus")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("OUTCOME: fail", proc.stdout)
        self.assertNotIn("exit 2", proc.stderr)

    def test_usage_error_top_without_value(self):
        proc = self.run_script("--top")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("OUTCOME: fail", proc.stdout)

    def test_unreadable_input_fails(self):
        proc = self.run_script(os.path.join(self.tmp, "no-such-dir"))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("OUTCOME: fail", proc.stdout)

    def test_non_markdown_input_fails(self):
        path = os.path.join(self.tmp, "plain.txt")
        with open(path, "w") as fh:
            fh.write("words words\n")
        proc = self.run_script(path)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("OUTCOME: fail", proc.stdout)

    def test_read_only_proof(self):
        before = []
        for root, dirs, files in os.walk(self.tmp):
            for f in files:
                p = os.path.join(root, f)
                st = os.stat(p)
                before.append((p, st.st_size, st.st_mtime_ns))
        status_before = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, cwd=self.tmp
        ).stdout if os.path.isdir(os.path.join(self.tmp, ".git")) else None
        proc = self.run_script(self.tmp)
        self.assertEqual(proc.returncode, 0)
        after = []
        for root, dirs, files in os.walk(self.tmp):
            for f in files:
                p = os.path.join(root, f)
                st = os.stat(p)
                after.append((p, st.st_size, st.st_mtime_ns))
        self.assertEqual(sorted(before), sorted(after))
        if status_before is not None:
            status_after = subprocess.run(
                ["git", "status", "--porcelain"], capture_output=True, text=True, cwd=self.tmp
            ).stdout
            self.assertEqual(status_before, status_after)

    def test_determinism(self):
        one = self.run_script("--json", self.tmp).stdout
        two = self.run_script("--json", self.tmp).stdout
        self.assertEqual(one, two)
        one_h = self.run_script(self.tmp).stdout
        two_h = self.run_script(self.tmp).stdout
        self.assertEqual(one_h, two_h)

    def test_json_shape_contract(self):
        out = self.run_script("--json", self.tmp)
        data = json.loads(out.stdout.split("OUTCOME: pass")[0])
        self.assertEqual(set(data.keys()), {"files", "pairs"})
        for f in data["files"]:
            self.assertEqual(set(f.keys()), {"path", "words", "repeated_span_pct", "duplicated_sentences"})
        for p in data["pairs"]:
            self.assertEqual(set(p.keys()), {"path_a", "path_b", "shared_shingles"})
        paths = [f["path"] for f in data["files"]]
        self.assertEqual(paths, sorted(paths))
        pair_keys = [(p["path_a"], p["path_b"]) for p in data["pairs"]]
        self.assertEqual(pair_keys, sorted(pair_keys))


if __name__ == "__main__":
    unittest.main()
