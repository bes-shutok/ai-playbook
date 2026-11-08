# Plan: Harvest-window rollout export for post-mortem evidence

Backlog origin: docs/history/backlog/2026-11-05-session-rollout-retention-postmortem-evidence.md
Driving force: automation
Plan review record: the staging series .ai-playbook/reviews/2026-11-07-plan-review-session-rollout-retention-postmortem-evidence-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 0.5h total, largest task 0.5h
Executed: no
Authoring claim: 2026-11-05-session-rollout-retention-postmortem-evidence.md (session sess_002a6379-efed-4b97-ae0a-d5cf37006674)

## Terms

- Harvest duty: the maintenance loop's Per-cycle harvest duty in `agents/skills/maintenance/decisions.md`, the bullet beginning `Per-cycle harvest duty (added 2026-09-30`; learn plus one investigate pass run before the next cycle's selection.
- Harvest pass: one run of the Per-cycle harvest duty over a completed cycle; the duty is the contract, the pass is its execution.
- Read legs: the harvest duty's learn and investigate legs, the legs that read cycle evidence.
- Rollout: the runtime's per-session conversation transcript file under the runtime rollout directory (`model-io-<session-id>.jsonl` on this host's ZCode runtime, purged within hours of session end).
- Durable session store: the runtime's SQLite session store of persisted transcript events, never deleted; its locator is the pinned tilde-form literal in the proxy-locator bullet of `agents/skills/maintenance/zcode.md`, which the duty text references and never restates.
- Facts-document key: a configuration key in the project facts document (`.ai-playbook/facts.md`) whose value, when set, overrides the inline fallback default (the skill design guidelines' Configuration pattern).
- Tilde-form default: the fallback locator literal beginning `~/` carried inside the duty sentence itself, the repository's pinned-locator form that never commits a resolved absolute home path.
- Overlay pin: a pinned locator literal carried in the runtime overlay file `agents/skills/maintenance/zcode.md`, the rollout-locator home this plan rejected on byte-cap grounds.
- Cycle outputs: the durable records a completed maintenance cycle produced (its commits, authoring and execution claims, and scheduler-state records), which name the session ids the harvest legs read.
- Evidence dir: the harvest pass's per-run directory under `docs/tmp/` (gitignored) where exported rollouts land, one session-id-named copy per session.
- Telemetry-only: the residual evidence posture for a session whose conversation evidence no surviving surface carries: the rollout is purged and the durable session store's persisted rows do not answer the question; structured telemetry (host logs, the runtime task index) and repository receipts are what remain.
- Evidence-class contract: the duty text naming which evidence classes a harvest may assume (telemetry, repository receipts), which it must export while it can (conversation rollouts), and which persisted surface it falls back to (the durable session store).
- Arm: one of the three retention alternatives the origin row enumerates: (a) raise the runtime rollout retention window, (b) add the bounded harvest-window export step (selected by this plan), (c) accept telemetry-only as the documented harvest contract.
- Origin row: docs/history/backlog/2026-11-05-session-rollout-retention-postmortem-evidence.md, the backlog row this plan promotes (the plan's Backlog origin).
- Stranded-record attribution: the post-mortem duty that attributes a stranded or interrupted run to its originating session; it reads the run's final report, whose rollout transcript the runtime had already purged for the 2026-11-04 run.
- Pins suite: `scripts/check_maintenance_pins.sh`, the repository's literal-grep pin suite over maintenance and skill text.

## Why

The runtime purges conversation rollouts within hours of session end, so a harvest pass running the day after finds only structured telemetry, and post-mortems cannot answer conversation-level questions. The stranded-record attribution for the 2026-11-04 run could not check the originating run's final report for exactly this reason. The repo-owned half of the fix is the harvest duty's own evidence-class contract: export what the harvest is about to read while it still exists.

## Gist & Examples

TLDR: the maintenance harvest duty gains a bounded rollout-export step, so the loop preserves the conversation evidence it is about to read before the runtime purges it; driving force automation.

Before: a harvest pass reads whatever rollouts survive. An authoring-time probe on 2026-11-07 found 3 files in the runtime rollout directory (about 14 MB, all currently-live sessions), while same-day earlier windows were already purged; every purged session degrades to telemetry-only silently, which is how the 2026-11-04 stranded-record attribution lost the run's final report.

After: the duty first exports the surviving rollouts of exactly the sessions the cycle's outputs name into the evidence dir, records per-session export outcome (exported, or, when already purged, the durable session store's persisted rows, and telemetry-only only when neither answers), and states which evidence classes a harvest may assume and which it must export while it can. A next-day harvest can name, from the workflow text alone, what it will and will not find.

## Outcome

The maintenance harvest duty preserves the conversation evidence of the sessions it reads, before runtime GC removes it.

- A harvest pass starts by exporting the surviving rollouts of the cycle's named sessions into the evidence dir, so its read legs work from exported copies instead of racing the runtime's purge window.
- Sessions whose rollouts are already purged fall back to the durable session store, and are recorded telemetry-only in the harvest's outputs only when neither surface carries the answer, so the degraded posture is visible instead of silent.
- The duty text states the evidence-class contract, so any harvest run can name which evidence classes it will and will not find, from the workflow text alone.

Gate delta: none - the selected arm (b) adds no refusal class, hard gate, fence, protocol layer, schema field, or dispatch-pausing condition; it inserts one bounded evidence-export step inside the existing Per-cycle harvest duty paragraph, warning-shaped by construction (export what survives, record what does not, never block the harvest on the export), the no-blocking-lane posture the repository guidelines' Machinery admission protocol requires, with the origin row as the named incident.

## Assumptions

- assume retention arm (b), the bounded harvest-window export step, is the selected arm; basis: the origin row's 2026-11-06 harvest append ("a bounded harvest-window export is the repo-owned half of lookup regardless of the retention-window decision"), arm (c) telemetry-only being rejected on the origin row's own witness (its Observed bullet records that the stranded-record attribution for the 2026-11-04 21:48 run could not be checked against that run's final report because the report's session transcript no longer exists, a conversation-level question structured telemetry cannot answer), and arm (a) a runtime retention raise living outside this repository (rollout GC is runtime-side configuration this repo's execution cannot land or verify). Simpler-design comparison: the simplest viable alternative is (c), pure duty text with no export mechanism; rejected because the origin's expected outcome wants the stranded-record attribution checkable, which telemetry-only cannot deliver.
- assume the export lands under `docs/tmp/` in the harvest's per-run evidence dir; basis: `docs/tmp/` is the repository's gitignored scratch home whose budget the docs/tmp retention redesign machinery already governs (docs/history/backlog/2026-11-02-docs-tmp-retention-redesign-strand-resumption.md), and the origin row's scope bounds the export to the sessions a harvest will actually read so it does not recreate the docs/tmp accumulation problem.
- assume the rollout locator resolves through a facts-document key with an inline tilde-form fallback default carried inside the duty sentence itself; basis: the skill design guidelines' Configuration (from facts document) pattern (key, purpose, fallback defaults), the repository's sanctioned pinned-locator literal being the tilde form (the proxy-locator precedent in `agents/skills/maintenance/zcode.md`), and `agents/skills/maintenance/zcode.md` already standing over its byte cap at authoring (119,065 bytes against the 116,647-byte cap in `scripts/skill_text_budget_caps.json`), so an overlay pin would need an equivalent-byte deletion in the same change. Simpler-design comparison: the overlay pin in `zcode.md` is the alternative; rejected because growing an already-breaching file requires the same-change deletion arm, a larger scope than the key-with-inline-default form.
- assume the single operative surface is the Per-cycle harvest duty paragraph in `agents/skills/maintenance/decisions.md`; basis: that bullet is the duty's definition of record, the maintenance SKILL.md Step 3 line loads `decisions.md` before dispatch decisions, and the SKILL.md Integration Points line only describes the duty without restating its steps.
- assume the export set is exactly the session ids the cycle's outputs name; basis: the origin row's bound ("bounded to the sessions a harvest will actually read", the row's Observed vs expected arm (b) sentence) and the duty's own read scope (the cycle's session logs and outputs).
- assume the decay claim is probe-backed as of authoring: a 2026-11-07 probe of the runtime rollout directory found 3 files (about 14 MB, all currently-live sessions) while same-day earlier windows were already purged; basis: authoring-time probe recorded in this plan's Gist and consistent with the origin row's Evidence section.
- assume no new pin is added for the edited paragraph; basis: the existing pins-suite pin greps the duty bullet's opening literal, which this plan keeps byte-identical, and the machinery admission protocol prices checked-set growth, so an unwitnessed second pin is not added.

Decision points requiring a grill: retention arm among (a) runtime retention raise, (b) bounded harvest-window export, (c) telemetry-only contract: arm (b) selected; source: origin row's 2026-11-06 harvest append (quoted verbatim in the row's Evidence section) and the row's Suspected root area line naming the repo-owned half; date: 2026-11-07; affected section: Outcome and Task 1; export target home: docs/tmp per-run evidence dir; source: the docs/tmp retention strand row (docs/history/backlog/2026-11-02-docs-tmp-retention-redesign-strand-resumption.md) and the origin row's bounded-scope sentence; date: 2026-11-07; affected section: Task 1; rollout locator home: facts-document key with the inline tilde-form fallback default in the duty sentence; source: the skill design guidelines' Configuration (from facts document) rule and `agents/skills/maintenance/zcode.md`'s byte-cap state; date: 2026-11-07; affected section: Task 1; conversation-evidence source: export-window rollouts plus the durable session store named in the evidence-class contract, rejecting the rollouts-only inventory; source: the proxy-locator bullet's never-deleted rows verified against the host store (4,715 sessions persisted against 3 rollout files surviving at authoring); date: 2026-11-07; affected section: Terms and Task 1; durable-store locator: by reference to the zcode.md proxy-locator pin, rejecting a second facts key that would duplicate the pinned literal into a second operative file; source: the zcode.md proxy-locator bullet and this plan's Maintainability criterion; date: 2026-11-08; affected section: Terms and Task 1.

## Standing constraints

- Skill-text anti-growth: the incident story stays in the origin row; the operative duty paragraph cites it in at most one line.
- The duty bullet's opening literal `Per-cycle harvest duty (added 2026-09-30` stays byte-identical (the pins suite greps it).
- No gate, validator, lock, ledger, or required ceremony is added by any task.
- Byte budget: Task 1's added operative text stays within `agents/skills/maintenance/decisions.md`'s remaining byte-cap headroom (92,132-byte cap in `scripts/skill_text_budget_caps.json`; 982 bytes of headroom at authoring, 91,150 bytes on disk, verified with `python3 scripts/skill_text_budget.py --check`); the added operative text targets at most 900 bytes, so the no-compression path is the planned one (the store is referenced, not restated, which keeps the addition short), and if the cap would otherwise be passed the same change compresses equivalent bytes inside the duty bullet's own existing text (pay-for-growth in the same change; the gate is advisory, the discipline is not).

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the amended duty paragraph names the export order (before the read legs), the bounded export set (cycle-outputs-named sessions), the rollout locator resolution chain (facts-document key, then the inline tilde-form default), the evidence dir home, and the telemetry-only fallback, with no ambiguous ordering or unresolvable locator.
- Maintainability: one operative surface (the decisions.md duty paragraph), one origin-citation line, no duplicated contract text in other maintenance files.
- Anti-growth balance: the paragraph's growth is bounded to the step's operative sentences within the file's byte-cap headroom; no incident narrative enters the skill text.

**Done when:**
- `agents/skills/maintenance/decisions.md`'s Per-cycle harvest duty bullet carries the export step, the rollout locator resolution chain, the evidence-class contract, and the telemetry-only recording duty, with the bullet's opening literal byte-identical.
- The duty-bullet pin holds: `grep -qF 'Per-cycle harvest duty (added 2026-09-30' agents/skills/maintenance/decisions.md` exits 0 after the edit. The full pins suite currently exits 1 repo-wide on two pre-existing failures this plan does not touch: the all-served stale-entry pin, failing on two stale prompt-log entries (`doing-code-review-staging-doc-scaffold-pointer` and `handoff-reconciler-date-stripped-plan-slug`, each origin row deleted while its entry stayed served; re-measured with `python3 scripts/check_prompt_log_origins.py` at the r4 fold), routed through the maintenance monitor's rolling prompt log duties, and the execute-plan resumed-lane arm-3 takeover pin (observed on main at the r4 rebase); both are out of this plan's scope, never this plan's landing.
- `python3 scripts/plan_readiness.py docs/history/plans/2026-11-07-session-rollout-retention-postmortem-evidence.md --pre-round` exits 0.
- `bash scripts/check-no-em-dash.sh added-lines --base main` exits 0 over the added lines.
- The public hygiene scan exits 0.
- `python3 scripts/skill_text_budget.py --check` reports no decisions.md breach beyond the authoring-time advisory state (the file stays within its 92,132-byte cap, or the same change compressed equivalent bytes to keep it there).

**Ship when:**
- A next-day harvest pass can name, from the workflow text alone, which evidence classes it will and will not find (the origin row's Ship-when condition; evidence owner: the maintenance loop's next harvest turn; closure: the harvest's outputs name the classes).
- The runtime-side retention-window decision (arm (a)) remains an operator environment decision outside this repository, tracked by the origin row and its cluster, and is not blocked by this plan [class: OPERATIONS_FOLLOW_UP]; evidence owner: the operator's runtime environment; closure: an operator retention decision recorded beside the origin row's cluster.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/decisions.md` (Task 1)
- `scripts/skill_text_budget.py` (review-only): the byte-budget check this plan's Done-when and Task 1 run, never an edit target

**Tests:**

None; the pins suite is validation-only for this plan and no pin is added.

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/SKILL.md`; the Integration Points line describes the harvest duty by reference and the duty paragraph owns the semantics; edit it only if a finding shows it now contradicts the amended duty text.
- `scripts/check_maintenance_pins.sh`; no new pin is added; the existing duty-bullet pin must stay green unchanged.
- `agents/skills/maintenance/zcode.md`; already over its byte cap at authoring, so the rollout locator resolves through the facts-key with the inline tilde-form default instead of an overlay pin (see Assumptions); edit it only if a finding shows the duty text contradicts the overlay's locator conventions.
- `docs/history/backlog/PLAN-PROMPTS.md`; the pre-existing stale entries named in Done when are the maintenance monitor's prune surface, never this landing's side effect (the log's prune rule reserves removals to a landing's own dispatch entry and its listed collateral).
- Runtime rollout GC configuration; outside this repository (the origin row's suspected root area notes the same).

## Validation Commands

```bash
bash scripts/check_maintenance_pins.sh
python3 scripts/plan_readiness.py docs/history/plans/2026-11-07-session-rollout-retention-postmortem-evidence.md --pre-round
bash scripts/check-no-em-dash.sh added-lines --base main
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
python3 scripts/skill_text_budget.py --check
```

### Task 1: Add the bounded rollout-export step to the Per-cycle harvest duty

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/decisions.md`

- [ ] The Per-cycle harvest duty bullet gains the export step, inserted before the duty's learn and investigate legs: at harvest start, for each session the cycle's outputs name, copy the surviving rollout files at the resolved locator into the evidence dir (one session-id-named copy per session, most-recent-first when the surviving set needs ordering), and run the duty's read legs against the exported copies where a leg would otherwise read a live rollout. [class: IMPLEMENTATION_REQUIRED]
- [ ] The export step resolves the rollout locator as: the facts document's rollout-directory key when set, else the tilde-form default literal carried inside the duty sentence itself (the repository's sanctioned pinned-locator form); given no locator resolves and a session's rollout is thereby unexportable, expects that session to record telemetry-only (never an improvised host path in operative text). [class: IMPLEMENTATION_REQUIRED]
- [ ] The duty bullet records the degraded posture: a session whose rollout is already purged when the harvest runs falls back to the durable session store's persisted rows, and is recorded telemetry-only in the harvest's outputs only when neither surface carries the answer; given a cycle naming a session whose rollout the runtime has already purged, expects the harvest to consult the store's persisted rows and its outputs to record the outcome, never fail or block. [class: IMPLEMENTATION_REQUIRED]
- [ ] The duty bullet states the evidence-class contract compactly: conversation rollouts are export-while-it-can and never assumable; the durable session store is the persisted conversation-evidence source of record for already-purged sessions (located by reference to the zcode.md proxy-locator pin); structured telemetry (host logs, the runtime task index) and repository receipts are assumable; telemetry-only is the residual when none of these carries the answer. [class: IMPLEMENTATION_REQUIRED]
- [ ] The export step stays bounded and warning-shaped: only cycle-outputs-named sessions, the evidence dir lives under `docs/tmp/` where the docs/tmp retention machinery governs its lifetime, the harvest never blocks on the export, and no gate, validator, lock, ledger, or required ceremony is added. [class: IMPLEMENTATION_REQUIRED]
- [ ] Anti-growth and pin safety: the bullet's opening literal `Per-cycle harvest duty (added 2026-09-30` is byte-identical before and after the edit, the origin row is cited in at most one line inside the bullet, and no other maintenance file restates the export contract. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect pass: `grep -qF 'Per-cycle harvest duty (added 2026-09-30' agents/skills/maintenance/decisions.md` exits 0 after the edit; the full `bash scripts/check_maintenance_pins.sh` reports no PIN FAIL beyond the two pre-existing failures recorded in Done when. [class: REPOSITORY_TEST]
- [ ] Run → expect pass: `python3 scripts/plan_readiness.py docs/history/plans/2026-11-07-session-rollout-retention-postmortem-evidence.md --pre-round` exits 0; `bash scripts/check-no-em-dash.sh added-lines --base main` exits 0; the public hygiene scan exits 0. [class: REPOSITORY_TEST]
- [ ] Run → expect pass: `python3 scripts/skill_text_budget.py --check` reports no decisions.md breach beyond the authoring-time advisory state (the Standing constraints byte budget holds). [class: REPOSITORY_TEST]
- [ ] Commit: `maintenance: harvest duty exports cycle sessions' rollouts before reading them`. [class: IMPLEMENTATION_REQUIRED]
