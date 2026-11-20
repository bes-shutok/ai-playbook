# Plan: Track private project skills in Codex discovery path

Backlog origin: docs/history/backlog/2026-11-02-private-project-skills-codex-discovery.md
Driving force: external (consumer-reported defect: a private Codex project's tracked skills were invisible to Codex project skill discovery until moved; source and verified before/after evidence recorded in the backlog row, 2026-11-02)
Plan review record: the staging series .ai-playbook/reviews/2026-11-02-plan-review-private-project-skills-codex-discovery-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 0.5h total, largest task 0.5h
Authoring claim: 2026-11-02-private-project-skills-codex-discovery.md (session sess_f8a947bf-fffd-4eb7-94c7-195302796345)

## Terms

- Project-local skills: skill packages tracked inside a consumer project's own repository (not the shared `skills_repo_path` registry), discovered by agents that scan a project skill directory.
- Codex project skill discovery: Codex desktop's scan of a project repository for skill directories; the observed discovery path for project-local skills is `.agents/skills/`.
- `skills_repo_path`: the user-facts key resolving the shared skill catalog (typically `agents/skills/` in the skills repository); the canonical source to edit first for shared skills.
- Shared catalog: the `skills_repo_path` skill tree, mirrored to agent-specific install paths; distinct from project-local skills.
- Private project: a consumer's own non-public repository that tracks its skills in-repo rather than in the shared catalog.
- Pet hygiene rules: the public-hygiene conventions this repository already publishes for public pet projects (no personal paths, no sensitive content); untouched by this plan.

## Why

The authoring guidance describes project-local skills only as an optional mirror convention and leaves their tracked path undefined. A private Codex project tracked skills at `agents/skills/`; Codex did not discover them, and the fix was to move them to `.agents/skills/` and track that subtree. Without documented guidance, every private Codex project repeats this mismatch.

## Gist & Examples

TLDR: document `.agents/skills/` as the tracked project-local skill path for private Codex projects, so authored skills are discoverable; driving force: external (consumer-reported, verified).

**Before (today):** An author follows the skill guidance, creates a project skill at `agents/skills/standup-report/` in a private project repository, and commits it. Codex desktop does not list the skill; calls from the Codex UI fail. The author must discover by trial that Codex scans `.agents/skills/`, move the package, and adjust ignore rules so the subtree is tracked while unrelated `.agents/` runtime state stays ignored.

**After (this plan):** The same author reads the location guidance in `how-to-write-skills` and learns: for a private project whose agent discovers project skills (Codex desktop verified 2026-11-02), track skills at `.agents/skills/<name>/`; keep `.gitignore` entries narrowed so `.agents/skills/` is tracked while other `.agents/` runtime state (caches, scratch, tool state) stays ignored; migrate an existing `agents/skills/<name>/` package with `git mv` plus the ignore update; and verify discovery per agent, since non-Codex agents may scan different project paths. The shared `skills_repo_path` registry guidance is unchanged and the two homes stay distinct.

**Edge cases:** a repository that uses both the shared catalog and project-local skills (the guidance states how the two homes relate and that they are distinct); an agent that does not support project skill directories (the guidance keeps the existing "only when your agent supports a project skill directory" gate); public projects and public pet hygiene rules (unchanged; the new guidance is additive and does not relax them).

## Outcome

Skill authors get one documented, verified convention for where tracked project-local skills live in private Codex projects, so skills are discoverable on first authoring instead of after a debugging session.

- The location guidance in `how-to-write-skills` defines `.agents/skills/` as the tracked project-local skill path for agents that discover project skills there, with the Codex evidence cited.
- Ignore guidance tells authors to track `.agents/skills/` while unrelated `.agents/` runtime state stays ignored.
- Safe migration from `agents/skills/` (move plus ignore update) and the supported-agent verification caveat are documented.
- The distinction from the shared `skills_repo_path` registry stays explicit, and public project and pet hygiene rules are untouched.

Gate delta: none (prose-only guidance change in one skill file; no gate, validator, classifier, ledger, refusal surface, or schema field added, removed, or changed)

## Assumptions

- assume `.agents/skills/` is the correct tracked project-local skill path for Codex; basis: the consumer project's verified before/after skill listing recorded in the backlog row (2026-11-02, Codex desktop, repository source).
- assume the change is guidance text only, in `agents/skills/how-to-write-skills/SKILL.md`; basis: the item's Location and evidence section names those sections and its Suggested change names no script, test, or registry surface.
- assume no executable verification of third-party agent behavior is possible in this repository; basis: discovery behavior is agent-owned; the plan documents the convention and the per-agent verification caveat instead of adding a probe.
Decision points requiring a grill: guidance placement (extend the existing "Wrong Location" section versus a new reference file): extended the existing section as the simpler design, the section is the location-guidance home and no second home is warranted; source: simpler-design comparison against `references/` layout, 2026-11-02, affected sections: Task 1; ignore-guidance scope (name concrete ignore examples versus generic wording): generic rule plus one concrete example, keeping skill text tool-agnostic and repo-agnostic per repository guidelines; source: guidelines tool-agnostic design rule, 2026-11-02, affected sections: Task 1.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the documented convention matches the verified Codex behavior recorded in the backlog row; no statement contradicts the shared `skills_repo_path` guidance.
- Consistency: all touched surfaces (Quick Start, Wrong Location, Quick Reference, Key Takeaways) agree; a grep for stale project-local wording finds no contradicting residual.
- Maintainability: no personal paths, org names, or tool-specific commands beyond naming agents; wording stays tool-agnostic per repository guidelines; public hygiene scan exits 0.

**Done when:**
- `agents/skills/how-to-write-skills/SKILL.md` documents `.agents/skills/` as the tracked project-local skill path with the Codex evidence, the narrowed ignore guidance, the migration step, and the per-agent verification caveat.
- `bash scripts/scan-public-hygiene.sh` exits 0; the em-dash added-lines gate over the plan's base exits 0.

**Ship when:**
- none (fully repository-verifiable; no deployed or cross-team condition)

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/how-to-write-skills/SKILL.md` (Task 1)

**Tests:**
- none (skill-text change; the repository keeps no test suite for this skill's prose)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/how-to-write-skills/references/*.md`; reason: the location guidance home is the SKILL.md section this plan extends, and no reference file carries project-local location content today
- `.gitignore`; reason: this repository's own ignore file is unrelated to the consumer-project guidance this plan documents
- any other skill directory; reason: the backlog item scopes the convention change to the authoring guidance skill

## Validation Commands

```bash
bash scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh added-lines --base main
grep -n "\.agents/skills" agents/skills/how-to-write-skills/SKILL.md
```

### Task 1: Document the tracked project-local skill path for private Codex projects

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/how-to-write-skills/SKILL.md`

- [x] The "4. Wrong Location" section documents the project-local convention: for a private project whose agent discovers project skills there, track skills at `.agents/skills/<name>/`; given a reader following only this section, expects the section to name the tracked path, the Codex discovery evidence (verified 2026-11-02 per the backlog row), and the distinction from the shared `skills_repo_path` registry. [class: IMPLEMENTATION_REQUIRED]
- [x] The section states the narrowed ignore guidance with the working gitignore form: ignore the `.agents/` directory's contents with `.agents/*` (the bare directory form cannot re-include children) and re-include the subtree with `!.agents/skills/`; given a project ignoring `.agents/` wholesale, expects the guidance to show this exact two-line narrowing. [class: IMPLEMENTATION_REQUIRED]
- [x] The section keeps unrelated `.agents/` runtime state (caches, scratch, tool state) ignored under the narrowed rules; given the two-line narrowing applied, expects non-skill `.agents/` state to stay ignored. [class: IMPLEMENTATION_REQUIRED]
- [x] The section states the migration precondition: create the destination directory first (`mkdir -p .agents/skills`); given no existing `.agents/skills/`, expects the documented sequence to run without a missing-destination failure. [class: IMPLEMENTATION_REQUIRED]
- [x] The section states the migration: move an existing `agents/skills/<name>/` package with `git mv agents/skills/<name> .agents/skills/<name>` plus the ignore update; given an existing tracked package at the shared-catalog-style path, expects no untracked or double-tracked copy to remain. [class: IMPLEMENTATION_REQUIRED]
- [x] The section's "document the convention in user or repo facts, not in generic skill bodies" clause is amended so the project-local path convention documented in this section is not self-contradicted: given the amended clause beside the new convention bullets, expects the clause to scope the facts-document rule to agent- or environment-specific values (paths that differ per installation) while the tracked project-local skill path itself stays documented in this section. [class: IMPLEMENTATION_REQUIRED]
- [x] The section keeps the supported-agent gate: project-local paths apply only when the agent supports a project skill directory; verify discovery per agent (Codex desktop verified; others may differ); given a reader using a different agent, expects the guidance to direct verification rather than assert universal behavior. [class: IMPLEMENTATION_REQUIRED]
- [x] The Quick Start comment (section 1), the Quick Reference table, and Key Takeaways stay consistent with the new convention: given the four surfaces side by side, expects no surface to state that `agents/skills/` is the only tracked home for project-local skills in private projects. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect pass: `grep -n "\.agents/skills" agents/skills/how-to-write-skills/SKILL.md` shows the convention in the Wrong Location section; `bash scripts/scan-public-hygiene.sh` exits 0; `bash scripts/check-no-em-dash.sh added-lines --base main` exits 0 over the task's committed change. [class: REPOSITORY_TEST]
- [x] Commit: `docs: document tracked project-local skill path for Codex discovery` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-11-02-private-project-skills-codex-discovery.md` (origin row): covered by this plan; deleted at landing; the SKILL.md evidence citation re-pointed to this archived plan as the row's durable home.
- Open sibling row untouched by this run: `docs/history/backlog/2026-11-02-wrong-location-lead-clause-contradiction.md` (owns the lead-clause fix; explicitly scoped out).
- Runtime registry twin `~/.agents/skills/how-to-write-skills/SKILL.md` received the same change in-run (vendored same-run landing; file in the plan's scope).
