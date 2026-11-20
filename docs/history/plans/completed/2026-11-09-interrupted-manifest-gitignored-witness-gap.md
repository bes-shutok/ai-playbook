# Plan: operator-directed loss disposition for truly-lost deliverables

Backlog origin: docs/history/backlog/2026-11-02-interrupted-manifest-gitignored-witness-gap.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-09-plan-review-interrupted-manifest-gitignored-witness-gap-pba23a018-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2.0h total, largest task 1.5h
Executed: yes (dde8e3a01eed128914778b72df5f8ceb96a713a9)
Authoring claim: 2026-11-02-interrupted-manifest-gitignored-witness-gap.md (session sess_87f3390d-ffbc-4bb5-8611-c5f6298aae24)

## Terms

- deliverables witness: the set-resolution check inside `disposition-manifest` (`_disposition_first_missing_deliverable` in `scripts/done_sweep_gates_lib.py`) that refuses when any owned deliverable resolves through none of the witness arms, naming the first missing one.
- tracked arms: the witness arms that verify a home on their own: the recorded path on disk, `HEAD:<path>`, the `plans_completed` archive twin at HEAD, a landed deletion reachable from HEAD (owned_paths set), and the docs branch (owned_review_paths set).
- note-backed arm: the last witness arm: a deliverable resolves when the `--note` text contains its path as a substring; the tool verifies no home behind the note.
- note-only deliverable: an owned deliverable that resolves through the note-backed arm and through no tracked arm.
- dispositioned record: the one-time stamp on an interrupted run manifest, `dispositioned: {reason, date, note}`; today's reason literals are `work-verified-landed` (dead root) and `work-verified-landed-live-recovery` (live root), and this plan adds `operator-directed-loss` (dead root, flag set, at least one note-only deliverable).
- dead root / live root: an interrupted run whose recorded repo root matches no checkout here (dead) or matches this repository (live); `disposition-manifest` serves dead roots only, `recover-manifest` live roots only.
- operator park: an interrupted head the census leaves undisposed on purpose while an operator decision about it is owed.
- truly-lost-content: deliverables that no longer exist anywhere, the class the origin row narrowed to on 2026-11-04; distinct from gitignored-but-surviving content, whose note names the surviving home.
- interrupted-manifest census: the maintenance survey arm (agents/skills/maintenance/survey-arms.md) that classifies `list-interrupted-manifests` output, counts undisposed dead roots, and drains up to five per turn through `disposition-manifest`.

## Why

A dead-root head whose deliverables are truly lost can close today only by naming each lost path in `--note`, which stamps `work-verified-landed`: the corpus then records lost work as verified landed work. There is no honest loss reason, so the standing 2026-10-25 head stays an operator park rather than being closed under a false record.

## Gist & Examples

TLDR: disposition-manifest gains an `--operator-directed-loss` flag that records note-only deliverables under an honest `operator-directed-loss` reason, adding no refusal and leaving every unflagged invocation byte-identical; code-quality.

Before: closing the parked head `20261025T194856Z-75b095a82a7d` takes `python3 scripts/done_sweep_gates_lib.py disposition-manifest --run-id 20261025T194856Z-75b095a82a7d --note "<lost path> lost with its dead checkout"`, which stamps `{reason: "work-verified-landed", ...}` although the owned plan path is not on disk, not at HEAD, has no completed twin, and has no landed deletion (live probe 2026-11-09).

After: the same invocation plus `--operator-directed-loss` stamps `{reason: "operator-directed-loss", date, note}`, exits 0, and the census line prints `dispositioned=yes`. With the flag on a manifest that has no note-only deliverable (every deliverable resolves through a tracked arm, or the manifest owns nothing), the flag is inert: the stamp stays `work-verified-landed` and the command prints one notice line saying the flag was unused. A flagged invocation whose note omits a missing path refuses exactly as today. On an already-dispositioned manifest (the reprint arm) or when a concurrent stamp wins the compare-and-swap (the racer arm), the flag is ignored and the existing record is reprinted, since that record already shows its reason.

## Outcome

Give truly-lost deliverables an honest record: an operator-invoked flag stamps the dispositioned record with a reason that says loss, while the witness and its refusals stay unchanged.

- The parked head can close with a record that states what happened (loss), not verified landing.
- Every refusal and every unflagged acceptance stays byte-identical; the flag changes only the reason value, and only when a note-only deliverable exists.
- The census treats a loss disposition like any other dispositioned line, with no census change.

Gate delta: none of the machinery classes the plans skill counts added: no gate, validator, lock, ledger, refusal class, or new state field; one optional CLI flag selecting a third value for the existing dispositioned record's `reason` field, and one survey-arm clause naming the flag as an operator-invoked remedy under the arm's existing rule that persistently refused heads are named through the `turn_error:` channel for operator direction (the automated turn never passes the flag; this restates who owns the remedy and blocks nothing). Incident: docs/history/backlog/2026-11-02-interrupted-manifest-gitignored-witness-gap.md; review date 2026-12-08. The listing's `dispositioned` column flip is pinned by test; the census counts `dispositioned=no` lines only (survey arm, lesson 352), so the census needs no code change.

## Assumptions

- assume the dispatch entry's operator-directed, artifact-specific scope supersedes the origin row's original suggested direction (census and refusal evidence accepted as witness without an operator choice); basis: the PLAN-PROMPTS entry requires an explicit operator choice and artifact-by-artifact absence proof, and the origin row's 2026-11-04 update narrowed the open scope to the truly-lost-content arm.
- assume the loss record rides the existing dispositioned stamp (a distinct reason literal, the note carrying per-artifact loss detail); basis: the entry's arm (2) names "the existing manifest/census evidence path", and `RunManifest` treats `dispositioned` as an additive dict, so a new reason value needs no schema change.
- assume the census consumption needs no code change; basis: the live probe 2026-11-09 (stamped heads print `dispositioned=yes`; the survey arm counts undisposed lines only, development_lessons.md #352).
- assume the witness homes the tool probes stay as they are; basis: sibling worktrees, stashes, other checkouts, and remote refs are not probed, which the usage text discloses so the operator's direction is informed (residual: a loss stamp can land over content surviving in one of those homes).

Decision points requiring a grill: acknowledgment surface: CLI flag `--operator-directed-loss` reusing the existing `--note` channel over a separate acknowledgment file or a marker word inside the note (maintenance-selected standing authorization, best-supported in-scope option: an explicit flag cannot be tripped by note prose; 2026-11-09; Task 1); refusal surface: no new refusal, the flag only selects the reason when a note-only deliverable exists and is inert otherwise, over the ambiguity refusals the r1 draft proposed (maintenance-selected standing authorization, the r1 panel showed those refusals unpaid and the named-resolvable one false-positive on honest mixed notes; 2026-11-09; Task 1); unflagged note channel: kept byte-identical, still stamping `work-verified-landed` for a note-named lost path, over tightening it (maintenance-selected standing authorization, tightening adds a refusal outside this plan's admission; 2026-11-09; Task 1); command scope: `disposition-manifest` only, `recover-manifest` unchanged over extending the flag to live roots (maintenance-selected standing authorization, a live root keeps recoverable surfaces and no live-root truly-lost head is witnessed; residual: such a head keeps its recover-manifest refusal; 2026-11-09; Task 1); note matching: the existing note-backed substring rule unchanged, the loss detail being prose the tool never validates (maintenance-selected standing authorization, one matching rule across both reasons; 2026-11-09; Task 1); remedy ownership: the census arm names the flag as operator-invoked and the automated turn never passes it (maintenance-selected standing authorization, mirrors the arm's live-root proposal-only posture; 2026-11-09; Task 2).

## Standing constraints

- Focused suites only: run the touched suite through the repo's pinned venv runner; never a full-suite run as this plan's validation.
- Witness posture is frozen: every existing witness arm, refusal text, and unflagged acceptance shape stays byte-identical; existing suite cells are not edited, only added to.

## Evaluation Criteria

**Quality dimensions:**
- correctness: without the flag, every existing refusal and acceptance shape is byte-identical (the existing suite passes with no edits to existing cells).
- safety: the flag adds no acceptance a no-flag invocation would refuse; on a manifest without a note-only deliverable it is inert and says so.
- observability: the stamp reason distinguishes `operator-directed-loss` from both `work-verified` reason literals; the census line prints `dispositioned=yes` after a loss disposition.
- maintainability: the focused suite carries one cell per shape this plan adds or pins.

**Done when:**
- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_sweep_gates_lib.py -q` passes, including the new cells.
- The top-level usage string of `scripts/done_sweep_gates_lib.py` declares the flag, its note-only condition, its inert notice, its operator-invoked ownership, its disposition-only scope, and the homes the witness never probes.
- agents/skills/maintenance/survey-arms.md's interrupted-manifest arm names the flag as the operator-invoked remedy for a truly-lost dead-root head, with no net byte growth in that paragraph.

**Ship when:**
- Each actual loss disposition is invoked by an operator, never by an automated census turn.
- The arm's admission is re-reviewed by 2026-12-08 per the machinery admission protocol.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done_sweep_gates_lib.py` (Task 1)

**Tests:**
- `scripts/test_done_sweep_gates_lib.py` (Task 1) *(new cells only; existing cells frozen)*

**Documentation:**
- `agents/skills/maintenance/survey-arms.md` (Task 2)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/done_run.sh`; reason: the done runner composes the lib unchanged; no surface of this plan lives there.
- `docs/maintenance/development_lessons.md`; reason: the lessons corpus is learn-owned, not this plan's surface.
- The census state file `docs/tmp/done-session/interrupted-census.json`; reason: the census read is unchanged by this plan.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_sweep_gates_lib.py -q
python3 scripts/done_sweep_gates_lib.py --help
```

### Task 1: Operator-directed loss reason in disposition-manifest

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

Primary class anchors:
- `_disposition_first_missing_deliverable` in `scripts/done_sweep_gates_lib.py`
- `_cmd_disposition_manifest` in `scripts/done_sweep_gates_lib.py`

- [x] `disposition-manifest --operator-directed-loss` records the loss: given a dead-root manifest whose owned_plan_paths entry resolves through no tracked arm, when invoked with the flag and a `--note` naming that path, expects the dispositioned stamp `{"reason": "operator-directed-loss", "date", "note"}`, exit 0, and a `list-interrupted-manifests` line printing `dispositioned=yes`; the same outcome holds for a never-tracked `owned_paths` entry named in the note [class: IMPLEMENTATION_REQUIRED]
- [x] The witness reports note-only deliverables through an optional collector parameter that defaults off, so `recover-manifest` and every unflagged call keep the first-missing return contract unchanged; the command selects `operator-directed-loss` only when the flag is set and the collected set is non-empty [class: IMPLEMENTATION_REQUIRED]
- [x] Inert-flag witness: given the flag on a dead-root manifest whose every deliverable resolves through a tracked arm (once without `--note` and once with a `--note` naming the tracked-resolved path), and given the flag on a manifest owning no deliverables, expects a `work-verified-landed` stamp, exit 0, and one printed notice line naming the flag as unused [class: REPOSITORY_TEST]
- [x] Flagged refusal witness (RED at RED: the flag is an unknown argument until implemented): given the flag with a note that omits the missing path, expects the existing refusal naming that path and the arms attempted, exit 1, manifest byte-identical [class: REPOSITORY_TEST]
- [x] Unflagged pin (green at RED): given the same manifest without the flag, expects the existing refusal with no note and the existing `work-verified-landed` stamp with a note naming the path, both byte-identical to today [class: REPOSITORY_TEST]
- [x] Recovery pin (green at RED): given `recover-manifest` with the flag, expects an argument-usage rejection with the manifest byte-identical, and without the flag its behavior unchanged [class: REPOSITORY_TEST]
- [x] The top-level usage string (`_usage()`, the `disposition-manifest` entry) declares the flag, the note-only condition, the inert notice, operator-invoked ownership, disposition-only scope, and the reprint and racer arms ignoring the flag, and the homes the witness never probes (sibling worktrees, stashes, other checkouts, remote refs); a suite cell asserts these over `lib._usage()`, and `python3 scripts/done_sweep_gates_lib.py --help` shows them [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED for the flag-bearing acceptance, inert-flag, flagged-refusal, and usage cells (the unflagged and recovery pins stay green) [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_sweep_gates_lib.py -q` → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: operator-directed loss reason for truly-lost deliverable dispositions` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Operator-invoked remedy in the interrupted-manifest survey arm

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/survey-arms.md`

- [x] The arm's sentence "persistently refused heads are named through the `turn_error:` channel for operator direction" gains one clause naming `disposition-manifest --operator-directed-loss` (semantics per its usage text) as the operator-invoked remedy for a head whose deliverables are truly lost, stating that the automated turn never passes the flag itself [class: IMPLEMENTATION_REQUIRED]
- [x] The same paragraph pays for that clause by deleting the self-referential clause "the arm's existing stale-deployment probe sentence keeps its remedy and its tail reads "instead of executing or proposing a closure the deployed lib cannot run";" and the duplicate tail "; a dispositioned manifest proposes nothing (it is closed)", so the paragraph shows no net byte growth [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: name the operator-invoked loss remedy in the interrupted-manifest census arm` [class: IMPLEMENTATION_REQUIRED]
