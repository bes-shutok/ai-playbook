#!/usr/bin/env python3
"""Step 3.1 record-validation gate arms over the existing staging validator.

Pins the execute-plan Step 3.1 verification gate item that runs
``python3 scripts/validate_review_staging.py --hard <record>`` before
Step 3.2 and continues only when the command succeeds AND its final
outcome line is ``OUTCOME: pass``:

- a malformed record+sidecar pair reports ``OUTCOME: fail`` at exit 0 in
  soft mode (the trap: exit code zero alone cannot gate) and fails the
  hard-mode gate with exit 1, so the conjunction is false on both legs
  and Phase 3 stops before Step 3.2;
- a valid findings-bearing record and a valid clear record both pass the
  same hard-mode invocation with ``OUTCOME: pass`` under the existing
  grammar, with no new schema rule;
- validator telemetry stays isolated under the test's temporary metrics
  home (no repository metrics writes from test runs).

The fixtures reuse the validator's own current-format builders
(``_current_finding``, ``_current_findings_markdown``) plus its
post-window freshness payload, so the shapes track the validator's own
grammar instead of hand-built Markdown.

Run from the repository root:

    PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_step31_record_validation_gate.py'
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


vrs = _load_from_path("validate_review_staging")
invocation_telemetry = _load_from_path("invocation_telemetry")

# The freshness Metadata lines a post-window record carries (the same
# lines the validator's own post-window fixture builder grafts onto the
# current-format clear-review Markdown). The current-format findings
# builder predates the dated freshness windows, so a findings-bearing
# fixture dated after the fences needs this graft to satisfy the full
# current contract.
_POST_WINDOW_META_LINES = [
    "- Review mode: targeted",
    "- Changed-risk signals: none",
    "- Prior findings supplied as filter: no",
    "- Last fix commit: none",
    "- Record kind: canonical",
    "- Coverage: clean",
]


def _post_window_findings_markdown(findings, title):
    """Findings-bearing Markdown twin of the post-window clear fixture."""
    markdown = vrs._current_findings_markdown(findings, title=title)
    return markdown.replace(
        "- Panel mode: full",
        "- Panel mode: full\n" + "\n".join(_POST_WINDOW_META_LINES),
        1,
    )


def _post_window_findings_payload(findings):
    """Post-window sidecar carrying ``findings`` with parity counts."""
    payload = vrs._post_window_fixture_payload("plan")
    payload["findings"] = findings
    payload["counts"]["staged_findings"] = len(findings)
    return payload


class Step31RecordValidationGateTest(unittest.TestCase):
    """The Step 3.1 gate conjunction over the unchanged validator CLI."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="step31-record-gate-")
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

    # -- fixture and runner helpers ---------------------------------------

    def _write_pair(self, tag, markdown, payload):
        """Write a staged record plus its .stats.json sidecar under root."""
        return vrs._write_staging(
            self.root,
            vrs._POST_WINDOW_FIXTURE_DATE + "-branch-review-step31-gate-" + tag + "-r1.md",
            markdown,
            payload,
        )

    def _malformed_pair(self):
        """A record whose Markdown declares one finding while its sidecar
        declares none: the conservation drift the gate must stop on."""
        finding = vrs._current_finding(id=1, severity="Medium", blocking=False)
        return self._write_pair(
            "broken",
            _post_window_findings_markdown([finding], title="step31-gate-broken"),
            vrs._post_window_fixture_payload("plan"),
        )

    def _findings_pair(self):
        finding = vrs._current_finding(id=1, severity="Medium", blocking=False)
        return self._write_pair(
            "findings",
            _post_window_findings_markdown([finding], title="step31-gate-findings"),
            _post_window_findings_payload([finding]),
        )

    def _clear_pair(self):
        return self._write_pair(
            "clear",
            vrs._post_window_fixture_markdown("plan", title="step31-gate-clear"),
            vrs._post_window_fixture_payload("plan"),
        )

    def _run_validator(self, argv):
        """Run the validator CLI in-process under stream capture; SystemExit
        is the usage-error channel, so its code is the return value."""
        out_buf, err_buf = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out_buf), contextlib.redirect_stderr(err_buf):
            try:
                code = vrs.main(argv)
            except SystemExit as exc:
                code = exc.code
        return code, out_buf.getvalue(), err_buf.getvalue()

    def _assert_single_final_outcome(self, stdout_text, expected):
        rows = [
            row.strip()
            for row in stdout_text.splitlines()
            if row.strip().startswith("OUTCOME:")
        ]
        self.assertEqual(rows, ["OUTCOME: " + expected])
        self.assertTrue(stdout_text.rstrip().endswith("OUTCOME: " + expected))

    # -- the gate arms -----------------------------------------------------

    def test_soft_mode_reports_fail_at_exit_zero_on_malformed_pair(self):
        """The trap arm: a malformed pair leaves exit 0 while the final
        outcome line still reads OUTCOME: fail, so exit code alone can
        never satisfy the gate."""
        path = self._malformed_pair()
        code, out, _err = self._run_validator([str(path)])
        self.assertEqual(code, 0)
        self._assert_single_final_outcome(out, "fail")

    def test_hard_mode_gates_malformed_pair_before_triage(self):
        """The gate conjunction fails on both legs for the malformed pair:
        the command does not succeed (exit 1) and the final line is not
        OUTCOME: pass, so Phase 3 stops before Step 3.2."""
        path = self._malformed_pair()
        code, out, err = self._run_validator(["--hard", str(path)])
        self.assertNotEqual(code, 0)
        self.assertEqual(code, 1)
        self._assert_single_final_outcome(out, "fail")
        self.assertIn("ERROR:", err)

    def test_malformed_sidecar_names_suppressed_checks_as_warnings(self):
        """A malformed sidecar keeps dependent checks suppressed but names
        the skipped checks on the warning channel beside the owning error."""
        path = self._clear_pair()
        path.write_text(path.read_text().replace("### Panel", "### Reviewers", 1))
        path.with_suffix(".stats.json").write_text('{"schema_version": 1,')

        result = vrs.validate_staging_file(path, hard=True)
        self.assertEqual(len(result.errors), 2, result.errors)
        self.assertTrue(
            result.errors[0].startswith("missing ### Panel under Review Statistics"),
            result.errors,
        )
        self.assertTrue(
            result.errors[1].startswith("invalid stats sidecar JSON:"),
            result.errors,
        )
        self.assertFalse(any("skipped " in error for error in result.errors))
        self.assertTrue(
            any("skipped finding conservation:" in warning for warning in result.warnings),
            result.warnings,
        )

        code, out, err = self._run_validator(["--hard", str(path)])

        self.assertEqual(code, 1)
        self._assert_single_final_outcome(out, "fail")
        self.assertIn("ERROR: invalid stats sidecar JSON:", err)
        warnings = [line for line in err.splitlines() if line.startswith("WARN: ")]
        self.assertTrue(warnings, err)
        self.assertTrue(
            any("version-1 sidecar schema" in line for line in warnings),
            warnings,
        )
        self.assertTrue(
            any("finding conservation" in line for line in warnings),
            warnings,
        )

    def test_missing_sidecar_names_only_the_sidecar_witness_check_as_skipped(self):
        """The sidecar witness source is skipped, while a Metadata source
        still reaches the witness validator."""
        path = self._clear_pair()
        content = path.read_text().replace(
            "- Last fix commit: none", "- Last fix commit: " + "a" * 40, 1
        )
        path.write_text(content)
        path.with_suffix(".stats.json").unlink()
        result = vrs.ValidationResult(path)

        with mock.patch.object(
            vrs,
            "validate_witness_ledger_shape",
            wraps=vrs.validate_witness_ledger_shape,
        ) as witness_validator:
            vrs.validate_stats_sidecar(path, content, result, enforce_witness=True)

        witness_validator.assert_called_once()
        skipped = {
            "version-1 sidecar schema validation",
            "record-kind enum validation",
            "cap-closure contract validation",
            "corrections extension validation",
            "last-fix commit agreement",
            "current sidecar field and finding validation",
            "finding conservation",
            "counts parity",
            "coverage Markdown agreement",
            "soften-watchlist agreement",
            "discarded-row ownership validation",
            "sidecar-surface witness-ledger shape validation",
        }
        self.assertEqual(
            {
                warning.split(": the stats sidecar is missing prevents evaluation", 1)[0]
                .removeprefix("skipped ")
                for warning in result.warnings
            },
            skipped,
            result.warnings,
        )
        self.assertTrue(
            any(
                "skipped sidecar-surface witness-ledger shape validation" in warning
                for warning in result.warnings
            ),
            result.warnings,
        )
        self.assertFalse(
            any("skipped witness-ledger shape validation" in warning for warning in result.warnings),
            result.warnings,
        )

    def test_nested_self_heal_skip_warning_reaches_current_result(self):
        """A skip found while walking a predecessor chain is not lost
        when that predecessor's result is merged into the current record."""
        review_id = "a" * 32
        date = "2026-10-10"
        current_path = self.root / (
            date + "-branch-review-step31-gate-nested-self-heal-r4.md"
        )
        prior_path = current_path.with_name(
            current_path.name.removesuffix("r4.md") + "r3.md"
        )
        markdown = vrs._post_window_fixture_markdown("plan").replace(
            "- Panel mode: full",
            "- Panel mode: full\n- review-run-id: " + review_id
            + "\n- review-started-at-ms: 123",
            1,
        )
        current_path.write_text(markdown)
        prior_path.write_text(markdown)
        prior_payload = vrs._post_window_fixture_payload("plan")
        prior_payload.update({"date": date, "round": 3, "source_digest": "b" * 64})
        prior_payload["extensions"] = {
            "convergence": {
                "self_heal_attempt": {"status": "unknown", "run_id": review_id}
            }
        }
        prior_path.with_suffix(".stats.json").write_text(json.dumps(prior_payload))
        current_payload = vrs._post_window_fixture_payload("plan")
        current_payload.update({"date": date, "round": 4, "source_digest": "c" * 64})
        current_payload["extensions"] = {
            "convergence": {
                "self_heal_attempt": {"status": "unknown", "run_id": review_id}
            }
        }
        result = vrs.ValidationResult(current_path)

        vrs.validate_self_heal_attempt_state(
            current_path, markdown, result, sidecar_payload=current_payload
        )

        self.assertTrue(
            any(
                "skipped self-heal chain validation for earlier rounds r1 through r1"
                in warning
                for warning in result.warnings
            ),
            result.warnings,
        )

    def test_unknown_discard_code_names_accepted_set_and_keeps_warning_pass(self):
        """An unknown discard code remains a warning and names the accepted
        set without changing the passing outcome."""
        path = self._clear_pair()
        markdown = path.read_text().replace(
            "### Discarded findings\nNone.",
            "### Discarded findings\n"
            "| Worker | Worker severity | Pattern | Theme | Reason | Notes |\n"
            "|---|---|---|---|---|---|\n"
            "| testing | Medium | testing#gap | example | "
            "not-a-real-reason | none |",
            1,
        )
        path.write_text(markdown)

        code, out, err = self._run_validator([str(path)])

        self.assertEqual(code, 0)
        self._assert_single_final_outcome(out, "pass")
        self.assertNotIn("ERROR:", err)
        warning = next(
            line
            for line in err.splitlines()
            if line.startswith("WARN: unknown discard reason code: not-a-real-reason")
        )
        accepted = ", ".join(sorted(vrs.VALID_DISCARD_REASONS))
        self.assertIn(f"accepted codes: {accepted}", warning)

    def test_identity_filename_refusal_names_required_token_shape(self):
        """A plan identity in the sidecar without an identity token keeps
        the existing refusal text and states the required filename token."""
        import hashlib

        path = self._clear_pair()
        sidecar_path = path.with_suffix(".stats.json")
        payload = json.loads(sidecar_path.read_text())
        repo_root = Path(__file__).resolve().parents[1]
        source_plan_tmp = tempfile.TemporaryDirectory(
            prefix="step31-source-plan-", dir=repo_root
        )
        self.addCleanup(source_plan_tmp.cleanup)
        plan_path = Path(source_plan_tmp.name) / "plan.md"
        plan_bytes = b"# Source plan fixture\n"
        plan_path.write_bytes(plan_bytes)
        plan_identity = plan_path.relative_to(repo_root).as_posix()
        payload.setdefault("extensions", {})["plan_identity"] = plan_identity
        payload["source_digest"] = hashlib.sha256(plan_bytes).hexdigest()
        sidecar_path.write_text(json.dumps(payload))

        code, out, err = self._run_validator(
            ["--hard", "--source-plan", str(plan_path), str(path)]
        )

        self.assertEqual(code, 1)
        self._assert_single_final_outcome(out, "fail")
        refusal = next(
            line
            for line in err.splitlines()
            if "sidecar plan_identity requires an identity-qualified review filename"
            in line
        )
        self.assertTrue(
            refusal.startswith(
                "ERROR: sidecar plan_identity requires an identity-qualified review filename"
            ),
            refusal,
        )
        self.assertIn(
            "required form: -p<8 lowercase hex>-r<N>.md",
            refusal,
        )

    def test_soft_mode_single_violation_keeps_legacy_report_and_exit(self):
        """A single independently-evaluable defect keeps soft mode's
        report-only exit and emits no cascade skip notes."""
        path = self._findings_pair()
        sidecar = path.with_suffix(".stats.json")
        payload = json.loads(sidecar.read_text())
        payload["findings"][0]["severity"] = "Critical"
        sidecar.write_text(json.dumps(payload))

        code, out, err = self._run_validator([str(path)])

        self.assertEqual(code, 0)
        self._assert_single_final_outcome(out, "fail")
        errors = [line for line in err.splitlines() if line.startswith("ERROR: ")]
        self.assertEqual(len(errors), 1, err)
        self.assertIn("finding conservation: finding 1 severity disagrees", errors[0])
        self.assertFalse(any("skipped " in line for line in err.splitlines()), err)

    def test_self_heal_first_refusal_names_skipped_earlier_rounds(self):
        """A malformed r2 stops the r3 predecessor walk with an explicit
        warning for the earlier chain segment that was not evaluated."""
        review_id = "a" * 32
        date = "2026-10-10"
        current_path = self.root / (
            date + "-branch-review-step31-gate-self-heal-r3.md"
        )
        prior_path = current_path.with_name(
            current_path.name.removesuffix("r3.md") + "r2.md"
        )
        prior_path.write_text("# Prior round\n")
        prior_payload = vrs._post_window_fixture_payload("plan")
        prior_payload.update({"date": date, "round": 2, "source_digest": "b" * 64})
        prior_payload["extensions"] = {
            "convergence": {
                "self_heal_attempt": {"status": "invalid", "run_id": review_id}
            }
        }
        prior_path.with_suffix(".stats.json").write_text(json.dumps(prior_payload))

        current_md = vrs._post_window_fixture_markdown("plan").replace(
            "- Panel mode: full",
            "- Panel mode: full\n- review-run-id: " + review_id
            + "\n- review-started-at-ms: 123",
            1,
        )
        current_path.write_text(current_md)
        current_payload = vrs._post_window_fixture_payload("plan")
        current_payload.update({"date": date, "round": 3, "source_digest": "c" * 64})
        current_payload["extensions"] = {
            "convergence": {
                "self_heal_attempt": {"status": "unknown", "run_id": review_id}
            }
        }
        result = vrs.ValidationResult(path=current_path)

        vrs._validate_self_heal_record(
            current_path, current_md, result, current_payload, [], {}
        )

        self.assertTrue(
            any(
                "self-heal chain validation for earlier rounds r1 through r1" in warning
                for warning in result.warnings
            ),
            result.warnings,
        )
        self.assertFalse(any("skipped " in error for error in result.errors))

    def test_hard_mode_passes_valid_findings_bearing_record(self):
        """A valid findings-bearing pair passes the same hard-mode
        invocation under the existing grammar, no new schema rule."""
        path = self._findings_pair()
        code, out, err = self._run_validator(["--hard", str(path)])
        self.assertEqual(code, 0, err)
        self._assert_single_final_outcome(out, "pass")

    def test_hard_mode_passes_valid_clear_record(self):
        """A valid clear pair passes the same hard-mode invocation with
        the validator's own post-window fixture shapes."""
        path = self._clear_pair()
        code, out, err = self._run_validator(["--hard", str(path)])
        self.assertEqual(code, 0, err)
        self._assert_single_final_outcome(out, "pass")

    def test_validator_telemetry_stays_under_the_temp_metrics_home(self):
        """Validator telemetry appends into the test's temporary metrics
        home, never into the repository (the sidecar test's Task 2
        isolation posture applied to this gate's runs)."""
        if vrs.invocation_telemetry is None:
            self.skipTest("invocation telemetry sibling absent (fail-open copy)")
        path = self._findings_pair()
        code, out, _err = self._run_validator(["--hard", str(path)])
        self.assertEqual(code, 0)
        metrics_log = self.metrics_home / invocation_telemetry.INVOCATION_COSTS_FILENAME
        self.assertTrue(metrics_log.is_file())
        self.assertGreaterEqual(
            len(metrics_log.read_text(encoding="utf-8").splitlines()), 1
        )


if __name__ == "__main__":
    unittest.main()
