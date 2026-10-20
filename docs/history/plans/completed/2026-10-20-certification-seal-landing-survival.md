# Plan: Certification seal survives the squash landing

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-07-corrections-graded-freshness-post-squash.md`
- `docs/history/backlog/2026-10-15-review-plan-seal-grammar-drift.md`
Driving force: efficiency
Plan review record: the staging series `.ai-playbook/reviews/2026-10-21-plan-review-certification-seal-landing-survival-p350a5729-r*.md` (the highest rN for this source-plan path is authoritative)
Execution budget: 3.0h total, largest task 1.5h

Authoring claim: docs/tmp/authoring-claims/2026-10-07-corrections-graded-freshness-post-squash.md (session zcode-maintenance-auth-20261020-2242-b27d4d45)

## Terms

- **Seal:** the certification seal file `.ai-playbook/review-certs/<artifact-slug>.md`, an untracked run artifact read from the working tree, never from git (`SEAL_DIR_RELPATH` in `scripts/corrections_record.py`).
- **Seal entry:** the canonical form is one `## round <N>` block carrying lowercase `key: value` lines; the parser also accepts the exact legacy prose row shape present in committed seal history. Both forms normalize to `artifact`, `round_start_commit`, `round_start_digest`, and `round_close_commit`. Plan-family entries select by numeric round and no family field or `family: plan`; code-family entries select by `family: code` and `staging_round: rN`, so matching numeric plan and code rounds remain distinct. Malformed, duplicate, ambiguous, and unsupported rows remain unresolved rather than silently degrading.
- **Anchor pair:** the seal entry's `round_start_commit` and `round_close_commit` fields.
- **Anchor leg:** the first verification leg of `verify_corrections` in `scripts/corrections_record.py`: each effective anchor must be an ancestor of the pinned verification HEAD. A plan-family anchor that is not reachable as recorded may resolve to the first-parent commit whose artifact blob re-hashes to `round_start_digest`; a code-family anchor must remain reachable as recorded. The round-start blob must re-hash to `round_start_digest`, and the effective round-start commit must not postdate the effective round-close commit.
- **Anchor-leg refusal:** the refusal `corrections verification: anchor leg refused: <detail>` the leg returns; `scripts/plan_readiness.py` surfaces it as `readiness FAILED: corrections verification: anchor leg refused: ...` with exit 1.
- **Squash landing:** the merge-lock-serialized landing that squashes an authoring or execution branch into one commit on the base branch (`scripts/land_squash.sh`), orphaning every branch commit; the anchor pair recorded before the landing then names commits no longer reachable from HEAD.
- **Byte identity:** the sha256 of the blob at the artifact path in some commit equals the seal entry's `round_start_digest`; the certified bytes themselves, independent of which commit carries them.
- **Landed anchor:** the most recent first-parent ancestor of HEAD whose blob at the artifact path has byte identity with the seal entry; the commit the anchor leg resolves a squash-orphaned anchor pair to.
- **Resolution scan:** enumerate at most `LANDED_ANCHOR_SCAN_LIMIT` commits with `git rev-list --first-parent -n <limit> HEAD`, then inspect each candidate's blob at the artifact path; the path is not passed as a revision-walk filter.
- **Verification head:** one full commit OID captured from the primary checkout's landed base tip and passed explicitly through both post-squash validators; source-worktree files and the untracked seal are still read from the source worktree, while every HEAD-dependent Git check uses this immutable OID.
- **Readiness oracle:** `python3 scripts/plan_readiness.py <plan path>`, read through the outcome contract (`scripts/OUTCOME_CONTRACT.md`): exit 0 with the final `OUTCOME: pass` line is the only pass.
- **Latest ready sidecar:** the `.stats.json` sidecar of the plan's highest review round that recorded `ready=yes`; its `source_digest` is the digest the readiness oracle compares the plan bytes against.
- **Needs-recert class:** the D1 dispatchability class in `agents/skills/maintenance/decisions.md` that keeps a plan dispatchable after an oracle failure, the execution child's PRE-STEP in `agents/skills/maintenance/template-execution.md` performing the re-certification.
- **Producer skills:** the three skills whose round-close text writes seal entries: `agents/skills/plans/SKILL.md` (review loop rule 6), `agents/skills/review-plan/SKILL.md` (the plan-family round-close seal paragraph), and `agents/skills/execute-plan/SKILL.md` (the code-family round-close seal paragraph).
- **Landing closeout:** the first bullet of `## Plan Lifecycle` in `agents/skills/plans/SKILL.md` (origin coverage, riders, prune audit, conflict discipline), the plans skill's home for what a plan landing must do.
- **Degraded grading:** the validator warning `corrections grading degraded to the exact-match digest rule` emitted when no seal entry resolves for a round.
- **Dispatching entry:** the `docs/history/backlog/PLAN-PROMPTS.md` entry `certification-seal-landing-survival` whose scope arms this plan implements (design input, distinct from the Backlog origins it cites).

## Why

Every authoring plan is certified before it lands and squash-landed after. The anchor leg was built when round commits survived landings; the 2026-10-11 re-homing of the seal to an untracked artifact and squash landing together orphan sealed anchors, so the readiness oracle refuses a byte-identical certified plan with `anchor leg refused` until a human re-anchors the seal. Four runs hit this in twelve days, the latest leaving a certified plan undispatched for a day while execution had spare mandate, and the two execution consumers lack a class for the refusal, so the plan is skipped without a mark. The verifier can resolve the same byte-identity witness mechanically.

## Gist & Examples

TLDR: resolve squash-orphaned seal anchors through the landing commit's plan bytes, verify readiness after squash landing, single-home the seal grammar in its producer skills, and route byte-identical anchor refusals through needs-recert, so certified plans survive landings without silent skips, for efficiency.

**Before (today):** a plan certified `ready=yes` at round N is squash-landed; its seal entry names two branch commits the squash orphaned. The readiness oracle refuses it with `anchor leg refused: the seal entry's round-close commit is not an ancestor of HEAD` although the landed plan bytes re-hash to the sealed digest. D1 keeps only a stale-`source_digest` failure dispatchable, so the exec lane skips the plan silently; the PRE-STEP re-certifies only that same stale-digest class. A human re-anchors both commit fields to the landing commit by hand and adds a `landing_note:` line. The three producer skills describe the seal as "one line carrying" five values while the parser reads a `## round <N>` block of `key: value` lines, so a producer writing the documented shape gets degraded grading and the round still closes as passing.

**After (this plan):** the same oracle run finds the orphaned plan anchor pair within the newest 400 first-parent commits whose plan blob re-hashes to the sealed digest, treats that landing commit as both anchors, and passes with the resolution named in its success message; a seal with no matching blob inside the bound refuses with distinct no-match or Git-plumbing evidence. Plan and code entries with the same staging round resolve to their own family. After squash landing, a warning-only readiness diagnostic and direct staging-validation pass record the plan, seal, and HEAD identities and expose degraded grading. Refusals remain actionable through needs-recert, with durable diagnostic receipts surviving origin-row closeout. The producer skills point to one parser-grammar example and name degraded grading as a round-close defect; code-family lookup uses its existing family and staging-round fields. D1 and the PRE-STEP class an anchor-leg refusal over plan bytes that re-hash to the latest ready sidecar's digest as needs-recert, so the residual case is re-certified instead of skipped.

**Edge cases:** resolution runs only for plan-family blob anchors and only after an anchor fails ancestry; an anchored pair never scans. The resolver considers at most 400 first-parent commits, including commits that do not touch the artifact, and a matching blob older than that bound routes through needs-recert. If only one anchor is orphaned, the resolved anchor still goes through the existing ordering check. Code-family seal lookup uses `family: code` plus `staging_round: rN`, allowing its header number to match a plan-family round; duplicates within the same family and staging round refuse. Correction-hop evidence commits that the squash orphaned keep their current refusal; the post-squash readiness diagnostic runs after the landing lock is released and is warning-only; the seal remains untracked, and `scripts/land_squash.sh` is unchanged.

## Outcome

A certified plan stays certified after it lands, without a human touching its seal.

- The readiness oracle passes a squash-landed plan whose sealed bytes it can find in one immutable verification context's first-parent history; missing anchor objects may scan, while malformed ids and other Git plumbing failures refuse distinctly. Canonical block entries and recognized legacy prose rows both resolve; ambiguous or malformed rows do not.
- The seal grammar the producer skills document is the grammar the parser reads, plan and code entries sharing a staging round resolve by family, and degraded grading is a defect at round close.
- The exec lane dispatches a byte-identical certified plan whose oracle run refuses on the anchor leg through the needs-recert class instead of skipping it.
- After squash landing, a warning-only readiness diagnostic and direct staging-validation pass record stable HEAD, plan, and seal identities; the validator exposes degraded grading, and refusals stay actionable through needs-recert without a closeout blocker.

Gate delta: the anchor leg accepts byte-identical squash-orphaned plan anchors through a 400-commit first-parent scan; one verification context pins every HEAD-dependent leg; seal lookup distinguishes plan and code family rounds and reads validated legacy rows; a warning-only diagnostic records landed-byte behavior. The gate-liveness ledger currently reports 28 catches to 41 incidents. This removes manual seal re-anchoring and adds no validator, lock, state field, seal field, or blocker class; byte mismatch, missing path, pinned snapshot, malformed id, and non-missing Git-plumbing failures remain distinct.

## Assumptions

- assume the landing-witness shape is ancestry resolution by byte identity through HEAD's first-parent history (the landed anchor), not a seal field the landing writes; basis: a written field cannot satisfy `is_ancestor` over the two hard-coded anchor fields (the `exec-review-records-at-round-close` seal still refuses with both anchors recorded), 37 existing seals carry no such field and the primary-checkout `land` class has no worktree seal to write into, while `verify_corrections` already holds `blob_bytes`, `is_ancestor`, and `sha256_hex`, so the scan needs no new producer data; rejected twin: a `landing_commit:` field written by `scripts/land_squash.sh` between its post-landing parentage gate and `emit_outcome pass`, which would still require this plan's leg change, miss every seal whose landing did not run the write, and add an idempotency duty under the helper's keep-the-landing arm.
- assume byte identity stays inside the graded binding's declared threat model; basis: `docs/history/plans/completed/2026-10-04-review-cert-graded-binding.md` accepts the certifying session minting its own seal as the trust boundary and defends post-hoc tampering through re-derivation from git, which the landed anchor preserves (the sealed digest must be carried by a reachable commit at the artifact path, and the round-start re-hash leg still runs over the resolved commit).
- assume the resolution scan enumerates at most 400 first-parent commits total, newest first, regardless of whether each touches the artifact; basis: a path-limited rev-list does not bound commits traversed, and the residual beyond 400 routes through needs-recert rather than a silent skip.
- assume the retirement record in the `scripts/corrections_record.py` module docstring (the committed-history seal witness retired 2026-10-11) is not reopened: the landed anchor reads the on-disk seal and git blobs only, never committed seal text; basis: that docstring's Retirement record and `seal_text`'s working-tree-only read.
- assume seal selection uses the parsed block number for plan-family entries and the existing `family: code` plus `staging_round: rN` fields for code-family entries; basis: the 2026-10-20 witness in the second origin records the collision, while this discriminator reuses fields already written by the code-family producer; rejected twin: continue the numeric header sequence across families, which leaves code entries undiscoverable by their staging round.
- assume the readiness and staging validators gain an optional explicit verification-head input, defaulting to their existing `HEAD` behavior: the post-squash diagnostic must verify the landed primary tip while reading source-worktree files, and the current hermetic Git environment intentionally strips inherited `GIT_*` overrides; basis: `corrections_record.hermetic_git_env()` removes those variables, so Git-dir/worktree environment overrides cannot establish the intended context through validator calls.
- assume lesson 141 in `docs/maintenance/development_lessons.md` (the manual re-anchor with a `landing_note:` line) is history and stays as written; basis: lessons are the incident dossier under the repository guidelines' anti-growth rules, and the verifier replaces the manual remedy while the warning-only post-squash diagnostic records behavior.
- assume the post-squash readiness diagnostic remains warning-only until a true catch by that diagnostic, a same-change blocker retirement, and the required pre-registered removal record support promotion; basis: AGENTS.md Machinery admission protocol forbids new blockers before those conditions. The origin records five historical post-squash refusals, but none is a catch by this new invocation. Review date: 2026-11-21; false-positive cost is seven prescribed Git/validator command invocations, six identity snapshots of four values each, and one receipt. Task 2 replaces the dispatching entry's still-active landing-witness arm with byte-identity resolution and this warning-only diagnostic.
- assume fix-class origin `docs/history/backlog/2026-10-15-review-plan-seal-grammar-drift.md` requires degraded seal grading to remain a closeout defect. Three exits were considered: a sanctioned override (rejected because it certifies without a resolvable seal), removing known false positives (adopted through strict legacy-row parsing and canonical grammar), and warning-only seal grading (rejected because it recreates the witnessed silent pass). This applies to certification grading; the separate post-landing diagnostic remains warning-only under Machinery admission.
- assume the `maintenance` authoring blueprint (`agents/skills/maintenance/template-authoring.md`) is not edited: its coverage-gate and rider sentences name the plans lifecycle as the procedure of record, which owns the warning-only post-squash readiness diagnostic.

Decision points requiring a grill: none remain.

## Standing constraints

- Land the rule, not the story: no edited home carries witness dates, incident narrative, or run names; the Backlog origins hold the story.
- Each skill-text arm is one sentence (review-plan: one sentence plus the worked example and one degraded-grading sentence) inside its existing paragraph; no new section, field paragraph, pin, or validator mode.
- Fail closed: every new refusal names the orphaned anchor and the missing byte identity; a plumbing failure during the scan refuses, never passes.
- The seal file gains no field and keeps its untracked home.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the four fixture arms hold (post-squash accept on byte identity, byte-mismatch refusal naming both facts, pre-landing path unchanged, moved-anchor re-hash refusal preserved), the resolver readiness twins hold (exit 0 `OUTCOME: pass` over a squash-landed seal; exit 1 `anchor leg refused` over one without byte identity), code-family hop ancestry remains intact, and Plan Lifecycle follows Task 2's receipt outcome matrix, proves the verification HEAD is the landed primary tip while reading source-worktree files, records both orphaned anchors as non-ancestors, and keeps all non-pass outcomes warning-only.
- faithfulness: Task 2 replaces the dispatching entry's landing-witness producer-complement arm with the selected byte-identity resolution and warning-only diagnostic; Task 1 matches the first Backlog origin's unorphaning Fix shape; the second origin's Expected (grammar with a worked example, degraded grading a defect) is met in the review-plan paragraph. Acceptance criteria and validation compare the same landing-context proof, ordered receipt destinations, and warning states.
- readability: every plan-specific term used from Why through Evaluation Criteria resolves in Terms; the prescribed skill sentences read as prose, not as a changelog.
- text discipline: review-plan owns one valid grammar example; sibling skills point to it and add only family-specific guidance; each edited skill file pays for byte growth.

**Done when:**
- `python3 scripts/test_corrections_record.py` and `python3 scripts/test_plan_readiness.py` exit 0 with the prescribed test names present, and every command in the Validation Commands list exits 0.
- a hermetic scratch repository whose seal anchors are parentless commits and whose pinned HEAD carries the sealed plan bytes passes; a mismatching digest or 401-commit fixture with no in-bound match refuses as no-match, while injected enumeration and candidate-read failures produce distinct plumbing refusals.
- plan and code seal blocks with the same staging number resolve to their own family in corrections verification and review-staging validation, and the worked example passes the parser's required-field and hex-width checks.
- readiness-level fixtures clear inherited Git repository overrides for the duration of the scratch-repository call; review-staging validation resolves same-number plan and code entries by the parsed family.
- the existing suites prove preserved behavior, the stale grammar clause is absent from every producer skill, and review-plan contains the canonical grammar example.
- the post-squash diagnostic proves the primary checkout HEAD is used with source-worktree files, both seal anchors are not ancestors of that HEAD, and each matrix outcome is recorded at its prescribed destination.
- `bash scripts/check-no-em-dash.sh touched`, `bash scripts/scan-public-hygiene.sh`, and `bash scripts/check_maintenance_pins.sh` exit 0 (the pins suite recorded zero `PIN FAIL` lines at main d2426ba81 on 2026-10-20, so no baseline failure is tolerated).

**Ship when:**
- the post-squash commands use one immutable landed verification OID and the reconciled source worktree, their outputs match Task 2's receipt outcome matrix, and the receipt-matrix rows are exercised against the observed landing of this plan. Every receipt carries the repo-relative plan and review paths, the landing-context proof commands and both prescribed validator command strings (a skipped staging-validator invocation is marked `not run`, never represented as executed), outcome states, warning state, and before/after identities. The named primary, fallback, or transcript destination matches the matrix; maintenance recovers transcript reports before sunset. Persistence failures and diagnostic warnings remain non-blocking.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/corrections_record.py` (family-aware `load_seal_entry`, one immutable verifier context across every HEAD-dependent leg, bounded `resolve_landed_anchor`, missing-anchor classification, candidate blob-read handling, the `LANDED_ANCHOR_SCAN_LIMIT` constant, and success message tail; unrelated functions stay frozen)
- `scripts/validate_review_staging.py` (pass its parsed family to `load_seal_entry` in corrections grading and thread optional `--verification-head` through plan-family corrections verification; every other path is frozen)
- `scripts/plan_readiness.py` (add optional `--verification-head` and thread it through plan corrections context; omission preserves existing `HEAD` behavior)

**Tests:**
- `scripts/test_corrections_record.py`
- `scripts/test_plan_readiness.py` (explicit verification-head CLI/context behavior)
- `scripts/validate_review_staging.py --selftest` (staging-validator CLI/context behavior)

**Documentation:**
- `docs/history/backlog/PLAN-PROMPTS.md` (replace the dispatching entry's superseded landing-witness producer-complement arm)
- `docs/history/backlog/2026-10-07-corrections-graded-freshness-post-squash.md` (durable diagnostic witness instructions only)
- `docs/history/certification-seal-landing-diagnostics.md` (append-only post-closeout diagnostic receipts)
- `docs/history/certification-seal-landing-diagnostic-write-failures.md` (append-only fallback receipts when the primary ledger append fails)
- `docs/history/backlog/2026-10-15-review-plan-seal-grammar-drift.md` (fix-class no-exit rationale)
- `agents/skills/plans/SKILL.md` (review loop rule 6 and Plan Lifecycle landing closeout clauses only; every other line is frozen)
- `agents/skills/review-plan/SKILL.md` (the plan-family round-close seal paragraph and its worked example only)
- `agents/skills/execute-plan/SKILL.md` (the code-family round-close seal paragraph's grammar clause only)
- `agents/skills/maintenance/decisions.md` (the D1 needs-recert sentence only)
- `agents/skills/maintenance/template-execution.md` (the PRE-STEP stale-digest sentence only)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/land_squash.sh`; reason: the landing-written seal field is the rejected twin of the landing-witness decision (Assumptions); the post-squash readiness check stays in the plans lifecycle.
- `scripts/check_maintenance_pins.sh`; reason: it remains an existing repository gate; the plan does not edit its configuration.
- `agents/skills/maintenance/template-authoring.md`; reason: it already delegates landing closeout to the plans lifecycle (Assumptions).
- `docs/maintenance/development_lessons.md`; reason: lesson 141 is history (Assumptions).
- the seal files under `.ai-playbook/review-certs/`; reason: untracked run artifacts the validator reads; this plan writes no field into them and re-anchors none by hand.

## Validation Commands

Run the relevant focused suites and existing repository gates from the repository root:

- `python3 scripts/test_corrections_record.py`
- `python3 scripts/test_plan_readiness.py`
- `python3 scripts/validate_review_staging.py --selftest`
- `python3 scripts/machinery_inventory.py --check`
- `bash scripts/check-no-em-dash.sh touched`
- `bash scripts/scan-public-hygiene.sh`
- `bash scripts/check_maintenance_pins.sh touched`

The focused suites cover the new resolver, missing-anchor handling, legacy and block seal parsing, family collisions, one-snapshot verification, producer grammar, and needs-recert routing. Verify the warning-only lifecycle procedure by running its prescribed post-squash commands and comparing the receipt with Task 2's outcome matrix, observed command outputs, warning state, identities, and selected persistence destination. Exercise each matrix row. Do not add a bespoke shell validator for this plan.

### Task 1: Resolve a squash-orphaned anchor pair by byte identity

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/corrections_record.py`
- `scripts/validate_review_staging.py`
- `scripts/plan_readiness.py`
- `scripts/test_corrections_record.py`
- `scripts/test_plan_readiness.py`

Primary class anchors:
- `SealEntry` in `scripts/corrections_record.py`
- `ValidationResult` in `scripts/validate_review_staging.py`
- `AnchorLegTest` in `scripts/test_corrections_record.py`

Prescribed constant (add verbatim directly below the `SEAL_FIELD_RE` assignment among the grammar constants):

```
LANDED_ANCHOR_SCAN_LIMIT = 400
```

Prescribed family-aware selector change in `load_seal_entry`:
- In `_run_graded_stale_arm` in `scripts/validate_review_staging.py`, pass the parsed family to `verify_corrections` (replace the current hard-coded `"plan"` argument) and to `cr.load_seal_entry`. Do not route family selection through `validate_corrections_extension`, which is schema-only. Add the family argument to `load_seal_entry`. Parse the committed legacy one-line seal rows using an anchored grammar derived from the on-disk corpus; normalize recognized fields into the same entry model as block records. Preserve the existing integrity and ancestry checks for both forms; malformed or duplicate rows refuse, and no silent exact-digest fallback may treat an unparsed committed seal as valid.
- For FAMILY_PLAN, match the numeric ## round N header and accept only entries with no family field or family: plan.
- For FAMILY_CODE, match family: code and staging_round: rN; do not select by the block number alone. Exactly one matching entry is required; zero or multiple matches remain unresolvable. This permits plan and code entries for the same staging number to coexist. The review-staging caller passes its parsed family too.

Prescribed verifier snapshot contract: at the start of `verify_corrections`, resolve the supplied `head` exactly once into the normalized full local `head_sha`; when a CLI caller supplies `--verification-head`, validate it as a full commit OID present in the source repository and pass it as `head`. The anchor block below consumes that local, and every correction-hop ancestry check, code-family terminal comparison, and first-parent resolver scan receives the same value. No callee in that verification run may resolve symbolic `HEAD` again. `plan_readiness.py` adds optional `--verification-head` and carries it in `_plan_corrections_context`; `validate_review_staging.py` adds the same optional argument and passes the context's head through `_run_graded_stale_arm`. When omitted, both commands keep their current `HEAD` behavior. Before ancestry, validate each recorded anchor with `HEX40_RE` and classify its object through a helper using `run_git`/`git cat-file`: return `present` only for a commit object, `missing` only for a conclusive absent-object result, and `error` for malformed ids, wrong object types, or any other Git failure. A confirmed missing plan-family commit follows the same bounded byte-identity resolver as an unreachable anchor; missing code-family commits preserve the existing not-an-ancestor refusal. Never convert an ambiguous plumbing error to `missing`. Enumerate at most `limit` first-parent commits without a path filter. For each candidate, distinguish a path absent from that tree from an `ls-tree` or blob-object read failure; absence is a non-match, while every Git plumbing failure returns a distinct `scan_error` and refuses the check.

```
def resolve_landed_anchor(repo, artifact_path, digest, head_sha,
                          limit=LANDED_ANCHOR_SCAN_LIMIT):
    """Return (anchor, scan_error) using the caller's pinned HEAD id."""
    text = git_text(repo, "rev-list", "--first-parent", "-n", str(limit),
                    head_sha)
    if text is None:
        return None, "git plumbing failed while enumerating first-parent history"
    for commit in text.split():
        candidate, read_error = tree_blob_bytes(repo, commit, artifact_path)
        if read_error is not None:
            return None, read_error
        if candidate is not None and sha256_hex(candidate) == digest:
            return commit, None
    return None, None
```

Prescribed anchor-leg replacement in `verify_corrections`: pass `family` to `load_seal_entry`; for an orphaned code-family anchor preserve the existing not-an-ancestor refusal without invoking the plan-blob resolver. For plan-family anchors, replace the span from the comment line `# Anchor: the entry's commits must be reachable and its bytes` through the line `start_commit = entry.fields["round_start_commit"]` with the lines below, verbatim):

```
    # Anchor: the entry's commits must be reachable and its bytes
    # re-derive to the round-start digest from git. A plan-family anchor
    # the squash landing orphaned resolves through the first-parent
    # ancestor whose plan blob carries the sealed bytes (byte identity,
    # never the recorded sha); a moved anchor without byte identity
    # still refuses.
    anchors = dict((key, entry.fields[key])
                   for key in ("round_close_commit", "round_start_commit"))
    landed_anchor = None
    for key in ("round_close_commit", "round_start_commit"):
        object_state = commit_object_status(srepo, anchors[key])
        if object_state == "error":
            return False, leg_reason("anchor", "Git cannot classify commit object %s" % anchors[key])
        if object_state == "missing":
            anchored = False
        else:
            anchored = is_ancestor(srepo, anchors[key], descendant=head_sha)
            if anchored is None:
                return False, leg_reason(
                    "anchor", "git plumbing failed over %s" % anchors[key])
        if anchored is False:
            if family == FAMILY_CODE:
                return False, leg_reason(
                    "anchor", "the seal entry's %s is not an ancestor of HEAD"
                    % _ANCHOR_COMMIT_LABELS[key])
            scan_error = None
            if landed_anchor is None and family == FAMILY_PLAN:
                landed_anchor, scan_error = resolve_landed_anchor(
                    srepo, artifact_path,
                    entry.fields["round_start_digest"], head_sha)
            if scan_error is not None:
                return False, leg_reason("anchor", scan_error)
            if landed_anchor is None:
                return False, leg_reason(
                    "anchor", "the seal entry's %s is not an ancestor of HEAD "
                    "and no first-parent ancestor carries the sealed "
                    "round-start bytes at %s"
                    % (_ANCHOR_COMMIT_LABELS[key], artifact_path))
            anchors[key] = landed_anchor
    start_commit = anchors["round_start_commit"]
```

Prescribed follow-on edits inside `verify_corrections`: checks whose descendant is the verification snapshot pass `descendant=head_sha`, including anchor and plan-family evidence-commit ancestry; preserve the code-family row-local check `is_ancestor(repo, row["after_base"], row["after_head"])`, which proves hop continuity rather than reachability to HEAD, and add a fixture where an intermediate after-head does not descend from its after-base. Code-family terminal validation compares its `after_head` with the same pinned `head_sha` instead of resolving `head` again; the seal-integrity dating line `close_date = commit_date(srepo, entry.fields["round_close_commit"])` reads `anchors["round_close_commit"]` instead, and every later read of the round-close commit in the function (the hop-dating leg) reads that same `anchors` value, so a resolved pair is one commit for every leg; the success return becomes a `verified` string built from the existing format and, only when `landed_anchor` is not None, extended with the suffix `; squash-orphaned seal anchors resolved through HEAD-ancestor <sha>` (the literal `squash-orphaned seal anchors resolved through HEAD-ancestor` followed by a space and the resolved commit).

Prescribed fixture arms in `scripts/test_corrections_record.py`, class `AnchorLegTest` (the module's `plan_fixture`, `orphan_commit`, `plan_row`, `vplan`, and `assert_refusal` helpers are the building blocks; the suite's existing cases are the regression floor):
- Add legacy-row fixtures for every recognized on-disk row shape. Assert parsed fields normalize to the canonical entry model; malformed rows, duplicate same-family rows, ambiguous abbreviated commit identifiers, and unsupported shapes remain unresolvable. This preserves the producer/backlog contract without rewriting seal artifacts.
- Add `test_load_seal_entry_distinguishes_plan_and_code_rounds`: write plan-family and code-family blocks with the same numeric header and `staging_round: r2`; assert both lookups return their own entries and a duplicate code block stays unresolvable. Add a verifier case proving an orphaned code-family anchor refuses despite a matching plan blob in HEAD history. Add a review-staging self-test assertion labelled `review-staging resolves code family by staging_round`, proving its caller passes `family: code` and resolves a colliding code entry.
- Add test_resolution_scan_caps_history: create a scratch repository with the sealed plan blob followed by 401 first-parent commits whose trees omit or change the artifact path; assert the scan returns no anchor and enumerates at most 400 commits.
- Add `test_resolution_scan_includes_candidate_400`: place the only matching blob at candidate 400 and assert it resolves. Add `test_resolution_scan_plumbing_failure_refuses`: force the first-parent enumeration command to fail and assert the distinct Git-plumbing refusal. Add a separate candidate-read failure fixture where `ls-tree` identifies the path but `cat-file` cannot read its blob; assert refusal without accepting an older match. Add a verification-context fixture asserting anchor checks, hop ancestry, code-family terminal comparison, and the resolver scan all receive the same resolved HEAD commit id.
- Add a present non-commit object and an injected ambiguous commit-object probe failure; both refuse without scanning. Add a full-format absent commit id and verify only confirmed absence reaches matching plan bytes.
- Preserve the code-family `after_base` to `after_head` ancestry relation with a regression fixture whose intermediate after-head does not descend from its after-base.
- Re-key the existing orphaned-round-close case inside test_seal_recorded_anchor (the case commented `A seal entry whose round-close commit is not an ancestor of HEAD.`) to the no-byte-identity shape: the seal entry's `round_start_digest` becomes `hx(D3)` (bytes no first-parent commit carries at `PLAN_REL`) with the round-close commit an `orphan_commit`, and the assertion becomes `assert_refusal(self, msg, "anchor", "round-close commit", "no first-parent ancestor")`.
- Add `test_squash_orphaned_anchors_resolve_by_byte_identity`: a `plan_fixture` whose seal entry is rewritten with both anchors as two distinct `orphan_commit` results and `round_start_digest` `hx(D1)`; `vplan` over the fixture's hop row passes, the message contains `squash-orphaned seal anchors resolved through HEAD-ancestor` followed by the fixture's `entry` commit (the most recent first-parent commit carrying `D1` at `PLAN_REL` before the D2 hop), and the zero-hop clean shape (`vplan(repo, [], hx(D1), D1)`) passes over the same seal.
- Add `test_single_orphaned_round_start_resolves_before_reachable_round_close`: orphan only `round_start_commit`; keep `round_close_commit` reachable; place the first matching plan blob after the reachable close commit; require resolution to that blob and refusal with `round-start commit postdates round-close`.
- Leave the moved-anchor re-hash case (anchors reachable, blob mismatch, `assert_refusal(..., "anchor", "re-hash")`) and every passing case byte-identical: they are the pre-landing path and the moved-anchor refusal this plan preserves.

Prescribed readiness-level twins in `scripts/test_plan_readiness.py`, beside the corrections selftest class that builds `_graded_fixture` and drives `_run_gate`:
- `test_squash_orphaned_seal_anchors_pass_the_gate`: build the graded fixture, rewrite its seal entry's two anchor fields to parentless commits minted from HEAD's tree (`git commit-tree` with no parent, the `orphan_commit` shape), keep the sealed digest and the plan bytes unchanged, run the gate, and expect exit 0 with the final `OUTCOME: pass` line.
- `test_squash_orphaned_seal_without_byte_identity_refuses`: the same rewrite with the seal entry's `round_start_digest` replaced by the sha256 of bytes no commit carries at the plan path; expect exit 1, `OUTCOME: fail`, and stderr carrying `anchor leg refused` and `no first-parent ancestor`.
- `test_readiness_fixture_clears_git_overrides`: inject an inherited repository override, invoke the readiness fixture, and verify it still evaluates the scratch repository before restoring the environment.
- Add an explicit-OID fixture whose verification commit differs from source-worktree `HEAD`; keep the untracked seal only in the source worktree and assert every Git-dependent corrections check receives the explicit OID while the plan and seal are read from the source-worktree paths. Make the plan bytes agree with the sealed bytes in the verification commit so the post-squash path can pass.
- Assert omitting `--verification-head` retains the existing source-worktree `HEAD` behavior. Reject abbreviated and malformed values and a full-width OID that is unavailable as a commit before corrections verification runs.
- Add matching `validate_review_staging.py --selftest` cases for the explicit verification-head, distinct source-worktree `HEAD`, omitted-option, and invalid-value behavior; keep `validate_corrections_extension` schema-only.
- `test_seal_example_loads`: read the five-line plan-family example from `review-plan/SKILL.md`, assert `parse_seal` yields one entry, and assert `load_seal_entry` accepts its valid field widths.
- Run these readiness fixtures with a controlled Git environment that clears inherited `GIT_*` repository overrides and restores the prior environment after each call; assert an inherited override cannot redirect the fixture away from its scratch repository.

- [x] Add optional `--verification-head` to both validators, thread it through `_plan_corrections_context` and `_run_graded_stale_arm`, and preserve current behavior when omitted; validate an explicit value as a full commit OID present in the source repository. [class: IMPLEMENTATION_REQUIRED]
- [x] Assign `scripts/plan_readiness.py` to this task's Files list and Task 1 CLI/context tests; Task 2 consumes this completed option and does not own a second implementation. [class: IMPLEMENTATION_REQUIRED]
- [x] Resolve the supplied `head` once to local `head_sha` at function entry; add the prescribed constant and helper; make `load_seal_entry` family-aware; pass the parsed family from `_run_graded_stale_arm` to `verify_corrections` and `cr.load_seal_entry`; keep `validate_corrections_extension` schema-only. [class: IMPLEMENTATION_REQUIRED]
- [x] Apply the prescribed anchor replacement and follow-on edits; every HEAD-dependent leg consumes local `head_sha`. Preserve unrelated semantics and existing refusal class and wording for malformed ids and non-missing plumbing failures. [class: IMPLEMENTATION_REQUIRED]
- [x] Preserve the existing code-family refusal, `the seal entry's <anchor> is not an ancestor of HEAD`, and never call the plan-blob resolver for code-family anchors. [class: IMPLEMENTATION_REQUIRED]
- [x] Land missing-anchor, anchor, family-collision, candidate-400 success, 401-candidate no-match, and scan-failure fixtures in `scripts/test_corrections_record.py`, plus readiness twins and the hermetic-environment case in `scripts/test_plan_readiness.py`; run both suites and expect exit 0. [class: REPOSITORY_TEST]
- [x] Run the corrections-record and plan-readiness suites; expect exit 0 with the legacy-row, pinned-HEAD, bounded-scan, candidate-read failure, and readiness fixtures passing. [class: REPOSITORY_TEST]
- [x] Commit: `corrections: resolve a squash-orphaned seal anchor pair through the landing commit's plan bytes`. [class: IMPLEMENTATION_REQUIRED]

### Task 2: Run a warning-only post-landing certification diagnostic

Context surface: the plan's Terms, this task, and the first Backlog origin's producer-complement arm.

Files:
- `agents/skills/plans/SKILL.md`
- `scripts/validate_review_staging.py` (read-only diagnostic invocation; Task 1 owns its verification-head implementation)
- `docs/history/backlog/PLAN-PROMPTS.md`
- `docs/history/backlog/2026-10-07-corrections-graded-freshness-post-squash.md` (origin evidence and receipt-ledger pointer)
- `docs/history/certification-seal-landing-diagnostics.md` *(new; primary-checkout tracked receipt home)*
- `docs/history/certification-seal-landing-diagnostic-write-failures.md` *(new; one-shot tracked fallback when the primary receipt append fails)*
- the `certification-seal-landing-survival` dispatching entry

Prescribed lifecycle diagnostic: after squash, lock release, and post-landing worktree reconciliation, capture the primary checkout's landed base tip once as a full commit OID with `git -C <primary-checkout> rev-parse --verify HEAD^{commit}` and the reconciled source worktree's own tip with `git -C <source-worktree> rev-parse --verify HEAD^{commit}`. Confirm the primary OID is readable in the source repository with `git -C <source-worktree> cat-file -e <verification-oid>^{commit}`, then read both original anchor ids from the untracked seal and run `git -C <source-worktree> merge-base --is-ancestor <anchor> <verification-oid>` for each; both must exit 1, proving the source branch anchors are not ancestors of the verification head. If any context check fails or is inconclusive, do not run readiness or staging validation; record that outcome as inconclusive. With context established, run `python3 scripts/plan_readiness.py --verification-head <verification-oid> <repo-relative plan path>` and, only after readiness passes, `python3 scripts/validate_review_staging.py --verification-head <same verification-oid> --hard <highest ready review record for this plan> --source-plan <repo-relative plan path>`. Both validators read plan and seal files from the source worktree while all HEAD-dependent checks use the same explicit immutable OID; do not use `GIT_DIR` or `GIT_WORK_TREE` overrides. The diagnostic assumes its source-worktree owner performs no ref, plan, or seal writes from the first identity snapshot through receipt creation; this operator sequencing constraint adds no lock, and if another writer cannot be excluded, skip both validators and record an inconclusive context outcome. Capture and compare the landed OID, source-worktree HEAD, plan-byte digest, and seal-byte digest immediately before and after each validator call and at the full diagnostic boundaries; any identity change or absent seal makes the result inconclusive. The staging validator's stderr exposes any `corrections grading degraded` warning. Append each serialized receipt with one `O_APPEND` write, verify the complete receipt bytes, and treat a partial or mismatched write as an append failure under the matrix; do not add a lock or blocking condition. Use this single receipt outcome matrix for every result:

| Condition | Readiness / staging validator | Degraded-grading warning | Receipt destination |
|---|---|---|---|
| Landing-context proof fails or is inconclusive | Neither command runs; record the failed or inconclusive context check and reason. | `not_observed`. | Append receipt to `docs/history/certification-seal-landing-diagnostics.md` in the primary checkout. |
| Landing context is established, readiness passes, and its post-call identities match | Record actual staging-validator invocation, exit code, and final `OUTCOME` line. | `present` or `absent`, from observed stderr. | Append receipt to `docs/history/certification-seal-landing-diagnostics.md` in the primary checkout. |
| Identities differ after readiness or at staging pre-call, so staging validation is skipped | Record the readiness command and result, the staging-validator command string as planned and marked `not run`, and the identity mismatch reason; null/not-applicable staging exit and outcome values. | `not_observed`. | Append receipt to the primary ledger; classify the diagnostic as inconclusive. |
| Readiness identities match and readiness does not pass | Record the prescribed staging-validator command string as the planned invocation marked `not run`, the readiness result as reason, and null/not-applicable exit and outcome values. | `not_observed`. | Append receipt to the primary ledger. |
| Staging validation ran but its post-call identities differ | Record both actual validator invocations and results, plus the identity mismatch; classify the full diagnostic as inconclusive. | `present` or `absent`, from observed stderr. | Append receipt to the primary ledger. |
| Primary-ledger append fails | Preserve the same serialized receipt and record the primary-write error. | Keep the value from the applicable row above. | Append once to `docs/history/certification-seal-landing-diagnostic-write-failures.md` in the primary checkout. |
| Both tracked appends fail | Preserve the same serialized receipt and both write errors; classify persistence as inconclusive. | Keep the value from the applicable row above. | Emit to the running maintenance session transcript; the next maintenance sunset review copies unresolved reports into the fallback ledger before deciding whether no catch occurred. |

Every receipt carries the repo-relative plan path and highest ready review-record path, all landing-context proof command strings and results, both prescribed validator command strings, each validator command's result or not-run state and reason, the warning value from the matrix, and before/after landed OID, source-worktree HEAD, plan-byte, and seal-byte identities for each validator call and the full diagnostic. When context proof fails or another writer cannot be excluded, mark both validators `not run`; when readiness identities differ, record staging as planned and `not run`; never present an unrun command as executed. Confirm only when the landed OID and source-worktree checks pass, both original anchors are not ancestors of that OID, the source-worktree no-write interval holds, every validator's surrounding identity snapshots match, both validators ran, both exited 0, each ended with `OUTCOME: pass`, and the staging validator emitted no degraded-grading warning. Exercise identity drift between validators and after staging validation and verify each receipt outcome. A receipt in either tracked ledger keeps both files and links. Every warning or inconclusive outcome remains warning-only: report it and leave needs-recert actionable for maintenance. Do not add a closeout condition, runtime branch, or retry loop.

Machinery admission: this diagnostic starts warning-only and adds no blocking condition. Expected frequency is one per affected landing while seals point at pre-squash tips, then on regression; false-positive cost is seven prescribed Git/validator command invocations, six identity snapshots of four values each, and one receipt. Review date: 2026-11-21. If no true catch is recorded by that date, remove the diagnostic instruction from Plan Lifecycle and its PLAN-PROMPTS clause in the same change. Remove both receipt files and their origin and dispatch-entry links only when neither tracked file has a receipt; retain both files and links when either has any receipt, including confirmed passes. If both tracked appends fail, the running maintenance session retains the transcript and the next maintenance sunset review owns recovery from that transcript into the fallback ledger before deciding whether no catch occurred. A receipt-storage failure does not block plan closeout or promote the diagnostic. If a diagnostic catch is recorded, the diagnostic remains warning-only; promotion requires a separate change that retires an existing blocker and has a pre-registered registry-removal record. The original backlog row links to both receipt files so evidence survives origin-row closeout.

- [x] Update Plan Lifecycle with the landed-HEAD/source-worktree context proof, both orphan-anchor non-ancestor checks, both diagnostic commands, stable before/after HEAD, plan, and seal identities, the validator's observable degraded-grading signal, and warning-only refusal handling. [class: IMPLEMENTATION_REQUIRED]
- [x] Create both append-only tracked receipt files and link them from the origin backlog and dispatching PLAN-PROMPTS entry. Implement ordered append and transcript recovery exactly as defined by the Task 2 receipt matrix; the matrix is the only source for branch behavior. [class: IMPLEMENTATION_REQUIRED]
- [x] Update the dispatching entry Machinery admission to seven prescribed Git/validator command invocations, six identity snapshots of four values each, and one receipt; preserve its warning-only status and existing removal simplification. [class: IMPLEMENTATION_REQUIRED]
- [x] Add no runtime closeout branch, registry edit, or completion blocker. [class: IMPLEMENTATION_REQUIRED]
- [x] Replace the dispatching entry's producer-complement arm: the verifier resolves squash-orphaned plan anchors through HEAD's first-parent plan bytes; the landing writes no seal field and does no readiness rerun. Align its Machinery admission with the warning-only tracked receipt ledgers, naming both incident origins, expected frequency, false-positive cost, sunset, and the existing refusal simplification. [class: IMPLEMENTATION_REQUIRED]
- [x] State that after lock release and worktree reconciliation, the plans lifecycle runs the warning-only readiness and staging diagnostic, records receipts, and leaves refusals actionable through needs-recert without blocking closeout. [class: IMPLEMENTATION_REQUIRED]
- [x] Retain the historical landing-witness requirement and evidence in the origin backlog. [class: IMPLEMENTATION_REQUIRED]
- [x] Record before/after byte counts and delete equivalent redundant operative bytes in `agents/skills/plans/SKILL.md` while preserving its landing contract. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `plans: verify certification after squash landing` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Single-home the seal grammar in the three producer skills

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `docs/history/backlog/2026-10-15-review-plan-seal-grammar-drift.md` (the fix-class no-exit analysis)
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`

Prescribed replacement in `agents/skills/plans/SKILL.md` (review loop rule 6; replace the clause `one line carrying the round, the artifact path, the round-start commit and digest, and the round-close commit.` with the line below, verbatim, in place):

```
the seal block grammar and plan-family example documented in the review-plan skill.
```

Prescribed replacement in `agents/skills/review-plan/SKILL.md` (the plan-family round-close seal paragraph; replace the clause `one line carrying the round, the artifact path, the round-start commit and digest, and the round-close commit.` with the first line below, verbatim, in place, and append the second line below as the paragraph's final sentence after `beside which this duty sits.`, separated by one space):

```
a `## round <N>` block carrying the lowercase `key: value` lines `parse_seal` and `load_seal_entry` in `scripts/corrections_record.py` read (`artifact:`, `round_start_commit:`, `round_start_digest:`, `round_close_commit:`; other lowercase fields are tolerated), with the plan-family example below.
```

```
A certification whose grading degraded to the exact-match digest rule for want of a resolvable seal entry (the validator's `corrections grading degraded` warning) is a round-close defect to fix before closeout, never a passing round.
```

Prescribed worked example in `agents/skills/review-plan/SKILL.md` (insert directly after the paragraph above, preceded by one blank line: a fenced code block (three backticks on their own lines, no language tag) wrapping exactly the five lines below, followed by one blank line before the next existing paragraph):

```
## round 1
artifact: docs/history/plans/2026-10-20-example-plan.md
round_start_commit: 1111111111111111111111111111111111111111
round_start_digest: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
round_close_commit: 2222222222222222222222222222222222222222
```

Prescribed replacement in `agents/skills/execute-plan/SKILL.md` (the code-family round-close seal paragraph; replace the clause `one line carrying the round, the artifact path, the round-start commit and digest, the round-close commit, and the certified range with the regenerated diff digest.` with the line below, verbatim, in place):

```
the seal block grammar and plan-family example documented in the review-plan skill. Code-family entries carry `family: code`, `staging_round: rN`, and the certified range as `reviewed_base:`, `reviewed_head:`, and `range_digest:`; lookup uses family and staging round.
```

- [x] Confirm the origin records why sanctioned override and warning-only are rejected and strict legacy compatibility is the false-positive remedy; apply the three prescribed replacements and the worked example at their named anchors; each paragraph's prefix through its colon stays byte-identical, code-family staging metadata is named, and each affected skill file deletes equivalent redundant operative bytes in the same change while preserving its contract; record before/after byte counts per file in the task log. [class: IMPLEMENTATION_REQUIRED]
- [x] Verify the stale clause is gone from all three files, legacy and block entries parse under the shared parser contract, and review-plan contains the canonical example. [class: REPOSITORY_TEST]
- [x] Commit: `skills: the round-close seal paragraphs show the parser's block grammar with one worked example`. [class: IMPLEMENTATION_REQUIRED]

### Task 4: Needs-recert class for the anchor-leg refusal

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/decisions.md`
- `agents/skills/maintenance/template-execution.md`

Prescribed replacement in `agents/skills/maintenance/decisions.md` (the D1 bullet's needs-recert sentence; replace the clause `a plan failing the certification oracle on a stale `source_digest` is not dropped from selection` with the line below, verbatim, in place):

```
a plan failing the certification oracle on a stale `source_digest`, or on an anchor-leg refusal (`corrections verification: anchor leg refused`) over plan bytes that re-hash to its latest ready sidecar's digest, is not dropped from selection
```

Prescribed replacement in `agents/skills/maintenance/template-execution.md` (the PRE-STEP paragraph is hard-wrapped; replace the single line `source_digest, the repo moved under the plan: run a fresh focused review-plan` with the two lines below, verbatim, keeping the preceding line `rule: stop and re-derive the state from disk. If the gate fails with a stale` and the following line `re-cert round over the current bytes, fold all blocking findings into the plan` byte-identical):

```
source_digest, or with an anchor-leg refusal over plan bytes that re-hash to
the latest ready sidecar's digest, the repo moved under the plan: run a fresh focused review-plan
```

- [x] Apply both prescribed replacements verbatim at their named anchors; `needs-recert` stays inside the D1 region and the PRE-STEP's gate sentence keeps preceding its resume rule. Delete equivalent redundant operative bytes in each grown maintenance skill file and record before/after byte counts while preserving both contracts. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Validation Commands list and expect every existing suite and repository gate to exit 0. [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: an anchor-leg refusal over byte-identical plan bytes is needs-recert, never a silent skip`. [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- docs/history/backlog/2026-10-07-corrections-graded-freshness-post-squash.md (moved to docs/history/backlog/completed/ with the covered flip; the plan's sealed-anchored post-squash recovery is the fix)
- docs/history/backlog/2026-10-15-review-plan-seal-grammar-drift.md (moved to docs/history/backlog/completed/ with the covered flip; the review-plan seal-grammar paragraph and worked example in Task 3 are the fix)
