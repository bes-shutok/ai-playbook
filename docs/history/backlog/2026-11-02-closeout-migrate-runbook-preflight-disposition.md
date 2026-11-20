## closeout-migrate-runbook-preflight-disposition

Added: 2026-11-02, doing-code-review r3 panel over the closeout-migrate-baseline-tracked-clobber ad-hoc landing (finding F7, documentation#missing-closeout-runbook-preflight-disposition)

Cluster: scripts/worktree_closeout_migrate.py (baseline clobber guards; family record: the EXEC-PROMPTS-PRUNE receipt at the top of docs/history/backlog/EXEC-PROMPTS.md)

Status: covered (docs/history/plans/2026-11-05-closeout-migrate-supplemental-inventory-and-guard-residuals.md)
Origin class: self-serving
Skill/step: `agents/skills/execute-plan/worktree-first.md`, Transfer-out-and-deletion implementation
Driving force: efficiency + simplicity
Catch frequency: one witnessed closeout refusal; further frequency is unknown
False-positive cost: a run retains its source worktree and branch for manual recovery; an overbroad transfer could overwrite or misclassify foreign artifacts
Consumer urgency: consumer projects using the shared closeout workflow need a sanctioned recovery for out-of-scope artifacts; the skills-repo priority profile must not defer the fix as repo-only formal hardening
Environment: Codex, ai-playbook repository skill copies, 2026-11-05
Dedup probe: searched open worktree-closeout and migration rows; `docs/history/backlog/2026-10-13-worktree-closeout-claims-sidecar-siblings.md` is covered and owns claimed record sidecars, while the self-heal recovery sibling owns landing proof. This row extends the existing runbook-preflight item with the distinct configured-home inventory gap.

Witness: .ai-playbook/reviews/2026-11-02-closeout-migrate-baseline-tracked-clobber-code-review-r3.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-finally-guard-exception-containment.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-guard-ambient-git-env-filter.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-guard-failure-manifest-trace.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-nested-repo-toplevel-boundary.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-preflight-direction-overbreadth.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-preflight-git-probe-n-plus-one.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-prelock-head-window.md

The closeout runbook paragraph (agents/skills/execute-plan/worktree-first.md:79, the Transfer-out-and-deletion implementation) documents the migrate lock, the removal gate, and the baseline/skip rules, but not this landing's primary operator-visible behavior: the exit-2 baseline clobber pre-flight refusal (its named paths and its narrow-dirs-and-recapture remedy, documented only in the refusal's own stderr text) or the prevented_clobbers manifest section.

Scope arm: add the exit-2 disposition (narrow the capture dirs to untracked session surfaces and re-capture, with the why) and the prevented_clobbers section to the paragraph.

## Update (2026-11-05, resumed worktree closeout)

The same transfer-out paragraph left a second recovery gap: the baseline migrator enumerates only the configured reviews, tmp, metrics, and review-certs homes, while the operator closeout requires every tracked, untracked, and ignored source item to have a verified destination before removal. This run found ignored artifacts outside those homes. The scoped `--inventory` route is explicitly baseline-less, so it could not be used as a supplemental transfer while the canonical baseline existed. Recovery initially treated that tool constraint as a prohibition on any transfer, then found the operator closeout's separate transfer-or-land step and copied a bounded explicit list to unique destinations with digest checks.

Expected: the canonical closeout text gives one safe, repeatable supplemental-transfer route for a finite inventory outside the configured homes when a baseline is present, preserving foreign destination bytes and recording verification in an existing run record. Do not broaden the baseline capture to unrelated caches or turn the baseline-less scoped route into a second baseline mode.

Evidence: `agents/skills/execute-plan/worktree-first.md`, Transfer-out-and-deletion implementation and the referenced `done` Operator branch closeout sequence; the source artifact set included foreign review records, generated caches, and the migration manifest itself.

Reaffirmed priority: high. The gap retained a completed run's worktree and branch until a manual recovery was derived, and the shared closeout path serves consumer projects.
