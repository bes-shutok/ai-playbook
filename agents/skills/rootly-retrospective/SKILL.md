---
name: rootly-retrospective
description: Create concise, evidence-backed incident retrospectives as local Markdown for a person to paste into Rootly. Use for incident reports, timelines, customer impact, root-cause analysis, and follow-up actions; do not use for publishing to Rootly.
---

# Rootly retrospective

Create a clear local Markdown retrospective that a user can review and paste into Rootly manually. The report must separate facts, evidence gaps, and proposed prevention work, so it remains useful after the original chat threads or dashboards are no longer available.

## Authority and handling rules

- Write or update the local document only. Do not create, edit, publish, or comment on a Rootly incident unless the user separately and explicitly asks for that external action and an authorized route is available.
- Do not include personal data or secrets in the report or this skill. Exclude user identifiers, contact details, device tokens, credentials, secrets, raw payloads, and unredacted logs.
- Use aggregated counts and neutral roles where they communicate the needed fact. Redact or omit a detail that is not necessary to explain impact, cause, response, or prevention.
- Use neutral placeholders in examples and templates, never project, organisation, incident, customer, or employee details.
- Keep the skill portable. If the caller project's facts file has an optional `team_references_project` setting, resolve and read that repository-relative private context before drafting. It may contain organisation-specific terms, approved internal source locations, or evidence-handling rules. Do not copy those details into this skill.
- If the user confirms the report is private and access-controlled, necessary internal service names, dashboard or change-record links, and named evidence sources may be included in that report. This does not permit secrets, credentials, personal data, raw identifiers, or raw logs.

## Build the report

1. Start with a short incident summary: customer-facing effect, affected scope, confirmed impact, and immediate cause. Do not state a hypothesis as a fact.
2. Add a small terms section when abbreviations or uncommon technical terms are necessary. Explain each term at first use if only a few are needed.
3. Give the incident mechanism once, in causal order. Do not repeat it in the summary, impact, and root-cause sections.
4. Record customer impact precisely. State what a metric measures and what it does not measure. Do not treat a message count as a distinct-user count unless the evidence proves that equivalence.
5. Create a timeline in UTC unless the user agrees another single time-zone convention. Do not mix time zones. For UTC-only reports, write every known time in UTC and no local-time equivalent; state when a source has no recorded time rather than inventing one. Keep the timeline to incident events, from the event that created the production-side effect through resolution. Put earlier configuration history and later follow-up work in root-cause analysis or actions instead.
6. Use connected Why paths for root-cause analysis. Each next Why must investigate the answer before it, rather than restating the same cause. Split into separate paths when distinct conditions combined to create the incident. For a credential or configuration cause, explain how it entered or remained in the environment, or label that provenance unknown. End each path with a prevention requirement that removes or meaningfully limits that condition.
7. Make actions specific and testable: action, confirmed owner or `Not assigned`, status, evidence or basis, and a completion check. Do not invent owners, completion, dates, or confirmation. When copying a rendered action table, read the Owner and Target cells separately. Do not infer an assignment from text appended to an action-name cell. A completed review or decision does not complete a larger remediation action: mark the action in progress until its full completion check passes.

## Evidence and wording

- Prefer durable evidence such as approved change records, incident records, retained dashboards, and stable documentation.
- Do not depend on temporary chat links in the report. For a necessary chat finding, add a local evidence appendix with the shortest useful paraphrase or a short, redacted quote, source role, and exact UTC time when known. Keep the quote only when its wording matters.
- Mark unconfirmed points explicitly as an evidence gap, working finding, or proposed action. State what is unknown without guessing its cause.
- Attribute a claim only when the source supports that exact claim. Keep independent causal paths separate: say whether an activity directly produced the effect, enabled processing of pre-existing work, or only happened at the same time. Do not imply causation from timing alone.
- Prefer plain language. Use technical terms only where they make the statement more precise, and define uncommon abbreviations once. Do not introduce terminology that is not supported by the evidence.

## Review-only requests

- If the user asks only for review, assessment, clarification, or suggested wording, do not modify the local report. Provide exact replacement text, identify any wording that should remain unchanged, and state the evidence gap or source for each proposed change.
- Edit the report only when the user asks to create or update it.

## Review before handoff

- Check that every important claim has a durable source or a local evidence reference.
- Check that every known time is in the agreed time zone and that missing times are marked as unavailable.
- Check that the timeline contains no unrelated historical actions or post-resolution follow-up work.
- Check that the Why paths, mechanism, impact, and actions do not contradict each other.
- Check that each causal path distinguishes a direct source from an enabler, backlog, or coincidence.
- Check that every action status reflects the whole action, not only a completed review or partial step.
- Check that no personal data, secrets, credentials, raw logs, or temporary links remain.
- Tell the user the local file path and that they must review and paste it into Rootly manually.
