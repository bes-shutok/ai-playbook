# Backlog: authoring-claim discovery misses convention-divergent claim filenames

Status: open
Workflow: backlog
Priority: medium
Origin class: self-serving
Quarantine: 2026-11-04
Class: fix-class
Driving force: consistency

Cluster: docs/history/backlog/2026-11-04-authoring-continuation-owner-attribution.md (same authoring-claim lifecycle, but this row owns peer-claim discovery before parallel authoring begins)

## Problem

Claim-presence checks key the claims directory scan on the checking session's own filename convention, but the claims directory carries both conventions in practice: slug-keyed claim files and origin-basename-keyed claim files. A single-key pattern scan therefore reports a clean authoring race while a foreign-convention claim sits in the same directory, so two sessions author competing plans for one origin and the loser's full review series is spent on text that can never land.

Witnessed 2026-11-03 (playbook repo, twin 18:13 auth carriers over one PLAN-PROMPTS entry): the loser's 18:22Z race re-check read clean while the winner's origin-basename claim file had been created the same minute; the winner landed 78a05db85 at 20:15:06Z under first-landed-wins while the loser sat paused at a provider usage wall, and the loser's r1-r4 series and worktree were discarded unread.

Prior same-class witness: 2026-09-30, two plans-skill Phase 0 lanes racing one origin (landing `0f4b7cf5` vs peers `a7b470e3`/`f18d818c`), fixed by wiring the AUTHORING CLAIM consult into selection (docs/history/plans/completed/2026-09-30-authoring-claim-cross-session-visibility.md); the 2026-11-03 collision recurred through the filename-convention gap that consult's canonical matching still assumes. The canonical claim filename is the backlog-item basename (the AUTHORING CLAIM duty in `agents/skills/maintenance/prompt-templates.md`); a noclobber create guards the filename, not the origin, so an off-convention claim file both evades peer discovery and gets no collision refusal at create time.

## Expected

A claim-presence check finds any existing claim for the origin or the entry regardless of which filename convention the claiming session used.

## Suggested change

Make claim discovery convention-independent: list the claims directory and match on the origin basename OR the entry slug (unfiltered listing, two-key match), or enforce the canonical backlog-item-basename convention (the AUTHORING CLAIM duty in `agents/skills/maintenance/prompt-templates.md`) with a same-change migration of the discovery call sites in the authoring lifecycle. The collision disposition (stand down, adopt, or first-landed-wins) then runs before authoring starts, not first at the duplicate-origin coverage gate at landing time.
