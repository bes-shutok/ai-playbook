# Plan: execute-plan skill-gate marker before plan-file edits

Blocks: resume of `docs/plans/2026-08-03-plan-executable-task-gates.md` (paused after Task 1 implement; checkboxes not marked because skill-gate denied the orchestrator edit).

## Terms

| Term | Meaning |
|------|---------|
| Skill-gate marker | Fresh per-(project, session) consent file under `~/.ai-playbook/runtime/skill-invoked/` that admits Write/StrReplace on gated plan paths |
| Marker WRITE RECIPE | Canonical steps in `ai-playbook/agents/hooks/skill-gate/README.md` (plans class); skills reference it, do not restate constants |
| Session channel | Opaque session id from `session_channel.py` (`CLAUDE_CODE_SESSION_ID` or `CURSOR_SESSION_ID`); empty becomes `no-session` |

## Gist & Examples

**Problem:** `execute-plan` Step 1.3 tells the orchestrator to edit the plan file (flip `- [ ]` → `- [x]`). Cursor skill-gate blocks those edits unless a fresh plans-class marker exists for the current session. Only the `plans` skill documents the marker WRITE RECIPE. `execute-plan` never requires it, so checkbox marking fails with "Invoke the plans skill before authoring a plan file" even though execute-plan is the legitimate writer.

**Related incident (same family):** when the Cursor hook runs with an empty or non-repo `cwd` while `CURSOR_SESSION_ID` is set, the gate keys a different project component than a marker written from the repo root. Adapter cwd handling is out of scope here; this plan only wires the recipe into `execute-plan` so the orchestrator refreshes the marker the same way `plans` does (from the repo workspace).

**Fix:** Before every orchestrator plan-file Write/StrReplace (Step 1.3 checkbox marking, Recovery checkbox marking, and any other execute-plan path that edits plan Markdown via Write/StrReplace), refresh the marker using the same recipe `plans` already references. Reorder Recovery to mark checkboxes (after marker refresh) **before** `done`, matching Phase 1. Do not weaken the gate. Do not duplicate window/filename/hash constants in the skill; point at the README.

**Before / after:**

- Before: Step 1.3 → StrReplace plan → skill-gate deny (missing session marker, or project key mismatch when the writer never ran the recipe).
- After: Step 1.3 → run WRITE RECIPE (`session_channel.py` + `skill_gate.py --write-marker`, fail-loud) → StrReplace plan → allow when marker fresh for that session/project keying.

**Out of scope for this plan:** fixing Cursor hook empty-cwd / no-anchor project keying; finishing the paused executable-task-gates plan (resume after this lands).

### Design Invariants (CR Guard)

- README remains the single source for the marker WRITE RECIPE; skill text references it.
- Gate stays fail-closed; no bypass, no "orchestrator is exempt" language.
- Same session-channel subprocess idiom as `plans` (Family D: one helper).
- Public skill stays tool-agnostic in prose (refresh marker before plan-file write); name the README Marker WRITE RECIPE section; do not restate CLI paths or constants in the skill.

## Evaluation Criteria

**Quality dimensions (Done when):**
- Correctness: Step 1.3 (and every other execute-plan plan-Markdown Write/StrReplace path called out in tasks) requires marker refresh before the edit; fail-loud if unwritable.
- Consistency: wording points at `ai-playbook/agents/hooks/skill-gate/README.md` Marker WRITE RECIPE (plans class); no inlined `SKILL_GATE_WINDOW` / hash rules.
- Hygiene: `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh` exits 0.

**Ship when:**
- None (skill text only).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope:

**Production code (skill Markdown):**
- `agents/skills/execute-plan/SKILL.md`

**Tests:**
- *(none; validation is grep + hygiene scan)*

**Plan-related extension**; implementation and review may change files not listed above when causally tied to this plan (for example a one-line cross-reference in `agents/skills/plans/SKILL.md` Integration Points). Drop unrelated findings with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/hooks/skill-gate/*.sh` and `skill_gate.py` behavior changes; gate stays as-is.
- Cursor empty-cwd / no-anchor adapter fix (separate follow-up).
- Edits under `docs/plans/completed/`.
- Completing `2026-08-03-plan-executable-task-gates.md` tasks.

## Validation Commands

```bash
# Fail-closed: every required positive check and every forbidden match must abort (do not rely on set -e / ! alone).

# Step 1.3: marker refresh BEFORE plan-file update (character order; catches same-line inversion)
step13=$(grep -nE '### Step 1\.3: Mark plan progress' -A6 agents/skills/execute-plan/SKILL.md)
case "$step13" in
  *'Plan-file edits'*'update the plan file'*) ;;
  *) echo "Step 1.3: Plan-file edits must precede update the plan file"; exit 1 ;;
esac

# Dedicated anti-pattern row and Hard Gate #20 (not -A80 spillover into Recovery)
grep -nE '^\| Edit plan Markdown without a fresh skill-gate marker \|' agents/skills/execute-plan/SKILL.md \
  || { echo "missing anti-pattern row"; exit 1; }
grep -nE '^20\. \*\*Skill-gate marker before plan-file edits\*\*' agents/skills/execute-plan/SKILL.md \
  || { echo "missing Hard Gate #20"; exit 1; }

# No bypass language (if-form: ! grep under set -e still exits 0)
if grep -nEi 'orchestrator is exempt|bypass skill-gate|skip.*skill-gate' agents/skills/execute-plan/SKILL.md; then
  echo "bypass language found"; exit 1
fi

# Recovery: marker before mark before Launch done (tight window; abort on miss/reorder)
recovery=$(grep -nE '## Recovery: retroactive execute-plan compliance' -A12 agents/skills/execute-plan/SKILL.md)
done_ln=$(echo "$recovery" | grep -n 'Launch \*\*done\*\*' | head -1 | cut -d: -f1)
mark_ln=$(echo "$recovery" | grep -nEi 'mark.*checkbox|checkbox.*\[x\]' | head -1 | cut -d: -f1)
marker_ln=$(echo "$recovery" | grep -nEi 'WRITE RECIPE|Plan-file edits|skill-gate' | head -1 | cut -d: -f1)
if ! { test -n "$done_ln" && test -n "$mark_ln" && test -n "$marker_ln" \
  && test "$marker_ln" -lt "$mark_ln" && test "$mark_ln" -lt "$done_ln"; }; then
  echo "Recovery order: need marker < mark < Launch done inside Recovery window"; exit 1
fi
if grep -nE 'Launch \*\*done\*\*.*mark .*checkboxes|Launch done.*mark .*checkboxes' agents/skills/execute-plan/SKILL.md; then
  echo "Recovery still has done-then-mark phrasing"; exit 1
fi

# Recipe points at README single source (not inlined window/hash constants)
grep -nF 'skill-gate/README.md' agents/skills/execute-plan/SKILL.md \
  || { echo "missing skill-gate README reference"; exit 1; }
grep -nE 'WRITE RECIPE|write-marker|session_channel|Plan-file edits' agents/skills/execute-plan/SKILL.md \
  || { echo "missing WRITE RECIPE / Plan-file edits tokens"; exit 1; }

# Shared Plan-file edits: polarity (refresh + FAIL-LOUD stop; not token leftovers)
grep -nE '### Plan-file edits \(skill-gate\)' -A6 agents/skills/execute-plan/SKILL.md \
  | grep -nEi 'refresh the plans-class skill-gate marker' >/dev/null \
  || { echo "shared Plan-file edits must require marker refresh"; exit 1; }
grep -nE '### Plan-file edits \(skill-gate\)' -A6 agents/skills/execute-plan/SKILL.md \
  | grep -nEi 'FAIL-LOUD|fail-loud' >/dev/null \
  || { echo "shared Plan-file edits must be FAIL-LOUD"; exit 1; }
grep -nE '### Plan-file edits \(skill-gate\)' -A6 agents/skills/execute-plan/SKILL.md \
  | grep -nEi 'stop and report|do not edit the plan' >/dev/null \
  || { echo "shared Plan-file edits must stop when unwritable"; exit 1; }
if grep -nE '### Plan-file edits \(skill-gate\)' -A6 agents/skills/execute-plan/SKILL.md \
  | grep -nEi 'continue editing|without refreshing|skip.*marker'; then
  echo "shared Plan-file edits polarity inverted"; exit 1
fi

# Structural: Step 1.3 + Recovery presence (order for Step 1.3 locked above)
for anchor in '### Step 1\.3: Mark plan progress' '## Recovery: retroactive execute-plan compliance'; do
  grep -nE "$anchor" -A45 agents/skills/execute-plan/SKILL.md | grep -nEi 'skill-gate|write-marker|WRITE RECIPE|marker|Plan-file edits' >/dev/null \
    || { echo "missing marker language near: $anchor"; exit 1; }
done

# Step 0.4b: tight window so shared Plan-file edits section cannot false-green
grep -nE '### Step 0\.4b:' -A12 agents/skills/execute-plan/SKILL.md \
  | grep -nEi 'immediately before that plan-file write|Plan-file edits' >/dev/null \
  || { echo "missing Step 0.4b per-write marker language"; exit 1; }

# No duplicated window constant in execute-plan skill
if grep -nE 'SKILL_GATE_WINDOW|14400' agents/skills/execute-plan/SKILL.md; then
  echo "inlined SKILL_GATE_WINDOW / 14400 in execute-plan skill"; exit 1
fi

bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

## Tasks

### Task 1: Wire marker WRITE RECIPE into execute-plan plan-file edits

Files:
- `agents/skills/execute-plan/SKILL.md`

- [x] In **Step 1.3: Mark plan progress**, require refreshing the plans-class skill-gate marker per `ai-playbook/agents/hooks/skill-gate/README.md` Marker WRITE RECIPE **before** any plan-file write (same obligation as `plans`; recipe details stay in the README). Marker write is fail-loud: if unwritable, stop and report; do not edit the plan.
- [x] In **Recovery: retroactive execute-plan compliance**, reorder each task loop to match Phase 1: (1) verify scope, (2) write/append implement log, (3) refresh marker (WRITE RECIPE, fail-loud), (4) mark **only that task's** checkboxes `[x]`, (5) launch **done**. Do **not** launch `done` before checkbox marking. Remove or rewrite the current "Launch done ...; mark ... checkboxes" combined step so marker-protected plan edits land in that task's commit.
- [x] Apply the same pre-write marker requirement to any other execute-plan step that edits plan Markdown via Write/StrReplace (call each out explicitly after inventorying the skill). Phase 4 `git mv` alone is not a Write/StrReplace; only add marker language there if the step also edits plan file contents through those tools.
- [x] Add an **anti-patterns** row and/or **Hard Gates** entry: do not edit plan files from execute-plan without a fresh marker; do not bypass or weaken skill-gate; do not `done`-then-mark in Recovery.
- [x] Reference the README as the single source; do not inline `SKILL_GATE_WINDOW`, hash derivation, or marker filename templates beyond pointing at the recipe.
- [x] Run → expect: Validation Commands succeed (including Recovery-scoped greps and per-path structural checks).
- [x] Commit: `execute-plan: refresh skill-gate marker before plan-file edits`
