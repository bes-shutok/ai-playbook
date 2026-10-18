#!/usr/bin/env python3
"""Done collapsed-spine contract suite (re-aimed at the done target-state flip).

The done skill is one collapsed SKILL.md (the done target-state plan's Task 4
flip dissolved the done-closeout-lock-span router split's module files). This
suite pins the collapsed contract:

1. Spine shape: the skill carries the three runner invocations verbatim
   (``done_run.sh setup``, ``done_run.sh commit``, ``done_run.sh finalize``)
   plus the sync reference (``docs_branch_sync.sh``), stays at or under the
   400-line budget, carries no inline lock ceremony or marker recipe, and no
   dispatchable module body survives beside it (no ``step-*.md`` /
   ``sweep-gates-*.md`` file under the done skill directory).
2. Reference parity: every ``done Step N`` citation across agents/, scripts/,
   docs/maintenance/, and README.md resolves to a ``## Step N:`` heading in
   SKILL.md, and the corpus's cited bold paragraph leads resolve to a bold
   lead defined in SKILL.md. Stale gate-numbering citations fail here.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "agents/skills/done"
SKILL = SKILL_DIR / "SKILL.md"

#: The runner invocations and the sync reference the collapsed spine names.
SPINE_INVOCATIONS = [
    "done_run.sh setup",
    "done_run.sh commit",
    "done_run.sh finalize",
    "docs_branch_sync.sh",
]

#: The line budget the flip set for the collapsed operative text.
LINE_BUDGET = 400

#: Citation surfaces the reference-parity sweep covers.
CITATION_SURFACES = [
    ROOT / "agents",
    ROOT / "scripts",
    ROOT / "docs/maintenance",
    ROOT / "README.md",
]

CITATION_SUFFIXES = (".md", ".py", ".sh")

#: ``done Step N`` / ``done Steps N, M`` citation shape (the apostrophe
#: possessive and the optional "skill" word included).
STEP_CITATION_RE = re.compile(
    r"done(?:'s)?\s+(?:skill\s+)?Steps?\s+"
    r"(\d+(?:\.\d+)?(?:\s*(?:,|and|\.\.|\u2013|-|through|to)\s*\d+(?:\.\d+)?)*)"
)
STEP_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")

#: Bold paragraph leads other surfaces cite by name; each must resolve to a
#: ``**<lead>`` definition in the collapsed skill.
CITED_BOLD_LEADS = [
    "Run placement",
    "Review-candidate classification",
    "Runner-owned merge-lock spans",
    "Runner-refusal posture",
]

#: Recipe signatures that must stay in script behavior, never in the skill.
FORBIDDEN_RECIPE_SIGNATURES = [
    "merge-wait-acquire",
    "run-start-$(date",
]


def _skill_text() -> str:
    return SKILL.read_text(encoding="utf-8")


def _markdown_headings(text: str) -> list[str]:
    """Heading lines outside fenced code blocks (bash comments inside
    fences start with ``# `` too and are never headings)."""

    headings = []
    fenced = False
    for line in text.splitlines():
        if line.startswith("```"):
            fenced = not fenced
            continue
        if not fenced and re.match(r"^#{1,3} ", line):
            headings.append(line)
    return headings


def _citation_files() -> list[Path]:
    files = []
    for surface in CITATION_SURFACES:
        if surface.is_file():
            files.append(surface)
            continue
        for path in sorted(surface.rglob("*")):
            if (
                path.is_file()
                and path.suffix in CITATION_SUFFIXES
                and ".git" not in path.parts
            ):
                files.append(path)
    return files


class CollapsedSpineTest(unittest.TestCase):
    """The collapsed skill is the one dispatchable body, at budget."""

    def test_no_module_body_survives(self):
        leftovers = sorted(
            p.name
            for p in SKILL_DIR.glob("step-*.md")
        ) + sorted(
            p.name
            for p in SKILL_DIR.glob("sweep-gates-*.md")
        )
        self.assertEqual(
            [],
            leftovers,
            "dispatchable module bodies survived the flip; the collapsed "
            "SKILL.md is the one body",
        )

    def test_spine_names_the_three_invocations_and_the_sync(self):
        text = _skill_text()
        for invocation in SPINE_INVOCATIONS:
            self.assertIn(invocation, text)

    def test_skill_stays_at_or_under_the_line_budget(self):
        lines = _skill_text().splitlines()
        self.assertLessEqual(
            len(lines),
            LINE_BUDGET,
            f"the collapsed skill drifted past the {LINE_BUDGET}-line budget",
        )

    def test_no_inline_recipe_signatures(self):
        text = _skill_text()
        for signature in FORBIDDEN_RECIPE_SIGNATURES:
            self.assertNotIn(signature, text)
        self.assertNotRegex(text, r"(^|\s)write-manifest(\s|$)")
        self.assertNotIn("Step 2.6", text)


class ReferenceParityTest(unittest.TestCase):
    """Done Step and bold-lead citations resolve to the collapsed skill."""

    @classmethod
    def setUpClass(cls):
        cls.headings = _markdown_headings(_skill_text())

    def _step_heading_exists(self, number: str) -> bool:
        prefix = f"## Step {number}:"
        return any(heading.startswith(prefix) for heading in self.headings)

    def test_done_step_citations_resolve(self):
        stale = []
        for path in _citation_files():
            text = path.read_text(encoding="utf-8", errors="replace")
            for match in STEP_CITATION_RE.finditer(text):
                for number in STEP_NUMBER_RE.findall(match.group(1)):
                    if not self._step_heading_exists(number):
                        stale.append(f"{path.relative_to(ROOT)}: done Step {number}")
        self.assertEqual(
            [],
            stale,
            "stale done Step citations resolve to no Step heading in the collapsed skill",
        )

    def test_cited_bold_leads_resolve(self):
        text = _skill_text()
        for lead in CITED_BOLD_LEADS:
            self.assertIn(
                f"**{lead}",
                text,
                f"cited bold lead resolves to no definition in the collapsed skill: {lead}",
            )


if __name__ == "__main__":
    unittest.main()
