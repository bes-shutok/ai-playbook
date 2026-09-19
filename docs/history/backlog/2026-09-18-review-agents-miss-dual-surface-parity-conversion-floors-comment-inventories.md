# Backlog: review agents miss dual-surface parity, conversion floors, and relocatable comment inventories

Status: open
Priority: high

Workflow: backlog
Source: 2026-09-18 post-merge PR bot review on a long execute-plan + review-loop branch; six unresolved threads were shapes the internal panel and loop never staged. Fixes and lessons landed first; this item tracks corpus upgrades so the same miss classes do not recur.

## Problem statement

After many full-panel and focused review rounds (execute-plan Phase 3 and a later review-loop), an external PR reviewer still found three defect families that internal reviews had treated as closed or never staged:

1. **Dual-surface policy asymmetry.** The same deny/allow policy existed at two call paths (for example transport parse vs domain validate). One path used a strict predicate; the other used a weaker shape (exact token vs substring marker). Direct callers of the weaker path bypassed the stronger gate. Plan and testing work had already covered "equivalence" for the primary path; they did not require a mechanical predicate-shape diff across both surfaces.

2. **Unit-conversion floor before a sink that treats zero as unlimited.** Config validation rejected zero and negative durations and capped maxima, but accepted positive sub-unit values. Downstream code truncated to whole milliseconds for a session timeout API that treats `0` as "no limit." The bound disappeared silently.

3. **Relocatable identifier inventories in operator comments.** Headers and runbooks restated versioned filenames (or equivalent relocatable labels) that the same change set already listed in mounts or resource paths. A renumber updated the real path and left the comment inventory stale. Disposition that worked: delete the inventory and point at the owning artifact, not rewrite the label forever.

These are not one-off product quirks. They are abstract miss classes for agent review instructions.

## Why the internal loops let them out (hypotheses with evidence shape)

| Miss class | Likely lens owner | Why current instructions under-fire |
|------------|-------------------|-------------------------------------|
| Dual-surface policy asymmetry | correctness / architecture / testing | Workers verify each surface in isolation ("validator exists", "parser matrix covers markers"). No mandatory probe: "list every entry point that enforces policy P; diff the predicate implementations byte-for-byte or by shared helper." Plan "equivalence" language is easy to satisfy with tests on one surface only. |
| Conversion floor at sink | implementation / Java-Spring overlay / risk | Guideline pack already stresses `@ConfigurationProperties` positivity and Duration types, not truncating converters (`toMillis`, `toSeconds`, integer casts) before sinks where zero means unlimited or disabled. Sub-unit positives look "valid" under `isZero()` / `isNegative()` checks. |
| Relocatable comment inventories | documentation / contract-docs | Documentation lens already flags restating "what" and decision duplication across docs. It does not specifically require: for every added comment that names a versioned path, enum ordinal, or migration id, check whether that identifier also appears as a real path or mount in the same diff; prefer pointer over inventory. Operator prose is often kept as "normative instructions," which protects stale inventories. Severity policy marks most documentation findings Low; clear-round exit is blocking-zero, so Lows are soft-dropped under round budget. |

Aggravators that are process-shaped, not product-shaped:

- Long branches with many high-attention concurrency / harness findings starve attention for quiet cross-file consistency.
- Fresh-adversarial rounds still inherit Review Scope and prior-finding context; quiet files that "already passed" get skimmed.
- External bots often run cheap cross-file string/consistency heuristics without the same scope bias; that is a useful adversarial signal, not proof the internal panel is useless.

## Exact locations to change (skills / guidelines corpus)

Do not hardcode service, ticket, or PR identifiers into the corpus. Target these homes:

1. `review-agents/architecture.md` or `review-agents/quality.md`: new pattern for **dual-surface invariant parity**.
2. `review-agents/testing.md`: require witnesses that fail when either surface weakens the shared predicate (shared helper preferred).
3. `doing-code-review/java-spring.md` (and Kotlin Duration notes if present): **truncating conversion floor** before sinks where zero means unlimited.
4. Shared `jvm_guidelines.md` already gained a Duration/`toMillis` floor rule and a "do not keep perpetual absent-path asserts" rule from learn; ensure the overlay **points at those rule numbers** in the mandatory Guideline Pack hints so workers apply them on every Java review, not only after the next incident.
5. `review-agents/documentation.md` phase 2: explicit gate for **relocatable identifier inventories** in comments and operator docs (point to owner; do not copy the list). Align with shared `coding_guidelines.md` family-D rule on relocatable identifiers in comments (added the same learn pass).
6. `review-agents/severity-calibration.md` and/or `doing-code-review` assessment: when a comment inventory contradicts a path in the same diff, classify as **correctness/operability drift** (Medium), not optional prose Low, because operators will follow the wrong file.
7. Optional: `review-panel-selection.md` targeted follow-up trigger: after a migration renumber or dual-entry validation change, force documentation + correctness on the paired surfaces even in a focused round.

## Suggested fix (smallest corpus update)

### A. Dual-surface policy parity (correctness / architecture / testing)

Add a pattern such as `architecture#dual-surface-policy-parity` (name can be refined):

**Trigger:** the diff adds or changes a deny-list, allow-list, marker set, or normalization used for the same policy at more than one public entry point (parser, validator, filter, gateway, batch importer).

**Required worker action:**

1. Enumerate every entry point that claims to enforce the policy.
2. Compare predicate shape (exact equality vs contains/prefix; normalization steps; shared vs duplicated constant sets).
3. Prefer one shared helper; if duplication remains, stage a finding unless tests prove both surfaces reject the same representative inputs (including the asymmetry examples: compound tokens that pass exact match but fail contains, or the reverse).

**Testing obligation:** at least one failing witness per surface when the shared helper is mutated to the weaker shape.

### B. Truncating conversion floor (Java/Kotlin overlay + implementation)

**Trigger:** config or API `Duration` / floating time is validated then rendered with `toMillis()`, `toSeconds()`, or integer cast into a sink documented (or known) to treat zero as unlimited, disabled, or "no timeout."

**Required worker action:**

1. Trace validation → conversion → sink.
2. Reject values whose converted integer is less than the sink's minimum meaningful unit (usually `1`), even when the `Duration` is positive.
3. Cite the shared JVM guideline on Duration floors when present in the Guideline Pack.

### C. Relocatable identifier inventories (documentation)

**Trigger:** added or changed comment/doc line lists versioned filenames, migration ids, enum ordinals, or other identifiers that also appear as real paths, mounts, or resource names in the same diff.

**Required worker action:**

1. Prefer delete + pointer to the owning artifact ("see mounts in compose", "see SQL file header").
2. Do not "fix" by rewriting the inventory to the new label unless the comment is the sole operator contract and cannot point elsewhere.
3. Severity: when the inventory contradicts a path in the same diff, treat as Medium operability drift, not Low optional prose.

### D. Process hygiene (execute-plan / review-loop)

- When Phase 3 or review-loop exits clean, do not treat external PR-bot threads as surprising if the three triggers above were never exercised; use them as corpus feedback (this item).
- After accepting an external finding in one of these families, run receiving-review **Agent corpus feedback** / **Generalize-on-fix** in the same session (this backlog is that capture).

## Acceptance

- [ ] Architecture/quality (or equivalent) lens documents dual-surface policy parity with trigger, required compare step, and shared-helper preference.
- [ ] Testing lens requires a cross-surface witness when dual entry points enforce the same policy.
- [ ] Java (and Kotlin if applicable) overlay documents truncating conversion floors before zero-means-unlimited sinks and points at the shared JVM guideline number.
- [ ] Documentation lens phase 2 adds relocatable-identifier inventory gate; severity calibration promotes same-diff contradiction to Medium.
- [ ] A short adversarial checklist example (language-agnostic) is included so workers can self-test without product names.
- [ ] Optional: panel-selection targeted follow-up trigger for renumber / dual-validation diffs.

## Non-goals / privacy

- Do not paste service names, ticket ids, PR numbers, hostnames, account ids, or payload field inventories into the skill bodies beyond abstract examples (`emailAddress`-style compound tokens as generic marker examples are fine; real customer or env data is not).
- Do not require cloning an external bot's full heuristic set; only close the three miss classes above.

## Related

- Shared guidelines already updated in the incident learn pass: JVM Duration floor / skipTests vs surefire.skip / drop perpetual absent-path asserts; coding guideline on relocatable identifiers in comments. This backlog is the **review-agent wiring** so those rules are probed, not only written.
- Sibling backlog themes: review-staging synthesis friction; verification fixture teardown (process), not the same defect family.
