# Review Panel Selection

Single source for which review workers launch, which lenses they load, and when a focused or escalated panel is valid. All orchestrators (`doing-code-review`, `review-plan`, `rfc-design`, `review-confluence-doc`) reference this file; do not duplicate panel policy inline.

## Recommended five-worker panel

Normal full code, plan, and RFC reviews launch exactly these workers:

| Worker | Required lenses | Conditional lenses | Owns |
|--------|-----------------|--------------------|------|
| `correctness-completeness` | `quality`, `implementation` | none | Runtime correctness, requirement coverage, wiring, compatibility |
| `testing` | `testing` | none | Test strategy, discriminating assertions, failure paths |
| `design-simplicity` | `architecture`, `simplification` | none | Dependency direction, maintainability, unnecessary structure |
| `contract-docs` | `documentation` | `consistency` for plans and RFCs | Contracts, source-of-truth drift, prose, cross-section consistency |
| `risk` | `security` | `concurrency`, `premortem` when signals below match | Security, ordering, rollout, and operational failure modes |

Prepend `severity-calibration.md` to every worker prompt. Each worker records every loaded lens. Pattern IDs retain the originating lens prefix.

## Launch accounting

- A worker is one launched sub-agent. Every descendant sub-agent is an additional worker.
- Worker returns declare `descendant_launches`; use an empty list when none launched.
- Flatten every descendant into staging Panel accounting with its `parent_worker`.
- Review workers must not launch nested review sub-agents. Premortem personas are independent reasoning sections inside `risk`.
- The hard ceiling is six actual launches per review pass, including descendants.
- At most one optional sixth escalation worker may launch in an active review run. Record `escalation_reason`; a second escalation is prohibited until a new run begins.
- The sixth worker requires an independent high-risk domain that cannot be covered credibly by `risk`, or an explicit user request. Do not use it for routine breadth.

## Focused panels

A narrow review may launch fewer than five workers when the artifact and user request do not need a full panel. Record `panel_mode: focused` and `selection_reason`.

Common focused panels:

- docs-only prose: `contract-docs`, plus `correctness-completeness` when prose specifies normative behavior;
- test-only change: `correctness-completeness`, `testing`;
- narrow security review: `correctness-completeness`, `testing`, `risk`;
- explicit `only check X`: the worker that owns X, plus correctness when the requested review can affect behavior.

Do not label a focused panel as a full review.

## Manual overrides

User args bypass lens heuristics when explicit:
- `include premortem` / `include concurrency` -> load that lens in `risk`
- `skip premortem` / `skip concurrency` -> do not load that conditional lens
- `only check X` -> honor the focused-panel rules

Record selection and conditional-lens rationale in staging Metadata.

## Conditional `premortem` lens

Load inside `risk` when any domain tag or diff signal matches:

| Signal | Examples |
|--------|----------|
| `cross-service` | BFF calling multiple backends, shared catalog contracts, event ingestion vs consumer |
| `auth` | RBAC, JWT, API keys, service-to-service auth surfaces |
| `infra-config` | K8s/Helm, datasource rollout, broker autostart, env-specific YAML |
| `rollout` | Feature flags, migration ordering, backward-incompatible deploy steps |
| `concurrency` | See concurrency signals below (premortem also launches when concurrency launches) |
| `new-public-api` | New REST/OpenAPI endpoints, published SDK contracts |

**Default skip** when none match:
- Localized feature code in one module
- Docs-only or comment-only diffs
- Deletion / simplify sweeps with no behavioral change
- Test-only PRs

Do **not** use changed-line count alone as a skip gate.

## Conditional `concurrency` lens

Scan all changed files, not diff hunks only, for:

| Signal | Examples |
|--------|----------|
| Transactional scope | `@Transactional`, `@Lock`, `FOR UPDATE`, isolation level config |
| Synchronization | `synchronized`, `ReentrantLock`, `Mutex`, virtual-thread pinning risks |
| Retry / backoff | `RetryTemplate`, `@Retryable`, 429 mapping, circuit breakers |
| Messaging / async | Kafka/RocketMQ consumers, outbox workers, `@Async`, thread pools |
| Shared mutable state | Cross-request caches with TTL races, compare-and-set upserts, deque queues shared across threads |

**Default skip** when none match in changed files or their direct call paths visible in the diff.

**execute-plan override:** When Phase 3 scope includes concurrency, transactional mutators, `FOR UPDATE`, or race ITs, load `premortem` in `risk` even on quiet follow-up rounds unless the user said `skip premortem`.

## `documentation` lens: two-phase execution

The `contract-docs` worker runs one or two documentation phases:

1. **Missing-docs phase** : always when the artifact has user-visible, architectural, or plan-tracking doc impact.
2. **Prose-clarity phase** : only when human-readable prose was added or modified (same scope as legacy prose-clarity skip inverse).

In a focused panel, skip `contract-docs` only for an internal refactor with no user-visible change and no prose in the reviewed artifact.

Pattern tags:
- Missing docs: `documentation#missing-<slug>`
- Prose issues: `documentation#prose-<slug>`
- Deprecated alias (orchestrator accepts, do not emit new): `prose-clarity#<slug>`

Prose findings default to `Low` unless the tangible consequence rules in `severity-calibration.md` justify promotion.

## Tiered ownership (dedup, not discard)

Ownership boundaries affect which worker and lens lead a dedup group, not silent discard of a different fix at the same site.

| Finding type | Lead worker | Lead lens |
|--------------|-------------|-----------|
| Runtime logic bug, wrong algorithm, edge case | `correctness-completeness` | `quality` |
| Missing wiring, incomplete feature, return propagation, API schema drift | `correctness-completeness` | `implementation` |
| Layer violation or excessive structure | `design-simplicity` | `architecture` or `simplification` |
| Missing or weak test | `testing` | `testing` |
| Config incomplete for feature to work | `correctness-completeness` | `implementation` |
| Cross-service, security, concurrency, or rollout failure | `risk` | closest loaded risk lens |
| Missing user-facing docs or prose issue | `contract-docs` | `documentation` |
| Plan or RFC internal contradiction | `contract-docs` | `consistency` |

**Hard rule:** When two agents report the **same root cause**, merge into one staged finding; pick the lead agent above.

**Exception:** When two agents report **different fixes** at the same site (e.g. wiring vs runtime behavior), stage one finding with both fixes or keep the higher-severity agent's finding; do not discard the behavioral angle.

### Plan and RFC `consistency` ownership

**Must report:**
- Design Invariants / Glossary vs Task step contradictions
- Cross-task format mismatches, stale task cross-refs, eval-criteria vagueness
- Naming drift across tasks

**Do not report:**
- Source-code algorithm correctness (quality)
- Missing tests (testing)
- Wiring gaps in existing codebase (implementation)
- Security vulnerabilities (security)

Invariant-vs-task contradictions stay with the `consistency` lens even when they sound like quality bugs.

## Recording wrong-owner discards

When tiered ownership merges duplicate root causes, discard non-lead returns with reason `wrong-owner`, not `duplicate`. Record `lead_worker` and `lead_lens`.
