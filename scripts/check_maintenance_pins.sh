#!/usr/bin/env bash
# Mechanical pins for the maintenance scheduler skill.
# Each pin guards an invariant the review loop or a manual edit could silently
# regress: guard structure, lane cap wording, dispatch-slice tag integrity,
# re-arm paragraph parity and escalation, the parent title's single creation
# source, the recognition span literal, section anchors other files navigate
# by, SKILL.md runtime-agnosticism, the pricing cache home, the schema-4 state
# contract, the pricing seed presence, and the budget-gate resume mirrors in
# the execute-plan and plans skills. Exit 0 = all pins hold; exit 1 with
# PIN FAIL lines otherwise. Repo-relative paths only; run from anywhere.
set -u
fail=0
repo="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "not inside a git repo" >&2; exit 1; }
S="$repo/agents/skills/maintenance/SKILL.md"
Z="$repo/agents/skills/maintenance/zcode.md"
P="$repo/agents/skills/maintenance/prompt-templates.md"
D="$repo/agents/skills/done/SKILL.md"
for f in "$S" "$Z" "$P" "$D"; do
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
#       default `docs/plans/`).' (zcode.md): superseded by the same P12
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
pin "execution lane never idle-dispatched" grep -qF 'never dispatched through a primitive without a clock' "$S"
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
pin "starvation releases only the starved lane" grep -qF 'releases only the starved lane' "$S"
pin "five sanctioned writer classes" grep -qF 'five sanctioned writer classes' "$S"
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
python3 - "$S" <<'EOF'
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
child = (doc.get("children") or [{}])[0]
if not {"fire_at", "requested_at", "quota_status", "progress_mark", "resume_count"} <= set(child):
    print("PIN FAIL: children entry fields drifted"); sys.exit(1)
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
pin "parent title in recipe"     grep -qF 'Title: `Maintenance scheduler turn (every 2 hours)`' "$Z"
pin "recognition span full literal in recipe" grep -qF 'You are the maintenance scheduler for the repository at {REPO_ROOT}' "$Z"
pin "pricing seed present"       grep -qF 'pricing_last_verified' "$Z"
pin "ladder rollback present"    grep -qF 'Rollback: if the child create then fails' "$Z"
pin "watchdog backstop present"  grep -qF 'Watchdog backstop' "$Z"
pin "2h cadence pinned"          grep -qF '15 */2 * * *' "$Z"
pin "peak window UTC+8 anchor"   grep -qF '14:00-18:00 UTC+8' "$Z"
pin "never pin local hours"      grep -qF 'never pin local hours' "$Z"
pin "execution-child marker repo containment" grep -qF 'and the resolved repository root (the relative plans-dir substring alone' "$Z"
expect_absent "superseded uncontained execution-child marker wording must be absent from zcode.md" 'plus a path under the resolved `plans_dir` (SKILL.md Configuration; default `docs/plans/`).' "$Z"
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

# Context-budget plan Task 4: the checkpoint duty paragraph added to each
# blueprint body. The anchor 'after each blueprint step block' occurs in BOTH
# blueprints, so each pin stretches to the blueprint-unique telemetry record
# span (same twice-needle trap as the F8 note above): reverting one body while
# the other keeps the duty must still fail.
pin "authoring blueprint checkpoint duty" grep -qF 'after each blueprint step block, at a boundary only, never mid-task, log one telemetry record (skill: plans-authoring) to docs/tmp/authoring/<plan-slug>/context.jsonl' "$P"
pin "execution blueprint checkpoint duty" grep -qF 'after each blueprint step block, at a boundary only, never mid-task, log one telemetry record (skill: execute-plan) to docs/tmp/execute-plan/<plan-slug>/context.jsonl' "$P"

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

# --- prompt-templates.md blueprint integrity ---
python3 - "$P" "$Z" "$D" <<'EOF'
import re, sys
p, z, d = open(sys.argv[1]).read(), open(sys.argv[2]).read(), open(sys.argv[3]).read()
def norm(t): return " ".join(t.split())
def need(text, anchor):
    if anchor not in text:
        print("PIN FAIL: missing anchor %s" % anchor); sys.exit(1)
need(p, "<prompt for the scheduled session>"); need(p, "</prompt>")
if p.count("<prompt for the scheduled session>") != 1 or p.count("</prompt>") != 1:
    print("PIN FAIL: execution dispatch-slice tags not exactly one pair"); sys.exit(1)
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
if p.count("Maintenance scheduler turn (every 2 hours)") != 0:
    print("PIN FAIL: title literal must not appear in prompt-templates.md (the zcode.md recipe is the single literal home)"); sys.exit(1)
if z.count("Maintenance scheduler turn (every 2 hours)") != 1:
    print("PIN FAIL: title literal must appear exactly once (recipe) in zcode.md"); sys.exit(1)
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
# must sit after the PRE-STEP gate; every predecessor anchor is fail-closed
for needle in ("Finally squash merge to main", "SUCCESSOR DISPATCH", "FINAL STEP",
               "once the gate exits 0", "this is a resume run"):
    need(inner, needle)
if not inner.index("Finally squash merge to main") < inner.index("SUCCESSOR DISPATCH") < inner.index("FINAL STEP"):
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
# merge landing lock group (plan 2026-09-20-merge-landing-lock-grouping):
# each blueprint acquires the merge landing lock exactly once (the dated
# deviation-list entries paraphrase the literal, so the count stays 2), the
# authoring blueprint carries the worktree isolation fragment, and the
# superseded riding sentence is absent from the fenced blueprint bodies
# (region-scoped like the checkbox-regex pin above, so the dated deviation-list
# history entry outside the fences stays legal).
if p.count("merge-wait-acquire") != 2:
    print("PIN FAIL: merge-wait-acquire count %d != 2 in prompt-templates.md (once per blueprint)" % p.count("merge-wait-acquire")); sys.exit(1)
need(norm(p), "git worktree add -b YYYY-MM-DD-authoring-<slug> <sibling-path> <default-branch>")
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
auth_bodies = [b for b in bodies if "git worktree add -b YYYY-MM-DD-authoring-<slug>" in norm(b)]
if len(auth_bodies) != 1:
    print("PIN FAIL: could not uniquely identify the authoring blueprint body"); sys.exit(1)
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
for para in paras:
    if "authoring-claims" in para:
        print("PIN FAIL: claim duty/gate must stay outside the shared re-arm FIRST ACTION span"); sys.exit(1)
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
E="$repo/agents/skills/execute-plan/SKILL.md"
PL="$repo/agents/skills/plans/SKILL.md"
for f in "$E" "$PL"; do
  [ -f "$f" ] || { echo "missing $f"; fail=1; }
done
[ "$fail" -eq 1 ] && exit 1
pin "resume-fit --fire-at check at resume-scheduling boundaries" grep -qF -- '--fire-at mode with the scheduled resume time as the fire instant' "$E"
pin "resume-pricing defers to the reported defer_to" grep -qF 'on exit 2 (defer-peak, a fitting slot inside the weekday peak window), schedule the watcher at the reported defer_to' "$E"
pin "plans budget gate mirrors the canonical resume checks" grep -qF 'The canonical resume-fit and resume-pricing checks apply at this boundary' "$PL"
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
pin "SKILL.md step 5 ladder-precheck precondition anchored" grep -qF 'ladder precheck' "$S"
pin "zcode.md Ladder precheck bullet anchored" grep -qF 'Ladder precheck' "$Z"
pin "clocked-lane stand-down reason pinned" grep -qF 'clocked-primitives-absent' "$Z"
pin "idle-lane stand-down reason pinned" grep -qF 'idle-primitive-absent' "$Z"
[ "$fail" -eq 1 ] && exit 1

echo "maintenance pins: all hold"
exit 0
