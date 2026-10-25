# Lesson 212 Rule still offers the cross-checkout `--manifest` alternative

Cluster: none
Status: open

## Driving force
The done-finalize-checkpoint-manifest-env-honoring execution review (r1, staging doc .ai-playbook/reviews/2026-10-26-done-finalize-checkpoint-manifest-env-honoring-code-review-r1.md, Low R1-F1) found lesson 212's Rule sentence still offering "or pass `--manifest <path>`" as an alternative remedy, while the newly landed Step 6 text in agents/skills/done/SKILL.md (commit c90abc18b) directs the owner-checkout rerun and states that finalize mutates only the invocation checkout. The script supports the SKILL text (`finalize --manifest` parses FINALIZE_MANIFEST but no arm reads it), so the lesson's alternative is dead guidance that re-bites on every owner-checkout recovery read.

## Suggested remedy
One-line amendment to lesson 212's Rule dropping the `--manifest` alternative (or marking it dead), keeping the owner-checkout rerun as the sole remedy. Same review also noted two non-blocking residuals worth folding into the same edit: the pre-existing Step 0 Run-placement sentence lists `{tmp_dir}/done-session/` among primary-resolving corpus surfaces in tension with the new worktree-owner parenthetical (R1-F2), and the added Step 6 paragraph uses the literal `docs/tmp/done-session/` where the skill elsewhere uses the facts-resolved `{tmp_dir}` convention (R1-F4, cosmetic).
