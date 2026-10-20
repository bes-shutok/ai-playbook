# Plan: Usage-wall governing probe before timed resume

Backlog origin: `docs/history/backlog/2026-10-19-usage-wall-probe-before-timed-resume.md`
Driving force: efficiency
Plan review record: the staging series `.ai-playbook/reviews/2026-10-20-plan-review-usage-wall-probe-before-timed-resume-p1efc0bd2-r*.md` (the highest rN for this source-plan path is authoritative)
Execution budget: 1.0h total, largest task 0.5h

Authoring claim: docs/tmp/authoring-claims/2026-10-19-usage-wall-probe-before-timed-resume.md (session sess_873419a5-2730-4102-8f8f-5159d119a3fa)

## Terms

- **Usage wall:** a provider refusal whose error text names a reset time an hour or more away (the runtime usage limit); the class a pause arms a timed resume carrier for.
- **Hardened probe:** one cheap, trivial sub-agent dispatch used as the wall's only oracle; clean means the dispatch completes without a usage-wall refusal, refused means the wall refuses the dispatch.
- **Governing probe:** the hardened probe a paused lane runs before its armed timed resume carrier would govern the resume; one dispatch per run, at the pause boundary and again at any later turn the lane receives while the pause stands.
- **Pause boundary:** the moment the pause protocol has armed the carrier and written its record, immediately before the lane settles idle.
- **Timed resume carrier:** the scheduled one-shot automation (or launchd one-shot) a pause arms at the wall's nominal reset to resume the lane; the pause's own carrier.
- **Pause record:** the `budget_pause` record the budget-gate pause paragraph appends to the round's staging doc (or to session notes at loop start).
- **Resolution line:** the line added to the pause record when a clean probe lifts the pause, naming the clean probe and the carrier deletion.
- **Pause protocol:** the budget-gate pause procedure's schedule-first, record, and report arms.
- **Self-lift:** the wall ending on its own before the nominal reset, so a refusal recorded at an earlier boundary no longer reflects the live wall; only a later probe observes it.
- **Duplicate-in-waiting:** an armed carrier whose lane already resumed in-session; left armed, it races the resumed lane's claims and the merge lock.
- **Maintenance overlay:** `agents/skills/maintenance/zcode.md`, the runtime overlay carried inside the maintenance skill.
- **Usage-wall doctrine:** the maintenance overlay's Quota-wall dispatch refusals sentence (the two-class split and its one hardened probe).
- **D-13:** the operator directive "usage-wall restarts follow the quota-wall dispatch doctrine" in `docs/maintenance/operator-directives.md`; it routes the usage-wall class to the usage-wall doctrine by name.
- **One-probe rule:** the usage-wall doctrine's rule that a usage-wall boundary spends one hardened probe, never the remaining budget's probes.
- **Budget-gate pause paragraph:** the review-loop skill paragraph that runs the quota probe and, on pause, the pause protocol.
- **Budget gate:** the execute-plan skill's quota-window pause and resume section, the canonical pause protocol home; this plan does not edit it.
- **Weekly secondary window:** the weekly secondary quota binding, which stays report-only in the pause protocol (no flag, no carrier, user decision).
- **Lane:** the agent session or work thread the pause protocol pauses and resumes; the subject every probe boundary governs.
- **Dispatching entry:** the `docs/history/backlog/PLAN-PROMPTS.md` entry `usage-wall-probe-before-timed-resume` whose scope arms this plan implements (design input, distinct from the Backlog origin row it cites).

## Why

A usage-wall pause arms its timed resume carrier at the wall's nominal reset and rides it unconditionally. Twice witnessed this week, the wall had already self-lifted well before that reset, so a resumable lane sat idle for hours while its armed carrier waited to fire over it as a duplicate. The governing probe, run at the pause boundary and again at any later turn the still-paused lane receives, decides each boundary correctly in both directions.

## Gist & Examples

TLDR: add a governing probe to the usage-wall pause protocol, so a wall that self-lifted early resumes the lane in-session instead of stranding it until the nominal reset, for efficiency.

**Before (today):** a lane paused on a usage-wall refusal at 15:19 arms a resume carrier for 18:05 (nominal reset 17:53:54) and goes idle. Nothing probes at the pause boundary or at any later turn the paused lane receives: a wall that had already self-lifted keeps the lane idle until the carrier fires, the lane loses about two hours plus a fresh-session re-derivation handoff, and the firing carrier races the lane's claims and the merge lock if the work was resumed first by anyone else.

**After (this plan):** the same pause arms the same carrier and writes the same record, then runs the governing probe once at the pause boundary before settling idle. A clean probe there lifts the pause in-session immediately: the pause record gains a resolution line, the lane deletes its own armed carrier as its owner, and the lane continues at its recorded next step. A refused probe leaves the carrier untouched, and the arm stays live: at any later turn the still-paused lane receives (the witnessed 15:56 case, 1h58m before the reset), the lane runs the governing probe again before continuing, so a wall that self-lifted late still resumes in-session and the owner deletes the carrier before it can fire as a duplicate.

**Edge cases:** a refused probe leaves the carrier's fire time and payload unchanged and schedules nothing (no timer, watcher, or polling loop; the next probe runs only when a boundary arrives on its own); a pause with no scheduled carrier (the weekly secondary window) runs no governing probe; the boundary where the wall refused keeps the doctrine's one hardened probe, so the later pause-boundary probes are not second probes at that boundary; the Budget gate section and its plans-skill mirror are not edited.

## Outcome

A usage-wall pause resolves at the wall's real state instead of its nominal reset.

- A lane whose governing probe runs clean, at the pause boundary or at any later turn it receives while the pause stands, resumes in-session immediately, records the resolution, and deletes its own armed carrier.
- A lane whose governing probe is refused keeps its timed resume carrier exactly as scheduled, and the arm stays live for the next boundary without any timer or polling.
- The two homes state the same semantics, so neither contradicts the other.

Gate delta: one protocol arm added to the pause protocol (the governing probe at the pause's resume boundaries, before a fired-armed carrier; prose-only; no gate, validator, lock, ledger, or schema field added or removed), priced by the completed failure the Backlog origin records (the 2026-10-19 pause stranded its lane about two idle hours and left the armed carrier a duplicate-in-waiting over the resumed lane; second witness the 2026-10-17 arm note); no refusal class, check, or field removed, and the arm supersedes no existing arm.

## Assumptions

- assume the two edit homes are the budget-gate pause paragraph (`agents/skills/review-loop/SKILL.md`) and the maintenance overlay's usage-wall doctrine sentence (`agents/skills/maintenance/zcode.md`, Dispatch discipline bullet); basis: the dispatching entry's scope arms and the Backlog origin's Ask.
- assume D-13 is not edited: its directive line routes the usage-wall class to the usage-wall doctrine by name, so the amended doctrine carries the arm; basis: the D-13 directive line in `docs/maintenance/operator-directives.md`.
- assume the governing probe is one trivial sub-agent dispatch per run, not a quota-script read; basis: the origin Ask's wording and its finding that the refusal string is the wall's only oracle.
- assume the probe runs at the pause boundary (after the carrier is armed and the record written, before the lane settles idle) and again at any later turn the still-paused lane receives while the pause stands, one dispatch per run, with no timer, watcher, or polling loop and a refused probe scheduling nothing; basis: the origin Ask's "before any timed resume carrier fires" placement plus its two witnesses (the 2026-10-17 arm note shows a wall already lifted at arm time, and the 2026-10-19 witness shows a wall that lifted 37 minutes after the pause armed, which only a later boundary can observe).
- assume the stale home-pointer clause inside the usage-wall doctrine sentence (it cites the execute-plan Sub-Agent Launch Rules block that commit e0d7d6961 removed on 2026-10-12) is out of scope: pre-existing drift no origin arm names, and this plan inserts beside that clause without rewriting it; basis: the git history of `agents/skills/execute-plan/SKILL.md`.
- assume the Budget gate section and the plans-skill Budget gate mirror stay byte-identical; basis: the dispatching entry's scope arms name exactly the two homes above.

Decision points requiring a grill: none remain.

## Standing constraints

- Land the rule, not the story: neither home carries incident narrative, dates, or witness quotes; the Backlog origin holds the story.
- Text-only: no new gate, validator, lock, ledger, schema field, or state file in either home.

## Evaluation Criteria

**Quality dimensions:**
- correctness (cross-home consistency): both homes state the same clean-probe outcome (in-session resume, resolution line, owner-deleted carrier, continuation at the recorded next step) and the same refused-probe outcome (carrier untouched, fire time and payload unchanged, nothing scheduled); each inserted sentence is unique in its file.
- faithfulness: each arm matches the dispatching entry's scope arms, including the unchanged schedule-first, record, and report arms and the unchanged one-probe rule.
- readability: every plan- or project-specific term used from Why through Evaluation Criteria resolves in Terms.
- text discipline: each home's operative text grows by one arm of at most three sentences, with no incident dates or witness narrative entering the prescribed insertions.

**Done when:**
- the governing-probe arm is present at both prescribed anchors, and the full Validation Commands block exits 0.
- the preserved-arms anchor spans in both files are still present exactly once each.
- the later-turn scenario holds as written: given a pause whose pause-boundary probe was refused (carrier armed for 18:05) and a later turn reaching the still-paused lane at 15:56, the arm's text expects the lane to run the governing probe again before continuing, so a clean probe records the resolution line and deletes the carrier before the 18:05 fire, and a refused probe leaves the carrier standing.
- the near-fire scenario holds as written: given a later-turn governing probe still in flight when the carrier's recorded fire time arrives, the arm's text expects the lane to abandon the probe (recorded in the pause record) and leave the fired carrier's own session as the sole resume path.
- `bash scripts/check-no-em-dash.sh touched` and `bash scripts/scan-public-hygiene.sh` exit 0 over the changed set, and `bash scripts/check_maintenance_pins.sh` shows no failure beyond its recorded pre-existing baseline (the Validation block models the carve-out).

**Ship when:**
- the change lands through the plan's normal review-certified landing; no external release condition exists.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Documentation:**
- `agents/skills/review-loop/SKILL.md` (the budget-gate pause paragraph only; every other line of the file is frozen)
- `agents/skills/maintenance/zcode.md` (the usage-wall doctrine sentence at the end of the Dispatch discipline bullet only; every other line of the file is frozen, including the stale home-pointer clause earlier in that sentence)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/maintenance/operator-directives.md`; reason: D-13 routes the usage-wall class to the usage-wall doctrine by name; no origin arm edits the directive file.
- `agents/skills/execute-plan/SKILL.md` and `agents/skills/plans/SKILL.md`; reason: the Budget gate section and its plans-skill mirror are not among the dispatching entry's two homes and stay byte-identical.
- the stale home-pointer clause inside the usage-wall doctrine sentence in `agents/skills/maintenance/zcode.md`; reason: pre-existing drift (the pointed-to execute-plan block was removed by commit e0d7d6961 on 2026-10-12) that no origin arm names; recorded in Assumptions.

## Validation Commands

Scope and polarity: the block runs from any working directory inside the repository (it re-derives the root itself), takes one optional stage argument (`interim1` for Task 1's mid-point, default `all`), aborts on the first miss, and never relies on `set -e`. Every pin is a fixed-string match against one of the two edited files, never against this plan (the plan's own quotes of those spans are the prescribed snippets, not stale references).

Authoring-time evidence (rule 19 RED-today and rule 22 audit, recorded 2026-10-20 in the authoring worktree at main 93fff300b, re-executed after the r1, r2, and r3 folds): the eleven section 1 pins and the twelve section 3 spans occur zero times in their target files today, so the battery is RED-today and its first actually-failing gate is the section 1 opening pin (exit 1); each flips GREEN exactly when its task lands. Every section 2 and section 4 preserved-arms pin occurs exactly once in its target file today (regression guards checked against current bytes per the rule 22 mirror carve-out). `check-no-em-dash.sh touched` and `scan-public-hygiene.sh` exit 0 over the unchanged tree today, and `check_maintenance_pins.sh` exits 1 on exactly one recorded pre-existing baseline failure (provenance per rule 39: the pin "clocked-order consult verify-successor leg", an orphaned needle for a span relocated out of `agents/skills/maintenance/survey-arms.md` by a later landing, present on main at 93fff300b and at the primary checkout before this plan; any other `PIN FAIL` line is a failure). Every section 1 and section 3 pin other than the two adjacency pins (the last of each set, each spanning the join between the insertion's edge and its neighboring preserved span) appears verbatim inside its owning task's prescribed insertion text (verified per owning snippet; three spans occur in both insertions), and the interim1 stage was executed in both polarities after the r2 fold (RED on the untouched tree at its section 1 opening pin; GREEN after a simulated faithful Task 1 insertion extracted from the prescribed span, then restored); the r3 fold re-verified RED-today for every pin and both adjacency pins' constructibility from the prescribed joins.

Round-start state for rN: recorded per round in the staging series; the certification wall of record is the seal file `.ai-playbook/review-certs/usage-wall-probe-before-timed-resume.md`.

```bash
#!/usr/bin/env bash
# Fail-closed battery over the two edited homes.
# Usage: run the whole block with no argument (final), or with the argument
# interim1 at Task 1's mid-point (section 3 must then still be absent).
set -u
STAGE="${1:-all}"
REPO="$(git rev-parse --show-toplevel)" || { echo "VALIDATION FAIL: not inside a repository" >&2; exit 1; }
cd "$REPO" || exit 1
fail() { echo "VALIDATION FAIL: $1" >&2; exit 1; }
RL="agents/skills/review-loop/SKILL.md"
ZC="agents/skills/maintenance/zcode.md"
test -f "$RL" || fail "missing $RL"
test -f "$ZC" || fail "missing $ZC"
expect_once() {
  local file="$1" span="$2" n rc
  n="$(set -o pipefail; grep -oF -- "$span" "$file" | wc -l | tr -d ' ')"; rc=$?
  if [ "$rc" -ge 2 ]; then fail "grep tool error (rc $rc) on $file"; fi
  [ "$n" -eq 1 ] || fail "expected exactly 1 occurrence in $file, got $n: $span"
}
expect_zero() {
  local file="$1" span="$2" n rc
  n="$(set -o pipefail; grep -oF -- "$span" "$file" | wc -l | tr -d ' ')"; rc=$?
  if [ "$rc" -ge 2 ]; then fail "grep tool error (rc $rc) on $file"; fi
  [ "$n" -eq 0 ] || fail "expected 0 occurrences in $file, got $n: $span"
}
# 1. The budget-gate pause paragraph carries the governing-probe arm verbatim.
expect_once "$RL" "Before a usage-wall pause's armed timed resume carrier fires"
expect_once "$RL" "the governing probe (one cheap trivial sub-agent dispatch per run)"
expect_once "$RL" "again before continuing at any later turn the lane receives while the pause stands"
expect_once "$RL" "the probe schedules nothing"
expect_once "$RL" "clean probe lifts the pause in-session"
expect_once "$RL" "the pause record gains a resolution line"
expect_once "$RL" "deletes its own armed carrier as its owner before continuing at the recorded next step"
expect_once "$RL" "a refused probe leaves the armed carrier standing with its fire time and payload unchanged"
expect_once "$RL" "starts no governing probe once the carrier's recorded fire time has passed"
expect_once "$RL" "a probe still in flight at the fire is abandoned and recorded in the pause record"
expect_once "$RL" "sole resume path. Weekly \`secondary\` bindings stay report-only"
# 2. The pause protocol's schedule-first, record, and report arms survived byte-intact.
expect_once "$RL" "schedule the resume automation FIRST"
expect_once "$RL" "then append a \`budget_pause\` record to the staging doc"
expect_once "$RL" "Weekly \`secondary\` bindings stay report-only"
expect_once "$RL" "On \`wait-for-reset\`, ride the boundary through in-session"
# 3. The usage-wall doctrine arm: full pins on the final stage, absent-spans at interim1.
ZC_SPANS=(
  "A usage-wall pause with a timed resume carrier armed gets the same governing probe"
  "one cheap probe (one trivial dispatch per run)"
  "again before continuing at any later turn the lane receives while the pause stands"
  "the probe schedules nothing"
  "a clean probe lifts the pause in-session"
  "a resolution line in the pause record"
  "the pause's owner deletes the armed carrier before the lane continues at its recorded next step"
  "a refused probe leaves the carrier standing with its fire time and payload unchanged"
  "the lane starts no probe once the carrier's recorded fire time has passed"
  "abandons one still in flight at the fire"
  "the doctrine's one-probe rule stays per boundary"
  "never the remaining budget's probes. A usage-wall pause with a timed resume carrier armed"
)
if [ "$STAGE" = "interim1" ]; then
  for span in "${ZC_SPANS[@]}"; do
    expect_zero "$ZC" "$span"
  done
else
  for span in "${ZC_SPANS[@]}"; do
    expect_once "$ZC" "$span"
  done
fi
# 4. The doctrine's existing two-class text survived byte-intact.
expect_once "$ZC" "Quota-wall dispatch refusals split into two classes"
expect_once "$ZC" "never the remaining budget's probes"
# 5. Repo gates over the changed set.
bash scripts/check-no-em-dash.sh touched || fail "em-dash scan failed"
bash scripts/scan-public-hygiene.sh || fail "public-hygiene scan failed"
# 6. Maintenance pins, no failure beyond the recorded pre-existing baseline
# (provenance in the preamble above; only that one PIN FAIL is tolerated).
pins_out="$(mktemp)" || fail "mktemp failed"
bash scripts/check_maintenance_pins.sh > "$pins_out" 2>&1
pins_rc=$?
if [ "$pins_rc" -ne 0 ]; then
  grep -q "PIN FAIL" "$pins_out" || fail "pins script failed without a PIN FAIL line (rc $pins_rc)"
  [ "$(grep -c "PIN FAIL" "$pins_out")" -eq 1 ] || fail "more than one PIN FAIL line; only the recorded baseline pin is tolerated"
  grep -qF "clocked-order consult verify-successor leg" "$pins_out" || fail "the PIN FAIL is not the recorded baseline pin"
fi
rm -f "$pins_out"
if [ "$STAGE" = "interim1" ]; then
  echo "INTERIM STAGE 1 PASS (overlay arm still absent as expected)"
else
  echo "ALL VALIDATIONS PASS"
fi
```

### Task 1: Governing-probe arm in the budget-gate pause paragraph

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/review-loop/SKILL.md`

Prescribed insertion (insert verbatim as three sentences into the budget-gate pause paragraph, immediately before the existing span `Weekly \`secondary\` bindings stay report-only`, with one separating space after the preceding sentence's closing period and one separating space between the insertion's final period and that existing span; the lines below are the whole insertion):

```
Before a usage-wall pause's armed timed resume carrier fires, the paused lane runs the governing probe (one cheap trivial sub-agent dispatch per run) once at the pause boundary, after the record above is written and before settling idle, and again before continuing at any later turn the lane receives while the pause stands; the probe schedules nothing. A clean probe lifts the pause in-session (the pause record gains a resolution line, and the lane deletes its own armed carrier as its owner before continuing at the recorded next step), and a refused probe leaves the armed carrier standing with its fire time and payload unchanged. The lane starts no governing probe once the carrier's recorded fire time has passed, and a probe still in flight at the fire is abandoned and recorded in the pause record, the fired carrier's own session being the sole resume path.
```

- [x] Insert the prescribed insertion above verbatim at its named anchor; the arm is the paragraph's only change. [class: IMPLEMENTATION_REQUIRED]
- [x] Change nothing else in the file: the schedule-first, record, and report arms (the spans pinned in Validation section 2) stay byte-identical, and the prescribed insertion adds no incident dates or witness narrative. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Validation Commands block with the argument `interim1` at this task's stage and expect exit 0 with the final line `INTERIM STAGE 1 PASS (overlay arm still absent as expected)`. [class: REPOSITORY_TEST]
- [x] Commit: `review-loop: run one governing probe before a usage-wall pause's timed resume carrier fires`. [class: IMPLEMENTATION_REQUIRED]

### Task 2: Usage-wall doctrine reconciliation in the maintenance overlay

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/zcode.md`

Prescribed insertion (append verbatim to the usage-wall doctrine sentence at the end of the Dispatch discipline bullet, immediately after the existing span `never the remaining budget's probes.` inside the same bullet line; the leading single space on the line below separates it from the existing sentence and is part of the insertion):

```
 A usage-wall pause with a timed resume carrier armed gets the same governing probe at its own boundaries: the paused lane runs one cheap probe (one trivial dispatch per run) once at the pause boundary and again before continuing at any later turn the lane receives while the pause stands, and the probe schedules nothing; a clean probe lifts the pause in-session (a resolution line in the pause record, and the pause's owner deletes the armed carrier before the lane continues at its recorded next step), a refused probe leaves the carrier standing with its fire time and payload unchanged, the lane starts no probe once the carrier's recorded fire time has passed and abandons one still in flight at the fire (the fired carrier's session is the sole resume path), and the doctrine's one-probe rule stays per boundary.
```

- [x] Append the prescribed insertion above verbatim at its named anchor; the sentence is the doctrine bullet's only change. [class: IMPLEMENTATION_REQUIRED]
- [x] Change nothing else in the file: the doctrine's existing two-class text (the spans pinned in Validation section 4) stays byte-identical, the stale home-pointer clause earlier in the sentence is not rewritten, and the prescribed insertion adds no incident dates or witness narrative. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the full Validation Commands block (no argument) and expect exit 0 with the final line `ALL VALIDATIONS PASS`. [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: governing probe lifts a usage-wall pause in-session before its carrier fires`. [class: IMPLEMENTATION_REQUIRED]
