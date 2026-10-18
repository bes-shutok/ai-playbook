# Plan: base-branch bypass fences (raw ref writes and amend authorship)

Backlog origin: docs/history/backlog/2026-10-04-main-rewind-consolidation-incident.md
Driving force: code-quality (primary), automation (secondary)
Plan review record: the staging series docs/reviews/2026-10-04-plan-review-main-rewind-bypass-fences-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

The two bypass shapes that executed the 2026-10-04 main rewind, a raw update-ref write with an empty reflog description and an unattributed `commit (amend)` entry, are named by standing audit arms the next time the base-branch reflog is audited, without moving any ref and without adding any gate to a commit path.

- A raw ref write that rewinds main onto a non-descendant tip (the 08:11:30 shape) surfaces as a `raw-ref-write:` row from the existing `reflog-window` audit, distinguishable from a message-bearing deliberate backward move.
- Amend entries on the base-branch reflog carry an attribution census: an amend whose creation-to-amend gap exceeds the critical-section bound exits 1 with an `amend-authorship:` row; an amend within the bound prints an `amend-attributed:` census row, so every amend entry on main's reflog surfaces for operator adjudication from one command, whatever its provenance.
- Detection stays post-hoc and read-only: both arms extend the existing audit inventory rather than adding refusal classes to any landing or commit flow.

Gate delta: additions are one new modeled row class (`raw-ref-write:`), one new read-only subcommand (`sweep-window`) carrying three new row forms (`amend-authorship:`, `amend-attributed:` census, `indeterminate:` attribution-failure), each priced with its paying sibling arm and the completed-integrity-failure witness: the `raw-ref-write:` row extends `scripts/base_reflog_audit.py reflog-window` (paying siblings: the arm's existing `backward-move:` and `empty-receipt:` rows), and `sweep-window` extends `scripts/base_branch_amend_guard.py` (paying sibling: the guard's landing-scoped `reflog-scan` arm, which never runs outside a landing critical section, exactly the gap the incident exploited); the completed-integrity-failure witness for both is the origin row's witnessed sequence (a foreign amend at 07:53:14 and a raw ref write at 08:11:30 bypassing every landed fence). Removals: none. No new refusal class touches a commit or landing path (both arms are post-hoc readers).

## Terms

- Reflog window: the consecutive reflog entry pairs walked from newest entry down to the anchor entry, with the walk and stop discipline already owned by `reflog-window` and `reflog-scan`.
- Critical-section bound: the maximum gap, in seconds, between a commit's committer timestamp and a same-critical-section amend of it; the default is 600, the merge-lock stale threshold (`MERGE_LOCK_STALE_SECS` parity), overridable by flag.
- Cross-window amend: an amend whose creation-to-amend gap exceeds the bound; provably outside one session's critical section from metadata alone.
- Attributed (in-window) amend: an amend within the bound at the immediate tip; metadata cannot exclude a foreign same-window amender, so the row is census evidence, never an exit-1 finding.
- Anchor: the `--since` sha that closes the walk window; an unclosed window is a tool failure, never a silent pass.

## Assumptions

- The witnessed evidence was re-derived from the live reflogs at authoring time (2026-10-04): the `10a22175` reflog entry carries an empty description and `7ea6123e` is not its ancestor; the amend pair `600aa460` over `af268a64` sits in the same reflog; `7ea6123e` remains reflog-reachable. The origin row's positional shorthand `main@{2}` has since drifted (today's commits pushed the granular tip deeper), so tasks cite sha anchors and the walk, never positional selectors; execution re-derives the anchors it uses from the live reflog before writing fixtures.
- Metadata ceiling, stated honestly: the witnessed amend pair shares author identity, committer identity, and preserved author date, so a foreign same-window amend is not separable from a sanctioned one by git metadata; the amend arm's exit-1 contract is therefore the derivable subset (cross-window rows), and the residual class is carried as census rows named in Terms.
- The `reflog-window` script is outcome-contract conformant and the guard keeps its own 0/1/2 convention without `OUTCOME:` lines; both conventions are preserved byte-stably for existing rows.
Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: two standing read-only audit arms name the raw-ref-write and amend-authorship bypass shapes on the base-branch reflog, why: the witnessed 2026-10-04 rewind executed through paths none of the landed fences watch, driving force code-quality.

The 2026-10-04 incident produced two reflog shapes no existing arm reports. First, at 08:11:30 main moved to `10a22175` through a ref write with an empty reflog description and no fast-forward relationship to the previous tip, orphaning 734 commits; the existing `backward-move:` row would eventually name the ancestry violation on a walk, but nothing distinguishes this silent raw write from a deliberate, message-bearing, operator-directed move. Second, at 07:53:14 a `commit (amend)` entry replaced `af268a64` with `600aa460`; the guard's `check-head` fires only at commit time in a flow that runs it, and `reflog-scan` runs only inside a landing critical section scoped to that landing's own allow-shas, so an amend executed outside any landing critical section is never swept by anything. After this plan, `reflog-window` prints a `raw-ref-write:` row for the first shape, and `base_branch_amend_guard.py sweep-window` prints an `amend-authorship:` row (exit 1) or an `amend-attributed:` census row (exit 0) for every amend entry in the window, so one standing audit command makes both bypass shapes adjudicable.

## Evaluation Criteria

**Quality dimensions:**

- Correctness: hermetic scratch-repo fixtures reproduce both witnessed shapes end to end (a bare `git update-ref` producing an empty-description non-descendant entry; an amend pair with controlled committer dates) and each fires exactly its modeled row with the pinned wording.
- No mutation: both arms and their fixtures are read-only over the audited repository; a fingerprint (HEAD sha, index, porcelain) captured before and after each arm run is byte-identical.
- Non-regression: existing row formats are byte-stable (`backward-move:`, `empty-receipt:`, `amend-entry`), existing suite tests stay green unchanged, and the anchor/stop/tool-error disciplines of both scripts are preserved.
- Convention fidelity: `base_reflog_audit.py` keeps the outcome contract (rows first, one final `OUTCOME:` line, exit 0/1/2/3); `base_branch_amend_guard.py` keeps its 0/1/2 convention with rows on stdout and evidence on stderr, no `OUTCOME:` lines.

**Done when:**

- `python3 scripts/test_base_reflog_audit.py` and `python3 scripts/test_base_branch_amend_guard.py` pass on the final bytes, including the new fixture families.
- A live-tree smoke over this repository's main reflog window re-derives the two historical shapes as printed rows without mutating anything, recorded in the execution session notes.

**Ship when:**

- The standing maintenance completion-arm audit invokes the extended arms on a routine run and the census output is adjudicable by the operator without reading the reflog by hand (loop-owned condition): the `raw-ref-write:` row rides the existing `reflog-window` invocation the sibling docs-branch entry's task 2 already wires, and that entry's task 2 is extended in this authoring cycle to name the `sweep-window` arm beside the two audit subcommands, so the third arm's standing invoker is owned by the same tail rather than left unwired.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `scripts/base_reflog_audit.py` (extends `reflog-window` with the raw-ref-write row class and the value-plus-message reflog read)
- `scripts/base_branch_amend_guard.py` *(new subcommand `sweep-window`)*

**Tests:**

- `scripts/test_base_reflog_audit.py` (new fixture family)
- `scripts/test_base_branch_amend_guard.py` (new fixture family)

**Contract files:**

- `scripts/OUTCOME_CONTRACT.md` (Task 3: the `base_reflog_audit.py` row gains the new modeled row class)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- The lineage decision for main (restore the granular tip, accept the consolidation, or merge both); reason: deliberately operator-directed per the origin row, and this plan is detection-only.
- Any ref-moving code, hook, or commit-path gate; reason: the plan adds post-hoc readers only, and a commit-path gate is a rejected alternative (hooks are machine-local; this repo's fences are audit-arm shaped).
- `agents/skills/maintenance/` text and the pins suite; reason: the landing-completion tail wording is the sibling docs-branch entry's task 2 surface.

## Validation Commands

```bash
python3 scripts/test_base_reflog_audit.py
python3 scripts/test_base_branch_amend_guard.py
python3 scripts/base_reflog_audit.py reflog-window --repo . --base-branch main --since-sha <anchor resolved from the live reflog at execution time>
python3 scripts/base_branch_amend_guard.py sweep-window --repo . --base-branch main --since <anchor resolved from the live reflog at execution time>
bash scripts/check-no-em-dash.sh added-lines --base <merge-base at landing>
```

### Task 1: reflog-window names the raw-ref-write shape

Files:
- `scripts/base_reflog_audit.py`
- `scripts/test_base_reflog_audit.py`

Write the RED fixture first: a hermetic scratch repo (per the suite's `audit_env` isolation discipline) whose main reflog receives a bare `git update-ref refs/heads/main <sibling-tip>` with no `-m`, reproducing the witnessed empty-description non-descendant entry; assert the current exit is not yet the modeled row, then implement:

- The `reflog-window` reflog read becomes value-plus-message pairs (one parse shape at implementation, for example `%H%x00%gs`), preserving the existing walk order, anchor stop, `--max-entries` behavior, and tool-error paths byte-stably for message-bearing entries. The decode is per field: the sha decodes as ASCII (the existing whole-line ASCII discipline keeps guarding the sha field, exit 3 on failure) and the message decodes UTF-8 with replacement (the guard's precedent), so a message-bearing entry with a non-ASCII subject stays a classified row rather than regressing a clean window into a tool error.
- New modeled row: for a consecutive pair whose newer value's reflog entry message is empty (the decoded message field strips to the empty string; `git update-ref` without `-m` renders a truly empty field) and whose ancestry check fails (`merge-base --is-ancestor older newer` exit 1), print `raw-ref-write: <newer> (empty reflog description; new tip is not a descendant of previous entry <older>)`.
- Message-bearing pairs keep the existing `backward-move: <older> -> <newer>` row format byte-identical; both row classes may fire in one run, rows print before outcome lines, and exit codes and the final `OUTCOME:` line discipline are unchanged (1 when any row exists, 2 indeterminate paths unchanged, 3 tool error unchanged).
- An empty-description pair whose ancestry passes prints no row (the adjacent fast-forward raw-write shape is deliberately out of scope; named in the module docstring).

Evidence: `python3 scripts/test_base_reflog_audit.py` (the RED fixture now exits 1 with the `raw-ref-write:` row and `OUTCOME: fail`; a message-bearing backward-move fixture asserts the unchanged row bytes; a clean window asserts exit 0 with the unchanged ok line; the full existing suite stays green); a non-ASCII-subject fixture asserts a message-bearing entry classifies without a tool error.

### Task 2: the amend guard gains the standing sweep-window arm

Files:
- `scripts/base_branch_amend_guard.py`
- `scripts/test_base_branch_amend_guard.py`

Write the RED fixtures first (hermetic scratch repos, the suite's existing isolation discipline, committer dates controlled via `GIT_COMMITTER_DATE` so reflog entry timestamps and commit timestamps diverge predictably), then implement the `sweep-window` subcommand:

- Invocation: `sweep-window --repo ROOT --base-branch NAME --since SHA [--critical-section-secs N]`, default bound 600 (merge-lock stale threshold parity).
- The walk reads value, message, and entry timestamp for every entry from newest down to the entry whose value resolves to the since sha; the window-closed discipline matches `reflog-scan` (a since sha that never appears as an entry is a tool failure, exit 2, never a silent pass).
- For each `commit (amend)` entry: the old value is the next older entry's value, the new value is the entry's own value, and the gap is the entry timestamp minus the old commit's committer timestamp.
- Cross-window rows: gap greater than the bound. Row wording `amend-authorship: <new> amends <old> (cross-window: gap <g>s exceeds bound <b>s)`; exit 1 when any cross-window row exists. The gap trigger is the only cross-window trigger: reflog entries chain old to new, so an amend's old value is by construction the adjacent older entry's value, and no real git operation produces a non-tip amend entry (verified empirically at review; only reflog tampering could imply otherwise, and tampering detection is out of scope for this read-only arm).
- Attributed census rows: gap at or under the bound. Row wording `amend-attributed: <new> amends <old> (in-window: gap <g>s at or under bound <b>s; metadata cannot exclude a foreign same-window amender)`; printed on stdout, exit stays 0 when only attributed rows exist.
- Attribution failure (old value unresolvable, or the entry timestamp unavailable): row `indeterminate: amend entry <new> could not be attributed (<reason>)` printed on stdout, exit 2; this extends the guard's existing exit-2 tool-failure convention with an uncertainty-over-rows rule (the uncertainty-dominates discipline the audit script already carries), stated here rather than inherited.
- Conventions preserved: rows and verdicts on stdout, evidence on stderr, exit codes 0/1/2, no `OUTCOME:` lines; `check-head` and `reflog-scan` behavior untouched.

Evidence: `python3 scripts/test_base_branch_amend_guard.py` (the cross-window fixture, old commit backdated via `GIT_COMMITTER_DATE` then amended with no env, exits 1 naming the amend-authorship row; the in-window fixture, both steps unbackdated, exits 0 printing only the attributed census row; the unclosed-window fixture exits 2 with the tool-failure line; the existing check-head and reflog-scan tests stay green unchanged).

### Task 3: contract, docstring, and live-tree smoke alignment

Files:
- `scripts/base_reflog_audit.py` (module docstring)
- `scripts/base_branch_amend_guard.py` (module docstring)
- `scripts/OUTCOME_CONTRACT.md` (the `base_reflog_audit.py` row gains the new modeled row class)

Evidence:
- Both module docstrings document the new row classes and subcommand with the witnessed shapes cited by sha and date.
- The outcome contract's `base_reflog_audit.py` row names the `raw-ref-write:` modeled row and the empty-description-passes-ancestry declared non-row arm.
- The live-tree smoke commands from Validation Commands run over this repository's main reflog with an anchor resolved from the live reflog at execution time; the printed rows (the two historical shapes appear in the window) are recorded in the execution session notes, and both suites are green on the final bytes.
- `python3 scripts/machinery_inventory.py --check` reports no row for this plan's files beyond the pre-existing tolerated baseline (no new script files were added).
