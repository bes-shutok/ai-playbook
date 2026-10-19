# Plan: Document live-holder done-lock release recovery

Backlog origin: docs/history/backlog/2026-10-10-done-lock-live-owner-blocks-plan-closeout.md
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-10-18-plan-review-done-live-owner-closeout-recovery-pe4f3ada4-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 0.5h total, largest task 0.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-10-done-lock-live-owner-blocks-plan-closeout.md (session 01a1501c-2267-70b3-9423-7dd6ba3e4dd8)

## Terms

- **done lock:** the project checkout's lock released by `done_run.sh finalize`.
- **from-holder release:** the existing `release-repo --from-holder` path, which checks the pinned holder and caller ancestry.
- **env-token release:** the existing `release-repo` path supplied with `DONE_LOCK_DIR` and `DONE_LOCK_TOKEN` in the command environment.
- **lock metadata:** the held lock's `meta.env`, which records its repo root and token.
- **compare-and-swap:** the release script's check that the lock token and start epoch still match before removing the lock.
- **setup lock witness:** the `DONE_LOCK_DIR` and SHA-256 fingerprint of `DONE_LOCK_TOKEN` emitted by Step 0 setup and retained in session context; the raw token is never copied into a durable record.
- **recovery witness:** the Step 0 setup lock witness and the original token retained in session context; the run manifest does not prove lock-generation ownership.
- **captured metadata image:** one atomic read of `meta.env` from the setup-witness lock path at Step 6, used only to corroborate the token fingerprint, lock path, and expected checkout against the Step 0 witness.

## Why

A completed run can leave its live done lock held when `done_run.sh finalize` cannot release from a caller outside the pinned holder's process ancestry. The existing env-token release can recover the witnessed case, but Step 6 does not explain that bounded path, so an operator must rediscover it.

## Gist & Examples

TLDR: done Step 6 documents env-token recovery bound to the Step 0 lock witness, because reducing repeated lock recovery work serves efficiency.

Before: Step 6 leaves recovery after lost exports underspecified and directs readers toward a tokenless `--from-holder` attempt that can release a replacement generation before any Step 0 witness check.

After: Step 6 uses the existing env-token release when exports are available. If exports are lost but the Step 0 witness and original token remain in session context, it re-exports that token and checks the lock path, token fingerprint, `repo_root`, and `status` against the witness and expected checkout before release. It never tries tokenless `--from-holder` as a recovery shortcut. If the original token or witness is unavailable, it stops; it does not infer ownership from a fresh metadata read or the run manifest. The token never appears in recovery output or durable records, and Step 6 confirms `status` is free after release.

Edge cases: a replacement generation, missing setup witness, missing original token, malformed or mismatched metadata, wrong checkout identity, or token/compare-and-swap refusal stops recovery. Do not attempt `--from-holder` or use `stale-clean` for this recovery.

## Outcome

Done Step 6 gives operators a safe recovery for the witnessed live-holder, out-of-ancestry refusal while preserving the lock script's existing release guards.

- Operators can release the expected lock with the existing token-checked path and verify it is free.
- The `--from-holder` ancestry guard and the release script's token comparison and compare-and-swap remain unchanged.
- The token is not printed, logged, or stored in a durable record.

Gate delta: none. The Step 0 witness clarifies the origin prompt's existing “same lock” and repo-identity conditions; it adds no new machinery, schema field, or blocking review duty.

## Assumptions

- The frozen prompt entry was corrected during this authoring run to use the original Step 0 token and witness; this plan keeps that wording aligned with the implementation guidance. The origin backlog row contains classification metadata and a Step 0 reference, not recovery acceptance text.
- The original token and lock path retained from Step 0 are the ownership witness. A later `meta.env` image can corroborate that witness but cannot establish ownership on its own; the run ID and manifest do not bind a lock generation.
- When exports are lost, recovery is safe only while both the original token and Step 0 fingerprint/path remain available in session context. If either is unavailable, stop and report for operator handling rather than using the tokenless `--from-holder` path.
- `release-repo` remains the existing token-checked recovery and needs no script change; basis: `scripts/done-lock.sh` `cmd_release` compares the supplied token and uses compare-and-swap removal.
- The frozen prompt entry now carries the original Step 0 token source and remains aligned with the plan; the origin row remains classification metadata. The separate generation-binding backlog description is corrected to distinguish this prompt guidance from the still-open runtime defect.
- The plan changes Steps 0 and 6 in `agents/skills/done/SKILL.md`, verifies the matching frozen prompt entry uses the same Step 0 token source, and corrects one stale sentence in the generation-binding backlog item. These are the smallest coherent documentation changes because the prompt guidance must stay aligned and the backlog description must distinguish that guidance from the runtime defect. Recording a non-secret fingerprint at Step 0 binds the existing token recovery to the acquired generation; no lock script, schema, or persistent ledger changes.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: each recovery step matches the existing `done_run.sh` and `done-lock.sh` behavior.
- safety: the procedure verifies the original lock generation and expected checkout, keeps the token secret, and confirms free status without weakening release guards.
- scope: Steps 0 and 6 document the existing recovery; no lock script or release mechanism changes.

**Done when:**
- Step 6 documents the env-token default and, for lost exports, permits only re-export of the original Step 0 token retained in session context; it never tries tokenless `--from-holder` as a recovery shortcut.
- It reads one atomic `meta.env` image to corroborate the setup fingerprint and lock path, checks checkout identity and status, and permits release only with the original token and matching witness.
- It stops when the original token or witness is unavailable, never infers ownership from a fresh metadata read or run manifest, keeps the token secret, and confirms status is free after release.

**Ship when:**
- None; the change is local documentation.

## Review Scope

**Explicit must-fix:** findings on this path are always in scope:

**Documentation:**
- `agents/skills/done/SKILL.md` (Steps 0 and 6 only; all other sections are frozen).
- `docs/history/backlog/PLAN-PROMPTS.md` (matching frozen entry only, to verify it uses the original Step 0 token and witness and remains aligned with the plan).
- `docs/history/backlog/2026-10-18-done-lock-from-holder-generation-binding.md` (one stale description sentence; the runtime defect remains open).

**Tests:**
- None; the plan documents existing release behavior and changes no executable behavior.

**Plan-related extension:** implementation and review may change files not listed above only when they are causally required by this plan or fix a regression it introduces.

**Out of scope; reject unless plan-related:**
- `scripts/done_run.sh` and `scripts/done-lock.sh`; reason: their existing refusal and token-fenced release behavior is the contract being documented.
- `docs/history/backlog/2026-10-10-done-lock-live-owner-blocks-plan-closeout.md`; reason: it is classification metadata and does not contain recovery acceptance text to narrow.

## Validation Commands

```bash
bash scripts/check-no-em-dash.sh touched
bash scripts/check_maintenance_pins.sh
bash scripts/scan-public-hygiene.sh
```

### Task 1: Retain the setup lock witness and document bounded recovery

Context surface: the plan's Terms and this task.

Files:
- `agents/skills/done/SKILL.md`
- `docs/history/backlog/PLAN-PROMPTS.md` (matching entry only)
- `docs/history/backlog/2026-10-18-done-lock-from-holder-generation-binding.md` (stale description sentence only)

- [x] Step 6 keeps the env-token path as default when exports are available; when exports are lost, it re-exports only the original token retained from Step 0 and never tries tokenless `--from-holder` as a recovery shortcut [class: IMPLEMENTATION_REQUIRED]
- [x] Step 0 retains `DONE_LOCK_DIR` and a SHA-256 fingerprint of its emitted `DONE_LOCK_TOKEN` in session context; it does not copy the raw token into a durable record [class: IMPLEMENTATION_REQUIRED]

- [x] Before release, Step 6 reads one atomic `meta.env` image and checks `repo_root` against `git rev-parse --show-toplevel`, `lock_dir` against `status`, and token fingerprint and path against the Step 0 witness; this image corroborates ownership and never supplies a substitute token [class: IMPLEMENTATION_REQUIRED]

- [x] If the Step 0 setup witness or original token is unavailable or mismatched, Step 6 stops; it never treats a fresh metadata read or run ID/manifest as proof of ownership [class: IMPLEMENTATION_REQUIRED]
- [x] A replacement generation cannot be released: the token passed to `release-repo` is the original Step 0 token, so the existing token comparison and compare-and-swap reject a replacement token; tokenless `--from-holder` is not attempted [class: IMPLEMENTATION_REQUIRED]
- [x] Step 6 keeps the token out of output and durable records, requires `status` to show free after release, and stops on wrong checkout identity, malformed metadata, witness mismatch, or any token/compare-and-swap refusal [class: IMPLEMENTATION_REQUIRED]
- [x] The documentation changes no release script or mechanism and preserves the existing token comparison, compare-and-swap, and `--from-holder` ancestry guard [class: IMPLEMENTATION_REQUIRED]
- [x] The frozen prompt `Prompt:` paragraph uses the original Step 0 token, corroborated by the setup witness and captured metadata image; the matching scope arm stays consistent, and recovery stops when the original token or witness is unavailable [class: IMPLEMENTATION_REQUIRED]
- [x] The generation-binding backlog item says the documentation plan changes the prompt guidance while the runtime defect remains open [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: document live-holder done-lock recovery` [class: IMPLEMENTATION_REQUIRED]
