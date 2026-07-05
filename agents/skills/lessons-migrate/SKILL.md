---
name: lessons-migrate
description: One-time-per-repo migration of a project's development_lessons.md into the two-layer corpus (strict user-level + convention project-level). Use when adopting the two-layer lessons convention in a repo for the first time, or when re-auditing a prior migration's review list.
---

# Lessons Migrate

One-time-per-repo migration engine that splits a project's
`docs/maintenance/development_lessons.md` into the two-layer corpus:
cross-project lessons move to the strict user-level corpus
(`<shared_docs_dir>/development_lessons.md`, `UL#N` namespace, gate-enforced);
project-specific lessons stay in the repo file (`#N` namespace, convention).
It also compact-renumers both files, rewrites repo-wide `#N` references from
the remap, dedups against the existing user corpus, deletes the derived
`principle-index.md`, emits a frozen audit snapshot, and self-checks via the
gate.

This skill is **repo-agnostic and zero-config**: the classifier keys off the
family catalog (`coding_guidelines.md` #17-#25) plus a generic-shape
engineering vocabulary. **No domain keywords are baked in or required** (there
is no `--domain-keywords` flag). The same skill runs in any repo.

## When to Use

- A repo is adopting the two-layer lessons convention for the first time (its
  `docs/maintenance/development_lessons.md` predates the split, or it has none
  yet and you are seeding from a project that does).
- You are re-running after a prior run's review list was curated (promotions,
  merges, ambiguous refs resolved) and you want a clean re-run.

Do NOT use for routine `learn` captures (use the `learn` skill). This is a
manual, one-time-per-repo tool.

## How It Works

The skill invokes `~/.ai-playbook/scripts/lessons_migrate.py` (canonical source
in the ai-playbook repo at `~/Projects/myrepos/ai-playbook/scripts/`). The
engine is stdlib-only and the only writer of BOTH files during a migration.

**Sibling script convention (mixed).** The runtime directory `~/.ai-playbook/scripts/`
is mixed by design, and the three lessons scripts adopt a **repo-homed** model
while older siblings stay **runtime-only**:

- **Repo-homed (canonical in `ai-playbook/scripts/`, synced to runtime):**
  `lessons_index.py`, `lessons_adopt.py`, `lessons_migrate.py`. These are
  version-controlled; edit the repo copy and sync to `~/.ai-playbook/scripts/`.
- **Runtime-only (no repo source):** `done-lock.sh`, `scan-public-hygiene.sh`,
  and similar older siblings. They live only at their runtime path.

This mixed convention is intentional; do not "normalize" it without a separate
cross-project decision.

### Inputs

- The repo's `docs/maintenance/development_lessons.md` (positional arg).
- The user corpus path `<shared_docs_dir>/development_lessons.md`, resolved by
  PARSING the lowercase `shared_docs_dir` key from `.ai-playbook/facts.md` (it
  is NOT an env var). Created if absent (cold start).

### Generic-first classifier (zero-config, repo-agnostic)

Signals, evaluated first-match-wins:

1. **Family tag (first checked):** a lesson already carrying a well-formed
   `**Principle:** Family <A-H>` tag (authored by `generalize`/`learn` as a
   cross-project precept) is **cross-project**.
2. **Generic engineering shape:** title/body matches a built-in generic
   vocabulary drawn from the family catalog (type-annotation specificity,
   exception handling, post-aggregation validation, test discipline,
   matching/dedup, review loops, data-loss/warning logging, atomic writes,
   sentinel values) AND has no domain residue is **cross-project**. This
   vocabulary is cross-project and stable (it IS the catalog), NEVER repo
   terms.
3. **Default - project-specific:** anything not matching (1)/(2) stays in the
   repo file. **This is the safe call:** the costly error (promoting a
   project-specific lesson into the shared corpus) is hard to make by
   construction. A bespoke engine that keyword-matched "validate"/"FIFO" as
   generic would wrongly promote a domain-coupled lesson; this classifier does
   not.
4. **Tail summary (non-routing):** the review list emits one summary line
   counting the retained untagged project-specific lessons, for a manual
   promotion pass. No auto-mining, no stoplist, no `--domain-keywords`
   override.

The per-family keyword phrase list is a SECONDARY DERIVED view of the catalog;
when a future audit revises a family's `**Shape trigger:**` wording this list
can drift. A `--selftest` discriminating-token assertion guards it (each
family's list has at least one token not in the union of the others').

### Preconditions (PROSE; no runtime enforcement for concurrency)

1. **git-clean precondition (FULL write scope, both repos).** The engine
   refuses to start unless `git diff --quiet` succeeds over EVERY path it will
   write: in the project repo `docs/maintenance/development_lessons.md`,
   `src/`, `tests/`, `AGENTS.md`, `docs/maintenance/`; in ai-playbook the
   user-corpus file. This is scoped to the FULL write scope (not just the
   inputs) so an unrelated uncommitted change in `src/`/`tests/` is not
   destroyed by the `git checkout -- <scope>` recovery.
2. **No concurrency with `learn`.** The migrator and a `learn` append BOTH
   rewrite the shared user corpus with NO lock and NO runtime detection.
   Before invoking the migrator, ensure NO `learn` is running in ANY terminal
   in ANY repo. A concurrent append between this tool's read and `os.replace`
   is silently lost (last-writer-wins). The operator is the sole guard.

### Atomic write order (true atomicity for the failure case)

Build BOTH file contents + the remap in memory first, then:

1. **User corpus first:** write the new corpus to a hardened `.tmp`
   (`O_EXCL|O_NOFOLLOW` - a planted `.tmp` symlink is refused), run the gate on
   the `.tmp`, require exit 0, and `os.replace` ONLY on success. On failure the
   `.tmp` is deleted and BOTH real files are left untouched (the project file
   has not been written yet).
2. **Project file + repo-wide refs second:** write the project file via the
   same hardened primitive, then rewrite repo-wide `#N` references. ALL write
   sites (user corpus, project file, EVERY repo-wide ref-rewrite target in
   `src/`/`tests/`/`AGENTS.md`/docs) use the shared `atomic_write_text`
   primitive. A later failure here is NOT rolled back (the project file is
   convention; `git checkout -- <files>` for the full write scope is full
   recovery per the git-clean precondition).

### Rewrite rule (single discriminator, applied everywhere)

ONE rewrite rule everywhere (`src/**/*.py`, `tests/**/*.py`, `**/*.md` minus
`docs/history/`, and in-body cross-links inside the lessons file itself). A
`#N` token is a LESSON citation iff ALL hold:

- (i) value is in the OLD number set;
- (ii) NOT inside a fenced code block;
- (iii) word boundary `#(\d+)\b` (so `#5,000 EUR` is not mismatched);
- (iv) after stripping a trailing backtick, if the immediately-preceding
  non-space token is a filename ending in `.md`, that filename MUST be
  `development_lessons.md` (a self-citation IS a lesson ref and IS rewritten);
  any OTHER `.md` filename (`coding_guidelines.md`, `python_guidelines.md`,
  etc.) is a RULE number in another file and is LEFT UNCHANGED;
- (v) the preceding token is NOT a process/identifier prefix
  (case-insensitive denylist: `Finding`, `Findings`, `Medium`, `Blocker`,
  `Low`, `High`, `Task`, `Tasks`, `Rule`, `Rules`, `Round`, `Rounds`, `Step`,
  `Steps`, `Invariant`, `Invariants`, `Family`, `Campo`, `Quadro`, `Anexo`,
  `Tabela`, `CIRS`, `CRG`, `SRG`; or the patterns `DP-\d+`, `r\d+`, `UL#`,
  `art\.?`).

Multi-number forms (`#N, #M`, `#N / #M`, `#N, #M, #K, #L`) are a repeated
group; EVERY `#N` in the match goes through the discriminator.

**Per-token resolution:**

- **same-tier** (stays project-side) -> rewrite to new `#N`;
- **cross-tier** (moved to user corpus) -> REMOVE the token (drop `#N`; the
  `UL#` namespace is user-level only, NEVER written to a project file). Within-
  line cleanup: a removed token that was the SOLE content of a parenthetical
  `(#N)` takes the parentheses with it. A removal from running prose is flagged
  "review prose grammar" in the audit list (no grammar engine; accepted
  cosmetic residual). **Cross-tier removal does NOT lose discoverability**:
  both layers load into the agent's context, so the moved lesson remains
  reachable via the user corpus.
- **ambiguous** -> FLAG (no rewrite; emitted to the review list).

**Renumber scope:** the compact-renumber pass rewrites `## N.` HEADINGS only;
in-body `#N` citations are rewritten SOLELY by this remap pass (renumbering
body `#N` in BOTH passes would double-shift every citation).

**Lead-in enumeration audit:** the review list emits EVERY distinct
`<lead-in> #N` token discriminated AS a lesson (rewritten or removed), grouped
by lead-in word. A hand-maintained denylist can never be PROVABLY complete, and
the authoritative remap-driven reconciliation does NOT catch a denylist miss
(the migrator records a mis-discriminated process-id as `renumbered-to-new`,
then "correctly" confirms its own mis-decision). The backstop for a ONE-TIME
migration of a KNOWN corpus is this minutes-long operator confirmation that no
process-id lead-in snuck through.

### Output

- **Frozen audit snapshot** at
  `docs/history/feature-notes/<run-date>-principle-index-audit-snapshot.md`
  (FROZEN ONE-TIME AUDIT banner; verbatim `## Blind-spot analysis`,
  `## Dry-run recall`, `## Precision gate`, `## Duplicate clusters`,
  `## Accounting check` from the deleted index). `<run-date>` is the migration
  run date.
- **Deletes** `docs/maintenance/principle-index.md`.
- **Review list** under `docs/tmp/lessons-migrate/<run-date>-review-list.md`:
  tail summary + dedup-merge flags + ambiguous-ref flags + the removed/
  renumbered token audit + the lead-in enumeration audit + the full remap
  table.
- **Self-check:** the gate ran on the `.tmp` in write-step 1 (abort-before-
  `os.replace`); the engine re-runs the gate on the final user corpus as
  belt-and-braces (exit 0). The AUTHORITATIVE stale-ref reconciliation is
  remap-driven (every touched token recorded old-value -> action; asserts no
  discriminated lesson token was left at its OLD value unless the action was
  `removed` or `left-non-lesson`). Coarse echoes: (a) repo-wide grep for old
  filename/lesson-qualified citations -> zero; (b) in-corpus discriminated
  lesson-`#N` with value > M -> zero (KNOWN blind spot: misses values <= M;
  the authoritative check closes it).
- **Summary** to stdout: counts (project-specific kept, cross-project moved,
  ambiguous flagged, dedup-merge flagged, refs rewritten, refs unremappable).

The **project file is convention** (no gate is ever applied to it); malformed
tags and zero-tag lessons survive unchanged in the project output.

## Procedure

### Step 0: Resolve the script

```bash
script="${LESSONS_MIGRATE_SCRIPT:-${HOME}/.ai-playbook/scripts/lessons_migrate.py}"
```

`~/.ai-playbook/scripts/` is trusted. `LESSONS_MIGRATE_SCRIPT` override is
local-testing only.

### Step 1: Dry-run first (audit before destructive write)

```bash
python "$script" --dry-run docs/maintenance/development_lessons.md
```

Review the emitted classification + review list (the untagged-retained tail
summary, ambiguous-ref flags, the planned cross-tier removals, the same-tier
renumbers, and the planned remap table). Confirm the classifier ran
zero-config (no domain arguments). Curate the review list: promote genuine
cross-project lessons from the project file to the user corpus by hand if the
classifier missed them (signal 1 misses ~40 untagged lessons until
`generalize` mandates tags for all Excluded lessons; the tail summary lists
them).

### Step 2: Preconditions check

- `git status` is clean across the FULL write scope in BOTH repos (the engine
  enforces this; if it refuses, commit or stash, then re-run).
- **No `learn` is running in ANY terminal in ANY repo** (prose precondition;
  the engine cannot detect this).

### Step 3: Run the migration

```bash
python "$script" docs/maintenance/development_lessons.md
```

Confirm the summary counts, that the self-check gate passed (exit 0), and that
the engine (not manual edits) performed the rewrite/remap/delete/snapshot.

### Step 4: Curate the review list

The review list at `docs/tmp/lessons-migrate/<run-date>-review-list.md` holds:

- **Tail summary:** untagged retained lessons to consider promoting.
- **MERGE flags:** near-duplicate cross-project lessons already in the user
  corpus; confirm the merge by hand (the engine flags-but-does-not-add).
- **AMBIGUOUS refs:** citations the engine could not map 1:1; resolve by hand.
- **Removed/renumbered token audit:** every discriminated lesson token
  (old -> action) for traceability.
- **Lead-in enumeration audit:** confirm no process-id lead-in snuck through
  the denylist.
- **Remap table:** the full old-`#N` -> new-`#N` / REMOVE / FLAG mapping.

Cross-tier in-corpus links are AUTO-REMOVED by the engine; no manual resolution
pass. The audit list shows what was removed (the moved lessons stay reachable
via the user corpus both layers load).

## Interruption recovery

No stage marker, no resume predicate, no `--force`. If interrupted, recover by
rolling back BOTH repos to the clean pre-migration state and re-running:

```bash
# In the project repo:
git checkout -- docs/maintenance/development_lessons.md src/ tests/ AGENTS.md docs/maintenance/
# In ai-playbook:
git checkout -- projects/.ai-playbook/development_lessons.md
```

**If the user-corpus `os.replace` in ai-playbook committed before the crash,
BOTH repos MUST be rolled back.** Rolling back only the project repo leaves
run-1's appended lessons in the user corpus; the re-run then emits a merge-flag
flood (dedup flags-but-does-not-add) rather than clean recovery. The dedup step
protects the user corpus from double-appends on a clean re-run.

The engine also refuses to re-run on a project file that is already in the
post-migration steady state (contiguous `## 1..N`); the refusal message
includes the recovery recipe.

## Idempotency

Re-running on an already-migrated project file (contiguous `## 1..N`) is
refused cleanly with the recovery recipe. There is no `--force`. To re-run
after curating a review list, roll back both repos per the interruption recipe
first.

## Validation

After a run, confirm:

- The user corpus passes the strict gate:
  `python ~/.ai-playbook/scripts/lessons_index.py <user_corpus>` exits 0.
- The gate's own contract still holds (the gate-behavior cases - duplicate,
  invalid-family, fenced pseudo-tag, taxonomy table, unbalanced fence - live
  in the gate's in-memory selftest, NOT in any adopting repo's pytest):
  `python ~/.ai-playbook/scripts/lessons_index.py --selftest` exits 0. Run
  this once per migration so a regression in the gate (the authority the
  migrated corpus is validated against) is caught at the run, not later.
- No tracked reference to `principle-index.md` survives anywhere it could hide
  (history excepted).
- The project file is plain markdown with contiguous `#N` and no coupling to
  the gate or user corpus (no `lessons_index`, no `UL#`).
- No stale OLD lesson numbers survived the remap (repo-wide grep for old
  filename/lesson-qualified citations -> zero).

## Threat model

- The git-clean precondition is the sole recovery guard. No `.bak`; no lock.
  `git checkout -- <scope>` is full recovery PRECISELY because the scope was
  clean before the run.
- The no-concurrency-with-`learn` contract is unenforced. The operator is the
  sole guard; a concurrent append is silently lost (last-writer-wins).
- `~/.ai-playbook/scripts/` is trusted; stdout is never `eval`'d. The engine
  writes via the hardened `atomic_write_text` primitive at every site.

## Additional resources

- Plan: `docs/history/plans/2026-06-29-lessons-corpus-derived-index.md` (Task 4
  is the authoritative spec).
- Gate: `~/.ai-playbook/scripts/lessons_index.py` (read-only; validates the
  user corpus).
- Shared primitives: `~/.ai-playbook/scripts/lessons_corpus.py` (parser,
  fence-aware collector, `VALID_FAMILIES`, `atomic_write_text`).
- Catalog: `coding_guidelines.md` #17-#25 (the family authority).
