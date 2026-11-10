# drift evals

Measures whether `/drift` finds the places where a product and its specs disagree, and
reports them with a run as evidence. The fixture is the blueprint fixture, ticketdesk with
agent docs, plus one commit that changes the product in five places. The specs stay as
they were. The commit message calls it a refactor.

## Layout

- `make_fixture.sh <dir>` builds the fixture and applies the planted commit.
- `evals.json` holds one eval in the skill-creator benchmark format.
- `workspace/iteration-N/` holds the reports and the benchmark.

## Planted drift

| ID | Plant | The criterion it breaks | Found by |
|---|---|---|---|
| X1 | A resolution note of 8 or 9 characters is accepted. | TKT-010 says 10, and names the error text. | closing a ticket with a 9-character note |
| X2 | `list` pads the state to 9 characters. | CLI-006 says 8. | counting the spaces in a `list` line |
| X3 | An unknown ticket fails with `ticket <id> not found`. | TKT-012 says `no ticket <id>`. | assigning or closing ticket 99 |
| X4 | Log lines are written with unsorted keys. | LOG-005 says keys sorted alphabetically. | reading the log file after a create |
| X5 | A `count` subcommand prints the number of tickets. | No criterion. CLI-001 lists four subcommands. | `--help`, or running `count` |

Two criteria cannot be observed from the surface and stay BLOCKED in a correct run.
TKT-005 promises a due time that no command prints. TKT-009 promises that closing keeps
the assignee, and no command shows an assignee. The CLI-007 TODO about tracebacks is OPEN,
not DRIFT.

## Baseline

`/e2e-test` told to sweep every spec found X1 to X5 in 2 of 2 runs, before the skill
existed. The runs were on `claude-sonnet-5-5`, at $0.38 to $0.43 and 138 to 146 seconds. One of the two
runs scored the CLI-007 TODO as a failure. That is the ambiguity the OPEN verdict closes.

## Running

Run with the skill-creator benchmark flow. Grade the prose with `scripts/prose-lint.py`.
