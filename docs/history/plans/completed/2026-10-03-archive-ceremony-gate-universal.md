# Plan: universal archive-ceremony verification on every lane egress path

Origin: `docs/history/backlog/2026-10-03-archive-ceremony-gate-universal.md` (operator-directed, fence-class)
Prose fence of record: `agents/skills/maintenance/SKILL.md` landed-plan disposition fence (landed edbb7f89)
Restoration of record: 950128bc (six plans restored to the plans root)
Plan review record: `docs/reviews/2026-10-03-plan-review-archive-ceremony-gate-universal-r*.md` (+ `.stats.json` sidecars)

## Driving force

The 2026-10-03 stray-close wave archived six landed-but-unexecuted plans as bare `plans:` renames (2702fe88 at 11:53, c030f087 at 14:57, 2a5573c7 at 15:38, 9bb1cd04 at 16:50; unchecked task boxes 28, 34, 23, 13, 17, 44), and no mechanical check existed on that path: the done skill's archive-ceremony gate refuses exactly this shape but the wave never went through the done lane. The prose fence (maintenance SKILL.md landed-plan disposition) and the carrier prompt are session-read text; the wave happened precisely where prose was the only defense. The operator-directed fix turn restored the six plans (950128bc) and queued this mechanical enforcement.

Live surface re-derivation (2026-10-03, authoring time; corrected by review r1): `scripts/reverse_squash_guard.py` already carries the symmetric refusal - its `check-staged` and `check-diff` modes refuse archive-dir EGRESS (deletions or renames out of `docs/history/plans/completed/` and `docs/history/backlog/completed/`; `check-commit` inspects only parentless near-full-repo snapshots) - and the first-parent-diff commit walk lives in `check-landed`, which is the family shape a plans-root-to-archive check extends. The done lane's evidence contract (archive-ceremony: no unchecked `- [ ]` box plus an exec-review record for the plan slug) is the evidence definition to generalize; its implementation lives in `scripts/done_sweep_gates_lib.py` (`_archive_state_dirs` names completed/ + deferred/ + rejected/ as the archive states; the slug derives from the dated basename minus its leading date; the exec-review series regex is `-exec-r\d+\.md$`), and the guard's new mode cross-names that lib as the contract twin so the predicate has one schema and two named implementations (r1 finding 17). The rejected-archive directory (`docs/history/plans/rejected/`) is the sanctioned non-execution egress.

## Outcome

- `scripts/reverse_squash_guard.py` gains a `check-archive` mode with TWO input arms over one evidence core: `--rev SHA` (commit inspection via the `check-landed` first-parent walk) and `--staged` (index-versus-HEAD inspection for a not-yet-built archive commit), plus `--ack-egress PATH`. Any egress - a rename or deletion moving a plan file from a plans root (`docs/history/plans/<file>`, `docs/history/backlog/<file>`, excluding their `completed/`, `deferred/`, and `rejected/` subdirectories) into an archive state directory (`completed/` or `deferred/` of either root, mirroring the done lib's `_archive_state_dirs`) or deleting it from a plans root - must carry execution evidence: the plan's bytes at the egress carry zero unchecked `- [ ]` task boxes AND a reviews-home exec-review record for the plan slug exists AT CHECK TIME whose content names the plan bytes' sha256 digest (the record binds the digest; a record with a missing or mismatching digest is refused - a filename match alone is forgeable and refuses, r1 finding 2). The rejected-archive path (destination under a `rejected/` subdirectory) is the sanctioned non-execution exit. Otherwise refuse naming the plan, the missing evidence leg, and the sanctioned exits (verify the work and check the boxes, land the plans skill's marked backfill completion record, take the rejected path, or the operator-directed ack). `--ack-egress` handles an unused ack - one whose path is not a detected egress - by printing the check-landed-style warning line and exiting 1 (a message component of the refusal, not a warning-only path); the ack is sanctioned by THIS plan's amendment of the maintenance fence (Task 3 lands the operator-directed single-archive escape sentence beside the existing prose), with the operator direction recorded in the turn record (the state file) and the acked egress restated in the commit message as an `Archive-egress-ack:` trailer citing that record. Exit codes stay in the guard family's 0/1/2 convention pending the family's queued outcome-contract migration row.
- The lanes that build archive commits run the check: the execute-plan landing critical section gains an archive-egress leg on the built landing commit before the ref move (same refuse posture as a parentage-gate refusal), and the plans skill's authoring closeout builds its archive commit, inspects it with `check-archive --rev` BEFORE any publication or handoff step, and on refusal keeps the commit local (reset the branch tip back one commit, keep the working tree) while reporting the sanctioned exits - the commit-then-inspect posture, never a staged-input call (r1 finding 4).
- The maintenance survey's census becomes state-recorded: each landed-unclaimed plan is recorded in the scheduler state file's `decision_reason` (a `queued_execution` entry naming the plan basename), the lane decision offers a landed-unclaimed plan's execution BEFORE any authoring dispatch while the record is non-empty, and an entry surviving three consecutive surveys without a dispatch fires `turn_error: queued-execution-starved` naming the oldest plan (aging mirrors the parked-dependency bound, r1 finding 18).
- The coordination arm: any carrier prompt or loop directive authorizing stray-close must quote the maintenance fence's sanctioned-stray-close sentence (the execution-evidence requirement) VERBATIM, and a session reading a stray-close authorization without the verbatim quote refuses it as a turn error; the plan's own check execution re-reads each anchor surface immediately before editing and stops on drift (r1 finding 13), and this plan sequences after the outcome-contract-migration-batch-1 plan where their surfaces touch (r1 finding 13). Mechanical coverage claim, stated honestly: the check runs on the wired lanes and retroactively via the done lane's archive-ceremony scan; sessions outside every lane remain prose-fenced (r1 overflow ds-6).

## Gate delta (machinery priced additions)

1. `check-archive` mode with `--rev`/`--staged` arms and digest-bound evidence; priced on the wave witnesses (four bare-rename commits, 159 unchecked boxes) plus the review-r1 forgeability witness (a filename-only record leg is one `echo` away from voiding the gate) per the machinery delta doctrine (`docs/history/plans/completed/2026-09-29-plans-machinery-delta-doctrine.md`).
2. Two skill-text wiring insertions (execute-plan landing critical section; plans-skill authoring closeout) plus the maintenance census/lane-decision state recording with its aging bound; priced by the same wave: every witnessed egress was a lane self-archive or bare rename.
3. The prompt-templates verbatim-quote coordination clause; priced on the carrier witness (the stretched clause ran 86 times under the old text).

## Terms

- **Plan-egress change**: in `--rev` mode, a first-parent-diff rename or deletion moving a plan file from a plans root into an archive state directory or deleting it from a plans root; in `--staged` mode, the same shapes judged between the index and HEAD.
- **Plans root**: `docs/history/plans/` and `docs/history/backlog/`, excluding their `completed/`, `deferred/`, and `rejected/` subdirectories.
- **Archive state directory**: `docs/history/plans/completed/`, `docs/history/plans/deferred/`, `docs/history/backlog/completed/`, `docs/history/backlog/deferred/` (the done lib's archive states minus rejected/, which stays the sanctioned exit; r1 finding 8).
- **Execution evidence**: two legs, both required - (a) the plan's bytes at the egress carry zero unchecked `- [ ]` task boxes; (b) an exec-review record for the plan slug EXISTS IN A REVIEWS HOME AT CHECK TIME (`docs/reviews/` or `docs/history/reviews/` under the `--repo` root; the slug derives from the dated basename minus its leading date, the done lib's rule; the filename matches the anchored record-name shape `^<...>-plan-review-<slug>-exec-r<N>.md$` (the whole name must match, anchored at both name ends, the slug in the whole hyphen-bounded segment, never bare substring) AND the record's content carries the sha256 of the plan's egress bytes (a record without the digest, or with a mismatching one, refuses - the leg is digest-bound, not name-bound, r1 finding 2). The record is per-checkout state (the homes are gitignored): a checkout whose homes lack a digest-matching record refuses fail-closed with the produce-the-record remedy, which is the done gate's own posture.
- **Rejected-archive path**: egress whose destination is under a `rejected/` subdirectory of a plans root; sanctioned without execution evidence.
- **Operator-directed ack**: `--ack-egress PATH` - passable only when the operator explicitly directed that specific archive in that turn, the direction recorded in the turn record (the scheduler state file), the acked egress restated in the commit message as `Archive-egress-ack: <path>` citing that record, at most one acked egress per turn; an ack for a non-egress path is a refusal (unused-ack), an acked path suppresses only its own refusal (r1 finding 12).
- **Stray-close authorization**: any carrier-prompt or loop-directive clause authorizing archiving a landed-but-unexecuted plan; valid only with the verbatim execution-evidence quote.

## Assumptions

- assume the check lives as a new mode of `scripts/reverse_squash_guard.py` with its contract tests in the EXISTING suite `scripts/test_reverse_squash_guard.py` (the guard has no in-file `--selftest` flag; the suite carries the ScratchRepo hermetic fixture and 59 passing tests). Basis: live probe 2026-10-03 (`--selftest` exits 2 argparse; suite run GREEN) - the draft's contrary claim was the review's r1 finding 1 and is corrected here (r1 finding 1).
- assume the evidence definition is the done gate's schema with FOUR named divergences, not one hardening: the digest binding (r1 finding 2), the anchored slug matching (the guard's record-name grammar is anchored at both name ends where the done lib's live match is a bare substring, its live substring hole), both reviews homes scanned (the done lib reads its single resolved home), and both plans roots covered (the done lib scans its own plans root only). The done lib stays the done-lane enforcement of record and is NOT duplicated in this plan's wiring; the guard's docstring cross-names `done_sweep_gates_lib.py`'s archive-ceremony section as the contract twin and names those divergences, and a future contract edit updates both named sites (r1 finding 17).
- assume deletions from a plans root are egress; renames within a plans root (root-internal moves) are NOT egress and exit clean. Basis: the wave's bare-rename witness shape and the review's boundary enumeration (r1 finding 10).
- assume `deferred/` destinations are egress requiring evidence or the ack: deferral removes a plan from the open census exactly as archiving does, and the sanctioned parking flow's human approval satisfies the operator-direction record. Basis: the done lib's archive-state set and the review's side-channel finding (r1 finding 8).
- assume the done lane's `archive-ceremony` gate stays the done-lane enforcement of record and is NOT duplicated in this plan's wiring. Basis: origin row arm 3 and the witness that the wave bypassed done.
- assume the maintenance census stays a prompt-side survey duty whose RECORD becomes state-file-mechanical; no new census script. Basis: origin row arm 2's wording.
- assume the six restored plans are execution work for the reopened execution lane; this plan builds the fence and does not execute them.
- assume the operator execution-lane reopening of 2026-10-03 stands: after this plan lands and is itself executed, its check runs on every wired lane's egress commits.
- assume peer-plan surface overlap (ref-move-integrity-fences, outcome-contract-migration-batch-1, single-commit-per-lane-event all touch this plan's surfaces): execution re-reads each anchor surface immediately before editing and stops on drift, and where outcome-contract-migration-batch-1 has landed, the exit-code references follow the migrated shapes. Basis: the open-plans census, 2026-10-03 (r1 finding 13).

Decision points requiring a grill: digest-binding record format; deferred/ evidence-or-ack treatment; ack per-turn cap value (resolved: one).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/reverse_squash_guard.py` *(modified; new `check-archive` mode with `--rev`/`--staged` arms)*
- `agents/skills/execute-plan/SKILL.md` *(modified; archive-egress leg in the landing critical section)*
- `agents/skills/plans/SKILL.md` *(modified; authoring-lane closeout gains the commit-then-inspect self-archive check)*
- `agents/skills/maintenance/SKILL.md` *(modified; the fence gains the state-recording sentence, the lane-decision ordering clause, the aging bound, and the operator-directed single-archive escape sentence)*
- `agents/skills/maintenance/prompt-templates.md` *(modified; the verbatim-quote coordination clause)*

**Tests:**
- `scripts/test_reverse_squash_guard.py` *(the guard's unittest suite; extended in place)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- The done lane's `archive-ceremony` and `execute-plan-closeout` gates and `scripts/done_sweep_gates.sh` / `done_sweep_gates_lib.py`; reason: the done lane already enforces this exact shape (the wave bypassed it); duplicating it in the runner is unpriced machinery.
- Executing the six restored plans; reason: execution work for the reopened execution lane, not this fence plan's payload.
- A git hook or commit-msg enforcement; reason: this repo's gates are skill-invoked scripts; a hook is new machinery the doctrine's bar does not clear.
- The outcome-contract migration of the guard's 0/1/2 exit family; reason: outcome-contract-migration-batch-1's scope, not this plan's.

## Validation Commands

```bash
python3 scripts/test_reverse_squash_guard.py
# wiring anchors (each RED before its task, GREEN after; [x] escapes keep the
# plan's own text from satisfying the greps; needles re-derived from the exact
# prescribed insertions, r1 findings 7 and 3).
grep -q "Archive-egress-ac[k]" scripts/reverse_squash_guard.py
grep -q "check-archiv[e] --rev" agents/skills/execute-plan/SKILL.md
grep -q "check-archiv[e] --rev" agents/skills/plans/SKILL.md
grep -q "queued_executio[n]" agents/skills/maintenance/SKILL.md
grep -q "queued-execution-starve[d]" agents/skills/maintenance/SKILL.md
grep -q "operator-directed single-archive escap[e]" agents/skills/maintenance/SKILL.md
grep -q "sanctioned-stray-close sentenc[e]" agents/skills/maintenance/prompt-templates.md
```

### Task 1: RED then GREEN - check-archive mode in the reverse-squash guard

Files:
- `scripts/reverse_squash_guard.py`
- `scripts/test_reverse_squash_guard.py`

- [x] `test_check_archive_refuses_unchecked_rename`; given a scratch-repo commit renaming `docs/history/plans/2026-10-03-x.md` (bytes carrying `- [x]` boxes) to `docs/history/plans/completed/2026-10-03-x.md`, `check-archive --rev <sha>` exits 1 naming the plan, the unchecked count, and the sanctioned exits [class: REPOSITORY_TEST]
- [x] `test_check_archive_refuses_missing_or_forged_record`; a rename of fully-checked bytes with NO exec-review record refuses naming the missing evidence leg; a record whose filename matches but whose content omits the plan bytes' sha256 (or carries a mismatching digest) refuses identically - the name-only leg is forgeable and must not pass; a record carrying the matching digest passes this leg [class: REPOSITORY_TEST]
- [x] `test_check_archive_passes_with_evidence`; checked bytes plus a digest-matching exec-review record in `docs/reviews/` under the `--repo` root exits 0; a record in `docs/history/reviews/` passes identically; a record for a DIFFERENT slug (hyphen-bounded containment: plan `foo` does not match `bar-foo`'s record) refuses [class: REPOSITORY_TEST]
- [x] `test_check_archive_rejected_path_deletions_and_deferred`; a rename into `docs/history/plans/rejected/` passes without evidence; a bare deletion of an unchecked plan from a plans root refuses like the rename; a deletion of an evidenced plan passes; a rename into `docs/history/plans/deferred/` of an unevidenced plan refuses (deferred is an archive state, r1 finding 8); a rename between two paths in the same plans root exits 0 (root-internal moves are not egress) [class: REPOSITORY_TEST]
- [x] `test_check_archive_staged_arm_and_ack`; `check-archive --staged` against an index holding the unchecked rename refuses identically to the committed shape; `--ack-egress <path>` suppresses exactly that path's refusal while another offending path in the same change still refuses; an ack whose path is not a detected egress exits 1 as an unused-ack refusal; more than one ack in one invocation is a refusal [class: REPOSITORY_TEST]
- [x] `test_check_archive_backlog_root`; a rename from `docs/history/backlog/<file>` into `docs/history/backlog/completed/` refuses like the plans-root shape [class: REPOSITORY_TEST]
- [x] Run `python3 scripts/test_reverse_squash_guard.py` -> expect RED (the new test cases fail: `check-archive` unknown) while all 59 pre-existing tests stay GREEN [class: REPOSITORY_TEST]
- [x] Implement: the `check-archive --rev SHA | --staged [--repo ROOT] [--ack-egress PATH]...` mode; plans-root and archive-state detection per the Terms sets; unchecked-box scan over the egress bytes; the digest-bound record leg (slug derivation stem-minus-leading-date, hyphen-bounded match, reviews homes resolved under the `--repo` root at check time, sha256 binding verified against the egress bytes, parent-side bytes for deletions); the rejected-path exit; the ack arms (unused-ack warning and refusal, per-path suppression); refused exits carry the named evidence and sanctioned exits; the module docstring's mode table updated (attributing the egress family to the staged/diff modes and the first-parent walk to check-landed, r1 finding 14) and cross-naming `done_sweep_gates_lib.py`'s archive-ceremony section as the contract twin (r1 finding 17); the family's 0/1/2 exits unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Run `python3 scripts/test_reverse_squash_guard.py` -> expect GREEN (all cases, pre-existing and new) [class: REPOSITORY_TEST]
- [x] Commit: `scripts: reverse-squash guard gains check-archive plans-egress mode` [class: IMPLEMENTATION_REQUIRED]

### Task 2: wiring - the lanes that build archive commits run the check

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/plans/SKILL.md`

- [x] Re-read the landing critical section and the plans closeout paragraph immediately before editing; any drift from the anchors this plan describes stops the task for reconciliation (three same-day peer plans touch these surfaces, r1 finding 13) [class: REPOSITORY_TEST]
- [x] Amend the execute-plan landing critical section: a landing commit whose diff moves plan files from a plans root into an archive state directory (or deletes them from one) runs `python3 scripts/reverse_squash_guard.py check-archive --rev <built-commit> --repo <root>` before the ref move and refuses the landing on exit 1 (same posture as a parentage-gate refusal: keep branch and worktree, report the named evidence and sanctioned exits); `--ack-egress` is passable only on the operator-directed-archive exception with the direction recorded in the scheduler state file's turn record and the `Archive-egress-ack:` trailer restating the acked path in the commit message [class: IMPLEMENTATION_REQUIRED]
- [x] Amend the plans skill's authoring closeout (the done-handoff that self-archives a landed plan): the lane BUILDS its archive commit, then runs `python3 scripts/reverse_squash_guard.py check-archive --rev <archive-commit> --repo <root>` BEFORE any publication or handoff step, and on exit 1 resets the branch tip back one commit (keeping the working tree) while reporting the sanctioned exits - the commit-then-inspect posture, never a staged-input call (r1 finding 4); the ack rules match the landing leg, record home unified to the turn record [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Validation Commands -> expect the two wiring greps GREEN [class: REPOSITORY_TEST]
- [x] Commit: `skills: lanes that archive plans run the check-archive egress gate` [class: IMPLEMENTATION_REQUIRED]

### Task 3: maintenance census recording, lane ordering, aging bound, and the ack's fence sentence

Files:
- `agents/skills/maintenance/SKILL.md`

- [x] Amend the landed-plan disposition fence with all four pieces in one targeted edit: (a) the survey's open-plans census records each landed-unclaimed plan in the scheduler state file's `decision_reason` as a `queued_execution` entry naming the plan basename; (b) the lane decision offers a landed-unclaimed plan's execution BEFORE any authoring dispatch while a `queued_execution` record is non-empty (the offer is the dispatch discipline's own claim/adoption path); (c) a `queued_execution` entry surviving three consecutive surveys without a dispatch fires `turn_error: queued-execution-starved` naming the oldest plan (aging mirrors the parked-dependency bound); (d) an operator-directed single-archive escape: archiving one specific plan without execution evidence is allowed only when the operator explicitly directed that specific archive in that turn, the direction recorded in the turn record and restated in the archive commit's `Archive-egress-ack:` trailer - this sentence is the escape of record the guard's `--ack-egress` implements (the fence previously carried no such escape; this plan introduces it, r1 finding 5) [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Validation Commands -> expect the three maintenance greps GREEN [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: census recording, execution-first lane ordering, aging bound, and the ack escape of record` [class: IMPLEMENTATION_REQUIRED]

### Task 4: coordination arm - verbatim quote requirement for stray-close authorizations

Files:
- `agents/skills/maintenance/prompt-templates.md`

- [x] Re-read the carrier-prompt duties paragraph immediately before editing and stop on drift [class: REPOSITORY_TEST]
- [x] Amend the carrier-prompt duties: any carrier prompt or loop directive whose text authorizes stray-close must quote the maintenance fence's sanctioned-stray-close sentence (the execution-evidence requirement) VERBATIM, and a session reading a stray-close authorization that lacks the verbatim quote refuses it as a turn error (naming the missing quote), with automation-c2937928's execution-less clause recorded as the anti-shape and the 2026-10-03 rewritten carrier as the corrected shape [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Validation Commands -> expect the coordination grep GREEN [class: REPOSITORY_TEST]
- [x] Commit: `skills: stray-close authorizations must quote the execution-evidence requirement verbatim` [class: IMPLEMENTATION_REQUIRED]

### Task 5: full validation pass and completion

Files:
- none (validation and bookkeeping only)

- [x] Run every Validation Command in order -> expect each GREEN, including the full guard suite with all pre-existing modes [class: REPOSITORY_TEST]
- [x] Re-derive the wave evidence recorded in Driving force against the archive commits (`git show --stat 2702fe88 c030f087 2a5573c7 9bb1cd04`); a material drift in the witness set is a plan-relevant finding, not a silent proceed [class: REPOSITORY_TEST]
- [x] Run the duplicate-origin coverage gate for the cited origin and mark it covered per the completion duty [class: REPOSITORY_TEST]
- [x] Commit (if any residue): `chore: archive-ceremony gate validation residue` [class: IMPLEMENTATION_REQUIRED]

## Execution residual fold (r2 deferred residuals, 2026-10-03)

Execution-run progress amendment (the acgu execution run, worktree wt-acgu2, branch plan-acgu-exec): the r2 round's eight deferred residuals (docs/reviews/2026-10-03-plan-review-archive-ceremony-gate-universal-r2.stats.json, `extensions.deferred_residuals`) fold here as one logical unit, before Task 5 signs the run off; the original task text above is unchanged. Per-residual disposition:

- F1 (ack trailer verification priced): `scripts/reverse_squash_guard.py` `check-archive` gains the `--rev`-mode arm - an acked egress must be verified by a matching `Archive-egress-ack: <path>` trailer in the rev's commit message (the whole trailer value compared, so a trailer naming a different path refuses the ack); a `--staged` ack is warning-level only (a printed warning that the ack cannot be trailer-verified pre-commit). Tests: an ack with the matching trailer passes; an ack without the trailer refuses; an ack whose trailer names a different path refuses; the staged ack prints the warning (scripts/test_reverse_squash_guard.py).
- F2 (queued_execution record shape pinned): `agents/skills/maintenance/SKILL.md`'s fence census clause now records each landed-unclaimed plan as a persistent entry of a top-level additive `queued_execution` state field (never a turn-scoped `decision_reason` token), each entry an object naming the plan basename and carrying a first-seen survey stamp (`since`, the parked-dependency ledger's since idiom, earliest-since retention on re-record); the consecutive-survey count and the oldest-plan ordering both read from those stamps. A State file field paragraph, the `"queued_execution": []` schema-line example, and the Step 6 carry-forward clause carry the field.
- F3 (backlog record-leg scoping): the guard's exec-review record leg is scoped to plans-root FILES (`docs/history/plans/` sources); backlog-root egress (`docs/history/backlog/`) requires only the zero-unchecked-boxes leg (a backlog item never carries an exec-review record; its sanctioned ticket is the sweep's own gate receipt context). The pinned backlog arm matches: an unchecked backlog rename refuses via the boxes leg only, and a checked backlog egress passes with no record at all.
- F4 (sideways-rename egress): the guard's egress extends to any rename whose source is a plans-root file and whose destination leaves that plans root entirely (docs/tmp/, the repo root, the other plans root); a rename into a rejected/ subdirectory of the source root stays the sanctioned non-execution exit and root-internal renames stay clean. Boundary test: a plans-root rename to docs/tmp/ refuses, and the evidenced sideways rename passes.
- F5 (contract-twin identity reworded; applied directly to the body): the Terms archive-state parenthetical now reads "the done lib's archive states minus rejected/, which stays the sanctioned exit"; Assumption 2 restates the evidence definition as the done schema with the four named divergences (digest binding, anchored slug matching, both homes, both roots), naming the done lib's live substring hole; the Terms record leg describes the anchored record-name shape; the guard docstring's contract-twin cross-name carries the divergence note.
- F6 (citations re-pointed): all 24 `(r1 finding N)` citations re-pointed to the r1 record's actual finding ids (the plan had cited the dedup-group numbering; the honest-coverage pointer is re-pointed to the r1 overflow manifest entry ds-6).
- F7 (unused-ack disposition unified; applied directly to the body): the Outcome now states the single disposition - an unused ack prints the check-landed-style warning line and exits 1 (a message component of the refusal, not a warning-only path).
- F8 (fourth refuse cell): the backlog test arm gained the backlog-root to `backlog/deferred/` refuse case, asserting exit 1 via the unchecked-boxes leg.

Also folded in the same unit (the interim exec review's two non-blocking findings): the combined findings-plus-unused-ack refusal now prints the sanctioned-exits block whenever evidence findings exist (previously an else-branch only), and the fence's closing clause no longer calls the rejected path an egress (it names rejected/ the sanctioned non-execution exit and this escape the fence's only non-evidence exit).

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-03-archive-ceremony-gate-universal.md`: this plan's own promoted origin. The universal plans-egress verification landed as the reverse-squash guard's `check-landed` sweep wired into the execute-plan landing critical section beside `check-archive`, with the operator-directed ack path; execution evidence docs/reviews/2026-10-03-exec-review-archive-ceremony-gate-universal-r1.md; origin fold-deleted 2026-10-04 in the backlog-root fold pass.
