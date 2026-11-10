# Rationalizations

Loaded when a shortcut looks reasonable. Each one below has looked reasonable before.

## "The code is right, the spec is stale. I'll note that the spec should change."

You do not know which side is right. The spec was signed off by a person, and the code
was merged by a person, and the two now disagree. The report shows the disagreement with
a run. The decision belongs to the user, who knows which promise was made to whom.
Propose nothing. Record the DRIFT.

## "I read the function. It clearly does what the criterion says."

Reading code tells you what the code intends. The criterion promises what the user sees.
Those differ whenever a format string, a flag, a default, or a wrapper sits between them.
A verdict comes from the surface or it is BLOCKED. Reading is allowed only to explain a
DRIFT you already saw.

## "The spec has a TODO on this, so it's not drift."

Correct for the part the TODO covers, and that is what OPEN is for. The settled part of
the criterion still gets cases. A criterion that says "exits with code 2" and carries a
TODO about the message is still DRIFT when it exits with 1.

## "This behaviour is obvious. Nobody needs a criterion for `--help`."

Then the user will say so when they see it under UNCOVERED, and it costs them one line.
A behaviour you left off the inventory because it seemed obvious is the one that changes
silently next year. List it and let the user decide.

## "The spec set is large. I'll sample the criteria."

A sample finds the drift in the sample. The report then says "no drift" about criteria
nobody checked, and the next reader trusts it. If the full set is too costly, say so and
narrow the scope by prefix or file with the user. State the narrowed scope in the report.
Never report a sample as the set.

## "The product can't be started here, but the tests pass."

The tests are the product's claim about itself. BLOCKED is the verdict, with "the product
did not start" as the reason, for every criterion that needed it. A report that says
"the tests pass, so MATCH" has tested nothing.
