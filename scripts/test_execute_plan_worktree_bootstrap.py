#!/usr/bin/env python3
"""Smoke check for the execute-plan Transfer-in implementation recipe.

Origin completion evidence for the worktree-gitignored-bootstrap gap: a
linked worktree (its ``.git`` is a file) lacks the gitignored inputs the
Step 0.5 readiness gate resolves - the facts file, the certified reviews
directory, and the tmp directory - and the execute-plan skill's
Worktree-first standard carries the Transfer-in implementation for exactly
that. This suite proves the recipe is load-bearing end to end:

1. The FIRST fenced bash block after the "Transfer-in implementation (how
   step 2 runs)" lead-in in ``agents/skills/execute-plan/SKILL.md`` is
   extracted at test runtime (so skill-text drift fails the test) and
   executed VERBATIM in a linked worktree of a synthetic primary repo
   fixture. A second fenced block (the transfer-out-and-deletion migration
   recipe) follows in the same region and must not be picked, so the
   extractor's pick is asserted against that block's distinctive literals.
2. After the recipe: the facts file and the review sidecar pair are
   present in the worktree, the run's tmp directory is created empty (the
   canonical recipe mkdirs it; per-run scratch does not transfer in), and
   the plan readiness validator (``scripts/plan_readiness.py`` of the repo
   carrying this test, resolved relative to ``__file__``) run from the
   worktree on the fixture plan exits 0.
3. Negative control: the same fixture's worktree WITHOUT the recipe makes
   the validator exit non-zero with an environment failure (facts or
   reviews missing), proving the recipe is load-bearing (guard, not RED).

Fixture derivation notes (measured against the validators, not guessed):
the sidecar is a COMPLETE version-1 record because the required top-level
fields are not date-fenced, while the fixture's 2026-01-01 date (mirrored
by the review filename's leading date) exempts it from the freshness
(2026-09-09), coverage (2026-09-16), and record-kind (2026-09-20) fences;
``source_kind`` is ``"plan"`` (enforced unconditionally for the latest
round) and ``source_digest`` is the fixture plan's SHA-256. The sidecar
sits beside the review Markdown under ``stats_sidecar_path`` (the
``.stats.json`` suffix replaces ``.md``). The facts file and the reviews
pair stay gitignored and UNTRACKED in the primary (mirroring the real
repository, where ``git ls-files docs/reviews`` is empty), so a fresh
linked worktree genuinely lacks them and the negative control holds.

Run: ``python3 scripts/test_execute_plan_worktree_bootstrap.py`` from the
repository root (or anywhere; every path resolves relative to this file).
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_PATH = REPO_ROOT / "agents" / "skills" / "execute-plan" / "SKILL.md"
READINESS_VALIDATOR = REPO_ROOT / "scripts" / "plan_readiness.py"

BOOTSTRAP_LEAD_IN = "Transfer-in implementation (how step 2 runs)"
# r1 F8: a second fenced bash block (the transfer-out-and-deletion migration
# recipe) follows the transfer-in recipe in the same region; these literals
# belong to that block and must never appear in the extracted recipe. (r3: the
# former "{reviews_dir}" marker was dropped; the migration fence never carries
# it, so it could not discriminate the two blocks.)
CLOSEOUT_BLOCK_MARKERS = ("CLOSEOUT_SCRIPT", "{tmp_dir}")

PLAN_REL = "docs/history/plans/2026-01-01-fixture-plan.md"
PLAN_DATE = "2026-01-01"
SLUG = "fixture-plan"
REVIEW_MD_NAME = f"{PLAN_DATE}-plan-review-{SLUG}-r1.md"
REVIEW_SIDECAR_NAME = f"{PLAN_DATE}-plan-review-{SLUG}-r1.stats.json"

GITIGNORE_BODY = "/.ai-playbook/\n/docs/reviews\n/docs/tmp/\n"

# The TOML keys the readiness gate and the bootstrap recipe resolve, with
# the shapes copied from the real repository's .ai-playbook/facts.md.
FACTS_BODY = """```toml
plans_dir = "docs/history/plans/"
plans_completed_dir = "docs/history/plans/completed/"
backlog_dir = "docs/history/backlog/"
backlog_completed_dir = "docs/history/backlog/completed/"
reviews_dir = "docs/reviews/"
tmp_dir = "docs/tmp/"
facts_path = ".ai-playbook/facts.md"
doc_registry_rel = "docs/maintenance/document-registry.md"
bootstrap_version = "1"
```
"""

FIXTURE_PLAN = """# Plan: Fixture plan for the worktree bootstrap smoke check

## Terms

- **Fixture**: synthetic plan bytes with no executable content.

## Assumptions

- assume the fixture plan needs no repository context; basis: synthetic fixture.

Decision points requiring a grill: none remain.

## Gist & Examples

A synthetic minimal plan whose only purpose is to exercise the worktree
bootstrap smoke fixture. Before: no fixture exists. After: the fixture
pair validates clean through the readiness gate from a linked worktree.

## Evaluation Criteria

- the fixture pair passes the shared readiness gate (exit 0).

## Review Scope

**Production code:**
- none (synthetic fixture).

**Out of scope; reject unless plan-related:**
- everything (the fixture is synthetic).

## Validation Commands

```bash
python3 scripts/plan_readiness.py docs/history/plans/2026-01-01-fixture-plan.md
```
"""

# Hierarchy-conformant review Markdown: Metadata, Review Statistics with
# the Panel/Counts/Deduplication/Discarded/Calibration/Triage subsections,
# the four severity groups (required, in order, by the shared gate's
# Markdown severity-group check), and a Summary verdict line.
FIXTURE_REVIEW_TEMPLATE = """# Plan Review: Fixture plan for the worktree bootstrap smoke check

## Metadata
- Type: Plan Review
- Date: {plan_date}
- URL or Artifact: {plan_rel}
- Round: r1
- Panel mode: focused
- Source digest: {digest}
- Findings: 0
- Status: CLEAN

## Review Statistics

### Panel
| Worker | Lenses | Parent worker | Status | Raw | Solo | Echo | Relaunch |
|--------|--------|---------------|--------|-----|------|------|----------|
| solo | quality | none | complete | 0 | 0 | 0 | no |

Focused single-worker round: the fixture plan is a synthetic minimal pair, so
one solo worker with the quality lens ran; no descendant launches.

### Counts
- Workers launched: 1
- Workers skipped: 0
- Raw findings (all workers): 0
- Staged findings: 0
- Discarded during synthesis: 0

### Deduplication groups

None.

### Discarded findings

None.

### Severity calibration

None.

### Triage outcomes
| Worker | Lens | Staged | Fixed | Dropped | Deferred | Pending |
|--------|------|--------|-------|---------|----------|---------|
| solo | quality | 0 | 0 | 0 | 0 | 0 |

No staged findings, so every triage outcome count is zero.

### Soften watchlist

None.

## Findings

### Critical

None.

### High

None.

### Medium

None.

### Low

None.

## Summary

Verdict: ready=yes
"""


def fixture_sidecar(digest: str) -> dict:
    """COMPLETE version-1 sidecar for the fixture plan.

    Every required version-1 top-level field is present (they are not
    date-fenced); the freshness/coverage/record-kind fences are exempt at
    the 2026-01-01 fixture date, so the extended fields, ``coverage``,
    and ``record_kind`` are lawfully omitted. ``source_kind`` is ``"plan"``
    (the readiness gate enforces the kind unconditionally) and
    ``source_digest`` is the fixture plan's SHA-256.
    """
    return {
        "schema_version": 1,
        "review_type": "Plan Review",
        "date": PLAN_DATE,
        "artifact_slug": SLUG,
        "round": "r1",
        "panel_mode": "focused",
        "selection_reason": (
            "focused single-worker round over a synthetic fixture plan"
        ),
        "source_kind": "plan",
        "source_digest": digest,
        "escalation_reason": None,
        "counts": {
            "workers_launched": 1,
            "workers_skipped": 0,
            "raw_findings": 0,
            "staged_findings": 0,
            "discarded": 0,
        },
        "panel": [
            {
                "worker": "solo",
                "lenses": ["quality"],
                "parent_worker": None,
                "descendant_launches": [],
                "status": "complete",
                "raw": 0,
                "solo": 0,
                "echo": 0,
                "relaunch": False,
            }
        ],
        "deduplication_groups": [],
        "discarded": [],
        "severity_calibration": [],
        "triage_outcomes": [],
        "findings": [],
        "overflow": [],
        "soften_watchlist": [],
        "verdict": "yes",
    }


def extract_bootstrap_recipe(skill_text: str) -> str:
    """Extract the FIRST fenced bash block after the bootstrap lead-in.

    The lead-in is a bold paragraph, not a heading, and two fenced bash
    blocks follow it in the same region (the transfer-in recipe, then the
    transfer-out-and-deletion migration recipe); this picker takes the
    first and the test asserts the pick against the second block's
    distinctive literals.
    """
    lead_at = skill_text.find(BOOTSTRAP_LEAD_IN)
    if lead_at < 0:
        raise AssertionError(
            f"bootstrap lead-in {BOOTSTRAP_LEAD_IN!r} not found in {SKILL_PATH.name}"
        )
    opener_at = skill_text.find("```bash", lead_at)
    if opener_at < 0:
        raise AssertionError(
            "no fenced bash block after the bootstrap lead-in in "
            f"{SKILL_PATH.name}"
        )
    body_start = skill_text.index("\n", opener_at) + 1
    body_end = skill_text.index("\n```", body_start)
    return skill_text[body_start:body_end]


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        ["git", *args], cwd=str(repo), capture_output=True, text=True
    )
    if proc.returncode != 0:
        raise AssertionError(
            f"git {' '.join(args)} failed (rc {proc.returncode}): {proc.stderr}"
        )
    return proc


def build_fixture_repo(primary: Path) -> None:
    """Build the synthetic primary repo fixture in ``primary``.

    The initial commit carries the fixture plan and the .gitignore; the
    facts file and the reviews sidecar pair stay gitignored and untracked
    (as in the real repository), so a linked worktree of this fixture
    starts without them and the bootstrap recipe has something to fix.
    """
    primary.mkdir(parents=True)
    # The primary's branch name is irrelevant to every assertion below, so a
    # pre-2.28 git without --initial-branch falls back to the default init.
    if subprocess.run(
        ["git", "init", "--initial-branch=main"],
        cwd=str(primary),
        capture_output=True,
        text=True,
    ).returncode != 0:
        _git(primary, "init")
    _git(primary, "config", "user.email", "fixture@example.com")
    _git(primary, "config", "user.name", "Fixture")
    _git(primary, "config", "commit.gpgsign", "false")

    (primary / ".gitignore").write_text(GITIGNORE_BODY, encoding="utf-8")

    facts_dir = primary / ".ai-playbook"
    facts_dir.mkdir(parents=True)
    (facts_dir / "facts.md").write_text(FACTS_BODY, encoding="utf-8")

    plan_path = primary / PLAN_REL
    plan_path.parent.mkdir(parents=True)
    plan_path.write_text(FIXTURE_PLAN, encoding="utf-8")
    digest = hashlib.sha256(plan_path.read_bytes()).hexdigest()

    reviews_dir = primary / "docs" / "reviews"
    reviews_dir.mkdir(parents=True)
    (reviews_dir / REVIEW_MD_NAME).write_text(
        FIXTURE_REVIEW_TEMPLATE.format(
            plan_date=PLAN_DATE, plan_rel=PLAN_REL, digest=digest
        ),
        encoding="utf-8",
    )
    (reviews_dir / REVIEW_SIDECAR_NAME).write_text(
        json.dumps(fixture_sidecar(digest), indent=2) + "\n",
        encoding="utf-8",
    )

    _git(primary, "add", ".gitignore", PLAN_REL)
    _git(primary, "commit", "-m", "fixture")


def add_worktree(primary: Path, path: Path, branch: str) -> Path:
    _git(primary, "worktree", "add", str(path), "-b", branch)
    return path


def run_readiness_validator(worktree: Path) -> subprocess.CompletedProcess:
    """Run the repo's plan readiness validator from ``worktree`` on the
    fixture plan, with ``PLAN_READINESS_VALIDATOR`` set the way the
    execute-plan Step 0.5 gate resolves it."""
    env = dict(os.environ)
    env["PLAN_READINESS_VALIDATOR"] = str(READINESS_VALIDATOR)
    return subprocess.run(
        [sys.executable, str(READINESS_VALIDATOR), PLAN_REL],
        cwd=str(worktree),
        capture_output=True,
        text=True,
        env=env,
    )


class WorktreeBootstrapTest(unittest.TestCase):
    """The Transfer-in implementation recipe executes verbatim and the
    readiness gate needs it."""

    def _fresh_fixture(self, name: str) -> tuple[Path, Path]:
        """One fixture per test: a primary repo plus a linked worktree."""
        tmp = Path(tempfile.mkdtemp(prefix=f"execute-plan-bootstrap-{name}-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        primary = tmp / "primary"
        build_fixture_repo(primary)
        worktree = add_worktree(primary, tmp / "wt", "run-branch")
        return primary, worktree

    def test_recipe_block_executes_verbatim_and_gate_exits_zero(self):
        skill_text = SKILL_PATH.read_text(encoding="utf-8")
        recipe = extract_bootstrap_recipe(skill_text)
        for marker in CLOSEOUT_BLOCK_MARKERS:
            self.assertNotIn(
                marker,
                recipe,
                "the extractor picked the transfer-out-and-deletion block "
                "instead of the transfer-in recipe (r1 F8)",
            )
        # The pick guard has teeth only while the second fenced block in the
        # same region is the transfer-out-and-deletion migration recipe; pin
        # that block's position and content so a skill-text change cannot
        # silently invalidate the discriminator above (r1 F8).
        recipe_opener = skill_text.index("```bash", skill_text.index(BOOTSTRAP_LEAD_IN))
        recipe_end = skill_text.index("\n```", recipe_opener)
        closeout_opener = skill_text.find("```bash", recipe_end)
        self.assertGreater(
            closeout_opener,
            recipe_end,
            "expected a second fenced bash block (the transfer-out-and-"
            "deletion migration recipe) after the transfer-in recipe in "
            "the same region",
        )
        closeout_start = skill_text.index("\n", closeout_opener) + 1
        closeout_block = skill_text[
            closeout_start : skill_text.index("\n```", closeout_opener)
        ]
        self.assertIn("CLOSEOUT_SCRIPT", closeout_block)

        _primary, worktree = self._fresh_fixture("recipe")

        proc = subprocess.run(
            ["bash", "-c", recipe],
            cwd=str(worktree),
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            proc.returncode,
            0,
            f"verbatim bootstrap recipe failed: {proc.stderr}",
        )

        # Outcome 1: the facts file copied into the worktree.
        self.assertTrue(
            (worktree / ".ai-playbook" / "facts.md").is_file(),
            "bootstrap did not copy .ai-playbook/facts.md into the worktree",
        )
        # Outcome 2: the certified reviews sidecar pair copied.
        reviews = worktree / "docs" / "reviews"
        self.assertTrue((reviews / REVIEW_MD_NAME).is_file())
        self.assertTrue((reviews / REVIEW_SIDECAR_NAME).is_file())
        # Outcome 3: the tmp directory created.
        self.assertTrue(
            (worktree / "docs" / "tmp").is_dir(),
            "bootstrap did not create docs/tmp in the worktree",
        )
        # Outcome 4: the readiness gate exits 0 from the worktree.
        gate = run_readiness_validator(worktree)
        self.assertEqual(
            gate.returncode,
            0,
            "readiness gate failed from the bootstrapped worktree: "
            f"stdout={gate.stdout!r} stderr={gate.stderr!r}",
        )

    def test_gate_fails_without_bootstrap(self):
        _primary, worktree = self._fresh_fixture("negative")

        gate = run_readiness_validator(worktree)
        self.assertNotEqual(
            gate.returncode,
            0,
            "readiness gate passed from an UN-bootstrapped worktree; the "
            "bootstrap recipe is not load-bearing against this fixture",
        )
        stderr = gate.stderr.lower()
        self.assertTrue(
            "facts" in stderr or "reviews" in stderr,
            f"expected an environment failure naming facts or reviews, "
            f"got: {gate.stderr!r}",
        )


if __name__ == "__main__":
    unittest.main()
