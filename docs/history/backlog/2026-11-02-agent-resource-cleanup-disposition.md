# Backlog: cleanup responses lose resource disposition across turns

- **Filed:** 2026-11-02, repeated operator-directed worktree and branch cleanup
- **Status:** covered (docs/history/plans/completed/2026-11-04-agent-resource-cleanup-disposition.md; executed tip 57c2b2158)
- **Workflow:** backlog
- **Priority:** high
- **Consumer urgency:** Consumer projects that run the cleanup and self-heal workflows need the resource-by-resource disposition and recovery handoff; the skills-repo personal priority profile must not park or defer this as formal-hardening for the skills repo alone.
- **Origin class:** consumer-feedback (company)
- **Class:** fix-class
- **Driving force:** efficiency + simplicity
- **Skill/step:** `agents/skills/self-heal/SKILL.md` Recovery 1-4; `agents/skills/execute-plan/SKILL.md` worktree closeout; `agents/skills/done/SKILL.md` final report
- **Catch frequency:** at least two earlier consumer sessions required follow-up: one repeated cleanup correction and one report that self-heal had to be invoked manually; the latter was not yet verified against a full resource disposition. A later plan-execution session adds another self-heal invocation and plan-identity witness below.
- **False-positive cost:** repeated cleanup work and an inaccurate completion impression; deleting a branch with unmerged commits could lose work
- **Review date:** 2026-12-02
- **Dedup probe:** searched open backlog filenames and bodies for worktree cleanup, branch retention, Codex task resources, and cross-turn continuation. `docs/history/backlog/2026-10-13-codex-task-resource-cleanup.md` covers task-attachment correlation and independent Codex-owner evidence; the completed investigation explicitly does not establish a repository cleanup owner for app-managed attachments. `docs/history/backlog/2026-10-11-ad-hoc-worktree-lifecycle-owner-gap.md` is covered by `docs/history/plans/completed/2026-10-24-ad-hoc-worktree-lifecycle-owner-gap.md`, which owns cleanup by one run's orchestrator. `docs/history/backlog/2026-11-02-closeout-branch-retention-base-drift.md` covers a closeout gate's branch-history proof. None covers the assistant losing the user's cleanup scope across turns and failing to give each remaining resource a terminal disposition.
- **Cluster:** `docs/history/backlog/2026-11-02-closeout-branch-retention-base-drift.md` (shared worktree and branch cleanup surface; this row owns cross-turn inventory and disposition, that row owns false-negative landing proof)

## Problem

During a multi-turn cleanup, the assistant removed two quota-related local branch refs, then saw two other registered worktrees and branches still present. The initial inventory counted one and three commits outside `main`; a fresh read while preparing this record counted one and four, with the authoring branch tip changed. The assistant classified the remaining resources as workflow-managed rather than ad-hoc and stopped, relying on a prior summary's caution instead of resolving the current user's cleanup scope. It did not provide a complete per-resource result or continue the owning workflow where authorized. The user had to ask again and request root-cause analysis.

The preservation decision itself was appropriate: both remaining branches had unmerged work, so deleting by name would have risked data loss. The failure was leaving the request without a clear disposition for each resource and implying that the cleanup scope was complete after disposing only part of it. This is distinct from the closeout gate's branch-accounting refusal recorded in the clustered origin.

## Expected

For a cleanup request, inventory the relevant worktree registrations and local branch refs, bind each to its run or claim record, compare its state with the current base, and record one outcome per resource: safely removed and verified, retained with its exact unmerged work and owner, or continued through its already-authorized closeout workflow. Do not report the request complete while in-scope resources remain undisposed. Do not delete active or unmerged work just to satisfy a broad cleanup request; when the user's intent to discard that work is not explicit, preserve it and name the specific decision required.

When resuming a run whose implementation may already have landed, report the exact plan path, the evidence-backed current lifecycle state, the owning worktree and branch, and the remaining completion steps. Distinguish a prior implementation landing from a plan-target change, and cite the commit evidence before describing the run as switched or resumed.

## Suggested direction

Trace how the self-heal, execute-plan, plans, and done workflows carry user cleanup intent and resource identity across turns and runtime boundaries. Determine whether the gap is a missed skill invocation, an unclear resource-inventory handoff, or a missing runtime-specific evidence adapter. Prefer reusing `git worktree list`, branch ancestry, and existing run or claim records over adding a new inventory surface. Keep the shared skill text runtime-neutral; put any verified runtime-specific lookup in its adaptor. Preserve all current artifact-transfer, active-owner, and unmerged-work protections.

## Evidence

- At filing, `git worktree list --porcelain` showed two non-primary worktrees with refs `2026-11-02-maintenance-self-heal-first` and `authoring/2026-11-02-private-project-skills-codex-discovery`.
- The first inventory observed one and three commits outside `main`. The fresh write-window read observed one and four; the separate authoring branch tip changed between reads. This is a time-bounded witness of live work, not stable deletion evidence.
- The project worktree owner's retention contract is recorded in `docs/history/plans/completed/2026-10-24-ad-hoc-worktree-lifecycle-owner-gap.md`; the separate task-resource evidence boundary is recorded in `docs/history/plans/completed/2026-10-14-codex-task-resource-cleanup-evidence-recovery.md`.
- Current shared recovery steps require continuing through the caller's complete terminal conditions (`agents/skills/self-heal/SKILL.md`, Recovery 3-4); the assistant's responses did not do so.
- In a second consumer session, the user asked whether every task-created worktree and branch had been disposed and reported having to invoke self-heal manually. The caller guidance already contains proactive self-heal duties (`agents/skills/using-skills/SKILL.md` and `agents/skills/plans/SKILL.md`), so this witness points to a missed invocation or handoff, not a missing self-heal integration sentence.
- In a 2026-11-04 plan-execution session, the user again had to direct self-heal during recovery and asked whether the run had switched plans. The invocation and archived plan were the same path, `docs/history/plans/2026-11-02-review-freshness-and-code-coverage-gaps.md`; its implementation landing `7d4d3f7a2` predates this run's archive commit `0085b695c` by several hours. This was a same-plan completion after an earlier or parallel implementation, not a plan switch. The assistant's earlier status wording did not make that distinction clear, and the user had to request exact worktree and branch identity.
