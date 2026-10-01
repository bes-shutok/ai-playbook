# The landing critical sections compare the creation base with the landing target

[github: https://github.com/admitriev/ai-playbook] Backlog origin: `docs/history/backlog/2026-09-28-checkout-flow-landing-mismatch-guard.md`
Driving force: correctness

## Gist TLDR

TLDR: add one fail-closed comparison sentence at each of the five landing critical sections in `agents/skills/maintenance/prompt-templates.md` (the execution blueprint's primary arm, its temp-worktree arm, the severed-ancestry landing rule, the unblock child's own checkout-holding landing tail, and the authoring blueprint's self-landing tail), so a landing whose resolved worktree-creation base differs from the branch the landing actually targets defers with both refs named, closing the witnessed gap where an unattended landing in a configured checkout-flow project could sweep operator-branch commits onto the default branch because nothing compared the two.

Witnessed 2026-09-28 (round-6 residual of the worktree-first standard-only-mode execution run): the payloads' landing tails pin the repository's default branch while worktree creation follows the canonical per-project base, and the peer-byte guard counts foreign paths as the branch's own changed paths by definition, so the mismatch is invisible to every existing gate. The compare-and-swap arms already refuse on tip MOVEMENT; this arm refuses on landing into the WRONG LINEAGE, which tip-equality cannot see.

## Outcome + Gate delta

A dispatched execution or authoring landing whose run worktree was created from a base other than what the landing actually targets stops before any commit touches the default branch, naming both refs, with the branch and worktree kept on the tails' existing deferred-landing path. Default-branch-integration runs are unaffected: their creation base IS the default branch, so the comparison passes by identity on every existing run; a checkout-flow run's landing now defers by construction (that behavior change is the point).

Gate delta: one checked condition (base-versus-target comparison) added at each of the five landing critical sections in `agents/skills/maintenance/prompt-templates.md`; no script, hook, refusal class outside the existing deferred-landing path, or protocol layer is added - every arm reuses the deferred-landing failure path its tail already defines.

## Terms

- Creation base: the branch or commit the run's worktree was created from (the canonical Base-branch resolution rule's output, recorded at Phase 0 as the session manifest's `run_base`).
- Landing target: what the landing actually moves - the default branch's held checkout in a checkout-holding path, the default ref in a compare-and-swap path.

## Assumptions

- assume the arm is unconditional (fires whenever the two differ) rather than gated on a configured project class: in a default-branch-integration project base and target are identical by construction (verbatim in the Base-branch resolution rule), so the class check adds nothing but a config read, and the unconditional form fails closed on misclassification too; the origin's alternative remedy (landing-to-resolved-base for checkout-flow projects) is rejected because it doubles the landing machinery for a defer-and-reconcile that the existing deferred-landing path already implements. Basis: the origin's Expected behavior offering both arms; the operator's standing accept-recommendations pre-authorization covers the choice.
- assume all five surfaces get the sentence, not only the execution primary arm: the origin names the payloads' landing tails plural, and the r1 and r2 reviews confirmed the temp-worktree arm (the likely path in a checkout-flow project, where no checkout holds the default), the severed-ancestry rule, the unblock child's own checkout-holding landing tail (a self-contained tail with its own capture, squash, and pre-swap invocation; only its no-checkout sub-path routes through the temp-worktree arm), and the authoring self-landing tail each land onto the same default branch under the same exposure. Basis: the origin's Problem sentence and the r1/r2 panels' surface surveys.
- assume the comparison uses what each section already holds: the checkout-holding arms compare the discovered held branch against the recorded creation base; the compare-and-swap arms compare the creation base against the default ref's lineage (a `git merge-base --is-ancestor <creation-base> refs/heads/<default>` success passes, since the creation base of an integration run IS on the default lineage); no new discovery machinery; basis: each paragraph's existing discovery and capture sentences, read on main.
- assume the pins suite stays green with five additive sentences: the suite's landing pins are presence and exactly-once pins elsewhere in the file, and the r1 panel's mechanical insertion simulation left the suite green; basis: the S16-S20 pin inventory, the r1 simulation, and rule 41's validation-time sweep.

Decision points requiring a grill: none remain.

### Task 1 - the comparison arm at the five landing critical sections

- [ ] In `agents/skills/maintenance/prompt-templates.md`, add one comparison sentence at each of the five surfaces below, in each tail's own voice, each carrying the shared shape: [class: IMPLEMENTATION_REQUIRED] compare the run's recorded creation base (the session manifest's `run_base`, recorded at Phase 0) with what the landing actually targets; a mismatch defers the landing naming both refs, keeping the branch and worktree on that tail's deferred-landing path, with the rationale that the peer-byte guard cannot catch the mismatch because it counts foreign paths as this branch's own. Surfaces and anchors (all present on main at authoring time; re-derive exact bytes from the worktree before each edit):
- [ ] Surface 1, the execution blueprint's primary arm: insert immediately before the sentence capturing the pre-landing tip for the parentage gate (anchor: the literal `capture ` followed by `PRE_TIP="$(git -C <default-checkout> rev-parse refs/heads/<default>)"`, which occurs exactly once on main; the comparison compares the creation base with the branch the default-branch checkout holds, discovered by the section's re-verification step). [class: IMPLEMENTATION_REQUIRED]
- [ ] Surface 2, the execution blueprint's temp-worktree arm: insert immediately before that arm's compare-and-swap ref update sentence (anchor: the arm's `then ` + the update-ref literal `git update-ref refs/heads/<default> <new-tip> <old-tip>` region; the comparison compares the creation base against the default ref's lineage with `git merge-base --is-ancestor <creation-base> refs/heads/<default>` (success passes, per Assumption 3). [class: IMPLEMENTATION_REQUIRED]
- [ ] Surface 3, the severed-ancestry landing rule: insert immediately before the rule's first parentage-gate pre-swap invocation sentence (anchor: the rule's `pre-swap` invocation with `--new-commit` pinned to the observed tip; the comparison compares the recorded `run_base` fork point with the default lineage; a severed-ancestry run whose `run_base` is not an ancestor of the default ref is the mismatch shape this surface exists for). [class: IMPLEMENTATION_REQUIRED]
- [ ] Surface 4, the authoring blueprint's self-landing tail: insert immediately AFTER the tail's critical-section re-verification sentence (anchor: the literal `re-verify inside the critical section which checkout holds the default branch`, occurring exactly once on main; after, not before, because the arm's text cites the held branch that sentence discovers). [class: IMPLEMENTATION_REQUIRED]
- [ ] Surface 5, the unblock child's checkout-holding landing tail: insert immediately before that tail's parentage-gate pre-swap invocation sentence (anchor: the tail's own pre-landing tip capture using the `UNBLOCK_PRE_TIP` variable, occurring exactly once on main; the comparison compares the run's recorded creation base with the branch the default-branch checkout holds, discovered by the capture sentence's worktree-list parenthetical (that tail has no separate re-verification sentence). [class: IMPLEMENTATION_REQUIRED]

### Task 2 - Validation

- [ ] Run every Validation Command below from the worktree root; each must pass against the amended tree. [class: REPOSITORY_TEST]
- [ ] Run the rule 22 mechanical audit over this plan: extract each pinned span below and verify it occurs exactly once in the task text that prescribes it; run `bash -n` over the extracted Validation Commands block; fix both sides of any mismatch in the same edit. [class: REPOSITORY_TEST]

## Evaluation Criteria

- A dispatched landing into any of the five sections whose creation base differs from the landing target defers with both refs named, before any commit touches the default branch.
- Default-branch-integration runs pass the comparison by identity; only checkout-flow (or mis-based) runs change behavior, and only by deferring.
- The pins suite stays green: the insertions are additive between pinned spans.

## Review Scope

Editable regions: `agents/skills/maintenance/prompt-templates.md` (the execution blueprint's primary-arm landing critical section around the pre-landing tip capture; its temp-worktree arm around the compare-and-swap; the severed-ancestry landing rule around its first pre-swap invocation; the unblock child's landing tail around its UNBLOCK_PRE_TIP capture; the authoring blueprint's self-landing tail around the critical-section re-verification sentence).

Read-only: `agents/skills/execute-plan/SKILL.md` (the Base-branch resolution rule and the reference-contract sentence); `scripts/check_maintenance_pins.sh` (a consumer, run but not edited); `scripts/landing_parentage_gate.py`; every other file.

## Origins dispositions

The origin stays in place at the backlog top level while this plan is open; execution folds it per the Plan Lifecycle.

## Validation Commands

Run from the worktree root; every check fails closed. Baselines derived from main at authoring time 2026-10-02 (commit 87379052); re-derive any drifted baseline at execution per the provenance rule before trusting a pass. Authoring-time record (rule 29): the em-dash `touched` scan over the plan bytes passed, the public-hygiene scan passed, and `plan_readiness.py --pre-round` passed on the unamended tree; the r1 review panel ran a mechanical insertion simulation leaving the pins suite green. Rule 19 RED-today evidence, verified 2026-10-02 against main bytes: command 1's arm literal is absent (grep rc 1), and command 8's anchor occurs exactly once (green today; insertion-anchor guard). Wrap tolerance: all counts run over the flattened file (`tr '\n' ' '`), the rule 19 flatten form, because the file wraps prose across lines. Rule 22 authoring-time mechanical audit: each pinned span occurs in Task 1's prescribing text exactly once.

1. `FLAT="$(tr '\n' ' ' < agents/skills/maintenance/prompt-templates.md)"; test "$(grep -oF "compare the run's recorded creation base" <<< "$FLAT" | wc -l | tr -d ' ')" -eq 5 || { echo FAIL: arm surface count != 5; exit 1; }` - the arm lands at exactly five surfaces (zero on main at authoring time).
2. `FLAT="$(tr '\n' ' ' < agents/skills/maintenance/prompt-templates.md)"; test "$(grep -oF "counts foreign paths as this branch's own" <<< "$FLAT" | wc -l | tr -d ' ')" -eq 5 || { echo FAIL: rationale clause count != 5; exit 1; }` - each of the five arms carries its why (the peer-byte guard counts foreign paths as this branch's own; zero on main at authoring time).
3. `FLAT="$(tr '\n' ' ' < agents/skills/maintenance/prompt-templates.md)"; grep -qF "defers the landing naming both refs" <<< "$FLAT" || { echo FAIL: defer shape missing; exit 1; }` - the arm names both refs and defers (no silent proceed).
4. `grep -cF 'merge-base --is-ancestor <creation-base> refs/heads/<default>' agents/skills/maintenance/prompt-templates.md | grep -q -v "^0$" || { echo FAIL: lineage form missing; exit 1; }` - the compare-and-swap arms' lineage comparison form exists.
5. `FLAT="$(tr '\n' ' ' < agents/skills/maintenance/prompt-templates.md)"; test "$(grep -oF "a severed-ancestry run whose \`run_base\` is not an ancestor of the default ref is the mismatch shape" <<< "$FLAT" | wc -l | tr -d ' ')" -ge 1 || { echo FAIL: severed-ancestry surface missing; exit 1; }` - surface 3 names its severed-ancestry mismatch shape.
6. `FLAT="$(tr '\n' ' ' < agents/skills/maintenance/prompt-templates.md)"; test "$(grep -oF "discovered by the capture sentence's worktree-list parenthetical" <<< "$FLAT" | wc -l | tr -d ' ')" -eq 1 || { echo FAIL: unblock-tail surface missing; exit 1; }` - surface 5's sentence cites the capture sentence's worktree-list parenthetical as the discovery source (zero on main at authoring time).
7. `bash scripts/check_maintenance_pins.sh || { echo FAIL: maintenance pins broken; exit 1; }` - the pins suite stays green with the five additive sentences.
8. `FLAT="$(tr '\n' ' ' < agents/skills/maintenance/prompt-templates.md)"; test "$(grep -oF '`PRE_TIP="$(git -C <default-checkout> rev-parse refs/heads/<default>)"' <<< "$FLAT" | wc -l | tr -d ' ')" -eq 1 || { echo FAIL: primary-arm anchor count; exit 1; }` - surface 1's anchor (the backtick-prefixed full capture literal; the backtick excludes the unblock child's UNBLOCK_PRE_TIP capture, whose backtick precedes the U; no escape inside the single quotes, a backslash would stay literal for grep -F) stays exactly once.
9. `bash scripts/check-no-em-dash.sh added-lines --base main agents/skills/maintenance/prompt-templates.md || { echo FAIL: em dash in added lines; exit 1; }` - the added-lines gate passes over the edited file.
10. Run the public-hygiene scan from the user facts document's `public_hygiene_scan_script` key over the repository; exit 0 required.
