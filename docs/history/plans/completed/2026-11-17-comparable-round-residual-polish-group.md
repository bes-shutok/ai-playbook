# Plan: comparable-round residual polish group

Residual polish over the churn-trigger comparability amendment (docs/history/plans/completed/2026-11-08-churn-trigger-degraded-round-comparability.md, executed at 93385f2f987d6d82f774c6870872d98df9ebd5e4); the certifying r1 review's deferred findings were filed as the six durable origin rows below.

Backlog origins (scope of record):

- docs/history/backlog/2026-11-16-churn-ratio-arm-window-coverage-gap.md
- docs/history/backlog/2026-11-16-reconciliation-audit-note-window-count.md
- docs/history/backlog/2026-11-16-coverage-degraded-term-undefined-in-skill-text.md
- docs/history/backlog/2026-11-16-blocking-arm-adjacency-vs-window-phrasing.md
- docs/history/backlog/2026-11-16-reconciliation-audit-note-window-count.md (Task 2 Span C pure-pointer shape)
- docs/history/backlog/2026-11-16-coverage-degraded-term-undefined-in-skill-text.md (Task 2 reuses the defined comparable-round term; no second definition)
- docs/history/backlog/2026-11-16-churn-ratio-arm-window-coverage-gap.md (Task 1 ratio-arm qualification)
- docs/history/backlog/2026-11-16-reconciliation-audit-note-window-count.md (Task 2 Span C pure-pointer shape)
- docs/history/backlog/2026-11-16-coverage-degraded-term-undefined-in-skill-text.md (Task 2 reuses the defined comparable-round term; no second definition)
- docs/history/backlog/2026-11-16-continuation-rule-zero-comparable-rounds-state.md
- docs/history/backlog/2026-11-16-continuation-rule-degraded-current-side-trajectory.md

Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-17-plan-review-comparable-round-residual-polish-group-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 1h total, largest task 0.5h
Executed: yes (<recorded tip: branch tip pre-squash, recorded at landing>)
Authoring claim: comparable-round-residual-polish-group.md (session sess_c2bfca1b-10a2-418d-ab15-ca95a9188871)

## Terms

- comparable round: a review round whose staging sidecar coverage outcome is neither `degraded` nor `failed` and whose panel carries no row whose status is anything other than `complete`; defined once in review-plan's Reconciliation gate.
- coverage-degraded round: any round that is not a comparable round.
- churn trigger: review-plan's measured non-convergence trigger over staged-findings and open-blocking totals.
- ratio arm: the churn trigger's first arm, fold-defect plus wording findings exceeding half of the measured round's staged findings.
- fold-defect finding: a staged review finding reporting a defect in a prior fold of the reviewed artifact.
- wording finding: a staged review finding reporting prose precision or consistency, with no behavioral claim.
- totals arms: the churn trigger's second and third arms, comparing counts across rounds.
- continuation rule: the Scope and complexity policy sentence deciding whether the review loop continues without asking for direction.
- baseline arm: the sentence continuing one review round while the trajectory baseline is not yet established.
- audit note: the review-reconciliation Trigger-section sentence recorded when auditing a measured firing.
- exclusion line: the prose line a round record carries naming an excluded window member.
- window: the rounds a churn-trigger arm compares.

## Why

The comparability amendment made the churn trigger's two totals arms run over comparable rounds, but its own review left four text states uncovered: the ratio arm still fires on partial staged findings, the audit note restates the window without the owned count and names an exclusion term defined only in a plan's Terms, and the continuation rule has no defined behavior while fewer than two comparable rounds exist or over a degraded current round. Loop-control decisions should not run on non-comparable data.

## Gist & Examples

TLDR: The trigger's ratio arm and the continuation rule are qualified to comparable rounds and the audit note defers to the owned window definition, closing the partial-data decision paths the comparability amendment left open (code-quality).

Before: a coverage-degraded round stages 4 findings from a 5-worker panel, 3 of them fold-defect or wording; the ratio arm fires reconciliation on the partial set. After: the arm measures a comparable round's staged findings, so the partial round cannot fire it.

Before: a run with fewer than two comparable rounds has blocker counts but no comparison reference; the continuation rule's reference does not exist, so two sections of the same policy hand the loop opposite instructions. After: the baseline arm continues one round, the same disposition the Reconciliation gate already prescribes.

Before: the current round is degraded and its partial blocking count is tested against the previous comparable round, so the loop can continue over a rising trajectory or pause on partial data. After: the comparison is skipped for that round, its record carries the exclusion line, and the baseline guards decide.

Before: the audit note's window carries no count and names an exclusion term no skill text defines. After: the note reads the window shape and the exclusion set from the owned definition and has no restated fragment left to drift.

## Outcome

Every churn-trigger and continuation decision in the review loop runs over comparable rounds only, and the reconciliation audit reads the window from its single owned definition.

- The churn trigger's three arms all measure comparable data, so a coverage-degraded round can no longer fire the ratio arm on partial staged findings.
- A run with fewer than two comparable rounds continues one round to establish the baseline instead of an undefined stop.
- A non-comparable current round can no longer drive the continue-without-asking decision from a partial count; its record carries the exclusion line and the baseline guards decide.
- The reconciliation audit note restates no window fragment, so the count and shape cannot drift from the owned definition again.

Gate delta: prose-only amendments to two skill files, replacing existing sentence spans in place; net machinery across refusal classes, hard gates, fences, protocol layers, schema fields, and dispatch-pausing conditions: none added and none removed; the one prose-duty extension (the exclusion-line recording now also covers the continuation rule's skipped comparison) mirrors the recorded-line duty the completed comparability amendment already established and closes the witnessed partial-data decision class (the six origin rows' deferred findings F1 through F5 and B1); no blocking review-layer duty declared; no gate or fence added, so no gate-liveness ledger citation applies.

## Assumptions

- assume the six origins amend within the two owning skill files and create no new file; basis: each origin row's Evidence and Expected name existing sentences in agents/skills/review-plan/SKILL.md or agents/skills/review-reconciliation/SKILL.md.
- assume the zero-open-blockers continuation leg stays unqualified; basis: the degraded-current-side origin's Expected scopes the fix to the trajectory comparison, and the zero-open-blockers state is the plan's own blocker ledger rather than a panel-derived estimate.
- assume the term comparable round stays defined once, in review-plan's Reconciliation gate; basis: the executed amendment placed the two-arm definition there and the audit-note fix points at it instead of duplicating it.
- Decision receipts (maintenance-selected arm, one per origin): the ratio-arm origin qualifies the arm over narrowing the outcome claims, because the covering plan's Outcome declares the spurious-fire class ended and qualification mirrors the shape already applied to the totals arms; the audit-note origin takes the pure-pointer shape over a count restatement or a pinned-mirror appositive, because the covering plan already converted the review-loop duplicate to a pointer and the restated count is the drift that produced the finding; the undefined-term origin reuses the defined term over adding a second definition, because the definition already lives in the owning gate; the window-phrasing origin unifies both totals arms on the two-most-recent window over defining consecutive, because one window shape reads simpler than a term only one arm uses; the zero-comparable origin amends the baseline sentence's condition to the gate's own fewer-than-two condition over extending the owning row, because the owning gate's baseline arm already fixes the comparable-round sense and the text contradiction is the defect, the condition covering the zero and the exactly-one comparable-round states (the r1 F1 fold); the degraded-current-side origin qualifies both sides of the trajectory comparison with the mirrored exclusion line over a caveat-only recording, because a caveat alone still lets the partial count drive the decision.

Decision points requiring a grill: none remain.

## Standing constraints

- Operative skill text carries no incident narrative and cites no backlog path; land the rule, not the story (repository anti-growth rule).
- Skill-text growth stays within the byte-budget gate's blocking ceilings; `python3 scripts/skill_text_budget.py --check` must exit 0 after the amendment.

## Evaluation Criteria

**Quality dimensions:**
- correctness: each amended sentence implements exactly its origin row's selected Expected arm (the decision receipts in Assumptions) and nothing else
- consistency: the trigger's three arms name one window shape, and the continuation rule and the Reconciliation gate's baseline arm give the loop one instruction per state
- minimality: only the prescribed sentence spans change in the two files; no drive-by rewrites
- anti-growth: no incident narrative or backlog-path citation in the amended text; the byte-budget gate exits 0

**Done when:**
- the Validation Commands block passes green over the amended tree
- the em-dash gate, the public hygiene scan, and the pre-round readiness gate pass over the plan bytes

**Ship when:**
- none; the change is repository-verifiable prose only.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/review-plan/SKILL.md` (Task 1)
- `agents/skills/review-reconciliation/SKILL.md` (Task 2)

**Tests:**
- none; validation is the grep-based block below over the amended text.

Partially-in-scope freeze note: in each listed file, only the sentence spans the tasks prescribe may change; all other lines in both files are frozen; reject any review finding that touches them.

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/history/plans/completed/2026-11-08-churn-trigger-degraded-round-comparability.md`; completed-history bytes are immutable context, not an edit surface.
- `agents/skills/review-loop/SKILL.md`; rule 5 already resolves the trigger through the owned definition and no origin names it as an edit target.

## Validation Commands

Authoring-time record (2026-11-17): the plan bytes passed `bash scripts/check-no-em-dash.sh touched` (exit 0, zero hits), `bash scripts/scan-public-hygiene.sh` (OUTCOME: pass), and `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-11-17-comparable-round-residual-polish-group.md` (readiness PRE-ROUND OK, structural checks clean, OUTCOME: pass). RED-today evidence executed against the target files' current bytes at authoring time: the forbidden pins are present today (exceeding half of staged findings, two consecutive comparable rounds, When no prior blocker count exists, coverage-degraded rounds are excluded, and most recent comparable rounds in review-reconciliation each 1 hit), the positive amendment pins are absent today, the G5 tail pins and G7 are green today by design (regression guards over text that already exists), and executing the block today fails at the first gate (G1 count got 0 want 1, exit 1), so the block is red as a whole before the tasks land and green exactly when they do. Mechanical audit (validation authoring rule on pinned spans): the block passes `bash -n` clean, and every pinned span occurs exactly once in a task prescription beside its single occurrence as a gate literal.

```bash
REPO="$(git rev-parse --show-toplevel)" || exit 1
cd "$REPO" || exit 1
RP="agents/skills/review-plan/SKILL.md"
RR="agents/skills/review-reconciliation/SKILL.md"
test -f "$RP" || { echo "missing $RP"; exit 1; }
test -f "$RR" || { echo "missing $RR"; exit 1; }

expect_absent() {
  rc=0; grep -qF -- "$1" "$2" || rc=$?
  if [ "$rc" -eq 0 ]; then echo "FORBIDDEN PRESENT: $1"; exit 1; fi
  if [ "$rc" -ge 2 ]; then echo "TOOL ERROR rc=$rc on: $1"; exit 1; fi
}
expect_present() {
  rc=0; grep -qF -- "$1" "$2" || rc=$?
  if [ "$rc" -ne 0 ]; then echo "MISSING (rc=$rc): $1"; exit 1; fi
}
expect_count() {
  n=$(grep -oF -- "$1" "$2" | wc -l | tr -d ' ')
  if [ "$n" -ne "$3" ]; then echo "COUNT MISMATCH: $1 got $n want $3"; exit 1; fi
}

# G1 ratio arm qualified (Task 1 Span A)
expect_count 'exceeding half of a comparable round' "$RP" 1
expect_absent 'exceeding half of staged findings' "$RP"

# G2 window shape unified across both totals arms (Task 1 Span A)
expect_absent 'two consecutive comparable rounds' "$RP"
expect_count 'the two most recent comparable rounds' "$RP" 2

# G3 baseline arm keys on the gate's own condition, covering zero and exactly one comparable rounds (Task 1 Span B)
expect_absent 'When no prior blocker count exists' "$RP"
expect_count 'When fewer than two comparable rounds exist, continue one review round' "$RP" 1

# G4 trajectory comparison qualified on the current side, exclusion line mirrored (Task 1 Span B)
expect_count 'the current round is a comparable round whose blocking count fell' "$RP" 1
expect_count 'the trajectory comparison is skipped for that round' "$RP" 1
expect_count 'carries the same excluded-window prose line' "$RP" 1

# G5 surviving tails byte-identical (Task 1 and Task 2 boundary guarantee)
expect_count 'A comparable round is a review round whose staging sidecar coverage outcome' "$RP" 1
expect_count 'Any active churn or recurrence trigger means non-convergence' "$RP" 1
expect_count 'a window with fewer than two comparable rounds is a baseline gap, not a firing' "$RR" 1

# G6 audit note defers to the owned definition, restatement gone (Task 2 Span C)
expect_absent 'coverage-degraded rounds are excluded' "$RR"
expect_absent 'most recent comparable rounds' "$RR"
expect_count 'not comparable under the definition in review-plan' "$RR" 1

# G7 byte-budget gate green over the amended skill text
python3 scripts/skill_text_budget.py --check >/dev/null 2>&1 || { echo "byte-budget gate failed"; exit 1; }

echo "validation: all gates green"
```

### Task 1: review-plan comparability completion

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/review-plan/SKILL.md`

Primary class anchors:
- `Reconciliation gate` in `agents/skills/review-plan/SKILL.md`
- `Scope and complexity policy` in `agents/skills/review-plan/SKILL.md`

Prescribed replacements, verbatim spans; each old span is text present today in the named section, each new span replaces it exactly, and all other bytes of the file are unchanged. Span A sits in the Reconciliation gate's cycle paragraph; Span B sits in the Scope and complexity policy's trajectory-reflection paragraph.

Span A, old:
"Reconcile before another panel when the same root issue recurs, review evidence contradicts itself, or the measured churn trigger fires against `extensions.convergence`: fold-defect plus wording findings exceeding half of staged findings, total staged findings not decreasing across the two most recent comparable rounds, or a positive open-blocking count not decreasing across two consecutive comparable rounds."

Span A, new:
"Reconcile before another panel when the same root issue recurs, review evidence contradicts itself, or the measured churn trigger fires against `extensions.convergence`: fold-defect plus wording findings exceeding half of a comparable round's staged findings, total staged findings not decreasing across the two most recent comparable rounds, or a positive open-blocking count not decreasing across the two most recent comparable rounds."

Span B, old:
"When no prior blocker count exists, continue one review round to establish the trajectory baseline if blockers remain and no churn or recurrence trigger is active. After a baseline exists, continue without asking for direction when no mechanical-churn or recurrence trigger is active and either the blocking count fell from the previous comparable round or there are zero open blockers."

Span B, new:
"When fewer than two comparable rounds exist, continue one review round to establish the trajectory baseline if blockers remain and no churn or recurrence trigger is active. After a comparable baseline exists, continue without asking for direction when no mechanical-churn or recurrence trigger is active and either the current round is a comparable round whose blocking count fell from the previous comparable round or there are zero open blockers; when the current round is not a comparable round, the trajectory comparison is skipped for that round, its round record carries the same excluded-window prose line the Reconciliation gate prescribes for an excluded window member, and the loop continues one round under the same guards as the baseline-establishment sentence."

Surviving tails, byte-identical before and after: the definition sentence following Span A opens "A comparable round is a review round whose staging sidecar coverage outcome"; the sentence following Span B opens "Any active churn or recurrence trigger means non-convergence".

- [x] Span A is replaced verbatim: the ratio arm measures a comparable round's staged findings, and both totals arms name the two most recent comparable rounds [class: IMPLEMENTATION_REQUIRED]
- [x] Span B is replaced verbatim: the baseline arm keys on fewer than two comparable rounds, the trajectory comparison requires a comparable current round, and a non-comparable current round records the exclusion line and continues under the baseline guards [class: IMPLEMENTATION_REQUIRED]
- [x] Both surviving tails are byte-identical to their pre-amendment text [class: REPOSITORY_TEST]
- [x] The amended spans carry no incident narrative and no backlog-path citation [class: REPOSITORY_TEST]
- [x] Run the Validation Commands block: expect the Task 1 gates green and the Task 2 gates still red at this task point [class: REPOSITORY_TEST]
- [x] Commit: `review: comparability reaches the ratio arm and the continuation rule` [class: IMPLEMENTATION_REQUIRED]

### Task 2: review-reconciliation audit note pointer

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/review-reconciliation/SKILL.md`

Primary class anchors:
- `Trigger` in `agents/skills/review-reconciliation/SKILL.md`

Prescribed replacement, verbatim span; the old span is the audit note's whole line in the Trigger section, the new span replaces it exactly, and all other bytes of the file are unchanged.

Span C, old:
"When auditing a measured churn-trigger firing, coverage-degraded rounds are excluded from the comparison window and the window runs over the most recent comparable rounds, defined in review-plan's Reconciliation gate; a window with fewer than two comparable rounds is a baseline gap, not a firing."

Span C, new:
"When auditing a measured churn-trigger firing, rounds that are not comparable under the definition in review-plan's Reconciliation gate are excluded from the comparison window that gate owns; a window with fewer than two comparable rounds is a baseline gap, not a firing."

- [x] Span C is replaced verbatim: the exclusion set is named through the defined comparable-round term and no window count or shape fragment is restated [class: IMPLEMENTATION_REQUIRED]
- [x] The surviving tail (a window with fewer than two comparable rounds is a baseline gap, not a firing) is byte-identical to its pre-amendment text [class: REPOSITORY_TEST]
- [x] The amended span carries no incident narrative and no backlog-path citation [class: REPOSITORY_TEST]
- [x] Run the full Validation Commands block: expect all gates green at this task point [class: REPOSITORY_TEST]
- [x] Commit: `review: reconciliation audit note defers to the owned window definition` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

Folded and deleted at execution completion per the plans skill's completion pass:

- docs/history/backlog/2026-11-16-blocking-arm-adjacency-vs-window-phrasing.md
- docs/history/backlog/2026-11-16-reconciliation-audit-note-window-count.md (Task 2 Span C pure-pointer shape)
- docs/history/backlog/2026-11-16-coverage-degraded-term-undefined-in-skill-text.md (Task 2 reuses the defined comparable-round term; no second definition)
- docs/history/backlog/2026-11-16-churn-ratio-arm-window-coverage-gap.md (Task 1 ratio-arm qualification)
- docs/history/backlog/2026-11-16-continuation-rule-zero-comparable-rounds-state.md
- docs/history/backlog/2026-11-16-continuation-rule-degraded-current-side-trajectory.md

Each origin's selected Expected arm landed verbatim in this plan's Task 1 spans (window phrasing, baseline condition, trajectory qualification with the mirrored exclusion line); the rows carried no residual scope beyond the landed spans.
