# Plan: Java Construction and Interface Conventions

Backlog origin: `docs/history/backlog/2026-10-20-java-construction-and-interface-guidance.md`
Driving force: code-quality + simplicity
Plan review record: `.ai-playbook/reviews/2026-10-20-plan-review-java-construction-and-interface-conventions-r*.md`
Execution budget: 1.5h total, largest task 0.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-20-java-construction-and-interface-guidance.md (session session_4695ea47c31fb336fbb43a911def3161)

## Terms

- **Builder threshold:** the parameter count above which an object is created through a builder: strictly more than three constructor parameters. Three or fewer is a simple construction.
- **Simple construction:** creating an object through a constructor with three or fewer parameters; a builder there is a simplification finding.
- **Construction call site:** any expression that creates an instance of a type the rule covers, a constructor call or a builder chain, in production or test sources.
- **Framework-managed constructor:** a constructor the runtime container invokes itself to assemble a managed component (dependency injection, configuration binding); application code never calls it.
- **Framework-constructed data type:** a type a library instantiates reflectively from external data (a persistence entity, a deserialized transport model, a generated request model) and that therefore requires a specific constructor shape.
- **Lombok:** the Java annotation processor that generates builders, constructors, and accessors at compile time (`@Builder`, `@RequiredArgsConstructor`, `@Value`).
- **Top-level interface:** an interface declared directly in its own source file, not inside a class, record, enum, or another interface.
- **Shared Java guideline:** `projects/.ai-playbook/java_guidelines.md`, the numbered Java rule list consumer projects reference by number; deployed as `~/Projects/.ai-playbook/java_guidelines.md` through a symlink to this repository directory.
- **Java review overlay:** `agents/skills/doing-code-review/java-spring.md`, the language overlay appended to every Java review worker prompt; its "Review-wide Java checks" list names the shared rules workers apply to the complete diff.
- **Guideline Pack:** the per-review bundle of guideline paths plus section or rule hints that `doing-code-review` Step 2.5 assembles for workers.
- **Rule hint:** a Guideline Pack entry telling a worker which numbered rule sections to open.
- **Review lens:** a catalog under `agents/skills/review-agents/` loaded by a review worker; lenses stay language- and product-agnostic.
- **Portability checker:** `scripts/check_review_agent_portability.py`, which fails when a review lens carries a language or framework name (the words Java and Spring among them).

## Why

Consumer Java pull requests asked for builders on constructors with more than three parameters and for interfaces declared as top-level types, but the shared Java guideline has neither rule and the Java review overlay asks for neither check, so each review repeats a manual sweep of every created or changed type. The simplification lens also flags builders for "simple constructions" without saying how large a construction stops being simple, so it can contradict the requested rule.

## Gist & Examples

TLDR: add two numbered Java rules (builder above three constructor parameters, interfaces as top-level types) and wire them into the Java review overlay, the Guideline Pack hints, and the architecture and simplification lenses, for code quality; simplicity pays the growth by collapsing a duplicated hint range and a fragile count sentence.

Before: a reviewer sees `new ShipmentQuote(origin, destination, weightKg, serviceLevel, insured)` in a diff. No shared rule says this should read `ShipmentQuote.builder().origin(origin).destination(destination).weightKg(weightKg).serviceLevel(serviceLevel).insured(insured).build()`, the overlay does not ask the worker to look, and the simplification lens could flag a correctly introduced builder as "excessive method chaining". A `public interface Pricing` nested inside `ShipmentService` passes review unremarked.

After: `java_guidelines.md` #27 says a constructor with more than three parameters is built through a builder (Lombok `@Builder` on the class or record where Lombok is available, a hand-written static nested builder otherwise), while a framework-managed constructor keeps its plain or `@RequiredArgsConstructor` form and a framework-constructed data type keeps its required constructor with the builder as an addition. #28 says every interface is a top-level type. The overlay's Review-wide Java checks list names both rules with their owning lenses, both Guideline Pack hint paths (the Step 2.5 paragraph and the execute-plan mandatory-evidence bullet) route to that list, the simplification lens bounds its builder heuristic at three or fewer parameters and names the missing-builder direction as its own sub-pattern, and the architecture lens flags an interface declared inside another type.

Edge cases: a Spring component with five injected dependencies is never a builder candidate (the architecture lens's coupling heuristic owns it); a record with four components gets `@Builder` while its compact constructor keeps validation; a generated request model keeps its no-argument constructor and setters; a sealed interface whose permitted records are nested inside it is not a nested-interface finding (the rule constrains where an interface is declared, not what it may contain); a hand-written builder is a nested class, which #28 does not forbid; construction call sites in tests follow the same rule as production.

## Outcome

Java reviews receive and apply one shared construction convention and one interface-placement convention.

- A Java review worker is directed to rules #27 and #28 for every added or changed class, record, constructor, interface, and construction call site in the complete diff.
- The simplification lens keeps flagging builders on simple constructions and can no longer contradict the larger-constructor rule.
- The architecture lens flags an interface declared inside another type.
- Framework construction stays intact: no framework-managed constructor or framework-constructed data type is forced into a builder.

Gate delta: none. No gate, validator, lock, ledger, fence, or schema field is added or removed; the new overlay bullets and lens lines are non-blocking finding classes, not blocking review-layer duties. The overlay's growth is paid by deleting its count sentence in the same edit, and the two numeric hint ranges (the Step 2.5 paragraph and the execute-plan mandatory-evidence bullet) are replaced by references to the overlay list; the two lens additions (one bounded line and one named sub-pattern in the simplification lens, one line in the architecture lens) are the origin-requested review coverage itself, recorded here as net-new rule content with no paying deletion in those files.

## Assumptions

- Spring-managed constructor-injection types (components, services, configuration classes, configuration-properties constructor binding) are exempt from the builder requirement and keep a plain or Lombok `@RequiredArgsConstructor` constructor over `final` fields; more than three injected dependencies is a coupling signal for the architecture lens, never a builder candidate; basis: the container invokes the constructor itself so a builder is dead surface, the origin requires framework construction preserved, and `agents/skills/review-agents/architecture.md` already owns the coupling heuristic under Cohesion and Coupling.
- Framework-constructed data types keep the constructor their framework requires and gain a builder only as an addition for hand-written construction sites; basis: the origin's "without breaking framework construction".
- The Lombok pattern is `@Builder` on the class or record (records are supported by current Lombok releases), with the canonical or compact constructor keeping its validation; without Lombok the form is a hand-written static nested builder class, which rule #28 does not forbid because it constrains interfaces only; basis: the origin's "Lombok builder usage where available" and the sibling-project precedent the origin names.
- The threshold is strictly more than three parameters, so the simplification lens's simple-construction boundary is three or fewer; basis: the operator's stated rule in the origin.
- The Guideline Pack hint path is the Java paragraph of `doing-code-review` Step 2.5, which today carries the numeric range "#16 through #25", and the execute-plan Phase 3 mandatory-evidence bullet restates the same range for Java plans (the only two copies repo-wide, verified by grep on 2026-10-20); replacing both with a reference to the overlay's Review-wide Java checks list single-homes the rule set the way the Kotlin and Python arms already defer to their overlay tables; basis: those sibling arms and the repository single-homing rule in `AGENTS.md`.
- Construction-shape findings in both directions (a missing builder above the threshold, an unnecessary builder at or below it) are owned by the simplification lens, and the interface-placement finding by the architecture lens; basis: one lens owning both sides of the threshold cannot contradict itself, and `architecture.md` owns type-placement and module-boundary structure.
- The shared Java guideline file in this repository is the deployed copy: `~/Projects/.ai-playbook` resolves to `projects/.ai-playbook` through a symlink, verified 2026-10-20 with `readlink`; basis: that probe.
- No blocking validator is added; basis: the origin and the dispatch entry both reject it with the missing-incident absence named, and the Machinery admission protocol requires a witnessed incident.
- Rule #26 is absent from the overlay's Review-wide list today; this plan does not add it, because that is a separate rule's reachability and not this plan's goal; basis: the scope-extension tie-breaker (the origin does not name it).
- No page under `docs/` changes: the rules live in the shared guideline and the review skills, and no skill name, path, or usage changes; basis: the Documentation Impact routing table (new conventions go to the guideline, not `README.md`).
- The origin's "maintainability + simplicity" force maps to `code-quality` (primary) and `simplicity` (secondary) in the closed taxonomy; basis: the plans taxonomy and the same mapping in `docs/history/plans/2026-10-20-maintenance-occupied-target-fallthrough.md`.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: rule #27 states the threshold, the Lombok pattern, the framework-managed-constructor exemption, and the framework-constructed-data-type clause in one reading; rule #28 states the top-level requirement and what it does not constrain.
- consistency: the simplification lens's builder line names the three-or-fewer boundary and defers larger constructions to the language guideline; no lens line contradicts #27.
- reachability: the Java review overlay lists #27 and #28 with their owning lenses, and both `doing-code-review` Step 2.5 and the execute-plan mandatory-evidence bullet route Java rule hints to that list.
- portability: the portability checker and `scripts/test_review_agent_doors.py` exit 0 after the lens edits.
- hygiene: `bash scripts/scan-public-hygiene.sh` exits 0.
- text balance: the overlay deletes its count sentence in the same edit that adds two bullets; Step 2.5 shrinks.

**Done when:**
- The Validation Commands block exits 0 from the repository root.

**Ship when:**
- The reviewed change lands on the default branch through the normal plan closeout with the origin's covered disposition; class EXTERNAL_RELEASE_GATE, evidence owner the landing session, closed by the landing commit on the default branch.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Documentation:**
- `projects/.ai-playbook/java_guidelines.md`
- `agents/skills/doing-code-review/java-spring.md`
- `agents/skills/doing-code-review/SKILL.md`, the Step 2.5 Java paragraph only; all other sections are frozen, reject any finding that touches them
- `agents/skills/execute-plan/SKILL.md`, the Phase 3 mandatory-evidence bullet's Java clause only; all other sections are frozen, reject any finding that touches them
- `agents/skills/review-agents/simplification.md`, the `shrink:` checklist and the Other patterns section only; all other sections are frozen, reject any finding that touches them
- `agents/skills/review-agents/architecture.md`, the Package Organization list only; all other sections are frozen, reject any finding that touches them

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/agents-best-practices/SKILL.md`; provider-neutral by design and stays unchanged
- `agents/skills/doing-code-review/kotlin-spring.md` and `projects/.ai-playbook/kotlin_guidelines.md`; Kotlin conventions were not requested
- `projects/.ai-playbook/jvm_guidelines.md` and `projects/.ai-playbook/coding_guidelines.md`; neither holds a construction or interface rule, verified by grep on 2026-10-20
- `scripts/`; no validator or gate is admitted
- consumer product code; the plan edits shared guidance only

## Validation Commands

Validation preamble: the block below is fail-closed (every positive check aborts on miss; the forbidden-match sweeps split rg exit codes so only rc 1 passes, one invocation per file). Authoring-time record (2026-10-20, re-run after the round-1 fold, before round 2): `bash -n` over the block passed; executed against today's tree the block exits 1 at its first check, `rule 27 heading missing` (RED today); every positive probe was confirmed absent today (`Review-wide Java checks` in both skills, the two ownership phrases in the overlay, `three or fewer parameters`, `available in the build`, and `simplification#shrink-missing-builder` in the simplification lens, `architecture#nested-interface` in the architecture lens) and every forbidden sweep was confirmed present today (`#16 through #25` in both skills, the `These four` count sentence), so every probe flips exactly when its task lands; `bash scripts/check-no-em-dash.sh touched` rc 0; public-hygiene scan OUTCOME: pass; `python3 scripts/plan_readiness.py --pre-round` OUTCOME: pass, structural checks clean.

```bash
set -u
REPO="$(git rev-parse --show-toplevel)"
cd "$REPO"
rg -q '^## 27\. ' projects/.ai-playbook/java_guidelines.md || { echo "rule 27 heading missing"; exit 1; }
rg -q '^## 28\. ' projects/.ai-playbook/java_guidelines.md || { echo "rule 28 heading missing"; exit 1; }
rg -q 'java_guidelines\.md` #27' agents/skills/doing-code-review/java-spring.md || { echo "overlay #27 bullet missing"; exit 1; }
rg -q 'java_guidelines\.md` #28' agents/skills/doing-code-review/java-spring.md || { echo "overlay #28 bullet missing"; exit 1; }
rg -q 'Review-wide Java checks' agents/skills/doing-code-review/SKILL.md || { echo "Step 2.5 does not reference the overlay list"; exit 1; }
rg -q 'Review-wide Java checks' agents/skills/execute-plan/SKILL.md || { echo "execute-plan mandatory-evidence bullet does not reference the overlay list"; exit 1; }
rg -q 'construction shape \(#27, both directions\) to simplification' agents/skills/doing-code-review/java-spring.md || { echo "overlay ownership sentence missing #27"; exit 1; }
rg -q 'interface placement \(#28\) to architecture' agents/skills/doing-code-review/java-spring.md || { echo "overlay ownership sentence missing #28"; exit 1; }
rg -q 'three or fewer parameters' agents/skills/review-agents/simplification.md || { echo "simplification boundary missing"; exit 1; }
rg -q 'available in the build' agents/skills/review-agents/simplification.md || { echo "simplification generator-availability qualifier missing"; exit 1; }
rg -q 'simplification#shrink-missing-builder' agents/skills/review-agents/simplification.md || { echo "simplification missing-builder sub-pattern missing"; exit 1; }
rg -q 'architecture#nested-interface' agents/skills/review-agents/architecture.md || { echo "architecture nested-interface pattern missing"; exit 1; }
rg -n '#16 through #25' agents/skills/doing-code-review/SKILL.md; rc=$?
if [ "$rc" -eq 0 ]; then echo "stale Java hint range still present in Step 2.5"; exit 1; elif [ "$rc" -ge 2 ]; then echo "rg error rc=$rc"; exit "$rc"; fi
rg -n '#16 through #25' agents/skills/execute-plan/SKILL.md; rc=$?
if [ "$rc" -eq 0 ]; then echo "stale Java hint range still present in the execute-plan mandatory-evidence bullet"; exit 1; elif [ "$rc" -ge 2 ]; then echo "rg error rc=$rc"; exit "$rc"; fi
rg -n 'These four `jvm_guidelines.md` rules' agents/skills/doing-code-review/java-spring.md; rc=$?
if [ "$rc" -eq 0 ]; then echo "overlay count sentence still present"; exit 1; elif [ "$rc" -ge 2 ]; then echo "rg error rc=$rc"; exit "$rc"; fi
python3 scripts/check_review_agent_portability.py || { echo "portability checker failed"; exit 1; }
python3 scripts/test_review_agent_doors.py || { echo "door-pattern registry test failed"; exit 1; }
bash scripts/scan-public-hygiene.sh || { echo "public hygiene scan failed"; exit 1; }
echo "validation OK"
```

### Task 1: Add the construction and interface rules to the shared Java guideline

Context surface: the plan's Terms and this task; referenced, never restated.

Files:
- `projects/.ai-playbook/java_guidelines.md`

- [x] Append `## 27. Build Constructors With More Than Three Parameters Through a Builder` after rule 26, stating the threshold (strictly more than three parameters, judged per constructor, so a type with several constructors is read one constructor at a time) and the Lombok form: `@Builder` on the class or record covering its canonical constructor, with the canonical or compact constructor keeping its validation. [class: IMPLEMENTATION_REQUIRED]
- [x] In rule 27, state the no-Lombok form (a hand-written static nested builder class) and that construction call sites in production and test sources follow the same rule. [class: IMPLEMENTATION_REQUIRED]
- [x] In rule 27, state the framework-managed-constructor exemption: dependency-injection and configuration-binding constructors keep a plain or `@RequiredArgsConstructor` form over `final` fields, and more than three injected dependencies is a coupling signal for the architecture lens, never a builder case. [class: IMPLEMENTATION_REQUIRED]
- [x] In rule 27, state the framework-constructed-data-type clause: a type a library instantiates reflectively keeps the constructor it requires, and the builder is an addition for hand-written construction sites. [class: IMPLEMENTATION_REQUIRED]
- [x] Add one compact example to rule 27: a four-component record with `@Builder` and a compact constructor, beside a managed component with `@RequiredArgsConstructor` that the rule leaves alone. [class: IMPLEMENTATION_REQUIRED]
- [x] Append `## 28. Declare Every Interface as a Top-Level Type`: an interface is declared in its own source file, never inside a class, record, enum, or another interface; the rule constrains where an interface is declared, not what it may contain. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the edited guideline, expect the Validation Commands block's first two checks (the rule 27 and rule 28 headings) to pass and the public-hygiene scan to exit 0. [class: REPOSITORY_TEST]
- [x] Commit: `guidelines: add Java builder threshold and top-level interface rules`. [class: IMPLEMENTATION_REQUIRED]

### Task 2: Wire the Java review overlay and both Guideline Pack hint paths

Context surface: the plan's Terms and this task; referenced, never restated.

Files:
- `agents/skills/doing-code-review/java-spring.md`
- `agents/skills/doing-code-review/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`

- [x] In the overlay's Review-wide Java checks list, add a rule #27 bullet in the list's existing form (guideline file name, then rule number) directing workers to inspect every added or changed class, record, constructor, and construction call site in the complete diff for the builder threshold, the framework-managed exemption, and unnecessary builders on simple constructions. [class: IMPLEMENTATION_REQUIRED]
- [x] In the same list, add a rule #28 bullet in the same form directing workers to inspect every added or changed interface declaration for top-level placement. [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the list's ownership sentence with the exact phrases `construction shape (#27, both directions) to simplification` and `interface placement (#28) to architecture`. [class: IMPLEMENTATION_REQUIRED]
- [x] Delete the overlay sentence beginning `These four` that counts the listed JVM guideline rules, so the overlay's growth is paid in the same edit; the list's intro already binds workers to the complete diff. [class: IMPLEMENTATION_REQUIRED]
- [x] In `doing-code-review` Step 2.5, replace the numeric range `Add rule hints for Java rules #16 through #25` with a reference to the rules the overlay's Review-wide Java checks list names, keeping the trigger clause and the open-the-hinted-sections duty unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] In the execute-plan Phase 3 mandatory-evidence bullet, replace the clause `Java rules #16 through #25 for Java/Spring plans` with a reference to the rules the overlay's Review-wide Java checks list names, mirroring the bullet's own Kotlin and Python arms and leaving its recording and sufficiency sentences unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the edited overlay and both skills, expect the Validation Commands block's overlay, Step 2.5, execute-plan, and ownership-sentence checks to pass and both stale-range sweeps and the count-sentence sweep to find nothing. [class: REPOSITORY_TEST]
- [x] Commit: `review: route Java reviews to the construction and interface rules`. [class: IMPLEMENTATION_REQUIRED]

### Task 3: Reconcile the simplification lens and add the architecture check

Context surface: the plan's Terms and this task; referenced, never restated.

Files:
- `agents/skills/review-agents/simplification.md`
- `agents/skills/review-agents/architecture.md`

- [x] In the simplification lens's `shrink:` checklist, rewrite the line `Excessive method chaining: builder pattern for simple constructions` to name the boundary: a builder on a construction with three or fewer parameters; above that threshold the language guideline's construction rule governs. Use no language or framework names. [class: IMPLEMENTATION_REQUIRED]
- [x] In the same checklist, qualify the line `Hand-written code that Lombok can generate` with the exact phrase `available in the build`, so it fires only when the generator is on the build's classpath; a hand-written builder where no generator is available follows the language guideline's construction rule. [class: IMPLEMENTATION_REQUIRED]
- [x] Under the lens's Other patterns section, add the missing-builder direction as its own named sub-pattern line carrying `simplification#shrink-missing-builder`: a direct constructor call with more than three parameters where the language guideline's construction rule requires a builder; the `shrink:` tag's fewer-lines meaning does not cover this direction, so the sub-pattern slug names it. [class: IMPLEMENTATION_REQUIRED]
- [x] In the architecture lens's Package Organization list, add the line `Interface declared inside another type: declare it as a top-level type in its own source file; the language guideline owns the rule. Pattern: architecture#nested-interface`. Use no language or framework names. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the edited lenses, expect the portability checker and the door-pattern registry test (the two scripts the Validation Commands block runs) to exit 0 and the full block to print `validation OK`. [class: REPOSITORY_TEST]
- [x] Commit: `review-agents: bound the builder heuristic and flag nested interfaces`. [class: IMPLEMENTATION_REQUIRED]
