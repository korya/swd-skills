# Drift actions

Drift report: 21 criteria, 20 MATCH, 0 DRIFT, 0 BLOCKED, 1 OPEN, 3 UNCOVERED. Subagent model: sonnet.

- DRIFT: none. No criterion text changed.
- BLOCKED: none. No criterion rewritten or moved.
- OPEN TKT-002 (message and exit code for a priority outside P1, P2, P3): kept the criterion and its TODO unchanged. The settled part matched. The traceback is a crash, so it stays a question (Q5 in questions.md), not a criterion.
- UNCOVERED 1 (`--help` and `-h` exit 0 on the top command and each command): added TKT-014 in docs/product-specs/tickets.md. A user relies on help. Checked that it prints to standard output before writing the criterion.
- UNCOVERED 2 (corrupt log line gives a ValueError traceback, exit 1): no criterion. A traceback goes to the questions (Q6 in questions.md). INV-004 already states that the command stops.
- UNCOVERED 3 (unreadable log path such as `--log ""` gives an IsADirectoryError traceback, exit 1): no criterion. Added Q7 to questions.md.
