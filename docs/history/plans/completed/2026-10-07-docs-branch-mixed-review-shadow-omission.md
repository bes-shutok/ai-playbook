# Plan: preserve ignored descendants of mixed configured shadow roots

Backlog origin: docs/history/backlog/2026-10-06-docs-branch-mixed-review-shadow-omission.md
Driving force: code-quality (the origin declares `reliability + data integrity`; code-quality is the mapping tag, justified per the template: the defect silently drops durable review records from the docs branch, a correctness property of the sync's output)
Plan review record: the staging series docs/history/reviews/2026-10-07-plan-review-docs-branch-mixed-review-shadow-omission-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 2.25h total, largest task 0.75h
Authoring claim: docs/tmp/authoring-claims/2026-10-06-docs-branch-mixed-review-shadow-omission.md (session sess_1e13991c-8e25-4535-9a7e-ae31500fc603)

## Terms

- mixed configured shadow root: a candidate root from the docs-branch skill's `SHADOW_CANDIDATES` resolution that contains both Git-tracked files and ignored untracked descendants.
- candidate-discovery loop: the assembled sync run's candidate classification - the Step 2 sync fence's `SHADOW_PATHS` loop (the routing decision the assembled run executes; arms: ignored wholesale, branch-tracked mirror, and this plan's new mixed-configured-root route) and the Step 1 snapshot fence's informational `SNAPSHOT_PATHS` loop (arms: ignored wholesale, zero-coverage loud skip, partially-tracked warning).
- filtered staging: the existing extra-shadow-root mechanism (`git ls-files --others --ignored --exclude-standard` per descendant, minus those under tracked subtrees) that copies only ignored descendants.
- discriminating reproduction: the plan's two probes - one running the real extracted candidate-discovery loop against a mixed-root fixture repo, one running the plumbing helper (`scripts/docs_branch_sync_noworktree.sh`) with the same root in `DOCS_SYNC_SHADOW_PATHS` - that show which mode drops the ignored descendants.
- plumbing helper: `scripts/docs_branch_sync_noworktree.sh`, the no-worktree sync mode's script.

## Why

A closeout's docs sync dropped four new review records from a configured shadow root that held tracked historical files beside ignored review artifacts: the mixed root enters no snapshot in either sync fence - the Step 2 fence's ignored-wholesale and mirror arms both miss it, and the Step 1 fence's partially-tracked arm only warns - so the manifest-owned witnesses went missing from the docs branch. Re-running the sync with the root marked as an extra shadow root recovered them, isolating the gap to the mixed-configured-root route rather than the source files.

## Outcome

A configured shadow root with tracked content and ignored untracked descendants syncs its ignored descendants to the docs branch through the existing filtered-staging mechanism, with tracked-content handling unchanged.

- The candidate-discovery classification gains a mixed-configured-root route: a root with tracked content whose raw ignored set is non-empty enters the sync through the existing filtered staging, giving the mixed root a sync route it lacked (unrouted untracked remainders, when they exist, stay local with the warning).
- The discriminating reproduction decides the plumbing helper's surface: its helper-alone wholesale behavior is unchanged and pinned by the new fixture, while the routed flow (the skill forwards the root in `EXTRA_SHADOW_DIRS`) exercises the helper's existing filtered arm.
- Ignored files nested inside tracked subtrees stay excluded, tracked content flows as before, and the live checkout is untouched.

Gate delta: one checked-condition-set growth on the candidate classification (the Step 2 sync fence's loop gains the mixed-configured-root arm that routes through `EXTRA_SHADOW_DIRS`; the Step 1 snapshot fence's partially-tracked warning keeps its unconditional shape), priced by the origin's cited completed failure (the witnessed 2026-10-06 closeout: four manifest-owned review records dropped from a mixed root and the extra-shadow-root retry recovered them); no refusal class, hard gate, fence, protocol layer, or schema state field is added or removed. The guard liveness ledger's catch-to-incident ratio is 12:14 at authoring time (`python3 scripts/gate_liveness_ledger.py show`, re-derived 2026-10-07); this plan adds no gate or fence, so the citation rides as context, not duty.

## Assumptions

- assume the fix concentrates in the Step 2 sync fence's candidate loop (the `SHADOW_PATHS` classification the assembled run executes: a mixed root today passes neither the ignored-wholesale gate nor the branch-tracked mirror arm, so it enters no snapshot in either mode) and that the plumbing helper needs no behavioral change: the helper's configured-root arm is a wholesale `cp -Rp` that already carries ignored descendants, and the routed flow reaches the helper's filtered arm through the `EXTRA_SHADOW_DIRS` env the skill's plumbing delegation forwards; basis: the skill's Step 2 fence candidate loop and helper snapshot loop re-derived at authoring time, r1 findings F1/F6 (the fence-boundary execution evidence), and Task 1's discriminating reproduction which re-proves both directions before any edit.
- assume the mixed-configured-root arm routes by appending the root to `EXTRA_SHADOW_DIRS` as well as `SHADOW_PATHS`, so the existing extra-root filtered staging runs for it verbatim in both modes (the Step 2 snapshot loop and the helper's filtered arm through the plumbing delegation's env forward): the origin demands the smallest existing filtered-copy mechanism and this is a two-line routing change beside it; basis: the Step 2 fence's `EXTRA_SHADOW_DIRS` consumption, the snapshot loop's extra-root filtered arm, the plumbing delegation's env forward, and r1 finding F6's two-invocation assembly evidence.
- assume the partially-tracked warning keeps its unconditional shape: the Step 1 fence runs before the tracked-subtree filter is defined, the warning's loose sense (some untracked content stays local) holds for every partially-tracked root, and the r2 review rejected the raw-empty narrowing as an overshoot that silences a true warning when an unignored stray coexists with routed ignored descendants; basis: the Step 1 fence's arm order, r1 finding F8, and r2 finding F14.
- assume the extracted-loop fixture is the established probe pattern (the docs-branch-temp-file-hygiene plan's probes run the real extracted Step 2 script in throwaway fixture repos): the fence is skill prose, so the mechanical witness extracts and assembles the fences the way the test suite's runner does; basis: docs/history/plans/completed/2026-09-03-docs-branch-temp-file-hygiene.md and the dispatch entry's prompt paragraph in docs/history/backlog/PLAN-PROMPTS.md (the fixture wording).
- assume the plumbing helper's regression fixture documents the helper-alone wholesale behavior (a root passed directly in `DOCS_SYNC_SHADOW_PATHS` with no routing env) while the routed flow's filtered arm is covered by the extracted-fence fixture: both modes' behavior stay pinned; basis: the origin row's Expected paragraph (keep tracked content handling unchanged) and the dispatch entry's prompt paragraph.

Decision points requiring a grill: none remain.

## Standing constraints

- Tracked content handling is unchanged everywhere: the new arm routes only through the existing filtered staging (ignored descendants not under tracked subtrees), the partially-tracked warning keeps its unconditional shape, and every existing arm keeps its exact behavior.
- The live checkout is never modified by the sync or the fixtures: fixtures build their repos in `mktemp -d` outside the worktree and clean up.

## Gist & Examples

TLDR: A configured shadow root that mixes tracked files with ignored review records now syncs the ignored records through the existing filtered staging instead of dropping them silently (code-quality, mapping the origin's reliability + data integrity).

**Before (today):** The review directory holds tracked historical files beside four new ignored review records. The mixed root enters no snapshot in either sync fence - the Step 2 fence's ignored-wholesale and mirror arms both miss it, and the Step 1 fence's partially-tracked arm only warns (and stays silent when the untracked content is entirely ignored, the origin's shape); the closeout's manifest recovery then refuses: the owned review witnesses are on disk but absent from the docs branch. The recovery is a manual re-run with the root re-declared as an extra shadow root.

**After (this plan):** The same root hits the new mixed-configured-root arm in the Step 2 sync fence: the root joins `SHADOW_PATHS` and `EXTRA_SHADOW_DIRS`, so the existing extra-root filtered staging runs for it in whichever mode the closeout uses, and the four records reach the docs branch without the manual re-run. A root with tracked content and no ignored descendants keeps today's warning (its untracked remainder still has no route), and the plumbing helper's helper-alone wholesale behavior is pinned by a fixture so it cannot regress.

Edge cases: ignored files nested inside tracked subtrees stay excluded (the `docs_branch_under_tracked_subtree` filter is reused verbatim); a fully-ignored root keeps the wholesale copy; the plumbing helper's configured-root arm keeps its wholesale copy and gains only the regression fixture.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the discriminating reproduction shows the assembled-run candidate loop excluding the mixed root before the fix and routing it into `SHADOW_PATHS` and `EXTRA_SHADOW_DIRS` after; the plumbing probe shows helper-alone inclusion both before and after (behavior preserved).
- regression safety: the helper's existing test suite passes; the pins suite, em-dash touched scan, and public hygiene scan pass.
- scope discipline: the skill change is the Step 2 fence's arm; the helper change is one fixture; tracked-content and tracked-subtree handling are byte-unchanged.

**Done when:**
- `( cd "$REPO" && "$TEST_PY" -m pytest scripts/test_docs_branch_sync_noworktree.py -q )` exits 0 with the new mixed-root fixture green.
- The extracted-loop fixture runs the real candidate-discovery block against the mixed-root fixture and the ignored descendants land in the snapshot.
- Every span check in `## Validation Commands` holds on the executed tree.

**Ship when:**
- The next closeout whose review root mixes tracked and ignored files syncs the ignored records without the extra-shadow-root manual retry; it follows from the executed tree.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/docs-branch/SKILL.md` (the Step 2 sync fence's new mixed-configured-root arm; all other spans frozen)
- `scripts/test_docs_branch_sync_noworktree.py` (the new plumbing mixed-root fixture; existing tests frozen)
- `scripts/check_maintenance_pins.sh` (two pin rows beside the existing docs-branch pins)

**Tests:**
- `docs/tmp/probes/` extraction probes *(new, gitignored; the extracted-loop fixture runs from the plan's prescribed heredoc)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/docs_branch_sync_noworktree.sh`; reason: Task 1's plumbing probe shows the helper already includes mixed-root ignored descendants, and the origin's fix shape routes the change through the smallest mechanism that needs it (the helper gains only the fixture).
- The Step 2 snapshot mechanics beyond the candidate loops' routing; reason: the mixed root never reaches a snapshot today, so the snapshot code cannot be the differing route (Task 1's reproduction discriminates).
- `agents/skills/review-staging/SKILL.md`; reason: the manifest-recovery refusal the origin witnessed is the consumer symptom, already recovered by the extra-shadow-root path.

## Validation Commands

Authoring-time evidence (rule 29 pre-round): the plan bytes passed the pre-round gate with exit 0 and `OUTCOME: pass` (one pre-round failure fixed before round 1: the Review Scope inventory omitted the pins file Task 4 edits; the scoped bytes re-ran clean); the em-dash fixer reported 0 substitutions and the touched scan exited 0; the hygiene scan answered `OUTCOME: pass`; the rule 19 RED-today probes ran the three r1-launch new-duty spans against their target files at the base tip with 0 matches each (the post-fold block carries four span gates; the fourth was added by the r1 fold and verified by the r2 round); `bash -n` accepted the extracted Validation Commands block. Round-start state for r1: authoring worktree ai-playbook-wt-dbn, branch 2026-10-07-docs-branch-mixed-shadow, base main 2cc8152e. Round-start state for r3 (post-r2-fold): the rule-19 probes re-ran after the fold (the corrected single-strip append needle 0 today, the narrowing gate removed with its narrowing, the fixture negative-case text 0 today); the r3 round-start commit and digest are this fold's. Round-start state for r4 (post-reconciliation): the rule 13 reconciliation (docs/history/reviews/2026-10-07-plan-review-docs-branch-mixed-review-shadow-omission-reconciliation.md) completed the narrowing revert across the three remaining surfaces, moved the negative assertion to Task 2's filtered-arm probe, restored Task 3 to wholesale-only expectations, and fixed the classification-mode descriptions; the r4 round-start commit and digest are this fold's.

```bash
set -euo pipefail
REPO="$(git rev-parse --show-toplevel)"
TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"
[ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"
( cd "$REPO" && test "$(grep -cF 'Mixed configured shadow root' agents/skills/docs-branch/SKILL.md)" -eq 1 )
( cd "$REPO" && test "$(grep -cF 'EXTRA_SHADOW_DIRS+=("${candidate%/}/")' agents/skills/docs-branch/SKILL.md)" -eq 1 )
( cd "$REPO" && test "$(grep -cF 'test_mixed_configured_root_syncs_ignored_descendants' scripts/test_docs_branch_sync_noworktree.py)" -eq 1 )
( cd "$REPO" && "$TEST_PY" -m pytest scripts/test_docs_branch_sync_noworktree.py -q )
( cd "$REPO" && bash scripts/check_maintenance_pins.sh )
( cd "$REPO" && bash scripts/check-no-em-dash.sh touched )
( cd "$REPO" && bash "${PUBLIC_HYGIENE_SCAN:-$HOME/.ai-playbook/scripts/scan-public-hygiene.sh}" )
```

### Task 1: The discriminating reproduction (RED probes)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `docs/tmp/probes/mixed-root-repro/` *(new, gitignored, cleaned by the task's teardown)*

Evidence:
- the extraction probe's recorded output; covers the before-state criterion (the assembled-run candidate loop excludes the mixed root from both arrays) and the preserved-behavior criterion (the plumbing helper includes the ignored descendant)

- [x] Build a mixed-root fixture repo in `mktemp -d`: one tracked file under the root, one ignored untracked file under the same root (the origin's shape) [class: REPOSITORY_TEST]
- [x] Run → expect RED: the extracted Step 2 sync fence (assembled with the Documentation-paths fence the way the test suite's runner assembles it) puts the mixed root on no `SHADOW_PATHS` entry and no `EXTRA_SHADOW_DIRS` entry (the ignored descendant is absent from the snapshot the run would take) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN-today: the plumbing helper with the same root in `DOCS_SYNC_SHADOW_PATHS` lands the ignored descendant on the docs branch (the no-helper-gap discrimination recorded in the task log) [class: REPOSITORY_TEST]
- [x] Record the probe outputs in the task log (the probes are gitignored and torn down; no commit carries them) [class: REPOSITORY_TEST]

### Task 2: The mixed-configured-root arm in the candidate-discovery block

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/docs-branch/SKILL.md` (the Step 2 sync fence's candidate loop)

Evidence:
- the extraction probe re-run after the edit; covers the after-state criterion (the mixed root enters `SHADOW_PATHS` and `EXTRA_SHADOW_DIRS`, and the assembled run's extra-root filtered staging carries the ignored descendants while the tracked-subtree exclusion holds)

- [x] Insert into the Step 2 sync fence's candidate loop, after the branch-tracked mirror arm and before the loop's closing `fi`, the mixed-configured-root arm: `elif [ -e "$clean" ] && git ls-files --error-unmatch -- "$clean" >/dev/null 2>&1 && git ls-files --others --ignored --exclude-standard -- "$clean" | grep -q .; then` followed by the comment lines `# Mixed configured shadow root: tracked content plus ignored untracked` / `# descendants. Route through the extra-root filtered staging so the` / `# ignored descendants (minus anything under a tracked subtree) reach the` / `# docs branch; tracked content handling is unchanged.` and the appends `SHADOW_PATHS+=("$candidate")` and `EXTRA_SHADOW_DIRS+=("${candidate%/}/")` (the single-strip form: a slash-terminated candidate must not enter the array as a double-slash entry, which would defeat the extra-paths loop's dedup and the snapshot and helper membership tests); the `EXTRA_SHADOW_DIRS` append precedes the fence's extra-paths loop, so the root takes the deduped extra-root route into the snapshot loop's filtered arm, and the plumbing delegation forwards it through the same env [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the extraction probe re-run against the same fixture shows the mixed root in both arrays and the assembled extra-root filtered staging carrying the ignored descendant; the tracked-subtree exclusion still holds (the probe asserts the negative case: a gitignored file nested inside a tracked subtree of the root stays absent); the probe works around the pre-existing first-sync bootstrap leak (the fixture seeds its docs branch before the run; the leak is proven pre-existing with today's fences) [class: REPOSITORY_TEST]
- [x] Commit: `feat: mixed configured shadow roots sync their ignored descendants` [class: IMPLEMENTATION_REQUIRED]

### Task 3: The helper's mixed-root regression fixture

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/test_docs_branch_sync_noworktree.py` (one fixture appended beside the existing extras-root tests)

Evidence:
- `( cd "$REPO" && "$TEST_PY" -m pytest scripts/test_docs_branch_sync_noworktree.py -q )`; covers the pinned-behavior criterion (the helper lands the mixed root's ignored descendant; tracked content flows unchanged)

- [x] Append `test_mixed_configured_root_syncs_ignored_descendants`: given a fixture repo whose configured shadow root holds one tracked file and one ignored untracked file, running the helper with that root in `DOCS_SYNC_SHADOW_PATHS` and no routing env (the helper-alone surface) expects both files present in the docs-branch commit via the wholesale copy and the live checkout unchanged (the wholesale copy carries the whole root, so no negative assertion belongs to this fixture; the tracked-subtree exclusion is asserted by Task 2's extracted-fence probe, which runs the filtered arm) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the helper suite with the new fixture [class: REPOSITORY_TEST]
- [x] Commit: `test: pin the plumbing helper's mixed-root wholesale behavior` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Pins and full validation

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/check_maintenance_pins.sh` (two pin rows beside the existing docs-branch pins)

Evidence:
- `( cd "$REPO" && bash scripts/check_maintenance_pins.sh )`; covers the pins criterion with the two new rows green
- the full Validation block; covers every remaining criterion

- [x] Append two pin rows beside the existing docs-branch pins: `pin "docs-branch mixed-configured-root arm present" grep -qF 'Route through the extra-root filtered staging so the' "$repo/agents/skills/docs-branch/SKILL.md"` and `pin "docs-branch mixed-root helper fixture present" grep -qF 'test_mixed_configured_root_syncs_ignored_descendants' "$repo/scripts/test_docs_branch_sync_noworktree.py"` [class: IMPLEMENTATION_REQUIRED]
- [x] Run the complete `## Validation Commands` block → expect exit 0 on the executed tree [class: REPOSITORY_TEST]
- [x] Commit: `test: pin the mixed-configured-root arm and fixture` [class: IMPLEMENTATION_REQUIRED]
