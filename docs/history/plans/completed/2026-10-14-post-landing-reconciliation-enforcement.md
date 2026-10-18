# Plan: enforce the landing reconcile receipt and sweep primary-checkout freshness

Backlog origins (scope of record):
- docs/history/backlog/2026-10-13-landing-staged-reversal-in-primary-index.md

Driving force: automation + code-quality
(the plans-skill closed taxonomy tags; compound ranked automation primary, code-quality secondary. Automation: the reconciliation duty stops depending on a landing session reading prose and the between-landings freshness check runs autonomously in the survey. Code-quality: the landing critical section gains the completion assertion its lifecycle always implied. No non-principle justification needed; both tags are taxonomy members.)

Plan review record: the staging series .ai-playbook/reviews/*-plan-review-post-landing-reconciliation-enforcement-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 3.5h total, largest task 1.5h

## Terms

- Landing critical section: the lock-held span of `scripts/land_squash.sh` (mode `land` or `land-worktree`) from lock authenticity through the compare-and-swap ref move and the parentage gate's post-landing invocation, ending at the helper's final OUTCOME line.
- Worktree-complete landing: the `land-worktree` mode; the squash composes in a temp index over the source worktree's bytes and the primary checkout receives only the compare-and-swap ref move, never an index or working-tree write.
- Reconcile receipt: the record `scripts/reconcile_post_landing.py` produces for one landing: the invocation command, its exit code, and its one-line-per-row output (restored, removed, block, wholesale, synced); this plan homes it at `docs/tmp/landing-receipts/<post-tip>.txt` under the primary checkout (gitignored, local-only), with the durable copy riding the landing session's session notes.
- Post-landing reconciliation: the landed implementation in the Worktree-first standard section of `agents/skills/execute-plan/SKILL.md`; `scripts/reconcile_post_landing.py --base <branch> --pre-tip <sha> --post-tip <sha>` classifies every landing-changed path in every live checkout of the base branch and restores the discriminator-gated stale classes; exit 0 all checkouts verified, exit 1 named block rows, exit 2 tool failure.
- Stale-checkout discriminator: the rule (single home: the Worktree-first standard section) that a tracked file is a stale-checkout artifact, never an edit, exactly when its blob equals that path's blob at a proper ancestor commit while HEAD has advanced past that ancestor; restore-and-record, never commit, never blanket-reset.
- Ancestor blob: a path's blob at a proper ancestor commit of HEAD, enumerated by walking `git log --format=%H <tip> -- <path>` and rev-parsing `<commit>:<path>`, skipping commits where the path does not exist (a deletion or rename-source commit), such skips never treated as a match or a tool failure.
- Named-block row: one `block <checkout> <path> <witness>` line the reconciliation prints for a genuine modification, a staged peer edit, a fresh-mtime bound, or a refused restore; the sanctioned partial state when recorded per the named-block protocol.
- Silent working-tree variant: the witness 5 residue class: worktree-landed landings leave primary bytes at pre-landing values with no staged signature, presenting as ordinary `M`/`MM` status entries; detectable only through the ancestor-blob discriminator.
- Warning-only posture: a machinery post-landing protocol shape: the arm reports findings, never blocks a lane, never writes; promotion to blocking only through the guard liveness ledger's first true catch with a pre-registered registry-removal row's criteria.
- Guard liveness ledger: `scripts/gate_liveness_ledger.py`, the measured catch-to-incident record per guard; a new gate's Gate delta cites its family's current ratio.
- Pins suite: `scripts/check_maintenance_pins.sh`, the literal-pin battery over skill and script text; a touched pinned span reconciles the pin and the text in the same edit beside the pin's provenance comment.
- Vendored twin: the runtime-side copy of an edited skill file, synced in the same landing change per the repository guidelines' Vendored Asset Sync Rules.

## Why

Six deterministic witnesses across 2026-10-13/14 show the same root: `scripts/reconcile_post_landing.py` is landed and correct, but nothing enforces running it. The invocation lives only in the landing session's prose recipe, which witness 4 recorded going unread (a primary-checkout commit then silently reverted a certified landing on main), and nothing re-checks live-checkout freshness between landings, which witness 5 recorded as a roughly three-hour silent window on the r3-certified citation-resolution fix. The mechanism exists; the missing complement is enforcement at the landing tail and an autonomous read-only detection arm between landings.

## Gist & Examples

TLDR: `scripts/land_squash.sh` runs the post-landing reconciliation itself at its tail and refuses the completion verdict without a recorded receipt, and the maintenance survey gains a warning-only read-only primary-freshness sweep; declared force automation plus code-quality, motivated by the six witnessed residue reversals.

Before (today): a worktree-landed landing moves the base ref and prints its pass verdict; the reconcile step exists only as prose in the Worktree-first standard section. A landing session that skips the prose leaves every live checkout stale (witnesses 1 through 4 stage the exact inverse into the primary index; witness 5 leaves silent stale bytes for three hours; witness 6 stages de-archive renames of four certified plans), and only a manual audit catches any of it.

After (this plan): the same landing, run through either helper mode, ends with the helper invoking `scripts/reconcile_post_landing.py` under the still-held merge lock, writing the receipt to `docs/tmp/landing-receipts/<post-tip>.txt`, printing `reconcile-receipt: <path>` plus a row summary, and completing with `OUTCOME: pass` only on a receipt recording exit 0 or exit 1 with every block row recorded; a reconcile tool failure refuses the completion verdict (`reconcile-gate` reason), keeps the landed ref, and names the re-run remedy. Between landings, each maintenance survey runs `scripts/reconcile_post_landing.py --check-primary` read-only over the primary checkout's status entries and reports any stale witness warning-only, so the silent variant is caught autonomously instead of by a manual audit three hours later.

Edge cases: a second live checkout carrying a genuine local edit on a landing path yields exit 1 block rows (the sanctioned partial state; the landing still completes and the closeout consumes the receipt); the primary checkout mid-merge or mid-rebase is skipped with a note row, never classified; untracked status entries carry no ancestor semantics and are skipped; the wholesale index signature stays the reconcile-time arm (it needs the landing's pre-tip, which a between-landings sweep does not have); the reconcile tool failure path never rolls back the ref move (the landing bytes are verified by the existing gates; the remedy is re-running the reconcile).

## Outcome

Landings can no longer skip the reconciliation, and stale primary bytes between landings are detected autonomously instead of by manual audit.

- Every `scripts/land_squash.sh` landing (both modes) ends with a recorded reconcile receipt, and the helper's pass verdict requires it: the skipped-reconcile class is mechanically refused at the tail instead of depending on prose being read.
- The maintenance survey reports primary-checkout stale witnesses warning-only on every turn, closing the between-landings detection gap witness 5 demonstrated.
- The two prose consumers re-point to the helper-written receipt, so the invocation runs exactly once per landing, under the lock, instead of once by the helper and once again (or never) by the session.
- Restore semantics, the discriminator's single home, and the single-scanner shape are unchanged: the sweep is a new read-only mode of the existing scanner.

Gate delta: additions priced, removals none. (1) The landing critical section gains one refusal class (completion without a recorded receipt: an exit-0 receipt or an exit-1 receipt with every block row recorded passes; a reconcile tool failure refuses the completion verdict with the landed ref kept and the re-run remedy named) plus one receipt artifact (`docs/tmp/landing-receipts/<post-tip>.txt`): fix-class refusal-path addition priced by the origin-cited no-exit justification, the origin recording why each class-default alternative is impossible: add the sanctioned exit (the named-block receipt IS the sanctioned exit and is included in the passing shapes), remove the false positive (the defect is a missing check, not a false positive; all six witnesses are true positives of no gate at all), simplify the flow (the prose-only flow is the simplification already tried and witnessed failing read-dependent: witness 4's recipe went unread, witness 5's window had no reader), further alternatives the origin and entry record with rejection reasons: routing all landings through the primary checkout (rejected: per-execution worktree isolation is the landed collision-list design), a standalone scanner script (rejected: duplicates the landed discriminator mechanism ahead of any new consumer), force-resetting live checkouts (rejected: the landed contract forbids force and preserves peer bytes), promoting the sweep to blocking at landing (rejected: the machinery admission protocol lands new machinery warning-only). Guard liveness ledger at authoring (2026-10-14): post-landing-staging catches=2 incidents=7, land-squash-containment catches=1 incidents=0, landing_parentage_gate catches=0 incidents=1. (2) The maintenance survey gains one read-only warning-only probe arm (registry id duty:primary-freshness-sweep) with its admission entry and pre-registered removals row in `scripts/machinery_registry.json`: not a gate (never blocks, never restores; promotion only through the ledger's first true catch). Removed refusals, checks, or fields: none (the prose duties are re-pointed, not removed).

## Assumptions

- assume the origin entry's two-arm design (landing-tail receipt gate plus warning-only between-landings sweep) is the validated scope; basis: the PLAN-PROMPTS entry post-landing-reconciliation-enforcement's investigation verdict, scope arms, and rejected alternatives (2026-10-14).
- assume both helper modes get the tail gate; basis: the prose recipe applies to the ref-level landing arms collectively (the Worktree-first standard's Post-landing reconciliation implementation block opens "the ref-level landing arms move the base branch's ref without writing any working tree").
- assume the receipt's machine home is `docs/tmp/landing-receipts/` under the primary checkout; basis: the resolved tmp_dir convention (docs/tmp is the gitignored scratch home; the receipt is session-local evidence whose durable copy rides the session notes).
- assume the sweep scopes to per-path stale detection and skips the wholesale index arm; basis: the wholesale arm's definition needs the landing's pre-tip (`git diff --cached <pre-landing-tip>`), which a between-landings sweep cannot know, while the per-path ancestor-blob rule covers every presented status row class in witnesses 1 through 6.
- assume a reconcile tool failure at the tail keeps the landed ref; basis: the helper's own post-CAS precedent (the origin-leg-only arm keeps the landing and names the operator reconciliation) and the existing prose rule that a failed reconcile fails the closeout, never the landing.

Decision points requiring a grill: none remain.

## Standing constraints

- Committed bytes carry no em-dash characters and no absolute personal filesystem paths; repo-relative paths only (the repository commit gates enforce this).
- The public-hygiene scan (exit 0 required) runs before every commit; validators run with the ai-playbook-test virtualenv first on PATH.
- Edited skill files' vendored twins sync in the same landing change per the repository guidelines' Vendored Asset Sync Rules; a runtime-side catalog edit lands its vendored twin or names the tracked landing path.
- The reconciliation's restore semantics (`classify`, `apply_entry`, `apply_plan`, `verify_checkout` in scripts/reconcile_post_landing.py) and the stale-checkout discriminator's single home (the Worktree-first standard section) are frozen surfaces this plan extends but never rewrites.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the tail gate refuses the completion verdict on a missing or tool-failed receipt and completes on both passing receipt shapes; fixtures prove each branch, including that a tool failure never rolls back the ref move.
- simplicity: no second scanner script exists; the sweep is a mode of the existing scanner; the prose consumers re-point by reference instead of restating the invocation.
- maintainability: the pins suite passes with every touched pinned span reconciled beside its provenance; the registry carries the admission entry and the pre-registered removals row.
- observability: every landing prints `reconcile-receipt: <path>` plus a row summary; the receipt file records the command, exit code, and rows; sweep output is one line per stale witness.

**Done when:**
- All task checkboxes are checked and the full validation battery below exits green.
- `bash scripts/check_maintenance_pins.sh` exits 0.
- Both touched test suites pass under the validator PATH.
- `python3 scripts/plan_readiness.py <this plan>` exits 0 with the final OUTCOME: pass line.

**Ship when:**
- none stated; this plan ships entirely inside this repository.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/land_squash.sh`
- `scripts/reconcile_post_landing.py`
- `scripts/machinery_registry.json`
- `scripts/check_maintenance_pins.sh` (pinned-span reconciliation only, per rule 41)

**Tests:**
- `scripts/test_land_squash.py`
- `scripts/test_reconcile_post_landing.py`

**Skill and doc surfaces:**
- `agents/skills/execute-plan/SKILL.md` (the Post-landing reconciliation implementation block and the landing class routing sentence, re-point and reconcile-gate arm only)
- `agents/skills/maintenance/template-authoring.md` (the self-landing paragraph's reconcile sentence and fail-routing clause, re-point and reconcile-gate arm only)
- `agents/skills/maintenance/survey-arms.md` (one new probe arm bullet)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression plan work introduced, closes wiring implied by an explicit must-fix change (the pins suite's pinned spans over the touched regions included), or contradicts a contract the plan changed.

**Out of scope; reject unless plan-related:**
- `scripts/reverse_squash_guard.py`; reason: the reverse-squash guard's restore semantics are the landed contract this plan must not widen.
- `scripts/reconcile_post_landing.py` restore semantics beyond the new mode (`classify`, `apply_entry`, `apply_plan`, `verify_checkout`); reason: frozen surface per Standing constraints.
- `agents/skills/execute-plan/SKILL.md` sections other than the Post-landing reconciliation implementation block and the landing class routing sentence; reason: the discriminator's single home stays byte-stable outside the re-point.
- `scripts/done_run.sh` and `scripts/done_sweep_gates_lib.py`; reason: the closeout gates are unchanged; the closeout consumes the receipt through the re-pointed prose, not a new gate.

## Validation Commands

Authoring-time rule 29 record: the no-em-dash scan, the public-hygiene scan, the readiness pre-round invocation, the rule 19 RED-today probes, and the rule 22 mechanical audit (each pinned span exactly once in its owning snippet, plus `bash -n` over this block) run over these bytes before round 1, with outcomes appended below as Recorded lines.

Recorded 2026-10-14 (authoring session sess_9f5841ba, over the v1 bytes on branch authoring/post-landing-reconciliation-enforcement): fix_plan_em_dashes.py 0 substitutions; em-dash touched scan exit 0; public-hygiene scan final line OUTCOME: pass; python3 scripts/plan_readiness.py --pre-round reached OUTCOME: pass on the fourth run (run 1 FAILed on the Review Scope inventory omitting scripts/check_maintenance_pins.sh, added to the inventory in the same pass; runs 2 through 4 FAILed on four over-512-byte acceptance items in Tasks 2 through 4, each split into independently verifiable items in the same pass; two non-blocking warnings stand adjudicated: the 3.5h declared total over the 3.0h advisory cap, kept as the honest estimate per the D-8 round-budget policy, and the files-coverage warnings over quoted invocation strings, runtime-created receipt paths, git refs, the read-only origin row, and the sibling-declared script mention in Task 4, none an undeclared edit target); rule 19 RED-today evidence, run before round 1 over the current tree: scripts/reconcile_post_landing.py --check-primary exits 2 (unrecognized arguments), all three land_squash.sh greps exit 1, the survey-arm grep exits 1, the registry grep exits 1, and all three re-point greps exit 1; both pre-existing suites (scripts.test_reconcile_post_landing, scripts.test_land_squash) pass today, the new fixtures not yet existing; rule 22 mechanical audit PASS (bash -n over this block green; all eight pinned spans extracted and verified at zero occurrences in their target files, the designed RED-today state). Round-start state for r1: the bytes at the fold commit carrying this preamble.

Recorded 2026-10-14, r1 fold re-run (sess_9f5841ba, over the post-fold bytes): the r1 panel's five staged findings folded (F1 removed the phantom plans-skill Final Step surface from Task 4, the Review Scope, the Files list, and the validation block, the plans skill carrying no reconcile sentence to re-point; F2 added the behavioral land-mode happy-path fixture and named both modes in the fault-seam fixture; F3 added the reconcile-gate keep-the-landing routing arm to the template-authoring fail-routing clause and the execute-plan landing class routing sentence, with per-site greps; F4 pinned the sweep's arm test order; F5 added the fresh-mtime witness variant and its fixture arm). Battery over the amended bytes: fix_plan_em_dashes.py 0 substitutions; em-dash touched exit 0; hygiene OUTCOME: pass; plan_delta_classifier.py --since 5a0bcb38b refused the corrections leg on 12 unclassified hunks (the round-launching default taken: a fresh delta round over the fold diff); rule 22 mechanical audit re-run over the new pin geometry (bash -n PASS; the dropped plans re-point pin removed, the two routing-arm pins added at zero occurrences RED-today). Round-start state for r2: the bytes at the fold commit carrying this preamble.

Recorded 2026-10-14, r2 fold re-run (sess_9f5841ba, over the post-fold bytes): the r2 panel's three staged findings folded (F1 rewrote the template-authoring re-point checkbox to prescribe its literal wording, fixing the dangling referent, and corrected the two stale counts in Task 4's RED line and pins-suite checkbox; F2 added the discriminating removals-row grep to the validation block; F3 split the arm-precedence fixture arms into their own item). Battery over the amended bytes: fix_plan_em_dashes.py 0 substitutions; em-dash touched exit 0; hygiene OUTCOME: pass; plan_delta_classifier.py --since ab10a5f84 refused the corrections leg on 4 unclassified hunks (the round-launching default taken); readiness --pre-round OUTCOME: pass after one same-pass item split. Round-start state for r3: the bytes at the fold commit carrying this preamble.

```bash
set -u
fail() { echo "VALIDATION FAIL: $1" >&2; exit 1; }

python3 -m unittest -q scripts.test_reconcile_post_landing || fail "reconcile sweep suite"

python3 -m unittest -q scripts.test_land_squash || fail "land squash suite"

bash scripts/check_maintenance_pins.sh || fail "pins suite"

python3 scripts/reconcile_post_landing.py --check-primary --repo . > /dev/null 2>&1
[ "$?" -le 1 ] || fail "check-primary mode absent or tool failure"

grep -q "Primary-freshness sweep probe" agents/skills/maintenance/survey-arms.md \
  || fail "survey arm bullet missing"

grep -q "duty:primary-freshness-sweep" scripts/machinery_registry.json \
  || fail "registry admission entry missing"

grep -q "co-removal set is the survey arm bullet" scripts/machinery_registry.json \
  || fail "registry removals row missing"

grep -q "reconcile-receipt:" scripts/land_squash.sh || fail "receipt line missing"

grep -q "reconcile-gate" scripts/land_squash.sh || fail "reconcile-gate refusal reason missing"

grep -q "landing-receipts" scripts/land_squash.sh || fail "receipt home missing"

grep -q "already ran this invocation" agents/skills/execute-plan/SKILL.md \
  || fail "execute-plan re-point missing"

grep -q "the receipt the landing tail wrote" agents/skills/maintenance/template-authoring.md \
  || fail "template-authoring re-point missing"

grep -q "reconcile-gate leg" agents/skills/maintenance/template-authoring.md \
  || fail "template-authoring routing arm missing"

grep -q "reconcile-gate leg" agents/skills/execute-plan/SKILL.md \
  || fail "execute-plan routing arm missing"
```

### Task 1: Read-only primary freshness sweep mode

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/reconcile_post_landing.py`
- `scripts/test_reconcile_post_landing.py`

Primary class anchors:
- `sweep_primary` in `scripts/reconcile_post_landing.py`

- [x] [class: IMPLEMENTATION_REQUIRED] Add a `--check-primary` flag to the argument parser that is mutually exclusive with `--base`, `--pre-tip`, and `--post-tip`: a combined invocation is a usage error exiting 2 with zero writes, and a docstring paragraph documents the mode's contract before any other docstring edit.
- [x] [class: IMPLEMENTATION_REQUIRED] In the new `sweep_primary` function, resolve the primary checkout as the first `git worktree list --porcelain` block; when it is mid-merge or mid-rebase (reuse `midflight_witness`), print `note <path> midflight <witness>` and skip classification.
- [x] [class: IMPLEMENTATION_REQUIRED] Enumerate the primary checkout's status entries with `git status --porcelain -z` (reuse the `status_paths` parse shape including rename-pair skipping); skip untracked-only entries; for every remaining path classify read-only per the stale-checkout discriminator: index blob via `ls-files --stage`, worktree blob via `hash-object`, then walk `git log --format=%H HEAD -- <path>` skipping path-absent commits and skipping the HEAD commit itself.
- [x] [class: IMPLEMENTATION_REQUIRED] When a walked ancestor's blob equals the index or worktree bytes, print `stale <path> <matching-commit> <arm>` (the worktree arm is tested before the index arm and a path matching both arms reports the `worktree` row; first match wins per path), stop that path's walk, and never write anything: the mode performs no restore, no remove, no index operation.
- [x] [class: IMPLEMENTATION_REQUIRED] A stale row whose worktree file's mtime postdates the matching ancestor commit's committer time reports witness `fresh-mtime` in the row (read via `os.stat` against the matched commit's `%ct`), mirroring the restore-time contract's primary fresh-mtime bound; the row stays warning-only and the mode still writes nothing.
- [x] [class: REPOSITORY_TEST] Exit codes: 0 when no stale witness was found, 1 when at least one stale row printed, 2 on tool failure; document the three codes in the docstring paragraph beside the invocation form.
- [x] [class: REPOSITORY_TEST] Fixture: the silent working-tree variant: a scratch repo where commit B changes a tracked path, then the primary worktree file is rewritten to commit B's parent's bytes with nothing staged, then HEAD is advanced past B; expect `stale` output naming the path and the parent commit, exit 1, and the file's bytes unchanged after the run.
- [x] [class: REPOSITORY_TEST] Fixtures for the negative arms: worktree bytes matching no ancestor blob produce no stale row and exit 0; an untracked file is skipped; a primary mid-rebase fixture prints the note row and classifies nothing; a fresh-mtime variant (stale bytes with a post-landing mtime) reports the `fresh-mtime` witness.
- [x] [class: REPOSITORY_TEST] Fixtures for the arm-precedence pins: a staged-ancestor variant (index bytes at the parent blob, worktree clean) reports the `index` arm, and a both-arms variant (index and worktree bytes each matching ancestor blobs) reports the `worktree` row per the pinned precedence.
- [x] [class: REPOSITORY_TEST] Run → expect RED: `python3 scripts/reconcile_post_landing.py --check-primary --repo <scratch>` exits 2 today (unrecognized arguments; recorded at authoring time per rule 19), then the mode lands and the suite runs GREEN.
- [x] [class: REPOSITORY_TEST] Run → expect GREEN: the full `scripts/test_reconcile_post_landing.py` suite passes under the validator PATH, with the pre-existing restore-semantics tests untouched and passing.
- [x] [class: IMPLEMENTATION_REQUIRED] Commit: `feat: read-only primary freshness sweep mode for the post-landing reconciler`

### Task 2: Landing tail reconcile gate in both helper modes

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/land_squash.sh`
- `scripts/test_land_squash.py`

Primary class anchors:
- `run_reconcile_gate` in `scripts/land_squash.sh`

- [x] [class: IMPLEMENTATION_REQUIRED] Add a `run_reconcile_gate` helper taking the pre-tip and post-tip: it invokes `python3 "$SCRIPT_DIR/reconcile_post_landing.py" --repo "$REPO_ROOT" --base "$BASE_BRANCH" --pre-tip <pre> --post-tip <post>` capturing stdout and the exit code, and returns the reconcile exit code to the caller.
- [x] [class: IMPLEMENTATION_REQUIRED] The same helper writes the receipt file `docs/tmp/landing-receipts/<post-tip>.txt` under `$REPO_ROOT` (mkdir -p first) containing the command, exit code, and captured rows, then prints `reconcile-receipt: <path>` plus a one-line row summary counting restored, removed, block, wholesale, and synced rows.
- [x] [class: IMPLEMENTATION_REQUIRED] Wire the helper into the `land-worktree` success tails (the normal pass and the origin-leg-only pass, each immediately before its `emit_outcome pass`) with pre-tip the verified `BASE_TIP` and post-tip `LANDING_COMMIT`, while the merge lock is still held.
- [x] [class: IMPLEMENTATION_REQUIRED] Wire the same helper into the `land` mode success tails (both `emit_outcome pass` sites after the post-landing parentage gate) with pre-tip `EXPECTED_TIP_SHA` and post-tip `LANDING_COMMIT`.
- [x] [class: IMPLEMENTATION_REQUIRED] Outcome routing at every wired site: reconcile exit 0 or 1 proceeds (exit 1 first prints every block row and the sanctioned-partial note); exit 2 prints `refuse: reconcile-gate: the post-landing reconciliation failed as a tool failure`, prints the receipt path, prints the remedy line naming the exact re-run command, and ends `emit_outcome fail` with exit 1 while the landed ref stays moved (mirroring the origin-leg-only keep-the-landing arm; the receipt records the failure).
- [x] [class: IMPLEMENTATION_REQUIRED] Add the test-only fault seam `LAND_SQUASH_TEST_FAULT=reconcile-tool-failure` (land-worktree and land): the seam substitutes an unresolvable post-tip value into the helper's reconcile invocation at its single declared point, printing the loud evidence line naming the seam and its env per the existing fault-seam convention.
- [x] [class: REPOSITORY_TEST] Fixture: happy path landing through `land` mode in a scratch repo with a source branch under the lock: expect the receipt gate fires at the land-mode tail, `reconcile-receipt:` prints, the receipt file exists recording exit 0, and OUTCOME is pass.
- [x] [class: REPOSITORY_TEST] Fixture: happy path landing through `land-worktree` in a scratch repo with a second live checkout of the base branch carrying pre-landing bytes: expect the reconcile restores the second checkout, `reconcile-receipt:` prints, the receipt file exists recording exit 0, and OUTCOME is pass.
- [x] [class: REPOSITORY_TEST] Fixture: block-rows path: the second live checkout carries a genuine local edit on a landing path: expect reconcile exit 1, every block row printed, the receipt recording the rows, OUTCOME pass, and the landed ref intact.
- [x] [class: REPOSITORY_TEST] Fixture: fault seam over both modes: `LAND_SQUASH_TEST_FAULT=reconcile-tool-failure` over a land-worktree landing and over a land landing: expect in each OUTCOME fail naming `reconcile-gate`, `refs/heads/<base>` still equal to the landing commit, the receipt recording the failure, and the remedy line present.
- [x] [class: REPOSITORY_TEST] Run → expect RED: today the tails carry no reconcile invocation, so the receipt-line and reconcile-gate greps exit 1 against current `scripts/land_squash.sh` (recorded at authoring time per rule 19), then the tasks land and the suite runs GREEN.
- [x] [class: REPOSITORY_TEST] Run → expect GREEN: the full `scripts/test_land_squash.py` suite passes under the validator PATH with the pre-existing mode and fault-seam tests untouched and passing.
- [x] [class: IMPLEMENTATION_REQUIRED] Commit: `feat: landing tail reconcile receipt gate in both land_squash modes`

### Task 3: Warning-only survey arm and machinery registry rows

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/survey-arms.md`
- `scripts/machinery_registry.json`
- `scripts/check_maintenance_pins.sh`

- [x] [class: IMPLEMENTATION_REQUIRED] Add one bullet to the liveness probe family in `agents/skills/maintenance/survey-arms.md`, titled `Primary-freshness sweep probe`, placed after the Plans-root liveness probe bullet: it runs `python3 scripts/reconcile_post_landing.py --check-primary --repo <repo-root>` once per survey, resolving the script repo-local first then the deployed home copy.
- [x] [class: IMPLEMENTATION_REQUIRED] The same bullet's reporting contract: every `stale` row is a survey finding warning-only (never blocking, never restoring; restoration stays with the landed post-landing contract until promotion), exit 2 is a tool failure recorded report-only, and promotion to blocking runs only through the guard liveness ledger's first true catch with the pre-registered removals row's criteria.
- [x] [class: IMPLEMENTATION_REQUIRED] Append the admission entry `duty:primary-freshness-sweep` to `scripts/machinery_registry.json` entries (shape per the freshest existing entries): disposition keep, kind protocol, and the witness ref pointing at this plan's completed twin once landed.
- [x] [class: IMPLEMENTATION_REQUIRED] The admission entry's admission record names the incident (`docs/history/backlog/2026-10-13-landing-staged-reversal-in-primary-index.md`, witnesses 4 through 6) and the expected catch frequency (every worktree-landed landing whose session skips the prose recipe, four deterministic firings across 2026-10-13/14 plus the silent variant).
- [x] [class: IMPLEMENTATION_REQUIRED] The same admission record names the false-positive cost (one warning line per stale witness; never blocking, never restoring) and the landing posture (warning-only; promotion only through the ledger's first true catch).
- [x] [class: IMPLEMENTATION_REQUIRED] Append the pre-registered removals row `duty:primary-freshness-sweep` to `scripts/machinery_registry.json` removals: the co-removal set is the survey arm bullet, the `--check-primary` mode, its fixtures, and both registry rows; sunset is 90 days from landing or the first promotion decision, whichever first; promotion criteria is a first true catch recorded on the guard liveness ledger.
- [x] [class: REPOSITORY_TEST] Run the pins suite (`bash scripts/check_maintenance_pins.sh`); any pinned-span hit over the touched survey-arms region is reconciled beside its provenance comment in the same edit (grep the pins script for the touched literals first, per rule 41), and the suite exits 0.
- [x] [class: REPOSITORY_TEST] Run → expect RED: both registry greps in the Validation Commands block exit 1 today (the registry carries no `duty:primary-freshness-sweep`; recorded at authoring time per rule 19), then the rows land and the battery runs GREEN.
- [x] [class: IMPLEMENTATION_REQUIRED] Commit: `feat: warning-only primary freshness sweep arm with registry admission rows`

### Task 4: Consumer re-points to the helper-written receipt

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/maintenance/template-authoring.md`

- [x] [class: IMPLEMENTATION_REQUIRED] In the Post-landing reconciliation implementation block of `agents/skills/execute-plan/SKILL.md`, insert one sentence immediately before the invocation fence: when the landing ran through `scripts/land_squash.sh` in either mode, the landing tail already ran this invocation under the merge lock and wrote the receipt its output names (`reconcile-receipt: <path>`).
- [x] [class: IMPLEMENTATION_REQUIRED] The inserted sentence's duty half: the landing session records the receipt path, exit code, and row summary beside the landing record, and re-runs the invocation by hand only as the recovery remedy for a receipt whose recorded run failed (the `reconcile-gate` refusal names the exact command).
- [x] [class: IMPLEMENTATION_REQUIRED] In `agents/skills/maintenance/template-authoring.md`'s self-landing paragraph, insert after the existing reconcile sentence, verbatim: `when the landing ran through scripts/land_squash.sh, the receipt the landing tail wrote satisfies this duty (record its path and row summary; the invocation re-runs by hand only as the recovery remedy)`, so a landed plan's closeout consumes the helper receipt instead of re-running the invocation.
- [x] [class: IMPLEMENTATION_REQUIRED] In the same paragraph's fail-routing clause, insert the reconcile-gate arm after the pre-commit failure path: an `OUTCOME: fail` whose output names the reconcile-gate leg (a post-ref-move reconcile tool failure) takes the keep-the-landing arm instead: the landed ref stands, no pending_landing record is written, and the session records the receipt and the refusal.
- [x] [class: IMPLEMENTATION_REQUIRED] The same arm's completion half: the session re-runs the reconcile command the refusal names and proceeds to the landed-bytes verification and closeout on the valid receipt; the pre-commit failure path stays reserved for pre-ref-move refusals.
- [x] [class: IMPLEMENTATION_REQUIRED] In `agents/skills/execute-plan/SKILL.md`'s landing class routing sentence ("every lane of the class routes solely on the helper's outcome contract"), insert the same reconcile-gate arm: a fail whose output names the reconcile-gate leg is the post-ref-move keep-the-landing arm (the landing stands, the receipt and refusal are recorded, the named re-run command executes).
- [x] [class: IMPLEMENTATION_REQUIRED] The execute-plan arm's completion half: the class's closeout completes on the valid receipt, and the deferred-landing restart path stays reserved for pre-ref-move refusals.
- [x] [class: REPOSITORY_TEST] Run the pins suite; reconcile any pinned-span hit over the two touched surfaces beside its provenance comment in the same edit (rule 41), and the suite exits 0.
- [x] [class: REPOSITORY_TEST] Run → expect RED: the template-authoring re-point grep and the two routing-arm greps in the Validation Commands block exit 1 today against the current skill bytes (recorded at authoring time per rule 19), then the inserts land and the battery runs GREEN.
- [x] [class: IMPLEMENTATION_REQUIRED] Commit: `docs: re-point landing reconcile consumers to the helper receipt`
