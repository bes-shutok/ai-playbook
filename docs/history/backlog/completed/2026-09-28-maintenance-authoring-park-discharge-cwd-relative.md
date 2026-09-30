Status: done (2026-09-30; executed+landed docs/history/plans/completed/2026-09-30-authoring-park-discharge-explicit-root.md, squash main 09fd0d49, exec review r1 ready=yes zero blocking)
Priority: high
Workflow: backlog
Class: correctness (a cwd-relative scheduler-state read or write from an ad-hoc worktree targets the per-worktree gitignored copy no reader reads)
Driving force: correctness
Consumer urgency: consumer projects that run the maintenance payloads from an ad-hoc worktree hit the same silent discharge no-op; the skills-repo personal priority profile must not park or defer this as formal-hardening for the skills repo alone.

# Authoring payload park discharge and re-arm duties still read scheduler state cwd-relative

**Exact location:** `agents/skills/maintenance/prompt-templates.md`, the authoring fenced payload body's `CLOSING PARK DISCHARGE DUTY` paragraph (bare `read .ai-playbook/scheduler-state.json`), and the same body's compact re-arm/successor-carrier duty set's bare `read .ai-playbook/scheduler-state.json` state probe.

## Problem

The worktree-first r4 address pass added the explicit-rooted clause (read the primary checkout's `.ai-playbook/scheduler-state.json`, explicit-rooted form per the claim duty's precedent, because a cwd-relative edit from the ad-hoc worktree would write a per-worktree gitignored file no reader reads) to four cross-checkout state-file sites: the authoring payload's successor-carrier closeout verification, the execution payload's successor dispatch, the execution payload's closing park discharge, and the parked-dependency unblock child's closing park discharge. The authoring body's own discharge paragraph and the re-arm duty set's state probe were not among the enumerated sites and still read the state file cwd-relative. From an ad-hoc worktree a cwd-relative read or write targets the per-worktree gitignored `.ai-playbook/scheduler-state.json`, so the discharge silently no-ops and the re-arm probe reads the wrong copy. Before that fix the two blueprints' discharge paragraphs were byte-identical; they now diverge, so a future single-paragraph edit to one body silently misses the twin.

## Observed versus expected

- Observed: the authoring body's discharge paragraph reads bare `.ai-playbook/scheduler-state.json` while the execution and unblock-child discharge paragraphs carry the explicit-rooted clause.
- Expected: every cross-checkout scheduler-state access in both payload bodies uses the explicit-rooted form, matching the claim duty's precedent.
- Refinement (2026-09-28, round-5 re-derivation): the round-5 re-derivation confirms the discharge-paragraph half; the item's second half (rooting the FIRST ACTION re-arm state probes) over-reaches. Those probes fire pre-worktree, where the cwd-relative read resolves correctly by design: the FIRST ACTION runs before the ad-hoc worktree exists, so the session is still in the primary checkout and the bare read hits the real scheduler state. The fix this item should drive covers the CLOSING PARK DISCHARGE paragraph only; the execution and unblock twins were already rooted by the r4 fix, and the authoring body's twin remains.

## Suggested fix

Apply the same explicit-rooted clause to the authoring body's `CLOSING PARK DISCHARGE DUTY` paragraph and the re-arm duty set's state probe; re-run the pins suite after the edit and re-key any anchor whose count shifts.

## Source reference

Sibling observation recorded (out of the r4 staged set) during the address pass for review round r4 of docs/reviews/2026-09-28-worktree-first-standard-only-mode-code-review-r4.md, then re-verified against the working tree (clause count 4; the authoring discharge line carries none); captured here per learn Step 1.8 because the address log is a gitignored session record and must not be the only record. Why not fixed now: content edits are outside this iteration's authorized review-fix commit scope. Capture hygiene: scan-public-hygiene --files pass.

Dedup probe: searched the open backlog corpus for park discharge, cwd-relative, RE-ARM, and scheduler-state; the only keyword hit is an unrelated done-lock gate-pin re-key item; the r4 fix's own four sites are committed content, not open items; no overlap.

Origin class: self-serving
