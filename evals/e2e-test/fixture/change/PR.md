# PR: Tidy the CLI and relax the resolution rule

- `list` output is shorter: the priority column moved out of the default view (it comes back with a flag in a later PR).
- The resolution note minimum is relaxed so short notes like "duplicate" are accepted.
- Assigning a ticket now works at any point in its life, which support asked for.
- `--help` gained a description line.

All tests pass locally.
