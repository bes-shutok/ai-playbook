# Done-lock one-shot holder reclaim semantics are undocumented in the done skill

Captured: 2026-09-28 (source: release-skill-follow-ups done closeout, lock release)
Status: open
Priority: low
Workflow: backlog
Class: documentation
Driving force: reliability
Origin class: self-serving
Consumer urgency: Operators who see a token-mismatch release refusal need to distinguish a hijack from documented reclaim behavior in the moment; today the reasoning lives only in session memory, not in the skill.

## Problem

A one-shot shell holder of the done lock goes dead after its acquiring call finishes. A live peer run can then reclaim the abandoned hold after the grace period. When the original run later attempts its token-fenced release, the release is refused with a token mismatch. During the release-skill-follow-ups closeout, exactly this sequence occurred (`done-ai-playbook-resume` reclaimed the abandoned one-shot hold before the closeout's release attempt). The refusal was correct behavior, but the operator had to re-derive why from scratch; the done skill does not document the one-shot-reclaim lifecycle or that a token-mismatch release refusal is the expected witness of a reclaimed hold, with nothing left to release and no further action required.

## Exact location

`agents/skills/done/SKILL.md`, done-lock usage section (Variant B / one-shot holder lifecycle and the release step's token-fence).

## Expected

- The skill documents the one-shot holder lifecycle: acquire, holder process exit, grace period, peer reclaim.
- The release step text states that a token-mismatch refusal after a peer reclaim is correct behavior, that the correct response is to record the witness and proceed (never bypass or re-acquire), so the operator does not re-derive the adjudication.

## Severity and source reference

Severity: low

Source: release-skill-follow-ups done closeout lock release, 2026-09-28; capture hygiene: scan-public-hygiene --files pass.

## Why not fixed now

The closeout completed without touching skill text. Recorded as a documentation fix for the done skill's lock section.

## Dedup probe

Search terms: `done-lock`, `one-shot holder`, `token mismatch release`, `reclaim`. No open item documents the reclaim lifecycle; the done-manifest and owned-commit items cover other finalize defects.

## Suggested fix

Add a short "One-shot holders and peer reclaim" paragraph to the done skill's lock section describing the lifecycle, the expected token-mismatch refusal witness, and the correct no-action response.
