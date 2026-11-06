# Questions for the overdue tickets spec

Nobody was available during this run. Each question below carries the assumption the spec
proceeds on. An answer that differs changes only the items named with it.

The numbers match the list "Open questions on overdue tickets" at the end of
`docs/product-specs/tickets.md`. Question 3 here is question 3 there.

## Blocking questions, asked as one round

Questions 1, 2, and 4 change the shape of the spec. The skill asks them before it drafts.

### 1. Is a closed ticket ever overdue?

A ticket can be closed after its due time. The request does not say whether that ticket
still shows as OVERDUE.

- **Assumption:** no. Only `open` and `assigned` tickets are overdue. Closing an overdue
  ticket ends its overdue status.
- **Why:** the list tells an agent what needs work now. A closed ticket needs none.
- **If the answer differs:** TKT-015 changes, and a "closed late" mark needs its own
  line format in CLI-006.

### 2. Where does OVERDUE appear in a `ticketdesk list` line?

Today a line is `#<id> [<priority>] <state> <title>`. The request says "show as OVERDUE"
and does not give the place of the word.

- **Assumption:** `OVERDUE` is an extra word before the state, and the state stays:
  `#<id> [<priority>] OVERDUE <state> <title>`. The line of a ticket that is not overdue
  does not change.
- **Why:** an agent still sees whether an overdue ticket has an owner. The start of a
  title cannot pass for the marker. I ran the current CLI with the title
  `OVERDUE invoice from ACME` and it printed `#2 [P3] assigned OVERDUE invoice from ACME`.
  A marker next to the title would make that line look overdue.
- **Cost of the assumption:** on an overdue line the state is the fourth field, not the
  third. The title starts 8 characters further right. A script that reads the state by
  position breaks on overdue lines.
- **Alternative A:** `OVERDUE` replaces the state word: `#1 [P1] OVERDUE  Printer on fire`.
  The columns stay aligned. The agent no longer sees `open` against `assigned`.
- **Alternative B:** `OVERDUE` after the state or after the title. A title can imitate it.
- **If the answer differs:** CLI-006 and CLI-010 change. No TKT item changes.

### 4. Does a line show the due time, or how late the ticket is?

No command shows the due time today. `ticketdesk overdue` sorts by a value that the agent
cannot see.

- **Assumption:** no. Both commands print the same fields as today plus the marker.
- **Why:** the request asks for a marker and a sorted list, not for a new field.
- **If the answer differs:** CLI-006 and CLI-010 get a new field, and its format needs a
  decision on time zone and precision.

## Questions that do not block the shape

The spec marks each of these with a `TODO` line and lists it under its open questions.

| # | Question | Assumption in the spec | Item |
|---|----------|------------------------|------|
| 3 | Is a ticket overdue at exactly its due time? | No. Overdue starts after the due time. | TKT-014 |
| 5 | Does `ticketdesk overdue` exit with a non-zero code when it finds overdue tickets? | No. It exits with code 0, like `list`. | CLI-010 |
| 6 | What is the order of two overdue tickets with the same due time? | ID ascending. | TKT-016 |
| 7 | What happens with an extra argument, as in `ticketdesk overdue 5`? | Usage on stderr and exit code 2. `ticketdesk list extra` does the same today. | CLI-011 |
| 8 | Do the goals, the non-goals, and the status stay in `tickets.md` after sign-off? | The goals and non-goals stay. The status line and each answered question go. | Section form |

Question 8 came from the cold read. The other spec files hold only an intro and the ID
items. The section "Overdue tickets" adds goals, non-goals, a status, and open questions.

## Assumptions that follow from existing specs

These have no `TODO` line, because an existing item already implies each one.

| Unknown | Assumption in the spec | Follows from |
|---------|------------------------|--------------|
| What does `ticketdesk overdue` print with no overdue ticket, or with no log file? | Nothing, with exit code 0. | CLI-006, CLI-008, LOG-006 |
| Does `ticketdesk list` change its order, or get a filter option? | No. | TKT-013, non-goals |
| Does assigning a ticket reset the due time? | No. The due time counts from the creation time. | TKT-005 |
| Which clock counts: wall clock or business hours? | Wall clock. | TKT-005, non-goals |
| Does the output of `create`, `assign`, or `close` change for an overdue ticket? | No. | CLI-003 to CLI-005, non-goals |

## Conflicts and adjacent specs

- **CLI-007 TODO, open before this run.** A corrupt log line escapes as a traceback with
  exit code 1. `ticketdesk overdue` replays the log, so it inherits this conflict. The
  spec does not settle it. CLI-010 points at the TODO.
- **LOG-009.** Replay stays deterministic. The output of `ticketdesk list` does not: the
  same log prints different lines once a ticket passes its due time. The spec says so.
- **INV-005.** It governs the time of events. TKT-014 needs the current time of a command,
  which no existing spec covers. The spec defines it as the moment the command runs and
  says that the plan chooses the source.
- **Titles with a line break, found by the cold read.** `ticketdesk create` accepts a title
  that contains a line break, and `list` then prints a second, false line. That gap exists
  today under TKT-002. CLI-006 names it and does not close it. Is a fix wanted?
- **No new invariant is proposed.** "Overdue is not a state and no event records it" is a
  feature-local contract. It follows from INV-001, INV-002, TKT-001, and LOG-002.

## Sign-off

The spec is a proposal. `AGENTS.md` and `docs/README.md` both say a doc change needs the
user's confirmation. Nothing is committed.
