# Operator directives (lane lifecycle home)

This file is the directive-lifecycle home of record for the scheduler loop and every lane it dispatches: an operator directive's issue, lift, supersession, or expiry is valid only when recorded here. Where a carrier prompt, loop directive, or state-file note carries directive text, the payload reads this home at turn start and the home's record wins on conflict; a directive lift or supersession is a one-file commit to this file. Automation payloads lift directive text from this home at dispatch instead of baking aging clauses: the 2026-10-02 carrier clause that outlived two in-chat lifts across 87 armed runs is the anti-shape (witness: the stray-close incident dossier, archived beside its plan at completion).

Record format (one `## D-<n>: <title>` section per directive):

- `issued`: the date the operator issued the directive.
- `status`: active, superseded, lifted, or expired.
- `expiry`: a date or none.
- the directive text, verbatim when operator-issued.
- `scope`: the lanes the directive binds.
- `superseded_by`: the superseding record's id, when not active; second shape admitted 2026-10-10: when the superseder is durable text and not a directive record, the text's homes with the landing plan as witness.
- `witness`: the commit or document that proves issuance.

## D-1: execution-lane state

- issued: 2026-10-03
- status: active
- expiry: none
- scope: all lanes of the maintenance loop
- directive: the execution lane is reopened; plans at the plans root dispatch for execution.
- superseded_by: none (this record supersedes the 2026-10-02 execution-lane closure, which was recorded only in a carrier prompt and the state file's survey notes and outlived two in-chat lifts)
- witness: the day's execution landings on main (27717b6a, cdeed760, 11460cf5, b18a5aba, 6cda8ee2, c0d26b88 and successors) and the dossier's directive history.

## D-2: archiving policy

- issued: 2026-10-03
- status: active
- expiry: none
- scope: every lane and turn that can archive a plan
- directive: archiving plans without any real changes is not allowed unless the operator specifically asks each time. Every ad-hoc fix made during the incident response must be validated or replaced through a proper plan with review, so the situation cannot happen again.
- superseded_by: none
- witness: the dossier's Operator policy section (verbatim) and the maintenance survey's landed-plan disposition fence.

## D-3: loop carrier cadence

- issued: 2026-10-04
- status: active
- expiry: none
- scope: the maintenance loop carrier (the parent automation and every re-arm of it)
- directive: the scheduler carrier runs on a fixed daily cadence at 11:00 local time. Operator wording, 2026-10-04: "also schedule to run with this prompt every day at 11 am". This operator-fixed cadence supersedes the recurring automation recipe's quota-aligned window-chaining form for carrier arming in this repository; the quota leg still governs lane decisions and child fire-time placement inside a turn, and a turn finding the carrier dark re-arms at the daily 11:00 slot.
- superseded_by: none
- witness: automation-7721fe58-fdd0-4bf9-9478-084a17d99932 (recurring, cron 0 11 * * *, enabled, next fire 2026-10-05 11:00 WEST), created in the operator's live session after the loop was found dark. Corrections: 2026-10-10 01:53 WEST — the then-live carrier automation-391f302b (armed 2026-10-04, verified ENABLED 11:02 listing 2026-10-09) found ABSENT from the automation listing (dark since the 2026-10-09 ~18:10 operator owner-deletion window at the latest); the D-11 fire session recorded the re-arm decision state-first, attempted the create once, stood down on emission suppression with no CronDelete primitive (cap-lift delete-plus-create not executable), and parked the recovery: state file `pending_rearm` + payload copy `docs/tmp/future-plan-prompts-2026-10-10.md`; memory note loop-parent-missing-20261010. Re-arm at this 11:00 slot is owed by the next primitive-capable session. Discharged 2026-10-10 07:25 WEST: the operator `$maintenance exec` session deleted its own spawner (D-11 automation-04e82355, lifting the automation-born cap) and created the new carrier; this witness supersedes the armed-automation witness above.

## D-4: 5-49 am authoring cadence

- issued: 2026-10-05
- status: active
- expiry: none
- scope: the authoring lane (the 05:49 automation and every fire of it)
- directive: operator wording, verbatim: "schedule at 5-49 am [$maintenance] Start authoring most urgent issues one by one without stops". The authoring lane runs on a fixed daily cadence at 05:49 local time; within a run it authors, reviews, and lands plans for the most urgent uncovered issues one after another without stopping between them. This is a second fixed cadence parallel to D-3's 11:00 carrier; it supersedes nothing.
- superseded_by: none
- witness: automation-a000835a-090e-48d8-972e-eeff7be9f4a4 (recurring, cron 49 5 * * *; DARK as of 2026-10-10 07:23 WEST listing - the 05:49 fire that morning did not run; restore owed by a fresh/interactive operator chat, one CronCreate, recurring cron 49 5 * * *, authoring-mode payload per the template recipe; earlier armed witness, re-armed 2026-10-09 ~11:22 WEST by the interactive `$maintenance exec` continuation session after the 11:02 CronList survey and state `rearm_note` found the workspace holding only the D-3 carrier — the third one-day disappearance; prior witness automation-15f03d78-5ee8-4e52-9d4f-d9c194f94c87, re-armed 2026-10-08 ~21:45 WEST and gone by 2026-10-09 11:02; earlier witnesses automation-cf16052d-b2c6-4205-b13d-eef5f10fb9a9 (second disappearance, restored 2026-10-08 ~20:30 WEST, gone by ~21:38) and automation-1faf3aae-23ee-4a79-8c53-4d608312f860, dark since 2026-10-07). Corrections: DARK again at the 2026-10-10 ~11:20 WEST listing (fourth disappearance). Re-armed 2026-10-10 ~11:30 WEST by the interactive operator chat per the operator's "restart subagents right now" as automation-9ff284dc-9c10-4777-90a7-fe603f0d6852 (recurring, cron 49 5 * * *, next fire 2026-10-11 05:49 WEST). The restored payload wording deliberately drops the scheduler template's opening line and carries the authoring-child marker ("author a plan"), so the armed record can neither span-match the duplicate-parent tripwire - the standing hypothesis for the repeated disappearances, since a scheduler-shaped prompt beside the armed D-3 parent is exactly the extra ENABLED span match that tripwire and its human-clear delete - nor classify as a both-lane occupant when a fired record sits inside the listing's six-hour window. If this fifth witness also disappears, the next investigation owns the deletion-cause question with the tripwire hypothesis as its first lead. Corrections: fifth disappearance CONFIRMED at the 2026-10-11 02:19 WEST listing (automation-9ff284dc absent; the listing held the D-3 parent automation-3619efc7 ENABLED recurring 11:00, the two lingered-completed 02:18 one-shots, and the 02:25 cycle-11 authoring resume automation-b9ce8ede ENABLED) — recorded by the 02:18 auth-mode scheduler turn; the deletion-cause investigation with the tripwire hypothesis as first lead is now owed; the restore stays owed by a fresh/interactive operator chat per the record above. Corrections: RESTORED 2026-10-14 ~13:42 local by the interactive auth-plans maintenance chat per that clause: automation-c5a96df7-56c8-4892-a09b-5d34cd9ee24b (recurring, cron 49 5 * * *, enabled, next fire 2026-10-15 05:49 local, title 'Authoring lane cadence (D-4)', authoring-mode payload without the scheduler template's opening line per the correction above, create echo verified enabled/active).

## D-5: a due-but-undispatchable audit entry never holds the work lanes

- issued: 2026-10-08
- status: active
- expiry: none
- scope: the maintenance loop's lane decisions (audit-lane and retriage-lane same-turn contention), the registry consult's dispatch discipline, and the Step 1 pending-dispatch reader, in this repository and every lane it dispatches
- pointer: the durable form of this rule is the landed skill text in agents/skills/maintenance/SKILL.md: the Audit-lane same-turn contention and Retriage-lane same-turn contention bullets, the Step 1 pending-dispatch reader's audit-kind validation arm, and the Recurring-task registry consult bullet's ordered fallback legs (added by the audit-lane-slot-take-unblock plan, landed with this record's execution); this record stays the operator will of record and its status stays active.
- directive: operator wording, 2026-10-08 ~20:40 WEST, on the witnessed stall (a due retriage entry consumed the turn's authoring slot while its only carrier, the idle-time queue, refused the dispatch on exhausted quota): "that is a mistake, we shouldn't wait because of that and lose time. create backlog on the main project and find a workaround to continue." Standing rule until superseded: a due audit-kind or retriage-kind registry task takes an authoring or execution lane's slot for a turn ONLY when the audit child actually dispatches that turn (a children[] entry exists). When every dispatch leg is unavailable (idle-time quota exhausted or refused, the host's one-pending-idle-task-per-session limit, or any other carrier refusal), the target retains in `pending_dispatch` with the refusal recorded as its quota signal, and the lane decision proceeds under the normal rules — the authoring lane keeps its selected target and the execution lane keeps its dispatch. A due read alone never spends a work-lane slot. The durable skill-text fix is tracked in `docs/history/backlog/2026-10-08-audit-lane-slot-take-stalls-authoring.md`.
- superseded_by: none
- witness: scheduler state notes 2026-10-08 20:35 (the stall) and backlog row 2026-10-08-audit-lane-slot-take-stalls-authoring.md (commit b3698fb1).

## D-6: executing and authoring lanes continue unless the 5h limit is low

- issued: 2026-10-09
- status: active
- expiry: none
- scope: every scheduler turn and payload session in this repository — the execution and authoring lanes, in-session and dispatched forms
- directive: operator wording, 2026-10-09 ~12:15 WEST, on the witnessed stop (the 11:00 D-3 carrier turn landed its execution child and then ended at the payload's designed stop-after-report boundary while the authoring lane held a fully specified dispatchable target and the primary window had hours of headroom): "You are not supposed to stop the maintenance work executing or authoring unless 5h limit is low. create backlog on the main project in ai-playbook and find a workaround to continue." Standing rule until superseded: a turn does not end at a designed stop boundary while an execution or authoring lane still holds dispatchable work and the 5h limit is not low; the turn continues the lane in-session (the sanctioned workaround legs: the authoring lane's in-session authoring primitive, the execution lane's in-session leg) instead of deferring dispatchable work to the next fixed-cadence fire. The stop condition is the 5h limit being low: the primary-window probe reading at its pause thresholds (the quota leg's decision), at which point the turn records the resume point in the state file and stops. The weekly-secondary binding window's pause stays report-only for same-day resume scheduling (the probe's own reason line) and never by itself stops in-session lane work under this directive. This directive overrides the default quota-defer branches for in-session lane work only; child dispatch scheduling still follows the quota leg.
- superseded_by: none
- witness: backlog row 2026-10-09-scheduler-turn-boundary-stops-live-lanes.md (the durable skill-text fix this record orders, committed with this record) and the same-turn in-session authoring dispatch on the PLAN-PROMPTS entry primary-class-anchors-grammar-drift recorded as this directive's first application.

## D-7: ledger-evidenced closeout-gate demotions are sanctioned ad-hoc work

- issued: 2026-10-09
- status: active
- expiry: none (review for lift when the carrier row's demotion program records completion)
- scope: the ad-hoc arm and every lane executing the "Demotion program (routed 2026-10-09)" section of docs/history/backlog/2026-10-08-done-closeout-ceremony-friction.md
- directive: operator direction, 2026-10-09 session, acting on docs/maintenance/machinery-blocker-audit-2026-10-09.md: "let's act on your suggestions one by one" and "make it implementable for maintenance e.g. in EXEC-PROMPTS.md". Standing rule until superseded or lifted: the demotion program's warning-only posture conversions, its repeatable `--ack` change, and its two named delete candidates (base-branch-amend-guard, per-task-done-subagent) are sanctioned ad-hoc-arm work notwithstanding the Ad-hoc backlog arm eligibility test's guard-bearing-path and machinery-removal denylist, when every changed gate cites a scripts/gate_liveness_ledger.json entry whose incident rows exceed its catch rows (delete candidates: zero live catches with the ledger's cost witness). Every other eligibility clause, the doing-code-review panel, the `Ad-hoc-panel-pass:` receipt with its three-way digest equality, scope containment, the suite gates, and the hygiene scan apply unchanged. No guard or machinery path outside that program section is sanctioned by this record; a ledger-evidenced demotion outside the program needs its own directive.
- superseded_by: none
- witness: docs/maintenance/machinery-blocker-audit-2026-10-09.md (commit 38fd7f176), the program routing commit 9b19d8f77, and the operator's same-session instructions quoted above.

## D-8: review-loop budget policy - delta rounds and blocking-only certification

- issued: 2026-10-09
- status: active
- expiry: none (the durable skill-text fix routes through the review-loop-round-budget plan prompt; this record remains the operator will of record until that text lands, and stands after it as policy of record)
- scope: every plan-review loop in this repository - `review-loop`, `review-plan`, `review-staging`, and execute-plan Phase 3, dispatched and in-session forms
- directive: operator-confirmed execution of docs/maintenance/machinery-blocker-audit-2026-10-09.md suggestion 2 ("the review-loop budget - your #1 rated blocker (25/25)"), confirmed next in the operator session of 2026-10-09. Standing policy until superseded: (1) after the initial full-panel review round, a fold's re-review covers the fold diff in the focused-panel mode; only a semantic plan change reopens a whole-plan panel, decided by the existing delta-classifier arm. (2) The certification round considers blocking findings; non-blocking findings fold into the terminal record's watchlist and never force a re-round. (3) The full-panel round budget is proportional to declared plan complexity: 2 for a plan whose declared execution budget is 2 hours or less, plus 1 full-panel round per additional started 2 hours of declared execution budget (a 3-4 hour plan gets 3, a 5-6 hour plan gets 4; normally executed plans are under 2 hours and the biggest plans execute within 6 hours - a declaration beyond 6 hours is the plan-sizing doctrine's split business, never a bigger review budget, and durations above that in the record were quota-wall and rate-limit stalls, not plan sizes); the declared execution budget is the complexity proxy, never the executed file count (plans declare only their main classes); delta rounds do not consume the budget; the landed round-cap operator gate's ask continues to govern breach (extend, continue, or park). (4) Per-round record validation runs at lint level except at the certification round, which keeps full validation. This policy binds lanes now; the durable skill-text fix is authored from the review-loop-round-budget prompt.
- superseded_by: none
- witness: docs/maintenance/machinery-blocker-audit-2026-10-09.md (commit 38fd7f176), the operator's program confirmations of the 2026-10-09 session, and the landed ask machinery this policy amends (docs/history/plans/completed/2026-10-07-review-round-cap-operator-gate.md).

## D-9: no lane blocks indefinitely on a coordination hold

- issued: 2026-10-09
- status: active
- expiry: none (the durable mechanism - TTL values, liveness probes, report routing - routes through the coordination single-writer plan prompt; this record binds the policy meanwhile)
- scope: every lane and critical section that can refuse on a foreign hold - landings (merge lock, staged-state pre-refusal), execution claims, done locks, manifest recovery - in this repository and every lane it dispatches
- directive: operator-confirmed execution of docs/maintenance/machinery-blocker-audit-2026-10-09.md suggestion 3 (single-writer + TTL coordination), confirmed next in the operator session of 2026-10-09. Standing policy until superseded: a lane never sits blocked without a recorded holder and a next action. Every refusal on a foreign hold waits boundedly first; on expiry it reports the holder's identity and routes onward (re-dispatch, park-for-operator, or skip-with-report). Self-service reclaim of a foreign hold requires a liveness proof that the holder is verifiably dead; a live holder is never reclaimed, only waited on boundedly or reported. No new lock family may be introduced to implement this policy; consolidate into the existing merge-lock and claim contracts.
- superseded_by: none
- witness: docs/maintenance/machinery-blocker-audit-2026-10-09.md (commit 38fd7f176), the lockless staged orphan row (docs/history/backlog/2026-10-09-lockless-staged-landing-orphan-blocks-landers.md), and the operator's program confirmations of the 2026-10-09 session.

## D-10: work-in-progress is checkpointed, and no worktree dies holding owned work

- issued: 2026-10-09
- status: active
- expiry: none (the durable mechanism - checkpoint cadence, commit-marker convention, landing and resume reconciliation - routes through the wip-auto-checkpoint plan prompt; this record binds the policy meanwhile)
- scope: every execution and authoring lane in this repository and every lane it dispatches
- directive: operator-confirmed execution of docs/maintenance/machinery-blocker-audit-2026-10-09.md suggestion 4 (auto-checkpoint work-in-progress), confirmed next in the operator session of 2026-10-09. Standing policy until superseded: a lane commits its uncommitted owned work at every task boundary and at every pause signal (quota pause, budget pause, stand-down, carrier expiry) on its own worktree branch, so a crash or quota wall never strands uncommitted work. No worktree is removed while it holds uncommitted owned files: removal requires an owned-files-clean check whose report records a transfer or commit first. Checkpoint commits are mechanical safety commits and never require operator approval.
- superseded_by: none
- witness: docs/maintenance/machinery-blocker-audit-2026-10-09.md (commit 38fd7f176), the witnessed authoring-plan artifact loss (docs/history/backlog/2026-10-09-authoring-plan-artifact-not-transferred-before-removal.md), and the 2026-10-07/08 quota-wall stall that held uncommitted work-in-progress for roughly eight hours.

## D-11: 1-53 am authoring cadence

- issued: 2026-10-09
- status: active
- expiry: none
- scope: the authoring lane (the 01:53 automation and every fire of it)
- directive: operator wording, verbatim: "schedule at 1-53 am [$maintenance] auth". The authoring lane runs on a fixed daily cadence at 01:53 local time, each fire executing the maintenance skill scheduler turn bound to author mode. This is a third fixed cadence parallel to D-3's 11:00 carrier and D-4's 05:49 authoring carrier; it supersedes nothing.
- superseded_by: none
- witness: automation-04e82355-4a71-4d53-9eb4-26de26028a10 (recurring, cron 53 1 * * *, armed 2026-10-09 ~21:21 WEST by the interactive scheduling ask in a fresh operator chat session). Corrections: fired 2026-10-10 01:53 WEST (first fire); the fire session stood down the automation-primitive surface on emission suppression while re-arming the dark D-3 parent (see D-3 corrections). DELETED 2026-10-10 07:25 WEST by the operator `$maintenance exec` session as the cap-lift step of the D-3 re-arm (the record deleted was this cadence's own carrier; the deletion is witnessed in D-3's corrections). DARK since; the 01:53 cadence's restore is owed by a fresh/interactive operator chat (fresh chats are never capped) - one CronCreate, recurring cron 53 1 * * *, authoring-mode payload per the template recipe in agents/skills/maintenance/zcode.md. Corrections: still DARK at the 2026-10-10 ~11:20 WEST listing; the interactive operator chat executing the operator's "restart subagents right now" could not take this restore - its one armed create was spent on the D-4 re-arm (the automation-born cap holds one armed created automation per session lineage) - so the restore stays owed by the next fresh chat, with the D-4 correction's non-span-matching payload wording as the recommended shape.

## D-12: the anti-growth rule set for skill text (witness budget, admission, append-tax, review lens)

- issued: 2026-10-10
- status: superseded
- expiry: none (the durable forms, the guidelines rules and the review lens, route through the anti-growth-rule-set plan prompt; this record binds the policy meanwhile; the append-tax arm binds in full once the repo-wide byte-budget gate lands and operates as review-time discipline until then)
- scope: every session editing skill text, guidelines, or plans in this repository, and every review panel over such edits
- directive: operator direction of 2026-10-10 ("limit ad hoc growth and trigger refactoring for all the skills, not just this one"), generalizing docs/maintenance/maintenance-skill-refactor-analysis-2026-10-09.md Part 5 to the whole tree. Four standing rules: (a) Witness budget: a fix lands the rule; the incident dossier (witness narrative, rejected alternatives, dates) lives in the backlog row, the analysis doc, or a changelog file; operative skill text cites it in at most one line. (b) Admission: a new top-level arm, section, or field must name the existing section it extends and why that section's predicate cannot absorb the case; when no such section exists, that absence, named, is the design input. (c) Append-tax: once the repo-wide byte-budget gate (the skill_text_budget.py wiring in the routed maintenance-skill-size-refactor plan) lands, a change growing a skill file past its cap deletes equivalent bytes in the same change, the gate's own breach report being the record (no separate growth-debt note surface is added); until that landing, the same discipline applies at review time only. (d) Review lens: plan-review panels treat operative text that grew without a deletion as a finding class, recorded as one line in the existing finding-class documentation, never a new panel duty.
- admission subordination (2026-10-10, reconciled against the audit's own Part 5): every mechanism this rule set spawns lands under the machinery audit's admission protocol (docs/maintenance/machinery-blocker-audit-2026-10-09.md Part 5 item 2) - warning-only or read-only at landing, promotion to blocking only after its first true catch, a stated sunset and review date, and a pre-registered machinery-registry removals row; no incident, no blocking gate. The removal-shaped arms of the child plans (changelog extraction, module split, contract single-sourcing) reduce surfaces and need no admission test. Corrections (2026-10-10, the machinery admission protocol plan): the protocol's durable home is the repository guidelines' Machinery admission protocol section (landed by docs/history/plans/completed/2026-10-10-machinery-admission-protocol.md), which this clause defers to on conflict.
- superseded_by: the repository guidelines' Skill text anti-growth rules section and the Growth balance sentence in agents/skills/review-plan/SKILL.md (landed by docs/history/plans/2026-10-10-anti-growth-rule-set.md; superseded 2026-10-10)
- witness: docs/maintenance/maintenance-skill-refactor-analysis-2026-10-09.md (commit f5df91509; the 35-commit one-shrink ratchet and the 24 percent changelog share), docs/history/backlog/2026-10-04-maintenance-doc-hygiene-review.md (the detect-only enforcement anti-shape this rule set answers).

## D-13: usage-wall restarts follow the quota-wall dispatch doctrine

- issued: 2026-10-10
- status: active
- expiry: none (the doctrine's durable home block is landed; this record stays the operator will of record and stands after it)
- scope: the execution and maintenance lanes in this repository and every payload session they dispatch, in-session and dispatched forms
- directive: restarts remain authorized; the usage-wall class (a provider refusal whose error text names a reset time hours away) follows the quota-wall dispatch doctrine (one hardened probe with the `pre_restart:`/`pre_restart_paths:` pair recorded first, then the timed resume at the recorded reset, or a parked clocked-order when the session cannot arm); every dispatch wave lands a launch ledger line (`launch-wave:`) in the session manifest.
- superseded_by: none (this record supersedes the conversational restart direction named in its witness, which lived only in the operator chat and memory notes, never in this home)
- witness: the superseded conversational restart direction - the 2026-10-07 usage-wall episode's relaunch direction for this repository's lanes, recorded only in the operator chat and the memory notes; the doctrine's home block, agents/skills/execute-plan/SKILL.md Sub-Agent Launch Rules quota-wall dispatch doctrine paragraph; and the landing plan docs/history/plans/2026-10-08-quota-wall-dispatch-doctrine.md.

## D-14: scheduler turns run author mode

- issued: 2026-10-13
- status: superseded
- expiry: 2026-10-15
- scope: the maintenance scheduler turns in this repository - the D-3 11:00 carrier's fires and every scheduler-turn payload session
- directive: operator wording, 2026-10-13 ~21:1x WEST, on the 20:40 scheduler turn planned as dual mode: "change mode to auth plans". Standing rule until superseded: a scheduler turn runs author mode - the authoring lane decides per its rules (in-session or dispatched per the quota leg), and the execution lane resolves to its D3 form with the mode recorded in decision_reason.
- superseded_by: D-15
- witness: the scheduler state file's last_turn.correction of 2026-10-13T21:12 recording the operator order, and the live D-3 carrier automation-71fb6b50-b42b-4310-8db2-ee0f338db710 whose armed prompt carries the same order.

## D-15: scheduler turns run exec mode

- issued: 2026-10-15
- status: superseded
- expiry: 2026-10-15
- scope: the maintenance scheduler turns in this repository - the D-3 11:00 carrier's fires and every scheduler-turn payload session
- directive: operator wording, 2026-10-15: "set it to execute mode and start executing". This was first recorded as a standing exec-mode rule; the operator later clarified that mode is selected per run and the default remains dual.
- superseded_by: D-16
- witness: the operator's 2026-10-15 instruction in the maintenance execution session and the later clarification that default mode is dual and per-run mode may be selected explicitly.

## D-16: maintenance mode defaults to dual with per-run selection

- issued: 2026-10-15
- status: active
- expiry: none
- scope: mode selection for maintenance runs in this repository
- directive: a maintenance run defaults to dual mode. An explicit mode keyword in the current run selects that run's mode: `auth`, `author`, or `authoring` selects author mode; `exec`, `execute`, or `execution` selects exec mode; `both`, `dual`, or alternation wording selects dual mode. A direct manual ruling for the current run also selects its mode. The selection is session-local and does not change the default or later runs. Survey or stand-down wording keeps the maintenance skill's survey-only precedence.
- superseded_by: none
- witness: the operator's 2026-10-15 clarification in the maintenance execution session: "default mode is dueal, and the mode of current run can be set with the key words like auth or exec (as short versions) or their full counterparts as well as manual rulling"; normalized spelling in this record follows the maintenance skill's `dual` term and its existing mode-binding vocabulary.
