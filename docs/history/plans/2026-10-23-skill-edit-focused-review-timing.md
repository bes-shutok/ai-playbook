# Plan: Set Focused Review Timing for Skill Edits

Backlog origin: docs/history/backlog/2026-10-23-skill-edit-focused-review-timing.md
Driving force: code-quality
Plan review record: .ai-playbook/reviews/2026-10-23-plan-review-skill-edit-focused-review-timing-p27d23c08-r*.md
Execution budget: 0.5h total, largest task 0.5h

## Terms

- **Exact working diff:** the complete uncommitted diff for the skill files this change proposes to commit.
- **Focused panel:** the review panel selected under the existing `review-panel-selection.md` policy for the changed files and their risks.
- **User-level instructions:** the shared instructions in `docs/AGENTS.md`, linked by the configured agent instruction entrypoints.

## Why

The skill editing guidance does not set the review point for skill changes, although the operator requires a focused review. A concise user-level rule records the demonstrated pre-commit review point without duplicating shared skill-authoring or panel-selection policy.

## Gist & Examples

TLDR: Add a pre-commit focused review step for skill edits in user-level instructions, so committed skill changes have received the review the operator requires.

Before: A skill change can be committed without a stated review point in the shared user instructions.

After: Before committing changed files under `agents/skills/`, review the exact working diff with the focused panel selected by the existing panel-selection policy. For example, review the staged and unstaged skill-file changes together before the commit.

## Outcome

The user-level instructions require a focused review of the exact working diff before committing skill edits.

- Skill changes have one clear, repeatable review point.
- Shared skill-authoring guidance and panel-selection policy remain single-sourced.

Gate delta: no standing machine refusal, fence, protocol layer, or schema field is added or removed; the plan reuses the existing scanner on an exact temporary copy of the changed instruction text, addressing r2 and r3 validation findings without adding a scanner; one human review-layer duty blocks committing skill-file changes, witnessed by the operator requirement recorded in `docs/history/backlog/2026-10-23-skill-edit-focused-review-timing.md` and its source prompt, with expected frequency once per skill-change commit (volume not yet measured), false-positive cost of review time and commit delay, and review date 2027-01-23.

## Assumptions

- `docs/AGENTS.md` is the durable user-level home because it identifies itself as the source of truth and the configured Codex entrypoint links to it.
- Review before commit is sufficient because the operator's focused panel reviewed the actual working diff before commit; requiring review before canonical writes would add a proposal-and-apply cycle.
- Scope is changed files under `agents/skills/` because the origin concerns shared skill edits; other changes remain governed by the current panel-selection policy.

Decision points requiring a grill: Put the rule in `docs/AGENTS.md`; basis: its source-of-truth declaration and configured entrypoint; simpler option rejected: adding a user preference to shared authoring guidance would duplicate policy. Require review before commit; basis: the origin records that the focused panel reviewed the working diff before commit; simpler option rejected: review before canonical writes adds a separate proposal-and-apply cycle without a demonstrated need.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the instruction names skill edits, the exact working diff, and the pre-commit review point.
- Maintainability: one user-level home changes and existing panel selection remains authoritative.
- Simplicity: no validator, lock, ledger, additional review worker, or second review policy is introduced.

**Done when:**
- The existing `Skill maintenance (summary)` section in `docs/AGENTS.md` contains the concise rule, and the focused panel has reviewed the exact changed diff before commit.
- Readiness and public-hygiene checks pass.

**Ship when:** The updated `docs/AGENTS.md` is available through the configured user-level instruction entrypoints.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:** none.

**Tests:** none.

**Documentation:**
- `docs/AGENTS.md`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan; if the link is weak or speculative, drop it as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/how-to-write-skills/SKILL.md`; the user-specific timing rule belongs in the existing user-level instructions source.
- `agents/skills/review-agents/review-panel-selection.md`; panel selection and composition remain governed by that source.

## Validation Commands

Resolve the scanner and deny-pattern configuration from user facts. Run the required repository scan from the instructions repository root. Because the scanner excludes `docs/AGENTS.md` and that existing file contains a fixed-pattern example, scan only the exact added instruction text through a temporary copy under the scanner's eligible `projects/.ai-playbook/` subtree using the same scanner's `--files` mode. Remove the copy whether the scan passes or fails. This reuses the configured and built-in checks and their existing error handling.

```bash
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
git diff --check
```

### Task 1: Record the pre-commit review point

Context surface: the plan's Terms, this task, and the source requirement in the backlog origin.

Files:
- `docs/AGENTS.md`

- [ ] In `docs/AGENTS.md`, extend the existing `## Skill maintenance (summary)` section with one concise, tool-agnostic rule requiring a focused panel to review the exact working diff for changed skill files before commit, following the current panel-selection policy and without requiring review before canonical writes. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given changed skill files and an existing working-tree diff, the pre-commit instruction identifies that exact diff as the panel input and requires review before commit. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given unrelated files in the same change, the rule limits its trigger to changed skill files and leaves other file review to the existing panel-selection policy. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the configured hygiene scanner on an exact temporary copy of only the added instruction text under the eligible project subtree; require a pass and remove the copy. [class: REPOSITORY_TEST]
- [ ] Commit: `docs: set focused review timing for skill edits` [class: IMPLEMENTATION_REQUIRED]
