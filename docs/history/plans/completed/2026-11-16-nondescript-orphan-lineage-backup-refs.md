# Plan: nondescript orphan lineage backup refs disposition

Backlog origin: docs/history/backlog/2026-11-13-nondescript-orphan-lineage-backup-refs.md
Authoring claim: 2026-11-13-nondescript-orphan-lineage-backup-refs.md (session sess_ce3c7b92-3419-4cd1-b99c-eeda7bc8fe7c)
Driving force: reliability
Force justification: reliability is outside the closed driving-force taxonomy; this plan is implemented anyway because it prevents irreversible lineage loss, the casualty class the 2026-10-04 rewind incident recorded, and park-triage would not take it because the nondescript names already misled an operator into suspecting a phantom branch (the origin row's triggering ask).
Plan review record: the staging series .ai-playbook/reviews/2026-11-16-plan-review-nondescript-orphan-lineage-backup-refs-pdde26303-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2.25h total, largest task 1h
Executed: yes (this landing a134f40f67946727eb434d3f227327557c8c957a)

## Terms

- keeper ref: one of the three nondescript refs under disposition: `refs/remembers/x`, `refs/remoted/main`, `refs/original/refs/heads/main`.
- orphan lineage: the commit set reachable from a keeper ref but from no branch; the object graph a keeper preserves.
- sole holder: state where a ref is the only ref whose reachable set contains a commit; deleting a sole holder destroys that lineage.
- unique commit set: the commits reachable from a ref but from no other ref; zero means another ref covers the whole lineage.
- corrected exclusion probe: the uniqueness computation that passes every other ref as an explicit exclusion (`git rev-list --count <ref> ^<other>...`); the row's literal `--not --all` form includes the walked ref and always reads zero.
- covering ref: a surviving ref whose reachable set contains a keeper ref's whole lineage.
- recovery namespace: `refs/recovery/`, the repository's dedicated keeper namespace; live convention example `refs/recovery/review-freshness-main-2026-11-04`.
- re-anchor: creating a new operator-named ref that covers the lineage before the keeper ref is deleted.
- holder continuity: mutating order in which the replacement ref exists and verifies before the old ref is deleted, so no window lacks a holder.
- disposition receipt: one fixed-order marker line the operator's per-ref choice is recorded as: `DISPOSITION-RECEIPT: ref=<r> choice=<keep|rename|reanchor|delete> new_ref=<r-or-none> cover_ref=<r-or-none> decided_by=operator date=<YYYY-MM-DD>`.
- marker line: a single-line, ordered, greppable record line (`LINEAGE-EVIDENCE:`, `DISPOSITION-RECEIPT:`, `POST-DISPOSITION-STATE:`, `MAIN-UNTOUCHED:`) appended to the origin row.
- facts document: `.ai-playbook/facts.md`; its `base_branch` key resolves the protected base branch (currently `main`).
- origin row: `docs/history/backlog/2026-11-13-nondescript-orphan-lineage-backup-refs.md`, the scope of record and this plan's only edited file.
- park: the operator-gated stop an operator-absent session takes at a decision boundary; the presentation is recorded, no receipt is written, and the run pauses without mutating any ref (Task 2).

## Why

Three refs hold orphan lineages under names that record neither creator nor purpose, and an operator reading the ref list cannot tell safety keeper from typo from foreign tool state; the triggering ask suspected a phantom `master` branch from these names. Deletion without disposition would repeat the 2026-10-04 lineage-loss casualty, so the refs persist unowned. This plan gives each ref one operator-chosen, recorded disposition with pre- and post-change reachability evidence.

## Gist & Examples

TLDR: turns three unowned keeper refs into operator-decided, recorded dispositions with fresh lineage evidence, so no orphan lineage is lost and no ref is deleted while it is the sole holder (reliability).

Before: `git for-each-ref` shows `refs/remembers/x`, `refs/remoted/main`, and `refs/original/refs/heads/main` with no recorded creator, purpose, or disposition; the 2026-11-13 origin row records their targets but uniqueness evidence is already stale (authoring-time probes show the first two lineages fully covered by named refs/release-backup/* backups and the third holding 9 unique commits as sole holder, a split the row could not have recorded because uniqueness drifts).

After: each ref carries one receipted disposition. A lineage covered elsewhere can be deleted on the operator's say-so with the covering refs on record; a sole holder is kept with a dated annotation or renamed into `refs/recovery/`; nothing is mutated before the operator chooses per ref, and the base branch ref is recorded before and verified identical after.

Edge cases that shaped the scope: a keeper ref whose tip stops resolving stops the run before any mutation; uniqueness is re-probed immediately before every mutation because it drifts (the recovery ref cited in the origin row went from 27 unreachable commits on 2026-11-14 to zero on 2026-11-16); an operator-absent session parks instead of choosing.

## Outcome

After execution, every keeper ref has exactly one operator-chosen disposition recorded in the origin row with pre- and post-change reachability evidence, and no lineage is lost.

- Each of the three refs is kept, renamed, re-anchored, or deleted under a recorded operator receipt, with the covering refs named.
- No ref is deleted or renamed away while a fresh probe still reads it as sole holder.
- The base branch ref value is recorded before any mutation and verified unchanged after.
- Follow-up disposition: a ref the operator defers keeps its receipt with the deferral reason in the row's disposition section and routes to the open 2026-10-04 lineage decision (docs/history/backlog/2026-10-04-main-rewind-consolidation-incident.md); this plan creates no new backlog rows.

Gate delta: adds one operator decision gate, the per-ref receipt recorded before Task 3 may mutate any ref (a pause condition on later work, priced by Rule 42's origin-cited no-exit justification: the origin's Class is fix-class and its Alternatives record that deleting without disposition repeats the 2026-10-04 casualty class while its Suggested investigation pins recovery as deliberately operator-visible per the 2026-10-04 precedent, so the three class defaults are each impossible: adding a sanctioned exit is impossible because the surface is git ref state with no existing validator to exit; removing a false positive is impossible because no check exists, the rejected default being autonomous deletion itself; simplifying the flow is impossible because the operator gate is the origin's pinned mechanism, not incidental friction). All other refusal classes, hard gates, fences, protocol layers, and schema fields: none added, none removed. Guard liveness ledger at authoring (2026-11-16, the script's own TOTAL line): 42 guards, 30 catches, 49 incidents.

## Assumptions

- assume the three keeper refs keep their row-recorded targets until execution; basis: probes 2026-11-16 resolved all three exactly (c53906c9200690759936864db1c852ce524d559d, f6d707877009a051f5c33e3e41f6151f9744486d, 8f37fcea791011aebf27a807103303ef56a6b6a8).
- assume uniqueness evidence must be re-derived at execution immediately before each decision and each mutation; basis: observed drift, the recovery ref named in the origin row lost all unique commits between 2026-11-14 and 2026-11-16.
- assume the row's literal `--not --all` uniqueness probe is self-defeating and the corrected exclusion probe is the operative computation; basis: authoring-time probe read 0 for the sole holder `refs/original/refs/heads/main` (9 unique under the corrected probe).
- assume renames target `refs/recovery/` with self-describing dated names per the live convention ref; basis: origin row Expected plus `refs/recovery/review-freshness-main-2026-11-04`.
- assume a kept ref's annotation is its dated receipt line in the row, not a git note; basis: maintenance-selected receipt 2026-11-16; a note would add a `refs/notes/*` ref, the same ambient-ref class the row complains about.
- assume evidence, receipts, and post-state ride sequential sections in the origin row, whose completion fold into the completed plan twin is the durable home; basis: maintenance-selected receipt 2026-11-16 and the plans lifecycle.
- assume an operator-absent session parks rather than choosing; basis: origin row operator-gated precedent and the maintenance stop-class vocabulary.
Decision points requiring a grill: kept-ref annotation mechanism: receipt line in the row, not git notes (maintenance-selected receipt 2026-11-16, Assumptions); uniqueness probe semantics: corrected exclusion probe enumerating every other ref (maintenance-selected receipt 2026-11-16, Assumptions); record home: origin row sections folding to the completed plan twin at completion (maintenance-selected receipt 2026-11-16, Assumptions); operator-absence behavior: park as an operator-gated stop, never autonomous mutation (maintenance-selected receipt 2026-11-16, Task 2).

## Standing constraints

- Manual git commands only; no new script, gate, scanner, or machinery (origin row Machinery assessment; repository Machinery admission protocol).
- The base branch resolved from the facts document's `base_branch` key is never moved, amended, or rewritten; no filter-branch or filter-repo runs.
- The three keeper refs are the only mutable ref surfaces; every other ref (`refs/codex/*`, `refs/release-backup/*`, `refs/stash`, `refs/recovery/*`, `refs/heads/*`, `refs/remotes/*`) is read-only for this plan.
- Ref operations mutate the repository's shared ref namespace regardless of which checkout runs them; verify state with `git for-each-ref` from the run's checkout.
- Records append sequential sections to the origin row; no other tracked file changes.
- Uniqueness probes follow the corrected exclusion probe (Terms) before any mutation; the plain `--not --all` form is valid only over a ref already deleted.
- Lineage evidence carries exactly one `LINEAGE-EVIDENCE:` line per ref at any time; a re-derivation after the section exists (a park or resume, a decision-boundary re-probe) replaces the existing per-ref lines in place and never appends a second dated evidence section.

## Evaluation Criteria

**Quality dimensions:**
- correctness: post-change `git for-each-ref` state matches the recorded receipts; every receipt has evidence and post-state lines.
- safety: sole-holder guard re-run immediately before every mutation; base branch ref recorded before and verified after.
- simplicity: manual git commands only; zero new files or scripts beyond the origin row sections.
- recordability: every receipt is one fixed-order marker line a grep can audit.

**Done when:**
- the origin row carries, per keeper ref, one `LINEAGE-EVIDENCE:`, one `DISPOSITION-RECEIPT:`, and one `POST-DISPOSITION-STATE:` marker line, plus one `MAIN-UNTOUCHED:` witness with match=yes.
- the Validation Commands block exits 0 against the executed state.
- no lineage loss: every deleted or renamed-away ref's tip remains reachable from a surviving ref.

**Ship when:**
- the operator's per-ref choices are made during execution (the Task 2 gate; human-owned, in-run).
- the 2026-10-04 row's separate lineage decision lands (owned by that row, out of scope here).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Records:**
- `docs/history/backlog/2026-11-13-nondescript-orphan-lineage-backup-refs.md` (Task 1)
- `docs/history/backlog/2026-11-13-nondescript-orphan-lineage-backup-refs.md` (Task 2)
- `docs/history/backlog/2026-11-13-nondescript-orphan-lineage-backup-refs.md` (Task 3)

**Production code:** none; this plan changes git ref state and the origin row record only.

**Tests:** none; verification lives in the task items and Validation Commands.

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- any ref outside the three keeper refs (`refs/codex/*`, `refs/release-backup/*`, `refs/stash`, `refs/recovery/*`, `refs/heads/*`, `refs/remotes/*`); the plan's Standing constraints freeze them.
- `scripts/`, `agents/skills/`, `docs/maintenance/`; no machinery or skill text changes are in scope.
- `docs/history/backlog/2026-10-04-main-rewind-consolidation-incident.md`, `docs/history/backlog/2026-10-26-release-sibling-loop-flags-orphan-branch.md`; read-only context owned by other rows.

## Validation Commands

Pinned-command outcomes at authoring (2026-11-16, plan bytes as touched set): em-dash touched scan pass (exit 0); public-hygiene scan pass (exit 0, OUTCOME: pass); readiness pre-round structural gate pass (exit 0, OUTCOME: pass); `bash -n` syntax check of this block pass; rule 22 pin audit pass. The block below executed RED-today: first failing gate `evidence marker for refs/remembers/x count=0`, exit 1 (the execution artifacts do not exist yet; the pass state is reachable only after Tasks 1 through 3 record their marker lines).

```bash
REPO="$(git rev-parse --show-toplevel)"; cd "$REPO" || exit 1
ROW="docs/history/backlog/2026-11-13-nondescript-orphan-lineage-backup-refs.md"
test -f "$ROW" || { echo "FAIL: origin row missing" >&2; exit 1; }
BASE="$(awk 'BEGIN{f=0} /^```toml$/{f=1;next} /^```$/{f=0} f && /^base_branch[[:space:]]*=/{gsub(/^base_branch[[:space:]]*=[[:space:]]*"/,""); gsub(/".*/,""); print; exit}' .ai-playbook/facts.md)"
test -n "$BASE" || { echo "FAIL: base_branch unresolved from facts" >&2; exit 1; }
for r in refs/remembers/x refs/remoted/main refs/original/refs/heads/main; do
  n=$(grep -cF "LINEAGE-EVIDENCE: ref=$r " "$ROW")
  [ "$n" -eq 1 ] || { echo "FAIL: evidence marker for $r count=$n" >&2; exit 1; }
  n=$(grep -cF "DISPOSITION-RECEIPT: ref=$r " "$ROW")
  [ "$n" -eq 1 ] || { echo "FAIL: receipt for $r count=$n" >&2; exit 1; }
  n=$(grep -cF "POST-DISPOSITION-STATE: source_ref=$r " "$ROW")
  [ "$n" -eq 1 ] || { echo "FAIL: post-state for $r count=$n" >&2; exit 1; }
done
line=$(grep -F 'MAIN-UNTOUCHED: ' "$ROW" | tail -1)
case "$line" in 'MAIN-UNTOUCHED: before='*after=*match=yes) ;; *) echo "FAIL: main-untouched witness malformed: $line" >&2; exit 1;; esac
before=$(printf '%s\n' "$line" | sed -E 's/^MAIN-UNTOUCHED: before=([0-9a-f]+) .*/\1/')
after=$(printf '%s\n' "$line" | sed -E 's/.* after=([0-9a-f]+) match=.*/\1/')
[ -n "$before" ] && [ "$before" = "$after" ] || { echo "FAIL: base branch ref moved between recordings" >&2; exit 1; }
[ "$(git rev-parse --verify "$BASE")" = "$after" ] || { echo "FAIL: current base ref $BASE differs from recorded after" >&2; exit 1; }
while IFS= read -r entry; do
  ref=$(printf '%s\n' "$entry" | sed -E 's/^DISPOSITION-RECEIPT: ref=([^ ]+) .*/\1/')
  choice=$(printf '%s\n' "$entry" | sed -E 's/.* choice=([a-z]+) .*/\1/')
  case "$choice" in
    keep)
      git show-ref --verify --quiet "$ref" || { echo "FAIL: kept ref $ref missing" >&2; exit 1; }
      ;;
    rename)
      newr=$(printf '%s\n' "$entry" | sed -E 's/.* new_ref=([^ ]+) .*/\1/')
      git show-ref --verify --quiet "$newr" || { echo "FAIL: renamed ref $newr missing" >&2; exit 1; }
      tip=$(grep -F "POST-DISPOSITION-STATE: source_ref=$ref " "$ROW" | sed -E 's/.* target=([0-9a-f]+) .*/\1/')
      [ -n "$tip" ] || { echo "FAIL: no recorded tip for $ref" >&2; exit 1; }
      [ "$(git rev-parse --verify "$newr")" = "$tip" ] || { echo "FAIL: renamed ref $newr does not hold recorded tip $tip" >&2; exit 1; }
      if git show-ref --verify --quiet "$ref"; then echo "FAIL: old ref $ref still present after rename" >&2; exit 1; fi
      ;;
    reanchor|delete)
      if git show-ref --verify --quiet "$ref"; then echo "FAIL: ref $ref still present after $choice" >&2; exit 1; fi
      tip=$(grep -F "POST-DISPOSITION-STATE: source_ref=$ref " "$ROW" | sed -E 's/.* target=([0-9a-f]+) .*/\1/')
      [ -n "$tip" ] || { echo "FAIL: no recorded tip for $ref" >&2; exit 1; }
      git cat-file -e "$tip" 2>/dev/null || { echo "FAIL: recorded tip $tip unresolvable" >&2; exit 1; }
      [ "$(git rev-list --count "$tip" --not --all)" -eq 0 ] || { echo "FAIL: $ref lineage orphaned after $choice" >&2; exit 1; }
      ;;
    *) echo "FAIL: unknown choice token: $choice" >&2; exit 1; ;;
  esac
done < <(grep '^DISPOSITION-RECEIPT: ' "$ROW")
echo "OUTCOME: pass"
```

### Task 1: re-derive lineage evidence and record it

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `docs/history/backlog/2026-11-13-nondescript-orphan-lineage-backup-refs.md`

- [x] Read-only probes over all three keeper refs: complete ref inventory (`git for-each-ref`), corrected exclusion probe unique count per ref, covering refs per tip (`git merge-base --is-ancestor` per surviving candidate), tip subject and date, loose-ref directory mtime, and reflog witnesses under .git/logs [class: IMPLEMENTATION_REQUIRED]
- [x] Append the row's `## Lineage evidence (<date>)` section with one ordered marker line per ref: `LINEAGE-EVIDENCE: ref=<r> target=<sha> unique_vs_other_refs=<n> covering_refs=<csv-or-none>` [class: IMPLEMENTATION_REQUIRED]
- [x] Creation-context recovery per ref: search .git/logs, packed-refs, and repo records (the origin row, the 2026-10-04 row, the completed bypass-fences plan) for the write that created each ref; record the best-supported creation story one line under each evidence marker [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness, unresolvable target: given a keeper ref whose `git rev-parse` fails at probe time, expects its evidence line to record the target as unresolvable and the run to stop before presentation or mutation, never guessing a target [class: REPOSITORY_TEST]
- [x] Determinism witness: rerun the corrected exclusion probe for each ref after re-reading the ref inventory and expect identical counts; a count change between the two reads records a concurrent ref write and stops the run before Task 2 [class: REPOSITORY_TEST]
- [x] Commit: `docs: record nondescript-refs lineage evidence (Task 1 probes)` [class: IMPLEMENTATION_REQUIRED]

### Task 2: present findings and record the operator's per-ref choices

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `docs/history/backlog/2026-11-13-nondescript-orphan-lineage-backup-refs.md`

- [x] Append the row's `## Disposition (<date>)` section: per ref one presentation block listing the Task 1 evidence values and the four options (keep with the dated receipt line as annotation; rename to refs/recovery/<lineage-name>-<date>; re-anchor to an operator-named cover ref then delete; delete when covered), then present the findings to the operator and record the operator's choice per ref as one receipt marker line in the fixed order the Terms define [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness, operator gate: given no operator available in the session at the decision boundary, expects the run to park with the presentation recorded and zero receipt lines written, never choosing or mutating autonomously [class: REPOSITORY_TEST]
- [x] Safety witness, receipt integrity: given a proposed receipt whose choice token is outside keep/rename/reanchor/delete, whose rename lacks new_ref, or whose delete or reanchor lacks cover_ref, expects the receipt rejected and the choice re-asked before Task 3 [class: REPOSITORY_TEST]
- [x] Commit: `docs: record nondescript-refs operator disposition receipts (Task 2)` [class: IMPLEMENTATION_REQUIRED]

### Task 3: apply the dispositions and record post-change evidence

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `docs/history/backlog/2026-11-13-nondescript-orphan-lineage-backup-refs.md`

- [x] Before any mutation: resolve the base branch from the facts document's `base_branch` key and record its ref value; append `MAIN-UNTOUCHED: before=<sha> after=pending match=no` to the row, completing it to `after=<same sha> match=yes` only after all mutations verify unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Apply each receipt per its choice, manual git commands, holder continuity order: rename creates refs/recovery/<new-name> at the old target first, verifies it resolves, then deletes the old ref; reanchor creates the operator-named cover ref first and verifies coverage before deleting; delete runs only when a fresh corrected exclusion probe immediately before the deletion reads zero [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness, sole holder at mutation time: given a delete or reanchor receipt whose fresh probe reads a nonzero unique count just before the mutation, expects the mutation refused and the choice re-presented to the operator, never applied anyway [class: REPOSITORY_TEST]
- [x] Append one post-state marker line per ref in the fixed five-field order: `POST-DISPOSITION-STATE: source_ref=<r> state_ref=<resulting holder ref or none> target=<old tip sha> cover_ref=<r-or-none> sole_holder_check=<pass|not-applicable>`; cover_ref names the surviving ref holding the lineage when state_ref is none or differs from source_ref, and stays none for a kept ref [class: IMPLEMENTATION_REQUIRED]
- [x] Reachability verification: for every deleted or renamed-away ref, verify its old tip stays reachable (`git rev-list --count <tip> --not --all` reads zero over the surviving ref set) before the final verification item runs [class: REPOSITORY_TEST]
- [x] Final verification: run this plan's Validation Commands block and expect exit 0; append the run's outcome line to the row's disposition section [class: REPOSITORY_TEST]
- [x] Commit: `docs: apply nondescript-refs dispositions and record post-state (Task 3)` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-11-13-nondescript-orphan-lineage-backup-refs.md`: completed by this plan. Each of the three nondescript keeper refs carries one operator receipt (delete x2 where release-backup refs cover the whole lineage; rename of the sole-holder filter-branch backup to refs/recovery/pre-charter-repair-main-2026-11-08), all old tips stay reachable, and the base branch ref was recorded before and verified identical after the mutations. The substance landed 2026-11-17 in a134f40f679; this completion pass re-verified every clause from disk 2026-11-20 and archived the plan. The former origin is deleted in this completion pass; its record sections are preserved below as the durable home.

### Origin-row record (folded 2026-11-20)

Lineage evidence probes 2026-11-17 from the run worktree; uniqueness per the plan's corrected exclusion probe, determinism witness passed (identical counts across two full re-reads of the ref inventory).

LINEAGE-EVIDENCE: ref=refs/remembers/x target=c53906c9200690759936864db1c852ce524d559d unique_vs_other_refs=0 covering_refs=refs/release-backup/pre-release-2026-10-04,refs/release-backup/pre-release-2026-10-04-2
Creation story: loose-ref directory mtime 2026-10-01 09:18; tip is a 2026-09-30 backlog commit; no reflog or packed-refs record of the write; best-supported story is a malformed `update-ref` destination write from the 2026-09-30/10-01 session work, a typo'd keeper not backed by any recorded intent.

LINEAGE-EVIDENCE: ref=refs/remoted/main target=f6d707877009a051f5c33e3e41f6151f9744486d unique_vs_other_refs=0 covering_refs=refs/release-backup/pre-release-2026-10-18,refs/release-backup/pre-release-2026-10-18-2
Creation story: loose-ref directory mtime 2026-10-19 04:02; tip is the 2026-10-17 authoring-claim freeze commit; no reflog record of the write; best-supported story is a malformed write mirroring `remotes/origin/main` spelling (`remoted` instead of `remotes`) from the 2026-10-18/19 release-window session work.

LINEAGE-EVIDENCE: ref=refs/original/refs/heads/main target=8f37fcea791011aebf27a807103303ef56a6b6a8 unique_vs_other_refs=9 covering_refs=none
Creation story: the standard `filter-branch` backup left by the 2026-11-08 charter-repair history rewrite; held 9 commits as sole holder, a genuine safety keeper until re-anchored or covered by the operator's 2026-10-04 lineage decision (owner row: docs/history/backlog/2026-10-04-main-rewind-consolidation-incident.md, still open for that decision).

Disposition presentation to the operator (interactive session, 2026-11-17): per ref the Task 1 evidence values plus the four options (keep with the dated receipt line as annotation; rename to refs/recovery/<lineage-name>-<date>; re-anchor to an operator-named cover ref then delete; delete when covered); operator chose per ref in-run.

- refs/remembers/x, covered lineage (0 unique commits, covered by pre-release-2026-10-04 backups); operator chose delete.
- refs/remoted/main, covered lineage (0 unique commits, covered by pre-release-2026-10-18 backups); operator chose delete.
- refs/original/refs/heads/main, sole holder of 9 unique commits (2026-11-08 filter-branch backup); operator chose rename to refs/recovery/pre-charter-repair-main-2026-11-08 to keep the lineage under a self-describing name.

DISPOSITION-RECEIPT: ref=refs/remembers/x choice=delete new_ref=none cover_ref=refs/release-backup/pre-release-2026-10-04 decided_by=operator date=2026-11-17
DISPOSITION-RECEIPT: ref=refs/remoted/main choice=delete new_ref=none cover_ref=refs/release-backup/pre-release-2026-10-18 decided_by=operator date=2026-11-17
DISPOSITION-RECEIPT: ref=refs/original/refs/heads/main choice=rename new_ref=refs/recovery/pre-charter-repair-main-2026-11-08 cover_ref=none decided_by=operator date=2026-11-17

MAIN-UNTOUCHED: before=d2c8b6015a2d6a0ba9bf928df11683b682f698eb after=d2c8b6015a2d6a0ba9bf928df11683b682f698eb match=yes

POST-DISPOSITION-STATE: source_ref=refs/remembers/x state_ref=none target=c53906c9200690759936864db1c852ce524d559d cover_ref=refs/release-backup/pre-release-2026-10-04 sole_holder_check=not-applicable
POST-DISPOSITION-STATE: source_ref=refs/remoted/main state_ref=none target=f6d707877009a051f5c33e3e41f6151f9744486d cover_ref=refs/release-backup/pre-release-2026-10-18 sole_holder_check=not-applicable
POST-DISPOSITION-STATE: source_ref=refs/original/refs/heads/main state_ref=refs/recovery/pre-charter-repair-main-2026-11-08 target=8f37fcea791011aebf27a807103303ef56a6b6a8 cover_ref=none sole_holder_check=pass

Run outcome 2026-11-17: Validation Commands block exit 0, OUTCOME: pass (executed from the run worktree; three receipts applied, all tips reachable, main unchanged).

Post-fold note 2026-11-20: the plan's pinned Validation Commands block binds the deleted living row path and exits 1 at its first gate (`FAIL: origin row missing`); re-verification greps the folded record sections of this twin instead. The block's base-ref check is separately time-bound known-red (recorded after=d2c8b6015, verified ancestor of live main at every later re-read).

Witness-exercise anchors (completion pass 2026-11-20): determinism witness passed (recorded above); receipt-integrity witness not exercised (no malformed receipt was proposed in-run); operator-gate park witness not exercised (the operator was present at the decision boundary); sole-holder refusal witness not exercised (both deletes ran only after fresh probes read zero); unresolvable-target witness not exercised (all three keeper refs resolved at probe time).

Marker-grammar note: POST-DISPOSITION-STATE cover_ref names a pre-existing cover distinct from the resulting holder; a rename keeps cover_ref=none because state_ref already names the resulting holder.
