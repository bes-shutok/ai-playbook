# Backlog: release-notes time-span claim written without measuring the previous release boundary

- **Status:** deferred (2026-10-06, operator adjudication: the remaining prevention arm is a prevention gate for a prose claim in a rare manual workflow; detection already worked)
- **Origin:** operator review of the published 2026-10-04 release (main 10a22175, push 2026-10-04); the CHANGELOG opening sentence says "a month of maintenance-loop hardening" while the previous release landed 2026-09-27 (backup ref refs/release-backup/pre-release-2026-09-27-2, its notes commit and CHANGELOG section dated that day), making the real span exactly one week
- **Driving force:** truthfulness of published prose - the release workflow measures the commit delta mechanically, but nothing in the workflow measures or gates the time span claimed in the CHANGELOG opening sentence; the drafting agent wrote the span from the pile's start date and volume impression and never cross-checked it against the previous release boundary, and no gate caught it, so the false claim published to the remote

## Outcome

Two-part closure:

1. Correction: the published 2026-10-04 CHANGELOG opening sentence states the true span (one week, 2026-09-27 to 2026-10-04), fixed by a forward commit on main, no history rewrite.
2. Prevention: the release-notes span claim becomes evidence-derived and gated, so a future run cannot publish an unverified span. Candidate mechanisms, to be adjudicated during authoring (they are alternatives, not a bundle):
   - Authoring-rule arm: the release skill's CHANGELOG authoring rules gain a duty to derive any time-span phrase from the measured boundaries only (previous section date in CHANGELOG or the newest refs/release-backup ref date, versus today) and to drop the phrase when the derivation is not performed.
   - Mechanical-gate arm: a check (or an arm in scripts/release-authoring.sh) that parses the drafted section for a time-span expression, recomputes the span from the delta boundaries, and fails the authoring step on mismatch or on an unverifiable span token ("month", "week", "days") lacking a derivation note in the run output.
   - Selftest arm: the release authoring selftest gains a fixture pair (span matches boundaries: green; span overstates: red) if the mechanical-gate arm is chosen.
   - Template arm (cheapest, weakest): the skill's example section shape gains a placeholder comment telling the author to compute the span from the previous release date, no enforcement.

Ship when: the correction commit is on origin/main; the chosen prevention mechanism is live in the release skill or its scripts with its selftest or fixture green; the release skill text documents the derivation duty; the em-dash gate and hygiene scan pass on the changed files.

Rejected alternatives (recorded at filing):
- Rewriting the published release commit to fix the sentence in place: rejected, the release contract never rewrites pushed history and a forward fix is cheap and honest.
- Banning time-span phrases outright in CHANGELOG openings: rejected, the span is genuinely useful to a reader when it is true; the fix is verification, not deletion.
- Backlabeling older CHANGELOG sections: rejected, they are published records; only the current section's claim is this release's own prose.
