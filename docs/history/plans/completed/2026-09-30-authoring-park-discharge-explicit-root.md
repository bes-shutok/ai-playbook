# Plan: Authoring park discharge explicit-rooted state access

Backlog origin: docs/history/backlog/2026-09-28-maintenance-authoring-park-discharge-cwd-relative.md
Driving force: code-quality
Plan review record: the staging series docs/reviews/2026-09-30-plan-review-authoring-park-discharge-explicit-root-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

The authoring payload's closing park discharge duty reads the scheduler state file in the explicit-rooted form, so a discharge performed from an ad-hoc worktree mutates the primary checkout's real scheduler state instead of silently no-oping on a per-worktree gitignored copy.

- A parked `pending_rearm` or `pending_dispatch` recorded by a run that later discharges from its ad-hoc worktree is actually consumed; today that discharge writes (or would write) a file no reader reads.
- Both blueprint bodies' discharge paragraphs carry the same rooted form again, ending the divergence a future single-paragraph edit to one body would silently miss.

Gate delta: none. The change roots one existing state-file access path; it adds no refusal class, no gate, and no checked condition - it removes a false write target (the class-default sanctioned exit for a fix-class origin), exactly the amendment the r4 address pass applied to the paragraph's three twin sites.

## Assumptions

- assume the fix is one paragraph amendment: the authoring fenced body's `CLOSING PARK DISCHARGE DUTY` paragraph (prompt-templates.md line 86 region, the first fenced body) gains the explicit-rooted clause byte-identical to the execution body's twin at the same paragraph (verified on this tree: line 86 reads the bare `read .ai-playbook/scheduler-state.json` form while the execution twin at line 287 and the unblock child at line 378 carry the rooted clause); basis: the origin's Observed-versus-expected section and its own round-5 refinement.
- assume the item's second half (rooting the FIRST ACTION re-arm state probes) is retracted and out of scope: those probes fire pre-worktree, where the cwd-relative read resolves the primary checkout correctly by design; basis: the origin's Refinement paragraph (2026-09-28, round-5 re-derivation) narrows the fix to the CLOSING PARK DISCHARGE paragraph only.
- assume the rooted clause wording is taken verbatim from the execution body's twin (the same clause the r4 fix landed there), so the two paragraphs stay byte-aligned in their shared shape; basis: the origin's divergence concern is precisely that the twins drift.
- assume the pins suite (`scripts/check_maintenance_pins.sh`, verified exit 0 on this tree today) is the mechanical gate: the plan adds one polarity pin for the bare form and re-runs the suite, re-keying any anchor whose count shifts; basis: the origin's Suggested fix names exactly this procedure, and the suite's discharge-anchor pin (count of `CLOSING PARK DISCHARGE DUTY` equal to 3) is unaffected by a clause that changes no anchor phrase.
- assume the runtime copy at `~/.agents/skills/maintenance/` is a real directory (verified on this host, not a symlink), so the landed repo copy propagates to the runtime only through an explicit vendored-sync step recorded under Ship when; basis: the repository guidelines' vendored-asset sync rules.
- assume the origin item's declared class agrees with a fix-class re-derivation; basis: the header declares the bare token `Class: correctness` with a parenthetical tail naming the defect (a cwd-relative state access targeting a copy no reader reads), which is a witnessed false-target removal, so the declared correctness class and the fix-class routing agree.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the authoring payload's closing park discharge reads the scheduler state through the primary checkout's explicit root, ending the last cwd-relative cross-checkout state access; the driving force is code-quality (a discharge must mutate the state every reader reads).

Before (today): an authoring session finishing in its ad-hoc worktree runs its CLOSING PARK DISCHARGE DUTY, which reads `.ai-playbook/scheduler-state.json` relative to the cwd - inside the worktree that resolves to the worktree's own gitignored copy, so the discharge observes no parked intent (or writes its clear into a file no reader reads) and the parked intent silently survives in the primary checkout's real state file. The execution body's twin paragraph carries the explicit-rooted clause; the authoring body does not, so the two no longer match byte-for-byte.

After (this plan): the authoring paragraph reads `read the primary checkout's .ai-playbook/scheduler-state.json` with the same explicit-rooted clause the execution twin carries, and a new polarity pin in the pins suite fails the suite whenever the bare duty-prefixed form reappears in the file. A discharge from a worktree now targets the state file every reader shares.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the authoring discharge paragraph carries the rooted clause; no `CLOSING PARK DISCHARGE DUTY, before ending: read .ai-playbook/scheduler-state.json` bare-prefixed form remains anywhere in the file.
- regression safety: the pins suite stays exit 0 with the new pin armed; the three discharge-anchor occurrences are unchanged.
- maintainability: the polarity pin makes the regression class (a cwd-relative cross-checkout state access reintroduced by a future edit) a suite failure, not a review catch.

**Done when:**
- The authoring body's discharge paragraph carries the rooted clause and the pins suite exits 0 including the new pin.
- All Validation Commands exit 0 from the worktree root.

**Ship when:**
- The runtime twin `~/.agents/skills/maintenance/prompt-templates.md` is refreshed from the landed repo copy at execution closeout (real directory, explicit vendored sync), with the refresh witnessed in the execution report by a byte-comparison receipt (the copied file's sha256 recorded beside the repo copy's sha256, both taken at closeout); consumer runtimes pick the skill up through their normal vendored-asset sync.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/prompt-templates.md`

**Tests:**
- `scripts/check_maintenance_pins.sh`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- The re-arm duty set's state probes in both bodies; reason: the origin's own round-5 refinement retracts that half (pre-worktree probes resolve correctly by design).
- The execution and unblock-child discharge paragraphs; reason: already rooted by the r4 fix; this plan only re-aligns the authoring twin.

## Validation Commands

```bash
# 1. The pins suite passes with the new polarity pin armed.
bash scripts/check_maintenance_pins.sh || { echo "FAIL: pins suite" >&2; exit 1; }

# 2. The bare duty-prefixed state read is gone (the new pin's own assertion, run directly).
[ "$(grep -cF 'DUTY, before ending: read .ai-playbook/scheduler-state.json' agents/skills/maintenance/prompt-templates.md)" -eq 0 ] || { echo "FAIL: bare cwd-relative discharge read remains" >&2; exit 1; }

# 3. The rooted clause is present in the authoring body (distinctive clause span, pin-once in the amended paragraph).
grep -qF 'CLOSING PARK DISCHARGE DUTY, before ending: read the primary checkout' agents/skills/maintenance/prompt-templates.md || { echo "FAIL: rooted discharge missing" >&2; exit 1; }

# 4. The three discharge anchors survive (the existing count pin's assertion, run directly).
[ "$(grep -cF 'CLOSING PARK DISCHARGE DUTY' agents/skills/maintenance/prompt-templates.md)" -eq 3 ] || { echo "FAIL: discharge anchor count moved" >&2; exit 1; }

# 5. Em-dash gate over the branch's added lines.
bash scripts/check-no-em-dash.sh added-lines --base main || { echo "FAIL: em-dash gate" >&2; exit 1; }
```

Authoring-time gate record (rule 29/19/22): the pins suite was executed on this tree before authoring (exit 0); the behavioral reads were executed directly: Command 2's bare form count is 1 today (the witnessed line 86), so Command 2 and Task 1's identical pin assertion both fail today (RED); Command 3's presence span already occurs in the two rooted twin paragraphs today and passes, extending to the amended paragraph after the fix (it is a presence pin, not a count pin). Command 4's count is 3 today and the amendment does not touch the anchor phrase. Rule 22 mechanical audit: Command 2's asserted span is an absence assertion (polarity); Command 3's pin span occurs in Task 2's prescription exactly once beside its Command occurrence (plan-wide mentions in Gist and Assumptions are not pin sites); `bash -n` over this block passed.

### Task 1: Arm the polarity pin (RED)

Files:
- `scripts/check_maintenance_pins.sh`

Evidence:
- `bash scripts/check_maintenance_pins.sh`; covers: the suite fails today on the new pin and passes after Task 2.

- [ ] Add one pin beside the existing discharge-anchor pin: the count of `DUTY, before ending: read .ai-playbook/scheduler-state.json` in `agents/skills/maintenance/prompt-templates.md` must equal 0 (the same `[ "$(grep -cF ... )" -eq 0 ]` shape the suite's other pins use, with a `PIN FAIL: cwd-relative discharge read reintroduced` message). [class: REPOSITORY_TEST]
- [ ] Run → expect RED: `bash scripts/check_maintenance_pins.sh` exits non-zero naming the new pin (the bare form occurs once today). [class: REPOSITORY_TEST]
- [ ] Commit: `test: pin cwd-relative discharge read polarity (RED)` [class: REPOSITORY_TEST]

### Task 2: Root the authoring discharge paragraph (GREEN)

Files:
- `agents/skills/maintenance/prompt-templates.md`

Evidence:
- `bash scripts/check_maintenance_pins.sh`; covers: the new pin passes and no other pin shifts.

- [ ] In the authoring fenced body's `CLOSING PARK DISCHARGE DUTY` paragraph, replace the opening `read .ai-playbook/scheduler-state.json` with the execution twin's rooted form: `read the primary checkout's `.ai-playbook/scheduler-state.json` (explicit-rooted form per the claim duty's precedent; a cwd-relative edit from the ad-hoc worktree would write a per-worktree gitignored file no reader reads)`, changing no other bytes of the paragraph. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: `bash scripts/check_maintenance_pins.sh` exits 0 (the new pin passes; if any count-keyed pin shifted, re-key it in the same edit and record the re-key in the commit message). [class: REPOSITORY_TEST]
- [ ] Commit: `fix: root authoring park discharge state read to the primary checkout` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Whole-plan validation gate

Files:
- `agents/skills/maintenance/prompt-templates.md`

Evidence:
- The full `## Validation Commands` block run from the worktree root; covers: every criterion in Done when.

- [ ] Run the complete `## Validation Commands` block from the worktree root; every command exits 0. [class: REPOSITORY_TEST]
- [ ] Commit: `test: whole-plan validation for authoring park discharge explicit root` [class: REPOSITORY_TEST]
