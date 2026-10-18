# Machinery Blocker Audit — plan authoring & execution pipeline

**Date:** 2026-10-09. **Question:** how do the existing machinery and scripts actually block or slow plan authoring and execution; which blockers matter most; why did so many accumulate; and what changes stop the accumulation — specifically for the maintenance loop that authors plans without a human in the loop.

**Sources swept for this audit** (all repository-relative):

- `docs/history/backlog/` — 107 open rows read and classified (subdir counts: completed 4, deferred 13, rejected 135).
- `docs/history/plans/` — 374 plans (360 completed, 10 rejected, 1 deferred, 3 open); all 10 rejection records read.
- `docs/history/review-certs/` — 36 certificates, certification round extracted from each.
- `docs/history/reviews/` — 721 plan-review series, max round per series.
- `docs/history/review-store-disposition-ledger.md` — disposition of 606 findings across 207 series.
- `docs/history/metrics/` — the single checkpoint log (a telemetry-absence record).
- `docs/maintenance/ai-harness-friction-audit.md` — prior baseline (2026-08-25..09-23 window).
- Persistent memory corpus (817 topic files + 15 feedback files) — every recorded blocking incident mined.
- Machinery self-inventory: `machinery_registry.json` (112 entries) and `gate_liveness_ledger.json` (15 guards).
- Skill and script payload sizes (`wc -c` / line counts across `agents/skills/` and `scripts/`).

**Rating scheme.** Impact = typical cost of one incident (1 = minutes, 5 = lane-days or irrecoverable work). Frequency = observed incident rate over 2026-09-15..10-09 (1 = once, 5 = near-daily). Priority = Impact x Frequency (max 25). Evidence links are given per family; ratings are incident-derived estimates, not telemetry — the repo currently cannot measure policy stops (the prior friction audit reached the same conclusion).

---

## Part 1 — Rated blocker inventory

### Summary matrix

| # | Blocker family | Primary components | Impact | Freq | Priority | Trend |
|---|---|---|---|---|---|---|
| 1 | Review-loop non-convergence | review-plan, review-loop, review-staging | 5 | 5 | **25** | rising |
| 2 | Peer coordination: claims, locks, staged orphans, duplicate work | execution-claims, done locks, shared primary index | 4 | 4 | **16** | rising |
| 3 | Done-closeout gate stack | done, sweep gates, reverse-squash, archive ceremony | 3 | 5 | **15** | rising |
| 4 | Contract drift: machinery refuses its own certified outputs | plans ↔ execute-plan seeding, scheduler state, staging validator | 5 | 3 | **15** | rising |
| 5 | Worktree lifecycle & recovery gaps; RED-on-main integrity guards | execute-plan runtime, pins suite, regressions suite | 4 | 3 | **12** | rising |
| 6 | Automation carrier infrastructure | D-3/D-4/D-5 carriers, CronCreate lineage cap, turn boundary | 3 | 4 | **12** | steady |
| 7 | Quota / model-capacity walls | provider quota, 1302 rate limits, dead quota probe | 4 | 3 | **12** | steady |
| 8 | Per-plan ceremony tax | skill-gate marker, em-dash fixer, 9-shape validation, ledgers | 2 | 5 | **10** | steady |
| 9 | Operator-judgment gaps in autonomous sessions | survey carrier, over-execution beyond mandate | 4 | 2 | **8** | steady |
| 10 | State drift & replayed-context false alarms | memory/session state, post-landing reads | 2 | 3 | **6** | steady |

### Backlog composition (107 open rows)

| Blocker class | Rows | Share |
|---|---:|---:|
| Machinery contract/recovery gap | 51 | 48% |
| State/doc drift | 18 | 17% |
| Gate false-positive or deadlock | 14 | 13% |
| Ceremony/process overhead | 10 | 9% |
| Race/serialization bug | 7 | 7% |
| Infra (quota/automation/model) | 4 | 4% |
| Genuine product bug unrelated to machinery | 3 | 3% |

Rows opened per day: 10-04: 5, 10-05: 17, 10-06: 10, 10-07: 18, 10-08: 32, 10-09: 25 — 74% of the open backlog was filed in the last two days of the window. `done-closeout` is the noisiest component (22 rows), then `execute-plan` (15).

### Family evidence

**1. Review-loop non-convergence (25).** Of 36 review certificates, only 8 certified at r2 or lower; the certified-plan median is 4 rounds, with r7 (3 plans), r8, r9, r10, r11, and r14 each represented; the raw reviews corpus (721 series) has a max of r21. Recent runaways: two-mode-loop-policy ran r1–r11 with the operator diagnosing the fold process itself as the defect source at r10; the project-strictness plan consumed six rounds, was r6-certified, then rejected by the operator and never executed; docs-branch-scope-and-tmp-retention certified at r14. Open row `2026-10-09-execute-plan-review-loop-blocker-convergence` states execution is blocked by review churn that never converges. Each round is a fresh worker panel; the rcgb execution paid ~16h wall / ~90–100M tokens with three rate-limit restarts. Fold-introduced blockers repeatedly dominated fresh rounds until the minimal-fold doctrine (10-07) and round-cap operator gate (10-06) landed — both operator-imposed after runaways "nobody asked" about.

**2. Peer coordination (16).** Witnessed: a duplicate execution that completed all 3 tasks plus a review panel before being thrown away as superseded (peer never wrote its claim, 10-07); a takeover that collided with a live peer mid-commit (10-08); a lockless 32-path staged index in the shared primary checkout that blocked every compliant lander overnight and stranded an authoring claim for about a day (10-08/09, row `2026-10-09-lockless-staged-landing-orphan-blocks-landers`); a stale-base squash that deleted 11 foreign paths off the branch — third witness of the clobber class (10-02). The execution-claim gateway itself exists because one pre-gateway collision cost 130 lane-minutes. Every one of these is a patch on the previous patch; there is no single-writer or bounded-wait doctrine underneath.

**3. Done-closeout gate stack (15).** 22 open rows. The repo's own `gate_liveness_ledger.json` shows the post-landing staging gate with 6 false-blocking incidents against 2 true catches; the reverse-squash guard's single `--ack` slot refused benign rewordings twice; the archive ceremony refused a deliberately rejected plan over 36 unchecked boxes; the docs-branch witness blocked a user-directed commit for 11 files the user said to skip; the undisposed-interrupted refusal misread a live peer manifest as dead. A done run died mid-run leaving an interrupted manifest; a successor dispatch was parked by closeout friction and only consumed the next day. The operator-directed row `2026-10-08-done-closeout-ceremony-friction` already concludes: "Do not retain a check only because it already exists, and do not add another ledger, gate, or recovery ceremony to manage the simplification."

**4. Contract drift (15).** The machinery now refuses outputs its own upstream stages certify: the plans skill documents a Primary-class-anchors shape that execution seeding rejects, dead-ending a certified, review-passed plan (`2026-10-09-primary-class-anchors-grammar-drift`); review-staging soft-mode printed `OUTCOME: pass` on a FAIL run, corrupting the certification boundary; scheduler-state decision fields drifted shape and the reader refused the state file, blocking a carrier turn; a peer's `reviews_dir` facts flip failed the readiness oracle for every open plan at once, zeroing the execution lane (10-06). Two landed plans prescribed replacing the same certification span with no ordering fence, so the second executor hit a stale anchor. Root shape: contracts are written twice (prose in one skill, checks in another) with no shared source and no paired conformance test.

**5. Worktree lifecycle & recovery gaps (12).** Worktree removal destroyed an uncommitted authoring plan (witnessed artifact loss, `2026-10-09-authoring-plan-artifact-not-transferred-before-removal`); a restored worktree cannot resume because its claim collides; reclaim-after-terminal-worker strands the run "in a state no autonomous path exits"; the 23:32 quota wall left a mid-execution worktree with uncommitted WIP stalled ~8h. Meanwhile two integrity guards are themselves RED on main — the origin-HEAD pin span and the parallel-work regressions suite (2 of 3 tests failing at tip, witnessed on two commits) — and a RED guard on the default branch blocks every pins-gated landing repo-wide. The guards that gate landings do not pass their own gate.

**6. Automation carrier infrastructure (12).** The D-4 authoring carrier disappeared three times in ~36 hours across three sessions, mechanism unexplained; each restoration is a CronList verification + create + witness commit + hygiene pass, plus a standing "re-check CronList every turn" tax. The CronList attractor produced 14 numbered occurrences over six days (sessions listing 3–40 times instead of acting), twice needed operator interjection, once left the whole loop dark ~1.5h, and took eight days to fix properly. CronCreate's lineage cap refuses automation-bound sessions, so budget-pause mid-run cannot always re-arm. The scheduler payload's stop-after-report boundary idles healthy, dispatchable lanes for up to a day (operator directive D-6, `2026-10-09-scheduler-turn-boundary-stops-live-lanes`), and due-but-undispatchable audit entries held work lanes until the operator issued the D-5 slot doctrine.

**7. Quota / capacity walls (12).** The 10-07 23:32 wall stalled an execution ~8h with uncommitted WIP and blocked its declared dependents; the same wall forced certification relaunches (two relaunch automations created then deleted), stop-fail-closed the PDS run ~74 min before reset, and deferred a landing. The ZCode quota probe was dead on arrival (fails open — a whole guardrails plan built around a probe that never fires), so nothing protected lanes until the quota-wall dispatch doctrine. Rate-limit (1302) restarts re-pay cold starts: three inside the 16h rcgb run. External cause, but the machinery amplifies it: no auto-checkpoint of WIP, fail-closed defers, and pause/resume protocols that themselves spawn rows.

**8. Per-plan ceremony tax (10).** Before any plan-file write: authoring claim, skill-gate marker, em-dash fixer pass. Every review record: nine-shape validation via an 18,722-line validator. Closeout: two lock families, a write-manifest sweep that once refused 4,508 unclassified candidates, pre-docs and pre-commit gate batteries, ledgers (owned-commits, gate-liveness, a 677-line disposition ledger that records 606 findings with 0 "fixed-here"). Two machinery pieces have zero catches ever (`base-branch-amend-guard`, and `per-task-done-subagent` at ~2.5M tokens per multi-task run). Friction-audit mining subagents cost 700k–950k tokens each. Individually small; multiplied by every plan and every round, this is the fixed cost that makes each of families 1–4 expensive.

**9. Operator-judgment gaps (8).** A survey carrier archived six unexecuted plans as "strays" (operator restored all six, ordered root-cause fixing, and mandated that even incident fixes go through plan-grade review); a session auto-started executing a plan beyond its mandate and had to be stood down with claim, worktree, and manifest rolled back. The pattern: autonomy is granted at judgment-heavy moments (what to archive, when to execute) while the operator is absent, then the operator is pulled in for judgment-light janitorial work (adjudicating an orphaned staged index, breaking a gate deadlock).

**10. State drift & replayed-context false alarms (6).** "Replayed context looks like drift after a landing" is twice-witnessed; one session nearly filed two false clobber/staleness rows in a single turn. A quota-pause divergence was recorded in memory as EXECUTED when only authored (corrected a day later from disk+git). Low direct cost so far, but it is the designated false-positive generator for incident adjudication.

### Counter-evidence — gates that did pay rent

Not all machinery is ceremony. The ledger records true catches: a fabricated CAS digest refused; a stale-base landing refused that would have deleted four peer paths; duplicate executions prevented post-gateway; the write-manifest claim-or-foreign check caught unclassified corpora twice; the review-staging shape validator has multiple real catches. The recommendation below is not "remove gates"; it is "gates must pay rent, and rent is audited."

---

## Part 2 — The most blocking issues

Ranked, with the single change that would relieve each most:

1. **Review-loop non-convergence.** It is the largest token/time sink and manufactures downstream blockers: folds introduce new blockers (r8–r10 of the r11 plan were dominated by fold-introduced findings), more rounds mean more drift surface, more ceremony executions, more quota exposure. Single change: default round budget of 2 with fold-diff-only re-review (review the delta, not a fresh whole-plan panel), escalation to the operator at breach instead of silent cap closure.
2. **Done-closeout gate stack.** Highest-frequency blocker; the repo's own ledger proves several gates block more than they catch. Single change: execute the operator-directed ceremony-friction row — demote to warning (or delete) every gate with incidents > catches, and reduce closeout to verify/land/note.
3. **Coordination primitives.** Duplicated executions and lockless orphans destroy or freeze whole lanes. Single change: one rule — a lane exists only while it holds the claim file, and a blocked lander waits with a TTL then auto-reports, never indefinitely; replace the lock lattice with that single invariant plus reclaim-on-TTL.
4. **Contract drift.** The only family that dead-ends already-certified work. Single change: single-source each cross-skill contract (grammars, state shapes, path conventions) in one machine-readable place consumed by both sides, with one paired conformance test per contract.

---

## Part 3 — Why so many blockers accumulated

1. **Fail-closed design with no bounded exit.** Nearly every gate fails closed, and many have no self-service adjudication, no bounded wait, no expiry. Fail-closed plus no exit equals deadlock, and deadlock equals an operator page or a stalled lane. Witnessed verbatim: "no bounded wait and no self-service adjudication path"; "stranding the run in a state no autonomous path exits"; gate-removal's "unremediable refuse deadlock."
2. **Incident-driven accretion: every failure begets a gate.** The machinery registry holds 112 entries, all dispositioned "keep": 58 kept by user-decision assertion, 47 by red-test (which proves the code runs, not that the guard ever caught anything), and exactly 1 by direct incident evidence. Blockers spawn backlog rows, rows spawn plans, plans add machinery, machinery mis-fires and spawns rows. That ratchet is visible in the numbers: ~95–97% of all 374 plans target the pipeline's own machinery; ~97% of open backlog rows are machinery-internal; the row creation rate accelerated to 25–32/day.
3. **Human in the loop at the wrong moments.** The operator is absent for scope and simplicity judgment (where the model overengineering shows: a plan r6-certified then rejected as over-derived machinery; a mechanism killed on "operator economics"; 8 of 10 rejected plans rejected as not plan-worthy), yet is summoned for judgment-light adjudications (orphaned staged index, gate deadlock, lane unblocking). The loop inverted: expensive judgments are automated, cheap ones escalate.
4. **Concurrency patched, not designed.** Peer sessions, carriers, claims, per-repo and per-worktree lock families, staged-index sharing — each collision produced one more patch (claim gateway after a 130-minute collision; TOCTOU and claim-race rows), so the same failure class recurred three times (the clobber family) because there is no single-writer invariant underneath.
5. **Reviewer and reviewed drift together.** The review machinery is itself the largest, fastest-moving machinery; record-format validation is expensive per round, and folds under review pressure introduce the next round's blockers. The review-staging validator has blocked closeouts on corruption of its own machinery's records.
6. **No cost feedback into authoring.** Execution budgets only arrived 10-05; the one plan created to instrument scope-complexity caps produced no measurements (its own review ran to r7); the 16h/100M-token execution was noticed only after the fact. The pipeline optimizes for certainty, not value per token, and nothing in the authoring loop sees cost.
7. **Ad-hoc fixes without cross-skill consideration — the operator's hypothesis, confirmed.** The shortest path out of a blocked lane has repeatedly been patching the gate right there, without checking the contract on the other side; 51 of 107 open rows are contract/recovery gaps, and the operator has twice had to order root-cause discipline (after the stray-close incident, and in the ceremony-friction row's "do not add another ledger... to manage the simplification").

---

## Part 4 — How to remove or minimize the machinery

Guiding principle: **gates must pay rent** — keep only machinery with a witnessed true catch, demote the rest to warnings, and make every new piece prove itself before it can block.

Program, in dependency order:

1. **Closeout reset (fastest relief, highest frequency).** For each closeout gate, compare incidents vs catches from `gate_liveness_ledger.json`; incidents > catches → warning-only immediately, delete after 30 clean days. Targets named by evidence: post-landing staging gate (6:2), reverse-squash single-ack (false-positive pattern witnessed), archive-ceremony checkbox refusal (witnessed), docs-branch witness for user-directed commits (witnessed), undisposed-interrupted refusal (witnessed misread). Closeout becomes: verify, land, note — anything else is opt-in. This executes the already-filed operator directive rather than adding machinery.
2. **Review-loop budget (largest cost).** Default 2 rounds; re-review scope is the fold diff, not the whole plan; blocking findings only for certification; cap breach escalates to the operator with a one-page summary instead of silently burning rounds (the round-cap operator gate already exists — give it teeth as the default path, not an exception). Demote the nine-shape record validation to a lint-level preflight for non-certification rounds.
3. **Single-writer + TTL coordination.** One invariant: a lane acts only while it holds its claim; anything that blocks a lander waits with a TTL, then reclaims or reports — never blocks indefinitely. Retire redundant lock families once the invariant is enforced at claim creation. The lockless-staged-orphan and duplicate-execution classes both die under this rule.
4. **Auto-checkpoint WIP.** Commit work-in-progress at every task boundary (and on any pause signal) so quota walls and crashes never strand uncommitted work — this alone removes the 8h-stall damage class and the destroyed-authoring-artifact class. Worktree removal requires an owned-files-clean check with report, never silent removal.
5. **Contract single-sourcing.** Extract each cross-skill contract (anchors grammar, state-file shapes, sidecar digests, path conventions) into one machine-readable definition consumed by both producer and checker skills, with one paired conformance test per contract pair. This converts drift rows (18 open) from "discover at execution" to "fail in CI."
6. **RED-on-main as a landing-queue precondition.** Fix the origin-HEAD pin span and the parallel-work regressions suite before any further machinery landings; a guard that is red on the default branch must demote itself to warning automatically rather than block the world.
7. **Deletion targets with zero or negative rent** (evidence above): `base-branch-amend-guard` (zero catches), `per-task-done-subagent` (~2.5M tokens/run, no catches), the disposition-ledger workflow (606 findings, 0 fixed-here — record only accepted risks going forward, one line each), friction-audit mining subagents (replace with the per-landing one-line telemetry below).
8. **Per-landing cost telemetry.** One JSON line per landing: plan id, wall hours, tokens, review rounds, gate refusals, operator interventions. Ship the minimal version of the instrumentation plan that already exists; review monthly and delete the bottom-quartile machinery by catch count. This is the feedback loop whose absence caused root cause 6.
   > Provenance note (2026-10-10, the covering plan `docs/history/plans/2026-10-10-landing-cost-telemetry.md` Task 3): this item's review contract's operative input home is the friction-audit task body (`docs/maintenance/recurring-tasks/friction-audit.md`), which reads `docs/history/metrics/landing-costs.jsonl` as its measured input and enforces the writer duty's sunset; the task body is what a recurring turn loads, this audit doc is a dated snapshot, and the item's historical text above is never rewritten.

Expected effect: of the ~2.15 MB of pipeline skill prose and ~84k lines of runtime scripts, the families above touch the majority of the closeout and coordination bulk; the intent is not a smaller codebase per se but a strictly smaller blocking surface — every remaining blocking gate backed by a witnessed catch.

---

## Part 5 — Stopping the accumulation: fixing the maintenance authoring loop

The maintenance loop's objective function is backlog-row elimination. Rows are therefore its revenue, and the loop farms them: machinery-internal rows generate plans, plans generate machinery, machinery generates misfire rows. Five changes convert it from ratchet to thermostat:

1. **Change the admission test for maintenance-dispatched plans.** A plan must cite an operator-value outcome — a user-facing fix, a feature, or a measured cost reduction — not a machinery-internal gap. Machinery-internal rows route to a quarantine list that the operator reviews weekly in one batch decision (one decision disposes many rows), instead of auto-authoring each into a plan. This directly attacks the 95–97% self-reference ratio.
2. **Machinery admission gate — the one meta-gate worth adding.** Any plan that adds a gate, validator, lock, ledger, or required ceremony must state: the concrete incident it prevents (with a link), expected catch frequency, false-positive cost, and a sunset/review date. No incident, no blocking gate — new machinery lands warning-only and is promoted only after its first true catch. This is the structural fix for "ad-hoc fixes without overarching consideration": it forces the cross-skill cost question at authoring time, when it is cheap.
3. **Deletion is a first-class plan outcome.** Every machinery plan must name what it removes or simplifies; net-machinery-growth plans require operator approval. The operator's own moves (rejecting the strictness plan, filing the machinery-elimination pass, the ceremony-friction row) already define this policy — encode it in the maintenance dispatch templates rather than re-deciding it per incident.
4. **Bounded repair instead of repair-by-patch.** When a gate blocks a lane, the allowed responses are: bounded retry, skip-with-report, or park-for-operator. Editing a gate or validator mid-lane to unblock oneself is forbidden without a plan. Symmetrically, make skip-with-report cheap (a one-line ledger note) so agents are never incentivized to invent workarounds — the 51 contract-gap rows are the residue of workarounds meeting each other.
5. **Insert the human at three leverage points, and only those.** (a) Plan scope: before any review rounds run, the operator sees a five-line gist plus budget and approves or refers — this prevents the r6-certified-then-rejected waste, which is the most expensive rejection class. (b) Round-cap or budget breach: surface to the operator instead of auto-continuing. (c) New blocking machinery: the admission gate in (2) is operator-approved by construction. Everything else stays autonomous — the goal is not more supervision, it is supervision at the moments where judgment is expensive and automation currently guesses.

**Success measures** (reviewable in 30 days): open machinery-internal backlog rows trending down from 104; median certification rounds at or below 2; zero closeout gates with incidents > catches in blocking mode; every blocking gate in `gate_liveness_ledger.json` carrying a last-true-catch date; per-landing telemetry present for every new landing.

---

## Limits of this audit

Ratings are incident-derived from backlog rows, review certificates, and memory records — the repo cannot yet measure policy stops directly (the prior friction audit, `docs/maintenance/ai-harness-friction-audit.md`, reached the same conclusion for its window). Incident records skew toward recent, dramatic events; quiet ceremony cost is likely undercounted, and gate true-catches may be under-recorded where no ledger row was written. The per-landing telemetry in Part 4 item 8 is the fix for both biases and should supersede this audit's estimates once it accumulates.

---

## Reconciliation (2026-10-10)

The operator's follow-on programs are children of this audit's Parts 4 and 5 and are bound by its own admission protocol (Part 5 item 2). Reconciled on 2026-10-10 after the operator caught the initial routing landing new machinery without it:

- The repo-wide byte-budget gate (`skill_text_budget.py`) lands **warning-only** with its admission test stated in the script header (incident: the 35-commit one-shrink ratchet and the roughly 89K-token per-turn doctrine load, `docs/maintenance/maintenance-skill-refactor-analysis-2026-10-09.md`), promoted to blocking exit 1 only after its first true catch, with a stated sunset and a pre-registered machinery-registry removals row.
- The duplication report (`skill_text_duplication.py`) lands read-only with the same stated incident, sunset, and removals row; it never blocks.
- The append-tax discipline lives inside the budget gate's breach report rather than a new growth-debt note ledger; the review lens is one line in the existing finding-class documentation, never a new panel duty.
- The removal-shaped arms (changelog extraction, module split, template split, contract single-sourcing) reduce surfaces and need no admission test.

Governing record: directive D-12's admission subordination clause (`docs/maintenance/operator-directives.md`); the amended plan entries sit at the top three positions of `docs/history/backlog/PLAN-PROMPTS.md`.
