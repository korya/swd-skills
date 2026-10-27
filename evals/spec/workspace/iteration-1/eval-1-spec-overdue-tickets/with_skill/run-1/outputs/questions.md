# Questions for the overdue tickets spec

Asked on 2026-10-27 while writing the spec. Nobody was available to answer, so each
question states the assumption the spec proceeds on. The same assumption is marked as a
`TODO` under the spec item it affects. An answer changes that item and nothing else.

## Blocking: these shape the contract

### Q1. Is a closed ticket ever overdue?

Assumption: no. Only an `open` or `assigned` ticket can be overdue. A ticket closed after
its due time shows no marker and is absent from `ticketdesk overdue`.

Why: the request is a work queue for support agents, and a closed ticket needs no work. A
late closure is a reporting concern, which the request does not mention.

Lands in: TKT-014.

### Q2. Where does `OVERDUE` go on a `list` line?

Assumption: between the padded state and the title, as
`#<id> [<priority>] <state> OVERDUE <title>`. The line of every other ticket does not
change.

Why: a marker before the title cannot be confused with a title that ends in "OVERDUE".
Lines without the marker stay identical to today, so a script that reads `list` output
keeps working for them. The cost is that titles of overdue lines sit seven characters to
the right of the others.

Lands in: CLI-010.

### Q3. What does a `ticketdesk overdue` line look like?

Assumption: the same line that `list` prints for that ticket, marker included.

Why: one ticket has one line shape. The two commands then never disagree, and a reader who
learns one has learned both.

Lands in: CLI-011.

## Open: the spec proceeds either way

### Q4. Should `overdue` show the due time, or how late a ticket is?

Assumption: no. The request asks for a list in due order, and no command shows a time
today. Adding a column later is a new spec item, not a change to CLI-011.

### Q5. Is a ticket overdue at the exact second it is due?

Assumption: no. A ticket is overdue when the current time is later than its due time.
Lands in TKT-014.

### Q6. Should `overdue` exit non-zero when overdue tickets exist?

A cron job or a shell script could then alert on the exit code alone. Assumption: no. The
command exits with code 0 like `list`, see CLI-008. Lands in CLI-011.

### Q7. Does anyone need to override the current time, for tests or demos?

Assumption: no option. A black-box test can append a `created` event with an old `at`
value to the log file, which is a product surface per `event-log.md`. Lands in CLI-011,
which says the command takes no options.
