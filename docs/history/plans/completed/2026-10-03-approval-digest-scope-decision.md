# Plan: The approval-digest binding scope decision: present, decide, record

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-02-review-approval-digest-byte-coupling.md`

Driving force: consistency (outside the closed taxonomy: this plan closes a silent flagged inconsistency between the review machinery's digest behavior and its recorded rationale by landing the explicit operator decision the origin routes for; park-triage would take it - the row is operator-routed, design-decision class, and its decision input atrophies as the record corpus grows)
Plan review record: the staging series docs/reviews/2026-10-03-plan-review-approval-digest-scope-decision-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

The approval-digest whole-file binding scope carries an explicit recorded operator decision instead of staying a silent flagged gap.

- The decision home (docs/maintenance/project-decisions.md) records the operator's choice - scoped approval digests, or the whole-file coupling consciously accepted - as a dated ADR entry carrying the rationale, the considered options, and the consequences.
- Under a scoped-binding choice whose follow-up pricing clears the machinery cost-benefit adjudication's bar, the mechanism exists as a sanctioned backlog origin instead of an unpriced idea; under a failed pricing or an accept choice, the consciously-accepted rationale is the written record.
- The survey-flagged gap stops being silent either way: the coupling's witnessed cost and its accepted-or-scoped outcome are written down where the review machinery is owned.

Gate delta: none - no refusal class, hard gate, fence, protocol layer, or schema state field is added, extended, or removed; the plan's surfaces are a decision record and one conditional backlog row.

## Gist & Examples

TLDR: the whole-file approval-digest coupling gets an explicit recorded operator decision instead of staying a silent flagged gap - the plan lands as the decision presentation itself (authored and landed, never executed per the 2026-10-02 lane closure), landing flips the origin covered as the ownership marker with the execution-time fold still owed, and the origin's Expected closes at execution when the recorded decision lands: a mechanism follow-up row only if the operator picks scoped binding and its pricing clears the machinery cost-benefit adjudication's bar, otherwise the acceptance record in the decision home beside the review machinery; consistency driving force, because the survey flagged the coupling in 2026-09-29 and the origin's whole point is that the gap stops being silent either way.

Decision presentation (the plan's authoring content; the operator decides at execution):

- **Witnessed cost of the coupling:** review approval digests bind whole files, so any byte change anywhere forces whole-round revalidation - the coupling applies to every multi-round series by construction (any byte change re-binds the whole round's approval digest), and the redundant re-approval it causes is directly witnessed across the landed record: sixty-two consecutive-round digest pairs re-approved byte-identical files, and a one-line fold re-binds the certification digest for the entire document.
- **Option A, scoped approval digests:** a region-or-section notion with an explicit per-round revalidation-scope statement. Benefit: unchanged regions stop re-binding the certification. Costs: real machinery (a scope grammar, validator changes, per-round scope statements in every record), which must clear the machinery cost-benefit adjudication's bar (2026-09-28 adjudication caps machinery growth) before any mechanism lands; partial mitigations already exist (targeted rounds, verification-only follow-up rounds, per-round source digests proving which rounds re-reviewed byte-identical files).
- **Option B, consciously accepted whole-file coupling:** zero machinery; the written rationale: whole-file binding is the conservative invariant (a changed document re-certifies whole, never partial), the redundant re-approval in cap-closure rounds is the accepted price of that simplicity, and the mitigations above already bound the common cases. The acceptance record lands in docs/maintenance/project-decisions.md (the decision home's ADR trail), and the coupling stops being silent.
- **The decision question, verbatim for the operator:** should review approval digests gain a scope/region notion with an explicit per-round revalidation-scope statement (Option A, machinery, adjudication-gated), or is the whole-file coupling consciously accepted with this rationale recorded (Option B, documentation-only)?

## Terms

- **The decision record:** the dated operator decision (Option A or Option B) recorded in docs/maintenance/project-decisions.md as an ADR entry with the chosen option's rationale; the artifact that closes the origin's Expected either way at execution.
- **The mechanism follow-up row:** a new backlog origin naming the scope/region grammar, the validator changes, and the per-round revalidation-scope statement, filed only when the operator picks Option A and the adjudication bar is cleared in the follow-up row's draft pricing.
- **The adjudicated-out amendment:** the Option A arm's failure branch: the draft pricing fails the adjudication bar, no row is filed, and the Task 1 decision entry's consequences gain the machinery-adjudicated-out rationale (the coupling stays whole-file, consciously accepted on pricing grounds) - which satisfies the origin's Expected acceptance branch.
- **Adjudication bar:** the machinery cost-benefit adjudication (docs/history/plans/completed/2026-09-29-plans-machinery-delta-doctrine.md): new machinery is priced on witnessed failures and rejected when its cost exceeds the incident class it prevents.
- **The committed-baseline em-dash gate:** the no-em-dash scan in its `added-lines --base main` form scoped by pathspec; the `--base HEAD` default is vacuous after the edited lines are committed, because re-scanning committed insertions is out of the default mode's scope by design.

## Coordination (binding, not re-litigating)

- The cluster sibling review-token-round-attribution landed and archived before this plan's draft (landed 49688320, origin covered 6d1194b6, archived at docs/history/plans/completed/2026-10-03-review-token-round-attribution.md); its per-round lineage work is adjacent but does not decide the digest binding scope, so this plan's decision stands alone.
- The reviews-home-alignment cluster sibling is landed; the reviews-home path is not this plan's surface.
- The review machinery's digest behavior (scripts/review_record_selection.py and the staging validator's source_digest binding) is never edited by this plan; Option A's machinery, if chosen, is the follow-up row's scope, not this plan's.
- The operator execution-lane closure (operator directive, 2026-10-02) means authoring only; the operator gate is this plan's first task by design (the PLAN-PROMPTS entry's authoring constraint).

## Review Scope

Every task's Files path, inventoried:

- docs/history/plans/2026-10-03-approval-digest-scope-decision.md (the landing-time authoring surface)
- docs/maintenance/project-decisions.md (Task 1's entry; Task 2's adjudicated-out amendment arm)
- docs/history/backlog/2026-10-03-approval-digest-scoped-binding.md (Task 2's conditional follow-up row, created only under Option A with cleared pricing)

The origin row (docs/history/backlog/2026-10-02-review-approval-digest-byte-coupling.md) is record scope, never a task edit: landing flips it covered as the ownership marker, and its fold-and-delete lands in this plan's completion pass. Gates re-checked but not edited: agents/skills/review-staging/SKILL.md (the digest behavior's owning skill, read for the presentation's accuracy), scripts/review_record_selection.py, scripts/validate_review_staging.py. Harness touched: none (decision-class; the only code surfaces are conditional follow-up scope, never this plan's edits). Reviewers verify the presentation's cost write-ups are re-derived from the witnessed record, the decision question is operator-ready verbatim, the three follow-through outcomes (A with cleared pricing, A with failed pricing, B) are exclusive and complete, and neither arm pre-commits the operator's choice.

## Tasks

### Task 1: the operator gate - present the question, record the decision (the plan's first task)

Files:
- `docs/maintenance/project-decisions.md`

Evidence:
- the Decision presentation block in this plan's Gist (authored at landing); the ADR trail's entry shape (ADR-0001 through ADR-0004)

- [x] RED: `grep -cE "^## ADR-[0-9]+: approval-digest binding scope" docs/maintenance/project-decisions.md` returns 0 today (the decision home carries no recorded decision, which is the silent state this plan closes) [class: REPOSITORY_TEST]
- [x] Re-verify the presentation is operator-ready against the live record before presenting: both options carry their benefits and costs (Option A's machinery scope against the adjudication bar and the existing partial mitigations; Option B's conservative-invariant rationale with the accepted cap-closure price), the decision question is stated verbatim in the Gist, and neither arm is pre-committed [class: IMPLEMENTATION_REQUIRED]
- [x] Present the Gist's decision question to the operator and record the answer as a dated ADR entry appended at the bottom of docs/maintenance/project-decisions.md (the home's newest-last convention): heading `## ADR-<next free number>: approval-digest binding scope decided`, body naming the choice (Option A, scoped approval digests, or Option B, the whole-file coupling consciously accepted), the chosen option's rationale as written in the presentation, the considered options, the consequences, and the origin row's path [class: IMPLEMENTATION_REQUIRED]
- [x] Count gate: `grep -cE "^## ADR-[0-9]+: approval-digest binding scope" docs/maintenance/project-decisions.md` returns exactly 1 (the gate counts the mandated heading token, immune to prose rementions of the subject; the subject's pinned spelling is the heading's hyphenated "approval-digest binding scope") [class: REPOSITORY_TEST]
- [x] Commit: `docs: record the approval-digest binding scope decision` [class: IMPLEMENTATION_REQUIRED]

### Task 2: the conditional follow-through and the origin closure

Files:
- `docs/history/backlog/2026-10-03-approval-digest-scoped-binding.md` *(new)* (created only under Option A with cleared pricing)
- `docs/maintenance/project-decisions.md` (the adjudicated-out amendment arm only)

Evidence:
- the operator's recorded choice (Task 1's entry); the follow-up row's draft pricing against the adjudication bar

- [x] Conditional on Option A: draft the mechanism follow-up row's pricing first (the scope grammar, the validator changes, the per-round revalidation-scope statements, priced against the machinery cost-benefit adjudication's bar in the draft's own text); if the draft pricing clears the bar, file the row at the listed path so the operator's choice has a sanctioned routing; if the draft pricing fails the bar, file nothing and apply the adjudicated-out amendment to the Task 1 entry's consequences [class: IMPLEMENTATION_REQUIRED]
- [x] Conditional on Option B: no follow-up row is filed (the acceptance record is the closure) [class: IMPLEMENTATION_REQUIRED]
- [x] Confirm the origin's Expected closes: the decision is recorded in the decision home either way (the landing-time coverage flip marked ownership only - a covered origin still owes the execution-time fold - and the origin row's fold-and-delete lands in this plan's completion pass per the plans skill) [class: REPOSITORY_TEST]
- [x] Commit: `docs: approval-digest decision follow-through and closure` [class: IMPLEMENTATION_REQUIRED]

## Validation Commands

```
grep -cE "^## ADR-[0-9]+: approval-digest binding scope" docs/maintenance/project-decisions.md   # 0 before execution; exactly 1 after Task 1
bash scripts/check-no-em-dash.sh added-lines --base main -- docs/history/plans/2026-10-03-approval-digest-scope-decision.md   # landing-time: this plan's inserted lines
bash scripts/check-no-em-dash.sh added-lines --base main -- docs/maintenance/project-decisions.md   # execution-time: the recorded entry's inserted lines
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

## Evaluation Criteria

1. The decision presentation carries both options with re-derived costs and a verbatim operator-ready question, pre-committing neither arm, and the three follow-through outcomes (Option A with cleared pricing, Option A with failed pricing, Option B) are exclusive and complete (Gist, Terms, Task 2).
2. The operator's answer is recorded as a dated ADR entry in the decision home, exactly once by the mandated heading token, naming the origin row (Task 1).
3. The conditional follow-through matches the choice and its pricing (the mechanism row only under Option A with cleared pricing; the adjudicated-out amendment otherwise under Option A; nothing under Option B), and the origin's Expected closes at execution either way (Task 2).

## Done When

- Every checkbox is `[x]`, the Validation Commands are GREEN, and the review rounds returned ready with zero blocking findings.
- The plan is landed; per the execution lane closure (operator directive, 2026-10-02) this plan is authored and landed, never executed - the operator gate inside Task 1 is the first thing its future execution performs.

## Assumptions

- The decision home (docs/maintenance/project-decisions.md) is the right recording surface for the operator's choice; basis: the ADR trail precedent and the origin's "recorded where the review machinery is owned".
- The origin's "Route through the operator before any authoring" routes as the execution-time operator gate (Task 1) rather than a pre-authoring grill; basis: the decision presentation is self-contained in the Gist so the operator decides on the recorded costs, the 2026-10-02 execution-lane closure keeps the authoring lane machine-driven, and the PLAN-PROMPTS entry's authoring constraint sanctions exactly this shape (the decision gate is the plan's first task).
- The presentation's cost write-ups are the authoring-time state of the witnessed record (the sixty-two-pair witness included); the operator decides on the live numbers at execution.
- The plan carries no machinery: both landing arms are documentation-only from this plan's side (Option A's machinery belongs to the follow-up row it files).

Decision points requiring a grill: operator-binding-scope-choice - deferred to the execution-time operator gate per the origin's routing (decision: the operator picks Option A or Option B at Task 1 from the Gist's recorded presentation, source: docs/history/backlog/2026-10-02-review-approval-digest-byte-coupling.md "Route through the operator before any authoring" and the PLAN-PROMPTS entry's authoring constraint, date: 2026-10-03, affected: Task 1 and the Terms).
