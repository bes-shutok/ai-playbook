# Backlog: summarizer pinned-open helper dedup (read_private_file / read_byte_buffer)

Status: done (2026-09-08, commit 9462142: extracted `_open_pinned_read`; full selftest suite ALL PASS; branch-review panel r1 zero findings)
Workflow: backlog
Source: docs/reviews/2026-09-07-2026-09-06-summarizer-tail-trio-code-review-r1.md (F3, Low, non-blocking, simplification#shrink)
Severity: Low
Scope: scripts/summarize_review_stats.py

## Problem

The dirfd-open / errno-translate / fdopen block now exists twice: `read_private_file` (final-component open, translated re-raise `cannot read private file: {path}: {exc}`) and `read_byte_buffer` (translated re-raise `cannot read byte buffer: {path}: {exc}`), differing only in message strings. Two hand-maintained copies of the security-sensitive symlink-refusal errno contract (ELOOP/ENOTDIR -> `PermissionsError("refusing to follow symlink target: ...")` via `from exc`) mean a future fix can land in one reader and miss the other.

- Exact location: `scripts/summarize_review_stats.py`, `read_private_file` (except branch around the final-component open) and `read_byte_buffer` (except branch around the final-component open).

## Suggested fix

Extract a single `_open_pinned_read(path, parent_fd, err_what)` helper owning the `os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC` dirfd-relative open, the ELOOP/ENOTDIR -> PermissionsError translation, and the `type(exc)(f"{err_what}: {path}: {exc}") from exc` re-raise; both readers call it with their own `err_what` prefix (`cannot read private file` / `cannot read byte buffer`). The fdopen-on-failure fd-close idiom can also fold in if it stays byte-identical per reader.

## Why not fixed now

The plan's Review Scope (docs/plans/2026-09-06-summarizer-tail-trio.md) freezes `read_private_file` except its final-component except branch (diagnostics only) and admits only `read_byte_buffer`'s body plus the new selftest arms; a helper extraction touches `read_private_file`'s open machinery beyond the in-scope except branch. Deferred by the address-r1 sub-agent per the plan scope boundary (decision recorded in the staging doc's F3 Analysis).
