# Plan: grill-answer readiness gate + Step 1.4 duplication

Backlog origins:
- `docs/history/backlog/2026-09-08-plans-grill-answer-required-readiness-gate.md` (primary, Medium)
- `docs/history/backlog/2026-09-07-plans-step14-meta-rule-grilling-duplication.md` (joined, Low)

## Terms

- **Material question**: a Phase 1 decision point whose answer changes plan scope, tasks, invariants, or Validation Commands; the units the confidence gate routes to `grill-with-docs`.
- **Answer state**: per-question status `open` or `closed` in the requirements buffer. A question is `open` from the moment it is asked until the user answers THAT question or accepts its recommendation via the opt-in phrase.
- **Opt-in phrase**: the exact user sentence "accept the recommendation for this question"; the only way to accept a pending recommendation without answering.
- **Decision receipt**: the one-line record left per closed question: decision, source, date, affected plan section.
- **Decision-points trailer**: the plain line starting `Decision points requiring a grill:` inside the plan's `## Assumptions` section, mechanically gated by `scripts/plan_readiness.py`.
- **Consolidated assumptions list**: the single list of clear or safely inferable items, never asked as questions, presented once at the end of the interview before readiness confirmation.

## Assumptions

- assume the open-question blocker lives in the existing decision-points trailer: a still-open material question renders there as an `open: <question>` receipt and the mechanical gate treats an `open` start as unresolved; basis: the trailer is already the digest-bound mechanical surface for decision receipts (2026-09-05 plan-readiness migration), and no separate durable state file exists in the workflow.
- assume the joined duplication item resolves as its option 2 (confirmation-time self-containment kept, bidirectional sync notes added); basis: the backlog item itself records that the Step 1.4 confirmation must gate when the grilling skill is not loaded, so a cross-reference pointer would weaken the confirmation-time gate.
- assume the backlog's five regression scenarios plus the assumptions-list scenario are covered by (a) new `plan_readiness.py` selftest cases for the trailer behavior and (b) fixed-string probe greps pinning each prescribed rule text in the three skill files; basis: the repo's deterministic fixture harness for workflow text is the validator selftest plus probe greps, the standing practice of prior skill-wording plans.
- assume README catalog entries stay unchanged; basis: no skill trigger or usage phrase changes, only intra-skill workflow rules, and the task constraint says update README only if trigger/usage text changes.
- assume grilling SKILL.md's existing "No generic acknowledgement confirms a material choice" block is the canonical home for the restate/resume rule and the opt-in phrase; basis: the primary backlog item names grilling as the generic-acknowledgement rule owner and the joined item's option 2 keeps grilling canonical.

Decision points requiring a grill: Step 1.4 duplication cross-reference vs self-containment: resolved as option 2, self-containment plus bidirectional sync notes (standing pre-authorization, backlog item options, 2026-09-08); open-question blocker mechanism: resolved as decision-points trailer extension with `open` as an unresolved placeholder stem (standing pre-authorization, probe showed an `open:` trailer passes today's gate, 2026-09-08)

## Gist & Examples

What changes: an unanswered material grill question becomes a hard blocker on plan readiness, and the interview gains explicit answer-state semantics so generic acknowledgements can never silently accept a recommendation. The plans Step 1.4 confirmation meta-rule duplication versus the grilling skill is settled as deliberate self-containment with sync notes.

Why: during PROJ-691 plan authoring on 2026-09-08 the user answered a material grill question with "go on"; the session read that as permission to continue authoring with the recommendation, while the user meant "continue asking". The plan then looked execution-ready while a user-owned decision stood unanswered. There was no mechanical gate that could catch this: the readiness validator only checks the decision-points trailer for placeholder stems `pending`, `tbd`, and `todo`, so an open question that never entered the trailer as one of those stems is invisible.

**Before (today):** the user says "go on" after a question carrying a recommendation. The authoring agent proceeds with the recommendation, never records a receipt, the plan carries no trace of the open decision, and the readiness gate passes `ready=yes` on a fresh review. A plan whose trailer reads `Decision points requiring a grill: open: phased-rollout decision` passes `decision_marker_problem` today (verified by probe at authoring time: returns `None`).

**After (this plan):** the same "go on" resumes the interview: the agent restates the same question or asks the next one, and the pending recommendation stays unaccepted. The plan can only be edited for non-decision facts or question framing while a question is open, and the trailer must carry `open: <question>`; `plan_readiness.py` fails it with "unresolved decision-points trailer". When the user answers, a one-line receipt replaces the open marker, and only the exact opt-in phrase "accept the recommendation for this question" closes a question without an answer. Example trailer states:

```text
OPEN:    Decision points requiring a grill: open: is the rollout phased or single deploy
CLOSED:  Decision points requiring a grill: rollout: phased (user answer 2026-09-08, affects Evaluation Criteria)
```

A receipt starting with the hyphenated word `open-question` still passes (the hyphen carve-out works exactly as for the pinned `todo-list` receipt), so the new stem does not reject legitimately worded receipts.

Edge cases motivating the design:

- "go on" after a recommended question: asks the next question (or restates the same one); the original question stays `open`; no receipt is written.
- "accept the recommendation": records the recommendation as the user decision, with a receipt.
- an answer to a different question: does not close the unanswered question; both states are tracked per question.
- review of a plan with one open question: the mechanical gate fails, so `ready=no` is enforced regardless of the review panel's verdict text.
- all receipts present: the trailer carries no open markers and the normal fresh-review path proceeds unchanged.
- assumptions-list scenario: items that are safely inferable or already decided are never asked; they surface once, in the consolidated assumptions list of the Step 1.4 confirmation block, where a single "no" vetoes any wrong assumption.

Joined item decision: the plans Step 1.4 meta-rule keeps restating the generic-acknowledgement and lifecycle-verb clauses (option 2, confirmation-time self-containment) and both files gain a sync note naming the mirrored clauses, so a future edit to either surface knows to update the peer in the same change.

## Evaluation Criteria

**Quality dimensions:**

- correctness: every acceptance criterion of both backlog items maps to a task checklist item or a probe in Validation Commands; the `open:` trailer RED-today probe (recorded above) flips to a failing gate after Task 2.
- mechanical gate integrity: `python3 scripts/plan_readiness.py --selftest` exits 0 including the two new cases; the hyphen-carve-out characterization (`open-question` receipt passes) stays green.
- no-drift: the mirrored rule surfaces in grilling and plans name each other through Integration Points sync notes, so a future edit to one knows to update the other.
- minimal blast radius: the existing fresh plan-review panel, review staging contract, sidecar schema, and branch/push authorization are untouched; the only validator change is the placeholder stem set and its documentation.

**Done when:**

- grilling SKILL.md carries: the restate/resume rule, the per-question answer state, the opt-in phrase, the per-question receipt rule, the question-economy and consolidated-assumptions-list rule, and the sync note.
- plans SKILL.md carries: the Step 1.4 meta-rule state-machine clauses, the readiness-contract blocker sentence, the sixth pre-finalization self-check question, the updated trailer paragraph naming `open`, and the sync note.
- grill-with-docs SKILL.md carries the answer-state and receipt reference in its workflow.
- `scripts/plan_readiness.py` rejects an `open:`-prefixed trailer value, a `open:`-bearing segment of a mixed trailer, and a `<`-bearing segment, each with the existing unresolved-trailer reason; its selftest covers open-fails, mixed-open-fails, mixed-template-fails, receipt-passes, and hyphen-carve-out-passes; full selftest exits 0.
- Both backlog items' acceptance criteria verifiably hold via the Validation Commands block.

**Ship when:**

- The next real plan-authoring session exercises the state machine against a live user and the PROJ-691 "go on" scenario behaves as specified; prose only, human-owned observation.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `scripts/plan_readiness.py` (placeholder stem set in `_PLACEHOLDER_RE`, its vocabulary comment, `decision_marker_problem` docstring, and the `_selftest_decision_marker` fixture family)

**Instruction files:**

- `agents/skills/grilling/SKILL.md`
- `agents/skills/grill-with-docs/SKILL.md`
- `agents/skills/plans/SKILL.md` (Step 1.4 meta-rule comment, readiness contract, pre-finalization self-check, Plan Format trailer paragraph, Integration Points)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- `README.md`; reason: no skill trigger or usage text changes, so the catalog stays as is per the task constraint.
- `agents/skills/execute-plan/SKILL.md` and `agents/skills/review-plan/SKILL.md`; reason: the fresh review panel and execution flow are invariant; only the plans readiness contract and the mechanical gate change.
- `docs/history/backlog/*.md`; reason: backlog items move to completed only in the plan-completion pass, not by execution tasks.

## Design Invariants (CR Guard)

- The fresh plan-review panel stays intact: no change to review-plan worker selection, review staging, sidecar schema, or verdict grammar.
- The existing trailer contract for CLOSED receipts and `none remain` is unchanged: `none remain.` passes, non-placeholder receipts pass, `pending`/`tbd`/`todo` stems still fail, the hyphen carve-out (`todo-list`) still passes. The change ADDS the `open` stem to the same fail-closed family AND extends the stem check to every semicolon-separated receipt segment; the mixed mid-interview trailer (closed receipts plus one `open:` segment) must fail, which a start-only check provably misses.
- No branch or push authorization wording changes in any skill.
- `scripts/plan_readiness.py` stays the single mechanical gate; no parallel checker is introduced.
- The receipt field set introduced by this plan is four fields (decision, source, date, affected plan section); tasks 4 and 5 align the older three-field receipt sentences in plans and grill-with-docs to the same four-field form so the workflow carries one receipt shape.
- `grilling` and `grill-with-docs` are vendored skills (`metadata.upstream`); this plan deepens the local fork. Task 6 captures a backlog item recording the fork so a future upstream `rsync --delete` sync does not silently drop the new rules.

## Validation Commands

```bash
#!/usr/bin/env bash
# Run from the repository root. Every check aborts non-zero on miss.
set -u

fail() { echo "VALIDATION FAIL: $1"; exit 1; }
expect_pin() { # expect_pin <file> <fixed-string>
  grep -qF -- "$2" "$1" || fail "missing in $1: $2"
}

# 1. Mechanical gate: full selftest must stay green (includes the new cases).
python3 scripts/plan_readiness.py --selftest > /dev/null 2>&1 || fail "plan_readiness selftest"
python3 - <<'PY' || fail "open-trailer gate probe"
import sys
sys.path.insert(0, "scripts")
from plan_readiness import decision_marker_problem
if decision_marker_problem("# P\n\n## Assumptions\n\nDecision points requiring a grill: open: phased-rollout decision\n") is None:
    sys.exit(1)
if decision_marker_problem("# P\n\n## Assumptions\n\nDecision points requiring a grill: rollout: phased (user confirmed 2026-09-08); open: is the migration coupled\n") is None:
    sys.exit(1)
if decision_marker_problem("# P\n\n## Assumptions\n\nDecision points requiring a grill: rollout: phased (user confirmed 2026-09-08); <point>: <receipt>\n") is None:
    sys.exit(1)
if decision_marker_problem("# P\n\n## Assumptions\n\nDecision points requiring a grill: rollout: phased (user confirmed 2026-09-08)\n") is not None:
    sys.exit(1)
if decision_marker_problem("# P\n\n## Assumptions\n\nDecision points requiring a grill: open-question policy: receipts in trailer (user confirmed 2026-09-08)\n") is not None:
    sys.exit(1)
PY

# 2. grilling SKILL.md pins (answer state, opt-in phrase, receipts, economy).
G=agents/skills/grilling/SKILL.md
expect_pin "$G" 'accept the recommendation for this question'
expect_pin "$G" 'RESUMES the interview (restate the same question or ask the next one)'
expect_pin "$G" 'an answer to a different question does not close the unanswered one'
expect_pin "$G" 'record a one-line decision receipt (decision, source, date, affected plan section) before asking the next question'
expect_pin "$G" 'presented as one consolidated list at the end of the interview'

# 3. plans SKILL.md pins (meta-rule clauses, readiness blocker, trailer paragraph, sync note).
P=agents/skills/plans/SKILL.md
expect_pin "$P" 'the only acceptance without answering is the explicit opt-in phrase'
expect_pin "$P" 'the Assumptions trailer carries it as `open: <question>` so the mechanical readiness gate fails'
expect_pin "$P" 'any open material grill question or unresolved scope-extension decision is not ready'
expect_pin "$P" 'pending, tbd, todo, or open'
expect_pin "$P" 'semicolon-separated (never comma-separated; the readiness gate splits receipt segments on semicolons only)'
expect_pin "$P" '<one-line receipt: user decision, source, date, affected plan section>'
expect_pin "$P" 'must update the peer in the same change'
# The old both-separators wording must be gone from BOTH occurrences.
if grep -qF 'comma- or semicolon-separated' "$P"; then fail "stale comma-or-semicolon separator wording in $P"; fi

# 4. grill-with-docs SKILL.md pin.
expect_pin agents/skills/grill-with-docs/SKILL.md 'never present a plan or RFC as ready while any question is open'

# 5. grilling SKILL.md sync note pin.
expect_pin "$G" 'must update the peer in the same change'

# 6. No em-dash in the three changed instruction files. Scoped to Markdown
# on purpose: check-no-em-dash.sh skips non-prose paths (plan_readiness.py
# legitimately carries U+2014 in existing docstrings), so a .py operand
# would make this guard vacuous.
for f in "$G" "$P" agents/skills/grill-with-docs/SKILL.md; do
  bash scripts/check-no-em-dash.sh file "$f" || fail "em-dash in $f"
done

echo "ALL VALIDATION CHECKS PASSED"
```

Probe provenance notes: every pin in checks 2 to 5 is a span absent from the tree today (verified by fixed-string grep at authoring time on 2026-09-08), so each probe is RED before its task lands and flips GREEN exactly when the prescribed text is written; the stale-separator forbidden check in check 3 fires today (both "comma- or semicolon-separated" occurrences exist in the plans skill) and goes silent exactly when the Task 4 separator change lands. The probe in check 1 is RED-today in its first three halves (verified at authoring time: `decision_marker_problem` returns `None` for the open trailer, the mixed closed-plus-open trailer, and the mixed closed-plus-template trailer on the current tree) and GREEN-today in its last two halves (both receipts already pass), pinning the characterization; the mixed-trailer halves are the regression catchers for the per-segment stem and template-token checks.

### Task 1: RED selftest cases for the open-question trailer gate

Files:
- `scripts/plan_readiness.py`

- [x] In `_selftest_decision_marker`'s case table, add case `gated_open_trailer_fails`: plan text `# P\n\n## Assumptions\n\n{trailer}open: phased-rollout decision\n`, round date `2026-09-08`, expected `False`, expected reason substring `unresolved decision-points trailer`; given a plan whose decision-points trailer starts with `open:`, expects the mechanical gate to reject it
- [x] In the same table, add case `gated_mixed_open_segment_fails`: plan text using `{trailer}rollout: phased (user confirmed 2026-09-08); open: is the migration coupled\n`, round date `2026-09-08`, expected `False`, expected reason substring `unresolved decision-points trailer`; given a mixed trailer whose value starts with a CLOSED receipt but carries a semicolon-separated `open:` segment later, expects the gate to reject it (the mid-interview state: previously answered questions plus a newly open one)
- [x] In the same table, add case `gated_mixed_template_segment_fails`: plan text using `{trailer}rollout: phased (user confirmed 2026-09-08); <point>: <receipt>\n`, round date `2026-09-08`, expected `False`, expected reason substring `unresolved decision-points trailer`; given a mixed trailer whose later segment starts with the `<` template token, expects the gate to reject it
- [x] In the same table, add characterization case `open_question_hyphen_receipt_passes`: plan text using `{trailer}open-question policy: receipts in trailer (user confirmed 2026-09-08)`, round date `2026-09-08`, expected `True`; given a legitimately worded receipt whose first word is the hyphenated `open-question`, expects the gate to keep passing it (hyphen carve-out, mirrors the pinned `todo-list` receipt)
- [x] Run → expect RED exactly on `gated_open_trailer_fails`, `gated_mixed_open_segment_fails`, and `gated_mixed_template_segment_fails`, and GREEN on their sibling cases including `open_question_hyphen_receipt_passes` and `gated_receipt_passes` (at this task point neither stem handling nor segment splitting exists, so all three open-marker and template-marker cases fail; the hyphen case already passes on today's code, verified by probe at authoring time): `python3 scripts/plan_readiness.py --selftest`

### Task 2: GREEN implementation of the open placeholder stem

Files:
- `scripts/plan_readiness.py`

- [x] Extend `_PLACEHOLDER_RE` from `^(pending|tbd|todo)(?!-)` to `^(pending|tbd|todo|open)(?!-)`; update the placeholder-vocabulary comment above it to name `open` as a stem, note that the hyphen carve-out preserves receipts like `open-question policy: ...`, and record the receipt-wording constraints this shares with the existing stems: a receipt segment must not begin with a bare stem word (reword it or hyphenate, e.g. "open-question"), since only the hyphen arm escapes the stem, and a receipt must not contain a semicolon, because any `;` starts a new segment under the per-segment split (use commas inside a receipt instead)
- [x] Extend `decision_marker_problem` to check the stem PER RECEIPT SEGMENT, not only at the value start: split the trailer value on `;`, apply `_PLACEHOLDER_RE` to the start of each stripped segment, extend the same per-segment treatment to the `<` template-token condition (a segment starting with `<` is unresolved wherever it sits), and return the existing reason `unresolved decision-points trailer: <value>` when ANY segment matches; a value whose every segment starts with `none remain`, a non-placeholder receipt, or a hyphen-escaped stem passes. The semicolon is the separator this plan prescribes for multi-receipt trailers; comma splitting is deliberately NOT used because commas inside receipt parentheticals would false-split (this plan's own Gist example carries commas inside parentheses). This is load-bearing for the mixed mid-interview state (closed receipts plus one newly open question), which a start-only check provably misses
- [x] Update the `decision_marker_problem` docstring's stem list (`pending`, `tbd`, `todo`, or a `<` template token) to include `open` and to describe the per-segment semantics (segment start = value start or the start after any `;`, applied to both the stem regex and the `<` token check)
- [x] Run → expect GREEN: `python3 scripts/plan_readiness.py --selftest`
- [x] Commit: `scripts: readiness gate rejects open decision-point trailers`

### Task 3: grilling SKILL.md answer-state rules

Files:
- `agents/skills/grilling/SKILL.md`

- [x] Replace the "No generic acknowledgement confirms a material choice" block with an expanded block that keeps its first sentence verbatim and appends, in this order: (a) the answer-state rule: after a material question is asked it stays `open` until the user gives an answer that addresses THAT question or explicitly rejects the recommended option; (b) the resume rule, containing verbatim `RESUMES the interview (restate the same question or ask the next one)` and the rule that a generic acknowledgement or continue request such as "go on" never accepts the pending recommendation; (c) verbatim `an answer to a different question does not close the unanswered one`; (d) the opt-in rule: the only way to accept the recommendation without answering is the exact phrase `accept the recommendation for this question`, never inferred from "sure", "okay", "go on", or an adjacent answer; (e) verbatim `record a one-line decision receipt (decision, source, date, affected plan section) before asking the next question`
- [x] Add a new block "Question economy and the consolidated assumptions list" stating: only genuinely unclear decisions are asked; anything safely inferable or already decided is never asked; every clear assumption is collected and `presented as one consolidated list at the end of the interview` (verbatim pin), before the shared-understanding or readiness confirmation, so wrong assumptions can be vetoed in a single pass
- [x] In the Integration Points "With `plans` skill" section, add the sync note: the plans Step 1.4 confirmation meta-rule mirrors this skill's generic-acknowledgement, lifecycle-verb, answer-state, and opt-in-phrase clauses for confirmation-time self-containment, so an edit to either set of clauses `must update the peer in the same change` (verbatim pin)
- [x] Commit: `skills: grilling answer-state rules with opt-in phrase and receipts`

### Task 4: plans SKILL.md state machine, readiness blocker, trailer paragraph, sync note

Files:
- `agents/skills/plans/SKILL.md`

- [x] In the Step 1.4 confirmation meta-rule comment (the HTML comment after the Step 1.4 template), append after the lifecycle-verb sentence: (a) verbatim `any open material grill question or unresolved scope-extension decision is not ready` for the readiness transition: while one stands the plan may be edited only for non-decision facts or question framing and the confirmation cannot proceed to readiness; (b) verbatim `the Assumptions trailer carries it as \`open: <question>\` so the mechanical readiness gate fails`; (c) the resume rule: a generic acknowledgement or continue request restates or resumes the interview instead of accepting the pending recommendation; (d) verbatim `the only acceptance without answering is the explicit opt-in phrase` "accept the recommendation for this question"; (e) the receipt rule mirroring grilling: each closed question leaves a one-line receipt (decision, source, date, affected plan section) in the Decision points requiring a grill subsection before the next question; (f) the economy rule: clear or safely inferable items are never asked and surface only in this block's single consolidated assumptions list
- [x] In the "Ready for execution" definition paragraph (the one starting "**Ready for execution** means the latest review artifact"), add the sentence: verbatim `any open material grill question or unresolved scope-extension decision is not ready`, whatever the review verdict says; and in the "Pre-finalization self-check" numbered list, update its intro from "answer these five questions" to "answer these six questions" and add question 6: does any material grill question or scope-extension decision remain open (any `open:` receipt in the decision-points trailer), noting the agent must not describe the plan as ready when any answer is negative
- [x] In the Plan Format section's Assumptions trailer paragraph, update the placeholder semantics from a value-start check on "pending, tbd, or todo" to verbatim `pending, tbd, todo, or open` checked at the start of the value and of every semicolon-separated receipt segment (including `<`-starting segments), so the skill text matches the per-segment validator contract
- [x] Change both "comma- or semicolon-separated" receipt separators in the plans SKILL.md (the Step 1.4 confirmation template's "carried into the plan's single Assumptions trailer line" clause and the Plan Format Assumptions paragraph) to verbatim `semicolon-separated (never comma-separated; the readiness gate splits receipt segments on semicolons only)`; comma splitting is rejected because commas inside receipt parentheticals would false-split, and a comma-separated mixed trailer would otherwise bypass the per-segment open check. In the SAME Step 1.4 template line, update the receipt token `<one-line receipt: user decision, source, date>` to verbatim `<one-line receipt: user decision, source, date, affected plan section>` so the template's receipt shape matches the four-field rule (verify the token's surrounding line keeps the "or the literal line ... none remain." alternative intact)
- [x] In the Phase 1 confidence-gate prose (the "Decision-ambiguity scan" paragraph), align its receipt field list to the four-field form used by this plan's receipt rule (decision, source, date, affected plan section) so the workflow carries one receipt shape
- [x] In the Integration Points "With `grilling` skill" section, add the mirror sync note naming the Step 1.4 meta-rule clauses that restate grilling's generic-acknowledgement, lifecycle-verb, answer-state, and opt-in-phrase rules, ending with verbatim `must update the peer in the same change`
- [x] Commit: `skills: plans Phase 1 open-question readiness blocker and trailer contract`

### Task 5: grill-with-docs SKILL.md interview state reference

Files:
- `agents/skills/grill-with-docs/SKILL.md`

- [x] In workflow step 2 (the "Follow `grilling`" step), append a sentence stating the interview tracks each material question's answer state per the grilling rules: a question stays open until the user answers that question or says the opt-in phrase "accept the recommendation for this question"; generic acknowledgements resume the interview; a one-line receipt is recorded per closed question during the interview; the session must `never present a plan or RFC as ready while any question is open` (verbatim pin); clear or safely inferable items are never asked and surface in the one consolidated assumptions list at the end of the interview. Do not place this under step 3 (the domain-modeling rules); it belongs with the grilling-follow step so it binds every interview, doc capture or not
- [x] In the "With `rfc-design` / `plans` skills" Integration Points section, align the receipt field list in the sentence about recording the answer as a one-line receipt to the four-field form (decision, source, date, affected plan section)
- [x] Commit: `skills: grill-with-docs carries answer state and receipts`

### Task 6: full validation and hygiene gate

Files: none (verification only)

- [x] Run the complete Validation Commands block from the repository root → expect `ALL VALIDATION CHECKS PASSED`
- [x] Run `bash scripts/scan-public-hygiene.sh` from the repository root → expect exit 0
- [x] Capture a backlog item under `docs/history/backlog/` recording that `agents/skills/grilling/` and `agents/skills/grill-with-docs/` now carry a deliberate local fork of upstream-vendored skills (the answer-state, opt-in-phrase, receipts, and consolidated-assumptions-list rules), so a future upstream `rsync --delete` sync re-applies or consciously drops these rules instead of silently losing them
- [x] Commit any remaining unstaged plan-owned files: `plans: grill-answer state machine validation and hygiene pass`

## Disposition of migrated backlog items

- docs/history/backlog/completed/2026-09-08-plans-grill-answer-required-readiness-gate.md: disposition folded into 2026-09-08-plans-grill-answer-state-machine.md (2026-09-25); per-item file deleted.
