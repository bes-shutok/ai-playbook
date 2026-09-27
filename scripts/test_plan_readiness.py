"""Unit tests for the plan_readiness scope-classification probe.

Covers the classification-tag placement check of
``scope_classification_problem`` (the enforcement side of the plans
skill's Classification tag rule): a ``[class: ...]`` tag must sit on a
task checklist item's first (checkbox-marker) line; a tag wrapped onto
a continuation line is reported as a placement problem instead of
classifying the item untagged, a tag mention inside backtick spans is a
quote and never trips, and a genuinely untagged item still fails.

Run from the repository root:

    PYTHONPATH=scripts python3 -m unittest scripts.test_plan_readiness
"""

import unittest

from plan_readiness import scope_classification_problem


def _plan_with_task_section(task_body: str) -> str:
    """Minimal plan text carrying one task section with ``task_body``."""
    return (
        "# P\n\n"
        "## Tasks\n\n"
        "### Task 1: Do the thing\n\n"
        f"{task_body}\n"
    )


class ScopeClassificationPlacementTest(unittest.TestCase):
    """Placement of the classification tag on a checklist item."""

    def test_continuation_line_tag_reports_placement(self):
        plan = _plan_with_task_section(
            "- [ ] Write the module with care\n"
            "  and diligence. [class: IMPLEMENTATION_REQUIRED]\n"
        )
        reason = scope_classification_problem(plan)
        self.assertIsNotNone(reason)
        self.assertIn("non-checkbox line", reason)
        self.assertIn("Task 1", reason)

    def test_first_line_tag_clears(self):
        plan = _plan_with_task_section(
            "- [ ] Write the module with care and diligence. "
            "[class: IMPLEMENTATION_REQUIRED]\n"
        )
        self.assertIsNone(scope_classification_problem(plan))

    def test_backticked_tag_mention_in_prose_clears(self):
        plan = _plan_with_task_section(
            "- [ ] Write the module. [class: IMPLEMENTATION_REQUIRED]\n"
            "\n"
            "Remember: every item carries `[class: ...]` at its end.\n"
        )
        self.assertIsNone(scope_classification_problem(plan))

    def test_untagged_item_still_fails(self):
        plan = _plan_with_task_section("- [ ] Write the module.\n")
        reason = scope_classification_problem(plan)
        self.assertIsNotNone(reason)
        self.assertIn("carries no", reason)


# --------------------------------------------------------------------------- #
# Fence-balance structural failure (both readiness entries, CLI level).
# --------------------------------------------------------------------------- #

import contextlib
import io
import json
import os
import shutil
import tempfile
from pathlib import Path

import plan_readiness

FACTS_BODY = (
    "# facts\n\n```toml\n"
    'plans_dir = "plans"\n'
    'reviews_dir = "reviews"\n'
    "```\n"
)

# A plan whose structural probes all pass cleanly, plus a trailing fenced
# block whose closer was dropped. The opener's line number is asserted
# verbatim in the failure message.
BALANCED_PLAN = (
    "# P\n\n"
    "## Assumptions\n\n"
    "Decision points requiring a grill: none remain.\n\n"
    "## Tasks\n\n"
    "### Task 1: Do the thing\n\n"
    "- [ ] Write the module. [class: IMPLEMENTATION_REQUIRED]\n"
)
UNCLOSED_TAIL = "\n```bash\necho never closed\n"


class PlanReadinessFenceBalanceTest(unittest.TestCase):
    """An unclosed fence fails closed naming the opener line; a balanced
    document runs the structural probes over the full text."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="fence-balance-fixture-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        (self.root / ".ai-playbook").mkdir()
        (self.root / ".ai-playbook" / "facts.md").write_text(
            FACTS_BODY, encoding="utf-8"
        )
        (self.root / "plans").mkdir()
        (self.root / "reviews").mkdir()

    def _run_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        prev = os.getcwd()
        os.chdir(self.root)
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc = plan_readiness.main(argv)
        finally:
            os.chdir(prev)
        return rc, out.getvalue(), err.getvalue()

    def _write_fixture(self, plan_text: str) -> Path:
        plan, _ = plan_readiness._write_clean_state(
            self.root / "plans",
            self.root / "reviews",
            plan_text=plan_text,
            date="2026-09-25",
        )
        return plan

    def test_unclosed_fence_fails_closed_naming_line(self):
        plan_text = BALANCED_PLAN + UNCLOSED_TAIL
        opener_line = plan_text.split("\n").index("```bash") + 1
        plan = self._write_fixture(plan_text)
        rc, out, err = self._run_main([str(plan)])
        self.assertNotEqual(rc, 0, (out, err))
        self.assertIn("unclosed fence", err)
        self.assertIn(f"line {opener_line}", err)
        # Pre-round entry: same structural failure through the pre-round
        # channel, before any probe evaluates the stripped text.
        rc, out, err = self._run_main(["--pre-round", str(plan)])
        self.assertNotEqual(rc, 0, (out, err))
        self.assertIn(
            f"readiness PRE-ROUND FAILED: unclosed fence opener at line "
            f"{opener_line}",
            err,
        )

    def test_balanced_fences_still_pass(self):
        plan = self._write_fixture(BALANCED_PLAN)
        rc, out, err = self._run_main([str(plan)])
        self.assertEqual(rc, 0, (out, err))
        self.assertNotIn("unclosed fence", err)
        rc, out, err = self._run_main(["--pre-round", str(plan)])
        self.assertEqual(rc, 0, (out, err))


# --------------------------------------------------------------------------- #
# --check-review-name probe: one round pair re-verified against the gate's
# own discovery shape (filename glob, sidecar presence, sidecar artifact_slug,
# coverage self-references) before the loop folds findings or relaunches.
# --------------------------------------------------------------------------- #

CANONICAL_ROUND_NAME = "2026-09-01-plan-review-fixture-feature-r1.md"
SHORT_SLUG_ROUND_NAME = "2026-09-01-plan-review-fixture-r1.md"
REVIEW_NAME_ROUND_MD = (
    "# Plan Review: fixture feature\n\n"
    "## Summary\n\n"
    "- ready=yes\n"
)


class ReviewNameCheckTest(unittest.TestCase):
    """The ``--check-review-name`` probe binds one written round pair to
    the plan's feature slug through the gate's own discovery shape."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="review-name-fixture-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        (self.root / ".ai-playbook").mkdir()
        (self.root / ".ai-playbook" / "facts.md").write_text(
            FACTS_BODY, encoding="utf-8"
        )
        self.plans = self.root / "plans"
        self.reviews = self.root / "reviews"
        self.plans.mkdir()
        self.reviews.mkdir()
        self.plan = self.plans / "2026-09-01-fixture-feature.md"
        self.plan.write_text("# Fixture plan\n\nBody.\n", encoding="utf-8")

    def _run_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        prev = os.getcwd()
        os.chdir(self.root)
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc = plan_readiness.main(argv)
        finally:
            os.chdir(prev)
        return rc, out.getvalue(), err.getvalue()

    def _write_round(self, name, sidecar, directory=None):
        """One round Markdown plus its ``.stats.json`` sidecar.

        ``sidecar`` is JSON-serialized when it is an object, written
        verbatim when it is a string, and skipped when ``None``.
        """
        round_path = (directory or self.reviews) / name
        round_path.write_text(REVIEW_NAME_ROUND_MD, encoding="utf-8")
        if sidecar is not None:
            sidecar_text = (
                sidecar if isinstance(sidecar, str) else json.dumps(sidecar)
            )
            round_path.with_suffix(".stats.json").write_text(
                sidecar_text, encoding="utf-8"
            )
        return round_path

    def _run_probe(self, round_path):
        return self._run_main(
            [str(self.plan), "--check-review-name", str(round_path)]
        )

    def _dangling_path(self):
        return self.reviews / "2026-08-01-plan-review-older-feature-r1.md"

    def test_accepts_canonical_pair(self):
        round_path = self._write_round(
            CANONICAL_ROUND_NAME, {"artifact_slug": "fixture-feature"}
        )
        rc, out, err = self._run_probe(round_path)
        self.assertEqual(rc, 0, (out, err))
        self.assertIn("review name check OK", out)

    def test_rejects_short_slug(self):
        round_path = self._write_round(
            SHORT_SLUG_ROUND_NAME, {"artifact_slug": "fixture"}
        )
        rc, out, err = self._run_probe(round_path)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn("fixture-feature", err)
        self.assertIn("discovery shape", err)

    def test_rejects_missing_sidecar(self):
        round_path = self._write_round(CANONICAL_ROUND_NAME, None)
        rc, out, err = self._run_probe(round_path)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn("missing stats sidecar", err)

    def test_rejects_sidecar_slug_mismatch(self):
        round_path = self._write_round(
            CANONICAL_ROUND_NAME, {"artifact_slug": "fixture"}
        )
        rc, out, err = self._run_probe(round_path)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn("artifact_slug", err)
        self.assertIn("expected 'fixture-feature'", err)

    def test_rejects_dangling_inherited_coverage(self):
        dangling = str(self._dangling_path())
        round_path = self._write_round(
            CANONICAL_ROUND_NAME,
            {
                "artifact_slug": "fixture-feature",
                "coverage": {
                    "inherited_coverage": [
                        {"lens": "testing", "artifact": dangling}
                    ]
                },
            },
        )
        rc, out, err = self._run_probe(round_path)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn(dangling, err)

    def test_rejects_dangling_attempt_reference(self):
        dangling = str(self._dangling_path())
        round_path = self._write_round(
            CANONICAL_ROUND_NAME,
            {
                "artifact_slug": "fixture-feature",
                "coverage": {
                    "attempts": [
                        {"attempt_id": 1, "artifact": dangling}
                    ]
                },
            },
        )
        rc, out, err = self._run_probe(round_path)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn(dangling, err)

    def test_rejects_dangling_replacement_reference(self):
        dangling = str(self._dangling_path())
        round_path = self._write_round(
            CANONICAL_ROUND_NAME,
            {
                "artifact_slug": "fixture-feature",
                "coverage": {
                    "replacement": [
                        {"lens": "testing", "original_artifact": dangling}
                    ]
                },
            },
        )
        rc, out, err = self._run_probe(round_path)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn(dangling, err)

    def test_rejects_corrupt_sidecar(self):
        round_path = self._write_round(CANONICAL_ROUND_NAME, "{not json")
        rc, out, err = self._run_probe(round_path)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn("malformed stats sidecar", err)
        self.assertNotIn("Traceback", err)
        self.assertNotIn("Traceback", out)

    def test_rejects_round_outside_reviews_dir(self):
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        round_path = self._write_round(
            CANONICAL_ROUND_NAME,
            {"artifact_slug": "fixture-feature"},
            directory=elsewhere,
        )
        rc, out, err = self._run_probe(round_path)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn("reviews directory", err)

    def test_rejects_symlinked_round_identity(self):
        # F1 canary: identity (parent + filename) is judged on the path as
        # claimed, never the symlink target, so a symlink named like a
        # nonexistent round cannot borrow a clean pair's identity.
        target = self._write_round(
            CANONICAL_ROUND_NAME, {"artifact_slug": "fixture-feature"}
        )
        claimed = self.reviews / "2026-09-01-plan-review-fixture-feature-r9.md"
        os.symlink(target, claimed)
        rc, out, err = self._run_probe(claimed)
        self.assertEqual(rc, 1, (out, err))
        # The claimed pair is judged under the claimed names: the symlink
        # borrows the target's identity checks but its own r9 sidecar is
        # missing, which is the fail.
        self.assertIn("missing stats sidecar", err)
        self.assertIn("r9", err)

    def test_missing_plan_path_is_usage_error(self):
        round_path = self.reviews / CANONICAL_ROUND_NAME
        with self.assertRaises(SystemExit) as caught:
            self._run_main(["--check-review-name", str(round_path)])
        self.assertEqual(caught.exception.code, 2)

    def test_mode_combination_is_usage_error(self):
        round_path = self.reviews / CANONICAL_ROUND_NAME
        for flag in ("--selftest", "--sweep", "--pre-round"):
            with self.subTest(flag=flag):
                with self.assertRaises(SystemExit) as caught:
                    self._run_main(
                        [
                            str(self.plan),
                            flag,
                            "--check-review-name",
                            str(round_path),
                        ]
                    )
                self.assertEqual(caught.exception.code, 2)


# --------------------------------------------------------------------------- #
# Cap-closure terminal shape (certification machinery contract-collisions
# plan, Task 1): the ``extensions.cap_closure`` sidecar contract in the
# staging validator and the readiness-gate acceptance built on it. The
# staged patterns, the residual section body, and the declared residuals
# count are reconciled by the gate probe; the four guards in
# ``CapClosureReadinessTest`` pin today's behavior and must keep passing
# before and after the change.
# --------------------------------------------------------------------------- #

import re

import validate_review_staging as vrs

CAP_CLOSURE_SECTION = "## Residual findings (cap closure)"
CAP_CLOSURE_SLUG = "cap-closure-fixture"
CAP_CLOSURE_ROUND = 5
CAP_CLOSURE_ROUND_SUFFIX = "r5"
CAP_CLOSURE_DATE = "2026-09-01"
CAP_CLOSURE_MODERN_DATE = "2026-09-08"
CAP_CLOSURE_PATTERN = "testing#weak-assertion"
CAP_CLOSURE_BLOCK_PATTERN = "quality#cap-blocker"
# Pre-fold plan bytes: their digest is the declaration's pre_fold_digest,
# always different from the digest of the current (post-fold) plan bytes.
CAP_CLOSURE_PRE_FOLD_BYTES = b"# Cap closure fixture (pre-fold plan bytes)\n"
CAP_CLOSURE_THIRD_BYTES = b"# Cap closure fixture (third recorded state)\n"
_MALFORMED_SIDECAR_PREFIX = (
    "malformed stats sidecar (schema validation failed) for round "
    f"r{CAP_CLOSURE_ROUND_SUFFIX[1:]}: "
)


def _cap_closure_pre_fold_digest():
    return vrs.compute_source_digest("plan", CAP_CLOSURE_PRE_FOLD_BYTES)


def _cap_closure_declaration(**overrides):
    """Conforming ``extensions.cap_closure`` declaration for the fixtures."""
    declaration = {
        "plan_section": CAP_CLOSURE_SECTION,
        "round": str(CAP_CLOSURE_ROUND),
        "residuals": 1,
        "pre_fold_digest": _cap_closure_pre_fold_digest(),
    }
    declaration.update(overrides)
    return declaration


def _cap_closure_finding(**overrides):
    """One valid version-1 finding row mirrored into the review Markdown."""
    finding = vrs._current_finding(
        pattern=CAP_CLOSURE_PATTERN, triage="fixed"
    )
    finding.update(overrides)
    return finding


class CapClosureContractTest(unittest.TestCase):
    """The ``validate_cap_closure_contract`` shape gate (contract level).

    Mirrors the ``validate_address_fanout_contract`` idiom: version-1-only
    with unknown-key rejection, called with the ``payload, result,
    schema_class`` idiom. The negative cases are table-driven and include
    declarations whose unknown keys are themselves named with the routed
    literals (the producer-echo path); the routed-substring arm pins the
    negative-literal routing contract as a suite invariant: every reported
    problem is static text plus filtered echoes (no problem may contain
    the step-3 routed substrings), so the readiness mapping can never
    misclassify a declaration rejection as a stale-digest or source-kind
    failure.
    """

    def _payload(self, declaration=None, round_value=CAP_CLOSURE_ROUND):
        payload = vrs._version1_payload()
        payload["review_type"] = "plan"
        payload["source_kind"] = "plan"
        payload["round"] = round_value
        if declaration is not None:
            payload["extensions"] = {"cap_closure": declaration}
        return payload

    def _validate(self, payload, schema_class="current-v1"):
        result = vrs.ValidationResult(path=Path("cap-closure-fixture.md"))
        vrs.validate_cap_closure_contract(
            payload, result, schema_class=schema_class
        )
        return result

    @staticmethod
    def _targeted(result, fragment):
        return [
            error
            for error in result.errors
            if "extensions.cap_closure" in error and fragment in error
        ]

    def _rejection_cases(self):
        """``(name, payload, targeted fragment)`` for every rejection arm;
        shared by the malformed-declaration and routed-substring tests."""
        cases = []
        for name, key in (
            ("missing plan_section", "plan_section"),
            ("missing round", "round"),
            ("missing residuals", "residuals"),
            ("missing pre_fold_digest", "pre_fold_digest"),
        ):
            declaration = _cap_closure_declaration()
            del declaration[key]
            cases.append(
                (
                    name,
                    self._payload(declaration),
                    f"missing required key '{key}'",
                )
            )
        for name, key in (
            ("unknown key", "scheme"),
            ("unknown key named source_digest", "source_digest"),
            ("unknown key named source_kind", "source_kind"),
        ):
            unknown = _cap_closure_declaration()
            unknown[key] = "extra"
            cases.append(
                (
                    name,
                    self._payload(unknown),
                    "accepts only the keys",
                )
            )
        cases.append(
            (
                "wrong plan_section literal",
                self._payload(
                    _cap_closure_declaration(plan_section="## Wrong section")
                ),
                "must be exactly",
            )
        )
        cases.append(
            (
                "float round",
                self._payload(_cap_closure_declaration(round=1.5)),
                "must be an integer or a string",
            )
        )
        cases.append(
            (
                "boolean round",
                self._payload(_cap_closure_declaration(round=True)),
                "boolean excluded",
            )
        )
        cases.append(
            (
                "round differs from sidecar",
                self._payload(_cap_closure_declaration(round="6")),
                "must equal the sidecar round",
            )
        )
        cases.append(
            (
                "unparsable round",
                self._payload(
                    _cap_closure_declaration(round="cap"), round_value="cap"
                ),
                "does not parse as an integer",
            )
        )
        for name, value in (
            ("negative residuals", -1),
            ("string residuals", "1"),
            ("boolean residuals", True),
        ):
            cases.append(
                (
                    name,
                    self._payload(_cap_closure_declaration(residuals=value)),
                    "must be a non-negative integer",
                )
            )
        for name, value in (
            ("non-hex pre_fold_digest", "not-hex"),
            ("uppercase pre_fold_digest", "A" * 64),
        ):
            cases.append(
                (
                    name,
                    self._payload(
                        _cap_closure_declaration(pre_fold_digest=value)
                    ),
                    "must be a lowercase 64-character hex",
                )
            )
        cases.append(
            (
                "pre_fold_digest equals the bound digest",
                self._payload(
                    _cap_closure_declaration(pre_fold_digest="0" * 64)
                ),
                "must differ",
            )
        )
        return cases

    def test_cap_closure_contract_rejects_malformed_declarations(self):
        """Every malformed declaration reports its specific problem, and
        every problem names ``extensions.cap_closure``."""
        for name, payload, fragment in self._rejection_cases():
            with self.subTest(case=name):
                result = self._validate(payload)
                self.assertFalse(result.ok, result.errors)
                self.assertTrue(
                    self._targeted(result, fragment), result.errors
                )

    def test_cap_closure_contract_enforces_minimum_round_floor(self):
        """The floor pins both directions: "2"/2 fails, "3"/3 passes."""
        below = self._payload(
            _cap_closure_declaration(round="2"), round_value=2
        )
        result = self._validate(below)
        self.assertFalse(result.ok, result.errors)
        self.assertTrue(
            self._targeted(result, "below CAP_CLOSURE_MIN_ROUND"),
            result.errors,
        )
        at = self._payload(
            _cap_closure_declaration(round="3"), round_value=3
        )
        result = self._validate(at)
        self.assertEqual([], result.errors)

    def test_cap_closure_contract_rejections_avoid_routed_substrings(self):
        """Every reported problem across all rejection arms avoids the
        step-3 routed substrings (``source_digest``, ``source_kind``,
        ``missing the required 'coverage' object``) and names
        ``extensions.cap_closure``, so the readiness error mapping can
        never route a declaration rejection into the wrong family. The
        arms include unknown keys named with the routed literals
        themselves (the producer-echo path: rejection messages are static
        templates plus filtered echoes and never repeat such text)."""
        collected = []
        for _name, payload, _fragment in self._rejection_cases():
            collected.extend(self._validate(payload).errors)
        versionless = self._payload(_cap_closure_declaration())
        del versionless["schema_version"]
        collected.extend(
            self._validate(versionless, schema_class="legacy").errors
        )
        self.assertTrue(collected)
        for error in collected:
            with self.subTest(error=error):
                self.assertIn("extensions.cap_closure", error)
                self.assertNotIn("source_digest", error)
                self.assertNotIn("source_kind", error)
                self.assertNotIn(
                    "missing the required 'coverage' object", error
                )

    def test_cap_closure_contract_accepts_int_typed_declaration_round(self):
        """Sidecar round ``"5"`` (string) with declaration round ``5``
        (integer): both sides normalize through ``str()``, the mirrored
        pairing of the string-declaration accept arm."""
        payload = self._payload(
            _cap_closure_declaration(round=5), round_value="5"
        )
        result = self._validate(payload)
        self.assertEqual([], result.errors)

    def test_cap_closure_contract_rejects_versionless_carrier(self):
        """A versionless legacy payload carrying ``extensions.cap_closure``
        fails closed at the version boundary (mirrors the sibling's
        schema-version-removed case)."""
        payload = self._payload(_cap_closure_declaration())
        del payload["schema_version"]
        result = self._validate(payload, schema_class="legacy")
        self.assertFalse(result.ok, result.errors)
        self.assertTrue(
            self._targeted(result, "version boundary"), result.errors
        )


class CapClosureReadinessTest(unittest.TestCase):
    """The readiness-gate acceptance of the cap-closure terminal shape.

    Fixture recipe (per the plan): full version-1 records adapted from
    ``vrs._version1_payload`` (``review_type``/``source_kind`` plan,
    ``verdict`` matching the arm, ``artifact_slug``/``round`` matching the
    fixture slug and round grammar, ``source_digest`` bound to the fixture
    plan bytes, findings mirrored into the review Markdown), with BOTH the
    sidecar ``date`` and the round filename's leading date below the
    structural fences so the gated probes stay exempt. Blocking rows in
    accept-derived arms carry a resolved ``fixed`` triage on both record
    surfaces. Guards (ordinary rounds, no-verdict-without-declaration,
    stale digest, conforming yes verdict) pin today's behavior; every
    other arm was RED before the gate probe existed (RED-first witness).
    """

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="cap-closure-fixture-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.plans = self.root / "plans"
        self.reviews = self.root / "reviews"
        self.plans.mkdir()
        self.reviews.mkdir()

    # -- fixture builders --------------------------------------------------

    def _plan_text(
        self,
        patterns=(CAP_CLOSURE_PATTERN,),
        *,
        omit_section=False,
        body=None,
        trailer=False,
        first_empty_second_body=None,
    ):
        parts = ["# Cap closure fixture plan", "", "Body."]
        if trailer:
            parts.extend(
                [
                    "",
                    "## Assumptions",
                    "",
                    "Decision points requiring a grill: none remain.",
                ]
            )
        if not omit_section:
            parts.extend(["", CAP_CLOSURE_SECTION, ""])
            if first_empty_second_body is not None:
                # First section stays empty; a later identical heading
                # carries the body (the first occurrence must govern).
                parts.extend(
                    ["", CAP_CLOSURE_SECTION, "", first_empty_second_body]
                )
            elif body is not None:
                parts.append(body)
            else:
                parts.extend(
                    f"- {pattern} (disposition: accepted)"
                    for pattern in patterns
                )
        return "\n".join(parts) + "\n"

    def _quote_only_plan_text(self):
        """The heading appears only inside a fenced block and as a ``###``
        heading; neither is a line-anchored level-2 heading."""
        return (
            "# Cap closure fixture plan\n\nBody.\n\n"
            "```markdown\n"
            f"{CAP_CLOSURE_SECTION}\n"
            f"- {CAP_CLOSURE_PATTERN} (disposition: accepted)\n"
            "```\n\n"
            f"### {CAP_CLOSURE_SECTION[3:]}\n\n"
            f"- {CAP_CLOSURE_PATTERN} (disposition: accepted)\n"
        )

    def _markdown(self, findings):
        """Review Markdown mirroring ``findings`` (id, severity, blocking,
        triage, and the ``- **Pattern**:`` bullet per finding)."""
        md = vrs._current_findings_markdown(findings, title=CAP_CLOSURE_SLUG)
        patterns = {
            row["id"]: row["pattern"]
            for row in findings
            if isinstance(row, dict) and "pattern" in row
        }
        if not patterns:
            return md
        out = []
        current = None
        for line in md.splitlines():
            out.append(line)
            header = re.match(r"#### F(\d+)\.", line)
            if header:
                current = int(header.group(1))
            elif line.startswith("- **Triage**:") and current in patterns:
                out.append(f"- **Pattern**: {patterns[current]}")
                current = None
        return "\n".join(out) + "\n"

    def _sidecar(
        self,
        digest_source_bytes,
        findings,
        declaration,
        *,
        verdict="no",
        round_value=CAP_CLOSURE_ROUND,
        date=CAP_CLOSURE_DATE,
        extensions=None,
    ):
        """Full version-1 sidecar adapted from ``vrs._version1_payload``."""
        payload = vrs._version1_payload()
        payload["review_type"] = "plan"
        payload["source_kind"] = "plan"
        payload["verdict"] = verdict
        payload["artifact_slug"] = CAP_CLOSURE_SLUG
        payload["round"] = round_value
        payload["date"] = date
        payload["source_digest"] = vrs.compute_source_digest(
            "plan", digest_source_bytes
        )
        payload["findings"] = findings
        payload["counts"]["staged_findings"] = len(findings)
        if extensions is not None:
            payload["extensions"] = extensions
        else:
            payload["extensions"] = {"cap_closure": declaration}
        return payload

    def _stage(
        self,
        plan_text,
        sidecar,
        markdown,
        *,
        date=CAP_CLOSURE_DATE,
        binary_plan_bytes=None,
    ):
        plan = self.plans / f"{date}-{CAP_CLOSURE_SLUG}.md"
        if binary_plan_bytes is not None:
            plan.write_bytes(binary_plan_bytes)
        else:
            plan.write_text(plan_text, encoding="utf-8")
        review = self.reviews / (
            f"{date}-plan-review-{CAP_CLOSURE_SLUG}-"
            f"{CAP_CLOSURE_ROUND_SUFFIX}.md"
        )
        review.write_text(markdown, encoding="utf-8")
        review.with_suffix(".stats.json").write_text(
            json.dumps(sidecar), encoding="utf-8"
        )
        return plan

    def _accept_fixture(
        self,
        *,
        verdict="no",
        patterns=(CAP_CLOSURE_PATTERN,),
        plan_text=None,
        declaration=None,
        date=CAP_CLOSURE_DATE,
    ):
        """The accept-arm fixture: one non-blocking triaged finding mirrored
        on both surfaces, a conforming declaration, and a residual section
        listing every staged pattern with an ``accepted`` disposition."""
        findings = [_cap_closure_finding()] if patterns else []
        if plan_text is None:
            plan_text = self._plan_text(patterns=patterns)
        if declaration is None:
            declaration = _cap_closure_declaration(residuals=len(patterns))
        sidecar = self._sidecar(
            plan_text.encode("utf-8"), findings, declaration,
            verdict=verdict, date=date,
        )
        return self._stage(
            plan_text, sidecar, self._markdown(findings), date=date
        )

    def _evaluate(self, plan):
        return plan_readiness.evaluate_readiness(plan, self.plans, self.reviews)

    # -- guards (pass today, must keep passing) ----------------------------

    def test_ordinary_rounds_unaffected_by_cap_closure_rule(self):
        """A normal ready=yes sidecar without any extensions object keeps
        today's outcome: the new rule does not over-block ordinary rounds."""
        plan, _review = plan_readiness._write_clean_state(
            self.plans, self.reviews
        )
        ok, reason = self._evaluate(plan)
        self.assertTrue(ok, reason)

    def test_gate_rejects_verdict_no_without_cap_closure(self):
        """verdict "no" with only ``extensions.convergence`` fails with
        today's verdict reason, unchanged; the reason discriminates the
        key name (an any-extensions-key gate would wrongly pass)."""
        plan_text = self._plan_text()
        findings = [_cap_closure_finding()]
        sidecar = self._sidecar(
            plan_text.encode("utf-8"),
            findings,
            None,
            verdict="no",
            extensions={"convergence": {"rounds": 3}},
        )
        plan = self._stage(plan_text, sidecar, self._markdown(findings))
        ok, reason = self._evaluate(plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("verdict field reports 'no'", reason)
        self.assertNotIn("cap closure", reason)

    def test_gate_rejects_stale_digest_under_cap_closure(self):
        """A sidecar whose ``source_digest`` still records the pre-fold
        bytes fails on the digest arm: the re-bind is load-bearing and the
        shared gate stays the single digest authority."""
        plan_text = self._plan_text()
        findings = [_cap_closure_finding()]
        stale_digest = _cap_closure_pre_fold_digest()
        declaration = _cap_closure_declaration(
            pre_fold_digest=vrs.compute_source_digest(
                "plan", CAP_CLOSURE_THIRD_BYTES
            )
        )
        sidecar = self._sidecar(
            CAP_CLOSURE_PRE_FOLD_BYTES, findings, declaration
        )
        self.assertEqual(stale_digest, sidecar["source_digest"])
        plan = self._stage(plan_text, sidecar, self._markdown(findings))
        ok, reason = self._evaluate(plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("is stale", reason)

    def test_gate_accepts_yes_verdict_sidecar_with_conforming_cap_closure(
        self,
    ):
        """The same fixture fully conforming under a yes verdict passes:
        the probe keys on declaration presence, not the verdict value."""
        plan = self._accept_fixture(verdict="yes")
        ok, reason = self._evaluate(plan)
        self.assertTrue(ok, reason)

    # -- new gate arms (RED before the probe existed) -----------------------

    def test_gate_accepts_cap_closure_terminal_shape(self):
        """verdict "no" with a conforming declaration passes: the sidecar
        round deliberately uses the paired-but-different type (sidecar the
        integer ``5``, declaration ``"5"``), proving string normalization
        is load-bearing."""
        plan = self._accept_fixture()
        ok, reason = self._evaluate(plan)
        self.assertTrue(ok, reason)

    def test_gate_rejects_cap_closure_without_plan_section(self):
        """Removing the section literal from the plan bytes fails naming
        the missing terminal state, never the verdict reason."""
        plan = self._accept_fixture(
            plan_text=self._plan_text(omit_section=True)
        )
        ok, reason = self._evaluate(plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("terminal state missing", reason)
        self.assertIn(CAP_CLOSURE_SECTION, reason)
        self.assertNotIn("verdict field reports", reason)

    def test_gate_rejects_cap_closure_heading_with_empty_body(self):
        """Heading present with an empty body under ``residuals: 1`` fails
        naming the missing-or-empty terminal state and the declared
        residual count; a ``###`` sub-heading body would count as body
        text, but there is none here."""
        plan = self._accept_fixture(plan_text=self._plan_text(body=""))
        ok, reason = self._evaluate(plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("missing or empty", reason)
        self.assertIn(CAP_CLOSURE_SECTION, reason)
        self.assertIn("claims 1 residual", reason)

    def test_gate_rejects_first_conforming_heading_governs(self):
        """An empty first section is never rescued by a non-empty body
        under a later identical conforming heading."""
        plan = self._accept_fixture(
            plan_text=self._plan_text(
                first_empty_second_body=(
                    f"- {CAP_CLOSURE_PATTERN} (disposition: accepted)"
                )
            ),
        )
        ok, reason = self._evaluate(plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("missing or empty", reason)
        self.assertIn("claims 1 residual", reason)

    def test_gate_rejects_cap_closure_under_reporting_staged_findings(self):
        """A body that does not list the staged patterns with dispositions
        fails with the dedicated under-reporting reason (``residuals: 0``
        with an empty body passes only when the round staged zero
        findings)."""
        plan = self._accept_fixture(
            plan_text=self._plan_text(body="No residual findings remain.")
        )
        ok, reason = self._evaluate(plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("under-reports", reason)
        self.assertIn(CAP_CLOSURE_PATTERN, reason)

    def test_gate_rejects_pattern_listed_without_disposition(self):
        """Listing every staged pattern but leaving one list entry without
        ``folded`` or ``accepted`` still under-reports: the disposition
        check is per pattern (same list entry as its pattern)."""
        plan_text = self._plan_text(
            body=(
                f"- {CAP_CLOSURE_PATTERN}\n"
                "Resolved outside the section."
            )
        )
        plan = self._accept_fixture(plan_text=plan_text)
        ok, reason = self._evaluate(plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("under-reports", reason)
        self.assertIn(CAP_CLOSURE_PATTERN, reason)

    def test_gate_rejects_cap_closure_disposition_outside_accepted_vocabulary(
        self,
    ):
        """A ``disposition: deferred`` marker and a bare pattern both
        under-report: the pinned disposition enum is ``folded``/
        ``accepted``, and words outside it are rejected while parsing."""
        plan_text = self._plan_text(
            body=(
                f"- {CAP_CLOSURE_PATTERN} (disposition: deferred)\n"
                f"- {CAP_CLOSURE_BLOCK_PATTERN}"
            )
        )
        findings = [
            _cap_closure_finding(pattern=CAP_CLOSURE_PATTERN),
            _cap_closure_finding(
                id=2, pattern=CAP_CLOSURE_BLOCK_PATTERN
            ),
        ]
        sidecar = self._sidecar(
            plan_text.encode("utf-8"),
            findings,
            _cap_closure_declaration(residuals=0),
        )
        plan = self._stage(plan_text, sidecar, self._markdown(findings))
        ok, reason = self._evaluate(plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("under-reports", reason)
        self.assertIn(CAP_CLOSURE_PATTERN, reason)

    def test_gate_rejects_residuals_count_mismatch(self):
        """The declared ``residuals`` count is tied to the accepted-entry
        tally the gate parses: 0 with one ``accepted`` entry fails, and 2
        with three ``accepted`` entries fails."""
        zero_plan = self._accept_fixture(
            declaration=_cap_closure_declaration(residuals=0)
        )
        ok, reason = self._evaluate(zero_plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("residuals count mismatch", reason)
        self.assertIn("claims 0 accepted", reason)
        self.assertIn("carries 1", reason)
        three_body = "\n".join(
            [
                f"- {CAP_CLOSURE_PATTERN} (disposition: accepted)",
                "- quality#extra-one (disposition: accepted)",
                "- quality#extra-two (disposition: accepted)",
            ]
        )
        two_plan = self._accept_fixture(
            plan_text=self._plan_text(body=three_body),
            declaration=_cap_closure_declaration(residuals=2),
        )
        ok, reason = self._evaluate(two_plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("residuals count mismatch", reason)
        self.assertIn("claims 2 accepted", reason)
        self.assertIn("carries 3", reason)

    def test_gate_accepts_cap_closure_with_zero_residuals_and_empty_body(
        self,
    ):
        """A genuinely finding-free round with ``residuals: 0`` and an
        empty section body passes."""
        plan = self._accept_fixture(
            patterns=(),
            plan_text=self._plan_text(patterns=(), body=""),
            declaration=_cap_closure_declaration(residuals=0),
        )
        ok, reason = self._evaluate(plan)
        self.assertTrue(ok, reason)

    def test_gate_rejects_cap_closure_only_as_quoted_or_misleveled_mention(
        self,
    ):
        """A fenced copy and a ``###`` heading never satisfy the conjunct:
        the gate still fails naming the missing terminal state."""
        plan = self._accept_fixture(
            plan_text=self._quote_only_plan_text()
        )
        ok, reason = self._evaluate(plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("terminal state missing", reason)
        self.assertIn(CAP_CLOSURE_SECTION, reason)

    def test_gate_rejects_cap_closure_with_unresolved_blocking(self):
        """One blocking finding left unresolved (mirrored on both record
        surfaces with the version-1 finding shape) fails on the blocking
        consistency arm, unchanged."""
        findings = [
            _cap_closure_finding(
                blocking=True,
                severity="High",
                triage="pending",
                pattern=CAP_CLOSURE_BLOCK_PATTERN,
            )
        ]
        plan_text = self._plan_text(patterns=(CAP_CLOSURE_BLOCK_PATTERN,))
        sidecar = self._sidecar(
            plan_text.encode("utf-8"),
            findings,
            _cap_closure_declaration(),
        )
        plan = self._stage(plan_text, sidecar, self._markdown(findings))
        ok, reason = self._evaluate(plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("unresolved blocking findings", reason)

    def test_gate_rejects_cap_closure_with_pending_triage(self):
        """Flipping one blocking finding's triage back to ``pending`` on
        both record surfaces fails at the ``is_review_ready`` reason: the
        composite requires the folded findings' triage resolved on both
        surfaces, not just in the residual section."""
        findings = [
            _cap_closure_finding(blocking=True, severity="High",
                                 triage="pending")
        ]
        plan_text = self._plan_text()
        sidecar = self._sidecar(
            plan_text.encode("utf-8"),
            findings,
            _cap_closure_declaration(),
        )
        plan = self._stage(plan_text, sidecar, self._markdown(findings))
        ok, reason = self._evaluate(plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("unresolved blocking findings", reason)

    def test_gate_rejects_malformed_cap_closure_declaration(self):
        """Non-conforming declarations fail with the step-3 mapped reason;
        each full mapped reason names ``extensions.cap_closure`` and lands
        in the malformed-sidecar family, never the stale-digest family."""
        differ_declaration = _cap_closure_declaration(pre_fold_digest=None)
        plan_text = self._plan_text()
        differ_declaration["pre_fold_digest"] = vrs.compute_source_digest(
            "plan", plan_text.encode("utf-8")
        )
        cases = (
            (
                "wrong plan_section literal",
                _cap_closure_declaration(plan_section="## Wrong section"),
                _MALFORMED_SIDECAR_PREFIX
                + (
                    "extensions.cap_closure 'plan_section' must be exactly "
                    "'## Residual findings (cap closure)'; "
                    "got '## Wrong section'"
                ),
            ),
            (
                "round mismatching the sidecar",
                _cap_closure_declaration(round="6"),
                _MALFORMED_SIDECAR_PREFIX
                + (
                    "extensions.cap_closure 'round' must equal the sidecar "
                    "round after string normalization (sidecar round 5 vs "
                    "declaration round '6')"
                ),
            ),
            (
                "unknown extension key",
                _cap_closure_declaration(scheme="extra"),
                _MALFORMED_SIDECAR_PREFIX
                + (
                    "extensions.cap_closure accepts only the keys "
                    "plan_section, round, residuals, pre_fold_digest"
                ),
            ),
            (
                "pre_fold_digest equal to the bound digest",
                differ_declaration,
                _MALFORMED_SIDECAR_PREFIX
                + (
                    "extensions.cap_closure 'pre_fold_digest' must differ "
                    "from the digest bound to the reviewed bytes: it "
                    "records the pre-fold state, not the folded state"
                ),
            ),
        )
        for name, declaration, expected in cases:
            with self.subTest(case=name):
                findings = [_cap_closure_finding()]
                sidecar = self._sidecar(
                    plan_text.encode("utf-8"), findings, declaration
                )
                plan = self._stage(
                    plan_text, sidecar, self._markdown(findings)
                )
                ok, reason = self._evaluate(plan)
                self.assertFalse(ok, reason is None and "unexpected pass")
                self.assertEqual(expected, reason)

    def test_gate_rejects_yes_verdict_sidecar_with_violating_cap_closure(
        self,
    ):
        """A yes-verdict sidecar whose residual section body is emptied
        under a nonzero ``residuals`` fails with the dedicated
        terminal-state reason, never a pass via the yes verdict."""
        plan = self._accept_fixture(
            verdict="yes",
            plan_text=self._plan_text(body=""),
            declaration=_cap_closure_declaration(residuals=2),
        )
        ok, reason = self._evaluate(plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("missing or empty", reason)
        self.assertIn("claims 2 residual", reason)

    def test_gate_accepts_cap_closure_on_modern_plan_with_structural_gates(
        self,
    ):
        """On/after ``DECISION_MARKER_MIN_DATE`` the trailer gate runs
        after a satisfied cap-closure conjunct: the conforming fixture
        passes, and removing the trailer line yields the trailer reason
        (fall-through, not early return)."""
        plan_text = self._plan_text(trailer=True)
        plan = self._accept_fixture(
            plan_text=plan_text, date=CAP_CLOSURE_MODERN_DATE
        )
        ok, reason = self._evaluate(plan)
        self.assertTrue(ok, reason)
        twin_text = plan_text.replace(
            "Decision points requiring a grill: none remain.\n", ""
        )
        twin = self._accept_fixture(
            plan_text=twin_text, date=CAP_CLOSURE_MODERN_DATE
        )
        ok, reason = self._evaluate(twin)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("decision-points trailer", reason)

    def test_gate_names_undecodable_plan_bytes_under_cap_closure(self):
        """Undecodable plan bytes with a matching sidecar return the named
        cannot-read-plan-bytes reason instead of raising: the
        declaration-gated decode keeps today's failure shape for
        declaration-free rounds, and the undecodable-bytes reason fires
        only when the declaration routes the probe at the bytes."""
        plan_bytes = b"\xff\xfe\x00 undecodable cap closure plan"
        findings = [_cap_closure_finding()]
        sidecar = self._sidecar(
            plan_bytes, findings, _cap_closure_declaration()
        )
        plan = self._stage(
            None,
            sidecar,
            self._markdown(findings),
            binary_plan_bytes=plan_bytes,
        )
        ok, reason = self._evaluate(plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("cannot read plan bytes", reason)


if __name__ == "__main__":
    unittest.main()
