# Plan: Contract single-sourcing for the executability contract (readiness oracle vs the driver's Phase 0 extraction rule)

Backlog origin: docs/history/backlog/2026-10-10-contract-single-sourcing.md (the PLAN-PROMPTS entry `contract-single-sourcing` carries the operator "next" walk; the machinery audit's contract-drift family, rated 15 of 25)
Driving force: automation
Design input: docs/maintenance/machinery-blocker-audit-2026-10-09.md (the contract-drift family); the account-governor precedent (agents/skills/maintenance/SKILL.md Step 4 Account governor policy: the policy table owned by the script and never re-stated)
Plan review record: the staging series docs/history/reviews/2026-10-10-plan-review-contract-single-sourcing-r*.md (created by this plan's review loop, r1 onward; the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 2h total, largest task 0.75h
Authoring claim: docs/tmp/authoring-claims/2026-10-10-contract-single-sourcing.md (session sess_5c51c846-299a-4dfe-a00c-4238d7883663)

## Terms

- The extraction rule: the create boundary's plan-shape refusals at manifest seeding, scoped to exactly the three components the origin row names - per-task checklist action classification (the driver's "task <id> has unclassified checklist actions", "task <id> checklist action classification is incomplete", and "task <id> has an unclassified checklist action" label family), the deep-equality global-checklist signature (the clone-signature problem basis over identical non-empty whole `verification_commands` lists), and the bounded-evidence envelope (the MAX_EVIDENCE_BYTES 4096 / MAX_EVIDENCE_ITEM_BYTES 512 / 100-criteria limits and their refusal labels). The create boundary's OTHER refusal families are not extraction-rule grounds under this plan: the discovery-path validations (malformed or missing `Files:` declarations, malformed Primary class anchors blocks, empty acceptance checkboxes, empty discovered scope, empty criteria sets, empty verification contracts), the Phase 0 mechanical malformed shapes outside the three components (the later-task-artifact verifier shape, the tail-boundary path-embedding shape), and the operational refusals (claim collisions, worktree gateways, merge locks). The parity claim scopes to the three components; the discovery-path class is the explicitly-deferred residual a follow-up plan may extend to, recorded as such rather than silently uncovered.
- The owned module: `scripts/runtime_capabilities.py`, the existing single home of the bounded-evidence constants ("no other module may define or assign them", its line-31 rule) and of `bounded_evidence`; this plan grows the extraction rule's check functions beside the constants they enforce, so one module owns the whole executability contract surface.
- Certification-parity: a plan the create boundary would refuse at Phase 0 on an extraction-rule ground fails `scripts/plan_readiness.py` certification with the same labels, and a plan that certifies clean never refuses at Phase 0 on an extraction-rule ground.
- The anchors-grammar boundary: the Primary class anchors grammar single-homing is owned by the covering plan docs/history/plans/completed/2026-10-09-primary-class-anchors-grammar-drift.md, which LANDED on 2026-10-10 before this plan's r1 review (the completed/ archive is the witness); this plan owns the evidence and checklist envelope beside it, never touches the anchors grammar surface (the anchors execution rewrote adjacent regions of the same two scripts), and re-derives its line anchors at each task start.

## Why

A readiness pass is not an executability fact today: `scripts/plan_readiness.py` certifies a plan as digest-intact while measuring none of the extraction-rule properties the driver's create boundary enforces at Phase 0, so a plan that cannot execute certifies clean and blocks at execution start (the witnessed 4096 extraction-cap collision, dispositioned to this family by the review-loop budget entry's rejected alternative). Beside that gap, the execute-plan skill restates the 512/4096/100 constants in prose with no consistency check binding text to code. Both legs are the same seam: copied contracts disagree. The fix is the landed account-governor shape: one owner, consumed everywhere, cited by text.

## Gist & Examples

TLDR: the extraction rule's check functions move into the owned module; the driver's create boundary calls them (byte-identical behavior), the readiness oracle runs them at certification with the same labels, and the skill text cites the module instead of restating the constants.

Before: a plan whose task carries an unclassified checklist action or an oversized evidence criterion certifies clean (readiness measures none of it), then refuses at Phase 0 execution start with "task N has unclassified checklist actions" or the evidence-envelope labels - an authoring cycle spent on a refusal certification should have caught.

After: the same plan fails certification with the same label text readiness and the driver share from one module; a certified plan never hits an extraction-rule refusal at Phase 0; the skill's constants sentence cites the module so no second copy exists.

Edge cases: a refusal ground the create boundary enforces that is NOT extraction-rule (claim collisions, worktree gateways, merge locks) stays out of readiness - certification parity covers the extraction rule only, and the driver keeps every check it has; a plan in the directory shape (charter PLAN.md plus tasks/ files) reads its task bodies through the same parse the driver uses, so parity holds across both plan shapes; the anchors-grammar plan landed on 2026-10-10 before this plan's r1 review, so the serialization arm is resolved and this plan's diffs never touch the anchors grammar surface.

## Outcome

Certification becomes a true executability oracle for the extraction rule, and the constants exist in exactly one file.

- A plan the create boundary would refuse at Phase 0 on one of the three extraction-rule components fails certification with the same labels (per-task classification; the clone-signature basis where its inputs are derivable from the plan file, the residual recorded explicitly otherwise; the bounded-evidence dimensions), and a certified plan never refuses at Phase 0 on any of those three grounds.
- The extraction rule's check functions live in `scripts/runtime_capabilities.py` beside the constants; the driver's create boundary and its codex twin consume them unchanged in behavior; `scripts/plan_readiness.py` consumes them at certification.
- `agents/skills/execute-plan/SKILL.md` cites the owned module for the 512/4096/100 constants instead of restating the numbers, per the account-governor precedent, with the citation shape pinned.
- The full driver suites (both runtimes), the readiness suite (including its selftest), and the pins suite stay green; no refusal semantics loosened anywhere - where readiness gains a check the driver already had, the driver keeps it.

Gate delta: one existing single-home module grows the check functions it already enforces the constants for; one oracle gains the checks that make its certification claim true; two skill sentences convert restatements into citations; pins re-pointed in the same landings; no new state field, no new lock, no refusal removed or weakened; the claims-drift cluster rows (dir resolution, stem case) stay separate small plans per the entry's rejected alternative (they are execution-claim-surface fixes with their own witnesses, not riders on this seam).

## Assumptions

- The owned module is `scripts/runtime_capabilities.py`, not a new file: the constants and the `bounded_evidence` envelope already live there under the no-other-module rule, the driver and its codex twin already import it, and a second module would split the contract this plan single-sources. Basis: the line-31 single-home rule, the import census (both runtimes import `runtime_capabilities`), and the origin row's "one owned module that both consume".
- Behavior parity is byte-level at the labels and structural at the call sites: the moved check functions raise the same `ValueError` strings from the same data conditions; the driver's create boundary calls them instead of inlining the logic, and its suite proves no observable change; readiness calls them over the parsed plan and maps a raised check to its certification failure with the label text preserved. Basis: the origin row's ship-when ("the same labels") and the no-loosening constraint.
- The clone-signature check moves its detection (the deep-equality comparison and problem construction) into the owned module while its call site keeps its preseed-verifier context; readiness runs the same detection over the certified plan's tasks. If the signature's inputs are not derivable from the plan file alone at certification time (they derive from the seeded manifest's verification commands, which the create boundary derives from the plan), readiness derives them through the same discovery path the create boundary documents, and where discovery is a create-boundary internal, the parity arm scopes to the checks whose inputs the plan file carries (per-task classification and the evidence envelope) and the signature arm records the residual explicitly rather than pretending parity. Basis: the driver's create-boundary discovery contract (the skill's create paragraph: the boundary derives scope, criteria, and verification contract from plan-owned inputs) and the no-false-parity rule this plan prefers over an overbroad claim.
- The skill's constants sentence keeps its authoring guidance (the split-the-criterion remedy) and loses only the restated numbers, which become a citation to the owned module; the pins suite carries the citation shape (the restated-number form frozen absent wrap-tolerant, the citation present count-gated). Basis: the account-governor precedent's exact shape and Leg B's wording.
- Residual accepted: certification parity is proven by fixture plans that refuse at Phase 0 today (each refusal class gets a fixture asserting readiness fails with the same label); a refusal class that cannot be expressed as a plan file (none known) would surface as a parity test gap and stops the task for reconciliation. Basis: the driver's existing refusal inventory in its create tests.
- The claims-drift rows stay out of scope: the entry's rejected alternatives already dispositioned them as separate small plans, and the execution budget does not need riders. Basis: the entry's constraint clause and the two cluster rows' own witnesses.

- The authoring claim path is machine-local by design (gitignored `docs/tmp/`): the freeze witness lives in the primary checkout for the loop's guards, and the durable receipts after the run are the prune audit and the entry's `Frozen:` line in landed history.

Decision points requiring a grill: none remain (the operator's "next" walk pre-authorized the entry; the entry records the two-leg shape, the five rejected alternatives, and the claims-drift disposition; the owned-module choice is fixed by the existing single-home rule).

## Standing constraints

- No refusal semantics loosened anywhere: the driver keeps every check it has; readiness only gains checks; a label may move homes but never changes text or trigger condition.
- The full driver suites (scripts/test_execute_plan_runtime.py and its codex twin suite), the readiness suites (scripts/test_plan_readiness.py and plan_readiness.py --selftest), and the pins suite stay green at every task landing; the public hygiene scan passes before each commit.
- The anchors-grammar plan landed before this plan's execution (docs/history/plans/completed/2026-10-09-primary-class-anchors-grammar-drift.md): the serialization arm is resolved, the task-start currency check is the operative protection, and this plan's diffs never touch the Primary class anchors grammar surface or the regions that execution rewrote; line anchors re-derive at each task start.
- No machine-specific absolute paths in any edited file; nothing is pushed to origin; execution runs on a branch kept rebased onto current main at each fold, with the plan's task-start currency check (pins suite exit 0, no commit in `git log HEAD..main` touching the anchor files) and the stop-and-report arm on a red baseline.
- Rollback arm: revert the offending task's commit, Task 2 before Task 1 (readiness imports the owned functions, so reverting Task 1 alone breaks the import), and re-land the pins honestly afterward - the Task 3 citation pin guards the citation's presence, not the cited home's continued ownership, so a post-revert hollow home is invisible to it; the owned module's new functions are additive, so a revert of Task 2 restores the readiness gap without touching the driver, and a revert of Task 1 restores the driver's inlined checks byte-identically.
- Mid-queue sequencing: certification tightening lands between queue entries by preference; a plan certified under the old oracle whose next review round re-runs readiness and now fails an extraction-rule check is the witnessed defect class caught working as designed, adjudicated as such and never read as this plan's regression.
- Deploy truth: `~/.agents/skills` symlinks to the primary checkout's `agents/skills`, so the skill edit reaches the runtime registry at this plan's merge-locked landing - the landing is the deploy, and until it lands the live loop keeps loading the pre-edit files; the origin row's vendored-twin ship-when is discharged by the landing itself, and the codex runtime twin is discharged by the shared import (verified at review r1: it carries no independent copies of the extraction-rule checks).

## Evaluation Criteria

**Quality dimensions:**
- correctness: every label of the three extraction-rule components raised by the create boundary is raised by certification over a fixture plan that triggers it, asserting the full ValueError strings (never regex fragments), with identical text; the driver's suite passes unchanged.
- regression safety: both runtime suites plus the codex twin suite, the readiness unit suite and selftest, and the pins suite green; the skill citation pins present exactly once and the constants-sentence restated-number form absent.
- scope discipline: the changes touch only the owned module, the driver's call sites, the readiness oracle, the execute-plan skill's two restating sentences, and the pins script.

**Done when:**
- Every span check in `## Validation Commands` holds on the executed tree.
- The parity fixtures pass: each Phase 0 refusal class of the three components fails certification with the same full label text.

**Ship when:**
- The next certified plan executes past Phase 0 without a refusal on any of the three extraction-rule components, and a deliberately malformed plan fails certification before any execution start; they follow from the executed tree (the discovery-path refusal class stays the documented residual).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/runtime_capabilities.py` (the owned module: the extraction-rule check functions land beside the constants)
- `scripts/execute_plan_runtime.py` (the create boundary's call sites move to the owned functions; behavior byte-identical)
- `scripts/plan_readiness.py` (certification runs the extraction-rule checks with the same labels)

**Tests:**
- `scripts/test_execute_plan_runtime.py` (the create-boundary tests keep passing; new parity fixtures land here or beside the readiness suite)
- `scripts/test_execute_plan_runtime_codex.py` (green-baseline guard for the touched shared imports)
- `scripts/test_plan_readiness.py` (the 2,700-line unit suite over the oracle Task 2 edits; green at review r1)
- `scripts/check_maintenance_pins.sh` (the citation-shape pins and any re-pointed spans)

**Docs:**
- `agents/skills/execute-plan/SKILL.md` (both restating sentences: restated numbers out, the owned-module citation in)

**Read-only (referenced, never edited):**
- `docs/history/plans/completed/2026-10-09-primary-class-anchors-grammar-drift.md` (the anchors-grammar boundary; landed 2026-10-10)
- the `scripts/runtime_capabilities.py` line-31 single-home rule (the design constraint that fixes the module choice; the file itself is Production code above)
- `docs/maintenance/machinery-blocker-audit-2026-10-09.md` (the contract-drift family evidence)
- `docs/history/backlog/2026-10-07-execution-claims-dir-resolution-drift.md`, `docs/history/backlog/2026-10-07-claim-fence-stem-case-drift.md` (the out-of-scope claims-drift cluster)
- `docs/history/backlog/2026-10-10-contract-single-sourcing.md` (read-only this plan; flipped covered by the landing rider)

**Receipts:**
- Origin row: docs/history/backlog/2026-10-10-contract-single-sourcing.md (Status: open; the landing rider flips it covered naming this plan)
- Prompt entry: docs/history/backlog/PLAN-PROMPTS.md `## contract-single-sourcing` (frozen under docs/tmp/authoring-claims/2026-10-10-contract-single-sourcing.md; pruned by the landing rider with the prune receipt)

## Validation Commands

**Production:**
```bash
grep -c "runtime_capabilities" scripts/plan_readiness.py   # expect >=1 (readiness consumes the owned module)
grep -c "def check_checklist_action_classification\|def check_bounded_evidence_envelope" scripts/runtime_capabilities.py   # expect >=2
grep -c "has unclassified checklist actions" scripts/runtime_capabilities.py   # expect >=1 (the label's single home)
grep -cE "MAX_EVIDENCE_ITEM_BYTES. is 512|4096 UTF-8 byte aggregate|100-criteria count limit" agents/skills/execute-plan/SKILL.md   # expect 0 (restated numbers gone)
grep -c "runtime_capabilities" agents/skills/execute-plan/SKILL.md   # expect >=1 (the citation)
grep -c "has unclassified checklist actions" scripts/plan_readiness.py   # expect 0 (the label is not copied here; readiness imports it)
```

**Tests:**
```bash
python3 scripts/test_execute_plan_runtime.py -k create   # exit 0 (create boundary unchanged)
python3 scripts/test_plan_readiness.py   # exit 0 (the oracle's unit suite)
python3 scripts/plan_readiness.py --selftest   # exit 0 (including the parity fixtures)
( cd "$REPO" && bash scripts/check_maintenance_pins.sh )   # exit 0
bash scripts/check-no-em-dash.sh file agents/skills/execute-plan/SKILL.md   # exit 0
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh   # exit 0 from the repo root
```

### Task 1: the owned module grows the extraction rule (driver call sites move)

Files:
- scripts/runtime_capabilities.py
- scripts/execute_plan_runtime.py

- [x] Land the extraction-rule check functions in `scripts/runtime_capabilities.py` beside the constants: the per-task checklist action classification check (raising the exact "task <id> has unclassified checklist actions", "task <id> checklist action classification is incomplete", and "task <id> has an unclassified checklist action" labels from the same data conditions), and the deep-equality global-checklist signature detection (the clone-signature problem basis), importing nothing new; the module docstring's single-home rule sentence grows the enumeration it already implies (the constants, the envelope, and now the checks). [class: IMPLEMENTATION_REQUIRED]
- [x] Move the driver's create-boundary call sites to the owned functions in `scripts/execute_plan_runtime.py` (the seeding-time per-task classification checks and the preseed clone-signature detection), behavior byte-identical: every label string, trigger condition, and refusal ordering unchanged; the checklist-action derivation (the `Commit:` promotion, worker-criteria diffing, and parent-obligation construction the create boundary applies after classification) moves to the owned module as the pure derivation the checks consume, its two derivation-refusal labels ("task <id> parent commit action requires its exact planned identity" and "task <id> has no worker-owned criteria") moving with it into the owned label inventory while the create boundary keeps its manifest assembly; the codex twin needs no edit (verified at review r1: it carries no independent copies of the labels or the signature detection - its `bounded_evidence` import already follows the owned module); both runtime suites pass unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Run both runtime suites green and record the label inventory (the exact refusal strings now owned by the module) in the session log for Task 2's parity fixtures. [class: REPOSITORY_TEST]

### Task 2: readiness consumes the owned module (certification parity)

Files:
- scripts/plan_readiness.py
- scripts/runtime_capabilities.py
- scripts/test_execute_plan_runtime.py

- [x] `scripts/plan_readiness.py` imports the owned module and runs the extraction-rule checks at certification over the DERIVED plan shape, not raw checkbox lines: the checklist-action derivation (the `Commit:`-prefix promotion to owner=parent/kind=commit, worker-action defaulting, criteria deduplication) is owned by the module beside the checks, and readiness derives through it exactly as the create boundary does, so a plan with Commit: checkboxes never false-fails "checklist action classification is incomplete"; the clone-signature detection runs through the same derivation, or - where an input proves to be a create-boundary internal not derivable from the plan file - the explicit residual recording per the Assumption, never a pretended parity; a raised check fails certification with the label text preserved. [class: IMPLEMENTATION_REQUIRED]
- [x] Land the parity fixtures: for each Phase 0 refusal class of the three components (unclassified actions, incomplete classification, per-action schema, evidence item bytes, aggregate bytes, criteria count, clone signature where derivable), a fixture plan that triggers the driver's refusal asserts readiness fails with the same FULL label text; because readiness exits on its first failed condition and the structural conditions (readability, sidecar, digest, verdict) precede the extraction-rule checks, each fixture carries a minted review record and sidecar at the matching digest so the extraction-rule check is the failing condition, and the checks' position in the condition ordering is stated where they are inserted; a clean plan certifies and would pass Phase 0's extraction-rule ground. [class: REPOSITORY_TEST]
- [x] Run the readiness selftest, its unit suite (`scripts/test_plan_readiness.py`), both runtime suites, and the new parity fixtures green, and land this task as its own commit. [class: REPOSITORY_TEST]

### Task 3: the skill cites the owned module (Leg B) and final verification

Files:
- agents/skills/execute-plan/SKILL.md
- scripts/check_maintenance_pins.sh

- [x] Rewrite BOTH restating sentences in `agents/skills/execute-plan/SKILL.md` per the account-governor precedent - the create paragraph's constants sentence (the 512 / 4096 / 100 restatement) and the later prose sentence restating the envelope dimensions ("Create refuses criteria that exceed UTF-8 byte or 100-item receipt limits before writing" gains the citation and keeps its behavioral content): the authoring guidance stays (UTF-8 bytes, the split-the-criterion remedy, the never-raised-silently rule), the restated numbers (512 / 4096 / 100) go, and one citation names `scripts/runtime_capabilities.py` as the single home the create boundary enforces; the pins suite carries the citation shape (the constants-sentence restated-number form frozen absent wrap-tolerant (scoped to that sentence's shape: the second sentence keeps its "100-item" behavioral content), the citation present count-gated exactly once). [class: IMPLEMENTATION_REQUIRED]
- [x] Run the full verification battery on the executed tree: both runtime suites plus the codex twin suite, the readiness unit suite and selftest with the parity fixtures, the pins suite, the em-dash scan over the touched paths, and the hygiene scan; record each exit code in the session log and fix any red span before reporting the task done. [class: REPOSITORY_TEST]
