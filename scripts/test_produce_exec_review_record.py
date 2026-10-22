#!/usr/bin/env python3
"""Producer tests for the findings-bearing execution review record helper.

Pins the execute-plan Task 2 items over ``produce_exec_review_record``:

- the emitted Markdown record and ``.stats.json`` sidecar match the
  validator's current findings-bearing grammar, including every
  post-window fence a current-dated canonical record arms (freshness
  Metadata lines, record-kind twin, plan coverage pair, usage mint pair,
  self-heal chain state), and pass the validator's ``--hard`` CLI
  contract with a final ``OUTCOME: pass``;
- producer success keys on the validator's final outcome line, never on
  the exit code alone (soft mode reports ``OUTCOME: fail`` at exit 0);
  the success stdout ends with exactly one final ``OUTCOME: pass`` line;
- a malformed generated pair is refused with the record path and the
  validator's result, leaves no strand behind, and never claims a
  repair; an existing orphan sidecar is a named refusal too;
- the exit-3 tool_error family is pinned: malformed findings JSON, a
  missing plan file, a clean round with ``--last-fix-commit`` set, and a
  failed pair write (output-directory creation included) each end exit 3
  with a final ``OUTCOME: tool_error`` line;
- findings with varied severity and triage states keep the Markdown
  counts, sidecar findings, and validator parity rules in agreement;
- the empty-findings round stays a clear record and the repair-only
  tool's zero-findings posture is untouched by this module;
- repeated inputs give byte-identical outputs, and validator telemetry
  is isolated under the test's temporary metrics home (the Task 1
  posture; no ``--metrics-home`` override exists on the validator CLI,
  so the in-process invocation is the isolation seam).

Run from the repository root:

    PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_produce_exec_review_record.py'
"""

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def _load_from_path(module_name: str):
    """Import a scripts/ sibling by file path (scripts/ is not a package)."""
    spec = importlib.util.spec_from_file_location(
        module_name, SCRIPTS_DIR / (module_name + ".py")
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


producer = _load_from_path("produce_exec_review_record")
vrs = _load_from_path("validate_review_staging")

RUN_ID = "0123456789abcdef0123456789abcdef"
STARTED_MS = 1792669591737
DATE = "2026-10-22"
SLUG = "producer-demo"
PLAN_BODY = "# Sample plan\n\nA sample plan body for the producer tests.\n"

VARIED_FINDINGS = [
    {
        "id": 1,
        "title": "Critical blocking finding",
        "severity": "Critical",
        "blocking": True,
        "status": "new",
        "triage": "pending",
        "file": "scripts/demo.py",
        "line": 12,
        "note": "The gate exits zero on a malformed pair.",
    },
    {
        "id": 2,
        "title": "High blocking finding",
        "severity": "High",
        "blocking": True,
        "triage": "pending",
        "note": "The receipt digest binds to stale plan bytes.",
    },
    {
        "id": 3,
        "title": "Medium non-blocking finding",
        "severity": "Medium",
        "blocking": False,
        "triage": "pending",
        "note": "The docstring drifts from the match rule.",
    },
    {
        "id": 4,
        "title": "Low pending finding",
        "severity": "Low",
        "blocking": False,
        "triage": "pending",
        "note": "A comment names a dropped helper.",
    },
    {
        "id": 5,
        "title": "Low resolved finding on a second worker",
        "severity": "Low",
        "blocking": False,
        "triage": "dropped",
        "pattern": "testing#non-discriminating-pin",
        "workers": ["testing", "risk"],
        "note": "The pin passed identically under the old sweep.",
    },
]


class ProduceExecReviewRecordTest(unittest.TestCase):
    """The Task 2 producer arms over the unchanged validator CLI."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="produce-exec-review-")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.metrics_home = self.root / "metrics"
        if vrs.invocation_telemetry is not None:
            patcher = mock.patch.object(
                vrs.invocation_telemetry,
                "resolve_metrics_home",
                lambda: self.metrics_home,
            )
            patcher.start()
            self.addCleanup(patcher.stop)
        self.plan_path = self.root / "sample-plan.md"
        self.plan_path.write_text(PLAN_BODY, encoding="utf-8")

    # -- fixture and runner helpers ---------------------------------------

    def _write_findings_json(self, findings, name="findings.json"):
        path = self.root / name
        path.write_text(json.dumps({"findings": findings}), encoding="utf-8")
        return path

    def _argv(self, findings_json, out_dir, **overrides):
        argv = [
            "--out-dir", str(out_dir),
            "--session", "producer demo session",
            "--plan", str(self.plan_path),
            "--findings-json", str(findings_json),
            "--review-run-id", RUN_ID,
            "--review-started-at-ms", str(STARTED_MS),
            "--date", DATE,
            "--artifact-slug", SLUG,
        ]
        for key, value in overrides.items():
            argv.extend(["--" + key.replace("_", "-"), str(value)])
        return argv

    def _run_main(self, argv):
        out_buf, err_buf = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out_buf), contextlib.redirect_stderr(err_buf):
            code = producer.main(argv)
        return code, out_buf.getvalue(), err_buf.getvalue()

    def _produce_varied(self, out_dir_name="out"):
        findings_json = self._write_findings_json(VARIED_FINDINGS)
        out_dir = self.root / out_dir_name
        code, out, err = self._run_main(self._argv(findings_json, out_dir))
        self.assertEqual(code, 0, err + out)
        record = out_dir / f"{DATE}-plan-review-{SLUG}-r1.md"
        sidecar = record.with_suffix(".stats.json")
        return record, sidecar, out

    def _run_validator(self, argv):
        out_buf, err_buf = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out_buf), contextlib.redirect_stderr(err_buf):
            try:
                code = vrs.main(argv)
            except SystemExit as exc:
                code = exc.code
        return code, out_buf.getvalue(), err_buf.getvalue()

    def _final_outcomes(self, stdout_text):
        return [
            row.strip()
            for row in stdout_text.splitlines()
            if row.strip().startswith("OUTCOME:")
        ]

    # -- criterion 1: the validator's current findings-bearing grammar ----

    def test_produced_pair_passes_validator_hard_mode(self):
        """The emitted pair passes the validator's --hard CLI contract with
        a single final OUTCOME: pass line."""
        record, sidecar, _out = self._produce_varied()
        self.assertTrue(record.is_file())
        self.assertTrue(sidecar.is_file())
        code, out, err = self._run_validator(["--hard", str(record)])
        self.assertEqual(code, 0, err)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: pass"])

    def test_produced_record_carries_the_post_window_fences(self):
        """A current-dated canonical record arms every date fence: the four
        freshness Metadata lines plus the record-kind, coverage, mint-pair,
        and self-heal-state twins ride the emitted pair."""
        record, _sidecar, _out = self._produce_varied()
        markdown = record.read_text(encoding="utf-8")
        for expected in (
            "- Review mode: targeted",
            "- Changed-risk signals: none",
            "- Prior findings supplied as filter: no",
            "- Last fix commit: none",
            "- Record kind: canonical",
            "- Coverage: clean",
            f"- review-run-id: {RUN_ID}",
            f"- review-started-at-ms: {STARTED_MS}",
            "## Verdict for this round (before fixes)",
        ):
            self.assertIn(expected, markdown)
        payload = json.loads(record.with_suffix(".stats.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["record_kind"], "canonical")
        self.assertEqual(payload["date"], DATE)
        self.assertEqual(payload["round"], "r1")
        self.assertEqual(payload["review_mode"], "targeted")
        self.assertEqual(payload["coverage"]["outcome"], "clean")
        self.assertEqual(
            payload["extensions"]["convergence"]["self_heal_attempt"],
            {"status": "unused", "run_id": RUN_ID},
        )
        self.assertEqual(payload["source_kind"], "plan")
        self.assertEqual(payload["source_digest"], vrs.compute_source_digest(
            "plan", self.plan_path.read_bytes()
        ))

    def test_chain_round_two_carries_the_prior_state(self):
        """A round-2 record beside its valid round-1 record carries the
        prior chain state verbatim and still passes hard mode."""
        findings_json = self._write_findings_json(VARIED_FINDINGS)
        out_dir = self.root / "chain"
        code, out, err = self._run_main(self._argv(findings_json, out_dir))
        self.assertEqual(code, 0, err + out)
        code, out, err = self._run_main(
            self._argv(findings_json, out_dir, round=2)
        )
        self.assertEqual(code, 0, err + out)
        record = out_dir / f"{DATE}-plan-review-{SLUG}-r2.md"
        payload = json.loads(record.with_suffix(".stats.json").read_text(encoding="utf-8"))
        self.assertEqual(
            payload["extensions"]["convergence"]["self_heal_attempt"],
            {"status": "unused", "run_id": RUN_ID},
        )
        code, out, err = self._run_validator(["--hard", str(record)])
        self.assertEqual(code, 0, err)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: pass"])

    # -- criterion 2: the final outcome line, never the exit code alone ---

    def test_soft_mode_failure_shape_exists_at_exit_zero(self):
        """The trap arm: a malformed findings-bearing pair reports
        OUTCOME: fail at exit 0 in soft mode, so exit code zero alone can
        never satisfy the success contract."""
        record, _sidecar, _out = self._produce_varied()
        corrupted = record.read_text(encoding="utf-8").replace(
            "- **Blocking**: true", "- **Blocking**: false", 1
        )
        record.write_text(corrupted, encoding="utf-8")
        code, out, _err = self._run_validator([str(record)])
        self.assertEqual(code, 0)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: fail"])

    def test_success_requires_the_outcome_line_not_the_exit_code(self):
        """The producer's validation helper refuses an exit-0 run whose
        final outcome line is not OUTCOME: pass."""
        record, _sidecar, _out = self._produce_varied()
        with mock.patch.object(
            producer, "run_validator", return_value=(0, "evidence\nOUTCOME: fail\n", "")
        ):
            ok, outcome, evidence = producer.validate_generated_pair(record)
        self.assertFalse(ok)
        self.assertEqual(outcome, "fail")
        self.assertIn("OUTCOME: fail", evidence)
        with mock.patch.object(
            producer, "run_validator", return_value=(0, "evidence\nOUTCOME: pass\n", "")
        ):
            ok, outcome, _evidence = producer.validate_generated_pair(record)
        self.assertTrue(ok)
        self.assertEqual(outcome, "pass")

    def test_success_stdout_ends_with_one_final_outcome_pass_line(self):
        """The success path's stdout carries exactly one OUTCOME line, it is
        the final line, and it reads OUTCOME: pass."""
        findings_json = self._write_findings_json(VARIED_FINDINGS)
        out_dir = self.root / "outcome-line"
        code, out, _err = self._run_main(self._argv(findings_json, out_dir))
        self.assertEqual(code, 0, out)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: pass"])
        self.assertTrue(out.rstrip().endswith("OUTCOME: pass"))

    def test_validation_helper_refuses_a_corrupted_pair_directly(self):
        """The direct helper call on a corrupted temp pair reports the
        failure with the validator's outcome and evidence naming the
        record's conservation defect."""
        record, _sidecar, _out = self._produce_varied()
        corrupted = record.read_text(encoding="utf-8").replace(
            "- **Blocking**: true", "- **Blocking**: false", 1
        )
        record.write_text(corrupted, encoding="utf-8")
        ok, outcome, evidence = producer.validate_generated_pair(record)
        self.assertFalse(ok)
        self.assertEqual(outcome, "fail")
        self.assertIn(str(record), evidence)
        self.assertIn("finding conservation: finding 1 blocking disagrees", evidence)

    # -- criterion 3: a malformed generated pair is refused ---------------

    def test_malformed_pair_refused_with_path_and_validator_result(self):
        """Mutating the emitted bytes before validation makes the produce
        flow refuse: the refusal names the record path, carries the
        validator's result, ends OUTCOME: fail at exit 1, and strands no
        pair on disk."""
        findings_json = self._write_findings_json(VARIED_FINDINGS)
        out_dir = self.root / "refused"

        def corrupt_write(out_dir_arg, record_name, markdown, payload):
            markdown = markdown.replace(
                "- **Blocking**: true", "- **Blocking**: false", 1
            )
            return original_write_pair(out_dir_arg, record_name, markdown, payload)

        record_path = out_dir / f"{DATE}-plan-review-{SLUG}-r1.md"
        original_write_pair = producer.write_pair
        with mock.patch.object(producer, "write_pair", side_effect=corrupt_write):
            code, out, err = self._run_main(self._argv(findings_json, out_dir))
        self.assertEqual(code, 1)
        self.assertIn(f"REFUSED: validator outcome 'fail' for record {record_path}", out)
        self.assertIn("finding conservation: finding 1 blocking disagrees", out)
        self.assertTrue(out.rstrip().endswith("OUTCOME: fail"))
        self.assertFalse(record_path.exists(), "a refused pair must not strand its record")
        self.assertFalse(
            record_path.with_suffix(".stats.json").exists(),
            "a refused pair must not strand its sidecar",
        )

    def test_tool_error_arms_exit_three_with_final_tool_error_line(self):
        """The exit-3 tool_error family: invalid findings JSON, a missing
        plan file, and a clean round with --last-fix-commit set under a
        non-fresh-adversarial mode each end exit 3 with a single final
        OUTCOME: tool_error line on stdout."""
        # Arm 1: malformed findings JSON.
        bad_json = self.root / "bad.json"
        bad_json.write_text("{not json", encoding="utf-8")
        code, out, err = self._run_main(self._argv(bad_json, self.root / "arm1"))
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: tool_error"])
        self.assertIn("is not valid JSON", err)
        # Arm 2: missing plan file.
        findings_json = self._write_findings_json(VARIED_FINDINGS, name="armed.json")
        argv = self._argv(findings_json, self.root / "arm2")
        argv[argv.index("--plan") + 1] = str(self.root / "missing-plan.md")
        code, out, err = self._run_main(argv)
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: tool_error"])
        self.assertIn("plan file not found", err)
        # Arm 3: clean round with --last-fix-commit set (targeted mode).
        empty_json = self._write_findings_json([], name="clean-armed.json")
        code, out, err = self._run_main(
            self._argv(empty_json, self.root / "arm3", last_fix_commit="abc123def")
        )
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: tool_error"])
        self.assertIn("requires --review-mode fresh-adversarial", err)

    def test_uncreatable_out_dir_ends_tool_error_without_a_half_pair(self):
        """An OSError raised while creating the output directory ends exit 3
        with a final OUTCOME: tool_error line and leaves no half-written
        pair behind."""
        blocker = self.root / "blocker"
        blocker.write_text("a file, not a directory\n", encoding="utf-8")
        findings_json = self._write_findings_json(VARIED_FINDINGS, name="mkdir.json")
        out_dir = blocker / "nested"
        code, out, err = self._run_main(self._argv(findings_json, out_dir))
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: tool_error"])
        self.assertIn("both halves removed", err)
        self.assertEqual(list(out_dir.glob("*")), [])

    # -- criterion 4: varied findings keep the parity rules ---------------

    def test_varied_findings_markdown_and_sidecar_agree(self):
        """Counts and per-finding data agree across the Markdown record,
        the sidecar, and the validator's parity rules: block count,
        severity, blocking, and triage per id; the declared counts
        surfaces; the severity-group ordering; and the per-worker panel
        attribution."""
        record, sidecar, _out = self._produce_varied()
        markdown = record.read_text(encoding="utf-8")
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
        findings = payload["findings"]
        self.assertEqual(len(findings), len(VARIED_FINDINGS))

        md_findings = vrs.parse_markdown_findings(markdown)
        self.assertEqual(len(md_findings), len(findings))
        md_by_id = {row["id"]: row for row in md_findings}
        for row in findings:
            md_row = md_by_id[row["id"]]
            self.assertEqual(md_row["severity"], row["severity"])
            self.assertEqual(md_row["blocking"], row["blocking"])
            self.assertEqual(md_row["triage"], row["triage"])
            self.assertEqual(md_row["pattern"], row["pattern"])

        self.assertEqual(payload["counts"]["staged_findings"], len(findings))
        self.assertIn(f"- Findings: {len(findings)}", markdown)
        self.assertIn(f"- Staged findings: {len(findings)}", markdown)
        self.assertIn(
            f"| Worker | Lenses | Parent worker | Status | Raw | Solo | Echo | Relaunch |",
            markdown,
        )
        # The testing worker stages exactly one shared echo row (finding 5's
        # two-worker attribution: raw 1, solo 0, echo 1); risk mirrors it.
        self.assertIn("| testing | testing | none | complete | 1 | 0 | 1 | no |", markdown)
        self.assertIn("| risk | security | none | complete | 1 | 0 | 1 | no |", markdown)
        # Severity groups sit in canonical order with ascending ids inside
        # each group (the validator's finding-order rule).
        order = [row["id"] for row in findings]
        ranks = [vrs.SEVERITY_ORDER.index(row["severity"]) for row in findings]
        self.assertEqual(ranks, sorted(ranks))
        lows = [row["id"] for row in findings if row["severity"] == "Low"]
        self.assertEqual(lows, sorted(lows))
        self.assertEqual(order, [1, 2, 3, 4, 5])

    # -- criterion 5: empty findings and the repair-only boundary ---------

    def test_empty_findings_produce_a_valid_clear_round(self):
        """The empty findings set emits a valid clear round (canonical
        clean verdict shape, verdict yes) that passes hard mode."""
        findings_json = self._write_findings_json([], name="empty.json")
        out_dir = self.root / "clear"
        code, out, err = self._run_main(self._argv(findings_json, out_dir))
        self.assertEqual(code, 0, err + out)
        record = out_dir / f"{DATE}-plan-review-{SLUG}-r1.md"
        markdown = record.read_text(encoding="utf-8")
        self.assertIn("0 Medium+ findings; clear round", markdown)
        payload = json.loads(record.with_suffix(".stats.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["findings"], [])
        self.assertEqual(payload["verdict"], "yes")
        code, out, err = self._run_validator(["--hard", str(record)])
        self.assertEqual(code, 0, err)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: pass"])

    def test_producer_never_repairs_or_touches_an_existing_record(self):
        """The producer only creates pairs: an existing target record is a
        named refusal, its bytes stay untouched, and no outcome claims a
        repair (the zero-findings repair posture stays owned by
        scripts/regenerate_review_sidecar.py, which this module never
        imports or edits)."""
        record, sidecar, out = self._produce_varied()
        for text in (out,):
            self.assertNotIn("repair", text.lower())
        before_record = record.read_bytes()
        before_sidecar = sidecar.read_bytes()
        findings_json = self._write_findings_json(VARIED_FINDINGS, name="again.json")
        code, out, _err = self._run_main(self._argv(findings_json, self.root / "out"))
        self.assertEqual(code, 1)
        self.assertIn("refusing to write an existing record", out)
        self.assertIn(str(record), out)
        self.assertNotIn("repair", out.lower())
        self.assertEqual(record.read_bytes(), before_record)
        self.assertEqual(sidecar.read_bytes(), before_sidecar)

    def test_orphan_sidecar_refused_without_overwrite(self):
        """An existing sidecar without its record is a named refusal too:
        the orphan sidecar stays byte-identical and no new pair appears."""
        record, sidecar, _out = self._produce_varied()
        before_sidecar = sidecar.read_bytes()
        record.unlink()
        findings_json = self._write_findings_json(VARIED_FINDINGS, name="orphan.json")
        code, out, _err = self._run_main(self._argv(findings_json, self.root / "out"))
        self.assertEqual(code, 1)
        self.assertIn("refusing to overwrite an existing sidecar", out)
        self.assertIn(str(sidecar), out)
        self.assertEqual(sidecar.read_bytes(), before_sidecar)
        self.assertFalse(record.exists())

    # -- criterion 6: deterministic bytes and isolated telemetry ----------

    def test_repeated_inputs_give_byte_identical_outputs(self):
        """The same inputs produce byte-identical Markdown and sidecar
        bytes in a fresh output directory."""
        _record, _sidecar, _out = self._produce_varied()
        first = (self.root / "out" / f"{DATE}-plan-review-{SLUG}-r1.md")
        findings_json = self._write_findings_json(VARIED_FINDINGS, name="repeat.json")
        out_dir = self.root / "repeat"
        code, out, err = self._run_main(self._argv(findings_json, out_dir))
        self.assertEqual(code, 0, err + out)
        second = out_dir / f"{DATE}-plan-review-{SLUG}-r1.md"
        self.assertEqual(
            first.read_bytes(), second.read_bytes(), "Markdown bytes must be identical"
        )
        self.assertEqual(
            first.with_suffix(".stats.json").read_bytes(),
            second.with_suffix(".stats.json").read_bytes(),
            "Sidecar bytes must be identical",
        )

    def test_validator_telemetry_stays_under_the_temp_metrics_home(self):
        """Validator telemetry appends into the test's temporary metrics
        home, never into the repository; no telemetry lands inside the
        producer's output directory either."""
        if vrs.invocation_telemetry is None:
            self.skipTest("invocation telemetry sibling absent (fail-open copy)")
        record, _sidecar, _out = self._produce_varied()
        metrics_log = self.metrics_home / vrs.invocation_telemetry.INVOCATION_COSTS_FILENAME
        self.assertTrue(metrics_log.is_file())
        rows = [
            json.loads(line)
            for line in metrics_log.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertGreaterEqual(len(rows), 1)
        self.assertTrue(
            all(row.get("script") == "validate_review_staging.py" for row in rows)
        )
        self.assertEqual(
            list((self.root / "out").glob("**/invocation-costs.jsonl")),
            [],
            "no telemetry file may land in the producer's output directory",
        )


if __name__ == "__main__":
    unittest.main()
