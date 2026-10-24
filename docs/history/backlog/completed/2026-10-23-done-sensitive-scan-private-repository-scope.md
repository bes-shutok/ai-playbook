# Backlog: scope sensitive-content scanning by repository visibility

- **Filed:** 2026-10-23
- **Status:** covered
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** operator-feedback
- **Class:** fix-class
- **Driving force:** correctness
- **Severity:** high; a private repository can have a valid staged change blocked by public-artifact patterns solely because its project type is unrecognized.
- **Cluster:** `docs/history/backlog/2026-10-11-done-sensitive-scan-neutral-token-assignment.md` (shared mechanism: done sensitive-data content gate; this item is profile-scope policy, not a credential-pattern false positive).
- **Source:** observed during a private repository closeout on 2026-10-23; the content scan rejected valid internal tracker links.

## Problem

The done sensitive-data scan exempts company projects and private pet projects from its content arms, but keeps scanning other private repositories when their facts do not resolve to those exact profiles. A repository explicitly marked private can therefore be blocked by public-artifact patterns even though the policy intent is that private repositories do not run the sensitive-content scan.

## Expected

Treat an explicit `artifact_visibility = "private"` as sufficient to skip both sensitive-content scan arms, independent of `project_type`. Preserve the non-content protections (commit-attribution audit and skills-repository hygiene arm) unless the established policy says otherwise. Keep the content scan active for public, absent, malformed, or unrecognized visibility values, and add regression coverage for private repositories with absent and recognized project types.

## Evidence

- `scripts/done_sweep_gates_lib.py`, `gate_sensitive_data_scan`: `profile_exempt` currently requires `project_type = "company"`, or `project_type = "pet"` with private visibility; other profiles populate both content pattern families.
- `docs/history/plans/completed/2026-10-12-done-sensitive-scan-profile-boundary.md`, Outcome and Edge cases: the previous change intentionally limited the exemption to company and private-pet profiles and kept unrecognized project types strict.
- The 2026-10-23 consumer closeout was blocked on valid internal tracker links in a repository whose facts declared private visibility but did not declare `project_type`.

## Dedup probe

The completed 2026-10-12 profile-boundary plan covers the earlier company/private-pet direction, but explicitly leaves unrecognized project types strict. `docs/history/backlog/2026-10-11-done-sensitive-scan-neutral-token-assignment.md` covers a credential-pattern false positive in parser code, not visibility-based content-scan scope. This item records the newly broadened operator direction rather than reopening either prior defect unchanged.

## Suggested direction

Derive the content-arm exemption from an explicitly private visibility value alone; keep other gate arms unchanged. Test the visibility boundary across private, public, absent, malformed, and unrecognized values, including that the non-content arms still run for private repositories.

## Covered

Covered by the execution landing of docs/history/plans/completed/2026-10-23-done-sensitive-scan-private-repository-scope.md (exec r2 ready=yes 0 blocking; landing commit on main 2026-10-24). Residual carried forward from the 2026-10-12 profile-boundary plan, now widened to every repository: the content arms are the only content backstop and landed history is never re-audited after a later visibility flip to public, so a declaration-trusted private exemption can hold credentials silently; the landed lib comment documents the declaration-trust consequence.
