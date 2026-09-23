# Backlog: plans skill-gate marker recipe is silent about which cwd keys the marker in ad-hoc-worktree sessions

Status: open
Priority: high
Workflow: backlog
Date: 2026-09-23
Origin: learn Step 1.8 capture from the P51 authoring run of docs/plans/2026-09-23-p51-plans-authoring-surface-hygiene.md (r5 ready=yes zero findings); skills-corpus workflow gap

## Skill and step

`agents/skills/plans/SKILL.md` Writing paragraph (marker duty) and `agents/hooks/skill-gate/README.md` "Marker WRITE RECIPE (plans class)"; interacting component: the skill-gate adapters' project-key derivation (`facts_paths.resolve_project_key`), which keys the marker by the write target's directory walk.

## Observed versus expected

Observed: in an ad-hoc-worktree authoring session, the marker write recipe was executed from the primary checkout's cwd (the session shell resets cwd between calls, and the natural habit is to run the documented one-liner from the checkout root). The marker landed keyed to the primary checkout's project key, while the gated Write targeted the worktree, whose directory walk derives a DIFFERENT project key (a worktree root is not the primary root for the key derivation). A gate consult keyed that way finds no fresh marker for the worktree project and blocks the plan-file write. The session recovered by re-running the marker write from inside the worktree cwd so the key matched the write target, but only after diagnosing the mismatch from the marker directory listing.

Expected: the marker recipe states which cwd (or explicit key input) the marker write must run from when the session authors inside an ad-hoc worktree: keyed to the WRITE TARGET's project derivation (the worktree), not the session's default or primary checkout cwd. One prescriptive sentence in the plans skill's marker duty and one in the skill-gate README's recipe (step 4 or 5) close it; an optional core-side `--cwd` pass-through from the write recipe is a mechanical alternative.

## Reproduction

1. Create an ad-hoc worktree of a gated repo; run `git worktree add -b <branch> <sibling> <default>`; copy gitignored facts in.
2. From the PRIMARY checkout cwd, run the marker write recipe (`session_channel.py` then `skill_gate.py --write-marker`), then verify a fresh marker exists keyed to the PRIMARY project key.
3. Write the plan file under the WORKTREE's `docs/plans/`; a wired gate consult derives the worktree's project key, finds no fresh marker under that key, and blocks.

## Suspected root area

The marker WRITE RECIPE (README, single source) and the plans skill's marker-duty sentence derive `project` per the README's Terms but never name the cwd/key relationship for worktree sessions; the adapters already carry the empty-cwd fallback (derive from the write target's dirname), which the recipe could simply reference as the expected behavior for ad-hoc-worktree authoring.

## Environment

ZCode runtime, 2026-09-23, repo copy and runtime source of the skills (agents/skills/plans, agents/hooks/skill-gate); the witnessing session is this repository's own authoring automation child.
