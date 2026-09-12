---
name: done
description: >
  Finalize a development session by running the learn workflow to capture lessons, then committing
  all uncommitted changes across all repositories (project, skills, docs/facts). Use when the user
  signals a session is complete (e.g. "done", "commit", "wrap up"). This is the only skill that
  performs git commits, other skills (learn, review, etc.) make file changes but never commit.
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

**Workflow continuity:** This skill executes as a continuous sequence of steps (0 → 1 → 1.5 → 2.65 → 2.648 → 2.645 → 2.64 → 2.63 → 2.62 → 2 → 2.5 → 2.6 → 2.7 → 2.75 → 2.76 → 2.8 → 3 → 4 → 5 → 6 → 7). After each step or skill invocation completes, immediately proceed to the next step without stopping or waiting for user input. Only stop if a step fails, produces an error, or requires user clarification. **Exception:** Step 0 uses a short agent wait (`DONE_LOCK_AGENT_MAX_WAIT_SECS`, default 90s); on timeout return `blocked` with lock `status` instead of polling for hours. **An empty project working tree is not a stop condition:** still run Steps 2.65, 2.648, 2.645, 2.64, 2.63, 2.62, 2, and 6 and finish with Step 7.

## Configuration (from facts document)

| Key | Purpose | Fallback |
|-----|---------|----------|
| `skills_repo_path` | Path to the skills repository | `~/.agents/scripts/commit-skills.sh` default |
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
   if [[ -z "${DONE_LOCK_DIR:-}" || -z "${DONE_LOCK_TOKEN:-}" || -z "${DONE_LOCK_GENERATION:-}" ]]; then
     echo "done-lock: acquire succeeded without lock exports" >&2
     exit 1
   fi
   ```

   Install a trap in the controlling shell immediately after the successful
   acquire so an interrupted same-shell run attempts generation-fenced release:

   ```bash
   trap 'status=$?; if [[ -n "${DONE_LOCK_DIR:-}" && -n "${DONE_LOCK_TOKEN:-}" && -n "${DONE_LOCK_GENERATION:-}" ]]; then DONE_LOCK_DIR="$DONE_LOCK_DIR" DONE_LOCK_TOKEN="$DONE_LOCK_TOKEN" DONE_LOCK_GENERATION="$DONE_LOCK_GENERATION" "$LOCK_SCRIPT" release-repo || true; fi; exit "$status"' EXIT INT TERM
   ```

   The trap is a safety net, not a substitute for the explicit Step 6 release.

3. Keep `DONE_LOCK_DIR`, `DONE_LOCK_TOKEN`, and `DONE_LOCK_GENERATION` in scope when the same shell session runs multiple steps. **Across separate Shell tool calls**, re-export all three values from your Step 0 acquire stdout (chat context). The file `<repo>/.ai-playbook/done-lock.session` is a **fence/status** signal only; Step 6 `release-repo` requires env vars and will **not** source that file (confused-deputy guard after stale-clean / peer acquire).
4. If **wait-acquire** times out, run `status`, report the holder (`label`, `age_secs`, `holder_pid`, `holder_alive`, `stealable` / `abandoned`), return `blocked`, and **do not** commit. Do not bypass an active lock. Do **not** run `stale-clean` unless `status` shows the lock is stale/abandoned **and** you intend to take over; after `stale-clean`, only the chat that successfully re-acquires may release (using that acquire's token).
5. **Stealable locks** (auto-stolen on the next `acquire` / `wait-acquire` poll):
   - **Stale:** age ≥ `DONE_LOCK_STALE_SECS` (default 1800 = 30m) permits explicit `stale-clean`; age alone does not authorize automatic takeover.
   - **Abandoned:** lock metadata records a holder PID and process identity, independent process-table verification says that holder is dead, the `DONE_LOCK_DEAD_HOLDER_GRACE_SECS` grace period has elapsed, and there is no matching `<repo>/.ai-playbook/done-lock.session` for the lock generation.
   - **Blocked recovery:** a live holder with a missing or invalid fence, a reused PID, or an ambiguous holder identity is never auto-stolen.
   - **Session fence:** a dead `holder_pid` with a live matching session file is **not** auto-stealable, even after stale TTL (normal after one-shot Shell tool exits). Operator escape: `stale-clean` may remove a fenced lock when it is also stale. Step 6 releases only with the env token from **your** acquire.
6. Optional: pass a richer `--label` (plan slug, task id, review round) when the orchestrator provides context.

**After the lock is acquired, immediately continue to Step 1.** Do not run learn, docs-branch, or project commits before Step 0 succeeds.

**Run-start marker:** immediately after the lock is acquired, write a content-bearing per-run marker file under `{tmp_dir}/done-session/` named `run-start-<UTCtimestamp>` (filename format `run-start-YYYYmmddTHHMMSSZ`, UTC; create the directory if missing). Step 1.5 anchors this run's session window on the newest marker written by a previous done run. Marker pruning is governed solely by the Step 2.62 sweep. The marker is content-bearing: its single line records the creation epoch, the trailing-slash-stripped resolved `$REPO_TOP`, and the writing shell PID, so gate-time identity can rely on content-match confirmation instead of chat recall alone. Field order in the marker line: the first field is the epoch, the last field is the PID, and everything between them is the repo root (repo roots containing spaces therefore parse unambiguously).

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

Keep the echoed marker path in chat context; Step 1.5 (anchor discrimination) and the Step 2.62 sweep (current-run marker immunity) reuse it across separate shell calls. If it is lost or matches no marker at gate time, Step 1.5 treats the window as unanchorable (conservative gating) and the Step 2.62 sweep prunes no `run-start-*` markers this run; never guess by recency. This rule is the Step 0 echo-loss fallback that Step 1.5 back-references.

## Step 1: Run Learn

Invoke the `learn` skill now to extract lessons and update the documentation corpus before committing.

**If `learn` reports a blocked state** (Step 6.6 user-corpus violation: a strict-tagged `UL#N` lesson is missing its `**Principle:** Family X` tag, or the gate script returned non-zero on the adopted corpus), release the lock via Step 6 and return `blocked` WITHOUT proceeding to Step 2 commit. `learn` is invoked here as a SKILL (a sub-procedure), not as a subprocess whose exit code this step checks, so the gate's block decision lives in `learn`'s Step 6.6 text and propagates here through `learn`'s returned state. The operator fixes the user corpus out-of-band (classify the listed `UL#N` via learn/generalize, or run `lessons_adopt.py --tag-unclassified <user_corpus>` manually) before the next `done`.

**After learn completes, immediately continue to Step 2.65.** Do not stop or wait for user input; the workflow is continuous and all steps should execute in sequence.

## Step 1.5: Plan readiness gate (this session's plan deliverables)

This gate applies ONLY to plans that are **this session's deliverable**: a plan file under the resolved `{plans_dir}` that is untracked or modified relative to HEAD at done time (`git status --porcelain -- <plans_dir>`), or a plan path listed in `{tmp_dir}/done-session/plan-deliverables.txt` (one repo-relative path per line; ignore blank lines and `#` comments). Plain `git status --porcelain` is inert when `{plans_dir}` is gitignored (a shadow-path repo hides untracked plans), so also run the ignored-matching arm `git status --porcelain --ignored=matching -- <plans_dir>`; a plan the ignored arm lists with the ignored marker (`!!`) counts as a session-deliverable candidate when that same path is listed in `{tmp_dir}/done-session/plan-deliverables.txt` or its modification time falls inside the session window (an unlisted `!!` plan with a modification time outside the window belongs to its authoring session and gets no gate). The session window's anchor is the newest `run-start-` marker written by a previous done run under `{tmp_dir}/done-session/` (every done run writes its own marker at Step 0; the current run's own marker (identified by the marker path echoed at Step 0, re-read from chat context across shell calls) does not anchor its own window; if the echoed marker path is lost or matches no marker under `{tmp_dir}/done-session/` at gate time, apply the Step 0 echo-loss fallback (unanchorable window; the conservative-gating branch below applies); never substitute the newest on-disk marker; when the echoed marker file exists, confirm its identity from its content (the recorded `$REPO_TOP` must equal this repo's resolved repo root); recorded content naming a different repository is a cross-repo done run: the starting repo's marker cannot anchor this repo's window, so this repo's gate deterministically lands in the conservative-gating branch (expected and named for a secondary repo; the gate still names every gated plan and never silently skips one); the window runs from the anchor marker's timestamp to gate time). When no marker from a previous run exists at all, the window is unanchorable: apply conservative gating and treat every `!!` plan as this session's deliverable (the gate names each gated plan; it never silently skips them). **Producers (must run before this gate):** (1) any plan-file mutation under `{plans_dir}` (excluding `{plans_completed_dir}`) appends the path to `{tmp_dir}/done-session/plan-deliverables.txt` (create the directory/file if missing; one repo-relative path per line; skip duplicates) (the `plans` skill does this on every Write, Edit, or StrReplace; any other skill or tool that mutates a plan file under `{plans_dir}` does the same); (2) any `git commit` that stages `{plans_dir}` paths appends those paths in the same turn before `git commit` returns (binding agent commit hygiene; see Step 3 item 0b). It does NOT sweep every plan under `{plans_dir}`: committed stale plans this session never touched and never listed get **no gate and no refusal** (they belong to their authoring session), and `{plans_completed_dir}` is explicitly excluded even when nested under `{plans_dir}` (completed plans are archived, not pending). The gate does NOT apply while the mechanical `execute-plan` marker is present: `{tmp_dir}/execute-plan/<PLAN_SLUG>/manifest.md` exists and records `workflow_state: active` (gate on that marker, never on caller-identity prose) AND that manifest carries an `updated:` timestamp (ISO8601, refreshed by the orchestrator on every manifest update) no older than 24 hours at done time; a stale or abandoned manifest grants NO exemption: an active manifest with no `updated:` line, or one older than 24 hours, is stale: the exclusion does not apply and the gate runs (treat the run as interrupted-and-drifted: the non-stop path below is a fresh `review-plan` round of the current bytes). `<PLAN_SLUG>` = the candidate plan's basename without `.md`, same as execute-plan Step 0.4. A legitimate resumed run re-establishes the fresh witness via the orchestrator's resume-time manifest refresh (execute-plan Step 0.4: the first action on resume is updating the manifest's `updated:` timestamp and confirming `workflow_state: active`), not via per-task review rounds. Such runs' checkbox marks (`- [ ]` → `- [x]`) legitimately mutate the plan digest after the final review round, and that mutation is covered by `execute-plan`'s Phase 3 fresh-review rule, not by this gate; for checkbox drift on an interrupted `execute-plan` run (marker present, run stopped, plan bytes drifted beyond the Step 0.5 resume exemption), the non-stop path is a fresh `review-plan` round of the checkbox-marked bytes, which re-binds the digest. When the gate applies, verify plan readiness before finalizing; run this gate once per repo that has a resolved `{plans_dir}` (a done session may commit across multiple repos). Run the readiness validator with the project git root as cwd, resolving the script via env-var override with two fallbacks (repo-local copy if present, then the deployed runtime copy; this skill may run in any consumer repo, not only the repo that ships the script):

```bash
GATE_TOP="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
PLAN_READINESS_VALIDATOR="${PLAN_READINESS_VALIDATOR:-}"
if [ -z "$PLAN_READINESS_VALIDATOR" ] && [ -f "$GATE_TOP/scripts/plan_readiness.py" ]; then
  PLAN_READINESS_VALIDATOR="$GATE_TOP/scripts/plan_readiness.py"
  echo "readiness gate: using repo-local validator $PLAN_READINESS_VALIDATOR" >&2
fi
PLAN_READINESS_VALIDATOR="${PLAN_READINESS_VALIDATOR:-$HOME/.ai-playbook/scripts/plan_readiness.py}"
python3 "$PLAN_READINESS_VALIDATOR" <plan-path>
```

- **Exit 0:** the latest review of these exact plan bytes reports `ready=yes` with a valid sidecar; continue to Step 2.65. Removal rule for `{tmp_dir}/done-session/plan-deliverables.txt`: remove every line listing that path after it passes the gate, after it is exempted via the manifest marker (the `execute-plan` mechanical exemption above), or after it is recorded-stopped; and every line listing a path that no longer exists under `{plans_dir}` (e.g. it archived to `{plans_completed_dir}`) is skipped as archived, not gated, and likewise removed. This keeps a later `done` in the same chat from re-gating stale or already-exempted entries.
- **Non-zero exit:** **refuse to finalize**. Report the first failed readiness condition to the user and require a fresh `review-plan` round (after any plan edit that changes the digest) before re-running this gate. **Deployment-gap signature (narrow, r5 Y8):** a deployment gap is ONLY (a) the validator file itself missing or unopenable, or (b) a `ModuleNotFoundError` in the output. For either: stop and report the wiring gap, and never use the recorded-stop exception for it; manual remedy: `cp scripts/plan_readiness.py ~/.ai-playbook/scripts/` plus siblings (the script imports `validate_review_staging.py` and `facts_paths.py` from its own directory, so copy all three; the deployed `facts_paths.py` may be a symlink, keep it one, e.g. `cp -P`, do not dereference it into a second copy). Any OTHER non-zero exit that prints no `readiness FAILED:` line (validator crash, traceback, unexpected output) is NOT covered by that copy remedy: investigate the validator before re-running the gate.
- **Recorded-stop exception:** the only permitted way past a failed gate is when the user explicitly chooses to stop without finalization and that choice is recorded in the session log. In that case do not commit the plan deliverable: record the excluded plan path in the session log and, in this session's later commit-all steps, exclude exactly that path plus its review artifacts (the review Markdown and `.stats.json` sidecar under `{reviews_dir}`) when staging, then continue with the remaining hygiene steps and report the recorded stop in Step 7. Also remove every line listing the excluded path from `{tmp_dir}/done-session/plan-deliverables.txt` so it does not reappear as a gate target.

**After Step 1.5 completes (or does not apply), immediately continue to Step 2.65.**

## Step 2.65: Confluence mirror and ephemeral tmp hygiene

Before `docs-branch`, validate Confluence mirror state and handle ephemeral publish snapshots under `docs/tmp/`. **Never delete `*-cf-out.md` until audit confirms the content is already represented in the docs hierarchy or is a stale duplicate.**

**Run when any of these are true:**

- `docs/maintenance/confluence-sync-manifest.json` exists in the project repo
- This session created or updated files under `docs/history/context/confluence/`
- This session pushed or restored Confluence pages via Atlassian MCP
- Ephemeral files exist under `docs/tmp/` (`*-cf-out.md`, `__pycache__`)

**Skip** when none apply and `docs/tmp/` has no ephemeral publish snapshots.

```bash
HYGIENE="${CONFLUENCE_MIRROR_HYGIENE_SCRIPT:-${HOME}/.ai-playbook/scripts/confluence-mirror-hygiene.sh}"
```

1. **Audit before delete.** Classify each `docs/tmp/*-cf-out.md`:

   ```bash
   "$HYGIENE" audit-cf-out
   ```

   - **NEEDS_UPGRADE:** promote content into the docs hierarchy first:
     1. `docs/history/context/confluence/{page_id}-{slug}.md` with standard mirror frontmatter (verbatim wiki body)
     2. `layer2_targets` from `confluence-sync-manifest.json` when curated Layer 2 is authoritative
     3. Engineering spike sync ledgers (for example ADR-46 §Confluence sync ledger) when versions changed
   - **UNMAPPED:** route manually (new manifest entry, mirror file, or Layer 2 doc); do not delete.
   - **STALE:** safe to remove after promotion pass (older publish snapshot, subset of mirror, or superseded wording).

   Re-run `audit-cf-out` until exit 0 before cleanup.

2. When a manifest exists, run validation:

   ```bash
   "$HYGIENE" validate
   ```

   On failure, fix before `docs-branch` and re-run until exit 0:

   - Mirror files use standard YAML frontmatter (`confluence_page_id`, `confluence_title`, `confluence_version`, `confluence_url`, `space_key`, `synced_at`, `sync_status`, `layer2_targets`). Do not use a bare `path:` key.
   - Mirror filenames follow `{page_id}-{slug}.md`.
   - `docs/maintenance/confluence-sync-manifest.json` lists every mirror with matching `local_path`, versions, and `layer2_targets`.
   - `docs/history/context/confluence/README.md` indexes manifest pages.
   - Engineering spike docs with a Confluence sync ledger (for example ADR-46) match manifest `confluence_version` after an intentional wiki push (`sync_status: synced`). Use `pending` when repo mirrors are ahead of wiki per project-guidelines #92.

3. After a live Confluence push, refresh mirror bodies from the published wiki content (or authoritative repo spike sections), bump manifest versions, and set `sync_status: synced` in the same session. Do not leave truncated wiki pages; republish the full body before marking synced (via `confluence-page-sync`).

4. **Cleanup only after audit passes:**

   ```bash
   "$HYGIENE" cleanup
   ```

   Removes `__pycache__` always; removes `*-cf-out.md` only when step 1 marked them STALE. Aborts when promotion is still pending.

**After Step 2.65 completes, immediately continue to Step 2.648.**

## Step 2.648: Document registry hygiene

Before `docs-branch`, validate the document ownership registry and gate writes to completed-history paths. The registered-src exemption is bounded to the transition: the src of a registry row with `state: completed` or `superseded` is licensed only when its change type is an add or rename (`A`/`R`, the one-time archive move); the same src modified or deleted (`M`/`D`) is a hard finding unless the row carries an audit-note override, and a path fed without a change-type letter passes at warn tier with a verify duty. Unregistered paths under completed-history dirs and every other immutable write stay gated regardless of change type. Resolve the validator via the facts key (env-var override for local testing):

```bash
DOC_REGISTRY_VALIDATOR="${DOC_REGISTRY_VALIDATOR_SCRIPT:-${HOME}/.ai-playbook/scripts/doc_registry_validator.py}"
```

Fail-open semantics (matching pre-deploy vendored consumers):

- If the validator script itself is absent at the runtime path, report that once and continue to Step 2.645; do not block the commit on a missing deployment.
- If the registry file is absent at the resolved path, the validator reports the inventory hint (`inventory` lists unregistered completed-history files; the migration backlog owns them); report the hint once and continue.

Run, from the project git root:

1. **Registry integrity:**

   ```bash
   python3 "$DOC_REGISTRY_VALIDATOR" validate
   ```

2. **Immutable-path write gate**, when the session produced changed files:

   ```bash
   TMP_DIR_2648="$(sed -n 's/^tmp_dir = ["'\'']\(.*\)["'\'']$/\1/p' "$REPO_TOP/.ai-playbook/facts.md" 2>/dev/null | head -n 1)"
   SESSION_HEAD_FILE="${TMP_DIR_2648:-docs/tmp}/done-session/session-start-head.txt"
   if [ -f "$SESSION_HEAD_FILE" ]; then
     SESSION_START_HEAD="$(cat "$SESSION_HEAD_FILE")"
   fi
   BASE="${SESSION_START_HEAD:-ORIG_HEAD}"
   git rev-parse -q --verify "$BASE^{commit}" >/dev/null \
     || { echo "2.648: session-start base '$BASE' unresolvable; using HEAD as base for this run"; BASE="$(git rev-parse HEAD)"; }
   { git -c core.quotePath=false status --porcelain; git -c core.quotePath=false diff --name-status --no-renames "$BASE" HEAD; } | sort -u \
     | python3 "$DOC_REGISTRY_VALIDATOR" check-writes --stdin
   mkdir -p "$(dirname "$SESSION_HEAD_FILE")" \
     && git rev-parse HEAD > "$SESSION_HEAD_FILE"
   ```

   The final line re-anchors the session-base file at the end of this step: because the session's commits land in later steps, the recorded HEAD predates them, so the next run re-covers this session's commits (change types intact; freeze-move adds stay licensed) rather than missing them; fail-closed by design.

   Include changed files from every write state with their change type: the porcelain arm covers unstaged edits, staged changes, and untracked files (`XY PATH`, renames as `R old -> new`); the name-status arm covers changes committed since the session started (`A/M/D<TAB>path`), matching the union pattern used by the neighboring hygiene steps; skip the gate when nothing changed. The change-type letters are what bound the registered-src exemption to the archive transition, so never downgrade the union to name-only output. Trust boundary: the letters are asserted by the feeding command and are only as trustworthy as it; the validator does not re-derive them from git, so never feed it a hand-typed or filtered change list in place of the git commands above. The committed-since base is fail-loud and self-anchoring: read the previous run's HEAD from `{tmp_dir}/done-session/session-start-head.txt` when present, else `ORIG_HEAD` (on first adoption, before any session-base file exists, `ORIG_HEAD` is the only anchor and may point at a checkout/rewrite base rather than the true session start; the session-base file removes that limitation from the second run on); when the base does not resolve to a commit (fresh clone or init-only repo), say so and use the current HEAD as the base for this run so the arm degrades loudly, never silently. Run this step's commands in each repository named by the Step 0 inventory when the session touched more than one (the gate must run where the immutable paths live, not only where the latest artifact sits).

Result handling:

- **Warn-only findings** (including but not limited to stale aliases, legacy files without registry entries, dangling successors, multiply-claimed srcs, and the no-change-type-letter verify warn on registered srcs): report them in the step summary; they do not block. A standing-override warn carries a duty, not just information: clear the audit note after the licensed write lands so the guard is not left disarmed.
- **Hard findings** (including but not limited to registry parse errors, invalid `sot`/`state` values, malformed audit-note tokens, duplicate identities or SOT declarations, successor cycles, and unprotected writes to completed-history paths): stop and remediate before continuing, with the same stop semantics as the neighboring hygiene steps; fix the registry row or move the change into the living SOT instead of editing a completed artifact.

**After Step 2.648 completes, immediately continue to Step 2.645.**

## Step 2.645: Backlog inbox location gate

Before `docs-branch`, verify no backlog-inbox-shaped file sits outside the resolved backlog home. This is the mechanical second line of defense behind the `receiving-review` skill hardening (2026-08-30 invented-destination incident). Run it over the validator's full scan surface: rule 2 over the tracked tree plus rule 1 hot-dir filesystem walk (untracked and gitignored shadow-tree files included).

```bash
VALIDATOR="${BACKLOG_LOCATION_GATE:-$HOME/.ai-playbook/scripts/check_backlog_inbox_location.py}"
GATE_TOP="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
if [ ! -f "$VALIDATOR" ] && [ -f "$GATE_TOP/scripts/check_backlog_inbox_location.py" ]; then
  VALIDATOR="$GATE_TOP/scripts/check_backlog_inbox_location.py"
  echo "backlog gate: using repo-local validator $VALIDATOR" >&2
fi
if [ ! -f "$VALIDATOR" ]; then
  echo "warning: check_backlog_inbox_location.py not found; skipping backlog inbox location gate" >&2
else
  python3 "$VALIDATOR" || exit 1
fi
```

Fail-open rationale: the done skill is vendored to project repos where the copy-sync redeploy has not landed; a hard abort there would block every commit until an external redeploy. When a copy exists, the gate fails closed (`|| exit 1`).

On failure, remediate before continuing (disposition-dependent, never a silent move that misfiles real content): a file that is genuine backlog material moves into the resolved `{backlog_dir}` per `receiving-review` Backlog capture (rename to the `YYYY-MM-DD-<slug>.md` convention when needed); a legitimate Layer 2 doc that merely trips the filename shape is renamed to a compliant name, asking the user when the run is interactive.

**After Step 2.645 completes, immediately continue to Step 2.64.**

## Step 2.64: Review staging hygiene

When this session wrote or updated review staging docs under `{reviews_dir}/` (resolve from `.ai-playbook/facts.md` via `using-skills` Step 0), validate each session-touched staging file before `docs-branch` sync. Cover every review-staging kind: basename matches `*review*.md`, or PR staging names (`*-PR-*` / `PR-<n>-...` per `review-staging`), or any path accepted by the validator's `is_staging_review_path`. Do not filter to `*review*.md` alone; that misses PR staging.

```bash
VALIDATOR="${REVIEW_STAGING_VALIDATOR:-$HOME/.ai-playbook/scripts/validate_review_staging.py}"
# Only paths this session created or edited (do not glob all historical rounds)
for f in <session-touched-staging-paths>; do
  [ -f "$f" ] || continue
  python3 "$VALIDATOR" --hard "$f" || exit 1
done
```

On failure: complete the staging doc per `review-staging` (Metadata, Review Statistics, Findings with Comment/Analysis) before continuing. Do not sync stub staging docs to the orphan `docs` branch.

**After Step 2.64 completes, immediately continue to Step 2.63.**

## Step 2.63: Clean stale Vim swap files

Remove only verified stale Vim swap files before `docs-branch` snapshots ignored files. These files are editor recovery artifacts, not untracked work to preserve. Never delete a swap file for a live editor process or a file whose owner cannot be verified.

1. Find candidate swap files, excluding `.git`:

   ```bash
   find . -path ./.git -prune -o -type f \( -name '.*.swp' -o -name '.*.swo' -o -name '.*.swn' \) -print
   ```

2. For each candidate, run `file -- <path>`. Continue only when it identifies a `Vim swap file` and reports a PID.

3. Check the PID with `ps -p <pid> -o command=`.
   - If the PID is live and its command names the edited document, preserve the swap file and report it as active.
   - If the PID is dead, remove that exact candidate with `rm -f -- <path>` and report it as removed.
   - If the PID is live but the document does not match, or the header has no usable PID, preserve the file and report that cleanup needs manual confirmation.

4. Do not remove other untracked, ignored, backup, lock, or temporary files automatically. This cleanup is deliberately limited to verified stale Vim swaps.

**After Step 2.63 completes, immediately continue to Step 2.62.**

## Step 2.62: docs/tmp plan-lifetime sweep

`{tmp_dir}/` (resolve from `.ai-playbook/facts.md` via `using-skills` Step 0) is scratch with plan lifetime, not an archive: durable findings graduate into lessons, completed plans, or Layer 2 docs, and the rest dies with its owner. Sweep what outlived its owner before `docs-branch` snapshots it:

1. For each entry directly under `{tmp_dir}/`, classify and remove when its owner is finished:
   - `execute-plan/<slug>/` whose plan file is no longer under `{plans_dir}/` (it archived to `{plans_completed_dir}/`): remove the whole session dir.
   - `plan-requirements-<slug>.md` whose plan is in `{plans_completed_dir}/`: remove.
   - `review-loop*`, `code-review/`, `handoff/` scratch: leave in place. A plan-less review loop has no liveness witness (the plan check cannot see it), and `done` runs inside review-loop's own fix cycles, so removing these here can delete an ACTIVE loop's unsynced staging. Their owning skills (review-loop, doing-code-review, handoff) remove them when their staging is final.
   - `done-session/`: owned by `done`. Remove `run-start-*` markers strictly older than the newest marker written by a previous done run; NEVER remove the newest previous-run marker (it is this run's session-window anchor) or the current run's marker (it is the next run's anchor). `plan-deliverables.txt` is governed by the Step 1.5 removal rule, not this sweep. If the echoed marker path is lost or matches no marker under this directory, prune no `run-start-*` markers this run (never guess by recency). Confirm the recalled current-run marker from its content the same way: a recorded `$REPO_TOP` matching this repo is the confirmable field, and the run-unique epoch and PID are recorded for post-hoc audit rather than gate-time comparison; a content mismatch applies the same no-prune rule as a lost echo.
   - One-off scripts and log notes (`.py`, `*.log.md`, dated one-off `.md`) with no pointer from a tracked doc and not from the current session: remove.
   - Anything else (unclear ownership, active work): leave in place and report it.
2. Never remove an ACTIVE `execute-plan` session: its dir contains `manifest.md` and its plan still sits under `{plans_dir}/`.
3. Sweep without prompting; removals stay recoverable from the `docs` branch history (the sweep deletion's parent commit) **only when a prior sync captured them**; a never-synced file's removal is permanent, so when presence on `refs/heads/docs` is uncertain, skip the file and report it instead. Report the removed list in the step summary.
4. Deletion propagation is the `docs-branch` sync's job (its `{tmp_dir}` sweep-eligible root drops branch copies in the same Step 2 run); do not hand-edit the docs branch here.

**After Step 2.62 completes, immediately continue to Step 2.**

## Step 2: Preserve Gitignored Docs and Instructions

Invoke the `docs-branch` skill now. It will:
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

## Step 2.7: Sensitive Data and Personal Information Scan

Before committing, scan all uncommitted changes (including untracked files) for sensitive or personal information that must not appear in public repositories.

**Check for:**
- Hardcoded absolute paths containing usernames (e.g., `<home>/username/` paths)
- Organization-specific domains, internal URLs, or service names
- Employee names, email addresses, or identifiers (except copyright lines in `LICENSE.txt`)
- API keys, tokens, passwords, or credentials
- Project-specific ticket prefixes or internal naming that reveals client/employer identity
- Environment names or internal infrastructure references
- `Co-authored-by:` / `Co-Authored-By:` trailers in commit messages being pushed
- Employer or client brand names in commit subjects (especially in vendored skills)

**How to scan:**
1. List all changed/untracked files: `git status --short`
2. For each file in the diff, grep for patterns:
   ```bash
   git diff --cached -U0 | grep -iE '/Users/|/home/|\.atlassian\.net|@[a-z]+\.(com|io|net)|api[_-]?key|token|password|secret'
   ```
   Also run `public_hygiene_scan_script` from user facts (deny patterns: `public_hygiene_patterns_file`).
3. For untracked files being staged, scan their full content.
4. When a push is planned, audit commits in the push range (`origin/<branch>..HEAD` or the squashed commit about to be pushed):
   ```bash
   git log origin/<branch>..HEAD --format='%B---' | grep -iE 'Co-authored-by|Co-Authored-By|<employer-brand-from-facts>'
   git log origin/<branch>..HEAD --format='%s' | grep -iE '<employer-brand-from-facts>'
   rg -i '<employer-brand-from-facts>' --glob '!**/LICENSE.txt' agents/skills/
   ```
   Resolve employer-brand patterns from the user's facts document; never hardcode them in skill files.

**If found:**
- Replace personal paths with facts-document references or generic placeholders (e.g., `<your-org>.atlassian.net`, `~/Projects/<project>/`)
- Replace internal names with generic equivalents
- Move credentials to `.env` or facts documents (never commit them)
- If the information is in a skill file, externalize **machine-specific** values to facts documents; keep **portable policy constants and workflow thresholds** in the skill body (see `learn` Step 2, Facts vs skill configuration; `agent_workflow_guidelines.md` §50).

**When committing this repository (`skills_repo_path`) or vendored skills:** run `public_hygiene_scan_script` from user facts at the instructions repo root and fix all failures before staging.

**Do NOT commit until all sensitive data is resolved.**

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

**After Step 2.75 completes, immediately continue to Step 2.76.**

## Step 2.76: No em dash scan (touched prose files)

Before committing, scan touched prose and instruction files for em dash (U+2014). Policy: `agent_workflow_guidelines.md` §39.

1. From the repo root (or each repo you will commit), run:
   ```bash
   "${CHECK_NO_EM_DASH_SCRIPT:-${HOME}/.ai-playbook/scripts/check-no-em-dash.sh}" touched
   ```
2. The script scans `*.md`, `*.mdc`, and instruction entrypoint filenames among touched paths. Fix every reported line: use a comma, colon, semicolon, period, or parentheses instead of a long dash.
3. Re-run until exit code 0.

Do not stage prose or instruction files while the scan fails.

**After Step 2.76 completes, immediately continue to Step 2.8.**

## Step 2.8: Instruction Size Gate (before commit)

When uncommitted changes touch always-loaded instruction entrypoints (`AGENTS.md`, `CLAUDE.md`, and others listed in `user_facts_path` when present), verify they still fit the context budget after learn compaction.

**Budget:** **30,720 bytes** per instruction entrypoint (same constant as learn Step 6.5).

1. From the repo root, run:
   ```bash
   "${HOME}/.ai-playbook/scripts/check-instruction-size.sh" gate
   ```
   (Override script path only for local testing via `INSTRUCTION_SIZE_CHECK_SCRIPT`.)
2. **Gate behavior:** exits non-zero when an instruction file exceeds the budget **and** has uncommitted changes. Grandfathered over-budget files with no pending edits do not block unrelated commits.
3. On failure: return to learn Step 6.5, compact hybrid bullets to cross-references, move infrequent rules to skills, then re-run **gate** before staging instruction files.

Do not stage instruction entrypoints for commit while **gate** fails.

**After Step 2.8 completes, immediately continue to Step 3.**

## Step 3: Commit Uncommitted Changes

After learn and stash steps complete:

0b. **Plan-deliverable append (producer 2 for Step 1.5):** Before any `git commit` in this session that stages paths under `{plans_dir}` (excluding `{plans_completed_dir}`), append each staged plan path to `{tmp_dir}/done-session/plan-deliverables.txt` (create dir/file if missing; one repo-relative path per line; skip duplicates). Do this in the same turn as the commit, including when the commit is not part of `done`.

0. **Distinguish session changes from pre-existing local changes.** Only commit changes that were made during this session. If `git status` shows uncommitted files that were not touched by you in this session, ask the user before staging them; they may be in-progress work the user does not want committed yet. For cleanup or restoration sessions, capture the dirty-tree and untracked-file baseline before the first edit: always record the git status --porcelain baseline in the session notes before the first edit; additionally run the cleanup baseline checker scripts/check_cleanup_scope_baseline.py against the task's scope ledger when the task's scope ledger exists (resolve the skills repo checkout from the skills-repo path key in the user facts document and pass this repo via --repo-root). Refuse to stage any path that was already dirty or untracked at baseline unless the user explicitly includes it. Checker exit codes: exit 1 means a path outside the ledger is dirty or deleted, so ask the user before staging it; exit 2 means the checker could not run, so fall back to the recorded session-notes baseline; if the checker exits 2 and no recorded baseline exists, ask the user before staging any path not created or modified this session. Run the checker before the first commit of the session for full coverage; after commits exist, only deletions remain checkable (against the ledger's session-start base ref, never with `--base HEAD`), because committed non-deletion sweeps are invisible at any base ref once committed: assess committed modifications from the recorded session-notes baseline instead. If no pre-edit baseline exists at done time (whatever the reason: checker never run, exit 2 with no recorded baseline, or baseline recorded after edits), ask the user before staging any path not created or modified this session; a baseline recorded after edits is not a baseline. Checker limitations: it cannot see gitignored files (capture the ignored set with `git status --porcelain --ignored` and record those paths in the session notes explicitly), and it matches allow-list paths byte-exact relative to the repo root (no `./` prefix). If the skills-repo path key is missing or unresolvable, record the session-notes baseline and note that the checker was skipped.
1. Run `git status` and `git diff` (staged + unstaged) to see all changes.
   **Pre-commit guard (post sub-agent git op):** Step 2 `docs-branch` (and any prior sub-agent `git worktree`/`git checkout`/`git stash` operation) can leave the main repo's index/worktree in a REVERTED state relative to HEAD while HEAD stays correct. Before staging, run `git diff --cached --stat`: if it shows large deletions across files you did not edit this iteration (e.g. +73/-1062 across 14 files) OR the test count dropped vs the last known-good count on HEAD, a leaked revert is staged. Run `git reset --hard HEAD`, re-stage only your intended edits, then re-verify. Never use `git add -A`/`git add .` here, or the rollback is swept into the commit. (Witness: 2026-07-23 group-leftover-crypto-warnings r6; see project `development_lessons.md` lesson on this family.)
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
   1. **Mechanical duplicate check.** First resolve the company guidelines master (`company_guidelines_master` in facts); if it does not resolve (personal repo), the mechanical check passes trivially (do not run the script). Otherwise verify the validator script file exists (e.g. `test -f` on the resolved path); if it is absent, print a one-line warning and continue with the placement-evidence check (cold-start; do not block the session on a missing optional validator). Only when the file exists, run the validator with stderr captured (with `$PROJECT_CORPUS` and `$COMPANY_MASTER` set to the resolved corpus and master paths; override the script path via `LESSON_SCOPE_SCRIPT` for local testing only):
```bash
python3 "${LESSON_SCOPE_SCRIPT:-${HOME}/.ai-playbook/scripts/check_lesson_scope.py}" "$PROJECT_CORPUS" "$COMPANY_MASTER"
```
       Outcome semantics: exit 0 with no WARNING line on stderr = clean pass, covering rules of at least 25 normalized words (the witness-pointer floor: shorter blocks are presumed witness pointers and never match). Exit 1 with at least one `DUPLICATE:` line = a full rule is duplicated across the project corpus and the company master (handled by item 3 below). Any WARNING line on stderr, any exit code other than 0 or 1 (including exit 2 and interpreter codes such as 126 or 127), or exit 1 with no `DUPLICATE:` line, is a tool failure: stop, report the validator error, release the lock per Step 6, and return blocked; do not stage the corpus. The validator is sized for prose corpora; an unusually long run signals a degenerate (for example fence-damaged or headingless) corpus and is treated as a tool failure per the sentence above. `$COMPANY_MASTER` must resolve to the canonical master from facts, never a repo mirror.
   2. **Placement-evidence check.** Confirm the learn run's placement receipt (`learn` Step 1.2 item 5c) covers every new or substantially edited lesson. If a lesson has no receipt, or its scope cannot be established from the receipt, stop before commit and request classification from the user; do NOT silently commit the narrower placement. For a fork (4) lesson, the receipt must state the residual dependency; a fork (4) receipt with no residual dependency stops before commit for reclassification, exactly like a missing receipt.
   3. **On exit 1 with at least one `DUPLICATE:` line (duplicate full rule):** stop before commit, release the lock per Step 6, and return blocked with the validator output; ask the user to classify the lesson (company master vs project corpus). Never move, rewrite, or duplicate lessons automatically.
   4. **Commit boundary:** the project witness and the company guidelines change are committed in the same pass ONLY when both were intentionally produced by the same workflow (`learn` placed them deliberately). done must not move or duplicate lessons to reconcile placements.
4b. **Session-touched project lessons corpus (non-ignored):** After Step 1 (`learn`), if this session created or updated the project lessons file (`docs/maintenance/development_lessons.md`, or `PROJECT_CORPUS_REL` from `lessons_recall.py`) and `git check-ignore` does **not** match it, **stage and commit it on the feature branch** with the other session changes. Untracked (`??`) is not a skip reason. Syncing the same path to the orphan `docs` branch in Step 2 does **not** replace the feature-branch commit. Only gitignored corpora stay docs-branch-only.
5. Stage relevant non-ignored files (including 4b when it applies). Prefer adding specific files by name; never use `git add -A` or `git add .` unless the user explicitly requests it.
6. Write a concise commit message. If there is a story key, prefix with `[<STORY-KEY>]`; otherwise use a plain descriptive subject. Focus on the "why" not the "what".
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

## Step 4: Commit Pending Skill Changes

After committing the current project, check whether any skills were modified during this session:

```bash
cd <skills_repo_path> && git diff --name-only -- agents/skills/
```

Resolve `<skills_repo_path>` from the user's facts document (key: `skills_repo_path`). If not found, check `~/.agents/scripts/commit-skills.sh` for the default path, or ask the user.

If there are changes, run:

```bash
<skills_repo_path>/scripts/commit-skills.sh
```

This commits any pending skill edits in the skills repository with an auto-generated message. You may pass a custom message as the first argument if the default is not descriptive enough.

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

From the project git root, release with **`DONE_LOCK_DIR`, `DONE_LOCK_TOKEN`, and `DONE_LOCK_GENERATION` from your Step 0 acquire** (re-export from that tool output if the shell lost env). `release-repo` requires those env vars and refuses to load the shared session file:

```bash
DONE_LOCK_DIR="${DONE_LOCK_DIR:?}" DONE_LOCK_TOKEN="${DONE_LOCK_TOKEN:?}" DONE_LOCK_GENERATION="${DONE_LOCK_GENERATION:?}" \
  "${DONE_LOCK_SCRIPT:-${HOME}/.ai-playbook/scripts/done-lock.sh}" release-repo
```

Equivalent:

```bash
DONE_LOCK_DIR="${DONE_LOCK_DIR:?}" DONE_LOCK_TOKEN="${DONE_LOCK_TOKEN:?}" DONE_LOCK_GENERATION="${DONE_LOCK_GENERATION:?}" \
  "${DONE_LOCK_SCRIPT:-${HOME}/.ai-playbook/scripts/done-lock.sh}" release
```

If release fails (token mismatch, env missing), run `status` from the project root. When `status` shows free, your hold is already gone (peer `stale-clean` or release); do not source `.ai-playbook/done-lock.session` to “fix” env. When `status` shows `abandoned: yes` with no session fence, run `stale-clean` only if you will re-acquire; ask the user before forcing removal of an **active** lock.

## Step 7: Report outcome to the user

**Never end `/done` silently after diagnostics.** Always send a short summary:

- Project repo: commit hash(es) created, or **working tree clean** at `HEAD` (include `git log -1 --oneline`).
- Skills / shared docs repos: commits created or none.
- Lock: confirm `status` shows **free** after Step 6.
- If `blocked` at Step 0, learn, or the Step 3 item 4a lesson scope audit: state why and what the user should run (`stale-clean`, fix corpus, classify the duplicated lesson, retry).

## Integration Points

### With `bootstrap-ai-playbook` skill
Writes and refreshes `.ai-playbook/facts.md` when Terms triggers fire (`using-skills` Step 0). This skill reads `{tmp_dir}` and other gitignored doc paths from that file for Step 2.1 (`docs-branch`).

### With `execute-plan` skill
Invoked as a sub-agent after **each** completed plan task (per-task commit) and after **each** review/fix iteration (per-iteration commit). The orchestrator passes the plan path, task or review-round context, suggested commit subject, and **sub-agent log paths** under resolved `{tmp_dir}/execute-plan/<plan-slug>/`.

**Before Step 1 (learn):** read only the **preceding-step** log(s) the orchestrator listed: for per-task `done`, the implement log from Step 1.2; for review-iteration `done`, the current round's review log (Step 3.1) and address log (Step 3.3) when it ran. Do not read full session history. Use log content as primary input for `learn`, not the orchestrator chat summary. If a required preceding-step log is missing, release the Step 0 lock (Step 6), return `blocked`, and do not commit. See `execute-plan/agent-logs.md`.

Each execute-plan `done` sub-agent still runs Step 0 and Step 6. Sequential tasks in one orchestrator usually acquire immediately after the prior release; parallel chats on the same repo wait on **wait-acquire**.

### With `review-staging` skill
Step 2.64 validates session-touched staging docs under `{reviews_dir}/` before docs-branch sync. Include `*review*.md`, PR staging (`*-PR-*` / `PR-<n>-...`), and any path accepted by `is_staging_review_path` (not only `*review*.md` or `*-r*.md`). Complete Metadata, Review Statistics, and Findings with Comment/Analysis before continuing; do not sync stub staging docs.

### With `plans` and `docs-branch` skills (docs/tmp sweep)
Step 2.62 sweeps `{tmp_dir}` entries whose owning plan archived (plans Plan Lifecycle cleanup) or that are one-off ownerless scratch; `review-loop*`/`code-review/`/`handoff/` scratch is never swept here (no liveness witness; their owning skills clean up). The `docs-branch` sync then drops branch-tracked `{tmp_dir}` paths absent on disk (`{tmp_dir}` is its one sweep-eligible root), so branch copies propagate without hand-editing the docs branch.

## Rules

- Always acquire the Step 0 project lock before learn or any project-side commit steps; always release it in Step 6 (`release-repo` from project git root).
- Never skip Step 6 or Step 7, even for "just commit" or empty working tree runs.
- Always run learn before committing; lessons must be captured first.
- Never skip the learn step even if the user says "just commit".
- Invoke `docs-branch` skill for all docs/instructions preservation; do not inline the stash or branch logic here.
- Run Step 2.65 (Confluence mirror validate, audit-cf-out promotion gate, ephemeral `docs/tmp` cleanup) before `docs-branch` when the manifest exists or the session touched Confluence mirrors, wiki pages, or ephemeral publish snapshots.
- Always verify that new or revised reusable docs, reference material, and explanatory artifacts added in the session are referenced from instructions or related canonical docs where future agents will need them.
- Never stage or commit a file that is gitignored, even if it appears in `git diff` (it was previously force-tracked). Use `git rm --cached` to remove it from tracking; do not commit it on the feature branch.
- Never skip a session-touched, non-gitignored project lessons corpus (`development_lessons.md`) just because it is untracked or already synced to the orphan `docs` branch; commit it on the feature branch (Step 3 item 4b).
- Never commit a new or substantially edited project lesson whose scope audit (Step 3 item 4a) has not passed.
- Never add `Co-Authored-By:` or `Co-authored-by:` trailers or use `git commit --trailer` for agent attribution. See user `AGENTS.md` (Git Commit Trailer Policy). Disable automatic agent attribution in IDE settings when present.
- Never use `--no-verify`.
- Never commit secrets, PII files (`.env`, credential files), or personal/org-specific information into public repositories.
- Never hardcode personal paths, org domains, or project-specific identifiers in skill files; externalize those to facts documents. Portable workflow policy and numeric thresholds stay in the skill (see `learn` Step 2, Facts vs skill configuration).
- If the branch has no story key, use a plain descriptive commit message on branches such as `main` or `master`; ask only when the repository convention is unclear.
