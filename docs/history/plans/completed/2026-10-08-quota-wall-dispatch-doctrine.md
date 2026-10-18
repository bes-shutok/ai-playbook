# Plan: Quota-wall dispatch doctrine (two refusal classes, one hardened probe, a visible launch ledger)

Backlog origin: docs/history/backlog/2026-10-08-quota-wall-dispatch-doctrine.md
Driving force: automation
Plan review record: the staging series docs/history/reviews/2026-10-08-plan-review-quota-wall-dispatch-doctrine-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 1.5h total, largest task 0.75h

## Terms

- **Transient rate-limit refusal:** a provider launch refusal whose error names no reset time hours away (momentary capacity or throttling); the class the landed bounded-retry budget already governs.
- **Usage-wall refusal:** a provider refusal whose error text names a reset timestamp hours in the future (the rolling usage window's oldest request aging out); the class this doctrine re-weights.
- **Mid-run usage-wall death:** a worker that launched successfully and later died on the usage wall; the structured `rate_limited` stop and end lines the Timeout protocol already records are its recognition and recording surface (the typed `dispatch_failed:` line stays pre-start only, exactly as landed).
- **Hardened probe:** the single post-usage-wall relaunch whose resume point is recorded first through the existing `pre_restart:`/`pre_restart_paths:` pair in the session manifest (the manifest stays the resume source of truth; no second resume record is invented).
- **Timed resume:** the one-shot automation armed at the reset time the refusal named; when the arming session cannot create (the lineage cap or a statically absent primitive), the landed clocked-order contract (docs/history/plans/completed/2026-10-05-authoring-clocked-resume-order.md: the park, the consult, and the runtime's clocked-order operations) owns the parked order. This plan never invents a second carrier path.
- **Launch ledger line:** the per-wave record `launch-wave: <n> <launched|transient|usage-wall> died-at <ISO timestamp|active>` in the session manifest's free-text lines; the operator-facing visibility receipt, not a new surface.
- **Wave ordinal:** the launch ledger's `<n>`: the 1-based launch sequence of one worker role at one boundary, equal to that role's existing per-path pass number for single-role waves; a multi-role wave writes one ledger line per role as `launch-wave: <role> <n> ...` so the ordinal never collides across roles.
- **Dispatch-failure contract (unchanged):** the landed typed `dispatch_failed:` line, its closed reason-code set (`model-capacity`, `thread-limit`, `rate-limit`, `other`), and the three-attempt bounded-retry budget; this doctrine never widens or rewrites them.

## Why

On 2026-10-07 a review worker was relaunched four times against a known usage wall: three relaunches died on the wall and the fourth succeeded roughly two hours before the nominal reset, so probes are not purely wasted (the window slides), but the same episode's real recurring cost was visibility: the operator asked why restarts had not happened while the second retry was already running, because restart actions were invisible across turns. The landed dispatch-failure contract deliberately left post-death retry policy open; today both refusal classes ride the same ad hoc relaunch loop.

## Gist & Examples

TLDR: Two dispatch-failure classes get distinct policy and a visible per-wave ledger, so usage walls stop burning probes and restarts stop being invisible (driving force: automation).

Before: every relaunch rides the same ad hoc loop regardless of the refusal's class; a usage wall burns the full three-attempt budget; the manifest's typed failure lines never summarize into a per-wave history, so the operator must ask what happened.
After: a transient refusal retries exactly as landed; a usage-wall refusal (the error names a reset time hours away) gets one hardened probe with the `pre_restart:` pair recorded first, and on that probe's death the lane arms the timed resume at the recorded reset instead of consuming the remaining budget; every wave appends one `launch-wave:` line, so the manifest alone answers the operator's visibility question.

## Outcome

Dispatch decisions distinguish the two refusal classes, a usage wall costs one hardened probe plus a timed resume instead of the full probe budget, and every dispatch wave is visible in the manifest without asking.

- A transient rate-limit refusal retries within the landed bounded-retry budget exactly as landed; nothing about the transient path changes.
- A usage-wall refusal gets one hardened probe (the `pre_restart:` pair recorded first), and on that probe's death the lane arms the timed resume at the recorded reset, or parks the order under the landed clocked-order contract when the session cannot arm.
- Every dispatch wave appends one launch ledger line beside the existing per-path pass numbering, so a reader reconstructs every wave's outcome from the manifest alone.
- The operator directives home carries the amended standing direction superseding the conversational restart direction for this repository's lanes.

Gate delta: adds one doctrine classification rule (two refusal classes where the dispatch text had one ad hoc loop; the paying sibling arm is the landed bounded-retry budget, which keeps owning the transient class unchanged, and the typed contract stays byte-identical), one manifest free-text line shape (the launch ledger, riding the existing per-path pass numbering, no new surface or schema field), and one directives-home record in the home's existing D-record shape (the conversational restart direction it supersedes is named in its witness); removes nothing.

## Assumptions

- The usage-wall class is recognized from the refusal's error text naming a reset time (hours away), not from a new reason code: the typed set stays closed and the doctrine reads the quoted error the `dispatch_failed:` line already carries. Basis: the landed reason-code contract and the origin row's demand not to reopen it.
- The rolling window sometimes clears early (the witnessed fourth probe succeeded about two hours before the nominal reset), so exactly one hardened probe retains value before the timed resume arms. Basis: the origin row's rejected alternative "stop retrying entirely" and its witness.
- The timed resume arm rides the landed clocked-order contract (docs/history/plans/completed/2026-10-05-authoring-clocked-resume-order.md), never a second carrier path; this plan executes independently of any other pending plan. Basis: the origin row's suggested direction and the landed contract's coverage of the park-and-arm shape.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the two-class boundary classifies from the error text alone; an error naming no reset time is transient under the landed budget, never doctrine-governed.
- composition: the typed `dispatch_failed:` line, its reason-code set, and the budget numbers are byte-identical before and after execution.
- visibility: a manifest across a multi-wave episode reconstructs every wave's outcome without chat history.

**Done when:**
- `scripts/test_quota_wall_doctrine.py` (new) runs green with the classification, ledger-shape, and deviation witnesses.
- The doctrine block exists in the execution skill's Sub-Agent Launch Rules and the maintenance overlay's Dispatch discipline bullet; the ledger line contract exists in the Phase 3 tracking list and agent-logs.md; the directive record exists in the directives home.

**Ship when:**
- The next real usage-wall episode lands launch ledger lines in its manifest without operator prompting (human-owned condition; no checklist item).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/execute-plan/SKILL.md` (Sub-Agent Launch Rules dispatch paragraphs and the Phase 3 tracking list)
- `agents/skills/maintenance/zcode.md` (the Dispatch discipline bullet)
- `docs/maintenance/operator-directives.md` (the new D-record)
- `agents/skills/execute-plan/agent-logs.md` (the per-path pass numbering sentence)

**Tests:**
- `scripts/test_quota_wall_doctrine.py` *(new)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- The execute-plan runtime driver modules; reason: the doctrine is dispatch policy text plus manifest line shapes, not runtime machinery, and the landed contract deliberately left this loop to policy.

## Validation Commands

```bash
"$HOME/.ai-playbook/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_quota_wall_doctrine.py -q
bash scripts/check_maintenance_pins.sh
bash "${HOME}/.ai-playbook/scripts/scan-public-hygiene.sh"
```

### Task 1: The doctrine rule block (execution and maintenance dispatch discipline)

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `scripts/test_quota_wall_doctrine.py` *(new)*

Primary class anchors:
- `Sub-Agent Launch Rules` in `agents/skills/execute-plan/SKILL.md`, the dispatch-mode paragraph
- `Dispatch discipline` in `agents/skills/maintenance/zcode.md`, the bullet

- [x] The execution skill's Sub-Agent Launch Rules carry the doctrine block beside the bounded-retry budget sentence; the typed `dispatch_failed:` line, its reason-code set, and the budget numbers are unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] The doctrine block classifies a transient rate-limit refusal as retrying within the landed budget, and a usage-wall refusal (the error names a reset time hours away) as getting one hardened probe with the `pre_restart:`/`pre_restart_paths:` pair recorded into the session manifest before the launch. [class: IMPLEMENTATION_REQUIRED]
- [x] The doctrine block routes a mid-run usage-wall death, recognized through the structured `rate_limited` stop/end lines, through the same doctrine: on the hardened probe's death the lane arms the timed resume at the recorded reset (or parks the order under the landed clocked-order contract when the session cannot arm) instead of consuming the remaining budget. [class: IMPLEMENTATION_REQUIRED]
- [x] The maintenance overlay's Dispatch discipline bullet mirrors the two-class rule in two sentences referencing the execution skill's block as the rule's home, so an unattended payload lifts the doctrine at dispatch time without a second copy of the mechanics. [class: IMPLEMENTATION_REQUIRED]
- [x] Witness (doctrine classification): given a manifest fixture whose `dispatch_failed:` line quotes a reset-time error and whose `pre_restart:` pair precedes exactly one relaunch, expects the test-local classifier to call it doctrine-conformant (one probe, ledger line classed usage-wall). [class: REPOSITORY_TEST]
- [x] Witness (doctrine deviation and transient): given the same fixture with a second usage-wall death and no timed-resume or parked-order record, expects the named doctrine deviation; given an error quoting no reset time, expects transient classification under the landed budget. [class: REPOSITORY_TEST]
- [x] Run → expect RED: the new test file's classification witnesses fail against the unmodified skill text (the classifier reads the skill block's literals). [class: IMPLEMENTATION_REQUIRED]
- [x] Write minimal implementation (the two rule texts above). [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `scripts/test_quota_wall_doctrine.py` passes; the execute-plan and maintenance pins literals over the touched spans stay green. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: quota-wall dispatch doctrine block in the execution and maintenance dispatch discipline` [class: IMPLEMENTATION_REQUIRED]

### Task 2: The launch ledger line (visibility receipt)

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/agent-logs.md`
- `scripts/test_quota_wall_doctrine.py`

Primary class anchors:
- `Phase 3 tracking list` in `agents/skills/execute-plan/SKILL.md`, the tracking list

- [x] The Phase 3 tracking list defines the launch ledger line `launch-wave: <n> <launched|transient|usage-wall> died-at <ISO timestamp|active>`: appended once per dispatch wave per worker role to the session manifest's free-text lines (the `<n>` is that role's 1-based launch sequence at the boundary, the per-path pass number; a multi-role wave writes one line per role as `launch-wave: <role> <n> ...`), and mirrored beside the `pre_restart:` pair when a usage-wall probe hardens. [class: IMPLEMENTATION_REQUIRED]
- [x] `agent-logs.md`'s per-path pass numbering section gains one sentence: the launch ledger line rides the same numbering so a reader reconstructs every wave's outcome from the manifest alone. [class: IMPLEMENTATION_REQUIRED]
- [x] Witness (ledger shape): given a three-wave manifest fixture (launched, usage-wall death, timed-resume arm), expects three ordered ledger lines whose ordinals and classes read in sequence; given a multi-role wave fixture, expects one line per role with the role token; given a boundary with zero dispatch attempts, expects no ledger line. [class: REPOSITORY_TEST]
- [x] Run → expect RED: the ledger witnesses fail against the unmodified tracking list. [class: IMPLEMENTATION_REQUIRED]
- [x] Write minimal implementation (the two line contracts above). [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: launch ledger line rides the per-path pass numbering` [class: IMPLEMENTATION_REQUIRED]

### Task 3: The operator directive record (supersede the conversational restart direction)

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `docs/maintenance/operator-directives.md`
- `scripts/test_quota_wall_doctrine.py`

Primary class anchors:
- `Record format` in `docs/maintenance/operator-directives.md`, the D-record shape

- [x] The directives home gains one record in the home's existing D-record shape (issued, status, expiry, scope, directive, superseded_by, witness): restarts remain authorized; the usage-wall class follows this doctrine (one hardened probe, then the timed resume at the recorded reset); every wave lands a launch ledger line. [class: IMPLEMENTATION_REQUIRED]
- [x] The record supersedes the conversational restart direction recorded in chat and memory notes for this repository's execution and maintenance lanes, named in the record's witness so the supersession is auditable. [class: IMPLEMENTATION_REQUIRED]
- [x] Witness (supersession scope): given the new record, expects its scope line to name the execution and maintenance lanes (so a dispatch-time lift resolves it) and its witness line to name the superseded conversational direction; given every other record in the file, expects their text unchanged. [class: REPOSITORY_TEST]
- [x] Run → expect RED: the record witness fails before the record exists. [class: IMPLEMENTATION_REQUIRED]
- [x] Write minimal implementation (the record). [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN; the hygiene scan passes over the changed file. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: operator directive supersedes the conversational restart direction with the quota-wall doctrine` [class: IMPLEMENTATION_REQUIRED]

## Validation

- The Validation Commands section's three commands run green over every changed path.
- The doctrine review replays the witnessed episode: the first usage-wall death hardens the resume point and lands wave lines one and two; the second death arms (or parks) the timed resume instead of a third probe; the manifest alone answers the operator's visibility question without asking.
- The landed dispatch-failure contract's typed line, reason codes, and budget numbers are byte-identical before and after execution (diff-checked in the execution record).

## Review requirements

- Round structure: r1 fresh adversarial panel, fold; r2 verification; cap 5 rounds total.
- Review targets: the two-class boundary (what happens when the error text names no reset time), the hardened probe's `pre_restart:` pair against any duplicate resume record, the ledger's wave-ordinal definition for multi-role waves, the mid-run death recognition surface, and the directive record's supersession scope (this repository's lanes only).
