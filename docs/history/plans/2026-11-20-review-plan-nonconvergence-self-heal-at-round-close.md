# Plan: Review-loop round-close convergence evaluation and unattended self-heal continuation

Backlog origin: docs/history/backlog/2026-11-20-review-plan-nonconvergence-pause-skips-self-heal.md
Driving force: automation (primary), simplicity (secondary)
Plan review record: the staging series .ai-playbook/reviews/2026-11-20-plan-review-review-plan-nonconvergence-self-heal-at-round-close-p2bf28b12-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 1h total, largest task 0.5h
Executed: no
Authoring claim: 2026-11-20-review-plan-nonconvergence-pause-skips-self-heal.md (session sess_ee74cc9d-6d23-48d4-a6f5-4d6cc7f94e86)

## Terms

- Comparable round: a review round whose staging sidecar coverage outcome is neither `degraded` nor `failed` and whose panel carries no row whose status is anything other than `complete` (the existing definition in review-plan's Reconciliation gate; unchanged).
- Churn trigger: the measured non-convergence trigger in review-plan's Reconciliation gate, one of whose trigger arms is a positive open-blocking count not decreasing across the two most recent comparable rounds (unchanged).
- extensions.convergence: the optional `extensions` member of a round's `.stats.json` sidecar carrying the loop's convergence telemetry (the classification counters and the run-wide `self_heal_attempt` state).
- Open-blocking count: the number of a round's staged findings whose sidecar row carries `blocking: true` without a resolved triage value.
- Round close: the pass that writes a review round's staging record and sidecar and then decides whether the loop continues or pauses.
- Round-close evaluation step: the duty this plan adds; the trigger evaluation run at every round close from the sidecars.
- Self-heal attempt state: the run-wide one-attempt marker at `extensions.convergence.self_heal_attempt` (`unused`, `consumed`, or `unknown`).
- Standing authorization: a run directive (the maintenance standing pre-authorization included) authorizing the loop to decide and proceed without questions.
- Recurrence trigger: review-plan's same-root-issue-recurs arm of the reconciliation triggers (unchanged).
- Non-convergence sequence: the Scope and complexity policy's reconcile-then-self-heal-assess prescription for an active trigger (unchanged; the policy never coins the phrase, this plan uses it as a label for that prescription).
- Cap-closure: the loop's configured-round-cap terminal mechanics (unchanged).
- Pause arms: the Scope and complexity policy's enumerated operator-direction pause paths (unchanged by this plan's terms).

## Why

A five-round plan review run closed round 4 with the churn trigger active (blocking rose from 1 to 2 across comparable rounds), and the loop paused for the user's reply instead of running the reconciliation and the one self-heal assessment its own policy orders before any pause. The duty text exists in review-plan's Scope and complexity policy, but nothing evaluates the triggers at the round close where the sidecars are written, so the decision was made by hand later from unread evidence. An unattended or standing-authorized loop therefore stalls on a question its policy already authorizes past.

## Gist & Examples

TLDR: Review-loop round closes gain a trigger-evaluation step and a standing-authorized run continues with its authorized self-heal option instead of pausing for a reply, so the loop keeps operating unattended (driving force: automation).

Before: in the witnessed run, round 4 closed with blocking rising 1 to 2 across comparable rounds r3 and r4; the session recognized the trigger by hand at the end, never consulted `extensions.convergence` or the `self_heal_attempt` state, skipped both the reconciliation and the self-heal assessment, and waited for the user's reply before applying the simplification that then converged in one round.

After: at every round close the orchestrator evaluates the churn and recurrence triggers against the two most recent comparable rounds' sidecars, records the evaluated outcome beside the round's convergence counters, and on a firing trigger in an unattended or standing-authorized run starts the non-convergence sequence at the close, applying the assessment's authorized simplification and continuing the loop without a user question.

Edge cases: fewer than two comparable rounds (the baseline round continues and no trigger fires, unchanged); the attempt state consumed, unknown, or the plan not authorizing the attempt, or no suitable option (the existing pause arms apply unchanged); a round whose sidecar never wrote convergence counters (its open-blocking count is read from its staged findings rows, so the comparison still works).

## Outcome

A non-converging review loop run under standing authorization evaluates its own triggers at the round close and continues past an authorized simplification without a user question.

- The controlling trigger outcome is recorded in each round's `extensions.convergence` beside the existing counters, so the convergence telemetry carries the decision input it was recorded from.
- An unattended or standing-authorized run applies the self-heal assessment's authorized option at the trigger and continues under the unchanged review budgets, cap-closure mechanics, and exit criteria.
- No new gate, validator, script, lock, ledger, schema field, or dispatch-pausing condition is added; the pause arms and every cap-closure and budget rule stay byte-identical in their terms.
- The insertions add 2328 bytes of operative text with no deletion (measured at the r3 fold over the three quoted insertion lines as they stand in these bytes: 1549 + 491 + 288, excluding the survival-note annotations; the figure moved 2055 to 2118 to 2328 as the r1 and r2 folds and the r3 telemetry-scoping clause grew the first snippet); both files sit under their byte-budget caps (measured at authoring: review-plan 76293 of 79202 bytes, plan-quality-gate 47459 of 50986 bytes), the unbalanced-growth class is priced ordinary by review-plan's Growth balance sentence, and no witness justifies deleting the mirrored restatements in this plan, so the advisory balance is a recorded acceptance rather than an implicit one.

Gate delta: none. The change clarifies prose duties in two skill files; it adds no refusal class, hard gate, fence, protocol layer, schema field, or condition that pauses dispatch or later work, and it converts a premature pause into an in-policy continuation. A mechanical evaluator script was considered and rejected: the machinery admission protocol requires a witnessed incident of a gate-shaped failure, and the witnessed failure is a skipped evaluation step, not a missing gate; the rejected disposition is recorded here so no follow-up re-litigates it without a fresh incident.

Follow-up disposition: a future incident showing the prose step still fails to execute (a second skipped-evaluation witness) files a fresh backlog row carrying that incident; this plan promotes none.

## Assumptions

- The witnessed round 4 trigger was active under the existing Reconciliation gate wording (a positive open-blocking count not decreasing across the two most recent comparable rounds); basis: the origin row and the r3 and r4 sidecars of the plan-review-gate-hook-round-tie series, total staged counts 5 then 6 with open blocking rising 1 to 2 (sidecar counts.staged_findings 5 and 6; blocking findings with unresolved triage 1 and 2).
- The round 4 sidecar's `extensions.convergence` carried only `self_heal_attempt` and no classification counters or blocker counts, so the evaluation step must derive the open-blocking count from the sidecar's findings rows when counters are absent; basis: the r4 sidecar read on 2026-11-20.
- The self-heal assessment procedure already exists (self-heal's Repeated review cycles section) and this plan adds no new assessment procedure; basis: read of `agents/skills/self-heal/SKILL.md` on 2026-11-20.
- The comparable-round definition and the comparison window (two most recent comparable rounds) stay as the Reconciliation gate defines them; this plan adds no redefinition.
- Prose over no-change: the smaller design is a bounded round-close evaluation step with an explicit unattended continuation sentence, chosen over no change because the witnessed failure is an unevaluated decision point whose timing is unpinned, not a wrong policy; the comparison and its evidence are recorded here per the maintenance-selected arm.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the evaluation reads counts that exist in every round's sidecar (findings rows), never depends on counters a round may not have written, and cannot pause a standing-authorized run while an authorized option exists.
- Simplicity: no new machinery; net text growth stays within the byte-budget gate's caps; the operative step single-homes in review-plan and the plans loop rule mirrors it by pointer.
- Maintainability: the inserted wording names its evidence sources (sidecars, findings rows) and preserves every existing pause, budget, and cap-closure term verbatim.

**Done when:**
- The Validation Commands block passes from the repository root over the changed tree, including the exactly-once counts and the ordering checks for every inserted span.
- Both edited files stay em-dash clean on added lines and the byte-budget gate's ceiling class stays clean.
- The readiness validator's full-gate mode passes over the plan bytes.

**Ship when:**
- The next non-converging review loop run under standing authorization evaluates the trigger at the round close, runs the reconciliation and the bounded self-heal assessment, applies the authorized simplification, and reaches a further review round without a user question (the origin row's Ship-when condition; external evidence owner: the next maintenance review loop over a non-converging plan, closure observed in that run's round records).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/review-plan/SKILL.md` (Task 1)
- `agents/skills/plans/plan-quality-gate.md` (Task 2)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/` (new validators, gate edits, or pin-suite rows); reason: the plan adds no machinery and must not edit gates or the pins suite.
- `agents/skills/self-heal/SKILL.md`; reason: the assessment procedure is unchanged by design.
- `review-loop`, `review-staging`, `doing-code-review` skills; reason: the witnessed gap is the plan-review loop's round close, not those surfaces.
- Sidecar schema or staging validator changes; reason: the evaluation records beside existing optional counters already sanctioned by the loop rules.

## Validation Commands

Validation preamble (authoring-time record, 2026-11-20): the span greps below are absent from both target files at authoring time (RED recorded: each `grep -qF` fired absent); the em-dash touched scan over both target files passed with zero hits; `bash scripts/scan-public-hygiene.sh` passed (`OUTCOME: pass`); `python3 scripts/skill_text_budget.py --check` passed (zero ceiling breaches, five advisory ratchet rows, one informational rolling-log row); `bash scripts/check_maintenance_pins.sh` recorded-red posture: exactly one `PIN FAIL: FINAL STEP prefix count` line, listed in the primary checkout's `.ai-playbook/maintenance/baseline-known-red-gates.json` under the maintenance_pins producer, with the counted literal at 2 both at the working tree and at the pre-session tip `a738046a0`, unchanged by this plan's surfaces, so the pins member passes with this note at its own sweep and fold-battery boundaries and is deliberately not re-run as a bare pass/fail command in this block (the baseline-aware battery at those boundaries owns the pass condition). The pins suite pins full literals elsewhere in the two target files; every pinned literal survives this plan's insertions byte-identical (verified by fixed-string grep at authoring time). The rule 22 authoring-time mechanical audit (pinned spans vs prescribed snippets, exactly-once, `bash -n` over this block) and the pre-round structural gate were executed over these plan bytes and passed: the audit found every pinned span present in its prescribed snippet with `bash -n` clean over this block, and the pre-round gate returned `readiness PRE-ROUND OK: structural checks clean` with `OUTCOME: pass` (recorded 2026-11-20; the em-dash fixer full mode over the plan made zero substitutions). The r1 fold batch (review-plan-nonconvergence-self-heal-at-round-close r1, 8 staged findings folded at wip 7e8742ef6) re-ran the rule 22 audit and the rule 8 and 36 joint simulation over the folded bytes: a faithful-landing scratch copy carrying all three prescribed insertions extracted mechanically from this plan passes all six ordering tuples and all eleven count gates, the swapped-adjacent-pair proof fails as required, and the delta classifier classified the fold unclassified (decision-bearing); the fresh round r2 therefore reviews the folded content (the three prescribed insertions unchanged since wip 7e8742ef6, whose plan bytes digest to dc00d29003ba) and re-binds the terminal sidecar's source_digest to the bytes it reviews per rule 9, never reusing a quoted digest.

```bash
REPO="$(git rev-parse --show-toplevel)" || exit 1
cd "$REPO" || exit 1
RPS="agents/skills/review-plan/SKILL.md"
PLQ="agents/skills/plans/plan-quality-gate.md"
test -f "$RPS" || { echo "missing $RPS"; exit 1; }
test -f "$PLQ" || { echo "missing $PLQ"; exit 1; }
# Task 1 spans: the round-close evaluation step (Reconciliation gate)
grep -qF 'The trigger evaluation is a round-close step, not a later hand read' "$RPS" || { echo "FAIL: evaluation-step sentence missing"; exit 1; }
grep -qF 'otherwise from its staged findings rows carrying `blocking: true` without a resolved triage value' "$RPS" || { echo "FAIL: counters fallback read missing"; exit 1; }
grep -qF 'the same two sidecars source the other arms' "$RPS" || { echo "FAIL: per-arm evidence sources missing"; exit 1; }
grep -qF 'The evaluation runs before the loop records the round' "$RPS" || { echo "FAIL: before-decision timing missing"; exit 1; }
grep -qF 'instead of a later hand-recognized pause' "$RPS" || { echo "FAIL: close-start clause missing"; exit 1; }
# Task 1 spans: the unattended continuation (Scope and complexity policy)
grep -qF 'An unattended or standing-authorized run does not pause for a user reply while the assessment names an option the execution plan explicitly authorizes' "$RPS" || { echo "FAIL: unattended continuation missing"; exit 1; }
grep -qF 'The pause arms of this policy stay the only pause paths: no suitable option, an unauthorized attempt, a consumed or unknown attempt state, the same blockers after a fresh review, and a review-budget breach.' "$RPS" || { echo "FAIL: pause-arms enumeration missing"; exit 1; }
# Task 2 span: the plans-loop mirror pointer
grep -qF 'The controlling trigger is evaluated at every round close, before the loop' "$PLQ" || { echo "FAIL: round-close timing pointer missing"; exit 1; }
grep -qF 'per the round-close evaluation step in review-plan' "$PLQ" || { echo "FAIL: mirror pointer missing"; exit 1; }
grep -qF 'which owns the recorded member set' "$PLQ" || { echo "FAIL: member-set owner clause missing"; exit 1; }
grep -qF 'adds no second procedure' "$PLQ" || { echo "FAIL: no-second-procedure clause missing"; exit 1; }
# Exactly-once counts for every inserted span (rule 33: count gates, not presence)
test "$(grep -oF 'The trigger evaluation is a round-close step' "$RPS" | wc -l | tr -d ' ')" -eq 1 || { echo "FAIL: evaluation sentence count"; exit 1; }
test "$(grep -oF 'otherwise from its staged findings rows carrying' "$RPS" | wc -l | tr -d ' ')" -eq 1 || { echo "FAIL: fallback read count"; exit 1; }
test "$(grep -oF 'the same two sidecars source the other arms' "$RPS" | wc -l | tr -d ' ')" -eq 1 || { echo "FAIL: per-arm sources count"; exit 1; }
test "$(grep -oF 'The evaluation runs before the loop records the round' "$RPS" | wc -l | tr -d ' ')" -eq 1 || { echo "FAIL: before-decision count"; exit 1; }
test "$(grep -oF 'instead of a later hand-recognized pause' "$RPS" | wc -l | tr -d ' ')" -eq 1 || { echo "FAIL: close-start count"; exit 1; }
test "$(grep -oF 'An unattended or standing-authorized run does not pause for a user reply' "$RPS" | wc -l | tr -d ' ')" -eq 1 || { echo "FAIL: continuation sentence count"; exit 1; }
test "$(grep -oF 'The pause arms of this policy stay the only pause paths' "$RPS" | wc -l | tr -d ' ')" -eq 1 || { echo "FAIL: pause-arms count"; exit 1; }
test "$(grep -oF 'The controlling trigger is evaluated at every round close' "$PLQ" | wc -l | tr -d ' ')" -eq 1 || { echo "FAIL: timing pointer count"; exit 1; }
test "$(grep -oF 'per the round-close evaluation step in review-plan' "$PLQ" | wc -l | tr -d ' ')" -eq 1 || { echo "FAIL: mirror pointer count"; exit 1; }
test "$(grep -oF 'which owns the recorded member set' "$PLQ" | wc -l | tr -d ' ')" -eq 1 || { echo "FAIL: member-set owner count"; exit 1; }
test "$(grep -oF 'adds no second procedure' "$PLQ" | wc -l | tr -d ' ')" -eq 1 || { echo "FAIL: no-second-procedure count"; exit 1; }
# Tail survival (replacement-span boundary rule): the anchor sentences after each insertion survive verbatim
grep -qF 'If a fresh review of the changed alternative leaves the same blockers, pause before another review.' "$RPS" || { echo "FAIL: policy tail sentence lost"; exit 1; }
grep -qF 'A configured cap alone does not trigger reconciliation.' "$PLQ" || { echo "FAIL: cap sentence lost"; exit 1; }
# Ordered adjacency (full chain): each insertion sits after its anchor and before its tail or section successor
python3 - <<'PYEOF'
import sys
rps = open("agents/skills/review-plan/SKILL.md", encoding="utf-8").read()
plq = open("agents/skills/plans/plan-quality-gate.md", encoding="utf-8").read()
checks = [
    (rps, "permitted mutation scope to reconciliation.", "The trigger evaluation is a round-close step"),
    (rps, "The trigger evaluation is a round-close step", "The reconciliation result is recorded in the next staging artifact"),
    (rps, "pause for operator direction before another change or review.", "An unattended or standing-authorized run does not pause for a user reply"),
    (rps, "An unattended or standing-authorized run does not pause for a user reply", "If a fresh review of the changed alternative leaves the same blockers"),
    (plq, "Record the previous and current blocker counts and the controlling trigger in `extensions.convergence` for each round.", "The controlling trigger is evaluated at every round close"),
    (plq, "The controlling trigger is evaluated at every round close", "A configured cap alone does not trigger reconciliation."),
]
for text, anchor, later in checks:
    a = text.find(anchor)
    n = text.find(later)
    if a < 0 or n < 0 or not (a < n):
        print("FAIL: ordering broken for anchor:", anchor[:48])
        sys.exit(1)
print("ordering ok")
PYEOF
# Mechanical gates over the whole change
bash scripts/check-no-em-dash.sh added-lines --base "$(git merge-base main HEAD)" || { echo "FAIL: em-dash on added lines"; exit 1; }
bash scripts/scan-public-hygiene.sh || { echo "FAIL: public hygiene"; exit 1; }
python3 scripts/skill_text_budget.py --check || { echo "FAIL: byte budget ceiling class"; exit 1; }
```

### Task 1: Round-close evaluation step and unattended continuation in review-plan

Context surface: the plan's Terms and this task.

Files:
- `agents/skills/review-plan/SKILL.md`

- [ ] Insert the quoted paragraph verbatim as a new paragraph in the `## Reconciliation gate` section, immediately after the sentence ending `permitted mutation scope to reconciliation.` and before the paragraph beginning `The reconciliation result is recorded`: [class: IMPLEMENTATION_REQUIRED]
  The trigger evaluation is a round-close step, not a later hand read: at every round close, while the round's staging sidecar is written, the orchestrator evaluates the churn and recurrence triggers against the two most recent comparable rounds and records the evaluated outcome in the round's `extensions.convergence` (the controlling trigger among the evaluated churn and recurrence arms, or `none` when no evaluated arm fired, with the two compared open-blocking counts; review evidence self-contradiction remains the gate's separate in-round reconcile condition and stays outside this recorded member set). Each round's open-blocking count is read from that round's own sidecar, from its written convergence blocker counts when present and otherwise from its staged findings rows carrying `blocking: true` without a resolved triage value, so a round whose convergence counters were never written still yields the count the trigger compares; the same two sidecars source the other arms (the findings rows' pattern fields, whose owner prefix names the lens per the sidecar pattern-id contract, for the fold-defect and wording ratio arm, the staged findings row count for the total-staged arm, and cross-round pattern recurrence for the recurrence trigger). The evaluation runs before the loop records the round's continue-or-pause decision; when a trigger fires at the close, the Scope and complexity policy's non-convergence sequence (reconcile, then the bounded self-heal assessment) starts at that close instead of a later hand-recognized pause.
- [ ] Insert the quoted sentences verbatim into the `Scope and complexity policy` paragraph of the same file, immediately after the sentence ending `pause for operator direction before another change or review.` and before the sentence beginning `If a fresh review of the changed alternative`: [class: IMPLEMENTATION_REQUIRED]
  An unattended or standing-authorized run does not pause for a user reply while the assessment names an option the execution plan explicitly authorizes: the run carries out that option and continues the loop under the unchanged review budgets, cap-closure mechanics, and exit criteria. The pause arms of this policy stay the only pause paths: no suitable option, an unauthorized attempt, a consumed or unknown attempt state, the same blockers after a fresh review, and a review-budget breach.
  The existing sentence `If a fresh review of the changed alternative leaves the same blockers, pause before another review.` survives verbatim after the insertion.
- [ ] Run → expect RED before the insertions and GREEN after: each Task 1 span grep in Validation Commands is absent from the file at authoring time (RED recorded in the preamble) and present exactly once once both insertions land. [class: REPOSITORY_TEST]
- [ ] Run the touched-set gates: the em-dash added-lines scan, the public-hygiene scan, and the byte-budget gate `--check` (ceiling class clean). [class: REPOSITORY_TEST]
- [ ] Commit: `review-plan: evaluate convergence triggers at round close and continue unattended past an authorized option` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Plans-loop mirror pointer for the round-close timing

Context surface: the plan's Terms and this task.

Files:
- `agents/skills/plans/plan-quality-gate.md`

- [ ] Insert the quoted sentence verbatim into rule 13 of the file, immediately after the sentence ending `Record the previous and current blocker counts and the controlling trigger in `extensions.convergence` for each round.` and before the sentence beginning `A configured cap alone does not trigger reconciliation.`: [class: IMPLEMENTATION_REQUIRED]
  The controlling trigger is evaluated at every round close, before the loop's continue-or-pause decision for the round, per the round-close evaluation step in review-plan's Reconciliation gate, which owns the recorded member set; this rule mirrors that timing and adds no second procedure.
  The existing sentence `A configured cap alone does not trigger reconciliation.` survives verbatim after the insertion.
- [ ] Run → expect RED before and GREEN after the insertion: the Task 2 span greps in Validation Commands (the timing pointer, the mirror pointer, the member-set owner clause, and the no-second-procedure clause) turn present-exactly-once. [class: REPOSITORY_TEST]
- [ ] Commit: `plans: mirror the round-close trigger-evaluation timing in the loop rules` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Joint battery over the changed tree

Context surface: the plan's Terms and this task.

Files: none (verification only; no file changes).

- [ ] Run the complete Validation Commands block from the repository root over the changed tree and expect every command green, with the pins recorded-red note carried where the loop's own battery runs the pins suite. [class: REPOSITORY_TEST]
- [ ] Verify cross-file consistency: the plans mirror sentence names review-plan's Reconciliation gate, and each of the three insertions occurs exactly once in its file with its anchor and tail sentences intact. [class: REPOSITORY_TEST]

## Documentation Impact Assessment

No documentation surface changes. The two edited files are the operative skill texts themselves and are routed by their own module dispatch tables; no `docs/` page, registry row, or README entry carries this behavior, and the plans skill's module list already names `plan-quality-gate.md`.
