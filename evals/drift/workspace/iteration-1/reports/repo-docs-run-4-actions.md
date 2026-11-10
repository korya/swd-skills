# Drift actions

Report: 22 criteria, 19 MATCH, 3 DRIFT, 0 BLOCKED, 0 OPEN, 8 UNCOVERED. Spec text changed, code and tests did not.

## DRIFT

- DRIFT TKT-015 (a title with a line break prints as two lines): fixed the text. TKT-015 no longer promises one line per ticket and states that a title prints as given. Listed in questions Q7.
- DRIFT LOG-005 (a change rewrites line 1 of a log without a final line break): fixed the text. LOG-005 now holds for a log whose last line ends with a line break. Added LOG-010 for the other case. Listed in questions Q7.
- DRIFT LOG-007 (a rejected `create` and non-UTF-8 bytes do not end in the corrupt-event traceback): fixed the text. LOG-007 now covers commands that read the log. Added LOG-008 (which commands read the log) and LOG-011 (non-UTF-8 bytes). Moved the blank-line sentence to LOG-009 and added that blank lines count in the line number.

## BLOCKED

- None reported.

## OPEN

- None reported.

## UNCOVERED

- UNCOVERED 5.1 (help output): added TKT-016.
- UNCOVERED 5.2 (usage errors, two lines, status 2): added TKT-017. Narrowed TKT-014 to the rejections it names and TKT-013 to an integer ID. LOG-003 now names a usage error.
- UNCOVERED 5.3 (unusable log path): added LOG-014 (path is a directory, empty `TICKETDESK_LOG`) and LOG-015 (missing directory). Listed in questions Q7.
- UNCOVERED 5.4 (valid JSON that is not an event): added LOG-012.
- UNCOVERED 5.5 (unknown `kind` is skipped): added LOG-013. Narrowed INV-003 to lines that are not valid JSON and pointed it at LOG-013. Listed in questions Q7.
- UNCOVERED 5.6 (a second `created` line with the same ID replaces the ticket): no criterion. Listed as question Q8. `docs/architecture.md` states the assumption that only the product writes the log.
- UNCOVERED 5.7 (order of checks): added one sentence on the order to each of TKT-003, TKT-008, and TKT-012.
- UNCOVERED 5.8 (the Python package exposes more than the due time): no criterion. Listed as question Q9.

## After the verdicts

- Reread the changed criteria against each other. Split LOG-015 from LOG-014, and aligned the term "a command that reads the log" across LOG-007, LOG-008, LOG-011, LOG-012, and LOG-014.
- Checked the new claims that the report did not show, with my own runs under `scratch/verify/`: `assign` and `close` on a log without a final line break, `create` and `assign` on a non-UTF-8 log, `assign` on a directory path and on a missing directory.
- The changed criteria did not get a second drift run.
