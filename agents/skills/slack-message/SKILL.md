---
name: slack-message
description: Use this skill whenever the user wants to send, post, draft, or update a Slack message. Triggers on phrases like "post to Slack", "send to channel", "put this in Slack", "message the team", "update the Slack post", or any time the user provides message content and a Slack channel or URL. Always draft first, show a formatted preview, then save to Slack Drafts only. Never post immediately; the user sends from the Slack client so the message stays user-attributed.
---

# Slack Message Skill

**Writing:** Follow `agent_workflow_guidelines.md` §39 (no em dashes) and §45 (plain English, globish-friendly). Scan every draft for the U+2014 em dash character before preview or draft-save.

## Core workflow

1. **Draft first, always.** Format the message and show it in a fenced block for review.
2. Format the message per the rules below.
3. When the user provides a Slack channel, channel URL, or thread URL for a standup or other Slack-ready message, save the draft to Slack Drafts by default after preparing the final text. Always show the final text in a fenced block in the response too, even after the draft is saved, so the user has a copy.
4. If no Slack destination is provided, show the preview and ask: "Does this look good, or any changes?"
5. After approval, or immediately when a Slack destination was provided, save to **Slack Drafts** using your environment's **draft-save** Slack integration only. Tell the user to open Slack → **Drafts & Sent** and click **Send** themselves.

**Never use immediate/direct send, even when the user says "post", "send it", or "send the message".** Treat every send-like instruction as draft-only: save to Slack Drafts and let the user send from the Slack client. Do not call a direct-send tool at all; use the draft-save tool exclusively. Some integrations add an agent attribution footer on direct send, and direct send removes the user's final review. Draft-only keeps the post attributed to the user when they send from Slack. If the user explicitly wants it sent without review, still save a draft and tell them to click Send themselves.

## Showing the draft (required)

**Always** return the full draft inside **one** outer fenced code block so the user can copy it intact. Short prose before/after the fence is fine (channel name, “does this look good?”); the **complete postable text** must live inside the fence.

**Never** reply with only “draft saved” / draft id / Drafts & Sent instructions and omit the fenced body. After every draft-save (including revisions), show the full preview fence in the same chat turn. If you already saved and forgot the fence, show it immediately in the next reply.

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
- When updating an existing standup section from a partial user snippet, add the new bullet(s) to the existing section unless the user explicitly says to replace/remove the old content. Do not drop an existing `*Today*` item just because the user sends another `*Today*` item.
- Code identifiers, class names, method names, field names, config keys: wrap in backticks
- Do not label widely-used, active tools or systems as "legacy" unless the user explicitly does so
- Use visible `@team-name` and `@person-name` forms for all colleague and team addressing. `@here` and `@channel` pass through as-is. Never emit Slack API subteam markup, raw user IDs, or other machine-readable mention syntax in a draft, including when saving through a Slack integration. Do not hardcode real people in this generic skill.
- When addressing a team or group, resolve `team_references_project` from the current company's repo facts, falling back to user or ownership facts when the repo key is absent. Inspect only the relevant team artifact for the visible shortcut/address. Keep machine paths and concrete aliases out of this generic skill.
- For recurring colleagues, preserve the visible `@` tag and use the full name plus local Slack signature only when local facts/instructions provide it.
- In manual copy-paste drafts, do not wrap confirmed teammate `@mentions` in Markdown links. Keep them as raw Slack-visible text such as `@Full Name [TEAM]`; links can prevent the copy-pasted text from behaving like a clean mention.
- **Hyperlinks (draft-save, required).** When saving via the Slack draft-save tool, use standard Markdown link syntax: `[link label](https://example.com/path)`. Do **not** convert links to Slack mrkdwn `<https://example.com/path|link label>` unless the active Slack tool explicitly requires mrkdwn for drafts.
- **Hyperlinks (chat preview).** Show the same Markdown link syntax inside the preview fence so copy-paste and draft-save stay aligned. Wrong in draft body for the current Slack draft tool: `<https://example.com/users/usr_002|mockup UI>`. Right: `[mockup UI](https://example.com/users/usr_002)`.
- **Preserve user link labels.** When the user provides link text (for example `mockup UI`, `CRM MVP Data Points`), keep their label; only fix the wrapper syntax before draft-save.

## Wording rules

Apply to every draft. Scan the final text before showing the preview.

- **No em-dashes.** Never use the U+2014 em dash character. Use a comma, semicolon, colon, period, or parentheses instead. Wrong shape: `same as profile-updates [em dash] implemented`. Right: `same as profile-updates; implemented and tested.` or `same as profile-updates (implemented and tested).`
- **Plain globish.** Short words, full sentences, readable for non-native speakers. No telegraphic shorthand.
- **Translate internal terms.** In cross-team drafts, keep exact identifiers only when the recipient needs them and translate the surrounding implementation language into plain actions and outcomes. For example, say "create and enter the secret directly in AWS Secrets Manager" instead of "out-of-band value insertion", and say "the current version" unless the exact API label is required.
- **HTTP status codes.** Do not use a bare number (`409`) when Product or cross-team readers need to understand the outcome. Write the standard name with the code: `409 Conflict`, `404 Not Found`, `200 OK`. First mention may be `HTTP 409 Conflict`; later mentions can shorten to `409 Conflict` if context is clear.
- **API response vs caller behavior.** When describing consent/messaging checks, separate what the API returns from what callers should do. Say the endpoint returns HTTP `200 OK` with `decision: "DENY"` and `reason: …`; then say callers should not deliver when `decision` is `DENY`. Do not write vague shorthand like "do not send (`DENY`)" without stating it is the JSON response field.
- **Internal engineering refs.** Product-facing Slack posts should not cite ADR numbers, plan filenames, or ticket-only context unless the audience uses them. Use endpoint names, user-visible behavior, and plain outcome language. Jira keys (e.g. `PROJ-1234`) are fine when the thread is already task-scoped.
- **No doc-revision meta.** Do not put internal document version labels in Slack (for example `v0.3.2`, “wiki version 8”, “local Markdown synced”). Link the living page or repo path; readers care about the content, not the edit counter. Keep version tables in the doc itself.
- **Validation evidence stays private by default.** Use repository checks, source links, and detailed evidence to validate the answer for the user, but do not paste long evidence sections into Slack unless the user explicitly asks for them. For cross-team technical replies, lead with the conclusion and only the shortest operationally useful bullets.
- **Source-backed decision replies.** Use inline hyperlinks at the claim they support. In draft-save bodies use the hyperlink style required by the active Slack draft tool (see Hyperlinks above). When compressing analysis, keep the strongest concrete tradeoffs and risk bullets in shorter form instead of smoothing them into generic narrative.
- **Primary-source verification.** Before drafting or revising a decision reply, read the target thread and every linked primary source that could settle the asked clause, especially newer contract or decision pages added later in the thread. Do not infer that an item is still open from an older summary when a newer source may resolve it. If a source is outside the requested scope or has not been reviewed, do not introduce its details or critique it in the reply.
- **Metric semantics before incident classification.** Before using a metric status such as `DELIVERED` or `SUCCESS` to describe user impact or alert severity, trace the code that emits it and the provider contract. Distinguish a local attempt, provider hand-off, client receipt, and user impact. Do not weaken or replace a confirmed incident classification without that evidence.
- **Clause-focused revisions.** When the user narrows a reply to one clause, answer that clause directly. Remove internal drafting history such as "I need to correct my earlier wording" or references to superseded drafts, and remove unsupported technical side comments. Keep evidence links attached to the claims they support.
- **Operational-risk framing.** When a stakeholder raises a load or operational risk, distinguish a manageable implementation concern from a decision blocker. State concrete mitigations and acceptable rollout trade-offs only when supported by the user or a verified source, such as metric monitoring, throttling, pause/resume, or a slower initial rollout.
- **Role-sensitive decision replies.** Before drafting a message to a named stakeholder when their role affects the framing, read the available ownership facts and any supplied primary-thread comment. When replying to a Product stakeholder, present the system design as the consequence or enabling detail of their stated product choice. Do not ask them to validate implementation mechanics or frame the message as a peer architecture correction.
- **Audience vocabulary.** Remove specialty jargon the author does not normally use, but keep common developer terms such as CRUD when writing to engineers. Do not replace precise familiar terms with vaguer wording or explain basic developer vocabulary to peer developers.
- **Non-expert (Product/PM) replies: define the term, show examples, explain *why*.** When answering a non-engineer about an engineering constraint or limit, first define the key domain term in plain language with 2-5 concrete examples, then explain *why* the constraint exists (the trade-off), not only *what* it is. Compress the deep technical part to "simple, not simpler". Do not open with implementation internals (data structures, algorithms, caps) as if the reader already shares them.
- **Adjacent-team asks: frame in their domain, show don't explain, drop your internals.** When asking a peer on another team or service for data/contract changes, phrase each need as a concrete question in *their* domain (their API or payload shape), the same way you would ask your clearest question. Prefer *showing* an annotated example payload over explaining in prose. Do not dump your own service's internal concepts (materialization caps, operator/window mappings, bitmap mechanics) that the reader is not aware of and does not own; keep those on your side.
- **Catalog scope vs MVP enablement.** When a peer plans to expose "all" items from a mockup or UI tab as the MVP catalog, clarify that your service may only *enable* a curated subset for MVP (link the stakeholder thread that set the constraint) and give a short example list of what is in scope. Distinguish "define broadly in the catalog contract" from "segmentation/filtering enables only the curated set."
- **Tentative architecture/source choices.** When a thread is still a spike or option analysis, do not turn candidate paths into final statements. Distinguish current research access from later production access, first baseline import from repeatable backfill or enrichment, and the default sync option from possible alternate workflows. If the source only supports "likely", "at this stage", or "one option", keep that uncertainty in the draft.
- **Standup blockers stay explicit.** Do not replace a blocker with `None` just because there was partial progress or a new reply. Keep blocker status when the underlying decision, approval, alignment, or dependency is still unresolved; downgrade to `None` only when the user explicitly says there are no blockers or the source text clearly resolves the dependency.
- **Minimal context.** Product or cross-team decision posts should open with the gap and the ask. Do not recap unrelated shipped work (e.g. a prior ticket's empty-state fix) unless it is required to understand the question.
- **Meeting and calendar titles.** When drafting a Slack ask that proposes a meeting, suggest a title that names the concrete subject (ownership, Legacy CRM reuse, PII, service boundaries). Do not reuse a product-phase label already used as the product nickname (for example "MVP") as topic shorthand; see `agent_workflow_guidelines.md` §45.9. Prefer plain terms over calques such as "eagle view" (use high-level or bird's-eye); see §45.2.
- **Symmetrical questions.** When a post has multiple product choices, give each question the same shape: short scenario, API or payload example when it helps, then labeled options `*A)*` / `*B)*` / `*C)*` with tradeoffs in one line each.
- **Architecture debate replies.** Ask one concrete open question between the real alternatives on the table. Do not invent a soft middle option the other party did not propose (for example "operator convenience on top of X") when that option is not a valid architectural outcome. Prefer "the open question is still A vs B" over "I am not sure why we should…" when challenging a peer proposal.

## BI / data-team asks (cross-team)

When the author investigated BI tables or schemas and asks BI/PJM for help:

- **First person when the author did the work.** Use *I searched*, *I found*, *I could not find*; not *we audited* unless a team did it together.
- **Avoid data-warehouse jargon** unless the reader uses it daily. Replace terms like *mart*, *baseline mart*, *cutover*, *delta*, *export shape* with plain words: *BI table*, *which table to use*, *last updated column*, *separate datasets*.
- **Ask about source tables, columns, and reliability** (completeness, v1 vs v2, which row is canonical, whether `update_time` is maintained). Do **not** ask how BI should deliver files (CSV, S3, file count); export transport is the requester's problem unless BI owns delivery by policy.
- **Missing fields:** give 3–4 examples with a one-line plain description of what the field means; link to a Confluence or doc section for the full list. Do not paste long tables in Slack.
- **Search scope in P.S.:** list which DBs/clusters were checked and ask the reader to point to other stores (e.g. Redshift) if data might live elsewhere.
- **Team signature tags** (e.g. `[TEAM-SIGNATURE]`): add only when local facts or the user confirm the tag. Do not copy signatures from other people's messages.

## Editing existing messages

Slack's API does not support editing sent messages. When the user asks to edit or update a previous post, say so clearly and ask how they want to handle it. Options: post a new corrected message (user deletes the original manually), or reply in-thread.

## Finding channel IDs

Extract the ID directly from a Slack URL: `https://.../archives/C0123456789` means the channel ID is `C0123456789`. If only a channel name is given, search for the channel using your Slack integration.

## Saving the draft (required delivery method)

Use the **draft-save** Slack integration with the channel ID and approved message text. Return any draft or channel link the integration provides so the user can open Slack and send.

- Before draft-save, scan the message body: every hyperlink must use the active Slack draft tool's supported link syntax. For the current Slack draft-save tool, use `[label](url)`, not `<url|label>` or bare URLs with a separate label line.
- For thread replies, pass the parent message timestamp when the integration supports it.
- If a draft already exists for that channel, tell the user to edit or delete it in Slack first, then retry.
- When the user asks for changes after a draft was saved, do not imply that the existing draft can be updated in place. Tell the user to delete/remove the old draft in Slack, then save a new draft with the corrected text.
- **Draft-save does not overwrite.** Each draft-save call creates a **new** draft; it does not update or replace a prior draft for the same channel/thread (there is usually no draft-update or draft-delete API). When you save a revised version, the old draft remains. Report the new draft id, name which draft to keep, and tell the user to delete the superseded one(s) in Slack. Do not assume a re-save replaced the earlier draft.
- **Immediate/direct send is forbidden** in this skill, even when the user says "post", "send", or "notify". Those words mean save a draft and instruct the user to send from Slack.

After saving, remind the user: *Open Slack → Drafts & Sent → review → Send.*
