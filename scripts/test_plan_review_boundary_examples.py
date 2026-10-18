"""Focused regression for the plan review readiness boundary.

Plan of record: docs/history/plans/2026-10-07-plan-detail-boundary.md
(Task 2). The review boundary separates behavior readiness from
implementation inventory: a behavior-complete plan is review-ready
without test identities, supporting path inventories, fixture details,
schema resources, or exact task commands, and a plan without an
observable behavior or safety witness stays blocked. The paired
judgments live in the readiness boundary examples of
agents/skills/review-plan/SKILL.md (the BOUNDARY-READY-FIXTURE and
BOUNDARY-BLOCKED-FIXTURE blocks); this module parses those documented
fixtures and proves both outcomes against the boundary rules encoded
here, then proves the structural readiness validator
(scripts/plan_readiness.py, pre-round mode) passes a witnessed plan
that carries no test identities and is invariant to their addition.

The structural validator stays path-structural by design (the plan's
Design Invariants): this test must never grow it into a semantic
review engine and asserts no new refusal class.

Run from the repository root:

    PYTHONPATH=scripts python3 -m unittest scripts.test_plan_review_boundary_examples

or from scripts/:

    python3 -m unittest test_plan_review_boundary_examples -v

Hermetic: tempdirs only, no network, no writes into the repository.
"""

import contextlib
import io
import re
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent
REVIEW_PLAN_SKILL = REPO_ROOT / "agents" / "skills" / "review-plan" / "SKILL.md"
PLANS_SKILL = REPO_ROOT / "agents" / "skills" / "plans" / "SKILL.md"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import plan_readiness  # noqa: E402

READY_MARKER = "BOUNDARY-READY-FIXTURE"
BLOCKED_MARKER = "BOUNDARY-BLOCKED-FIXTURE"

# The boundary rules as documented, encoded. A primary class anchor is
# a production class name plus source path in the Primary class
# anchors: block (the plans template's shape). An observable witness is
# a scenario-and-outcome claim in the given/expects form on an owned
# checklist item. Test identities (backticked `Class#method` tokens)
# are execution inventory: they never count as witnesses and never
# contribute to the verdict in either direction.
_ANCHOR_RE = re.compile(
    r"^- `([A-Za-z_][A-Za-z0-9_]*)` in `([^`]+)`", re.MULTILINE
)
_TEST_IDENTITY_RE = re.compile(
    r"`[A-Za-z_][A-Za-z0-9_]*(?:Test|Tests|IT|ITs)#[A-Za-z0-9_]+`"
)
_WITNESS_RE = re.compile(r"given [^,\n]+, expects ")
_CHECKLIST_ITEM_RE = re.compile(r"^- \[[ xX]\] (.*)$", re.MULTILINE)


def extract_fixture(skill_text: str, marker: str) -> str:
    """Return one fenced boundary fixture block by its marker line."""
    lines = skill_text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() != marker:
            continue
        opener = index
        while opener > 0 and not lines[opener].startswith("```"):
            opener -= 1
        closer = index
        while closer < len(lines) - 1 and lines[closer].strip() != "```":
            closer += 1
        if not lines[opener].startswith("```") or lines[closer].strip() != "```":
            raise AssertionError(
                f"boundary fixture {marker!r} is not inside a closed fence"
            )
        return "\n".join(lines[opener + 1 : closer])
    raise AssertionError(
        f"boundary fixture marker {marker!r} not found in {REVIEW_PLAN_SKILL}"
    )


def boundary_verdict(text: str) -> str:
    """The documented review boundary, encoded.

    Ready iff the excerpt names at least one primary production class
    with its source path AND carries at least one observable behavior
    or safety witness on an owned checklist item. Blocked otherwise.
    Guessed inventory (test identities, supporting paths, Evidence
    blocks, commands) is inert: it never unblocks a witnessless plan
    and its absence never blocks a witnessed one.
    """
    if not _ANCHOR_RE.search(text):
        return "blocked"
    for item in _CHECKLIST_ITEM_RE.findall(text):
        if _TEST_IDENTITY_RE.search(item):
            continue
        if _WITNESS_RE.search(item):
            return "ready"
    return "blocked"


def _boundary_fixture_plan(extra_task_lines: str = "") -> str:
    """A structurally complete minimal plan embedding the ready shape.

    Observable witnesses and a primary class anchor, no test
    identities. ``extra_task_lines`` appends checklist lines to the
    task (used by the twin arm that adds guessed test identities).
    """
    return (
        "# Plan: Boundary fixture\n"
        "\n"
        "Driving force: efficiency\n"
        "Plan review record: none\n"
        "\n"
        "## Terms\n"
        "\n"
        "none.\n"
        "\n"
        "## Why\n"
        "\n"
        "The digest notification is lost on a transient send failure.\n"
        "\n"
        "## Gist & Examples\n"
        "\n"
        "TLDR: one retry for the digest notification, for efficiency.\n"
        "\n"
        "Before: a failed send loses the notification.\n"
        "After: one retry; a still-failing delivery is recorded as failed.\n"
        "\n"
        "## Outcome\n"
        "\n"
        "Digest notifications survive one transient send failure.\n"
        "\n"
        "- A failed send retries once and records the outcome.\n"
        "\n"
        "Gate delta: none.\n"
        "\n"
        "## Assumptions\n"
        "\n"
        "- assume the retry budget stays at one; basis: current delivery policy.\n"
        "Decision points requiring a grill: none remain.\n"
        "\n"
        "## Review Scope\n"
        "\n"
        "**Explicit must-fix:** findings on these paths are always in scope "
        "(review and fix if valid):\n"
        "\n"
        "**Production code:**\n"
        "- `scripts/notify.py`\n"
        "\n"
        "**Plan-related extension:** implementation and review may change files "
        "not listed above when causally related to a plan task.\n"
        "\n"
        "## Validation Commands\n"
        "\n"
        "```bash\n"
        "python3 -m compileall scripts/notify.py\n"
        "```\n"
        "\n"
        "### Task 1: Retry the digest notification once\n"
        "\n"
        "Files:\n"
        "- `scripts/notify.py`\n"
        "\n"
        "Primary class anchors:\n"
        "- `NotificationRetry` in `scripts/notify.py`\n"
        "\n"
        "- [ ] `NotificationRetry` redelivers once after a failed send: given "
        "a first send that fails and a second that succeeds, expects exactly "
        "one notification delivered and the delivery recorded as retried. "
        "[class: IMPLEMENTATION_REQUIRED]\n"
        "- [ ] A retry never duplicates a delivered notification: given an "
        "already-delivered receipt, expects the retry pass to be a no-op. "
        "[class: IMPLEMENTATION_REQUIRED]\n"
        f"{extra_task_lines}"
        "- [ ] Commit: `notify: retry the digest notification once` "
        "[class: IMPLEMENTATION_REQUIRED]\n"
    )


_TEST_IDENTITY_TASK_LINE = (
    "- [ ] `NotificationRetryTest#test_retry_no_duplicate_delivery`; given "
    "an already-delivered receipt, expects a no-op retry pass. "
    "[class: REPOSITORY_TEST]\n"
)


class PlanReviewBoundaryExamplesTest(unittest.TestCase):
    """The paired documented judgments and their encoded rule."""

    @classmethod
    def setUpClass(cls):
        cls.skill_text = REVIEW_PLAN_SKILL.read_text(encoding="utf-8")
        cls.ready = extract_fixture(cls.skill_text, READY_MARKER)
        cls.blocked = extract_fixture(cls.skill_text, BLOCKED_MARKER)

    def test_paired_fixtures_present_with_expected_judgments(self):
        self.assertIn("Judgment: ready", self.ready)
        self.assertIn("Judgment: blocked", self.blocked)

    def test_ready_example_is_ready_without_test_identities(self):
        self.assertEqual(boundary_verdict(self.ready), "ready")
        self.assertTrue(_ANCHOR_RE.search(self.ready), "anchor missing")
        self.assertTrue(_WITNESS_RE.search(self.ready), "witness missing")
        self.assertIsNone(
            _TEST_IDENTITY_RE.search(self.ready),
            "the ready example must carry no guessed test identities",
        )
        self.assertNotIn("Evidence:", self.ready)
        self.assertNotIn("test-command", self.ready)

    def test_blocked_example_is_blocked_without_witness(self):
        self.assertEqual(boundary_verdict(self.blocked), "blocked")
        # It names an anchor and even a guessed supporting test path,
        # and is still blocked: the witness is what carries readiness.
        self.assertTrue(_ANCHOR_RE.search(self.blocked), "anchor missing")
        self.assertIn("tests/test_ingest.py", self.blocked)
        for item in _CHECKLIST_ITEM_RE.findall(self.blocked):
            if item.startswith("Commit:"):
                continue
            self.assertIsNone(
                _WITNESS_RE.search(item),
                f"blocked example item carries a witness: {item!r}",
            )

    def test_test_identities_never_unblock_a_witnessless_plan(self):
        with_identity = self.blocked + (
            "\n- [ ] `IngestSchedulerTest#test_harden`; given any ingest "
            "input, expects the hardened output. [class: REPOSITORY_TEST]\n"
        )
        self.assertEqual(boundary_verdict(with_identity), "blocked")
        with_evidence = self.blocked + (
            "\nEvidence:\n"
            "- `python3 -m unittest tests.test_ingest -v`; covers the "
            "hardening criterion\n"
        )
        self.assertEqual(boundary_verdict(with_evidence), "blocked")

    def test_guessed_supporting_paths_are_not_witnesses(self):
        without_test_path = self.blocked.replace(
            "- `tests/test_ingest.py`\n", ""
        )
        self.assertEqual(
            boundary_verdict(without_test_path),
            "blocked",
            "dropping the guessed test path must not unblock a "
            "witnessless plan",
        )
        stripped = "\n".join(
            line
            for line in self.ready.splitlines()
            if not _WITNESS_RE.search(line)
        )
        self.assertEqual(
            boundary_verdict(stripped),
            "blocked",
            "removing the observable witnesses must block the ready "
            "example: the witness, not the inventory, carries the verdict",
        )

    def test_plans_skill_carries_the_boundary_rules(self):
        plans_text = PLANS_SKILL.read_text(encoding="utf-8")
        self.assertIn("No guessed implementation inventory", plans_text)
        self.assertIn(
            "review-plan's readiness boundary examples", plans_text
        )
        self.assertIn("Primary class anchors:", plans_text)


class StructuralValidatorBoundaryTest(unittest.TestCase):
    """The structural readiness validator stays inventory-blind.

    Pre-round mode (the structural-only authoring gate) must pass a
    behavior-witnessed plan with no test identities, and adding guessed
    test identities must change nothing it reports.
    """

    @staticmethod
    def _run_pre_round(plan_path: Path, plans_dir: Path):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = plan_readiness.run_pre_round(plan_path, plans_dir)
        return code, out.getvalue(), err.getvalue()

    def test_validator_passes_witnessed_plan_without_test_identities(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plans_dir = root / "plans"
            plans_dir.mkdir()
            (root / "scripts").mkdir()
            (root / "scripts" / "notify.py").write_text(
                "class NotificationRetry:\n    pass\n", encoding="utf-8"
            )
            plan_path = plans_dir / "2099-01-01-boundary-fixture.md"
            plan_path.write_text(_boundary_fixture_plan(), encoding="utf-8")
            code, out, err = self._run_pre_round(plan_path, plans_dir)
            self.assertEqual(code, 0, f"pre-round failed: {err}")
            self.assertIn("readiness PRE-ROUND OK", out)

    def test_validator_output_is_invariant_to_added_test_identities(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plans_dir = root / "plans"
            plans_dir.mkdir()
            (root / "scripts").mkdir()
            (root / "scripts" / "notify.py").write_text(
                "class NotificationRetry:\n    pass\n", encoding="utf-8"
            )
            base = plans_dir / "2099-01-01-boundary-fixture.md"
            base.write_text(_boundary_fixture_plan(), encoding="utf-8")
            twin = plans_dir / "2099-01-01-boundary-fixture-twin.md"
            twin.write_text(
                _boundary_fixture_plan(_TEST_IDENTITY_TASK_LINE),
                encoding="utf-8",
            )
            base_run = self._run_pre_round(base, plans_dir)
            twin_run = self._run_pre_round(twin, plans_dir)
            self.assertEqual(base_run[0], 0, base_run[2])
            self.assertEqual(twin_run[0], 0, twin_run[2])
            self.assertEqual(base_run[1], twin_run[1])
            self.assertEqual(base_run[2], twin_run[2])


if __name__ == "__main__":
    unittest.main()
