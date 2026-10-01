# Plan: Docs-branch sync single-marker window anchoring

Backlog origin: `docs/history/backlog/2026-09-28-docs-branch-sync-single-marker-unanchorable-window.md`
Driving force: reliability
Plan review record: the staging series docs/reviews/2026-10-01-plan-review-docs-branch-single-marker-window-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

A done run that starts fresh (a single content-confirmable run-start marker) anchors its own session window from its manifest and owned-commits ledger, un-blocking every window-scoped gate behavior for fresh-start runs while the two-marker path and the conservative default stay exactly as they are.

- Single-marker runs stop returning an unanchorable window when their own witness pair exists: the manifest bound to the current marker (via the existing marker-field binding in load_run_manifest) plus the run's owned-commits ledger anchor the window at the manifest's `created_epoch`, with `anchor` deliberately None so marker pruning stays conservative.
- The origin's second arm (a durable pending-sync record) is dispositioned as moot against current machinery, with the stale-premise evidence recorded in the plan: the sweep-gates lib's contract is "sync nothing", and the real docs-branch sync is agent-side, wholesale, and window-independent, so the window-skip the origin witnessed no longer exists to record against.

Gate delta: one fallback anchor source added to the existing session-window derivation (used only when fewer than two content-confirmable markers exist and the witness pair is complete; `anchor` stays None so the conservative marker-pruning immunity holds), plus pins for the derivation arms (two new tests; the no-manifest pins stay green); no refusal surface is removed, and the no-manifest and manifest-without-ledger cases keep today's unanchorable return. Fix-class origin pricing: the sanctioned exit is the alternative anchor the origin's own expected behavior prescribes; there is no false positive to remove (the conservative gating is correct for what it can see - the defect is the missing second source); narrowing is rejected because silent under-inclusion in window-scoped gating is the witnessed failure class.

## Terms

- Content-confirmable marker: a run-start marker whose recorded digest matches the recomputed repo-root digest (or a legacy raw-path marker confirmed by resolved path); the session window needs two (current run + previous-run anchor).
- Witness pair: the run manifest bound to the current marker plus the run's owned-commits ledger on disk; together they anchor a single-marker run's own window at the manifest's `created_epoch`.
- Anchor-None fallback: the fallback window returns `anchored=True` with `anchor=None`, so every consumer that keys on the anchor marker (marker pruning) keeps its conservative behavior.

## Assumptions

- The origin's second Expected arm (a durable pending-sync sidecar for skipped artifacts) is moot against current machinery and is dispositioned rather than implemented: the sweep-gates lib's own contract states "sync nothing: this runner never touches the docs branch", every derive_session_window consumer is a gate that prunes or scopes candidates (returning conservative empties when unanchored), and the real docs-branch sync is agent-side (done Step 2 invoking the docs-branch skill), wholesale from disk, and window-independent - so there is no window-gated sync skip left to record against. The origin's witnessed miss (the 2026-09-28 recreated review record) predates the machinery absorption. (Basis: the lib contract line, the consumer survey, and the docs-branch skill's window-free candidate build, all read this cycle; the r1 panel verified each.)
- The window derivation lives in `derive_session_window` (scripts/done_sweep_gates_lib.py), restated for the operator at done SKILL.md's Step 0 marker paragraph, which names the fewer-than-two-markers unanchorable case verbatim; the origin's exact-location pointer at the docs-branch skill predates the absorption and that file carries no window restatement (grep verified). (Basis: the done SKILL.md paragraph and the docs-branch grep, this cycle.)
- The manifest always exists for a done run that reached the gates (Step 0 writes it before any gate runs), and load_run_manifest already binds manifests to the current marker by filename with root matching and a newest-created_epoch tie-break, working on an unanchored window. (Basis: the Step 0 write-manifest duty and the loader implementation, read this cycle.)
- The origin's temp-repo regression suggestion is dispositioned as the suite pins below (Markdown-free machinery change; the suite is the testing surface). (Basis: the origin's suggested fix versus the gates suite's established fixtures.)

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: A single-marker done run anchors its session window from its manifest and owned-commits ledger (anchor deliberately None so marker pruning stays conservative), and the origin's pending-sync arm is dispositioned as moot against the wholesale agent-side sync; force: reliability.

A closeout that recreates a code-review record late in the run has exactly one run-start marker, so the two-marker window is unanchorable and every window-scoped gate falls back to conservative empties - the review-staging gate sees no session candidates, and window-dependent behaviors silently under-include. After this plan the run's own manifest (bound to the current marker by filename) and its owned-commits ledger anchor the window at the manifest's `created_epoch`, so the gates scope correctly for fresh-start runs; without the witness pair the window stays unanchorable exactly as today. The origin's second arm asked for a durable record of sync-skipped artifacts, but the sync it witnessed against no longer window-skips: the lib's contract is "sync nothing" and the agent-side sync is wholesale, so that arm is recorded as moot rather than built.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the fallback fires only when fewer than two content-confirmable markers exist AND the witness pair is complete (parsable `created_epoch`, ledger on disk); the two-marker path and the unanchorable returns are otherwise unchanged.
- Conservatism: the fallback window carries `anchor=None`, so marker pruning and every anchor-keying consumer keep today's behavior.
- Minimality: no new state-file fields, no new artifacts, no docs-branch writes.

**Done when:**
- Every Validation Commands line exits 0, including the gates suite with the two new derivation pins.

**Ship when:**
- The next fresh-start done run's gates scope their candidates from the manifest-anchored window (operator-observed; external condition, no checklist item).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done_sweep_gates_lib.py`
- `agents/skills/done/SKILL.md`

**Tests:**
- `scripts/test_done_sweep_gates_lib.py`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/docs-branch/SKILL.md`; reason: the agent-side sync is wholesale and window-independent (Assumptions); no window restatement exists to amend (grep verified).
- the marker content/location backlog family; reason: marker content is not the defect, anchoring sufficiency is.
- a pending-sync sidecar artifact; reason: dispositioned as moot (Assumptions); nothing window-gates the sync.

## Validation Commands

```bash
TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"
"$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -q || { echo FAIL: gates suite; exit 1; }
grep -c "test_session_window_single_marker_falls_back_to_manifest_witness" scripts/test_done_sweep_gates_lib.py | grep -q -v "^0$" || { echo FAIL: fallback pin; exit 1; }
grep -c "test_session_window_manifest_without_ledger_stays_unanchorable" scripts/test_done_sweep_gates_lib.py | grep -q -v "^0$" || { echo FAIL: middle-arm pin; exit 1; }
grep -q "witness pair" agents/skills/done/SKILL.md || { echo FAIL: step-0 wording; exit 1; }
grep -q "when fewer than two markers are content-confirmable" agents/skills/done/SKILL.md || { echo FAIL: conservative default kept; exit 1; }
bash scripts/check_maintenance_pins.sh || { echo FAIL: pins baseline; exit 1; }
bash scripts/check-no-em-dash.sh file scripts/done_sweep_gates_lib.py agents/skills/done/SKILL.md docs/history/plans/2026-10-01-docs-branch-single-marker-window.md || { echo FAIL: em-dash; exit 1; }
```

### Task 1: the manifest-plus-ledger fallback anchor in derive_session_window

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

Evidence:
- `"$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -k single_marker_falls_back -q`; covers the fallback and its return shape

- [x] Run → expect RED: `grep -c "test_session_window_single_marker_falls_back_to_manifest_witness" scripts/test_done_sweep_gates_lib.py` returns 0 [class: REPOSITORY_TEST]
- [x] In `derive_session_window`, when fewer than two content-confirmable markers exist (today's unanchorable return): resolve this run's manifest via the existing load_run_manifest binding (the manifest's `marker` field equals the current marker's filename; the loader already root-matches and tie-breaks by newest `created_epoch`, and it works on an unanchored window), or failing that the newest root-matched manifest in the done-session dir; when the resolved manifest carries a parsable `created_epoch` AND the owned-commits ledger for its run id exists on disk, return `SessionWindow(anchored=True, anchor=None, current=the single marker, start_epoch=created_epoch, notes naming the witness pair)` - `anchor=None` deliberately keeps every anchor-keying consumer (marker pruning) conservative; a window with zero content-confirmable markers stays unanchorable (the witness pair is bound to the current marker; the secondary newest-root-matched arm applies only when exactly one marker exists), without the complete witness pair the window stays unanchorable exactly as today, and the two-marker path is untouched [class: IMPLEMENTATION_REQUIRED]
- [x] Add `test_session_window_single_marker_falls_back_to_manifest_witness` (fixture: one content-confirmable marker, its bound manifest with `created_epoch`, its owned-commits ledger; `window.anchored` is True, `window.anchor` is None, `window.start_epoch` is the manifest epoch, the note names the witness pair) and `test_session_window_manifest_without_ledger_stays_unanchorable` (manifest present, ledger missing; the window stays unanchorable with a witness-pair-incomplete note); the existing no-manifest unanchorable pins stay green unchanged [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the Evidence command; gates suite green [class: REPOSITORY_TEST]
- [x] Commit: `done-sweep: single-marker windows anchor from the manifest witness pair` [class: IMPLEMENTATION_REQUIRED]

### Task 2: the operator-facing restatement and the stale-premise disposition

Files:
- `agents/skills/done/SKILL.md`

Evidence:
- `grep -q "witness pair" agents/skills/done/SKILL.md`; covers the Step 0 restatement
- `grep -q "when fewer than two markers are content-confirmable" agents/skills/done/SKILL.md`; covers the conservative default kept

- [x] Run → expect RED: `grep -c "witness pair" agents/skills/done/SKILL.md` returns 0 [class: REPOSITORY_TEST]
- [x] In the Step 0 marker paragraph, after the existing fewer-than-two-markers sentence's conservative-gating clause, append: `A run whose manifest and owned-commits ledger both exist anchors its own window from that witness pair (the window's anchor stays unset, so marker pruning keeps its conservative behavior); without the complete pair the window stays unanchorable.` keeping the existing default sentence intact [class: IMPLEMENTATION_REQUIRED]
- [x] Record the stale-premise disposition in the task log: the origin's pending-sync arm is moot because the sweep-gates lib's contract is "sync nothing: this runner never touches the docs branch", every window consumer is a gate returning conservative empties, and the real docs-branch sync (done Step 2 invoking the docs-branch skill) is wholesale from disk and window-independent; quote the lib contract line and the docs-branch candidate-build span as the evidence, and note the origin's witnessed miss predates the machinery absorption [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the Evidence commands; both the witness-pair token and the conservative-default sentence present [class: REPOSITORY_TEST]
- [x] Commit: `done skill: single-marker window restatement and stale-premise disposition` [class: IMPLEMENTATION_REQUIRED]

### Task 3: full-suite validation

Files:
- none; verification-only task

Evidence:
- the full Validation Commands block; covers both pins, the Step 0 wording (witness pair plus the kept conservative default), the pins baseline, and em-dash

- [x] Run the full Validation Commands block from the repository root; every line exits 0 [class: REPOSITORY_TEST]
