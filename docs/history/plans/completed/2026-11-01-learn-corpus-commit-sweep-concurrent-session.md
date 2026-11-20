# Plan: learn corpus commit discipline - author-side shared-checkout arm

Backlog origin: docs/history/backlog/2026-11-01-learn-corpus-commit-sweep-concurrent-session.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-01-plan-review-learn-corpus-commit-sweep-concurrent-session-pd653c99e-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 0.5h total, largest task 0.5h
Authoring claim: docs/tmp/authoring-claims/2026-11-01-learn-corpus-commit-sweep-concurrent-session.md (session sess_8d8917a5-8d21-4e48-9048-a3c1ab416393)

## Terms

- gated corpus hunks: learn-authored edits to skills-repo corpus files (backlog items, lesson entries, sibling catalog edits) that the Step 1.8 commit rule stages and commits by explicit path.
- bounded span: the single step sequence marker, edit, scan, commit inside one learn capture leg, within which the commit of the authored hunks is expected to land.
- blob id: a git object id recorded at write time (`git hash-object -w <path>`), so authored content stays recoverable even if a parallel commit absorbs or displaces the working-tree bytes.
- own-edit check: the mechanical pre-staging check codified in the Step 1.8 commit rule (lesson 134 witness class): word-diff the path against HEAD and treat foreign-only hunks as not this session's to stage.
- mixed-author path: a path whose working-tree delta carries both this session's authored hunks and hunks this session did not write.
- absorption: the witnessed failure mode where a parallel session's explicit-path commit lands its own hunks together with this session's authored-but-uncommitted hunks, so the absorbed content loses its `committed:` receipt and subject-based attribution (witness eb77d5782, lesson 351).
- Step 1.8 commit rule: the "**Commit rule:**" paragraph inside Step 1.8 of `agents/skills/learn/step-1-extract.md`.
- dispatch entry: this plan's frozen entry in the maintenance rolling prompt log (`docs/history/backlog/PLAN-PROMPTS.md`, entry learn-corpus-commit-sweep-concurrent-session), the entry the maintenance monitor dispatches authoring work from; not learn SKILL.md's module-dispatch entries.

## Why

Two learn sessions authored the project lessons corpus concurrently in one shared checkout, and the faster session's explicit-path commit landed its own hunks together with the other session's uncommitted lesson text; the content survived but its attribution did not: no `committed:` receipt names the absorbed lesson, and the commit subject names only the absorbing session's work. The Step 1.8 commit rule's write-side parallel discipline covers write-time conflicts only, and its own-edit check tells a committing session to skip foreign paths without telling the authoring session to protect its own uncommitted hunks between the write and the commit. A bounded commit-span discipline with blob-id fallback, plus a post-parallel re-derivation duty before receipts, closes the window the witnessed absorption rode.

## Gist & Examples

TLDR: the Step 1.8 commit rule gains the author-side shared-checkout arm (commit gated hunks in the same bounded span as the gated write, or record their blob ids; re-derive what actually landed after any parallel commit before reporting the receipt) and the own-edit check's mixed-author skip case is made explicit, so a concurrent learn session can no longer silently absorb authored-but-uncommitted corpus hunks (driving force: code-quality).

Today, a learn session that writes a lesson row and delays its commit (a hygiene failure, an index-lock retry, a boundary wait) leaves the authored hunks exposed: any peer's explicit-path commit over the same file stages the worktree bytes and carries both sessions' work in one commit attributed to the peer. Witnessed 2026-11-01: commit eb77d5782 landed lesson 349 and a lesson 44 witness append authored by the other session; the bytes are correct on main but no receipt names them. After the change, the same session either commits inside the bounded span (marker, edit, scan, commit) or records blob ids at the write, and after any parallel commit lands on an edited file it re-derives what actually landed (`git log -S` over an authored span) before printing `committed:`; a path that turns mixed-author mid-run is skipped and reported like any foreign path, with the session's own hunks recoverable from the recorded blob ids.

## Outcome

Learn-authored corpus hunks in a shared checkout are either committed inside the write's bounded span or recoverable from recorded blob ids, and no `committed:` receipt is reported for content a parallel commit may have absorbed without a re-derivation check.

- A learn session authoring in a checkout with live peers no longer loses attribution for authored-but-uncommitted corpus hunks.
- After a parallel commit lands on an edited file, the authoring session re-derives what actually landed before reporting, so receipts name only this session's landed hunks.
- A mixed-author path is skipped and reported explicitly instead of being silently staged or silently dropped.
- The remedy stays prompt-discipline text inside the existing Step 1.8 commit rule, with no hook, lock, validator, or new machinery.

Gate delta: none (no gate, validator, fence, protocol layer, or schema field added or removed; prose-only instruction clarification inside an existing skill section; the dispatch entry's machinery-admission note rejects a pre-commit hook or validator for this fix).

## Assumptions

- assume the fix belongs in the Step 1.8 commit rule text only: the dispatch entry's scope arms (a)-(c) name the commit-rule arm, the explicit mixed-author skip case, and "no runtime or hook machinery in this arm"; basis: the origin row docs/history/backlog/2026-11-01-learn-corpus-commit-sweep-concurrent-session.md and the PLAN-PROMPTS entry learn-corpus-commit-sweep-concurrent-session.
- assume staging does not protect authored content: a peer's explicit-path `git add <path>` re-stages worktree bytes over the index entry, so only a prompt commit or a recorded blob id protects the hunks; basis: lesson 290 in `docs/maintenance/development_lessons.md` (pathspec commits land working-tree bytes).
- assume the `committed:` receipt is the attribution surface of record: receipt-ledger consumers and the done owned-commits ledger read it, so the re-derivation duty gates the receipt, not the commit itself; basis: the origin row's Problem section.
- assume the remedy is prompt-discipline text with no pre-commit hook, lock, or validator: the dispatch entry's machinery-admission note rejects them for now (the false-positive cost is a blocked legitimate landing whenever peers share a staged path), revisitable only after a second absorption despite the discipline; basis: the PLAN-PROMPTS entry's Machinery admission paragraph and the repository guidelines' Machinery admission protocol section.
- assume no test suite pins the Step 1.8 commit rule paragraph's prose byte-identically, while `scripts/test_learn_router_dispatch.py` pins the file's module headings and is green on main at authoring time (verified 2026-11-01, 8 passed); the prescribed text appends sentences inside an existing paragraph and introduces no heading, so the expectation is the suite stays green; basis: the suite's frozen heading contract run against main at authoring time.
- assume `git log -S` over an authored span is an adequate re-derivation probe for prose corpus edits: it finds commits touching the authored string span, which is what the receipt must name; basis: the dispatch entry's scope arm (a), which prescribes the tool.
Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: reading the edited commit rule against the witnessed incident (eb77d5782) routes the authoring session to bounded-span commit or blob-id recording, and the post-parallel re-derivation gates the `committed:` receipt.
- simplicity: the arm is prose inside the existing commit rule paragraph; no new subsection, step, gate, or tooling.
- maintainability: the mixed-author case reads as an explicit instance of the existing own-edit check rather than a parallel rule, and the arm does not duplicate the write-side retry discipline.

**Done when:**
- the Step 1.8 commit rule paragraph carries the shared-checkout arm text from Task 1 and no other section of the file changed.
- `bash scripts/check-no-em-dash.sh file agents/skills/learn/step-1-extract.md` exits 0.
- `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh` exits 0.
- the learn router-dispatch suite passes (8 passed at authoring time).

**Ship when:**
- none; the change is repository-internal with no external release condition.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/learn/step-1-extract.md` (Task 1) (the Step 1.8 commit rule paragraph only; all other sections and steps in this file are frozen; reject any review finding that touches them)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/maintenance/development_lessons.md`; reason: lessons 134, 290, and 351 are this plan's orientation witnesses; the lessons corpus is edited by learn runs, not by this plan.
- `docs/history/backlog/2026-11-01-learn-corpus-commit-sweep-concurrent-session.md`; reason: the origin row is this plan's scope-of-record input; its covered flip rides the landing lifecycle, not this plan's tasks.
- `scripts/test_learn_router_dispatch.py`; reason: the suite is this plan's validation oracle, not an edit target.

## Validation Commands

```bash
bash scripts/check-no-em-dash.sh file agents/skills/learn/step-1-extract.md
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_learn_router_dispatch.py -q
python3 scripts/plan_readiness.py docs/history/plans/2026-11-01-learn-corpus-commit-sweep-concurrent-session.md
```

(The readiness command is the plan-lifecycle certification gate: it passes once this plan's authoritative review record pair exists in the resolved reviews home; it is not an edit gate.)

### Task 1: Append the author-side shared-checkout arm to the Step 1.8 commit rule

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/learn/step-1-extract.md`

Primary class anchors:
- `Step 1.8` in `agents/skills/learn/step-1-extract.md`

Exact text to insert (verbatim, inside the Step 1.8 "**Commit rule:**" paragraph, after the own-edit check sentence ending "(done Step 4's ask-first fallback carries the skipped path)." and before the sentence beginning "When a staged path sits under `agents/skills/maintenance/`"):

```text
In a checkout shared with live peers, commit learn-authored corpus hunks in the same bounded span as the gated write (marker, edit, scan, commit), or record their blob ids at the write (`git hash-object -w <path>`) so the content stays recoverable; re-derive what actually landed (`git log -S` over an authored span) before printing a `committed:` receipt for a file this session edited but committed outside that bounded span, and after any observed parallel commit lands on a file this session edited, and keep the commit's descriptive subject and the run output naming only this session's landed hunks. When the own-edit check finds a mixed-author path (this session's authored hunks alongside hunks this session did not write), skip staging that path and report it like any foreign path; the recorded blob ids or the bounded-span commit keep this session's own hunks recoverable.
```

- [x] The Step 1.8 commit rule paragraph carries the shared-checkout arm text, inserted at the position quoted in this task's Context block above [class: IMPLEMENTATION_REQUIRED]
- [x] The inserted text is verbatim the exact text quoted in this task's Context block above [class: IMPLEMENTATION_REQUIRED]
- [x] No other section or step of the file changed: given `git diff main -- agents/skills/learn/step-1-extract.md`, expects exactly one paragraph gaining the two sentences [class: REPOSITORY_TEST]
- [x] The edited wording routes the witnessed incident to the guarded behavior: a session that wrote lesson text and delayed its commit either committed inside the bounded span or holds recorded blob ids, its re-derivation check (`git log -S` over the authored span) precedes any `committed:` receipt for an out-of-span commit and fires on an observed parallel landing, and the commit subject and run output name only this session's landed hunks [class: REPOSITORY_TEST]
- [x] The mixed-author case is an explicit instance of the own-edit check: a path carrying both authored and foreign hunks is skipped and reported, never silently staged [class: REPOSITORY_TEST]
- [x] Run `bash scripts/check-no-em-dash.sh file agents/skills/learn/step-1-extract.md`, expect exit 0 [class: REPOSITORY_TEST]
- [x] Run `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh`, expect exit 0 [class: REPOSITORY_TEST]
- [x] Run the learn router-dispatch suite per Validation Commands, expect all passing (8 passed at authoring time); on a red run, first check whether the failure names `step-1-extract.md` heading pins: failures citing other learn modules, citations, or surfaces are peer edits in the shared checkout, so re-run after the peer lands or report the witness blocked-by-peer, never editing this file's frozen sections [class: REPOSITORY_TEST]
- [x] Commit: `learn: add author-side shared-checkout commit arm to Step 1.8` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- Origin row `docs/history/backlog/2026-11-01-learn-corpus-commit-sweep-concurrent-session.md`: deleted at this archive per the covered-row convention; the covering landing commit is the witness. Task 1 landed verbatim (review worker byte-verified the 883-byte insert); the Step 1.8 commit rule now carries the author-side shared-checkout arm, the receipt-gated `log -S` re-derivation duty, and the explicit mixed-author skip case.
