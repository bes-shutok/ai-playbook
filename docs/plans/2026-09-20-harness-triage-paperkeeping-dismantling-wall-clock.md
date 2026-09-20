# Plan: harness triage: paperkeeping dismantling and wall-clock

Backlog origins (all `docs/history/backlog/`): `2026-09-18-harness-paperkeeping-triage-dismantle.md`,
`2026-09-18-harness-wall-clock-speedups.md`, `2026-09-18-done-sweep-gate-runner-codification.md`,
`2026-09-18-done-rearm-on-touch-mechanical-gate.md`. Analysis of record (frozen input):
`docs/tmp/2026-09-18-harness-principles-triage.md`.

## Terms

- **Done sweep gate runner**: `scripts/done_sweep_gates.sh` plus its Python helper
  `scripts/done_sweep_gates_lib.py`; runs the done skill's deterministic gates in
  SKILL.md order and emits one machine-readable report (gate, rc, short message) plus
  a human summary.
- **Gate phase**: a runner invocation covering a contiguous slice of the done step
  order. `pre-docs` covers the gates that run before the docs-branch skill (done Steps
  1.5, 2.65, 2.648, 2.645, 2.64, 2.63, 2.62); `pre-commit` covers the gates that run
  before commit (done Steps 2.7 scan half, 2.76, 2.8). Judgment steps between them stay
  in the skill.
- **Rearm-on-touch check (script)**: `scripts/rearm_on_touch.py`; the mechanical form
  of the maintenance Step 0 duty: reads the scheduler state file state-first, classifies
  the loop state, applies the three bookkeeping edits, emits a verdict or an explicit
  skipped-reason line.
- **Scheduler state file**: `.ai-playbook/scheduler-state.json` at the repository root
  (schema per `agents/skills/maintenance/SKILL.md` State file section; fields used here:
  `parent_automation_id`, `children[]`, `parent_absent_since`, `rearm_note`).
- **Recognition rule**: an ENABLED automation whose title matches the recipe title,
  whose prompt begins with the scheduler prompt template's opening line, and whose
  prompt contains the resolved repository root; literals live in
  `agents/skills/maintenance/zcode.md` (frozen; pinned by `scripts/check_maintenance_pins.sh`).
- **Shell fast-path**: the budget-guard wrapper change: when the guard flag file is
  absent, exit 0 without spawning python; when present, exec the core unchanged.
- **Parallel implement group**: a set of K >= 2 single-task implement workers the
  execute-plan orchestrator launches concurrently for pairwise file-disjoint tasks,
  each with its own session, claim, policy token, and log; per-member done still runs
  sequentially in document order after members land.
- **Zero-lifetime-finding check**: a validator check or gate whose firing count over
  the lifetime review corpus is zero per the usage-capture output or an equivalent
  one-off count; the evidence artifact for every prune in Tasks 6 and 7.
- **Three-question triage test**: per component: does it prevent a recorded incident
  (quality), save more agent time than it costs (efficiency), and is it the cheapest
  such mechanism (simplicity); fails all three, dismantle; passes but over-built, shrink.

## Assumptions

- assume the runner absorbs exactly the ten deterministic steps listed in the Gate
  phase term and every judgment step stays in the skill (lock and run-start marker,
  learn, docs-branch, formatting-only rollback, cross-reference review, unused-import
  scan, commit staging decisions, lock release, outcome report); basis: origin
  done-sweep-gate-runner-codification names the keep-set ("lock acquire/release, learn,
  commit staging decisions, and failure handling") and each absorbed step is a fixed
  command or mechanical rule with an exit-code verdict.
- assume two gate phases because learn and docs-branch (skill invocations, not gates)
  interleave the deterministic steps in the SKILL.md order (0, 1, 1.5, 2.65, 2.648,
  2.645, 2.64, 2.63, 2.62, 2, 2.5, 2.6, 2.7, 2.75, 2.76, 2.8, 3); basis: the on-disk
  step sequence of `agents/skills/done/SKILL.md`.
- assume the rearm script classifies, books, and decides, while the agent performs any
  automation primitives (create, update, delete are agent-side tools, not shell
  primitives); the script accepts an optional listing JSON as decision input, the shape
  the origin names "or accepts the listing as input"; basis: origin
  done-rearm-on-touch-mechanical-gate, Expected behavior.
- assume parallel implement groups land and the batch contract stays untouched, and
  batch-cap widening (origin proposal 3) is declined: batch members implement
  sequentially inside one worker, so widening buys launch amortization, not wall-clock,
  and grows single-session context against the context-budget principle; basis: origin
  harness-wall-clock-speedups proposals 2 and 3 (proposal 3 is marked "consider"),
  triage table row 2, standing pre-authorization 2026-09-20.
- assume validator shrink is evidence-gated: only zero-lifetime-finding checks are
  pruned and incident-linked checks stay even when never fired; basis: triage method
  section and origin harness-paperkeeping-triage-dismantle direction 2.
- assume the fail-open/dead-probe cluster of the dismantle origin needs no work here:
  the owning plan executed and shipped the detection seam and skip predicate
  (`scripts/harness_detection.py` on disk, completed plan
  `docs/plans/completed/2026-09-18-harness-detection-and-budgeting-skip.md`); basis:
  on-disk verification 2026-09-20.
- assume deployment steps cover only this plan's own artifacts (gate runner, rearm
  script, fast-path wrappers, lessons hub CLI) copied to the `~/.ai-playbook/` runtime
  homes per the canonical-copy rule, while the recall hooks stay per-agent SYMLINKS
  into the repo wrappers per the README install table (agents/hooks/lessons-recall/
  README.md, verified live 2026-09-20); no blanket sync of pre-existing deployed
  drift; basis: runtime-registry-sync model and the live symlink probe.
- assume the pins suite freezes done-skill prose this plan touches, so pin updates ride
  the same tasks that move the prose; basis: `scripts/check_maintenance_pins.sh`
  verified 2026-09-20 at its two done-skill pin sites (the done-skill ordering pin in
  the python block and the "done-skill rearm-on-touch pointer" grep pin near the end of
  the file).
- assume telemetry readership evidence is gathered at execution time; the public alias
  of `summarize_review_stats` inside `validate_review_staging.py` (line 1504) is
  resolved inside the same verdict task; basis: authoring rg probe 2026-09-20 found
  references in README.md, `agents/skills/review-staging/SKILL.md`, and the alias line.

Decision points requiring a grill: gate-step absorption set: resolved by origin 3 keep-list, source docs/history/backlog/2026-09-18-done-sweep-gate-runner-codification.md, 2026-09-20, affects Tasks 1-2; two-phase runner split: resolved by on-disk done step interleaving, source agents/skills/done/SKILL.md, 2026-09-20, affects Task 1; rearm script boundary (classify/book/decide, agent performs primitives): resolved by origin 4 listing-as-input option, source docs/history/backlog/2026-09-18-done-rearm-on-touch-mechanical-gate.md, 2026-09-20, affects Task 3; parallel groups over batch widening: resolved by standing pre-authorization on origin 2 proposals, source authoring dispatch, 2026-09-20, affects Task 5; telemetry verdict procedure (evidence-first, both outcomes executable): resolved by origin 1 direction 2, source docs/history/backlog/2026-09-18-harness-paperkeeping-triage-dismantle.md, 2026-09-20, affects Task 6.

## Gist & Examples

TLDR: the done skill's ten deterministic gates collapse into one runner invoked twice
per run (before docs-branch, before commit), the one ungated done duty (rearm-on-touch)
becomes a script whose outcome lands in the run record, the per-tool-call hook tax is
removed by a shell stat, file-disjoint implement tasks gain real concurrency, and the
over-built validators shrink behind lifetime evidence; the Go rewrite and the batch cap
stay rejected/untouched, recorded for durability.

Driving force: the 2026-09-18 harness principles triage. Its ranking: review rounds are
semantically serial (keep; churn control exists); the implement loop and the done sweep
are the wall-clock costs this plan removes; the PreToolUse hook is the one true hot
path; the validators are over-built relative to their evidence.

1. **Done sweep, one call per phase.** Today a done run reads 690 lines of prose and
   runs each gate by hand, one agent-read-run-interpret cycle per step. Example: the
   backlog-inbox gate alone is read prose, a resolved path, an invoked validator, and
   an interpreted exit code. After Task 2 the same run executes
   `done_sweep_gates.sh pre-docs` after learn and `done_sweep_gates.sh pre-commit`
   before staging, reads one report, and fixes only what the report flags. The skill
   keeps the judgment work: lock, learn, docs-branch, formatting rollback,
   cross-references, imports, commit staging, release, report.

2. **Rearm-on-touch, gated like its siblings.** Witness 2026-09-18: an automation-born
   authoring session ran done end to end and skipped the prose-only rearm check; the
   maintenance loop stayed dark for hours and the skip left no trace. After Task 3 the
   check is a script invocation whose verdict (including an explicit skipped-reason) is
   echoed in the Step 7 report, so a skipped or failed check is visible in the run
   record like a flagged gate result, while a failed check stays advisory for the
   commit path (echo-and-continue, pinned in Task 3), matching the state file's
   advisory status.

3. **Hook fast-path.** The ZCode and Codex PreToolUse adapters exec
   `python3 budget_guard_core.py` on every tool call of every session; the common case
   (no flag file) needs only a stat. After Task 4 the wrappers return empty-pass
   immediately when the flag is absent and exec the core only when a window is armed.

4. **Parallel implement groups.** The batch contract (up to four file-disjoint tasks in
   ONE worker, implemented sequentially) buys launch amortization only. After Task 5
   the orchestrator may launch K single-task implement workers concurrently when the
   next K unchecked tasks are pairwise file-disjoint and validation-independent; the
   driver enforces disjointness at claim time and records the group; per-member done
   still runs in document order, so commit and manifest discipline are unchanged.

5. **Evidence-gated shrink.** The registry validator, the review-staging validator,
   the telemetry pair, and the five lessons scripts shrink only where the lifetime
   corpus shows zero findings or proven redundancy; incident-linked checks stay.
   Example: a doc-registry check that never fired in the whole corpus is deleted with
   the firing-count table recorded in the task log; the archive-transition write gate
   that guards recorded incident classes stays. (The sizing figures in the frozen
   triage doc, registry validator 2.6k lines with 116 checks and staging validator
   12k lines, are quoted from the 2026-09-18 analysis of record, not current
   measurements; the live selftest reports 148 registry checks and the staging
   validator is larger today. The shrink stays evidence-gated at execution either
   way.)

## Design Invariants (CR Guard)

- **P10 skip predicate stays intact.** The harness-detection seam and the
  unsupported-harness budgeting skip (completed plan
  `2026-09-18-harness-detection-and-budgeting-skip.md`) are recent executed work; no
  task in this plan touches `scripts/harness_detection.py` or
  `scripts/quota_window_probe.py` detection semantics.
- **Gate preservation.** Every gate absorbed by the runner keeps gating: the runner
  gate registry must equal the collapsed step set at gate AND named sub-check
  granularity (every mechanical sub-check of each absorbed step, such as the Step 2.7
  push-range commit-message audit, keeps checking); no check is silently dropped,
  weakened, or reordered within a phase.
- **done ordering discipline.** Per-task done, document order, one commit per task:
  parallel groups change launch concurrency only; Hard Gate 4 (done after every task)
  and the never-parallel clause for done itself stay.
- **Recipe literals frozen.** `agents/skills/maintenance/zcode.md` recognition literals
  are the pinned source of record; the rearm script mirrors, never edits, them.
- **Import surface stability.** `scripts/plan_readiness.py` imports
  `validate_review_staging.py` and `facts_paths.py` from its own directory; the VRS
  shrink keeps both importable and `plan_readiness` importable.
- **Sidecar contract stays.** The review sidecar contract prevents a recorded incident
  class; the VRS shrink may prune checks and collapse redundant layers but keeps the
  version-1 contract enforced.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the runner gate registry equals the ten absorbed steps at gate and
  sub-check granularity, including the Step 2.7 push-range commit-message audit
  (Co-authored-by trailers and employer-brand patterns over the push range) inside the
  sensitive-data-scan gate; each absorbed gate keeps its pre-existing invocation
  semantics (same validator, same conditions, same fail-open or fail-closed behavior);
  the rearm classification covers the state space (parent-ok, surrendered-live-child,
  darkness-rearm-required, listing-required with reason fresh-absence or
  null-parent-id, stale-state-listing-required, no-state-file, malformed); the wrapper
  never spawns python when the flag is absent and behaves byte-identically when it is
  present; the driver refuses an overlapping or over-cap parallel group at claim time.
- performance: hook fast-path latency observed before and after (recorded numbers in
  the task log; observation, not a hard gate, because sandbox python spawns are
  environment-dependent); parallel-group wall-clock observed non-increasing on a
  disjoint fixture plan (observation).
- simplicity: done SKILL.md under 450 lines after the rewire; the lessons CLI behind
  one entry point (`scripts/lessons.py`) while the five lessons modules remain
  importable libraries; telemetry verdict recorded with reader evidence either way.
  (The origin's "~350 lines" aspiration is unreachable without compressing sections
  Task 2 keeps untouched in meaning: the r2 review measured the keep-set end state at
  406-435 lines, so the gate binds at the measured feasible bound 450; the shrink from
  690 lines is still the deliverable.)
- maintainability: gate and classification logic lives in code with hermetic tests, not
  prose; the pins suite stays green across every prose move.

**Done when:**
- `python3 -m pytest scripts/test_done_sweep_gates_lib.py scripts/test_rearm_on_touch.py scripts/test_budget_guard_hooks.py scripts/test_execute_plan_runtime.py -q` passes.
- `bash -n scripts/done_sweep_gates.sh` exits 0 and `list-gates` prints the ten gate
  ids in phase order.
- `wc -l agents/skills/done/SKILL.md` reports fewer than 450 lines (the measured
  feasible bound; see the simplicity criterion).
- `bash scripts/check_maintenance_pins.sh` exits 0.
- The rearm fixture matrix passes (six state classes, adoption guards, earliest-value
  retention, ghost horizon, skipped-reason, atomic no-other-field edit).
- The fast-path shim test passes (flag absent: exit 0, empty stdout, no python; flag
  present via `BUDGET_GUARD_FLAG` override: python invoked).
- The driver parallel-group tests pass (overlapping refuse, disjoint accept, manifest
  group record, close on last member commit, failed-member isolation).
- Post-prune: `doc_registry_validator.py --selftest`, `validate_review_staging.py
  --selftest`, and the plan_readiness import check pass; the telemetry verdict and the
  zero-finding evidence table exist in the task log.
- `python3 scripts/lessons.py selftest --all` passes and the recall hooks resolve the
  hub.
- Runtime copies of every changed runtime-resolved script match the repo
  (`cmp -s` per file).

**Ship when:**
- No external conditions; every criterion above is repository-verifiable. Deployment
  of changed runtime copies is in-task and verified by the `cmp -s` checks.

## Review Scope

**Explicit must-fix; findings on these paths are always in scope (review and fix if valid):**

**Production code:**
- `scripts/done_sweep_gates.sh` *(new)*
- `scripts/done_sweep_gates_lib.py` *(new)*
- `scripts/rearm_on_touch.py` *(new)*
- `scripts/lessons.py` *(new)*
- `agents/skills/done/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/maintenance/SKILL.md` (Step 0 consumer-script reference only)
- `agents/skills/review-staging/SKILL.md` (contract sync only)
- `agents/skills/learn/SKILL.md`,
  `agents/skills/lessons-migrate/SKILL.md` (lessons hub reference updates only)
- `agents/hooks/budget-guard/zcode.sh`, `agents/hooks/budget-guard/codex.sh`
- `~/.ai-playbook/hooks/budget-guard/` (deployed copies of the two wrappers; `cmp -s` verified in Task 4 and gate G9)
- `agents/hooks/lessons-recall/` (the wrappers directory: three CLI wrappers switch to the hub, cursor.sh retained on its inline library import; installed per-agent as symlinks per the README install table, resolve-checked in gate G9)
- `scripts/execute_plan_runtime.py`
- `scripts/doc_registry_validator.py`, `scripts/validate_review_staging.py`
- `scripts/check-no-em-dash.sh` (Validation Commands G14 gate script; touched only as verdict-dependent telemetry-line replacement context in Task 6)
- `scripts/summarize_review_stats.py`, `scripts/review_usage_capture.py` (verdict-dependent:
  shrink coupling or deletion)
- `scripts/lessons_adopt.py`, `scripts/lessons_classify.py`, `scripts/lessons_index.py`,
  `scripts/lessons_migrate.py`, `scripts/lessons_recall.py` (library role retained;
  standalone CLI dispatch removed)
- `scripts/check_maintenance_pins.sh` (pin updates for moved prose only)
- `README.md` (skill catalog and telemetry section updates only)

**Tests:**
- `scripts/test_done_sweep_gates_lib.py` *(new)*
- `scripts/test_rearm_on_touch.py` *(new)*
- `scripts/test_budget_guard_hooks.py`
- `scripts/test_execute_plan_runtime.py`

**Plan-related extension**; implementation and review may change files not listed above.
Treat a finding as in scope when it is **causally related to this plan**: it implements
or completes a plan task, fixes a regression introduced by plan work, closes wiring or
docs implied by an explicit must-fix change, or contradicts a contract the plan changed.
If the link to the plan is weak or speculative, drop as out of scope with a one-line
reason.

**Out of scope; reject unless plan-related:**
- `docs/tmp/2026-09-18-harness-principles-triage.md`; reason: frozen analysis of record
  cited by all four origins, not a work surface.
- `agents/skills/maintenance/zcode.md`; reason: recipe literals are the pinned source
  of record (see Design Invariants); the rearm script mirrors them.
- `scripts/harness_detection.py`, `scripts/quota_window_probe.py`; reason: P10-owned,
  recently executed, protected by a CR Guard.
- `docs/plans/2026-09-19-scheduler-ops-contract-fix.md`,
  `docs/plans/2026-09-19-scheduler-ops-lanes-durability.md`,
  `docs/plans/2026-09-19-no-silent-gate-satisfying-prose-rewrites.md`; reason: peer
  sessions' authored plans, not this plan's surfaces.
- `agents/skills/execute-plan/subagent-prompts.md`, `agent-logs.md`; reason: the
  parallel-group option reuses the existing Implement Task template and log conventions;
  only if execution proves a template edit unavoidable does it enter scope as a
  plan-related extension.

## Validation Commands

```bash
set -u
cd "$(git rev-parse --show-toplevel)" || { echo "VALIDATION FAIL: no git root"; exit 1; }
fail() { echo "VALIDATION FAIL: $1"; exit 1; }

# G1 runner syntax
bash -n scripts/done_sweep_gates.sh || fail "done_sweep_gates.sh syntax"

# G2 gate registry equivalence: all ten absorbed gates, each present
LIST="$(bash scripts/done_sweep_gates.sh list-gates)" || fail "list-gates invocation"
for gate in plan-readiness confluence-hygiene doc-registry backlog-inbox review-staging vim-swap-sweep docs-tmp-sweep sensitive-data-scan em-dash-scan instruction-size; do
  printf '%s\n' "$LIST" | grep -qx "$gate" || fail "gate missing from runner registry: $gate"
done

# G3 phase wiring inside done SKILL.md (per-obligation probes)
grep -q "done_sweep_gates.sh pre-docs" agents/skills/done/SKILL.md || fail "pre-docs phase not wired"
grep -q "done_sweep_gates.sh pre-commit" agents/skills/done/SKILL.md || fail "pre-commit phase not wired"

# G4 size target (measured feasible bound; the keep-untouched sections floor the end state at 406-435 lines)
LINES="$(wc -l < agents/skills/done/SKILL.md)"
[ "$LINES" -lt 450 ] || fail "done SKILL.md is $LINES lines (target < 450)"

# G5 rearm wiring: invocation precedes the Step 0 heading; stale prose-only wording gone
awk '/^## Step 0: Acquire project done lock/{exit} /rearm_on_touch\.py/{found=1} END{exit found?0:1}' agents/skills/done/SKILL.md \
  || fail "rearm script invocation missing before Step 0 heading"
grep -q "rearm_on_touch" agents/skills/done/SKILL.md || fail "rearm outcome echo missing"

# G6 maintenance Step 0 names the consumer script
grep -q "rearm_on_touch" agents/skills/maintenance/SKILL.md || fail "maintenance Step 0 does not name the consumer script"

# G7 pins suite
bash scripts/check_maintenance_pins.sh >/dev/null 2>&1 || fail "maintenance pins suite"

# G8 fast-path, hermetic: absent flag exits 0 with empty stdout and no python spawn
SHIM="$(mktemp -d)" || fail "mktemp shim"
SENTINEL="$SHIM/sentinel"
printf '#!/bin/sh\nprintf x > "%s"\nexit 0\n' "$SENTINEL" > "$SHIM/python3"
chmod +x "$SHIM/python3"
OUT="$(env PATH="$SHIM:$PATH" BUDGET_GUARD_FLAG="$SHIM/absent.flag" bash agents/hooks/budget-guard/zcode.sh </dev/null 2>/dev/null)"
RC=$?
[ "$RC" -eq 0 ] || fail "fast-path rc $RC with absent flag"
[ -z "$OUT" ] || fail "fast-path stdout not empty with absent flag"
[ ! -e "$SENTINEL" ] || fail "fast-path spawned python with absent flag"
touch "$SHIM/armed.flag"
env PATH="$SHIM:$PATH" BUDGET_GUARD_FLAG="$SHIM/armed.flag" bash agents/hooks/budget-guard/zcode.sh </dev/null >/dev/null 2>&1
[ -e "$SENTINEL" ] || fail "fast-path did not exec python with flag present"
rm -rf "$SHIM"

# G9 deployed runtime copies match the repo
cmp -s agents/hooks/budget-guard/zcode.sh "$HOME/.ai-playbook/hooks/budget-guard/zcode.sh" || fail "zcode.sh runtime copy drift"
cmp -s agents/hooks/budget-guard/codex.sh "$HOME/.ai-playbook/hooks/budget-guard/codex.sh" || fail "codex.sh runtime copy drift"
cmp -s scripts/rearm_on_touch.py "$HOME/.ai-playbook/scripts/rearm_on_touch.py" || fail "rearm runtime copy drift"
cmp -s scripts/done_sweep_gates.sh "$HOME/.ai-playbook/scripts/done_sweep_gates.sh" || fail "gate runner runtime copy drift"
cmp -s scripts/done_sweep_gates_lib.py "$HOME/.ai-playbook/scripts/done_sweep_gates_lib.py" || fail "gate runner lib runtime copy drift"
cmp -s scripts/lessons.py "$HOME/.ai-playbook/scripts/lessons.py" || fail "lessons hub runtime copy drift"
# Recall hooks deploy as per-agent symlinks into each agent's hook home (README install
# table, verified live 2026-09-20); resolve-check them, never cmp: a repo edit propagates
# through the link, a copy-installed or dangling link is drift.
REPO_TOP="$(pwd)"
for pair in "claude:$HOME/.claude/hooks/lessons-recall.sh" "codex:$HOME/.codex/hooks/lessons-recall.sh" "cursor:$HOME/.cursor/hooks/lessons-recall.sh" "agy:$HOME/.gemini/antigravity-cli/hooks/lessons-recall.sh"; do
  name="${pair%%:*}"; link="${pair#*:}"
  if [ -L "$link" ] && [ ! -e "$link" ]; then fail "recall hook link is dangling: $link"; fi
  if [ -e "$link" ]; then
    [ "$(readlink -f "$link")" = "$REPO_TOP/agents/hooks/lessons-recall/$name.sh" ] || fail "recall hook is not a symlink resolving to the repo wrapper (copy-installed?): $link"
  else
    echo "note: recall hook link not installed on this host (per README install table): $link"
  fi
done

# G10 python suites (gate runner lib, rearm, hook wrappers, driver)
python3 -m pytest scripts/test_done_sweep_gates_lib.py scripts/test_rearm_on_touch.py scripts/test_budget_guard_hooks.py scripts/test_execute_plan_runtime.py -q || fail "python suites"

# G11 pruned validators still certify; import surface stable
python3 scripts/doc_registry_validator.py --selftest || fail "doc_registry selftest"
python3 scripts/validate_review_staging.py --selftest || fail "validate_review_staging selftest"
python3 -c "import sys; sys.path.insert(0, 'scripts'); import plan_readiness" || fail "plan_readiness import surface"
# Telemetry selftest: on the keep verdict this passes; on the dismantle verdict Task 6
# replaces this line with the zero-reference sweep (the deleted scripts must leave no
# stale import), never left pointing at a deleted file.
python3 scripts/review_usage_capture.py --selftest || fail "review_usage_capture selftest"

# G12 lessons hub: one entry point, selftests green, recall hooks resolve the hub
python3 scripts/lessons.py selftest --all || fail "lessons hub selftests"
for w in agy claude codex; do
  # comment-stripped match: a mention in a comment is not a witness of the call path
  sed 's/#.*//' "agents/hooks/lessons-recall/$w.sh" | grep -q "lessons.py" || fail "recall hook not on the hub: $w.sh"
done

# G13 consolidation and stale-wording gates (negated, per-obligation)
for path in scripts/lessons_adopt.py scripts/lessons_classify.py scripts/lessons_index.py scripts/lessons_migrate.py scripts/lessons_recall.py; do
  [ -f "$path" ] || fail "lessons library module missing: $path"
  if grep -q "__main__" "$path"; then fail "standalone CLI dispatch still present in lessons library module: $path"; fi
done
test -f scripts/lessons.py || fail "lessons hub missing"
# G13b parallel-group carve-out, per-site probes (r2 F4): each superseded launch-rule
# site must name the carve-out on its own line; Task 5 keeps each site's anchor phrase
# exactly so these probes stay anchored. A deleted anchor line is a re-derivation the
# fresh review round must judge, not a gate pass.
XSP=agents/skills/execute-plan/SKILL.md
grep -q "parallel-group" "$XSP" || fail "parallel-group contract absent from execute-plan SKILL.md"
for anchor in "one launch at a time" "one launch per iteration" "never parallel" "Always wait"; do
  grep -q "$anchor" "$XSP" || fail "launch-rule anchor phrase missing (deleted or reworded away): $anchor"
done
XSP_ROW="$(grep -E '^\| *Implement' "$XSP" || true)"
[ -n "$XSP_ROW" ] || fail "Implement task row missing from the launch-rules table"
echo "$XSP_ROW" | grep -q "parallel-group" || fail "launch-rules Implement row missing the parallel-group carve-out"
if grep -n "one launch at a time" "$XSP" | grep -qv "parallel-group"; then fail "intro launch rule missing the parallel-group carve-out"; fi
if grep -n "one launch per iteration" "$XSP" | grep -qv "parallel-group"; then fail "Step 1.1 launch rule missing the parallel-group carve-out"; fi
if grep -n "never parallel" "$XSP" | grep -qv "parallel-group"; then fail "never-parallel line missing the parallel-group carve-out"; fi
if grep -n "Always wait" "$XSP" | grep -qv "parallel-group"; then fail "always-wait bullet missing the parallel-group carve-out"; fi
if grep -n "rearm-on-touch check defined in the maintenance skill" agents/skills/done/SKILL.md | grep -qv "rearm_on_touch"; then
  fail "stale prose-only rearm duty line survived without the script invocation"
fi
python3 -c "import sys; sys.path.insert(0, 'scripts'); import skill_gate" || fail "skill_gate import surface (lessons libraries)"

# G14 no em dash in touched instruction and script surfaces
bash scripts/check-no-em-dash.sh touched || fail "em dash scan"
```

### Task 1: Done sweep gate runner script

Files:
- `scripts/done_sweep_gates.sh` *(new)*
- `scripts/done_sweep_gates_lib.py` *(new)*
- `scripts/test_done_sweep_gates_lib.py` *(new)*

- [ ] `test_done_sweep_gates_lib.py#test_gate_registry_matches_absorbed_steps`; given the lib gate registry, expects exactly ten gate ids in the two phase slices, in done SKILL.md order, matching `plan-readiness, confluence-hygiene, doc-registry, backlog-inbox, review-staging, vim-swap-sweep, docs-tmp-sweep, sensitive-data-scan, em-dash-scan, instruction-size` [class: REPOSITORY_TEST]
- [ ] `test_done_sweep_gates_lib.py#test_plan_readiness_candidates`; given a fixture repo with `plan-deliverables.txt` naming one plan, a second plan untracked under `{plans_dir}` inside the session window, an active execute-plan manifest with a fresh `updated:` line over a third, and a completed-plan dir entry, expects candidates = first and second only, third exempted by the fresh-manifest rule, completed dir excluded [class: REPOSITORY_TEST]
- [ ] `test_done_sweep_gates_lib.py#test_plan_readiness_conservative_gating`; given no previous-run `run-start-` marker under `{tmp_dir}/done-session/`, expects the window to be unanchorable and every gitignored-arm (`!!`) plan to be treated as a session deliverable, each gated plan named [class: REPOSITORY_TEST]
- [ ] `test_done_sweep_gates_lib.py#test_plan_readiness_stale_manifest_no_exemption`; given an active manifest whose `updated:` line is 30 hours old, expects the exemption refused and the plan gated [class: REPOSITORY_TEST]
- [ ] `test_done_sweep_gates_lib.py#test_deliverables_removal_rule`; given a passing, an exempted, and an archived plan listed in `plan-deliverables.txt`, expects exactly those lines removed and no others [class: REPOSITORY_TEST]
- [ ] `test_done_sweep_gates_lib.py#test_report_shape_and_order`; given a phase where an early gate fails, expects one JSON line per gate in registry order with `gate`, `rc`, `message` fields, a human summary block, and a phase-level non-zero exit [class: REPOSITORY_TEST]
- [ ] `test_done_sweep_gates_lib.py#test_fail_open_gates_preserved`; given a fixture repo where the backlog-inbox validator, the review-staging validator, or the doc-registry validator is absent from every resolved path, expects each to degrade per its pre-existing arm: backlog-inbox warn-and-continue (rc 0, warning recorded), review-staging no-op when no session-touched staging path exists, doc-registry report-once-and-continue (rc 0) per the Step 2.648 fail-open paragraph [class: REPOSITORY_TEST]
- [ ] `test_done_sweep_gates_lib.py#test_sensitive_data_scan_push_range_audit`; given a fixture repo with a reachable upstream where a commit in the push range carries a `Co-authored-by:` trailer (and a second fixture carrying an employer-brand pattern from facts), expects the sensitive-data-scan gate to fail naming the offending commit and pattern [class: REPOSITORY_TEST]
- [ ] `test_done_sweep_gates_lib.py#test_sensitive_data_pattern_hits`; given staged or untracked fixture content containing a personal absolute path pattern, expects the diff-content grep arm to fail the gate; given clean content, expects the gate to pass [class: REPOSITORY_TEST]
- [ ] `test_done_sweep_gates_lib.py#test_vim_swap_liveness_refusal`; given a fixture tree with one swap file owned by a live editor PID and one owned by a dead PID (both `file --` verified as Vim swaps), expects the dead-owner file removed and the live-owner file preserved and reported active [class: REPOSITORY_TEST]
- [ ] `test_done_sweep_gates_lib.py#test_docs_tmp_sweep_classification_and_marker_immunity`; given a fixture `docs/tmp` containing an execute-plan session whose plan archived, a `plan-requirements-<slug>.md` whose plan is completed, a `review-loop` scratch dir, a never-synced one-off script, and done-session markers from two prior runs plus the current run, expects: archived-owner entries removed, protected scratch left in place, the never-synced file skipped and reported, and exactly the markers strictly older than the previous-run anchor pruned (current-run and anchor markers immune) [class: REPOSITORY_TEST]
- [ ] `test_done_sweep_gates_lib.py#test_confluence_run_when_gating`; given a fixture repo with no manifest, no confluence-path touches, and no ephemeral snapshots, expects the gate to no-op rc 0; given an ephemeral `*-cf-out.md`, expects `audit-cf-out` to run and a NEEDS_UPGRADE classification to fail the gate [class: REPOSITORY_TEST]
- [ ] `test_done_sweep_gates_lib.py#test_session_window_and_staging_candidate_derivations`; given fixture done-session markers from a previous run and the current run, expects the session window anchored on the previous-run marker (content-confirmed repo root) and the current-run marker immune; given one gitignored staging doc under `{reviews_dir}` inside the window and one outside it, expects exactly the in-window doc among the review-staging gate candidates via the porcelain plus ignored-matching arms filtered by the validator's staging-path predicate [class: REPOSITORY_TEST]
- [ ] Write the runner: `done_sweep_gates.sh <phase>` with phases `pre-docs` and `pre-commit`, plus `list-gates`; read-only gates may run concurrently inside a phase, sweeps and state-mutating gates run sequentially in registry order, report order stays registry order; resolve paths via `scripts/facts_paths.py` helpers with the repo root as anchor; sync nothing yet [class: IMPLEMENTATION_REQUIRED]
- [ ] Implement `pre-docs` gates in lib with the exact pre-existing semantics, each gate's session-scoped input derived mechanically (the runner cannot read chat context): plan-readiness (candidate derivation per the tests above: `plan-deliverables.txt` union porcelain union ignored-matching under `{plans_dir}` excluding `{plans_completed_dir}`, session window from the run-start markers where the newest marker is the current run and the newest strictly older one is the previous-run anchor, content-confirmed against this repo's root, fewer than two markers means unanchorable and conservative gating applies, then `plan_readiness.py <plan>` per candidate), confluence-hygiene (run-when derived mechanically: manifest exists, OR any path under `docs/history/context/confluence/` in the porcelain/ignored set or the session window, OR ephemeral `docs/tmp` snapshots present; `audit-cf-out` until exit 0, `validate` when a manifest exists, `cleanup` last; NEEDS_UPGRADE and UNMAPPED are gate failures so the judgment stays in the skill), doc-registry (`validate`, then the `check-writes --stdin` union of porcelain and `git diff --name-status` from the session-start head with its re-anchor write), backlog-inbox (`check_backlog_inbox_location.py`, fail-open when absent), review-staging (`validate_review_staging.py --hard` over candidates derived mechanically: porcelain plus ignored-matching paths under the resolved `{reviews_dir}` filtered by the validator's own staging-path predicate and restricted to the session window, never a bare `*review*.md` glob and never chat recall), vim-swap-sweep (find, `file --` verification, PID liveness check, remove only verified stale), docs-tmp-sweep (classification rules of done Step 2.62 with the marker-immunity identity derived mechanically per the session-window rule above: current run = newest marker, anchor = newest strictly older, fewer than two markers prunes nothing; plus the never-synced skip) [class: IMPLEMENTATION_REQUIRED]
- [ ] Implement `pre-commit` gates in lib: sensitive-data-scan (the mechanical half of done Step 2.7 in full: the `git diff` pattern greps over staged and untracked content, `scan-public-hygiene.sh` when the repo is the skills repo, AND the push-range commit-message audit (`git log @{u}..HEAD --format=%B` grepped for `Co-authored-by` trailers and the employer-brand patterns resolved from facts) whenever an upstream is configured; the fourth mechanical arm of Step 2.7 item 4, the skills-tree employer-brand grep over `agents/skills/` with LICENSE.txt excluded, is absorbed by the scan-public-hygiene arm because the employer-brand patterns live in the hygiene deny-patterns file that scan covers agents/skills with LICENSE.txt excluded, verified at r2; the scan's excludes (`done/SKILL.md`, `how-to-write-skills/**`) leave those two paths' tree-grep coverage unabsorbed, which the done flow only exposes through that-session diffs, where the diff-content greps of this same gate apply; if the deny-patterns file ever drops the brand pattern, the tree grep re-enters this gate; any hit is a gate failure, fixing stays in the skill), em-dash-scan (`check-no-em-dash.sh touched`), instruction-size (`check-instruction-size.sh gate`) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run `python3 -m pytest scripts/test_done_sweep_gates_lib.py -q`; expect GREEN [class: REPOSITORY_TEST]
- [ ] Deploy `scripts/done_sweep_gates.sh` and `scripts/done_sweep_gates_lib.py` to `~/.ai-playbook/scripts/` (`cp` then `cmp -s` verify) [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `scripts: done sweep gate runner with phase registry and hermetic lib tests` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Rewire done SKILL.md to the runner

Files:
- `agents/skills/done/SKILL.md`
- `scripts/check_maintenance_pins.sh` (only if a pinned line moves)

- [ ] Replace done Steps 1.5, 2.65, 2.648, 2.645, 2.64, 2.63, and 2.62 with one step: run `done_sweep_gates.sh pre-docs` after learn; on gate failure, fix what the report flags using the compressed per-gate failure guidance (recorded-stop exception and the deployment-gap signature for the readiness gate stay verbatim in meaning); re-run the runner until exit 0 [class: IMPLEMENTATION_REQUIRED]
- [ ] Replace the mechanical halves of done Steps 2.7, 2.76, and 2.8 with one step: run `done_sweep_gates.sh pre-commit` after docs-branch and the judgment steps (formatting rollback, cross-references, unused imports); on failure fix and re-run [class: IMPLEMENTATION_REQUIRED]
- [ ] Keep untouched in meaning: Step 0 lock and run-start marker, Step 1 learn, Step 2 docs-branch, Step 2.5 formatting rollback, Step 2.6 cross-references, Step 2.75 unused imports, Steps 3 to 7 commits, skills-repo, facts, release, report [class: IMPLEMENTATION_REQUIRED]
- [ ] Re-derive the glue surfaces that reference collapsed step numbers in the same edit: the three named surfaces (the Workflow-continuity paragraph in the Invocation section including its empty-tree exception sentence ordering Steps 2.65 through 2.62, the Rules bullet instructing Step 2.65 before docs-branch, and the Integration Points entries referencing Steps 2.64 and 2.62) plus a sweep of the final file for ANY remaining reference to a collapsed step number (`grep -nE 'Step (2\.645|2\.648|2\.62|2\.63|2\.64|2\.65|2\.76|2\.7|1\.5|2\.8)([^0-9]|$)'`), each re-pointed to its runner gate name or renumbered kept step; the runner steps carry no fixed numbers, so re-point by name, not by position [class: IMPLEMENTATION_REQUIRED]
- [ ] Verify `wc -l agents/skills/done/SKILL.md` reports fewer than 450 lines (the measured feasible bound; the keep-untouched sections end at 406-435 lines, so no compression inside kept sections is authorized) [class: REPOSITORY_TEST]
- [ ] Run `bash scripts/check_maintenance_pins.sh`; update any pin whose frozen prose line this rewire moved, preserving each pin's invariant (the rearm pointer must still precede the Step 0 heading), and record every pin edit in the commit body [class: REPOSITORY_TEST]
- [ ] Run the Task 1 suite plus the pins suite; expect GREEN [class: REPOSITORY_TEST]
- [ ] Commit: `skills: done gate steps collapse into the sweep gate runner` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Rearm-on-touch mechanical check

Files:
- `scripts/rearm_on_touch.py` *(new)*
- `scripts/test_rearm_on_touch.py` *(new)*
- `agents/skills/done/SKILL.md`
- `agents/skills/maintenance/SKILL.md`
- `scripts/check_maintenance_pins.sh` (only if a pinned line moves)

- [ ] `test_rearm_on_touch.py#test_class_parent_ok`; given a state file with a recorded live parent and null `parent_absent_since`, expects class `parent-ok`, no bookkeeping edits, rc 0 [class: REPOSITORY_TEST]
- [ ] `test_rearm_on_touch.py#test_class_surrendered_live_child`; given an absent parent with a pending `children[]` entry whose `fire_at` is 1 hour past and no failed outcome, expects class `surrendered-live-child` and no re-arm decision [class: REPOSITORY_TEST]
- [ ] `test_rearm_on_touch.py#test_class_ghost_pending_does_not_suppress_darkness`; given a pending entry whose `fire_at` is 7 hours past with a failed outcome and `parent_absent_since` older than one cadence period (2 hours), expects class `darkness-rearm-required` [class: REPOSITORY_TEST]
- [ ] `test_rearm_on_touch.py#test_class_fresh_absence_listing_required`; given an absent parent, no live pending child, and `parent_absent_since` younger than one cadence period, expects class `listing-required` with reason `fresh-absence` (absence not yet darkness) and no bookkeeping edits [class: REPOSITORY_TEST]
- [ ] `test_rearm_on_touch.py#test_class_null_parent_id_listing_required`; given a state file with null or missing `parent_automation_id` and no live pending child, expects class `listing-required` with reason `null-parent-id` and no bookkeeping edits [class: REPOSITORY_TEST]
- [ ] `test_rearm_on_touch.py#test_class_stale_state_file`; given a state file whose last write is older than one cadence period, expects class `stale-state-listing-required` (the staleness escape) and no bookkeeping edits [class: REPOSITORY_TEST]
- [ ] `test_rearm_on_touch.py#test_no_state_file_skipped_reason`; given no `.ai-playbook/scheduler-state.json`, expects the explicit skipped-reason line `no-scheduler-state-file`, rc 0, and an inert verdict [class: REPOSITORY_TEST]
- [ ] `test_rearm_on_touch.py#test_malformed_state_file_fails_loud`; given unparseable JSON, expects rc 2 and a loud error, never a silent pass [class: REPOSITORY_TEST]
- [ ] `test_rearm_on_touch.py#test_listing_input_armed_again_bookkeeping`; given `--listing-json` input whose parsed content shows an ENABLED recognition match (title match, prompt opening match, resolved repo root contained) and a set `parent_absent_since`, expects `parent_absent_since` cleared and `rearm_note` cleared in one atomic targeted edit with no other field touched [class: REPOSITORY_TEST]
- [ ] `test_rearm_on_touch.py#test_adoption_guards`; given a listing match whose id differs from the recorded one where the recorded id is itself live-enabled, expects no adoption; where the recorded id is absent-or-disabled, expects adoption with the earliest `parent_absent_since` retention rule [class: REPOSITORY_TEST]
- [ ] `test_rearm_on_touch.py#test_bookkeeping_edit_atomic_no_other_field`; given any bookkeeping scenario, expects the write to go through a temp file plus atomic replace, changing only the named fields, preserving all others byte-for-byte [class: REPOSITORY_TEST]
- [ ] Write `scripts/rearm_on_touch.py`: state-first classification per maintenance Step 0 and the zcode.md re-arm hygiene shape, covering the full class set (parent-ok, surrendered-live-child, darkness-rearm-required, listing-required with reason fresh-absence or null-parent-id, stale-state-listing-required; plus the inert no-state-file skipped-reason and the malformed rc 2), cadence period 2 hours, live-child horizon 6 hours, earliest-value retention, adoption guards, optional `--listing-json <path|->` decision input, JSON verdict plus one-line human summary on stdout, rc 0 normal, rc 2 malformed-or-failed; the script never calls automation primitives; deploy to `~/.ai-playbook/scripts/` with `cmp -s` verify [class: IMPLEMENTATION_REQUIRED]
- [ ] Wire the done preamble: the line before Step 0 invokes the script, keeps the pinned pointer phrase, and adds the script path; the escalation contract is echo-and-continue: normal verdicts and rc 2 (malformed-or-failed) alike are echoed in the Step 7 report (class, bookkeeping, skipped-reason, or the failure) so a skipped or failed check is visible in the run record, and a failed check never blocks the commit path, matching the scheduler state file's advisory status and the sibling fail-open hygiene gates [class: IMPLEMENTATION_REQUIRED]
- [ ] Update maintenance SKILL.md Step 0 to name `scripts/rearm_on_touch.py` as the consumer script for rearm-on-touch sessions, mirroring (not replacing) the duty prose [class: IMPLEMENTATION_REQUIRED]
- [ ] Run `python3 -m pytest scripts/test_rearm_on_touch.py -q` and the pins suite; update pins only if a frozen line moved; expect GREEN [class: REPOSITORY_TEST]
- [ ] Commit: `scripts+skills: rearm-on-touch duty becomes a mechanical gate with recorded outcome` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Budget-guard shell fast-path

Files:
- `agents/hooks/budget-guard/zcode.sh`
- `agents/hooks/budget-guard/codex.sh`
- `scripts/test_budget_guard_hooks.py`
(the deployed copies under `~/.ai-playbook/hooks/budget-guard/` are runtime deploy targets
written by the task's deploy step and verified by gate G9; they are not repo Files entries)

- [ ] `test_budget_guard_hooks.py#test_wrapper_fast_path_absent_flag_no_python`; given a PATH shim whose `python3` sentinel records invocation and `BUDGET_GUARD_FLAG` pointing at an absent file, expects rc 0, empty stdout, and the sentinel never invoked, for both wrappers [class: REPOSITORY_TEST]
- [ ] `test_budget_guard_hooks.py#test_wrapper_flag_present_execs_core`; given the same shim with the flag file present, expects the sentinel invoked with the wrapper's runtime id argument [class: REPOSITORY_TEST]
- [ ] Edit both wrappers: after `FLAG` resolution, honor `BUDGET_GUARD_FLAG` as an override for hermetic testing, then `[ -f "$FLAG" ] || exit 0` before the exec line, with a comment stating the invariant: absent flag means never armed, so empty-pass is semantically exact, and a present flag (armed or expired) takes the unchanged core path [class: IMPLEMENTATION_REQUIRED]
- [ ] Run `python3 -m pytest scripts/test_budget_guard_hooks.py -q`; expect GREEN [class: REPOSITORY_TEST]
- [ ] Deploy both wrappers to `~/.ai-playbook/hooks/budget-guard/` and verify with `cmp -s` [class: IMPLEMENTATION_REQUIRED]
- [ ] Latency observation (recorded, not gating): time 50 wrapper invocations with the flag absent before deploying and after; record both numbers in the task log; if sandbox python spawns are killed or throttled, record the environment blockage instead of fabricating numbers [class: REPOSITORY_TEST]
- [ ] Commit: `hooks: budget-guard wrappers take the shell stat fast-path` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Parallel implement groups

Files:
- `agents/skills/execute-plan/SKILL.md`
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

- [ ] `test_execute_plan_runtime.py#test_parallel_group_claim_refuses_overlap`; given a parallel-group claim whose members share a canonical file, expects refusal with stale-claim evidence naming the shared path [class: REPOSITORY_TEST]
- [ ] `test_execute_plan_runtime.py#test_parallel_group_claim_accepts_disjoint`; given K pairwise-disjoint member tasks in canonical order, expects the claim accepted, the group recorded in the machine manifest with members and state active, and each member holding an ordinary claim bound to the group id [class: REPOSITORY_TEST]
- [ ] `test_execute_plan_runtime.py#test_parallel_group_closes_on_last_member_commit`; given all members committed, expects group state closed and no lingering claim [class: REPOSITORY_TEST]
- [ ] `test_execute_plan_runtime.py#test_parallel_group_failed_member_isolation`; given one member with a terminal blocked receipt inside an active group, expects reclaim allowed for that member only (the terminal-receipt executable exit) and siblings unaffected [class: REPOSITORY_TEST]
- [ ] `test_execute_plan_runtime.py#test_parallel_group_claim_refuses_over_cap`; given 5 pairwise-disjoint eligible tasks, expects the claim refused citing the member cap (the batch numeric caps carried verbatim) [class: REPOSITORY_TEST]
- [ ] Driver: extend the claim path with a parallel-group operation reusing the batch membership disjointness computation (pairwise-disjoint canonical `Files:` sets) and carrying the batch numeric caps verbatim (4 members, 8 combined member files) as the known-safe envelope; the implementation threads these divergence points from the batch protocol, which otherwise stays untouched: a group-kind discriminator in the manifest group record (batch vs parallel) so validation and stale-claim fences can branch; the receipt fence accepts concurrent members (no active-member ordinal gate, no shared anchor session, each member keeps its own session, claim, and log path); reclaim is per member (the terminal-receipt executable exit releases only that member, never an atomic group fail); close = last member commit; group record in the machine manifest [class: IMPLEMENTATION_REQUIRED]
- [ ] execute-plan SKILL.md: add the Step 1.2 parallel-group option (eligibility: K >= 2 next unchecked tasks capped at 4 members and 8 combined member files, pairwise-disjoint canonical `Files:` sets, no cross-task validation dependency, no host-wiring exception receipts and no inclusion-gate ambiguity, mirroring the batch guardrail); the orchestrator launches the single-task Implement Task workers concurrently, records the group and membership in the session manifest, and after all members land runs per-member done in document order; a failed member recovers through the standard single-task path without failing siblings [class: IMPLEMENTATION_REQUIRED]
- [ ] Reword Hard Gate 3 to permit a parallel implement group under the Step 1.2 parallel-group contract while keeping done strictly sequential and the address fan-out governed by its own Step 3.3 contract; then sweep the WHOLE execute-plan SKILL.md for superseded never-parallel wording (known sites: the intro's one-launch-at-a-time line, the Phase 1 loop item, Hard Gate 3 itself, the launch-rules table row and its always-wait bullet, and the Step 1.2 batch prose) and re-derive every surviving line to name the parallel-group carve-out in the same edit; keep each site's anchor phrase ("one launch at a time", "one launch per iteration", "never parallel", "Always wait", the Implement task table row label) so the G13b per-site probes stay anchored [class: IMPLEMENTATION_REQUIRED]
- [ ] Run `python3 -m pytest scripts/test_execute_plan_runtime.py -q`; expect GREEN [class: REPOSITORY_TEST]
- [ ] Commit: `execute-plan: parallel implement groups for file-disjoint tasks` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Paperkeeping evidence pass, registry prune, telemetry verdict

Files:
- `scripts/doc_registry_validator.py`
- `scripts/summarize_review_stats.py`, `scripts/review_usage_capture.py` (verdict-dependent)
- `scripts/validate_review_staging.py` (alias coupling, verdict-dependent)
- `README.md`, `agents/skills/review-staging/SKILL.md` (verdict-dependent)
- `scripts/check-no-em-dash.sh` and the Validation Commands block of this plan (telemetry line, verdict-dependent)

- [ ] Evidence pass: run `scripts/review_usage_capture.py` over the lifetime review corpus (or an equivalent one-off count over the same artifacts) and produce the per-check firing-count table for `doc_registry_validator.py`'s full check inventory (the frozen triage's "116 checks" figure; the live selftest count may differ) and for `validate_review_staging.py`'s check families; write the zero-lifetime-finding list into the task log as the pruning evidence artifact [class: IMPLEMENTATION_REQUIRED]
- [ ] Registry prune: delete exactly the zero-lifetime-finding registry checks; keep incident-linked checks regardless of firing count (the archive-transition write gate and the registry integrity core stay); run `doc_registry_validator.py --selftest`; expect GREEN [class: IMPLEMENTATION_REQUIRED]
- [ ] Telemetry verdict: inventory every consumer of `summarize_review_stats.py` and `review_usage_capture.py` outputs (README sections, review-staging SKILL.md references, the `validate_review_staging.py` public alias at line 1504, any scheduled or docs-branch reader); record the verdict with evidence: keep when a live reader exists, dismantle when none does; on dismantle, delete both scripts, refactor the VRS alias to its private implementation, remove the README section and the review-staging references, sweep for stale references with a negated zero-match check, and replace the telemetry selftest line in this plan's Validation Commands block with that sweep in the same commit; on keep, record the reader evidence and leave the selftest line in place [class: IMPLEMENTATION_REQUIRED]
- [ ] Fold-probe inventory for anything deleted in this task: enumerate every enforceable obligation of the deleted source (`git show <rev>:<path>` before deletion) and give each surviving obligation a dedicated probe; prose remnant sweeps are case-insensitive [class: REPOSITORY_TEST]
- [ ] Run the post-prune validation set (`doc_registry_validator.py --selftest`, `validate_review_staging.py --selftest`, plan_readiness import check); expect GREEN [class: REPOSITORY_TEST]
- [ ] Commit: `scripts: registry prune and telemetry verdict on lifetime evidence` [class: IMPLEMENTATION_REQUIRED]

### Task 7: Review-staging validator shrink and lessons consolidation

Files:
- `scripts/validate_review_staging.py`
- `agents/skills/review-staging/SKILL.md`
- `scripts/lessons.py` *(new)*
- `scripts/lessons_adopt.py`, `scripts/lessons_classify.py`, `scripts/lessons_index.py`, `scripts/lessons_migrate.py`, `scripts/lessons_recall.py`
- `agents/hooks/lessons-recall/` wrappers (three CLI wrappers switch to the hub; `cursor.sh` retained on its library import; per-agent symlink installs resolve-checked in gate G9, no copy deploy)
- `agents/skills/learn/SKILL.md`, `agents/skills/lessons-migrate/SKILL.md`, `agents/skills/done/SKILL.md` (lessons entry-point references only)
- `README.md` (catalog lines only)

- [ ] VRS shrink: delete the zero-lifetime-finding checks from Task 6's evidence table; inventory the hand-written-validation and derived-schema layers and collapse only layers proven redundant by that inventory (the same obligation enforced twice through different shapes); keep the version-1 sidecar contract, the freshness fields, and the staged-Markdown hierarchy checks; keep `facts_paths` and the module importable; run `validate_review_staging.py --selftest` and the plan_readiness import check; expect GREEN [class: IMPLEMENTATION_REQUIRED]
- [ ] Sync `agents/skills/review-staging/SKILL.md` to the surviving schema: every documented requirement the shrink removed is either deleted from the skill or listed as validator-warn-only, so the skill never documents a check the validator no longer enforces; sweep for stale requirement prose [class: IMPLEMENTATION_REQUIRED]
- [ ] Lessons hub: create `scripts/lessons.py` with subcommands `index`, `adopt`, `classify`, `migrate`, `recall`, and `selftest` (per-module or `--all`) owning ALL lessons CLI dispatch; the five existing modules stay in place as importable libraries (their constants and helpers keep their importers working: `scripts/skill_gate.py` imports `lessons_corpus` and `lessons_recall`, `scripts/hooks_log_summary.py`'s pinned recall-schema comment keeps matching `lessons_recall.py` constants, and the cursor recall wrapper's inline import of `lessons_recall.PROJECT_CORPUS_REL` keeps resolving), and each loses only its standalone `__main__` CLI entry block, which moves into the hub; `scripts/lessons_corpus.py` remains the shared-primitives module and gains no CLI duty; the existing runtime symlinks for the five modules stay valid because the files persist [class: IMPLEMENTATION_REQUIRED]
- [ ] Switch the consumers: the THREE CLI-dispatch wrappers (`agy.sh`, `claude.sh`, `codex.sh`) call the hub; `cursor.sh` is deliberately NOT switched because its inline family-index build has no hub subcommand equivalent and switching it would regress Cursor's only recall channel; it keeps its inline import of the retained `lessons_recall` library, which is exactly the import-level compatibility the library-retention bullet preserves (gate G12 witnesses the three switched wrappers and deliberately excludes `cursor.sh`). There is NO copy-deploy step for the wrappers: per the README install table (agents/hooks/lessons-recall/README.md, verified live 2026-09-20) the recall hooks are per-agent symlinks into the repo wrappers, so repo edits propagate without copying; verification is G9's resolve-check loop, and on a host where a hook was copy-installed the run records a one-time `cp` sync or re-symlink instead; update the lessons entry-point references in learn, lessons-migrate, and done (the Step 1 learn-blocked paragraph's `lessons_adopt.py --tag-unclassified` manual remedy line, NOT Step 4a, which references `check_lesson_scope.py`; the remedy must switch to the hub form because direct module invocation becomes a silent no-op once the `__main__` block moves to the hub) to the hub form; deploy `scripts/lessons.py` to `~/.ai-playbook/scripts/` and verify with `cmp -s` [class: IMPLEMENTATION_REQUIRED]
- [ ] Verify the consolidation end state: every import-level consumer still resolves (`python3 -c "import sys; sys.path.insert(0, 'scripts'); import skill_gate"` and the hub selftests), no lessons module retains a `__main__` dispatch (the G13 gate), and any caller the sweep still finds that cannot switch is reported rather than silently left on a dead entry path; run `python3 scripts/lessons.py selftest --all`; expect GREEN [class: REPOSITORY_TEST]
- [ ] Run the full python suite set from Evaluation Criteria and `bash scripts/check_maintenance_pins.sh`; expect GREEN [class: REPOSITORY_TEST]
- [ ] Commit: `scripts+skills: staging validator shrink and single lessons entry point` [class: IMPLEMENTATION_REQUIRED]
