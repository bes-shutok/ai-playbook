# Plan: Single-home the Primary class anchors grammar and enforce it at the authoring gate

Backlog origin: docs/history/backlog/2026-10-09-primary-class-anchors-grammar-drift.md
Driving force: code-quality
Plan review record: the staging series docs/history/reviews/2026-10-09-plan-review-primary-class-anchors-grammar-drift-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 2.75h total, largest task 1.25h

## Terms

- Primary class anchors: the per-task block in a plan naming the production identifier that owns the task's behavior, one entry per bullet.
- Entry grammar: the shared regex `PRIMARY_CLASS_ANCHOR_ENTRY` (public name at its single home): `- `ClassName` in `path``, both tokens backticked, optionally followed by a comma and prose; single-homed in `scripts/plan_shape.py` by this plan.
- Anchors parser: the task-section extractor plus the anchors block loop (heading literal, blank-line termination, bullet scan, `fullmatch` on the stripped line); single-homed in `scripts/plan_shape.py` by this plan, consumed by both the runtime and the readiness probe.
- Canonical shape constant: the shared string `PRIMARY_CLASS_ANCHOR_SHAPE` in `scripts/plan_shape.py` naming the entry form; both refusal messages interpolate it.
- Prose-form entry: an anchors bullet naming its subject as a descriptive phrase without the backticked identifier-in-path shape; the runtime refuses it at manifest `create`.
- Manifest `create`: the runtime driver's create operation, where anchors parsing and discovery seeding run at execution start.
- Execution seeding: the create boundary's discovery step that turns each task's declared anchors into the worker's allowed paths and criteria.
- Execution claim: the per-run claim file an execution run takes before any plan work.
- Transfer-in: copying the run's gitignored inputs (facts, reviews) into a fresh worktree before work starts.
- Worktree-first standard: the execute-plan skill section mandating every plan run works in an ad-hoc worktree on its own branch.
- Readiness pre-round gate: `python3 scripts/plan_readiness.py --pre-round <plan>`, the cheap authoring-side gate run before each review round.
- Doctrine plan: `docs/history/plans/2026-10-08-quota-wall-dispatch-doctrine.md`, the certified plan stuck at `create` on its prose-form anchors.
- Semantic plan-edit path: the skill-gated edit of a certified plan's bytes plus a fresh whole-plan review round in that plan's own review series before dispatch.
- Sidecar digest: the review sidecar's `source_digest` hash over the plan's current bytes; a mismatch refuses the plan at the gates that consult reviews.
- Owner fingerprint: the readiness selftest assertion that the symbol the plans skill prose names still exists, as a definition, in the grammar's single home.
- Backlog rider: a follow-up backlog row filed by a running plan for work causally adjacent to but outside its declared scope.
- Identity witness: the Task 1 assertion pair proving both consumers run the moved parser objects (`is`-equal, no local definition).
- Behavioral fixture: a readiness selftest anchors case (prose-form refused, conforming accepted, blockless unaffected, blank-line boundary, fenced refusal, subsection read-through, non-task section ignored, second-section enumeration).
- Refusal-suffix fixture: the Task 3 test asserting the malformed-entry message ends with the canonical shape.
- Guard liveness ledger: the catch-to-incident accounting printed by `python3 scripts/gate_liveness_ledger.py show`.
- No-exit justification: the origin-recorded rejection of the class-default alternatives pricing a refusal-path addition.
- Dispatch entry: the item's entry in `docs/history/backlog/PLAN-PROMPTS.md` carrying the prompt of record and the rejected alternatives.
- Single-file plan shape: a plan stored as one Markdown file at the plans root, today's only shape in use; the directory shape stores a charter plus per-task files.
- Single-home witness: the Task 1 readiness selftest assertion that no second definition of the grammar literals exists outside `scripts/plan_shape.py`, distinct from the Identity witness.
- Refusal class: a family of gate refusal counted in the Gate delta ledger; this plan adds one.
- Fence-blindness: scanning raw section text without excluding fenced example blocks, which the runtime parser does and the probe mirrors.
- D-record shape: the operator-directives record format (issued, status, expiry, scope, directive, superseded_by, witness) the doctrine plan's anchors entry points at.

## Why

The runtime refuses prose-form anchors at execution seeding, after the execution claim and transfer-in are done, while the plans skill's own prose teaches the prose form and no authoring gate validates the grammar, so the doctrine plan is stuck at `create` today. The fix completes the mechanism's authoring-side complement: one grammar and one parser in one home, taught correctly, enforced at the earliest cheap boundary, with a self-remedying refusal.

## Gist & Examples

TLDR: the anchors entry grammar and its parser single-homed in the shared plan module and refused at the readiness pre-round gate, with the plans skill prose and the discovery refusal teaching the shared shape, a code-quality fix for a contract drift that passes authoring today and fails at execution seeding (driving force: code-quality).

Before: a plan certifies with `- The Sub-Agent Launch Rules dispatch-mode paragraph in agents/skills/execute-plan/SKILL.md`, then the driver's `create` refuses: `discovery refused the Primary class anchors block: malformed Primary class anchors entry: ...`.

After: the readiness pre-round gate refuses the same entry with the canonical shape named, the plans skill prose states the runtime-owned form and the identifier rule by reference to the grammar's single home, the discovery refusal appends the same shared shape, and the doctrine plan is dispositioned through the semantic plan-edit path so its execution start passes seeding.

## Outcome

For the single-file plan shape (today's only shape in use), a plan passing the readiness pre-round gate's anchors check passes execution seeding's anchors block, and a malformed entry is refused in seconds at authoring with the fix stated in the refusal.

- The readiness pre-round gate refuses any present anchors block carrying a prose-form entry, naming the canonical shape, wired solely into the pre-round probe chain; and a plan (single-file shape, today's only shape in use) passing the anchors check passes execution seeding's anchors block.
- The plans skill's anchors prose states the runtime-owned form and the repository-verifiable identifier rule by reference to the grammar's single home in `scripts/plan_shape.py`.
- The discovery refusal for a malformed entry appends the same canonical shape from the same shared constant, so an execution-side refusal is self-remedying.
- The doctrine plan's prose-form anchors are converted or removed through the semantic plan-edit path and re-certified in its own review series, unblocking its dispatch.

Gate delta: one refusal class added, the readiness pre-round probe chain gains the anchors-block grammar check (a new probe, `anchors_block_problem`, wired solely into `run_pre_round`'s probe chain; the full gate's posture unchanged); priced by this fix-class origin's no-exit justification naming the class-default alternatives: add the sanctioned exit is answered by the sanctioned exit that already exists (the execute-plan skill's create-boundary remedy naming the semantic plan-edit path, kept and relocated rather than replaced); remove the false positive is witnessed rejected in the item's dispatch entry (docs/history/backlog/PLAN-PROMPTS.md, section primary-class-anchors-grammar-drift: widening discovery to descriptive phrases makes discovered scope non-deterministic across repo states); simplify the flow is witnessed rejected there (the prose-only correction already failed a witnessed r2-certified plan); a further recorded alternative (a review-layer checklist item) is probabilistic and missed the drift in the witnessed rounds, per the doctrine r2 record's unstaged descriptive-anchor note; the check adds no new restriction, it relocates the runtime's existing `create` refusal to the cheap boundary (context locating the addition, not itself the payment); the guard liveness ledger's catch-to-incident ratio at authoring time, from `python3 scripts/gate_liveness_ledger.py show`, is catches=18 incidents=23 (ratio 18:23, overrides=0). One refusal message grows a suffix interpolated from the shared canonical shape constant (the discovery malformed-entry error), message text, not a new check. The anchors parser (the task-section extractor, the block loop, the heading literal, the entry regex) moves from `scripts/execute_plan_runtime.py` to `scripts/plan_shape.py`, the entry regex renamed to the public `PRIMARY_CLASS_ANCHOR_ENTRY` and the parser function promoted to the public `primary_class_anchors` at their home (the runtime keeps module-local aliases), plus one new shared string `PRIMARY_CLASS_ANCHOR_SHAPE`; the moves are to one home, not second definitions. Prose corrections in the plans skill (the shape sentence and the pre-round enumeration updates) and one teaching-fixture period fix in the review-plan skill, no machinery. No other additions or removals.

## Assumptions

- The runtime grammar and parser are correct as landed and are the single form owners; nothing in this plan widens or weakens them (the origin's rejected alternatives). Test-local re-encodings of the boundary rule for fixture verification (the `_ANCHOR_RE` compiled pattern in `scripts/test_plan_review_boundary_examples.py`) are sanctioned non-definitions, not grammar homes.
- `scripts/plan_shape.py` is the shared home for the anchors parser and shape constant: it is stdlib-only and already imported by both consumers (`scripts/plan_readiness.py` and `scripts/execute_plan_runtime.py`), so the move adds no dependency edge and no mirror.
- Parser parity holds by construction once the parser is shared: both consumers run the same code, and the behavioral fixtures (prose-form refused, conforming accepted, blockless unaffected, blank-line boundary, fenced block refused, subsection content inside the section) pin the shared behavior. The probe reads raw section text exactly like the runtime, so a fenced anchors-block example inside a task section refuses on both surfaces (inherited fence-blindness, parity with `create`, not a new restriction). The single-file plan shape is today's only shape in use; the directory shape's file-identity section selection rides the same shared block loop when directory plans arrive, and the fixtures pin the single-file shape.
- The runtime in-file selftest (`python3 scripts/execute_plan_runtime.py --selftest`) is red at this plan's baseline for an unrelated pre-existing reason (the selftest driver has no Codex model-guard probe adapter, so its claim fixture blocks); this plan does not repair it, Task 3's fixtures live in the green `scripts/test_execute_plan_runtime.py` suite and the red baseline is filed as a backlog rider.
- The doctrine plan's five anchors entries disposition per entry: four subjects have identifiers whose bytes exist at their named paths (converted with named identifiers, the D-record shape subject through its `Record format` definition heading); the per-path pass numbering subject has no identifier bytes at its named path (that bullet is removed, the block stays for its convertible sibling, a task owning no production behavior there).
- The doctrine plan's sidecar digest is already stale at baseline (its r2 sidecar digest predates its current bytes; the full readiness gate refuses on the stale digest today), and the doctrine plan fails the pre-round gate today on twelve untagged checklist items (the classification probe), a second pre-existing drift; the semantic plan-edit path is implicated before Task 4's conversion, and Task 4's r3 round identifies and dispositions the pre-existing post-r2 byte delta including the tag additions, the anchor conversion, and the one bullet removal. The re-cert is a whole-plan review round (panel_mode focused per the doctrine r2 precedent, its selection_reason naming the anchors-grammar re-verification) recorded as r3 in the doctrine plan's own review series, execution work inside Task 4.

Decision points requiring a grill: none remain.

## Standing constraints

- The anchors parser, the two grammar literals, and the canonical shape constant live only in `scripts/plan_shape.py`: the runtime and the readiness probe both import them; no consumer defines a second copy of any of them.
- An anchors class name is a repository-verifiable identifier (a bytes-scan token discovery searches tracked files for), never a descriptive phrase.
- The readiness probe parses through the shared parser, so a readiness refusal implies a `create` refusal; the probe enumerates task ordinals over fence-stripped text and parses each section raw, and `create` refuses whatever its requested ordinals parse.
- Never push to origin; all run work happens in the run's ad-hoc worktree per the Worktree-first standard.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: readiness and execution run the same parser code, proven by the identity witnesses and pinned by the behavioral fixtures.
- Fail-closed behavior: a malformed entry refuses at the gate with a named problem line; a missing block stays unaffected; the full gate's posture is unchanged.
- Maintainability: the code literals (heading, entry regex, shape constant, parser) exist in exactly one file; prose restatements reference the owner by name and are not definitions.

**Done when:**
- `python3 scripts/plan_readiness.py --selftest` exits 0 including the new anchors fixtures (prose-form refused, conforming accepted, blockless unaffected, blank-line boundary, fenced block refused, non-task section ignored, second-section enumeration, full-gate posture unchanged, owner fingerprint, single-home identity).
- `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-09-primary-class-anchors-grammar-drift.md` exits 0.
- `python3 scripts/test_execute_plan_runtime.py -k primary_class_anchors` exits 0 with at least one test run, including the refusal-suffix fixture.
- `python3 scripts/test_execute_plan_runtime.py -k discovery` exits 0 after Task 1's move (the existing discovery family over the moved parser).
- `python3 scripts/test_execute_plan_runtime.py` (full suite) exits 0 after Task 1's move and again after Task 3's suffix.
- `python3 scripts/plan_readiness.py docs/history/plans/2026-10-08-quota-wall-dispatch-doctrine.md` exits 0 after Task 4 (the full gate refusing on the stale digest today).
- `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-08-quota-wall-dispatch-doctrine.md` exits 0 after Task 4.

**Ship when:**
- The doctrine plan passes both `python3 scripts/plan_readiness.py --pre-round` and the full `python3 scripts/plan_readiness.py docs/history/plans/2026-10-08-quota-wall-dispatch-doctrine.md` after Task 4's disposition; its dispatch decision stays the operator's.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/plan_shape.py`
- `scripts/plan_readiness.py`
- `scripts/execute_plan_runtime.py`
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `docs/history/plans/2026-10-08-quota-wall-dispatch-doctrine.md`

**Tests:**
- the in-file selftest of `scripts/plan_readiness.py` *(extended in place)*
- `scripts/test_execute_plan_runtime.py` *(extended in place)*

**Receipts:**
- `docs/history/backlog/2026-10-09-runtime-selftest-model-guard-baseline-red.md` *(new, Task 3 rider)*
- `docs/history/reviews/2026-10-08-plan-review-quota-wall-dispatch-doctrine-r3.md` *(new, Task 4 re-cert)*
- `docs/history/reviews/2026-10-08-plan-review-quota-wall-dispatch-doctrine-r3.stats.json` *(new, Task 4 re-cert sidecar)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- widening the runtime grammar to accept descriptive phrases; reason: rejected in the item's dispatch entry (non-deterministic discovered scope)
- review-agent catalog changes owning the anchors grammar; reason: review is probabilistic and cannot own the guarantee (dispatch entry's rejected alternative)
- repairing the runtime in-file selftest's model-guard blockage; reason: pre-existing, unrelated to the anchors contract; filed as a rider by Task 3

## Validation Commands

```bash
python3 scripts/plan_readiness.py --selftest
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-09-primary-class-anchors-grammar-drift.md
python3 scripts/test_execute_plan_runtime.py -k primary_class_anchors
python3 scripts/test_execute_plan_runtime.py -k discovery
python3 scripts/test_execute_plan_runtime.py
python3 scripts/plan_readiness.py docs/history/plans/2026-10-08-quota-wall-dispatch-doctrine.md
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-08-quota-wall-dispatch-doctrine.md
```

### Task 1: Single-home the anchors parser in the shared plan module and refuse prose-form blocks at the pre-round gate

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/plan_shape.py`
- `scripts/plan_readiness.py`
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`
- `agents/skills/plans/SKILL.md`

Primary class anchors:
- `PRIMARY_CLASS_ANCHOR_ENTRY` in `scripts/plan_shape.py`
- `anchors_block_problem` in `scripts/plan_readiness.py`

- [ ] Given the anchors parser (the `RuntimeDriver._plan_task_section` span extractor, the block loop, the heading literal, the entry regex) moved from `scripts/execute_plan_runtime.py` to `scripts/plan_shape.py`, expects the entry regex renamed to the public `PRIMARY_CLASS_ANCHOR_ENTRY`, the parser function promoted to the public `primary_class_anchors`, and the runtime keeping module-local aliases [class: IMPLEMENTATION_REQUIRED]
- [ ] Scope carve-out: given the runtime's other section helpers, expects `_directory_task_section` and `_plan_task_section_lines` staying runtime-local under the directory-shape carve-out [class: IMPLEMENTATION_REQUIRED]
- [ ] Identity witness: given the moved bytes, expects both consumers to run the shared code, `scripts/execute_plan_runtime.py` to carry no local definition, its names to be identity-equal (`is`) to the shared objects, and the readiness probe's parser binding to be the shared object by the same identity test [class: IMPLEMENTATION_REQUIRED]
- [ ] Single-home witness: given the tracked repository source, expects a readiness selftest assertion that no definition of the heading literal, the entry regex, or the canonical shape constant exists outside `scripts/plan_shape.py`, and that a shadowing redefinition in a consumer fails the selftest [class: REPOSITORY_TEST]
- [ ] Witness discriminator: a definition is an assignment to the exact protected name whose right-hand side is not a `plan_shape.`-qualified reference; the shadowing arm covers one regex-valued and one plain-string literal, and a sanctioned-reference arm asserts the scan accepts the runtime's alias assignments and the skill's prose mentions [class: REPOSITORY_TEST]
- [ ] Witness hermeticity: the scan resolves tracked source via the module file path, never the process cwd, and takes an injectable path-to-text mapping so the shadowing arm feeds tracked files plus one synthetic consumer carrying a redefinition; the enumeration is self-checking, asserting it observed the home and at least one consumer file before asserting absence, so a git failure never reads as a vacuous pass [class: REPOSITORY_TEST]
- [ ] Given a plan whose task section carries a `Primary class anchors:` block with a prose-form entry, expects the new probe `anchors_block_problem`, wired solely into the pre-round probe chain, to refuse with a named problem line that quotes the offending entry and interpolates `PRIMARY_CLASS_ANCHOR_SHAPE`, exit 1, `readiness PRE-ROUND FAILED:` [class: IMPLEMENTATION_REQUIRED]
- [ ] Enumeration: the probe enumerates `### Task N:` ordinals over fence-stripped text and parses each extracted section raw, mirroring the create path's payload-driven ordinals [class: IMPLEMENTATION_REQUIRED]
- [ ] Fenced-example fixture: given a one-task plan fencing a full `### Task 2:` example section carrying a prose-form anchors entry, expects the probe to ignore it exactly as `create` never requests that ordinal [class: REPOSITORY_TEST]
- [ ] Given a plan whose anchors block entries all conform to the entry grammar (backticked identifier and path, optional comma-plus-prose tail), expects the gate to accept the block with no anchors problem line [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a task section with no anchors block, expects the gate to behave exactly as before the check existed (no anchors problem line, no refusal) [class: IMPLEMENTATION_REQUIRED]
- [ ] Behavioral fixtures: given a block followed by a blank line and acceptance checkbox bullets, expects the checkboxes to not be read as anchor entries; given an anchors block quoted inside a fenced example, expects refusal; given anchors content under a subsection heading inside the task section, expects the shared parser's section span to still read it [class: REPOSITORY_TEST]
- [ ] Scope and posture fixtures: given an anchors-shaped block under a non-task section, expects the probe to ignore it exactly as `create` never reads that section; given the full readiness gate over a prose-form fixture, expects its verdict unchanged from before this plan [class: REPOSITORY_TEST]
- [ ] Enumeration fixture: given a two-task plan whose first task's anchors conform and whose second task's block carries the prose-form entry, expects the pre-round refusal and the problem line to name the second section's entry [class: REPOSITORY_TEST]
- [ ] Given every authoring-side enumeration of the pre-round probe set (the plans skill's rule 29 list and its done-boundary pre-round sentence, `run_pre_round`'s docstring probe list, the `--pre-round` argparse help string's probe count, and the pre-round selftest family's count wordings), expects all updated in this task's commit to include the anchors-block grammar check, verified by a repository sweep for the old enumerations [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect RED: the pre-round refusal of a prose-form fixture plan fails before implementation [class: IMPLEMENTATION_REQUIRED]
- [ ] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the readiness selftest, `python3 scripts/test_plan_readiness.py`, and `python3 scripts/test_execute_plan_runtime.py -k discovery` pass over the moved parser [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `plans: single-home the anchors parser and refuse prose-form blocks at pre-round` [class: IMPLEMENTATION_REQUIRED]

### Task 2: State the runtime-owned anchors form in the skills' prose and fixtures

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `scripts/plan_readiness.py`
- `scripts/test_execute_plan_runtime.py`

- [ ] The plans skill's "Primary class anchors; required:" prose states the runtime-owned entry shape (both tokens backticked, optional comma-plus-prose tail) and names `PRIMARY_CLASS_ANCHOR_ENTRY` in `scripts/plan_shape.py` as the form's owner: given the corrected prose sentence, expects the backticked shape and the owner reference present as one statement by reference [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the identifier rule the same prose states, expects the repository-verifiable-identifier rule present and no second shape definition anywhere in the skill [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the suite pins over that paragraph (`ContractContentParityTest`'s plans-skill assertions), expects the corrected prose to retain the pinned fragments verbatim and the template fence's example entry byte-identical [class: REPOSITORY_TEST]
- [ ] Given the review-plan skill's blocked boundary fixture anchors entry carrying a trailing period after the path, expects the period dropped so the entry conforms to the entry grammar, with the fixture's marker lines and Judgment text otherwise untouched, and a test assertion extracting that fixture's anchor line and requiring a `PRIMARY_CLASS_ANCHOR_ENTRY` fullmatch [class: IMPLEMENTATION_REQUIRED]
- [ ] Owner fingerprint: given the plans skill's corrected owner-reference sentence, expects a readiness selftest assertion that parses the backticked symbol out of that sentence and asserts it is a compiled-regex binding in `scripts/plan_shape.py`, resolved via its module file path [class: REPOSITORY_TEST]
- [ ] Prose pin: given the corrected shape sentence, expects a runtime-suite pin named `test_plans_skill_anchor_shape_sentence_names_the_owner` asserting the backticked shape fragment and that the sentence names `PRIMARY_CLASS_ANCHOR_ENTRY` and `scripts/plan_shape.py`, and asserting by fixed-string search that no second shape definition exists anywhere in the skill [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: the runtime suite's plans-skill parity pins and boundary-example checks pass against the corrected skill bytes (`python3 scripts/test_execute_plan_runtime.py -k plans_skill` and `python3 scripts/test_plan_review_boundary_examples.py`), and `bash scripts/check_maintenance_pins.sh` exits 0 over the touched spans [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `plans: state the shared anchors grammar in the skills' prose and fixtures` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Make the discovery refusal self-remedying

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/plan_shape.py`
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`
- `docs/history/backlog/2026-10-09-runtime-selftest-model-guard-baseline-red.md` *(new)*

Primary class anchors:
- `primary_class_anchors` in `scripts/plan_shape.py`

- [ ] Given a malformed anchors entry reaching the shared block loop, expects the canonical shape appended at the shared loop's raise site in `scripts/plan_shape.py`, interpolated from `PRIMARY_CLASS_ANCHOR_SHAPE`, so the error names the fix and both execution-side wraps (discovery's and the coverage gate's) carry it; the runtime alias and call sites unchanged [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a focused test named `test_primary_class_anchors_malformed_entry_refusal_appends_canonical_shape` in `scripts/test_execute_plan_runtime.py`, invoking the shared parser on a fixture section, expects it to assert the message ends with the canonical shape and to fail before implementation [class: REPOSITORY_TEST]
- [ ] Both-surfaces fixture: given the pre-round problem line and the runtime malformed-entry error, expects a fixture asserting both interpolate the same `PRIMARY_CLASS_ANCHOR_SHAPE` string [class: REPOSITORY_TEST]
- [ ] Rider: given the pre-existing red of the runtime in-file selftest (its claim fixture blocks on the missing Codex model-guard probe adapter), expects the rider backlog row filed with a Dedup probe line, and no repair attempted in this plan [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect RED: the named test fails against the unshared message before implementation [class: IMPLEMENTATION_REQUIRED]
- [ ] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the named test passes and `python3 scripts/test_execute_plan_runtime.py -k primary_class_anchors` runs at least one test [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `runtime: append the shared anchors shape to the malformed-entry refusal` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Disposition the doctrine plan's prose-form anchors through the semantic plan-edit path

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `docs/history/plans/2026-10-08-quota-wall-dispatch-doctrine.md`
- `docs/history/reviews/2026-10-08-plan-review-quota-wall-dispatch-doctrine-r3.md` *(new)*
- `docs/history/reviews/2026-10-08-plan-review-quota-wall-dispatch-doctrine-r3.stats.json` *(new)*

- [ ] Given the four verifiable doctrine anchors entries, expects conversion to the runtime form with these exact identifiers: `- `Sub-Agent Launch Rules` in `agents/skills/execute-plan/SKILL.md``, `- `Dispatch discipline` in `agents/skills/maintenance/zcode.md``, `- `Phase 3 tracking list` in `agents/skills/execute-plan/SKILL.md``, `- `Record format` in `docs/maintenance/operator-directives.md``, each entry's descriptive text moved after a comma [class: IMPLEMENTATION_REQUIRED]
- [ ] Given each converted identifier, expects a scan witness that its bytes exist at the named path, and the real discovery linkage run per identifier asserting the named path appears in that run's selected paths or provenance output for its doctrine task, with its linked and excluded lines recorded in the task log [class: REPOSITORY_TEST]
- [ ] Given the one unverifiable doctrine anchors entry (the per-path pass numbering bullet in doctrine Task 2's block), expects that bullet removed, the block staying for its converted `Phase 3 tracking list` sibling [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the doctrine plan's task checklist items, expects every item to carry a classification tag from the readiness vocabulary on its first line: given the converted bytes, expects `python3 scripts/plan_readiness.py --pre-round` to accept the plan [class: REPOSITORY_TEST]
- [ ] Safety witness, round shape: given the doctrine plan's changed bytes, expects a whole-plan re-cert round recorded as r3 in the doctrine plan's own review series, panel_mode focused per the doctrine r2 precedent with its selection_reason naming the anchors-grammar re-verification, and the pre-existing post-r2 byte delta identified and dispositioned in the r3 record [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness, digest: given the r3 record, expects its stats sidecar `source_digest` to equal the amended bytes' digest and the latest review round for the doctrine plan's slug to resolve to that r3 [class: IMPLEMENTATION_REQUIRED]
- [ ] Mechanical witness: given the converted doctrine plan and its r3 record, expects `python3 scripts/plan_readiness.py docs/history/plans/2026-10-08-quota-wall-dispatch-doctrine.md` to exit 0, the full gate that refuses on the stale digest today [class: REPOSITORY_TEST]
- [ ] Repository scan: given the open plans root, expects a scan for remaining prose-form anchors blocks recorded in the task log; any plan found beyond the declared file is filed as a backlog rider, never edited out of declared scope [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `plans: convert quota-wall-dispatch-doctrine anchors to the shared grammar form` [class: IMPLEMENTATION_REQUIRED]
