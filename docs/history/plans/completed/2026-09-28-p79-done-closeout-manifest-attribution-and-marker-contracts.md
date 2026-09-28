# Plan: p79 done closeout manifest attribution and marker contracts

Backlog origins (scope of record):

- docs/history/backlog/2026-09-28-done-manifest-root-identity-contract.md
- docs/history/backlog/2026-09-28-done-owned-commit-ledger-interleaving.md
- docs/history/backlog/2026-09-28-run-start-marker-writer-path-selfcheck.md
- docs/history/backlog/2026-09-28-done-lock-one-shot-reclaim-releases-documentation.md
- docs/history/backlog/2026-09-28-write-manifest-legacy-foreign-bulk-load.md

Driving force: code-quality + token-usage
Plan review record: the staging series docs/reviews/2026-09-28-plan-review-p79-done-closeout-manifest-attribution-and-marker-contracts-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Make the done skill's closeout state machinery self-verifying, so a closeout can no longer complete with a corrupted audit trail or silently succeed against the wrong location.

- The run manifest's repository identity is enforced by one versioned contract on both writer and finalizer sides: the existing manifest `schema` version key and the fingerprint-valued `repo_root` field gain a named finalize-path mismatch error, so producer/consumer drift surfaces as a named abort instead of a generic missing-manifest and a manual completion-flag edit.
- Commit ownership for commits the done skill executes is captured in the same shell invocation that creates the commit, and commit ownership for learn-created commits is recorded in order from the `committed: <sha> <subject>` receipts learn prints after each successful commit (a one-line learn-side output obligation this plan adds), so the range enumeration's systemic peer exposure is gone; a peer worktree's commit does not enter this run's audit ledger through any enumeration.
- The Step 0 marker write verifies its own landing location against an independently re-derived done-session root, so a misderived path dies loudly with the stray removed instead of persisting invisibly.
- The done skill documents the one-shot lock holder lifecycle and the expected token-mismatch refusal, and prescribes a deterministic first-finalize bulk-load sequence for established repositories.

## Terms

- run manifest: the `run-manifest-<run_id>.json` record written at done Step 0 and finalized at Step 6.
- owned-commits ledger: the `owned-commits-<run_id>.txt` audit file listing the commits this done run created.
- run-start marker: the content-bearing `run-start-<UTCtimestamp>` file under the done-session directory that anchors the docs-tmp sweep window.
- claim-or-foreign gate: the write-manifest rule that every staging candidate must be owned or foreign before a manifest finalizes.
- deployed runtime copy: the `~/.ai-playbook/scripts/done_sweep_gates_lib.py` twin that consumer repos execute when no repo-local copy exists.

## Assumptions

- assume the identity contract reuses the lib's existing manifest keys rather than adding parallel ones: the `schema` version key (`MANIFEST_SCHEMA_VERSION`, already enforced in from_dict) is the contract's version, and the fingerprint-valued `repo_root` field (the writer already stores `_repo_root_digest` there) is the identity value, so the frozen sweep-gate and adopt consumers of `repo_root` keep working untouched; basis: measured on the lib (schema key, writer digest store, two-arm `_manifest_root_matches`) 2026-09-28; the new work is the named finalize-path mismatch replacing the generic not-found and the silent version degradation.
- assume legacy manifests (wrong or missing schema, unidentifiable root) are rejected at finalize with the named mismatch error rather than migrated, and the adopt path keeps its existing readable-root-matched named error (the adopt consumer already names its own failure mode); basis: completed runs never re-finalize, the origin names no migration consumer, and the adopt error already exists on disk.
- assume `--claim-none` conflicting with `--owned-review` needs no new code: the conflict abort exists and is already documented in the Step 0 recipe (verified on disk 2026-09-28); the origin's surfacing ask is covered by the first-finalize subsection restating it where operators first hit it.
- assume the interleaving proof executes the prescribed ledger snippet verbatim in a scratch git repository rather than unit-testing a lib function, because attribution is recipe-side bash; basis: the owned-commits ledger is a skill recipe over git, not a lib function.

- assume the plan's declared force is the closed-taxonomy mapping of the origins' `Driving force: reliability` headers (reliability is not in the plans closed taxonomy): correctness repair of shared closeout machinery is `code-quality`, and the operator-ergonomics arms are `token-usage`; basis: the five origin files record reliability verbatim and the plans template requires the closed taxonomy.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: five witnessed done-closeout defects become one contract pass: a named versioned repository-identity mismatch on the finalize path, fused-capture commit ownership, a self-verifying marker write, documented one-shot lock reclaim, and a deterministic first-finalize bulk load, for code-quality and token-usage.

Today the closeout's audit inputs can corrupt silently. The manifest writer and the deployed finalizer can disagree on what `repo_root` means (one records the content fingerprint, the other compares a filesystem path), and the closeout then cannot complete through its normal finalizer; the witnessed recovery was a manual completion-flag edit. The owned-commits ledger enumerates `git rev-list --reverse BASE..HEAD`, so any peer commit landing inside that range is recorded as this run's work. The Step 0 marker write exits 0 even when a misderived path puts the marker in system temp or inside the repository, where no sweep gate ever looks. The one-shot lock holder's reclaim lifecycle lives only in session memory, so a token-mismatch release refusal sends every operator re-deriving the adjudication. And the first finalize in a repository with a large review corpus drowns in unclassified candidates, resolved today only by a hand-assembled bulk-load file.

Each defect gets its arm in this plan: the finalize path gains a pre-parse identity check over the manifest's existing `schema` key and `repo_root` fingerprint with the named `run-manifest identity mismatch` abort (no silent version degradation, no generic not-found), the ledger append is fused into the same shell invocation as the commit it attributes; a post-write marker check against an independently re-parsed done-session root (with the recipe's fallback mirrored) removes the stray and dies loudly; a one-shot holder lifecycle paragraph carries the record-and-proceed response; and an `--emit-foreign-candidates` helper mode plus the canonical two-command first-finalize sequence completes the ergonomics arm.

## Evaluation Criteria

**Quality dimensions:**

- correctness: the round-trip test writes a manifest with the production writer and finalizes it through the same contract, and a wrong-version or unidentifiable-root manifest is rejected at finalize with the named mismatch, manifest unchanged.
- correctness: the interleaving simulation executes the prescribed ledger snippet against a scratch repository with a peer commit between two owned commits, and the ledger holds exactly the two owned SHAs.
- correctness: the marker check passes on a correct derivation and on the documented no-facts-key fallback, and fails loudly with the stray removed on a corrupted derivation, executed in all polarities at authoring time.
- operability: an operator reading the lock section can adjudicate a token-mismatch refusal without session memory; an operator on a first finalize can run the two-command bulk-load sequence without hand-assembling a file.

**Done when:**

- the finalize path checks the raw payload's `schema` version and `repo_root` identity before the tolerant parse, aborts with the named `run-manifest identity mismatch` error leaving the manifest unchanged, and the writer's fingerprint store is unchanged.
- the owned-commits recipe appends `git rev-parse HEAD` at each owned commit's return, the range enumeration is gone from the skill, and the interleaving simulation passes.
- the Step 0 recipe's post-write check runs on the resolved path against the freshly re-derived root, and both polarity executions pass.
- the lock section carries the one-shot lifecycle paragraph, the first-finalize subsection sits at the Step 0 write-manifest guidance with the canonical bulk-load sequence, and `--emit-foreign-candidates` emits the deterministic candidate list.

**Ship when:**

- nothing; all surfaces are repository-local skill and script files with no external dependency or release condition.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `agents/skills/done/SKILL.md` *(Steps 0, 1, 6, Step 3 item 9, and the done-lock usage section; all other sections are frozen: reject any review finding that touches them, documenting real defects elsewhere as separate findings for triage instead of in-place fixes)*
- `scripts/done_sweep_gates_lib.py` *(the run-manifest dataclass, the write-manifest and finalize-manifest paths, and the new emit-foreign-candidates mode; the sweep-gates and audit surfaces are frozen)*
- `scripts/done-lock.sh` *(no code change is planned; listed because the documentation arm describes its one-shot lifecycle, and a finding that the prose misstates the implementation is in scope)*
- `agents/skills/learn/SKILL.md` *(the Step 1.8 commit rule gains the one-line `committed:` output obligation; all other sections frozen)*

**Tests:**

- `scripts/test_done_sweep_gates_lib.py` *(existing pytest suite; this plan appends the six named tests in the file's house style; the existing tests are frozen: reject any review finding that touches them, and the venv pytest runner must stay green over the whole file)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- `scripts/done_sweep_gates.sh`; reason: the sweep-gates command surface is not one of the five witnessed defects.
- the deployed home copy `~/.ai-playbook/scripts/done_sweep_gates_lib.py` as an edit target; reason: the plan changes the repo-local canonical file; the deployed twin refreshes through the existing deployment flow, and the round-trip test covers the contract both sides must share.

## Validation Commands

```bash
#!/usr/bin/env bash
# G1 count pin helper: occurrence counting (grep -oF) with the three-way exit
# split (rc 0 matches counted, rc 1 clean zero, rc >= 2 tool error).
cnt() { rc=0; got="$(grep -oF -- "$1" "$2")" || rc=$?; if [ "$rc" -ge 2 ]; then echo "FAIL: grep error rc=$rc on $2"; exit 1; fi; n=0; if [ "$rc" -eq 0 ]; then n="$(printf '%s\n' "$got" | wc -l | tr -d ' ')"; fi; if [ "$n" != "$3" ]; then echo "FAIL: occurrences of pinned span in $2 is $n, want $3: $1"; exit 1; fi; }
REPO="$(git rev-parse --show-toplevel)" || { echo "FAIL: not a git checkout"; exit 1; }
DK="$REPO/agents/skills/done/SKILL.md"
LIB="$REPO/scripts/done_sweep_gates_lib.py"
TST="$REPO/scripts/test_done_sweep_gates_lib.py"
test -f "$DK" || { echo "FAIL: missing $DK"; exit 1; }
test -f "$LIB" || { echo "FAIL: missing $LIB"; exit 1; }
test -f "$TST" || { echo "FAIL: missing $TST"; exit 1; }
# G2: the range-enumeration ledger recipe is gone from the done skill (both Step 1 and Step 3 item 9 rewrote to exact-SHA recording).
cnt 'rev-list --reverse' "$DK" 0
# G3: the exact-SHA append is pinned in the ledger recipe (both the Step 1 recipe and the Step 3 item 9 rule carry the prescribed line).
cnt 'git rev-parse HEAD >> "$LEDGER"' "$DK" 2
# G3b: the retired range machinery is gone from the done skill (each span lives at one site today; want 0 after Task 2).
cnt 'LAST="$(tail -n 1 "$LEDGER")"' "$DK" 0
cnt 'must skip the ledger append' "$DK" 0
cnt 'between the manifest' "$DK" 0
cnt 'Enumerate with the last appended sha as the base' "$DK" 0
cnt 'START_COMMIT' "$DK" 0
cnt 'keep it one sha per line and never edit a recorded line' "$DK" 1
# G3e: the learn receipt contract and the recovery disposition are pinned (both RED-today, introduced by Task 2).
cnt 'committed: <sha> <subject>' "$DK" 1
cnt 'an append is not an edit of a recorded line' "$DK" 1
# G3c: the Task 1 Step 6 operator-facing sentences are pinned (distinctive spans of the prescribed text).
grep -qF 'stale-finalizer signature' "$DK" || { echo "FAIL: the stale-finalizer signature sentence is missing"; exit 1; }
grep -qF 're-running the Step 0 writer' "$DK" || { echo "FAIL: the corrupt-record response sentence is missing"; exit 1; }
# G3d: the frozen test population survives (rule 39 provenance: 75 existing tests measured under the venv pytest runner 2026-09-28 on the pre-edit tree, plus the six named tests).
test "$(grep -c '^def test_' "$TST")" -ge 81 || { echo "FAIL: frozen suite shrank below 81 test functions"; exit 1; }
# G4: the marker post-write check is present exactly once and runs on the resolved path.
cnt 'not the expected done-session root' "$DK" 1
cnt 'MARKER_DIR="$(cd "$(dirname "$MARKER")"' "$DK" 1
# G5: the one-shot lifecycle paragraph and its record-and-proceed response are present.
cnt 'One-shot holders and peer reclaim' "$DK" 1
cnt 'record the witness and proceed' "$DK" 1
# G6: the first-finalize subsection and the canonical bulk-load sequence are present
# (presence pins: the flag name legitimately appears in both the subsection prose and the command sequence).
cnt 'first finalize in an established repository' "$DK" 1
grep -qF -- '--emit-foreign-candidates' "$DK" || { echo "FAIL: the emit-foreign-candidates sequence is missing from the done skill"; exit 1; }
# G7: the identity contract surfaces in the lib (presence pins: the identity key and the version wording the contract reuses, plus the prescribed error literal exactly once; prose mentions of the error literal elsewhere in the lib are forbidden so that pin stays stable).
grep -qF 'repo_root' "$LIB" || { echo "FAIL: lib lost the repo_root identity key"; exit 1; }
grep -qF 'schema_version' "$LIB" || { echo "FAIL: lib lost the schema_version wording"; exit 1; }
# The error literal is prescribed verbatim; prose (docstring/comment) mentions of it elsewhere in the lib are forbidden so this exactly-once pin stays stable.
cnt 'run-manifest identity mismatch' "$LIB" 1
# G8: the round-trip, mismatch, marker, interleaving, and determinism tests exist and are named in the test file.
for t in test_round_trip_writer_to_finalizer test_legacy_manifest_rejected_with_named_mismatch test_marker_check_passes_on_correct_derivation test_marker_check_fails_loud_on_corrupted_derivation test_ledger_interleaving_simulation test_emit_foreign_candidates_deterministic; do grep -q "def $t" "$TST" || { echo "FAIL: missing test $t"; exit 1; }; done
# G9: the whole suite (existing tests frozen + the six new tests) is green under the venv pytest runner.
RUNNER="${AI_PLAYBOOK_TEST_PYTHON:-$HOME/.agents/venvs/ai-playbook-test/bin/python3}"
test -x "$RUNNER" || { echo "FAIL: venv pytest runner missing at $RUNNER"; exit 1; }
( cd "$REPO" && "$RUNNER" -m pytest scripts/test_done_sweep_gates_lib.py -q >/dev/null 2>&1 ) || { echo "FAIL: test_done_sweep_gates_lib.py suite not green under the venv pytest runner"; exit 1; }
# G10: no em-dash anywhere in the touched files (the .py arms set the scanner's
# documented all-paths knob: without it the prose filter skips non-.md files and
# the arms are vacuous).
( cd "$REPO" && bash scripts/check-no-em-dash.sh file agents/skills/done/SKILL.md ) || { echo "FAIL: em-dash in done SKILL.md"; exit 1; }
( cd "$REPO" && CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file scripts/done_sweep_gates_lib.py ) || { echo "FAIL: em-dash in done_sweep_gates_lib.py"; exit 1; }
( cd "$REPO" && CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file scripts/test_done_sweep_gates_lib.py ) || { echo "FAIL: em-dash in test file"; exit 1; }
( cd "$REPO" && bash scripts/check-no-em-dash.sh file docs/history/plans/2026-09-28-p79-done-closeout-manifest-attribution-and-marker-contracts.md ) || { echo "FAIL: em-dash in plan file"; exit 1; }
echo "ALL VALIDATION GATES GREEN"
```

Authoring-time gate record and snippet polarity record (plans Validation rules 19, 22, 24, 27, 29): the block passes `bash -n` and was executed against the pre-edit tree; G2 was RED (occurrences 2 against want 0: both the Step 1 recipe and the Step 3 item 9 rule still carry the range enumeration), G3 through G8 were RED (counts 0 against their wants; G8 names the six test functions absent from the existing suite), G9 was GREEN-today and is a regression gate (the existing 75-test suite passes under the venv pytest runner on the pre-edit tree), and G10 was GREEN on the touched files (verified individually). Both prescribed snippets were executed at authoring time: the marker post-write check ran in its polarities in a scratch tree (correct derivation with a facts tmp_dir key: exit 0 with the marker present under the done-session root; corrupted absolute derivation into a system-temp anchor: exit 1 with both paths named and zero strays left; corrupted relative derivation anchored inside the repository: exit 1 with zero strays left in the repo-internal tree; the no-facts-key fallback polarity is added by the r1 fold and runs green under the mirrored fallback before certification), and the prescribed ledger line ran in a scratch git repository with a peer commit interleaved between two owned commits (the ledger held exactly the two owned SHAs, the peer sha absent). The pre-round readiness invocation and the hygiene scan were run over the final plan bytes with no structural failure (authoring record 2026-09-28, r1 fold); the r2 fold's joint-direction verification additionally executed a faithful post-edit simulation in a scratch clone (all prescribed edits applied: the two-arm finalize pre-parse with the named mismatch error, fused ledger lines at both sites, the full retirement set, the marker block, the lock paragraph, the Step 6 operator sentences, the first-finalize subsection, and the six named tests appended to the existing suite) and the block exits ALL VALIDATION GATES GREEN on that tree with the frozen 75-test population green under the venv pytest runner; the simulation's first fingerprint-only pre-parse draft broke the frozen suite's path-rooted fixture, which is why the plan's both-arms wording (fingerprint arm and resolvable-path arm) is load-bearing and must not be narrowed at implementation time ; the r3 fold extended the retirement inventory (the Step 1 base-derivation sentence, the uppercase START_COMMIT machinery at all seven sites, and the operator-response recovery disposition), pinned the never-edit-a-recorded-line audit tail as a GREEN-today regression guard, pinned the mismatch abort's non-zero exit, scoped the learn arm to post-hoc-from-receipt, and re-anchored the lock paragraph to the Step 0 lock paragraphs as an operator-response arm (authoring record 2026-09-28, r3 fold: new RED-today pins Enumerate-span 1, START_COMMIT 7, want 0; tail span 1, want 1); the r4 fold forced the em-dash scanner's all-paths knob on the two .py arms (the prose filter made them vacuous), defined the learn receipt producer-side (`committed: <sha> <subject>` printed per learn commit), sanitized the mismatch error's raw-value rendering, moved the first-finalize subsection to the Step 0 write-manifest guidance, added the foreign-root arm to the legacy-rejection test, and added the G3e receipt/recovery pins (authoring record 2026-09-28, r4 fold)

### Task 1: Versioned typed repository identity for the run manifest

Files:

- `scripts/done_sweep_gates_lib.py`
- `agents/skills/done/SKILL.md`

- [x] Reuse the manifest's existing keys as the identity contract (no parallel fields): `schema` (already `MANIFEST_SCHEMA_VERSION = 1`) is the contract version and `repo_root` (already written as the `_repo_root_digest` fingerprint) is the identity value; the frozen sweep-gate and adopt consumers of `repo_root` keep working untouched because the field and its two-arm matcher stay [class: IMPLEMENTATION_REQUIRED]
- [x] Make the finalize path check the raw payload BEFORE the tolerant from_dict parse: a payload whose `schema` is missing or not 1, or whose `repo_root` is missing or matches neither the fingerprint arm nor the resolvable-path arm, aborts with the exact error `run-manifest identity mismatch: manifest schema_version <v> repo_root <state> is not supported by this finalizer (expected schema_version 1 and a 64-hex fingerprint root matching this repository); manifest left unchanged` where `<v>` renders the raw value or the word absent and `<state>` renders one of exactly three values (`fingerprint` for a 64-hex root that is not this repository's, `path` for any non-hex root value, `absent` when the key is missing), nothing is written, the abort exits non-zero so the Step 6 recipe's abort-on-non-zero guard fires, `<v>` renders sanitized (the word absent when the key is missing, else the raw value with newlines and control characters stripped, truncated at 64 characters, so a corrupt manifest cannot forge log lines into the finalize stderr), and the finalize-manifest docstring plus the `_usage()` finalize line are reworded to the two-way contract (absent file: the existing zero-exit note; present but foreign or wrong-version: the non-zero named abort) without using the reserved error literal; the tolerant from_dict and its silent None degradation stay for the frozen non-finalize consumers (interrupted-run detection, adopt), which never see the finalize path's named abort [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the Step 6 skill text with the stale-deployment signature, scoped two-stage: a `no run manifest found` note at finalize for a run_id this session exported, when the manifest file exists under the done-session directory, is a stale-finalizer signature on the first occurrence (redeploy the runtime twin once and retry); a second not-found with the file still present is a corrupt record whose only supported response is re-running the Step 0 writer, never a manual edit [class: IMPLEMENTATION_REQUIRED]
- [x] Remove the manual completion-flag repair from the supported closeout path in the done skill: the Step 6 text gains one sentence stating that an identity mismatch is a named abort whose only supported response is re-running the Step 0 writer, and any historical manual-repair mention is deleted from the skill [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `done: versioned typed repository identity for the run manifest` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Exact-SHA owned-commit attribution

Files:

- `agents/skills/done/SKILL.md`
- `agents/skills/learn/SKILL.md` *(plan-related extension: the ledger contract needs the producer receipt; the learn commit rule gains the one-line `committed:` output obligation and nothing else in that file is touched)*

- [x] Replace the Step 1 ledger recipe's range enumeration with fused exact-SHA capture: each owned commit and its ledger append run in ONE shell invocation, the commit command chained to the prescribed line so the ownership witness is the same command whose success creates the commit; the multi-commit learn rule records every sha learn reports it created, in order, from the `committed: <sha> <subject>` receipts learn prints after each successful commit (a one-line learn-side output obligation this plan adds via the plan-related extension clause, since learn executes its own commits and that arm is post-hoc-from-receipt, one append per reported sha; the fused form is reserved for commits the done skill executes); the Step 3 item 9 rule is reworded to the same fused form, and the empty-BASE skip note is replaced by a note that the ledger is created on first append with no base needed; the rule text also carries the recovery disposition: on the doc-registry report naming a foreign-commit exclusion for a sha this run created, appending that sha to the ledger (an append is not an edit of a recorded line) and re-running the gate is the remedy, never restoring the range enumeration [class: IMPLEMENTATION_REQUIRED]
- [x] Add the learn-side producer obligation: learn's commit rule (Step 1.8) gains one sentence requiring, after each successful commit, printing `committed: <sha> <subject>` so the done Step 1 rule can consume the receipts; no other learn text changes [class: IMPLEMENTATION_REQUIRED]
- [x] Retire the range machinery the fusion orphans, at every surviving site: the `START_COMMIT` skip guard and the `LAST`/`BASE` derivation lines leave the Step 1 recipe (keeping the `RUN_ID` filename guard); the Step 0 echo block drops the `START_COMMIT` extraction and echo lines, drops the keep-or-skip sentence (an empty value must skip the ledger append), and its comment is reworded to the fused-capture contract; the Step 1 paragraph's base-derivation sentence (Enumerate with the last appended sha as the base, falling back to the Step 0 manifest's start_commit) and its tail sentence defining the ledger as the record of commits between the manifest's start commit and HEAD are reworded to the fused-capture semantics (the ledger records exactly the commits this run created; the never-edit-a-recorded-line audit tail survives the rewording verbatim); adoption still reads `start_commit` from the manifest record, so the manifest field stays [class: IMPLEMENTATION_REQUIRED]
- [x] The prescribed append line lands at exactly the two named sites (the Step 1 recipe and the Step 3 item 9 rule); the multi-commit learn rule lives at the Step 1 site and appends the receipts' shas literally (one append per reported sha, in receipt order), never via the prescribed line; no third copy of the line exists [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `done: exact-sha owned-commit attribution replaces range enumeration` [class: IMPLEMENTATION_REQUIRED]

Prescribed ledger append line (verbatim, replaces the `git rev-list --reverse` enumeration in both the Step 1 recipe and the Step 3 item 9 rule):

```
git rev-parse HEAD >> "$LEDGER"
```

### Task 3: Marker post-write location self-check

Files:

- `agents/skills/done/SKILL.md`

- [x] Append the prescribed check block to the Step 0 marker recipe immediately after the marker write line: it re-parses `tmp_dir` from the facts document into a fresh variable (an independent second parse, so a corrupted derivation line in the recipe is caught), re-anchors and resolves the expected done-session root, resolves the written marker's directory, and on mismatch removes the stray marker, dies with both paths named, and leaves no marker behind [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `done: marker post-write location self-check` [class: IMPLEMENTATION_REQUIRED]

Prescribed marker check block (verbatim):

```
# Post-write location self-check: independent fresh parse, resolved-path compare.
TMP_DIR_FRESH="$(sed -n 's/^tmp_dir = ["'\'']\(.*\)["'\'']$/\1/p' "$REPO_TOP/.ai-playbook/facts.md" 2>/dev/null | head -n 1)"
TMP_DIR_FRESH="${TMP_DIR_FRESH:-$REPO_TOP/docs/tmp/}"
case "$TMP_DIR_FRESH" in /*) ;; *) TMP_DIR_FRESH="$REPO_TOP/$TMP_DIR_FRESH";; esac
EXPECTED_ROOT="${TMP_DIR_FRESH%/}/done-session"
EXPECTED_ROOT="$(cd "$EXPECTED_ROOT" 2>/dev/null && pwd)" || EXPECTED_ROOT=""
MARKER_DIR="$(cd "$(dirname "$MARKER")" 2>/dev/null && pwd)" || MARKER_DIR=""
if [ -z "$EXPECTED_ROOT" ] || [ "$MARKER_DIR" != "$EXPECTED_ROOT" ]; then
  rm -f "$MARKER"
  echo "run-start marker: resolved path ${MARKER_DIR:-unresolvable} is not the expected done-session root ${EXPECTED_ROOT:-unresolvable}; stray marker removed" >&2
  exit 1
fi
```

### Task 4: One-shot lock holder lifecycle documentation

Files:

- `agents/skills/done/SKILL.md`

- [x] Add a short paragraph titled by the exact lead phrase `One-shot holders and peer reclaim` to the done skill's Step 0 lock paragraphs (after the Stealable locks item), scoped as the operator-response arm that links to the `scripts/done-lock.sh` usage text as the semantics owner (the skill's existing delegation sentence stays; this paragraph does not restate the fence mechanics, it names the lifecycle and the operator adjudication): a one-shot shell holder goes dead when its acquiring call finishes, a live peer may reclaim the abandoned hold after the dead-holder grace period, and a token-fenced release from the original run is then refused with a token mismatch; the refusal is the expected witness of a peer reclaim, the correct response is to record the witness and proceed (never bypass the fence or re-acquire), and nothing is left to release [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `done: document one-shot holder reclaim and token-mismatch response` [class: IMPLEMENTATION_REQUIRED]

### Task 5: First-finalize bulk-load ergonomics

Files:

- `agents/skills/done/SKILL.md`
- `scripts/done_sweep_gates_lib.py`

- [x] Add an `--emit-foreign-candidates <file>` mode to write-manifest: it runs the same staging-candidate enumeration as the claim-or-foreign gate, subtracts the invocation's `--owned-review` claims (and the adopted manifest's inherited owned claims when `--adopt` is passed), writes the remaining candidate paths one per line in sorted order to the file, aborts with a named error listing any candidate whose path contains a newline or leading or trailing whitespace (the loader cannot round-trip such lines), and exits 0 without writing a manifest; add a subsection at the Step 0 write-manifest guidance (where the claim-or-foreign abort fires) with the exact lead phrase `first finalize in an established repository` prescribing the canonical two-command sequence: run write-manifest with `--emit-foreign-candidates` first, review the emitted list, then re-run the real write with `--foreign-review-from <file>`, noting there that `--claim-none` conflicts with `--owned-review` [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `done: deterministic first-finalize foreign bulk load` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Mechanical selftest

Files:

- `scripts/test_done_sweep_gates_lib.py`

- [x] Extend the existing pytest suite (it already carries the lib's coverage; existing tests are frozen and must stay green under the venv pytest runner) with at least the six named tests in the file's house style: `test_round_trip_writer_to_finalizer` (production writer emits the fingerprint root, the finalize path resolves it and finalizes), `test_legacy_manifest_rejected_with_named_mismatch` (a wrong-version payload aborts at finalize with the exact `run-manifest identity mismatch` error, non-zero exit, and the file is unchanged; the same test also drives a schema-valid payload carrying a foreign 64-hex root through the same assertions, so the root arm cannot regress to silent acceptance), `test_marker_check_passes_on_correct_derivation` and `test_marker_check_fails_loud_on_corrupted_derivation` (the prescribed Step 0 block executed verbatim in a scratch tree, both polarities; the corrupted arm must remove the stray and exit non-zero; the correct arm includes the no-facts-key fallback polarity), `test_ledger_interleaving_simulation` (the prescribed fused ledger line executed in a scratch git repository with a peer commit interleaved between two owned commits; the ledger holds exactly the two owned SHAs in order), and `test_emit_foreign_candidates_deterministic` (two invocations over the same tree emit byte-identical sorted files, and an owned artifact never appears) [class: REPOSITORY_TEST]
- [x] Run the Validation Commands block; expect ALL VALIDATION GATES GREEN [class: REPOSITORY_TEST]
- [x] Run `( cd "$(git rev-parse --show-toplevel)" && python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-09-28-p79-done-closeout-manifest-attribution-and-marker-contracts.md )`; expect exit 0 [class: REPOSITORY_TEST]
- [x] Run the public hygiene scan from the repository root; expect exit 0 [class: REPOSITORY_TEST]
- [x] Commit: `done: closeout contract selftest` [class: IMPLEMENTATION_REQUIRED]
