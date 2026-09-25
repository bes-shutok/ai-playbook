# Plan: Proactive Lessons-Recall Hook + Skill-Gate Hook

Revision history (delta + outcome per revision; full detail in the cited reviews):

- **r8** (user-approved): Claude keys on `CLAUDE_CODE_SESSION_ID`; Codex/Cursor/agy use PID-walk via `os.getppid()` (PID-recycling caveat accepted); `#same_session_pair` demoted to sanity selftest; Task 7 LIVE per-adapter write-then-read is the sole B1 gate; LOUD keying mode. Folded mediums: HEAD-truncate, cold-start FileNotFoundError, makedirs-before-stat, byte-identical `project` hash, settings.json `Write|Edit|MultiEdit` matcher in-scope + doctor checks registration, `Lesson #N` format + real-corpus budget, bounded `dedup_concurrent`.
- **r9**: DROPPED the uncomputable r8 PID-walk; session DERIVATION moved to adapter-layer `session_channel.py` (NOT the core); Claude keys via the helper -> `--session-id`; Codex/Cursor/agy run PROJECT-ONLY as DOCUMENTED STEADY STATE; `project = sha1(<repo anchor>).hexdigest()[:16]` replaces `sha1(realpath(cwd)).hexdigest()[:16]` so in-repo cwd navigation no longer false-blocks. Kept r8 mediums.
- **r10**: USER DECISIONS - (1) `session_channel.py` as a shared `scripts/` MODULE, subprocess-invoked (cores NEVER import it); (2) COLLAPSE the halved-window steady state to ONE full window for ALL agents. Bounded the repo-anchor walk-up at `git rev-parse --show-toplevel`; `.hexdigest()[:16]` fix; empty-string `--session-id` treated as absent. Applied M3-M11 + L1-L8.
- **r11**: Fixed 2 r10 Blockers. B1: the `no-anchor` fallback `sha1(realpath(cwd))` was cwd-unstable WITHIN a worktree -> permanent FALSE BLOCK; fallback is now `sha1(realpath(git_toplevel))`, `no-anchor` fires ONLY in non-git dirs. B2: the `session_channel.py` install model was contradictory (no Task performed it -> silent exit 127); pinned the literal `ln -sf` install + doctor verifies every abspath. Also applied the r10 mediums/lows.
- **r12**: r11 reached 0 Blockers; folded the 8 r11 Mediums into a shared `resolve_project_key`
  (M1, Family-D code-duplication collapse), install `mkdir -p` (M2), doctor covers the 2 cores (M3,
  11 paths), Claude empty-SID alarm (M4), Codex config-file gate (M5), forced-collision
  `FileExistsError` selftest (M6), plus r11 lows. Detail in Tasks and the r12 Amendments table.
- **r13**: r12 review raised 1 Blocker (the M1 "dead code" rationale was false - `<facts-file-dir>` is `<toplevel>/.ai-playbook`, one dir deeper; corrected to the honest Family-D + r11-inconsistency rationale) and 8 Mediums; r13 corrects the rationale, moves `#project_single_source` into each core's own `--selftest` (downward import only), broadens the git-failure exception spec, pins the `FileExistsError` catch at the call site, adds `~/.ai-playbook/scripts/` to mkdir+doctor, and adds Install+Doctor subsections to both READMEs.
- **r14**: r13 reached 0 Blockers; the r13 review raised 5 Mediums led by a CONVERGENT finding
  (`TimeoutExpired` omitted from the catch tuple). r14 collapses the catch to
  `(subprocess.SubprocessError, OSError)`, drops the dead `no_anchor` flag (resolver logs
  `keying=no-anchor` itself; return now `-> str`), pins the sibling-import `sys.path` bootstrap in
  both cores, adds the lessons_recall behavioral selftest, and puts the full literal `ln -sf` block
  in both READMEs. Detail in the r14 Amendments table.
- **r15**: r14 reached 0 Blockers; the r14 review raised 4 Mediums led by a CONVERGENT finding: the
  M3 "resolver logs `keying=no-anchor` itself" change routed the token to the WRONG SINK
  (`logging.warning` -> stderr, discarded by the adapters). r15 makes the resolver write `no-anchor`
  DIRECTLY to `hooks.log`, narrows the core's vocabulary to `env-var|project-only`, and tightens both
  selftests to assert the FILE. Detail in the r15 Amendments table.
- **r16**: r15 reached 0 Blockers; a CONVERGENT cold-start finding (4 agents): the resolver's
  `os.open(O_CREAT)` does not makedirs the logs dir -> `no-anchor` (and the core's own keying lines)
  swallowed on a fresh install. r16 adds makedirs+`O_NOFOLLOW`+newline to both write sites, bumps the
  doctor count, and folds the security/testing/doc Lows. Detail in the r16 Amendments table.
- **r17**: r16 reached 0 Blockers but 6 Mediums (diverged from r15's 3 - the fold added surface).
  r17 collapses the root cause STRUCTURALLY rather than re-stating the recipe: one shared
  `_append_hooks_log_line` helper, one `RESOLVER_GIT_TIMEOUT_S` constant, sink-fix stated once, the
  third agy assumption, and absent-parent arms on both writers. Detail in the r17 Amendments table.
- **r18**: r17 reached 0 Blockers / 3 Mediums (halved), all surfaced by measuring the new structure.
  r18 makes the shared helper serialize-defensively (`default=str`), pins the core absent-parent arm to
  a git-repo cwd, fixes the last stale README timeout literal, and scopes the constant-lockstep claim
  to its Python consumers. Detail in the r18 Amendments table.
- **r19**: r18 reached 0 Blockers / 2 Mediums (both prose-clarity, both in the helper bullet) + 1
  substantive Low (the serialize over-claim). r19 rewrites the helper body recipe-first with compact
  single-sentence rationale clauses and scopes the serialize claim honestly. Detail in the r19
  Amendments table.
- **r20**: r19 reached 0 Blockers / 1 Medium / 3 Low. The Medium was a broken pointer from the r19
  trim; r20 corrects it and folds the prose Lows. r20 itself reached 0 Blockers / 0 Medium / 2 Low
  (both prose bookkeeping, folded). Detail in the r20 Amendments table.
Plan review: ai-playbook/docs/reviews/2026-07-03-plan-review-lessons-recall-hook-r20.md (r20: READY - 0 Blocker / 0 Medium / 2 Low; the r19 broken-pointer Medium closed (SRP pointer now cites r18 row 4), 2 prose-bookkeeping Lows folded)
Plan review: ai-playbook/docs/reviews/2026-07-03-plan-review-lessons-recall-hook-r19.md (r19: Not ready - 0 Blocker / 1 Medium / 3 Low; SRP/extraction-trigger pointer cited r17 Amendments but the project_key.py trigger lives in r18 row 4, SERIALIZE clause 78w vs claimed ~45w, r19 header bullet 61w, realistic-scalar enumeration duplicated (accepted cross-boundary) folded into the r20 revision)
Plan review: ai-playbook/docs/reviews/2026-07-03-plan-review-lessons-recall-hook-r18.md (r18: Not ready - 0 Blocker / 2 Medium / 4 Low; SERIALIZE-DEFENSIVELY paragraph 112w run-on, helper body 290w wall of text, "can never escape" over-claim (circular / __str__-raises escape; bytes sub-claim FALSE), SRP-home parenthetical restates Amendments, r18 header bullet 69w folded into the r19 revision)
Plan review: ai-playbook/docs/reviews/2026-07-03-plan-review-lessons-recall-hook-r17.md (r17: Not ready - 0 Blocker / 3 Medium; README Doctor subsection stale >=6/5s literal, core absent-parent selftest arm non-discriminating non-git cwd, shared helper json.dumps TypeError escapes try/except OSError violating NEVER-raises + silent agy gate-off folded into the r18 revision)
Plan review: ai-playbook/docs/reviews/2026-07-03-plan-review-lessons-recall-hook-r16.md (r16: Not ready - 0 Blocker / 6 Medium; core keying write lacks a cold-start absent-parent selftest arm, doctor check (5) cross-refs "two existing agy assumptions" the Monitor still lists as two, makedirs+open+write duplicated across resolver and core with no shared helper, resolver/doctor/README timeout triple a prose lockstep not a named constant, r16 header bullet 143w, r15-M1 sink-loss story restated at ~9 sites folded into the r17 revision)
Plan review: ai-playbook/docs/reviews/2026-07-03-plan-review-lessons-recall-hook-r15.md (r15: Not ready - 0 Blocker / 3 Medium; resolver os.open(O_CREAT) does not makedirs the logs dir -> cold-start FileNotFoundError swallows no-anchor + core keying lines, r15 header bullet 109w, doctor count FOUR not bumped to FIVE folded into the r16 revision)
Plan review: ai-playbook/docs/reviews/2026-07-03-plan-review-lessons-recall-hook-r14.md (r14: Not ready - 0 Blocker / 4 Medium; no-anchor token routed to wrong sink (logging.warning->stderr, not hooks.log), project_filename_uses_resolver fixture non-discriminating, Codex verified-file recording missing from README, agy timeout unpinned folded into the r15 revision)
Plan review: ai-playbook/docs/reviews/2026-07-03-plan-review-lessons-recall-hook-r13.md (r13: Not ready - 0 Blocker / 5 Medium; TimeoutExpired escapes the catch tuple, sibling modules not path-bootstrapped, dead no_anchor flag, lessons_recall missing behavioral selftest, README defers ln -sf as prose folded into the r14 revision)
Plan review: ai-playbook/docs/reviews/2026-07-03-plan-review-lessons-recall-hook-r12.md (r12: Not ready - 1 Blocker / 8 Medium; M1 'dead code' rationale false, selftest reverses dependency direction, mkdir omits scripts dir, FileExistsError catch placement ambiguous, git-binary-missing unhandled, doctor readlink-f dangle semantics, README install+doctor scope folded into the r13 revision)
Plan review: ai-playbook/docs/reviews/2026-07-02-plan-review-lessons-recall-hook-r6.md (r6: Not ready - 1 Blocker / 6 Medium; worktree Blocker closed by home-anchored marker, but session-id write/read asymmetry opened a new brick (B1, resolved Option A this r7), r5-M5 resolve_table_key repo-first + r5-M2 held-back machinery + r5-L4 WRITE-RECIPE wording carried forward, body-equality guard unreachable, dedup state file path-isolated, marker mkdir/perms, stale rebuttals folded into this r7 revision)
Plan review: ai-playbook/docs/reviews/2026-07-02-plan-review-lessons-recall-hook-r5.md (r5: Not ready - 1 Blocker / 9 Medium; worktree Blocker - .ai-playbook gitignored so cwd-relative tmp_dir unresolvable in worktrees, dedup suppression predicate, cross-session discriminator, resolve_table_key order, doctor model-agnostic, RECALL_DEDUP_WINDOW, selftest-name drift, field-name misstatement folded into the r6 revision)
Plan review: ai-playbook/docs/reviews/2026-07-02-plan-review-lessons-recall-hook-r4.md (r4: Not ready - 0 Blocker / 5 Medium; marker cwd reverted to strict realpath equality (tmp_dir is cwd-relative), None-handling pinned, budget ranker cardinality, dedup_concurrent bounded count, single-source narrowed, carve-outs replaced by explicit family order folded into this r5 revision)
Plan review: ai-playbook/docs/reviews/2026-07-02-plan-review-lessons-recall-hook-r3.md (r3: Not ready - 0 Blocker / 7 Medium; marker second-signal dropped, de-dup read-side in-memory, C/H carve-out, marker realpath, SKILL.md/AGENTS.md placement folded into the r4 revision)
Plan review: ai-playbook/docs/reviews/2026-07-01-plan-review-lessons-recall-hook-r2.md (r2: Not ready - 1 Blocker / 9 Medium; facts-path format split + marker/de-dup/concurrency/contract fixes folded into the r3 revision)

## Terms

- **UserPromptSubmit / PreToolUse**: Claude Code hook events. UserPromptSubmit fires on every
  prompt and can inject context; PreToolUse fires before a tool call and can allow/block.
- **additionalContext**: the context-injection field. Claude wraps it as
  `{"hookSpecificOutput":{"hookEventName":"...","additionalContext":"..."}}`; Codex emits flat
  `{"additionalContext":"..."}`.
- **Family tag**: a `**Principle:** Family <A-H>` line in a lessons corpus entry. The tags ARE
  the recall index.
- **Lesson-shape classifier vs prompt classifier** (B1 fix): `lessons_migrate._matches_family_vocab`
  classifies a LESSON ENTRY's shape against `FAMILY_KEYWORDS` (lesson-descriptive phrases like
  "silent drop", "single source of truth") for migration routing. It does NOT classify a user
  prompt's intent - its phrases are not things users write, so it silently no-ops on real prompts
  (verified empirically: 7 of 7 realistic prompts returned None). Hook 1 therefore uses a NEW
  `classify_prompt(prompt) -> tuple[str, list[str]] | None` (returns `(family_letter, matched_phrases)`
  or None, same return shape as `_matches_family_vocab`) keyed on user-intent vocabulary (lemmas +
  inflections + domain shapes). The two classifiers are distinct; do not conflate them.
- **Adapter**: a thin per-agent shell wrapper around an agent-agnostic Python core. Text in,
  agent-protocol envelope out.
- **Skill-gate marker** (r6 home-anchored redesign; supersedes the r5 cwd-relative/tmp_dir design,
  which was silently OFF in git worktrees - see r5 Blocker 1): a receipt file the plans skill
  writes/refreshes on EVERY plan-file write (not only create-only Phase 0) to prove it ran RECENTLY
  in THIS project AND THIS session, checked by the skill-gate hook. The marker lives at a
  HOME-ANCHORED path that is ALWAYS present regardless of cwd or worktree:
  `~/.ai-playbook/runtime/skill-invoked/plans.<project>.<session>.marker`.
  - `project` derivation (r12-M1 collapse; r13 corrects the rationale and return shape; r11-B1
    supersedes r10/r9/r8-M2; r10-M3 hexdigest fix - bare `sha1(...)[:16]` is a `TypeError` on the
    non-subscriptable `_hashlib.HASH` object). ONE shared resolver,
    `facts_paths.resolve_project_key(start_dir) -> str`, returning `project_hash` ONLY; BOTH
    cores (`skill_gate.py`, `lessons_recall.py`) IMPORT and CALL it (they do NOT re-implement the
    derivation - the "duplicated VERBATIM across both cores" Family-D obligation collapses to one
    function object; see `#project_single_source`). stdlib-only, agent-agnostic leaf; it composes the
    git-toplevel resolution + sha1 hexdigest. Algorithm:
    1. Invoke git via `subprocess.run(['git','-C',start_dir,'rev-parse','--show-toplevel'],
       capture_output=True, text=True, timeout=RESOLVER_GIT_TIMEOUT_S)` (list-form argv; `shell=False`;
       NEVER
       f-string-interpolate `start_dir` into a shell command string). `start_dir` is a literal path
       argument.
    2. If git SUCCEEDS (exit 0): return `sha1(realpath(toplevel))[:16]`. NOTE
       (r13 corrects the false r12-M1 "dead code" rationale): the in-worktree facts-file search is
       DROPPED for project derivation because (a) collapsing to the toplevel anchor removes the
       `project` derivation duplicated VERBATIM across both cores (Family-D code duplication - single
       source of truth); (b) it ALSO removes an r11 inconsistency where a normal checkout (facts present) keyed
       on `sha1(realpath(<toplevel>/.ai-playbook))` but a worktree-without-facts keyed on
       `sha1(realpath(toplevel))`, giving DIFFERENT keys for the same repo - `<facts-file-dir>` is
       `<toplevel>/.ai-playbook` (one dir deeper), NOT `toplevel`, so the two hashes DIFFER; the
       collapse yields ONE stable key per repo. The resulting key value differs from the r11
       facts-file-keyed value, but the feature is GREENFIELD (the runtime state dir
       `~/.ai-playbook/runtime/skill-invoked/` does not yet exist; no marker/state files have ever
       been written), so no state is orphaned. Facts resolution is STILL used for `plans_dir`
       CLASSIFICATION (a different question; `resolve_plans_dir` and facts-path resolution stay in
       `facts_paths.py` - only the project hash no longer consults the facts file).
    3. If git FAILS - nonzero exit (non-git dir), the binary absent (`FileNotFoundError`/
       `PermissionError`), or a timeout - then `anchor = os.path.realpath(start_dir)`, and the resolver
       calls `_append_hooks_log_line({"ts": <iso8601 utc>, "keying": "no-anchor"})` BEFORE returning
       (it is the sole place that knows the git-failure branch fired). The catch is
       `(subprocess.SubprocessError, OSError)`: `SubprocessError` covers BOTH `CalledProcessError`
       (nonzero exit, if `check=True`) AND `TimeoutExpired` (the resolver's git invocation firing after
       `RESOLVER_GIT_TIMEOUT_S`; NFS-mounted repo, locked `index.lock`, gpgsign prompt); `OSError`
       covers `FileNotFoundError`/`PermissionError` on the git binary. `resolve_project_key` NEVER
       raises (so the gate's fail-open policy does not need to cover this path).
    - **`_append_hooks_log_line(payload)` (r17 shared helper; the SINGLE contract home for the
      `hooks.log` write - both the resolver's `no-anchor` line and the core's `env-var`/`project-only`
      line call it; restated NOWHERE else).** Lives in `facts_paths.py` (stdlib-only, already imported
      by both writers; its sole leaf caller `resolve_project_key` lives there). The SRP tradeoff and the
      `project_key.py` extraction trigger are recorded in the r18 Amendments table (row 4), not restated
      here. Body: `os.makedirs(Path.home()/".ai-playbook"/"logs", exist_ok=True, mode=0o700)`, then
      `os.open(<that>/hooks.log, O_WRONLY|O_CREAT|O_APPEND|O_NOFOLLOW, 0o600)`, then ONE
      `os.write(fd, (json.dumps(payload, default=str) + "\n").encode())`; the makedirs, the open, AND
      the write are ALL wrapped in ONE `try/except OSError` and SILENT on failure (never raises).
      Defensive choices (each one sentence; the load-bearing rationale):
      (1) **SERIALIZE-DEFENSIVELY (r18-M3, Family B):** `default=str` is REQUIRED - bare
      `json.dumps` raises `TypeError`/`ValueError` (NOT `OSError`) on a non-serializable field (a caller
      passing `datetime.now()` for `ts`), which escapes the silent-catch, violates NEVER-raises, and on
      agy disables the gate. `default=str` covers the realistic non-serializable scalars
      (`datetime`/`Path`/`bytes`); a circular payload or a value whose `__str__` raises still escapes and
      is the caller's responsibility to keep literals-only (PRECONDITION: `payload` is an acyclic dict of
      str-coercible-without-raising values), not silently swallowed.
      (2) **Makedirs in the SAME except (r17-L1):** the `try/except OSError` MUST cover makedirs too -
      a read-only `~/.ai-playbook/` parent makes makedirs raise `PermissionError` (the correct
      silent-loss outcome); narrowing to `except FileNotFoundError` re-raises and violates NEVER-raises.
      (3) **TOCTOU (r18-L6):** a concurrent deletion of `logs/` between makedirs and open loses the line
      silently - observability-only, gate unaffected, acceptable in the single-user trust boundary.
    - **Why the helper writes DIRECTLY to the file (r15-M1 sink fix + r16-M1 cold-start fix, stated
      ONCE):** (a) the resolver must NOT use `logging.warning` - a stdlib-only leaf has NO handler
      installed, so `logging.warning` routes to `logging.lastResort` -> STDERR, which the adapters
      DISCARD; the token is silently lost in production and a `logging`-record selftest false-passes
      while the file stays empty. Writing DIRECTLY to `hooks.log` is the only route that survives
      adapter stderr-discard. (b) The `os.makedirs` FIRST is required because `O_CREAT` creates the
      file but NOT its parent dir; on a fresh install `~/.ai-playbook/logs/` is absent and the bare
      `os.open` raises `FileNotFoundError`, which the silent catch swallows -> the token is lost on the
      exact cold-install path r15 was meant to protect (mirrors the r8-M4 makedirs-before-stat
      discipline used for `runtime/skill-invoked/`). (c) `O_NOFOLLOW` refuses a pre-planted symlink at
      the leaf. (d) `O_APPEND` offset-atomicity + the single sub-4096-byte `write()` of the `+ "\n"`
      line keep concurrent resolver/core appends non-interleaving and parseable line-by-line.
    - **Threat model (r17-L2/L5/L6, unchanged framing):** the payload is literals-only (no
      user/secret data; no `start_dir`/`toplevel`/`--session-id` interpolation); the target derives
      from the hook process's own `HOME` (trusted single-user environment); assumes `~/.ai-playbook/`
      is not itself a symlink (the single-user trust boundary is breached if it is). The write does NOT
      change the "consent reminder, not a security boundary" framing - `~/.ai-playbook/` is the 0o700
      single-user trust boundary.
    - **`RESOLVER_GIT_TIMEOUT_S = 5` (r17 named constant, in `facts_paths.py`):** the SINGLE source
      for the resolver's `subprocess.run(..., timeout=RESOLVER_GIT_TIMEOUT_S)`, the doctor's
      `timeout > RESOLVER_GIT_TIMEOUT_S` bound (check (5)), and the README's
      `timeout >= 2 * RESOLVER_GIT_TIMEOUT_S` recipe. This constant IS the lockstep for the Python
      consumers (resolver, doctor) and the `#doctor_agy_timeout` selftest (all import
      `facts_paths.RESOLVER_GIT_TIMEOUT_S`, so a rename/move breaks them loudly at import time). r18-L5
      HONEST-SCOPING: the README install recipe is PROSE, not import-checked - its literal integer must
      still be HAND-SYNCED when the constant changes (the doctor backstops a stale install value with a
      FAIL, so this is a usability regression, not a silent-correctness one); the prior unqualified
      prose lockstep note is removed only for the Python sites.
    4. `project = hashlib.sha1(anchor.encode()).hexdigest()[:16]` (the returned `project_hash`).
       On the git-failure branch the resolver writes the `keying=no-anchor` line to `hooks.log`
       (step 3) BEFORE returning this cwd-derived hash.
    REALPATH RULE (resolves quality-F2 bound-comparison ambiguity): `anchor =
    os.path.realpath(toplevel or start_dir)`; if any walk is retained for `plans_dir`, both operands
    of the bound comparison are realpath'd.
    KEY CHANGE vs r10 (resolves B1 + M5): the fallback when a worktree has no facts file is
    `sha1(realpath(toplevel))`, NOT `sha1(realpath(cwd))`. `keying=no-anchor` fires ONLY in the true
    non-git-dir case, so it is genuinely rare/alarming (an external worktree - no facts file - keys
    on `sha1(realpath(git_toplevel))` and does NOT fire `no-anchor`, since `git rev-parse` succeeds).
    This closes the r8 false-block where same-repo different-cwd produced different hashes (Family C)
    WITHOUT introducing the r9 cross-repo aliasing (Family H - `.ai-playbook/` is gitignored, so an
    external worktree contains no facts file and an unbounded walk-up would alias every sibling repo
    to ONE ownership hash). PER-PROJECT isolation holds ONLY when the anchor resolves WITHIN the
    worktree.
    NON-GIT INSTABILITY (r12-L4): in a non-git directory tree, `project` is cwd-derived and therefore
    UNSTABLE across `cd` within the tree; if you edit plans across subdirs of a non-git scratch dir,
    expect blocks. Treat any `keying=no-anchor` line as a real signal, not steady state.
  - `session = sha1(<adapter-supplied channel value>).hexdigest()[:16]` (r10-M3 hexdigest; r11-M3:
    the emptiness check is the FIRST operation, before any hashing - see "Session value is
    SANITIZED"). The adapter passes `--session-id`; Claude = `CLAUDE_CODE_SESSION_ID` (via the shared
    helper, see Session key), Codex/Cursor/agy = helper returns empty -> adapter OMITS `--session-id`
    -> core keys the literal `no-session`. An empty-string `--session-id` (after strip) is treated
    IDENTICALLY to absent -> `no-session` (r10-M4: a literal empty would hash to the constant
    `da39a3ee5e6b4b0d` and silently bypass the `keying=project-only` log line - r11-M2: pure log
    metadata, not an alarm). SANITIZED to hex so a hostile env var like
    `CLAUDE_CODE_SESSION_ID="../foo"` cannot traverse the runtime dir - r8-M6.
  - Acceptance: the gate looks up the marker by the SAME `(project, session)` it derives, and accepts
    iff the marker file EXISTS AND `0 <= (now - mtime) <= SKILL_GATE_WINDOW` (default 14400s / 4h,
    FLAGGED; r10-M10: ONE full window for ALL agents - the halved-window steady state is COLLAPSED).
    A future-dated/zero mtime is STALE (block), not a perpetual allow.
  - The marker BODY stores the writer's `os.path.realpath(cwd)` AND the resolved repo-anchor path as
    FORENSIC/debug metadata ONLY - it is NOT a checked guard (r7-M4: the identity check is encoded in
    the FILENAME components, so the body is retained only to aid diagnosis).
  - RATIONALE: home-anchored storage eliminates the worktree hole (`.ai-playbook/` is gitignored, so
    `<worktree>/.ai-playbook/facts.md` is absent and a cwd-relative tmp_dir cannot be resolved there -
    r5-B1); the repo-ANCHORED `project` (bounded walk-up to `.ai-playbook/facts.md` within the git
    worktree) locates the repo root for the key. PER-PROJECT isolation comes from the `project`
    filename component (two repos read different files). PER-SESSION isolation comes from the
    `session` component (Claude only at v9; a fresh Claude marker from session A does NOT admit
    session B's writes in the same repo - r6).
  - Runtime dir + perms: `~/.ai-playbook/runtime/skill-invoked/` is created by the skill on first
    write with `os.makedirs(..., exist_ok=True, mode=0o700)` and the marker file is written `0o600`
    (r7-L4, mirrors the lessons-recall store). The GATE also does a benign
    `os.makedirs(dir, exist_ok=True, mode=0o700)` BEFORE its `os.stat`, so a missing dir on a fresh
    install cannot fail-OPEN the gate via `FileNotFoundError` (an OSError) - the absent-marker branch
    is always reachable, faithful to "absent marker ALWAYS blocks" (r8-M4; the FIRST plan write on a
    fresh machine is gated, not silently allowed).
  - `plans_dir` CLASSIFICATION (what target paths are gated) is a path-suffix test with a
    `docs/plans/` default (FLAGGED hardcoded convention - confirm/override per repo at
    implementation; optionally read from repo `.ai-playbook/facts.md` when present); it works in
    worktrees because they contain `docs/plans/`.
- **Symlink model** (r11-B2 decided): hook scripts are versioned under `ai-playbook/agents/hooks/<hook>/`
  and symlinked into each agent's `~/` config dir, mirroring how `ai-playbook/agents/skills/` symlinks
  to `~/.agents/skills`, `~/.claude/skills`, `~/.gemini/config/skills`. The NEW cores
  (`lessons_recall.py`, `skill_gate.py`) and the helper (`session_channel.py`) are SYMLINKED to
  `~/.ai-playbook/scripts/` (so a hook always runs the latest code). This is a DEVIATION from the four
  existing copy-synced lessons scripts (`lessons_index.py`/`lessons_adopt.py`/`lessons_migrate.py`/
  `lessons_corpus.py`, whose cleanup is OUT OF SCOPE for this plan).
- **agy (Antigravity CLI) hook events**: five total; the two this plan uses are `PreInvocation`
  (prompt-level, the lessons-recall target, analogous to Claude `UserPromptSubmit`) and
  `PreToolUse` (tool-level gate, the skill-gate target). The other three (`PostToolUse`,
  `PostInvocation`, `Stop`) are out of scope.
- **agy decision contract**: the hook returns a TOP-LEVEL JSON object. Block with
  `{"allow_tool": false, "deny_reason": "..."}`; allow with `{"allow_tool": true}`. The hook
  MUST exit 0 even when denying (non-zero means the hook itself failed). Wrapping the payload in
  a `hookSpecificOutput` envelope (Claude's shape) FAILS agy schema validation; this is why each
  agent has its own adapter.
- **agy payload path**: tool-call arguments arrive on stdin nested under `.toolCall.args.*`
  (e.g. `.toolCall.args.CommandLine` for `run_command`, `.toolCall.args.ToolName` for MCP).
  File-management tools (`write_to_file`, `replace_file_content`, `multi_replace_file_content`)
  carry the target path under the same `.toolCall.args`; the exact path field name is verified at
  build time (see Task 5 / Monitor).
- **Session key** (r10 resolution of the r9 placement Blocker; supersedes the r9 helper-home design
  and the r8 PID-walk design, both of which were uncomputable/unimportable as specified): a
  per-session discriminator used as the `session` component of the skill-gate marker filename and of
  the lessons-recall dedup state filename, so two concurrent sessions of the SAME project do not
  collide. Historical note: the r8 panel (6/11 agents) measured that the PID-walk could not work (no
  portable stopping predicate, PID recycling, cross-session collision at PID 1); r9 DROPPED the
  PID-walk and moved derivation to an adapter-layer helper but specified the helper unimportably
  (bare `python3 -c 'from session_channel import ...'` adds no dir to `sys.path`) and a core importing
  it would reach UP into the adapter layer (Family F). r10 RESOLUTION (user-approved Decision 1): keep
  `session_channel.py` as a shared MODULE in `ai-playbook/scripts/` (leaf, same tier as
  `facts_paths.py`/`lessons_corpus.py`, symlinked to `~/.ai-playbook/scripts/` - the established
  single-source model), invoked as a SUBPROCESS that PRINTS the session id; the cores NEVER import it.
  - **`session_channel.py` is a `scripts/` leaf consumed by adapters AND the plans-skill marker
    recipe, NOT by the cores (r10-B1).** It prints `os.environ.get("CLAUDE_CODE_SESSION_ID") or ""`
    (Claude at v9; empty for Codex/Cursor/agy). Adapters and the plans-skill marker recipe invoke it
    as a SUBPROCESS: `SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"`. When `SID` is empty,
    the adapter OMITS `--session-id`. The cores (`skill_gate.py`, `lessons_recall.py`) NEVER import
    `session_channel.py`; they accept `--session-id` as OPAQUE data with ZERO agent-channel knowledge,
    so the agent-agnostic-core invariant holds and the "cores depend only downward" claim is true
    (Family D single source enforced by a real shared artifact, not an import; Family F avoided).
  - **Claude: the `CLAUDE_CODE_SESSION_ID` env var.** Measured present and stable for the session;
    inherited by EVERY subprocess, so the skill's Bash tool call and the hook subprocess read the SAME
    string with zero asymmetry. This is the ONLY genuinely per-session channel at v9 (a UUID; does not
    recycle within a live session - resume/compact behavior UNVERIFIED, see Monitor) and the one the
    live smoke (Task 7) exercises. The Claude adapter passes `--session-id "$SID"`.
  - **Codex/Cursor/agy: project-only at v9.** The helper returns empty (no verified per-session env
    var) -> adapter OMITS `--session-id` -> core keys the literal `no-session`. This is the DOCUMENTED
    STEADY STATE for those agents (per-session isolation is Claude-only at v9, NOT a degraded
    fallback). A future VERIFIED per-agent env var adds a branch in the helper + a new selftest arm -
    stated as a known extension point, NOT as zero-cost.
  - **`#same_session_pair` remains a trivial sanity selftest** (write(id) then read(id) -> ALLOW). It
    cannot detect live divergence by construction and is not credited as the B1 gate; the Claude
    live write-then-read is.
  - **LOUD keying mode (r11-M2: `keying` is PURE LOG METADATA and drives NO core branch).** ALL
    `keying=` lines land in ONE sink, `~/.ai-playbook/logs/hooks.log`, so an agent on project-only or
    a failed anchor walk is OBSERVABLE, not silent (Family G). OWNERSHIP SPLIT (r15-M1, the single
    deliberate exception to "cores own the keying vocabulary"): the CORE writes
    `keying=env-var` (a session id was supplied - Claude steady state) / `keying=project-only` (no
    session id - Codex/Cursor/agy steady state at v9); the RESOLVER `facts_paths.resolve_project_key`
    writes `keying=no-anchor` (a non-git dir, per B1 step 3 - the sole place that knows the git-failure
    branch fired; the core CANNOT derive it, since re-running `git rev-parse` to re-derive the branch
    is forbidden). Both the resolver and the core append their lines via the shared
    `_append_hooks_log_line` helper (step 3; the sink-fix rationale lives there ONCE). Because the core is forbidden from knowing which agent is calling it (the
    agent-agnostic invariant), `keying=env-var`-vs-`project-only` drives NO core branch: "Claude with
    missing env var" and "Codex steady state" both arrive as `--session-id` absent/empty
    (byte-identical), so the core CANNOT alarm on `project-only`-for-Claude. The resume Monitor
    (below) + the Task 7 LIVE resume assertion handle the missing-env-var case. `no-anchor` is
    ORTHOGONAL and reachable only in non-git dirs (per B1). The Claude-missing-env-var alarm
    (relocated M2/M4 alarm) lives in the CLAUDE ADAPTER (the one place that knows its own
    identity): `claude.sh` emits a stderr warning `CLAUDE_CODE_SESSION_ID absent; running in
    no-session mode` when SID is empty-after-strip, BEFORE invoking the core. Only the Claude adapter
    does this; for Codex/Cursor/agy empty is documented steady state. There is NO halved-window
    consequence: ALL
    agents use the FULL `SKILL_GATE_WINDOW` and FULL `RECALL_DEDUP_WINDOW` unconditionally (r10-M10
    collapsed the halved steady state). lessons-recall uses the SAME channel so its dedup state is
    keyed consistently.
  - **Session value is SANITIZED before filename interpolation (r8-M6/security; r10-M3 hexdigest;
    r11-M3 both layers normalize).** BOTH layers normalize empty-after-strip to absent: the adapter
    OMITS `--session-id` when SID is empty-after-strip (primary), AND the core INDEPENDENTLY treats
    empty-after-strip as absent (defense in depth, so a future divergent adapter that re-introduces
    an empty `--session-id` cannot re-open the hole). The emptiness check (`.strip() == ""`) is the
    FIRST operation, before any hashing. The core then passes the `--session-id` value through
    `sha1(<value>.encode()).hexdigest()[:16]` (hex, path-safe, byte-identical write/read for free;
    `sha1(...)[:16]` without `.hexdigest()` is a `TypeError`) before building the marker/state
    filename, so a hostile env var like `CLAUDE_CODE_SESSION_ID="../foo"` or one containing `/`/NUL
    cannot traverse outside the runtime dir or alias another session's marker. `project` is already
    hex (`sha1(...).hexdigest()[:16]`); now `session` is too.

## Gist & Examples

Two independent hooks, sharing one adapter/symlink model, versioned in ai-playbook.

**Hook 1, lessons-recall (proactive recall).** Today the lessons corpus is recalled only when an
agent remembers to grep. This hook makes recall proactive: on each prompt, classify the prompt's
INTENT against a user-intent vocabulary (`classify_prompt`, a NEW deterministic classifier in the
`lessons_classify` leaf - NOT the lesson-shape classifier, which no-ops on prompts); `classify_prompt`
iterates an explicit family order with G (data-loss) and H (verify-the-real-thing) BEFORE C
(representation), so if it matches a family A-H, silently inject the 1-2 most relevant tagged
lessons as context. The injected body is
truncated to <= `--budget` chars (default 1500), measured on the body before json.dumps wrapping
(one definition everywhere - Gist, Evaluation Criteria, and the `#budget` selftest all use this).
Session de-dup (time-windowed, default 24h) so the same lesson is not re-injected every turn or
suppressed forever. No embeddings, no RAG, no network: deterministic local grep. The corpus reader
(`lessons_corpus.iter_lessons`) and the facts resolvers (new `facts_paths` leaf) are reused; the
prompt classifier is new.

Example: prompt "the report dropped a row" -> `classify_prompt` matches Family G (data-loss
observability) on the intent lemma "dropped" (the vocab seeds lemmas + inflections: drop/drops/
dropped, and bare "missing" is reserved for G) -> the hook injects the highest-ranked Family G
lesson(s), HEAD-truncated to the budget (at the default 1500-char budget and real-corpus G bodies of
~1057-4694 chars, typically ONE full lesson plus a slice of the next - r8-M7; the budget is a
FLAGGED threshold the user may raise). Prompt
"fix the typo" -> no intent phrase matches -> the hook emits nothing (correct no-op). (An explicit
opt-in menu was considered for v1 and CUT - the existing `grep -nE '^\*\*Principle:\*\* Family'`
recall command already documented in user AGENTS.md covers it; see Task 2 / Monitor.)

**Hook 2, skill-gate (artifact gate).** This session exhibited the exact failure: a plan was
about to be written without invoking the `plans` skill. This hook prevents that. On PreToolUse
for Write/Edit, if the target path is a plan file under `{plans_dir}` AND the plans skill left no
RECENT marker (mtime within `SKILL_GATE_WINDOW`), block the write with a message naming the
required skill. v1 gates the plans-dir class only (done/learn classes are added later via a plain
module-level table). It generalizes the existing `check-plan-review-gate.sh` (blocks plan commits
with No-Go review) and `execute-plan-manifest-gate.sh` (blocks Write without a manifest).

Example: an agent calls Write on `docs/plans/some-plan.md` with no fresh plans-marker -> the hook
blocks with "Invoke the plans skill before authoring a plan file." Same write shortly after the plans
skill ran (fresh marker) -> allowed silently.

**Why two hooks, one plan:** they share all infrastructure (symlink model, adapter layout, leaf
extraction, design-doc home, per-agent wiring recipes) but are independent in trigger and contract
(UserPromptSubmit/injection vs PreToolUse/blocking). They ship as two hooks under one plan to avoid
duplicating the wiring design.

**Recreate-in-any-agent requirement:** the agent-agnostic cores (text in, text out; ZERO agent
knowledge - all session-channel logic lives in the `session_channel.py` `scripts/` leaf, r10) plus
thin per-agent adapters mean a new agent is supported by writing one shell wrapper, one config entry,
and (if it has a verified per-session env var) a branch in the shared `session_channel.py` `scripts/`
leaf - NOT a core change.
Four agents are wired in this plan: Claude, Codex, Cursor, and Antigravity (agy). PER-SESSION
isolation is CLAUDE-ONLY at v9 (Claude is the one agent with a verified per-session channel,
`CLAUDE_CODE_SESSION_ID`); Codex/Cursor/agy run PROJECT-ONLY (helper returns empty -> adapter OMITS
`--session-id` -> core keys `no-session`) as the DOCUMENTED STEADY STATE (NOT a degraded fallback).
ALL agents use the FULL `SKILL_GATE_WINDOW` and FULL `RECALL_DEDUP_WINDOW` unconditionally (r10-M10:
the halved-window steady state is COLLAPSED). On agy, skill-gate is full-fidelity (the `PreToolUse` +
`allow_tool`/`deny_reason` block mechanism is verified from the cited article); lessons-recall is
best-effort via `PreInvocation` (the context-injection field is described in the article but not shown
in a concrete agy example, so it is verified at build time, the same status the plan gives Codex's
prompt-event availability).

## Evaluation Criteria

**Quality dimensions:**
- Determinism (both hooks): grep/exact-match only; no ML, no embeddings, no ordering nondeterminism
  (prompt classifier: first-match-wins over an EXPLICIT `PROMPT_FAMILY_ORDER` tuple with G/H before C;
  lesson-shape classifier: first-match-wins over `sorted(VALID_FAMILIES)`;
  skill-gate path-classifier is a `realpath` subtree check, never a raw string prefix). Verified by
  `--selftest` on all three cores/leaves.
- Anti-noise (lessons-recall): fast no-op on non-matching prompts; injected body truncated to <= `--budget` chars (default 1500), measured before json.dumps wrapping; session
  de-dup. Verified by echo-pipe tests: a non-matching prompt yields empty stdout; a repeat matching
  prompt yields empty stdout on the second call.
- Correct blocking (skill-gate): blocks gated writes without a fresh marker; allows with a fresh
  marker; fail-open (never blocks) when the marker store is unreadable, with a stderr warning.
  Verified by echo-pipe tests for each arm.
- Local-only and read-only-on-corpus: no network; the core never writes a corpus file, only a
  best-effort tmp state file; no env-var secrets read. Verified by inspection + a read-only corpus
  (mode 0444) still works.
- Recreate-ability: each wired agent (Claude, Codex, Cursor, Antigravity) has a versioned adapter + a
  README recipe. agy skill-gate is full-fidelity (verified block contract); agy lessons-recall is
  best-effort pending the build-time field check.
- Hard-rules compliance: no em dashes (U+2014) in any generated text or output; `~/` home-relative
  paths in all docs.

**Release gates:**
- All cores/leaves pass `python3 <core> --selftest` (exit 0).
- All four wired adapters (Claude, Codex, Cursor, Antigravity) pass their echo-pipe tests
  (skill-gate: allow/block/non-gated/fail-open; lessons-recall: match/no-match). ALL FOUR adapters
  ship LIVE and symlinked (r7-M3, user decision "fix on first use"): the assumed agy field names
  (context-injection field, file-tool path field) and the Codex prompt-event /
  blocking-event availability are DOCUMENTED in each README and validated on the first real session,
  with correction as fix-on-first-use - NOT held back to a follow-on. The cores + the Claude adapters
  are the combination the live smoke exercises; the others ship on the same documented-assumptions
  basis.
- `check-no-em-dash.sh` clean on every new `.md` and `.py`.
- Live smoke in a Claude session: recall fires on a realistic matching prompt (no literal family
  phrase), is silent on a non-matching prompt, and does not repeat (de-dup); skill-gate blocks a
  plan-file Write without a fresh marker and allows it with one.
- No regression: `pr-skill-reminder.sh`, `learn-counter`, `check-plan-review-gate.sh`, and
  `execute-plan-manifest-gate.sh` still fire independently.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code (new):**
- `ai-playbook/scripts/facts_paths.py` *(new; B3/M6 - facts-key resolver leaf)*
- `ai-playbook/scripts/lessons_classify.py` *(new; B1/M6 - prompt classifier leaf; mid-tier node importing `lessons_corpus`)*
- `ai-playbook/scripts/lessons_recall.py` *(new)*
- `ai-playbook/scripts/session_channel.py` *(new; r10-B1 - shared session-id helper leaf in `scripts/`, subprocess-invoked; never imported by cores)*
- `ai-playbook/scripts/skill_gate.py` *(new)*
- `ai-playbook/agents/hooks/lessons-recall/claude.sh` *(new)*
- `ai-playbook/agents/hooks/lessons-recall/codex.sh` *(new)*
- `ai-playbook/agents/hooks/lessons-recall/cursor.sh` *(new)*
- `ai-playbook/agents/hooks/lessons-recall/agy.sh` *(new)*
- `ai-playbook/agents/hooks/skill-gate/claude.sh` *(new)*
- `ai-playbook/agents/hooks/skill-gate/codex.sh` *(new)*
- `ai-playbook/agents/hooks/skill-gate/cursor.sh` *(new)*
- `ai-playbook/agents/hooks/skill-gate/agy.sh` *(new)*

**Production code (modified):**
- `ai-playbook/scripts/lessons_migrate.py` *(modify; M6 - re-import resolvers + classifiers from the
  new leaves, byte-identical bodies; public API unchanged)*

**Docs / wiring (new + modified):**
- `ai-playbook/agents/hooks/lessons-recall/README.md` *(new)*
- `ai-playbook/agents/hooks/skill-gate/README.md` *(new; single source for the marker WRITE RECIPE)*
- `ai-playbook/agents/skills/plans/SKILL.md` *(modify: write skill-gate marker on Phase 0)*
- `ai-playbook/docs/AGENTS.md` *(modify: one-line note pointing at the two hooks + marker README)*

**Out of scope (config outside any git repo; installed, not committed here):**
- `~/.claude/settings.json`, `~/.codex/config.toml` AND `~/.codex/hooks.json` (r12-M5: BOTH are
  candidate Codex config files - `config.toml` `[hooks]` table carries `post_tool_use`;
  `hooks.json` carries the `SessionStart` array; which one Codex consults for a BLOCKING
  `pre_tool_use` is verified at build time), `~/.cursor/hooks.json`,
  `~/.gemini/antigravity-cli/hooks.json` (global) and `<project>/.agents/hooks.json` (project):
  per-agent wiring; documented in the READMEs, applied on the user's machine. The agy config
  `command` MUST be an absolute path (relative paths resolve against the launch cwd and fail with
  exit 127, silently bypassing the guardrail); the README recipe uses the absolute symlink target.

**Plan-related extension:** the symlink install into `~/` agent dirs and the live smoke test may
surface environment-specific issues (e.g. an agent refusing a symlinked command); these are in
scope as plan-related follow-on.

## Validation Commands

```bash
# Leaves and cores (agent-agnostic, headless)
python3 ~/.ai-playbook/scripts/facts_paths.py --selftest
python3 ~/.ai-playbook/scripts/lessons_classify.py --selftest
python3 ~/.ai-playbook/scripts/lessons_recall.py --selftest
python3 ~/.ai-playbook/scripts/session_channel.py --selftest
python3 ~/.ai-playbook/scripts/skill_gate.py --selftest

# lessons-recall: realistic match / inflected match / no-match / de-dup / budget / adversarial / cold-start / no em dash
python3 ~/.ai-playbook/scripts/lessons_recall.py --prompt "the report dropped a row"   # realistic prompt -> Family G reminder (NO literal family phrase)
python3 ~/.ai-playbook/scripts/lessons_recall.py --prompt "the report drops a sell"    # inflected lemma match -> Family G (pins M5)
python3 ~/.ai-playbook/scripts/lessons_recall.py --prompt "fix the typo"               # expect empty stdout
python3 ~/.ai-playbook/scripts/lessons_recall.py --state-dir "$(mktemp -d)" --prompt "the report dropped a row"  # first call non-empty
# (re-run identical) -> second call empty (de-dup), via isolated --state-dir
python3 ~/.ai-playbook/scripts/lessons_recall.py --prompt "the report dropped a row" | grep -P '\x{2014}' && echo BAD || echo GOOD

# skill-gate: traversal bypass / fail-open
python3 ~/.ai-playbook/scripts/skill_gate.py --selftest#traversal_bypass   # src/../../docs/plans/x.md -> gated
python3 ~/.ai-playbook/scripts/skill_gate.py --selftest#doctor_agy_timeout   # agy PreToolUse timeout > RESOLVER_GIT_TIMEOUT_S boundary + README value + absent case

# Adapters (echo-piped)
echo '{"prompt":"the report dropped a row"}' | ~/.claude/hooks/lessons-recall.sh
echo '{"prompt":"continue"}' | ~/.claude/hooks/lessons-recall.sh   # expect empty, exit 0
echo '{"tool_name":"Write","tool_input":{"file_path":"docs/plans/x.md"}}' | ~/.claude/hooks/skill-gate.sh   # without fresh marker -> block
# (after the plans skill writes the marker) same call -> allow

# agy adapters (echo-piped; field names UNVERIFIED until a real agy payload is captured - see Monitor)
echo '{"prompt":"the report dropped a row"}' | ~/.gemini/antigravity-cli/hooks/lessons-recall-agy.sh   # match -> additionalContext
echo '{"toolCall":{"args":{"path":"docs/plans/x.md"}}}' | ~/.gemini/antigravity-cli/hooks/skill-gate-agy.sh   # without marker -> {"allow_tool":false,...}; exit 0
# (after the plans skill writes the marker) same call -> {"allow_tool":true}; exit 0 always

# Hard rules
CHECK_NO_EM_DASH_ALL=1 bash ~/.ai-playbook/scripts/check-no-em-dash.sh file \
  ai-playbook/scripts/facts_paths.py ai-playbook/scripts/lessons_classify.py \
  ai-playbook/scripts/lessons_recall.py ai-playbook/scripts/session_channel.py \
  ai-playbook/scripts/skill_gate.py \
  ai-playbook/agents/hooks/lessons-recall/README.md ai-playbook/agents/hooks/skill-gate/README.md \
  ai-playbook/docs/plans/2026-07-01-lessons-recall-hook.md
```

### Task 1: shared leaves (`facts_paths.py`, `lessons_classify.py`)

Files:
- `ai-playbook/scripts/facts_paths.py` *(new)*
- `ai-playbook/scripts/lessons_classify.py` *(new)*
- `ai-playbook/scripts/lessons_migrate.py` *(modify: re-import from the leaves)*

- [x] `facts_paths --selftest#resolves_all_keys`; given a REAL-SHAPED facts file (a ```toml fence block with `plans_dir`/`tmp_dir` AND a separate markdown table row `| \`shared_docs_dir\` | ... |`), expects `resolve_plans_dir`/`resolve_tmp_dir` (TOML parser) and `resolve_shared_docs_dir`/`user_corpus_path` (table parser) each to return ITS OWN format's value; a stub that hardcodes one parser fails (pins the r2 Blocker - the two keys live in DIFFERENT on-disk formats)
- [x] `facts_paths --selftest#shared_docs_dir_unchanged`; against the REAL home `~/.ai-playbook/facts.md` (table row, line 30), expects `resolve_shared_docs_dir` to return the SAME `Path` the migrator returned before the move (byte-identical table parser; NOT a fake fixture)
- [x] `facts_paths --selftest#table_key_repo_first`; given a `start_dir` whose OWN `.ai-playbook/facts.md` has a `shared_docs_dir` table row pointing at a DIFFERENT path than the home facts file, expects `resolve_shared_docs_dir(start_dir)` to return the REPO value, NOT the home value (pins the repo-first two-candidate search order byte-identical to `resolve_shared_docs_dir`; a home-only impl false-returns the home path - r7-M2/r5-M5)
- [x] `lessons_classify --selftest#prompt_realistic`; given "the report dropped a row" (NO literal family phrase), expects `classify_prompt` to return a non-None tuple whose FIRST element is family G, proving the prompt classifier fires where the lesson-shape classifier no-ops
- [x] `lessons_classify --selftest#prompt_realistic_inflected`; given "the report is missing a row", "the report drops a sell", "the report is dropping rows", AND "the total disagrees between the two tabs", expects a non-None match on EACH (pins lemma+inflection seeding incl. the present participle "dropping" - the `_phrase_present` edge guard does NOT match "drop" inside "dropping", so it must be seeded explicitly; the bare-phrase seed would silently no-op here)
- [x] `lessons_classify --selftest#overlap_missing`; given "missing data", expects family G (data-loss), NOT C - bare "missing" is seeded ONLY in G; documented resolution direction
- [x] `lessons_classify --selftest#overlap_verify_vs_representation`; given "verify the null-handling path" (the LOAD-BEARING discriminator: `verify`=H and `null`=C genuinely collide), expects family H (verify-the-real-thing), NOT C - H precedes C in `PROMPT_FAMILY_ORDER = ("G","H",...,"C")` (r5-L1), so H wins first-match-wins even though C also seeds `null` (pins the explicit family order; under `sorted(VALID_FAMILIES)` C would be consulted first and route to C). (Note: C does NOT seed `field name` - only H does - so a `"trace the actual field name"` input is H-only under either order and does not discriminate; it is kept only as a second H-direction sample, not as an order pin.)
- [x] `lessons_classify --selftest#prompt_no_match`; given "fix the typo", expects `classify_prompt` to return None
- [x] `lessons_classify --selftest#lesson_shape_unchanged`; given a lesson body, expects `_matches_family_vocab` (now re-exported from the leaf) to return the SAME family the migrator returned before the move (byte-identical behavior)
- [x] `lessons_classify --selftest#depends_on_lessons_corpus`; expects `lessons_classify` to import `lessons_corpus` (it is a mid-tier node, NOT a stdlib-only leaf; pins L4)
- [x] Run -> expect RED: `python3 ai-playbook/scripts/facts_paths.py --selftest` and `python3 ai-playbook/scripts/lessons_classify.py --selftest` (stubs fail)
- [x] Implement `facts_paths.py` (stdlib-only leaf):
  - **Module docstring.** Scope BOTH responsibilities: facts-FILE key resolution (parsing
    `.ai-playbook/facts.md` for `plans_dir`/`tmp_dir`) AND repo-anchor/project-key derivation
    (git-based; does NOT read the facts file). r15-L4 NOTE: the project-key path now also owns ONE
    observability side effect (writing `keying=no-anchor` to `hooks.log`); acceptable for v1, but if
    a SECOND leaf-side log token or side effect appears, extract `resolve_project_key` (and its log
    write) into its own leaf (`project_key.py`), leaving `facts_paths.py` as pure facts-file parsing.
  - **Two parsers (r2 Blocker).** DO NOT introduce a generic `resolve_facts_key`; `plans_dir`/
    `tmp_dir` are TOML-fence keys and `shared_docs_dir` is a markdown table row - they cannot share
    one parser.
  - **`resolve_toml_key(start_dir, key)`.** Parses the repo `.ai-playbook/facts.md` opening ```toml
    fenced block (`key = "value"` lines); backs NEW `resolve_plans_dir`/`resolve_tmp_dir`.
  - **`resolve_table_key(start_dir, key)`.** Parses a markdown table row `| \`key\` | \`value\` |`,
    searching `<start_dir>/.ai-playbook/facts.md` FIRST then `~/.ai-playbook/facts.md`; backs the
    MOVED `resolve_shared_docs_dir`/`user_corpus_path`. Byte-identical body INCLUDING the repo-first
    two-candidate order (r7-M2/r5-M5: a home-only reading is NOT byte-identical and silently drops a
    repo-scoped `shared_docs_dir` row).
  - **`resolve_project_key(start_dir) -> str` (r12-M1; r14: return is `-> str`; r15-M1: the resolver
    WRITES `keying=no-anchor` to `hooks.log`; r17: via the shared helper).** Algorithm per
    Terms (Skill-gate marker steps 1-4); local facts: signature
    `resolve_project_key(start_dir) -> str`, list-form argv
    `subprocess.run(['git','-C',start_dir,'rev-parse','--show-toplevel'], capture_output=True,
    text=True, timeout=RESOLVER_GIT_TIMEOUT_S)`, catch `(subprocess.SubprocessError, OSError)`. NEVER
    raises; on the git-failure branch calls the shared
    `_append_hooks_log_line({"ts": <iso8601 utc>, "keying": "no-anchor"})` (Terms step 3; the helper
    IS the makedirs+`O_NOFOLLOW`+newline recipe - the resolver restates no part of it).
  - **Facts-path carve-out.** `resolve_plans_dir` and facts-path resolution STAY (used for
    `plans_dir` CLASSIFICATION); only the project hash no longer consults the facts file.
- [x] Implement `lessons_classify.py` (mid-tier node importing `lessons_corpus`): MOVE `FAMILY_KEYWORDS`, the lesson-shape classifier, and the phrase-present primitive here (byte-identical) AND PROMOTE them to PUBLIC leaf API on the move (r8-L2: drop the underscore - `matches_family_vocab`, `phrase_present` - because they are now consumed cross-module, which violates the private-naming convention; the move IS the deliberate promotion moment); ADD `PROMPT_INTENT_VOCAB: dict[str, list[str]]` (a NEW user-intent vocabulary; seed with LEMMAS + common inflections, not only multi-word phrases - seed: A="test the case"/"empty string"/"null input"/"boundary"/"edge case"/"parametrized"; B="swallow"/"swallowed"/"degrade"/"raise vs warn"/"fallback"/"silent failure"; C="null"/"none"/"sentinel"/"absent"/"placeholder" (NOT bare "missing" - reserved for G); D="two places"/"disagree"/"disagrees"/"disagreed"/"drift"/"duplicate"/"consistent"; E="ordering"/"race"/"stale"/"timing"/"reorder"; F="circular"/"reach up"/"dependency direction"/"refactor the layer"; G="drop"/"drops"/"dropped"/"dropping"/"missing"/"missing row"/"skipped"/"unmatched"/"lost"/"losing"/"loses"; H="trace"/"verify"/"mock"/"actual data"/"field name"). ADD `classify_prompt(prompt) -> tuple[str, list[str]] | None` (same phrase-matching primitive as the lesson-shape classifier; returns `(letter, matched_phrases)` or None). RESOLUTION ORDER (r5-L1, replacing the r4 carve-out layer): iterate an EXPLICIT `PROMPT_FAMILY_ORDER = ("G","H","A","B","D","E","F","C")` tuple (NOT `sorted(VALID_FAMILIES)`), first-match-wins over THIS order. Rationale: G (data-loss) and H (verify-the-real-thing) are the plan's flagship families and must win over C (representation) on overlap - sorted order consults C before G/H, so "verify the null-handling path" would route to C (C seeds `null`) instead of H, inverting the flagship direction; C is the catch-all representation family and goes last. (Note: C does NOT seed bare "missing", so the G/"missing" case needs no special handling - only the G/H-before-C ordering is load-bearing. This explicit order replaces the r4 H-carve-out + G-carve-out layer with one constant in one place.) The lesson-shape classifier (`_matches_family_vocab`) keeps its OWN `sorted(VALID_FAMILIES)` first-match-wins - it classifies lesson entries, not prompts, and is unchanged
- [x] `lessons_migrate.py`: replace the moved bodies with re-imports from the leaf (the migrator keeps NO own copy of `phrase_present`/`matches_family_vocab` - r8-L1 single source); public API shape (`resolve_shared_docs_dir`, `user_corpus_path`, the lesson-shape classifier, `FAMILY_KEYWORDS`) unchanged, but the underscore is dropped where the migrator re-exports them (r8-L2). Add `lessons_classify --selftest#phrase_present_single_source` asserting `lessons_migrate.phrase_present is lessons_classify.phrase_present` (IDENTITY, not equality) after the re-import - a second copy would diverge silently (Family D)
- [x] `facts_paths --selftest#resolve_project_key_no_raise_on_missing_git` (r13-M5; r14-M1 adds the
  `TimeoutExpired` arm; r14-M3 collapses the return to `-> str`; r15-M1 tightens the log assertion to
  the FILE): parametrize over TWO failure causes - monkeypatch `subprocess.run` to raise
  `FileNotFoundError` (git binary absent) AND `subprocess.TimeoutExpired(cmd, 5)` (hung git: NFS mount,
  locked `index.lock`, gpgsign prompt); assert EACH arm returns `sha1(realpath(start_dir))[:16]` (a
  plain `str`, NOT a tuple) rather than propagating, AND that the resolver WROTE `keying=no-anchor`
  to the `hooks.log` FILE (monkeypatch `HOME` to a tmp dir - the resolver derives the log path from
  `Path.home()` at call time, r16-L3, so the test reads back the REAL file the resolver opened with
  `os.open` - NOT a `logging` record; a `logging.warning` impl FAILS this assertion because the file
  stays empty, even though `assertLogs` would capture the record). r16-L4 SHAPE ASSERTION: read the
  file back and `json.loads` the LAST non-empty line -> a dict with EXACTLY `{"ts": ..., "keying":
  "no-anchor"}` keys (no `WARNING:`/`levelname`/`Formatter` prefix); a `logging.FileHandler` impl
  with default formatting fails `json.loads`. r16-M1 ABSENT-PARENT ARM: set `HOME` to a tmp dir whose
  `.ai-playbook/logs/` does NOT pre-exist; assert the resolver STILL returns the hash WITHOUT raising
  AND the line reaches the file (the `os.makedirs(parent, exist_ok=True, 0o700)` created the dir) - a
  bare-`os.open` impl raises `FileNotFoundError` here and the file stays empty. r17-L1 READ-ONLY-PARENT
  ARM: make `~/.ai-playbook/` itself read-only (chmod 0500) so the helper's makedirs raises
  `PermissionError`; assert the resolver STILL returns the hash WITHOUT raising (the single
  `try/except OSError` covers the makedirs too, so the gate is unaffected - an impl that narrows to
  `except FileNotFoundError` re-raises here and FAILs). r18-M3 NON-SERIALIZABLE-PAYLOAD ARM: call the
  shared helper directly with a payload whose `ts` is a NON-JSON-serializable object
  (`datetime.now(timezone.utc)`, NOT `.isoformat()`); assert the helper returns WITHOUT raising (a
  bare-`json.dumps(payload)` impl raises `TypeError`, which is NOT an `OSError` and escapes the
  `try/except OSError`, violating NEVER-raises; only `json.dumps(payload, default=str)` degrades the
  field to `str` and PASSES). Pins that the helper's serialize step covers the realistic
  non-serializable-scalar mistake (a `datetime`/`Path` passed where an iso8601/str was intended); it
  does NOT pin absolute never-escape, which holds only for literals-only payloads (a circular payload
  or a `__str__`-raising value is out of contract and remains the caller's responsibility).
  Pins that
  `resolve_project_key` NEVER raises, that the catch
  `(subprocess.SubprocessError, OSError)` covers BOTH `TimeoutExpired` (a `SubprocessError`, NOT an
  `OSError`) and `FileNotFoundError` (the gate's fail-open policy does not need to cover this path),
  AND that the no-anchor signal reaches the SAME sink operators grep (r15-M1 sink fix). Note: the
  single-source IDENTITY selftest (`#project_single_source`) is asserted in EACH CORE's own
  `--selftest` (downward import only), NOT here - a leaf asserting
  `lessons_recall.resolve_project_key is facts_paths.resolve_project_key` would reverse the
  dependency direction and crash on ImportError before the cores exist (r13-M2).
- [x] Run -> expect GREEN: both selftests exit 0; `python3 ai-playbook/scripts/lessons_migrate.py --selftest` still passes (no behavior change)
- [x] Commit: `refactor(lessons): extract facts_paths and lessons_classify leaves; add prompt classifier`

### Task 2: lessons-recall core (`lessons_recall.py`)

Files:
- `ai-playbook/scripts/lessons_recall.py` *(new)*

- [x] `lessons_recall --selftest#realistic_match`; given "the report dropped a row" (NO literal family phrase), expects a reminder block citing a Family G lesson and exit 0 (pins the B1 fix - the OLD plan no-oped here)
- [x] `lessons_recall --selftest#no_match`; given "fix the typo", expects empty stdout and exit 0
- [x] `lessons_recall --selftest#dedup`; given the same matching prompt twice with a fixed `--session-id` (and an isolated `--state-dir $(mktemp -d)`), expects the FIRST call non-empty AND the SECOND (within window) empty - both resolve to the SAME per-(project,session) state file so the second's `N` is in `seen` (both assertions; "second empty" alone is non-discriminating)
- [x] `lessons_recall --selftest#dedup_expiry`; given the same matching prompt a third time AFTER simulating `now > RECALL_DEDUP_WINDOW` since the prior injection, expects NON-EMPTY output again (pins the time window; without it, recall silently decays to zero for long-used cwds)
- [x] `lessons_recall --selftest#dedup_concurrent`; the selftest CREATES AND ASSERTS its OWN fresh empty `--state-dir $(mktemp -d)` immediately before launch (in-test assertion the dir is empty, not prose - r8-L11). Given TWO `lessons_recall` invocations of the SAME matching prompt (same `N` membership key in the per-(project,session) state file, fixed `--session-id`) against that one shared `--state-dir`, launched concurrently via `xargs -P 2`, expects: no crash; STATE-FILE INTEGRITY (every line present is a well-formed `N\tts\n` record - no partial/interleaved/corrupted bytes, no lost record); `0 <= line_count <= 2` (BOUNDED, not exact - r8-M8: the append is BEST-EFFORT on the write side, so if BOTH processes' appends raise (ENOSPC/EMFILE) and are swallowed, line_count == 0 with both having emitted; do NOT assert `>= 1` which would false-RED on a correct impl); and combined stdout <= 2 budget-capped blocks. A read-modify-write `os.replace` impl would lose a line or corrupt a record (unparseable line)
- [x] `lessons_recall --selftest#dedup_window_boundary`; given a state file PRE-SEEDED with two lines at known `ts` offsets straddling the window (one at `now - RECALL_DEDUP_WINDOW - 60` = STALE, one at `now - RECALL_DEDUP_WINDOW + 60` = FRESH, same `N` - r8-L4 widens the margin from 1s to 60s so seed-to-read skew across two `time.time()` calls plus file I/O cannot flip the FRESH entry stale on a correct impl), expects the FRESH key suppressed and the STALE key re-admitted - pinning the `ts >= now - RECALL_DEDUP_WINDOW` COMPARISON itself, not an elapsed-time outcome (a stub that re-injects on every call passes an elapsed-time test but fails this one)
- [x] `lessons_recall --selftest#dedup_partial_family`; given a state file PRE-SEEDED with `N1` FRESH (in window) and `N2` STALE (out of window) for the SAME family, and a prompt matching that family (both N1 and N2 are family-matched candidates), expects N2 INJECTED and N1 SUPPRESSED - pinning the PER-LESSON (P1) suppression predicate (a per-prompt/stub-whole-family P2 impl would emit NOTHING because N1 is seen; this test discriminates P1 from P2)
- [x] `lessons_recall --selftest#budget`; given a synthetic corpus with N>=5 family-G lessons EACH with body length in `(budget/4, budget/2)` (concrete bounds, independent of the selected count) and COMBINED bodies EXCEEDING the budget, expects (a) output non-empty, (b) total lesson-body length <= `--budget` (default 1500), (c) output cites >=2 distinct lesson numbers (guaranteed: >=2 full bodies fit before the cap), and (d) a truncation indicator present IFF any selected lesson was sliced (drop "plus framing"; the cap is on the injected body before json.dumps wrapping). Truncation keeps the FIRST `--budget` chars of the ranked concatenation (HEAD), so the highest-ranked (title-matched, lowest-number) lessons survive and the tail is sliced/dropped - r8-M2
- [x] `lessons_recall --selftest#budget_rank_priority`; given a synthetic corpus where the TITLE-PHRASE-MATCHED lesson is the LONGEST body and combined bodies exceed budget by exactly one body, expects the title-matched lesson IS PRESENT in the output (fails under the old TAIL-truncation wording, which dropped the front/highest-ranked first; passes under HEAD-truncation - r8-M2 discriminator)
- [x] `lessons_recall --selftest#dedup_cold_start_file_absent`; given a matching prompt with NO state file present (the `<project>.<session>.state` file itself ABSENT - not just an empty dir; the runtime dir is absent by default on a fresh machine, so every session's first matching call is a cold start), expects NON-EMPTY output (injects, since `seen` is empty) AND exit 0, then after the call the file EXISTS with one well-formed `N\tts\n` line - pins the read path opens `O_RDONLY` inside `try/except FileNotFoundError` yielding `seen = set()` rather than crashing (r8-M3)
- [x] `lessons_recall --selftest#no_em_dash`; given any input, expects no U+2014 in output
- [x] `lessons_recall --selftest#adversarial_corpus`; given a corpus body containing `"`, `}`, newlines, and a literal `"additionalContext"` key, expects the emitted envelope (built by the adapter) to round-trip `json.loads` with the body intact as one string - the CORE emits a plain JSON string via `json.dumps`; envelope assembly is the adapter's job
- [x] `lessons_recall --selftest#corpus_readonly`; given a corpus with mode 0444, expects the core to still read and emit, never attempt a corpus write
- [x] `lessons_recall --selftest#cold_start_project_only`; given NO user corpus but a project corpus (`docs/maintenance/development_lessons.md`) present with a tagged lesson matching the prompt, expects NON-EMPTY output citing the project lesson (a no-op stub returning empty fails; drops the ambiguous "or")
- [x] `lessons_recall --selftest#cold_start_both_absent`; given NEITHER corpus present, expects EMPTY stdout and exit 0 (never crash)
- [x] `lessons_recall --selftest#project_single_source` (r13-M2 moved here from `facts_paths --selftest`;
  downward import only): assert `lessons_recall.resolve_project_key is facts_paths.resolve_project_key`
  (IDENTITY, not equality - the core must import the SAME function object, not a copy). A core that
  copies the function body fails its own `is` check; a second copy would drift silently and desync the
  dedup state key from the marker key (Family D).
- [x] `lessons_recall --selftest#project_filename_uses_resolver` (r14-M4; r15-M2 pins the fixture
  shape): given a fixture `start_dir` that is a SUBDIR of a git repo (so
  `realpath(start_dir)` != `realpath(git_toplevel)`), expects the resolved dedup state filename's
  `project` component EQUALS `facts_paths.resolve_project_key(<same fixture start_dir>)` AND DIFFERS
  from `sha1(realpath(<fixture>).encode()).hexdigest()[:16]` (the value a never-calls-resolver impl
  that computes `project` locally would produce). A non-git fixture does NOT discriminate: there
  both derivations return `sha1(realpath(start_dir))[:16]`, so pin the git-subdir case (pins that the
  core actually CALLS the resolver, not just imports it; complements `#project_single_source` which
  catches a byte-identical copy).
- [x] Run -> expect RED: `python3 ai-playbook/scripts/lessons_recall.py --selftest`
- [x] Implement (per Terms Skill-gate marker + Session key for the full contract; this bullet
  states only the LOCAL elements):
  - **Sibling-import bootstrap (r14-M2).** As the FIRST line after the stdlib imports:
    `sys.path.insert(0, str(Path(__file__).resolve().parent))` (mirrors `lessons_adopt.py:38-41`;
    REQUIRED because the core is symlinked into `~/.ai-playbook/scripts/` and imports sibling leaves
    `facts_paths`/`lessons_classify`/`lessons_corpus` from the repo scripts dir, not
    `~/.ai-playbook/scripts/`; `Path(__file__).resolve().parent` follows the symlink to the repo dir
    where the siblings exist).
  - **Prompt classify gate.** Classify via `lessons_classify.classify_prompt(prompt)` (NOT
    `_matches_family_vocab`); if it returns None, emit nothing and exit 0 WITHOUT touching the state
    file (the dedup read is GATED behind a successful classify - non-matching prompts must not pay
    the file read, and the append-only file must not grow on no-op turns).
  - **Selection + budget.** If it returns a family: resolve corpora via
    `facts_paths.user_corpus_path(cwd)` + cwd-relative `docs/maintenance/development_lessons.md`;
    filter `lessons_corpus.iter_lessons` by `family in lesson.tags`; SELECT ALL family-matched
    lessons, RANK (title-phrase-match first, then lowest number), CONCATENATE bodies (each rendered
    `f"Lesson #{N} ({title}): {body}"` joined by a separator - r8-M7: the `#N` token is the SAME field
    the dedup key and the `#budget` selftest count), TRUNCATE the concatenated body to the FIRST
    `--budget` chars (HEAD - r8-M2: highest-ranked survive; do NOT truncate from the tail); the core
    emits a single `json.dumps(text)` string value.
  - **State file location (PATH-ISOLATED per (project, session)).** Genuinely APPEND-ONLY state file
    at `<--state-dir>/<project>.<session>.state` where `--state-dir` defaults to HOME-ANCHORED
    `~/.ai-playbook/runtime/lessons-recall/` (home-anchored like the marker; created `0o700`). PATH
    -ISOLATION replaces the r6 global flat file: each (project, session) pair gets its OWN file, so
    deletion/prune is per-session, read cost scales with current-session activity, and the membership
    key simplifies to `N` (project and session are encoded in the PATH).
  - **`project` derivation (per Terms "Skill-gate marker"; r12-M1 collapse).** Call
    `facts_paths.resolve_project_key(start_dir)` and use the returned `project_hash` (a plain `str`;
    do NOT re-implement the derivation locally. The duplicated-VERBATIM-Family-D obligation to
    `skill_gate.py` is enforced by `#project_single_source` (IDENTITY on one shared function object,
    asserted in each core's own `--selftest` - downward import only).
  - **`session` derivation + sanitization (per Terms "Session key").** The emptiness check
    (`.strip() == ""`) is the FIRST operation, before any hashing. An empty-after-strip
    `--session-id` is treated IDENTICALLY to absent (r11-M3: BOTH layers normalize - the adapter
    OMITS when empty-after-strip, AND the core independently treats empty-after-strip as absent,
    defense in depth) -> key by the literal `no-session` (NOT `sha1("").hexdigest()[:16]` =
    `da39a3ee5e6b4b0d`, which would be a constant collision - r10-M4). Otherwise
    `session = sha1(<--session-id value>.encode()).hexdigest()[:16]` (SANITIZED to hex before
    filename interpolation - path-traversal safety, byte-identical write/read for free; a hostile env
    var like `../foo` cannot escape the runtime dir or alias another session's state).
  - **One full window (r10-M10).** `RECALL_DEDUP_WINDOW` default 86400s / 24h (FLAGGED, analogous to
    `SKILL_GATE_WINDOW`). ALL agents use the FULL window unconditionally - the halved-window steady
    state is COLLAPSED; omitting `--session-id` NO LONGER halves any window.
  - **Read path (cold-start - r8-M3).** Open the state file `O_RDONLY` inside
    `try/except FileNotFoundError` (and the `OSError` family); a MISSING/unreadable file yields
    `lines = []` -> `seen = set()` - the first matching call in a session ALWAYS takes this cold-start
    branch (the runtime dir is absent on a fresh machine), exercised by every cold start, never a
    crash.
  - **Append + membership key.** APPEND with `os.open(path, O_WRONLY|O_CREAT|O_APPEND, 0o600)` and
    write one `f"{N}\t{ts}\n"` line per injection (NOT `atomic_write_text`, which is a full-file
    `os.replace` read-modify-write and is NOT concurrency-atomic). The DE-DUP MEMBERSHIP KEY is `N`
    within the file; `ts` is PRUNING METADATA, NOT part of the key (if `ts` were part of the key, no
    two writes would collide and dedup would never suppress - r4-M2). The file is APPEND-ONLY for its
    entire lifetime and is NEVER rewritten: the reader computes
    `seen = { N for line in lines if ts >= now - RECALL_DEDUP_WINDOW }` IN MEMORY (no rewrite race
    with concurrent appenders); stale lines are ignored on read, never truncated out.
  - **Suppression predicate (r6-M3).** PER-LESSON (P1), NOT per-prompt: drop every lesson whose `N`
    is in `seen`, then RANK + CONCATENATE + TRUNCATE the REMAINDER; emit nothing iff the filtered
    remainder is empty (a same-lesson concurrent pair may inject twice before either append is
    visible - best-effort, bounded by the budget cap).
  - **Concurrency.** `O_APPEND` guarantees STATE-FILE INTEGRITY (no lost/corrupted lines); injection
    de-duplication is BEST-EFFORT (a same-lesson concurrent pair may inject twice before either
    append is visible; the append is best-effort on the write side - r8-M8 - bounded by the budget
    cap; do NOT over-claim a concurrency-atomic injection guarantee).
  - **Agent-agnostic core.** The core accepts `--session-id` as OPAQUE data; ALL session-channel
    knowledge lives in the `scripts/session_channel.py` leaf, subprocess-invoked by the adapter, NEVER
    imported by the core (r10-B1; see Session key term).
  - **Cut.** The opt-in menu / `representative_lesson_per_family` path is CUT from v1 (the existing
    `grep -nE '^\*\*Principle:\*\* Family' <corpus>` recall command already documented in user
    AGENTS.md covers it; re-introduce only when a real session demonstrates the trigger firing
    organically).
  - **Flags accepted.** `--state-dir DIR`, `--no-dedup`, `--budget N`, `--prompt TEXT` (or stdin),
    `--session-id ID` (adapter-supplied; absent/empty -> `no-session` key + full window), `--selftest`.
- [x] Run -> expect GREEN: `python3 ai-playbook/scripts/lessons_recall.py --selftest`
- [x] Commit: `feat(lessons-recall): agent-agnostic core with prompt classifier`

### Task 3: lessons-recall adapters (Claude/Codex/Cursor/agy) + symlinks + wiring

Files:
- `ai-playbook/scripts/session_channel.py` *(new; r10-B1 Decision 1: shared MODULE in `scripts/` - leaf, same tier as `facts_paths.py`/`lessons_corpus.py`; symlinked to `~/.ai-playbook/scripts/` like the other cores - the established single-source model. Invoked as a SUBPROCESS that PRINTS the session id; the cores NEVER import it. Shared by BOTH hooks' adapters AND the plans-skill marker recipe - single source, Family D)*
- `ai-playbook/agents/hooks/lessons-recall/claude.sh` *(new)*
- `ai-playbook/agents/hooks/lessons-recall/codex.sh` *(new)*
- `ai-playbook/agents/hooks/lessons-recall/cursor.sh` *(new)*
- `ai-playbook/agents/hooks/lessons-recall/agy.sh` *(new)*
- `ai-playbook/agents/hooks/lessons-recall/README.md` *(new)*

- [x] session_channel.py (r10-B1 Decision 1: shared MODULE in `scripts/`, leaf, same tier as
  `facts_paths.py`/`lessons_corpus.py`; per the Symlink model term it is SYMLINKED to
  `~/.ai-playbook/scripts/` - a DEVIATION from the four existing copy-synced lessons scripts, whose
  cleanup is out of scope). It is a SUBPROCESS that PRINTS the session id via
  `sys.stdout.write(...)` with NO trailing newline (r11-L9: so the captured value is independent of
  the shell's newline-stripping; the `$(...)` capture form is no longer load-bearing on
  newline-stripping). It writes `os.environ.get("CLAUDE_CODE_SESSION_ID") or ""` (Claude at v9; empty
  for Codex/Cursor/agy). It is NOT imported by the cores (`skill_gate.py`, `lessons_recall.py`
  accept `--session-id` as OPAQUE data; all session-channel knowledge lives in the leaf - the
  agent-agnostic-core invariant and the "cores depend only downward" claim both hold). Adapters and
  the plans-skill marker recipe invoke it VERBATIM as
  `SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"`; when `SID` is empty, the adapter
  OMITS `--session-id`. This is the Family-D single-source claim enforced by a real shared artifact,
  not an import. DOCSTRING NOTE (r10-L7/L8): a second verified per-agent env var adds a branch in the
  helper + a new selftest arm - stated as a KNOWN EXTENSION POINT, NOT as zero-cost (v9 has one
  channel). Drop the "one line per new agent" extension-point language and the
  `elif agent_env_var in os.environ` branch shape; state the helper plainly. Expose `--selftest` (the
  `#derive_session_channel_env_var` selftest, Task 7)
- [x] claude.sh (subprocess session model - r10-B1): read stdin JSON, extract `.prompt` with
  python3 (NOT jq; see Design Invariant), pipe to core (`--prompt`); derive the session VERBATIM as
  `SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"` (Claude: prints
  `CLAUDE_CODE_SESSION_ID`) and pass `--session-id "$SID"` to the core (when `SID` is empty the
  adapter OMITS `--session-id`); if SID is empty-after-strip, emit a stderr warning
  `CLAUDE_CODE_SESSION_ID absent; running in no-session mode` BEFORE invoking the core (r12-M4
  relocated alarm - the Claude adapter is the one place that knows its own identity; for
  Codex/Cursor/agy empty is documented steady state, so only Claude warns); build the envelope ONLY
  via
  `json.dumps({"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext": <core stdout>}})`
  when stdout is non-empty (dict construction, never f-string; M3); exit 0 always; discard core stderr
- [x] codex.sh: read the Codex hook payload, extract the prompt with **python3** (NOT jq; see Design
  Invariant - state the Codex delivery channel: stdin JSON or env), pipe to core (`--prompt`); derive
  the session VERBATIM as `SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"`; when `SID` is
  non-empty pass `--session-id "$SID"`, when empty (v9 steady state for Codex) OMIT `--session-id` ->
  core keys `no-session` (full window - r10-M10: omitting `--session-id` NO LONGER halves any window;
  the DOCUMENTED STEADY STATE for this agent, NOT a degraded fallback); build the envelope ONLY via
  `json.dumps({"additionalContext": <core stdout>})` when non-empty (M3); exit 0 always
- [x] cursor.sh: best-effort sessionStart one-shot (Cursor cannot silently inject per prompt); emit a
  compact family index built directly from the corpus by iterating `lessons_corpus.iter_lessons` and
  picking the lowest-numbered lesson per present family INLINE (inline selection in the adapter; no
  shared helper); derive the session VERBATIM as
  `SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"`; when non-empty pass `--session-id`,
  when empty (v9 steady state for Cursor) OMIT `--session-id` -> `no-session` (full window), so the
  per-(project,session) state file is keyed consistently even for the one-shot; document the
  limitation in README
- [x] agy.sh: `PreInvocation` adapter. Read stdin, extract the prompt with python3 (NOT jq), pipe to
  core (`--prompt`); derive the session VERBATIM as
  `SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"`; when non-empty pass `--session-id`,
  when empty (v9 steady state for agy) OMIT `--session-id` -> `no-session` (full window). Build a
  TOP-LEVEL envelope ONLY via `json.dumps({"additionalContext": <core stdout>})` when non-empty (no
  `hookSpecificOutput` wrapper; that fails agy schema validation). Exit 0 always. ASSUMPTION
  (documented in README, validated fix-on-first-use, r6): the context-injection field for agy
  `PreInvocation` is `additionalContext` (the article describes the event but does not show the field
  in a concrete example); ship it LIVE wired, and on the first real agy session confirm the injected
  text surfaces in the agent's next turn - if it does not, correct the field name and re-test
- [x] README.md (per Terms Skill-gate marker + Session key for the full contract; this bullet states
  only the LOCAL elements):
  - Per-agent wiring recipes (Claude settings.json UserPromptSubmit entry; Codex `[hooks]` event;
    Cursor sessionStart; agy `~/.gemini/antigravity-cli/hooks.json` with `PreInvocation` and an
    ABSOLUTE `command` path), the symlink targets, the jq-free/python-parse adapter convention, the
    json.dumps-envelope invariant.
  - Install model (per Symlink model term): `session_channel.py` is a `scripts/` leaf SYMLINKED to
    `~/.ai-playbook/scripts/session_channel.py` (the new cores + helper are symlinked; the four
    existing copy-synced lessons scripts are out of scope); the adapters are symlinked into each
    agent's `~/` hook dir. The README carries a short "Install" subsection with the FULL literal
    block (copied byte-for-byte from the Task 3 INSTALL step):
    ```bash
    # r12-M2: create target parent dirs that do not always exist on a default install
    # (measured: ~/.codex/hooks/ and ~/.gemini/antigravity-cli/hooks/ MISSING; ~/.claude/hooks/ and
    # ~/.cursor/hooks/ exist; mkdir -p on the latter is harmless belt-and-suspenders).
    # r13-M3: ~/.ai-playbook/scripts/ is the symlink TARGET dir for the cores + helper.
    mkdir -p ~/.ai-playbook/scripts ~/.codex/hooks ~/.gemini/antigravity-cli/hooks ~/.claude/hooks ~/.cursor/hooks
    # Helper symlinked to ~/.ai-playbook/scripts/ (subprocess-invoked by every adapter + the plans recipe)
    ln -sf ~/Projects/myrepos/ai-playbook/scripts/session_channel.py ~/.ai-playbook/scripts/session_channel.py
    ln -sf ~/Projects/myrepos/ai-playbook/scripts/lessons_recall.py    ~/.ai-playbook/scripts/lessons_recall.py
    # Four lessons-recall adapter symlinks (absolute targets)
    ln -sf ~/Projects/myrepos/ai-playbook/agents/hooks/lessons-recall/claude.sh ~/.claude/hooks/lessons-recall.sh
    ln -sf ~/Projects/myrepos/ai-playbook/agents/hooks/lessons-recall/codex.sh  ~/.codex/hooks/lessons-recall.sh
    ln -sf ~/Projects/myrepos/ai-playbook/agents/hooks/lessons-recall/cursor.sh ~/.cursor/hooks/lessons-recall.sh
    ln -sf ~/Projects/myrepos/ai-playbook/agents/hooks/lessons-recall/agy.sh    ~/.gemini/antigravity-cli/hooks/lessons-recall.sh
    ```
    the INSTALL step runs these literal commands.
  - Session channel (per Terms "Session key"): derivation is a SUBPROCESS invocation, NOT an import -
    the VERBATIM idiom `SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"` is pinned in the
    README so the plans-skill marker recipe and every adapter use the SAME artifact (Family D single
    source). When `SID` is empty the adapter OMITS `--session-id` -> core keys `no-session` (full
    window - per Terms; per-session isolation is Claude-only at v9).
  - Window + budget (r10-M10/L6): `RECALL_DEDUP_WINDOW` default 86400s/24h; ALL agents use the FULL
    window unconditionally. `--budget` default 1500 chars (measured on the injected body before
    json.dumps wrapping; FLAGGED, user-tunable; HEAD-truncated). Observability (per Terms "LOUD
    keying mode"): `~/.ai-playbook/logs/hooks.log` records one JSON line per consultation. The CORE
    emits `keying=env-var` (Claude steady state) / `keying=project-only` (Codex/Cursor/agy steady
    state at v9; PURE LOG METADATA, drives NO core branch; the Claude adapter warns
    `CLAUDE_CODE_SESSION_ID absent; running in no-session mode` on empty SID - r12-M4 relocated
    alarm); the RESOLVER `facts_paths.resolve_project_key` emits `keying=no-anchor` to the SAME file
    on its git-failure branch (r15-M1 sink fix; the shared `_append_hooks_log_line` helper in Terms
    step 3 writes the line DIRECTLY to `hooks.log`, so the token survives adapter stderr-discard;
    alarm, non-git dirs only per B1; in a non-git tree `project` is cwd-derived and unstable across
    `cd` - r12-L4). The runtime paths (`~/.ai-playbook/runtime/lessons-recall/`,
    `~/.ai-playbook/logs/hooks.log`) are disposable; safe to delete.
  - Dedup behavior (per Terms; local element): append-only home-anchored state file PATH-ISOLATED per
    (project,session) at `~/.ai-playbook/runtime/lessons-recall/<project>.<session>.state`, membership
    key `N`, file grows unbounded within a session and is safe to delete per-session - r7-M5. The
    `<project>` component derives `project` via the shared `facts_paths.resolve_project_key` (the ONE
    function both cores import; do NOT re-implement; see Terms Skill-gate marker).
- [x] Verify Codex exposes a prompt-equivalent hook event (`user_prompt_submit` preferred, else
  `session_start`); record the chosen event in README
- [x] Verify the agy `PreInvocation` context-injection field name on the FIRST real agy session (see
  agy.sh bullet); record the outcome in README. (The session channel is NOT an agy-payload
  assumption - r10: the adapter derives it via the shared `session_channel.py` subprocess.) Until then
  the assumption is documented and the adapter ships live; correction is fix-on-first-use
- [x] INSTALL step (r11-B2: pin the literal install commands; ALL FOUR adapters LIVE, r6). The new
  cores (`lessons_recall.py`, `skill_gate.py`) and the helper (`session_channel.py`) are SYMLINKED to
  `~/.ai-playbook/scripts/` - a DEVIATION from the four existing copy-synced lessons scripts
  (`lessons_index.py`/`lessons_adopt.py`/`lessons_migrate.py`/`lessons_corpus.py`, whose cleanup is
  OUT OF SCOPE). Run these literal commands:
  ```bash
  # r12-M2: create target parent dirs that do not always exist on a default install
  # (measured: ~/.codex/hooks/ and ~/.gemini/antigravity-cli/hooks/ MISSING; ~/.claude/hooks/ and
  # ~/.cursor/hooks/ exist; mkdir -p on the latter is harmless belt-and-suspenders).
  # r13-M3: ~/.ai-playbook/scripts/ is the symlink TARGET dir for the cores + helper.
  mkdir -p ~/.ai-playbook/scripts ~/.codex/hooks ~/.gemini/antigravity-cli/hooks ~/.claude/hooks ~/.cursor/hooks
  # Helper symlinked to ~/.ai-playbook/scripts/ (subprocess-invoked by every adapter + the plans recipe)
  ln -sf ~/Projects/myrepos/ai-playbook/scripts/session_channel.py ~/.ai-playbook/scripts/session_channel.py
  ln -sf ~/Projects/myrepos/ai-playbook/scripts/lessons_recall.py    ~/.ai-playbook/scripts/lessons_recall.py
  # Four lessons-recall adapter symlinks (absolute targets)
  ln -sf ~/Projects/myrepos/ai-playbook/agents/hooks/lessons-recall/claude.sh ~/.claude/hooks/lessons-recall.sh
  ln -sf ~/Projects/myrepos/ai-playbook/agents/hooks/lessons-recall/codex.sh  ~/.codex/hooks/lessons-recall.sh
  ln -sf ~/Projects/myrepos/ai-playbook/agents/hooks/lessons-recall/cursor.sh ~/.cursor/hooks/lessons-recall.sh
  ln -sf ~/Projects/myrepos/ai-playbook/agents/hooks/lessons-recall/agy.sh    ~/.gemini/antigravity-cli/hooks/lessons-recall.sh
  ```
  (The Task 5 INSTALL step adds the matching `skill_gate.py` + four skill-gate adapter symlinks.)
  Without this step, `SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"` exits 127 on first
  run, the adapter captures empty stdout, omits `--session-id`, and the gate silently runs in
  `no-session` mode for Claude too (the exact r7-B1 silent degradation).
- [x] Echo-pipe tests pass for all four adapters
- [x] Commit: `feat(lessons-recall): per-agent adapters + shared session_channel helper + wiring recipes`

### Task 4: skill-gate core (`skill_gate.py`)

Files:
- `ai-playbook/scripts/skill_gate.py` *(new)*

- [x] `skill_gate --selftest#block_without_marker`; given a Write of a path under `{plans_dir}` with no plans-marker, expects a block decision naming the plans skill
- [x] `skill_gate --selftest#allow_with_fresh_marker`; given the same Write with a marker keyed by the SAME `(project, session)` the gate derives and mtime within `SKILL_GATE_WINDOW`, expects allow (the body is forensic-only, not a checked guard - r7-M4)
- [x] `skill_gate --selftest#block_with_stale_marker`; given the same Write with a marker older than `SKILL_GATE_WINDOW`, expects block (pins the timestamp-window design)
- [x] `skill_gate --selftest#block_with_future_dated_marker`; given a marker with `mtime = now + 86400` (or `mtime == 0`), expects BLOCK (a negative delta is stale, NOT a perpetual allow; pins M4-future)
- [x] `skill_gate --selftest#block_cross_session_marker`; given the SAME project (repo anchor equal) but a DIFFERENT `session_id` than the gate's, expects BLOCK - the gate looks up its OWN session's marker file (`plans.<project>.<gate-session>.marker`), which is ABSENT, so it blocks (pins PER-SESSION isolation, r6/r9: a fresh marker from session A must not admit session B's writes in the same repo; PER-SESSION isolation is Claude-only at v9 - this selftest exercises the Claude `--session-id` path; a project-only-keyed impl would false-allow here)
- [x] `skill_gate --selftest#same_session_pair`; TRIVIAL SANITY selftest (r8 demotes this from the r7 B1 gate - a headless core selftest feeds the SAME id to both sides by construction and CANNOT detect a live divergent pair): given a marker written under `(project, session=X)` and a gate that resolves the SAME `(project, session=X)` within window, expects ALLOW. This only confirms the read/write path uses the supplied id consistently; the SOLE B1 discriminator is the Task 7 LIVE Claude write-then-read (r9: no per-adapter PID live test)
- [x] `skill_gate --selftest#absent_dir_blocks_not_failopens`; given a gate cwd whose runtime dir `~/.ai-playbook/runtime/skill-invoked/` does NOT exist (fresh install) and a Write target under `{plans_dir}`, expects BLOCK (NOT allow). Pins r8-M4: the gate `os.makedirs(dir, exist_ok=True)` before `os.stat`, so a missing dir cannot raise `FileNotFoundError` (an OSError) and fail-OPEN the gate; the absent-marker branch is always reachable, faithful to "absent marker ALWAYS blocks" on the FIRST plan write of a fresh install
- [x] `skill_gate --selftest#block_no_session_fallback` (r10-M10: halved arm DROPPED); given an
  agent that cannot provide a session id (`--session-id` absent/empty - the Codex/Cursor/agy STEADY
  STATE at v9), the marker is looked up under the `no-session` key; a marker written under that key
  within the FULL `SKILL_GATE_WINDOW` -> ALLOW, an absent marker -> BLOCK. Pins the simpler
  no-session -> `no-session` key path; the halved-vs-full window assertions are REMOVED (all agents
  use the FULL window unconditionally)
- [x] `skill_gate --selftest#reroot_absent_path_blocks`; given the repo re-rooted between skill turn and gate turn to a DIFFERENT repo (both sides call `resolve_project_key`; the derived `project` hashes for the two repos DIFFER per Terms (Skill-gate marker)), expects BLOCK via the ABSENT-marker path - the gate derives a DIFFERENT `project` and looks up a filename that was never written (pins that re-root protection comes from the `project` filename component itself, NOT a body-equality check - r7-M4; the body field is forensic/debug metadata only, never a checked guard). NOTE (r9-M2/r10-B2): re-rooting WITHIN THE SAME REPO (e.g. invoking the skill from the repo root then `cd`-ing into a subdir before the Write) does NOT block - the toplevel anchor is STABLE across in-repo navigation, so `project` is byte-identical on both sides; covered by `#project_stable_across_sibling_cwd`
- [x] `skill_gate --selftest#plans_dir_default_classification`; given a gate cwd with NO resolvable `.ai-playbook/facts.md` (e.g. a git WORKTREE, where the gitignored facts file is absent) and a Write target `docs/plans/x.md`, expects the target STILL CLASSIFIED as gated via the `docs/plans/` default (pins that classification works WITHOUT facts resolution - the r5-B1 worktree hole is closed by default-suffix classification, not by resolving a worktree-absent tmp_dir)
- [x] `skill_gate --selftest#session_empty_string_treated_as_absent` (r10-M4; r11-M3 two arms;
  r12-M8 byte-identical filename pin): TWO arms: (a) `--session-id ""` (empty string after strip);
  (b) `--session-id "   "` (whitespace-only after strip). BOTH are treated IDENTICALLY to absent ->
  keys the literal `no-session` AND logs `keying=project-only` (full window). ASSERT the resolved
  marker/state FILENAME for the whitespace input is BYTE-IDENTICAL to the empty-string input arm ->
  BOTH contain the literal token `no-session` (e.g. `plans.<project>.no-session.marker`); ASSERT the
  derived `session` variable equals the literal string `"no-session"` (for BOTH arms). RATIONALE
  (L7): the empty-string arm defends against the `da39a3ee5e6b4b0d` constant collision
  (`sha1(b"")`); the whitespace arm defends against a stable-but-meaningless alias
  (`sha1(b"   ")` = `088fb1a4ab057f4f`, not the constant, not `no-session`). Pins that a
  present-but-empty env var does NOT hash to the constant `da39a3ee5e6b4b0d` and silently bypass the
  `keying=project-only` log line, and that the emptiness check is the FIRST operation (before any
  hashing) so whitespace-only does not reach `sha1(...).hexdigest()` either.
- [x] `skill_gate --selftest#cross_tree_absolute_target_classified` (r10-L5); when the gate cwd is a
  git worktree, an absolute Write target into the MAIN repo's `docs/plans/` is STILL classified as
  gated (the target is checked against the default `docs/plans/` suffix on the target's OWN realpath,
  independent of the cwd-resolved `plans_dir`); a stub that classifies only against the cwd-resolved
  `plans_dir` false-allows here
- [x] `skill_gate --selftest#doctor_pretooluse_array` (r10-M9); given a settings.json whose
  `hooks.PreToolUse` array has BOTH a `"Bash"` entry (for `check-plan-review-gate.sh`) AND a
  `"Write|Edit|MultiEdit"` entry -> PASS; given ONLY the `"Bash"` entry -> FAIL; given a
  `"Write|MultiEdit"` entry (missing `Edit`) -> FAIL. Pins that the doctor iterates the ARRAY, finds
  an entry whose matcher `|`-split alternation is a SUPERSET of `{Write,Edit,MultiEdit}`, and does
  NOT flag the separate `"Bash"` entry missing
- [x] `skill_gate --selftest#doctor_dangling_symlink` (r13-M6; also carries the r12-M3 rationale for
  checking `lessons_recall.py`): create a DANGLING symlink among the 11 doctor paths (target
  removed so `[ -L <path> ] && [ ! -e <path> ]` holds) and assert `--doctor` FAILs loud on it (and
  reports the canonical target via `readlink -f` in the message, informational only). Pins that the
  predicate is `test -e` / dangling-symlink detection - NOT `readlink -f` (which returns a
  non-empty canonicalized target even for a dangling link and would false-pass). ALSO pins why
  `lessons_recall.py` is among the 11: it has no `--doctor` flag and nothing imports it at doctor
  time, so a dangling symlink would silently exit 127 on every prompt with empty stdout =
  byte-identical to "classify returned None" (Family-G silent-disable of the proactive-recall
  feature).
- [x] `skill_gate --selftest#doctor_agy_timeout` (r15-M4; r16-M3 pins the boundary; r17: constant +
  README-value arm): given a synthetic `~/.gemini/antigravity-cli/hooks.json`, parametrize the
  skill-gate `PreToolUse` entry's `timeout` against the imported `facts_paths.RESOLVER_GIT_TIMEOUT_S`:
  `timeout=RESOLVER_GIT_TIMEOUT_S` -> `--doctor` FAILs (equals the resolver's git timeout, would
  preempt it); `timeout=RESOLVER_GIT_TIMEOUT_S + 1` -> PASSES (the lower bound); `timeout =
  2 * RESOLVER_GIT_TIMEOUT_S` -> PASSES (r17-L2: the README install value, pinning the bound against an
  `== RESOLVER_GIT_TIMEOUT_S + 1` misimplementation that false-fails the shipped recipe); `timeout`
  ABSENT -> FAILs. Pins the `> RESOLVER_GIT_TIMEOUT_S` bound, the README value, and the absent-field
  case so an implementer cannot omit check (5) and still pass the doctor selftest suite.
- [x] `skill_gate --selftest#project_not_aliased_across_sibling_worktree` (r10-B2; r11-B1/M4
  tightened); TWO sibling EXTERNAL git worktrees (neither has a `.ai-playbook/facts.md` - it is
  gitignored). For a NAMED fixture pair (e.g. worktree A at `/tmp/wt_a`, worktree B at `/tmp/wt_b`),
  assert: (a) `project` for A = `sha1(realpath("/tmp/wt_a").encode()).hexdigest()[:16]` and
  `project` for B = `sha1(realpath("/tmp/wt_b").encode()).hexdigest()[:16]` - the CONCRETE expected
  hex values for the fixture, and they DIFFER (each keys on its OWN toplevel, so two sibling
  worktrees are NOT aliased to one hash); (b) `hooks.log` carries `keying=env-var` or
  `keying=project-only` for BOTH (NOT `keying=no-anchor` - `git rev-parse` SUCCEEDS for an external
  worktree, so the no-anchor branch does NOT fire). After r11-B1, an external worktree (no facts
  file) keys on `sha1(realpath(git_toplevel))` and does NOT fire `no-anchor`. Pins that the walk-up
  is BOUNDED by `git rev-parse --show-toplevel` and never aliases every sibling repo to one
  ownership `project` hash, AND pins the concrete `keying=` label. (r13-L8; r14-M3 return is now
  `-> str`; r15-L3: the appended resolver-call clause is DROPPED here as duplicative - the
  different-hash BLOCK above already proves the resolver is called; the canonical behavioral
  assertion lives in `#project_stable_across_sibling_cwd_in_worktree` and `#project_filename_uses_resolver`.)
- [x] `skill_gate --selftest#project_stable_across_sibling_cwd_in_worktree` (r11-B1 discriminator;
  r12-M1: both sides call the shared `facts_paths.resolve_project_key`); a SINGLE external git
  worktree with NO `.ai-playbook/facts.md` (gitignored). The skill invokes `--write-marker` from the
  worktree ROOT, then the gate fires `--target <plan>` from a SUBDIR of the SAME worktree. Expects
  the SAME `project` hash on both sides (both derive from `sha1(realpath(toplevel))`, STABLE across
  in-worktree cd) -> ALLOW. A `realpath(cwd)` fallback FAILS this (it derives different hashes for
  root vs subdir -> permanent FALSE BLOCK - the r10-B1 regression on the load-bearing r5 case).
  (r13-L8; r14-M3 return is now `-> str`) ADDITIONALLY assert the resolved marker filename's
  `project` component EQUALS `facts_paths.resolve_project_key(<same fixture start_dir>)` (a plain
  `str` return, NOT a tuple; no `[0]`) and that the core actually CALLS the resolver (not just
  imports it).
- [x] `skill_gate --selftest#project_no_anchor_in_non_git_dir` (r11-B1/M5; r15-M1 tightens to the
  FILE); a non-git cwd (no `.git`): both the skill `--write-marker` and the gate derive
  `project = sha1(realpath(cwd))` AND the `hooks.log` FILE carries `keying=no-anchor` (monkeypatch
  `HOME` to a tmp dir - r16-L3, resolver derives the log path from `Path.home()`; read back the REAL
  file the resolver opened with `os.open` - NOT a `logging` record; this is the r15-M1 sink-fix
  discriminator: a `logging.warning` impl leaves the file empty and FAILS here; r16-L4/r18-L2: also
  `json.loads` the LAST non-empty line -> a dict with EXACTLY `{"ts": ..., "keying": "no-anchor"}`
  keys (no `WARNING:`/`levelname`/`Formatter` prefix); a `logging.FileHandler` impl with default
  formatting fails `json.loads` (byte-identical to the Task 1 resolver selftest wording). Pins the non-git branch AND the realpath choice (resolves M5: macOS `/tmp` vs
  `/private/tmp` symlink - both sides realpath, so they agree). This is the ONLY branch where
  `realpath(cwd)` + `no-anchor` fire. r17-M1 ABSENT-PARENT ARM (core side; r18-M2 GIT-REPO CWD PIN):
  set `HOME` to a tmp dir whose `.ai-playbook/logs/` does NOT pre-exist AND run the core consultation
  from a GIT-REPO cwd (NOT the non-git cwd of the primary arm) so the resolver's `git rev-parse`
  SUCCEEDS, its no-anchor branch does NOT fire, and the resolver does NOT call the helper / does NOT
  pre-create `logs/`; assert the core's own `keying=env-var`/`project-only` line REACHES the file (the
  shared `_append_hooks_log_line` helper's makedirs created the dir). WITHOUT the git-repo pin the
  resolver's no-anchor branch fires first and its helper call makedirs's the dir, so a core that omits
  the helper still finds the dir present and PASSES - non-discriminating. A core that omits the
  helper's makedirs raises `FileNotFoundError` on its own write and the line never reaches the file.
  This mirrors the resolver absent-parent arm so BOTH writers are cold-start-covered.
- [x] `skill_gate --selftest#project_single_source` (r13-M2 moved here from `facts_paths --selftest`;
  downward import only): assert `skill_gate.resolve_project_key is facts_paths.resolve_project_key`
  (IDENTITY, not equality - the core must import the SAME function object, not a copy). A core that
  copies the function body fails its own `is` check; a second copy would drift silently and desync the
  marker key from the dedup state key (Family D).
- [x] `skill_gate --selftest#absent_marker_blocks`; given a Write of a path under `{plans_dir}` with NO plans-marker present (regardless of whether the plans skill was recently invoked - the gate has no way to know and consults NO second signal), expects BLOCK. Discriminating only as a PAIR with `#allow_with_fresh_marker`: a stub that always-blocks passes THIS selftest and fails the allow-arm, so keep both (r5-L4)
- [x] `skill_gate --selftest#non_gated_path`; given a Write of `src/foo.py`, expects allow (not a gated artifact)
- [x] `skill_gate --selftest#traversal_bypass`; given a Write of `src/../../docs/plans/x.md`, AND a second arm where `plans_dir` is itself a SYMLINK to `<elsewhere>/plans/` with a Write target inside it, expects BOTH classified as gated (realpath subtree check on BOTH the target AND `realpath(plans_dir)`, never `str.startswith` and never the lexical `plans_dir` string - M4)
- [x] `skill_gate --selftest#fail_open`; given an unreadable marker store (`OSError`/`PermissionError`), expects allow + a stderr warning (never block on a broken gate)
- [x] `skill_gate --selftest#deny_reason_adversarial`; given a block on a target path containing `"`, `}`, newline, and a literal `"allow_tool"` field name, expects the emitted envelope to round-trip `json.loads` with `deny_reason` as ONE string (pins L9; `deny_reason` is data-influenced and must go through `json.dumps`)
- [x] `skill_gate --selftest#no_em_dash`; given any input, expects no U+2014 in output
- [x] `skill_gate --selftest#write_marker_concurrent` (r11-L6; r12-M6 deterministic forced-collision;
  r13-M4/L7 placement + parent-dir pin): the selftest FIRST ensures
  `{runtime}/skill-invoked/` exists (the same `os.makedirs(dir, exist_ok=True, mode=0o700)` the
  writer uses) BEFORE pre-creating the `.tmp`, so the pre-create cannot raise `FileNotFoundError` and
  mask the `FileExistsError`. PRE-CREATE the marker `.tmp` path
  `{runtime}/skill-invoked/plans.<project>.<session>.marker.tmp` immediately before a SINGLE
  `--write-marker` call; the writer calls `atomic_write_text` which opens `.tmp` with `O_EXCL` ->
  raises `FileExistsError`. Assert: the writer CATCHES `FileExistsError`, exits 0, leaves the marker
  ABSENT or unchanged (NO `os.replace` occurred), and does NOT delete the pre-created `.tmp` out from
  under its holder (the test owns cleanup of its own pre-created `.tmp`). (r14-L8) AFTER the
  `--write-marker` call returns exit 0, RE-`os.stat` the pre-created `.tmp` path and assert it STILL
  EXISTS with the SAME inode/mtime the test set (catches a caller-side `os.unlink` regression in the
  except block). COMMENT: the measure's internal cleanup is unreachable on the O_EXCL path; this
  re-stat guards against a caller-side cleanup regression. The loser-exit-0 contract
  is pinned: "the loser returns exit 0 WITHOUT writing." A SUPPLEMENTARY non-deterministic arm (two
  `--write-marker` calls on the SAME `--session-id` + `--cwd` via `xargs -P 2`) may be retained as a
  sanity check but is not the discriminator. ADDITIONALLY (r13-M4) assert ONE of: (i) the measure
  file `lessons_corpus.py` is UNCHANGED by this task (grep its docstring/contract line - the catch
  lives at the CALL SITE in `skill_gate.py`, not inside `atomic_write_text`), OR (ii)
  `atomic_write_text` RAISES `FileExistsError` (not "catches" it) when `.tmp` exists - proving the
  catch is at the caller.
- [x] Run -> expect RED: `python3 ai-playbook/scripts/skill_gate.py --selftest`
- [x] Implement (per Terms Skill-gate marker + Session key for the full contract; this bullet
  states only the LOCAL elements):
  - **Sibling-import bootstrap (r14-M2).** As the FIRST line after the stdlib imports:
    `sys.path.insert(0, str(Path(__file__).resolve().parent))` (mirrors `lessons_adopt.py:38-41`;
    REQUIRED because the core is symlinked into `~/.ai-playbook/scripts/` and imports sibling leaves
    `facts_paths`/`lessons_classify`/`lessons_corpus` from the repo scripts dir, not
    `~/.ai-playbook/scripts/`; `Path(__file__).resolve().parent` follows the symlink to the repo dir
    where the siblings exist).
  - **Public surface.** Expose TWO functions the doctor asserts: `classify_path(target, plans_dir)
    -> bool` and `check_marker(project, session) -> bool` (r7-L5).
  - **Agent-agnostic core.** The core contains ZERO agent knowledge: it accepts the session string as
    `--session-id <value>` and treats it as OPAQUE data; ALL session-channel knowledge lives in the
    `scripts/session_channel.py` leaf, subprocess-invoked by the adapter, NEVER imported by the core
    (r10-B1; see Session key term).
  - **`project` derivation (per Terms "Skill-gate marker"; r12-M1 collapse).** Call
    `facts_paths.resolve_project_key(start_dir)` and use the returned `project_hash` (a plain `str`;
    do NOT re-implement the derivation locally. The duplicated-VERBATIM-Family-D obligation to
    `lessons_recall.py` is enforced by `#project_single_source` (IDENTITY on one shared function
    object, asserted in each core's own `--selftest` - downward import only).
  - **`session` derivation + sanitization (per Terms "Session key"; r11-M3 both layers normalize).**
    The emptiness check (`.strip() == ""`) is the FIRST operation, before any hashing. An
    empty-after-strip `--session-id` is treated IDENTICALLY to absent -> key the literal `no-session`
    (NOT `sha1("").hexdigest()[:16]` = `da39a3ee5e6b4b0d`, which would be a constant collision -
    r10-M4). Otherwise `session = sha1(<--session-id value>.encode()).hexdigest()[:16]`
    (path-traversal safety; byte-identical write/read for free). When `--session-id` is absent/empty
    (Codex/Cursor/agy project-only STEADY STATE), key the literal `no-session`.
  - **One full window + LOUD keying (per Terms "LOUD keying mode").** ALL agents use the FULL
    `SKILL_GATE_WINDOW` (default 14400s / 4h, FLAGGED) unconditionally. LOG the resolved channel to
    `~/.ai-playbook/logs/hooks.log` on every consultation. r15-M1: the CORE's vocabulary is
    `keying=env-var|project-only` ONLY (r11-M2: PURE LOG METADATA, drives NO core branch - the core is
    agent-agnostic and cannot know which agent is calling it; "Claude missing env var" and "Codex
    steady state" both arrive as `--session-id` absent/empty): `keying=env-var` when `--session-id`
    was supplied (Claude steady state); `keying=project-only` when absent/empty
    (Codex/Cursor/agy steady state at v9). The CORE does NOT emit `keying=no-anchor`: that token is
    written to the SAME `hooks.log` file by `facts_paths.resolve_project_key` itself on its git-failure
    branch (see Terms LOUD keying mode ownership split - the core cannot derive it without re-running
    git, which is forbidden). The resume Monitor + the Task 7 LIVE resume assertion handle the
    missing-env-var case.
  - **Path classification (`classify_path`).** Read `plans_dir` from repo `.ai-playbook/facts.md` via
    `facts_paths.resolve_plans_dir(cwd)` when present, else DEFAULT to `docs/plans/` (FLAGGED
    hardcoded convention). Classify via `os.path.realpath` subtree test (`Path.relative_to`/
    `os.path.commonpath` against `realpath(plans_dir)`, resolving BOTH the target and `plans_dir`
    through realpath - never `str.startswith`, never the lexical `plans_dir` string - M4).
    Cross-tree absolute target (r10-L5): when the gate cwd is a worktree, an absolute Write target
    into the MAIN repo is not classified by the cwd-resolved `plans_dir`; ALSO check the target
    against the default `docs/plans/` suffix on the target's OWN realpath (independent of the
    resolved `plans_dir`), so a cross-tree plan write is still gated.
  - **Gated-class set.** Module-level literal with ONE entry (plans-dir -> "plans"); add a comment
    `# v1: one entry; on adding a SECOND entry, promote to a registry (path-prefix -> (skill,
    marker_name, doctor_check)) in the same change` (r6-L6); no registry abstraction in v1 (L3).
  - **Marker lookup + makedirs-before-stat.** `check_marker` at the HOME-ANCHORED path
    `~/.ai-playbook/runtime/skill-invoked/plans.<project>.<session>.marker`: FIRST
    `os.makedirs(dir, exist_ok=True, mode=0o700)` (r8-M4) BEFORE `os.stat(marker_path)`, so a missing
    dir cannot raise `FileNotFoundError` (an OSError) and fail-OPEN the gate; accept iff the file
    EXISTS AND `0 <= (now - mtime) <= SKILL_GATE_WINDOW` (FLAGGED; a future-dated/negative delta or
    `mtime == 0` is STALE -> block, NOT a perpetual allow). The marker BODY is forensic/debug
    metadata ONLY (r7-M4). An ABSENT marker ALWAYS blocks (r4-M1: NO second-signal fallback;
    recovery via `skill_gate --doctor` (Mon1), NOT a gate-side bypass).
  - **Fail-open policy (PermissionError ONLY).** Fail-open ONLY on `PermissionError` (a truly
    broken/unwritable store) - allow + stderr warning + `hooks.log` line whose path label is
    HARDCODED (no untrusted interpolation; exception `filename`/`strerror` passed as a json.dumps
    field, never f-interpolated raw - r8-L6 extends L9 to the log sink); `FileNotFoundError` is NOT
    fail-open (the makedirs + absent-marker branch handle it - r8-M4).
  - **Atomic write + `FileExistsError` catch (r10-L1; r12-M6 loser-exit-0 contract; r13-M4 pins the
    catch at the call site).** `--write-marker` writes ATOMICALLY via
    `lessons_corpus.atomic_write_text` (`O_EXCL|O_NOFOLLOW` + `os.replace`, r8-L3) at mode `0o600`
    (perms mirror the lessons-recall store). The `try/except FileExistsError` wraps the
    `atomic_write_text(...)` CALL SITE inside `skill_gate.py --write-marker`. Do NOT modify
    `atomic_write_text`: its `os.open(tmp, O_EXCL|O_NOFOLLOW)` raises `FileExistsError` BEFORE its
    internal `try:` (the internal `except BaseException` cleanup never runs on the O_EXCL path), so
    the error propagates to the caller; the loser performs NO `os.unlink` and NO `os.replace`.
    CATCH `FileExistsError` from `atomic_write_text` and treat it as BENIGN: the LOSER returns exit 0
    WITHOUT writing (no retry, no `os.replace`, no deletion of a pre-existing `.tmp` out from under
    its holder). A concurrent skill-refresh racing on the SAME marker means another writer is
    refreshing an identically-keyed marker; the winner's marker is fresh and identically keyed, so
    the loser's abort is harmless. Read-side torn-read-safe under concurrent skill-refresh; a
    concurrent WRITE pair aborts the loser benignly with `FileExistsError`, surfaced as a skill-side
    warning.
  - **Deny message.** Emit any deny message through `json.dumps` (the `deny_reason` string is
    data-influenced - L9). The block message EXACT text is "Invoke the plans skill before authoring a
    plan file." (emitted as `deny_reason`; Claude surfaces on stderr + exit 2; agy as
    `{"allow_tool": false, "deny_reason": ...}` exit 0).
  - **Log discipline.** The CORE writes its `hooks.log` lines (one per consultation) by calling the
    shared `_append_hooks_log_line({"ts": <iso8601 utc>, "keying": <env-var|project-only>})` helper
    defined in Terms step 3 (the helper IS the makedirs+`O_NOFOLLOW`+newline recipe; the core restates
    no part of it - r17 collapsed the prior byte-identical duplication). Threat model per Terms step 3
    (r18-L3 back-reference; not restated here).
  - **Doctor (PreToolUse ARRAY - r10-M9; r11-B2/M1 extension; r13-L3 tightened, L9/M6/M3
    literalized; r15-M4 adds check (5)).** `--doctor` does FIVE checks (rationale lives in the cited
    selftests):
    (1) **PreToolUse array.** Iterates `settings.json['hooks']['PreToolUse']`; finds an entry whose
    `matcher` `|`-split alternation is a SUPERSET of `{Write,Edit,MultiEdit}`; FAILs iff none. ALSO
    asserts a SEPARATE `"Bash"` entry (for `check-plan-review-gate.sh`) is preserved. See
    `#doctor_pretooluse_array`.
    (2) **11 paths live + parent dirs exist (r11-B2; r12-M3; r13-L9 literal lessons-recall paths,
    r13-M6 predicate, r13-M3 scripts parent dir).**
    - **Predicate:** for EACH of the 11 paths, FAIL LOUD iff `test -e <path>` is false OR
      (`[ -L <path> ] && [ ! -e <path> ]`, a dangling symlink); `readlink -f` is informational only.
    - **The 11 paths:** helper + 2 cores + 8 adapters (the literal list lives in the Task 3/5
      INSTALL `ln -sf` blocks).
    - **ALSO each parent dir exists:** `~/.ai-playbook/scripts/`, `~/.codex/hooks/`,
      `~/.gemini/antigravity-cli/hooks/`, `~/.claude/hooks/`, `~/.cursor/hooks/`. See
      `#doctor_dangling_symlink` for the predicate + the `lessons_recall.py` rationale.
    (3) **Subprocess idiom (r11-M1).** grep each adapter (`agents/hooks/skill-gate/*.sh` AND
    `agents/hooks/lessons-recall/*.sh`) AND the plans-skill marker recipe for the literal
    `python3 ~/.ai-playbook/scripts/session_channel.py`; FAIL if any adapter reads
    `CLAUDE_CODE_SESSION_ID` directly or omits the helper call. See the Family-D single-source note
    in Terms (Session key).
    (4) **Core-symbol + writable runtime (r10-M9).** Verify the installed core IMPORTS and resolves
    symbols (`classify_path`, `check_marker` - r7-L5; NOTE r10/r9: `derive_session` is NO LONGER a
    core symbol - it is the `scripts/session_channel.py` leaf, so the doctor does NOT assert it on
    the core); CREATES `~/.ai-playbook/runtime/skill-invoked/` if absent (r7-M6/r8-M4); confirms
    that dir is WRITABLE BY THE SKILL's uid.
    (5) **agy hook timeout (r15-M4).** Read `~/.gemini/antigravity-cli/hooks.json` and FAIL iff NO
    `PreToolUse` entry carrying the skill-gate matcher has `timeout > RESOLVER_GIT_TIMEOUT_S` (must
    exceed the resolver's internal git timeout, else a hung git makes agy kill the hook before the
    resolver's `TimeoutExpired` catch fires -> agy treats hook-kill as failure, not block -> gate
    silently off).
    r16-L5: the `timeout` FIELD PATH inside `hooks.json` is verified at BUILD TIME alongside the
    other agy assumptions (see Task 5 README + the Monitor "agy field names are ASSUMED" list, which
    now carries it as assumption (c)); the doctor asserts the verified path. r17/r18 LOCKSTEP: the
    `RESOLVER_GIT_TIMEOUT_S` named constant (Terms step 3) IS the lockstep for the Python consumers
    (doctor reads `timeout > facts_paths.RESOLVER_GIT_TIMEOUT_S`, selftest imports it); the README
    recipe `timeout >= 2 * RESOLVER_GIT_TIMEOUT_S` is PROSE and its literal must be HAND-SYNCED on a
    constant change (the doctor FAIL backstops a stale install). See `#doctor_agy_timeout`.
  - **Flags accepted.** `--target PATH`, `--session-id ID` (adapter-supplied; absent/empty ->
    `no-session` key + full window), `--cwd DIR`, `--write-marker` (writes the marker using the
    adapter-supplied `--session-id` + bounded repo-anchor `project` + the atomic recipe), `--doctor`
    (PreToolUse array check above), `--selftest`.
- [x] Run -> expect GREEN: `python3 ai-playbook/scripts/skill_gate.py --selftest`
- [x] Commit: `feat(skill-gate): agent-agnostic core with timestamp-window marker`

### Task 5: skill-gate adapters + symlinks + wiring

Files:
- `ai-playbook/agents/hooks/skill-gate/claude.sh` *(new)*
- `ai-playbook/agents/hooks/skill-gate/codex.sh` *(new)*
- `ai-playbook/agents/hooks/skill-gate/cursor.sh` *(new)*
- `ai-playbook/agents/hooks/skill-gate/agy.sh` *(new)*
- `ai-playbook/agents/hooks/skill-gate/README.md` *(new; SINGLE SOURCE for the marker WRITE RECIPE - M7/r7-L2)*

- [x] claude.sh (subprocess session model - r10-B1): PreToolUse on Write/Edit/MultiEdit; read
  `.tool_input.file_path` with python3 (NOT jq; see Design Invariant); derive the session VERBATIM as
  `SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"` (Claude: prints
  `CLAUDE_CODE_SESSION_ID`) and pass `--session-id "$SID"` to the core (`--target`); when `SID` is
  empty OMIT `--session-id`; if SID is empty-after-strip, emit a stderr warning
  `CLAUDE_CODE_SESSION_ID absent; running in no-session mode` BEFORE invoking the core (r12-M4
  relocated alarm - only the Claude adapter warns; for Codex/Cursor/agy empty is documented steady
  state); build any block decision via `json.dumps` (M3). PINNED CONTRACT (M6):
  match the only wired precedent - `check-plan-review-gate.sh` blocks via `exit 2` + reason on
  stderr, exit 0 on allow. The block message EXACT text is "Invoke the plans skill before authoring a
  plan file." (emitted as `deny_reason`; written to stderr AND exit 2 on block, exit 0 on allow). The
  `~/.claude/settings.json` `PreToolUse` entry IS IN SCOPE as a required install step (r8-M6: THIS
  hook's matcher MUST be `Write|Edit|MultiEdit`, stated verbatim in the README install recipe and
  verified by `skill_gate --doctor`). Add a selftest that, given a block decision, asserts BOTH
  stderr-reason AND exit 2.
- [x] codex.sh (r10-M8: deliverable GATED on blocking verification; r12-M5: config-file gate):
  Codex `pre_tool_use`. The installed `~/.codex/config.toml` shows
  `post_tool_use = "~/.agents/scripts/learn-counter-codex.sh"` (which cannot block); verify Codex
  actually exposes a BLOCKING `pre_tool_use` event and cite the source. CONFIG-FILE GATE (r12-M5):
  VERIFY which config file Codex consults for a BLOCKING `pre_tool_use` event at BUILD TIME -
  `~/.codex/config.toml` `[hooks]` table vs `~/.codex/hooks.json` `hooks.PreToolUse` array (measured:
  `config.toml` has only `post_tool_use`; `hooks.json` carries `SessionStart` in array shape). Pin
  the literal edit for the VERIFIED-LIVE location and PRESERVE `post_tool_use`. BUILD-TIME PROBE
  (r13-M8): run the literal `grep -nE 'pre_tool_use|PreToolUse' ~/.codex/config.toml ~/.codex/hooks.json`;
  PASS/FAIL: non-empty match in exactly one file -> wire `codex.sh` there; empty in both -> record a
  no-op (do NOT install `codex.sh`); the README records the verified file by name. INSTALL GATE: state
  the literal edit that ADDS the blocking entry WITHOUT removing the existing `post_tool_use` line
  (do NOT regress an existing wired hook - Family G); the doctor asserts BOTH the `post_tool_use`
  line AND the new blocking entry survive, AND asserts (r12-M5) the Codex config entry pointing at
  `~/.codex/hooks/skill-gate.sh` exists (in whichever file the build-time check verified). IF Codex
  lacks blocking `pre_tool_use`, `codex.sh` is NOT installed and
  the README records a no-op (this is a Task 5 GATE, not just a Monitor note). Emit the Codex
  deny/allow JSON via `json.dumps` (M3); read the path with python3; derive the session VERBATIM as
  `SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"`; when non-empty pass `--session-id`,
  when empty (v9 steady state for Codex) OMIT `--session-id` -> core keys `no-session` (full window -
  r10-M10; DOCUMENTED STEADY STATE, NOT a degraded fallback); pass to core (`--target`).
- [x] cursor.sh: Cursor `preToolUse` matcher Write|EditNotebook (full-fidelity blocking, unlike
  lessons-recall); extract the target path from the Cursor tool input with python3 (NOT jq; see
  Design Invariant - L2); derive the session VERBATIM as
  `SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"`; when non-empty pass `--session-id`,
  when empty (v9 steady state for Cursor) OMIT `--session-id` -> `no-session` (full window); pass to
  core (`--target`); verify the exact Cursor tool-name matcher.
- [x] agy.sh: `PreToolUse` adapter, matcher `write_to_file|replace_file_content|multi_replace_file_content`
  (the agy file-management tools; confirmed in the article). Read stdin, extract the target path from
  `.toolCall.args` with python3 (jq may be absent on agy hosts; python3 is the fallback); derive the
  session VERBATIM as `SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"`; when non-empty
  pass `--session-id`, when empty (v9 steady state for agy) OMIT `--session-id` -> `no-session` (full
  window). ASSUMPTION (documented in README, validated fix-on-first-use, r6): the path field inside
  `.toolCall.args` is `path` (the article is not concrete for file tools); ship it LIVE wired, and on
  the first real agy session confirm a `write_to_file` of a plan file is gated - if not, correct the
  field name and re-test. Call the core (`--target`); emit a TOP-LEVEL `json.dumps({"allow_tool":
  True})` to allow or `json.dumps({"allow_tool": False, "deny_reason": <core message>})` to block;
  **exit 0 always** (non-zero = hook failure on agy, NOT a block). Never wrap in `hookSpecificOutput`.
  This is full-fidelity: agy CAN block.
- [x] README.md (per Terms Skill-gate marker + Session key for the full contract; this bullet states
  only the LOCAL elements - r8-L7 collapses the prior 4x path/body/window restatement):
  - Per-agent wiring recipes (Claude PreToolUse exit-2+stderr contract with the concrete settings.json
    `Write|Edit|MultiEdit` entry - r8-M6/r10-M9; Codex `[hooks]` pre_tool_use ADDING the key without
    removing `post_tool_use` - r10-M8; Cursor preToolUse; agy
    `~/.gemini/antigravity-cli/hooks.json` `PreToolUse` with matcher regex and an ABSOLUTE `command`
    path + `timeout >= 2 * RESOLVER_GIT_TIMEOUT_S` (r17: was the literal `timeout=10`; now derived
    from the constant) - r15-M4: MUST exceed the resolver's internal git timeout or agy kills the
    hook before the resolver's `TimeoutExpired` catch fires, silently disabling the gate; r16-L5 the
    `timeout` FIELD PATH inside `hooks.json` is build-time-verified as agy assumption (c) - see the
    Monitor "agy field names are ASSUMED" list). r15-M3: the README RECORDS which file the Codex build-time probe verified
    (`~/.codex/config.toml` `[hooks]` table OR `~/.codex/hooks.json` `PreToolUse` array) carries the
    blocking `pre_tool_use` entry, so the doctor's later assertion against that file is auditable; if
    the probe returned empty in both, the README records a Codex skill-gate no-op.
  - SINGLE-SOURCE POLICY: the README is the single source for the byte-identical marker WRITE RECIPE;
    the plans SKILL.md step REFERENCES it (does not restate the constants - r3-M7). Terms and the
    Design Invariant STATE THE CONTRACT and MUST be co-edited with the README if constants change.
  - VERBATIM subprocess invocation (r10-B1 Decision 1): BOTH the plans-skill marker recipe AND every
    adapter use `SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"`; when `SID` is empty the
    adapter OMITS `--session-id`. This pins the Family-D single-source claim to a real shared artifact.
  - WRITE recipe (per Terms; local elements): FIRST `os.makedirs(~/.ai-playbook/runtime/skill-invoked/,
    exist_ok=True, mode=0o700)` (r8-M4), then ATOMICALLY write via
    `lessons_corpus.atomic_write_text` (`O_EXCL|O_NOFOLLOW` + `os.replace`, r8-L3) at mode `0o600`;
    `--write-marker` CATCHES `FileExistsError` and treats it as benign (r10-L1: a concurrent
    skill-refresh racing on the same marker; the loser's abort is harmless). Acceptance requires the
    file EXISTS AND `0 <= (now - mtime) <= SKILL_GATE_WINDOW` (default 4h, FLAGGED; future-dated/zero
    mtime is stale - M4); ALL agents use the FULL window (r10-M10). The marker filename's `project`
    component derives `project` via the shared `facts_paths.resolve_project_key` (the ONE function
    both cores import; do NOT re-implement; see Terms Skill-gate marker).
  - Install subsection: the FULL literal block (copied byte-for-byte from the Task 5 INSTALL step)
    - core + 4 skill-gate adapter symlinks:
    ```bash
    # r12-M2: create target parent dirs that do not always exist on a default install
    # (measured: ~/.codex/hooks/ and ~/.gemini/antigravity-cli/hooks/ MISSING; ~/.claude/hooks/ and
    # ~/.cursor/hooks/ exist; mkdir -p on the latter is harmless belt-and-suspenders). The Task 3
    # INSTALL already mkdir'd these once; re-running here is idempotent and pins the step per-Task.
    # r13-M3: ~/.ai-playbook/scripts/ is the symlink TARGET dir for the cores + helper.
    mkdir -p ~/.ai-playbook/scripts ~/.codex/hooks ~/.gemini/antigravity-cli/hooks ~/.claude/hooks ~/.cursor/hooks
    # Core symlinked to ~/.ai-playbook/scripts/
    ln -sf ~/Projects/myrepos/ai-playbook/scripts/skill_gate.py ~/.ai-playbook/scripts/skill_gate.py
    # Four skill-gate adapter symlinks (absolute targets)
    ln -sf ~/Projects/myrepos/ai-playbook/agents/hooks/skill-gate/claude.sh ~/.claude/hooks/skill-gate.sh
    ln -sf ~/Projects/myrepos/ai-playbook/agents/hooks/skill-gate/codex.sh  ~/.codex/hooks/skill-gate.sh
    ln -sf ~/Projects/myrepos/ai-playbook/agents/hooks/skill-gate/cursor.sh ~/.cursor/hooks/skill-gate.sh
    ln -sf ~/Projects/myrepos/ai-playbook/agents/hooks/skill-gate/agy.sh    ~/.gemini/antigravity-cli/hooks/skill-gate.sh
    ```
  - Doctor subsection: user-facing, what `skill_gate --doctor` verifies - the helper + 2 cores + 8
    adapter symlinks all resolve (11 paths; the 11 paths are the union of the Task 3 + Task 5 INSTALL
    `ln -sf` targets - helper + 2 cores + 8 adapters), the parent dirs exist (incl.
    `~/.ai-playbook/scripts/`), the PreToolUse array has the `Write|Edit|MultiEdit` matcher, adapters
    grep-clean for the literal helper invocation, the runtime dir is writable, AND the agy
    `PreToolUse` hook's `timeout` is `> RESOLVER_GIT_TIMEOUT_S` (r15-M4/r17-M4; must exceed the
    resolver's `RESOLVER_GIT_TIMEOUT_S` git timeout - see Terms step 3 / Task 4 doctor check (5)).
    Reference the Task 4 Doctor spec for the full algorithm (incl. the dangling-symlink predicate,
    the build-time Codex probe, and the agy-timeout check).
  - Block message + observability (r10-L6; r11-M2/M6; r12-M4/L4): (a) the block message EXACT text
    "Invoke the plans skill before authoring a plan file." (emitted as `deny_reason`; Claude surfaces
    on stderr + exit 2; agy as `{"allow_tool": false, "deny_reason": ...}` exit 0); (b) Observability
    (per Terms "LOUD keying mode"): `~/.ai-playbook/logs/hooks.log` records one JSON line per
    consultation. The CORE emits `keying=env-var` (Claude steady state) / `keying=project-only`
    (Codex/Cursor/agy steady state at v9; PURE LOG METADATA, drives NO core branch; the Claude
    adapter warns `CLAUDE_CODE_SESSION_ID absent; running in no-session mode` on empty SID - r12-M4
    relocated alarm); the RESOLVER emits `keying=no-anchor` to the SAME file on its git-failure branch
    (r15-M1 sink fix; the shared `_append_hooks_log_line` helper in Terms step 3 writes the line
    DIRECTLY to `hooks.log`, so it survives adapter stderr-discard; alarm, non-git dirs only per B1;
    r12-L4: in a non-git directory tree,
    `project` is cwd-derived and UNSTABLE across `cd` within the tree; if you edit plans across
    subdirs of a non-git scratch dir, expect blocks; treat any `keying=no-anchor` line as a real
    signal, not steady state). (r11-M6: `--budget` is a `lessons_recall.py` flag, NOT a
    `skill_gate.py` flag - it is documented ONLY in the Task 3 lessons-recall README, not here.) The
    three runtime paths (`~/.ai-playbook/runtime/skill-invoked/`, `~/.ai-playbook/runtime/lessons-recall/`,
    `~/.ai-playbook/logs/hooks.log`) are disposable; safe to delete.
  - Marker refresh policy: the plans skill writes/REFRESHES the marker on EVERY plan-file write it
    performs (not only create-only Phase 0 - M2) BEFORE the gated tool call; the marker write is
    FAIL-LOUD in the skill (abort with a clear error if unwritable - M2); an ABSENT marker ALWAYS
    blocks and the gate consults NO second signal (r4-M1: recovery via `skill_gate --doctor`).
  - Also: how to add a second gated class (promote the module-level dict to a registry IN THAT
    CHANGE), the agy absolute-path / always-exit-0 / jq-absent constraints, and a THREAT-MODEL note
    that the marker is a consent reminder, NOT a security boundary (forgeable by any process with
    write access to the runtime dir; accepted because the protected files are already fully writable
    by the same user - r6-L2).
- [x] Verify the agy file-tool path field name inside `.toolCall.args`/payload on the FIRST real agy session (see agy.sh bullet); record in README. Until then the assumption is documented and the adapter ships live; correction is fix-on-first-use
- [x] INSTALL step (r11-B2: pin the literal install commands; ALL FOUR adapters LIVE, r6). Run these
  literal commands:
  ```bash
  # r12-M2: create target parent dirs that do not always exist on a default install
  # (measured: ~/.codex/hooks/ and ~/.gemini/antigravity-cli/hooks/ MISSING; ~/.claude/hooks/ and
  # ~/.cursor/hooks/ exist; mkdir -p on the latter is harmless belt-and-suspenders). The Task 3
  # INSTALL already mkdir'd these once; re-running here is idempotent and pins the step per-Task.
  # r13-M3: ~/.ai-playbook/scripts/ is the symlink TARGET dir for the cores + helper.
  mkdir -p ~/.ai-playbook/scripts ~/.codex/hooks ~/.gemini/antigravity-cli/hooks ~/.claude/hooks ~/.cursor/hooks
  # Core symlinked to ~/.ai-playbook/scripts/
  ln -sf ~/Projects/myrepos/ai-playbook/scripts/skill_gate.py ~/.ai-playbook/scripts/skill_gate.py
  # Four skill-gate adapter symlinks (absolute targets)
  ln -sf ~/Projects/myrepos/ai-playbook/agents/hooks/skill-gate/claude.sh ~/.claude/hooks/skill-gate.sh
  ln -sf ~/Projects/myrepos/ai-playbook/agents/hooks/skill-gate/codex.sh  ~/.codex/hooks/skill-gate.sh
  ln -sf ~/Projects/myrepos/ai-playbook/agents/hooks/skill-gate/cursor.sh ~/.cursor/hooks/skill-gate.sh
  ln -sf ~/Projects/myrepos/ai-playbook/agents/hooks/skill-gate/agy.sh    ~/.gemini/antigravity-cli/hooks/skill-gate.sh
  ```
  (The Task 3 INSTALL step covers the helper + four lessons-recall adapter symlinks.)
- [x] Echo-pipe tests pass for all four adapters (block / allow / non-gated / fail-open); the agy block selftest asserts BOTH exit 0 AND `"allow_tool": false` in the body (Mon2). ADAPTER-GLUE SELFTEST (r10-M5; r11-L8 tightened): an adapter echo-pipe (e.g. codex.sh) that FORCES the helper to return empty (unset every known session env var) -> the adapter's built argv contains NO element whose prefix is `--session-id` (neither `--session-id` standalone NOR `--session-id=...` glued-empty, NOR the literals `""`/`no-session`); pins the adapter glue between "helper returns empty" and "core sees no `--session-id`"
- [x] Commit: `feat(skill-gate): per-agent adapters + wiring recipes`

### Task 6: plans-skill marker + AGENTS.md note

Files:
- `ai-playbook/agents/skills/plans/SKILL.md` *(modify)*
- `ai-playbook/docs/AGENTS.md` *(modify)*

- [x] plans SKILL.md: add a marker-refresh obligation that runs on EVERY plan-file write the skill performs (including updates/completion - NOT only create-only Phase 0, which `plans/SKILL.md:14-15` skips on updates; without this the gate blocks the most common plan-write path - in-flight revisions like this r1->...->r11 cycle - M2). PINNED INSERTION POINT (r4-M6): insert it as a numbered obligation in the **Writing:** paragraph at `plans/SKILL.md:16` - the only authoring-flow obligation that runs on EVERY plan-file write, create AND update (NOT Phase 0, which `:14-15` skips on updates; NOT a free-floating step, which would not reliably fire before each Write during conversational authoring). Phrase it as a REFERENCE to the single-source recipe, not a restatement: "Before each plan-file Write, refresh the skill-gate marker per `ai-playbook/agents/hooks/skill-gate/README.md` (the recipe derives `project` and `session` per Terms (Skill-gate marker; Session key), invokes the shared `session_channel.py` subprocess VERBATIM, ensures `~/.ai-playbook/runtime/skill-invoked/` exists, then ATOMICALLY writes the marker, and is FAIL-LOUD)." Do NOT inline the path/body/window constants here (M7 single source; r11-L3: the full `project`/`session` derivation lives ONLY in Terms). State that the plans skill and the gate adapter share the ONE helper subprocess (Family D)
- [x] AGENTS.md: add a ONE-LINE note (M7 - not the full convention). PINNED INSERTION POINT (r4-M7): add it as a new bullet immediately AFTER the existing "Cursor hooks (optional)" sentence (line 61), LABELED "ai-playbook-versioned hooks" to distinguish these cross-agent hooks (versioned under `agents/hooks/`, symlinked into each agent's `~/` config) from the project-scoped `cursor/hooks/` above. The note states the two hooks exist (lessons-recall = proactive recall via UserPromptSubmit/PreInvocation injection; skill-gate = PreToolUse block on gated artifacts) and that the marker WRITE RECIPE + wiring live in `ai-playbook/agents/hooks/skill-gate/README.md` (single source). Do NOT append to the `cursor/hooks/` sentence. Keep AGENTS.md canonical-rule-only per its own placement rule (line 57: LLM-workflow rules -> skills, not AGENTS.md)
- [x] Verify the plans skill still reads cleanly and the marker step does not break the existing Phase 0 flow
- [x] Commit: `feat(skills): plans-skill marker for skill-gate; AGENTS.md hooks pointer`

### Task 7: live smoke + regression + liveness

Files:
- *(no new files; verification only)*

- [x] Live (Claude): a REALISTIC family-matching prompt (e.g. "the report dropped a row", NO literal family phrase) injects a reminder; retyping it does not re-inject (de-dup); a non-matching prompt injects nothing
- [x] Live (Claude) REAL-CORPUS BUDGET SMOKE (r8-M7): run `lessons_recall` against the REAL user-level corpus (`docs/maintenance/development_lessons.md` + the user corpus) for a Family-G prompt and assert the emitted body is `<= --budget`, STARTS with the `Lesson #N (title):` format for the highest-ranked lesson, and at the default 1500-char budget with real G bodies (~1057-4694 chars) contains ONE full lesson (possibly plus a HEAD slice of the next) - NOT a tail slice and NOT empty. Pins HEAD-truncation + the `Lesson #N` render format + that the budget binds on real corpus sizes (a budget that never binds on real data is a dead threshold)
- [x] Live (Claude): a Write to a NEW `docs/plans/*.md` path without a fresh plans-marker is blocked; after invoking the plans skill it is allowed; a marker older than `SKILL_GATE_WINDOW` is treated as absent (block). Write the marker in one turn and check the gate in a DIFFERENT turn to confirm cross-turn file persistence (B2). ALSO: an Edit to an EXISTING `docs/plans/*.md` (the revision case, the most common plan-write path - M2) after the plans skill revised it is allowed (the marker is refreshed on every plan-file write, not only create-only Phase 0); confirm a revision WITHOUT a fresh marker is still blocked
- [x] **LIVE Claude write-then-read (r8-B1/r9/r10 - the SOLE divergent-pair discriminator - replaces
  the demoted `#same_session_pair`)**: per-session isolation is CLAUDE-ONLY at v9 (Claude is the one
  agent with a verified per-session channel). Re-framed (r10-M7) to the genuinely non-tautological
  claims: (a) the marker is written from a DIFFERENT cwd than the gate fires from (skill invoked at
  repo root, gate after `cd` into a subdir - pins `project` walk-up agreement across two real
  processes, the r9-M2/r10-B2 risk); (b) the resolved marker FILENAME the gate looks up
  (`plans.<project>.<session>.marker`) is BYTE-IDENTICAL to the filename `--write-marker` wrote
  (transitively covers `project` + session sanitization). DROP the "both sides called the shared
  helper" framing (unfalsifiable now that one `scripts/session_channel.py` subprocess is used by both
  sides). This MUST pass before the Claude symlink is trusted. A divergent pair here is a loud fail,
  not a silent degrade. ALSO assert `~/.ai-playbook/logs/hooks.log` shows `keying=env-var` for Claude,
  NOT `keying=project-only` (r11-M2: this is a DETECTION, not a core alarm - the core is agent-agnostic
  and cannot know Claude is calling it; a `keying=project-only` line observed during a Claude LIVE run
  indicates the Claude env var was missing, which the Claude adapter MAY log separately if it detects
  its own env var missing). r16-L10: ALSO assert `hooks.log` shows NO `keying=no-anchor` line for a
  Claude LIVE run whose cwd is inside a git repo (`git rev-parse` succeeds, so the resolver's
  git-failure branch must not fire); a `no-anchor` line indicates the cwd was a non-git dir (Terms
  NON-GIT INSTABILITY) and is a real alarm, not steady state. Codex/Cursor/agy run project-only (full window - r10-M10) as their STEADY
  STATE and are validated LIVE only for "does not crash + classifies a gated path + blocks an absent
  marker" (NO per-session divergent-pair claim for these agents at v9 - they have no per-session
  isolation to diverge on).
- [x] **LIVE Claude resume write-then-read (r10 Monitor 1)**: `CLAUDE_CODE_SESSION_ID` does not
  recycle within a live session; resume/compact behavior UNVERIFIED. In a REAL Claude session: write
  the marker, RESUME the session (or simulate compact), re-read the session id, then Edit a plan file
  -> ALLOW. If the id ROTATES on resume, the plans skill re-writes the marker on its FIRST invocation
  in the resumed session so the post-resume Edit finds a fresh marker. Pins that a resume does not
  silently brick every plan Edit after resume (the env var stays present, so `keying=env-var` logs;
  r11 Monitor: mitigation is deferred - if the id rotates, the user re-invokes the plans skill once,
  and the block message names the skill so recovery is one step. Do not leave a SessionStart hook or
  skill-side check implied when no Task delivers it).
- [x] Liveness (Mon1; r11-B2/L5 install is SYMLINKED, not copy-synced): a broken install (break a
  symlink TARGET - a `mv` of the helper/adapter source so the symlink DANGLES) makes the hook fail
  loudly (non-zero / clear stderr), NOT silently no-op; append one line per gate consultation to
  `~/.ai-playbook/logs/hooks.log`; `python3 ~/.ai-playbook/scripts/skill_gate.py --doctor` (per the
  Task 4 Doctor spec: `test -e` + `readlink -f` every abspath AND grep each adapter for the literal
  helper invocation AND the PreToolUse-array check AND the core-symbol/import check) catches a
  missing/dangling helper or adapter symlink before the user trusts the gate. CREATES
  `~/.ai-playbook/runtime/skill-invoked/` if absent (r7-M6/r8-M4: so recovery actually fixes a
  first-run brick, not just reports it), confirms that dir is WRITABLE BY THE SKILL's uid.
- [x] `skill_gate --selftest#derive_session_channel_env_var` (r10-L2 rename; was `#derive_session_env_var`): the helper subprocess prints `os.environ.get("CLAUDE_CODE_SESSION_ID") or ""` - monkeypatch `CLAUDE_CODE_SESSION_ID` set -> stdout is that value; unset -> stdout is empty (pins the `scripts/session_channel.py` leaf, NOT a core function). The name MUST NOT reuse the dead core symbol `derive_session`
- [x] `skill_gate --selftest#session_value_path_safe` (M6/r9; r10-M3 hex format assertion): `--session-id "../evil"` -> the sanitized filename stays inside the runtime dir (the core passes the value through `sha1(...).hexdigest()[:16]` -> hex, no traversal, no aliasing of another session's marker); assert the produced value matches `^[0-9a-f]{16}$`
- [x] `skill_gate --selftest#project_stable_across_sibling_cwd` (M2/r9; r10-M3 hexdigest; r12-M1 collapsed): skill invoked from the REPO ROOT, gated Write fired from a SUBDIR of the SAME repo -> SAME `project` (both sides call `resolve_project_key`; the derived `project` hashes for the root and the subdir are EQUAL per Terms (Skill-gate marker; r12-M1))) -> ALLOW. Discriminates the shared resolver from a `sha1(realpath(cwd)).hexdigest()[:16]` stub, which would derive DIFFERENT project hashes and false-block
- [x] `skill_gate --selftest#plans_dir_resolved_from_subdir` (M3/r9; r10-M6 EQUALS, not "not None"): gate cwd is a SUBDIR of the repo; `facts_paths.resolve_plans_dir(cwd)` walks UP to the repo `.ai-playbook/facts.md` and the resolved value EQUALS the byte-for-byte `plans_dir` from the repo facts TOML fence. PLUS an arm where the repo facts declares a NON-default `plans_dir` (e.g. `plans_dir = "docs/my-plans/"`) invoked from a subdir - only a real walk-up returns it; a default-returning stub fails
- [x] Regression: `pr-skill-reminder.sh`, `learn-counter`, `check-plan-review-gate.sh`, `execute-plan-manifest-gate.sh` still fire independently; confirm `pr-skill-reminder.sh` and lessons-recall are disjoint (pr-skill-reminder injects the PR-skill reminder; lessons-recall injects family-tagged lessons - state the boundary in README)
- [x] `check-no-em-dash.sh` clean across all new files
- [x] Commit: `test(hooks): live smoke + regression + liveness confirm no breakage`

## Design Invariants (CR Guard)

- **The corpus reader and facts resolvers are reused; the PROMPT classifier is new.** lessons-recall
  MUST call `lessons_classify.classify_prompt` (NOT the lesson-shape `_matches_family_vocab`) for
  prompts, because the lesson-shape classifier's `FAMILY_KEYWORDS` are lesson-descriptive and no-op on
  real prompts (B1, verified empirically). It MUST reuse `lessons_corpus.iter_lessons` and
  `facts_paths.user_corpus_path`. Rationale: Family H (verify the real thing) and Family D (single
  source of truth - the corpus reader is the one reader; a second would drift). The lesson-shape
  classifier remains in use by the migrator for lesson routing - it is NOT wrong, just not a prompt
  classifier.
- **Classifiers and facts resolvers live in leaves/mid-tier; cores depend only downward.** The
  dependency graph is (r11-L7 leaf row split into two tiers; r12-M1: BOTH cores depend on
  `facts_paths.resolve_project_key` in addition to the existing `facts_paths`/`lessons_corpus`
  dependencies):
  (a) agent-agnostic primitives: `facts_paths.py` (stdlib-only leaf; exports
  `resolve_project_key` consumed by BOTH cores - r12-M1 collapse), `lessons_corpus.py` (stdlib-only
  leaf);
  (b) `session_channel.py` (stdlib-only `scripts/` leaf, r10-B1) - a `scripts/`-resident ADAPTER-LAYER
  leaf that carries agent-knowledge (`CLAUDE_CODE_SESSION_ID`); consumed ONLY by adapters AND the
  plans-skill marker recipe (subprocess invocation
  `SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"`), NEVER imported by cores.
  Above them: `lessons_classify.py` (MID-TIER node: imports `lessons_corpus` for
  `VALID_FAMILIES`/`Lesson`, so it is NOT stdlib-only - L4) <- `lessons_migrate.py`,
  `lessons_recall.py`, `skill_gate.py` (cores; BOTH cores IMPORT and CALL
  `facts_paths.resolve_project_key` for the `project` filename component - r12-M1: the duplicated-
  VERBATIM-Family-D obligation collapses to one shared function object, asserted by
  `#project_single_source` in EACH CORE's own `--selftest` (downward import only - r13-M2: the
  selftest lives in each core, NOT in the leaf; a leaf asserting a core's identity would reverse the
  dependency direction). The cores accept `--session-id` as OPAQUE data with
  ZERO agent-channel knowledge, so the "cores depend only downward" claim stays true (Family F
  avoided, Family D single source enforced by a real shared artifact). The graph is acyclic; no core
  reaches up into the migrator's private API (Family F).
- **`facts_paths.py` has TWO parsers, not one generic resolver.** `plans_dir`/`tmp_dir` live in the
  repo `.ai-playbook/facts.md` as TOML-fence `key = "value"` lines; `shared_docs_dir` lives in the
  home `~/.ai-playbook/facts.md` as a markdown table row `| \`key\` | \`value\` |` (r2 Blocker,
  verified empirically). The leaf exports `resolve_toml_key` (NEW, backs `resolve_plans_dir`/
  `resolve_tmp_dir`) and `resolve_table_key` (MOVED byte-identical, backs `resolve_shared_docs_dir`/
  `user_corpus_path`, preserving the repo-first two-candidate search order byte-identical - r7-M2).
  There is NO generic `resolve_facts_key(start_dir, key)`. Rationale: Family H
  (the format split is real; one parser silently returns None for the other format -> skill-gate
  fail-opens on every consult) and Family D.
- **Cores are agent-agnostic (text in, text out) - now TRULY so under r10.** No agent protocol in
  `lessons_recall.py` or `skill_gate.py`: the cores contain ZERO agent knowledge - they accept the
  session string as `--session-id <value>` and treat it as OPAQUE data (r10-B1 Decision 1). All
  session-channel knowledge lives in the `session_channel.py` `scripts/` leaf (subprocess-invoked by
  adapters AND the plans-skill marker recipe via
  `SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"`; NEVER imported by the cores - Family D
  single source enforced by a real shared artifact, Family F avoided). Rationale: the
  recreate-in-any-agent requirement; a new agent is ONE adapter + ONE config entry + (if it has a
  verified per-session env var) a branch in `session_channel`, NOT a core change.
- **Each agent's decision/injection envelope is distinct; adapters build envelopes via `json.dumps`
  dict construction, never f-string/concatenation.** Claude wraps context as
  `{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":...}}`; Codex emits
  flat `{"additionalContext":...}`; agy emits TOP-LEVEL `{"allow_tool":...,"deny_reason":...}` for
  decisions and exits 0 even when blocking (a non-zero exit is a hook FAILURE on agy, not a block).
  Wrapping agy output in `hookSpecificOutput` FAILS its schema validation. json.dumps prevents
  corpus text containing `"`, `}`, or newlines from breaking the envelope or injecting sibling keys
  (M3). This applies to the `deny_reason` string too (it is data-influenced - the agy path field is
  tolerant-scanned from `.toolCall.args`): control chars (newline, CR, U+2028/U+2029) in ANY adapter
  diagnostic pass through `json.dumps` and are never written raw to stderr; the fail-open warning
  hardcodes the path label, no untrusted interpolation (L9). Rationale: Family H, Family C, Family G.
- **Adapters parse stdin/payload with python3, not jq.** All FOUR adapters that parse a payload
  (claude/codex/cursor/agy, BOTH hooks) extract with python3. Rationale: agy hosts may not have jq
  (the article requires a grep/cut fallback); python3 is already required by the core, so it is the
  single robust extraction path across all four agents.
- **The skill-gate path-classifier is a `realpath` subtree check, never a string prefix.** Rationale:
  `..`/symlink/absolute-path evasion bypasses a naive `startswith` (M4). Resolve both the target and
  `{plans_dir}` through `os.path.realpath` and use `Path.relative_to`/`os.path.commonpath`.
- **The skill-gate marker is a per-(PROJECT, SESSION), timestamp-window existence check, stored at a
  HOME-ANCHORED path (r6; supersedes the r5 cwd-relative design, which was silently OFF in git
  worktrees - r5-B1; r10 bounded repo-anchor `project` + adapter-derived `session` amendments).** The
  marker lives at `~/.ai-playbook/runtime/skill-invoked/plans.<project>.<session>.marker`, where
  `project` is derived per Terms (Skill-gate marker; r12-M1 collapse: via the SHARED
  `facts_paths.resolve_project_key(start_dir)` consumed by BOTH cores; r11-B1: the worktree-no-facts
  fallback is `sha1(realpath(toplevel))`, NOT `sha1(realpath(cwd))`; `realpath(cwd)` +
  `keying=no-anchor` fire ONLY in a non-git dir) and `session` is derived per Terms (Session key;
  r11-M3: emptiness check is the FIRST operation, both layers normalize). PER-PROJECT isolation holds
  ONLY when the anchor resolves WITHIN the worktree. This path is ALWAYS PRESENT regardless of cwd or worktree (home is not worktree-dependent;
  `.ai-playbook/` is gitignored so a worktree has no repo facts file and a cwd-relative tmp_dir is
  unresolvable there). PER-PROJECT isolation comes from the `project` filename component; PER-SESSION
  isolation comes from the `session` component AND IS CLAUDE-ONLY AT v9 (a fresh Claude marker from
  session A does NOT admit session B's writes in the same repo - r6/r9/r10; Codex/Cursor/agy run
  project-only with the FULL `SKILL_GATE_WINDOW` as the DOCUMENTED STEADY STATE, stated as an
  INVARIANT not a fallback - per-session isolation is Claude-only at v9; r10-M10: the halved-window
  steady state is COLLAPSED, all agents use the FULL window unconditionally). The marker BODY stores
  the writer's `os.path.realpath(cwd)` AND the resolved repo-anchor path as FORENSIC/debug metadata
  ONLY - it is NOT a checked guard (r7-M4: a body-equality check is structurally UNREACHABLE, because
  `project = sha1(realpath(git_toplevel or cwd)).hexdigest()[:16]` per Terms (Skill-gate marker;
  r12-M1 collapsed resolver) already encodes the repo, so a re-root to a DIFFERENT
  repo changes the FILENAME and the gate blocks via the absent-marker path before any body comparison;
  the body is retained only for diagnosis). The gate accepts iff the file EXISTS AND
  `0 <= (now - mtime) <= SKILL_GATE_WINDOW` (default 4h, FLAGGED). The runtime dir is created on first
  write (`os.makedirs(..., exist_ok=True, mode=0o700)`, r7-M6) and the marker is written ATOMICALLY at
  `0o600` via `lessons_corpus.atomic_write_text` (`O_EXCL|O_NOFOLLOW` + `os.replace`, r8-L3/r6-L1/
  r7-L4, torn-read-safe under concurrent skill-refresh; r10-L1: `--write-marker` CATCHES
  `FileExistsError` from `atomic_write_text` and treats it as BENIGN - a concurrent skill-refresh
  racing on the same marker aborts the loser harmlessly, surfaced as a skill-side warning). The GATE
  does a benign `os.makedirs(dir, exist_ok=True, mode=0o700)` BEFORE its `os.stat` (r8-M4), so a
  missing dir on a fresh install cannot fail-OPEN the gate via `FileNotFoundError` - the
  absent-marker branch is always reachable (the FIRST plan write on a fresh machine is gated, not
  silently allowed). A future-dated/negative delta or `mtime == 0` is STALE -> block (M4). `plans_dir`
  CLASSIFICATION is a path-suffix test with a `docs/plans/` default (FLAGGED), so it works in worktrees
  (which contain `docs/plans/`) without resolving a worktree-absent facts file; r10-L5: when the gate
  cwd is a worktree, an absolute Write target into the MAIN repo is ALSO checked against the default
  `docs/plans/` suffix on the target's OWN realpath, so a cross-tree plan write is still gated.
  Rationale: Family H (the r5 design's rationale did not hold against the real `.gitignore` - measure
  the artifact, not the assertion; the r9 unbounded walk-up repeated the same Family-H failure - r10
  bounds it), Family D (one marker location, keyed two ways; one `session_channel.py` `scripts/` leaf
  for write and read, subprocess-invoked), Family E (the writer's session/project must hold for the
  reader's decision).
- **The marker is written/refreshed on EVERY plan-file write the skill performs (including updates),
  the write is FAIL-LOUD, and an ABSENT marker ALWAYS blocks (no second signal).** The plans skill
  refreshes the marker before each gated Write, not only in create-only Phase 0 (which
  `plans/SKILL.md:14-15` skips on updates - M2). If the marker cannot be written, the skill aborts
  with a clear error; because the skill never reaches a gated tool call with the marker unwritten,
  the "skill ran but marker absent due to write failure" state CANNOT OCCUR, so the gate needs NO
  second-signal fallback (r4-M1). An absent marker therefore always blocks; recovery from a
  transient/unwritable/divergently-resolved store is via `skill_gate --doctor` (Mon1), NOT a
  gate-side bypass. Rationale: Family E (the writer's
  precondition must hold for the reader's decision) and Family C (absent marker = "skill not invoked"
  must not conflate with "skill invoked but failed to write" - but the fail-loud write means the
  latter is unreachable, so no second representation is needed).
- **lessons-recall de-dup is genuinely append-only (`O_APPEND`), time-windowed, per-(project, session),
  home-anchored, and never uses raw cwd as a filename.** The state file lives under `--state-dir`
  (default HOME-ANCHORED `~/.ai-playbook/runtime/lessons-recall/`, r6 - present in worktrees/subdirs,
  never depends on resolving a cwd-relative tmp_dir; created `0o700`), opened with
  `os.open(path, O_WRONLY|O_CREAT|O_APPEND, 0o600)` (NOT `atomic_write_text`, which is a full-file
  `os.replace` read-modify-write and is NOT concurrency-atomic - M1). The DE-DUP MEMBERSHIP KEY is
  `N` (the lesson number) WITHIN the per-(project,session) file - project and session are encoded in
  the PATH, no longer needed in the key body (r7-M5; r10/r9: `session` is reliable on both sides
  because the SAME `scripts/session_channel.py` leaf (subprocess-invoked) keys both the dedup state
  and the marker - `CLAUDE_CODE_SESSION_ID` -> `--session-id` for Claude, helper prints empty ->
  omitted -> `no-session` for the others; no payload-field asymmetry; r10-M10: ALL agents use the
  FULL `RECALL_DEDUP_WINDOW`, the halved window is COLLAPSED); each stored
  line `f"{N}\t{ts}\n"` carries `ts` as PRUNING METADATA, not as part of the key (r4-M2: keying on
  `ts` would make every write distinct and dedup would never suppress). The SUPPRESSION PREDICATE is
  PER-LESSON (P1): drop each lesson whose `N` is in `seen`, rank+concat+truncate the remainder; emit
  nothing iff the remainder is empty (r6-M3). The file is APPEND-ONLY for its entire lifetime and is
  NEVER rewritten; the reader computes the seen-set IN MEMORY from lines whose
  `ts >= now - RECALL_DEDUP_WINDOW` (default 24h, FLAGGED - M7: without a window, recall silently
  decays to zero for long-used cwds), so stale lines are ignored on read, never truncated out - there
  is no rewrite race with concurrent appenders. The READ PATH opens the state file `O_RDONLY`
  inside `try/except FileNotFoundError` (and the `OSError` family); a missing/unreadable file yields
  `seen = set()` (r8-M3: the FIRST matching call in a session always takes this cold-start branch -
  the runtime dir is absent on a fresh machine - so it is exercised by every cold start, never a
  crash). The state file is PATH-ISOLATED per (project,
  session) at `<--state-dir>/<project>.<session>.state` where `project` is derived per Terms
  (Skill-gate marker) VERBATIM-identical to the skill-gate marker's `project` (r12-M1:
  VERBATIM now means BOTH cores CALL the SAME `facts_paths.resolve_project_key` function object - asserted by
  `#project_single_source` in EACH CORE's own `--selftest`, downward import only - r13-M2; the
  selftest lives in each core, NOT in the leaf; r11-B1/r10/r9/r8-M5 historical: the prior SAME-ordered-rule obligation
  is superseded by the single shared resolver - a divergent local copy would split dedup and marker
  across different files on mid-session cwd navigation within the same repo); deletion/prune is per-session, read cost
  scales with the current session's activity not global host usage - the prior r6 global flat file is
  superseded). `O_APPEND` guarantees STATE-FILE INTEGRITY under
  concurrency (no lost/corrupted lines); injection de-duplication itself is BEST-EFFORT (a same-lesson
  concurrent pair may inject twice before either append is visible to the other's read; bounded by the
  budget cap) - the design does NOT claim concurrency-atomic injection (r4-M2/L4).
- **lessons-recall never blocks (exit 0, silent or inject).** skill-gate MAY block. The two contracts
  must not be conflated in one adapter.
- **skill-gate fails open ONLY on `PermissionError` (a truly broken/unwritable store).** The marker
  is HOME-ANCHORED (`~/.ai-playbook/runtime/skill-invoked/`, r6); path resolution cannot return None.
  An unwritable home runtime dir (`PermissionError`) MUST allow the write and warn on stderr + append
  a `hooks.log` line (path label HARDCODED, exception fields passed as a json.dumps field - r8-L6
  extends L9 to the log sink), never block. `FileNotFoundError` is NOT fail-open: the gate's
  makedirs-before-stat plus the absent-marker branch handle it (r8-M4). `plans_dir` classification
  falls back to the `docs/plans/` default when repo facts is absent (e.g. a worktree), so
  classification does not fail-open either. A present but future-dated/zero mtime marker is NOT
  fail-open - it is stale -> block (M4). Rationale: a gate that blocks on its own I/O bug is worse
  than no gate, but a gate that perpetual-allows on a hostile mtime is no gate at all.
- **No em dashes (U+2014)** in any core output or doc; `~/` home-relative paths in all docs.
- **Corpus is read-only.** lessons-recall writes only a best-effort tmp state file, never a corpus.

## Monitor

- **Prompt-classifier vocabulary is a v1 best-effort and needs real-world tuning** (owner: this plan's
  follow-up). `PROMPT_INTENT_VOCAB` is seeded with lemmas + common inflections (drop/drops/dropped/
  dropping, disagree/disagrees/disagreed) and bare "missing" is reserved for G (data-loss), NOT C.
  Resolution (r5-L1): `classify_prompt` iterates an EXPLICIT `PROMPT_FAMILY_ORDER = ("G","H","A","B",
  "D","E","F","C")` tuple (first-match-wins), so the two flagship families G (data-loss) and H
  (verify-the-real-thing) win over C (representation) on overlap; C is the catch-all and goes last.
  Other C/X boundaries may still misroute. Real prompts will still miss or mis-route. The
  `#prompt_realistic`, `#prompt_realistic_inflected`, `#overlap_missing`, and
  `#overlap_verify_vs_representation` selftests pin the known directions; expand them as misses are
  observed in `hooks.log`. This is the direct consequence of the B1 fix (the deterministic-reuse
  premise could not classify prompts; a hand-authored vocabulary can, at the cost of needing tuning).
- **`RECALL_DEDUP_WINDOW` (default 24h) and `SKILL_GATE_WINDOW` (default 4h) are flagged thresholds.**
  Confirm both at implementation. The de-dup window guards recall-value decay (too long and a lesson
  stays suppressed across fresh tasks; too short and the same lesson re-injects every session). The gate
  window guards stale-marker admission (too short and a long planning session re-trips the gate, too
  long and the marker admits writes well after the skill context is gone). Record both in the READMEs.
  Observability for the de-dup window: log recall suppress-vs-fire counts per session in hooks.log; if
  the suppress ratio trends to 1.0 over time, the window is too long (M7). The append-only state file
  is PATH-ISOLATED per (project, session) (`<project>.<session>.state`, r7-M5); each grows unbounded
  within its session (one line per injection, never rewritten or truncated) and is SAFE TO DELETE
  per-session (recreated on the next injection). Read cost is a single pass over ONE session's file
  filtered by `ts >= now - window`, so it scales with current-session activity, not global host usage.
  `lessons_recall --doctor` (Mon1 liveness self-check) reports total state-dir size; if stale
  per-session files accumulate across a long-lived host, prune the directory (every file is
  disposable).
- **Skill-gate self-lockout residual blast radius** (owner: skill-gate maintainer). With the
  fail-loud marker write and the absent-marker-always-blocks rule (r4-M1, no second signal), the
  residual brick surfaces are: (a) a home-runtime dir the skill's uid cannot write; (b) the repo
  re-rooted to a DIFFERENT REPO between skill turn and gate turn - because
  `project = sha1(realpath(git_toplevel or cwd)).hexdigest()[:16]` per Terms (Skill-gate marker;
  r12-M1 collapsed resolver), a re-root to a different repo changes the FILENAME,
  so the gate derives a DIFFERENT `project`, looks up a marker that was never written, and blocks via
  the absent-marker path (r7-M4; the body is forensic-only, so there is no body-snapshot comparison to
  false-block on); recoverable by re-invoking the skill in the new repo so the marker is written under
  the new `project`. NOTE (r9-M2/r10-B2): re-rooting WITHIN THE SAME REPO (e.g. `cd` into a subdir
  after invoking the skill) does NOT brick - the repo anchor is STABLE across in-repo navigation, so
  `project` is byte-identical on both sides (this closed the r8 false-block; pinned by
  `#project_stable_across_sibling_cwd`); (c) r10/r9/r8 CLOSED the divergent-pair brick by construction
  for Claude: BOTH `--write-marker` (plans skill) and the gate adapter invoke the SAME
  `scripts/session_channel.py` subprocess (`SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"`),
  so write and read agree by construction (Family D single source - the payload-field asymmetry that
  could permanently brick an agent is gone). For Codex/Cursor/agy the divergent-pair risk is HONESTLY
  OUT OF SCOPE at v9: those agents run project-only (helper prints empty -> `--session-id` omitted ->
  `no-session`; FULL `SKILL_GATE_WINDOW` - r10-M10) as their DOCUMENTED STEADY STATE, and project-only
  has NO per-session isolation to diverge on. Observability: `skill_gate --doctor` must verify the
  home marker store `~/.ai-playbook/runtime/skill-invoked/` is WRITABLE BY THE SKILL's uid (not just
  readable by the hook's uid) and CREATE it if absent (r7-M6, so recovery fixes a first-run brick). Run
  from the README and a weekly cron.
- **Codex prompt-event and Codex blocking-event availability.** If Codex lacks `user_prompt_submit`,
  the Codex lessons-recall adapter falls back to `session_start` (degraded, one-shot). The Codex
  `pre_tool_use` BLOCKING event is NOT evidenced in the installed config (`post_tool_use` only); if
  absent, Codex skill-gate degrades to no-op. Resolved at Task 3/Task 5 build time; recorded in README.
- **Cursor lessons-recall is degraded by design** (no silent per-prompt injection; sessionStart
  one-shot only). skill-gate on Cursor IS full-fidelity (Cursor can block).
- **agy field names are ASSUMED and validated fix-on-first-use (r6; ships LIVE, not held back).**
  The cited article shows the block mechanism and the `.toolCall.args` nesting concretely, but not:
  (a) the context-injection field name for `PreInvocation` (lessons-recall; assumed `additionalContext`);
  (b) the path field name inside `.toolCall.args` for `write_to_file`/`replace_file_content`
  (skill-gate; assumed `path`); (c) the `timeout` field path inside
  `~/.gemini/antigravity-cli/hooks.json` carrying the `PreToolUse` skill-gate matcher's timeout
  (build-time-verified alongside (a)/(b); asserted by doctor check (5) - the resolver runs with an
  internal `RESOLVER_GIT_TIMEOUT_S` git timeout, so the agy wrapper `timeout` MUST be `>= 2 *
  RESOLVER_GIT_TIMEOUT_S` else agy kills the hook before the resolver's `TimeoutExpired` catch fires
  and the gate silently goes off). (r10/r9: the session channel is NOT an agy-payload assumption - the
  agy adapter calls the shared `scripts/session_channel.py` subprocess, which prints empty for agy at
  v9 -> `no-session` key, FULL window - r10-M10.) All four agy adapters ship LIVE and
  symlinked; the assumptions are DOCUMENTED in the README and validated on the FIRST real agy session
  (confirm an injected reminder surfaces; confirm a `write_to_file` of a plan file is gated). If an
  assumption is wrong, the hook may silently fail to fire until corrected (Family G) - accepted
  because the user will catch it on first use and the fix is a one-line field rename + re-test. Same
  fix-on-first-use discipline applies to Codex/Cursor event availability. agy `command` MUST be an
  absolute path and the hook MUST exit 0 even when blocking (captured in the README recipe and the agy
  adapter bullets).
- **Session-channel availability is per-agent and resolved by a SHARED `scripts/session_channel.py`
  leaf (r10; supersedes the r9 helper-home design and the r7/r8 core `derive_session()` / PID-walk
  design, which were unimportable/uncomputable as specified - see Session key term).** The helper
  prints `os.environ.get("CLAUDE_CODE_SESSION_ID") or ""` (Claude at v9 - the ONLY genuinely
  per-session channel; a UUID that does NOT recycle within a live session; resume/compact behavior
  UNVERIFIED - see the resume Monitor below); empty for Codex/Cursor/agy -> `no-session` key, FULL
  `SKILL_GATE_WINDOW` (r10-M10: the halved-window steady state is COLLAPSED - NOT a degraded fallback;
  per-session isolation is Claude-only at v9). Monitor for a future VERIFIED per-agent env var to add
  to the helper (a branch in `session_channel.py` + a new selftest arm, NOT a core change - r10-B1b;
  stated as a known extension point, NOT as zero-cost). The headless `#same_session_pair` selftest is
  DEMOTED to a sanity check (it feeds the SAME id to both sides and cannot detect live divergence);
  the SOLE B1 discriminator is the Task 7 LIVE CLAUDE write-then-read (the one agent with a verified
  per-session channel): the model emits its channel value AND the hook fires on a real Write; assert
  byte-identical marker filenames. This MUST pass before the Claude symlink is trusted. Codex/Cursor/
  agy are validated LIVE only for "does not crash + classifies a gated path + blocks an absent marker"
  (no per-session divergent-pair claim for these agents at v9). The core logs
  `keying=env-var|project-only` to `~/.ai-playbook/logs/hooks.log` on every consultation
  (r11-M2: PURE LOG METADATA, drives NO core branch - the core is agent-agnostic and cannot know
  which agent is calling it; "Claude with missing env var" and "Codex steady state" both arrive as
  `--session-id` absent/empty). `keying=env-var` is the Claude steady state; `keying=project-only`
  for Codex/Cursor/agy is the documented steady state; the resume Monitor + the Task 7 LIVE resume
  assertion handle the missing-env-var case (if a Claude-missing-env-var alarm is wanted, it lives in
  the CLAUDE ADAPTER, which knows its own identity and may log if it detects its own env var
  missing). `keying=no-anchor` (a non-git dir, per B1 step 3) is ALWAYS an alarm, is orthogonal
  to the env-var/project-only axis, AND is written by the RESOLVER `facts_paths.resolve_project_key`
  to the SAME `hooks.log` via the shared `_append_hooks_log_line` helper (NOT the core; r15-M1 sink
  fix - rationale in Terms step 3, stated once).
- **`CLAUDE_CODE_SESSION_ID` rotation on resume/compact (r10 Monitor 1; r11-M2 reframed; r12-L6
  clarified).** The session id does NOT recycle within a live session; resume/compact behavior is
  UNVERIFIED. If Claude rotates it on `--resume`/compact, a planning session paused across a resume
  writes the marker under session A and the post-resume Edit derives session B -> ABSENT marker ->
  blocks every plan Edit after resume, SILENTLY. `hooks.log` detects a MISSING env var
  (`keying=project-only` during a Claude run) but NOT a ROTATED id (the env var stays present, so
  `keying=env-var` still logs and cannot distinguish rotated from steady state). The SOLE rotation
  signal is the user observing post-resume blocks; recovery is ONE re-invocation of the plans skill
  (the block message names the skill). (Do not leave a "SessionStart hook or skill-side check"
  mitigation implied when no Task delivers it - optional future Task.) The Task 7 LIVE resume
  write-then-read (write marker, resume, re-read id, Edit -> ALLOW) is the detection.
- **No hook-liveness observability is a silent-disable risk** (Mon1). A broken/migrated symlink, an
  agent refusing a symlinked command, or an adapter bug caught by a broad `except` makes the hook
  silently never fire (Family G), and because agy/Claude contracts REQUIRE exit 0 even when denying,
  an internal exception becomes exit-0-allow = gate off. Mitigation: append one line per gate
  consultation to `~/.ai-playbook/logs/hooks.log`; `skill_gate --doctor` (per the Task 4 Doctor
  spec: `test -e` + `readlink -f` every abspath AND grep each adapter for the literal helper
  invocation AND the PreToolUse-array check AND the core-symbol/import check + marker store writable)
  is runnable from the README and a weekly cron; the cores fail loudly at top-level import (not
  swallowed by a permissive `except`). Task 7 pins the loud-failure claim.
- **Precision of lessons-recall** (owner: this plan's follow-up). An intent phrase used incidentally
  triggers a false-positive injection. Accepted for v1 (cap + de-dup bound the cost). v2 should require
  the phrase AND a task verb in proximity.
- **Core install model decided (r6; r11-B2 pins the literal install + doctor verification): the new
  cores are SYMLINKED, not copy-synced.** `~/.ai-playbook/scripts/lessons_recall.py`,
  `skill_gate.py`, and `session_channel.py` symlink to the repo copies. A hook MUST run the latest
  core (a stale copy would silently re-bite), so symlink is the correct model for hooks specifically.
  RECONCILED (r11-B2): the EXISTING four lessons scripts (`lessons_index.py`, `lessons_adopt.py`,
  `lessons_migrate.py`, `lessons_corpus.py`) are COPY-SYNCED file copies (the documented convention
  in `agents/skills/lessons-migrate/SKILL.md:46`); the NEW cores + helper are SYMLINKED; cleanup of
  the existing copy-synced scripts is OUT OF SCOPE (do NOT retrofit them in this plan). The literal
  `ln -sf` install commands are pinned in the Task 3 and Task 5 INSTALL steps (helper + 4
  lessons-recall adapters; core + 4 skill-gate adapters). r8-L3 novelty statement: unlike the skills
  dirs (ONE shared symlink target per agent), NO hook is currently versioned or symlinked - the cited
  precedents (`pr-skill-reminder.sh`, `learn-counter-codex.sh`, `check-plan-review-gate.sh`) are
  installed-only FILE COPIES. This plan introduces the versioned-and-symlinked hook model as a NEW
  convention; the per-agent hook target dirs (`~/.codex/hooks/`, `~/.cursor/hooks/`,
  `~/.gemini/antigravity-cli/hooks/`) must be CREATED at install, and the Task 7 live-smoke MUST
  verify each agent actually executes a symlinked command (an agent that refuses a symlinked command
  and silently no-ops is the Family-G failure this gate exists to surface). The doctor (Task 4) now
  `test -e` + `readlink -f` every abspath (helper + 2 cores + 8 adapters = 11 paths; r12-M3: the 2
  cores are `lessons_recall.py` and `skill_gate.py`) and FAILs loud on a missing/dangling
  symlink (r11-B2), so a broken install is caught before the user trusts the gate.

## r15 Amendments

| # | Finding | Affects | Action |
|---|---------|---------|--------|
| 1 | M1 no-anchor routed to stderr not `hooks.log` (convergent) | Terms step 3 + LOUD keying, Task 1, Task 4 ~911, Task 5 README ~1124, Monitor ~1485, selftests | Resolver writes `no-anchor` DIRECTLY to `hooks.log` (`os.open`+`json.dumps`, best-effort); core vocabulary narrows to `env-var\|project-only`; LOUD keying splits ownership; selftests assert the FILE |
| 2 | M2 selftest fixture non-discriminating | Task 2 `#project_filename_uses_resolver` | Pin git-subdir fixture + assert divergence from local computation |
| 3 | M3 Codex verified-file recording | Task 5 README | Add recording-obligation sentence to Codex wiring recipe |
| 4 | M4 agy timeout unpinned | Task 5 agy recipe, doctor | Pin `timeout=10` literal + doctor check `>= 6` |

## r16 Amendments

| # | Finding | Affects | Action |
|---|---------|---------|--------|
| 1 | M1 cold-start `FileNotFoundError` (convergent, 4 agents) | Terms step 3, Task 1 impl, Task 4 Log discipline, selftests | `os.makedirs(parent, exist_ok=True, 0o700)` in `try/except OSError` before `os.open` at BOTH write sites; absent-parent resolver selftest arm |
| 2 | M2 r15 header bullet 109w | Header | Trim to ~60w |
| 3 | M3 doctor count FOUR not bumped | Task 4 doctor, Task 5 README, selftest | Bump count to FIVE; README names check (5); add `#doctor_agy_timeout` |
| 4 | L1 `O_NOFOLLOW` | Terms step 3, Task 1, Task 4 Log discipline | Add `O_NOFOLLOW` to open flags at both sites |
| 5 | L2 threat-model write side effect | Threat model, LOUD keying, Task 1 docstring | One-sentence reaffirmation |
| 6 | L3 `--log-dir` nonexistent flag | Task 1/4 selftests | Drop; `HOME`-only redirection |
| 7 | L4 line-shape assertion | Task 1/4 selftests | `json.loads` round-trip on the written line |
| 8 | L5 agy timeout field path | Task 5 README, doctor (5) | Build-time-verify the `timeout` field path |
| 9 | L6 Task 7 LIVE negative `no-anchor` | Task 7 LIVE assertion | Assert no `no-anchor` for in-repo Claude run |

## r17 Amendments

| # | Finding | Affects | Action |
|---|---------|---------|--------|
| 1 | M1 core keying write lacks absent-parent selftest arm | Task 4 `#project_no_anchor_in_non_git_dir` | Add core-side absent-parent arm (helper makedirs creates the dir) |
| 2 | M2 doctor cross-refs "two existing agy assumptions" but Monitor lists two | Monitor enumeration, doctor spec | Add the `timeout` field path as agy assumption (c) |
| 3 | M3 makedirs+open+write duplicated byte-for-byte, no shared helper | Terms step 3, Task 1, Task 4 Log discipline | Extract `_append_hooks_log_line(payload)` in `facts_paths.py`; both writers call it (also folds M6, L4 SRP, L9 wording, L10 run-on) |
| 4 | M4 resolver/doctor/README timeout triple is a prose lockstep | Terms, doctor (5), README | `RESOLVER_GIT_TIMEOUT_S = 5` named constant; drop the prose lockstep note |
| 5 | M5 r16 header bullet 143w | Header | Trim to ~60w; add an r17 bullet |
| 6 | M6 r15-M1 sink-loss story restated at ~9 sites | Terms, LOUD keying, Task 1/4, READMEs, Monitor | State ONCE in Terms step 3; one-clause back-refs elsewhere (folds into M3) |
| 7 | L1 single `try/except OSError` must cover makedirs | Terms step 3, Log discipline, selftest | Name the read-only-parent guard; add a read-only-parent arm |
| 8 | L2 doctor `timeout=10` PASS arm | `#doctor_agy_timeout` | Add `2 * RESOLVER_GIT_TIMEOUT_S` PASS arm |
| 9 | L3 selftest "the line" wording | Task 4 selftest | "LAST non-empty line" (byte-identical to Task 1) |
| 10 | L5/L6 threat-model clauses | Terms threat model | Add symlinked-ancestor assumption + HOME-trust clause |
| 11 | L7 missing r16 Amendments table | End of plan | Add the r16 Amendments table |
| 12 | L8 `#doctor_agy_timeout` not in Validation Commands | Validation Commands | Add the cores-block line |
| 13 | L9 "sub-PIPE_BUF" wrong mechanism | Terms step 3, Log discipline | "`O_APPEND` offset-atomic single `write()`" |
| 14 | L10 Log discipline 8-line run-on | Task 4 Log discipline | Break the sentence (folds into M3) |

## r18 Amendments

| # | Finding | Affects | Action |
|---|---------|---------|--------|
| 1 | M1 README Doctor subsection stale `>= 6`/`5s` literal | Task 5 README | Rewrite to `> RESOLVER_GIT_TIMEOUT_S` (constant-derived) |
| 2 | M2 core absent-parent arm non-discriminating (non-git cwd) | Task 4 selftest | Pin a git-repo cwd so the resolver does not pre-create `logs/` |
| 3 | M3 `json.dumps` `TypeError` escapes the helper's `try/except OSError` | Terms step 3 helper body, selftest | `json.dumps(payload, default=str)` + non-serializable-payload selftest arm |
| 4 | L1 `facts_paths.py` SRP home for the helper | Terms step 3 | Accept documented v1 tradeoff (helper's sole leaf caller lives there; `project_key.py` extraction is the real trigger) |
| 5 | L2 Task 4 `json.loads` wording not byte-identical to Task 1 | Task 4 selftest | Match Task 1 verbatim ("LAST non-empty line" + prefix clause) |
| 6 | L3 threat model echoed in Log discipline | Task 4 Log discipline | One-clause "Threat model per Terms step 3" back-ref |
| 7 | L4 r17 header bullet 76w | Header r17 bullet | Trim to ~60w (now ~58w) |
| 8 | L5 "no prose note to keep" over-reaches for README | Terms step 3, doctor spec | Scope the lockstep claim to Python consumers; README literal hand-synced |
| 9 | L6 makedirs-then-open TOCTOU silent-loss | Terms step 3 helper body | Accept with a one-line note (single-user trust boundary; gate unaffected) |
| 10 | L7 r15 Amendments row 4 historical literal | r15 Amendments table | Informational; left as historical record |

## r19 Amendments

| # | Finding | Affects | Action |
|---|---------|---------|--------|
| 1 | M1 SERIALIZE-DEFENSIVELY 112w run-on (prose-clarity) | Terms step 3 helper body | Compressed the 112w six-clause run-on to one numbered clause under "Defensive choices (1)" (target ~45w; delivered ~78w - the residual is the load-bearing L1 honest-scoping + PRECONDITION) |
| 2 | M2 helper body 290w wall of text (prose-clarity + simplification) | Terms step 3 helper body | Rewritten recipe-first; rationale as three compact numbered clauses; ~180w (folds L2 SRP parenthetical) |
| 3 | L1 "can never escape" over-claim (testing + premortem; circular / `__str__`-raises escape; the agents' `bytes` sub-claim is FALSE - `default=str` handles bytes) | Terms step 3 prose, selftest arm | Scoped the claim to realistic scalars; stated the acyclic/str-coercible PRECONDITION; tightened the selftest wording from "can never escape" to "covers the realistic non-serializable-scalar mistake" |
| 4 | L3 r18 header bullet 69w (simplification) | Header r18 bullet | Cut to ~55w; dropped the over-claim clause |

## r20 Amendments

| # | Finding | Affects | Action |
|---|---------|---------|--------|
| 1 | M1 SRP/extraction-trigger pointer cited r17 Amendments but the `project_key.py` trigger lives in r18 row 4 (architecture) | Terms step 3 line 120 | Corrected pointer to "r18 Amendments table (row 4)" |
| 2 | L1 SERIALIZE clause 78w vs the ~45w target (simplification) | Terms step 3 clause (1) | Dropped the redundant "(not bare `json.dumps`)" parenthetical (78w -> 75w); no load-bearing content lost |
| 3 | L2 r19 header bullet 61w, inline scope parenthetical re-derives mechanism (prose-clarity) | Header r19 bullet | Trimmed to ~46w; dropped the inline scope parenthetical |
| 4 | (Accepted) realistic-scalar enumeration duplicated across Terms clause (1) and the selftest arm (simplification F2) | Terms step 3 + Task 1 selftest arm | Left as-is; tolerable cross-boundary (contract vs verification) duplication of a one-phrase list |


