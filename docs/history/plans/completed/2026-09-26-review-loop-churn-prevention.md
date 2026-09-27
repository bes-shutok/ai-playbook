# Plan: Review-loop churn prevention (convergence telemetry, state-free plan bytes, consolidation gate)

Backlog origins (scope of record):
- docs/history/backlog/2026-09-26-nonconverging-review-cycles-prevention.md (full scope; anchor: convergence telemetry, runnable-carrier preference, fold receipts, case-growth cap)
- docs/history/backlog/2026-09-26-plan-review-state-self-reference-nonconvergence.md (full scope; co-anchor: round-independent plan bytes)
- docs/history/backlog/2026-09-20-plans-pin-text-audit-before-first-review-round.md (full scope: pin/text mechanical audit moves before round r1)
- docs/history/backlog/2026-09-15-review-sot-consolidation-gate.md (full scope: one consolidation finding instead of per-consumer duplicates; fold-in justification in Assumptions)
- docs/history/backlog/2026-09-26-p64-execution-review-deferred-findings.md (ride-along: all six items dispositioned individually; items 1-2 carry their own scope lines in Task 6, items 3-6 are polish)
- docs/history/backlog/2026-09-26-review-loop-fix-churn-reconciliation-trigger.md (ride-along: the same mechanical churn trigger as the anchor origin, independently witnessed; zero marginal tasks; receipt in the Assumptions trailer)

Driving force: efficiency + token-usage (primary efficiency: a review loop that feeds on its own fixes burns rounds without moving toward exit, witnessed as eight- and six-round loops halted by operator attention; secondary token-usage: every churn round re-hires a full panel to re-review the loop's own edits. Both forces are closed-taxonomy principles, so no non-principle justification is required.)

Plan review record: the staging series docs/reviews/2026-09-26-plan-review-review-loop-churn-prevention-r*.md (the highest rN is the authoritative record, including any deferred-residual list); the review loop closed at the operator-set round cap with every staged finding and overflow row folded, none deferred

## Outcome

Review loops stop consuming their own fixes: the churn that kept two witnessed loops running past eight and six rounds is now measurable, and a fired trigger forces reconciliation instead of another panel.

- Each review round stages a root classification (new defect, defect in a prior fix, missing test witness, wording), and a loop whose findings are mostly its own churn, or whose blocking count stops shrinking, routes through reconciliation by rule instead of waiting for an operator to halt it.
- Plan files no longer carry review-state prose that goes stale with every round, so a reviewed plan reaches a stable certified state instead of alternating between stale prose and stale verdicts.
- Reviews of documentation stop fanning one scope decision out into a finding per file: one consolidation finding names the owning document and each other document's disposition.
- The plan review's own mechanical audit runs before the first review round, so gate-versus-text mismatches cost a mechanical gate instead of a reviewer round.

## Terms

- **Convergence classification**: the per-round root classes assigned to every staged finding: `new-root`, `fold-defect`, `test-witness-gap`, `wording`.
- **Churn trigger**: the mechanical condition set that, when it fires, mandates `review-reconciliation` before another panel launches.
- **Fold receipt**: the mechanical post-fold audit record proving each accepted finding's fix actually landed in the new bytes.
- **Round-independent pointer**: a plan-header line naming the staging series by glob without naming any round number as current.
- **Self-referential review-state prose**: plan-bytes statements whose truth depends on which review rounds exist (latest-round pointers, verdict citations, round-attributed residual narratives).
- **Runnable carrier**: a script file under `scripts/` carrying mechanical logic directly testable without an extraction seam, as opposed to verbatim multi-line bash embedded in prose.
- **Armed predicate**: the single field-paragraph definition of when `authoring_cycle_gate` is armed, in terms of the inner `gate` member.
- **Consolidation finding**: one review finding naming the nominated SOT owner(s) and each affected consumer's disposition, staged instead of one finding per duplicated consumer.

## Assumptions

- One plan covers all six origins as one churn family; basis: authoring directive 2026-09-26 (the two anchors are one plan by design per the self-reference origin's own suggested fix).
- The SOT consolidation gate folds in as full scope rather than staying standalone; basis: the directive names "duplicated outputs" as one of the three churn classes and this origin is the only one covering it, the origin shares the review-agents surface the anchor origin already touches, and the directive explicitly offers fold-in-with-justification; the origin's 2026-09-18 standalone note recorded a scope split from the review-records-contract plan, not a bar against churn-family membership, so the note's intent (no free-riding on an unrelated contract plan) is preserved.
- The SOT gate fix changes finding-body guidance and the doors selftest only; the sidecar schema and `validate_review_staging.py` stay untouched; basis: the origin's acceptance criterion requires validator coverage only "of any new required metadata", and nominating owners inside the consolidation-finding body introduces no new required sidecar metadata, avoiding a deployed-validator-copy ripple for no churn benefit.
- Origin 2's fix includes rewriting review-plan SKILL.md Step 5 rule 4; basis: that rule currently mandates adding `Plan review: {reviews_dir}/<latest-rN>.md (latest, ready)` to the plan header, which is precisely the latest-round-pointer producer the origin bans (verified against the file on the base commit).
- `extensions.convergence` is the telemetry home; basis: the sidecar contract declares `extensions` as the object where "all future extra data belongs", so no schema rejection risk.
- The convergence classification is produced at round close from the orchestrator's fold history (the round launch already carries `last_fix_commit` and prior-findings context), not re-derived by workers; basis: only the orchestrator knows what its own folds introduced.
- P64 items 1 and 2 get their own scope lines (Medium latent hazards: a regression witness that cannot fire; a misreading that silently suppresses both lanes after a normal arm-then-clear cycle); items 3-6 are polish dispositions; basis: directive plus the origin's own acceptance notes.
- P64 item 3 lands as plans SKILL.md rule 29 wording (prescribe a real subcommand for the no-em-dash scan, never argless); basis: the origin marks the fix forward-looking and rule 29 is the authoring-time home of that scan.
- Corpus insertions stay stack-portable and the shared-body runtime-neutrality gate covers plans SKILL.md insertions; basis: the AGENTS.md standing gates and the shared-file set verified in `scripts/test_execute_plan_runtime.py` on the base commit.
- Existing maintenance pins are expected to hold after the Task 6 text edits; basis: pin-corpus sweep at authoring time found no pin on the edited spans (the cycle-gate pins cover the section anchor, the resting JSON literal, and the write-class name, none of which Task 6 changes).

Decision points requiring a grill: SOT-consolidation fold-vs-standalone: folded as full scope per the 2026-09-26 authoring directive's explicit fold-in-with-justification option; affects Origins block and Task 5; fix-churn trigger item inclusion: added as ride-along origin per standing pre-authorization and the self-reference origin's own pairing instruction, 2026-09-26; affects Origins block, Tasks 3-4, and the completion disposition; P64 item 3 forward-looking home: plans SKILL.md rule 29 subcommand wording per the origin's own fix text, 2026-09-26; affects Task 1.

## Gist & Examples

TLDR: the review loop gains mechanical convergence telemetry with a mandatory reconciliation trigger, plan bytes become round-independent by rule, the pin/text audit moves before round 1, duplicated SOT findings collapse into one consolidation finding, and the six deferred P64 findings get dispositions, because loops that review their own fixes must be stopped by rule rather than by operator attention.

Two witnessed loops show the same failure from opposite sides. A release-skill plan loop ran eight rounds (blocking counts 8, 6, 3, 7, 4, 3, 1, 3) where from round 4 onward the majority of findings were defects in earlier folds; nothing tripped because the exit condition only counts unresolved blocking findings. A doc-corpus plan loop had its corpus substance clean from round 6 onward while every remaining blocking finding targeted the plan's own review-state prose; each fold re-staled the prose, so no fold could fix the class. Both loops stopped only on operator attention. This plan makes the churn measurable (per-round root classification in the round sidecar's `extensions.convergence`), makes the trigger mechanical (composition majority, staged-total non-decrease, or blocking non-decrease across two rounds routes to `review-reconciliation` before any further panel), removes the prose that cannot converge (round-independent plan bytes), moves the pin/text audit before round 1 so gate/insert mismatches stop costing a reviewer round, and collapses review-output fan-out (one consolidation finding with a nominated owner and per-consumer dispositions instead of one finding per duplicated consumer).

Example of the round-independent pointer this plan mandates (and its own header carries): `Plan review record: the staging series docs/reviews/<date>-plan-review-<slug>-r*.md (the highest rN is the authoritative record, including any deferred-residual list)`. The banned alternatives are a header chain naming the latest round, verdict citations, and residual sections attributing findings to rounds; the staging record, not the plan, owns that state.

Example of the consolidation shape: a review that would otherwise stage the same scope correction in five documents stages one finding naming the nominated owner plus five dispositions (pointer, audience-specific delta, historical context banner, independent contract update).

## Evaluation Criteria

**Quality dimensions:**
- Mechanical decidability: every new gate (churn trigger, case-growth cap, fold receipt, span audit) names its inputs and comparison so an orchestrator can evaluate it without judgment calls; verified by review of the prescribed rule text against this criterion.
- Non-circularity: no new rule may depend on plan bytes carrying round state; the round-independent pointer is the only sanctioned review reference in plan bytes; verified by the absence sweeps in Validation Commands.
- Corpus compatibility: existing pins, the doors selftest, the portability scan, the shared-body runtime-neutrality test, and the em-dash and hygiene scans all exit 0 after the changes; verified by the Validation Commands block.
- Origin fidelity: each origin's suggested fix is delivered or its disposition recorded; verified by the archived plan's origin disposition section at completion, per Task 7's fold-then-delete step (after this plan lands).

**Done when:**
- All tasks' checklists are complete and the final Validation Commands block runs green end to end on the changed tree.
- Each of the six origins is deliverable-closed by this plan's tasks: telemetry and trigger (anchor + fix-churn item), round-independence (self-reference origin), authoring-time span audit (pin-audit origin), consolidation gate (SOT origin), six dispositions (P64 origin).
- The plan's own bytes contain no self-referential review-state prose (the plan practices the rule it adds).

**Ship when:**
- The next real plan review loop that hits a churn signal routes through `review-reconciliation` automatically, and its reconciliation note carries the per-round classification table (human-owned observation; prose only, no checklist item).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/review-loop/SKILL.md`
- `agents/skills/review-agents/documentation.md`
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `scripts/check_maintenance_pins.sh`

**Tests:**
- `scripts/test_review_agent_doors.py` *(edit: new door registration + fixture annotation)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/history/backlog/2026-09-26-at-cap-finalization-done-gate-collision.md`; reason: finalization-gate collision mechanism, not churn generation; owned by the corpus-family lane's follow-ups.
- `scripts/validate_review_staging.py` and any sidecar schema surface; reason: the SOT gate fix deliberately introduces no new required sidecar metadata (see Assumptions).
- `docs/history/backlog/2026-09-21-review-framework-and-runner-contracts.md`, `docs/history/backlog/2026-09-21-review-panel-terminal-path-and-boundary-contract-coverage.md`, `docs/history/backlog/2026-09-18-review-agents-miss-dual-surface-parity-conversion-floors-comment-inventories.md`; reason: claimed by the open plan at the plans home for `2026-09-26-review-agents-corpus-family`.
- `docs/history/backlog/2026-09-25-authoring-cycle-gate-auto-resume.md`; reason: scheduler pacing gate, not review convergence.

## Validation Commands

Preamble (authoring-time execution record, rule 29): executed 2026-09-26 against the base-commit tree, before round r1, and re-measured after each fold so the census below always describes the CURRENT block. Final census: 34 pinned checks (22 presence, 10 absence, 2 count) plus 2 raw greps (the header-loop canary needle, a line-anchored grep -E regex measured against the real script bytes, and the door declaration, a fixed-string grep -F whose verbatim bytes Task 5 item 3 prescribes). Of the 22 presence pins, 21 are red-today (span absent from its target file, flips green post-implementation) and 1 passes today as a guard (`one consolidation finding` already exists in the lens); of the 10 absence pins, 6 fire today (`a non-null gate value`, `updated from seven to eight in the same task`, `both extended this task`, `in the same task, the count`, `per the ordering. (the precheck imports`, and review-plan's `(latest, ready)`; all flip absent post-implementation) and 4 pass today as regression guards; the 2 count gates bind the pointer text to exactly one occurrence per skill file and the eight-class lead-in to its current single occurrence. The 4 passing absence pins, the 1 already-green presence pin, and the 2 count gates are the preamble's declared regression guards: the rule 22 routing measures them against the target file's current bytes instead of task snippets, and every other presence pin has a verbatim prescribed-text source in its owning task under the per-owning-snippet semantics this plan prescribes for rule 22 (cross-surface mirror spans appear once per owning snippet, the rule 36 shape). The Group A canary ran green on current bytes: the anchored needle matches the real header loop and flips on the member-dropped copy. `bash -n` over this block: clean. Group A suites on current bytes: maintenance pins exit 0, doors selftest exit 0, portability scan exit 0, shared-body runtime neutrality OK (invoked from the scripts directory: `( cd scripts && python3 -m unittest test_execute_plan_runtime -k shared_skill_bodies )`; the repo-root module-path form fails on a sibling import, which is why the anchored form is prescribed). Em-dash scan executed with a real subcommand (`touched`): exit 0. Public-hygiene scan: PASS. Readiness validator pre-round invocation: `python3 scripts/plan_readiness.py --pre-round <this plan under the repo's plans home>` reported structural checks clean, no failure class. Group A gates must be green before Task 1; Group B gates are red-today by design (they pin content the tasks introduce) and must be green after all tasks.

```bash
# Group A: existing-tree gates; green before Task 1 and after all tasks.
set -u
repo="$(git rev-parse --show-toplevel)" || exit 1
cd "$repo" || exit 1

expect_present() { # expect_present <file> <fixed-string>: fails when the span is missing
  grep -qF -- "$2" "$1" || { echo "FAIL: missing in $1: $2"; exit 1; }
}
expect_count() { # expect_count <file> <fixed-string> <n>: exact-occurrence gate
  n="$(grep -oF -- "$2" "$1" | wc -l | tr -d ' ')"
  [ "$n" -eq "$3" ] || { echo "FAIL: count $n != $3 in $1: $2"; exit 1; }
}
expect_absent() { # expect_absent <file> <fixed-string>: rc 1 passes, rc 0 fails, rc >= 2 aborts
  out="$(grep -nF -- "$2" "$1" 2>&1)"; rc=$?
  if [ "$rc" -eq 0 ]; then echo "FAIL: forbidden span present in $1: $2"; exit 1
  elif [ "$rc" -ge 2 ]; then echo "FAIL: grep error on $1: $out"; exit 1; fi
}

bash -n scripts/check_maintenance_pins.sh || { echo "FAIL: pins script syntax"; exit 1; }
bash scripts/check_maintenance_pins.sh || { echo "FAIL: maintenance pins corpus"; exit 1; }
python3 scripts/test_review_agent_doors.py || { echo "FAIL: doors selftest"; exit 1; }
python3 scripts/check_review_agent_portability.py || { echo "FAIL: portability scan"; exit 1; }
( cd scripts && python3 -m unittest test_execute_plan_runtime -k shared_skill_bodies ) || { echo "FAIL: shared-body runtime neutrality"; exit 1; }
bash scripts/check-no-em-dash.sh touched || { echo "FAIL: em-dash scan"; exit 1; }

# Pin canary for Task 6 item 1 (executed at authoring time on base bytes:
# the anchored needle matches the real header loop today; the mutated copy
# witness below flips only after the re-anchoring lands).
canary="$(mktemp -d)"
cp scripts/check_maintenance_pins.sh "$canary/pins.sh"
grep -qE '^for f in "\$S" "\$Z" "\$P" "\$D" "\$E"; do$' scripts/check_maintenance_pins.sh || { echo "FAIL: anchored needle misses the real header loop"; rm -rf "$canary"; exit 1; }
sed 's/ "\$E"; do/; do/' "$canary/pins.sh" > "$canary/pins-mutated.sh"
grep -qF 'for f in "$S" "$Z" "$P" "$D"; do' "$canary/pins-mutated.sh" || { echo "FAIL: mutation did not apply (the member-dropped loop form is absent)"; rm -rf "$canary"; exit 1; }
out="$(grep -nE '^for f in "\$S" "\$Z" "\$P" "\$D" "\$E"; do$' "$canary/pins-mutated.sh" 2>&1)"; rc=$?
if [ "$rc" -eq 0 ]; then echo "FAIL: anchored needle still matches the member-dropped loop"; rm -rf "$canary"; exit 1; fi
if [ "$rc" -ge 2 ]; then echo "FAIL: grep error on mutated copy: $out"; rm -rf "$canary"; exit 1; fi
rm -rf "$canary"

# Group B: post-implementation gates; red-today by design, green after all tasks.
# plans SKILL.md (Tasks 1-2)
expect_present "agents/skills/plans/SKILL.md" "The same audit also runs at authoring time, before the first review round"
expect_present "agents/skills/plans/SKILL.md" "never argless (argless prints usage and exits 0 scanning nothing)"
expect_present "agents/skills/plans/SKILL.md" "treat that as a design smell and prescribe a runnable carrier"
expect_present "agents/skills/plans/SKILL.md" "test-witness-gap, wording"
expect_present "agents/skills/plans/SKILL.md" "extensions.convergence"
expect_present "agents/skills/plans/SKILL.md" "route through review-reconciliation before launching another panel"
expect_present "agents/skills/plans/SKILL.md" "grows by more than 50 percent"
expect_present "agents/skills/plans/SKILL.md" "before the batch is marked triaged"
expect_present "agents/skills/plans/SKILL.md" "no latest-round pointers, no verdict citations, no round-attributed residual narratives"
expect_count "agents/skills/plans/SKILL.md" "the highest rN is the authoritative record" 1
expect_absent "agents/skills/plans/SKILL.md" "(latest, ready)"
# review-plan SKILL.md (Task 3): the sweep surface excludes this plan file,
# whose command text quotes the spans as checker literals, not stale prose.
expect_present "agents/skills/review-plan/SKILL.md" "extensions.convergence"
expect_present "agents/skills/review-plan/SKILL.md" "the highest rN is the authoritative record"
expect_present "agents/skills/review-plan/SKILL.md" "the staging record, not the plan bytes, owns review state"
expect_present "agents/skills/review-plan/SKILL.md" "mandates review-reconciliation before any further panel launch"
expect_absent "agents/skills/review-plan/SKILL.md" "(latest, ready)"
expect_absent "agents/skills/review-plan/SKILL.md" "review-state prose is out of scope only when the plan carries no pointer"
# review-loop SKILL.md (Task 4)
expect_present "agents/skills/review-loop/SKILL.md" "staged findings did not decrease across the two most recent rounds"
# review-agents (Task 5)
expect_present "agents/skills/review-agents/documentation.md" "no more than two current SOT owners"
expect_present "agents/skills/review-agents/documentation.md" "one consolidation finding"
expect_present "agents/skills/review-agents/documentation.md" "historical context banner"
grep -qF 'Pattern: `documentation#prose-sot-consolidation`' agents/skills/review-agents/documentation.md || { echo "FAIL: door declaration missing"; exit 1; }
expect_present "agents/skills/review-agents/review-panel-selection.md" "is a design-simplicity finding candidate"
expect_present "scripts/test_review_agent_doors.py" "documentation#prose-sot-consolidation"
# maintenance surfaces (Task 6)
expect_absent "agents/skills/maintenance/SKILL.md" "a non-null gate value"
expect_present "agents/skills/maintenance/SKILL.md" "whose \`gate\` member is a non-null string"
expect_present "agents/skills/maintenance/SKILL.md" "(the eighth sanctioned writer class)"
expect_absent "agents/skills/maintenance/SKILL.md" "updated from seven to eight in the same task"
expect_absent "agents/skills/maintenance/SKILL.md" "both extended this task"
expect_present "agents/skills/maintenance/SKILL.md" "dispatches it (the precheck imports only the trap rule"
expect_absent "agents/skills/maintenance/SKILL.md" "per the ordering. (the precheck imports"
expect_absent "agents/skills/maintenance/SKILL.md" "in the same task, the count"
expect_count "agents/skills/maintenance/SKILL.md" "eight sanctioned writer classes" 1
expect_absent "agents/skills/maintenance/zcode.md" "six sanctioned writer classes"
expect_absent "agents/skills/maintenance/zcode.md" "seven sanctioned writer classes"

# Repository hygiene before commit (session gate, not plan content).
bash scripts/check-no-em-dash.sh touched || { echo "FAIL: em-dash rescan"; exit 1; }
```

### Task 1: plans SKILL.md authoring-time anti-churn rules (origins: pin-audit full scope; anchor fix 2; P64 item 3)

Files:
- `agents/skills/plans/SKILL.md`

- [x] Extend Validation Commands authoring rule 22 with one sentence after its "after EVERY fold" audit obligation, verbatim: `The same audit also runs at authoring time, before the first review round, as part of the rule 29 pre-round execution record, with rule 36's mirror carve-out applied to its exactly-once comparison (a cross-surface mirror span is checked once per owning snippet) and with pins the plan's Validation preamble declares as regression guards checked against the target file's current bytes instead of a task snippet, plus the shell syntax check, so a gate/insert mismatch costs a mechanical gate instead of a reviewer round.` [class: IMPLEMENTATION_REQUIRED]
- [x] Extend authoring rule 29's scan sentence to prescribe the scan's real subcommand form (`check-no-em-dash.sh touched`, or `added-lines --base REF` for committed baselines) and add, verbatim: `never argless (argless prints usage and exits 0 scanning nothing)`, naming the witnessed defect class (a validation line that runs the scanner without a subcommand proves nothing). [class: IMPLEMENTATION_REQUIRED]
- [x] Add one sentence to the Writing guidance block in plans SKILL.md (runnable-carrier preference), verbatim: `When a plan's correctness story requires verbatim multi-line bash embedded in a skill or document, treat that as a design smell and prescribe a runnable carrier instead: a real script file under scripts/ that tests call directly, with the prose carrying only invocation and judgment steps; a review lens treats a verbatim-block prescription in a plan as a finding candidate.` [class: IMPLEMENTATION_REQUIRED]
- [x] Run the authoring-time span audit and `bash -n` over this plan's own Validation Commands block per the extended rule 22; record both green in the session notes. Run → expect GREEN (the rule text is self-satisfying on this plan's own bytes). [class: REPOSITORY_TEST]
- [x] Commit: `skills: authoring-time churn gates in plans rules 22 and 29 plus runnable-carrier rule` [class: IMPLEMENTATION_REQUIRED]

### Task 2: plans SKILL.md loop-churn gates and round-independent plan bytes (origins: anchor fixes 1, 3, 4; self-reference origin, plans side)

Files:
- `agents/skills/plans/SKILL.md`

- [x] Add one Plan Quality Gate loop rule (convergence telemetry), verbatim anchor span: `After each round's staging, classify every staged finding by root: new-root, fold-defect, test-witness-gap, wording; fold-defect means the finding anchors on text a prior round's accepted fold introduced, judged against the orchestrator's fold history (the record of accepted findings folded in earlier rounds and the spans their fixes touched), new-root means no prior fold's touched text anchors the finding, test-witness-gap means the prescription lacked a test that would have caught the defect, and wording means clarity or consistency with no behavioral claim; a finding matching multiple classes records the most specific: fold-defect, then wording, then test-witness-gap, then new-root; record the counts and the open-blocking count in that round's sidecar under extensions.convergence`. [class: IMPLEMENTATION_REQUIRED]
- [x] Add one Plan Quality Gate loop rule (mechanical churn trigger), verbatim anchor span: `When fold-defect plus wording findings exceed half of the round's staged findings, or total staged findings did not decrease across the two most recent rounds, or the open-blocking count did not decrease across two consecutive rounds, route through review-reconciliation before launching another panel instead of folding and re-rounding, even when the blocking count is converging`. [class: IMPLEMENTATION_REQUIRED]
- [x] Add one Plan Quality Gate loop rule (fold receipts), verbatim anchor span: `After every fold batch, run a mechanical audit that each accepted finding's fix actually landed (the pinned span occurs in the new bytes, or the prescribed behavior exists) before the batch is marked triaged; a claimed-but-unlanded fold is an orchestrator error to record in the staging doc and re-execute, never a silent pass`. [class: IMPLEMENTATION_REQUIRED]
- [x] Add one Plan Quality Gate loop rule (case-growth cap), verbatim anchor span: `When the plan's prescribed test list grows by more than 50 percent across rounds relative to its pre-loop count, answer the simplification question (are these cases testing the design or testing the pins?) before the next fold or round and record the answer in the staging doc`. [class: IMPLEMENTATION_REQUIRED]
- [x] Add to the Plan Format metadata block the round-independent review-record pointer convention as a line the author copies with the feature name filled in, verbatim: `Plan review record: the staging series {reviews_dir}/YYYY-MM-DD-plan-review-<feature-name>-r*.md (the highest rN is the authoritative record, including any deferred-residual list)`, plus one ban sentence, verbatim anchor span: `Plan bytes carry no self-referential review-state prose: no latest-round pointers, no verdict citations, no round-attributed residual narratives; deferred residuals live in the staging record, which remains authoritative after certification`. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: Group A gates still green (the rule insertions do not touch pinned budget-gate mirror spans); the plans-side Group B checks for this task's spans pass at this task's tree state; the review-plan Group B checks stay red until Task 3 lands them. [class: REPOSITORY_TEST]
- [x] Commit: `skills: convergence telemetry, mechanical churn trigger, fold receipts, case cap, round-independent plan bytes` [class: IMPLEMENTATION_REQUIRED]

### Task 3: review-plan SKILL.md round-close churn wiring (origins: anchor fix 1 review side; self-reference origin review side; fix-churn item home)

Files:
- `agents/skills/review-plan/SKILL.md`

- [x] Step 4 output: require the round-close pass to write the convergence object under the key `extensions.convergence` in the sidecar's optional extensions object, populated from the orchestrator-supplied fold history, with the shape `{"new_root": 0, "fold_defect": 0, "test_witness_gap": 0, "wording": 0, "blocking_open": 0}`; the classification mirrors the plans skill's Plan Quality Gate loop rule so both skills name the same classes. [class: IMPLEMENTATION_REQUIRED]
- [x] Step 4 output: add the reviewer-side ban, verbatim anchor span: `A finding whose only subject is a plan's review-state prose being stale (a round chain omitting the round just staged, a verdict citation naming a superseded record, a residual narrative lagging the record) is invalid when the plan carries the round-independent review-record pointer; the staging record, not the plan bytes, owns review state`. [class: IMPLEMENTATION_REQUIRED]
- [x] Step 5 rule 4 rewrite: replace the `Plan review: {reviews_dir}/<latest-rN>.md (latest, ready)` instruction with the round-independent pointer line, verbatim: `Plan review record: the staging series {reviews_dir}/YYYY-MM-DD-plan-review-<feature-name>-r*.md (the highest rN is the authoritative record, including any deferred-residual list)`, so folds stop adding round-attributed lines to plan bytes; keep the rule number and position. [class: IMPLEMENTATION_REQUIRED]
- [x] Reconciliation gate section: replace the open-ended "fixes regenerate findings" phrasing with the mechanical trigger referencing the round's convergence object: fold-defect plus wording findings that exceed half of the round's staged findings, or staged-total non-decrease across the two most recent rounds, or blocking non-decrease across two consecutive rounds, or the configured cycle cap; a fired trigger mandates review-reconciliation before any further panel launch even when blocking converges. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Group B review-plan checks pass ((latest, ready) absent, pointer text present exactly once, convergence span present); Group A gates stay green. [class: REPOSITORY_TEST]
- [x] Commit: `skills: review-plan round-close convergence object, reviewer-side state-prose ban, pointer rewrite, mechanical reconciliation trigger` [class: IMPLEMENTATION_REQUIRED]

### Task 4: review-loop SKILL.md churn-signal mirror (origin: fix-churn item)

Files:
- `agents/skills/review-loop/SKILL.md`

- [x] Extend orchestration rule 5 (reconciliation before continued churn) with the mechanical signal sentence, verbatim anchor span: `fixes regenerate findings means the measured churn trigger fired: the latest round's recorded classification shows fold-defect plus wording findings that exceed half of staged findings, or total staged findings did not decrease across the two most recent rounds, or the open-blocking count did not decrease across two consecutive rounds; standalone loop rounds record the same per-round root classification (new-root, fold-defect, test-witness-gap, wording) in their round record so the signal stays evaluable, and a loop whose records carry no classification falls back to the open-ended trigger phrasing; a fired trigger mandates review-reconciliation before any further review or fix pass, even when the blocking count converges`. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the review-loop presence check passes; Group A gates stay green. [class: REPOSITORY_TEST]
- [x] Commit: `skills: review-loop mechanical fix-churn reconciliation signal` [class: IMPLEMENTATION_REQUIRED]

### Task 5: review-agents SOT consolidation gate and runnable-carrier lens line (origins: SOT consolidation gate; anchor fix 2 review-lens half)

Files:
- `agents/skills/review-agents/documentation.md`
- `agents/skills/review-agents/review-panel-selection.md`
- `scripts/test_review_agent_doors.py`

- [x] Add the doors-test entry first (typed-catalog test method asserting the required actions inside the `documentation#prose-sot-consolidation` pattern window: nominate no more than two current SOT owners; one consolidation finding; per-consumer disposition; historical context banner; plus one fixture-annotations entry: a duplicated normative paragraph across living documents). Run the doors selftest → expect RED (declaration not yet present, `pattern_window` raises). [class: REPOSITORY_TEST]
- [x] Extend the documentation lens "Consolidation finding shape" bullet (the one bullet the door declaration closes, so every required-action phrase sits inside the doors selftest's 700-character pattern window) to require, before any multi-document scope edit set: authority-role classification and nomination of no more than two current SOT owners; one consolidation finding naming the nominated owners; each affected consumer's disposition recorded: pointer, audience-specific delta, historical context banner, or independent contract update; a broad synchronized edit suggested only when a consumer owns an independent contract that would otherwise go stale; and that historical-path documents are not current SOT by default and can require an explicit context banner when stale content could mislead. Leave the existing "Authority roles" bullet's authority distinctions untouched. Keep wording abstract (portability scan must stay green). [class: IMPLEMENTATION_REQUIRED]
- [x] Add the door declaration line, verbatim: ``Pattern: `documentation#prose-sot-consolidation` `` as the closing line of the SAME extended Consolidation finding shape bullet that carries the required-action phrases (owner nomination, one consolidation finding, per-consumer dispositions, historical context banner), so the doors selftest's 700-character pattern window reaches them; exactly one occurrence in the lens file. Run the doors selftest → expect GREEN. [class: IMPLEMENTATION_REQUIRED]
- [x] Add one sentence to review-agents/review-panel-selection.md's five-worker panel guidance (the anchor origin's review-lens half for plan reviews), verbatim: `A plan prescribing verbatim multi-line bash where a script file under scripts/ would carry the mechanical logic is a design-simplicity finding candidate (the runnable-carrier preference).` [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/check_review_agent_portability.py` exit 0; Group A gates stay green. [class: REPOSITORY_TEST]
- [x] Commit: `skills: SOT consolidation gate as a documentation-lens door plus the runnable-carrier panel-selection line` [class: IMPLEMENTATION_REQUIRED]

### Task 6: maintenance surfaces, P64 deferred dispositions (origin: P64 deferred findings, items 1-6)

Files:
- `scripts/check_maintenance_pins.sh`
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`

- [x] Item 1 (Medium, own scope line: self-satisfying regression pin): re-anchor the pin at the `pins header existence loop covers E` line from the bare fixed-string needle to the line-anchored form `grep -qE '^for f in "\$S" "\$Z" "\$P" "\$D" "\$E"; do$' "${BASH_SOURCE[0]}"`, so dropping a member from the script's real header loop fires the pin while the pin's own line (prefixed, not line-anchored) can no longer satisfy the needle. Run → expect RED first: with today's bare needle, the canary's member-dropped copy still matches (the defect witness); after the re-anchor, the canary's member-dropped copy fails and the real header loop matches. [class: IMPLEMENTATION_REQUIRED]
- [x] Item 2 (Medium, own scope line: cycle-gate armed predicate ambiguity): add to the `authoring_cycle_gate` field paragraph the single armed definition, verbatim anchor span: ``the gate is armed when the field is an object whose `gate` member is a non-null string; a cleared field (an object carrying `gate: null` plus a cleared timestamp) is not armed``; rewrite the Step 1 pending-dispatch reader and the Step 3 enforcement sites to reference the field paragraph's armed predicate instead of the standalone phrase `a non-null gate value`, so a post-clear `gate: null` object cannot read as armed (the permanent lane-suppression witness). [class: IMPLEMENTATION_REQUIRED]
- [x] Item 3 (Low): no maintenance-surface edit; its forward-looking fix is Task 1's rule 29 subcommand wording; disposition recorded here per the origin's ride-along instruction. [class: IMPLEMENTATION_REQUIRED]
- [x] Item 4 (Low): widen the two superseded sanctioned-writer-classes absence pins from SKILL.md-only targets to the full maintenance file set by replacing each single-target `expect_absent` call with an explicit loop over the five targets, one call shape per literal, verbatim: `for f in "$S" "$Z" "$P" "$D" "$E"; do expect_absent "superseded six sanctioned writer classes literal in $f" 'six sanctioned writer classes' "$f"; done` and the same loop shape for the seven literal, keeping the eight-class presence pin on SKILL.md (the pins script itself stays outside the swept set: its own pin lines legitimately quote the literals); run the corpus and verify every widened sweep passes on the current corpus before commit. [class: IMPLEMENTATION_REQUIRED]
- [x] Item 5 (Low): rewrap the stranded lowercase parenthetical in the Step 5 precondition bullet: move `(the precheck imports only the trap rule's park-or-retain write, never its clear-on-idle-success clause)` from the stranded form, verbatim: `per the ordering. (the precheck imports`, to attach to the park-persistence sentence, so the parenthetical directly follows the dispatch wording, forming the contiguous span ``dispatches it (the precheck imports only the trap rule`` with no intervening sentence boundary. [class: IMPLEMENTATION_REQUIRED]
- [x] Item 6 (Low): trim plan-task narration from the `authoring_cycle_gate` field paragraph: replace the parenthetical `(the eighth class; the lead-in count sentence is updated from seven to eight in the same task, the count's own movement precedent being the 2026-09-25 six-to-seven entry)` with `(the eighth sanctioned writer class)`, and drop the `both extended this task` narration from the Readers sentence; the movement history remains owned by the Revisions ledger entry dated 2026-09-26. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `bash scripts/check_maintenance_pins.sh` exit 0 after all six dispositions (the pin corpus holds with the edited text); the canary in Group A flips to its post-fix expectations; Group B maintenance checks pass. [class: REPOSITORY_TEST]
- [x] Commit: `skills: p64 deferred dispositions, anchored header-loop pin, single armed predicate, pin sweep widening, prose rewrap` [class: IMPLEMENTATION_REQUIRED]

### Task 7: final validation and completion closure

Files: none beyond the tasks above.

- [x] Run the full Validation Commands block end to end; expect exit 0 with Group A and Group B both green on the changed tree. [class: REPOSITORY_TEST]
- [x] Sweep the plan's own bytes for self-referential review-state prose before certification; the needles are the banned prose forms Task 2's ban sentence names (latest-round pointers, verdict citations, round-attributed residual narratives); occurrences inside Validation Commands checker literals and quoted old-form instructions (the Step 5 rewrite quote and the inversion-guard needle) are checker text, not review-state prose; expect zero occurrences outside those literal spans. [class: REPOSITORY_TEST]
- [x] At completion, fold each origin with its disposition into the archived plan per the standard lifecycle (fold-then-delete; no per-item archives), including the six individual P64 dispositions and the fix-churn ride-along receipt; origins close only after this plan lands. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `plans: review-loop churn prevention validation complete` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items (fold-then-delete, closed at landing)

All six origins delivered-closed by the tasks above; per-item backlog files deleted, no per-item archives.

- `2026-09-26-nonconverging-review-cycles-prevention.md`: CLOSED by Tasks 2-4. Convergence telemetry (plans rule 12, `extensions.convergence` sidecar object), mechanical churn trigger (plans rule 13; review-plan reconciliation gate; review-loop rule 5 mirror), fold receipts (rule 14), case-growth cap (rule 15).
- `2026-09-26-plan-review-state-self-reference-nonconvergence.md`: CLOSED by Tasks 2-3. Round-independent review-record pointer in the plans Plan Format metadata block with the self-referential-prose ban; review-plan Step 5 rule 4 rewritten off `(latest, ready)`; reviewer-side review-state ban added.
- `2026-09-20-plans-pin-text-audit-before-first-review-round.md`: CLOSED by Task 1. Rule 22 extended: the span audit also runs at authoring time, before round 1, as part of the rule 29 pre-round record.
- `2026-09-15-review-sot-consolidation-gate.md`: CLOSED by Task 5. SOT consolidation gate landed as `documentation#prose-sot-consolidation` door with doors-selftest coverage and the fixture annotation; validator untouched per the Assumptions scope split.
- `2026-09-26-p64-execution-review-deferred-findings.md`: CLOSED by Task 6, all six items dispositioned: item 1 header-loop pin re-anchored line-anchored (canary flips); item 2 armed predicate single-homed in the field paragraph with both enforcement sites referencing it; item 3 forward-looking fix delivered as Task 1 rule 29 subcommand wording (no maintenance-surface edit); item 4 two superseded-literal absence pins widened to the full five-file maintenance set; item 5 stranded parenthetical rewrapped onto the park-persistence sentence; item 6 task narration trimmed from the field paragraph, movement history owned by the Revisions ledger.
- `2026-09-26-review-loop-fix-churn-reconciliation-trigger.md`: CLOSED by Task 4 (review-loop rule 5 mechanical signal, per-round classification for standalone loops, fallback phrasing), ride-along receipt with the anchor origin's Task 2/3 trigger.

Execution record: executed 2026-09-27 in worktree `exec/review-loop-churn-prevention` over base 6759174c; Tasks 1-6 committed with the prescribed messages; full Validation Commands block green end to end (Group A and Group B) post-fold; review r1 blind two-worker panel (correctness/completeness + consistency/operations) staged zero blocking findings, verdicts ready=yes both; one Low folded (lens bullet "can require" fidelity).
