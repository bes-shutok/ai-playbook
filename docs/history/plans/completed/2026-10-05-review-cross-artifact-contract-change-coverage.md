# Plan: review contract-impact closure for unchanged dependent artifacts

Backlog origin: docs/history/backlog/2026-10-05-review-cross-artifact-contract-change-coverage.md
Driving force: reliability (not one of the five driving principles; implemented because the witnessed failure shipped consumer-visible contract defects to external review, and the origin's Consumer urgency header classifies it real and never profile-deferred)
Plan review record: the staging series docs/reviews/2026-10-05-plan-review-review-cross-artifact-contract-change-coverage-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Terms

- contract-impact closure: the new phase-1 duty that enumerates the directly dependent example and source-reference surfaces of a changed public contract invariant and replays or reconciles each against the changed invariant.
- dependent artifact: a document that names or depends on a changed contract invariant (a normative example, a schema summary, a migration or executable-definition pointer).
- read-set: the files a review worker must read before reporting; here the diff plus the enumerated dependent artifacts.
- out-of-diff finding: a finding on a document the change does not modify; it carries no diff line anchor and is never posted inline.
- review body: the PR-level review summary comment surface, as opposed to inline diff comments.
- boundary-contract checklist: the review metadata checklist required by the coverage floor in agents/skills/review-agents/review-panel-selection.md; this plan adds one family to it.
- contract-docs: the review worker that loads the documentation lens, and after this plan the consistency lens when the closure trigger fires.
- normative example: a request/response sample, config snippet, or mode-rule illustration that consumers may copy as contract.
- executable definition: the migration chain and generated schema contract that is the authoritative source a schema paragraph must point to.
- staging doc: the local review record under the reviews directory; internal scratch that is never posted.
- lens: a review agent's checking catalog (documentation, consistency).
- pinned span: a verbatim multi-word text fragment the declaration fixture asserts against a target file with a fixed-string containment check.
- declaration fixture: the RED-first unittest suite (`scripts/test_review_contract_impact_closure.py`) that pins the prescribed declarations before the prose lands.

## Why

A tightened public contract can invalidate normative examples and schema-source references in directly related but unchanged documents. Today's review boundary drops those defects: the example-replay duty covers changed examples only, and the unchanged-document rule tells reviewers not to raise what they notice. The witnessed gap shipped an invalid identifier example and a stale migration pointer past a full internal panel and was caught only in external review.

## Outcome

When a change tightens a public contract, the contract-docs reviewer replays directly dependent unchanged examples against the changed invariant, reconciles their schema-source references, and reports out-of-diff contract-impact findings through the review body without inline comments or silent drops.

- Dependent unchanged examples are replayed against the changed invariant, including version and variant constraints and equivalent format restrictions.
- Stale executable-definition references in dependent documents are reconciled against the complete migration chain and routed for a separate fix.
- Out-of-diff contract-impact findings reach the author through the review body and a separate follow-up, never dropped and never posted inline.
- Gate delta: grows the contract-docs lens's checked-condition set (the contract-impact closure duty), adds one boundary-contract checklist family, and adds one doing-code-review out-of-diff disposition route; no refusal class, hard gate, fence, protocol layer, or schema state field is added, and nothing is removed. Priced by the cited completed-integrity-failure witness: the external-review escape recorded in the origin backlog item, where a full panel with the contract-documentation worker complete and the related specification already named in its boundary-contract checklist still shipped the defects. The review-layer duty declared here does not block a review run; it produces findings through the routed surfaces.

## Assumptions

- assume the out-of-diff route of record stages each contract-impact item as a finding row anchored to the unchanged document's section heading (review-staging's Anchor field carries section-heading anchor text, so no diff line anchor is needed), posts one consolidated PR review body finding (the doing-code-review section 4.9.0 out-of-diff telemetry precedent, mirrored as a posting-step exception), and routes the tracked-document fix to a separate follow-up (section 4.9.2); basis: the authoring survey found no existing out-of-diff route for this class (today the defect class is discarded as out-of-scope and the unchanged-document rule forbids inline comments), while those three surfaces already exist and need only the class-specific instruction.
- assume the fixture form is the repository's established lens-declaration suite (the scripts/test_review_agent_doors.py precedent) rather than a live review-run simulation; basis: the review pipeline is prompt-driven, the repository AGENTS.md mandates the doors and portability suites as the mechanical gates over review-agents changes, and no in-repo harness launches live review panels.
- assume no severity-calibration change is needed; basis: severity defaults already cover documentation findings and the origin names no severity defect.
- assume the consistency lens reaches code reviews only through the contract-docs worker's conditional-lens cell, so the cell change is what makes the cross-artifact drift arm reachable outside plan and RFC reviews; basis: the five-worker table in review-panel-selection.md marks consistency conditional on plans and RFCs today.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: Reviews close contract impact into unchanged dependent artifacts, so a tightened contract cannot leave an invalid example or a stale reference behind; closes the witnessed external-review escape (reliability).

**Before (today):** A PR tightens an identifier format to require a specific UUID version and variant and adds a newer executable definition for the schema. An unchanged specification still shows an identifier example of the wrong UUID version, keeps a permissive pattern the new rule rejects, and names an older migration as the executable definition. The full panel runs with the contract-documentation worker complete; the boundary-contract checklist even names the related specification. The replay duty covers only examples changed in the diff, and the unchanged-document rule forbids commenting on the specification, so nothing fails internally. External review reports all three defects.

**After (this plan):** The same PR triggers contract-impact closure: the reviewer enumerates the directly dependent surfaces (the checklist already names the specification), replays its example against the new version-and-variant rule, reconciles its schema paragraph against the migration chain, and posts one consolidated contract-impact finding in the review body naming the document, the invalidated statements, and the changed invariant; the document fix routes to a separate follow-up. No inline comment on the unchanged document is attempted, and nothing is silently dropped.

Edge cases: a dependent document that already satisfies the new invariant yields no finding; artifacts without a direct dependency never enter the read-set; a plan or RFC review gets the same closure through the consistency lens when the trigger fires.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the declaration fixture passes; every pinned span occurs exactly once in its target file.
- regression safety: the preserved-rule pins stay green (the changed-example replay scope in documentation.md, the inline ban in doing-code-review section 4.9.2); the portability and doors suites exit 0.
- scope discipline: the bounded-read-set boundary spans are present in both lenses (never a repository-wide documentation freshness scan; only via the contract-impact closure trigger).

**Done when:**
- `( cd "$REPO" && python3 scripts/test_review_contract_impact_closure.py )` exits 0.
- The full Validation Commands block exits 0 on the executed tree.

**Ship when:**
- Consumer repositories pick the updated skills up on their next vendored sync; no further human action is required in this repository.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/review-agents/documentation.md` (the region between the normative example replay subsection and the plan and RFC prose subsection; all other sections are frozen; reject any review finding that touches them)
- `agents/skills/review-agents/consistency.md` (the Loaded-by header line, the Scope paragraph's final sentence, and the new cross-artifact contract drift subsection; all other sections are frozen)
- `agents/skills/review-agents/review-panel-selection.md` (the contract-docs table row, the boundary-contract coverage floor paragraphs, and the cross-artifact contract drift row in the Tiered ownership table; all other sections are frozen)
- `agents/skills/doing-code-review/SKILL.md` (section 4.9.2, and the contract-impact exception line in the Direct Mode section's posting exception list; all other sections are frozen)

**Tests:**
- `scripts/test_review_contract_impact_closure.py` *(new)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/validate_review_staging.py`; reason: no staging-schema change is prescribed; the route uses existing summary and review-body surfaces.
- `agents/skills/review-agents/severity-calibration.md`; reason: no severity-table change is prescribed.
- `scripts/test_review_agent_doors.py` and `scripts/check_review_agent_portability.py`; reason: consumed as gates, not edited.
- `agents/skills/review-loop/SKILL.md` and `agents/skills/execute-plan/`; reason: loop exit criteria and plan-execution flow are unchanged.

## Validation Commands

Authoring-time evidence (rule 29 pre-round): the plan bytes passed `python3 scripts/plan_readiness.py --pre-round` with exit 0 and `OUTCOME: pass` in the authoring worktree; the rule 19 RED-today probe ran each pinned span with grep against the four target files at the authoring base (the 15 new-duty spans returned no match; the three preserved spans matched); the rule 22 mechanical audit verified every pinned span occurs exactly once in its owning surface's prescribed snippet (the two deliberately cross-surface spans checked per owning snippet) and `bash -n` accepted the Validation Commands block. Round-start state for r1: authoring worktree ai-playbook-wt-rccc, branch 2026-10-05-review-cross-artifact-coverage, plan bytes at the draft commit.

```bash
REPO="$(git rev-parse --show-toplevel)"
( cd "$REPO" && python3 scripts/test_review_contract_impact_closure.py -v )
( cd "$REPO" && python3 scripts/check_review_agent_portability.py )
( cd "$REPO" && python3 scripts/test_review_agent_doors.py )
( cd "$REPO" && bash scripts/check-no-em-dash.sh added-lines --base main )
( cd "$REPO" && bash ~/.ai-playbook/scripts/scan-public-hygiene.sh )
```

### Task 1: Pin the declaration contract (RED fixture suite)

Files:
- `scripts/test_review_contract_impact_closure.py` *(new)*

Evidence:
- `( cd "$REPO" && python3 scripts/test_review_contract_impact_closure.py )`; covers the RED-today criterion: the four declaration tests fail on the absent spans while the preserved-boundaries test passes

- [x] Create `scripts/test_review_contract_impact_closure.py` as a unittest module that resolves the repository root from its own file location (`Path(__file__).resolve().parents[1]`) and reads the four target files from it; every span assertion quotes the verbatim span the Task 2 prose prescribes, asserted with a fixed-string containment check against the whole file bytes [class: REPOSITORY_TEST]
- [x] `ReviewContractImpactClosureTest#test_documentation_lens_declares_contract_impact_closure`; given agents/skills/review-agents/documentation.md, expects the file to contain all of: `### Contract-impact closure (phase 1)`, `changes a public contract invariant`, `directly dependent example and source-reference surfaces`, `documentation#missing-contract-impact-replay`, `contract-impact exception`, and `never a repository-wide documentation freshness scan` [class: REPOSITORY_TEST]
- [x] `ReviewContractImpactClosureTest#test_consistency_lens_declares_cross_artifact_drift`; given agents/skills/review-agents/consistency.md, expects the file to contain all of: `### Cross-artifact contract drift`, `enters the consistency read-set only via the contract-impact closure trigger`, and `consistency#stale-schema-source-reference` [class: REPOSITORY_TEST]
- [x] `ReviewContractImpactClosureTest#test_panel_selection_carries_trigger`; given agents/skills/review-agents/review-panel-selection.md, expects the file to contain all of: `for plans and RFCs and when contract-impact closure triggers` and `changed public contract invariant is a boundary-contract family` [class: REPOSITORY_TEST]
- [x] `ReviewContractImpactClosureTest#test_doing_code_review_declares_out_of_diff_route`; given agents/skills/doing-code-review/SKILL.md, expects the file to contain all of: `Contract-impact exception (out-of-diff route)`, `one consolidated contract-impact finding in the PR review body`, `Never post it as an inline comment`, and `route the tracked-document fix to a separate follow-up` [class: REPOSITORY_TEST]
- [x] `ReviewContractImpactClosureTest#test_preserved_boundaries_stay_pinned`; given the four target files, expects the preserved spans `For every changed normative example in the diff` (documentation.md replay scope), `Do not comment on it in the PR` (doing-code-review section 4.9.2 inline ban), and `drop or move to a separate PR` (doing-code-review section 4.9.2 quick gate, whose drop disposition the contract-impact exception overrides for its class) to remain present [class: REPOSITORY_TEST]
- [x] Run → expect RED: `( cd "$REPO" && python3 scripts/test_review_contract_impact_closure.py )` fails with the four declaration tests erroring or failing on the absent spans, while `test_preserved_boundaries_stay_pinned` passes [class: REPOSITORY_TEST]
- [x] Commit: `test: pin the contract-impact closure declaration contract (RED)` [class: REPOSITORY_TEST]

### Task 2: Declare the duty across the four surfaces (GREEN)

Files:
- `agents/skills/review-agents/documentation.md`
- `agents/skills/review-agents/consistency.md`
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/doing-code-review/SKILL.md`

Evidence:
- `( cd "$REPO" && python3 scripts/test_review_contract_impact_closure.py )`; covers the GREEN criterion: all fixture tests pass
- `( cd "$REPO" && python3 scripts/check_review_agent_portability.py )`; covers the regression-safety criterion: the shared catalogs stay free of stack-specific tokens
- `( cd "$REPO" && python3 scripts/test_review_agent_doors.py )`; covers the regression-safety criterion: the door registry stays green beside the new subsections

- [x] Insert the following subsection into `agents/skills/review-agents/documentation.md` immediately before the heading `### Plan / RFC prose (phase 1)` (that heading is the unique anchor; the insertion starts with its own heading line) [class: IMPLEMENTATION_REQUIRED]

```markdown
### Contract-impact closure (phase 1)

When the diff changes a public contract invariant (a schema constraint, an API schema shape, a migration, or a canonical source reference), the replay duty above extends from changed examples to the invariant's directly dependent artifacts:

- Enumerate the **directly dependent example and source-reference surfaces**: normative examples, schema summaries, and migration or executable-definition pointers in documents that name or depend on the changed invariant. The boundary-contract checklist's related documents and a reference search on the invariant's name are the discovery inputs; the read-set stays bounded to that dependency set. This is never a repository-wide documentation freshness scan.
- **Replay** each dependent unchanged example against the changed invariant exactly as the changed-example replay prescribes (validate against the active rule, including version and variant constraints and equivalent format restrictions), and **reconcile** each dependent schema or executable-definition reference against the complete migration chain and generated schema contract.
- A dependent example the changed invariant rejects, and a dependent reference the changed contract supersedes, are findings even though their documents are unchanged: use pattern `documentation#missing-contract-impact-replay`, state in the finding body that the artifact is out of the diff, and route per the orchestrator's contract-impact exception (`doing-code-review` section 4.9.2). Inline anchors are never attempted on unchanged documents.

Scope boundary: only artifacts with a direct contract dependency enter the read-set; unrelated docs, broad freshness sweeps, and unrelated reviewer lenses stay out of scope.
```

- [x] Insert the following subsection into `agents/skills/review-agents/consistency.md` immediately before the heading `## Invalid validation claims` (that heading is the unique anchor; as the only H3 in the file it deliberately nests the drift arm under the Source-of-truth drift section, its parent family) [class: IMPLEMENTATION_REQUIRED]

```markdown
### Cross-artifact contract drift

When a changed public contract invariant supersedes a normative statement in a directly dependent artifact (a schema paragraph naming an older migration as the executable definition, a table sketch the new schema rejects), the drift between the changed contract and the dependent statement is a finding here: name both statements and their locations, quote the conflicting text, and state which is authoritative (the changed contract) and what reconciliation the dependent document needs.

The dependent artifact enters the consistency read-set only via the contract-impact closure trigger (`documentation.md` phase 1); unrelated documents and broad freshness sweeps stay out of scope. Findings use pattern `consistency#stale-schema-source-reference` and route through the contract-impact exception (`doing-code-review` section 4.9.2).
```

- [x] In `agents/skills/review-agents/consistency.md`, amend the two frozen scope lines so they admit the new arm: replace the header paragraph's final sentence (the span below is the line's tail sentence, not a standalone line; the paragraph's opening sentence is kept and nothing after the span is dropped) with the new sentence below it [class: IMPLEMENTATION_REQUIRED]

```markdown
Loaded by `contract-docs` in plan and RFC reviews per `review-panel-selection.md`.
```

```markdown
Loaded by `contract-docs` in plan and RFC reviews, and when contract-impact closure triggers per `review-panel-selection.md`.
```

and replace the Scope paragraph's final sentence (the span `It does not judge runtime code.` ends at a sentence terminator; the replacement ends with the same period and nothing after it is dropped) with:

```markdown
It does not judge runtime code; directly dependent documents pulled in by the contract-impact closure trigger (`documentation.md` phase 1) join the compared statements.
```

- [x] In `agents/skills/review-agents/review-panel-selection.md`, replace the following pre-image line (the full unique contract-docs row; the rest of the table untouched) with the new row below it [class: IMPLEMENTATION_REQUIRED]

```markdown
| `contract-docs` | `documentation` | `consistency` for plans and RFCs | Contracts, source-of-truth drift, prose, cross-section consistency |
```

```markdown
| `contract-docs` | `documentation` | `consistency` for plans and RFCs and when contract-impact closure triggers (duty: `documentation.md` phase 1) | Contracts, source-of-truth drift, prose, cross-section consistency |
```

- [x] Insert the following paragraph into `agents/skills/review-agents/review-panel-selection.md` between the coverage-floor paragraph ending `safety-boundary test.` and the paragraph starting `The worker may record` (both anchors unique) [class: IMPLEMENTATION_REQUIRED]

```markdown
A changed public contract invariant is a boundary-contract family: the checklist names the directly dependent example and source-reference surfaces (the contract-impact closure read-set, `documentation.md` phase 1), and an unnamed dependent surface degrades coverage like any other family.
```

- [x] In `agents/skills/review-agents/review-panel-selection.md`, append one row to the Tiered ownership (dedup, not discard) table immediately after the row beginning `| Plan or RFC internal contradiction` (that row is the unique anchor) so dedup lead selection covers the new class [class: IMPLEMENTATION_REQUIRED]

```markdown
| Cross-artifact contract drift after a changed public contract | `contract-docs` | `consistency` |
```

- [x] Insert the following paragraph into `agents/skills/doing-code-review/SKILL.md` in section 4.9.2, immediately before the bold line `**Personal style preferences are never a PR comment, regardless of doc status.**` (that line is the unique anchor) [class: IMPLEMENTATION_REQUIRED]

```markdown
**Contract-impact exception (out-of-diff route):** when the contract-impact closure duty (`review-agents/documentation.md` phase 1) produces a finding on a document that is NOT in the diff, the finding is not silently dropped: stage each as a finding row anchored to the unchanged document's section heading (record the document path in File, the section heading in the Anchor field per `review-staging`, and omit the diff Line item for this class), and post one consolidated contract-impact finding in the PR review body (the same out-of-diff surface section 4.9.0 gives telemetry findings, and the Direct Mode posting exception list carries the matching exception), naming the unchanged document, the invalidated statement, and the changed invariant that supersedes it. Never post it as an inline comment, and route the tracked-document fix to a separate follow-up (or the document owner) per the unchanged-document rule above. The quick gate below keeps its inline-scope verdict, and its drop-or-move disposition does not apply to this class: an out-of-diff contract-impact finding goes to the review body, never dropped and never to an inline anchor.
```

- [x] Insert the following exception line into the posting exception list in the Direct Mode section of `agents/skills/doing-code-review/SKILL.md`, immediately before the bold line `**Exception; multi-key deploy checklists:**` (that line is the unique anchor) so the closed posting exception list admits the mandated body route and the body finding survives the posting step's landing verification [class: IMPLEMENTATION_REQUIRED]

```markdown
**Exception; out-of-diff contract-impact findings:** one consolidated PR review body comment for contract-impact findings on unchanged documents (see §4.9.2); the consolidated body finding is exempt from the per-line landing receipt (verify it by fetching the PR review body and counting the fragment present), the inline recovery pass never re-posts it, and the exempt finding row's Status stays `pending` (it is not part of the per-line receipt census) with the verified body-fragment count recorded in its Analysis section.
```

- [x] Run → expect GREEN: `( cd "$REPO" && python3 scripts/test_review_contract_impact_closure.py )` passes all five tests; `python3 scripts/check_review_agent_portability.py` exits 0; `python3 scripts/test_review_agent_doors.py` passes its suite [class: REPOSITORY_TEST]
- [x] Commit: `feat: declare contract-impact closure across the review lenses and the orchestrator route` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Full validation and boundary sweep

Evidence:
- The full `## Validation Commands` block; covers every Done-when criterion on the executed tree

- [x] Run → expect GREEN: the full Validation Commands block exits 0 line by line; the em-dash added-lines scan and the hygiene scan report no findings on the changed files [class: REPOSITORY_TEST]
- [x] Verify span uniqueness: for each span pinned in Task 1, `grep -cF` over its target file returns exactly 1 [class: REPOSITORY_TEST]
- [x] Run `python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-review-cross-artifact-contract-change-coverage.md`; expect exit 0 with `OUTCOME: pass` at the certification boundary [class: REPOSITORY_TEST]

## Disposition

Executed 2026-10-06 in worktree ai-playbook-wt-rcc (branch plan-review-cross-artifact-contract-exec) by the standing maintenance execution lane. Task 1 (ee2eece8): scripts/test_review_contract_impact_closure.py pins the five-test declaration contract with the prescribed RED split. Task 2 (3b60a38e): all eight prescribed edits land verbatim at their unique anchors across agents/skills/review-agents/documentation.md, consistency.md, review-panel-selection.md, and agents/skills/doing-code-review/SKILL.md, with the three pre-image spans absent after the edit and a mechanical block-by-block comparison against the plan's eleven fenced blocks returning zero mismatches.

Validation: the declaration selftest 5/5 OK; check_review_agent_portability.py exit 0; test_review_agent_doors.py 16/16 OK; pins suite exit 0; em-dash added-lines scan and hygiene scan exit 0; all twenty pinned spans exactly once at occurrence granularity. Exec review r5 (fresh-adversarial, one worker) found zero blocking findings with one Low accepted (the body-fragment verification claim names no existing shared primitive; plan-origin, future alignment) and three informational plan-bound notes; records at docs/reviews/2026-10-05-plan-review-review-cross-artifact-contract-change-coverage-r5.{md,stats.json} plus the r6 certification probe.

Deferred residuals: the r5 Low above; the quick-gate carve-out asymmetry and the phase-1 pointer ambiguity remain plan-bound informational notes. Origin row docs/history/backlog/2026-10-05-review-cross-artifact-contract-change-coverage.md is covered by this execution and folded in the landing.
