---
name: jira-workflow
description: Jira workflow for creating/updating Jira stories and creating git branches from Jira tickets. Trigger phrases: "create a Jira story", "update Jira ticket", "create a branch for PROJ-XXXXX".
---

# Jira Workflow

## Jira Story Format
- Keep scope at the requested service level (not program-wide).
- Use forward-looking sections (for example scope/out-of-scope).
- Limit body to business-relevant scope and main dev points; keep Jira story descriptions business-facing and move detailed technical implementation content into comments or linked docs.
- For rollout or verification tickets, keep the issue body focused on the outcome to verify; put environment-specific manual test procedures and tactical technical caveats in comments, not in the main description.
- Avoid retrospective phrasing.
- When a user wants a ticket to stand on its own, describe the substance of the change directly instead of relying on rollout labels or phase names as shorthand.
- When adding links in Jira descriptions or comments, use standard markdown link syntax: put the title in `[]` and the URL in `()`.
- Before proposing a manual verification scenario, verify that the induced failure exercises the component under change rather than only a downstream dependency.
- When replanning a sequential backlog, reuse existing placeholder Jira keys when the user asks for ticket-number parity with implementation order; do not create new keys unless placeholders are exhausted or the user requests new issues.
- When updating repurposed tickets, prefer **Goal / Problem / Product decisions / Deliverables / Acceptance criteria / References** sections. Do **not** add **Out of scope** sections unless the user explicitly asks for them.
- Do **not** add a separate **Dependencies** section that lists follow-up Jira keys for parallel or later stories. Mention cutover or timing coordination inline under the relevant deliverable slice only when it helps humans (for example "timed with profile batch migration follow-up").
- A ticket describes only its **own** scope. Omit extraction/split history ("former Slice 2"), prioritization reasoning ("lowest near-term priority"), and transient current-state caveats; that meta belongs in planning/decision docs, not the ticket. See agent_workflow_guidelines.md §45.8 (document results, not deliberation).
- **Writing style (mandatory):** no em dashes (`—`) in ticket summaries, descriptions, or comments; use commas, semicolons, colons, or short sentences, and prefer globish. Before saving a ticket body via your Atlassian integration, scan the composed text for `—` and replace every occurrence. See agent_workflow_guidelines.md §39 and §45.
- Match MVP product vocabulary in ticket text to canonical repo docs (for example single-client MVP; avoid multi-tenant ingestion language when docs state Sporty is the sole source).
- When repurposing an existing Jira issue, review older comments for stale scope. If your own older comments now conflict with the active story body and Jira comment deletion is available, delete the outdated comments instead of leaving superseding clarification comments that keep obsolete guidance visible.
- When cleaning up Jira comments after a story-scope change, do not touch comments left by other people unless the user explicitly asks for that.
- When a Jira story/comment cites a specific Slack discussion as scope evidence, include the Slack permalink in that comment rather than referring to the discussion indirectly.

---

# Create Branch from Jira Ticket

This skill automates the process of creating a git branch from a Jira ticket. It fetches the ticket information, determines the appropriate branch type, and creates a branch following the project's naming convention.

## Instructions

When the user provides a Jira ticket URL (e.g., `https://your-org.atlassian.net/browse/PROJ-12345`) or asks to create a branch from a Jira ticket, follow these steps:

### Step 0: Pre-requisite Checks

#### Check 1: Verify Atlassian integration

1. Verify you can read Jira issues via your environment's **Atlassian integration** (issue fetch capability).
2. If the integration is unavailable, tell the user:
   ```
   ⚠️  Atlassian integration is not available.

   Install and authenticate Jira/Atlassian access for your agent environment,
   then retry this workflow. See user AGENTS.md or your agent setup docs if present.
   ```
3. STOP execution until the integration works.
4. If calls fail with OAuth refresh errors such as `invalid_grant`, `Invalid refresh token`, or `OAuth token refresh failed`, tell the user to re-authenticate the Atlassian integration, then retry.
5. When the integration is authenticated, continue to Step 1.

#### Check 2: Verify Git Repository
1. Check if the current directory is a git repository using `git status`
2. If NOT a git repository:
   - Show error: "This is not a git repository. Please navigate to your project directory first."
   - STOP execution
3. If IS a git repository, continue to Step 1

### Step 1: Extract Ticket Information from URL
1. If user provided a URL like `https://your-org.atlassian.net/browse/PROJ-12345`:
   - Extract the cloud ID: `your-org.atlassian.net`
   - Extract the issue key: `PROJ-12345`
2. If user only provided a ticket key like `PROJ-12345`:
   - Check the user's facts/profile document (e.g. `facts.md`) for a default Jira domain; use it as the cloud ID if present
   - Otherwise ask user for the Atlassian cloud ID or full URL
3. If user didn't provide any ticket info:
   - Ask user: "Please provide the Jira ticket URL or ticket key (e.g., PROJ-12345)"

### Step 2: Fetch Jira Ticket Details
1. Fetch the Jira issue via your Atlassian integration with:
   - `cloudId`: extracted from URL or provided by user
   - `issueIdOrKey`: extracted ticket key
2. Extract the following information:
   - Issue type (from `fields.issuetype.name`)
   - Summary (from `fields.summary`)
   - Description (from `fields.description`)
3. If the API call fails:
   - Show error message to user
   - Ask if they want to retry or provide a different ticket

### Step 3: Determine Branch Type
Map the Jira issue type to a git branch type:
- If issue type contains "bug", "error", "incident" → use `fix/`
- If issue type contains "feature", "enhancement", "new feature" → use `feature/`
- If issue type contains "refactor", "refactoring" → use `refactor/`
- If issue type contains "task", "work item" → use `feature/`
- If issue type contains "chore" → use `chore/`
- If issue type contains "epic", "large work item" → use `feature/` (epics are feature work, not structural refactoring)
- Otherwise → ask user to choose: "fix/", "feature/", "refactor/", or "chore/"

### Step 4: Generate Branch Name
1. Take the ticket summary and convert it to kebab-case:
   - Convert to lowercase
   - Replace spaces with hyphens
   - Remove special characters except hyphens
   - Remove "be -", "backend -", "service -", etc. prefixes if present
   - Trim to reasonable length (max ~50 characters for the description part)
2. Construct the full branch name:
   ```
   <type>/<TICKET-KEY>-<kebab-case-description>
   ```
   Example: `refactor/PROJ-12345-service-refactor`

### Step 5: Show Ticket Information and Proposed Branch
1. Display the ticket details to the user:
   ```
   📋 Jira Ticket Information:
   - Ticket: <TICKET-KEY>
   - Type: <issue type>
   - Summary: <ticket summary>
   ```
2. Generate and show the proposed branch name
3. **IMPORTANT**: DO NOT create the branch yet. Only show what will be done.

### Step 6: Ask for User Confirmation
1. Show a clear confirmation message in English:
   ```
   I will create this branch from `master`: <branch-name>

   Please confirm:
   - If the branch name is correct, reply "yes" or "ok"
   - If you want to change it, provide the new branch name
   - If you want to cancel, reply "cancel"
   ```
2. **STOP and WAIT for user response**
3. Do NOT proceed to Step 7 until user confirms
4. If user provides a custom name:
   - Update the branch name to use the custom name
   - Show the updated message again and ask for confirmation
5. If user cancels:
   - Stop execution and thank the user
6. If user confirms (says "yes", "ok", "looks good", etc.):
   - Proceed to Step 7

### Step 7: Create Branch from Master (Only After Confirmation)
1. **ONLY execute this step if user confirmed in Step 6**
2. Get the current branch name using `git branch --show-current`
3. Checkout master branch: `git checkout master`
4. Pull latest changes: `git pull origin master`
5. Create and checkout new branch: `git checkout -b <branch-name>`
6. Confirm success to user:
   ```
   ✅ Successfully created branch: <branch-name>

   You are now on the new branch and can start working.
   ```

### Step 8: Error Handling
If any step fails:
- Show the error message to user
- Provide suggestions on how to fix it
- Ask if they want to retry or abort

## Examples

### Example 1: Create branch from URL
```
User: https://your-org.atlassian.net/browse/PROJ-12345
```

Expected flow:
1. Check Atlassian integration is available ✓
2. Extract: cloudId = `your-org.atlassian.net`, issueKey = `PROJ-12345`
3. Fetch ticket → Type: "large work item", Summary: "BE - service refactor"
4. Determine type: `feature/` (epic maps to feature)
5. Show ticket info and generate name: `feature/PROJ-12345-be-service-refactor`
6. Show confirmation message: "I will create this branch from `master`: feature/PROJ-12345-be-service-refactor"
7. **WAIT for user confirmation**
8. User says "yes" or "ok"
9. Create branch from master

### Example 2: Create branch with custom name
```
User: Create a branch for PROJ-12345
```

Expected flow:
1. Ask for full URL or cloud ID
2. Fetch ticket details
3. Show ticket info and proposed branch name
4. Ask for confirmation
5. User provides custom name instead
6. Show updated confirmation message with new name
7. **WAIT for user confirmation**
8. User confirms
9. Create branch with custom name

### Example 3: Atlassian integration unavailable
```
User: https://your-org.atlassian.net/browse/PROJ-12345
```

If the Atlassian integration is unavailable:
- Tell the user to install and authenticate Jira access for their agent environment
- Stop execution
- Wait for the user to retry

## Notes

- This skill requires an authenticated Atlassian integration for Jira read/write
- The branch naming convention follows: `<type>/<TICKET-KEY>-<description>`
- Common types: `fix/`, `feature/`, `refactor/`, `chore/`
- The skill always creates branches from the master branch
- If the proposed branch name is too long, it will be trimmed to a reasonable length
- **The user MUST confirm before the branch is created** - the skill will NOT automatically create the branch
- The user always has the option to provide a custom branch name during confirmation
- The user can also cancel the operation at any time

---

# Bug / Incident Ticket Format

When creating bug or incident tickets, use this constrained format.

## Hard Size Rules
- Jira description: **hard max 800 characters**, target 400
- Count characters. If over 800, rewrite/compress or move detail to a supporting doc.
- Move all deep technical context to a temporary Markdown document (no size limit).

## Jira Description MUST NOT contain
- Core/key concepts or terminology sections
- Architecture explanations
- Incident timelines or root cause analysis
- Solution design or implementation detail

## Required Sections (plain text, no markdown headers in Jira)

1. **Incident Summary**: 1-2 sentences. What is broken, who is impacted, why it matters now.
2. **Impact**: 1 short paragraph or 2 bullets. User/business impact, duration/frequency.
3. **Current Behavior**: observable behavior based on errors/logs/metrics.
4. **Expected Behavior**: outcome-focused, testable, no solution design.
5. **Acceptance Criteria**: 2-4 bullets, outcome-based, independently verifiable.
6. **Technical References**: short list of class/API/method names only.
7. **Supporting Material**: reference to the temporary Markdown document.

## Supporting Markdown Document
Contains everything excluded from Jira: domain concepts, timelines, logs, code walkthroughs, reproduction steps, assumptions, risks.

## Final Validation
- Jira description ≤ 800 characters
- Readable by non-engineers
- No conceptual sections in Jira
- All depth in supporting doc
