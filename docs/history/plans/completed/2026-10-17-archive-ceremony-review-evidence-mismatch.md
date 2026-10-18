# Plan: accept digest-bound review receipts at the archive ceremony gate

Backlog origins (scope of record):

- docs/history/backlog/2026-10-17-archive-ceremony-review-evidence-mismatch.md
- docs/history/backlog/2026-10-18-maintenance-pin-stale-schedule-ask-contract.md

Driving force: reliability
Plan review record: the staging series .ai-playbook/reviews/2026-10-17-plan-review-archive-ceremony-review-evidence-mismatch-p98c6e6d2-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2.5h total, largest task 1.5h
Authoring claim: docs/tmp/authoring-claims/archive-ceremony-review-evidence-mismatch.md (session sess_d7b16c2e-0ca5-4449-8d37-07e65ed62f54)

## Terms

- archive ceremony: the closeout step that moves a completed plan under the archive directory, gated by `gate_archive_ceremony` in `scripts/done_sweep_gates_lib.py`.
- exec-review receipt: the plan-specific execution-review record the gate requires today, a file whose name matches `*-plan-review-<slug>-exec-r<N>.md` under the reviews home.
- bound receipt: a live plan-review record (its markdown twin present, neither name carrying a backup or orphan infix; a name shape whose sidecar is absent at the shared derivation declines fail-closed) whose stats sidecar binds it to the archived plan: the sidecar's `extensions.plan_identity` equals the recovered pre-archive path when the derivation recovers one, else the archive-state path (an absent sidecar identity, a basename-only match, or the markdown URL-or-Artifact line is never binding evidence), the sidecar's `source_digest` equals the sha256 of the plan's raw bytes at the reviewed revision when the derivation recovers one, else at the archived state, and the sidecar's `verdict` reads yes (an absent or non-yes verdict declines the record).
- acceptance arm: the gate's second recognition path beside the filename series, defined by the binding helper and the acceptance predicate.
- stale-deliverables twin: an archive the derivation surfaces from a stale run-deliverables line whose recorded plan path now sits archived, when no rename row covers it; its reviewed revision is unrecoverable.
- reviewed revision: the plan's raw bytes immediately before the landing edit, recovered from git as the parent-state blob at the pre-archive path (the HEAD blob at the rename source for a staged rename, the rename commit's parent blob for a committed rename); for a stale-deliverables twin or a committed addition the reviewed revision is unrecoverable and the record binds on the archived-bytes form alone (this plan's recorded shape decision); reproduced on the witnessed corpus: the certified r3 digest of rearm-dispatch-ladder equals its pre-landing blob, not its archived bytes.
- staging sidecar: the sidecar twin of a review record at the shared `stats_sidecar_path` derivation (the record's name with its suffix replaced), whose `source_digest` is version-1-required and whose `extensions.plan_identity` is the skill-mandated staging convention for identity-qualified records staged through the --source-plan flow (the validator itself admits a legacy URL-or-Artifact fallback, which the arm declines by design); this plan invents no new field.
- marked reconstruction: the execute-plan completion-evidence path that rebuilds a missing receipt from surviving review evidence with recorded re-verification, never inventing findings.
- archive state: one of the derivation's three states for a surfaced archive (completed, deferred, rejected); only the rejected state is exempt from the execution-evidence demand today and stays exempt.
- single-file plan: a plan archived as one regular file; the acceptance arm's only covered shape.
- directory-shape archive: a plan archived as a directory whose charter receipt names the charter file rather than a single plan file; outside the arm's scope with the receipt demand unchanged.
- reviews home: the configured reviews directory the gate's rglob already scans.
- pins suite: the maintenance pin checks run by `scripts/check_maintenance_pins.sh`.
- stale schedule-ask pin: the whole-sentence check in the pins suite that currently expects superseded wording in the `AGENTS.md` scheduling contract.
- binding helper: the new sibling helper beside `_has_exec_review_record` that routes the digest leg through `compute_source_digest` and the shared sidecar path derivation, reads the sidecar's identity, digest, and verdict fields only, each read minimal, and re-validates nothing else in the version-1 schema.
- gate refusal remedy: the refusal text `gate_archive_ceremony` emits, which names the sanctioned recoveries.

## Why

The archive ceremony requires a filename-shaped exec-review receipt, and a completed plan whose passing implementation review exists under a different record identity is blocked at closeout after its work and review are done, even when the surviving review evidence binds to the reviewed plan bytes. The witnessed closeout blocker is recorded in the origin row.

## Gist & Examples

TLDR: the archive ceremony gate accepts a reviewed-revision-bound review receipt beside the filename series, so a reviewed plan closes without producing a duplicate receipt.

Before: a completed plan with a passing implementation review refuses `gate_archive_ceremony` because no file is named `*-plan-review-<slug>-exec-r<N>.md`; the closeout blocks until the receipt is produced or reconstructed, though the surviving record's sidecar already proves the reviewed bytes were covered (the origin row's witnessed blocker).

After: the gate's recognition arm probes for a bound receipt (sidecar identity naming the archived plan, raw-byte digest binding to the shape-demanded raw-byte form (the reviewed revision, else the archived bytes), verdict yes) when the filename series is absent, accepting it with a warning line and failing closed on an unreadable sidecar, a non-yes verdict, or a digest or identity mismatch; the gate's refusal remedy names the new acceptance; no writer-side change is needed because staged plan-review records already carry the binding fields through the staging flow, and the residual writer-side text standardization is tracked in a filed backlog row.

## Outcome

An archive closeout whose reviews home carries a review record bound to the reviewed plan bytes passes the archive ceremony without producing a filename-shaped duplicate, while every protection the ceremony carries stays intact.

- A bound receipt satisfies the execution-evidence demand; the acceptance emits a warning naming the accepted record and its digest match.
- An unreadable sidecar, a digest matching neither raw-byte form or only the archived form while the reviewed revision is recoverable, an identity absent from the sidecar or naming a different plan, or a non-yes verdict fails with today's refusal behavior, the two sanctioned recoveries still named, plus the bound-receipt acceptance clause.
- The filename exec-review receipt remains accepted unchanged, and a rejected-state archive remains exempt unchanged.
- The writer side needs no change: staged plan-review records already carry the binding fields through the staging flow, and exec-series receipts keep their filename path; the residual writer-side text standardization is tracked in a filed backlog row.

Gate delta: one false-refusal class removed (a non-exempt archive whose reviews home holds a live, plan-review record bound to the shape-demanded raw-byte form with a passing verdict no longer refuses; priced by the witnessed closeout blocker the origin row records, whose closeout stopped after the work and its review were complete); the same change adds the acceptance arm to the existing archive gate and is its removal shape, threading the pre-archive path and raw bytes through the existing derivation as its implementation; the no-receipt refusal's remedy names the bound-receipt acceptance; directory-shape archives stay outside the arm's scope with their receipt demand unchanged (the recorded scope decision); no new gate, ledger, or receipt schema: the binding fields are the staging sidecar's existing fields, preserving the 2026-10-08 plan's no-schema-change contract.

## Assumptions

- assume the staging sidecar's existing fields are the binding evidence of record and no new receipt schema is needed; basis: `source_digest` is version-1-required, `extensions.plan_identity` is the skill-mandated staging convention for identity-qualified records staged through the --source-plan flow (the validator itself admits a legacy URL-or-Artifact fallback, which the arm declines by design), and the 2026-10-08 archive-ceremony plan fixed the receipt namespace while preserving "no receipt schema changes".
- assume the binding target is the reviewed revision's raw bytes (the witnessed workflow's dominant reachable form: the landing edit follows the last passing round, measured as 0 digest matches against archived bytes across 9 rounds of the witnessed 2026-10-17 completed plans), with the archived bytes accepted as the convergent no-edit form; a post-archive byte change still re-fails the archived-form comparison, and the box-completeness demand keeps reading the current archive text; for a staged rename the reviewed-revision form is the HEAD blob at the source, so an uncommitted post-review amendment riding the staged move is accepted on that form (this plan's recorded approximation decision: the form-naming warning makes the divergence visible); basis: the origin row's Expected section ("Preserve evidence that the exact final plan was covered") and the reproduced pre-landing-blob digest match on the witnessed corpus, which covers 2 of the 3 witnessed 2026-10-17 completed plans; the third's landing followed a citation-only post-review amendment whose re-bind round lacks a stats sidecar, and that plan keeps the exec-series path.
- assume the witnessed record is a plan-kind review round whose sidecar binds the plan: the arm's acceptance universe is plan-review rounds staged through the --source-plan flow, and the plan-bytes binding satisfies the origin's "final plan and implementation bytes" phrasing because the plan-review record is the completion evidence of record for the executed plan; basis: `compute_source_digest` binds plan-kind reviews to the exact document bytes, and the origin row's Problem section names a review recorded under a different artifact identity (its Evidence section records the observed closeout sequence), not a code-kind diff review.
- assume the writer side needs no change in this landing: the acceptance arm takes the origin row's Expected-section gate-recognition alternative, so the execute-plan-consistently-produces-a-separate-receipt alternative is not needed; the acceptance universe's records carry the binding fields through the staging flow, exec-series receipts keep their filename path unchanged, and the residual binding-text standardization is tracked in a filed backlog row; basis: the 2026-10-08 plan's namespace exclusion and the staging flow's required fields.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the bound-receipt acceptance fires only on a readable sidecar whose identity field matches the recovered pre-archive path (else the archive-state path), whose digest matches the raw-byte form the shape demands, and whose verdict reads yes; every mismatch class keeps today's refusal behavior with the two sanctioned recoveries still named and the bound-receipt acceptance clause, each pinned by its own test on an isolated temp home.
- compatibility: the gate library's existing suite passes with only contract-following test additions; the filename-series path and the rejected-state exemption are unchanged.
- docs parity: the gate's refusal remedy carries the new clause in this landing; the completion-evidence text stays out of scope with the residual tracked in the filed backlog row; the pins suite stays green.

**Done when:**
- a completed-state archive whose reviews home holds a record bound to the reviewed revision (or the archived bytes when the reviewed revision is unrecoverable) with a yes verdict passes the gate with the acceptance warning (test)
- a record whose digest matches neither raw-byte form still refuses with the two sanctioned recoveries and the bound-receipt acceptance named (test)
- a bound record beside an archive with an unchecked box still refuses at the box demand (test)
- a record whose sidecar identity is absent or names a different plan still refuses (test)
- a record whose sidecar verdict is no or absent still refuses (test)
- an unreadable or missing sidecar still refuses (test)
- a stale earlier round beside a binding latest round passes with the warning naming the binding record (test)
- the filename exec-review receipt path and the rejected-state exemption pass unchanged (test)
- the gate library suite, the pins suite, and the public hygiene scan all exit 0

**Ship when:**
- none; this repository is the release surface for its own scripts and skills.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done_sweep_gates_lib.py` *(modified)*
- `scripts/check_maintenance_pins.sh` *(modified)*

**Tests:**
- `scripts/test_done_sweep_gates_lib.py` *(modified)*

**Documentation and tracking:**
- `docs/history/backlog/2026-10-18-maintenance-pin-stale-schedule-ask-contract.md` *(deleted on completion)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/validate_review_staging.py` and the version-1 receipt schema; reason: the binding fields already exist and the 2026-10-08 plan fixed the no-schema-change contract
- the deferred legacy-filename sibling (`docs/history/backlog/deferred/2026-10-09-archive-ceremony-legacy-exec-review-name.md`); reason: that row owns an existing receipt under a legacy name, a different defect class
- `agents/skills/doing-code-review/SKILL.md` and the execute-plan completion-evidence text; reason: the writer side is adjudicated out of scope with the residual tracked in `docs/history/backlog/2026-10-17-archive-ceremony-writer-side-binding-text.md`, and the panel-of-record surface is plan-route-only

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_sweep_gates_lib.py -q
bash scripts/check_maintenance_pins.sh
```

The public hygiene scan (the user facts document's `public_hygiene_scan_script`) runs over the changed files and exits 0 before landing.

### Task 1: Thread the pre-archive path and raw bytes through the archive derivation

Context surface: the plan's Terms and this task.

Files:
- `scripts/done_sweep_gates_lib.py` *(modified)*
- `scripts/test_done_sweep_gates_lib.py` *(modified)*

Primary class anchors:
- `_derive_archived_plans` in `scripts/done_sweep_gates_lib.py`
- `gate_archive_ceremony` in `scripts/done_sweep_gates_lib.py`

- [x] The derivation threading delivers `pre-archive path evidence`: given a staged rename, a committed rename, and a stale-deliverables twin archive, expects each surfaced archive tuple to carry the pre-archive path (the rename source, the name-status old path, the deliverables rel; None for untracked additions) [class: IMPLEMENTATION_REQUIRED]
- [x] The derivation threading delivers `pre-landing path and raw bytes`: given a staged rename, a committed rename, and a stale-deliverables twin, expects each tuple to carry the pre-archive path and the raw bytes at its pre-archive state: the HEAD blob at the rename source for a staged rename, the rename commit's parent blob for a committed rename, None for a stale-deliverables twin [class: IMPLEMENTATION_REQUIRED]
- [x] The threading covers the addition shapes: staged and untracked additions carry the worktree raw bytes, the representation the staging flow certifies, committed additions carry the HEAD blob at the archive path with pre-archive path None, and this plan's recorded shape decision binds the stale-deliverables twin on the archived-bytes form alone [class: IMPLEMENTATION_REQUIRED]
- [x] Raw-byte reads: blob forms are captured bytes-mode (a binary blob read from git, never text-mode git show), worktree and index forms are read as raw bytes, and the tuple's decoded text is never re-encoded for digesting [class: IMPLEMENTATION_REQUIRED]
- [x] Degenerate-rename fixture: given a committed rename realized as delete-then-add in separate commits, with the run-manifest start commit seeded between the plan commit and the delete commit and the plan bytes amended between the boundary and the archive add by a small edit above the rename-detection threshold, expects the aggregate row to pair them [class: REPOSITORY_TEST]
- [x] Degenerate-rename disposition: on that fixture, expects the tuple to carry the name-status old path with raw bytes None, the reviewed revision unrecoverable and the record binding on the archived-bytes form alone, the base blob never an approximation [class: IMPLEMENTATION_REQUIRED]
- [x] The committed-rename fixture carries an intermediate post-review commit between the run boundary and the rename so the parent blob differs from the base blob, discriminating the parent-blob read from base-blob approximations [class: REPOSITORY_TEST]
- [x] The threading keeps a single consumer and owns its mechanical updates: the tuple change adds fields beside the existing archive path and text pair, and the task widens the gate's unpack sites, destructuring the new fields with loop behavior unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: the surfaced tuples carry no pre-archive path or raw bytes today [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `scripts: thread pre-archive evidence through the archive derivation` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Write the refusal-side witness suite

Context surface: the plan's Terms plus Task 1.

Files:
- `scripts/test_done_sweep_gates_lib.py` *(modified)*

Primary class anchors:
- `gate_archive_ceremony` in `scripts/done_sweep_gates_lib.py`

- [x] Every witness below runs on an isolated temp home fixture and pins one conjunct, holding the others constant [class: REPOSITORY_TEST]
- [x] Safety witness (record first): given a well-formed bound sidecar whose markdown record is absent, expects today's refusal (the half-pair fail-closed precedent) [class: REPOSITORY_TEST]
- [x] Safety witness (retired evidence): given a backup-infix or orphan-infix named pair, expects today's refusal [class: REPOSITORY_TEST]
- [x] Safety witness (digest mismatch): given a record whose sidecar identity matches while its digest matches neither raw-byte form, expects today's refusal with today's two sanctioned recoveries still named (the acceptance-clause assertion is added to this witness at Task 5) [class: REPOSITORY_TEST]
- [x] Safety witness (foreign identity): given a record whose sidecar digest matches the reviewed revision's raw bytes while its identity names a different plan, expects today's refusal [class: REPOSITORY_TEST]
- [x] Safety witness (sidecar identity absent): given a record whose sidecar lacks `extensions.plan_identity` while its markdown twin names the archived plan and its digest matches, expects today's refusal [class: REPOSITORY_TEST]
- [x] Safety witness (basename-only identity): given a record whose sidecar identity is the plan's bare basename while its digest matches the binding form and its verdict reads yes, expects today's refusal [class: REPOSITORY_TEST]
- [x] Safety witness (sidecar file absent): given a live record whose stats sidecar file is absent, expects the arm declining the candidate and today's refusal [class: REPOSITORY_TEST]
- [x] Safety witness (rejected twin): given a record whose sidecar identity names a same-basename path in the rejected archive state, expects today's refusal [class: REPOSITORY_TEST]
- [x] Safety witness (failing verdict): given a record whose sidecar verdict is no or absent, expects today's refusal [class: REPOSITORY_TEST]
- [x] Safety witness (decline, not blocker): given an unreadable sidecar on the candidate record, expects the arm declining that record and today's refusal; given a filename exec-review receipt present beside an unrelated malformed sidecar, expects the gate passing unchanged [class: REPOSITORY_TEST]
- [x] Safety witness (unchanged paths): given a filename exec-review receipt, expects acceptance unchanged; given a rejected-state archive, expects the exemption unchanged [class: REPOSITORY_TEST]
- [x] Scope witness (directory archive): given a directory-shape archive carrying a bound charter receipt, expects today's refusal, this plan's recorded scope decision [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: these witnesses pin today's refusals and unchanged paths against the current gate [class: REPOSITORY_TEST]

### Task 3: Write the binding-form witness suite

Context surface: the plan's Terms plus Tasks 1, 2, and 5.

Files:
- `scripts/test_done_sweep_gates_lib.py` *(modified)*

Primary class anchors:
- `gate_archive_ceremony` in `scripts/done_sweep_gates_lib.py`

- [x] Raw-byte witnesses: given a CRLF committed-addition plan reviewed raw then archived, whose record carries the archive-state identity and whose archive bytes route through the blob path, expects the arm to fire byte-exactly with the helper digest equal to the fixture file's sha256; given a committed archive whose worktree copy drifted after the landing commit, expects the digest to follow the certified blob; the fixture repo pins core.autocrlf=false with no text or eol attributes [class: REPOSITORY_TEST]
- [x] Multi-candidate witness: given a stale earlier round (digest bound to pre-amendment bytes) beside a binding latest round, expects the gate passing with the warning naming the binding record, the counted acceptance clause, and the digest form that matched; given a malformed-sidecar record beside a later binding record, expects the gate passing naming the binding record [class: REPOSITORY_TEST]
- [x] Shape witness (stale-deliverables twin): given a stale-deliverables archive whose only record carries the recovered deliverables-rel identity and binds the archived-bytes digest, expects the gate passing on the archived-bytes form with the counted acceptance clause [class: REPOSITORY_TEST]
- [x] Wrong-revision witness: given a committed rename whose only record binds the pre-amendment base-blob bytes, expects today's refusal [class: REPOSITORY_TEST]
- [x] Form-quantifier witness: given a rename archive whose record carries the pre-archive identity, a yes verdict, and a digest matching only the archived bytes, expects today's refusal [class: REPOSITORY_TEST]
- [x] Population witness (no recovery): given an untracked-addition archive whose record carries an identity naming the plan's former plans-root path and a matching archived-bytes digest, expects today's refusal, because the derivation recovers no pre-archive path for this shape and only the archive-state identity binds it [class: REPOSITORY_TEST]
- [x] Else-form witness: given a rename archive whose only record carries the archive-state identity with a matching digest and a yes verdict, expects today's refusal; given an untracked-addition archive whose record carries the archive-state identity with the archived-bytes digest and a yes verdict, expects the gate passing; the same binding on a committed-addition archive expects the gate passing [class: REPOSITORY_TEST]
- [x] Positive-witness identity forms: the acceptance fixture pins the pre-archive plans-root identity (the witnessed dominant form), with the archive-state-identity acceptance pins carried by the else-form witness's addition arms and the CRLF committed-addition raw-byte fixture, and the stale-deliverables shape witness pinning the twin's mixed-form binding (its identity the recovered deliverables rel, its digest the archived bytes) [class: REPOSITORY_TEST]
- [x] Run → expect RED: on these fixtures, the bound-receipt archive refuses today [class: REPOSITORY_TEST]
### Task 4: Write the drift, precedence, and environment witness suite

Context surface: the plan's Terms plus Tasks 1, 3, and 5.

Files:
- `scripts/test_done_sweep_gates_lib.py` *(modified)*

Primary class anchors:
- `gate_archive_ceremony` in `scripts/done_sweep_gates_lib.py`

- [x] Committed-drift witness: given a committed rename whose rename commit amends the plan bytes while a record binds the parent blob, expects acceptance with the divergence clause naming both digests, each equal to the fixture blobs' exact sha256 values [class: REPOSITORY_TEST]
- [x] Degenerate-rename witness: on the delete-then-add fixture, a record whose identity is the old path, whose digest is the archived bytes' exact sha256, and whose verdict reads yes expects the pass with the counted clause naming the archived-bytes form, while a base-blob-binding record refuses [class: REPOSITORY_TEST]
- [x] Precedence witness: given a bound record beside an archive carrying an unchecked box, expects today's unchecked-box refusal [class: REPOSITORY_TEST]
- [x] Staged-drift witness: given a staged rename whose staged archive text differs from the HEAD blob at the source while a record binds the blob, expects the gate passing with the divergence clause naming both digests; given a staged rename with no drift, expects the acceptance without the divergence clause [class: REPOSITORY_TEST]
- [x] Screening witness: given a bound record whose basename carries a control character and exceeds 64 characters, expects acceptance with the full screened basename rendered in the warning, distinguishing the no-truncation variant from the manifest helper's default truncation [class: REPOSITORY_TEST]
- [x] Environment witnesses: a nested reviews-home subdir record accepted with rglob parity, and a deferred-state archive whose record fully binds expecting the pass with the counted acceptance clause [class: REPOSITORY_TEST]
- [x] Normalization witness: given a record whose sidecar identity is a non-normalized posix equivalent of the recovered pre-archive path with matching digest and verdict, expects acceptance [class: REPOSITORY_TEST]
- [x] Run → expect RED on the acceptance arms (the precedence arm is GREEN today) [class: REPOSITORY_TEST]
### Task 5: Accept a digest-bound review receipt at the archive gate

Context: plan Tasks 1–4; backlog row `docs/history/backlog/2026-10-18-maintenance-pin-stale-schedule-ask-contract.md`.

Files:
- `scripts/done_sweep_gates_lib.py` *(modified)*
- `scripts/test_done_sweep_gates_lib.py` *(modified)*
- `scripts/check_maintenance_pins.sh` *(modified)*

Primary class anchors:
- `gate_archive_ceremony` in `scripts/done_sweep_gates_lib.py`
- `_has_exec_review_record` in `scripts/done_sweep_gates_lib.py`
- `stats_sidecar_path` in `scripts/validate_review_staging.py`
- `compute_source_digest` in `scripts/validate_review_staging.py`

- [x] The binding helper delivers `bound-receipt acceptance`: given a non-exempt archive (completed or deferred state) whose reviews home holds no filename-series receipt but holds a live plan-review record whose sidecar identity, raw-byte digest, and yes verdict bind it, expects the gate passing [class: IMPLEMENTATION_REQUIRED]
- [x] Acceptance predicate: the record is live (markdown twin present, no backup or orphan infix), its sidecar `extensions.plan_identity` equals the recovered pre-archive path (else the archive-state path), its `source_digest` equals the sha256 of the raw bytes at the reviewed revision (else at the archived state), and its sidecar `verdict` reads yes [class: IMPLEMENTATION_REQUIRED]
- [x] Candidate-set rule: the arm accepts when at least one live candidate fully binds, declining and continuing on every non-binding or unreadable candidate, and the acceptance warning names the accepted record [class: IMPLEMENTATION_REQUIRED]
- [x] The identity comparison normalizes both sides with the identity owner's posix form before equality, matching the validator's certified form [class: IMPLEMENTATION_REQUIRED]
- [x] Acceptance surfacing: expects the acceptance named in the pass message as a counted clause beside the checked and exempted counts, with the accepted record and its digest match named in a warning line that names which digest form matched (the reviewed-revision blob or the archived bytes) [class: IMPLEMENTATION_REQUIRED]
- [x] Drift surfacing: when the matched form's digest differs from the archive text's digest, the warning appends a divergence clause naming both digests and stating the amendment is unreviewed; the archive text's digest is sha256 over the tuple's captured raw bytes, never the decoded text re-encoded [class: IMPLEMENTATION_REQUIRED]
- [x] Warning screening: the warning renders the record's basename screened of control characters through the manifest-error screening helper's no-truncation variant, the variant reason recorded (record basenames exceed its default truncation) [class: IMPLEMENTATION_REQUIRED]
- [x] The binding helper is a sibling beside `_has_exec_review_record`, routing the digest leg through `compute_source_digest` over the captured raw bytes beside the shared sidecar path derivation; it reads only the sidecar's identity, digest, and verdict fields, each read minimal, and re-validates nothing else in the version-1 schema [class: IMPLEMENTATION_REQUIRED]
- [x] The helper routes the verdict leg through the declared single owner (`sidecar_verdict` / `VERDICT_VALUES`, the shared predicate of the validator and readiness scripts) and the live-record infix check through the imported `BACKUP_INFIX` and `ORPHAN_INFIX`, never inline literals [class: IMPLEMENTATION_REQUIRED]
- [x] Refusal remedy: the no-receipt refusal's remedy names the bound-receipt acceptance beside the existing two sanctioned recoveries [class: IMPLEMENTATION_REQUIRED]
- [x] The digest-mismatch witness now also asserts the bound-receipt acceptance clause named in the refusal remedy, completing the Done-when final state [class: REPOSITORY_TEST]
- [x] The precedence witness's recording double is installed against the landed helper and asserts zero calls on the box-refusal fixture [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN, with the registry and pin verification in the same step: no registry row or pin literal describes the archive gate's receipt acceptance narrowly enough to contradict the new arm (verified; edit nothing unless verification says otherwise) [class: REPOSITORY_TEST]
- [x] Commit: `scripts: accept digest-bound review receipts at the archive ceremony gate` [class: IMPLEMENTATION_REQUIRED]
- [x] Retarget the stale schedule-ask pin to the current contract phrase `list existing automations first`, preserving the neighboring never-executes-inline and owner-naming pins [class: IMPLEMENTATION_REQUIRED]
- [x] Re-run pins suite; expect exit 0 and `OUTCOME: pass` [class: REPOSITORY_TEST]
- [x] Run `git diff --check` [class: REPOSITORY_TEST]
- [x] Delete the backlog row; tidy `Cluster:` pointers [class: IMPLEMENTATION_REQUIRED]
- [x] Commit pin retarget + backlog deletion: `scripts: retarget stale schedule-ask pin`; name the backlog row as witness [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- docs/history/backlog/2026-10-17-archive-ceremony-review-evidence-mismatch.md: covered by this plan's archive-gate implementation and witness suite; the former backlog row is deleted in the plan archive transition.
- docs/history/backlog/2026-10-18-maintenance-pin-stale-schedule-ask-contract.md: covered by Task 5's pin retarget to the current scheduling contract; the former backlog row was deleted with that corrective task commit before this archive transition.
