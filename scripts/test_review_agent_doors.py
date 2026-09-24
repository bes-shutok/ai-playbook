"""Review-agent door-pattern registry selftest.

Gates the consumer-facing door patterns (typed-catalog enumeration, helper
retargeting after a door, delivery-slice meta prose) exactly once per lens
file, with the origin-mandated required actions present in each pattern's
text, and characterizes the witnessed miss shapes against the pre-existing
concurrency patterns. Run: python3 scripts/test_review_agent_doors.py
"""

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LENS = REPO / "agents" / "skills" / "review-agents"


def lens_text(name: str) -> str:
    return (LENS / name).read_text(encoding="utf-8")


def pattern_window(text: str, pattern_id: str, before: int = 700) -> str:
    """Text surrounding a `Pattern: `<id>`` declaration: the preceding
    `before` characters (the item the declaration closes) plus the
    declaration line itself."""
    occurrences = [
        m for m in re.finditer(re.escape(pattern_id), text)
    ]
    declaration = [m for m in occurrences if f"Pattern: `{pattern_id}`" in text[max(0, m.start() - 12):m.end() + 2]]
    if len(occurrences) != 1 or len(declaration) != 1:
        raise AssertionError(
            f"{pattern_id}: expected exactly one `Pattern: \\`{pattern_id}\\`` "
            f"declaration, found {len(declaration)} (total mentions {len(occurrences)})"
        )
    start = declaration[0].start()
    window = text[max(0, start - before):start + len(pattern_id) + 12]
    return re.sub(r"\s+", " ", window)


class ReviewAgentDoorsTest(unittest.TestCase):
    def test_typed_catalog_enumeration_door_declared(self):
        text = lens_text("quality.md")
        window = pattern_window(text, "quality#typed-catalog-enumeration-door")
        # (a) key source is the typed/published definition set, not a wider
        # all-keys helper, unless the plan documents the wider set
        self.assertIn("typed or published definition set", window)
        self.assertIn("all-keys", window)
        self.assertIn("unless the plan explicitly documents the wider set", window)
        # (b) the finding body names both enumeration APIs
        self.assertIn("names both enumeration APIs", window)
        # (c) the finding body cites one illegal key the wide API admits
        self.assertIn("one illegal key", window)

    def test_helper_path_retarget_after_door_declared(self):
        text = lens_text("testing.md")
        window = pattern_window(text, "testing#helper-path-retarget-after-door")
        # (a) grep of test helpers for the newly banned path
        self.assertIn("grep of test helpers", window)
        # (b) same-change-set retarget or update
        self.assertIn("same-change-set", window)
        # (c) green run of the owning integration class, not only unit suite
        self.assertIn("owning integration class", window)
        self.assertIn("not only the unit suite", window)

    def test_delivery_slice_meta_declared(self):
        text = lens_text("documentation.md")
        window = pattern_window(text, "documentation#prose-delivery-slice-meta")
        # class-level comment carrying only plan-slice ids, ticket keys, or
        # add-narrative is a finding requiring behavior-facing prose
        self.assertIn("plan-slice identity", window)
        self.assertIn("ticket key", window)
        self.assertIn("behavior-facing", window)

    def test_panel_signal_names_both_doors(self):
        text = lens_text("review-panel-selection.md")
        self.assertIn("quality#typed-catalog-enumeration-door", text)
        self.assertIn("testing#helper-path-retarget-after-door", text)

    def test_fixture_annotations_cover_witnessed_shapes(self):
        fixtures = [
            # catalog fixture: a materialize loop enumerating an all-keys
            # helper where the typed definitions set is required
            ("quality#typed-catalog-enumeration-door", "quality.md",
             ["all-keys", "typed or published definition set"]),
            # documentation fixture: a class javadoc whose only content is a
            # P0.n slice id plus ticket key
            ("documentation#prose-delivery-slice-meta", "documentation.md",
             ["P0.n", "ticket key"]),
            # testing fixture: a shared test helper calling a path a new
            # production door rejects
            ("testing#helper-path-retarget-after-door", "testing.md",
             ["helper"]),
        ]
        for pattern_id, lens_name, tokens in fixtures:
            window = pattern_window(lens_text(lens_name), pattern_id)
            for token in tokens:
                self.assertIn(token, window,
                              f"{pattern_id} pattern text lacks fixture token {token!r}")

    def test_concurrency_lost_work_fixtures_characterized(self):
        text = lens_text("concurrency.md")
        # fixture 1: ungated multi-row cleanup CTE deleting without an
        # update-generation fence -> cleanup-gated-on-update names the fence
        cleanup = pattern_window(text, "concurrency#cleanup-gated-on-update")
        self.assertIn("gate the", cleanup)
        self.assertIn("updated", cleanup)
        self.assertIn("RETURNING", cleanup)
        # fixture 2: worker permit acquired without a finally release ->
        # permit-finally names the finally release
        permit = pattern_window(text, "concurrency#permit-finally")
        self.assertIn("finally", permit)
        self.assertIn("release", permit)


if __name__ == "__main__":
    unittest.main(verbosity=2)
