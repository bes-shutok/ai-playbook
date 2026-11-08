# Backlog: certification-time checkpoint skip carries no observation surface

Status: open
Priority: normal
Class: fix-class
Origin class: investigate over the 2026-11-03 coverage-gate-checkpoint-twin-self-exemption authoring session (session-witnessed process deviation)
Added: 2026-11-03

## Observed versus expected

The plans skill's certification-time checkpoint duty (`agents/skills/plans/SKILL.md` rule 6, the Certification-time checkpoint paragraph) binds the checkpoint to the turn that closes the final review round. In the witnessed authoring run the r8 round-close turn recorded the seal, passed the readiness full gate, and proceeded into the done closeout without committing the checkpoint; no surface (readiness gate, done setup, commit leg, landing, or reconcile) flagged the absence, and the run's post-round window held a quota-wall pause plus a session restart before the authoring landing landed the bytes. Expected: a later deciding turn in the same run either completes the checkpoint (byte identity to the certified digest) or records its absence as a deviation, so the durability gap is visible while the run is still alive.

## Reproduction evidence (trimmed)

- The certified plan's bytes first reached the primary checkout's plans root at the authoring landing adb12d26223186ec33c56f321295222da803647b (2026-11-03), not at the round-close turn; `git log --all -S` over the plan slug shows no checkpoint commit on main before that landing.
- The sibling duty binding in the same paragraph (deciding-turn step order, checkpoint preceding removal) landed as the ad-hoc entry deciding-turn-inherits-step-order; the total-skip class sits adjacent and uncovered.

- Second witness 2026-11-08 (the session-rollout-retention-postmortem-evidence authoring run, r5 certification): the checkpoint was attempted and skipped, recorded in the run report: a live peer held the primary done lock, and `scripts/done_run.sh commit` without a run manifest runs in rolling-log mode, which refuses any path outside the two rolling prompt logs, so a plans-root checkpoint commit has no manifest-free primitive; the plan bytes reached the primary checkout at the authoring landing.

## Suspected root area

The checkpoint paragraph binds a duty to one turn (round-close) with no recovery or observation arm for the case where that turn ends without the commit; every downstream surface assumes the checkpoint ran.

## Fix shape (arms, priced at plan time)

One binding sentence in the certification-time checkpoint paragraph: a deciding turn that finds the checkpoint absent at a later boundary before the authoring landing commits it then under the same record-keeping authority, or records the absence as a deviation line in the run's own records. Single surface, byte-balanced in the same file per the skill text anti-growth rules; no gate, no validator, no manifest schema change.
