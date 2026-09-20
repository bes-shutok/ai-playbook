# Plan: Context budget and telemetry for long-running skills

Backlog origin: docs/history/backlog/2026-09-18-context-budget-and-telemetry-long-running-skills.md (stays in place while this plan is open).
Plan review: docs/reviews/2026-09-20-plan-review-context-budget-and-telemetry-long-running-skills-r7.md (latest, ready) · r6 at docs/reviews/2026-09-20-plan-review-context-budget-and-telemetry-long-running-skills-r6.md · r1-r5 at docs/reviews/2026-09-19-plan-review-context-budget-and-telemetry-long-running-skills-r1..r5.md

## Terms

- **Checkpoint**: a named safe boundary at which a skill measures its context size, logs one telemetry record, and applies the ladder. Never mid-task: a compaction between a worker claim and its completion risks orphaning driver state.
- **Threshold ladder**: the budget-fraction policy applied at each checkpoint: below 70% of budget, log and continue; 70-85%, cheap shedding first; above 85%, full compaction. Checkpoints act well before the wall on normal runs; a single step large enough to jump from below 85% past 100% between checkpoints remains the residual case.
- **Cheap shedding**: dropping superseded material from the working context (applied diff snapshots, resolved quota chatter, superseded round payloads) without compacting the run.
- **Context telemetry**: one JSONL record per checkpoint, `{ts, skill, run_slug, phase, est_tokens_before, action, est_tokens_after, compactions_to_date}`, appended to a gitignored per-run log. The `skill` vocabulary is closed: `execute-plan` for execution runs, `review-loop` for loop rounds, `plans-authoring` for authoring children, so the archived corpus analyzes cleanly per skill.
- **Measurement primitive**: the runtime-specific way a checkpoint measures context: session/transcript stats where the runtime exposes them; otherwise a char-count proxy over the transcript file with a pinned ~4 chars/token ratio, clearly labeled an estimate.

## Assumptions

- assume the budget constant is `context_budget_tokens = 300000` in `.ai-playbook/facts.md`'s opening TOML block, the single knob; changing it needs no skill edits; basis: backlog item's suggested key and value. The file is gitignored by design (per-machine runtime knob), so this plan edits it without committing it.
- assume the post-hoc analysis of context.jsonl (token cost per plan family, compaction count vs missed-detail incidents) is OUT of scope; basis: backlog item's scope note.
- assume the scheduler turn itself needs no new checkpoints (the turn is a fresh short session each cadence, and the child blueprints' final compaction step keeps payload transcripts short); basis: backlog item, corrected by review r2 to the audit-surviving rationale.
- assume the compaction survival list is enumerated normatively in execute-plan's new section (machine manifest `runtime_state.json`, current round state, claim tokens, peer-safety fences); the `handoff` skill's template does not pin such a list, so this plan owns the enumeration; basis: backlog item's survival intent, corrected by review r1.
Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the long-running skills (`execute-plan`, `review-loop`, maintenance children) measure context at named safe checkpoints and act on a budget ladder, so the `external`-forced cost and fidelity failures (observed r18 loops, early-detail loss) stop relying on silent auto-summarization.

What changes: one facts-backed budget constant (untracked, per-machine); a checkpoint-and-ladder policy written into the core skills (tool-agnostic) with the measurement fallback carried inline where the overlay is not loaded; the runtime-specific measurement primitive named in the maintenance overlay; and one gitignored JSONL telemetry record per checkpoint, archived at run completion so it outlives the session-tmp cleanup, designed so a completed run answers peak size, compactions performed, and per-phase tokens without reading the transcript.

Example: an execute-plan run finishes review round r7; the parent measures (proxy: 4 chars/token over the transcript), appends `{ts, skill: execute-plan, run_slug: ..., phase: review-r7, est_tokens_before: 248000, action: shed, est_tokens_after: 231000, compactions_to_date: 0}` to `docs/tmp/execute-plan/<PLAN_SLUG>/context.jsonl` (82.7% of budget: the 70-85% rung, cheap shedding drops a superseded round payload). At r9 the measure reads 262k (87% of 300k): the parent performs full compaction at the round boundary by writing the handoff document per `agents/skills/handoff/SKILL.md`'s template (the skill itself is user-invocation-only, so the parent follows the template manually), reloading from `runtime_state.json` and the survival list, and logs `action: compact`. At Phase 4 archive the parent copies the run's context.jsonl to `docs/tmp/context-telemetry/<PLAN_SLUG>.jsonl` so Phase 5's session-tmp cleanup cannot delete the run's telemetry.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every long-running skill measures context at its named checkpoints and appends one telemetry record per checkpoint (grep-able, gitignored, per-run).
- correctness: a run crossing 85% of budget performs a documented compaction at a safe boundary via an executable path (manual template procedure when no runtime primitive or user-only skill stands in) and resumes from durable state; no run relies on runtime auto-summarization as its only mechanism.
- survivability: a completed run's telemetry outlives Phase 5's session-tmp cleanup via the `docs/tmp/context-telemetry/` archive copy.
- configurability: the budget is a single facts-backed constant.
- analyzability: a completed run's archived context.jsonl answers peak size, compactions, and per-phase tokens through the Phase 4 boundary (the archive refresh ordering preserves records up to the final pre-archive checkpoint) without the transcript.

**Done when:**
- All Task greps pass (fail-closed, per Validation Commands).
- Each task commit touches exactly its declared Files list plus this plan's checkbox marks (witnessed by the commit-scope gates); no plan bytes under `docs/plans/` other than this plan are touched by this execution's commits; concurrent peer commits on the shared branch are outside this plan's Done-when by construction.

**Ship when:**
- [class: OPERATIONS_FOLLOW_UP] The telemetry format proves stable across several runs; the post-hoc analysis (cost per plan family, compactions vs missed-detail incidents) is a follow-up; evidence owner: Andrey; closure: a follow-up plan exists or the decision is recorded.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `.ai-playbook/facts.md` (TOML block: the budget constant; untracked, no commit)
- `agents/skills/execute-plan/SKILL.md` (checkpoint-and-ladder policy section, survival list, measurement fallback, telemetry archive)
- `agents/skills/review-loop/SKILL.md` (round-boundary checkpoint)
- `agents/skills/maintenance/prompt-templates.md` (both child blueprints' checkpoint duty and documented-deviations entries)
- `agents/skills/maintenance/zcode.md` (context measurement primitive)
- `scripts/check_maintenance_pins.sh` (one pin per blueprint checkpoint sentence)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed.

**Out of scope; reject unless plan-related:**
- `scripts/plan_readiness.py` and any other validator; reason: no contract of theirs changes.
- The post-hoc telemetry analysis tooling; reason: explicitly out of scope per the backlog item.
- `agents/skills/handoff/SKILL.md`; reason: this plan enumerates the survival list in execute-plan and prescribes the manual-template degrade path; the handoff skill itself is not modified.

## Validation Commands

```bash
set -u
cd "$(git rev-parse --show-toplevel)"
FACTS=.ai-playbook/facts.md
EXEC=agents/skills/execute-plan/SKILL.md
LOOP=agents/skills/review-loop/SKILL.md
TMPL=agents/skills/maintenance/prompt-templates.md
ZCODE=agents/skills/maintenance/zcode.md
PINS=scripts/check_maintenance_pins.sh
PLAN=docs/plans/2026-09-19-context-budget-and-telemetry-long-running-skills.md
fail() { echo "GATE FAIL: $1" >&2; exit 1; }

# Task 1 gate: the budget constant (untracked file, no commit).
grep -q "context_budget_tokens = 300000" "$FACTS" || fail "budget constant missing"

# Task 2 gates: checkpoint policy, ladder, telemetry, survival list, measurement fallback, archive.
grep -q "Context budget checkpoints" "$EXEC" || fail "checkpoint section missing"
grep -q "after each worker return" "$EXEC" || fail "checkpoint placements missing"
grep -q "at each phase transition" "$EXEC" || fail "checkpoint placements missing"
grep -q "after each review round" "$EXEC" || fail "checkpoint placements missing"
grep -q "below 70% of budget, log and continue" "$EXEC" || fail "ladder first rung missing"
grep -q "cheap shedding first" "$EXEC" || fail "ladder shedding rung missing"
grep -q "performs full compaction" "$EXEC" || fail "ladder compaction rung missing"
grep -q "a checkpoint is never mid-task" "$EXEC" || fail "safe-boundary rule missing"
grep -q "context.jsonl" "$EXEC" || fail "telemetry path missing"
grep -q "compactions_to_date" "$EXEC" || fail "telemetry record shape missing"
grep -q "current round state, claim tokens, peer-safety fences" "$EXEC" || fail "survival list missing"
grep -q "~4 chars/token" "$EXEC" || fail "inline measurement fallback missing"
grep -q "context_budget_tokens" "$EXEC" || fail "budget read path missing from policy"
grep -q "the archived telemetry file" "$EXEC" || fail "Phase 5 checklist anchor missing"
grep -q "docs/tmp/context-telemetry/" "$EXEC" || fail "telemetry archive missing"

# Task 3 gate: review-loop round-boundary checkpoint.
grep -q "at each round boundary" "$LOOP" || fail "review-loop checkpoint missing"

# Task 4 gates: blueprint checkpoint duty, deviation entries, placeholder-free path, pins extension.
grep -q "after each blueprint step block" "$TMPL" || fail "blueprint checkpoint duty missing"
grep -q "context-budget checkpoint duty" "$TMPL" || fail "deviation entry missing"
grep -q "docs/tmp/execute-plan/<plan-slug>/context.jsonl" "$TMPL" || fail "execution blueprint telemetry path missing"
grep -q "docs/tmp/authoring/<plan-slug>/context.jsonl" "$TMPL" || fail "authoring blueprint telemetry path missing"
grep -q "skill: plans-authoring" "$TMPL" || fail "authoring skill value missing"
test "$(grep -cF 'context-budget checkpoint duty' "$TMPL")" -eq 2 || fail "deviation entry not once per blueprint"
grep -q "after each blueprint step block" "$PINS" || fail "pins extension missing"

# Task 5 gates: the measurement primitive and its proxy labeling.
grep -q "Context measurement primitive" "$ZCODE" || fail "measurement primitive section missing"
grep -q "~4 chars/token" "$ZCODE" || fail "proxy ratio missing"
grep -q "labeled an estimate" "$ZCODE" || fail "estimate labeling missing"
grep -q "action: no-primitive" "$ZCODE" || fail "no-locator fallback missing"

# Keep-green regression witness: the pins suite (extended by Task 4) stays green.
bash scripts/check_maintenance_pins.sh || fail "pins suite drifted"

# Commit-scope witness for the Done-when criterion (BASE recorded before the first commit;
# Task 1's facts edit is untracked and carries no commit, so it has no gate here; every
# gate's declared list includes this plan, whose checkbox marks ride the done commits).
BASE="$(cat docs/tmp/ctxbudget-base-sha.txt)"
commit_scope_ok() {
  subj="$1"; shift
  c="$(git log -F --grep="$subj" --format=%H "$BASE"..HEAD | tail -1)"
  test -n "$c" || fail "task commit missing: $subj"
  for f in "$@"; do
    git show --name-only --format= "$c" | grep -qxF "$f" || fail "commit $c missing declared file $f"
  done
  EXTRA="$(git show --name-only --format= "$c" | grep -v '^$' | grep -vxF -f <(printf '%s\n' "$@") || true)"
  test -z "$EXTRA" || fail "commit $c touches undeclared files: $EXTRA"
}
commit_scope_ok "execute-plan: context budget checkpoints and ladder" "$EXEC" "$PLAN"
commit_scope_ok "review-loop: round-boundary context checkpoint" "$LOOP" "$PLAN"
commit_scope_ok "maintenance: context checkpoint duty in child blueprints" "$TMPL" "$PINS" "$PLAN"
commit_scope_ok "maintenance: context measurement primitive in the overlay" "$ZCODE" "$PLAN"
```

Gate provenance: every new-string gate is RED today (none of the strings exist in the six target files; first gate measured firing with exit 1 at authoring) and flips GREEN exactly when the tasks land; each gate needle is a contiguous span of its task bullet's prescribed text; the pins-suite invocation is a keep-green witness, GREEN today and required to stay GREEN after Task 4's pin extension; the commit-scope gates run last, require BASE (recorded before Task 2's commit) plus the four landed commits, and measure committed history by subject, never working-tree state, so concurrent peer edits cannot fail them.

### Task 1: Budget constant (untracked, no commit)

Files:
- `.ai-playbook/facts.md`

- [x] Before the first commit, record the current HEAD sha to `docs/tmp/ctxbudget-base-sha.txt` (one line, `git rev-parse HEAD`); the commit-scope gates read it as BASE. Commit discipline for the whole run: each task's done commits ONLY the task's declared files plus this plan ("commit only this session's files; leave foreign staged files and peer changes alone", the execution blueprint's own phrasing), so the commit-scope gates measure only this run's work. [class: IMPLEMENTATION_REQUIRED]
- [x] Add to the opening TOML block of `.ai-playbook/facts.md` (an untracked, gitignored file: this edit carries NO commit, the file stays per-machine by design): `context_budget_tokens = 300000` (one knob, one owner; skills read it with a 300000 fallback when the key is absent). [class: IMPLEMENTATION_REQUIRED]
- [x] Witness: the grep gate in Validation Commands verifies the constant on the untracked file; no commit-scope gate exists for Task 1. [class: REPOSITORY_TEST]

### Task 2: execute-plan checkpoint policy

Files:
- `agents/skills/execute-plan/SKILL.md`

- [x] Add a `Context budget checkpoints` section stating the policy: checkpoints run after each worker return, at each phase transition, and after each review round; a checkpoint is never mid-task (the safe-boundary rule: never mid-task, because a compaction between a worker claim and its completion orphans driver state; the machine manifest mitigates but the boundary rule removes the exposure). [class: IMPLEMENTATION_REQUIRED]
- [x] State the threshold ladder in the same section: at each checkpoint measure context size (measurement: runtime session/transcript stats where available; otherwise a char-count proxy over the transcript with a ~4 chars/token ratio, labeled an estimate, carried inline here because standalone execute-plan runs never load the maintenance overlay); the budget is `context_budget_tokens` read from `.ai-playbook/facts.md`'s opening TOML block, falling back to 300000 when the key is absent; below 70% of budget, log and continue; 70-85%, cheap shedding first (drop superseded round payloads, applied diff snapshots, resolved quota chatter); above 85%, performs full compaction at the safe boundary, via the runtime compaction primitive when the runtime exposes one, otherwise by writing the handoff document following `agents/skills/handoff/SKILL.md`'s template manually (that skill is user-invocation-only), resuming from `runtime_state.json` and the survival list, enumerated here as the normative owner: machine manifest runtime_state.json, current round state, claim tokens, peer-safety fences; a run without a machine manifest resolves the survival list against its own durable state: the run's staging docs and, for scheduled children, the scheduler state file. [class: IMPLEMENTATION_REQUIRED]
- [x] State the telemetry duty and its survival in the same section: append one JSONL record per checkpoint `{ts, skill, run_slug, phase, est_tokens_before, action, est_tokens_after, compactions_to_date}` to `docs/tmp/execute-plan/<plan-slug>/context.jsonl` (gitignored, per-run); at Phase 4 archive the parent copies the run's context.jsonl to `docs/tmp/context-telemetry/<plan-slug>.jsonl`, so Phase 5's session-tmp cleanup (which removes the whole run directory) cannot delete the completed run's telemetry. Anchor the copy in the executed flow so it cannot decay from attention: the new section orders the copy as a Phase 4 step performed BEFORE the pre-archive stage, and the plan edits execute-plan's Phase 5 success checklist by adding a checklist item: the archived telemetry file `docs/tmp/context-telemetry/<plan-slug>.jsonl` is present. [class: IMPLEMENTATION_REQUIRED]
- [x] Witness: the section names all three checkpoint placements (worker return, phase transition, review round) and the section is quoted by the Validation Commands' dedicated greps; each ladder rung has its own needle. [class: REPOSITORY_TEST]
- [x] Commit: `execute-plan: context budget checkpoints and ladder` [class: IMPLEMENTATION_REQUIRED]

### Task 3: review-loop round-boundary checkpoint

Files:
- `agents/skills/review-loop/SKILL.md`

- [x] Add the round-boundary checkpoint to the one-iteration flow: at each round boundary the orchestrator applies the execute-plan `Context budget checkpoints` policy (measure, log one telemetry record to the run's telemetry file `docs/tmp/review-loop/<branch-slug>/context.jsonl`, act per the ladder); review-loop does not restate the ladder, it references the policy. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `review-loop: round-boundary context checkpoint` [class: IMPLEMENTATION_REQUIRED]

### Task 4: maintenance child blueprint checkpoint duty

Files:
- `agents/skills/maintenance/prompt-templates.md`
- `scripts/check_maintenance_pins.sh`

- [x] In BOTH child blueprints, add a checkpoint duty as instruction sentences inside each fenced body (no new `{placeholder}` tokens and no `{tmp_dir}`-style placeholder notation: the pins suite pins the placeholder set exactly, so the telemetry path is written placeholder-free as the literal `docs/tmp/execute-plan/<plan-slug>/context.jsonl` for execute-plan children (recorded with `skill: execute-plan`) and `docs/tmp/authoring/<plan-slug>/context.jsonl` for authoring children (recorded with `skill: plans-authoring`), creating the run's telemetry directory if needed): after each blueprint step block, the child measures context (per the overlay's measurement primitive; char-count proxy fallback labeled an estimate), logs one telemetry record, and acts per the threshold ladder of the execute-plan `Context budget checkpoints` policy; at a boundary only, never mid-task. The scheduler turn itself gets no checkpoints (the turn is a fresh short session each cadence; the blueprints' final compaction step keeps payload transcripts short). [class: IMPLEMENTATION_REQUIRED]
- [x] Register the blueprint change in the documented-deviations header list with the entry name `context-budget checkpoint duty` and a one-line rationale, for each blueprint. [class: IMPLEMENTATION_REQUIRED]
- [x] Extend `scripts/check_maintenance_pins.sh` with one checkpoint-sentence pin per blueprint (pin a distinctive contiguous span of each new duty sentence, for example the `after each blueprint step block` anchor), so the new normative paragraphs cannot silently regress. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `maintenance: context checkpoint duty in child blueprints` [class: IMPLEMENTATION_REQUIRED]

### Task 5: overlay measurement primitive

Files:
- `agents/skills/maintenance/zcode.md`

- [x] Add a `Context measurement primitive` section: this runtime exposes session/transcript stats where available (the section names the stats surface or, for the char-count proxy, pins the concrete transcript/session-artifact location the proxy counts, host-scoped like the overlay's existing literals); when no locator exists, the checkpoint degrades loudly: it appends the checkpoint record with `action: no-primitive` and continues, so an unexecutable measurement is visible in the telemetry corpus instead of silently skipping checkpoints; the proxy ratio is a pinned ~4 chars/token, labeled an estimate in every telemetry record (the record carries `est_`-prefixed fields for exactly this reason); for compaction the section references the overlay's existing Session compaction bullet by anchor (single living home for the user-side-command fact) and adds: when the runtime cannot invoke a compaction primitive, compaction degrades to the manual template procedure prescribed in execute-plan's `Context budget checkpoints` section. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `maintenance: context measurement primitive in the overlay` [class: IMPLEMENTATION_REQUIRED]

## Residual review findings (at-cap finalize, 2026-09-19)

Review loop r1-r5 (artifacts at docs/reviews/2026-09-19-plan-review-context-budget-and-telemetry-long-running-skills-r1..r5.md; focused re-cert r6 at docs/reviews/2026-09-20-plan-review-context-budget-and-telemetry-long-running-skills-r6.md). Every blocking finding from r1-r4 was folded; r4 reported ready=yes with zero blocking, its three non-blocking findings were folded per the full-closure preference; r5's single blocking finding (the `no-primitive` needle was GREEN before Task 5) was folded to the RED-today span `action: no-primitive` (verified absent from zcode.md today), and r5's Low was folded to a first checkpoint-placement needle (`after each worker return`). The authoring cap was reached before those folds could be re-reviewed, so the execution pre-step ran the focused re-cert r6 (2026-09-20) over the post-fold bytes: ready=yes, zero blocking, the F1 fold certified clean; r6's two staged Lows are folded in this batch — the two remaining checkpoint-placement needles (`at each phase transition`, `after each review round`, both verified RED today), and the Task 3 and Task 4 needles re-pinned to spans the prescribed landing text forces (`at each round boundary` in review-loop, `after each blueprint step block` in the pins script, replacing `round-boundary checkpoint` and `checkpoint-sentence pin`) — together with the header Plan review reference line. The fresh certification round r7 (2026-09-20) ran over these bytes: ready=yes, zero blocking; its two staged Lows were deferred to docs/history/backlog/2026-09-20-context-budget-plan-telemetry-gate-strength.md. No other residuals are open.
