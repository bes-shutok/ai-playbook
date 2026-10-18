# Plan: delivery-channel intent doctrine for user-directed scheduling asks

Backlog origin: docs/history/backlog/2026-10-04-concurrent-scheduling-ask-dedup.md
Driving force: reliability (not one of the five driving principles; justification: the witnessed silent defer defeated one of two intended parallel lanes and the collision window makes recurrence timing-dependent; park-triage would take it on wording alone, and the doctrine lands now because the defer is witnessed and the surviving automation re-exposes the gap on every parallel ask)
Plan review record: the staging series docs/reviews/2026-10-06-plan-review-concurrent-scheduling-ask-dedup-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Terms

- delivery-channel intent: an operator scheduling ask delivered to a session is that session's scheduling intent; each delivered channel arms its own lane, the affirmative arm duty landing through the intent attribution and the decline-only-by-asking inversion.
- sanctioned parallelism: arming a lane whose prompt is similar rather than byte-identical to an existing automation's; target-level deconfliction belongs to the lane's claim and occupancy machinery, never to create-time dedup.
- ask-before-deferring: a session may decline to arm only by asking the operator when it genuinely believes coverage already exists; the witnessed 2026-10-04 08:06 silent defer-to-existing is the anti-shape.
- lane occupancy fence: the per-lane machinery a user-directed lane payload carries (authoring claim, merge lock, peer-material hands-off) so parallel lanes converge on distinct targets.
- endgame form: running parallel lanes inside one session, which supersedes the cross-session automation form once learned; the interim form stays recognizable as interim.

## Why

The ask "resume repeated authoring at 11 am" reached two standing sessions; the first created the lane, the sibling surveyed three minutes later and silently deferred to the existing automation, defeating the operator's intent to run two parallel lanes. The dedup was accidental (timing, not mechanism): the user-directed scheduling path owns no creation-time doctrine, the duplicate-parent tripwire is carrier-shaped and scheduler-turn-scoped, and the deferring session's only durable record was a memory note outside the repository.

## Outcome

An operator scheduling ask delivered to a session arms that session's lane under the delivery-channel intent doctrine, decline-to-arm requires asking the operator, and every user-directed lane payload carries the occupancy fence, with the endgame direction recorded beside the doctrine.

- `agents/skills/maintenance/zcode.md`'s Interactive dispatch template section states the doctrine: the delivery-channel intent rule with sanctioned parallelism, the ask-before-deferring inversion naming the witnessed silent defer as the anti-shape, the lane occupancy fence requirement for every user-directed lane payload, and the endgame direction recorded as interim-form recognition.
- `agents/skills/maintenance/SKILL.md`'s user-directed payload duties bullet carries the runtime-agnostic sentence pairing the delivery-channel intent rule with the ask-before-deferring inversion, the overlay owning the concrete wording per its own split convention.
- Gate delta: grows the overlay's and the skill's checked-condition sets (the doctrine and its inversion); no refusal class, hard gate, fence, protocol layer, or schema state field is added, and nothing is removed. Priced by the witnessed 2026-10-04 08:06 silent defer recorded in the origin row, re-derived from the row's witnessed-collision narrative in the investigate pass.

## Assumptions

- assume the doctrine lands in the overlay's Interactive dispatch template section, not the maintenance skill's Step 2: basis: the overlay owns the runtime-specific duties per its own split convention and the section is the user-directed scheduling path's procedure of record, while the skill mirror carries only the runtime-agnostic sentence per that same convention.
- assume the duplicate-parent tripwire stays byte-untouched: basis: the origin's rejected alternative (widening its recognition rule to lane payloads would let a scheduler-turn guard's self-heal delete operator-created parallel lanes), and its carrier-shaped recognition is deliberate design predating this collision.
- assume the occupancy-fence arm prescribes the fence for future payloads only: basis: the witnessed 2026-10-04 11:00 fire standing beside the peer's live authoring claim is the working witness already operating, so no armed automation is edited.
- assume the endgame direction stays a recognition note, not a migration duty: basis: the PLAN-PROMPTS entry's arm (4) ("running parallel lanes inside one session supersedes the cross-session automation form once learned") with the Standing pre-authorization naming in-session parallelism as the superseding endgame, and the origin row's "supersedes this row's cross-session mechanics once learned", mark the interim form recognizable, and no in-session mechanism exists yet to migrate to.
- assume the overlap case (an operator scheduling ask delivered to a session while it executes its Step 2 guard chain) resolves by the delivery-channel reading: basis: an ask delivered interactively initiates the interactive path regardless of the receiving session's other duties, the duplicate-user-directed-dispatch tripwire stays deliberately frozen, and the interactive dispatch template path is separate from Step 2.
- assume the mirror sentence's scope is the intent attribution plus the ask-before-deferring inversion while the sanctioned-parallelism clause and its deconfliction statement live in the overlay paragraph: basis: Prompt arm (5) mirrors arm (1)'s runtime-agnostic sentence and the skill surface's per-turn scheduler duties already carry the deconfliction side, so the mirror records both clauses it does carry and the overlay owns the concrete wording.
- assume the disposition record for a decline-after-ask stays with the asking session's own turn record: basis: the gate delta adds no protocol layer, scheduler-state is rejected for scope, and memory notes are rejected as non-binding, so the plan narrows to the witnessed defect (the silent defer) and leaves the record home to the standing session-notes discipline.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: A scheduling ask delivered to a session is that session's intent to arm; declining needs a question, and every parallel lane carries its own occupancy fence (reliability).

**Before (today):** Two sessions receive the same ask; the second surveys, finds the peer's automation armed, and silently defers with a payload patch, defeating the intended parallel lane; nothing in the repository requires the survey, defines payload equivalence, or owns the disposition record.

**After (this plan):** The overlay's Interactive dispatch template states the doctrine (each delivered channel is that session's intent; similar prompts are sanctioned parallelism), a session declines only by asking the operator, every user-directed lane payload carries the occupancy fence, and the endgame direction sits beside the doctrine so the interim form is recognizable.

Edge cases: byte-identical duplicate asks remain possible and resolve by explicit operator instruction (the duplicate-parent tripwire stays untouched by this plan and cannot recognize user-directed shapes, so the operator-instruction disposition is unmechanized by design); scheduler-dispatched children keep their existing duties unchanged; a session that arms nothing because the operator answered the ask records the answer and proceeds per it (the record home is consciously left to the standing session-notes discipline, recorded in the assumptions).

## Evaluation Criteria

**Quality dimensions:**
- correctness: the doctrine, inversion, fence requirement, and endgame note appear in the overlay section and the mirrored sentence in the skill bullet.
- regression safety: the pins suite stays green (the carrier title and template literals are pinned and untouched); the em-dash added-lines scan and the hygiene scan report no findings.
- scope discipline: the duplicate-parent tripwire and scheduler-state schema are untouched; no armed automation is edited.

**Done when:**
- The full Validation Commands block exits 0 on the executed tree.

**Ship when:**
- The next user-directed scheduling ask delivered to a session arms without a silent defer, and the next parallel ask arms its second lane under the doctrine; both are routine-turn behaviors requiring no further human action in this repository beyond the executed tree.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/zcode.md` (the doctrine paragraph in the Interactive dispatch template section; all other sections are frozen)
- `agents/skills/maintenance/SKILL.md` (the one mirrored sentence appended to the user-directed payload duties bullet; all other sections are frozen)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- the duplicate-parent tripwire bullet and its recognition rule; reason: the origin's rejected alternative keeps the carrier-shaped design and the plan freezes the bullet.
- `scheduler-state.json` schema and the scheduler-state registration of user-directed automations; reason: the origin's rejected alternative (a schema migration the doctrine makes unnecessary).
- `agents/skills/maintenance/prompt-templates.md`; reason: the standing pre-authorization and authoring-constraint sentences are carried verbatim there and referenced, not restated.
- armed automations (including the witnessed 2026-10-04 11:00 lane); reason: the fence arm prescribes future payloads; the working witness stays live.

## Validation Commands

Authoring-time evidence (rule 29 pre-round): the plan bytes passed the pre-round gate with exit 0 and `OUTCOME: pass` in the authoring worktree; the rule 19 RED-today probe ran each pinned span with grep against its owning target (the new-duty spans returned no match; the preserved spans matched); the rule 22 mechanical audit verified every pinned span occurs exactly once in its owning prescribed snippet (rule 36 mirrors included; the preserved spans matched against the current target bytes) and `bash -n` accepted the Validation Commands block. Round-start state for r3: authoring worktree ai-playbook-wt-csad, branch 2026-10-06-concurrent-scheduling-ask-dedup, plan bytes at the r2 fold commit.

```bash
REPO="$(git rev-parse --show-toplevel)"
( cd "$REPO" && bash scripts/check_maintenance_pins.sh )
( cd "$REPO" && bash scripts/check-no-em-dash.sh added-lines --base main )
( cd "$REPO" && bash ~/.ai-playbook/scripts/scan-public-hygiene.sh )
```

### Task 1: Delivery-channel intent doctrine and the mirrored sentence (GREEN)

Files:
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/SKILL.md`

Evidence:
- `( cd "$REPO" && bash scripts/check_maintenance_pins.sh )`; covers the pins-reconciliation criterion: the carrier title and template literals stay pinned and untouched

- [x] In `agents/skills/maintenance/zcode.md`, insert the following paragraph into the Interactive dispatch template section immediately after the paragraph beginning the unique span `This block is for interactive asks from a fresh session`, separated by blank lines on both sides, reading exactly: [class: IMPLEMENTATION_REQUIRED]

```markdown
**Delivery-channel intent (added 2026-10-06, the concurrent-scheduling-ask-dedup plan):** an operator scheduling ask delivered to a session is that session's scheduling intent; arming a lane whose prompt is similar rather than byte-identical to an existing automation's is sanctioned parallelism, and target-level deconfliction belongs to the lane's claim and occupancy machinery, never to create-time dedup. A session may decline to arm only by asking the operator when it genuinely believes coverage already exists; the witnessed 2026-10-04 08:06 silent defer-to-existing is the anti-shape. Every user-directed lane payload carries the lane's occupancy fence (authoring claim, merge lock, peer-material hands-off) so parallel lanes converge on distinct targets; the 2026-10-04 11:00 fire standing beside the peer's live authoring claim is the working witness. The endgame direction: in-session parallelism supersedes this cross-session automation form once learned; the interim form stays recognizable as interim. This rule governs interactive user-directed asks; scheduler-turn guards keep their existing defer duties unchanged.
```

- [x] In `agents/skills/maintenance/SKILL.md`, append one sentence to the end of the User-directed maintenance payload duties bullet (the bullet ending in the unique span `no new writer class is created`), reading exactly: ` Delivery-channel intent (2026-10-06, the concurrent-scheduling-ask-dedup plan): an operator scheduling ask delivered to a session is that session's scheduling intent; a session declines to arm only by asking the operator when it genuinely believes coverage already exists, never by silent defer.` [class: IMPLEMENTATION_REQUIRED]

- [x] Run → expect GREEN: the pins suite exits 0 (the carrier title and template literals untouched); the inserted paragraph and appended sentence read as ordinary prose [class: REPOSITORY_TEST]
- [x] Commit: `concurrent-scheduling-ask-dedup: delivery-channel intent doctrine for user-directed scheduling asks` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Full validation

Evidence:
- The full `## Validation Commands` block; covers every Done-when criterion on the executed tree

- [x] Run → expect GREEN: the full Validation Commands block exits 0 line by line; the em-dash added-lines scan and the hygiene scan report no findings on the changed files [class: REPOSITORY_TEST]
- [x] Verify span uniqueness: for each new-duty span introduced by this plan, `grep -cF` over its owning file returns exactly 1 after the edits (`Delivery-channel intent` in `agents/skills/maintenance/zcode.md`; `decline to arm only by asking the operator` in `agents/skills/maintenance/zcode.md`; `in-session parallelism supersedes` in `agents/skills/maintenance/zcode.md`; `Delivery-channel intent` in `agents/skills/maintenance/SKILL.md`), and for the preserved spans it returns at least 1 (`This block is for interactive asks from a fresh session` in `agents/skills/maintenance/zcode.md`; `no new writer class is created` in `agents/skills/maintenance/SKILL.md`) [class: REPOSITORY_TEST]
- [x] Run the readiness gate over this plan; expect exit 0 with `OUTCOME: pass` at the certification boundary [class: REPOSITORY_TEST]

## Disposition

Executed 2026-10-06 in worktree ai-playbook-wt-csa (branch plan-concurrent-scheduling-ask-dedup-exec) by the standing maintenance execution lane. Task 1: the Delivery-channel intent doctrine paragraph lands verbatim in the Interactive dispatch template section of agents/skills/maintenance/zcode.md (blank-line separated after the anchor paragraph), and the mirrored sentence lands verbatim at the end of the User-directed maintenance payload duties bullet in agents/skills/maintenance/SKILL.md; byte-identity against the plan's fenced block and adjacency verified mechanically.

Validation: pins suite exit 0 (carrier title and template literals untouched); em-dash added-lines scan exit 0; hygiene scan exit 0; span uniqueness holds for all four new-duty and two preserved spans; the diff is limited to the two files at one insertion each. Exec review r4 was verified directly in-session (the subagent dispatch layer returned a quota limit mid-round; the verification, its scope, and the bare-capture-fallback attribution are recorded in the record): zero findings; records at docs/reviews/2026-10-06-plan-review-concurrent-scheduling-ask-dedup-r4.{md,stats.json} plus the r5 certification probe.

Deferred residuals: none. Origin row docs/history/backlog/2026-10-04-concurrent-scheduling-ask-dedup.md is covered by this execution and folded in the landing.
