I've finished testing and am now writing up the findings. The product ran fine; I just needed to compare the spec against its output. Nothing in the repo was changed. My scratch files are in temp directories.

FINDINGS

- **Severity:** Blocker
  **Where:** `tickets.md`, TKT-019, the worked example ("ticket 1 has priority `P3` and was created 80 hours ago…").
  **What:** The arithmetic is wrong, so the example gives the opposite order from the rule it illustrates. Ticket 1 (P3, 80h ago) was due 80−72 = 8 hours ago, not 1 hour ago. Ticket 2 (P1, 10h ago) was due 6 hours ago. The earliest-due ticket is ticket 1, so it comes first. The doc says ticket 2 comes first. Someone building from the example would get the wrong order.
  **Evidence:** I built a log with those two tickets (`at` = now−80h and now−10h) and used TKT-005's table. `python3 -c "print(80-72, 10-4)"` prints `8 6`. `overdue` isn't built, so I couldn't run the ordering itself.

- **Severity:** Blocker
  **Where:** `cli.md`, CLI-012 (overdue skips unreadable lines, exit 0).
  **What:** This contradicts INV-004 and LOG-007, which say a corrupt line stops the operation and nothing is skipped. It also breaks CLI-006's "`overdue` shows the same tickets as `list`", since `list` fails on the same log. The spec doesn't flag this as an invariant break, and AGENTS.md says that needs explicit user confirmation. Skipping a line can also silently drop a `closed` or `assigned` event. A closed ticket would then show as `OVERDUE`, or the ticket list would go wrong without warning. Skipping is also not enough on its own: three other kinds of damage make the product crash today (see the next item).
  **Evidence:** Appending `not json` plus a valid line to a log and running `list` gives `ValueError: …d.jsonl:5: corrupt event: Expecting value…` with `[rc=1]`.

- **Severity:** Major
  **Where:** `cli.md`, CLI-012 ("a log line that it cannot read").
  **What:** "Cannot read" is undefined, and the product has more failure modes than bad JSON. All of them escape as raw tracebacks with exit 1. CLI-007 already lists this as an open TODO.
  **Evidence:**
  - `{"kind":"created","id":9}` gives `KeyError: 'title'`, rc=1.
  - A line of `\xff` gives `UnicodeDecodeError`, rc=1.
  - An `assigned` event for a nonexistent ticket gives `KeyError: 7`, rc=1.
  - `--log <directory>` gives `IsADirectoryError`, rc=1.

- **Severity:** Major
  **Where:** `cli.md`, CLI-010 (`ticketdesk overdue --log desk.jsonl`) and CLI-011 ("`overdue` takes no argument and no option of its own").
  **What:** The example command is rejected by the product today. `--log` belongs to the top-level parser and must come before the subcommand, so the CLI-010 example would fail on a built `overdue` unless the parser is redesigned. The CLI-011 wording is also muddled, because `--log` is an option after the command name.
  **Evidence:** `ticketdesk list --log a.jsonl` gives `ticketdesk: error: unrecognized arguments: --log /…/a.jsonl`, `[rc=2]`.

- **Severity:** Major
  **Where:** `cli.md`, CLI-006 ("`list` prints the overdue tickets first… then the other tickets") against its own claim and TKT-013.
  **What:** This is a conflict inside the draft. It says a non-overdue ticket prints the same as in 0.3.0 and that `list` is "in ID order, see TKT-013". Putting overdue tickets first breaks TKT-013's "sorted by ID ascending" for any log with a late ticket. The request only asked for tickets to *show* as OVERDUE in `list`, not to be reordered. The reordering is not listed among the open questions and TKT-013 is not amended.
  **Evidence:** `list` today sorts only by ID (`sorted(..., key=lambda t: t.id)`). My log with tickets 1 (old P3), 2 and 3 prints `#1`, `#2`, `#3`. Under the draft, `#1` would come first only if it was due earliest.

- **Severity:** Major
  **Where:** `cli.md`, CLI-006 ("Every output line with `OVERDUE` in that position is one overdue ticket, so a script counts the overdue tickets by counting those lines").
  **What:** The guarantee is false. A title can contain a newline, and `create` accepts it, so a single ticket can print a second line that looks exactly like an overdue ticket. Counting lines then overcounts. The only reliable fix is to sanitize or escape titles, which the spec doesn't mention.
  **Evidence:** `create $'x\n#9 [P1] OVERDUE  fake'` prints `#2 open x` then `#9 [P1] OVERDUE  fake` on the next line, and `list` shows the forged line:
  ```
  #2 [P3] open     x
  #9 [P1] OVERDUE  fake
  ```
  The title `OVERDUE` on its own is harmless: `#1 [P3] open     OVERDUE`.

- **Severity:** Major
  **Where:** `cli.md`, CLI-010 (empty result prints `no overdue tickets` to stderr, exit 0), against CLI-008 ("a command that succeeds… writes nothing to stderr").
  **What:** The draft contradicts CLI-008 and doesn't say so. The only open question about it covers the exit code, not the clash with CLI-008. The nearest built command, `list`, prints nothing on empty and nothing to stderr.
  **Evidence:** `ticketdesk --log none.jsonl list` prints nothing, `[rc=0]`, and doesn't create the file.

- **Severity:** Minor
  **Where:** `tickets.md`, TKT-019 ("The log stamps events in whole seconds, so two tickets of one priority created in the same second have an equal due time").
  **What:** The log stamps fractional seconds, not whole seconds. `at` comes from `time.time()`, so equal due times are very unlikely. The ID tie-break and the "exact due time" boundary in TKT-014 almost never apply in practice. TKT-014's "exact due time is not overdue" rule is effectively untestable with a real clock.
  **Evidence:** `{"at": 1793913097.391066, "id": 1, …}` and `{"at": 1793913097.421195, "id": 2, …}`.

- **Severity:** Minor
  **Where:** `cli.md`, CLI-011 ("`ticketdesk list extra` is rejected in the same way", "Nothing is printed to stdout").
  **What:** This is true today (exit 2, usage on stderr, nothing on stdout), so it's supported. But "usage error" is the argparse message, and `-h` exits 0, which the spec leaves out of scope. The spec doesn't address `ticketdesk overdue` run before a subcommand is recognized, because the command is unknown today.
  **Evidence:** `ticketdesk --log a.jsonl list extra` gives `unrecognized arguments: extra`, `[rc=2]`. `ticketdesk list -h` gives rc=0. `ticketdesk overdue` today gives `invalid choice: 'overdue'`, rc=2.

- **Severity:** Minor
  **Where:** `cli.md`, CLI-006 ("padded to 8 characters like a state").
  **What:** The example's spacing is right (`OVERDUE` is 7 characters plus one pad), but with non-ASCII titles the output shows the pad is by code points, not terminal width. This is cosmetic. TKT-017's claim that `list` doesn't alter the log or create a missing file did hold.
  **Evidence:** `shasum` of the log is identical before and after `list`, and a missing log is not created.

**Not testable today:** TKT-014 to TKT-016, TKT-018 and the OVERDUE rendering depend on code that doesn't exist. The checks above cover only what the nearest built command, `list`, can confirm or refute.

**Supported:** the 0.3.0 line format, TKT-017's no-write and no-create behavior, the exit code 2 for a bad or missing subcommand, and `list extra` rejection.