"""Plant the nine defects of seeded-9.patch into a fixture that holds base.patch.

Usage: plant.py <repo>   The repo is a fresh fixture with specs/base.patch applied.
seeded-3.patch holds only P1, I1, and I3. The classes: D against existing specs, P
against the product, I inside the draft.
"""
import pathlib, sys
repo = pathlib.Path(sys.argv[1])
def sub(path, old, new):
    p = repo / path
    text = p.read_text()
    assert text.count(old) == 1, (path, old[:50], text.count(old))
    p.write_text(text.replace(old, new))

cli, tkt = "docs/product-specs/cli.md", "docs/product-specs/tickets.md"

# D1: skipping unreadable lines. Against INV-004 and LOG-007.
sub(cli, """### CLI-012: overdue on a log that cannot be read

A log that stops `ticketdesk list` with an error stops `ticketdesk overdue` too. No ticket
line is printed. A corrupt line per LOG-007 is one such log, and a `created` event with an
unknown priority is another. `overdue` ends with the same error message and the same exit
code as `list` on the same log.

TODO: the open TODO under CLI-007 decides what that report is. CLI-012 does not settle it.
Today `list` on a corrupt log prints a Python traceback and exits with code 1.
""", """### CLI-012: overdue on a damaged log

`ticketdesk overdue` skips a log line that it cannot read and lists the overdue tickets
from the other lines. One bad line does not hide the late tickets from the agent. The
command exits with code 0.
""")
sub(tkt, """- TODO: decide the open TODO under CLI-007. Until then CLI-012 ties the report of
  `overdue` on a log that cannot be read to the report of `list`.
""", "")

# D2: a note on stderr with exit code 0. Against CLI-008.
sub(cli, "With no overdue tickets it prints nothing and exits with code 0. A missing\nlog file is one such case, see LOG-006.",
         "With no overdue tickets it prints nothing to\nstdout, prints `no overdue tickets` to stderr, and exits with code 0. A missing log file\nis one such case, see LOG-006.")
sub(tkt, "- TODO: confirm that `overdue` with no overdue tickets prints nothing and exits with code\n  0. CLI-010 assumes it.",
         "- TODO: confirm that `overdue` with no overdue tickets prints only a note on stderr and\n  exits with code 0. CLI-010 assumes it.")

# D3: list puts overdue tickets first. Against TKT-013 and the first line of CLI-006.
sub(cli, "For an overdue ticket, see TKT-014, the line shows `OVERDUE` in place of the state. This\nrule is a draft and is not built.",
         "For an overdue ticket, see TKT-014, the line shows `OVERDUE` in place of the state. `list`\nprints the overdue tickets first, in the order of TKT-019, and then the other tickets. This\nrule is a draft and is not built.")
sub(tkt, "- **No options.** `list` gets no filter option and no sort option, and it keeps the order\n  of TKT-013. `overdue` takes no option of its own.",
         "- **No options.** `list` gets no filter option and no sort option. `overdue` takes no\n  option of its own.")

# P1: the counting claim. A line break in a title prints a forged line.
sub(cli, "position of the state. A title may contain the same word. For example, when only ticket 1\nis overdue:",
         "position of the state. A title may contain the same word. Every output line with `OVERDUE`\nin that position is one overdue ticket, so a script counts the overdue tickets by counting\nthose lines. For example, when only ticket 1 is overdue:")

# P2: --log after the command name. The product takes it only before.
sub(cli, "shows `OVERDUE`. With no overdue tickets",
         "shows `OVERDUE`. The log path follows CLI-002, for example\n`ticketdesk overdue --log desk.jsonl`. With no overdue tickets")

# P3: whole seconds. The log stamps fractions of a second.
sub(tkt, "Tickets with an equal due time are sorted by ID ascending.",
         "Tickets with an equal due time are sorted by ID ascending. The log stamps events in\nwhole seconds, so two tickets of one priority created in the same second have an equal\ndue time.")

# I1: the summary also fits a ticket closed late. Against TKT-015.
sub(tkt, "A ticket whose due\ntime has passed shows as `OVERDUE` in the ticket list until it is closed.",
         "A ticket that was\nnot closed by its due time shows as `OVERDUE` in the ticket list.")

# I2: the example. 80 - 72 = 8 hours, so ticket 1 was due first.
sub(tkt, "was created 73 hours ago", "was created 80 hours ago")

# I3: an assigned ticket always shows its state. Against TKT-016 and TKT-014.
sub(cli, "A `closed`\nticket always shows `closed`.", "A `closed`\nor `assigned` ticket always shows its state.")
