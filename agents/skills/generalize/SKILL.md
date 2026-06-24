---
name: generalize
description: >
  Map a single incident or lesson to its underlying root-cause principle family, or audit a whole
  lessons corpus for duplicates and blind spots. Use when capturing or reviewing a lesson with
  the `learn` skill (so the lesson is recalled by problem shape, not by file location), or when
  auditing a bloated lessons corpus that may hide true duplicates or gaps. Trigger phrases:
  "generalize this lesson", "what family is this", "audit my lessons", "consolidate these rules",
  "principle theater", "find duplicate lessons".
---

# Principle Generalization

## Core Concept

A lesson is most useful when it can be recalled by the *shape* of the problem it solves, not by
where the last incident happened. Two failures with the same root cause but different file surfaces
should point to the same principle; otherwise the second failure re-bites because nothing
cross-references it.

The **catalog** at `coding_guidelines.md` #17+ (the Root-Cause Principle Catalog, under
`shared_docs_dir`) is the family authority: it names the families (A to H) and the shape triggers
that belong to each. Skills run under the user context, so resolve `shared_docs_dir` from the
USER-facts document (this key is NOT present in per-repo facts); never hardcode the path.

The **incident is always kept as the witness.** A bare precept with no concrete failure mode is
unfalsifiable and forgettable. The family names the pattern; the incident proves it bites.
Generalization strips the incident-specific skin (file name, module, framework jargon) but keeps
the incident as evidence that the family is real.

This skill has two modes:

- **`map`**: one incident or lesson: name its family, write its shape trigger, decide cross-ref
  vs new entry.
- **`audit`**: a whole corpus: cluster lessons by family AND decompose them into atoms for
  cross-family dedup, surface true duplicates, overlapping siblings, contrasts, and blind spots,
  emit a consolidation map.

## When to Use

- During the `learn` Generalization pass, before a lesson is written to its final destination.
- When reviewing a captured lesson and wondering "is this already a rule somewhere else?"
- When a lessons corpus has grown past easy recall and may hide duplicates or gaps.
- Standalone when the user asks to generalize, consolidate, or audit lessons.

## The Iron Law

```
GENERALIZE THE PATTERN, KEEP THE INCIDENT. THE CATALOG IS THE AUTHORITY.
```

Do not invent a family that is not in the catalog without curating it. Do not strip the incident
down to a precept with no witness. Do not renumber existing lessons to make consolidation tidy.

## map Mode: One Incident or Lesson

### Phase 1: Strip the incident-specific skin

Read the incident as captured (the bug, the diff, the failure mode). Identify and remove the
skin that is *not* part of the root cause:

- File paths, module names, class names
- Framework or language jargon that does not bear on the mechanism
- The specific values that happened to be wrong (keep the *kind* of value, drop the literal)

What remains is the mechanism: the step where a precondition was stale, a sentinel was conflated
with a real value, an unmatched record was discarded, and so on. If you cannot state the mechanism
without naming a file, you have not finished stripping.

### Phase 2: Name the root-cause family from the catalog

Open `coding_guidelines.md` #17+ under `shared_docs_dir` and match the mechanism to a family:

| Family | Recognize it when |
|--------|-------------------|
| **A. Equivalence-class coverage** (#18) | A test pins one cell of a class of inputs; the fix must cover the class |
| **B. Error-policy propagation** (#19) | A centralized fallible op is reused, but each call site's raise-vs-degrade policy was not carried over |
| **C. Representation: sentinel vs None vs exception** (#20) | A None, a sentinel, and an exception are conflated; recoverability differs |
| **D. Single source of truth** (#21) | Two authoritative copies exist; one drifts |
| **E. Temporal / ordering invariants** (#22) | An earlier event consumes state a later event changes; preconditions go stale |
| **F. Layering / dependency direction** (#23) | Logic lives in the wrong layer, or dependencies point both ways |
| **G. Data-loss observability** (#24) | Unmatched or dropped records could vanish silently |
| **H. Verify the real thing, not the abstraction** (#25) | Code trusts a name, summary, mock, or field-name conflation instead of tracing real data |

If the mechanism fits a family, name that family. If it genuinely fits none, **propose a new
family** to the catalog. New families are *curated, never auto-generated*: state the family name,
the shape trigger, and at least two concrete incidents that justify it. Until the catalog accepts
the proposal, the lesson stays anchored to its incident under the existing family closest to it.

### Phase 3: Write the shape trigger

The shape trigger is the sentence a reader in a *different module* would recognize as "this is
that family." It must be independent of the original file or surface. Compare:

- Weak (incident-anchored): "In the FIFO matcher, the tolerance was stale."
- Strong (shape-anchored): "After a sliding window shrinks, recompute the tolerance before
  admitting the next candidate; a stale bound admits invalid windows."

The shape trigger names the *situation*, not the *place*.

### Phase 4: Keep the concrete incident as the witness

The lesson body keeps the original incident: the failing test, the diff, the row that was
silently dropped. The family and shape trigger go in the headline and the cross-ref; the incident
stays as proof. A rule with no witness is principle theater (see Anti-Patterns).

### Phase 4.5: Format using the standard Principle-based Template

Every new lesson added to a repository's `development_lessons.md` must follow the standard principle-based template to ensure formatting consistency. Construct the lesson entry with these exact sections:

- `**Principle:** Family [Letter] ([Family Name])` (omit only for Excluded/process-only lessons)
- Description: Plain language explanation of the lesson and its context
- `**Why this matters:**` (or inline description): Detail the rationale and risk of ignoring the lesson
- `**Required behavior:**` / `**Qualification gate:**`: Clear, action-oriented instructions on what to do or avoid
- `**Shape trigger (when to suspect this family):**`: The situation, independent of the files or framework, where this pattern is relevant
- `**General form:**`: The abstract, domain-independent rule governing the class of problems
- `**Example ([plan/feature]):**`: The concrete incident that serves as the witness
- `**See also:**`: Clickable links to other related lessons or guidelines

### Phase 5: Check for an existing same-family lesson

Before writing a new entry, look for an existing lesson in the same family. Resolve in this order:

1. **`principle-index.md` (O(1) lookup).** If the repo maintains a `principle-index.md` mapping
   family to lesson numbers, read it first. This is the preferred resolution path.
2. **Corpus scan (fallback).** If no index exists, scan the lessons corpus for entries citing the
   same family. This is slower and more error-prone; flag the absence of an index so the audit
   mode can create one later.

**Prefer cross-ref over a new entry.** If an existing lesson already covers this family at this
generality, add the new incident as a witness to that lesson (a second example, a cross-reference)
rather than creating a near-duplicate. Open a new entry only when the angle is genuinely distinct
(see the overlapping-cluster rule in audit mode).

## audit Mode: A Whole Corpus

### Phase 1: Require unique lesson numbers as a precondition

A consolidation pass is meaningless if the corpus has duplicate lesson numbers, because two
lessons sharing a number collapse ambiguously. Before anything else, gate on uniqueness:

```bash
grep -oE '^[0-9]+\.' path/to/development_lessons.md | sort | uniq -d
```

If this prints anything, **abort with guidance.** Do not attempt consolidation over a corpus with
duplicate numbers; tell the user to renumber until the `uniq -d` output is empty, then re-run.

### Phase 2: Map every lesson to a family

For each numbered lesson, apply the `map` mode (Phases 1 through 3) and record the family it
belongs to. A lesson may map to more than one family; pick the primary one and note the secondary.

### Phase 3: Cluster by family

Group all lessons sharing a primary family into a cluster. The cluster is the unit of comparison
for the next phase.

### Phase 4: Classify each cluster

For each cluster, classify every pair of lessons as one of three categories:

- **true-duplicate**: same atom; one re-states the other. Same family, same shape trigger, same
  mechanism, same action prescribed. One should collapse into the other.
- **overlapping**: same family but DIFFERENT atoms (siblings). The two lessons share a root-cause
  family but prescribe distinct actions (e.g., one covers the read path, another the write path).
  "Overlapping" means different-atom siblings, NOT partial-duplicates; keep both.
- **contrasting**: same family or topic but OPPOSITE prescriptions. The two lessons point in
  opposite directions (e.g. "sibling callers must be byte-identical" vs "sibling callers must
  intentionally diverge"). These are related but neither duplicate nor overlapping: do not
  collapse, do not treat as overlapping. Cross-link them with a "distinguishing from" note that
  explains the contrast. Witness: lessons #119 ("identical sibling implementations") and #136
  ("intentionally divergent caller policies, mirroring the wrong one is the bug") prescribe
  opposite actions for sibling code and must remain distinct.

When in doubt, classify as overlapping, not true-duplicate. Collapsing an overlapping lesson
destroys a distinct angle (see Anti-Patterns).

### Phase 4b: Atom-level cross-family dedup (family-agnostic safety net)

Phase 3 clusters by family, so Phase 4 only compares within a family. It is structurally blind to
two lessons that share an ATOMIC principle but have DIFFERENT primary families. This phase catches
those by decomposing every lesson into atoms and deduping family-agnostically.

- **Decompose**: for each lesson, extract its atomic principle(s), the smallest
  independently-actionable rule(s) it states. Most lessons yield one atom; a multi-rule lesson
  (e.g. one with several bullets) yields two or three. Name each atom as a short imperative, e.g.
  "pin each caller policy arm when centralizing a shared helper" or "recompute tolerance after
  every window shrink".
- **Dedupe family-agnostically**: collect all atoms across the whole corpus. Two atoms are the
  SAME atom only if they prescribe the same action, different incident or different family is NOT
  sufficient (same sharp bar as Phase 4). Do not over-merge; this is a safety net, not a sweep.
- **Flag shared atoms**: report every atom stated in 2+ lessons, and split them into two kinds:
  - **Intra-family shares** are atoms shared by lessons with the same primary family. Phase 4
    should have caught these. If Phase 4 classified them overlapping, reclassify as true-duplicate
    and collapse (they prescribe the same action, not sibling actions).
  - **Cross-family shares** are atoms shared by lessons with DIFFERENT primary families. Phase 4
    structurally could not see these. Extract the shared atom to one canonical home and trim each
    lesson to its distinct residue.
- **Witness note**: lesson #81 (Family E, temporal/ordering) once bundled a column-coupling bullet
  that fully restated lesson #82 (Family D, single source of truth). Family-clustering never
  compared them; the duplicate was found only by this family-agnostic atom pass.
- **Calibration note**: most corpora are near-atomic (few shared atoms, roughly 2% shared-atom
  ratio on a real corpus). This phase is a SAFETY NET, not the primary consolidation lever. Do not
  force merges when the atom pass surfaces nothing.

### Phase 5: Emit the consolidation map and blind-spot analysis

**Consolidation map.** For each true-duplicate cluster, name the canonical lesson number (the one
kept) and the numbers that collapse into it. Preserve lesson numbers per invariant 2:

- The canonical number is the lowest-numbered lesson in the cluster (or the one already most
  cross-referenced).
- Collapsed lessons are removed, but **no surviving lesson is renumbered.** Gaps from removed
  lessons stay as gaps. Renumbering during consolidation breaks every external cross-reference.

**Blind-spot analysis.** After mapping, report:

- **Over-represented families**: families with many lessons, where consolidation yields the most
  value and where the next incident probably duplicates an existing rule.
- **Under-represented families**: families with zero or one lesson, where the corpus has a blind
  spot and future incidents are likely to be missed.

Suggest creating or refreshing the repo's `principle-index.md` from the final family map so the
next `map` mode resolves in O(1).

## Integration Points

### With learn

The `learn` skill's Generalization pass calls this skill's `map` mode before a lesson is written
to its final destination, so the lesson is anchored to its family and cross-referenced rather
than duplicated. See `../learn/SKILL.md` for the Generalization pass steps. `audit` mode is
invoked separately, when a corpus has grown large enough to need consolidation.

### With plans

A plan's pre-computation or invariant checks may name a family ("this design touches the
single-source-of-truth family D, so verify there is no second authoritative copy"). Naming the
family in the plan lets reviewers recognize the risk by shape. See `../plans/SKILL.md`. The
catalog families are the canonical vocabulary; do not invent ad-hoc family names in a plan body.

### With review-agents

Premortem and other quality lenses may cite a family when surfacing a risk ("the centralized
fallible op here is an Error-policy propagation (B) hazard"). Citing the family lets the review
connect to the catalog and to prior incidents without re-deriving the principle. See
`../review-agents/SKILL.md`.

## Anti-Patterns

| Anti-pattern | Correction |
|---|---|
| Principle theater: a family name with no incident witness | Keep the concrete incident in the lesson body; the family names the pattern, the incident proves it bites |
| Over-clustering: forcing distinct lessons together | When two same-family lessons differ in shape trigger or witness, classify them overlapping, not true-duplicate |
| Renumbering during consolidation | Preserve lesson numbers; collapsed entries leave gaps. Renumbering breaks every external cross-reference |
| Auto-generating families | Families are curated from the catalog, never auto-derived. Propose new families to the catalog with at least two incidents |
| Collapsing an overlapping-but-distinct lesson | Same family is not same lesson. Distinct angles survive consolidation as separate entries with a cross-ref |
| Stripping the incident entirely | Strip the skin (file, module, jargon), keep the witness (the failure mode). A precept with no witness is unfalsifiable |
| Skipping the `principle-index.md` lookup | Always try the O(1) index first; fall back to a corpus scan only if the index is absent, and flag the absence |
| Family-clustered-only audit (skipping the atom-level pass) | Phases 3 and 4 cluster within a family, so they cannot see a shared atom whose lessons have different primary families. Always run the atom-level family-agnostic pass (Phase 4b) after family-clustering, or cross-family duplicates hide silently |

## Standalone Invocation

When invoked directly (not as part of `learn`):

1. Ask the user which mode: `map` (one incident or lesson) or `audit` (a corpus).
2. For `map`: get the incident or lesson text, then run Phases 1 through 5 and report the family,
   shape trigger, and cross-ref-vs-new-entry decision.
3. For `audit`: confirm the corpus path, run the `uniq -d` gate first, then Phases 1 through 5 and
   report the consolidation map and blind-spot analysis.
4. Offer: "Want me to write the cross-refs / create the `principle-index.md` / propose the new
   family to the catalog now?"
