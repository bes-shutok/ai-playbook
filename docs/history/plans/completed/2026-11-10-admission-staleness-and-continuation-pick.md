# Plan: admission staleness horizon (and the continuation-pick row disposition)

Backlog origin: docs/history/backlog/2026-11-10-paused-run-admission-record-starves-exec-lane.md
Required agent type: none (runtime-neutral)
Driving force: efficiency (primary), simplicity (secondary)
Plan review record: the staging series .ai-playbook/reviews/2026-11-10-plan-review-admission-staleness-and-continuation-pick-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 1.5h total, largest task 0.75h
Executed: yes (c8ce2a885cc4a5348b3d10cd036c08adbb3898ff; exec run interactive resume 2026-11-10, session sess_dbbda86c)
Authoring claim: 2026-11-10-paused-run-admission-record-starves-exec-lane.md (session sess-zcode-20261110-0635-interactive-admission-starvation)

## Terms

- Outstanding run: an execution run recorded as live for the admission consult — via a claim-live admission record (`docs/tmp/execution-claims/<plan-slug>-admission.json`) or a done-session manifest.
- Claim staleness horizon: an age bound, in hours, on an outstanding run's claim `updated:` timestamp, beyond which the run no longer blocks dispatch. Default 8h (one 5h quota window plus a 3h pause-recovery margin): a run whose claim has not re-stamped within its window's maximum plus margin is abandoned — its carrier failed or its session died. A healthy run re-stamps at every task boundary and a healthy pause ends at its carrier's fire time, inside the horizon.
- Stale-parked verdict: the consult's non-blocking verdict for an outstanding run whose claim-live claim is older than the horizon; the run is named with its age in the consult's stdout output and never treated as admitted-through. Precedence: the existing tool-error class stays first (an unreadable or unparseable manifest is a tool error even when the run's claim is stale); claim staleness is then decided before owned-path evidence, so a stale-parked run is excluded from the blocking loop regardless of its owned-path evidence state; only an unparseable or missing claim timestamp keeps the conservative blocking verdict. Without `--stale-after-hours`, no staleness evaluation happens and supplied claim stamps are inert (default-off, byte-identical).
- Continuation pick: already-covered territory — directive D-17 (`docs/maintenance/operator-directives.md`) records the autopilot doctrine "continue after each completed pick while another eligible pick remains", preserving the five-hour quota pause, the empty-queue stop, and an explicit current stop request; a scheduled payload's own max-1 cap is such an explicit stop and stays preserved. No machinery is built for it here.

## Why

The 2026-11-10 06:35 exec turn witnessed the healthy-pause shape: a paused run with an armed resume carrier (claim updated 04:24Z, carrier 11:00Z) blocks its window by design, and every open candidate behind it. That witnessed case is deliberately NOT what this plan removes — the resume path owns it, and Task 3 files the residual row for it. The horizon removes the sibling abandoned-run shape (carrier failed, session died, claim never re-stamps): structurally identical blocking, no recovery path, unbounded. Separately, the continuation-pick origin row is dispositioned: its remedy already exists as D-17's autopilot doctrine, and the observed early ends came from the operator's own explicit caps, which D-17 preserves by name.

## Gist & Examples

TLDR: give the dispatch admission consult a claim-staleness horizon so abandoned runs stop starving the lane, and disposition the continuation row against D-17, for efficiency.

Before: an abandoned outstanding run blocks every candidate forever behind its untouched claim; the continuation row proposes machinery D-17 already records.

After: an outstanding run whose claim-live claim `updated:` stamp is older than the horizon (default 8h, `--stale-after-hours`) takes the stale-parked verdict — non-blocking, named with its age in stdout, recorded as `admission-stale-parked:<run>` in `decision_reason` — while fresh claims keep their blocking semantics unchanged. The deciding turn derives each claim-live run's stamp by reading the `<plan-slug>.md` `updated:` line in the primary checkout and passes `--outstanding-claim-updated <slug> <ISO>` beside the existing manifest operand together with `--stale-after-hours 8`; an unresolvable claim file means no pair, hence conservative blocking; an unpaired claim stamp is a tool error naming the unmatched id. A plan whose own claim-live run is stale-parked stays skipped from D1 selection (parked for the operator; takeover remains the claim protocol's), so the consult's verdict and the selection never diverge.

Edge cases: an unparseable or missing claim timestamp holds the conservative blocking verdict (staleness never loosens evidence); several stale-parked runs are each named; a stale-parked run's claim, worktree, and branch stay untouched — the consult reads, never disposes, and the strand-drain machinery keeps its own path. Accepted residual (named, bounded): a run revived by operator action during its stale window can intersect a candidate admitted meanwhile; with the default exceeding any healthy pause, revival requires operator action, and the collision is policed by what already exists — the claim protocol's branch-occupant gate (a stale foreign claim on a branch held by an existing worktree refuses the take, so no second executor on the same target) and the landing critical section's serialized squash under the merge landing lock, whose rebase conflict machinery surfaces intersecting-path edits before landing. Two horizons share the claim `updated:` field by design: the guards' fresh-claim skip at the 2h cadence period frees a target-level pick, the admission horizon at 8h frees the lane — a 2–8h-aged claim admits a pick onto a different target while the old run still blocks its own; intended. The horizon reads claim-live operands only; retired-manifest, `children[]`, and pending-landing operands keep the conservative verdict.

## Outcome

An abandoned outstanding run cannot starve the execution lane beyond the staleness horizon; the healthy-pause window stays owned by its resume path with a residual row carrying the resume-first duty; the continuation row closes against D-17 with no new machinery. The stale-parked verdict is a demotion of the existing global blocker's reach for abandoned runs only — net blocker reduction, no new blocking gate; it lands read-only with the registry note's review date owning promotion or removal.

## Task 1

- [ ] Given `--stale-after-hours N` with an outstanding run whose paired `--outstanding-claim-updated ID ISO` stamp is more than N hours old, expects the consult to skip that run as stale-parked: non-blocking exit, the run id and its age named in the stdout output; tests compute both an old stamp (`now − (N+1)h`) and a young stamp (`now − 1h`, blocking preserved) from the real current UTC time so the age comparison itself is witnessed, in the real claim-writer shape `YYYY-MM-DDTHH:MM:SSZ` [class: REPOSITORY_TEST]
- [ ] Given an outstanding run without a paired claim stamp, with an unparseable one, or given an `--outstanding-claim-updated` id matching no outstanding run, expects respectively the existing conservative blocking verdict, the same, and a tool error naming the unmatched id [class: REPOSITORY_TEST]
- [ ] Given a stale-paired run whose manifest is unreadable or unparseable, expects the tool-error class to win (tool errors stay first); and given a stale-paired run with well-formed owned-path evidence, expects exclusion before the blocking loop (precedence pinned by test on both sides) [class: REPOSITORY_TEST]
- [ ] Given no `--stale-after-hours` flag, expects byte-identical existing behavior for every current invocation shape, supplied claim pairs included (inert without the flag; witnessed by the existing suite passing unmodified) [class: REPOSITORY_TEST]
- [ ] Implement the horizon: `--stale-after-hours N` (float hours) and the repeatable `--outstanding-claim-updated ID ISO` pair (`action="append", nargs=2`, keyed by id, not argv order); stale-parked runs are reported before the blocking loop and excluded from it; parse stamps with `datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)` against `datetime.now(timezone.utc)` (the claim writer's `date -u +%Y-%m-%dT%H:%M:%SZ` shape), a failed parse taking the conservative verdict [class: IMPLEMENTATION_REQUIRED]
- [ ] Append the machinery-registry delta note to the `script:dispatch_admission.py` row: incident (the abandoned-run starvation shape this plan's Why names), expected catch (abandoned-run starvation, rare), false-positive cost (a revived run colliding on intersecting paths, policed by the branch-occupant gate and the serialized landing squash, named as the accepted residual), review date (2026-12-10), removal criteria (no true catch by the review date removes the horizon flags) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_dispatch_admission.py scripts/test_claimed_target_skip_and_continue.py scripts/test_done_sweep_gates_lib.py -q` (no new failures; the dispatch_admission consumers' suites stay green), and `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_machinery_inventory.py -q` with exactly the baseline failure (`RealTreeCheck::test_real_tree_checks_green`, the unregistered `scripts/profile_skill_gate_consult.py` regrowth line) unchanged [class: REPOSITORY_TEST]
- [ ] Commit: `scripts: admission claim-staleness horizon (stale-parked verdict)`

Files:
- `scripts/dispatch_admission.py`
- `scripts/test_dispatch_admission.py`
- `scripts/machinery_registry.json`

## Task 2

- [ ] Given the consult's stale-parked verdict, expects both consult homes bound in one pass: the SKILL.md admission-consult invariant names the horizon read (claim-live operands only, default 8h, the deciding turn passing `--stale-after-hours 8` with the derived pairs, the derivation duty: reading the `<plan-slug>.md` `updated:` line in the primary checkout, an unresolvable claim meaning no pair hence conservative blocking, pairs without the flag inert) and the `admission-stale-parked:<run>` decision_reason token; the decisions.md D1 landing-gate paragraph carries the same bound by the same edit (D2's landing mirror inherits by reference, no restatement); the invariant's one clause covers the Step 5 final-slot re-consult passing the same horizon operands; the stale-parked run stays recorded for the operator with its claim, worktree, and branch untouched [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the stale-parked verdict, expects D1's selection bound too: a plan whose own claim-live run is stale-parked stays skipped from selection with the sanctioned must-dispatch exemption reason `admission-stale-parked` (parked for the operator; takeover remains the claim protocol's), so selection and consult never diverge [class: IMPLEMENTATION_REQUIRED]
- [ ] Byte payment, pinned: decisions.md pre-edit 98,250 bytes (already over its 92,132 cap) lands the Task 2 edits at or below that count; SKILL.md pre-edit 39,195 bytes stays under its 44,233 cap; both edits stay inside their sections' existing spans by compression of redundant wording [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: `bash scripts/check_maintenance_pins.sh` with exactly the baseline failure (`PIN FAIL: prompt log has no all-served (stale) entry`) unchanged and no new failures, and `python3 scripts/skill_text_budget.py --check` with no worsened breach for any touched file [class: REPOSITORY_TEST]
- [ ] Commit: `maintenance: bind the stale-parked admission verdict in skill text`

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/decisions.md`

## Task 3

- [ ] Given the continuation-pick origin row (`docs/history/backlog/2026-11-10-exec-continuation-pick-allowance-waste.md`), expects its disposition: deleted in this change as covered by existing machinery — directive D-17 (`docs/maintenance/operator-directives.md`) records the autopilot continuation doctrine and preserves explicit operator stop caps by name; no code or skill text changes [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the witnessed healthy-pause window blockage this plan deliberately leaves to the resume path, expects the residual row `docs/history/backlog/2026-11-10-paused-run-resume-first-duty.md` filed: a survey-time arm proposing (never auto-executing) resuming a paused outstanding run whose quota wall has lifted, its claim/worktree/branch staying owned by its resume path; shapes and guard interactions open to authoring [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: `rg -l 'exec-continuation-pick-allowance-waste' docs/` returns only the deletion commit's own record surfaces (no living pointer), and the new row passes the backlog shape conventions [class: REPOSITORY_TEST]
- [ ] Commit: `backlog: disposition continuation-pick row against D-17 + file resume-first residual`

Files:
- `docs/history/backlog/2026-11-10-exec-continuation-pick-allowance-waste.md`
- `docs/history/backlog/2026-11-10-paused-run-resume-first-duty.md`

## Disposition of migrated backlog items

- docs/history/backlog/2026-11-10-paused-run-admission-record-starves-exec-lane.md: covered by this plan's Tasks 1-2 (the claim-staleness horizon and its skill-text binds); the witnessed healthy-pause window blockage this plan deliberately left to the resume path is carried by the residual row docs/history/backlog/2026-11-10-paused-run-resume-first-duty.md.
- docs/history/backlog/2026-11-10-exec-continuation-pick-allowance-waste.md: deleted by Task 3 — its remedy already exists as directive D-17 (docs/maintenance/operator-directives.md), which records the autopilot continuation doctrine and preserves explicit operator stop caps by name.
