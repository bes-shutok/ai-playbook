# Consistency Lens

Review abstract artifacts (plans, RFCs, design documents) for internal contradictions, stale cross-references, source-of-truth drift, and invalid validation claims. Loaded by `contract-docs` in plan and RFC reviews per `review-panel-selection.md`.

**Scope:** document-level contradictions only. This lens compares statements in the artifact against each other and against the artifact's own declared sources of truth. It does not judge runtime code.

**Boundary (single ownership):**
- Runtime bugs, wrong algorithms, edge cases in existing code: `quality` (lead worker `correctness-completeness`).
- Weak or missing tests: `testing` (lead worker `testing`).
- Wiring, registration, configuration, and completeness gaps in code or the codebase: `implementation` (lead worker `correctness-completeness`).
- Contradictions inside the reviewed plan or RFC, between its sections, or against its declared source of truth: this lens.

When a finding sounds like a bug but the defect is that two statements in the artifact cannot both hold, keep it here even if the fix lands in a task step.

Pattern tags: `consistency#<kebab-slug>`.

## Internal contradictions

1. Design invariants, glossary, or terminology vs task steps: a step that violates an invariant stated elsewhere in the same artifact.
2. Task A output format vs Task B input expectation: a cross-task mismatch that would surface only at integration time.
3. Stated goal vs proposed mechanism: the plan's approach cannot achieve its own stated outcome as written.
4. Naming drift: the same concept named differently across tasks, sections, or the eval criteria.
5. Severity or blocking claims that conflict between the summary and the detail sections.

## Stale cross-references

1. References to sections, tasks, or files that do not exist in the current artifact revision (renamed, renumbered, or removed).
2. References that resolve to the wrong target after a restructure (a task pointing at a prior revision's file list).
3. Round-to-round references in looped reviews that cite a superseded round's content as current.

## Source-of-truth drift

1. A rule, decision, or contract restated in two or more places in the artifact with diverging wording; propose consolidating into the single owning section and linking from the copies.
2. The artifact declares a source of truth (glossary, schema, config shape) and then contradicts it in task prose.
3. Measured counts or inventories asserted in prose that the artifact's own referenced source disagrees with; require a re-measurement, not a re-assertion.

## Invalid validation claims

1. A validation command that does not exercise what the surrounding text claims it proves (checks presence, not behavior).
2. A gate phrased as a claim ("tests cover X") with no command or observable evidence that runs X.
3. Inherited or validated-by-prior-round statements used as proof without a re-verification step; treat the claim as a flag to re-probe, not as evidence.

## Evidence requirements

Each finding must name both statements (or the statement and the referenced source) with their locations in the artifact, quote the conflicting text, and state which one is authoritative or how to reconcile them.

Report problems only. No positive observations.
