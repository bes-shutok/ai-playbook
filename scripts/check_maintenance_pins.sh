#!/usr/bin/env bash
# Mechanical pins for the maintenance scheduler skill.
# Each pin guards an invariant the review loop or a manual edit could silently
# regress: guard structure, lane cap wording, dispatch-slice tag integrity,
# re-arm paragraph parity and escalation, the parent title's single creation
# source, the recognition span literal, section anchors other files navigate
# by, SKILL.md runtime-agnosticism, the pricing cache home, the schema-4 state
# contract, the state-durability loop_mode/pending_rearm contract, the pricing
# seed presence, and the budget-gate resume mirrors in
# the execute-plan and plans skills, and the discovery-ladder rung 1
# workflow_state bound (terminal-or-complete before a no-live-session closure).
# Exit 0 = all pins hold; exit 1 with
# PIN FAIL lines otherwise. Repo-relative paths only; run from anywhere.
set -u
fail=0
repo="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "not inside a git repo" >&2; exit 1; }
S="$repo/agents/skills/maintenance/SKILL.md"
Z="$repo/agents/skills/maintenance/zcode.md"
P="$repo/agents/skills/maintenance/prompt-templates.md"
D="$repo/agents/skills/done/SKILL.md"
E="$repo/agents/skills/execute-plan/SKILL.md"
for f in "$S" "$Z" "$P" "$D" "$E"; do
  [ -f "$f" ] || { echo "missing $f"; fail=1; }
done
[ "$fail" -eq 1 ] && exit 1

pin() { # pin <description> <command...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then
    return 0
  fi
  echo "PIN FAIL: $desc"
  fail=1
  return 1
}

expect_absent() { # expect_absent <description> <pattern> <file>: rc 0 = fail, rc >= 2 = grep error (fail), rc 1 = pass
  local desc="$1" pat="$2" f="$3" out rc
  out="$(grep -nF -- "$pat" "$f" 2>&1)"; rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "PIN FAIL: $desc"
    fail=1
  elif [ "$rc" -ge 2 ]; then
    echo "PIN FAIL: grep error on $f while checking absence: $out"
    fail=1
  fi
}

# Wrap-tolerant absence check (plan
# 2026-09-24-p57-per-execution-worktree-isolation.md, Task 5): a multi-word
# phrase can be line-wrapped in the target, so the line-oriented check above
# never matches it; newlines are flattened to spaces (repeats squeezed) before
# the fixed-string match. Same three-way polarity as expect_absent:
# rc 0 = forbidden match (fail), rc >= 2 = grep error (fail), rc 1 = pass.
expect_absent_flat() { # expect_absent_flat <description> <pattern> <file>
  local desc="$1" pat="$2" f="$3" out rc
  out="$(tr '\n' ' ' < "$f" | tr -s ' ' | grep -nF -- "$pat" 2>&1)"; rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "PIN FAIL: $desc"
    fail=1
  elif [ "$rc" -ge 2 ]; then
    echo "PIN FAIL: grep error on $f while checking flat absence: $out"
    fail=1
  fi
}

# --- deliberate freeze literals (review r1 RISK-4) ---
# The expect_absent pins below freeze exact prose in files whose owning plans
# are completed or frozen. A future legitimate edit that trips one of them is
# a wording change to a pinned span, not a suite bug; reconcile the pin and
# the text in the same edit and record the superseding origin. Freeze origins:
#   'spacing window, classify its prompt:' (SKILL.md): superseded by the P12
#       origin 1 repo-scoped widened arm (plan
#       2026-09-18-maintenance-loop-residuals-occupancy-anchors-rearm-wording, Task 1).
#   'when the automation listing shows no ENABLED parent' (SKILL.md):
#       superseded by the P12 origin 4 state-first Step 0 rewrite (same plan, Task 2).
#   'plus a path under the resolved `plans_dir` (SKILL.md Configuration;
#       default `docs/history/plans/`).' (zcode.md): superseded by the same P12
#       origin 1 containment extension of the execution-child marker.
#   'a rollback create refusal means the child create actually succeeded: ...'
#       (zcode.md) and 'counts as success only after one more listing confirms
#       an ENABLED automation with that title and prompt opening is present;
#       ...' (prompt-templates.md): pre-r4 unscoped spans extracted from git
#       history (a4ffa82f^) by the P12 origins 2-3 discriminating-guard task.
#   'sessions whose spawner automation has completed are not blocked'
#       (zcode.md): superseded by the 2026-09-16 linger-model correction.
#   'list once more immediately before the create' (prompt-templates.md):
#       superseded by the state-first re-arm duty (liveness plan, Task 3).
#   'when it is under 60 (the observed one-to-four-hour child run'
#       (zcode.md): superseded by the runtime-fit rule (plan
#       2026-09-19-scheduler-operations-discipline-quota-peaks-locks,
#       Task 1, P6 origin 1; the rule names the superseded 2026-09-15
#       60-minute fire-time horizon in its own lead-in).
#   'never inside a deferred window' (prompt-templates.md): superseded
#       fire-time sentence replaced by the blueprint-unique probe
#       --fire-at pin (code review r1 F8, plan
#       2026-09-19-scheduler-operations-discipline-quota-peaks-locks);
#       the deviation bullet's paraphrase of the pinned anchor is
#       deliberately not frozen (code review r2 F12 deferred half).
#   done-skill ordering pin (python block): freezes the pointer line
#       'Before Step 0, in a repository that resolves the maintenance skill'
#       above the Step 0 heading (liveness plan, Task 4; the line is
#       prescribed unchanged in its owning plan).
#   'Maintenance scheduler turn (every 2 hours)' (zcode.md recipe title):
#       superseded by the quota-aligned cadence plan
#       (docs/history/plans/2026-09-21-maintenance-turn-self-scheduling-cadence.md,
#       Task 1): the recognition title is form-independent, the cadence
#       parenthetical is deleted from the recipe, and the cadence pin is
#       rescoped to the never-dark fallback branch (exactly once).
#   the one-recorded-mutation carve-out pin spans (zcode.md: the anchor
#       'One-recorded-mutation carve-out' and the twelve obligation spans
#       pinned beside it; prompt-templates.md: "the overlay's
#       one-recorded-mutation carve-out" and "and this session owns that
#       record"): their superseding origin is plan
#       2026-09-21-loop-guard-one-recorded-mutation-carve-out (Tasks 1-2
#       landed the spans, Task 3 pins each at its count; a wording change to
#       any pinned span is a change to that plan's prescribed text, so
#       reconcile the pin and the text in the same edit and record the
#       superseding origin).
#   the toolset-precheck re-needle and the audit-lane pin spans (SKILL.md:
#       the Step 5 needle 'Ladder precheck: after the quota leg (for a
#       clocked dispatch)' replacing the aliasing generic 'ladder precheck'
#       presence pin, where the generic phrase stands 3 times in SKILL.md
#       and stays legal, only unpinned; 'when due and lanes allow, dispatch
#       at most one audit child' at exactly 1 whole-file; the
#       friction_audit_cadence_days row at exactly 1 in the Configuration
#       section and the execute|author|audit|retriage kind literal (the
#       four-kind form since the 2026-09-26 origin-class provenance plan's
#       additive retriage kind) at exactly 2 in
#       the State file section, both region-scoped because the Task 2
#       Revisions-ledger entry quotes both literals verbatim; the Step 5
#       region's 'or the dispatch decision (for an idle-time dispatch)' at
#       exactly 1; zcode.md: 'clocked-primitives-absent' and
#       'idle-primitive-absent' at exactly 2 each and the '## Audit recipe'
#       heading at exactly 1): their superseding origin is plan
#       2026-09-21-scheduler-maintenance-loop-quality-hygiene (Tasks 1-5
#       landed the spans, Task 6 pinned them, 2026-09-23; a wording change
#       to any pinned span is a change to that plan's prescribed text, so
#       reconcile the pin and the text in the same edit and record the
#       superseding origin).
#   Executed RED/GREEN evidence for these pins (scratch regressions, failing
#       pin lines, sweep rcs): plan
#       2026-09-18-maintenance-loop-residuals-occupancy-anchors-rearm-wording,
#       'Triage notes (execution)', entry 2026-09-19 (code review r2, TEST-R2-1).
# --- SKILL.md structure ---
pin "G1e guard present"      grep -qF 'G1e (execution lane)' "$S"
pin "G1a guard present"      grep -qF 'G1a (authoring lane)' "$S"
pin "per-lane cap wording"   grep -qF 'at most one child per lane per scheduler turn' "$S"
pin "idle-time floor exemption" grep -qF 'exempt from the 5-minute floor' "$S"
pin "pricing rule pointer"   grep -qF 'usage-pricing rule' "$S"
pin "state-file lane arm present" grep -qF 'State-file arm' "$S"
pin "idle children in the lane arm" grep -qF 'null `fire_at`' "$S"
pin "tripwire self-heal present" grep -qF 'Self-heal arm' "$S"
pin "tripwire span shape excludes the title conjunct" grep -qF "deliberately without that rule's title conjunct" "$S"
pin "widened-arm classification repo-scoped" grep -qF 'classify its prompt only when the prompt contains the resolved repository root' "$S"
pin "widened-arm outcomes scoped to contained prompts" grep -qF 'Among contained prompts:' "$S"
expect_absent "superseded unscoped widened-arm classification wording must be absent from SKILL.md" 'spacing window, classify its prompt:' "$S"
pin "failure-cap section anchored" grep -qF '## Failure detection and the failure cap' "$S"
pin "idle-time outcome arm present" grep -qF 'Idle-time children are covered too' "$S"
pin "pricing edits stay in the state cache" grep -qF 'never edits tracked skill files' "$S"
pin "state pricing_cache field named" grep -qF 'pricing_cache' "$S"
pin "step 6 carries forward externally written values" grep -qF 'carry forward the values whose authoritative writes may occur outside Step 6' "$S"
# review r1 F4 (state durability plan): the carry-forward enumeration must name
# the two state-durability fields; the opener pin above predates them, so a
# rewrite that drops the enumeration tail stays green without this membership pin
pin "carry-forward names the state-durability fields" grep -qF 'plus `loop_mode` and `pending_rearm`' "$S"
pin "starvation releases only the starved lane" grep -qF 'releases only the starved lane' "$S"
# 2026-09-25 parked-dependency visibility Task 6: the writer-class count moved
# from six to seven (the execute-plan serialization-boundary write joined as a
# new named class); the old literal is frozen absent so the count cannot
# silently revert
# 2026-09-26 P64 Task 2: the count moved again, from seven to eight (the
# cycle-gate write class joined); the seven literal joined the six literal in
# the frozen-absent set, and the Task 2 companion pins sit directly below so a
# single RED run witnesses the amended count pins and the new presence pins
# together (the suite's later exit checkpoints would otherwise cut the run
# short before they execute)
pin "eight sanctioned writer classes" grep -qF 'eight sanctioned writer classes' "$S"
for f in "$S" "$Z" "$P" "$D" "$E"; do expect_absent "superseded six sanctioned writer classes literal in $f" 'six sanctioned writer classes' "$f"; done
for f in "$S" "$Z" "$P" "$D" "$E"; do expect_absent "superseded seven sanctioned writer classes literal in $f" 'seven sanctioned writer classes' "$f"; done
# --- durable cycle gate pins (plan
# 2026-09-26-p64-execution-lane-liveness-long-session-continuity.md, Task 2) ---
# Presence pins are dedicated fixed-string greps that fail when their span is
# deleted: the resting JSON literal, the section anchor other files navigate
# by, and the eighth writer-class bullet in SKILL.md, plus the overlay's
# continuation-resume classification bullet and its field naming in zcode.md.
pin "authoring_cycle_gate resting JSON literal" grep -qF '"authoring_cycle_gate": null' "$S"
pin "cycle gate section anchored" grep -qF '## Cycle gate (durable pacing between cycles)' "$S"
pin "cycle-gate write class named" grep -qF 'cycle-gate write class' "$S"
pin "continuation-summary resume classification in zcode" grep -qF 'continuation-summary resume' "$Z"
pin "zcode overlay names the authoring_cycle_gate field" grep -qF 'authoring_cycle_gate' "$Z"
[ "$fail" -eq 1 ] && exit 1
pin "execution-child progress counts checked checkboxes" grep -qF 'checked-checkbox count' "$S"
# the corrected checkbox regex literal is pinned region-scoped to the failure-detection
# section in the python block below (a whole-file grep is satisfied by the Revisions-ledger copy)
pin "fast re-dispatch stop evidence" grep -qF 'timestamp older than one cadence period' "$S"
pin "enabled-only arms ignore lingered records" grep -qF 'lifecycleStatus` is completed or `enabled` is false' "$S"
pin "parent_absent_since needle" grep -qF 'parent_absent_since' "$S"
pin "darkness clock keeps the earliest value" grep -qF 'keeps the earliest value' "$S"
pin "step 0 keep-earliest phrasing" grep -qF 'keeping the earliest value' "$S"
pin "idle occupancy join mirrored in SKILL.md" grep -qF 'whose target carries the `(idle)` marker' "$S"
# merge landing lock group (plan 2026-09-20-merge-landing-lock-grouping): the
# G3b guard arm; the prompt-templates and overlay needles live in their own
# file sections below (count and body-scoped absence in the python block)
pin "G3b guard present"      grep -qF 'G3b (landing in flight)' "$S"
pin "pricing note read-back"  grep -qF 'note surfaces in the survey read-back' "$S"
# P37 (plan 2026-09-22-p37-context-budget-probes-and-runtime-state, Task 6):
# the State-file advisory note must name the merge lock among the joint-state
# safety sources, and the G3b final-slot effect span it already carries stays
# pinned (the wiring landed before the pin; the pin protects it).
pin "state-file note names the merge lock" grep -qF 'the done-lock, the merge lock, and claim checks' "$S"
pin "G3b final-slot effect named in the state-file note" grep -qF 'the `G3b` final-slot effect' "$S"
# --- state durability contract (scheduler/maintenance state durability plan, Task 6) ---
# The loop_mode and pending_rearm prose surfaces. The paragraph openers and the
# Step 3 enforcement spans below are unique-span whole-file greps (measured
# 2026-09-21: each occurs exactly once in SKILL.md; the Revisions-ledger
# entries paraphrase these spans and do not carry them). The schema literals,
# the Step 1 reader arm, and the Step 0 verifiable echo arm are pinned
# region-scoped in the python block below: the pending_rearm whole-file and
# Step 1-region counts are computed and asserted there (the suite computes
# both counts itself and asserts the invariant that matters, so no manual
# total is frozen in a comment), and verifiable echo
# also occurs in the self-heal arm's Revisions-ledger entry, so whole-file
# greps there would be satisfied by a stray copy.
pin "loop_mode field paragraph opener" grep -qF 'is the standing loop directive' "$S"
pin "authoring-only enforcement needle" grep -qF 'authoring-only resolves D1 and D4 to D3' "$S"
pin "execution-only enforcement needle" grep -qF 'execution-only resolves D2 to D3' "$S"
pin "pending_rearm field paragraph opener" grep -qF 'is the re-arm intent record' "$S"
# --- quota leg bindings (P6 origins 1-2; schema-4 fire-time bookkeeping) ---
pin "quota leg binds every clocked dispatch path" grep -qF 'binds every clocked child dispatch, from any session type' "$S"
pin "runtime-fit rule defers to reset regardless of pricing" grep -qF 'fire at reset_at_epoch instead, regardless of pricing' "$S"
pin "deferred-peak quota_status recorded" grep -qF 'quota_status: "deferred-peak"' "$S"
pin "probe-invocation bullet present" grep -qF 'Run `python3 scripts/quota_window_probe.py`' "$S"
pin "deferred slot fit-checked before pricing deferral" grep -qF 'before deferring for pricing, verify the deferred slot' "$S"
pin "starvation beats pricing never fit" grep -qF 'starvation beats pricing, never the runtime-fit rule' "$S"
# quota-aware authoring primitive selection (plan
# 2026-09-20-quota-aware-scheduling-semantics, Task 5): the D2 quota-signal
# decision input in SKILL.md and the authoring blueprint's stand-down gate
# span in prompt-templates.md (the acceptance countability; the plan's
# Validation block pins the sibling G6 spans author in-session, quota_signal,
# still plan-uncovered, and in-session authoring primitive)
pin "D2 quota-signal decision input" grep -qF "quota leg's probe report as a required decision input" "$S"
pin "authoring stand-down gate span" grep -qF 're-check the assigned backlog item is still plan-uncovered under the resolved plans directory' "$P"
python3 - "$S" <<'EOF' || fail=1  # r7 F1: propagate the block status; without this the block is fail-open at the exit-code surface
import json, re, sys
s = open(sys.argv[1]).read()
def need(text, anchor):
    if anchor not in text:
        print("PIN FAIL: missing anchor %s" % anchor); sys.exit(1)
order_ok = (lambda seq: all(s.find(a) != -1 and s.find(a) < s.find(b, s.find(a))
             for a, b in zip(seq, seq[1:])))
if not order_ok(["G1e (execution lane)", "G1a (authoring lane)", "G2 (failure cap)", "G3 (joint state)"]):
    print("PIN FAIL: guard order G1e<G1a<G2<G3"); sys.exit(1)
if not order_ok(["D1 (execute)", "D4 (propose park)", "D2 (author)", "D3 (no-op)"]):
    print("PIN FAIL: decision order D1<D4<D2<D3"); sys.exit(1)
if re.search(r'Cron(Create|List|Update|Delete)|OffPeak(Create|List)', s):
    print("PIN FAIL: SKILL.md names a runtime primitive (must stay runtime-agnostic)"); sys.exit(1)
need(s, "## State file")
m = re.search(r"```json\n(.*?)```", s.split("## State file", 1)[1].split("\n## ", 1)[0], re.S)
if not m:
    print("PIN FAIL: state schema json block missing"); sys.exit(1)
try:
    doc = json.loads(m.group(1))
except ValueError as exc:
    print("PIN FAIL: state schema json block does not parse: %s" % exc); sys.exit(1)
if doc.get("schema") != 4:
    print("PIN FAIL: state schema is not 4"); sys.exit(1)
lanes = {"execution", "authoring"}
if set(doc.get("decision", {})) != lanes or set(doc.get("decision_reason", {})) != lanes:
    print("PIN FAIL: per-lane decision/decision_reason keys drifted"); sys.exit(1)
pc = doc.get("pricing_cache", {})
if not {"last_verified", "source"} <= set(pc):
    print("PIN FAIL: pricing_cache fields drifted"); sys.exit(1)
if "rearm_note" not in doc:
    print("PIN FAIL: rearm_note missing from the state schema"); sys.exit(1)
if "parent_absent_since" not in doc or "pending_dispatch" not in doc:
    print("PIN FAIL: top-level parent_absent_since/pending_dispatch missing from the state schema"); sys.exit(1)
# state durability plan Tasks 1 and 4: the additive loop_mode and pending_rearm
# fields join the schema-4 block (checked against the parsed doc, so deleting
# either literal line, or breaking the block's JSON, fails here)
if "loop_mode" not in doc or "pending_rearm" not in doc:
    print("PIN FAIL: top-level loop_mode/pending_rearm missing from the state schema"); sys.exit(1)
child = (doc.get("children") or [{}])[0]
if not {"fire_at", "requested_at", "quota_status", "progress_mark", "resume_count"} <= set(child):
    print("PIN FAIL: children entry fields drifted"); sys.exit(1)
# P57 per-execution worktree isolation plan Task 1 (plan
# 2026-09-24-p57-per-execution-worktree-isolation.md): the additive per-run
# `worktree` field joins the children[] entry shape, null at rest (checked
# against the parsed doc, so deleting the literal line, or breaking the block's
# JSON, fails here); the schema stays 4 with no version bump (the assertion
# above is untouched and not duplicated)
if "worktree" not in child or child["worktree"] is not None:
    print("PIN FAIL: children entry lacks the additive worktree field (null at rest)"); sys.exit(1)
# scheduler ops lanes and durability plan Task 2: the decision-time quota
# record. Schema stays 4 (the assertion above is untouched and not duplicated);
# the key joins additively with its per-lane shape, and the Step 3 region must
# carry the record duty, the near-reset branch, and the fresh-window anchor.
qad = doc.get("quota_at_decision")
if not isinstance(qad, dict) or set(qad) != lanes:
    print("PIN FAIL: quota_at_decision missing or per-lane keys drifted"); sys.exit(1)
for lane in ("execution", "authoring"):
    if not {"status", "percent_used", "minutes_to_reset"} <= set(qad.get(lane) or {}):
        print("PIN FAIL: quota_at_decision %s shape drifted" % lane); sys.exit(1)
step3 = s.split("### Step 3: decision")[1].split("### Step 4")[0]
for needle in ("quota_at_decision",
               "D1 defers the execution dispatch past the reset and D2 defers the authoring dispatch",
               "must cite an explicit non-quota reason"):
    if needle not in step3:
        print("PIN FAIL: Step 3 lacks the quota decision needle %r" % needle); sys.exit(1)
need(s, "### Step 1: survey"); need(s, "### Step 2")
step1 = s.split("### Step 1: survey")[1].split("### Step 2")[0]
if "pending_dispatch" not in step1:
    print("PIN FAIL: pending_dispatch reader missing from the Step 1 list"); sys.exit(1)
# state durability plan Task 4: the pending_rearm reader arm, region-scoped to
# the Step 1 region (the counts are computed and asserted below, never frozen
# in a comment; a whole-file grep is satisfied by a stray copy, and deleting
# the Pending re-arm reader bullet empties the region and fails here)
if "pending_rearm" not in step1:
    print("PIN FAIL: pending_rearm reader arm missing from the Step 1 region"); sys.exit(1)
# review r3 F10: the suite self-measures the pending_rearm counts instead of
# restating brittle totals: both counts are computed here, and the invariant
# that matters is asserted; every in-region occurrence must sit inside the
# "- Pending re-arm:" bullet, so a future sentence elsewhere in the region that
# names the field cannot re-satisfy the token check above after the reader arm
# is deleted (the bare-token backlog item's vacuous-canary shape)
pr_total = s.count("pending_rearm")
pr_hits = [m.start() for m in re.finditer("pending_rearm", step1)]
pr_region = len(pr_hits)
b_at = step1.find("- Pending re-arm: when `pending_rearm` is set")
if b_at == -1:
    print("PIN FAIL: Step 1 lacks the Pending re-arm bullet anchor"); sys.exit(1)
b_start = step1.rfind("\n", 0, b_at) + 1
b_end = step1.find("\n", b_at)
if b_end == -1:
    b_end = len(step1)
pr_bullet = sum(1 for pos in pr_hits if b_start <= pos < b_end)
# superseded 2026-09-24, P54 plan Task 2 (plan
# 2026-09-24-p54-scheduler-loop-continuity-directives.md): the Step 1 region
# gained the park-discharge duty bullet after the Pending re-arm bullet, and
# that bullet legitimately names pending_rearm (the field it discharges), so
# occurrences inside the discharge bullet are allowed beside the reader bullet.
d_at = step1.find("- Parked-intent discharge (the park-discharge duty):")
d_start = step1.rfind("\n", 0, d_at) + 1 if d_at != -1 else -1
d_end = step1.find("\n", d_at) if d_at != -1 else -1
if d_end == -1:
    d_end = len(step1)
pr_discharge = sum(1 for pos in pr_hits if d_start <= pos < d_end)
if (pr_bullet + pr_discharge) != pr_region:
    print("PIN FAIL: %d of %d pending_rearm occurrence(s) in the Step 1 region sit outside the Pending re-arm and park-discharge bullets (whole-file count %d)" % (pr_region - pr_bullet - pr_discharge, pr_region, pr_total)); sys.exit(1)
# review r2 F7: the r1-added operative contracts pinned region-scoped (the
# Revisions-ledger prose paraphrases these spans, so whole-file greps would be
# vacuous): the loop-mode-held retention gate and the consume-semantics span
# in Step 1
if "loop-mode-held" not in step1:
    print("PIN FAIL: Step 1 lacks the loop-mode-held retention gate"); sys.exit(1)
if "never a precondition" not in step1:
    print("PIN FAIL: Step 1 lacks the pending_rearm consume-semantics span"); sys.exit(1)
# review r3 F12: the consume pin above keys on the generic phrase, so pin the
# crash-window span itself (deleting only the survival clause must fail)
if "only after the re-arm's state edit has survived" not in step1:
    print("PIN FAIL: Step 1 lacks the pending_rearm consume crash-window span"); sys.exit(1)
# review r4 F7: the three r3 Step 1 contracts (the reader refusal branch, the
# cannot-decide signal, and the label precedence), region-scoped to the Step 1
# region (the ledger paraphrases these contracts and carries none of the spans;
# region-scoping keeps the pin robust against future ledger prose; deleting any
# of the three sentences empties its span and fails here)
for needle in ("record the structured-first-line `rearm_note` under the reader-side token",
               "a set `pending_rearm` is itself a cannot-decide signal",
               "the short-circuit `loop-mode-held` reason wins when both holds coincide"):
    if needle not in step1:
        print("PIN FAIL: Step 1 lacks the r3 Step 1 contract span %r" % needle); sys.exit(1)
# review r2 F7: the loop-mode-held retention clause's operative sub-span;
# moved from the Step 1 region to the Step 3 region by the
# deferred-residual-dispositions plan Task 9 (T4 named the exclusion at the
# Step 3 enforcement sentence and reduced the Step 1 clauses to references, so
# the clause still carrying the retention wording verbatim lives in Step 3; the
# Step 1 bare-token pin above stays green on the referencing clauses)
if "is retained in `pending_dispatch` with reason `loop-mode-held`" not in step3:
    print("PIN FAIL: Step 3 lacks the loop-mode-held retention clause span"); sys.exit(1)
# review r3 F12: the writer-classes closedness membership clauses, pinned per
# class line (each sanctioned class is one bullet line), so dropping a member
# from its class line fails where the whole-file topic greps stay green
def class_line(prefix):
    for line in s.split("\n"):
        if line.startswith(prefix):
            return line
    return ""
sched_turn_class = class_line("  - Scheduler turns, whose write modes are")
child_first_class = class_line("  - A child's re-arm FIRST ACTION")
if not sched_turn_class or "the `loop_mode` write/replace" not in sched_turn_class:
    print("PIN FAIL: scheduler-turn writer class lacks the loop_mode write/replace membership"); sys.exit(1)
if not child_first_class or "the `pending_rearm` park write" not in child_first_class:
    print("PIN FAIL: child FIRST ACTION writer class lacks the pending_rearm park write membership"); sys.exit(1)
# review r5 F2: the three remaining writer-class membership clauses, pinned per
# class line like the two above, so the closed writer-classes list cannot drop
# a member and stay green (the watchdog class line carries the landed "and
# clears `pending_rearm`" wording; "and `pending_rearm`" is the zcode.md
# watchdog bullet's span, already pinned in the later block)
successor_class = class_line("  - A completing execution child's successor-dispatch")
watchdog_class = class_line("  - The idle-time watchdog")
rot_class = class_line("  - Rearm-on-touch sessions")
if not successor_class or "the both-legs-fail `pending_dispatch` park write" not in successor_class:
    print("PIN FAIL: successor-dispatch writer class lacks the both-legs-fail pending_dispatch park write membership"); sys.exit(1)
if not watchdog_class or "and clears `pending_rearm` in that same recovery edit" not in watchdog_class:
    print("PIN FAIL: watchdog writer class lacks the pending_rearm recovery clear membership"); sys.exit(1)
if not rot_class or "the `loop_mode` write/replace" not in rot_class:
    print("PIN FAIL: rearm-on-touch writer class lacks the loop_mode write/replace membership"); sys.exit(1)
# loop liveness durable carriers and park coverage plan: the watchdog
# escalation park coverage hole (state-durability review r1 F11). Writer-side
# needles, region-scoped per class line and per field paragraph line so the
# closed enumerations cannot drop the watchdog and stay green; the class-line
# membership reuses the watchdog_class extraction of the r5 F2 block above.
if not watchdog_class or "parks `pending_rearm` with its paired payload copy" not in watchdog_class:
    print("PIN FAIL: watchdog writer class lacks the escalation park write membership"); sys.exit(1)
pr_line = ""
for line in s.split("\n"):
    if line.startswith("`pending_rearm` is the re-arm intent record"):
        pr_line = line
        break
if not pr_line or "and the idle-time watchdog escalation (a refused re-arm" not in pr_line:
    print("PIN FAIL: pending_rearm paragraph lacks the watchdog escalation writer"); sys.exit(1)
# placement pin (review r1 T2): state-first ordering inside the Step 0
# rearm-on-touch bullet; the consult anchor and the listing-gate anchor are
# both fail-closed so a reworded bullet cannot pass vacuously, and the order
# assertion catches a listing-first regression that keeps the positive needle
step0 = s.split("### Step 0: context load")[1].split("### Step 1: survey")[0]
a_consult = "rearm-on-touch check: consult the scheduler state file first"
a_gate = "run the automation listing only when the state file cannot decide"
if a_consult not in step0 or a_gate not in step0:
    print("PIN FAIL: step 0 state-first placement anchors missing"); sys.exit(1)
if step0.index(a_gate) < step0.index(a_consult):
    print("PIN FAIL: step 0 must consult the state file before the listing (state-first placement)"); sys.exit(1)
# review r1 C1: the turn-start duty bullet's Step 0 placement precedes the
# rearm-on-touch bullet (the duty runs before the survey and supersedes the
# check's re-arm leg for the turn itself, so it must lead); both anchors are
# fail-closed and the comparison catches a reordered Step 0 that keeps both
# positive spans intact
a_turnstart = "turn-start carrier re-arm: run the runtime overlay's Turn-start carrier re-arm duty before the survey"
if a_turnstart not in step0 or a_consult not in step0:
    print("PIN FAIL: step 0 duty-before-touch placement anchors missing"); sys.exit(1)
if step0.index(a_turnstart) > step0.index(a_consult):
    print("PIN FAIL: step 0 turn-start duty bullet must precede the rearm-on-touch bullet (placement)"); sys.exit(1)
# state durability plan Task 2: the mode-appendix self-heal arm's verifiable
# echo contract, region-scoped to the Step 0 region (the arm's Revisions-ledger
# entry repeats the span, so a whole-file grep is satisfied by the ledger copy;
# deleting the self-heal arm sentence empties the region and fails here).
# Review r1 F17: the needle is the distinctive span, which the fallback
# sentence's "non-verifiable echo" does not contain, so deleting only the
# landed-gate sentence while keeping the fallback wording fails too
if "only on a verifiable echo" not in step0:
    print("PIN FAIL: step 0 self-heal lacks the verifiable echo arm"); sys.exit(1)
# review r2 F7: the self-heal attempt-bound span, region-scoped to the Step 0
# region (the writer-classes line paraphrases it, so a whole-file grep would be
# satisfied by a stray copy; deleting the attempt-bound sentence empties the
# region and fails here)
if "suppresses the repair for that touch" not in step0:
    print("PIN FAIL: step 0 lacks the self-heal attempt-bound span"); sys.exit(1)
# review r3 F12: the loop_mode removal leg's intended-form span, region-scoped
# to the Step 0 region (the Revisions ledger paraphrases it)
if "carrying no mode appendix" not in step0:
    print("PIN FAIL: step 0 lacks the loop_mode removal leg span"); sys.exit(1)
# review r5 F2: the removal trigger's mode-value phrasing (the landed r4
# wording), region-scoped to the Step 0 region (the Revisions ledger
# paraphrases it; deleting the removal-trigger sentence empties the span)
if "mode value is `dual` or null (the withdrawn field's cleared trace, whose mode is null, included)" not in step0:
    print("PIN FAIL: step 0 lacks the removal-trigger mode-value span"); sys.exit(1)
# review r2 F7: the loop_mode withdrawal arm span, region-scoped to the
# loop_mode field paragraph in the State file section ('is withdrawn' also
# occurs in the writer-classes line and the Revisions ledger, so a whole-file
# grep would be satisfied by a stray copy)
state_region = s.split("## State file", 1)[1].split("\n## ", 1)[0]
lp_at = state_region.find("`loop_mode` is the standing loop directive")
if lp_at == -1:
    print("PIN FAIL: loop_mode field paragraph missing from the State file section"); sys.exit(1)
loop_mode_para = state_region[lp_at:state_region.find("\n\n`", lp_at)]
if "is withdrawn" not in loop_mode_para:
    print("PIN FAIL: loop_mode field paragraph lacks the withdrawal arm span"); sys.exit(1)
# review r5 F2: the withdrawal trace's cleared_at key, region-scoped to the
# loop_mode field paragraph (the Step 0 freshness test reads it; the Step 0
# cannot-decide clause and the Revisions ledger also name it, so a whole-file
# grep would be satisfied by a stray copy)
if "cleared_at" not in loop_mode_para:
    print("PIN FAIL: loop_mode field paragraph lacks the cleared_at trace"); sys.exit(1)
# review r4 F1: the identity-bound derivation's home literal is pinned
# region-scoped to the pending_rearm field paragraph (the paragraph owns the
# derivation; deleting the derivation clause fails here), and the superseded
# bare date-only payload path stays absent from every operative SKILL.md
# surface (the cut before the Revisions ledger excludes the ledger's
# historical copies)
pr_at = state_region.find("`pending_rearm` is the re-arm intent record")
if pr_at == -1:
    print("PIN FAIL: pending_rearm field paragraph missing from the State file section"); sys.exit(1)
pending_rearm_para = state_region[pr_at:state_region.find("\n\n`", pr_at)]
if "docs/tmp/future-plan-prompts-<date>-rearm.md" not in pending_rearm_para:
    print("PIN FAIL: pending_rearm paragraph lacks the rearm-kind derivation literal"); sys.exit(1)
# review r5 F2: the dispatch kind's derivation literal, pinned region-scoped to
# the same owning paragraph (the r4 F1 pin above guards the rearm kind only,
# so deleting the dispatch-kind form stayed green)
if "docs/tmp/future-plan-prompts-<date>-dispatch-<target-basename>.md" not in pending_rearm_para:
    print("PIN FAIL: pending_rearm paragraph lacks the dispatch-kind derivation literal"); sys.exit(1)
operative = s.split("## Revisions", 1)[0]
if "docs/tmp/future-plan-prompts-<date>.md" in operative:
    print("PIN FAIL: superseded bare date-only payload path still in an operative SKILL.md surface"); sys.exit(1)
need(s, "G1e (execution lane)"); need(s, "Duplicate-parent tripwire")
arms = s.split("G1e (execution lane)")[1].split("Duplicate-parent tripwire")[0]
if "certification oracle" not in arms:
    print("PIN FAIL: lane-arm release rules missing the certification oracle needle"); sys.exit(1)
# placement pin (review r4 RISK-1): inside the G1e region the classification
# outcomes lead-in ("Among contained prompts: ...") must sit after the
# containment gate sentence; both anchors are fail-closed so a deleted scope
# marker or an outcomes-grafted-above-the-gate regression cannot pass vacuously
a_gate = "classify its prompt only when the prompt contains the resolved repository root"
a_scope = "Among contained prompts:"
need(s, a_gate); need(s, a_scope)
if a_gate not in arms or a_scope not in arms:
    print("PIN FAIL: widened-arm containment anchors missing from the G1e region"); sys.exit(1)
if arms.index(a_gate) > arms.index(a_scope):
    print("PIN FAIL: widened-arm outcomes must follow the containment gate (placement)"); sys.exit(1)
need(s, "## Failure detection and the failure cap")
failure_region = s.split("## Failure detection and the failure cap", 1)[1].split("\n## ", 1)[0]
if "\\[[xX]\\]" not in failure_region:
    print("PIN FAIL: corrected checkbox regex literal missing from the failure-detection region"); sys.exit(1)
# authoring claim file surfaces (scheduler ops lanes and durability plan,
# Task 1): the claim reading is the G1a guard's own discovery arm, so pin it
# region-scoped to the G1a region (a stray authoring-claims mention elsewhere
# in SKILL.md must not satisfy it vacuously)
g1a_region = s.split("G1a (authoring lane)")[1].split("Duplicate-parent tripwire")[0]
if "authoring-claims" not in g1a_region:
    print("PIN FAIL: G1a discovery arm missing the authoring-claims claim reading"); sys.exit(1)
EOF
rc=$?
[ "$rc" -ne 0 ] && fail=1
[ "$fail" -eq 1 ] && exit 1

# --- zcode.md anchors and single creation source ---
pin "recipe section anchored"    grep -qF '## Recurring automation recipe' "$Z"
pin "ladder section anchored"    grep -qF '## Child dispatch ladder' "$Z"
pin "quota section anchored"     grep -qF '## Quota leg' "$Z"
pin "model policy section anchored" grep -qF '## Child model and effort policy' "$Z"
pin "parent title in recipe"     grep -qF 'Title: `Maintenance scheduler turn`' "$Z"
# quota-aligned cadence plan Task 1: the old cadence-pinned title literal is
# frozen absent (superseding origin recorded in the freeze block above)
expect_absent "superseded cadence-pinned title literal must be absent from zcode.md" 'Maintenance scheduler turn (every 2 hours)' "$Z"
pin "recognition span full literal in recipe" grep -qF 'You are the maintenance scheduler for the repository at {REPO_ROOT}' "$Z"
pin "pricing seed present"       grep -qF 'pricing_last_verified' "$Z"
pin "ladder rollback present"    grep -qF 'Rollback: if the child create then fails' "$Z"
pin "watchdog backstop present"  grep -qF 'Watchdog backstop' "$Z"
pin "fallback cadence pinned (never-dark fallback branch, exactly once)" grep -qF '15 */2 * * *' "$Z"
pin "peak window UTC+8 anchor"   grep -qF '14:00-18:00 UTC+8' "$Z"
pin "never pin local hours"      grep -qF 'never pin local hours' "$Z"
pin "execution-child marker repo containment" grep -qF 'and the resolved repository root (the relative plans-dir substring alone' "$Z"
expect_absent "superseded uncontained execution-child marker wording must be absent from zcode.md" 'plus a path under the resolved `plans_dir` (SKILL.md Configuration; default `docs/history/plans/`).' "$Z"
pin "zcode tripwire shape excludes the title conjunct" grep -qF 'title conjunct is deliberately not required' "$Z"
# scheduler ops lanes and durability plan Task 4 (2026-09-19): the recycling
# update call is demoted to a verified-only optimization leg, so the old
# 'ladder recycling needle' literal (the update-as-primary step 2 sentence)
# and the old 'hand-off proceed refusal bound' literal (the update-refusal
# convergence sentence "converges to the fallback's fresh-id create within
# the same dispatch attempt") both died with the recycling primary path.
# The refusal-bound pin is REWRITTEN, not dropped: the successor sentence
# below carries the same semantics on the operative path (a create refusal
# routes to the next mutating call, the lingered-record delete, instead of
# stranding the dispatch). Both dead literals are frozen absent.
pin "ladder operative delete-plus-create needle" grep -qF 'delete-plus-create is the operative path' "$Z"
pin "recycling update is a verified-only optimization leg" grep -qF 'may replace the delete-plus-create above only when a live-verified parent-to-child flip is recorded' "$Z"
pin "hand-off proceed refusal bound (operative path)" grep -qF 'deleting your own lingered completed spawner record first when the create is refused for the automation-born cap' "$Z"
expect_absent "demoted update-as-primary recycling wording must be absent from zcode.md" 'update the recorded parent record into the child one-shot' "$Z"
expect_absent "superseded update-refusal convergence sentence must be absent from zcode.md" "converges to the fallback's fresh-id create within the same dispatch attempt" "$Z"
pin "verification section anchored" grep -qF '## Automation primitive verification' "$Z"
pin "linger-deletion needle"     grep -qF 'deleting your own lingered' "$Z"
pin "ambiguous-outcome carve-out kept" grep -qF 'treat the child as dispatched' "$Z"
expect_absent "superseded unscoped ambiguous-outcome carve-out must be absent from zcode.md" 'a rollback create refusal means the child create actually succeeded: skip the retries, the `parent-restore-failed` record, and the memory note, treat the child as dispatched, and stop' "$Z"
pin "idle attribution per-session" grep -qF ' sessionId matches the current session' "$Z"
pin "pricing clear-on-success"   grep -qF 'clears the pricing-verification-failed note' "$Z"
expect_absent "superseded completed-spawner claim must be absent from zcode.md" 'sessions whose spawner automation has completed are not blocked' "$Z"
pin "ladder clocked create runs the quota check first" grep -qF 'runs the peak-window and runtime-fit check first' "$Z"
pin "runtime-fit probe invocation shape" grep -qF -- '--fire-at <iso> --need-minutes' "$Z"
pin "--fire-at mode contract present" grep -qF -- '--fire-at <iso> [--need-minutes <N>]' "$Z"
pin "straddle rule bound in the off-peak preference" grep -qF -- '--straddle-minutes 60' "$Z"
# Review r1 F7: zcode.md carries a CAPITALIZED copy of the fit-before-pricing
# sentence (the SKILL.md pin's lowercase needle cannot match it), so deleting
# the operative zcode copy stayed green; pin it separately.
pin "fit-before-pricing rule bound (zcode copy)" grep -qF 'Before deferring for pricing, verify the deferred slot' "$Z"
expect_absent "superseded 60-minute horizon bullet must be absent from zcode.md" 'when it is under 60 (the observed one-to-four-hour child run' "$Z"
# merge landing lock group: the overlay must name the merge lock family
pin "overlay names the merge lock acquire command" grep -qF 'merge-acquire' "$Z"
# state durability plan Tasks 2 and 4: the recipe's mode-appendix clause and
# the Cron-tool boundary's reduced-toolset inheritance note (unique-span
# whole-file greps; measured 2026-09-21: each occurs exactly once in zcode.md)
pin "recipe mode appendix clause" grep -qF 'mode appendix sourced from state' "$Z"
# review r1 F8: the existence pin above guards presence only, so a content
# needle for the clause's directive-wording span (unique in zcode.md) pins the
# determinate appendix shape the Step 0 detection predicate reads; the needle
# moved with the span in the deferred-residual-dispositions plan Task 9 (T2
# reworded the span to defer to the pinned literal, which names the lane the
# mode keeps, and pinned the trim-plus-single-line normalization)
pin "recipe mode appendix content (directive wording span)" grep -qF "in the pinned canonical form below, which names the lane the mode keeps" "$Z"
pin "recipe mode appendix pins the directive normalization" grep -qF "the field's directive wording, trimmed and collapsed to a single line" "$Z"
# review r2 F6: the recipe pins the appendix's canonical template literal, so
# every renderer class builds one form and SKILL.md's detection predicate diffs
# against it (unique literal in zcode.md)
pin "recipe mode appendix canonical template literal" grep -qF 'Mode directive: <directive> (<mode> lane only.)' "$Z"
# review r1 F15: re-needled from the generic topic phrase 'reduced toolset' to
# the operative precheck-routing fragment, which a partial edit cannot satisfy
# by leaving the phrase behind (unique in zcode.md)
pin "reduced toolset precheck routing duty" grep -qF 'payload duties precheck before leg selection' "$Z"
# review r2 F7: the Re-arm hygiene Loop guard's suppressed-re-arm park write
# (the SKILL.md rearm-on-touch writer class names it; unique span in zcode.md).
# Review r3 F1: the span now carries the derivation reference (the field
# paragraph owns the filename), replacing the bare date-only path; the pin
# moved with the wording in the same edit.
pin "loop guard park-write span" grep -qF "write \`pending_rearm\` plus the assembled parent payload copy under the identity-bound payload filename derived per the \`pending_rearm\` field paragraph (the rearm kind) in that same targeted state edit" "$Z"

# --- one-recorded-mutation carve-out pins (plan
# 2026-09-21-loop-guard-one-recorded-mutation-carve-out, Task 3) ---
# Count-gated pins for the overlay's carve-out obligations (the Task 1 spans
# of the same plan). Each span below is unique-span whole-file (measured on
# the post-Task-1 tree: each occurs exactly once in zcode.md), so a count of
# exactly 1 fails both a deletion of that obligation and a stray duplicate
# copy. The escalation-note recovery duty and the single-call decision-write
# mandate live in the re-arm hygiene paragraph (the recipe section); the
# other eleven spans live in the dispatch-discipline bullet.
[ "$(grep -oF 'One-recorded-mutation carve-out' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: carve-out anchor count"; fail=1; }
[ "$(grep -oF 'exactly ONE mutating call implementing that recorded decision' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: single-call bound count"; fail=1; }
[ "$(grep -oF 'never curtails an advancing dispatch' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: advancing-dispatch scoping count"; fail=1; }
[ "$(grep -oF 'The bound counts decided mutations, not primitive calls' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: bound unit clause count"; fail=1; }
# bound unit-clause parenthetical count (dfm loop-guard successor)
[ "$(grep -oF "a parent re-arm's shape is per the recipe's operative shape (delete-plus-create today; the recycling leg only if a verified flip reopens it)" "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: bound unit-clause parenthetical count"; fail=1; }
[ "$(grep -oF 'any refusal after that single call takes the existing escalation paths' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: escalation-routing count"; fail=1; }
[ "$(grep -oF "must stop touching automation primitives immediately after it regardless of the call's outcome" "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: stop-bound tail count"; fail=1; }
[ "$(grep -oF "the loop's signature appeared (two listings, no mutating step between them)" "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: guard-signature restatement count"; fail=1; }
[ "$(grep -oF 'a state-first write that preceded the first listing' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: state-first gate count"; fail=1; }
[ "$(grep -oF 'a decision recorded only in chat narration does not qualify' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: narration-exclusion count"; fail=1; }
[ "$(grep -oF 'or the pending record it takes as its own' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: decision-ownership count"; fail=1; }
[ "$(grep -oF 'an explicit user instruction to proceed outranks them' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: operator-override count"; fail=1; }
[ "$(grep -oF 'records its decided re-arm in the state file before its first primitive call' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: single-call decision-write mandate count"; fail=1; }
[ "$(grep -oF 'must name the mechanical recovery' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: escalation-note recovery duty count"; fail=1; }
[ "$fail" -eq 1 ] && exit 1

# --- quota-aligned cadence pins (plan 2026-09-21-maintenance-turn-self-scheduling-cadence, Task 1) ---
# Count-gated pins for the overlay's cadence rule and Turn-start carrier re-arm
# duty. Each span below is unique-span whole-file (measured on the post-Task-1
# tree: each occurs exactly once in zcode.md), so a count of exactly 1 fails
# both a deletion and a stray duplicate copy; the fallback cadence literal is
# rescoped here to exactly once (the never-dark fallback branch is its only
# legal home after the fixed cadence was superseded).
python3 - "$Z" <<'EOF' || fail=1  # r7 F1: propagate the block status; without this the block is fail-open at the exit-code surface
import sys
z = open(sys.argv[1]).read()
def one(span):
    n = z.count(span)
    if n != 1:
        print("PIN FAIL: cadence span count %d != 1 in zcode.md: %s" % (n, span)); sys.exit(1)
one("Loop carrier: the armed automation that fires scheduler turns")
one("the carrier is a one-shot carrying this recipe's title and prompt template")
one("reset_at_epoch plus 10 minutes")
one("no arming path may end with the loop dark")
one("attempt the recurring fallback create per the recipe before escalating")
one("Turn-start carrier re-arm duty")
one("the same state-first re-arm duty the child blueprints carry as their FIRST ACTION")
one("before any survey or dispatch step")
one("or the live recurring fallback record this session spawned from")
one("unless it is the carrier this session's turn-start duty armed this turn")
one("re-arms the carrier per the recipe's cadence rule")
one("15 */2 * * *")
# review r1 C1: the duty-before-survey placement is pinned positionally, not just
# by span counts: the duty bullet must sit before the overlay's first Step 1
# survey reference. Both anchors fail closed (the count pins above hold the duty
# anchor at exactly one; a stripped survey reference fails the membership check),
# so a moved or reworded bullet cannot pass vacuously
if "Turn-start carrier re-arm duty" not in z or "Step 1 survey" not in z:
    print("PIN FAIL: duty-before-survey placement anchors missing from zcode.md"); sys.exit(1)
if z.index("Turn-start carrier re-arm duty") > z.index("Step 1 survey"):
    print("PIN FAIL: turn-start duty bullet must precede the Step 1 survey reference in zcode.md"); sys.exit(1)
EOF
rc=$?
[ "$rc" -ne 0 ] && fail=1
[ "$fail" -eq 1 ] && exit 1

# --- quota-aligned cadence blueprint pins (plan
# 2026-09-21-maintenance-turn-self-scheduling-cadence, Task 2) ---
# Count-gated pins for the cadence-rule spans the Task 2 edits landed inside
# both byte-identical FIRST ACTION re-arm paragraphs. Each span below occurs
# exactly twice in prompt-templates.md (once per blueprint paragraph; the
# deviation-list entries paraphrase and must not carry the spans, or these
# counts drift), so a count of exactly 2 fails both a deletion and a stray
# duplicate copy; the blueprint integrity block's byte-identity parity pin
# covers the two paragraphs' byte equality, so exact-literal count 2 plus that
# parity is the byte-parity guarantee per span. Freeze origins (the superseded
# literals these gates replaced; both stood exactly twice before Task 2 and
# must not return): '(its title, its cadence cron, recurring true, enabled
# true, its prompt template with {REPO_ROOT} filled)' (the full form
# parenthetical in step (1) of each paragraph) and 'then update
# "parent_automation_id" as a targeted field edit' (the step (3) closing) are
# superseded by Task 2 of plan
# 2026-09-21-maintenance-turn-self-scheduling-cadence; review r1 flagged that
# freeze as claimed but unenforced, and the two expect_absent pins after this
# block enforce it.
python3 - "$P" <<'EOF' || fail=1  # r7 F1: propagate the block status; without this the block is fail-open at the exit-code surface
import sys
p = open(sys.argv[1]).read()
def two(span):
    n = p.count(span)
    if n != 2:
        print("PIN FAIL: blueprint cadence span count %d != 2 in prompt-templates.md: %s" % (n, span)); sys.exit(1)
two("in the form the recipe's cadence rule selects")
two('record the armed carrier\'s fire time into "next_turn_at"')
EOF
rc=$?
[ "$rc" -ne 0 ] && fail=1
[ "$fail" -eq 1 ] && exit 1
# review r1 C2: enforcement pins for the Task 2 freeze literals recorded in the
# comment block above (both stood exactly twice before Task 2 and must not
# return; the superseding origin is Task 2 of plan
# 2026-09-21-maintenance-turn-self-scheduling-cadence). Fixed-string greps, so
# the pin fires only on the verbatim superseded prose returning in any copy.
expect_absent "superseded fixed-form blueprint parenthetical must be absent from prompt-templates.md" '(its title, its cadence cron, recurring true, enabled true, its prompt template with {REPO_ROOT} filled)' "$P"
expect_absent "superseded parent_automation_id-only re-arm closing must be absent from prompt-templates.md" 'then update "parent_automation_id" as a targeted field edit' "$P"
[ "$fail" -eq 1 ] && exit 1

# --- quota-aligned cadence SKILL.md pins (plan
# 2026-09-21-maintenance-turn-self-scheduling-cadence, Task 3) ---
# Count-gated pins for the SKILL.md wiring of the cadence rule: the Step 0
# turn-start carrier re-arm duty bullet, the next_turn_at schema line, the
# human-check armed-chain exemption clause, the parent_automation_id carrier
# wording, and the Revisions ledger entry. Each span below occurs exactly once
# in SKILL.md (measured on the post-Task-3 tree), so a count of exactly 1
# fails both a deletion and a stray duplicate copy; the ledger span is
# count-gated so a future ledger entry naming the plan again cannot
# re-satisfy a presence-only grep. Freeze origins (the superseded literals
# these gates replaced; none may return):
#   'the recurring parent automation's id' (the parent_automation_id
#       definitional head; exactly one occurrence before Task 3):
#       superseded by the carrier wording (the chained one-shot or the
#       recurring fallback record; the form is the cadence rule's) of plan
#       2026-09-21-maintenance-turn-self-scheduling-cadence, Task 3.
expect_absent "superseded recurring-parent definitional wording must be absent from SKILL.md" "the recurring parent automation's id" "$S"
python3 - "$S" <<'EOF' || fail=1  # r7 F1: propagate the block status; without this the block is fail-open at the exit-code surface
import sys
s = open(sys.argv[1]).read()
def one(span):
    n = s.count(span)
    if n != 1:
        print("PIN FAIL: cadence SKILL.md span count %d != 1: %s" % (n, span)); sys.exit(1)
one("the runtime overlay's Turn-start carrier re-arm duty")
one('"next_turn_at": null,')
one("in the future and the recorded `parent_automation_id` is ENABLED")
one("the loop carrier automation's id")
one("maintenance-turn-self-scheduling-cadence")
EOF
rc=$?
[ "$rc" -ne 0 ] && fail=1
[ "$fail" -eq 1 ] && exit 1

# --- prompt-templates.md child-duty needles (state-driven rearm, successor dispatch, resume) ---
pin "state-first rearm duty" grep -qF 'state-first, without listing first' "$P"
pin "rearm anti-loop guard" grep -qF 'listed twice without a mutating step' "$P"
pin "successor carve-out in the opening guard" grep -qF 'beyond the re-arm duty below and the single successor-dispatch duty below' "$P"
pin "successor fallback delete-plus-create" grep -qF 'fall back to deleting your own spawner record whatever its current form' "$P"
pin "successor both-legs-fail re-create" grep -qF 'when both legs fail' "$P"
pin "successor adopt matcher repo containment" grep -qF 'whose prompt also contains the resolved repository root is present, adopt its id into "parent_automation_id" (targeted field edit) and end without creating' "$P"
pin "resume rule in the execution payload" grep -qF 'this is a resume run' "$P"
pin "rearm lingered-record deletion in blueprints" grep -qF 'deleting your own lingered' "$P"
pin "success-via-existing confirmation" grep -qF 'counts as success only after one more listing confirms' "$P"
pin "successor fire time names the full quota leg" grep -qF 'runtime-fit, deferred-window, peak-pricing, and floor rules' "$P"
pin "successor entry records requested_at" grep -qF 'requested_at carrying the originally requested fire time' "$P"
# scheduler ops lanes and durability plan Task 4: the durable HOST CAVEAT.
# The re-arm caveat span sits inside the byte-identical FIRST ACTION
# paragraphs; the plain grep here is a presence canary only (satisfiable by
# a single occurrence), and the python parity block below pins the count
# exactly (2 for the re-arm span, one per blueprint paragraph; 1 for the
# successor reshape leg; the deviation-list entries paraphrase and must not
# carry the spans, or those counts drift).
pin "blueprint re-arm HOST CAVEAT present" grep -qF 'HOST CAVEAT: any recycling update whose echoed record is not verifiably the intended form' "$P"
pin "successor reshape-leg HOST CAVEAT present" grep -qF 'HOST CAVEAT: any recycling update whose echoed record is not verifiably the intended form (enabled true, recurring false, a future nextRunAt matching the successor fire time, confirmed by a listing) is treated as a refusal' "$P"
# Review r1 F8: the 'runtime-fit, deferred-window, ...' needle above occurs
# TWICE in prompt-templates.md (blueprint + deviation paraphrase), so
# reverting only the blueprint's --fire-at sentence stayed green; pin the
# blueprint-unique span too, and keep the superseded fire-time span absent.
pin "successor blueprint names the probe --fire-at mode" grep -qF 'using its --fire-at mode with --need-minutes set to this lane' "$P"
expect_absent "superseded fire-time sentence must be absent from prompt-templates.md" 'never inside a deferred window' "$P"
expect_absent "superseded unscoped success-via-existing clause must be absent from prompt-templates.md" 'counts as success only after one more listing confirms an ENABLED automation with that title and prompt opening is present; on that success-via-existing path' "$P"
expect_absent "superseded listing-driven rearm wording must be absent from prompt-templates.md" 'list once more immediately before the create' "$P"

# --- blueprint carve-out reference parity pins (plan
# 2026-09-21-loop-guard-one-recorded-mutation-carve-out, Task 3) ---
# Count-gated pins for the carve-out reference sentence Task 2 of the same
# plan landed inside both byte-identical FIRST ACTION re-arm paragraphs. Each
# span below occurs exactly twice in prompt-templates.md (once per paragraph;
# the deviation-list entries paraphrase and must not carry the spans, or
# these counts drift), so a count of exactly 2 fails a deletion in either
# paragraph and a stray duplicate copy; combined with the blueprint
# integrity block's byte-identity parity this is the byte-parity guarantee
# per span.
[ "$(grep -oF "the overlay's one-recorded-mutation carve-out" "$P" | wc -l | tr -d ' ')" -eq 2 ] || { echo "PIN FAIL: blueprint carve-out reference count"; fail=1; }
[ "$(grep -oF 'and this session owns that record' "$P" | wc -l | tr -d ' ')" -eq 2 ] || { echo "PIN FAIL: blueprint ownership clause count"; fail=1; }
[ "$fail" -eq 1 ] && exit 1

# Same-edit coupling (P51 origin 3): a payload telemetry path change edits the body or payload text carrying the literal and these pins in one edit; see the execute-plan skill's telemetry exception sentence.
# Context-budget plan Task 4: the checkpoint duty paragraph added to each
# blueprint body. The anchor 'after each blueprint step block' occurs in BOTH
# blueprints, so each pin stretches to the blueprint-unique telemetry record
# span (same twice-needle trap as the F8 note above): reverting one body while
# the other keeps the duty must still fail. P51 origin 2 (plan
# docs/history/plans/2026-09-23-p51-plans-authoring-surface-hygiene.md Task 2) retyped
# both pins from presence greps to count gates (the pin helper carrying the
# count as its command): the authoring span occurs exactly 2 times in
# prompt-templates.md (body + the payload paragraph's compact mirror), the
# execution span exactly 1 (in the execution payload block, not a body
# paragraph), so slice text and the transmitted
# region cannot drift apart again; a wording change to a pinned span is a
# change to the owning plan's prescribed text, so reconcile the pin and the
# text in the same edit and record the superseding origin.
pin "authoring blueprint checkpoint duty" test "$(grep -oF 'after each blueprint step block, at a boundary only, never mid-task, log one telemetry record (skill: plans-authoring) to docs/tmp/authoring/<plan-slug>/context.jsonl' "$P" | wc -l | tr -d ' ')" -eq 2
pin "execution blueprint checkpoint duty" test "$(grep -oF 'after each blueprint step block, at a boundary only, never mid-task, log one telemetry record (skill: execute-plan) to docs/tmp/execute-plan/<plan-slug>/context.jsonl' "$P" | wc -l | tr -d ' ')" -eq 1
# P51 origin 2 payload duty sentence sets and slice reconciliation (same plan,
# Task 2): the payload paragraph's compact RE-ARM DUTY, CONTEXT CHECKPOINTS,
# and FINAL STEP sets are count-gated so the payload stays self-contained for
# the duties a child session must see (the deviation-ledger entry paraphrases
# and must not carry the spans, or these counts drift), and the Step 5
# authoring slice wording is pinned to the payload-paragraph assembly it must
# describe (the pin pair above keeps its prescribed names for the execute-plan
# telemetry coupling sentence).
pin "authoring slice payload-region wording" grep -qF 'observed dispatch practice transmits the authoring blueprint' "$S"
# 2026-09-25 parked-dependency visibility Task 6: the unblock template's
# recipe-delegating re-arm sentences take the count to 2
pin "payload re-arm sentence set count" test "$(grep -oF 'restore the maintenance loop parent state-first, without listing first' "$P" | wc -l | tr -d ' ')" -eq 2
# 2026-09-25 parked-dependency visibility Task 6: the unblock template's
# closing park-discharge and compaction duties take the counts up by one each;
# 2026-09-28 continuation policy plan: the tails are reworded (compaction is
# operator-only) and gated by the plan's positive-count checks, the prefix stays
pin "FINAL STEP prefix count" test "$(grep -oF 'FINAL STEP, after the report:' "$P" | wc -l | tr -d ' ')" -eq 4

# --- authoring claim file surfaces (scheduler ops lanes and durability plan, Task 1) ---
# The 2026-09-18 authoring-lane collision (automation-343ce2b0 vs a foreign
# session on the same item scope) was invisible to the listing- and state-based
# arms; the fix is a claim file the authoring payload writes before its
# pre-work gate and the G1a discovery arm reads. The plain greps below are
# whole-file (satisfiable by the dated deviation-list entry, the F8 precedent),
# so the python integrity block below re-asserts the operative literals
# body-scoped. Design constraints pinned there: the claim duty and gate stay
# separate authoring-blueprint paragraphs (never inside the shared FIRST
# ACTION re-arm span, keeping the re-arm parity pin untouched), and the
# execution blueprint must never carry the claim literal at all (an execution
# payload writing authoring claim files would false-trip G1a's foreign-claim
# reading and stall the lane; expect-absent, body-scoped).
pin "G1a authoring claim discovery arm" grep -qF 'authoring-claims' "$S"
pin "authoring blueprint claim duty" grep -qF 'authoring-claims' "$P"
pin "foreign-claim clobber-witness span present" grep -qF "never clobber the first writer's witness" "$P"
pin "overlay names the concrete claim directory" grep -qF 'docs/tmp/authoring-claims/' "$Z"

# --- authoring claim hardening (P36 scheduler durability and audit plan, Task 3) ---
# Presence canaries only (whole-file, satisfiable by a single occurrence); the
# blueprint integrity block below pins the four added fragments region-scoped
# to the authoring body's two claim paragraphs (the AUTHORING CLAIM duty
# paragraph and the foreign-claim gate paragraph share vocabulary, so a
# whole-file grep cannot tell them apart) with exactly-once file-wide counts,
# so a stray copy in the sibling claim paragraph or the deviation-list ledger
# entry fails there (the ledger entry paraphrases the spans and must not carry
# them).
pin "claim create noclobber recipe present" grep -qF 'set -C; printf' "$P"
pin "takeover re-read-before-delete span present" grep -qF 're-reads the claim file immediately before the unlink' "$P"
pin "ownership re-check stand-down clause present" grep -qF 'stands this session down from authoring the item' "$P"
pin "unparseable-session-line disposition present" grep -qF 'no parseable session: line is treated as foreign' "$P"

# --- prompt-templates.md blueprint integrity ---
python3 - "$P" "$Z" "$D" <<'EOF' || fail=1  # r7 F1: propagate the block status; without this the block is fail-open at the exit-code surface
import re, sys
p, z, d = open(sys.argv[1]).read(), open(sys.argv[2]).read(), open(sys.argv[3]).read()
def norm(t): return " ".join(t.split())
def need(text, anchor):
    if anchor not in text:
        print("PIN FAIL: missing anchor %s" % anchor); sys.exit(1)
need(p, "<prompt for the scheduled session>"); need(p, "</prompt>")
if p.count("<prompt for the scheduled session>") != 1 or p.count("</prompt>") != 2:
    print("PIN FAIL: execution dispatch-slice tag counts drifted (expected 1 opener + 2 closers: the blueprint pair plus the unblock wrapper's closer)"); sys.exit(1)
inner = p.split("<prompt for the scheduled session>")[1].split("</prompt>")[0]
for needle in ("FIRST ACTION", "{some_plan}", "{REPO_ROOT}", "SUCCESSOR DISPATCH", "this is a resume run"):
    if needle not in inner:
        print("PIN FAIL: execution inner block missing %s" % needle); sys.exit(1)
for banned in ("{execution_time}", "SCHEDULER"):
    if banned in inner:
        print("PIN FAIL: execution inner block must not contain %s" % banned); sys.exit(1)
paras = [norm(m.group(0)) for m in
         re.finditer(r"FIRST ACTION, before any gate or phase: re-arm the maintenance loop state-first, without listing first\..*?reading that note re-arms per the recipe\.", p, re.S)]
if len(paras) != 2 or paras[0] != paras[1]:
    print("PIN FAIL: the two re-arm duty paragraphs differ or are not both present"); sys.exit(1)
for needle in ('"rearm_note"', "loop-parent-missing", "parent_automation_id",
               "Recurring automation recipe", "after two retries",
               "counts as success only after one more listing confirms",
               "listed twice without a mutating step", "first applicable step wins",
               "(1) when", "(2) when", "(3) when"):
    if needle not in paras[0]:
        print("PIN FAIL: re-arm paragraph escalation drifted (missing %s)" % needle); sys.exit(1)
# state durability plan Tasks 3 and 5: the re-arm duty paragraph carries the
# appendix-sourcing sentence and the primitive-precheck sentences (before the
# reshape and the create/recycle legs); paras[0] membership plus the
# byte-identity parity above cover both blueprints, so deleting either
# sentence from either paragraph fails a pin
for needle in ("assert the session actually owns", "mode appendix sourced from state"):
    if needle not in paras[0]:
        print("PIN FAIL: re-arm paragraph lacks the state-durability needle %s" % needle); sys.exit(1)
# review r1 F5: the pending_rearm park duties (the (4) escalation park, the
# Loop-guard stand-down park, and the decision-first recording) are pinned
# paras[0]-scoped (the byte-identity parity covers the twin paragraph); the
# deviation-list entries paraphrase these spans and must not carry them
for needle in ('then write "pending_rearm" plus the assembled parent payload copy under the rearm kind\'s identity-bound payload filename (derived per the pending_rearm field paragraph) in the same targeted state edit (the park-path pairing rule: intent record and payload copy are one paired write, always before the memory note)',
               'write "pending_rearm" plus the assembled parent payload copy under the rearm kind\'s identity-bound payload filename (derived per the pending_rearm field paragraph) in that same targeted state edit (the park-path pairing rule)',
               'set "pending_rearm" (targeted field edit) paired with the assembled parent payload copy under the rearm kind\'s identity-bound payload filename (derived per the pending_rearm field paragraph; the park-path pairing rule)'):
    if needle not in paras[0]:
        print("PIN FAIL: re-arm paragraph lacks the pending_rearm park duty span %s" % needle[:72]); sys.exit(1)
# scheduler ops lanes and durability plan Task 4: the durable HOST CAVEAT is
# pinned parity-safe by count (the spans sit inside the byte-identical re-arm
# paragraphs, so exactly one occurrence per blueprint; the deviation-list
# entries paraphrase and must not carry the spans, or these counts drift)
rearm_caveat = "HOST CAVEAT: any recycling update whose echoed record is not verifiably the intended form (enabled true, the intended recurring value, a future nextRunAt confirmed by a listing) is treated as a refusal and takes the delete-plus-create path"
if p.count(rearm_caveat) != 2:
    print("PIN FAIL: re-arm HOST CAVEAT count %d != 2 (one per blueprint paragraph)" % p.count(rearm_caveat)); sys.exit(1)
succ_caveat = "HOST CAVEAT: any recycling update whose echoed record is not verifiably the intended form (enabled true, recurring false, a future nextRunAt matching the successor fire time, confirmed by a listing) is treated as a refusal"
if p.count(succ_caveat) != 1:
    print("PIN FAIL: successor reshape-leg HOST CAVEAT count %d != 1" % p.count(succ_caveat)); sys.exit(1)
# state durability plan Tasks 3-5: whole-file count floors for the two
# blueprint sentences. The mode-appendix sourcing sentence must stand in all
# three legs (each re-arm paragraph plus the successor both-legs-fail leg; the
# deviation-list entries paraphrase the span and must not carry it, or this
# floor drifts); the floor is the prescribed whole-file minimum, and review
# r1 F21's shrink suggestion for it overflowed to backlog, so it stays.
# Review r1 F14: the primitive-precheck needle is pinned to the exact total 5
# (the re-arm paragraphs carry it twice each, before the reshape and the
# create/recycle legs, and the successor leg once), so any single deletion
# anywhere fails it; the per-paragraph distribution below is pinned at 2 for
# the both-legs-identical-deletion shape: the byte-identity parity pin already
# fails a single-leg deletion first, so this pin's marginal direction is the
# both-legs deletion, which keeps the two paragraphs byte-identical and drops
# the needle from both at once (the successor leg's copy is covered by its own
# region membership check above)
if p.count("mode appendix sourced from state") < 3:
    print("PIN FAIL: mode appendix sourcing count %d < 3 in prompt-templates.md" % p.count("mode appendix sourced from state")); sys.exit(1)
if p.count("assert the session actually owns") != 5:
    print("PIN FAIL: primitive precheck count %d != 5 in prompt-templates.md" % p.count("assert the session actually owns")); sys.exit(1)
if paras[0].count("assert the session actually owns") != 2:
    print("PIN FAIL: re-arm paragraph precheck distribution %d != 2 per paragraph" % paras[0].count("assert the session actually owns")); sys.exit(1)
if p.count("Maintenance scheduler turn (every 2 hours)") != 0:
    print("PIN FAIL: title literal must not appear in prompt-templates.md (the zcode.md recipe is the single literal home)"); sys.exit(1)
if z.count("Title: `Maintenance scheduler turn`") != 1:
    print("PIN FAIL: new title literal must appear exactly once (recipe) in zcode.md"); sys.exit(1)
span = "You are the maintenance scheduler for the repository at"
if z.count(span) != 2 or p.count(span) != 0:
    print("PIN FAIL: recognition span literal counts drifted (want 2 in zcode.md, 0 in prompt-templates.md)"); sys.exit(1)
if p.count("SUCCESSOR DISPATCH") != 1:
    print("PIN FAIL: successor anchor must appear exactly once in prompt-templates.md (execution blueprint only)"); sys.exit(1)
need(p, "## Authoring child"); need(p, "## Execution child")
auth = p.split("## Authoring child")[1].split("## Execution child")[0]
ph = set(re.findall(r"\{[A-Za-z_]+\}", auth))
if ph != {"{schedule_time}", "{backlog_item}", "{REPO_ROOT}"}:
    print("PIN FAIL: authoring body placeholder set drifted: %s" % sorted(ph)); sys.exit(1)
exec_ph = set(re.findall(r"\{[A-Za-z_]+\}", inner))
if exec_ph != {"{REPO_ROOT}", "{some_plan}"}:
    print("PIN FAIL: execution inner placeholder set drifted: %s" % sorted(exec_ph)); sys.exit(1)
if "cron expression" in paras[0]:
    print("PIN FAIL: re-arm paragraph hardcodes the cadence; creation must follow the recipe"); sys.exit(1)
# ordering pins (region-scoped to the execution inner block): the payload must
# chain the successor before the final compaction step, and the resume rule
# must sit after the PRE-STEP gate; every predecessor anchor is fail-closed.
# r2 F7: the final-merge lead-in keys on the landing-target wording, never on
# the bare old lead-in (the literal "to main" was a shared-prose hardcode the
# consolidation review retired). r5 resolution: the tail pins the default
# branch per the majority reading; the literal 'to main' stays retired, and
# the generic default-branch wording is not a repository-name hardcode.
for needle in ("Finally squash merge to the repository's default branch", "SUCCESSOR DISPATCH", "FINAL STEP",
               "once the gate exits 0", "this is a resume run"):
    need(inner, needle)
if not inner.index("Finally squash merge to the repository's default branch") < inner.index("SUCCESSOR DISPATCH") < inner.index("FINAL STEP"):
    print("PIN FAIL: execution payload ordering drifted (squash merge < SUCCESSOR DISPATCH < FINAL STEP)"); sys.exit(1)
if not inner.index("once the gate exits 0") < inner.index("this is a resume run"):
    print("PIN FAIL: execution payload ordering drifted (resume rule must follow the PRE-STEP gate)"); sys.exit(1)
# done-skill ordering pin: the rearm-on-touch pointer precedes the Step 0 heading
need(d, "Before Step 0, in a repository that resolves the maintenance skill")
need(d, "## Step 0")
if not d.index("Before Step 0, in a repository that resolves the maintenance skill") < d.index("## Step 0"):
    print("PIN FAIL: done-skill rearm-on-touch pointer must precede the Step 0 heading"); sys.exit(1)
# confinement pins (origin 3 scope note): execution-only spans stay inside the
# execution inner block, split off the blueprint headings and dispatch-slice tags
def confined(span):
    if p.count(span) != 1 or inner.count(span) != 1:
        print("PIN FAIL: execution-only span left the execution inner block: %s" % span); sys.exit(1)
confined("beyond the re-arm duty below and the single successor-dispatch duty below")
confined("this is a resume run")
# state durability plan Tasks 4 and 5: the successor both-legs-fail leg carries
# its own precheck sentence (before the reshape leg), its own appendix
# sentence (on the re-create leg), and its own pending_dispatch park write (the
# both-legs-fail tail); all are pinned region-scoped to the successor paragraph
# (everything in the execution inner block after the SUCCESSOR DISPATCH anchor),
# so a single-leg deletion cannot hide behind the other legs' copies (the park
# write pin is review r1 F5)
succ = inner.split("SUCCESSOR DISPATCH")[1]
for needle in ("assert the session actually owns", "mode appendix sourced from state",
               'write "pending_dispatch" (kind execute'):
    if needle not in succ:
        print("PIN FAIL: successor dispatch leg lacks the state-durability needle %s" % needle); sys.exit(1)
# review r2 F7: the chain-nothing loop_mode condition, region-scoped to the
# successor paragraph (the deviation-list entry paraphrases it, so a whole-file
# grep would be satisfied by the registration prose); the needle re-anchored on
# the named-exclusion reference in the deferred-residual-dispositions plan
# Task 9 (T4 reduced the restated mode semantics to the named Step 3 exclusion)
if "the Step 3 loop-mode exclusion" not in succ:
    print("PIN FAIL: successor leg lacks the chain-nothing loop_mode condition"); sys.exit(1)
# review r3 F12: the watchdog recovery clear span (the SKILL.md watchdog writer
# class names it), region-scoped to the Watchdog backstop bullet (one line; the
# whole-file zcode greps cannot scope it, so the check lives here)
watchdog_line = ""
for line in z.split("\n"):
    if line.startswith("- Watchdog backstop:"):
        watchdog_line = line
        break
if not watchdog_line or "and `pending_rearm`" not in watchdog_line:
    print("PIN FAIL: watchdog bullet lacks the rearm_note-and-pending_rearm recovery clear span"); sys.exit(1)
# loop liveness durable carriers and park coverage plan: the bullet's level-2
# escalation carries the park write (region-scoped to the one bullet line the
# block above already extracts, so a stray copy elsewhere cannot satisfy it).
if not watchdog_line or "escalation plus the watchdog park write" not in watchdog_line:
    print("PIN FAIL: watchdog bullet lacks the level-2 escalation park write span"); sys.exit(1)
# review r5 F2: the recipe gate's mode-value phrasing (the landed r4 wording),
# region-scoped to the recipe section (the Step 0 removal trigger and the
# Revisions ledger paraphrase the same gate on other surfaces, so a whole-file
# grep would be satisfied by a stray copy; deleting the gate's clause empties
# the span and fails here)
recipe_region = z.split("## Recurring automation recipe")[1].split("\n## ")[0]
if "carries a mode of `authoring-only` or `execution-only`" not in recipe_region:
    print("PIN FAIL: recipe section lacks the mode-value gate span"); sys.exit(1)
# merge landing lock group (plan 2026-09-20-merge-landing-lock-grouping):
# each blueprint acquires the merge landing lock exactly once (the dated
# deviation-list entries paraphrase the literal, so the count stays 2), the
# authoring blueprint carries the worktree-first reference span (re-keyed
# 2026-09-28 by the worktree-first standard consolidation, plan
# 2026-09-28-worktree-first-standard-only-mode.md Task 4: the retired
# create-command literal was the old key), and the
# superseded riding sentence is absent from the fenced blueprint bodies
# (region-scoped like the checkbox-regex pin above, so the dated deviation-list
# history entry outside the fences stays legal).
if p.count("merge-wait-acquire") != 2:
    print("PIN FAIL: merge-wait-acquire count %d != 2 in prompt-templates.md (once per blueprint)" % p.count("merge-wait-acquire")); sys.exit(1)
need(norm(p), "per the Worktree-first standard section in agents/skills/execute-plan/SKILL.md; that worktree's own branch is the authoring branch")
fence = "```"
bodies = re.findall(r"^" + fence + r"\n(.*?)^" + fence + r"$", p, re.S | re.M)
if not bodies:
    print("PIN FAIL: no fenced blueprint bodies found (absence check would be vacuous)"); sys.exit(1)
riding = "final squash merge as joint-state content"
hits = [i for i, body in enumerate(bodies) if riding in body]
if hits:
    print("PIN FAIL: superseded riding sentence still in fenced blueprint body(ies) %s" % hits); sys.exit(1)
# r3 F2 (plan 2026-09-20-merge-landing-lock-grouping, r3 folds): the
# r2-generation landing invariants are pinned scoped to the authoring body
# itself; the dated deviation-list entries only paraphrase these literals,
# so a body-scoped check cannot be satisfied by the registration prose.
# The filter keys on the new authoring reference sentence's distinctive span
# (re-keyed 2026-09-28, worktree-first standard consolidation, plan
# 2026-09-28-worktree-first-standard-only-mode.md Task 4; the span lives
# inside the authoring fenced body and is unique there and whole-file).
auth_bodies = [b for b in bodies if "per the Worktree-first standard section in agents/skills/execute-plan/SKILL.md; that worktree's own branch is the authoring branch" in norm(b)]
if len(auth_bodies) != 1:
    print("PIN FAIL: could not uniquely identify the authoring blueprint body"); sys.exit(1)
# r2 F5: the authoring span's exactly-once whole-file count is normalized
# here (beside the filter it protects) instead of a line-bound grep -oF, so
# the whole re-keyed pin family shares one wrap tolerance.
if norm(p).count("per the Worktree-first standard section in agents/skills/execute-plan/SKILL.md; that worktree's own branch is the authoring branch") != 1:
    print("PIN FAIL: authoring worktree-first reference span count != 1 (auth_bodies identification would degenerate)"); sys.exit(1)
for needle in ("git add -- <paths>",
               "git update-ref refs/heads/<default> <new> <old>",
               "git show refs/heads/<default>:"):
    need(norm(auth_bodies[0]), needle)
# authoring claim file surfaces (scheduler ops lanes and durability plan,
# Task 1): body-scoped positives for the authoring blueprint and the
# expect-absent half for the execution blueprint. The plain greps above are
# satisfiable by the dated deviation-list prose, so the operative literals are
# asserted inside the authoring body itself; the execution body and its
# dispatch slice must never carry the literal (a foreign-claim false trip
# would stall G1a), and the re-arm parity span must stay claim-free (the duty
# and gate are separate paragraphs, never inside the shared FIRST ACTION span).
if "docs/tmp/authoring-claims/" not in auth_bodies[0]:
    print("PIN FAIL: claim directory literal missing from the authoring blueprint body"); sys.exit(1)
if "never clobber the first writer's witness" not in auth_bodies[0]:
    print("PIN FAIL: foreign-claim gate (clobber-witness span) missing from the authoring blueprint body"); sys.exit(1)
exec_bodies = [b for b in bodies if "SUCCESSOR DISPATCH" in b]
if len(exec_bodies) != 1:
    print("PIN FAIL: could not uniquely identify the execution blueprint body"); sys.exit(1)
if "authoring-claims" in exec_bodies[0] or "authoring-claims" in inner:
    print("PIN FAIL: execution blueprint carries the authoring-claims literal (a foreign-claim false trip would stall G1a)"); sys.exit(1)
# r1 F10 (worktree-first consolidation review): the execution-body absence half for the authoring identification span was dropped as provably unreachable: the auth_bodies exactly-once check above already fails every corruption shape it claimed (a stray copy in the execution body makes len(auth_bodies) != 1, and the python block's normalized whole-file count pin above catches any copy anywhere; the shell section below carries no such pin), so no check remains here on purpose.
# r1 F3 (worktree-first consolidation review): the execution blueprint's and
# the unblock template's worktree-first reference sentences are pinned
# exactly-once whole-file (wrap-tolerant, normalized) and body-scoped, so
# wholesale deletion of either paragraph fails the suite; the deviation-list
# entries outside the fences paraphrase and must not carry the spans.
# r2 F5: the unblock identification filter keys on norm(b) like the
# auth_bodies filter above, so the pin family shares one wrap tolerance.
exec_wf_span = "own ad-hoc worktree on its own branch per the Worktree-first standard section in agents/skills/execute-plan/SKILL.md"
unblock_wf_span = "works inside its own ad-hoc worktree created per the Worktree-first standard section in agents/skills/execute-plan/SKILL.md"
unblock_bodies = [b for b in bodies if "WORK ORDER (the target plan is the serialized plan" in norm(b)]
if len(unblock_bodies) != 1:
    print("PIN FAIL: could not uniquely identify the unblock blueprint body"); sys.exit(1)
for wf_span, wf_body, wf_desc in ((exec_wf_span, exec_bodies[0], "execution"), (unblock_wf_span, unblock_bodies[0], "unblock")):
    if norm(p).count(wf_span) != 1:
        print("PIN FAIL: %s worktree-first reference span count %d != 1 (wrap-tolerant whole-file)" % (wf_desc, norm(p).count(wf_span))); sys.exit(1)
    if wf_span not in norm(wf_body):
        print("PIN FAIL: %s worktree-first reference span missing from its fenced blueprint body" % wf_desc); sys.exit(1)
# execution-integrity worker-evidence plan Task 3: the payload tail claim
# duty. Scoped to the Schedule-at paragraph itself (distinct from the
# whole-body authoring pin above): the payload paragraph is what scheduled
# sessions actually receive, so its own claim sentences are pinned here and
# their omission cannot regress silently.
payload_paras = [q for q in p.split("\n") if "the following task: Using the plans skill" in q]
if len(payload_paras) != 1:
    print("PIN FAIL: authoring payload paragraph matched %d lines, expected exactly 1" % len(payload_paras)); sys.exit(1)
for needle in ("docs/tmp/authoring-claims/", "updated:", "refresh", "closeout", "delete"):
    if needle not in payload_paras[0]:
        print("PIN FAIL: payload tail claim paragraph missing %s" % needle); sys.exit(1)
for para in paras:
    if "authoring-claims" in para:
        print("PIN FAIL: claim duty/gate must stay outside the shared re-arm FIRST ACTION span"); sys.exit(1)
# P36 scheduler durability and audit plan Task 3: the claim-protocol
# hardening. The four added fragments are pinned region-scoped to the authoring
# body's two claim paragraphs, located by their unique openers inside
# auth_bodies[0] (the deviation list sits outside the fences, so a ledger copy
# cannot satisfy the region membership); each fragment is also asserted exactly
# once file-wide, so deleting it, duplicating it into the sibling claim
# paragraph, or carrying it in the deviation-list ledger entry all fail here.
cduty_at = auth_bodies[0].find("AUTHORING CLAIM, the claim file this session writes before any plan work")
if cduty_at == -1:
    print("PIN FAIL: AUTHORING CLAIM duty paragraph missing from the authoring body"); sys.exit(1)
cduty = auth_bodies[0][cduty_at:auth_bodies[0].find("\n\n", cduty_at)]
gate_at = auth_bodies[0].find("Before writing anything: verify no merge or rebase is in progress")
if gate_at == -1:
    print("PIN FAIL: foreign-claim gate paragraph missing from the authoring body"); sys.exit(1)
gate = auth_bodies[0][gate_at:auth_bodies[0].find("\n\n", gate_at)]
for desc, frag, region in (
    ("noclobber create recipe",
     "set -C; printf '%s\\n' <frontmatter lines> > \"<primary-root>/docs/tmp/authoring-claims/<backlog-item-basename>.md\"",
     cduty),
    ("takeover re-read-before-delete",
     "re-reads the claim file immediately before the unlink and deletes it only while it still names the same foreign session id with a stale updated: line",
     gate),
    ("ownership re-check stand-down",
     "a foreign id at an ownership re-check stands this session down from authoring the item",
     cduty),
    ("unparseable-session-line disposition",
     "a claim file with no parseable session: line is treated as foreign",
     gate),
):
    if p.count(frag) != 1:
        print("PIN FAIL: %s fragment count %d != 1 in prompt-templates.md" % (desc, p.count(frag))); sys.exit(1)
    if frag not in region:
        print("PIN FAIL: %s fragment missing from its owning claim paragraph" % desc); sys.exit(1)
EOF
rc=$?
[ "$rc" -ne 0 ] && fail=1
[ "$fail" -eq 1 ] && exit 1

# --- rearm-on-touch surfaces (Task 4) ---
pin "step 0 rearm-on-touch check" grep -qF 'rearm-on-touch check: consult the scheduler state file first' "$S"
expect_absent "superseded listing-first rearm-on-touch trigger must be absent from SKILL.md" 'when the automation listing shows no ENABLED parent' "$S"
pin "done-skill rearm-on-touch pointer" grep -qF 'rearm-on-touch check defined in the maintenance skill' "$D"
[ "$fail" -eq 1 ] && exit 1

# --- budget-gate resume mirrors (P6 origins 1-2) ---
PL="$repo/agents/skills/plans/SKILL.md"
R="$repo/agents/skills/review-loop/SKILL.md"
RC="$repo/agents/skills/execute-plan/runtime-contract.md"
for f in "$E" "$PL" "$R" "$RC"; do
  [ -f "$f" ] || { echo "missing $f"; fail=1; }
done
[ "$fail" -eq 1 ] && exit 1
pin "resume-fit --fire-at check at resume-scheduling boundaries" grep -qF -- '--fire-at mode with the scheduled resume time as the fire instant' "$E"
pin "resume-pricing defers to the reported defer_to" grep -qF 'on exit 2 (defer-peak, a fitting slot inside the weekday peak window), schedule the watcher at the reported defer_to' "$E"
pin "plans budget gate mirrors the canonical resume checks" grep -qF 'The canonical resume-fit and resume-pricing checks apply at this boundary' "$PL"

# --- dfm gate-suite successor pins (P56 Task 4; archived plan bytes frozen) ---
# dfm r1 F5 successor (whole-file; the archived plan's gates saw only the extracted template region)
[ "$(grep -oF 'Driving force: <tag>' "$PL" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: driving-force template count (F5)"; fail=1; }
[ "$(grep -oF 'TLDR: <what changes>' "$PL" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: TLDR template count (F5)"; fail=1; }
# dfm r1 F8 successor (taxonomy tail and park-triage half had no needles)
pin "dfm r1 F8 successor external-cites-source needle" grep -qF 'where `external` must cite its source' "$PL"
pin "dfm r1 F8 successor park-triage needle" grep -qF 'why park-triage would or would not take it' "$PL"
pin "dfm r2 F1 successor backlog-origin-none producer line" grep -qF 'otherwise the line reads `Backlog origin: none`' "$PL"
pin "dfm r2 F1 successor driving-principles enumeration" grep -qF 'five driving principles (`efficiency`, `token-usage`, `simplicity`, `code-quality`, `automation`)' "$PL"

# --- budget-gate resume fallback preservation pins (plan 2026-09-21-budget-gate-resume-fallbacks, Task 1) ---
# Freeze-literal origin note: the preservation spans' origin is plan
# docs/history/plans/2026-09-21-budget-gate-resume-fallbacks.md; their text was landed
# by commit e71fd55a (the quota-aware-scheduling-semantics delivery), and the
# two re-frozen mirror spans (the mirror carrier-aware record span and the
# mirror host idle-time automation rung span) had their current literal wording
# shaped by commit 8a77ec46 (commit dated 2026-09-22; re-freeze recorded 2026-09-23). A wording change to any
# pinned span is a change to that plan's prescribed text, so reconcile the pin
# and the text in the same edit and record the superseding origin.
# Count-gated (not the grep -qF `pin` helper) so drift fails in either
# direction: exactly 1 fails a deletion and a stray duplicate copy; the mirror
# rung span is count-gated at exactly 3. Reuses the $E and $PL variables the
# mirrors block above sets.
n="$(grep -oF -- 'The create carries the canonical lineage-cap branch' "$E" | wc -l | tr -d ' ')"; [ "$n" -eq 1 ] || { echo "PIN FAIL: preservation: canonical lineage-cap branch span count $n != 1"; fail=1; }
n="$(grep -oF -- 'Resume carrier fallback ordering (canonical)' "$E" | wc -l | tr -d ' ')"; [ "$n" -eq 1 ] || { echo "PIN FAIL: preservation: Resume carrier fallback ordering heading span count $n != 1"; fail=1; }
n="$(grep -oF -- 'the OffPeakCreate rung first' "$E" | wc -l | tr -d ' ')"; [ "$n" -eq 1 ] || { echo "PIN FAIL: preservation: OffPeakCreate pause rung span count $n != 1"; fail=1; }
n="$(grep -oF -- "wired via the driver's scheduler chain" "$E" | wc -l | tr -d ' ')"; [ "$n" -eq 1 ] || { echo "PIN FAIL: preservation: launchd wired mark span count $n != 1"; fail=1; }
n="$(grep -oF -- 'the prompt must carry the reset epoch and a wait instruction' "$E" | wc -l | tr -d ' ')"; [ "$n" -eq 1 ] || { echo "PIN FAIL: preservation: OffPeakCreate prompt contract span count $n != 1"; fail=1; }
n="$(grep -oF -- 'or when the OffPeakCreate rung carries the resume' "$E" | wc -l | tr -d ' ')"; [ "$n" -eq 1 ] || { echo "PIN FAIL: preservation: canonical carrier-aware record span count $n != 1"; fail=1; }
n="$(grep -oF -- 'or when the host idle-time automation rung carries the resume' "$PL" | wc -l | tr -d ' ')"; [ "$n" -eq 1 ] || { echo "PIN FAIL: preservation: mirror carrier-aware record span count $n != 1"; fail=1; }
n="$(grep -oF -- "deletes the session's own completed spawner record and retries the create once" "$PL" | wc -l | tr -d ' ')"; [ "$n" -eq 1 ] || { echo "PIN FAIL: preservation: mirror lineage-cap branch span count $n != 1"; fail=1; }
n="$(grep -oF -- 'host idle-time automation rung' "$PL" | wc -l | tr -d ' ')"; [ "$n" -eq 3 ] || { echo "PIN FAIL: preservation: mirror OffPeakCreate rung span count $n != 3"; fail=1; }

# --- rate-limited end claim boundary, receipt carrier, and recovery marker (P37 rate-pressure ingestion and quota scheduling plan, Task 1) ---
pin "rate-limited end resolves its open claim" grep -qF 'the end resolves an open task claim' "$E"
pin "claim-less end derives from stop lines" grep -qF 'claim-less rate-limited end has no receipt carrier' "$E"
pin "post-backoff success writes a recovery marker" grep -qF 'writes the recovery marker line' "$E"
pin "state table derives the claim-less case" grep -qF 'for a claim-less rate-limited end, the recorded rate-limited stop lines' "$E"
pin "contract mirrors the claim boundary" grep -qF 'resolves the claim per the budget-pause precedent' "$RC"
pin "contract derives the claim-less case from stop lines" grep -qF 'its waiting-for-capacity derivation reads the recorded stop lines' "$RC"
# --- backoff floor and scaled panel bounds (P37 rate-pressure ingestion and quota scheduling plan, Task 2) ---
pin "resume backoff carries a floor" grep -qF 'after a backoff of at least 60 seconds' "$E"
pin "serialized cap doubles the intermediate-panel bound" grep -q 'intermediate panels inherit the 20-minute timeout.*panel wall-clock bounds double' "$E"
pin "serialized cap doubles the Step 3.1 bound" grep -q 'wall-clock from Step 3.1 start.*panel wall-clock bounds double' "$E"
pin "serialized cap doubles the fanned-round bound" grep -q 'fanned address wave inherits the Step 3.1 timeout semantics.*panel wall-clock bounds double' "$E"
pin "serialized cap doubles the omnibus bound" grep -q 'If a sequential sub-agent.*panel wall-clock bounds double' "$E"
# --- writer/ingester stop-line token format (P37 rate-pressure ingestion and quota scheduling plan, Task 3) ---
pin "stop line token format pinned" grep -qF 'a line-initial rate_limited: token followed by an ISO timestamp' "$E"
pin "ingestion mirrors the stop-line token format" grep -qF 'a line-initial rate_limited: token followed by an ISO timestamp' "$S"
# --- dedup ledger decoupled from the capped array (P37 rate-pressure ingestion and quota scheduling plan, Task 4) ---
pin "dedup consults the rolling ledger" grep -qF 'the dedup consults the rolling ledger' "$S"
pin "ledger rides the same 24-hour window" grep -qF 'pruned to the same 24-hour window' "$S"
pin "step 6 carries the dedup ledger" grep -qF 'plus the dedup ledger (the ledger is a top-level field' "$S"
pin "dedup ledger declared in the schema block" grep -qF '"rate_limited_dedup_ledger"' "$S"
# --- lost-update enumeration and define-once rate_pressure (P37 rate-pressure ingestion and quota scheduling plan, Task 5) ---
pin "lost-update enumeration names the rate rail" grep -qF 'the rate-pressure rail' "$S"
pin "rate_pressure defined once in the schema block" grep -qF 'the derived count defined in State file' "$S"
[ "$fail" -eq 1 ] && exit 1

# --- cap-semantics policy cluster (plan
# 2026-09-22-p37-context-budget-probes-and-runtime-state, Task 1) ---
# Heading anchors for the two sections other files navigate by (characterization:
# both hold today) and the capped-rung policy pins over the Above 85% bullet of
# the Context budget checkpoints section in execute-plan.
pin "context checkpoints section anchored" grep -qF '### Context budget checkpoints' "$E"
pin "measurement primitive section anchored" grep -qF '## Context measurement primitive' "$Z"
pin "capped rung degrades to shedding" grep -qF 'a capped rung degrades to the 70-85% shedding rung' "$E"
pin "capped record action vocabulary" grep -qF 'action: capped' "$E"
pin "compaction completion timing pinned" grep -qF 'increments only when the compaction completes' "$E"
pin "terminal rung after consecutive capped checkpoints" grep -qF 'three consecutive capped above-85% checkpoints' "$E"
# P37 Task 2 (dual-lane coordination and archive vocabulary): review-loop's
# round-boundary checkpoint subordination to the execute-plan ladder, and the
# child telemetry lanes' live paths kept as their analysis home in execute-plan.
pin "review-loop ladder precedence" grep -qF 'authoritative for ladder actions' "$R"
pin "review-loop first-record baseline" grep -qF 'the first record review-loop appends for a run is the baseline' "$R"
pin "child lanes analysis home" grep -qF 'as their analysis home' "$E"
# P37 Task 3 (tmp-dir substitution sentence): the Telemetry bullet's
# substitution rule scoped to every telemetry path this policy names, with the
# maintenance blueprints' payload paths recorded as the pinned literal exception.
pin "telemetry substitution rule scopes this policy's paths" grep -qF 'governs every telemetry path this policy names' "$E"
# P48 Task 1 (unlanded-plan worktree cherry-pick): the linked-worktree bootstrap
# names the missing-plan remedy for plan bytes living on an unlanded branch.
pin "worktree bootstrap names the unlanded-plan remedy" grep -qF 'cherry-pick only the plan-authoring commit' "$E"
# P37 Task 4 (turn-usage live verification): the measurement primitive section
# must name the store's turn_usage table (the live-verified source or the
# recorded negative, per the variant applied).
pin "measurement primitive names turn_usage" grep -qF 'turn_usage' "$Z"
# --- worktree-first r3 witness needles (plan
# 2026-09-28-worktree-first-standard-only-mode.md, review round 3 address) ---
# Exactly-once, wrap-tolerant (normalized) presence pins over the canonical
# Worktree-first section's two r2/r3 fix-commit paragraphs in execute-plan
# SKILL.md: the Provisioned-worktree adoption paragraph and the Base-branch
# resolution rule's origin-HEAD fallback arm. Whole-file greps would satisfy a
# stray copy in another file's prose, so both are scoped to "$E" and counted
# normalized, per the r2 F5 wrap-tolerance convention; wholesale deletion of
# either paragraph empties its count and fails here.
python3 - "$E" <<'EOF' || fail=1  # r7 F1: propagate the block status; without this the block is fail-open at the exit-code surface
import sys
e = open(sys.argv[1]).read()
def norm(t): return " ".join(t.split())
for desc, needle in (
    ("Provisioned-worktree adoption paragraph", "Provisioned-worktree adoption"),
    ("base-branch origin-HEAD fallback arm", "resolves its default branch via the origin HEAD symbolic ref"),
):
    n = norm(e).count(needle)
    if n != 1:
        print("PIN FAIL: %s count %d != 1 in execute-plan SKILL.md" % (desc, n)); sys.exit(1)
EOF
[ "$fail" -eq 1 ] && exit 1

# --- discovery ladder rung 1 bound (P36 scheduler durability and audit plan, Task 5) ---
# The rung 1 closure sentence is bounded to a terminal or complete workflow_state
# before it may close no-live-session, and an absent or non-terminal workflow_state
# falls through to rung 2's heartbeat signals. Presence canaries below are
# whole-file; the python block re-asserts both spans region-scoped to the
# Live-session discovery ladder section with exactly-once file-wide counts (the
# workflow-state table and rung 2's heartbeat prose share vocabulary, so a
# whole-file grep cannot tell the owning bullet from a stray copy; deleting the
# bound or the fall-through clause empties the span and fails there).
pin "rung 1 terminal-or-complete workflow_state bound present" grep -qF 'is terminal or complete' "$E"
pin "rung 1 fall-through clause present" grep -qF 'rung 1 does not close the question and the ladder falls through to rung 2' "$E"
python3 - "$E" <<'EOF' || fail=1  # r7 F1: propagate the block status; without this the block is fail-open at the exit-code surface
import sys
e = open(sys.argv[1]).read()
if "## Live-session discovery ladder" not in e:
    print("PIN FAIL: Live-session discovery ladder section missing from execute-plan SKILL.md"); sys.exit(1)
ladder = e.split("## Live-session discovery ladder", 1)[1].split("\n## ", 1)[0]
for desc, span in (
    ("rung 1 terminal-or-complete workflow_state bound", "is terminal or complete"),
    ("rung 1 fall-through to rung 2", "rung 1 does not close the question and the ladder falls through to rung 2"),
):
    if e.count(span) != 1:
        print("PIN FAIL: %s count %d != 1 in execute-plan SKILL.md" % (desc, e.count(span))); sys.exit(1)
    if span not in ladder:
        print("PIN FAIL: %s missing from the Live-session discovery ladder section" % desc); sys.exit(1)
EOF
rc=$?
[ "$rc" -ne 0 ] && fail=1
[ "$fail" -eq 1 ] && exit 1

# --- trigger-verb contract surfaces (schedule-vs-execute verb contract plan, Task 3) ---
A="$repo/AGENTS.md"
[ -f "$A" ] || { echo "missing $A"; fail=1; }
[ "$fail" -eq 1 ] && exit 1
pin "SKILL.md trigger-verb subsection anchored" grep -qF 'Trigger verbs (schedule vs execute vs resume)' "$S"
pin "repo AGENTS.md scheduling verb contract anchored" grep -qF 'Scheduling asks (verb contract)' "$A"
pin "zcode.md interactive dispatch template anchored" grep -qF 'Interactive dispatch template' "$Z"
[ "$fail" -eq 1 ] && exit 1

# --- toolset precheck surfaces (scheduler ops contract plan, Task 4) ---
# Pin-vacuity fixes (plan 2026-09-21-scheduler-maintenance-loop-quality-hygiene,
# Task 6, 2026-09-23): the SKILL.md pin below is re-needled from the generic
# 'ladder precheck' phrase (measured 2026-09-23: 3 occurrences in SKILL.md,
# the operative Step 5 precondition plus two scoping notes, so the presence
# pin aliases and stayed green with the precondition deleted; the phrase
# stays legal in SKILL.md and is deliberately not frozen absent, only
# unpinned) to the distinctive Step 5 needle quoted verbatim from the Task 5
# rephrase, which matches only the operative precondition (measured: 1
# occurrence). The stand-down-reason pins convert from presence to
# per-occurrence counts (measured 2026-09-23: 2 occurrences each in
# zcode.md, both normative, so a presence pin was satisfiable by either
# occurrence alone; a single deletion now trips the count).
pin "SKILL.md step 5 ladder-precheck precondition anchored" grep -qF 'Ladder precheck: after the quota leg (for a clocked dispatch)' "$S"
pin "zcode.md Ladder precheck bullet anchored" grep -qF 'Ladder precheck' "$Z"
[ "$(grep -oF 'clocked-primitives-absent' "$Z" | wc -l | tr -d ' ')" -eq 2 ] || { echo "PIN FAIL: clocked-lane stand-down reason count"; fail=1; }
[ "$(grep -oF 'idle-primitive-absent' "$Z" | wc -l | tr -d ' ')" -eq 2 ] || { echo "PIN FAIL: idle-lane stand-down reason count"; fail=1; }
[ "$fail" -eq 1 ] && exit 1

# --- audit-lane pins (plan 2026-09-21-scheduler-maintenance-loop-quality-hygiene, Task 6) ---
# The same distinctive spans the plan's Validation Commands gate, pinned so a
# deletion of the operative audit-lane text fails (the spans landed in Tasks
# 1-5 of the same plan; Task 6 pins them, dated 2026-09-23). The lane
# paragraph's operative span is count-gated at exactly 1 whole-file (the
# Task 2 ledger entry paraphrases it and must never quote it). The
# friction_audit_cadence_days row and the execute|author|audit|retriage
# kind literal (the four-kind form; the retriage kind joined additively per
# plan 2026-09-26-origin-class-provenance-and-deferred-retriage-lane.md,
# Task 4) are quoted verbatim by the Task 2 Revisions-ledger entry, so bare presence
# greps would be satisfied by the ledger copy after an operative deletion;
# they are pinned region-scoped to their owning sections instead
# (Configuration table row: exactly 1; State file section: exactly 2, the
# children-entry schema line and the `pending_dispatch` field paragraph,
# both normative arms). The overlay's recipe heading is count-gated at
# exactly 1 (zcode.md carries no ledger copy). The Step 5
# dispatch-class-neutral rephrase span is count-gated to exactly 1
# region-scoped between the '### Step 5: scheduling' and
# '### Step 6: state update' headings, so the Task 5 sentence cannot be
# deleted or duplicated in the region without tripping the pin.
[ "$(grep -oF 'when due and lanes allow, dispatch at most one audit child' "$S" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: audit lane operative span count"; fail=1; }
python3 - "$S" "$Z" <<'EOF' || fail=1  # r7 F1: propagate the block status; without this the block is fail-open at the exit-code surface
import sys
s, z = open(sys.argv[1]).read(), open(sys.argv[2]).read()
def region(text, start, end, desc):
    if start not in text:
        print("PIN FAIL: %s region start anchor missing: %s" % (desc, start)); sys.exit(1)
    rest = text.split(start, 1)[1]
    if end not in rest:
        print("PIN FAIL: %s region end anchor missing: %s" % (desc, end)); sys.exit(1)
    return rest.split(end, 1)[0]
# the Configuration table row (the ledger entry quotes the key, so the pin
# is region-scoped to the Configuration section)
conf = region(s, "## Configuration (from facts document)", "\n## ", "Configuration")
n = conf.count("friction_audit_cadence_days")
if n != 1:
    print("PIN FAIL: friction_audit_cadence_days row count %d != 1 in the Configuration section" % n); sys.exit(1)
# the kind enum literal (exactly 2 normative arms: the children-entry schema
# line and the pending_dispatch field paragraph; the ledger copy sits
# outside this region). The four-kind literal supersedes the original
# three-kind count (plan
# 2026-09-26-origin-class-provenance-and-deferred-retriage-lane.md, Task 4:
# the retriage kind joined additively at both normative arms).
state = region(s, "## State file", "\n## ", "State file")
n = state.count("execute|author|audit|retriage")
if n != 2:
    print("PIN FAIL: execute|author|audit|retriage kind literal count %d != 2 in the State file section" % n); sys.exit(1)
# the Step 5 region's dispatch-class-neutral rephrase span
step5 = region(s, "### Step 5: scheduling", "### Step 6: state update", "Step 5")
n = step5.count("or the dispatch decision (for an idle-time dispatch)")
if n != 1:
    print("PIN FAIL: Step 5 rephrase span count %d != 1 in the Step 5 region" % n); sys.exit(1)
# the overlay's audit recipe section heading
n = z.count("## Audit recipe")
if n != 1:
    print("PIN FAIL: ## Audit recipe heading count %d != 1 in zcode.md" % n); sys.exit(1)
EOF
[ "$fail" -eq 1 ] && exit 1

# --- mechanical gates wiring pins (scheduler-maintenance-loop-quality-gates plan, Task 8) ---
# Needle spans below are unique to the OPERATIVE sentences (review r2 finding: changelog
# copies of a needle must never satisfy a pin), measured single-occurrence at pin time.
EP="$repo/agents/skills/execute-plan/SKILL.md"
MS="$repo/agents/skills/maintenance/SKILL.md"
RR="$repo/agents/skills/receiving-review/SKILL.md"
RP="$repo/agents/skills/review-plan/SKILL.md"
for f in "$EP" "$MS" "$RR" "$RP"; do
  [ -f "$f" ] || { echo "missing $f"; fail=1; }
done
[ "$fail" -eq 1 ] && exit 1
pin "origins-closure archive arm wired in execute-plan SKILL.md" grep -qF 'check_plan_origins_closed.py' "$EP"
pin "origins-block survey warn arm wired in maintenance SKILL.md" grep -qF 'Archived-coverage warn arm: an open top-level backlog item' "$MS"
pin "dirt regression merge arm wired in execution blueprint" grep -qF 'dirt_regression_gate.py --base' "$P"
pin "origins-closure blueprint archive-sentence duty wired" grep -qF 'origins-closure check (`python3' "$P"
pin "done dirt guard wired" grep -qF 'dirt_regression_gate.py' "$D"
pin "done review-thread closure gate wired" grep -qF 'review_thread_gate.py --marker' "$D"
pin "receiving-review review-thread marker duty wired" grep -qF 'write a review-thread marker at `docs/tmp/review-threads/<session-slug>.json` before posting any reply' "$RR"
pin "review-plan rule 5 vendored landing clause wired" grep -qF 'vendored-sync backlog item' "$RP"
# dfm r2 F1 successor (the archived gates left these producer steps ungated; the declaration-audit half lives on review-plan)
pin "dfm r2 F1 successor declaration audit producer step" grep -qF 'Declaration audit' "$RP"
# dfm r1 F6 successor (the archived gate's shorter needle was satisfied by the boundary sixth family without any pricing sentence)
pin "dfm r1 F6 successor narrowed contradiction pricing needle" grep -qF "contradicts the plan's content is blocking" "$RP"
pin "AGENTS.md vendored landing mirror clause wired" grep -qF 'land the vendored copy in the same run' "$A"
[ "$fail" -eq 1 ] && exit 1

# --- sequential landing discipline pins (plan
# 2026-09-22-sequential-landing-discipline-no-dispatch-before-squash, Task 5) ---
# Whole-file pins below cover operative spans; Revisions-ledger entries
# paraphrase, never quote, them (the four spans the Task 2 ledger entry did
# quote are region-scoped in the python block below per the r6 F1 fold;
# landed_path and branch_tip are deliberately not single-occurrence).
# Region-scoped and count pins live in the python block at the end of this
# section. Flip-probe outcomes for every pin here are recorded in the Task 5
# commit message body (each pin's failure direction simulated once against a
# mutated temp copy).
# the three fleet-invariant needles are region-scoped to the Invariants section
# in the python block below (the Task 1 Revisions ledger entry paraphrases them,
# so whole-file greps would be satisfied by the changelog copy)
pin "pending_landing schema literal" grep -qF '"pending_landing": null' "$S"
pin "pending_landing field paragraph opener" grep -qF 'is the deferred-landing intent record' "$S"
pin "record shape landed_path" grep -qF 'landed_path' "$S"
pin "record shape branch_tip" grep -qF 'branch_tip' "$S"
pin "record shape attempts" grep -qF '"attempts": 0' "$S"
pin "carry-forward opener unchanged" grep -qF 'carry forward the values' "$S"
pin "human-clear landing addition" grep -qF 'deletes the per-run note in the same action' "$S"
pin "completion-work gate set: gmail-author" grep -qF 'gmail-author' "$S"
pin "peer-byte guard" grep -qF "no staged path outside the branch's changed paths" "$S"
pin "labeled stash" grep -qF 'git stash push -m' "$S"
pin "stash untracked-flag prohibition" grep -qF 'never uses `-u`' "$S"
pin "stash failure path leaves stash in place" grep -qF 'leaves the stash in place' "$S"
pin "release on every completion-work exit" grep -qF 'every completion-work exit' "$S"
pin "index-preserving stash restore" grep -qF 'git stash pop --index' "$S"
# --- sequential landing discipline blueprint pins (prompt-templates.md) ---
pin "blueprint landed-commit verification" grep -qF 'verify the landed commit on main' "$P"
pin "successor own-landing conjunct" grep -qF 'its own landing is not verified on main' "$P"
pin "successor outstanding-record conjunct" grep -qF 'an outstanding pending_landing record' "$P"
pin "execution deferred-landing record lane literal" grep -qF '"lane": "execute"' "$P"
pin "authoring stranding record lane literal" grep -qF '"lane": "author"' "$P"
pin "lock-timeout record duty" grep -qF 'the lock-acquire timeout path' "$P"
pin "authoring record duty span" grep -qF 'before ending, write the pending_landing record' "$P"
pin "blueprint conflict cleanup" grep -qF 'git reset --merge' "$P"
pin "record-before-release ordering" grep -qF 'before releasing the lock' "$P"
pin "successor chain-nothing anchor intact" grep -qF 'Chain nothing, and end, when any of these holds' "$P"
python3 - "$S" "$P" <<'PYSEQ' || fail=1  # r7 F1: propagate the block status; without this the block is fail-open at the exit-code surface
import sys
s, p = open(sys.argv[1]).read(), open(sys.argv[2]).read()
fail = 0
def check(cond, desc):
    global fail
    if not cond:
        print("PIN FAIL: " + desc); fail = 1
# pending_landing must be named across schema, carry-forward, writer classes,
# Step 1, and Step 3 (whole-file count floor)
n = s.count("pending_landing")
check(n >= 5, f"pending_landing count {n} < 5 in SKILL.md")
# r6 F1 fold: the four needles below are quoted verbatim by the Task 2
# Revisions ledger entry, so they are pinned region-scoped to their owning
# regions (Step 5, State file section, Step 3) rather than whole-file
a = s.index("### Step 5: scheduling"); b = s.index("### Step 6: state update")
check("pre-dispatch landing gate" in s[a:b], "Step 5 region missing: pre-dispatch landing gate")
a = s.index("Each non-turn write is a targeted field edit"); b = s.index("- The `children` array")
check("re-evaluate their precondition" in s[a:b], "State file region missing: re-evaluate their precondition")
a = s.index("### Step 3: decision"); b = s.index("### Step 4: quota leg")
for needle in ["temporary worktree", "git reset --merge"]:
    check(needle in s[a:b], "Step 3 region missing: " + needle)
# Invariants-region needles (the fleet-rule bullet lives only there)
a = s.index("## Invariants"); b = s.index("## Revisions")
inv = s[a:b]
for needle in ["post-review, pre-landed state", "zero outstanding unlanded runs",
               "no surviving repo-matching"]:
    check(needle in inv, "Invariants region missing: " + needle)
# Step 1-region needles (the read-back and reconciliation bullets live only there)
a = s.index("### Step 1: survey"); b = s.index("### Step 2: guards")
st1 = s[a:b]
for needle in ["re-creates the pending_landing record from the note",
               "delete the note of the cleared record",
               "landed-commit test", "reflog", "re-targets",
               "pending-landing-orphaned"]:
    check(needle in st1, "Step 1 region missing: " + needle)
# ordering: the read-back anchor precedes the pending-dispatch reader opening,
# both inside the Step 1 region (fail-closed on either anchor missing)
check("run the landed-commit test for its" in st1, "Step 1 read-back anchor missing")
check("- Pending dispatch:" in st1, "Step 1 reader anchor missing")
if "run the landed-commit test for its" in st1 and "- Pending dispatch:" in st1:
    check(st1.index("run the landed-commit test for its") < st1.index("- Pending dispatch:"),
          "Step 1 read-back does not precede the pending-dispatch reader")
# Step 3-region needles (the landing gate and completion work live only there)
a = s.index("### Step 3: decision"); b = s.index("### Step 4: quota leg")
st3 = s[a:b]
for needle in ["landing-completion",
               "pending-landing (primary occupied by peer session)",
               "pending-landing (outstanding unlanded run)",
               "pending-landing-stuck", "pending-landing-stash-left",
               "re-runs the same gate set"]:
    check(needle in st3, "Step 3 region missing: " + needle)
# blueprint body-scoped counts (per the F8 precedent: the deviation-list
# paraphrase must never satisfy a body count). The authoring body runs from
# the '## Authoring child' heading to the '## Execution child' heading; the
# execution body runs from there to end of file.
aa = p.index("## Authoring child"); ea = p.index("## Execution child")
auth, exe = p[aa:ea], p[ea:]
for name, body in (("authoring", auth), ("execution", exe)):
    c = body.count("pending-landing-<plan-slug>")
    check(c == 1, f"{name} blueprint pending-landing-<plan-slug> count {c} != 1")
g = p.count("never overwrites an existing record")
check(g >= 2, f"occupied-field guard count {g} < 2 in prompt-templates.md")
ga, ge = auth.count("never overwrites an existing record"), exe.count("never overwrites an existing record")
check(ga >= 1 and ge >= 1, f"occupied-field guard body counts author={ga} execute={ge}")
if fail:
    sys.exit(1)
PYSEQ
[ "$fail" -eq 1 ] && exit 1

# --- quota-blind dispatch primitive choice pins (plan
# 2026-09-21-quota-blind-dispatch-primitive-choice, Task 4) ---
# Pins for the quota-state-aware authoring carrier selection, the grep-able
# quota_signal record token, and the idle authoring payload's
# re-verification stand-down gate. Presence pins are fixed-string greps in
# the file's standard idiom. Two pins deviate from plain whole-file greps,
# each for a reason this plan's own Task 4 wording requires, implemented in
# the file's closest established idiom:
#   - "carrier-selection rule present": the Revisions ledger entry quotes the
#     gate 1 span verbatim, so a whole-file grep would stay green when the
#     operative D2 rule sentence is deleted, and the Task 4 mutation probe
#     (removing that sentence) must flip the pin; it is therefore pinned
#     region-scoped to the Step 3 decision region in the python block below
#     (the r2 F7 precedent for ledger-carried spans).
#   - "covered-stand-down marker schema parity": exactly-once per file is
#     required (the SKILL.md machine-test prescription and the blueprint's
#     write prescription must not drift), so the carve-out block's count
#     idiom is used, one count pin per file, instead of an exists-style grep.
pin "authoring payload re-verification gate" grep -qF 're-verify the target backlog item still sits at the backlog top level and is still plan-uncovered' "$P"
pin "quota signal token documented" grep -qF 'quota_signal=' "$S"
pin "in-session marker documented" grep -qF '(in-session)' "$S"
pin "decision-time probe binding" grep -qF 'the signal is derived at decision time' "$S"
pin "in-session lane hold branch" grep -qF 'idle-listing attribution inapplicable' "$S"
pin "quota signal slug vocabulary" grep -qF 'probe-scarce, probe-near-reset' "$S"
[ "$(grep -oF '{"item": "<backlog item path>", "reason": "<covered|gone>", "date": "<iso date>"}' "$S" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: covered-stand-down marker schema parity (SKILL.md) count != 1"; fail=1; }
[ "$(grep -oF '{"item": "<backlog item path>", "reason": "<covered|gone>", "date": "<iso date>"}' "$P" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: covered-stand-down marker schema parity (prompt-templates.md) count != 1"; fail=1; }
python3 - "$S" <<'EOF' || fail=1  # r7 F1: propagate the block status; without this the block is fail-open at the exit-code surface
import sys
s = open(sys.argv[1]).read()
if "### Step 3: decision" not in s or "### Step 4" not in s:
    print("PIN FAIL: carrier-selection rule region anchors missing (Step 3/Step 4)"); sys.exit(1)
step3 = s.split("### Step 3: decision")[1].split("### Step 4")[0]
if "quota-state-aware carrier-selection rule" not in step3:
    print("PIN FAIL: carrier-selection rule present (the operative D2 sentence is gone from the Step 3 decision region; the Revisions ledger quotes the span, so a whole-file grep cannot guard it)"); sys.exit(1)
EOF
rc=$?
[ "$rc" -ne 0 ] && fail=1
# --- P54 park-discharge duty pins (plan 2026-09-24-p54-scheduler-loop-continuity-directives.md Task 2) ---
pin "P54 able-session predicate literal" grep -qF 'able-session predicate' "$S"
pin "P54 discharge field predicate" grep -qF 'pending_rearm or pending_dispatch' "$S"
pin "P54 discharge duty anchor" grep -qF 'park-discharge duty' "$S"
pin "P54 discharge operative phrase" grep -qF 'discharges the parked intents in the same session before ending, guard-bound' "$S"
[ "$(grep -cF 'CLOSING PARK DISCHARGE DUTY' "$P")" -eq 3 ] || { echo "PIN FAIL: blueprint discharge anchor count != 3"; fail=1; }
# 2026-09-25 parked-dependency visibility Task 6: the new unblock wrapper is
# count-pinned at exactly one opener beside the existing wrapper-count pin
pin "parked-dependency unblock wrapper count" test "$(grep -oF '<prompt for the parked-dependency unblock session>' "$P" | wc -l | tr -d ' ')" -eq 1
# --- parked-dependency visibility pins (plan 2026-09-25-parked-dependency-visibility.md Task 6) ---
pin "parked_dependencies schema literal" grep -qF '"parked_dependencies": [],' "$S"
pin "parked_dependencies field paragraph opener" grep -qF 'parked_dependencies is the ordered array of parked-dependency ledger entries' "$S"
pin "parked_dependencies occurrence floor" test "$(grep -oF 'parked_dependencies' "$S" | wc -l | tr -d ' ')" -ge 5
pin "parked-dependency survey arm anchor" grep -qF 'parked-dependency liveness arm' "$S"
pin "parked-dependency survey state vocabulary" grep -qF 'waiting, stale, or actionable' "$S"
pin "D1 live-entry skip span" grep -qF 'live parked_dependencies entry' "$S"
pin "parked-dependency carry-forward span" grep -qF 'plus `parked_dependencies` (the boundary-write, unblock-clear, and survey-clear writers above, so the rewrite must carry the field)' "$S"
pin "execute-plan boundary-writer span" grep -qF 'parked-dependency ledger entry' "$E"
pin "unblock-template opener span" grep -qF 'parked-dependency unblock dispatch' "$P"
pin "dependency-branch landing-race discipline span" grep -qF 'actual pre-landing main' "$P"
pin "Step 5 unblock-dispatch slice sentence" grep -qF "the content of the unblock template's own" "$S"
pin "SUCCESSOR DISPATCH amended skip clause" grep -qF 'a live `parked_dependencies` entry (any entry not yet cleared by the State file field paragraph' "$P"
pin "deferred landing-duty dependency-branch record identity" grep -qF 'Dependency-landing record identity' "$P"
pin "unblock-child progress witness span" grep -qF 'manifest refreshes count as progress for unblock children' "$S"
pin "lane-hold unblock completion-evidence span" grep -qF 'ledger entry cleared plus the serialized plan present in `execution_queue`' "$S"
pin "deferred outcome_reason schema note value" grep -qF 'the value `deferred` per the parked-dependency unblock deferral' "$S"
# --- P54 execution queue and priority pins (plan ... Task 3) ---
pin "P54 execution_queue schema line" grep -qF '"execution_queue": []' "$S"
pin "P54 execution_priority schema line" grep -qF '"execution_priority": null' "$S"
pin "P54 park-first anchor in execution blueprint" grep -qF 'Park-first chaining' "$P"
python3 - "$S" <<'EOF' || fail=1
import sys
s = open(sys.argv[1]).read()
cf = [l for l in s.split("\n") if "carry forward" in l]
if not cf or "execution_queue" not in cf[0] or "execution_priority" not in cf[0]:
    print("PIN FAIL: P54 execution_queue/execution_priority absent from the Step 6 carry-forward list"); sys.exit(1)
EOF
rc=$?
[ "$rc" -ne 0 ] && fail=1
# --- P54 dedup guard and execution claims pins (plan ... Task 4) ---
pin "P54 duplicate-user-directed-dispatch tripwire" grep -qF 'duplicate-user-directed-dispatch' "$S"
pin "P54 user-directed negative-shape payload-opening prefix" grep -qF 'You are an unattended scheduled session in the repository at' "$S"
pin "P54 execution-claims directory in discovery arm" grep -qF 'execution-claims' "$S"
pin "P54 blueprint claim duty anchor" grep -qF 'EXECUTION CLAIM' "$P"
# --- P54 needs-recert pin (plan ... Task 5), region-scoped to the Step 3 decision region ---
python3 - "$S" <<'EOF' || fail=1
import sys
s = open(sys.argv[1]).read()
if "### Step 3: decision" not in s or "### Step 4" not in s:
    print("PIN FAIL: P54 Step 3 region anchors missing"); sys.exit(1)
step3 = s.split("### Step 3: decision")[1].split("### Step 4")[0]
if "needs-recert" not in step3:
    print("PIN FAIL: P54 needs-recert literal absent from the D1 region"); sys.exit(1)
EOF
rc=$?
[ "$rc" -ne 0 ] && fail=1
# --- P54 needs-recert pin block end marker (plan ... Task 5; comment label corrected 2026-09-24 review r4) ---
[ "$fail" -eq 1 ] && exit 1

# --- duplicate-parent tripwire migration arm pins (plan
# 2026-09-23-p50-scheduler-state-durability-leftovers.md, Task 3) ---
# Count-gated pins for the tripwire's migration arm: the Step 3 arm bullet's
# dated anchor (pinned by the disambiguated span, unique whole-file after the
# writer join names the arm in the two closed enumerations), the delete-leg
# span, the retitle-leg span, the Revisions ledger span, and the zcode.md
# pointer. Each span occurs exactly once in its file (measured on the
# post-Task-3 tree), so a count of exactly 1 fails both a deletion of the
# operative text and a stray duplicate copy; the ledger span is count-gated
# so a future ledger entry naming the plan again cannot re-satisfy a
# presence-only grep. Freeze-literal origins (the spans' owning text; a
# legitimate wording change reconciles the pin and the text in the same
# edit and records the superseding origin):
#   'Duplicate-parent migration arm (added 2026-09-23' (SKILL.md): the Step 3
#       arm bullet's dated anchor of plan
#       2026-09-23-p50-scheduler-state-durability-leftovers.md Task 3; the
#       "(added 2026-09-23" tail disambiguates it from the two writer-join
#       entries ("the Duplicate-parent migration arm" in the rearm_note
#       Writers list and the scheduler-turn write-mode enumeration).
#   'the leg is a delete of the old-form record targeted by its listed id'
#       (SKILL.md): the carrier-live leg's operative span (same plan Task 3).
#   'retimes and retitles the old-form record per the cadence rule'
#       (SKILL.md): the no-live-carrier leg's operative span (same plan
#       Task 3).
#   '2026-09-23: the duplicate-parent tripwire gained the migration arm'
#       (SKILL.md): the Revisions ledger entry's dated span (same plan
#       Task 3).
#   'the migration arm (SKILL.md Step 3)' (zcode.md): the tripwire
#       description bullet's pointer sentence naming the arm's owning bullet
#       (same plan Task 3).
[ "$(grep -oF 'Duplicate-parent migration arm (added 2026-09-23' "$S" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: migration arm Step 3 anchor count != 1"; fail=1; }
[ "$(grep -oF 'the leg is a delete of the old-form record targeted by its listed id' "$S" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: migration arm delete-leg span count != 1"; fail=1; }
[ "$(grep -oF 'retimes and retitles the old-form record per the cadence rule' "$S" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: migration arm retitle-leg span count != 1"; fail=1; }
[ "$(grep -oF '2026-09-23: the duplicate-parent tripwire gained the migration arm' "$S" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: migration arm ledger span count != 1"; fail=1; }
[ "$(grep -oF 'the migration arm (SKILL.md Step 3)' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: migration arm zcode.md pointer count != 1"; fail=1; }
[ "$fail" -eq 1 ] && exit 1

# --- per-execution worktree field and per-run read pins (plan
# 2026-09-24-p57-per-execution-worktree-isolation.md, Task 1) ---
# Companion pins for the additive children[] `worktree` field and the per-run
# read sites. Each pin below is a dedicated fixed-string grep that fails when
# its span is deleted (spans S1, S2, S3, S4, S5, S21 of the plan's Validation
# Commands, against SKILL.md). The schema-block half (the parsed children[0]
# carries a "worktree" key with value null and schema stays 4) lives in the
# first SKILL.md python block beside the existing children-entry fields pin,
# mirroring that block's block-parse mechanism.
pin "P57 S1 worktree field paragraph" grep -qF 'once its blueprint-created per-execution worktree exists' "$S"
pin "P57 S2 progress-mark per-run clause" grep -qF "resolved inside the entry's recorded \`worktree\` when that additive field is set" "$S"
pin "P57 S3 ingestion per-run clause" grep -qF 'the same repository-relative manifest path inside the recorded worktree' "$S"
pin "P57 S4 fast re-dispatch per-run clause" grep -qF 'the same per-run resolution the rate-limited ingestion bullet applies' "$S"
pin "P57 S5 sanctioned-writer own-record clause" grep -qF 'own-record per-run worktree recording' "$S"
pin "P57 S21 ref-based archival read" grep -qF 'the archival arm is read ref-based' "$S"
[ "$fail" -eq 1 ] && exit 1

# --- interim-constraint retirement and fleet/merge-order policy pins (plan
# 2026-09-24-p57-per-execution-worktree-isolation.md, Task 2) ---
# Companion pins for the operative flip of the execution-lane stance. S7 and S8
# live outside the stance section (the Step 2 fleet-cap bullet and the
# Invariants fleet-cap bullet), so their pins are file-scoped; S9 lives in the
# Execution-lane concurrency stance section, so its pin is region-scoped with
# the same awk region the plan's Validation Commands use (a Revisions-ledger
# paraphrase must not satisfy it). Both absence pins are case-sensitive
# fixed-string checks with the three-way polarity above (rc 1 = clean), so the
# P54 Revisions ledger entry's lowercase historical wording cannot satisfy or
# break them; the S10 count is exactly-once so a duplicated ledger entry fails.
pin "P57 S7 fleet-cap execution-isolation sentence" grep -qF 'EXECUTION ISOLATION (landed 2026-09-24, P57' "$S"
pin "P57 S8 Invariants worktree-isolated fleet-member clause" grep -qF 'execution children run in per-execution ad-hoc worktrees per the Worktree-first standard' "$S"
pin "P57 S9 stance rework-executed lead-in (region-scoped)" bash -c "awk '/^### Execution-lane concurrency stance/{f=1; next} /^## Revisions/{f=0} f' \"$S\" | grep -qF 'REWORK EXECUTED (landed 2026-09-24, P57'"
pin "P57 S9 stance overlap-shapes tail (region-scoped)" bash -c "awk '/^### Execution-lane concurrency stance/{f=1; next} /^## Revisions/{f=0} f' \"$S\" | grep -qF 'up to four concurrent children across mixed kinds with executions worktree-isolated'"
expect_absent "retired INTERIM EXECUTION CONSTRAINT heading must be absent from SKILL.md (the ledger's lowercase historical wording must not satisfy or break this)" 'INTERIM EXECUTION CONSTRAINT' "$S"
expect_absent "superseded Until-P57 sanctioned-overlap-shapes sentence must be absent from SKILL.md" 'Until P57, the sanctioned overlap shapes' "$S"
[ "$(grep -cF '2026-09-24 (P57 per-execution worktree isolation' "$S")" -eq 1 ] || { echo "PIN FAIL: P57 Revisions ledger date string count != 1"; fail=1; }
[ "$fail" -eq 1 ] && exit 1

# --- runtime overlay execution-lane flip pins (plan
# 2026-09-24-p57-per-execution-worktree-isolation.md, Task 3) ---
# Companion pins for the overlay's two flipped clauses (the child-classification
# markers bullet and the dispatch ladder's never-routed-in-session
# parenthetical). Both absence pins are fixed-string checks with the three-way
# polarity above (rc 1 = clean), so the retired interim wording cannot return
# anywhere in zcode.md and a grep error cannot read as clean; the S11/S12
# presence pins are dedicated fixed-string greps that fail when their span is
# deleted.
expect_absent "retired execution-lane-stays-single interim wording must be absent from zcode.md" 'stays single until P57' "$Z"
expect_absent "retired one-in-flight-hold interim wording must be absent from zcode.md" 'holds at one in-flight child until P57' "$Z"
pin "P57 S11 zcode markers worktree-isolated fleet clause" grep -qF 'execution children in their per-execution worktrees, P57' "$Z"
pin "P57 S12 zcode ladder single-child-hold-retired clause" grep -qF 'retired 2026-09-24 by P57' "$Z"
[ "$fail" -eq 1 ] && exit 1

# --- execution blueprint per-execution worktree pins (plan
# 2026-09-24-p57-per-execution-worktree-isolation.md, Task 4; dispositions
# re-keyed by the worktree-first standard consolidation, plan
# 2026-09-28-worktree-first-standard-only-mode.md Task 4) ---
# The 2026-09-28 consolidation replaced the blueprint's per-execution
# worktree paragraph and its per-run pre-work gate paragraph with references
# to the Worktree-first standard section in the execute-plan skill, retiring
# the P57 payload spans: S13 (the execution create-literal count) and the
# authoring create-literal count became wrap-tolerant freeze-absent pins (the
# create commands are canonical-section owned; the retired literals must not
# return); S14 (the Linked-worktree bootstrap recipe span pin) is dropped
# (that recipe name was REMOVED from the skill by that plan's Task 2, not
# folded under it; the canonical section's Transfer-in implementation is the
# successor span, and scripts/test_execute_plan_worktree_bootstrap.py is that
# span's operative guard, so no span pin remains here to protect); S15 is
# re-keyed on the rewritten per-run pre-work gate span. The
# new authoring reference span is count-gated exactly-once whole-file for the
# same reason the old authoring create literal was: a stray copy anywhere
# would degenerate the suite's auth_bodies identification above (the
# authoring-body python filter keys on it); the count itself lives in the
# python block beside that filter as a normalized count (r2 F5), replacing
# the line-bound grep this block used to carry. The execution and unblock
# bodies' own worktree-first reference sentences are pinned exactly-once
# (wrap-tolerant) and body-scoped in the python block above (consolidation
# review r1 F3), so wholesale deletion of either paragraph fails the suite.
expect_absent_flat "retired execution worktree create literal must be absent from prompt-templates.md (wrap-tolerant; superseded 2026-09-28 by the worktree-first consolidation)" 'git worktree add -b <execution-branch> <sibling-path> <default-branch>' "$P"
expect_absent_flat "retired authoring worktree create literal must be absent from prompt-templates.md (wrap-tolerant; superseded 2026-09-28 by the worktree-first consolidation)" 'git worktree add -b YYYY-MM-DD-authoring-<slug> <sibling-path> <default-branch>' "$P"
expect_absent_flat "retired authoring payload worktree create literal must be absent from prompt-templates.md (wrap-tolerant; superseded 2026-09-28 by the worktree-first consolidation)" 'git worktree add -b <date>-authoring-<slug> <sibling-path> <default-branch>' "$P"
pin "per-run pre-work gate span (re-keyed 2026-09-28; was P57 S15)" grep -qF "the run's own per-worktree done lock is free" "$P"
[ "$fail" -eq 1 ] && exit 1

# --- execution blueprint dual-arm landing and per-worktree archive pins (plan
# 2026-09-24-p57-per-execution-worktree-isolation.md, Task 5) ---
# Companion pins for the blueprint's dual-arm landing rework (S16, S17, S18)
# and the per-run archive and done-lock scoping spans (S19, S20). S17-S20 are
# dedicated fixed-string presence greps that fail when their span is deleted;
# S16 is tightened (review-panel r1) from the bare `merge --squash <branch>`
# presence grep to exactly-once counts of the full primary-arm literal and of
# the temp arm's bare form (the prefixed form does not contain the bare
# substring: `git -C <default-checkout> ` intervenes, so the two counts are
# disjoint).
# The merge-wait-acquire exactly-2 count pin (each blueprint acquires the merge
# landing lock once) already lives in the blueprint integrity block above and
# continues to pass unchanged. The superseded shared-checkout Phase 0 clause is
# frozen absent with the wrap-tolerant flattened form (expect_absent_flat
# above): the clause was line-wrapped in the file, so the plain line-oriented
# expect_absent is a no-op against the wrapped bytes and must not be used here.
[ "$(grep -oF 'git -C <default-checkout> merge --squash <branch>' "$P" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: P57 S16 primary-arm prefixed squash command count != 1"; fail=1; }
[ "$(grep -oF 'git merge --squash <branch>' "$P" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: P57 S16 temp-arm bare squash command count != 1"; fail=1; }
pin "P57 S17 temp-worktree arm create command" grep -qF 'git worktree add --detach <temp-path> refs/heads/<default>' "$P"
pin "P57 S18 compare-and-swap landing command" grep -qF 'git update-ref refs/heads/<default> <new-tip> <old-tip>' "$P"
pin "P57 S19 archive per-run worktree commit span" grep -qF 'the archive commit is a per-run worktree commit' "$P"
pin "P57 S20 done-lock per-run scoping span" grep -qF "so the run's done lock is its own" "$P"
expect_absent_flat "superseded shared-checkout Phase 0 clause must be absent from prompt-templates.md (wrap-tolerant)" 'Phase 0 dedicated branch from main' "$P"
[ "$fail" -eq 1 ] && exit 1

# --- review r1 fleet-stance straggler fold pins (plan
# 2026-09-24-p57-per-execution-worktree-isolation.md, review-panel r1 fold) ---
# Companion pins for the two strictly-sequential stragglers the Task 1-3 flip
# spans missed: the G1a lane bullet's execution-sequencing sentence and the D2
# carrier-selection parenthetical, both reworded to the fleet-member stance.
# The presence pins are dedicated fixed-string greps that fail when their span
# is deleted; the absence pins are case-sensitive fixed-string checks with the
# three-way polarity above (rc 1 = clean). The G1a absence literal is the live
# sentence's unique full form: its bare prefix also occurs in the Revisions
# ledger's historical 2026-09-15 entry ("never two at once"), so the
# file-scoped check pins the longer form and the ledger's historical wording
# can neither satisfy nor break it.
pin "P57 r1 G1a fleet-member sequencing sentence" grep -qF 'Executions are fleet members and may overlap, each in its own per-execution worktree' "$S"
pin "P57 r1 D2 carrier sequencing-superseded parenthetical" grep -qF "sequencing superseded 2026-09-24 by P57's per-execution worktree isolation" "$S"
expect_absent "retired strictly-sequential execution sentence must be absent from SKILL.md (the ledger's historical wording must not satisfy or break this)" 'Executions are strictly sequential (never two in flight)' "$S"
expect_absent "retired strictly-sequential clocked-child stance parenthetical must be absent from SKILL.md" 'strictly sequential clocked-child stance is unchanged' "$S"
[ "$fail" -eq 1 ] && exit 1


# --- Live-vs-archive basename gate (plans-lifecycle integrity, 2026-09-25) ---
# Additive read-only section: for each live root, assert no basename also
# exists in its archive subtrees (completed/, deferred/, rejected/ where
# present). PINS_DUPLICATE_ROOT overrides the scanned root for THIS section
# only (fixture proving); the default root is the git toplevel exactly as
# every pinned span above uses. Implemented as a function taking the root as
# its argument so the inline selftest below can call it directly on a fixture
# (never a whole-suite re-invocation, which would die for the wrong reason on
# a temp fixture or recurse on an in-repo one).
# Landing-time net over the plans home: gate_plans_archive_twin in
# scripts/done_sweep_gates_lib.py (dated plan basenames only, facts-key
# driven). This section stays the corpus-wide scheduled owner (plans AND
# backlog roots, non-dated names included) and is the designated absorber
# of the two-state-directories-no-root-copy edge that gate does not cover.
check_live_vs_archive_duplicates() { # $1 = root to scan
  local root="$1"
  local live_root archive_dir base rc=0
  for live_root in "docs/history/backlog" "docs/history/plans"; do
    [ -d "$root/$live_root" ] || continue
    # Collect archive basenames under the root's archive subtrees.
    for archive_dir in completed deferred rejected; do
      [ -d "$root/$live_root/$archive_dir" ] || continue
      while IFS= read -r base; do
        [ -n "$base" ] || continue
        if [ -f "$root/$live_root/$base" ]; then
          echo "PIN FAIL: live-vs-archive basename twin: $live_root/$base also archived at $live_root/$archive_dir/$base"
          rc=1
        fi
      done < <(find "$root/$live_root/$archive_dir" -name "*.md" -type f -exec basename {} \;)
    done
  done
  return "$rc"
}

DUPLICATE_ROOT="${PINS_DUPLICATE_ROOT:-$repo}"
if ! check_live_vs_archive_duplicates "$DUPLICATE_ROOT"; then
  fail=1
fi

# Lasting failure-arm guard: run the same function against a synthetic
# fixture (a live basename duplicated into a fake archive subtree) and
# require the non-zero result and the offending-pairs message naming the
# fixture pair; a selftest failure fails the suite.
DUPLICATE_FIXTURE="$(mktemp -d "${TMPDIR:-/tmp}/pins-duplicate-fixture.XXXXXX")"
mkdir -p "$DUPLICATE_FIXTURE/docs/history/backlog/completed" "$DUPLICATE_FIXTURE/docs/history/backlog"
echo fixture > "$DUPLICATE_FIXTURE/docs/history/backlog/completed/2026-01-01-fake-twin.md"
echo fixture > "$DUPLICATE_FIXTURE/docs/history/backlog/2026-01-01-fake-twin.md"
DUPLICATE_OUT="$(check_live_vs_archive_duplicates "$DUPLICATE_FIXTURE" 2>&1)"
DUPLICATE_RC=$?
rm -rf "$DUPLICATE_FIXTURE"
if [ "$DUPLICATE_RC" -eq 0 ]; then
  echo "PIN FAIL: live-vs-archive selftest: synthetic twin pair did not fail (rc 0)"
  fail=1
elif ! printf '%s' "$DUPLICATE_OUT" | grep -q "2026-01-01-fake-twin.md"; then
  echo "PIN FAIL: live-vs-archive selftest: refusal output does not name the fixture pair"
  fail=1
fi

[ "$fail" -eq 1 ] && exit 1

# --- quota display staleness and refresh-cadence pins (plan
# 2026-09-25-quota-display-refresh-cadence.md) ---
[ "$(grep -oF 'Sidebar display staleness and operator refresh cadence' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: quota sidebar-staleness bullet count != 1"; fail=1; }
[ "$(grep -oF 'Quota display caveat' "$S" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: quota display caveat bullet count != 1"; fail=1; }
[ "$fail" -eq 1 ] && exit 1

# --- execution queue-drain turn-end and taxonomy-parity pins (plan
# 2026-09-25-execution-lane-queue-drain-continuation.md) ---
[ "$(grep -oF 'a request for the user to confirm starting the next plan is never a sanctioned turn end' "$D" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: queue-drain turn-end bullet count != 1"; fail=1; }
[ "$(grep -oF 'a guard fire (a quota pause or near-reset with the Budget gate' "$E" | wc -l | tr -d ' ')" -eq 1 ] && [ "$(grep -oF 'a guard fire (a quota pause or near-reset with the Budget gate' "$D" | wc -l | tr -d ' ')" -eq 1 ] && [ "$(grep -oF 'a landing-gate hold reported by `scripts/done-lock.sh` merge-status, a lane hold from the scheduler guards, provider rate pressure with its structured rate-limited end) or an empty queue (no digest-intact open plan remains); a user interrupt or explicit abort is always sanctioned as well' "$E" | wc -l | tr -d ' ')" -eq 1 ] && [ "$(grep -oF 'a landing-gate hold reported by `scripts/done-lock.sh` merge-status, a lane hold from the scheduler guards, provider rate pressure with its structured rate-limited end) or an empty queue (no digest-intact open plan remains); a user interrupt or explicit abort is always sanctioned as well' "$D" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: queue-drain taxonomy parity span count != 1"; fail=1; }
[ "$fail" -eq 1 ] && exit 1

# --- execution-lane carrier-selection ordering pins (plan
# 2026-09-26-p64-execution-lane-liveness-long-session-continuity.md, Task 1) ---
# Companion pins for the execution lane's ordered carrier ladder (the SKILL.md
# Step 3 ordering bullet and the zcode.md Execution-lane fallback legs bullet).
# Presence pins are dedicated fixed-string greps that fail when their span is
# deleted; the ordering sequence is count-gated at exactly once whole-file in
# SKILL.md (the grep -oF | wc -l count form), so the Task 1 Revisions-ledger
# entry or any later edit restating the sequence verbatim fails the suite.
# Absence pins are case-sensitive fixed-string checks with the three-way
# polarity above (rc 1 = clean, rc >= 2 = grep error fails), freezing the four
# retired absolute wordings out of their files; the deleted idle-dispatched
# presence pin's retirement is owned by the no-clock absence pin below.
pin "Execution-lane carrier-selection ordering present" grep -qF 'Execution-lane carrier-selection ordering' "$S"
pin "ordering sequence literal present" grep -qF 'clocked, then idle, then in-session, then park-with-carrier' "$S"
pin "ordering sequence exactly-once count" test "$(grep -oF 'clocked, then idle, then in-session, then park-with-carrier' "$S" | wc -l | tr -d ' ')" -eq 1
pin "in-session execution dispatch leg present" grep -qF 'in-session execution dispatch' "$S"
pin "Execution-lane fallback legs overlay bullet present" grep -qF 'Execution-lane fallback legs' "$Z"
pin "park launchd resume-carrier pairing present" grep -qF 'pairs the park with the launchd resume carrier' "$Z"
expect_absent "retired execution-lane never-routed-in-session wording must be absent from SKILL.md" 'the execution lane is never routed in-session' "$S"
expect_absent "retired overlay never-routes-in-session wording must be absent from zcode.md" 'The execution lane never routes in-session' "$Z"
expect_absent "retired no-clock execution dispatch wording must be absent from SKILL.md" 'never dispatched through a primitive without a clock' "$S"
expect_absent "retired clocked-only trap-sentence wording must be absent from zcode.md" 'stays clocked-only' "$Z"
[ "$fail" -eq 1 ] && exit 1

# --- task-boundary checkpoint duty and queue-drain fold pins (plan
# 2026-09-26-p64-execution-lane-liveness-long-session-continuity.md, Task 3) ---
# Companion pins for the task-boundary checkpoint duty and the densified
# execution-claim refresh record. The two P pins are count-gated at exactly
# once whole-file (the grep -oF | wc -l count form) so the deviation-ledger
# entry (which names the anchors by description only) or any stray duplicate
# copy fails the suite; the E presence pins are dedicated fixed-string greps
# that fail when their span is deleted. The header-loop presence pin guards the
# pins suite's own $E existence check (a missing execute-plan SKILL.md must
# fail loudly as missing, not as per-pin grep errors). The absence pin is a
# case-sensitive fixed-string check with the three-way polarity above
# (rc 1 = clean, rc >= 2 = grep error fails), freezing the retired
# one-execution-child guard wording out of the execute-plan skill after the
# queue-drain fold named the asserted-unchanged guard family instead.
# 2026-09-28 continuation policy plan: duty renamed TASK-BOUNDARY CHECKPOINT
pin "execution blueprint task-boundary checkpoint paragraph anchor" test "$(grep -oF 'TASK-BOUNDARY CHECKPOINT' "$P" | wc -l | tr -d ' ')" -eq 1
pin "densified execution-claim refresh record exactly-once" test "$(grep -oF 'at every task completion inside the implementation loop' "$P" | wc -l | tr -d ' ')" -eq 1
# 2026-09-28 continuation policy plan: mirrored duty rename in execute-plan
pin "execute-plan task-boundary checkpoint duty policy anchor" grep -qF 'Task-boundary checkpoint duty' "$E"
pin "queue-drain fold names the asserted-unchanged guard family" grep -qF 'lane guard and the P54 fleet cap' "$E"
pin "pins header existence loop covers E" grep -qE '^for f in "\$S" "\$Z" "\$P" "\$D" "\$E"; do$' "${BASH_SOURCE[0]}"
expect_absent "retired one-execution-child guard wording must be absent from the execute-plan skill" 'one-execution-child guard' "$E"
[ "$fail" -eq 1 ] && exit 1

# --- deferred-corpus re-triage lane pins (plan
# 2026-09-26-origin-class-provenance-and-deferred-retriage-lane.md, Task 4) ---
# Companion pins for the lane's operative spans: the consult bullet's
# distinctive fragment, the contention clause's sanctioned must-dispatch
# reason literal, the zcode.md recognition literal, the fleet-cap
# enumerations (zcode.md's fleet-cap sentence and the SKILL.md Step 2
# fleet-cap guard), and the prompt-templates retriage pointer stub. The
# consult bullet's fragment is count-gated at exactly 1 whole-file (the
# Revisions ledger entry names the lane but never quotes the fragment), so
# a ledger or stub copy can never satisfy the pin after an operative
# deletion. The reason literal is likewise exactly-once (the contention
# bullet is its only operative home).
pin "deferred-corpus re-triage consult bullet present" grep -qF 'Deferred-corpus re-triage consult: read the re-triage record' "$S"
pin "deferred-corpus re-triage consult bullet exactly-once" test "$(grep -oF 'Deferred-corpus re-triage consult' "$S" | wc -l | tr -d ' ')" -eq 1
pin "retriage-lane-due reason literal present" grep -qF 'retriage-lane-due' "$S"
pin "retriage-lane-due reason literal exactly-once" test "$(grep -oF 'retriage-lane-due' "$S" | wc -l | tr -d ' ')" -eq 1
pin "zcode.md re-triage child recognition literal" grep -qF 'deferred re-triage lane' "$Z"
pin "zcode.md fleet-cap enumeration widened to the re-triage kind" grep -qF 'authoring, audit, re-triage, and execution children are fleet members' "$Z"
pin "SKILL.md Step 2 fleet-cap enumeration widened to the re-triage kind" grep -qF 'like the authoring, audit, and re-triage kinds' "$S"
pin "prompt-templates retriage pointer stub present" grep -qF 'deferred re-triage lane' "$P"
[ "$fail" -eq 1 ] && exit 1

# --- authoring-lane target-distinctness pins (plan
# 2026-09-28-maintenance-autonomous-pipeline.md, Task 1) ---
# The 2026-09-28 09:32 stand-down (the authoring lane stood down beside a live
# peer's claim without checking the candidate target's distinctness, while a
# standing user directive to keep authoring was recorded) is the witness for
# rewriting the authoring-vs-authoring clause into the target-distinctness
# rule. The rule's home sentence is count-gated at exactly 1 whole-file: the
# discovery arm, the D2 guard-resolution sentence, and the rolling-log
# dispatch clause all reference the rule by name, so a restatement anywhere
# would create a second home. The carve-out pin covers the arms inheritance
# sentence (the release condition for the state-file, armed, fired, and
# widened arms), and the two exclusivity pins hold the audit-child and
# re-triage-child spans the rewrite had to preserve byte-for-byte in meaning.
pin "G1a target-distinctness rule home sentence" grep -qF 'does not hold the lane when the targets are distinct' "$S"
pin "G1a target-distinctness home sentence exactly-once" test "$(grep -oF 'does not hold the lane when the targets are distinct' "$S" | wc -l | tr -d ' ')" -eq 1
pin "G1a arms target-distinctness carve-out" grep -qF "releases when the recorded or listed child's target is distinct from the candidate target and the standing-directive sanction exists" "$S"
pin "G1a audit-child exclusivity span preserved" grep -qF 'an audit child never runs alongside an authoring child or another audit child' "$S"
pin "G1a re-triage-child exclusivity span preserved" grep -qF 'never runs alongside an authoring child, another re-triage child, or an audit child' "$S"
[ "$fail" -eq 1 ] && exit 1

# --- stall-class recovery pins (plan
# 2026-09-28-maintenance-autonomous-pipeline.md, Task 4) ---
# Companion pins for the stall-class recovery spans: the Step 0 re-arm
# discharge precedence (a timing amendment of the Step 1 park-discharge duty,
# the turn discharging parked re-arm records before the survey; the
# pending_dispatch half stays owned by the Step 1 duty, so the pins hold the
# cross-reference instead of a duplicate), the Step 6 completion-stranding
# detection (the turn_error literal plus the wide explanation predicate that
# never trips a healthy loop: a within-one-cadence armed carrier and a
# reset-window carrier armed by the recipe's cadence rule both count, and the
# recorded quota-pause reason suppresses the trip while such a carrier is
# armed), and the zcode.md Child dispatch ladder's named reduced-toolset
# terminal rung (the listing-only park whose recovery path is the Step 0
# discharge precedence). The two SKILL.md literals are count-gated at exactly
# 1 whole-file so a restatement anywhere cannot create a second home; the
# renumbered last-resort rung pin holds the ladder's numbering through the
# rung insertion (the prompt-templates.md closeout duty references the
# last-resort step by name, so the numbering must stay resolvable).
pin "step 0 discharge precedence duty sentence" grep -qF 'the turn discharges parked re-arm records before it surveys' "$S"
pin "step 0 discharge precedence literal exactly-once" test "$(grep -oF 'discharges parked' "$S" | wc -l | tr -d ' ')" -eq 1
pin "step 0 discharge joins the duty's writer enumeration" grep -qF "discharge writes join the sanctioned-writer enumeration that duty's writes use" "$S"
pin "step 0 dispatch half stays with the step 1 duty" grep -qF 'dispatch discharge stays owned by the existing Step 1 parked-intent discharge duty' "$S"
pin "completion-stranding literal present" grep -qF 'turn_error: completion-stranded' "$S"
pin "completion-stranding literal exactly-once" test "$(grep -oF 'completion-stranded' "$S" | wc -l | tr -d ' ')" -eq 1
pin "stranding reset-window carrier explanation span" grep -qF "a reset-window carrier armed by the recipe's cadence rule for a later quota window counts as well" "$S"
pin "stranding quota-pause suppression span" grep -qF 'suppresses the trip while such a reset-window carrier is armed' "$S"
pin "reduced-toolset terminal rung present" grep -qF 'Reduced-toolset terminal' "$Z"
pin "reduced-toolset rung listing-only predicate" grep -qF 'a session whose automation toolset is the listing primitive only parks the decided action with its payload copy' "$Z"
pin "reduced-toolset rung names the step 0 recovery path" grep -qF 'the SKILL.md Step 0 discharge precedence' "$Z"
pin "ladder last-resort rung renumbered intact" grep -qF '5. Last resort:' "$Z"
[ "$fail" -eq 1 ] && exit 1

echo "maintenance pins: all hold"
exit 0
