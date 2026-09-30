- **Filed:** 2026-09-30
- **Status:** covered (docs/history/plans/2026-10-01-done-boundary-receipt-and-closeout-gate-sweep.md)
- **Workflow:** done (learn Step 1.8)
- **Priority:** high
- **Origin class:** self-serving
- **Driving force:** reliability
- **Class:** fix-class

Cluster: docs/history/backlog/2026-09-28-done-lock-one-shot-reclaim-releases-documentation.md
Cluster: docs/history/backlog/2026-09-28-write-manifest-legacy-foreign-bulk-load.md
Cluster: docs/history/backlog/2026-09-29-done-sweep-consumes-run-tmp-before-worktree-migration.md
Cluster: docs/history/backlog/2026-09-29-em-dash-gate-run-backlog-candidates.md
Cluster: docs/history/backlog/2026-09-29-emit-roundtrip-vt-ff-unreachability.md
Cluster: docs/history/backlog/2026-09-29-p79-gates-no-r1-fix-behavior-pins.md
Cluster: docs/history/backlog/2026-09-29-step1-ledger-tmp-dir-loss-residual.md
Cluster: docs/history/backlog/2026-09-30-plan-archive-cited-review-receipts.md

# Execution ceremony prevention: enforce the execute-plan skill mechanically

Witnesses 2026-09-30 (13:54 and 14:06 local, landings 21178a3f and 66b91d23): two peer sessions executed plans and archived them to completed/ while violating the execute-plan skill's completion ceremony. Directive of record (operator, 2026-09-30): plan execution must always follow the execute-plan skill. These items make the skill's ceremony mechanically enforced, so a session that skips it cannot present as done. Each item is independently actionable; split on pickup. The after-the-fact verification and checkbox backfill landed as a38ff7de.

## 1. Archive-checkbox gate (high)

An archive landing that moves a plan from the plans root into a completed archive must fail when the plan bytes carry unchecked `- [ ]` task boxes, unless the run records an explicit exemption. Witness: both plans archived with 0/10 and 0/12 boxes checked. Home: the done-sweep gates (a sibling of plans-archive-twin in `done_sweep_gates.sh` pre-commit, which already sees the rename union), so the check is one gate, not prose. Driving force: automation (the gate closes the exact hole twice witnessed on 2026-09-30). Backfill-after-verification (a38ff7de shape) is the sanctioned recovery for already-archived stragglers.

## 2. Archived-plan review-coverage hole (high)

The pre-docs plan-readiness gate prunes archived plans from its deliverable lines, so the landing that archives a plan escapes review-coverage verification entirely. Witness: commit messages claiming "exec r1 ready=yes" for both plans with no execution review staging doc or `.stats.json` sidecar anywhere under docs/reviews (only the authoring-round plan-review r1 records exist). Extend the gate: a plan archived within the session window still requires a review record binding its final bytes (or a recorded exemption in the run manifest). Driving force: reliability (a claimed review round must be evidenced on disk).

## 3. Unfinalized done-run manifests must surface (medium)

Witness: run-manifest-20260930T125655Z-681b1860d42e sits complete:false since 13:56 local (the recovery-baseline executor's done run) and nothing consumed the signal. The done skill's Step 0 already reports interrupted runs, but the report is passive. Make it loud and bounded: Step 0 must name every complete:false manifest in the repo window and require an explicit disposition (adopt via --adopt, or record a disown with reason) before writing the new run's manifest. Driving force: reliability (an unfinalized run is indistinguishable from a crashed one until someone reads the file).

## 4. Queue enumeration must count the plans root (medium)

Witness: the 13:37 scheduler turn recorded the exec queue empty while two freshly-landed plans sat at the plans root unexecuted (landed 12:48 and 13:16). The queue-drain enumeration derives the queue from memory and claim files; it must also enumerate unarchived plan files at the resolved plans_dir, excluding those holding fresh foreign execution claims (the claim duty landed in 21178a3f makes that checkable), so a plan on disk is never invisible to the lane. Driving force: automation (disk is the source of truth, not session memory).

## 5. Mechanical stale-base landing guard (high)

Witness: the p102 squash landing (2bcc562d) was built from a stale base and silently reverted four peer commits; the tree-identical gate passed vacuously because it compared the branch against the regressed main. The landing tails' "integrate the current default tip before building the squash" prose needs a mechanical check in the landing critical section: before any CAS ref move, assert the source tree's merge-base with the base branch equals the base branch's current tip (or that the base tip's tree is an ancestor of the source tree), and refuse the landing otherwise. Driving force: reliability (peer work destroyed without a trace).

## 6. Payload-level skill binding for plan execution (medium)

The operator directive: plan execution must always follow the execute-plan skill. The maintenance payload blueprints and the queue-drain chaining paragraph carry no binding line, so a session can pick up a plan and improvise the ceremony (witnessed twice on 2026-09-30: no per-task done commits, no checkbox marking, no staged review). Add an explicit binding to the payload templates: every plan execution runs through the execute-plan skill (Step 0.5 gate, per-task implement and done commits, per-task checkbox marking, review staging under docs/reviews, archive ceremony), and the execution-claim file records the skill path plus the run's session identity so guards can verify the binding at claim time. Driving force: reliability (the skill is the ceremony; skipping it silently is what items 1-3 catch after the fact).

Witness append (2026-09-30 ~22:30, done-run 0d scan over 224 archived plans): five more same-day plans cite authoring review records that exist under docs/reviews in zero rounds, same shape as the survey-anchored witness: 2026-09-30-execute-plan-zero-allowed-path-refuse-at-create (r3), 2026-09-30-hygiene-residue-masked-ticket-sweep (r2), 2026-09-30-java-review-fqcn-coverage (r1), 2026-09-30-review-staging-sidecar-kind-validation (r1), plus survey-anchored (r1). The staging transfer-out skip is therefore batch-wide, not a one-off; items 1-3 and the p98 gate arms own the fix.
