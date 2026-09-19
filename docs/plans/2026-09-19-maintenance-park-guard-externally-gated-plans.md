# Plan: Maintenance park-guard for externally gated plans

Backlog origin: docs/history/backlog/2026-09-18-maintenance-park-guard-externally-gated-plans.md (stays in place while this plan is open).

## Terms

- **Externally gated plan**: an open top-level plan that declares an external prerequisite it cannot satisfy itself, via an `External gate:` line in its header block. The header block is the region from the `# Plan:` title line to the first `## ` section heading; the classification scan covers exactly that region (no whole-file scan). Absence of the line means not gated.
- **Gate declaration format**: the `External gate:` line's value takes exactly one form, detected mechanically: DATE FORM when the value's first whitespace-delimited token matches `YYYY-MM-DD` (four digits, hyphens, four digits, hyphens, two digits); SLUG FORM otherwise, where the slug is the value's first whitespace-delimited token and must be kebab-case (lowercase letters, digits, hyphens). A date-form gate has no slug and evaluates only by calendar passage; a slug-form gate evaluates only by prerequisite existence; no value evaluates under both. This is the single normative definition; D1's self-heal and D4's unsatisfiability evidence both reference it and must not restate it.
- **Gate satisfaction** (mechanical match rule, defined once here): a declared gate is satisfied when (date form) the named date has passed at turn time, or (slug form) some open top-level plan or open backlog item OTHER THAN the declaring plan itself has the slug in its file basename as a hyphen-bounded segment (the basename contains the slug with a hyphen or a string edge on both sides; a match inside a longer word does not count). The match set is exactly the open surfaces: top-level `*.md` files directly under the resolved plans_dir (never the `completed/` or `deferred/` subdirectories) and open backlog items directly under the resolved backlog_dir top level (never its parked/completed subdirectories). Basename matching only; no body-text matching, so the declaring plan's own body can never self-satisfy its gate. The turn model judges no semantics beyond this rule. An unsatisfied gate is the complement. Both D1's skip self-heal and D4's unsatisfiability conjunct evaluate this rule; neither redefines it.
- **D4 (propose park)**: a scheduler decision, evaluated between D1 and D2, that records park proposals per plan: for EACH open plan that D1 skipped this turn with reason `externally-gated` AND whose gate is unsatisfied per the Gate satisfaction rule AND whose plan-file bytes have been unchanged for 7+ days, D4 records a park proposal for that plan. A turn where D1 dispatched a healthy plan still skipped the gated plans, so D4 still fires for them; D4 never fires for a plan D1 dispatched, a plan whose gate is satisfied, or a plan whose bytes changed within 7 days. It never moves plan bytes.
- **Stand-down outcome**: an execution child outcome (documented enum `pending|progress|failed` unchanged) whose `outcome_reason` field is `stand-down`; see Task 3.
- **Pins suite**: `scripts/check_maintenance_pins.sh`, the mechanical invariant checker for `agents/skills/maintenance/SKILL.md`.

## Assumptions

- assume gate classification is plan-declared (backlog item option (i)): a plan declares its gate with a header-block `External gate: <text>` line; the turn trusts the declaration and checks satisfaction only via the Gate satisfaction rule above; "no declaration" classifies as not gated, preserving today's behavior; basis: backlog item recommendation and its stated risk mitigation.
- assume Fix C (autonomous park execution) is NOT taken in this change; D4 only proposes; basis: backlog item's explicit recommendation against bundling C with A/B.
- assume the failure-cap carve-out is taken in this change independent of A/B; basis: backlog item "take it regardless".
- assume the park-proposal stasis threshold is 7 days of unchanged plan-file bytes (git evidence, not a new state history); basis: backlog item's suggested 7-day value, refined per review r1 F2 to a trigger with no new state path.
- assume the `External gate:` line is the interim metadata surface; when docs/history/backlog/2026-09-18-plan-driving-force-and-gist-tldr-metadata.md lands its unified metadata block, this line folds into that block (coordination noted there and here; the fold is out of scope for this plan).
- assume stand-down detection as a gate-classification signal (backlog option (ii)) is out of scope; the failure-cap carve-out (Task 3) already removes its main harm, and the item classifies it as usable only as a secondary signal.
Decision points requiring a grill: none remain.

## Gist & Examples

The maintenance scheduler's decision space is D1 execute / D2 author / D3 no-op. A plan whose own Ship-when names an unsatisfiable external prerequisite is indistinguishable to D1 from a dispatchable plan: it gets dispatched, its Task-1 stand-down edits nothing, the failure cap reads the zero-progress child outcome as a failure, and three such rounds halt the loop on a spurious alert. This happened with the legacy-verdict-grammar deletion plan (parked by hand 2026-09-18 only after Andrey asked why maintenance never proposed the deferral).

This plan adds three changes to `agents/skills/maintenance/SKILL.md`:

1. **Gated skip (Fix A).** Step 1's survey classifies each open plan as externally gated (header block declares `External gate:`) or not. Step 3's D1 skips gated plans exactly like dependency-blocked ones, with the mirrored self-heal: a gated plan whose gate satisfies the Gate satisfaction rule is no longer skipped and becomes dispatchable again without human action. The skip reason joins the dispatch-defect exemption list, so a turn that correctly refuses to dispatch a gated plan is not a `turn_error`. The Step 1 `pending_dispatch` reader re-verifies the classification before dispatching a decided-but-unscheduled target, so a plan gated between the deciding turn and the reader's turn is not dispatched.
2. **D4 propose park (Fix B).** D4 is a sibling decision evaluated after D1 (before D2). For each open plan D1 skipped this turn with reason `externally-gated` whose gate is unsatisfied per the Gate satisfaction rule and whose plan-file bytes have been unchanged for 7+ days (git evidence), D4 records a park proposal naming the plan, the gate text, and the unsatisfiability evidence, in three surfaces: an upserted `park_proposals` entry in the state file (keyed by plan path, bounded at 10 entries, oldest evicted), a per-plan repo-keyed `park-proposal-<plan-basename>` memory note, and the turn output (the turn's `decision_reason.execution` summary string names the plans proposed; the state schema's fixed two-key `decision_reason` object is not extended). Lifecycle: when the proposed plan leaves the top-level survey (a human parks it per `docs/plans/deferred/README.md`, or it executes), the next turn clears that plan's `park_proposals` entry and memory note; a later revival starts a fresh first-proposed date. No autonomous `git mv`; the deferred never-auto-picked invariant is unchanged.
3. **Failure-cap carve-out.** When an execution child's zero checkbox progress is explained by its own recorded stand-down (evidence, both conjuncts: the child's final report opens with the literal marker line `STAND-DOWN: <plan-path> <reason>` that the execution-child payload blueprint is extended to require whenever the plan's own Task 1 prescribes edit-nothing stand-down, and the target plan file is unchanged since dispatch, compared via git against the `dispatch_plan_sha` recorded on the children entry at dispatch time), the turn records the child outcome as `failed` (enum unchanged) with the documented new `outcome_reason: stand-down` field on the children entry, and the failure cap counts only entries whose `outcome_reason` is not `stand-down`, in the same spirit as the existing evidenced-provider-stop exception. The marker is a literal line prefix matched exactly, so a broken child whose traceback merely contains the word anywhere does not qualify.

Example (slug form): a plan whose header reads `External gate: deferred-archive-sweep` is skipped by D1 with reason `externally-gated` while no other open top-level plan or open backlog item has `deferred-archive-sweep` as a hyphen-bounded basename segment; when its bytes have been unchanged for 7+ days, D4 records a park proposal naming the plan, the gate line, and that evidence. When the archive sweep lands as an open backlog item named `...-deferred-archive-sweep.md`, the gate reads satisfied and the plan returns to D1's dispatchable set on its own. Example (date form): a plan whose header reads `External gate: 2026-11-01` is skipped until 2026-11-01 passes, then dispatchable; its value has no slug and no basename is ever consulted for it.

## Evaluation Criteria

**Quality dimensions:**
- correctness: a gated plan is never selected by D1 while its gate is unsatisfied, and a satisfied gate re-enables selection (self-heal) without human action; D4 is reachable (fires for every plan meeting all three conjuncts, and does not fire for a plan missing any single conjunct).
- correctness: a stand-down-explained zero-progress child outcome never increments `consecutive_failures` and can never alone trip the G2 alert.
- observability: every park proposal is visible in three places (turn output, bounded state-file entry, per-plan repo-keyed memory note) and names plan, gate, and unsatisfiability evidence; proposals for different plans never overwrite each other.
- maintainability: the pins suite still passes and pins the extended decision order in evaluation order.

**Done when:**
- `bash scripts/check_maintenance_pins.sh` exits 0 with the decision-order pin extended to the evaluation order D1, D4, D2, D3.
- All Task greps pass (fail-closed, per Validation Commands).
- Each task commit touches exactly its declared Files list (witnessed by the commit-scope gates); no task touches `docs/plans/deferred/` or `docs/plans/completed/`, so parked plan bytes stay identical. Concurrent peer commits on the shared branch are outside this plan's Done-when by construction (the commit-scope gates attribute by subject).

**Ship when:**
- [class: OPERATIONS_FOLLOW_UP] A production scheduler turn observes a live gated plan and records the first real park proposal or skip reason; evidence owner: the next scheduler turns' state files; closure: one turn output naming `externally-gated` for a real plan.
- [class: OPERATIONS_FOLLOW_UP] After A/B have run long enough to trust the classifier (human judgment, per backlog item), Fix C (D4 graduates to executing the byte-identical park) is a separate follow-up plan; evidence owner: Andrey; closure: a follow-up plan exists or the decision is recorded.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/SKILL.md` (Step 1 survey and pending_dispatch reader, Step 3 decision list, the failure-cap section and its children-entry schema documentation, the state-file schema block and writer-classes list, the Invariants list, the schema changelog)
- `agents/skills/maintenance/prompt-templates.md` (execution-child payload blueprint: stand-down report marker duty and its documented-deviations registration)
- `scripts/check_maintenance_pins.sh` (decision-order pin extension only)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed.

**Out of scope; reject unless plan-related:**
- `docs/plans/deferred/` contents; reason: the never-auto-picked invariant is unchanged and no plan bytes move.
- `agents/skills/maintenance/zcode.md`; reason: the backlog scope note says the overlay changes only if the classification helper lives there; this plan puts classification in SKILL.md prose, not the overlay.
- `docs/history/backlog/2026-09-18-plan-driving-force-and-gist-tldr-metadata.md` implementation; reason: coordination target only, its metadata block is a separate plan.

## Validation Commands

```bash
set -u
cd "$(git rev-parse --show-toplevel)"
SKILL=agents/skills/maintenance/SKILL.md
fail() { echo "GATE FAIL: $1" >&2; exit 1; }

# Task 1 gates: gated-skip in D1, the exemption list extension, the reader re-check, and the self-heal witness.
grep -q "externally gated" "$SKILL" || fail "no externally-gated classification in survey/D1"
grep -q "externally-gated" "$SKILL" || fail "no externally-gated skip reason"
grep -q "or external-gate reason" "$SKILL" || fail "dispatch-defect exemption not extended"
grep -q "reader re-verifies the external-gate classification" "$SKILL" || fail "reader re-verification missing"
grep -q "mirrored self-heal" "$SKILL" || fail "self-heal wording missing from D1"

# Task 2 gates: D4 exists, in evaluation order between D1 and D2, with its three visibility surfaces.
grep -q "D4 (propose park)" "$SKILL" || fail "D4 decision missing"
grep -q "park_proposals" "$SKILL" || fail "state-file park proposal surface missing"
grep -q "park-proposal-" "$SKILL" || fail "per-plan memory-note surface missing"
grep -qi "never auto-picked" "$SKILL" || fail "deferred invariant text vanished"
SKILL_ORDER="$(grep -oE 'D[0-9]+ \([a-z- ]+\)' "$SKILL" | head -4 | tr '\n' ' ')"
case "$SKILL_ORDER" in "D1 (execute) D4 (propose park) D2 (author) D3 (no-op) "*) ;; *) fail "decision evaluation order wrong: $SKILL_ORDER";; esac

# Task 3 gates: stand-down carve-out with its evidence surface, schema home, and cap exclusion.
grep -q "outcome_reason" "$SKILL" || fail "children-entry outcome_reason field missing"
grep -q "dispatch_plan_sha" "$SKILL" || fail "children-entry dispatch_plan_sha field missing"
grep -qi "stand-down carve-out" "$SKILL" || fail "failure-cap carve-out missing"
grep -q "outcome_reason.\{0,1\} is not .\{0,1\}stand-down" "$SKILL" || fail "cap exclusion not pinned"
grep -q "STAND-DOWN:" agents/skills/maintenance/prompt-templates.md || fail "stand-down report marker not added to the execution payload blueprint"
if grep -qi "stand-down carve-out accrues failure credit" "$SKILL"; then fail "carve-out inverted"; fi

# Commit-scope witness for the Done-when criterion: each of this execution's three task
# commits touches exactly its declared Files list (attributable by subject; concurrent
# peer commits on the shared branch are invisible to this gate by construction).
BASE="$(cat docs/tmp/park-guard-base-sha.txt)"
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
commit_scope_ok "maintenance: D1 skips externally gated plans with mirrored self-heal" agents/skills/maintenance/SKILL.md agents/skills/maintenance/prompt-templates.md
commit_scope_ok "maintenance: D4 proposes park for stalled externally gated plans" agents/skills/maintenance/SKILL.md scripts/check_maintenance_pins.sh
commit_scope_ok "maintenance: stand-down child outcomes do not accrue failure credit" agents/skills/maintenance/SKILL.md agents/skills/maintenance/prompt-templates.md

# Task 4: pins suite over the extended evaluation-order pin.
bash scripts/check_maintenance_pins.sh || fail "pins suite"
```

Gate provenance: the new-string gates (classification, exemption, reader re-check, mirrored self-heal, D4, both proposal surfaces, `outcome_reason`, `dispatch_plan_sha`, the carve-out, the cap exclusion, the payload marker) are RED today (none exist in the target files; first gate measured firing with exit 1 at authoring) and flip GREEN exactly when the tasks land; the `never auto-picked` grep is a preservation canary, GREEN today and required to stay GREEN; the evaluation-order `case` gate is RED today under the current three-decision file and GREEN only under the Task 2 order (its `D[0-9]+ \([a-z- ]+\)` class admits the hyphen in `no-op`); the reader and cap-exclusion needles use `\{0,1\}` tolerance so they match the field name with OR without backticks (measured both forms at authoring); the BASE variable in the byte-identity gate is the git sha recorded before the first task commit, so the gate measures this execution's committed history and is insensitive to concurrent peers' working-tree files.

### Task 1: Gated classification and D1 skip

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/prompt-templates.md`

- [ ] Before the first commit, record the current HEAD sha to `docs/tmp/park-guard-base-sha.txt` (one line, `git rev-parse HEAD`); the Validation Commands' commit-scope gates read it as BASE. [class: IMPLEMENTATION_REQUIRED]
- [ ] In the Step 1 survey's open-plans bullet, add the classification rule: each open top-level plan's header block (title line through the first `## ` heading, nothing beyond it) is scanned for a line matching `^External gate:`; a plan carrying the line is externally gated and its gate is evaluated per the Gate satisfaction rule in this plan's Terms; a plan without the line in that region is not gated (no declaration = not gated, preserving current behavior; body text never classifies). Record the skip with reason `externally-gated` in the survey output. [class: IMPLEMENTATION_REQUIRED]
- [ ] In Step 3's `D1 (execute)` bullet, extend the skip rule: D1 skips externally gated plans exactly like dependency-blocked ones, with the mirrored self-heal (a gated plan whose gate satisfies the Gate satisfaction rule is no longer skipped and becomes dispatchable again without human action), so a satisfied gate cannot starve the queue. [class: IMPLEMENTATION_REQUIRED]
- [ ] In the same D1 bullet's must-dispatch sentence, extend the exemption list from "without a guard, quota, or dependency reason" to "without a guard, quota, dependency, or external-gate reason", so a correct refusal to dispatch a gated plan records no `turn_error`. [class: IMPLEMENTATION_REQUIRED]
- [ ] Extend the Step 1 `pending_dispatch` reader: before dispatching a decided-but-unscheduled target, the reader re-verifies the external-gate classification of the target plan; a target that has become gated is not dispatched and the pending entry is cleared with the skip reason recorded. [class: IMPLEMENTATION_REQUIRED]
- [ ] Reachability witness for the classification: a plan declaring `External gate:` in its header block classifies as gated even when digest-intact and oldest; a plan with the phrase only in its body (below the first `## ` heading) classifies as not gated; a plan without the line classifies as not gated even when its prose mentions external preconditions. [class: REPOSITORY_TEST]
- [ ] Self-heal witness: a gated plan whose gate reads satisfied (the declared date passes for a date-form gate, or an open top-level plan or open backlog item other than the declaring plan gains the slug as a hyphen-bounded basename segment for a slug-form gate) is no longer skipped by D1 and is dispatched under the normal selection rules with no human action; a gated plan whose only slug match is the declaring plan itself, or whose slug matches only inside a longer word (not hyphen-bounded), stays skipped. [class: REPOSITORY_TEST]
- [ ] Reader-race witness: a `pending_dispatch` target that gains an `External gate:` line between the deciding turn and the reader's turn is not dispatched by the reader; the pending entry is cleared and the skip reason recorded, so the bypass cannot reintroduce a gated dispatch. [class: REPOSITORY_TEST]
- [ ] Exemption witness: a turn that ends with the execution lane free and only externally gated plans queued records NO dispatch-defect `turn_error` (the external-gate reason exempts it); the negative control holds: a turn that idles with an ungated dispatchable plan available still records the defect. [class: REPOSITORY_TEST]
- [ ] Sync the execution blueprint's SUCCESSOR DISPATCH paragraph in `agents/skills/maintenance/prompt-templates.md`: its self-contained D1-rule restatement gains the same external-gate skip (mechanically restated in the payload's own words: skip open top-level plans whose header block, title line through the first `## ` heading, carries an `External gate:` line that is unsatisfied per the same rule the payload restates: date form unsatisfied until the named `YYYY-MM-DD` date passes; slug form unsatisfied while no open top-level plan or open backlog item other than the declaring plan carries the slug as a hyphen-bounded basename segment), and register the change in prompt-templates.md's documented-deviations header list. Precedent: the r2-hardening deviation entry synced this same paragraph's deferred-blocker skip to D1. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `maintenance: D1 skips externally gated plans with mirrored self-heal` [class: IMPLEMENTATION_REQUIRED]

### Task 2: D4 propose park

Files:
- `agents/skills/maintenance/SKILL.md`
- `scripts/check_maintenance_pins.sh`

- [ ] Add `D4 (propose park)` as a sibling decision bullet evaluated after `D1 (execute)` and before `D2 (author)` (it refines D1's per-plan skip outcomes; the pins order literal in this task's pin checkbox pins that evaluation order, so a placement behind the `D3 (no-op)` catch-all fails the pin). Firing conjuncts, evaluated PER PLAN and all required for that plan: D1 skipped the plan this turn with reason `externally-gated` (D1 dispatches at most one plan; every gated plan it skipped is a D4 candidate even in a turn where another plan was dispatched); the plan's gate is unsatisfied per the Gate satisfaction rule; the plan file's bytes are unchanged for 7+ days (git log/diff evidence against the plan path). For EACH plan meeting all three conjuncts, record a park proposal naming the plan, the gate text, and the unsatisfiability evidence, in all three surfaces: an upserted `park_proposals` entry in the state file (keyed by plan path, bounded at 10 entries, oldest evicted), a per-plan repo-keyed `park-proposal-<plan-basename>` memory note (repo-keyed like `loop-parent-missing`, plan-basename-suffixed so concurrent proposals never overwrite each other), and the turn output (the turn's `decision_reason.execution` summary string names the plans proposed; the schema's fixed two-key `decision_reason` object gains no new key). Lifecycle: when a proposed plan leaves the top-level survey (human park per `docs/plans/deferred/README.md`, or execution), the next turn clears that plan's `park_proposals` entry and memory note; a revival starts a fresh first-proposed date. The plan keeps being skipped; no autonomous `git mv` of certified work; the deferred never-auto-picked invariant is unchanged. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add `park_proposals` to the state-file schema documentation block (top-level array, each entry: plan path, gate text, first proposed date, latest evidence, upsert key = plan path, cap 10); note it is additive under schema 3 (no version bump). [class: IMPLEMENTATION_REQUIRED]
- [ ] Update the state-file writer-classes list to include the park-proposal write as a sanctioned write mode. [class: IMPLEMENTATION_REQUIRED]
- [ ] Extend the pins suite's decision-order check from `["D1 (execute)", "D2 (author)", "D3 (no-op)"]` to the evaluation order `["D1 (execute)", "D4 (propose park)", "D2 (author)", "D3 (no-op)"]`; no other pins change (new invariants get pins only after they settle, per the backlog acceptance criteria). [class: IMPLEMENTATION_REQUIRED]
- [ ] Reachability witness: D4 fires for every plan meeting all three conjuncts, including two or more stalled gated plans in one turn (one proposal each, never overwriting); D4 does not fire for a plan D1 dispatched, a plan whose gate is satisfied, or a plan whose bytes changed within 7 days. Guard witness: a tripped `G1e` resolves D4 to D3 like D1 (D4 is execution-lane material); a `G2`/`G3` stand-down suppresses D4 entirely for the turn (no proposal is recorded and none is emitted; the next unstood-down turn re-evaluates and records then). [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: `bash scripts/check_maintenance_pins.sh` (extended evaluation-order pin passes against the updated SKILL.md) [class: REPOSITORY_TEST]
- [ ] Commit: `maintenance: D4 proposes park for stalled externally gated plans` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Failure-cap stand-down carve-out

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/prompt-templates.md`

- [ ] In the execution-child payload blueprint in `agents/skills/maintenance/prompt-templates.md`, add the stand-down report duty: whenever the target plan's own first task prescribes an edit-nothing stand-down (external gate unsatisfied), the child writes `.ai-playbook/last-stand-down.json` (an object: plan path, gate-unsatisfied reason, ISO date) as its LAST action before reporting, and its final report opens with the literal marker line `STAND-DOWN: <plan-path> <gate-unsatisfied-reason>`; on any other outcome the marker must not appear and the file must not be written (no false positives from ordinary failure reports). Register this addition in prompt-templates.md's documented-deviations header list with a one-line rationale, keeping the file's copied-verbatim provenance claim true. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add `outcome_reason` and `dispatch_plan_sha` to the documented children-entry schema (the failure-detection section's schema documentation): `outcome_reason` is an optional string, `null` by default, value `stand-down` per this task; `dispatch_plan_sha` is the target plan file's sha256 recorded at dispatch time, `null` for authoring children; note both are additive under schema 3. [class: IMPLEMENTATION_REQUIRED]
- [ ] In "Failure detection and the failure cap", add the stand-down carve-out beside the existing evidenced-stop exceptions. Machine test, two conjuncts, both required and named: `.ai-playbook/last-stand-down.json` is present and names the target plan path (the json file is the machine-readable retrieval surface; no report-retrieval primitive exists and none is assumed), and the target plan file is unchanged since dispatch (git comparison of the plan path's current sha against the children entry's `dispatch_plan_sha`). The child's final report opening with the literal `STAND-DOWN:` marker line is the human-visible witness quoted in the turn output, produced by the payload duty above; it is not part of the machine test. On the carve-out: the outcome stays the documented enum value `failed`, `outcome_reason` is set to `stand-down`, `consecutive_failures` is not incremented, the cap's count includes only children entries whose `outcome_reason` is not `stand-down`, and the checked json file is consumed (deleted or cleared) by the checking turn so a stale file cannot qualify a later child. A genuinely broken child that wrote no json file does not qualify, so real stall loops keep accruing credit. [class: IMPLEMENTATION_REQUIRED]
- [ ] Carve-out witness: a stand-down outcome accrues nothing, so a stand-down followed by two real failures holds `consecutive_failures` at 2, below the three-strike cap; three stand-down outcomes alone never trip the alert; a child whose report opens with the marker while its plan file changed since `dispatch_plan_sha` does NOT qualify and accrues credit normally; a child whose report contains the word stand-down anywhere but does not OPEN with the marker does not qualify. [class: REPOSITORY_TEST]
- [ ] Commit: `maintenance: stand-down child outcomes do not accrue failure credit` [class: IMPLEMENTATION_REQUIRED]

## Residual review findings (at-cap finalize, 2026-09-19)

Review loop r1-r5 (artifacts at docs/reviews/2026-09-19-plan-review-maintenance-park-guard-externally-gated-plans-r1..r5.md). All blocking findings from r1-r4 and r5's single blocking finding (F1 successor-dispatch bypass: the execution blueprint's SUCCESSOR DISPATCH paragraph now carries the external-gate skip and its documented-deviations registration) were folded. The cap was reached, so the final fold set (r5 F1-F4 folds: successor sync, exemption witness, corrected witness arithmetic, json+sha machine-test wording) has NOT been re-reviewed by a fresh round: the latest sidecar (r5) digest precedes the final plan bytes, so `plan_readiness.py` reports the sidecar stale and the execution PRE-STEP must run a fresh certification round before dispatch. Non-blocking residuals accepted at the cap: none open beyond that re-certification requirement (r5 F2-F4 were folded in the same pass).
