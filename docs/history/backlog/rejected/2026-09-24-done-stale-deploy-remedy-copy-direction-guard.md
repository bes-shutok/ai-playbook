# Backlog: done stale-deployment cp remedy lacks copy-direction guard wording

- Priority: low
- Status: rejected (2026-09-27; hypothetical operator misreading; wording-only guard, no witnessed wrong-direction copy)
- Workflow: backlog
- Scope: `agents/skills/done/SKILL.md` (doc-registry gate bullet, Stale-deployment signature remedy)
- Owner: playbook maintenance
- Source: code review r1 F3 for plan 2026-09-24-p55-audit-deployment-gaps-gate-blind-spots (Low, non-blocking)
- Driving force: code-quality + simplicity

Origin: docs/reviews/2026-09-24-2026-09-24-p55-audit-deployment-gaps-gate-blind-spots-code-review-r1.md, finding F3. The stale-deployment signature's remedy reads "redeploy with `cp scripts/doc_registry_validator.py ~/.ai-playbook/scripts/`", which states the copy as a bare command without wording that guards its direction. An operator (or a later amendment) can misread the remedy as copying from the runtime home back into the repo, which would overwrite the fixed repo copy with the stale deployed bytes and reverse the remedy.

Suggested fix: amend the remedy wording in the done SKILL.md doc-registry bullet to guard the copy direction explicitly (repo copy is the source, runtime home is the destination; never the reverse), keeping the existing command text intact.
