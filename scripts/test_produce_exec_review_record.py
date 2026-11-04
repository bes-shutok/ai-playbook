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

Run from the repository root:

    PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_produce_exec_review_record.py'
"""

import argparse
import contextlib
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
        """The argparse namespace build_context reads, mirroring the CLI's
        parsed flags (the producer's parser is not module-exposed)."""
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


if __name__ == "__main__":
    unittest.main()
