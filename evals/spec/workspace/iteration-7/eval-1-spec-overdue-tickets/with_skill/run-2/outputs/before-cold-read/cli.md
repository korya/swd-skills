# Command line

The `ticketdesk` command is the only user interface. Each invocation runs one command
against one log file and exits. Ticket rules are in [`tickets.md`](tickets.md). Log
behavior is in [`event-log.md`](event-log.md). This file covers the command surface:
arguments, output, errors, and exit codes.

The `overdue` command and the `OVERDUE` marker are proposed and not built. They are in
CLI-001, CLI-006, CLI-010, and CLI-011. The status and the open questions are under
[Overdue tickets](tickets.md#overdue-tickets).

Prefix: `CLI`.

---

### CLI-001: Commands

The `ticketdesk` command takes one of five subcommands. They are `create`, `assign`,
`close`, `list`, and `overdue`. Invoking `ticketdesk` with no subcommand, or with an
unknown one, prints usage to stderr and exits with code 2.

### CLI-002: Log path selection

The log path comes from the first of three sources that is set. In order, they are the
`--log` option, the `TICKETDESK_LOG` environment variable, and `tickets.jsonl` in the
current directory.

### CLI-003: create

`ticketdesk create <title> [--priority <P>]` creates a ticket per TKT-002 and TKT-003 and
prints `#<id> open <title>`. Without `--priority` the ticket gets priority `P3`.

### CLI-004: assign

`ticketdesk assign <id> <assignee>` assigns the ticket per TKT-006 to TKT-008 and prints
`#<id> assigned -> <assignee>`.

### CLI-005: close

`ticketdesk close <id> <resolution>` closes the ticket per TKT-009 to TKT-011 and prints
`#<id> closed`.

### CLI-006: list

`ticketdesk list` prints one line per ticket in ID order, see TKT-013. Each line is
`#<id> [<priority>] <state> <title>` with the state padded to 8 characters. With no tickets
it prints nothing.

The line of an overdue ticket, see TKT-014, carries the word `OVERDUE` before the state. It
is `#<id> [<priority>] OVERDUE <state> <title>`, with the state still padded to 8
characters. The line of a ticket that is not overdue has no marker and is the same as
before this change.

```
#1 [P1] OVERDUE open     Printer on fire
#2 [P3] assigned OVERDUE invoice from ACME
#3 [P2] closed   Email bounces
```

In this example only ticket `1` is overdue. Ticket `2` is not overdue, and its title starts
with the word `OVERDUE`. The marker comes before the state, so a title cannot imitate it.

TODO: the place of the marker is an assumption, see open question 2 under
[Overdue tickets](tickets.md#overdue-tickets).

### CLI-007: Ticket rule errors

A command rejected by a ticket rule prints `error: <message>` to stderr and exits with
code 2. Nothing is printed to stdout. The ticket rules are TKT-002 and TKT-007 to TKT-012.

TODO: two failures do not follow this rule today. An unknown priority (TKT-003) and a
corrupt log line (LOG-007) escape as a Python traceback with exit code 1. Confirm with the
user whether CLI-007 should cover them, then fix either the code or this spec.

### CLI-008: Success exit code

A command that succeeds exits with code 0 and writes nothing to stderr.

### CLI-009: Ticket ID is an integer

A non-integer `<id>` for `assign` or `close` is rejected with a usage error on stderr and
exit code 2. No event is appended.

### CLI-010: overdue

`ticketdesk overdue` prints one line per overdue ticket, in the order of TKT-016. Each line
has the format that CLI-006 gives for an overdue ticket, marker included. With no overdue
ticket it prints nothing. That covers a log file that does not exist, see LOG-006. The exit
code is 0 whether or not a ticket is overdue, see CLI-008.

A corrupt log line stops `ticketdesk overdue` as it stops `ticketdesk list`, see LOG-007.
How the command reports that error is the open TODO under CLI-007. This item does not
settle it.

### CLI-011: overdue takes no argument

`ticketdesk overdue` takes no argument after the subcommand. An extra argument, as in
`ticketdesk overdue 5`, prints usage to stderr and exits with code 2. Nothing is printed to
stdout.
