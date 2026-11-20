# Plan: Closeout recovery proves landed content and never manufactures it

Backlog origin: docs/history/backlog/2026-11-04-self-heal-closeout-workaround-must-preserve-landed-tree.md
Driving force: code-quality + simplicity
Plan review record: the staging series .ai-playbook/reviews/2026-11-06-plan-review-self-heal-closeout-workaround-must-preserve-landed-tree-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 2.0h total, largest task 1.0h
Executed: no

Authoring claim: 2026-11-04-self-heal-closeout-workaround-must-preserve-landed-tree.md (session sess_e75fced0-7001-4b90-b69d-979e2eec1dea)

## Terms

- branch-accounting gate: the closeout adjudication in `scripts/worktree_closeout_migrate.py` (`_gate_branch_closeout`) that judges a branch tip by ancestry, then exact tree, then legacy changed-path evidence, and refuses removal when content proof fails.
- sanctioned landing helper: `bash scripts/land_squash.sh land-worktree ...`, the only authorized worktree-complete landing path (`docs/maintenance/development_lessons.md` #264).
- transfer-or-land route: the inventory step of done's Operator branch closeout (sub-step 4 of the Operator branch closeout sequence in `agents/skills/done/SKILL.md`): an inventory item without a verified destination retains the worktree and ref until it is transferred or landed, then the gate is re-run.
- tree-identical marker commit: a commit whose tree equals its first parent's tree (a synthetic merge or squash marker); it carries no content delta and is not landing evidence.
- retained disposition: the adjudication outcome `status: retained`: the branch's removal is not authorized; the disposition line's `reasons` name the failed proof or guard. Retained covers three populations: a failed content proof (the pointer of this plan prints here), a failed guard with content proven (no pointer), and a legacy-evidence retention where the changed-path scope proved the content landed (no pointer).
- closeout: the run-final completion pass owned by the done skill and its closeout helpers, whose branch accounting and removal sequence this plan's surfaces serve.
- gate-removal mode: the `worktree_closeout_migrate.py gate-removal` invocation that adjudicates a worktree's branch (with or without the `--no-charter` authoring stand-down arm) before worktree removal.
- branch-only closeout: the gate invocation that adjudicates a branch ref with no linked worktree (`--branch` mode).
- baseline-less closeout: a closeout whose run produced no Phase 0 closeout baseline to migrate from, so transfer-out falls to the manual scoped-copy arm of done's Transfer-out-and-deletion implementation.

## Why

An operator-directed closeout recovery twice failed to prove that a source branch's content had landed. The first recovery manufactured commit history instead: commits `e7c14aa8` and `eaca3b03` carry trees identical to their first parent while the source tip differs from the destination by 50 paths, and the worktree and branch were then removed. The second recovery (2026-11-05) concluded no safe transfer existed although the owning closeout's inventory step permits exactly that transfer. The contracts that prevent both outcomes (done's transfer-or-land route; lessons #6 and #264 in `docs/maintenance/development_lessons.md` and #450 in `projects/.ai-playbook/development_lessons.md`) were not consulted at the recovery handoff.

## Gist & Examples

TLDR: the recovery handoff gains a never-manufacture instruction that defines a valid landing by resulting tree and gate proof, and a branch adjudication retained for unproven content prints the transfer-or-land route, because two recoveries invented or missed the proof path (code-quality: the proof contract becomes explicit at the handoff; simplicity: no new machinery).

Before: a branch-removal refusal leads a recovery session to create a tree-identical merge commit as a fake landing receipt (`e7c14aa8`, then single-parent `eaca3b03`, both tree-identical to their first parent), or to conclude no safe transfer exists while the done operator sequence's inventory step permits transferring the unverified item and re-running the gate.

After: the self-heal Recovery handoff states that a closeout workaround never manufactures commit history, that a landing counts only when the resulting tree carries the source content through the sanctioned landing helper and the branch-accounting gate passes, and that unprovable proof retains the branch and worktree. A branch adjudication retained for unproven content prints one report-only line naming the transfer-or-land route and the never-manufacture rule before its outcome line; guard-held and legacy-evidence retentions (content proven) print no cause claim.

## Outcome

Closeout recovery can no longer satisfy a branch-removal refusal with synthetic commits, and a recovery stuck at an unproven-content retention verdict is pointed at the sanctioned transfer-or-land route at the moment the gate reports it.

- A recovery workaround that changes commit history to make a refusal appear satisfied is named as never authorized in the recovery skill, with the observable proof test stated beside the prohibition.
- A branch adjudication whose content proof failed reports the exact sanctioned next action at every output path that reports the retained disposition (the gate-removal held block, the gate-removal pass fall-through, and the branch-only path), through one shared emission in the adjudication itself; guard-held, legacy-evidence, and no-charter retentions (content proven) print no cause claim.
- No new gate, validator, lock, ledger, or landing receipt is added; the branch-accounting gate's enforcement and the landing helper are unchanged.

Gate delta: additions priced by the origin's completed-integrity-failure witness (docs/history/backlog/2026-11-04-self-heal-closeout-workaround-must-preserve-landed-tree.md: the 2026-11-04 fabricated-landing recovery, commits e7c14aa8 and eaca3b03, plus the 2026-11-05 retrieval-failure recovery recorded in the origin's update): one prose-only recovery-handoff requirement (Task 1) and one report-only pointer line emitted inside the branch adjudication for the unproven-content retention population, inherited by every output path that reports the retained disposition (Task 2; report output growth, never a new refusal class; the line changes no exit code); removals: none (no refusal, check, or field is removed); blocking review-layer duties added: none; net: two report/prose additions on a witnessed completed failure, enforcement machinery unchanged.

## Assumptions

- assume the smallest repair is a recovery-handoff instruction plus a report-only adjudication pointer, not a landing-helper change; basis: the witnessed bypass happened in hand-created commits outside `scripts/land_squash.sh` (`e7c14aa8`, `eaca3b03`), so a clearer helper refusal would not have fired, lessons #6 and #264 in `docs/maintenance/development_lessons.md` and #450 in `projects/.ai-playbook/development_lessons.md` already own the helper's mechanics, and the origin's suggested direction names exactly this comparison.
- assume the pointer's hook is the failed-content-proof retention population, emitted once inside the adjudication (`_gate_branch_closeout`) so every output path inherits it; basis: both witnesses stood at an unproven-content retention (the second at a branch-only closeout after the worktree was already gone), a retained status can also mean a failed guard with proven content (the held paths' predicate is `removal_blocked = guard_failed`), and the gate-removal unproven-content shape with clean guards ends `OUTCOME: pass` (test `test_unlanded_branch_preserved_and_reported`), so a reason-keyed shared emission that excludes the legacy-evidence population is the only hook that covers every path without a false cause claim.
- assume the gate-removal mode's existing `held:` retention line stays as written; basis: it already names operator resolution, and Task 2's pointer adds the route without rewriting it.
- Origin acceptance carries over verbatim: the origin's Expected paragraph (recovery authorizes diagnosis and safe recovery within the existing contract, never changing commit history to make a refusal appear satisfied) is the Task 1 instruction's content; no SOT supersession applies.
- The 2026-11-05 update witness is in scope as the retrieval-pointer requirement inside Task 1 (the scoped inventory command applies only to baseline-less closeouts; the operator sequence separately permits transfer), never as a new inventory surface.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the prohibition names the observable proof test (resulting tree carries the source content through the sanctioned landing helper and the branch-accounting gate passes); a tree-identical marker commit never reads as landing evidence.
- minimality: two production surfaces change (`agents/skills/self-heal/SKILL.md`, `scripts/worktree_closeout_migrate.py`) and the existing migrate suite gains canaries in `scripts/test_worktree_closeout_migrate.py`; no new machinery; `scripts/land_squash.sh`, `agents/skills/done/SKILL.md`, and `agents/skills/execute-plan/worktree-first.md` are not edited.
- single-homing: the transfer-or-land route is named by pointer to done's Operator branch closeout, never restated as a second procedure.

**Done when:**
- `agents/skills/self-heal/SKILL.md` Recovery carries the never-manufacture instruction, the landing-proof definition, the retention duty, and the done transfer-or-land pointer (Task 1 pins GREEN).
- Every output path in `scripts/worktree_closeout_migrate.py` that reports a failed-content-proof retained disposition prints the report-only pointer line (shared emission in `_gate_branch_closeout`); canaries cover the branch-only, gate-removal pass, and ordinary-held positives and the guard-held, legacy-evidence, and no-charter negatives (Task 2 GREEN).
- `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-11-06-self-heal-closeout-workaround-must-preserve-landed-tree.md` exits 0; the pins suite, the hygiene scan, and the em-dash touched scan exit 0.

**Ship when:**
- No external or deployed condition; the change is repository-internal.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/self-heal/SKILL.md` (Task 1)
- `scripts/worktree_closeout_migrate.py` (Task 2)

**Tests:**
- `scripts/test_worktree_closeout_migrate.py` (Task 2)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/land_squash.sh`; reason: the witnessed bypass never invoked the helper, so its refusal report needs no change (Assumptions, first bullet).
- `agents/skills/done/SKILL.md`; reason: the transfer-or-land route already exists there and is pointed at, not restated.
- `agents/skills/execute-plan/worktree-first.md`; reason: the landing lifecycle is unchanged; `docs/maintenance/development_lessons.md` #264 and `projects/.ai-playbook/development_lessons.md` #450 own its mechanics.

## Validation Commands

Authoring-time record (rule 29): the em-dash touched scan, the hygiene scan, the pins suite, and the readiness pre-round ran over the plan bytes before round 1; the Task 1 pins (F1-F5) and the F6 pin were executed against the untouched targets at worktree tip 5821f1b9c on 2026-11-06 and fired RED-today (absent from their target files; the unproven-content reason prefix was deliberately not pinned because it pre-exists as the adjudication's own reason text); the migrate suite ran GREEN-today excluding the new canaries (they do not exist yet); `bash -n` over this block exits 0.

```bash
REPO="$(git rev-parse --show-toplevel)"; cd "$REPO" || exit 1

# Task 1 pins (RED-today at authoring; GREEN after Task 1). One dedicated
# grep per obligation (rule 7); every check aborts on miss (rule 10).
grep -qF "never manufactures commit history" agents/skills/self-heal/SKILL.md \
  || { echo "F1: never-manufacture instruction missing"; exit 1; }
grep -qF "the branch-accounting gate passes" agents/skills/self-heal/SKILL.md \
  || { echo "F2: landing-proof definition missing"; exit 1; }
grep -qF "retain the branch and worktree" agents/skills/self-heal/SKILL.md \
  || { echo "F3: retention-on-unprovable-proof duty missing"; exit 1; }
grep -qF "permits transferring an unverified inventory item" agents/skills/self-heal/SKILL.md \
  || { echo "F4: transfer-or-land pointer to the done operator sequence missing"; exit 1; }
# Order (rule 8): the insertion sits inside Recovery step 4 after the anchor
# sentence; Recovery steps are single physical lines, so the order check uses
# byte offsets (grep -bo), which order correctly for a mid-line insertion.
A=$(grep -bo "prompt-log freeze and prune procedure" agents/skills/self-heal/SKILL.md | head -1 | cut -d: -f1)
B=$(grep -bo "never manufactures commit history" agents/skills/self-heal/SKILL.md | head -1 | cut -d: -f1)
if [ -z "$A" ] || [ -z "$B" ] || [ "$A" -ge "$B" ]; then
  echo "F5: insertion not after the Recovery step 4 anchor"; exit 1
fi

# Task 2 pins: the pointer literal lives exactly once in the adjudication's
# shared emission (rule 33 count gate; the canaries assert each output path).
grep -qF "transfer-or-land route" scripts/worktree_closeout_migrate.py \
  || { echo "F6: pointer line missing from the adjudication output"; exit 1; }
test "$(grep -oF 'transfer-or-land route' scripts/worktree_closeout_migrate.py | wc -l | tr -d ' ')" -eq 1 \
  || { echo "F6b: pointer literal not unique to the shared emission"; exit 1; }
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_worktree_closeout_migrate.py -q \
  || { echo "F7: migrate suite failed"; exit 1; }

# Boundary scans (rule 29 mechanical-gate subset; final task boundary).
bash scripts/check-no-em-dash.sh touched \
  || { echo "F8: em-dash residue in the touched set"; exit 1; }
bash scripts/scan-public-hygiene.sh \
  || { echo "F9: public hygiene findings"; exit 1; }
bash scripts/check_maintenance_pins.sh \
  || { echo "F10: maintenance pins suite failed"; exit 1; }
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-11-06-self-heal-closeout-workaround-must-preserve-landed-tree.md \
  || { echo "F11: readiness pre-round failed"; exit 1; }
```

### Task 1: Recovery handoff instruction in self-heal

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/self-heal/SKILL.md`

- [ ] In `## Recovery` step 4, immediately after the sentence ending "let maintenance apply its prompt-log freeze and prune procedure when its conditions are met." (that sentence, the rest of step 4, and later steps survive untouched), append this sentence verbatim: "A closeout or branch-removal workaround never manufactures commit history: creating a merge or marker commit whose tree is identical to its parent (the `e7c14aa8` and `eaca3b03` witnesses) is not a landing receipt." [class: IMPLEMENTATION_REQUIRED]
- [ ] Immediately after that appended sentence, append this sentence verbatim: "A landing counts only when the resulting tree carries the source branch's content through the sanctioned landing helper and the branch-accounting gate passes; when that proof cannot be produced, retain the branch and worktree, park, and report the exact evidence needed." [class: IMPLEMENTATION_REQUIRED]
- [ ] Immediately after that appended sentence, append this sentence verbatim: "Before concluding that no safe route exists at such a refusal, re-read the owning closeout's operator sequence: its inventory step (Operator branch closeout in the done skill) permits transferring an unverified inventory item and re-running the gate." [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness: given a branch-removal refusal whose content proof fails, expects the recovery to retain the branch and worktree and report the exact evidence needed, never to create a tree-identical commit or remove either resource. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect RED: the F1-F5 pins in Validation Commands fail against today's Recovery text (all five verified RED-today at authoring, see the Validation preamble). [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: the F1-F5 pins pass after the edit, with the F5 byte-offset order check confirming the insertion follows the step 4 anchor sentence within the step's line. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: forbid history-manufacturing closeout workarounds in self-heal recovery` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Retained-adjudication pointer line in the closeout migrate gate

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `scripts/worktree_closeout_migrate.py`
- `scripts/test_worktree_closeout_migrate.py`

Primary class anchors:
- `_gate_branch_closeout` in `scripts/worktree_closeout_migrate.py`

- [ ] Inside `_gate_branch_closeout`, when the adjudication builds a retained disposition whose reasons include a reason starting `no ancestry or exact-tree proof` that is NOT the legacy changed-path-scope accounting note (the reason the adjudication inserts at `legacy_evidence`-set time, quoted in the next item), append the report-only pointer line defined in the next item to the returned branch lines. [class: IMPLEMENTATION_REQUIRED]
- [ ] The excluded populations never carry the line: a guard-only retention (content proven) and a legacy-evidence retention (content proven by the changed-path scope, whose inserted reason reads `no ancestry or exact-tree proof; the legacy changed-path scope is accounting evidence only and never permits deleting a non-ancestor branch`). [class: IMPLEMENTATION_REQUIRED]
- [ ] The pointer line reads verbatim: `branch-closeout: retained branch holds unproven content; the sanctioned next action is the transfer-or-land route of the done skill's Operator branch closeout; never manufacture a landing commit to satisfy removal`, printed by every output path reporting a failed-content-proof retained disposition (the gate-removal held block, the pass fall-through, the branch-only path) before its `OUTCOME:` line. [class: IMPLEMENTATION_REQUIRED]
- [ ] The `--no-charter` arm structurally inherits the shared emission, but its retained population is always content-proven through its own identity row, so it prints no pointer. [class: IMPLEMENTATION_REQUIRED]
- [ ] The line is report-only: it changes no exit code, no refusal class, no disposition value, and no existing line's bytes. [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness (cause accuracy, negative): given a guard-held retention whose content proof passed (for example a migrated artifact missing under the target), expects no pointer line to print; given a legacy-evidence retention whose content the changed-path scope proved landed, expects no pointer line to print; given a `--no-charter` held run whose identity row proves the content via recorded landing, expects no pointer line to print. [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness: given a branch-only closeout whose adjudication retains the branch for unproven content, expects the gate run to print the pointer line and still end `OUTCOME: fail` with exit 1. [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness: given the gate-removal unproven-content shape with clean guards, expects the pointer to print and the run to still end `OUTCOME: pass` with exit 0; given the ordinary held shape (unproven content plus a failed guard), expects the pointer before the `held:` line and `OUTCOME: fail` with exit 1. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect RED: the three positive canaries in `scripts/test_worktree_closeout_migrate.py` (branch-only retained, the gate-removal pass shape, the ordinary gate-removal held arm) fail because no pointer line prints, while the pre-existing suite still passes; the three negative canaries (guard-held, legacy-evidence, `--no-charter` held) pass today by construction, the pointer literal occurring nowhere in the script, and become discriminating only once the emission lands. [class: REPOSITORY_TEST]
- [ ] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the migrate suite from the Validation Commands block (F7) exits 0 including the six new canaries. [class: REPOSITORY_TEST]
- [ ] Commit: `feat: name the transfer-or-land route on retained branch adjudications` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Boundary scans and mechanical audit

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files: none (validation and run-record duties only; no tracked bytes change)

- [ ] Run the full Validation Commands block from the repository root and record each command's outcome (F1-F11) in the run record; every command must exit 0. [class: REPOSITORY_TEST]
- [ ] Record in the run record that the F1-F5 pins flipped RED-to-GREEN exactly at Task 1 and the F6 and F6b pins at Task 2, matching the authoring-time RED-today evidence in the Validation preamble (the unproven-content reason prefix is deliberately unpinned; the six canaries, three positives and three negatives, carry Task 2's behavioral proof). [class: REPOSITORY_TEST]
- [ ] Commit: none (the boundary records the justified nothing-to-commit outcome per execute-plan Step 1.4) [class: IMPLEMENTATION_REQUIRED]
