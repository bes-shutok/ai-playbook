# Backlog: extended prune audit cannot witness an ad-hoc EXEC-PROMPTS prune whose removal rides the landing

- **Filed:** 2026-10-23, exec carrier automation-8cff854e (operator mandate: exec EXEC-PROMPTS max 2)
- **Status:** open
- **Workflow:** backlog
- **Priority:** normal
- **Origin class:** witnessed twice in one run (landings 1b742efd2 and c10f655ca)
- **Class:** fix-class (audit witness recognition; no landing-gate change implied)
- **Driving force:** reliability
- **Skill/step:** `scripts/check_prompt_log_origins.py` (`--prune-audit`); `docs/history/backlog/EXEC-PROMPTS.md` Prune rule delta
- **Cluster:** docs/history/backlog/EXEC-PROMPTS.md (the log whose receipt grammar the audit reads)

## Problem

The extended prune audit classifies an EXEC-PROMPTS entry removal by three evidence classes: a plans-root file witness in the same commit, the removal commit's own message carrying the strict `EXEC-PROMPTS-PRUNE: <slug> -> <token>` line (token must resolve as a commit), or the log's post-image ledger line with a resolving commit-or-path token. An ad-hoc prune whose receipt reads `-> landing in this commit` can satisfy none of the three: the token "landing" resolves to neither a commit nor a path, and the removal's own commit can never cite its own not-yet-existing landing sha. Pre-landing the audit sees no removal (riders uncommitted or the removal riding the not-yet-created squash), post-landing the removal commit is immutable, so the flag is unrepairable without rewriting landed main.

Witnessed: audits over `906d3460f^..HEAD` and the two 2026-10-23 landings above each print `REMOVED-WITHOUT-WITNESS` for exactly these ad-hoc prunes while every other removal class passes; the repair commits `87717839f`/`65088647a` (receipt in message citing a full landing sha) are the recognized shape but only work when the removal commit itself carries them.

## Outcome sought

One of: the audit's ledger class accepting a self-referential landing witness for ad-hoc receipts (recognizing `landing in this commit` when the removal commit also carries the ad-hoc landing's content), or the EXEC-PROMPTS Prune rule delta prescribing a receipt grammar the audit can resolve at landing time (for example staging the removal so the audit's pre-landing range includes a witnessing rider), with the standing corpus flags dispositioned either way. Machinery admission applies: name the incident (this row), expected catch frequency, and false-positive cost before any gate change.

## Rejected alternatives

- Rewrite the landed commits to embed resolving shas: forbidden, landed main is immutable.
- Leave the flags standing unrecorded: rejected, the corpus already carries unresolved flags from 906d3460f and 243c26d68 and each new ad-hoc prune adds one.
