# Plan: merge-lock release reachability and owner recovery

Backlog origin: docs/history/backlog/2026-10-08-merge-lock-release-stranded-outside-failure-path.md
Driving force: code-quality
Plan review record: the staging series docs/history/reviews/2026-10-08-plan-review-merge-lock-release-path-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 2.0h total, largest task 1.0h

## Terms

- merge lock: the repo-keyed landing lock family (`merge-*` commands in `scripts/done-lock.sh`, root `~/.ai-playbook/locks/merge`) held across a landing critical section; sibling of the done lock, one holder may hold both.
- token-fenced CAS release: the only sanctioned live-release path; `merge-release`/`merge-release-repo` compare the lock metadata token against the caller's `MERGE_LOCK_TOKEN` env and remove the hold only on a match.
- release-repo: the `merge-release-repo` form that refuses to source the shared session file; callers must re-export `MERGE_LOCK_DIR`/`MERGE_LOCK_TOKEN` from their own acquire output.
- shared session file: `.ai-playbook/merge-lock.session`, a status/fence-only record of the current holder; adopting it for release is the confused-deputy hazard.
- confused-deputy guard: the constraint that no release path may adopt the shared session file, because after a stale-clean plus peer reclaim the file names the new holder, and sourcing it would let an overthrown chat release a live peer hold.
- dead-holder reclaim: the sanctioned path where a peer removes an abandoned hold after verifying the recorded holder process is dead and the hold is past the stale threshold.
- self-reclaim: an owner recovery that acquires and immediately releases its own fresh hold; today's fallback when the original acquire exports are lost.
- acquire-output-lost case: the failure shape where the acquiring shell died or its output was truncated before the `MERGE_LOCK_*` exports could be captured, so the owner holds no token and cannot run the fenced release.
- orphaned release: the candidate owner-only arm (Task 3): a release form that succeeds only when the recorded holder process is verifiably dead (the same liveness evidence the dead-holder path uses) and never on a live holder.
- mode-dispatch row: the sibling backlog row `docs/history/backlog/2026-10-07-done-lock-release-mode-dispatch.md`; its root area is stale per the investigate archaeology (the env prefix is selected from the command family, both release forms exist, and an empty-env release exits 3 fail-loud).
- stderr suppression: caller-side redirection (`2>/dev/null` and siblings) that hides the release refusal messages the fence already prints.
- dead-holder grace: `MERGE_LOCK_DEAD_HOLDER_GRACE_SECS` (default 5 in `scripts/done-lock.sh`), the minimum age a verified-dead hold must reach before the dead-holder gate accepts it; distinct from the stale threshold (`MERGE_LOCK_STALE_SECS`), which this plan's arm never gates on.
- lock-internal helpers: `is_dead_holder_lock` (the verified-dead gate: numeric `holder_pid`, `ps` absence with `holder_state` not alive or ambiguous, age at or past the dead-holder grace; recorded `holder_identity` emptiness is checked only while the pid is live), `steal_remove_if_unchanged` (the CAS removal that re-checks token and epoch), and `clear_lock_session_if_token` (the token-fenced shared-session fence clear), all existing in `scripts/done-lock.sh` and reused unchanged by Task 3.
- `mrun`: the selftest helper in `scripts/done-lock.sh` that builds real locks in an env-discarding subshell and passes `MERGE_LOCK_HOLDER_PID` and `MERGE_LOCK_DEAD_HOLDER_GRACE_SECS` through, which is what makes the acquire-output-lost fixtures writable.

## Why

Two same-day stranded-hold recoveries (one needed a peer dead-holder reclaim, one an acquire-and-release self-reclaim) showed the merge-lock release is structurally unreachable after any mid-chain failure inside one-call lock-held closeout sequences, and unreachable again when the acquiring shell itself died with the token. The lock is correct; its release path lacks a reachable owner exit, which turns every composition slip into a stalled lane waiting for a peer.

## Gist & Examples

TLDR: make the merge-lock release always-run in prescribed closeout compositions and give the lock's owner a provably safe recovery when the acquire exports are lost, because a correct fence with an unreachable release strands landings (code-quality).

Today, a done run that consolidates gates, docs-branch sync, verify, and release into one `&&` chain loses the release whenever any earlier check exits non-zero (witnessed 2026-10-08: the verify loop's exit 1 short-circuited the chain, the follow-up release was refused because the token never made it out of the truncated acquire output, and recovery needed a fresh acquire-and-release cycle). The same day, a one-shot acquiring shell died when its Bash call ended, and a peer run reclaimed the abandoned hold. After this plan, the prescribed compositions run the release from an always-run position with unsuppressed stderr, the empty-env refusal names the owner's recovery recipe, and an owner whose shell died can still prove the hold orphaned (holder process verifiably dead) and release it without touching a live peer's hold.

## Outcome

Executing this plan makes the merge lock's release path reachable on every failure shape the fence itself does not deliberately refuse.

- A mid-chain failure inside a prescribed lock-held closeout no longer strands the hold: the release term rides an always-run position and its refusals are visible.
- An owner whose acquire output was lost has a named, written recovery: the refusal hint teaches the recipe, and the orphaned-release arm executes it mechanically when the recorded holder is verifiably dead.
- The sibling mode-dispatch row stops pointing at a stale root area: it flips to covered with the witnesses recorded by the investigate archaeology.
- The confused-deputy constraint, the token-fenced CAS release, and the dead-holder peer reclaim are unchanged and pinned by fixtures.

Gate delta: additions, each priced: (1) one new release refusal-class arm (the orphaned-release form, refusing live holders) with its paying sibling arm and origin-cited no-exit justification: the acquire-output-lost case has no owner exit today (the witnessed 2026-10-08 one-shot shell death needed a peer reclaim; cited in docs/history/backlog/2026-10-08-merge-lock-release-stranded-outside-failure-path.md, Suggested direction (a)); (2) remedy-text growth on the empty-env refusal hint (names the owner self-reclaim and orphaned-release recipe), paying sibling: the same origin's witnessed truncated-output recovery; (3) two skill-text composition duties (release in always-run position, release stderr never suppressed) in agents/skills/done/SKILL.md and the maintenance overlay merge-lock paragraphs, paying sibling: the witnessed `&&`-chain stranding in the same origin's Evidence. No removals; the token-fenced CAS release, the dead-holder reclaim, and every existing refusal keep their semantics.

## Assumptions

- The lock implementation of record is `scripts/done-lock.sh` (single file, inline selftest); the origin row's `scripts/done_lock.py` citation is stale, the module does not exist on disk (disk-verified 2026-10-08: `ls scripts/done_lock.py` absent, `wc -l scripts/done-lock.sh` = 1814).
- The witnessed silent no-op decomposes into caller-side stderr suppression plus wrong-family invocation, not a missing subcommand: the env prefix is selected from the command family, `merge-release`/`merge-release-repo` exist, and an empty-env release exits 3 fail-loud naming the required variables (receipt: the investigate charter, PLAN-PROMPTS entry merge-lock-release-path, Prompt paragraph, archaeology sentence).
- The runtime deployment of the lock script is already the repo script via symlink (restored 2026-10-07); no redeploy work is in scope.
- Releasing one's own hold after composition discipline requires no new capability when the exports survived; the orphaned-release arm exists only for the lost-exports shape.
Decision points requiring a grill: orphaned-release scope bounded to the verifiably-dead-holder-only constraint per the log entry charter, decided 2026-10-08, affects Task 3 (PLAN-PROMPTS entry merge-lock-release-path, Task 2 arm (c)); composition and remedy arms taken verbatim from the origin row's Suggested direction (a)/(b), decided 2026-10-08, affects Task 2 (docs/history/backlog/2026-10-08-merge-lock-release-stranded-outside-failure-path.md).

## Standing constraints

- The confused-deputy constraint is absolute: no release path sources or adopts the shared session file; the orphaned release reads lock metadata only.
- The token-fenced CAS release and the dead-holder peer reclaim keep their current semantics byte-for-byte; nothing in this plan widens who may release a live hold.
- The one-lock-lifecycle two-command-families structure of `scripts/done-lock.sh` is preserved; new surface rides the existing mode dispatch (`merge-*` family).
- Skill-text edits keep the pins suite green: any pinned span touched by Task 2 is re-keyed in the same task.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the orphaned release releases only a hold whose recorded holder process is verifiably dead, and refuses a live holder with a fail-loud message; fixtures prove both directions
- composition safety: the prescribed closeout sequences in the touched skills place release where a mid-chain failure cannot skip it, and no prescribed line suppresses release stderr
- recoverability: the empty-env refusal hint alone (without reading this plan) tells a stranded owner what to do next
- regression safety: the existing selftest suite passes unchanged except for the added fixtures

**Done when:**
- `bash scripts/done-lock.sh selftest` passes with the new orphaned-release fixtures (live-holder refusal, dead-holder release, token mismatch refusal)
- the touched skill spans carry the composition duties and `bash scripts/check_maintenance_pins.sh` shows no NEW failure versus the pre-task baseline recorded before Task 2's first edit (the pre-existing execute-plan origin-HEAD-fallback RED at the base tip is out of scope and filed as its own row)
- the mode-dispatch row reads `- **Status:** covered (docs/history/plans/2026-10-08-merge-lock-release-path.md)` with the five archaeology witnesses appended as Evidence bullets
- the origin row's failure shapes each have a written exit: mid-chain failure (composition), truncated output (hint + orphaned release), dead shell (orphaned release)

**Ship when:**
- the next real done-run closeout lands and releases under the prescribed composition without operator intervention (operator-owned observation, recorded in the done run's report)

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done-lock.sh`
- `agents/skills/done/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/SKILL.md` (merge-lock paragraphs only)

**Tests:**
- selftest fixtures appended inside `scripts/done-lock.sh` (same file as the mechanism; fixtures land in the script's selftest section)

**Docs:**
- `docs/history/backlog/2026-10-07-done-lock-release-mode-dispatch.md` (Task 1 status flip)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/history/backlog/2026-10-08-done-closeout-ceremony-friction.md`; reason: the closeout-ceremony trio's scope is receipt validation and placement, a different lane on the shared done surface
- `docs/history/backlog/2026-10-08-quota-wall-dispatch-doctrine.md`; reason: dispatch-carrier doctrine, unrelated to the lock lifecycle
- the execute-plan SKILL.md base-branch origin-HEAD-fallback pin span restoration; reason: pre-existing RED at the base tip unrelated to this plan's surfaces, filed as its own backlog row (r1 fold A1)

## Validation Commands

```bash
bash scripts/done-lock.sh selftest
bash scripts/check_maintenance_pins.sh
bash scripts/check-no-em-dash.sh touched
python3 scripts/plan_readiness.py docs/history/plans/2026-10-08-merge-lock-release-path.md
```

### Task 1: Re-disposition the mode-dispatch sibling row

Files:
- `docs/history/backlog/2026-10-07-done-lock-release-mode-dispatch.md`


Flip `docs/history/backlog/2026-10-07-done-lock-release-mode-dispatch.md` from open to covered, recording the archaeology witnesses so the stale root area stops generating follow-up rows.

- [x] RED/GREEN: before the flip, confirm the row's Problem text names the env-name dispatch defect and the archaeology witnesses contradict it (the command family selects the env prefix; both release forms exist; empty-env release exits 3 fail-loud naming `MERGE_LOCK_DIR`/`MERGE_LOCK_TOKEN`; the runtime path is the repo script's symlink restored 2026-10-07; agents/skills/done/SKILL.md Step 2 already prescribes merge-release-repo with re-exported env on every exit path) [class: REPOSITORY_TEST]
- [x] Flip the row in the corpus covered-flip format: `- **Status:** covered (docs/history/plans/2026-10-08-merge-lock-release-path.md)` (the covering-plan pointer parenthetical; the row has no witness section of its own) [class: IMPLEMENTATION_REQUIRED]
- [x] Append the five archaeology witnesses as Evidence bullets in the row: env prefix selected from the command family; both release forms exist; empty-env release exits 3 fail-loud naming `MERGE_LOCK_DIR`/`MERGE_LOCK_TOKEN`; the runtime path is the repo script's symlink restored 2026-10-07; agents/skills/done/SKILL.md Step 2 already prescribes merge-release-repo with re-exported env on every exit path [class: IMPLEMENTATION_REQUIRED]
- [x] Mark the row's stale `scripts/done_lock.py` citation superseded by one clause in the appended evidence [class: IMPLEMENTATION_REQUIRED]
- [x] Repoint the row's Cluster bullet at this plan's path (the primary origin row's own disposition rides this plan's completion step, the plans lifecycle fold-and-delete, witnessed by the archive commit) [class: IMPLEMENTATION_REQUIRED]
- [x] GREEN: `git grep -c '\*\*Status:\*\* covered' docs/history/backlog/2026-10-07-done-lock-release-mode-dispatch.md` returns 1, the row body carries the five witnesses, and the Cluster bullet names this plan [class: REPOSITORY_TEST]

### Task 2: Composition discipline and remedy text

Files:
- `agents/skills/done/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/SKILL.md`
- `scripts/done-lock.sh`


Make the prescribed closeout compositions release-safe and the refusal hints self-sufficient.

- [x] In `agents/skills/done/SKILL.md` (the lock-held closeout sequence and Step 2 region, which already prescribes a standalone release on every exit path): ADD two composition duties without moving the existing text: one sentence stating a release term must never sit at the tail of an `&&` chain (always-run position, `;`-sequenced or explicitly unconditional), one sentence stating release stderr is never suppressed (no `2>/dev/null` on any prescribed release call) [class: IMPLEMENTATION_REQUIRED]
- [x] The added sentences must not imply re-acquiring after a failed release (the never-re-acquire rule stands) and must not touch the stale-clean or G3b semantics [class: IMPLEMENTATION_REQUIRED]
- [x] Mirror the same two sentences, each kept to one sentence so the bodies stay prose-accurate, in the maintenance overlay's merge-lock paragraphs (`agents/skills/maintenance/zcode.md` merge-landing lock bullet; `agents/skills/maintenance/SKILL.md` where the landing lock acquire/release duties are stated) [class: IMPLEMENTATION_REQUIRED]
- [x] Scope note (r1 fold): the blueprint spans in `agents/skills/maintenance/prompt-templates.md` are exempt; they already carry release-on-any-failure duties and no prescribed `&&` tail or stderr suppression exists there, and the file's exactly-once span pins make incidental edits disproportionate [class: IMPLEMENTATION_REQUIRED]
- [x] In `scripts/done-lock.sh` `cmd_release`/`cmd_release_repo` empty-env refusal branches: extend the hint text to name the owner recovery in one line: re-export from the acquire output, else acquire-and-release self-reclaim, else the orphaned release when the recorded holder is verifiably dead [class: IMPLEMENTATION_REQUIRED]
- [x] Re-key any pins-suite span the skill edits touch (`bash scripts/check_maintenance_pins.sh` green in the same task) [class: IMPLEMENTATION_REQUIRED]
- [x] Before Task 2's first edit, record the pins baseline: run `bash scripts/check_maintenance_pins.sh` and save its output beside the run record (the pre-existing execute-plan origin-HEAD RED is the expected baseline failure) [class: REPOSITORY_TEST]
- [x] GREEN: the touched skill files carry the always-run and stderr sentences exactly once each; `bash scripts/check_maintenance_pins.sh` shows no new failure versus the recorded baseline (the baseline execute-plan RED persists, unchanged); the refusal hint names all three recovery legs [class: REPOSITORY_TEST]

### Task 3: Orphaned-release owner arm

Files:
- `scripts/done-lock.sh`


Add the owner-only recovery form and its fixtures.

- [x] RED: write the fixtures first in the selftest (all writable via the existing `mrun` helper, passing `MERGE_LOCK_HOLDER_PID` and `MERGE_LOCK_DEAD_HOLDER_GRACE_SECS` through): (a) a live hold with a live recorded holder pid refuses, naming the live holder; (b) a hold whose recorded holder pid is verifiably dead and past the grace releases and leaves the success receipt; (c) a dead holder still inside the grace refuses with its own message [class: IMPLEMENTATION_REQUIRED]
- [x] RED fixtures continued: (d) an ambiguous holder (a deliberately wrong recorded `holder_identity`, the pid-reuse class) refuses; (e) a meta with a missing `holder_pid` refuses; (f) missing or unparseable meta refuses [class: IMPLEMENTATION_REQUIRED]
- [x] RED fixtures continued: (g) a mismatched-token attempt (stale env against a newer hold) refuses unchanged; (h) a stale shared-session fence naming a different, newer token survives the orphaned release untouched (fence independence); (i) the usage text lists `merge-release-orphaned` [class: IMPLEMENTATION_REQUIRED]
- [x] GREEN: implement `merge-release-orphaned` (and the `release-orphaned` done-family twin only if it shares the code path unchanged) in `scripts/done-lock.sh`: reads lock metadata only (never the session file); the release gate reuses `is_dead_holder_lock` unchanged (numeric `holder_pid`, `ps -p` absence, recorded non-empty `holder_identity`, age at or past `MERGE_LOCK_DEAD_HOLDER_GRACE_SECS`) and never gates on `MERGE_LOCK_STALE_SECS` [class: IMPLEMENTATION_REQUIRED]
- [x] GREEN continued: refuse, each with a distinct fail-loud message: a live holder, a hold younger than the dead-holder grace, a `holder_state` of `unknown` or `ambiguous` (the pid-reuse class: recorded `holder_identity` mismatch while the pid is live), a meta with a missing `holder_pid`, and metadata that fails to parse [class: IMPLEMENTATION_REQUIRED]
- [x] GREEN continued: remove the hold via `steal_remove_if_unchanged` with the loaded token and epoch and clear the shared session fence only via `clear_lock_session_if_token`, never a hand-rolled remove; print a receipt naming the released hold, the dead-pid evidence, and the caller [class: IMPLEMENTATION_REQUIRED]
- [x] The orphaned release never bypasses the confused-deputy constraint: fixtures prove it sources nothing from `.ai-playbook/merge-lock.session` and refuses when lock metadata is missing or unparseable [class: IMPLEMENTATION_REQUIRED]
- [x] GREEN: `bash scripts/done-lock.sh selftest` passes with the new fixtures; no existing fixture changed semantics [class: REPOSITORY_TEST]
- [x] Record the new command in the script's usage text (the `merge-*` command list) so `merge-status` consumers discover it [class: IMPLEMENTATION_REQUIRED]
