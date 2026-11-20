# Plan: byte-budget posture alignment

Backlog origin: docs/history/backlog/2026-11-10-byte-budget-advisory-lens-divergence.md
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-11-11-plan-review-byte-budget-posture-alignment-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 1.0h total, largest task 0.5h
Executed: yes (2c4f9fd0b17bafcf99c83d804d7d1fff04545a38)
Authoring claim: 2026-11-10-byte-budget-advisory-lens-divergence.md (session sess_8703b9bf-d85c-44b6-ac59-ac1286847fee)

## Terms

- byte-budget gate: `scripts/skill_text_budget.py`, the fleet-wide skill-text budget check: blocking on the single-read ceiling class, advisory on per-file ratchet caps, informational on the rolling logs.
- ceiling class: a skill file whose byte size exceeds the single-read ceiling (100000 bytes); the gate's blocking class (`--check` exits 1 while any such file exists).
- ratchet cap: a file's own per-file cap in `scripts/skill_text_budget_caps.json`; an over-cap row prints an advisory line and never moves the exit.
- advisory row: a gate output line whose class label is `(advisory)` or `(informational)`; stable prefixes `BREACH (advisory):`, `CAPS GAP (advisory):`, `STALE CAP (advisory):`, `PILOT OVER (advisory):`, `PILOT PENDING (advisory):`, `LOG OVER (informational):`, `LOG (informational):`.
- posture: the decided enforcement split (ceiling blocking, sub-ceiling advisory) recorded in the gate docstring and the machinery-registry row `script:skill_text_budget.py`.
- machinery-registry row: the machinery inventory entry for a gate; the gate's registry row carries its promotion witness and review date.
- plan-review lens: the review-panel judgment layer over a plan (here the correctness-completeness and contract-docs workers); the lens the Growth balance class arms with the posture rule.
- pay-for-growth bullet: the `Pay for growth` line in AGENTS.md's Skill text anti-growth rules section; the guidelines' pay-for-growth home.
- rule-41 sweep: the touched-literal sweep over external pin suites (validation-authoring-rules rule 41) run before rewording gated prose.
- growth balance: the plan-review finding class for operative text grown without a deletion, priced ordinary; its one home is the Growth balance sentence in `agents/skills/review-plan/SKILL.md`.
- pins suite: `scripts/check_maintenance_pins.sh`, the maintenance span-pin suite; rule-41 touched-literal sweeps run against it.

## Why

The byte-budget gate was promoted to blocking on the ceiling class, with advisory ratchet rows, by the operative-file-read-budget-gate landing (3f8dc5d1f, 2026-11-10). The review and guidelines surfaces still carry the pre-landing posture: the plan-review lens has no rule consuming the gate's decided classes, and the guidelines' pay-for-growth bullet still reads "once the repo-wide byte-budget gate lands" with an "until that landing" tail. The corpus therefore holds two sources of truth for one duty, and review capacity re-litigates a decided posture on every breach instance.

## Gist & Examples

TLDR: the review lens and the guidelines consume the landed byte-budget gate posture instead of re-litigating it, because review capacity should stop re-paying a decided decision (efficiency).

Before: an exec-run review lens declared the maintenance decisions file over-cap breach blocking while the gate records the same breach advisory; a reviewer triaging gate output must decide the posture again each time; the guidelines bullet still says the discipline applies at review time only until a landing that has already happened.
After: the Growth balance finding class names the gate as the enforcing instrument; advisory rows are consumed as advisory and never blocking, the ceiling class stays the gate's own blocking exit; the guidelines bullet states the landed posture in present tense.
Edge cases: a lens seeing a ceiling-class row routes to the gate's own exit (the file is over the 100000-byte ceiling and `--check` exits 1); a lens seeing advisory rows records them as growth-watch signals, at most ordinary findings; caps gaps stay the ratchet's seeding surface, not a review blocker.

## Outcome

Review and guidelines surfaces state one decided byte-budget posture keyed to the landed gate.

- A plan-review lens weighing growth findings knows advisory rows are never blocking, ending the witnessed advisory-to-blocking escalation.
- The guidelines' pay-for-growth duty names its instrument instead of a conditional once-lands/until-that-landing shape.
- The lesson corpus's taxonomy note matches the landed design, verified from disk with the disposition recorded.

Gate delta: none

## Assumptions

- assume the Growth balance sentence in `agents/skills/review-plan/SKILL.md` is the correct lens home for the posture rule; basis: the sentence's own text declares it the class's one home, and the origin entry's orientation names review-plan's lens rules.
- assume the gate script needs no change; basis: probed 2026-11-11 (worktree at base f9997eb88): `--check --suite` prints stable-prefixed advisory rows and exits 0; the origin entry's alignment arm rejects new machinery.
- assume no pins needle pins the touched literals; basis: grep over `scripts/check_maintenance_pins.sh` for "Growth balance", "Pay for growth", "until that landing", "grew without a deletion" returned 0 hits (2026-11-11); Tasks 1 and 2 re-run the rule-41 sweep and the pins suite re-runs in validation.
- assume lesson #421's taxonomy wording already matches the landed design; basis: read 2026-11-11, its Why records the two-class taxonomy (blocking ceiling class, advisory sub-ceiling growth watch); Task 3 verifies and records the disposition either way.

Decision points requiring a grill: scope-derivation: origin acceptance rewritten to the landed SOT, promotion arm already landed (3f8dc5d1f; origin row witness addendum 2026-11-11; Why and Assumptions); no-gate-change: advisory rows already machine-diffable, no new machinery (probe 2026-11-11; Assumptions and Review Scope); lens-home: the Growth balance sentence is the class's one home (Task 1); guidelines-home: the Pay for growth bullet is the guidelines' pay-for-growth home (Task 2); lesson-421: verify then align, expected no-edit (Task 3).

## Standing constraints

- No em dashes in any byte this plan adds; the repository's added-lines em-dash gate applies at landing, and prescribed insertions are drafted em-dash-free.
- Text edits stay inside the anti-growth rules: the Task 1 amendment extends the Growth balance sentence's own paragraph (the named home), the AGENTS.md bullet stays one bullet line, and any lessons edit stays inside lesson #421's Why note.

## Evaluation Criteria

**Quality dimensions:**
- consistency: all three surfaces state the same posture (the gate is the enforcing instrument; the ceiling class stays the gate's own blocking exit; advisory rows are growth-watch signals never blocking); a reader of any one surface can name the posture without reading the others.
- byte discipline: `agents/skills/review-plan/SKILL.md` stays under its 79202-byte cap after the amendment; the AGENTS.md bullet stays a single bullet line; any lessons edit stays inside the #421 Why note.

**Done when:**
- the prescribed texts are in place (Tasks 1 through 3) and the Validation Commands block passes end to end on the working tree.
- `python3 scripts/skill_text_budget.py --check --suite` still exits 0 with no new advisory row naming an amended file.

**Ship when:**
- none; this plan is repository-internal with no external release conditions.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/review-plan/SKILL.md` (Task 1)
- `AGENTS.md` (Task 2)
- `docs/maintenance/development_lessons.md` (Task 3)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/skill_text_budget.py`; reason: the gate's output contract is unchanged by design (alignment arm: no new machinery; advisory rows already carry stable machine-diffable prefixes).
- `scripts/skill_text_budget_caps.json`; reason: caps governance stays the ratchet's own wholesale run; seeding gaps are its surface, not a review blocker.
- `agents/skills/review-loop/` and `agents/skills/maintenance/zcode.md`; reason: fold-time gate ordering and the dispatch ladder are owned by the frozen peer entry review-fold-output-prevalidation (authoring session sess_2b51c910) and by execute-plan respectively; this plan must not absorb them.
- machine-readable known-red baseline consumption; reason: owned by the separate backlog entry known-red-gates-consumed-baseline; this plan coordinates by naming the boundary and does not absorb it.

## Validation Commands

Validation preamble (authoring-time record, 2026-11-11, worktree base f9997eb88): every pinned command below ran against the pre-change tree; the RED-today set is command 1 (both greps fail: the posture clause is absent), command 2 first gate (the landed-form grep fails) and command 2 second gate (the stale-tail forbidden-match fires: "until that landing" is present today); the GREEN-today set is command 3 (the #421 taxonomy note is present), command 4 (gate suite exits 0), command 5 (both focused suites pass), and command 6 (pins suite passes). Occurrence-count evidence: the posture-clause phrase occurs 0 times in `agents/skills/review-plan/SKILL.md` today, so the exactly-once count gate is meaningful; rule-22 audit ran (each pinned span occurs exactly once in its task's prescribed snippet; `bash -n` over the block passes); the pre-round structural gate outcome is recorded beside the certification evidence at round launch. Fold note (post-r1, review findings F1-F4 all accepted): the Terms advisory-row list gained the PILOT PENDING and LOG informational rows and three new term entries; validation command 4 became a content gate (ceiling-clean summary line plus absence of any budget row naming the amended skill file, replacing the discarded-output form that could only fail on a tool error); a sibling-bullet survival pin joined command 2; the Task 1 snippet's parenthetical now enumerates the full advisory and informational line set. Fold note 2 (post-r2, r2 findings F1-F3 all accepted, the comprehensive reconciliation fold): the sibling-bullet pin gained the `--` operand separator its dash-leading fixed pattern requires; the ceiling-clean pin is anchored to the summary line's `skill-text budget: 0` prefix so count substrings (10, 20) cannot alias it; the Task 1 snippet's parenthetical is the drift-free class-keyed phrase (every gate line whose class label is advisory or informational) instead of a prefix enumeration synchronized with the gate script's print inventory; the Terms advisory-row entry keeps the full prefix list as the plan-side dictionary. The delta classifier owns the classification of both folds; its output and any correction row are recorded beside the certification evidence.

```bash
REPO="$(git rev-parse --show-toplevel)"
cd "$REPO" || exit 1

# 1. Lens home: the Growth balance amendment carries the posture clause (distinctive spans; exactly once).
grep -qF "never escalates an advisory-class row to blocking" agents/skills/review-plan/SKILL.md || { echo "FAIL: lens posture clause missing"; exit 1; }
test "$(grep -cF "never escalates an advisory-class row to blocking" agents/skills/review-plan/SKILL.md)" -eq 1 || { echo "FAIL: lens posture clause count != 1"; exit 1; }
grep -qF "is the enforcing instrument for that duty" agents/skills/review-plan/SKILL.md || { echo "FAIL: lens instrument wording missing"; exit 1; }

# 2. Guidelines bullet: landed-gate form present; stale conditional tail absent (wrap-tolerant flatten for the tail sweep).
grep -qF "Pay for growth: the repo-wide byte-budget gate" AGENTS.md || { echo "FAIL: guidelines bullet not in landed form"; exit 1; }
grep -qF -- "- Price unbalanced growth: treat operative text" AGENTS.md || { echo "FAIL: sibling bullet lost"; exit 1; }
if tr '\n' ' ' < AGENTS.md | tr -s ' ' | grep -qF "until that landing"; then echo "FAIL: stale conditional tail still present"; exit 1; fi

# 3. Lesson #421 taxonomy note still records the two-class taxonomy (positive pin over the landed design).
grep -qF "blocking ceiling class, advisory sub-ceiling growth watch" docs/maintenance/development_lessons.md || { echo "FAIL: #421 taxonomy note lost"; exit 1; }

# 4. Byte-budget gate: suite surface green; ceiling class clean; amended files absent from budget rows.
GATE_OUT="$(python3 scripts/skill_text_budget.py --check --suite 2>&1)" || { echo "FAIL: gate suite surface tool error"; exit 1; }
printf '%s\n' "$GATE_OUT" | grep -qF "skill-text budget: 0 ceiling breach(es) (blocking)" || { echo "FAIL: ceiling class not clean"; exit 1; }
if printf '%s\n' "$GATE_OUT" | grep -qF "agents/skills/review-plan/SKILL.md"; then echo "FAIL: amended file appears in a budget row"; exit 1; fi

# 5. Focused suites over the touched surfaces.
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_skill_text_budget.py -q || { echo "FAIL: gate unit suite"; exit 1; }
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_plan_review_boundary_examples.py -q || { echo "FAIL: review boundary examples"; exit 1; }

# 6. Pins suite green (no-regression proof; Tasks 1-2 carry the rule-41 touched-literal sweep).
bash scripts/check_maintenance_pins.sh > /dev/null 2>&1 || { echo "FAIL: pins suite"; exit 1; }
```

### Task 1: Review lens consumes the landed gate posture

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/review-plan/SKILL.md`

Prescribed insertion (append one sentence directly after the Growth balance sentence, whose span ends at the sentence terminator `creates no new panel duty.`; the exact tail text `When a plan's arm shaping contradicts` survives verbatim; the original sentence bytes stay intact):

```
The landed byte-budget gate (scripts/skill_text_budget.py, promoted to blocking on the ceiling class 2026-11-10) is the enforcing instrument for that duty: its advisory rows (every gate line whose class label is advisory or informational) are growth-watch signals a lens consumes as advisory, a lens never escalates an advisory-class row to blocking, and the ceiling class stays the gate's own blocking exit, so review never re-litigates the posture the gate's machinery-registry row records.
```

- [x] Append the prescribed sentence after the Growth balance sentence in `agents/skills/review-plan/SKILL.md`; the replaced-span boundary rule holds (span ends at `creates no new panel duty.`, tail `When a plan's arm shaping contradicts` verbatim). [class: IMPLEMENTATION_REQUIRED]
- [x] Rule-41 sweep: grep `scripts/check_maintenance_pins.sh` for the touched literals (`Growth balance`, `enforcing instrument`, `advisory-class`); reconcile any hit beside its provenance comment in the same edit; expected 0 hits (authoring evidence 2026-11-11). [class: REPOSITORY_TEST]
- [x] Run the lens-side focused suite: `scripts/test_plan_review_boundary_examples.py`; expect GREEN. [class: REPOSITORY_TEST]

### Task 2: Guidelines bullet states the landed posture

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `AGENTS.md`

Prescribed replacement (the whole Pay for growth bullet; the following bullet starting `- Price unbalanced growth:` survives verbatim):

```
- Pay for growth: the repo-wide byte-budget gate (scripts/skill_text_budget.py, promoted to blocking 2026-11-10) is the enforcing instrument for that duty: a change that grows a skill file past its cap deletes equivalent bytes in the same change, the gate's own breach report being the record, and no separate growth-debt note surface is added; the gate's advisory ratchet rows are growth-watch signals, never a review-time blocking input.
```

- [x] Replace the Pay for growth bullet in `AGENTS.md` with the prescribed form; the stale tail `until that landing, the same discipline applies at review time only` leaves the file; the next bullet `- Price unbalanced growth:` survives verbatim. [class: IMPLEMENTATION_REQUIRED]
- [x] Rule-41 sweep: grep `scripts/check_maintenance_pins.sh` for the touched literals (`Pay for growth`, `growth-debt`, `until that landing`); reconcile any hit beside its provenance comment in the same edit; expected 0 hits (authoring evidence 2026-11-11). [class: REPOSITORY_TEST]

### Task 3: Lesson taxonomy verification and final validation

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `docs/maintenance/development_lessons.md`

- [x] Verify lesson #421's taxonomy note against the landed posture recorded in the `scripts/skill_text_budget.py` docstring; on a contradiction, apply the minimal rewrite inside the #421 Why note only; on a match, record the quoted-evidence no-edit disposition in the task log; expected outcome (authoring evidence 2026-11-11): match, no edit. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the full Validation Commands block; every gate green on the working tree. [class: REPOSITORY_TEST]
