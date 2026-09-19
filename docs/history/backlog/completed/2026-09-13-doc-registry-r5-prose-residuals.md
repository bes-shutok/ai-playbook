# Backlog: doc-registry validator r5 prose residuals

Status: done
Origin: review round r5 of the 2026-09-13 doc-registry validator residuals close-out (branch 2026-09-13-doc-registry-validator-residuals, HEAD d084490; staging doc `docs/reviews/2026-09-13-doc-registry-validator-residuals-code-review-r5.md`). Valid non-blocking findings deferred at the five-round cap per the backlog-deferral default; fixing them would have mutated the reviewed digest and required a sixth round.

## Items

1. **doc-hierarchy exemption sentence scoping** (r5 F1, Medium non-blocking; echoed by contract-docs): `agents/skills/doc-hierarchy/SKILL.md` ~line 124 says "except for three bounded warn tiers", which reads as exhaustive, but the validator has six warn families for un-overridden writes; the three pre-existing ones (untracked byte-equal registered src stage-the-move; bare-line no-letter verify; case-variant add near-match verify) are unlisted. Fix: scope to "three further bounded warn tiers" (matching the validator module docstring) and optionally list the legacy warn paths. Evidence: r5 live probe matrix; validator module docstring lines ~60-70.

2. **Duplicated word in validator selftest comment** (r5 F2, Low): `scripts/doc_registry_validator.py` ~1751-1752, "(argparse / argparse independently rejects...)". Delete one.

3. **Plan prose duty wording** (r5 F3, Low): plan `2026-09-13-doc-registry-validator-residuals.md` lines ~81 and ~131 say the three mandated tiers each carry "an explicit verify duty"; two of the three duties are "stage the move". The plan archived as history, so if it is ever superseded by a successor record, carry the correction "each carries an explicit duty (stage the move, or verify)". No living-doc edit required.

## Classification

Prose-precision / sibling-doc restatement family. No code behavior implicated; the runtime gate is correct, fail-closed, and fully pinned (r5 testing lens live-verified the full conjunct kill map).
