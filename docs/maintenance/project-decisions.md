# Project decisions

Architectural and workflow decisions for the ai-playbook instruction repository. Newest entries append at the bottom.

## ADR-0001: Immutable completed history and non-mirror context

Completed implementation plans, completed review digests, and non-mirror context under `docs/history/context/` (and legacy `docs/context/`) are immutable historical records of considerations at the time. Do not annotate or rewrite them to reinterpret process outcomes after the fact. Allowed edits only after explicit user confirmation for factual corruption (for example leaked secrets or broken paths). Confluence mirrors under `docs/history/context/confluence/` may refresh to match the wiki; that sync is not a license to revise completed plans or non-mirror context.

**Considered options:** leave only one prior completed plan untouched; annotate completed plans for honesty; freeze the entire context tree including Confluence mirrors.

**Consequences:** prevention work is forward-looking (skills and guidelines). Completed plans are context, not templates for copying rollout checklist shapes into new plans. New plans classify candidates as repository implementation, external prerequisites, or release gates. Only repository implementation becomes an executable plan task by default. A release-gate exception requires a current bound receipt (exact confirmation text or stable message reference, specific checklist item, target or environment, confirmation time or session), a meaningful `why executable now`, and observable `completion evidence` in the plan file. External prerequisites are never exception-admissible. `done` Confluence mirror sync remains valid. Future readers must not expect archives to be patched when process rules change.

## ADR-0002: Phase 3 churn control (cap-5 budget, reflection stop, two-class backlog default)

Decided 2026-09-01 by the user after an execute-plan run kept reviewing past the expected five-review stop: production converged, but focused post-fix panels kept finding "fresh-looking" residuals (sibling docs restating an already-fixed rule; sibling tests missing a witness another test already pins), and each cheap fix manufactured another review round until the user stopped the session manually. Decisions: (1) execute-plan Phase 3 counts every review round, full-panel and focused alike, and stops for user direction before any further round once the total reaches 5; the existing five-full-panel budget stays unchanged alongside it. (2) During Phase 3 addressing, exactly two residual classes are backlog-by-default instead of fixed-inline: sibling-doc restatements (canonical home already correct) and duplicate unit witnesses (another passing test pins the invariant); the fix-everything default of `receiving-review` stands for everything else, including cheap YAGNI/rename Lows. (3) The deferred classes resolve through the convergence machinery of the sibling backlog items: one fan-out finding naming a canonical home with peer pointers, and one family-completeness item per false-green family.

**Considered options:** total cap of 7 or no total cap (relying on qualitative reflection triggers); the five-review-cap backlog item's full exit-policy table (also auto-deferring YAGNI/rename Lows and ticket-tag drift); cap checkpoint only (no class-based default).

**Consequences:** `receiving-review`'s "address every finding by default" gains a scoped Phase 3 exception whose two classes are defined in the glossary (sibling-doc restatement, duplicate unit witness), not a general weakening. Once the cap fires, each further round needs user direction unless the user gives a standing "continue until clean" instruction for that loop. Harness rules stay tool-agnostic and enforceable on hosts that cannot launch sub-agents. The harness-side rules of the single-SOT and false-green backlog items are implemented in this change; the doc-hierarchy and plans-authoring rows remain with their owning skills.

## ADR-0003: Document lifecycle binds service repos by schema and this repo by convention

Decided 2026-09-08 during the grill of backlog item `2026-09-08-document-ownership-and-archive-lifecycle`. The document ownership/immutability lifecycle (living SOT vs completed history artifact, registry, freeze transition) is part of the doc-hierarchy schema, so company service repos bind automatically once migration-complete. The ai-playbook instruction repo itself is outside the migration-complete signal (the verify script fatals on it), but adopts the same lifecycle by convention for its own `docs/` tree without requiring the signal, extending ADR-0001 rather than defining a third scope class.

**Considered options:** service-repos-only (leaves the churn that motivated the backlog legal in this repo); require a new "adopted" signal for non-service repos (third scope class, more machinery).

**Consequences:** doc-hierarchy-family wording must distinguish schema binding (service repos, signal-gated) from convention adoption (this repo). Validators and registry tooling must work on any repo with resolved facts paths, not depend on the migration-complete signal.

**Update 2026-09-13:** the ownership registry appends one filesystem-derivable registry row per completed document by design (identity derives from the filename per the registry header scheme); this per-row append is an accepted ADR-0003 cost, not an automation gap. The derive-by-default tier, where tooling would derive and append rows from the filesystem itself, was considered and declined.
