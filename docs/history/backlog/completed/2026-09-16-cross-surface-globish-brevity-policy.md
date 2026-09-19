# Backlog: align human-facing writing skills around concise Globish

Status: done
Priority: medium
Workflow: backlog
Date: 2026-09-16

Privacy boundary: this item is sanitized. It contains no personal names, email
addresses, internal URLs, company or product identifiers, ticket keys, branch
names, credentials, or private message text. The original discussion remains
outside this repository. The public research links below are safe to retain.

## Research signal

A recent internal discussion about AI-generated workplace text raised two related
needs:

1. Human-facing text should be short, direct, and easy for non-native English
   speakers to follow. Use common words. Keep only jargon and abbreviations that
   the audience needs.
2. The author remains responsible for meaning and accuracy. Editing grammar must
   not change the idea.

The current Slack boundary is more precise than the shorthand “AI-free” can
suggest: AI may prepare a draft, but the user manually reviews and edits the
draft before sending. The posted message therefore remains human-finalized.
That review boundary is separate from writing-quality guidance and must not be
weakened by improving the message-drafting skill.

Public research supports the cost concern. The linked Sifted article describes
growing resistance to long, formulaic AI-generated workplace writing and calls
out recognizable patterns such as em dashes, hype, and repeated contrast
phrases: [Sifted, "Startups are clamping down on internal AI slop"](https://sifted.eu/articles/startups-ai-slop-internal-communications).
The business.com survey reports that workers are especially frustrated when
unchecked AI output creates review or correction work, and ranks unedited output
and robotic messages among the main complaints: [business.com, "The AI Habits Your Coworkers Secretly Hate Most"](https://www.business.com/articles/annoying-ai-habits-study/).

## Current state

The repository already has several pieces of this policy:

- `projects/.ai-playbook/agent_workflow_guidelines.md` §39 requires plain,
  direct English and §45 defines plain-language vocabulary, first-use expansion,
  and a `## Terms` rule.
- `agents/skills/slack-message/SKILL.md` requires plain Globish, audience-aware
  vocabulary, and removal of unnecessary internal terms.
- `agents/skills/jira-workflow/SKILL.md` requires Globish and first-use
  clarification for abbreviations, with a hard size limit for bug and incident
  descriptions.
- `agents/skills/review-confluence-doc/SKILL.md` checks concise, plain-language
  prose and undefined jargon.
- `agents/skills/doing-code-review/SKILL.md` requires Globish in review comments
  and spells out abbreviations.
- `agents/skills/github-pr-workflow/SKILL.md` asks for simple, low-jargon PR
  summaries.
- `agents/skills/review-agents/documentation.md` reviews comments and docs for
  redundancy, wall-of-text writing, and jargon without payoff.

The rules are not yet one coherent contract. In particular:

1. Brevity is not consistently treated as a primary quality constraint across
   all human-facing surfaces.
2. The shared plain-language section explicitly excludes code comments, while
   code-comment review has related but separate prose rules.
3. Jargon and abbreviation thresholds differ by skill. Some skills define
   first-use rules, some add a `## Terms` section after a count threshold, and
   some only say to prefer plain language.
4. The Slack drafting workflow already supports AI-prepared drafts, while the
   discussion uses “AI-free” as shorthand for keeping sent Slack messages
   human-finalized. The policy wording should make the draft, review, edit, and
   send boundary explicit so it is not misread as either unrestricted posting or
   a ban on draft assistance.
5. Existing rules mostly describe how to write well, but do not always require
   a final compression pass that removes repeated context, generic conclusions,
   and author-facing process narration.

## Problem

An agent can satisfy one surface-specific writing rule while producing text that
is too long, too abstract, or too dependent on local jargon for the actual
reader. It can also make the Slack human-finalization boundary ambiguous or
allow the user-review step to be skipped. Duplicated wording rules make these
boundaries easy to miss and allow the same concept to drift across Slack, Jira,
Atlassian content, PR and review comments, plans, and code comments.

## Questions to answer before implementation

1. Does “Globish” mean a shared default for all human-facing output, with
   audience-specific exceptions, or only a recommendation for selected document
   types?
2. What is the minimum useful brevity check for each surface? A universal word
   or character limit would be unsafe for code comments, contracts, and detailed
   technical reviews.
3. Which terms count as widely shared technical vocabulary? The rule should
   keep familiar terms such as API or JSON when the audience needs them, while
   discouraging team-local abbreviations and unexplained metaphors.
4. Should the shared rule cover code comments, or should comments keep a linked
   language-specific rule under the documentation review skill?
5. How should a Slack skill express the human-finalization policy? The current
   practice is that AI prepares a draft, the user edits and verifies its meaning,
   and the user sends it. The skill should make that sequence and the ban on
   direct AI posting unambiguous.
6. Which Atlassian surfaces are in scope: Jira summaries and descriptions,
   Jira comments, Confluence pages, Confluence comments, or all of them?
7. How can the rules preserve accuracy and author voice? Shorter text must not
   remove uncertainty, acceptance criteria, safety constraints, or the author's
   actual decision.

## Fix candidates

1. Establish one canonical writing contract in the shared guidelines. Make
   these priorities explicit and ordered: preserve meaning, be concise, use
   plain Globish, keep only audience-relevant jargon, define uncommon terms,
   and verify the final text before saving.
2. Add a small decision table for audience and artifact type rather than a
   universal length cap. For example, use short outcome-first messages for
   Slack and comments, compact business-facing Jira text, and complete but
   compressed contracts and review findings.
3. Add a reusable final-pass checklist: remove duplicated context, generic
   introductions, stale drafting history, unnecessary headings, unexplained
   abbreviations, and sentences that do not change the reader's next action.
4. Reconcile each affected skill with the canonical contract. Keep only
   surface-specific rules in `slack-message`, `jira-workflow`, Confluence
   workflows, PR workflows, and review skills.
5. Preserve the Slack human-finalization boundary while improving the drafting
   workflow. Keep draft creation separate from sending, require user review and
   editing, and do not treat grammatical cleanup as automatically safe when it
   could change the intended idea.
6. Add realistic examples and negative examples for one Slack-like message,
   one Jira item, one Atlassian comment, one PR/review comment, and one code
   comment. Test that the examples remain accurate after compression and that
   uncommon terms are either replaced or defined.
7. Add a lightweight validation check only where a mechanical check is useful,
   such as em-dash detection, obvious duplicate boilerplate, or missing
   first-use expansion. Keep judgment-based readability and meaning checks in
   the skills.

## Acceptance criteria

- One canonical rule defines the relationship between meaning, brevity,
  Globish, audience vocabulary, and terminology handling.
- The rule clearly distinguishes widely shared technical terms from local or
  niche jargon and states when to spell out an abbreviation or add `## Terms`.
- The rule covers or explicitly delegates code comments, Jira and Confluence
  content, Slack-related workflows, PRs, and review comments.
- Every affected skill points to the canonical rule and retains only its own
  surface-specific constraints.
- The Slack human-finalization policy is explicit: AI can prepare a draft, the
  user reviews and edits it, and only the user sends it. A writing-quality
  improvement cannot silently authorize direct AI posting or skip that review.
- Examples show shorter text without loss of meaning, uncertainty, safety
  constraints, acceptance criteria, or author voice.
- A review of the changed skills finds no duplicated or contradictory writing
  policy, and the public-hygiene scan passes.

## Additional witness: session language was not preserved

In a later agent session, the user explicitly established English as the
conversation language, but subsequent progress and status text switched to
another language. This is not a Globish-quality issue alone. It is a session
state violation that can make technical status, safety gates, and next actions
hard to verify.

The shared writing contract should therefore treat an explicit user-selected
language as a session invariant. Resumed turns, compacted context, delegated
review updates, and final responses must inherit it. When no language has been
selected, English is the default for this workflow. Before emitting human-facing
text, the agent or a lightweight hook should check language consistency and fall
back to the session language when the draft does not match it. This check must
preserve code, quoted source text, and user-requested translations.
