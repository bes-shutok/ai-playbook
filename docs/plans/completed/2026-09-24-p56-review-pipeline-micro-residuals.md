# Plan: P56 review pipeline + micro-residuals

Backlog origins (scope of record):
- `docs/history/backlog/2026-09-23-doing-code-review-incomplete-literal-and-partial-recovery-status.md`
- `docs/history/backlog/2026-09-23-receiving-review-marker-pr-live-shape.md` (filed as peer commit 9e107862 and absent from main; Task 2 materializes this file verbatim so the completion archive step can move it)
- `docs/history/backlog/2026-09-23-dfm-cr-f4-origins-gate-singular-form.md`
- `docs/history/backlog/2026-09-23-dfm-cr-f5f6f8-gate-suite-under-constraints.md`
- `docs/history/backlog/2026-09-23-dfm-cr-f7-receiving-review-tag-mapping.md`
- `docs/history/backlog/2026-09-23-dfm-cr-f9-pricing-phrase-clarity.md`
- `docs/history/backlog/2026-09-23-dfm-r6-gate-comment-misgrouping.md`
- `docs/history/backlog/2026-09-23-loop-guard-unit-clause-recycling-leg-wording.md`

Driving force: external + code-quality
Justification (non-principle force): the primary force is `external`: eight filed review findings deferred from certified executions and code reviews, each carrying precise fix text already accepted by its deferral decision (sources: the eight backlog item paths cited in "Origins and dispositions"); park-triage would take them because they are small, witnessed, mechanically verifiable fixes whose deferral cost grows with every touched surface.

## Terms

- **Origin**: one promoted backlog item from the parked P56 entry (`docs/tmp/future-plan-prompts-2026-09-16.md`, "P56" section); eight total.
- **Pins suite**: `scripts/check_maintenance_pins.sh`, the living mechanical pin suite over the maintenance, plans, and review-plan skills; run from anywhere inside the repo (it resolves the root via `git rev-parse --show-toplevel`).
- **Successor pins**: pin lines added to the pins suite that enforce what an archived plan's one-shot certification Validation Commands could enforce only once.
- **Origins-closure gate**: `scripts/check_plan_origins_closed.py`; archive arm (`--plan`) gates one plan's own origins, corpus arm is the warn-only survey.
- **Review-thread marker**: `docs/tmp/review-threads/<session-slug>.json` written per receiving-review's marker duty; consumed by `scripts/review_thread_gate.py`.
- **Staging record**: the review-staging Markdown review artifact plus its `.stats.json` sidecar.

## Assumptions

- assume the eight origins of the parked P56 entry are the whole scope; basis: the authoring payload names exactly those eight origin slugs and the parked entry enumerates them (`docs/tmp/future-plan-prompts-2026-09-16.md` lines 1132-1144; that file is session-local scratch and untracked, so the eight tracked item paths in the Origins block are the durable record of the scope).
- assume the origin file `2026-09-23-receiving-review-marker-pr-live-shape.md` is read from peer commit 9e107862 (branch `2026-09-22-codex-execute-plan-runtime-reconciliation`) where it was filed; it is absent from main `4cda5152` and every merged descendant; basis: `git log --all --follow` and `git cat-file` checks on 2026-09-24. Its bytes are the scope of record for that origin verbatim, and Task 2 embeds them in this plan as the durable source because that branch was rewritten on 2026-09-24, leaving the commit reachable only through reflog.
- assume the gate-tolerant marker schema: `--live` accepts the canonical `owner/repo#N` string and the session shape (numeric `pr` plus `repo` or `url`), the writer duty documents both, and `--inventory` is unchanged; basis: the origin's Expected paragraph requires a unit covering both shapes, which presupposes both shapes stay valid, and writer-strictness would strand every existing numeric marker.
- assume archived and completed plan bytes stay frozen: the dfm-cr-f5f6f8 "successors" leg and the loop-guard "plan freeze literal" leg land as successor pins in the pins suite plus recorded drift, never as edits to `docs/plans/completed/*`; basis: the plans metadata retrofit rule (archived plans are immutable context), the P54 plan's resolved-by-archive precedent, and dfm-r6's own "next natural edit / moot" framing.
- assume the two existing unit-clause count pins survive the reword unchanged and one new count pin is added for the reworded span; basis: pins suite lines pinning `exactly ONE mutating call implementing that recorded decision` and `The bound counts decided mutations, not primitive calls` are untouched by the fix sketch (verified by fixed-string count on 2026-09-24).
- assume authoring-time probes witnessed 2026-09-24 in this repo: (a) a plan whose only origin line is the singular form exits 0 ("no origins block; nothing to verify") while the plural-block fixture over the same open origin exits 1; (b) `review_thread_gate.py --live` with marker `"pr": 63, "repo": "owner/name"` exits 1 printing `error: marker pr '63' is not owner/repo#N; cannot fetch live` before any network call.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: lands the eight filed review findings' precise fix texts across the review-pipeline skills and their gates, so small witnessed defects deferred from certified executions stop compounding.

The origins cluster into four fixes and two bookkeeping records. Two record-accuracy literals in doing-code-review's posting path (bare `INCOMPLETE` header, missing recovered-findings status) become the transitions paragraph's full literal plus an explicit per-finding `posted` sentence. The review-thread marker schema drift (writer stores numeric `pr` plus `repo`, gate demands `owner/repo#N`) resolves by teaching `--live` both shapes behind one pure resolver, documented in the marker duty and done's consuming bullet. The origins-closure gate learns the canonized singular `Backlog origin:` header so single-origin plans stop evading archive-gate enforcement. The archived driving-force plan's weak one-shot gates (region-scoped counts, a contradiction needle the boundary family satisfies, missing tail needles, three ungated producer steps) get successor pins in the pins suite, which already carries the plans and review-plan surfaces. Two wording defects (receiving-review's stale future-tense tag-mapping bridge missing two tags; review-plan's compressed pricing phrase) get their precise rewordings. The loop-guard unit clause stops overstating the re-arm shape with a qualified parenthetical plus its own pin. dfm-r6 records a no-fix disposition against frozen archived bytes.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every landing literal named in a task's edit instruction is pinned by a dedicated fail-closed fixed-string grep; code shapes beyond those literals (the resolver's accepted shapes, the error exit) are owned by the unit suites; both authoring-time probes flip under the prescribed fixes (the singular-form fixture is detected; the numeric-pr session shape resolves offline through the new resolver unit).
- completeness: eight of eight origins dispositioned and traceable to a task or a recorded no-fix.
- minimality: no archived or frozen bytes change; existing gated needles survive; every forbidden-span sweep is scoped to the exact file the fix edits.

**Done when:**
- all tasks checked and the full Validation Commands block exits 0
- `python3 scripts/test_review_thread_gate.py` and `python3 scripts/test_check_plan_origins_closed.py` both pass
- `bash scripts/check_maintenance_pins.sh` exits 0 with the new successor pins present
- the pins suite passes `bash -n`

**Ship when:**
- the landed fixes survive the next maintenance review loop; no external or human-owned conditions.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/doing-code-review/SKILL.md`
- `agents/skills/receiving-review/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/done/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `scripts/review_thread_gate.py`
- `scripts/check_plan_origins_closed.py`
- `scripts/check_maintenance_pins.sh`
- `docs/history/backlog/2026-09-23-receiving-review-marker-pr-live-shape.md` *(new; byte-verbatim materialization from peer commit 9e107862, no prose edits)*

**Tests:**
- `scripts/test_review_thread_gate.py`
- `scripts/test_check_plan_origins_closed.py`

**Partially-in-scope files:** in `doing-code-review/SKILL.md` only the posting step's incomplete branch (step 6) and the Direct Mode bullet are open; every other section is frozen. In `receiving-review/SKILL.md` only the review-thread marker section and the driving-force tag-mapping bridge paragraph are open. In `done/SKILL.md` only the review-thread closure bullet is open. In `review-plan/SKILL.md` only the Declaration findings pricing paragraph is open. In `zcode.md` only the dispatch-discipline bullet's unit-clause sentence is open. In `review_thread_gate.py` only the marker schema docstring paragraph, `fetch_live`, and the new resolver are open. In `check_plan_origins_closed.py` only the module docstring, the header regex block, `extract_origin_basenames`, and its docstring are open. In the pins suite only the new and updated pin lines are open. Reject any review finding that touches a frozen region; document it as a separate backlog item instead.

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/plans/completed/**`; reason: archived plan bytes are frozen immutable context, including the dfm gate-suite plan and the loop-guard carve-out plan this plan only pins successors for
- `agents/skills/plans/SKILL.md`; reason: needle source only, no edit prescribed
- `docs/history/backlog/**` except the one origin file Task 2 materializes; reason: origin items move to the completed directory through the done flow at completion, not through plan execution, and only that one file must exist at the top level for the move to be mechanically gated
- `docs/tmp/**`; reason: session-local scratch, never committed

## Validation Commands

```bash
#!/usr/bin/env bash
# Run from the repository root. Exit 0 when every gate holds; print GATE FAIL lines otherwise.
set -u
fail=0
fail_msg() { echo "GATE FAIL: $1"; fail=1; }
R="$(git rev-parse --show-toplevel)"
DCR="$R/agents/skills/doing-code-review/SKILL.md"
RR="$R/agents/skills/receiving-review/SKILL.md"
RPV="$R/agents/skills/review-plan/SKILL.md"
DON="$R/agents/skills/done/SKILL.md"
ZC="$R/agents/skills/maintenance/zcode.md"
GT="$R/scripts/review_thread_gate.py"
OG="$R/scripts/check_plan_origins_closed.py"
PINS="$R/scripts/check_maintenance_pins.sh"
for f in "$DCR" "$RR" "$RPV" "$DON" "$ZC" "$GT" "$OG" "$PINS" \
         "$R/scripts/test_review_thread_gate.py" "$R/scripts/test_check_plan_origins_closed.py"; do
  test -f "$f" || { echo "GATE FAIL: missing required file $f"; fail=1; }
done

count1() { # count1 <fixed-string> <file> <desc>
  n=$(grep -oF -- "$1" "$2" | wc -l | tr -d ' ')
  [ "$n" -eq 1 ] || fail_msg "$3 (count $n, want 1)"
}
absent() { # absent <fixed-string> <file> <desc>; rc 1 is clean, rc 0 is a forbidden match, rc >= 2 is a tool error
  n=$(grep -cF -- "$1" "$2")
  rc=$?
  if [ "$rc" -ge 2 ]; then fail_msg "grep error (rc $rc) scanning $2"; return; fi
  [ "$n" -eq 0 ] || fail_msg "$3"
}

# Task 1: doing-code-review INCOMPLETE literals (r1 F2 + F3, r3 addendum)
count1 'header to `INCOMPLETE (posting incomplete; unlanded findings remain pending)`' "$DCR" "step 6 full INCOMPLETE literal missing"
count1 'Findings the recovery pass did land carry the per-finding Status `posted`.' "$DCR" "recovered-findings posted-status sentence missing"
count1 '(header `INCOMPLETE (posting incomplete; unlanded findings remain pending)`, finding left `pending`)' "$DCR" "Direct Mode full INCOMPLETE literal missing"
count1 '- Status: STAGED (not yet posted)' "$DCR" "STAGED validator anchor must survive untouched"
absent 'Status header to `INCOMPLETE`,' "$DCR" "bare step-6 INCOMPLETE literal still present"
absent '(header `INCOMPLETE`, ' "$DCR" "bare Direct Mode INCOMPLETE literal still present"

# Task 2: review-thread marker schema (dual shape behind one resolver)
count1 'def _resolve_live_target(' "$GT" "pure live-target resolver missing"
count1 'or the session shape, numeric ``pr`` plus ``repo`` (as ``owner/name``) or ``url`` (a GitHub pull-request URL)' "$GT" "gate docstring dual-shape sentence missing"
count1 'is not resolvable to owner/repo#N; cannot fetch live' "$GT" "rewritten live error message missing"
count1 'numeric digits plus `repo` (`owner/name`) or `url` (a GitHub pull-request URL); `review_thread_gate.py --live` accepts both' "$RR" "marker-duty dual-shape sentence missing"
count1 'the gate accepts both marker shapes: canonical `owner/repo#N`, or numeric `pr` plus `repo`/`url`' "$DON" "done --live dual-shape parenthetical missing"
# Task 2: materialized origin item byte identity (hermetic sha256 pin; source-agnostic)
test "$(shasum -a 256 "$R/docs/history/backlog/2026-09-23-receiving-review-marker-pr-live-shape.md" 2>/dev/null | cut -d' ' -f1)" = "0c27c76c8f1b8957857f3daf510358b9b0e64a61e371cd6e9273a891d4a9c84c" || fail_msg "materialized origin item missing or sha256 mismatch vs the peer commit 9e107862 bytes"

# Task 3: origins-closure gate singular form
count1 'ORIGIN_SINGULAR_RE = re.compile(' "$OG" "singular header regex missing"
count1 'a plan may also open its scope with a single `Backlog origin:` line' "$OG" "module docstring singular-form sentence missing"
count1 'the singular line ends the origins paragraph' "$OG" "extract docstring singular-form sentence missing"

# Task 4: successor pins for the archived dfm gate suite
count1 'dfm r1 F5 successor' "$PINS" "whole-file template count pin missing"
count1 "contradicts the plan's content is blocking" "$RPV" "narrowed contradiction pricing needle missing from review-plan"
grep -qF 'dfm r1 F5 successor' "$PINS" && grep -qF 'dfm r1 F6 successor' "$PINS" && grep -qF 'dfm r1 F8 successor' "$PINS" && grep -qF 'dfm r2 F1 successor' "$PINS" || fail_msg "one or more dfm successor pin lines missing"
count1 'why park-triage would or would not take it' "$R/agents/skills/plans/SKILL.md" "park-triage needle vanished from plans SKILL (pin target drift)"
count1 'otherwise the line reads `Backlog origin: none`' "$R/agents/skills/plans/SKILL.md" "backlog-origin-none needle vanished from plans SKILL (pin target drift)"
count1 'four driving principles (`efficiency`, `token-usage`, `simplicity`, `code-quality`)' "$R/agents/skills/plans/SKILL.md" "driving-principles enumeration needle vanished from plans SKILL (pin target drift)"

# Task 5: receiving-review tag-mapping bridge (dfm r1 F7)
count1 "Plans declare a driving force from the plans skill's own closed set" "$RR" "present-tense bridge opener missing"
count1 'its new-capability and external tags carry over verbatim' "$RR" "verbatim-carry mapping clause missing"
absent 'Once the certified plans driving-force metadata plan lands' "$RR" "stale future-tense bridge opener still present"

# Task 6: review-plan pricing phrase (dfm r1 F9)
count1 'a missing Gist TLDR, a force outside the taxonomy, and a non-principle force without its one-line justification are ordinary (non-blocking by default) findings' "$RPV" "explicit four-shape pricing sentence missing"
absent 'missing/coherent-shape defects' "$RPV" "compressed pricing phrase still present"

# Task 7: loop-guard unit clause reword
count1 "a parent re-arm's shape is per the recipe's operative shape (delete-plus-create today; the recycling leg only if a verified flip reopens it)" "$ZC" "qualified unit-clause parenthetical missing"
absent "shape is the recipe's delete-plus-create" "$ZC" "flat unit-clause identity claim still present"
count1 'bound unit-clause parenthetical count (dfm loop-guard successor)' "$PINS" "new unit-clause parenthetical pin missing"

# Task 8: dfm-r6 frozen-byte verification (no-fix disposition)
count1 'grep -q "declared driving force that contradicts" "$REV"' "$R/docs/plans/completed/2026-09-19-plan-driving-force-and-gist-tldr-metadata.md" "archived dfm plan boundary gate line must stay byte-frozen"
count1 'a parent re-arm'"'"'s shape is the recipe'"'"'s delete-plus-create' "$R/docs/plans/completed/2026-09-21-loop-guard-one-recorded-mutation-carve-out.md" "archived carve-out plan freeze literal must stay byte-frozen"

# Whole-suite mechanical gates
bash -n "$PINS" || fail_msg "pins suite failed bash -n"
bash "$PINS" || fail_msg "pins suite exit non-zero"
python3 "$R/scripts/test_review_thread_gate.py" 2>&1 | tail -1 | grep -q '^OK' || fail_msg "review_thread_gate unit suite not OK"
python3 "$R/scripts/test_check_plan_origins_closed.py" 2>&1 | tail -1 | grep -q '^OK' || fail_msg "origins-gate unit suite not OK"
bash "$R/scripts/check-no-em-dash.sh" file "$R/docs/plans/2026-09-24-p56-review-pipeline-micro-residuals.md" || fail_msg "em dash in plan bytes"

if [ "$fail" -ne 0 ]; then echo "Validation Commands: FAILED"; exit 1; fi
echo "Validation Commands: all gates hold"
```

### Task 1: doing-code-review INCOMPLETE literals (origin 1, r1 F2 + F3 and r3 addendum)

Files:
- `agents/skills/doing-code-review/SKILL.md`

- [x] In the posting step's incomplete branch (the step 6 sentence reading "When findings are still missing after this one recovery pass, set the staging doc's Status header to `INCOMPLETE`, leave the unlanded findings' Status as `pending`, and report the review as incomplete: name each finding that did not land."), replace "set the staging doc's Status header to `INCOMPLETE`" with "set the staging doc's Status header to `INCOMPLETE (posting incomplete; unlanded findings remain pending)`" so the branch carries the transitions paragraph's full literal (r1 F2; this also unwraps the r3 addendum's hard-wrapped quote, which lived only in the backlog item's code span) [class: IMPLEMENTATION_REQUIRED]
- [x] In the same step 6 branch, append after "name each finding that did not land." the sentence "Findings the recovery pass did land carry the per-finding Status `posted`." (r1 F3) [class: IMPLEMENTATION_REQUIRED]
- [x] In the Direct Mode bullet, replace `(header `INCOMPLETE`, finding left `pending`)` with `(header `INCOMPLETE (posting incomplete; unlanded findings remain pending)`, finding left `pending`)` (r1 F2) [class: IMPLEMENTATION_REQUIRED]
- [x] Do not touch the validator anchor line `- Status: STAGED (not yet posted)`; it stays byte-identical [class: IMPLEMENTATION_REQUIRED]
- [x] Re-run the archived landing-verification plan's whole gate block (`docs/plans/completed/2026-09-22-review-post-landing-verification.md`, Validation Commands) after the edits rather than reasoning about which exactly-once pins are adjacent, per the origin's note; expect it to still pass with the full literals [class: REPOSITORY_TEST]
- [x] Run the Task 1 gates of the plan's Validation Commands block; expect GREEN with each new literal exactly once and both bare-word spans absent [class: REPOSITORY_TEST]
- [x] Commit: `fix: doing-code-review full INCOMPLETE literal and recovered-findings posted status` [class: REPOSITORY_TEST]

### Task 2: review-thread marker dual shape behind one resolver (origin 2)

Files:
- `scripts/review_thread_gate.py`
- `scripts/test_review_thread_gate.py`
- `agents/skills/receiving-review/SKILL.md`
- `agents/skills/done/SKILL.md`

- [x] Add a pure resolver `def _resolve_live_target(marker):` returning `(owner, name, number, error)`; accepted shapes, first match wins: (a) canonical: `pr` is a string containing `#` whose base contains `/` and whose number part is all digits; (b) session shape with `repo`: `pr` is all digits and `repo` is `owner/name` containing exactly one `/`; (c) session shape with `url`: `pr` is all digits and `url` is a GitHub pull URL whose path after `github.com/` is exactly `<owner>/<name>/pull/<digits>` with non-empty owner and name and no extra segments; on no match return a nonempty error message [class: IMPLEMENTATION_REQUIRED]
- [x] Rewrite `fetch_live` to call the resolver; on error print `error: <message>` to stderr and exit 1, using the message `marker pr {pr!r} is not resolvable to owner/repo#N; cannot fetch live`; the gh invocation and the canned `--inventory` path are unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Update the module docstring's marker schema paragraph to name both shapes in the file's existing double-backtick RST style, with the exact sentence span pinned by the Validation Commands: "or the session shape, numeric ``pr`` plus ``repo`` (as ``owner/name``) or ``url`` (a GitHub pull-request URL)" [class: IMPLEMENTATION_REQUIRED]
- [x] Extend `scripts/test_review_thread_gate.py` (unittest, no network, module import of the gate script is safe because it keeps its main guard) with `ResolveLiveTargetTest#test_canonical_shape`; given `{"pr": "owner/repo#63"}`, expects `(owner, name, 63)` and empty error [class: REPOSITORY_TEST]
- [x] `ResolveLiveTargetTest#test_numeric_pr_with_repo`; given `{"pr": 63, "repo": "owner/name"}`, expects the same resolution and empty error (the authoring probe witnessed today's script exiting 1 on exactly this marker, so this test is RED before the fix) [class: REPOSITORY_TEST]
- [x] `ResolveLiveTargetTest#test_numeric_pr_with_url`; given `{"pr": 63, "url": "https://github.com/owner/name/pull/63"}`, expects the same resolution and empty error [class: REPOSITORY_TEST]
- [x] `ResolveLiveTargetTest#test_malformed_url_rejected`; given `{"pr": 63, "url": "https://github.com/owner/pull/63"}` (a pull URL missing the repo segment), expects a nonempty error so the live gh call can never point at a wrong repo [class: REPOSITORY_TEST]
- [x] `ResolveLiveTargetTest#test_unresolvable_error`; given `{"pr": 63}` with neither `repo` nor `url`, expects a nonempty error and no network access attempted [class: REPOSITORY_TEST]
- [x] `LiveGateErrorPathTest#test_unresolvable_marker_exits_before_network`; given a session-shape-unresolvable marker file under `--live` (subprocess run, hermetic: the resolver rejects before any gh invocation), expects exit 1 with `error: marker pr '63' is not resolvable to owner/repo#N; cannot fetch live` on stderr [class: REPOSITORY_TEST]
- [x] In receiving-review's review-thread marker section (the paragraph starting "When the session begins processing external PR feedback"), append the sentence "The `pr` field carries either the canonical `owner/repo#N` string, or the session shape: numeric digits plus `repo` (`owner/name`) or `url` (a GitHub pull-request URL); `review_thread_gate.py --live` accepts both." [class: IMPLEMENTATION_REQUIRED]
- [x] In done's review-thread closure bullet, insert after the existing text "or `--live`" the parenthetical " (the gate accepts both marker shapes: canonical `owner/repo#N`, or numeric `pr` plus `repo`/`url`)" [class: IMPLEMENTATION_REQUIRED]
- [x] Materialize the filed origin item byte-verbatim (no prose edits), producing the sha256 pinned in Validation Commands (`0c27c76c8f1b8957857f3daf510358b9b0e64a61e371cd6e9273a891d4a9c84c`, 28 lines): preferred source is the peer commit holding its only committed form, `git show 9e107862:docs/history/backlog/2026-09-23-receiving-review-marker-pr-live-shape.md > docs/history/backlog/2026-09-23-receiving-review-marker-pr-live-shape.md`; when that commit is unreachable (its branch was rewritten 2026-09-24 and the commit survives only in reflog), extract the exact bytes embedded in this plan below the materialization item instead: `sed -n '/^==== P56-ORIGIN-2-BYTES-BEGIN ====$/,/^==== P56-ORIGIN-2-BYTES-END ====$/p' docs/plans/2026-09-24-p56-review-pipeline-micro-residuals.md | sed '1d;$d' > docs/history/backlog/2026-09-23-receiving-review-marker-pr-live-shape.md`; either path must hash to the pin, the file must exist at the backlog top level so the archive gate classifies it instead of failing closed as missing, and the completion step can move it [class: IMPLEMENTATION_REQUIRED]

The origin item's exact bytes (28 lines, sha256 `0c27c76c8f1b8957857f3daf510358b9b0e64a61e371cd6e9273a891d4a9c84c`), extracted from peer commit 9e107862 at authoring time 2026-09-24; this embedded copy is the durable source when the peer commit is unreachable:

````markdown
==== P56-ORIGIN-2-BYTES-BEGIN ====
# Backlog: receiving-review marker `pr` shape vs review_thread_gate --live

- Priority: high
- Status: open
- Workflow: backlog
- Scope: `receiving-review` marker writer + `scripts/review_thread_gate.py` live fetch
- Owner: playbook maintenance
- Source: done pre-docs review-thread closure (2026-09-23); marker carried numeric `pr` plus separate `repo`, while `--live` requires `owner/repo#N`
- Why not fixed now: dispositions already closed the gate via canned inventory; schema alignment needs a coordinated writer+gate change and fixture update, not a session-side patch
- Driving force: workflow reliability
- capture hygiene: pending scan

## Problem

`review_thread_gate.py --live` fails with `marker pr '63' is not owner/repo#N; cannot fetch live` when the marker uses the receiving-review session shape (`"pr": 63`, `"repo": "owner/name"`). The gate docstring canonical shape is `"pr": "owner/repo#N"`. Agents must fall back to `gh api graphql` + `--inventory`, which is easy to miss and blocks done when network-only `--live` is attempted.

## Expected

One agreed marker schema: either the writer always stores `pr` as `owner/repo#N`, or `--live` accepts numeric `pr` plus `repo` / `url`. Keep canned `--inventory` working. Add a unit covering both shapes.

## Skill / step

- Skill: `agents/skills/receiving-review/SKILL.md` (marker duty / schema)
- Script: `scripts/review_thread_gate.py` (`--live` parse)

## Suspected root area

Schema drift between marker writer and gate live path; Fix-risk / done docs cite `--live` without mentioning the dual shape.
==== P56-ORIGIN-2-BYTES-END ====
````

- [x] Run `python3 scripts/test_review_thread_gate.py`; expect RED before the resolver lands (all six new tests fail: the five `ResolveLiveTargetTest` cases via AttributeError on the missing resolver, `LiveGateErrorPathTest` via its exact-stderr assertion) and GREEN after, with the pre-existing subprocess tests unaffected [class: REPOSITORY_TEST]
- [x] Commit: `fix: review-thread gate accepts numeric-pr session marker shape live` (the materialized origin file is part of this commit) [class: REPOSITORY_TEST]

### Task 3: origins-closure gate singular form (origin 3, dfm r1 F4)

Files:
- `scripts/check_plan_origins_closed.py`
- `scripts/test_check_plan_origins_closed.py`

- [x] Add `ORIGIN_SINGULAR_RE = re.compile(r"^\s*Backlog origin\s*:\s*(\S+)")` beside the existing plural header regex, with a comment naming the canonized single-origin template form [class: IMPLEMENTATION_REQUIRED]
- [x] In `extract_origin_basenames`, when not already inside a plural block and the line matches the singular regex: take the first capture group, strip trailing punctuation, and when it ends `.md` and passes `_is_backlog_ref` contribute its basename and end the scan (the singular line is the whole origins paragraph); a shape match that is not a backlog reference keeps scanning [class: IMPLEMENTATION_REQUIRED]
- [x] Update the module docstring's opening sentence and the `extract_origin_basenames` docstring to name both forms, inserting the exact spans pinned by the Validation Commands: "a plan may also open its scope with a single `Backlog origin:` line" in the module docstring; "the singular line ends the origins paragraph" in the function docstring [class: IMPLEMENTATION_REQUIRED]
- [x] Extend `PlanOriginsClosedTest` with `test_singular_origin_line_gates`; given a scratch repo whose plan under test opens with `Backlog origin: <path>` naming an open top-level item, expects exit 1 and the item basename in output (the authoring probe witnessed today's script exiting 0 on exactly this fixture, so this test is RED before the fix) [class: REPOSITORY_TEST]
- [x] `PlanOriginsClosedTest#test_singular_origin_closed_item_passes`; given the same singular shape with the item archived under the completed directory, expects exit 0 [class: REPOSITORY_TEST]
- [x] `PlanOriginsClosedTest#test_singular_origin_non_backlog_path_ignored`; given a singular line naming a non-backlog `.md` path, expects exit 0 via the trivial no-origins arm [class: REPOSITORY_TEST]
- [x] Run `python3 scripts/test_check_plan_origins_closed.py`; expect the new tests RED before the fix and GREEN after, with the existing fixture cases (six tests) unaffected [class: REPOSITORY_TEST]
- [x] Commit: `fix: origins-closure gate parses the singular Backlog origin header form` [class: REPOSITORY_TEST]

### Task 4: successor pins for the archived dfm gate suite (origin 4, dfm r1 F5/F6/F8 and r2 F1)

Files:
- `scripts/check_maintenance_pins.sh`

- [x] In the pins suite's plans section (the `PL="$repo/agents/skills/plans/SKILL.md"` block), add the F5 whole-file count pins in the suite's raw count-pin form: `Driving force: <tag>` exactly 1 and `TLDR: <what changes>` exactly 1 over `$PL`, with one shared comment line above the pair reading `dfm r1 F5 successor (whole-file; the archived plan's gates saw only the extracted template region)` [class: IMPLEMENTATION_REQUIRED]
- [x] In the pins suite's review-plan section (the `RP="$repo/agents/skills/review-plan/SKILL.md"` block), add the F6 successor pin: presence of the narrowed needle `contradicts the plan's content is blocking` over `$RP`, on a line commented `dfm r1 F6 successor (the archived gate's shorter needle was satisfied by the boundary sixth family without any pricing sentence)`; the needle already exists in the surface today, so the pin lands GREEN [class: IMPLEMENTATION_REQUIRED]
- [x] Add the F8 successor pins over `$PL`: presence of "where `external` must cite its source" and presence of "why park-triage would or would not take it", with one shared comment line above the pair reading `dfm r1 F8 successor (taxonomy tail and park-triage half had no needles)` [class: IMPLEMENTATION_REQUIRED]
- [x] Add the r2 F1 producer-step pins: presence of `Declaration audit` over `$RP`, and over `$PL` presence of "otherwise the line reads `Backlog origin: none`" and of "four driving principles (`efficiency`, `token-usage`, `simplicity`, `code-quality`)", with one shared comment line above the group reading `dfm r2 F1 successor (the archived gates left these producer steps ungated)` [class: IMPLEMENTATION_REQUIRED]
- [x] Run `bash scripts/check_maintenance_pins.sh`; expect exit 0 with all new pins holding (every pinned literal already exists on its surface; verified by fixed-string count at authoring time on 2026-09-24) [class: REPOSITORY_TEST]
- [x] Run the Task 4 gates of the Validation Commands block; expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `test: successor pins for the archived driving-force gate suite gaps` [class: REPOSITORY_TEST]

### Task 5: receiving-review tag-mapping bridge (origin 5, dfm r1 F7)

Files:
- `agents/skills/receiving-review/SKILL.md`

- [x] In the bridge paragraph currently reading `Once the certified plans driving-force metadata plan lands, plans declare a driving force from that skill's own closed set; the plans efficiency tag reads as performance or token-usage, its code-quality force maps to maintainability, and its simplicity force maps here unchanged.`, replace the whole paragraph with `Plans declare a driving force from the plans skill's own closed set; the plans efficiency tag reads as performance or token-usage, its code-quality force maps to maintainability, its simplicity force maps here unchanged, and its new-capability and external tags carry over verbatim.` (present tense, the two missing tags mapped) [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Task 5 gates of the Validation Commands block; expect GREEN with the stale opener absent from the file [class: REPOSITORY_TEST]
- [x] Commit: `fix: receiving-review plans tag mapping present tense and complete` [class: REPOSITORY_TEST]

### Task 6: review-plan pricing phrase (origin 6, dfm r1 F9)

Files:
- `agents/skills/review-plan/SKILL.md`

- [x] In the Declaration findings paragraph, replace `Pricing: missing/coherent-shape defects are ordinary (non-blocking by default) findings; a force that contradicts the plan's content is blocking.` with `Pricing: a missing driving-force line, a missing Gist TLDR, a force outside the taxonomy, and a non-principle force without its one-line justification are ordinary (non-blocking by default) findings; a force that contradicts the plan's content is blocking.` so the four shape classes are named explicitly while the gated needles `a missing driving-force line`, `non-blocking by default`, and `contradicts the plan's content is blocking` all survive [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Task 6 gates of the Validation Commands block; expect GREEN with the compressed phrase absent [class: REPOSITORY_TEST]
- [x] Commit: `fix: review-plan declaration pricing names the four shape classes` [class: REPOSITORY_TEST]

### Task 7: loop-guard unit-clause reword (origin 7)

Files:
- `agents/skills/maintenance/zcode.md`
- `scripts/check_maintenance_pins.sh`

- [x] In the dispatch-discipline bullet's carve-out unit clause, replace `and a parent re-arm's shape is the recipe's delete-plus-create, so deleting` with `and a parent re-arm's shape is per the recipe's operative shape (delete-plus-create today; the recycling leg only if a verified flip reopens it), so deleting` so the flat identity claim no longer overstates the recipe's conditional shape [class: IMPLEMENTATION_REQUIRED]
- [x] In the pins suite's zcode section, beside the existing single-call bound and unit-clause count pins, add the raw count pin commented `bound unit-clause parenthetical count (dfm loop-guard successor)`: the new parenthetical needle from the Validation Commands exactly 1 over `$Z` [class: IMPLEMENTATION_REQUIRED]
- [x] Leave the two existing count pins and the archived carve-out plan's freeze literal byte-identical; their counted spans survive the reword, and the archived plan is immutable context (the recorded drift: its quoted parenthetical documents the shape at its certification date) [class: IMPLEMENTATION_REQUIRED]
- [x] Run `bash scripts/check_maintenance_pins.sh`; expect exit 0 including the new pin [class: REPOSITORY_TEST]
- [x] Commit: `fix: qualify loop-guard re-arm shape deferral for the inoperative recycling leg` [class: REPOSITORY_TEST]

### Task 8: dfm-r6 disposition verification (origin 8, no-fix by record)

Files:
- none (read-only verification; the disposition is recorded in "Origins and dispositions" below)

- [x] Verify the archived dfm plan's misfiled boundary gate (the line reading `grep -q "declared driving force that contradicts" "$REV"` sitting under the `# Task 2 gates:` comment) stays byte-frozen; the precise fix text (move it below the `# Task 3 gates:` comment or add a dedicated comment, and update the Task 3 witness bullet to four dedicated Task 3 greps) applies only if that plan is ever unfrozen, which the retrofit rule keeps out of scope [class: REPOSITORY_TEST]
- [x] Run the Task 8 gate of the Validation Commands block; expect GREEN with the archived line exactly once [class: REPOSITORY_TEST]
- [x] Commit: none (read-only task; no tree change) [class: REPOSITORY_TEST]

### Task 9: full validation

Files:
- none (verification only)

- [x] Run the whole Validation Commands block from the repository root; expect the single closing line `Validation Commands: all gates hold` and exit 0 [class: REPOSITORY_TEST]

## Origins and dispositions

- `2026-09-23-doing-code-review-incomplete-literal-and-partial-recovery-status.md`: fixed by Task 1 (r1 F2 full literal, r1 F3 recovered-findings status, r3 addendum unwrapped by prescribing the full literal in the task text)
- `2026-09-23-receiving-review-marker-pr-live-shape.md`: fixed by Task 2 (gate-tolerant dual shape; scope of record read from peer commit 9e107862 where the item was filed, absent from main); Task 2 also materializes the item file byte-verbatim at the backlog top level so the completion archive step moves every origin mechanically
- `2026-09-23-dfm-cr-f4-origins-gate-singular-form.md`: fixed by Task 3 (regex extension option, the origin's first-listed fix; template annotation option not taken)
- `2026-09-23-dfm-cr-f5f6f8-gate-suite-under-constraints.md`: fixed by Task 4 as successor pins (the origin's "edit the archived plan's Validation Commands or their successors" resolves to successors because archived bytes are frozen)
- `2026-09-23-dfm-cr-f7-receiving-review-tag-mapping.md`: fixed by Task 5
- `2026-09-23-dfm-cr-f9-pricing-phrase-clarity.md`: fixed by Task 6
- `2026-09-23-loop-guard-unit-clause-recycling-leg-wording.md`: fixed by Task 7 (the origin's "update the two identical pins" leg resolves to: both existing pins survive verbatim and one successor pin is added; the "plan freeze literal" leg resolves to recorded drift per the archived-bytes invariant)
- `2026-09-23-dfm-r6-gate-comment-misgrouping.md`: no fix by record (origin's own moot/next-natural-edit framing; precise fix text preserved here and in the item; verification only, Task 8)
