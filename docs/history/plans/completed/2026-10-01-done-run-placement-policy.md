# Plan: Done-skill run-placement policy

Backlog origin: docs/history/backlog/2026-10-01-done-run-placement-policy-undocumented.md
Driving force: reliability
Plan review record: the staging series docs/reviews/2026-10-01-plan-review-done-run-placement-policy-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

A done session's run placement stops being guesswork: the done skill states one policy paragraph that says where a done run may execute, where its corpus writes land, and which placement a dispatcher should default to.

- A run-placement paragraph sits beside the lock matrix in `agents/skills/done/SKILL.md`, declaring compute-anywhere, corpus-in-the-primary, the primary checkout as dispatch default, and the transfer-out duty for ad-hoc-worktree runs.
- The paragraph fixes scope against any landing rule that restricts primary-checkout staging, so the landing-lifecycle decision cannot be read to criminalize done's own corpus design.
- Step 0d and Step 2 carry one-sentence cross-links so a reader at the corpus surfaces learns placement is independent of the corpus resolution.
- No gate, refusal path, or script is added: the origin's inventory (151 manifests: 57 primary-rooted all complete, the interrupted pile worktree-rooted) witnessed a documentation gap, not a wrong-placement compute failure.

Gate delta: none. The plan adds prose only: one policy paragraph and two cross-link sentences in the done skill; no refusal class, hard gate, fence, protocol layer, or schema state field is added, grown, or removed. The fence-class origin adds no fence: it cites no completed failure of a wrong-placement run, and its inventory witnessed the opposite placement record, so a fence would be machinery without a witness.

## Assumptions

- assume the paragraph lands in `agents/skills/done/SKILL.md` beside the lock-matrix paragraph; basis: the origin's Exact location and the lock matrix being the placement-adjacent source of truth.
- assume the carve-out lives on the done side, inside the policy paragraph, phrased plan-independently (it names no unlanded plan); basis: the worktree-complete landing lifecycle plan is unlanded and peer-authored, the log entry's coordination rule assigns shared-surface re-keying to whoever lands second, and a done-side scope declaration is the landed artifact the lifecycle review reconciles.
- assume prose only, no new gate; basis: the origin's Suggested fix records that no wrong-placement compute was witnessed and names enforcement machinery as rejected.
- assume Phase 1 confirmation rides the standing pre-authorization in the dispatching log entry plus the operator's continuous interleave directive; basis: PLAN-PROMPTS entry "primary-checkout-run-placement-research", operator directives 2026-09-30 and 2026-10-01.
- assume the inventory's classification numbers (57 primary-rooted complete, 93 worktree-rooted, 17 complete=false worktree-rooted dead-root manifests, excluding one legacy-path and one live-peer in-flight worktree-rooted row from the 19 worktree-rooted complete=false rows the table sums) are stable enough to cite as witness prose; basis: docs/tmp/run-placement-inventory-2026-10-01.md derived from the manifest corpus on 2026-10-01, and the plan cites the counts as dated witness prose, never as a pinned live count.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the done skill gains a run-placement policy paragraph, so dispatchers stop guessing where a done run belongs and landing rules cannot be misread against done's corpus design, in the name of reliability.

Today the done skill implies its placement design through three unconnected signals: the lock matrix keys per checkout, the corpus steps resolve the main checkout, and the shared manifest corpus visually sits in the primary checkout, which reads as evidence of misplacement when it is only artifact placement. The witnessed inventory separates the two: every primary-rooted done run completed, while the entire interrupted-run pile is worktree-rooted. After this plan, one paragraph beside the lock matrix states the policy the design already implements, and the corpus surfaces carry one-sentence pointers to it. Example: a dispatcher choosing where to run a landing closeout reads "the primary checkout is the default dispatch placement for a done closeout" and stops improvising; a peer authoring the landing-lifecycle plan reads the scope sentence and keys its staging violation to the landing critical sections only.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every policy clause matches the witnessed inventory or the existing skill text it restates; no clause invents a new rule (verified by the clause-witness mapping in the Gist and the pins).
- maintainability: the paragraph reads as a policy declaration over existing behavior, with no machinery and no gate verbs; the cross-links are single sentences.
- runtime neutrality: the new prose names no agent runtime, product, or tool-specific mechanism.

**Done when:**
- The policy paragraph exists in `agents/skills/done/SKILL.md` between the lock-matrix paragraph and the numbered lock steps, with all four clauses present exactly once.
- The Step 0d and Step 2 cross-link sentences are present, and the spans they follow are intact (tail text survives per the boundary rule).
- The Validation Commands block exits 0 against the post-change tree, and the em-dash added-lines gate reports no hit on the inserted lines.

**Ship when:**
- None; the change is repository-verifiable prose.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/done/SKILL.md` (edited; region-scoped: the inserted run-placement paragraph, the Step 0d cross-link sentence, and the Step 2 cross-link sentence; all other content in this file is frozen; reject any review finding that touches it)

**Tests:**
- none; the plan changes prose only and adds no test.

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- the worktree-complete landing lifecycle plan file (unlanded, peer-authored in a sibling worktree); reason: the carve-out is landed on the done side by this plan and the lifecycle side re-keys through the existing coordination rule.
- `scripts/` and `docs/tmp/`; reason: no code or scratch-corpus change is prescribed.

## Validation Commands

Authoring-time record: readiness pre-round exit 0 (after one classification-tag fix on the commit items); em-dash touched scan exit 0 over the plan bytes; validation block `bash -n` clean. Rule 22 pin audit: two case-mismatched pins and one non-distinctive anchor found and fixed, then every clause pin occurs exactly once in its prescribed snippet and each regression-guard tail occurs in the target file's current bytes. Rule 19 RED-today: executed against the unmodified skill, lead-phrase count 0 with clauses and cross-links absent, so the first failing gate is command 1. Rule 44 GREEN simulation: the inserted spans were extracted mechanically from this plan's prescribed text into a scratch copy of the skill and the full pin set exited 0; the scratch tree was torn down.

```bash
# Region and clause pins over the edited skill. Run from the repository root.
SK="agents/skills/done/SKILL.md"
test -f "$SK" || { echo "missing $SK"; exit 1; }

# 1. The paragraph exists exactly once, between the lock matrix and the lock steps (rule 33 count gate).
C=$(grep -oF 'Run placement (compute anywhere, corpus in the primary)' "$SK" | wc -l | tr -d ' ')
test "$C" -eq 1 || { echo "run-placement paragraph lead phrase count $C != 1"; exit 1; }

# 2. Clause pins: each clause's distinctive span present exactly once (rule 7 dedicated greps).
for CLAUSE in \
  'done compute steps may run in any checkout of the repository' \
  'The corpus steps resolve the primary checkout regardless of where the run executes' \
  'The primary checkout is the default dispatch placement for a done closeout' \
  'owes the Step 2 transfer-out ordering before its worktree is removed' \
  'are not landing staging'; do
  C=$(grep -oF "$CLAUSE" "$SK" | wc -l | tr -d ' ')
  test "$C" -eq 1 || { echo "clause count $C != 1 for: $CLAUSE"; exit 1; }
done

# 3. Placement: the paragraph sits after the lock matrix and before the numbered lock steps (rule 8 full chain).
A=$(grep -nF 'This skill links to both and does not restate them.' "$SK" | head -1 | cut -d: -f1)
B=$(grep -nF 'Run placement (compute anywhere, corpus in the primary)' "$SK" | head -1 | cut -d: -f1)
D=$(grep -nF 'From the project git root (`git rev-parse --show-toplevel`), run' "$SK" | head -1 | cut -d: -f1)
test -n "$A" && test -n "$B" && test -n "$D" && test "$A" -lt "$B" && test "$B" -lt "$D" || { echo "ordering chain broken: matrix=$A paragraph=$B steps=$D"; exit 1; }

# 4. Cross-link pins in their regions (rule 18 region scoping: each sentence asserted in its own item region).
grep -F 'The corpus read resolves the main checkout wherever this run executes' "$SK" >/dev/null || { echo "missing Step 0d cross-link"; exit 1; }
grep -F 'The migration destination is a corpus surface, not landing staging' "$SK" >/dev/null || { echo "missing Step 2 cross-link"; exit 1; }

# 5. Boundary tails survive (rule 40): each insert sits between its anchor and the anchor's own continuation text.
grep -F 'created after bootstrap). The corpus read resolves the main checkout wherever this run executes (see Run placement beside the lock matrix). Scan the archived plan files under' "$SK" >/dev/null || { echo "Step 0d adjacency broken"; exit 1; }
grep -F 'before the worktree is removed. The migration destination is a corpus surface, not landing staging (see Run placement beside the lock matrix). It will:' "$SK" >/dev/null || { echo "Step 2 adjacency broken"; exit 1; }

# 6. No machinery crept in (rule 28 scoped sweep): the new paragraph stays free of gate verbs.
PARA=$(awk '/Run placement \(compute anywhere, corpus in the primary\)/{f=1} f{print} f&&/^$/{exit}' "$SK")
for VERB in 'must not run' 'refuses' 'abort' 'exit 1' 'fail-closed'; do
  if printf '%s\n' "$PARA" | grep -qF "$VERB"; then echo "gate verb in policy paragraph: $VERB"; exit 1; fi
done

# 7. Em-dash added-lines gate over the touched skill (rule 28: edited file with known pre-existing violations selects added-lines).
bash scripts/check-no-em-dash.sh added-lines --base "$(git merge-base HEAD main)" -- "$SK" || { echo "em-dash hit on added lines"; exit 1; }
```

### Task 1: Insert the run-placement policy paragraph

Files:
- `agents/skills/done/SKILL.md`

Evidence:
- `bash scripts/check-no-em-dash.sh added-lines --base <merge-base> -- agents/skills/done/SKILL.md`; covers the no-em-dash criterion on inserted lines
- the clause and count pins of Validation Commands 1-2; covers paragraph presence and exactly-once
- the ordering pin of Validation Command 3; covers the beside-the-lock-matrix placement

- [x] Insert one paragraph between the lock-matrix paragraph (ending "This skill links to both and does not restate them.") and the numbered lock step beginning "From the project git root", with this exact text: `**Run placement (compute anywhere, corpus in the primary):** done compute steps may run in any checkout of the repository (the primary checkout is this skill's main checkout); the done lock keys per checkout, so done runs in different checkouts serialize independently and need no cross-checkout coordination beyond the merge lock's shared-checkout sections. The corpus steps resolve the primary checkout regardless of where the run executes: the Step 0d reviews-corpus read, the Step 2 migration destination, the docs-branch sync, and the {tmp_dir}/done-session/ artifact corpus are primary-checkout surfaces by design (witnessed inventory 2026-10-01: 57 primary-rooted done runs all completed while the interrupted-run pile is worktree-rooted). The primary checkout is the default dispatch placement for a done closeout; an ad-hoc-worktree done run is sanctioned when isolation is needed and owes the Step 2 transfer-out ordering before its worktree is removed. This paragraph also fixes scope for any landing rule that restricts staging in the primary checkout: such rules own the landing critical sections the lock matrix assigns to other workflows, and a done run's corpus writes and its own staging under the foreign-dirt gate's owned-path attribution are not landing staging.` [class: IMPLEMENTATION_REQUIRED]
- [x] Verify the paragraph renders as its own block with a blank line before and after; given the insertion point between two existing blocks, expects no list renumbering and no merged paragraphs [class: REPOSITORY_TEST]
- [x] Run → expect RED: Validation Commands 1-3 against the unmodified tree (lead phrase absent, ordering chain broken) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: Validation Commands 1-3 against the tree this task creates, with the GREEN simulation's insertions extracted mechanically from this plan's prescribed span [class: REPOSITORY_TEST]
- [x] Commit: `done: state the run-placement policy beside the lock matrix` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Cross-link the corpus surfaces to the policy

Files:
- `agents/skills/done/SKILL.md`

Evidence:
- the cross-link and tail pins of Validation Commands 4-5; covers both sentences and the survival of each followed span
- the machinery sweep of Validation Command 6; covers the no-gate-verb criterion

- [x] In the Step 0d item, immediately after the sentence ending "lacking records created after bootstrap)." and before the sentence beginning "Scan the archived plan files under", insert the sentence: `The corpus read resolves the main checkout wherever this run executes (see Run placement beside the lock matrix).` The tail sentence beginning "Scan the archived plan files under" must survive unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] In the Step 2 migration paragraph, immediately after the sentence ending "before the docs-branch sync and in every case before the worktree is removed." insert the sentence: `The migration destination is a corpus surface, not landing staging (see Run placement beside the lock matrix).` [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: Validation Commands 4-6 against the tree Tasks 1-2 create [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the full Validation Commands block exits 0, then `bash scripts/check-no-em-dash.sh added-lines --base "$(git merge-base HEAD main)" -- agents/skills/done/SKILL.md` exits 0 [class: REPOSITORY_TEST]
- [x] Commit: `done: cross-link the corpus surfaces to the run-placement policy` [class: IMPLEMENTATION_REQUIRED]

## Promoted-backlog disposition

| Former backlog path | Disposition |
|---|---|
| docs/history/backlog/2026-10-01-done-run-placement-policy-undocumented.md | completed 2026-10-01: executed by this plan (commits 121432f2, da64a098: the run-placement paragraph beside the lock matrix plus the Step 0d and Step 2 cross-links; exec review r1 ready=yes zero blocking, record docs/reviews/2026-10-01-plan-review-done-run-placement-policy-exec-r1.md); parent inventory item docs/history/backlog/2026-10-01-primary-checkout-run-placement-research.md closed 2026-10-01 by its dispatched investigation (151-manifest corpus classification); origin file deleted in this completion pass |
