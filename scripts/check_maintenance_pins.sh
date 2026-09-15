#!/usr/bin/env bash
# Mechanical pins for the maintenance scheduler skill (review r1/r2 fix rounds).
# Each pin guards an invariant the review loop or a manual edit could silently
# regress: guard structure, lane cap wording, dispatch-slice tag integrity,
# re-arm paragraph parity and escalation, the parent title's single creation
# source, the recognition span literal, section anchors other files navigate
# by, SKILL.md runtime-agnosticism, the pricing cache home, the schema-2 state
# contract, and the pricing seed presence. Exit 0 = all pins hold; exit 1 with
# PIN FAIL lines otherwise. Repo-relative paths only; run from anywhere.
set -u
fail=0
repo="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "not inside a git repo" >&2; exit 1; }
S="$repo/agents/skills/maintenance/SKILL.md"
Z="$repo/agents/skills/maintenance/zcode.md"
P="$repo/agents/skills/maintenance/prompt-templates.md"
for f in "$S" "$Z" "$P"; do
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

# --- SKILL.md structure ---
pin "G1e guard present"      grep -qF 'G1e (execution lane)' "$S"
pin "G1a guard present"      grep -qF 'G1a (authoring lane)' "$S"
pin "per-lane cap wording"   grep -qF 'at most one child per lane per scheduler turn' "$S"
pin "idle-time floor exemption" grep -qF 'exempt from the 30-minute floor' "$S"
pin "pricing rule pointer"   grep -qF 'usage-pricing rule' "$S"
pin "execution lane never idle-dispatched" grep -qF 'never dispatched through a primitive without a clock' "$S"
pin "state-file lane arm present" grep -qF 'State-file arm' "$S"
pin "idle children in the lane arm" grep -qF 'null `fire_at`' "$S"
pin "tripwire self-heal present" grep -qF 'Self-heal arm' "$S"
pin "failure-cap section anchored" grep -qF '## Failure detection and the failure cap' "$S"
pin "idle-time outcome arm present" grep -qF 'Idle-time children are covered too' "$S"
pin "pricing edits stay in the state cache" grep -qF 'never edits tracked skill files' "$S"
pin "state pricing_cache field named" grep -qF 'pricing_cache' "$S"
pin "step 6 carries child-written values" grep -qF 'carry forward the child-written values' "$S"
pin "starvation releases only the starved lane" grep -qF 'releases only the starved lane' "$S"
pin "three sanctioned writer classes" grep -qF 'three sanctioned writer classes' "$S"
python3 - "$S" <<'EOF'
import json, re, sys
s = open(sys.argv[1]).read()
order_ok = (lambda seq: all(s.find(a) != -1 and s.find(a) < s.find(b, s.find(a))
             for a, b in zip(seq, seq[1:])))
if not order_ok(["G1e (execution lane)", "G1a (authoring lane)", "G2 (failure cap)", "G3 (joint state)"]):
    print("PIN FAIL: guard order G1e<G1a<G2<G3"); sys.exit(1)
if not order_ok(["D1 (execute)", "D2 (author)", "D3 (no-op)"]):
    print("PIN FAIL: decision order D1<D2<D3"); sys.exit(1)
if re.search(r'Cron(Create|List|Update|Delete)|OffPeak(Create|List)', s):
    print("PIN FAIL: SKILL.md names a runtime primitive (must stay runtime-agnostic)"); sys.exit(1)
m = re.search(r"```json\n(.*?)```", s, re.S)
if not m:
    print("PIN FAIL: state schema json block missing"); sys.exit(1)
try:
    doc = json.loads(m.group(1))
except ValueError as exc:
    print("PIN FAIL: state schema json block does not parse: %s" % exc); sys.exit(1)
if doc.get("schema") != 2:
    print("PIN FAIL: state schema is not 2"); sys.exit(1)
lanes = {"execution", "authoring"}
if set(doc.get("decision", {})) != lanes or set(doc.get("decision_reason", {})) != lanes:
    print("PIN FAIL: per-lane decision/decision_reason keys drifted"); sys.exit(1)
pc = doc.get("pricing_cache", {})
if not {"last_verified", "source"} <= set(pc):
    print("PIN FAIL: pricing_cache fields drifted"); sys.exit(1)
if "rearm_note" not in doc:
    print("PIN FAIL: rearm_note missing from the state schema"); sys.exit(1)
child = (doc.get("children") or [{}])[0]
if not {"fire_at", "quota_status"} <= set(child):
    print("PIN FAIL: children entry fields drifted"); sys.exit(1)
EOF
rc=$?
[ "$rc" -ne 0 ] && fail=1
[ "$fail" -eq 1 ] && exit 1

# --- zcode.md anchors and single creation source ---
pin "recipe section anchored"    grep -qF '## Recurring automation recipe' "$Z"
pin "ladder section anchored"    grep -qF '## Child dispatch ladder' "$Z"
pin "quota section anchored"     grep -qF '## Quota leg' "$Z"
pin "model policy section anchored" grep -qF '## Child model and effort policy' "$Z"
pin "parent title in recipe"     grep -qF 'Title: `Maintenance scheduler turn (hourly)`' "$Z"
pin "recognition span full literal in recipe" grep -qF 'You are the maintenance scheduler for the repository at {REPO_ROOT}' "$Z"
pin "pricing seed present"       grep -qF 'pricing_last_verified' "$Z"
pin "ladder rollback present"    grep -qF 'Rollback: if the child create then fails' "$Z"
pin "watchdog backstop present"  grep -qF 'Watchdog backstop' "$Z"
pin "hourly cadence pinned"      grep -qF '15 * * * *' "$Z"
pin "peak window UTC+8 anchor"   grep -qF '14:00-18:00 UTC+8' "$Z"
pin "never pin local hours"      grep -qF 'never pin local hours' "$Z"

# --- prompt-templates.md blueprint integrity ---
python3 - "$P" "$Z" <<'EOF'
import re, sys
p, z = open(sys.argv[1]).read(), open(sys.argv[2]).read()
def norm(t): return " ".join(t.split())
if p.count("<prompt for the scheduled session>") != 1 or p.count("</prompt>") != 1:
    print("PIN FAIL: execution dispatch-slice tags not exactly one pair"); sys.exit(1)
inner = p.split("<prompt for the scheduled session>")[1].split("</prompt>")[0]
for needle in ("FIRST ACTION", "{some_plan}", "{REPO_ROOT}"):
    if needle not in inner:
        print("PIN FAIL: execution inner block missing %s" % needle); sys.exit(1)
for banned in ("{execution_time}", "SCHEDULER"):
    if banned in inner:
        print("PIN FAIL: execution inner block must not contain %s" % banned); sys.exit(1)
paras = [norm(m.group(0)) for m in
         re.finditer(r"FIRST ACTION, before any gate or phase:.*?re-arms per the recipe\.", p, re.S)]
if len(paras) != 2 or paras[0] != paras[1]:
    print("PIN FAIL: the two re-arm duty paragraphs differ or are not both present"); sys.exit(1)
for needle in ('"rearm_note"', "loop-parent-missing", "parent_automation_id",
               "Recurring automation recipe", "retry at most twice",
               "list once more immediately before the create"):
    if needle not in paras[0]:
        print("PIN FAIL: re-arm paragraph escalation drifted (missing %s)" % needle); sys.exit(1)
if p.count("Maintenance scheduler turn (hourly)") != 2:
    print("PIN FAIL: title literal must appear exactly twice in prompt-templates.md"); sys.exit(1)
if z.count("Maintenance scheduler turn (hourly)") != 1:
    print("PIN FAIL: title literal must appear exactly once (recipe) in zcode.md"); sys.exit(1)
span = "You are the maintenance scheduler for the repository at"
if z.count(span) != 2 or p.count(span) != 2:
    print("PIN FAIL: recognition span literal counts drifted (want 2 in zcode.md, 2 in prompt-templates.md)"); sys.exit(1)
auth = p.split("## Authoring child")[1].split("## Execution child")[0]
ph = set(re.findall(r"\{[A-Za-z_]+\}", auth))
if ph != {"{schedule_time}", "{backlog_item}", "{REPO_ROOT}"}:
    print("PIN FAIL: authoring body placeholder set drifted: %s" % sorted(ph)); sys.exit(1)
exec_ph = set(re.findall(r"\{[A-Za-z_]+\}", inner))
if exec_ph != {"{REPO_ROOT}", "{some_plan}"}:
    print("PIN FAIL: execution inner placeholder set drifted: %s" % sorted(exec_ph)); sys.exit(1)
if "cron expression" in paras[0]:
    print("PIN FAIL: re-arm paragraph hardcodes the cadence; creation must follow the recipe"); sys.exit(1)
EOF
rc=$?
[ "$rc" -ne 0 ] && fail=1
[ "$fail" -eq 1 ] && exit 1

echo "maintenance pins: all hold"
exit 0