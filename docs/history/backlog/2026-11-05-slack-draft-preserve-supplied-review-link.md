# Backlog: preserve the user's supplied review-stack URL in Slack drafts

Status: open
Priority: high
Class: fix-class
Origin class: skills-corpus defect (learn Step 1.8, 2026-11-05 session analysis)
Added: 2026-11-05

## Observed versus expected

The session received a review-stack URL directly from the user, then drafted the message with separate pull-request URLs instead. The user had to correct the draft and restate that the supplied stack URL was the intended link. The Slack skill says to preserve user-provided link labels, but it does not explicitly make a supplied destination URL authoritative when the assistant can infer component links.

Expected: when a user supplies the URL for a requested link, preserve that destination and use it in the draft. Do not substitute inferred component links unless the user asks for them or the supplied link is verified unusable and the difference is explained before saving.

## Reproduction evidence (trimmed)

- In an interactive Slack-draft session, the user supplied a stack URL in the initial request.
- The first draft listed the component pull requests separately; the user corrected it to use the supplied stack URL.
- `agents/skills/slack-message/SKILL.md` says to preserve user-provided link labels but has no matching rule for preserving the supplied destination URL.

## Suspected root area

`agents/skills/slack-message/SKILL.md`, link-source selection in the message composition and final link scan. The draft workflow treated inferred repository links as replacements for an explicit user-provided destination.

## Fix shape

Add one concise, tool-agnostic rule to the existing hyperlink guidance: preserve user-provided destination URLs for the requested link; do not replace them with inferred links unless asked or the provided destination is verified unusable. Keep the existing syntax-specific wrapper rule. Do not add a URL-validation gate or another link inventory.

## Ship when

The Slack skill explicitly preserves a user-supplied destination URL, and a realistic draft exercise using a supplied stack URL retains that URL even when individual pull-request links are also discoverable.
