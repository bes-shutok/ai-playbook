# Backlog: review-plan skill does not state the cap-closure seal anchor composition

- **Filed:** 2026-11-03, authoring-run closeout capture (learn Step 1.8, skills-corpus)
- **Status:** open
- **Priority:** high
- **Origin class:** session-witnessed producer rediscovery (the accepted seal shape was derived from validator refusals, not from the skill text)
- **Cluster:** docs/history/backlog/2026-11-03-review-plan-seal-example-short-anchor.md (same surface and defect class: the seal duty text versus the validator seal contract)
- **Workflow:** backlog
- **Class:** fix-class (documentation composition: the seal paragraph plus the rule-8 re-bind clause name the two halves but never their intersection)
- **Skill and step:** `agents/skills/review-plan/SKILL.md`, the "Round-close seal (plan family)" paragraph and Iteration Discipline rule 8 (cap-closure procedure)

## Observed vs expected

Observed: a certification run closing through the cap-closure terminal shape drafted the certified round's seal entry from the round's pre-fold review state (round_start_commit resolving the bytes the round reviewed, digest matching the record's pre-bind `source_digest`). With that entry resolvable, the staging validator's corrections anchor leg graded the sidecar's re-bound `source_digest` against the seal's `round_start_digest` and refused the sanctioned re-bind as a bare rewrite ("the declared digest matches neither the round-start digest nor a verifying chain"). Without any entry the same shape degrades to the exact-match rule with a named warning, which the seal duty calls a round-close defect. The accepted composition - the seal entry for the certified round anchors at the checkpoint carrying the certified bytes, per the authoring-checkpoint duty's fresh-anchor-after-every-plan-edit rule, with round_start_commit and round_close_commit resolving the blob whose bytes hash to the re-bound digest - had to be derived from the refusal and confirmed by re-running both gates.

Expected: the skill text states the composition once, where the re-bind clause and the seal paragraph meet, so a producer drafts the conforming seal on the first pass.

## Reproduction evidence (trimmed)

1. Write the cap-closure terminal shape: plan residual section, triage marks on both record surfaces, sidecar `source_digest` re-bound to the post-section digest, `extensions.cap_closure` with `pre_fold_digest` set to the reviewed pre-fold digest.
2. Draft the seal entry with round_start anchored at the pre-fold fold commit (digest = the reviewed bytes).
3. Run the staging validator hard mode with `--source-plan`: anchor-leg refusal, bare rewrite.
4. Re-anchor the entry at the cap-closure checkpoint (blob hash equals the re-bound digest) and re-run: staging validator and readiness full gate both pass; the post-squash diagnostic's not-an-ancestor anchor checks hold under the squash-orphaned anchors.

## Environment

- Playbook skills repo, 2026-11-03; repo-local validator and deployed copy agree on the refusal (the anchor leg is pair-coupled, compatibility version 3).
- The lesson corpus carries the generalized mechanic (development_lessons.md #383); this item tracks the skill-text fix, not the lesson.

## Suspected root area

The seal paragraph documents the grammar and the re-bind clause documents the sidecar edit; neither states which state the certified round's seal anchors once the re-bind exists, and rule 8's retained mechanics do not mention the seal at all.
