# Agent Workflow Guidelines — Language-Agnostic

Canonical reference for generic agent workflow patterns observed across all projects
(work and personal). Instruction files reference numbered clauses here.

Some section numbers appear out of numeric order (historical inserts). Prefer section titles over numbers when a cross-reference might be ambiguous.

## 1. Multi-Direction Aggregation Testing

When implementing aggregation or grouping logic that processes records with different
subtypes (in/out, send/receive, credit/debit, buy/sell):

1.1. Write explicit test cases for EACH subtype BEFORE implementing.
Do not assume the aggregation logic is symmetric.

1.2. One direction may produce a single output from multiple inputs, while the reverse
produces multiple outputs from a single input. The aggregation code path is often
different for each direction.

1.3. When fixing an aggregation bug found in one direction, immediately add a test
for the opposite direction before touching the code. The fix is likely to regress it.

## 2. Review Agent False-Positive Protocol

When an automated review agent (quality, security, or requirements checker) reports
a critical or high-severity finding:

2.1. Run the relevant test or write a targeted reproduction BEFORE reading the code.
If the test passes, the finding is likely a false positive.

2.2. Do not spend time tracing code paths to verify a finding that a test run can
confirm or deny in seconds. Test-first verification is the cheapest filter.

2.3. Common false-positive patterns: claims of unreachable code in multi-branch
conditionals, claims of data not flowing correctly when tests assert the output,
claims of missing validation when upstream code already guards it.

2.4. Document confirmed false positives briefly in the review log so future review
iterations don't re-report the same non-issue.

## 3. Field Semantics — Prevent Role Confusion

When a data model has two fields with similar but distinct purposes
(e.g., one for matching and one for audit trail):

3.1. Document the distinction in a single canonical location (module docstring,
domain doc, or field-level KDoc/JSDoc). Do not scatter the semantics across
multiple files.

3.2. Never use one field to gate logic that belongs to the other, even if it
"simplifies" the code. The shortcut will be caught by review and require multiple
fix iterations.

3.3. When both fields carry dates, ensure the temporal ordering constraint is
explicit (e.g., `serviceStartDate <= validFrom`) and documented at the definition
site. Validate it in an init block or constructor when the language allows.

3.4. When renaming or repurposing a field, update every doc that defines its
semantics in the same commit — not just the code. Out-of-sync field semantics
between code and docs is worse than no docs at all.

## 4. Post-Refactoring Cleanup

After any code extraction, module split, or significant refactoring:

4.1. Run unused-import detection on the source module before committing.
Python: `ruff check <source> --select=F401,F811`. Kotlin: IDE inspection or
`./gradlew detektMain`. Java: IDE "unused declaration" inspection.

4.2. Search for duplicate function/method definitions in the source file.
Partial extraction often leaves the original alongside the import.

4.3. Run the full test suite after extraction, not just the new module's tests.
Import paths may break in distant consumers that aren't in the new module's
test scope.

## 5. Gitignored Docs — Code Comment References

When design docs (RFCs, plans) are gitignored and only live on the author's
machine (e.g. under `docs/history/feature-notes/`, `docs/history/plans/`, or legacy `docs/rfcs/` / `docs/plans/` before migration):

5.1. Code comments that reference design rationale must link to the shared
location (Confluence page URL, shared wiki, etc.), not the local file path.
Other team members and reviewers cannot see gitignored files.

5.2. When production code implements a constraint documented in an RFC with
explicit identifiers (e.g. §C4, §Rule 9), add a concise single-line inline
comment stating the rationale and linking to the shared RFC. This prevents
future contributors or agents from removing intentional design choices that
satisfy documented architectural constraints.

## 6. Formatting-Only File Detection in Branch Diffs

When cleaning up a branch diff to remove formatting-only files before a PR:

6.1. `git diff -w` (ignore whitespace) is insufficient. It misses ktlint and
auto-formatter changes that are semantically identical but structurally
different: trailing commas added/removed, multi-line ↔ single-line expression
wraps, import reordering, `when` block re-indentation, method chain splitting,
empty body removal (`{ }` → single-line), semicolon addition/removal, and
AAA scaffold comment removal (`// Arrange:`, `// Act:`, `// Assert:`).

6.2. The only reliable method is to read the full `git diff -- <file>` for
every changed file and classify each hunk manually. A file is formatting-only
when every hunk changes only tokens' arrangement, not their identity or count
(with the exception of trailing commas and semicolons, which are cosmetic).

6.3. Batch the analysis: first use `git diff -w` to find the obvious
whitespace-only files (zero `-w` diff), then inspect the remaining files'
full diffs for the patterns in 6.1. Do not assume a file with a small
`-w` diff has real changes — it may be entirely trailing commas.

## 7. Protect Non-Obvious Design Choices with Inline Comments

When code makes a non-obvious technical choice driven by an architectural
constraint (dispatcher selection, threading model, algorithm constant,
concurrency strategy):

7.1. Add a concise inline comment explaining *why* the choice was made, not
*what* the code does. Without this, future contributors or LLM agents will
"simplify" the code by removing the seemingly unnecessary complexity.

7.2. Include a link to the shared design document (Confluence, wiki) so the
rationale is verifiable. A comment that says "required for performance" without
a traceable source will eventually be questioned and removed anyway.

7.3. This is especially critical for choices that look like they could be
simplified but exist due to framework constraints (e.g. blocking I/O requiring
a specific dispatcher, ordering constraints in async pipelines, defensive
duplication of safety mechanisms across architectural layers).

## 8. Scope Discipline — No "While I'm Here" Changes

When implementing a task, do not make opportunistic improvements to files that
are not directly required by the current task, even if the improvements are
genuinely valuable.

8.1. Before modifying any file, verify it is in scope for the task. If a file
is not referenced in the task description, plan, or ticket, do not touch it.

8.2. Opportunistic improvements (adding try-catch wrappers, changing log
formats, reordering method calls, extracting constants) in unrelated files
create review noise, risk accidental behavioral changes, and trigger
unnecessary Copilot/reviewer comments that consume the author's time.

8.3. If you spot a genuine improvement in an unrelated file, note it for a
separate PR or follow-up ticket — do not bundle it into the current change.

8.4. Scope discipline applies within in-scope files too. When a file is in
scope, add only what was explicitly requested — do not add adjacent settings,
properties, or cleanup that wasn't asked for (for example, adding extra logging
rules to a config file because a sibling env file has them). Extra additions
inside an in-scope file are still scope creep.

## 9. Docker Tooling — Prefer Host Mounts Over Baked-in Scripts

When a Docker-wrapped tool (e.g. ralphex) needs agent wrapper scripts or config
that changes independently of the tool itself:

9.1. Symlink the entire scripts directory from the source repo into the tool's
config directory on the host (e.g. `~/.config/ralphex/scripts` → ralphex repo).
The Docker wrapper auto-mounts the config directory into the container. This
avoids image rebuilds on every script change — just `git pull` in the source repo.

9.2. Symlink the entire folder, not individual scripts. The active agent (copilot,
codex, gemini) is selected via config and may change later. Hardcoding to one
agent's script creates unnecessary image rebuilds when switching.

9.3. Config paths inside the container must use container-internal absolute paths
(e.g. `/home/app/.config/ralphex/scripts/...`), NOT `~`-prefixed paths. The Go
binary does not expand tilde — `~` is treated literally and the command is not
found.

9.4. When updating Docker images after a base image pull, cached layers may
reference a non-existent parent snapshot. Run `docker builder prune` before
rebuilding, or use `--no-cache` to avoid stale snapshot errors.

## 10. Out-of-Scope Revert: Verify API Dependencies First

Before reverting a file classified as out-of-scope to a prior branch baseline:

10.1. Run `git diff <base>..HEAD -- <file>` and list every changed function/method
signature, parameter name, or property name in that file.

10.2. Search in-scope files for callers of each changed API. If any in-scope file
calls an API that was changed in the candidate file, the candidate is actually
in-scope — its change was required by in-scope code. Do NOT revert it.

10.3. A compile error immediately after reverting is hard evidence that 10.2 was
skipped. The correct fix is to un-revert the file (restore to HEAD state) and move
it from out-of-scope to in-scope in the plan's Review Scope section with a one-line
reason.

10.4. Cosmetic or formatting changes in a file that also contains a required API
change travel with that API change — they are not a separate justification for
reverting.

## 11. Failing Tests Are Always the Current Branch's Responsibility

There is no such thing as "pre-existing" or "unrelated infra integration test"
failures. If tests fail on the current branch, they must be fixed before the
work is considered complete.

11.1. A test that fails on the current branch is the current branch's
responsibility regardless of whether the branch introduced the failure
or inherited it from an earlier commit.

11.2. Do not dismiss failures with labels like "pre-existing", "flaky",
"infrastructure-only", or "unrelated". Each label is a deferral that will
eventually block merging or surface as a production incident.

11.3. If a test was already failing before the current change, the correct
action is still to fix it (or raise a separate ticket and fix it on this
branch) — not to declare it out of scope.

11.4. The only exception is a test that is explicitly annotated and tracked
as a known skip (e.g. `@Disabled` with a linked ticket). If no such
annotation exists, the test must pass before merge.

## 12. Verify Test Execution Count After Adding @Test Methods

After adding one or more `@Test` methods to a test class, confirm the actual
number of tests executed by the runner matches the expected count.

12.1. If the runner reports fewer tests than expected, a method is being
silently skipped. Common causes: expression body with non-Unit return type
(see kotlin_guidelines.md #1), accidentally returning a lambda instead of
executing it (`= { ... }` vs `{ ... }`), or a broad catch block swallowing
an `IllegalArgumentException` thrown during test setup.

12.2. Use the runner's test-count output to verify. A silently skipped test
produces zero failures — the count mismatch is the only signal.

12.3. Apply this check whenever a test class is first created or when test
methods are refactored. Count mismatches are easy to miss in code review
because nothing appears broken.

## 13. Portable Shell Script Locking

Shell scripts intended for cross-agent use (Claude Code, Codex, etc.) must not
depend on `flock` — it is not installed on macOS by default and the failure is
silent when combined with `set -euo pipefail` and `|| exit 0` fallbacks.

13.1. Use `mkdir`-based locking instead: `until mkdir "$LOCK_DIR" 2>/dev/null;
do sleep 0.1; done` with a `trap 'rmdir "$LOCK_DIR" 2>/dev/null' EXIT` cleanup.

13.2. When a `flock` call silently exits via `|| exit 0`, the entire script
terminates before reaching any logic. The only symptom is that the script's
side effects never happen — no error, no output.

## 14. Agent-Specific Hook Protocol Wrappers

Different agents have different hook I/O protocols. Codex PostToolUse hooks
ignore plain text on stdout — they require JSON with `additionalContext` or
`systemMessage` fields. Claude Code hooks accept plain text on stdout.

14.1. When a shared script outputs plain text (e.g. a counter/nudge script),
create a thin agent-specific wrapper rather than modifying the shared script.
The wrapper handles protocol translation (plain text → JSON) and delegates to
the shared script.

14.2. Keep the shared script agent-agnostic. Agent-specific protocol concerns
belong in wrappers, not in the shared logic.

## 15. Out-of-Scope Findings — Document as Separate Ticket, Never Fix In-Place

**Scope: projects with peer review and shared codebases (e.g. company repos). Not
applicable to solo pet projects where fixing-as-you-go is fine.**

This rule applies at every stage: plan authoring, implementation, and code review.
Any finding — bug, security concern, quality issue, or improvement — that is not
part of the current task must be documented as a separate feature or bug-fix request,
not fixed on the current branch. This includes findings discovered while reading
code that is not being changed.

Rationale: fixing unrelated legacy code on a feature branch introduces untested
production risk (the fix may not be covered by existing tests), inflates PR scope,
and makes review harder — regardless of how legitimate the underlying concern is.

15.1. Do not fix the issue in-place on the current branch, even if the file is
listed as in scope. A file being in scope means the named methods are touchable —
it does not grant permission to modify any other method in that file.

15.2. Document the finding as a separate bug or feature ticket. Include the file,
the method or area, a one-line description, and where it was spotted. Decline any
review finding on out-of-scope code with "out of scope for this PR — tracked as
[ticket/note]".

15.3. When authoring a plan that partially touches a large file, explicitly name
the methods being modified and add a freeze note: "All other methods in this file
are frozen — reject any review finding that touches them."

15.4. Exception — trivially correct one-liner with no test surface: a genuinely
absent fix (e.g. a missing `log.error` in an exception handler that is clearly wrong)
may be kept on the branch if: (a) it is a single statement, (b) no new test is
needed to validate it, and (c) the user explicitly approves keeping it. This exception
is narrow — it does not apply to refactors, style changes, or anything requiring a
new test.

## 16. Merge-Time Compile Errors from Divergent Refactoring

When a squash merge or rebase produces a compilation error in code that was
moved from one class to another (e.g. a method moved from `EventBusImpl` to
`TriggerDispatcher`), the error may be a merge artifact rather than a bug on
either source branch.

16.1. Before propagating a merge-time fix to a source branch, verify the
source branch compiles independently. Check the branch's version of the
involved types (DTOs, interfaces, sealed classes) with
`git show <branch>:<file>` — do not switch branches to investigate; that
disrupts the merge state.

16.2. A compile error that appears only after merging is a merge artifact
when: (a) branch A moved code that constructs or uses a type, and (b) branch
B independently added required fields/parameters to that type. The fix
belongs only in the merged result — neither source branch has a bug.

16.3. To confirm: if the source branch's DTO lacks the fields that are
missing at the call site, the source branch compiled cleanly against its
own DTO and needs no fix. The merged branch needs the fix because it now
has the expanded DTO from the other branch.

## 17. Reading CI Test Output — Application Errors vs Test Failures

When reviewing CI (Jenkins/GitHub Actions) test run output:

17.1. Application-level `ERROR` log lines (e.g. `[com.example.Service:71]: input is invalid`) in test output are NOT test failures. They are emitted by the service's own logger while exercising invalid-input rejection paths — exactly as designed.

17.2. Actual test failures are reported by JUnit as `Failures: N` or `Errors: N` in the summary: `Tests run: N, Failures: N, Errors: N, Skipped: N`. A summary with `Failures: 0, Errors: 0` means all tests passed regardless of how many ERROR lines appear in the log.

17.3. When a user asks "why did CI fail with these?" for a set of test output, check the `Tests run` summary line first. If `Failures: 0, Errors: 0`, the CI failure was caused by something else (another test class, compilation error, downstream step) — not the tests shown.

## 18. Skill Directory Sync — Include All Files, Not Just SKILL.md

When **creating** a new skill, add `LICENSE.txt` before the first commit — copy MIT `LICENSE.txt` from an existing skill (for example `agents/skills/plans/LICENSE.txt`). Personal email belongs only in the LICENSE copyright line.

When syncing or mirroring a skill directory between repos or to a home directory registry (`~/.agents/skills/`, `~/.claude/skills/`), copy every file in the skill folder — `SKILL.md`, `LICENSE.txt`, asset files, reference docs, and scripts. Copying only `SKILL.md` silently drops licensing metadata and support assets.

```bash
# Correct: copy entire directory
cp -r "$SRC/agents/skills/$skill/." "$DST/agents/skills/$skill/"

# Wrong: copy only SKILL.md
cp "$SRC/agents/skills/$skill/SKILL.md" "$DST/agents/skills/$skill/SKILL.md"
```

After syncing, verify with: `diff -r "$SRC/agents/skills/$skill/" "$DST/agents/skills/$skill/"`

## 19. Claude Skills Directory — Use Symlink, Not a Copy

In any skill registry repo, `claude/skills/` must be a symlink to `../agents/skills/`, not a separate directory with duplicated files. A real directory creates drift: skills get updated in one location but not the other.

```bash
# Correct setup
rm -rf claude/skills
ln -s ../agents/skills claude/skills

# Wrong: maintaining a separate real directory
cp -r agents/skills/ claude/skills/   # creates a copy that drifts
```

In the skills repository (`skills_repo_path` in `~/.ai-playbook/facts.md`), `claude/skills` must symlink to `../agents/skills`.

## 20. Skill and Doc Examples — Always Use Placeholder Values, Never Real Identifiers

When writing examples in skill files, documentation, or command specs, use generic placeholder values instead of real internal identifiers. Real identifiers (ticket numbers, account IDs, internal URLs) embedded in examples leak internal project state and require manual cleanup later.

- Jira tickets: use `PROJ-XXXXX` or `TEAM-XXXXX`, never a real ticket number
- AWS account IDs: use `<AWS_ACCOUNT_ID>`, never a numeric account ID
- Internal Atlassian URLs: use `https://your-org.atlassian.net/...` as a template
- Internal IPs: use `<BROKER_IP>` or `192.0.2.x` (documentation range), never production/staging IPs

Apply this rule to the source repo as well — do not wait until the downstream sync to replace real identifiers.

This rule applies to negative examples too: do not illustrate what a real identifier looks like by showing one. The placeholder format is self-explanatory without a concrete bad example.

## 21. Configuration File Changes — Only When Explicitly Requested

Do not modify configuration files (`.gitignore`, `package.json`, `pom.xml`, CI configs, etc.) unless the user explicitly requests it. Inferring "this should also be gitignored" or "this dependency should be updated" from context and acting on it without prompting causes unexpected side-effects and makes changes harder to review.

When a configuration change seems necessary as a side-effect of another task, ask first rather than applying it silently.

## 22. PR Chain Awareness — Check Downstream Branches Before Flagging Missing Changes

When reviewing a PR in a stacked/chained PR series (multiple open PRs where each builds on the previous), a change that appears missing from the current PR may already be addressed in a downstream branch.

22.1. Before posting a review comment about missing tests, missing logic, or incomplete implementation, check whether the change exists in a later PR in the chain. If it does, the comment is unnecessary and creates noise.

22.2. To check: inspect open PRs targeting branches that are downstream of the current PR's head. If any downstream PR contains the referenced change, skip the comment entirely.

22.3. When a comment about a missing change has already been posted and the change is found downstream, remove the comment rather than leaving it open — open comments on stacked PRs that are addressed in a later PR mislead reviewers.

## 23. Rollback Ambiguity — Clarify Before Rolling Back a Pushed Commit

When asked to "rollback", "undo", or "revert" a pushed commit, clarify the intent before acting — the two approaches have different history implications:

- `git revert` (safe default): creates a new commit that undoes the change. Preserves history. Appropriate for shared branches where force-pushing is restricted.
- `git reset --hard <sha> && git push --force-with-lease` (clean history): removes the commit entirely. Appropriate when the user explicitly wants a clean history and force-pushing is acceptable.

23.1. If the user says "rollback" without specifying approach, ask: "Should I use `git revert` (adds a revert commit, preserves history) or `git reset --hard` + force push (removes the commit entirely)?"

23.2. Do not default to `git revert` when the user's intent is clearly to clean history. A revert of a recently pushed mistake adds unnecessary noise to the branch history.

## 24. Context Sharing Is Not an Action Directive

When a user shares context without an explicit action instruction — PR comments, review notes, error logs, issue descriptions, or similar — do not assume the task is to implement a fix or make changes.

24.1. Sharing context is a review/discussion act until the user explicitly says to implement, fix, apply, or create something. Ask about the intended working mode before acting.

24.2. Common ambiguous patterns:
- "We got this review comment: …" — may mean "discuss it", "plan it", or "do it"; clarify.
- "The CI failed with: …" — may mean "explain it", "investigate it", or "fix it"; clarify.
- "The PR has a finding about: …" — may mean "is this valid?", "should we address it?", or "address it now"; clarify.

24.3. Ask once, concisely — not a multi-paragraph clarification. "Should I implement this or are we reviewing/discussing?" is enough.

## 25. Intent-Dependent Review Findings — Ask, Don't Prescribe

When a code review finding hinges on unstated design intent rather than clear incorrectness — for example, what a metric should count, what a state transition should allow, or what a timeout should cover — frame it as an open clarifying question instead of a directive correction.

25.1. Indicators that a finding is intent-dependent:
- The ticket says "add X" without specifying the semantics (e.g. "add metrics" without saying what to count).
- Both the current implementation and the suggested fix are reasonable depending on the goal.
- The artifact's own documentation (comment, name, description) hints at one interpretation but doesn't rule out the other.

25.2. Preferred framing: state the observation ("the metric fires after dispatch, so failures are not counted"), cite the documented intent ("the comment says 'entry point' which suggests counting all arrivals"), then ask ("should this metric count all attempts including failures, or only successful dispatches?"). Do not prescribe a fix when the answer depends on a design decision the author must make.

25.3. Before posting an intent-dependent finding, check the artifact's own description (metric comment, enum javadoc, constant name). If the description supports your interpretation, cite it. If the description is also ambiguous, say so explicitly in the question.

## 26. Read Telemetry Before Proposing Remediation

When diagnosing a system issue with metrics, logs, or dashboards available, read the actual evidence before proposing a remediation. Do not anchor on the first plausible hypothesis and present a fix as confirmed when the underlying data has not yet been inspected.

26.1. The failure mode this rule prevents: an early hypothesis (e.g. "pool too small, raise from 20 to 60") is written into a doc, ticket, or PR before any dashboard is opened. Later evidence flips the diagnosis (e.g. "pool is half-empty; the real cause is connection-creation latency"), forcing rewrites and undermining trust.

26.2. Discipline:
- Frame initial hypotheses explicitly as hypotheses, not as the diagnosis. Use phrasing like "candidate cause" or "to be confirmed".
- Before recommending a numeric change to a config value, surface the current metric reading for that value's effect (e.g. peak utilisation, max acquired, p99 latency).
- When the evidence flips a hypothesis, rewrite the artefact rather than appending a correction; future readers should not have to trace which version of the diagnosis is current.

26.3. Verify framework semantics before computing concurrency or capacity. A configuration knob's name often does not match its runtime effect (e.g. RocketMQ `consumeMessageBatchMaxSize` is the batch size delivered to the listener, not the parallelism — actual parallelism is `consumeThreadMax`). Read the listener implementation, not just the knob name, before arithmetic.

## 27. Separating Chronic Noise from Blocking Urgency

When a recurring error pattern is observed in production, separate "chronic background noise that retries catch" from "blocker that prevents the next change". Do not default to framing every error pattern as urgent or as a release blocker.

27.1. The failure mode this rule prevents: writing tickets that say "blocks safe rollout of X" when in fact X is unrelated and the existing retry/fallback path catches the failure. Overstating urgency wastes reviewer attention and creates artificial dependencies between unrelated work.

27.2. Tests to apply before claiming a fix is required for a downstream change:
- Does the failure pre-date the downstream change? If yes, the downstream change is not the cause.
- Does an existing retry/fallback mechanism catch the failure on first occurrence (RocketMQ `RECONSUME_LATER`, HTTP retry, idempotent re-publish)? If yes, the user-visible impact is limited to retries, not lost work.
- Does the downstream change increase the per-event resource footprint that drives the failure? If no, it does not amplify the issue.
- Is there a counter (e.g. permanently-dropped count, max-retries-exceeded count) that quantifies the user-visible impact? Use that, not the raw error rate, when arguing urgency.

27.3. When the above tests all pass, frame the work as "infra hygiene — fix opportunistically" rather than as a release blocker, and explicitly state that downstream changes are not blocked.

## 28. Do Not Add Unnecessary Coordination Steps

Do not add "confirm with team X" or "wait for approval from Y" acceptance criteria to tickets or PRs unless the change's effect actually requires that coordination. Adding coordination steps that the change does not warrant slows delivery without reducing risk.

28.1. The failure mode this rule prevents: a config or code change that does not alter peak resource usage, contract shape, or downstream-visible behaviour gets a "DBA must confirm capacity" or "SRE must approve" line. Reviewer and approver chains grow, but the underlying risk is unchanged.

28.2. Apply this test before adding a coordination step:
- Does the change move the peak load, peak resource count, or peak concurrency? If no, coordination based on peak capacity is not needed.
- Does the change alter an external contract (API, schema, message format)? If no, downstream consumer coordination is not needed.
- Does the change touch shared infrastructure that another team owns? If no, that team's approval is not needed.

28.3. If the change only shifts a baseline within previously-allowed peak (e.g. raising `min-idle` on a pool whose `max` is unchanged), the relevant capacity envelope is already approved; do not gate the change on re-approval.

## 29. Confirm Timezone Before Time-Correlating User-Shared Dashboards

When a user shares a dashboard screenshot, log excerpt, or timeline, confirm the timezone before correlating it to events with known timestamps (UTC stack traces, cron expressions, release windows). Local-time displays in Grafana, Kibana, and IDEs are common.

29.1. The failure mode this rule prevents: drawing a wrong correlation conclusion ("the screenshot doesn't show the incident window") because the dashboard is rendered in the user's local time but the incident timestamp is in UTC. The reverse error is also possible.

29.2. Discipline:
- When the user shares a screenshot whose time axis matters, ask once which timezone is displayed.
- When stating a correlation, include both representations explicitly (e.g. "08:11 UTC = 09:11 local CEST").
- When in doubt, prefer UTC for written analysis; convert to local only when addressing the user directly.

## 30. Verify Observability Artifact Inputs Before Authoring

When authoring a Grafana panel, Prometheus alert, or any observability artefact, verify that its inputs exist and have the expected shape before saving the artefact.

30.1. The failure mode this rule prevents: a new panel is added with a query against a metric that is not emitted, or a filter regex that does not match any label value (e.g. case mismatch). The panel renders empty in production and adds noise rather than signal.

30.2. Concrete checks:
- For a new metric query: confirm the metric appears in Prometheus today (`{__name__="<metric>"}` returns series) before adding the panel. If the metric requires app-side instrumentation that is not yet shipped, defer the panel and call out the instrumentation gap explicitly.
- For a regex filter against a label: read the actual label values in the running system. PromQL `=~` is case-sensitive; Micrometer often labels series with bean names (camelCase) rather than configured human-readable names. Test the regex against current label values before saving.
- When fixing an "empty panel" symptom, fix the underlying label/regex mismatch and document the actual label format inline in the dashboard's README so the next author does not repeat the mistake.

## 31. Verify Terminal State After Automation, Not Intermediate Confirmations

"Successfully triggered" is not "successfully applied". When invoking automation that spans multiple steps (UI button → API call → CI pipeline → git commit → reconciler sync → pod restart → config bind), verify the terminal observable state, not just the immediate response from the first step.

31.1. The failure mode this rule prevents: a tool returns HTTP 200 / `:white_check_mark: Successfully restarted` / similar success message at the API layer, but a downstream step (commit, deploy, restart, validation) silently no-ops or is reverted. The user-side experience looks fine while the actual state never changed. Subsequent debugging starts from a wrong premise ("we already restarted, so the issue must be elsewhere").

31.2. Discipline:
- Identify the terminal observable for the action: log content stops appearing, pod creation timestamp moves forward, metric value changes, file content updates.
- After the automation reports success, sample that observable before concluding the action took effect.
- If the user reports "it didn't work" after a successful trigger, treat the success message as advisory only and verify the terminal state from scratch.

## 32. GitOps Reconcilers Revert Imperative Changes

When a Kubernetes (or other declarative) resource is managed by a reconciler such as Argo CD, Flux, or similar (visible labels: `argocd.argoproj.io/instance`, `app.kubernetes.io/managed-by: Helm` paired with an ArgoCD Application, etc.), any imperative cluster mutation (`kubectl rollout restart`, `kubectl edit`, manual annotation) can be reverted on the next reconcile cycle. The reliable mechanism is to commit the change to the git source of truth so the reconciler propagates it.

32.1. The failure mode this rule prevents: a "restart didn't take" symptom is mistakenly attributed to the application (e.g. assumed startup failure) when in fact the reconciler scaled the new ReplicaSet down because the triggering annotation wasn't in git.

32.2. Diagnostic checks:
- Before troubleshooting a restart-that-didn't-restart, check the resource for reconciler-ownership labels.
- If the deployment is reconciler-managed, confirm the change reached git (commit log of the helm-values repo / kustomize overlay / etc.), not just the live cluster.
- Pod creation timestamps and reconciler "missing replicas" panels show the revert pattern: count briefly increases (new ReplicaSet started) then returns to baseline (reverted).

## 33. Follow the Project PR Template When Automation Depends on It

Many config-only repos gate CI behaviour on PR-template fields (a `[x]` checkbox in a "Restart Required?" section, machine-readable metadata `isRestartRequired: true`, region/service lists). Custom PR descriptions that bypass the template can silently disable that automation. When opening a PR against a repo with a configured template (`.github/pull_request_template.md` or visible default when the new-PR page loads), either use the template directly or, if a custom description is necessary for clarity, retain the template's machine-readable metadata block.

33.1. The failure mode this rule prevents: a custom PR description that reads well but omits `isRestartRequired: true`. The downstream pipeline silently sees the default (`false`) and skips the restart step. The PR merges, "nothing happens", and the discrepancy is invisible until someone notices the live state is stale.

33.2. Discipline:
- Before writing a custom PR description against an unfamiliar repo, read `.github/pull_request_template.md` (and any wiki/README about CI behaviour).
- Preserve template metadata blocks even when rewriting the human-readable sections.
- If the template's intent is unclear, search for the repo's wiki/runbook (see rule 34) for the pipeline that consumes those fields.

33.3. Squash-merge with a cleaned commit body is the second failure mode of the same rule. Many CI pipelines that read PR-template fields fetch them from the merge commit body, not from the PR body via API. When a user squash-merges and clears the body in the GitHub merge dialog, the metadata block disappears and the pipeline silently defaults to "no action". When opening a PR against a repo with PR-metadata-driven automation, warn the user explicitly at PR creation time AND if they signal they are about to merge: do not squash-merge with a cleaned commit message body. Either use a regular merge, or leave the body intact in the squash-merge dialog so the metadata survives.

## 34. Check Internal Runbooks Before Diagnosing Platform Tooling

When the user references an internal platform tool (autodeploy URL, custom Slack bot, deployment service, custom CI step), search for project-internal documentation (Confluence, repo wiki, README, runbook) describing its expected behaviour before running deep diagnostics or making assumptions. A 5-minute read of the runbook can settle questions that would otherwise take an hour of cluster probing or speculation.

34.1. The failure mode this rule prevents: developing an incorrect mental model of how an internal tool works ("the Slack bot must do `kubectl rollout restart` directly"), spending time gathering evidence to disprove it, and arriving at the same conclusion the runbook stated upfront.

34.2. Discipline:
- When the user names a tool, URL, or pipeline you have not seen documented, ask "is there a runbook / Confluence page / README for this?" before forming hypotheses.
- Read the page end-to-end, especially priority-order and default-value sections.
- When the runbook contradicts an earlier hypothesis, correct the hypothesis explicitly rather than quietly pivoting.

## 35. Do Not Raise Pure Formatting Nits In Design Review Threads

When drafting review feedback for a shared design doc, TDD, RFC, ticket, or Slack thread, do not raise purely cosmetic formatting issues unless the user explicitly asks for proofreading or polish.

35.1. The failure mode this rule prevents: review feedback includes a missing Markdown space, punctuation spacing, typo that does not affect comprehension, or similar low-value nit. This distracts from product, design, correctness, security, and implementation questions.

35.2. Apply this threshold before including a nit:
- If the issue changes meaning, creates ambiguity, breaks a code/config example, or could mislead implementers, include it.
- If the issue is only visual polish and the document remains understandable, omit it from the team-facing feedback.
- If tiny cleanups are useful to the user privately, mention them separately as optional polish, not as review comments to send to the team.

## 36. Commit Messages Must Describe Only Implemented Changes

A commit message must describe what the code actually does, not what a plan document says will be done in the future. When a squash merge includes an updated plan file alongside implemented changes, the commit message should describe only the implemented changes. A plan file being updated is a documentation change, not an implementation of the planned features.

36.1. Before writing the commit message for a squash merge, distinguish: which changes are working code/tests, and which are plan documents that describe future work. Only reference the working code in the message body.

## 37. Verify Branch Scope Before Committing PR Review Fixes

When implementing fixes for PR review comments, every change must belong to the scope of the PR's branch before it is committed there.

37.1. Before staging any file change, ask: "Does this file belong to this branch?" If a file lives in a folder that should go to a different branch (e.g., `individual/<name>/` while on a team feature branch), commit it to the correct branch separately instead.

37.2. The failure mode this rule prevents: a PR review batch includes comments on both `individual/` files and `department/` files. Committing all fixes together pollutes the PR with out-of-scope files, breaks branch isolation, and forces a soft-reset to untangle them.

37.3. In multi-scope repositories, establish which folders belong to which branches before starting a review fix session. Only then classify each review comment by branch scope.

## 38. Verify a Skill's Default Behavior Before Writing About It

Before writing any documentation, PR description, or explanation that describes what a skill or tool does by default, read the skill's `SKILL.md` (or the tool's README) to confirm the default output mode, trigger conditions, and opt-in flags.

38.1. Do not infer default behavior from memory, the skill's name, or partial context. Default behavior that diverges from expectations is usually the intentional design (e.g., "write locally first, post to PR only on explicit opt-in").

38.2. If no canonical source is readily available, note uncertainty inline rather than stating the behavior as fact.

## 39. Output Writing Style — No Em Dashes, Prefer Globish

When generating any text artifact (PR descriptions, READMEs, skill docs, commit messages, comments):

39.1. Do not use em dashes (—). Use a colon, a comma, a semicolon, a period, or rewrite the sentence. This applies to Jira issue descriptions and comments, Confluence pages, and any other content sent through MCP tools, not only files on disk.

39.2. Use plain, direct English (globish): short sentences, common words, active voice. Avoid complex punctuation or literary constructions. For vocabulary replacements and `## Terms` rules, see §45.

39.3. **Self-check before saving or sending.** Before writing a ticket/page/PR body or committing, scan the composed text for `—` and replace every occurrence. Treat this as a mandatory step when a skill composes an artifact (for example `jira-workflow`).

## 40. Named Tools and Skills Must Be Visually Listed, Not Only Inline

When writing documentation that describes a workflow involving named tools, skills, or components, make those names discoverable by listing them explicitly at the end of each section — not only embedded in prose sentences.

40.1. Use a labeled list (`Skills:`, `Tools:`, `Components:`) as the last item in each workflow section. Monospace inline mentions alone are not sufficient: they scatter names across sentences and make the tool inventory hard to scan.

40.2. The prose explains behaviour; the list names what to invoke. Both are required.

40.3. When the skill set covers multiple review modes (e.g. code review and design-document review), include a separate section for each mode with its own labeled skill list. Do not merge them into one block.

## 41. Markdown Tables — Escape Pipes in Cell Values

When a Markdown table cell contains a literal `|` (for example Grafana panel titles with dimension separators):

41.1. Escape pipes as `\|` inside the cell, or switch to a numbered/bulleted list when values are long or pipe-heavy.

41.2. Unescaped `|` breaks column alignment; the row renders as extra columns or truncated content.

## 42. User AGENTS Entrypoints vs Repository Paths

When documenting setup for Codex, Claude, or Copilot user instructions:

42.1. Agents load `<instructions_repo>/docs/AGENTS.md` through `~/.codex/AGENTS.md` or an `@` import in `~/.claude/CLAUDE.md`, not by opening the repo path during a session.

42.2. Put entrypoint verification commands (symlink checks, `test -f` on `~/.codex/AGENTS.md`) in `docs/AGENTS.md`. Keep runtime folder mapping and symlink recipes in `agent-runtime-layout.md` under `shared_docs_dir` (directory symlink to `instructions_repo/projects/.ai-playbook/`).

42.3. Keep user identity and machine paths in `~/.ai-playbook/facts.md` only. Do not place `facts.md` under `shared_docs_dir`; that directory is for shared, committable guidelines.

## 43. Shared Guidelines Repo Path Mirrors Runtime `.ai-playbook`

Cross-project coding and workflow guidelines belong in version control at `instructions_repo/projects/.ai-playbook/`, matching the runtime directory name under `~/Projects/.ai-playbook/`.

43.1. Do not use a different repo folder name (for example `docs/projects/`) when runtime `shared_docs_dir` is already `~/Projects/.ai-playbook/`.

43.2. Wire runtime with one directory symlink: `ln -sfn "<instructions_repo>/projects/.ai-playbook" ~/Projects/.ai-playbook` (see `agent-runtime-layout.md`).

## 44. Public Repository Push Hygiene

Before pushing to a public repository (especially vendored skills), verify both file content and commit history in the push range.

44.1. Never force-push without explicit user approval, even when correcting a mistaken push.

44.2. When asked to squash before push, squash only unpushed commits (`origin/<branch>..HEAD` via `git reset --soft origin/<branch>`). Do not rewrite the full repository history unless the user explicitly asks.

44.3. Audit commit subjects and bodies in the push range for `Co-authored-by:` trailers and employer or client brand names. Scan vendored skill files for the same patterns. Copyright lines in `LICENSE.txt` are exempt.

## 45. Plain Language for Human-Facing Artifacts

Applies to plans, RFCs, PR descriptions, BFF/API docs, Confluence pages, Slack drafts, and any other text meant for humans to read (not code comments or internal transport-layer notes).

45.1. **Default vocabulary:** use common English when it carries the same meaning as insider jargon. Short sentences, active voice. Complements §39 (globish); §45 adds actionable replacements and glossary rules.

45.2. **Prefer plain terms in human-facing docs** (use the right column unless the audience is transport/OpenAPI code). Examples in this table use generic placeholders per §20 — not real endpoints, fields, or domain nouns from one project.

| Avoid in plans, RFCs, PRs | Prefer |
|---|---|
| wire contract / wire format | **API contract**, **public API response shape**, **JSON request/response** |
| wire names / wire enums | **JSON field names**, **API enum values** |
| snapshot (alone) | **read result**, **GET response payload** — or name the endpoint |
| gate term (alone) | name the endpoint (e.g. `POST /v1/<resource>-checks`) or **validation API** |
| transport layer | **HTTP/API layer** (e.g. `app` module) |
| orchestration shell | **coordinates steps**; name what it calls |
| normalization-aware | **compare values after formatting them the same way** |
| enum-sourced message | **error text from a fixed enum**, not exception text |
| partial-empty | describe literally (e.g. `items: []`, `isHidden: true`) |
| INNER JOIN gap | **database join misses rows** when stored values do not match exactly |
| RED / GREEN (in Gist only) | OK in plan **tasks**; in Gist use **failing test first**, **make test pass** |

45.3. **Code vs docs split:** "wire format" and similar transport vocabulary are fine in `project-guidelines.md`, OpenAPI descriptions, and Java transport comments where the team already uses them. Do not use them in plan **Gist & Examples**, PR summaries, or BFF docs when a plain equivalent exists.

45.4. **`## Terms` section (required when needed):** add immediately after the document title (before the main body) when the doc uses **three or more** project-specific terms, acronyms, or jargon that a new reader might not know. Format:

```markdown
## Terms
| Term | Meaning |
|------|---------|
| ... | One-line plain English |
```

45.5. **First-use rule:** when a niche term must appear and a `## Terms` section is not warranted (one or two terms only), spell it out on first use: **"user read result (`GET /v1/users/{userId}`)"**.

45.6. **Shared dictionary:** recurring workspace terms belong in the ownership `dictionary.md` (company or personal-projects `.ai-playbook/`) or repo `docs/glossary.md` when present. Document-level `## Terms` tables are for one-off context; do not duplicate long glossary entries inline.

45.7. **Skill and instruction hooks:** writing-heavy skills (`plans`, `github-pr-workflow`, `rfc-design`, `review-confluence-doc`, `slack-message`) must reference this section. When `learn` captures a wording correction, add the replacement to the table in 45.2 (if universal) or the relevant `dictionary.md` / `docs/glossary.md`.

45.8. **Document results, not deliberation.** In long-lived artifacts (canonical docs, high-level task docs, issue trackers) record the decision and its current-state outcome, not the reasoning path that produced it (why alternatives were rejected, what was extracted/renamed/split from where, phrases like "former Slice 2", or transient caveats like "not exercised yet in the current state"). Keep rationale and alternatives in the single designated decisions/ADR doc; everywhere else state only the result. In an issue/ticket description, describe only that ticket's own scope; do not narrate adjacent or follow-up tickets, extraction history, or prioritization reasoning. State the split/mapping as a plain pointer when needed, not as a justification.

## 46. Maintain Workflow Invariants Until Explicitly Paused

When a workflow (plan review, TDD cycle, PR process) has an explicit exit condition
(e.g., "Repeat until Blockers=0 AND Medium=0"), the agent must:

46.1. Track whether the exit condition is met. Maintain this invariant as active
until it is satisfied.

46.2. NOT stop when only a formatting/content constraint is given (e.g., "TEXT ONLY",
"no tool calls", "respond in plain text"). Such constraints are output format
requirements, not pause signals.

46.3. Clarify with the user whether they want to continue or pause the workflow
when uncertain. State the workflow's current state and next step explicitly.

46.4. To pause, the user must say "pause", "stop", or give an equivalent explicit
instruction. A format constraint alone does not override a workflow's exit condition.

46.5. When uncertain: acknowledge the constraint, state the workflow invariant and
next step, and ask whether to proceed.

**Examples of correctly handling format constraints vs pause requests:**

| User says | Workflow state | Correct response |
|----------|----------------|------------------|
| "TEXT ONLY" | Review Round 2 has Medium=2, exit condition requires Medium=0 | Acknowledge, state "Round 2 has Medium=2, must continue to Round 3. Proceed with fixes?" |
| "pause" | Any state | Stop workflow, await explicit continuation signal |
| "no tool calls" | Review Round 2 has Medium=2 | Provide text summary of fixes needed, ask whether to apply them |

**Why this matters:** Multi-step workflows like plan review have quality gates
that must be satisfied. Stopping early due to a misinterpreted format constraint
produces incomplete output that fails downstream quality checks.

## 47. Shared Skill References in Generic Instructions

47.1. **Runtime edit path:** `~/.agents/skills/<skill>/SKILL.md`. When `~/.claude/skills` is symlinked to `~/.agents/skills`, both resolve to one tree — edit once; do not maintain duplicate sync rules.

47.2. **Commit/mirror target:** resolve the skills repository from `skills_repo_path` in `~/.ai-playbook/facts.md`, or deduce via `readlink -f ~/.agents/skills`. Do not hardcode local clone names or paths in generic skills or cross-project instruction files.

47.3. **Project repo instruction files:** defer shared skill maintenance with a one-liner (for example: follow self-maintenance rules in `~/.agents/skills/learn/SKILL.md`). Do not restate multi-path sync recipes or vendor-specific command copies.

47.4. **Migrated skills:** workflows moved to the shared registry (for example `learn`) are skill-only. Remove stale `.opencode/command/<skill>.md` references and local command copies when encountered.

## 48. Public Skill Examples and Local Hygiene Scans

48.1. **Neutral placeholders only** in committed skill and instruction files: use fictitious ticket keys (`PROJ-1234`), domains (`your-org.atlassian.net`), and feature slugs (`feature-name`). Never real Jira numbers, employer ticket prefixes, org domains, GitHub handles, or session-specific identifiers — even in "example" prose.

48.2. **Deny patterns stay local:** machine-specific hygiene regexes belong in `public_hygiene_patterns_file` (user facts), not in the public repo. The repo may ship an empty template (`docs/scan-public-hygiene.patterns.example`) only.

48.3. **Runner stays local:** execute `public_hygiene_scan_script` from user facts (typically under `~/.ai-playbook/scripts/`). Gitignore repo-root `/scripts/` so local copies cannot be committed accidentally.

48.4. **Before skill commits:** run the hygiene scan; personal contact email is allowed only in `LICENSE.txt` copyright lines.
