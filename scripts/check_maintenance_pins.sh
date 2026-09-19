#!/usr/bin/env bash
# Mechanical pins for the maintenance scheduler skill.
# Each pin guards an invariant the review loop or a manual edit could silently
# regress: guard structure, lane cap wording, dispatch-slice tag integrity,
# re-arm paragraph parity and escalation, the parent title's single creation
# source, the recognition span literal, section anchors other files navigate
# by, SKILL.md runtime-agnosticism, the pricing cache home, the schema-3 state
# contract, and the pricing seed presence. Exit 0 = all pins hold; exit 1 with
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
pin "widened-arm classification repo-scoped" grep -qF 'classify its prompt only when the prompt contains the resolved repository root' "$S"
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
pin "pricing note read-back"  grep -qF 'note surfaces in the survey read-back' "$S"
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
if not order_ok(["D1 (execute)", "D2 (author)", "D3 (no-op)"]):
    print("PIN FAIL: decision order D1<D2<D3"); sys.exit(1)
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
if doc.get("schema") != 3:
    print("PIN FAIL: state schema is not 3"); sys.exit(1)
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
if not {"fire_at", "quota_status", "progress_mark", "resume_count"} <= set(child):
    print("PIN FAIL: children entry fields drifted"); sys.exit(1)
need(s, "### Step 1: survey"); need(s, "### Step 2")
step1 = s.split("### Step 1: survey")[1].split("### Step 2")[0]
if "pending_dispatch" not in step1:
    print("PIN FAIL: pending_dispatch reader missing from the Step 1 list"); sys.exit(1)
need(s, "G1e (execution lane)"); need(s, "Duplicate-parent tripwire")
arms = s.split("G1e (execution lane)")[1].split("Duplicate-parent tripwire")[0]
if "certification oracle" not in arms:
    print("PIN FAIL: lane-arm release rules missing the certification oracle needle"); sys.exit(1)
need(s, "## Failure detection and the failure cap")
failure_region = s.split("## Failure detection and the failure cap", 1)[1].split("\n## ", 1)[0]
if "\\[[xX]\\]" not in failure_region:
    print("PIN FAIL: corrected checkbox regex literal missing from the failure-detection region"); sys.exit(1)
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
pin "ladder recycling needle"    grep -qF 'update the recorded parent record into the child one-shot' "$Z"
pin "hand-off proceed refusal bound" grep -qF "converges to the fallback's fresh-id create within the same dispatch attempt" "$Z"
pin "verification section anchored" grep -qF '## Automation primitive verification' "$Z"
pin "linger-deletion needle"     grep -qF 'deleting your own lingered' "$Z"
pin "ambiguous-outcome carve-out kept" grep -qF 'treat the child as dispatched' "$Z"
expect_absent "superseded unscoped ambiguous-outcome carve-out must be absent from zcode.md" 'a rollback create refusal means the child create actually succeeded: skip the retries, the `parent-restore-failed` record, and the memory note, treat the child as dispatched, and stop' "$Z"
pin "idle attribution per-session" grep -qF ' sessionId matches the current session' "$Z"
pin "pricing clear-on-success"   grep -qF 'clears the pricing-verification-failed note' "$Z"
expect_absent "superseded completed-spawner claim must be absent from zcode.md" 'sessions whose spawner automation has completed are not blocked' "$Z"

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
expect_absent "superseded unscoped success-via-existing clause must be absent from prompt-templates.md" 'counts as success only after one more listing confirms an ENABLED automation with that title and prompt opening is present; on that success-via-existing path' "$P"
expect_absent "superseded listing-driven rearm wording must be absent from prompt-templates.md" 'list once more immediately before the create' "$P"

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
EOF
rc=$?
[ "$rc" -ne 0 ] && fail=1
[ "$fail" -eq 1 ] && exit 1

# --- rearm-on-touch surfaces (Task 4) ---
pin "step 0 rearm-on-touch check" grep -qF 'rearm-on-touch check: consult the scheduler state file first' "$S"
expect_absent "superseded listing-first rearm-on-touch trigger must be absent from SKILL.md" 'when the automation listing shows no ENABLED parent' "$S"
pin "done-skill rearm-on-touch pointer" grep -qF 'rearm-on-touch check defined in the maintenance skill' "$D"
[ "$fail" -eq 1 ] && exit 1

echo "maintenance pins: all hold"
exit 0
