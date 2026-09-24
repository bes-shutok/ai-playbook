# Plan: done-skill/validator wording one-offs trio

Backlog origins (scope of record):
- `docs/history/backlog/2026-09-06-done-marker-r5-residuals.md` (R5-1, R5-2, R5-3)
- `docs/history/backlog/2026-09-06-done-run-start-probe-coverage.md` (r1-r4 probe pins; landed post-archive in the origin plan)
- `docs/history/backlog/2026-09-06-vrs-unclosed-fence-warning-print-wording.md` (validator warning reword)

## Terms

- Run-start marker: the per-done-run file `run-start-<UTCtimestamp>` written under `{tmp_dir}/done-session/` at done Step 0.
- Echo-loss fallback: the Step 0 rule governing what Step 1.5 and the Step 2.62 sweep do when the echoed marker path is lost or matches nothing at gate time (conservative gating; never guess by recency).
- Conservative gating: treating every ignored-arm plan as this session's deliverable when the session window cannot be anchored; plans are named, never skipped.
- Content-match confirmation: verifying a marker's identity by reading the fields recorded in the marker file instead of relying on chat recall of the echoed path alone.
- Unclosed-fence warning: the fallback warning `parse_markdown_findings` emits through the optional `warn` callback when the Findings section has an unclosed code fence.

## Assumptions

- assume the R5-1 fix is a one-clause acknowledgment in the skill, not per-repo marker writes at each Step 1.5 invocation; basis: the backlog item offers both directions, the acknowledgment is additive prose with no new runtime state, and conservative gating is already the safe outcome for a secondary repo.
- assume R5-2 ships as additive hardening (content-bearing marker plus content-match confirmation) with unchanged gating semantics; basis: the backlog item marks it "hardening, not a gap" and every confusion path already degrades to conservative gating.
- assume the archived origin plan `docs/plans/completed/2026-09-04-done-deliverables-log-dedupe-and-anchors.md` is edited additively only: a dated post-archive addendum section carries the new probes and a dated annotation sits under Task 1; the frozen task bytes and the original Validation Commands block are not rewritten; basis: the probe backlog item prescribes a post-archive edit and offers "annotate that the snippet evolved" as the alternative to rewriting the stale quote, and frozen history stays immutable.
- assume the probe backlog item's "count 2" claim for `prune no `run-start-*` markers this run` is stale; the measured count on 2026-09-06 is 1 (the Step 0 canonical statement reads "prunes no", a different literal); basis: `grep -cF` measured at authoring time; the probes therefore pin presence, and the mechanical pin audit re-measures counts at execution.
- assume the three backlog origin files move to `{backlog_completed_dir}` only in this plan's completion task; basis: plans skill Plan Lifecycle.

## Gist & Examples

**Area 1: the done run-start marker (two backlog items).**

Before (today): the run-start marker is an empty file. Step 1.5 anchors this run's session window on the newest marker written by a previous done run and uses the echoed marker path recalled from chat context to identify the current run's marker; if the recall is lost, the echo-loss fallback applies conservative gating. In a multi-repo done run (the gate runs once per repo), a secondary repo's gate compares the starting repo's echoed path against the secondary repo's own `{tmp_dir}/done-session/`, deterministically finds no match, and conservatively gates every ignored-arm plan there: safe, but the operator sees spurious refusal noise with no explanation. Identity of a marker rests entirely on recalling the echoed path; the file itself carries no identity.

After (this plan): the marker is content-bearing: its single line records the creation epoch, the resolved `$REPO_TOP`, and the writing shell PID. Step 0 explicitly names its loss rule as "the Step 0 echo-loss fallback" (the label Step 1.5 already back-references). Step 1.5 gains a confirmation clause: when the echoed marker file exists, read it; its recorded `$REPO_TOP` must equal this repo's resolved root, and content naming a different repository is a cross-repo done run, so this repo's gate deterministically lands in the conservative-gating branch (expected and named for a secondary repo, never a silent skip). Step 2.62 confirms the current-run marker the same way, and a content mismatch applies the same no-prune rule as a lost echo.

Example: a done run starts in repo A (marker written under A's `docs/tmp/done-session/`), then the session commits in repo B. Today B's gate reports every `!!` plan as gated with no reason. After this plan B's gate reports the cross-repo acknowledgment: the anchor belongs to repo A, so B's window is unanchorable and conservative gating is the expected, named outcome.

**Area 2: the unclosed-fence warning tail.**

Before (today): `parse_markdown_findings` no longer prints; the warning travels through the `warn` callback into `ValidationResult.warnings` and surfaces as `WARN:` lines or JSON entries. Its tail clause still says "so a full validation run may print it more than once", stale from the pre-callback print era (a current-v1 validation parses the Findings section twice, so the warning is genuinely reported twice).

After (this plan): the tail reads "so a full validation run may report it more than once". The selftest's full-text equality pin (and any other pin of the tail clause) is updated in the same change, RED first.

**Area 3: post-archive probe pins.** The origin plan's Validation Commands block was checkbox-frozen during its execution, so the r1-r4 probe literals landed in a backlog item instead. This plan appends a dated addendum section to the archived plan carrying those probes as an executable block, plus a dated annotation under Task 1 noting that the Step 0 snippet evolved during Phase 3 rounds (the "verbatim"/"four lines" claim reflects authoring time, not the final snippet).

## Evaluation Criteria

**Quality dimensions:**
- correctness: every obligation from the three backlog items maps to a dedicated probe in Validation Commands; each new-wording and new-content pin was absent on today's tree at authoring time (measured, recorded below), and the stale-wording forbidden sweep fires today (measured: 2 hits).
- no-regression: every pre-existing pinned literal in the done skill (snippet lines, canonical echo-loss statement, prune clauses, producer-scope wording) survives Task 2; survival pins enforce this.
- validation breadth: Validation Commands cover both areas (validator script, done skill) and the archived-plan addendum, not one entry point.
- scope fidelity: the archived plan's frozen bytes are untouched; edits are the addendum section and the Task 1 annotation only.

**Done when:**
- `python3 scripts/validate_review_staging.py --selftest` exits 0 on the modified tree.
- The full Validation Commands block exits 0 from the repo root with `VALIDATION OK`.
- `bash -n` over the Validation Commands block exits 0.
- The three backlog origins are archived under `docs/history/backlog/completed/` with `Status: done`.

**Ship when:**
- Runtime copy redeploy of the done skill and validator to `~/.ai-playbook` mirrors (separate pending sync, not this repo's tree).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/validate_review_staging.py`
- `agents/skills/done/SKILL.md`

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Tests:**
- the `--selftest` checks inside `scripts/validate_review_staging.py` (same file; the `(# unclosed-fence-warning)` equality pin is the test surface)

**Documentation:**
- `docs/plans/completed/2026-09-04-done-deliverables-log-dedupe-and-anchors.md` (addendum + Task 1 annotation only; all other sections frozen)
- `docs/history/backlog/2026-09-06-done-marker-r5-residuals.md`, `docs/history/backlog/2026-09-06-done-run-start-probe-coverage.md`, `docs/history/backlog/2026-09-06-vrs-unclosed-fence-warning-print-wording.md` (git mv to `docs/history/backlog/completed/` plus a `Status: done` line; no prose rewording)

**Out of scope; reject unless plan-related:**
- `scripts/plan_readiness.py`; reason: peer-modified in the working tree by another session, untouched by this plan.
- `~/.ai-playbook/scripts/` deployed runtime copies; reason: separate pending redeploy, not this repository's tree.
- `docs/reviews/` history artifacts; reason: immutable review history.
- `README.md`; reason: no catalog or usage change.

## Validation Commands

```bash
#!/usr/bin/env bash
# Run from the repo root. Prints VALIDATION OK and exits 0 on success.
fail() { echo "FAIL: $1"; exit 1; }
V=scripts/validate_review_staging.py
S=agents/skills/done/SKILL.md
P=docs/plans/completed/2026-09-04-done-deliverables-log-dedupe-and-anchors.md
B=docs/history/backlog
BC=docs/history/backlog/completed
[ -f "$V" ] || fail "validator missing"
[ -f "$S" ] || fail "done SKILL.md missing"
[ -f "$P" ] || fail "archived origin plan missing"
python3 "$V" --selftest || fail "selftest"
# Task 1: warning transport wording (stale-wording sweep is negated: it must find nothing)
if grep -Fq "print it more than once" "$V"; then fail "stale print wording still present"; fi
grep -Fq "report it more than once" "$V" || fail "new report wording missing"
[ "$(grep -cF 'report it more than once' "$V")" -eq 2 ] || fail "report wording count != 2 (emit + selftest pin)"
# Task 2: new done-skill obligations
if grep -Fq "empty per-run marker file" "$S"; then fail "stale empty-marker wording still present"; fi
grep -Fq "content-bearing per-run marker file" "$S" || fail "reworded content-bearing marker prose missing"
grep -Fq '$(date -u +%s) ${REPO_TOP%/} $$' "$S" || fail "content-bearing marker literal missing"
grep -Fq "The marker is content-bearing" "$S" || fail "content-bearing prose missing"
grep -Fq "content-match confirmation" "$S" || fail "content-match confirmation prose missing"
grep -Fq "everything between them is the repo root" "$S" || fail "marker field-order clause missing"
grep -Fq "This rule is the Step 0 echo-loss fallback" "$S" || fail "echo-loss label missing"
grep -Fq "cross-repo done run" "$S" || fail "cross-repo acknowledgment missing"
grep -Fq "confirm its identity from its content" "$S" || fail "gate content confirmation missing"
grep -Fq "a content mismatch applies the same no-prune rule" "$S" || fail "sweep content mismatch rule missing"
# Task 2: survival pins (pre-existing obligations must remain)
grep -Fq 'mkdir -p "${TMP_DIR%/}/done-session"' "$S" || fail "snippet mkdir line lost"
grep -Fq 'run-start-$(date -u +%Y%m%dT%H%M%SZ)' "$S" || fail "marker filename literal lost"
grep -Fq 'MARKER="$(cd "$(dirname "$MARKER")" && pwd)/$(basename "$MARKER")"' "$S" || fail "canonicalization line lost"
grep -Fq "matches no marker at gate time" "$S" || fail "canonical echo-loss statement lost"
grep -Fq "Keep the echoed marker path in chat context" "$S" || fail "marker-echo chat-context sentence lost"
grep -Fq "apply the Step 0 echo-loss fallback" "$S" || fail "Step 1.5 back-reference lost"
grep -Fq "never substitute the newest on-disk marker" "$S" || fail "never-recency clause lost"
grep -Fq 'prune no `run-start-*` markers this run' "$S" || fail "Step 2.62 prune-skip clause lost"
grep -Fq "prunes no" "$S" || fail "Step 0 canonical prune clause lost"
grep -Fq "NEVER remove the newest previous-run marker" "$S" || fail "never-delete pruning lost"
grep -Fq "create the directory if missing" "$S" || fail "directory-creation wording lost"
grep -Fq 'excluding `{plans_completed_dir}`' "$S" || fail "producer scope exclusion lost"
grep -Fq "remove every line listing that path" "$S" || fail "removal-rule wording lost"
grep -Fq "one repo-relative path per line" "$S" || fail "repo-relative path form lost"
grep -Fq 'head -n 1' "$S" || fail "r2 head -n 1 lost"
grep -Fq 'case "$TMP_DIR"' "$S" || fail "r2 relative-path anchor lost"
# Task 3: archived-plan addendum present and intact
grep -Fq "Post-archive addendum (2026-09-06)" "$P" || fail "addendum section missing"
grep -Fq "Post-archive annotation (2026-09-06)" "$P" || fail "Task 1 annotation missing"
for lit in 'mkdir -p "${TMP_DIR%/}/done-session"' 'run-start-$(date -u +%Y%m%dT%H%M%SZ)' "matches no marker at gate time" 'prune no `run-start-*` markers this run'; do
  grep -Fq "$lit" "$P" || fail "addendum lost literal: $lit"
done
# Task 4: backlog origins archived as done
for b in 2026-09-06-done-marker-r5-residuals 2026-09-06-done-run-start-probe-coverage 2026-09-06-vrs-unclosed-fence-warning-print-wording; do
  [ -f "$BC/$b.md" ] || fail "backlog origin not archived: $b"
  grep -q "^Status: done" "$BC/$b.md" || fail "backlog origin not marked done: $b"
  if [ -f "$B/$b.md" ]; then fail "backlog origin still open: $b"; fi
done
echo "VALIDATION OK"
```

Authoring-time measurements (2026-09-06, pre-change tree): the stale-wording sweep pattern `print it more than once` has 2 hits in `$V` (the sweep is RED-today); every Task 1/2 new-obligation literal above has 0 hits today in its target; every survival literal has at least 1 hit today; `Post-archive addendum (2026-09-06)` has 0 hits in `$P`.

### Task 1: Reword the unclosed-fence warning tail (RED then GREEN)

Files:
- `scripts/validate_review_staging.py`

- [x] RED: in the selftest check whose full name begins `fence fix: unclosed fence warning passed once to the warn callback` (the `warns[0] ==` full-text equality pin; the other `(# unclosed-fence-warning)` check, the default silent-stderr one, is NOT touched), replace the tail fragment `"so a full validation run may "` `"print it more than once"` with `"so a full validation run may "` `"report it more than once"`; given the emit site still reads `print it more than once`, expects exactly that check to fail while all other selftest checks stay green
- [x] Run → expect RED: `python3 scripts/validate_review_staging.py --selftest` (fails the `fence fix: unclosed fence warning passed once to the warn callback...` check only)
- [x] GREEN: in `parse_markdown_findings`, in the `warn(...)` message for the unclosed-fence fallback, replace `print it more than once` with `report it more than once`; change nothing else in the message
- [x] Run → expect GREEN: `python3 scripts/validate_review_staging.py --selftest`
- [x] Interim probes: `grep -cF "print it more than once" scripts/validate_review_staging.py` prints 0; `grep -cF "report it more than once" scripts/validate_review_staging.py` prints 2
- [x] Commit: `fix: unclosed-fence warning tail names the warn-callback transport`

### Task 2: done run-start marker content identity, cross-repo acknowledgment, echo-loss naming

Files:
- `agents/skills/done/SKILL.md`

All edits are additive; no existing sentence or snippet line is deleted, with ONE prescribed exception: the Step 0 prose word `empty` is reworded to `content-bearing` in the checklist item below (the stale `empty` wording would contradict the content-bearing marker and break content-match confirmation). The Step 0 snippet line `: > "$MARKER" && printf 'run-start marker: %s\n' "$MARKER"` is the only line replaced.

- [x] Step 0 snippet: replace `: > "$MARKER" && printf 'run-start marker: %s\n' "$MARKER"` with `printf '%s\n' "$(date -u +%s) ${REPO_TOP%/} $$" > "$MARKER" && printf 'run-start marker: %s\n' "$MARKER"`
- [x] Step 0 prose (the run-start marker paragraph): reword `write an empty per-run marker file` to `write a content-bearing per-run marker file`, then append after `Marker pruning is governed solely by the Step 2.62 sweep.` the sentence `The marker is content-bearing: its single line records the creation epoch, the resolved \`$REPO_TOP\`, and the writing shell PID, so gate-time identity can rely on content-match confirmation instead of chat recall alone.`
- [x] Step 0 prose (the paragraph beginning `Keep the echoed marker path in chat context`): append at the end, after `never guess by recency.`, the sentence `This rule is the Step 0 echo-loss fallback that Step 1.5 back-references.`
- [x] Step 1.5 prose: inside the anchor parenthetical, immediately after `never substitute the newest on-disk marker` and before `; the window runs from the anchor marker's timestamp to gate time`, insert `; when the echoed marker file exists, confirm its identity from its content (the recorded \`$REPO_TOP\` must equal this repo's resolved repo root); recorded content naming a different repository is a cross-repo done run: the starting repo's marker cannot anchor this repo's window, so this repo's gate deterministically lands in the conservative-gating branch (expected and named for a secondary repo; the gate still names every gated plan and never silently skips one)`
- [x] Step 2.62 prose: after `(never guess by recency).` in the `done-session/` bullet, append `Confirm the recalled current-run marker from its content the same way: a recorded \`$REPO_TOP\` matching this repo plus the run-unique epoch and PID identify the current run's marker; a content mismatch applies the same no-prune rule as a lost echo.`
- [x] Characterization (must stay true, enforced by the survival pins): the mkdir line, the marker filename literal, the canonicalization line, the canonical echo-loss statement, the Step 1.5 back-reference and never-recency clause, both prune clauses, the never-delete pruning, directory-creation, producer-scope, removal-rule, repo-relative, `head -n 1`, and `case "$TMP_DIR"` wordings are all unchanged
- [x] Interim probes (each must print at least 1): `grep -cF '$(date -u +%s) ${REPO_TOP%/} $$' agents/skills/done/SKILL.md`, `grep -cF "cross-repo done run" agents/skills/done/SKILL.md`, `grep -cF "This rule is the Step 0 echo-loss fallback" agents/skills/done/SKILL.md`, `grep -cF "a content mismatch applies the same no-prune rule" agents/skills/done/SKILL.md`; and the survival probe `grep -cF "matches no marker at gate time" agents/skills/done/SKILL.md` still prints 1
- [x] Commit: `skills: done run-start marker content identity and cross-repo gating acknowledgment`

### Task 3: post-archive probe addendum in the archived deliverables-log plan

Files:
- `docs/plans/completed/2026-09-04-done-deliverables-log-dedupe-and-anchors.md`

- [x] Append at the end of the file the section `## Post-archive addendum (2026-09-06): run-start marker probe pins` with this intro line and this exact fenced block:

    Intro: `Added by the wording-trio plan for backlog 2026-09-06-done-run-start-probe-coverage (r1-r4 probe literals; the original Validation Commands block stays frozen; counts re-measured at authoring). Run from the repo root.`

    ```bash
    F=agents/skills/done/SKILL.md
    fail() { echo "FAIL: $1"; exit 1; }
    [ -f "$F" ] || fail "done SKILL.md missing"
    grep -Fq 'mkdir -p "${TMP_DIR%/}/done-session"' "$F" || fail "snippet mkdir line"
    grep -Fq 'run-start-$(date -u +%Y%m%dT%H%M%SZ)' "$F" || fail "marker filename literal"
    grep -Fq 'MARKER="$(cd "$(dirname "$MARKER")" && pwd)/$(basename "$MARKER")"' "$F" || fail "canonicalization line"
    # the sed literal is pinned as two fixed fragments (shell-quoting the whole line would need embedded single-quote escapes)
    grep -Fq 's/^tmp_dir = ["' "$F" || fail "sed literal head"
    grep -Fq '\1/p' "$F" || fail "sed literal tail"
    grep -Fq "matches no marker at gate time" "$F" || fail "echo-loss canonical statement"
    grep -Fq "Keep the echoed marker path in chat context" "$F" || fail "marker-echo chat-context sentence"
    grep -Fq "apply the Step 0 echo-loss fallback" "$F" || fail "Step 1.5 back-reference"
    grep -Fq "never substitute the newest on-disk marker" "$F" || fail "never-recency clause"
    grep -Fq 'prune no `run-start-*` markers this run' "$F" || fail "Step 2.62 prune-skip clause"
    grep -Fq "prunes no" "$F" || fail "Step 0 canonical prune clause"
    grep -Fq "NEVER remove the newest previous-run marker" "$F" || fail "never-delete pruning"
    grep -Fq "create the directory if missing" "$F" || fail "directory creation"
    grep -Fq 'excluding `{plans_completed_dir}`' "$F" || fail "producer scope exclusion"
    grep -Fq "remove every line listing that path" "$F" || fail "removal rule"
    grep -Fq "one repo-relative path per line" "$F" || fail "repo-relative path form"
    grep -Fq 'head -n 1' "$F" || fail "r2 head -n 1"
    grep -Fq 'case "$TMP_DIR"' "$F" || fail "r2 relative-path anchor"
    echo "ADDENDUM PROBES OK"
    ```

- [x] Under the Task 1 heading in the same archived plan, append this dated annotation line (italic, directly after the heading): `*Post-archive annotation (2026-09-06): the Step 0 snippet evolved during Phase 3 review rounds (r1: REPO_TOP resolution, the $REPO_TOP-anchored fallback, the MARKER variable, the printf echo; r2: head -n 1 and the case "$TMP_DIR" relative-path anchor; 2026-09-06 wording-trio plan: the content-bearing marker line). The verbatim/four-lines claim in the checklist text reflects authoring time, not the final snippet.*`
- [x] Run the addendum block from the repo root → expect `ADDENDUM PROBES OK` (every addendum literal pins a pre-existing skill wording, so all are on disk once Task 2 has landed; Task 2's new obligations are pinned by the main Validation Commands block, not by the addendum)
- [x] No other byte of the archived plan changes
- [x] Commit: `docs: post-archive probe addendum for done run-start marker behaviors`

### Task 4: archive backlog origins and final validation

Files:
- `docs/history/backlog/2026-09-06-done-marker-r5-residuals.md` *(moved)*
- `docs/history/backlog/2026-09-06-done-run-start-probe-coverage.md` *(moved)*
- `docs/history/backlog/2026-09-06-vrs-unclosed-fence-warning-print-wording.md` *(moved)*

- [x] `git mv` each of the three backlog files to `docs/history/backlog/completed/` and set `Status: done` in the same edit (no prose rewording; note the vrs origin's status line is the bold `- **Status:** open` form: replace that whole line with the plain `Status: done`)
- [x] Run the full Validation Commands block from the repo root → expect exit 0 with `VALIDATION OK`
- [x] `bash -n` over the Validation Commands block → expect exit 0
- [x] Mechanical pin audit: for every pinned fragment in the Validation Commands block, `grep -cF` on its target file returns at least 1 for positive pins and the stale-wording sweep returns 0; fix both sides of any mismatch in the same edit
- [x] Commit: `backlog: complete done-skill/validator wording trio origins`

## Post-execution review folds (2026-09-07)

Recorded during the Phase 3 review loop (r1 panel + r2 targeted pass), superseding the byte-literal expectations above where noted:

- r1 F1 (echo×4): the Task 3 commit checkbox above was ticked after the fact; commit `22ec577` is its evidence.
- r1 F2: the Task 1 annotation in `docs/plans/completed/2026-09-04-done-deliverables-log-dedupe-and-anchors.md` was extended in place (2026-09-07 clause naming the now-stale `write an empty per-run marker file` probe in that plan's frozen Validation Commands block). The prescribed annotation text ending `...not the final snippet.*` is therefore no longer verbatim on disk, and the `[x] No other byte of the archived plan changes` tick holds only as of Task 3's own commit (`22ec577`), not at HEAD.
- r1 F3: a field-order sentence was appended after the Step 0 content-bearing sentence in `agents/skills/done/SKILL.md` (first field epoch, last field PID, everything between them is the repo root), now pinned by the `everything between them is the repo root` Validation Command above.
- r1 F4 (deferred): marker-content persistence onto the docs branch → backlog `docs/history/backlog/2026-09-07-run-start-marker-content-docs-branch-leak.md`.
- r3 F1: the Step 2.62 content-confirmation sentence (prescribed verbatim by Task 2) over-claimed identity strength: the echo prints only the marker path, so epoch and PID have no gate-time comparison witness. Reworded in `agents/skills/done/SKILL.md` to the checkable form (a recorded `$REPO_TOP` matching this repo is the confirmable field; epoch and PID are recorded for post-hoc audit); the pinned `a content mismatch applies the same no-prune rule` clause is unchanged.
- r3 F2: the r1 F3 fold bullet above originally said the clause was "appended to the Step 0 content-bearing sentence"; corrected to "appended after".
- r4 F1: the Step 0 content-bearing prose now says "the trailing-slash-stripped resolved `$REPO_TOP`" to match the snippet's `${REPO_TOP%/}` literal.

## Disposition of migrated backlog items

- docs/history/backlog/completed/2026-09-04-done-4c-mutation-append-wording.md: disposition folded into 2026-09-06-done-skill-validator-wording-trio.md (2026-09-25); per-item file deleted.
