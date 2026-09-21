---
name: done
description: >
  Finalize a development session by running the learn workflow to capture lessons, then committing
  all uncommitted changes across all repositories (project, skills, docs/facts). Use when the user
  signals a session is complete (e.g. "done", "commit", "wrap up").
  This skill owns all git commits except learn's own learn-authored skills-repo artifacts
  (learn Step 1.8 and the learn skill-placement commit workflow; artifacts in the
  failed-capture set (done Step 4) may be staged by Step 4 after asking) and the docs-branch skill's
  orphan-branch commits; other skills (review, etc.) make file changes but never commit.
---

# Done

Run `/learn` to capture lessons from this session, then commit all uncommitted changes across all repositories touched during the session.

For dated reports or any request containing relative dates such as "today", "tomorrow", or "next Monday", verify the current date from the system environment at the start of the task and derive the target date from that value. Do not infer the date from conversation timing or a previously drafted filename.

## Repository scope ledger

Before Step 0, inventory every repository touched by the task from tool activity, the user's explicit scope, and repository status. `done` applies to each applicable repository, not only the repository containing the latest artifact or the current working directory. Process each project repository independently through Steps 0-3 with its own lock, then run the shared skills and docs/facts commit checks. Never report completion while a touched repository remains unverified or uncommitted.

## Invocation (read first)

`done`, `learn`, and `docs-branch` are **markdown skills**, not shell commands or binaries. There is no runner under `~/.ai-playbook/runtime` and no `/learn` executable.

- **Do not** run `done`, `learn`, `docs-branch`, `SKILL.md`, or `/learn` as shell commands.
- **Do not** delegate this workflow to a Task/subagent that tries to exec a skill path.
- **Do** read each skill file (`~/.agents/skills/<name>/SKILL.md`) and execute its steps in **this** agent session using normal tools (shell for scripts, Read/Write for skill logic).

**Workflow continuity:** This skill executes as a continuous sequence of steps (0 → 1 → the pre-docs sweep gate run → 2 → 2.5 → 2.6 → 2.75 → the pre-commit sweep gate run → 3 → 4 → 5 → 6 → 7); the two sweep gate runs are the `done_sweep_gates.sh` phases (`pre-docs`, `pre-commit`) and carry no fixed step numbers. After each step or skill invocation completes, immediately proceed to the next step without stopping or waiting for user input. Only stop if a step fails, produces an error, or requires user clarification. **Exception:** Step 0 uses a short agent wait (`DONE_LOCK_AGENT_MAX_WAIT_SECS`, default 90s); on timeout return `blocked` with lock `status` instead of polling for hours. **An empty project working tree is not a stop condition:** still run the pre-docs sweep gate run (`done_sweep_gates.sh pre-docs`), Step 2, and Step 6 and finish with Step 7.

## Configuration (from facts document)

| Key | Purpose | Fallback |
|-----|---------|----------|
| `skills_repo_path` | Path to the skills repository | ask the user |
| `done_lock_script` | Per-repo done lock script | `~/.ai-playbook/scripts/done-lock.sh` |
| `confluence_mirror_hygiene_script` | Confluence mirror validate + ephemeral tmp cleanup | `~/.ai-playbook/scripts/confluence-mirror-hygiene.sh` |
| `doc_registry_validator_script` | Document registry integrity + immutable-path write gate | `~/.ai-playbook/scripts/doc_registry_validator.py` |

Script path for Step 0 / Step 6 (override with `DONE_LOCK_SCRIPT` for local testing):

```bash
"${DONE_LOCK_SCRIPT:-${HOME}/.ai-playbook/scripts/done-lock.sh}"
```

Agent wait budget for Step 0 (override for local testing):

```bash
"${DONE_LOCK_AGENT_MAX_WAIT_SECS:-90}"
```

Before Step 0, in a repository that resolves the maintenance skill, run the rearm-on-touch check defined in the maintenance skill's Step 0 through its mechanical script, from the project git root: `python3 "${REARM_ON_TOUCH_SCRIPT:-${HOME}/.ai-playbook/scripts/rearm_on_touch.py}"` (a repo-local `scripts/rearm_on_touch.py` copy wins when present), passing `--listing-json <path|->` when an automation listing was fetched as decision input. The escalation contract is echo-and-continue: echo the verdict in the Step 7 report (the class, any bookkeeping edits it applied, the skipped-reason, or the rc 2 malformed-or-failed error) so a skipped or failed check is visible in the run record, and never block the commit path on it: a failed check is advisory, matching the scheduler state file's advisory status and the sibling fail-open hygiene gates; the script classifies, books, and decides but never calls automation primitives, so perform any listing or re-arm the verdict calls for per the maintenance skill before continuing.

## Step 0: Acquire project done lock

Parallel agent sessions on the **same git repository** must not run `learn`, `docs-branch`, or project commits at the same time. Acquire an exclusive per-repo lock **before** Step 1.

1. From the project git root (`git rev-parse --show-toplevel`), run **`status`** first (non-blocking) so a held lock is visible before waiting.

2. Acquire with a **short agent wait** (do not use the script default 7200s in agent sessions):

   ```bash
   LABEL="$(git branch --show-current 2>/dev/null || echo unknown-branch)"
   MAX_WAIT="${DONE_LOCK_AGENT_MAX_WAIT_SECS:-90}"
   LOCK_SCRIPT="${DONE_LOCK_SCRIPT:-${HOME}/.ai-playbook/scripts/done-lock.sh}"
   if ! LOCK_EXPORTS="$("$LOCK_SCRIPT" wait-acquire --label "$LABEL" --max-wait "$MAX_WAIT")"; then
     "$LOCK_SCRIPT" status >&2
     echo "done-lock: blocked after ${MAX_WAIT}s; another done holds the lock" >&2
     echo "done-lock: if holder PID is dead or lock is stale, run: $LOCK_SCRIPT stale-clean" >&2
     exit 2
   fi
   eval "$LOCK_EXPORTS"
   # Print the exports: Step 6 release runs in a LATER shell call whose env is
   # fresh, and release-repo refuses to source the session fence file, so the
   # token must survive here in chat context to be re-exported there.
   printf '%s\n' "$LOCK_EXPORTS"
   if [[ -z "${DONE_LOCK_DIR:-}" || -z "${DONE_LOCK_TOKEN:-}" ]]; then
     echo "done-lock: acquire succeeded without lock exports" >&2
     exit 1
   fi
   ```

   Choose the lock-holding variant by shell mode:

   - **Variant A, persistent controlling shell:** install the trap in the controlling shell immediately after the successful acquire (the existing trap snippet stays here) so an interrupted same-shell run attempts token-fenced release. The trap is a safety net, not a substitute for the explicit Step 6 release.

     ```bash
     trap 'status=$?; if [[ -n "${DONE_LOCK_DIR:-}" && -n "${DONE_LOCK_TOKEN:-}" ]]; then DONE_LOCK_DIR="$DONE_LOCK_DIR" DONE_LOCK_TOKEN="$DONE_LOCK_TOKEN" "$LOCK_SCRIPT" release-repo || true; fi; exit "$status"' EXIT INT TERM
     ```

   - **Variant B, one-shot shell calls:** never install the exit trap in the acquiring call; the acquiring shell exits when the call ends and the trap would release the lock while the workflow continues. Retain `DONE_LOCK_DIR` and `DONE_LOCK_TOKEN` in session context from the acquire output (Step 0 item 3), and the run must reach the Step 6 release on every exit path (completion, failure, or blocked). When a long-lived process is identifiable (for example the agent runtime), pin DONE_LOCK_HOLDER_PID to a long-lived process so dead-holder recovery cannot reclaim the lock mid-run after the grace period.

   **Interruption cleanup for both variants:** Variant A's trap attempts release on interrupt; in Variant B the lock intentionally survives the call, cleanup is the explicit Step 6 release from session context, and when the session itself died the operator escapes are `status` plus `stale-clean` per Step 0 item 5.

3. Keep `DONE_LOCK_DIR` and `DONE_LOCK_TOKEN` in scope when the same shell session runs multiple steps. **Across separate Shell tool calls**, re-export both values from your Step 0 acquire stdout (chat context). The file `<repo>/.ai-playbook/done-lock.session` is a **fence/status** signal only; Step 6 `release-repo` requires env vars and will **not** source that file (confused-deputy guard after stale-clean / peer acquire).
4. If **wait-acquire** times out, run `status`, report the holder (`label`, `age_secs`, `holder_pid`, `holder_alive`, `stealable` / `abandoned`), return `blocked`, and **do not** commit. Do not bypass an active lock. Do **not** run `stale-clean` unless `status` shows the lock is stale/abandoned **and** you intend to take over; after `stale-clean`, only the chat that successfully re-acquires may release (using that acquire's token).
5. **Stealable locks** (auto-stolen on the next `acquire` / `wait-acquire` poll):
   - **Stale:** age ≥ `DONE_LOCK_STALE_SECS` (default 1800 = 30m) permits explicit `stale-clean`; age alone does not authorize automatic takeover.
   - **Abandoned:** lock metadata records a holder PID and process identity, independent process-table verification says that holder is dead, and the `DONE_LOCK_DEAD_HOLDER_GRACE_SECS` grace period has elapsed. A matching `<repo>/.ai-playbook/done-lock.session` does not prevent reclaiming a verified-dead holder.
   - **Blocked recovery:** a live holder with a missing or invalid fence, a reused PID, or an ambiguous holder identity is never auto-stolen.
   - **Session fence:** the session file is a fence/status signal, not proof that its owner is alive. A verified-dead `holder_pid` is auto-reclaimed after the dead-holder grace period even when the matching session file remains (normal after one-shot Shell tool exits). A live or ambiguous holder remains protected, and `stale-clean` is the operator escape for stale locks without a verified-dead owner. Step 6 releases only with the env token from **your** acquire.
6. Optional: pass a richer `--label` (plan slug, task id, review round) when the orchestrator provides context.

**After the lock is acquired, immediately continue to Step 1.** Do not run learn, docs-branch, or project commits before Step 0 succeeds.

**Run-start marker:** immediately after the lock is acquired, write a content-bearing per-run marker file under `{tmp_dir}/done-session/` named `run-start-<UTCtimestamp>` (filename format `run-start-YYYYmmddTHHMMSSZ`, UTC; create the directory if missing). The pre-docs sweep gate run's plan-readiness gate anchors this run's session window on the newest marker written by a previous done run. Marker pruning is governed solely by the docs-tmp-sweep gate. The marker is content-bearing: its single line records the creation epoch, the trailing-slash-stripped resolved `$REPO_TOP`, and the writing shell PID, so gate-time identity can rely on content-match confirmation instead of chat recall alone. Field order in the marker line: the first field is the epoch, the last field is the PID, and everything between them is the repo root (repo roots containing spaces therefore parse unambiguously).

```bash
REPO_TOP="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
TMP_DIR="$(sed -n 's/^tmp_dir = ["'\'']\(.*\)["'\'']$/\1/p' "$REPO_TOP/.ai-playbook/facts.md" 2>/dev/null | head -n 1)"
TMP_DIR="${TMP_DIR:-$REPO_TOP/docs/tmp/}"
case "$TMP_DIR" in /*) ;; *) TMP_DIR="$REPO_TOP/$TMP_DIR";; esac
mkdir -p "${TMP_DIR%/}/done-session"
MARKER="${TMP_DIR%/}/done-session/run-start-$(date -u +%Y%m%dT%H%M%SZ)"
MARKER="$(cd "$(dirname "$MARKER")" && pwd)/$(basename "$MARKER")"
printf '%s\n' "$(date -u +%s) ${REPO_TOP%/} $$" > "$MARKER" && printf 'run-start marker: %s\n' "$MARKER"
```

Keep the echoed marker path in chat context as this run's audit record. The sweep gates derive the session window mechanically from the `run-start-*` markers under `{tmp_dir}/done-session/` (the newest content-confirmed marker is the current run; the newest strictly older one is the previous-run anchor), which is the mechanical counterpart of the echo: when fewer than two markers are content-confirmable at gate time, the window is unanchorable (conservative gating) and the docs-tmp-sweep gate prunes no `run-start-*` markers this run; never guess by recency. This rule is the Step 0 echo-loss fallback that the plan-readiness gate back-references.

## Step 1: Run Learn

Invoke the `learn` skill now to extract lessons and update the documentation corpus before committing.

**Learn-owned commits in this step:** learn may commit its own skills-repo artifacts during this step (its Step 1.8 backlog items and skill-placement edits); that is expected and does not double-commit, because Step 4 sees only non-learn leftovers plus the failed-capture set, and no-ops when clean.

**If `learn` reports a blocked state** (Step 6.6 user-corpus violation: a strict-tagged `UL#N` lesson is missing its `**Principle:** Family X` tag, or the gate script returned non-zero on the adopted corpus), release the lock via Step 6 and return `blocked` WITHOUT proceeding to Step 2 commit. `learn` is invoked here as a SKILL (a sub-procedure), not as a subprocess whose exit code this step checks, so the gate's block decision lives in `learn`'s Step 6.6 text and propagates here through `learn`'s returned state. The operator fixes the user corpus out-of-band (classify the listed `UL#N` via learn/generalize, or run `lessons.py adopt --tag-unclassified <user_corpus>` manually) before the next `done`.

**After learn completes, immediately continue to the pre-docs sweep gate run.** Do not stop or wait for user input; the workflow is continuous and all steps should execute in sequence.

## Pre-docs sweep gates (`done_sweep_gates.sh pre-docs`)

Immediately after learn and before `docs-branch`, run the deterministic pre-docs gates once per repo from the project git root:

```bash
bash "${DONE_SWEEP_GATES_SCRIPT:-${HOME}/.ai-playbook/scripts/done_sweep_gates.sh}" pre-docs
```

Gates run in this order: plan-readiness, confluence-hygiene, doc-registry, backlog-inbox, review-thread closure (a session-level conditional gate the runner does not execute; apply it in-session per its bullet below before continuing), review-staging, vim-swap-sweep, docs-tmp-sweep. The runner derives every session-scoped input mechanically (it cannot read chat context): the session window anchors on the `run-start-*` markers under `{tmp_dir}/done-session/` (the newest content-confirmed marker is the current run, the newest strictly older one is the previous-run anchor, and fewer than two confirmable markers means an unanchorable window with conservative gating), and candidates come from `{tmp_dir}/done-session/plan-deliverables.txt` plus the porcelain and ignored-matching git arms. **Exit 0:** continue immediately to Step 2. **Failure:** every gate reports even after an earlier failure; fix what the report flags using the per-gate guidance below and re-run the runner until it exits 0.

- **plan-readiness** (a gated plan's latest review does not cover its current bytes): refuse to finalize; require a fresh `review-plan` round (after any plan edit that changes the digest) before re-running the gate; passed, manifest-exempted, and archived plans have their deliverable lines pruned by the runner. **Deployment-gap signature (narrow):** a deployment gap is ONLY (a) the validator file itself missing or unopenable, or (b) a `ModuleNotFoundError` in the output. For either: stop and report the wiring gap, and never use the recorded-stop exception for it; manual remedy: `cp scripts/plan_readiness.py ~/.ai-playbook/scripts/` plus siblings (the script imports `validate_review_staging.py` and `facts_paths.py` from its own directory, so copy all three; the deployed `facts_paths.py` may be a symlink, keep it one, e.g. `cp -P`, do not dereference it into a second copy). Any OTHER non-zero exit that prints no `readiness FAILED:` line (validator crash, traceback, unexpected output) is NOT covered by that copy remedy: investigate the validator before re-running the gate. **Recorded-stop exception:** the only permitted way past a failed gate is when the user explicitly chooses to stop without finalization and that choice is recorded in the session log. In that case do not commit the plan deliverable: record the excluded plan path in the session log and, in this session's later commit-all steps, exclude exactly that path plus its review artifacts (the review Markdown and `.stats.json` sidecar under `{reviews_dir}`) when staging, then continue with the remaining hygiene steps and report the recorded stop in Step 7; also remove every line listing the excluded path from `{tmp_dir}/done-session/plan-deliverables.txt` so it does not reappear as a gate target.
- **confluence-hygiene:** never delete `*-cf-out.md` until audit confirms the content is already represented in the docs hierarchy or is a stale duplicate. NEEDS_UPGRADE: promote first (mirror at `docs/history/context/confluence/{page_id}-{slug}.md` with standard frontmatter, manifest `layer2_targets`, or the spike sync ledger). UNMAPPED: route manually (new manifest entry, mirror file, or Layer 2 doc); do not delete. On `validate` failure: fix the mirror frontmatter and filenames, the manifest rows, and the mirror index; after a live push, refresh mirror bodies, bump manifest versions, and set `sync_status: synced` in the same session (never leave truncated wiki pages; republish the full body). **Deployment gap:** when `confluence-mirror-hygiene.sh` is absent from every resolved path while a run-when trigger is live, the gate fails rc 1 as a deployment gap; deploy the script to the runtime home `scripts/` directory and re-run, and never use the recorded-stop exception for a deployment gap.
- **doc-registry:** warn-only findings (legacy files without registry entries, multiply-claimed srcs) do not block: report them, and clear a standing-override's audit note after the licensed write lands. Hard findings (registry parse errors, invalid `sot`/`state` values, malformed audit-note tokens, duplicate identities or SOT declarations, successor cycles, unprotected writes to completed-history paths): fix the registry row or move the change into the living SOT instead of editing a completed artifact. An absent validator is fail-open (reported once, non-blocking). The runner's check-writes stdin union carries git's change-type letters verbatim (porcelain `XY PATH` rows with renames as `R  old -> new`, the committed-since-session-start name-status rows, and ignored files as bare rows); the letters are what bind the registered-src exemption to the archive transition, so the union is never downgraded to name-only paths.
- **backlog-inbox:** genuine backlog material moves into the resolved `{backlog_dir}` per `receiving-review` Backlog capture (rename to `YYYY-MM-DD-<slug>.md` when needed); a legitimate Layer 2 doc that merely trips the filename shape is renamed to a compliant name, asking the user when the run is interactive; never a silent move that misfiles real content.
- **review-thread closure:** when a review-thread marker (a `docs/tmp/review-threads/<session-slug>.json` per `receiving-review`'s marker duty) whose recorded session identity matches the CURRENT session exists, run `python3 scripts/review_thread_gate.py --marker <path>` with an inventory source (canned file/pipe such as captured `gh` output, or `--live`): exit 0 only when every tracked thread carries a verified agent reply or an explicit disposition. On failure, report blocked, release the project done lock per Step 6, and do not report completion; report push authorization separately from review-response state. A session with no marker, or a marker whose recorded identity does not match the current session (stale or foreign), is unaffected: the gate reports it as stale/skipped and never gates this session's done run. Human-authored threads are never auto-resolved.
- **review-staging:** complete each flagged staging doc per `review-staging` (Metadata, Review Statistics, Findings with Comment/Analysis) before continuing; do not sync stub staging docs to the orphan `docs` branch.
- **vim-swap-sweep:** the runner removes only verified stale swaps (dead-owner PID) and preserves live-owner or unverifiable files; a `needs-manual` entry stays in place until manually confirmed.
- **docs-tmp-sweep:** durable findings graduate into lessons, completed plans, or Layer 2 docs; the rest dies with its owner. The runner never removes an ACTIVE `execute-plan` session (its plan pending anywhere under `{plans_dir}`, nested subdirectories included), `review-loop*`/`code-review/`/`handoff/` scratch (their owning skills clean up), the previous-run anchor marker, or the current-run marker, and it skips rather than removes anything never synced to the `docs` branch or of unclear ownership; a one-off already synced to the `docs` branch is likewise skipped while it was modified inside the session window (removal waits for a session whose window no longer covers it, and an unanchorable window removes nothing). Resolve skips by hand only after confirming sync state, and report what was left and why.

**After the pre-docs sweep gate run completes (or no-ops), immediately continue to Step 2.** Do not stop or wait for user input; the workflow is continuous and all steps should execute in sequence.

## Step 2: Preserve Gitignored Docs and Instructions

Invoke the `docs-branch` skill now. When the session runs in an ad-hoc worktree, first migrate the run's review staging docs and session logs to the main checkout (the execute-plan Phase 5 migration, `worktree_closeout_migrate.py migrate`), before the docs-branch sync and in every case before the worktree is removed. It will:
1. Snapshot all configured gitignored shadow paths (`docs/`, `.github/docs/`, `.ai-playbook/`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `COPILOT.md`, plus repo `extra_shadow_dirs`) while leaving the live checkout on the current branch.
2. Sync those files to the permanent `docs` orphan branch through a temporary `git worktree`, creating it if it doesn't exist.

**After docs-branch completes, immediately continue to Step 2.5.** Do not stop or wait for user input; the workflow is continuous and all steps should execute in sequence.

> All implementation details, edge cases, and the full bash script live in `docs-branch/SKILL.md`. Refer there for the canonical script when executing.

**After docs-branch completes, verify gitignored files are still on disk:**
```bash
# Read gitignored doc paths from .ai-playbook/facts.md TOML (using-skills Step 0); include common candidates:
for p in docs/tmp docs/history/reviews docs/reviews docs/personal .ai-playbook/facts.md AGENTS.md CLAUDE.md GEMINI.md COPILOT.md; do
  [ -e "$p" ] && git check-ignore -q "$p" && echo "OK: $p" || true
done
```

**Verify untracked WIP survived** (docs-branch keeps the live checkout on the current branch):

```bash
# Before docs-branch (optional but recommended):
git ls-files --others --exclude-standard > /tmp/docs-branch-untracked-manifest.$$
# After docs-branch:
while IFS= read -r f; do
  [ -e "$f" ] || echo "MISSING untracked: $f"
done < /tmp/docs-branch-untracked-manifest.$$
rm -f /tmp/docs-branch-untracked-manifest.$$
```

If any path is missing, restore from docs-branch `UNTRACKED_BACKUP` or Cursor Local History before committing.

If any gitignored path that existed before docs-branch is now missing, restore it immediately from the `docs` orphan branch before proceeding (docs-branch add-only sync restores missing shadow files automatically, including reviews; use manual restore only when that step did not run):
```bash
git checkout refs/heads/docs -- <missing-path>
git restore --staged <missing-path>
```

## Step 2.5: Roll Back Formatting-Only Changes

Before committing, identify and revert any **uncommitted** files where the only diff is formatting (whitespace, trailing commas, blank lines, import reordering, line wrapping, or collapsing multi-line expressions to a single line) with no logic, naming, or structural change.

**This applies to ALL uncommitted files, including pre-existing local changes not made in this session.**

1. List uncommitted changed files: `git diff --name-only && git diff --cached --name-only`.
2. For each file, visually inspect `git diff -- <file>`. Revert if **every** hunk is one of:
   - whitespace / blank line changes
   - line wrapping / unwrapping (same tokens, different line breaks)
   - trailing commas added/removed
   - import reordering
   - end-of-file newline added
   - collapsing or expanding multi-line expressions with no token change

   Do **not** rely solely on `git diff -w --ignore-blank-lines`; that flag misses ktlint reformatting such as line splits and trailing commas.
   ```bash
   git restore <file>          # unstaged changes
   git restore --staged <file> # staged changes
   ```
3. Confirm no unintended reverts: re-read the diff for any reverted file before staging.

> Formatting-only files add noise to PRs and waste reviewer time. Never include them unless the PR's explicit purpose is formatting cleanup.

## Step 2.6: Check Documentation Cross-References Added In This Session

Before committing, review whether this session created or substantially revised reusable documentation, reference material, instruction guidance, or explanatory artifacts. If yes, verify the required cross-references were added.

Check for these cases:

1. **New or expanded reusable guidance**
   - If the session added or materially expanded a guidance document that future agents or contributors are expected to consult, make sure instruction files or nearby canonical docs point to it.
   - Update both `AGENTS.md` and `CLAUDE.md` together when adding such references.

2. **New or updated reference material**
   - If the session added or relied on source manifests, mirrored references, standards, regulations, specs, external research docs, or similar reference material, verify the relevant manifest or index was updated and that dependent docs point to that reference set appropriately.

3. **New explanatory artifacts**
   - If the session added or materially revised a walkthrough, presentation artifact, decision note, or similar explanatory document, verify that any relevant authoring guidance or discoverability references were added where future agents would reasonably look for them.

4. **New instruction rules**
   - If the session added rules to instruction files, confirm any canonical docs those rules depend on are referenced explicitly instead of leaving the relationship implicit.

5. **Doc-hierarchy migration or doc-only PRs**
   - If the session ran **doc-hierarchy-migrate** verify (`step6` or `full`) successfully, do not add PR **Test plan** items for that gate as unchecked reviewer tasks. The gate is an implementer checkpoint from the skill install, not a repo-local script.
   - When updating the PR description, use the [PR checklist](../doc-hierarchy/company-decisions.md#pr-checklist-team-proposal-accepted) only unless the reviewer asked for more; follow [PR description rules](../doc-hierarchy/company-decisions.md#pr-description-rules).
   - Mark session-verified checks `[x]` or omit them; never leave implementer-completed verification as unchecked homework.

Do not assume the `learn` step already wired these references correctly. Re-check the final diff before staging and commit any missing cross-links as part of cleanup.

## Step 2.75: Unused import scan (all touched source files)

Before committing, verify every changed or new **source file** from this session has no unused-import diagnostics (or the language equivalent: `using`, `require`, type-only imports, and so on).

1. List touched paths from unstaged, staged, and untracked diffs:
   ```bash
   { git diff --name-only; git diff --cached --name-only; git ls-files --others --exclude-standard; } | sort -u
   ```
2. From that list, keep paths the IDE or language server can lint. Exclude obvious non-source artifacts (markdown, plain YAML/JSON config, lockfiles, images, binaries, generated stubs under build output). When unsure whether a path is lintable, include it; `ReadLints` skips what it cannot analyze.
3. Run IDE or language-server diagnostics on **every remaining touched path** (for example Cursor `ReadLints` per file or batched by directory). Fix every unused-import-class diagnostic before staging. Common cases:
   - **Java / Kotlin:** unused `import` or static import (including static imports shadowed by instance calls such as `lenient().doAnswer()` vs `import static … doAnswer`).
   - **Python:** unused `import` / `from … import`.
   - **TypeScript / JavaScript:** unused value or type-only `import`.
   - **C#:** unused `using`.
   - **Go / Rust:** unused imports (still run diagnostics even when `go build` / `cargo check` also enforces).
4. When no linter is configured for a touched language, eyeball new or changed import blocks in the diff and remove lines with no references in the file.
5. Re-run diagnostics after fixes until clean on all touched lintable source paths.

Do not stage source files for commit while unused-import diagnostics remain on any touched path from this session.

**After Step 2.75 completes, immediately continue to the pre-commit sweep gate run.**

## Pre-commit sweep gates (`done_sweep_gates.sh pre-commit`)

After Step 2.75 and before Step 3, run the deterministic pre-commit gates once per repo from the project git root:

```bash
bash "${DONE_SWEEP_GATES_SCRIPT:-${HOME}/.ai-playbook/scripts/done_sweep_gates.sh}" pre-commit
```

Gates run in this order: **sensitive-data-scan** (diff-content pattern grep over staged content, full-content scan of untracked files, the push-range commit-message audit when an upstream is configured, skipped with a warning line in the report when none is (`Co-authored-by:` trailers and employer-brand patterns resolved from the facts document), and `public_hygiene_scan_script` when this repo is the skills repo), **em-dash-scan** (`check-no-em-dash.sh touched` over touched prose; policy: `agent_workflow_guidelines.md` §39; a script absent from every resolved path is a rc 1 deployment gap, never a skip), **instruction-size** (`check-instruction-size.sh gate`; budget 30,720 bytes per instruction entrypoint, the learn Step 6.5 constant; only over-budget files with uncommitted changes block; a script absent from every resolved path is a rc 1 deployment gap, never a skip). Fixing stays in this skill: on a failure, fix per the guidance below and re-run the runner until exit 0; for a deployment gap, deploy the missing script to the runtime home `scripts/` directory and re-run, and never use the recorded-stop exception for it. Do not stage files a failing gate flags; after the pre-commit sweep gate run exits 0, immediately continue to Step 3.

- **sensitive-data-scan:** replace personal paths with facts-document references or generic placeholders (e.g., `<your-org>.atlassian.net`, `~/Projects/<project>/`); replace internal names with generic equivalents; move credentials to `.env` or facts documents (never commit them); in a skill file, externalize machine-specific values to facts documents and keep portable policy constants and workflow thresholds in the skill body (see `learn` Step 2, Facts vs skill configuration; `agent_workflow_guidelines.md` §50); fix all `public_hygiene_scan_script` failures before staging. **Do NOT commit until all sensitive data is resolved.**
- **em-dash-scan:** fix every reported line with a comma, colon, semicolon, period, or parentheses, under the no-silent-gate-satisfying-rewrites rule (see Rules): when the failures reach untouched user-authored prose, or no minimal edit exists, stop and surface the conflict for the user to adjudicate; do not re-run the scan for exit code 0, leave the failing prose unstaged, and do not continue to Step 3 until the user adjudicates.
- **instruction-size:** return to learn Step 6.5 (compact hybrid bullets to cross-references, move infrequent rules to skills), then re-run the runner before staging instruction files.

## Step 3: Commit Uncommitted Changes

After learn and stash steps complete:

0b. **Plan-deliverable append (producer 2 for the pre-docs sweep gate run's plan-readiness gate):** Before any `git commit` in this session that stages paths under `{plans_dir}` (excluding `{plans_completed_dir}`), append each staged plan path to `{tmp_dir}/done-session/plan-deliverables.txt` (create dir/file if missing; one repo-relative path per line; skip duplicates). Do this in the same turn as the commit, including when the commit is not part of `done`.

0. **Distinguish session changes from pre-existing local changes.** Only commit changes that were made during this session. If `git status` shows uncommitted files that were not touched by you in this session, ask the user before staging them; they may be in-progress work the user does not want committed yet. For cleanup or restoration sessions, capture the dirty-tree and untracked-file baseline before the first edit: always record the git status --porcelain baseline in the session notes before the first edit; additionally run the cleanup baseline checker scripts/check_cleanup_scope_baseline.py against the task's scope ledger when the task's scope ledger exists (resolve the skills repo checkout from the skills-repo path key in the user facts document and pass this repo via --repo-root). Refuse to stage any path that was already dirty or untracked at baseline unless the user explicitly includes it. Checker exit codes: exit 1 means a path outside the ledger is dirty or deleted, so ask the user before staging it; exit 2 means the checker could not run, so fall back to the recorded session-notes baseline; if the checker exits 2 and no recorded baseline exists, ask the user before staging any path not created or modified this session. Run the checker before the first commit of the session for full coverage; after commits exist, only deletions remain checkable (against the ledger's session-start base ref, never with `--base HEAD`), because committed non-deletion sweeps are invisible at any base ref once committed: assess committed modifications from the recorded session-notes baseline instead. If no pre-edit baseline exists at done time (whatever the reason: checker never run, exit 2 with no recorded baseline, or baseline recorded after edits), ask the user before staging any path not created or modified this session; a baseline recorded after edits is not a baseline. Checker limitations: it cannot see gitignored files (capture the ignored set with `git status --porcelain --ignored` and record those paths in the session notes explicitly), and it matches allow-list paths byte-exact relative to the repo root (no `./` prefix). If the skills-repo path key is missing or unresolvable, record the session-notes baseline and note that the checker was skipped.
1. Run `git status` and `git diff` (staged + unstaged) to see all changes.
   **Pre-commit guard (post sub-agent git op):** Step 2 `docs-branch` (and any prior sub-agent `git worktree`/`git checkout`/`git stash` operation) can leave the main repo's index/worktree in a REVERTED state relative to HEAD while HEAD stays correct. Before staging, run `git diff --cached --stat`: if it shows large deletions across files you did not edit this iteration (e.g. +73/-1062 across 14 files) OR the test count dropped vs the last known-good count on HEAD, a leaked revert is staged. Run `git reset --hard HEAD`, re-stage only your intended edits, then re-verify. Never a directory-wide add (no `git add -A`/`git add .`) here, or the rollback is swept into the commit. The same guard covers unstaged dirt that REGRESSES HEAD: after the cached-diff check, run the dirt regression gate (`python3 scripts/dirt_regression_gate.py --base <merge-base-with-default-branch>`, resolved via `git merge-base HEAD <default>`; skip with a one-line note when no default branch resolves) over the working tree's modified files; any file it names as a dirt REGRESSION is restored from HEAD (`git checkout -- <file>`) and reported, never staged or committed. (Witness: 2026-07-23 group-leftover-crypto-warnings r6; see project `development_lessons.md` lesson on this family.)
2. Run `git log --oneline -5` to match existing commit message style.
3. Derive the story key from the current branch name (e.g. `feature/PROJ-1234-...` → `PROJ-1234`). If the branch name contains no story key, use a plain descriptive commit message without a ticket prefix on branches such as `main` or `master`. Ask the user only if the repository convention is unclear and there is no obvious non-ticket fallback.
4. **Before staging any file, verify it is not gitignored:**
   ```bash
   git check-ignore -q <file> && echo "IGNORED, do not stage"
   ```
   If a file appears in `git diff` but is gitignored, it was previously force-tracked. Remove it from tracking first and do **not** commit it on the feature branch:
   ```bash
   git rm --cached <file>
   ```
   Gitignored files belong on the `docs` branch only (handled in Step 2), not on the working feature branch.
4a. **Pre-commit lesson scope audit (when the project lessons corpus is touched).** If the session's staged or unstaged diff creates or substantially edits the project lessons corpus (`docs/maintenance/development_lessons.md`, or `PROJECT_CORPUS_REL` from `lessons_recall.py`), audit scope BEFORE staging it:
   1. **Mechanical duplicate check.** First resolve the company guidelines master (`company_guidelines_master` in facts) by applying the ownership-scoping resolution test (`learn` Step 1.2 item 5d, anchored to the repo being audited): it resolves only when the repo sits under the company workspace root (`company_projects_root` in facts) and the key's path exists. Outside the company root (a repo under the personal root, or under neither workspace root) the master does not resolve and the mechanical check passes trivially: do not run the script, and print a one-line note (`company master out of scope for this repo; duplicate check skipped`). Under the company root with the key's path missing, print a one-line WARNING (`config drift: company guidelines master not found; company duplicate audit not run`); this outcome counts as passed-with-drift and does not block the Step 3 commit (the placement-evidence check below still applies); it is not a failed audit. Because the duplicate check did not run, the commit message body of the Step 3 commit that stages this corpus change carries the drift witness on its own body line, `lesson-scope-audit: config drift: company guidelines master not found; company duplicate audit not run`, so the skip decision is reconstructable from repository history alone. When the project corpus path is gitignored there is no Step 3 corpus commit to carry the line: invoke the docs-branch skill's witness append (its Step 3) with the exact witness line so the docs-branch history carries the same byte-for-byte line. Otherwise (master resolved) verify the validator script file exists (e.g. `test -f` on the resolved path); if it is absent, print a one-line warning (`lesson scope validator absent; mechanical duplicate check skipped (cold-start)`) and continue with the placement-evidence check (cold-start; do not block the session on a missing optional validator). Only when the file exists, run the validator with stderr captured (with `$PROJECT_CORPUS` and `$COMPANY_MASTER` set to the resolved corpus and master paths; override the script path via `LESSON_SCOPE_SCRIPT` for local testing only):
```bash
python3 "${LESSON_SCOPE_SCRIPT:-${HOME}/.ai-playbook/scripts/check_lesson_scope.py}" "$PROJECT_CORPUS" "$COMPANY_MASTER"
```
       Whichever witness line fired above (out-of-scope note, drift WARNING, cold-start warning) is echoed into the Step 7 outcome report so the skip decision is reconstructable after the session; on the drift path the witness is additionally carried durably in the corpus commit message body, so repository history alone identifies the skip.
       Outcome semantics: exit 0 with no WARNING line on stderr = clean pass, covering rules of at least 25 normalized words (the witness-pointer floor: shorter blocks are presumed witness pointers and never match). Exit 1 with at least one `DUPLICATE:` line = a full rule is duplicated across the project corpus and the company master (handled by item 3 below). Any WARNING line on stderr, any exit code other than 0 or 1 (including exit 2 and interpreter codes such as 126 or 127), or exit 1 with no `DUPLICATE:` line, is a tool failure: stop, report the validator error, release the lock per Step 6, and return blocked; do not stage the corpus. `$COMPANY_MASTER` must resolve to the canonical master from facts, never a repo mirror.
   2. **Placement-evidence check.** Confirm the learn run's placement receipt (`learn` Step 1.2 item 5c) covers every new or substantially edited lesson. If a lesson has no receipt, or its scope cannot be established from the receipt, stop before commit and request classification from the user; do NOT silently commit the narrower placement. For a fork (4) lesson, the receipt must state the residual dependency; a fork (4) receipt with no residual dependency stops before commit for reclassification, exactly like a missing receipt.
   3. **On exit 1 with at least one `DUPLICATE:` line (duplicate full rule):** stop before commit, release the lock per Step 6, and return blocked with the validator output; ask the user to classify the lesson (company master vs project corpus). Never move, rewrite, or duplicate lessons automatically.
   4. **Commit boundary:** the project witness and the company guidelines change are committed in the same pass ONLY when both were intentionally produced by the same workflow (`learn` placed them deliberately). done must not move or duplicate lessons to reconcile placements.
4b. **Session-touched project lessons corpus (non-ignored):** After Step 1 (`learn`), if this session created or updated the project lessons file (`docs/maintenance/development_lessons.md`, or `PROJECT_CORPUS_REL` from `lessons_recall.py`) and `git check-ignore` does **not** match it, **stage and commit it on the feature branch** with the other session changes. Untracked (`??`) is not a skip reason. Syncing the same path to the orphan `docs` branch in Step 2 does **not** replace the feature-branch commit. Only gitignored corpora stay docs-branch-only.
5. Stage relevant non-ignored files (including 4b when it applies). Prefer adding specific files by name; never a directory-wide add (no `git add -A` or `git add .`) unless the user explicitly requests it. On a shared checkout, also give the commit itself an explicit pathspec (`git commit -m "..." -- <paths>`), because a peer's staged-but-uncommitted entries sit in the shared index and a pathspec-less commit sweeps them (witnessed 2026-09-18: a learn commit naming its own two files swept a peer's staged backlog item). The inverse is equally binding: a pathspec commit builds from HEAD plus the named paths only, so it excludes your own staged changes outside the pathspec. After `git mv`, pass both the old and the new paths (or, when the index holds only your staged renames, commit the index state with a plain `git commit`) and verify the commit with `git show --stat -M` records the rename rather than a bare create. And immediately before any `--amend` on a shared branch, re-run `git log -1 --oneline`: a peer commit landing between your commands turns the amend into a rewrite of their commit (new sha under their message, your staged leftovers inside); if that happened, verify the tree and stop rewriting (witnessed 2026-09-18, see user-corpus lesson #371).
6. Write a concise commit message. If there is a story key, prefix with `[<STORY-KEY>]`; otherwise use a plain descriptive subject. Focus on the "why" not the "what". When the item 4a audit fired the drift witness, the commit body includes the `lesson-scope-audit:` body line exactly as specified in item 4a. When the audited corpus path is gitignored (no Step 3 corpus commit exists), the witness append on the docs branch carries the line instead; the append failure is a manual follow-up reported in the Step 7 outcome report and never blocks the Step 3 commit path.
7. Commit using a HEREDOC. **Never** add `Co-Authored-By:` or `Co-authored-by:` trailers or use `git commit --trailer` for agent attribution. See user `AGENTS.md` (Git Commit Trailer Policy). If your IDE adds co-author trailers automatically, disable agent attribution in its settings.
8. Run `git status` after the commit to confirm success.

### Commit message format

With a story key:

```
git commit -m "$(cat <<'EOF'
[PROJ-1234] <concise description of what and why>
EOF
)"
```

Without a story key:

```
git commit -m "$(cat <<'EOF'
<concise description of what and why>
EOF
)"
```

## Step 4: Commit Pending Skill Changes (non-learn fallback)

After committing the current project, check the skills repository for leftover changes beyond learn's own Step 1 commits. Learn-owned artifacts (Step 1.8 backlog items and skill-placement edits) were committed by learn during Step 1; this step is a narrowed fallback covering non-learn leftovers plus the failed-capture set. The failed-capture set is the learn-authored artifacts whose Step 1.8 commit learn reported as failed.

1. Resolve the skills repo from the user's facts document (key `skills_repo_path`). When unresolvable, ask the user.
2. Check for dirty non-learn skills-repo paths (skills files, the skills repo's README.md, and its projects/.ai-playbook/ surfaces), plus any failed-capture-set artifacts (defined above). Resolve the backlog home first (`backlog_dir` from the skills repo's `.ai-playbook/facts.md` TOML; fallback `docs/history/backlog/`, per learn Step 1.8) into `backlog_home`, then:

   ```bash
   cd <skills_repo_path> && git status --porcelain -- agents/skills/ "${backlog_home:?}" README.md projects/.ai-playbook/
   ```

   When clean, report "no non-learn skills-repo changes" and no-op.
3. Classify each dirty path as session-attributed (this session's non-learn skill edits, or failed-capture-set artifacts) or foreign. Ask the user before staging each session-attributed path (same discipline as Step 3 item 0); never stage foreign or peer-session paths. For paths learn reported as skipped for foreign or unrecognizable hunks, review the path's diff and stage only after the user confirms the foreign hunks are acceptable (path-level staging stages the file as a whole); when they are not, leave the path unstaged and report it.
4. Stage by explicit path only; never a directory-wide add (no `git add -A` or `git add .`). Re-run the pre-commit sweep gate run's sensitive-data-scan gate (`done_sweep_gates.sh pre-commit`) over the staged content, then commit with a descriptive message.

## Step 5: Commit Pending Facts and Docs Changes

After committing skills, check whether any facts documents or docs repositories were modified during this session. Each docs directory is its own git repo and must be committed independently.

Resolve paths from the user's facts document:
- `shared_docs_dir`, cross-project guidelines and shared facts
- Project-specific docs directories are determined from the current working project

For each docs git repo that has uncommitted changes:

```bash
cd <docs_dir> && git status --short
```

If there are changes:

```bash
cd <docs_dir> && git add -A && git commit -m "docs: <brief description of what was added/updated>"
```

Do not push. These are local-only docs repositories.

**Common docs repos to check:**
- Shared docs (from facts `shared_docs_dir`)
- Current project's `docs/` directory (if it is a separate git repo)

## Step 6: Release project done lock

**Always run Step 6 before Step 7**, including when Steps 1–5 failed or returned early. This lets a waiting parallel `done` resume.

From the project git root, release with **`DONE_LOCK_DIR` and `DONE_LOCK_TOKEN` from your Step 0 acquire** (re-export from that tool output if the shell lost env). In Variant B environments re-export both values from your Step 0 acquire output (chat context) before releasing. `release-repo` requires those env vars and refuses to load the shared session file. The lock session/metadata shape is token-only as of the 2026-09-11 done-lock change; no generation export is involved:

```bash
DONE_LOCK_DIR="${DONE_LOCK_DIR:?}" DONE_LOCK_TOKEN="${DONE_LOCK_TOKEN:?}" \
  "${DONE_LOCK_SCRIPT:-${HOME}/.ai-playbook/scripts/done-lock.sh}" release-repo
```

Equivalent:

```bash
DONE_LOCK_DIR="${DONE_LOCK_DIR:?}" DONE_LOCK_TOKEN="${DONE_LOCK_TOKEN:?}" \
  "${DONE_LOCK_SCRIPT:-${HOME}/.ai-playbook/scripts/done-lock.sh}" release
```

If release fails (token mismatch, env missing), run `status` from the project root. When `status` shows free, your hold is already gone (peer auto-recovery, `stale-clean`, or release); do not source `.ai-playbook/done-lock.session` to “fix” env. A verified-dead holder is reclaimed by the next acquire even if its session fence remains; use `stale-clean` only for the explicit stale-lock escape, and ask the user before forcing removal of an **active** lock.

## Step 7: Report outcome to the user

**Never end `/done` silently after diagnostics.** Always send a short summary:

- Project repo: commit hash(es) created, or **working tree clean** at `HEAD` (include `git log -1 --oneline`).
- Skills / shared docs repos: commits created or none.
- Lock: confirm `status` shows **free** after Step 6.
- If `blocked` at Step 0, learn, or the Step 3 item 4a lesson scope audit: state why and what the user should run (`stale-clean`, fix corpus, classify the duplicated lesson, retry).

When the session used a passive review workflow, distinguish local finalization from
review finalization. Before reporting completion, re-check the live review state and
report the disposition of every tracked thread: verified reply, explicit deferral, or
blocked. A local commit does not replace a required reviewer reply, and a reply does
not imply that the branch was pushed. Keep push authorization separate from permission
to reply to review feedback.

## Integration Points

### With `bootstrap-ai-playbook` skill
Writes and refreshes `.ai-playbook/facts.md` when Terms triggers fire (`using-skills` Step 0). This skill reads `{tmp_dir}` and other gitignored doc paths from that file for Step 2.1 (`docs-branch`).

### With `execute-plan` skill
Invoked as a sub-agent after **each** completed plan task (per-task commit) and after **each** review/fix iteration (per-iteration commit). The orchestrator passes the plan path, task or review-round context, suggested commit subject, and **sub-agent log paths** under resolved `{tmp_dir}/execute-plan/<plan-slug>/`.

**Before Step 1 (learn):** read only the **preceding-step** log(s) the orchestrator listed: for per-task `done`, the implement log from Step 1.2; for review-iteration `done`, the current round's review log (Step 3.1) and address log (Step 3.3) when it ran. Do not read full session history. Use log content as primary input for `learn`, not the orchestrator chat summary. For a review-iteration commit, derive the staging file set from the address log's files-touched list rather than from the handoff's scope summary; when the two disagree, the log is authoritative, because a handoff that under-lists files would otherwise leave one fold of the fix half-committed and the working tree dirty. If a required preceding-step log is missing, release the Step 0 lock (Step 6), return `blocked`, and do not commit. See `execute-plan/agent-logs.md`.

Each execute-plan `done` sub-agent still runs Step 0 and Step 6. Sequential tasks in one orchestrator usually acquire immediately after the prior release; parallel chats on the same repo wait on **wait-acquire**.

**Batch implement launches (Step 1.2 batch contract):** when the orchestrator launched several file-disjoint tasks as one batch, `done` still runs **per member task, in document order**, never once for the batch. Each member's `done` reads only **its own** `task-<N>-implement.log.md` as the preceding-step log, exactly as the single-task flow does. The member's done staging receipt is **member-scoped**: the driver's claim-group protocol fences the handoff to that member's own canonical allowed paths against its moving baseline (the pre-batch launch baseline for the first member; the immediately preceding member's commit for later members, r1 F27), so a member done that touches another member's file is rejected by the driver before any commit is recorded. Members between the first and the last advance only through the driver's typed `resume_member` action on the group's one anchor session; the batch never produces a batch-level commit, and the orchestrator's generic next-task claim stays suppressed until the group closes. **Parallel-group launches (Step 1.2 parallel-group contract):** the per-member rule carries over when the members implemented concurrently instead: each member has its own session, claim, policy token, and `task-<N>-implement.log.md`, and per-member `done` still runs one at a time in document order with the same member-scoped receipt, so the group closes on the last member commit with no group-level commit.

### With `review-staging` skill
The pre-docs sweep gate run's review-staging gate validates session-touched staging docs under `{reviews_dir}/` before docs-branch sync (candidates: porcelain plus ignored-matching paths restricted to the session window, filtered by the validator's `is_staging_review_path`; include `*review*.md`, PR staging (`*-PR-*` / `PR-<n>-...`), and any path the predicate accepts, never only `*review*.md`). Complete Metadata, Review Statistics, and Findings with Comment/Analysis before continuing; do not sync stub staging docs.

### With `receiving-review` skill (review-thread closure gate)
`receiving-review`'s marker duty is the provider: a passive-review session writes the review-thread marker at feedback-processing start and keeps per-thread dispositions in it. `done` is the gate consumer: the pre-docs sweep's review-thread-closure gate runs `scripts/review_thread_gate.py` only for a marker whose recorded session identity matches the current session, failing closed while closure is not established. This skill does not restate the marker schema or reply idempotence rules (owned by `receiving-review`).

### With `plans` and `docs-branch` skills (docs/tmp sweep)
The pre-docs sweep gate run's docs-tmp-sweep gate sweeps `{tmp_dir}` entries whose owning plan archived (plans Plan Lifecycle cleanup) or that are one-off ownerless scratch; `review-loop*`/`code-review/`/`handoff/` scratch is never swept here (no liveness witness; their owning skills clean up). The `docs-branch` sync then drops branch-tracked `{tmp_dir}` paths absent on disk (`{tmp_dir}` is its one sweep-eligible root), so branch copies propagate without hand-editing the docs branch.

## Rules

- Always acquire the Step 0 project lock before learn or any project-side commit steps; always release it in Step 6 (`release-repo` from project git root).
- Never skip Step 6 or Step 7, even for "just commit" or empty working tree runs.
- Always run learn before committing; lessons must be captured first.
- Never skip the learn step even if the user says "just commit".
- Invoke `docs-branch` skill for all docs/instructions preservation; do not inline the stash or branch logic here.
- Never remove an ad-hoc worktree before its run's gitignored review artifacts verify present in the main checkout; the docs-branch sync runs where the on-disk corpus is canonical (the main checkout after migration).
- Run the pre-docs sweep gate run (`done_sweep_gates.sh pre-docs`) after learn and before `docs-branch`; it carries the Confluence mirror validate, audit-cf-out promotion gate, and ephemeral `docs/tmp` cleanup gates, and it no-ops the gates whose triggers (manifest, Confluence mirror or wiki touches, ephemeral publish snapshots) are absent.
- Always verify that new or revised reusable docs, reference material, and explanatory artifacts added in the session are referenced from instructions or related canonical docs where future agents will need them.
- Never stage or commit a file that is gitignored, even if it appears in `git diff` (it was previously force-tracked). Use `git rm --cached` to remove it from tracking; do not commit it on the feature branch.
- Stage by explicit path only; never a directory-wide add. Learn-owned artifacts are committed by learn in Step 1, and Step 4 stages only session-attributed non-learn paths (plus failed-capture-set artifacts, and paths learn reported as skipped for foreign or unrecognizable hunks, staged only after the user confirms the foreign hunks are acceptable) after asking.
- Never skip a session-touched, non-gitignored project lessons corpus (`development_lessons.md`) just because it is untracked or already synced to the orphan `docs` branch; commit it on the feature branch (Step 3 item 4b).
- Never commit a new or substantially edited project lesson whose scope audit (Step 3 item 4a) has not passed.
- Never add `Co-Authored-By:` or `Co-authored-by:` trailers or use `git commit --trailer` for agent attribution. See user `AGENTS.md` (Git Commit Trailer Policy). Disable automatic agent attribution in IDE settings when present.
- Never use `--no-verify`.
- Never commit secrets, PII files (`.env`, credential files), or personal/org-specific information into public repositories.
- Never hardcode personal paths, org domains, or project-specific identifiers in skill files; externalize those to facts documents. Portable workflow policy and numeric thresholds stay in the skill (see `learn` Step 2, Facts vs skill configuration).
- If the branch has no story key, use a plain descriptive commit message on branches such as `main` or `master`; ask only when the repository convention is unclear.
- No silent gate-satisfying rewrites of human-authored prose: when a gate or validator fails on prose the user authored, do not rewrite the passage wholesale and do not silently substitute its wording, punctuation, or structure. Make only the narrowly-scoped edit the gate actually requires, only inside the lines this run's own change touches (the hunks this run edited, not merely the same file), and report the edit in the return or commit summary; when the failures reach untouched user prose, or no minimal edit exists, stop and surface the conflict for the user to adjudicate (returned-for-ask shape: name the gate, the failing lines, and the options). Whole-file rewording of user-authored text is out of scope for any worker, always. Restoring the user's original text outranks a green gate. Text you authored this run is yours to fix freely; this pin never applies to it and never excuses stopping for routine fixable failures.
