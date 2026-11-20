# Plan: machinery CLIs self-describe operand contracts at refusal time

Backlog origin: docs/history/backlog/2026-11-11-machinery-cli-operand-self-description.md
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/YYYY-MM-DD-plan-review-machinery-cli-operand-self-description-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 3h total, largest task 1h
Executed: yes (this landing c313fcd18)

## Terms

- declaration class: operand-shape constraints declared in argparse (mutually exclusive groups, required operands, typed arguments) so the parser refuses bad shapes at parse time with a usage error
- refusal wording: a semantic refusal's message or help text naming the expected invocation shape at the surface a session holds at refusal time
- checkout resolution: how a tool finds the repository checkout whose inputs it reads when invoked from another working directory
- witnessed invocation: the exact command shape the origin row records as the discovery-round trigger
- pricing table: the per-instance classification of the five named surfaces into declaration, refusal wording, checkout resolution, already declared (a priced no-op pin), or a compound of these, each with probe evidence
- linked worktree: a git worktree whose git-dir resolves differently from the common git-dir
- transfer-in: the Worktree-first step copying gitignored inputs (facts, reviews) into a fresh run worktree
- minute precision: a requested_at_iso whose seconds and microseconds are zero

## Why

Sessions repeatedly rebuild machinery invocations from prose memory, the tool refuses with a generic or mid-flow error, and the session re-derives the contract by trial before writing the finding into the feedback corpus, where the next refusing session will not have it loaded. Five named surfaces cost those discovery rounds, and argparse-level self-description or one wording line removes each.

## Gist & Examples

TLDR: five machinery surfaces declare or name their operand contracts at the refusal surface, ending recurring invocation archaeology rounds (driving force: efficiency).

**Before (today):** a session composes `gate-removal --branch B --worktree W`, the tool accepts the parse and refuses mid-flow with a runtime message the session only learns by trying; `rearm_on_touch.py --listing-json '{"automations":[]}'` fails with "listing input unreadable" because the literal is treated as a path; plan_readiness invoked from a run worktree missing its transfer-in says only "cannot resolve plans_dir/reviews_dir from the facts TOML block", leaving the session to guess whether to fix the worktree or move; the clocked-order-schedule help documents payload keys but not the minute-precision rule, so a sub-minute ISO is composed and refused downstream.

**After (this plan):** the gate-removal usage line declares `[--worktree WORKTREE | --branch BRANCH]` and the conflict refuses at parse time through the same exit contract; an inline JSON object parses as a listing; the facts-resolution failure names the invoking checkout, whether it is a linked worktree, and both remedies; the runtime help names the minute-precision constraint; the dirt gate's already-correct no-paths refusal is pinned as a regression fixture. Every witnessed invocation is a fixture.

**Edge cases:** an inline JSON literal (object or array, the shapes the file-path form already accepts) parses like its file form; only input that is not JSON and not a readable path stays refused; detection attempts the JSON parse before the path read, so a readable path whose literal name parses as a JSON scalar or object is refused by the shape check instead of read as a file, and the file form stays reachable for such names via an absolute or `./`-prefixed path; a nonexistent local time ISO keeps its epoch-mismatch refusal; a worktree with inputs present keeps working unchanged (input anchoring never moves to the primary checkout).

**Pricing table (the per-instance classification of record):**

| # | Surface | Witnessed invocation | Priced class | Remedy home |
|---|---|---|---|---|
| 1 | `scripts/dirt_regression_gate.py` | `--base <sha>` with no path operands | already declared | Task 4 pins the existing refusal as a fixture |
| 2 | `scripts/worktree_closeout_migrate.py` gate-removal | `--branch` and `--worktree` together | declaration | Task 1: argparse mutually exclusive group, parse-time refusal, same exit contract |
| 3 | `scripts/rearm_on_touch.py` `--listing-json` | inline JSON literal | declaration + wording | Task 2: literal JSON accepted beside path and stdin; refusal names the three forms |
| 4 | `scripts/plan_readiness.py` | run from a worktree without transfer-in inputs | checkout resolution | Task 3: failure names the invoking checkout, its linked-worktree fact, and both remedies |
| 5 | `scripts/execute_plan_runtime.py` clocked-order-schedule | sub-minute `requested_at_iso` | wording | Task 4: help names minute precision; the downstream refusal is unchanged |

## Outcome

Repository machinery tools carry their operand contracts on their own refusal surfaces.

- A session composing a conflicting operand pair sees the constraint in the usage line and at parse time, not after composing a full run.
- A session holding a JSON listing passes it inline; malformed input refusal text names the three accepted forms.
- A session invoking plan_readiness from an inputless worktree reads which checkout is expected and both remedies without a discovery round.
- The witnessed invocations stay pinned as regression fixtures so the self-description cannot silently regress.

Gate delta: none added; no gate, fence, schema field, or refusal class is added; one runtime mutual-exclusion refusal is re-homed to argparse declaration with the same refuse decision and exit/OUTCOME contract (Task 1), its dead runtime duplicate removed; failure and usage wording is extended at three existing refusal surfaces (Tasks 2, 3, 4); the plan makes exactly three decision moves, all declared here: the re-homing's own boundary, Task 2's JSON-parse-first disambiguation flip declared in Edge cases, and Task 2's witnessed inline-JSON listing acceptance (refused today, accepted post-fix). The moves in detail: the declared exclusion fires on operand presence, so a degenerate empty-string `--branch` beside `--worktree` flips from accepted to parse-time refusal; a readable path whose literal name parses as a JSON scalar flips from accepted to the shape refusal; the witnessed inline-JSON listing invocation flips from refused to accepted; every input class the pricing table does not move to accepted keeps its refusal decision unchanged.

Follow-up disposition: no follow-up candidates anticipated; an instance whose execution-time probe proves already self-describing is recorded as a priced no-op row beside the pricing table with its probe evidence, and the deployed-copy sync rides Ship when as an external prerequisite, never a backlog row.

## Assumptions

- assume "five named instances" means the four scripts in the origin row's Skill/step field plus the adjacent clocked-order requested_at_iso note; basis: the origin row enumerates exactly these five surfaces and the entry's scope arms price "each named instance"
- assume the dirt gate's no-paths invocation is priced already-declared and remedied by a pinning fixture only, with no whole-tree capability added; basis: authoring probe 2026-11-13 shows argparse `paths` nargs="+" already refuses the witnessed invocation with a usage error naming paths, and the origin row warns against blanket usage-printing
- assume the deployed runtime path ~/.ai-playbook/scripts/rearm_on_touch.py is a reference symlink to the primary checkout's script (the origin row's referenced-not-vendored orientation), so the runtime surface propagates the landed change at merge time with no operator step; basis: the deployed path resolves by symlink into the primary checkout (probed 2026-11-14); the vendored-sync rules scope skills, not scripts
- assume plan_readiness input anchoring stays at the invoking checkout with no primary fallback; basis: authoring probe 2026-11-13 shows the gate runs correctly from a linked worktree with inputs present; a silent primary fallback would read the wrong reviews home
- assume the origin's Class: design-class re-derives from the body (five surfaces, two remedy families, one open checkout-resolution choice); basis: the origin body matches its declared Class line, so the arms shape to the declared class
Decision points requiring a grill: gate-removal constraint re-homing: argparse mutually exclusive group over epilog wording, the witnessed cost is the constraint being invisible until refusal and parser.error prints usage but not epilog, 2026-11-13, Task 1; rearm listing-json acceptance: literal-JSON acceptance (object or array, the file form's shapes) in load_listing over docs-only wording, the tool is what the session holds at refusal time (origin row's own rejected alternative), 2026-11-13, Task 2; plan_readiness worktree contract: refuse naming the invoking checkout and remedies over silent primary fallback, a fallback would read the wrong reviews home, 2026-11-13, Task 3; rearm literal-versus-path disambiguation order: JSON-parse-first over path-exists-first, path-exists-first would silently read a JSON literal colliding with an existing relative filename as a file while JSON-parse-first keeps such names reachable as files via an absolute or ./-prefixed path and Task 2's disambiguation-order fixture pins the refusal, 2026-11-14, Task 2; rearm refusal-message map: per-category messages over a merged three-forms message, the file-form message pins (`listing input is not parseable JSON`) survive unchanged and only the inline-arm refusal names the three accepted forms, 2026-11-14, Task 2

## Standing constraints

- Focused suites only (facts test_suite_policy focused-never-full): validation runs the named focused suites, never the full inventory.
- Every touched refusal whose input class the pricing table does not move to accepted keeps its decision and its exit/OUTCOME contract per scripts/OUTCOME_CONTRACT.md; message wording may re-home but the refuse-or-accept decision for those classes and the final OUTCOME line semantics stay. The pricing table's acceptance move (the witnessed inline-JSON listing under Task 2) is the declared exception; the surviving refusals it pins are the unreadable-input classified refusal, the malformed-content message pin, and the stdin/path forms.
- No production behavior beyond the priced surfaces changes; scripts outside the five named instances are frozen.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the focused suites for all five touched surfaces pass after execution
- regression safety: every refusal decision and exit/OUTCOME contract named in the pricing table is pinned by a fixture, and the fixtures fail if the contract moves
- self-description: each priced gap closes at the surface a session holds at refusal time (usage line, help text, or failure message), not in a corpus note

**Done when:**
- re-running each witnessed invocation against the executed tree produces the pricing table's declared outcome
- the focused suites named in Validation Commands pass
- the em-dash added-lines gate and the public-hygiene scan exit 0 over the changed set

**Ship when:** the runtime surface carries the accepted inline-listing behavior; because the deployed path is a reference symlink into the primary checkout this holds automatically once the landing reaches the primary checkout, closure evidenced by the primary checkout's HEAD containing the landing commit (digest-equality through the link is tautological and is not the closure). [class: OPERATIONS_FOLLOW_UP]

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/worktree_closeout_migrate.py` (Task 1)
- `scripts/rearm_on_touch.py` (Task 2)
- `scripts/plan_readiness.py` (Task 3)
- `scripts/execute_plan_runtime.py` (Task 4)

**Tests:**
- `scripts/test_worktree_closeout_migrate.py` (Task 1)
- `scripts/test_rearm_on_touch.py` (Task 2)
- `scripts/test_plan_readiness.py` (Task 3)
- `scripts/test_execute_plan_resume_watcher.py` (Task 4)
- `scripts/test_dirt_regression_gate.py` (Task 4)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/dirt_regression_gate.py`; reason: the instance is priced already-declared, the task pins its existing behavior with a fixture only, no production edit is prescribed
- `docs/` and `agents/skills/` surfaces; reason: no skill-text or documentation edit is prescribed; the pricing of record lives in this plan
- `~/.ai-playbook/scripts/rearm_on_touch.py` (the deployed path); reason: a reference symlink into the primary checkout, no repository edit exists at that path, propagation rides the landing (Ship when)

## Validation Commands

Authoring-time record (2026-11-13, this plan's bytes at authoring): fix_plan_em_dashes.py pass (0 substitutions, run before each write); check-no-em-dash.sh touched pass; scan-public-hygiene.sh pass (OUTCOME: pass); pre-round structural gate pass (OUTCOME: pass, one warning-only FILES-COVERAGE row quoting a Task 1 commit message, not a file path); rule 22 audit: bash -n over the Validation Commands block clean; rule 19 RED-today evidence, each probe executed 2026-11-13 against the base tip: dirt gate `--base HEAD` with no paths exits 3 with `OUTCOME: tool_error` naming paths (already declared, Task 4 pins it); rearm inline-JSON object fails with the unreadable-path tool error (Task 2 RED); plan_readiness from a linked worktree without facts names no checkout context or remedies (Task 3 RED); the runtime `--input` help carries no minute-precision constraint (Task 4 RED); the gate-removal usage line shows no worktree/branch alternative and the conflict refuses at runtime after parse (Task 1 RED). Round-start state for r1: worktree branch tip at authoring, plan bytes at the pre-round pass digest.

```bash
REPO="$(git rev-parse --show-toplevel)"; cd "$REPO" || exit 1
PY=python3
[ -x "$HOME/.agents/venvs/ai-playbook-test/bin/python" ] && PY="$HOME/.agents/venvs/ai-playbook-test/bin/python"
"$PY" -m pytest scripts/test_worktree_closeout_migrate.py -q || exit 1
"$PY" -m pytest scripts/test_rearm_on_touch.py -q || exit 1
"$PY" -m pytest scripts/test_plan_readiness.py -q || exit 1
"$PY" -m pytest scripts/test_execute_plan_resume_watcher.py -q || exit 1
"$PY" -m pytest scripts/test_dirt_regression_gate.py -q || exit 1
"$PY" scripts/plan_readiness.py --selftest || exit 1
# witnessed-invocation probes over the executed tree; each aborts on any outcome
# other than the pricing table's declared one; the rearm probe seeds a minimal
# valid state file (the three bookkeeping fields) into a temp dir so the run
# reaches the listing decision and the bookkeeping write lands in the temp file
# (a state file without the parent_absent_since field would refuse the
# structural insert; against the live state file the run would perform
# bookkeeping writes)
"$PY" scripts/dirt_regression_gate.py --base HEAD >/dev/null 2>&1
[ $? -eq 3 ] || { echo "dirt gate no-paths probe: expected exit 3"; exit 1; }
REARM_TMP="$(mktemp -d)"
printf '{"parent_automation_id":null,"parent_absent_since":null,"rearm_note":null}' > "$REARM_TMP/state.json"
"$PY" scripts/rearm_on_touch.py --listing-json '{"automations":[]}' --state-path "$REARM_TMP/state.json" --repo-root "$REPO" >/dev/null 2>&1
REARM_RC=$?
rm -rf "$REARM_TMP"
[ $REARM_RC -eq 0 ] || { echo "rearm inline-json probe: expected exit 0 with a temp state path"; exit 1; }
bash scripts/check-no-em-dash.sh added-lines --base main || exit 1
bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" || exit 1
```

### Task 1: gate-removal declares the branch/worktree exclusion at argparse

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/worktree_closeout_migrate.py`
- `scripts/test_worktree_closeout_migrate.py`

Primary class anchors:
- `_add_gate_removal_arguments` in `scripts/worktree_closeout_migrate.py`

- [ ] `--worktree` and `--branch` sit in one argparse mutually exclusive group on the gate-removal subparser so the usage line shows the `[--worktree WORKTREE | --branch BRANCH]` alternative; given `gate-removal --help`, expects the usage line to carry that alternative [class: IMPLEMENTATION_REQUIRED]
- [ ] given the witnessed conflict invocation with `--plan` and `--target` supplied alongside `--branch` and `--worktree`, expects a parse-time usage-error refusal through the gate-removal scoped error override with exit 3 and final line `OUTCOME: tool_error`, and the runtime branch of the old duplicate check removed so exactly one surface owns the conflict [class: IMPLEMENTATION_REQUIRED]
- [ ] given the degenerate invocation `gate-removal --plan P --target T --branch '' --worktree W`, expects the parse-time usage-error refusal (the group fires on operand presence, value ignored; this is the flip the Gate delta declares) [class: REPOSITORY_TEST]
- [ ] given branch-only mode with no explicit migration manifest, expects the existing runtime refusal message and exit contract unchanged (regression pin) [class: REPOSITORY_TEST]
- [ ] given neither `--worktree` nor `--branch`, expects the existing runtime refusal message and exit contract unchanged (regression pin) [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the witnessed conflict invocation refuses only at runtime after parse and the usage line shows no alternative; conflict-message fixtures pinning the old runtime text fail until re-pinned to the parse-time message [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: the focused worktree-closeout suite passes with the parse-time conflict, the usage alternative, and both sibling runtime pins [class: REPOSITORY_TEST]
- [ ] Commit: `refactor: declare gate-removal branch/worktree exclusion in argparse usage` [class: IMPLEMENTATION_REQUIRED]

### Task 2: rearm_on_touch accepts an inline JSON listing literal

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/rearm_on_touch.py`
- `scripts/test_rearm_on_touch.py`

Primary class anchors:
- `load_listing` in `scripts/rearm_on_touch.py`

- [ ] `load_listing` accepts a literal JSON string (object or array, the shapes the file-path form's consumer already accepts) as a third accepted form beside an existing file path and `-`, with detection attempting the JSON parse before the path read; given the witnessed invocation `--listing-json '{"automations":[]}'` against a temp state path, expects the listing to parse and the verdict JSON to report the listing used [class: IMPLEMENTATION_REQUIRED]
- [ ] given unparseable listing input that neither parses as a JSON object or array nor names a readable path (for example a nonexistent path), expects the classified refusal with exit 3, final line `OUTCOME: tool_error`, and a reason naming all three accepted forms; given a JSON scalar literal with no same-named readable file, expects the existing shape refusal naming array-or-object (the shape-refusal arm of the disambiguation order) [class: IMPLEMENTATION_REQUIRED]
- [ ] given a literal JSON array, expects it to parse exactly like an array delivered by file (the consumer's existing bare-array acceptance); given input that is neither JSON nor a readable path, expects the same classified refusal as today [class: REPOSITORY_TEST]
- [ ] given a readable file whose literal name parses as JSON (for example a file named `123`), expects its bare name as the `--listing-json` value to take the shape-refusal and the same file to parse when passed as an absolute or `./`-prefixed path (disambiguation-order pin) [class: REPOSITORY_TEST]
- [ ] given a readable file with unparseable content passed as a path, expects the existing `listing input is not parseable JSON` message pin to survive unchanged (the wording change is scoped to the inline-arm refusal; the per-category message map keeps this pin) [class: REPOSITORY_TEST]
- [ ] given `-` and a real file path, expects both forms unchanged (regression pins) [class: REPOSITORY_TEST]
- [ ] the `--listing-json` help text names the three accepted forms [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect RED: the witnessed inline-object invocation fails with the unreadable-path tool error today; run it against a temp state path that exists (create the state file first with the same three-field seed the Validation Commands block uses, after `mktemp -d`) so the run reaches the listing path and no live scheduler state is touched [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: the focused rearm suite passes with the inline form, the three-form refusal wording, and the stdin/path regression pins [class: REPOSITORY_TEST]
- [ ] Commit: `feat: accept inline JSON in rearm listing input with self-describing refusal` [class: IMPLEMENTATION_REQUIRED]

### Task 3: plan_readiness names the invoking checkout when facts resolution fails

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/plan_readiness.py`
- `scripts/test_plan_readiness.py`

Primary class anchors:
- `main` in `scripts/plan_readiness.py`

- [ ] when facts TOML resolution fails at the invoking checkout, the failure text keeps the existing lead line verbatim (the substring the script's `--selftest#cli/missing_facts` check pins) and adds the invoking checkout path, whether that checkout is a linked worktree, and the two remedies (transfer the gitignored inputs via transfer-in, the Worktree-first step, or invoke from the checkout holding them) [class: IMPLEMENTATION_REQUIRED]
- [ ] input anchoring itself does not move: given the gate invoked from a linked worktree whose facts and reviews are present, expects the gate to resolve and run from that worktree exactly as today (regression pin) [class: REPOSITORY_TEST]
- [ ] given the gate invoked from a linked worktree whose facts file is absent, expects the failure text to name that checkout's path, the linked-worktree fact, and both remedies (this is the RED witness; the current text names none of the three) [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the facts-less worktree failure text today carries no checkout context or remedies [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: the focused plan-readiness suite passes with the extended message and the anchoring regression pin, and the script's `--selftest` passes (it owns the verbatim lead-line pin) [class: REPOSITORY_TEST]
- [ ] Commit: `feat: name invoking checkout and remedies in readiness facts failure` [class: IMPLEMENTATION_REQUIRED]

### Task 4: clocked-order help names minute precision; dirt gate refusal pinned

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_resume_watcher.py`
- `scripts/test_dirt_regression_gate.py`

Primary class anchors:
- `main` in `scripts/execute_plan_runtime.py`
- `main` in `scripts/dirt_regression_gate.py`

- [ ] the `--input` help for clocked-order-schedule states that requested_at_iso must be minute precision (seconds and microseconds zero; sub-minute input refuses); given `--help`, expects the clocked-order-schedule key documentation to carry that constraint [class: IMPLEMENTATION_REQUIRED]
- [ ] given a sub-minute ISO to clocked-order-schedule, expects the existing refusal token and exit contract unchanged (regression pin; the refusal function in the resume watcher is not edited) [class: REPOSITORY_TEST]
- [ ] given the dirt gate invoked with `--base` and no path operands, expects the existing usage error naming paths with exit 3 and final line `OUTCOME: tool_error`, pinned as a regression fixture (no production edit; the declaration already exists) [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the runtime help today names no minute-precision constraint for clocked-order-schedule [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: the focused resume-watcher and dirt-gate suites pass with the help constraint, the sub-minute refusal pin, and the no-paths fixture [class: REPOSITORY_TEST]
- [ ] Commit: `docs: name minute precision in clocked-order usage and pin dirt gate refusal` [class: IMPLEMENTATION_REQUIRED]
