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

    def test_prose_sot_consolidation_door_declared(self):
        text = lens_text("documentation.md")
        window = pattern_window(text, "documentation#prose-sot-consolidation")
        # (a) authority-role classification and owner nomination
        self.assertIn("no more than two current SOT owners", window)
        # (b) one consolidation finding, not one finding per consumer
        self.assertIn("one consolidation finding", window)
        # (c) each affected consumer's disposition recorded
        self.assertIn("historical context banner", window)
        self.assertIn("independent contract update", window)

    def test_prose_relocatable_identifier_inventory_declared(self):
        text = lens_text("documentation.md")
        window = pattern_window(text, "documentation#prose-relocatable-identifier-inventory")
        # (a) trigger: the listed identifiers also appear as real paths,
        # mounts, or resource names in the same diff
        self.assertIn("real paths, mounts, or resource names in the same diff", window)
        # (b) delete-plus-pointer preference over rewriting the inventory
        self.assertIn("delete plus pointer to the owning artifact", window)
        # (c) rewrite only when the comment is the sole operator contract
        self.assertIn("sole operator contract", window)
        # (d) shared-rule alignment with the coding guidelines
        self.assertIn("coding_guidelines.md` #35", window)

    def test_dual_surface_policy_parity_declared(self):
        text = lens_text("architecture.md")
        window = pattern_window(text, "architecture#dual-surface-policy-parity")
        # (a) trigger: one deny or allow policy enforced at more than one
        # public entry point (parser, validator, filter, gateway, batch
        # importer)
        self.assertIn("deny or allow policy enforced at more than one public entry point", window)
        self.assertIn("batch importer", window)
        # (b) predicate-shape compare: exact equality versus contains or
        # prefix, normalization steps, shared versus duplicated constant sets
        self.assertIn("exact equality versus contains or prefix", window)
        self.assertIn("normalization steps", window)
        self.assertIn("shared versus duplicated constant sets", window)
        # (c) shared-helper preference plus the per-surface witnesses
        # alternative
        self.assertIn("prefer one shared helper", window)
        self.assertIn("both surfaces reject the same representative inputs", window)
        # (d) asymmetry examples: passes exact match but fails contains
        self.assertIn("passes exact match but fails contains", window)

    def test_cross_surface_policy_witness_declared(self):
        text = lens_text("testing.md")
        window = pattern_window(text, "testing#cross-surface-policy-witness")
        # weaker-shape mutation of a shared helper forces one failing
        # witness per surface
        self.assertIn("a shared helper enforcing one policy is mutated to the weaker shape", window)
        self.assertIn("at least one failing witness per surface", window)
        # shared helper preferred over duplicated predicates
        self.assertIn("shared helper preferred over duplicated predicates", window)

    def test_truncating_conversion_floor_declared(self):
        text = lens_text("implementation.md")
        # before=900: the trigger bullet sits ~730 chars above the
        # declaration, past the default 700-char lookback, so this door
        # widens the window to keep the trigger class selector pinned.
        window = pattern_window(
            text, "implementation#truncating-conversion-floor", before=900
        )
        # (a) trigger: a validated config or API duration or numeric
        # quantity rendered through a truncating conversion
        self.assertIn("a validated config or API duration or numeric quantity", window)
        # (a2) trigger tail: the zero-meaning sink qualifier stays pinned
        self.assertIn("treat zero as unlimited, disabled, or no-limit", window)
        # (b) the finding traces the span: validation, conversion, sink
        self.assertIn("trace validation, conversion, sink", window)
        # (c) sub-floor rejection even when the source value is positive
        self.assertIn(
            "reject values whose converted integer is below the sink's "
            "minimum meaningful unit even when the source value is positive",
            window,
        )
        # (d) cites the shared JVM guideline when present in the Guideline Pack
        self.assertIn(
            "cite the shared JVM guideline when present in the Guideline Pack",
            window,
        )

    def test_nullable_jdbc_type_declared(self):
        text = lens_text("quality.md")
        window = pattern_window(text, "quality#nullable-jdbc-type")
        # (a) nullable mapper parameter or bound value requires an explicit
        # JDBC type for the SQL NULL case
        self.assertIn(
            "nullable mapper parameter or bound value requires an explicit "
            "JDBC type for the SQL NULL case",
            window,
        )
        # (b) plus a test exercising the null representation
        self.assertIn("plus a test exercising the null representation", window)

    def test_null_tuple_claim_predicates_declared(self):
        text = lens_text("concurrency.md")
        window = pattern_window(text, "security#null-tuple-claim-predicates")
        # (a) SQL three-valued logic for first-write-wins audit tuples
        self.assertIn("SQL three-valued logic for first-write-wins audit tuples", window)
        # (b) equality never matches NULL, so the fresh-claim branch needs
        # IS NULL per field
        self.assertIn("SQL equality never matches NULL", window)
        self.assertIn("IS NULL per field in the fresh-claim branch", window)
        # (c) fresh-claim, identical-retry, and conflicting-retry witnesses
        self.assertIn("fresh-claim, identical-retry, and conflicting-retry witnesses", window)

    def test_packaged_schema_parity_declared(self):
        text = lens_text("implementation.md")
        window = pattern_window(text, "implementation#packaged-schema-parity")
        # (a) compare packaged deployment and local-development manifests
        # against the canonical migration and seed inventory
        self.assertIn("compare packaged deployment and local-development manifests", window)
        # (b) including ordering
        self.assertIn("canonical migration and seed inventory, including ordering", window)
        # (c) non-absorption boundary: verify-script expected inventories and
        # missing ops-doc or bootstrap-mount updates stay owned by their
        # landed sections
        self.assertIn("bootstrap-mount updates stay owned by", window)

    def test_container_discovery_fast_path_declared(self):
        text = lens_text("testing.md")
        window = pattern_window(text, "testing#container-discovery-fast-path")
        # (a) an auto-detected test extension decides the non-container fast
        # path before any container discovery
        self.assertIn(
            "an auto-detected test extension decides the non-container fast "
            "path before any container discovery",
            window,
        )
        # (b) container probes on classes needing no container are a runner
        # defect
        self.assertIn("container probes on classes needing no container are a runner defect", window)

    def test_panel_signal_names_both_doors(self):
        text = lens_text("review-panel-selection.md")
        self.assertIn("quality#typed-catalog-enumeration-door", text)
        self.assertIn("testing#helper-path-retarget-after-door", text)
        # targeted follow-up trigger: the migration-renumber branch forces
        # contract-docs plus correctness-completeness on the paired surfaces
        self.assertIn("migration renumber", text)
        self.assertIn("contract-docs` and `correctness-completeness` workers on the paired surfaces", text)
        # the dual-entry validation-policy branch additionally forces
        # design-simplicity plus testing
        self.assertIn("dual-entry validation-policy change", text)
        self.assertIn("design-simplicity` and `testing` workers", text)

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
            # documentation fixture: a duplicated normative paragraph across
            # living documents with no nominated SOT owner
            ("documentation#prose-sot-consolidation", "documentation.md",
             ["SOT owners", "consolidation finding"]),
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
