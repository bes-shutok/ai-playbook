# Plan: Quota display refresh cadence

Backlog origin: docs/history/backlog/2026-09-25-quota-counter-manual-refresh-cadence.md
Driving force: code-quality (operator-side quota-state judgment during parallel runs)

## Terms

- **Display snapshot**: a runtime or desktop quota percentage that renders a server-fetched entitlement snapshot held in a client cache whose TTL is 10 minutes (`entitlementCacheTtlMs = 600*1e3` in the desktop renderer) and whose display rounds to integer percent. It is not a live counter: any observation window shorter than the cache TTL can show a stale value regardless of real consumption, and a sub-1-percent burst can sit inside one integer step.
- **Operator refresh action**: the runtime's manual `Refresh quota` control on the sidebar usage panel, which forces a fresh server fetch of the entitlement snapshot. It is a desktop UI control: only a human at the desktop can operate it; an unattended maintenance turn cannot.
- **Refresh cadence**: the operator-side rule this plan pins: while a parallel fleet is active, at least one manual refresh per 5 minutes whenever quota state is being judged from the display, so the displayed value is at most about 5 minutes stale instead of up to 10 or more.
- **Evidence hierarchy**: the ordering of quota evidence for agent decisions: the probe reading (used_percent, minutes_remaining, status) together with the snapshot-recorded source value (probe | unknown | skipped-unsupported-harness) and the taken time the turn records is the primary reading; when the probe is unusable, log-derived liveness counting substitutes (count `model.request.completed` events per minute in the runtime log; 429 retry backoffs consume no quota, so a busy-looking interval can legitimately deduct little); the display is advisory only: while a probe or log-derived reading is obtainable it is never decision evidence, and on the only-a-display edge its freshest manually refreshed value is used only when it is not older than the refresh cadence (an older value is recorded as unknown rather than used), with the staleness recorded as an annotation on the recorded source value, never a competing source kind.
- **Pin**: a fixed-string exact-count gate in `scripts/check_maintenance_pins.sh` that fails when its prose span is deleted or duplicated. This plan adds two pins, one per prose insertion.

## Assumptions

- assume the full mechanics and the cadence rule live in the maintenance runtime overlay `agents/skills/maintenance/zcode.md`, inside the Quota leg, as a new bullet between the timezone-trap bullet (ending `convert before comparing.`) and the usage-pricing-seed bullet; basis: the Quota leg is the corpus's quota-judgment home, the timezone-trap bullet is its display-mechanics neighbor (both are look-and-convert traps around quota readings), and the overlay is the one file allowed to name runtime-specific surfaces such as the sidebar control.
- assume `agents/skills/maintenance/SKILL.md` carries only a runtime-agnostic caveat bullet placed immediately after the Quota snapshot bullet of the Step 1 survey arm list (the bullet ending `transcription of those two keys.`); basis: SKILL.md must stay runtime-agnostic (the existing agnosticism pin forbids primitive names there), the Quota snapshot bullet is the survey's decision-input home, and the caveat governs exactly that input's display-layer sibling.
- assume the mechanical gate is a new pins section appended to `scripts/check_maintenance_pins.sh` immediately before its final `maintenance pins: all hold` echo, holding one exact-count pin per insertion, authored before the prose (pins-first, so each insertion flips its pin from RED to GREEN); basis: the pins script is the established mechanical gate for maintenance-skill wording and its sections follow this append pattern.
- assume the origin item's probe-endpoint re-verification parenthetical is already satisfied: the Quota leg's fallback paragraph records the endpoint as repaired by the budget-gate execution with the live monitor endpoint, and the origin item's 2026-09-13 witness predates that repair; basis: the landed wording at the fallback bullet; no probe script changes in this plan.
- assume the origin fix shape's recurring-reminder-automation arm is an accepted limitation here, not an implemented surface; basis: an unattended turn cannot operate the desktop refresh action, so a reminder automation would add loop load without acting, and the durable remedy is the evidence hierarchy plus the operator cadence rule.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the maintenance corpus stops treating a frozen quota percentage as evidence, pins the display-staleness mechanics and the 5-minute operator refresh cadence into the quota leg, and makes the probe report the only decision-grade source, with two new pins guarding both insertions.

During a 4-session parallel run on 2026-09-25 the sidebar 5h quota percentage sat at 43 percent for over 15 minutes while the sessions completed dozens of model requests per minute. App-bundle diagnosis proved the display renders a server-fetched entitlement snapshot cached for 10 minutes and rounded to integer percent, so the frozen reading was display staleness, not stalled consumption. An agent or operator judging quota state from that display during the run could not distinguish a healthy window from an exhausted one, and the loop's pause and dispatch decisions depend on exactly that judgment.

Example of the new behavior: a maintenance turn mid-parallel-fleet sees the operator quoting a flat sidebar percentage. The turn's quota leg (overlay) now names the mechanics, treats the display as advisory, takes its decision reading from the probe report (or, when the probe is unusable, from per-minute log counting that proves counting is alive), and the turn output says so with source and timestamp; the corpus also tells the human operator to refresh the display at least every 5 minutes while the fleet runs, so the next display glance is at most 5 minutes stale. If a later edit deletes either insertion, its pin fails the maintenance pins gate with a named PIN FAIL line.

## Evaluation Criteria

**Quality dimensions:**
- correctness: both insertions sit at their named anchors (zcode.md Quota leg between the timezone-trap and pricing-seed bullets; SKILL.md survey list between the Quota snapshot and Friction-audit consult bullets), each present exactly once at its pinned span, verified in the joint direction (both insertions and both pins applied together).
- reliability: the pins fail loudly (exit 1 with named PIN FAIL lines) when either insertion is deleted or duplicated; the RED-then-GREEN arc is executed and recorded for each pin.
- maintainability: runtime-specific mechanics stay in the runtime overlay; SKILL.md carries only a runtime-agnostic caveat and the existing agnosticism pin stays green after the insertion.
- reviewability: every claim about the display mechanics traces to the origin item's app-bundle diagnosis, and every insertion is pinned by an exact-count gate over an apostrophe-free distinctive span.

**Done when:**
- `scripts/check_maintenance_pins.sh` carries the two new pins and exits 0 on the executed tree, after having exited 1 with exactly those two PIN FAIL lines before the prose landed.
- The zcode.md Quota leg bullet and the SKILL.md caveat bullet are present exactly once each at their pinned spans, with both baseline counts reading 0 before insertion.
- The full Validation Commands block passes end to end on the executed tree, including the public hygiene scan and the em-dash gate.

**Ship when:**
- The corpus rule is live in this repository now; consumer repositories receive it through the standing vendored-sync rules (the maintenance skill is already a synced surface), and the operator cadence reaches the human through turn outputs quoting the rule while a fleet is active.

### Accepted limitations (premortem residuals, recorded deliberately)

- The refresh cadence is an operator habit the corpus can state but not enforce: an unattended turn cannot operate the desktop refresh action, and no mechanical witness exists for a human skipping it. For probe-obtainable runs the evidence hierarchy mitigates by making agent decisions display-independent; the bounded display-only edge (a display older than the cadence, or a freshness claim the conversation did not observe, records as unknown) remains the accepted residual.
- The reminder-automation arm of the origin fix shape is deliberately not implemented (an automation cannot act on the desktop UI); reviving it needs a desktop-automation capability, not a corpus edit.
- The mechanics pin records the diagnosed constants (10-minute TTL, integer percent) as of the 2026-09-25 app-bundle diagnosis; a runtime update that changes the cache semantics can stale the wording, and the pin would keep the stale sentence green. Re-verification is not a scheduled duty; the method is desktop app-bundle inspection (extract the renderer bundle and locate the entitlement cache constant and the refresh action), which this limitation restates so it survives the origin item's closeout deletion.
- The log-counting fallback is named as the probe-unusable substitute but this plan adds no new tooling; the counting recipe lives in the landed quota-leg bullet, with the friction-audit recipe supplying only the log location and line schema, and an operator following it does the counting by hand or with existing scripts.
- The pins guard the corpus wording, not the display behavior; a display-layer change never fails a pin, by design.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

- `docs/plans/2026-09-25-quota-display-refresh-cadence.md` (this plan, whole file)
- `agents/skills/maintenance/zcode.md` (the Quota leg region: the new bullet and its two anchor neighbors; the rest of the file is frozen context)
- `agents/skills/maintenance/SKILL.md` (the Step 1 survey arm list region: the new caveat bullet and its two anchor neighbors; the rest of the file is frozen context)
- `scripts/check_maintenance_pins.sh` (the new pins section and the file tail it appends to; the rest of the file is frozen context)
- `docs/history/backlog/2026-09-25-quota-counter-manual-refresh-cadence.md` (read-only origin; disposition wording only)

Out of scope: `scripts/quota_window_probe.py` and its modes; the done and execute-plan skills; `agents/skills/maintenance/prompt-templates.md`; the friction-audit recipe beyond naming it as the counting home; any runtime app-bundle change.

## Validation Commands

The helper (dash-leading fixed strings stay positional; `--` before the file operand):

```bash
occ() { grep -oF -e "$1" -- "$2" | wc -l | tr -d ' '; }
```

Gates, evaluated on the executed tree from the repository root (all must hold):

1. Pins gate green: `bash scripts/check_maintenance_pins.sh` exits 0 and prints `maintenance pins: all hold`.
2. Overlay insertion pinned exactly once: `occ 'Sidebar display staleness and operator refresh cadence' agents/skills/maintenance/zcode.md` prints `1`.
3. Survey caveat pinned exactly once: `occ 'Quota display caveat' agents/skills/maintenance/SKILL.md` prints `1`.
4. Pin section present exactly once per span: `occ 'quota sidebar-staleness bullet count != 1' scripts/check_maintenance_pins.sh` prints `1` and `occ 'quota display caveat bullet count != 1' scripts/check_maintenance_pins.sh` prints `1`.
5. Joint-direction placement witnesses (evaluated with all three edits applied together; these two exits are the joint-direction simulation record): `awk 'index($0, "convert before comparing."){a=NR} index($0, "Sidebar display staleness and operator refresh cadence"){b=NR} index($0, "- Usage pricing seed"){c=NR} END{exit !(a && b && c && a<b && b<c)}' agents/skills/maintenance/zcode.md` exits 0, and `awk 'index($0, "transcription of those two keys."){a=NR} index($0, "Quota display caveat"){b=NR} index($0, "- Friction-audit consult:"){c=NR} END{exit !(a && b && c && a<b && b<c)}' agents/skills/maintenance/SKILL.md` exits 0.
6. Em-dash gate green over the plan's added lines (the base tree already carries one U+2014 in zcode.md frozen context, so whole-file prose mode would red at base; the added-lines mode scans every extension regardless of the prose filter, so the pins script's added lines are included): `bash scripts/check-no-em-dash.sh added-lines --base <base-sha> agents/skills/maintenance/zcode.md agents/skills/maintenance/SKILL.md scripts/check_maintenance_pins.sh docs/plans/2026-09-25-quota-display-refresh-cadence.md` exits 0 (the path operands scope the window to this plan's Review Scope set, so a peer commit's added lines elsewhere never fail this gate), where `<base-sha>` is the base commit recorded in Task 1.
7. Public hygiene scan green: run the hygiene scan script from the user facts key `public_hygiene_scan_script` from the repository root; exit 0 required.

RED expectations recorded during execution, before their flipping edit:

- After Task 2 (pins only): gate 1 exits 1 with exactly the two new PIN FAIL lines (`quota sidebar-staleness bullet count != 1`, `quota display caveat bullet count != 1`) and no other new failures.
- Before Task 3: gate 2 prints `0`. Before Task 4: gate 3 prints `0`.

## Tasks

### Task 1: Phase-0 drift gate

Record the base digests of the three touched files and verify them before any edit; the gate fails closed on unexplained drift (a run-explained mismatch routes through the drift recovery arm's resume shortcut instead of standing down) and runs once per execution:

- zcode.md sha256: `e2e526ecdd596d2d16be285e6327cb660e2707e535beb3c2d5c6a61c1be97ded`
- SKILL.md sha256: `6d240024b74b0680c80f13df4e443c97f91e9345a0f631118702acdbcdef8831`
- check_maintenance_pins.sh sha256: `2594971fab3a044897670ab501ec3c582a173a2b8930e834a77374d0400ffddd`

- [x] Run → verify GREEN (gate holds on the base tree): `shasum -a 256 agents/skills/maintenance/zcode.md agents/skills/maintenance/SKILL.md scripts/check_maintenance_pins.sh` matches all three digests above (fail-closed on unexplained drift, once-only: record the verification in the execution log and do not re-run the plan-recorded base set's digest comparison after later tasks' commits within the same execution; a resumed execution's Phase-0 digest check is that execution's single run, not the prohibited re-run; after a drift-arm re-derivation the fresh digests are the governing set) [class: REPOSITORY_TEST]
- [x] Record the base commit: `git rev-parse HEAD` as the run's first action, before the run's first commit; that sha is the `<base-sha>` operand of Validation Command 6; on a resumed run the base recorded in the run log governs and is never re-recorded mid-plan (a re-recorded base would silently narrow gate 6's added-lines window) [class: REPOSITORY_TEST]
- [x] Baseline span counts read zero: `occ 'Sidebar display staleness and operator refresh cadence' agents/skills/maintenance/zcode.md` prints `0` and `occ 'Quota display caveat' agents/skills/maintenance/SKILL.md` prints `0` [class: REPOSITORY_TEST]
- [x] Pins-gate baseline observation: run `bash scripts/check_maintenance_pins.sh` on the base tree and record exit 0 printing `maintenance pins: all hold` in the execution log; this observed empty failure set is the baseline Task 2's RED expectation diffs against; on any pre-existing failure, record the output, STOP, and stand down at Phase 0 with that recorded reason instead of surfacing it at Task 5 [class: REPOSITORY_TEST]
- [x] Drift recovery arm (executes only on a digest mismatch): first check whether the mismatch is explained by this run's own recorded commits: every Commit step records its resulting full sha in the execution log, and the resume shortcut requires all of (a) the recorded sha set is non-empty (an empty set never takes this shortcut; a digest mismatch before the first recorded commit routes to the re-derivation below), (b) `git rev-list <recorded-base>..HEAD` equals exactly the recorded sha set, and (c) `git status --porcelain -- agents/skills/maintenance/zcode.md agents/skills/maintenance/SKILL.md scripts/check_maintenance_pins.sh` is empty (a crash between an insertion edit and its commit leaves uncommitted bytes that commit-graph equality alone would wave through); when all three hold, resume from the execution log's next unchecked task, never re-executing a task already recorded as committed, and skip the re-derivation below. Otherwise re-read the three regions and re-assert, against the drifted bytes, each named anchor span by fixed-string count (apply the occ helper to each of the four anchor-neighbor strings: `convert before comparing.`, `- Usage pricing seed`, `transcription of those two keys.`, `- Friction-audit consult:`; each prints `1`), the zero baselines for insertions whose tasks are not yet recorded as committed in the execution log (a baseline reading exactly 1 for a recorded-committed insertion is consistent; re-assert count 1 against the landed bullet's pinned span instead of stopping), and the two gate 4 spans (`quota sidebar-staleness bullet count != 1`, `quota display caveat bullet count != 1`; expected count 1 when the log records Task 2 as committed, 0 otherwise); then record the re-derived state and fresh digests in the execution log and apply the stand-down enumeration below, resuming from the execution log's next unchecked task, never re-executing a task already recorded as committed, only when no stand-down condition fired. Stand-down enumeration (STOP with the recorded reason instead of editing): the recorded sha set carries an extra or missing commit relative to `git rev-list <recorded-base>..HEAD`; any anchor span is missing or duplicated; a baseline reads non-zero for an insertion whose task is not recorded as committed; a recorded-committed insertion's baseline reads anything other than exactly 1 (0 meaning the logged commit is no longer on disk, 2 meaning duplication); a gate 4 span reads other than its expected count [class: REPOSITORY_TEST]

### Task 2: Pins section in the maintenance pins gate

Append the two-pin section to `scripts/check_maintenance_pins.sh` immediately before the final `echo "maintenance pins: all hold"` / `exit 0` pair, mirroring the existing section style (comment naming the plan, exact-count checks on `$Z` and `$S`, fail-block, `exit 1` guard):

```bash
# --- quota display staleness and refresh-cadence pins (plan
# 2026-09-25-quota-display-refresh-cadence.md) ---
[ "$(grep -oF 'Sidebar display staleness and operator refresh cadence' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: quota sidebar-staleness bullet count != 1"; fail=1; }
[ "$(grep -oF 'Quota display caveat' "$S" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: quota display caveat bullet count != 1"; fail=1; }
[ "$fail" -eq 1 ] && exit 1
```

- [x] Run → expect RED: `bash scripts/check_maintenance_pins.sh` exits 1 and its output contains exactly the two new PIN FAIL lines `PIN FAIL: quota sidebar-staleness bullet count != 1` and `PIN FAIL: quota display caveat bullet count != 1`, with no other new failures [class: REPOSITORY_TEST]
- [x] Commit: `skills+scripts: add quota display staleness pins to the maintenance pins gate`, after asserting `git rev-parse HEAD` equals the sha recorded by the previous Commit step (the Phase-0 base commit for the first commit; on mismatch record both shas, STOP, and stand down), then recording the resulting full sha in the execution log [class: IMPLEMENTATION_REQUIRED]

### Task 3: Quota leg overlay bullet

Insert one new bullet into the Quota leg of `agents/skills/maintenance/zcode.md`, between the timezone-trap bullet (ending `convert before comparing.`) and the `- Usage pricing seed` bullet, as a sibling list item at the same indentation:

```markdown
- Sidebar display staleness and operator refresh cadence (diagnosed 2026-09-25 against the desktop app bundle): a desktop quota percentage is not a live counter; it renders a server-fetched entitlement snapshot held in a client cache whose TTL is 10 minutes (`entitlementCacheTtlMs = 600*1e3` in the renderer), and the display rounds to integer percent, so a value that stays flat across a busy interval is never by itself evidence that consumption stopped (it can reflect display staleness or a legitimately small deduction, since 429 retry backoffs consume no quota). The runtime exposes a manual `Refresh quota` action on the sidebar usage control that forces a fresh server fetch; that action belongs to the human operator at the desktop (an unattended turn cannot operate it), and while a parallel fleet is active the operator cadence is at least one refresh per 5 minutes whenever quota state is being judged from the display. While a probe or log-derived reading is obtainable, an agent turn never cites the desktop display as decision evidence: the primary reading is the probe's JSON (used_percent, minutes_remaining, status) together with the snapshot-recorded source value (probe | unknown | skipped-unsupported-harness) and the taken time the turn records; when the probe is unusable, log-derived liveness counting substitutes (count `model.request.completed` events per minute in the runtime log per the friction-audit recipe's log schema); every surfaced quota observation names its source and timestamp.
```

- [x] Run → expect RED before the insertion: `occ 'Sidebar display staleness and operator refresh cadence' agents/skills/maintenance/zcode.md` prints `0` [class: REPOSITORY_TEST]
- [x] Run → expect GREEN after the insertion: the same command prints `1`, and `bash scripts/check_maintenance_pins.sh` now passes the sidebar-staleness pin while still failing only the caveat pin (the SKILL.md insertion has not landed yet) [class: REPOSITORY_TEST]
- [x] Commit: `skills: pin sidebar display staleness and the operator refresh cadence into the quota leg`, after asserting `git rev-parse HEAD` equals the sha recorded by the previous Commit step (on mismatch record both shas, STOP, and stand down), then recording the resulting full sha in the execution log [class: IMPLEMENTATION_REQUIRED]

### Task 4: Runtime-agnostic survey caveat bullet

Insert one new bullet into the Step 1 survey arm list of `agents/skills/maintenance/SKILL.md`, between the Quota snapshot bullet (ending `transcription of those two keys.`) and the `- Friction-audit consult:` bullet, as a sibling list item at the same indentation:

```markdown
- Quota display caveat: a runtime or desktop quota display may render a cached server snapshot rather than a live counter (multi-minute cache lifetimes and integer rounding are common), so a display value that stays unchanged across a busy interval is never by itself evidence that consumption stopped; it can reflect display staleness or a legitimately small deduction. The probe's reading is the decision source, and when only a display is available, prefer its freshest manually refreshed value, never one older than the refresh cadence (display age is operator-attested, never measured: absent a refresh observed during the conversation, record the reading as unknown regardless of the claimed freshness; a display value older than about 5 minutes is recorded as unknown rather than used), and record the display staleness as an annotation on the snapshot's recorded source value (probe | unknown | skipped-unsupported-harness), never as a competing source kind.
```

- [x] Run → expect RED before the insertion: `occ 'Quota display caveat' agents/skills/maintenance/SKILL.md` prints `0` [class: REPOSITORY_TEST]
- [x] Run → expect GREEN after the insertion: the same command prints `1`, `bash scripts/check_maintenance_pins.sh` exits 0 printing `maintenance pins: all hold` (both new pins green, the existing agnosticism pin still green), and the two anchor-neighbor bullets are unchanged and unduplicated [class: REPOSITORY_TEST]
- [x] Commit: `skills: add the runtime-agnostic quota display caveat to the survey snapshot`, after asserting `git rev-parse HEAD` equals the sha recorded by the previous Commit step (on mismatch record both shas, STOP, and stand down), then recording the resulting full sha in the execution log [class: IMPLEMENTATION_REQUIRED]

### Task 5: Final validation sweep

- [x] Run → expect GREEN, in order, from the repository root: gates 1 through 7 of Validation Commands all hold on the executed tree [class: REPOSITORY_TEST]
Certification of this plan's bytes is owned by the authoring review loop (the readiness gate over the final bytes before landing); execution schedules no certification duty of its own, so no execution-time plan_readiness invocation runs.

## Closeout

- Per the plans skill Backlog origin contract, leave the origin item's disposition to the Plan Lifecycle completion step: the completion folds the disposition into the completed plan and deletes `docs/history/backlog/2026-09-25-quota-counter-manual-refresh-cadence.md`; do not flip the item's Status in place and do not keep a per-item archive.
- Record the execution in the scheduler state children ledger per the standing ledger rules.
- No new backlog items are expected from this plan; any review residual follows the standing residual-routing rules.


## Execution record (2026-09-25, in-session run on worktree branch 2026-09-25-execute-quota-display-cadence)

- All 14 boxes ticked. Base commit 023e9706d8a594e0f1a1970c850c38899569ae26 (Validation Command 6 operand). Commits: c7534d19 (Task 2 pins, RED verified exit 1 with exactly the two named PIN FAIL lines), d2bcc3fd (Task 3 overlay bullet; sidebar pin flipped green, caveat pin still red), 00171be2 (Task 4 caveat bullet; both pins green, agnosticism pin green).
- Phase-0 drift: zcode.md digest matched; SKILL.md and check_maintenance_pins.sh digests did NOT match the plan-recorded set. Drift explained by the recorded parked-dependency execution 817acbee landing on main after plan certification (the plan-recorded digests equal the tree at 2bc9ac8f, so that landing predates certification and caused no drift; 817acbee alone moved SKILL.md and check_maintenance_pins.sh to the observed values); not this run's commits and not unexplained, so the drift recovery arm's re-derivation ran: all four anchor-neighbor spans read 1, both insertion baselines read 0, both gate-4 spans read 0, pins baseline green (`maintenance pins: all hold`). Fresh governing digests recorded: zcode e2e526ec... (unchanged), SKILL.md 676ac8183d15eb2d4eb59ed05093d81b0da36107b38153a98fde54719f3fb76b, check_maintenance_pins.sh 2b6e2862a98e7da2f35b9be534865aea2badc3168b0090766442cdb45af7a84d. No stand-down condition fired.
- Task 5 gates 1-7 all green on the executed tree (gate 6 with base-sha 023e9706...). RED arc recorded per insertion (baseline occ 0 before each, 1 after; pins gate RED after Task 2 with exactly the two new PIN FAIL lines, green after Task 4).
- Origin disposition (folded per Closeout): the display-staleness mechanics, the 5-minute operator refresh cadence, the evidence hierarchy (probe primary, log-counting fallback, display advisory-only), and the accepted limitation of the reminder-automation arm are all landed and pinned; origin docs/history/backlog/2026-09-25-quota-counter-manual-refresh-cadence.md deleted with disposition folded into this completed plan record.
