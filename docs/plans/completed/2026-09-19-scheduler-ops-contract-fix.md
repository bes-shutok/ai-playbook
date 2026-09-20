# Plan: Scheduler ops contract fix (selection helper grammar, verb contract, toolset precheck)

Backlog origins (all `docs/history/backlog/`): `2026-09-19-selection-helper-suffix-shadowing.md`,
`2026-09-19-selection-helper-prose-precision.md`, `2026-09-19-schedule-vs-execute-verb-contract.md`,
`2026-09-19-scheduler-toolset-precheck-before-dispatch.md`.

Split of record: the 14-origin dispatch "scheduler ops liveness residuals" exceeds the
single-plan authoring budget and is split into two plans per the dispatch's split guidance.
This is plan 1 (the coherent contract fix: the selection-helper pair, the interactive verb
contract, and the toolset precheck). Plan 2 is
`docs/plans/2026-09-19-scheduler-ops-lanes-durability.md` (lanes and durability). The
friction-audit-lane origin is deferred to its own future plan (disposition annotated on the
item by plan 2).

## Terms

- **Selection helper**: `scripts/review_record_selection.py`; makes the review-record round
  decision mechanical (`select`, `mark-superseded`, `backup`).
- **Pair grammar**: the record-name pattern `_pair_pattern(slug)` matches; a record pair base
  is a Markdown/sidecar name minus extension, e.g. `2026-09-19-demo-r1`.
- **Suffix shadowing**: a slug that is a hyphen-suffix of another slug (e.g. `plan` vs
  `review-plan`) enumerating the other family's records through a loose prefix.
- **Verb contract**: the interactive-ask rule separating scheduling verbs ("schedule at ...")
  from execution verbs ("run/execute now") and loop verbs ("resume/re-arm").
- **Dispatch ladder**: the ZCode overlay's ordered child-dispatch steps (create, recycling,
  fallback, idle lane, last resort).
- **Toolset precheck**: the pre-ladder assertion that the session owns the mutating
  automation primitives the decided dispatch needs.
- **Pins suite**: `scripts/check_maintenance_pins.sh`; mechanical invariant greps, exit 0 =
  all pins hold.

## Assumptions

- assume the two selection-helper items' triggers are met by this plan (it edits the helper's
  enumeration grammar and error paths); basis: the items' Trigger lines.
- assume empty `--source-digest` becomes a usage error (exit 2), superseding the r2 exit-1
  carve-out; basis: the item's fix shape lists "raise the empty-digest refusal as a usage
  error (exit 2)" first; both fail closed, taxonomy consistency is the goal.
- assume the anchored pair grammar keeps both live record families enumerable: the
  helper-emitted shape `<date>-<slug>-r<N>` and the legacy `<date>-plan-review-<slug>-r<N>`
  shape (the review-plan skill's output shape, confirmed live under `docs/reviews/`);
  basis: enumeration of `docs/reviews/` 2026-09-19.
- assume the toolset precheck checks the mutating primitives the ladder needs regardless of
  which primary leg is operative (clocked: `CronCreate` plus `CronDelete`; idle:
  `OffPeakCreate`), so this plan and plan 2 (which rewrites the ladder's primary leg) stay
  order-independent; basis: the ladder's delete-plus-create fallback predates both plans.
- assume the interactive dispatch template shipped into the runtime overlay stays a compact
  form and the scheduled-payload source of record remains `prompt-templates.md` (the
  overlay block is for interactive asks, which carry no child re-arm duty); basis:
  prompt-templates.md legend and blueprint roles.
- assume the verb contract's standing rule lands in the repo-root `AGENTS.md` as a new short
  section; basis: the item's "one-line standing rule in the repo AGENTS.md".

Decision points requiring a grill: empty-digest taxonomy: usage error exit 2 (first-listed fix option), source: dispatch standing pre-authorization over the item's fix shape, 2026-09-19, Task 2; suffix-shadowing shape: anchored grammar (first-listed option) after live-family verification, source: dispatch standing pre-authorization plus docs/reviews enumeration, 2026-09-19, Task 1.

## Gist & Examples

Four contract fixes that stop two classes of silent misbehavior: one in the review-record
selection helper, two at the scheduler's interactive boundary, one in the dispatch ladder.

1. **Suffix shadowing (Task 1).** Today `_pair_pattern` is `^(?:.+-)?<slug>-r(\d+)$`; the
   `(?:.+-)?` prefix matches any hyphen chain, so the slug `plan` enumerates the record
   `2026-09-19-review-plan-r1` that belongs to the slug `review-plan`. With
   `--explicit-new-round` the helper then emits a `new-round` decision whose `prior` and
   `supersedes` name the foreign record: a wrong audit trail (no overwrite, no data loss).
   After the fix the prefix is anchored to the two real shapes, the date stamp plus an
   optional literal `plan-review-` infix, so only the owning family's records enumerate:
   slug `plan` in a directory holding only `2026-09-19-review-plan-r1` gets decision
   `new-record` (its own `-r1`), and the legacy `2026-09-08-plan-review-demo-r2` record
   still enumerates for slug `demo`.

2. **Helper prose and exit-code precision (Task 2).** The `SelectionUsageError` docstring
   claims "invalid argument (exit 2)" while four of its raise sites are environmental
   (symlinked prior, unclosed fence, backup-name collision, collision-suffix exhaustion); the empty `--source-digest`
   refusal exits 1 while every other malformed digest exits 2; the slug error claims
   "no '..'" though `a..b` is accepted (no separator is possible in the grammar); and the
   F9 note in the scanner-allowlist backlog item overstates the absolute-spelling shape.
   All fail closed today; this is the polish batch those items deferred to exactly this
   trigger.

3. **Verb contract (Task 3).** The friction audit's largest correction theme (~20 prompts):
   scheduling asks executed inline. The maintenance skill's trigger surface gains an
   explicit rule: "schedule at HH:MM ..." means create or patch the automation only and
   echo its id plus next fire time; "run/execute now" means execute; "resume/re-arm the
   loop" means the state-file re-arm recipe. The compact interactive dispatch template
   (`{schedule_time}`/`{backlog_item}`) ships into the runtime overlay so it stops being
   hand-pasted, and the repo `AGENTS.md` carries the one-line standing rule.

4. **Toolset precheck (Task 4).** The 2026-09-19 04:15Z scheduler turn found
   `CronCreate`/`CronUpdate`/`CronDelete` absent from its toolset only mid-ladder, burned
   the selection-loop guard reaching for the missing call, and polluted the `turn_error`
   streak with a cause it was never meant to count. The turn now asserts, before entering
   the dispatch ladder, that the mutating primitives the decided dispatch needs exist; on
   absence it records the reason, parks or retains the dispatch per the existing trap rule,
   and stands down with zero listings performed.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every prescribed behavior is observable through the helper CLI, the pins
  suite, or a grep with a recorded RED-today flip; no gate passes vacuously on missing paths.
- regression safety: the anchored grammar keeps every live record family enumerable
  (emitted shape and legacy `plan-review-` shape); the exit-code change flips only the
  empty-digest path and its two tests.
- docs/contract alignment: skill-layer wording lands once in the owning surface and is
  pinned mechanically; no duplicated template bodies between the overlay and
  `prompt-templates.md`.

**Done when:**
- `python3 scripts/test_review_record_selection.py` exits 0 with the new grammar tests
  present and the empty-digest test expecting exit 2.
- `bash scripts/check_maintenance_pins.sh` exits 0 with the new pins (grammar anchor,
  verb contract, toolset precheck) present.
- `grep` finds no `(?:.+-)?` loose prefix in `scripts/review_record_selection.py`.
- The verb contract subsection exists in the maintenance skill, the standing rule exists in
  the repo `AGENTS.md`, and the overlay carries the interactive template section.
- The F9 note's parenthetical is gone from the scanner-allowlist backlog item.

**Ship when:**
- Zero schedule-vs-execute corrections in the next corrections-mining pass over typed
  prompts [class: OPERATIONS_FOLLOW_UP]; evidence owner: the friction-audit mining pass;
  closure: a dated mining-pass result recording the zero.
- The first observed suffix collision between two real slugs sharing one reviews directory
  enumerates correctly (no audit-trail finding) [class: OPERATIONS_FOLLOW_UP]; evidence
  owner: any future review-records round; closure: absence of new shadowing findings.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/review_record_selection.py`
- `scripts/check_maintenance_pins.sh`

**Tests:**
- `scripts/test_review_record_selection.py`

**Docs and skill layer:**
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `AGENTS.md`
- `docs/history/backlog/2026-09-19-scanner-allowlist-glob-single-source.md`

**Plan-related extension**; implementation and review may change files not listed above.
Treat a finding as in scope when it is **causally related to this plan**: it implements or
completes a plan task, fixes a regression introduced by plan work, closes wiring or docs
implied by an explicit must-fix change, or contradicts a contract the plan changed. If the
link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `projects/.ai-playbook/development_lessons.md`; peer-session-owned and currently dirty in
  the shared checkout; never a target of this plan.
- `agents/skills/maintenance/prompt-templates.md`; plan 2's surface (the child blueprints);
  this plan deliberately does not edit it.
- `scripts/scan-public-hygiene.sh`; its backlog note gets a wording fix only (Task 2), the
  scanner itself is out of scope.
- Any file under `docs/tmp/`; gitignored session scratch.

## Validation Commands

```bash
set -u
repo="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 1
fail=0

# 1. Helper suite: the grammar tests and the exit-code flip must exist and pass.
if python3 "$repo/scripts/test_review_record_selection.py" 2>&1; then :; else
  echo "GATE FAIL: helper suite"; fail=1; fi

# 2. The loose prefix is gone from the helper (forbidden pattern; rc>=2 is a tool error).
out="$(grep -nF '(?:.+-)?' "$repo/scripts/review_record_selection.py" 2>&1)"; rc=$?
if [ "$rc" -eq 0 ]; then echo "GATE FAIL: loose prefix still present: $out"; fail=1
elif [ "$rc" -ge 2 ]; then echo "GATE FAIL: grep error on helper: $out"; fail=1; fi

# 3. The anchored grammar and the legacy infix alternative are present (positive pins).
grep -qF 'plan-review-' "$repo/scripts/review_record_selection.py" \
  || { echo "GATE FAIL: anchored grammar missing the legacy infix"; fail=1; }

# 4. Pins suite (mechanical invariants incl. the new verb-contract and precheck pins).
if bash "$repo/scripts/check_maintenance_pins.sh" 2>&1; then :; else
  echo "GATE FAIL: pins suite"; fail=1; fi
bash -n "$repo/scripts/check_maintenance_pins.sh" || { echo "GATE FAIL: pins syntax"; fail=1; }

# 5. Verb contract surfaces: per-file obligation, dedicated greps.
if ! grep -q "Trigger verbs" "$repo/agents/skills/maintenance/SKILL.md"; then
  echo "GATE FAIL: verb contract subsection missing from maintenance SKILL.md"; fail=1; fi
if ! grep -q "Scheduling asks" "$repo/AGENTS.md"; then
  echo "GATE FAIL: standing rule missing from repo AGENTS.md"; fail=1; fi
if ! grep -q "Interactive dispatch template" "$repo/agents/skills/maintenance/zcode.md"; then
  echo "GATE FAIL: interactive template section missing from overlay"; fail=1; fi

# 6. Toolset precheck registered with its dated witness.
if ! grep -q "clocked-primitives-absent" "$repo/agents/skills/maintenance/zcode.md"; then
  echo "GATE FAIL: precheck stand-down reason missing from overlay"; fail=1; fi
if ! grep -q "2026-09-19 04:15Z" "$repo/agents/skills/maintenance/zcode.md"; then
  echo "GATE FAIL: precheck witness date missing from overlay"; fail=1; fi

# 7. F9 note parenthetical dropped (forbidden phrase, flattened sweep: the sentence wraps).
flat="$(tr '\n' ' ' < "$repo/docs/history/backlog/2026-09-19-scanner-allowlist-glob-single-source.md" | tr -s ' ')"
case "$flat" in
  *"and absolute spellings of it"*) echo "GATE FAIL: F9 parenthetical still present"; fail=1;;
esac

# 8. No em-dash in any file this plan creates or edits: the repo's own scanner
#    (agent_workflow_guidelines.md section 39 policy) over the explicit must-fix set.
#    CHECK_NO_EM_DASH_ALL=1 disables the scanner's default prose-extension filter, which
#    would silently skip the .py and .sh files in this list (four of the seven).
#    Every file in this set was verified em-dash clean before the first task lands
#    (2026-09-19), so the sweep is satisfiable on arrival and stays green after the tasks.
if CHECK_NO_EM_DASH_ALL=1 bash "$repo/scripts/check-no-em-dash.sh" file \
     "$repo/scripts/review_record_selection.py" \
     "$repo/scripts/test_review_record_selection.py" \
     "$repo/scripts/check_maintenance_pins.sh" \
     "$repo/agents/skills/maintenance/SKILL.md" \
     "$repo/agents/skills/maintenance/zcode.md" \
     "$repo/AGENTS.md" \
     "$repo/docs/history/backlog/2026-09-19-scanner-allowlist-glob-single-source.md"; then :; else
  echo "GATE FAIL: em-dash scan over the must-fix set"; fail=1; fi

if [ "$fail" -eq 1 ]; then exit 1; fi
echo "ALL GATES GREEN"
```

Authoring-time note (rule 19/337): the whole block was executed against the tree before the
tasks land (recorded 2026-09-19); the FIRST failing gate today is gate 2 (the loose prefix is
present before Task 1 and must be absent after it), with gates 3, 5, 6, and 7 also red today
for the corresponding missing content, and gates 1, 4, and 8 green today (the helper suite
ran 28 tests OK, the pins suite holds, and every must-fix file is em-dash clean on the
unmodified tree, so the scanner sweep is satisfiable on arrival). Every red gate flips green
exactly when its task lands.

### Task 1: Anchor the selection helper's pair grammar (suffix shadowing)

Files:
- `scripts/review_record_selection.py`
- `scripts/test_review_record_selection.py`

- [x] `SelectionHelperTest#test_pair_pattern_cross_slug_negative`; given a reviews dir holding only the pair `2026-09-19-review-plan-r1.md` + `.stats.json` (slug `review-plan`), `select` with slug `plan` expects decision `new-record` emitting the `-plan-r1` pair with `prior` null and `supersedes` null, exit 0 [class: REPOSITORY_TEST]
- [x] `SelectionHelperTest#test_explicit_new_round_cross_slug_negative`; given the same directory, `select --explicit-new-round` with slug `plan` expects decision `new-record` (not `new-round`), `prior` null, and no foreign `supersedes` value [class: REPOSITORY_TEST]
- [x] `SelectionHelperTest#test_pair_pattern_legacy_plan_review_positive`; given the pair `2026-09-08-plan-review-demo-r2.md` + `.stats.json`, `select` with slug `demo` expects `reuse` of that exact record (legacy `plan-review-` enumeration preserved, round 2) [class: REPOSITORY_TEST]
- [x] `SelectionHelperTest#test_pair_pattern_emitted_shape_positive`; given the pair `2026-09-19-demo-r3.md` + `.stats.json`, `select` with slug `demo` expects `reuse` at round 3 (emitted shape) [class: REPOSITORY_TEST]
- [x] `SelectionHelperTest#test_pair_pattern_owner_family_enumeration`; given a directory holding both the family's own pair `2026-09-19-review-plan-r1.md` + `.stats.json` and a foreign family's pair `2026-09-08-plan-review-demo-r2.md` + `.stats.json`, `select` with slug `review-plan` expects `reuse` of exactly its own `-r1` record (an owner-family enumeration never picks up another family's records through the infix alternative) [class: REPOSITORY_TEST]
- [x] Run the four new tests -> expect RED: `python3 scripts/test_review_record_selection.py` (the two negative tests fail against the loose prefix: the cross-slug select reuses the foreign record) [class: REPOSITORY_TEST]
- [x] Implement: `_pair_pattern` returns `re.compile(r"^(?:\d{4}-\d{2}-\d{2}-(?:plan-review-)?)" + re.escape(slug) + r"-r(\d+)$")` (plain string concatenation, NOT an f-string: an f-string parses the regex's `{4}`/`{2}` brace quantifiers as replacement fields and collapses them, silently matching nothing; a brace-doubled f-string variant is equally correct and was verified against the live corpus, but the plan prescribes the concatenation form so no brace escaping is load-bearing); update its docstring to name the two supported prefixes (the emitted date-stamped shape and the legacy `plan-review-` infix) and to document the accepted residual alias (a slug beginning with `plan-review-`, of the form `plan-review-Y`, enumerates the same legacy-shaped records as bare `Y`, because the infix alternative and the slug spelling both reach `<date>-plan-review-Y-r<N>`; documented, not guarded) [class: IMPLEMENTATION_REQUIRED] (superseded 2026-09-20 review r1: generalized to the live review-kind infix set plus guarded bare review- infix; see commit bd36aac8 and _pair_pattern docstring)
- [x] Run the whole helper suite -> expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `fix: anchor review-record pair grammar against suffix shadowing` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Selection helper prose and exit-code precision batch

Files:
- `scripts/review_record_selection.py`
- `scripts/test_review_record_selection.py`
- `docs/history/backlog/2026-09-19-scanner-allowlist-glob-single-source.md`

- [x] `SelectionHelperTest#test_select_rejects_empty_source_digest`; given an empty and a whitespace-only `--source-digest`, expects exit 2 with `--source-digest` in the error and no files created (updated from the r2 exit-1 pin: the dedicated test at the `Refused before any comparison` comment now expects 2) [class: REPOSITORY_TEST]
- [x] `SelectionHelperTest#test_select_rejects_malformed_source_digest`; given the malformed digests (`xyz`, 63/65 chars, uppercase, non-hex), expects exit 2 and no files created, with the comment's exit-1 carve-out sentence removed (all invalid digests now share the usage-error taxonomy) [class: REPOSITORY_TEST]
- [x] Broaden the `SelectionUsageError` docstring from "invalid argument (exit 2)" to name the class's real contract: an invalid invocation OR an unusable target/state that is the caller's to repair (exit 2), citing the environmental raise sites (symlinked prior, unclosed fence, backup-name collision, collision-suffix exhaustion); exit taxonomy stated once: usage errors exit 2, environmental refusals (`SelectionRefused`: a missing or damaged record target, an orphaned half, a differing digest without a decision) exit 1 [class: IMPLEMENTATION_REQUIRED]
- [x] Reword the slug error message: drop the "no '..'" claim (the grammar cannot carry a separator, so `a..b` is inert and accepted), keep "no path separators, no trailing newline" [class: IMPLEMENTATION_REQUIRED]
- [x] Change the empty `--source-digest` refusal from `SelectionRefused` to `SelectionUsageError` (exit 2), keeping the existing message text (an empty digest would silently disable the overwrite guard) [class: IMPLEMENTATION_REQUIRED]
- [x] In `docs/history/backlog/2026-09-19-scanner-allowlist-glob-single-source.md`, drop the parenthetical "(and absolute spellings of it)" from the r3 overflow F5 sentence: absolute spellings of the root `LICENSE.txt` are excluded in files mode (the `*/LICENSE.txt` case pattern matches across slashes); only the bare root-level relative spelling is scanned [class: IMPLEMENTATION_REQUIRED]
- [x] Run the helper suite -> expect GREEN (the two updated digest tests plus the untouched rest) [class: REPOSITORY_TEST]
- [x] Commit: `fix: selection helper usage-error taxonomy and message precision` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Schedule-vs-execute verb contract

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `AGENTS.md`
- `scripts/check_maintenance_pins.sh`

- [x] Add a `### Trigger verbs (schedule vs execute vs resume)` subsection to the maintenance skill immediately after the `# Maintenance` intro paragraph, with a scope sentence and three bindings stated as rules: the bindings govern interactive asks (a human-typed message); an unattended scheduler turn never blocks on questions regardless of wording and follows its blueprint duties instead; a scheduling verb ("schedule at HH:MM", "reschedule", "patch the automation") means create or patch the automation only and end the reply by echoing the automation id and its next fire time, never executing the payload inline in the same turn; an execution verb ("run now", "execute") means perform the work in-session; a loop verb ("resume", "re-arm the loop") means the state-file re-arm recipe per the runtime overlay; an ambiguous time ("12am 30 minutes this night") is resolved to a concrete timestamp before any create, never guessed [class: IMPLEMENTATION_REQUIRED]
- [x] Add the one-line standing rule to the repo `AGENTS.md` as a new short section `## Scheduling asks (verb contract)`: a "schedule at ..." ask schedules (create/patch the automation, report id and next fire time) and never executes the payload in the same turn [class: IMPLEMENTATION_REQUIRED]
- [x] Add an `## Interactive dispatch template` section to the runtime overlay carrying the compact interactive template as a fenced text block (`Schedule at {schedule_time} the following task: Using the plans skill, author a plan covering backlog item: {backlog_item} ...`) plus three sentences: this block is for interactive asks from a fresh session (no child re-arm duty); the standing pre-authorization and authoring-constraint sentences are carried verbatim by the authoring blueprint in `agents/skills/maintenance/prompt-templates.md` and this section references that blueprint for them instead of restating them; the scheduled-payload source of record remains `agents/skills/maintenance/prompt-templates.md` [class: IMPLEMENTATION_REQUIRED]
- [x] Pin all three surfaces in `scripts/check_maintenance_pins.sh`: the SKILL.md subsection heading, the AGENTS.md section heading, the overlay section heading (one `pin` per file; grep for the exact heading strings) [class: IMPLEMENTATION_REQUIRED]
- [x] Run the pins suite -> expect GREEN: `bash scripts/check_maintenance_pins.sh` [class: REPOSITORY_TEST]
- [x] Commit: `feat: schedule-vs-execute verb contract and interactive dispatch template` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Toolset precheck before the dispatch ladder

Files:
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/SKILL.md`
- `scripts/check_maintenance_pins.sh`

- [x] Add a `Ladder precheck` bullet at the top of the overlay's `Child dispatch ladder` section: before entering the ladder, assert the session's toolset exposes the mutating primitives the decided dispatch needs, per the path the session will take: a fresh unbound chat needs only the create primitive `CronCreate` (ladder step 1 takes no delete); an automation-born session needs `CronCreate` plus `CronDelete` (its own lingered record must be deleted before a cap-refused create); the update primitive is only a recycling-optimization input and its absence alone never blocks dispatch; an idle-time child needs `OffPeakCreate`. The precheck is lane-scoped: on absence, stand down only the lane whose decided dispatch lacks its primitives (record `turn_error: clocked-primitives-absent` for the clocked lane, `turn_error: idle-primitive-absent` for the idle lane), park or retain that dispatch per the existing selection-loop trap rule (`pending_dispatch` via a Bash state edit), and evaluate the other lane's precheck independently [class: IMPLEMENTATION_REQUIRED]
- [x] Register the behavior with its dated witness in the overlay's `Dispatch discipline and loop stand-down` bullet: the 2026-09-19 04:15Z turn tripped the selection-loop guard reaching for a statically absent `CronCreate`; the precheck exists so the guard fires only on genuine listing-without-mutation loops [class: IMPLEMENTATION_REQUIRED]
- [x] Add the Step 5 precondition sentence to the maintenance skill's scheduling step: after the quota leg fixes the final fire time and before any ladder step, run the runtime overlay's ladder precheck; a tripped precheck resolves the lane to D3 with the overlay's `turn_error` reason and schedules nothing; the parked `pending_dispatch` entry the precheck write creates persists until the next turn's Step 1 reader dispatches it (the precheck imports only the trap rule's park-or-retain write, never its clear-on-idle-success clause) [class: IMPLEMENTATION_REQUIRED]
- [x] Pin the Step 5 precondition sentence in `scripts/check_maintenance_pins.sh` alongside the overlay pins (grep for the precondition's anchor phrase `ladder precheck`) [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the sanctioned state-writer enumeration for the precheck park: SKILL.md's State file Scoping note lists the scheduler turn's write modes exhaustively, and the pre-ladder precheck's `pending_dispatch` park via a Bash state edit is a new mode on a path that today exists nowhere: add the precheck park to the scheduler-turn write-mode enumeration (one clause, naming the lane-scoped precheck as the writer) so the skill's own state-writer contract covers the path Task 4 creates [class: IMPLEMENTATION_REQUIRED]
- [x] Both-lanes precedence: when both lanes' prechecks trip in one turn, record a single `turn_error` with the most severe reason (the clocked lane's `clocked-primitives-absent` over the idle lane's `idle-primitive-absent`), mirroring the existing most-severe-reason precedence for the single `turn_error` field; both parks still write [class: IMPLEMENTATION_REQUIRED] (superseded 2026-09-20 review r2: pending_dispatch is single-valued, so both-lanes trips park only the most severe lane's dispatch with the other lane named in decision_reason; the unparked dispatch re-selects next turn per the Step 3 reader)
- [x] Pin the precheck in `scripts/check_maintenance_pins.sh`: the `Ladder precheck` literal in the overlay and both stand-down reason strings (`clocked-primitives-absent`, `idle-primitive-absent`; one `pin` each) [class: IMPLEMENTATION_REQUIRED]
- [x] Run the pins suite and the plan Validation Commands -> expect GREEN end to end [class: REPOSITORY_TEST]
- [x] Commit: `feat: toolset precheck before the maintenance dispatch ladder` [class: IMPLEMENTATION_REQUIRED]
