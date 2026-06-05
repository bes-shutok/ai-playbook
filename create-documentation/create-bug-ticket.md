# Command: Create Jira Incident / Bug Ticket (Strict Size Enforcement)

## Purpose
Generate a concise, human-readable Jira ticket description for an incident or bug.
All extended context, domain concepts, and technical analysis MUST be extracted into a separate temporary Markdown document.

---

## Hard Size Rules (non-negotiable)
- Jira description:
  - Hard maximum: 800 characters
  - Target: 400 characters
- The command MUST count characters.
- If the description exceeds 800 characters:
  1. Rewrite and compress wording.
  2. Move content to the temporary Markdown document.
  3. Repeat until under limit.
- If still above 800 characters, fail and ask the user what to trim.

---

## Jira Description Content Rules
- Jira description MUST NOT contain:
  - Core Concepts
  - Key Concepts
  - Terminology sections
  - Architecture explanations
  - Incident timelines
  - Root cause analysis
- Abbreviations may be used, but MUST be clarified in parentheses on first use.
  Example: MQ (message queue)

---

## Input Rules
- Use provided textual context (alerts, incidents, Slack threads, logs).
- Inspect relevant code to understand behavior.
- Perform external research only if required to understand behavior.
- Do NOT include solution design or implementation detail in Jira.
- Technical identifiers are allowed only as navigational anchors.

---

## Output Artifacts
The command produces exactly two outputs:
1. Jira ticket description (final, size-constrained)
2. Temporary Markdown document (supporting detail)

---

## Jira Ticket Description Structure (fixed)

### Formatting
- Each section header starts on its own line.
- One empty line between sections.
- Plain text only.
- No markdown headers, no symbols, no decorative bullets.
- Do NOT include ticket type or priority (these are Jira metadata).

---

### Incident Summary
- 1–2 sentences.
- Plain language.
- Describe:
  - What is broken
  - Who is impacted
  - Why it matters now
- No speculation.
- No technical detail.

---

### Impact
- One short paragraph or up to 2 bullets.
- User and/or business impact.
- Duration or frequency if known.
- If unknown, explicitly state what is unknown.

---

### Current Behavior
- One short paragraph.
- Observable behavior only.
- Based on errors, logs, metrics, or known repro.
- No explanation of internal logic.

---

### Expected Behavior
- One short paragraph.
- Outcome-focused and testable.
- No solution design.
- If unclear, stop and ask questions before writing.

---

### Acceptance Criteria
- 2–4 bullets max.
- Outcome-based.
- Independently verifiable.
- No class names or method names.

---

### Technical References
- Short list only:
  - Class names
  - API names
  - Method names
- No explanations.

---

### Supporting Material
- Reference to the temporary Markdown document(s).

---

## Temporary Markdown Document

### Purpose
Contain all information excluded from Jira to preserve brevity.

### Allowed Content
- Domain concepts and terminology
- Full incident timeline
- Logs, metrics, dashboards
- Detailed reproduction steps
- Code walkthroughs
- Assumptions, risks, and unknowns
- External research
- Non-scope clarifications
- Dependencies

### Rules
- No size limit.
- Deep technical detail allowed.
- Must not restate the Jira summary or Acceptance Criteria verbatim.

---

## Final Validation (must pass)
- Jira description ≤ 800 characters.
- Jira description readable by non-engineers.
- No conceptual sections in Jira.
- All depth moved to the temporary Markdown document.
- Output does not look templated or auto-generated.