# Plan: keep durable project docs independent of configurable artifact paths

Backlog origins (scope of record):
- docs/history/backlog/2026-10-14-configurable-artifact-paths-in-docs.md

Driving force: code-quality
(the plans-skill closed taxonomy has no docs/maintainability entry; the origin's "docs + maintainability" is code-quality here - durable documentation stops drifting from configured artifact homes.)

Plan review record: the staging series .ai-playbook/reviews/2026-10-15-plan-review-configurable-artifact-paths-in-docs-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 1h total, largest task 0.5h

## Terms

- durable project documentation: committed, human-facing project prose that states policy, concepts, or workflow for future readers (READMEs, guides, runbooks) - not generated artifacts and not historical records.
- configurable artifact home: a review, certification, metrics, or scratch location that resolves from per-user or per-repository facts configuration (facts keys, facts documents) and is owned by a shared workflow skill; the concrete value is machine-local.
- duplication-of-workflow-guidance defect: durable prose that copies a configurable artifact home's concrete value or a temporary configuration detail, creating a second, drifting statement of what the owning skill or facts source already defines.
- documentation lens: `agents/skills/review-agents/documentation.md`, the review-agents catalog's delegated owner of documentation prose review and of the existing prose-consolidation pattern.
- conditional archive-lookup leg: the origin's second observation (closeout reported historical references absent from its current lookup) - in scope only if the miss is independently reproduced against the configured home and archive source.
- closeout: the done skill's landing/closeout ceremony; its live-corpus check treats an absent reference as a non-blocking reconstruction duty.
- docs-branch: the docs-branch sync skill that owns the archive-branch source of historical records.
- live-corpus: the current, configured artifact homes the closeout checks read.
- covered flip: the `--mark-covered` rider that records a plan as the covering witness on a completed origin row.
- doors gates: the two mandated scripts for `agents/skills/review-agents/` changes (portability checker, door-pattern registry tests).

## Why

A consumer project's durable documentation duplicated exact local artifact locations although those locations resolve from configuration and the shared skills own the workflow, so the docs drifted brittle and inconsistent. The cleanup landed consumer-side; the shared authoring and review guidance still lacks the portable rule, and the same report's archive-lookup claim was never verified against the configured home or archive source.

## Gist & Examples

TLDR: the documentation lens learns to flag durable project prose that copies configurable artifact locations or temporary configuration values, pointing at the owning facts source or skill instead - code-quality, shared review guidance closes the witnessed duplication class.

Before: a guide states "review records live in `<repo>/.ai-playbook/reviews/`"; a consumer's facts resolve reviews elsewhere; the prose silently drifts and nothing in review guidance classifies it.

After: the lens recognizes the added or changed prose as duplication of workflow/configuration guidance, cites the owning source, and proposes pointing at the owner; the closeout archive-lookup contract changes only on an independently reproduced miss.

## Outcome

Review guidance identifies durable-documentation duplication of configurable artifact locations as a prose defect with a concrete disposition, and the archive-lookup leg stays contractually gated on reproduction.

- The documentation lens classifies the witnessed prose shape (pattern tag, disposition, rationale) beside its existing consolidation pattern.
- `agents-best-practices` is recorded as the rejected home with the scoping evidence; no vendored file is edited.
- The closeout live-corpus contract and docs-branch archive lookup are unchanged; the conditional leg's reproduction precondition and independent-origin routing are recorded.

Gate delta: none - one review-lens guidance/check block is added to an existing catalog file (no new refusal class, hard gate, fence, protocol layer, or schema field, and no task pauses dispatch or later work); the fix-class origin-cited no-exit justification applies (the dispatching PLAN-PROMPTS entry records the alternatives and why each fails).

## Assumptions

- `agents/skills/agents-best-practices/SKILL.md` is vendored upstream (frontmatter `upstream:`) with a provider-neutral-agent-harness scope; it owns neither project-document conventions nor documentation review, and a local fork there would be overwritten by upstream sync; basis: the skill's own frontmatter and scope line, and the origin's rejected alternative.
- The repo-local shared guidance surface that owns documentation prose review is the documentation lens; the authoring principle lands as that check's stated rationale, and consumer-side canonical authoring guidelines remain the external home of the authoring rule; basis: the lens's own delegation paragraph and the origin's Expected.
- The archive-lookup miss is not reproducible from this repository (the witness is consumer-local and the historical documents were left unchanged); the done contract already treats an absent live-corpus reference as a non-blocking reconstruction duty, so no closeout or docs-branch change ships here; basis: the origin's Problem and the done skill's current contract.
- The lens addition extends the existing consolidation guidance in place; no deletion pairs with it because no superseded sentence exists - the block absorbs the witnessed shape into the pattern that already owns prose duplication; no second documentation surface is added.
- Review-layer execution duty: the executor runs the Validation Commands battery before landing; this restates Task 2's acceptance items and existing execute-plan law, so no separate blocking-duty declaration is made.

Decision points requiring a grill: none remain: the dispatching PLAN-PROMPTS entry is the confirmed design (operator-directed investigate pass, rejected alternatives recorded 2026-10-14); the taken arm is the lens check with its rationale and the recorded home adjudication, with the entry's other arms rejected - review-check-only is absorbed because the lens carries the rationale with the check, consumer-local-only leaves the cross-project rule unspecified, a validator or gate has no witnessed recurring catch, and changing closeout archive lookup lacks an independently reproduced miss

## Standing constraints

- Never push to origin; stage by explicit path only; never amend a commit reachable from main.
- The hygiene scan (exit 0) runs before every commit; no em-dashes and no absolute personal home directory paths in committed files.
- Bounded repair only: never edit a gate or validator mid-lane to unblock the lane.

## Evaluation Criteria

**Quality dimensions:**
- portability: the check names no tool, agent product, or machine-specific path.
- precision: legitimate audience-specific content and genuinely stable public URLs are not flagged.
- simplicity: one guidance/check block in one existing catalog file; no new surface.

**Done when:**
- the Validation Commands battery exits 0, including the review-agent portability and doors gates mandated for `agents/skills/review-agents/` changes.

**Ship when:**
- the landing carries the lens change and the origin row's covered flip; no external release condition remains.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/review-agents/documentation.md`

**Documentation:**
- `docs/history/backlog/2026-10-14-configurable-artifact-paths-in-docs.md` *(covered-flip rider)*
- `docs/history/backlog/PLAN-PROMPTS.md` *(landing prune rider, its own entry only)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Tests:**
- `scripts/check_review_agent_portability.py`
- `scripts/test_review_agent_doors.py`

**Out of scope; reject unless plan-related:**
- `agents/skills/agents-best-practices/SKILL.md`; reason: vendored upstream, harness-design scope, rejected home (Assumptions)
- `agents/skills/done/SKILL.md` and the docs-branch sync surfaces; reason: the archive-lookup leg is gated on an independently reproduced miss this plan does not have
- `README.md` and the review-agents catalog indexes; reason: the change adds no skill, door pattern, or catalog entry, only lens-internal guidance

## Validation Commands

Validation preamble (authoring-time mechanical audit): pre-round structural gate OUTCOME: pass; no-em-dash scan over the plan bytes (touched): clean; public-hygiene scan: clean.
Round-start state for r1: this commit.

Run from the repository root (the executor's checkout of this plan):

- `python3 scripts/check_review_agent_portability.py`
- `python3 scripts/test_review_agent_doors.py`
- `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-15-configurable-artifact-paths-in-docs.md`
- `bash scripts/check-no-em-dash.sh touched`
- `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh`

### Task 1: documentation-lens duplication check for configurable artifact paths

- [x] The documentation lens classifies the witnessed shape: given phase-2 prose review over durable project documentation that states a configurable artifact home's concrete value or a temporary configuration detail, expects a finding that names it duplication of workflow/configuration guidance, cites the owning facts source or skill, and never invents a project-specific path. [class: IMPLEMENTATION_REQUIRED]
- [x] The check rides the existing consolidation pattern: given the lens's decision-restated/consolidation guidance, expects the new block placed beside it with the same disposition vocabulary (point at the single owner, replace the copy with a reference), the pattern tag form `documentation#prose-local-artifact-paths`, and the abstract authoring principle (durable docs state policy and stable concepts; configuration facts stay in facts sources) as its rationale. [class: IMPLEMENTATION_REQUIRED]
- [x] Portability and precision guards hold: given the added block, expects tool-agnostic wording, no flagging of legitimate audience-specific content or genuinely stable public references, and no new validator, gate, or panel duty. [class: IMPLEMENTATION_REQUIRED]

Files:
- agents/skills/review-agents/documentation.md

Primary class anchors:
- `Documentation Agent` in `agents/skills/review-agents/documentation.md`

### Task 2: validation battery over the lens change

- [x] Mandated review-agents gates pass: given the Task 1 edit, expects `python3 scripts/check_review_agent_portability.py` and `python3 scripts/test_review_agent_doors.py` each exit 0. [class: REPOSITORY_TEST]
- [x] Plan and prose gates pass: given the final bytes, expects the readiness gate, the no-em-dash touched scan, and the public-hygiene scan each clean. [class: REPOSITORY_TEST]

Files:
- agents/skills/review-agents/documentation.md
- scripts/check_review_agent_portability.py
- scripts/test_review_agent_doors.py

### Task 3: origin disposition and landing riders

- [x] Origin row covered: given the origin row completed by this plan, expects `--mark-covered` to flip its `Status:` to covered naming this plan as the covering witness, riding the landing as a rider commit. [class: IMPLEMENTATION_REQUIRED]
- [x] Entry pruned with receipt: given the landing flow, expects the frozen PLAN-PROMPTS entry pruned by the landing rider with its `PLAN-PROMPTS-PRUNE:` receipt line and the prune audit passing. [class: IMPLEMENTATION_REQUIRED]

Files:
- docs/history/backlog/2026-10-14-configurable-artifact-paths-in-docs.md
- docs/history/backlog/PLAN-PROMPTS.md
