I've revised the spec, and a second cold read is still owed. I couldn't run it here. Nothing is committed.

**Verdicts**

| # | Finding | Verdict |
|---|---|---|
| 1 | TKT-019 example arithmetic is wrong (Blocker) | FIX. Ticket 1 is now created 73 hours ago, so it was due 1 hour ago and ticket 2 still comes first. The reader's own numbers (80 hours) would have put ticket 1 first, which doesn't show that order follows due time. |
| 2 | CLI-012 skips corrupt lines, against INV-004 and LOG-007 (Blocker) | FIX. CLI-012 now says `overdue` fails like `list` and follows the CLI-007 TODO. I also added an open question. |
| 3 | CLI-006 moves overdue tickets to the top of `list` | FIX. The ID order of TKT-013 is kept, the example now shows an overdue ticket 4 in ID order, and there is an open question. |
| 4 | `--log` example is invalid after the subcommand | FIX. The example is now `ticketdesk --log desk.jsonl overdue`, and the item says why. |
| 5 | The stderr note in CLI-010 conflicts with CLI-008 | FIX. `overdue` prints nothing when empty, like `list`. The open question now says a note would need an exception to CLI-008. |
| 6 | "Events are stamped in whole seconds" is false | FIX. It now says event times are fractions of a second (`store.py:14,20`), so equal due times are rare, with an example. |
| 7 | `OVERDUE` replacing the state hides `open` and `assigned` | ASK. The open question now offers the alternative of keeping the state and adding a marker column. |
| 8 | Overdue output depends on the clock, and LOG-009 is easy to misread | FIX. TKT-014 says a test can fix the current time, and TKT-017 says overdue is not covered by LOG-009. `tickets.py` has no clock, as the reader said. |
| 9 | "Same clock that stamps events" is misleading | FIX. The current time is now read when the command runs, uses the epoch scale of LOG-004, and is never stored. |
| 10 | `-h` is unspecified | FIX. `-h` works as for the other subcommands. |
| 11a | "Not built" sits inside the normative items CLI-001, CLI-006 and CLI-010 | FIX. I removed it from those items. The status banners stay. |
| 11b | The AGENTS.md and README edits were out of scope | REJECT. `docs/README.md:57-58` requires the `AGENTS.md` and specs README indexes to stay in sync with spec changes. The draft is flagged for sign-off (`docs/README.md:39` bans only silent changes). |

**Cold-read note**
- Read 1: 10 FIX, 1 ASK, 1 REJECT. That is 12 verdicts from 11 findings, because finding 11 was split in two.
- REJECT 11b: the evidence is `docs/README.md:57-58` and `docs/README.md:39`, as in the table.
- ASK 7: choose between replacing the state with `OVERDUE` and adding a marker next to it. It is now in the open questions of `tickets.md`.
- Two new ASKs came from the fixes: `list` keeps ID order, and an empty `overdue` is silent.
- Read 2: not run, because I can't start a subagent here.

SECOND READ: yes (rule 4: Blockers 1 and 2 got FIX; rule 3 also applies, because removing the reorder from `list` and the skip-corrupt-lines behavior from `overdue` changed requirements)