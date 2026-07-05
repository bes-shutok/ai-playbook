---
name: slack-message
description: Use this skill whenever the user wants to send, post, draft, or update a Slack message. Triggers on phrases like "post to Slack", "send to channel", "put this in Slack", "message the team", "update the Slack post", or any time the user provides message content and a Slack channel or URL. Always draft first, show a formatted preview, then save to Slack Drafts only. Never post immediately; the user sends from the Slack client so the message stays user-attributed.
---

# Slack Message Skill

**Writing:** Follow `agent_workflow_guidelines.md` §39 (no em dashes) and §45 (plain English, globish-friendly). Scan every draft for the U+2014 em dash character before preview or draft-save.

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
- Preserve explicit section-specific bullet style from the user, even when it differs from the default template. For example, if the user writes `*Blockers*` with `- None`, keep `- None` rather than normalizing it to `• None`.
- Code identifiers, class names, method names, field names, config keys: wrap in backticks
- Do not label widely-used, active tools or systems as "legacy" unless the user explicitly does so
- `@here`, `@channel`, and user `@mentions` pass through as-is.
- For recurring colleagues, preserve the `@` tag and use the full name plus local Slack signature only when local facts/instructions provide it. For manual copy-paste drafts, prefer that local tag form over raw Slack user IDs such as `<@U...>`; use raw Slack IDs only when saving/sending through a Slack integration that requires them, or when the user explicitly asks for real Slack mention syntax. Do not hardcode real people in this generic skill.
- In manual copy-paste drafts, do not wrap confirmed teammate `@mentions` in Markdown links. Keep them as raw Slack-visible text such as `@Full Name [TEAM]`; links can prevent the copy-pasted text from behaving like a clean mention.

## Wording rules

Apply to every draft. Scan the final text before showing the preview.

- **No em-dashes.** Never use the U+2014 em dash character. Use a comma, semicolon, colon, period, or parentheses instead. Wrong shape: `same as profile-updates [em dash] implemented`. Right: `same as profile-updates; implemented and tested.` or `same as profile-updates (implemented and tested).`
- **Plain globish.** Short words, full sentences, readable for non-native speakers. No telegraphic shorthand.
- **HTTP status codes.** Do not use a bare number (`409`) when Product or cross-team readers need to understand the outcome. Write the standard name with the code: `409 Conflict`, `404 Not Found`, `200 OK`. First mention may be `HTTP 409 Conflict`; later mentions can shorten to `409 Conflict` if context is clear.
- **API response vs caller behavior.** When describing consent/messaging checks, separate what the API returns from what callers should do. Say the endpoint returns HTTP `200 OK` with `decision: "DENY"` and `reason: …`; then say callers should not deliver when `decision` is `DENY`. Do not write vague shorthand like "do not send (`DENY`)" without stating it is the JSON response field.
- **Internal engineering refs.** Product-facing Slack posts should not cite ADR numbers, plan filenames, or ticket-only context unless the audience uses them. Use endpoint names, user-visible behavior, and plain outcome language. Jira keys (e.g. `PROJ-1234`) are fine when the thread is already task-scoped.
- **Validation evidence stays private by default.** Use repository checks, source links, and detailed evidence to validate the answer for the user, but do not paste long evidence sections into Slack unless the user explicitly asks for them. For cross-team technical replies, lead with the conclusion and only the shortest operationally useful bullets.
- **Source-backed decision replies.** Use Slack markdown inline links (`[label](url)`) at the claim they support. When compressing analysis, keep the strongest concrete tradeoffs and risk bullets in shorter form instead of smoothing them into generic narrative.
- **Audience vocabulary.** Remove specialty jargon the author does not normally use, but keep common developer terms such as CRUD when writing to engineers. Do not replace precise familiar terms with vaguer wording or explain basic developer vocabulary to peer developers.
- **Tentative architecture/source choices.** When a thread is still a spike or option analysis, do not turn candidate paths into final statements. Distinguish current research access from later production access, first baseline import from repeatable backfill or enrichment, and the default sync option from possible alternate workflows. If the source only supports "likely", "at this stage", or "one option", keep that uncertainty in the draft.
- **Standup blockers stay explicit.** Do not replace a blocker with `None` just because there was partial progress or a new reply. Keep blocker status when the underlying decision, approval, alignment, or dependency is still unresolved; downgrade to `None` only when the user explicitly says there are no blockers or the source text clearly resolves the dependency.
- **Minimal context.** Product or cross-team decision posts should open with the gap and the ask. Do not recap unrelated shipped work (e.g. a prior ticket's empty-state fix) unless it is required to understand the question.
- **Symmetrical questions.** When a post has multiple product choices, give each question the same shape: short scenario, API or payload example when it helps, then labeled options `*A)*` / `*B)*` / `*C)*` with tradeoffs in one line each.

## BI / data-team asks (cross-team)

When the author investigated BI tables or schemas and asks BI/PJM for help:

- **First person when the author did the work.** Use *I searched*, *I found*, *I could not find*; not *we audited* unless a team did it together.
- **Avoid data-warehouse jargon** unless the reader uses it daily. Replace terms like *mart*, *baseline mart*, *cutover*, *delta*, *export shape* with plain words: *BI table*, *which table to use*, *last updated column*, *separate datasets*.
- **Ask about source tables, columns, and reliability** (completeness, v1 vs v2, which row is canonical, whether `update_time` is maintained). Do **not** ask how BI should deliver files (CSV, S3, file count); export transport is the requester's problem unless BI owns delivery by policy.
- **Missing fields:** give 3–4 examples with a one-line plain description of what the field means; link to a Confluence or doc section for the full list. Do not paste long tables in Slack.
- **Search scope in P.S.:** list which DBs/clusters were checked and ask the reader to point to other stores (e.g. Redshift) if data might live elsewhere.
- **Team signature tags** (e.g. `[EU-CRM-BE]`): add only when local facts or the user confirm the tag. Do not copy signatures from other people's messages.

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
