# Inventory: the product read back against the specs

Loaded from `SKILL.md` step 5. The spec-to-product direction finds criteria the product
broke. This direction finds behaviour the product has that no criterion describes. Both
are drift. The second kind arrives without anyone noticing, because nothing fails.

## Enumerate the surface

List what the product does, from the outside:

- **Commands, screens, endpoints.** Every entry the help output, the navigation, or the
  API docs show, and every one you reached during the run that they do not show.
- **Options and arguments.** Every flag, parameter, and environment variable the product
  reads.
- **Output.** Every line format, file, and record the product writes for its user.
- **Exit paths.** Every exit code and every error path you hit, including crashes.

Take the list from the product's own help and from the evidence log of step 4. A CLI's
`--help`, a web app's navigation, and an API's documented routes are the starting point.
Behaviour you found only by running it goes on the list too.

## Map each behaviour

For each behaviour, name the criterion that covers it. A behaviour with no criterion is
**UNCOVERED**. Report it with the run that shows it: the command or action, and the
output. An UNCOVERED item is a fact, not a defect. The user decides whether it gets a
criterion, gets removed, or stays undocumented on purpose.

## What counts

A behaviour worth reporting is one a user could rely on, or be surprised by:

- a command, screen, or endpoint
- an option or an argument
- an output line, a file, or a field in a file
- an exit code or an error message
- a crash or a stack trace a user can reach

Input tolerance is not a behaviour, unless a criterion claims the opposite. A title that
accepts unicode, a negative number parsed as an integer, and whitespace kept as given are
details of the implementation. Report them only when a criterion says they should be
rejected or transformed. The same goes for the precision of a timestamp and the order of
fields in a record, unless a criterion names them.

## A criterion with no behaviour

The reverse case belongs to step 3, not here. A criterion whose behaviour you could not
reach is BLOCKED, and the report's BLOCKED list already names what is missing.
