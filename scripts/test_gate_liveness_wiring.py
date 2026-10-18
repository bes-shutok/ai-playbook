"""Pins the guard liveness wiring contract.

Declaration group: fixed-string spans the three duty surfaces must carry
(the friction-audit read side, the plans skill's Gate delta ledger citation
bullet, and review-plan's Declaration findings citation audit), plus the
preserved anchors the edits must not disturb. Behavior group: the ledger's
`show` subcommand run against the repository's real ledger.
"""

import os
import subprocess
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FRICTION_AUDIT = os.path.join(
    REPO_ROOT, "docs", "maintenance", "recurring-tasks", "friction-audit.md"
)
PLANS_SKILL = os.path.join(REPO_ROOT, "agents", "skills", "plans", "SKILL.md")
REVIEW_PLAN_SKILL = os.path.join(
    REPO_ROOT, "agents", "skills", "review-plan", "SKILL.md"
)
LEDGER_SCRIPT = os.path.join(REPO_ROOT, "scripts", "gate_liveness_ledger.py")


def read(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


class LivenessWiringDeclarationTest(unittest.TestCase):
    def test_friction_audit_read_side_declared(self):
        body = read(FRICTION_AUDIT)
        for span in (
            "Guard liveness read-side",
            "gate_liveness_ledger.py show",
            "removal-or-narrow candidate",
            "when the observation window closes",
        ):
            self.assertIn(span, body)

    def test_gate_delta_citation_declared(self):
        body = read(PLANS_SKILL)
        for span in (
            "Gate delta ledger citation",
            "gate_liveness_ledger.py show",
        ):
            self.assertIn(span, body)

    def test_review_plan_audit_declared(self):
        body = read(REVIEW_PLAN_SKILL)
        for span in (
            "cites no ledger ratio",
            "the plans skill's Gate delta ledger citation bullet",
        ):
            self.assertIn(span, body)

    def test_preserved_anchors_stay_pinned(self):
        friction_audit = read(FRICTION_AUDIT)
        self.assertIn("Filing rule", friction_audit)
        self.assertIn("Caps", friction_audit)
        self.assertIn("scope_classification_problem", read(PLANS_SKILL))
        self.assertIn("Declaration findings", read(REVIEW_PLAN_SKILL))


class LivenessWiringBehaviorTest(unittest.TestCase):
    def test_ledger_show_prints_stack_ratio(self):
        proc = subprocess.run(
            ["python3", LEDGER_SCRIPT, "show"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0)
        output = proc.stdout
        lines = [line for line in output.splitlines() if line.strip()]
        self.assertTrue(lines)
        self.assertEqual(lines[-1].strip(), "OUTCOME: pass")
        self.assertIn("catches=", output)
        self.assertIn("incidents=", output)
        self.assertIn("ratio=", output)


if __name__ == "__main__":
    unittest.main()
