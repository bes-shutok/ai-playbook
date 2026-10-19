## Step 1: Extract Lessons
Review communication from this task and list concrete items:
- mistakes and false assumptions
- user corrections and constraints
- missing or misleading documentation
- recurring rework/friction

Classify each lesson as exactly one:
- Human best-practice guidance
- Module/system-specific knowledge
- Enforceable LLM instruction rule
- LLM-only example/playbook
- Temporary artifact

**Important: style and wording corrections are lessons too.** If a user corrects the tone, phrasing, vocabulary, or formatting of generated output (e.g. "remove long dashes", "use simpler words", "prefer globish", "use API contract not wire contract"), treat it as a lesson and capture it as a skill rule, not just apply it to the current artifact and move on. Vocabulary replacements that apply across projects go in `agent_workflow_guidelines.md` §45.2; recurring workspace terms go in the relevant `dictionary.md` or repo glossary (`docs/maintenance/glossary.md` after migration; legacy `docs/glossary.md`).

### Correction ledger for overturned technical output
When a user corrects, rejects, or materially redirects a technical explanation or implementation, build a correction ledger before classifying the lesson. Record: the initial claim or recommendation, the rejected alternative, the user-supplied correction, the evidence that settled the dispute (source, log, reproduction, or test), the corrected mechanism, and the missing verification step. Review the complete current-task conversation, including failed attempts and user-provided attachments, rather than deriving lessons only from the final diff or a completion summary. Preserve both layers when they differ: the technical mechanism belongs in the appropriate canonical project or language guidance, and the missing verification step belongs in the owning workflow skill when it could prevent the same correction in a future task.

### Source-check self-audit
When the user corrects a factual detail or asks what could have been learned by digging deeper, explicitly ask:
- Could an available source system, repository artifact, ticket comment, PR state, log, or local file have revealed this before the user corrected it?
- Did I stop at a summary when primary sources were available?
- Is the lesson only the corrected fact, or is the deeper lesson a missing verification step?

When a user challenges a framework explanation, also check whether the verified behavior is a
reusable language or framework guideline. Do not classify it as conversational clarification
until the applicable canonical guideline file has been checked for an existing rule or a missing
durable rule.

For framework or integration behavior, verify the exact boundary that failed: exercise the
actual adapter, mapper, serializer, or client with the proposed method signature and inspect
both execution and result mapping. A successful side effect is not proof that the surrounding
return-type contract is valid. If the proposed and corrected forms differ, test the rejected
form or preserve its observed failure as the witness before dismissing it as already covered.

If the answer is yes, capture the deeper verification rule, not only the corrected output. For example, if a weekly report missed replaced PRs, Jira-comment-only work, or ownership split across two Jira stories, the lesson is to check GitHub/Jira source state before drafting ambiguous report sections.

### Generalization pass
Before writing any lesson to its final destination, apply a generalization pass:

1. **Identify the abstract principle** behind the specific incident. Ask: "What is the underlying pattern, independent of this particular technology, file, module, **or employer identity**?" Generalize across all of these axes, not only technology: a rule that still requires a specific company, service name, or ticket system to be stated has not been fully generalized.
1b. **Name the root-cause family and the shape trigger.** Identify which family in the principle catalog (`coding_guidelines.md` #17+) this incident belongs to, and write the *shape trigger*: the situation (independent of this file/module) that should make a future reader suspect this family. If no family fits, propose one to the catalog rather than leaving the lesson unanchored. See the `generalize` skill (`../generalize/SKILL.md`) for the map procedure.
1c. **Interrogate every proper noun and identifier in the incident** before drafting. Service names, company names, product names, ticket prefixes/IDs, branch/plan slugs, person names, customer/market lists, internal hostnames/URLs, and exact counts/dates are NOT background color: each one must earn its place. For each, ask: "Would the rule be weaker if I replaced this with a generic role ('the target service', 'a reviewer', 'the new markets', 'the feature branch')?" If no, the generic form IS the lesson; the specific value belongs only in your private notes, never in a corpus that may be public. This step is what stops an example from being drafted around `<employer>-<product>-service` / a country-code list / `<TICKET>-10889` in the first place: those read as incidental context but are employer fingerprints.
2. **State the general rule first**, then add the specific instance as a concrete example. The rule should remain correct even if the specific tool, framework, or module changes.
2b. **Format using the standard Principle-based Template**: When adding a new lesson (e.g., to `development_lessons.md`), format it according to the standard template defined in the `generalize` skill (`../generalize/SKILL.md` Phase 4.5).
3. **Check whether the generalized rule already exists** in canonical docs or instruction files, and whether an existing same-family lesson already covers this shape. If either holds, add only the missing witness and cross-link rather than creating a near-duplicate; do not create a duplicate rule.
3b. **Incident-repo vs cwd pre-check (required before the five-branch fork in item 4).** Before classifying as fork (3) cross-project UL, identify the repo where the incident occurred  -  the witness's repo, derived from file paths, git history, or session context (NOT the cwd where `learn` happens to be running). If that repo is **not** the current cwd repo, you are capturing a **deferred lesson**: STOP and either (a) `cd` to the incident repo and re-run `learn` there so it lands in that repo's `docs/maintenance/development_lessons.md`, or (b) ask the user whether to defer the capture. **Never write a project-specific incident into the UL corpus just because that is the corpus available in the current cwd**  -  this is exactly how the playbook UL corpus came to hold project-specific lessons: before 2026-10 the playbook repo had no project corpus of its own, so any incident captured while cwd is the playbook repo defaulted into the only corpus on disk (the UL file). Item 4's five-branch fork is judgment; this pre-check is the high-recall first gate that catches the cross-repo case before judgment is applied.
4. **Decide the scope**: after generalizing, apply the FIRST discriminator - **abstract precept vs concrete lesson** - then assess portability. Do **not** treat "not useful in every language" as proof the rule is project-specific. Five-branch fork (resolve `shared_docs_dir` from `user_facts_path`):
   - **(1) Abstract universal precept -> `coding_guidelines.md`**: a do/do-not rule that is correct and useful in *any* project (Kotlin microservice, Python data pipeline, frontend app) and carries no incident witness. If the rule mentions FIFO matching, batch aggregation, CSV parsing, report generation, or similar domain concepts, it is likely too specific for this file even after generalization.
   - **(2) Stack or language-ecosystem precept -> language/JVM file under `shared_docs_dir`**: a do/do-not (or short methodology) rule that is portable across repos of one stack or language but not every language. Examples: Java/Kotlin import vs fully qualified type names, MockK/Mockito idioms, Reactor error stubbing, Python packaging patterns. Place the **full rule** in the matching file (`jvm_guidelines.md` for shared JVM/Java+Kotlin style, `java_guidelines.md` / `kotlin_guidelines.md` / `python_guidelines.md` for language-only). Add a one-line pointer in user `AGENTS.md` shared-guidelines index when a new `#N` is easy to miss. In the incident repo, keep **at most** a thin project-corpus witness pointer (`see jvm_guidelines.md #N`), never the full rule body. **Default here when the rule would correctly guide an unrelated service in the same language/stack with no shared domain model.**
   - **(2b) Company-wide convention -> `company_guidelines_master` (facts key)**: a do/do-not rule or convention shared by repositories of the same company or organization because they perform the same kind of work (same integration responsibility, shared platform or delivery conventions), even when their product domains differ and the rule is not universal across organizations. Place the **full rule** in the company guidelines master and keep at most a concise project witness plus a pointer in the incident repo's project corpus; sync repo mirrors after editing the master (Company rule workflow, Step 2). Add a one-line cross-reference in instruction files per the Step 6 placement ladder. **Sibling search is required before choosing fork (4)**: when the incident repo is company-scoped (under `company_projects_root` per facts; ownership-scoping resolution test in item 5d), grep the company guidelines master for the lesson's topic keywords first; a hit is strong evidence the company scope applies. Under the company root with the master file missing (config drift), do not treat the failed or empty grep as evidence against company scope; route through the item 5c blocking placement question. Outside the company root (a personal repo, or a repo under neither workspace root) the company master is out of scope: skip the sibling search and do not select fork (2b); if the rule still looks company-scope, follow item 5c (blocking placement question) instead of defaulting to fork (4).
   - **(3) Concrete cross-project lesson -> user-level corpus**: a generalized lesson whose value is the **incident witness** (mechanism + failure mode) and that would re-bite in another project of any stack. Tag it strict (`**Principle:** Family X`, next `UL#N`) in the user-level `development_lessons.md` (resolved from `shared_docs_dir`); Step 6.6 gates this corpus. Prefer (3) over flattening into (1)/(2) when stripping the witness loses the preventive signal.
   - **(4) Project-specific -> repo `development_lessons.md`**: a reusable principle within this project that **requires** domain context (financial calculations, data matching, tax reporting, product-specific contracts). Write it as a general principle with repo-specific examples, convention-tagged (`**Principle:** Family X`). Module-level quirks stay module-scoped but still phrased as a reusable principle for that module rather than a one-off incident report.
4a. **Separate the generalized rule from its incident witness (required for every candidate lesson).** The generalized rule determines placement; the incident witness (the concrete failure, files, and reproduction) may remain in the project corpus as a short example or pointer. Never let a long witness narrative justify a narrower placement: placement follows the rule, not the story.
4b. **Stack-portability gate (required before fork (4) full project lesson).** Ask: "Would this rule correctly guide work in an unrelated repo that shares only the language or JVM/Spring/Python stack, with no shared domain?" If **yes**, you are in fork **(2)** (or (1) if truly universal): write the canonical rule under `shared_docs_dir` first, then optionally a witness pointer in the project corpus. If you almost chose fork (4) because the incident happened in one product repo, re-run this gate. Anti-pattern: dumping Java/Kotlin style hygiene into `development_lessons.md` as a full `#N` because it "is not Python-universal" (that is fork (2), not fork (4)).
4c. **Company-portability gate (required before fork (4) full project lesson).** Ask: "Would this rule guide another repository in the same organization that performs the same kind of work, even if its product domain differs?" If **yes** and the master resolves per the item 5d ownership-scoping resolution test, you are in fork **(2b)**: write the full rule to `company_guidelines_master` first, keep only a concise project witness and pointer in the project corpus, and sync repo mirrors. If **yes** but the master does not resolve, stop and report the item 5c blocking placement question. If you almost chose fork (4) because the incident happened in one company repo, re-run this gate after the 4b stack-portability gate. Anti-pattern: storing a company-wide integration convention as a full project lesson because "it is not universal across every possible project" (that is fork (2b), not fork (4)). A team or infrastructure ownership boundary (which team owns which tickets, components, or delivery stages) binds sibling repos with the same responsibility, so it is company scope, not project scope. If no, continue down the ladder: fork (3) when the witness is the reusable value, fork (4) only with a stated residual dependency.
5. **Place accordingly**: write the full text at the chosen scope. If the rule goes to shared canonical docs (fork 1, 2, or 2b), reduce the project instruction / project corpus entry to a cross-reference (plus optional short witness). If it stays project-level (fork 4), write the full lesson in the project corpus.
5b. **Mirror-fan-out when this skill's fork changes:** if you renumber or retarget the placement fork (item 4 / 4b), grep sibling skills for `mirrors learn`, `three-way fork`, and `fork 2 vs fork 3`, and update every living claim that mirrors this pass (especially `generalize`) in the **same change set**. The same fan-out applies when the ownership-scoping resolution test changes (living surfaces: facts `Guideline canonical homes`, fork (2b), item 5d, the Completion Checklist sibling-search line, `done` Step 3 item 4a). Also update living UL See also lines that cite item 4 by those old labels. Do not leave a skill claiming it mirrors learn while still describing the previous fork.
5d. **Ownership-scoping resolution test:** the master resolves only when the incident repo (per item 3b) sits under the company workspace root (`company_projects_root` in facts) AND the key's path exists. Containment compares fully resolved absolute paths component by component: resolve symlinks, expand the tilde, strip trailing separators, normalize Unicode to a single form, and normalize case when the filesystem is case-insensitive (mechanics mirrored in the facts `Guideline canonical homes` paragraph; update both per item 5b). A repo at the root itself is not under it, and a directory sharing only a leading substring with the root does not match. Outside the company root (a repo under the personal root, or under neither workspace root) the key is treated as unresolved even though the user-level facts table lists a global value; under the root with the path missing it is also unresolved (reason: config drift), which `done` Step 3 item 4a audits at commit time as a non-blocking drift WARNING.
5c. **Placement receipt (required in the learn run output).** For every placed lesson, state the selected scope, why each alternative scope was rejected, and the ownership-scoping resolution outcome (master resolved, outside the company root, or config drift; one line per lesson; for example "fork (2b): company-wide convention; master resolved; not universal (org-specific), not fork (4) (guides sibling repos with the same responsibility)"). Evaluate the residual dependency and the canonical-destination resolution BEFORE executing item 5's corpus write: item 5c conditions the write, it does not follow it. For a fork (4) placement the receipt must also state the residual dependency that keeps the rule project-specific (a material dependency on the service domain, module contract, repository architecture, or project-only operational behavior). If no residual dependency remains, do not write the full lesson to the project corpus: re-route to fork (2b) or fork (3). When the rule is company-scope but `company_guidelines_master` does not resolve, report the missing canonical destination as a blocking placement question instead of writing a full project lesson. The question and the routing answer appear in the run output as a one-line receipt (for example `company-scope rule; master unresolved (config drift): routed to <scope> per user`), and the receipt states the reason: outside the company root, or config drift when the repo is under the root but the key's path is missing. The routing answer respects fork (2b): outside the company root, fork (2b) is not offered even on request (deferral to a company repo is the preferred routing; the user may instead select fork (3) or (4)). The resolution outcome is decided by the ownership-scoping resolution test (item 5d). The receipt is temporary run output; it need not become part of the canonical lesson, but the done commit run's lesson-scope audit uses it as placement evidence.
6. **Add cross-references for discoverability**: When placing or updating a lesson in project docs (development_lessons.md), also add or update cross-references from instruction files (CLAUDE.md, AGENTS.md) so the lesson is discoverable when working on the relevant topic. A guideline in `development_lessons.md` is only useful if agents know to look for it when processing related code. Check for sibling documents (grep for related keywords) that should reference the same lesson.
7. **Verify numbered lesson anchors before writing**: when a lesson cites another lesson by number (Principle, See also, Distinguishing), grep the target corpus for the cited `## N.` heading FIRST and confirm that heading's topic matches the cited description; a number that resolves to an unrelated lesson silently breaks the recall chain. Never copy a cited number from memory or from another lesson's text.

Example:
- **Too specific**: "Excel column headers in the crypto gains sheet should say 'Quantity' instead of 'Amount'"
- **Generalized (fork 1, universal)**: "User-facing output labels (column headers, API field names, report section titles) should use self-explanatory terminology, not terse names inherited from upstream source formats." → any project, any output surface → `coding_guidelines.md`.
- **Generalized (fork 2, stack/language)**: "Prefer imports over fully qualified type names for annotations and constructors; when one FQN is fixed in review, fan out across PR-touched sources." → true for any Java/Kotlin repo, useless as a Python rule → full text in `jvm_guidelines.md` (pointers from `java_guidelines.md` / `kotlin_guidelines.md`); project corpus gets at most a witness pointer. **Wrong default:** a full project `development_lessons.md` `#N` because the incident was reviewed on one service PR.
- **Generalized but project-scoped (fork 4)**: "Post-aggregation validation must run after all groups are accumulated, not per-row." → sounds general but assumes batch row processing with mid-accumulation state, so only relevant in data-pipeline projects → keep full text in project corpus, do not elevate to `coding_guidelines.md` or `jvm_guidelines.md`.
- **Identity generalization (required on every lesson)**: Draft example *"On `<config-repo>` PR #6, commits added `<country-list>` markets but the title still said `<TICKET>-10889: Add <service>-<market> UAT config draft`"* → the employer fingerprints are the config-repo name, the country list, the ticket prefix+ID, and the service slug. None are load-bearing for the rule "keep the PR title in sync with scope as it expands." Generalize to: *"On a config PR, commits added new markets and segment keys but the title still named only the original market draft"* (rule identical, no employer identity leaked). The discriminator: if replacing the identifier with a role/category leaves the rule intact, the identifier was fingerprint, not lesson.

### Anti-pattern: premature dismissal as "already covered"
Before discarding a candidate lesson because an existing rule seems to cover it,
verify that the **specific failure mode** from this session is addressed, not
just the general topic. Common missed distinctions:
- **Policy vs methodology**: an existing rule says *what* to do (e.g. "don't
  commit formatting-only files") but the lesson is about *how* to do it reliably
  (e.g. "`git diff -w` misses trailing commas"). Both need separate rules.
- **Narrow vs broad**: the specific instance was captured (e.g. "link RFC
  references to Confluence") but the general principle was not (e.g. "protect
  any non-obvious design choice with an inline rationale comment").
- **Symptom vs root cause**: a correction was made (e.g. "restore Dispatchers.IO")
  but the preventive measure was not captured (e.g. "add inline comments to
  prevent future removal of intentional design choices").

When in doubt, write the candidate lesson and run it through Step 3's
qualification gate rather than skipping it at extraction time.

## Step 1.5: Ralphex Execution Log Analysis (when available)

When `.ralphex/progress/` exists in the current project directory:

1. Read the 5 most recent `*.txt` files from `.ralphex/progress/` (by modification time).
2. For each log, extract recurring patterns:
   - **Rate-limit hits**: phase where the limit was hit (task/review/automation), frequency, reset window noted in the log.
   - **Review-phase warnings**: `first review pass did not complete cleanly` (non-fatal; flag if frequent).
   - **Already-done detection**: agent found work pre-completed in a prior commit; note if it caused repeated plan runs.
   - **Environment/tool gaps**: tool not found inside container (Maven, Python, etc.) during a phase that assumed it was available.
   - **Automated review loop failures**: external review parse or exit errors.
3. Classify each extracted pattern using the same Step 1 categories (human guidance, module knowledge, LLM rule, or temporary).
4. Feed classified patterns into the placement workflow (Steps 2–6) alongside lessons from communication.

**Specific placement guidance for common patterns:**
- Frequent rate-limit hits → resolved best-practices path (`docs/maintenance/best-practices.md` after migration; legacy `docs/BEST_PRACTICES.md` only when exploration confirms it still exists) or cross-project shared docs (from facts `shared_docs_dir`): plan size guidelines, recommended run windows.
- Container tool gaps → project `AGENTS.md` / `CLAUDE.md`: document which tools are available in which execution phase.
- Automated review loop failures → note disabling the external review loop in project or user-level docs when applicable.
- Non-fatal review warnings → no action needed unless they occur in every run; if so, note as known pattern in project docs.

## Step 1.6: Internet Research Capture

When research is conducted via web search or other external sources:

**Always capture findings to dedicated documentation:**
- Create or update canonical docs in `docs/` with numbered chapters/clauses
- Use descriptive filenames (e.g., `pdf_generation_guidelines.md`, not `research.md`)
- Include comparison tables, code examples, and source links
- Reference these docs from instruction files (e.g., `see pdf_generation_guidelines.md #1`)

**Format for research docs:**
- Start with Purpose section explaining what the doc covers
- Use numbered chapters (## 1, ## 2) and clauses (### 1.1, ### 1.2)
- Include "Quick Reference" or comparison tables when applicable
- Add Sources section at the end with URLs and dates

**LLM examples vs canonical docs:**
- Canonical docs = technical facts, best practices, comparisons (home per `.ai-playbook/facts.md` TOML and project guidelines)
- LLM examples / playbooks = reasoning patterns, anti-patterns (resolve `caller_catalog`, `{tmp_dir}`, or project-documented example path; do not assume `docs/examples/`)
- Examples file should reference main doc, not duplicate it

**When to create new research docs:**
- After web search for best practices, technical comparisons, tool selection
- When user asks for research on a topic
- When the same questions recur across sessions
- Before making technical decisions with alternatives

## Step 1.7: Proper-Noun Justification Review (required before any lesson is written)

This gate is the second layer of defense after the Step 1.2 generalization pass (item 1c). Where 1.2 prevents identifiers from entering the draft, this gate catches any that slipped through by re-reading the *already drafted* text and forcing a justification per identifier. It is NOT a checklist of known-bad tokens  -  such lists cannot catch the next employer's service names, ticket prefixes, or the bare company name (the leaks that motivated this gate all bypassed enumeration-based scans). It is a per-identifier judgment review.

**Why this matters:** Lessons land in corpora that may be public (this playbook is a public repo; project corpora can be synced, forked, or pasted into tickets/PRs). A lesson's value is the generalized rule; employer fingerprints add zero rule value and identify the employer, the team, the customer base, and sometimes individuals.

**The review (run on the drafted text before each Write/Edit of a lesson):**

1. **Inventory every identifier** in the draft. Walk the text and list each: service/module name, company/product name, ticket prefix or ID, branch/plan/PR slug, person name, customer/market list or country-code list, internal hostname/URL/wiki link, exact count, and date.
2. **For each, run the load-bearing test:** "If I replace this with a generic role or category, does the rule lose any enforceable meaning?" Examples of replacement: a service name → "the target service"; a company name → "the company"; a ticket ID → drop it; a country list → "the new markets"; a person → "a reviewer" / "the author"; a wiki URL → "an internal wiki page"; an exact incidental count → "many". If the rule is unchanged, the identifier was fingerprint  -  redact it. If removing it genuinely weakens the rule, keep it but flag it for step 4.
3. **Identifier-class awareness (not a closed list  -  a shape guide):** the classes that most often leak because they *feel* like legitimate context, but almost never are:
   - Service/product/company names and their prefixed slugs (`<employer>-<product>-service`)
   - Ticket-system prefixes and IDs (`PROJ-123`, `<EMPLOYER>-456`)  -  the prefix alone identifies the employer's tracker
   - Customer/market enumerations (country codes, region lists)  -  these fingerprint the customer base
   - Person names, handles, and GitHub logins
   - Internal hostnames, domains, and wiki/Confluence URLs (even with the org redacted, a real space key or page path can identify)
   - Exact counts and dates tied to a specific private run (keep only when the count/date IS the rule, e.g. a byte budget)
4. **Backstop  -  deny-pattern cross-check:** after the review, run the repo's hygiene deny-pattern file (`public_hygiene_patterns_file` in facts) against the draft. Treat any hit as a definite redact. This catches identifier classes the judgment review might still rationalize away. Note: the deny-pattern file is itself an incomplete enumeration; the judgment review in steps 1-2 is the primary defense, not the pattern file.
5. **Escalate true load-bearing cases:** if a sensitive identifier genuinely cannot be removed without gutting the rule (rare), escalate to the user before writing  -  present the rule with and without the identifier and let the user decide. Do NOT silently publish a load-bearing private identifier.
6. **Residual-domain test (run after redaction).** After steps 1-5 have redacted identifiers, run the residual-domain test: does the rule **still require a specific application domain** (tax reporting, capital-gains calculation, FIFO lot matching, batch-row aggregation) to be meaningful? If yes  -  even with every proper noun redacted  -  the lesson is **fork (4) project-specific**, not fork (2) stack guidelines and not fork (3) UL. A rule like "post-aggregation validation must run after all groups are accumulated, not per-row" survives identifier redaction yet still assumes batch-row processing with mid-accumulation state, so it is project-specific. Route it to the incident repo's project corpus (`docs/maintenance/development_lessons.md`), not the UL corpus and not `jvm_guidelines.md`. If the residual test says **no** domain dependence but the rule only applies inside one language or JVM/Spring/Python ecosystem, that is fork **(2)** shared language/JVM guidelines, **not** fork (4). Do not use "framework semantics" alone as proof of project scope when the framework is the shared stack (Spring, Reactor, Mockito). Step 1.2 item 3b's incident-repo-vs-cwd pre-check is the high-recall first gate; this residual-domain test plus Step 1.2 item 4b stack-portability is the second-layer reinforcement.

**Keep without question:** public playbook artifacts the rule operates on (the done landing sweep, `check-no-em-dash.sh`, `ruff`)  -  those are this repo's own content, not employer context. The generalized principle, shape trigger, rule steps, and cross-references to other public lessons/docs are likewise kept in full.

**Self-application:** If a lesson is later found to have leaked a private identifier, that is a learn-skill output defect. Fix the lesson, then ask which layer failed: did Step 1.2 item 1c not prompt the interrogation (root cause = generalization), or did the agent skip/rationationalize the Step 1.7 review (root cause = review discipline)? Strengthen the failed layer; do not just add the new token to a list.

## Step 1.8: Skill-usage issue capture

While classifying session findings (Step 1), also identify skill-usage issues: gate failures rooted in skill or script bugs, wrong or ambiguous skill instructions, missing runtime deployments, trigger failures. Classify an issue as a skills-corpus defect only when the fault traces to a skill's instructions, a bundled script, a gate validator, or a missing or wrong runtime deployment; consumer-project code bugs are out of scope (they belong to the project's own workflow).

**Backlog home (per issue family):** issues sharing the same root area, the same skill, and the same step form one family. For each family, resolve the skills repo from `skills_repo_path` (user facts; runtime symlink equivalent) and its resolved backlog home (`backlog_dir` from the skills repo's `.ai-playbook/facts.md` TOML; fallback `docs/history/backlog/`).

**Dedupe before create:** survey open items (`Status: open`, top level of the backlog home, excluding the completed and deferred subdirectories) for an existing item on the same skill and step; when found, append the new witness details there and re-affirm its priority instead of creating a duplicate. Immediately before creating a new item, re-survey the family (the directory listing can race a parallel session's create) and fold into a match that appeared instead of creating a duplicate.

**New item files:** follow `YYYY-MM-DD-<slug>.md` with `Status: open` and `Priority: high` (the corpus's top priority value, which routes the maintenance loop's authoring lane). Required contents:
- which skill and step (file path plus step number)
- observed versus expected behavior
- trimmed reproduction evidence with secrets, usernames, org domains, project names, and ticket prefixes scrubbed
- environment context (runtime, date, vendored copy versus repo copy)
- suspected root area
- the `Class:` line per receiving-review's Backlog capture (fix-class or fence-class), so the incident class is decided at filing time

Follow receiving-review's "Backlog capture for valid findings not fixed in scope" for item shape, including its `Origin class:` provenance line, and apply the landing sweep's sensitive-data-scan gate discipline and learn Step 1.7's proper-noun review to the drafted item text before writing it. Phrase everything in skill terms so the item reads correctly without knowing which project the session ran in.

**Commit rule:** stage and commit learn-authored skills-repo artifacts by explicit path (the backlog item files, skill-file edits from lessons, and learn-authored sibling catalog edits such as the skills repo's README.md row updates and projects/.ai-playbook/ entries) with a descriptive message; never a directory-wide add. Before committing, run the public hygiene scan and the em-dash scan over the drafted item text and the changed skill files; fix hits before staging, or report per the failure semantics below. Before staging each non-backlog path, verify the working-tree delta for that path is this session's own edit (review the path's diff); on foreign or unrecognizable hunks, skip staging that path and report it per the failure semantics (done Step 4's ask-first fallback carries the skipped path). Retry once when the commit fails because another process holds the git index lock file (retry after the lock clears; delete nothing) before reporting. After each successful commit, print `committed: <sha> <subject>` exactly (one line per commit, in commit order); the boundary's `task_boundary:` manifest row consumes these receipts at intermediate boundaries, and the done run's owned-commits ledger consumes them at the final closeout.

**Failure semantics:** capture and the commit must not block learn or the enclosing boundary; on failure, report the failure as a manual follow-up in the learn run's output (plus a one-line issue summary where the failure has one); durability rides the run's session logs, which the boundary's record mirror copies to the primary checkout at intermediate boundaries (learn runs without an intermediate boundary, the final closeout, standalone, and harvest invocations, rely on the session logs directly).

**Skill issues versus lessons:** a skill issue may also yield a lesson when it generalizes; the backlog item is the fix-tracking artifact, not a lesson replacement. A session with no skill issues creates no backlog items and reports nothing new.

## Step 1.9: Project issue backlog capture

While classifying session findings (Step 1), also identify project issues worth fixing outside the current task's scope: defects, gaps, and follow-ups the session witnessed but did not own. Step 1.8 owns skills-corpus defects; this step owns the project issues outside that home. Issues sharing the same root area, surface, and step form one family; a session with no project issues creates no rows and reports nothing new.

**Routing (per family):** each row routes to the related project's repository: the repository whose subject code, documentation, or module paths the issue is about, wherever the session runs. When that project is present in the current worktree (including when it is the current run checkout itself), the row lands in that checkout's resolved backlog directory (`backlog_dir` from that checkout's `.ai-playbook/facts.md`; fallback `docs/history/backlog/`); otherwise learn files the row on the current branch of the corresponding project's own checkout, in its resolved backlog directory. When that checkout cannot be resolved on disk, report the family as a manual follow-up in the learn output: an explicit non-blocking drop, never a silent loss. Dedupe runs against the destination home, never the current one.

**Dedupe before create:** apply Step 1.8's dedupe discipline against the destination home: survey its open items (`Status: open`, top level of the backlog home, excluding the completed and deferred subdirectories) for an existing item in the family; on a match, append the new witness details there and re-affirm its priority instead of creating a duplicate, and re-survey immediately before creating (a parallel session's create can land between survey and write).

**New item files:** follow `YYYY-MM-DD-<slug>.md` with `Status: open` and a priority value (the destination corpus's top priority value when the issue blocks consumer runs). Follow receiving-review's "Backlog capture for valid findings not fixed in scope" for the item shape, including its `Class:` and `Origin class:` lines, phrased so the row reads correctly inside the related project's own corpus.

**Hygiene before write:** apply the Step 1.7 proper-noun review to the drafted row text, then run the public hygiene scan and the em-dash scan over it, plus the landing sweep's sensitive-data-scan gate discipline Step 1.8 applies to its items (an off-tree row crosses the repository boundary that gate polices and never passes this repository's landing sweep); fix hits before writing, never after.

**Commit rule (off-tree rows):** a row filed outside the current checkout is committed at create time in its destination checkout by explicit path per Step 1.8's commit discipline (staging, hygiene-before-stage, index-lock retry, the `committed:` receipt line); never leave the row untracked residue. Adjudicate the destination checkout's state before the commit: on a detached HEAD, an unresolved branch, or unowned staged or dirty entries in its index, report the family as a manual follow-up instead of committing (the same shape as the direct-commit class's closeout-compatibility precondition). Report each off-tree receipt in the learn output so the enclosing boundary's `task_boundary:` manifest row records the sha.

**Investigate invocation:** when this step created or updated rows, invoke the `investigate` skill anchored on them within the same learn run, its own contract applying unchanged (survey, routing, entry emission, entry commit). For off-tree rows, invoke it from the destination checkout with the row anchored there, so the entry and its commit land in that project's own logs; foreign-data redaction applies to anything carried back.

**Failure semantics:** capture and the investigate invocation never block the enclosing boundary; on failure, report the failure as a manual follow-up in the learn run's output (plus a one-line issue summary where the failure has one); durability rides the run's session logs, which the boundary's record mirror copies to the primary checkout at intermediate boundaries (learn runs without an intermediate boundary, the final closeout, standalone, and harvest invocations, rely on the session logs directly).
