# Plan: Done closeout target state, learn-plus-one-commit

- Date: 2026-10-11
- Status: draft v8
- Origin: docs/history/backlog/2026-10-11-done-target-state-learn-commit-closeout.md
- Entry: docs/history/backlog/PLAN-PROMPTS.md `done-target-state-learn-commit-closeout`
- Work type: plan-authored cross-surface machinery removal (operator-directed)

## Terms

- Disposition classes, fixed by the origin entry: **retained core** (learn capture; the single landing carrying work plus lessons), **automated** (mechanical decisions collapse into one script invocation with zero agent inference and no skill text to read), **demoted or deleted** (checks whose ledger record shows zero or negative net catches), **relocated** (duties owned by another skill's lane move there).
- Closeout step stack: the done skill's operative sequence (Step 0 lock and setup, Step 1 learn, the two sweep-gate runs, Steps 2 through 2.75, the Step 3 commit ladder, Steps 4 and 5, Step 6 release, Step 7 report).
- The runner: one new thin orchestrator script `scripts/done_run.sh` with three subcommands (`setup`, `commit`, `finalize`) that compose existing commands; it adds no gate, no ledger, no required ceremony, and owns no new predicate (admission note under Gate delta).
- The flip: the Task 4 change that deletes the `pre-docs` and `pre-commit` sweep phases and makes `landing` the only sweep run.
- Landing boundary: the point in the closeout where the retained sweep run gates the staged set before the single landing commit.
- Run roster: the closed list of gates one sweep phase executes, enumerated by the sweep lib's gate registry.
- Warning posture: a gate that reports its finding as a warning line and never refuses the run.
- Demotion program: the landed closeout-gate demotion program whose landing discipline is one gate per change, each demotion carrying its own ledger row update at its own evidence intake.
- Ordering rider: this plan's execution preflight, which verifies the sibling plan's implementation arms before starting (the execution prelude before Task 1).
- From-holder arm: the sibling plan's `--from-holder` release credential arm on the lock script's release subcommands, sanctioned when exports are lost with the recorded holder verifiably alive.
- Rearm-on-touch: the advisory pre-closeout check that classifies scheduler carrier state; echo-and-continue, never blocking.
- Fold-in clause, from the entry prompt verbatim: this plan dispatched before `done-closeout-lock-span-and-output-cost` executed, so that plan's compression arms fold into this classification and its own landing prunes its entry.

## Why

The operator set the target state directly: a done run is a review-for-learning plus one commit carrying work and lessons, minutes-max (origin row, operator direction 2026-10-11). Today a clean closeout walks a 723-line, seventeen-section skill: an agent-inference Step 0 (marker recipe, manifest writer, classification flags, partial-setup resume), two sweep-gate runs (eight and ten executed slots; seventeen unique gates with plans-archive-twin deduped, plus two session-level gates classified separately), a five-part Step 2 verification block, three judgment steps (2.5, 2.6, 2.75), a nine-item commit ladder with six guard paragraphs, and separate skills/docs/facts commit passes, plus the finalize-and-release ceremony. The machinery blocker audit rates this stack the number 3 blocker family, priority 15, rising, with false-blocking exceeding true catches on the staging, reverse-squash, archive, and docs-branch witness gates (docs/maintenance/machinery-blocker-audit-2026-10-09.md family 3). The ledger confirms: `run-manifest-writer` 4 incidents, 0 catches; `post-landing-staging` 5 incidents, 2 catches; `backlog-inbox` 1 incident, 1 override, 0 catches; `vim-swap-sweep`, `instruction-size`, `description-length` have no ledger rows at all. The first cost plan (landed cf43eec48) kept every step and predicate; this plan owns moving and removing them.

## Gist & Examples

A clean closeout after this plan reads, in the skill text: run the setup script (one line out: locked, marker, manifest, swept), run learn, run the commit script (which executes the one landing sweep over the staged set, then the docs-branch sync under its runner-owned lock span, then makes the one landing commit carrying work plus lessons, with learn's commits recorded by receipt in the ledger, and walks the side repos), run the finalize script (manifest complete, checkpoint removed, locks released, status free), write the report. The spine has no standalone sweep or sync invocation: both live inside the commit subcommand at their today relative positions (sweep gates the staged set, the sync publishes review docs, the landing commit carries work plus lessons). Every mechanical decision inside those scripts is fail-loud with named errors; the agent's inference lives only in learn and in the staging decisions the commit script surfaces.

## Outcome

The classification of every done-skill step and sub-check, landed:

| Step or sub-check | Disposition | Lands as |
|---|---|---|
| Step 0 lock acquire, rearm-on-touch echo, worktree residue sweep | automated | `done_run.sh setup` composes the existing lock, rearm, and sweep invocations |
| Step 0 pre-lock review-candidate classification (emit-foreign-candidates and the owned-claims decision) | retained inference + automated backstop | the agent classifies the staging corpus before the lock as today and feeds the decision to the setup subcommand as claims; the writer's claim-or-foreign abort stays the fail-loud backstop |
| Step 0 runtime-helper drift advisory (deploy check mode) | automated | joins the setup subcommand's composition as its echo-and-continue advisory line, per the rearm-on-touch posture |
| Step 0 run-start marker + run manifest write + partial-setup resume | automated | same setup subcommand; the fail-atomic block moves into script behavior; the resume procedure classifies and surfaces the matching remedy (recover, adopt, finalize, disposition), requiring the operator's explicit choice for adopt or disposition, never adopting implicitly |
| Step 0 revert-set, adoption, disposition, recovery ceremony text | relocated | the sweep-gates lib's own usage text and module docs own the semantics; the skill links, never restates (the sibling plan's module split owns the generated inventories) |
| Step 1 learn harvest | retained core | unchanged invocation; learn keeps its own commit contract and prints its receipts |
| Owned-commits ledger | automated append + retained receipt handoff | the fused exact-SHA capture moves into the commit subcommand's own append; the agent writes learn's printed receipts to a file under the run's done-session directory immediately after learn, and the commit subcommand accepts `--learn-receipts-from <file>`, appending them to the ledger post-hoc-from-receipt, one line per receipt, before its in-script landing re-run |
| Pre-docs sweep run + pre-commit sweep run (two runs, eighteen executed gate slots) | demoted to one | a single `done_sweep_gates.sh landing` run at the landing boundary carries the retained set below |
| backlog-inbox gate | demoted (0 catches, 1 incident, 1 override; already report-not-fail) | removed from the run roster; the filing duty stays with receiving-review's capture step |
| vim-swap-sweep gate | demoted (no ledger row) | removed from the run roster; periodic maintenance-survey advisory |
| instruction-size, description-length gates | demoted (no ledger rows) | warning posture inside the landing run; they report, never block |
| docs-tmp-sweep gate | retained | landing roster; it is the sole governor of run-start marker pruning and keeps that duty |
| sensitive-data-scan, em-dash-scan, doc-registry, review-staging, plan-readiness, foreign-staging, post-landing-staging (staged leg), plans-root-claim-fence, archive-ceremony, execute-plan-closeout, plans-archive-twin (deduped to one run slot), confluence-hygiene (conditional) | retained | unchanged predicates, one run; the entry's two witnessed frictions assessed at authoring time: the sensitive-data-scan's credential-pattern false-positive class (origin row docs/history/backlog/2026-10-11-done-sensitive-scan-neutral-token-assignment.md) recurs at token-assignment time and its remedy lands through that row's own lane, while the scan's retention cost stays bounded because its findings resolve before staging; the docs-branch interpreter floor (origin row docs/history/backlog/2026-10-11-docs-branch-python-runtime-floor.md) is adjacent to this plan's python3.14 standing constraint, which pins every plan script and the rehearsal, and the floor's own fix lands through its row's lane |
| review-thread closure, plans-root liveness (session-level conditional gates) | retained, in-session | they stay session-applied duties in the collapsed text with their receiving-review and authoring-claims links named; the runner does not execute them |
| Step 2 migration + docs sync + merge lock + verification | automated | the sibling plan's runner-owned bounded-wait spans are presupposed (Task 5 verifies the arms); the commit subcommand invokes the sync at its today position and reads its result (the execution prelude verifies the arms); the explicit sync deferral availability arm (owned-review presence check) stays skill text in the collapsed stack |
| Step 2.5 formatting rollback | automated | the commit script lists whitespace-only-diff candidates mechanically; the agent confirms the revert list in one line |
| Step 2.6 documentation cross-reference check | relocated | learn's capture contract owns cross-reference wiring at placement time; the standalone step dies |
| Step 2.75 unused-import scan | automated | the commit script runs the resolved linter over touched lintable paths, skip-note when none resolve |
| Step 3 item 0b plan-deliverable append | automated | the commit subcommand appends staged plans-root paths to the deliverables file in the same invocation |
| Step 3 item 0 baseline + item 1a foreign-dirt gate | automated | the commit subcommand runs the foreign-dirt disposition ladder (claims, report-and-leave, live-peer abort) inside the script |
| Step 3 item 0c stale-checkout adjudication | automated | the commit subcommand classifies ancestor-blob debris and index reversions mechanically, reporting restorations, never staging them |
| Step 3 item 0d missing-review-record adjudication | retained, report-only | stays a report duty in the finalize subcommand's summary assembly; never blocking, never fabricating |
| Step 3 items 1, 2, 3 guards (cached-diff, dirt regression, staged-scope) | automated | all run inside the commit script in the skill's current order; refusals are the guards' own named errors |
| Step 3 items 4, 4a, 4b (gitignored check, lesson scope audit, lessons corpus commit) | retained core | the gitignored check runs scripted; the lesson-scope audit runs in the commit script and surfaces its findings for the agent's one-line confirmation; the corpus rides the single landing commit (no separate lessons commit) |
| Step 3 items 5, 5a, 5b (staging, gate re-run, registry arms) plus the reverse-squash check-staged | automated | the commit script stages by explicit pathspec, re-runs the landing phase before committing, runs the registry digest-capture arms, and runs the reverse-squash check-staged last, immediately before the landing commit |
| Step 3 items 6 through 9 (message, HEREDOC commit, status, ledger append) | automated | the script builds the why-first message (story key from the branch, no trailers, resolve-at-use digests), makes exactly one landing commit, and appends the ledger fused to the commit; base-branch immutability stays the skill-text rule it is today, reported by the script as a warning line, never a new refusal |
| Repository scope ledger (touched-repo inventory, per-repo iteration with its own lock, never-report-unverified guard) and the header date-verification sub-check | retained core | stays skill text in the collapsed stack; the runner sequence executes per project repository as today, and the run never reports completion while a touched repository stays unverified |
| Steps 4 and 5 (skills, facts, docs repos) | automated inventory + retained commit decision | the commit subcommand walks the facts-resolved repos, reports dirty paths per repo, and executes one commit action per repo the agent confirms, re-running the landing phase's sensitive-data-scan over each staged side-repo set before that repo's commit (the today Step 4 arm carried forward) |
| Step 6 manifest finalize, checkpoint remove, lock release | automated | `done_run.sh finalize` composes the checkpoint refresh, finalize-manifest, checkpoint remove, done-lock release, merge-lock release when held, and the status-free verification; when exports are lost mid-run the finalize subcommand accepts the from-holder arm under its own recorded guards instead of re-creating a chat-context token-retention duty |
| Step 7 report + ledger and telemetry appends | retained, trimmed | the report stays the agent's; the guard-liveness and landing-cost appends move into the finalize subcommand (advisory, never blocking) |

The clean-run skill text a reader loads drops to the collapsed stack above; the target is a done skill at or under 400 total lines (wc -l) from 723, with every removed paragraph's semantics surviving in script behavior or the owning module's docs.

Gate delta: net machinery removal. Removed from the blocking roster: backlog-inbox and vim-swap-sweep (run-roster removals, each with its own ledger row update at landing per the demotion program's landing discipline), instruction-size and description-length demoted to warning posture, the Step 2.6 standalone step deleted into learn, the Step 2.5 and 2.75 judgment passes mechanized into the commit script. Added: the `done_run.sh` runner, which is a composition of existing commands and owns no gate, no ledger, no lock family, and no new refusal class: every refusal it can print is one of the composed commands' existing named errors, except the relocated one-for-one refusals (the foreign-dirt ladder's live-peer abort, the cached-diff leaked-revert stop, and the confirmation-gated formatting revert), each of which relocates an existing skill-text refusal verbatim into the script with no new predicate or vocabulary, and the admission protocol's incident is this plan's own origin row (operator cost review 2026-10-11; the audit's family 3), expected frequency every done run, false-positive cost none (composition cannot refuse what its parts do not), sunset review 2027-01; and the ordering rider, carried by the plan-execution prelude and never inside `done_run.sh` (admission: incident is this plan's dispatch before the sibling plan executed, per the fold-in clause; expected catch once at the first execution attempt; false-positive cost none once the sibling's arms persist on main; sunset vacuously green at that point). No replacement machinery: the demotion program's conclusion binds, no new ledger, gate, or ceremony manages the simplification.

## Assumptions

- Resolved by the entry (already-confirmed operator decision, cited source: PLAN-PROMPTS entry `done-target-state-learn-commit-closeout`, operator direction 2026-10-11): the four-disposition classification, the one-commit topology, the two-sweeps-to-one shrink, minutes-max target.

Decision points requiring a grill: none remain. (Material decision points, each resolved by the entry's own text: which steps survive, recorded above with the entry as the source; where relocated duties go, fixed by the origin row's fix shape; the demotion evidence base, fixed by the ledger and the audit.)

- The sibling plan (`done-closeout-lock-span-and-output-cost`) is landed as a plan document (755ca1572, r3-certified at 9e2d3a1d) and amended post-landing (879dfe41a, r4 delta-certified ready=yes; current bytes digest b2e4f94a), but NOT yet executed: its runner-owned lock spans, from-holder arm, bounded reports, and module splits are tasks, not main bytes. The execution prelude's ordering rider verifies the arms and gates execution on them, accepting the sibling document's presence at the plans root or its completed archive twin digest-verified against the latest ready=yes certification record (the r4 delta, not the landing's r3 digest).

## Standing constraints

- All authoring and review happens in the worktree; main commits need the repository merge lock; staging is by explicit pathspec only; peer working-tree dirt is never staged, committed, reset, or reverted.
- Plan scripts run under `python3.14` (bare python3 is 3.9.6 and crashes on `X | Y` annotations); pytest suites are the documented exception, running under the repo-standard `python3 -m pytest` (pytest is not importable under python3.14 on this host), and every plan-created test file carries `from __future__ import annotations`.
- Machinery admission: this plan adds no gate, validator, lock, ledger, or required ceremony; the runner composes existing commands (admission note in Gate delta).
- Bounded repair: when a landing blocks a lane, the allowed responses are a bounded retry, skip-with-report, or park-for-operator.

## Evaluation Criteria

- A rehearsal clean-run closeout on a scratch checkout completes in minutes of wall clock (target under 10, from run start to released locks, recorded in the run transcript), executes exactly one landing commit carrying work plus lessons, plus learn's commits recorded by receipt in the ledger, one sweep run, and reports free locks.
- The done skill's operative text is at or under 400 total lines (wc -l) with the collapsed step stack; every removed paragraph's contract is demonstrably owned by script behavior, the owning module's docs, learn, or the survey.
- The demoted gates are absent or warning-only in the landing run's roster and the ledger carries their landing-dated row updates.
- Every retained gate's OUTCOME in the rehearsal equals the pre-change baseline run's OUTCOME on an identically seeded scratch tree (the baseline generation runs from its own materialized pre-change copy).

## Review Scope

- The classification table above (every done-skill step and sub-check appears exactly once, including docs-tmp-sweep, the two session-level gates, and Step 3 items 0b through 5b).
- The rehearsed carriers:
  - `scripts/done_run.sh` (new runner: setup, commit, finalize subcommands) and its suite `scripts/test_done_run_wrapper.py` (hermetic fixture repo, env pins per the wrapper-suite pattern).
  - `scripts/done_sweep_gates.sh` landing phase (new roster; pre-docs and pre-commit phases retained for compat during the transition, deleted at the flip) and the `list-gates` metadata exit extended to accept a phase argument.
  - `agents/skills/done/SKILL.md` rewrite (collapsed stack) and every machine consumer of its bytes re-aimed in the same change.
  - the learn capture-contract placement paragraph, wherever the sibling plan's split holds it at execution time (relocated cross-reference duty) and the peer-skill reference migration (learn, plans, execute-plan, docs-branch, doc-hierarchy, review-staging, confluence-page-sync, receiving-review).
  - `docs/maintenance/` survey advisory note (periodic arms for the demoted sweeps).
- The pins surfaces: `scripts/check_maintenance_pins.sh` done rows re-aimed to the collapsed sentences; the pins suite joins the validation block.
- Out of scope: learn's own step stack (the sibling plan splits it), execute-plan driver guards (owned by the closeout-gate-demotion-continuation entry), the docs-branch runner internals (owned by the sibling plan), the sweep-gates lib's retained gate predicates (unchanged).

## Validation Commands

```bash
# Fail-closed block: every check aborts non-zero on miss or forbidden match.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# Abort helpers: a bare `! cmd` pipeline can never abort (errexit ignores
# inverted pipelines), so every forbidden-match check runs through these.
forbid_grep() { # flags pattern file: abort on any match or scan error
  local flags="$1" pat="$2" file="$3"
  local rc=0
  grep $flags -q -- "$pat" "$file" || rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "forbidden match: $pat in $file" >&2
    exit 1
  elif [ "$rc" -gt 1 ]; then
    echo "scan error (rc=$rc): $pat in $file" >&2
    exit 1
  fi
}
forbid_rg() { # pattern paths...: abort on match (rc 0) or scan error (rc > 1)
  local pat="$1"
  shift
  local rc=0
  rg -n "$pat" "$@" || rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "forbidden match: $pat" >&2
    exit 1
  elif [ "$rc" -gt 1 ]; then
    echo "scan error (rc=$rc): $pat" >&2
    exit 1
  fi
}

# 1. The runner exists, is executable, composes existing commands, and adds
#    no new refusal vocabulary beyond its parts' named errors plus the three
#    relocated one-for-one refusals the Gate delta names.
test -x scripts/done_run.sh
bash -n scripts/done_run.sh
for sub in setup commit finalize; do grep -q "$sub)" scripts/done_run.sh; done
grep -q "done-lock.sh" scripts/done_run.sh
grep -q "done_sweep_gates.sh" scripts/done_run.sh
grep -q "done_sweep_gates_lib.py" scripts/done_run.sh

# 2. Roster shape through the tasked listing interface: the landing roster
#    keeps the retained gates, drops the removed two, and marks the two
#    warning-posture gates.
ROSTER="$(mktemp)"
bash scripts/done_sweep_gates.sh list-gates landing > "$ROSTER"
for gate in docs-tmp-sweep confluence-hygiene sensitive-data-scan em-dash-scan doc-registry review-staging plan-readiness foreign-staging post-landing-staging plans-root-claim-fence archive-ceremony execute-plan-closeout plans-archive-twin; do
  grep -qx "$gate" "$ROSTER"
done
forbid_grep -qx "backlog-inbox" "$ROSTER"
forbid_grep -qx "vim-swap-sweep" "$ROSTER"
grep -qx "instruction-size (warning)" "$ROSTER"
grep -qx "description-length (warning)" "$ROSTER"
rm -f "$ROSTER"

# 3. The skill text collapsed: no inline lock ceremony, no marker or writer
#    recipe signatures (continuation or single-line form); the three runner
#    subcommands are the operative spine.
LINES=$(wc -l < agents/skills/done/SKILL.md)
test "$LINES" -le 400
forbid_grep -qF "merge-wait-acquire" agents/skills/done/SKILL.md
forbid_grep -qF 'run-start-$(date' agents/skills/done/SKILL.md
forbid_grep -qF 'printf '"'"'%s\n'"'"' "$(date -u +%s) $REPO_HASH $$"' agents/skills/done/SKILL.md
forbid_grep -qE '(^|[[:space:]])write-manifest([[:space:]]|$)' agents/skills/done/SKILL.md
grep -q "done_run.sh setup" agents/skills/done/SKILL.md
grep -q "done_run.sh commit" agents/skills/done/SKILL.md
grep -q "done_run.sh finalize" agents/skills/done/SKILL.md
grep -q "docs_branch_sync.sh" agents/skills/done/SKILL.md

# 4. Relocations landed both directions, on needles that are red today.
rg -qF "cross-reference wiring for session-created guidance happens at placement time, before the done boundary" agents/skills/learn/
forbid_grep -qF "Step 2.6" agents/skills/done/SKILL.md

# 5. No living surface still points at the deleted phases or the stale
#    done-flow claim, the phases are dead where they live (roster keys,
#    dispatch, usage text), and every machine consumer re-aim is witnessed.
forbid_rg "pre-docs sweep|pre-commit sweep" agents/skills/ docs/maintenance/ README.md docs/AGENTS.md projects/.ai-playbook/ scripts/ -g '!docs/maintenance/machinery-blocker-audit-2026-10-09.md' -g '!agents/skills/maintenance/templates-CHANGELOG.md' -g '!scripts/gate_liveness_ledger.json' -g '!scripts/machinery_registry.json'
forbid_rg 'done_sweep_gates\.sh pre-(docs|commit)' README.md agents/ scripts/ docs/AGENTS.md docs/maintenance/ projects/.ai-playbook/ -g '!docs/maintenance/machinery-blocker-audit-2026-10-09.md' -g '!agents/skills/maintenance/templates-CHANGELOG.md' -g '!docs/maintenance/document-registry.md' -g '!scripts/gate_liveness_ledger.json' -g '!scripts/machinery_registry.json'
forbid_rg 'pre-docs' agents/skills/ docs/maintenance/ README.md docs/AGENTS.md projects/.ai-playbook/ scripts/ -g '!docs/maintenance/machinery-blocker-audit-2026-10-09.md' -g '!agents/skills/maintenance/templates-CHANGELOG.md' -g '!docs/maintenance/document-registry.md' -g '!scripts/gate_liveness_ledger.json' -g '!scripts/machinery_registry.json'
forbid_rg 'pre-commit (sensitive-data|audit|guard|scan|phase|gate)' agents/skills/ docs/maintenance/ README.md docs/AGENTS.md projects/.ai-playbook/ scripts/ -g '!docs/maintenance/machinery-blocker-audit-2026-10-09.md' -g '!agents/skills/maintenance/templates-CHANGELOG.md' -g '!docs/maintenance/document-registry.md' -g '!scripts/gate_liveness_ledger.json' -g '!scripts/machinery_registry.json'
forbid_rg '"pre-(docs|commit)":' scripts/
if bash scripts/done_sweep_gates.sh pre-docs >/dev/null 2>&1; then echo "pre-docs phase still dispatchable" >&2; exit 1; fi
if bash scripts/done_sweep_gates.sh pre-commit >/dev/null 2>&1; then echo "pre-commit phase still dispatchable" >&2; exit 1; fi
grep -E '^\| .scripts/done_sweep_gates.sh.' README.md | grep -q landing
forbid_grep -qF "run by the done flow" agents/skills/receiving-review/SKILL.md
python3 -m pytest scripts/test_done_run_wrapper.py scripts/test_done_sweep_gates_wrapper.py scripts/test_done_sweep_gates_lib.py scripts/test_docs_branch_sync.py scripts/test_lessons_recovery_contract.py scripts/test_harness_policy_contract.py
bash scripts/check_maintenance_pins.sh

# 6. Ledger rows updated at the demotions: pinned to the plan's landing date
#    and content-checked as demotion rows.
python3.14 - <<'PY'
import json
d = json.load(open("scripts/gate_liveness_ledger.json"))
for gate in ("backlog-inbox", "vim-swap-sweep", "instruction-size", "description-length"):
    rows = d["guards"].get(gate, {}).get("rows", [])
    assert any(
        isinstance(r.get("date"), str) and r["date"] >= "2026-10-11"
        and "roster" in str(r.get("note", "")).lower()
        for r in rows
    ), f"{gate}: no landing-dated demotion ledger row"
PY

# 7. Hygiene and em-dash policy over the touched set, plus the pre-round gate.
bash scripts/check-no-em-dash.sh touched
bash scripts/scan-public-hygiene.sh
python3.14 scripts/plan_readiness.py docs/history/plans/2026-10-11-done-target-state-learn-commit-closeout.md --pre-round

echo "validation: all checks passed"
```

## Tasks

### Execution prelude (the ordering rider, before Task 1)

This plan executes after the sibling plan's implementation lands on main; the rider runs here, before any task. The preflight verifies the arms, not the document: `git grep -q "from-holder" scripts/done-lock.sh`, the internal bounded-wait acquire present in `scripts/docs_branch_sync.sh`, the bounded-report emission helper present in `scripts/done_sweep_gates_lib.py`, and the sibling's module split executed or dissolved, witnessed mechanically: every `step-*.md`/`sweep-gates-*.md` file present under the done skill directory is named by a committed dispatch site (`git grep -qF <filename>` over agents/skills/ and scripts/), and the arm also passes when no such file exists; the sibling plan document must be present at the plans root or its completed archive twin, digest-verified against the sibling's latest ready=yes certification record (currently the r4 delta-certified bytes, not the landing's r3 digest). Any missing arm refuses the start naming "execute the sibling plan first" as the remedy.

Primary class anchors:
- `from-holder` in `scripts/done-lock.sh`, the release-credential arm the rider verifies present
- `from-holder` in `docs/history/plans/2026-10-10-done-closeout-lock-span-and-output-cost.md`, the sibling plan's recorded guards

- [x] Ordering rider enforced before any task: verify each sibling arm on main (from-holder in the lock script, internal acquire in the sync runner, bounded-report helper in the lib, the module-split arm: each existing `step-*.md`/`sweep-gates-*.md` file under the done skill named by a committed dispatch site, absence of all such files also passing), refuse to start while any is missing naming the sibling plan as the prerequisite, and accept the sibling document at the plans root or its completed archive twin digest-verified against the latest ready=yes certification record [class: IMPLEMENTATION_REQUIRED]

### Task 1: The runner, setup subcommand

Step 0's mechanical core becomes one invocation. The setup subcommand composes, in order: the rearm-on-touch echo (existing script, advisory posture unchanged), the done-lock `wait-acquire` with the short agent wait and the outcome-contract handling the skill prescribes today, the runtime-helper drift advisory (the deploy check-mode invocation, echo-and-continue, per the rearm posture), the worktree residue sweep (existing script, fail-open posture unchanged), the run-start marker write (the existing content-bearing recipe), and the run manifest write (the existing writer invocation with the run's owned and foreign claims as arguments). The fail-atomic block binding, the empty-echo abort, and the partial-setup resume procedure move into the script's behavior and its usage text; the resume arm classifies a found boundary and surfaces the matching remedy, requiring the operator's explicit choice for adopt or disposition. The script prints one status line plus the exports (lock dir, token, marker path, manifest path, run id) the later subcommands consume, and every refusal is the composed command's own named error. A `--from-manifest <run_id>` flag lets a resumed session re-enter an existing boundary through the same script.

Primary class anchors:
- `setup` in `scripts/done_run.sh`, the subcommand dispatch site
- `wait-acquire` in `scripts/done-lock.sh`
- `write-manifest` in `scripts/done_sweep_gates_lib.py`

- [x] Write `scripts/done_run.sh` with the setup subcommand composing rearm-on-touch, done-lock wait-acquire, the runtime-helper drift advisory, the residue sweep, the marker recipe, and the manifest writer, echoing the composed exports and failing loud with each part's named error [class: IMPLEMENTATION_REQUIRED]
- [x] Partial-setup resume: given a found marker or manifest from an interrupted attempt, expects the setup subcommand to classify the boundary and print the matching remedy (recover, adopt, finalize, disposition), performing only the read-only classification until the operator's explicit choice, never adopting implicitly [class: REPOSITORY_TEST]
- [x] Refusal passthrough: given a held done lock, expects the setup subcommand to exit non-zero with the lock script's own blocked evidence and outcome line, writing no marker and no manifest [class: REPOSITORY_TEST]
- [x] Create `scripts/test_done_run_wrapper.py` with a hermetic fixture repo; every test pins `DONE_LOCK_ROOT`, `MERGE_LOCK_ROOT`, `DONE_LOCK_SCRIPT` (repo-local copy), `DONE_SWEEP_REPO_ROOT`, `DONE_SWEEP_RUNTIME_HOME`, and `DONE_SWEEP_USER_FACTS`, and every `resolve_script` env override in `done_sweep_gates_lib.py` except `DONE_LOCK_SCRIPT` (pinned separately to the repo-local copy), and unsets or fixture-pins every `DONE_LOCK_*` and `MERGE_LOCK_*` variable either lock script resolves (dir, token, holder pid, poll, stale, incomplete, and dead-holder-grace seconds) plus `DOCS_SYNC_NOW` and `DOCS_SYNC_TRACE_FILE` whenever a test drives the real sync stage; the runner owns the short agent wait itself, reading `DONE_LOCK_AGENT_MAX_WAIT_SECS` (at today's 90-second default) and passing it to `wait-acquire --max-wait`; all of these, plus the runner's own `DONE_LOCK_AGENT_MAX_WAIT_SECS`, are unset or fixture-pinned into the fixture tmp tree with a fixture facts document, so no test reads or writes the host lock home, runtime home, personal facts, or host-resolved gate validators [class: REPOSITORY_TEST]
- [x] Run → expect RED: the runner and its suite are absent and the skill still carries the inline recipes [class: REPOSITORY_TEST]
- [x] Write minimal implementation, then Run → expect GREEN on `python3 -m pytest scripts/test_done_run_wrapper.py` [class: REPOSITORY_TEST]
- [x] Commit: `feat: done_run.sh setup composes the closeout's mechanical prologue` [class: IMPLEMENTATION_REQUIRED]

### Task 2: The landing sweep, one run

The sweep lib gains a `landing` phase carrying the retained roster from the classification table; `instruction-size` and `description-length` move to warning posture inside it; `backlog-inbox` and `vim-swap-sweep` leave the per-run roster (their duties live with receiving-review's capture step and the periodic survey). The `list-gates` metadata exit accepts a phase argument (`list-gates landing`) and prints the phase's roster one gate per line, warning-posture gates suffixed ` (warning)`. The pre-docs and pre-commit phases stay shimmable during the transition and are deleted at the flip task, where the parity comparison becomes a run-once rehearsal artifact of Task 5 (never a standing test). The two-sweeps-to-one restructure is one operator-directed structural change, sanctioned by the origin row's operator direction; each of the four demotions still carries its own landing-dated ledger row update naming its own gate's evidence in the same change, preserving the demotion program's evidence-intake isolation inside the one sanctioned restructure.

Primary class anchors:
- `landing` in `scripts/done_sweep_gates.sh`, the phase dispatch site
- `list-gates` in `scripts/done_sweep_gates.sh`, the metadata exit
- `PRE_DOCS_GATES` in `scripts/done_sweep_gates_lib.py`, the roster registry

- [x] Add the landing phase with the retained roster; demote instruction-size and description-length to warning lines; remove backlog-inbox and vim-swap-sweep from the roster, each with its own ledger row update dated at landing naming the roster change [class: IMPLEMENTATION_REQUIRED]
- [x] Extend `list-gates` to accept a phase argument printing that phase's roster one gate per line with warning-posture gates suffixed; document the interface in the script usage text [class: IMPLEMENTATION_REQUIRED]
- [x] Roster parity (run-once, Task 5 harness): given the same scratch tree, expects the landing run's per-gate OUTCOME lines to equal the union of a baseline pre-docs-plus-pre-commit pair for every retained gate, enumerated from the lib's registry minus the named demotions, with plans-archive-twin deduped to one slot and the demoted gates absent or warning-only [class: REPOSITORY_TEST]
- [x] Warning-posture run-path witness: given a fixture breaching both demoted gates (an over-budget instruction entrypoint and an over-length folded description), expects the landing run to exit 0 with a warning line naming each gate, while the same fixture under a baseline pre-commit run refuses; roster membership and absence assertions join the lib suite so the metadata check is not the only standing roster guard [class: REPOSITORY_TEST]
- [x] Survey note: the periodic arms (vim-swap sweep, backlog-inbox filing audit) are recorded in the maintenance survey's advisory documentation so the duty outlives the roster removal; name the arms, not the retired runs, so the note never carries the deleted phase names [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: no landing phase exists today; `list-gates landing` exits 0 printing the legacy union roster (the extra argument is ignored), and check 2's negative and warning-suffix greps fail until the extension lands [class: REPOSITORY_TEST]
- [x] Write minimal implementation, then Run → expect GREEN on `python3 -m pytest scripts/test_done_sweep_gates_wrapper.py scripts/test_done_sweep_gates_lib.py` [class: REPOSITORY_TEST]
- [x] Commit: `feat: one landing sweep run, demoted roster per the ledger` [class: IMPLEMENTATION_REQUIRED]

### Task 3: One landing commit

The commit subcommand owns the collapsed Step 3: stage by explicit pathspec from the run's owned set, append staged plans-root paths to the deliverables file, run the stale-checkout adjudication, then the cached-diff and dirt-regression guards, the staged-scope guard, and the foreign-dirt disposition ladder inside the script (that enumeration is the authoritative composed order and matches the skill's current relative order), then list formatting-only-diff candidates for one-line confirmation, run the unused-import pass over touched lintable paths when a linter resolves, run the lesson-scope audit when the lessons corpus is touched, execute the landing phase over the final staged set (the closeout's one sweep run), then invoke the docs-branch sync (the sibling plan's runner-owned lock span; the migration precedes it when the session runs in an ad-hoc worktree), then run the registry digest-capture arms, then the reverse-squash check-staged as its own ordered step at its today observation point, immediately before the landing commit, build the why-first message (story key from the branch, no trailers, resolve-at-use digests), make exactly one landing commit carrying work plus lessons, and append the owned-commits ledger line fused to the commit; base-branch immutability stays the skill-text rule, reported by the script as a warning line when an amend of a base-reachable commit is attempted, never a new refusal. The subcommand then walks the facts-resolved side repos (provisioned as sandbox repos in tests), reports dirty paths per repo, and executes one confirmed commit action each, re-running the sensitive-data-scan over each staged side-repo set before that repo's commit. Learn's own commits remain learn's: after learn, the agent writes learn's printed receipts to `<tmp_dir>/done-session/learn-receipts-<run_id>.txt`, and the commit subcommand takes `--learn-receipts-from <file>`, resolving each receipt sha in the run repository (`git rev-parse -q --verify '<sha>^{commit}'`) and appending only same-repository receipts to the ledger post-hoc-from-receipt before its in-script landing re-run, skipping an unresolvable cross-repo sha with a one-line note, so the landing sweep's doc-registry gate observes them. Task 3 also lands the learn-side relocation sentence: learn's capture contract gains the sentence "cross-reference wiring for session-created guidance happens at placement time, before the done boundary" in whatever file carries the placement paragraph at execution time (the sibling plan's split may hold it in a learn module; the validation needle greps the learn skill directory, not one file), and the done skill's Step 2.6 dies at the flip.

Primary class anchors:
- `commit` in `scripts/done_run.sh`, the subcommand dispatch site
- `check-staged` in `scripts/reverse_squash_guard.py`
- `classify` in `scripts/revert_set_classifier.py`

- [x] Implement the commit subcommand with the guards inlined in the skill's current order, the single landing commit, the fused ledger append, and the side-repo walk over sandbox-provisioned repos in tests [class: IMPLEMENTATION_REQUIRED]
- [x] Single-commit witness: given a session with work plus lessons and learn receipts reported separately, expects exactly one landing commit carrying work plus lessons, learn's commits recorded by receipt, every same-repository receipt line present in the ledger, and exactly one landing-phase execution plus one sync invocation in the run trace [class: REPOSITORY_TEST]
- [x] Receipt skip arm: given a receipts file holding one resolvable same-repo sha and one sha that fails resolution, expects the ledger to contain only the same-repo line and stdout to carry the one-line skip note [class: REPOSITORY_TEST]
- [x] Sync wiring: given a clean session, expects the commit subcommand's trace to contain the docs-branch sync stage between the landing sweep and the landing commit, with the sync's own runner-owned lock span and a pass or named-refusal outcome [class: REPOSITORY_TEST]
- [x] Guard refusals: given a staged foreign path, a reverse-squash signature, a dirt regression, a staged diff deviating from the classified revert set (the cached-diff leaked-revert stop), or a staged path outside the run's owned set (the staged-scope guard), expects the named guard's refusal and no commit [class: REPOSITORY_TEST]
- [x] Formatting candidates: given a whitespace-only diff, expects the candidate list output and no revert without the confirmation flag [class: REPOSITORY_TEST]
- [x] Relocation: the file carrying learn's placement paragraph at execution time gains the cross-reference-at-placement-time sentence verbatim; the done skill's Step 2.6 dies at the flip [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED against today's ladder (no runner subcommand exists) [class: REPOSITORY_TEST]
- [x] Write minimal implementation, then Run → expect GREEN on `python3 -m pytest scripts/test_done_run_wrapper.py` [class: REPOSITORY_TEST]
- [x] Commit: `feat: done_run.sh commit collapses the closeout commit ladder` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Finalize, the flip, and the consumer migration

The finalize subcommand composes the Step 6 ceremony (checkpoint refresh, finalize-manifest, checkpoint remove, done-lock release, merge-lock release when held, status-free verification), assembles the Step 7 report inputs (including the report-only missing-review-record scan result), and runs the advisory appends (guard-liveness ledger, landing-cost telemetry, both never blocking); when lock exports are lost mid-run it accepts the sibling plan's from-holder arm under its own recorded guards. Then the skill rewrite and the one-pass consumer migration: the done skill's operative stack becomes setup, learn, commit (which owns the one landing sweep over the staged set, the docs-branch sync at its today position between sweep and landing commit, and the single landing commit), finalize, report; the pre-docs and pre-commit phases die at this flip; every machine consumer of the done skill's bytes re-aims in the same change; every peer-skill reference to the deleted phase names updates to the landing phase or its owning surface; the target is at or under 400 total lines.

Primary class anchors:
- `finalize` in `scripts/done_run.sh`, the subcommand dispatch site
- `finalize-manifest` in `scripts/done_sweep_gates_lib.py`
- `release-repo` in `scripts/done-lock.sh`

- [x] Implement the finalize subcommand with the composed ceremony, the report-input assembly, the advisory appends, and the from-holder acceptance [class: IMPLEMENTATION_REQUIRED]
- [x] Rewrite `agents/skills/done/SKILL.md` to the collapsed stack and delete the pre-docs and pre-commit phases in the same change; the end shape is one readable spine: the sibling plan's `step-*.md` and `sweep-gates-*.md` module files dissolve in the same change (their operative bodies are either superseded by the collapsed stack or already landed by the sibling's execution), their consumers re-aim back to SKILL.md, and no dispatchable module body survives the flip; link every removed paragraph's contract to its owning surface in the diff commentary using the owners' names (the concept names the removed recipes carried stay usable in prose); the collapsed spine names its three invocations verbatim (`done_run.sh setup`, `done_run.sh commit`, `done_run.sh finalize`) and the sync reference (`docs_branch_sync.sh`) so check 3's needles are reachable from the prescribed text [class: IMPLEMENTATION_REQUIRED]
- [x] Same-change machine-consumer re-aim: sweep `rg -n "done/SKILL.md|done skill|done/step-|done/sweep-gates-" scripts/ agents/skills/ docs/maintenance/ README.md -g '!docs/maintenance/document-registry.md'` (dated append-only registry rows are verify-only, never re-aimed) and re-aim every byte consumer: the docs-branch suite's skill-sentence assertions, the lib's checkpoint and phase-slice docstring anchors, the lessons-recovery anchor pairs, the harness-policy surface list, the survey arm's procedure-of-record pointer, and the pins rows; the touched suites and `bash scripts/check_maintenance_pins.sh` join the Task GREEN gate [class: IMPLEMENTATION_REQUIRED]
- [x] Peer-reference migration: update every phase-name reference (adjacency, bare invocation, and bare phase name) in learn, plans, execute-plan, docs-branch, doc-hierarchy, review-staging, confluence-page-sync, and the README runner row to the landing phase or owning surface; correct receiving-review's "run by the done flow" claim about the backlog-inbox location checker to the receiving-review capture step; reword the README lesson-scope validator row's done-pre-commit-audit phrase and the matching phrase in scripts/check_lesson_scope.py's header docs to the landing posture; refresh the living surfaces the check-5 needles cover (docs/AGENTS.md's em-dash arm, the projects/.ai-playbook/ session-end and consumer-catalog rows agent_workflow_guidelines.md, agent-runtime-layout.md, and development_lessons.md, the header docs of scripts/confluence-mirror-hygiene.sh and scripts/check-instruction-size.sh, plus the sweep script's and lib's usage-text phase vocabulary) to the landing phase or owning surface; disposition done's Integration Points section in the diff commentary [class: IMPLEMENTATION_REQUIRED]
- [x] Retire or rewrite the wrapper and lib tests that pin the deleted phase names onto the landing phase in the same change as the flip [class: IMPLEMENTATION_REQUIRED]
- [x] Finalize composition and from-holder arms: given a fixture session with held locks and a written manifest, expects finalize to end with both locks released, the manifest finalized, and the checkpoint absent; given lost exports with the recorded holder verifiably alive, expects the from-holder acceptance to follow the sibling plan's recorded guards [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the validation block above passes end to end [class: REPOSITORY_TEST]
- [x] Commit: `feat: done skill collapses to learn, one sweep, one commit, one finalize` [class: IMPLEMENTATION_REQUIRED]

### Task 5: The rehearsal

The ordering rider ran at the execution prelude before Task 1. The run-once rehearsal from a scratch checkout: materialize the baseline scripts from the pre-change revision into a second scratch tree (the deployed runtime home is never the baseline), pin the same hermeticity overrides as Task 1's suite plus `DONE_LOCK_SCRIPT` at each generation's own copy, seed a scratch tree with a closed session's shape, run baseline and candidate closeouts, capture the timed transcript, and diff every retained gate's OUTCOME against the baseline run on the same tree, with the roster-parity comparison as the run-once witness. Four outcomes are acceptable: full parity pass, parity with warning-posture deltas naming each, recorded stop on an environment failure (rerun once, then park), or parity failure naming the gate (fix before landing).

Primary class anchors:
- `main` in `scripts/docs_branch_sync.sh`, the presupposed runner-owned span the rehearsal verifies free
- `landing` in `scripts/done_sweep_gates.sh`, the one run the rehearsal times
- `setup` in `scripts/done_run.sh`, the rehearsal entry point

- [x] Rehearsal harness (run once from a scratch location, never committed as standing machinery): materialize both script generations into scratch trees, seed a scratch tree with a closed session's shape, run baseline and candidate closeouts under the hermeticity pins, emit the timing and the per-gate OUTCOME diff [class: REPOSITORY_TEST]
- [x] Wall-clock and commit-count gates: the candidate run completes under the minutes target with exactly one landing commit plus recorded learn receipts and both locks free [class: REPOSITORY_TEST]
- [x] Commit: `test: done target-state rehearsal transcript and parity verdict` [class: IMPLEMENTATION_REQUIRED]
