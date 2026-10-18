# Plan: worktree removal migration gate

Backlog origin: docs/history/backlog/2026-10-05-authoring-worktree-migration-ordering-fence.md
Driving force: code-quality
Plan review record: the staging series docs/history/reviews/2026-10-07-plan-review-worktree-removal-migration-gate-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 1.5h total, largest task 1.0h

## Terms

- removal point: the moment a session is about to run `git worktree remove` for its own ad-hoc authoring or execution worktree; the gate prescribed by this plan fires here and nowhere earlier.
- gate-removal subcommand: a new subcommand of `scripts/worktree_closeout_migrate.py` that verifies the session's owned staging docs are present in the primary reviews home and refuses the removal otherwise.
- primary reviews home: the primary checkout's `{reviews_dir}` (facts key, `docs/history/reviews/` default); the migration destination the prose orderings already name.
- owned staging docs: the review-record series the session's plan header cites through its `Plan review record:` or `Plan review:` label (the gate's own header-line extraction, whole plan body never scanned) plus any `--claims` file paths; a claims entry outside the reviews home is refused, never skipped.
- verify-present primitive: the helper's existing capture/verify-records presence check; the gate composes it for presence and performs its own header-line extraction (the extraction, the refusal rendering, the claims refusal, and the exit vocabulary are the gate's own, per the Task 1 arms).

## Why

Twice witnessed (2026-09-18, 2026-10-05), an in-session run landed its plan and tore down its ad-hoc worktree in the same command before the review-artifact migration ran, destroying the gitignored staging records; the 2026-10-05 loss was rebuilt only from session records. The ordering is prose in three homes and none of them sits between the landing commit and the worktree removal on the in-session path.

## Outcome

Removing an ad-hoc worktree whose owned staging docs are not verified in the primary reviews home fails loudly at the removal point, naming the missing paths and the migrate command that fixes them.

- `scripts/worktree_closeout_migrate.py gate-removal` refuses (exit 1, `OUTCOME: fail`) while any owned record is absent, refuses on an empty owned set naming the absent header line (the fail-closed arm; a vacuous pass would be the silent-pass neighbor of the witnessed loss), and passes (exit 0, `OUTCOME: pass`) printing the sanctioned removal command when every owned record is verified present.
- The three prose homes prescribe the gated invocation at their removal sentences, so the in-session path reads the gate at its own teardown.
- The maintenance pins suite holds the three prescribed-invocation literals, so removing a re-point fails the suite.

Gate delta: one new refusal path (a new gate-removal subcommand) plus one pins section (three presence pins); declared residual: the gate binds sessions that follow the re-pointed rule text - a teardown assembled without consulting skill prose bypasses it, and the dispatching entry's Plan 2 residue sweep reusing this gate's primitive is the recorded backstop; paying witness: the twice-witnessed teardown data-loss class the origin row records (the 2026-10-05 instance destroyed review artifacts rebuilt only from session records); no new protocol layer, state field, or gate in any skill body; removals: none. A review-layer duty whose violation blocks is declared here: the prescribed invocation is a session duty enforced by this helper's exit code, witnessed by the origin row's recovery-path prose.

## Assumptions

- The gate is a new `gate-removal` subcommand of `scripts/worktree_closeout_migrate.py` reusing its existing capture/verify primitives; basis: the dispatching entry names the helper as the verify-present primitive to reuse.
- Owned staging docs derive from the plan header's `Plan review record:` line (the r-series paths) plus the optional `--claims` file, mirroring the helper's existing `--plan`/`--claims` interface; basis: the helper's own interface.
- The prose homes and their anchors: the done skill's Step 2 migration paragraph's removal sentence, the maintenance authoring payload's closeout sentence set in `agents/skills/maintenance/prompt-templates.md`, and the plans skill's Final Step section each gain exactly one prescribed gated-invocation sentence (one per home; the never-remove Rules bullet stays untouched); the plans skill's Final Step section (which today carries no removal wording - the anchor premise the r1 review corrected) gains one new removal-ordering-plus-gate sentence; basis: the origin row's prose-homes evidence for done and the authoring payload, the origin's candidate (c) for the plans skill, and the r1 fold that re-scoped the plans-skill home from amend to add.
- Plan 2 of the dispatching entry (the residue sweep) is authored after this plan lands, under the same frozen entry; basis: the entry's strictly-sequenced split and the sweep's dependency on this gate's primitive.
- The suite runs under the venv pytest runner when present (`$HOME/.agents/venvs/ai-playbook-test/bin/python3`), falling back to `python3`; basis: suite precedent in prior plan validations.

Decision points requiring a grill: none remain: the dispatching PLAN-PROMPTS entry is the confirmed design (operator-directed investigate pass with rejected alternatives recorded; live operator directive 2026-10-07); the arm adjudication the entry demands resolves to a mechanical pre-removal gate on the existing helper routed by re-pointed rule text (the landing-tail placement is rejected by the operator-directed investigate pass's recorded alternatives: the authoring side never reaches a landing-time tail; the entry's constraint sentence is the rule that rejects it); basis: the entry's constraint sentence plus the origin row's candidate list.

## Standing constraints

- Repo-relative paths only in pinned content, pins, and error messages; no machine-specific absolute paths.
- The gate-removal subcommand is born-conformant to `scripts/OUTCOME_CONTRACT.md` (per-subcommand scope, on the check-claim-fence subcommand-row precedent): one final `OUTCOME:` line per run, exit 0 pass / exit 1 fail / exit 3 tool error, the argparse usage violation overridden to exit 3; the helper's existing subcommands stay legacy plain-exit and byte-unchanged, and the contract's assumptions register gains the gate's row.
- Session-scoped git behavior (branch names, removal commands) stays session-scoped: the plans re-point sentences prescribe behavior for sessions, never for plans.

## Gist & Examples

TLDR: a mechanical gate now sits at the worktree removal point - teardown refuses while the session's review artifacts are unverified in the primary reviews home, closing the twice-witnessed silent data loss.

Example: a session that lands its plan and immediately runs `git worktree remove --force ../ai-playbook-wt-x` without migrating first now runs `worktree_closeout_migrate.py gate-removal --plan <plan> --target <primary> --worktree ../ai-playbook-wt-x` first; the gate refuses, naming `docs/history/reviews/2026-10-07-plan-review-<slug>-r1.md` (and siblings) as absent from the primary home, until `worktree_closeout_migrate.py migrate` runs; only the all-present pass prints the removal command the session then executes.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the gate's refuse path names every missing owned path; the pass path prints the removal command; both reachable in the suite fixtures
- regression value: deleting a cited record from a fixture primary home flips the gate to refuse; deleting any prescribed-invocation literal from a prose home fails the pins suite
- simplicity: one subcommand composing existing primitives; no new state, no new protocol layer

**Done when:**
- `python3 scripts/worktree_closeout_migrate.py gate-removal --plan <plan> --target <primary> --worktree <wt>` exits 1 with `OUTCOME: fail` and one line per missing owned path, and exits 0 with `OUTCOME: pass` plus the removal command when the fixture primary home holds all owned records
- the new unittest suite passes under the venv runner
- the three prose homes each carry the prescribed invocation and `bash scripts/check_maintenance_pins.sh` passes with the new section

**Ship when:**
- none; repository-verifiable only

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/worktree_closeout_migrate.py` (new `gate-removal` subcommand; existing subcommands byte-unchanged)
- `scripts/OUTCOME_CONTRACT.md` (one assumptions register row for the gate-removal subcommand)
- `agents/skills/plans/SKILL.md` (one new removal-ordering-plus-gate sentence added to the Final Step section, which carries no removal wording today)
- `agents/skills/maintenance/prompt-templates.md` (one prescribed-invocation sentence in the authoring closeout sentence set)
- `agents/skills/done/SKILL.md` (one prescribed-invocation sentence in the Step 2 migration paragraph)

**Tests:**
- `scripts/test_worktree_closeout_migrate.py` *(new section for the gate-removal arms; existing tests byte-unchanged)*
- `scripts/check_maintenance_pins.sh` *(new pins section for the three prescribed-invocation literals; existing sections byte-unchanged)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- the residue sweep of the dispatching entry (its own later plan, authored after this one lands); reason: the entry's strictly-sequenced split
- `agents/skills/execute-plan/SKILL.md` Phase 5 migration text; reason: execute-plan already enforces the ordering at its own boundary; this plan gates the in-session authoring path

## Validation Commands

Authoring-time evidence (rule 29 pre-round): the em-dash touched scan and the public-hygiene scan answered pass over the plan bytes; the pre-round structural gate answered `OUTCOME: pass`; the rule 19 RED-today probes confirmed the subcommand is absent today (`gate-removal` 0 occurrences in the helper and its suite) and the three prose homes carry no prescribed-invocation literal yet (0 matches each), so the plan's arms start RED; `bash -n` accepted the extracted Validation Commands block; the rule 22 authoring-time mechanical audit has no span-extraction object at authoring time (the plan pins no verbatim snippets; the pins section is task output), and the unlabeled mechanical run beside the rule 19 evidence covered the pins suite, the em-dash scan, and the hygiene scan over the plan bytes (all green); the rule 36 joint-direction simulation duty is carried as a Task 2 criterion because the three prose homes are existing pin targets with exactly-once count pins. Round-start state for r1: authoring worktree ai-playbook-wt-swcs, branch authoring/stale-worktree-closeout-sweep, base main d1177f70.

```bash
set -euo pipefail
REPO="$(git rev-parse --show-toplevel)"
TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"
[ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"
( cd "$REPO" && "$TEST_PY" -m pytest scripts/test_worktree_closeout_migrate.py -q )
( cd "$REPO" && bash scripts/check_maintenance_pins.sh )
( cd "$REPO" && bash scripts/check-no-em-dash.sh touched )
( cd "$REPO" && bash "${PUBLIC_HYGIENE_SCAN:-$HOME/.ai-playbook/scripts/scan-public-hygiene.sh}" )
```

### Task 1: The gate-removal subcommand and its suite

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/worktree_closeout_migrate.py` (new subcommand; existing subcommands byte-unchanged)
- `scripts/test_worktree_closeout_migrate.py` *(new section; existing tests byte-unchanged)*
- `scripts/OUTCOME_CONTRACT.md` (the gate-removal assumptions register row)

Evidence:
- `"$TEST_PY" -m pytest scripts/test_worktree_closeout_migrate.py -q`; covers every checklist criterion below

- [x] `gate-removal` reads the citations from the `--plan` file's `Plan review record:` / `Plan review:` label lines (the gate's own extraction; the whole plan body is never scanned), plus `--claims` paths, and verifies each, repo-relative, present under `--target`'s reviews home (the verify-records resolution); `--worktree` names only the worktree the sanctioned removal command removes [class: IMPLEMENTATION_REQUIRED]
- [x] Refuse arm: with any owned record absent from the target home, or with an empty owned set (no header citations and no claims), exit 1, final `OUTCOME: fail`, one line per missing path rendered repo-relative (never absolute), a claims entry outside the reviews home refused with its path, and a remedy line naming the helper's `migrate` invocation [class: IMPLEMENTATION_REQUIRED]
- [x] Pass arm: with all owned records present, exit 0, final `OUTCOME: pass`, and one line printing the sanctioned removal command for `--worktree` [class: IMPLEMENTATION_REQUIRED]
- [x] Tool-error arms: an unresolvable `--plan`, `--claims`, or `--target` (including a `--target` whose facts-resolved reviews home cannot resolve) exits 3 with `OUTCOME: tool_error`; a usage violation (argparse) is overridden to exit 3 with the same final `OUTCOME: tool_error` line [class: REPOSITORY_TEST]
- [x] The assumptions register row for the gate-removal subcommand lands in `scripts/OUTCOME_CONTRACT.md`, scoped per-subcommand on the check-claim-fence row precedent, declaring the usage override and the no-final-line rule [class: IMPLEMENTATION_REQUIRED]
- [x] Suite fixtures: a temp-dir scratch pair (worktree + primary home) exercising refuse, pass, and tool-error arms, with mktemp placement and explicit `rm -rf` teardown [class: REPOSITORY_TEST]

### Task 2: Prescribed invocation in the three prose homes plus pins

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/plans/SKILL.md` (one new removal-ordering-plus-gate sentence in the Final Step section)
- `agents/skills/maintenance/prompt-templates.md` (one sentence in the authoring closeout sentence set)
- `agents/skills/done/SKILL.md` (one sentence in the Step 2 migration paragraph)
- `scripts/check_maintenance_pins.sh` *(new section; existing sections byte-unchanged)*

Evidence:
- `bash scripts/check_maintenance_pins.sh`; covers the pins criterion below

- [x] The done skill's Step 2 migration paragraph's removal sentence gains one prescribed-invocation sentence at the existing removal wording, repo-relative literal only (one sentence per home; the never-remove Rules bullet stays untouched) [class: IMPLEMENTATION_REQUIRED]
- [x] The maintenance authoring payload's closeout sentence set gains the prescribed-invocation sentence; the sentence stays placeholder-free (angle-bracket forms only) and never duplicates a pinned count span, so the authoring-body placeholder and exact-count pins stay green [class: IMPLEMENTATION_REQUIRED]
- [x] The plans skill's Final Step section gains one new removal-ordering-plus-gate sentence (the section carries no removal wording today; the sentence adds the ordering and prescribes the gate in one sentence) [class: IMPLEMENTATION_REQUIRED]
- [x] The pins suite gains a section holding the prescribed-invocation literals (one presence pin per home), and the suite passes; before landing, the joint-direction simulation runs each edited file's complete surviving count-gate set plus the new pins against a temp copy carrying all prescribed insertions, verifying every expected count simultaneously (the rule-36 strict-superstring hazard) [class: REPOSITORY_TEST]

## Documentation Impact Assessment

- No user-facing documentation changes beyond the three skill-body sentences this plan itself edits; `README.md` catalogs skills, not helper subcommands; no doc-hierarchy surface owns helper inventories.
