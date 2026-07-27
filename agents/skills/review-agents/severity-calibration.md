# Severity Calibration

Canonical severity, blocking, ordering, and output-budget rules for every review worker and orchestrator. Severity reflects tangible consequence, not comment length, reviewer effort, or document inconsistency alone.

**Upstream pattern:** adapted from [umputun/cc-thingz](https://github.com/umputun/cc-thingz) planning exec review prompts; deep links in `skill-upstream-catalog.md` **Merged pattern index**. Mapped to this repo's four-tier model below.

## Required on every finding

1. Set `severity` explicitly to one of: `Critical`, `High`, `Medium`, `Low`.
2. When uncertain after applying the decision procedure, choose **`Low`** (same default as upstream `MINOR` when no tag is present).
3. Set `blocking` independently from severity.
4. Include `consequence`, `reachability`, `blast_radius`, and `confidence`.
5. Explain why the consequence meets the selected tier.

Orchestrators may **upgrade** or **downgrade** after verification; record deltas in staging **Severity calibration** with a reason tied to this file.

## Tier definitions

| Tier | Tangible consequence |
|------|----------------------|
| **Critical** | Immediate, broad, and severe deployment, availability, security, data, or financial harm on an expected path |
| **High** | Likely wrong behavior, incompatible contract, data loss, or security exposure on a normal or enabled path |
| **Medium** | Reachable edge-case failure, meaningful rework, or ambiguity with two plausible implementations and a concrete harmful outcome |
| **Low** | Clarity, naming, formatting, optional completeness, simplification, test, metric, comment, or document issue without demonstrated behavior impact |

**Critical vs High:** use `Critical` only when harm is both broad and immediate on an expected path. Use `High` when harm is material but narrower or depends on an enabled path.

## Decision procedure (apply in order)

1. **Wrong outcome for users or data?** (money, PII, auth, persisted state, API contract violated in happy path) → **High** or **Critical** (step 1 split above).
2. **Security exposure?** Untrusted input reaches dangerous sink without validation → **High** minimum; **Critical** if trivially exploitable in production config.
3. **Crash, panic, or unrecoverable error on common path?** → **Critical** if on deploy/startup; **High** if on typical request handling.
4. **Behavior wrong only in a reachable edge case, race, or documented limitation?** -> `Medium` unless the demonstrated consequence meets `High`.
5. **Underlying behavior correct; gap is tests, metrics, docs, naming, or simplification?** -> `Low`.
6. Still unsure -> `Low`.

## Blocking decision procedure

`blocking` answers one question: **must this be remediated before the artifact is safe to execute, merge, or release?** It is independent from severity. A Low can block (rare but real: a tiny contract typo that would ship an incompatible API); a Critical can be non-blocking (a severe issue in code that is not yet wired into any call site). Set `blocking: true` only when leaving the finding unresolved creates concrete risk in the next step the artifact enables.

Apply in order; the first match wins:

1. **Execution or merge would produce wrong behavior on a normal path?** → `blocking: true`. (Code: a defect reachable in the happy path. Plan: a task whose stated steps would not achieve its acceptance criteria. RFC: a design whose stated mechanism would not satisfy its requirements. Document: instructions that, if followed, cause wrong behavior.)
2. **Execution or merge would break a contract other components or consumers rely on?** → `blocking: true`. (API signature change without migration; schema change without backfill; config key rename without fallback; cross-skill contract drift where one skill references a field or path another skill no longer emits.)
3. **Execution or merge would remove a guard against a real failure mode?** → `blocking: true`. (Removing the only test for a data-loss path; deleting a validation step; weakening a security check; removing a rollback step from a migration plan.)
4. **Execution or merge would deploy an untested or unverifiable change?** → `blocking: true` when there is no way to confirm correctness after the fact (no reproducer, no assertion, no canary). Otherwise non-blocking.
5. **The finding improves quality but the artifact is safe to execute/merge without it?** → `blocking: false`. (Clarity, naming, optional completeness, simplification, additional tests for already-guarded paths, documentation polish.)

### Examples by review type

**Code review** (`doing-code-review`):
- Blocking: a null dereference on a request-handling path; an API response field renamed without a compat shim; deletion of the only assertion guarding a money-movement path.
- Non-blocking: a variable name that could be clearer; a missing test for a path already guarded elsewhere; a simplification opportunity.

**Plan review** (`review-plan`):
- Blocking: a task whose validation command does not actually verify the task's claim; a task that contradicts an earlier task's contract; a missing rollback step in a migration plan.
- Non-blocking: a task that could be split more cleanly; a phrasing improvement; an optional extra test.

**RFC / design review** (`rfc-design`):
- Blocking: a design whose stated mechanism fails its own acceptance criteria; an interface that is incompatible with an existing consumer; a rollout plan with no rollback.
- Non-blocking: a section that could be clearer; an accepted risk that should be recorded; a suggestion to add an optional metric.

**Document review** (`review-confluence-doc`):
- Blocking: instructions that cause wrong behavior when followed; a procedure that contradicts the actual system contract; a runbook step that would escalate rather than mitigate an incident.
- Non-blocking: prose clarity; formatting; an optional diagram; a term that could be expanded on first use.

### Interaction with severity and readiness

- `blocking` never overrides `severity` and vice versa; set each independently using its own procedure.
- **Readiness** keys only on blocking: a review is clean when zero unresolved findings have `blocking: true`. Resolved findings (`triage: done` or `dropped`) no longer block, regardless of severity.
- A non-blocking finding may still be worth fixing before merge when its tangible consequence is high; that is a judgment call for the author, not a readiness gate.

## Category defaults

| Finding type | Default | Promote to Medium when | Promote to High/Critical when |
|--------------|---------|------------------------|--------------------------------|
| **Simplification / yagni / over-engineering** | Low | Complexity hides a correctness bug or makes a safe fix impossible | (rare) abstraction causes active data loss |
| **Metrics / observability** | Low | Missing telemetry masks an active production problem on a hot path | (essentially never) |
| **Missing test** | Low | Untested path is the **only** guard for a real failure mode (blast-radius bound) | Untested path allows data loss or security bypass |
| **Documentation / inline comment** | Low | Two plausible implementations plus a realistic harmful outcome | Following it likely causes wrong normal-path behavior or an incompatible contract |
| **Prose clarity** | Low | (none) | (none) |
| **Concurrency / race** | Medium | Race window achievable under stated TTL/load; verify I/O cost before claiming | Data loss or double-spend in achievable window → **High** |
| **Security** | High | (none) | Trivial exploit → **Critical** |
| **Feature-flag gated bug** | Same as ungated | Flag does **not** reduce severity; judge impact when flag is on |
| **Wrong module / endpoint error code** (typed 4xx, wrong `ApiError` ownership) | Low if only naming and clients ignore `code` | Integrators or shared handlers key on `code`, or sibling endpoint docs document a different code for the same failure shape → **Medium** | Wrong code causes incorrect client retry/alert routing on a normal path → **High** |
| **Catalog-loop N+1** (per-key repo read; bulk API exists) | Low when N is tiny and local | Hot path or catalog expected to grow beyond a handful of keys → **Medium** | (rare) unbounded catalog without pagination causes availability harm → **High** |

**Pre-existing pattern** does not reduce severity of **new** code introduced by this PR. Note pre-existing instances as EXISTING debt at **Low** or omit (`doing-code-review` §4.11).

**NEW vs EXISTING debt:** structural/size findings on files this PR only touched lightly → downgrade to **Low** or omit.

## Upstream mapping (cc-thingz)

| cc-thingz tag | Typical local severity |
|---------------|------------------------|
| `CRITICAL` | `Critical` or `High` (use decision procedure) |
| `MAJOR` | `Medium` or `High` |
| `MINOR` | `Low` |
| (missing tag) | `Low` |

## Document calibration

Document inconsistency alone is `Low`. Promote to `Medium` only when the reviewer names two plausible implementations and a realistic harmful outcome. Promote to `High` only when following the text is likely to cause wrong normal-path behavior or a materially incompatible contract.

## Ordering

Group findings in this exact order: `Critical`, `High`, `Medium`, `Low`.

Within each group order by:

1. `blocking: true` before `false`;
2. `blast_radius`: `global`, `multi-service`, `single-service`, `local`;
3. `reachability`: `expected`, `common`, `plausible-edge`, `theoretical`;
4. `confidence`: `verified`, `strong-evidence`, `hypothesis`;
5. finding ID ascending.

## Finding budget

Every worker fully expands:

- every `Critical`, whether blocking or not;
- every finding with `blocking: true`;
- up to five additional non-blocking `High` or `Medium` findings;
- up to two additional non-blocking `Low` findings.

Additional credible non-blocking candidates use the compact overflow manifest defined by `review-staging`. This budget controls presentation, not detection.

## Worker output

Return JSON findings with the required fields above, `pattern`, evidence anchor, and concrete remediation. Also return `descendant_launches`, normally `[]`.

**Depth by severity** (orchestrator `doing-code-review` §4.12): `Medium+` needs four Comment sections; `Low` needs claim + evidence + suggestion.

## Orchestrator synthesis

When merging duplicate findings from multiple agents, stage the **highest** verified severity unless evidence supports downgrade (record in **Severity calibration**).

**Readiness:** a review is clean only when no unresolved finding has `blocking: true`. Do not infer readiness from severity alone.
