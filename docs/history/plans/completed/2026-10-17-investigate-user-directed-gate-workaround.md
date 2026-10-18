# Plan: user-directed gate-block recovery clause

Authoring claim: docs/tmp/authoring-claims/investigate-user-directed-gate-workaround.md (session sess_zcode-auth-20261017-1443)

Backlog origin: docs/history/backlog/2026-10-17-investigate-user-directed-gate-workaround.md
Driving force: reliability; off-taxonomy justification: the property this clause protects is continuation of a blocked-but-authorized lane under an explicit operator direction, a reliability property rather than one of the five driving principles; park-triage would not take it because the operator already directed this exact recovery behavior in the witnessed episode and the pause re-bites on every future gate block inside a directed session
Plan review record: the staging series .ai-playbook/reviews/2026-10-17-plan-review-investigate-user-directed-gate-workaround-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 0.5h total, largest task 0.5h

## Terms

- Blocked lane: a workflow lane whose progress a gate or validator refusal stopped; the bounded-repair policy's existing subject.
- Bounded repair: the AGENTS.md Machinery admission protocol bullet that names the allowed responses when a gate blocks a lane; the clause's single home.
- User-directed recovery: an operator direction to investigate and recover the blocked lane, issued in the blocked lane's own session while the block stands.
- Safe workaround within existing authority: a change or action already permitted to the lane (replacement text, a retry shape, an alternate route) that does not edit or bypass the refused gate or validator and does not add machinery.
- Completion boundary: the interrupted lane's own existing end state (its landing, closeout, or report step); the clause binds continuation up to it, never past it.

## Why

The bounded-repair policy names three responses for a blocked lane but never binds an explicit operator recovery direction to any of them, so a session holding a live direction and a validated workaround can still read an earlier "operator decision" record as a required stop. The witnessed 2026-10-16/17 episode (a done closeout refused by the dirt-regression gate while a same-hunk replacement workaround was already validated, and the session parked until the operator corrected it) is the cost this clause removes.

## Gist & Examples

TLDR: binds an explicit operator-directed gate-block recovery into the existing bounded-repair policy, so a directed lane continues through workaround and gate rerun, up to its own completion boundary; declared force reliability.

Before: a done-closeout commit is refused by the dirt-regression gate over an intentional documentation removal; a prior investigation record calls the sanctioned gate change an operator decision, so the session parks the lane even though the operator has explicitly directed investigation and recovery and a validated replacement-text workaround exists; the operator must intervene again to restart the work.

After: the same refusal inside a session that received an explicit operator direction to investigate and recover is worked: the session diagnoses the refusal, applies the safe workaround within its existing authority, reruns the refused gate, and continues the interrupted work up to the lane's existing completion boundary; only a block that remains unresolved falls back to the allowed responses. A session with no such direction keeps today's three bounded responses unchanged.

Edge cases: the direction never authorizes editing or bypassing the refused gate or validator, new machinery, or work beyond the lane's existing completion boundary (gate edits stay plan-gated; machinery stays behind the admission protocol); the clause yields to any rule that names its own trip non-overridable, so the maintenance loop's integrity guards keep refusing overrides; a failed workaround attempt is reverted or disclosed in the disposition report; a block that survives the workaround falls back to the allowed responses; the witnessed episode's own interrupted work is already complete (the closeout landed through the validated workaround), so the clause binds future blocks, not a pending one.

## Outcome

An explicit operator recovery direction moves a blocked lane instead of parking it, without weakening any gate.

- A blocked lane whose session was explicitly directed to investigate and recover continues to its existing completion boundary: diagnosis, a safe workaround within existing authority, and the refused gate's rerun happen first, and an unresolved block still falls back to the allowed responses.
- Gate and validator edit authority is unchanged: still forbidden mid-lane without a plan; the three bounded responses remain the default for undirected lanes.
- No new machinery: the change is one clarifying sentence in the existing policy home.
- Gate delta: none.

## Assumptions

- assume the witnessed interrupted work is already complete through its validated workaround; basis: the placement-closing-doctrine-enforcement closeout landed 1e86f42b3 applying the meaningful-replacement workaround, with follow-up a6b6b15ba, both verified on main 2026-10-17, so the new clause binds future blocks.
- assume the AGENTS.md bounded-repair bullet is the clause's single home; basis: it is the repo-wide policy owner every session loads; the investigate skill's Hard gates (a pinned surface governing the investigate pass, not the caller lane) and the maintenance decision module's maintenance-scoped Blocker recovery paragraph are the recorded rejected homes.
- assume the clause changes no machine-checked behavior; basis: it is policy prose in an instruction document; the pins suite holds no pins over the bounded-repair bullet (verified 2026-10-17 against scripts/check_maintenance_pins.sh).

Decision points requiring a grill: clause home resolved to the AGENTS.md bounded-repair bullet as the single home with no pointer lines (source: the routing entry's Orientation and the operator's standing pre-authorization, 2026-10-17; affected section: Task 1); recovery-carry-out applicability resolved to future blocks because the witnessed blocked closeout already landed through its workaround (source: landing witnesses 1e86f42b3 and a6b6b15ba re-derived from main, 2026-10-17; affected section: Assumptions).

## Evaluation Criteria

**Quality dimensions:**
- correctness: the clause names all four recovery legs (diagnose, apply a safe workaround within existing authority, rerun the refused gate, continue the interrupted work up to the lane's existing completion boundary) plus the allowed-responses fallback; verbatim-span greps over AGENTS.md.
- safety: the clause explicitly withholds gate/validator edit-bypass authority; the two original bullet sentences survive byte-identical; polarity greps.
- minimality: one sentence in one existing home; no new gate, ledger, section, or validator; pins suite and public-hygiene scan green.

**Done when:**
- The prescribed clause span is present verbatim in the AGENTS.md bounded-repair bullet, and the bullet's original two sentences are byte-intact.
- scripts/check_maintenance_pins.sh exits 0; the public-hygiene scan exits 0; the no-em-dash scan over the added lines is clean.

**Ship when:**
- none; the change is fully repository-verifiable.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `AGENTS.md` (the bounded-repair bullet only; all other guidelines sections frozen)

**Tests:**
- none; validation is span-grep and suite based

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/investigate/SKILL.md`; pinned surface governing the investigate pass, not the caller lane, and the clause's single home is AGENTS.md
- `agents/skills/maintenance/decisions.md`; its Blocker recovery paragraph already carries the maintenance-scoped apply-and-continue rule and stays consistent, untouched
- `scripts/dirt_regression_gate.py`; the witnessed refusal's gate is the sibling entry's surface with its own routed work
- `docs/history/backlog/2026-10-17-investigate-user-directed-gate-workaround.md`; the origin row's lifecycle is this landing's riders (the coverage gate's mark-covered flip writing the Status: covered witness) with the row deleted at this plan's execution completion per the repo commit guidelines; no executor edit

## Validation Commands

Validation preamble (authoring-time record): the plans skill's Validation Commands authoring-rules pre-round battery ran before round 1 with these recorded outcomes: the no-em-dash touched scan over the plan bytes (clean), the public-hygiene scan (clean), and the readiness structural pre-round gate (pass). RED-today evidence, re-executed after the r1 folds on 2026-10-17: the full-bullet pin grep and the withholding-polarity grep below each exit 1 against the pre-change AGENTS.md (rc 1 both; the pin cannot match a bullet that does not yet carry the clause). The authoring-time mechanical audit: the full-bullet pin span and the withholding span were extracted from this plan and matched once each against the Prescribed insertion's simulated post-change bullet; the two remaining structural gates (bullet count, numstat confinement) were simulated against a scratch copy carrying the insertion; bash -n over this block is clean.

```bash
# RED-today proven: this full-bullet pin exits 1 against AGENTS.md before Task 1 (rc 1 on 2026-10-17).
# One contiguous fixed string pins placement, verbatim presence, and the original two sentences' byte-intactness.
grep -qF -- "- Bounded repair: when a gate blocks a lane, the allowed responses are a bounded retry, skip-with-report, or park-for-operator. Editing a gate or validator mid-lane to unblock oneself is forbidden without a plan. Additionally, an explicit operator direction to investigate and recover the blocked lane, issued in the blocked lane's session while the block stands, authorizes diagnosing the refusal, applying a safe workaround within existing authority, rerunning the refused gate, and continuing the interrupted work up to the lane's existing completion boundary; it never authorizes editing or bypassing the refused gate or validator, new machinery, or work beyond that boundary, and a block that remains unresolved falls back to the allowed responses above." AGENTS.md || { echo "FAIL: post-change bounded-repair bullet not present verbatim at its single home"; exit 1; }
# Safety polarity witness (independent, diagnosable): the withholding half must be present verbatim.
grep -qF "it never authorizes editing or bypassing the refused gate or validator, new machinery, or work beyond that boundary" AGENTS.md || { echo "FAIL: withholding half missing"; exit 1; }
# The bullet stays one bullet: the clause rides the same line, no new list item.
test "$(grep -c '^- Bounded repair:' AGENTS.md)" -eq 1 || { echo "FAIL: bounded-repair bullet count changed"; exit 1; }
# Scope freeze enforcement: AGENTS.md's whole diff since the merge base is exactly one modified line.
test "$(git diff --numstat "$(git merge-base HEAD refs/heads/main)" -- AGENTS.md)" = "$(printf '1\t1\tAGENTS.md')" || { echo "FAIL: AGENTS.md diff is not exactly one modified line"; exit 1; }
# Shared-body gates over the changed bytes.
bash scripts/check_maintenance_pins.sh || { echo "FAIL: pins suite"; exit 1; }
bash scripts/check-no-em-dash.sh added-lines --base "$(git merge-base HEAD refs/heads/main)" || { echo "FAIL: em-dash in added lines"; exit 1; }
( cd "$(git rev-parse --show-toplevel)" && bash ~/.ai-playbook/scripts/scan-public-hygiene.sh ) || { echo "FAIL: public-hygiene scan"; exit 1; }
```

### Task 1: Land the user-directed recovery clause in the bounded-repair policy

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `AGENTS.md`

Primary class anchors:
- `Bounded repair` in `AGENTS.md`, the Machinery admission protocol bullet this task extends (prose anchor; the bullet's lead token)

Prescribed insertion (verbatim, one sentence appended to the `- Bounded repair:` bullet in AGENTS.md after its existing two sentences and before the bullet's end):
"Additionally, an explicit operator direction to investigate and recover the blocked lane, issued in the blocked lane's session while the block stands, authorizes diagnosing the refusal, applying a safe workaround within existing authority, rerunning the refused gate, and continuing the interrupted work up to the lane's existing completion boundary; it never authorizes editing or bypassing the refused gate or validator, new machinery, or work beyond that boundary, and a block that remains unresolved falls back to the allowed responses above."

- [x] The bounded-repair bullet carries the recovery clause: given an explicit operator direction to investigate and recover the blocked lane issued in its session while the block stands, expects the policy to authorize diagnose, safe workaround within existing authority, rerun, and continuation up to the existing completion boundary, with machinery and beyond-boundary work withheld and an unresolved block falling back to the allowed responses. [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness (withholding boundary): given a reading of the recovery direction as permission to change or bypass the refused gate or validator, expects the clause to withhold that authority verbatim so the plan gate on gate edits still binds. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: the clause-presence grep over AGENTS.md fails (span absent; verified 2026-10-17, grep rc 1). [class: REPOSITORY_TEST]
- [x] Write minimal implementation: append the task's Prescribed insertion, byte-verbatim, to the AGENTS.md bounded-repair bullet after its existing two sentences, before the bullet's end. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: both span greps pass, the bullet-count and numstat scope-freeze gates pass, and the pins suite, em-dash added-lines scan, and public-hygiene scan each exit 0. [class: REPOSITORY_TEST]
- [x] Commit: `docs: bind explicit operator-directed recovery into the bounded-repair policy` [class: IMPLEMENTATION_REQUIRED]
