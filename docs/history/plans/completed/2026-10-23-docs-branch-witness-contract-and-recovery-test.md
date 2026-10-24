# Plan: Make the Docs-Branch Witness Contract Generic and Test CAS Recovery

Backlog origin: docs/history/backlog/2026-10-09-docs-branch-witness-contract-and-recovery-test.md
Driving force: code-quality
Plan review record: .ai-playbook/reviews/2026-10-23-plan-review-docs-branch-witness-contract-and-recovery-test-r*.md
Execution budget: 1h total, largest task 0.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-09-docs-branch-witness-contract-and-recovery-test.md (session 01a1638f-189d-7b02-9cf8-0990eb6f3dfd)

## Terms

- **Witness line:** the caller-provided `lesson-scope-audit:` line stored in the docs branch commit body.
- **CAS:** compare-and-swap publication of the docs branch ref, conditional on the observed tip remaining current.
- **Recovery ref:** the direct ref under `refs/docs-witness-recovery/` that retains a witness commit after CAS refuses.
- **Skill-gate marker:** the fresh plans-class marker required before each plan-file write, named `plans.<project>.<session>.marker` in `~/.ai-playbook/runtime/skill-invoked/`.
- **Project key:** the key resolved by `facts_paths.resolve_project_key` from the plan write target's worktree root.
- **Pinned fixture environment:** the existing `direct_main_environment` test helper, which fixes Git configuration, author identity, clock, trace file, and lock paths for direct runner calls.
- **Session key:** the `session_channel.py` subprocess result; an empty or whitespace-only result maps to `no-session`, otherwise the key is the first 16 hexadecimal characters of SHA-1 over the result.

## Why

The shared docs-branch skill documents one organization's witness text as canonical even though callers provide the exact line. The runner preserves a witness commit when CAS loses a race, but its tests do not prove that this recovery path leaves the competing docs tip current and the recovery commit reachable.

## Gist & Examples

TLDR: Clarify caller ownership of witness text and cover CAS recovery in a deterministic test, improving the shared workflow's code quality.

Before: The shared skill names an organization-specific witness sentence as canonical. A race that moves `refs/heads/docs` during witness append has no regression test for the competing tip or recovery ref.

After: The skill documents the required caller-supplied prefix and exact-line behavior without naming one caller's sentence as canonical. A deterministic fixture advances the docs ref immediately before the runner's CAS update and checks the refusal, the still-current competing tip, and the recovery commit's witness body.

## Outcome

The shared witness contract is organization-neutral, and CAS recovery has a deterministic regression witness.

- Callers remain responsible for supplying the exact witness line.
- A losing witness append leaves the competing docs tip in place.
- The failed witness commit remains directly addressable and contains the caller's line.

Gate delta: no runtime gate, refusal class, fence, protocol layer, or schema field is added or removed; the regression test adds no runtime machinery or blocking review duty.

## Assumptions

- The plan changes only the shared witness wording and its runner test because the backlog identifies the current runner as safe and names these two gaps; basis: the backlog origin's Problem, Evidence and location, and Expected sections.
- The race test will patch the existing `update_docs_ref` function at the test boundary instead of adding a production hook; basis: `scripts/test_docs_branch_sync.py` already loads a runner namespace for direct function tests, and this avoids production machinery.
- The race fixture will use `direct_main_environment` and enumerate recovery refs rather than predicting their timestamp-and-process-id names; basis: the existing helper pins Git inputs and the runner generates recovery ref names from the current time and process id.
- The two backlog concerns form one bounded plan because both concern the same witness contract and append failure path; no neighboring cluster item is included without additional evidence.

Decision points requiring a grill: Keep the scope to the shared skill contract and an isolated race test; basis: maintenance-selected authorization for this backlog item and its explicit Expected section; simpler option rejected: a production injection hook would add runtime surface when the existing test namespace can interpose the update.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the contract describes caller ownership and exact-line validation, while the recovery test proves the active ref is not overwritten.
- Testability: the race is forced deterministically and its recovery object is inspected directly.
- Simplicity: the change adds no production seam, runtime gate, or broader backlog scope.

**Done when:**
- `agents/skills/docs-branch/SKILL.md` describes only the caller-supplied prefix and exact-line contract, without an organization-specific canonical example.
- `scripts/test_docs_branch_sync.py` deterministically interposes a competing docs-ref update and verifies refusal, the unchanged competing tip, and a directly readable recovery ref whose commit contains the witness line.
- The focused docs-branch test suite, public-hygiene scan, em-dash scan, and plan readiness pass.

**Ship when:** The shared docs-branch skill and runner test contain the contract and recovery coverage described above.

## Review Scope

**Explicit must-fix:** valid findings causally related to these contract and recovery-test changes.

**Production code:**
- `agents/skills/docs-branch/SKILL.md`
- `scripts/docs_branch_sync.sh` only if the current contract wording or observed behavior requires a correction to meet the stated outcome.

**Tests:**
- `scripts/test_docs_branch_sync.py`

**Plan-related extension:** implementation and review may change files not listed above only when a finding is causally required by this plan's contract or race test; otherwise record it out of scope.

**Out of scope; reject unless plan-related:**
- `agents/skills/done/SKILL.md`; done continues to own the witness text and docs-branch owns append mechanics.
- Broader docs-branch synchronization, archive selection, or lock behavior; this plan covers the witness append contract and CAS recovery only.
- The clustered selector-test and untracked-record-loss backlog items; neither is needed to establish this outcome.

## Validation Commands

Run the focused runner test file, the configured public-hygiene scan over the scoped non-Markdown files, the em-dash scan over those files, and plan readiness for the reviewed plan bytes. Check that the old organization-specific canonical sentence is absent from the witness contract and the generic prefix and exact-line behavior remain documented. Every command fails closed, including the expected no-match check.

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_docs_branch_sync.py' || { check_rc=$?; echo "docs-branch tests failed" >&2; exit "$check_rc"; }
if rg -n 'canonical drift witness line this skill expects|company guidelines master not found' agents/skills/docs-branch/SKILL.md; then echo "organization-specific canonical example remains" >&2; exit 1; else check_rc=$?; if [ "$check_rc" -ne 1 ]; then echo "rg failed while checking the old example" >&2; exit "$check_rc"; fi; fi
rg -n 'caller passes the exact witness line|lesson-scope-audit:|byte-for-byte identical' agents/skills/docs-branch/SKILL.md || { check_rc=$?; echo "generic witness contract text is missing" >&2; exit "$check_rc"; }
PUBLIC_HYGIENE_REPO_ROOT="$PWD" bash scripts/scan-public-hygiene.sh --files scripts/test_docs_branch_sync.py scripts/docs_branch_sync.sh || { check_rc=$?; echo "public-hygiene scan failed" >&2; exit "$check_rc"; }
CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file scripts/test_docs_branch_sync.py scripts/docs_branch_sync.sh || { check_rc=$?; echo "em-dash scan failed" >&2; exit "$check_rc"; }
python3 scripts/plan_readiness.py docs/history/plans/2026-10-23-docs-branch-witness-contract-and-recovery-test.md || { check_rc=$?; echo "plan readiness failed" >&2; exit "$check_rc"; }
```

### Task 1: Make the witness contract caller-neutral

Context surface: the plan's Terms and Outcome, plus the backlog origin's Evidence and location and Expected sections.

Files:
- `agents/skills/docs-branch/SKILL.md`

- [x] Remove the organization-specific canonical witness example while retaining the caller-supplied `lesson-scope-audit:` prefix and exact-line contract. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep witness ownership with the caller and append mechanics with docs-branch, consistent with the existing integration point. [class: IMPLEMENTATION_REQUIRED]

### Task 2: Pin the losing-CAS recovery behavior

Context surface: the plan's Terms and Outcome, plus `scripts/docs_branch_sync.sh` `append_witness` and the existing runner namespace test fixture.

Primary class anchors:
- `append_witness` in `scripts/docs_branch_sync.sh`
- `load_runner_namespace` in `scripts/test_docs_branch_sync.py`

Files:
- `scripts/test_docs_branch_sync.py`

- [x] Add a deterministic fixture that advances the docs ref after witness creation but before the compare-and-swap update. [class: REPOSITORY_TEST]
- [x] Assert the append refuses, the competing docs tip remains current, and an enumerated, directly addressable recovery ref points to a commit containing the exact witness line; run under `direct_main_environment` so Git inputs and clock are pinned. [class: REPOSITORY_TEST]
- [x] Run the focused docs-branch runner test suite. [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

- docs/history/backlog/2026-10-09-docs-branch-witness-contract-and-recovery-test.md: covered by this plan (Tasks 1-2 landed; Phase 3 execution review r3 ready=yes zero blocking; origin file deleted in the same completion pass per the origins-closure disposition; the covering landing commit is the witness).
