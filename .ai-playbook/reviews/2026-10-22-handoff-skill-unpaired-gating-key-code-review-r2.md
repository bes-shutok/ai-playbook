# Code Review: Branch adhoc/2026-10-22-handoff-gating-key → main (ad-hoc landing, handoff-skill-unpaired-gating-key)

## Metadata
- Type: Branch Review (ad-hoc backlog arm landing review)
- Record kind: canonical
- Review mode: fresh-adversarial
- Date: 2026-10-22
- Branch: adhoc/2026-10-22-handoff-gating-key → main
- Findings: r1 one blocking (prune owed at landing), r2 two blocking (botched fold: duplicated receipt block, entry not removed), r3 clean after repair
- Status: POSTED
- Base resolved non-interactively: main (repo default; ad-hoc exec run)
- Changed-risk signals: none (skill frontmatter line + fork notice, one guidelines sentence, origin-row deletion, EXEC-PROMPTS entry prune with receipt)
- Panel mechanism note: one fresh-adversarial general-purpose review worker (r1 full delta; r2 focused fold delta caught the coordinator's corrupted fold; r3 pending on repaired head ad2fc9567)
- Last fix commit: ad2fc9567 (EXEC-PROMPTS.md rebuilt from main base with exactly the receipt insertion and the entry-block removal after the fold corruption)
- Source digest: b12e493aa60844fed04573b75730e0af6c9fc20eaf2039c13cbf8b74732bbfab (sha256 over `git diff main...HEAD` at final head ad2fc9567)

## Delta
- agents/skills/handoff/SKILL.md: top-level when_to_use frontmatter line (i-have-adhd shape, /handoff) + Local fork notice naming the divergence and the recovery source; description and all other frontmatter keys byte-unchanged.
- AGENTS.md Vendored Asset Sync Rules fork paragraph: one sentence naming the handoff fork, mirroring the i-have-adhd sentence.
- Origin row docs/history/backlog/2026-10-22-handoff-skill-unpaired-gating-key.md deleted per the covered-row rule.
- EXEC-PROMPTS.md: handoff-skill-unpaired-gating-key entry pruned with the EXEC-PROMPTS-PRUNE receipt ("landing in this commit" form, matching the 14-receipt precedent).

## Verification
when_to_use byte-identical to the i-have-adhd shape after the name swap; YAML frontmatter parses with all keys; fork notice byte-identical to the model after the name swap, no over-claim (upstream carries disable-model-invocation: true); AGENTS.md pure one-sentence append; census: handoff was the last vendored skill carrying the key unpaired, both carriers now paired; how-to-write-skills pairing requirement satisfied; deleted row cited by nothing outside the pruned entry; gates on final head: em-dash 0, hygiene PASS, pins 0, check_skill_description_length 0 (pre-existing unrelated warning), check_investigate_entries 1 entry 0 violations. Known accepted state: check_prompt_log_origins --prune-audit over a window covering the landing flags the "landing in this commit" receipt family as REMOVED-WITHOUT-WITNESS (0 by log ledger); today's peer precedent landings (check-landed-sweep ac335fad5 et al.) share the identical signature, so the receipt form matches the operative precedent and the flag is an audit-window artifact, not a delta defect.

## Verdict
ready=yes, zero blocking findings (final round on ad2fc9567).
