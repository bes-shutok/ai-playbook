# Plan: Scheduler/maintenance loop-quality hygiene (audit lane, pin precision, emission discipline, dedupe, closures)

Backlog origins (scope of record): `docs/history/backlog/2026-09-19-maintenance-friction-audit-lane.md`,
`docs/history/backlog/2026-09-20-maintenance-pin-vacuity-lows.md`,
`docs/history/backlog/2026-09-20-maintenance-precheck-trigger-idle-turn-vacuity.md`,
`docs/history/backlog/2026-09-20-maintenance-primitive-emission-suppression-and-resume-carriers.md`,
`docs/history/backlog/2026-09-20-dedupe-cannot-distinguish-reopen-from-stale-leftover.md`,
`docs/history/backlog/2026-09-19-b2p2-remaining-origin-item-closure.md`.

Sibling plans: `2026-09-21-scheduler-maintenance-state-durability.md` and
`2026-09-21-scheduler-maintenance-loop-quality-gates.md`. This plan edits the maintenance SKILL.md
survey/lane section, the State file children-entry schema, the overlay, the pins suite, and one-sentence
budget-gate additions; the unlanded peer branches touch adjacent (not identical) sections, and landing
order resolves via the PRE-STEP re-certification and union-merge precedent. The friction-audit origin was
deferred to "its own future plan" by `docs/plans/2026-09-19-scheduler-ops-lanes-durability.md` Task 7;
that future plan is this one.

Plan review: docs/reviews/2026-09-21-plan-review-scheduler-maintenance-loop-quality-hygiene-r*.md (latest ready round)

## Terms

- **Audit lane**: the bounded, watermark-driven friction-audit sub-lane of the maintenance loop, dispatched like an authoring child but idle/off-peak preferred.
- **Audit child**: a scheduler-dispatched child whose state-file `kind` is `audit`; it occupies the authoring lane (never beside an authoring child), its completion evidence is the audit state file's digest and `next_due` being updated after its `created_at`, and its progress predicate is the same update.
- **Watermark**: per-source progress record (max scanned timestamp, row count, last daily log, sampled mtime) in the audit state file; advanced only after a source is fully processed; missing state means cold start.
- **next_due**: the audit state file's ISO timestamp of the next due audit; the quantitative script writes it at each processing completion as completion time plus the cadence; the scheduler turn's survey reads it.
- **Quantitative pass**: the deterministic script pass computing error rates, event histograms, provider-code counts, and correction-heuristic candidates; the model pass reads only its digest plus targeted samples.
- **Emission suppression**: the witnessed failure where a session repeats read-only automation listings and never emits the already-decided mutating call.
- **Headless resume recipe**: the launchd job script form that exports the provider-config environment variables explicitly so a scheduled resume survives the desktop app's absence.

## Assumptions

- assume app db, log, and transcript locations stay host-local runtime inputs resolved at invocation (tilde-form defaults, never committed absolute paths); basis: the origin's own data map and the never-hardcode-paths guideline.
- assume the budget-gate sections can take one added sentence each without colliding with the in-flight quota-aware sibling work; basis: that work rewrites adjacent semantics, not the automation-first carrier sentences this plan annotates.

Decision points requiring a grill: `friction_audit_dir` defaults to `.ai-playbook/friction-audit/` (runtime-local and gitignored, verified `/.ai-playbook/` in .gitignore) while the key resolution follows the `tmp_dir` pattern; standing pre-authorization (scheduling ask, 2026-09-21); affects the bootstrap key and the SKILL.md Configuration row. The Step 5 rephrase lands before the pin-vacuity count pins in the same plan so the new pins anchor the new phrase; standing pre-authorization (scheduling ask, 2026-09-21); affects task order. Dedupe removes a twin only when normalized bodies AND Status values match, treating Status-only differences as surface-and-keep; standing pre-authorization (scheduling ask, 2026-09-21); affects the script and tests. The audit child is a dedicated `kind: "audit"` occupying the authoring lane (rather than reusing kind `author`), because the authoring completion evidence (target-plan certification) and progress predicate are unsatisfiable for an audit run; standing pre-authorization (scheduling ask, 2026-09-21); affects the State file schema, the G1a sentence, the Invariants bullet, and the writer-classes list. The audit cadence is a Configuration row `friction_audit_cadence_days` (fallback 7) and `next_due` is written by the quant script at processing completion; standing pre-authorization (scheduling ask, 2026-09-21); affects Tasks 1, 2, and the Configuration table.

## Gist & Examples

What changes: the one-off 2026-09-19 friction audit becomes a standing, capped, watermark-driven lane of
the maintenance loop; the pins suite stops passing when the operative text it names is deleted; the Step 5
precheck trigger stops being vacuous on idle-only turns; suppressed mutation emissions leave durable
intent; the docs-branch dedupe stops deleting legitimately re-opened backlog items; and three long-open
batch-2 phase-2 origin items finally read closed.

**Before (today):** the audit's mining recipe works but nothing schedules a re-run, nothing remembers
scanned ranges, and a naive re-run re-spends 700k-950k tokens per mining sub-agent; the correction rate
stayed flat for three months because fixes land as one-off snapshots. The pins suite's `ladder precheck`
pin stays green when the Step 5 precondition sentence is deleted (a scoping note also carries the
phrase), and each stand-down-reason string passes with either occurrence. On a turn whose decided
dispatch is idle-only, the Step 5 precondition's quota-leg clause never literally occurs, so the
runtime-agnostic contract reads as untriggered there. Sessions twice stood down after repeating listings
with the decided create unsent, once leaving the loop dark overnight. The dedupe deletes a re-opened item
whose archived twin matches beyond Status. The three batch-2 phase-2 items sit open with now-fixed
problem statements (the squash 7334dd25 is on main).

**After (this plan):** the scheduler consults the audit state's `next_due`; when due and lanes allow, it
dispatches at most one audit child (idle/off-peak preferred, park/retain on pressure) whose quantitative
script pass writes a digest the model pass reads with hard sub-agent and token caps; watermarks make the
second run delta-only, and the script stamps `next_due` at completion so the lane runs at its cadence
instead of every turn. The pins pin the exact Step 5 needle and per-occurrence reason-string counts, so a
single deletion trips them. The Step 5 precondition reads "after the quota leg (for a clocked dispatch)
or the dispatch decision (for an idle-time dispatch), and before any ladder step", triggering on every
dispatch class. The dispatch-discipline text names the suppression witness and routes stand-downs through
immediate Bash state writes carrying durable intent, with a new launchd resume-carrier bullet documenting
the env-complete headless recipe. The dedupe requires Status agreement before removal. The three items
flip to `Status: closed (fixed by batch-2 phase-2)` with pointers to 7334dd25.

**Edge cases:** a missing audit state file means cold start (full corpus, same as other maintenance state
files); a legitimately archived-then-reopened item with a non-Status body edit is kept with the existing
mismatch warning (only Status-only differences surface-and-keep); an idle-lane turn on a runtime whose
overlay omits the precheck bullet still reads a literal trigger from SKILL.md.

## Design Invariants (CR Guard)

- SKILL.md stays runtime-agnostic: the audit recipe's db paths, table shapes, and provider codes live in
  the zcode.md overlay; SKILL.md carries only lane semantics.
- The audit lane never becomes the bottleneck it measures: at most one audit child, it occupies the
  authoring lane, at most 2 sub-agents per run, recorded token budget, idle/off-peak preferred,
  park/retain on quota pressure.
- Pins fail closed on the exact text they claim to protect: occurrence counts, not presence, for
  multi-site phrases; distinctive multi-word spans quoted verbatim from the prescribed text so a
  Revisions-ledger mention cannot satisfy a pin; freeze-literal origin notes appended per the suite's protocol.
- The dedupe sweep never widens beyond archived twins; idempotent; always exits 0 (warn-and-continue posture).
- No personal or absolute machine paths in repo files; the audit script takes `--db`, `--logs-dir`,
  `--out-dir` arguments with tilde-form defaults only.

## Evaluation Criteria

**Quality dimensions:**
- correctness: watermark semantics, `next_due` write rule, status-matching dedupe, and cap recording
  each have an owning paragraph and a test; b2p2 flips cite the landed commit; the audit child's state
  representation is coherent end to end (kind, lane, completion evidence, progress).
- testability: script unit tests with scratch fixtures and teardown; every new or replaced pin has a
  recorded flip-probe; the rephrased Step 5 sentence's pin fails when the sentence is deleted.
- consistency: bootstrap key table and Integration Points row, SKILL.md Configuration rows, overlay
  recipe, and audit-lane paragraph agree on the dir default and the cadence; Integration Points updated
  in both directions (bootstrap provides the key with a maintenance consumer row; maintenance consumes it).
- simplicity: one new script per concern (audit quant, dedupe fix in place), no new primitives.

**Done when:**
- All tasks checked; `python3 scripts/test_friction_audit_quant.py` and `python3 scripts/test_docs_branch_backlog_dedupe.py` exit 0.
- `bash scripts/check_maintenance_pins.sh` exits 0 including the replaced and new pins.
- `python3 scripts/plan_readiness.py docs/plans/2026-09-21-scheduler-maintenance-loop-quality-hygiene.md` exits 0.
- The latest review round reports ready=yes with zero unresolved blocking findings on the final digest.

**Ship when:**
- The first watermark-driven audit re-run processes only its delta at a fraction of cold-start cost, and
  the corrections-mining pass shows new friction landing as dated evidence lines instead of new items.
  Loop-owned; prose only. [class: OPERATIONS_FOLLOW_UP]

## Review Scope

**Explicit must-fix; findings on these paths are always in scope (review and fix if valid):**

**Production code:**
- `scripts/friction_audit_quant.py` *(new)*
- `scripts/docs_branch_backlog_dedupe.py`
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `agents/skills/bootstrap-ai-playbook/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `docs/history/backlog/2026-09-18-execute-plan-sidecar-boundary-sentence-dedup.md`
- `docs/history/backlog/2026-09-18-execute-plan-contract-requiredness-wording.md`
- `docs/history/backlog/2026-09-18-execute-plan-recurrence-relay-consumer-seam.md`

**Tests:**
- `scripts/test_friction_audit_quant.py` *(new)*
- `scripts/test_docs_branch_backlog_dedupe.py`
- `scripts/check_maintenance_pins.sh`

**Plan-related extension;** findings are in scope when causally related to this plan.

**Partially-in-scope files:** in `maintenance/SKILL.md`, only the Configuration table, the Step 1/Step 5
sentences named (including the Step 1 pending-dispatch reader's audit validation arm, the Step 3 D2
decision sentence and its must-dispatch exemption wording for the `audit-lane-due` reason, and the
Step 5 final-slot precondition's audit visibility), the audit-lane paragraph region, the State file
children-entry schema (the `kind` enum and the audit completion-evidence arm), the `pending_dispatch`
field paragraph (the audit kind and its validation arm), the Step 2 state-file arm release-rules
sentence (the completion-evidence enumeration, for the audit arm), the writer-classes list, the
failure-cap section's progress-definition bullets (the audit progress predicate arm only), the G1a lane
sentence and the Invariants bullet, and the Revisions ledger are open. In `zcode.md`, only the
dispatch-discipline bullet, the child classification markers bullet (the audit marker), the new "Audit
recipe" section, and the new launchd resume-carrier bullet are open. In `plans/SKILL.md` and
`execute-plan/SKILL.md`, only the one-sentence suppression-risk addition near each budget gate's
automation-first carrier reference is open. In the pins suite, only the toolset-precheck block and the
new audit-lane pins are open. The three backlog items are open only for their Status line and pointer.

**Out of scope; reject unless plan-related:**
- `scripts/quota_window_probe.py`; reason: the in-flight quota-aware sibling owns it.
- any blueprint body in `prompt-templates.md`; reason: this plan deliberately does not touch the payloads.
- pre-existing em dashes outside the open regions (measured 2026-09-21: one in the zcode.md Session
  compaction bullet, three in execute-plan SKILL.md budget sections); reason: frozen or peer-contested regions.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)"
S="$REPO/agents/skills/maintenance/SKILL.md"
Z="$REPO/agents/skills/maintenance/zcode.md"
PIN="$REPO/scripts/check_maintenance_pins.sh"
fail=0
# 1. Script tests
python3 "$REPO/scripts/test_friction_audit_quant.py" >/dev/null 2>&1 || { echo "FAIL: audit quant tests"; fail=1; }
python3 "$REPO/scripts/test_docs_branch_backlog_dedupe.py" >/dev/null 2>&1 || { echo "FAIL: dedupe tests"; fail=1; }
# 2. Audit-lane wiring needles: distinctive verbatim spans of the prescribed text, count-gated where the
#    Revisions ledger could also quote them
n=$(grep -oF 'when due and lanes allow, dispatch at most one audit child' "$S" | wc -l | tr -d ' ')
[ "$n" -eq 1 ] || { echo "FAIL: lane paragraph operative span missing or duplicated ($n)"; fail=1; }
grep -qF 'friction_audit_dir' "$S" || { echo "FAIL: config row missing"; fail=1; }
grep -qF 'friction_audit_cadence_days' "$S" || { echo "FAIL: cadence row missing"; fail=1; }
grep -qF 'execute|author|audit' "$S" || { echo "FAIL: audit kind literal missing from schema"; fail=1; }
grep -qF 'next_due' "$S" || { echo "FAIL: next_due wording missing"; fail=1; }
grep -qF '## Audit recipe' "$Z" || { echo "FAIL: overlay recipe section missing"; fail=1; }
grep -qF 'friction_audit_dir' "$REPO/agents/skills/bootstrap-ai-playbook/SKILL.md" || { echo "FAIL: bootstrap key missing"; fail=1; }
# 3. Step 5 dispatch-class-neutral rephrase: region-scoped count so the Revisions-ledger quote cannot inflate it
n=$(awk '/^### Step 5: scheduling/{f=1;next} /^### Step 6: state update/{f=0} f' "$S" | grep -oF 'or the dispatch decision (for an idle-time dispatch)' | wc -l | tr -d ' ')
[ "$n" -eq 1 ] || { echo "FAIL: Step 5 rephrase missing or duplicated in region ($n)"; fail=1; }
# 4. Emission-suppression discipline needles
grep -qF 'emission suppression' "$Z" || { echo "FAIL: suppression witness missing"; fail=1; }
grep -qF 'ZCODE_BUILTIN_PROVIDER_CONFIG_FILE' "$Z" || { echo "FAIL: headless recipe missing"; fail=1; }
# 5. b2p2 closures: all three items read closed
for b in 2026-09-18-execute-plan-sidecar-boundary-sentence-dedup 2026-09-18-execute-plan-contract-requiredness-wording 2026-09-18-execute-plan-recurrence-relay-consumer-seam; do
  grep -qF 'Status: closed (fixed by batch-2 phase-2)' "$REPO/docs/history/backlog/$b.md" || { echo "FAIL: $b not closed"; fail=1; }
done
# 6. Pins suite green
bash "$PIN" || { echo "FAIL: pins do not hold"; fail=1; }
# 7. Em-dash ban via a portable byte pattern (printf octal works on bash 3.2 where $'\u2014' does not),
#    scoped to files this plan creates (plans rule 28): the canonical check-no-em-dash.sh is not used
#    here because its prose filter is vacuous on .py targets and its invocation takes a `file`
#    subcommand; the edited files carry legacy em dashes in frozen or peer-contested regions (measured
#    2026-09-21: one in zcode.md, three in execute-plan SKILL.md) and their insertions are covered by
#    the exact-needle greps above.
EMDASH="$(printf '\342\200\224')"
for f in scripts/friction_audit_quant.py scripts/test_friction_audit_quant.py; do
  if grep -q "$EMDASH" "$REPO/$f"; then echo "FAIL: em dash in $f"; fail=1; fi
done
[ "$fail" -eq 0 ] && echo "validation: all hold" || exit 1
```

### Task 1: Friction-audit quantitative script and tests

Files:
- `scripts/friction_audit_quant.py` *(new)*
- `scripts/test_friction_audit_quant.py` *(new)*

- [ ] Write the script: CLI args `--db`, `--logs-dir`, `--out-dir`, `--since`, `--cadence-days` (all optional with tilde-form documented defaults, never committed absolute paths); computes per-tool error rates and message classes, per-day event histograms (with the persistence-noise filter applied), provider 429 code counts, and correction-heuristic candidates; writes `digest.md` plus `counts.json` under the out dir and updates `state.json`: per-source watermarks (max timestamps, row counts, last daily log) advanced only after full processing, and `next_due` written at each processing completion as completion time plus `--cadence-days` (default 7); missing state means cold start [class: IMPLEMENTATION_REQUIRED]
- [ ] `test_friction_audit_quant.py#test_cold_start_full_scan`; given an empty state file, expects full-range aggregates written and `next_due` stamped completion plus 7 days [class: REPOSITORY_TEST]
- [ ] `test_friction_audit_quant.py#test_watermark_delta_only`; given a state file whose watermarks sit mid-corpus, expects only post-watermark rows aggregated and watermarks advanced [class: REPOSITORY_TEST]
- [ ] `test_friction_audit_quant.py#test_noise_filter`; given histogram input containing persistence-event lines, expects them excluded from the digest counts [class: REPOSITORY_TEST]
- [ ] `test_friction_audit_quant.py#test_digest_and_counts_written`; expects both artifacts with the documented fields including `next_due` [class: REPOSITORY_TEST]
- [ ] Fixtures: synthetic sqlite/logs under mktemp with explicit teardown; run → expect GREEN [class: REPOSITORY_TEST]

### Task 2: SKILL.md audit-lane paragraph, Configuration rows, and the audit child's state representation

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md` *(the child classification markers bullet only; the audit marker edit)*

- [ ] Configuration table: add the `friction_audit_dir` row (purpose: audit watermark state and digests; fallback `.ai-playbook/friction-audit/`) and the `friction_audit_cadence_days` row (purpose: audit lane cadence consumed by the quant script's `next_due` write; fallback 7) [class: IMPLEMENTATION_REQUIRED]
- [ ] Add the audit-lane paragraph in the survey/lane region, containing the exact span `when due and lanes allow, dispatch at most one audit child`: the turn consults the audit state's `next_due` during the survey; when due and lanes allow, dispatch at most one audit child with the authoring dispatch discipline (claim check, children[] entry, park/retain on quota pressure), idle/off-peak preferred; hard caps: at most 2 sub-agents and a total token budget recorded in the audit state; dedupe-and-fold: evidence on existing items becomes a dated evidence line, new items only after checking open plus completed plus deferred [class: IMPLEMENTATION_REQUIRED]
- [ ] State file children-entry schema: extend the `kind` enum to `execute|author|audit` (JSON block and field prose, the exact literal `execute|author|audit`); the audit child occupies the authoring lane, so amend the G1a exclusivity sentence ("One authoring child still never runs alongside another") to add that an audit child occupies the same lane [class: IMPLEMENTATION_REQUIRED]
- [ ] Step 2 state-file arm release rules: add the audit arm to the completion-evidence definition: for kind `audit`, completion evidence is the audit state file's digest and `next_due` updated after the entry's `created_at` (so the lane hold releases on evidenced audit completion instead of the unsatisfiable target-plan certification) [class: IMPLEMENTATION_REQUIRED]
- [ ] Failure-cap progress definitions: add the audit progress predicate: progress for an audit child means the audit state file's digest and `next_due` updated after the recorded `created_at` (same witness as the completion evidence), so an audit child neither accrues credit while running nor holds the lane after finishing [class: IMPLEMENTATION_REQUIRED]
- [ ] Overlay child classification markers: add the audit marker: a prompt containing the audit dispatch marker occupies only `G1a` (mirroring the authoring-marker rule), so a listed audit record never occupies both lanes [class: IMPLEMENTATION_REQUIRED]
- [ ] `pending_dispatch` audit arm: extend the field's kind enum to `execute|author|audit` (JSON-adjacent field paragraph and the schema line's documented shape), and add the Step 1 reader validation arm for an audit-kind target: valid while the audit lane consult (the state file's `next_due`, or its cold-start absence) still reads due per the lane paragraph, otherwise cleared with the reason recorded in `decision_reason`; the audit park/retain write joins the sanctioned `pending_dispatch` Bash-state-edit write modes (alongside the ladder-precheck and rate-pressure parks) [class: IMPLEMENTATION_REQUIRED]
- [ ] Same-turn contention resolution (the audit consult at Step 1 precedes the Step 3 decisions, so the turn knows before deciding): when the audit consult reads due and the authoring lane is free, the audit dispatch takes the authoring lane's slot and D2 resolves to D3 for that turn with reason `audit-lane-due` (a sanctioned must-dispatch exemption, so no dispatch-defect `turn_error` fires; one audit per cadence bounds the authoring starvation at one slot per cadence period); when the audit reads due but `G1a` holds the lane, the audit parks in `pending_dispatch` (audit kind) and the next turn's reader re-dispatches it when the lane frees; cold start (no audit state file) reads due, so the first full-corpus audit dispatches at the next free authoring-lane slot under the same guard; the Step 5 final-slot precondition counts the recorded audit child via the state-file arm, so a same-turn authoring dispatch cannot pass the lane re-evaluation after the audit took the slot [class: IMPLEMENTATION_REQUIRED]
- [ ] Audit-park occupancy arbitration (the `pending_dispatch` slot is single-valued): the audit park writes only when the slot is null; when a retained execute or author dispatch already occupies it, the audit dispatch is skipped this turn with reason `pending-dispatch-occupied` recorded in `decision_reason`; the retained entry is never silently overwritten (the slot's existing retained-entry contract), and the audit consult simply re-fires next turn because its `next_due` still reads due [class: IMPLEMENTATION_REQUIRED]

(Recorded residual, bounded and owned elsewhere: the interaction between the audit consult and the
sibling state-durability plan's `loop_mode` enforcement is deliberately NOT tasked here. Under a future
`execution-only` directive the audit consult would still fire, though the audit rides the authoring lane
that such a directive closes; under `authoring-only` and `dual` it proceeds by the rules above. The
enforcement sentence is the sibling plan's creation, and coupling this plan's task to another plan's
future text would break task-coupling; the interaction clause belongs to whichever plan lands second.
This note is the tracked handoff for that one-clause follow-up.)
- [ ] Invariants bullet: amend "It schedules at most one child per lane per scheduler turn (one execution and one authoring at most)" to name the audit child on the authoring lane [class: IMPLEMENTATION_REQUIRED]
- [ ] Writer-classes list: note that audit dispatches record their children[] entries under the scheduler-turn class (no new writer class) [class: IMPLEMENTATION_REQUIRED]
- [ ] Revisions ledger entry covering the lane paragraph, the schema extension, and the lane-occupancy amendment [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN on the SKILL.md needles (lane span count 1, config rows, `"audit"` kind, `next_due`) [class: REPOSITORY_TEST]

### Task 3: Overlay audit recipe

Files:
- `agents/skills/maintenance/zcode.md`

- [ ] New overlay section titled `## Audit recipe`: db path and table shapes (tilde-form locator literals, never resolved absolute paths), log location and event schema, the persistence-noise filter, provider code meanings, watermark rules, the `next_due` write rule, and the script invocation with its digest-then-sample reading order [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN on the overlay recipe heading needle [class: REPOSITORY_TEST]

### Task 4: Bootstrap key documentation and Integration Points row

Files:
- `agents/skills/bootstrap-ai-playbook/SKILL.md`

- [ ] Document `friction_audit_dir` as an optional TOML key with fallback `.ai-playbook/friction-audit/` (same resolution pattern as `tmp_dir`); NOT added to the required-keys list (absence falls back, existing installs stay valid); the runtime directory is gitignored by the existing `/.ai-playbook/` rule [class: IMPLEMENTATION_REQUIRED]
- [ ] Integration Points consumer table: add the maintenance row (reads `friction_audit_dir` and `friction_audit_cadence_days` for the audit lane), so the bidirectional integration documentation holds [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN on the bootstrap key needle [class: REPOSITORY_TEST]

### Task 5: Step 5 precondition rephrase (idle-turn vacuity)

Files:
- `agents/skills/maintenance/SKILL.md`

- [ ] Rephrase the Step 5 ladder-precheck precondition to the dispatch-class-neutral form, containing the exact span `or the dispatch decision (for an idle-time dispatch)` exactly once in the Step 5 region: "Ladder precheck: after the quota leg (for a clocked dispatch) or the dispatch decision (for an idle-time dispatch), and before any ladder step, run the runtime overlay's ladder precheck for the lane"; keep the D3/`turn_error` consequence text unchanged [class: IMPLEMENTATION_REQUIRED]
- [ ] Revisions ledger entry naming the vacuity origin [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN on the region-scoped rephrase needle (exactly once in the Step 5 region) [class: REPOSITORY_TEST]

### Task 6: Pin vacuity fixes and audit-lane pins

Files:
- `scripts/check_maintenance_pins.sh`

- [ ] Replace the SKILL.md `ladder precheck` presence pin with the distinctive Step 5 needle ("Ladder precheck: after the quota leg (for a clocked dispatch)"); measured today: the phrase occurs 3 times in SKILL.md, so a presence pin aliases; the new needle matches only the operative precondition [class: REPOSITORY_TEST]
- [ ] Convert the stand-down-reason pins to per-occurrence counts: `grep -oF 'clocked-primitives-absent' "$Z" | wc -l` -eq 2 and the same for `idle-primitive-absent` (measured today: 2 occurrences each, both normative) [class: REPOSITORY_TEST]
- [ ] Add pins for the audit-lane paragraph using the same distinctive spans the Validation Commands use (the `when due and lanes allow, dispatch at most one audit child` count-1 span, the `friction_audit_cadence_days` row, the `execute|author|audit` kind literal, the `## Audit recipe` heading) and the region-scoped Step 5 rephrase count [class: REPOSITORY_TEST]
- [ ] Append the freeze-literal origin notes per the suite's protocol; simulate every changed/new pin's failure direction once against a mutated temp copy and record the flip-probe outcomes in the commit message body [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: `bash scripts/check_maintenance_pins.sh` exits 0 on the post-Task-1..5 tree [class: REPOSITORY_TEST]

### Task 7: Emission-suppression discipline and headless resume recipe

Files:
- `agents/skills/maintenance/zcode.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`

- [ ] zcode.md dispatch-discipline bullet: add the suppression witness and rule: when a read-only primitive listing repeats with a decided mutating call still unsent, do not attempt a third listing OR a narrated create; stand down via a Bash state write immediately, and name the launchd + headless-CLI recipe as the sanctioned resume-carrier fallback when a scheduled resume must survive the session [class: IMPLEMENTATION_REQUIRED]
- [ ] New launchd resume-carrier bullet in the overlay's dispatch-discipline region (created by this bullet, not referenced from existing text): the env-complete headless recipe exports `ZCODE_BUILTIN_PROVIDER_CONFIG_FILE` (and sibling provider-config vars) explicitly in the job script, with the 2026-09-20 instant-death witness (a hand-armed resume job died instantly on the missing provider config) [class: IMPLEMENTATION_REQUIRED]
- [ ] plans SKILL.md and execute-plan SKILL.md: add one sentence each near the budget gate's automation-first carrier references noting the suppression risk (a pause-boundary resume decided but not emitted must be carried by a state write, not narration) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN on the suppression and recipe needles [class: REPOSITORY_TEST]

### Task 8: Dedupe status-match fix and tests

Files:
- `scripts/docs_branch_backlog_dedupe.py`
- `scripts/test_docs_branch_backlog_dedupe.py`

- [ ] Change the comparison: remove the top-level twin only when normalized bodies match AND the top-level Status value equals the archived twin's Status; Status-only differences print an informational surface-and-keep line (not the mismatch warning) and keep both copies [class: IMPLEMENTATION_REQUIRED]
- [ ] Invert the existing `test_docs_branch_backlog_dedupe.py::test_removes_when_twin_differs_only_in_status_line` (it currently asserts REMOVED for a Status-only difference, the exact behavior this fix reverses): rename to `test_status_only_difference_keeps_both` and assert both copies exist plus the informational line [class: REPOSITORY_TEST]
- [ ] `test_docs_branch_backlog_dedupe.py#test_matching_status_removed`; given equal bodies and equal Status, expects removal (existing behavior preserved); run the full existing suite → expect GREEN with the new and inverted tests [class: REPOSITORY_TEST]

### Task 9: b2p2 origin closures

Files:
- `docs/history/backlog/2026-09-18-execute-plan-sidecar-boundary-sentence-dedup.md`
- `docs/history/backlog/2026-09-18-execute-plan-contract-requiredness-wording.md`
- `docs/history/backlog/2026-09-18-execute-plan-recurrence-relay-consumer-seam.md`

- [ ] Verify each item's problem statement is covered by the landed batch-2 phase-2 squash (`git show --stat 7334dd25` plus the commit body's per-item mapping); record the verification per item [class: IMPLEMENTATION_REQUIRED]
- [ ] Flip each item in place to `Status: closed (fixed by batch-2 phase-2)` and append a one-line pointer to the landed change [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN on the three closure needles [class: REPOSITORY_TEST]

### Task 10: Final validation

- [ ] Run → expect GREEN: full Validation Commands block, exit 0 [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: `python3 scripts/plan_readiness.py docs/plans/2026-09-21-scheduler-maintenance-loop-quality-hygiene.md` exits 0 [class: REPOSITORY_TEST]
- [ ] Commit: `feat: friction-audit lane, pin precision, emission discipline, dedupe status match, b2p2 closures` [class: REPOSITORY_TEST]
