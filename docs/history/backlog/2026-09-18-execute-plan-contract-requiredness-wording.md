# Staged-terminal contract requiredness wording overstates (r5 CD5-1, deferred at round cap)

Evidence: runtime-contract.md clause (4) says "the verdict is the only optional field", but last_fix_commit is equally tolerated absent or null (code: payload.get("last_fix_commit"); ancestry check only when non-null; schema defines it as "commit sha string or null").

Direction: reword to "the verdict is the only field whose absence falls through" or append "last_fix_commit is nullable (absent or null skips the ancestry check)".
