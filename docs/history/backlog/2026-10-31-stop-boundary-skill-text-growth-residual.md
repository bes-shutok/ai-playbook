# Stop-boundary skill-text growth residual

Driving force: simplicity

Source: plan 2026-10-27-maintenance-stop-boundary-continuation Phase 3 r6 review (record .ai-playbook/reviews/2026-10-31-plan-review-maintenance-stop-boundary-continuation-p54cc877b-r6.md).

The D-6 alignment added ~1.3 KB net operative bytes across four maintenance skill files (template-authoring +512, template-execution +256, template-unblock +256, zcode.md +277; decisions.md net negative). The old unconditional-stop text was deleted in the same change, but the replacement D-6 wording is longer. A later Codex continuation review also found operative growth in `agents/skills/maintenance/codex.md` without an equivalent deletion (code-review r2 finding F2). No byte-budget gate has landed, so both remain instances of the review-time finding class. Include the Codex adapter in the deferred trim when the repo-wide byte-budget gate lands.
