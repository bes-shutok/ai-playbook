# Backlog: plans authoring in a company primary-placement project never offers the branch choice and never checkpoints the plan

- **Filed:** 2026-11-15, interactive plans authoring run in a company project that declares primary placement (user-corrected mid-run)
- **Status:** covered (docs/history/plans/2026-11-15-plans-authoring-primary-company-branch-and-checkpoint-enforcement.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** consumer-feedback (company)
- **Class:** fence-class (lost-evidence risk: the authored plan stayed untracked through two review rounds and certification, and every gate still passed)
- **Driving force:** reliability
- **Skill/step:** `agents/skills/plans/phase-0-placement.md` (Phase 0 intro paragraph; Step 0.1; the Authoring checkpoint duty paragraph); `agents/skills/execute-plan/worktree-first.md` (Project worktree policy paragraph, company task-branch arm, and lifecycle step 3); `scripts/plan_readiness.py` (`--pre-round` and full mode); `scripts/plan_delta_classifier.py` (`--since`)
- **Cluster:** EXEC-PROMPTS receipt certification-time-checkpoint-skip-observability (covered 2026-11-16, ad-hoc landing; same family: checkpoint duties that a run can skip with no observation surface)
- **Cluster:** docs/history/backlog/2026-11-15-plans-run-skipped-branch-choice-and-checkpoint-invocation.md (the agent-side half of this incident)

## Observed versus expected

Observed. A plans authoring session in a company-profile project whose facts declare `worktree_policy = "primary"` ran start to finish on the base branch of the primary checkout:

1. No branch choice was offered. The policy paragraph gives a company-profile primary-placement run a per-run operator choice (keep the current branch, or create a named task branch from the current HEAD) and fixes a default only for unattended runs ("an unattended run with no directive keeps the current branch by default"). An interactive run with no directive is not covered, and nothing in the plans skill's Phase 0 steps asks the operator.
2. No `wip:` checkpoint commit was made. The Phase 0 Authoring checkpoint duty says the session commits the plan file under the `wip:` marker at every authored plan write and verifies a round-start anchor commit before the first review round. The session never did, and the plan file stayed untracked.

Consequences witnessed in that one run:

- `python3 scripts/plan_readiness.py --pre-round <plan>` exited 0 with the plan untracked.
- After a `ready=yes` review round, `python3 scripts/plan_readiness.py <plan>` also exited 0 with the plan untracked (`readiness OK: latest review of these plan bytes is ready`).
- `scripts/plan_delta_classifier.py` needs a start commit (`--since`), so none of the review-driven folds could be classified. Every fold fell back to the unclassified default, which forced an extra delta review round (about 13 minutes of reviewer time) that a classified, fully exempt fold would not have needed for the cosmetic findings.
- The round-close certification seal could not be recorded: the seal binds to a commit blob and no commit existed. Both staging validators warned `corrections grading degraded to the exact-match digest rule: no certification seal entry resolves`.

Expected. For an interactive company-profile primary-placement run, Phase 0 asks for the branch choice (or records the default it applied, with the evidence that no directive existed) before any plan write, and the checkpoint duty is a visible step whose absence a gate reports.

## Reproduction evidence (trimmed)

- Facts keys in the consumer project: `worktree_policy = "primary"`, `project_type = "company"`, a recorded base branch; current branch equal to the base branch at start.
- Order of events: Phase 0 claim written, closeout baseline capture attempted (failed on a missing facts key, skip note recorded), plan written, `--pre-round` gate passed, two review rounds ran, full gate passed, `git status --short` showed only the untracked plan file.
- `plan_readiness.py` full mode, final line: `OUTCOME: pass`, with the plan untracked.
- Validator warning text (both rounds): `corrections grading degraded to the exact-match digest rule: no certification seal entry resolves for round N`.

## Environment

Interactive Claude Code session, 2026-11-15, skills read from the deployed home copies (the runtime symlinks to the skills repo checkout). Consumer project profile: company, primary placement.

## Suspected root area

1. **Discoverability.** Phase 0 mentions the company task-branch arm only as a parenthetical ("beside a company-profile run's recorded task branch"). The mechanism lives in one very long paragraph in a different module, so a reader following Phase 0's own steps never reaches the choice.
2. **Undefined interactive default.** The policy paragraph defines the no-directive default only for unattended runs. The interactive case has no rule, so an agent can default silently.
3. **Checkpoint duty is prose, not a step.** The Authoring checkpoint duty is one sentence inside a long Phase 0 paragraph and has no checklist entry, no announce line, and no gate.
4. **No mechanical check.** Neither `--pre-round` nor full readiness mode checks that the plan path is tracked or that a round-start anchor commit exists, so the run's omission is invisible to every gate.
5. **Classifier dependency.** The classifier's only input shape is `--since <commit>`; an untracked plan has no usable before side, so the failure mode is silent loss of the zero-round path, not a refusal.

## Outcome sought

- Phase 0 renders the branch choice as a named step with the interactive rule stated next to it (ask when no directive exists, or record the applied default and why), pointing at the single home of the policy paragraph.
- The checkpoint duty becomes a Phase 0 and pre-first-round step with an announce line.
- A readiness warning (or refusal in full mode before a certification seal is requested) names an untracked plan or a missing round-start anchor commit, so the omission is observable.
- The classifier reports "plan has no start commit" as a distinct tool-error reason instead of leaving the caller to infer it.

## Rejected alternatives

- Make the agent remember harder: rejected, the same omission class was already filed for the certification-time checkpoint and a memory-only fix has no observation surface.
- Auto-create the branch without asking: rejected, the policy paragraph makes the choice the operator's, and a branch-name collision with foreign work must re-ask.
- Refuse authoring on the base branch in primary placement: rejected, keep-current is a valid operator choice and the personal and pet arms require the base branch.
