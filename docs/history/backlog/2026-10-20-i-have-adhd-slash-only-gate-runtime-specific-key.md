# Backlog: i-have-adhd's slash-only gate rides a runtime-specific frontmatter key that other runtimes ignore

- **Filed:** 2026-10-20, all-skills loader review after the execute-plan description fix (learn Step 1.8 capture)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium (Step 1.8's high default lowered: divergence only, no witnessed harm this session)
- **Origin class:** session-witnessed cross-runtime portability gap in a vendored skill's frontmatter
- **Class:** fix-class
- **Driving force:** correctness (the author's "explicit invocation only" intent holds on one runtime and silently does not on another)
- **Skill/step:** `agents/skills/i-have-adhd/SKILL.md` frontmatter (`disable-model-invocation: true`); AGENTS.md Skill Design Guidelines, tool-agnostic design bullet; AGENTS.md Vendored Asset Sync Rules (the skill is vendored from its upstream with no local fork notice; README row names it opt-in via `/i-have-adhd`)
- **Capture hygiene:** repo-relative paths only; the upstream URL already appears in the skill's own metadata and README row.
- **Dedup probe:** searched open backlog text for `disable-model-invocation`, `runtime-specific key`, `frontmatter key`, `i-have-adhd`; no hits.

## Problem

The skill marks itself slash-only with `disable-model-invocation: true`, a frontmatter field one agent runtime honors. Another runtime's loader recognizes only `name`, `description`, `when_to_use`, `license`, and `metadata` (its skill-diagnostics guide lists them) and ignores unknown top-level keys, so there the skill loads as an ordinary model-invocable skill: the model may switch the user's output into ADHD-shaping mode on its own judgment, which is exactly what the key was meant to prevent. The description's "Invoke with /i-have-adhd" sentence is the only remaining signal, and a description is a trigger hint, not a gate.

This is the tool-agnostic design rule in its frontmatter form: an intent expressed through one runtime's vocabulary does not travel. The skill is vendored, so any frontmatter change is a local-fork decision that the sync rules require recording (the way `grilling` and `grill-with-docs` carry a Local fork notice).

## Expected

The same invocation intent on every runtime the repository targets: the skill stays dormant until the user names it, and a runtime that cannot gate honors the intent through the fields it does read.

## Suggested fix

Smallest form first:

1. Add a portable `when_to_use` line stating that the skill is used only when the user explicitly names it (and is otherwise never invoked), keeping `disable-model-invocation` for the runtime that honors it; the loader that ignores the key presents `when_to_use` to the model, which is the strongest portable signal available.
2. Record the change as a deliberate local fork: a Local fork notice in the skill body and a line in the Vendored Asset Sync Rules' fork list, so an upstream sync re-applies it instead of overwriting it.
3. Generalize by one sentence in `how-to-write-skills` frontmatter requirements: a runtime-specific gating key is paired with portable `when_to_use` wording.

Rejected: removing `disable-model-invocation` (loses the hard gate on the runtime that honors it); a runtime-side hook that hides the skill (tool-specific machinery with no witnessed incident); leaving the divergence undocumented (the README row promises opt-in behavior the skill does not deliver everywhere).
