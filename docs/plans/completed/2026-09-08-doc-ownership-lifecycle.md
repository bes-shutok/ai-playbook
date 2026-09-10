# Plan: Document ownership and immutable archive lifecycle

Origin backlog: `docs/history/backlog/2026-09-08-document-ownership-and-archive-lifecycle.md` (grill-complete 2026-09-08). Decisions: ADR-0003 in `docs/maintenance/project-decisions.md`; terms in `docs/maintenance/glossary.md`.

## Terms

- **Living SOT**: the one document or wire/schema source that owns the current normative rule for an idea (glossary).
- **Completed history artifact**: a completed plan, investigation, proposal, RFC, or non-mirror context file recording what was known or decided at a point in time; immutable after the freeze transition (glossary, widened).
- **Ownership registry**: one central Layer 2 file, `docs/maintenance/document-registry.md` by default, mapping document identity to the living SOT, completed history artifacts, and aliases; overridable via the `doc_registry_rel` facts key (glossary; grill decision 2/6).
- **Document identity**: a stable capability or concept identifier, independent of ticket, branch, or task (glossary).
- **Freeze transition**: the explicit lifecycle action that closes a document: archive move (where applicable), registry row with date and reason, no body edits (grill decision 4).
- **Registry validator**: the new `scripts/doc_registry_validator.py`; validates registry integrity, gates writes to immutable paths, and inventories legacy files (grill decision 3).
- **Skill-gate marker**: consent marker per `agents/hooks/skill-gate/README.md` Marker WRITE RECIPE (plans class); refresh before every plan-file write; constants live there, not here.
- **Session key**: empty-after-strip session id becomes literal `no-session`; otherwise `sha1(value)[:16]` hex.

## Assumptions

- assume glossary and ADR capture is already done and this plan references rather than repeats it; basis: ADR-0003 plus the Ownership registry, Document identity, and Living SOT glossary entries landed in the 2026-09-08 grill.
- assume the validator follows the `scripts/confluence-mirror-hygiene.sh` pattern (subcommands plus a `--selftest` mode with inline fixtures); basis: grill decision 3, existing sibling script.
- assume the dogfood migration covers only this repo's own docs tree; basis: grill decision 12.
- assume facts keys are read via the existing `scripts/facts_paths.py` helpers where one fits; basis: sibling validators do the same.

Decision points requiring a grill: scope dual-path binding (ADR-0003, 2026-09-08); central registry over frontmatter (grill Q2, 2026-09-08); standalone two-tier validator in done (grill Q3, 2026-09-08); explicit agent-prompted freeze (grill Q4, 2026-09-08); vocabulary reuse, registry location, corruption override per ADR-0001, mirrors unchanged, ephemera excluded, superseded archived not deleted, fixed 8-skill set, dogfood migration (backlog Grill decisions 5-12, 2026-09-08).

## Gist & Examples

**What changes.** Documentation lifecycle becomes explicit: every document is either a Living SOT (editable while its work is active) or a Completed history artifact (immutable after its freeze transition). One Ownership registry file records identity, SOT status, archive location, and successor relations. A Registry validator runs in `done`, hard-failing on duplicate identities, unprotected writes to completed-history paths, and successor cycles, warn-only on stale aliases and legacy files without registry entries. Skills prompt the freeze transition at natural moments instead of leaving archival to habit.

**Why.** Today a path rename or contract clarification edits several already-completed artifacts, which rewrites the historical record, churns small doc tasks, and obscures which document is authoritative. The existing single-SOT policy covers duplicate living prose but no close-freeze-move lifecycle and no alias handling (in-place redirect stubs are banned, so aliases need a registry home).

**Before (today).** A contract rule moves from plan A to `doc-hierarchy-upkeep` prose. Fixing a stale link into completed plan B means editing B's body; `done` notices nothing; superseded plan C is deleted outright.

**After (this plan).** Plan A completes: `git mv` to the completed dir plus one registry row (`identity`, `sot`, `archived`, `src`). The stale link into B is reported by the validator as a warn with a suggested alias; B's bytes never change; the alias lands in the registry. Superseded C is archived with a `superseded_by` successor row instead of being deleted.

**Edge cases.** Repos without a registry fail open (warnings only; the inventory mode is the migration backlog). A factual corruption fix to an immutable file requires explicit user confirmation per ADR-0001 plus an audit note in the registry row. Ephemera (`docs/history/reviews/`, `docs/tmp/`) and Confluence mirrors are out of scope; mirrors keep their existing refresh workflow.

## Evaluation Criteria

**Quality dimensions:**
- correctness: validator hard/warn tiers fire exactly per grill decision 3, proven by `--selftest` fixtures (dup identity, immutable-path write without override, successor cycle, stale alias, missing legacy entry).
- tool-agnosticism: no tool-specific names in skill edits; behaviors described by intent.
- hygiene: no PII, no absolute machine paths; `scan-public-hygiene.sh` exit 0; no em-dash in changed skill prose.
- immutability: no task edits a completed-history artifact's body; registry and metadata only.

**Done when:**
- the eight skills updated with bidirectional Integration Points.
- validator selftest green; validator wired into `done` as a numbered step.
- `docs/maintenance/document-registry.md` exists for this repo, backfilled by the inventory/migration pass; a full validator run on this repo exits 0 (warn-only findings allowed).
- plan review `ready=yes`, zero blocking.

**Ship when:**
- product service repos adopt the lifecycle (incremental, user-initiated migrations; prose only, no checklist).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/doc_registry_validator.py` *(new)*
- `agents/skills/doc-hierarchy/SKILL.md`
- `agents/skills/doc-hierarchy-upkeep/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/done/SKILL.md`
- `agents/skills/rfc-design/SKILL.md`
- `agents/skills/receiving-review/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/confluence-page-sync/SKILL.md`
- `README.md`
- `docs/maintenance/document-registry.md` *(new)*

**Tests:**
- `scripts/doc_registry_validator.py` `--selftest` fixtures (inline, same file) *(new)*

**Partially-in-scope freeze notes:** `agents/skills/plans/SKILL.md` and `agents/skills/done/SKILL.md` are open only for the lifecycle edits named in Tasks 2 and 5 (completion transition, superseded handling; new numbered step and its continuity line, facts-key table row); all other sections are frozen; reject any review finding that touches them. Peer-modified working-tree content in `agents/skills/plans/SKILL.md` and `agents/skills/review-plan/SKILL.md` from the parallel session is preserved; edits are additive and scoped to named sections.

**Out of scope; reject unless plan-related:**
- `agents/skills/learn/**`, `agents/skills/docs-branch/**`; reason: grill decision 11 leaves them untouched.
- `agents/skills/doc-hierarchy-migrate/**` and `scripts/verify-doc-hierarchy.sh`; reason: migration tooling stays untouched per grill decision 3.
- `docs/history/**` bodies (except registry metadata recorded elsewhere); reason: immutability is the plan's own subject.
- `agents/skills/review-plan/SKILL.md` beyond the additive immutable-context classification named in Task 7; reason: the peer session owns all other edits there.

## Validation Commands

```bash
# Validator selftest (fixtures inline in the script)
python3 scripts/doc_registry_validator.py --selftest

# Full run against this repo (registry present after Task 9): exit 0, warn-only findings allowed
python3 scripts/doc_registry_validator.py validate

# Immutable-path sweep over tracked history: no completed-history BODY changed since this plan's baseline
# commit. --diff-filter=MD scopes to modifications and deletions: a body edit under an immutable dir fails,
# and so does deleting a completed-history file (this plan's own Task 5 abolishes superseded-work deletion);
# ADDS (legitimate future lifecycle moves that register their rows) do not trip this plan's gate.
# The baseline is recorded by Task 1's first checklist item, before any task commit, so per-task
# commits cannot hide a body edit behind HEAD. Paths are pinned repo-relative on purpose: in this repo
# the facts values equal these defaults; the validator itself resolves per-repo dirs from facts keys.
BASE="$(cat docs/tmp/done-session/doc-lifecycle-base.txt)" || { echo "missing baseline file"; exit 1; }
[ -n "$BASE" ] || { echo "empty baseline file"; exit 1; }
git rev-parse -q --verify "$BASE^{commit}" >/dev/null || { echo "baseline is not a commit"; exit 1; }
CHANGED="$(git diff --name-only --no-renames --diff-filter=MD "$BASE" HEAD -- docs/plans/completed/ docs/history/backlog/completed/ docs/history/context/ docs/history/feature-notes/ ':(exclude)docs/history/context/confluence/')" || { echo "git diff failed"; exit 1; }
[ -z "$CHANGED" ] || { printf 'unexpected history edits:\n%s\n' "$CHANGED"; exit 1; }

# Uncommitted working-tree edits are gated too: porcelain keeps change-type letters so the
# gate can bound the registered-src exemption to the freeze move (renames gate both sides)
git -c core.quotePath=false status --porcelain | python3 scripts/doc_registry_validator.py check-writes --stdin

# Wiring pins (distinct spans; one probe per obligation)
grep -q "Step 2.648: Document registry hygiene" agents/skills/done/SKILL.md || { echo "missing done step"; exit 1; }
grep -q "doc_registry_validator_script" agents/skills/done/SKILL.md || { echo "missing facts key row"; exit 1; }
grep -q "superseded_by" agents/skills/plans/SKILL.md || { echo "missing successor archive rule"; exit 1; }
grep -qi "never licenses edits to local" agents/skills/confluence-page-sync/SKILL.md || { echo "missing mirror line"; exit 1; }
grep -q "document-registry" agents/skills/doc-hierarchy/SKILL.md || { echo "missing registry spec"; exit 1; }
test -f docs/maintenance/document-registry.md || { echo "missing registry file"; exit 1; }

# Stale-deletion sweep: plans must no longer prescribe deleting superseded plans
if grep -qi "When superseded, delete rather" agents/skills/plans/SKILL.md; then echo "stale deletion rule"; exit 1; fi

# Runtime deploy pin (Task 2): the done step invokes the runtime copy, which must be the repo symlink
test -L ~/.ai-playbook/scripts/doc_registry_validator.py || { echo "missing runtime symlink"; exit 1; }
readlink ~/.ai-playbook/scripts/doc_registry_validator.py | grep -q "scripts/doc_registry_validator.py" || { echo "runtime symlink has wrong target"; exit 1; }

# Format gates over changed files (file subcommand; prose files only)
bash scripts/check-no-em-dash.sh file agents/skills/doc-hierarchy/SKILL.md agents/skills/doc-hierarchy-upkeep/SKILL.md agents/skills/plans/SKILL.md agents/skills/done/SKILL.md agents/skills/rfc-design/SKILL.md agents/skills/receiving-review/SKILL.md agents/skills/review-plan/SKILL.md agents/skills/confluence-page-sync/SKILL.md README.md
bash scripts/scan-public-hygiene.sh
```

The immutable-path sweeps are fail-closed in both directions: a missing baseline file aborts with exit 1, an empty diff (correct state) passes, and any listed path fails loudly; the working-tree line gates uncommitted edits through the validator's `check-writes --stdin` mode. The em-dash checker invocation is fail-closed via the repo script's own exit code.

### Task 1: Registry validator script with selftest

Files:
- `scripts/doc_registry_validator.py` *(new)*

- [x] Record the plan baseline commit before any task commit (the Validation Commands immutable-path sweep diffs against it): `mkdir -p docs/tmp/done-session && git rev-parse HEAD > docs/tmp/done-session/doc-lifecycle-base.txt`. If the file already exists, stop and ask the user; never overwrite it (re-recording blesses a later HEAD and silently disarms the sweep).
- [x] Write failing selftest fixtures first (subcommands below, inline fixtures under a temp dir): `test_duplicate_identity_fails`; given a registry with two rows sharing one document identity, expects exit 1 with a duplicate-identity finding. `test_duplicate_sot_fails`; given two rows each declaring SOT ownership of one identity, expects exit 1 with a duplicate-SOT finding. `test_missing_required_field_fails`; given a registry row missing its identity or state field, expects exit 1 with a required-field finding. `test_successor_cycle_fails`; given A superseded_by B and B superseded_by A, expects exit 1 with a cycle finding. `test_immutable_write_fails`; given a changed-file list containing a path under a completed-history dir (`docs/plans/completed/`, `{backlog_completed_dir}`, `docs/history/context/` minus `confluence/`, `docs/history/feature-notes/`) with no override note in its registry row, expects exit 1. `test_immutable_write_override_passes`; given the same path with an audit-noted override row, expects exit 0. `test_stale_alias_warns`; given an alias whose target no longer exists, expects exit 0 with a warn finding. `test_missing_legacy_entry_warns`; given a completed-history file absent from the registry, expects exit 0 with a warn finding (fail-open). `test_inventory_lists_missing_entries`; given a completed-history tree with two files of which one has a registry row, expects `inventory` output to name exactly the unregistered file and exit 0. `test_mirror_paths_exempt`; given a changed path under `docs/history/context/confluence/`, expects exit 0 with no finding. `test_ephemera_exempt`; given paths under `docs/history/reviews/` or `docs/tmp/`, expects exit 0 with no finding. `test_validate_absent_registry_fails_open`; given a repo tree with no registry file at the resolved path, `validate` expects exit 0 with a single warn hint. `test_check_writes_absent_registry_fails_open`; given the same tree and a completed-history path on stdin, `check-writes --stdin` expects exit 0 with a warn hint (never exit 1). `test_check_writes_stdin_channel`; given three paths on stdin where exactly one is under an immutable dir, `check-writes --stdin` expects exit 1 naming only that path. `test_check_writes_argv_channel`; given the same three paths as argv, `check-writes` (no flag) expects exit 1 naming only the immutable one. `test_removed_diff_channel_fails_closed`; given the retired `--diff` flag (channel removed in the r2 fix round), expects exit 2 with a usage error (fail closed; callers feed `git diff` output to `--stdin` themselves). `test_unknown_flag_fails_closed`; given an unrecognized flag (for example `--st din` typo), expects exit 2 with a usage error, never a silent pass. All fixtures own their facts values under the temp fixture dir (never the host repo's `docs/` paths) so the selftest is hermetic.
- [x] Run `python3 scripts/doc_registry_validator.py --selftest` → expect RED (script absent or fixtures failing).
- [x] Implement subcommands: `validate` (registry integrity: required fields, duplicate identity/SOT declarations, successor cycles, alias target resolution; exit 0 with warns, exit 1 with hard findings), `check-writes` (input channels: paths as argv or a path list on stdin via `--stdin`; an unknown flag exits 2 fail-closed, never silent-ignore; the retired `--diff` channel is one such usage error; hard-fail per fixtures; override = registry row audit note), `inventory` (list completed-history files missing registry entries; exits 0 except on hard parse errors, warn output is the migration backlog). Note for the queued 2026-09-09 freeze-move follow-up plan: the r3 fix round restored staged-move observability via change-type-prefixed stdin (`git status --porcelain` / `git diff --name-status` output), so that plan must re-derive its staged-move premise from the porcelain channel instead of the removed `--diff` flag. Read facts keys (`plans_completed_dir`, `backlog_completed_dir`, `doc_registry_rel` default `docs/maintenance/document-registry.md`) via `scripts/facts_paths.py` where a helper exists; tolerate missing facts file by falling back to defaults (pre-registry repos fail open).
- [x] Run `python3 scripts/doc_registry_validator.py --selftest` → expect GREEN (all fixtures pass).
- [x] Commit: `skills: add doc registry validator with selftest`

### Task 2: Wire the validator into done

Files:
- `agents/skills/done/SKILL.md`

- [x] Add new Step 2.648, titled exactly `Step 2.648: Document registry hygiene` (numerically between 2.65 and 2.645; respect the existing step order and continuity line; the Validation Commands wiring pin greps this exact heading): runs `python3 ~/.ai-playbook/scripts/doc_registry_validator.py validate` and, when the session produced changed files, `check-writes --stdin` over the union of unstaged, staged, untracked, and committed-since-session-start changed paths (matching the neighboring hygiene steps' union pattern); warn-only findings are reported and do not block; hard findings block with the same stop semantics as neighboring hygiene steps; when the registry file is absent, the step reports the inventory hint once and continues (fail-open); when the validator script itself is absent at the runtime path, the step reports that once and continues the same way (fail-open, matching pre-deploy vendored consumers).
- [x] Deploy the runtime copy: create the symlink `~/.ai-playbook/scripts/doc_registry_validator.py` pointing at the repo `scripts/doc_registry_validator.py` (matching the existing runtime registry symlink model); fail loudly if the runtime dir is unwritable.
- [x] Update the Workflow continuity line to include 2.648 and add a facts-key table row `doc_registry_validator_script` (default `~/.ai-playbook/scripts/doc_registry_validator.py`), matching the `confluence_mirror_hygiene_script` row shape.
- [x] Commit: `skills: gate done on doc registry hygiene`

### Task 3: doc-hierarchy schema: states, registry, archive semantics

Files:
- `agents/skills/doc-hierarchy/SKILL.md`

- [x] Add a Document states subsection: Living SOT vs Completed history artifact; freeze transition definition (explicit, agent-prompted, never time-inferred); registry shape (identity, sot, state, archived date, reason, src path, successor/superseded_by, aliases, optional audit note); `doc_registry_rel` facts key with default `docs/maintenance/document-registry.md`; scope note that service repos bind via the migration-complete signal and the instructions repo adopts by convention (ADR-0003).
- [x] Add Integration Points rows: `done` (Step 2.648 runs the registry validator), `plans` (completion transition writes the registry row), `rfc-design` (closure transition).
- [x] Commit: `skills: doc-hierarchy gains document states and ownership registry`

### Task 4: upkeep refuses edits to immutable artifacts

Files:
- `agents/skills/doc-hierarchy-upkeep/SKILL.md`

- [x] Add the refusal rule: routine edits to Completed history artifacts are forbidden; change lands in the Living SOT plus a minimal pointer; broken historical links are alias/registry work, never body edits; corruption override follows ADR-0001 semantics (explicit user confirmation, minimal edit, registry audit note).
- [x] Add an Integration Points step referencing the doc-hierarchy registry spec and the freeze-prompt duty (nag when a Layer 3 file is still cited as current truth; never auto-reclassify).
- [x] Commit: `skills: upkeep refuses edits to completed history artifacts`

### Task 5: plans completion and supersession transitions

Files:
- `agents/skills/plans/SKILL.md`

- [x] Extend Plan Lifecycle: completion = archive move plus one registry row append (identity, archived date, src path) in the same pass; the archived plan's body is not edited.
- [x] Replace the superseded-plan deletion rule (the existing line "When superseded, delete rather than leaving stale `[ ]` items."): superseded plans are archived with a `superseded_by` successor registry row; superseded backlog items move to `{backlog_completed_dir}` marked `Status: superseded` instead of deletion. The replacement must remove the pinned deletion sentence; the Validation Commands stale-deletion sweep greps for it.
- [x] Commit: `skills: plans archives superseded work with successor rows`

### Task 6: rfc-design closure transition

Files:
- `agents/skills/rfc-design/SKILL.md`

- [x] Add the closure step: when the user declares an RFC superseded or accepted, prompt the freeze transition (registry row with successor or accepted-SOT relation); the old body is preserved; require a stable capability identity at creation (ticket ids as provenance only).
- [x] Commit: `skills: rfc-design closes with successor relation`

### Task 7: review skills treat history as immutable context

Files:
- `agents/skills/receiving-review/SKILL.md`, `agents/skills/review-plan/SKILL.md`

- [x] `receiving-review`: findings located in Completed history artifacts are classified immutable context; the fix is a pointer or successor in the Living SOT, not an edit to the artifact (extends the existing frozen-docs disposition).
- [x] `review-plan` (additive only; peer edits preserved): reviewers classify historical-artifact findings as immutable context pointing at the current SOT.
- [x] Commit: `skills: review skills classify history as immutable context`

### Task 8: confluence sync no-license line and README catalog

Files:
- `agents/skills/confluence-page-sync/SKILL.md`, `README.md`

- [x] Add the explicit line to `confluence-page-sync`: mirror sync never licenses edits to local historical artifacts or non-mirror context.
- [x] Update `README.md` skill catalog entries where the eight skills' descriptions changed (doc-hierarchy family registry wording; done step mention if the catalog describes it).
- [x] Commit: `skills: confluence sync no-license line and README catalog`

### Task 9: dogfood registry and migration on this repo

Files:
- `docs/maintenance/document-registry.md` *(new)*

- [x] Run `python3 scripts/doc_registry_validator.py inventory` against this repo; classify candidates per the backlog migration rules, but this task records registry rows and aliases ONLY (no `git mv` moves): any candidate that would need an archive move is listed in the task log for a user-approved follow-up, so the immutable-path sweep stays satisfiable; no body rewrites.
- [x] Create `docs/maintenance/document-registry.md` with backfilled rows for existing completed plans under `docs/plans/completed/`, backlog items under `docs/history/backlog/completed/`, and RFC/proposal files under `docs/history/feature-notes/`; add `doc_registry_rel` to `.ai-playbook/facts.md` (gitignored runtime file; not committed).
- [x] Run the full Validation Commands block → expect GREEN (exit 0; warn-only findings allowed).
- [x] Commit: `skills: dogfood doc registry migration on ai-playbook`

## Design Invariants (CR Guard)

- Completed-history bodies are never edited by this plan's tasks or by the workflows it prescribes; the freeze transition is metadata plus move only (ADR-0001, grill decision 2).
- In-place redirect stub files stay banned; aliases live only in the registry (verify script deletes stubs; grill decision 2).
- Pre-registry repos fail open; the validator never auto-reclassifies a living document (grill decisions 3 and 4).
- The migration/instructions repo stays out of `verify-doc-hierarchy.sh` scope; the validator must work on any repo with resolved facts paths (ADR-0003).
- Push, branch, review, and user-approval authorization are unchanged (backlog non-goal).
