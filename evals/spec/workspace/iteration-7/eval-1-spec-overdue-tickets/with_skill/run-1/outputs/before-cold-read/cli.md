# Command line

The `ticketdesk` command is the only user interface. Each invocation runs one command
against one log file and exits. Ticket rules are in [`tickets.md`](tickets.md). Log
behavior is in [`event-log.md`](event-log.md). This file covers the command surface:
arguments, output, errors, and exit codes.

The overdue items are a draft of 2026-11-05, not signed off by the user and not built.
They are CLI-010 to CLI-012, the `overdue` subcommand in CLI-001, and the `OVERDUE` word
in CLI-006. ticketdesk 0.3.0 has four subcommands and never prints `OVERDUE`. The goals,
the non-goals, and the open questions are in
[`tickets.md`](tickets.md#overdue-tickets).

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

For an overdue ticket, see TKT-014, the line shows `OVERDUE` in place of the state. The
word is uppercase and is padded to 8 characters like a state. The line of a ticket that is
not overdue is the same as in ticketdesk 0.3.0, so a `closed` ticket always shows
`closed`. For example, when only ticket 1 is overdue:

```
#1 [P1] OVERDUE  Printer on fire
#2 [P3] assigned New badge for Lee
#3 [P2] closed   Reset the VPN token
```

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

`ticketdesk overdue` prints one line per overdue ticket, in the order of TKT-019, see also
TKT-018. Each line is the line that `list` prints for that ticket per CLI-006, so each one
shows `OVERDUE`. With no overdue tickets it prints nothing and exits with code 0. A missing
log file is one such case, see LOG-006.

### CLI-011: overdue takes no arguments

`ticketdesk overdue` takes no argument after the command name. An extra argument is
rejected with a usage error on stderr and exit code 2. Nothing is printed to stdout.

### CLI-012: overdue on a corrupt log

A corrupt log line stops `ticketdesk overdue` per LOG-007, and no ticket line is printed.
The stderr output and the exit code are the same as those of `ticketdesk list` on the same
log.

TODO: the open TODO under CLI-007 decides what that report is. CLI-012 does not settle it.
Today `list` on a corrupt log prints a Python traceback and exits with code 1.
