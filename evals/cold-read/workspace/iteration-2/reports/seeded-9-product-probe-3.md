Testing is finished and I'm writing up the report. I ran 0.3.0 against odd titles, bad arguments, a missing log and a damaged log. For `overdue` I used `list` as the nearest built command, since `overdue` doesn't exist yet.

FINDINGS

- **Severity:** Blocker
  **Where:** cli.md CLI-012 (with INV-004, LOG-007, and the cli.md status note)
  **What:** CLI-012 says `overdue` skips an unreadable line and exits 0. INV-004 says a corrupt line is never skipped and no partial state is returned. LOG-007 says every operation stops on one. The draft breaks an invariant and does not mention it. AGENTS.md says that needs explicit user confirmation. It also leaves `list` and `overdue` disagreeing on the same log. A skipped line may be a `closed` event, which would show a closed ticket as overdue. A skipped `created` line would make a later `assigned` event crash replay with a `KeyError`.
  **Evidence:**
  ```
  $ ticketdesk --log bad.jsonl list      # bad.jsonl ends with the line "garbage"
  ValueError: bad.jsonl:5: corrupt event: Expecting value: line 1 column 1 (char 0)
  [exit 1]
  ```
  Today a damaged log gives a traceback and exit 1 from every command, `list` included.

- **Severity:** Blocker
  **Where:** cli.md CLI-006, the claim that counting lines with `OVERDUE` in the state position counts the overdue tickets
  **What:** Titles can contain newlines, and `create` accepts them. A title can therefore forge a line that looks like `#9 [P1] OVERDUE  fake`, and a script that counts those lines counts it. The claim "every output line with OVERDUE in that position is one overdue ticket" is false.
  **Evidence:**
  ```
  $ ticketdesk --log d.jsonl create $'line1\n#9 [P1] OVERDUE  fake'
  #2 open line1
  #9 [P1] OVERDUE  fake
  $ ticketdesk --log d.jsonl list
  ...
  #2 [P3] open     line1
  #9 [P1] OVERDUE  fake
  ```
  The title containing only the word `OVERDUE` (`Printer OVERDUE`) is harmless. The multi-line title is the problem. The spec needs to drop the counting claim or reject newlines in titles.

- **Severity:** Major
  **Where:** cli.md CLI-010, the example `ticketdesk overdue --log desk.jsonl`, against CLI-002 and CLI-011
  **What:** `--log` is a top-level option and must come before the subcommand. The example is a usage error on the nearest built command, `list`. It also contradicts CLI-011, which says `overdue` takes no option of its own.
  **Evidence:**
  ```
  $ ticketdesk list --log d.jsonl
  ticketdesk: error: unrecognized arguments: --log d.jsonl
  [exit 2]
  ```
  The working form is `ticketdesk --log desk.jsonl overdue`.

- **Severity:** Major
  **Where:** cli.md CLI-006, "`list` prints the overdue tickets first", against the first paragraph of CLI-006 and tickets.md TKT-013
  **What:** CLI-006 still says "one line per ticket in ID order, see TKT-013", and TKT-013 still says "sorted by ID ascending". The new paragraph moves overdue tickets to the top, so both statements become false. It also breaks the goal that output for non-overdue tickets stays unchanged. A non-overdue ticket with a low ID moves down when a later ticket goes overdue. The spec edits neither statement and does not flag the conflict.
  **Evidence:** Today `list` sorts strictly by ID.
  ```
  $ ticketdesk --log old.jsonl list
  #1 [P3] open     old
  #2 [P1] assigned p1
  ```
  Ticket 1 was created 100 hours ago, so it is overdue by the draft's rule. It is still in ID order.

- **Severity:** Major
  **Where:** cli.md CLI-006, "A `closed` or `assigned` ticket always shows its state"
  **What:** This contradicts "`OVERDUE` in place of the state" for an overdue ticket, and TKT-016 ("Assigning an overdue ticket leaves it overdue"). An overdue `assigned` ticket cannot both show `assigned` and show `OVERDUE`. The sample output hides this because ticket 2 is not overdue. The open questions admit that the assignee is lost, but this sentence says the opposite.
  **Evidence:** In the fixture above, ticket 2 is `P1`, 10 hours old and assigned. Today it prints `assigned`, so there is no behavior to support either reading.

- **Severity:** Major
  **Where:** cli.md CLI-010, "prints `no overdue tickets` to stderr and exits with code 0", against CLI-008
  **What:** CLI-008 says a successful command exits 0 and writes nothing to stderr. CLI-010 writes to stderr on a success, and the spec doesn't mention the conflict. The nearest command, `list`, with no tickets or no log file, prints nothing to either stream. The spec doesn't say why `overdue` should differ. It is also an open question that the user hasn't confirmed.
  **Evidence:**
  ```
  $ ticketdesk --log nope.jsonl list
  [exit 0]        # stdout and stderr both empty, and nope.jsonl is not created
  ```

- **Severity:** Minor
  **Where:** tickets.md TKT-019, "The log stamps events in whole seconds"
  **What:** The log stamps events with fractional float seconds, so the premise is false. LOG-004 says only "seconds since the Unix epoch". Same-second ties are practically impossible for tickets created one command at a time, but the tie rule and its justification need rewording. A hand-edited log or a coarse clock could still tie.
  **Evidence:**
  ```
  {"at": 1793913099.526433, "id": 1, "kind": "created", ...}
  {"at": 1793913099.5557141, "id": 2, "kind": "created", ...}
  ```

- **Severity:** Minor
  **Where:** cli.md CLI-001 and CLI-011
  **What:** CLI-001 says an unknown subcommand prints usage to stderr and exits 2, and today that is true. CLI-011 says "`ticketdesk list extra` is rejected in the same way", and that is also true. There's a small gap in CLI-011's "Nothing is printed to stdout", which I checked only for `list extra`. `-h` is excluded. For `list`, `-h` prints usage to stdout and exits 0 (observed). Whether `overdue -h` follows the same pattern is unsupported until it is built.
  **Evidence:**
  ```
  $ ticketdesk --log d.jsonl list extra
  ticketdesk: error: unrecognized arguments: extra
  [exit 2]
  $ ticketdesk overdue
  ticketdesk: error: argument cmd: invalid choice: 'overdue' (choose from 'create', 'assign', 'close', 'list')
  [exit 2]
  ```
  This is not a defect. It shows the draft's 0.3.0 claims hold, and it also shows `overdue` is not yet testable.

Checked and holding: an `OVERDUE`-like word inside a single-line title is harmless. A missing log makes `list` print nothing and leaves no file created, which matches the "neither listing creates it" part of TKT-017. Everything else (TKT-014 to TKT-016, TKT-018, the TKT-019 sort order and the "nothing printed" parts of CLI-010) describes unbuilt behavior, so I can't test it.

I changed nothing in the repository or the document. My test files are in `/tmp/td_t`.