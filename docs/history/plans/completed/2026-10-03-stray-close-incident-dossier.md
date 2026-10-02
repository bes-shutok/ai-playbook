# Plan: stray-close incident closure: validate the ad-hoc response, move directive lifecycle repo-side, make completion claims correctable

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-03-stray-close-incident-dossier.md`

Driving force: consistency (outside the closed taxonomy: the incident let seven unexecuted archives read as completed work across three record homes, and this plan restores one consistent completion story; park-triage would not take it: the record corpus is the operator's decision surface, its false rows already misdirected a full day of lanes, and the next stale directive would recreate the wave, so the inconsistency closes now while the witnesses are fresh)

Plan review record: the staging series docs/reviews/2026-10-03-plan-review-stray-close-incident-dossier-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

The 2026-10-03 stray-close incident's ad-hoc response is validated through review, and the directive-lifecycle and completion-record gaps that let the wave happen close with repo-side rules an automation payload can no longer outlive.

- The seven-plan restoration is audited complete against git (plan bytes, origin cross-references, registry rows, review-record references), with defects repaired on sight and a clean verdict recorded when there are none.
- An operator directives home, a tracked reviewed file, records operator lane directives with issue dates, statuses, and supersessions; maintenance turns read it before acting on any directive-bearing clause, carrier payloads lift directive text from it at dispatch instead of baking aging clauses, and a session never deletes or silently replaces its own carrier automation without a state-file retirement record.
- The origin-flip invariant and reopen rules land beside the survey's landed-plan disposition fence: a covered flip is truthful only while the covering plan sits at the plans root, unexecuted-archive discovery restores by reverse rename with origins staying covered, and a rejected-archive egress un-covers the archived plan's origin rows in the same commit.
- The false-completion correction protocol names the three remedies (tree, registry, memory) in order, generalizing the hand-built corrections this incident needed.

Gate delta: +1 protocol layer (the operator directives home with its turn-start read-and-obey duty and supersession records; witness: the completed failure recorded in the dossier's Problem section, the 2026-10-02 DO-NOT-EXECUTE clause outliving two in-chat lifts across 87 armed carrier runs while propagating through three homes, none carrying supersession); +1 protocol duty (the carrier retirement-record rule; witness: automation-c2937928 silently deleted between 17:23 and 17:38 on 2026-10-03, discovered by an empty automation listing); +1 commit-content duty (the rejected-egress un-cover flip; witness: 875594fe archived evidence-integrity-fences with its three origin rows false-closed against the completed path); +2 prose rule families (the origin-flip invariant with its reopen procedure, and the false-completion correction protocol; witnesses: the wave's seven archives reading as completed work, and this incident's hand-built corrections proving the protocol's shape); 0 scripts, hooks, or schema state fields added; 0 removals; the mechanical plans-egress gate and the census and lane-ordering machinery are the sibling plan's priced delta, never this plan's (see Coordination); the standing machinery inventory check's pre-existing failure on the base tree (the unregistered scripts/sync_runtime_scripts.sh, landed 92b7db1b) is outside this plan's delta and outside its scope (Task 6 records it for the registry's owner, never repairs it).

## Gist & Examples

TLDR: the stray-close response gets validated and its root causes close repo-side, so a stale directive can no longer masquerade as operator policy.

Between 11:53 and 17:23 on 2026-10-03, seven landed-but-unexecuted plans were archived as bare renames (2702fe88 archiving two, c030f087, 2a5573c7, 9bb1cd04 archiving two, 6ce2e017), 159-plus unchecked task boxes in total, while the armed survey-only carrier restored a lifted directive from its 2026-10-02 prompt text. The fix turn's response was deliberately ad hoc: the carrier rewrite, the state-file flag flip, the survey fence (edbb7f89, amended), the seven-plan restorations (950128bc, 4dc5a2bb), and the dossier. The operator policy binds every arm of this plan verbatim: archiving plans without any real changes is not allowed unless the operator specifically asks each time. Every ad-hoc fix made during the incident response must be validated or replaced through a proper plan with review, so the situation cannot happen again.

This plan validates each fix (restoration audit, fence and state-file re-derivation, carrier-mandate consistency), then closes the two gaps the fixes could not: directives that live only in prompts and state files carry no supersession, so the plan lands a tracked directives home that payloads read at turn start; and completion claims (covered rows, pruned entries, memory records) had no correction procedure, so the plan names one. The mechanical plans-egress gate that refuses the wave's rename shape on every lane is the sibling plan's payload and is only re-keyed here (see Coordination).

Example: when the operator next lifts or issues a lane directive in chat, the lift lands as a one-file commit to the directives home, and every carrier fire after that commit reads the lifted state; the 2026-10-02 failure mode, a prompt clause outliving its own lift across 87 fires, is closed structurally.

## Terms

- **Operator directives home**: `docs/maintenance/operator-directives.md`, the tracked file of record for operator lane directives. A directive's issue, lift, supersession, or expiry is valid only when recorded there. Where a carrier prompt, loop directive, or state-file note carries directive text, the payload reads the home at turn start and the home wins on conflict.
- **Directive record**: one `## D-<n>: <title>` section in the home: `issued` date, `status` (active, superseded, lifted, or expired), `expiry` (a date or none), the directive text verbatim when operator-issued, `scope` (the lanes it binds), `superseded_by` when not active, and a `witness` line citing the commit or document that proves issuance.
- **Origin-flip invariant**: a covered origin flip is truthful only while the covering plan sits at the plans root; an archive that removes a plan from the plans root without the done gate's evidence turns the flip into a false-completion claim subject to the correction protocol.
- **Reopen-on-unexecuted-archive**: the recorded remedy for discovering an unexecuted archive: restore the plan by reverse rename, origins stay covered, and the restored plan is recorded as queued execution work in the turn record; no actor flips the origin rows at discovery. The rejected-archive directory is the one sanctioned exit where rows un-cover instead (the un-cover duty).
- **False-completion correction protocol**: the three-remedy procedure for a discovered false completion claim: tree first (the reopen rule), registry second (the affected entry or row corrected with a dated corrections line naming the false claim and its witness commit), memory third (a supersession note in the affected memory record naming the false claim, the correction, and the witness).
- **Turn record**: the scheduler state file plus the session's recorded decision reasons; gitignored operational state, never a directives home.

## Coordination (binding, not re-litigating)

- The sibling plan `docs/history/plans/2026-10-03-archive-ceremony-gate-universal.md` (landed on main as 6006a9d7 on 2026-10-03, its origin covered by 04d8d604, execution pending; the reviewed branch tip 035b81c0's amendment regions are byte-identical to the landed bytes) owns the mechanical plans-egress gate (its check-archive mode, the landing-lane wiring, the authoring-closeout wiring), the census and lane-ordering machinery (queued_execution state records, execution-before-authoring ordering, the aging bound), and the verbatim-quote coordination clause. This plan re-keys the dossier's mechanical-gate arm and exec-queue arm to the sibling plan and lands none of that machinery; the duplicate-origin coverage gate's fold-or-re-key duty is discharged by this authoring pass itself: the origin `docs/history/backlog/2026-10-03-archive-ceremony-gate-universal.md` remains the sibling plan's origin of record, and this plan's scope-of-record block deliberately does not claim it.
- Same-surface sequencing: the sibling's Task 3 amends the same landed-plan disposition fence this plan edits. Every task below that edits the fence re-reads it immediately before editing and stops on drift for reconciliation instead of proceeding. The sibling's Task 4 targets prompt-templates.md, a file this plan never touches (Task 3 anchors the carrier prompt's actual definition home instead; see that task's re-keying note).
- The sibling-owned origin file is never edited by this plan; the dossier origin alone is this plan's fold at completion.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `docs/maintenance/operator-directives.md` *(new)*
- `agents/skills/maintenance/SKILL.md` *(modified; the Step 0 directives-home read duty, the carrier retirement-record rule, the fence-adjacent invariant and reopen rules, the correction protocol, and the Task 2 verbatim-policy repair)*
- `agents/skills/maintenance/zcode.md` *(modified; the Recurring automation recipe gains the lift-directives-at-dispatch pointer)*

**Tests:**
- none; the plan adds no code and no test files, and its checks are the Validation Commands

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason. A restoration-audit defect (Task 1) or a fence-defect repair (Task 2) may touch plans-root plan files, the rolling prompt log, or the fence's own wording; those repairs are plan-related by definition.

**Out of scope; reject unless plan-related:**
- `scripts/reverse_squash_guard.py`, `agents/skills/execute-plan/SKILL.md`, `agents/skills/plans/SKILL.md`, and the sibling's census and state-recording machinery; reason: sibling-owned surfaces (see Coordination); this plan edits none of them.
- `agents/skills/maintenance/prompt-templates.md`; reason: the carrier prompt's definition home is zcode.md's Recurring automation recipe (prompt-templates.md carries child-payload templates and no carrier-prompt duties paragraph); the sibling plan's own prompt-templates amendment is its payload to reconcile, not this plan's.
- `scripts/machinery_registry.json` and `scripts/sync_runtime_scripts.sh`; reason: the inventory check's pre-existing baseline failure (the script landed unregistered in 92b7db1b) predates this plan; Task 6 records it for the registry's owner, never repairs it here.
- The scheduler state file's bytes; reason: gitignored operational state and the turn record; this plan adds no schema field and stores no directive there.
- Carrier automation payloads; reason: they live outside the repo; their governance lands as the directives home and the zcode.md recipe pointer.
- Executing the restored plans; reason: the execution lane's queue work, offered per the fence, not this plan's payload.

## Validation Commands

```bash
# wiring anchors, each RED before its task and GREEN after ([x] escapes keep the
# plan's own text from satisfying the greps; needles re-derived from the exact
# prescribed insertions)
grep -q "operator-directives" agents/skills/maintenance/SKILL.md
grep -q "retiremen[t] record" agents/skills/maintenance/SKILL.md
grep -q "operator-directives" agents/skills/maintenance/zcode.md
grep -q "truthful only while the covering plan sits at the plans roo[t]" agents/skills/maintenance/SKILL.md
grep -q "origins stay covere[d]" agents/skills/maintenance/SKILL.md
grep -q "un-covers the archived plan's origin rows, covered to open, in the same commi[t]" agents/skills/maintenance/SKILL.md
grep -q "false-completion correction protoco[l]" agents/skills/maintenance/SKILL.md
# Task 2 repair gate: the fence gains the origin's verbatim policy sentence (with
# "any") in Task 2; the landed fence carries the form without "any" today (RED)
grep -q "archiving plans without any real changes is not allowed unless the operator specifically asks each time" agents/skills/maintenance/SKILL.md
# Task 3 GREEN: the home exists and carries the two mandated seed records (count gates = 1)
test "$(grep -cE '^## D-[0-9]+: execution-lane state' docs/maintenance/operator-directives.md)" = 1
test "$(grep -cE '^## D-[0-9]+: archiving policy' docs/maintenance/operator-directives.md)" = 1
# machinery inventory: the plan adds zero registered-class machinery; expect exactly
# the pre-existing baseline failure (the unregistered scripts/sync_runtime_scripts.sh,
# landed 92b7db1b) and zero new failures; the baseline row is recorded, never repaired
python3 scripts/machinery_inventory.py --check
```

### Task 1: restoration completeness audit (the seven wave plans and the template case)

Files:
- none mandated (audit; a rider repair commit only on a verified defect)

Evidence:
- `for c in 2702fe88 c030f087 2a5573c7 9bb1cd04 6ce2e017 875594fe; do git show "$c" --name-status --format='commit %h'; done`; covers `the wave inventory re-derivation: each archive commit lists its renamed plans`
- `diff <(git show 2702fe88^:docs/history/plans/2026-10-03-ref-move-integrity-fences.md) <(git show main:docs/history/plans/2026-10-03-ref-move-integrity-fences.md)`; covers `the byte-identity method (archive-parent bytes against committed bytes), shown for one wave plan; item 2 runs it for every plan still at the plans root`
- `git cat-file -e main:docs/history/backlog/2026-10-02-round-scoped-review-token-metrics.md`; covers `origin cross-reference resolution, shown for one path; item 3 runs it per origin path`
- `grep -n "Plan review record:" docs/history/plans/2026-10-03-ref-move-integrity-fences.md`; covers `review-record reference presence and form, shown for one plan`
- `git log --diff-filter=R --name-status -- docs/history/plans/completed docs/history/backlog/completed docs/history/plans/deferred docs/history/backlog/deferred`; covers `the full-archive-history pairing sweep's rename enumeration`

- [x] Re-derive the wave inventory from the dossier against git: archive commits 2702fe88 (ref-move-integrity-fences, single-commit-per-lane-event), c030f087 (soften-watchlist-source-of-truth), 2a5573c7 (interrupted-manifest-pile-drain), 9bb1cd04 (pins-suite-simplification, review-token-round-attribution), 6ce2e017 (selection-docstring-precision); the audit-window template case 875594fe (evidence-integrity-fences, restored in the audit itself); restorations 950128bc and 4dc5a2bb; a witness commit that no longer resolves, or a roster name that does not match its commit, is a finding, never a silent proceed [class: REPOSITORY_TEST]
- [x] For each wave plan still at the plans root at execution time: byte-identity holds, `diff <(git show <archive-commit>^:docs/history/plans/<name>) <(git show main:docs/history/plans/<name>)` empty; for any wave plan since legitimately executed, verify its exec landing commit and archive carry the done gate's evidence shape (checked boxes plus the exec-review record) instead of byte-identity [class: REPOSITORY_TEST]
- [x] Full-archive-history pairing sweep (the dossier Problem section's mandate beyond the 2026-09-29 window): enumerate every rename into an archive state directory over all history (the Evidence sweep command), and for each renamed plan verify the pairing (an exec landing or an archive carrying the done gate's evidence shape, or a wave or template-case member already covered by item 2); an unpaired older archive is a finding: repair per the reopen rule when the remedy is a reverse rename, otherwise file the finding as a backlog row in the same turn [class: REPOSITORY_TEST]
- [x] Origin cross-references: every path in each audited plan's Backlog origins block resolves on the committed tree (`git cat-file -e main:<path>` per path), or the turn record names the path's fold commit (an executed plan's origin deleted per the fold-and-delete gate is a legitimate disposition, witnessed by its exec landing); a dangling path with no fold witness is a defect [class: REPOSITORY_TEST]
- [x] Registry rows: each restored-and-unexecuted plan has its PLAN-PROMPTS entry listing its origins, or the turn record names the entry's legitimate disposition (executed, superseded, covered by another plan); a live plan with no entry and no recorded disposition is a defect repaired in the rider commit [class: REPOSITORY_TEST]
- [x] Review-record references: each audited plan carries a `Plan review record:` header line naming its staging series with a well-formed repo-relative path; the homes are per-checkout state, so the check is the reference's presence and form, never a sidecar's existence in this checkout [class: REPOSITORY_TEST]
- [x] Record the verdict per plan in the turn record; on zero defects record `restoration-audit: clean`; on any defect repair it in the same turn (restore bytes, re-point the row, re-add the entry) and commit `plans: stray-close restoration audit repairs (<defect count>)` [class: IMPLEMENTATION_REQUIRED]
- [x] Commit (if any residue): `chore: restoration audit residue` [class: IMPLEMENTATION_REQUIRED]

### Task 2: fence, state-file edit, and carrier-mandate re-derivation (the fix turn's three prose fixes)

Files:
- `agents/skills/maintenance/SKILL.md` (only on a verified defect)

Evidence:
- `(cd "$(git rev-parse --path-format=absolute --git-common-dir | sed -e 's,/.git$,,')" && python3 -c "import json;json.load(open('.ai-playbook/scheduler-state.json'))")`; covers `state-file parse safety at the primary checkout (the explicit-rooted form; the state file is primary-checkout-only operational state)`
- `git show --stat 2702fe88 c030f087 2a5573c7 9bb1cd04 6ce2e017 edbb7f89 950128bc 4dc5a2bb`; covers `witness-commit reality`
- `grep -q "archiving plans without any real changes is not allowed unless the operator specifically asks each time" agents/skills/maintenance/SKILL.md`; covers `the operator policy verbatim as issued; the landed fence carries the form without "any", the defect criterion (1) records and this task repairs`

- [x] Re-read the landed-plan disposition fence and the Step 0 carrier duties immediately before judging; drift from the shape this plan describes stops the task for reconciliation (the sibling plan amends the same fence) [class: REPOSITORY_TEST]
- [x] Judge the fence on six criteria, one verdict line each in the turn record: (1) the operator policy sentence present verbatim as issued (the origin's form with "any"; the landed fence carries the form without "any", which is the defect this criterion records today); (2) the refusal scoped to every lane and every turn including carrier-prompt clauses; (3) the sanctioned stray-close evidence form names the on-disk checks (exec-review record for the final bytes, task boxes verified, the 32cedc71 form); (4) the per-case operator-ask escape is present with the direction recorded in the turn record; (5) the witness commits named in the fence resolve in git; (6) the fence's placement in the survey step is where a disposition decision is actually made; a failed criterion other than (1) is a defect fixed by a targeted wording or placement edit in this task, never by new machinery [class: IMPLEMENTATION_REQUIRED]
- [x] Apply the criterion (1) repair: insert "any" into the fence's policy sentence (a targeted wording edit under the task's drift stop), then run the policy needle GREEN [class: IMPLEMENTATION_REQUIRED]
- [x] Judge the state-file edit safety: the state file parses as JSON (read at the primary checkout per the Evidence line's explicit-rooted form); the survey_only flip and its survey-note trail read consistent with the fence's witness sentence; the loop's targeted-update protocol (the rolling prompt log's standing rules and this skill's State file section) covers the edit class the fix turn performed; the verdict records the residual this plan acts on: operational state stays in the gitignored state file, directives move to the tracked home (Task 3), and no state-file machinery is added here [class: REPOSITORY_TEST]
- [x] Judge the re-armed carrier mandate against the skill lifecycle: enumerate the armed scheduled automations, record the carrier's mandate clauses (restored mandate, hard fence, per-case operator-ask policy, never-delete-self) in the turn record, and verify each clause's durable repo-side home exists (the fence, the skill's carrier duties, and after Task 3 the directives home); a clause living only in the payload is a finding remedied by Task 3's home, never by editing the payload [class: REPOSITORY_TEST]
- [x] Commit (only on a defect fix): `maintenance: fence re-derivation repair (<criterion>)` [class: IMPLEMENTATION_REQUIRED]

### Task 3: the operator directives home and the carrier lifecycle rules

Files:
- `docs/maintenance/operator-directives.md` *(new)*
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`

Evidence:
- `test "$(grep -cE '^## D-[0-9]+: execution-lane state' docs/maintenance/operator-directives.md)" = 1`; covers `the execution-lane seed record`
- `test "$(grep -cE '^## D-[0-9]+: archiving policy' docs/maintenance/operator-directives.md)" = 1`; covers `the archiving-policy seed record`
- `grep -q "operator-directives" agents/skills/maintenance/SKILL.md`; covers `the Step 0 read duty wiring`
- `grep -q "retiremen[t] record" agents/skills/maintenance/SKILL.md`; covers `the carrier retirement-record rule`
- `grep -q "operator-directives" agents/skills/maintenance/zcode.md`; covers `the recipe lift-at-dispatch pointer`

- [x] RED: run the Task 3 Validation Commands probes; the home is absent and the wiring needles fail today (the home-absence probe is this item: `test ! -e docs/maintenance/operator-directives.md` exits 0 before item 2) [class: REPOSITORY_TEST]
- [x] Create the home with the Directive record format as its preamble (`issued` date, `status` active, superseded, lifted, or expired, `expiry` a date or none, the directive text verbatim when operator-issued, `scope`, `superseded_by`, `witness`; the supremacy rule: issue, lift, supersession, and expiry are valid only when recorded here, and a payload-carried directive defers to the home at turn start) and seed it by transcription with the two mandated records re-derived at execution time: `## D-1: execution-lane state` (status active, expiry none: the execution lane reopened 2026-10-03, superseding the 2026-10-02 execution-lane closure; witness: the day's execution landings and the dossier's directive history) and `## D-2: archiving policy` (status active, expiry none: the operator's verbatim policy sentence with "any", per the origin; witness: the survey fence and the dossier's Operator policy section); seeding invents no new directive and no third record is required by this plan [class: IMPLEMENTATION_REQUIRED]
- [x] Amend Step 0 (context load): the turn reads `docs/maintenance/operator-directives.md` (the directives home) before acting on any directive-bearing clause, the home's record wins on conflict with any prompt or state-file clause, and a directive lift is a one-file commit to the home; drift stop: re-read Step 0 immediately before the edit [class: IMPLEMENTATION_REQUIRED]
- [x] Amend the Step 0 carrier duties with the retirement rule: a session never deletes or silently replaces its own carrier automation without a state-file retirement record naming the automation id and the reason; witness: the silent deletion of automation-c2937928 on 2026-10-03, discovered by an empty automation listing [class: IMPLEMENTATION_REQUIRED]
- [x] Amend the Recurring automation recipe in agents/skills/maintenance/zcode.md (the loop carrier's prompt definition home): the carrier prompt construction lifts lane directive text from `docs/maintenance/operator-directives.md` at dispatch instead of baking aging clauses, with the 2026-10-02 carrier clause named as the anti-shape; drift stop: re-read the recipe immediately before the edit; this plan deliberately does not anchor a carrier-prompt duties paragraph in prompt-templates.md (that file carries child-payload templates and no such paragraph; the sibling plan's own Task 4 anchor there is its payload to reconcile) [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Task 3 Validation Commands GREEN (both count gates exactly 1, all three wiring greps pass) [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: operator directives home with turn-start reads and carrier retirement records` [class: IMPLEMENTATION_REQUIRED]

### Task 4: the origin-flip invariant and the reopen rules

Files:
- `agents/skills/maintenance/SKILL.md`

Evidence:
- `grep -q "truthful only while the covering plan sits at the plans roo[t]" agents/skills/maintenance/SKILL.md`; covers `<the invariant sentence>`
- `grep -q "origins stay covere[d]" agents/skills/maintenance/SKILL.md`; covers `<the restore remedy's row treatment>`
- `grep -q "un-covers the archived plan's origin rows, covered to open, in the same commi[t]" agents/skills/maintenance/SKILL.md`; covers `the rejected-egress un-cover duty`

- [x] RED: the three Task 4 needles fail today [class: REPOSITORY_TEST]
- [x] Drift stop: re-read the fence paragraph immediately before editing (the sibling plan amends the same paragraph; compose, never duplicate) [class: REPOSITORY_TEST]
- [x] Land the three sentences beside the fence in one targeted edit: the invariant (a covered origin flip is truthful only while the covering plan sits at the plans root; an unevidenced archive turns the flip into a false-completion claim under the correction protocol); the reopen rule (discovering an unexecuted archive, any survey turn or session restores the plan by reverse rename, origins stay covered, and the restored plan is recorded as queued execution work in the turn record; no actor flips the origin rows at discovery); the un-cover duty (an egress to a rejected directory un-covers the archived plan's origin rows, covered to open, in the same commit, owned by the archiving session; witness: 875594fe's three rows false-closed against the completed path) [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Task 4 needles GREEN [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: origin-flip invariant with the reopen and rejected-egress un-cover rules` [class: IMPLEMENTATION_REQUIRED]

### Task 5: the false-completion correction protocol

Files:
- `agents/skills/maintenance/SKILL.md`

Evidence:
- `grep -q "false-completion correction protoco[l]" agents/skills/maintenance/SKILL.md`; covers `<the protocol's landing>`

- [x] RED: the Task 5 needle fails today [class: REPOSITORY_TEST]
- [x] Drift stop: re-read the fence paragraph immediately before editing [class: REPOSITORY_TEST]
- [x] Land the false-completion correction protocol beside the fence in one targeted edit: when a completion claim is discovered false (a covered row over an unexecuted plan, a pruned entry over a live origin, a memory record describing a standdown that was a violation), the correction lands in the discoverer's turn as three named remedies in order: tree first (the reopen rule above), registry second (the affected entry or row corrected with a dated corrections line naming the false claim and its witness commit), memory third (a supersession note in the affected memory record naming the false claim, the correction, and the witness); the protocol generalizes this incident's hand-built corrections (the restorations, the re-pointed rows, the memory supersession notes, the dossier itself) [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Task 5 needle GREEN [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: false-completion correction protocol (tree, registry, memory)` [class: IMPLEMENTATION_REQUIRED]

### Task 6: full validation and coordination reconciliation

Files:
- none (validation and bookkeeping only)

Evidence:
- `python3 scripts/machinery_inventory.py --check`; covers `<zero machinery-registration delta>`
- `bash scripts/check-no-em-dash.sh paths -- agents/skills/maintenance/SKILL.md agents/skills/maintenance/prompt-templates.md docs/maintenance/operator-directives.md`; covers `<no em-dash in the changed surfaces>`

- [x] Run every post-landing Validation Command in order, expect each GREEN, with the machinery inventory check read per its baseline comment (the pre-existing failure recorded for the registry's owner, never repaired) [class: REPOSITORY_TEST]
- [x] Sibling reconciliation: verify the sibling plan's landed bytes (6006a9d7 or its successor amendments) at execution time; confirm the Coordination section's claims still hold against them (its egress gate and census machinery own the re-keyed arms); no sibling surface is edited either way [class: REPOSITORY_TEST]
- [x] Re-verify the standing operator policy sentence still reads verbatim in the fence after all amendments [class: REPOSITORY_TEST]
- [x] Commit (if any residue): `chore: stray-close closure validation residue` [class: IMPLEMENTATION_REQUIRED]

## Evaluation Criteria

**Quality dimensions:**
- correctness: every audit verdict cites the command that produced it, and the byte-identity method (archive-parent bytes against committed bytes) is re-derivable from the Evidence lines alone
- consistency: the home's records follow one format, and the fence-adjacent rules compose with the sibling plan's amendments without duplication (the drift stops bind)
- maintainability: the Directive record format lives in the home's own preamble, so a future record needs no new convention and no skill edit

**Done when:**
- every post-landing Validation Command is green on the executed tree, with the machinery inventory check's pre-existing baseline failure recorded rather than repaired
- the directives home exists with the two mandated seed records and the preamble format
- the Step 0 read duty, the retirement-record rule, the invariant and reopen rules, the un-cover duty, the correction protocol, and the payload pointer are present in the two skill files
- the restoration audit verdicts are recorded and any defect repaired
- no sibling-owned surface changed

**Ship when:**
- the re-armed carrier and its successor payloads actually read the directives home at dispatch (operational adoption outside the repo; recorded via the turn record, never verifiable repo-side)

## Assumptions

- assume the origin's `Class: incident-investigation` re-derives, per the machinery doctrine's filing-time consumption rule, as fence-class: the dossier's Problem section witnesses completed integrity failures (archives reading as completed work, origin rows false-closed), so the completed-integrity-failure bar governs this plan's protocol-layer addition; basis: the doctrine's fence-class definition and the dossier's Problem section
- assume the sibling plan's landed bytes (6006a9d7) keep the check-archive and census machinery its reviewed branch tip 035b81c0 drafted, so the Coordination pointers hold; if a later amendment reshapes them, only the Coordination pointers need reconciliation, never this plan's tasks; basis: the landed plan read at this plan's authoring time, byte-identical to 035b81c0 in the amendment regions
- assume the window audit's completeness holds for its window (2026-09-29 onward); the dossier's full-history extension is Task 1's sweep duty, and an unpaired older archive it finds is a finding to repair or file, never an assumption violation; basis: the dossier's Problem section and its operator-directed 2026-10-03 audit record
- assume seeding the home with the execution-lane state and the archiving policy transcribes already-issued operator directives (witnessed in the dossier, the fence, and the day's execution landings) and invents no new directive; basis: the operator policy's verbatim recording in the dossier's Operator policy section
- assume the home lives at `docs/maintenance/operator-directives.md`: the directory is the tracked operational-record home (project-decisions.md, document-registry.md, glossary.md live there) and every reference stays repo-relative; basis: the directory's existing inventory, read 2026-10-03
- assume the execution lane is reopened (operator directive, 2026-10-03) and this plan dispatches for execution after landing; basis: the dossier's Operator policy section and the entry's authoring constraints
- assume the state file stays the turn record and keeps its gitignored status; no directive lives there permanently, and the fix turn's flag flip remains valid operational history; basis: the dossier's arm 3 wording

Decision points requiring a grill: none remain.

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-03-stray-close-incident-dossier.md` (origin class: operator-directed, incident-investigation): the covering plan executed 2026-10-03 (restoration audit clean including the full-archive-history pairing sweep; fence re-derived with the verbatim with-any policy repair; operator directives home seeded with D-1 execution-lane state and D-2 archiving policy plus the Step 0 read duty, the carrier retirement-record rule, and the zcode.md directive-lift pointer; origin-flip invariant with the reopen and rejected-egress un-cover rules; false-completion correction protocol; exec review r1 ready=yes zero blocking); the backlog item is deleted in the same completion pass per the fold-then-delete rule; this section is its disposition of record.
