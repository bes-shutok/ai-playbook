# Plan: docs-branch assembly guard and the named maintenance completion-arm audit duty

Backlog origin: docs/history/backlog/2026-10-03-docs-branch-silent-partial-extract-no-op.md; docs/history/backlog/2026-10-03-maintenance-completion-arm-audit-duty.md
Driving force: reliability (primary, the witnessed silent no-op), consistency (secondary, the completion-arm audit duty)
Plan review record: the staging series docs/reviews/2026-10-04-plan-review-docs-branch-sync-fail-loud-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

The two guard-text gaps close together. First, executing the docs-branch Step 2 sync fence without the Documentation-paths fence assembled into the same invocation refuses at fence entry with a named error on stderr and a non-zero exit, instead of reaching the witnessed silent rc-0 no-op (a consumer repo's docs branch drifted a week behind two rc-0 no-op syncs on 2026-10-03). Second, the maintenance D1 landing-completion success tail names the closeout audit duty by subcommand and arm beside the reconcile receipt, so a literal actor on the deferred-landing-retry path can no longer run reconcile-only and skip the audits that today are adopted only by region reference.

- The refusal keys on `SHADOW_CANDIDATES` being unset at sync-fence entry, never on an empty post-disk result: the assembled run always initializes the array non-empty (the Documentation-paths fence builds it as its first statement), so the unset key means unassembled, and the legitimate post-disk empty case keeps exiting 0 through the existing `SHADOW_PATHS`-empty early return.
- The Critical paragraph gains one assembly sentence so an agent assembling the script from SKILL.md source extracts both fences, the failure mode the guard turns loud.
- The maintenance tail enumerates the two `scripts/base_reflog_audit.py` subcommands (`reflog-window`, `landed-receipt`), the `scripts/base_branch_amend_guard.py` `sweep-window` arm, and the landed commit's first-parent diffstat receipt; a companion pins group holds the enumeration.

Gate delta: additions are one entry guard (an unset-keyed refusal at the top of an existing fence, paying sibling: the fence's existing `SHADOW_PATHS`-empty early return, which keeps its exit-0 semantics for the legitimate empty case), one assembly sentence, an explicit audit-receipt enumeration in the D1 tail, and one new pins group over that tail (paying sibling: the suite's existing base-branch ref-move pins at the suite tail, which pin the execute-plan wiring of the audit legs but not the maintenance tail's region reference). Removals: none. No script bytes change; the pins suite gains pins only; no new files.

## Terms

- Partial extraction: executing the Step 2 sync fence alone, without the Documentation-paths fence concatenated into the same bash invocation; the witnessed production failure shape (2026-10-03, two rc-0 no-op syncs while the docs branch held a week of drift).
- Assembly: the two fences concatenated into one bash invocation, per the Step 2 Critical paragraph's existing single-invocation rule.
- Unset-keyed guard: the refusal condition is `${SHADOW_CANDIDATES+x}` expanding empty, which on the fence's documented bash 3.2 target means the variable is unset or a declared-empty array (`SHADOW_CANDIDATES=()`, which bash 3.2 treats as unset for this expansion), never an emptiness test on the post-disk result; the expansion is non-empty for any array assigned at least one element, and the Documentation-paths fence's first statement assigns a non-empty literal, so the refusal condition is exactly "the build never ran in this invocation".
- The audit duty (the maintenance D1 tail): the named invocations the post-landing reconciliation implementation in `agents/skills/execute-plan/SKILL.md` carries today, namely the `reflog-window` and `landed-receipt` subcommands of `scripts/base_reflog_audit.py`, the base-branch amend guard's arm beside them (`sweep-window`, delivered by the landed plan `docs/history/plans/2026-10-04-main-rewind-bypass-fences.md`), and the landed commit's first-parent diffstat receipt, recorded beside the reconcile receipt.

## Assumptions

- Fence anchors were re-derived from the live bytes at authoring time (2026-10-04, HEAD 9de75c8b): the Documentation-paths fence initializes `SHADOW_CANDIDATES` unconditionally as its first build statement and defines the shared `docs_branch_candidate_ignored` probe; the Step 2 sync fence opens with `CURRENT_BRANCH=` and `DOCS_BRANCH=` assignments followed by the two-line build comment beginning `# Build SHADOW_CANDIDATES per Documentation paths section above`; the legitimate `SHADOW_PATHS`-empty early return sits below the candidate disk checks. Tasks anchor to those byte shapes, never to line numbers; execution re-derives each anchor from the live file before editing.
- The named error text is the origin row's recorded string verbatim. The guard keys on unset while the message's first clause reads "empty at entry": an unset array expands empty, so the message names the observable state the partial extraction creates, and keeping the row's exact bytes lets the fixtures, the pins, and the origin row cite one string.
- The pins suite carried one pre-existing failure at the authoring anchor (review r1 witness: `PIN FAIL: recognition line in deferred-retriage task file`): the interim unblock commit 8d0066eb renamed the retriage task file while the suite's stem-derived recognition loop still consumed the old filename, the one live filename consumer its census missed. This cycle repairs that loop in the separate commit eae2cbfe (explicit filename/literal pairs; the stored recognition tail carries the TOML id, not the filename stem; superseding origin recorded beside the loop per the suite's reconcile convention) before this plan lands, so every green-suite receipt in this plan reads against the repaired suite, and the repair touches no pin this plan's tasks own.
- Execution-order dependency, stated: the D1 tail's `sweep-window` literal names the arm the plan `docs/history/plans/2026-10-04-main-rewind-bypass-fences.md` delivers, and that plan sits at the plans root ahead of this one, so this plan executes after it. If the order ever flips, the tail names a not-yet-shipped arm; under the completion duty's existing probe discipline (a guard copy absent from every resolved path is a rc 1 deployment gap, never a skip) that failure is loud, which is the accepted direction.
- The optional before/after branch-tip echo stays dropped (origin row optional hardening, rejected for scope in the dispatch entry).
- Task 1 adds no committed test suite: docs-branch carries no pins suite today and the dispatch entry's validation is extraction-based; the fixtures run at execution time from Validation Commands.
- The D1 tail's skip-clause ("a skipped or failed reconcile fails the closeout") stays byte-identical: the row's contract is the naming, and the enumerated receipts join the recorded receipt set the clause already governs.
Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the docs-branch sync fence refuses a solo extraction loudly and the maintenance completion tail names its audit subcommands, why: one witnessed production failure (a week of docs-branch drift behind two rc-0 no-op syncs) and one reconcile-only backstop gap, driving force reliability.

The docs-branch skill splits Step 2's executable across two bash fences, and the dependency runs one way: the Documentation-paths fence builds `SHADOW_CANDIDATES` and the shared candidate-ignored probe, the sync fence consumes both. The sync fence's own build comment documents the dependency, but nothing checks it was honored, so an agent that extracts the larger self-titled fence alone gets silence: the unset array expands empty, the candidate loop runs zero times, and the script exits 0 at the `SHADOW_PATHS`-empty early return. That exact shape ran twice in a consumer repo on 2026-10-03 while plans archived and reviews landed, and the docs branch stayed a week stale. The guard makes the unassembled state refuse at entry, before any artifact creation, with the origin row's named error; the assembled run is untouched because its first statement always initializes the array.

The maintenance D1 landing-completion success tail reconciles live checkouts "per the post-landing reconciliation implementation" in execute-plan and records the reconcile receipt, naming no audit arm of its own. The implementation it points at names `reflog-window`, `landed-receipt`, the diffstat receipt, and the amend guard, but a literal actor following only the maintenance tail runs reconcile-only and skips the audits; the row re-confirmed the gap at execution review in 2026-10-03. The tail now names the receipts explicitly, and the pins suite holds the naming region-scoped to the D1 bullet, the same vacuous-canary discipline the suite applies wherever the Revisions ledger paraphrases an operative span.

## Evaluation Criteria

**Quality dimensions:**

- Correctness: the guard fires exactly when the build never ran (unset, and a declared-empty array on bash 3.2, which treats it as unset for the `${var+x}` expansion); any array assigned at least one element passes and the legitimate post-disk empty case keeps exiting 0 through the existing early return; the assembled fixture performs real sync work, not merely absence of refusal.
- Fail-loud fidelity: the lone-fence refusal prints the named error to stderr with a non-zero exit before any artifact creation (no refs created, no worktrees, no staged content, clean status).
- Non-regression: no existing pin literal is edited and the pins suite stays green throughout; the fence's bash-3.2 unset-safe expansion discipline is preserved (no `set -u` is introduced, the rejected alternative); the sync fence's bytes below the guard are untouched.
- Pin fidelity: the new pins group is region-scoped to the D1 bullet line per the suite's vacuous-canary doctrine (the Revisions ledger paraphrases the tail) and demonstrates RED when a named literal is deleted from the tail.

**Done when:**

- The three extraction fixtures pass on the final bytes: the concatenated fences parse under `bash -n`; the lone sync fence in a scratch repo refuses with the named error and zero mutations; the assembled fences in a scratch repo with one ignored candidate reach the sync logic and commit the candidate.
- `bash scripts/check_maintenance_pins.sh` exits 0 on the final bytes with the new group present, and a scratch deletion of one tail literal turns the new group RED, recorded in the execution session notes.

**Ship when:**

- The next landing-completion run on the deferred-landing-retry path records the audit receipts by name beside the reconcile receipt without the actor needing to open the execute-plan implementation (loop-owned condition; the tail's own pins hold).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `agents/skills/docs-branch/SKILL.md` (the Step 2 sync fence gains the unset-keyed entry guard; the Step 2 Critical paragraph gains the assembly sentence)
- `agents/skills/maintenance/SKILL.md` (the D1 landing-completion success tail names the audit duty explicitly)

**Tests:**

- `scripts/check_maintenance_pins.sh` (companion pins group over the maintenance tail; no existing pin line edited)

**Contract files:**

- `scripts/OUTCOME_CONTRACT.md` (consulted, no change required: the `check_maintenance_pins.sh` row already covers the emission funnel and exit-code contract the new group reuses)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- The Documentation-paths fence and Step 1 fence bytes; reason: they already initialize and build `SHADOW_CANDIDATES` correctly, and the witnessed failure is the sync fence's missing entry check, not their behavior.
- A committed test suite or pins coverage for docs-branch; reason: the dispatch entry's validation is extraction-based and the skill carries no pins suite today; inventing one is a separate corpus decision.
- Wiring `sweep-window` into the execute-plan completion duty text; reason: that wiring is the landed sibling plan's Ship-when (`docs/history/plans/2026-10-04-main-rewind-bypass-fences.md`); this plan only names the arm in the maintenance tail.
- The docs-branch sync algorithm itself (deletes parse, worktree sync, certified-plan ordering guard, restores); reason: no witnessed defect in it, and the guard is an entry check, not a behavior change.

## Validation Commands

```bash
# Extraction (re-derive the fence ranges from the live bytes at execution time):
#   fence A = the ```bash fence under "## Documentation paths"
#   fence B = the ```bash fence under "## Step 2: Sync to the `docs` Branch"
sed -n '<A-start>,<A-end>p' agents/skills/docs-branch/SKILL.md > /tmp/db-fence-a.sh
sed -n '<B-start>,<B-end>p' agents/skills/docs-branch/SKILL.md > /tmp/db-fence-b.sh

# 1. the concatenated fences parse
cat /tmp/db-fence-a.sh /tmp/db-fence-b.sh > /tmp/db-assembled.sh && bash -n /tmp/db-assembled.sh

# 2. the lone sync fence refuses loudly with zero mutations (RED before the edit:
#    the same fixture exits 0 with no skill-generated output, the witnessed shape)
s1=$(mktemp -d) && git -C "$s1" init -q && git -C "$s1" config user.email t@example.com && git -C "$s1" config user.name t && git -C "$s1" commit --allow-empty -q -m init
out=$(cd "$s1" && bash /tmp/db-fence-b.sh 2>&1); rc=$?
test "$rc" -ne 0 && echo "$out" | grep -qF "SHADOW_CANDIDATES empty at entry"
git -C "$s1" show-ref --verify --quiet refs/heads/docs && exit 1 || true
test -z "$(git -C "$s1" status --porcelain)" && test "$(git -C "$s1" worktree list --porcelain | grep -c '^worktree ')" -eq 1

# 3. the assembled fences reach the sync logic and commit the candidate
s2=$(mktemp -d) && git -C "$s2" init -q && git -C "$s2" config user.email t@example.com && git -C "$s2" config user.name t && git -C "$s2" commit --allow-empty -q -m init
printf 'docs/\n' > "$s2/.gitignore"
mkdir -p "$s2/docs/history/reviews" && echo note > "$s2/docs/history/reviews/note.md"
(cd "$s2" && bash /tmp/db-assembled.sh)
git -C "$s2" show-ref --verify --quiet refs/heads/docs
git -C "$s2" ls-tree -r --name-only refs/heads/docs | grep -qx 'docs/history/reviews/note.md'

bash scripts/check_maintenance_pins.sh
python3 scripts/machinery_inventory.py --check
bash scripts/check-no-em-dash.sh added-lines --base <merge-base at landing>
```

### Task 1: the sync fence refuses a partial extraction at entry

Files:
- `agents/skills/docs-branch/SKILL.md`

Witness the silent shape first: extract the Step 2 sync fence alone per Validation Commands and run fixture 2 against the pre-edit bytes; it exits 0 with no skill-generated output (the witnessed consumer-repo no-op), and that run is the RED receipt recorded in the execution session notes. Then:

- Insert the guard immediately after the two-line build comment (whose second line reads `# section also defines the shared candidate-ignored probe used below).`; the two-line form is unique, the Step 1 fence carrying a one-line variant of the same comment) and before every other statement of the fence, so the refusal precedes any artifact creation:

```bash
# Unset-keyed entry guard: the assembled run always initializes SHADOW_CANDIDATES
# (the Documentation paths fence builds it first), so unset means this fence was
# extracted without it; refuse before any artifact creation.
if [ -z "${SHADOW_CANDIDATES+x}" ]; then
  echo "docs-branch: SHADOW_CANDIDATES empty at entry; the Documentation-paths fence was not assembled with the sync fence; refusing to no-op silently" >&2
  exit 1
fi
```

- The key is `${SHADOW_CANDIDATES+x}`, verified on the fence's documented target shell (/bin/bash, 3.2): it expands to `x` for any array assigned at least one element and to the empty string when the variable is unset or declared empty (`SHADOW_CANDIDATES=()`, which bash 3.2 treats as unset for this expansion), so the refusal condition is exactly "the build never ran in this invocation"; the Documentation-paths fence's first statement assigns a non-empty literal, the assembled run always passes, and the legitimate post-disk empty case keeps exiting 0 through the existing `SHADOW_PATHS`-empty early return. The expansion belongs to the same unset-safe family as the fence's documented `${arr[@]+...}` bash-3.2 idiom; no `set -u` is introduced (rejected alternative: blanket unset-noun-set breaks the fence's intentional empty expansions).
- The exit is 1 (non-zero per the origin row's contract) and the message goes to stderr verbatim as the origin row records it, so fixtures and any downstream caller can match the fixed string `docs-branch: SHADOW_CANDIDATES empty at entry`.
- Append exactly one sentence to the Step 2 Critical paragraph (the paragraph opening `> **Critical:** Run this entire script as a **single shell invocation**.`): "Extract the `## Documentation paths` fence and this sync fence together into the same invocation: the sync fence refuses to run when `SHADOW_CANDIDATES` is unset at entry, which is the signature of a solo extraction, so a partial assembly fails loudly instead of syncing nothing."
- Every other byte of the fence below the guard is untouched (the deletes parse, worktree lifecycle, certified-plan ordering guard, restores, commits, trap).

Evidence: Validation Commands 1 through 3 on the post-edit bytes (the concatenated fences parse; the lone fence exits non-zero naming the error with no docs ref, no extra worktree, and clean status in the scratch repo; the assembled run creates the docs branch and commits `docs/history/reviews/note.md`); fixture 2's pre-edit silent rc-0 run recorded as the RED witness; `bash scripts/check_maintenance_pins.sh` stays green (no pin touches docs-branch, the edit must not change that).

### Task 2: the maintenance completion tail names the audit duty

Files:
- `agents/skills/maintenance/SKILL.md`
- `scripts/check_maintenance_pins.sh`

Write the RED pin first (the group below fails while the tail still carries only the region reference), then:

- In the D1 bullet's landing-completion success tail, replace the span

`reconcile live checkouts of the base branch per the post-landing reconciliation implementation in the Worktree-first standard section of \`agents/skills/execute-plan/SKILL.md\` and record the reconcile receipt;`

with

`reconcile live checkouts of the base branch per the post-landing reconciliation implementation in the Worktree-first standard section of \`agents/skills/execute-plan/SKILL.md\`, and record the reconcile receipt beside the implementation's named audit receipts (the \`scripts/base_reflog_audit.py\` \`reflog-window\` and \`landed-receipt\` subcommands, the \`scripts/base_branch_amend_guard.py\` \`sweep-window\` arm, and the landed commit's first-parent diffstat receipt);`

- The tail's skip-clause and every other byte of the D1 bullet stay untouched; the enumeration names what the pointed-to implementation already runs, including the third arm the sibling plan ships, so the maintenance tail and the execute-plan implementation name the same duty.
- Append the companion pins group at the suite tail, after the primary-checkout landing helper block and before the final all-hold checkpoint, with no existing pin line edited:

```bash
# --- maintenance completion-arm audit-duty pins (plan
# docs/history/plans/2026-10-04-docs-branch-sync-fail-loud.md Task 2) ---
# The D1 landing-completion success tail must name the closeout audit duty
# explicitly (origin:
# docs/history/backlog/2026-10-03-maintenance-completion-arm-audit-duty.md):
# region-scoped to the D1 bullet line per the suite's vacuous-canary doctrine
# (the Revisions ledger paraphrases the tail, so a whole-file grep is satisfied
# by a stray copy; deleting any named literal from the tail empties its span
# and fails here).
python3 - "$S" <<'EOF' || fail=1  # the block must fail the suite, never let a failed pin pass
import sys
s = open(sys.argv[1]).read()
d1 = ""
for line in s.split("\n"):
    if line.startswith("- `D1 (execute)`:"):
        d1 = line
        break
if not d1:
    print("PIN FAIL: D1 bullet line missing from SKILL.md"); sys.exit(1)
for needle in ("`scripts/base_reflog_audit.py` `reflog-window`",
               "`landed-receipt`",
               "`scripts/base_branch_amend_guard.py` `sweep-window`",
               "first-parent diffstat receipt"):
    if needle not in d1:
        print("PIN FAIL: D1 landing-completion tail lacks the audit-duty needle %r" % (needle,)); sys.exit(1)
EOF
```

Evidence: `bash scripts/check_maintenance_pins.sh` exits 0 on the final bytes with the new group present; the RED demonstration (scratch-delete the `sweep-window` literal from the tail, the suite prints the needle PIN FAIL and exits 1, restore) is recorded in the execution session notes; the pins suite is green before the edit too, so the only delta is the new group.

## Disposition

Executed 2026-10-04 in worktree ai-playbook-wt-dbsf (branch plan-dbsf-exec) under the merge lock; implementation commits 7897f7a6 (Task 1), 526b1c45 (Task 2), fold commit 6e6b5f16. Exec review: r1 ready=yes zero blocking, 3 Low plan-byte fidelity findings folded (heredoc delimiter restored to EOF, D1 prefix carries the trailing colon, guard insertion made whitespace-exact so below-guard fence bytes are untouched); record docs/reviews/2026-10-04-plan-review-docs-branch-sync-fail-loud-exec-r1.md (gitignored home).

RED receipts recorded in-session: the lone sync fence extracted from the pre-edit bytes exited rc 0 with no skill-generated output, no docs ref, and no worktrees (the witnessed consumer-repo silent no-op); the pins group appended before the tail replacement failed the suite with "PIN FAIL: D1 landing-completion tail lacks the audit-duty needle", and the post-fold scratch deletion of the sweep-window literal reproduced the needle PIN FAIL before restore. Fixture receipts on the final bytes: concatenated fences parse under bash -n; the lone fence exits 1 naming the exact fixed string with zero mutations; the assembled run creates the docs branch and commits docs/history/reviews/note.md. Bash 3.2 semantics verified empirically by the reviewer (unset and declared-empty both refuse; one element passes).

Execution-order note: the sweep-window arm named in the D1 tail is being delivered in parallel by the sibling plan main-rewind-bypass-fences (peer execution in worktree ai-playbook-wt-mrbf, task 1 committed at execution time); the plan's assumption accepts this loud direction.
