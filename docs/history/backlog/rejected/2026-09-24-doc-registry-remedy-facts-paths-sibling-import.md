# Backlog: doc-registry stale-deployment remedy omits facts_paths.py sibling import

- Priority: low
- Status: rejected (2026-09-27; hypothetical stale-deployment scenario; remedy-wording polish)
- Workflow: backlog
- Scope: `agents/skills/done/SKILL.md` (doc-registry gate bullet, Stale-deployment signature remedy)
- Owner: playbook maintenance
- Source: code review r1 F4 for plan 2026-09-24-p55-audit-deployment-gaps-gate-blind-spots (Low, non-blocking)
- Driving force: code-quality + simplicity

Origin: docs/reviews/2026-09-24-2026-09-24-p55-audit-deployment-gaps-gate-blind-spots-code-review-r1.md, finding F4. The stale-deployment remedy redeploys only `scripts/doc_registry_validator.py`, but the validator imports the sibling `facts_paths.py` module when available (`_import_facts_paths`, never fatal): a deployed runtime home missing or carrying a stale `facts_paths.py` silently degrades facts resolution to the warn path ("facts_paths module not importable next to the validator") instead of the TOML-backed resolution.

Suggested fix: extend the stale-deployment remedy wording (not the signature trigger) to note the sibling-import dependency and refresh the sibling alongside the validator (`cp scripts/facts_paths.py ~/.ai-playbook/scripts/`), or explicitly document why the sibling stays outside the redeploy.
