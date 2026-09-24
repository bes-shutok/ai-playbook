# Plan: Review pointer-wiring polish

Backlog origin: `docs/history/backlog/2026-08-28-review-pointer-wiring-polish.md` (items 1-8; item 6 already landed, see Assumptions).
Review artifacts: `docs/reviews/2026-09-04-plan-review-review-pointer-wiring-polish-r<N>.md` (prefix glob, one per review round).

## Terms

- **Fix-risk triage**: the `receiving-review` section **Fix-risk triage when fixes regenerate findings**; the provider of the fix-vs-backlog decision rules and the stop-for-user-direction clause.
- **Targeted follow-ups**: the `review-agents/review-panel-selection.md` section (renamed from "Review-loop follow-ups" by Task 1) that owns the focused-round composition and exit-coverage rules.
- **Name-only pointer**: a reference that names the owning skill and section without restating the rule's decision content (the single-sourcing target state for call sites).
- **Blocking re-evaluation**: the three-part mechanic (rewrite the Blocking bullet in place, rationale on Analysis, sidecar `findings[].blocking` mirror); contract owner is `review-staging` **Triage presentation freeze**.
- **Staging doc**: the `{reviews_dir}` review artifact produced by `doing-code-review` and updated by triage.

## Assumptions

- assume the renamed section title is **Targeted follow-ups**; basis: backlog item 2's candidate fix names it, and the scheduled run's standing pre-authorization adopts recommended options.
- assume backlog item 6 is already satisfied on the current tree: the catalog bullet points positively at execute-plan Step 3.4/3.5 and the negative "no separate worker-coverage exit rule" claim is absent (grep verified 2026-09-04); basis: repo evidence. This plan adds only an absence sweep, no edit, for item 6.
- assume all edits are instruction-prose single-sourcing with no semantic change at the pointed-at rules; validation is grep-based because the repo has no test harness for skill markdown; basis: repo evidence (skill files are prose instruction sets).
- assume no separate origin copy of the edited skills needs syncing: `~/.agents/skills` is a symlink to this repo's `agents/skills/` (verified 2026-09-04), so repo edits are the live runtime surface and the repo is canonical; basis: host filesystem evidence (`ls -la ~/.agents/skills`).

Decision points requiring a grill: none remain.

## Gist & Examples

Six skill files carry near-copy restatements of rules that are already single-sourced in their provider sections. Each restatement is a drift hazard: when the provider changes, the copies silently diverge (the Step 3.5 row already dropped the "non-interactive" and "minimal" qualifiers). This plan collapses every copy to a name-only pointer and renames the catalog section that all targeted-round call sites point at.

Example (execute-plan Hard Gate 17, before):

> ...and the fix-risk stop for user direction when a must-stay-blocking finding has neither a minimal additive path nor a user in a non-interactive run (same section).

After (pointer only; the conditions live in `receiving-review`):

> ...and the fix-risk stop for user direction under the same section.

Example (catalog section header, before → after): `### Review-loop follow-ups` → `### Targeted follow-ups`, because the section's scope line already governs both `review-loop` and `execute-plan` Phase 3 rounds; the three call sites that cite the old title are updated in the same commit.

Not changed: the decision content itself. `receiving-review` **Fix-risk triage when fixes regenerate findings**, `review-staging` **Triage presentation freeze**, and the catalog's preference rule keep every condition they own today; only downstream copies shrink.

## Evaluation Criteria

**Quality dimensions:**

- Correctness (single-sourcing): every collapsed site retains a resolvable name-only pointer; each provider section retains its full mechanic (positive greps in the Validation Commands block).
- Consistency: zero occurrences of the old section title anywhere under `agents/skills/` (catches missed call sites, not just the four known ones).
- Maintainability: duplicated stop-condition copies are removed without dropping execute-plan-owned orchestration (the budget-question fold into a single ask and the short session note survive in the Step 3.5 row).

**Done when:**

- The full Validation Commands block passes from the repository root (`ALL VALIDATIONS PASSED`).
- Exactly five skill files are modified across three commits: `review-panel-selection.md`, `receiving-review/SKILL.md`, `review-loop/SKILL.md`, `execute-plan/SKILL.md`, `execute-plan/subagent-prompts.md`.
- `review-staging/SKILL.md` is byte-identical to its pre-plan state.

**Ship when:**

- The user accepts the wording pass; the next review round over the fix-risk skill family runs without re-raising pointer-duplication findings (human-owned evidence, prose only).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code (instruction sources):**
- `agents/skills/review-agents/review-panel-selection.md` (only the `### Review-loop follow-ups` section heading and its preference bullet are in scope; all other content frozen)
- `agents/skills/receiving-review/SKILL.md` (only rule 4 of **Staging doc triage outcomes**, the `(Review-loop follow-ups)` pointer in **Fix-risk triage when fixes regenerate findings** rule 4, and that section's closing paragraph are in scope; all other content frozen)
- `agents/skills/review-loop/SKILL.md` (only orchestration rule 4 is in scope; all other content frozen)
- `agents/skills/execute-plan/SKILL.md` (only Hard Gates 17 and 23, the Step 3.5 max-rounds row, and the Step 3.3 verification gate item 4 are in scope; all other content frozen)
- `agents/skills/execute-plan/subagent-prompts.md` (only Address Review step 7 is in scope; all other content frozen)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/review-staging/SKILL.md`; contract owner of the Blocking re-evaluation mechanic — this plan deliberately does not touch it; reject any edit unless a finding shows the owner text itself is wrong.
- `docs/history/backlog/2026-08-28-review-pointer-wiring-polish.md`; archived by the plan-completion pass per Plan Lifecycle, not by a plan task.
- `scripts/plan_readiness.py`; carries an unrelated uncommitted modification from a parallel session; do not touch.
- `README.md`; the catalog indexes skills, not their internal section titles.

## Validation Commands

Run from the repository root. Sweeps are path-scoped to `agents/skills/`, which is why the block's own embedded patterns (present in this plan file under `docs/plans/`) cannot self-match — the scoping is intentional, do not widen it. `test -f` pre-checks exist so a missing file cannot masquerade as a clean zero-match sweep (a grep rc 2 would otherwise pass the forbidden-match branch).

```bash
#!/usr/bin/env bash
set -u
cd "$(git rev-parse --show-toplevel)" || { echo "not a repo" >&2; exit 1; }
fail() { echo "VALIDATION FAILED: $1" >&2; exit 1; }
no_match() { pat="$1"; shift; for f in "$@"; do if grep -qF -- "$pat" "$f"; then fail "forbidden text still present in $f: $pat"; fi; done; }

for f in agents/skills/receiving-review/SKILL.md agents/skills/review-loop/SKILL.md \
         agents/skills/execute-plan/SKILL.md agents/skills/execute-plan/subagent-prompts.md \
         agents/skills/review-agents/review-panel-selection.md agents/skills/review-staging/SKILL.md; do
  test -f "$f" || fail "missing $f"
done

# --- Task 1 probes: catalog rename + split + call-site pointers ---
grep -qF '### Targeted follow-ups' agents/skills/review-agents/review-panel-selection.md \
  || fail "catalog section header not renamed"
if grep -rn 'Review-loop follow-ups' agents/skills/; then fail "stale section name remains under agents/skills"; fi
grep -qF '(Targeted follow-ups' agents/skills/receiving-review/SKILL.md || fail "receiving-review rule 4 pointer not renamed"
grep -qF '(Targeted follow-ups' agents/skills/review-loop/SKILL.md || fail "review-loop rule 4 pointer not renamed"
grep -qF '(Targeted follow-ups' agents/skills/execute-plan/SKILL.md || fail "Hard Gate 23 pointer not renamed"
grep -qF -- '- Exit-coverage rules still apply before declaring exit on a focused clear round' \
  agents/skills/review-agents/review-panel-selection.md || fail "exit-coverage bullet not split out"

# --- Task 2 probes: stop-condition paraphrases collapsed ---
no_match 'has neither a minimal additive path nor a user in a non-interactive run' agents/skills/execute-plan/SKILL.md
grep -qF 'the fix-risk stop for user direction under the same section' agents/skills/execute-plan/SKILL.md \
  || fail "Hard Gate 17 pointer not landed"
no_match 'take the Fix-risk direction per Hard Gate 23 (a stop-and-ask)' agents/skills/execute-plan/SKILL.md
grep -qF 'stop and ask per Hard Gate 23' agents/skills/execute-plan/SKILL.md || fail "Step 3.5 row not collapsed"
no_match 'ends iterations until the user answers' agents/skills/review-loop/SKILL.md
grep -qF 'follows the stop clause of `receiving-review`' agents/skills/review-loop/SKILL.md \
  || fail "review-loop stop note not collapsed"
no_match 'record it as returned-for-ask per review-staging' agents/skills/execute-plan/subagent-prompts.md
no_match 'is recorded as returned-for-ask per review-staging' agents/skills/execute-plan/SKILL.md
grep -qF 'follows the **Backlog capture** returned-for-ask exception' agents/skills/execute-plan/SKILL.md \
  || fail "Step 3.3 gate item 4 not reduced to pointer"
grep -qF 'durable backlog item per `receiving-review` **Backlog capture**' agents/skills/execute-plan/subagent-prompts.md \
  || fail "Backlog capture pointer lost from subagent step 7"

# --- Task 3 probes: receiving-review single-sourcing ---
no_match "rewrite the finding's **Blocking** bullet in place" agents/skills/receiving-review/SKILL.md
grep -qF 'apply the review-staging **Triage presentation freeze**' agents/skills/receiving-review/SKILL.md \
  || fail "triage-outcomes step 4 not reduced to pointer"
grep -qF 'rewrite the Blocking bullet in place' agents/skills/review-staging/SKILL.md \
  || fail "contract-owner mechanic lost from review-staging"
grep -qF 'applies **Staging doc triage outcomes** to the held finding' agents/skills/receiving-review/SKILL.md \
  || fail "post-answer ownership sentence missing"

# --- Backlog item 6 (already landed): must stay absent ---
if grep -qiE 'has no separate worker-coverage exit rule' agents/skills/review-agents/review-panel-selection.md; then
  fail "negative-by-absence Phase 3 exit claim present"
fi

echo "ALL VALIDATIONS PASSED"
```

RED-today evidence (probed against the current tree, 2026-09-04, all fired; returned-for-ask spans re-baselined 2026-09-08 after commit e754d33 rewrote them and were re-probed the same day, both fired): `Review-loop follow-ups` matched once in each of the four Task 1 files; the Hard Gate 17 span, the Step 3.5 stop-and-ask span, the review-loop stop-note span, the subagent returned-for-ask span (`record it as returned-for-ask per review-staging`), the execute-plan Step 3.3 returned-for-ask span (`is recorded as returned-for-ask per review-staging`), and the receiving-review Blocking-mechanic span each matched exactly once; `has no separate worker-coverage exit rule` matched zero (the item 6 absence probe is born GREEN and guards regression only); the `durable backlog item per `receiving-review` **Backlog capture**` and `rewrite the Blocking bullet in place` positive probes each matched exactly once and are born GREEN keep-guards (they protect the surviving pointer and the frozen contract owner's mechanic, and must stay present, never RED).

### Task 1: Catalog section rename and split, with call-site pointers

Files:
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/receiving-review/SKILL.md`
- `agents/skills/review-loop/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`

- [x] Rename the section header `### Review-loop follow-ups` to `### Targeted follow-ups` in `review-agents/review-panel-selection.md`
- [x] Split the overloaded second bullet into two bullets: (a) keep the focused-over-full preference and its fewer-than-five-workers applicability sentence together; (b) move the exit-coverage sentences into a new bullet starting `- Exit-coverage rules still apply before declaring exit on a focused clear round:` carrying the review-loop exit-criteria sentence (including the design-simplicity hybrid), the Phase 3 Step 3.4/3.5 pointer, and the once-only exit-hybrid allowance sentence, wording preserved
- [x] Update the three call-site section pointers to the new name: `receiving-review/SKILL.md` rule 4 `(Review-loop follow-ups)` → `(Targeted follow-ups)`; `review-loop/SKILL.md` orchestration rule 4 `(Review-loop follow-ups; orchestration rule 3 selects the set)` → `(Targeted follow-ups; orchestration rule 3 selects the set)`; `execute-plan/SKILL.md` Hard Gate 23 `(Review-loop follow-ups)` → `(Targeted follow-ups)` (this rename completes backlog item 1; the call sites are already name-only apart from the section title)
- [x] Do not edit the Phase 3 exit sentence further: backlog item 6 is already satisfied (see Assumptions)
- [x] Run the Task 1 probes from the Validation Commands block → expect Task 1 probes green, Task 2/3 probes still failing (RED-today spans present)
- [ ] Commit: `skills: rename catalog follow-up section to Targeted follow-ups`

### Task 2: Collapse stop-condition paraphrases to name-only pointers

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/review-loop/SKILL.md`

- [x] Hard Gate 17 (`execute-plan/SKILL.md`): replace the clause `the fix-risk stop for user direction when a must-stay-blocking finding has neither a minimal additive path nor a user in a non-interactive run (same section)` with `the fix-risk stop for user direction under the same section` (backlog item 3)
- [x] Step 3.5 max-rounds row (`execute-plan/SKILL.md`): replace `take the Fix-risk direction per Hard Gate 23 (a stop-and-ask)` with `stop and ask per Hard Gate 23 / `receiving-review` **Fix-risk triage when fixes regenerate findings**`, keeping the surrounding parentheses content (direction taken regardless of reconciliation trigger, reconciliation still runs first, budget question folded into the single ask, short session note still written) — this restores the dropped "non-interactive" and "minimal" qualifiers by delegation (backlog item 8a)
- [x] Orchestration rule 4 stop note (`review-loop/SKILL.md`): replace `A fix-risk stop for user direction ends iterations until the user answers, like the max-rounds stop.` with `A fix-risk stop for user direction follows the stop clause of `receiving-review` **Fix-risk triage when fixes regenerate findings**.` (backlog item 8b)
- [x] Address Review step 7 (`execute-plan/subagent-prompts.md`): delete the parenthetical `(a finding held `pending` for the fix-risk user decision per **Fix-risk triage when fixes regenerate findings** is the exception: record it as returned-for-ask per review-staging's receiving-review consumer row, not backlogged)` — span re-baselined 2026-09-08 after commit e754d33 inserted the `per review-staging's receiving-review consumer row` phrase; the sentence ends after `record its path on the finding or in the execution log`; the `receiving-review` **Backlog capture** pointer stays (backlog item 7)
- [x] Step 3.3 verification gate item 4 (`execute-plan/SKILL.md`): replace `a finding held `pending` for the fix-risk user decision (Hard Gate 23) is recorded as returned-for-ask per review-staging's receiving-review consumer row, not backlogged.` with `a finding held `pending` for the fix-risk user decision (Hard Gate 23) follows the **Backlog capture** returned-for-ask exception (`receiving-review`).` — the last full restatement of the exception collapses to a pointer (backlog item 7 family; span re-baselined 2026-09-08 after commit e754d33)
- [x] Run the Task 2 probes → expect Task 2 probes green, Task 1 probes still green, Task 3 probes still failing
- [ ] Commit: `skills: collapse fix-risk stop paraphrases to name-only pointers`

### Task 3: receiving-review single-sourcing

Files:
- `agents/skills/receiving-review/SKILL.md`

- [x] **Staging doc triage outcomes** step 4: replace the full mechanic `When an authorizing rule directs a Blocking re-evaluation (see **Fix-risk triage when fixes regenerate findings**), rewrite the finding's **Blocking** bullet in place, record the rationale on its Analysis section, and mirror the flip in the sidecar `findings[].blocking` per review-staging **Severity and ordering** (Triage presentation freeze).` with `When an authorizing rule directs a Blocking re-evaluation, apply the review-staging **Triage presentation freeze** (Severity and ordering) procedure.` — the full three-part mechanic stays in `review-staging` (contract owner; backlog item 4)
- [x] **Fix-risk triage when fixes regenerate findings** closing paragraph: immediately after `until answered, the finding stays `pending` and is recorded as returned-for-ask per review-staging's receiving-review consumer row.` insert `When the answer arrives, the orchestrator applies **Staging doc triage outcomes** to the held finding before the next round.` — anchor re-baselined 2026-09-08 after commit e754d33 extended the sentence; insert after the full sentence ends, not mid-clause; the backlog-or-fix direction stays single-sourced in **Backlog capture**, so the insert must not restate it (backlog item 5)
- [x] Run the Task 3 probes → expect Task 3 probes green
- [ ] Commit: `skills: single-source blocking re-evaluation and post-answer triage ownership`

### Task 4: Full validation

- [x] `bash -n` the Validation Commands block → expect no syntax errors
- [x] Run the full Validation Commands block from the repository root → expect `ALL VALIDATIONS PASSED`
- [x] `git status --short` → expect only the five in-scope skill files modified (plus this plan's own artifacts); `agents/skills/review-staging/SKILL.md` unmodified; `scripts/plan_readiness.py` untouched

## Disposition of migrated backlog items
- docs/history/backlog/completed/2026-09-15-maintenance-review-r4-polish-residue.md: disposition folded into 2026-09-04-review-pointer-wiring-polish.md (2026-09-25); per-item file deleted.

- docs/history/backlog/completed/2026-08-28-review-pointer-wiring-polish.md: disposition folded into 2026-09-04-review-pointer-wiring-polish.md (2026-09-25); per-item file deleted.
