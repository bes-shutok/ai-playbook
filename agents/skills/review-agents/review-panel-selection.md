# Review Panel Selection

Single source for which review sub-agents launch or skip. All orchestrators (`doing-code-review`, `review-plan`, `rfc-design`, `review-confluence-doc`) reference this file; do not duplicate skip/launch prose inline.

## Default panels

| Context | Default agents | Conditional agents |
|---------|----------------|-------------------|
| Code review | `quality`, `implementation`, `testing`, `simplification`, `documentation`, `architecture`, `security` (7) | `concurrency`, `premortem` |
| Plan review | Same 7 shared + inline `consistency` (8) | `concurrency`, `premortem` |
| RFC Light | `quality`, `implementation`, `security`, `architecture`, `simplification`, `documentation` + inline consistency (7) | `concurrency` |
| RFC Full | All 7 shared + inline consistency (8) | `concurrency` (always), `premortem` (heuristics) |
| Confluence doc | `documentation` (prose pass always), `premortem` when matched | Step 4.6 code lenses per `review-confluence-doc` |

Prepend `severity-calibration.md` for code review sub-agents only.

## Manual overrides

User args bypass heuristics when explicit:
- `include premortem` / `include concurrency` → launch even if heuristics say skip
- `skip premortem` / `skip concurrency` → skip even if heuristics say launch
- `only check X` → honor per caller focused-review rules

Record launch/skip rationale in staging doc `## Metadata` `Domains:` (comma-separated tags).

## Conditional: `premortem`

**Opt-in.** Launch when **any** domain tag or diff signal matches:

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

## Conditional: `concurrency`

**Opt-in.** Scan **all changed files** (not diff hunks only) for:

| Signal | Examples |
|--------|----------|
| Transactional scope | `@Transactional`, `@Lock`, `FOR UPDATE`, isolation level config |
| Synchronization | `synchronized`, `ReentrantLock`, `Mutex`, virtual-thread pinning risks |
| Retry / backoff | `RetryTemplate`, `@Retryable`, 429 mapping, circuit breakers |
| Messaging / async | Kafka/RocketMQ consumers, outbox workers, `@Async`, thread pools |
| Shared mutable state | Cross-request caches with TTL races, compare-and-set upserts, deque queues shared across threads |

**Default skip** when none match in changed files or their direct call paths visible in the diff.

**execute-plan override:** When the caller is `execute-plan` Phase 3 and plan Review Scope / Domains include concurrency, transactional mutators, `FOR UPDATE`, or race ITs, **launch premortem** even on "quiet" clear-streak rounds unless the user said `skip premortem`. Clear-streak silence is not a skip signal (lock-duration miss when premortem was skipped on a quiet clear-streak round).

## `documentation` agent: two-phase execution

The merged `documentation.md` agent runs **one or two phases** per launch:

1. **Missing-docs phase** : always when the artifact has user-visible, architectural, or plan-tracking doc impact.
2. **Prose-clarity phase** : only when human-readable prose was added or modified (same scope as legacy prose-clarity skip inverse).

**Skip entire agent** only when: internal refactor with no user-visible change **and** no prose in diff/plan/RFC body.

Pattern tags:
- Missing docs: `documentation#missing-<slug>`
- Prose issues: `documentation#prose-<slug>`
- Deprecated alias (orchestrator accepts, do not emit new): `prose-clarity#<slug>`

Prose findings default to **Low** unless paired with normative contract drift (then severity follows owning agent).

## Tiered ownership (dedup, not discard)

Ownership boundaries affect **which agent leads a dedup group**, not silent discard of a different fix at the same site.

| Finding type | Lead agent | Others: do not duplicate same root cause |
|--------------|------------|------------------------------------------|
| Runtime logic bug, wrong algorithm, edge case | `quality` | `implementation`, `architecture` |
| Missing wiring, incomplete feature, return propagation, API schema drift | `implementation` | `quality`, `architecture` |
| Layer violation, god class, DDD/CQRS breach | `architecture` | `quality`, `implementation` |
| Missing or weak test | `testing` | `quality` (unless test passes while impl is wrong) |
| Config/env incomplete for feature to work | `implementation` | `premortem` (unless rollout blast radius) |
| Cross-service contract unset | `premortem` (when launched) | `quality`, `implementation` |
| Missing user-facing docs | `documentation` (missing-docs phase) | all |
| Redundant/verbose prose | `documentation` (prose phase) | `quality`, `simplification` |

**Hard rule:** When two agents report the **same root cause**, merge into one staged finding; pick the lead agent above.

**Exception:** When two agents report **different fixes** at the same site (e.g. wiring vs runtime behavior), stage one finding with both fixes or keep the higher-severity agent's finding; do not discard the behavioral angle.

### Plan `consistency` agent ownership

**Must report:**
- Design Invariants / Glossary vs Task step contradictions
- Cross-task format mismatches, stale task cross-refs, eval-criteria vagueness
- Naming drift across tasks

**Do not report:**
- Source-code algorithm correctness (quality)
- Missing tests (testing)
- Wiring gaps in existing codebase (implementation)
- Security vulnerabilities (security)

Invariant-vs-task contradictions stay with `consistency` even when they sound like quality bugs.

## Recording wrong-owner discards

When tiered ownership merges duplicate root causes, discard non-lead agent returns with reason `wrong-owner` (not `duplicate`). In staging **Notes** and sidecar `lead_agent`, name the lead agent from the ownership table. This enables weekly aggregation: high `wrong-owner` count for an agent suggests merging that lens into the lead agent.

