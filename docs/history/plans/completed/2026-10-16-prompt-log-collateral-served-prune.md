# Plan: collateral served-entry prune discovery for the authoring landing closeout

Backlog origin: docs/history/backlog/2026-10-10-plan-prompts-collateral-served-prune-sweep.md
Driving force: automation
Plan review record: the staging series .ai-playbook/reviews/2026-10-16-plan-review-prompt-log-collateral-served-prune-p5947faf4-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2h total, largest task 1h
Authoring claim: docs/tmp/authoring-claims/2026-10-16-prompt-log-collateral-served-prune.md (session sess_automation-4f96f211-remainder)

## Terms

- collateral served entry: a rolling-log entry, other than the landing's own dispatch entry, every origin of which is served at HEAD or was served at base and absent at HEAD because the landing's range deleted the covered row (the repository's delete-not-stub disposition for covered rows).
- range-produced origins: the origins whose served state the discovery range produced: served at HEAD and not served at base (a status flipped or an archive move), or served at base and absent at HEAD (a covered row deleted in range; an origin live or deferred at base and deleted in range counts nothing, because the deletion moved no coverage); the only origins a listed entry's line names.
- origin coverage verdict: the per-origin classification `scripts/check_prompt_log_origins.py` `classify_origin` already produces (`served`, `deferred`, or `live`) for an entry's `Origins:` row; a tree-absent origin classifies `live`, which is why the deletion arm is an explicit extension named in this plan's Terms and fence, never an implicit all-served read.
- prune evaluation: the authoring landing's closeout step that removes dispatch entries from the tracked log and prints one `PLAN-PROMPTS-PRUNE: <slug> -> <witness path>` receipt line per removal.
- prune audit: `python3 scripts/check_prompt_log_origins.py --prune-audit --base <merge-base>`, the existing fail-closed removal audit.
- discovery range: the landing branch's merge-base..HEAD commit range, so only commits the landing itself carries can produce a listed served state.
- pins suite: `scripts/check_maintenance_pins.sh`, whose origins checker run is today's only detector of a served-but-unpruned entry.

## Why

A landing can serve rolling-log entries other than its own dispatch entry (every origin served at HEAD, or a covered row deleted in range), but nothing discovers them at the landing: the served entry sits in the log until the pins suite's STALE verdict blocks a later landing, and the fix is a manual out-of-band prune. The discovery belongs inside the same closeout that already prunes with receipts.

## Gist & Examples

TLDR: the landing closeout gains a read-only collateral discovery leg that lists non-own entries every origin of which is served at HEAD or deleted-in-range, where the served state is the landing's own range's production, so they are pruned with receipts in the same closeout instead of surfacing later as a pins-suite blocker; driving force: automation.

Before: landing bbdc8f999 fully served the entry `execute-plan-restored-manifest-terminal-evidence`; the own-entry-only prune left it queued, the pins suite went STALE-red, and the next landing stayed blocked until commit 0c09305f6 removed the entry out of band with its own receipt.

After: the same closeout runs the discovery mode, sees the collateral entry listed (every origin served or deleted-in-range, at least one served state produced inside the landing range), prunes it with `PLAN-PROMPTS-PRUNE: <slug> -> <in-tree plan-file witness of the covering landing>` (the covering landing's squash commit does not exist at rider time, so the witness is the landing's plan file under the plans root, which resolves in the rider commit's tree; the incident's digest form worked only because that prune landed after the landing), and the prune audit passes on the net diff; no later landing is blocked and no out-of-band commit is needed.

Edge cases: an entry a peer's landing already served before this branch's base is not listed (no served state inside the range; the monitor's log duties stay its owner); a mixed entry with one origin still live is never listed; the landing's own dispatch entry is never listed (the existing own-entry leg owns it, no double removal); a listed entry the author chooses not to prune blocks nothing (the leg is read-only; the pins suite remains the unchanged backstop).

## Outcome

The authoring landing closeout discovers its collateral served entries mechanically and prunes them with receipts in the same riders, so a fully served entry never again reaches the pins suite as a stale blocker.

- The checker gains a read-only discovery mode that lists collateral served entries with the per-origin evidence of what the landing range produced.
- Pruning a listed entry follows the existing receipt discipline and passes the existing prune audit unchanged.
- No new blocker: the discovery is a listing, the pins suite's stale-entry refusal remains the only enforcement, and the manual out-of-band recovery shape (the 0c09305f6 pattern) becomes unnecessary.

Gate delta: removes one prose exclusion, adds nothing counted. The log prune rule's blanket any-other-removal exclusion narrows for exactly the listed collateral shape (a listed all-served-or-deleted-in-range entry pruned with its own receipt); the change adds a read-only discovery subcommand and two procedure sentences beside the existing prune audit, and no refusal class, hard gate, fence, protocol layer, or schema field; the existing pins-suite stale-entry blocker is unchanged. Residual surface, recorded: the generic plans landing leg and the maintenance monitor's decisions text restate the own-entry-only behavior and keep it for their lanes; the collateral arm rides the authoring blueprint and the log rule only. The paying simplification is the retired manual recovery shape (an out-of-band standalone prune commit after a red pins suite), witnessed by the origin row's recorded incident; the discovery leg itself is a listing with no enforcement, so it is priced as the automation the origin orders rather than a new blocker (incident, catch frequency one, false-positive cost an incorrectly listed entry, review date 2027-01-16, replacing nothing that blocks).

## Assumptions

- assume the discovery range is the landing branch's merge-base..HEAD, so a peer landing's already-landed coverage never lists; basis: the landing rebase convention (branch equals main plus its own commits) and the prune audit's existing `--base` semantics.
- assume the listing fence is the composite the Terms and Standing constraints own: every origin served at HEAD, plus the single deleted-in-range arm for rows served at base; the checker's bare all-served STALE predicate is its base case, not the whole fence (a tree-absent origin classifies `live`); basis: the completed prune-eligibility fence plan (`docs/history/plans/completed/2026-10-05-plan-prompts-prune-eligibility-fence.md`), the checker's STALE predicate, and the Standing constraints sentence.
- assume a covered origin row deleted by the landing's range still witnesses coverage: the deletion is the repository's covered-row disposition (the repo commit guidelines' delete-not-stub rule; the ad-hoc-superseded prune receipts recorded by commit 04e505e4e name fb120691c as the covering landing and witness origin rows deleted in that same landing), so an origin served at base and absent at HEAD counts as a served state the range produced; basis: the repo commit guidelines and the 04e505e4e prune receipts naming fb120691c. The 44b0d049f landing witnesses the status-flip shape, not a deletion; a tree-absent origin classifies `live` under the current classifier, so this arm is the explicit extension Task 2 implements.

Decision points requiring a grill: none remain.

## Standing constraints

- The anti-over-prune fence holds: only an entry whose every origin is served at HEAD, or whose every origin is served at HEAD or served-at-base-deleted-in-range per the Terms' collateral definition, may be pruned by a landing; the deleted-in-range arm is the fence's one sanctioned extension, and every removal carries exactly one receipt line.
- The discovery leg stays read-only at the checker level: it lists, it never prunes; pruning remains the author's receipted rider edit.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the selftest and the pytest suite prove every Task 1 listed and skipped shape with the real classifier functions.
- simplicity: the mode reuses `classify_origin` and the existing blob-at-commit machinery; no second classification grammar.
- maintainability: the procedure text lives once in the authoring blueprint and once in the log's prune rule, pointing at the checker mode instead of restating mechanics.

**Done when:**
- `python3 scripts/check_prompt_log_origins.py --selftest` exits 0 with the discovery shapes among its inline fixtures.
- The repository's canonical venv pytest run of `scripts/test_check_prompt_log_origins.py` exits 0.
- The new mode run on the fixture logs lists exactly the collateral entries, one per listed-shape fixture, and none of the fenced shapes.

**Ship when:**
- none (repository-internal tooling and skill text).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/check_prompt_log_origins.py`

**Tests:**
- `scripts/test_check_prompt_log_origins.py` (new fixtures added to the existing file)

**Documentation:**
- `docs/history/backlog/PLAN-PROMPTS.md` (the log header's prune rule gains the collateral class sentence)
- `agents/skills/maintenance/template-authoring.md` (the authoring blueprint's prune-evaluation sentence gains the discovery leg)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/history/backlog/EXEC-PROMPTS.md` and the ad-hoc-superseded removal class; reason: that class already covers the execution lane's post-landing prune shape and the origin incident is authoring-lane.
- `scripts/check_maintenance_pins.sh`; reason: the pins suite is the unchanged backstop, not a change target.

## Validation Commands

```bash
python3 scripts/check_prompt_log_origins.py --selftest
python3 -m pytest scripts/test_check_prompt_log_origins.py -q  # under the repository's canonical test venv
python3 scripts/check_prompt_log_origins.py --collateral-served --base main
python3 scripts/check_prompt_log_origins.py --prune-audit --base main
```

### Task 1: RED fixtures for the collateral discovery mode

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/test_check_prompt_log_origins.py`

Primary class anchors:
- `classify_origin` in `scripts/check_prompt_log_origins.py`, which owns the per-origin coverage verdict the fixtures drive.

Fixture construction: reuse the test module's existing scratch-repository builder (its identity-pinned `git -c user.name=... -c user.email=...` commit helper and fixed default branch) so base-side states are committed blobs at the base commit and HEAD-side states at the HEAD commit; working-tree-only files cannot express served-at-base.

- [ ] `classify_origin`-driven fixtures witness the listed shape in all three range-produced arms as named fixtures: a status flipped to covered in range, an archive move in range, and a covered row deleted in range; each entry carries at least one further origin served identically at base and HEAD, and each listing line names the range-produced origins only and never the served-at-both origin. [class: REPOSITORY_TEST]
- [ ] Fixtures witness the coverage-fenced shapes: given a mixed entry (one origin live) and an entry all-served already at base (foreign coverage), expects neither listed. [class: REPOSITORY_TEST]
- [ ] Fixtures witness the absence- and deletion-fenced shapes: given an origin absent at both base and HEAD (its entry never listed regardless of other origins) and an origin live or deferred at base that the range deletes (the deletion moved no coverage: never listed), expects neither listed. [class: REPOSITORY_TEST]
- [ ] Fixtures witness the unserved-HEAD-fenced shapes: given an origin served at base whose row is still present at HEAD with an unserved status or a deferred resolution (a covered row re-opened or re-deferred rather than deleted: never listed, never counted) and an origin live or deferred at base that is deferred at HEAD (the deferred verdict is never HEAD-side coverage: never listed), expects neither listed. [class: REPOSITORY_TEST]
- [ ] Fixtures witness the verdict-difference arm: given an origin deferred at base that turns served at HEAD, expects the entry listed with that origin named. [class: REPOSITORY_TEST]
- [ ] Fixtures witness the procedural own-entry fence: given the post-own-prune log state (the landing's own entry already removed from the log before discovery runs), expects no line naming the own entry's slug, pinning that the mode lists only entries present in the log it reads. [class: REPOSITORY_TEST]
- [ ] Fixtures witness the read-only contract: given any listing run, expects the log bytes and the origin rows unchanged on disk after the run. [class: REPOSITORY_TEST]
- [ ] Run -> expect RED: the repository's canonical venv pytest run of `scripts/test_check_prompt_log_origins.py` fails on the missing discovery mode (the prune-audit fixture class's docstring names the venv runner the canonical invocation). [class: REPOSITORY_TEST]
- [ ] Run -> expect GREEN (after Task 2): the same suite passes. [class: REPOSITORY_TEST]
- [ ] Commit: `check: collateral served-entry discovery fixtures` [class: IMPLEMENTATION_REQUIRED]

### Task 2: the read-only discovery mode

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/check_prompt_log_origins.py`

Primary class anchors:
- `collateral_served_cli` in `scripts/check_prompt_log_origins.py`, the new read-only discovery entry point reusing `classify_origin`, `parse_entries`, and the existing blob-at-commit reader

Design note (context, not a criterion): the mode is separate from the default listing because the default mode's output is the pins suite's consumed gate surface, which this plan does not change; the per-origin evidence list is the author's adjudication input for the prune decision.

- [ ] `collateral_served_cli` lists collateral served entries: given `--collateral-served --base <ref>` and the working-tree log, expects one `COLLATERAL-SERVED: <slug> -> <origin basename> [...]` line per listed entry naming only the range-produced origins, exit 0 whether the list is empty or not. [class: IMPLEMENTATION_REQUIRED]
- [ ] An origin counts as range-produced only when its served state differs between base and HEAD: given an origin served by status or archive at HEAD and not served at base, or an origin served at base (a covered row) and absent at HEAD, expects exactly those origins counted. [class: IMPLEMENTATION_REQUIRED]
- [ ] Exclusions hold beside the counted arms: given an origin served at both, expects it excluded from the evidence list while the entry still lists when another origin is range-produced; given an origin absent at both, expects the entry never listed regardless of its other origins, because the Terms' composite predicate fails for it. [class: IMPLEMENTATION_REQUIRED]
- [ ] The deletion arm keys on tree-absence, not on the classifier's `live` verdict: given an origin served at base whose row is still present at HEAD with an unserved status or a deferred resolution, expects it never counted (a present unserved row also returns the `live` verdict). [class: IMPLEMENTATION_REQUIRED]

Design note (context, not a criterion): the base-side verdict reuses `classify_origin` unchanged: materialize the base commit's backlog directory into a temporary directory (`git archive <base> -- docs/history/backlog` extracted outside the repository) and classify against that copy, so no second classification grammar exists and the worktree stays untouched.
- [ ] The mode never writes: given any invocation, expects no log mutation and no index or worktree change outside stdout; the base-side materialization lands in a temporary directory outside the repository. [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness: given a `--base` that does not resolve, expects the tool-error exit (3) with the reason printed through the script's existing tool-error convention on stdout and a final `OUTCOME: tool_error` line, matching the sibling `--prune-audit` mode, never a silent empty listing. [class: IMPLEMENTATION_REQUIRED]
- [ ] The checker's built-in `--selftest` gains the discovery shapes: given the selftest's inline fixture style, expects it to exercise the listed shapes (status flip, archive move, deletion, deferred-at-base-turned-served) and each fenced shape (including the re-opened covered row, the no-coverage deletion, and the deferred-at-HEAD cell) so the mode's regression gate runs without pytest. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run -> expect GREEN: `python3 scripts/check_prompt_log_origins.py --selftest` and the pytest suite both pass. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `check: collateral served-entry discovery mode` [class: IMPLEMENTATION_REQUIRED]

### Task 3: procedure text for the landing closeout

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `docs/history/backlog/PLAN-PROMPTS.md`
- `agents/skills/maintenance/template-authoring.md`

- [ ] The log's prune rule names the collateral class: given the amended rule sentence, expects it to admit exactly one landing-side collateral removal shape (a listed entry pruned with its own receipt whose witness is the covering landing's in-tree plan-file path) while the blanket any-other-removal exclusion still stands for unserved or unlisted entries. [class: IMPLEMENTATION_REQUIRED]
- [ ] The authoring blueprint's prune-evaluation sentence names the discovery leg: given the amended sentence, expects the closeout to run the discovery mode after the own-entry prune, prune each listed entry with one receipt line whose witness is the covering landing's in-tree plan-file path (never the future landing commit digest, which cannot resolve at rider time), and re-run the prune audit so the net diff carries every witness. [class: IMPLEMENTATION_REQUIRED]
- [ ] The amended sentences preserve the log's pinned literal verbatim: given `scripts/check_maintenance_pins.sh` (out of scope for this plan), expects the literal `A landing prunes only its own dispatch entry` to survive byte-identical in the log, the only file carrying it. [class: IMPLEMENTATION_REQUIRED]
- [ ] The amended blueprint preserves its pinned literals verbatim: expects the literals `PLAN-PROMPTS-PRUNE: <slug> -> <witness path>` and `python3 scripts/check_prompt_log_origins.py --prune-audit --base <merge-base>` to survive byte-identical in both amended files, with the collateral leg added beside them rather than by rewording them. [class: IMPLEMENTATION_REQUIRED]
- [ ] The vendored-sync disposition is recorded: given the two edited skill/log text files, expects the run to either mirror them to the deployed runtime copies in the same run or to name the changed files in a tracked vendored-sync landing row, recorded beside the landing. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run -> expect GREEN: the amended sentences are present, the prune audit passes at the task's own commit, and the pins suite is green. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `docs: collateral prune discovery in the landing closeout procedure` [class: IMPLEMENTATION_REQUIRED]

### Task 4: live probe and full validation

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/check_prompt_log_origins.py`

Primary class anchors:
- `collateral_served_cli` in `scripts/check_prompt_log_origins.py`, exercised against the repository real log

- [ ] Live probe: given the repository's real rolling log at the run branch with a clean worktree for the origin rows, expects the discovery mode to run exit 0, to print no line naming the target entry's slug (whose origin is open), and to leave the log byte-identical; other entries the real log may legitimately list are adjudicated at run time, never asserted empty. [class: REPOSITORY_TEST]
- [ ] Full battery: given the four Validation Commands, expects all exit 0 in sequence. [class: REPOSITORY_TEST]
- [ ] Run -> expect GREEN: the battery passes. [class: REPOSITORY_TEST]
- [ ] Commit: `check: collateral discovery live probe green` [class: IMPLEMENTATION_REQUIRED]
