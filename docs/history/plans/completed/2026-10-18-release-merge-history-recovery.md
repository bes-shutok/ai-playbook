# Plan: Release recovery mode for merge-containing unpushed history

Backlog origin: docs/history/backlog/2026-10-18-release-merge-history-recovery.md
Driving force: new-capability
Justification: the witnessed release completed only through an unsupported operator-driven reset and lease push outside the release workflow (origin row Evidence), so the capability moves that recovery inside the guarded contract; park-triage would not defer it: the origin row is priority high and the gap re-arms with every future merge landing in an unpushed delta.
Plan review record: the staging series .ai-playbook/reviews/2026-10-18-plan-review-release-merge-history-recovery-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 3.5h total, largest task 1.5h

Authoring claim: docs/tmp/authoring-claims/2026-10-18-release-merge-history-recovery.md (session sess_d7b16c2e-0ca5-4449-8d37-07e65ed62f54)

## Terms

- **Recovery mode**: the new `release-rewrite.sh` invocation form carrying `--recovery-base <oid>` and `--expect-remote-oid <oid>`. It rebuilds `main` onto an operator-selected base when the publish delta is not releasable by the ordinary flow, and publishes with a lease-bound force.
- **Ordinary release**: the existing release flow of record (agents/skills/release/SKILL.md): linear publish delta, plain fast-forward publish, forced pushes never used. Its behavior is frozen by this plan.
- **Selected base**: the operator-chosen commit the rebuilt history is rooted at. It must sit on `main`'s first-parent line and be an ancestor of `main`, strictly behind the tip.
- **First-parent line**: the chain of commits reached from `main` by repeatedly taking the first parent. The recovery tiling enumerates exactly the segment of this line between the selected base and the tip.
- **Expected remote OID**: the exact commit id the operator observed on `<remote>/main` when authorizing the recovery. The recovery publish is bound to it twice: at rewrite start and inside the push script at publish time.
- **Lease-bound force publish**: `git push --force-with-lease=refs/heads/main:<expected remote OID>`, the only force form this plan introduces. It refuses unless the remote ref still sits at the expected OID at push time.
- **Captured final tree**: the tree id of the original `main` tip, recorded by the rewrite before the swap. The rebuilt tip must carry exactly this tree, and the push script re-proves it before publishing.
- **Groups file**: unchanged input contract: one `base <sha>` line (the current `main` tip, as the ordinary flow writes it), then alternating `group <count>` / `msg <subject>` lines; in recovery mode the counts tile the first-parent segment instead of the linear range.
- **Backup ref**: `refs/release-backup/pre-release-<date>` at the pre-rewrite tip; in recovery mode it holds the accidental or merge-containing state and is the only path back to the original boundaries.
- **Push script**: the persisted 0700 script the rewrite emits. The recovery variant carries the recovery constants, re-runs the tree and privacy verifications, and publishes with the lease instead of a plain fast-forward.
- **Recovery refusal sentinel**: the fail-loud message prefix `RECOVERY REFUSED:` printed by every recovery precondition refusal, so a usage error can never satisfy a recovery refusal check.

## Why

The release workflow refuses any publish delta containing a merge commit, so a merge landing in the unpushed pile blocks releases with no supported way out; the one witnessed recovery was a manual reset and force push outside every guard. A recovery mode keeps the guards (backup ref, tree proof, privacy scan, compare-and-swap, verified publish) while making the exceptional path deliberate and bounded.

## Gist & Examples

TLDR: a recovery mode for the release rewrite rebuilds `main` onto an operator-selected base and publishes it with a lease-bound force after the full guard set, so a merge-containing unpushed delta stops forcing unsupported manual history surgery.

Before (today): a release with merge commits in `<remote>/main..main` aborts naming the offending commits (`a release needs a linear range`), and the only way out is an operator-hand-driven soft reset to a picked base plus `--force-with-lease`, holding none of the workflow's guarantees by construction. Witnessed 2026-10-18: base `1e5ecc56`, three feature commits published by hand, and a later `CHANGELOG.md` correction landed after the tree proof, so the published bytes were never re-proven as a whole.

After (this plan): the agent proposes the recovery (base, expected remote OID, grouping), the operator explicitly authorizes it, and the scripted flow runs the same guard set rooted at the selected base: backup ref, per-group tree identity, byte-identical final tree, privacy scan of the published result, compare-and-swap of `main`, then a push script that re-verifies the remote is exactly the observed state, re-proves the final tree, re-runs the privacy scan, and publishes with `--force-with-lease` bound to the observed OID. A moved remote, a drifted tree, or a dirty scan aborts before anything is published.

Edge cases: a concurrent commit landing mid-rewrite still routes to `REGROUP REQUIRED`; a recovery attempt on a delta the ordinary flow can release is refused (`RECOVERY REFUSED:` naming the ordinary flow); a base that is an ancestor but not on the first-parent line is refused (the tiling would not be exhaustive); a same-day second recovery collides with the existing backup ref name and takes the next `-N` suffix.

## Outcome

Make the witnessed exceptional release a supported, guarded workflow mode instead of an out-of-contract manual operation.

- A merge-containing or diverged unpushed delta can be released through the release skill with explicit operator authorization, producing feature-level commits (the witnessed shape: three feature commits atop the selected base) instead of one aggregate squash.
- Every guard of the ordinary release holds in recovery: backup ref at the original tip, byte-identical final tree, privacy scan of every published blob and message plus the groups file, compare-and-swap ref move, and a persisted push script whose re-assertions bind the publish to the exact observed remote state.
- Ordinary releases are unchanged: the merge refusal, its selftest pin, the plain fast-forward publish, and the forced-pushes-never rule all keep their existing bytes and verdicts.

Gate delta: adds refusal classes confined to the recovery mode (recovery flags unpaired or malformed, selected base absent, not an ancestor of `main`, equal to the tip, or off the first-parent line; a recovery invocation whose delta the ordinary flow could release; expected-remote-OID mismatch at rewrite start; push-time remote-OID mismatch, final-tree mismatch, or privacy re-scan hit) and adds the recovery publish switch; removes nothing (the ordinary merge refusal string and the ordinary divergence refusal keep their bytes, the latter mode-conditioned to ordinary runs, and the plain fast-forward push and the existing selftest pins keep their bytes); the additions are priced by the origin's recorded alternatives, each rejected there with its reason (refusal-only with no supported path, first-parent counts without tree proof, manual rewrite or replacement refs, throwaway-clone publish, manual checklist: docs/history/backlog/2026-10-18-release-merge-history-recovery.md), and the guard liveness ledger at authoring time (`python3 scripts/gate_liveness_ledger.py show`, 2026-10-18) reads catches-to-incidents across existing rows (dirt-regression-gate 1:4, doc-registry 1:0, em-dash-added-lines 1:0, land-squash-containment 1:0) with no row yet for the new recovery gates.

Machinery admission: the new refusals arm only inside the recovery invocation, so no ordinary-release surface gains a refusal; incident link: docs/history/backlog/2026-10-18-release-merge-history-recovery.md (one witnessed unsupported recovery); expected catch frequency: recovery-mode runs only, rare by construction; false-positive cost: a recovery attempt aborts until the operator re-observes the remote tip and re-authorizes (minutes, no state lost); sunset and review: the pre-registered registry-removal row (Task 4) names review by 2026-11-18 with promotion criteria (a true catch by the push-time rails or a second witnessed recovery), and the row lands in the same change.

## Assumptions

- assume the two recovery flags together are the technical record of the operator's authorization, and the skill prose owns the confirmation dialog that must precede them; basis: origin Expected ("explicitly authorized") and the entry's scope arm prescribing a verified lease before an explicitly authorized force-with-lease.
- assume the recovery tiling enumerates the first-parent line between the selected base and the tip; basis: the rewrite's per-group tree identity needs each group's newest tree to be a `main`-side tree, and only the first-parent walk guarantees that across merges (each merge's tree snapshot already contains its side branches, so excluded side-branch commits lose nothing).
- assume `scripts/release-authoring.sh` is unchanged; the recovery groups file has the same shape (base line equal to the `main` tip after the notes commit) and the same producer; basis: script and skill contract read 2026-10-18.
- assume the witnessed three-feature-commit result is grouping evidence, not a fixed count; the groups file remains the agent-authored judgment input; basis: origin Evidence and Prompt.
- assume the push-time privacy re-scan executes on bytes the tree re-verify just proved identical to the scanned final tree, and is kept because the origin demands tree and privacy checks rerun before publishing on this exceptional path; basis: origin Workaround assessment.
- assume sibling branches pointing into the rewritten range stay untouched and reported exactly as the ordinary flow reports them; basis: the ordinary skill contract, preserved.
- Sources inspected: not a tracker-linked request.
Decision points requiring a grill: add a release-owned recovery path selected by an operator-chosen base while ordinary releases stay fast-forward-only: user decision (operator mandate via the investigated dispatch entry's scope-arm adjudication), docs/history/backlog/2026-10-18-release-merge-history-recovery.md plus docs/history/backlog/PLAN-PROMPTS.md entry release-merge-history-recovery, 2026-10-18, Gist, Outcome, Tasks; the exceptional publish binds to the exact observed remote OID under explicit authorization: user decision (same source), 2026-10-18, Tasks, Terms; feature-level commits are the product shape, an aggregate-only result is insufficient: user decision (same source, witnessed three-commit result), 2026-10-18, Gist, Tasks; tree and privacy checks rerun after any later correction before publishing: user decision (origin Workaround assessment), 2026-10-18, Tasks

## Standing constraints

- No em dashes in committed files; the repository gate is `scripts/check-no-em-dash.sh`.
- Skill text stays tool-agnostic: describe behaviors by intent, never by tool names; the new skill prose obeys the existing `agents/skills/release/SKILL.md` wording rules (force-push phrasing included).
- `refs/release-backup/*` refs are never deleted, moved, or published; recovery adds no exception.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the selftest exits 0 with the new recovery cases passing and every pre-existing case (the ordinary refusal pins included) still passing unchanged.
- safety: every recovery rail fails closed before mutation or publication; the backup ref exists before the rewrite starts; the publish is lease-bound and aborts on remote movement, tree drift, or a privacy hit; the done lock is released on every exit path.
- clarity: the skill text states when recovery applies, what the operator must confirm, and what the summary must report, without weakening the ordinary contract.
- portability and hygiene: no tool-specific wording, no absolute personal paths, public-hygiene scan exits 0, em-dash scan exits 0 over the plan's added lines.

**Done when:**
- `scripts/release-rewrite.sh` carries the recovery mode with the preconditions and push script this plan prescribes, and `scripts/test_release_skill_selftest.py` covers every recovery witness below.
- `agents/skills/release/SKILL.md` carries the recovery contract (preconditions exception, authorization dialog, invocation, push step, summary) and the Rules section scopes the forced-push prohibition to ordinary releases.
- The pre-registered registry-removal row exists in `scripts/machinery_registry.json` and the ADR paragraph exists in `docs/maintenance/project-decisions.md`.
- The full Validation Commands block exits 0.

**Ship when:**
- The next witnessed merge-containing or diverged release delta completes through the recovery mode with the operator's explicit authorization and the operator confirms the published result and notes read right. Evidence owner: the user; closure: a live recovery run publishes with the lease verified and the summary delivered. [class: EXTERNAL_RELEASE_GATE]

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/release-rewrite.sh` *(edit: recovery mode)*
- `agents/skills/release/SKILL.md` *(edit: recovery contract)*
- `scripts/machinery_registry.json` *(edit: one pre-registered removals row)*
- `docs/maintenance/project-decisions.md` *(edit: one new ADR section appended; rest frozen)*
- `README.md` *(edit: the release Skill Catalog row's key-behavior cell only; all other regions frozen)*

**Tests:**
- `scripts/test_release_skill_selftest.py` *(edit: recovery cases and the harness support they need)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/release-authoring.sh`; reason: unchanged by design (Assumptions), no recovery behavior lives there.
- `docs/history/plans/completed/2026-09-26-release-skill.md`; reason: completed archive is immutable history, not a live contract.
- This plan file itself.

## Validation Commands

Pre-round gates at authoring: em-dash scan over the plan bytes 0 hits (fixer 0 substitutions), public-hygiene scan exit 0, `plan_readiness.py --pre-round` structural pass (after the item-envelope splits below).

```bash
set -euo pipefail
REPO="$(git rev-parse --show-toplevel)"
cd "$REPO"

# 1. Declared files exist
test -f scripts/release-rewrite.sh
test -f scripts/release-authoring.sh
test -f agents/skills/release/SKILL.md
test -f scripts/test_release_skill_selftest.py
test -f scripts/machinery_registry.json

# 2. Full selftest: new recovery cases green, every ordinary case still green
python3 scripts/test_release_skill_selftest.py

# 3. Ordinary merge refusal string intact (the ordinary mode is frozen; deleting
#    the refusal breaks this probe)
grep -qF 'a release needs a linear range' scripts/release-rewrite.sh || { echo "FAIL: ordinary merge refusal missing"; exit 1; }

# 4. Public hygiene over the full tree
bash scripts/scan-public-hygiene.sh

# 5. Em-dash ban over this change's added lines
bash scripts/check-no-em-dash.sh added-lines --base main

# 6. Registry carries the pre-registered recovery removal row (identity pin)
python3 - <<'PYEOF'
import json, sys
d = json.load(open("scripts/machinery_registry.json"))
rows = [r for r in d.get("removals", []) if r.get("id") == "release-recovery-push-rails"]
if not rows:
    print("FAIL: pre-registered recovery removal row missing"); sys.exit(1)
r = rows[0]
if "2026-11-18" not in r.get("note", ""):
    print("FAIL: removal row lacks the review-by date"); sys.exit(1)
print("registry row ok")
PYEOF

# 7. ADR paragraph landed (distinctive heading)
grep -qE '^## ADR-[0-9]{4}: release recovery mode publishes a lease-bound force$' docs/maintenance/project-decisions.md || { echo "FAIL: recovery ADR missing"; exit 1; }

# 8. Recovery contract present in the skill (distinctive spans, per-file probes)
grep -qF 'RECOVERY REFUSED:' agents/skills/release/SKILL.md || { echo "FAIL: recovery sentinel undocumented"; exit 1; }
grep -qF -- '--recovery-base' agents/skills/release/SKILL.md || { echo "FAIL: recovery base flag undocumented"; exit 1; }
grep -qF -- '--expect-remote-oid' agents/skills/release/SKILL.md || { echo "FAIL: expected remote OID flag undocumented"; exit 1; }

# 9. Catalog row still names the release skill (frozen regions untouched elsewhere)
grep -qF '| `release` | `agents/skills/release/SKILL.md`' README.md || { echo "FAIL: README catalog row missing"; exit 1; }
```

### Task 1: Recovery selftest cases (RED first)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/test_release_skill_selftest.py` *(edit: new recovery cases plus the fixture support they need)*

The harness extension reuses the existing scratch-repo machinery (temp dir, bare `origin`, stub lock, per-case `TMPDIR`, scanner-copy scheme) and adds what the recovery witnesses need: a scratch delta whose history contains a merge commit, a pre-merge first-parent commit usable as the selected base, and a bare remote sitting at the merge-containing tip; plus, for the push-time cases, the ability to move the bare remote or commit a tracked-file correction after the swap and before the push script executes. All fixtures live in `mktemp -d` with explicit teardown on every exit path, per the existing harness contract.

- [x] Merge-in-delta fixture shape: local `main` carries the merge and the bare remote sits strictly below it at an ancestor preceding the merge, so the merge sits inside the unpushed delta while `main` stays a descendant of the remote [class: REPOSITORY_TEST]
- [x] Recovery rewrite outcome: given that fixture, a selected base on the first-parent line behind the merge, the expected remote OID equal to the remote tip, and counts tiling the first-parent segment, expects exit 0, `main` at the rebuilt tip, and the rebuilt commit subjects equal to the groups-file `msg` lines in order [class: REPOSITORY_TEST]
- [x] Diverged-delta admission: given the bare remote at a merge-containing tip local `main` has diverged from and the expected remote OID equal to that tip, expects the ordinary divergence refusal not to fire and the recovery run to reach the rewritten-tip outcome [class: REPOSITORY_TEST]
- [x] Recovery tree and backup witness: given the same happy-path run, expects `git diff` between the rebuilt tip and the original `main` tip empty with the diff command zero exit asserted (an unresolvable ref fails the case), and the backup ref created at the original merge-containing tip [class: REPOSITORY_TEST]
- [x] Recovery publish witness: given the same happy-path run, expects the bare remote unchanged until the persisted push script executes, then equal to the rebuilt tip, with the push script completing the tree re-verification and the privacy re-scan before publishing [class: REPOSITORY_TEST]
- [x] Usage refusals: given unpaired or missing recovery flags, or an unknown flag, expects a non-zero usage FATAL with `main` unchanged and no backup ref created [class: REPOSITORY_TEST]
- [x] Base refusals: given a recovery base that is absent, an ancestor but off the first-parent line, or equal to the current tip, expects a non-zero exit carrying the `RECOVERY REFUSED:` sentinel naming the reason, `main` unchanged, no backup ref [class: REPOSITORY_TEST]
- [x] Delta and remote refusals: given a recovery invocation whose delta carries no merge and no divergence, expects the refusal naming the ordinary flow as the correct tool; given an expected remote OID differing from the fetched `<remote>/main`, expects the refusal before the backup ref [class: REPOSITORY_TEST]
- [x] Push-time remote rail: given the bare remote moved after the swap so it no longer equals the expected remote OID, expects the push script to abort at the remote re-assertion with its recovery restore message before publishing, the bare remote unchanged, and the script removed [class: REPOSITORY_TEST]
- [x] Push-time correction rail: given a tracked-file correction committed after the swap (the witnessed CHANGELOG correction shape, clean content or carrying a deny-pattern blob), expects the push script to abort at its first failing re-assertion (tip equality) with the recovery restore message naming the re-run remedy, nothing published, the bare remote unchanged, and the script removed [class: REPOSITORY_TEST]
- [x] Push script shape: given a successful recovery rewrite, the script text carries exactly one `--force-with-lease=refs/heads/main:` occurrence bound to the expected-OID constant, the final-tree re-verification, and the privacy re-scan invocation [class: REPOSITORY_TEST]
- [x] Ordinary preservation: given an ordinary run in the same suite, its persisted push script stays free of any force form (the existing ordinary cases keep asserting this) [class: REPOSITORY_TEST]
- [x] Run → expect RED: the recovery cases fail (the script does not accept the recovery flags, so every recovery invocation ends in the usage FATAL, which asserts none of the recovery sentinels, shapes, or outcomes), while the ordinary cases stay green [class: REPOSITORY_TEST]
- [x] Commit: `test: release recovery-mode selftest cases (RED)` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Recovery mode core in the rewrite script (GREEN)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/release-rewrite.sh` *(edit)*

Primary class anchors:
- `recovery_context` in `scripts/release-rewrite.sh`, a new function this task introduces as the recovery argument parser and precondition gate
- `invoke_scanner` in `scripts/release-rewrite.sh`, the existing scanner-invocation function whose immutable-copy scheme the recovery push script's re-scan follows

- [x] Argument parsing: with no recovery flags present the script keeps its ordinary one-positional contract byte-identical; each recovery flag is accepted at most once, must appear together with the other, and must be followed by its value; an unknown flag is a usage FATAL naming both recovery flags [class: IMPLEMENTATION_REQUIRED]
- [x] `recovery_context` base preconditions: after the shared preconditions (done lock held, HEAD on `main`, fetch), the selected base resolves to a commit, is an ancestor of `main`, sits on `main`'s first-parent line, and differs from the tip; each failure prints its `RECOVERY REFUSED:` line and exits 1 before the backup ref is created [class: IMPLEMENTATION_REQUIRED]
- [x] `recovery_context` delta and remote preconditions: the fetched `<remote>/main` equals the expected remote OID exactly; the delta must fail at least one ordinary precondition (a merge inside `<remote>/main..main`, or `<remote>/main` not an ancestor of `main`), the refusal naming the ordinary flow when neither holds; in ordinary mode none of these checks run [class: IMPLEMENTATION_REQUIRED]
- [x] Shared-block mode split: the shared precondition block splits by mode after the fetch: the divergence refusal (`main` not a descendant of `<remote>/main`) becomes ordinary-mode-only with its refusal bytes preserved, and a recovery invocation reaches `recovery_context`'s own admission instead [class: IMPLEMENTATION_REQUIRED]
- [x] Merge-scan mode split: the ordinary merge scan (a merge commit inside the delta fails the tiling, naming the offending commits, `a release needs a linear range`) becomes ordinary-mode-only with its refusal bytes preserved; a recovery invocation skips it and reaches the first-parent enumeration [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness (ordinary preservation): given an ordinary invocation on a merge-containing delta, expects the existing refusal bytes (offending commits named, `a release needs a linear range`) with exit 1 and `main` unchanged, identical to today [class: IMPLEMENTATION_REQUIRED]
- [x] Recovery enumeration: in recovery mode the delta enumerates the first-parent line from the selected base to the tip and the range count matches it; the groups tiling check runs against that count; the ordinary enumeration keeps its bytes [class: IMPLEMENTATION_REQUIRED]
- [x] Recovery rewrite and guards: the rewritten chain seeds from the selected base; per-group tree identity, rewrite ordering, author preservation, the final tree gate against the original `main` tip, the backup ref, the privacy gate over the materialized published result plus the groups file, and the compare-and-swap keep their mechanics; a concurrent landing still routes to `REGROUP REQUIRED` [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN at this task point: the recovery rewrite cases pass (the push-time rail cases may stay red until Task 3), and every ordinary case still passes [class: REPOSITORY_TEST]
- [x] Commit: `feat: release recovery mode rebuilds main onto a selected base` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Recovery push script (GREEN)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/release-rewrite.sh` *(edit)*

Primary class anchors:
- `invoke_scanner` in `scripts/release-rewrite.sh`, the existing scanner-invocation function whose immutable-copy scheme the push script's re-scan follows

- [x] Constants and assets: the recovery push script carries the expected remote OID, the captured final tree, the backup ref, the rewritten tip, and the snapshot hash, plus its own 0700 asset directory (`mktemp -d` under `TMPDIR`) holding an immutable groups-file copy and an immutable copy of the privacy scanner (plus the resolved patterns copy when the override is set) [class: IMPLEMENTATION_REQUIRED]
- [x] The asset copies exist so the push-time re-scan uses the same immutable scheme after the rewrite's EXIT trap has removed the originals [class: IMPLEMENTATION_REQUIRED]
- [x] Re-assertion order: `main` equals the rewritten tip; the status snapshot matches; a fresh fetch shows `<remote>/main` exactly equal to the expected remote OID (a moved remote aborts naming re-observation and re-authorization); `main`'s tree equals the captured final tree; every recovery abort message names the re-run remedy (re-run from Step 1 so the new tree is re-proven and re-scanned); each abort happens before publishing [class: IMPLEMENTATION_REQUIRED]
- [x] Publish-boundary verification: after the re-assertions, the tree proof against the captured final tree and the privacy re-scan over the materialized current tree plus the groups-file copy run on every legitimate publish, reached whenever the assertions hold; tip equality logically subsumes the tree proof (a commit id determines its tree) and both reruns stay per the origin's demand; a scan hit aborts before publishing [class: IMPLEMENTATION_REQUIRED]
- [x] Lease publish and teardown: only after the re-assertions pass, the publish runs as the lease-bound push of the rewritten tip to the remote `main` ref, and the script removes itself and its asset directory on every exit [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN at this task point: the full recovery case set passes and every ordinary case still passes; validation commands 2 and 3 pass [class: REPOSITORY_TEST]
- [x] Commit: `feat: release recovery push script re-verifies the observed remote and publishes lease-bound` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Skill contract, ADR, registry row, catalog cell

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/release/SKILL.md` *(edit)*
- `scripts/machinery_registry.json` *(edit: one pre-registered removals row)*
- `docs/maintenance/project-decisions.md` *(edit: one new ADR appended)*
- `README.md` *(edit: the release row's key-behavior cell only)*

- [x] `agents/skills/release/SKILL.md` recovery section: Preconditions names the recovery exception (a merge-containing or diverged delta is recoverable through the recovery mode); a new `## Recovery mode` section states when it applies, the authorization dialog (the agent proposes base, expected remote OID, and grouping; the operator's explicit confirmation precedes the run, the flags recording it), the invocation shape, and the push step [class: IMPLEMENTATION_REQUIRED]
- [x] `agents/skills/release/SKILL.md` recovery reporting: the section states the `RECOVERY REFUSED:` exit meaning and the summary additions (expected remote OID, selected base, the backup ref holding the accidental state); the Rules forced-push line gains the recovery carve-out scoped to the lease-bound publish, keeping the ordinary prohibition intact; the ordinary Steps 1 to 3 keep their bytes [class: IMPLEMENTATION_REQUIRED]
- [x] Pre-registered registry-removal row: `scripts/machinery_registry.json` gains exactly one `removals` row with id `release-recovery-push-rails`, its note naming the review-by date 2026-11-18, the promotion criteria (a true catch by the push-time rails, or a second witnessed recovery), and the incident link to docs/history/backlog/2026-10-18-release-merge-history-recovery.md; the JSON must still parse [class: IMPLEMENTATION_REQUIRED]
- [x] ADR appended under the exact heading `## ADR-<next free number>: release recovery mode publishes a lease-bound force`, recording the decision (recovery rooted at an operator-selected base, publish bound to the observed remote OID) and the rejected alternatives with their origin-cited reasons (refusal-only, first-parent counts without tree proof, manual rewrite, throwaway clone, manual checklist) [class: IMPLEMENTATION_REQUIRED]
- [x] The same ADR records the rails (backup ref, final-tree proof, privacy scan plus push-time reruns, compare-and-swap, lease-bound publish, done-lock serialization) and the ordinary-mode preservation statement [class: IMPLEMENTATION_REQUIRED]
- [x] `README.md` release row: the key-behavior cell is rewritten in place to scope the ordinary clause ("ordinary releases push a plain fast-forward of the verified tip, never forced") and add the recovery clause ("a recovery mode publishes a lease-bound force after explicit operator authorization"), touching no other cell or row [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: release recovery contract, ADR, registry pre-registration` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Full validation sweep

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- none new; runs the Validation Commands block over the landed tree

- [x] Run → expect GREEN at this task point (all earlier tasks landed): the complete Validation Commands block exits 0; record the outcome in the execution log [class: REPOSITORY_TEST]
- [x] If the sweep required any tracked-file fixes, commit them as `test: release recovery validation sweep green`; on a first-pass green no commit is made and instead `git status --porcelain --untracked-files=no` restricted to this plan's declared file set must be empty [class: REPOSITORY_TEST]
