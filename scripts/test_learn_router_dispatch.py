#!/usr/bin/env python3
"""Learn router dispatch and reference parity suite (done-closeout-lock-span plan, Task 5).

The learn skill is a router plus per-concern modules (the same module-dispatch
shape the done skill's Task 4 split landed, itself the maintenance size
refactor's shape). This suite pins the two Task 5 parity contracts:

1. Dispatch parity: the module filenames named in the router all exist, every
   module on disk is named by the router (both directions), the dispatch list
   preserves the Step 1 through the completion-checklist order, every router
   pointer carries the load-on-dispatch instruction, the router keeps its
   contract sections (frontmatter, Core Concepts, When to Use, Goal, module
   dispatch, Integration Points) and carries no step bodies, and every module
   keeps its section headings byte-identical to the pre-split headings.
2. Reference parity: every ``learn Step N`` citation across agents/,
   scripts/, docs/maintenance/, and README.md resolves to a ``## Step N:``
   heading in the router or a module, and the corpus's cited heading names
   resolve to a heading defined in the router or a module. Stale
   gate-numbering citations (steps that exist under no heading) fail here.

The router/module file names and the frozen heading tables below are the
contract of record for the split.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "agents/skills/learn"
ROUTER = SKILL_DIR / "SKILL.md"

#: The module files the router dispatches, in the run order (Step 1
#: extraction through the completion checklist).
EXPECTED_DISPATCH_ORDER = [
    "step-1-extract.md",
    "step-2-placement.md",
    "step-6-instruction-updates.md",
    "step-completion.md",
]

#: The frozen heading contract per module: the pre-split SKILL.md section
#: headings each module must carry byte-identically, in order, and no others.
EXPECTED_MODULE_HEADINGS = {
    "step-1-extract.md": [
        "## Step 1: Extract Lessons",
        "### Correction ledger for overturned technical output",
        "### Source-check self-audit",
        "### Generalization pass",
        '### Anti-pattern: premature dismissal as "already covered"',
        "## Step 1.5: Ralphex Execution Log Analysis (when available)",
        "## Step 1.6: Internet Research Capture",
        "## Step 1.7: Proper-Noun Justification Review (required before any lesson is written)",
        "## Step 1.8: Skill-usage issue capture",
    ],
    "step-2-placement.md": [
        "## Step 2: Placement Rules",
        "### Fork-4 project-corpus existence check (mechanical gate  -  required before ANY corpus write)",
        "### Guideline file roles (resolve from facts keys only)",
        "### Facts vs skill configuration (required before adding keys or constants)",
        "### Temporary artifacts",
        "### BEST_PRACTICES scope",
        "### Module/system knowledge",
        "### LLM examples/playbooks",
        "### LLM instruction rules",
        "### Exact class-name hygiene",
        "## Step 3: LLM Rule Qualification Gate",
        "## Step 4: Documentation Consolidation",
        "## Step 4.5: Add Cross-References for Lesson Discoverability",
        "## Step 5: Module Layout and Skill Workflow Lessons",
        "### Skill Output Improvement (corrected/retracted/downgraded outputs)",
    ],
    "step-6-instruction-updates.md": [
        "## Step 6: Instruction File Updates",
        "### Instruction placement ladder (required before any edit)",
        "## Step 6.5: Instruction size gate (required before finishing learn)",
        "## Step 6.6: Corpus gates (required before finishing learn)",
        "### User-level lessons-corpus gate (script)",
        "### Lesson concision gate (required before finishing learn)",
        "## Step 7: API Contract Naming Hygiene",
    ],
    "step-completion.md": [
        "## Completion Checklist",
    ],
}

#: The router sections the split must keep in SKILL.md.
ROUTER_CONTRACT_SECTIONS = [
    "## Core Concepts",
    "## When to Use",
    "## Goal",
    "## Module dispatch (the router contract)",
    "## Integration Points",
]

#: The citation surfaces the reference-parity sweep covers.
CITATION_SURFACES = [
    ROOT / "agents",
    ROOT / "scripts",
    ROOT / "docs/maintenance",
    ROOT / "README.md",
]

CITATION_SUFFIXES = (".md", ".py", ".sh")

#: ``learn Step N`` / ``learn Steps N, M`` citation shape (the apostrophe
#: possessive and the optional "skill" word included).
STEP_CITATION_RE = re.compile(
    r"learn(?:'s)?\s+(?:skill\s+)?Steps?\s+"
    r"(\d+(?:\.\d+)?(?:\s*(?:,|and|\.\.|\u2013|-|through|to)\s*\d+(?:\.\d+)?)*)"
)
STEP_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")

#: Heading names other surfaces cite by name; each must resolve to a heading
#: defined in the router or a module.
CITED_HEADING_NAMES = [
    "Generalization pass",
    "Facts vs skill configuration",
]


def _router_text() -> str:
    return ROUTER.read_text(encoding="utf-8")


def _module_texts() -> dict[str, str]:
    texts = {}
    for path in sorted(SKILL_DIR.glob("step-*.md")):
        texts[path.name] = path.read_text(encoding="utf-8")
    return texts


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


def _learn_headings() -> list[str]:
    """Every heading line carried by the router or a module."""

    lines = []
    for text in [_router_text(), *_module_texts().values()]:
        lines.extend(_markdown_headings(text))
    return lines


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


class DispatchParityTest(unittest.TestCase):
    """The router names exactly the modules on disk, in run order."""

    def test_router_named_modules_exist(self):
        named = set(re.findall(r"step-[a-z0-9-]+\.md", _router_text()))
        self.assertTrue(named, "router names no module files")
        for name in sorted(named):
            self.assertTrue(
                (SKILL_DIR / name).is_file(),
                f"router names absent module: {name}",
            )

    def test_modules_on_disk_named_by_router(self):
        router_text = _router_text()
        for name in sorted(p.name for p in SKILL_DIR.glob("step-*.md")):
            self.assertIn(name, router_text, f"module on disk not named by router: {name}")

    def test_dispatch_order_preserves_run_order(self):
        router_text = _router_text()
        found = []
        for name in re.findall(r"step-[a-z0-9-]+\.md", router_text):
            if name not in found:
                found.append(name)
        self.assertEqual(
            EXPECTED_DISPATCH_ORDER,
            found,
            "router dispatch order drifted from the Step 1 through completion order",
        )

    def test_every_router_pointer_carries_load_on_dispatch(self):
        router_text = _router_text()
        for line in router_text.splitlines():
            if re.search(r"step-[a-z0-9-]+\.md", line):
                self.assertIn(
                    "load",
                    line,
                    f"router pointer lacks the load-on-dispatch instruction: {line[:80]}",
                )
        self.assertIn(
            "loads the named module",
            router_text,
            "router lacks the load-on-dispatch instruction sentence",
        )

    def test_router_keeps_contract_sections_and_no_step_bodies(self):
        router_text = _router_text()
        self.assertTrue(router_text.startswith("---"), "router lost its frontmatter")
        self.assertIn("name: learn", router_text)
        for section in ROUTER_CONTRACT_SECTIONS:
            self.assertIn(section, router_text, f"router lost section: {section}")
        step_headings = [
            line
            for line in _markdown_headings(router_text)
            if re.match(r"^##+ Step \d", line)
        ]
        self.assertEqual(
            [],
            step_headings,
            f"router carries step body headings (bodies live in modules): {step_headings}",
        )

    def test_module_headings_byte_identical(self):
        texts = _module_texts()
        self.assertEqual(
            sorted(EXPECTED_DISPATCH_ORDER),
            sorted(texts),
            "module files on disk drifted from the dispatch contract",
        )
        for name, expected in EXPECTED_MODULE_HEADINGS.items():
            found = _markdown_headings(texts[name])
            self.assertEqual(
                expected,
                found,
                f"module headings are not byte-identical to the pre-split contract: {name}",
            )


class ReferenceParityTest(unittest.TestCase):
    """Learn Step and heading-name citations resolve to real definitions."""

    @classmethod
    def setUpClass(cls):
        cls.headings = _learn_headings()
        cls.learn_texts = [_router_text(), *_module_texts().values()]

    def _step_heading_exists(self, number: str) -> bool:
        prefix = f"## Step {number}:"
        return any(heading.startswith(prefix) for heading in self.headings)

    def test_learn_step_citations_resolve(self):
        stale = []
        for path in _citation_files():
            text = path.read_text(encoding="utf-8", errors="replace")
            for match in STEP_CITATION_RE.finditer(text):
                for number in STEP_NUMBER_RE.findall(match.group(1)):
                    if not self._step_heading_exists(number):
                        stale.append(f"{path.relative_to(ROOT)}: learn Step {number}")
        self.assertEqual(
            [],
            stale,
            "stale learn Step citations resolve to no Step heading in the router or modules",
        )

    def test_cited_heading_names_resolve(self):
        for name in CITED_HEADING_NAMES:
            definitions = [
                text for text in self.learn_texts if f"# {name}" in text
            ]
            self.assertTrue(
                definitions,
                f"cited heading name resolves to no definition in the router or modules: {name}",
            )


if __name__ == "__main__":
    unittest.main()
