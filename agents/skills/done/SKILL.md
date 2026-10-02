---
name: done
description: >
  Finalize a development session by running the learn workflow to capture lessons, then committing
  all uncommitted changes across all repositories (project, skills, docs/facts). Use when the user
  signals a session is complete (e.g. "done", "commit", "wrap up").
  This skill owns all git commits except learn's own learn-authored skills-repo artifacts
  (learn Step 1.8 and the learn skill-placement commit workflow; artifacts in the
  failed-capture set (done Step 4) may be staged by Step 4 after asking) and the docs-branch skill's
  orphan-branch commits, and the release skill's own CHANGELOG notes commit (created inside a
  release run); other skills (review, etc.) make file changes but never commit.
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
- **Edit discipline:** read-before-edit is mandatory per file per session; Read a file in this session before this workflow's first edit to it, and re-Read it after any external-change signal, including a peer commit, a plan fold, a formatter run, docs-branch operations, a sweep-gate operation, or a `modified since read` failure; on such a failure, re-Read the file before retrying the edit.

**Workflow continuity:** This skill executes as a continuous sequence of steps (0 → 1 → the pre-docs sweep gate run → 2 → 2.5 → 2.6 → 2.75 → the pre-commit sweep gate run → 3 → 4 → 5 → 6 → 7); the 0c and 0d adjudications run inside Step 3 before item 1's gates; the two sweep gate runs are the `done_sweep_gates.sh` phases (`pre-docs`, `pre-commit`) and carry no fixed step numbers. After each step or skill invocation completes, immediately proceed to the next step without stopping or waiting for user input. Only stop if a step fails, produces an error, or requires user clarification. **Exception:** Step 0 uses a short agent wait (`DONE_LOCK_AGENT_MAX_WAIT_SECS`, default 90s); on timeout return `blocked` with lock `status` instead of polling for hours. **An empty project working tree is not a stop condition:** still run the pre-docs sweep gate run (`done_sweep_gates.sh pre-docs`), Step 2, and Step 6 and finish with Step 7.

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

Before Step 0, in a repository that resolves the maintenance skill, run the rearm-on-touch check defined in the maintenance skill's Step 0 through its mechanical script, from the project git root: `python3 "${REARM_ON_TOUCH_SCRIPT:-${HOME}/.ai-playbook/scripts/rearm_on_touch.py}"` (a repo-local `scripts/rearm_on_touch.py` copy wins when present), passing `--listing-json <path|->` when an automation listing was fetched as decision input. The escalation contract is echo-and-continue: echo the verdict in the Step 7 report (the class, any bookkeeping edits it applied, the skipped-reason, or the error evidence) so a skipped or failed check is visible in the run record, and never block the commit path on it: a failed check is advisory, matching the scheduler state file's advisory status and the sibling fail-open hygiene gates. The check answers in the outcome contract's four-outcome vocabulary (scripts/OUTCOME_CONTRACT.md): every classified verdict (any class, a skip included) exits 0 with a final `OUTCOME: pass` line after the verdict JSON (the machine-readable payload stays parseable; a classification that ran is a pass on the exit channel even when the verdict calls for a re-arm), exit 3 with `OUTCOME: tool_error` is the malformed-or-failed shape (an unparseable state or listing file, a refused structural edit, an unexpected internal error, or a usage violation), and a run that ends with no final `OUTCOME:` line is tool error per the contract's no-line rule: re-derive the state file from disk before echoing any verdict as decided. The script classifies, books, and decides but never calls automation primitives, so perform any listing or re-arm the verdict calls for per the maintenance skill before continuing.

## Step 0: Acquire project done lock

Parallel agent sessions on the **same git repository** must not run `learn`, `docs-branch`, or project commits at the same time. Acquire an exclusive per-repo lock **before** Step 1.

**Lock matrix (two lock families, one script):** the done lock stays keyed **per-worktree** (`git rev-parse --show-toplevel`) and serializes one checkout's done run end to end (sweep gates, learn, project commits); the merge lock (the `merge-*` commands of the same script) is keyed **per-repository** (the resolved git common dir, shared by every linked worktree of one repository) and serializes only shared-checkout critical sections: the Step 2 docs-branch sync and ad-hoc-worktree migration, plus landing critical sections owned by other workflows. Authoring work confined to separate worktrees requires neither lock: per-worktree done runs do not contend with each other, and their shared-checkout writes meet only inside the merge lock's critical sections. The lock commands, exit codes, and stale/steal semantics are owned by the `scripts/done-lock.sh` usage text (the merge lock's canonical home); the maintenance overlay's Merge landing lock paragraph (`agents/skills/maintenance/zcode.md`) mirrors the same semantics for the scheduler lanes. This skill links to both and does not restate them.

**Run placement (compute anywhere, corpus in the primary):** done compute steps may run in any checkout of the repository (the primary checkout is this skill's main checkout); the done lock keys per checkout, so done runs in different checkouts serialize independently and need no cross-checkout coordination beyond the merge lock's shared-checkout sections. The corpus steps resolve the primary checkout regardless of where the run executes: the Step 0d reviews-corpus read, the Step 2 migration destination, the docs-branch sync, and the {tmp_dir}/done-session/ artifact corpus are primary-checkout surfaces by design (witnessed inventory 2026-10-01: 57 primary-rooted done runs all completed while the interrupted-run pile is worktree-rooted). The primary checkout is the default dispatch placement for a done closeout; an ad-hoc-worktree done run is sanctioned per the project worktree policy below and owes the Step 2 transfer-out ordering before its worktree is removed. A done closeout consults the project worktree policy per the Worktree-first standard's policy paragraph before provisioning or adopting any worktree: the arm follows that paragraph's resolutions (an explicit user request for isolation in this run, or the paragraph's opt-in warrant for the named lanes; a disabling project's non-lane closeout resolves to the primary checkout with the placement reported in the run record; no policy ever skips the transfer-out ordering or the migration-before-removal rule). This paragraph also fixes scope for any landing rule that restricts staging in the primary checkout: such rules own the landing critical sections the lock matrix assigns to other workflows, and a done run's corpus writes and its own staging under the foreign-dirt gate's owned-path attribution are not landing staging.

1. From the project git root (`git rev-parse --show-toplevel`), run **`status`** first (non-blocking) so a held lock is visible before waiting.

2. Acquire with a **short agent wait** (do not use the script default 7200s in agent sessions):

   ```bash
   LABEL="$(git branch --show-current 2>/dev/null || echo unknown-branch)"
   MAX_WAIT="${DONE_LOCK_AGENT_MAX_WAIT_SECS:-90}"
   LOCK_SCRIPT="${DONE_LOCK_SCRIPT:-${HOME}/.ai-playbook/scripts/done-lock.sh}"
   LOCK_ERR="$(mktemp)"
   if ! LOCK_EXPORTS="$("$LOCK_SCRIPT" wait-acquire --label "$LABEL" --max-wait "$MAX_WAIT" 2>"$LOCK_ERR")"; then
     "$LOCK_SCRIPT" status >&2
     # The lock script reports the outcome contract (scripts/OUTCOME_CONTRACT.md):
     # read the final OUTCOME line from STDERR (the acquire subcommands print it
     # there; their stdout is eval-consumed exports only) together with the exit code.
     case "$(grep -E '^OUTCOME: ' "$LOCK_ERR" | tail -n1)" in
       "OUTCOME: fail")
         echo "done-lock: blocked after ${MAX_WAIT}s; another done holds the lock" >&2
         echo "done-lock: if holder PID is dead or lock is stale, run: $LOCK_SCRIPT stale-clean" >&2
         ;;
       "OUTCOME: indeterminate")
         echo "done-lock: holder state ambiguous; the hold cannot be adjudicated: report and stop (stale-clean stays the explicit operator escape only)" >&2
         ;;
       *)
         # OUTCOME: tool_error, or no final OUTCOME line at all: tool error
         # under the outcome contract, never a hold.
         echo "done-lock: lock tool error (outcome: $(grep -E '^OUTCOME: ' "$LOCK_ERR" | tail -n1) ); fix the invocation or environment and re-derive from disk with status" >&2
         ;;
     esac
     rm -f "$LOCK_ERR"
     exit 2
   fi
   grep -qx 'OUTCOME: pass' "$LOCK_ERR" || {
     echo "done-lock: acquire emitted no final OUTCOME: pass on stderr; treating as tool error" >&2
     "$LOCK_SCRIPT" status >&2
     rm -f "$LOCK_ERR"
     exit 2
   }
   rm -f "$LOCK_ERR"
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
4. If **wait-acquire** times out, run `status`, report the holder (`label`, `age_secs`, `holder_pid`, `holder_alive`, `stealable` / `abandoned`), return `blocked`, and **do not** commit. Read the lock script's result through the outcome contract (`scripts/OUTCOME_CONTRACT.md`): exit 0 with `OUTCOME: pass`; exit 1 with `OUTCOME: fail` (held, or the wait exhausted; the holder evidence precedes the line); exit 2 with `OUTCOME: indeterminate` (ambiguous holder: a meta-less lock past the incomplete age, or an unverifiable holder identity; stop and report, never auto-adjudicate); exit 3 with `OUTCOME: tool_error` (usage or environment; fix the invocation and re-derive from disk, never report it as a hold). The acquire subcommands print the `OUTCOME:` line on stderr because their stdout is eval-consumed exports only, and a run with no final `OUTCOME:` line is tool error under the contract: stop and re-derive the state from disk. Do not bypass an active lock. Do **not** run `stale-clean` unless `status` shows the lock is stale/abandoned **and** you intend to take over; after `stale-clean`, only the chat that successfully re-acquires may release (using that acquire's token).
5. **Stealable locks** (auto-stolen on the next `acquire` / `wait-acquire` poll):
   - **Stale:** age ≥ `DONE_LOCK_STALE_SECS` (default 1800 = 30m) permits explicit `stale-clean`; age alone does not authorize automatic takeover.
   - **Abandoned:** lock metadata records a holder PID and process identity, independent process-table verification says that holder is dead, and the `DONE_LOCK_DEAD_HOLDER_GRACE_SECS` grace period has elapsed. A matching `<repo>/.ai-playbook/done-lock.session` does not prevent reclaiming a verified-dead holder.
   - **Blocked recovery:** a live holder with a missing or invalid fence, a reused PID, or an ambiguous holder identity is never auto-stolen.
   - **Session fence:** the session file is a fence/status signal, not proof that its owner is alive. A verified-dead `holder_pid` is auto-reclaimed after the dead-holder grace period even when the matching session file remains (normal after one-shot Shell tool exits). A live or ambiguous holder remains protected, and `stale-clean` is the operator escape for stale locks without a verified-dead owner. Step 6 releases only with the env token from **your** acquire.

**One-shot holders and peer reclaim:** a one-shot shell holder goes dead when its acquiring call finishes (the Variant B `DONE_LOCK_HOLDER_PID` pin exists to keep a long-lived process in the holder role instead), a live peer may reclaim the abandoned hold after the dead-holder grace period, and a token-fenced release from the original run is then refused with a token mismatch. That refusal is the expected witness of a peer reclaim, not a fault: record the witness and proceed (never bypass the fence or re-acquire); nothing is left to release because the hold now belongs to the reclaiming peer. The reclaim and release-refusal semantics are owned by the `scripts/done-lock.sh` usage text.
6. Optional: pass a richer `--label` (plan slug, task id, review round) when the orchestrator provides context.

**After the lock is acquired, immediately continue to Step 1.** Do not run learn, docs-branch, or project commits before Step 0 succeeds.

**Run-start marker:** immediately after the lock is acquired, write a content-bearing per-run marker file under `{tmp_dir}/done-session/` named `run-start-<UTCtimestamp>` (filename format `run-start-YYYYmmddTHHMMSSZ`, UTC; create the directory if missing). The pre-docs sweep gate run's plan-readiness gate anchors this run's session window on the newest marker written by a previous done run. Marker pruning is governed solely by the docs-tmp-sweep gate. The marker is content-bearing: its single line records the creation epoch, the SHA-256 hex digest of the trailing-slash-stripped resolved `$REPO_TOP`, and the writing shell PID, so gate-time identity can rely on content-match confirmation instead of chat recall alone. The raw repo-root path is never recorded. Field order in the marker line: the first field is the epoch, the last field is the PID, and everything between them is the digest (a single 64-character token, so the middle field parses unambiguously).

```bash
REPO_TOP="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
TMP_DIR="$(sed -n 's/^tmp_dir = ["'\'']\(.*\)["'\'']$/\1/p' "$REPO_TOP/.ai-playbook/facts.md" 2>/dev/null | head -n 1)"
TMP_DIR="${TMP_DIR:-$REPO_TOP/docs/tmp/}"
case "$TMP_DIR" in /*) ;; *) TMP_DIR="$REPO_TOP/$TMP_DIR";; esac
mkdir -p "${TMP_DIR%/}/done-session"
MARKER="${TMP_DIR%/}/done-session/run-start-$(date -u +%Y%m%dT%H%M%SZ)"
MARKER="$(cd "$(dirname "$MARKER")" && pwd)/$(basename "$MARKER")"
REPO_HASH="$(printf '%s' "${REPO_TOP%/}" | (shasum -a 256 2>/dev/null || sha256sum) | awk '{print $1}')"
printf '%s' "$REPO_HASH" | grep -qE '^[0-9a-f]{64}$' || { echo "run-start marker: sha256 tool missing or malformed digest" >&2; exit 1; }
printf '%s\n' "$(date -u +%s) $REPO_HASH $$" > "$MARKER" && printf 'run-start marker: %s\n' "$MARKER"
# Post-write location self-check: independent fresh parse, resolved-path compare.
TMP_DIR_FRESH="$(sed -n 's/^tmp_dir = ["'\'']\(.*\)["'\'']$/\1/p' "$REPO_TOP/.ai-playbook/facts.md" 2>/dev/null | head -n 1)"
TMP_DIR_FRESH="${TMP_DIR_FRESH:-$REPO_TOP/docs/tmp/}"
case "$TMP_DIR_FRESH" in /*) ;; *) TMP_DIR_FRESH="$REPO_TOP/$TMP_DIR_FRESH";; esac
EXPECTED_ROOT="${TMP_DIR_FRESH%/}/done-session"
EXPECTED_ROOT="$(cd "$EXPECTED_ROOT" 2>/dev/null && pwd)" || EXPECTED_ROOT=""
MARKER_DIR="$(cd "$(dirname "$MARKER")" 2>/dev/null && pwd)" || MARKER_DIR=""
if [ -z "$EXPECTED_ROOT" ] || [ "$MARKER_DIR" != "$EXPECTED_ROOT" ]; then
  rm -f "$MARKER"
  echo "run-start marker: resolved path ${MARKER_DIR:-unresolvable} is not the expected done-session root ${EXPECTED_ROOT:-unresolvable}; stray marker removed" >&2
  exit 1
fi
```

**Run manifest:** immediately after the marker, write the run manifest record next to it under `{tmp_dir}/done-session/` (filename pattern `run-manifest-<run_id>.json`). The manifest is this run's ownership record: it carries a unique `run_id`, the marker filename it extends, the `start_commit` (HEAD at Step 0), the pre-existing dirt snapshot, the plan and review paths this run owns, the review candidates explicitly marked foreign, the `adopted_from` link (null unless an adoption was passed), and a `complete` flag written false. Resolve the sweep-gates lib repo-local first (a repo-local `scripts/done_sweep_gates_lib.py` wins; otherwise derive the deployed lib path from the sweep-gates script default), then invoke the writer:

```bash
REPO_TOP="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
LIB="$REPO_TOP/scripts/done_sweep_gates_lib.py"
if [ ! -f "$LIB" ]; then
  LIB="${DONE_SWEEP_GATES_SCRIPT:-$HOME/.ai-playbook/scripts/done_sweep_gates.sh}"
  LIB="${LIB%done_sweep_gates.sh}done_sweep_gates_lib.py"
fi
WM_OUT="$(python3 "$LIB" write-manifest \
  --owned-plan <plan-path-this-run-finalizes> \
  --owned-review <review-staging-doc-this-run-finalizes> \
  --foreign-review <peer-staging-candidate> \
  --owned-path <start-dirt-path-this-run-may-stage>)"
printf '%s\n' "$WM_OUT"
MANIFEST="$(printf '%s\n' "$WM_OUT" | sed -n 's/^manifest: //p')"
RUN_ID="$(printf '%s\n' "$WM_OUT" | sed -n 's/^run_id: //p')"
if [ -z "$MANIFEST" ] || [ -z "$RUN_ID" ]; then
  echo "run manifest: writer left no manifest/run_id echo to capture; aborting Step 0" >&2
  exit 1
fi
# Export the audit variables the owned-commits ledger append (Step 1)
# reads: MANIFEST and RUN_ID are parsed from the writer's echoed
# "manifest:" and "run_id:" stdout lines. Commit ownership itself is
# captured per commit at write time by the Step 1 fused exact-SHA append,
# so no start_commit read-back is exported here (adoption still reads
# start_commit from the manifest record itself). Re-derive them the same
# way when re-exporting in one-shot shells.
```

Pass `--owned-path` once per start-dirt path this run may stage: record every baseline-dirt path (dirty or untracked at the porcelain snapshot) this run will stage in its landing, and for an adopting run also the adopted run's uncommitted output per the adoption re-derivation record, after re-reviewing the adopted manifest's inherited `owned_paths` claims (an inherited claim the re-derivation does not support is never exercised: leave its path unstaged and record the disowned claim in the session notes; the writer unions inherited `owned_paths` verbatim and there is no drop flag). Claims are load-bearing only against Step-0-recorded rows (mid-session creations pass the foreign-staging gate without claims), and the gate-side pass result naming exempted owned paths is the audit of record for baseline-dirt claims. Pass `--owned-plan` once per plan this run finalizes, `--owned-review` once per review staging doc this run finalizes, and `--foreign-review` once per staging candidate the operator recognizes as a peer's artifact. For bulk answers the two affordances replace one-flag-per-path enumeration (F13 field witness: a reviews directory holding hundreds of prior-session staging docs): `--claim-none` asserts this run owns no staging doc of its own and marks every unclaimed candidate foreign (each recorded in the manifest's `foreign_review_paths` for audit; it conflicts with `--owned-review` and with an adopted manifest that owns staging docs, aborting with a named ownership-conflict error), and `--foreign-review-from <file>` bulk-loads foreign paths one per line from a file, merged with the same dedup as `--foreign-review`. Pass `--adopt <run_id>` only when the operator explicitly adopts a prior interrupted run's boundary; nothing is adopted implicitly. An interrupted boundary under this checkout's done-session directory that is neither adopted nor dispositioned refuses a new write-manifest invocation (`write-manifest: undisposed-interrupted:`), and the report line's remedies are the exits: `--adopt <run_id>` or `finalize-manifest --run-id <id>` for a live root, `disposition-manifest --run-id <id>` only for a dead root. Resume continuation: a later session that finds a resumable-closeout checkpoint verifies the run identity (the checkpoint's run_id and session identity against the done-session directory's records), re-runs the deliverables witness (every owned deliverable resolves per the witness arms on disk at execution time, including the landed-deletion and note-backed arms once the deliverables-witness plan executes - it orders before this plan's Task 2), and verifies commit ownership (the owned-commits ledger's commits reachable from the landing destination); only then does it run the remaining gates and the finalizer, recording the continuation as a session-notes receipt (the precedent home the skill's own receipts use; the manifest's disposition record is a dead-root-only mechanism and is never hand-edited); it refuses automatic continuation - leaving the record for explicit `--adopt`, finalize, or disposition - when the checkpoint is stale (the recomputed manifest sha256 differs from the checkpoint's recorded sha), the identity differs, any claimed deliverable is unverifiable, or the owned commits are not verifiably landed; it never adopts or stages another run's work implicitly. The writer enforces claim-or-foreign over every staging candidate on disk at Step 0: a candidate that is neither owned nor foreign aborts Step 0 with a named error and no manifest (the error names both bulk affordances), so classify every candidate before invoking. The write is fail-loud: an unwritable done-session directory aborts Step 0 with a clear error, mirroring the marker recipe's failure stance. Keep the echoed manifest path and run_id in chat context: they join the marker path as the run's audit record, and the owned-commits ledger rule (Step 1) plus the Step 6 finalize consume this record. Treat the echo capture as part of the write: after the writer has run, an empty captured `MANIFEST` or `RUN_ID` must abort Step 0 with the block's named error, never leave the ledger append and the Step 6 finalize silently disabled. When the run enters the finalizer span, Step 0 creates the resumable-closeout checkpoint in the run's manifest directory (a sibling JSON naming the run_id, the manifest path, the session identity, the manifest's sha256, and the gates already green at write time); Step 6 REFRESHES that checkpoint at the finalize preamble (same filename, updated manifest sha and gate set) rather than writing a second copy, and a successful finalize removes the checkpoint sibling; on an interruption the checkpoint is what a resume continuation reads, and staleness is the recomputed-manifest-sha mismatch.

**first finalize in an established repository:** the staging corpus may hold many prior-session docs, so classify it with the canonical two-command bulk-load sequence instead of hand-assembling a foreign list: run the writer once with `--emit-foreign-candidates <file>` (it enumerates the same staging candidates the claim-or-foreign gate checks, subtracts this invocation's `--owned-review` claims plus an adopted run's inherited owned claims, writes the remaining candidate paths one per line in sorted order to the file, and exits 0 without writing a manifest), review the emitted list and move any path this run actually owns into an `--owned-review` claim, then re-run the real write with `--foreign-review-from <file>` carrying the reviewed list. Run this emit invocation directly, never through the echo-capture block above: its stdout is the emitted-list summary line, not the `manifest:`/`run_id:` echo that block requires, so wrapping the emit call in the capture trips the empty-echo abort on a successful emission; only real manifest writes go through the capture. A candidate path holding a newline or leading or trailing whitespace cannot round-trip through a one-per-line file (the bulk loader strips and splits lines), so the emission aborts with a named error listing the offending paths; classify those with per-path `--foreign-review` or `--owned-review` flags instead. Note `--claim-none` conflicts with `--owned-review` (a named ownership-conflict abort): a run that owns any staging doc of its own cannot bulk-mark the remainder foreign, so it claims its own docs and lets the emitted list carry only the unowned paths.

**Stale-deployment signature (Step 0 lib):** an argparse unrecognized arguments error naming a write-manifest flag this skill documents (`--claim-none`, `--foreign-review-from`, `--emit-foreign-candidates`, `--owned-path`) is a stale runtime-home copy of the sweep-gates lib, not a lib defect to investigate: redeploy the sweep-gates script/lib pair from the repo (repo is the source, the runtime home is the destination, never the reverse), moving each live copy aside to a `.bak-<date>` sibling before the copy, then re-run Step 0; never route this signature to the investigate path or the recorded-stop exception.

**Revert-set adjudication (baseline dirt):** when the Step 0 porcelain baseline snapshot shows dirty tracked paths, classify the dirt before any ownership claim: run `python3 scripts/revert_set_classifier.py classify --repo <repo-root>` (resolve the script repo-local first, then the deployed home copy, the resolution this skill's other gates use). The classifier answers in the outcome contract's four-outcome vocabulary (scripts/OUTCOME_CONTRACT.md): exit 0 with the final `OUTCOME: pass` line records one line in the session notes and the dirt keeps the existing baseline discipline unchanged. Exit 1 with `OUTCOME: fail` is read through the summary line: on `revert-set: pure` the dirt is reversal damage (a staged or unstaged transplant of pre-landing vintages, every hunk the inverse of a landed commit's diff) and the adjudication runs before any claim, staging, or adoption: export the evidence with `git diff HEAD > {tmp_dir}/done-session/revert-set-evidence-<run_id>.diff`, restore the classified paths to HEAD with `git restore --source=HEAD --staged --worktree -- <paths>` (path-scoped; never a whole-tree reset; untracked paths are never removed), record the token `revert-set-adjudicated` in the session notes with the per-path commit ids the classifier rows name (the ancestor-vintage or reverted-addition commits), then re-run the porcelain snapshot: the post-restore state is the baseline of record and the adjudicated paths carry no `--owned-path` claims. On `revert-set: partial` the set is never adjudicated: the rows are recorded in the session notes and each path keeps the existing foreign-work and item adjudication protocols. Exit 2 (`OUTCOME: indeterminate`, a git plumbing failure over already-resolved inputs) and exit 3 (`OUTCOME: tool_error`, an unresolvable `--repo` or head ref, or a usage violation) are never reversal findings: stop and report with the classifier's error evidence recorded, and a run that ends with no final `OUTCOME:` line is tool error per the contract's no-line rule: stop and re-derive the tree state from disk. A classified revert set is never adopted, transplanted, or committed; the classification runs at Step 0 so every downstream lane of this run (residual staging, adoption, landing) reads a restored, classified baseline.

**Adopted-run re-derivation (adoption boundary):** an adopted interrupted run re-derives its remaining work against the current default branch before any staging: a fresh diff of the run branch tip versus the current default-branch tip, recomputed at adoption time, which is the what-would-transplanting-change view that exposes a stale-base inversion. The prior session's working-tree diff, index state, or exported patch is never transplanted into this checkout, because a stale-base diff re-applied onto an advanced default branch materializes as a reverse-squash revert set (witness: the 2026-09-25 rule29 restaging, recorded in the backlog archive). The adoption continues only after the re-derived work plan is recorded in the session notes beside the run manifest reference and the Step 3 Reverse-squash arm passes on the first staged set.

**Manifest disposition (dead-boundary close):** when an interrupted run's recorded root digest names a checkout that no longer exists, the adoption boundary above and the finalize identity check refuse it forever, so the boundary is unadoptable and the manifest would stay interrupted indefinitely; when the operator directs closure and the run's work is verified landed, resolve `$LIB` exactly as Step 0 does and run `disposition-manifest --run-id <id>`. The operation's deliverables witness verifies every owned deliverable through its set-specific resolution (an owned plan passes at its recorded path, its `plans_completed` archive twin at HEAD, `HEAD:<recorded path>`, or note-backed; an owned path additionally passes at its `plans_completed` archive twin when the recorded path sits under the plans tree, through its landed deletion - a commit reachable from HEAD that deleted the path, the sanctioned outcome of a deletion landed through the repo's own gates - or note-backed) and refuses the closure naming any owned deliverable whose resolution fails; the remedy is landing or restoring the deliverable in the set's own home, and closure without the deliverable in its home requires the operator's `--note` recording the home checkout and verifying commit (the note-backed escape; the never-forcing rule holds for every entry neither armed nor note-named). On success the operation prints a `dispositioned` receipt line; record that receipt in the session notes beside the manifest reference. An unknown-sub-command exit 2 from the resolved lib (a runtime twin predating the outcome-contract migration) or an unknown-sub-command exit 3 whose output ends `OUTCOME: tool_error` (a migrated twin predating the manifest subcommands) is the stale-deployment signature: redeploy the sweep-gates script/lib pair per the Step 0 stale-deployment recipe and retry. The maintenance survey's interrupted-manifest classification arm is the executing consumer of this paragraph for dead-root manifests: it runs this procedure in the same turn it proposes the closure, per its bounded-census gate, while operator-directed closure remains available at any time through this paragraph's own invocation; this paragraph stays the procedure of record, so the maintenance arm and an operator direction resolve to the identical steps. Witness: interrupted manifest 20260929T023532Z-3fb1c11bb98b, refused by both adopt and finalize on 2026-09-29, its disposition recorded only in a memory note.

Keep the echoed marker path in chat context as this run's audit record. The sweep gates derive the session window mechanically from the `run-start-*` markers under `{tmp_dir}/done-session/` (the newest content-confirmed marker is the current run; the newest strictly older one is the previous-run anchor; content confirmation compares the marker's recorded digest against the SHA-256 hex digest of this repo's resolved repo root recomputed via the Step 0 recipe, with a legacy raw-path marker confirmed by its resolved path instead, and recorded content that cannot be recomputed or does not match this repo is a cross-repo done run), which is the mechanical counterpart of the echo: when fewer than two markers are content-confirmable at gate time, the window is unanchorable (conservative gating) and the docs-tmp-sweep gate prunes no `run-start-*` markers this run; never guess by recency. A run whose manifest and owned-commits ledger both exist anchors its own window from that witness pair (the window's anchor stays unset, so marker pruning keeps its conservative behavior); without the complete pair the window stays unanchorable. This rule is the Step 0 echo-loss fallback that the plan-readiness gate back-references.

## Step 1: Run Learn

Invoke the `learn` skill now to extract lessons and update the documentation corpus before committing.

**Learn-owned commits in this step:** learn may commit its own skills-repo artifacts during this step (its Step 1.8 backlog items and skill-placement edits); that is expected and does not double-commit, because Step 4 sees only non-learn leftovers plus the failed-capture set, and no-ops when clean.

**Owned-commits ledger (Step 1 site; the same rule applies after every project commit from here on, Step 3 included):** after the learn-owned commits above and before the pre-docs sweep gate run, record every commit this run creates in `{tmp_dir}/done-session/owned-commits-<run_id>.txt` (the ledger is created on first append; no base commit is needed), so a multi-commit learn phase (backlog commit plus skill-placement commit) lands every sha, not only the newest. Attribution is fused exact-SHA capture: each owned commit and its ledger append run in ONE shell invocation, the commit command chained to the prescribed append line so the ownership witness is the same command whose success creates the commit; the fused form is reserved for commits the done skill executes. Learn-owned commits are post-hoc-from-receipt: learn prints `committed: <sha> <subject>` after each successful commit (the receipt contract learn Step 1.8 owns), and the multi-commit learn rule records every sha learn reports it created in this repository, in order, appending the receipts' shas literally, one append per reported sha, in receipt order, never via the prescribed append line. Only same-repository receipts are appended: resolve each reported sha first (`git rev-parse -q --verify '<sha>^{commit}'`) and skip one that does not resolve with a one-line note, because learn may commit its artifacts in a second repository and a cross-repo sha can never resolve in this run's ledger. Skip the append with the one-line note when the run has no manifest from Step 0 (the `RUN_ID`/`TMP_DIR` guard below). Recovery disposition: on the doc-registry report naming a foreign-commit exclusion for a sha this run created, appending that sha to the ledger (an append is not an edit of a recorded line) and re-running the gate is the remedy, never restoring the range enumeration:

```bash
# RUN_ID comes from the Step 0 manifest echo (the run-manifest-<run_id>.json
# audit record); TMP_DIR from the Step 0 marker block. Re-export both from
# chat context in one-shot shells. The guard gates the whole recipe and checks
# BOTH inputs: with no RUN_ID there is no ledger path to append to, and a lost
# TMP_DIR misassigns the ledger path to /done-session/... under bash 3.2
# set -u, and the run then fails at the redirect after the commit landed; in
# both cases only the skip note runs (an owned commit must never happen
# without its ledger append defined).
if [ -z "${RUN_ID:-}" ] || [ -z "${TMP_DIR:-}" ]; then
  echo "owned-commits: no RUN_ID or TMP_DIR from Step 0; ledger append skipped"
else
  # The first append below creates the file; no base commit is needed.
  LEDGER="${TMP_DIR%/}/done-session/owned-commits-${RUN_ID}.txt"
  # Fused exact-SHA capture for a commit the done skill executes: the commit
  # command and its ledger append run in ONE shell invocation, chained so the
  # ownership witness is the same command whose success creates the commit:
  git commit -m "<message>" -- <paths> && git rev-parse HEAD >> "$LEDGER"
  # Learn-owned commits are post-hoc-from-receipt instead: for each receipt
  # learn printed (the receipt contract above), append the reported sha
  # literally, one append per reported sha, in receipt order:
  printf '%s\n' '<reported-sha>' >> "$LEDGER"
fi
```

The ledger is the gate-side record of this run's work: it records exactly the commits this run created, each captured at its own commit's write time, and nothing enumerated from a range; keep it one sha per line and never edit a recorded line.

**If `learn` reports a blocked state** (Step 6.6 user-corpus violation: a strict-tagged `UL#N` lesson is missing its `**Principle:** Family X` tag, or the gate script returned non-zero on the adopted corpus), release the lock via Step 6 and return `blocked` WITHOUT proceeding to Step 2 commit. `learn` is invoked here as a SKILL (a sub-procedure), not as a subprocess whose exit code this step checks, so the gate's block decision lives in `learn`'s Step 6.6 text and propagates here through `learn`'s returned state. The operator fixes the user corpus out-of-band before the next `done`, branching on the validator category each listed `UL#N` carries (`duplicate` | `untagged` | `multiple-tags` | `invalid-family`, classified in that precedence order by `lessons_index.py`); the recovery is operator-driven - it never renumbers lessons or rewrites cross-references itself:
- `duplicate`: inspect the colliding headings, choose a unique identifier for the colliding lesson, update the same-corpus references to the renumbered id by hand, then re-run the validator (a duplicate is a heading collision, not a tagging case).
- `untagged` / `invalid-family`: classify the listed `UL#N` via learn/generalize, or run `lessons.py adopt --tag-unclassified <user_corpus>` manually.
- `multiple-tags`: classify the lesson first, then remove the competing family tags so exactly one `**Principle:** Family X` line remains outside fenced blocks, then re-run the validator.

**After learn completes, immediately continue to the pre-docs sweep gate run.** Do not stop or wait for user input; the workflow is continuous and all steps should execute in sequence.

## Pre-docs sweep gates (`done_sweep_gates.sh pre-docs`)

Immediately after learn and before `docs-branch`, run the deterministic pre-docs gates once per repo from the project git root:

```bash
bash "${DONE_SWEEP_GATES_SCRIPT:-${HOME}/.ai-playbook/scripts/done_sweep_gates.sh}" pre-docs
```

Gates run in this order: plan-readiness, confluence-hygiene, doc-registry, backlog-inbox, review-thread closure (a session-level conditional gate the runner does not execute; apply it in-session per its bullet below before continuing), review-staging, vim-swap-sweep, docs-tmp-sweep, plans-archive-twin. The runner derives every session-scoped input mechanically (it cannot read chat context): the session window anchors on the `run-start-*` markers under `{tmp_dir}/done-session/` (the newest content-confirmed marker is the current run, the newest strictly older one is the previous-run anchor, and fewer than two confirmable markers means an unanchorable window with conservative gating), and candidates come from `{tmp_dir}/done-session/plan-deliverables.txt` plus the porcelain and ignored-matching git arms. The enumeration's closing obligation: Archiving a plan is a move, never an add-plus-keep; the plans-archive-twin gate fails any landing while a twin from an earlier run sits unresolved at the plans root. **Exit 0** (`OUTCOME: pass`): continue immediately to Step 2. **Outcome contract:** the runner ends every run with a final `OUTCOME:` line (scripts/OUTCOME_CONTRACT.md), and the exit code and that line are read together: exit 1 (`OUTCOME: fail`) is a modeled gate finding - every gate reports even after an earlier failure; fix what the report flags using the per-gate guidance below and re-run the runner until it exits 0. Exit 2 (`OUTCOME: indeterminate`: a crashed gate helper captured and named by the runner, or a gate child exiting outside its 0/1 answer vocabulary) and exit 3 (`OUTCOME: tool_error`: a usage or environment failure) are never read as pass or as a modeled finding: stop the closeout, report the named gate's observed/could-not-determine or error lines, and re-derive the state from disk before re-running; no dependent step (docs-branch, staging, commit) proceeds on such a result. A run that ends without its final `OUTCOME:` line is tool error under the contract: stop and re-derive the same way.

- **plan-readiness** (a gated plan's latest review does not cover its current bytes): refuse to finalize; require a fresh `review-plan` round (after any plan edit that changes the digest) before re-running the gate, except when the failure is remediable through the cap-closure terminal shape; passed, manifest-exempted, and archived plans have their deliverable lines pruned by the runner. The same validator also runs at authoring time as the structural-only pre-round gate (plans rule 29, `--pre-round`); a structural-clean pre-round pass means this exit gate re-proves only the review-record bindings (sidecar schema, source_kind, digest, verdict, zero blocking). Exception: a sidecar declaring the operator-authorized cap-closure terminal shape, `extensions.cap_closure` bound to the plan section `## Residual findings (cap closure)` and carrying `pre_fold_digest`, with zero unresolved blocking findings, passes; folded staged findings carry resolved triage from the vocabulary `fixed`, `dropped`, or `done` on both record surfaces, the review Markdown `- **Triage**:` bullet and the matching sidecar `findings[].triage`, the same value on both per the triage-agreement arm; the re-bind rewrites only `source_digest` and never the sidecar `verdict` field. Recorded-stop remains the only way past every other failure. A plan archived under the plans `rejected/` directory (an explicit decision against the work; see that archive's README) is not a gated candidate at all: the runner excludes it like a completed-plan archive and prunes only its own deliverable lines. **Deployment-gap signature (narrow):** a deployment gap is ONLY (a) the validator file itself missing or unopenable, or (b) a `ModuleNotFoundError` in the output. For either: stop and report the wiring gap, and never use the recorded-stop exception for it; manual remedy: `cp scripts/plan_readiness.py ~/.ai-playbook/scripts/` plus siblings (the script imports `validate_review_staging.py` and `facts_paths.py` from its own directory, so copy all three; the deployed `facts_paths.py` may be a symlink, keep it one, e.g. `cp -P`, do not dereference it into a second copy). Any OTHER non-zero exit that prints no `readiness FAILED:` line (validator crash, traceback, unexpected output) is NOT covered by that copy remedy: investigate the validator before re-running the gate. **Recorded-stop exception:** the only permitted way past a failed gate is when the user explicitly chooses to stop without finalization and that choice is recorded in the session log. In that case do not commit the plan deliverable: record the excluded plan path in the session log and, in this session's later commit-all steps, exclude exactly that path plus its review artifacts (the review Markdown and `.stats.json` sidecar under `{reviews_dir}`) when staging, then continue with the remaining hygiene steps and report the recorded stop in Step 7; also remove every line listing the excluded path from `{tmp_dir}/done-session/plan-deliverables.txt` so it does not reappear as a gate target.
- **confluence-hygiene:** never delete `*-cf-out.md` until audit confirms the content is already represented in the docs hierarchy or is a stale duplicate. NEEDS_UPGRADE: promote first (mirror at `docs/history/context/confluence/{page_id}-{slug}.md` with standard frontmatter, manifest `layer2_targets`, or the spike sync ledger). UNMAPPED: route manually (new manifest entry, mirror file, or Layer 2 doc); do not delete. On `validate` failure: fix the mirror frontmatter and filenames, the manifest rows, and the mirror index; after a live push, refresh mirror bodies, bump manifest versions, and set `sync_status: synced` in the same session (never leave truncated wiki pages; republish the full body). **Deployment gap:** when `confluence-mirror-hygiene.sh` is absent from every resolved path while a run-when trigger is live, the gate fails rc 1 as a deployment gap; deploy the script to the runtime home `scripts/` directory and re-run, and never use the recorded-stop exception for a deployment gap.
- **doc-registry:** warn-only findings (legacy files without registry entries, multiply-claimed srcs) do not block: report them, and clear a standing-override's audit note after the licensed write lands. Hard findings (registry parse errors, invalid `sot`/`state` values, malformed audit-note tokens, duplicate identities or SOT declarations, successor cycles, unprotected writes to completed-history paths): fix the registry row or move the change into the living SOT instead of editing a completed artifact; before moving a change into the living SOT, verify the destination registry row owns those topics (the registered SOT for the moved content), and when no registered owner exists or the destination is itself frozen, record the conflict and route it through an explicit policy decision instead of moving content by inference, recording the conflict in the session log. An absent validator is fail-open (reported once, non-blocking). Before publishing or landing changes that touch tracked prose under `docs/`, run the hygiene scan in explicit changed-files mode (the scan script's `--files` form) or the full pattern-file sweep over the touched tracked files, because the default scan scope covers only the strict source trees per the standing result-only adjudication (2026-09-27); the scan answers in the outcome contract's four-outcome vocabulary (scripts/OUTCOME_CONTRACT.md), so a findings run (exit 1, final `OUTCOME: fail`) has each residue hit sanitized to the operator-approved generic form in the same run and re-run to `OUTCOME: pass`, while a tool error (exit 3, `OUTCOME: tool_error`: a missing patterns file, an unreadable input path, an invalid regex line in the shared patterns file) or a run with no final `OUTCOME:` line records failed-resolution evidence and stops (re-derive the scan setup from disk before re-running; never sanitize around a scan that could not run). **Stale-deployment signature:** a doc-registry failure printing `invalid state value` on a state value the repo-copy validator accepts is a stale runtime-home validator, not a registry defect: redeploy with `cp scripts/doc_registry_validator.py ~/.ai-playbook/scripts/` and re-run the gate; the same redeploy covers the silent direction (a pre-fix deployed copy lacks the rejected-archive immutability and licensed-transition coverage, so a body edit or deletion under a rejected archive passes the gate silently until redeploy); never route a stale deployment to the investigate path or the recorded-stop exception. The runner's check-writes stdin union carries git's change-type letters verbatim (porcelain `XY PATH` rows with renames as `R  old -> new`, the committed-since-session-start name-status rows, and ignored files as bare rows); the letters are what bind the registered-src exemption to the archive transition, so the union is never downgraded to name-only paths.
- **backlog-inbox:** genuine backlog material moves into the resolved `{backlog_dir}` per `receiving-review` Backlog capture (rename to `YYYY-MM-DD-<slug>.md` when needed); a legitimate Layer 2 doc that merely trips the filename shape is renamed to a compliant name, asking the user when the run is interactive; never a silent move that misfiles real content.
- **review-thread closure:** when a review-thread marker (a `docs/tmp/review-threads/<session-slug>.json` per `receiving-review`'s marker duty) whose recorded session identity matches the CURRENT session exists, run `python3 scripts/review_thread_gate.py --marker <path>` with an inventory source (canned file/pipe such as captured `gh` output, or `--live` (the gate accepts both marker shapes: canonical `owner/repo#N`, or numeric `pr` plus `repo`/`url`)). The gate answers in the outcome contract's four-outcome vocabulary (scripts/OUTCOME_CONTRACT.md): exit 0 with the final `OUTCOME: pass` line only when every tracked thread carries a verified agent reply or an explicit disposition, and the missing-marker skip (the gate's documented "nothing to check" reason line) is also a pass at exit 0; exit 1 with `OUTCOME: fail` lists the unclosed threads: report blocked, release the project done lock per Step 6, and do not report completion; exit 2 (`OUTCOME: indeterminate`) and exit 3 (`OUTCOME: tool_error`: an unresolvable marker PR target, a failed gh inventory fetch, an unreadable or shape-violating marker or inventory, or a usage violation) are never review findings: fix the invocation, the marker, or the gh state and re-run the gate before any done report; and a run that ends with no final `OUTCOME:` line is tool error per the contract's no-line rule: stop and re-derive the marker's state from disk. Report push authorization separately from review-response state. A session with no marker, or a marker whose recorded identity does not match the current session (stale or foreign), is unaffected: the gate reports it as stale/skipped and never gates this session's done run. Human-authored threads are never auto-resolved.
- **review-staging:** complete each flagged staging doc per `review-staging` (Metadata, Review Statistics, Findings with Comment/Analysis) before continuing; do not sync stub staging docs to the orphan `docs` branch.
- **vim-swap-sweep:** the runner removes only verified stale swaps (dead-owner PID) and preserves live-owner or unverifiable files; a `needs-manual` entry stays in place until manually confirmed.
- **docs-tmp-sweep:** durable findings graduate into lessons, completed plans, or Layer 2 docs; the rest dies with its owner. The runner never removes an ACTIVE `execute-plan` session (its plan pending anywhere under `{plans_dir}`, nested subdirectories included), an ARCHIVED-plan `execute-plan` session that still holds its captured `closeout-baseline.json` as a regular file (transfer-out may be pending; a crashed run's directory is left in place - no lane removes it today, and its disposition runs through the next run's interrupted-run report and explicit adoption, not destruction), `review-loop*`/`code-review/`/`handoff/` scratch (their owning skills clean up), the previous-run anchor marker, or the current-run marker (a marker whose recorded digest matches the SHA-256 hex digest of this repo's resolved repo root, computed as in Step 0, is content-confirmable; a legacy raw-path marker confirms by its resolved path), and it skips rather than removes anything never synced to the `docs` branch or of unclear ownership; a one-off already synced to the `docs` branch is likewise skipped while it was modified inside the session window (removal waits for a session whose window no longer covers it, and an unanchorable window removes nothing). Resolve skips by hand only after confirming sync state, and report what was left and why.
- **plans-archive-twin:** a failed finding names the root-plus-archive pair; the ownership-and-tracking-scoped remedy: a twin this session created resolves by true rename in-landing; for a byte-different pair, diff the two sides first and reconcile the root side's extra content into the archive side (or ask the user) before any removal; an untracked unclaimed start-dirt twin resolves by unstaged removal of the plans-root side, never the archive side; a tracked plans-root side that is dirty at Step 0 resolves at the next Step 0 via an `--owned-path` claim followed by a staged deletion committed in that landing's pathspec (unstaged removal of a tracked side leaves the twin committed); a clean tracked side may resolve in-landing by a staged deletion without a claim (its path is not start-dirt), re-verifying the side is clean against HEAD immediately before the deletion (if it went dirty mid-window, route to the tracked-dirty arm; never delete with force); a run deferring resolution to the next Step 0 records a recorded stop.

**After the pre-docs sweep gate run completes (or no-ops), immediately continue to Step 2.** Do not stop or wait for user input; the workflow is continuous and all steps should execute in sequence.

## Step 2: Preserve Gitignored Docs and Instructions

Invoke the `docs-branch` skill now. When the session runs in an ad-hoc worktree, first migrate the run's review staging docs and session logs to the main checkout (the execute-plan Phase 5 migration, `worktree_closeout_migrate.py migrate`), before the docs-branch sync and in every case before the worktree is removed. The migration destination is a corpus surface, not landing staging (see Run placement beside the lock matrix). It will:
1. Snapshot all configured gitignored shadow paths (`docs/`, `.github/docs/`, `.ai-playbook/`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `COPILOT.md`, plus repo `extra_shadow_dirs`) while leaving the live checkout on the current branch.
2. Sync those files to the permanent `docs` orphan branch through a temporary `git worktree`, creating it if it doesn't exist.

**Repo merge lock (acquire before the migration and the sync):** the worktree migration and the docs-branch sync are shared-checkout critical sections: the migration writes the main checkout's review staging docs and session logs, and the sync writes the `docs` orphan branch that every worktree of the repository shares. Both run under the repository-keyed merge lock, the `merge-*` family of the same lock script; its canonical semantics (per-repository keying from the git common dir, bounded wait, token-fenced release from the exported `MERGE_LOCK_DIR` and `MERGE_LOCK_TOKEN`) live in the `scripts/done-lock.sh` usage text, mirrored for the scheduler lanes by the maintenance overlay's Merge landing lock paragraph. Acquire once per done run, before the migration when the session runs in an ad-hoc worktree and before the docs-branch sync in every mode, and hold the exports across the migration and the sync:

```bash
LOCK_SCRIPT="${DONE_LOCK_SCRIPT:-${HOME}/.ai-playbook/scripts/done-lock.sh}"
MERGE_ERR="$(mktemp)"
if ! MERGE_EXPORTS="$("$LOCK_SCRIPT" merge-wait-acquire --label done-docs-sync --max-wait 300 2>"$MERGE_ERR")"; then
  "$LOCK_SCRIPT" merge-status >&2
  # Outcome contract: the final OUTCOME line lands on STDERR for the acquire
  # subcommands (their stdout is eval-consumed exports only).
  case "$(grep -E '^OUTCOME: ' "$MERGE_ERR" | tail -n1)" in
    "OUTCOME: fail")
      echo "merge-lock: blocked after 300s; a landing or a peer docs sync holds the repo merge lock" >&2
      ;;
    "OUTCOME: indeterminate")
      echo "merge-lock: holder state ambiguous; the hold cannot be adjudicated: report and stop (merge-stale-clean stays the explicit operator escape only)" >&2
      ;;
    *)
      # OUTCOME: tool_error, or no final OUTCOME line at all: tool error
      # under the outcome contract, never a hold.
      echo "merge-lock: lock tool error (outcome: $(grep -E '^OUTCOME: ' "$MERGE_ERR" | tail -n1) ); fix the invocation or environment and re-derive from disk" >&2
      ;;
  esac
  rm -f "$MERGE_ERR"
  exit 2
fi
grep -qx 'OUTCOME: pass' "$MERGE_ERR" || {
  echo "merge-lock: merge-wait-acquire emitted no final OUTCOME: pass on stderr; treating as tool error" >&2
  "$LOCK_SCRIPT" merge-status >&2
  rm -f "$MERGE_ERR"
  exit 2
}
rm -f "$MERGE_ERR"
eval "$MERGE_EXPORTS"
# Print the exports: the release runs in a LATER shell call whose env is
# fresh, and merge-release-repo refuses to source the session fence, so the
# token must survive here in chat context to be re-exported there. That
# later shell no longer has this LOCK_SCRIPT variable; the release command
# re-derives the script path from the same DONE_LOCK_SCRIPT override variable
# (same default), so
# only MERGE_LOCK_DIR and MERGE_LOCK_TOKEN need to survive.
printf '%s\n' "$MERGE_EXPORTS"
if [[ -z "${MERGE_LOCK_DIR:-}" || -z "${MERGE_LOCK_TOKEN:-}" ]]; then
  echo "merge-lock: acquire succeeded without lock exports" >&2
  exit 1
fi
```

On the `OUTCOME: fail` timeout (and the same blocked stance for an `OUTCOME: indeterminate` ambiguous holder), return `blocked` keeping every artifact of the run (run-start marker, run manifest, owned-commits ledger, created commits, and an ad-hoc worktree with its review docs), mirroring the Step 0 done-lock stance, and release the done lock per Step 6 before reporting. In one-shot shell calls, pin `MERGE_LOCK_HOLDER_PID` to a long-lived process (for example the agent runtime), the same pinning discipline as the done lock's Variant B, so the hold survives the acquiring call and cannot be reclaimed mid-section.

**After docs-branch completes, run the verification below, release the merge lock per the release rule at the end of this step, then immediately continue to Step 2.5.** Do not stop or wait for user input; the workflow is continuous and all steps should execute in sequence.

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

**Resolve-at-use digest rule for landing receipts:** when this verification names or restores from a commit, or a landing receipt records one, the digest obeys **resolve-at-use**: a full digest used in a state-changing command or a durable record is produced by `git rev-parse`, `git log --format=%H`, or `git show -s --format=%H` at the moment of use; landing helper invocations pass refs (branch names, `HEAD`, relative forms) rather than literal digests wherever the tool accepts them. (Added 2026-10-03; origin `docs/history/backlog/2026-10-02-sha-resolution-at-use-fence.md`; witness: the 2026-10-02 fabricated-digest slip, a 40-character digest whose tail was fabricated by hand from a 7-character display prefix and refused by the CAS old-value existence check.)

**Merge-lock release (every exit path):** release with `merge-release-repo` using the exported `MERGE_LOCK_DIR` and `MERGE_LOCK_TOKEN`, re-exporting both from the acquire output in the releasing shell (the release requires the env and refuses to source the session fence). The release is explicit, never a stray-trap, mirroring the Step 0 done-lock Variant B discipline, and it runs on EVERY exit path: after the verification above on success; on any migration or sync failure, before reporting the failure; and as interruption cleanup when the run is interrupted while holding the lock (the explicit release from session context; when the session itself died holding the lock, name the held label `done-docs-sync` and `MERGE_LOCK_DIR` in the outcome so the holder state is inspectable):

The release command re-derives the lock script path itself (same default and the same `DONE_LOCK_SCRIPT` override variable the acquire block resolves, falling back to `~/.ai-playbook/scripts/done-lock.sh`), because the acquire shell's `LOCK_SCRIPT` variable does not survive into the later releasing shell; only `MERGE_LOCK_DIR` and `MERGE_LOCK_TOKEN` must be re-exported from the acquire output. The same command (and the same default) is the interruption-cleanup arm: run it verbatim from session context when the run is interrupted while holding the lock.

```bash
MERGE_LOCK_DIR="${MERGE_LOCK_DIR:?}" MERGE_LOCK_TOKEN="${MERGE_LOCK_TOKEN:?}" \
  "${DONE_LOCK_SCRIPT:-${HOME}/.ai-playbook/scripts/done-lock.sh}" merge-release-repo
```

If the release itself fails, read it through the outcome contract: `OUTCOME: fail` (exit 1: token mismatch, or the lock changed under us) or `OUTCOME: tool_error` (exit 3: env missing, or the lock directory carries no metadata so the release check cannot run reliably); a release run with no final `OUTCOME:` line is tool error under the contract. Run `merge-status`, report the holder state and the outcome line, and never re-acquire to fix it.

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

Gates run in this order: **sensitive-data-scan** (diff-content pattern grep over staged content, full-content scan of untracked files - both content arms always run the credential-shaped patterns and run the public-artifact pattern family (local paths, employer hostname, generic contact emails) active unless the repository declares `artifact_visibility = "private"` in its `.ai-playbook/facts.md`, the push-range commit-message audit when an upstream is configured, skipped with a warning line in the report when none is (`Co-authored-by:` trailers and employer-brand patterns resolved from the facts document), and `public_hygiene_scan_script` when this repo is the skills repo), **em-dash-scan** (`check-no-em-dash.sh touched` over touched prose; policy: `agent_workflow_guidelines.md` §39; a script absent from every resolved path is a rc 1 deployment gap, never a skip; on failure the gate falls back to added-lines --base HEAD per tracked path, reporting the first pre-existing line per hitting file as pre-existing (known-violation baseline): <path>:<line> (one row per hitting file, matching the whole-file probe's reporting shape); untracked hits and dirty added lines still fail), **instruction-size** (`check-instruction-size.sh gate`; budget 30,720 bytes per instruction entrypoint, the learn Step 6.5 constant; only over-budget files with uncommitted changes block; a script absent from every resolved path is a rc 1 deployment gap, never a skip), **description-length** (`python3 scripts/check_skill_description_length.py` over the repo's `agents/skills` tree; folded frontmatter description over 1024 characters fails naming the file and length, over 950 warns; a script absent from every resolved path is a rc 1 deployment gap, never a skip), **foreign-staging** (fails staged paths recorded as start-dirt but not owned by this run per the Step 0 manifest), **post-landing-staging** (fails primary-checkout residue after a landing: the primary checkout's index must match HEAD except staged paths owned by the resolvable current-session manifest, and unstaged tracked modifications are permitted only for the record-only allowlist; residue observed while the merge lock is held reports indeterminate, never a violation; the refusal names the residue paths, the sanctioned cleanup recipe (the land_squash.sh probe-then-reland path), and the operator escape for dead residue), **archive-ceremony** (fails a plan archive its derivation surfaces whose bytes still carry an unchecked `- [ ]` task box, and a derived archive whose boxes are complete but whose exec-review record is missing: no reviews-home file named `*-plan-review-<plan-slug>-exec-r<N>`; the derivation reads same-run staged or worktree renames into an archive state directory, committed renames into the completed archive since the active run manifest's `start_commit` (`ORIG_HEAD` fallback), and stale plan-deliverables lines whose archive twin exists at HEAD; the checkbox failure names the plan, the unchecked count, and the two sanctioned exits: check the boxes after verified work, or land a marked backfill completion record per the plans skill's archive-correction exception; A receipt-closed plan - one whose Commit, verification, and bounded-RED lines the execute-plan preflight's receipt-backed reconciliation deliberately leaves unchecked in the plan bytes - still has its boxes flipped, or lands a marked backfill, before archiving; the reconciliation's acceptance is verification evidence for the check-the-boxes exit, never license to archive unchecked bytes; the coverage failure names the missing series and the reconstruction remedy: produce the exec-review record for the plan's final bytes, or land a marked reconstruction per the cited-review-receipt-integrity precedent), **execute-plan-closeout** (the landing-side execute-plan lifecycle net: for every execute-plan session manifest the active run manifest's owned plan claims scope, a landed-complete run's archived bytes must re-hash to its terminal receipt's `plan_digest`, the active plan path must be gone from the index and the working tree, the archived plan's promoted origins must be closed per `check_plan_origins_closed.py --plan`, and the ownership registry must name the archived path; an owned session manifest whose tasks are all done under the runtime done predicate with no terminal receipt refuses as landed without terminal evidence; a missing execute-plan home, an unanchorable session window, no resolvable run manifest, or a manifest owning no plans is a warning skip naming the reason, never a silent pass; a still-executing mid-run session passes with a note), **plans-archive-twin** (fails a dated plan basename sitting both at the plans root and in an archive state directory; it also ran in the pre-docs phase). Fixing stays in this skill, read through the outcome contract (the runner ends every run with a final `OUTCOME:` line, scripts/OUTCOME_CONTRACT.md): on a failure (`OUTCOME: fail`) fix per the guidance below and re-run the runner until exit 0; an `OUTCOME: indeterminate` result (a crashed gate helper captured and named by the runner, or a gate child exiting outside its 0/1 answer vocabulary) or an `OUTCOME: tool_error` result is never read as pass or as a modeled finding - stop the closeout, report the named gate's observed/could-not-determine or error lines, and re-derive the state from disk before re-running (a run with no final `OUTCOME:` line is tool error under the contract and takes the same stop), and nothing stages or commits on either reading; for a deployment gap, deploy the missing script to the runtime home `scripts/` directory and re-run, and never use the recorded-stop exception for it. A `execute-plan-closeout` refusal keeps the run's session directory, the worktree, and its branch exactly like the transfer-out failure posture, preserves the manifest and resumable-closeout checkpoint untouched, and reports the named condition with the resume remedy instead of a completion report. Do not stage files a failing gate flags. Per-gate fix guidance:
- **foreign-staging:** the failure names staged paths recorded as start-dirt but not owned; unstage them (`git restore --staged <path>`); if the path is genuinely this run's baseline dirt, re-run Step 0 with an `--owned-path` claim for it (or adopt the prior run) and re-stage, never stage foreign paths to silence the gate.
- **plans-archive-twin:** apply the pre-docs plans-archive-twin guidance bullet's ownership-and-tracking-scoped remedy above; the pre-commit run catches the creating landing itself, which was already past pre-docs when its own copy-not-move staging appeared.
After the pre-commit sweep gate run exits 0, immediately continue to Step 3.

- **sensitive-data-scan:** credential hits are resolved in every repository: move credentials to `.env` or facts documents (never commit them). Hostname and contact-email hits are public-audience-artifact hygiene: replace personal paths with facts-document references or generic placeholders (e.g., `<your-org>.atlassian.net`, `~/Projects/<project>/`) in artifacts destined for public audiences; a repository declaring `artifact_visibility = "private"` in its `.ai-playbook/facts.md` keeps its valid internal service links (the content arms skip the public-artifact family there; the key absent or unparseable reads as `public` - today's strictness). replace internal names with generic equivalents; move credentials to `.env` or facts documents (never commit them); in a skill file, externalize machine-specific values to facts documents and keep portable policy constants and workflow thresholds in the skill body (see `learn` Step 2, Facts vs skill configuration; `agent_workflow_guidelines.md` §50); fix all `public_hygiene_scan_script` findings (child exit 1, final `OUTCOME: fail`) before staging, and read a scan child reporting `OUTCOME: indeterminate` (exit 2) or `OUTCOME: tool_error` (exit 3), or ending with no final `OUTCOME:` line, as failed-resolution evidence naming the child in the gate report, never as a finding to fix here: stop, report the child's observed/could-not-determine or error lines, and re-derive the scan setup from disk before staging. **Do NOT commit until all sensitive data is resolved.**
- **em-dash-scan:** fix every reported line with a comma, colon, semicolon, period, or parentheses, under the no-silent-gate-satisfying-rewrites rule (see Rules): when the failures reach untouched user-authored prose, or no minimal edit exists, stop and surface the conflict for the user to adjudicate; do not re-run the scan for exit code 0, leave the failing prose unstaged, and do not continue to Step 3 until the user adjudicates; enumerated pre-existing tracked hits pass with the baseline report; the stop-and-adjudicate path applies to added-lines failures and untracked-path hits.
- **description-length:** trim the flagged SKILL.md's folded frontmatter description under 1024 characters, keeping every trigger phrase (drop redundancy, not triggers); a script absent from every resolved path is a rc 1 deployment gap, never a skip.
- **instruction-size:** return to learn Step 6.5 (compact hybrid bullets to cross-references, move infrequent rules to skills), then re-run the runner before staging instruction files.

## Step 3: Commit Uncommitted Changes

After learn and stash steps complete:

0b. **Plan-deliverable append (producer 2 for the pre-docs sweep gate run's plan-readiness gate):** Before any `git commit` in this session that stages paths under `{plans_dir}` (excluding `{plans_completed_dir}`), append each staged plan path to `{tmp_dir}/done-session/plan-deliverables.txt` (create dir/file if missing; one repo-relative path per line; skip duplicates). Do this in the same turn as the commit, including when the commit is not part of `done`.

0. **Distinguish session changes from pre-existing local changes.** Only commit changes that were made during this session. If `git status` shows uncommitted files that were not touched by you in this session, ask the user before staging them; they may be in-progress work the user does not want committed yet. For cleanup or restoration sessions, capture the dirty-tree and untracked-file baseline before the first edit: always record the git status --porcelain baseline in the session notes before the first edit; additionally run the cleanup baseline checker scripts/check_cleanup_scope_baseline.py against the task's scope ledger when the task's scope ledger exists (resolve the skills repo checkout from the skills-repo path key in the user facts document and pass this repo via --repo-root). Refuse to stage any path that was already dirty or untracked at baseline unless the user explicitly includes it. The checker answers in the outcome contract's four-outcome vocabulary (scripts/OUTCOME_CONTRACT.md), the exit code and the final `OUTCOME:` line read together: exit 1 (`OUTCOME: fail`) means a path outside the ledger is dirty or deleted, so ask the user before staging it; exit 2 (`OUTCOME: indeterminate`, a git plumbing failure over already-resolved inputs) means the classification could not be determined, so fall back to the recorded session-notes baseline; exit 3 (`OUTCOME: tool_error`: an unresolvable base ref, a non-repo root, a usage violation) and a run that ends with no final `OUTCOME:` line (the contract's no-line rule) mean the checker could not run, so fall back to the recorded session-notes baseline the same way; if no recorded baseline exists in either shape, ask the user before staging any path not created or modified this session. Run the checker before the first commit of the session for full coverage; after commits exist, only deletions remain checkable (against the ledger's session-start base ref, never with `--base HEAD`), because committed non-deletion sweeps are invisible at any base ref once committed: assess committed modifications from the recorded session-notes baseline instead. If no pre-edit baseline exists at done time (whatever the reason: checker never run, an indeterminate or tool-error run with no recorded baseline, or baseline recorded after edits), ask the user before staging any path not created or modified this session; a baseline recorded after edits is not a baseline. For a landing closeout, item 1a's foreign-dirt gate paragraph supersedes this baseline arm's staging ask: landing staging follows the gate's disposition ladder, with user-owned baseline dirt claimed at Step 0 via an `--owned-path` claim before staging and never re-asked at landing. Checker limitations: it cannot see gitignored files (capture the ignored set with `git status --porcelain --ignored` and record those paths in the session notes explicitly), and it matches allow-list paths byte-exact relative to the repo root (no `./` prefix). If the skills-repo path key is missing or unresolvable, record the session-notes baseline and note that the checker was skipped.
0c. **Stale-checkout adjudication (before any disposition).** Before item 1's gates and item 1a's ladder classify any uncommitted modification, apply the stale-checkout discriminator (the Worktree-first standard section in agents/skills/execute-plan/SKILL.md): a tracked file whose blob equals that path's blob at an ancestor commit is landing debris, restored from the base tip with the restoration recorded, never staged, never committed, never reported as peer work; an index byte-identical to a pre-landing tree is remediated under the discriminator's per-path gate: a landing-changed path is remediated per the gate's arms (restore, or a named block; the pre-landing tip resolves from the landing's recorded tips or the base branch's reflog entry preceding the landing commit). A path this session's own records claim (an `--owned-path` claim or session attribution) is never auto-restored: report it for confirmation instead. A path this arm restored passes item 1's dirt regression gate vacuously; the gate keeps hunk-level regressions on the paths this arm leaves. A pre-commit sweep-gate failure (instruction-size, em-dash) naming a path this arm has not yet classified is never remedied by the gate's content fix: run this arm's classification on the named path first, then apply the gate guidance to whatever the arm leaves.
0d. **Missing-review-record adjudication (before any disposition).** Resolve `{plans_completed_dir}` and the main checkout's `{reviews_dir}` (never a worktree-local corpus: worktree review directories are bootstrap-time copies lacking records created after bootstrap). The corpus read resolves the main checkout wherever this run executes (see Run placement beside the lock matrix). Scan the archived plan files under `{plans_completed_dir}` for review-record references: filename literals containing `plan-review` or `code-review` with a trailing `-r<N>` before the extension (the repository's record-naming convention). A referenced record absent from the live reviews corpus is a reconstruction duty: report it in the run report (Step 7) with a witness note naming the citing plan and the missing path; the note may mention the docs branch as a historical last resort for records predating Step 2's add-only restore. State the bounds: never fabricate record content, never block the run (the loss already happened; blocking cannot recover it), never delete anything; cite-less legacy plans are undetectable by this arm.

1. Run `git status` and `git diff` (staged + unstaged) to see all changes.
   **Pre-commit guard (post sub-agent git op):** Step 2 `docs-branch` (and any prior sub-agent `git worktree`/`git checkout`/`git stash` operation) can leave the main repo's index/worktree in a REVERTED state relative to HEAD while HEAD stays correct. Before staging, run `git diff --cached --stat`: if it shows large deletions across files you did not edit this iteration (e.g. +73/-1062 across 14 files) OR the test count dropped vs the last known-good count on HEAD, a leaked revert is staged. Run `git reset --hard HEAD`, re-stage only your intended edits, then re-verify. Never a directory-wide add (no `git add -A`/`git add .`) here, or the rollback is swept into the commit. The same guard covers unstaged dirt that REGRESSES HEAD: after the cached-diff check, run the dirt regression gate (`python3 scripts/dirt_regression_gate.py --base <merge-base-with-default-branch>`, resolved via `git merge-base HEAD <default>`; skip with a one-line note when no default branch resolves) over the working tree's modified files; any file it names as a dirt REGRESSION is restored from HEAD (`git checkout -- <file>`) and reported, never staged or committed. (Witness: 2026-07-23 group-leftover-crypto-warnings r6; see project `development_lessons.md` lesson on this family.) The gate reports the outcome contract's four outcomes (scripts/OUTCOME_CONTRACT.md, final `OUTCOME:` line): on pass proceed; on fail restore the named files; on indeterminate or tool error stop this staging pass (do not stage or commit): report the gate's observed/could-not-determine or error lines and re-derive the tree from disk before any further staging. A run that emits no final `OUTCOME:` line is tool error under the contract: stop and re-derive. An indeterminate or tool-error result is never treated as pass or fail, and no dependent destructive or landing action continues on it.
1a. **Foreign-dirt gate (landing closeouts).** This paragraph explicitly supersedes Step 3 item 0's baseline arm for landing staging. Before staging, run the foreign-dirt gate: list uncommitted paths (staged, unstaged, untracked) and compare them against this session's owned path list, which comprises the run manifest's owned claims and every path this session created or modified during the run, attributed from the session's own records; every uncommitted path outside the list and not attributable to this session's recorded work is foreign: report it by path; unclaimed baseline dirt is reported and left unstaged for the next run, and a foreign path attributable to a live peer session aborts the landing (waiting is futile while this run holds the done lock the peer's own landing would need); never stage a foreign path. Disposition ladder: the item 0 ask for user-owned baseline dirt happens at Step 0, where an approval is recorded as an `--owned-path` claim before staging, and baseline dirt discovered unclaimed at landing is reported and left unstaged (it stays for the next run); a live peer session's uncommitted work is reported by path and the landing aborts. Landing commits use explicit pathspecs only; a directory-wide add in a landing closeout is a gate violation.
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
5. Stage relevant non-ignored files (including 4b when it applies). Prefer adding specific files by name; never a directory-wide add (no `git add -A` or `git add .`) unless the user explicitly requests it (that carve-out never applies in a landing closeout: item 1a makes a directory-wide add there a gate violation). On a shared checkout, also give the commit itself an explicit pathspec (`git commit -m "..." -- <paths>`), because a peer's staged-but-uncommitted entries sit in the shared index and a pathspec-less commit sweeps them (witnessed 2026-09-18: a learn commit naming its own two files swept a peer's staged backlog item). The inverse is equally binding: a pathspec commit builds from HEAD plus the named paths only, so it excludes your own staged changes outside the pathspec. After `git mv`, pass both the old and the new paths (or, when the index holds only your staged renames, commit the index state with a plain `git commit`) and verify the commit with `git show --stat -M` records the rename rather than a bare create. A pathspec naming a path that no longer exists on the branch (renamed away or deleted before the add) aborts the ENTIRE `git add` invocation while everything earlier commands staged survives, so a mixed rename+delete+add landing that chains one multi-path add through the removed old path commits without its new files while the message still claims them; after a failed add, stage the surviving paths in their own invocation, and before committing verify the staged stat names every path the message claims (witnessed twice 2026-10-02: archive commits landed missing the registry row and the new backlog file until the staged amend repaired them). And immediately before any `--amend` on a shared branch, re-run `git log -1 --oneline`: a peer commit landing between your commands turns the amend into a rewrite of their commit (new sha under their message, your staged leftovers inside); if that happened, verify the tree and stop rewriting (witnessed 2026-09-18, see user-corpus lesson #371). Committed witness lines (registry audit notes on new rows, disposition sections, and Status lines) name repo-relative paths and dates, never a landing digest; the digest belongs to the commit message and the session-side receipts.
5a. **Commit-time gate re-run (observation point).** After staging and before committing, re-run the pre-commit phase so the foreign-staging and plans-archive-twin gates observe the final staged set and the plans tree at the commit boundary, and record the re-run's exit line in the session notes beside the registry digest record.
5b. **Registry concurrent-writer detection arms.** When computing a document-registry edit, record the file's sha256 as the registry digest alongside the edit (in the session notes) before further edits. Before staging a landing commit that includes the document registry, verify the file's working-tree bytes still hash to the recorded registry digest; on a mismatch a concurrent writer intervened: stop, re-read the file, re-apply the session's rows onto the freshly read bytes (never write a pre-computed block; re-apply only rows not already present, matched byte-exact as full registry lines, not by row token), then confirm the written bytes by re-reading, recapture the registry digest, re-run the re-grep arm, re-stage, and re-run the pre-commit phase and the staged-blob check before committing. Before committing, re-grep that every registry row this session added is still present in the file being staged; a missing row means a concurrent write clobbered it: abort and reconcile instead of committing the loss. Immediately before committing, re-hash the working-tree registry bytes against the staged blob (`git ls-files -s`); on divergence a write landed after staging: re-run the verify arm (re-read, re-apply the session's rows not already present, matched byte-exact as full registry lines, onto the fresh bytes, confirm by re-reading, recapture the digest, re-run the re-grep arm, re-add) or abort.

**Reverse-squash arm (immediately before each commit):** after staging this session's files and immediately before each `git commit`, probe the guard copy (test -f on the repo-local `scripts/reverse_squash_guard.py` first, then on the deployed `$HOME/.ai-playbook/scripts/reverse_squash_guard.py`) and run the probed copy with `check-staged` from the repo root (`python3 scripts/reverse_squash_guard.py check-staged` when the repo-local probe hit); exit 1 means the staged set carries a reverse-squash signature (an archive-dir egress deletion or rename, a reviews-home egress addition under the deny set docs/reviews/ or docs/history/reviews/, or a diffstat mirror of one commit reachable from HEAD): print the detector output, unstage the refused set, and rebuild it from the intended edits; never commit the refused set; when the refused set is transplanted stale dirt rather than this session's intended edits, stop and surface the conflict for reconciliation in the Step 7 outcome report instead of restaging; when the findings are mirror-only and the deliberate-revert intent is recorded in the session notes, re-running with `--ack <sha>` naming the mirrored commit suppresses the mirror finding, and the acknowledged sha is written to the session notes at ack time and reported in the Step 7 outcome report (archive-egress and reviews-home findings are never ackable). Exit 2 is a tool failure: stop and report. When neither probe hits (cold start), print `reverse-squash guard absent; check skipped` and continue.

**Resolve-at-use digest rule (immediately before each commit):** any full digest this step writes into a commit message, receipt, or durable record, or passes as a digest argument to a landing or guard helper, obeys **resolve-at-use**: a full digest used in a state-changing command or a durable record is produced by `git rev-parse`, `git log --format=%H`, or `git show -s --format=%H` at the moment of use; landing helper invocations pass refs (branch names, `HEAD`, relative forms) rather than literal digests wherever the tool accepts them. (Added 2026-10-03; origin `docs/history/backlog/2026-10-02-sha-resolution-at-use-fence.md`; witness: the 2026-10-02 fabricated-digest slip, a 40-character digest whose tail was fabricated by hand from a 7-character display prefix and refused by the CAS old-value existence check.)

**Base-branch immutability rule and amend guard (immediately before each commit):** once a commit is reachable from the base branch it is never amended; corrections land as additive follow-up commits; amend is legal only inside a session's own unlanded branch before the landing critical section. Before each commit operation in this step, probe the base-branch amend guard copy (repo-local `scripts/base_branch_amend_guard.py` first, then the deployed `$HOME/.ai-playbook/scripts/base_branch_amend_guard.py`) and run the probed copy with `check-head --base-branch <base branch>` (the base branch resolves from the project's facts `base_branch` key or its project class, never a hardcoded name): exit 1 means HEAD is the base branch and its last reflog entry is an amend (`commit (amend)`) - stop the commit path and do not commit (the base-branch tip is immutable; the correction lands as its own additive commit naming the amended sha); ordinary additive commits are unaffected and proceed on exit 0; exit 2 is a tool failure: stop and report. When neither probe hits (cold start), print `base-branch amend guard absent; check skipped` and continue. (Added 2026-10-03; origin `docs/history/backlog/2026-10-02-base-branch-commit-immutability.md`; witness: the 2026-10-02 18:09 amend of a peer's landed tip, a peer session amending the base-branch tip another session had landed four minutes earlier.)

6. Write a concise commit message. If there is a story key, prefix with `[<STORY-KEY>]`; otherwise use a plain descriptive subject. Focus on the "why" not the "what". When the item 4a audit fired the drift witness, the commit body includes the `lesson-scope-audit:` body line exactly as specified in item 4a. When the audited corpus path is gitignored (no Step 3 corpus commit exists), the witness append on the docs branch carries the line instead; the append failure is a manual follow-up reported in the Step 7 outcome report and never blocks the Step 3 commit path.
7. Commit using a HEREDOC. **Never** add `Co-Authored-By:` or `Co-authored-by:` trailers or use `git commit --trailer` for agent attribution. See user `AGENTS.md` (Git Commit Trailer Policy). If your IDE adds co-author trailers automatically, disable agent attribution in its settings.
8. Run `git status` after the commit to confirm success.
9. **Owned-commits ledger append (Step 3 site):** after each project commit in this step, apply the Step 1 owned-commits ledger rule (same `owned-commits-<run_id>.txt` file, the same fused exact-SHA capture) so every commit this step creates is recorded; skip with the one-line note when the run has no manifest from Step 0. Each commit here is a done-executed commit, so its commit command and its ledger append run in ONE shell invocation, chained to the prescribed line:

```bash
git commit -m "<message>" -- <paths> && git rev-parse HEAD >> "$LEDGER"
```

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
3. Classify each dirty path as session-attributed (this session's non-learn skill edits, or failed-capture-set artifacts) or foreign. Ask the user before staging each session-attributed path (same discipline as Step 3 item 0; this step is the non-landing fallback, so Step 3 item 1a's landing foreign-dirt gate paragraph does not govern here, the baseline discipline does); never stage foreign or peer-session paths. For paths learn reported as skipped for foreign or unrecognizable hunks, review the path's diff and stage only after the user confirms the foreign hunks are acceptable (path-level staging stages the file as a whole); when they are not, leave the path unstaged and report it.
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

**Manifest finalize (immediately before the release):** set the run manifest's `complete` flag to true so this run is not left looking interrupted; first refresh the resumable-closeout checkpoint at this preamble (same filename, updated manifest sha and gate set) so an interruption during the finalize window still reads a current checkpoint; a run that dies before Step 6 leaves `complete` false, which is the interrupted-run signal the next Step 0 reports (a retry continues an interrupted run's boundary only through an explicit `adopted_from` adoption; with the widened detection a dead-root unadoptable manifest surfaces in the Step 0 report until it closes, while a dispositioned manifest is not re-reported as interrupted because the detection filter suppresses it, so the advisory fires until the incident closes and never after). Resolve `$LIB` exactly as in Step 0 (a repo-local `scripts/done_sweep_gates_lib.py` wins; otherwise derive the deployed lib path from the sweep-gates script default) and finalize with the Step 0 run_id. A missing manifest is tolerated with a one-line note and never blocks the release:

```bash
REPO_TOP="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
LIB="$REPO_TOP/scripts/done_sweep_gates_lib.py"
if [ ! -f "$LIB" ]; then
  LIB="${DONE_SWEEP_GATES_SCRIPT:-$HOME/.ai-playbook/scripts/done_sweep_gates.sh}"
  LIB="${LIB%done_sweep_gates.sh}done_sweep_gates_lib.py"
fi
# RUN_ID from the Step 0 manifest echo (chat context), same re-export
# discipline as the lock token.
if [ -z "${RUN_ID:-}" ]; then
  echo "finalize-manifest: no run manifest from Step 0; nothing to finalize"
else
  # The lib answers exit 0 with a note for a run without a manifest (the
  # only nothing-to-finalize path); any non-zero exit is a real failure and
  # must abort, never be masked as "nothing to finalize". A not-found note
  # while run-manifest-$RUN_ID.json still exists under the done-session
  # directory is the stale-finalizer signature (triage below). The manifest
  # subcommands are record flows outside the outcome contract's OUTCOME
  # coverage (scripts/OUTCOME_CONTRACT.md, batch 1): no final OUTCOME line
  # and legacy exits, so the contract's no-line rule does not apply here.
  python3 "$LIB" finalize-manifest --run-id "$RUN_ID"
  finalize_rc=$?
  if [ "$finalize_rc" -ne 0 ]; then
    echo "finalize-manifest: FAILED (exit $finalize_rc); the run manifest finalize did not complete" >&2
    exit "$finalize_rc"
  fi
fi
```

**Not-found and mismatch triage:** a `no run manifest found` note at finalize for a run_id this session exported, when the `run-manifest-<run_id>.json` file still exists under the done-session directory (`{tmp_dir}/done-session/`), is a stale-finalizer signature on first occurrence: the executing runtime twin predates the manifest identity contract, so redeploy the runtime twin once (refresh the deployed `done_sweep_gates_lib.py` from the repo-local `scripts/` copy, the copy the Step 0 `$LIB` resolution prefers) and retry the finalize. A second not-found note with the file still present is a corrupt record whose only supported response is re-running the Step 0 writer, never a manual edit of the record. An identity mismatch at finalize (the manifest's `schema` version is not the contract version, or its `repo_root` is not this repository's identity) is a named non-zero abort that leaves the manifest unchanged; its only supported response is re-running the Step 0 writer, never a manual completion-flag repair.

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

If release fails, read it through the outcome contract (`scripts/OUTCOME_CONTRACT.md`): `OUTCOME: fail` at exit 1 (token mismatch, or the lock changed under us), `OUTCOME: tool_error` at exit 3 (env missing, or the lock directory carries no metadata), and no final `OUTCOME:` line means tool error under the contract; then run `status` from the project root. When `status` shows free, your hold is already gone (peer auto-recovery, `stale-clean`, or release); do not source `.ai-playbook/done-lock.session` to “fix” env. A verified-dead holder is reclaimed by the next acquire even if its session fence remains; use `stale-clean` only for the explicit stale-lock escape, and ask the user before forcing removal of an **active** lock.

## Step 7: Report outcome to the user

**Never end `/done` silently after diagnostics.** Always send a short summary:

- Project repo: commit hash(es) created, or **working tree clean** at `HEAD` (include `git log -1 --oneline`).
- Skills / shared docs repos: commits created or none.
- Lock: confirm `status` shows **free** after Step 6.
- If `blocked` at Step 0, learn, or the Step 3 item 4a lesson scope audit: state why and what the user should run (`stale-clean`, fix corpus, classify the duplicated lesson, retry).
- Turn-end reason: in the run's final report, when the session executed under a standing queue-drain directive (recorded in the orchestrator's handoff context or the session's standing directive to execute plans), the report states the turn-end reason as a guard fire (a quota pause or near-reset with the Budget gate's constants on the interactive lane, a landing-gate hold reported by `scripts/done-lock.sh` merge-status, a lane hold from the scheduler guards, provider rate pressure with its structured rate-limited end) or an empty queue (no digest-intact open plan remains); a user interrupt or explicit abort is always sanctioned as well, and a request for the user to confirm starting the next plan is never a sanctioned turn end under such a directive.
- Record-bearing claim re-derivation (added 2026-10-03; origin `docs/history/backlog/2026-10-02-stale-read-record-derivation-fence.md`; witness: the 2026-10-02 ~17:17 stale-false reads that recorded a wrong conclusion into a user-facing report and a memory file): before this step's report states a **record-bearing claim**, a fact statement about repository state written into a durable channel (a user-facing report, a memory file, a backlog row, a commit message, a session note) whose wrongness outlives the session, the claim gets **two-command disk re-derivation**: immediately before a record write, re-derive the claimed fact with two independent commands: an existence claim via a filesystem probe (`ls`/`stat`) plus a git probe (`git cat-file -e <tip>:<path>` or `git show <tip>:<path>`); an absence claim via a working-tree `grep` plus `git grep` at the tip commit. A cross-check mismatch stops the record write until resolved.
- Base-branch immutability in reported commits (added 2026-10-03; origin `docs/history/backlog/2026-10-02-base-branch-commit-immutability.md`; witness: the 2026-10-02 18:09 amend of a peer's landed tip): once a commit is reachable from the base branch it is never amended; corrections land as additive follow-up commits; amend is legal only inside a session's own unlanded branch before the landing critical section; a commit sha this report cites is expected to stay reachable and immutable, so an amend of a cited commit surfaces as a cross-check mismatch under the re-derivation bullet above and stops the report write until resolved.

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
The pre-docs sweep gate run's review-staging gate validates this run's staging docs under `{reviews_dir}/` before docs-branch sync (candidates: `manifest-owned` review paths from the Step 0 run manifest when one is present, with the session-window porcelain plus ignored-matching fallback when it is not, filtered by the validator's `is_staging_review_path`; staging docs the manifest does not claim are reported as foreign and preserved, never validated as this run's own; include `*review*.md`, PR staging (`*-PR-*` / `PR-<n>-...`), and any path the predicate accepts, never only `*review*.md`). Complete Metadata, Review Statistics, and Findings with Comment/Analysis before continuing; do not sync stub staging docs.

### With `receiving-review` skill (review-thread closure gate)
`receiving-review`'s marker duty is the provider: a passive-review session writes the review-thread marker at feedback-processing start and keeps per-thread dispositions in it. `done` is the gate consumer: the pre-docs sweep's review-thread-closure gate runs `scripts/review_thread_gate.py` only for a marker whose recorded session identity matches the current session, failing closed while closure is not established. This skill does not restate the marker schema or reply idempotence rules (owned by `receiving-review`).

### With `plans` and `docs-branch` skills (docs/tmp sweep)
The pre-docs sweep gate run's docs-tmp-sweep gate sweeps `{tmp_dir}` entries whose owning plan archived (plans Plan Lifecycle cleanup; except an execute-plan session still holding its closeout-baseline.json, per the docs-tmp-sweep bullet) or that are one-off ownerless scratch; `review-loop*`/`code-review/`/`handoff/` scratch is never swept here (no liveness witness; their owning skills clean up). The `docs-branch` sync then drops branch-tracked `{tmp_dir}` paths absent on disk (`{tmp_dir}` is its one sweep-eligible root), so branch copies propagate without hand-editing the docs branch.

### With `release` skill
The `release` skill borrows this skill's per-worktree done lock (label `release-<date>`, acquired by its authoring step and released by its final shell call, mirroring Steps 0 and 6): during a `release` skill run (the squash-and-publish workflow; unrelated to the done-lock release in Step 6), done neither commits nor pushes. The release run commits only its own CHANGELOG notes commit and publishes through its persisted push script; the reciprocal note lives in the `release` skill's Integration Points.

## Rules

- Always acquire the Step 0 project lock before learn or any project-side commit steps; always release it in Step 6 (`release-repo` from project git root).
- Wrap the Step 2 ad-hoc-worktree migration and docs-branch sync in the repository-keyed merge lock (`merge-wait-acquire --label done-docs-sync --max-wait 300`) and release it with `merge-release-repo` on every exit path; never enter either critical section unlocked, and never re-acquire to fix a failed release (run `merge-status` and report the holder state instead).
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
