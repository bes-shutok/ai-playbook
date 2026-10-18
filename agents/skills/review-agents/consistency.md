# Consistency Lens

Review abstract artifacts (plans, RFCs, design documents) for internal contradictions, stale cross-references, source-of-truth drift, and invalid validation claims. Loaded by `contract-docs` in plan and RFC reviews, and when contract-impact closure triggers per `review-panel-selection.md`.

**Scope:** document-level contradictions only. This lens compares statements in the artifact against each other and against the artifact's own declared sources of truth. It does not judge runtime code; directly dependent documents pulled in by the contract-impact closure trigger (`documentation.md` phase 1) join the compared statements.

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
4. Ticket-as-gate drift: a living artifact gates behavior on an issue key (for example `PROJ-1234`) whose churn is unrelated to the capability it names; stage one SOT-drift finding proposing the durable capability name, not per-surface staleness findings; canonical gates in `documentation.md` Living-doc gates. <!-- portability: abstract --> issue-key shape is an abstract illustration owned by the orchestrator layer
5. Wire-contract duplication: a caller catalog restates OpenAPI schemas, enums, or status maps; stage one fan-out finding that thin-indexes the catalog to the OpenAPI definition, not one finding per restated row; canonical gates in `documentation.md` Living-doc gates.

### Cross-artifact contract drift

When a changed public contract invariant supersedes a normative statement in a directly dependent artifact (a schema paragraph naming an older migration as the executable definition, a table sketch the new schema rejects), the drift between the changed contract and the dependent statement is a finding here: name both statements and their locations, quote the conflicting text, and state which is authoritative (the changed contract) and what reconciliation the dependent document needs.

The dependent artifact enters the consistency read-set only via the contract-impact closure trigger (`documentation.md` phase 1); unrelated documents and broad freshness sweeps stay out of scope. Findings use pattern `consistency#stale-schema-source-reference` and route through the contract-impact exception (`doing-code-review` section 4.9.2).

## Invalid validation claims

1. A validation command that does not exercise what the surrounding text claims it proves (checks presence, not behavior).
2. A gate phrased as a claim ("tests cover X") with no command or observable evidence that runs X.
3. Inherited or validated-by-prior-round statements used as proof without a re-verification step; treat the claim as a flag to re-probe, not as evidence.

## Evidence requirements

Each finding must name both statements (or the statement and the referenced source) with their locations in the artifact, quote the conflicting text, and state which one is authoritative or how to reconcile them.

Report problems only. No positive observations.
