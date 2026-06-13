---
name: slack-message
description: Use this skill whenever the user wants to send, post, draft, or update a Slack message. Triggers on phrases like "post to Slack", "send to channel", "put this in Slack", "message the team", "update the Slack post", or any time the user provides message content and a Slack channel or URL. Always draft first, show a formatted preview, then save to Slack Drafts only. Never post immediately; the user sends from the Slack client so the message stays user-attributed.
---

# Slack Message Skill

**Writing:** Follow `agent_workflow_guidelines.md` §45 (plain English, globish-friendly).

## Core workflow

1. **Draft first, always.** Format the message and show it in a fenced block for review.
2. Format the message per the rules below.
3. Show the preview and ask: "Does this look good, or any changes?"
4. After approval, save to **Slack Drafts** using your environment's **draft-save** Slack integration only. Tell the user to open Slack → **Drafts & Sent** and click **Send** themselves.

**Never use immediate/direct send.** Some integrations add an agent attribution footer on direct send. Draft-only keeps the post attributed to the user when they send from Slack.

## Showing the draft (required)

**Always** return the full draft inside **one** outer fenced code block so the user can copy it intact. Short prose before/after the fence is fine (channel name, “does this look good?”); the **complete postable text** must live inside the fence.

Format:

````
**Draft for #channel-name:**

```
[entire Slack message, start to finish]
```

Does this look good, or any changes?
````

### Preview fence rules

- **One fence only.** The preview uses a single opening ` ``` ` and a single closing ` ``` ` after the last line of the draft. The fence must not end early because of nested code blocks inside the message.
- **No nested triple-backtick fences inside the preview.** If the Slack message includes HTTP or JSON examples, use plain lines inside the outer fence (as Slack will receive them), not inner ` ``` ` blocks. Example:

  ```
  GET /v1/consents/p_abc…
  Response:
  HTTP 200 OK
  {
    "consents": []
  }
  ```

  Wrong: wrapping that JSON in ` ```json ` inside the preview fence (closes the outer fence early and truncates the draft).

- **Inline backticks are fine** inside the preview fence for endpoints, field names, and status text (e.g. `PATCH /v1/consent-updates`, `decision: "DENY"`).

- The **posted Slack message** is plain text with Slack markdown; only the **chat preview** uses the outer code fence for copy-paste.

## Formatting rules (inside the Slack message)

- Use Slack markdown: `*bold*`, `_italic_`, `` `inline code` ``. Fenced code blocks in the actual Slack post are optional; prefer plain indented lines for short HTTP/JSON samples so Product readers are not fighting nested formatting.
- Follow any local or task-specific Slack template over the generic rules here. For example, daily standups use `*Previous working day / Completed*`, `*Today*`, `*Blockers*`, and `•` bullets.
- Use `•` for standup/report bullets and any other message where the local instructions or source material use `•`. Use `-` only for generic ad-hoc Slack lists with no local template.
- Code identifiers, class names, method names, field names, config keys: wrap in backticks
- Do not label widely-used, active tools or systems as "legacy" unless the user explicitly does so
- `@here`, `@channel`, and user `@mentions` pass through as-is.
- For recurring colleagues, preserve the `@` tag and use the full name plus local Slack signature only when local facts/instructions provide it. Do not hardcode real people in this generic skill.

## Wording rules

Apply to every draft. Scan the final text before showing the preview.

- **No em-dashes.** Never use the `—` character. Use a comma, semicolon, colon, period, or parentheses instead. Wrong: `same as profile-updates — implemented`. Right: `same as profile-updates; implemented and tested.` or `same as profile-updates (implemented and tested).`
- **Plain globish.** Short words, full sentences, readable for non-native speakers. No telegraphic shorthand.
- **HTTP status codes.** Do not use a bare number (`409`) when Product or cross-team readers need to understand the outcome. Write the standard name with the code: `409 Conflict`, `404 Not Found`, `200 OK`. First mention may be `HTTP 409 Conflict`; later mentions can shorten to `409 Conflict` if context is clear.
- **API response vs caller behavior.** When describing consent/messaging checks, separate what the API returns from what callers should do. Say the endpoint returns HTTP `200 OK` with `decision: "DENY"` and `reason: …`; then say callers should not deliver when `decision` is `DENY`. Do not write vague shorthand like "do not send (`DENY`)" without stating it is the JSON response field.
- **Internal engineering refs.** Product-facing Slack posts should not cite ADR numbers, plan filenames, or ticket-only context unless the audience uses them. Use endpoint names, user-visible behavior, and plain outcome language. Jira keys (e.g. `PROJ-1234`) are fine when the thread is already task-scoped.
- **Minimal context.** Product or cross-team decision posts should open with the gap and the ask. Do not recap unrelated shipped work (e.g. a prior ticket's empty-state fix) unless it is required to understand the question.
- **Symmetrical questions.** When a post has multiple product choices, give each question the same shape: short scenario, API or payload example when it helps, then labeled options `*A)*` / `*B)*` / `*C)*` with tradeoffs in one line each.

## Editing existing messages

Slack's API does not support editing sent messages. When the user asks to edit or update a previous post, say so clearly and ask how they want to handle it. Options: post a new corrected message (user deletes the original manually), or reply in-thread.

## Finding channel IDs

Extract the ID directly from a Slack URL: `https://.../archives/C0123456789` means the channel ID is `C0123456789`. If only a channel name is given, search for the channel using your Slack integration.

## Saving the draft (required delivery method)

Use the **draft-save** Slack integration with the channel ID and approved message text. Return any draft or channel link the integration provides so the user can open Slack and send.

- For thread replies, pass the parent message timestamp when the integration supports it.
- If a draft already exists for that channel, tell the user to edit or delete it in Slack first, then retry.
- **Immediate/direct send is forbidden** in this skill, even when the user says "post", "send", or "notify". Those words mean save a draft and instruct the user to send from Slack.

After saving, remind the user: *Open Slack → Drafts & Sent → review → Send.*
