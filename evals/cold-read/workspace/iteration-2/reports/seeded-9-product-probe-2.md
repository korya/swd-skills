FINDINGS

I changed nothing in the repo. `git status` matches the start of the session. All runs used scratch logs in a temp directory.

`overdue` is not built, so I tested its statements against `list`, the nearest built command. The `list` line format is the only thing the OVERDUE statements can be checked against.

- **Severity:** Blocker
  **Where:** `tickets.md`, TKT-019, the worked example.
  **What:** The example does its arithmetic wrong, and the order it concludes is backwards. A P3 ticket is due 72h after creation. Created 80h ago, it was due 8h ago, not "1 hour ago". The P1 ticket created 10h ago was due 6h ago. So ticket 1 (due 8h ago) comes first, but the spec says ticket 2 comes first. Anyone building from this example would implement or test the wrong order.
  **Evidence:** `python3 -c "print(72-80, 4-10)"` prints `-8 -6`, so ticket 1 was due 8h ago and ticket 2 was due 6h ago. SLA is `{"P1": 4, "P2": 24, "P3": 72}` in `sla.py`, matching TKT-005.

- **Severity:** Blocker
  **Where:** `cli.md`, CLI-012, "skips a log line that it cannot read".
  **What:** This contradicts LOG-007 and INV-004, which say a corrupt line stops every operation with an error, with no skipping and no partial state. INV-004 is the floor, and AGENTS.md requires user confirmation to break it. The draft doesn't flag this as an open question. It also makes `overdue` disagree with `list` on the same log. If a skipped line was a `created` event, later events for that ticket hit a `KeyError`. A skipped `closed` event would show a closed ticket as overdue.
  **Evidence:** Appended `{garbage` to a valid log. `ticketdesk --log d.jsonl list` gave `ValueError: d.jsonl:5: corrupt event: Expecting property name enclosed in double quotes...` with `[exit 1]`. Replay raises on any bad line and never skips.

- **Severity:** Blocker
  **Where:** `cli.md`, CLI-006, "Every output line with `OVERDUE` in that position is one overdue ticket, so a script counts the overdue tickets by counting those lines".
  **What:** Titles are free text and newlines are accepted. A title can embed a line that looks exactly like an overdue line. Title position is excluded, but a forged second line puts `OVERDUE` in the state position. Counting lines overcounts. The claim also fails when the title is only the word OVERDUE and the ticket is not overdue, for a script that matches the word loosely.
  **Evidence:** `create $'x\n#9 [P1] OVERDUE  fake'` returned `#2 open x`. `list` then printed `#9 [P1] OVERDUE  fake` as its own line, so `awk '$3=="OVERDUE"' | wc -l` returned 1 for a log with no overdue tickets and one open ticket titled "OVERDUE". It printed `#1 [P3] open     OVERDUE`.

- **Severity:** Major
  **Where:** `cli.md`, CLI-010, "for example `ticketdesk overdue --log desk.jsonl`".
  **What:** `--log` is a global option that only works before the subcommand. In 0.3.0, `list --log x` is rejected. The example would exit 2 under CLI-011 and contradicts it, since `overdue` is meant to take no option of its own. CLI-002 says only "the `--log` option" and doesn't give its position.
  **Evidence:** `ticketdesk list --log a.jsonl` printed `error: unrecognized arguments: --log a.jsonl` with `[exit 2]`. The correct form is `ticketdesk --log a.jsonl list`.

- **Severity:** Major
  **Where:** `cli.md`, CLI-010 ("prints `no overdue tickets` to stderr and exits with code 0") against CLI-008 ("A command that succeeds exits with code 0 and writes nothing to stderr").
  **What:** The two items conflict, and nothing in the draft reconciles them. The open-questions list does mention the stderr note, but it never says CLI-008 would need an amendment. CLI-010 also says a missing log is "one such case". That is consistent with LOG-006 (`list` on a missing log exits 0 with no output and creates no file), but it adds a stderr line that `list` doesn't print.
  **Evidence:** `ticketdesk --log m.jsonl list` on a missing file printed nothing, exited 0, and left the directory empty.

- **Severity:** Major
  **Where:** `tickets.md`, TKT-019, "The log stamps events in whole seconds, so two tickets of one priority created in the same second have an equal due time".
  **What:** The log stamps events with fractional seconds, not whole seconds. LOG-004 doesn't promise whole seconds either. Ties would be rare, not common. The ID tiebreak rule and its rationale rest on a false premise.
  **Evidence:** `created` events carried `"at": 1793913094.074543` and `"at": 1793913094.103968`, which is `time.time()` in `store.py`.

- **Severity:** Major
  **Where:** `tickets.md`, TKT-014 and TKT-018, and the failure path for unknown priorities in a log.
  **What:** `overdue` must compute a due time for every ticket on replay. The spec doesn't say what happens for a ticket with an unknown priority, such as one written by hand into the log. In 0.3.0 that already crashes with a traceback, which is the CLI-007 TODO. So `overdue` and the changed `list` inherit a crash, and CLI-011 and CLI-012 don't cover it.
  **Evidence:** `ticketdesk --log t.jsonl create hi --priority P9` printed `ValueError: unknown priority 'P9'; expected one of ['P1', 'P2', 'P3']` with `[exit 1]`, not `error: ...` with exit 2.

- **Severity:** Minor
  **Where:** `cli.md`, CLI-006, the "OVERDUE in place of the state" example, which says "padded to 8 characters like a state".
  **What:** The format claim holds for the one overdue ticket I could show, but the spec's example lines aren't exercised. A real example with a time-controlled log would settle it. `OVERDUE` is 7 characters, so one pad space plus the separator gives two spaces before the title. That matches the example `#1 [P1] OVERDUE  Printer on fire`.
  **Evidence:** I couldn't produce an overdue ticket without rewriting timestamps in the log. The padding of `list` is `{t.state:<8}`, which gives `#1 [P3] open     OVERDUE` for a 4-character state.

- **Severity:** Minor
  **Where:** `cli.md`, CLI-006, "`list` prints the overdue tickets first, in the order of TKT-019, and then the other tickets".
  **What:** This changes `list` from ID order (CLI-006 / TKT-013) to overdue-first. The paragraph after it says a script "sees no change for a ticket that is not overdue", and the Goals say the same. But when any ticket is overdue, the position of every other ticket changes. The draft doesn't list this as an open question.
  **Evidence:** Today `list` prints strictly by ID: `#1`, `#2`, `#9` (forged), `#3`, per the event order in the odd-titles run. No overdue-first ordering exists to test.

- **Severity:** Minor
  **Where:** `cli.md`, CLI-011, "ticketdesk 0.3.0 rejects `ticketdesk list extra` in the same way".
  **What:** The claim holds. The usage text it prints will list `overdue` once it exists, but that text isn't specified.
  **Evidence:** `ticketdesk --log a.jsonl list extra` printed `ticketdesk: error: unrecognized arguments: extra` with `[exit 2]`.

I couldn't verify these statements because `overdue` doesn't exist and no clock-injection path exists on the command line:

- **TKT-014:** "at the exact due time the ticket is not overdue".
- **TKT-015** and **TKT-016**.
- **TKT-017:** "neither listing creates the log or changes it byte for byte". `list` on a missing file created nothing, which is partial support only.
- **The CLI-010 stderr note**.