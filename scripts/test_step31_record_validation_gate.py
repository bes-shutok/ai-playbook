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

The seam canaries (``SeamDerivationCanaryTest``) pin the validator's
public self-heal chain-grammar derivation seam (``well_formed_self_heal_state``,
``valid_prior_chain_state``, ``self_heal_chain_state``,
``calendar_valid_record_date``, ``AmbiguousChainPredecessor``) with literal
golden values derived from the producer's behavior at promotion time. The
seam and the enforcement carry-forward block in
``validate_self_heal_attempt_state``/``_validate_self_heal_record`` are
intentional twins with a change-both duty; the parity witness holds them
in agreement on the documented prior-evidence corpus. This suite never
imports ``produce_exec_review_record`` (no differential-oracle import
whose oracle the producer rewiring deletes).

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


class SeamDerivationCanaryTest(unittest.TestCase):
    """Canaries over the validator's public self-heal chain-grammar seam.

    Every expected value below is a literal pinned from the producer's
    behavior at promotion time (2026-11-07, plan
    docs/history/plans/2026-11-07-producer-code-family-record-arm.md
    Task 1); the suite never imports ``produce_exec_review_record``, so
    the pins survive the producer's Task 2 rewiring onto the seam. The
    seam derivation and the enforcement carry-forward block inside
    ``_validate_self_heal_record`` are intentional twins with a
    change-both duty; the parity witness at the bottom of this class
    holds the twins in agreement on the documented prior-evidence corpus.
    """

    # Literal golden ids/digests (never generated, so a grammar change
    # that flips acceptance flips a visible constant, not a computed one).
    RUN_ID_A = "a" * 32
    RUN_ID_B = "b" * 32
    RUN_ID_C = "c" * 32
    DIGEST_D = "d" * 64
    DIGEST_E = "e" * 64

    DATE = "2026-10-10"
    CURRENT_DATE = "2026-10-11"
    CHAIN_STEM = "branch-review-step31-seam"

    # The producer's exact ambiguous-predecessor refusal text at
    # promotion time, carried verbatim by the seam's
    # AmbiguousChainPredecessor.
    AMBIGUOUS_MESSAGE = (
        "ambiguous prior-round records for chain "
        "'branch-review-ambiguity' round r1: "
        "['2026-10-10-branch-review-ambiguity-r1.md', "
        "'2026-10-11-branch-review-ambiguity-r1.md']; the shared "
        "self-heal gate refuses an ambiguous predecessor, "
        "disambiguate the directory first"
    )

    # The enforcement arm's acceptance text for an unknown state bound to
    # the current run id when a valid prior exists; its presence in the
    # current record's errors is the enforcement-side witness that the
    # carry-forward block classified the prior as valid.
    ENFORCEMENT_VALID_PRIOR_MESSAGE = (
        "unknown state is allowed only when prior round evidence is unavailable"
    )

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="step31-seam-canary-")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    # -- fixture helpers ---------------------------------------------------

    def _minted_markdown(self, run_id):
        """Post-window clear Markdown carrying the mint pair for run_id."""
        return vrs._post_window_fixture_markdown("plan").replace(
            "- Panel mode: full",
            "- Panel mode: full\n- review-run-id: " + run_id
            + "\n- review-started-at-ms: 123",
            1,
        )

    def _bare_markdown(self):
        """Post-window clear Markdown with no mint pair and no fallback
        marker (the mint-gate-error shape)."""
        return vrs._post_window_fixture_markdown("plan")

    def _prior_payload(self, run_id=RUN_ID_A, digest=DIGEST_D, round_value=1,
                       date=DATE, status="unused", record_kind="canonical"):
        """Post-window canonical sidecar for a prior record with the given
        self-heal chain state (consumed states carry their bindings)."""
        payload = vrs._post_window_fixture_payload("plan")
        payload.update({"date": date, "round": round_value, "source_digest": digest})
        if record_kind is not None:
            payload["record_kind"] = record_kind
        state = {"status": status, "run_id": run_id}
        if status == "consumed":
            state.update({"round": "r1", "source_digest": digest})
        payload["extensions"] = {"convergence": {"self_heal_attempt": state}}
        return payload

    def _write_pair(self, directory, name, markdown, payload):
        """Write a record plus its .stats.json sidecar under directory;
        a string payload is written verbatim (malformed-JSON shapes)."""
        path = directory / name
        path.write_text(markdown)
        if payload is not None:
            path.with_suffix(".stats.json").write_text(
                payload if isinstance(payload, str) else json.dumps(payload)
            )
        return path

    def _prior_name(self, stem=CHAIN_STEM, date=DATE):
        return f"{date}-{stem}-r1.md"

    # -- well_formed_self_heal_state canaries ------------------------------

    def test_well_formed_self_heal_state_golden_booleans(self):
        """The state grammar's golden booleans pinned from the producer's
        behavior: the three status shapes accept with their exact key
        sets; wrong key sets, malformed bindings, and non-dict payloads
        all refuse."""
        cases = [
            ({"status": "unused", "run_id": self.RUN_ID_A}, True),
            ({"status": "consumed", "run_id": self.RUN_ID_B,
              "round": "r1", "source_digest": self.DIGEST_D}, True),
            ({"status": "unknown", "run_id": self.RUN_ID_C}, True),
            ({"status": "unused", "run_id": self.RUN_ID_A, "extra": 1}, False),
            ({"status": "unused", "run_id": "xyz"}, False),
            ({"status": "consumed", "run_id": self.RUN_ID_B,
              "round": "1", "source_digest": self.DIGEST_D}, False),
            ({"status": "consumed", "run_id": self.RUN_ID_B,
              "round": "r1", "source_digest": "zz"}, False),
            ({"status": "done", "run_id": self.RUN_ID_A}, False),
            ("unused", False),
            ({"status": "unused"}, False),
        ]
        for state, expected in cases:
            with self.subTest(state=state):
                self.assertIs(vrs.well_formed_self_heal_state(state), expected)

    # -- calendar_valid_record_date public surface -------------------------

    def test_calendar_valid_record_date_public_surface_goldens(self):
        """The public calendar surface returns the pinned results of the
        private date validator it aliases: calendar-valid dates accept;
        impossible calendar dates, shape-valid-but-non-calendar strings,
        non-strings, and non-values refuse."""
        cases = [
            ("2026-10-10", True),
            ("2026-02-30", False),
            ("2026-13-01", False),
            ("not-a-date", False),
            (None, False),
            (20261010, False),
        ]
        for value, expected in cases:
            with self.subTest(value=repr(value)):
                self.assertIs(vrs.calendar_valid_record_date(value), expected)
                self.assertIs(
                    vrs.calendar_valid_record_date(value),
                    vrs._calendar_valid_record_date(value),
                )

    # -- valid_prior_chain_state corpus ------------------------------------

    def _corpus_builders(self):
        """The documented prior-evidence fixture corpus, one builder per
        documented shape; each builder writes into a fresh directory."""
        stem, date, markdown = self.CHAIN_STEM, self.DATE, self._minted_markdown(self.RUN_ID_A)

        def _build(directory, name, md, payload):
            return self._write_pair(directory, name, md, payload)

        return {
            "valid": lambda d: _build(d, self._prior_name(stem, date), markdown,
                                      self._prior_payload()),
            "missing_file": lambda d: None,
            "missing_sidecar": lambda d: (d / self._prior_name(stem, date)).write_text(markdown),
            "malformed_json": lambda d: _build(d, self._prior_name(stem, date), markdown,
                                               '{"schema_version": 1,'),
            "pre_fence": lambda d: _build(d, self._prior_name(stem, "2026-10-08"),
                                          markdown, self._prior_payload(date="2026-10-08")),
            "non_canonical": lambda d: _build(d, self._prior_name(stem, date), markdown,
                                              self._prior_payload(record_kind="review_notes")),
            "bad_digest": lambda d: _build(d, self._prior_name(stem, date), markdown,
                                           self._prior_payload(digest="deadbeef")),
            "state_not_well_formed": lambda d: _build(d, self._prior_name(stem, date), markdown,
                                                      self._prior_payload(status="bogus")),
            "gate_errors": lambda d: _build(d, self._prior_name(stem, date),
                                            self._bare_markdown(), self._prior_payload()),
            # The non-dict JSON payload: the shape class the enforcement
            # arm's AttributeError tolerance exists for.
            "nondict_json": lambda d: _build(d, self._prior_name(stem, date), markdown, "[]"),
        }

    def _corpus_prior_name(self, label):
        """The prior record name the builder for ``label`` actually
        wrote; label-aware so cases like ``pre_fence`` (written at the
        2026-10-08 pre-fence date) exercise the fence arm, not the
        missing-file arm."""
        date = "2026-10-08" if label == "pre_fence" else self.DATE
        return self._prior_name(self.CHAIN_STEM, date)

    def test_valid_prior_chain_state_corpus_goldens(self):
        """The prior-evidence corpus pinned from the producer's behavior:
        only the fully valid post-fence canonical pair yields its chain
        state; every other documented shape yields None."""
        for label, builder in self._corpus_builders().items():
            with self.subTest(case=label):
                directory = self.root / f"corpus-{label}"
                directory.mkdir()
                builder(directory)
                prior_path = directory / self._corpus_prior_name(label)
                result = vrs.valid_prior_chain_state(prior_path)
                if label == "valid":
                    self.assertEqual(
                        result,
                        {"status": "unused", "run_id": self.RUN_ID_A},
                    )
                else:
                    self.assertIsNone(result)

    # -- self_heal_chain_state arms -----------------------------------------

    def test_self_heal_chain_state_round_selection_starts_unused(self):
        """Round 1 and unnumbered records start unused bound to the
        record's own run id, with no directory walk."""
        for name in (f"{self.CURRENT_DATE}-{self.CHAIN_STEM}-r1.md",
                     f"{self.CURRENT_DATE}-{self.CHAIN_STEM}.md"):
            with self.subTest(name=name):
                record_path = self.root / name  # the record need not exist
                self.assertEqual(
                    vrs.self_heal_chain_state(record_path, self.RUN_ID_C),
                    {"status": "unused", "run_id": self.RUN_ID_C},
                )

    def test_self_heal_chain_state_carries_valid_consumed_prior(self):
        """A higher round with one valid prior carries the prior's state
        verbatim: the returned run_id is the prior's own id (distinct
        from the record-under-construction's run id) and the status is
        consumed with its bindings, a shape reachable only by carrying,
        never by re-minting."""
        directory = self.root / "carry"
        directory.mkdir()
        self._write_pair(
            directory, self._prior_name(), self._minted_markdown(self.RUN_ID_B),
            self._prior_payload(run_id=self.RUN_ID_B, status="consumed"),
        )
        record_path = directory / f"{self.CURRENT_DATE}-{self.CHAIN_STEM}-r2.md"
        self.assertEqual(
            vrs.self_heal_chain_state(record_path, self.RUN_ID_A),
            {"status": "consumed", "run_id": self.RUN_ID_B,
             "round": "r1", "source_digest": self.DIGEST_D},
        )

    def test_self_heal_chain_state_unknown_when_no_valid_prior(self):
        """A higher round with no valid prior reports unknown bound to the
        record's own run id: over an empty directory and when only a
        wrong-round same-stem record is present (the round filter
        honored)."""
        empty = self.root / "unknown-empty"
        empty.mkdir()
        self.assertEqual(
            vrs.self_heal_chain_state(
                empty / f"{self.CURRENT_DATE}-{self.CHAIN_STEM}-r3.md", self.RUN_ID_C
            ),
            {"status": "unknown", "run_id": self.RUN_ID_C},
        )
        wrong_round = self.root / "unknown-wrong-round"
        wrong_round.mkdir()
        self._write_pair(wrong_round, self._prior_name(),  # an r1 present
                         self._minted_markdown(self.RUN_ID_A), self._prior_payload())
        self.assertEqual(
            vrs.self_heal_chain_state(
                wrong_round / f"{self.CURRENT_DATE}-{self.CHAIN_STEM}-r3.md",
                self.RUN_ID_C,
            ),
            {"status": "unknown", "run_id": self.RUN_ID_C},
        )

    def test_self_heal_chain_state_treats_unnumbered_record_as_prior_candidate(self):
        """A higher round with an unnumbered same-stem record selects it
        as the prior candidate: its state is carried verbatim."""
        directory = self.root / "unnumbered-candidate"
        directory.mkdir()
        self._write_pair(
            directory, f"{self.DATE}-{self.CHAIN_STEM}.md",
            self._minted_markdown(self.RUN_ID_A), self._prior_payload(),
        )
        record_path = directory / f"{self.CURRENT_DATE}-{self.CHAIN_STEM}-r2.md"
        self.assertEqual(
            vrs.self_heal_chain_state(record_path, self.RUN_ID_C),
            {"status": "unused", "run_id": self.RUN_ID_A},
        )

    def test_self_heal_chain_state_refuses_ambiguous_predecessor(self):
        """Two dated records resolving to the same chain stem and prior
        round raise the seam's own AmbiguousChainPredecessor (a
        ValueError subclass) carrying the producer's exact refusal text,
        before anything is written."""
        directory = self.root / "ambiguous"
        directory.mkdir()
        ambiguity_stem = "branch-review-ambiguity"
        self._write_pair(
            directory, self._prior_name(ambiguity_stem, "2026-10-10"),
            self._minted_markdown(self.RUN_ID_A), self._prior_payload(),
        )
        self._write_pair(
            directory, self._prior_name(ambiguity_stem, "2026-10-11"),
            self._minted_markdown(self.RUN_ID_B),
            self._prior_payload(run_id=self.RUN_ID_B),
        )
        record_path = directory / (
            "2026-10-12-branch-review-ambiguity-r2.md"
        )
        with self.assertRaises(vrs.AmbiguousChainPredecessor) as caught:
            vrs.self_heal_chain_state(record_path, self.RUN_ID_C)
        self.assertIsInstance(caught.exception, ValueError)
        self.assertEqual(str(caught.exception), self.AMBIGUOUS_MESSAGE)

    # -- parity witness (seam vs enforcement twin) --------------------------

    def _parity_case(self, label, builder):
        """Run one corpus case through both derivations: the seam's
        ``valid_prior_chain_state`` and the enforcement carry-forward
        block (via ``validate_self_heal_attempt_state`` over a
        well-formed unknown-state r2 whose run id binds to the prior's
        state when the seam accepted it). Returns
        (seam_state, enforcement_saw_valid_prior, errors)."""
        directory = self.root / f"parity-{label}"
        directory.mkdir()
        builder(directory)
        prior_path = directory / self._corpus_prior_name(label)
        seam_state = vrs.valid_prior_chain_state(prior_path)
        prior_run_id = seam_state["run_id"] if seam_state else self.RUN_ID_B
        current_path = directory / f"{self.CURRENT_DATE}-{self.CHAIN_STEM}-r2.md"
        current_md = self._minted_markdown(prior_run_id)
        current_payload = self._prior_payload(
            run_id=prior_run_id, digest=self.DIGEST_E, round_value=2,
            date=self.CURRENT_DATE,
        )
        current_payload["extensions"] = {
            "convergence": {
                "self_heal_attempt": {"status": "unknown", "run_id": prior_run_id}
            }
        }
        current_path.write_text(current_md)
        current_path.with_suffix(".stats.json").write_text(json.dumps(current_payload))
        result = vrs.ValidationResult(current_path)
        vrs.validate_self_heal_attempt_state(
            current_path, current_md, result, sidecar_payload=current_payload
        )
        enforcement_saw_valid_prior = any(
            self.ENFORCEMENT_VALID_PRIOR_MESSAGE in error for error in result.errors
        )
        return seam_state, enforcement_saw_valid_prior, result.errors

    def test_parity_witness_seam_and_enforcement_twins_agree(self):
        """Parity witness over the shared prior-evidence corpus: the seam
        (``valid_prior_chain_state``) and the enforcement carry-forward
        block agree on every documented case: the block classifies a
        prior valid exactly when the seam returns its state. The two
        derivations are intentional twins: a grammar change lands in
        both together (see the twin-duty comments in
        scripts/validate_review_staging.py)."""
        for label, builder in self._corpus_builders().items():
            with self.subTest(case=label):
                seam_state, enforcement_saw_valid_prior, errors = self._parity_case(label, builder)
                self.assertEqual(
                    enforcement_saw_valid_prior,
                    seam_state is not None,
                    f"twin disagreement on {label}: seam={seam_state!r} errors={errors}",
                )
                if label == "valid":
                    self.assertEqual(
                        seam_state, {"status": "unused", "run_id": self.RUN_ID_A}
                    )
                    self.assertEqual(len(errors), 1, errors)
                else:
                    self.assertEqual(errors, [], errors)


if __name__ == "__main__":
    unittest.main()
