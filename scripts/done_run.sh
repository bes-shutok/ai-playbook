#!/usr/bin/env bash
# done_run.sh - thin orchestrator composing the done closeout's mechanical
# steps. Subcommands: setup, commit, finalize. The runner adds no gate and no
# ledger, and it authors exactly one refusal class of its own: incompatible
# transition inputs for setup (--from-manifest with ownership options or with
# --adopt, and an --adopt target that names no adoptable boundary); every
# other refusal it prints is one of the composed commands' own named errors,
# the parse-time usage errors (an unknown argument or an empty flag operand),
# or the relocated one-for-one setup refusals below (the empty-echo abort and
# the partial-setup classification stop), each moved verbatim from the done
# skill's Step 0 text (plan
# docs/history/plans/completed/2026-10-25-done-run-resume-ownership-gap.md).
#
# Usage:
#   done_run.sh setup [--label TEXT] [--from-manifest RUN_ID]
#        [--adopt RUN_ID]
#        [--owned-plan PATH]... [--owned-review PATH]... [--owned-path PATH]...
#        [--foreign-review PATH]... [--foreign-review-from FILE] [--claim-none]
#   done_run.sh commit --stage PATH... --subject TEXT
#        [--expected-ref REF --expected-oid OID]
#        [--guard-firing NAME:KIND:EVIDENCE[:NOTE]]...
#        [--learn-receipts-from FILE] [--revert-formatting PATH]...
#        [--side-commit REPO_PATH]... [--manifest PATH] [--run-id RUN_ID]
#        [--authorize-ancestor-restoration PATH BLOB_ID]
#        [--authorize-dirt-correction PATH BLOB_ID]...
#   done_run.sh finalize [--manifest PATH] [--run-id RUN_ID]
#        [--from-holder] [--session IDENTITY] [--no-landing-cost]
#        [--guard-firing NAME:KIND:EVIDENCE[:NOTE]]...
#
# finalize composes the closeout's release ceremony: the resumable-closeout
# checkpoint refresh (a no-checkpoint refusal falls back to create-then-
# refresh; an already-finalized manifest skips the refresh arm), the run
# manifest finalize (a missing manifest is a one-line note; any other
# non-zero exit aborts after the releases, never masking the error), the
# checkpoint remove, the done-lock release (env-token path by default; with
# --from-holder, or when the exports are lost, the lock script's
# metadata-sourced release arm under its own recorded guards: the hold was
# pinned at acquire, the recorded hostname matches this host, the recorded
# holder is verifiably alive with exact identity, is not pid 1, and this
# shell descends from it - every refusal names the failed gate), the
# merge-lock release when a hold survives (exports when present, else the
# same from-holder arm), and the status-free verification. It then assembles
# the report inputs: the landing summary from the run's owned-commits ledger
# and the report-only missing-review-record scan over the archived plans
# (missing review records are reported, never blocking, never fabricated).
# The guard-firing rows finalize receives never append directly and never
# append twice after a successful landing (plan
# 2026-10-24-done-run-lock-span-and-append-ordering): with a prior landing
# commit they are reported as already carried by it; with no prior landing
# they land through the checked commit subcommand as a child while the done
# lock is still held, the child writing them before its declared staging and
# landing the ledger bytes in its own commit; a child failure before its
# landing restores the prior ledger bytes and index, a failure after the
# landing preserves the committed row and reports without rollback; every
# outcome is a warning line and the release still runs. The landing-cost
# telemetry line runs last, never blocking: one
# line when this run landed work in the project repo (skip with --no-
# landing-cost or when nothing landed; a failed append is a warning line).
#
# setup composes, in order: the rearm-on-touch echo (advisory), the done-lock
# wait-acquire with the short agent wait (DONE_LOCK_AGENT_MAX_WAIT_SECS,
# default 90), the runtime-helper drift advisory (echo-and-continue), the
# worktree residue sweep (fail-open), the partial-setup classification (the
# sweep-gates lib's classify-run-boundary verdict at run identity: a terminal
# boundary continues to the fresh marker and manifest behind a one-line note,
# an unresolved orphan takes the verbatim refusal remedies, an unreadable
# record fails closed), the run-start marker write, and the run
# manifest write bound to that marker via --run-marker; a manifest whose
# owned_plan_paths count is not exactly one also gets the run-ID-keyed
# migration skip record (worktree-migrate-baseline-<run id>-skip.json)
# written in the same session directory - the commit stage's only
# zero/multi-plan skip evidence - and the explicit --from-manifest re-entry
# completes the same producer duty for its re-entered boundary. An explicit
# --adopt RUN_ID continues the classified interrupted boundary: it routes to
# the writer's existing adoption only when it names the classified orphan run
# ID (an orphan-verdict mismatch, a classified terminal or already-adopted
# boundary's own ID, or --from-manifest combined with ownership options or
# --adopt each refuse before any new marker or manifest; a mismatched target
# whose own boundary classifies already-adopted or dispositioned refuses the
# same way before the fresh marker; any other mismatched target against a
# terminal-newest boundary is not refused here - the fresh boundary carries
# it to the writer's own adoption validations, and a refused write rolls the
# fresh marker back), and the writer carries the prior start
# commit and ownership claims into the new linked manifest. On success it
# prints one status line on stdout followed by eval-able export lines for the
# downstream consumers: DONE_LOCK_DIR, DONE_LOCK_TOKEN, DONE_RUN_MARKER,
# DONE_RUN_MANIFEST, DONE_RUN_ID.
#
# Every terminal classification and fail-closed exit after the acquire
# releases only the lock generation that invocation acquired (the env-token
# release arm; the token compare-and-swap never releases a newer generation,
# and a refused release is one warning line) before exiting with the
# original refusal outcome and remedy text, so the remedy-and-retry path
# never waits on the stopped attempt's own hold; the successful
# --from-manifest re-entry keeps the acquired lock.
#
# commit owns the collapsed Step 3 (the plan's authoritative composed order):
# stage by explicit pathspec from the run's owned set (--stage, gitignored
# paths reported and never staged), append staged plans-root paths to the
# deliverables file, the stale-checkout adjudication (revert_set_classifier
# classify restores ancestor-blob debris outside the declared set, never
# staging it), the cached-diff guard (a declared staged path whose content
# equals an ancestor vintage is the relocated leaked-revert stop), the
# staged-scope guard, the foreign-dirt disposition ladder (a manifest
# foreign claim aborts the landing; other unclaimed dirt is reported and
# left), the formatting-only candidate list (no revert without
# --revert-formatting), the unused-import pass (skip-note when no linter
# resolves; findings report-only), the lesson-scope audit when the lessons
# corpus is touched, the --learn-receipts-from ledger appends
# (post-hoc-from-receipt, before the sweep), the landing sweep over the
# final staged set, and the description-length pre-refusal catch record: a
# sweep result of gate=description-length with rc=1 is the one modeled
# over-cap class, and its catch row (run identity in the existing note
# field, deduplicated by the ledger writer for sequential retries) is
# appended to scripts/gate_liveness_ledger.json while the done lock is
# still held and before the commit refuses; that refusal names the ledger
# path as a required declaration for the next successful retry (declare the
# fixed description and the ledger JSON together so the catch lands with
# the fix); a ledger append failure refuses naming the unrecorded catch;
# sweep results with rc=2 (indeterminate) or rc=3 (tool error) refuse
# without a catch. Then the docs-branch sync (the worktree migration precedes it
# in an ad-hoc worktree, reusing the run's one pre-work Phase 0 baseline or
# its valid skip record, never capturing a late baseline; the sync holds its own runner-owned merge-lock
# span; --boundary-class per-task skips the sync as a final-closeout leg and
# forwards the class to the landing sweep, whose per-task roster drops the
# primary-checkout inspection; the default final-closeout keeps today's
# behavior byte-identically; the sweep-gates runner's usage text is the
# canonical roster split), the registry digest arm, the reverse-squash
# check-staged, and exactly one captured-tree landing with the owned-commits
# ledger append fused to it. That landing records the staged tree with git
# write-tree, runs the dirt regression gate exactly once against that
# captured tree (--tree mode: classification reads the immutable tree, never
# the mutable worktree), captures HEAD's symbolic target and OID (or
# detached state and direct HEAD OID) before the hooks, runs pre-commit,
# prepare-commit-msg, and commit-msg in Git order with normal
# args/env/message-file handling, refuses any hook failure or staged-index
# tree change, re-verifies each authorized blob against the captured tree
# before the hooks run, revalidates the live run tuple immediately before
# the ref update, and lands the unchanged tree with sole
# parent at captured HEAD through one compare-and-swap ref transaction
# (git update-ref --stdin; direct HEAD with no-deref when detached, never
# creating a branch), the owned-commits ledger append fused after the swap,
# and post-commit run last (its failure cannot undo the commit; it sees the
# actual HEAD, including after a checkout race). The landing reports the
# captured destination: only the captured branch advances, and a later
# checkout cannot retarget the commit. Reference-transaction hooks keep
# their standard phases and veto power; their side effects are outside the
# wrapper guarantee. Ordinary (unauthorized) and authorized commits share
# this one captured-tree landing flow. That landing commit refuses an empty
# declared set over a non-empty staged index, naming every staged path as
# the foreign set, and keeps the clean-index skip (no staged changes;
# landing commit skipped). The base-branch immutability rule is reported as
# a warning line, never a refusal. The subcommand then walks the
# facts-resolved side repos (user-facts keys skills_repo_path and
# shared_docs_dir), reports dirty paths per repo, and executes one
# confirmed commit action per repo named by --side-commit, re-running the
# public-hygiene scan over each staged side-repo set before that repo's
# commit. With --authorize-ancestor-restoration PATH BLOB_ID the
# invocation authorizes exactly one declared staged restoration to the
# named blob, bound to the current run: the newest root-confirmed marker,
# the manifest bound to it (selected exports, run id, and repo root must
# match), and the live env-token done lock must all resolve before any ref
# update, the authorized path must sit in the declared set with a staged
# blob equal to BLOB_ID, and the cached-diff guard lifts only that path
# (every other ancestor-matching path still refuses). With
# --authorize-dirt-correction PATH BLOB_ID (repeatable) the invocation
# authorizes one finite correction set: an exact mapping from each
# operator-declared path to that path's expected staged blob, bound to the
# operator direction and the same live run tuple; at the landing each
# mapping entry's blob must still equal the path's blob in the captured
# tree, and the dirt regression gate lifts only a regressed path the set
# names with the exact matching blob, while indeterminate and tool-error
# classifier outcomes, stale runs, duplicate or undeclared paths, malformed
# mappings, and unmatched regressions all refuse. The two authorizations
# are separate: neither satisfies or lifts the other guard. Nothing about
# either authorization is persisted to the manifest, staging, message, or
# classifier. When DONE_RUN_TRACE_FILE
# is set the subcommand appends
# one `stage <name>` line per composed stage, so a run's trace shows the
# order the plan fixes. The invocation's repeated --guard-firing
# NAME:KIND:EVIDENCE[:NOTE] rows append to scripts/gate_liveness_ledger.json
# BEFORE the declared-path staging and the landing sweep (plan
# 2026-10-24-done-run-lock-span-and-append-ordering): accepted rows stage the
# ledger path into the declared set so the bytes ride the landing commit
# exactly once; a malformed firing or a failed append is one warning line;
# the writer's pre-write public-hygiene screen leaves the canonical ledger
# bytes unchanged and skips a flagged advisory row without refusing the
# landing.
#
# The primary rolling-log transaction (--expected-ref/--expected-oid given
# as one pair) binds a write to either rolling prompt log
# (docs/history/backlog/PLAN-PROMPTS.md or docs/history/backlog/EXEC-
# PROMPTS.md) to the caller-selected branch: the caller selects the symbolic
# ref and starting OID under the primary done lock before the final log
# read or edit and passes them unchanged; the runner rechecks the pair
# before staging and inside captured_tree_landing before and after the tree
# capture (the post-hook and pre-transaction HEAD-identity checks then
# carry the same captured pair through the compare-and-swap), the declared
# set is limited to the two log paths, a two-path pre-stage guard refuses
# when either log already has a staged delta, and an early guard refuses
# any other staged path before staging. Once staging begins, one cleanup
# owner (an EXIT trap) unstages and verifies only this writer's declared
# owned log delta on every refusal before the captured-ref swap succeeds;
# it disarms immediately after the swap, so a later ledger-append or
# post-commit-hook failure reports that the landed commit stands, and an
# unverifiable cleanup reports blocked recovery (the two-path guard then
# refuses the next primary log writer). The mode never takes the repo-wide
# merge lock: the docs-branch sync (a final-closeout leg) is skipped.
# Pair-less calls, worktree log commits, and every other behavior keep
# their existing paths unchanged.
#
# Env: DONE_LOCK_SCRIPT overrides the lock script (default: this repo's
# scripts/done-lock.sh, then the deployed home copy); the sweep-gates lib is
# resolved from this repo's scripts/ then the deployed home copy. All other
# DONE_LOCK_* / MERGE_LOCK_* / DONE_SWEEP_* variables pass through to the
# composed commands unchanged; the one exception the runner composes itself
# is DONE_SWEEP_DECLARED_STAGE_PATHS, written by the commit subcommand for
# its own landing-sweep invocation only (the final declared set, one path
# per line; actively unset for the sweep subprocess when the declared set is
# empty), never passed through. DONE_RUN_LINTER overrides the unused-import
# linter (default: ruff resolved from PATH).
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOME_SCRIPTS="${HOME}/.ai-playbook/scripts"

resolve_helper() { # name -> prints path or nothing
  if [ -f "$SCRIPT_DIR/$1" ]; then printf '%s\n' "$SCRIPT_DIR/$1"
  elif [ -f "$HOME_SCRIPTS/$1" ]; then printf '%s\n' "$HOME_SCRIPTS/$1"; fi
}

# Release the done-lock generation this setup invocation acquired, on the
# terminal exits below. The env-token release-repo arm is the same path
# finalize composes: the acquire's own exports name the hold and the token
# compare-and-swap releases only that generation, never a newer one, so no
# reentrant or holder-ancestry semantics are added. The release output is
# echoed; a refused release is one warning line and the caller's original
# refusal outcome and remedy text stay the exit of record. The exports-lost
# acquire corner keeps its own refusal: no token, no generation to name.
# The no-OUTCOME-pass acquire corner is the second tokenless corner (an
# acquire that holds but emits no final OUTCOME line discards its exports
# unadopted before this arm runs), so its hold waits for the lock script's
# stale-clean or the operator; this arm names no token to release it with.
setup_release_acquired_lock() { # -> prints the release output; never refuses
  local rel_out rel_rc=0
  [ -n "${LOCK_SCRIPT:-}" ] && [ -n "${DONE_LOCK_DIR:-}" ] && [ -n "${DONE_LOCK_TOKEN:-}" ] || return 0
  rel_out="$(DONE_LOCK_DIR="$DONE_LOCK_DIR" DONE_LOCK_TOKEN="$DONE_LOCK_TOKEN" \
    bash "$LOCK_SCRIPT" release-repo 2>&1)" || rel_rc=$?
  printf '%s\n' "$rel_out"
  if [ "$rel_rc" -ne 0 ]; then
    echo "done_run setup: WARNING: the acquired done lock did not release (rc=$rel_rc); the refusal above still stands; re-derive the hold with the lock script's status" >&2
  fi
  return 0
}

# A terminal setup exit after the acquire: release this invocation's
# generation, then exit with the original refusal code.
setup_die() { # rc
  setup_release_acquired_lock
  exit "$1"
}

fail_partial() { # step evidence
  echo "done Step 0 partial-setup: $1; $2; no manifest bound" >&2
  setup_die 1
}

# Compose the CWD repo's facts-resolved done-session directory; print nothing.
session_dir() {
  local repo_top tmp_dir
  repo_top="$(git rev-parse --show-toplevel 2>/dev/null)" || return 1
  tmp_dir="$(sed -n 's/^tmp_dir = ["'\'']\(.*\)["'\'']$/\1/p' \
    "$repo_top/.ai-playbook/facts.md" 2>/dev/null | head -n 1)"
  tmp_dir="${tmp_dir:-$repo_top/docs/tmp/}"
  case "$tmp_dir" in /*) ;; *) tmp_dir="$repo_top/$tmp_dir";; esac
  printf '%s\n' "${tmp_dir%/}/done-session"
}

# Content-confirm a marker against the CWD repo root (digest middle field).
marker_confirms() { # marker-path -> rc
  local repo_top digest recorded
  repo_top="$(git rev-parse --show-toplevel 2>/dev/null)" || return 1
  digest="$(printf '%s' "${repo_top%/}" | (shasum -a 256 2>/dev/null || sha256sum) | awk '{print $1}')"
  recorded="$(awk '{print $2}' "$1" 2>/dev/null)"
  [ -n "$digest" ] && [ "$recorded" = "$digest" ]
}

# The zero/multi-plan producer half of the run-ID-keyed migration skip
# record: a run manifest that does not select exactly one owned plan has no
# plan baseline the commit stage's migration leg may reuse, and this record
# is that leg's only skip evidence. Setup writes it beside its own session
# resolution - the same directory the commit leg reads - so producer and
# consumer never disagree on the location, and a single-plan run writes
# nothing (its baseline route needs no skip evidence). Idempotent per run
# id; returns non-zero only when the write itself fails.
write_zero_multi_plan_skip_record() { # session manifest-path -> rc
  local session="$1" manifest="$2" run_id count record
  [ -n "$session" ] && [ -n "$manifest" ] && [ -f "$manifest" ] || return 0
  run_id="$(manifest_scalar "$manifest" run_id)"
  [ -n "$run_id" ] || return 0
  count="$(manifest_field "$manifest" owned_plan_paths | grep -c .)"
  [ "$count" -eq 1 ] && return 0
  record="$session/worktree-migrate-baseline-$run_id-skip.json"
  if [ ! -f "$record" ]; then
    printf '%s\n' "{\"skip\": true, \"reason\": \"owned_plan_paths selects $count owned plan(s); no single plan baseline to reuse; the manual scoped copy is the session's before-commit duty\", \"fallback\": \"manual scoped copy\"}" \
      > "$record" || return 1
  fi
  echo "done_run setup: zero/multi-plan run: migration skip record present: $(basename "$record")"
  # Migrate-shape twin (lesson 289): a branch-only gate-removal pass reads
  # the migration manifest's shape, which no zero-plan producer wrote before
  # this skeleton, so setup emits it at the same session resolution with the
  # same run-id idempotency. Separate file; the session manifest stays
  # field-frozen. The scoped-copy arm appends each verified transfer to the
  # skeleton's migrated list (the Worktree-first standard's baseline-less
  # closeout arm).
  local skeleton repo_top run_branch
  skeleton="$session/worktree-migrate-baseline-$run_id-manifest.json"
  if [ ! -f "$skeleton" ]; then
    repo_top="$(git rev-parse --show-toplevel 2>/dev/null)" || repo_top=""
    run_branch=""
    [ -n "$repo_top" ] && run_branch="$(git -C "$repo_top" branch --show-current 2>/dev/null)"
    if [ -n "$repo_top" ] && [ -n "$run_branch" ]; then
      printf '%s\n' "{\"branch\": [{\"branch\": \"$run_branch\", \"source\": \"$repo_top\"}], \"migrated\": []}" \
        > "$skeleton" || return 1
      echo "done_run setup: zero/multi-plan run: migrate-shape manifest skeleton present: $(basename "$skeleton")"
    else
      echo "done_run setup: zero/multi-plan run: no checkout root or current branch resolved; migrate-shape manifest skeleton not written (the branch-only hand-build remedy keeps applying)" >&2
    fi
  fi
  return 0
}

# Classify a found partial setup; print the remedy lines on stderr and, for
# an explicit --from-manifest re-entry, the audit exports on stdout, and for
# an explicit --adopt of the classified orphan a routing note before the
# fresh adopting boundary (the refusal class below never writes).
# Read-only except the re-entry arm's one zero/multi-plan skip-record write
# (the same producer duty a fresh setup performs; a plain classification
# writes nothing). Its terminal exits release the acquired lock generation
# through setup_die before exiting with the original refusal. The state
# verdict comes from the repo-local
# sweep-gates lib's classify-run-boundary subcommand (the canonical
# RunManifest parse plus the adopted-set orphan filter, read at run identity
# over every run-manifest-*.json record sharing the newest file's payload run
# id); bash holds no manifest state predicate of its own: a terminal verdict
# (finalized | adopted | dispositioned | shadow-closed) continues to the
# fresh boundary behind a one-line note, an orphan verdict takes the verbatim
# remedy refusals, and an unreadable record fails closed naming the file.
classify_partial() { # from_manifest(empty allowed) adopt_target(empty allowed)
  local session from_manifest adopt_target newest_marker newest_manifest mid marker_name verdict
  session="$(session_dir)" || return 1
  from_manifest="$1"
  adopt_target="${2:-}"
  newest_marker=""
  for f in "$session"/run-start-*; do
    [ -f "$f" ] || continue
    if marker_confirms "$f"; then
      if [ -z "$newest_marker" ] || [ "$f" \> "$newest_marker" ]; then newest_marker="$f"; fi
    fi
  done
  newest_manifest=""
  for f in "$session"/run-manifest-*.json; do
    [ -f "$f" ] || continue
    if [ -z "$newest_manifest" ] || [ "$f" \> "$newest_manifest" ]; then newest_manifest="$f"; fi
  done
  if [ -z "$newest_marker" ] && [ -z "$newest_manifest" ]; then
    return 1  # fresh setup
  fi
  if [ -n "$newest_manifest" ]; then
    # The canonical classification owner: the verdict is read at run identity
    # through the lib's RunManifest parse and the adopted-set orphan filter.
    local lib class_out
    lib="$(resolve_helper done_sweep_gates_lib.py)"
    if [ -z "$lib" ]; then
      echo "done_run setup: no done_sweep_gates_lib.py resolved (repo-local scripts/ or deployed home); cannot classify: $(basename "$newest_manifest")" >&2
      setup_die 3
    fi
    class_out="$(python3 "$lib" classify-run-boundary --session-dir "$session" --manifest "$newest_manifest" 2>&1)" || {
      printf '%s\n' "$class_out" >&2
      echo "done_run setup: the manifest-state classifier failed; no new boundary written (fail-closed)" >&2
      setup_die 3
    }
    verdict="$(printf '%s\n' "$class_out" | sed -n 's/^verdict: //p')"
    mid="$(printf '%s\n' "$class_out" | sed -n 's/^run_id: //p')"
    marker_name="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("marker",""))' "$newest_manifest" 2>/dev/null)"
    if [ "$verdict" = "unreadable" ]; then
      echo "done_run setup: found an unparseable run manifest record: $(basename "$newest_manifest") (corrupt or schema-invalid; run_id unreadable)" >&2
      echo "done_run setup: no new boundary written (fail-closed; repair or remove the named record explicitly)" >&2
      setup_die 2
    fi
    case "$verdict" in
      finalized|adopted|dispositioned|shadow-closed)
        if [ -z "$from_manifest" ]; then
          if [ -n "$adopt_target" ] && [ "$adopt_target" = "$mid" ]; then
            echo "done_run setup: --adopt $adopt_target names the classified boundary run_id=$mid, which is $verdict (closed; only an interrupted orphan boundary is adoptable); no new boundary written" >&2
            exit 1
          fi
          if [ -n "$adopt_target" ]; then
            # A mismatched target gets its own boundary read first (the same
            # classify-run-boundary machinery the writer applies): an
            # already-adopted or dispositioned target refuses here, before
            # the fresh marker, instead of forwarding a closed boundary to
            # the writer; any other read (orphan, finalized, unreadable, a
            # missing target record, or a failed probe) forwards unchanged to
            # the writer's own adoption validations.
            local target_manifest target_out target_verdict
            target_manifest="$session/run-manifest-$adopt_target.json"
            if [ -f "$target_manifest" ]; then
              target_out="$(python3 "$lib" classify-run-boundary --session-dir "$session" --manifest "$target_manifest" 2>/dev/null)" || target_out=""
              target_verdict="$(printf '%s\n' "$target_out" | sed -n 's/^verdict: //p')"
              case "$target_verdict" in
                adopted)
                  echo "done_run setup: --adopt $adopt_target names run_id=$adopt_target, whose own boundary is already adopted (closed; only an interrupted orphan boundary is adoptable); no new boundary written" >&2
                  exit 1
                  ;;
                dispositioned)
                  echo "done_run setup: --adopt $adopt_target names run_id=$adopt_target, whose own boundary is dispositioned (closed; only an interrupted orphan boundary is adoptable); no new boundary written" >&2
                  exit 1
                  ;;
              esac
            fi
            echo "done_run setup: newest manifest run_id=$mid is $verdict (closed boundary); --adopt $adopt_target is not the classified boundary and is forwarded to the writer's own adoption validations behind the fresh marker (a refused write rolls that marker back)"
          else
            echo "done_run setup: newest manifest run_id=$mid is $verdict (closed boundary); continuing with a fresh marker and manifest"
          fi
          return 1
        fi
        ;;
      orphan)
        ;;  # the unadopted-boundary remedies below, verbatim
      *)
        echo "done_run setup: unknown boundary verdict from the classifier: $verdict" >&2
        setup_die 3
        ;;
    esac
    # Explicit adoption routing (plan 2026-10-25-done-run-resume-ownership-gap):
    # a classified orphan boundary is adoptable only by its own run ID, and a
    # matching --adopt continues past the remedies to the writer's existing
    # adoption below, which preserves the prior start commit and ownership
    # claims; both refusals here precede any new marker or manifest.
    if [ -z "$from_manifest" ] && [ -n "$adopt_target" ]; then
      if [ "$adopt_target" != "$mid" ]; then
        echo "done_run setup: --adopt $adopt_target names no classified interrupted boundary (classified run_id: ${mid:-none}); only the classified orphan boundary may be adopted; no new boundary written" >&2
        exit 1
      fi
      echo "done_run setup: adopting the classified interrupted boundary run_id=$mid via --adopt (the manifest writer carries its start commit and ownership claims into the new manifest)" >&2
      return 1
    fi
    if [ -n "$newest_marker" ] && [ "$marker_name" = "$(basename "$newest_marker")" ]; then
      echo "done_run setup: found an unadopted current-boundary manifest run_id=$mid bound to the newest content-confirmed marker" >&2
      echo "done_run setup: remedies: python3 scripts/done_sweep_gates_lib.py recover-manifest --run-id $mid | re-enter exactly with --from-manifest $mid | adopt via setup --adopt $mid | python3 scripts/done_sweep_gates_lib.py finalize-manifest --run-id $mid" >&2
    else
      echo "done_run setup: found a stale-marker or markerless interrupted manifest run_id=${mid:-unknown}" >&2
      echo "done_run setup: remedies: python3 scripts/done_sweep_gates_lib.py recover-manifest --run-id ${mid:-<id>} | adopt via setup --adopt ${mid:-<id>} | re-enter exactly with --from-manifest ${mid:-<id>} | python3 scripts/done_sweep_gates_lib.py finalize-manifest --run-id ${mid:-<id>} | python3 scripts/done_sweep_gates_lib.py disposition-manifest --run-id ${mid:-<id>} (dead root only)" >&2
    fi
    if [ -n "$from_manifest" ]; then
      if [ "$from_manifest" != "$mid" ]; then
        echo "done_run setup: --from-manifest $from_manifest names no found boundary (found: ${mid:-none})" >&2
        setup_die 1
      fi
      RUN_MARKER_PATH=""
      [ -n "$newest_marker" ] && [ "$marker_name" = "$(basename "$newest_marker")" ] && RUN_MARKER_PATH="$newest_marker"
      echo "done_run setup: re-entering boundary run_id=$mid (explicit --from-manifest)"
      # the re-entered boundary completes the zero/multi-plan producer duty
      # before its exports are handed back, so an interrupted setup never
      # strands its run without the commit stage's skip evidence
      write_zero_multi_plan_skip_record "$session" "$newest_manifest" || {
        echo "done_run setup: the zero/multi-plan migration skip record write failed for the re-entered boundary" >&2
        setup_die 1
      }
      echo "export DONE_RUN_MANIFEST=$(printf '%q' "$newest_manifest")"
      echo "export DONE_RUN_ID=$mid"
      echo "export DONE_RUN_MARKER=$(printf '%q' "$RUN_MARKER_PATH")"
      return 0
    fi
    echo "done_run setup: no new boundary written (read-only classification; pass --from-manifest to re-enter explicitly)" >&2
    setup_die 2
  fi
  # Marker without manifest: the interrupted attempt died inside the marker
  # recipe or before the writer; the marker-boundary remedy is a fresh write
  # (the writer's --run-marker binding governs identity), so report and stop.
  echo "done_run setup: found a content-confirmed marker with no manifest (partial marker write)" >&2
  echo "done_run setup: remedy: re-run setup to write the manifest bound to that marker, or remove the marker to discard the attempt" >&2
  echo "done_run setup: no new boundary written" >&2
  setup_die 2
}

cmd_setup() {
  # WM_ARGS and ADOPT_ARGS are function-local so an environment-inherited
  # WM_ARGS can neither satisfy the mixed-input probe below nor leak into the
  # writer call (a declared-empty bash array reads unset under ${var+set}).
  local label="" from_manifest="" adopt_target="" ownership_opts=""
  local WM_ARGS=() ADOPT_ARGS=()
  shift # subcommand
  while [ $# -gt 0 ]; do
    case "$1" in
      --label) label="$2"; shift 2;;
      --from-manifest)
        if [ -z "${2:-}" ]; then
          echo "done_run setup: --from-manifest requires a run-id operand (got an empty operand)" >&2
          exit 3
        fi
        from_manifest="$2"; shift 2;;
      --adopt)
        if [ -z "${2:-}" ]; then
          echo "done_run setup: --adopt requires a run-id operand (got an empty operand)" >&2
          exit 3
        fi
        adopt_target="$2"; shift 2;;
      --owned-plan|--owned-review|--owned-path|--foreign-review)
        WM_ARGS+=("$1" "$2"); shift 2;;
      --foreign-review-from)
        WM_ARGS+=("$1" "$2"); shift 2;;
      --claim-none) WM_ARGS+=("$1"); shift;;
      *) echo "done_run setup: unknown argument: $1" >&2; exit 3;;
    esac
  done

  # Incompatible transition inputs (one refusal class, plan
  # 2026-10-25-done-run-resume-ownership-gap): --from-manifest is exact
  # re-entry and never carries ownership options or an adoption target. Both
  # mixed forms refuse here, before any advisory, lock, marker, or manifest,
  # and the refusal names setup --adopt as the supported transition.
  if [ -n "$from_manifest" ]; then
    if [ -n "$adopt_target" ]; then
      echo "done_run setup: --from-manifest $from_manifest and --adopt $adopt_target are conflicting modes; --from-manifest is exact re-entry and changes no claims; to add ownership claims to that boundary, run setup --adopt $from_manifest with them" >&2
      exit 3
    fi
    if [ "${WM_ARGS+set}" = "set" ]; then
      ownership_opts="$(printf '%s ' ${WM_ARGS+"${WM_ARGS[@]}"})"
      echo "done_run setup: --from-manifest is exact re-entry and cannot carry ownership options (${ownership_opts% }); to add those claims to boundary $from_manifest, run setup --adopt $from_manifest with them" >&2
      exit 3
    fi
  fi

  # 1. Rearm-on-touch echo (advisory, echo-and-continue).
  REARM="$(resolve_helper rearm_on_touch.py)"
  if [ -n "$REARM" ]; then
    REARM_OUT="$(python3 "$REARM" 2>&1 || true)"
    echo "done_run setup: rearm-on-touch (advisory): $(printf '%s' "$REARM_OUT" | head -n 1)"
  else
    echo "done_run setup: rearm-on-touch (advisory): helper not deployed; skipped"
  fi

  # 2. Done-lock wait-acquire with the short agent wait.
  LOCK_SCRIPT="${DONE_LOCK_SCRIPT:-$(resolve_helper done-lock.sh)}"
  if [ -z "$LOCK_SCRIPT" ]; then
    echo "done-lock: no lock script resolved (set DONE_LOCK_SCRIPT)" >&2
    exit 3
  fi
  LABEL="${label:-$(git branch --show-current 2>/dev/null || echo unknown-branch)}"
  MAX_WAIT="${DONE_LOCK_AGENT_MAX_WAIT_SECS:-90}"
  LOCK_ERR="$(mktemp)"
  if ! LOCK_EXPORTS="$(bash "$LOCK_SCRIPT" wait-acquire --label "$LABEL" --max-wait "$MAX_WAIT" 2>"$LOCK_ERR")"; then
    bash "$LOCK_SCRIPT" status >&2 || true
    echo "done-lock: acquire outcome: $(grep -E '^OUTCOME: ' "$LOCK_ERR" | tail -n1)" >&2
    case "$(grep -E '^OUTCOME: ' "$LOCK_ERR" | tail -n1)" in
      "OUTCOME: fail")
        echo "done-lock: blocked after ${MAX_WAIT}s; another done holds the lock" >&2
        echo "done-lock: if holder PID is dead or lock is stale, run: $LOCK_SCRIPT stale-clean" >&2 ;;
      "OUTCOME: indeterminate")
        echo "done-lock: holder state ambiguous; the hold cannot be adjudicated: report and stop (stale-clean stays the explicit operator escape only)" >&2 ;;
      *)
        echo "done-lock: lock tool error (outcome: $(grep -E '^OUTCOME: ' "$LOCK_ERR" | tail -n1)); fix the invocation or environment and re-derive from disk with status" >&2 ;;
    esac
    rm -f "$LOCK_ERR"
    exit 2
  fi
  grep -qx 'OUTCOME: pass' "$LOCK_ERR" || {
    echo "done-lock: acquire emitted no final OUTCOME: pass on stderr; treating as tool error" >&2
    rm -f "$LOCK_ERR"
    exit 2
  }
  rm -f "$LOCK_ERR"
  eval "$LOCK_EXPORTS"
  printf '%s\n' "$LOCK_EXPORTS"
  if [ -z "${DONE_LOCK_DIR:-}" ] || [ -z "${DONE_LOCK_TOKEN:-}" ]; then
    echo "done-lock: acquire succeeded without lock exports" >&2
    exit 1
  fi

  # 3. Runtime-helper drift advisory (echo-and-continue, once per run).
  DEPLOY="$(resolve_helper deploy_runtime_helpers.sh)"
  if [ -n "$DEPLOY" ]; then
    DRIFT_OUT="$(bash "$DEPLOY" --check 2>&1 || true)"
    if [ -n "$DRIFT_OUT" ]; then
      printf 'done_run setup: runtime-helper drift advisory (echo-and-continue):\n%s\n' "$DRIFT_OUT"
    else
      echo "done_run setup: runtime-helper drift advisory: no drift"
    fi
  fi

  # 4. Worktree residue sweep (fail-open, report-and-continue). The sweep
  #    removes stale registrations only; on-disk worktrees, their artifacts,
  #    and every branch ref stay operator-controlled, so the setup report
  #    carries every retained branch name, its disposition, the proven OID,
  #    and the retention reasons through the final closeout (plan
  #    2026-10-19-gate-removal-closeout-accounting Task 2).
  SWEEP="$(resolve_helper worktree_closeout_migrate.py)"
  if [ -n "$SWEEP" ]; then
    PRIMARY="$(git worktree list --porcelain | sed -n 's/^worktree //p' | head -1)"
    SWEEP_OUT="$(python3 "$SWEEP" sweep --target "$PRIMARY" --apply 2>&1 || true)"
    printf 'done_run setup: residue sweep (fail-open): %s\n' "$(printf '%s' "$SWEEP_OUT" | grep -E '^(OUTCOME|remove|registration|branch-report):')"
  fi

  # 5. Partial-setup classification (read-only unless --from-manifest; an
  #    explicit --adopt of the classified orphan also continues from here).
  classify_partial "$from_manifest" "$adopt_target" && return 0

  # 6. Run-start marker (content-bearing recipe, moved verbatim).
  session="$(session_dir)" || { echo "done-run: cannot resolve the repo root" >&2; setup_die 3; }
  mkdir -p "$session"
  REPO_TOP="$(git rev-parse --show-toplevel)"
  MARKER="$session/run-start-$(date -u +%Y%m%dT%H%M%SZ)"
  REPO_HASH="$(printf '%s' "${REPO_TOP%/}" | (shasum -a 256 2>/dev/null || sha256sum) | awk '{print $1}')"
  printf '%s' "$REPO_HASH" | grep -qE '^[0-9a-f]{64}$' || \
    fail_partial "run-start marker" "sha256 tool missing or malformed digest"
  printf '%s\n' "$(date -u +%s) $REPO_HASH $$" > "$MARKER" || \
    fail_partial "run-start marker" "marker write failed"
  # Post-write location self-check (independent fresh parse).
  session_fresh="$(session_dir)" || session_fresh=""
  if [ "$session_fresh" != "$session" ]; then
    rm -f "$MARKER"
    fail_partial "run-start marker" "resolved path is not the expected done-session root; stray marker removed"
  fi

  # 7. Run manifest write bound to the marker (fail-atomic block). An
  #    explicit --adopt rides the writer's existing adoption path: the writer
  #    keeps its own validations (root identity, completion state,
  #    start-commit resolvability) and a refused write rolls the fresh
  #    marker back below.
  LIB="$(resolve_helper done_sweep_gates_lib.py)"
  if [ -z "$LIB" ]; then
    rm -f "$MARKER"
    fail_partial "run manifest" "no sweep-gates lib resolved (repo-local scripts/ or deployed home)"
  fi
  [ -n "$adopt_target" ] && ADOPT_ARGS+=(--adopt "$adopt_target")
  WM_OUT="$(python3 "$LIB" write-manifest --run-marker "$MARKER" ${WM_ARGS+"${WM_ARGS[@]}"} ${ADOPT_ARGS+"${ADOPT_ARGS[@]}"} 2>&1)" || {
    rm -f "$MARKER"
    fail_partial "run manifest" "the writer refused: $(printf '%s' "$WM_OUT" | tail -n 3)"
  }
  printf '%s\n' "$WM_OUT"
  MANIFEST="$(printf '%s\n' "$WM_OUT" | sed -n 's/^manifest: //p')"
  RUN_ID="$(printf '%s\n' "$WM_OUT" | sed -n 's/^run_id: //p')"
  if [ -z "$MANIFEST" ] || [ -z "$RUN_ID" ]; then
    rm -f "$MARKER"
    fail_partial "run manifest" "writer left no manifest/run_id echo to capture"
  fi

  # 8. The zero/multi-plan migration skip record (the producer duty): a
  #    manifest whose owned_plan_paths count is not exactly one gets its
  #    run-ID-keyed skip record written at this setup's own session
  #    resolution - the same directory the commit leg reads - so the
  #    commit stage's zero/multi-plan closeout never dead-ends at its
  #    refusal with no producer. A single-plan run writes nothing; its
  #    baseline route needs no skip evidence.
  write_zero_multi_plan_skip_record "$session" "$MANIFEST" || {
    echo "done_run setup: the zero/multi-plan migration skip record write failed: $session/worktree-migrate-baseline-$RUN_ID-skip.json; re-enter with --from-manifest $RUN_ID to complete the duty" >&2
    setup_die 1
  }

  echo "done_run setup: ok run_id=$RUN_ID"
  echo "export DONE_LOCK_DIR=$(printf '%q' "$DONE_LOCK_DIR")"
  echo "export DONE_LOCK_TOKEN=$(printf '%q' "$DONE_LOCK_TOKEN")"
  echo "export DONE_RUN_MARKER=$(printf '%q' "$MARKER")"
  echo "export DONE_RUN_MANIFEST=$(printf '%q' "$MANIFEST")"
  echo "export DONE_RUN_ID=$RUN_ID"
}

# --- commit subcommand ------------------------------------------------------

trace_stage() { # name: one `stage <name>` line when DONE_RUN_TRACE_FILE is set
  if [ -n "${DONE_RUN_TRACE_FILE:-}" ]; then
    printf 'stage %s\n' "$1" >> "$DONE_RUN_TRACE_FILE"
  fi
  return 0
}

commit_die() { # rc message...: fail loud with the named evidence
  local rc="$1"
  shift
  echo "done_run commit: $*" >&2
  exit "$rc"
}

# --- primary rolling-log transaction ----------------------------------------
# The two rolling prompt logs and the pair-selected mode's state. The pair
# (--expected-ref canonicalized to a full symbolic ref, --expected-oid) is
# selected by the caller under the primary done lock and rechecked by the
# runner before staging and through captured_tree_landing; plan
# docs/history/plans/2026-10-25-primary-log-branch-drift-at-commit.md
# (Task 1).
PLAN_PROMPTS_REL="docs/history/backlog/PLAN-PROMPTS.md"
EXEC_PROMPTS_REL="docs/history/backlog/EXEC-PROMPTS.md"

arm_rolling_log_cleanup() { # arm the one cleanup owner before staging begins
  ROLLING_CLEANUP_ARMED=1
  trap rolling_log_cleanup EXIT
}

disarm_rolling_log_cleanup() { # kill the owner; the captured ref has advanced
  ROLLING_CLEANUP_ARMED=0
  trap - EXIT
}

# The one cleanup owner for every refusal before the captured-ref
# compare-and-swap succeeds: unstage only this writer's declared owned log
# deltas, verify that delta is empty again, and leave every unrelated staged
# and worktree byte unchanged. An unverifiable cleanup reports blocked
# recovery; the two-path pre-stage guard then refuses the next primary log
# writer until the residue is resolved. The trap preserves the refusal's
# original exit status.
rolling_log_cleanup() {
  trap - EXIT
  ROLLING_CLEANUP_ARMED=0
  local path owned_delta
  for path in ${DECLARED+"${DECLARED[@]}"}; do
    git reset -q -- "$path" 2>/dev/null || true
  done
  owned_delta="$(git diff --cached --name-only HEAD -- \
    ${DECLARED+"${DECLARED[@]}"} 2>/dev/null || true)"
  if [ -n "$owned_delta" ]; then
    echo "done_run commit: rolling-log cleanup: BLOCKED RECOVERY: the owned log delta could not be unstaged cleanly: $(printf '%s' "$owned_delta" | tr '\n' ' '); resolve the residue before the next primary log write (the two-path pre-stage guard refuses either rolling log while it stands)" >&2
  else
    echo "done_run commit: rolling-log cleanup: owned log delta unstaged and verified empty; unrelated staged and worktree bytes unchanged" >&2
  fi
}

facts_toml_value() { # key -> value from the repo facts TOML block
  local repo_top key="$1"
  repo_top="$(git rev-parse --show-toplevel 2>/dev/null)" || return 1
  sed -En "/^${key} = [\"']/{s/^${key} = [\"'](.*)[\"']$/\\1/p;}" \
    "$repo_top/.ai-playbook/facts.md" 2>/dev/null | head -n 1
}

plan_session_slug() { # repo-relative plan path -> the canonical <PLAN_SLUG>
  # The execute-plan canonical session-slug rule (Step 0.4): a dated plan
  # file contributes the filename after removing the leading date and the
  # .md extension; the PLAN.md charter of a dated plan directory contributes
  # the directory name after removing the leading date.
  local base name
  base="${1##*/}"
  if [ "$base" = "PLAN.md" ]; then
    name="${1%/*}"
    name="${name##*/}"
  else
    name="${base%.md}"
  fi
  printf '%s\n' "$name" | sed -E 's/^[0-9]{4}-[0-9]{2}-[0-9]{2}-//'
}

valid_skip_record() { # path -> rc 0 when the file is a valid skip record
  # A skip record is valid when it parses as a JSON object carrying
  # "skip": true (the shape the execute-plan Phase 0 failure arm writes and
  # the run-ID-keyed sibling mirrors); anything else is no skip evidence.
  [ -n "$1" ] && [ -f "$1" ] || return 1
  python3 -c 'import json, sys
try:
    payload = json.load(open(sys.argv[1], encoding="utf-8"))
except (OSError, ValueError):
    raise SystemExit(1)
raise SystemExit(0 if isinstance(payload, dict) and payload.get("skip") is True else 1)' "$1"
}

manifest_field() { # manifest field -> one value per line (list field)
  python3 -c 'import json,sys
values = json.load(open(sys.argv[1])).get(sys.argv[2]) or []
for value in values:
    print(value)' "$1" "$2" 2>/dev/null
}

manifest_scalar() { # manifest field -> the scalar value or empty
  python3 -c 'import json,sys
print(json.load(open(sys.argv[1])).get(sys.argv[2]) or "")' "$1" "$2" 2>/dev/null
}

resolve_manifest_path() { # explicit arg, then the setup export, then newest
  if [ -n "${COMMIT_MANIFEST:-}" ] && [ -f "$COMMIT_MANIFEST" ]; then
    printf '%s\n' "$COMMIT_MANIFEST"
    return 0
  fi
  if [ -n "${DONE_RUN_MANIFEST:-}" ] && [ -f "$DONE_RUN_MANIFEST" ]; then
    printf '%s\n' "$DONE_RUN_MANIFEST"
    return 0
  fi
  local session newest=""
  session="$(session_dir)" || return 1
  for f in "$session"/run-manifest-*.json; do
    [ -f "$f" ] || continue
    if [ -z "$newest" ] || [ "$f" \> "$newest" ]; then newest="$f"; fi
  done
  [ -n "$newest" ] && printf '%s\n' "$newest"
  return 0
}

resolve_run_id() { # --run-id arg, then the manifest, then the setup export
  local manifest
  if [ -n "${RUN_ID_ARG:-}" ]; then printf '%s\n' "$RUN_ID_ARG"; return 0; fi
  manifest="$(resolve_manifest_path)" || return 1
  if [ -n "$manifest" ] && [ -f "$manifest" ]; then
    manifest_scalar "$manifest" run_id
    return 0
  fi
  printf '%s\n' "${DONE_RUN_ID:-}"
}

repo_root_digest() { # -> the 64-hex identity digest of the CWD repo root
  local repo_top
  repo_top="$(git rev-parse --show-toplevel 2>/dev/null)" || return 1
  printf '%s' "${repo_top%/}" | (shasum -a 256 2>/dev/null || sha256sum) | awk '{print $1}'
}

newest_confirmed_marker() { # -> path of the newest root-confirmed marker
  local session f newest=""
  session="$(session_dir)" || return 1
  for f in "$session"/run-start-*; do
    [ -f "$f" ] || continue
    if marker_confirms "$f"; then
      if [ -z "$newest" ] || [ "$f" \> "$newest" ]; then newest="$f"; fi
    fi
  done
  [ -n "$newest" ] && printf '%s\n' "$newest"
  return 0
}

lock_owned_by_this_run() { # rc: live env-token done-lock ownership of this repo
  local meta lock_token lock_root
  [ -n "${DONE_LOCK_DIR:-}" ] && [ -n "${DONE_LOCK_TOKEN:-}" ] || return 1
  [ -d "$DONE_LOCK_DIR" ] || return 1
  meta="$DONE_LOCK_DIR/meta.env"
  [ -f "$meta" ] || return 1
  lock_token="$(sed -n 's/^lock_token=//p' "$meta" | head -n 1)"
  lock_root="$(sed -n 's/^repo_root=//p' "$meta" | head -n 1)"
  [ -n "$lock_token" ] && [ "$lock_token" = "$DONE_LOCK_TOKEN" ] || return 1
  [ "$lock_root" = "$(git rev-parse --show-toplevel 2>/dev/null)" ] || return 1
  return 0
}

# Resolve and validate the current-run tuple an authorized restoration binds
# to, through the existing loader/classifier: the newest root-confirmed
# marker, the manifest bound to it, the matching selected exports, the
# canonical nonterminal verdict, the manifest's repo root, and the live
# env-token done lock. Refuses (exit) on any stale/terminal/mismatched
# member; on success stashes the tuple for the pre-transaction revalidation.
resolve_authorized_run_tuple() {
  local newest_marker manifest marker_field lib verdict_out verdict tuple_run_id \
    manifest_root root_digest
  newest_marker="$(newest_confirmed_marker)" || \
    landing_die 3 "authorized restoration: cannot resolve the repo root"
  [ -n "$newest_marker" ] || \
    landing_die 1 "authorized restoration: no root-confirmed run-start marker for the current run; nothing committed"
  if [ -n "${DONE_RUN_MARKER:-}" ] && [ "$DONE_RUN_MARKER" != "$newest_marker" ]; then
    landing_die 1 "authorized restoration: the selected DONE_RUN_MARKER export is not the newest root-confirmed marker; nothing committed"
  fi
  manifest="$(resolve_manifest_path)" || \
    landing_die 3 "authorized restoration: cannot resolve the repo root"
  if [ -z "$manifest" ] || [ ! -f "$manifest" ]; then
    landing_die 1 "authorized restoration: no run manifest resolved for the current run; nothing committed"
  fi
  marker_field="$(manifest_scalar "$manifest" marker)"
  [ "$marker_field" = "$(basename "$newest_marker")" ] || \
    landing_die 1 "authorized restoration: the selected run manifest is not bound to the newest root-confirmed marker; nothing committed"
  lib="$(resolve_helper done_sweep_gates_lib.py)"
  [ -n "$lib" ] || \
    landing_die 3 "authorized restoration: no done_sweep_gates_lib.py resolved (repo-local scripts/ or deployed home)"
  verdict_out="$(python3 "$lib" classify-run-boundary --session-dir "$(session_dir)" --manifest "$manifest" 2>&1)" || \
    { printf '%s\n' "$verdict_out" >&2; landing_die 2 "authorized restoration: the run-manifest classifier failed; nothing committed"; }
  verdict="$(printf '%s\n' "$verdict_out" | sed -n 's/^verdict: //p')"
  tuple_run_id="$(printf '%s\n' "$verdict_out" | sed -n 's/^run_id: //p')"
  case "$verdict" in
    orphan) ;;  # the live current boundary: unadopted and nonterminal
    unreadable)
      landing_die 2 "authorized restoration: the run manifest record is unreadable (fail-closed); nothing committed";;
    *)
      landing_die 1 "authorized restoration: the run boundary is $verdict (terminal, not the live current run); nothing committed";;
  esac
  if [ -n "${DONE_RUN_ID:-}" ] && [ "$DONE_RUN_ID" != "$tuple_run_id" ]; then
    landing_die 1 "authorized restoration: the selected DONE_RUN_ID export does not match the run manifest run_id=$tuple_run_id; nothing committed"
  fi
  if [ -n "${RUN_ID_ARG:-}" ] && [ "$RUN_ID_ARG" != "$tuple_run_id" ]; then
    landing_die 1 "authorized restoration: --run-id $RUN_ID_ARG does not match the run manifest run_id=$tuple_run_id; nothing committed"
  fi
  manifest_root="$(manifest_scalar "$manifest" repo_root)"
  root_digest="$(repo_root_digest)" || \
    landing_die 3 "authorized restoration: cannot resolve the repo root"
  [ "$manifest_root" = "$root_digest" ] || \
    landing_die 1 "authorized restoration: the run manifest records a different repo root; nothing committed"
  lock_owned_by_this_run || \
    landing_die 1 "authorized restoration: no live done-lock ownership for this run (lock dir, token, or recorded repo root mismatch); nothing committed"
  AUTH_MARKER="$newest_marker"
  AUTH_MANIFEST="$manifest"
  AUTH_RUN_ID="$tuple_run_id"
  AUTH_MANIFEST_DIGEST="$( (shasum -a 256 2>/dev/null || sha256sum) < "$manifest" | awk '{print $1}')"
}

# Run one Git commit hook the way git runs it: hooksPath resolution, cwd at
# the repository root, GIT_DIR exported, the given arguments passed through.
# A missing or non-executable hook is the pass-through skip; the rc is the
# hook's own.
run_commit_hook() { # hook-name [args...] -> rc
  local hook="$1"; shift
  local hook_path
  hook_path="$(git rev-parse --git-path hooks)/$hook"
  [ -x "$hook_path" ] || return 0
  GIT_DIR="${GIT_DIR:-$(git rev-parse --absolute-git-dir)}" "$hook_path" "$@"
}

landing_die() { # rc message...: a captured-tree-landing refusal (cleans the commit scratch first)
  local rc="$1"
  shift
  rm -rf "${tmpd:-}" 2>/dev/null || true
  commit_die "$rc" "$@"
}

# The captured-tree landing shared by every primary-repository commit
# (ordinary and authorized alike): one guarded staged tree, the dirt
# regression gate run exactly once against it, Git-order pre-update commit
# hooks, index-tree and HEAD-identity refusals, and one compare-and-swap
# ref transaction. Caller globals: FULL_SUBJECT, DRIFT_WITNESS, LEDGER_PATH,
# the validated AUTH_* run tuple, the cached-diff authorization (AUTH_PATH
# and AUTH_BLOB), and the dirt correction set (DIRT_CORRECTION_PATHS and
# DIRT_CORRECTION_BLOBS). Every refusal here happens before the ref update
# and before the ledger append.
captured_tree_landing() {
  local tree_accepted head_target="" head_detached=0 head_oid \
    git_dir msg_file tree_after new_oid gpgsign \
    auth_declared_now staged_blob_now declared_path \
    base_ref base_sha dirt_gate correction_path correction_blob \
    tree_blob rpath rpath_ci ci staged_path staged_now \
    rl_ref rl_oid
  local -a sign_args=() dirt_paths=() regressed_paths=()
  # 0. Capture-window fence: re-assert the staged-scope equality
  #    immediately before the tree capture. Anything staged into the index
  #    since the step-6 guard ran (a concurrent-looking extra staged path)
  #    must refuse here, never ride the captured tree. Fail-closed corner:
  #    a rename whose only declared member is its origin refuses too
  #    (declare the destination as well).
  staged_now="$(git diff --cached --name-only HEAD)"
  if [ -n "$staged_now" ]; then
    while IFS= read -r staged_path; do
      [ -n "$staged_path" ] || continue
      auth_declared_now=0
      for declared_path in ${DECLARED+"${DECLARED[@]}"}; do
        [ "$declared_path" = "$staged_path" ] && auth_declared_now=1
      done
      [ "$auth_declared_now" -eq 1 ] || \
        landing_die 1 "captured-tree landing: a foreign path entered the staged index before the tree capture: $staged_path; refusing before the ref update; nothing committed"
    done < <(printf '%s\n' "$staged_now")
  fi
  # 0b. The rolling-log ref precondition (pair-carrying calls only): the
  #     caller-selected symbolic ref and starting OID must still equal
  #     primary HEAD before the tree capture; a mismatch uses the existing
  #     recovery (reselect under the done lock) without a ref update. The
  #     commit then builds from that captured primary HEAD as sole parent
  #     through the existing captured-HEAD compare-and-swap below, whose
  #     post-hook and pre-transaction HEAD-identity checks carry the same
  #     captured pair forward.
  if [ "$ROLLING_LOG" -eq 1 ]; then
    trace_stage rolling-log-ref-precondition
    rl_ref="$(git symbolic-ref -q HEAD 2>/dev/null || true)"
    [ "$rl_ref" = "$EXPECTED_REF" ] || \
      landing_die 1 "rolling-log ref precondition: HEAD's symbolic target (${rl_ref:-detached}) does not match the expected ref ($EXPECTED_REF) before the tree capture; recover and reselect under the done lock, then retry; refusing without a ref update; nothing committed"
    rl_oid="$(git rev-parse --verify HEAD 2>/dev/null || true)"
    [ "$rl_oid" = "$EXPECTED_OID" ] || \
      landing_die 1 "rolling-log ref precondition: HEAD's OID (${rl_oid:-unresolved}) does not match the expected starting OID ($EXPECTED_OID) before the tree capture; recover and reselect under the done lock, then retry; refusing without a ref update; nothing committed"
  fi
  # 1. Record the accepted staged tree (the guards' declared-set tree).
  tree_accepted="$(git write-tree)" || \
    landing_die 2 "captured-tree landing: cannot record the accepted staged tree (write-tree failed)"
  # 1b. The rolling-log pair must still hold immediately after the tree
  #     capture: a ref move inside the capture window refuses here without
  #     a ref update, the cleanup owner unstaging this writer's owned delta.
  if [ "$ROLLING_LOG" -eq 1 ]; then
    rl_ref="$(git symbolic-ref -q HEAD 2>/dev/null || true)"
    rl_oid="$(git rev-parse --verify HEAD 2>/dev/null || true)"
    if [ "$rl_ref" != "$EXPECTED_REF" ] || [ "$rl_oid" != "$EXPECTED_OID" ]; then
      landing_die 1 "rolling-log ref precondition: primary HEAD moved during the tree capture (${rl_ref:-detached} at ${rl_oid:-unresolved}, expected $EXPECTED_REF at $EXPECTED_OID); recover and reselect under the done lock, then retry; refusing without a ref update; nothing committed"
    fi
  fi
  # 2. The dirt regression gate, exactly once, against the captured tree:
  #    done commits classify the immutable tree (--tree mode), never the
  #    mutable worktree, so a worktree-only cleanup after this capture
  #    cannot change the verdict. An authorized dirt correction lifts only
  #    a regressed path it names (with the exact matching blob, checked
  #    below); indeterminate and tool-error outcomes refuse, and so does
  #    every unmatched regression.
  trace_stage dirt-regression-guard
  base_ref="$(facts_toml_value base_branch)"
  if [ -z "$base_ref" ]; then
    base_ref="$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || true)"
  fi
  for declared_path in ${DECLARED+"${DECLARED[@]}"}; do
    git cat-file -e "$tree_accepted:$declared_path" 2>/dev/null && \
      git cat-file -e "HEAD:$declared_path" 2>/dev/null && \
      dirt_paths+=("$declared_path")
  done
  if [ "${#dirt_paths[@]}" -gt 0 ]; then
    if [ -z "$base_ref" ]; then
      echo "done_run commit: dirt regression gate: no default branch resolved; skipped"
    else
      dirt_gate="$(resolve_helper dirt_regression_gate.py)"
      if [ -z "$dirt_gate" ]; then
        echo "done_run commit: dirt regression gate: no dirt_regression_gate.py resolved; skipped" >&2
      else
        base_sha="$(git merge-base HEAD "$base_ref" 2>/dev/null || true)"
        if [ -z "$base_sha" ]; then
          echo "done_run commit: dirt regression gate: base $base_ref does not merge-base against HEAD; skipped" >&2
        else
          DG_RC=0
          DG_OUT="$(python3 "$dirt_gate" --base "$base_sha" --tree "$tree_accepted" -- ${dirt_paths+"${dirt_paths[@]}"} 2>&1)" || DG_RC=$?
          printf '%s\n' "$DG_OUT"
          if [ "$DG_RC" -ne 0 ] && [ "$DG_RC" -ne 1 ]; then
            # Indeterminate and tool-error classifier outcomes refuse with
            # or without an authorization: no authorization suppresses a
            # non-regression classifier result.
            landing_die "$DG_RC" "dirt regression guard refused the captured tree (rc=$DG_RC); nothing committed"
          fi
          if [ "$DG_RC" -eq 1 ]; then
            # Fail-closed handoff: rc=1 must carry the gate's contractual
            # verdict line and at least one machine-readable regression
            # path. A drifted helper (a python traceback exit, a rewritten
            # output format) is a refusal, never a fail-open landing.
            printf '%s\n' "$DG_OUT" | grep -q '^OUTCOME: fail$' || \
              landing_die 2 "captured-tree dirt guard: rc=1 carried no contractual 'OUTCOME: fail' line (helper drift); refusing before the ref update; nothing committed"
            regressed_paths=()
            while IFS= read -r rpath; do
              [ -n "$rpath" ] && regressed_paths+=("$rpath")
            done < <(printf '%s\n' "$DG_OUT" | sed -n 's/^dirt REGRESSION PATH: //p')
            if [ "${#regressed_paths[@]}" -eq 0 ]; then
              landing_die 1 "captured-tree dirt guard: rc=1 named no parsable regression path (helper drift); refusing before the ref update; nothing committed"
            fi
            for rpath in ${regressed_paths+"${regressed_paths[@]}"}; do
              rpath_ci=""
              ci=0
              for correction_path in ${DIRT_CORRECTION_PATHS+"${DIRT_CORRECTION_PATHS[@]}"}; do
                [ "$correction_path" = "$rpath" ] && rpath_ci="$ci"
                ci=$((ci+1))
              done
              if [ -z "$rpath_ci" ]; then
                landing_die 1 "dirt regression guard: unmatched regression in the captured tree: $rpath; an authorized dirt correction covers only its exact path and staged blob; refusing before the ref update; nothing committed"
              fi
              echo "done_run commit: dirt regression guard: authorized dirt correction accepted for this invocation: $rpath"
            done
          fi
        fi
      fi
    fi
  fi
  # 3. Each authorized dirt correction's blob must still equal the path's
  #    blob in the captured tree: a mutation between the staging binding
  #    and this capture refuses here, whether or not the gate flagged the
  #    path.
  ci=0
  for correction_path in ${DIRT_CORRECTION_PATHS+"${DIRT_CORRECTION_PATHS[@]}"}; do
    correction_blob="${DIRT_CORRECTION_BLOBS[$ci]}"
    tree_blob="$(git rev-parse --verify --quiet "$tree_accepted:$correction_path" 2>/dev/null || true)"
    [ "$tree_blob" = "$correction_blob" ] || \
      landing_die 1 "authorized dirt correction: the captured tree's blob for $correction_path (${tree_blob:-absent}) does not equal the expected blob ($correction_blob); refusing before the ref update; nothing committed"
    ci=$((ci+1))
  done
  # 4. The cached-diff authorization binding must still hold at the
  #    tree-capture moment: the path is still in the declared set and its
  #    staged blob still equals the expected blob. A mutation between the
  #    guard lift and this landing (the --revert-formatting arm among
  #    them) refuses here instead of landing a blob different from the
  #    authorized one.
  if [ -n "$AUTH_PATH" ]; then
    auth_declared_now=0
    for declared_path in ${DECLARED+"${DECLARED[@]}"}; do
      [ "$declared_path" = "$AUTH_PATH" ] && auth_declared_now=1
    done
    [ "$auth_declared_now" -eq 1 ] || \
      landing_die 1 "authorized landing: the authorized path left the declared set before the tree capture: $AUTH_PATH; refusing before the ref update; nothing committed"
    staged_blob_now="$(git ls-files -s -- "$AUTH_PATH" | awk '{print $2}')"
    [ "$staged_blob_now" = "$AUTH_BLOB" ] || \
      landing_die 1 "authorized landing: the authorized path's staged blob changed before the tree capture ($staged_blob_now, expected $AUTH_BLOB for $AUTH_PATH); refusing before the ref update; nothing committed"
  fi
  # 5. Capture HEAD identity before the hooks run.
  if head_target="$(git symbolic-ref -q HEAD)"; then
    head_detached=0
  else
    head_detached=1
  fi
  head_oid="$(git rev-parse --verify HEAD)" || \
    landing_die 3 "captured-tree landing: cannot resolve HEAD"
  # 6. The message file, composed the way git commit -m <s> -m <w> renders it.
  git_dir="$(git rev-parse --git-dir)"
  msg_file="$git_dir/COMMIT_EDITMSG"
  { printf '%s\n' "$FULL_SUBJECT"
    if [ -n "$DRIFT_WITNESS" ]; then printf '\n%s\n' "$DRIFT_WITNESS"; fi
  } > "$msg_file" || landing_die 3 "captured-tree landing: cannot write the commit message file"
  # 7. The pre-update commit hooks in Git order, normal args/env/message
  #    handling; a hook failure refuses before any ref or ledger update.
  run_commit_hook pre-commit || \
    landing_die 1 "captured-tree landing: pre-commit hook refused; nothing committed"
  run_commit_hook prepare-commit-msg "$msg_file" message || \
    landing_die 1 "captured-tree landing: prepare-commit-msg hook refused; nothing committed"
  run_commit_hook commit-msg "$msg_file" || \
    landing_die 1 "captured-tree landing: commit-msg hook refused; nothing committed"
  # 8. Any staged-index tree change during the hooks refuses before the ref
  #    update; mutations staged after this final check stay excluded from
  #    the landed commit.
  tree_after="$(git write-tree)" || \
    landing_die 2 "captured-tree landing: cannot re-read the staged tree after the pre-update commit hooks"
  [ "$tree_after" = "$tree_accepted" ] || \
    landing_die 1 "captured-tree landing: a pre-update commit hook changed the staged index tree ($tree_accepted -> $tree_after); refusing before the ref update; nothing committed"
  # 9. The captured HEAD identity must still hold.
  if [ "$head_detached" -eq 0 ]; then
    [ "$(git symbolic-ref -q HEAD)" = "$head_target" ] || \
      landing_die 1 "captured-tree landing: HEAD's symbolic target changed during the pre-update commit hooks; refusing before the ref update; nothing committed"
  else
    git symbolic-ref -q HEAD >/dev/null 2>&1 && \
      landing_die 1 "captured-tree landing: HEAD left detached during the pre-update commit hooks; refusing before the ref update; nothing committed"
  fi
  [ "$(git rev-parse --verify HEAD)" = "$head_oid" ] || \
    landing_die 1 "captured-tree landing: HEAD's OID moved during the pre-update commit hooks; refusing before the ref update; nothing committed"
  # 10. One commit from the unchanged tree, sole parent at captured HEAD,
  #     message exactly the post-commit-msg file bytes; the worktree is never
  #     reread. The configured signing is preserved through commit-tree -S.
  gpgsign="$(git config --bool --get commit.gpgsign 2>/dev/null || true)"
  [ "$gpgsign" = "true" ] && sign_args=(-S)
  new_oid="$(git commit-tree "$tree_accepted" -p "$head_oid" -F "$msg_file" ${sign_args+"${sign_args[@]}"})" || \
    landing_die 2 "captured-tree landing: git commit-tree refused; nothing committed"
  # 11. An authorized invocation revalidates the exact current-run tuple
  #     and the same live token-owned lock directory/token, immediately
  #     before the ref transaction.
  if [ -n "$AUTH_RUN_ID" ]; then
    local r_marker="$AUTH_MARKER" r_manifest="$AUTH_MANIFEST" \
      r_run_id="$AUTH_RUN_ID" r_digest="$AUTH_MANIFEST_DIGEST"
    resolve_authorized_run_tuple
    if [ "$AUTH_MARKER" != "$r_marker" ] || [ "$AUTH_MANIFEST" != "$r_manifest" ] || \
       [ "$AUTH_RUN_ID" != "$r_run_id" ] || [ "$AUTH_MANIFEST_DIGEST" != "$r_digest" ]; then
      landing_die 1 "captured-tree landing: the current-run tuple changed during the pre-update commit hooks; refusing before the ref update; nothing committed"
    fi
  fi
  # 11b. Last-instant HEAD identity re-check, immediately before the ref
  #      transaction: the tuple revalidation subprocesses above sit in the
  #      window the pre-hook check (step 9) cannot cover.
  if [ "$head_detached" -eq 0 ]; then
    [ "$(git symbolic-ref -q HEAD)" = "$head_target" ] || \
      landing_die 1 "captured-tree landing: HEAD's symbolic target changed before the ref transaction; refusing; nothing committed"
  else
    git symbolic-ref -q HEAD >/dev/null 2>&1 && \
      landing_die 1 "captured-tree landing: HEAD left detached before the ref transaction; refusing; nothing committed"
  fi
  [ "$(git rev-parse --verify HEAD)" = "$head_oid" ] || \
    landing_die 1 "captured-tree landing: HEAD's OID moved before the ref transaction; refusing; nothing committed"
  # 12. One ref transaction: atomically verify the captured identity and
  #     compare-and-swap the captured branch ref (or direct HEAD when
  #     detached; no branch is created). Reference-transaction hooks keep
  #     their standard phases and veto power; only the captured branch
  #     advances, and a checkout raced into the transaction cannot
  #     retarget the commit.
  if [ "$head_detached" -eq 0 ]; then
    printf 'start\nupdate %s %s %s\nprepare\ncommit\n' \
      "$head_target" "$new_oid" "$head_oid" \
      | git update-ref --stdin || \
      landing_die 1 "captured-tree landing: the ref transaction refused the captured branch ref compare-and-swap (a reference-transaction hook may have vetoed, or the ref moved); nothing committed"
    echo "done_run commit: captured-tree landing: landed $new_oid on captured branch $head_target (captured at $head_oid)"
  else
    printf 'start\noption no-deref\nupdate HEAD %s %s\nprepare\ncommit\n' \
      "$new_oid" "$head_oid" \
      | git update-ref --stdin || \
      landing_die 1 "captured-tree landing: the ref transaction refused the detached HEAD compare-and-swap (a reference-transaction hook may have vetoed, or HEAD moved); nothing committed"
    echo "done_run commit: captured-tree landing: landed $new_oid on detached HEAD (captured at $head_oid)"
  fi
  # 12b. The rolling-log cleanup owner disarms immediately after the
  #      captured-ref swap: a later ledger-append or post-commit-hook
  #      failure reports that the landed commit stands and never rolls it
  #      back.
  disarm_rolling_log_cleanup
  # 13. The owned-commits ledger append fused after the swap; recorded once.
  #     A failed append refuses loudly naming the landed commit that stands.
  AUTH_LANDED_OID="$new_oid"
  if [ -n "$LEDGER_PATH" ]; then
    printf '%s\n' "$new_oid" >> "$LEDGER_PATH" || \
      landing_die 1 "captured-tree landing: the owned-commits ledger append failed; the landed commit stands ($new_oid)"
  fi
  # 14. post-commit after success on the actual HEAD; its failure cannot
  #     undo the commit.
  run_commit_hook post-commit || \
    echo "done_run commit: captured-tree landing: post-commit hook failed; the landed commit stands" >&2
}

remove_from_declared() { # path: drop one reverted path from DECLARED
  local path="$1" kept=()
  for p in ${DECLARED+"${DECLARED[@]}"}; do
    [ "$p" = "$path" ] || kept+=("$p")
  done
  DECLARED=()
  for p in ${kept+"${kept[@]}"}; do DECLARED+=("$p"); done
}

# Compose the declared-stage channel bytes from the current DECLARED set:
# one path per line, newline-terminated, on stdout. A DECLARED path
# containing a newline is excluded from the channel with the one warning
# line here (the sweep gate keeps its strict behavior for it); any non-zero
# exit is the caller's composition-failure arm (one warning line, then
# continue with the channel unset). Bookkeeping only: this never gates and
# never refuses.
compose_declared_channel() {
  local row
  for row in ${DECLARED+"${DECLARED[@]}"}; do
    case "$row" in
      *$'\n'*)
        echo "done_run commit: declared-stage channel: declared path containing a newline excluded (the sweep gate keeps its strict behavior for it): $row" >&2
        ;;
      *)
        printf '%s\n' "$row"
        ;;
    esac
  done
}

side_facts_value() { # key -> value from the user facts markdown table
  local user_facts="${DONE_SWEEP_USER_FACTS:-${HOME}/.ai-playbook/facts.md}"
  [ -f "$user_facts" ] || return 0
  awk -v key="$1" '
    $0 ~ ("^[|][ \t]*`" key "`[ \t]*[|]") {
      line = $0
      sub(/^[^|]*[|][^|]*[|]/, "", line)
      gsub(/`/, "", line)
      sub(/[|].*$/, "", line)
      gsub(/^[ \t]+|[ \t]+$/, "", line)
      print line
      exit
    }' "$user_facts"
}

cmd_commit() {
  local subject="" receipts_file="" path row
  STAGE_ARGS=(); REVERT_FMT_ARGS=(); SIDE_COMMIT_ARGS=(); GUARD_FIRINGS=()
  DECLARED=()
  COMMIT_MANIFEST=""; RUN_ID_ARG=""; BOUNDARY_CLASS="final-closeout"
  AUTH_PATH=""; AUTH_BLOB=""
  AUTH_MARKER=""; AUTH_MANIFEST=""; AUTH_RUN_ID=""; AUTH_MANIFEST_DIGEST=""
  AUTH_LANDED_OID=""
  DIRT_CORRECTION_PATHS=(); DIRT_CORRECTION_BLOBS=()
  ROLLING_LOG=0; EXPECTED_REF=""; EXPECTED_OID=""; ROLLING_CLEANUP_ARMED=0
  shift # subcommand
  while [ $# -gt 0 ]; do
    case "$1" in
      --boundary-class) BOUNDARY_CLASS="$2"; shift 2;;
      --stage) STAGE_ARGS+=("$2"); shift 2;;
      --guard-firing) GUARD_FIRINGS+=("$2"); shift 2;;
      --revert-formatting) REVERT_FMT_ARGS+=("$2"); shift 2;;
      --side-commit) SIDE_COMMIT_ARGS+=("$2"); shift 2;;
      --subject) subject="$2"; shift 2;;
      --learn-receipts-from) receipts_file="$2"; shift 2;;
      --manifest) COMMIT_MANIFEST="$2"; shift 2;;
      --run-id) RUN_ID_ARG="$2"; shift 2;;
      --expected-ref)
        case "${2:-}" in ""|--*)
          echo "done_run commit: --expected-ref needs <symbolic-branch-ref>" >&2
          exit 3;;
        esac
        EXPECTED_REF="$2"; shift 2;;
      --expected-oid)
        case "${2:-}" in ""|--*)
          echo "done_run commit: --expected-oid needs <full-hex-starting-oid>" >&2
          exit 3;;
        esac
        printf '%s' "$2" | grep -qE '^[0-9a-f]{40}$|^[0-9a-f]{64}$' || {
          echo "done_run commit: --expected-oid: malformed expected starting OID: $2 (want a full hex object id)" >&2
          exit 3;
        }
        EXPECTED_OID="$2"; shift 2;;
      --authorize-ancestor-restoration)
        if [ -n "$AUTH_PATH" ]; then
          echo "done_run commit: --authorize-ancestor-restoration given more than once; one authorized path per invocation" >&2
          exit 3
        fi
        case "${2:-}" in ""|--*)
          echo "done_run commit: --authorize-ancestor-restoration needs <repo-relative-path> <expected-blob-id>" >&2
          exit 3;;
        esac
        case "${3:-}" in ""|--*)
          echo "done_run commit: --authorize-ancestor-restoration needs <repo-relative-path> <expected-blob-id>" >&2
          exit 3;;
        esac
        AUTH_PATH="$2"; AUTH_BLOB="$3"; shift 3;;
      --authorize-dirt-correction)
        case "${2:-}" in ""|--*)
          echo "done_run commit: --authorize-dirt-correction needs <repo-relative-path> <expected-blob-id>" >&2
          exit 3;;
        esac
        case "${3:-}" in ""|--*)
          echo "done_run commit: --authorize-dirt-correction needs <repo-relative-path> <expected-blob-id>" >&2
          exit 3;;
        esac
        printf '%s' "$3" | grep -qE '^[0-9a-f]{40}$|^[0-9a-f]{64}$' || {
          echo "done_run commit: --authorize-dirt-correction: malformed expected blob id: $3 (want a full hex object id)" >&2
          exit 3;
        }
        for path in ${DIRT_CORRECTION_PATHS+"${DIRT_CORRECTION_PATHS[@]}"}; do
          [ "$path" = "$2" ] && {
            echo "done_run commit: --authorize-dirt-correction given more than once for path: $2; one entry per path" >&2
            exit 3;
          }
        done
        DIRT_CORRECTION_PATHS+=("$2"); DIRT_CORRECTION_BLOBS+=("$3"); shift 3;;
      *) echo "done_run commit: unknown argument: $1" >&2; exit 3;;
    esac
  done
  [ -n "$subject" ] || commit_die 3 "a --subject is required (the why-first landing message)"

  # The expected symbolic-ref and starting-OID pair selects the primary
  # rolling-log transaction. A partial pair is a usage refusal before
  # anything mutates (refs, index, and worktree unchanged); a complete pair
  # canonicalizes to a full symbolic ref and rides unchanged through
  # staging, tree capture, and the captured-HEAD compare-and-swap.
  if [ -n "$EXPECTED_REF" ] || [ -n "$EXPECTED_OID" ]; then
    if [ -z "$EXPECTED_REF" ] || [ -z "$EXPECTED_OID" ]; then
      commit_die 3 "--expected-ref and --expected-oid are one pair; give both or neither (ref='${EXPECTED_REF:-none}', oid='${EXPECTED_OID:-none}')"
    fi
    case "$EXPECTED_REF" in
      refs/*) ;;
      *) EXPECTED_REF="refs/heads/$EXPECTED_REF";;
    esac
    ROLLING_LOG=1
  fi

  local repo_top session plans_dir deliverables
  repo_top="$(git rev-parse --show-toplevel 2>/dev/null)" || \
    commit_die 3 "not inside a git repository"
  cd "$repo_top" || commit_die 3 "cannot enter the repository root"
  session="$(session_dir)" || commit_die 3 "cannot resolve the repo root"

  # 0. An authorized landing (the cached-diff restoration or the dirt
  #    correction set) binds to the current run before anything else
  #    mutates: resolve the run tuple through the existing loader/classifier
  #    and refuse every stale/terminal/mismatched member before any
  #    staging, ref, or ledger update.
  if [ -n "$AUTH_PATH" ] || [ "${#DIRT_CORRECTION_PATHS[@]}" -gt 0 ]; then
    trace_stage authorize-run-tuple
    resolve_authorized_run_tuple
  fi

  # 0a. The primary rolling-log pre-stage guards (pair-carrying calls only;
  #     ordinary calls keep their existing paths). Every refusal here
  #     precedes any staging and any cleanup arming: refs, the index, and
  #     worktree bytes stay unchanged.
  if [ "$ROLLING_LOG" -eq 1 ]; then
    local rl_ref="" rl_oid="" rl_residue="" rl_path="" rl_foreign="" rl_owned=0
    trace_stage rolling-log-pre-stage-guard
    [ "${#STAGE_ARGS[@]}" -gt 0 ] || \
      commit_die 3 "rolling-log mode declares its owned log paths via --stage; none given"
    for path in ${STAGE_ARGS+"${STAGE_ARGS[@]}"}; do
      case "$path" in
        "$PLAN_PROMPTS_REL"|"$EXEC_PROMPTS_REL") ;;
        *) commit_die 3 "rolling-log mode stages only the rolling prompt logs ($PLAN_PROMPTS_REL, $EXEC_PROMPTS_REL): $path";;
      esac
    done
    rl_ref="$(git symbolic-ref -q HEAD 2>/dev/null || true)"
    [ "$rl_ref" = "$EXPECTED_REF" ] || \
      commit_die 1 "rolling-log ref precondition: HEAD's symbolic target (${rl_ref:-detached}) does not match the expected ref ($EXPECTED_REF); recover under the done lock (reselect the intended ref), then retry; nothing staged, no ref update"
    rl_oid="$(git rev-parse --verify HEAD 2>/dev/null || true)"
    [ "$rl_oid" = "$EXPECTED_OID" ] || \
      commit_die 1 "rolling-log ref precondition: HEAD's OID (${rl_oid:-unresolved}) does not match the expected starting OID ($EXPECTED_OID); recover under the done lock (reselect the new tip), then retry; nothing staged, no ref update"
    rl_residue="$(git diff --cached --name-only HEAD -- \
      "$PLAN_PROMPTS_REL" "$EXEC_PROMPTS_REL")"
    [ -z "$rl_residue" ] || \
      commit_die 1 "rolling-log pre-stage guard: a staged delta already exists on a rolling prompt log; resolve it before any primary log write; residue left untouched: $(printf '%s' "$rl_residue" | tr '\n' ' ')"
    while IFS= read -r rl_path; do
      [ -n "$rl_path" ] || continue
      rl_owned=0
      for path in ${STAGE_ARGS+"${STAGE_ARGS[@]}"}; do
        [ "$path" = "$rl_path" ] && rl_owned=1
      done
      [ "$rl_owned" -eq 1 ] || rl_foreign="$rl_foreign $rl_path"
    done < <(git diff --cached --name-only HEAD)
    [ -z "$rl_foreign" ] || \
      commit_die 1 "rolling-log pre-stage guard: a staged path outside the declared owned log set refuses before staging; bytes left untouched:$rl_foreign"
  fi

  # 0b. Guard-firing appends: the advisory rows supplied for this landing are
  #     written BEFORE the declared-path staging and the landing sweep (plan
  #     2026-10-24-done-run-lock-span-and-append-ordering), then the ledger
  #     path is staged into the declared set so the accepted bytes ride the
  #     landing commit exactly once. Echo-and-continue: a malformed firing, a
  #     missing writer, or a failed append is one warning line and the
  #     landing continues; the writer's pre-write public-hygiene screen leaves
  #     the canonical ledger bytes unchanged and skips a flagged row. Guard
  #     rows stay advisory: no step here refuses the landing over them except
  #     an actual staging failure of the ledger path itself.
  if [ "${#GUARD_FIRINGS[@]}" -gt 0 ]; then
    trace_stage guard-firing-appends
    GUARD_LEDGER_REL="scripts/gate_liveness_ledger.json"
    GUARD_LEDGER_STAGED=0
    local gname gkind gevidence gnote firing glf_out
    GLF_LEDGER_SCRIPT="$(resolve_helper gate_liveness_ledger.py)"
    if [ -z "$GLF_LEDGER_SCRIPT" ]; then
      echo "done_run commit: WARNING: no gate_liveness_ledger.py resolved (repo-local scripts/ or deployed home); guard-firing appends skipped (advisory)" >&2
    fi
    for firing in ${GUARD_FIRINGS+"${GUARD_FIRINGS[@]}"}; do
      gname="$(printf '%s' "$firing" | cut -d: -f1)"
      gkind="$(printf '%s' "$firing" | cut -d: -f2)"
      gevidence="$(printf '%s' "$firing" | cut -d: -f3)"
      gnote="$(printf '%s' "$firing" | cut -d: -f4-)"
      if [ -z "$gname" ] || [ -z "$gkind" ] || [ -z "$gevidence" ]; then
        echo "done_run commit: WARNING: malformed --guard-firing (want NAME:KIND:EVIDENCE[:NOTE]): $firing" >&2
        continue
      fi
      if [ -n "$GLF_LEDGER_SCRIPT" ]; then
        GLF_ARGS=(--ledger "$GUARD_LEDGER_REL" record --guard "$gname" --kind "$gkind" \
          --date "$(date -u +%F)" --evidence "$gevidence")
        [ -n "$gnote" ] && GLF_ARGS+=(--note "$gnote")
        glf_out="$(python3 "$GLF_LEDGER_SCRIPT" ${GLF_ARGS+"${GLF_ARGS[@]}"} 2>&1)" \
          || echo "done_run commit: WARNING: guard-firing append failed for $gname (advisory; the landing continues; read the writer's output above)" >&2
        [ -n "$glf_out" ] && printf '%s\n' "$glf_out"
      fi
    done
    if [ -f "$GUARD_LEDGER_REL" ]; then
      if git check-ignore -q "$GUARD_LEDGER_REL"; then
        echo "done_run commit: WARNING: the ledger path is gitignored; the guard-firing bytes cannot ride the commit (advisory)" >&2
      else
        git add -- "$GUARD_LEDGER_REL" || \
          commit_die 3 "guard-firing ledger staging refused for $GUARD_LEDGER_REL; stage it deliberately in a follow-up invocation or fix the staging failure; nothing committed"
        GUARD_LEDGER_STAGED=1
      fi
    fi
    if [ "$GUARD_LEDGER_STAGED" -eq 1 ]; then
      DECLARED+=("$GUARD_LEDGER_REL")
    fi
  fi

  # 1. Stage by explicit pathspec from the run's owned set (the declared
  #    --stage paths). Gitignored paths are reported and never staged.
  #    The declared set partitions into three arms: worktree-existing or
  #    index-tracked paths ride the git add below; an already-staged
  #    deletion (worktree-absent, index-absent, HEAD-tracked) needs no
  #    staging operation; a path tracked nowhere refuses so a typo never
  #    silently vanishes from the declared set.
  trace_stage staging
  STAGE_LIST=()
  for path in ${STAGE_ARGS+"${STAGE_ARGS[@]}"}; do
    if git check-ignore -q "$path"; then
      echo "done_run commit: gitignored path not staged (previously force-tracked; untrack it instead, never commit it here): $path" >&2
    elif [ ! -e "$path" ] && ! git ls-files -- "$path" | grep -qxF -- "$path"; then
      if git cat-file -e "HEAD:$path" 2>/dev/null; then
        echo "done_run commit: already-staged deletion, no staging operation needed: $path" >&2
        DECLARED+=("$path")
      else
        commit_die 3 "declared path is absent and not tracked: $path"
      fi
    else
      DECLARED+=("$path")
      STAGE_LIST+=("$path")
    fi
  done
  # Staging begins here in rolling-log mode: arm the one cleanup owner so
  # every later pre-CAS refusal restores this writer's owned delta.
  if [ "$ROLLING_LOG" -eq 1 ]; then
    arm_rolling_log_cleanup
  fi
  if [ "${#STAGE_LIST[@]}" -gt 0 ]; then
    git add -- ${STAGE_LIST+"${STAGE_LIST[@]}"} || \
      commit_die 3 "git add refused the declared pathspec; stage the surviving paths in their own invocation and re-run"
  fi

  # 1b. Bind each authorization to this invocation's declared set and its
  #     exact staged blob: the cached-diff restoration's path and the dirt
  #     correction set's every path must have been declared via --stage
  #     here, and each staged blob must equal the operator-supplied
  #     expected blob. All refusals happen before any ref or ledger update.
  if [ -n "$AUTH_PATH" ]; then
    AUTH_DECLARED=0
    for path in ${DECLARED+"${DECLARED[@]}"}; do
      [ "$path" = "$AUTH_PATH" ] && AUTH_DECLARED=1
    done
    [ "$AUTH_DECLARED" -eq 1 ] || \
      commit_die 3 "authorized restoration: the authorized path is not in the declared --stage set: $AUTH_PATH"
    AUTH_STAGED_BLOB="$(git ls-files -s -- "$AUTH_PATH" | awk '{print $2}')"
    [ -n "$AUTH_STAGED_BLOB" ] || \
      commit_die 1 "authorized restoration: the authorized path has no staged index entry: $AUTH_PATH; nothing committed"
    [ "$AUTH_STAGED_BLOB" = "$AUTH_BLOB" ] || \
      commit_die 1 "authorized restoration: the staged blob $AUTH_STAGED_BLOB does not equal the expected blob $AUTH_BLOB for $AUTH_PATH; nothing committed"
    echo "done_run commit: authorized restoration: path $AUTH_PATH bound to expected blob $AUTH_BLOB for this invocation"
  fi
  if [ "${#DIRT_CORRECTION_PATHS[@]}" -gt 0 ]; then
    ci=0
    for path in ${DIRT_CORRECTION_PATHS+"${DIRT_CORRECTION_PATHS[@]}"}; do
      correction_blob="${DIRT_CORRECTION_BLOBS[$ci]}"
      AUTH_DECLARED=0
      for declared_path in ${DECLARED+"${DECLARED[@]}"}; do
        [ "$declared_path" = "$path" ] && AUTH_DECLARED=1
      done
      [ "$AUTH_DECLARED" -eq 1 ] || \
        commit_die 3 "authorized dirt correction: the authorized correction path is not in the declared --stage set: $path"
      correction_blob_staged="$(git ls-files -s -- "$path" | awk '{print $2}')"
      [ -n "$correction_blob_staged" ] || \
        commit_die 1 "authorized dirt correction: the authorized correction path has no staged index entry: $path; nothing committed"
      [ "$correction_blob_staged" = "$correction_blob" ] || \
        commit_die 1 "authorized dirt correction: the staged blob $correction_blob_staged does not equal the expected blob $correction_blob for $path; nothing committed"
      echo "done_run commit: authorized dirt correction: path $path bound to expected blob $correction_blob for this invocation"
      ci=$((ci+1))
    done
  fi

  # 2. Append staged plans-root paths to the deliverables file.
  trace_stage deliverables
  plans_dir="$(facts_toml_value plans_dir)"
  plans_dir="${plans_dir:-docs/history/plans/}"
  deliverables="$session/plan-deliverables.txt"
  for path in ${DECLARED+"${DECLARED[@]}"}; do
    # a worktree-absent declared path is a deletion, not a deliverable
    [ -e "$path" ] || continue
    case "$path" in
      "$plans_dir"*)
        case "$path" in
          "$plans_dir"completed/*) continue;;
        esac
        mkdir -p "$session"
        grep -qxF "$path" "$deliverables" 2>/dev/null || \
          printf '%s\n' "$path" >> "$deliverables"
        ;;
    esac
  done

  # 3. Stale-checkout adjudication over the non-declared tracked dirty set:
  #    ancestor-blob debris is restored from HEAD and reported, never staged.
  trace_stage stale-checkout-adjudication
  CLASSIFIER="$(resolve_helper revert_set_classifier.py)"
  [ -n "$CLASSIFIER" ] || commit_die 3 "no revert_set_classifier.py resolved (repo-local scripts/ or deployed home)"
  local tmpd
  tmpd="$(mktemp -d)" || commit_die 3 "no scratch directory available"
  if [ "${#DECLARED[@]}" -gt 0 ]; then
    printf '%s\n' ${DECLARED+"${DECLARED[@]}"} | sort > "$tmpd/declared"
  else
    : > "$tmpd/declared"
  fi
  git diff --name-only HEAD | sort > "$tmpd/dirty"
  comm -13 "$tmpd/declared" "$tmpd/dirty" > "$tmpd/nondecl"
  if [ -s "$tmpd/nondecl" ]; then
    CL_PATHS=()
    while IFS= read -r row; do
      [ -n "$row" ] && CL_PATHS+=(--path "$row")
    done < "$tmpd/nondecl"
    CL_RC=0
    CL_OUT="$(python3 "$CLASSIFIER" classify --repo "$repo_top" ${CL_PATHS+"${CL_PATHS[@]}"} 2>&1)" || CL_RC=$?
    case "$CL_RC" in
      0) ;;
      1)
        printf '%s\n' "$CL_OUT" | while IFS= read -r row; do
          case "$row" in
            "reversal: "*)
              rpath="$(printf '%s' "$row" | awk '{print $2}')"
              if git diff --cached --name-only HEAD | grep -qxF "$rpath"; then
                echo "done_run commit: stale-checkout adjudication: reversal path left (index state differs from HEAD; the staged-scope guard owns it when a declared set is present, and an empty declared set refuses before any landing commit): $rpath" >&2
              elif git checkout -- "$rpath" 2>/dev/null; then
                echo "done_run commit: stale-checkout adjudication: restored from HEAD, never staged: $rpath" >&2
              else
                echo "done_run commit: stale-checkout adjudication: reversal path reported (restore failed): $rpath" >&2
              fi
              ;;
          esac
        done
        ;;
      *)
        printf '%s\n' "$CL_OUT" >&2
        rm -rf "$tmpd"
        commit_die 2 "stale-checkout adjudication could not classify the non-declared dirty set (rc=$CL_RC)"
        ;;
    esac
  fi

  # 4. Cached-diff guard over the declared staged paths: a declared path
  #    whose staged content equals an ancestor vintage is a leaked revert
  #    (the relocated stop). Declared deletions are the set's own removals.
  trace_stage cached-diff-guard
  if [ "${#DECLARED[@]}" -gt 0 ]; then
    CD_PATHS=()
    for path in ${DECLARED+"${DECLARED[@]}"}; do CD_PATHS+=(--path "$path"); done
    CD_RC=0
    CD_OUT="$(python3 "$CLASSIFIER" classify --repo "$repo_top" ${CD_PATHS+"${CD_PATHS[@]}"} 2>&1)" || CD_RC=$?
    case "$CD_RC" in
      0) ;;
      1)
        LEAKED="$(printf '%s\n' "$CD_OUT" | grep '^reversal: ' | grep ' dirty state equals ancestor ' | awk '{print $2}')"
        # The invocation-scoped authorization lifts exactly the authorized
        # path, and only while its staged blob still equals the expected
        # blob bound above; every other ancestor-matching path still refuses.
        if [ -n "$AUTH_PATH" ] && [ -n "$LEAKED" ]; then
          AUTH_GUARD_BLOB="$(git ls-files -s -- "$AUTH_PATH" | awk '{print $2}')"
          if [ "$AUTH_GUARD_BLOB" = "$AUTH_BLOB" ]; then
            LEAKED="$(printf '%s\n' "$LEAKED" | grep -vxF -- "$AUTH_PATH" || true)"
            echo "done_run commit: cached-diff guard: authorized ancestor restoration accepted for this invocation: $AUTH_PATH (expected blob $AUTH_BLOB)"
          fi
        fi
        if [ -n "$LEAKED" ]; then
          echo "done_run commit: cached-diff guard: a leaked revert is staged across: $(printf '%s' "$LEAKED" | tr '\n' ' ')" >&2
          echo "done_run commit: cached-diff guard: reset the leaked paths and restage only the intended edits, then re-run; nothing committed" >&2
          rm -rf "$tmpd"
          exit 1
        fi
        # Deliberate pass-through: a reversal naming a declared path whose
        # index entry is absent is the declared deletion itself, the set's
        # own removal, not a leaked revert; pin the passage so it does not
        # depend on the classifier's message wording.
        for path in ${DECLARED+"${DECLARED[@]}"}; do
          if ! git ls-files -- "$path" | grep -qxF -- "$path" && \
             printf '%s\n' "$CD_OUT" | grep '^reversal: ' | awk '{print $2}' | grep -qxF -- "$path"; then
            echo "done_run commit: cached-diff guard: declared deletion is the set's own removal: $path" >&2
          fi
        done
        ;;
      *)
        printf '%s\n' "$CD_OUT" >&2
        rm -rf "$tmpd"
        commit_die "$CD_RC" "cached-diff guard: the revert-set classifier could not answer (rc=$CD_RC)"
        ;;
    esac
  fi

  # 5. (moved) The dirt regression gate runs exactly once per landing,
  #    against the captured tree, inside captured_tree_landing below: done
  #    commits classify their captured tree, and the shared boundary keeps
  #    one gate invocation per primary-repository commit.

  # 6. Staged-scope guard over the declared set before the commit.
  trace_stage staged-scope-guard
  SCOPE_GUARD="$(resolve_helper staged_scope_guard.py)"
  if [ "${#DECLARED[@]}" -gt 0 ]; then
    if [ -z "$SCOPE_GUARD" ]; then
      rm -rf "$tmpd"
      commit_die 2 "staged-scope guard: no resolvable copy (repo-local scripts/ and the deployed runtime home were both searched); the commit path stops until a resolvable copy exists"
    fi
    SG_ARGS=()
    for path in ${DECLARED+"${DECLARED[@]}"}; do SG_ARGS+=(--include "$path"); done
    SG_RC=0
    SG_OUT="$(python3 "$SCOPE_GUARD" ${SG_ARGS+"${SG_ARGS[@]}"} 2>&1)" || SG_RC=$?
    printf '%s\n' "$SG_OUT"
    if [ "$SG_RC" -ne 0 ]; then
      rm -rf "$tmpd"
      commit_die "$SG_RC" "staged-scope guard refused the declared set (rc=$SG_RC); unstage the named entries or widen the declared set deliberately; nothing committed"
    fi
  fi

  # 7. Foreign-dirt disposition ladder over the remaining dirty paths: a
  #    manifest foreign claim is a live peer's work and aborts the landing;
  #    other unclaimed dirt is reported and left unstaged.
  trace_stage foreign-dirt-ladder
  FOREIGN_CLAIMS="$(mktemp)" || commit_die 3 "no scratch file available"
  RUN_MANIFEST="$(resolve_manifest_path)" || RUN_MANIFEST=""
  if [ -n "$RUN_MANIFEST" ] && [ -f "$RUN_MANIFEST" ]; then
    manifest_field "$RUN_MANIFEST" foreign_review_paths >> "$FOREIGN_CLAIMS"
  fi
  git ls-files --others --exclude-standard | sort > "$tmpd/untracked"
  comm -13 "$tmpd/declared" "$tmpd/untracked" > "$tmpd/untracked-foreign"
  sort -u "$tmpd/nondecl" "$tmpd/untracked-foreign" | comm -13 "$tmpd/declared" - > "$tmpd/remaining"
  PEER_ABORT=""; REPORTED=""
  while IFS= read -r row; do
    [ -n "$row" ] || continue
    if grep -qxF "$row" "$FOREIGN_CLAIMS"; then
      PEER_ABORT="$PEER_ABORT $row"
    else
      REPORTED="$REPORTED $row"
    fi
  done < "$tmpd/remaining"
  rm -f "$FOREIGN_CLAIMS"
  if [ -n "$PEER_ABORT" ]; then
    rm -rf "$tmpd"
    commit_die 1 "foreign-dirt gate: uncommitted work attributable to a live peer session; the landing aborts:$PEER_ABORT (waiting is futile while this run holds the done lock the peer's own landing would need)"
  fi
  if [ -n "$REPORTED" ]; then
    echo "done_run commit: foreign-dirt gate: unclaimed baseline dirt reported and left unstaged:$REPORTED" >&2
  fi

  # 8. Formatting-only diff candidates: listed for one-line confirmation;
  #    no revert without the --revert-formatting flag.
  trace_stage formatting-candidates
  FMT_CANDIDATES=()
  for path in ${DECLARED+"${DECLARED[@]}"}; do
    [ -f "$path" ] || continue
    FULL_DIFF="$(git diff HEAD -- "$path")"
    [ -n "$FULL_DIFF" ] || continue
    CORE_DIFF="$(git diff HEAD --ignore-all-space --ignore-blank-lines -- "$path")"
    if [ -z "$CORE_DIFF" ]; then FMT_CANDIDATES+=("$path"); fi
  done
  if [ "${#FMT_CANDIDATES[@]}" -gt 0 ]; then
    echo "done_run commit: formatting-only diff candidate(s), revert list needs one-line confirmation via --revert-formatting (no revert without it): ${FMT_CANDIDATES[*]}"
  fi
  for path in ${REVERT_FMT_ARGS+"${REVERT_FMT_ARGS[@]}"}; do
    IS_CANDIDATE=""
    for candidate in ${FMT_CANDIDATES+"${FMT_CANDIDATES[@]}"}; do
      [ "$candidate" = "$path" ] && IS_CANDIDATE=1
    done
    if [ -z "$IS_CANDIDATE" ]; then
      rm -rf "$tmpd"
      commit_die 3 "--revert-formatting names a path that is not a formatting-only candidate: $path"
    fi
    git checkout HEAD -- "$path" || { rm -rf "$tmpd"; commit_die 3 "revert failed for $path"; }
    remove_from_declared "$path"
    echo "done_run commit: formatting-only diff reverted after confirmation: $path"
  done

  # 9. Unused-import pass over touched lintable paths (report-only).
  trace_stage unused-import-pass
  LINTER="${DONE_RUN_LINTER:-ruff}"
  if ! command -v "$LINTER" >/dev/null 2>&1; then
    echo "done_run commit: unused-import pass: no linter resolved; skipped"
  else
    LINT_PATHS=()
    for path in ${DECLARED+"${DECLARED[@]}"}; do
      case "$path" in
        *.py) [ -f "$path" ] && LINT_PATHS+=("$path");;
      esac
    done
    if [ "${#LINT_PATHS[@]}" -eq 0 ]; then
      echo "done_run commit: unused-import pass: no lintable touched paths; skipped"
    else
      LINT_OUT="$("$LINTER" check --no-fix --select F401 -- ${LINT_PATHS+"${LINT_PATHS[@]}"} 2>&1 || true)"
      if [ -n "$LINT_OUT" ]; then
        printf 'done_run commit: unused-import pass findings (report-only; fix before staging):\n%s\n' "$LINT_OUT" >&2
      else
        echo "done_run commit: unused-import pass: clean"
      fi
    fi
  fi

  # 10. Lesson-scope audit when the lessons corpus is touched.
  trace_stage lesson-scope-audit
  CORPUS_REL="docs/maintenance/development_lessons.md"
  DRIFT_WITNESS=""
  STAGED_NOW="$(git diff --cached --name-only HEAD)"
  if printf '%s\n' "$STAGED_NOW" | grep -qxF "$CORPUS_REL"; then
    CPR="$(facts_toml_value company_projects_root)"
    CGM="$(facts_toml_value company_guidelines_master)"
    if [ -z "$CPR" ] || [ -z "$CGM" ]; then
      echo "done_run commit: lesson-scope audit: company master out of scope for this repo; duplicate check skipped"
    else
      UNDER_ROOT=""
      case "$repo_top" in
        "$CPR"|"$CPR"/*) UNDER_ROOT=1;;
      esac
      if [ -z "$UNDER_ROOT" ]; then
        echo "done_run commit: lesson-scope audit: company master out of scope for this repo; duplicate check skipped"
      elif [ ! -f "$CGM" ]; then
        echo "done_run commit: lesson-scope audit: WARNING: config drift: company guidelines master not found; company duplicate audit not run" >&2
        DRIFT_WITNESS="lesson-scope-audit: config drift: company guidelines master not found; company duplicate audit not run"
      else
        VALIDATOR="${LESSON_SCOPE_SCRIPT:-$(resolve_helper check_lesson_scope.py)}"
        if [ -z "$VALIDATOR" ] || [ ! -f "$VALIDATOR" ]; then
          echo "done_run commit: lesson-scope audit: lesson scope validator absent; mechanical duplicate check skipped (cold-start)" >&2
        else
          LS_RC=0
          LS_OUT="$(python3 "$VALIDATOR" "$repo_top/$CORPUS_REL" "$CGM" 2>&1)" || LS_RC=$?
          printf '%s\n' "$LS_OUT"
          if [ "$LS_RC" -eq 1 ] && printf '%s' "$LS_OUT" | grep -q '^DUPLICATE:'; then
            rm -rf "$tmpd"
            commit_die 1 "lesson-scope audit: a full rule is duplicated across the project corpus and the company master; stop before commit and ask the user to classify the lesson"
          elif [ "$LS_RC" -ne 0 ]; then
            rm -rf "$tmpd"
            commit_die 2 "lesson-scope audit: validator tool failure (rc=$LS_RC); do not stage the corpus"
          fi
        fi
      fi
    fi
    echo "done_run commit: lesson-scope audit: placement receipts remain the agent confirmation duty (owned by the learn skill placement receipts duty)"
  fi

  # 11. Learn receipts: post-hoc-from-receipt ledger appends, before the
  #     in-script landing re-run, so the sweep's doc-registry gate sees them.
  if [ -n "$receipts_file" ]; then
    trace_stage learn-receipts
    [ -f "$receipts_file" ] || { rm -rf "$tmpd"; commit_die 3 "learn receipts file not readable: $receipts_file"; }
    RUN_ID="$(resolve_run_id)"
    if [ -z "$RUN_ID" ]; then
      echo "done_run commit: learn receipts skipped (no run manifest from Step 0; no ledger path)"
    else
      LEDGER_PATH="$session/owned-commits-$RUN_ID.txt"
      mkdir -p "$session"
      while IFS= read -r row; do
        sha="$(printf '%s' "$row" | grep -oE '[0-9a-fA-F]{40}' | head -n 1)"
        [ -n "$sha" ] || continue
        if git rev-parse -q --verify "$sha^{commit}" >/dev/null 2>&1; then
          printf '%s\n' "$sha" >> "$LEDGER_PATH"
        else
          echo "done_run commit: learn receipt skip (not resolvable in this repository): $sha"
        fi
      done < "$receipts_file"
    fi
  fi

  # 12. The landing sweep over the final staged set: the closeout's one
  #     run. Immediately before the invocation, the declared-stage channel
  #     is composed from the final DECLARED set (the step-8 formatting
  #     revert has resolved it) and rides this one sweep invocation only.
  trace_stage landing-sweep
  SWEEP="$(resolve_helper done_sweep_gates.sh)"
  [ -n "$SWEEP" ] || { rm -rf "$tmpd"; commit_die 3 "no done_sweep_gates.sh resolved (repo-local scripts/ or deployed home)"; }
  # Declared-stage channel composition (bookkeeping in the commit flow,
  # never gates and never refuses): one final DECLARED path per line,
  # newline-terminated, handed to the sweep subprocess below and to nothing
  # else. A declared path containing a newline is excluded from the channel
  # with the composer's one warning line (the gate keeps its strict
  # behavior for it); a composition failure prints the one warning line
  # here and continues with the channel unset.
  SWEEP_CHANNEL="$(compose_declared_channel)" || {
    echo "done_run commit: declared-stage channel composition failed; continuing with the channel unset" >&2
    SWEEP_CHANNEL=""
  }
  SWEEP_RC=0
  if [ -n "$SWEEP_CHANNEL" ]; then
    SWEEP_OUT="$(DONE_SWEEP_DECLARED_STAGE_PATHS="$SWEEP_CHANNEL" bash "$SWEEP" landing --boundary-class "$BOUNDARY_CLASS" 2>&1)" || SWEEP_RC=$?
  else
    # empty declared set: actively unset the variable for the sweep
    # subprocess rather than skipping the assignment, so no ambient export
    # can leak into a channel-free sweep
    SWEEP_OUT="$(env -u DONE_SWEEP_DECLARED_STAGE_PATHS bash "$SWEEP" landing --boundary-class "$BOUNDARY_CLASS" 2>&1)" || SWEEP_RC=$?
  fi
  printf '%s\n' "$SWEEP_OUT"
  if [ "$SWEEP_RC" -ne 0 ]; then
    # Description-length pre-refusal catch record (plan
    # 2026-10-24-description-length-gate-catch-promotion, Task 1): the
    # sweep's structured JSON gate and rc are the complete capture input.
    # gate=description-length with rc=1 is the one measured over-cap class:
    # append its catch row to the repo ledger (run identity in the existing
    # note field; the ledger writer deduplicates it for sequential retries
    # of the same run) while the done lock is still held, then refuse. The
    # refusal names the ledger path as a required declaration for the next
    # successful retry. An append failure refuses naming the unrecorded
    # catch. rc=2 (indeterminate) and rc=3 (tool error, including a missing
    # checker deployment or a checker operational exception) refuse without
    # a catch.
    DESC_CATCH=0
    if printf '%s\n' "$SWEEP_OUT" | python3 -c '
import json, sys
for line in sys.stdin:
    line = line.strip()
    if not line.startswith("{"):
        continue
    try:
        row = json.loads(line)
    except ValueError:
        continue
    if (
        isinstance(row, dict)
        and row.get("gate") == "description-length"
        and row.get("rc") == 1
    ):
        sys.exit(0)
sys.exit(1)
'; then
      DESC_CATCH=1
    fi
    if [ "$DESC_CATCH" -eq 1 ]; then
      trace_stage guard-catch-record
      LEDGER_SCRIPT="$(resolve_helper gate_liveness_ledger.py)"
      CATCH_RUN_ID="$(resolve_run_id)"
      if [ -n "$CATCH_RUN_ID" ]; then
        CATCH_NOTE="run_id=$CATCH_RUN_ID; over-cap folded skill description refused before landing; declare scripts/gate_liveness_ledger.json on the fixing retry so this catch lands with the fix"
      else
        CATCH_NOTE="over-cap folded skill description refused before landing; no run manifest resolved, so this row carries no run-identity token and is never deduplicated"
      fi
      CATCH_OK=1
      if [ -n "$LEDGER_SCRIPT" ]; then
        GL_CATCH_OUT="$(python3 "$LEDGER_SCRIPT" --ledger scripts/gate_liveness_ledger.json record --guard description-length --kind catch --date "$(date -u +%F)" --evidence "landing sweep gate=description-length rc=1 at the done commit boundary" --note "$CATCH_NOTE" 2>&1)" || CATCH_OK=0
        printf '%s\n' "$GL_CATCH_OUT"
      else
        CATCH_OK=0
        echo "done_run commit: no gate_liveness_ledger.py resolved (repo-local scripts/ or deployed home); the catch could not be recorded" >&2
      fi
      rm -rf "$tmpd"
      if [ "$CATCH_OK" -eq 1 ]; then
        commit_die "$SWEEP_RC" "the landing sweep refused the staged set (rc=$SWEEP_RC); nothing committed; the description-length catch was recorded in scripts/gate_liveness_ledger.json (declare that path alongside the fixed description on the next successful retry so the catch lands with the fix); fix the over-cap description(s) and re-run"
      else
        commit_die "$SWEEP_RC" "the landing sweep refused the staged set (rc=$SWEEP_RC); nothing committed; the description-length catch could not be recorded in scripts/gate_liveness_ledger.json (the ledger append failed; read its output above); fix that failure, then fix the over-cap description(s) and re-run"
      fi
    fi
    rm -rf "$tmpd"
    commit_die "$SWEEP_RC" "the landing sweep refused the staged set (rc=$SWEEP_RC); nothing committed"
  fi

  # 13. The docs-branch sync at its today position; the migration precedes it
  #     when this session runs in an ad-hoc worktree. The commit never
  #     captures a baseline (plan
  #     2026-10-18-worktree-closeout-single-start-baseline): exactly one
  #     owned plan reuses that plan's canonical Phase 0 closeout baseline;
  #     zero or multiple owned plans take the run-ID-keyed sibling skip
  #     record whose manual scoped copy and recorded artifact list the
  #     session completed before this commit; neither evidence keeps the
  #     existing refusal. Both mutating runners hold their own
  #     repository-keyed merge lock inside their own process.
  trace_stage docs-sync
  PRIMARY="$(git worktree list --porcelain | sed -n 's/^worktree //p' | head -n 1)"
  if [ -n "$PRIMARY" ] && [ "$repo_top" != "$PRIMARY" ]; then
    MIGRATE="$(resolve_helper worktree_closeout_migrate.py)"
    if [ -n "$MIGRATE" ]; then
      RUN_ID_MIG="$(resolve_run_id)"
      MIG_SKIP_RECORD="$session/worktree-migrate-baseline-${RUN_ID_MIG:-adhoc}-skip.json"
      mkdir -p "$session"
      MG_RC=0
      MG_OUT=""
      MIG_BYPASS=""
      MIG_BYPASS_RECORD=""
      MIG_BASELINE=""
      OWNED_PLAN_LIST="$(manifest_field "${RUN_MANIFEST:-}" owned_plan_paths)"
      OWNED_PLAN_COUNT="$(printf '%s\n' "$OWNED_PLAN_LIST" | grep -c .)"
      if [ "$OWNED_PLAN_COUNT" -eq 1 ]; then
        # Exactly one owned plan: that plan's canonical Phase 0 baseline is
        # the only baseline this run may reuse; a valid plan-session skip
        # sibling (the recorded Phase 0 capture failure) routes to the
        # manual scoped-copy arm instead.
        OWNED_PLAN_PATH="$(printf '%s\n' "$OWNED_PLAN_LIST")"
        PLAN_SLUG="$(plan_session_slug "$OWNED_PLAN_PATH")"
        MIG_TMP_RAW="$(facts_toml_value tmp_dir)"
        MIG_TMP_RAW="${MIG_TMP_RAW:-docs/tmp/}"
        case "$MIG_TMP_RAW" in /*) MIG_TMP_ROOT="$MIG_TMP_RAW";; *) MIG_TMP_ROOT="$repo_top/${MIG_TMP_RAW#/}";; esac
        MIG_BASELINE="${MIG_TMP_ROOT%/}/execute-plan/$PLAN_SLUG/closeout-baseline.json"
        # The one-owned-plan migration manifest lands at the PRIMARY
        # checkout's canonical plan-slug path, so the plans closeout's
        # gate-removal finds the branch record there through its explicit
        # --migration-manifest operand (plan
        # 2026-10-27-plan-authoring-branch-manifest-handoff); the worktree
        # session directory keeps the run-id skip-record form for the
        # degraded arms below.
        case "$MIG_TMP_RAW" in
          /*) MIG_MANIFEST_DEST="${MIG_TMP_RAW%/}/execute-plan/$PLAN_SLUG/closeout-migration.json";;
          *) MIG_MANIFEST_DEST="${PRIMARY%/}/${MIG_TMP_RAW#/}/execute-plan/$PLAN_SLUG/closeout-migration.json";;
        esac
        if [ ! -f "$MIG_BASELINE" ] && valid_skip_record "${MIG_BASELINE%.json}-skip.json"; then
          MIG_BYPASS=1
          MIG_BYPASS_RECORD="${MIG_BASELINE%.json}-skip.json"
        fi
      elif valid_skip_record "$MIG_SKIP_RECORD"; then
        MIG_BYPASS=1
        MIG_BYPASS_RECORD="$MIG_SKIP_RECORD"
      fi
      if [ -n "$MIG_BYPASS" ]; then
        echo "done_run commit: ad-hoc worktree: valid closeout skip record governs ($MIG_BYPASS_RECORD); baseline migration bypassed; the session recorded its manual scoped copy and artifact list as completed before this commit (the wrapper validates only the skip record)"
      elif [ "$OWNED_PLAN_COUNT" -ne 1 ]; then
        echo "done_run commit: ad-hoc worktree: owned_plan_paths selects $OWNED_PLAN_COUNT plan baseline(s); none is chosen arbitrarily and no valid skip record: $MIG_SKIP_RECORD" >&2
        rm -rf "$tmpd"
        commit_die 2 "the worktree migration refused (rc=2); resolve what it named before the sync; nothing committed"
      else
        echo "done_run commit: ad-hoc worktree: migrating review staging docs and session logs to the main checkout before the sync"
        mkdir -p "$(dirname "$MIG_MANIFEST_DEST")"
        MG_OUT="$(python3 "$MIGRATE" migrate --baseline "$MIG_BASELINE" --source "$repo_top" --target "$PRIMARY" --manifest "$MIG_MANIFEST_DEST" 2>&1)" || MG_RC=$?
        printf '%s\n' "$MG_OUT"
        if [ "$MG_RC" -ne 0 ]; then
          rm -rf "$tmpd"
          commit_die 2 "the worktree migration refused (rc=$MG_RC); resolve what it named before the sync; nothing committed"
        fi
      fi
      if [ "$OWNED_PLAN_COUNT" -eq 1 ] && [ -n "$OWNED_PLAN_PATH" ]; then
        # Copy the plan's cited review records from the primary reviews home
        # into this run's reviews home before the closeout's verify-records
        # leg resolves that home from this worktree: a record written per the
        # no-mirror remedy is foreign by construction until copied run-side
        # (lesson 270). Report-and-continue: the verify-records refusal stays
        # the enforcing gate downstream.
        CC_OUT="$(python3 "$MIGRATE" copy-cited-records --plan "$OWNED_PLAN_PATH" --source "$PRIMARY" --target "$repo_top" 2>&1)" && CC_RC=0 || CC_RC=$?
        printf 'done_run commit: ad-hoc worktree: cited-record copy (rc=%s):\n%s\n' "$CC_RC" "$CC_OUT"
      fi
    fi
  fi
  if [ "$BOUNDARY_CLASS" = "per-task" ]; then
    # per-task boundary: the docs-branch sync is a final-closeout leg (the
    # boundary-class split, plan worktree-done-boundary-gate-roster-split);
    # the review-artifact migration above kept its position, and one trace
    # line names the skipped leg so the skip stays visible in the run record
    trace_stage docs-sync-skip
    echo "done_run commit: per-task boundary: skipping the docs-branch sync (a final-closeout leg; the run's final closeout owns the publication)"
  elif [ "$ROLLING_LOG" -eq 1 ]; then
    # rolling-log boundary: primary log writes hold the primary done lock
    # only and never take the repo-wide merge lock the sync would acquire
    trace_stage docs-sync-skip
    echo "done_run commit: rolling-log boundary: skipping the docs-branch sync (a final-closeout leg; primary log writes hold the done lock only)"
  else
    SYNC="$(resolve_helper docs_branch_sync.sh)"
    [ -n "$SYNC" ] || { rm -rf "$tmpd"; commit_die 3 "no docs_branch_sync.sh resolved (repo-local scripts/ or deployed home)"; }
    SYNC_RC=0
    SYNC_OUT="$(bash "$SYNC" 2>&1)" || SYNC_RC=$?
    printf '%s\n' "$SYNC_OUT"
    if [ "$SYNC_RC" -ne 0 ]; then
      rm -rf "$tmpd"
      commit_die "$SYNC_RC" "the docs-branch sync refused (rc=$SYNC_RC); nothing committed"
    fi
  fi

  # 14. Registry digest-capture arm: the working-tree registry bytes must
  #     still hash to the staged blob immediately before the commit.
  trace_stage registry-digest-arms
  REGISTRY_REL="docs/maintenance/document-registry.md"
  if printf '%s\n' "$STAGED_NOW" | grep -qxF "$REGISTRY_REL"; then
    STAGED_BLOB="$(git ls-files -s -- "$REGISTRY_REL" | awk '{print $2}')"
    WORK_BLOB="$(git hash-object "$REGISTRY_REL")"
    if [ "$STAGED_BLOB" != "$WORK_BLOB" ]; then
      rm -rf "$tmpd"
      commit_die 1 "registry digest arm: working-tree bytes diverge from the staged blob; a write landed after staging: re-read the file, re-apply this session's rows, re-stage, and re-run the commit"
    fi
    echo "done_run commit: registry digest arm: staged blob matches the working-tree bytes"
  fi

  # 15. Reverse-squash check-staged: its today observation point, immediately
  #     before the landing commit.
  trace_stage reverse-squash-check-staged
  RS_GUARD="$(resolve_helper reverse_squash_guard.py)"
  if [ -n "$RS_GUARD" ]; then
    RS_RC=0
    RS_OUT="$(python3 "$RS_GUARD" check-staged --repo "$repo_top" 2>&1)" || RS_RC=$?
    printf '%s\n' "$RS_OUT"
    case "$RS_RC" in
      0) ;;
      1) rm -rf "$tmpd"; commit_die 1 "reverse-squash guard refused the staged set; unstage the refused set and rebuild it from the intended edits; nothing committed" ;;
      *) rm -rf "$tmpd"; commit_die "$RS_RC" "reverse-squash guard tool failure (rc=$RS_RC)" ;;
    esac
  else
    echo "done_run commit: reverse-squash guard absent; check skipped"
  fi

  # 16. Exactly one captured-tree landing carrying work plus lessons, with
  #     the owned-commits ledger append fused to it; base-branch
  #     immutability is a warning line, never a refusal. An empty declared
  #     set over a non-empty staged index refuses before the construction:
  #     with no trailing pathspec Git reads `git commit --` as commit-the-
  #     whole-index, so every staged path is foreign and nothing may land.
  trace_stage landing-commit
  STAGED_NOW="$(git diff --cached --name-only HEAD)"
  if [ -z "$STAGED_NOW" ]; then
    if [ -n "$AUTH_PATH" ]; then
      # An authorized invocation whose staged set emptied before the landing
      # (the --revert-formatting arm among the causes) is a silent-inert
      # authorization if skipped: refuse naming the missing staged content.
      rm -rf "$tmpd"
      commit_die 1 "authorized landing: the staged set is empty at the landing (the authorized path's content left the index: $AUTH_PATH); nothing committed"
    fi
    if [ "${#DIRT_CORRECTION_PATHS[@]}" -gt 0 ]; then
      rm -rf "$tmpd"
      commit_die 1 "authorized landing: the staged set is empty at the landing (the authorized correction paths' content left the index: ${DIRT_CORRECTION_PATHS[*]}); nothing committed"
    fi
    echo "done_run commit: no staged changes; landing commit skipped"
    # no captured-ref swap will run on this path: the armed rolling-log
    # cleanup owner has nothing to own and disarms here
    disarm_rolling_log_cleanup
  elif [ "${#DECLARED[@]}" -eq 0 ]; then
    FOREIGN_SET="$(printf '%s\n' "$STAGED_NOW" | tr '\n' ' ')"
    rm -rf "$tmpd"
    commit_die 1 "landing commit refuses an empty declared set over a non-empty staged index; every staged path is foreign: $FOREIGN_SET; re-run with the set declared via --stage or unstage the foreign entries; nothing committed"
  else
    BRANCH="$(git branch --show-current)"
    STORY_KEY="$(printf '%s' "$BRANCH" | grep -oE '[A-Z][A-Z0-9]*-[0-9][0-9]*' | head -n 1)"
    FULL_SUBJECT="$subject"
    if [ -n "$STORY_KEY" ]; then FULL_SUBJECT="[$STORY_KEY] $subject"; fi
    echo "done_run commit: base-branch immutability: a commit reachable from the base branch is never amended; corrections land as additive follow-up commits (warning line, never a refusal)" >&2
    LEDGER_PATH=""
    RUN_ID="$(resolve_run_id)"
    if [ -n "$RUN_ID" ]; then
      LEDGER_PATH="$session/owned-commits-$RUN_ID.txt"
      mkdir -p "$session"
    else
      echo "done_run commit: owned-commits ledger skipped (no run manifest from Step 0)"
    fi
    if [ -n "$AUTH_RUN_ID" ]; then
      # An authorized invocation (cached-diff restoration or dirt
      # correction set) keys its ledger to the validated run tuple.
      LEDGER_PATH="$session/owned-commits-$AUTH_RUN_ID.txt"
      mkdir -p "$session"
    fi
    # The shared captured-tree landing: ordinary and authorized
    # primary-repository commits both record the staged tree, run the dirt
    # gate once against it, and land through the guarded ref transaction.
    captured_tree_landing
    echo "done_run commit: landed ${AUTH_LANDED_OID:-$(git rev-parse HEAD)}"
  fi

  # 17. The facts-resolved side repos: dirty paths reported per repo; one
  #     confirmed commit action each, the sensitive-data scan re-run over the
  #     staged side-repo set before that repo's commit.
  trace_stage side-repo-walk
  SIDE_REPOS=""
  for key in skills_repo_path shared_docs_dir; do
    value="$(side_facts_value "$key")"
    case "$value" in ""|/*) ;; *) continue;; esac
    [ -e "$value/.git" ] || continue
    case "$SIDE_REPOS" in *" $value "*) ;; *) SIDE_REPOS="$SIDE_REPOS $value ";; esac
  done
  if [ -z "$(printf '%s' "$SIDE_REPOS" | tr -d ' ')" ]; then
    echo "done_run commit: side-repo walk: no facts-resolved side repos resolved; walk skipped"
  fi
  for repo in $SIDE_REPOS; do
    DIRTY="$(git -C "$repo" status --porcelain --no-renames)"
    if [ -z "$DIRTY" ]; then
      echo "done_run commit: side-repo walk: $repo: clean"
      continue
    fi
    echo "done_run commit: side-repo walk: $repo: dirty paths:"
    printf '%s\n' "$DIRTY" | sed 's/^/  /'
    CONFIRMED=""
    for confirmed in ${SIDE_COMMIT_ARGS+"${SIDE_COMMIT_ARGS[@]}"}; do
      [ "$confirmed" = "$repo" ] && CONFIRMED=1
    done
    if [ -z "$CONFIRMED" ]; then
      echo "done_run commit: side-repo walk: $repo: left uncommitted (no confirmation for this repo)"
      continue
    fi
    SIDE_PATHS=()
    while IFS= read -r row; do
      [ -n "$row" ] && SIDE_PATHS+=("$(printf '%s' "$row" | cut -c4-)")
    done < <(printf '%s\n' "$DIRTY")
    git -C "$repo" add -- ${SIDE_PATHS+"${SIDE_PATHS[@]}"} || { rm -rf "$tmpd"; commit_die 3 "side-repo walk: git add refused in $repo"; }
    SCAN="$(resolve_helper scan-public-hygiene.sh)"
    if [ -n "$SCAN" ]; then
      SCAN_RC=0
      SCAN_OUT="$(cd "$repo" && PUBLIC_HYGIENE_REPO_ROOT="$repo" bash "$SCAN" --files ${SIDE_PATHS+"${SIDE_PATHS[@]}"} 2>&1)" || SCAN_RC=$?
      printf '%s\n' "$SCAN_OUT"
      if [ "$SCAN_RC" -ne 0 ]; then
        rm -rf "$tmpd"
        commit_die "$SCAN_RC" "side-repo walk: the sensitive-data scan refused $repo's staged set (rc=$SCAN_RC); that repo's commit did not happen"
      fi
    fi
    if ! git -C "$repo" commit -m "docs: done closeout side-repo landing" -- ${SIDE_PATHS+"${SIDE_PATHS[@]}"}; then
      rm -rf "$tmpd"
      commit_die 1 "side-repo walk: the commit refused in $repo"
    fi
    echo "done_run commit: side-repo walk: $repo: landed $(git -C "$repo" rev-parse HEAD)"
  done
  rm -rf "$tmpd"
}

# --- finalize subcommand ----------------------------------------------------

finalize_die() { # rc message...: fail loud with the named evidence
  local rc="$1"
  shift
  echo "done_run finalize: $*" >&2
  exit "$rc"
}

landing_pending_state() { # <session-dir> <run-id>; sets LANDING_PENDING, LANDING_TIP, BASE_BRANCH
  # The deferred-squash witness (backlog 2026-10-26-finalize-deferred-squash-
  # silent-success): the run's owned-commits ledger carries a landing commit
  # that is not on the base branch, so the squash to the default branch never
  # ran and a success-shaped summary would lie. Landed means either the
  # commit is an ancestor of the base branch (direct and merge landings) or
  # a recent base-history commit carries an equal tree (the squash proof's
  # tree fast path, the worktree-first standard's squash arm: a squash
  # landing changes the sha, so ancestry alone never sees it) or, when a
  # rebase after the ledger lines were written changed the branch's trees,
  # a recent base-history commit carries an equal first-parent delta
  # patch-id (the squash proof's content form, compared inside the same
  # 500-commit window). The base branch resolves from the
  # facts base_branch key, then origin/HEAD's short name; an unresolvable
  # base fails open to the current success shape (the caller warns), never
  # blocking the release ceremony. Quiet: callers own every emission.
  LANDING_PENDING=0; LANDING_TIP=""; BASE_BRANCH=""
  local ledger="$1/owned-commits-$2.txt" tip_tree
  [ -f "$ledger" ] || return 0
  LANDING_TIP="$(tail -n 1 "$ledger" 2>/dev/null)"
  [ -n "$LANDING_TIP" ] || { LANDING_TIP=""; return 0; }
  git cat-file -e "$LANDING_TIP" 2>/dev/null || { LANDING_TIP=""; return 0; }
  BASE_BRANCH="$(facts_toml_value base_branch)"
  if [ -z "$BASE_BRANCH" ]; then
    BASE_BRANCH="$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@')"
  fi
  if [ -z "$BASE_BRANCH" ] || ! git rev-parse --verify --quiet "refs/heads/$BASE_BRANCH" >/dev/null 2>&1; then
    LANDING_TIP=""; BASE_BRANCH=""; return 0
  fi
  if git merge-base --is-ancestor "$LANDING_TIP" "refs/heads/$BASE_BRANCH" 2>/dev/null; then
    return 0
  fi
  tip_tree="$(git rev-parse "$LANDING_TIP^{tree}" 2>/dev/null)" || { LANDING_TIP=""; BASE_BRANCH=""; return 0; }
  if git log --format='%T' -n 500 "refs/heads/$BASE_BRANCH" 2>/dev/null | grep -qxF "$tip_tree"; then
    return 0
  fi
  # Content-form squash proof: a run branch rebased after its ledger lines
  # were written carries the same delta under new shas and trees, so the
  # tree-identity scan above misses the squash; compare the branch delta's
  # patch-id against each scanned base commit's first-parent delta patch-id
  # inside the same 500-commit window (root commits and unreadable pairs
  # skip; the first match proves landed).
  local merge_base branch_pid base_commit base_parent base_pid
  merge_base="$(git merge-base "$LANDING_TIP" "refs/heads/$BASE_BRANCH" 2>/dev/null)" || merge_base=""
  if [ -n "$merge_base" ]; then
    branch_pid="$(git diff "$merge_base..$LANDING_TIP" | git patch-id --stable 2>/dev/null | awk 'NR==1{print $1; exit}')"
    if [ -n "$branch_pid" ]; then
      while IFS= read -r base_commit; do
        base_parent="$(git rev-parse "$base_commit^" 2>/dev/null)" || continue
        base_pid="$(git diff "$base_parent..$base_commit" | git patch-id --stable 2>/dev/null | awk 'NR==1{print $1; exit}')"
        if [ -n "$base_pid" ] && [ "$base_pid" = "$branch_pid" ]; then
          return 0
        fi
      done < <(git log --format='%H' -n 500 "refs/heads/$BASE_BRANCH" 2>/dev/null)
    fi
  fi
  LANDING_PENDING=1
}

cmd_finalize() {
  # Invocation telemetry start stamp (plan
  # docs/history/plans/2026-10-14-script-runtime-cost-telemetry.md, Task 3):
  # one python3-derived epoch captured at the function's entry so the
  # exit-side append below spans the whole finalize; fail-open and silent
  # (a missing python3 leaves the variable empty and the closeout unchanged).
  FINALIZE_START_EPOCH="$(python3 -c 'import time; print(repr(time.time()))' 2>/dev/null || :)"
  local from_holder=0 no_landing_cost=0 session_id="" path
  FINALIZE_MANIFEST=""; RUN_ID_ARG=""; GUARD_FIRINGS=()
  shift # subcommand
  while [ $# -gt 0 ]; do
    case "$1" in
      --manifest) FINALIZE_MANIFEST="$2"; shift 2;;
      --run-id) RUN_ID_ARG="$2"; shift 2;;
      --from-holder) from_holder=1; shift;;
      --session) session_id="$2"; shift 2;;
      --no-landing-cost) no_landing_cost=1; shift;;
      --guard-firing) GUARD_FIRINGS+=("$2"); shift 2;;
      *) echo "done_run finalize: unknown argument: $1" >&2; exit 3;;
    esac
  done

  local repo_top session lib
  repo_top="$(git rev-parse --show-toplevel 2>/dev/null)" || \
    finalize_die 3 "not inside a git repository"
  cd "$repo_top" || finalize_die 3 "cannot enter the repository root"
  session="$(session_dir)" || finalize_die 3 "cannot resolve the repo root"

  LOCK_SCRIPT="${DONE_LOCK_SCRIPT:-$(resolve_helper done-lock.sh)}"
  [ -n "$LOCK_SCRIPT" ] || finalize_die 3 "no lock script resolved (set DONE_LOCK_SCRIPT)"
  LIB="$(resolve_helper done_sweep_gates_lib.py)"
  [ -n "$LIB" ] || finalize_die 3 "no done_sweep_gates_lib.py resolved (repo-local scripts/ or deployed home)"

  RUN_MANIFEST="$(resolve_manifest_path)" || RUN_MANIFEST=""
  RUN_ID="$(resolve_run_id)"
  local finalize_rc=0 release_rc=0 marking_withheld=0

  # 1. Checkpoint refresh at the finalize preamble: a no-checkpoint refusal
  #    falls back to create-then-refresh; an already-finalized manifest is
  #    the skip-the-refresh arm. A missing manifest is a one-line note.
  if [ -z "$RUN_ID" ] || [ ! -f "$RUN_MANIFEST" ]; then
    echo "done_run finalize: no run manifest from setup; nothing to finalize or checkpoint; the release still runs"
  else
    SESSION_ID="${session_id:-${DONE_RUN_SESSION:-done_run_finalize}}"
    CK_OUT="$(python3 "$LIB" checkpoint-manifest --run-id "$RUN_ID" --mode refresh --session "$SESSION_ID" --gates landing 2>&1)"
    if [ $? -ne 0 ]; then
      case "$CK_OUT" in
        *"already finalized"*|"already complete"*)
          echo "done_run finalize: checkpoint refresh skipped (the manifest already finalized; nothing to refresh)";;
        *"no checkpoint present"*|*"create it first"*)
          python3 "$LIB" checkpoint-manifest --run-id "$RUN_ID" --mode create --session "$SESSION_ID" --gates landing >&2 \
            && python3 "$LIB" checkpoint-manifest --run-id "$RUN_ID" --mode refresh --session "$SESSION_ID" --gates landing >/dev/null \
            || { printf '%s\n' "$CK_OUT" >&2; echo "done_run finalize: WARNING: checkpoint create-then-refresh refused (mutated nothing); continuing" >&2; };;
        *)
          printf '%s\n' "$CK_OUT" >&2
          echo "done_run finalize: WARNING: checkpoint refresh refused (mutated nothing); continuing" >&2;;
      esac
    else
      printf '%s\n' "$CK_OUT"
    fi

    # 2. Manifest finalize: a missing manifest answers exit 0 with the lib's
    #    own note; any other non-zero exit is a real failure recorded for the
    #    final exit (the releases below still run; never stranded).
    #    Deferred-squash withholding: when the ledger's landing commit is not
    #    on the base branch (ancestry or the squash proof; the squash never
    #    ran), the complete marking is withheld and the deferral prints loud
    #    while the boundary stays continuable (rc 0, releases below run): the
    #    kept checkpoint and the incomplete manifest are the resumable state
    #    a re-run finalize consumes once the squash lands.
    if [ -n "$RUN_ID" ] && [ -f "$session/owned-commits-$RUN_ID.txt" ]; then
      landing_pending_state "$session" "$RUN_ID"
      if [ "$LANDING_PENDING" -eq 1 ]; then
        marking_withheld=1
        local ms_out ms_state ms_label
        ms_out="$(bash "$LOCK_SCRIPT" merge-status 2>/dev/null)"
        if [ -z "$ms_out" ]; then
          ms_state="unreadable"
        elif printf '%s\n' "$ms_out" | grep -qE ': held( |$)'; then
          ms_label="$(printf '%s\n' "$ms_out" | sed -En 's/^[[:space:]]*label: (.*)$/\1/p' | head -n 1)"
          ms_state="held by ${ms_label:-unknown}"
        else
          ms_state="free"
        fi
        echo "done_run finalize: WARNING: LANDING DEFERRED: the squash to $BASE_BRANCH has not landed; merge lock $ms_state; re-run finalize or the landing helper's land-worktree mode after the lock frees; the branch tip is $LANDING_TIP" >&2
        echo "done_run finalize: run manifest complete marking withheld until the squash lands (the checkpoint is kept for the resume)"
      elif [ -z "$LANDING_TIP" ] && [ -z "$BASE_BRANCH" ]; then
        echo "done_run finalize: WARNING: the deferred-squash honesty check is skipped (unresolvable base branch or unreadable ledger tip); the summary is not landing-verified" >&2
      fi
    fi
    if [ "$marking_withheld" -eq 0 ]; then
      FM_OUT="$(python3 "$LIB" finalize-manifest --run-id "$RUN_ID" 2>&1)" || finalize_rc=$?
      printf '%s\n' "$FM_OUT"
      if [ "$finalize_rc" -ne 0 ]; then
        echo "done_run finalize: FAILED (exit $finalize_rc); the run manifest finalize did not complete; running the releases so no lock strands" >&2
      else
        # 3. Checkpoint remove (only after the successful finalize).
        CR_OUT="$(python3 "$LIB" checkpoint-manifest --run-id "$RUN_ID" --mode remove 2>&1)"
        if [ $? -ne 0 ]; then
          printf '%s\n' "$CR_OUT" >&2
          echo "done_run finalize: WARNING: checkpoint remove refused; the sibling stays for a resume continuation" >&2
        else
          printf '%s\n' "$CR_OUT"
        fi
      fi
    fi
  fi

  # 3b. Guard-firing rows, BEFORE the done-lock release, never appended twice
  #     after a successful landing (plan
  #     2026-10-24-done-run-lock-span-and-append-ordering): rows known at
  #     landing time ride the landing commit through the commit subcommand's
  #     own --guard-firing, so a run with a prior landing commit has nothing
  #     left to append here. With no prior landing commit, the rows land
  #     through the checked commit subcommand as a child while the parent
  #     retains the done lock: the child writes them before its declared
  #     staging, stages the ledger path, and lands the bytes in its own
  #     captured-tree commit. A child failure before its landing restores the
  #     prior ledger bytes and index; a failure after the landing preserves
  #     the committed row and reports without rollback. Every outcome stays
  #     advisory: warnings only, and the release and status checks below run
  #     regardless.
  trace_stage guard-liveness-appends
  local guard_ledger_rel guard_snapshot child_pre_head child_post_head child_out firing
  if [ "${#GUARD_FIRINGS[@]}" -gt 0 ]; then
    guard_ledger_rel="scripts/gate_liveness_ledger.json"
    if [ -n "$RUN_ID" ] && [ -f "$session/owned-commits-$RUN_ID.txt" ] \
       && [ -s "$session/owned-commits-$RUN_ID.txt" ]; then
      # The carried claim is verified before printing: each firing's evidence
      # must appear in the landing commit's ledger bytes, else the message
      # says so instead of over-claiming (r1 residual item 2).
      landing_head="$(tail -n 1 "$session/owned-commits-$RUN_ID.txt")"
      carried_unverified=0
      for firing in ${GUARD_FIRINGS+"${GUARD_FIRINGS[@]}"}; do
        firing_evidence="$(printf '%s' "$firing" | cut -d: -f3)"
        if [ -z "$firing_evidence" ] || ! git show "$landing_head:$guard_ledger_rel" 2>/dev/null | grep -qF -- "$firing_evidence"; then
          carried_unverified=1
          break
        fi
      done
      if [ "$carried_unverified" -eq 0 ]; then
        echo "done_run finalize: guard-liveness rows verified in this run's landing commit $landing_head; never appended twice after a successful landing"
      else
        echo "done_run finalize: WARNING: a guard-firing row's evidence was not found in the landing commit $landing_head ledger bytes; the rows are not verified as carried; re-append them with --guard-firing on a follow-up invocation if they are still owed" >&2
      fi
    elif [ ! -f "$guard_ledger_rel" ]; then
      echo "done_run finalize: WARNING: no $guard_ledger_rel in this repository; the guard-liveness rows are skipped (advisory)" >&2
    else
      trace_stage guard-firing-child-commit
      GUARD_CHILD_ARGS=()
      for firing in ${GUARD_FIRINGS+"${GUARD_FIRINGS[@]}"}; do
        GUARD_CHILD_ARGS+=(--guard-firing "$firing")
      done
      guard_snapshot="$(mktemp)" || guard_snapshot=""
      guard_snapshot_ok=0
      guard_existed_before=0
      if [ -f "$guard_ledger_rel" ]; then
        guard_existed_before=1
        if [ -n "$guard_snapshot" ] && cp "$guard_ledger_rel" "$guard_snapshot" 2>/dev/null; then
          guard_snapshot_ok=1
        fi
      fi
      child_pre_head="$(git rev-parse --verify HEAD 2>/dev/null || true)"
      GUARD_CHILD_RC=0
      child_out="$(bash "$SCRIPT_DIR/done_run.sh" commit \
        --stage "$guard_ledger_rel" \
        --subject "telemetry: land guard-liveness ledger rows for run ${RUN_ID:-no-manifest}" \
        ${GUARD_CHILD_ARGS+"${GUARD_CHILD_ARGS[@]}"} 2>&1)" || GUARD_CHILD_RC=$?
      printf '%s\n' "$child_out"
      if [ "$GUARD_CHILD_RC" -ne 0 ]; then
        child_post_head="$(git rev-parse --verify HEAD 2>/dev/null || true)"
        # The reset is unconditional on child failure: a peer immediate-commit
        # in the classification window must not leave the child's staged
        # ledger entry behind in either arm (r1 residual item 3).
        git reset -q -- "$guard_ledger_rel" 2>/dev/null || true
        if { [ -z "$child_pre_head" ] && [ -z "$child_post_head" ]; } || \
           { [ -n "$child_pre_head" ] && [ "$child_post_head" = "$child_pre_head" ]; }; then
          if [ "$guard_snapshot_ok" -eq 1 ]; then
            cp "$guard_snapshot" "$guard_ledger_rel" 2>/dev/null || true
          elif [ "$guard_existed_before" -eq 0 ]; then
            rm -f "$guard_ledger_rel"
          else
            echo "done_run finalize: WARNING: the prior ledger bytes could not be snapshotted; the child's ledger bytes are left in the worktree" >&2
          fi
          echo "done_run finalize: WARNING: the guard-liveness child commit failed (rc=$GUARD_CHILD_RC) before landing; the prior ledger bytes and index were restored; the advisory rows are skipped; the release and status checks continue" >&2
        else
          echo "done_run finalize: WARNING: the guard-liveness child commit reported rc=$GUARD_CHILD_RC after landing; the committed ledger row is preserved (no rollback); read the child output above" >&2
        fi
      fi
      [ -n "$guard_snapshot" ] && rm -f "$guard_snapshot"
    fi
  fi

  # 4. Done-lock release: the env-token path by default; --from-holder (or
  #    lost exports) takes the lock script's metadata-sourced arm under its
  #    own recorded guards (pinned hold, same host, holder verifiably alive
  #    with exact identity, not pid 1, this shell descends from it).
  if [ "$from_holder" -eq 1 ] || [ -z "${DONE_LOCK_DIR:-}" ] || [ -z "${DONE_LOCK_TOKEN:-}" ]; then
    echo "done_run finalize: releasing the done lock via the from-holder arm (the hold's own acquire-time records gate it)"
    REL_OUT="$(bash "$LOCK_SCRIPT" release-repo --from-holder 2>&1)" || release_rc=$?
  else
    REL_OUT="$(DONE_LOCK_DIR="$DONE_LOCK_DIR" DONE_LOCK_TOKEN="$DONE_LOCK_TOKEN" bash "$LOCK_SCRIPT" release-repo 2>&1)" || release_rc=$?
  fi
  printf '%s\n' "$REL_OUT"
  if [ "$release_rc" -ne 0 ]; then
    echo "done_run finalize: done-lock release refused (rc=$release_rc); read the OUTCOME line above through the outcome contract, then run status" >&2
    # Observability (report-only): name the inputs the failed release actually
    # read, so a silent refusal never costs a diagnosis round guessing the env.
    if [ "$from_holder" -eq 1 ]; then
      echo "done_run finalize: release inputs: the from-holder arm (no session env consumed; the hold's own acquire-time records gate the release)" >&2
    elif [ -z "${DONE_LOCK_DIR:-}" ] || [ -z "${DONE_LOCK_TOKEN:-}" ]; then
      echo "done_run finalize: release inputs: DONE_LOCK_DIR/DONE_LOCK_TOKEN empty or unset (env lost with its tool-call shell); re-derive both from the hold's meta.env and re-run finalize" >&2
    else
      echo "done_run finalize: release inputs: lock dir ${DONE_LOCK_DIR}; token prefix ${DONE_LOCK_TOKEN:0:8}... (the env this shell actually read)" >&2
    fi
    [ "$finalize_rc" -eq 0 ] && finalize_rc="$release_rc"
  fi

  # 5. Merge-lock release when a hold survives (the sync and migration
  #    runners release their own spans in finally blocks; a surviving hold is
  #    a stranded span: exports when present, else the same from-holder arm).
  MS_OUT="$(bash "$LOCK_SCRIPT" merge-status 2>&1)" || MS_OUT=""
  if printf '%s\n' "$MS_OUT" | grep -qE ': free( |$)'; then
    echo "done_run finalize: merge lock free"
  else
    echo "done_run finalize: merge lock held; releasing the surviving span"
    if [ -n "${MERGE_LOCK_DIR:-}" ] && [ -n "${MERGE_LOCK_TOKEN:-}" ]; then
      MREL_OUT="$(MERGE_LOCK_DIR="$MERGE_LOCK_DIR" MERGE_LOCK_TOKEN="$MERGE_LOCK_TOKEN" bash "$LOCK_SCRIPT" merge-release-repo 2>&1)" || release_rc=$?
    else
      MREL_OUT="$(bash "$LOCK_SCRIPT" merge-release-repo --from-holder 2>&1)" || release_rc=$?
    fi
    printf '%s\n' "$MREL_OUT"
    if printf '%s\n' "$MREL_OUT" | grep -q '^OUTCOME: pass'; then
      echo "done_run finalize: surviving merge-lock span released"
    else
      echo "done_run finalize: WARNING: the merge-lock hold did not release under this shell (a foreign or ambiguous holder; every refusal names its failed gate); report and leave it" >&2
    fi
  fi

  # 6. Status-free verification.
  ST_OUT="$(bash "$LOCK_SCRIPT" status 2>&1)" || ST_OUT=""
  printf '%s\n' "$ST_OUT"
  if printf '%s\n' "$ST_OUT" | grep -qE ': free( |$)'; then
    echo "done_run finalize: done lock status: free"
  else
    # Honesty (report-only): the FAILED line distinguishes a completed
    # manifest (a release-only retry is safe) from an incomplete one, so the
    # next invocation is chosen from state, not guessed.
    local manifest_complete
    manifest_complete="unknown"
    if [ ! -f "${RUN_MANIFEST:-}" ]; then
      manifest_complete="no-manifest"
    else
      manifest_complete="$(python3 -c 'import json,sys
try:
    print("true" if json.load(open(sys.argv[1])).get("complete") else "false")
except Exception:
    print("unknown")' "$RUN_MANIFEST" 2>/dev/null)" || manifest_complete="unknown"
    fi
    case "$manifest_complete" in
      true)
        echo "done_run finalize: FAILED: done lock status is not free after the release; the run manifest is complete, so a release-only retry of this finalize with corrected DONE_LOCK_DIR/DONE_LOCK_TOKEN env is safe; do not report completion while a hold survives" >&2;;
      false)
        echo "done_run finalize: FAILED: done lock status is not free after the release; the run manifest is NOT complete, so the run needs its full finalize re-run after the hold resolves, not a release-only retry; do not report completion while a hold survives" >&2;;
      no-manifest)
        echo "done_run finalize: FAILED: done lock status is not free after the release; no run manifest was bound, so there is no finalize state to resume; do not report completion while a hold survives" >&2;;
      *)
        echo "done_run finalize: FAILED: done lock status is not free after the release; the run manifest's completion state is unreadable, so re-derive it from the manifest before choosing a release-only retry; do not report completion while a hold survives" >&2;;
    esac
    [ "$finalize_rc" -eq 0 ] && finalize_rc=1
  fi

  # 7. Report-input assembly: the landing summary plus the report-only
  #    missing-review-record scan (never blocking, never fabricating).
  local ledger landing_commit
  ledger=""
  if [ -n "$RUN_ID" ] && [ -f "$session/owned-commits-$RUN_ID.txt" ]; then
    ledger="$session/owned-commits-$RUN_ID.txt"
  fi
  landing_commit=""
  if [ -n "$ledger" ]; then
    landing_commit="$(tail -n 1 "$ledger")"
    # Fresh recompute: the guard-firing child commit above may have appended
    # the ledger's first line after the marking decision, so the summary
    # names the commit by its own current state; a commit not on the base
    # branch is a branch commit, never landing_commit=.
    landing_pending_state "$session" "$RUN_ID"
    if [ "$LANDING_PENDING" -eq 1 ]; then
      if [ "$marking_withheld" -eq 0 ]; then
        # The guard-firing child commit created the ledger's first line after
        # the marking decision: the manifest reads complete while the squash
        # pends, so the deferral prints here with the marking-consistent duty.
        echo "done_run finalize: WARNING: LANDING DEFERRED: the squash to $BASE_BRANCH has not landed; the complete marking above predates this ledger line; re-run finalize or the landing helper's land-worktree mode after the squash lands; the branch tip is $LANDING_TIP" >&2
      fi
      echo "done_run finalize: landing summary: run_id=$RUN_ID ledger=$ledger commits=$(wc -l < "$ledger" | tr -d ' ') branch_commit=$landing_commit (not on $BASE_BRANCH; squash pending)"
    else
      echo "done_run finalize: landing summary: run_id=$RUN_ID ledger=$ledger commits=$(wc -l < "$ledger" | tr -d ' ') landing_commit=$landing_commit"
    fi
  else
    echo "done_run finalize: landing summary: no owned-commits ledger for this run; nothing landed in the project repo through the commit subcommand"
  fi
  trace_stage missing-review-record-scan
  python3 - "$repo_top" <<'PYEOF' || echo "done_run finalize: WARNING: the missing-review-record scan could not run (report-only; the closeout continues)" >&2
import os
import re
import subprocess
import sys

repo_top = sys.argv[1]


def facts_toml_value(key):
    try:
        text = open(os.path.join(repo_top, ".ai-playbook", "facts.md"), encoding="utf-8").read()
    except OSError:
        return ""
    import re as _re
    m = _re.search(r'^%s = ["\'](.*)["\']$' % key, text, _re.M)
    return m.group(1) if m else ""


primary = subprocess.run(
    ["git", "-C", repo_top, "worktree", "list", "--porcelain"],
    capture_output=True, text=True,
).stdout
primary = next((line[len("worktree "):] for line in primary.splitlines()
                if line.startswith("worktree ")), repo_top)


def facts_rooted(value):
    if not value:
        return ""
    return value if os.path.isabs(value) else os.path.join(repo_top, value)


plans_completed = facts_rooted(facts_toml_value("plans_completed_dir")) \
    or os.path.join(repo_top, "docs/history/plans/completed")
reviews_dir = facts_rooted(facts_toml_value("reviews_dir")) \
    or os.path.join(primary, ".ai-playbook/reviews")

record_re = re.compile(r"[A-Za-z0-9._/-]*(?:plan-review|code-review)[A-Za-z0-9._/-]*-r\d+\.md")
reviewed = {}
for base, _dirs, files in os.walk(reviews_dir):
    for name in files:
        reviewed[name] = True

missing = []
try:
    plan_files = sorted(os.listdir(plans_completed))
except OSError:
    plan_files = []
for name in plan_files:
    if not name.endswith(".md"):
        continue
    try:
        text = open(os.path.join(plans_completed, name), encoding="utf-8", errors="replace").read()
    except OSError:
        continue
    for record in sorted(set(record_re.findall(text))):
        if os.path.basename(record) not in reviewed:
            missing.append((name, record))

for citing, record in missing:
    print(f"missing-review-record: {record} cited by {citing} (reconstruction duty: report with a witness note; never fabricate, never block, never delete)")
print(f"missing-review-record scan: {len(missing)} missing record(s)")
PYEOF

  # 8. Advisory append: the landing-cost telemetry line. Echo-and-continue:
  #    a failed append is a warning line and never blocks the closeout. The
  #    guard-firing rows ran before the done-lock release (step 3b), the
  #    landing-carried ones never appended again and the rest landed through
  #    the checked child commit under the held lock.
  trace_stage advisory-appends
  # A pending (unsquashed) landing commit records no cost line: the resume
  # re-run that completes the boundary appends the line once at completion.
  if [ "$no_landing_cost" -eq 0 ] && [ "${LANDING_PENDING:-0}" -eq 0 ] && [ -n "$landing_commit" ] && [ -n "$RUN_MANIFEST" ] && [ -f "$RUN_MANIFEST" ]; then
    metrics_dir="$(facts_toml_value metrics_dir)"
    metrics_dir="${metrics_dir:-.ai-playbook/metrics}"
    case "$metrics_dir" in /*) ;; *) metrics_dir="$repo_top/$metrics_dir";; esac
    mkdir -p "$metrics_dir" 2>/dev/null || true
    LC_RC=0
    LC_OUT="$(python3 - "$RUN_MANIFEST" "$landing_commit" "$metrics_dir/landing-costs.jsonl" "$session" <<'PYEOF' 2>&1
import datetime
import json
import os
import sys

manifest_path, landing_commit, costs_path, session = sys.argv[1:5]
plan_slug = None
note = "no owned plan recorded for this run"
try:
    record = json.load(open(manifest_path, encoding="utf-8"))
    owned = record.get("owned_plan_paths") or []
    if owned:
        plan_slug = owned[0]
        note = None
except (OSError, ValueError):
    pass
wall_hours = None
try:
    markers = sorted(
        (os.path.join(session, name) for name in os.listdir(session)
         if name.startswith("run-start-")),
        key=lambda p: os.path.getmtime(p),
    )
    if markers:
        start_epoch = int(open(markers[-1]).read().split()[0])
        wall_hours = round((datetime.datetime.now().timestamp() - start_epoch) / 3600.0, 4)
except (OSError, ValueError, IndexError):
    pass
line = {
    "plan_slug": plan_slug,
    "landing_commit": landing_commit,
    "wall_hours": wall_hours,
    "review_rounds": None,
    "gate_refusals": None,
    "operator_interventions": None,
    "tokens_est": None,
    "recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
}
if plan_slug is None:
    line["note"] = note
with open(costs_path, "a", encoding="utf-8") as handle:
    handle.write(json.dumps(line, sort_keys=True) + "\n")
print(f"landing-cost telemetry appended: {costs_path}")
PYEOF
    )" || LC_RC=$?
    printf '%s\n' "$LC_OUT"
    if [ "$LC_RC" -ne 0 ]; then
      echo "done_run finalize: WARNING: the landing-cost telemetry append failed (advisory; the closeout continues)" >&2
    fi
  fi

  # 9. Invocation telemetry: one invocation_kind closeout-battery line
  #    spanning the whole finalize (plan
  #    docs/history/plans/2026-10-14-script-runtime-cost-telemetry.md,
  #    Task 3). Unconditional and outside the landing-cost guard above:
  #    every real finalize arm (no-ledger, --no-landing-cost, no-manifest)
  #    records exactly one line; the usage-error and early-refusal arms
  #    exit before this block and record none. Same facts-resolved metrics
  #    home shape as the landing-cost writer, via the telemetry library
  #    beside this script. Fail-open and stdout-silent: the one python3
  #    call is fully silenced and `|| :`-guarded, so telemetry success or
  #    failure never changes the closeout's exit status, stdout, or stderr
  #    contract (diagnostics stderr-only at most, none by default).
  if [ -n "$FINALIZE_START_EPOCH" ]; then
    python3 -c '
import sys, time
from pathlib import Path
script_path = sys.argv[1]
try:
    lib_dir = str(Path(script_path).resolve().parent)
    if lib_dir not in sys.path:
        sys.path.insert(0, lib_dir)
    import invocation_telemetry as telemetry
    wall_ms = max(0.0, (time.time() - float(sys.argv[2])) * 1000.0)
    telemetry.record_invocation(script_path, "closeout-battery", wall_ms)
except Exception:
    pass
' "${BASH_SOURCE[0]}" "$FINALIZE_START_EPOCH" >/dev/null 2>&1 || :
  fi

  exit "$finalize_rc"
}

main() {
  if [ $# -lt 1 ]; then
    sed -n '2,182p' "${BASH_SOURCE[0]}" >&2
    exit 3
  fi
  case "$1" in
    setup) cmd_setup "$@";;
    commit) cmd_commit "$@";;
    finalize) cmd_finalize "$@";;
    *) echo "done_run: unknown subcommand: $1" >&2; exit 3;;
  esac
}

main "$@"
