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

Range arm (producer code-family record arm plan, Task 1): every fixture
is a hermetic scratch git repo under TemporaryDirectory (the
``scripts/test_corrections_record.py`` ``build_scratch_repo`` pattern),
the process cwd is pinned to a non-repository workspace so the range arm
can never satisfy itself from ambient cwd, and the range inputs resolve
before any git diff call. Pinned: the code-family filename and sidecar
``source_kind``, the base/head-derived title, URL, and digest annotation
lines with the digest equal to the SHA-256 of
``corrections_record.reviewed_scope_bytes()`` output, the option-shaped
and unresolvable half refusals ahead of any ``reviewed_scope_bytes``
call, the bookkeeping-only, empty reviewed-scope, and git-plumbing-failure
pre-write refusals,
the mutually exclusive ``--plan``/``--range`` usage errors, the
raw-hash-inequality plus subprocess ``verify-digest`` acceptance over a
mixed range, the range-mode surface pins (explicit ``--artifact-slug``,
the ``- Type:`` code-family label, the relaxed findings-JSON ``plan``
cross-check, the out-dir-anchored repo root), and
``extensions.certified_range`` recording the resolved base and head.

Flag surface and lens-table single-homing (producer code-family record
arm plan, Task 2): ``--review-type`` is removed from the CLI (any
invocation naming it is the argparse usage tool error ending exit 3 with
a final ``OUTCOME: tool_error`` line); the narrowed ``--review-mode``
set is named once as the producer constant ``SUPPORTED_REVIEW_MODES``
(exactly the modes the builder truthfully renders for findings-bearing
rounds) and enforced once in ``build_context``, the funnel both surfaces
share, with the argparse ``choices`` derived from that same constant so
the flag and findings-JSON refusals name one set; the clean-round
contradiction stays owned by the two existing guards (the last-fix
freshness gate pre-write, the validator's clean-verdict contradiction
post-write) and is never duplicated here; the five worker/lens
associations single-home in one ordered producer constant whose rendered
Markdown and sidecar surfaces equal the projection of
``vrs.REQUIRED_PANEL_LENSES``; and ``ctx["verdict_field"]`` computes in
``build_context`` so ``build_markdown`` and ``build_payload`` are pure
readers (each builder called twice yields identical output with no
context mutation, and ``build_payload`` runs first without depending on
``build_markdown``).

Self-heal chain rewiring (producer-code-family-record-arm plan, Task 2):
the producer reads the chain grammar from the validator's public seam
instead of re-encoding it. A source-level drift canary pins that the
producer source defines none of the three chain-grammar functions nor
the round-tail regex constant and reaches none of the validator
privates, while the ``vrs.self_heal_chain_state(`` and
``vrs.calendar_valid_record_date(`` call sites are present; a
delegation pin monkeypatches the seam function on the validator module
the producer imported and asserts ``build_context`` carries its return;
the ambiguity mapping turns the seam's ambiguous-predecessor raise into
the producer refusal carrying the exact message text; and the
non-calendar ``--date`` tool-error refusal is pinned as a regression
arm.

Run from the repository root:

    PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_produce_exec_review_record.py'
"""

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import subprocess
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
corrections_record = _load_from_path("corrections_record")
guard = _load_from_path("reverse_squash_guard")

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

    # -- focused-panel inputs (codex-plan-review-producer-focused-panel) --

    def _focused_argv(self, findings_json, out_dir, workers, reason=None):
        argv = [
            "--out-dir", str(out_dir),
            "--session", "producer demo session",
            "--plan", str(self.plan_path),
            "--findings-json", str(findings_json),
            "--review-run-id", RUN_ID,
            "--review-started-at-ms", str(STARTED_MS),
            "--date", DATE,
            "--artifact-slug", SLUG,
            "--panel-mode", "focused",
        ]
        for worker in workers:
            argv.extend(["--worker", worker])
        if reason is not None:
            argv.extend(["--selection-reason", reason])
        return argv

    def test_focused_pair_passes_validator_hard_mode(self):
        """A focused mint emits panel rows, worker counts, and coverage
        lenses only for the workers that ran, carries the sidecar
        panel_mode/selection_reason pair, and passes hard mode."""
        findings_json = self._write_findings_json(VARIED_FINDINGS, name="focused.json")
        out_dir = self.root / "focused"
        code, out, err = self._run_main(
            self._focused_argv(
                findings_json,
                out_dir,
                ["correctness-completeness", "testing"],
                "docs-only normative plan; focused contract-docs plus "
                "correctness-completeness panel per the selection policy",
            )
        )
        self.assertEqual(code, 0, err + out)
        record = out_dir / f"{DATE}-plan-review-{SLUG}-r1.md"
        payload = json.loads(record.with_suffix(".stats.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["panel_mode"], "focused")
        self.assertIn("selection policy", payload["selection_reason"])
        self.assertEqual(payload["counts"]["workers_launched"], 2)
        self.assertEqual(
            [row["worker"] for row in payload["panel"]],
            ["correctness-completeness", "testing"],
        )
        expected_lenses = sorted(
            {lens for lens in vrs.REQUIRED_PANEL_LENSES["correctness-completeness"]}
            | set(vrs.REQUIRED_PANEL_LENSES["testing"])
        )
        self.assertEqual(payload["coverage"]["material_lens_set"], expected_lenses)
        self.assertEqual(payload["coverage"]["completed"], expected_lenses)
        markdown = record.read_text(encoding="utf-8")
        self.assertIn("- Panel mode: focused", markdown)
        self.assertIn("- Selection reason:", markdown)
        self.assertIn("- Workers launched: 2", markdown)
        self.assertNotIn("| contract-docs |", markdown)
        code, out, err = self._run_validator(["--hard", str(record)])
        self.assertEqual(code, 0, err)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: pass"])

    def test_duplicate_worker_flags_dedupe_to_one_launch(self):
        """A repeated --worker names one launch: the worker appears once
        in the panel rows and workers_launched counts distinct workers,
        so the pair stays consistent pre-write."""
        findings_json = self._write_findings_json(VARIED_FINDINGS, name="dup.json")
        out_dir = self.root / "dup"
        code, out, err = self._run_main(
            self._focused_argv(
                findings_json, out_dir, ["testing", "testing"], "single-worker round"
            )
        )
        self.assertEqual(code, 0, err + out)
        record = out_dir / f"{DATE}-plan-review-{SLUG}-r1.md"
        payload = json.loads(record.with_suffix(".stats.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["counts"]["workers_launched"], 1)
        self.assertEqual([row["worker"] for row in payload["panel"]], ["testing"])
        code, out, err = self._run_validator(["--hard", str(record)])
        self.assertEqual(code, 0, err)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: pass"])

    def test_full_panel_defaults_unchanged_without_the_new_flags(self):
        """A mint without the new flags keeps the historical full shape:
        panel_mode full, null selection_reason, five launched workers."""
        findings_json = self._write_findings_json(VARIED_FINDINGS, name="full.json")
        out_dir = self.root / "full"
        code, _out, err = self._run_main(self._argv(findings_json, out_dir))
        self.assertEqual(code, 0, err)
        record = out_dir / f"{DATE}-plan-review-{SLUG}-r1.md"
        payload = json.loads(record.with_suffix(".stats.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["panel_mode"], "full")
        self.assertIsNone(payload["selection_reason"])
        self.assertEqual(payload["counts"]["workers_launched"], 5)
        self.assertEqual(len(payload["panel"]), 5)

    def test_focused_input_refusal_arms(self):
        """Each malformed focused/full flag pairing is a named pre-write
        refusal (exit 1, no pair written)."""
        findings_json = self._write_findings_json(VARIED_FINDINGS, name="ref.json")
        arms = [
            ("no workers", self._focused_argv(findings_json, self.root / "r1", [], "reason")),
            (
                "no reason",
                self._focused_argv(
                    findings_json, self.root / "r2", ["correctness-completeness"], None
                ),
            ),
            (
                "unknown worker",
                self._focused_argv(
                    findings_json, self.root / "r3", ["correctness-completeness", "ghost"], "reason"
                ),
            ),
            (
                "reason with full",
                self._argv(findings_json, self.root / "r4", selection_reason="reason"),
            ),
            (
                "worker with full",
                self._argv(findings_json, self.root / "r5", worker="testing"),
            ),
            (
                "newline-bearing reason",
                self._focused_argv(
                    findings_json,
                    self.root / "r6",
                    ["testing"],
                    "line one\nline two",
                ),
            ),
            (
                "whitespace-only reason",
                self._focused_argv(findings_json, self.root / "r7", ["testing"], "   "),
            ),
        ]
        for label, argv in arms:
            with self.subTest(arm=label):
                code, out, err = self._run_main(argv)
                self.assertEqual(code, 1, f"{label}: {out}{err}")
                self.assertIn("REFUSED", out)
                self.assertEqual(list(self.root.glob("r[0-9]")), [])


class RangeArmTest(unittest.TestCase):
    """Task 1 range arm: `--range base...head` emits the code-family pair.

    Every fixture is a hermetic scratch git repo (the
    corrections_record.build_scratch_repo pattern); the process cwd is
    pinned to a non-repository workspace so repo-root resolution can
    never succeed from ambient cwd, making the out-dir anchor the only
    live source."""

    CODE_FAMILY_LABEL = "Code Review"

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="produce-range-arm-")
        self.addCleanup(tmp.cleanup)
        self.workspace = Path(tmp.name)
        # Pin cwd to the non-repository workspace for every test: the
        # range arm must resolve the repo from the out-dir anchor only.
        self._original_cwd = os.getcwd()
        os.chdir(self.workspace)
        self.addCleanup(os.chdir, self._original_cwd)
        # Sanitize the ambient GIT_* family (the corrections_record
        # hermetic_git_env posture): no host git override may steer the
        # scratch-repo resolution the range arm rides.
        self._original_git_env = {
            key: value
            for key, value in os.environ.items()
            if key.startswith("GIT_")
        }
        for key in self._original_git_env:
            del os.environ[key]
        self.addCleanup(self._restore_git_env)
        self.metrics_home = self.workspace / "metrics"
        if vrs.invocation_telemetry is not None:
            patcher = mock.patch.object(
                vrs.invocation_telemetry,
                "resolve_metrics_home",
                lambda: self.metrics_home,
            )
            patcher.start()
            self.addCleanup(patcher.stop)
        self.findings = [
            {
                "id": 1,
                "title": "Range finding on reviewed code",
                "severity": "Medium",
                "blocking": False,
                "file": "src/beta.py",
                "line": 1,
                "note": "The reviewed delta introduces the unchecked return.",
            }
        ]
        self.repo, self.base_sha, self.head_sha = self._build_range_repo()
        self.findings_json = self.workspace / "range-findings.json"
        self.findings_json.write_text(
            json.dumps({"findings": self.findings}), encoding="utf-8"
        )
        self.out_dir = self.repo.root / "out"

    def _restore_git_env(self):
        for key, value in self._original_git_env.items():
            os.environ[key] = value

    def _build_range_repo(self):
        """Scratch repo whose base...head delta mixes a reviewed path with
        the docs/history/backlog/ bookkeeping prefix the reviewed-scope
        helper excludes."""
        repo = corrections_record.build_scratch_repo(self, name="range-repo")
        base = repo.commit_file(
            "src/alpha.py", "def alpha():\n    return 1\n", "seed alpha"
        )
        repo.commit_file(
            "docs/history/backlog/zz-bookkeeping-row.md",
            "bookkeeping row note\n",
            "bookkeeping row",
        )
        head = repo.commit_file(
            "src/beta.py", "def beta():\n    return 2\n", "feature beta"
        )
        return repo, base, head

    def _argv(self, out_dir, **overrides):
        range_value = overrides.pop("range", f"{self.base_sha}...{self.head_sha}")
        argv = [
            "--out-dir", str(out_dir),
            "--session", "range arm session",
            # The equals form is the only CLI spelling that hands a
            # leading-dash value to the producer instead of argparse
            # refusing it as an unknown option first.
            f"--range={range_value}",
            "--findings-json", str(self.findings_json),
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
            try:
                code = producer.main(argv)
            except SystemExit as exc:  # argparse usage-error channel
                code = exc.code
        return code, out_buf.getvalue(), err_buf.getvalue()

    def _final_outcomes(self, text):
        return [
            row.strip()
            for row in text.splitlines()
            if row.strip().startswith("OUTCOME:")
        ]

    def _produce_range(self, out_dir=None, **overrides):
        out_dir = Path(out_dir if out_dir is not None else self.out_dir)
        code, out, err = self._run_main(self._argv(out_dir, **overrides))
        self.assertEqual(code, 0, err + out)
        record = out_dir / f"{DATE}-{SLUG}-code-review-r1.md"
        self.assertTrue(record.is_file(), out)
        return record, out

    def test_focused_range_mode_mint_passes_hard_mode(self):
        """The focused selection applies to a range (code-family) mint the
        same way: rows, launch count, and coverage lenses derive from the
        named workers, and the pair passes hard mode."""
        out_dir = self.out_dir / "focused-range"
        argv = [
            *self._argv(out_dir),
            "--panel-mode", "focused",
            "--worker", "testing",
            "--selection-reason", "focused follow-up over a two-commit range",
        ]
        code, out, err = self._run_main(argv)
        self.assertEqual(code, 0, err + out)
        record = out_dir / f"{DATE}-{SLUG}-code-review-r1.md"
        payload = json.loads(record.with_suffix(".stats.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["panel_mode"], "focused")
        self.assertEqual(payload["counts"]["workers_launched"], 1)
        self.assertEqual(
            payload["coverage"]["material_lens_set"],
            sorted(vrs.REQUIRED_PANEL_LENSES["testing"]),
        )
        code, out, err = self._run_validator_hard(record)
        self.assertEqual(code, 0, err)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: pass"])

    def _no_scope_calls(self):
        """Patch reviewed_scope_bytes to record any call; returns the calls
        list for the not-called assertions."""
        calls = []
        patcher = mock.patch.object(
            producer.corrections_record,
            "reviewed_scope_bytes",
            side_effect=lambda *a: calls.append(a) or (corrections_record.SCOPE_UNRESOLVED, None),
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        return calls

    # -- checkbox 1: the pair exists with the code-family truth shape -----

    def test_range_invocation_writes_code_family_pair(self):
        """A range invocation writes a pair named
        {date}-{slug}-code-review-rN.md whose sidecar declares
        source_kind "code" and whose producer run ends OUTCOME: pass in
        hard mode."""
        record, out = self._produce_range()
        self.assertEqual(
            record.name, f"{DATE}-{SLUG}-code-review-r1.md"
        )
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: pass"])
        payload = json.loads(record.with_suffix(".stats.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["source_kind"], "code")
        markdown = record.read_text(encoding="utf-8")
        self.assertTrue(markdown.startswith(f"# {self.CODE_FAMILY_LABEL}: "))
        code, vout, verr = self._run_validator_hard(record)
        self.assertEqual(code, 0, verr)
        self.assertEqual(self._final_outcomes(vout), ["OUTCOME: pass"])

    def _run_validator_hard(self, record):
        out_buf, err_buf = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out_buf), contextlib.redirect_stderr(err_buf):
            try:
                code = vrs.main(["--hard", str(record)])
            except SystemExit as exc:
                code = exc.code
        return code, out_buf.getvalue(), err_buf.getvalue()

    # -- checkbox 2: surfaces derive from base and head, digest domain ----

    def test_range_record_surfaces_derive_from_base_and_head(self):
        """The title, URL or Artifact, and digest annotation lines derive
        from the recorded base and head with no plan reference, and the
        Source digest equals the SHA-256 of the range's
        reviewed_scope_bytes output."""
        record, _out = self._produce_range()
        markdown = record.read_text(encoding="utf-8")
        outcome, scope_bytes = corrections_record.reviewed_scope_bytes(
            self.repo.root, self.base_sha, self.head_sha
        )
        self.assertEqual(outcome, corrections_record.SCOPE_BYTES)
        expected_digest = corrections_record.sha256_hex(scope_bytes)
        self.assertIn(f"(range {self.base_sha}...{self.head_sha})", markdown)
        self.assertIn(
            f"- URL or Artifact: {self.base_sha}...{self.head_sha}", markdown
        )
        self.assertIn(
            f"- Source digest: {expected_digest} "
            f"(sha256 of reviewed-scope bytes "
            f"{self.base_sha}...{self.head_sha})",
            markdown,
        )
        self.assertNotIn("plan", markdown.lower(), "a code-family record carries no plan reference")
        payload = json.loads(record.with_suffix(".stats.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["source_digest"], expected_digest)

    # -- checkbox 3: range inputs resolve before any git diff call --------

    def test_option_shaped_half_refuses_before_any_scope_call(self):
        """A base or head half beginning with '-' refuses as tool_error
        before any reviewed_scope_bytes call and no pair is written; both
        halves are exercised."""
        calls = self._no_scope_calls()
        for bad_range in (
            f"-weird-ref...{self.head_sha}",  # option-shaped base half
            f"{self.base_sha}...-odd-head",  # option-shaped head half
        ):
            code, out, err = self._run_main(
                self._argv(self.out_dir, range=bad_range)
            )
            self.assertEqual(code, 3)
            self.assertEqual(self._final_outcomes(out), ["OUTCOME: tool_error"])
            self.assertIn("option-shaped", err)
        self.assertEqual(calls, [], "no reviewed_scope_bytes call may precede the refusal")
        self.assertEqual(list(self.out_dir.glob("*")), [])

    def test_unresolvable_half_refuses_before_any_scope_call(self):
        """A half git cannot resolve refuses as tool_error before any
        reviewed_scope_bytes call and no pair is written."""
        calls = self._no_scope_calls()
        code, out, err = self._run_main(
            self._argv(self.out_dir, range=f"no-such-ref...{self.head_sha}")
        )
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: tool_error"])
        self.assertIn("no-such-ref", err)
        self.assertEqual(calls, [], "no reviewed_scope_bytes call may precede the refusal")
        self.assertEqual(list(self.out_dir.glob("*")), [])

    # -- checkbox 4: helper outcome routing refusals pre-write ------------

    def test_bookkeeping_only_range_refuses_pre_write(self):
        """A range whose delta filters to zero reviewed-scope bytes
        (SCOPE_BOOKKEEPING_ONLY) refuses before any write and no pair is
        written (a digest is never minted from it). Its own fixture repo:
        every commit after base touches only the excluded prefix."""
        repo = corrections_record.build_scratch_repo(self, name="bk-only-repo")
        base = repo.commit_file(
            "src/alpha.py", "def alpha():\n    return 1\n", "seed alpha"
        )
        repo.commit_file(
            "docs/history/backlog/zz-row.md", "bookkeeping row\n", "row one"
        )
        head = repo.commit_file(
            "docs/history/backlog/zz-row-two.md", "more rows\n", "row two"
        )
        outcome, _data = corrections_record.reviewed_scope_bytes(
            repo.root, base, head
        )
        self.assertEqual(
            outcome, corrections_record.SCOPE_BOOKKEEPING_ONLY,
            "fixture precondition: the range must filter to zero bytes",
        )
        out_dir = repo.root / "out"
        code, out, err = self._run_main(self._argv(out_dir, range=f"{base}...{head}"))
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: tool_error"])
        self.assertIn("bookkeeping-only", err)
        self.assertEqual(list(out_dir.glob("*")), [])

    def test_empty_reviewed_scope_refuses(self):
        """An empty reviewed scope (equal base and head, the raw-empty
        SCOPE_BYTES-over-b"" outcome) refuses the same pre-write way."""
        code, out, err = self._run_main(
            self._argv(self.out_dir, range=f"{self.head_sha}...{self.head_sha}")
        )
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: tool_error"])
        self.assertIn("empty reviewed scope", err)
        self.assertEqual(list(self.out_dir.glob("*")), [])

    def test_git_plumbing_failure_over_the_range_refuses(self):
        """The SCOPE_UNRESOLVED outcome (a git plumbing failure inside the
        reviewed-scope byte function) refuses as the named tool_error with
        no pair written."""
        patcher = mock.patch.object(
            producer.corrections_record, "git_bytes", return_value=None
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        code, out, err = self._run_main(self._argv(self.out_dir))
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: tool_error"])
        self.assertIn("cannot derive the reviewed scope", err)
        self.assertEqual(list(self.out_dir.glob("*")), [])

    # -- checkbox 5: flag-surface mutual exclusion -------------------------

    def test_both_plan_and_range_is_a_usage_tool_error(self):
        """Supplying --plan and --range together is the argparse usage
        tool error ending OUTCOME: tool_error."""
        code, out, err = self._run_main(
            [
                "--out-dir", str(self.out_dir),
                "--session", "s",
                "--plan", str(self.workspace / "any-plan.md"),
                "--range", f"{self.base_sha}...{self.head_sha}",
                "--findings-json", str(self.findings_json),
                "--review-run-id", RUN_ID,
                "--review-started-at-ms", str(STARTED_MS),
            ]
        )
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(err), ["OUTCOME: tool_error"])
        self.assertEqual(list(self.out_dir.glob("*")), [])

    def test_neither_plan_nor_range_is_a_usage_tool_error(self):
        """Supplying neither source flag is the argparse usage tool error
        ending OUTCOME: tool_error."""
        code, out, err = self._run_main(
            [
                "--out-dir", str(self.out_dir),
                "--session", "s",
                "--findings-json", str(self.findings_json),
                "--review-run-id", RUN_ID,
                "--review-started-at-ms", str(STARTED_MS),
            ]
        )
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(err), ["OUTCOME: tool_error"])
        self.assertEqual(list(self.out_dir.glob("*")), [])

    # -- checkbox 6: digest correctness over a mixed range -----------------

    def test_digest_differs_from_raw_hash_and_verifier_accepts_it(self):
        """Over the mixed range the emitted digest differs from the raw
        git diff hash (the bookkeeping exclusion is observable) and a
        subprocess verify-digest call with cwd in the scratch repo
        accepts it as fresh."""
        record, _out = self._produce_range()
        payload = json.loads(record.with_suffix(".stats.json").read_text(encoding="utf-8"))
        raw = self.repo.git("diff", f"{self.base_sha}...{self.head_sha}")
        raw_digest = corrections_record.sha256_hex(raw.stdout.encode("utf-8"))
        self.assertNotEqual(
            payload["source_digest"], raw_digest,
            "the emitted digest must hash the filtered scope, not the raw diff",
        )
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "review_record_selection.py"),
                "verify-digest",
                "--record", str(record),
                "--dir", str(self.out_dir),
                "--base", self.base_sha,
                "--expect-head", self.head_sha,
            ],
            cwd=str(self.repo.root),
            capture_output=True,
            text=True,
            env=corrections_record.hermetic_git_env(),
        )
        self.assertEqual(
            proc.returncode, 0,
            f"verify-digest refused the emitted digest: {proc.stderr or proc.stdout}",
        )
        receipt = json.loads(proc.stdout)
        self.assertEqual(receipt["outcome"], "fresh")
        self.assertEqual(receipt["recorded_digest"], payload["source_digest"])

    # -- checkbox 7: range-mode surface pins -------------------------------

    def test_artifact_slug_is_required_in_range_mode(self):
        """The plan-stem default has no input in range mode: omitting the
        explicit --artifact-slug is a named tool_error."""
        argv = self._argv(self.out_dir)
        del argv[argv.index("--artifact-slug") + 1]
        del argv[argv.index("--artifact-slug")]
        code, out, err = self._run_main(argv)
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: tool_error"])
        self.assertIn("--artifact-slug", err)
        self.assertEqual(list(self.out_dir.glob("*")), [])

    def test_type_line_renders_the_code_family_label(self):
        """The - Type: line renders the code-family truth's own label and
        the sidecar review_type matches it (each family renders its own
        fixed label; no free label flag exists)."""
        record, _out = self._produce_range()
        markdown = record.read_text(encoding="utf-8")
        self.assertIn(f"- Type: {self.CODE_FAMILY_LABEL}", markdown)
        payload = json.loads(record.with_suffix(".stats.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["review_type"], self.CODE_FAMILY_LABEL)

    def test_findings_json_plan_cross_check_is_relaxed_in_range_mode(self):
        """Range mode does not cross-check the findings JSON 'plan' key
        against a plan file: a JSON carrying a plan value produces
        normally."""
        findings_path = self.workspace / "with-plan-key.json"
        findings_path.write_text(
            json.dumps({"plan": "docs/history/plans/not-involved.md",
                        "findings": self.findings}),
            encoding="utf-8",
        )
        argv = self._argv(self.out_dir)
        argv[argv.index("--findings-json") + 1] = str(findings_path)
        code, out, err = self._run_main(argv)
        self.assertEqual(code, 0, err + out)
        record = self.out_dir / f"{DATE}-{SLUG}-code-review-r1.md"
        self.assertTrue(record.is_file())
        self.assertNotIn(
            "not-involved", record.read_text(encoding="utf-8"),
            "the relaxed JSON plan value must not leak into the record",
        )

    def test_repo_root_resolves_from_the_out_dir_anchor(self):
        """The suite's cwd is a non-repository workspace, so a successful
        range production whose digest matches the scratch repo's scope
        proves the repo root resolved from the out-dir anchor, never the
        ambient cwd."""
        self.assertFalse(
            (self.workspace / ".git").exists(),
            "fixture precondition: the pinned cwd must not be a repository",
        )
        record, _out = self._produce_range()
        _outcome, scope_bytes = corrections_record.reviewed_scope_bytes(
            self.repo.root, self.base_sha, self.head_sha
        )
        payload = json.loads(record.with_suffix(".stats.json").read_text(encoding="utf-8"))
        self.assertEqual(
            payload["source_digest"],
            corrections_record.sha256_hex(scope_bytes),
        )

    # -- checkbox 8: extensions.certified_range -----------------------------

    def test_certified_range_records_base_and_head(self):
        """The sidecar's extensions.certified_range records the resolved
        40-hex base and head of the emitted range (no schema change: the
        existing optional field's exact shape), and the hard-mode schema
        gate accepts the pair."""
        record, _out = self._produce_range()
        payload = json.loads(record.with_suffix(".stats.json").read_text(encoding="utf-8"))
        certified = payload["extensions"]["certified_range"]
        self.assertEqual(certified, {"base": self.base_sha, "head": self.head_sha})
        code, vout, verr = self._run_validator_hard(record)
        self.assertEqual(code, 0, verr)
        self.assertEqual(self._final_outcomes(vout), ["OUTCOME: pass"])


class FlagSurfaceAndLensSingleHomingTest(unittest.TestCase):
    """Task 2 (producer code-family record arm): the flag surface renders
    only truths the builder emits.

    Pinned: ``--review-type`` removed (any invocation naming it is the
    argparse usage tool error), the narrowed ``--review-mode`` set named
    once as ``producer.SUPPORTED_REVIEW_MODES`` and enforced once in
    ``build_context`` with both surfaces' refusals naming one set, the
    clean-round contradiction staying owned by the two existing guards
    (never duplicated as a mode-vs-clean rule here), the five worker/lens
    associations single-homed in one ordered producer constant whose
    rendered surfaces equal the ``vrs.REQUIRED_PANEL_LENSES`` projection,
    and ``ctx["verdict_field"]`` computing in ``build_context`` so both
    builders are pure readers."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="produce-flag-surface-")
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

    def _write_findings_json(self, findings, name="findings.json", extra=None):
        data = {"findings": findings}
        if extra:
            data.update(extra)
        path = self.root / name
        path.write_text(json.dumps(data), encoding="utf-8")
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
            try:
                code = producer.main(argv)
            except SystemExit as exc:  # argparse usage-error channel
                code = exc.code
        return code, out_buf.getvalue(), err_buf.getvalue()

    def _final_outcomes(self, text):
        return [
            row.strip()
            for row in text.splitlines()
            if row.strip().startswith("OUTCOME:")
        ]

    def _produce_varied(self, out_dir_name="out"):
        findings_json = self._write_findings_json(VARIED_FINDINGS)
        out_dir = self.root / out_dir_name
        code, out, err = self._run_main(self._argv(findings_json, out_dir))
        self.assertEqual(code, 0, err + out)
        record = out_dir / f"{DATE}-plan-review-{SLUG}-r1.md"
        self.assertTrue(record.is_file(), out)
        return record, record.with_suffix(".stats.json")

    def _namespace(self, out_dir, findings_json, **overrides):
        """The argparse namespace build_context reads (the producer's
        parser is not module-exposed). Omits the newer focused-panel
        fields; build_context's getattr fallbacks keep such hand-built
        namespaces mintable as the historical full shape."""
        values = {
            "out_dir": str(out_dir),
            "session": "producer demo session",
            "plan": str(self.plan_path),
            "range": None,
            "findings_json": str(findings_json),
            "review_mode": None,
            "round": None,
            "date": DATE,
            "artifact_slug": SLUG,
            "review_run_id": RUN_ID,
            "review_started_at_ms": STARTED_MS,
            "prior_findings_filter": "no",
            "last_fix_commit": None,
        }
        values.update(overrides)
        return argparse.Namespace(**values)

    @staticmethod
    def _ctx_snapshot(ctx):
        return json.dumps(ctx, sort_keys=True, default=str)

    @staticmethod
    def _payload_text(payload):
        return json.dumps(payload, sort_keys=True)

    # -- checkbox 1: --review-type removed ---------------------------------

    def test_review_type_flag_is_removed_as_a_usage_tool_error(self):
        """Any invocation naming --review-type is the argparse usage tool
        error (exit 3, final OUTCOME: tool_error line) and no pair is
        written."""
        findings_json = self._write_findings_json(
            VARIED_FINDINGS, name="type-flag.json"
        )
        out_dir = self.root / "type-flag"
        code, out, err = self._run_main(
            self._argv(findings_json, out_dir, review_type="Plan Review")
        )
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(err), ["OUTCOME: tool_error"])
        self.assertIn("--review-type", err)
        self.assertEqual(
            list(out_dir.glob("*")), [], "no pair may be written"
        )

    # -- checkbox 2+4: the narrowed mode set on both surfaces --------------

    def test_out_of_set_mode_refusal_names_the_supported_set_on_both_surfaces(self):
        """An out-of-set mode refuses on both surfaces with one named set:
        via the findings JSON with the flag omitted (the build_context
        funnel) and via the flag (the argparse choices derived from the
        same constant)."""
        findings_json = self._write_findings_json(
            VARIED_FINDINGS,
            name="mode.json",
            extra={"review_mode": "bogus-mode"},
        )
        # JSON surface, flag omitted.
        out_dir = self.root / "json-surface"
        code, out, err = self._run_main(self._argv(findings_json, out_dir))
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: tool_error"])
        self.assertIn("review mode 'bogus-mode' must be one of", err)
        # The refusal renders the producer constant itself, so a swap of
        # the funnel's check back to the validator enum (whose message
        # would name a different rendering) cannot pass silently.
        self.assertIn(f"must be one of {producer.SUPPORTED_REVIEW_MODES}", err)
        self.assertEqual(list(out_dir.glob("*")), [])
        # Flag surface: the argparse choices ride the same constant; the
        # exact rendering pin kills a choices-widening mutation
        # deterministically.
        flag_dir = self.root / "flag-surface"
        code, out, err = self._run_main(
            self._argv(findings_json, flag_dir, review_mode="bogus-mode")
        )
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(err), ["OUTCOME: tool_error"])
        self.assertIn("invalid choice", err)
        self.assertIn(
            "(choose from 'fresh-adversarial', 'targeted', 'verification-only')",
            err,
        )
        self.assertEqual(list(flag_dir.glob("*")), [])

    # -- checkbox 3: clean-round contradiction ownership -------------------

    def test_clean_round_contradiction_stays_owned_by_the_existing_guards(self):
        """The clean-round contradiction is never duplicated as a
        producer-side mode-vs-clean rule: the no-last-fix subset
        (verification-only) rides to the validator, whose clean-verdict
        contradiction refuses it post-write with the pair removed; the
        last-fix-carrying subset refuses pre-write through the existing
        freshness gate."""
        empty_json = self._write_findings_json([], name="clean-vo.json")
        out_dir = self.root / "clean-vo"
        code, out, err = self._run_main(
            self._argv(empty_json, out_dir, review_mode="verification-only")
        )
        self.assertEqual(code, 1, "the no-last-fix subset is not a tool error")
        self.assertIn("REFUSED: validator outcome 'fail'", out)
        self.assertIn("clean verdict contradicts", out)
        self.assertTrue(out.rstrip().endswith("OUTCOME: fail"))
        self.assertEqual(list(out_dir.glob("*")), [])
        code, out, err = self._run_main(
            self._argv(
                empty_json,
                self.root / "clean-lf",
                review_mode="targeted",
                last_fix_commit="abc123def",
            )
        )
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: tool_error"])
        self.assertIn("requires --review-mode fresh-adversarial", err)

    # -- checkbox 5: the single-homed worker/lens associations -------------

    def test_rendered_worker_lens_associations_equal_required_panel_projection(self):
        """The discriminating witness: both surfaces' rendered worker/lens
        associations equal the projection of ``vrs.REQUIRED_PANEL_LENSES``
        (workers in canonical insertion order, each worker's lens set
        normalized to sorted order) — the five associations single-home in
        one ordered producer constant. The two-lens correctness-completeness
        Markdown row is additionally pinned byte-exact, so the expected bytes
        are literal rather than computed same-process."""
        record, sidecar = self._produce_varied()
        expected = [
            (worker, sorted(lenses))
            for worker, lenses in vrs.REQUIRED_PANEL_LENSES.items()
        ]
        self.assertEqual(len(expected), 5, "fixture precondition: five workers")
        self.assertEqual(
            producer.PANEL_WORKER_LENSES,
            tuple(
                (worker, tuple(sorted(lenses)))
                for worker, lenses in vrs.REQUIRED_PANEL_LENSES.items()
            ),
        )
        # Seed-independent ordering pin: each lens tuple must be in sorted
        # order (the dropped-sorted() mutation iterates the lens frozenset
        # directly, whose order is process-hash-seed dependent).
        self.assertTrue(
            all(list(t) == sorted(t) for _, t in producer.PANEL_WORKER_LENSES)
        )
        markdown = record.read_text(encoding="utf-8")
        lines = markdown.splitlines()
        header = (
            "| Worker | Lenses | Parent worker | Status | Raw | Solo | Echo "
            "| Relaunch |"
        )
        start = lines.index(header) + 2  # skip the header and separator rows
        md_associations = []
        for line in lines[start:]:
            if not line.startswith("|"):
                break
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            md_associations.append(
                (cells[0], [part.strip() for part in cells[1].split(",")])
            )
        self.assertEqual(md_associations, expected, "Markdown panel rows")
        # Byte-exact rendering pin for the two-lens row (lesson #397's
        # byte-exact arm): the same-process sorted() expectation above is
        # blind whenever the hash seed orders the lens frozenset sorted, so
        # the ordering witness also pins the row's literal bytes.
        self.assertIn(
            "| correctness-completeness | implementation, quality | none |"
            " complete | 4 | 4 | 0 | no |",
            lines,
            "Markdown panel row byte-exact (seed-independent)",
        )
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
        sidecar_associations = [
            (row["worker"], list(row["lenses"])) for row in payload["panel"]
        ]
        self.assertEqual(sidecar_associations, expected, "sidecar panel rows")

    # -- checkbox 6: verdict_field computes in build_context ---------------

    def test_verdict_field_computes_in_build_context_and_builders_are_pure(self):
        """``ctx["verdict_field"]`` is present right after ``build_context``
        (``no`` for findings-bearing rounds, ``yes`` for clean ones), both
        builders are pure readers (called twice: identical output, context
        snapshot unchanged), and ``build_payload`` runs first on a fresh
        context without depending on ``build_markdown``."""
        findings_json = self._write_findings_json(VARIED_FINDINGS, name="pure.json")
        out_dir = self.root / "pure"
        args = self._namespace(out_dir, findings_json)
        ctx = producer.build_context(args, producer.load_findings_input(findings_json))
        self.assertEqual(ctx["verdict_field"], "no")
        snapshot = self._ctx_snapshot(ctx)
        markdown_one = producer.build_markdown(ctx)
        payload_one = self._payload_text(producer.build_payload(ctx))
        self.assertEqual(
            self._ctx_snapshot(ctx),
            snapshot,
            "the builders must not mutate the context",
        )
        self.assertEqual(producer.build_markdown(ctx), markdown_one)
        self.assertEqual(
            self._payload_text(producer.build_payload(ctx)), payload_one
        )
        fresh_ctx = producer.build_context(
            self._namespace(out_dir, findings_json),
            producer.load_findings_input(findings_json),
        )
        self.assertEqual(producer.build_payload(fresh_ctx)["verdict"], "no")
        clean_json = self._write_findings_json([], name="pure-clean.json")
        clean_ctx = producer.build_context(
            self._namespace(out_dir, clean_json),
            producer.load_findings_input(clean_json),
        )
        self.assertEqual(clean_ctx["verdict_field"], "yes")
        self.assertEqual(producer.build_payload(clean_ctx)["verdict"], "yes")


class SeamRewiringTest(unittest.TestCase):
    """Task 2 (producer-code-family-record-arm plan): the producer reads
    the self-heal chain grammar from the validator's public seam.

    Pinned: the source-level drift canary (the producer source defines
    none of the three chain-grammar functions nor the round-tail regex
    constant and reaches none of the validator privates, while the two
    public-seam call sites are present), the delegation pin
    (``build_context`` carries the seam function's return), the ambiguity
    mapping (two dated records for the same chain stem and prior round
    end in the producer refusal carrying the seam exception's exact
    message text), and the non-calendar ``--date`` tool-error regression
    pin."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="produce-seam-rewiring-")
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

    def _namespace(self, out_dir, findings_json, **overrides):
        """The argparse namespace build_context reads (the producer's
        parser is not module-exposed). Omits the newer focused-panel
        fields; build_context's getattr fallbacks keep such hand-built
        namespaces mintable as the historical full shape."""
        values = {
            "out_dir": str(out_dir),
            "session": "producer demo session",
            "plan": str(self.plan_path),
            "range": None,
            "findings_json": str(findings_json),
            "review_mode": None,
            "round": None,
            "date": DATE,
            "artifact_slug": SLUG,
            "review_run_id": RUN_ID,
            "review_started_at_ms": STARTED_MS,
            "prior_findings_filter": "no",
            "last_fix_commit": None,
        }
        values.update(overrides)
        return argparse.Namespace(**values)

    def _run_main(self, argv):
        out_buf, err_buf = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out_buf), contextlib.redirect_stderr(err_buf):
            try:
                code = producer.main(argv)
            except SystemExit as exc:  # argparse usage-error channel
                code = exc.code
        return code, out_buf.getvalue(), err_buf.getvalue()

    def _final_outcomes(self, text):
        return [
            row.strip()
            for row in text.splitlines()
            if row.strip().startswith("OUTCOME:")
        ]

    # -- drift canary (source-level) ---------------------------------------

    def test_drift_canary_producer_carries_no_chain_grammar_and_reads_the_seam(self):
        """Source-level drift canary over the producer's bytes: none of the
        three chain-grammar functions nor the round-tail regex constant is
        defined (``def <name>`` needles; the constant by its plain name),
        none of the four validator-private reaches appears (exact string
        needles), and the two public-seam call sites are required
        present."""
        source = (SCRIPTS_DIR / "produce_exec_review_record.py").read_text(
            encoding="utf-8"
        )
        for needle in (
            # Grammar re-encoding needles (def <name> forms; the constant
            # by its plain name, which no call site may mention either).
            "def _well_formed_self_heal_state",
            "def _valid_prior_chain_state",
            "def self_heal_chain_state",
            "_ROUND_TAIL_RE",
            # Validator-private reaches (exact string needles).
            "vrs._date_fence",
            "vrs._calendar_valid_record_date",
            "vrs.ValidationResult",
            "vrs.validate_usage_mint_gate",
        ):
            self.assertNotIn(
                needle, source,
                f"forbidden needle present in producer source: {needle!r}",
            )
        for needle in ("vrs.self_heal_chain_state(", "vrs.calendar_valid_record_date("):
            self.assertIn(
                needle, source,
                f"required seam call site absent from producer source: {needle!r}",
            )

    # -- delegation pin -----------------------------------------------------

    def test_delegation_pin_build_context_carries_the_seam_return(self):
        """Monkeypatching ``self_heal_chain_state`` on the validator module
        the producer imported makes ``build_context`` carry that function's
        return verbatim and call it with the record path and run id (a
        producer-local re-encoding would ignore the patch and fail this
        pin; ``producer.vrs`` is the patch target because this suite's
        path-loader yields distinct module instances for the same file)."""
        findings_json = self._write_findings_json(
            VARIED_FINDINGS, name="delegate.json"
        )
        out_dir = self.root / "delegate"
        sentinel = {"status": "unused", "run_id": RUN_ID, "delegation": "sentinel"}
        calls = []

        def fake_chain_state(record_path, run_id):
            calls.append((record_path, run_id))
            return sentinel

        with mock.patch.object(
            producer.vrs, "self_heal_chain_state", fake_chain_state
        ):
            ctx = producer.build_context(
                self._namespace(out_dir, findings_json),
                producer.load_findings_input(findings_json),
            )
        self.assertIs(ctx["self_heal_state"], sentinel)
        self.assertEqual(
            calls,
            [(out_dir / f"{DATE}-plan-review-{SLUG}-r1.md", RUN_ID)],
        )

    # -- ambiguity mapping ---------------------------------------------------

    def test_ambiguous_predecessor_maps_seam_raise_to_producer_refusal(self):
        """Two dated records resolving to the same chain stem and prior
        round: the round-2 production refuses (exit 1, OUTCOME: fail)
        before anything is written, and the refusal text is byte-identical
        to the message the seam's ``AmbiguousChainPredecessor`` raises for
        the same directory (the mapping arm of the ambiguity checkbox)."""
        findings_json = self._write_findings_json(
            VARIED_FINDINGS, name="ambiguous.json"
        )
        out_dir = self.root / "ambiguous"
        code, out, err = self._run_main(self._argv(findings_json, out_dir))
        self.assertEqual(code, 0, err + out)
        r1 = out_dir / f"{DATE}-plan-review-{SLUG}-r1.md"
        self.assertTrue(r1.is_file())
        # A second dated record for the same chain stem and round r1: the
        # unnumbered twin of the r1 record (content irrelevant; the
        # ambiguity fires before any prior validation). The producer
        # always emits -rN names, so the duplicate candidate is written
        # directly.
        unnumbered = out_dir / f"{DATE}-plan-review-{SLUG}.md"
        unnumbered.write_bytes(r1.read_bytes())
        r2 = out_dir / f"{DATE}-plan-review-{SLUG}-r2.md"
        code, out, err = self._run_main(self._argv(findings_json, out_dir, round=2))
        self.assertEqual(code, 1)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: fail"])
        self.assertFalse(r2.exists(), "a refused production writes no record")
        self.assertFalse(
            r2.with_suffix(".stats.json").exists(),
            "a refused production writes no sidecar",
        )
        with self.assertRaises(vrs.AmbiguousChainPredecessor) as caught:
            vrs.self_heal_chain_state(r2, RUN_ID)
        self.assertIn(
            f"REFUSED: {caught.exception}", out,
            "the producer refusal must carry the seam exception's message verbatim",
        )
        self.assertIn(
            "ambiguous prior-round records for chain "
            f"'plan-review-{SLUG}' round r1: [", out,
        )
        self.assertIn("disambiguate the directory first", out)

    # -- date pre-flight regression pin ---------------------------------------

    def test_non_calendar_date_refuses_as_the_same_tool_error(self):
        """A non-calendar ``--date`` (a shape-valid string that is not a
        real calendar day) keeps the exit-3 ``ProducerToolError`` refusal
        with its exact message text, through the public
        ``vrs.calendar_valid_record_date`` pre-flight; no pair is
        written."""
        findings_json = self._write_findings_json(VARIED_FINDINGS, name="date.json")
        out_dir = self.root / "non-calendar"
        code, out, err = self._run_main(
            self._argv(findings_json, out_dir, date="2026-02-30")
        )
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: tool_error"])
        self.assertIn(
            "date '2026-02-30' must be a calendar-valid YYYY-MM-DD date", err
        )
        self.assertEqual(list(out_dir.glob("*")), [])


class OverflowInputAndExecCompletionArmTest(unittest.TestCase):
    """Exec-review record producer gaps (EXEC-PROMPTS entry
    exec-review-record-producer-gaps): the ``overflow`` array in the
    findings JSON renders both surfaces at mint time (no post-production
    hand patch), the canonical overflow placement shapes refuse at the
    input boundary, and the ``--kind exec-completion`` arm mints the
    ``*-plan-review-<slug>-exec-r<N>`` completion receipt pair with
    ``extensions.certified_range`` resolved from ``--certified-range``.
    The clean verification-only round keeps its documented mapping at the
    freshness gate's error text; the contradiction guard itself is never
    duplicated (the existing pin above holds)."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="produce-overflow-arm-")
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
        self.findings = [
            {
                "id": 1,
                "title": "Medium finding",
                "severity": "Medium",
                "blocking": False,
                "note": "The medium consequence.",
                "workers": ["correctness-completeness"],
            },
            {
                "id": 2,
                "title": "Low finding",
                "severity": "Low",
                "blocking": False,
                "note": "The low consequence.",
                "workers": ["contract-docs"],
            },
        ]

    def _write_findings_json(self, payload, name="findings.json"):
        path = self.root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _argv(self, findings_json, out_dir, **overrides):
        argv = [
            "--out-dir", str(out_dir),
            "--session", "overflow arm session",
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
            try:
                code = producer.main(argv)
            except SystemExit as exc:  # argparse usage-error channel
                code = exc.code
        return code, out_buf.getvalue(), err_buf.getvalue()

    def _final_outcomes(self, text):
        return [
            row.strip()
            for row in text.splitlines()
            if row.strip().startswith("OUTCOME:")
        ]

    # -- overflow input arm ------------------------------------------------

    def test_overflow_array_renders_both_surfaces_at_mint_time(self):
        """An ``overflow`` array in the findings JSON renders the Markdown
        overflow manifest bullets and the sidecar ``overflow`` list and
        ``counts.overflow`` in one minted pair the validator accepts in
        hard mode; no post-production hand edit exists."""
        payload = {
            "plan": str(self.plan_path),
            "findings": self.findings,
            "overflow": [
                {
                    "title": "Credible overflow candidate",
                    "note": "The candidate beyond the per-worker Low budget.",
                    "severity": "Low",
                    "workers": ["risk"],
                }
            ],
        }
        findings_json = self._write_findings_json(payload)
        out_dir = self.root / "overflow-pair"
        code, out, err = self._run_main(self._argv(findings_json, out_dir))
        self.assertEqual(code, 0, err + out)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: pass"])
        record = out_dir / f"{DATE}-plan-review-{SLUG}-r1.md"
        markdown = record.read_text(encoding="utf-8")
        self.assertIn("### Overflow manifest", markdown)
        self.assertIn("**Credible overflow candidate** (Low, non-blocking)", markdown)
        self.assertIn("The candidate beyond the per-worker Low budget.", markdown)
        self.assertIn("- Overflow: 1", markdown)

    def test_overflow_row_location_renders_in_the_manifest(self):
        """An overflow row's ``file``/``line`` anchor renders as the
        manifest bullet's location (the ride-along convention findings
        rows follow), so an anchored overflow candidate's location
        survives mint time."""
        payload = {
            "findings": self.findings,
            "overflow": [
                {
                    "title": "Anchored overflow candidate",
                    "note": "The candidate with a location anchor.",
                    "file": "scripts/demo.py",
                    "line": 7,
                }
            ],
        }
        findings_json = self._write_findings_json(payload, name="anchored-ov.json")
        out_dir = self.root / "anchored-ov"
        code, out, err = self._run_main(self._argv(findings_json, out_dir))
        self.assertEqual(code, 0, err + out)
        record = out_dir / f"{DATE}-plan-review-{SLUG}-r1.md"
        markdown = record.read_text(encoding="utf-8")
        self.assertIn("**Anchored overflow candidate** (Low, non-blocking)", markdown)
        self.assertIn("location: `scripts/demo.py:7`", markdown)

    def test_critical_overflow_row_refuses_at_the_input_boundary(self):
        """A Critical overflow row refuses pre-write as the tool error
        naming the validator's canonical overflow placement gate; no pair
        is written."""
        payload = {
            "findings": self.findings,
            "overflow": [{"title": "T", "note": "N", "severity": "Critical"}],
        }
        findings_json = self._write_findings_json(payload, name="critical-ov.json")
        out_dir = self.root / "critical-ov"
        code, out, err = self._run_main(self._argv(findings_json, out_dir))
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: tool_error"])
        self.assertIn("Critical findings in", err)
        self.assertEqual(list(out_dir.glob("*")), [])

    def test_blocking_overflow_row_refuses_at_the_input_boundary(self):
        """A blocking overflow row refuses pre-write as the tool error
        naming the validator's canonical overflow placement gate; no pair
        is written."""
        payload = {
            "findings": self.findings,
            "overflow": [
                {"title": "T", "note": "N", "severity": "Low", "blocking": True}
            ],
        }
        findings_json = self._write_findings_json(payload, name="blocking-ov.json")
        out_dir = self.root / "blocking-ov"
        code, out, err = self._run_main(self._argv(findings_json, out_dir))
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: tool_error"])
        self.assertIn("blocking findings in", err)
        self.assertEqual(list(out_dir.glob("*")), [])

    def test_overflow_without_findings_mints_a_clean_certifying_pair(self):
        """Two non-blocking residuals in overflow with no staged findings
        mint verdict yes and pass the validator in hard mode, with no hand
        patch (the certification round's terminal record shape)."""
        payload = {
            "findings": [],
            "overflow": [
                {"title": "T1", "note": "N1"},
                {"title": "T2", "note": "N2"},
            ],
        }
        findings_json = self._write_findings_json(payload, name="clean-ov.json")
        out_dir = self.root / "clean-ov"
        code, out, err = self._run_main(self._argv(findings_json, out_dir))
        self.assertEqual(code, 0, err + out)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: pass"])
        sidecar = next(out_dir.glob("*.stats.json"))
        data = json.loads(sidecar.read_text(encoding="utf-8"))
        self.assertEqual(len(data["overflow"]), 2)
        self.assertEqual(data["verdict"], "yes")
        self.assertIn("### Overflow manifest", next(out_dir.glob("*.md")).read_text(encoding="utf-8"))

    def test_malformed_overflow_row_refuses_with_the_row_index(self):
        """An overflow row missing its required ``note`` refuses as the
        tool error naming the row index; no pair is written."""
        payload = {
            "findings": self.findings,
            "overflow": [{"title": "Only a title"}],
        }
        findings_json = self._write_findings_json(payload, name="malformed-ov.json")
        out_dir = self.root / "malformed-ov"
        code, out, err = self._run_main(self._argv(findings_json, out_dir))
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: tool_error"])
        self.assertIn("overflow row at index 0", err)
        self.assertEqual(list(out_dir.glob("*")), [])

    def test_freshness_gate_error_text_carries_the_round_shape_mapping(self):
        """The clean verification-only mapping lives at the helper's error
        text: the freshness gate's refusal names the fresh-adversarial
        with --last-fix-commit spelling and the validator's post-write
        refusal sentence; the producer adds no new mode-vs-clean
        guard."""
        findings_json = self._write_findings_json(
            {"findings": []}, name="mapping.json"
        )
        code, out, err = self._run_main(
            self._argv(
                findings_json,
                self.root / "mapping",
                review_mode="targeted",
                last_fix_commit="abc123def",
            )
        )
        self.assertEqual(code, 3)
        self.assertIn("Round-shape mapping:", err)
        self.assertIn("--last-fix-commit <sha>", err)
        self.assertIn("the validator refuses it post-write", err)


class ExecCompletionArmTest(unittest.TestCase):
    """The ``--kind exec-completion`` completion receipt mint: the
    ``*-plan-review-<slug>-exec-r<N>`` series filename the reverse-squash
    guard and done sweep gate grammars pin, with
    ``extensions.certified_range`` populated from ``--certified-range``.
    Every fixture is a hermetic scratch git repo (the
    corrections_record.build_scratch_repo pattern) so the certified range
    resolves without ambient state."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="produce-exec-completion-")
        self.addCleanup(tmp.cleanup)
        self.workspace = Path(tmp.name)
        self._original_cwd = os.getcwd()
        os.chdir(self.workspace)
        self.addCleanup(os.chdir, self._original_cwd)
        self.metrics_home = self.workspace / "metrics"
        if vrs.invocation_telemetry is not None:
            patcher = mock.patch.object(
                vrs.invocation_telemetry,
                "resolve_metrics_home",
                lambda: self.metrics_home,
            )
            patcher.start()
            self.addCleanup(patcher.stop)
        self.repo, self.base_sha, self.head_sha = self._build_range_repo()
        self.plan_path = self.workspace / "sample-plan.md"
        self.plan_path.write_text(PLAN_BODY, encoding="utf-8")
        self.findings_json = self.workspace / "findings.json"
        self.findings_json.write_text(
            json.dumps(
                {
                    "findings": [
                        {
                            "id": 1,
                            "title": "Exec completion finding",
                            "severity": "Low",
                            "blocking": False,
                            "note": "The residual the completion certifies.",
                            "workers": ["correctness-completeness"],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        self.out_dir = self.repo.root / "out"

    def _build_range_repo(self):
        repo = corrections_record.build_scratch_repo(self, name="exec-completion-repo")
        base = repo.commit_file("src/alpha.py", "def alpha():\n    return 1\n", "seed alpha")
        head = repo.commit_file("src/beta.py", "def beta():\n    return 2\n", "feature beta")
        return repo, base, head

    def _argv(self, out_dir, **overrides):
        argv = [
            "--out-dir", str(out_dir),
            "--session", "exec completion session",
            "--plan", str(self.plan_path),
            "--findings-json", str(self.findings_json),
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
            try:
                code = producer.main(argv)
            except SystemExit as exc:  # argparse usage-error channel
                code = exc.code
        return code, out_buf.getvalue(), err_buf.getvalue()

    def _final_outcomes(self, text):
        return [
            row.strip()
            for row in text.splitlines()
            if row.strip().startswith("OUTCOME:")
        ]

    def test_exec_completion_mints_the_series_filename_pair(self):
        """``--kind exec-completion --certified-range`` writes the
        ``{date}-plan-review-{slug}-exec-r<N>.md`` pair the series
        grammars pin, with sidecar ``extensions.certified_range``
        recording the resolved base and head, and the validator accepts
        the pair in hard mode."""
        argv = self._argv(
            self.out_dir,
            kind="exec-completion",
            certified_range=f"{self.base_sha}...{self.head_sha}",
        )
        code, out, err = self._run_main(argv)
        self.assertEqual(code, 0, err + out)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: pass"])
        record = self.out_dir / f"{DATE}-plan-review-{SLUG}-exec-r1.md"
        self.assertTrue(record.is_file(), out)
        side = json.loads(
            record.with_suffix(".stats.json").read_text(encoding="utf-8")
        )
        self.assertEqual(side["extensions"]["certified_range"]["base"], self.base_sha)
        self.assertEqual(side["extensions"]["certified_range"]["head"], self.head_sha)
        self.assertEqual(side["artifact_slug"], f"{SLUG}-exec")

    def test_exec_completion_requires_the_certified_range(self):
        """``--kind exec-completion`` without ``--certified-range``
        refuses as the tool error naming the required input; no pair is
        written."""
        out_dir = self.repo.root / "out-no-range"
        code, out, err = self._run_main(
            self._argv(out_dir, kind="exec-completion")
        )
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: tool_error"])
        self.assertIn("--kind exec-completion requires --certified-range", err)
        self.assertEqual(list(out_dir.glob("*")), [])

    def test_exec_completion_slug_already_carrying_the_token_refuses(self):
        """A slug already ending in ``-exec`` refuses under
        ``--kind exec-completion`` (the series token appends once, never
        twice)."""
        out_dir = self.repo.root / "out-double"
        code, out, err = self._run_main(
            self._argv(
                out_dir,
                kind="exec-completion",
                certified_range=f"{self.base_sha}...{self.head_sha}",
                artifact_slug=f"{SLUG}-exec",
            )
        )
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: tool_error"])
        self.assertIn("already carries the -exec", err)
        self.assertEqual(list(out_dir.glob("*")), [])

    def test_certified_range_with_range_is_a_usage_tool_error(self):
        """``--certified-range`` and ``--range`` are mutually exclusive:
        the certified range annotates a plan-family record, never a
        code-family record that already certifies its own range. The
        invocation omits ``--plan`` so the producer's own exclusion guard
        in ``build_context`` is the enforcement point under test (the
        argparse ``--plan``/``--range`` group must not fire first)."""
        out_dir = self.repo.root / "out-both"
        argv = [
            "--out-dir", str(out_dir),
            "--session", "exec completion session",
            f"--range={self.base_sha}...{self.head_sha}",
            "--findings-json", str(self.findings_json),
            "--review-run-id", RUN_ID,
            "--review-started-at-ms", str(STARTED_MS),
            "--date", DATE,
            "--artifact-slug", SLUG,
            "--certified-range", f"{self.base_sha}...{self.head_sha}",
        ]
        code, out, err = self._run_main(argv)
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: tool_error"])
        self.assertIn("--certified-range and --range are mutually exclusive", err)
        self.assertEqual(list(out_dir.glob("*")), [])

    def test_certified_range_under_the_default_kind_refuses(self):
        """``--certified-range`` with the default ``--kind plan-review``
        refuses: the certified range is the completion receipt's
        annotation, never a free-standing option on the default arm."""
        out_dir = self.repo.root / "out-default-kind"
        code, out, err = self._run_main(
            self._argv(
                out_dir,
                certified_range=f"{self.base_sha}...{self.head_sha}",
            )
        )
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: tool_error"])
        self.assertIn("--certified-range requires --kind exec-completion", err)
        self.assertEqual(list(out_dir.glob("*")), [])

    def test_certified_range_unresolvable_half_refuses(self):
        """An unresolvable ``--certified-range`` half refuses through the
        shared range source rules; no pair is written."""
        out_dir = self.repo.root / "out-badref"
        code, out, err = self._run_main(
            self._argv(
                out_dir,
                kind="exec-completion",
                certified_range=f"{self.base_sha}...does-not-exist",
            )
        )
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: tool_error"])
        self.assertIn("does not resolve to a commit", err)
        self.assertEqual(list(out_dir.glob("*")), [])


class EgressDigestMintTest(ExecCompletionArmTest):
    """The mint-time archive-egress digest arms (the
    producer-egress-digest-mint gap): ``--egress-digest``/``--egress-path``
    place the archived bytes' sha256 into the minted completion receipt on
    both surfaces at mint, and the minted pair satisfies the reverse-squash
    guard's ``find_evidence_record`` evidence leg unchanged (no hand
    ``cat >>`` backfill after the completion pass)."""

    def _mint_completion(self, out_dir, **overrides):
        return self._run_main(
            self._argv(
                out_dir,
                kind="exec-completion",
                certified_range=f"{self.base_sha}...{self.head_sha}",
                **overrides,
            )
        )

    def test_egress_digest_renders_on_both_surfaces(self):
        """``--egress-digest`` places the hex into the Metadata line and
        the sidecar's free-form ``extensions.archive_egress_digest``; the
        run's final ``OUTCOME: pass`` carries the validator hard-mode
        acceptance (the producer validates before reporting pass)."""
        out_dir = self.repo.root / "out-egress-digest"
        digest = "a" * 64
        code, out, err = self._mint_completion(
            out_dir, egress_digest=digest
        )
        self.assertEqual(code, 0, err + out)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: pass"])
        record = out_dir / f"{DATE}-plan-review-{SLUG}-exec-r1.md"
        self.assertTrue(record.is_file(), out)
        self.assertIn(f"- Archive-egress digest: {digest}", record.read_text())
        side = json.loads(
            record.with_suffix(".stats.json").read_text(encoding="utf-8")
        )
        self.assertEqual(side["extensions"]["archive_egress_digest"], digest)

    def test_egress_path_digests_the_archived_bytes_at_mint(self):
        """``--egress-path`` digests the named file's bytes at mint time
        and renders the same sha256 on both surfaces."""
        out_dir = self.repo.root / "out-egress-path"
        archived = self.workspace / "archived-plan.md"
        archived_bytes = b"# archived plan bytes\n\nthe egress body\n"
        archived.write_bytes(archived_bytes)
        expected = hashlib.sha256(archived_bytes).hexdigest()
        code, out, err = self._mint_completion(
            out_dir, egress_path=str(archived)
        )
        self.assertEqual(code, 0, err + out)
        record = out_dir / f"{DATE}-plan-review-{SLUG}-exec-r1.md"
        self.assertIn(
            f"- Archive-egress digest: {expected}", record.read_text()
        )
        side = json.loads(
            record.with_suffix(".stats.json").read_text(encoding="utf-8")
        )
        self.assertEqual(side["extensions"]["archive_egress_digest"], expected)

    def test_minted_pair_satisfies_find_evidence_record(self):
        """The scope pin: a receipt minted under a reviews home satisfies
        ``find_evidence_record`` unchanged - the anchored slug-and-digest
        leg finds the record without any post-mint edit."""
        out_dir = self.repo.root / ".ai-playbook" / "reviews"
        digest = "b" * 64
        code, out, err = self._mint_completion(
            out_dir, egress_digest=digest
        )
        self.assertEqual(code, 0, err + out)
        found = guard.find_evidence_record(self.repo.root, SLUG, digest)
        self.assertIsNotNone(found)
        self.assertTrue(found.endswith(f"{DATE}-plan-review-{SLUG}-exec-r1.md"))

    def test_malformed_egress_digest_refuses_as_tool_error(self):
        """A digest that is not 64 lowercase hex hex characters refuses at
        the input boundary; no pair is written."""
        out_dir = self.repo.root / "out-bad-digest"
        code, out, err = self._mint_completion(
            out_dir, egress_digest="XYZ" * 21
        )
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: tool_error"])
        self.assertIn("must be a 64-character lowercase hex", err)
        self.assertEqual(list(out_dir.glob("*")), [])

    def test_missing_egress_path_refuses_as_tool_error(self):
        """A nonexistent ``--egress-path`` refuses at the input boundary
        (the producer digests existing bytes once, never re-reads); no
        pair is written."""
        out_dir = self.repo.root / "out-missing-path"
        code, out, err = self._mint_completion(
            out_dir, egress_path=str(self.workspace / "no-such-file.md")
        )
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: tool_error"])
        self.assertIn("egress path not found", err)
        self.assertEqual(list(out_dir.glob("*")), [])

    def test_egress_flags_with_range_are_a_plan_family_refusal(self):
        """The egress flags are plan-family options: a range-mode record
        (the code family) refuses them as a tool error instead of minting
        an annotation no evidence leg reads."""
        out_dir = self.repo.root / "out-range-egress"
        argv = [
            "--out-dir", str(out_dir),
            "--session", "code family session",
            f"--range={self.base_sha}...{self.head_sha}",
            "--findings-json", str(self.findings_json),
            "--review-run-id", RUN_ID,
            "--review-started-at-ms", str(STARTED_MS),
            "--date", DATE,
            "--artifact-slug", SLUG,
            "--egress-digest", "c" * 64,
        ]
        code, out, err = self._run_main(argv)
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: tool_error"])
        self.assertIn("are plan-family options", err)
        self.assertEqual(list(out_dir.glob("*")), [])

    def test_both_egress_flags_are_a_usage_error(self):
        """``--egress-digest`` and ``--egress-path`` are mutually
        exclusive at the argparse layer (one digest source, never two);
        the OutcomeArgumentParser usage idiom ends exit 3 with a final
        ``OUTCOME: tool_error`` line."""
        out_dir = self.repo.root / "out-both-egress"
        code, out, err = self._mint_completion(
            out_dir,
            egress_digest="d" * 64,
            egress_path=str(self.plan_path),
        )
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(err + out), ["OUTCOME: tool_error"])
        self.assertIn("not allowed with argument", err + out)
        self.assertEqual(list(out_dir.glob("*")), [])

    def test_egress_flags_on_the_default_kind_refuse(self):
        """The egress flags on the plain ``--kind plan-review`` arm refuse
        as a tool error (the r1 panel's converged Low): a round record's
        filename never matches the guard's anchored ``-exec-r<N>``
        grammar, so the digest would be dead evidence there."""
        out_dir = self.repo.root / "out-round-egress"
        code, out, err = self._run_main(
            self._argv(out_dir, egress_digest="e" * 64)
        )
        self.assertEqual(code, 3)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: tool_error"])
        self.assertIn("require --kind exec-completion", err)
        self.assertEqual(list(out_dir.glob("*")), [])


class MintTimeExecRecordWarningTest(unittest.TestCase):
    """The mint-time exec-record warning arm (producer-exec-record-grammar
    plan, Tasks 1-2): a range-mode (code-family) mint whose
    ``--artifact-slug`` equals an executed or active plan's canonical slug
    prints one stderr warning naming the archive-ceremony gate, the repair
    producer, and the exec-series grammar. Warning-only: the exit code, the
    stdout outcome grammar, and the produced pair's bytes are unaffected;
    the slug-match probe is fail-open. Plan-family mints stay warning-free
    on a matching slug (the slug-conditioned-probe regression catcher).

    Fixtures are hermetic scratch git repos (the corrections_record
    build_scratch_repo pattern) carrying fixture plans under the plans
    roots; the process cwd is pinned to a non-repository workspace so the
    probe and the range resolution anchor only on the out-dir."""

    GATE_TOKEN = "scripts/done_sweep_gates_lib.py"
    REPAIR_TOKEN = "scripts/produce_exec_review_record.py"
    SERIES_TOKEN = "-exec-r"
    COMPLETED_SLUG = "fixture-completed-plan"
    LIVING_SLUG = "fixture-living-plan"

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="produce-warning-arm-")
        self.addCleanup(tmp.cleanup)
        self.workspace = Path(tmp.name)
        self._original_cwd = os.getcwd()
        os.chdir(self.workspace)
        self.addCleanup(os.chdir, self._original_cwd)
        self._original_git_env = {
            key: value
            for key, value in os.environ.items()
            if key.startswith("GIT_")
        }
        for key in self._original_git_env:
            del os.environ[key]
        self.addCleanup(self._restore_git_env)
        self.metrics_home = self.workspace / "metrics"
        if vrs.invocation_telemetry is not None:
            patcher = mock.patch.object(
                vrs.invocation_telemetry,
                "resolve_metrics_home",
                lambda: self.metrics_home,
            )
            patcher.start()
            self.addCleanup(patcher.stop)
        self.findings_json = self.workspace / "warning-findings.json"
        self.findings_json.write_text(
            json.dumps({"findings": [
                {
                    "id": 1,
                    "title": "Warning arm finding",
                    "severity": "Low",
                    "blocking": False,
                    "note": "The mint-time warning arm finding fixture.",
                }
            ]}),
            encoding="utf-8",
        )

    def _restore_git_env(self):
        for key, value in self._original_git_env.items():
            os.environ[key] = value

    def _repo(self, name):
        """Scratch repo seeded with the reviewed range delta."""
        repo = corrections_record.build_scratch_repo(self, name=name)
        self.base_sha = repo.commit_file(
            "src/alpha.py", "def alpha():\n    return 1\n", "seed alpha")
        self.head_sha = repo.commit_file(
            "src/beta.py", "def beta():\n    return 2\n", "feature beta")
        return repo

    def _seed_plans(self, repo):
        """Fixture plans under both plans roots, untracked (the probe reads
        the filesystem, never git)."""
        repo.write_file(
            "docs/history/plans/completed/2026-01-01-%s.md" % self.COMPLETED_SLUG,
            "# Archived fixture plan\n\nArchived plan body.\n",
        )
        repo.write_file(
            "docs/history/plans/2026-01-01-%s.md" % self.LIVING_SLUG,
            "# Living fixture plan\n\nLiving plan body.\n",
        )

    def _argv(self, out_dir, slug, plan=None):
        argv = [
            "--out-dir", str(out_dir),
            "--session", "warning arm session",
            "--findings-json", str(self.findings_json),
            "--review-run-id", RUN_ID,
            "--review-started-at-ms", str(STARTED_MS),
            "--date", DATE,
        ]
        if plan is not None:
            argv.extend(["--plan", str(plan)])
        else:
            argv.append("--range=%s...%s" % (self.base_sha, self.head_sha))
        argv.extend(["--artifact-slug", slug])
        return argv

    def _run_main(self, argv):
        out_buf, err_buf = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out_buf), contextlib.redirect_stderr(err_buf):
            try:
                code = producer.main(argv)
            except SystemExit as exc:
                code = exc.code
        return code, out_buf.getvalue(), err_buf.getvalue()

    def _final_outcomes(self, text):
        return [
            row.strip()
            for row in text.splitlines()
            if row.strip().startswith("OUTCOME:")
        ]

    def _assert_no_warning(self, out, err):
        self.assertNotIn(self.GATE_TOKEN, err)
        self.assertNotIn(self.GATE_TOKEN, out)

    def _mint(self, repo, out_name, slug, plan=None):
        out_dir = repo.root / out_name
        code, out, err = self._run_main(self._argv(out_dir, slug, plan=plan))
        self.assertEqual(code, 0, err + out)
        return out_dir, out, err

    # -- the matching classes ---------------------------------------------

    def test_completed_root_slug_match_warns(self):
        """A range-mode mint whose artifact slug equals an archived
        fixture plan's canonical slug under the completed root prints the
        stderr warning naming the gate file, the repair producer, and the
        exec-series token."""
        repo = self._repo("warn-completed")
        self._seed_plans(repo)
        out_dir, out, err = self._mint(repo, "out", self.COMPLETED_SLUG)
        self.assertIn(self.GATE_TOKEN, err)
        self.assertIn(self.REPAIR_TOKEN, err)
        self.assertIn(self.SERIES_TOKEN, err)
        self.assertTrue(
            (out_dir / ("%s-%s-code-review-r1.md" % (DATE, self.COMPLETED_SLUG))).is_file()
        )

    def test_living_root_slug_match_warns(self):
        """The active-plan firing window: a matching slug under the living
        plans root warns the same way (a Phase 3 mint names a plan still
        living at mint time)."""
        repo = self._repo("warn-living")
        self._seed_plans(repo)
        out_dir, out, err = self._mint(repo, "out", self.LIVING_SLUG)
        self.assertIn(self.GATE_TOKEN, err)
        self.assertIn(self.REPAIR_TOKEN, err)
        self.assertIn(self.SERIES_TOKEN, err)
        self.assertTrue(
            (out_dir / ("%s-%s-code-review-r1.md" % (DATE, self.LIVING_SLUG))).is_file()
        )

    # -- the non-matching and probe-failure classes ------------------------

    def test_non_matching_slug_prints_no_warning(self):
        """A range-mode mint whose artifact slug matches no plan under the
        plans roots prints no warning line on either channel."""
        repo = self._repo("warn-none")
        self._seed_plans(repo)
        _out_dir, out, err = self._mint(repo, "out", SLUG)
        self._assert_no_warning(out, err)

    def test_plan_family_mint_with_matching_slug_prints_no_warning(self):
        """The slug-conditioned-probe regression catcher: a plan-family
        mint whose --artifact-slug deliberately names a plan slug under
        the plans roots prints no warning on either channel."""
        repo = self._repo("warn-plan-family")
        self._seed_plans(repo)
        plan = repo.root / ("docs/history/plans/2026-01-01-%s.md" % self.LIVING_SLUG)
        _out_dir, out, err = self._mint(
            repo, "out", self.LIVING_SLUG, plan=plan)
        self._assert_no_warning(out, err)

    def test_unresolvable_probe_fails_open(self):
        """A slug-match probe that cannot resolve (no plans roots
        reachable in the minting repository) fails open: the mint
        succeeds with no warning and an unchanged final OUTCOME line."""
        repo = self._repo("warn-fail-open")
        out_dir, out, err = self._mint(repo, "out", self.COMPLETED_SLUG)
        self._assert_no_warning(out, err)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: pass"])

    # -- the warning-only posture -----------------------------------------

    def test_warning_leaves_outcome_and_pair_bytes_unaffected(self):
        """The pinned warning scenario: exit code 0, the final OUTCOME:
        pass line unchanged, and the produced record and sidecar bytes
        byte-identical to an identical mint under the same inputs with no
        matching plan present (the warning rides stderr only)."""
        repo = self._repo("warn-bytes")
        self._seed_plans(repo)
        warned_dir, out, err = self._mint(repo, "out-warned", self.COMPLETED_SLUG)
        self.assertEqual(self._final_outcomes(out), ["OUTCOME: pass"])
        self.assertIn(self.GATE_TOKEN, err)
        # Remove the fixture plans (untracked) so the same mint no longer
        # matches; same repo, same range shas, same inputs.
        import shutil
        shutil.rmtree(repo.root / "docs/history/plans")
        clean_dir, clean_out, clean_err = self._mint(
            repo, "out-clean", self.COMPLETED_SLUG)
        self._assert_no_warning(clean_out, clean_err)
        for name in (
            "%s-%s-code-review-r1.md" % (DATE, self.COMPLETED_SLUG),
            "%s-%s-code-review-r1.stats.json" % (DATE, self.COMPLETED_SLUG),
        ):
            warned = (warned_dir / name).read_bytes()
            clean = (clean_dir / name).read_bytes()
            self.assertEqual(warned, clean)


if __name__ == "__main__":
    unittest.main()
