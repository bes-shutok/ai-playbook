# Plan: execute-plan Phase 3 review churn control (cap-5 budget, reflection stop, two-class backlog default)

Backlog origins: `docs/history/backlog/2026-09-01-execute-plan-five-review-cap-vs-focused-churn.md` (primary); `docs/history/backlog/2026-09-01-single-sot-for-cross-cutting-contract-rules.md` and `docs/history/backlog/2026-09-01-review-test-false-green-completeness-checklist.md` (folded into scope by user decision 2026-09-01: the exit policy names the two residual classes, these two items define how the named classes resolve). Requirements buffer: `docs/tmp/plan-requirements-review-cap-reflection-gate.md`. Decision record: `docs/maintenance/project-decisions.md` ADR-0002. Review trail: `docs/reviews/2026-09-01-plan-review-phase3-review-churn-control-r1.md` (prefix; later rounds append `-r2`, `-r3`, ...).

## Terms

- **Review iteration cap**: the total count of review rounds in one execute-plan Phase 3 loop, counting full-panel and focused rounds alike, stated as the `max_review_rounds` budget (default 5) in the Review end condition table. `review_round` starts at 0 and increments on every counted launch, so the initial review is round 1. Once the count reaches the budget and a further round would be required, the loop stops and asks the user before that round; a clean round at the budget proceeds to Phase 4. An explicit standing instruction from the user lifts the `max_review_rounds` cap stops (not the full-panel or escalation budgets) for that loop, is recorded in the loop's manifest, and is closed out (marked ended with the exit reason) when the loop exits. (Glossary: "Review iteration cap".)
- **Full-panel round / focused panel**: per `agents/skills/review-agents/review-panel-selection.md`. A full-panel round launches all five base workers and increments `full_panel_rounds`; a focused panel launches fewer and does not.
- **Exit hybrid**: one round whose worker set adds the clear-round quality-bar lenses a prior blocking-clean round lacked (typically design-simplicity and risk), scheduled once for exit coverage. The exit hybrid counts as a review round; at the cap it requires the same ask (waived when a standing instruction covers the loop). Not a new adversarial cycle.
- **Reflection stop**: the mandatory stop at the cap where the agent writes a short session note under `{tmp_dir}/` (rounds run, unresolved residuals by class, backlog items written, whether exit coverage has run) and asks the user before continuing.
- **Canonical home**: the single living document or skill section designated as the source of truth for a cross-cutting rule; peers hold pointers, not restatements.
- **Sibling-doc restatement / duplicate unit witness**: the two backlog-by-default classes. The skill rules below are self-contained (public, portable); the glossary entries in `docs/maintenance/glossary.md` are this repo's language index of the same terms, and both are pinned by validation.
- **Fan-out finding**: one staged finding naming the canonical home and listing the peer restatements, replacing N per-surface findings.
- **Family checklist**: the enumerated list of sibling tests that must gain the same witness for a false-green fix to close.
- **Skill-gate marker**: before EVERY plan-file write, refresh `~/.ai-playbook/runtime/skill-invoked/plans.<project>.<session>.marker` (mode 0o700 dir, atomic 0o600 write, `FileExistsError` is benign, fail loud if unwritable) via `python3 ~/.ai-playbook/scripts/skill_gate.py --write-marker [--session-id "$SID"]`. `project` derives via the shared `facts_paths.resolve_project_key` on `realpath(cwd)`; `session` derives per Session key.
- **Session key**: `SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"`; empty-after-strip means the literal `no-session`; otherwise `sha1(value)[:16]` hex.

## Assumptions

- assume skill edits stay tool-agnostic and runtime-neutral (no runtime or tool names in new text; obligations phrased as verifiable behavior); basis: workspace AGENTS.md tool-agnostic design rule.
- assume every new gate is enforceable on hosts that cannot launch sub-agents: counters count review passes, not worker launches; stops are user asks; basis: `doing-code-review/SKILL.md` :17 "Nested recovery is only for hosts that cannot launch workers".
- assume no runtime registration task is needed for cursor/zcode/codex: the repo is canonical and the shared-registry symlink model propagates skill edits; basis: `projects/.ai-playbook/agent-runtime-layout.md` :19-21, :40.
- assume the harness-side SOT rule stays generic (designate a canonical home, convert peers to pointers or backlog pointer cleanup) without enumerating canonical-home-per-rule-class; basis: the single-SOT item's workflow-embedding table is harness-level.
- assume one address pass may migrate an enumerated test family when the finding is the sole witness for that path; otherwise the family defers as one backlog item; basis: false-green item fixes 1-2 plus the confirmed two-class decision.
- assume only the cap trigger of the primary origin's reflection-stop list is implemented as a stop; the qualitative triggers (two consecutive production-clean rounds, theme regeneration) are subsumed by the cap stop, the exit-hybrid-once rule, and the existing Step 3.5 reconciliation row; basis: the confirmed minimal two-class policy.
- assume the optional one-page convergence checklist (five-review-cap item fix 6) and the optional testing-guideline blurb (false-green item fix 4) are dropped; basis: confirmed minimal two-class policy and documentation minimalism.
- assume the single-SOT origin's soft convergence metric (living full-rule restatement count converging to one plus pointers) is subsumed by the fan-out finding shape and the pointer-cleanup backlog disposition; basis: it is an outcome of the harness rules this plan implements, not a separate mechanism.

## Gist & Examples

What changes:

1. execute-plan Phase 3 gains a total-round budget `max_review_rounds` (default 5), stated as a row in the existing Review end condition table, checked at Step 3.1 before launching and enforced by a new Step 3.5 table row; the amended clean-review row sits above it, so a clean round at the budget proceeds to Phase 4 and the stop fires only when a further round would be required. At the stop the agent writes a session note and asks the user. Every counted Step 3.1 launch increments the count; first same-round verification/timeout re-entries do not (a second same-round re-entry counts, per the counting paragraph). The existing full-panel budget stays unchanged alongside.
2. Two residual classes become backlog-by-default during Phase 3 addressing (a scoped bound on receiving-review's fix-everything default, superseding Class-exhaustive fixes for these two classes only, with an explicit blocking guard, a shipped-surface pointer default, and a reproduced-pin evidence requirement for witness deferrals), together with the canonical-home ordering for fan-outs and the family-completeness closure rule for false-green fixes.
3. Staging side: one fan-out finding replaces N per-surface restatement findings; after a production-path blocking-clean round, at most one exit hybrid is scheduled (reset when a hybrid finding re-enters the address path), unbounded docs/test-only focused clears stop, the superseded :47 exit-rule clause is removed, and the Step 3.5 clean-review row requires that exit coverage before Phase 4.
4. review-loop aligns wording: a review round counts regardless of panel mode.

Why (incident walk-through, sanitized from the backlog item): rounds 1-3 fix production races. Rounds 4-9 find only sibling prose and duplicate witnesses; each cheap fix mutates the tree; each mutation forces a fresh round; `full_panel_rounds` stays at 2, so the only existing stop never fires, and the user intervenes manually. After this change: the round-4 residuals classify into the two backlog classes and are deferred as one fan-out finding and one family-completeness item; the loop reaches a blocking-clean round, runs at most one exit hybrid for quality-bar coverage, and exits; if residuals outside the two classes keep arriving, the cap stop fires after five counted rounds with a session note and an ask. The loop terminates by rule, not by user interruption.

Example (sibling-doc restatement): a cross-cutting rule (say, when a Retry-After header must be emitted) is already fixed in its canonical wire-contract section. A peer operator guide still shows the old wording. Old behavior: fix the guide, mutate the tree, run a fresh round, discover a third doc, repeat. New behavior: the canonical home is already correct; the shipped guide converts to a pointer in the same pass (a legacy peer defers as one pointer-cleanup backlog item). The conversion mutates the digest and follows the normal fresh-targeted-review rule, so the following review ends cleanly instead of discovering a third doc.

Example (duplicate unit witness): round N hardens test A with a call-order assert for a lock-before-classify path. The next round finds test B for a sibling scenario missing the same assert, but test A demonstrably pins that production path (it fails when the order is violated). New behavior: defer as one family-completeness item naming B and its siblings, recording A as the pinning test with a reproduced failure against a violated-invariant mutation; do not fix B inline round after round.

Edge cases: the initial review is round 1 and the budget counts from there; a clean round at the budget proceeds to Phase 4, so the stop applies only when a further round would be required; drops do not mutate code and never extend the loop; at the cap the user can say continue, backlog-and-stop, give a standing "continue until clean" instruction (recorded in that loop's manifest with its loop instance and closed out at exit), or take the Fix-risk direction when fix-risk stop conditions also hold; on a host without sub-agents the same loop runs inline and the same counters apply because rounds are counted, not workers.

## Evaluation Criteria

**Quality dimensions:**

- Decidability: every new Step 3.5 row is evaluable from manifest fields alone (`review_round`, the stated `max_review_rounds` default, the per-round `re_entry_count`, the recorded `standing_continue` line with its session key and loop-instance id, prior round's worker-set composition); the table stays first-match-wins with the amended clean-review row first and the cap row directly below it, and the Fix-risk and reconciliation carve-outs apply when their conditions co-hold at the cap.
- Cross-skill consistency: the cap semantics, the two class definitions, and the fan-out/family shapes each have exactly one owning skill section (glossary for the repo language index; receiving-review for the addressing bound; review-panel-selection and review-staging for staging policy; execute-plan for Phase 3 loop mechanics); the staging trio cites its owners in-sentence, and minimal operational restatements in standalone-skill text cite the owner.
- Anti-churn acceptance: the incident walk-through above, executed against the new Step 3.5 text (including reconciliation detours and relaunch paths), terminates in at most one exit hybrid per coverage need plus a user ask.
- Tool-agnosticism: no added line in the changed skill files names a runtime or tool; the loop is executable inline on hosts without sub-agents.
- Repo gates: `scripts/check-instruction-size.sh` exits 0; the hygiene scan passes at done.

**Done when:**

- All tasks checked; the full Validation Commands block exits 0 on the branch with all plan edits committed.
- One commit per task, each leaving the repo gates green.

**Ship when:**

- The edited skills reach the next cursor/zcode/codex sessions through the registry symlinks at those agents' next session start (no deploy step; session restarts are human-owned).
- The three promoted backlog items are archived to `{backlog_completed_dir}` at plan completion with their status updates (the archival rides with the plans-skill completion flow, not a task of this plan).

## Design Invariants (CR guard)

- The full-panel budget is NOT weakened: `max_full_panel_rounds` = 5 and its ask-before-a-sixth rule stay exactly as they are; `max_review_rounds` is added alongside.
- The fix-everything default of receiving-review stands for every finding outside the two named classes, including cheap Low findings; the bound is scoped to execute-plan Phase 3, and a blocking finding in these classes is never silently backlogged.
- One canonical home per rule: non-owning files reference the owner, the staging trio cites its owners in-sentence, and minimal operational restatements in standalone-skill text are permitted only when they cite the owner. (The glossary-to-skill term mirror is intentional: skills are portable and self-contained, the glossary is this repo's language index.)
- Runtime neutrality: every new obligation is enforceable on a host that cannot launch sub-agents.
- No project names, ticket ids, or review staging contents from the originating incident; the walk-through stays sanitized.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Skill files:**
- `agents/skills/execute-plan/SKILL.md` (Review end condition table; Step 3.1 before-launching check; Step 3.5 table, clean-review row, and reflection stop; Step 3.2 class-routing pointer)
- `agents/skills/receiving-review/SKILL.md` ("Default: address all findings regardless of severity" section bound; canonical-home ordering; family-completeness closure rule)
- `agents/skills/review-agents/review-panel-selection.md` (fan-out staging policy; exit-hybrid-once; docs/test-only focused-clear bound; :47 exit-rule tail replacement)
- `agents/skills/review-agents/testing.md` (family-checklist staging requirement)
- `agents/skills/review-staging/SKILL.md` (fan-out finding shape, "Orchestrator recording rules" section)
- `agents/skills/review-loop/SKILL.md` (round-definition alignment)

**Docs (Phase-1 artifacts on this branch; Task 0 commits them):**
- `docs/maintenance/glossary.md` (three terms)
- `docs/maintenance/project-decisions.md` (ADR-0002)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/doc-hierarchy/SKILL.md`; layout schema, not churn control; its Layer 2 leanness rule is untouched by this plan.
- `agents/skills/doc-hierarchy-upkeep/SKILL.md`; its pointer-preference rule already exists (:27, "Single SOT for decisions"); a parallel restatement would violate this plan's own single-home invariant.
- `agents/skills/doing-code-review/SKILL.md`; the orchestrator contract is unchanged; Phase 3 mechanics live in execute-plan, staging policy in review-panel-selection.
- `agents/skills/plans/SKILL.md`; its review loop already stops before a sixth full panel, and the confirmed decision is scoped to execute-plan Phase 3.
- plans-skill authoring note (the single-SOT workflow-embedding table's "execute-plan implement / plans authoring" row); deferred: authoring-time SOT preference is not exercised by Phase 3 addressing and rides with a future plans-skill change.
- `scripts/**`; no production code changes in this plan.
- `docs/history/**` and `docs/plans/completed/**` except the three promoted backlog items at plan completion; frozen history per ADR-0001 (which covers completed plans, completed review digests, and non-mirror context, not open backlog items).

## Validation Commands

Checks are numbered `[1]`-`[8]` in block comments; the prose below references those numbers. RED-today proof (2026-09-01, this branch): every NEW span pinned in `[1]`-`[4]` is absent from the six skill files today, verified by `rg --count-matches -F` per span or per a shorter substring of it (`max_review_rounds`, "would exceed", "no standing instruction covers this loop, stop", "Total-round budget", "A standing instruction from the user", "as a `standing_continue` line with its scope", "standing_continue: ended", "the granting run's session key", "a loop-instance id when first applied", "differs from the current run", "re_entry_count", "ambiguous means absent", "session note under", "whether exit coverage", "review-reconciliation runs first, then the session note", "Every launch of a Step 3.1 review panel", "starts a new review round", "a second re-entry", "starts at 0", "including exit coverage per", "still writing the session note", "backlog-by-default classes", "and Step 3.3 is skipped", "applying the owner's evidence rules", "skip Step 3.3's launch but still run its verification gate", "supersedes **Class-exhaustive fixes", "never silently backlogged", "regardless of whether", "reproduced failure of the pinning test", "disqualifies the duplicate-witness class", "preferring a pointer over deletion", "follows the normal fresh-targeted-review rule", "canonical home first", "family checklist", "one fan-out finding", "at most one exit hybrid", "no production paths", "Do not resume docs/test-only focused rounds", "once-only allowance resets", "exit coverage additionally follows the exit-hybrid-once rule below", "per the fan-out policy in", "regardless of panel mode", "Return to Step 3.1 with the targeted worker set"); two pre-existing anchors are present today exactly once and are pinned with expect_once as presence guards, not absence claims ("Recurring root, contradictory review artifacts, or configured non-monotonic-cycle cap is reached", "At most five full-panel rounds; ask before a sixth"); the third pre-existing anchor ("Current digest has a fresh clean review") is present today exactly once and is covered after Task 3 by the amended-variant pin below it. The superseded-clause probe `[3]` and the removed-increment probe `[1]` (`Increment ` + backtick-review_round) are RED-today by design: their target text exists today, so those probes fail until Task 3 and Task 1 respectively remove it. Checks `[5]` (doc artifacts) and `[8]` (repo gates) are green today in the working tree: the glossary terms and ADR-0002 exist (Task 0 commits them), and instruction-size exits 0; `[7]` (committed state) is RED-today by design on this branch (Phase-1 doc edits and the plan file are uncommitted until Task 0 and the task commits land). The `[6]` sweep was verified in BOTH directions on the working tree (2026-09-01): an empty skill diff yields `add_bad=0` (pass) and a synthetic added line "+ uses Cursor hooks here" fires the failure; the sweep diffs the merge base against the working tree so uncommitted plan edits are inspected at the full-block run; the deny-list keywords do not appear on any line this plan adds (their existing occurrences in unchanged lines of receiving-review :59, review-loop :88, review-staging :263 are outside the added-line sweep). For interim checks, run each numbered group's lines individually: the block aborts at the first failing group, so a green later group is only observable by running its lines directly.

```bash
cd "$(git rev-parse --show-toplevel)" || exit 1
fail() { echo "VALIDATION FAIL: $1" >&2; exit 1; }
expect_once() { local file=$1 span=$2 n; n=$(rg --count-matches -F "$span" "$file" 2>/dev/null | tr -d ' '); [ "$n" = "1" ] || fail "span not exactly once in $file: $span"; }

# [1] Task 1: execute-plan budget row, cap row, counting, reflection stop
expect_once agents/skills/execute-plan/SKILL.md '`max_review_rounds` review rounds in the whole Phase 3 loop'
expect_once agents/skills/execute-plan/SKILL.md 'whose number would exceed `max_review_rounds`'
expect_once agents/skills/execute-plan/SKILL.md 'A standing instruction from the user'
expect_once agents/skills/execute-plan/SKILL.md 'as a `standing_continue` line with its scope'
expect_once agents/skills/execute-plan/SKILL.md 'standing_continue: ended'
expect_once agents/skills/execute-plan/SKILL.md 'differs from the current run'
expect_once agents/skills/execute-plan/SKILL.md 'session note under'
expect_once agents/skills/execute-plan/SKILL.md 'whether exit coverage'
expect_once agents/skills/execute-plan/SKILL.md 'Every launch of a Step 3.1 review panel'
expect_once agents/skills/execute-plan/SKILL.md 'starts a new review round'
expect_once agents/skills/execute-plan/SKILL.md 'a second re-entry'
expect_once agents/skills/execute-plan/SKILL.md 'starts at 0'
expect_once agents/skills/execute-plan/SKILL.md "the granting run's session key"
expect_once agents/skills/execute-plan/SKILL.md 'a loop-instance id (branch plus loop start timestamp) when first applied'
expect_once agents/skills/execute-plan/SKILL.md 'ambiguous means absent'
expect_once agents/skills/execute-plan/SKILL.md 'Return to Step 3.1 with the targeted worker set'
expect_once agents/skills/execute-plan/SKILL.md 'At most five full-panel rounds; ask before a sixth'
budget_ln=$(rg -nF '`max_review_rounds` review rounds in the whole Phase 3 loop' agents/skills/execute-plan/SKILL.md | head -1 | cut -d: -f1)
fullpanel_ln=$(rg -nF 'At most five full-panel rounds; ask before a sixth' agents/skills/execute-plan/SKILL.md | head -1 | cut -d: -f1)
[ -n "$budget_ln" ] && [ -n "$fullpanel_ln" ] || fail "budget row or full-panel anchor not found"
[ "$((budget_ln - fullpanel_ln))" = "1" ] || fail "budget row must sit directly after the Full-panel budget row"
row_ln=$(rg -nF 'has reached `max_review_rounds` and no standing instruction' agents/skills/execute-plan/SKILL.md | head -1 | cut -d: -f1)
recon_ln=$(rg -nF 'Recurring root, contradictory review artifacts, or configured non-monotonic-cycle cap is reached' agents/skills/execute-plan/SKILL.md | head -1 | cut -d: -f1)
expect_once agents/skills/execute-plan/SKILL.md 'has reached `max_review_rounds` and no standing instruction'
expect_once agents/skills/execute-plan/SKILL.md 'Recurring root, contradictory review artifacts, or configured non-monotonic-cycle cap is reached'
[ -n "$row_ln" ] && [ -n "$recon_ln" ] || fail "Step 3.5 cap row or reconciliation anchor not found"
[ "$((recon_ln - row_ln))" = "1" ] || fail "cap row must sit directly above the reconciliation row"
rg --count-matches -F 'Increment `review_round`' agents/skills/execute-plan/SKILL.md >/dev/null; rc=$?
[ "$rc" = "1" ] || fail "Otherwise row must not carry its own increment (probe rc=$rc)"

# [2] Task 2: receiving-review bound + execute-plan routing pointer
expect_once agents/skills/execute-plan/SKILL.md 'backlog-by-default classes'
expect_once agents/skills/execute-plan/SKILL.md 'and Step 3.3 is skipped'
expect_once agents/skills/execute-plan/SKILL.md "skip Step 3.3's launch but still run its verification gate"
expect_once agents/skills/execute-plan/SKILL.md "applying the owner's evidence rules"
expect_once agents/skills/receiving-review/SKILL.md 'sibling-doc restatement'
expect_once agents/skills/receiving-review/SKILL.md 'duplicate unit witness'
expect_once agents/skills/receiving-review/SKILL.md 'backlog-by-default'
expect_once agents/skills/receiving-review/SKILL.md 'supersedes **Class-exhaustive fixes'
expect_once agents/skills/receiving-review/SKILL.md 'never silently backlogged'
expect_once agents/skills/receiving-review/SKILL.md 'regardless of whether'
expect_once agents/skills/receiving-review/SKILL.md 'reproduced failure of the pinning test'
expect_once agents/skills/receiving-review/SKILL.md 'disqualifies the duplicate-witness class'
expect_once agents/skills/receiving-review/SKILL.md 'preferring a pointer over deletion'
expect_once agents/skills/receiving-review/SKILL.md 'follows the normal fresh-targeted-review rule'
expect_once agents/skills/receiving-review/SKILL.md 'canonical home first'
expect_once agents/skills/receiving-review/SKILL.md 'family checklist'

# [3] Task 3: staging-side rules, clean-row amendment, superseded-clause removal
expect_once agents/skills/review-agents/review-panel-selection.md 'one fan-out finding'
expect_once agents/skills/review-agents/review-panel-selection.md 'at most one exit hybrid'
expect_once agents/skills/review-agents/review-panel-selection.md 'once-only allowance resets'
expect_once agents/skills/review-agents/review-panel-selection.md 'exit coverage additionally follows the exit-hybrid-once rule below'
expect_once agents/skills/review-agents/review-panel-selection.md 'no production paths'
expect_once agents/skills/review-agents/review-panel-selection.md 'Do not resume docs/test-only focused rounds'
rg --count-matches -F ', Phase 3 has no separate worker-coverage exit rule' agents/skills/review-agents/review-panel-selection.md >/dev/null; rc=$?
[ "$rc" = "1" ] || fail "superseded :47 clause must be removed (probe rc=$rc)"
expect_once agents/skills/execute-plan/SKILL.md 'including exit coverage per `review-panel-selection`'
expect_once agents/skills/execute-plan/SKILL.md 'Current digest has a fresh clean review satisfying the clear-round quality bar'
row_ln=$(rg -nF 'has reached `max_review_rounds` and no standing instruction' agents/skills/execute-plan/SKILL.md | head -1 | cut -d: -f1)
[ -n "$row_ln" ] || fail "cap row not found"
clean_ln=$(rg -nF 'Current digest has a fresh clean review satisfying the clear-round quality bar' agents/skills/execute-plan/SKILL.md | head -1 | cut -d: -f1)
[ -n "$clean_ln" ] || fail "amended clean-review row not found"
[ "$((row_ln - clean_ln))" = "1" ] || fail "clean-review row must sit directly above the cap row"
expect_once agents/skills/review-staging/SKILL.md 'per the fan-out policy in `review-panel-selection`'
expect_once agents/skills/review-agents/testing.md 'family checklist'
expect_once agents/skills/review-agents/testing.md 'closure rule in `receiving-review`'

# [4] Task 4: review-loop alignment
expect_once agents/skills/review-loop/SKILL.md 'regardless of panel mode'

# [5] Phase-1 doc artifacts (Task 0 commits them)
expect_once docs/maintenance/glossary.md '**Review iteration cap**'
expect_once docs/maintenance/glossary.md '**Sibling-doc restatement**'
expect_once docs/maintenance/glossary.md '**Duplicate unit witness**'
expect_once docs/maintenance/project-decisions.md '## ADR-0002'

# [6] Tool-agnosticism: no ADDED line (committed or working tree) names a runtime or tool; staged-but-uncommitted lines become visible at the final committed-state run, which is why Task 4 runs the block after all commits
diff_out=$(git diff "$(git merge-base main HEAD)" -- agents/skills/execute-plan/SKILL.md agents/skills/receiving-review/SKILL.md agents/skills/review-loop/SKILL.md agents/skills/review-agents/review-panel-selection.md agents/skills/review-agents/testing.md agents/skills/review-staging/SKILL.md) || fail "git diff failed for the tool-agnosticism sweep"
add_bad=$(printf '%s\n' "$diff_out" | grep -E '^\+' | grep -vE '^\+\+\+' | grep -c -iE "\b(cursor|codex|zcode|claude|copilot|antigravity)\b" | tr -d ' ')
[ "$add_bad" = "0" ] || fail "added lines mention a runtime or tool name"

# [7] Committed state: the final run requires all plan edits committed
test -z "$(git status --porcelain -- docs/plans/2026-09-01-phase3-review-churn-control.md agents/skills/execute-plan/SKILL.md agents/skills/receiving-review/SKILL.md agents/skills/review-loop/SKILL.md agents/skills/review-agents/review-panel-selection.md agents/skills/review-agents/testing.md agents/skills/review-staging/SKILL.md docs/maintenance/glossary.md docs/maintenance/project-decisions.md)" || fail "uncommitted plan edits at the final validation run"

# [8] Repo gates
bash scripts/check-instruction-size.sh || fail "instruction-size gate failed"

echo "ALL VALIDATION COMMANDS PASS"
```

### Task 0: commit the Phase-1 doc artifacts and the plan

Files:
- `docs/maintenance/glossary.md`
- `docs/maintenance/project-decisions.md`
- `docs/plans/2026-09-01-phase3-review-churn-control.md`

- [x] Commit the files above that still have pending edits (typically `glossary.md` and this plan; `project-decisions.md` may already be committed) in one commit so the working-tree basis of checks `[5]` and `[7]` is durable: `plans: phase3 review churn control plan (Phase-1 artifacts)`
- [x] Refresh the plans-class skill-gate marker before each plan-file write per Terms (Skill-gate marker)
- [x] Run → expect, BEFORE this task's commit: `[5]`-`[6]` and `[8]` green; `[1]`-`[4]` and `[7]` RED. AFTER the commit: `[7]` green too (run the groups individually)
- [x] No separate commit for later plan edits: subsequent review-round plan updates ride with their triggering task's commit or a final commit before re-running the full validation block

### Task 1: execute-plan Phase 3 budget row, cap row, counting, reflection stop

Files:
- `agents/skills/execute-plan/SKILL.md`

- [x] In the "Review end condition" table, directly after the **Full-panel budget** row, add this exact row: "| **Total-round budget** | At most `max_review_rounds` review rounds in the whole Phase 3 loop (default 5), counting full-panel and focused rounds alike; ask at the cap |"
- [x] In Step 3.1 "Before launching", extend the existing sentence so it reads: "If a sixth full-panel round or second escalation would be required, stop at Step 3.5 for user direction; if a next round whose number would exceed `max_review_rounds` would be required and no standing instruction covers this loop, stop at Step 3.5 for user direction." (the standing-instruction carve-out attaches to the budget condition only; the full-panel and escalation stops keep no carve-out)
- [x] In the Step 3.5 table, insert directly above the "Recurring root, contradictory review artifacts, or configured non-monotonic-cycle cap is reached" row this exact row: "| `review_round` has reached `max_review_rounds` and no standing instruction covers this loop | Stop; write a short session note under `{tmp_dir}/` (rounds run, unresolved residuals by class, backlog items written, whether exit coverage per `review-panel-selection` has run) and ask the user whether to continue, backlog non-blocking residuals, give a standing continue instruction, or stop; archiving with unresolved blocking findings additionally requires the user's explicit documented acceptance; where fix-risk stop conditions also hold, take the Fix-risk direction instead, still writing the session note; where a reconciliation trigger also holds, review-reconciliation runs first, then the session note and ask |"
- [x] Edit the "Otherwise" table row to read: "| Otherwise | Return to Step 3.1 with the targeted worker set |" (its increment clause moves into the counting paragraph below; the row keeps no increment of its own)
- [x] Directly under the Step 3.5 table, add this exact paragraph: "Every launch of a Step 3.1 review panel increments `review_round`; `review_round` starts at 0, so the initial review is round 1. A relaunch that starts a new review round (a next `-r<N>` staging doc) counts as a launch; a verification-gate or timeout re-entry that re-runs or re-synthesizes the same round's staging doc does not increment, a second re-entry that re-runs workers within the same round (tracked as `re_entry_count` in the manifest, reset each round) counts as a launch and continues the same round's `-r<N>` staging doc as an appended pass, so staging-doc numbering and `review_round` may diverge after a counted re-entry; the cap compares `review_round` only, which this launch advances. A standing instruction from the user for this loop (for example, continue until clean) lifts only the `max_review_rounds` cap stops until the loop exits; record it in `manifest.md` as a `standing_continue` line with its scope, the granting run's session key, and a loop-instance id (branch plus loop start timestamp) when first applied. At loop exit, overwrite it as `standing_continue: ended` with the exit reason. Step 3.5 treats a standing_continue line whose session key or loop-instance id differs from the current run as absent, re-asking rather than honoring it (ambiguous means absent; a loop resumed in a new session therefore re-asks, which is the intended recovery). The full-panel and escalation budgets are unchanged and continue to apply alongside this cap; Step 3.5's manifest update records the round just completed and never advances the counter."
- [x] Run → expect, BEFORE this task's edits: the new-span pins and both adjacency checks are RED (spans absent, rows missing) and the removed-increment probe is RED (its target text is present); AFTER this task's edits: group `[1]` passes on this file, including the flipped increment probe and both adjacency checks; groups `[2]`-`[4]` still fail because their files are untouched. TRANSITIONAL (Task 1 commit only): the cap row sits above the not-yet-moved clean row, so a clean round at the budget stops and asks until Task 3 moves the clean row above it; this interim inversion is intended. Run each numbered group's lines individually when checking interim state; the full block aborts at the first failing group
- [x] Commit: `skills: execute-plan Phase 3 total-round budget and reflection stop`

### Task 2: receiving-review addressing bound + execute-plan routing pointer

Files:
- `agents/skills/receiving-review/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`

- [x] In the "Default: address all findings regardless of severity" section, directly after the existing default paragraph, append this exact bound: "During execute-plan Phase 3, two classes are backlog-by-default instead of fixed-inline; this bound supersedes **Class-exhaustive fixes for recurring classes** for these two classes only. A sibling-doc restatement means the rule's canonical home already states it correctly; a peer on a shipped doc surface converts to a pointer on the canonical home in the same pass, preferring a pointer over deletion when readers may search the old location, and only a non-shipped or legacy peer defers as one pointer-cleanup backlog item. A duplicate unit witness means another test demonstrably pins the invariant, named with evidence it fails when the invariant is violated; defer as one family-completeness backlog item, recording a reproduced failure of the pinning test against a violated-invariant mutation as verify-fix evidence before the backlog item is accepted; a pin that cannot be reproduced disqualifies the duplicate-witness class and the finding reverts to the fix-everything default. A same-pass pointer conversion mutates the digest and follows the normal fresh-targeted-review rule; the round ends when the following review is clean. A finding in these classes that is `blocking: true` follows the blocking re-evaluation procedure of **Fix-risk triage when fixes regenerate findings** (the severity-calibration Blocking decision procedure against the current digest), regardless of whether that section's operational trigger has fired, and is never silently backlogged. Everything else keeps the fix-everything default, including cheap Low findings."
- [x] In the same section, add this exact ordering rule: "For a fan-out on one cross-cutting rule, keep the existing consolidation rule in **Documentation and Comment Findings** and apply it in Phase 3 order: fix the canonical home first, then convert peers to pointers in the same pass or backlog the remaining peers as pointer cleanup; do not rewrite the full rule into every peer."
- [x] Add this exact closure rule beside it: "Mark a `testing#always-passes` fix done only when the finding ships a family checklist (the sibling tests that must gain the same witness) or the enumerated family migrated to a shared helper; a single hardened test closes the finding only when the remaining family is explicitly deferred to backlog as one item."
- [x] In execute-plan's "Step 3.3 verification gate" list, add this exact item: "5. On the Step 3.3-skip path, the skip-path receiving-review pass ran and every valid unfixed finding carries a durable backlog item; items 1-3 apply only when Step 3.3 launched, and on the skip path this item governs."
- [x] Amend execute-plan's Step 3.3 skip sentence so it reads: "If Step 3.2 shows no unresolved blocking findings, skip Step 3.3's launch but still run its verification gate and go to Step 3.4." (item 5 governs the skip path, so the skip must not bypass the gate)
- [x] In execute-plan Step 3.2, after the "Compare rounds" sentence, add this exact routing pointer: "Class membership in the two backlog-by-default classes defined by `receiving-review` (sibling-doc restatement, duplicate unit witness) is decided by the receiving-review sub-agent during Step 3.3 triage, never by the orchestrator here; a blocking candidate still takes the Fix-risk blocking re-evaluation and is never silently backlogged. When Step 3.2 shows no unresolved blocking findings and Step 3.3 is skipped, the orchestrator still routes non-blocking residuals through a receiving-review pass (which may run inline) applying the owner's evidence rules; the pass fixes findings it does not defer (mutating the digest and restarting the fresh-review rule); deferrals of the two classes are classify-and-record only, with pin and mutation evidence produced at backlog-acceptance time, and deferred findings (the two classes, user-deferred, scope-dropped) become durable backlog items per `receiving-review` **Backlog capture** (for the two classes, pointer-cleanup and family-completeness items) before the clean row may exit."
- [x] Run → expect `[1]` still passes, `[2]` now passes, `[3]`-`[4]` still fail, `[5]`-`[6]` green; `[7]` green once this task's commit lands
- [x] Commit: `skills: receiving-review Phase 3 bound (two backlog classes, blocking guard, family completeness) + execute-plan routing pointer`

### Task 3: staging-side rules, clean-row amendment (panel selection, review-staging, testing lens)

Files:
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/review-staging/SKILL.md`
- `agents/skills/review-agents/testing.md`
- `agents/skills/execute-plan/SKILL.md` (clean-row amendment only)

- [x] In the "Exit-coverage rules" sentence of the focused-round bullet, replace the trailing clause ", Phase 3 has no separate worker-coverage exit rule" with "; exit coverage additionally follows the exit-hybrid-once rule below." (the probe in `[3]` fails until this replacement lands)
- [x] Amend the Step 3.5 "Current digest has a fresh clean review" table row to read "| Current digest has a fresh clean review satisfying the clear-round quality bar, including exit coverage per `review-panel-selection` | Proceed to Phase 4; first close any standing_continue line as ended with the exit reason; where a reconciliation trigger also holds, review-reconciliation runs first, and if it changes the digest or staged artifacts, the clean review is no longer fresh and the loop returns to Step 3.1 |" and move it to the position directly above the cap row, so a clean round at the budget proceeds to Phase 4 and the cap stop fires only when a further round would be required. The demotion is intended and stated: below the clean row, the reconciliation row matches only non-clean digests; at the cap with a reconciliation trigger, the cap row's reconciliation-first clause applies (the exit-hybrid rule this names is defined in this same task and commit)
- [x] In review-panel-selection, near the focused-panel rules, add this exact policy: "Before staging multiple findings that one rule's restatement explains, list the living restatements of the rule; when more than one living surface restates it, stage one fan-out finding naming the intended canonical home (or designate a canonical home), not one finding per surface. This is the staging counterpart of the addressing bound in `receiving-review`."
- [x] In review-panel-selection, near the post-fix focused-round preference, add this exact exit rule: "When the plan has production paths and a prior round was blocking-clean on them under the risk and correctness lenses, schedule at most one exit hybrid (the missing quality-bar lenses, typically design-simplicity and risk) for clear-round coverage; when the plan has no production paths, any blocking-clean round satisfies that precondition and the exit hybrid is still required before execute-plan Step 3.5's clean-review row may exit, unless the prior blocking-clean round was a full panel (it already carried every quality-bar lens, so exit coverage is satisfied). Do not resume docs/test-only focused rounds after it, and a blocking finding in the exit hybrid re-enters the normal address path. The exit-hybrid once-only allowance resets when a hybrid finding re-enters the address path, so the post-fix exit attempt again requires coverage."
- [x] In review-staging's "Orchestrator recording rules" section, add this exact finding-shape rule: "A fan-out finding, per the fan-out policy in `review-panel-selection`, records the canonical home and the list of peer restatements in its Analysis; peers resolve by pointer conversion or one pointer-cleanup backlog item, not as independent contract bugs."
- [x] In the testing lens, add this exact staging rule: "A `testing#always-passes` finding on a shared production path must stage the family checklist (sibling tests needing the same witness) or the shared-helper migration plan with the finding; the closure rule in `receiving-review` owns the fix side."
- [x] Run → expect `[1]`-`[2]` still pass, `[3]` now passes (including the superseded-clause probe and the clean-row-above-cap-row adjacency), `[4]` still fails, `[5]`-`[6]` green, `[7]` green once this task's commit lands, `[8]` green
- [x] Commit: `skills: clean-round exit coverage and one fan-out finding staging policy, exit-hybrid-once, family-checklist staging`

### Task 4: review-loop alignment + full validation

Files:
- `agents/skills/review-loop/SKILL.md`

- [x] Near the `max_full_panel_rounds` configuration row, add this exact alignment: "A review round is one review pass regardless of panel mode; full-panel and focused rounds both count; this skill keeps its full-panel-only budget."
- [x] Commit: `skills: review-loop round-definition alignment with Phase 3 budget`
- [x] With ALL plan edits committed, run the FULL Validation Commands block → expect `ALL VALIDATION COMMANDS PASS` (groups `[1]`-`[7]`, including the adjacency checks, the superseded-clause probe, the tool-agnosticism sweep over committed and working-tree state (its failure direction was verified manually on 2026-09-01 with a synthetic added line), and the instruction-size gate)

## Disposition of migrated backlog items
- docs/history/backlog/completed/2026-09-02-phase3-churn-control-r1-review-residuals.md: disposition folded into 2026-09-01-phase3-review-churn-control.md (2026-09-25); per-item file deleted.

- docs/history/backlog/completed/2026-09-02-phase3-churn-control-certification-residuals.md: disposition folded into 2026-09-01-phase3-review-churn-control.md (2026-09-25); per-item file deleted.
