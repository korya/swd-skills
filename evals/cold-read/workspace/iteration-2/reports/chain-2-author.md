I've applied the fixes to `cli.md` and `tickets.md`. The final summary follows.

**Spec revised after the cold read, not committed.** The two Blockers and most Majors are fixed in `cli.md` and `tickets.md`. I did not re-run `make lint` or `make test`, since only docs changed.

| # | Finding | Verdict | Action |
|---|---|---|---|
| 1 | Blocker: CLI-012 skips corrupt lines (INV-004, LOG-007) | FIX | CLI-012 now fails like every other command and defers the failure format to the open CLI-007 conflict. An unknown priority in the log is covered the same way (finding 13). |
| 2 | Blocker: TKT-019 example arithmetic | FIX | Ticket 1 was due 8 h ago and ticket 2 6 h ago, so ticket 1 comes first. |
| 3 | `list` reordered, against TKT-013 | FIX | The reorder is removed. `list` stays in ID order, and the example now has the overdue ticket at ID 2. I added an open question. |
| 4 | CLI-010 example puts `--log` after the subcommand | FIX | The example is now `ticketdesk --log desk.jsonl overdue`. CLI-011 mentions that `--log` goes before the subcommand. |
| 5 | stderr note on success breaks CLI-008 | FIX | The note is dropped. Empty output with exit 0, as `list` does. I added an open question. |
| 6 | "Whole seconds" is false | FIX | The claim is removed (`store.py:14,20`). |
| 7 | `OVERDUE` replaces the state; no alternative; script claim | ASK | The marker alternative is in the open questions. The script-counting promise is removed from CLI-006. |
| 8 | CLI tests cannot control time | FIX | TKT-014 now says the plan must decide how a test controls time. |
| 9 | TKT-014 cites LOG-004 | FIX | It now cites INV-005. |
| 10 | TKT-017 overstates determinism | FIX | It now says the displayed word also depends on the time of the run. |
| 11 | Draft written into the index files; extra sections | REJECT | Both index entries and AGENTS.md:118-119 label it a draft awaiting sign-off. `product-specs/README.md` "Spec format" sets rules per item, not per file section, and forbids no extra sections. |
| 12 | CLI-011 relies on unspecced `list extra` behaviour | FIX | That sentence is removed. |
| 13 | Unknown priority on `overdue` | FIX | Covered in CLI-012 (see finding 1). |

**Cold-read note**
- Read 1: 13 findings. 11 FIX, 1 ASK, 1 REJECT.
- REJECT (finding 11): the draft is labelled in `AGENTS.md:118-119` and in both index entries. `product-specs/README.md` "Spec format" has no per-file section rule.
- ASK (finding 7): whether `OVERDUE` replaces the state or is added alongside it. It is in the open questions.
- New open questions: `list` keeps ID order, and `overdue` prints nothing when empty.
- Read 2: not run, because I can't start a subagent here.

SECOND READ: yes — rule 4: a Blocker got FIX, and rule 3 also applies because CLI-012 and the `list` order changed requirements.