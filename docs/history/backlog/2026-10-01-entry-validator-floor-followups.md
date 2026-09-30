- **Filed:** 2026-10-01
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** self-serving (execute-plan Step 1.2b intermediate review backlogged candidates, marker-floor-tightening run)
- **Class:** fix-class
- **Driving force:** documentation precision; fail-safe consistency

# Entry-validator floor follow-ups: skill drift note, cwd guard, multi-line dispositions, tail-strip edge

## Problem

Four low-severity follow-ups from the marker-floor tightening:

1. **Skill drift:** `agents/skills/investigate/SKILL.md:53` describes the floor as path/hex/witness-token markers without the new file-precision semantics; the validator's docstring owns the list by design, but the skill's description now silently under-describes it (the plan acknowledged the drift; nothing points a future editor at it).
2. **cwd guard:** `_span_names_file_evidence`'s `isfile` arm is cwd-relative with no guard; a subdirectory invocation silently drops the existence arm.
3. **Multi-line dispositions:** the per-line END anchor would reject a disposition whose citation lands mid-block in a multi-line style — latent, not pinned by any live line today.
4. **Tail-strip edge:** `CITATION_TAIL_CHARS` strips a legitimate trailing `)`/quote-like character from a real path — theoretical corruption of exotic filenames, accepted per plan assumption.

## Expected behavior

One small pass: add a pointer sentence to investigate SKILL.md (or accept and record the drift in the validator docstring), guard or document the cwd dependence, state the single-line disposition constraint in the docstring, and note the tail-strip edge beside `CITATION_TAIL_CHARS`.

## Location

- `agents/skills/investigate/SKILL.md:53`
- `scripts/check_investigate_entries.py` (the predicate, the docstring, `CITATION_TAIL_CHARS`)
