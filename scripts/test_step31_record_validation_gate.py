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
