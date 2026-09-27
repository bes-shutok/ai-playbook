# Completed plans archive

This directory holds completed plans. It is an archive home, not a working surface: an
archive transition is a rename of the live path (`git mv`), never an add-plus-keep copy. A plan exists in exactly one lifecycle state at a time
(open, completed, deferred, rejected), and the plans root must not retain an
archived basename.

The done sweep's `plans-archive-twin` gate fails a closeout that leaves a
dated plan basename at the plans root and in an archive state at the same
time; `scripts/check_maintenance_pins.sh` (`check_live_vs_archive_duplicates`)
owns the corpus-wide post-hoc check over both the plans and backlog roots.

The `deferred/` and `rejected/` homes carry their own arrival disciplines in
their own READMEs; this file scopes only the completed home.
