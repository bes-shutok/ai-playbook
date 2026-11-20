Status: covered (docs/history/plans/completed/2026-11-15-pr-review-hook-skill-name-ownership.md)
Workflow: backlog
Priority: medium
Origin class: consumer-feedback (company)
Class: fix-class
Driving force: reliability (primary), maintainability (secondary)
Added: 2026-11-09

# The PR-reference prompt hook tells the agent to invoke a skill that no longer exists, and it is not versioned with the other hooks

## Problem

A user-level `UserPromptSubmit` script (`~/.claude/scripts/pr-skill-reminder.sh`, wired in `~/.claude/settings.json`) injects, whenever a prompt contains a pull-request reference, the instruction to invoke the `receiving-code-review` skill for passive review. The skill is named `receiving-review`; `receiving-code-review` is a retired name. The hint fired about 19 times in one session (including on turns where the user had already typed the explicit `/receiving-review` command, where it is pure noise), each time pointing at a name that resolves to nothing. The agent recovered only because the user's own slash command named the right skill; an unprompted PR-URL message would have sent it looking for a skill that is not installed.

Why it survived the rename: the script is not in this repository. `agents/hooks/` versions the budget, model, lessons-recall, plan-readiness and skill-gate hooks and their install wiring, and the playbook's rename fan-out (grep sibling skills and instruction files for the old name) never reaches `~/.claude/scripts/`. Per-project agent memory files in other projects also still carry the retired name.

## Exact location

`~/.claude/scripts/pr-skill-reminder.sh` (outside the repo); `agents/hooks/` (missing home); the rename fan-out guidance in `agents/skills/how-to-write-skills/SKILL.md` and learn Step 1.2 item 5b (fan-out scope).

## Suggested fix and options considered

- **Recommended: version the hook and probe the names it emits.** Move the script under `agents/hooks/` with the same install/probe wiring as its siblings, correct the name to `receiving-review`, skip the injection when the prompt already begins with a slash command that names a skill, and extend the existing hooks probe (`python3 scripts/hooks_probe.py --all`) to assert every skill name inside a hook's emitted text exists under the installed skills directory.
- Patch the one string in place: rejected, the next rename repeats the failure; the cause is the missing owner and the missing check.
- Delete the hook: rejected, the PR-URL hint had value before the rename (it routes active versus passive review).

Machinery admission: the probe assertion is a small check on an existing probe. Incident = this session (19 injections with a dead skill name); expected catch frequency = every skill rename; false-positive cost = low; review date 2027-01-09.

## Severity and source

Medium. Source: learn Step 1.8 session analysis, 2026-11-09. Capture hygiene: scan-public-hygiene --files pass (recorded at commit).

## Why not fixed now

Capture only. The script lives outside the repository; editing it is a user-level change the analyzing session did not make.

## Dedup probe

Searched open items for `pr-skill-reminder`, `skill name` with `hook`, `rename fan-out`: no hits. The hooks README lists the versioned hooks and does not include this one.
