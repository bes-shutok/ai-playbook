#!/usr/bin/env bash
# Mechanical pins for the maintenance scheduler skill.
# Each pin guards an invariant the review loop or a manual edit could silently
# regress: guard structure, lane cap wording, dispatch-slice tag integrity,
# re-arm paragraph parity and escalation, the parent title's single creation
# source, the recognition span literal, section anchors other files navigate
# by, SKILL.md runtime-agnosticism, the pricing cache home, the schema-4 state
# contract, the state-durability pending_rearm contract, the loop_mode
# zero-survivor gate, the pricing
# seed presence, and the budget-gate resume mirrors in
# the execute-plan and plans skills, and the discovery-ladder rung 1
# workflow_state bound (terminal-or-complete before a no-live-session closure),
# and the user-directed-payload-duties family (the re-arm-first duty and its
# liveness report for the user-directed payload class), and the Step 1
# corpus-freshness rule (status reads bind to the committed tree at HEAD), and
# the origin-independent eligibility and privacy-emission contract across the
# investigate and maintenance skills (the section's fixture fail-arm joins the
# witnessed-fail-arm family under the same per-section fixture seam), and the
# warning-only placement-pins family over the placement doctrine spans in the four placement-decision owners,
# and the warning-only prompt-log prune-range pin family over the landed prune-range, receipt-preservation,
# write-boundary, and audit-separation clauses across the two rolling logs and the five operative procedures.
# Outcome contract (scripts/OUTCOME_CONTRACT.md): exit 0 = all pins hold
# (`OUTCOME: pass`) or every standing red is an unexpired recorded red named
# in the run summary line, exit 1 = a failing pin (`OUTCOME: fail` after the PIN
# FAIL lines; every mid-suite `[ "$fail" -eq 1 ]` checkpoint funnels
# through the one emit_outcome helper so each run ends with exactly one
# final `OUTCOME:` line on stdout), exit 3 = tool error (the
# not-inside-a-git-repo arm, or the recorded-red register unreadable or
# unparseable arm with one bounded re-read); exit 2 stays reserved for
# indeterminate and
# is never emitted. PIN FAIL carve-out: the placement family's PIN FAIL lines never move the exit; the summary names the first missing span on an exit-0 run. Outcome evidence shape: the in-repo run is the pass
# arm, the live-vs-archive section's built-in synthetic-fixture selftest
# is the witnessed fail arm (the per-section fixture seam; no suite-wide
# harness), and the non-repo invocation probe is the tool-error arm.
# Repo-relative paths only; run from anywhere.
set -u
# --- invocation telemetry entry hook (plan
# docs/history/plans/2026-10-14-script-runtime-cost-telemetry.md, Task 2) ---
# The start stamp: a python3-derived epoch float written into a temp stamp
# file created at script entry; the emit_outcome exit hook spends it. The
# hook pair is fail-open by construction: a missing python3, an unwritable
# tmp dir, or a corrupt stamp is swallowed silently and the script's exit
# status, stdout, and stderr stay byte-identical; the two interpreter
# spawns add roughly 20-60ms per invocation, priced by the machinery
# registry entry's admission note beside the per-line JSONL cost.
PINS_START_STAMP="$(mktemp "${TMPDIR:-/tmp}/pins-start-stamp.XXXXXX")" 2>/dev/null || PINS_START_STAMP=""
if [ -n "$PINS_START_STAMP" ]; then
  python3 -c 'import sys, time; open(sys.argv[1], "w").write(repr(time.time()))' "$PINS_START_STAMP" >/dev/null 2>&1 || :
fi
# The one emission funnel: every exit site (the mid-suite checkpoints,
# the not-inside-a-git-repo arm, the all-hold tail) prints its final
# `OUTCOME:` line through this helper and nowhere else. When this run
# suppressed recorded reds, the funnel first prints the one summary line
# naming every suppressed red, so the summary appears on every exit path
# including mid-suite checkpoint exits; it prints only when at least one
# red was suppressed (red-on-main-baseline-repair-and-auto-demote, Task 3).
SUPPRESSED_NAMES=""
emit_outcome() { # emit_outcome <pass|fail|tool_error>
  if [ -n "$SUPPRESSED_NAMES" ]; then
    echo "PIN RECORDED REDS SUPPRESSED THIS RUN: $SUPPRESSED_NAMES"
  fi
  echo "OUTCOME: $1"
  # --- invocation telemetry exit hook (plan
  # docs/history/plans/2026-10-14-script-runtime-cost-telemetry.md, Task 2) ---
  # ONE python3 call reads the entry stamp, computes wall_ms, appends the
  # invocation_kind pins-suite line, and removes the stamp file. It fires
  # only in the main shell (the two modeled-refusal selftests call this
  # helper from command-substitution subshells, where BASH_SUBSHELL is
  # nonzero, so those calls never touch the stamp) and only when the
  # entry stamp exists. Every output is silenced and the call is
  # `|| :`-guarded: telemetry success or failure never changes this
  # helper's stdout/stderr or the caller's exit path (fail-open).
  if [ "${BASH_SUBSHELL:-0}" -eq 0 ] && [ -n "${PINS_START_STAMP:-}" ] && [ -f "$PINS_START_STAMP" ]; then
    python3 -c '
import sys, time
from pathlib import Path
script_path = sys.argv[1]
stamp = Path(sys.argv[2])
try:
    lib_dir = str(Path(script_path).resolve().parent)
    if lib_dir not in sys.path:
        sys.path.insert(0, lib_dir)
    import invocation_telemetry as telemetry
    start = float(stamp.read_text(encoding="utf-8").strip())
    wall_ms = max(0.0, (time.time() - start) * 1000.0)
    telemetry.record_invocation(script_path, "pins-suite", wall_ms)
finally:
    try:
        stamp.unlink()
    except OSError:
        pass
' "$0" "$PINS_START_STAMP" >/dev/null 2>&1 || :
  fi
}
fail=0
repo="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "not inside a git repo" >&2; emit_outcome tool_error; exit 3; }

# --- recorded-red consult begin (red-on-main-baseline-repair-and-auto-demote plan, Task 3) ---
# Recorded-red row-shape contract: a standing red is one override row under
# the `check_maintenance_pins` guard in scripts/gate_liveness_ledger.json
# whose note carries the keys `pin: <stable pin name>` and
# `review-by: YYYY-MM-DD` plus a witness. These rows are standing reds rather
# than interactive proceeds; the `pin:` key is the distinguishing marker a
# demotion census can filter on. Matching between a failing row's stable pin
# name and the recorded name is exact string equality (the token between
# `pin: ` and the next ` review-by:` delimiter in the note); when several
# unexpired rows match one pin, the last matching row wins. A recorded,
# unexpired failing pin prints `PIN RECORDED RED (recorded <date>, review-by
# <date>): <name>` and does not set fail; an expired review-by prints
# `PIN RECORDED RED EXPIRED (recorded <date>, review-by <date>): <name>` and
# fails as unrecorded; a note failing the parse contract (missing or
# non-calendar `review-by:`) produces one loud MALFORMED advisory line naming
# the row at load time and is treated as not recorded; unrecorded failures
# behave byte-identically to the pre-consult suite. The register path is
# overridable for fixtures through PINS_RECORDED_RED_REGISTER (the suite's
# fixture-seam convention). exit 0 = all pins hold or every standing red is
# an unexpired recorded red named in the summary line; a missing
# `check_maintenance_pins` guard key means zero recorded reds (normal
# first-run state); a missing or unparseable register is a loud tool_error
# (exit 3, naming the path) with one bounded re-read on failure. The expiry
# comparison runs against the system date in production; selftests may pin
# that clock through PINS_RECORDED_RED_AS_OF (an explicit calendar date), and
# a set but non-calendar value is a tool error, never a silent fallback.
# Placement guidance for new pin rows: land a new row BEFORE the earliest
# `[ "$fail" -eq 1 ]` checkpoint that fires in the current baseline posture
# (while the baseline is green any placement executes; dormancy returns
# exactly when a standing red precedes the row again). Every green-result
# check is paired with a negative-arm probe before it is trusted, and a
# provenance comment notes dormancy only while an upstream standing red
# exists.
PINS_RECORDED_RED_REGISTER="${PINS_RECORDED_RED_REGISTER:-$repo/scripts/gate_liveness_ledger.json}"
RECORDED_REDS=""
EXPIRED_REDS=""
# The heredoc router runs in a pipeline subshell, so its all-suppressed
# verdict and the suppressed names cross back through state files, not
# variables (the funnel summary must name heredoc-suppressed reds too).
PINS_CONSULT_STATE="$(mktemp "${TMPDIR:-/tmp}/pins-consult-state.XXXXXX")"
PINS_CONSULT_NAMES="$PINS_CONSULT_STATE.names"
printf '0\n' > "$PINS_CONSULT_STATE"
: > "$PINS_CONSULT_NAMES"
trap 'rm -f "$PINS_CONSULT_STATE" "$PINS_CONSULT_NAMES"' EXIT
load_recorded_reds() { # sets RECORDED_REDS / EXPIRED_REDS (tab-separated name, recorded, review-by); returns 3 on an unreadable or unparseable register
  local attempt out rc line state name rest rec rev
  for attempt in 1 2; do
    out="$(python3 - "$PINS_RECORDED_RED_REGISTER" <<'PY_READER'
import sys, json, re, os
from datetime import date

def clean(value):
    return "".join(ch for ch in str(value) if ord(ch) >= 32 and ord(ch) != 127)

path = sys.argv[1]
try:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
except (OSError, ValueError) as exc:
    print("READER-ERROR\t%s\t%s" % (path, clean(exc)), file=sys.stderr)
    sys.exit(3)
guards = data.get("guards") if isinstance(data, dict) else None
if not isinstance(guards, dict):
    guards = {}
guard = guards.get("check_maintenance_pins")
rows = guard.get("rows") if isinstance(guard, dict) else None
if not isinstance(rows, list):
    rows = []
# Expiry clock: the system date in production; selftests pin it through
# PINS_RECORDED_RED_AS_OF. The empty string reads as unset (the scenario shell
# forwards an unset variable as empty); any other set value must be a
# YYYY-MM-DD calendar date, whitespace-only included, or the reader
# tool-errors instead of silently falling back.
as_of_raw = os.environ.get("PINS_RECORDED_RED_AS_OF")
if as_of_raw is None or as_of_raw == "":
    today = date.today()
else:
    as_of = as_of_raw.strip()
    try:
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", as_of):
            raise ValueError(as_of)
        today = date.fromisoformat(as_of)
    except ValueError:
        print("AS-OF-OVERRIDE-ERROR\tPINS_RECORDED_RED_AS_OF is not a calendar date: %s" % clean(as_of), file=sys.stderr)
        sys.exit(3)
for row in rows:
    if not isinstance(row, dict) or row.get("kind") != "override":
        continue
    note = row.get("note") if isinstance(row.get("note"), str) else ""
    if "pin: " not in note:
        continue
    payload = note.split("pin: ", 1)[1]
    name = payload.split(" review-by:", 1)[0].strip()
    match = re.search(r"review-by:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", payload)
    if not match:
        print("MALFORMED\t%s" % clean(name or "<unnamed override row>"))
        continue
    try:
        expired = date.fromisoformat(match.group(1)) < today
    except ValueError:
        print("MALFORMED\t%s" % clean(name or "<unnamed override row>"))
        continue
    recorded = clean(row.get("date", ""))
    state = "EXPIRED" if expired else "RECORDED"
    print("%s\t%s\t%s\t%s" % (state, name, recorded, match.group(1)))
PY_READER
)" ; rc=$?
    if [ "$rc" -eq 0 ]; then
      RECORDED_REDS=""
      EXPIRED_REDS=""
      while IFS= read -r line; do
        [ -n "$line" ] || continue
        state="${line%%$'\t'*}"
        rest="${line#*$'\t'}"
        name="${rest%%$'\t'*}"
        rest="${rest#*$'\t'}"
        rec="${rest%%$'\t'*}"
        rev="${rest#*$'\t'}"
        case "$state" in
          RECORDED) RECORDED_REDS="${RECORDED_REDS}${name}"$'\t'"${rec}"$'\t'"${rev}"$'\n' ;;
          EXPIRED)  EXPIRED_REDS="${EXPIRED_REDS}${name}"$'\t'"${rec}"$'\t'"${rev}"$'\n' ;;
          MALFORMED) echo "PIN RECORDED RED MALFORMED (treated as not recorded): $name" >&2 ;;
        esac
      done <<PY_READER_LINES
$out
PY_READER_LINES
      return 0
    fi
    # the loop is the one bounded re-read on reader failure (bounded-repair menu)
  done
  if [ -n "${PINS_RECORDED_RED_AS_OF:-}" ]; then
    echo "recorded-red reader failed with PINS_RECORDED_RED_AS_OF set (see the AS-OF-OVERRIDE-ERROR line above) or the register unreadable or unparseable at $PINS_RECORDED_RED_REGISTER" >&2
  else
    echo "recorded-red register unreadable or unparseable at $PINS_RECORDED_RED_REGISTER" >&2
  fi
  return 3
}
recorded_red_lookup() { # recorded_red_lookup <map-var-name> <pin name>; prints "<recorded> <review-by>" of the LAST matching row, or nothing
  local map="$1" name="$2" line hit=""
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    if [ "${line%%$'\t'*}" = "$name" ]; then
      hit="${line#*$'\t'}"
    fi
  done <<PY_LOOKUP_LINES
${!map}
PY_LOOKUP_LINES
  [ -n "$hit" ] && printf '%s\n' "${hit//$'\t'/ }"
  return 0
}
recorded_red_check() { # recorded_red_check <stable pin name> <rendered PIN FAIL line>; prints the emission; rc 0 = suppressed, rc 1 = failed (fail=1 set by the caller shape)
  local name="$1" line="$2" hit
  hit="$(recorded_red_lookup RECORDED_REDS "$name")"
  if [ -n "$hit" ]; then
    echo "PIN RECORDED RED (recorded ${hit% *}, review-by ${hit#* }): ${name}"
    if [ -z "$SUPPRESSED_NAMES" ]; then
      SUPPRESSED_NAMES="$name"
    else
      SUPPRESSED_NAMES="$SUPPRESSED_NAMES; $name"
    fi
    return 0
  fi
  hit="$(recorded_red_lookup EXPIRED_REDS "$name")"
  if [ -n "$hit" ]; then
    echo "PIN RECORDED RED EXPIRED (recorded ${hit% *}, review-by ${hit#* }): ${name}"
  fi
  echo "$line"
  return 1
}
route_heredoc_stream() { # stdin-router for a piped python pin block: routes each PIN FAIL line through the shared check, passes every other line through; writes 1 to the state file only when at least one PIN FAIL line was seen and every one was suppressed
  local line any_fail=0 saw=0
  while IFS= read -r line; do
    case "$line" in
      "PIN FAIL: "*)
        saw=1
        if recorded_red_check "${line#PIN FAIL: }" "$line"; then
          route_note_suppressed "${line#PIN FAIL: }"
        else
          any_fail=1
        fi
        ;;
      *) printf '%s\n' "$line" ;;
    esac
  done
  if [ "$saw" -eq 1 ] && [ "$any_fail" -eq 0 ]; then
    printf '1\n' > "$PINS_CONSULT_STATE"
  else
    printf '0\n' > "$PINS_CONSULT_STATE"
  fi
  return 0
}
route_note_suppressed() { # route_note_suppressed <name>; records one heredoc-routed suppression for the funnel summary
  printf '%s\n' "$1" >> "$PINS_CONSULT_NAMES"
  return 0
}
heredoc_settle() { # heredoc_settle <rc>; after a routed heredoc pipeline: fold the router's suppressed names into the funnel summary, then fail=1 unless the block failed and every printed red was suppressed
  local all_suppressed name
  all_suppressed="$(cat "$PINS_CONSULT_STATE" 2>/dev/null || printf '0')"
  while IFS= read -r name; do
    [ -n "$name" ] || continue
    if [ -z "$SUPPRESSED_NAMES" ]; then
      SUPPRESSED_NAMES="$name"
    else
      SUPPRESSED_NAMES="$SUPPRESSED_NAMES; $name"
    fi
  done < "$PINS_CONSULT_NAMES"
  : > "$PINS_CONSULT_NAMES"
  if [ "$1" -ne 0 ] && [ "$all_suppressed" -ne 1 ]; then
    fail=1
  fi
  printf '0\n' > "$PINS_CONSULT_STATE"
  return 0
}
# --- recorded-red consult end ---
load_recorded_reds || { emit_outcome tool_error; exit 3; }
S="$repo/agents/skills/maintenance/SKILL.md"
CL="$repo/agents/skills/maintenance/CHANGELOG.md"
# post-split module homes (maintenance-skill-size-refactor plan, Task 3):
# SA survey-arms, GU guards, DE decisions, QP quota-policy, SC scheduling,
# FC failure-cap, SF state-file; S remains the router
SA="$repo/agents/skills/maintenance/survey-arms.md"
GU="$repo/agents/skills/maintenance/guards.md"
DE="$repo/agents/skills/maintenance/decisions.md"
QP="$repo/agents/skills/maintenance/quota-policy.md"
SC="$repo/agents/skills/maintenance/scheduling.md"
FC="$repo/agents/skills/maintenance/failure-cap.md"
SF="$repo/agents/skills/maintenance/state-file.md"
Z="$repo/agents/skills/maintenance/zcode.md"
P="$repo/agents/skills/maintenance/prompt-templates.md"
TA="$repo/agents/skills/maintenance/template-authoring.md"
TE="$repo/agents/skills/maintenance/template-execution.md"
TU="$repo/agents/skills/maintenance/template-unblock.md"
DC="$repo/agents/skills/maintenance/duties-core.md"
PTCL="$repo/agents/skills/maintenance/templates-CHANGELOG.md"
D="$repo/agents/skills/done/SKILL.md"
# Re-aimed 2026-10-11 (the done target-state flip): the per-concern module
# homes dissolved; the collapsed SKILL.md is the one done skill surface, and
# scripts/done_run.sh is the runners' pin home.
DR="$repo/scripts/done_run.sh"
E="$repo/agents/skills/execute-plan/SKILL.md"
for f in "$S" "$Z" "$P" "$D" "$E"; do
  [ -f "$f" ] || { echo "missing $f"; fail=1; }
done
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

pin() { # pin <description> <command...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then
    return 0
  fi
  recorded_red_check "$desc" "PIN FAIL: $desc" || fail=1
  return 1
}

expect_absent() { # expect_absent <description> <pattern> <file>: rc 0 = fail, rc >= 2 = grep error (fail), rc 1 = pass
  local desc="$1" pat="$2" f="$3" out rc
  out="$(grep -nF -- "$pat" "$f" 2>&1)"; rc=$?
  if [ "$rc" -eq 0 ]; then
    recorded_red_check "$desc" "PIN FAIL: $desc" || fail=1
  elif [ "$rc" -ge 2 ]; then
    recorded_red_check "grep error on $f while checking absence" "PIN FAIL: grep error on $f while checking absence: $out" || fail=1
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
    recorded_red_check "$desc" "PIN FAIL: $desc" || fail=1
  elif [ "$rc" -ge 2 ]; then
    recorded_red_check "grep error on $f while checking flat absence" "PIN FAIL: grep error on $f while checking flat absence: $out" || fail=1
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
pin "G1e guard present"      grep -qF 'G1e (execution lane)' "$GU"
pin "G1a guard present"      grep -qF 'G1a (authoring lane)' "$GU"
pin "per-lane cap wording"   grep -qF 'at most one child per lane per scheduler turn' "$SC"
pin "idle-time floor exemption" grep -qF 'exempt from the 5-minute floor' "$SC"
pin "pricing rule pointer"   grep -qF 'usage-pricing rule' "$QP"
pin "state-file lane arm present" grep -qF 'State-file arm' "$GU"
pin "idle children in the lane arm" grep -qF 'null `fire_at`' "$GU"
pin "tripwire self-heal present" grep -qF 'Self-heal arm' "$GU"
pin "tripwire span shape excludes the title conjunct" grep -qF "deliberately without that rule's title conjunct" "$GU"
pin "widened-arm classification repo-scoped" grep -qF 'classify its prompt only when the prompt contains the resolved repository root' "$GU"
pin "widened-arm outcomes scoped to contained prompts" grep -qF 'Among contained prompts:' "$GU"
expect_absent "superseded unscoped widened-arm classification wording must be absent from SKILL.md" 'spacing window, classify its prompt:' "$S"
pin "failure-cap section anchored" grep -qF '## Failure detection and the failure cap' "$FC"
pin "idle-time outcome arm present" grep -qF 'Idle-time children are covered too' "$FC"
pin "pricing edits stay in the state cache" grep -qF 'never edits tracked skill files' "$QP"
pin "state pricing_cache field named" grep -qF 'pricing_cache' "$QP"
pin "step 6 carries forward externally written values" grep -qF 'carry forward the values whose authoritative writes may occur outside Step 6' "$SF"
# review r1 F4 (state durability plan): the carry-forward enumeration must name
# the state-durability fields; the opener pin above predates them, so a rewrite
# that drops the enumeration tail stays green without this membership pin.
# Re-aimed by the two-mode loop policy plan Task 2: the enumeration dropped the
# retired loop_mode field and gained the survey_only flag (the Mode enforcement
# paragraph's operator-directed targeted edit writes it outside Step 6).
pin "carry-forward names the state-durability fields" grep -qF 'plus `pending_rearm` and `survey_only`' "$SF"
pin "starvation releases only the starved lane" grep -qF 'releases only the starved lane' "$QP"
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
pin "eight sanctioned writer classes" grep -qF 'eight sanctioned writer classes' "$SF"
for f in "$S" "$Z" "$P" "$D" "$E"; do expect_absent "superseded six sanctioned writer classes literal in $f" 'six sanctioned writer classes' "$f"; done
for f in "$S" "$Z" "$P" "$D" "$E"; do expect_absent "superseded seven sanctioned writer classes literal in $f" 'seven sanctioned writer classes' "$f"; done
# --- durable cycle gate pins (plan
# 2026-09-26-p64-execution-lane-liveness-long-session-continuity.md, Task 2) ---
# Presence pins are dedicated fixed-string greps that fail when their span is
# deleted: the resting JSON literal, the section anchor other files navigate
# by, and the eighth writer-class bullet in SKILL.md, plus the overlay's
# continuation-resume classification bullet and its field naming in zcode.md.
pin "authoring_cycle_gate resting JSON literal" grep -qF '"authoring_cycle_gate": null' "$SF"
pin "cycle gate section anchored" grep -qF '## Cycle gate (durable pacing between cycles)' "$S"
pin "cycle-gate write class named" grep -qF 'cycle-gate write class' "$SF"
pin "continuation-summary resume classification in zcode" grep -qF 'continuation-summary resume' "$Z"
pin "zcode overlay names the authoring_cycle_gate field" grep -qF 'authoring_cycle_gate' "$Z"
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }
pin "execution-child progress counts checked checkboxes" grep -qF 'checked-checkbox count' "$FC"
# the corrected checkbox regex literal is pinned region-scoped to the failure-detection
# section in the python block below (a whole-file grep is satisfied by the Revisions-ledger copy)
pin "fast re-dispatch stop evidence" grep -qF 'timestamp older than one cadence period' "$FC"
pin "enabled-only arms ignore lingered records" grep -qF 'lifecycleStatus` is completed or `enabled` is false' "$GU"
pin "parent_absent_since needle" grep -qF 'parent_absent_since' "$SA"
pin "darkness clock keeps the earliest value" grep -qF 'keeps the earliest value' "$SF"
pin "step 0 keep-earliest phrasing" grep -qF 'keeping the earliest value' "$S"
pin "idle occupancy join mirrored in SKILL.md" grep -qF 'whose target carries the `(idle)` marker' "$GU"
# merge landing lock group (plan 2026-09-20-merge-landing-lock-grouping): the
# G3b guard arm; the prompt-templates and overlay needles live in their own
# file sections below (count and body-scoped absence in the python block)
pin "G3b guard present"      grep -qF 'G3b (landing in flight)' "$GU"
pin "pricing note read-back"  grep -qF 'note surfaces in the survey read-back' "$SA"
# P37 (plan 2026-09-22-p37-context-budget-probes-and-runtime-state, Task 6):
# the State-file advisory note must name the merge lock among the joint-state
# safety sources, and the G3b final-slot effect span it already carries stays
# pinned (the wiring landed before the pin; the pin protects it).
pin "state-file note names the merge lock" grep -qF 'the done-lock, the merge lock, and claim checks' "$SF"
pin "G3b final-slot effect named in the state-file note" grep -qF 'the `G3b` final-slot effect' "$SC"
# --- state durability contract (scheduler/maintenance state durability plan, Task 6) ---
# The pending_rearm prose surfaces (the loop_mode surfaces retired by the
# two-mode loop policy plan Task 2: the field paragraph opener pin deleted with
# the paragraph, the enforcement needles re-aimed to the Loop modes section's
# Mode enforcement paragraph literals, which are the Step 3 enforcement's
# source of record). The openers are unique-span whole-file greps; the schema
# literals and the Step 1 reader arm are pinned region-scoped in the python
# block below (the suite computes the counts itself and asserts the invariant
# that matters, so no manual total is frozen in a comment).
pin "author-mode enforcement needle" grep -qF 'author mode resolves D1 and D4 to D3' "$DE"
pin "exec-mode enforcement needle" grep -qF 'exec mode resolves D2 to D3' "$DE"
pin "pending_rearm field paragraph opener" grep -qF 'is the re-arm intent record' "$SF"
# --- quota leg bindings (P6 origins 1-2; schema-4 fire-time bookkeeping) ---
pin "quota leg binds every clocked dispatch path" grep -qF 'binds every clocked child dispatch, from any session type' "$QP"
# origin: docs/history/backlog/2026-10-06-parallel-execution-turn-cap-and-fired-arm.md
pin "cap second execution leg" grep -qF 'directive-bound second execution leg' "$DE"
# origin: docs/history/backlog/2026-10-06-parallel-execution-turn-cap-and-fired-arm.md
pin "fired arm same-directive carve-out" grep -qF 'releases for a same-directive session' "$GU"
pin "runtime-fit rule defers to reset regardless of pricing" grep -qF 'fire at reset_at_epoch instead, regardless of pricing' "$QP"
pin "deferred-peak quota_status recorded" grep -qF 'quota_status: "deferred-peak"' "$QP"
pin "probe-invocation bullet present" grep -qF 'Run `python3 scripts/quota_window_probe.py`' "$QP"
pin "deferred slot fit-checked before pricing deferral" grep -qF 'before deferring for pricing, verify the deferred slot' "$QP"
pin "starvation beats pricing never fit" grep -qF 'starvation beats pricing, never the runtime-fit rule' "$QP"
# quota-aware authoring primitive selection (plan
# 2026-09-20-quota-aware-scheduling-semantics, Task 5): the D2 quota-signal
# decision input in SKILL.md and the authoring blueprint's stand-down gate
# span in prompt-templates.md (the acceptance countability; the plan's
# Validation block pins the sibling G6 spans author in-session, quota_signal,
# still plan-uncovered, and in-session authoring primitive)
pin "D2 quota-signal decision input" grep -qF "quota leg's probe report as a required decision input" "$DE"
pin "authoring stand-down gate span" grep -qF 're-check the assigned backlog item is still plan-uncovered under the resolved plans directory' "$TA"
# --- clocked operator order pins (plan
# 2026-10-05-authoring-clocked-resume-order, Task 2) ---
# The maintenance-side spans the clocked-order machinery rides on: the
# survey's once-per-order missed recording (the plan's pinned skill-text
# duty; the watcher owns only the classification), the pickup arm's
# one-armed-receipt check, the quota leg's operator-named-wall-clock
# exemption (the exemption sentence lands beside the pinned peak-pricing
# span above; no needle of the pins above that span was disturbed by the
# insertion, so the same-edit re-key is this new pin keyed beside it), the
# overlay's receiving-session duty and launchd carrier family clause with
# its own exemption mirror, and the authoring blueprint's closing duty with
# the two chaining-guard sentences amended to except the arming duty (the
# exception phrase is count-gated at 2, role line + closing guard; the
# deviation-list entries paraphrase and must not carry these exact spans).
pin "clocked-order missed recording duty span" test "$(grep -oF 'turn_error: clocked-order-missed' "$SA" | wc -l | tr -d ' ')" -eq 1
pin "clocked-order pickup one-armed-receipt span" grep -qF 'one armed receipt per order' "$SA"
pin "operator-named wall-clock peak exemption" grep -qF 'operator-named wall-clock time is exempt from this peak deferral' "$QP"
pin "clocked-order overlay receiving-session duty" grep -qF 'Clocked operator order duty (added 2026-10-05' "$Z"
pin "clocked-order overlay family clause" grep -qF 'Clocked-order family (added 2026-10-05' "$Z"
pin "clocked-order overlay peak exemption" grep -qF 'fire stays at its requested minute despite peak' "$Z"
pin "authoring blueprint clocked-order closing duty" grep -qF 'CLOCKED OPERATOR ORDER DUTY' "$TA"
pin "authoring chaining guards except the clocked-order arm" test "$(grep -oF 'the clocked operator order arming duty' "$TA" | wc -l | tr -d ' ')" -eq 2
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }
python3 - "$S" "$SA" "$GU" "$DE" "$QP" "$SC" "$SF" "$FC" <<'EOF' | route_heredoc_stream # r7 F1: propagate the block status; without this the block is fail-open at the exit-code surface 
import json, re, sys
# post-split homes (maintenance-skill-size-refactor plan, Task 3): the
# operative regions moved to the per-concern modules, so this block reads the
# CANONICAL CONCATENATION (router, then survey-arms, guards, decisions,
# quota-policy, scheduling, state-file - the original document order) for its
# region cuts and ordering checks; the guard order reads the guards module,
# the decision order the decisions module, the runtime-primitive absence
# covers every operative maintenance file, and the state schema reads the
# state-file module's own section
parts = [open(sys.argv[i]).read() for i in range(1, 8)]
s = "".join(parts)
sf = parts[6]
gu = parts[2]
de = parts[3]
def need(text, anchor):
    if anchor not in text:
        print("PIN FAIL: missing anchor %s" % anchor); sys.exit(1)
order_ok = (lambda seq, text: all(text.find(a) != -1 and text.find(a) < text.find(b, text.find(a))
             for a, b in zip(seq, seq[1:])))
if not order_ok(["G1e (execution lane)", "G1a (authoring lane)", "G2 (failure cap)", "G3 (joint state)"], gu):
    print("PIN FAIL: guard order G1e<G1a<G2<G3 (guards module)"); sys.exit(1)
if not order_ok(["D1 (execute)", "D4 (propose park)", "D2 (author)", "D3 (no-op)"], de):
    print("PIN FAIL: decision order D1<D4<D2<D3 (decisions module)"); sys.exit(1)
for name, text in (("SKILL.md", parts[0]), ("survey-arms.md", parts[1]), ("guards.md", gu), ("decisions.md", de), ("quota-policy.md", parts[4]), ("scheduling.md", parts[5]), ("state-file.md", sf)):
    if re.search(r'Cron(Create|List|Update|Delete)|OffPeak(Create|List)', text):
        print("PIN FAIL: %s names a runtime primitive (must stay runtime-agnostic)" % name); sys.exit(1)
need(sf, "## State file")
m = re.search(r"```json\n(.*?)```", sf.split("## State file", 1)[1].split("\n## ", 1)[0], re.S)
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
# state durability plan Task 4: the additive pending_rearm field joins the
# schema-4 block (checked against the parsed doc, so deleting the literal
# line, or breaking the block's JSON, fails here); the loop_mode half of this
# check retired with the field (two-mode loop policy plan Task 2, the
# zero-survivor gate below carrying the absence direction)
if "pending_rearm" not in doc:
    print("PIN FAIL: top-level pending_rearm missing from the state schema"); sys.exit(1)
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
step3 = s.split("\n### Step 3: decision")[1].split("### Step 4")[0]
for needle in ("quota_at_decision",
               "D1 defers the execution dispatch past the reset and D2 defers the authoring dispatch",
               "must cite an explicit non-quota reason"):
    if needle not in step3:
        print("PIN FAIL: Step 3 lacks the quota decision needle %r" % needle); sys.exit(1)
need(s, "### Step 1: survey"); need(s, "### Step 2")
step1 = s.split("\n### Step 1: survey")[1].split("### Step 2")[0]
if "pending_dispatch" not in step1:
    print("PIN FAIL: pending_dispatch reader missing from the Step 1 list"); sys.exit(1)
# the maintenance survey head-bytes rule (plan
# 2026-10-02-maintenance-survey-head-bytes-rule.md): the Step 1 corpus
# freshness rule needles, region-scoped per the suite's vacuous-canary
# doctrine ("a whole-file grep is satisfied by a stray copy, and deleting
# the Pending re-arm reader bullet empties the region and fails here";
# that sentence wraps across two comment lines in this file)
for needle in ("Corpus freshness rule",
               "git show HEAD:<path>",
               "git status --porcelain --untracked-files=no",
               "not-yet-landed",
               "git ls-tree HEAD --name-only",
               "the rolling prompt log's own write discipline",
               "working-tree-only by construction",
               "never records absence",
               "keep their current semantics"):
    if needle not in step1:
        print("PIN FAIL: Step 1 lacks the corpus freshness rule needle %r" % (needle,)); sys.exit(1)
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
# review r2 F7: the r1-added operative consume-semantics span pinned
# region-scoped (the Revisions-ledger prose paraphrases it, so a whole-file
# grep would be vacuous); the loop-mode-held retention gate pin retired with
# the retention itself (two-mode loop policy plan Task 2)
if "never a precondition" not in step1:
    print("PIN FAIL: Step 1 lacks the pending_rearm consume-semantics span"); sys.exit(1)
# review r3 F12: the consume pin above keys on the generic phrase, so pin the
# crash-window span itself (deleting only the survival clause must fail)
if "only after the re-arm's state edit has survived" not in step1:
    print("PIN FAIL: Step 1 lacks the pending_rearm consume crash-window span"); sys.exit(1)
# review r4 F7: the surviving r3 Step 1 contracts (the reader refusal branch
# and the cannot-decide signal), region-scoped to the Step 1 region (the
# ledger paraphrases these contracts and carries none of the spans;
# region-scoping keeps the pin robust against future ledger prose; deleting
# either sentence empties its span and fails here); the label-precedence
# contract retired with the loop-mode-held retention (two-mode loop policy
# plan Task 2)
for needle in ("record the structured-first-line `rearm_note` under the reader-side token",
               "a set `pending_rearm` is itself a cannot-decide signal"):
    if needle not in step1:
        print("PIN FAIL: Step 1 lacks the r3 Step 1 contract span %r" % needle); sys.exit(1)
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
if not sched_turn_class or "the `authoring_cycle_gate` clear when the turn carries an explicit user directive" not in sched_turn_class:
    print("PIN FAIL: scheduler-turn writer class lacks the authoring_cycle_gate clear membership"); sys.exit(1)
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
if not rot_class or "the `authoring_cycle_gate` clear when the session carries an explicit user directive" not in rot_class:
    print("PIN FAIL: rearm-on-touch writer class lacks the authoring_cycle_gate clear membership"); sys.exit(1)
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
step0 = s.split("\n### Step 0: context load")[1].split("### Step 1: survey")[0]
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
# review r2 F7: the self-heal attempt-bound span, region-scoped to the Step 0
# region (the writer-classes line paraphrases it, so a whole-file grep would be
# satisfied by a stray copy; deleting the attempt-bound sentence empties the
# region and fails here)
if "suppresses the repair for that touch" not in step0:
    print("PIN FAIL: step 0 lacks the self-heal attempt-bound span"); sys.exit(1)
# state_region (kept for the pending_rearm paragraph pins below; the
# loop_mode withdrawal-arm and cleared_at pins retired with the loop_mode
# field paragraph itself, two-mode loop policy plan Task 2)
# the State file section moved to the state-file module (the
# maintenance-skill-size-refactor split); the region reads that module
state_region = open(sys.argv[7]).read().split("## State file", 1)[1].split("\n## ", 1)[0]
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
# the failure-detection section moved to its own module (the
# maintenance-skill-size-refactor split); the region reads that module
fc = open(sys.argv[8]).read()
need(fc, "## Failure detection and the failure cap")
failure_region = fc.split("## Failure detection and the failure cap", 1)[1].split("\n## ", 1)[0]
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
heredoc_settle "${PIPESTATUS[0]}"
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

# --- two-mode loop policy zero-survivor gate (plan
# docs/history/plans/completed/2026-10-06-two-mode-loop-policy.md, Task 2) ---
# The retired loop_mode machinery must survive nowhere on the governed
# surfaces: no loop[_-]mode spelling outside SKILL.md's Revisions ledger, and
# none at all in zcode.md or prompt-templates.md (neither carries a Revisions
# heading). The suite is the gate's home, not a target: its own literals here
# are the gate's, so inserting either spelling into any governed surface
# fails the matching count.
n=$(awk '/^## Revisions/{exit} {print}' "$S" | grep -cE 'loop[_-]mode' || true)
[ "$n" -eq 0 ] || { recorded_red_check "SKILL.md carries loop[_-]mode references outside Revisions" "PIN FAIL: SKILL.md carries $n loop[_-]mode references outside Revisions" || fail=1; }
n=$(grep -cE 'loop[_-]mode' "$Z" || true)
[ "$n" -eq 0 ] || { recorded_red_check "zcode.md carries loop[_-]mode references" "PIN FAIL: zcode.md carries $n loop[_-]mode references" || fail=1; }
n=$(grep -cE 'loop[_-]mode' "$P" || true)
[ "$n" -eq 0 ] || { recorded_red_check "prompt-templates.md carries loop[_-]mode references" "PIN FAIL: prompt-templates.md carries $n loop[_-]mode references" || fail=1; }
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

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
# state durability plan Tasks 2 and 4: the recipe's mode-appendix clause pins
# (the clause pin and its content, normalization, and canonical-template
# companions) retired with the clause itself: the two-mode loop policy plan
# Task 2 deleted the Mode appendix paragraph whole, so the spans no longer
# exist to protect. The Cron-tool boundary's reduced-toolset inheritance note
# pin stays below.
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
[ "$(grep -oF 'One-recorded-mutation carve-out' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "carve-out anchor count" "PIN FAIL: carve-out anchor count" || fail=1; }
[ "$(grep -oF 'exactly ONE mutating call implementing that recorded decision' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "single-call bound count" "PIN FAIL: single-call bound count" || fail=1; }
[ "$(grep -oF 'never curtails an advancing dispatch' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "advancing-dispatch scoping count" "PIN FAIL: advancing-dispatch scoping count" || fail=1; }
[ "$(grep -oF 'The bound counts decided mutations, not primitive calls' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "bound unit clause count" "PIN FAIL: bound unit clause count" || fail=1; }
# bound unit-clause parenthetical count (dfm loop-guard successor)
[ "$(grep -oF "a parent re-arm's shape is per the recipe's operative shape (delete-plus-create today; the recycling leg only if a verified flip reopens it)" "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "bound unit-clause parenthetical count" "PIN FAIL: bound unit-clause parenthetical count" || fail=1; }
[ "$(grep -oF 'any refusal after that single call takes the existing escalation paths' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "escalation-routing count" "PIN FAIL: escalation-routing count" || fail=1; }
[ "$(grep -oF "must stop touching automation primitives immediately after it regardless of the call's outcome" "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "stop-bound tail count" "PIN FAIL: stop-bound tail count" || fail=1; }
[ "$(grep -oF "the loop's signature appeared (two listings, no mutating step between them)" "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "guard-signature restatement count" "PIN FAIL: guard-signature restatement count" || fail=1; }
[ "$(grep -oF 'a state-first write that preceded the first listing' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "state-first gate count" "PIN FAIL: state-first gate count" || fail=1; }
[ "$(grep -oF 'a decision recorded only in chat narration does not qualify' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "narration-exclusion count" "PIN FAIL: narration-exclusion count" || fail=1; }
[ "$(grep -oF 'or the pending record it takes as its own' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "decision-ownership count" "PIN FAIL: decision-ownership count" || fail=1; }
[ "$(grep -oF 'an explicit user instruction to proceed outranks them' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "operator-override count" "PIN FAIL: operator-override count" || fail=1; }
[ "$(grep -oF 'records its decided re-arm in the state file before its first primitive call' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "single-call decision-write mandate count" "PIN FAIL: single-call decision-write mandate count" || fail=1; }
[ "$(grep -oF 'must name the mechanical recovery' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "escalation-note recovery duty count" "PIN FAIL: escalation-note recovery duty count" || fail=1; }
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

# --- quota-aligned cadence pins (plan 2026-09-21-maintenance-turn-self-scheduling-cadence, Task 1) ---
# Count-gated pins for the overlay's cadence rule and Turn-start carrier re-arm
# duty. Each span below is unique-span whole-file (measured on the post-Task-1
# tree: each occurs exactly once in zcode.md), so a count of exactly 1 fails
# both a deletion and a stray duplicate copy; the fallback cadence literal is
# rescoped here to exactly once (the never-dark fallback branch is its only
# legal home after the fixed cadence was superseded).
python3 - "$Z" <<'EOF' | route_heredoc_stream # r7 F1: propagate the block status; without this the block is fail-open at the exit-code surface 
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
heredoc_settle "${PIPESTATUS[0]}"
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

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
python3 - "$TA" "$TE" "$DC" <<'EOF' | route_heredoc_stream # r7 F1: propagate the block status; without this the block is fail-open at the exit-code surface 
import sys
# the split (maintenance-skill-size-refactor plan Task 4): the byte-identical
# FIRST ACTION paragraphs moved to duties-core.md as the canonical copy, so
# the per-blueprint count-2 checks read the per-kind files plus the core copy
ta, te, dc = (open(sys.argv[i]).read() for i in range(1, 4))
p = ta + te + dc
# post-split counts re-derived (Task 4): the byte-identical FIRST ACTION
# paragraphs are one canonical copy in duties-core.md, so the per-blueprint
# count-2 shape is now exactly-once over the core copy (the blueprints carry
# the span by reference; a stray second copy anywhere fails)
def two(span):
    n = p.count(span)
    if n != 1:
        print("PIN FAIL: blueprint cadence span count %d != 1 across the per-kind files plus the duties core: %s" % (n, span)); sys.exit(1)
two("in the form the recipe's cadence rule selects")
two('record the armed carrier\'s fire time into "next_turn_at"')
EOF
heredoc_settle "${PIPESTATUS[0]}"
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }
# review r1 C2: enforcement pins for the Task 2 freeze literals recorded in the
# comment block above (both stood exactly twice before Task 2 and must not
# return; the superseding origin is Task 2 of plan
# 2026-09-21-maintenance-turn-self-scheduling-cadence). Fixed-string greps, so
# the pin fires only on the verbatim superseded prose returning in any copy.
expect_absent "superseded fixed-form blueprint parenthetical must be absent from prompt-templates.md" '(its title, its cadence cron, recurring true, enabled true, its prompt template with {REPO_ROOT} filled)' "$P"
expect_absent "superseded parent_automation_id-only re-arm closing must be absent from prompt-templates.md" 'then update "parent_automation_id" as a targeted field edit' "$P"
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

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
python3 - "$S" "$SF" <<'EOF' | route_heredoc_stream # r7 F1: propagate the block status; without this the block is fail-open at the exit-code surface 
import sys
# the schema spans re-keyed to the state-file module (the
# maintenance-skill-size-refactor split); the overlay-duty span stays in the
# router
s, sf = open(sys.argv[1]).read(), open(sys.argv[2]).read()
def one(text, home, span):
    n = text.count(span)
    if n != 1:
        print("PIN FAIL: cadence %s span count %d != 1: %s" % (home, n, span)); sys.exit(1)
one(s, "SKILL.md", "the runtime overlay's Turn-start carrier re-arm duty")
one(sf, "state-file.md", '"next_turn_at": null,')
one(sf, "state-file.md", "in the future and the recorded `parent_automation_id` is ENABLED")
one(sf, "state-file.md", "the loop carrier automation's id")
EOF
heredoc_settle "${PIPESTATUS[0]}"
# the ledger span moved with the Revisions ledger (changelog extraction plan,
# Task 1): it is count-gated in the extracted changelog file now, so a future
# changelog entry naming the plan again still cannot re-satisfy it
python3 - "$CL" <<'EOF2' | route_heredoc_stream
import sys
c = open(sys.argv[1]).read()
n = c.count("maintenance-turn-self-scheduling-cadence")
if n != 1:
    print("PIN FAIL: cadence CHANGELOG span count %d != 1: maintenance-turn-self-scheduling-cadence" % n); sys.exit(1)
EOF2
heredoc_settle "${PIPESTATUS[0]}"
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

# --- prompt-templates.md child-duty needles (state-driven rearm, successor dispatch, resume) ---
pin "state-first rearm duty" grep -qF 'state-first, without listing first' "$TA"
pin "rearm anti-loop guard" grep -qF 'listed twice without a mutating step' "$TE"
pin "successor carve-out in the opening guard" grep -qF 'beyond the re-arm duty below and the single successor-dispatch duty below' "$TE"
pin "successor fallback delete-plus-create" grep -qF 'fall back to deleting your own spawner record whatever its current form' "$TE"
pin "successor both-legs-fail re-create" grep -qF 'when both legs fail' "$TE"
pin "successor adopt matcher repo containment" grep -qF 'whose prompt also contains the resolved repository root is present, adopt its id into "parent_automation_id" (targeted field edit) and end without creating' "$TE"
pin "resume rule in the execution payload" grep -qF 'this is a resume run' "$TE"
pin "rearm lingered-record deletion in blueprints" grep -qF 'deleting your own lingered' "$DC"
pin "success-via-existing confirmation" grep -qF 'counts as success only after one more listing confirms' "$DC"
pin "successor fire time names the full quota leg" grep -qF 'runtime-fit, deferred-window, peak-pricing, and floor rules' "$TE"
pin "successor entry records requested_at" grep -qF 'requested_at carrying the originally requested fire time' "$TE"
# scheduler ops lanes and durability plan Task 4: the durable HOST CAVEAT.
# The re-arm caveat span sits inside the byte-identical FIRST ACTION
# paragraphs; the plain grep here is a presence canary only (satisfiable by
# a single occurrence), and the python parity block below pins the count
# exactly (2 for the re-arm span, one per blueprint paragraph; 1 for the
# successor reshape leg; the deviation-list entries paraphrase and must not
# carry the spans, or those counts drift).
pin "blueprint re-arm HOST CAVEAT present" grep -qF 'HOST CAVEAT: any recycling update whose echoed record is not verifiably the intended form' "$TE"
pin "successor reshape-leg HOST CAVEAT present" grep -qF 'HOST CAVEAT: any recycling update whose echoed record is not verifiably the intended form (enabled true, recurring false, a future nextRunAt matching the successor fire time, confirmed by a listing) is treated as a refusal' "$TE"
# Review r1 F8: the 'runtime-fit, deferred-window, ...' needle above occurs
# TWICE in prompt-templates.md (blueprint + deviation paraphrase), so
# reverting only the blueprint's --fire-at sentence stayed green; pin the
# blueprint-unique span too, and keep the superseded fire-time span absent.
pin "successor blueprint names the probe --fire-at mode" grep -qF 'using its --fire-at mode with --need-minutes set to this lane' "$TE"
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
# post-split counts (Task 4): the byte-identical shared duty sets are one canonical copy in duties-core.md
[ "$(grep -oF "the overlay's one-recorded-mutation carve-out" "$DC" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "blueprint carve-out reference count" "PIN FAIL: blueprint carve-out reference count" || fail=1; }
[ "$(grep -oF 'and this session owns that record' "$DC" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "blueprint ownership clause count" "PIN FAIL: blueprint ownership clause count" || fail=1; }
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

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
pin "authoring blueprint checkpoint duty" test "$(grep -oF 'after each blueprint step block, at a boundary only, never mid-task, log one telemetry record (skill: plans-authoring) to docs/tmp/authoring/<plan-slug>/context.jsonl' "$TA" | wc -l | tr -d ' ')" -eq 2
pin "execution blueprint checkpoint duty" test "$(grep -oF 'after each blueprint step block, at a boundary only, never mid-task, log one telemetry record (skill: execute-plan) to docs/tmp/execute-plan/<plan-slug>/context.jsonl' "$TE" | wc -l | tr -d ' ')" -eq 1
# P51 origin 2 payload duty sentence sets and slice reconciliation (same plan,
# Task 2): the payload paragraph's compact RE-ARM DUTY, CONTEXT CHECKPOINTS,
# and FINAL STEP sets are count-gated so the payload stays self-contained for
# the duties a child session must see (the deviation-ledger entry paraphrases
# and must not carry the spans, or these counts drift), and the Step 5
# authoring slice wording is pinned to the payload-paragraph assembly it must
# describe (the pin pair above keeps its prescribed names for the execute-plan
# telemetry coupling sentence).
pin "authoring slice payload-region wording" grep -qF 'observed dispatch practice transmits the authoring blueprint' "$SC"
# 2026-09-25 parked-dependency visibility Task 6: the unblock template's
# recipe-delegating re-arm sentences take the count to 2
# post-split: one copy stayed in the authoring blueprint, its byte-identical
# FIRST ACTION copy moved to the duties core (Task 4)
pin "payload re-arm sentence set count" test "$(cat "$TA" "$TU" | grep -oF 'restore the maintenance loop parent state-first, without listing first' | wc -l | tr -d ' ')" -eq 2
# 2026-09-25 parked-dependency visibility Task 6: the unblock template's
# closing park-discharge and compaction duties take the counts up by one each;
# 2026-09-28 continuation policy plan: the tails are reworded (compaction is
# operator-only) and gated by the plan's positive-count checks, the prefix stays
# post-split: the per-kind files carry their counts individually (2+1+1)
pin "FINAL STEP prefix count" test "$(cat "$TA" "$TE" "$TU" | grep -oF 'FINAL STEP, after the report:' | wc -l | tr -d ' ')" -eq 4

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
pin "G1a authoring claim discovery arm" grep -qF 'authoring-claims' "$SA"
pin "authoring blueprint claim duty" grep -qF 'authoring-claims' "$TA"
pin "foreign-claim clobber-witness span present" grep -qF "never clobber the first writer's witness" "$TA"
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
pin "claim create noclobber recipe present" grep -qF 'set -C; printf' "$TA"
pin "takeover re-read-before-delete span present" grep -qF 're-reads the claim file immediately before the unlink' "$TA"
pin "ownership re-check stand-down clause present" grep -qF 'stands this session down from authoring the item' "$TA"
pin "unparseable-session-line disposition present" grep -qF 'no parseable session: line is treated as foreign' "$TA"

# --- prompt-templates.md blueprint integrity ---
python3 - "$DC" "$TA" "$TE" "$TU" "$Z" "$D" <<'EOF' | route_heredoc_stream # r7 F1: propagate the block status; without this the block is fail-open at the exit-code surface 
import re, sys
# the split (Task 4): the dispatch-slice tag checks read the per-kind files
# (the authoring pair in template-authoring.md, the execution opener in
# template-execution.md, the unblock wrapper's closer in template-unblock.md)
dc_text = open(sys.argv[1]).read()
p = "".join(open(sys.argv[i]).read() for i in range(2, 5))
z, d = open(sys.argv[5]).read(), open(sys.argv[6]).read()
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
# post-split parity (Task 4): the byte-identical FIRST ACTION paragraphs are
# ONE canonical copy in duties-core.md - the parity guarantee becomes the core
# copy's presence at exactly one (the byte-identity the old two-way comparison
# enforced is now single-homed by construction; a stray second copy anywhere
# in the per-kind files fails the count)
dc_text = open(sys.argv[1]).read()
paras = [norm(m.group(0)) for m in
         re.finditer(r"FIRST ACTION, before any gate or phase: re-arm the maintenance loop state-first, without listing first\..*?reading that note re-arms per the recipe\.", dc_text, re.S)]
if len(paras) != 1:
    print("PIN FAIL: the duties core does not carry the re-arm duty paragraph exactly once"); sys.exit(1)
if re.search(r"FIRST ACTION, before any gate or phase: re-arm the maintenance loop state-first, without listing first\.", p):
    print("PIN FAIL: a blueprint carries its own FIRST ACTION copy beside the duties-core reference"); sys.exit(1)
for needle in ('"rearm_note"', "loop-parent-missing", "parent_automation_id",
               "Recurring automation recipe", "after two retries",
               "counts as success only after one more listing confirms",
               "listed twice without a mutating step", "first applicable step wins",
               "(1) when", "(2) when", "(3) when"):
    if needle not in paras[0]:
        print("PIN FAIL: re-arm paragraph escalation drifted (missing %s)" % needle); sys.exit(1)
# state durability plan Task 5: the re-arm duty paragraph carries the
# primitive-precheck sentences (before the reshape and the create/recycle
# legs); paras[0] membership plus the byte-identity parity above cover both
# blueprints, so deleting either sentence from either paragraph fails a pin
# (the appendix-sourcing needle retired with the sourcing sentence,
# two-mode loop policy plan Task 2)
for needle in ("assert the session actually owns",):
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
# post-split (Task 4): the caveat's byte-identical copies live in the single
# duties-core paragraph; exactly-once over the core
if dc_text.count(rearm_caveat) != 1 or p.count(rearm_caveat) != 0:
    print("PIN FAIL: re-arm HOST CAVEAT must be exactly-once in duties-core and absent from the blueprints"); sys.exit(1)
succ_caveat = "HOST CAVEAT: any recycling update whose echoed record is not verifiably the intended form (enabled true, recurring false, a future nextRunAt matching the successor fire time, confirmed by a listing) is treated as a refusal"
if p.count(succ_caveat) != 1:
    print("PIN FAIL: successor reshape-leg HOST CAVEAT count %d != 1" % p.count(succ_caveat)); sys.exit(1)
# state durability plan Tasks 3-5: whole-file count floor for the blueprint
# precheck sentence (the mode-appendix sourcing floor retired with the
# sourcing sentence, two-mode loop policy plan Task 2).
# Review r1 F14: the primitive-precheck needle is pinned to the exact total 5
# (the re-arm paragraphs carry it twice each, before the reshape and the
# create/recycle legs, and the successor leg once), so any single deletion
# anywhere fails it; the per-paragraph distribution below is pinned at 2 for
# the both-legs-identical-deletion shape: the byte-identity parity pin already
# fails a single-leg deletion first, so this pin's marginal direction is the
# both-legs deletion, which keeps the two paragraphs byte-identical and drops
# the needle from both at once (the successor leg's copy is covered by its own
# region membership check above)
# post-split totals (Task 4): the split corpus carries the five copies
# individually (2 authoring + 1 execution + 1 unblock + 1 duties core); the
# per-paragraph distribution reads the core copy at 2
if p.count("assert the session actually owns") != 1 or dc_text.count("assert the session actually owns") != 2:
    print("PIN FAIL: primitive precheck distribution drifted (want 3 across the blueprints + 2 in the duties core)"); sys.exit(1)
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
# done-skill ordering pin (re-aimed 2026-10-11, the done target-state flip):
# the rearm-on-touch pointer precedes the `## Step 0` heading in the collapsed
# SKILL.md, which carries that heading byte-verbatim
need(d, "Before Step 0, in a repository that resolves the maintenance skill")
if not d.index("Before Step 0, in a repository that resolves the maintenance skill") < d.index("## Step 0: Acquire project done lock"):
    print("PIN FAIL: done-skill rearm-on-touch pointer must precede the Step 0 heading"); sys.exit(1)
need(d, "## Step 0: Acquire project done lock")
# confinement pins (origin 3 scope note): execution-only spans stay inside the
# execution inner block, split off the blueprint headings and dispatch-slice tags
def confined(span):
    if p.count(span) != 1 or inner.count(span) != 1:
        print("PIN FAIL: execution-only span left the execution inner block: %s" % span); sys.exit(1)
confined("beyond the re-arm duty below and the single successor-dispatch duty below")
confined("this is a resume run")
# state durability plan Tasks 4 and 5: the successor both-legs-fail leg carries
# its own precheck sentence (before the reshape leg) and its own
# pending_dispatch park write (the both-legs-fail tail; the appendix sentence
# retired with the sourcing re-aims, two-mode loop policy plan Task 2); both
# are pinned region-scoped to the successor paragraph (everything in the
# execution inner block after the SUCCESSOR DISPATCH anchor), so a single-leg
# deletion cannot hide behind the other legs' copies (the park write pin is
# review r1 F5)
succ = inner.split("SUCCESSOR DISPATCH")[1]
for needle in ("assert the session actually owns",
               'write "pending_dispatch" (kind execute'):
    if needle not in succ:
        print("PIN FAIL: successor dispatch leg lacks the state-durability needle %s" % needle); sys.exit(1)
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
for needle in ("git update-ref refs/heads/<default> <the landing commit's first parent> <the landing commit>",
               "git show refs/heads/<default>:"):
    need(norm(auth_bodies[0]), needle)
# (the retired pathspec staging needle was dropped from the tuple above by the
# 2026-10-02 worktree-complete landing lifecycle; the literal is frozen absent
# whole-file beside the retired-create-literal precedent below. The
# compare-and-swap needle was re-pointed 2026-10-11, plan
# docs/history/plans/2026-10-11-execute-plan-boundary-reliability.md Task 2,
# from the retired temp-index forward CAS to the retained verification-failure
# arm's recorded inverse compare-and-swap, the helper flow holding no
# read-tree capture.)
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
# unblock-landing-worktree-rework plan Task 3 pins (b) and (c): the reworked
# step 6 delegation sentence (the Worktree arm named with its file+section
# anchor) and the verify-squash needle counted exactly once inside the unblock
# fenced body. The whole-file landing-race discipline span pin below stays
# green off the deviation-list history entries, so the body-scoped count is
# the real enforcement that the clause survives the rewrite.
rework_delegation = "Worktree arm of the execution blueprint's final-merge paragraph in `agents/skills/maintenance/prompt-templates.md`"
if norm(p).count(rework_delegation) != 1:
    print("PIN FAIL: unblock step 6 Worktree-arm delegation sentence count %d != 1 (wrap-tolerant whole-file)" % norm(p).count(rework_delegation)); sys.exit(1)
if rework_delegation not in norm(unblock_bodies[0]):
    print("PIN FAIL: unblock step 6 Worktree-arm delegation sentence missing from the unblock fenced body"); sys.exit(1)
verify_squash_needle = "verify the squash against the actual pre-landing main"
n = norm(unblock_bodies[0]).count(verify_squash_needle)
if n != 1:
    print("PIN FAIL: verify-squash needle count %d != 1 inside the unblock fenced body" % n); sys.exit(1)
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
heredoc_settle "${PIPESTATUS[0]}"
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

# --- rearm-on-touch surfaces (Task 4) ---
pin "step 0 rearm-on-touch check" grep -qF 'rearm-on-touch check: consult the scheduler state file first' "$S"
expect_absent "superseded listing-first rearm-on-touch trigger must be absent from SKILL.md" 'when the automation listing shows no ENABLED parent' "$S"
pin "done-skill rearm-on-touch pointer" grep -qF 'rearm-on-touch check defined in the maintenance skill' "$D"
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

# --- budget-gate resume mirrors (P6 origins 1-2) ---
PL="$repo/agents/skills/plans/SKILL.md"
R="$repo/agents/skills/review-loop/SKILL.md"
RC="$repo/agents/skills/execute-plan/runtime-contract.md"
for f in "$E" "$PL" "$R" "$RC"; do
  [ -f "$f" ] || { echo "missing $f"; fail=1; }
done
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }
# Removed 2026-10-14, arm remove-beside-provenance: the pinned resume-fit
# --fire-at and resume-pricing defer_to spans were adapter-era execute-plan
# prose deliberately removed by the certified landing e0d7d6961 (the
# sequential-only adapter-removal plan's Task 2); the literals survive only in
# the owning completed plan
# docs/history/plans/completed/2026-09-19-scheduler-operations-discipline-quota-peaks-locks.md.

# --- company task-branch placement choice and PR-pairing pins (plan
# docs/history/plans/2026-10-13-execute-plan-company-task-branch.md, Task 3) ---
# The Worktree-first standard placement paragraph's company-profile arm: the
# per-run operator choice clause (keep current or create a named task branch)
# and the company task-branch arm's PR-pairing consequence clause (the task
# branch as source, the confirmed base as target). Count-gated exactly 1 each
# on the execute-plan skill so the fragments cannot drift out of their
# arm-local scopes.
# Re-aimed 2026-10-19 (plan docs/history/plans/2026-10-14-skill-monolith-module-extraction.md Task 2): the needle's span moved verbatim to agents/skills/execute-plan/worktree-first.md.
pin "execute-plan company placement arm's per-run task-branch choice clause" test "$(grep -oF 'gains the per-run operator choice beside that base-branch-only rule' "$repo/agents/skills/execute-plan/worktree-first.md" | wc -l | tr -d ' ')" -eq 1
pin "execute-plan company task-branch arm's PR-pairing consequence clause" test "$(grep -oF 'names the PR pairing (the task branch as source, the confirmed base as target)' "$repo/agents/skills/execute-plan/worktree-first.md" | wc -l | tr -d ' ')" -eq 1

# Removed 2026-10-14, arm remove-beside-provenance (mirror coherence): this
# passing mirror cross-referenced the canonical resume-fit and resume-pricing
# spans adjudicated away above (deliberately removed by the certified landing
# e0d7d6961), so it was stale by dependency; the mirror sentence left
# agents/skills/plans/SKILL.md in the same edit.
pin "plans cap is reflection, not automatic stop" grep -qF 'Cap alone does not stop reviews or trigger reconciliation' "$PL"
pin "review-plan cap is reflection, not operator ask" grep -qF 'Cap alone does not require reconciliation or an operator ask' "$repo/agents/skills/review-plan/SKILL.md"
pin "plans dependency-derived reconciliation gate present" grep -qF 'Dependency edges inform ordering only and never authorize inclusion' "$PL"
pin "review-plan dependency-derived scope audit present" grep -qF 'A dependency-derived deliverable with no recorded decision is a blocking correctness-completeness finding' "$repo/agents/skills/review-plan/SKILL.md"

# --- plan review readiness boundary pins (plan 2026-10-07-plan-detail-boundary, Task 2) ---
# Presence pins over the changed skill spans; absence pins over the removed
# guessed-inventory authoring rules. scripts/test_plan_review_boundary_examples.py
# executes the paired boundary fixtures the review-plan skill carries, so the
# fixture markers are load-bearing spans.
pin "plans plan-owned behavior and safety decisions rule wired" grep -qF 'Plan-owned behavior and safety decisions; required' "$PL"
pin "plans primary class anchors rule wired" grep -qF 'Every plan task that owns production behavior declares a `Primary class anchors:` block' "$PL"
pin "plans no-guessed-inventory rule wired" grep -qF 'The plan does not name supporting production or test paths, test identities, fixture wiring, schema resources, or exact task commands' "$PL"
pin "plans observable witness format bullet wired" grep -qF 'Observable witness format' "$PL"
pin "plans gist placement directly after Why wired" grep -qF 'directly after Why and before Outcome' "$PL"
pin "plans task template primary anchor wired" grep -qF -- '- `OwningClass` in `path/to/ExistingFile.ext`' "$PL"
expect_absent "Evidence-declaration plan-authoring rule must be gone from plans" '**Evidence declaration; required:**' "$PL"
expect_absent "guessed test-identity template items must be gone from plans" 'SomeClassTest#methodName' "$PL"
expect_absent "Evidence-block sole-seeding-source claim must be gone from plans integration points" 'is the sole source for execute-plan' "$PL"
RPB="$repo/agents/skills/review-plan/SKILL.md"
pin "review-plan readiness boundary clarification wired" grep -qF 'a behavior-complete plan is ready without test identities' "$RPB"
pin "review-plan behavior and safety closure matrix wired" grep -qF 'Behavior and safety closure matrix' "$RPB"
pin "review-plan paired boundary fixture ready arm wired" grep -qF 'BOUNDARY-READY-FIXTURE' "$RPB"
pin "review-plan paired boundary fixture blocked arm wired" grep -qF 'BOUNDARY-BLOCKED-FIXTURE' "$RPB"
pin "review-plan boundary regression test wired" grep -qF 'scripts/test_plan_review_boundary_examples.py' "$RPB"
expect_absent "plan-closure inventory audit must be gone from review-plan" 'Plan-closure matrix' "$RPB"
expect_absent "Evidence:-per-task prerequisite must be gone from execute-plan" 'one `Evidence:` block per task' "$E"
expect_absent "Evidence-declaration seeding remedy must be gone from execute-plan" 'adding an Evidence block changes the evidence class' "$E"

# --- dfm gate-suite successor pins (P56 Task 4; archived plan bytes frozen) ---
# dfm r1 F5 successor (whole-file; the archived plan's gates saw only the extracted template region)
[ "$(grep -oF 'Driving force: <tag>' "$PL" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "driving-force template count (F5)" "PIN FAIL: driving-force template count (F5)" || fail=1; }
[ "$(grep -oF 'TLDR: <what changes>' "$PL" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "TLDR template count (F5)" "PIN FAIL: TLDR template count (F5)" || fail=1; }
# dfm r1 F8 successor (taxonomy tail and park-triage half had no needles)
pin "dfm r1 F8 successor external-cites-source needle" grep -qF 'where `external` must cite its source' "$PL"
pin "dfm r1 F8 successor park-triage needle" grep -qF 'why park-triage would or would not take it' "$PL"
pin "dfm r2 F1 successor backlog-origin-none producer line" grep -qF 'otherwise the line reads `Backlog origin: none`' "$PL"
pin "dfm r2 F1 successor driving-principles enumeration" grep -qF 'five driving principles (`efficiency`, `token-usage`, `simplicity`, `code-quality`, `automation`)' "$PL"

# --- budget-gate resume fallback preservation pins (plan 2026-09-21-budget-gate-resume-fallbacks, Task 1) ---
# Freeze-literal origin note: the surviving mirror spans' text was landed by
# plan docs/history/plans/completed/2026-09-21-budget-gate-resume-fallbacks.md
# (commit 8a77ec46 shaped the current mirror wording, re-freeze recorded
# 2026-09-23). The six canonical execute-plan preservation rows were removed
# 2026-10-14, arm remove-beside-provenance: their pinned spans were
# adapter-era execute-plan prose deliberately removed by the certified landing
# e0d7d6961 (the sequential-only adapter-removal plan's Task 2); the literals
# survive only in the owning completed plan
# docs/history/plans/completed/2026-09-21-budget-gate-resume-fallbacks.md.
# The plans-skill mirror spans below live in plans/SKILL.md's own authoring
# text, were not touched by that removal, and stay pinned. A wording change to
# a pinned span is a change to that plan's prescribed text, so reconcile the
# pin and the text in the same edit and record the superseding origin.
# Count-gated (not the grep -qF `pin` helper) so drift fails in either
# direction: exactly 1 fails a deletion and a stray duplicate copy; the mirror
# rung span is count-gated at exactly 3. Reuses the $E and $PL variables the
# mirrors block above sets.
n="$(grep -oF -- 'or when the host idle-time automation rung carries the resume' "$PL" | wc -l | tr -d ' ')"; [ "$n" -eq 1 ] || { recorded_red_check "preservation: mirror carrier-aware record span count != 1" "PIN FAIL: preservation: mirror carrier-aware record span count $n != 1" || fail=1; }
n="$(grep -oF -- "deletes the session's own completed spawner record and retries the create once" "$PL" | wc -l | tr -d ' ')"; [ "$n" -eq 1 ] || { recorded_red_check "preservation: mirror lineage-cap branch span count != 1" "PIN FAIL: preservation: mirror lineage-cap branch span count $n != 1" || fail=1; }
n="$(grep -oF -- 'host idle-time automation rung' "$PL" | wc -l | tr -d ' ')"; [ "$n" -eq 3 ] || { recorded_red_check "preservation: mirror OffPeakCreate rung span count != 3" "PIN FAIL: preservation: mirror OffPeakCreate rung span count $n != 3" || fail=1; }

# --- rate-limited end claim boundary, receipt carrier, and recovery marker (P37 rate-pressure ingestion and quota scheduling plan, Task 1) ---
# Removed 2026-10-14, arm remove-beside-provenance: the seven pinned
# claim-boundary, recovery-marker, and contract-mirror spans were
# adapter-era execute-plan and runtime-contract prose deliberately removed by
# the certified landing e0d7d6961 (the sequential-only adapter-removal plan's
# Task 2); the literals survive only in the owning completed plan
# docs/history/plans/completed/2026-09-22-p37-rate-pressure-ingestion-and-quota-scheduling.md.
# --- backoff floor and scaled panel bounds (P37 rate-pressure ingestion and quota scheduling plan, Task 2) ---
# Removed 2026-10-14, arm remove-beside-provenance: the resume-backoff floor
# span and the three serialized-cap doubling spans met the same fate as the
# Task 1 rows above (removed by the certified landing e0d7d6961; literals
# survive only in the owning completed plan
# docs/history/plans/completed/2026-09-22-p37-rate-pressure-ingestion-and-quota-scheduling.md).
# --- writer/ingester stop-line token format (P37 rate-pressure ingestion and quota scheduling plan, Task 3) ---
# The execute-plan writer-side mirror row was removed 2026-10-14, arm
# remove-beside-provenance: the execute-plan span was removed by the certified
# landing e0d7d6961; the canonical carrier agents/skills/maintenance/failure-cap.md
# keeps its pin (the next row) untouched.
pin "ingestion mirrors the stop-line token format" grep -qF 'a line-initial rate_limited: token followed by an ISO timestamp' "$FC"
# --- typed dispatch-failure records and the follow-up takeover (plan docs/history/plans/2026-10-05-execute-plan-dispatch-failure-resilience.md, Task 1) ---
# Both rows were removed 2026-10-14, arm remove-beside-provenance: the typed
# pre-start `dispatch_failed:` record contract (the dispatch-mode paragraph's
# literal and the tracking-list entry head) was adapter-era execute-plan prose
# deliberately removed by the certified landing e0d7d6961 (the
# sequential-only adapter-removal plan's Task 2); the literals survive only in
# the owning completed plan
# docs/history/plans/completed/2026-10-05-execute-plan-dispatch-failure-resilience.md
# (for the record literal, scripts/test_quota_wall_doctrine.py also asserts it
# against the live SKILL.md and stays byte-identically red since that landing -
# a pre-existing stale drift detector outside this plan's scope). The
# follow-up-takeover paragraph's surviving citations of
# the `dispatch_failed:` line shape were reconciled to the removal in the same
# edit so the skill cites no record shape no surface defines.
# --- dedup ledger decoupled from the capped array (P37 rate-pressure ingestion and quota scheduling plan, Task 4) ---
pin "dedup consults the rolling ledger" grep -qF 'the dedup consults the rolling ledger' "$SF"
pin "ledger rides the same 24-hour window" grep -qF 'pruned to the same 24-hour window' "$SF"
pin "step 6 carries the dedup ledger" grep -qF 'plus the dedup ledger (the ledger is a top-level field' "$SF"
pin "dedup ledger declared in the schema block" grep -qF '"rate_limited_dedup_ledger"' "$SF"
# --- lost-update enumeration and define-once rate_pressure (P37 rate-pressure ingestion and quota scheduling plan, Task 5) ---
pin "lost-update enumeration names the rate rail" grep -qF 'the rate-pressure rail' "$SF"
pin "rate_pressure defined once in the schema block" grep -qF 'the derived count defined in State file' "$DE"
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

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
# P37 Task 3 (tmp-dir substitution sentence), moved 2026-10-06 onto the
# reworded span: the Telemetry bullet's substitution rule scoped to the
# per-run telemetry log paths only, with the fixed Phase 4 archive
# destination .ai-playbook/metrics/ carved out (gitignored, docs-branch
# preserved) and the maintenance blueprints' payload paths recorded as the
# pinned literal exception.
pin "telemetry substitution rule scopes the per-run telemetry paths" grep -qF 'governs the per-run telemetry log paths this policy names' "$E"
# P48 Task 1 (unlanded-plan worktree cherry-pick): the canonical Worktree-first
# standard's Transfer-in implementation in agents/skills/execute-plan/worktree-first.md
# names the missing-plan remedy for plan bytes living on an unlanded branch.
# Re-aimed 2026-10-19 (plan docs/history/plans/2026-10-14-skill-monolith-module-extraction.md Task 2): the needle's span moved verbatim to agents/skills/execute-plan/worktree-first.md.
pin "worktree bootstrap names the unlanded-plan remedy" grep -qF 'cherry-pick only the plan-authoring commit' "$repo/agents/skills/execute-plan/worktree-first.md"
# P37 Task 4 (turn-usage live verification): the measurement primitive section
# must name the store's turn_usage table (the live-verified source or the
# recorded negative, per the variant applied).
pin "measurement primitive names turn_usage" grep -qF 'turn_usage' "$Z"
# --- worktree-first r3 witness needles (plan
# 2026-09-28-worktree-first-standard-only-mode.md, review round 3 address) ---
# Exactly-once, wrap-tolerant (normalized) presence pins over the canonical
# Worktree-first section's surviving r2/r3 fix-commit paragraph, originally in
# execute-plan SKILL.md, now in agents/skills/execute-plan/worktree-first.md:
# the Provisioned-worktree adoption paragraph, and (removed from the
# pin set 2026-10-08: the Base-branch resolution rule's origin-HEAD fallback
# arm, whose span landing 605761d54 deleted when it removed the class-derived
# base-branch fallbacks and made the confirmed facts base_branch the consumed
# resolution) the surviving paragraph below. Whole-file greps would satisfy a
# stray copy in another file's prose, so the surviving paragraph is scoped to the worktree-first module and counted
# normalized, per the r2 F5 wrap-tolerance convention; wholesale deletion of
# the paragraph empties its count and fails here.
# Re-aimed 2026-10-19 (plan docs/history/plans/2026-10-14-skill-monolith-module-extraction.md Task 2): the Provisioned-worktree adoption paragraph moved verbatim to agents/skills/execute-plan/worktree-first.md; the heredoc target follows the span.
python3 - "$repo/agents/skills/execute-plan/worktree-first.md" <<'EOF' | route_heredoc_stream # r7 F1: propagate the block status; without this the block is fail-open at the exit-code surface 
import sys
e = open(sys.argv[1]).read()
def norm(t): return " ".join(t.split())
for desc, needle in (
    ("Provisioned-worktree adoption paragraph", "Provisioned-worktree adoption"),
):
    n = norm(e).count(needle)
    if n != 1:
        print("PIN FAIL: %s count %d != 1 in execute-plan worktree-first.md" % (desc, n)); sys.exit(1)
EOF
heredoc_settle "${PIPESTATUS[0]}"
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

# --- discovery ladder rung 1 bound (P36 scheduler durability and audit plan, Task 5) ---
# The two rung 1 pin rows and the heredoc's ladder-scoped span checks were
# removed 2026-10-14, arm remove-beside-provenance: the rung 1
# terminal-or-complete bound and fall-through clause were adapter-era
# execute-plan prose deliberately removed by the certified landing e0d7d6961
# (the sequential-only adapter-removal plan's Task 2); the literals survive
# only in the owning completed plan
# docs/history/plans/completed/2026-09-22-p36-scheduler-durability-audit.md.
# The preceding Provisioned-worktree adoption check stays (that span is live).
python3 - "$E" <<'EOF' | route_heredoc_stream # r7 F1: propagate the block status; without this the block is fail-open at the exit-code surface 
import sys
e = open(sys.argv[1]).read()
if "## Live-session discovery ladder" not in e:
    print("PIN FAIL: Live-session discovery ladder section missing from execute-plan SKILL.md"); sys.exit(1)
EOF
heredoc_settle "${PIPESTATUS[0]}"
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

# --- trigger-verb contract surfaces (schedule-vs-execute verb contract plan, Task 3) ---
A="$repo/AGENTS.md"
[ -f "$A" ] || { echo "missing $A"; fail=1; }
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }
pin "SKILL.md trigger-verb subsection anchored" grep -qF 'Trigger verbs (schedule vs execute vs resume)' "$DE"
pin "repo AGENTS.md scheduling verb contract anchored" grep -qF 'Scheduling asks (verb contract)' "$A"

# --- schedule-ask exhaust-delete-first pins (plan
# 2026-10-17-croncreate-cap-delete-own-spawner-leg.md, Task 2) ---
# Count pin over the re-arm surface's landed delete-first ordering sentence
# (the span the operator-ordered schedule surface paragraph names as a
# boundary and must not restate); presence pins over the schedule ask
# contract's opening scheduling requirement, its never-executes-inline
# literal, and the bound clause's owner-naming literal.
[ "$(grep -oF 'the FIRST automation primitive of the decided re-arm is the delete of that record by the state-recorded id' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "re-arm delete-first count" "PIN FAIL: re-arm delete-first count" || fail=1; }
pin "schedule ask bullet 1 opening requirement" grep -qF 'list existing automations first' "$A"
# Added 2026-10-19, plan 2026-10-18-clocked-order-successor-verification Task 3: the
# consult leg's distinctive span (same-edit pin convention).
pin "clocked-order consult verify-successor leg" grep -qF 'runs the read-only operation once per consult' "$SA"
# Added 2026-10-19, plan 2026-10-18-clocked-order-successor-verification Task 4: the stall
# sentence's distinctive span (same-edit pin convention).
pin "rearm hygiene verify-successor stall classification" grep -qF 'is a stall, never healthy idle' "$Z"
pin "schedule ask never-executes-inline" grep -qF 'it never executes the payload in the same turn' "$A"
pin "schedule ask bound clause owner naming" grep -qF 'the operator-ordered schedule surface paragraph in agents/skills/maintenance/zcode.md' "$A"
pin "zcode.md interactive dispatch template anchored" grep -qF 'Interactive dispatch template' "$Z"
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

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
pin "SKILL.md step 5 ladder-precheck precondition anchored" grep -qF 'Ladder precheck: after the quota leg (for a clocked dispatch)' "$SC"
pin "zcode.md Ladder precheck bullet anchored" grep -qF 'Ladder precheck' "$Z"
[ "$(grep -oF 'clocked-primitives-absent' "$Z" | wc -l | tr -d ' ')" -eq 2 ] || { recorded_red_check "clocked-lane stand-down reason count" "PIN FAIL: clocked-lane stand-down reason count" || fail=1; }
[ "$(grep -oF 'idle-primitive-absent' "$Z" | wc -l | tr -d ' ')" -eq 2 ] || { recorded_red_check "idle-lane stand-down reason count" "PIN FAIL: idle-lane stand-down reason count" || fail=1; }
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

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
# RETIRED 2026-10-03 (recurring-task-registry plan Task 8): the operative
# span 'when due and lanes allow, dispatch at most one audit child' belonged
# to the friction-audit consult bullet that the registry migration stubbed;
# replaced by the presence-plus-exactly-once pin over the registry consult's
# dispatch span below.
# the registry consult dispatch span moved to the survey-arms module (the
# maintenance-skill-size-refactor split)
[ "$(grep -oF 'dispatches at most one overdue audit-kind task' "$SA" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "registry consult dispatch span count" "PIN FAIL: registry consult dispatch span count" || fail=1; }
python3 - "$S" "$Z" "$SF" "$SC" <<'EOF' | route_heredoc_stream # r7 F1: propagate the block status; without this the block is fail-open at the exit-code surface 
import sys
# the State file and Step 5 regions moved to their modules (the
# maintenance-skill-size-refactor split); the configuration region stays in
# the router
s, z = open(sys.argv[1]).read(), open(sys.argv[2]).read()
sf, sc = open(sys.argv[3]).read(), open(sys.argv[4]).read()
def region(text, start, end, desc, source=None):
    text = source if source is not None else text
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
# in the state-file module the State file section is followed by the moved
# Step 6 section (a "### " heading), so the end anchor names it
state = region(s, "## State file", "\n### Step 6: state update", "State file", source=sf)
n = state.count("execute|author|audit|retriage")
if n != 2:
    print("PIN FAIL: execute|author|audit|retriage kind literal count %d != 2 in the State file section" % n); sys.exit(1)
# the Step 5 region's dispatch-class-neutral rephrase span
# the scheduling module's Step 5 section runs to end of file (Step 6 moved
# to the state-file module), so the region reads to EOF
step5 = sc.split("### Step 5: scheduling", 1)[1] if "### Step 5: scheduling" in sc else (_ for _ in ()).throw(SystemExit(1))
n = step5.count("or the dispatch decision (for an idle-time dispatch)")
if n != 1:
    print("PIN FAIL: Step 5 rephrase span count %d != 1 in the Step 5 region" % n); sys.exit(1)
# the overlay's audit recipe section heading
n = z.count("## Audit recipe")
if n != 1:
    print("PIN FAIL: ## Audit recipe heading count %d != 1 in zcode.md" % n); sys.exit(1)
EOF
heredoc_settle "${PIPESTATUS[0]}"
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

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
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }
# duty (b) freeze clause presence pin (prompt-log freeze follow-through plan, Task 4):
# freeze-literal convention, the needle is the operative sentence. Re-aimed
# 2026-10-08 (two-mode loop policy plan Task 3): duty (b) now covers both
# rolling logs, and the operative sentence names the PLAN-PROMPTS entry.
pin "duty (b) freeze clause wired" grep -qF 'marks any PLAN-PROMPTS.md entry whose authoring has started' "$DE"
# Removed 2026-10-14, arm remove-beside-provenance: the origins-closure archive
# arm wiring in execute-plan SKILL.md was adapter-era prose deliberately
# removed by the certified landing e0d7d6961; the closure tool itself
# (scripts/check_plan_origins_closed.py) stays live and is witnessed by the
# maintenance templates' own references.
# contract single-sourcing citation shape (contract-single-sourcing plan, Task 3):
# the bounded-evidence constants restatement is gone from the skill (the
# restated-number form frozen ABSENT, wrap-tolerant over the sentence's
# line wrapping; the second sentence keeps its "100-item" behavioral
# content) and the owned-module citation is present exactly once.
if grep -qE "MAX_EVIDENCE_ITEM_BYTES. is 512|4096 UTF-8 byte aggregate|100-criteria count limit" "$EP"; then
  echo "pin fail: execute-plan SKILL.md restates the bounded-evidence constants; the citation single-homes them"
  fail=1
fi
cite_count=$(grep -cF "runtime_capabilities" "$EP" || true)
if [ "$cite_count" -ne 1 ]; then
  echo "pin fail: execute-plan SKILL.md owned-module citation must appear exactly once (found $cite_count)"
  fail=1
fi
pin "origins-block survey warn arm wired in maintenance SKILL.md" grep -qF 'Archived-coverage warn arm' "$SA"
pin "dirt regression merge arm wired in execution blueprint" grep -qF 'dirt_regression_gate.py --base' "$TE"
pin "origins-closure blueprint archive-sentence duty wired" grep -qF 'origins-closure check (`python3' "$TE"
pin "done dirt guard wired" grep -qF 'dirt_regression_gate.py' "$DR"
pin "done review-thread closure gate wired" grep -qF 'review_thread_gate.py --marker' "$D"
pin "receiving-review review-thread marker duty wired" grep -qF 'write a review-thread marker at `docs/tmp/review-threads/<session-slug>.json` before posting any reply' "$RR"
pin "review-plan rule 5 vendored landing clause wired" grep -qF 'vendored-sync backlog item' "$RP"
# dfm r2 F1 successor (the archived gates left these producer steps ungated; the declaration-audit half lives on review-plan)
pin "dfm r2 F1 successor declaration audit producer step" grep -qF 'Declaration audit' "$RP"
# dfm r1 F6 successor (the archived gate's shorter needle was satisfied by the boundary sixth family without any pricing sentence)
pin "dfm r1 F6 successor narrowed contradiction pricing needle" grep -qF "contradicts the plan's content is blocking" "$RP"
pin "AGENTS.md vendored landing mirror clause wired" grep -qF 'land the vendored copy in the same run' "$A"
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

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
pin "pending_landing schema literal" grep -qF '"pending_landing": null' "$SF"
pin "pending_landing field paragraph opener" grep -qF 'is the deferred-landing intent record' "$SF"
pin "record shape landed_path" grep -qF 'landed_path' "$SA"
pin "record shape branch_tip" grep -qF 'branch_tip' "$SA"
pin "record shape attempts" grep -qF '"attempts": 0' "$SF"
pin "carry-forward opener unchanged" grep -qF 'carry forward the values' "$SF"
pin "human-clear landing addition" grep -qF 'deletes the per-run note in the same action' "$SF"
pin "completion-work gate set: gmail-author" grep -qF 'gmail-author' "$DE"
pin "peer-byte guard" grep -qF "no staged path outside the branch's changed paths" "$DE"
pin "labeled stash" grep -qF 'git stash push -m' "$DE"
pin "stash untracked-flag prohibition" grep -qF 'never uses `-u`' "$DE"
pin "stash failure path leaves stash in place" grep -qF 'leaves the stash in place' "$DE"
pin "release on every completion-work exit" grep -qF 'every completion-work exit' "$DE"
pin "index-preserving stash restore" grep -qF 'git stash pop --index' "$DE"
# --- sequential landing discipline blueprint pins (prompt-templates.md) ---
pin "blueprint landed-commit verification" grep -qF "verify the landed commit on the repository's default branch" "$TE"
pin "successor own-landing conjunct" grep -qF 'its own landing is not verified on the default branch' "$TE"
pin "successor outstanding-record conjunct" grep -qF 'an outstanding pending_landing record' "$TE"
pin "execution deferred-landing record lane literal" grep -qF '"lane": "execute"' "$TE"
pin "authoring stranding record lane literal" grep -qF '"lane": "author"' "$TA"
pin "lock-timeout record duty" grep -qF 'the lock-acquire timeout path' "$TA"
pin "authoring record duty span" grep -qF 'before ending, write the pending_landing record' "$TA"
pin "blueprint conflict cleanup" grep -qF 'git reset --merge' "$TE"
pin "record-before-release ordering" grep -qF 'before releasing the lock' "$TE"
pin "successor chain-nothing anchor intact" grep -qF 'Chain nothing, and end, when any of these holds' "$TE"
python3 - "$S" "$SA" "$GU" "$DE" "$QP" "$SC" "$SF" "$FC" "$TA" "$TE" "$TU" <<'PYSEQ' | route_heredoc_stream # r7 F1: propagate the block status; without this the block is fail-open at the exit-code surface 
import sys
# the split corpus: the whole-file floors count over the canonical
# concatenation (router + modules), p stays prompt-templates.md
s = "".join(open(sys.argv[i]).read() for i in range(1, 9))
# the per-kind files carry the blueprint bodies (the split, Task 4)
p = "".join(open(sys.argv[i]).read() for i in range(9, 12))
fail = 0
def check(cond, desc):
    global fail
    if not cond:
        print("PIN FAIL: " + desc); fail = 1
# pending_landing must be named across schema, carry-forward, writer classes,
# Step 1, and Step 3 (whole-file count floor)
n = s.count("pending_landing")
check(n >= 5, f"pending_landing count {n} < 5 across the split corpus")
# r6 F1 fold: the four needles below are quoted verbatim by the Task 2
# Revisions ledger entry, so they are pinned region-scoped to their owning
# regions (Step 5, State file section, Step 3) rather than whole-file
a = s.index("\n### Step 5: scheduling"); b = s.index("\n### Step 6: state update")
check("pre-dispatch landing gate" in s[a:b], "Step 5 region missing: pre-dispatch landing gate")
a = s.index("Each non-turn write is a targeted field edit"); b = s.index("- The `children` array")
check("re-evaluate their precondition" in s[a:b], "State file region missing: re-evaluate their precondition")
a = s.index("\n### Step 3: decision"); b = s.index("\n### Step 4: quota leg")
for needle in ["temporary worktree", "git reset --merge"]:
    check(needle in s[a:b], "Step 3 region missing: " + needle)
# Invariants-region needles (the fleet-rule bullet lives only there); the
# region's end anchor moved with the Revisions ledger (changelog extraction
# plan, Task 1), so the Invariants region now runs to the Integration Points
# heading that follows it in the operative file
a = s.index("## Invariants"); b = s.index("## Integration Points")
inv = s[a:b]
for needle in ["post-review, pre-landed state", "zero outstanding unlanded runs",
               "no surviving repo-matching"]:
    check(needle in inv, "Invariants region missing: " + needle)
# Step 1-region needles (the read-back and reconciliation bullets live only there)
a = s.index("\n### Step 1: survey"); b = s.index("\n### Step 2: guards")
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
a = s.index("\n### Step 3: decision"); b = s.index("\n### Step 4: quota leg")
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
heredoc_settle "${PIPESTATUS[0]}"
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

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
pin "authoring payload re-verification gate" grep -qF 're-verify the target backlog item still sits at the backlog top level and is still plan-uncovered' "$TA"
pin "quota signal token documented" grep -qF 'quota_signal=' "$QP"
pin "in-session marker documented" grep -qF '(in-session)' "$SA"
pin "decision-time probe binding" grep -qF 'the signal is derived at decision time' "$DE"
pin "in-session lane hold branch" grep -qF 'idle-listing attribution inapplicable' "$SF"
pin "quota signal slug vocabulary" grep -qF 'probe-scarce, probe-near-reset' "$QP"
[ "$(grep -oF '{"item": "<backlog item path>", "reason": "<covered|gone>", "date": "<iso date>"}' "$SF" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "covered-stand-down marker schema parity (state-file module) count != 1" "PIN FAIL: covered-stand-down marker schema parity (state-file module) count != 1" || fail=1; }
[ "$(grep -oF '{"item": "<backlog item path>", "reason": "<covered|gone>", "date": "<iso date>"}' "$TA" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "covered-stand-down marker schema parity (authoring template) count != 1" "PIN FAIL: covered-stand-down marker schema parity (authoring template) count != 1" || fail=1; }
python3 - "$DE" <<'EOF' | route_heredoc_stream # r7 F1: propagate the block status; without this the block is fail-open at the exit-code surface 
import sys
# the Step 3 decision region moved to the decisions module (the
# maintenance-skill-size-refactor split)
s = open(sys.argv[1]).read()
if "### Step 3: decision" not in s:
    print("PIN FAIL: carrier-selection rule region anchor missing (Step 3)"); sys.exit(1)
# the decisions module's Step 3 section runs to end of file (Step 4 moved to
# the quota-policy module), so the region reads to EOF
step3 = s.split("\n### Step 3: decision")[1]
if "quota-state-aware carrier-selection rule" not in step3:
    print("PIN FAIL: carrier-selection rule present (the operative D2 sentence is gone from the Step 3 decision region; the Revisions ledger quotes the span, so a whole-file grep cannot guard it)"); sys.exit(1)
EOF
heredoc_settle "${PIPESTATUS[0]}"
# --- P54 park-discharge duty pins (plan 2026-09-24-p54-scheduler-loop-continuity-directives.md Task 2) ---
pin "P54 able-session predicate literal" grep -qF 'able-session predicate' "$SA"
pin "P54 discharge field predicate" grep -qF 'pending_rearm or pending_dispatch' "$SA"
pin "P54 discharge duty anchor" grep -qF 'park-discharge duty' "$SA"
pin "P54 discharge operative phrase" grep -qF 'discharges the parked intents in the same session before ending, guard-bound' "$SA"
# post-split: each per-kind file carries its copy individually (Task 4)
[ "$(cat "$TA" "$TE" "$TU" | grep -cF 'CLOSING PARK DISCHARGE DUTY')" -eq 3 ] || { recorded_red_check "blueprint discharge anchor count != 3" "PIN FAIL: blueprint discharge anchor count != 3" || fail=1; }
[ "$(grep -cF 'DUTY, before ending: read .ai-playbook/scheduler-state.json' "$P")" -eq 0 ] || { recorded_red_check "cwd-relative discharge read reintroduced" "PIN FAIL: cwd-relative discharge read reintroduced" || fail=1; }
# 2026-09-25 parked-dependency visibility Task 6: the new unblock wrapper is
# count-pinned at exactly one opener beside the existing wrapper-count pin
pin "parked-dependency unblock wrapper count" test "$(grep -oF '<prompt for the parked-dependency unblock session>' "$TU" | wc -l | tr -d ' ')" -eq 1
# --- parked-dependency visibility pins (plan 2026-09-25-parked-dependency-visibility.md Task 6) ---
pin "parked_dependencies schema literal" grep -qF '"parked_dependencies": [],' "$SF"
pin "parked_dependencies field paragraph opener" grep -qF 'parked_dependencies is the ordered array of parked-dependency ledger entries' "$SF"
pin "parked_dependencies occurrence floor" test "$(cat "$SF" "$DE" | grep -oF 'parked_dependencies' | wc -l | tr -d ' ')" -ge 5
pin "parked-dependency survey arm anchor" grep -qF 'parked-dependency liveness arm' "$SF"
# the span's satisfying copy lived in the Revisions-ledger entry (a whole-file
# grep over the operative file was satisfied by the ledger copy); re-aimed to
# the extracted changelog beside provenance (changelog extraction plan, Task 1)
pin "parked-dependency survey state vocabulary" grep -qF 'waiting, stale, or actionable' "$CL"
pin "D1 live-entry skip span" grep -qF 'live parked_dependencies entry' "$DE"
pin "parked-dependency carry-forward span" grep -qF 'plus `parked_dependencies` (the boundary-write, unblock-clear, and survey-clear writers above, so the rewrite must carry the field)' "$SF"
# Removed 2026-10-14, arm remove-beside-provenance: the parked-dependency
# ledger entry span in execute-plan SKILL.md was adapter-era prose deliberately
# removed by the certified landing e0d7d6961; the literal survives only in the
# owning completed plan
# docs/history/plans/completed/2026-09-25-parked-dependency-visibility.md.
pin "unblock-template opener span" grep -qF 'parked-dependency unblock dispatch' "$TU"
pin "dependency-branch landing-race discipline span" grep -qF 'actual pre-landing main' "$TE"
pin "Step 5 unblock-dispatch slice sentence" grep -qF "the content of the unblock template's own" "$SC"
pin "SUCCESSOR DISPATCH amended skip clause" grep -qF 'a live `parked_dependencies` entry (any entry not yet cleared by the State file field paragraph' "$TE"
pin "deferred landing-duty dependency-branch record identity" grep -qF 'Dependency-landing record identity' "$TU"
pin "unblock-child progress witness span" grep -qF 'manifest refreshes count as progress for unblock children' "$FC"
pin "lane-hold unblock completion-evidence span" grep -qF 'ledger entry cleared plus the serialized plan present in `execution_queue`' "$GU"
pin "deferred outcome_reason schema note value" grep -qF 'the value `deferred` per the parked-dependency unblock deferral' "$FC"
# --- unblock-landing-worktree-rework pins (plan 2026-10-02-unblock-landing-worktree-rework.md Task 3) ---
# (a) the retired checkout-holding capture literal is frozen absent from the
# whole file (wrap-tolerant; superseded 2026-10-02 by the worktree-complete
# landing shape the unblock landing rework delegated to).
expect_absent_flat "retired unblock pre-landing capture literal must be absent from prompt-templates.md (wrap-tolerant; superseded 2026-10-02 by the unblock landing rework)" 'UNBLOCK_PRE_TIP' "$P"
# --- P54 execution queue and priority pins (plan ... Task 3) ---
pin "P54 execution_queue schema line" grep -qF '"execution_queue": []' "$SF"
pin "P54 execution_priority schema line" grep -qF '"execution_priority": null' "$SF"
pin "P54 park-first anchor in execution blueprint" grep -qF 'Park-first chaining' "$TE"
python3 - "$SF" <<'EOF' | route_heredoc_stream
import sys
# the carry-forward list moved to the state-file module (the
# maintenance-skill-size-refactor split)
s = open(sys.argv[1]).read()
cf = [l for l in s.split("\n") if "carry forward" in l]
if not cf or "execution_queue" not in cf[0] or "execution_priority" not in cf[0]:
    print("PIN FAIL: P54 execution_queue/execution_priority absent from the Step 6 carry-forward list"); sys.exit(1)
EOF
heredoc_settle "${PIPESTATUS[0]}"
# --- P54 dedup guard and execution claims pins (plan ... Task 4) ---
pin "P54 duplicate-user-directed-dispatch tripwire" grep -qF 'duplicate-user-directed-dispatch' "$GU"
pin "P54 user-directed negative-shape payload-opening prefix" grep -qF 'You are an unattended scheduled session in the repository at' "$GU"
pin "P54 execution-claims directory in discovery arm" grep -qF 'execution-claims' "$GU"
pin "P54 blueprint claim duty anchor" grep -qF 'EXECUTION CLAIM' "$TE"
# --- P54 needs-recert pin (plan ... Task 5), region-scoped to the Step 3 decision region ---
python3 - "$DE" <<'EOF' | route_heredoc_stream # the Step 3 region moved to the decisions module (the maintenance-skill-size-refactor split) 
import sys
s = open(sys.argv[1]).read()
if "### Step 3: decision" not in s:
    print("PIN FAIL: P54 Step 3 region anchor missing"); sys.exit(1)
step3 = s.split("\n### Step 3: decision")[1]
if "needs-recert" not in step3:
    print("PIN FAIL: P54 needs-recert literal absent from the D1 region"); sys.exit(1)
EOF
heredoc_settle "${PIPESTATUS[0]}"
# --- P54 needs-recert pin block end marker (plan ... Task 5; comment label corrected 2026-09-24 review r4) ---
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

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
[ "$(grep -oF 'Duplicate-parent migration arm (added 2026-09-23' "$DE" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "migration arm Step 3 anchor count != 1" "PIN FAIL: migration arm Step 3 anchor count != 1" || fail=1; }
[ "$(grep -oF 'the leg is a delete of the old-form record targeted by its listed id' "$DE" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "migration arm delete-leg span count != 1" "PIN FAIL: migration arm delete-leg span count != 1" || fail=1; }
[ "$(grep -oF 'retimes and retitles the old-form record per the cadence rule' "$DE" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "migration arm retitle-leg span count != 1" "PIN FAIL: migration arm retitle-leg span count != 1" || fail=1; }
# ledger-span count re-aimed to the extracted changelog (changelog extraction
# plan, Task 1: the span's home was the Revisions ledger entry)
[ "$(grep -oF '2026-09-23: the duplicate-parent tripwire gained the migration arm' "$CL" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "migration arm ledger span count != 1" "PIN FAIL: migration arm ledger span count != 1" || fail=1; }
[ "$(grep -oF 'the migration arm (SKILL.md Step 3)' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "migration arm zcode.md pointer count != 1" "PIN FAIL: migration arm zcode.md pointer count != 1" || fail=1; }
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

# --- per-execution worktree field and per-run read pins (plan
# 2026-09-24-p57-per-execution-worktree-isolation.md, Task 1) ---
# Companion pins for the additive children[] `worktree` field and the per-run
# read sites. Each pin below is a dedicated fixed-string grep that fails when
# its span is deleted (spans S1, S2, S3, S4, S5, S21 of the plan's Validation
# Commands, against SKILL.md). The schema-block half (the parsed children[0]
# carries a "worktree" key with value null and schema stays 4) lives in the
# first SKILL.md python block beside the existing children-entry fields pin,
# mirroring that block's block-parse mechanism.
pin "P57 S1 worktree field paragraph" grep -qF 'once its blueprint-created per-execution worktree exists' "$SF"
pin "P57 S2 progress-mark per-run clause" grep -qF "resolved inside the entry's recorded \`worktree\` when that additive field is set" "$FC"
pin "P57 S3 ingestion per-run clause" grep -qF 'the same repository-relative manifest path inside the recorded worktree' "$FC"
pin "P57 S4 fast re-dispatch per-run clause" grep -qF 'the same per-run resolution the rate-limited ingestion bullet applies' "$FC"
pin "P57 S5 sanctioned-writer own-record clause" grep -qF 'own-record per-run worktree recording' "$SF"
pin "P57 S21 ref-based archival read" grep -qF 'the archival arm is read ref-based' "$FC"
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

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
pin "P57 S7 fleet-cap execution-isolation sentence" grep -qF 'EXECUTION ISOLATION (landed 2026-09-24, P57' "$GU"
pin "P57 S8 Invariants worktree-isolated fleet-member clause" grep -qF 'execution children run in per-execution ad-hoc worktrees per the Worktree-first standard' "$GU"
pin "P57 S9 stance rework-executed lead-in (region-scoped)" bash -c "awk '/^### Execution-lane concurrency stance/{f=1; next} /^## Revisions/{f=0} f' \"$S\" | grep -qF 'REWORK EXECUTED (landed 2026-09-24, P57'"
pin "P57 S9 stance overlap-shapes tail (region-scoped)" bash -c "awk '/^### Execution-lane concurrency stance/{f=1; next} /^## Revisions/{f=0} f' \"$S\" | grep -qF 'up to four concurrent children across mixed kinds with executions worktree-isolated'"
expect_absent "retired INTERIM EXECUTION CONSTRAINT heading must be absent from SKILL.md (the ledger's lowercase historical wording must not satisfy or break this)" 'INTERIM EXECUTION CONSTRAINT' "$S"
expect_absent "superseded Until-P57 sanctioned-overlap-shapes sentence must be absent from SKILL.md" 'Until P57, the sanctioned overlap shapes' "$S"
[ "$(grep -cF '2026-09-24 (P57 per-execution worktree isolation' "$CL")" -eq 1 ] || { recorded_red_check "P57 ledger date string count != 1 (re-aimed to the extracted changelog, changelog extraction plan Task 1)" "PIN FAIL: P57 ledger date string count != 1 (re-aimed to the extracted changelog, changelog extraction plan Task 1)" || fail=1; }
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

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
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

# --- execution blueprint per-execution worktree pins (plan
# 2026-09-24-p57-per-execution-worktree-isolation.md, Task 4; dispositions
# re-keyed by the worktree-first standard consolidation, plan
# 2026-09-28-worktree-first-standard-only-mode.md Task 4) ---
# The 2026-09-28 consolidation replaced the blueprint's per-execution
# worktree paragraphs with references to the Worktree-first standard section
# in the execute-plan skill; the blueprint's per-run pre-work gate paragraph
# was rewritten to post-transfer-in scope in that same consolidation, not
# retired with them (S15 below is re-keyed on the rewritten gate sentence),
# retiring the P57 payload spans the replacement retired: S13
# (the execution create-literal count) and the
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
# Freeze (2026-10-02, worktree-complete landing lifecycle): the authoring
# self-landing's pathspec arm is retired (staging in the primary checkout is a
# landing-gate violation), so its explicit staging command is frozen absent
# whole-file; this origin supersedes the body-scoped need needle the tuple
# above used to carry, per the suite's freeze-literal convention.
expect_absent_flat "retired authoring pathspec-arm staging command must be absent from prompt-templates.md (wrap-tolerant; superseded 2026-10-02 by the worktree-complete landing lifecycle)" 'git add -- <paths>' "$P"
pin "per-run pre-work gate span (re-keyed 2026-09-28; was P57 S15)" grep -qF "the run's own per-worktree done lock is free" "$TE"
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

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
# continues to pass unchanged.
# Restoration note (origin 2026-09-28-s15-rekey-narrowed-done-lock-gate-pin):
# the 2026-09-28 re-key (plan 2026-09-28-worktree-first-standard-only-mode.md
# Task 4, archived under docs/history/plans/completed/) narrowed the gate pin
# to the gate's done-lock conjunct only, leaving the done-lock keying basis
# between that conjunct span and the S20 scoping span unpinned; the keying
# pin below restores that coverage. A wording change to the keying sentence
# must reconcile pin and text in the same edit and record the superseding
# origin per the suite's freeze-literal convention. The superseded shared-checkout Phase 0 clause is
# frozen absent with the wrap-tolerant flattened form (expect_absent_flat
# above): the clause was line-wrapped in the file, so the plain line-oriented
# expect_absent is a no-op against the wrapped bytes and must not be used here.
# Re-key (2026-10-02, worktree-complete landing lifecycle): the dual-arm
# landing machinery was retired for the single Worktree arm, so the S16
# primary-arm prefixed count pin and the S17 temp-worktree create-command
# presence pin are superseded by wrap-tolerant freeze-absent pins (the retired
# commands must not return); this origin supersedes per the suite's
# freeze-literal convention.
# Re-point (2026-10-11, plan
# docs/history/plans/2026-10-11-execute-plan-boundary-reliability.md Task 2):
# the spelled Worktree arm retired for the land_squash.sh land-worktree helper
# invocation, so the S16 bare count pin and the S18 compare-and-swap presence
# pin consciously retire with their literals into freeze-absent form (the
# 2026-10-02 keep-rationale, the spelled arm carrying the literals, lapses).
expect_absent_flat "retired primary-arm prefixed squash command must be absent from prompt-templates.md (wrap-tolerant; superseded 2026-10-02 by the worktree-complete landing lifecycle)" 'git -C <default-checkout> merge --squash <branch>' "$P"
expect_absent_flat "retired worktree-arm bare squash command must be absent from the execution template (wrap-tolerant; superseded 2026-10-11 by the boundary-reliability helper re-point)" 'git merge --squash <branch>' "$TE"
expect_absent_flat "retired temp-worktree arm create command must be absent from prompt-templates.md (wrap-tolerant; superseded 2026-10-02 by the worktree-complete landing lifecycle)" 'git worktree add --detach <temp-path> refs/heads/<default>' "$P"
expect_absent_flat "retired worktree-arm compare-and-swap command must be absent from the execution template (wrap-tolerant; superseded 2026-10-11 by the boundary-reliability helper re-point)" 'git update-ref refs/heads/<default> <new-tip> <old-tip>' "$TE"
pin "P57 S19 archive per-run worktree commit span" grep -qF 'the archive commit is a per-run worktree commit' "$TE"
pin "P57 S20 done-lock per-run scoping span" grep -qF "so the run's done lock is its own" "$TE"
[ "$(grep -oF 'locks are keyed per-worktree on --show-toplevel' "$TE" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "done-lock keying basis (restores pre-consolidation S15 scope; origin 2026-09-28-s15-rekey-narrowed-done-lock-gate-pin)" "PIN FAIL: done-lock keying basis (restores pre-consolidation S15 scope; origin 2026-09-28-s15-rekey-narrowed-done-lock-gate-pin)" || fail=1; }
# Landing-tail parenthetical exactly-once pin (origin
# 2026-09-28-landing-tail-parenthetical-precedence-and-pin): the landing tail's
# parenthetical carries the checkout-flow carve-out beside the
# default-branch-integration equality clause, and the equality fragment is
# pinned exactly-once (wrap-tolerant, the S16 normalized-count idiom), scoped
# to "$P", so the reconciling clause cannot silently drift or invert with the
# suite green.
[ "$(grep -oF 'equals the resolved base in a default-branch-integration project' "$TE" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "landing-tail parenthetical default-branch-integration equality clause count != 1 (origin 2026-09-28-landing-tail-parenthetical-precedence-and-pin)" "PIN FAIL: landing-tail parenthetical default-branch-integration equality clause count != 1 (origin 2026-09-28-landing-tail-parenthetical-precedence-and-pin)" || fail=1; }
expect_absent_flat "superseded shared-checkout Phase 0 clause must be absent from prompt-templates.md (wrap-tolerant)" 'Phase 0 dedicated branch from main' "$P"
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

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
pin "P57 r1 G1a fleet-member sequencing sentence" grep -qF 'Executions are fleet members and may overlap, each in its own per-execution worktree' "$GU"
# the span's only home was the Revisions ledger entry (the operative sentence is retired and frozen absent); re-aimed to the extracted changelog (changelog extraction plan Task 1)
pin "P57 r1 D2 carrier sequencing-superseded parenthetical" grep -qF "sequencing superseded 2026-09-24 by P57's per-execution worktree isolation" "$DE"
expect_absent "retired strictly-sequential execution sentence must be absent from SKILL.md (the ledger's historical wording must not satisfy or break this)" 'Executions are strictly sequential (never two in flight)' "$S"
expect_absent "retired strictly-sequential clocked-child stance parenthetical must be absent from SKILL.md" 'strictly sequential clocked-child stance is unchanged' "$S"
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }


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
          recorded_red_check "live-vs-archive basename twin: / also archived at //" "PIN FAIL: live-vs-archive basename twin: $live_root/$base also archived at $live_root/$archive_dir/$base" || rc=1
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
# Outcome-contract arm (scripts/OUTCOME_CONTRACT.md): a refusal run ends
# with exactly one final `OUTCOME: fail` line emitted by the same helper
# every exit checkpoint funnels through; modeled on this section's fixture
# seam (never a whole-suite re-invocation, per the declared per-section
# scoping in the header comment).
MODELED_REFUSAL="$( { check_live_vs_archive_duplicates "$DUPLICATE_FIXTURE" 2>&1 || emit_outcome fail; } )"
rm -rf "$DUPLICATE_FIXTURE"
if [ "$DUPLICATE_RC" -eq 0 ]; then
  recorded_red_check "live-vs-archive selftest: synthetic twin pair did not fail (rc 0)" "PIN FAIL: live-vs-archive selftest: synthetic twin pair did not fail (rc 0)" || fail=1
elif ! printf '%s' "$DUPLICATE_OUT" | grep -q "2026-01-01-fake-twin.md"; then
  recorded_red_check "live-vs-archive selftest: refusal output does not name the fixture pair" "PIN FAIL: live-vs-archive selftest: refusal output does not name the fixture pair" || fail=1
elif [ "$(printf '%s\n' "$MODELED_REFUSAL" | tail -n 1)" != "OUTCOME: fail" ] || \
     [ "$(printf '%s\n' "$MODELED_REFUSAL" | grep -c '^OUTCOME:' | tr -d ' ')" != "1" ]; then
  recorded_red_check "live-vs-archive selftest: refusal run does not end with exactly one final OUTCOME: fail line" "PIN FAIL: live-vs-archive selftest: refusal run does not end with exactly one final OUTCOME: fail line" || fail=1
fi

[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

# --- quota display staleness and refresh-cadence pins (plan
# 2026-09-25-quota-display-refresh-cadence.md) ---
[ "$(grep -oF 'Sidebar display staleness and operator refresh cadence' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "quota sidebar-staleness bullet count != 1" "PIN FAIL: quota sidebar-staleness bullet count != 1" || fail=1; }
[ "$(grep -oF 'Quota display caveat' "$SA" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "quota display caveat bullet count != 1 (re-pointed to the survey-arms module, the size-refactor split)" "PIN FAIL: quota display caveat bullet count != 1 (re-pointed to the survey-arms module, the size-refactor split)" || fail=1; }
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

# --- execution queue-drain turn-end and taxonomy-parity pins (plan
# 2026-09-25-execution-lane-queue-drain-continuation.md) ---
[ "$(grep -oF 'a request for the user to confirm starting the next plan is never a sanctioned turn end' "$D" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "queue-drain turn-end bullet count != 1" "PIN FAIL: queue-drain turn-end bullet count != 1" || fail=1; }
[ "$(grep -oF 'a guard fire (a quota pause or near-reset with the Budget gate' "$E" | wc -l | tr -d ' ')" -eq 1 ] && [ "$(grep -oF 'a guard fire (a quota pause or near-reset with the Budget gate' "$D" | wc -l | tr -d ' ')" -eq 1 ] && [ "$(grep -oF 'a landing-gate hold reported by `scripts/done-lock.sh` merge-status, a lane hold from the scheduler guards, provider rate pressure with its structured rate-limited end) or an empty queue (no digest-intact open plan remains); a user interrupt or explicit abort is always sanctioned as well' "$E" | wc -l | tr -d ' ')" -eq 1 ] && [ "$(grep -oF 'a landing-gate hold reported by `scripts/done-lock.sh` merge-status, a lane hold from the scheduler guards, provider rate pressure with its structured rate-limited end) or an empty queue (no digest-intact open plan remains); a user interrupt or explicit abort is always sanctioned as well' "$D" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "queue-drain taxonomy parity span count != 1" "PIN FAIL: queue-drain taxonomy parity span count != 1" || fail=1; }
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

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
pin "Execution-lane carrier-selection ordering present" grep -qF 'Execution-lane carrier-selection ordering' "$SA"
pin "ordering sequence literal present" grep -qF 'clocked, then idle, then in-session, then park-with-carrier' "$DE"
pin "ordering sequence exactly-once count" test "$(grep -oF 'clocked, then idle, then in-session, then park-with-carrier' "$DE" | wc -l | tr -d ' ')" -eq 1
pin "in-session execution dispatch leg present" grep -qF 'in-session execution dispatch' "$DE"
pin "Execution-lane fallback legs overlay bullet present" grep -qF 'Execution-lane fallback legs' "$Z"
pin "park launchd resume-carrier pairing present" grep -qF 'pairs the park with the launchd resume carrier' "$Z"
expect_absent "retired execution-lane never-routed-in-session wording must be absent from SKILL.md" 'the execution lane is never routed in-session' "$S"
expect_absent "retired overlay never-routes-in-session wording must be absent from zcode.md" 'The execution lane never routes in-session' "$Z"
expect_absent "retired no-clock execution dispatch wording must be absent from SKILL.md" 'never dispatched through a primitive without a clock' "$S"
expect_absent "retired clocked-only trap-sentence wording must be absent from zcode.md" 'stays clocked-only' "$Z"
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

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
pin "execution blueprint task-boundary checkpoint paragraph anchor" test "$(grep -oF 'TASK-BOUNDARY CHECKPOINT' "$TE" | wc -l | tr -d ' ')" -eq 1
pin "densified execution-claim refresh record exactly-once" test "$(grep -oF 'at every task completion inside the implementation loop' "$TE" | wc -l | tr -d ' ')" -eq 1
# 2026-09-28 continuation policy plan: mirrored duty rename in execute-plan
pin "execute-plan task-boundary checkpoint duty policy anchor" grep -qF 'Task-boundary checkpoint duty' "$E"
pin "queue-drain fold names the asserted-unchanged guard family" grep -qF 'lane guard and the P54 fleet cap' "$E"
pin "pins header existence loop covers E" grep -qE '^for f in "\$S" "\$Z" "\$P" "\$D" "\$E"; do$' "${BASH_SOURCE[0]}"
expect_absent "retired one-execution-child guard wording must be absent from the execute-plan skill" 'one-execution-child guard' "$E"
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

# --- WIP auto-checkpoint pins (plan 2026-10-10-wip-auto-checkpoint.md, Task 1) ---
# Companion pins for the D-10 checkpoint mechanism: the marker convention and
# pause-signal duty in the execute-plan skill (the paragraph added beside the
# task-boundary checkpoint duty), the resume-restart sentence beside the
# restored-worktree arm, and the subagent-prompts batch mirror. Each is a
# presence pin over its distinctive fragment, added beside the provenance
# named in the plan's Task 1 files list.
EPSP="$repo/agents/skills/execute-plan/subagent-prompts.md"
pin "execute-plan wip checkpoint marker convention" grep -qF 'checkpoint commit-marker convention (a `wip:` subject prefix on the worktree branch)' "$E"
pin "execute-plan wip checkpoint pause signals" grep -qF 'at every task boundary and every pause signal (quota pause, budget pause, stand-down, carrier expiry, input stop, lane hold; input stop being the stop-for-operator class of the Only-stop-between-tasks list)' "$E"
pin "execute-plan wip no-new-ledger supersession" grep -qF 'no new ledger lands (the prompt arm' "$E"
# Re-aimed 2026-10-19 (plan docs/history/plans/2026-10-14-skill-monolith-module-extraction.md Task 2): the needle's span moved verbatim to agents/skills/execute-plan/worktree-first.md.
pin "execute-plan resume restart from last checkpoint" grep -qF 'restarts from the last checkpoint' "$repo/agents/skills/execute-plan/worktree-first.md"
# Removed 2026-10-14, arm remove-beside-provenance: the subagent-prompts wip
# checkpoint batch mirror was adapter-era fan-out prose deliberately removed
# by the certified landing e0d7d6961 (the sequential-only adapter-removal
# plan's Task 2); the orchestrating skill's own wip convention rows above stay
# pinned.

# --- WIP auto-checkpoint pins, Task 2 (plan 2026-10-10-wip-auto-checkpoint.md) ---
# The removal preflight's two skill homes and its script home, plus the
# authoring checkpoint duty in the plans skill; presence pins beside the
# provenance the plan's Task 2 files list names.
PLN="$repo/agents/skills/plans/SKILL.md"
WCM="$repo/scripts/worktree_closeout_migrate.py"
pin "plans final handoff owned-files-clean preflight" grep -qF 'owned-files-clean removal preflight' "$PLN"
pin "plans authoring checkpoint duty marker" grep -qF 'commits the plan file on its authoring branch under the `wip:` checkpoint marker' "$PLN"
# Re-aimed 2026-10-19 (plan docs/history/plans/2026-10-14-skill-monolith-module-extraction.md Task 2): the needle's span moved verbatim to agents/skills/execute-plan/worktree-first.md.
pin "execute-plan transfer-out owned-files-clean preflight" grep -qF 'owned-files-clean preflight' "$repo/agents/skills/execute-plan/worktree-first.md"
pin "migrate script owned-files-clean subcommand" grep -qF 'def cmd_owned_files_clean' "$WCM"

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
# ADDED 2026-10-03 (recurring-task-registry plan Task 8): presence pins for
# the registry migration's load-bearing literals. The recognition literal is
# count-gated at exactly 2 in SKILL.md (the consult bullet plus the Step 5
# registry-task dispatch slice) and present once in the overlay marker
# clause; each of the five task files stores its own recognition-line tail
# (deliberate insurance, so a body run verbatim by a non-registry session
# still announces its lane; the overlay marker matches containment, so the
# assembler prefix plus the stored tail is harmless duplication).
# the two operative copies moved with the split (survey arm + scheduling step)
[ "$(cat "$SA" "$SC" | grep -oF 'recurring task <id> lane' | wc -l | tr -d ' ')" -eq 2 ] || { recorded_red_check "recognition literal count across the split corpus" "PIN FAIL: recognition literal count across the split corpus" || fail=1; }
pin "recognition literal in overlay" grep -qF 'recurring task <id> lane' "$Z"
# RE-KEYED 2026-10-04 (superseding origin: the interim unblock commit
# 8d0066eb renamed the retriage task file deferred-retriage.md -> retriage.md
# with the TOML id unchanged; the pins loop is a live filename consumer the
# interim unblock's consumer census missed, witnessed by the r1 review of
# docs/history/plans/2026-10-04-docs-branch-sync-fail-loud.md): explicit
# filename/literal pairs replace the stem-derived loop, because the stored
# recognition tail carries the TOML id, not the filename stem.
pin "recognition line in friction-audit task file" grep -qF "recurring task friction-audit lane" "docs/maintenance/recurring-tasks/friction-audit.md"
pin "recognition line in the retriage task file" grep -qF "recurring task deferred-retriage lane" "docs/maintenance/recurring-tasks/retriage.md"
pin "recognition line in weekly-measurement-rider task file" grep -qF "recurring task weekly-measurement-rider lane" "docs/maintenance/recurring-tasks/weekly-measurement-rider.md"
pin "recognition line in weekly-skill-review task file" grep -qF "recurring task weekly-skill-review lane" "docs/maintenance/recurring-tasks/weekly-skill-review.md"
# ADDED 2026-10-08 (memory-index-consolidation plan Task 1): the fifth
# recognition-line pin joins the sibling block for the newly registered
# memory-index-audit task file, same deliberate-insurance rationale.
pin "recognition line in memory-index-audit task file" grep -qF "recurring task memory-index-audit lane" "docs/maintenance/recurring-tasks/memory-index-audit.md"
# RE-KEYED 2026-10-03 (recurring-task-registry plan Task 8): the consult
# bullet became the registry pointer stub; the pin rides the stub's new
# opening span.
pin "deferred-corpus re-triage consult stub present" grep -qF 'Deferred-corpus re-triage consult (pointer stub' "$SA"
pin "deferred-corpus re-triage consult bullet exactly-once" test "$(grep -oF 'Deferred-corpus re-triage consult' "$SA" | wc -l | tr -d ' ')" -eq 1
pin "retriage-lane-due reason literal present" grep -qF 'retriage-lane-due' "$DE"
pin "retriage-lane-due reason literal exactly-once" test "$(grep -oF 'retriage-lane-due' "$DE" | wc -l | tr -d ' ')" -eq 1
pin "zcode.md re-triage child recognition literal" grep -qF 'deferred re-triage lane' "$Z"
# RE-AIMED 2026-10-08 (superseding origin: the two-mode loop policy plan
# Task 4 widened the overlay's fleet-member enumeration with the ad-hoc kind,
# fleet membership following the execution lane a child occupies; the pin
# had keyed on the re-triage-kind literal since the origin-class provenance
# plan's Task 4)
pin "zcode.md fleet-cap enumeration widened to the ad-hoc kind" grep -qF 'authoring, audit, re-triage, ad-hoc, and execution children are fleet members' "$Z"
pin "SKILL.md Step 2 fleet-cap enumeration widened to the re-triage kind" grep -qF 'like the authoring, audit, and re-triage kinds' "$GU"
pin "prompt-templates retriage pointer stub present" grep -qF 'deferred re-triage lane' "$P"
# 2026-10-03 amnesia incident record (a deferred row carried two conflicting
# recorded adjudications, owner shown neither), plan
# docs/history/plans/2026-10-03-retriage-lane-duties.md, Task 4: the one new
# presence pin guards the read-before-adjudicate precedence span, its
# companion holds it exactly-once.
pin "retriage adjudication precedence" grep -qF 'records agreement or the distinguishing evidence for the divergence (read-before-adjudicate precedence)' "$SA"
pin "retriage adjudication precedence exactly-once" test "$(grep -oF 'records agreement or the distinguishing evidence for the divergence (read-before-adjudicate precedence)' "$SA" | wc -l | tr -d ' ')" -eq 1
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

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
pin "G1a target-distinctness rule home sentence" grep -qF 'does not hold the lane when the targets are distinct' "$GU"
pin "G1a target-distinctness home sentence exactly-once" test "$(grep -oF 'does not hold the lane when the targets are distinct' "$GU" | wc -l | tr -d ' ')" -eq 1
pin "G1a arms target-distinctness carve-out" grep -qF "releases when the recorded or listed child's target is distinct from the candidate target and the standing-directive sanction exists" "$GU"
pin "G1a audit-child exclusivity span preserved" grep -qF 'an audit child never runs alongside an authoring child or another audit child' "$GU"
pin "G1a re-triage-child exclusivity span preserved" grep -qF 'never runs alongside an authoring child, another re-triage child, or an audit child' "$GU"
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

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
pin "completion-stranding literal present" grep -qF 'turn_error: completion-stranded' "$SF"
pin "completion-stranding literal exactly-once" test "$(grep -oF 'completion-stranded' "$SF" | wc -l | tr -d ' ')" -eq 1
pin "stranding reset-window carrier explanation span" grep -qF "a reset-window carrier armed by the recipe's cadence rule for a later quota window counts as well" "$SF"
pin "stranding quota-pause suppression span" grep -qF 'suppresses the trip while such a reset-window carrier is armed' "$SF"
pin "reduced-toolset terminal rung present" grep -qF 'Reduced-toolset terminal' "$Z"
pin "reduced-toolset rung listing-only predicate" grep -qF 'a session whose automation toolset is the listing primitive only parks the decided action with its payload copy' "$Z"
pin "reduced-toolset rung names the step 0 recovery path" grep -qF 'the SKILL.md Step 0 discharge precedence' "$Z"
pin "ladder last-resort rung renumbered intact" grep -qF '5. Last resort:' "$Z"
# --- standing-directive loop continuation contract pins (plan 2026-09-30-maintenance-loop-interruption-resume-and-cycle-harvest.md Task 5) ---
pin "interruption-resume rule bullet present" grep -qF 'Interruption-resume rule (added 2026-09-30' "$DE"
pin "resumed-standing-directive token present" grep -qF 'resumed-standing-directive' "$DE"
pin "per-cycle harvest duty bullet present" grep -qF 'Per-cycle harvest duty (added 2026-09-30' "$DE"
pin "cycles_completed key present" grep -qF 'cycles_completed' "$SF"
# re-aimed by the two-mode loop policy plan Task 2: the pinned dual-default
# mapping span lived in the retired loop_mode field paragraph; the semantic
# now homes in the Mode binding paragraph (Loop modes section), so the pin
# re-keys on that paragraph's literal. Re-aimed again 2026-10-15 (plan
# 2026-10-15-post-landing-origin-ancestry-diagnostic Task 4): the fa22ac133
# rewording replaced that sentence with the current carrier span, the
# semantics unchanged (a run no keyword or manual ruling classifies still
# defaults to dual), so the pin re-keys on the new span
pin "dual-default mapping span present" grep -qF 'When no keyword or manual ruling classifies the run, default to dual' "$S"
pin "scheduler-turn write-mode clause present" grep -qF 'the resumed-session `decision_reason` targeted edit and the harvest-deferral `decision_reason` record' "$SF"
pin "zcode readiness mirror present" grep -qF 'cycles_completed' "$Z"

# --- user-directed payload re-arm duties pins (plan 2026-09-30-user-directed-maintenance-payload-rearm-duties.md Task 4) ---
pin "user-directed payload duties bullet in the skill" grep -qF 'User-directed maintenance payload duties' "$S"
pin "narrowed disclaimer in the overlay" grep -qF 'no blueprint child re-arm duty' "$Z"

# --- prompt-log origin checker pin (plan 2026-10-01-prompt-log-prune-check.md) ---
# The registry's prune clause gains its mechanical home: the checker exits 1 on
# any PLAN-PROMPTS.md entry whose every origin is served, so the next all-served
# drift is a suite failure instead of an operator question. Deliberately placed
# BEFORE the failure gate below: the script has no set -e and pin only sets
# fail=1, so a pin added after the gate would print PIN FAIL yet the sweep would
# still exit 0 and the wedge would survive every landing.
pin "prompt log has no all-served (stale) entry" python3 "$repo/scripts/check_prompt_log_origins.py"

# --- rearm-on-touch recognition mirror pins (2026-10-11: the validator's mirrored title kept the superseded cadence parenthetical the recipe deleted, so a listing-provided check booked a false parent_absent_since against the correctly titled armed parent) ---
pin "rearm-on-touch recognition title mirror matches the recipe literal" grep -qF 'RECOGNITION_TITLE = "Maintenance scheduler turn"' "$repo/scripts/rearm_on_touch.py"
expect_absent "rearm-on-touch must not carry the superseded cadence-pinned title literal" 'Maintenance scheduler turn (every 2 hours)' "$repo/scripts/rearm_on_touch.py"


# --- user-directed override predicate pins (plan 2026-09-30-user-directed-override-for-interactive-guard-standdowns.md Task 4) ---
pin "override predicate sentence present in the skill" grep -qF 'The override predicate is user presence, never confidence.' "$GU"
pin "override predicate sentence present in the overlay" grep -qF 'The override predicate is user presence, never confidence.' "$Z"
pin "override integrity exclusion present in the skill" grep -qF 'Integrity guards are never overridable' "$GU"

pin "dirty-primary classification arm present" grep -qF 'Dirty-primary classification arm' "$SA"
pin "revert-set classifier wired in the survey" grep -qF 'revert_set_classifier.py classify --repo' "$SA"

# Re-aimed 2026-10-19 (plan docs/history/plans/2026-10-14-skill-monolith-module-extraction.md Task 2): the needle's span moved verbatim to agents/skills/execute-plan/worktree-first.md.
pin "squash tree-equality invariant present" grep -qF 'tree equality between the squashed branch tip and the produced squash commit' "$repo/agents/skills/execute-plan/worktree-first.md"
# Re-pointed/retired 2026-10-11 (plan
# docs/history/plans/2026-10-11-execute-plan-boundary-reliability.md Task 2):
# the spelled Worktree arm retired for the land_squash.sh land-worktree helper
# invocation, so the arm's tree-equality command pin consciously retires into
# freeze-absent form; the execute-plan invariant pin above is preserved policy
# text (its needle lives in the step-4 paragraph's retained sentence).
expect_absent_flat "retired worktree-arm tree-equality command must be absent from the execution template (wrap-tolerant; superseded 2026-10-11 by the boundary-reliability helper re-point)" 'git diff --quiet <branch> <new-tip>' "$TE"

# Re-aimed 2026-10-19 (plan docs/history/plans/2026-10-14-skill-monolith-module-extraction.md Task 2): the needle's span moved verbatim to agents/skills/execute-plan/worktree-first.md.
pin "check-landing base-freshness arm wired in execute-plan" grep -qF 'check-landing --source-branch <run-branch> --target-ref <base-branch>' "$repo/agents/skills/execute-plan/worktree-first.md"
pin "check-landing mode present in the guard" grep -qF 'def cmd_check_landing' "$repo/scripts/reverse_squash_guard.py"

# --- claim-fence warning-posture pins (plan
# docs/history/plans/2026-10-11-landing-deleted-unclaimed-execution-ready-plan.md
# Tasks 1 and 2; the pins suite's first claim-fence section) ---
# Presence needles for the unclaimed-deletion warning leg and the
# rejected-state sanction in the guard's check-claim-fence mode, plus the
# landing-boundary naming leg in check-landing's stale-base branch
# (Task 2). The warning leg is warning-only at this landing (promotion to
# a refusal is the registry-governed flip), so these pin the warning and
# sanction literals, never the refusal grammar.
pin "claim-fence warning literal in the guard" grep -qF 'claim-fence-warning:' "$repo/scripts/reverse_squash_guard.py"
pin "claim-fence rejected-state sanction literal in the guard" grep -qF '(same-commit rejected-state move at ' "$repo/scripts/reverse_squash_guard.py"
pin "claim-fence landing-boundary literal in the guard" grep -qF 'absent protected plan at the landing boundary' "$repo/scripts/reverse_squash_guard.py"

# --- landing-tail wiring pins (plan 2026-10-02-revert-set-clobber-and-reviews-home.md Task 2) ---
pin "check-landed mode present in the guard" grep -qF 'def cmd_check_landed' "$repo/scripts/reverse_squash_guard.py"
# Re-aimed 2026-10-19 (plan docs/history/plans/2026-10-14-skill-monolith-module-extraction.md Task 2): the needle's span moved verbatim to agents/skills/execute-plan/worktree-first.md.
pin "post-landing sweep wired in execute-plan closeout" grep -qF 'check-landed --rev <squash-commit>' "$repo/agents/skills/execute-plan/worktree-first.md"
# Re-aimed 2026-10-14, arm re-aim beside provenance: the delegated-sweep
# pointer in template-execution.md wrapped across a line break (the original
# single-line literal can no longer match any line), so the pin follows the
# carrier through its unique delegation-clause fragment; the pointed-to
# Worktree-first sweep implementation in execute-plan SKILL.md is witnessed by
# the row above (the carrier-pointer phrase itself recurs three times in the
# template, so a whole-fragment count cannot be exactly-once).
[ "$(grep -oF 'post-landing sweep implementation in the' "$TE" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "post-landing sweep delegated in the blueprint (delegation clause fragment) count != 1" "PIN FAIL: post-landing sweep delegated in the blueprint (delegation clause fragment) count != 1" || fail=1; }
expect_absent_flat "retired worktree-arm check-landing payload must be absent from the execution template (wrap-tolerant; superseded 2026-10-11 by the boundary-reliability helper re-point)" 'check-landing --source-branch <branch> --target-ref <default>' "$TE"
pin "severed-ancestry lane egress fence" grep -qF 'check-diff --against <fork-point> --repo <run-worktree>' "$TE"

# --- reviews-home egress refusal class pins (plan 2026-10-02-revert-set-clobber-and-reviews-home.md Task 3) ---
pin "reviews-home egress class present in the guard" grep -qF 'reviews-home egress' "$repo/scripts/reverse_squash_guard.py"
pin "reviews-home class named in the done arm" grep -qF 'reviews-home egress addition under the deny set' "$D"
pin "reviews-home findings never ackable in the done arm" grep -qF 'archive-egress and reviews-home findings still refuse and are never ackable' "$D"
pin "reviews-home prefix set present in the guard" grep -qF 'REVIEWS_HOME_PREFIXES = (".ai-playbook/reviews/",)' "$repo/scripts/reverse_squash_guard.py"

# --- runtime deployment manifest pins (plan 2026-10-02-revert-set-clobber-and-reviews-home.md Task 4) ---
pin "guard entry in the runtime manifest" grep -qFx 'reverse_squash_guard.py' "$repo/scripts/runtime-scripts.list"
pin "guard selftest entry in the runtime manifest" grep -qFx 'test_reverse_squash_guard.py' "$repo/scripts/runtime-scripts.list"
# manifest-membership pin (plan docs/history/plans/2026-10-07-execution-claim-write-enforcement.md
# Task 3; the reverse-squash-guard precedent above pins the guard's manifest
# entry the same way)
pin "execution-claim gateway entry in the runtime manifest" grep -qFx 'execution_claim.sh' "$repo/scripts/runtime-scripts.list"

# --- single-commit-per-lane-event tail pins (plan 2026-10-03-single-commit-per-lane-event.md Task 7) ---
pin "plans landing tail owns the rider-commit flip ordering" grep -qF 'before the landing critical section' "$repo/agents/skills/plans/SKILL.md"
pin "overlay payload orders the flip and prune before the critical section" grep -qF 'run before the landing critical section and their bytes land as rider commits on the authoring branch' "$TA"
# Re-aimed 2026-10-19 (plan docs/history/plans/2026-10-14-skill-monolith-module-extraction.md Task 2): the needle's span moved verbatim to agents/skills/execute-plan/worktree-first.md.
pin "execute-plan final-merge pins the rider-commit duty" grep -qF 'land as rider commits on the landing branch before the critical section' "$repo/agents/skills/execute-plan/worktree-first.md"
# plans-egress trigger companion pins (plan docs/history/plans/2026-10-06-plans-egress-coverage.md Task 2)
# Re-aimed 2026-10-19 (plan docs/history/plans/2026-10-14-skill-monolith-module-extraction.md Task 2): the needle's span moved verbatim to agents/skills/execute-plan/worktree-first.md.
pin "plans-egress any-depth trigger" grep -qF 'at any depth under the root outside' "$repo/agents/skills/execute-plan/worktree-first.md"
pin "plans-egress sideways trigger" grep -qF 'sideways out of the source plans root entirely' "$repo/agents/skills/execute-plan/worktree-first.md"
pin "plans-egress deletion depth trigger" grep -qF 'deletes them from a plans root at any depth outside' "$repo/agents/skills/execute-plan/worktree-first.md"
pin "digest-free witness rule in doc-hierarchy" grep -qF 'never a landing digest' "$repo/agents/skills/doc-hierarchy/SKILL.md"
pin "digest-free witness rule in done" grep -qF 'never a landing digest' "$D"
pin "digest-free witness rule in plans" grep -qF 'never a landing digest' "$repo/agents/skills/plans/SKILL.md"
pin "digest-free witness rule in execute-plan" grep -qF 'never a landing digest' "$E"
# Re-aimed 2026-10-19 (plan docs/history/plans/2026-10-14-skill-monolith-module-extraction.md Task 2): the needle's span moved verbatim to agents/skills/execute-plan/worktree-first.md.
pin "check-single-commit usage literal in the execute-plan tail" grep -qF 'check-single-commit --prev-landing-of <new landing tip>' "$repo/agents/skills/execute-plan/worktree-first.md"
pin "check-single-commit mode present in the guard" grep -qF 'def cmd_check_single_commit' "$repo/scripts/reverse_squash_guard.py"
pin "maintenance survey batch arm wired" grep -qF 'check-single-commit --scan-window' "$SA"

# --- interrupted-manifest bounded-drain census pins (plan 2026-10-03-interrupted-manifest-pile-drain.md Task 3) ---
pin "drain-up-to-five fragment in the survey arm" grep -qF 'drain-up-to-five' "$SA"
pin "interrupted-census.json fragment in the survey arm" grep -qF 'interrupted-census.json' "$SA"
pin "grows-across-turns fragment in the survey arm" grep -qF 'grows across turns' "$SA"
pin "closeout census fragment in the survey arm" grep -qF 'closeout census' "$SA"

# --- base-branch ref-move integrity fence pins (plan 2026-10-03-ref-move-integrity-fences.md Tasks 3-4) ---
# Each wired region of the ref-move integrity plan carries one fixed-string
# presence needle: the pre-swap empty-diff leg and the two audit subcommands
# pin the Task 1-2 scripts, the two execute-plan needles pin the landing
# critical section's fast-forward verification and the closeout audit duty's
# reflog-window invocation, and the blueprint needle pins the final-merge
# paragraph's delegate-form mirror.
pin "pre-swap empty-diff leg present in the parentage gate" grep -qF 'tree-identical to its parent' "$repo/scripts/landing_parentage_gate.py"
pin "reflog-window subcommand present in the audit" grep -qF 'reflog-window' "$repo/scripts/base_reflog_audit.py"
pin "landed-receipt subcommand present in the audit" grep -qF 'landed-receipt' "$repo/scripts/base_reflog_audit.py"
# Re-aimed 2026-10-19 (plan docs/history/plans/2026-10-14-skill-monolith-module-extraction.md Task 2): the needle's span moved verbatim to agents/skills/execute-plan/worktree-first.md.
pin "fast-forward verification wired in execute-plan" grep -qF 'merge-base --is-ancestor <old-tip> <new-tip>' "$repo/agents/skills/execute-plan/worktree-first.md"
pin "reflog-window audit leg wired in execute-plan" grep -qF 'base_reflog_audit.py reflog-window --repo <primary-root>' "$repo/agents/skills/execute-plan/worktree-first.md"
pin "base-branch receipts delegated in the blueprint" grep -qF 'scripts/base_reflog_audit.py' "$TE"

# --- primary-checkout landing helper and staging-gate pins (plan
# docs/history/plans/2026-10-03-squash-landing-failure-path-guard.md Task 4) ---
# Re-pointed 2026-10-11 (plan
# docs/history/plans/2026-10-11-execute-plan-boundary-reliability.md Task 2):
# the blueprints' spelled pre-swap invocation literals retired for the
# land_squash.sh land-worktree helper invocation, so the two containment-leg
# pins re-point to that invocation literal; the execute-plan helper pin
# tightens to the primary-checkout `land --branch` spelling so the new
# worktree-complete ownership sentence (which names land-worktree) cannot
# satisfy it as a substring. Presence needles (at-least-once; no exactly-once
# tripwires on shared files): the helper invocations above; the execution
# claim's `base:` frontmatter line; and the staging-gate id in the done
# enumeration. The execute-plan worktree-complete tail's
# `check-landing --source-branch` containment literal is deliberately NOT
# re-pinned here: its enforcement stays with the sibling plan's landed
# landing-tail wiring (a recorded scoping decision, not an omission).
# Re-aimed 2026-10-19 (plan docs/history/plans/2026-10-14-skill-monolith-module-extraction.md Task 2): the needle's span moved verbatim to agents/skills/execute-plan/worktree-first.md.
pin "primary-checkout helper land invocation wired in execute-plan (tightened 2026-10-11: the land-worktree ownership sentence must not satisfy this pin as a substring)" grep -qF 'scripts/land_squash.sh land --branch' "$repo/agents/skills/execute-plan/worktree-first.md"
pin "containment leg on the execution blueprint's helper invocation literal (re-pointed 2026-10-11 from the retired pre-swap literal)" grep -qF 'land_squash.sh land-worktree' "$TE"
pin "containment leg on the authoring blueprint's helper invocation literal (re-pointed 2026-10-11 from the retired pre-swap literal)" grep -qF 'land_squash.sh land-worktree' "$TA"
pin "execution claim base frontmatter line literal" grep -qF 'base: <the run_base value' "$TE"
pin "post-landing-staging gate id in the done enumeration" grep -qF 'post-landing-staging' "$repo/scripts/done_sweep_gates_lib.py"

# --- maintenance completion-arm audit-duty pins (plan
# docs/history/plans/2026-10-04-docs-branch-sync-fail-loud.md Task 2) ---
# The D1 landing-completion success tail must name the closeout audit duty
# explicitly (origin:
# docs/history/backlog/2026-10-03-maintenance-completion-arm-audit-duty.md):
# region-scoped to the D1 bullet line per the suite's vacuous-canary doctrine
# (the Revisions ledger paraphrases the tail, so a whole-file grep is satisfied
# by a stray copy; deleting any named literal from the tail empties its span
# and fails here).
python3 - "$DE" <<'EOF' | route_heredoc_stream # the D1 bullet moved to the decisions module (the maintenance-skill-size-refactor split); the block must fail the suite, never let a failed pin pass 
import sys
s = open(sys.argv[1]).read()
d1 = ""
for line in s.split("\n"):
    if line.startswith("- `D1 (execute)`:"):
        d1 = line
        break
if not d1:
    print("PIN FAIL: D1 bullet line missing from SKILL.md"); sys.exit(1)
for needle in ("`scripts/base_reflog_audit.py` `reflog-window`",
               "`landed-receipt`",
               "first-parent diffstat receipt"):
    if needle not in d1:
        print("PIN FAIL: D1 landing-completion tail lacks the audit-duty needle %r" % (needle,)); sys.exit(1)
EOF
heredoc_settle "${PIPESTATUS[0]}"

# --- canonical docs-branch sync pins (origin: shared docs-branch archive task) ---
DOC_BRANCH_SKILL="agents/skills/docs-branch/SKILL.md"
# landing-cost telemetry never-blocking pin (landing-cost-telemetry plan, Task 1;
# re-aimed 2026-10-11 to the report module, the done-closeout-lock-span Task 4
# router split): the doctrine sentence frozen verbatim in the done skill's
# Step 7 module - a future edit
# relocating the landing-cost bullet into a required path or weakening the
# fail-open tail fails the suite. The metric path mention is count-gated by
# the plan's validation greps, not duplicated here.
pin "landing-cost record home named in the done skill" grep -qF "landing-costs.jsonl" "$D"
pin "landing-cost telemetry never-blocking posture verbatim" grep -qF "**The never-blocking posture: telemetry is analysis data, never correctness evidence - a failed append (read-only checkout, missing directory, any write error) is reported in this step's outcome and the closeout continues; no step, gate, or landing ever refuses or stalls on a missing, failed, or incomplete record.**" "$D"
DOCS_SYNC_SH="scripts/docs_branch_sync.sh"
DOCS_SYNC_TEST="scripts/test_docs_branch_sync.py"
pin "canonical docs-branch entry point anchor" grep -qF 'docs_branch_sync_main' "$DOCS_SYNC_SH"
pin "canonical runner validates configured roots before traversal" grep -qF 'resolve_roots(repo, facts)' "$DOCS_SYNC_SH"
pin "canonical runner applies strict two-calendar-month UTC cutoff" grep -qF 'month_index = now.year * 12 + now.month - 1 - 2' "$DOCS_SYNC_SH"
pin "canonical runner prunes only after archive snapshot" grep -qF 'trace("prune")' "$DOCS_SYNC_SH"
pin "docs-branch skill names the canonical entry point" grep -qF 'bash scripts/docs_branch_sync.sh' "$DOC_BRANCH_SKILL"
pin "docs-branch skill excludes local tmp from archive roots" grep -qF 'It excludes `docs/tmp/`' "$DOC_BRANCH_SKILL"
pin "docs-branch skill documents the unconditional CAS backend" grep -qF 'uses one repository-level temporary-index and `commit-tree` path with compare-and-swap' "$DOC_BRANCH_SKILL"
pin "docs-branch focused suite covers absent branch paths and pruning" grep -qF 'test_only_review_and_metrics_archives_remain_and_removed_absent_paths_are_reported' "$DOCS_SYNC_TEST"
pin "docs-branch focused suite covers symlink alias resolution" grep -qF 'test_fixed_reviews_symlink_to_configured_root_is_archived_once_at_target' "$DOCS_SYNC_TEST"
pin "docs-branch fixture proves worktree policy does not select a backend" grep -qF 'test_worktree_policy_is_ignored_and_sync_does_not_report_mode' "$DOCS_SYNC_TEST"
pin "docs-branch fixture covers no-op CAS races" grep -qF 'test_noop_update_uses_cas_and_refuses_a_competing_tip' "$DOCS_SYNC_TEST"
pin "docs-branch fixture rejects symlink swap during read" grep -qF 'test_no_follow_read_rejects_file_replaced_after_validation' "$DOCS_SYNC_TEST"
pin "docs-branch restore fixture rejects symlinked parents" grep -qF 'test_restore_refuses_a_symlinked_parent_without_writing_outside' "$DOCS_SYNC_TEST"
expect_absent "retired no-worktree docs helper is absent" 'docs_branch_sync_noworktree.sh' "$repo/scripts/runtime-scripts.list"
pin "retired no-worktree helper file is absent" test ! -e "$repo/scripts/docs_branch_sync_noworktree.sh"
pin "retired plan guard helper and tests are absent" test ! -e "$repo/scripts/docs_branch_plan_guard.py" -a ! -e "$repo/scripts/test_docs_branch_plan_guard.py"
pin "retired backlog dedupe helper and tests are absent" test ! -e "$repo/scripts/docs_branch_backlog_dedupe.py" -a ! -e "$repo/scripts/test_docs_branch_backlog_dedupe.py"
pin "retired no-worktree sync test suite is absent" test ! -e "$repo/scripts/test_docs_branch_sync_noworktree.py"
# Re-aimed 2026-10-11 (done-closeout-lock-span plan Task 4 router split):
# the Step 2 module carries the sync-facing contract rows; the
# merge-wait-acquire absence check sweeps the router plus every module.
pin "done invokes canonical docs-branch runner" grep -qF 'scripts/docs_branch_sync.sh' "$D"
# Re-keyed 2026-10-11 (plan 2026-10-10-done-closeout-lock-span-and-output-cost
# Task 1): the done-side skill lock ceremony was retired for runner-owned
# spans (the sync, witness append, and migration runners hold the merge lock
# inside their own processes), so the row that froze the old
# acquire-before-the-sync sentence now freezes the replacement contract and
# freezes the retired acquire command absent.
pin "done names the runner-owned merge-lock spans" grep -qF 'Runner-owned merge-lock spans' "$D"
for f in "$D"; do expect_absent "retired done-side merge-wait-acquire block is absent from the done skill corpus ($f)" 'merge-wait-acquire' "$f"; done
pin "done keeps availability-checked sync deferral" grep -qF 'Explicit sync deferral (availability-checked)' "$D"
pin "done retains a separate docs-tmp-sweep gate" grep -qF '`docs-tmp-sweep` remains the separate local cleanup gate' "$D"
# --- graded-corrections vocabulary pins (plan
# docs/history/plans/2026-10-04-review-cert-graded-binding.md Task 8) ---
# Two target families. The script-side literals pin the new modules' sources
# (plan_delta_classifier, code_delta_classifier, fix_plan_em_dashes,
# corrections_record), so a script-side widening of the narrowed typography
# equivalence map, the closed directive-comment family, the encoding-cookie
# refusal, the fixer's comma form, or the corrections-record routing constants
# is a visible pinned-literal move, reconciled beside its provenance in the
# same edit. The prose literals pin the graded sentences in the plans and
# execute-plan skill files (and the review-plan seal producer beside the Step 4
# gate it feeds), so a wording change to a pinned graded span is a change to
# the graded contract, never a silent drift. All presence pins (at-least-once;
# no exactly-once tripwires on shared files).
pin "narrowed typography equivalence map comment in the plan classifier" grep -qF 'only em-dash arm is the comma form' "$repo/scripts/plan_delta_classifier.py"
pin "directive-comment refusal family in the code classifier" grep -qF 'the directive-comment family is closed' "$repo/scripts/code_delta_classifier.py"
pin "encoding-cookie refusal in the code classifier" grep -qF 'an encoding declaration on lines 1-2 is runtime' "$repo/scripts/code_delta_classifier.py"
pin "fixer comma form in the em-dash fixer" grep -qF 'comma plus one trailing space' "$repo/scripts/fix_plan_em_dashes.py"
pin "ack receipt field names in corrections_record" grep -qF '("directive", "authorization_witness", "classifier_gap_row")' "$repo/scripts/corrections_record.py"
pin "corrections_record marker prefix constant" grep -qF 'MARKER_PREFIX = "corrections verification: "' "$repo/scripts/corrections_record.py"
pin "corrections_record banned-literal constants" grep -qF 'BANNED_LITERALS = ("source_digest", "source_kind")' "$repo/scripts/corrections_record.py"
# Removed 2026-10-14, arm remove-beside-provenance: the three graded
# resume-exemption spans in execute-plan SKILL.md (the classifier invocation,
# the exemption and correction branch convergence clause, and the
# hand-composed verdict refusal) were adapter-era prose deliberately removed
# by the certified landing e0d7d6961; the literals survive only in the owning
# completed plan
# docs/history/plans/completed/2026-10-04-review-cert-graded-binding.md (whose
# classifier-side rows above stay pinned).
# 2026-10-08 (plan-directory-shape plan, Task 4): the remedy inventory gained
# the shared shape resolver, so the count moved from seven to eight; the old
# literal is re-keyed in the same edit as the reworded inventory sentence.
# Removed 2026-10-14, arm remove-beside-provenance: the remedy inventory in
# execute-plan SKILL.md was adapter-era prose deliberately removed by the
# certified landing e0d7d6961; the superseded seven-file absence row below
# stays (still satisfied trivially).
expect_absent "superseded seven-file remedy count literal must be absent from execute-plan" 'copy all seven' "$E"
pin "code-family seal producer in execute-plan" grep -qF 'records the certification seal entry in the local seal file' "$E"
# Re-aimed 2026-10-19 (plan docs/history/plans/2026-10-14-skill-monolith-module-extraction.md Task 1): the needle's rule-29 span moved verbatim to agents/skills/plans/validation-authoring-rules.md.
pin "graded post-certification rule in plans" grep -qF 'a post-certification delta forces a fresh round unless the classifier proves every hunk exempt' "$repo/agents/skills/plans/validation-authoring-rules.md"
pin "graded fold-row producer span in plans" grep -qF 'A fully exempt fold records one CLI-produced correction row' "$repo/agents/skills/plans/SKILL.md"
pin "graded exit-digest span in plans" grep -qF 'the digest the verified corrections chain terminates at' "$repo/agents/skills/plans/SKILL.md"
pin "plan-family seal producer in review-plan" grep -qF 'records the certification seal entry for the round it certified in the local seal file' "$repo/agents/skills/review-plan/SKILL.md"

# --- revert-set classifier source-resolution pins (plan
# docs/history/plans/2026-10-05-done-lifecycle-recovery-gaps.md Task 1) ---
# The Step 0 revert-set adjudication paragraph's resolution order is the
# contract: three ordered arms (repo-local, deployed home copy,
# facts-resolved canonical skills checkout) with the missing-dependency
# block standing only when all three arms miss. One fixed-string needle over
# the amended paragraph witnesses the ordered arms and the all-miss block
# together, so rewording either is a visible pinned-span move; the
# classifier's own outcome handling stays pinned by its existing suite
# (scripts/test_revert_set_classifier.py).
pin "revert-set classifier fail-closed resolution in the commit runner" grep -qF 'no revert_set_classifier.py resolved (repo-local scripts/ or deployed home)' "$DR"

# --- prompt-log prune-eligibility fence pins (plan
# docs/history/plans/2026-10-05-plan-prompts-prune-eligibility-fence.md Task 2) ---
# Each wired region of the prune-eligibility fence carries one fixed-string
# presence needle: the scoped Prune-rule bullet in the log itself, the landing
# closeout's receipt line and prune-audit invocation in the plans skill, the
# delegated receipt and audit invocation in the authoring blueprint, the
# execute-plan rider-list parenthetical naming both, and the maintenance
# survey's consultative audit arm. The log is read inline by path and is NOT
# added to the header existence loop (whose exact loop line is itself pinned);
# the checker's stale-mode invocation above stays the only execution pin.
# All presence pins (at-least-once).
L="$repo/docs/history/backlog/PLAN-PROMPTS.md"
pin "scoped Prune-rule own-entry bullet in the log" grep -qF 'A landing prunes only its own dispatch entry' "$L"
pin "prune-audit invocation named in the log's scoped rule" grep -qF 'python3 scripts/check_prompt_log_origins.py --prune-audit --base <merge-base>' "$L"
pin "prune receipt duty wired in the plans closeout" grep -qF 'PLAN-PROMPTS-PRUNE: <slug> -> <witness path>' "$repo/agents/skills/plans/SKILL.md"
pin "prune-audit invocation wired in the plans closeout" grep -qF 'python3 scripts/check_prompt_log_origins.py --prune-audit --base <merge-base>' "$repo/agents/skills/plans/SKILL.md"
pin "prune receipt duty delegated in the authoring blueprint" grep -qF 'PLAN-PROMPTS-PRUNE: <slug> -> <witness path>' "$TA"
pin "prune-audit invocation delegated in the authoring blueprint" grep -qF 'python3 scripts/check_prompt_log_origins.py --prune-audit --base <merge-base>' "$TA"
# Re-aimed 2026-10-19 (plan docs/history/plans/2026-10-14-skill-monolith-module-extraction.md Task 2): the needle's span moved verbatim to agents/skills/execute-plan/worktree-first.md.
pin "rider parenthetical names receipt and audit gate in execute-plan" grep -qF 'one `PLAN-PROMPTS-PRUNE: <slug> -> <witness path>` receipt line per removed entry, gated by the pre-rider prune audit' "$repo/agents/skills/execute-plan/worktree-first.md"
pin "consultative prune-audit arm wired in the maintenance survey" grep -qF 'python3 scripts/check_prompt_log_origins.py --prune-audit --base <ref>' "$DE"

# --- execution-claim gateway wiring pins (plan
# docs/history/plans/2026-10-07-execution-claim-write-enforcement.md Task 2) ---
# Companion pins for the gateway wiring: the execute-plan worktree-first
# creation step (lifecycle step 1) carries the pinned take invocation as the
# single worktree create path (count-gated whole-file), the execution
# blueprint's PER-EXECUTION WORKTREE paragraph carries the same invocation
# (exactly-once whole-file), the blueprint's EXECUTION CLAIM paragraph names
# the script as the claim-creation procedure of record, and the execute-plan
# skill carries the claim-mode invocation for the authorized primary-placement
# lane. Pin inventory note (same task): no pre-existing pin row keyed on the
# retired hand-write prose (the create sentence's noclobber redirection
# clause, the registration paragraph's hand-write duty, the separate creation
# prose), and every overlapping pin (the EXECUTION CLAIM anchor, the
# `base:` frontmatter literal, the densified-refresh exactly-once count, the
# worktree-first reference spans) keys on text this edit preserves verbatim,
# so there were no rows to re-key; the recognition moves forward onto the new
# pinned sentences through these companion pins, and the retired operative
# prose is frozen absent wrap-tolerant per the suite's freeze-literal
# convention (superseding origin: the plan's Gate delta). The blueprint's
# take-invocation pin is exactly-once whole-file (the dated deviation-list
# entry paraphrases the line, so a ledger copy cannot satisfy it); the
# execute-plan skill's is a count gate (== 2, the two legitimate sites: the
# gateway step and the claim registration paragraph; the queue-drain
# continuation paragraph routes through the pinned invocation by reference
# and must not grow a third literal copy).
# Re-aimed 2026-10-19 (plan docs/history/plans/2026-10-14-skill-monolith-module-extraction.md Task 2): split-count re-aim - the take invocation's site 1 (lifecycle step 1) moved verbatim to agents/skills/execute-plan/worktree-first.md and site 2 (claim registration) stays in agents/skills/execute-plan/SKILL.md; the pre-extraction total 2 is preserved as 1+1 across the two legs.
pin "execution-claim take gateway invocation in execute-plan lifecycle step 1" test $(( $(grep -oF 'bash scripts/execution_claim.sh take <plan-path> --session <id> --branch <name> --worktree-parent <dir> [--base <ref>]' "$repo/agents/skills/execute-plan/worktree-first.md" | wc -l | tr -d ' ') + $(grep -oF 'bash scripts/execution_claim.sh take <plan-path> --session <id> --branch <name> --worktree-parent <dir> [--base <ref>]' "$E" | wc -l | tr -d ' ') )) -eq 2
pin "execution-claim take invocation in the blueprint's per-execution worktree paragraph" test "$(grep -oF 'bash scripts/execution_claim.sh take <plan-path> --session <id> --branch <name> --worktree-parent <dir> [--base <ref>]' "$TE" | wc -l | tr -d ' ')" -eq 1
pin "execution-claim script named as the claim-creation procedure of record in the blueprint" grep -qF 'by scripts/execution_claim.sh, the creation procedure of record' "$TE"
# --- primary-resolution stand-down pins (plan
# docs/history/plans/completed/2026-10-10-execute-plan-primary-placement-resolution.md,
# Task 1; re-keyed by the placement-closing-doctrine-enforcement plan Task 1)
# --- the two-route stop-report pins were retired with the conflict-and-stop
# arm they pinned; these pins cover the consolidated primary resolution's
# stand-down-relevant sentences (the two-spelled-forms unconfigured fallback,
# the base-branch verification stand-down, the serialization refusal, and the
# resume branch-mismatch stand-down), each count-gated exactly 1 on the
# post-edit tree so the fragments cannot drift out of their arm-local scopes.
# Re-aimed 2026-10-19 (plan docs/history/plans/2026-10-14-skill-monolith-module-extraction.md Task 2): the needle's span moved verbatim to agents/skills/execute-plan/worktree-first.md.
pin "primary resolution enum value falls back to unconfigured with a named report" test "$(grep -cF 'outside the two spelled forms, or an unresolvable root, is treated as unconfigured with a named report, never a silent fallback' "$repo/agents/skills/execute-plan/worktree-first.md" | tr -d ' ')" -eq 1
pin "primary resolution base-branch verification stand-down for personal and pet profiles" test "$(grep -cF 'is the base branch at run start, and a run finding a non-base current branch stands down with the remedy named in its stand-down report' "$repo/agents/skills/execute-plan/worktree-first.md" | tr -d ' ')" -eq 1
pin "primary resolution serialization refusal on a fresh run" test "$(grep -cF 'a fresh run in the primary checkout refuses to start while another live execution claim or recorded witness occupies the primary checkout' "$repo/agents/skills/execute-plan/worktree-first.md" | tr -d ' ')" -eq 1
pin "primary resolution resume branch-mismatch stand-down" test "$(grep -cF 'stands down on a mismatch instead of re-recording the switched branch' "$E" | tr -d ' ')" -eq 1

# --- coordination single-writer TTL arm pins (plan
# 2026-10-10-coordination-single-writer-ttl, Task 2) ---
# The arm-3 restored-worktree takeover and the arm-4 compare-and-delete
# serialization, by reference in the execute-plan skill's resumed-lane
# sentence (lifecycle step 1) and the claim-registration paragraph's grant
# sentence; count-gated exactly 1 each on the post-edit tree.
# Re-aimed 2026-10-19 (plan docs/history/plans/2026-10-14-skill-monolith-module-extraction.md Task 2): the needle's span moved verbatim to agents/skills/execute-plan/worktree-first.md.
# Re-aimed 2026-10-23 (plan docs/history/plans/2026-10-21-dead-run-resume-claim-conversion.md Task 3): the arm-3 matcher semantic is retired by the dead-run conversion arm; both resumed-lane needles route to the recovery procedure in agents/skills/maintenance/template-execution.md, the arm-4 compare-and-delete needle unchanged.
pin "execute-plan resumed-lane sentence names the arm-3 takeover" test "$(grep -cF "converts through the claim gateway's dead-run conversion arm per the recovery procedure in agents/skills/maintenance/template-execution.md (the sole recovery procedure; the gateway refuses unchanged when the evidence does not verify" "$repo/agents/skills/execute-plan/worktree-first.md" | tr -d ' ')" -eq 1
pin "execute-plan claim-registration sentence names arms 3 and 4" test "$(grep -cF "the restored-worktree resume routes through the claim gateway's dead-run conversion arm per the recovery procedure in agents/skills/maintenance/template-execution.md, the sole recovery procedure, and the gateway's claim mutations are last-instant compare-and-delete serialized per its arm-4 with a lost race refusing naming the racing holder" "$E" | tr -d ' ')" -eq 1
pin "execution-claim take-refusal clause named in the user-directed-override rule" grep -qF 'the execution-claim take refusal (the run-worktree creation gateway refusing over a fresh foreign claim; its refusal names this rule as the override route)' "$GU"
expect_absent_flat "retired execution-claim hand-write noclobber clause must be absent from prompt-templates.md (wrap-tolerant; superseded 2026-10-07 by the execution-claim gateway wiring)" 'the write is create-if-absent noclobber, the redirection failure being the refusal path' "$P"
expect_absent_flat "retired execution-claim hand-write registration duty must be absent from the execute-plan skill (wrap-tolerant; superseded 2026-10-07 by the execution-claim gateway wiring)" 'the run writes and thereafter honors the claim file' "$E"
expect_absent_flat "retired queue-drain hand-write claim duty must be absent from the execute-plan skill (wrap-tolerant; superseded 2026-10-07 by the gateway routing)" 'a noclobber claim file under the primary checkout' "$E"
expect_absent_flat "retired separate worktree creation prose must be absent from the execute-plan skill (wrap-tolerant; superseded 2026-10-07 by the execution-claim gateway wiring)" 'Create an ad-hoc worktree on its own branch off the per-project base branch' "$E"

# --- origin-independent eligibility and privacy emission pins (plan
# docs/history/plans/2026-10-07-investigate-origin-independent-eligibility.md,
# Tasks 1-2) ---
# The eligibility contract commit 4a9ddba4 landed as prose only: investigate
# eligibility never depends on where a defect's evidence originated (the only
# sanctioned skips are duplicate representation by an existing log entry's
# `Origins:` line and plans-root coverage), emitted log entries and cluster
# annotations stay personal-data-free and repo-relative, and the maintenance
# monitor's matching skip rule holds the same duplicate-or-covered shape.
# Presence pins freeze the landed sentences (a wording change to a pinned span
# is a change to the owning plan's prescribed text, so reconcile the pin and
# the text in the same edit and record the superseding origin); the
# maintenance-side spans are count-gated at exactly 1 (the grep -oF | wc -l
# form). That whole-file count gate's actual guarantee: a future
# Revisions-ledger quote is caught while the live span also exists (the count
# rises to 2), while a deletion of the live span masked by exactly one
# surviving quote is outside the whole-file count gate (the count stays 1 and
# the gate passes). The suite's vacuous-canary doctrine closes that masking
# case with region-scoped needles (the D1 precedent); the whole-file form here
# is the plan's prescribed form, so the region-scoping doctrine deviation is
# deliberate. The investigate presence pins stay plain presence greps on the
# recorded assumption that the investigate skill carries no Revisions-ledger
# quoting surface (a surviving quote would satisfy a presence pin through a
# live-sentence deletion the same way); if such a quoting surface appears
# there, re-key these pins to the same count gate.
# Anti-pattern pins freeze the three historical exclusion literals
# ('foreign-origin', 'ownership skip', 'never grouped, investigated, or
# dispatched'; the third is investigate-only) out of both skill files with the
# wrap-tolerant flat form (the expect_absent_flat normalization, per the p57
# Task 5 doctrine comment), so a line-wrapped reintroduction cannot evade the
# pin. Benign mentions trip these pins too: a future ledger note naming a
# banned literal matches its flat scan, and a note quoting a count-gated span
# pushes that span's count to 2; reconcile by rewording the note or by
# reconciling the pin in the same edit. The collision-prone one is the
# count-gated needle (c) 'repo-relative paths only' (Task 2's lettering),
# whose short generic form is ordinary convention prose.
# Implemented as a function taking the root as its argument so the inline
# selftest below can call it directly on a fixture (never a whole-suite
# re-invocation, which would die for the wrong reason on a temp fixture or
# recurse on an in-repo one); this section adds no mid-suite checkpoint, so
# its only exit path is the selftest assertions plus the suite's final gate
# funnel.
check_origin_independent_eligibility() { # $1 = root carrying agents/skills/investigate/SKILL.md and agents/skills/maintenance/SKILL.md
  local root="$1" rc=0
  local inv="$root/agents/skills/investigate/SKILL.md"
  # the monitor duties moved to the decisions module (the
  # maintenance-skill-size-refactor split); the fixture selftest reads there
  local mon="$root/agents/skills/maintenance/decisions.md"
  local out grc pat
  # investigate presence pins (Task 1): one fixed-string grep per landed sentence
  grep -qF 'Origin repository or organization does not restrict investigation' "$inv" || { recorded_red_check "investigate eligibility opener sentence missing from" "PIN FAIL: investigate eligibility opener sentence missing from $inv" || rc=1; }
  grep -qF "Skip an origin only when it is already represented by an existing entry's \`Origins:\` line in either rolling log" "$inv" || { recorded_red_check "investigate sanctioned skip-shape span missing from" "PIN FAIL: investigate sanctioned skip-shape span missing from $inv" || rc=1; }
  grep -qF 'origin repository and organization do not affect eligibility' "$inv" || { recorded_red_check "investigate eligibility-indifference sentence missing from" "PIN FAIL: investigate eligibility-indifference sentence missing from $inv" || rc=1; }
  grep -qF 'origin repository and organization do not exclude the input item or a relevant sibling' "$inv" || { recorded_red_check "investigate non-exclusion sentence missing from" "PIN FAIL: investigate non-exclusion sentence missing from $inv" || rc=1; }
  grep -qF 'redact foreign identifiers and personal data' "$inv" || { recorded_red_check "investigate redaction duty sentence missing from" "PIN FAIL: investigate redaction duty sentence missing from $inv" || rc=1; }
  grep -qF 'keep foreign identifiers, personal data, and details outside this repository out of cluster annotations and emitted entries' "$inv" || { recorded_red_check "investigate emission-privacy duty sentence missing from" "PIN FAIL: investigate emission-privacy duty sentence missing from $inv" || rc=1; }
  grep -qF "Keep cluster annotations within this repository's safe, repo-relative vocabulary and omit foreign identifiers or personal data" "$inv" || { recorded_red_check "investigate Stage 0 redaction sentence missing from" "PIN FAIL: investigate Stage 0 redaction sentence missing from $inv" || rc=1; }
  # investigate anti-pattern pins (Task 1): wrap-tolerant flat absence with the
  # expect_absent_flat three-way polarity (rc 0 = reintroduced, rc >= 2 = grep
  # error, rc 1 = clean)
  for pat in 'foreign-origin' 'ownership skip' 'never grouped, investigated, or dispatched'; do
    out="$(tr '\n' ' ' < "$inv" | tr -s ' ' | grep -nF -- "$pat" 2>&1)"; grc=$?
    if [ "$grc" -eq 0 ]; then
      recorded_red_check "banned literal '' reintroduced in (wrap-tolerant flat scan)" "PIN FAIL: banned literal '$pat' reintroduced in $inv (wrap-tolerant flat scan)" || rc=1
    elif [ "$grc" -ge 2 ]; then
      recorded_red_check "grep error on while checking flat absence:" "PIN FAIL: grep error on $inv while checking flat absence: $out" || rc=1
    fi
  done
  # maintenance presence pins (Task 2): count-gated at exactly 1 (the
  # grep -oF | wc -l form; a future Revisions-ledger quote must not satisfy a
  # deletion). The two skip-shape needles re-aimed 2026-10-08 (two-mode loop
  # policy plan Task 3): duty (e) now reads the two-log shape, its
  # origin-intersection skip naming "either rolling log" and the investigate
  # leg firing only when neither log has a ready entry.
  [ "$(grep -oF "skip any ungrouped open backlog item whose origins intersect an existing entry's" "$mon" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "monitor eligibility rule span count != 1 in" "PIN FAIL: monitor eligibility rule span count != 1 in $mon" || rc=1; }
  [ "$(grep -oF "origins intersect an existing entry's \`Origins:\` line in either rolling log or a plans-root plan file" "$mon" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "monitor duplicate-or-covered skip shape count != 1 in" "PIN FAIL: monitor duplicate-or-covered skip shape count != 1 in $mon" || rc=1; }
  [ "$(grep -oF 'repo-relative paths only' "$mon" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "monitor emission vocabulary rule count != 1 in" "PIN FAIL: monitor emission vocabulary rule count != 1 in $mon" || rc=1; }
  # maintenance anti-pattern pins (Task 2): the same wrap-tolerant flat form
  for pat in 'foreign-origin' 'ownership skip'; do
    out="$(tr '\n' ' ' < "$mon" | tr -s ' ' | grep -nF -- "$pat" 2>&1)"; grc=$?
    if [ "$grc" -eq 0 ]; then
      recorded_red_check "banned literal '' reintroduced in (wrap-tolerant flat scan)" "PIN FAIL: banned literal '$pat' reintroduced in $mon (wrap-tolerant flat scan)" || rc=1
    elif [ "$grc" -ge 2 ]; then
      recorded_red_check "grep error on while checking flat absence:" "PIN FAIL: grep error on $mon while checking flat absence: $out" || rc=1
    fi
  done
  return "$rc"
}

# Section-local existence check (the budget-gate seam's local-check shape): a
# missing investigate skill fails loudly as missing here because the suite
# header's byte-pinned existence loop must stay byte-unchanged.
I="$repo/agents/skills/investigate/SKILL.md"
[ -f "$I" ] || { echo "missing $I"; fail=1; }

# live-tree run (the pass arm): pin failures print here and the suite's final
# gate funnel turns them into the exit
if ! check_origin_independent_eligibility "$repo"; then
  fail=1
fi

# Witnessed fail arm (the per-section fixture seam): a mktemp fixture root
# carrying byte-copies of BOTH skill files at their repo-relative paths. The
# clean fixture passes; the injection loop then seeds one exclusion sentence
# per banned literal into the copy whose file bans it (all three into the
# investigate copy, two into the maintenance copy), each injection restoring
# the pristine copies first so each run's trip stays single-sided and the
# runtime stays linear in the literal count, and each captured refusal must
# trip the section's pin function at function level and name the injected
# literal; a selftest failure fails the suite.
ORIGIN_FIXTURE="$(mktemp -d "${TMPDIR:-/tmp}/pins-origin-fixture.XXXXXX")"
mkdir -p "$ORIGIN_FIXTURE/agents/skills/investigate" "$ORIGIN_FIXTURE/agents/skills/maintenance"
cp "$I" "$ORIGIN_FIXTURE/agents/skills/investigate/SKILL.md"
cp "$S" "$ORIGIN_FIXTURE/agents/skills/maintenance/SKILL.md"
cp "$DE" "$ORIGIN_FIXTURE/agents/skills/maintenance/decisions.md"
# the same fixture without the injection passes (no stray PIN FAIL lines in a
# passing run)
ORIGIN_CLEAN_OUT="$(check_origin_independent_eligibility "$ORIGIN_FIXTURE" 2>&1)"
ORIGIN_CLEAN_RC=$?
if [ "$ORIGIN_CLEAN_RC" -ne 0 ] || printf '%s' "$ORIGIN_CLEAN_OUT" | grep -q 'PIN FAIL'; then
  recorded_red_check "origin-eligibility selftest: clean fixture copy failed (rc ):" "PIN FAIL: origin-eligibility selftest: clean fixture copy failed (rc $ORIGIN_CLEAN_RC): $ORIGIN_CLEAN_OUT" || fail=1
fi
# inject every literal the investigate file bans, one sentence per injection
for ORIGIN_PAT in 'foreign-origin' 'ownership skip' 'never grouped, investigated, or dispatched'; do
  cp "$I" "$ORIGIN_FIXTURE/agents/skills/investigate/SKILL.md"
  cp "$S" "$ORIGIN_FIXTURE/agents/skills/maintenance/SKILL.md"
  cp "$DE" "$ORIGIN_FIXTURE/agents/skills/maintenance/decisions.md"
  printf '%s\n' "A historical exclusion returns here: $ORIGIN_PAT." >> "$ORIGIN_FIXTURE/agents/skills/investigate/SKILL.md"
  ORIGIN_INJ_OUT="$(check_origin_independent_eligibility "$ORIGIN_FIXTURE" 2>&1)"
  ORIGIN_INJ_RC=$?
  if [ "$ORIGIN_INJ_RC" -eq 0 ]; then
    recorded_red_check "origin-eligibility selftest: injected '' into the investigate copy did not fail (rc 0)" "PIN FAIL: origin-eligibility selftest: injected '$ORIGIN_PAT' into the investigate copy did not fail (rc 0)" || fail=1
  elif ! printf '%s' "$ORIGIN_INJ_OUT" | grep -qF -- "$ORIGIN_PAT"; then
    recorded_red_check "origin-eligibility selftest: refusal output does not name the injected literal ''" "PIN FAIL: origin-eligibility selftest: refusal output does not name the injected literal '$ORIGIN_PAT'" || fail=1
  fi
done
# Outcome-contract arm (scripts/OUTCOME_CONTRACT.md): a refusal run ends with
# exactly one final `OUTCOME: fail` line emitted by the same helper every exit
# checkpoint funnels through; modeled on the live-vs-archive section's fixture
# seam (never a whole-suite re-invocation). One witnessed run bounds the
# loop's runtime; the terminal shape is literal-independent (the loop already
# asserted the trip and the named literal for every injection).
cp "$I" "$ORIGIN_FIXTURE/agents/skills/investigate/SKILL.md"
cp "$S" "$ORIGIN_FIXTURE/agents/skills/maintenance/SKILL.md"
printf '%s\n' 'A historical exclusion returns here: foreign-origin.' >> "$ORIGIN_FIXTURE/agents/skills/investigate/SKILL.md"
MODELED_REFUSAL="$( { check_origin_independent_eligibility "$ORIGIN_FIXTURE" 2>&1 || emit_outcome fail; } )"
if [ "$(printf '%s\n' "$MODELED_REFUSAL" | tail -n 1)" != "OUTCOME: fail" ] || \
   [ "$(printf '%s\n' "$MODELED_REFUSAL" | grep -c '^OUTCOME:' | tr -d ' ')" != "1" ]; then
  recorded_red_check "origin-eligibility selftest: refusal run does not end with exactly one final OUTCOME: fail line" "PIN FAIL: origin-eligibility selftest: refusal run does not end with exactly one final OUTCOME: fail line" || fail=1
fi
# the maintenance anti-pattern pins share this fixture seam: the same loop
# over the literals the maintenance file bans, each injection restoring the
# pristine investigate half so only the monitor-side pins trip
for ORIGIN_PAT in 'foreign-origin' 'ownership skip'; do
  cp "$I" "$ORIGIN_FIXTURE/agents/skills/investigate/SKILL.md"
  cp "$S" "$ORIGIN_FIXTURE/agents/skills/maintenance/SKILL.md"
  cp "$DE" "$ORIGIN_FIXTURE/agents/skills/maintenance/decisions.md"
  printf '%s\n' "A historical exclusion returns here: $ORIGIN_PAT." >> "$ORIGIN_FIXTURE/agents/skills/maintenance/decisions.md"
  ORIGIN_MON_OUT="$(check_origin_independent_eligibility "$ORIGIN_FIXTURE" 2>&1)"
  ORIGIN_MON_RC=$?
  if [ "$ORIGIN_MON_RC" -eq 0 ]; then
    recorded_red_check "origin-eligibility selftest: injected '' into the maintenance copy did not fail (rc 0)" "PIN FAIL: origin-eligibility selftest: injected '$ORIGIN_PAT' into the maintenance copy did not fail (rc 0)" || fail=1
  elif ! printf '%s' "$ORIGIN_MON_OUT" | grep -qF -- "$ORIGIN_PAT" || \
       ! printf '%s' "$ORIGIN_MON_OUT" | grep -qF 'maintenance/decisions.md'; then
    recorded_red_check "origin-eligibility selftest: maintenance refusal does not name the injected literal '' on the maintenance copy" "PIN FAIL: origin-eligibility selftest: maintenance refusal does not name the injected literal '$ORIGIN_PAT' on the maintenance copy" || fail=1
  elif printf '%s' "$ORIGIN_MON_OUT" | grep -qF 'investigate/SKILL.md'; then
    recorded_red_check "origin-eligibility selftest: maintenance-only injection tripped an investigate-side pin (the pristine investigate half must hold)" "PIN FAIL: origin-eligibility selftest: maintenance-only injection tripped an investigate-side pin (the pristine investigate half must hold)" || fail=1
  fi
done
rm -rf "$ORIGIN_FIXTURE"

# --- worktree-removal migration gate prescribed-invocation pins (plan
# docs/history/plans/2026-10-07-worktree-removal-migration-gate.md Task 2) ---
# One presence pin per prose home (the done skill's Step 2 module's migration
# paragraph, the maintenance authoring payload's closeout sentence set, the
# plans skill's Final Step section) holding the gated invocation literal the
# gate-removal subcommand prescribes at the worktree removal point, so
# deleting or re-pointing any home's prescribed invocation fails the suite.
# Plain presence form per the plan's Task 2 prescription (no new count
# obligation): the rule-36 joint-direction simulation over each edited file's
# surviving count-gate set plus these pins ran at authoring time against a
# temp copy carrying all prescribed insertions and is recorded in the run
# log, not re-enacted here.
pin "done skill Step 2 prescribed gate-removal invocation" grep -qF 'python3 scripts/worktree_closeout_migrate.py gate-removal --plan <plan> --target <primary> --worktree <worktree>' "$D"
pin "maintenance authoring payload prescribed gate-removal invocation" grep -qF 'python3 scripts/worktree_closeout_migrate.py gate-removal --plan <plan> --target <primary> --worktree <worktree>' "$TA"
pin "plans Final Step prescribed gate-removal invocation" grep -qF 'python3 scripts/worktree_closeout_migrate.py gate-removal --plan <plan> --target <primary> --worktree <worktree>' "$PL"
# --- per-session Loop modes section pins (plan
# docs/history/plans/completed/2026-10-06-two-mode-loop-policy.md, Task 1) ---
# Companion presence pins over the new section's prescribed spans, one per
# Validation Commands item 4 obligation: the section heading, the binding
# vocabulary and precedence spans, the per-turn mode token, the enforcement
# marker, the survey_only operator write-duty span, the starvation bypass
# token, the visibility format literal, and the guard literals (the
# survey-only resolution span and the class-guard-survey-only exemption
# token). Plain presence form per the plan's Task 1 prescription (no count
# obligation; single-line homes; corrected 2026-10-08, tmlp exec r12: the
# earlier claim that these paragraphs carry no Revisions ledger copy is false
# for the starvation bypass token, whose needle the Task 2 Revisions ledger
# entry quotes verbatim, so a whole-file grep stayed green through a
# live-span deletion; that pin is scoped pre-Revisions below and the other
# paragraphs' pins keep the whole-file form), so a deleted paragraph marker
# or duty span fails here.
pin "Loop modes section anchored" grep -qF '## Loop modes' "$S"
pin "mode binding paragraph marker" grep -qF 'Mode binding.' "$S"
# re-aimed 2026-10-15 (plan 2026-10-15-post-landing-origin-ancestry-diagnostic
# Task 4): the fa22ac133 rewording folded the postfix vocabulary sentence into
# the mode vocabulary enumeration whose author clause is the current carrier
# span, the semantics unchanged (the same wording classes resolve to the same
# modes; only the `auth` keyword was added), so the pin re-keys on that clause
pin "binding postfix vocabulary span" grep -qF 'classifies auth, author, authoring wording as author mode' "$S"
pin "binding survey-wording precedence span" grep -qF 'survey and stand-down wording outrank both-lanes wording' "$S"
pin "binding per-turn mode token" grep -qF 'mode:<author|exec|dual|survey>' "$DE"
pin "mode enforcement paragraph marker" grep -qF 'Mode enforcement.' "$S"
pin "survey_only operator write-duty span" grep -qF 'writes the flag via one targeted field edit in that turn, before the turn ends, beside the decision record' "$S"
# r12 fold (2026-10-08): pre-Revisions scope, the Task 2 Revisions ledger
# entry quoting the token verbatim; same awk idiom as the zero-survivor gate.
pin "starvation switch bypass token (pre-Revisions) (operative corpus)" bash -c "cat \"$S\" \"$SA\" \"$GU\" \"$DE\" \"$QP\" \"$SC\" \"$SF\" \"$FC\" | grep -qF 'mode-starved-bypass'"
pin "mode visibility format literal" grep -qF 'mode: <author|exec|dual|survey> (session)' "$S"
pin "class guard survey-only resolution span" grep -qF 'resolves both work lanes to survey-only' "$S"
pin "class-guard-survey-only exemption token" grep -qF 'class-guard-survey-only' "$SA"
pin "Project-class guard paragraph marker" grep -qF 'Project-class guard.' "$S"

# --- re-arm dispatch-ladder incident-guard pins (plan
# docs/history/plans/2026-10-17-rearm-dispatch-ladder-incident-guards.md,
# Task 4) ---
# Companion count-exact pins over the three guard arms' insertion spans, one
# row per Validation Commands expect1 obligation: arm 1 the ownership
# allowlist (the overlay rule set, the widened live-child stand-down, the
# retired null-id span-match fallback span, the Otherwise-arm park span, the
# duties-core FIRST ACTION mirror, and the SKILL.md Step 0 mirror), arm 2 the
# post-delete probe with the distinct-failure rollback (the rule set, the
# rollback supersession, the truncation no-re-poll span, the
# dispatch-discipline exception enumeration, the two-mutating-calls
# parenthetical, and the duties-core mirror), and arm 3 the launchd
# default-in-waiting demotion paragraph. Every row is count-gated at exactly 1
# whole-file per the plan's expect1 idiom, so a restatement anywhere fails as
# a second home.
pin "arm 1 ownership-allowlist rule-set heading" test "$(grep -oF 'Ownership allowlist (every automation delete on this ladder)' "$Z" | wc -l | tr -d ' ')" -eq 1
pin "arm 1 null-id no-deletable-record sentence" test "$(grep -oF 'A null recorded id has no deletable record' "$Z" | wc -l | tr -d ' ')" -eq 1
pin "arm 1 bind-at-create sentence" test "$(grep -oF "Bind at create: a successful create's returned id" "$Z" | wc -l | tr -d ' ')" -eq 1
pin "arm 1 ownership-test repo-scoped recognition span" test "$(grep -oF 'the ownership allowlist is the test and recognition matching is repo-scoped' "$Z" | wc -l | tr -d ' ')" -eq 1
pin "arm 1 delete-first targets preserved span" test "$(grep -oF 'stay the delete-first targets' "$Z" | wc -l | tr -d ' ')" -eq 1
pin "arm 1 retired span-match fallback span" test "$(grep -oF 'never a span-matched fallback delete' "$Z" | wc -l | tr -d ' ')" -eq 1
pin "arm 1 otherwise-arm park span" test "$(grep -oF 'the Otherwise arm below parks that dispatch for the operator per the ownership allowlist' "$Z" | wc -l | tr -d ' ')" -eq 1
pin "arm 1 form-unknown park span" test "$(grep -oF 'Form-unknown or a recorded recurring form' "$Z" | wc -l | tr -d ' ')" -eq 1
pin "arm 1 duties-core allowlist mirror span" test "$(grep -oF 'never any other lingered record in the listing' "$DC" | wc -l | tr -d ' ')" -eq 1
pin "arm 1 SKILL.md allowlist mirror span" test "$(grep -oF "The overlay's ownership allowlist governs every automation delete" "$S" | wc -l | tr -d ' ')" -eq 1
pin "arm 2 post-delete probe rule heading" test "$(grep -oF 'Post-delete probe: after any automation delete on this ladder' "$Z" | wc -l | tr -d ' ')" -eq 1
pin "arm 2 distinct-failure rollback rule heading" test "$(grep -oF 'Distinct-failure rollback: a retry after a failed create must change mechanism' "$Z" | wc -l | tr -d ' ')" -eq 1
pin "arm 2 truncation no-re-poll span" test "$(grep -oF 'never re-poll against the same cap' "$Z" | wc -l | tr -d ' ')" -eq 1
pin "arm 2 rollback supersession span" test "$(grep -oF 'the distinct-failure rollback rule supersedes the identical-retry budget' "$Z" | wc -l | tr -d ' ')" -eq 1
pin "arm 2 dispatch-discipline probe exception span" test "$(grep -oF 'and the post-delete probe listing), which precedes or intervenes' "$Z" | wc -l | tr -d ' ')" -eq 1
pin "arm 2 two-mutating-calls probe span" test "$(grep -oF 'plus the mandated post-delete probe listing between them' "$Z" | wc -l | tr -d ' ')" -eq 1
pin "arm 2 duties-core probe mirror span" test "$(grep -oF 'one read-only listing probe precedes the create' "$DC" | wc -l | tr -d ' ')" -eq 1
pin "arm 3 demoted-fallback paragraph heading" test "$(grep -oF 'Demoted fallback (arm 3)' "$Z" | wc -l | tr -d ' ')" -eq 1
pin "arm 3 retired default-dispatch span" test "$(grep -oF 'stops being the default child dispatch for sessions already bound to an armed record' "$Z" | wc -l | tr -d ' ')" -eq 1
pin "arm 3 promotion-review activation span" test "$(grep -oF 'takes over as the operative default for bound sessions only when the promotion review' "$Z" | wc -l | tr -d ' ')" -eq 1

# --- two-mode loop policy Task 3 pins (plan
# docs/history/plans/completed/2026-10-06-two-mode-loop-policy.md, Task 3) ---
# Companion presence pins over the exec-mode machinery's prescribed spans,
# one per Validation Commands item 5 obligation plus the plan's named
# spans: the unified selection rule and its ordering contract, the ad-hoc
# arm span (kind adhoc, the panel receipt, the plan-file abstinence), the
# queued-execution fence carve-outs, the EXEC-PROMPTS duties (the receipt,
# the dispatch leg, the dual-log monitor lead), the dual-log survey
# exclusion and the never-cited invariant, the ad-hoc completion evidence
# and the append-only kind enum, the PLAN-PROMPTS ad-hoc-superseded
# prune-witness class with its freeze reopen case, the investigate verdict
# span, and the re-aimed Stage 4 self-check invocation literal. Plain
# presence form per the Task 1 idiom (single-line homes; no count
# obligation; corrected 2026-10-08, tmlp exec r12: the earlier claim that
# these spans carry no Revisions ledger copy is false for the four SKILL.md
# pins whose needles the Task 3 Revisions ledger entry quotes verbatim, so
# a whole-file grep stayed green through a live-span deletion; those four
# are scoped pre-Revisions below and the rest keep the whole-file form), so
# a deleted span fails here.
R="$repo/docs/history/backlog/PLAN-PROMPTS.md"
X="$repo/docs/history/backlog/EXEC-PROMPTS.md"
for f in "$R" "$X"; do
  [ -f "$f" ] || { echo "missing $f"; fail=1; }
done
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

# r12 fold (2026-10-08): the four SKILL.md pins whose needles the Task 3
# Revisions ledger entry quotes verbatim are pre-Revisions scoped below
# (same awk idiom as the zero-survivor gate).
pin "exec-mode selection rule span (operative corpus)" bash -c "cat \"$S\" \"$SA\" \"$GU\" \"$DE\" \"$QP\" \"$SC\" \"$SF\" \"$FC\" | grep -qF 'urgency-ordered candidate set'"
pin "selection ordering contract span" grep -qF 'read first exactly as D1' "$DE"
pin "ad-hoc arm kind span" grep -qF 'kind `adhoc` in its own ad-hoc worktree' "$DE"
pin "ad-hoc arm panel receipt literal (operative corpus)" bash -c "cat \"$S\" \"$SA\" \"$GU\" \"$DE\" \"$QP\" \"$SC\" \"$SF\" \"$FC\" | grep -qF 'Ad-hoc-panel-pass:'"
pin "ad-hoc arm plan-file abstinence span" grep -qF 'the arm never authors, edits, or archives plan files' "$DE"
pin "queued-execution fence author-mode carve-out" grep -qF 'the author-mode carve-out' "$SA"
pin "queued-execution fence class-guard carve-out" grep -qF 'the class-guard carve-out' "$SA"
pin "EXEC-PROMPTS prune receipt duty span (pre-Revisions) (operative corpus)" bash -c "cat \"$S\" \"$SA\" \"$GU\" \"$DE\" \"$QP\" \"$SC\" \"$SF\" \"$FC\" | grep -qF 'EXEC-PROMPTS-PRUNE: <slug> -> <landing commit>'"
pin "EXEC-PROMPTS dispatch duty span" grep -qF "the top ready unfrozen EXEC-PROMPTS.md entry is the ad-hoc run's context source" "$DE"
pin "dual-log monitor lead span" grep -qF 'reading EXEC-PROMPTS.md beside PLAN-PROMPTS.md with the same write discipline' "$DE"
pin "dual-log survey exclusion span" grep -qF 'excludes both rolling prompt log files (`PLAN-PROMPTS.md` and `EXEC-PROMPTS.md` under the resolved backlog home)' "$SA"
pin "never-cited invariant dual-log span" grep -qF 'neither log is a backlog item and neither is ever cited as a plan' "$SA"
pin "ad-hoc completion evidence span" grep -qF "the run's own landing receipt" "$GU"
pin "adhoc kind enum extended append-only" grep -qF '"kind": "execute|author|audit|retriage|adhoc"' "$SF"
pin "PLAN-PROMPTS ad-hoc-superseded prune witness class" grep -qF 'ad-hoc-superseded' "$R"
pin "PLAN-PROMPTS freeze reopen ad-hoc case" grep -qF 'a freeze recorded for an ad-hoc run claim clears' "$R"
pin "EXEC-PROMPTS log exists" test -f "$X"
pin "EXEC-PROMPTS receipt delta named in the log header" grep -qF 'EXEC-PROMPTS-PRUNE: <slug> -> <landing commit>' "$X"
pin "investigate work-type verdict span" grep -qF 'work-type verdict' "$I"
pin "investigate stage 4 re-aimed self-check invocation" grep -qF 'check_investigate_entries.py --log' "$I"

[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

# --- two-mode loop policy Task 4 pins (plan
# docs/history/plans/completed/2026-10-06-two-mode-loop-policy.md, Task 4) ---
# Companion presence pins over the effort-policy rewrite and the integration
# joins: the Mode-coupled effort pairing marker (the rewritten overlay body's
# lead literal; the section heading pin above is unchanged), the overlay's
# ad-hoc child-marker catalog entry (the widened-arm ad-hoc marker's
# definition home), and the doing-code-review With-maintenance integration
# subsection (Validation item 6's ad-hoc join). Plain presence form per the
# Task 1 idiom (single-line homes; no count obligation), so a deleted span
# fails here.
RS="$repo/agents/skills/review-staging/SKILL.md"
DCR="$repo/agents/skills/doing-code-review/SKILL.md"
for f in "$RS" "$DCR"; do
  [ -f "$f" ] || { echo "missing $f"; fail=1; }
done
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }
pin "mode-coupled effort pairing marker" grep -qF 'Mode-coupled effort pairing:' "$Z"
pin "ad-hoc child marker catalog entry in overlay" grep -qF 'Ad-hoc child (added 2026-10-06' "$Z"
pin "ad-hoc child marker occupancy span in overlay" grep -qF "a prompt containing \`ad-hoc backlog lane\` plus the resolved repository root" "$Z"
pin "staging digest field present" grep -qF 'Source digest' "$RS"
pin "doing-code-review ad-hoc integration span" grep -qF 'ad-hoc backlog arm' "$DCR"

[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

# --- review scope / reflection policy pins (ADR-0006) ---
RP="$repo/agents/skills/review-plan/SKILL.md"
PA="$repo/agents/skills/review-agents/review-panel-selection.md"
PL="$repo/agents/skills/plans/SKILL.md"
EP="$repo/agents/skills/execute-plan/SKILL.md"
RL="$repo/agents/skills/review-loop/SKILL.md"
RS="$repo/agents/skills/review-staging/SKILL.md"
RR="$repo/agents/skills/receiving-review/SKILL.md"
for f in "$RP" "$PA" "$PL" "$EP" "$RL" "$RS" "$RR"; do
  [ -f "$f" ] || { echo "missing $f"; fail=1; }
done
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }
# plan-authoring-done-closeout: Phase 0 closeout-evidence establishment, the completion-claims boundary, and the stranded-input pre-pass
pin "plans Phase 0 establishment incompleteness boundary" grep -qF 'the worktree setup is incomplete until one of the two records exists' "$PL"
pin "plans completion-claims boundary names review-readiness evidence" grep -qF 'is review-readiness evidence, never completion evidence' "$PL"
pin "plans Final Step deferral arm byte-identical" grep -qF 'The user explicitly says "not yet" / "wait" / "I'"'"'ll commit myself"; honor that and stop.' "$PL"
pin "plans Final Step first-task-ownership deferral arm byte-identical" grep -qF 'say so and let `execute-plan` own the first commit' "$PL"
# Re-aimed 2026-10-19 (plan docs/history/plans/2026-10-14-skill-monolith-module-extraction.md Task 2): the needle's span moved verbatim to agents/skills/execute-plan/worktree-first.md.
pin "execute-plan stranded-input pre-pass routing literal" grep -qF 'stranded-input pre-pass' "$repo/agents/skills/execute-plan/worktree-first.md"
pin "review effort follows scope and complexity" grep -qF "Select review effort from the plan and changed work's scope and complexity" "$RP"
pin "shared panel policy has scope signals" grep -qF 'affected components and contracts, interactions' "$PA"
pin "review-plan later recurring checkpoints" grep -qF 'For example, a five-round interval reflects at rounds 5, 10, and 15' "$PL"
# Re-aimed 2026-10-14, arm re-aim beside provenance: the execute-plan copy of
# the interval-combining sentence was adapter-era prose deliberately removed by
# the certified landing e0d7d6961; the canonical carrier is
# agents/skills/plans/SKILL.md's convergence-telemetry item, reworded there to
# "need one reflection", and the pin follows that carrier's live bytes.
pin "recurring intervals combine once (plans carrier)" grep -qF 'Coincident total-round and full-panel intervals need one reflection' "$PL"
pin "review-loop delegates convergence to canonical plan-review policy" grep -qF 'Apply the convergence, reconciliation, and bounded self-heal decisions in `review-plan`’s Scope and complexity policy' "$RL"
pin "review-loop delegates self-heal decisions to review-plan" grep -qF 'that policy is the single owner of continuation and authorization decisions' "$RL"
# Removed 2026-10-14, arm remove-beside-provenance: the execute-plan copy of
# the single-owner delegation sentence was adapter-era prose deliberately
# removed by the certified landing e0d7d6961; the review-loop carrier stays
# pinned by the row above.
pin "panel choice uses the narrow-scope signal" grep -qF 'use a focused panel when work is demonstrably narrow' "$PA"
pin "panel choice preserves the risk-signal floor" grep -qF 'the risk-signal floor remains a minimum' "$PA"
pin "review-plan defines first-round blocker baseline" grep -qF 'When no prior blocker count exists, continue one review round to establish the trajectory baseline' "$RP"
pin "review-plan states the convergence predicate" grep -qF 'either the blocking count fell from the previous round or there are zero open blockers' "$RP"
pin "review-plan makes active churn override convergence" grep -qF 'Any active churn or recurrence trigger means non-convergence' "$RP"
pin "review-plan bounds self-heal and pauses after one failed alternative" grep -qF 'at most one concrete simplification or refactor attempt' "$RP"
pin "review-plan self-heal allowance is run-wide" grep -qF 'for the entire review run when the execution plan explicitly authorizes that attempt' "$RP"
pin "review-staging requires post-fence self-heal state" grep -qF 'filename and sidecar `date` are on or after `SELF_HEAL_STATE_MIN_DATE`' "$RS"
pin "review-staging records legacy resume disposition" grep -qF 'A missing, malformed, or legacy prior record on resume requires' "$RS"
pin "validator validates run-wide attempt carry-forward" grep -qF 'consumed or unknown self-heal state must carry forward unchanged within a run' "$repo/scripts/validate_review_staging.py"
# Hard-mode error count/order re-derivation (review-staging fail-fast
# iteration plan, Task 2): NONE found. Every validator pin below is a
# message-presence grep; no pin asserts exactly one hard-mode error, a
# pinned error count, or a pinned error order for validate_review_staging,
# and this script never invokes the validator CLI. The multi-error report
# order stays pinned by the validator's own embedded selftest
# (hard_mode_diagnostics arm), not here.
# Drift guard (Task 2 review fold; witness: the r1 pointer mapping that
# named a section not owning its field): every SKILL_CLAUSE_POINTERS section
# string, read from the live table, must remain a heading or inline mention
# in the review-staging skill, so a renamed section or a new mapping cannot
# silently leave hard-mode pointers aiming at nothing. Presence-grep pin
# class; review alongside the pointer table.
ptr_sections="$(python3 - "$repo/scripts/validate_review_staging.py" <<'PYEOF_PTR'
import re, sys
src = open(sys.argv[1], encoding="utf-8").read()
start = src.index("SKILL_CLAUSE_POINTERS: tuple")
end = src.index("\n)\n", start)
seen = []
for _marker, section in re.findall(r'\(\s*"([^"]+)",\s*"([^"]+)"\s*\)', src[start:end]):
    if section not in seen:
        seen.append(section)
print("\n".join(seen))
PYEOF_PTR
)"
[ -n "$ptr_sections" ] || { echo "PIN FAIL: clause-pointer table yielded no sections (parse drift)" >&2; exit 1; }
printf '%s\n' "$ptr_sections" | while IFS= read -r ptr_section; do
  grep -qF "$ptr_section" "$RS" || { echo "PIN FAIL: clause-pointer section missing from review-staging skill: $ptr_section" >&2; exit 1; }
done || exit 1
pin "validator binds consumption to current round and digest" grep -qF 'unused-to-consumed transition must bind to this round and its sidecar source_digest' "$repo/scripts/validate_review_staging.py"
pin "validator requires new r1 identity" grep -qF 'r1 must start a new run with unused or consumed state bound to its review-run-id' "$repo/scripts/validate_review_staging.py"
pin "validator rejects later-round allowance reset" grep -qF 'run_id cannot change after r1 in the same artifact chain' "$repo/scripts/validate_review_staging.py"
pin "validator iteratively validates prior chain" grep -qF 'validate_self_heal_attempt_state(' "$repo/scripts/validate_review_staging.py"
pin "validator rejects predecessor sidecar without valid digest" grep -qF 'predecessor sidecar source_digest must be a lowercase SHA-256' "$repo/scripts/validate_review_staging.py"
pin "validator tests pair missing and malformed predecessor digest recovery" grep -qF 'malformed predecessor digest requires unknown' "$repo/scripts/validate_review_staging.py" && grep -qF 'malformed predecessor digest rejects unused' "$repo/scripts/validate_review_staging.py" && grep -qF 'missing predecessor digest requires unknown' "$repo/scripts/validate_review_staging.py" && grep -qF 'missing predecessor digest rejects unused' "$repo/scripts/validate_review_staging.py"
pin "validator gates current self-heal state on calendar dates" grep -qF 'post-fence self-heal state requires calendar-valid filename and sidecar dates' "$repo/scripts/validate_review_staging.py"
pin "validator tests pair current invalid date outcomes" grep -qF '("invalid current filename date",' "$repo/scripts/validate_review_staging.py" && grep -qF '("invalid current sidecar date",' "$repo/scripts/validate_review_staging.py" && grep -qF 'f"{label} rejects unused"' "$repo/scripts/validate_review_staging.py" && grep -qF 'f"{label} rejects unknown"' "$repo/scripts/validate_review_staging.py"
pin "validator tests pair predecessor invalid date recovery" grep -qF 'calendar-invalid prior filename requires unknown' "$repo/scripts/validate_review_staging.py" && grep -qF 'calendar-invalid prior filename rejects unused' "$repo/scripts/validate_review_staging.py" && grep -qF 'calendar-invalid prior sidecar date requires unknown' "$repo/scripts/validate_review_staging.py" && grep -qF 'calendar-invalid prior sidecar date rejects unused' "$repo/scripts/validate_review_staging.py"
pin "validator catches corrupted earlier chain on resume" grep -qF 'self-heal resume: broken earlier chain rejects unused' "$repo/scripts/validate_review_staging.py"
pin "validator carries state across date rollover" grep -qF 'self-heal resume: stable state carries across date rollover' "$repo/scripts/validate_review_staging.py"
pin "validator rejects missing self-heal mint" grep -qF 'post-fence self-heal state requires a minted review-run-id' "$repo/scripts/validate_review_staging.py"
pin "staging contract permits unnumbered singleton r1" grep -qF 'An unnumbered canonical filename is a singleton r1' "$RS"
pin "staging contract binds predecessor lookup across dates" grep -qF 'so a chain can continue across calendar dates' "$RS"
pin "selection recognizes unnumbered singleton records" grep -qF 'an unnumbered legacy singleton is round 1' "$repo/scripts/review_record_selection.py"
pin "selection refuses duplicate round identities" grep -qF 'matching records contain ambiguous duplicate round number(s)' "$repo/scripts/review_record_selection.py"
pin "selection tests unnumbered singleton continuation" grep -qF 'test_select_reuses_unnumbered_singleton_as_round_one' "$repo/scripts/test_review_record_selection.py"
pin "review-plan records run-wide self-heal consumption" grep -qF 'the run-wide `self_heal_attempt` member' "$RP"
pin "review-plan defines consumed self-heal state" grep -qF '"status":"consumed","run_id":"<stable-run-id>","round":"rN","source_digest":"<sha256>"' "$RP"
pin "review-plan reads attempt state after resume" grep -qF 'A resumed post-fence workflow reads the latest value' "$RP"
pin "fixture distinguishes resume after consumed attempt" grep -qF '| G, resumed after attempt | Latest state is consumed' "$repo/scripts/review_policy_sample_contexts.md"
pin "fixture asserts strict churn threshold outcomes" grep -qF '2 of 4 does not trigger; 3 of 4 triggers reconciliation' "$repo/scripts/review_policy_sample_contexts.md"
pin "fixture asserts staged-total churn outcomes" grep -qF '4 to 3 does not trigger; 4 to 4 and 4 to 5 trigger reconciliation' "$repo/scripts/review_policy_sample_contexts.md"
pin "fixture asserts blocker churn outcomes" grep -qF '2 to 1 does not trigger; 2 to 2 triggers reconciliation' "$repo/scripts/review_policy_sample_contexts.md"
pin "review-loop quick prompt uses reflection checkpoints" grep -qF 'Reflect at every configured total-round and full-panel interval; intervals are checkpoints, not stop limits' "$RL"
expect_absent "review-loop quick prompt has no five-panel stop" 'Max 5 full-panel rounds' "$RL"
pin "fixture distinguishes exact half from greater than half" grep -qF '2 of 4 is exactly half' "$repo/scripts/review_policy_sample_contexts.md"
pin "fixture covers both staged finding trajectory directions" grep -qF '4 to 4 is flat; 4 to 5 increases' "$repo/scripts/review_policy_sample_contexts.md"
pin "fixture covers blocker trajectory boundary" grep -qF '2 to 2 stays positive and flat' "$repo/scripts/review_policy_sample_contexts.md"
pin "plans delegates churn self-heal to canonical plan-review rule" grep -qF 'Use the active mechanical-churn and recurrence triggers, convergence decisions, and bounded self-heal rule defined in `review-plan`' "$PL"
expect_absent "plans does not impose per-round blocker decrease" 'must reduce the nonnegative blocker count' "$PL"
pin "receiving-review recognizes explicit plan authorization" grep -qF 'the execution plan expressly authorizes' "$RR"
pin "review-loop reflects at every configured interval" grep -qF 'At every `max_review_rounds` total-round interval and every `max_full_panel_rounds` full-panel interval' "$RL"
pin "review-loop combines coincident interval reflections" grep -qF 'Coincident intervals share one reflection' "$RL"
pin "fixture covers the first-round blocker baseline" grep -qF 'Positive blockers; no prior blocker count and no churn or recurrence trigger' "$repo/scripts/review_policy_sample_contexts.md"
pin "fixture records the full recurring schedules" grep -qF 'Full-panel F3/F6/F9/F12/F15; total R5/R10/R15' "$repo/scripts/review_policy_sample_contexts.md"
expect_absent "project class does not resolve review strictness" 'project class resolver' "$PA"
for f in "$RP" "$PA" "$PL" "$EP" "$RL" "$RS" "$RR"; do
  expect_absent "project-class review resolver removed from $f" 'project class resolver' "$f"
  expect_absent "personal-only cap wording removed from $f" 'In a `personal`-class project' "$f"
done
expect_absent "personal-only review cap removed" 'personal projects' "$RL"
for f in "$RS" "$RR"; do
  [ -f "$f" ] || { echo "missing $f"; fail=1; }
done
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }
expect_absent "review-staging cap closure has no project-specific limit" 'personal projects' "$RS"
expect_absent "receiving-review cap closure has no project-specific limit" 'personal projects' "$RR"
expect_absent "cap-only stop removed" 'stop for user direction once the total reaches 5' "$RL"
expect_absent "cap-only reconciliation removed" 'A `max_full_panel_rounds` interval alone triggers reconciliation' "$RL"
expect_absent "execute-plan has no cap-only stop" 'stop for user direction once the total reaches 5' "$EP"
expect_absent "execute-plan has no cap-only reconciliation" 'interval alone triggers reconciliation' "$EP"
expect_absent "plans no longer stops before a sixth full-panel round" 'Before a sixth full-panel round, stop for user direction' "$PL"

# --- personal-project remote-boundary pointer pins (plan
# docs/history/plans/2026-10-17-personal-project-remote-boundary-enforcement.md, Task 3) ---
# Presence pins over the provider gate heading and the two drafted consumer
# pointer fragments, so a gate rename or a pointer deletion breaks the battery.
GPW="$repo/agents/skills/github-pr-workflow/SKILL.md"
DCR="$repo/agents/skills/doing-code-review/SKILL.md"
RR="$repo/agents/skills/receiving-review/SKILL.md"
for f in "$GPW" "$DCR" "$RR"; do
  [ -f "$f" ] || { echo "missing $f"; fail=1; }
done
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }
pin "remote-operation gate section anchored" grep -qF '## Project-scope and remote-operation gate' "$GPW"
pin "doing-code-review gate pointer wired" grep -qF 'Project-scope and remote-operation gate: on personal and pet projects it stops before remote access, and the operator alone handles remote operations.' "$DCR"
pin "receiving-review gate pointer wired" grep -qF 'Project-scope and remote-operation gate: on personal and pet projects it stops before remote access, leaving remote operations to the operator.' "$RR"

# --- review-loop-round-budget pins (plan 2026-10-09-review-loop-round-budget, Task 1) ---
# Count-gated pins for the plans-skill spans the same plan's Task 1 landed in
# the Plan Quality Gate. Each span below is unique-span whole-file (measured
# on the post-Task-1 tree: each occurs exactly once in the plans skill), so a
# count of exactly 1 fails both a deletion of that obligation and a stray
# duplicate copy. All ten spans sit on single physical lines in the target.
[ "$(grep -oF 'the full-panel budget is 2 full-panel rounds for a declared execution budget of 2 hours or less' "$PL" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "budget formula count" "PIN FAIL: budget formula count" || fail=1; }
[ "$(grep -oF 'extend the derived budget by a stated number of full-panel rounds, continue for one further full-panel round, or park and report; an unattended lane parks and reports' "$PL" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "budget breach-pause completion count" "PIN FAIL: budget breach-pause completion count" || fail=1; }
[ "$(grep -oF 'The round a classified round-launching fold triggers is a delta round' "$PL" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "delta-round sentence count" "PIN FAIL: delta-round sentence count" || fail=1; }
[ "$(grep -oF 'Only a semantic plan change (an unclassified or operator-acked delta under the same classifier arm) reopens a whole-plan panel' "$PL" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "delta-round semantic-reopen completion count" "PIN FAIL: delta-round semantic-reopen completion count" || fail=1; }
[ "$(grep -oF 'Only whole-plan-scope rounds count as full-panel rounds' "$PL" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "counting-rule sentence count" "PIN FAIL: counting-rule sentence count" || fail=1; }
[ "$(grep -oF "the certification round considers blocking findings only; its non-blocking findings are recorded in the terminal record's overflow section" "$PL" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "certification-residual routing sentence count" "PIN FAIL: certification-residual routing sentence count" || fail=1; }
[ "$(grep -oF 'the backlog row is the only durable copy of a consequence-bearing residual' "$PL" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "certification-residual capture-homes completion count" "PIN FAIL: certification-residual capture-homes completion count" || fail=1; }
[ "$(grep -oF 'the row-by-row verification that every consequence-bearing certification residual carries its durable backlog row' "$PL" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "reflection-paragraph growth sentence count" "PIN FAIL: reflection-paragraph growth sentence count" || fail=1; }
[ "$(grep -oF 'per-round validation runs at lint level' "$PL" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "lint-split sentence count" "PIN FAIL: lint-split sentence count" || fail=1; }
[ "$(grep -oF 'the round-close full-gate precondition and the execution and finalization boundaries keep their existing full readiness validators' "$PL" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "lint-split boundary-retention completion count" "PIN FAIL: lint-split boundary-retention completion count" || fail=1; }

# --- review-loop-round-budget review-plan mirror pins (same plan, Task 2) ---
RP2="$repo/agents/skills/review-plan/SKILL.md"
[ -f "$RP2" ] || { echo "missing $RP2"; fail=1; }
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }
[ "$(grep -oF "The full-panel round budget derives from the plan's declared execution budget per the plans skill's Plan Quality Gate budget formula" "$RP2" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "review-plan budget-by-reference sentence count" "PIN FAIL: review-plan budget-by-reference sentence count" || fail=1; }
[ "$(grep -oF "at certification, non-blocking findings are recorded in the terminal record's overflow section with durable backlog capture and never force a re-round or a plan fold" "$RP2" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "review-plan certification-residual routing sentence count" "PIN FAIL: review-plan certification-residual routing sentence count" || fail=1; }
[ "$(grep -oF 'extend the derived budget by a stated number of full-panel rounds, continue for one further full-panel round, or park and report; an unattended lane parks and reports' "$RP2" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "review-plan pause-mechanics sentence count" "PIN FAIL: review-plan pause-mechanics sentence count" || fail=1; }
[ "$(grep -oF 'run the lint-level `--preflight` pass and resolve its findings' "$RP2" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "review-plan lint-split sentence count" "PIN FAIL: review-plan lint-split sentence count" || fail=1; }
[ "$(grep -oF 'subordinated to the validation-level partition per review-staging'"'"'s record-validation-levels subsection' "$RP2" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "review-plan standing-mandate subordination sentence count" "PIN FAIL: review-plan standing-mandate subordination sentence count" || fail=1; }
[ "$(grep -oF 'The operator-authorization requirement applies at the configured round cap and at full-panel budget breach alike, the closure mechanics byte-identical' "$RP2" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "review-plan rule-8 trigger-extension sentence count" "PIN FAIL: review-plan rule-8 trigger-extension sentence count" || fail=1; }

# --- review-loop-round-budget review-loop and review-staging pins (same plan, Task 3) ---
RL3="$repo/agents/skills/review-loop/SKILL.md"
RS3="$repo/agents/skills/review-staging/SKILL.md"
for f in "$RL3" "$RS3"; do
  [ -f "$f" ] || { echo "missing $f"; fail=1; }
done
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }
[ "$(grep -oF "the full-panel budget derives from it per the plans skill's Plan Quality Gate budget formula and breach pauses the loop for operator direction per review-plan's Scope and complexity policy duty" "$RL3" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "review-loop Limits budget sentence count" "PIN FAIL: review-loop Limits budget sentence count" || fail=1; }
[ "$(grep -oF 'delta (focused) rounds never consume the full-panel counter and the whole-plan review scope, not the panel roster, decides the full-panel count' "$RL3" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "review-loop plan-scoped counting-rule sentence count" "PIN FAIL: review-loop plan-scoped counting-rule sentence count" || fail=1; }
[ "$(grep -oF 'intermediate rounds run the lint-level `--preflight` pass over the staging pair with the same source context and resolve its findings before the round'"'"'s triage and counter decisions are consumed' "$RL3" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "review-loop mechanical-gate split sentence count" "PIN FAIL: review-loop mechanical-gate split sentence count" || fail=1; }
[ "$(grep -oF 'count a full-panel round only when the round'"'"'s scope is the whole plan (plan-scoped loops)' "$RL3" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "review-loop rule-3 post-fold scope-key sentence count" "PIN FAIL: review-loop rule-3 post-fold scope-key sentence count" || fail=1; }
[ "$(grep -oF '### Record validation levels' "$RS3" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "review-staging record-validation-levels subsection heading count" "PIN FAIL: review-staging record-validation-levels subsection heading count" || fail=1; }
[ "$(grep -oF 'a round that could record the certifying clean verdict (any fresh-adversarial round with zero staged unresolved blocking findings, and any round in doubt) runs the full `--hard` source-context gate' "$RS3" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "review-staging round-class gate-selection sentence count" "PIN FAIL: review-staging round-class gate-selection sentence count" || fail=1; }
[ "$(grep -oF 'a code-family loop that terminates without certifying rests on a lint-only record' "$RS3" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "review-staging ledger lint-only-record sentence count" "PIN FAIL: review-staging ledger lint-only-record sentence count" || fail=1; }
[ "$(grep -oF 'the fill-order step-6 `--hard` sentence above is subordinated to this partition' "$RS3" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "review-staging fill-order subordination sentence count" "PIN FAIL: review-staging fill-order subordination sentence count" || fail=1; }
[ "$(grep -oF 'its Source digest is the SHA-256 of the post-fold whole plan bytes (recording compatibly with `scripts/review_record_selection.py`'"'"'s differing-digest new-round path), the fold-diff scope is named in the Selection reason, and `panel_mode` stays focused' "$RS3" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "review-staging delta-round recording rule count" "PIN FAIL: review-staging delta-round recording rule count" || fail=1; }
[ "$(grep -oF 'never enter the soften watchlist, whose fix-keyed shape and closure obligations stay untouched' "$RS3" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "review-staging certification-residual routing note count" "PIN FAIL: review-staging certification-residual routing note count" || fail=1; }

# --- review-loop-round-budget execute-plan pins (same plan, Task 4) ---
EP4="$repo/agents/skills/execute-plan/SKILL.md"
[ -f "$EP4" ] || { echo "missing $EP4"; fail=1; }
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }
# Removed 2026-10-14, arm remove-beside-provenance: the tracking-line
# derivation sentence and the increment-rule scope-key sentence in
# execute-plan SKILL.md were adapter-era prose deliberately removed by the
# certified landing e0d7d6961; the literals survive only in the frozen owning
# completed plan docs/history/plans/completed/2026-10-09-review-loop-round-budget.md.
# The amended end-condition row below stays pinned (its span is live).
[ "$(grep -oF "The full-panel round budget derives from the plan's declared execution budget (plans without a declared line keep the flat default 3); delta (focused) rounds never consume it; breach pauses the loop for operator direction per review-plan's Scope and complexity policy pause duty and its breach mechanics before another full-panel round" "$EP4" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "execute-plan amended end-condition row count" "PIN FAIL: execute-plan amended end-condition row count" || fail=1; }

# --- cross-task trace sweep pins (plan 2026-10-13-plan-review-cross-task-lifecycle, Task 2) ---
# Count-gated pins for the two clauses the same plan's Task 1 landed in the
# plans skill's claim-to-task ownership sweep bullet (the cross-task trace
# sweep). Each span below is unique-span whole-file (measured on the
# post-Task-1 tree: each occurs exactly once in the plans skill), so a count
# of exactly 1 fails both a deletion of that clause and a stray duplicate
# copy. Both spans sit on the sweep bullet's single physical line in the
# target.
[ "$(grep -oF 'its evidence owner, a measurable closure condition, and evidence sources that each trace to an explicit task output' "$PL" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "cross-task sweep Ship-when evidence-trace clause count" "PIN FAIL: cross-task sweep Ship-when evidence-trace clause count" || fail=1; }
[ "$(grep -oF 'an explicit em-dash scan and a public-hygiene scan (files mode, repository root set) for each scoped non-Markdown path' "$PL" | wc -l | tr -d ' ')" -eq 1 ] || { recorded_red_check "cross-task sweep validation scan clause count" "PIN FAIL: cross-task sweep validation scan clause count" || fail=1; }

# --- authoring gist report paths, scoped to their owning sections ---
python3 - "$S" "$repo/agents/skills/maintenance/template-authoring.md" "$repo/agents/skills/plans/SKILL.md" <<'PY_CHECK' | route_heredoc_stream
from pathlib import Path
import sys
skill, templates, plans = map(lambda value: Path(value).read_text(), sys.argv[1:])
authoring_gist = skill.split("### Authoring plan gist reports", 1)[1].split("### Stop-promotion criterion", 1)[0]
cycle = skill.split("## Cycle gate (durable pacing between cycles)", 1)[1].split("## Loop modes", 1)[0]
# Re-aimed 2026-10-14, arm re-aim beside provenance: the authoring-gist
# requirement sentence was reworded by the maintenance-skill-size-refactor
# landing 12b9f028e (the section now points at plans/SKILL.md's source and
# budget rules instead of restating them); the pin follows the live sentence.
if "Before the first `review-plan` round, report the plan title, five-line gist (`Title`, `TLDR`, `Before`, `After`, `Edge cases`), and execution budget using `agents/skills/plans/SKILL.md`'s source and budget rules." not in authoring_gist:
    print("PIN FAIL: in-session and scheduled authoring both emit gist and budget before first review")
    raise SystemExit(1)
if "This extends **Cycle gate**: that resumed-turn readiness report cannot define the separate pre-review and authoring-closeout emissions." not in authoring_gist:
    print("PIN FAIL: gist report section names its parent and admission rationale")
    raise SystemExit(1)
# Re-aimed 2026-10-14, arm re-aim beside provenance: the readiness, final,
# and in-session-closeout gist emissions were reworded by later landings
# (the readiness and final-report sentences restructured, the in-session
# closeout emission folded into the authoring-gist section's repeat rule, and
# the advisory clause stated once); the checks follow the live sentences.
if "Repeat the gist and budget in readiness, final, and in-session closeout reports." not in authoring_gist:
    print("PIN FAIL: in-session authoring closeout includes the gist and budget")
    raise SystemExit(1)
for label, phrase in (
    ("final report includes the gist and budget", "Include that same gist and budget in the final report."),
    ("Cycle gate readiness and final reports include the gist and budget", "When reporting Cycle gate readiness, include the plan title, the five-line gist (Title, TLDR, Before, After, Edge cases), and the declared execution budget for the authored plan"),
    ("Cycle gate gist and budget are advisory", "This content is advisory only and never blocks a lane or stops the loop (directive D-6 remains intact)."),
    ("Cycle gate points to the canonical gist and budget mapping", "follow the source mapping and budget rules in `agents/skills/plans/SKILL.md`."),
):
    if phrase not in cycle:
        print(f"PIN FAIL: {label}")
        raise SystemExit(1)
author = templates
for label, phrase in (
    ("scheduled authoring emits gist before first review", "Before launching the plan's first `review-plan` round"),
    ("scheduled authoring includes title and five gist fields", "five-line gist (Title, TLDR, Before, After, Edge cases)"),
    ("scheduled authoring repeats the gist and budget in its final report", "Include the same gist and budget in the final report."),
    ("scheduled authoring gist is advisory", "it never blocks a lane or stops the loop (directive D-6 remains intact)."),
):
    if phrase not in author:
        print(f"PIN FAIL: {label}")
        raise SystemExit(1)
plan_quality = plans.split("## Plan Quality Gate", 1)[1].split("## ", 1)[0]
for label, phrase in (
    ("in-session plan-created pre-review transition emits title, gist, and budget", "After the plan file is created and before launching its first `review-plan` round, report the plan title, the five-line gist, and its declared execution budget."),
    ("in-session authoring closeout repeats the gist and budget", "Repeat the same gist and budget in the in-session authoring closeout report."),
    ("plans gist fields and explicit source mapping are defined", "The five lines are `Title`, `TLDR`, `Before`, `After`, and `Edge cases`: use the plan title; the required `TLDR:` line in `Gist & Examples`; matching `Before`/`After` entries there (or `none stated` if absent); and explicitly named edge cases or named-boundary handling (or `none stated`)."),
    ("plans budget is verbatim or undeclared", "Report the declared execution budget verbatim, or `undeclared` when the plan has no execution budget declaration."),
    ("plans gist and budget remain advisory", "This material is advisory only: it never blocks a lane or stops the loop (directive D-6 remains intact)."),
):
    if phrase not in plan_quality:
        print(f"PIN FAIL: {label}")
        raise SystemExit(1)
print("authoring gist report path pins: all hold")
PY_CHECK
heredoc_settle "${PIPESTATUS[0]}"

# --- stop promotion, scoped to its owning section ---
python3 - "$S" <<'PY_CHECK' | route_heredoc_stream
from pathlib import Path
import sys
skill = Path(sys.argv[1]).read_text()
section = skill.split("### Stop-promotion criterion", 1)[1].split("## Loop modes", 1)[0]
for label, phrase in (
    ("activation contract and approval required", "No stop activates without a separate, explicitly approved and landed activation contract naming its owner, authoritative witness, activation action, and reader."),
    ("criterion links its owning backlog", "[promotion-threshold activation backlog](../../../docs/history/backlog/2026-10-10-promotion-threshold-activation-contract.md)"),
):
    if phrase not in section:
        print(f"PIN FAIL: {label}")
        raise SystemExit(1)
print("stop promotion pins: all hold")
PY_CHECK
heredoc_settle "${PIPESTATUS[0]}"
[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }
echo "maintenance pins: all hold"

# --- placement pins (placement-closing-doctrine-enforcement plan, Task 4) ---
# WARNING-ONLY pin family over the placement doctrine spans in the four
# placement-decision owners (execute-plan, done, maintenance, plans skills):
# one dedicated fixed-string grep per span, a missing span printing a
# FAIL-format line naming it and the first missing span named in the summary.
# The section never sets fail and never moves the suite's exit code; the
# summary line is the assertion (machinery admission protocol: warning-only
# landing). It coexists with the primary-resolution stand-down pins above,
# which count-gate their own spans through the blocking pin helper.
# Admission (machinery protocol): incident 9a046452e (an oversized behavior-bearing direct landing past the direct-commit class, witnessed 2026-10-16, plus five-day worktree residue); catch frequency: every pins run over skill text edits; false-positive cost: a legitimate rewording trips a pin until the pin list is updated in the same change; sunset: review after the first true catch.
PLACEMENT_MISSING=""
PD="$repo/agents/skills/done/SKILL.md"
placement_pin() { # placement_pin <file> <span>: warning-only presence grep, never touches fail
  local f="$1" span="$2" disp
  disp="${f#"$repo"/}" # repo-relative display path; the grep still runs on the absolute path
  if ! grep -qF -- "$span" "$f"; then
    echo "PIN FAIL: placement pin: $span ($disp)"
    if [ -z "$PLACEMENT_MISSING" ]; then PLACEMENT_MISSING="$span ($disp)"; fi
  fi
}
# Re-aimed 2026-10-19 (plan docs/history/plans/2026-10-14-skill-monolith-module-extraction.md Task 2): the needle's span moved verbatim to agents/skills/execute-plan/worktree-first.md.
placement_pin "$repo/agents/skills/execute-plan/worktree-first.md" "outside the two spelled forms"
placement_pin "$repo/agents/skills/execute-plan/worktree-first.md" "immediate-commit rule"
# Re-aimed 2026-10-20 (plan docs/history/plans/2026-10-19-done-immediate-commit-single-homing.md Task 1): the removed full-rule wording is not restored; the pin guards the done skill's retained by-name reference to the immediate-commit rule owned by the Worktree-first standard.
placement_pin "$PD" "immediate-commit rule"
placement_pin "$PD" "editing no tracked corpus and committing nothing"
placement_pin "$PD" "dangling session-owned work product"
# Re-aimed 2026-10-20 (plan docs/history/plans/2026-10-19-done-immediate-commit-single-homing.md Task 1): the threshold fragment alone under-pins the advisory; the pin now guards a distinctive span within the advisory's cumulative-diff measurement clause.
placement_pin "$PD" "measures the session's cumulative diff of its own committed changes"
# Re-aimed 2026-10-19 (plan docs/history/plans/2026-10-14-skill-monolith-module-extraction.md Task 2): the needle's span moved verbatim to agents/skills/execute-plan/worktree-first.md.
placement_pin "$repo/agents/skills/execute-plan/worktree-first.md" "Delete only after verification"
placement_pin "$repo/agents/skills/execute-plan/worktree-first.md" "before any worktree removal, migrate the run"
# dispatch-isolation span: the grep -q form over the short fragment plus the
# full span count-gated exactly 1, so a stray duplicate copy also fails
if ! grep -qF "per-execution ad-hoc worktrees per the Worktree-first standard" "$S" \
   || [ "$(grep -cF "execution children run in per-execution ad-hoc worktrees per the Worktree-first standard (isolation landed 2026-09-24, P57)" "$S" | tr -d ' ')" -ne 1 ]; then
  echo "PIN FAIL: placement pin: dispatch-isolation span (agents/skills/maintenance/SKILL.md)"
  if [ -z "$PLACEMENT_MISSING" ]; then PLACEMENT_MISSING="dispatch-isolation span (agents/skills/maintenance/SKILL.md)"; fi
fi
# Re-aimed 2026-10-19 (plan docs/history/plans/2026-10-14-skill-monolith-module-extraction.md Task 1): the span lives in rule 29, moved verbatim to agents/skills/plans/validation-authoring-rules.md.
placement_pin "$repo/agents/skills/plans/validation-authoring-rules.md" "relocation-digest correction"
if [ -z "$PLACEMENT_MISSING" ]; then
  echo "placement pins: all hold"
else
  echo "placement pins: first missing span: $PLACEMENT_MISSING"
fi

# changelog-extraction plan (Task 1): the deviation list moved byte-verbatim to
# templates-CHANGELOG.md, so the deviation-paraphrase must-not-carry protection
# gains twins over the moved copy (the operative-file checks below stay
# unchanged; no check deleted, no count loosened)
expect_absent "superseded fixed-form blueprint parenthetical must be absent from the templates changelog" '(its title, its cadence cron, recurring true, enabled true, its prompt template with {REPO_ROOT} filled)' "$PTCL"
expect_absent "superseded parent_automation_id-only re-arm closing must be absent from the templates changelog" 'then update "parent_automation_id" as a targeted field edit' "$PTCL"
expect_absent "superseded fire-time sentence must be absent from the templates changelog" 'never inside a deferred window' "$PTCL"
expect_absent "superseded unscoped success-via-existing clause must be absent from the templates changelog" 'counts as success only after one more listing confirms an ENABLED automation with that title and prompt opening is present; on that success-via-existing path' "$PTCL"
expect_absent "superseded listing-driven rearm wording must be absent from the templates changelog" 'list once more immediately before the create' "$PTCL"
expect_absent_flat "retired unblock pre-landing capture literal must be absent from the templates changelog (wrap-tolerant)" 'UNBLOCK_PRE_TIP' "$PTCL"
expect_absent_flat "retired execution worktree create literal must be absent from the templates changelog (wrap-tolerant)" 'git worktree add -b <execution-branch> <sibling-path> <default-branch>' "$PTCL"
expect_absent_flat "retired authoring worktree create literal must be absent from the templates changelog (wrap-tolerant)" 'git worktree add -b YYYY-MM-DD-authoring-<slug> <sibling-path> <default-branch>' "$PTCL"
expect_absent_flat "retired authoring payload worktree create literal must be absent from the templates changelog (wrap-tolerant)" 'git worktree add -b <date>-authoring-<slug> <sibling-path> <default-branch>' "$PTCL"
expect_absent_flat "retired authoring pathspec-arm staging command must be absent from the templates changelog (wrap-tolerant)" 'git add -- <paths>' "$PTCL"

# --- skill-text byte-budget gate (maintenance-skill-size-refactor plan, Task 2) ---
# Advisory wiring: the gate runs --check on every pins-suite invocation and its
# report prints here; WARNING-ONLY by the machinery admission protocol (a breach
# line never moves this suite's exit code at this landing). Admission fields:
# concrete incident = the 35-commit/one-shrink ratchet and the ~89K-token
# per-turn doctrine load (the measured analysis
# docs/maintenance/maintenance-skill-refactor-analysis-2026-10-09.md); expected
# catch frequency = one breach line on any landing that grows a file past its
# cap; false-positive cost = zero blocking (fail-open, bounded by the seeded
# margin). Promotion path: blocking exit 1 only after the gate's first true
# catch, promoted by a later change.
BUDGET_REPORT="$(python3 "$repo/scripts/skill_text_budget.py" --check 2>&1)"
BUDGET_RC="$?"
# The budget helper's own OUTCOME_CONTRACT line stays inside its report; the
# suite's emission funnel owns the run's one final OUTCOME line, so the echo
# filters it (the red baseline's first checkpoint used to exit before this
# echo ran, which is why the leak stayed dormant until the green baseline).
printf '%s\n' "$BUDGET_REPORT" | grep -v '^OUTCOME:' || true
if [ "$BUDGET_RC" -ne 0 ]; then
  recorded_red_check "skill-text budget gate did not run reliably (exit ; a tool_error is a wiring failure, never advisory)" "PIN FAIL: skill-text budget gate did not run reliably (exit $BUDGET_RC; a tool_error is a wiring failure, never advisory)" || fail=1
fi



# --- router-integrity pins (maintenance-skill-size-refactor plan, Task 3) ---
# every router dispatch pointer names an existing module file, each named
# module carries its step heading verbatim, and the router's frontmatter
# name:/description: lines are byte-unchanged; a later edit that renames or
# drops a module fails the suite instead of stranding a pointer
python3 - "$S" "$repo/agents/skills/maintenance" <<'PYRTR' | route_heredoc_stream
import re, sys
from pathlib import Path
router_text = open(sys.argv[1]).read()
mdir = Path(sys.argv[2])
name_line = [l for l in router_text.splitlines() if l.startswith("name:")]
desc_line = [l for l in router_text.splitlines() if l.startswith("description:")]
if len(name_line) != 1 or len(desc_line) != 1:
    print("PIN FAIL: router frontmatter name:/description: lines drifted"); sys.exit(1)
expected = {
    "survey-arms.md": "### Step 1: survey",
    "guards.md": "### Step 2: guards (fixed order)",
    "decisions.md": "### Step 3: decision",
    "quota-policy.md": "### Step 4: quota leg",
    "scheduling.md": "### Step 5: scheduling",
    "state-file.md": "## State file",
    "failure-cap.md": "## Failure detection and the failure cap",
}
pointers = set(re.findall(r"agents/skills/maintenance/([a-z-]+\.md)", router_text))
for mod, heading in sorted(expected.items()):
    path = mdir / mod
    if not path.is_file():
        print("PIN FAIL: router names module %s which does not exist" % mod); sys.exit(1)
    if mod not in pointers and mod != "failure-cap.md" and mod != "state-file.md":
        # failure-cap and state-file are reachable through the failure-cap
        # bullet and Step 6 entry naming them; verify by membership below
        pass
for mod in sorted(pointers):
    if not (mdir / mod).is_file():
        print("PIN FAIL: router pointer names missing module %s" % mod); sys.exit(1)
if not {"survey-arms.md", "guards.md", "decisions.md", "quota-policy.md", "scheduling.md", "state-file.md"} <= pointers:
    print("PIN FAIL: router dispatch table does not name every module: %s" % sorted(pointers)); sys.exit(1)
for mod, heading in sorted(expected.items()):
    if heading not in (mdir / mod).read_text():
        print("PIN FAIL: module %s lost its verbatim heading %s" % (mod, heading)); sys.exit(1)
PYRTR
heredoc_settle "${PIPESTATUS[0]}"

# --- recorded-red consult selftest (red-on-main-baseline-repair-and-auto-demote, Task 3) ---
# Permanent regression net over the consult's live bytes: the scenario
# runner extracts the consult block from THIS file (from the
# SUPPRESSED_NAMES funnel seed through the consult end marker) into a bash
# subshell against a mktemp fixture register addressed through
# PINS_RECORDED_RED_REGISTER, so the reader-to-lookup-to-check-to-funnel
# chain is exercised exactly as deployed. Asserted arms: suppression
# (helper form and count-gated form), expiry, unrecorded (register lacking
# the guard key), summary at a checkpoint-style funnel exit, malformed
# review-by, corrupt register (tool_error exit 3), strict-prefix collision
# exact-equality, duplicates last-row-wins with an expired row shadowed,
# control-character stripping, the heredoc router's
# all-suppressed-settles-clean arm, and the as-of clock override (a review-by
# equal to the as-of date stays live, the day before expires, and a
# non-calendar override tool-errors). No mid-suite checkpoint is added; the
# assertions set fail=1 and the suite's final gate funnels them.
CONSULT_SELFTEST_FIXTURE="$(mktemp -d "${TMPDIR:-/tmp}/pins-recorded-red-selftest.XXXXXX")"
CONSULT_BLOCK="$(sed -n '/^SUPPRESSED_NAMES=""$/,/^# --- recorded-red consult end/p' "$0")"
[ -n "$CONSULT_BLOCK" ] || { echo "PIN FAIL: recorded-red consult selftest could not extract the live consult block"; fail=1; }
printf '%s\n' "$CONSULT_BLOCK" > "$CONSULT_SELFTEST_FIXTURE/consult-block.sh"
consult_scenario() { # consult_scenario <fixture-register> <scenario body>; prints the scenario's combined output
  SCENARIO_BODY="$2" SCENARIO_BLOCK="$CONSULT_SELFTEST_FIXTURE/consult-block.sh" PINS_RECORDED_RED_REGISTER="$1" PINS_RECORDED_RED_AS_OF="${PINS_RECORDED_RED_AS_OF:-}" bash -c '
set -u
. "$SCENARIO_BLOCK"
eval "$SCENARIO_BODY"
' 2>&1
}
if [ -n "$CONSULT_BLOCK" ]; then
  # suppression arm, helper form: a stub pin helper over a recorded unexpired red
  printf '%s' '{"schema":1,"window":{},"guards":{"check_maintenance_pins":{"notes":"","rows":[{"kind":"override","date":"2026-10-14","evidence":"selftest","note":"pin: stub-alpha review-by: 2999-01-01 witness selftest"}]}}}' > "$CONSULT_SELFTEST_FIXTURE/reg.json"
  SC_OUT="$(consult_scenario "$CONSULT_SELFTEST_FIXTURE/reg.json" "
load_recorded_reds || { emit_outcome tool_error; exit 3; }
pin() { local d=\"\$1\"; shift; if \"\$@\" >/dev/null 2>&1; then return 0; fi; recorded_red_check \"\$d\" \"PIN FAIL: \$d\" || fail=1; return 0; }
fail=0
pin \"stub-alpha\" false
emit_outcome pass
exit 0
")"
  if ! printf '%s\n' "$SC_OUT" | grep -q '^PIN RECORDED RED (recorded 2026-10-14, review-by 2999-01-01): stub-alpha$' \
     || printf '%s\n' "$SC_OUT" | grep -q '^PIN FAIL: stub-alpha$' \
     || ! printf '%s\n' "$SC_OUT" | grep -q '^PIN RECORDED REDS SUPPRESSED THIS RUN: stub-alpha$' \
     || [ "$(printf '%s\n' "$SC_OUT" | grep -c '^OUTCOME:' | tr -d ' ')" != "1" ] \
     || [ "$(printf '%s\n' "$SC_OUT" | tail -n 1)" != "OUTCOME: pass" ]; then
    echo "PIN FAIL: recorded-red consult selftest: suppression arm (helper form)"; fail=1
  fi
  # suppression arm, count-gated form: stable name decoupled from the rendered count-bearing text
  SC_OUT="$(consult_scenario "$CONSULT_SELFTEST_FIXTURE/reg.json" "
load_recorded_reds || { emit_outcome tool_error; exit 3; }
fail=0
recorded_red_check \"stub-alpha\" \"PIN FAIL: stub-alpha span count 0 != 1\" && fail=9
emit_outcome pass
exit 0
")"
  if ! printf '%s\n' "$SC_OUT" | grep -q '^PIN RECORDED RED (recorded 2026-10-14, review-by 2999-01-01): stub-alpha$' \
     || ! printf '%s\n' "$SC_OUT" | grep -q '^PIN RECORDED REDS SUPPRESSED THIS RUN: stub-alpha$' \
     || [ "$(printf '%s\n' "$SC_OUT" | grep -c '^OUTCOME:' | tr -d ' ')" != "1" ]; then
    echo "PIN FAIL: recorded-red consult selftest: suppression arm (count-gated form)"; fail=1
  fi
  # expiry arm
  printf '%s' '{"schema":1,"window":{},"guards":{"check_maintenance_pins":{"notes":"","rows":[{"kind":"override","date":"2026-09-01","evidence":"selftest","note":"pin: stub-alpha review-by: 2020-01-01 witness selftest"}]}}}' > "$CONSULT_SELFTEST_FIXTURE/reg.json"
  SC_OUT="$(consult_scenario "$CONSULT_SELFTEST_FIXTURE/reg.json" "
load_recorded_reds || { emit_outcome tool_error; exit 3; }
fail=0
recorded_red_check \"stub-alpha\" \"PIN FAIL: stub-alpha\" && fail=9
emit_outcome fail
exit 0
")"
  if ! printf '%s\n' "$SC_OUT" | grep -q '^PIN RECORDED RED EXPIRED (recorded 2026-09-01, review-by 2020-01-01): stub-alpha$' \
     || ! printf '%s\n' "$SC_OUT" | grep -q '^PIN FAIL: stub-alpha$' \
     || [ "$(printf '%s\n' "$SC_OUT" | tail -n 1)" != "OUTCOME: fail" ]; then
    echo "PIN FAIL: recorded-red consult selftest: expiry arm"; fail=1
  fi
  # unrecorded arm: the register omits the guard key entirely
  printf '%s' '{"schema":1,"window":{},"guards":{"other-guard":{"notes":"","rows":[]}}}' > "$CONSULT_SELFTEST_FIXTURE/reg.json"
  SC_OUT="$(consult_scenario "$CONSULT_SELFTEST_FIXTURE/reg.json" "
load_recorded_reds || { emit_outcome tool_error; exit 3; }
fail=0
recorded_red_check \"stub-alpha\" \"PIN FAIL: stub-alpha\" && fail=9
emit_outcome fail
exit 0
")"
  if printf '%s\n' "$SC_OUT" | grep -q 'RECORDED RED' \
     || ! printf '%s\n' "$SC_OUT" | grep -q '^PIN FAIL: stub-alpha$' \
     || [ "$(printf '%s\n' "$SC_OUT" | tail -n 1)" != "OUTCOME: fail" ]; then
    echo "PIN FAIL: recorded-red consult selftest: unrecorded arm (absent guard key)"; fail=1
  fi
  # summary-at-checkpoint arm: one suppressed red plus one unrecorded failing pin
  printf '%s' '{"schema":1,"window":{},"guards":{"check_maintenance_pins":{"notes":"","rows":[{"kind":"override","date":"2026-10-14","evidence":"selftest","note":"pin: stub-alpha review-by: 2999-01-01 witness selftest"}]}}}' > "$CONSULT_SELFTEST_FIXTURE/reg.json"
  SC_OUT="$(consult_scenario "$CONSULT_SELFTEST_FIXTURE/reg.json" "
load_recorded_reds || { emit_outcome tool_error; exit 3; }
fail=0
recorded_red_check \"stub-alpha\" \"PIN FAIL: stub-alpha\"
recorded_red_check \"stub-live\" \"PIN FAIL: stub-live\" && fail=1
emit_outcome fail
exit 0
")"
  if ! printf '%s\n' "$SC_OUT" | grep -q '^PIN RECORDED REDS SUPPRESSED THIS RUN: stub-alpha$' \
     || ! printf '%s\n' "$SC_OUT" | grep -q '^PIN FAIL: stub-live$' \
     || [ "$(printf '%s\n' "$SC_OUT" | grep -c '^OUTCOME:' | tr -d ' ')" != "1" ] \
     || [ "$(printf '%s\n' "$SC_OUT" | tail -n 1)" != "OUTCOME: fail" ]; then
    echo "PIN FAIL: recorded-red consult selftest: summary at the checkpoint funnel exit"; fail=1
  fi
  # malformed arm: a non-calendar review-by is treated as not recorded, one loud advisory
  printf '%s' '{"schema":1,"window":{},"guards":{"check_maintenance_pins":{"notes":"","rows":[{"kind":"override","date":"2026-10-14","evidence":"selftest","note":"pin: stub-alpha review-by: 2026-13-45 witness selftest"}]}}}' > "$CONSULT_SELFTEST_FIXTURE/reg.json"
  SC_OUT="$(consult_scenario "$CONSULT_SELFTEST_FIXTURE/reg.json" "
load_recorded_reds || { emit_outcome tool_error; exit 3; }
fail=0
recorded_red_check \"stub-alpha\" \"PIN FAIL: stub-alpha\" && fail=1
emit_outcome fail
exit 0
")"
  if ! printf '%s\n' "$SC_OUT" | grep -q 'PIN RECORDED RED MALFORMED (treated as not recorded): stub-alpha' \
     || ! printf '%s\n' "$SC_OUT" | grep -q '^PIN FAIL: stub-alpha$'; then
    echo "PIN FAIL: recorded-red consult selftest: malformed review-by arm"; fail=1
  fi
  # corrupt-register arm: a garbage fixture register tool-errors with exit 3
  printf '%s' 'not json at all {{{' > "$CONSULT_SELFTEST_FIXTURE/reg.json"
  SC_OUT="$(consult_scenario "$CONSULT_SELFTEST_FIXTURE/reg.json" "
load_recorded_reds || { emit_outcome tool_error; exit 3; }
exit 0
")"
  if [ "$(printf '%s\n' "$SC_OUT" | tail -n 1)" != "OUTCOME: tool_error" ] \
     || ! printf '%s\n' "$SC_OUT" | grep -q 'unreadable or unparseable at .*/reg.json'; then
    echo "PIN FAIL: recorded-red consult selftest: corrupt register arm"; fail=1
  fi
  # collision arm: a strict-prefix pair, each name suppressed only by its own row's dates
  printf '%s' '{"schema":1,"window":{},"guards":{"check_maintenance_pins":{"notes":"","rows":[{"kind":"override","date":"2026-01-01","evidence":"selftest","note":"pin: retriage adjudication precedence review-by: 2998-01-01 witness selftest"},{"kind":"override","date":"2026-02-02","evidence":"selftest","note":"pin: retriage adjudication precedence exactly-once review-by: 2999-02-02 witness selftest"}]}}}' > "$CONSULT_SELFTEST_FIXTURE/reg.json"
  SC_OUT="$(consult_scenario "$CONSULT_SELFTEST_FIXTURE/reg.json" "
load_recorded_reds || { emit_outcome tool_error; exit 3; }
fail=0
recorded_red_check \"retriage adjudication precedence\" \"PIN FAIL: x\"
recorded_red_check \"retriage adjudication precedence exactly-once\" \"PIN FAIL: y\"
emit_outcome pass
exit 0
")"
  if ! printf '%s\n' "$SC_OUT" | grep -q '^PIN RECORDED RED (recorded 2026-01-01, review-by 2998-01-01): retriage adjudication precedence$' \
     || ! printf '%s\n' "$SC_OUT" | grep -q '^PIN RECORDED RED (recorded 2026-02-02, review-by 2999-02-02): retriage adjudication precedence exactly-once$'; then
    echo "PIN FAIL: recorded-red consult selftest: strict-prefix collision arm"; fail=1
  fi
  # duplicates arm: two matching rows, one expired and one future, the future row wins
  printf '%s' '{"schema":1,"window":{},"guards":{"check_maintenance_pins":{"notes":"","rows":[{"kind":"override","date":"2026-01-01","evidence":"selftest","note":"pin: stub-dup review-by: 2020-01-01 witness selftest"},{"kind":"override","date":"2026-03-03","evidence":"selftest","note":"pin: stub-dup review-by: 2999-03-03 witness selftest"}]}}}' > "$CONSULT_SELFTEST_FIXTURE/reg.json"
  SC_OUT="$(consult_scenario "$CONSULT_SELFTEST_FIXTURE/reg.json" "
load_recorded_reds || { emit_outcome tool_error; exit 3; }
fail=0
recorded_red_check \"stub-dup\" \"PIN FAIL: x\" || fail=9
emit_outcome pass
exit 0
")"
  if ! printf '%s\n' "$SC_OUT" | grep -q '^PIN RECORDED RED (recorded 2026-03-03, review-by 2999-03-03): stub-dup$' \
     || ! printf '%s\n' "$SC_OUT" | grep -q '^PIN RECORDED REDS SUPPRESSED THIS RUN: stub-dup$'; then
    echo "PIN FAIL: recorded-red consult selftest: duplicates last-row-wins arm"; fail=1
  fi
  # control-character arm: a note payload with a control character stays single-line and stripped
  printf '%s' '{"schema":1,"window":{},"guards":{"check_maintenance_pins":{"notes":"","rows":[{"kind":"override","date":"2026-10-14","evidence":"selftest","note":"pin: stub-ctrl review-by: 2999-01-01 witness a\u0007b"}]}}}' > "$CONSULT_SELFTEST_FIXTURE/reg.json"
  SC_OUT="$(consult_scenario "$CONSULT_SELFTEST_FIXTURE/reg.json" "
load_recorded_reds || { emit_outcome tool_error; exit 3; }
fail=0
recorded_red_check \"stub-ctrl\" \"PIN FAIL: x\" || fail=9
emit_outcome pass
exit 0
")"
  if [ "$(printf '%s\n' "$SC_OUT" | grep -c '^PIN RECORDED RED ' | tr -d ' ')" != "1" ] \
     || ! printf '%s\n' "$SC_OUT" | grep -q '^PIN RECORDED RED (recorded 2026-10-14, review-by 2999-01-01): stub-ctrl$'; then
    echo "PIN FAIL: recorded-red consult selftest: control-character stripping arm"; fail=1
  fi
  # heredoc-router arm: an all-suppressed block settles clean, a mixed one fails
  SC_OUT="$(consult_scenario "$CONSULT_SELFTEST_FIXTURE/reg.json" "
load_recorded_reds || { emit_outcome tool_error; exit 3; }
fail=0
printf 'PIN FAIL: stub-ctrl\n' | route_heredoc_stream
heredoc_settle 1
[ \"\$fail\" -eq 0 ] || { echo 'PIN FAIL: all-suppressed heredoc block must settle clean'; exit 7; }
printf 'PIN FAIL: stub-ctrl\nPIN FAIL: stub-live\n' | route_heredoc_stream
heredoc_settle 1
[ \"\$fail\" -eq 1 ] || { echo 'PIN FAIL: mixed heredoc block must fail'; exit 7; }
emit_outcome pass
exit 0
")"
  if printf '%s\n' "$SC_OUT" | grep -q '^PIN FAIL: .*heredoc block' \
     || ! printf '%s\n' "$SC_OUT" | grep -q '^PIN RECORDED REDS SUPPRESSED THIS RUN: stub-ctrl; stub-ctrl$'; then
    echo "PIN FAIL: recorded-red consult selftest: heredoc router arm"; fail=1
  fi
  # as-of clock arm (plan docs/history/plans/2026-10-20-plan-prompts-prune-range-content-inventory.md, Task 2):
  # an explicit PINS_RECORDED_RED_AS_OF pins the evaluation clock for selftests
  # while production keeps the system date; with as-of 2026-10-20 a review-by
  # of 2026-10-20 stays live (expired means strictly before the as-of date) and
  # a review-by of 2026-10-19 is expired; both outcomes asserted
  printf '%s' '{"schema":1,"window":{},"guards":{"check_maintenance_pins":{"notes":"","rows":[{"kind":"override","date":"2026-09-20","evidence":"selftest","note":"pin: stub-asof-live review-by: 2026-10-20 witness selftest"},{"kind":"override","date":"2026-09-20","evidence":"selftest","note":"pin: stub-asof-expired review-by: 2026-10-19 witness selftest"}]}}}' > "$CONSULT_SELFTEST_FIXTURE/reg.json"
  SC_OUT="$(PINS_RECORDED_RED_AS_OF=2026-10-20 consult_scenario "$CONSULT_SELFTEST_FIXTURE/reg.json" "
load_recorded_reds || { emit_outcome tool_error; exit 3; }
fail=0
recorded_red_check \"stub-asof-live\" \"PIN FAIL: stub-asof-live\" || fail=9
recorded_red_check \"stub-asof-expired\" \"PIN FAIL: stub-asof-expired\" && fail=9
emit_outcome fail
exit 0
")"
  if ! printf '%s\n' "$SC_OUT" | grep -q '^PIN RECORDED RED (recorded 2026-09-20, review-by 2026-10-20): stub-asof-live$' \
     || ! printf '%s\n' "$SC_OUT" | grep -q '^PIN RECORDED RED EXPIRED (recorded 2026-09-20, review-by 2026-10-19): stub-asof-expired$' \
     || ! printf '%s\n' "$SC_OUT" | grep -q '^PIN FAIL: stub-asof-expired$' \
     || [ "$(printf '%s\n' "$SC_OUT" | tail -n 1)" != "OUTCOME: fail" ]; then
    echo "PIN FAIL: recorded-red consult selftest: as-of clock override arm"; fail=1
  fi
  # malformed as-of arm: a set but non-calendar override tool-errors instead of
  # silently falling back to the system date
  SC_OUT="$(PINS_RECORDED_RED_AS_OF=not-a-calendar-date consult_scenario "$CONSULT_SELFTEST_FIXTURE/reg.json" "
load_recorded_reds || { emit_outcome tool_error; exit 3; }
exit 0
")"
  if [ "$(printf '%s\n' "$SC_OUT" | tail -n 1)" != "OUTCOME: tool_error" ]; then
    echo "PIN FAIL: recorded-red consult selftest: malformed as-of override arm"; fail=1
  fi
fi
rm -rf "$CONSULT_SELFTEST_FIXTURE"

# --- routed-heredoc wiring guard (execution review r1 fold): the pipe must
# precede any trailing comment - everything after an unquoted # is comment
# text, so a line like `cmd <<'D' # note | route_heredoc_stream` dead-wires
# the block and its failures bypass the shared suppression check entirely
# (12 sites shipped that way before this guard). The searched literal is
# split across two strings so this guard line cannot match itself.
[ "$(grep -c "^[^#].*#.*| route_""heredoc_stream" "$0" | tr -d ' ')" -eq 0 ] || { recorded_red_check "routed heredoc pipe dead-wired after a trailing comment" "PIN FAIL: routed heredoc pipe dead-wired after a trailing comment" || fail=1; }

# --- prompt-log prune-range pins (plan docs/history/plans/2026-10-20-plan-prompts-prune-range-content-inventory.md, Task 2) ---
# WARNING-ONLY pin family over the landed prune-range clauses: full-range
# inventory, slug and origin binding, per-origin coverage, target refusal,
# partial scope, freeze retention, one final receipt, lock lifecycle, receipt
# preservation, and audit separation, across the two rolling logs and the five
# operative procedures. One dedicated fixed-string grep per clause span; a
# missing clause prints one PIN WARN line naming it and the first missing
# clause is named in the summary. The section never sets fail and never moves
# the suite's exit code (machinery admission protocol: warning-only landing).
# Admission: incident docs/history/backlog/2026-10-15-plan-prompts-prune-end-anchor-overreach.md
# (the 2026-10-19 neighboring-receipt loss at a correctly anchored range tail);
# expected catch frequency: uncommon (the family evaluates on every pins run over a log-rule or procedure edit);
# false-positive cost: one non-blocking warning until the pin list is updated
# in the same change; review due 2027-01-20; promotion requires a production
# true catch and a pre-registered registry-removal row naming sunset and
# promotion criteria.
PRUNE_RANGE_MISSING=""
prune_range_pin() { # prune_range_pin <file> <span>: warning-only presence grep, never touches fail
  local f="$1" span="$2" disp
  disp="${f#"$repo"/}" # repo-relative display path; the grep still runs on the absolute path
  if ! grep -qF -- "$span" "$f"; then
    echo "PIN WARN: prune-range pin: $span ($disp)"
    if [ -z "$PRUNE_RANGE_MISSING" ]; then PRUNE_RANGE_MISSING="$span ($disp)"; fi
  fi
}
# PLAN-PROMPTS.md owns the shared Prune, Coverage and removal, Freeze, and Write boundary rules.
prune_range_pin "$repo/docs/history/backlog/PLAN-PROMPTS.md" 'Every prune first reads the target entry through its actual next heading (never assumed adjacency) and inventories every receipt line in that range before any deletion'
prune_range_pin "$repo/docs/history/backlog/PLAN-PROMPTS.md" 'every pre-existing receipt line stays byte-for-byte and in its original order regardless of slug'
prune_range_pin "$repo/docs/history/backlog/PLAN-PROMPTS.md" 'so a landing or monitor prune removes only covered origin bullets and their explicitly paired scope arms'
prune_range_pin "$repo/docs/history/backlog/PLAN-PROMPTS.md" "The separate pending-change audit (warning-only detection of prompt-log changes no landing has recorded) is out of this rule's scope: it stays report-only under its own backlog row."
prune_range_pin "$repo/docs/history/backlog/PLAN-PROMPTS.md" 'exactly one heading whose `Frozen:` witness names the plan'\''s authoring claim, whose `Origins:` includes the plan'\''s source backlog origin, and whose slug equals the canonical feature slug (the plan filename minus its leading date prefix)'
prune_range_pin "$repo/docs/history/backlog/PLAN-PROMPTS.md" "a collateral entry is covered only where the closeout's read-only origin discovery reports an origin removed inside the landing range"
prune_range_pin "$repo/docs/history/backlog/PLAN-PROMPTS.md" 'an ordinary monitor origin is covered only when a plan in the plans root or its `completed/` twin carries a `Backlog origin:` line exactly equal to that origin path, entry-slug discovery covering only the origin that plan itself names and never any other `Origins:` bullet'
prune_range_pin "$repo/docs/history/backlog/PLAN-PROMPTS.md" 'an ad-hoc origin (either log) is covered only when its entry was frozen before its recorded ad-hoc landing commit'
prune_range_pin "$repo/docs/history/backlog/PLAN-PROMPTS.md" 'A partial removal (origins remain) deletes only covered origin bullets and their paired scope arms, keeps the unresolved origins dispatchable, and adds no receipt'
prune_range_pin "$repo/docs/history/backlog/PLAN-PROMPTS.md" 'the `Frozen:` mark stays while any retained origin has a live claim or worktree (a fresh check over the retained origins, never the landing plan'\''s own authoring claim) and clears only after landing when that check finds none'
prune_range_pin "$repo/docs/history/backlog/PLAN-PROMPTS.md" 'Full removal (the heading empties) writes exactly one receipt using the last removed origin'\''s class and witness in the original `Origins:` order'
prune_range_pin "$repo/docs/history/backlog/PLAN-PROMPTS.md" 'Ambiguous origin-to-scope pairing or missing, duplicate, or shared binding evidence (duplicate own-entry headings included) leaves that target byte-identical with the reason reported; other independent targets stay eligible, and the log stays unchanged when no target qualifies.'
prune_range_pin "$repo/docs/history/backlog/PLAN-PROMPTS.md" 'a landing that removes only some of the entry'\''s origins keeps or clears the mark per the `Coverage and removal rule`'\''s freeze-retention clause'
prune_range_pin "$repo/docs/history/backlog/PLAN-PROMPTS.md" 'acquires or reuses the primary done lock, then the repo-wide merge lock (the repository'\''s `scripts/done-lock.sh` lock families), before any staging or index write and before the final log read, holding both through the commit and failure recovery'
prune_range_pin "$repo/docs/history/backlog/PLAN-PROMPTS.md" 'the write refuses when a pre-staged delta already exists on its owned paths, stages and commits only those owned paths, and on commit failure unstages and verifies only its own staged delta before release'
prune_range_pin "$repo/docs/history/backlog/PLAN-PROMPTS.md" 'Done-lock acquisition failure does no work'
prune_range_pin "$repo/docs/history/backlog/PLAN-PROMPTS.md" 'merge-lock acquisition failure releases the done lock token-fenced and does no work'
prune_range_pin "$repo/docs/history/backlog/PLAN-PROMPTS.md" 'Release is merge then done on every exit, attempting the done release even when the merge release fails'
prune_range_pin "$repo/docs/history/backlog/PLAN-PROMPTS.md" 'A session working from a worktree keys the primary done lock from primary-checkout context (the Phase 0 freeze included)'
prune_range_pin "$repo/docs/history/backlog/PLAN-PROMPTS.md" 'worktree branch commits stay isolated under the existing merge-lock guard, and no new lock is added'
# EXEC-PROMPTS.md carries the ad-hoc log's operation-specific deltas.
prune_range_pin "$repo/docs/history/backlog/EXEC-PROMPTS.md" 'receipt line per fully removed entry, a partial removal adding none'
prune_range_pin "$repo/docs/history/backlog/EXEC-PROMPTS.md" 'every pre-existing `EXEC-PROMPTS-PRUNE` receipt line stays byte-for-byte and in order'
prune_range_pin "$repo/docs/history/backlog/EXEC-PROMPTS.md" 'an EXEC-PROMPTS origin is covered only when its entry was frozen before its recorded ad-hoc landing commit, a full removal cites that commit as the witness'
prune_range_pin "$repo/docs/history/backlog/EXEC-PROMPTS.md" 'the `Coverage and removal rule`'\''s freeze-retention clause applies by label'
# plans/SKILL.md: the landing closeout prune clause (by label) and the Phase 0 freeze write.
prune_range_pin "$repo/agents/skills/plans/SKILL.md" 'the landing pruning only its own dispatch entry plus discovery-listed collateral served entries under the log'\''s `Coverage and removal rule` label'
prune_range_pin "$repo/agents/skills/plans/SKILL.md" 'the prune evaluated per the log'\''s `Prune rule` and `Coverage and removal rule` labels (range inventory, per-origin coverage, partial narrowing with freeze retention, the single full-removal receipt, receipt preservation, and target refusal are that rule'\''s, not restated here)'
prune_range_pin "$repo/agents/skills/plans/SKILL.md" 'The freeze write is a primary-checkout log write under the log'\''s `Write boundary rule` label in `docs/history/backlog/PLAN-PROMPTS.md` (lock order, owned-path staging, and recovery live there), the primary done lock keyed from primary-checkout context per that rule'
prune_range_pin "$repo/agents/skills/plans/SKILL.md" 'on any lock refusal the session releases each acquired lock, removes only this session'\''s claim file through the AUTHORING CLAIM procedure'\''s ownership-checked delete, and stands down before any plan-file work'
# template-authoring.md: the authoring landing closeout prune clause (by label) and its collateral delta.
prune_range_pin "$repo/agents/skills/maintenance/template-authoring.md" 'the prune evaluated per the log'\''s `Coverage and removal rule` label, this run'\''s own entry being the one whose `Frozen:` witness names this plan'\''s authoring claim'
prune_range_pin "$repo/agents/skills/maintenance/template-authoring.md" 'this closeout'\''s collateral delta being that a collateral entry retaining a served origin is a partial removal that keeps that origin'\''s scope arm and adds no receipt'
# decisions.md: the monitor's rolling prompt log duties (by label) and the monitor's lock-refusal delta.
prune_range_pin "$repo/agents/skills/maintenance/decisions.md" 'each monitor prune is evaluated per the log'\''s `Prune rule` and `Coverage and removal rule` labels (range inventory, per-origin coverage including the ordinary-monitor exact `Backlog origin:` match, partial narrowing with freeze retention, the single full-removal receipt, receipt preservation, and target refusal live there)'
prune_range_pin "$repo/agents/skills/maintenance/decisions.md" 'the same `Coverage and removal rule` applying to EXEC-PROMPTS.md by label'
prune_range_pin "$repo/agents/skills/maintenance/decisions.md" 'each write that commits runs under the log'\''s `Write boundary rule` label, this monitor'\''s delta being that a lock refusal leaves both logs byte-identical with the write deferred and the reason recorded'
# zcode.md: the monitor lock primitives, their primary-checkout keying, and the token-fenced release order.
prune_range_pin "$repo/agents/skills/maintenance/zcode.md" 'run under the log'\''s `Write boundary rule` label in `docs/history/backlog/PLAN-PROMPTS.md`; the concrete primitives'
prune_range_pin "$repo/agents/skills/maintenance/zcode.md" 'run from primary-checkout context so the done key resolves to the primary worktree'
prune_range_pin "$repo/agents/skills/maintenance/zcode.md" 'a worktree session addresses the primary checkout through an explicit-rooted form, never its own worktree'\''s key'
prune_range_pin "$repo/agents/skills/maintenance/zcode.md" 'release token-fenced as `merge-release-repo`, then `release-repo`'
prune_range_pin "$repo/agents/skills/maintenance/zcode.md" 'an acquisition refusal defers the write per the monitor duty (the monitor never rewrites a log to recover a refused write)'
# worktree-first.md: the primary-placement commit class, its lock refusal, and the landing closeout prune (by label).
prune_range_pin "$repo/agents/skills/execute-plan/worktree-first.md" 'a primary-placement commit that writes a rolling prompt log, the Phase 0 freeze included, is the log'\''s `Write boundary rule` write'
prune_range_pin "$repo/agents/skills/execute-plan/worktree-first.md" 'a lock refusal standing the write down with the log unchanged'
prune_range_pin "$repo/agents/skills/execute-plan/worktree-first.md" 'evaluated per the log'\''s shared `Coverage and removal rule` label'
prune_range_pin "$repo/agents/skills/execute-plan/worktree-first.md" 'that receipt counting fully removed entries only'
# Missing-clause probe, the family's own warning path run in this shell so fail is observed directly:
# a scratch file lacking the probed span must draw exactly one PIN WARN line while fail stays untouched,
# and the probe's warn never enters the family summary (PRUNE_RANGE_MISSING is restored). A probe that
# does not warn is a broken warner, a suite defect, hence the PIN FAIL (machinery selftest, never clause content).
prune_range_probe_file="$(mktemp "${TMPDIR:-/tmp}/prune-range-probe.XXXXXX")"
prune_range_probe_out="$(mktemp "${TMPDIR:-/tmp}/prune-range-probe-out.XXXXXX")"
printf '%s\n' 'unrelated text only' > "$prune_range_probe_file"
prune_range_missing_saved="$PRUNE_RANGE_MISSING"; prune_range_fail_before="$fail"
prune_range_pin "$prune_range_probe_file" 'clause deliberately absent from the probe file' > "$prune_range_probe_out"
PRUNE_RANGE_MISSING="$prune_range_missing_saved"
if [ "$(grep -c '^PIN WARN: prune-range pin: clause deliberately absent from the probe file' "$prune_range_probe_out" | tr -d ' ')" -ne 1 ] || [ "$fail" != "$prune_range_fail_before" ]; then
  echo "PIN FAIL: prune-range pins selftest: missing-clause probe did not warn exactly once with fail untouched"; fail=1
fi
rm -f "$prune_range_probe_file" "$prune_range_probe_out"
if [ -z "$PRUNE_RANGE_MISSING" ]; then
  echo "prune-range pins: all hold"
else
  echo "prune-range pins: first missing clause: $PRUNE_RANGE_MISSING"
fi

[ "$fail" -eq 1 ] && { emit_outcome fail; exit 1; }

emit_outcome pass
exit 0
