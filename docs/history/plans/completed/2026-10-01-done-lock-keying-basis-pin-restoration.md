# Done-lock keying basis pin (restores the pre-re-key S15 protection scope)

Backlog origins (scope of record): `docs/history/backlog/2026-09-28-s15-rekey-narrowed-done-lock-gate-pin.md`

Classification: [class: test-class] pins-suite coverage restoration over landed prose; no runtime behavior changes.

## Terminology and core concepts

- **Pins suite**: `scripts/check_maintenance_pins.sh`; each `pin "desc" grep ...` (or inline `[ count -eq N ]` check) prints `PIN FAIL: <desc>` and sets `fail=1`; the per-section `[ "$fail" -eq 1 ] && exit 1` gates terminate the suite. `fail` is sticky, so a pin placed after its own section's gate is still caught by the next gate — but a pin placed after the FINAL gate (script tail, ~line 2011) prints its failure yet the suite exits 0, and code past the final `exit 0` never runs at all. Insert pins before their section's gate, per the suite's convention.
- **Re-key**: when the pinned prose is rewritten, the pin is re-pointed at the new span. The suite's own convention (stated in its freeze-literal header): a wording change to a pinned span must reconcile pin and text in the same edit AND record the superseding origin, so the re-key preserves the old pin's protection scope.
- **Coverage narrowing** (the defect class here): the 2026-09-28 re-key moved the per-run pre-work gate pin onto the gate's done-lock conjunct only (`the run's own per-worktree done lock is free`), dropping the done-lock keying basis from pin coverage. S20 separately pins the scoping tail (`so the run's done lock is its own`), but the keying basis sentence between them is unpinned: deleting it leaves the suite green while the gate's documented semantics (done locks are per-worktree-keyed, on `--show-toplevel`) silently vanish. (The origin item's "stand-down clause" gloss is loose: the stand-down is the consequence clause, not the pinned conjunct.)
- **Keying basis span**: `locks are keyed per-worktree on --show-toplevel` — contiguous on a single prompt-templates.md line (wrap-clean; the surrounding sentence wraps across lines, so the pin fragment must stay inside that one line, never spanning the wrap before `locks`).

## Coverage dispositions (verified on disk 2026-10-01, do not re-implement)

- The prose is landed and correct: `agents/skills/maintenance/prompt-templates.md` line "Then run the done skill ONLY on clean exit; it runs in this worktree; done / locks are keyed per-worktree on --show-toplevel, / so the run's done lock is its own (...)". This plan adds ONLY the missing pin; the prose stays untouched.
- S20 (`P57 S20 done-lock per-run scoping span`) and the re-keyed S15 (`per-run pre-work gate span (re-keyed 2026-09-28; was P57 S15)`) already exist and stay untouched.
- The pins suite is green on the authoring tree (verified 2026-10-01 on branch `done-lock-keying-basis-pin` @ afc3bb8c: `bash scripts/check_maintenance_pins.sh` exits 0 with `maintenance pins: all hold`).
- The re-key history is verifiable at `docs/history/plans/completed/2026-09-28-worktree-first-standard-only-mode.md` Task 4 (commit 5cb09eb1 performed the re-key); the suite's own comment convention cites the bare filename.
- Out of scope: the same keying invariant also appears unpinned in `agents/skills/maintenance/SKILL.md`'s supersession paragraph (~line 327); that is a separate surface and a separate origin if ever warranted — this plan does not cover it.

## Outcome

The maintenance pins suite fails when the execution blueprint's done-lock keying basis sentence is deleted, rewritten in place, or duplicated, restoring the protection scope the pre-consolidation S15 span carried. (Relocation of the phrase to another spot in the file is not detected by this count; the gate paragraph's own flanking pins — the re-keyed S15 done-lock conjunct and the S20 scoping span, both presence greps — anchor that paragraph.)

## Gate delta

`scripts/check_maintenance_pins.sh` gains one exactly-once inline count pin in the existing S16 style, plus a comment paragraph note; no other file's behavior changes.

## Assumptions

- The keying basis fragment remains semantically load-bearing (it is the only place the execution body names the done lock's keying basis and its `--show-toplevel` key).
- `expect_absent_flat` is NOT the right helper here: it asserts absence; this pin asserts exactly-once presence.
- Exactly-once count over a lighter `grep -qF` presence pin is deliberate: prompt-templates.md is the file where presence pins go vacuous — its amendment ledger already paraphrases this very done-skill sentence, and a future ledger entry quoting the operative sentence verbatim would silence a presence pin while the count still trips on deletion.

Decision points requiring a grill: none remain.

## Gist

One pin, one comment paragraph, three mechanical proofs (unpinned-today RED direction, suite-green after, mutation witness proving the pin trips on deletion and restores clean).

## Evaluation Criteria

- The suite exits 0 on the landed tree with the new pin present.
- Removing the keying basis phrase from prompt-templates.md makes the suite exit 1 naming the new pin; restoring the phrase returns the suite to exit 0.
- The pin sits before its section's `[ "$fail" -eq 1 ] && exit 1` gate.

## Review Scope

Inventory: `scripts/check_maintenance_pins.sh` (pin + comment paragraph), `agents/skills/maintenance/prompt-templates.md` (Task 3 mutation witness only; landed bytes must be identical to HEAD after restore). Verify pin placement is before the section gate, the fragment is wrap-clean and exactly-once, the comment paragraph's history claim matches the origin item, and the mutation-witness evidence is real (suite output quoted, restore verified).

## Validation Commands

- `bash scripts/check_maintenance_pins.sh` → exit 0, prints `maintenance pins: all hold`
- `grep -c 'locks are keyed per-worktree on --show-toplevel' scripts/check_maintenance_pins.sh` → 0 before Task 2 (RED), 1 after (GREEN; the pin line is the only carrier — the comment paragraph must describe the span without quoting this literal)
- `grep -c 'locks are keyed per-worktree on --show-toplevel' agents/skills/maintenance/prompt-templates.md` → 1
- `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh` → exit 0 (landing-time gate, run from repo root)

## Tasks

### Task 1: mechanical RED-today proofs (no edits)

Files:
- `scripts/check_maintenance_pins.sh` (read-only this task)
- `agents/skills/maintenance/prompt-templates.md` (read-only this task)

- [x] Run → expect RED: `grep -c 'locks are keyed per-worktree on --show-toplevel' scripts/check_maintenance_pins.sh` prints 0 (grep exits 1) — the keying basis is unpinned [class: REPOSITORY_TEST]
- [x] Run → expect exact counts: `grep -c 'locks are keyed per-worktree on --show-toplevel' agents/skills/maintenance/prompt-templates.md` prints 1, and `grep -c "so the run's done lock is its own" scripts/check_maintenance_pins.sh` prints 1 (S20 sibling present), and `bash scripts/check_maintenance_pins.sh` exits 0 [class: REPOSITORY_TEST]

### Task 2: add the keying-basis pin

Files:
- `scripts/check_maintenance_pins.sh`

- [x] In the dual-arm landing block (the S16–S20 section), immediately AFTER the `P57 S20 done-lock per-run scoping span` pin line and BEFORE that block's `[ "$fail" -eq 1 ] && exit 1` gate, add an exactly-once inline count pin in the S16 idiom — occurrence count via `grep -oF 'locks are keyed per-worktree on --show-toplevel' "$P" | wc -l` equal to 1 (the `grep -oF | wc -l` form, NOT `grep -cF`; the sibling S16 lines append `| tr -d ' '` to strip `wc` padding — both forms pass, keep whichever matches the neighboring lines), with its own `PIN FAIL:` label reading `done-lock keying basis (restores pre-consolidation S15 scope; origin 2026-09-28-s15-rekey-narrowed-done-lock-gate-pin)` [class: REPOSITORY_TEST]
- [x] Extend that block's comment paragraph with the restoration note: the 2026-09-28 re-key (plan `2026-09-28-worktree-first-standard-only-mode.md` Task 4 — archived under `docs/history/plans/completed/`; the sibling comments cite the bare filename) narrowed the gate pin to the gate's done-lock conjunct; the keying basis between that conjunct span and the S20 scoping span was left unpinned; this pin restores that coverage, and a wording change to the keying sentence must reconcile pin and text in the same edit and record the superseding origin per the suite's freeze-literal convention. The comment must describe the pinned span WITHOUT quoting the counted literal (a verbatim quote would break the exactly-once GREEN count) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `bash scripts/check_maintenance_pins.sh` exits 0 and `grep -c 'locks are keyed per-worktree on --show-toplevel' scripts/check_maintenance_pins.sh` prints 1 [class: REPOSITORY_TEST]

Evidence:
- `bash scripts/check_maintenance_pins.sh; echo $?` → `maintenance pins: all hold` and `0`

### Task 3: mutation witness (delete → RED → restore → GREEN)

Files:
- `agents/skills/maintenance/prompt-templates.md` (mutated temporarily, MUST be restored to HEAD bytes)

- [x] Mutate with exactly this command: `sed -i '' 's/locks are keyed per-worktree on --show-toplevel/keying-basis placeholder (mutation witness)/' agents/skills/maintenance/prompt-templates.md`, then run → expect RED: `bash scripts/check_maintenance_pins.sh` exits 1 and its output names the new pin's `PIN FAIL:` label [class: REPOSITORY_TEST]
- [x] Restore with `git checkout HEAD -- agents/skills/maintenance/prompt-templates.md`, then run → expect GREEN: suite exits 0, `git status --porcelain agents/skills/maintenance/prompt-templates.md` prints nothing, and `git diff HEAD --stat` shows no residual mutation in either touched file beyond `scripts/check_maintenance_pins.sh` [class: REPOSITORY_TEST]
