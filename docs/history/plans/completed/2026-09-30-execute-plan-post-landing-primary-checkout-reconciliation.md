# Plan: Post-landing primary-checkout reconciliation and stale-checkout discriminator

Backlog origin: docs/history/backlog/2026-09-29-execute-plan-post-landing-primary-checkout-reconciliation.md
Driving force: automation (the landing's reconcile-and-verify loop runs itself from now on, instead of relying on sessions noticing debris; paying witnesses: the two 2026-09-29 landing incidents and the r1 review's dead-arm defect)
Plan review record: the staging series docs/reviews/2026-09-30-plan-review-execute-plan-post-landing-primary-checkout-reconciliation-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Squash landings stop stranding live checkouts of the base branch: every landing finishes with a verified reconciliation of the checkouts the landing made stale, and landing debris left by an earlier landing is mechanically recognizable and restored instead of being misread as an edit.

- After releasing the merge-landing lock, the landing session reconciles every live checkout of the base branch and verifies completion; a partial refresh no longer presents as done (the 17:04 witness rewrote sixteen of seventeen changed paths with no completion check).
- Foreign modifications that block reconciliation produce a recorded named block; the duty never force-resets and never steals a peer's file.
- A working file whose blob equals the path's blob at an ancestor commit is classified a stale-checkout artifact at every dirt-classification site and restored with the restoration recorded, never committed; the hazard that survived two session handoffs on 2026-09-29 as "likely a peer's edit" dies.
- A primary-checkout index sitting byte-identical to a pre-landing tree is recognized wholesale and targeted-restored, never committed as a staged reversal.

## Terms

- **Merge-landing lock**: the repo-keyed sibling of the done lock acquired at every landing critical section (`scripts/done-lock.sh merge-wait-acquire`).
- **Primary checkout**: the checkout holding the repository's common git dir (the first `worktree` line of `git worktree list --porcelain`), where live peer sessions work.
- **Live checkout (of the base branch)**: any checkout in the worktree list whose HEAD symref is the base branch the landing moved, or whose detached HEAD is an ancestor of the landing's post-landing tip.
- **Pre-landing tip / post-landing tip**: the base branch ref's values captured immediately before and after the landing's ref move.
- **Stale-checkout artifact (stale witness)**: a working or staged file whose blob hash equals that path's blob at an ancestor commit while HEAD has advanced past that ancestor; landing debris, never an edit.
- **Named block**: the recorded refusal artifact (blocked checkout, paths, plus blocking witness) produced when foreign modifications stop a reconciliation step; it never implies force; it is recorded in the run's session notes and, repo-keyed, as a pending-landing memory note (the record family the maintenance blueprints define) so the next session reads it instead of re-discovering the dirt.

## Assumptions

- assume the ref-level landing arms (the temp-index squash, the temporary-worktree arm, and the compare-and-swap ref update) move the base branch's ref without writing any working tree, while the checkout-writing arms (the execution blueprint's primary-arm squash and the authoring blueprint's pathspec copy) write the landing's paths in the checkout that holds the base branch; basis: the Worktree-first standard lifecycle step 4 and the maintenance blueprints' landing literals, read on disk 2026-09-30 at main 4e2c2d95.
- assume lesson 6 in docs/maintenance/development_lessons.md owns only the landing-side clobber arm (peer safety at the ref move) and no checkout-side owner exists today; basis: lesson 6 and the lifecycle's six steps plus both named implementations carry nothing about live-checkout freshness (read 2026-09-30).
- assume the p100 machinery-delta doctrine had not landed on main at authoring time, so no origin `Class:` classification and no machinery-delta declaration line are part of this plan; basis: agents/skills/plans/SKILL.md at 4e2c2d95 carries no machinery-delta text (grep 2026-09-30); the doctrine plan file exists but its skill-byte changes are absent from main.
- assume the discriminator's git one-liners behave as documented; basis: authoring-time probe on the authoring worktree plus a scratch-repo fixture run with passing assertions covering both incident arms and the genuine-edit negative case (2026-09-30; the same fixture is G7 in Validation Commands).
- assume prescribed insertions into agents/skills/execute-plan/SKILL.md must stay runtime-neutral; basis: the shared-body forbidden-term gate (test_shared_skill_bodies_remain_runtime_neutral in scripts/test_execute_plan_runtime.py); every prescribed insertion for that file was swept against the gate's term tuple at authoring time and is green in G8.
- assume the maintenance pins suite is green at baseline and its count pins (for example `merge-wait-acquire` exactly twice in prompt-templates.md) must hold after the prescribed edits; basis: scripts/check_maintenance_pins.sh run green 2026-09-30; each task re-keys any pin its span shift breaks in the same edit, and G5 pins the affected counts.
- assume a checkout whose HEAD symref is the base branch already resolves to the moved ref after a ref-level landing, so content sync is a per-path restore concern, never a merge; basis: r1 panel reproduction (three workers, scratch fixtures): `git merge --ff-only` on such a checkout is "Already up to date" while the working file stays stale, and git forbids two worktrees on one branch.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: a post-landing reconciliation implementation and a mechanical stale-checkout discriminator land in the worktree-first canonical lifecycle, the done closeout, and the maintenance landing tails, so landings stop stranding live checkouts with reversal hazards that read as edits (driving force: automation).

Squash landings are ref-level by design: a run lands from its ad-hoc worktree as a temp-index squash under the merge-landing lock, and the ref-level arms move the base branch's ref without writing any working tree. That trade is accepted on the landing side, where lesson 6 owns the clobber arm (integrate the current default tip before building the squash, and attribute every changed path of the landing diff). The checkout side has no owner: after a ref-level landing, every live checkout of the base branch carries stale bytes, nothing in the worktree-first canonical lifecycle, the done closeout, or the maintenance landing tails brings them current, and nothing helps a later session recognize the debris. This plan gives the checkout side an owner inside the canonical section (consumers update by reference per the section's consumer rule) and wires the twice-proven discriminator into the existing dirt-classification sites.

Example 1 (the 17:04 witness): a landing session refreshed the primary checkout by rewriting sixteen of the landing's seventeen changed paths and skipped one. No completion check existed, so the partial refresh presented as done; the stale file then read as an ordinary local modification, survived two session handoffs as "likely a live peer's in-flight edit", and one less careful step would have committed a silent reversal of three landed prose blocks. After this plan, the landing is not done until the reconciliation verifies each landing-changed path carries no diff against the new base tip and no status entry, which that partial refresh fails; the stale path classifies as a stale witness and is restored with a record.

Example 2 (the 20:24 witness): a later landing left the primary checkout's whole index sitting at the pre-landing tree, so `git status` presented a full staged reversal of the landing until manual reconciliation. After this plan, the discriminator's index arm recognizes the signature (empty `git diff --cached <pre-landing-tip>` while HEAD advanced past it) and targeted-restores exactly the landing-changed paths, with the restoration recorded.

The discriminator itself is two read-only git one-liners that proved both incidents: a suspected-modified file whose blob hash (`git hash-object`) equals the path's blob at an ancestor commit (`git rev-parse <commit>:<path>` over `git log --format=%h -- <path>`) is a stale witness, never an edit. It is documented once in the canonical section and consumed by reference at the tracked-dirt inversion check and the done closeout. The reconciliation mechanics live in one script carrier behind a thin invocation recipe, matching the section's sibling implementations, with a hermetic fixture suite covering both witnessed shapes, the genuine-modification refusal, and the negative case.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the discriminator's two arms produce the witnessed classifications with zero false restores, proven by the G7 fixture including its negative case (a genuine edit is never classified stale); the reconciliation script's fixture suite covers both witnessed shapes end to end and asserts the post-state.
- fail-safety: every refusal path records a named block and preserves peer bytes; the prescribed text and the script contain no force-reset and no steal; unstaged and staged peer work on landing-changed paths is preserved and reported.
- machinery economy: the discriminator adds no script; the one new script carrier pays for itself with the executable fixture witness the r1 review required; prose duties land in existing gated files; the pins suite and the shared-body gate stay green.
- integration coherence: lesson 6 and the guard family reference the new duty in their own surfaces; consumers reference the canonical section without restating its rules (the section's consumer rule holds).

**Done when:**
- every gate in Validation Commands exits 0 on the tree after the final task (span pins green, discriminator fixture green with its negative case, reconciliation fixture suite green, suites green, scans clean).

**Ship when:**
- none; the duty takes effect at the next landing after the plan lands (repository-verifiable only).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/execute-plan/SKILL.md` (the Worktree-first standard section: the two new named blocks and the step 4 sentence; the tracked-dirt inversion check's adjudication paragraph; every other region is frozen)
- `agents/skills/done/SKILL.md` (Step 3 item 0c only; every other region is frozen)
- `agents/skills/maintenance/prompt-templates.md` (the three landing-tail sentences (authoring, execution, unblock) only; every other region is frozen, and the pins suite gates the file)
- `docs/maintenance/development_lessons.md` (the lesson 6 checkout-side sibling line only)
- `scripts/reverse_squash_guard.py` (module docstring only; all logic is frozen)
- `scripts/reconcile_post_landing.py` *(new)*

**Tests:**
- `scripts/test_reconcile_post_landing.py` *(new; the reconciliation fixture suite)*

The suites this plan must keep green are the ones Validation Commands runs: the shared-body gate, the maintenance pins suite, the em-dash and hygiene scans, the discriminator fixture (G7), and the new reconciliation fixture suite; the readiness validator runs at the done boundary, not in this block.

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- a dedicated stale-checkout detector script as the discriminator's carrier; reason: this plan's design of record from the r1 fold (the discriminator is two read-only git one-liners, witnessed by G7; see Design Invariants); the reconciliation carrier script is the separate, witnessed deliverable.
- `agents/skills/execute-plan/runtime-contract.md` and `scripts/execute_plan_runtime.py`; reason: no runtime behavior changes; the duties bind landing and closeout sessions, not driver code.
- `agents/skills/execute-plan/subagent-prompts.md`, `agents/skills/execute-plan/agent-logs.md`, `agents/skills/plans/SKILL.md`; reason: shared-body neighbors this plan does not touch.

## Design Invariants (CR Guard)

- Ref-level landings stay. The plan must not mandate checked-out merges on the primary (lesson 6 fixed the landing-side danger more cheaply; reintroducing checkout serialization is the origin's rejected alternative).
- Never force-reset, never steal. A live checkout's local modifications belong to whoever made them; both witnessed incidents had a peer staged in the primary checkout while the debris sat there. Every restore is gated per path on discriminator evidence, and a session-owned ancestor-blob match is reported for confirmation, never auto-restored.
- Machinery carries its witness. The discriminator stays two read-only git one-liners in prose (this plan's design of record from the r1 fold: the origin documents the discriminator as exactly the two read-only one-liners, and G7 is its witness). The reconciliation mechanics live in one script carrier (`scripts/reconcile_post_landing.py`) behind the thin-recipe shape of the section's sibling implementations (`worktree_closeout_migrate.py`, `reverse_squash_guard.py`), because a prose recipe is what hid the r1 review's dead-arm defect (an unreachable repair primitive every grep gate scored green); the fixture suite is the paying witness.
- Lifecycle numbering is frozen. The Worktree-first standard's steps 1 through 6 keep their numbers and every cross-reference to them; new duties join as named implementation blocks beside the existing ones.
- Consumers reference, never restate. The Worktree-first standard section's consumer rule ("consumer skills reference it, they do not restate it") governs the done skill and the maintenance payloads: they carry reference sentences and bounded disposition summaries, not copied rule text.

## Validation Commands

```bash
#!/usr/bin/env bash
# Run from the repository root after all tasks land. Exit non-zero on the first failed gate.
set -u
E=agents/skills/execute-plan/SKILL.md
D=agents/skills/done/SKILL.md
P=agents/skills/maintenance/prompt-templates.md
L=docs/maintenance/development_lessons.md
G=scripts/reverse_squash_guard.py
R=scripts/reconcile_post_landing.py
T=scripts/test_reconcile_post_landing.py
fail() { echo "VALIDATION FAIL: $1"; exit 1; }
count() { grep -oF "$2" "$1" | wc -l | tr -d ' '; }

# G1 canonical discriminator (Task 1)
[ "$(count "$E" 'Stale-checkout discriminator (before any dirt is classified)')" -eq 1 ] || fail "G1a block heading"
[ "$(count "$E" 'is a stale-checkout artifact, never an edit, exactly when its blob hash equals')" -eq 1 ] || fail "G1b stale definition"
[ "$(count "$E" 'restore-and-record: restore the file'"'"'s worktree bytes from the base tip (the index is never written by this arm), record the restoration, and never commit the stale bytes')" -eq 1 ] || fail "G1c restore arm"
[ "$(count "$E" 'a supporting signal, not the gate')" -eq 1 ] || fail "G1d mtime signal"
[ "$(count "$E" 'never commit, never blanket-reset')" -eq 1 ] || fail "G1e index arm disposition"
[ "$(count "$E" 'reported for confirmation instead of auto-restored')" -eq 1 ] || fail "G1f attribution bound"
[ "$(count "$E" 'the restore materializes and removes as the post-tip dictates')" -eq 1 ] || fail "G1g add/delete arms"
[ "$(count "$E" 'only when its index AND worktree bytes both equal the path'"'"'s blob at an ancestor commit')" -eq 1 ] || fail "G1h canonical gating rule"

# G2 canonical reconciliation implementation (Task 2)
[ "$(count "$E" 'Post-landing reconciliation implementation (how step 4 finishes)')" -eq 1 ] || fail "G2a block heading"
[ "$(count "$E" 'the landing is not done until that reconciliation verifies completion')" -eq 1 ] || fail "G2b step 4 sentence"
[ "$(count "$E" 'reconcile every live checkout of the base branch')" -eq 1 ] || fail "G2c duty sentence"
[ "$(count "$E" 'as a pending-landing memory note')" -eq 1 ] || fail "G2d named block surface"
[ "$(count "$E" 'never force-resets a genuine modification and never steals a peer'"'"'s file')" -eq 1 ] || fail "G2e refusal disposition"
[ "$(count "$E" 'rewrote sixteen of seventeen changed paths and presented as done')" -eq 1 ] || fail "G2f partial-refresh witness"
[ "$(count "$E" 'scripts/reconcile_post_landing.py')" -eq 2 ] || fail "G2g script invocation present"
[ "$(count "$E" '.ai-playbook/scripts/reconcile_post_landing.py')" -eq 1 ] || fail "G2g2 runtime-home fallback present"
[ "$(count "$E" 'exit 2 = tool failure')" -eq 1 ] || fail "G2h exit contract"
[ "$(count "$E" 'on lock contention stand down keeping the worktree and branch and report). After releasing the lock')" -eq 1 ] || fail "G2i step-4 tail preserved"

# G2j lifecycle numbering freeze (steps keep their headings exactly once each)
[ "$(count "$E" '1. **Create the worktree.**')" -eq 1 ] || fail "G2j step1"
[ "$(count "$E" '2. **Transfer the inputs in.**')" -eq 1 ] || fail "G2j step2"
[ "$(count "$E" '3. **Do the work there.**')" -eq 1 ] || fail "G2j step3"
[ "$(count "$E" '4. **Land under the lock.**')" -eq 1 ] || fail "G2j step4"
[ "$(count "$E" '5. **Transfer the artifacts out and verify.**')" -eq 1 ] || fail "G2j step5"
[ "$(count "$E" '6. **Delete only after verification.**')" -eq 1 ] || fail "G2j step6"

# G3 inversion-check adjudication (Task 3)
[ "$(count "$E" 'Stale-checkout adjudication (guard refusal and classification)')" -eq 1 ] || fail "G3a adjudication heading"
[ "$(count "$E" 'cannot tell a stale witness from a genuine reversal')" -eq 1 ] || fail "G3b guard division of labor"
[ "$(count "$E" 'reported for the operator'"'"'s confirmation rather than auto-restored')" -eq 1 ] || fail "G3c inversion-site attribution bound"

# G4 done closeout arm (Task 4)
[ "$(count "$D" '0c. **Stale-checkout adjudication (before any disposition).**')" -eq 1 ] || fail "G4a item 0c"
[ "$(count "$D" 'landing debris, restored from the base tip with the restoration recorded, never staged, never committed, never reported as peer work')" -eq 1 ] || fail "G4b debris classification"
[ "$(count "$D" 'is never auto-restored: report it for confirmation instead')" -eq 1 ] || fail "G4c attribution bound"
[ "$(count "$D" 'passes item 1'"'"'s dirt regression gate vacuously')" -eq 1 ] || fail "G4d gate precedence"

# G5 maintenance landing tails (Task 5)
[ "$(count "$P" 'reconcile live checkouts of the base branch per the post-landing reconciliation implementation')" -eq 3 ] || fail "G5a three landing-tail references"
[ "$(count "$P" 'merge-wait-acquire')" -eq 2 ] || fail "G5b lock literal count"
[ "$(count "$P" 'then delete the authoring branch and worktree;')" -eq 1 ] || fail "G5c authoring tail"
[ "$(count "$P" 'the landing closeout ends only when that reconciliation is verified or a named block is recorded')" -eq 1 ] || fail "G5d execution tail"

# G6 integration points (Task 6)
[ "$(count "$L" 'live-checkout freshness after the move is owned by the post-landing reconciliation implementation')" -eq 1 ] || fail "G6a lesson 6 sibling"
[ "$(count "$G" 'stale-checkout discriminator in the Worktree-first standard section')" -eq 1 ] || fail "G6b guard docstring"
python3 -m py_compile "$G" || fail "G6c guard compiles"

# G7 discriminator fixture: both witnessed arms, the negative case, hermetic, always torn down
FIX="$(mktemp -d "${TMPDIR:-/tmp}/p102-discriminator.XXXXXX")" || fail "G7 mktemp"
trap 'rm -rf "$FIX"' EXIT
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null GIT_CONFIG_NOSYSTEM=1
git -c init.defaultBranch=main init -q "$FIX/repo"
git -C "$FIX/repo" config user.email fixture@example.com
git -C "$FIX/repo" config user.name fixture
git -C "$FIX/repo" config commit.gpgsign false
printf 'landed v1\n' > "$FIX/repo/skill.md"
git -C "$FIX/repo" add skill.md
git -C "$FIX/repo" commit -qm v1
PRE="$(git -C "$FIX/repo" rev-parse HEAD)"
printf 'landed v2\n' > "$FIX/repo/skill.md"
git -C "$FIX/repo" add skill.md
git -C "$FIX/repo" commit -qm v2
git -C "$FIX/repo" show "${PRE}:skill.md" > "$FIX/repo/skill.md"
W="$(git -C "$FIX/repo" hash-object "$FIX/repo/skill.md")"
H="$(git -C "$FIX/repo" rev-parse 'HEAD:skill.md')"
A="$(git -C "$FIX/repo" rev-parse "${PRE}:skill.md")"
[ "$W" = "$A" ] && [ "$W" != "$H" ] || fail "G7 arm1 stale witness not detected"
git -C "$FIX/repo" restore skill.md
[ "$(git -C "$FIX/repo" hash-object "$FIX/repo/skill.md")" = "$H" ] || fail "G7 arm1 restore"
printf 'a genuine new edit\n' > "$FIX/repo/skill.md"
W2="$(git -C "$FIX/repo" hash-object "$FIX/repo/skill.md")"
[ "$W2" != "$A" ] && [ "$W2" != "$H" ] || fail "G7 negative case setup"
[ -z "$(git -C "$FIX/repo" rev-list --objects HEAD -- skill.md | cut -d' ' -f1 | grep -F "$W2")" ] || fail "G7 negative case: new blob is an ancestor blob"
git -C "$FIX/repo" read-tree "$PRE"
[ -z "$(git -C "$FIX/repo" diff --cached "$PRE")" ] || fail "G7 arm2 index signature"
git -C "$FIX/repo" diff --cached --name-only HEAD | grep -q skill.md || fail "G7 arm2 staged reversal visible"
git -C "$FIX/repo" restore --source=HEAD --staged --worktree -- skill.md
[ -z "$(git -C "$FIX/repo" diff --cached HEAD)" ] || fail "G7 arm2 restore"

# G8 shared-body runtime neutrality (insertions into execute-plan SKILL.md)
python3 scripts/test_execute_plan_runtime.py ExecutePlanRuntimeTest.test_shared_skill_bodies_remain_runtime_neutral || fail "G8 shared-body gate"

# G9 maintenance pins suite (all blueprints and pinned spans)
bash scripts/check_maintenance_pins.sh || fail "G9 pins suite"

# G10 reconciliation fixture suite (the script's executable witness)
python3 "$T" || fail "G10 reconciliation fixture suite"

# G11 em-dash: the scanner's file mode covers the prose files; the python files get a direct byte check
bash scripts/check-no-em-dash.sh file "$E" "$D" "$P" "$L" || fail "G11a em-dash prose files"
EMDASH="$(printf '\342\200\224')"
if grep -qF "$EMDASH" "$G" "$R" "$T"; then fail "G11b em-dash python files"; fi

# G12 public hygiene scan in explicit files mode (the scanner's exclusion of the done
# skill file is a pre-existing scanner behavior; G11a still covers that file)
bash scripts/scan-public-hygiene.sh --files "$E" "$P" "$L" "$R" "$T" || fail "G12 hygiene"

echo "ALL P102 VALIDATION GATES GREEN"
exit 0
```

### Task 1: canonical stale-checkout discriminator

Files:
- `agents/skills/execute-plan/SKILL.md`

Insert immediately before the line `**Transfer-out-and-deletion implementation (how steps 5 and 6 run):**` (the anchor line is unique in the file today):

**Stale-checkout discriminator (before any dirt is classified):** a suspected-modified tracked file is a stale-checkout artifact, never an edit, exactly when its blob hash equals that path's blob at an ancestor commit while HEAD has advanced past that ancestor: compute the file's blob (`git hash-object <file>`) and compare it against the path's blob at ancestor commits (`git rev-parse <commit>:<path>` over `git log --format=%h -- <path>`, skipping commits where the path does not exist, a deletion or rename-source commit, rather than treating the failure as a match or a tool failure). An ancestor-blob match means restore-and-record: restore the file's worktree bytes from the base tip (the index is never written by this arm), record the restoration, and never commit the stale bytes; the file's mtime predating the commits it reverses is a supporting signal, not the gate. The index arm is wholesale: when a checkout's index sits byte-identical to a pre-landing tree (`git diff --cached <pre-landing-tip>` coming back empty while HEAD has advanced past the pre-landing tip), the staged state presents a reversal block of the whole landing. The remediation is gated per path, and this block is the rule's single home: restore a landing-changed path from the base tip (`git restore --source=<base-tip> --staged --worktree --` that one path) only when its index AND worktree bytes both equal the path's blob at an ancestor commit (the pre-landing tip's blob or any older ancestor), or when its worktree bytes equal the base tip while its index bytes equal an ancestor blob (a half-synced residue; the restore clears the index without changing the worktree bytes), or when its worktree bytes equal an ancestor blob while its index bytes equal the base tip (the wholesale residue a mixed reset leaves; the worktree-only restore clears it and the index is untouched), re-reading both byte states immediately before the restore in any arm; a path whose bytes match no ancestor blob in either state is a genuine modification and a named block, never restored; record the restoration or the block, and never commit, never blanket-reset. Where the classifying site carries session attribution (the done closeout's owned-path claims), a session-owned ancestor-blob match is reported for confirmation instead of auto-restored. The discriminator runs before any dirt is classified at every site that consumes this standard (the tracked-dirt inversion check below, the done skill's closeout classification, the post-landing reconciliation implementation in this section): a stale witness found at any of them takes the restore-and-record arm instead of being left as unexplained dirt. The class includes a landing-added path absent in the checkout and a landing-deleted path carrying only pre-landing bytes: the restore materializes and removes as the post-tip dictates.

Evidence:
- `grep -oF 'Stale-checkout discriminator (before any dirt is classified)' agents/skills/execute-plan/SKILL.md | wc -l` equals 1 after the edit; covers the block heading pin
- `bash scripts/check-no-em-dash.sh file agents/skills/execute-plan/SKILL.md`; covers the no-em-dash gate on the touched file
- `python3 scripts/test_execute_plan_runtime.py ExecutePlanRuntimeTest.test_shared_skill_bodies_remain_runtime_neutral`; covers the shared-body gate after the insertion
- `bash scripts/check_maintenance_pins.sh`; covers pin integrity after the insertion

- [x] Insert the block above verbatim at the named anchor; expect the eight G1 spans (G1a through G1h) present exactly once each afterward [class: IMPLEMENTATION_REQUIRED]
- [x] Run the task's Evidence commands; expect all green, and the G1 set green when the final Validation block runs [class: REPOSITORY_TEST]
- [x] Commit: `skills: add canonical stale-checkout discriminator to the worktree-first standard` [class: IMPLEMENTATION_REQUIRED]

### Task 2: post-landing reconciliation script and canonical implementation

Files:
- `scripts/reconcile_post_landing.py` *(new)*
- `scripts/test_reconcile_post_landing.py` *(new)*
- `agents/skills/execute-plan/SKILL.md`

Edit 1: create `scripts/reconcile_post_landing.py`. The script carries the reconciliation mechanics behind this contract:

- Invocation: `python3 scripts/reconcile_post_landing.py --base <branch> --pre-tip <sha> --post-tip <sha> [--repo ROOT]`, run by the landing session after the merge-landing lock release.
- Resolve every checkout from `git worktree list --porcelain` whose HEAD symref is `--base` or whose detached HEAD is an ancestor of `--post-tip`; skip unrelated checkouts.
- Tip guard first: when `refs/heads/<base>` no longer equals `--post-tip`, a newer landing owns the checkouts; emit block rows for the live checkouts (one per checkout), naming the newer landing, write nothing anywhere, exit 1. Re-check the tip immediately before the restore phase; a mismatch maps to the newer-landing block rows and exit 1.
- A checkout mid-merge or mid-rebase (`MERGE_HEAD`, `rebase-merge`, or `rebase-apply` in its git dir) is a block row; write nothing in it.
- A detached checkout genuinely behind the post-landing tip is fast-forwarded with `git merge --ff-only`; a refusal is a block row, never force.
- The wholesale index signature (`git diff --cached <pre-tip>` empty while HEAD holds the post-landing tip) is recorded as the wholesale recognition line; remediation is still per path.
- For each landing-changed path (`git diff --name-only <pre-tip> <post-tip>`), classify from the path's byte states at the two tips and in the checkout. A path absent in the checkout and absent at `--pre-tip` (the landing added it) is a stale witness: materialize it from the post-tip. A path present in the checkout whose bytes equal the pre-landing blob while the path is absent at `--post-tip` (the landing deleted it) is a stale witness: the same restore removes it. A path present at both tips is synced when the checkout's index AND worktree bytes both equal the post-tip blob; it is a stale witness only when its index AND worktree bytes both equal the path's blob at an ancestor commit (the discriminator's own walk: the pre-landing tip's blob or any older ancestor, `git rev-parse <commit>:<path>` over `git log --format=%H -- <path>`, skipping commits where the path does not exist, a deletion or rename-source commit, never a tool failure), restored from the post-tip with the single-path restore (`git restore --source=<post-tip> --staged --worktree --` that one path, subprocess argument list, no shell), re-reading both byte states immediately before the restore so a mid-window change re-classifies; a landing-changed path whose worktree bytes equal the post-tip blob while its index bytes equal an ancestor blob is a stale-witness residue, completed by the single-path restore from the post-tip, which clears the index without changing worktree bytes; a landing-changed path whose worktree bytes equal an ancestor blob while its index bytes equal the post-tip blob is the wholesale residue a mixed reset leaves, restored worktree-only from the post-tip with the index untouched; any other byte state, including a matching index with a differing worktree, is a genuine modification and a block row, never restored. This classification implements the canonical gating rule the Task 1 block states; where the two texts could ever disagree, the canonical block wins and this contract is corrected in the same edit.
- In the checkout holding the common git dir (the primary), an ancestor-blob match whose worktree file mtime postdates the pre-landing tip's commit time is a block row carrying that witness instead of an auto-restore (a peer touched the path after the landing); other resolved live checkouts auto-restore freely; the bound applies only at the checkout holding the common git dir.
- Output one line per row (`restored <checkout> <path>`, `block <checkout> <path> <witness>`, `wholesale <checkout>`, `synced <checkout>`); exit 0 when every live checkout is verified complete, exit 1 when block rows exist (the caller records them as named blocks), exit 2 on tool failure; a `--base`, `--pre-tip`, or `--post-tip` value git cannot resolve is exit 2 with zero writes, never a silent pass.

Edit 2: create `scripts/test_reconcile_post_landing.py`, a hermetic unittest suite (fixtures under `mktemp -d`, nulled `GIT_CONFIG_GLOBAL` and `GIT_CONFIG_SYSTEM`, `commit.gpgsign false`, `user.email` and `user.name` pinned, teardown on all paths) with at least these cases, each in given/expects form:

- `test_stale_primary_restored_and_recorded`; given a ref-level landing whose primary checkout carries two landing-changed paths, one stale (its mtime backdated to predate the pre-landing tip's commit time) and one already carrying post-tip bytes in both byte states, expects exit 0, the stale path restored to the post-tip content, a `restored` row, and a `synced` row for the current path.
- `test_landing_added_path_materialized`; given a ref-level landing adding one path and an untouched primary checkout, expects exit 0, the file present at post-tip content, and a `restored` row.
- `test_landing_deleted_path_removed`; given a landing deleting one path still present with pre-landing bytes in the checkout (its mtime backdated to predate the pre-landing tip's commit time when sited in the primary), expects exit 0 and the path removed.
- `test_wholesale_index_signature_targeted_restore`; given the index sitting at the pre-landing tree (stale-path mtimes backdated to predate the pre-landing tip's commit time), expects the `wholesale` recognition line and per-path restores ending clean.
- `test_genuine_modification_blocked_not_restored`; given a landing-changed path carrying new content matching no pre-landing blob, expects exit 1 with a `block` row and the peer bytes preserved byte-for-byte.
- `test_detached_ancestor_fast_forwarded`; given a detached checkout at the pre-landing tip, expects it fast-forwarded to the post-landing tip.
- `test_dirty_detached_ff_refusal_blocked`; given a detached ancestor checkout with a local modification on a landing-changed path, expects a block row and the bytes preserved.
- `test_mid_merge_checkout_blocked`; given a checkout with `MERGE_HEAD` present, expects a block row and zero writes to that checkout.
- `test_rebase_state_blocked`; given a checkout with `rebase-merge` present in its git dir, expects a block row and zero writes to that checkout.
- `test_older_ancestor_stale_restored`; given a checkout whose landing-changed path carries, in both byte states, a blob from an ancestor older than the pre-landing tip, expects a `restored` row and exit 0.
- `test_half_synced_index_stale_restored`; built in the standard fixture repo harness; given the worktree at post-tip bytes and the index at an ancestor blob on a landing-changed path, expects a `restored` row, the worktree bytes unchanged, and exit 0.
- `test_pre_restore_tip_move_blocks`; driven in-process: given classification started against `--post-tip` and `refs/heads/<base>` moved before the restore phase, expects the restore phase to map to the newer-landing block rows and exit 1 with zero writes.
- `test_delete_readd_history_restored`; given a landing-changed path whose history deletes and re-adds it and a checkout carrying the pre-deletion blob in both byte states, expects a `restored` row and exit 0.
- `test_unrelated_checkout_untouched`; given a second worktree on an unrelated branch carrying local dirt, expects no rows for it and a byte-identical status after the run.
- `test_base_moved_guard_blocks_without_writes`; given `refs/heads/<base>` no longer equal to `--post-tip`, expects block rows naming the newer landing and zero writes anywhere.
- `test_tool_failure_maps_to_exit_2`; given a `--pre-tip` value git cannot resolve in a live fixture repo, expects exit 2 and zero writes.
- `test_index_stale_worktree_peer_edit_blocked`; given the index left at the pre-landing blob and the worktree carrying the peer's unstaged edit, expects a block row and both byte states preserved.
- `test_worktree_stale_index_peer_staged_blocked`; given the worktree at the pre-landing blob and the index carrying the peer's staged edit, expects a block row and both byte states preserved.
- `test_primary_reverted_path_with_fresh_mtime_blocked`; given the primary checkout holding an ancestor-blob match whose file mtime postdates the pre-landing tip's commit time, expects a block row instead of an auto-restore and the bytes preserved.
- `test_midwindow_change_reclassifies`; driven in-process against the module: given classification of a stale path followed by a mutation of the path's bytes before the re-read, expects the restore to abort to a block row.

Edit 3: extend lifecycle step 4. The step's current text ends with the exact span `on lock contention stand down keeping the worktree and branch and report).` (unique); append immediately after that span, before the line's end: ` After releasing the lock, reconcile every live checkout of the base branch per the **Post-landing reconciliation implementation** below; the landing is not done until that reconciliation verifies completion, and an unverified refresh does not count as done.`

Edit 4: insert the block below immediately after the line ending `the restore materializes and removes as the post-tip dictates.` (the discriminator block's tail as Task 1 inserts it, so the reconciliation implementation sits between the discriminator and the Transfer-out-and-deletion implementation):

**Post-landing reconciliation implementation (how step 4 finishes):** the ref-level landing arms move the base branch's ref without writing any working tree, so the moment the landing lands, every live checkout of that branch carries stale bytes; the checkout-writing arms write the landing's paths themselves, which the per-path checks below handle correctly. After releasing the merge-landing lock, the landing session reconciles every live checkout of the base branch. Run from the primary checkout or pass its path via `--repo` (resolved from the worktree list, never from the session's cwd; the run worktree may already be scheduled for removal or gone):

```bash
RECON_REPO="<the primary checkout's path, the first worktree line>"
BASE_BRANCH="<the base branch the landing moved>"
PRE_TIP="<the base branch ref's value captured before the landing's ref move>"
POST_TIP="<the base branch ref's value after the landing's ref move>"
RECONCILE_SCRIPT="${RECONCILE_SCRIPT:-$(git -C "$RECON_REPO" rev-parse --show-toplevel)/scripts/reconcile_post_landing.py}"
[ -f "$RECONCILE_SCRIPT" ] || RECONCILE_SCRIPT="${HOME}/.ai-playbook/scripts/reconcile_post_landing.py"
python3 "$RECONCILE_SCRIPT" --repo "$RECON_REPO" \
  --base "$BASE_BRANCH" --pre-tip "$PRE_TIP" --post-tip "$POST_TIP"
```

Completion is verified, not assumed: exit 0 means every live checkout of the base branch was verified current (each path the landing changed carries no diff against the new base tip and no status entry); exit 1 means the reconciliation completed with named blocks: record every block row in the run's session notes and, repo-keyed, as a pending-landing memory note (the record family the maintenance blueprints define in agents/skills/maintenance/prompt-templates.md), so the next session reads the paths plus witness instead of re-discovering the dirt; exit 2 = tool failure, stop and report without writing further. The 2026-09-29 17:04 witness rewrote sixteen of seventeen changed paths and presented as done exactly because no completion check existed. Every restore is per path and discriminator-gated: the reconciliation never force-resets a genuine modification and never steals a peer's file. Integration: lesson 6 (`docs/maintenance/development_lessons.md`) owns peer safety at the ref move; this implementation owns live-checkout freshness; the tracked-dirt inversion check below owns the run-worktree side at closeout.

Evidence:
- `grep -oF 'the landing is not done until that reconciliation verifies completion' agents/skills/execute-plan/SKILL.md | wc -l` equals 1; covers the step 4 sentence pin
- `grep -oF 'Post-landing reconciliation implementation (how step 4 finishes)' agents/skills/execute-plan/SKILL.md | wc -l` equals 1; covers the block heading pin
- `python3 scripts/test_reconcile_post_landing.py`; covers the script's fixture suite green at this task boundary
- `bash scripts/check-no-em-dash.sh file agents/skills/execute-plan/SKILL.md`; covers the no-em-dash gate
- `python3 scripts/test_execute_plan_runtime.py ExecutePlanRuntimeTest.test_shared_skill_bodies_remain_runtime_neutral`; covers the shared-body gate
- `bash scripts/check_maintenance_pins.sh`; covers pin integrity

- [x] Create the fixture suite with the given/expects cases below, hermetic with teardown on all paths [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: `python3 scripts/test_reconcile_post_landing.py` fails because the script module does not exist yet [class: REPOSITORY_TEST]
- [x] Create `scripts/reconcile_post_landing.py` with the stated contract; every contract bullet is observable in its behavior or output [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/test_reconcile_post_landing.py` exits 0 [class: IMPLEMENTATION_REQUIRED]
- [x] Apply edit 3 with the exact quoted span and appended sentence; the span's tail (end of the numbered line) survives verbatim [class: IMPLEMENTATION_REQUIRED]
- [x] Apply edit 4 at the named anchor so the block sits between the discriminator and the Transfer-out-and-deletion implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run the task's Evidence commands; expect all green [class: REPOSITORY_TEST]
- [x] Commit: `skills: add post-landing reconciliation script and canonical implementation` [class: IMPLEMENTATION_REQUIRED]

### Task 3: tracked-dirt inversion check adjudication

Files:
- `agents/skills/execute-plan/SKILL.md`

Insert the paragraph below immediately before the line `**Fail-closed stand-downs:**` (unique in the file today), so it sits directly after the tracked-dirt inversion check's fenced recipe:

**Stale-checkout adjudication (guard refusal and classification):** the reverse-squash guard refuses inversion content wholesale and cannot tell a stale witness from a genuine reversal; before any manual move, removal, or classification decision on tracked dirt at this check, run the stale-checkout discriminator above on each suspected-modified entry: an ancestor-blob match is landing debris, restored from the base tip with the restoration recorded, never transplanted and never committed, except that a path the run's own records claim is reported for the operator's confirmation rather than auto-restored; an index byte-identical to a pre-landing tree is the wholesale reversal signature, remediated under the discriminator's per-path gate (restore per the gate's arms, or a named block); anything else keeps the refusal's disposition unchanged.

Evidence:
- `grep -oF 'Stale-checkout adjudication (guard refusal and classification)' agents/skills/execute-plan/SKILL.md | wc -l` equals 1; covers the adjudication heading pin
- `bash scripts/check-no-em-dash.sh file agents/skills/execute-plan/SKILL.md`; covers the no-em-dash gate
- `python3 scripts/test_execute_plan_runtime.py ExecutePlanRuntimeTest.test_shared_skill_bodies_remain_runtime_neutral`; covers the shared-body gate
- `bash scripts/check_maintenance_pins.sh`; covers pin integrity

- [x] Insert the paragraph verbatim at the named anchor [class: IMPLEMENTATION_REQUIRED]
- [x] Run the task's Evidence commands; expect all green [class: REPOSITORY_TEST]
- [x] Commit: `skills: wire the stale-checkout discriminator into the tracked-dirt inversion check` [class: IMPLEMENTATION_REQUIRED]

### Task 4: done closeout dirt classification arm

Files:
- `agents/skills/done/SKILL.md`

Replace the exact span `1. Run `git status` and `git diff` (staged + unstaged) to see all changes.` (unique in the file today) with the new item 0c followed by that same line verbatim as the tail:

0c. **Stale-checkout adjudication (before any disposition).** Before item 1's gates and item 1a's ladder classify any uncommitted modification, apply the stale-checkout discriminator (the Worktree-first standard section in agents/skills/execute-plan/SKILL.md): a tracked file whose blob equals that path's blob at an ancestor commit is landing debris, restored from the base tip with the restoration recorded, never staged, never committed, never reported as peer work; an index byte-identical to a pre-landing tree is remediated under the discriminator's per-path gate: a landing-changed path is remediated per the gate's arms (restore, or a named block; the pre-landing tip resolves from the landing's recorded tips or the base branch's reflog entry preceding the landing commit). A path this session's own records claim (an `--owned-path` claim or session attribution) is never auto-restored: report it for confirmation instead. A path this arm restored passes item 1's dirt regression gate vacuously; the gate keeps hunk-level regressions on the paths this arm leaves. A pre-commit sweep-gate failure (instruction-size, em-dash) naming a path this arm has not yet classified is never remedied by the gate's content fix: run this arm's classification on the named path first, then apply the gate guidance to whatever the arm leaves.

Evidence:
- `grep -oF '0c. **Stale-checkout adjudication (before any disposition).**' agents/skills/done/SKILL.md` equals 1; covers the item pin
- `bash scripts/check-no-em-dash.sh file agents/skills/done/SKILL.md`; covers the no-em-dash gate
- `bash scripts/check_maintenance_pins.sh`; covers pin integrity (the pins suite gates this file)

- [x] Apply the replacement with the exact quoted span and keep the tail line verbatim; item 0c sits after item 0 and before item 1 [class: IMPLEMENTATION_REQUIRED]
- [x] Run the task's Evidence commands; expect all green [class: REPOSITORY_TEST]
- [x] Commit: `done: restore stale-checkout witnesses at closeout before any disposition` [class: IMPLEMENTATION_REQUIRED]

### Task 5: maintenance blueprint landing tails

Files:
- `agents/skills/maintenance/prompt-templates.md`

Edit 1 (authoring blueprint): replace the exact span `after that release, delete the authoring branch and worktree;` (unique today) with: `after that release, reconcile live checkouts of the base branch per the post-landing reconciliation implementation in the Worktree-first standard section of agents/skills/execute-plan/SKILL.md (fast-forward plus verified completion, named-block refusal, stale-witness restore-and-record), then delete the authoring branch and worktree;` (the replacement's tail, `delete the authoring branch and worktree;`, survives verbatim inside the replacement).

Edit 2 (execution blueprint): replace the exact span `release the lock only after the branch is deleted.` (unique today) with: `release the lock only after the branch is deleted. After the release, reconcile live checkouts of the base branch per the post-landing reconciliation implementation in the Worktree-first standard section of agents/skills/execute-plan/SKILL.md (fast-forward plus verified completion, named-block refusal, stale-witness restore-and-record); the landing closeout ends only when that reconciliation is verified or a named block is recorded.` (the following sentence beginning `If any release` survives verbatim after the replacement).

Edit 3 (unblock template): replace the exact span `7. On a verified landing: record the landing's squash commit sha as the entry's` (unique today) with: `7. On a verified landing: after the landing's critical section, reconcile live checkouts of the base branch per the post-landing reconciliation implementation in the Worktree-first standard section of agents/skills/execute-plan/SKILL.md (fast-forward plus verified completion, named-block refusal, stale-witness restore-and-record), then record the landing's squash commit sha as the entry's` (the tail `record the landing's squash commit sha as the entry's` survives verbatim inside the replacement).

All three sentences reference the canonical implementation per the section's consumer rule; none restates lifecycle steps, and none adds a `merge-wait-acquire` literal (its count stays exactly 2).

Evidence:
- `grep -oF 'reconcile live checkouts of the base branch per the post-landing reconciliation implementation' agents/skills/maintenance/prompt-templates.md | wc -l` equals 3; covers the three landing-tail references (authoring, execution, unblock)
- `grep -oF 'merge-wait-acquire' agents/skills/maintenance/prompt-templates.md | wc -l` equals 2; covers the pins-suite count pin
- `bash scripts/check_maintenance_pins.sh`; covers pin integrity after both edits
- `bash scripts/check-no-em-dash.sh file agents/skills/maintenance/prompt-templates.md`; covers the no-em-dash gate

- [x] Apply edit 1 with the exact quoted span and replacement [class: IMPLEMENTATION_REQUIRED]
- [x] Apply edit 2 with the exact quoted span and replacement [class: IMPLEMENTATION_REQUIRED]
- [x] Apply edit 3 with the exact quoted span and replacement [class: IMPLEMENTATION_REQUIRED]
- [x] Run the task's Evidence commands; expect all green, pins suite included [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: reference post-landing reconciliation from all three landing tails` [class: IMPLEMENTATION_REQUIRED]

### Task 6: integration points with lesson 6 and the reverse-squash guard family

Files:
- `docs/maintenance/development_lessons.md`
- `scripts/reverse_squash_guard.py`

Edit 1: in lesson 6 ("Land a Squash Only From a Tree Merged With the Current Default Branch"), insert a new paragraph immediately after the line ending `landing it would have silently reverted every peer change.` (the lesson's last line, unique today), before the `## 7.` heading:

Checkout-side sibling: this lesson owns peer safety at the ref move; live-checkout freshness after the move is owned by the post-landing reconciliation implementation and the stale-checkout discriminator in the Worktree-first standard section of agents/skills/execute-plan/SKILL.md.

Edit 2: in `scripts/reverse_squash_guard.py`, insert a docstring line immediately after the line `Exit codes: 0 clean, 1 refusal with named evidence, 2 tool failure.` (unique today), keeping the module docstring's indentation:

  Stale-checkout adjudication: a refused or suspect entry whose blob equals the path's blob at an ancestor commit is a stale witness per the stale-checkout discriminator in the Worktree-first standard section of agents/skills/execute-plan/SKILL.md; restore-and-record, never commit.

The docstring line is the guard family's backward direction; the guard's logic bytes are frozen.

Evidence:
- `grep -oF 'live-checkout freshness after the move is owned by the post-landing reconciliation implementation' docs/maintenance/development_lessons.md | wc -l` equals 1; covers the lesson pin
- `grep -oF 'stale-checkout discriminator in the Worktree-first standard section' scripts/reverse_squash_guard.py | wc -l` equals 1; covers the docstring pin
- `python3 -m py_compile scripts/reverse_squash_guard.py`; covers the docstring-only change compiling
- `bash scripts/check-no-em-dash.sh file docs/maintenance/development_lessons.md`; covers the no-em-dash gate

- [x] Apply edit 1 with the exact quoted anchor and paragraph [class: IMPLEMENTATION_REQUIRED]
- [x] Apply edit 2 with the exact quoted anchor and docstring line; logic bytes untouched [class: IMPLEMENTATION_REQUIRED]
- [x] Run the task's Evidence commands; expect all green [class: REPOSITORY_TEST]
- [x] Commit: `docs: cross-reference post-landing reconciliation from lesson 6 and the guard docstring` [class: IMPLEMENTATION_REQUIRED]

### Final task: whole-plan validation gate

Files: none changed by this task.

Evidence:
- the full Validation Commands block; covers every criterion above at once

- [x] Run the full Validation Commands block from the repository root; expect `ALL P102 VALIDATION GATES GREEN` [class: REPOSITORY_TEST]

## Residual findings (cap closure)

The r5 cap round staged the entries below; each entry names its pattern id beside its disposition, and the fixes are in the delivered plan bytes (echo deferrals, the mirror wholesale-residue arm, the fixture split, the walk skip). The round-4 overflow rows (the Reference contract's closed-literal list lagging its consumers, and the fast-forward-led tail summaries) were recorded in the r4 record's overflow manifest and ride this closure as documented residuals.

- r5 F1: architecture#dual-surface-policy-parity, folded
- r5 F2: consistency#naming-drift, folded
- r5 F3: implementation#missing-error-handling, folded
- r5 F5: consistency#count-word-drift, folded
- r5 F6: testing#given-state-omits-load-bearing-pin, folded
